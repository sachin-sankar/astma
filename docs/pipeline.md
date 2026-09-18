# Pipeline Execution Guide

Instructions for running the data processing pipeline, analytical models, and dashboard.

## Prerequisites

- Python 3.12+
- `uv` and `just`

```bash
uv sync
```

## Running stages individually

### Phase 1: Dataset profiling
Streams raw JSON files and computes initial distribution summaries:
```bash
uv run python -m src.profiling.profiler
```
Outputs: `artifacts/profiling/dataset_summary.json`, `earnings_summary.json`, `text_summary.json`, `skill_summary.parquet`, `geography_summary.parquet`.

### Phase 2: Ingestion and normalization
Parses raw files, removes duplicate profiles, sets the 90th percentile earnings threshold, and writes Parquet tables:
```bash
uv run python -m src.ingestion.pipeline
```
Outputs: `data/parquet/{freelancers,freelancer_skills,profile_text,portfolios}.parquet`.

### Phase 3: Baseline skill statistics
Calculates skill frequencies, prevalence, and median earnings using DuckDB:
```bash
uv run python -m src.analysis.skills.baseline
```
Outputs: `data/analytical/overview_metrics.json`, `earnings_distribution.parquet`, `skill_statistics.parquet`.

### Phase 4: Skill combinations and regressions
Mines pairs and triples, calculates support, lift, odds ratios with 95% CIs, Chi-square p-values, FDR corrections, and controlled regressions:
```bash
uv run python -m src.analysis.combinations.vectorized_mining
```
Outputs: `data/analytical/skill_combinations.parquet`, `combination_regression.json`.

### Phase 5: Skill network and community detection
Builds the co-occurrence graph, computes network centralities, Louvain communities, and precomputes 2D layout coordinates:
```bash
uv run python -m src.analysis.network.graph_builder
```
Outputs: `data/analytical/network_{nodes,edges,communities}.parquet`.

### Phase 6: Language and topic models
Extracts differential TF-IDF unigrams and bigrams, then fits an 8-topic LDA model:
```bash
uv run python -m src.analysis.text.language_models
```
Outputs: `data/analytical/text_terms.parquet`, `data/analytical/topics.parquet`.

### Phase 7: Geographic analysis
Aggregates metrics by country and metropolitan area:
```bash
uv run python -m src.analysis.geography.geo_analytics
```
Outputs: `data/analytical/geographic_statistics.parquet`, `city_statistics.parquet`.

### Phase 8: Integrated summary
Synthesizes findings into a single summary artifact:
```bash
uv run python -m src.analysis.integrated.insights_generator
```
Outputs: `data/analytical/integrated_insights.json`.

## Launching the Dash application

Start the web application:
```bash
uv run python -m dashboard.app
```
Open `http://localhost:8050` in a browser.

Application pages:
1. Overview (`/`): Summary metrics, earnings distribution, and skill counts per profile.
2. Skill bundles (`/skill-bundles`): Interactive combination filter, lift scatter plot, controlled regression effect sizes, and data table.
3. Skill network (`/skill-network`): Force-directed co-occurrence graph with Louvain clusters and bridge skills.
4. Profile language (`/profile-language`): Differential TF-IDF terms and LDA topic breakdowns.
5. Geography (`/geography`): Global map, country rankings, and city table.

## Running tests

Run the test suite:
```bash
uv run pytest -v
```
