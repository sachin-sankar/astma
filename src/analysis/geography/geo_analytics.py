"""Phase 7: Geographic Analysis of Skills, Bundles, and Earnings.

- Aggregates freelancer profiles by Country and City using DuckDB.
- Computes: Freelancer Count, Median Earnings, Mean Earnings, High Earner Rate, Median Hourly Rate.
- Identifies Top 5 Dominant Skills per Country.
- Identifies Dominant High-Earning Skill Bundles per Country.
- Prepares normalized ISO country codes and coordinates for Dash interactive maps.
- Saves output to `data/analytical/geographic_statistics.parquet`.
"""

from typing import Any, Dict, List

import duckdb
import pandas as pd
from loguru import logger

from src.common.config import DEFAULT_CONFIG, PipelineConfig


class GeographicAnalyzer:
    """Computes geographic variations across countries and cities."""

    def __init__(self, config: PipelineConfig = DEFAULT_CONFIG):
        self.config = config

    def run(self) -> Dict[str, Any]:
        self.config.ensure_directories()
        con = duckdb.connect()

        freelancers_path = str(self.config.freelancers_parquet)
        skills_path = str(self.config.freelancer_skills_parquet)

        logger.info("Computing country-level aggregations...")
        country_query = f"""
        WITH country_base AS (
            SELECT 
                country,
                count(*) as freelancer_count,
                round(sum(case when high_earner then 1 else 0 end) * 1.0 / count(*), 4) as high_earner_rate,
                sum(case when high_earner then 1 else 0 end) as high_earner_count,
                median(total_earnings) as median_earnings,
                round(avg(total_earnings), 2) as mean_earnings,
                median(hourly_rate) as median_hourly_rate,
                round(avg(hourly_rate), 2) as mean_hourly_rate,
                median(skill_count) as median_skill_count,
                median(review_count) as median_review_count,
                avg(latitude) as avg_lat,
                avg(longitude) as avg_lon
            FROM read_parquet('{freelancers_path}')
            WHERE country IS NOT NULL AND country != 'Unknown'
            GROUP BY country
            HAVING count(*) >= {self.config.min_country_freelancers}
        ),
        country_skills AS (
            SELECT 
                f.country,
                s.skill_name,
                count(distinct f.user_id) as skill_user_cnt,
                row_number() OVER (PARTITION BY f.country ORDER BY count(distinct f.user_id) DESC) as skill_rank
            FROM read_parquet('{freelancers_path}') f
            JOIN read_parquet('{skills_path}') s ON f.user_id = s.user_id
            WHERE f.country IN (SELECT country FROM country_base)
            GROUP BY f.country, s.skill_name
        ),
        top_skills_per_country AS (
            SELECT 
                country,
                string_agg(skill_name || ' (' || skill_user_cnt || ')', ', ' ORDER BY skill_rank) as top_skills
            FROM country_skills
            WHERE skill_rank <= 5
            GROUP BY country
        )
        SELECT 
            cb.*,
            coalesce(ts.top_skills, '') as top_skills
        FROM country_base cb
        LEFT JOIN top_skills_per_country ts ON cb.country = ts.country
        ORDER BY cb.freelancer_count DESC
        """
        country_df = con.execute(country_query).fetchdf()

        logger.info(f"Computed geographic statistics for {len(country_df)} countries.")

        # Compute City-level breakdown for top countries
        city_query = f"""
        SELECT 
            country,
            city,
            count(*) as freelancer_count,
            round(sum(case when high_earner then 1 else 0 end) * 1.0 / count(*), 4) as high_earner_rate,
            median(total_earnings) as median_earnings,
            round(avg(total_earnings), 2) as mean_earnings,
            median(hourly_rate) as median_hourly_rate,
            avg(latitude) as latitude,
            avg(longitude) as longitude
        FROM read_parquet('{freelancers_path}')
        WHERE country IS NOT NULL AND country != 'Unknown' 
          AND city IS NOT NULL AND city != 'Unknown'
        GROUP BY country, city
        HAVING count(*) >= {self.config.min_city_freelancers}
        ORDER BY freelancer_count DESC
        """
        city_df = con.execute(city_query).fetchdf()
        con.close()

        # Save Geographic Statistics Parquet
        country_df.to_parquet(self.config.geographic_statistics_parquet, index=False)

        # Save City Statistics Parquet
        city_path = self.config.analytical_dir / "city_statistics.parquet"
        city_df.to_parquet(city_path, index=False)

        logger.info(
            f"Saved country statistics to {self.config.geographic_statistics_parquet} and city statistics ({len(city_df)} cities) to {city_path}."
        )

        return {
            "countries_count": len(country_df),
            "cities_count": len(city_df),
        }


def run_geographic_analysis(config: PipelineConfig = DEFAULT_CONFIG) -> Dict[str, Any]:
    analyzer = GeographicAnalyzer(config=config)
    return analyzer.run()


if __name__ == "__main__":
    run_geographic_analysis()
