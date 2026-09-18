"""Phase 1: Dataset Profiling Module.

Streams raw JSON files chunk by chunk without loading the entire dataset into memory.
Generates comprehensive single-pass dataset profiling artifacts.
"""

import json
from collections import Counter
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

from src.common.config import DEFAULT_CONFIG, PipelineConfig


def _safe_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return f if not np.isnan(f) else None
    except (ValueError, TypeError):
        return None


def _safe_str(val: Any) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s if len(s) > 0 else None


class ProfilingAccumulator:
    """Accumulates single-pass statistics across raw JSON files."""

    def __init__(self) -> None:
        self.total_files = 0
        self.malformed_files = 0
        self.total_records = 0
        self.user_ids_seen: set[str] = set()
        self.duplicate_user_ids = 0

        # Field completeness
        self.field_presence_counts: Counter[str] = Counter()

        # Earnings
        self.earnings_list: list[float] = []
        self.hourly_rates_list: list[float] = []
        self.zero_earnings_count = 0
        self.missing_earnings_count = 0
        self.zero_rate_count = 0
        self.missing_rate_count = 0

        # Skills
        self.skills_counter: Counter[str] = Counter()
        self.user_skill_counts: list[int] = []
        self.unique_skill_ids: set[int] = set()
        self.all_skills_counter: Counter[str] = (
            Counter()
        )  # includes is_user_skill == False

        # Geography
        self.countries_counter: Counter[str] = Counter()
        self.cities_counter: Counter[str] = Counter()
        self.coordinates_present_count = 0

        # Profile text
        self.profile_text_lengths: list[int] = []
        self.tagline_present_count = 0
        self.portfolios_present_count = 0
        self.portfolio_items_count = 0

    def process_record(self, rec: dict[str, Any]) -> None:
        self.total_records += 1

        uid = _safe_str(rec.get("user_id"))
        if uid:
            if uid in self.user_ids_seen:
                self.duplicate_user_ids += 1
            else:
                self.user_ids_seen.add(uid)

        for k, v in rec.items():
            if v is not None and v != "" and v != []:
                self.field_presence_counts[k] += 1

        # Earnings
        tot_earn = _safe_float(rec.get("total_earnings"))
        if tot_earn is not None:
            self.earnings_list.append(tot_earn)
            if tot_earn == 0.0:
                self.zero_earnings_count += 1
        else:
            self.missing_earnings_count += 1

        # Hourly rate
        hr = _safe_float(rec.get("hourlyrate"))
        if hr is not None:
            self.hourly_rates_list.append(hr)
            if hr == 0.0:
                self.zero_rate_count += 1
        else:
            self.missing_rate_count += 1

        # Skills
        skills = rec.get("skills") or []
        user_explicit_skills = 0
        if isinstance(skills, list):
            for s in skills:
                if not isinstance(s, dict):
                    continue
                s_name = _safe_str(s.get("skill_name"))
                s_id = s.get("skill_id")
                is_user = s.get("is_user_skill", False)
                if s_name:
                    self.all_skills_counter[s_name] += 1
                    if is_user:
                        self.skills_counter[s_name] += 1
                        user_explicit_skills += 1
                if s_id is not None:
                    try:
                        self.unique_skill_ids.add(int(s_id))
                    except (ValueError, TypeError):
                        pass
        self.user_skill_counts.append(user_explicit_skills)

        # Geography
        country = _safe_str(rec.get("country"))
        if country:
            self.countries_counter[country] += 1
        city = _safe_str(rec.get("city"))
        if city:
            self.cities_counter[city] += 1
        loc = rec.get("location")
        if (
            isinstance(loc, dict)
            and loc.get("lat") is not None
            and loc.get("lon") is not None
        ):
            self.coordinates_present_count += 1

        # Text
        profile = _safe_str(rec.get("user_profile"))
        if profile:
            self.profile_text_lengths.append(len(profile))
        if _safe_str(rec.get("tagline")):
            self.tagline_present_count += 1
        portfolios = rec.get("portfolios") or []
        if isinstance(portfolios, list) and len(portfolios) > 0:
            self.portfolios_present_count += 1
            self.portfolio_items_count += len(portfolios)


