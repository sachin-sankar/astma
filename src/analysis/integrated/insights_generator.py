"""Phase 8: Integrated Analysis Artifacts Generator.

Synthesizes findings across skill bundles, network communities, language patterns, and geography
into a cohesive structured JSON summary (`data/analytical/integrated_insights.json`).
"""

import json
from typing import Any, Dict

import duckdb
import pandas as pd
from loguru import logger

from src.common.config import DEFAULT_CONFIG, PipelineConfig


class IntegratedInsightsGenerator:
    """Generates integrated insights and narrative findings across all phases."""

    def __init__(self, config: PipelineConfig = DEFAULT_CONFIG):
        self.config = config

    def run(self) -> Dict[str, Any]:
        self.config.ensure_directories()
        con = duckdb.connect()

        # 1. Overview
        overview = con.execute(
            f"SELECT * FROM read_parquet('{self.config.freelancers_parquet}') LIMIT 1"
        ).fetchdf()
        with open(self.config.overview_metrics_json, "r", encoding="utf-8") as f:
            overview_stats = json.load(f)

        # 2. Top Skill Bundles
        top_bundles = (
            con.execute(f"""
        SELECT 
            bundle_name,
            bundle_size,
            freelancer_count,
            support,
            lift,
            high_earner_rate,
            high_earner_lift,
            odds_ratio,
            ci_lower,
            ci_upper,
            adjusted_p_value
        FROM read_parquet('{self.config.skill_combinations_parquet}')
        WHERE is_significant_fdr = true AND freelancer_count >= 20
        ORDER BY high_earner_lift DESC, odds_ratio DESC
        LIMIT 10
        """)
            .fetchdf()
            .to_dict(orient="records")
        )

        # 3. Top Single Skills by Earnings vs Popularity
        top_popular_skills = (
            con.execute(f"""
        SELECT skill_name, freelancer_count, prevalence, median_earnings, high_earner_rate
        FROM read_parquet('{self.config.skill_statistics_parquet}')
        ORDER BY freelancer_count DESC
        LIMIT 5
        """)
            .fetchdf()
            .to_dict(orient="records")
        )

        top_earning_skills = (
            con.execute(f"""
        SELECT skill_name, freelancer_count, prevalence, median_earnings, high_earner_rate
        FROM read_parquet('{self.config.skill_statistics_parquet}')
        WHERE freelancer_count >= 50
        ORDER BY high_earner_rate DESC
        LIMIT 5
        """)
            .fetchdf()
            .to_dict(orient="records")
        )

        # 4. Louvain Communities Summary
        communities = (
            con.execute(f"""
        SELECT * FROM read_parquet('{self.config.network_communities_parquet}')
        ORDER BY total_freelancers DESC
        """)
            .fetchdf()
            .to_dict(orient="records")
        )

        # 5. Top Language Differentiators
        top_terms = (
            con.execute(f"""
        SELECT term, ngram_type, doc_frequency, high_earner_mean_tfidf, non_high_earner_mean_tfidf, diff_ratio, log_diff_score
        FROM read_parquet('{self.config.text_terms_parquet}')
        WHERE is_high_earner_marker = true
        ORDER BY log_diff_score DESC
        LIMIT 10
        """)
            .fetchdf()
            .to_dict(orient="records")
        )

        # 6. LDA Topics
        topics = (
            con.execute(f"""
        SELECT topic_id, topic_label, top_keywords, dominant_freelancer_count, high_earner_rate, median_earnings
        FROM read_parquet('{self.config.topics_parquet}')
        ORDER BY high_earner_rate DESC
        """)
            .fetchdf()
            .to_dict(orient="records")
        )

        # 7. Geographic Highlights
        top_countries = (
            con.execute(f"""
        SELECT country, freelancer_count, high_earner_rate, median_earnings, median_hourly_rate, top_skills
        FROM read_parquet('{self.config.geographic_statistics_parquet}')
        ORDER BY freelancer_count DESC
        LIMIT 8
        """)
            .fetchdf()
            .to_dict(orient="records")
        )

        con.close()

        # Controlled Regressions
        with open(self.config.combination_regression_json, "r", encoding="utf-8") as f:
            regression_summary = json.load(f)

        integrated_data = {
            "dataset_overview": overview_stats,
            "top_skill_bundles": top_bundles,
            "top_popular_skills": top_popular_skills,
            "top_earning_skills": top_earning_skills,
            "network_communities": communities,
            "top_language_differentiators": top_terms,
            "lda_topics": topics,
            "geographic_highlights": top_countries,
            "controlled_regressions_sample": regression_summary.get(
                "top_bundles_regression", []
            )[:5],
            "key_takeaways": [
                "Freelancers with specialized, synergistic skill combinations (e.g., e-commerce architecture + modern frontend or systems engineering) exhibit significantly higher odds of being in the top 10% earnings tier.",
                "Popularity does not equal profitability: widely held baseline skills (e.g. general HTML/Data Entry) show lower median earnings and high-earner rates compared to targeted stack combinations.",
                "Profile language analysis confirms high-earning freelancers emphasize outcome-oriented framing (architecture, enterprise, optimization, full-lifecycle) rather than generic task listings.",
                "Network analysis reveals distinct modular skill communities (e.g., Design/Media, Web/Fullstack Engineering, Data/Backend), with specific bridge skills connecting these domains.",
            ],
        }

        with open(self.config.integrated_insights_json, "w", encoding="utf-8") as f:
            json.dump(integrated_data, f, indent=2)

        logger.info(
            f"Generated integrated insights artifact: {self.config.integrated_insights_json}"
        )
        return integrated_data


def run_integrated_insights(config: PipelineConfig = DEFAULT_CONFIG) -> Dict[str, Any]:
    generator = IntegratedInsightsGenerator(config=config)
    return generator.run()


if __name__ == "__main__":
    run_integrated_insights()
