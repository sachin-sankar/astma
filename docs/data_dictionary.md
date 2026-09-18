# Data Dictionary

Schemas, types, and descriptions for all normalized tables and analytical outputs.

## 1. Normalized tables (`data/parquet/`)

### `freelancers.parquet`
Demographics, platform earnings, and feedback scores for each unique freelancer profile.

| Field | Type | Description |
|---|---|---|
| `user_id` | `VARCHAR` | Unique profile ID |
| `username` | `VARCHAR` | Profile handle |
| `public_name` | `VARCHAR` | Display name |
| `country` | `VARCHAR` | Country of residence |
| `city` | `VARCHAR` | City of residence |
| `hourly_rate` | `DOUBLE` | Stated hourly rate in USD |
| `total_earnings` | `DOUBLE` | Cumulative lifetime platform earnings in USD |
| `log_earnings` | `DOUBLE` | Natural logarithm transformed earnings $\ln(\text{total\_earnings} + 1)$ |
| `high_earner` | `BOOLEAN` | True if `total_earnings` $\ge \$79,497.80$ (90th percentile threshold) |
| `reputation` | `DOUBLE` | Platform reputation score |
| `review_count` | `BIGINT` | Number of completed reviews |
| `stars` | `DOUBLE` | Average feedback star rating out of 5.0 |
| `score` | `DOUBLE` | Platform algorithmic score |
| `skill_count` | `BIGINT` | Count of explicit skills selected by the freelancer |
| `latitude` | `DOUBLE` | Latitude coordinate |
| `longitude` | `DOUBLE` | Longitude coordinate |

### `freelancer_skills.parquet`
Normalized skills linked to each freelancer (`is_user_skill == True`).

| Field | Type | Description |
|---|---|---|
| `user_id` | `VARCHAR` | Profile ID referencing `freelancers.user_id` |
| `skill_id` | `BIGINT` | Skill numeric identifier |
| `skill_name` | `VARCHAR` | Standardized skill name |

### `profile_text.parquet`
Textual content extracted from profiles and portfolio items.

| Field | Type | Description |
|---|---|---|
| `user_id` | `VARCHAR` | Profile ID referencing `freelancers.user_id` |
| `profile_text` | `VARCHAR` | Main biography text |
| `tagline` | `VARCHAR` | Profile tagline or headline |
| `portfolio_text` | `VARCHAR` | Concatenated text of portfolio titles and descriptions |
| `combined_text` | `VARCHAR` | Merged and cleaned text corpus for NLP modeling |

### `portfolios.parquet`
Individual portfolio items.

| Field | Type | Description |
|---|---|---|
| `user_id` | `VARCHAR` | Profile ID referencing `freelancers.user_id` |
| `portfolio_id` | `BIGINT` | Portfolio index for the user |
| `title` | `VARCHAR` | Portfolio item title |
| `description` | `VARCHAR` | Portfolio item description |

## 2. Analytical outputs (`data/analytical/`)

### `skill_statistics.parquet`
Individual skill metrics and baseline earnings statistics.

| Field | Type | Description |
|---|---|---|
| `skill_id` | `BIGINT` | Skill ID |
| `skill_name` | `VARCHAR` | Skill name |
| `freelancer_count` | `BIGINT` | Total freelancers listing the skill |
| `prevalence` | `DOUBLE` | Skill prevalence among all freelancers |
| `median_earnings` | `DOUBLE` | Median earnings of freelancers with this skill |
| `mean_earnings` | `DOUBLE` | Mean earnings of freelancers with this skill |
| `median_log_earnings` | `DOUBLE` | Median log earnings |
| `high_earner_rate` | `DOUBLE` | Proportion of freelancers with this skill who are high earners |
| `median_hourly_rate` | `DOUBLE` | Median hourly rate |
| `mean_hourly_rate` | `DOUBLE` | Mean hourly rate |
| `median_user_skill_count` | `DOUBLE` | Median skill count of users listing this skill |

### `skill_combinations.parquet`
Evaluated pairs and triples with statistical association metrics.

| Field | Type | Description |
|---|---|---|
| `bundle_name` | `VARCHAR` | Ordered skill names joined by ` + ` |
| `bundle_skills` | `VARCHAR` | JSON list of constituent skills |
| `bundle_size` | `BIGINT` | Number of skills in the combination (2 or 3) |
| `freelancer_count` | `BIGINT` | Freelancers with all skills in the bundle |
| `support` | `DOUBLE` | Empirical support $P(\text{Bundle})$ |
| `expected_prevalence` | `DOUBLE` | Expected joint prevalence under independence |
| `lift` | `DOUBLE` | Co-occurrence lift |
| `high_earner_count` | `BIGINT` | High earners with the bundle |
| `high_earner_rate` | `DOUBLE` | Proportion of bundle holders who are high earners |
| `high_earner_lift` | `DOUBLE` | High-earner rate divided by the population baseline rate |
| `odds_ratio` | `DOUBLE` | Haldane-Anscombe corrected Odds Ratio |
| `ci_lower` | `DOUBLE` | 95% Confidence Interval lower bound |
| `ci_upper` | `DOUBLE` | 95% Confidence Interval upper bound |
| `p_value` | `DOUBLE` | Chi-square test p-value with Yates continuity correction |
| `adjusted_p_value` | `DOUBLE` | Benjamini-Hochberg FDR adjusted p-value |
| `is_significant_fdr` | `BOOLEAN` | True if adjusted p-value is below 0.05 |

### `network_nodes.parquet`, `network_edges.parquet`, `network_communities.parquet`
Graph topology and Louvain community detection data.

- Nodes: `skill_name`, `community_id`, `freelancer_count`, `high_earner_rate`, `degree_centrality`, `weighted_degree`, `betweenness_centrality`, `closeness_centrality`, `bridge_score`, `x`, `y`.
- Edges: `source`, `target`, `weight`.
- Communities: `community_id`, `num_skills`, `total_freelancers`, `avg_high_earner_rate`, `median_earnings`, `top_skills`.

### `text_terms.parquet` & `topics.parquet`
Differential TF-IDF vocabulary and LDA topic models.

- Text terms: `term`, `ngram_type`, `doc_frequency`, `high_earner_mean_tfidf`, `non_high_earner_mean_tfidf`, `diff_ratio`, `log_diff_score`, `is_high_earner_marker`.
- Topics: `topic_id`, `topic_label`, `top_keywords`, `dominant_freelancer_count`, `high_earner_rate`, `median_earnings`, `mean_doc_weight`.

### `geographic_statistics.parquet`
Country-level summaries with top localized skills and high-earner rates.

- Fields: `country`, `freelancer_count`, `high_earner_rate`, `median_earnings`, `mean_earnings`, `median_hourly_rate`, `mean_hourly_rate`, `top_skills`, `avg_lat`, `avg_lon`.
