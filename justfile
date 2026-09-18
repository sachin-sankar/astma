# Skill Bundles Analysis & Dashboard Justfile

default:
    @just --list

# Synchronize python dependencies with uv
sync:
    uv sync

# Run all pipeline phases end-to-end
pipeline: profiling ingestion baseline combinations network text geography insights
    @echo "Full analytical pipeline successfully completed."

# Phase 1: Stream raw JSON files and compute dataset profiling
profiling:
    uv run python -m src.profiling.profiler

# Phase 2: Ingest, deduplicate and normalize raw JSON into Parquet tables
ingestion:
    uv run python -m src.ingestion.pipeline

# Phase 3: Baseline skill statistics and earnings distributions
baseline:
    uv run python -m src.analysis.skills.baseline

# Phase 4: Skill combinations, FDR correction, and controlled regressions
combinations:
    uv run python -m src.analysis.combinations.vectorized_mining

# Phase 5: Skill co-occurrence network, centrality, and Louvain communities
network:
    uv run python -m src.analysis.network.graph_builder

# Phase 6: Profile language differential TF-IDF and LDA topic modeling
text:
    uv run python -m src.analysis.text.language_models

# Phase 7: Geographic statistics by country and metropolitan area
geography:
    uv run python -m src.analysis.geography.geo_analytics

# Phase 8: Integrated cross-domain insights generator
insights:
    uv run python -m src.analysis.integrated.insights_generator

# Launch the interactive multi-page Dash application
dashboard:
    uv run python -m dashboard.app

# Run pytest test suite
test:
    uv run pytest -v

# Run pytest with code coverage
test-cov:
    uv run pytest -v --cov=src --cov=dashboard

# Check artifact status and row counts
status:
    @uv run python -c "import duckdb, json; from src.common.config import DEFAULT_CONFIG; con = duckdb.connect(); print('--- Pipeline Artifacts Status ---'); print(f'Freelancers: {con.execute(f\"SELECT count(*) FROM read_parquet(\'{DEFAULT_CONFIG.freelancers_parquet}\')\").fetchone()[0]:,}'); print(f'Skill Links: {con.execute(f\"SELECT count(*) FROM read_parquet(\'{DEFAULT_CONFIG.freelancer_skills_parquet}\')\").fetchone()[0]:,}'); print(f'Combinations: {con.execute(f\"SELECT count(*) FROM read_parquet(\'{DEFAULT_CONFIG.skill_combinations_parquet}\')\").fetchone()[0]:,}'); print(f'Network Nodes: {con.execute(f\"SELECT count(*) FROM read_parquet(\'{DEFAULT_CONFIG.network_nodes_parquet}\')\").fetchone()[0]:,}'); print(f'TF-IDF Terms: {con.execute(f\"SELECT count(*) FROM read_parquet(\'{DEFAULT_CONFIG.text_terms_parquet}\')\").fetchone()[0]:,}'); print(f'Countries: {con.execute(f\"SELECT count(*) FROM read_parquet(\'{DEFAULT_CONFIG.geographic_statistics_parquet}\')\").fetchone()[0]:,}'); con.close()"
