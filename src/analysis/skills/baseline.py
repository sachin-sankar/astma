"""Phase 3: Baseline Skill and Earnings Analytics.

Uses DuckDB to calculate:
- Skill frequencies, prevalence, median & mean earnings, high earner rate, median hourly rate.
- Overview dataset metrics and earnings distribution percentiles/bins.
"""

import json
from typing import Any, Dict

import duckdb
import numpy as np
import pandas as pd
from loguru import logger

from src.common.config import DEFAULT_CONFIG, PipelineConfig


class SkillAnalytics:
    """Calculates skill and overall earnings baseline metrics using DuckDB."""

    def __init__(self, config: PipelineConfig = DEFAULT_CONFIG):
        self.config = config

    def compute_overview_and_earnings(
        self, con: duckdb.DuckDBPyConnection
    ) -> Dict[str, Any]:
        """Computes high-level overview metrics and earnings histogram distribution."""
        freelancers_path = str(self.config.freelancers_parquet)
        skills_path = str(self.config.freelancer_skills_parquet)

        # Overview statistics
        overview_query = f"""
        SELECT 
            count(*) as total_freelancers,
            sum(case when high_earner then 1 else 0 end) as total_high_earners,
            avg(case when high_earner then 1.0 else 0.0 end) as high_earner_rate,
            median(total_earnings) as median_earnings,
            avg(total_earnings) as mean_earnings,
            stddev(total_earnings) as std_earnings,
            median(hourly_rate) as median_hourly_rate,
            avg(hourly_rate) as mean_hourly_rate,
            median(skill_count) as median_skills_per_user,
            avg(skill_count) as mean_skills_per_user,
            median(review_count) as median_review_count,
            avg(review_count) as mean_review_count,
            (SELECT count(distinct skill_name) FROM read_parquet('{skills_path}')) as total_unique_skills
        FROM read_parquet('{freelancers_path}')
        """
        overview_res = (
            con.execute(overview_query).fetchdf().to_dict(orient="records")[0]
        )

        # Earnings Distribution for plotting
        earnings_query = f"""
        SELECT 
            total_earnings,
            log_earnings,
            hourly_rate,
            skill_count,
            review_count,
            high_earner,
            country
        FROM read_parquet('{freelancers_path}')
        """
        earnings_df = con.execute(earnings_query).fetchdf()

        # Save overview metrics json
        with open(self.config.overview_metrics_json, "w", encoding="utf-8") as f:
            json.dump(overview_res, f, indent=2)

        # Save earnings distribution parquet
        earnings_df.to_parquet(self.config.earnings_distribution_parquet, index=False)
        logger.info(
            f"Overview metrics and earnings distribution saved. Total freelancers: {overview_res['total_freelancers']}"
        )
        return overview_res

    def compute_skill_statistics(self, con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
        """Calculates per-skill baseline statistics."""
        freelancers_path = str(self.config.freelancers_parquet)
        skills_path = str(self.config.freelancer_skills_parquet)

        query = f"""
        WITH user_stats AS (
            SELECT 
                f.user_id,
                f.total_earnings,
                f.log_earnings,
                f.high_earner,
                f.hourly_rate,
                f.skill_count,
                s.skill_id,
                s.skill_name
            FROM read_parquet('{freelancers_path}') f
            JOIN read_parquet('{skills_path}') s ON f.user_id = s.user_id
        ),
        total_users AS (
            SELECT count(distinct user_id) as total_n FROM read_parquet('{freelancers_path}')
        )
        SELECT 
            s.skill_id,
            s.skill_name,
            count(distinct s.user_id) as freelancer_count,
            round(count(distinct s.user_id) * 1.0 / (SELECT total_n FROM total_users), 5) as prevalence,
            median(s.total_earnings) as median_earnings,
            round(avg(s.total_earnings), 2) as mean_earnings,
            median(s.log_earnings) as median_log_earnings,
            round(sum(case when s.high_earner then 1 else 0 end) * 1.0 / count(distinct s.user_id), 4) as high_earner_rate,
            round(median(s.hourly_rate), 2) as median_hourly_rate,
            round(avg(s.hourly_rate), 2) as mean_hourly_rate,
            round(median(s.skill_count), 2) as median_user_skill_count
        FROM user_stats s
        GROUP BY s.skill_id, s.skill_name
        HAVING count(distinct s.user_id) >= {self.config.min_skill_frequency}
        ORDER BY freelancer_count DESC
        """
        skill_stats_df = con.execute(query).fetchdf()

        # Save to parquet
        skill_stats_df.to_parquet(self.config.skill_statistics_parquet, index=False)
        logger.info(
            f"Skill statistics saved for {len(skill_stats_df)} skills (min frequency {self.config.min_skill_frequency})."
        )
        return skill_stats_df

    def run(self) -> Dict[str, Any]:
        self.config.ensure_directories()
        con = duckdb.connect()
        overview = self.compute_overview_and_earnings(con)
        skill_stats = self.compute_skill_statistics(con)
        con.close()
        return {
            "overview": overview,
            "skill_count": len(skill_stats),
        }


def run_skill_analytics(config: PipelineConfig = DEFAULT_CONFIG) -> Dict[str, Any]:
    analytics = SkillAnalytics(config=config)
    return analytics.run()


if __name__ == "__main__":
    run_skill_analytics()
