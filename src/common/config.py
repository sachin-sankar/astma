"""Unified configuration settings and paths for the analysis pipeline."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    """Central configuration for paths, parameters, and statistical thresholds."""

    # Project Root and Data Paths
    project_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parents[2]
    )
    raw_json_dir: Path = field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[2] / "artifacts" / "raw_json"
        )
    )
    profiling_dir: Path = field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[2] / "artifacts" / "profiling"
        )
    )
    parquet_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parents[2] / "data" / "parquet"
    )
    analytical_dir: Path = field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[2] / "data" / "analytical"
        )
    )

    # Parquet Subdirectories / Files
    freelancers_parquet: Path = field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[2]
            / "data"
            / "parquet"
            / "freelancers.parquet"
        )
    )
    freelancer_skills_parquet: Path = field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[2]
            / "data"
            / "parquet"
            / "freelancer_skills.parquet"
        )
    )
    profile_text_parquet: Path = field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[2]
            / "data"
            / "parquet"
            / "profile_text.parquet"
        )
    )
    portfolios_parquet: Path = field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[2]
            / "data"
            / "parquet"
            / "portfolios.parquet"
        )
    )

    # Analytical Artifact Files
    overview_metrics_json: Path = field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[2]
            / "data"
            / "analytical"
            / "overview_metrics.json"
        )
    )
    earnings_distribution_parquet: Path = field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[2]
            / "data"
            / "analytical"
            / "earnings_distribution.parquet"
        )
    )
    skill_statistics_parquet: Path = field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[2]
            / "data"
            / "analytical"
            / "skill_statistics.parquet"
        )
    )
    skill_combinations_parquet: Path = field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[2]
            / "data"
            / "analytical"
            / "skill_combinations.parquet"
        )
    )
    combination_regression_json: Path = field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[2]
            / "data"
            / "analytical"
            / "combination_regression.json"
        )
    )
    network_nodes_parquet: Path = field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[2]
            / "data"
            / "analytical"
            / "network_nodes.parquet"
        )
    )
    network_edges_parquet: Path = field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[2]
            / "data"
            / "analytical"
            / "network_edges.parquet"
        )
    )
    network_communities_parquet: Path = field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[2]
            / "data"
            / "analytical"
            / "network_communities.parquet"
        )
    )
    text_terms_parquet: Path = field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[2]
            / "data"
            / "analytical"
            / "text_terms.parquet"
        )
    )
    topics_parquet: Path = field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[2]
            / "data"
            / "analytical"
            / "topics.parquet"
        )
    )
    geographic_statistics_parquet: Path = field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[2]
            / "data"
            / "analytical"
            / "geographic_statistics.parquet"
        )
    )
    integrated_insights_json: Path = field(
        default_factory=lambda: (
            Path(__file__).resolve().parents[2]
            / "data"
            / "analytical"
            / "integrated_insights.json"
        )
    )

    # Statistical & Modeling Parameters
    high_earner_percentile: float = 0.90
    min_skill_frequency: int = 15
    min_combination_support: float = 0.002  # e.g., ~70 freelancers in 36k
    min_combination_count: int = 20
    fdr_alpha: float = 0.05
    network_min_edge_weight: int = 25
    network_max_nodes: int = 150
    lda_num_topics: int = 8
    random_seed: int = 42

    # Geography thresholds
    min_country_freelancers: int = 15
    min_city_freelancers: int = 5

    def ensure_directories(self) -> None:
        """Create all required data and artifact directories."""
        self.profiling_dir.mkdir(parents=True, exist_ok=True)
        self.parquet_dir.mkdir(parents=True, exist_ok=True)
        self.analytical_dir.mkdir(parents=True, exist_ok=True)


DEFAULT_CONFIG = PipelineConfig()