def run_profiling(config: PipelineConfig = DEFAULT_CONFIG) -> dict[str, Any]:
    """Runs single-pass dataset profiling across all raw json files."""
    config.ensure_directories()
    raw_files = sorted(config.raw_json_dir.glob("*.json"))
    logger.info(
        f"Profiling {len(raw_files)} raw JSON files in {config.raw_json_dir}..."
    )

    accum = ProfilingAccumulator()
    for fp in raw_files:
        accum.total_files += 1
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for rec in data:
                        if isinstance(rec, dict):
                            accum.process_record(rec)
                elif isinstance(data, dict):
                    accum.process_record(data)
        except (json.JSONDecodeError, OSError, ValueError) as e:
            accum.malformed_files += 1
            logger.warning(f"Malformed JSON file {fp}: {e}")

    # Compute Summary Stats
    earnings_arr = (
        np.array(accum.earnings_list) if accum.earnings_list else np.array([0.0])
    )
    hourly_arr = (
        np.array(accum.hourly_rates_list)
        if accum.hourly_rates_list
        else np.array([0.0])
    )
    (np.array(accum.user_skill_counts) if accum.user_skill_counts else np.array([0]))
    text_len_arr = (
        np.array(accum.profile_text_lengths)
        if accum.profile_text_lengths
        else np.array([0])
    )

    dataset_summary = {
        "total_files": accum.total_files,
        "malformed_files": accum.malformed_files,
        "total_records": accum.total_records,
        "unique_users": len(accum.user_ids_seen),
        "duplicate_user_ids": accum.duplicate_user_ids,
        "field_completeness": {
            k: {
                "count": v,
                "percentage": round(100.0 * v / max(accum.total_records, 1), 2),
            }
            for k, v in accum.field_presence_counts.most_common()
        },
    }

    earnings_summary = {
        "count_present": len(earnings_arr),
        "count_missing": accum.missing_earnings_count,
        "count_zero": accum.zero_earnings_count,
        "pct_zero_or_missing": round(
            100.0
            * (accum.zero_earnings_count + accum.missing_earnings_count)
            / max(accum.total_records, 1),
            2,
        ),
        "min": float(np.min(earnings_arr)),
        "max": float(np.max(earnings_arr)),
        "mean": float(np.mean(earnings_arr)),
        "std": float(np.std(earnings_arr)),
        "median": float(np.median(earnings_arr)),
        "p25": float(np.percentile(earnings_arr, 25)),
        "p75": float(np.percentile(earnings_arr, 75)),
        "p90": float(np.percentile(earnings_arr, 90)),
        "p95": float(np.percentile(earnings_arr, 95)),
        "p99": float(np.percentile(earnings_arr, 99)),
        "iqr": float(np.percentile(earnings_arr, 75) - np.percentile(earnings_arr, 25)),
        "hourly_rates": {
            "count_present": len(hourly_arr),
            "count_missing": accum.missing_rate_count,
            "count_zero": accum.zero_rate_count,
            "min": float(np.min(hourly_arr)),
            "max": float(np.max(hourly_arr)),
            "mean": float(np.mean(hourly_arr)),
            "median": float(np.median(hourly_arr)),
            "p25": float(np.percentile(hourly_arr, 25)),
            "p75": float(np.percentile(hourly_arr, 75)),
            "p90": float(np.percentile(hourly_arr, 90)),
        },
    }

    text_summary = {
        "profiles_with_text": len(text_len_arr),
        "pct_profiles_with_text": round(
            100.0 * len(text_len_arr) / max(accum.total_records, 1), 2
        ),
        "profiles_with_tagline": accum.tagline_present_count,
        "profiles_with_portfolios": accum.portfolios_present_count,
        "total_portfolio_items": accum.portfolio_items_count,
        "text_length_mean": float(np.mean(text_len_arr)),
        "text_length_median": float(np.median(text_len_arr)),
        "text_length_max": int(np.max(text_len_arr)),
    }

    # Save JSON summaries
    with open(
        config.profiling_dir / "dataset_summary.json", "w", encoding="utf-8"
    ) as f:
        json.dump(dataset_summary, f, indent=2)

    with open(
        config.profiling_dir / "earnings_summary.json", "w", encoding="utf-8"
    ) as f:
        json.dump(earnings_summary, f, indent=2)

    with open(config.profiling_dir / "text_summary.json", "w", encoding="utf-8") as f:
        json.dump(text_summary, f, indent=2)

    # Save Skill Summary Parquet
    skills_df = pd.DataFrame(
        [
            {
                "skill_name": k,
                "user_skill_count": v,
                "all_mentions_count": accum.all_skills_counter.get(k, 0),
                "prevalence_pct": round(100.0 * v / max(accum.total_records, 1), 4),
            }
            for k, v in accum.skills_counter.most_common()
        ]
    )
    skills_df.to_parquet(config.profiling_dir / "skill_summary.parquet", index=False)

    # Save Geography Summary Parquet
    geo_rows = []
    for country, count in accum.countries_counter.most_common():
        geo_rows.append(
            {
                "country": country,
                "count": count,
                "percentage": round(100.0 * count / max(accum.total_records, 1), 2),
            }
        )
    geo_df = pd.DataFrame(geo_rows)
    geo_df.to_parquet(config.profiling_dir / "geography_summary.parquet", index=False)

    logger.info("Phase 1 Profiling completed successfully.")
    return {
        "dataset_summary": dataset_summary,
        "earnings_summary": earnings_summary,
        "text_summary": text_summary,
        "unique_skills_count": len(accum.skills_counter),
        "total_records": accum.total_records,
    }


if __name__ == "__main__":
    run_profiling()
