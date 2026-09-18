# Pipeline Execution Guide

This guide describes how to run the end-to-end data pipeline from raw JSON scraping artifacts to normalized Parquet tables, analytical artifacts, and the interactive dashboard.

---

## Prerequisites
- Python 3.12+ installed.
- `uv` package and project manager.

```bash
# Install and synchronize virtual environment
uv sync
```

---

## 1. Running the Pipeline Steps Individually

### Phase 1: Dataset Profiling
Streams raw JSON files chunk-by-chunk and generates initial single-pass distribution summaries:
```bash
uv run python -m src.profiling.profiler
```
*Outputs*: `artifacts/profiling/dataset_summary.json`, `earnings_summary.json`, `text_summary.json`, `skill_summary.parquet`, `geography_summary.parquet`.

### Phase 2: Ingestion & Relational Normalization
Parses raw JSON, deduplicates user profiles, computes the empirical 90th percentile high-earner threshold, and generates typed Parquet tables:
```bash
uv run python -m src.ingestion.pipeline
```
*Outputs*: `data/parquet/{freelancers,freelancer_skills,profile_text,portfolios}.parquet`.

### Phase 3: Baseline Skill & Earnings Analytics
Computes aggregate frequencies, prevalence, median earnings, and baseline hourly rates using DuckDB:
```bash
uv run python -m src.analysis.skills.baseline
```
*Outputs*: `data/analytical/overview_metrics.json`, `earnings_distribution.parquet`, `skill_statistics.parquet`.

### Phase 4: Skill Combinations, Association Mining & Econometric Regressions
Mines frequent pairs and triples, computes support, lift, Odds Ratios with 95% CIs, Chi-square p-values, Benjamini-Hochberg FDR correction, and controlled regressions:
```bash
uv run python -m src.analysis.combinations.vectorized_mining
```
*Outputs*: `data/analytical/skill_combinations.parquet`, `combination_regression.json`.

### Phase 5: Skill Network & Louvain Community Detection
Builds the co-occurrence graph, computes network centralities, Louvain communities, bridge skills, and precomputes 2D layout coordinates:
```bash
uv run python -m src.analysis.network.graph_builder
```
*Outputs*: `data/analytical/network_{nodes,edges,communities}.parquet`.

### Phase 6: Profile Language & LDA Topic Modeling
Performs differential TF-IDF extraction (unigrams/bigrams) and trains an 8-topic LDA model:
```bash
uv run python -m src.analysis.text.language_models
```
*Outputs*: `data/analytical/text_terms.parquet`, `data/analytical/topics.parquet`.

### Phase 7: Geographic Analysis
Calculates country-level and metropolitan aggregations:
```bash
uv run python -m src.analysis.geography.geo_analytics
```
*Outputs*: `data/analytical/geographic_statistics.parquet`, `city_statistics.parquet`.

### Phase 8: Integrated Insights Synthesis
Compiles top findings into a single summary artifact:
```bash
uv run python -m src.analysis.integrated.insights_generator
```
*Outputs*: `data/analytical/integrated_insights.json`.

---

## 2. Launching the Interactive Dash Application

Start the Dash web application:
```bash
uv run python -m dashboard.app
```
Open your browser at `http://127.0.0.1:8050` or `http://localhost:8050`.

Pages included:
1. **Overview (`/`)**: High-level market metrics, log-earnings distribution, skills per user, popular vs high-earning skills.
2. **Skill Bundles (`/skill-bundles`)**: Interactive combination filtering, scatter matrix (Lift vs High-Earner Rate), controlled regression effect sizes, and sortable data table.
3. **Skill Network (`/skill-network`)**: Force-directed topological graph, community cluster filters, node coloring, and bridge skill leaderboards.
4. **Profile Language (`/profile-language`)**: High vs non-high earner distinctive vocabulary bars and LDA topic archetypes.
5. **Geography (`/geography`)**: Global choropleth map, regional comparisons, and city-level drill-down tables.

---

## 3. Running Automated Tests

Run the full pytest suite:
```bash
uv run pytest -v
```
