# Analytical Outputs & Artifacts

Summary of all generated data artifacts and analytical results in `data/analytical/`.

---

## 1. Primary Empirical Findings

1. **Total Cataloged Profiles**: 10,002 deduplicated freelancer profiles with 350,811 skill associations across 3,195 unique skills.
2. **High-Earner Threshold**: Top 10% (90th percentile) lifetime earnings begins at **$79,497.80 USD**.
3. **Skill Combinations Mined**: Over 428,000 frequent pairs and triples evaluated with full Benjamini-Hochberg FDR correction. Over 404,000 combinations demonstrate statistically significant association with earnings tier ($p_{\text{adj}} < 0.05$).
4. **Network Topology**: Modularity score of 0.163 partitioned into 3 major functional skill communities (Design/Creative, Fullstack/Web Architecture, and Data/Systems Engineering).
5. **Bridge Skills**: Skills with the highest betweenness-to-degree ratio (connecting disparate communities) include specialized architecture integrations, API systems, and cross-platform tools.
6. **Language Markers**: High-earning profiles feature terms emphasizing structural ownership, optimization, scalable architecture, and end-to-end delivery over generic task lists.

---

## 2. Artifacts Catalog

| File | Format | Key Contents |
|---|---|---|
| `overview_metrics.json` | JSON | Dataset-wide totals, medians, means, rates |
| `earnings_distribution.parquet` | Parquet | User-level earnings, log earnings, rates, review counts |
| `skill_statistics.parquet` | Parquet | 1,859 individual skills with frequency, prevalence, median earnings, high-earner rate |
| `skill_combinations.parquet` | Parquet | 428k+ pairs/triples with Support, Lift, Odds Ratio, 95% CI, p-value, FDR adjusted p-value |
| `combination_regression.json` | JSON | Controlled logit & OLS regression coefficients controlling for skill count, reviews, and country |
| `network_nodes.parquet` | Parquet | 150 top nodes with degree, betweenness, closeness, bridge score, and 2D layout coordinates |
| `network_edges.parquet` | Parquet | 11,147 weighted co-occurrence edges |
| `network_communities.parquet` | Parquet | Community-level aggregates and top skills per cluster |
| `text_terms.parquet` | Parquet | 4,000 TF-IDF unigrams/bigrams with differential prominence scores |
| `topics.parquet` | Parquet | 8 LDA topic models with top keywords and earnings breakdown |
| `geographic_statistics.parquet` | Parquet | 59 country profiles with top localized skills and high-earner rates |
| `city_statistics.parquet` | Parquet | 262 metropolitan city summaries |
| `integrated_insights.json` | JSON | Master executive summary and key strategic findings |
