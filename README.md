# Skill Bundles and Freelancer Earnings

Analysis pipeline and multi-page Dash application examining which combinations of freelancer skills associate with top-tier earnings.

## Key findings

- The dataset contains 10,002 deduplicated freelancer profiles with 350,811 skill links across 3,195 skills.
- The 90th percentile platform earnings threshold is $79,497.80.
- Out of 428,795 evaluated skill pairs and triples, 404,773 combinations show statistically significant earnings associations after Benjamini-Hochberg FDR correction.
- Multivariable logistic and OLS regressions confirm these bundle premiums hold after controlling for total skill count, review volume, and country fixed effects.
- Louvain community detection partitions the co-occurrence network into 3 functional clusters (Design, Web Engineering, Systems/Backend).
- High-earning profiles use terms focused on architecture, scalability, and delivery rather than basic task lists.

## Tech stack

- Data processing: Python 3.12, DuckDB, Apache Parquet, PyArrow, Pandas, NumPy, Scipy
- Statistics and NLP: Scikit-learn, Statsmodels
- Network analysis: NetworkX, python-louvain
- Visualization: Dash, Dash Bootstrap Components, Plotly
- Testing and environment: Pytest, uv, just

## Quickstart

Use the `justfile` to run common workflow commands:

```bash
# Sync dependencies
just sync

# Run the complete analysis pipeline
just pipeline

# Start the Dash web app
just dashboard

# Run test suite
just test

# Check artifact record counts
just status
```

### Running stages directly

```bash
# Phase 1: Profiling
uv run python -m src.profiling.profiler

# Phase 2: Ingestion and normalization
uv run python -m src.ingestion.pipeline

# Phase 3: Baseline skill metrics
uv run python -m src.analysis.skills.baseline

# Phase 4: Skill combinations and regressions
uv run python -m src.analysis.combinations.vectorized_mining

# Phase 5: Skill network and communities
uv run python -m src.analysis.network.graph_builder

# Phase 6: Language and topic models
uv run python -m src.analysis.text.language_models

# Phase 7: Geographic statistics
uv run python -m src.analysis.geography.geo_analytics

# Phase 8: Integrated summary
uv run python -m src.analysis.integrated.insights_generator
```

Start the dashboard directly with:
```bash
uv run python -m dashboard.app
```
The dashboard runs at `http://localhost:8050`.

Run tests with:
```bash
uv run pytest -v
```

## Repository structure

```text
├── artifacts/
│   ├── raw_json/              # Scraped raw profile files (3,661 files)
│   └── profiling/             # Initial profiling summaries
├── data/
│   ├── parquet/               # Clean relational tables (freelancers, skills, text, portfolios)
│   └── analytical/            # Precomputed analytical outputs
├── src/
│   ├── common/                # Shared config and paths
│   ├── profiling/             # Raw data profiling
│   ├── ingestion/             # JSON to Parquet ingestion
│   └── analysis/
│       ├── skills/            # Baseline skill statistics
│       ├── combinations/      # Itemset mining and regressions
│       ├── network/           # Co-occurrence graph and Louvain clusters
│       ├── text/              # TF-IDF and LDA models
│       ├── geography/         # Country and city summaries
│       └── integrated/        # Summary findings generator
├── dashboard/
│   ├── app.py                 # Dash application entrypoint
│   └── pages/                 # Overview, bundles, network, language, geography
├── docs/
│   ├── data_dictionary.md     # Schema descriptions
│   ├── methodology.md         # Mathematical definitions
│   ├── pipeline.md            # Pipeline execution guide
│   ├── analytical_outputs.md  # Generated output descriptions
│   └── dashboard.md           # Dashboard user guide
├── tests/                     # Test suite
├── justfile                   # Task runner configuration
└── pyproject.toml             # Project dependencies
```

## Documentation

- [Data dictionary](docs/data_dictionary.md)
- [Methodology](docs/methodology.md)
- [Pipeline execution guide](docs/pipeline.md)
- [Analytical outputs](docs/analytical_outputs.md)
- [Dashboard guide](docs/dashboard.md)
