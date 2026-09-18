"""Pytest test suite covering profiling, ingestion, analytics, combinations, network, NLP, and artifacts."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import scipy.sparse as sp

from src.common.config import DEFAULT_CONFIG, PipelineConfig
from src.profiling.profiler import ProfilingAccumulator
from src.ingestion.pipeline import (
    _clean_float,
    _clean_int,
    _clean_str,
    IngestionPipeline,
)


def test_clean_helpers():
    assert _clean_str("  hello world  ") == "hello world"
    assert _clean_str("") is None
    assert _clean_str(None) is None

    assert _clean_float("123.45") == 123.45
    assert _clean_float(None) is None
    assert _clean_float("invalid") is None
    assert _clean_float(np.nan) is None

    assert _clean_int("10") == 10
    assert _clean_int(None) == 0
    assert _clean_int("abc") == 0


def test_profiling_accumulator():
    accum = ProfilingAccumulator()
    sample_rec = {
        "user_id": "101",
        "username": "tester",
        "total_earnings": 1000.0,
        "hourlyrate": 25.0,
        "country": "Germany",
        "city": "Berlin",
        "user_profile": "Senior Python developer",
        "skills": [
            {"skill_id": 1, "skill_name": "Python", "is_user_skill": True},
            {"skill_id": 2, "skill_name": "Django", "is_user_skill": True},
            {"skill_id": 3, "skill_name": "Docker", "is_user_skill": False},
        ],
    }
    accum.process_record(sample_rec)
    assert accum.total_records == 1
    assert "101" in accum.user_ids_seen
    assert accum.skills_counter["Python"] == 1
    assert accum.skills_counter["Django"] == 1
    assert accum.skills_counter["Docker"] == 0  # is_user_skill is False
    assert accum.all_skills_counter["Docker"] == 1


def test_parquet_artifacts_exist():
    config = DEFAULT_CONFIG
    assert config.freelancers_parquet.exists()
    assert config.freelancer_skills_parquet.exists()
    assert config.profile_text_parquet.exists()
    assert config.portfolios_parquet.exists()


def test_analytical_artifacts_exist():
    config = DEFAULT_CONFIG
    assert config.overview_metrics_json.exists()
    assert config.earnings_distribution_parquet.exists()
    assert config.skill_statistics_parquet.exists()
    assert config.skill_combinations_parquet.exists()
    assert config.combination_regression_json.exists()
    assert config.network_nodes_parquet.exists()
    assert config.network_edges_parquet.exists()
    assert config.network_communities_parquet.exists()
    assert config.text_terms_parquet.exists()
    assert config.topics_parquet.exists()
    assert config.geographic_statistics_parquet.exists()
    assert config.integrated_insights_json.exists()


def test_freelancers_schema_and_invariants():
    df = pd.read_parquet(DEFAULT_CONFIG.freelancers_parquet)
    assert len(df) > 0
    assert "user_id" in df.columns
    assert "high_earner" in df.columns
    assert "total_earnings" in df.columns
    assert "log_earnings" in df.columns

    # High earner proportion should be roughly 10%
    high_rate = df["high_earner"].mean()
    assert 0.08 <= high_rate <= 0.12

    # Log earnings invariant: log_earnings == log1p(total_earnings)
    sample = df.sample(min(100, len(df)), random_state=42)
    expected_logs = np.log1p(sample["total_earnings"])
    np.testing.assert_allclose(sample["log_earnings"], expected_logs, rtol=1e-4)


def test_skill_combinations_invariants():
    df = pd.read_parquet(DEFAULT_CONFIG.skill_combinations_parquet)
    assert len(df) > 0

    # Statistical bounds
    assert (df["support"] > 0).all()
    assert (df["support"] <= 1).all()
    assert (df["lift"] > 0).all()
    assert (df["odds_ratio"] > 0).all()
    assert (df["p_value"] >= 0).all()
    assert (df["p_value"] <= 1).all()
    assert (df["adjusted_p_value"] >= 0).all()
    assert (df["adjusted_p_value"] <= 1).all()

    # CI ordering
    assert (df["ci_upper"] >= df["ci_lower"]).all()


def test_network_and_communities():
    nodes_df = pd.read_parquet(DEFAULT_CONFIG.network_nodes_parquet)
    edges_df = pd.read_parquet(DEFAULT_CONFIG.network_edges_parquet)
    comm_df = pd.read_parquet(DEFAULT_CONFIG.network_communities_parquet)

    assert len(nodes_df) > 0
    assert len(edges_df) > 0
    assert len(comm_df) > 0

    assert "x" in nodes_df.columns and "y" in nodes_df.columns
    assert "community_id" in nodes_df.columns
    assert "betweenness_centrality" in nodes_df.columns
    assert "bridge_score" in nodes_df.columns


def test_text_and_topics():
    terms_df = pd.read_parquet(DEFAULT_CONFIG.text_terms_parquet)
    topics_df = pd.read_parquet(DEFAULT_CONFIG.topics_parquet)

    assert len(terms_df) > 0
    assert len(topics_df) == 8

    assert "term" in terms_df.columns
    assert "log_diff_score" in terms_df.columns
    assert "topic_label" in topics_df.columns
    assert "high_earner_rate" in topics_df.columns


def test_integrated_insights_json():
    with open(DEFAULT_CONFIG.integrated_insights_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "dataset_overview" in data
    assert "top_skill_bundles" in data
    assert "key_takeaways" in data
    assert len(data["key_takeaways"]) > 0
