# Data Dictionary

This document defines schemas, data types, constraints, and descriptions for all raw, normalized, and analytical datasets in the pipeline.

---

## 1. Normalized Relational Tables (`data/parquet/`)

### `freelancers.parquet`
Primary demographic, earnings, and reputation table per unique freelancer.

| Field | Type | Description |
|---|---|---|
| `user_id` | `VARCHAR` | Unique identifier for the freelancer profile |
| `username` | `VARCHAR` | Account handle/slug |
| `public_name` | `VARCHAR` | Public display name |
| `country` | `VARCHAR` | Self-reported primary country |
| `city` | `VARCHAR` | Self-reported primary city |
| `hourly_rate` | `DOUBLE` | Stated hourly rate in USD |
| `total_earnings` | `DOUBLE` | Platform cumulative earnings in USD |
| `log_earnings` | `DOUBLE` | Natural logarithm transformed earnings $\ln(\text{total\_earnings} + 1)$ |
| `high_earner` | `BOOLEAN` | True if `total_earnings` $\ge$ 90th percentile threshold ($79,498) |
| `reputation` | `DOUBLE` | Platform reputation score |
| `review_count` | `BIGINT` | Number of completed client reviews |
| `stars` | `DOUBLE` | Average feedback star rating (out of 5.0) |
| `score` | `DOUBLE` | Platform algorithmic score |
| `skill_count` | `BIGINT` | Count of explicit user-selected skills |
| `latitude` | `DOUBLE` | Geographic latitude coordinate |
| `longitude` | `DOUBLE` | Geographic longitude coordinate |

---

### `freelancer_skills.parquet`
Normalized many-to-many relationship table between freelancers and explicitly selected skills (`is_user_skill == True`).

| Field | Type | Description |
|---|---|---|
| `user_id` | `VARCHAR` | Foreign key referencing `freelancers.user_id` |
| `skill_id` | `BIGINT` | Platform canonical numeric skill identifier |
| `skill_name` | `VARCHAR` | Cleaned and trimmed skill name (e.g. `React.js`, `Python`) |

---

### `profile_text.parquet`
Textual descriptions and portfolio content.

| Field | Type | Description |
|---|---|---|
| `user_id` | `VARCHAR` | Foreign key referencing `freelancers.user_id` |
| `profile_text` | `VARCHAR` | Primary profile biography/description |
| `tagline` | `VARCHAR` | One-line headline/tagline |
| `portfolio_text` | `VARCHAR` | Aggregated text of all portfolio titles and descriptions |
| `combined_text` | `VARCHAR` | Concatenated and cleaned corpus string for NLP analysis |

---

### `portfolios.parquet`
Individual portfolio items.

| Field | Type | Description |
|---|---|---|
| `user_id` | `VARCHAR` | Foreign key referencing `freelancers.user_id` |
| `portfolio_id` | `BIGINT` | 1-indexed portfolio item identifier per user |
| `title` | `VARCHAR` | Title of the portfolio entry |
| `description` | `VARCHAR` | Detailed description of the portfolio entry |

---

## 2. Analytical Output Artifacts (`data/analytical/`)

### `skill_statistics.parquet`
Individual skill frequencies and earnings associations.

| Field | Type | Description |
|---|---|---|
| `skill_id` | `BIGINT` | Canonical skill ID |
| `skill_name` | `VARCHAR` | Skill name |
| `freelancer_count` | `BIGINT` | Total freelancers listing this skill |
| `prevalence` | `DOUBLE` | Frequency as a proportion of all freelancers $\frac{N_{\text{skill}}}{N_{\text{total}}}$ |
| `median_earnings` | `DOUBLE` | Median total earnings of freelancers with this skill |
| `mean_earnings` | `DOUBLE` | Mean total earnings of freelancers with this skill |
| `median_log_earnings` | `DOUBLE` | Median log earnings |
| `high_earner_rate` | `DOUBLE` | Proportion of freelancers with this skill who are high earners |
| `median_hourly_rate` | `DOUBLE` | Median hourly rate |
| `mean_hourly_rate` | `DOUBLE` | Mean hourly rate |
| `median_user_skill_count` | `DOUBLE` | Median total skills possessed by holders of this skill |

---

### `skill_combinations.parquet`
Skill bundles (pairs and triples), associations, and FDR statistics.

| Field | Type | Description |
|---|---|---|
| `bundle_name` | `VARCHAR` | Alphabetically ordered skill names joined by ` + ` |
| `bundle_skills` | `VARCHAR` | JSON-encoded array of constituent skills |
| `bundle_size` | `BIGINT` | 2 for pairs, 3 for triples |
| `freelancer_count` | `BIGINT` | Number of freelancers possessing all skills in bundle |
| `support` | `DOUBLE` | Empirical prevalence $P(\text{Bundle})$ |
| `expected_prevalence` | `DOUBLE` | Expected independent joint prevalence $\prod P(S_i)$ |
| `lift` | `DOUBLE` | Co-occurrence lift $\frac{\text{Support}}{\text{Expected Prevalence}}$ |
| `high_earner_count` | `BIGINT` | High earners possessing the bundle |
| `high_earner_rate` | `DOUBLE` | Proportion of bundle holders who are high earners |
| `high_earner_lift` | `DOUBLE` | Disproportionate high earner multiplier $\frac{P(\text{High} \mid \text{Bundle})}{P(\text{High})}$ |
| `odds_ratio` | `DOUBLE` | Cross-product Odds Ratio with Haldane-Anscombe continuity correction |
| `ci_lower` | `DOUBLE` | 95% Confidence Interval lower bound for Odds Ratio |
| `ci_upper` | `DOUBLE` | 95% Confidence Interval upper bound for Odds Ratio |
| `p_value` | `DOUBLE` | Chi-Square test p-value (with Yates continuity correction) |
| `adjusted_p_value` | `DOUBLE` | Benjamini-Hochberg False Discovery Rate (FDR) adjusted p-value |
| `is_significant_fdr` | `BOOLEAN` | True if `adjusted_p_value` $< 0.05$ |

---

### `network_nodes.parquet`, `network_edges.parquet`, `network_communities.parquet`
Graph topological topology, Louvain partition, and precomputed spring layout coordinates.

- **Nodes**: `skill_name`, `community_id`, `freelancer_count`, `high_earner_rate`, `degree_centrality`, `weighted_degree`, `betweenness_centrality`, `closeness_centrality`, `bridge_score`, `x`, `y`.
- **Edges**: `source`, `target`, `weight` (co-occurrence count).
- **Communities**: `community_id`, `num_skills`, `total_freelancers`, `avg_high_earner_rate`, `median_earnings`, `top_skills`.

---

### `text_terms.parquet` & `topics.parquet`
NLP differential TF-IDF terms and Latent Dirichlet Allocation topic archetypes.

- **Text Terms**: `term`, `ngram_type`, `doc_frequency`, `high_earner_mean_tfidf`, `non_high_earner_mean_tfidf`, `diff_ratio`, `log_diff_score`, `is_high_earner_marker`.
- **Topics**: `topic_id`, `topic_label`, `top_keywords`, `dominant_freelancer_count`, `high_earner_rate`, `median_earnings`, `mean_doc_weight`.

---

### `geographic_statistics.parquet`
Aggregations across countries and metropolitan hubs.

- **Fields**: `country`, `freelancer_count`, `high_earner_rate`, `median_earnings`, `mean_earnings`, `median_hourly_rate`, `mean_hourly_rate`, `top_skills`, `avg_lat`, `avg_lon`.
