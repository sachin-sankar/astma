"""Ingestion package."""

from src.ingestion.pipeline import IngestionPipeline, run_ingestion

__all__ = ["IngestionPipeline", "run_ingestion"]
