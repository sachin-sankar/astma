"""Phase 4: Fast Vectorized High-Performance Skill Combination Miner.

Computes skill bundle associations using int32 sparse matrices:
- Support, Independent Expected Prevalence, Lift, High-Earner Proportion, High-Earner Lift.
- Contingency Tables, Odds Ratios (OR) with 95% Confidence Intervals.
- Chi-Square test with Yates continuity correction and Benjamini-Hochberg FDR correction.
- Controlled Logistic Regression (ORs with controls) and OLS Regression (log-earnings coefficients).
"""

import json
from typing import Any

import duckdb
import numpy as np
import pandas as pd
import scipy.sparse as sp
import statsmodels.api as sm
from loguru import logger
from scipy.stats import chi2
from statsmodels.stats.multitest import multipletests

from src.common.config import DEFAULT_CONFIG, PipelineConfig


class VectorizedCombinationMiner:
    """Vectorized statistical miner for skill bundles."""

    def __init__(self, config: PipelineConfig = DEFAULT_CONFIG):
        self.config = config

    def run(self) -> dict[str, Any]:
        self.config.ensure_directories()
        logger.info("Loading tables with DuckDB...")
        con = duckdb.connect()
        freelancers_df = con.execute(f"""
        SELECT user_id, high_earner, total_earnings, log_earnings, hourly_rate, skill_count, review_count, country
        FROM read_parquet('{self.config.freelancers_parquet}')
        ORDER BY user_id
        """).fetchdf()

        skills_df = con.execute(f"""
        SELECT user_id, skill_name 
        FROM read_parquet('{self.config.freelancer_skills_parquet}')
        """).fetchdf()
        con.close()

        total_n = len(freelancers_df)
        is_high_earner = freelancers_df["high_earner"].to_numpy(dtype=bool)
        base_rate = float(np.mean(is_high_earner))
        high_earner_n = int(np.sum(is_high_earner))

        # Filter skills by frequency threshold
        skill_counts = skills_df["skill_name"].value_counts()
        valid_skills = skill_counts[
            skill_counts >= self.config.min_skill_frequency
        ].index.tolist()
        logger.info(
            f"Retaining {len(valid_skills)} skills with frequency >= {self.config.min_skill_frequency}"
        )

        user_to_idx = {uid: i for i, uid in enumerate(freelancers_df["user_id"])}
        skill_to_idx = {s: i for i, s in enumerate(valid_skills)}

        skills_filtered = skills_df[skills_df["skill_name"].isin(skill_to_idx)].copy()
        row_indices = skills_filtered["user_id"].map(user_to_idx).to_numpy()
        col_indices = skills_filtered["skill_name"].map(skill_to_idx).to_numpy()

        # Build Sparse Matrix (Users x Skills) in int32 to prevent overflow
        data = np.ones(len(row_indices), dtype=np.int32)
        user_skill_mat = sp.csr_matrix(
            (data, (row_indices, col_indices)),
            shape=(total_n, len(valid_skills)),
            dtype=np.int32,
        )

        skill_freqs = np.array(user_skill_mat.sum(axis=0)).flatten()
        skill_prevalences = skill_freqs / float(total_n)
        min_cnt = max(
            self.config.min_combination_count,
            int(self.config.min_combination_support * total_n),
        )

        # 1. Pairs Co-occurrence Matrix (S^T * S)
        logger.info("Computing co-occurrence matrices...")
        cooc_mat = user_skill_mat.T.dot(user_skill_mat)
        cooc_coo = sp.triu(cooc_mat, k=1).tocoo()

        pair_mask = cooc_coo.data >= min_cnt
        p_row = cooc_coo.row[pair_mask]
        p_col = cooc_coo.col[pair_mask]
        n_bundle_arr = cooc_coo.data[pair_mask].astype(float)
        logger.info(
            f"Filtered to {len(p_row)} frequent pairs (>= {min_cnt} freelancers)."
        )

        # High Earner Co-occurrence Matrix
        high_mat = user_skill_mat[is_high_earner, :]
        high_cooc_mat = high_mat.T.dot(high_mat).tocsr()

        # Fast extraction of high_counts for pairs
        high_cnt_arr = np.asarray(high_cooc_mat[p_row, p_col]).reshape(-1).astype(float)

        # Vectorized Statistical Calculation for Pairs
        exp_prev_arr = skill_prevalences[p_row] * skill_prevalences[p_col]

        # Build Vectorized Triples for Top Pairs
        logger.info("Mining candidate triples...")
        top_pair_order = np.argsort(-n_bundle_arr)[:300]
        triple_candidates: set[tuple[int, int, int]] = set()

        for idx in top_pair_order:
            i, j = p_row[idx], p_col[idx]
            overlap = cooc_mat.getrow(i).multiply(cooc_mat.getrow(j)).tocoo()
            for k in overlap.col:
                if k > j and overlap.data[overlap.col == k][0] >= min_cnt:
                    triple_candidates.add((i, j, k))

        logger.info(
            f"Found {len(triple_candidates)} candidate triples. Evaluating exact counts..."
        )

        t_skills_1 = []
        t_skills_2 = []
        t_skills_3 = []
        t_n_bundle = []
        t_high_cnt = []
        t_exp_prev = []

        if len(triple_candidates) > 0:
            user_skill_csc = user_skill_mat.tocsc()
            for i, j, k in triple_candidates:
                col_i = user_skill_csc[:, i]
                col_j = user_skill_csc[:, j]
                col_k = user_skill_csc[:, k]
                overlap_vec = col_i.multiply(col_j).multiply(col_k)
                cnt = int(overlap_vec.sum())
                if cnt >= min_cnt:
                    h_cnt = int(overlap_vec[is_high_earner].sum())
                    t_skills_1.append(i)
                    t_skills_2.append(j)
                    t_skills_3.append(k)
                    t_n_bundle.append(cnt)
                    t_high_cnt.append(h_cnt)
                    t_exp_prev.append(
                        skill_prevalences[i]
                        * skill_prevalences[j]
                        * skill_prevalences[k]
                    )

        logger.info(f"Validated {len(t_n_bundle)} frequent triples.")

        # Combine Pairs & Triples Arrays
        all_sizes = np.array([2] * len(p_row) + [3] * len(t_n_bundle))
        all_n_bundle = np.concatenate([n_bundle_arr, np.array(t_n_bundle, dtype=float)])
        all_high_cnt = np.concatenate([high_cnt_arr, np.array(t_high_cnt, dtype=float)])
        all_exp_prev = np.concatenate([exp_prev_arr, np.array(t_exp_prev, dtype=float)])

        # Bundle Names and JSON list
        bundle_names = []
        bundle_skills_json = []
        for i, j in zip(p_row, p_col):
            s = sorted([valid_skills[i], valid_skills[j]])
            bundle_names.append(" + ".join(s))
            bundle_skills_json.append(json.dumps(s))

        for i, j, k in zip(t_skills_1, t_skills_2, t_skills_3):
            s = sorted([valid_skills[i], valid_skills[j], valid_skills[k]])
            bundle_names.append(" + ".join(s))
            bundle_skills_json.append(json.dumps(s))

        # Vectorized Statistical Calculations
        support_arr = all_n_bundle / float(total_n)
        lift_arr = np.where(all_exp_prev > 0, support_arr / all_exp_prev, 1.0)

        a = all_high_cnt
        b = all_n_bundle - a
        c = float(high_earner_n) - a
        d = float(total_n - high_earner_n) - b

        bundle_high_rate_arr = np.where(all_n_bundle > 0, a / all_n_bundle, 0.0)
        high_lift_arr = np.where(base_rate > 0, bundle_high_rate_arr / base_rate, 1.0)

        # Haldane-Anscombe corrected Odds Ratio
        a_c = np.where((a == 0) | (b == 0) | (c == 0) | (d == 0), a + 0.5, a)
        b_c = np.where((a == 0) | (b == 0) | (c == 0) | (d == 0), b + 0.5, b)
        c_c = np.where((a == 0) | (b == 0) | (c == 0) | (d == 0), c + 0.5, c)
        d_c = np.where((a == 0) | (b == 0) | (c == 0) | (d == 0), d + 0.5, d)

        or_arr = (a_c * d_c) / (b_c * c_c)
        se_log_or = np.sqrt(1.0 / a_c + 1.0 / b_c + 1.0 / c_c + 1.0 / d_c)
        log_or = np.log(or_arr)
        ci_lower_arr = np.exp(log_or - 1.96 * se_log_or)
        ci_upper_arr = np.exp(log_or + 1.96 * se_log_or)

        # Vectorized Chi-Square Test with Yates continuity correction
        n_tot = a + b + c + d
        obs_diff = np.abs(a * d - b * c) - (n_tot / 2.0)
        obs_diff = np.maximum(obs_diff, 0.0)
        chi2_stat = (n_tot * (obs_diff**2)) / (
            (a + b) * (c + d) * (a + c) * (b + d) + 1e-9
        )
        p_val_arr = chi2.sf(chi2_stat, df=1)

        # Construct DataFrame
        comb_df = pd.DataFrame(
            {
                "bundle_name": bundle_names,
                "bundle_skills": bundle_skills_json,
                "bundle_size": all_sizes,
                "freelancer_count": all_n_bundle.astype(int),
                "support": np.round(support_arr, 5),
                "expected_prevalence": np.round(all_exp_prev, 6),
                "lift": np.round(lift_arr, 3),
                "high_earner_count": all_high_cnt.astype(int),
                "high_earner_rate": np.round(bundle_high_rate_arr, 4),
                "high_earner_lift": np.round(high_lift_arr, 3),
                "odds_ratio": np.round(or_arr, 3),
                "ci_lower": np.round(ci_lower_arr, 3),
                "ci_upper": np.round(ci_upper_arr, 3),
                "p_value": p_val_arr,
            }
        )

        # Benjamini-Hochberg FDR correction
        _, adj_pvals, _, _ = multipletests(
            comb_df["p_value"], alpha=self.config.fdr_alpha, method="fdr_bh"
        )
        comb_df["adjusted_p_value"] = adj_pvals
        comb_df["is_significant_fdr"] = (
            comb_df["adjusted_p_value"] < self.config.fdr_alpha
        )

        # Sort by high earner lift descending
        comb_df = comb_df.sort_values(
            by=["high_earner_lift", "freelancer_count"], ascending=[False, False]
        )
        comb_df.to_parquet(self.config.skill_combinations_parquet, index=False)
        logger.info(
            f"Successfully evaluated and saved {len(comb_df)} combinations. Significant FDR: {comb_df['is_significant_fdr'].sum()}"
        )

        # Regressions for Top 30 Bundles
        reg_results = self.run_regressions(
            comb_df, user_skill_mat, valid_skills, freelancers_df
        )
        return {
            "total_bundles": len(comb_df),
            "significant_fdr": int(comb_df["is_significant_fdr"].sum()),
            "regressions_run": len(reg_results.get("top_bundles_regression", [])),
        }

    def run_regressions(
        self,
        comb_df: pd.DataFrame,
        user_skill_mat: sp.csr_matrix,
        valid_skills: list[str],
        freelancers_df: pd.DataFrame,
        top_n: int = 30,
    ) -> dict[str, Any]:
        """Runs controlled logistic and OLS regressions for top high-earning skill bundles."""
        logger.info(f"Running controlled regressions for top {top_n} bundles...")
        skill_to_idx = {s: i for i, s in enumerate(valid_skills)}

        top_countries = freelancers_df["country"].value_counts().head(5).index.tolist()
        df_reg = freelancers_df.copy()
        df_reg["log_reviews"] = np.log1p(df_reg["review_count"])

        for c in top_countries:
            df_reg[f"country_{c}"] = (df_reg["country"] == c).astype(int)

        country_cols = [f"country_{c}" for c in top_countries]
        base_covars = ["skill_count", "log_reviews"] + country_cols

        regression_results: list[dict[str, Any]] = []
        top_bundles = comb_df.head(top_n)

        for _, row in top_bundles.iterrows():
            skills = json.loads(row["bundle_skills"])
            col_indices = [skill_to_idx[s] for s in skills if s in skill_to_idx]
            if len(col_indices) == len(skills):
                submat = user_skill_mat[:, col_indices]
                bundle_mask = (
                    np.array(submat.sum(axis=1) == len(skills)).flatten().astype(int)
                )
            else:
                bundle_mask = np.zeros(len(freelancers_df), dtype=int)

            df_reg["bundle_dummy"] = bundle_mask
            X = df_reg[["bundle_dummy"] + base_covars]
            X = sm.add_constant(X)

            # Logit
            try:
                logit_model = sm.Logit(df_reg["high_earner"].astype(int), X).fit(
                    disp=False
                )
                bundle_coef = logit_model.params["bundle_dummy"]
                bundle_se = logit_model.bse["bundle_dummy"]
                bundle_pval = logit_model.pvalues["bundle_dummy"]
                controlled_or = float(np.exp(bundle_coef))
                ci_low = float(np.exp(bundle_coef - 1.96 * bundle_se))
                ci_high = float(np.exp(bundle_coef + 1.96 * bundle_se))
            except (ValueError, TypeError, np.linalg.LinAlgError) as e:
                logger.warning(f"Logit failed for bundle {row['bundle_name']}: {e}")
                controlled_or = float(row["odds_ratio"])
                ci_low = float(row["ci_lower"])
                ci_high = float(row["ci_upper"])
                bundle_pval = float(row["p_value"])

            # OLS
            try:
                ols_model = sm.OLS(df_reg["log_earnings"], X).fit()
                ols_coef = float(ols_model.params["bundle_dummy"])
                ols_pval = float(ols_model.pvalues["bundle_dummy"])
                ols_r2 = float(ols_model.rsquared)
            except (ValueError, TypeError, np.linalg.LinAlgError) as e:
                logger.warning(f"OLS failed for bundle {row['bundle_name']}: {e}")
                ols_coef = 0.0
                ols_pval = 1.0
                ols_r2 = 0.0

            regression_results.append(
                {
                    "bundle_name": row["bundle_name"],
                    "bundle_skills": skills,
                    "bundle_size": int(row["bundle_size"]),
                    "freelancer_count": int(row["freelancer_count"]),
                    "raw_odds_ratio": float(row["odds_ratio"]),
                    "controlled_odds_ratio": round(controlled_or, 3),
                    "controlled_ci_lower": round(ci_low, 3),
                    "controlled_ci_upper": round(ci_high, 3),
                    "controlled_logit_pval": float(bundle_pval),
                    "ols_log_earnings_coef": round(ols_coef, 3),
                    "ols_pval": float(ols_pval),
                    "ols_r2": round(ols_r2, 4),
                }
            )

        output_data = {
            "model_controls": base_covars,
            "top_bundles_regression": regression_results,
        }

        with open(self.config.combination_regression_json, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)

        return output_data


def run_combination_analysis(config: PipelineConfig = DEFAULT_CONFIG) -> dict[str, Any]:
    miner = VectorizedCombinationMiner(config=config)
    return miner.run()


if __name__ == "__main__":
    run_combination_analysis()
