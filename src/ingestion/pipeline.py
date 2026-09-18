"""Phase 2: Ingestion and Normalization Pipeline.

Converts raw scraped JSON files into clean, typed, relational Parquet tables:
1. `freelancers`: user profile metadata, earnings, log_earnings, high_earner status, rates.
2. `freelancer_skills`: normalized user skills (where is_user_skill == True).
3. `profile_text`: profile descriptions, taglines, portfolio aggregated text.
4. `portfolios`: portfolio items (title, description).

Handles deduplication, missing values, and schema standardization.
"""

import json
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

from src.common.config import DEFAULT_CONFIG, PipelineConfig


def _clean_str(val: Any) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s if len(s) > 0 else None


def _clean_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return f if not (np.isnan(f) or np.isinf(f)) else None
    except (ValueError, TypeError):
        return None


def _clean_int(val: Any) -> int:
    if val is None:
        return 0
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


class IngestionPipeline:
    """Processes raw JSON files into structured Parquet datasets."""

    def __init__(self, config: PipelineConfig = DEFAULT_CONFIG):
        self.config = config

    def extract_records(self) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
        """Reads raw files and deduplicates by user_id keeping the record with highest earnings or latest information."""
        raw_files = sorted(self.config.raw_json_dir.glob("*.json"))
        logger.info(f"Ingesting {len(raw_files)} raw JSON files...")

        user_records: dict[str, dict[str, Any]] = {}
        conflicts: list[dict[str, Any]] = []

        for fp in raw_files:
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    items = data if isinstance(data, list) else [data]
                    for rec in items:
                        if not isinstance(rec, dict):
                            continue
                        uid = _clean_str(rec.get("user_id"))
                        if not uid:
                            continue

                        if uid in user_records:
                            existing = user_records[uid]
                            conflicts.append(
                                {
                                    "user_id": uid,
                                    "source_file": fp.name,
                                    "existing_skills": len(
                                        existing.get("skills") or []
                                    ),
                                    "new_skills": len(rec.get("skills") or []),
                                }
                            )
                            # Pick record with higher total_earnings or more skills/reviews
                            existing_earn = (
                                _clean_float(existing.get("total_earnings")) or 0.0
                            )
                            new_earn = _clean_float(rec.get("total_earnings")) or 0.0
                            if new_earn > existing_earn or (
                                new_earn == existing_earn
                                and len(rec.get("skills") or [])
                                > len(existing.get("skills") or [])
                            ):
                                user_records[uid] = rec
                        else:
                            user_records[uid] = rec
            except (json.JSONDecodeError, OSError, ValueError) as e:
                logger.warning(f"Error reading {fp}: {e}")

        logger.info(f"Deduplicated to {len(user_records)} unique freelancer profiles.")
        return user_records, conflicts

    def run(self) -> dict[str, Any]:
        self.config.ensure_directories()
        user_records, conflicts = self.extract_records()

        # Save conflicts artifact
        with open(
            self.config.profiling_dir / "ingestion_conflicts.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                {
                    "conflict_count": len(conflicts),
                    "conflicts_sample": conflicts[:100],
                },
                f,
                indent=2,
            )

        # 1. Compute 90th percentile of total_earnings for High Earner threshold
        all_earnings = [
            _clean_float(r.get("total_earnings")) or 0.0 for r in user_records.values()
        ]
        high_earner_threshold = float(
            np.percentile(all_earnings, self.config.high_earner_percentile * 100)
        )
        logger.info(
            f"Computed High Earner threshold (p{int(self.config.high_earner_percentile * 100)}): ${high_earner_threshold:,.2f}"
        )

        # 2. Build Tables
        freelancers_rows: list[dict[str, Any]] = []
        skills_rows: list[dict[str, Any]] = []
        text_rows: list[dict[str, Any]] = []
        portfolio_rows: list[dict[str, Any]] = []

        for uid, rec in user_records.items():
            username = _clean_str(rec.get("username")) or uid
            public_name = _clean_str(rec.get("public_name")) or username
            country = _clean_str(rec.get("country")) or "Unknown"
            city = _clean_str(rec.get("city")) or "Unknown"
            hourly_rate = _clean_float(rec.get("hourlyrate")) or 0.0
            total_earnings = _clean_float(rec.get("total_earnings")) or 0.0
            log_earnings = float(np.log1p(total_earnings))
            is_high_earner = bool(
                total_earnings >= high_earner_threshold and total_earnings > 0.0
            )

            reputation = _clean_float(rec.get("freelancer_reputation")) or 0.0
            review_count = _clean_int(rec.get("no_reviews"))
            stars = _clean_float(rec.get("stars")) or 0.0
            score = _clean_float(rec.get("score")) or 0.0

            loc = rec.get("location") or {}
            lat = _clean_float(loc.get("lat")) if isinstance(loc, dict) else None
            lon = _clean_float(loc.get("lon")) if isinstance(loc, dict) else None

            # User skills processing
            skills = rec.get("skills") or []
            user_skill_count = 0
            seen_skill_names_for_user: set[str] = set()

            if isinstance(skills, list):
                for s in skills:
                    if not isinstance(s, dict):
                        continue
                    s_name = _clean_str(s.get("skill_name"))
                    if not s_name:
                        continue
                    is_user = bool(s.get("is_user_skill", False))
                    if is_user:
                        s_norm = s_name.strip()
                        if s_norm.lower() not in seen_skill_names_for_user:
                            seen_skill_names_for_user.add(s_norm.lower())
                            user_skill_count += 1
                            s_id = _clean_int(s.get("skill_id"))
                            skills_rows.append(
                                {
                                    "user_id": uid,
                                    "skill_id": s_id,
                                    "skill_name": s_norm,
                                }
                            )

            freelancers_rows.append(
                {
                    "user_id": uid,
                    "username": username,
                    "public_name": public_name,
                    "country": country,
                    "city": city,
                    "hourly_rate": hourly_rate,
                    "total_earnings": total_earnings,
                    "log_earnings": log_earnings,
                    "high_earner": is_high_earner,
                    "reputation": reputation,
                    "review_count": review_count,
                    "stars": stars,
                    "score": score,
                    "skill_count": user_skill_count,
                    "latitude": lat,
                    "longitude": lon,
                }
            )

            # Text processing
            user_profile = _clean_str(rec.get("user_profile")) or ""
            tagline = _clean_str(rec.get("tagline")) or ""

            # Portfolios
            portfolios = rec.get("portfolios") or []
            port_texts: list[str] = []
            if isinstance(portfolios, list):
                for idx, p in enumerate(portfolios):
                    if not isinstance(p, dict):
                        continue
                    p_title = _clean_str(p.get("title")) or ""
                    p_desc = _clean_str(p.get("description")) or ""
                    if p_title or p_desc:
                        portfolio_rows.append(
                            {
                                "user_id": uid,
                                "portfolio_id": idx + 1,
                                "title": p_title,
                                "description": p_desc,
                            }
                        )
                        port_texts.append(f"{p_title} {p_desc}".strip())

            portfolio_combined = " ".join(port_texts)
            text_rows.append(
                {
                    "user_id": uid,
                    "profile_text": user_profile,
                    "tagline": tagline,
                    "portfolio_text": portfolio_combined,
                    "combined_text": f"{tagline} {user_profile} {portfolio_combined}".strip(),
                }
            )

        # Convert to DataFrames and Save Parquet
        df_freelancers = pd.DataFrame(freelancers_rows)
        df_skills = pd.DataFrame(skills_rows)
        df_text = pd.DataFrame(text_rows)
        df_portfolios = pd.DataFrame(portfolio_rows)

        df_freelancers.to_parquet(self.config.freelancers_parquet, index=False)
        df_skills.to_parquet(self.config.freelancer_skills_parquet, index=False)
        df_text.to_parquet(self.config.profile_text_parquet, index=False)
        df_portfolios.to_parquet(self.config.portfolios_parquet, index=False)

        report = {
            "unique_freelancers": len(df_freelancers),
            "high_earners_count": int(df_freelancers["high_earner"].sum()),
            "high_earners_pct": round(
                100.0 * float(df_freelancers["high_earner"].mean()), 2
            ),
            "high_earner_threshold": high_earner_threshold,
            "total_skill_links": len(df_skills),
            "unique_skills": int(df_skills["skill_name"].nunique()),
            "portfolio_items_count": len(df_portfolios),
            "profiles_with_text": int((df_text["combined_text"].str.len() > 0).sum()),
        }

        with open(
            self.config.profiling_dir / "ingestion_report.json", "w", encoding="utf-8"
        ) as f:
            json.dump(report, f, indent=2)

        logger.info(f"Ingestion finished: {report}")
        return report


def run_ingestion(config: PipelineConfig = DEFAULT_CONFIG) -> dict[str, Any]:
    pipeline = IngestionPipeline(config=config)
    return pipeline.run()


if __name__ == "__main__":
    run_ingestion()
