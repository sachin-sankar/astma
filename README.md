# Skill Bundles and Freelancer Earnings

> An end-to-end reproducible analytical pipeline and interactive multi-page Dash application investigating **which combinations of freelancer-selected skills are disproportionately associated with high-earning freelancers**.

---

## 🚀 Key Highlights & Findings

- **Dataset Scale**: Analyzed 10,002 deduplicated freelancer profiles with 350,811 skill links across 3,195 unique skills. Designed for scalability up to 3M+ records under 16GB RAM constraints using columnar Parquet and vectorized sparse operations.
- **High-Earner Threshold (90th Percentile)**: Defined at **$79,497.80 USD** lifetime platform earnings.
- **Skill Combination Synergies**: Evaluated over 428,000 candidate skill pairs and triples using support, lift, Haldane-Anscombe Odds Ratios, 95% confidence intervals, Chi-square tests, and Benjamini-Hochberg FDR correction.
- **Econometric Controls**: Validated bundle associations using multivariable logistic regression and OLS log-earnings models controlling for skill count, review volume, and country fixed effects.
- **Skill Topology & Communities**: Modeled network co-occurrences with Louvain community detection (3 major functional clusters) and identified critical bridge skills.
- **Language Patterns & LDA**: Uncovered high-earner differential vocabulary (TF-IDF log-odds) and trained an 8-topic Latent Dirichlet Allocation (LDA) model.

---

## 🛠 Tech Stack

- **Data Processing & Storage**: Python 3.12, DuckDB, Apache Parquet, PyArrow, Pandas, NumPy, Scipy Sparse.
- **Machine Learning & NLP**: Scikit-Learn (TF-IDF, LDA), Statsmodels (Logistic Regression, OLS, Benjamini-Hochberg FDR).
- **Network Analysis**: NetworkX, python-louvain (`community`).
- **Interactive Visualization**: Dash, Dash Bootstrap Components, Plotly.
- **Testing & Packaging**: Pytest, uv.

---

## 📦 Quickstart

A `justfile` is provided for running tasks:

```bash
# Synchronize virtual environment
just sync

# Run full analytical pipeline end-to-end
just pipeline

# Launch Dash interactive web dashboard
just dashboard

# Run automated pytest suite
just test

# Inspect pipeline artifacts & row counts
just status
```

### Manual Pipeline Invocation with UV
```bash
# Phase 1: Profiling
uv run python -m src.profiling.profiler

# Phase 2: Ingestion & Relational Normalization
uv run python -m src.ingestion.pipeline

# Phase 3: Baseline Analytics
uv run python -m src.analysis.skills.baseline

# Phase 4: Skill Bundles & Regressions
uv run python -m src.analysis.combinations.vectorized_mining

# Phase 5: Skill Co-occurrence Network
uv run python -m src.analysis.network.graph_builder

# Phase 6: Profile Language & Topics
uv run python -m src.analysis.text.language_models

# Phase 7: Geographic Analysis
uv run python -m src.analysis.geography.geo_analytics

# Phase 8: Integrated Insights
uv run python -m src.analysis.integrated.insights_generator
```

### 3. Launch Interactive Dashboard
```bash
uv run python -m dashboard.app
```
Access the application at `http://localhost:8050`.

### 4. Run Test Suite
```bash
uv run pytest -v
```

---

## 📂 Repository Structure

```text
├── artifacts/
│   ├── raw_json/              # Scraped JSON profile batches (3,661 files)
│   └── profiling/             # Single-pass profiling summaries
├── data/
│   ├── parquet/               # Normalized relational tables (freelancers, skills, text, portfolios)
│   └── analytical/            # Precomputed analytical outputs for Dash
├── src/
│   ├── common/                # Unified config & paths
│   ├── profiling/             # Phase 1 profiler
│   ├── ingestion/             # Phase 2 JSON to Parquet ingestion pipeline
│   └── analysis/
│       ├── skills/            # Phase 3 baseline skill metrics
│       ├── combinations/      # Phase 4 vectorized association mining & regressions
│       ├── network/           # Phase 5 NetworkX graph & Louvain clustering
│       ├── text/              # Phase 6 Differential TF-IDF & LDA topic models
│       ├── geography/         # Phase 7 Country & city analytics
│       └── integrated/        # Phase 8 Master narrative synthesizer
├── dashboard/
│   ├── app.py                 # Multi-page Dash entrypoint
│   └── pages/                 # Overview, Skill Bundles, Network, Language, Geography
├── docs/
│   ├── data_dictionary.md     # Full schema documentation
│   ├── methodology.md         # Mathematical & statistical formulations
│   ├── pipeline.md            # Execution guide
│   ├── analytical_outputs.md  # Detailed summary of analytical artifacts
│   └── dashboard.md           # Guide to Dash interactive features
├── tests/                     # Unit and integration test suite
└── pyproject.toml             # uv configuration and dependencies
```

---

## 📚 Documentation Links
- [Data Dictionary](docs/data_dictionary.md)
- [Methodology & Formulations](docs/methodology.md)
- [Pipeline Execution Guide](docs/pipeline.md)
- [Analytical Outputs](docs/analytical_outputs.md)
- [Dashboard Guide](docs/dashboard.md)
