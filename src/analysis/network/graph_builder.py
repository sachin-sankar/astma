"""Phase 5: Skill Co-occurrence Network, Centrality, and Louvain Communities.

- Builds skill co-occurrence graph via NetworkX.
- Filters edges and nodes for fast rendering and high modularity.
- Calculates node centrality metrics: Degree, Weighted Degree (Strength), Betweenness, Closeness.
- Runs Louvain Community Detection to discover functional skill ecosystems.
- Identifies "bridge skills" (high betweenness relative to degree).
- Precomputes 2D force-directed layout coordinates (Fruchterman-Reingold / Spring layout) with fixed seed for instant visualization.
"""

import json
from typing import Any, Dict, List, Tuple

import community as community_louvain
import duckdb
import networkx as nx
import numpy as np
import pandas as pd
from loguru import logger

from src.common.config import DEFAULT_CONFIG, PipelineConfig


class SkillNetworkAnalyzer:
    """Constructs and analyzes the skill co-occurrence network."""

    def __init__(self, config: PipelineConfig = DEFAULT_CONFIG):
        self.config = config

    def build_network(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Constructs graph, computes centrality, Louvain communities, and precomputed 2D layout."""
        self.config.ensure_directories()
        con = duckdb.connect()

        # Load skill stats
        skills_stat_df = con.execute(f"""
        SELECT skill_id, skill_name, freelancer_count, median_earnings, high_earner_rate, median_hourly_rate
        FROM read_parquet('{self.config.skill_statistics_parquet}')
        ORDER BY freelancer_count DESC
        """).fetchdf()

        # Load edges (pairs co-occurrence)
        edges_query = f"""
        WITH top_skills AS (
            SELECT skill_id, skill_name 
            FROM read_parquet('{self.config.skill_statistics_parquet}')
            ORDER BY freelancer_count DESC
            LIMIT {self.config.network_max_nodes}
        ),
        user_top_skills AS (
            SELECT s.user_id, s.skill_name 
            FROM read_parquet('{self.config.freelancer_skills_parquet}') s
            JOIN top_skills t ON s.skill_name = t.skill_name
        )
        SELECT 
            s1.skill_name as source,
            s2.skill_name as target,
            count(distinct s1.user_id) as weight
        FROM user_top_skills s1
        JOIN user_top_skills s2 ON s1.user_id = s2.user_id AND s1.skill_name < s2.skill_name
        GROUP BY s1.skill_name, s2.skill_name
        HAVING count(distinct s1.user_id) >= {self.config.network_min_edge_weight}
        ORDER BY weight DESC
        """
        edges_df = con.execute(edges_query).fetchdf()
        con.close()

        logger.info(
            f"Built network graph with {len(edges_df)} edges (min weight >= {self.config.network_min_edge_weight})."
        )

        # Build NetworkX graph
        G = nx.Graph()

        # Add edges with weights
        for _, row in edges_df.iterrows():
            G.add_edge(row["source"], row["target"], weight=float(row["weight"]))

        # Filter nodes in G
        active_nodes = set(G.nodes())
        node_meta = skills_stat_df[
            skills_stat_df["skill_name"].isin(active_nodes)
        ].copy()
        meta_dict = node_meta.set_index("skill_name").to_dict(orient="index")

        # Centrality metrics
        deg_centrality = nx.degree_centrality(G)
        weighted_degree = dict(G.degree(weight="weight"))
        betweenness = nx.betweenness_centrality(
            G, weight="weight", seed=self.config.random_seed
        )
        closeness = nx.closeness_centrality(G)

        # Louvain Community Detection
        partition = community_louvain.best_partition(
            G, weight="weight", random_state=self.config.random_seed
        )
        modularity = community_louvain.modularity(partition, G, weight="weight")
        logger.info(
            f"Louvain Community Detection modularity: {modularity:.4f}, total communities: {len(set(partition.values()))}"
        )

        # Precompute 2D Spring Layout (Fixed Seed)
        pos = nx.spring_layout(
            G, weight="weight", seed=self.config.random_seed, k=0.35, iterations=100
        )

        # Construct Nodes DataFrame
        node_rows: List[Dict[str, Any]] = []
        for node in G.nodes():
            info = meta_dict.get(node, {})
            deg = float(deg_centrality.get(node, 0.0))
            w_deg = float(weighted_degree.get(node, 0.0))
            betw = float(betweenness.get(node, 0.0))
            close = float(closeness.get(node, 0.0))
            comm_id = int(partition.get(node, 0))
            x, y = pos.get(node, (0.0, 0.0))

            # Bridge score: high betweenness relative to degree
            bridge_score = betw / (deg + 1e-5)

            node_rows.append(
                {
                    "skill_name": node,
                    "community_id": comm_id,
                    "freelancer_count": int(info.get("freelancer_count", 0)),
                    "median_earnings": float(info.get("median_earnings", 0.0)),
                    "high_earner_rate": float(info.get("high_earner_rate", 0.0)),
                    "median_hourly_rate": float(info.get("median_hourly_rate", 0.0)),
                    "degree_centrality": round(deg, 4),
                    "weighted_degree": int(w_deg),
                    "betweenness_centrality": round(betw, 6),
                    "closeness_centrality": round(close, 4),
                    "bridge_score": round(bridge_score, 4),
                    "x": float(x),
                    "y": float(y),
                }
            )

        nodes_df = pd.DataFrame(node_rows).sort_values(
            by=["community_id", "freelancer_count"], ascending=[True, False]
        )

        # Community Summary DataFrame
        comm_summary = (
            nodes_df.groupby("community_id")
            .agg(
                num_skills=("skill_name", "count"),
                total_freelancers=("freelancer_count", "sum"),
                avg_high_earner_rate=("high_earner_rate", "mean"),
                median_earnings=("median_earnings", "median"),
                top_skills=("skill_name", lambda s: ", ".join(list(s)[:5])),
            )
            .reset_index()
        )

        # Save Parquet artifacts
        nodes_df.to_parquet(self.config.network_nodes_parquet, index=False)
        edges_df.to_parquet(self.config.network_edges_parquet, index=False)
        comm_summary.to_parquet(self.config.network_communities_parquet, index=False)

        logger.info(
            f"Saved network nodes ({len(nodes_df)}), edges ({len(edges_df)}), and communities ({len(comm_summary)})."
        )
        return nodes_df, edges_df, comm_summary

    def run(self) -> Dict[str, Any]:
        nodes_df, edges_df, comm_df = self.build_network()
        return {
            "node_count": len(nodes_df),
            "edge_count": len(edges_df),
            "community_count": len(comm_df),
        }


def run_network_analysis(config: PipelineConfig = DEFAULT_CONFIG) -> Dict[str, Any]:
    analyzer = SkillNetworkAnalyzer(config=config)
    return analyzer.run()


if __name__ == "__main__":
    run_network_analysis()
