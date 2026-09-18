# Analytical Outputs

Summary of generated datasets and analytical results stored in `data/analytical/`.

## Key findings

1. The clean dataset contains 10,002 deduplicated freelancer profiles with 350,811 skill links across 3,195 skills.
2. The top 10% earnings tier starts at $79,497.80.
3. Out of 428,795 evaluated skill pairs and triples, 404,773 combinations show statistically significant association with earnings tier ($p_{\text{adj}} < 0.05$) after Benjamini-Hochberg FDR correction.
4. Louvain community detection partitions the skill co-occurrence graph (modularity 0.163) into 3 functional clusters: Design and Creative, Web and Fullstack Engineering, and Data and Systems Engineering.
5. Skills with high betweenness relative to degree act as bridges connecting separate technical disciplines.
6. High-earning profiles feature terms centered on system architecture, optimization, and project delivery rather than generic task listings.

## Artifacts catalog

| File | Format | Contents |
|---|---|---|
| `overview_metrics.json` | JSON | Overall dataset totals, medians, means, and rates |
| `earnings_distribution.parquet` | Parquet | Individual earnings, log earnings, rates, and review counts |
| `skill_statistics.parquet` | Parquet | 1,859 individual skills with frequency, prevalence, median earnings, and high-earner rates |
| `skill_combinations.parquet` | Parquet | 428k+ pairs and triples with support, lift, odds ratios, 95% CIs, and FDR adjusted p-values |
| `combination_regression.json` | JSON | Controlled logit and OLS regression coefficients adjusting for skill count, reviews, and country |
| `network_nodes.parquet` | Parquet | 150 top nodes with degree, betweenness, closeness, bridge score, and 2D layout coordinates |
| `network_edges.parquet` | Parquet | 11,147 weighted co-occurrence edges |
| `network_communities.parquet` | Parquet | Community aggregates and prominent skills per cluster |
| `text_terms.parquet` | Parquet | 4,000 TF-IDF unigrams and bigrams with differential prominence scores |
| `topics.parquet` | Parquet | 8 LDA topic models with top keywords and earnings breakdown |
| `geographic_statistics.parquet` | Parquet | 59 country profiles with localized skills and high-earner rates |
| `city_statistics.parquet` | Parquet | 262 metropolitan city summaries |
| `integrated_insights.json` | JSON | Summary artifact combining core results |
