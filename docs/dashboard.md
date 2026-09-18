# Interactive Dashboard Guide

The Dash application provides a zero-runtime-overhead, reactive UI exploring the precomputed analytical models.

---

## 1. Application Structure

```text
dashboard/
├── app.py                 # Multi-page Dash entrypoint, navbar, theme
└── pages/
    ├── overview.py        # Overview KPI cards, earnings dist, popular vs high-earning skills
    ├── skill_bundles.py   # Skill combination explorer, lift scatter plot, controlled regressions
    ├── skill_network.py   # 2D force-directed co-occurrence graph, Louvain clusters, bridge skills
    ├── profile_language.py# Differential TF-IDF terms & LDA topic models
    └── geography.py       # Global choropleth map & metropolitan breakdown
```

---

## 2. Key Interactive Features

### Overview (`/`)
- Summary KPI Cards: Total Freelancers, 90th Percentile High-Earner Threshold, Median Earnings, Median Hourly Rate.
- Earnings distribution histogram with toggle between log and linear scales.
- Comparison of top 15 most popular skills vs top 15 high-earner-associated skills.

### Skill Bundles (`/skill-bundles`)
- Filter combinations by specific skill dropdown, bundle size (pairs vs triples), or minimum sample size slider.
- Co-occurrence Lift vs High-Earner Proportion bubble chart (bubble size = freelancer count, color = Odds Ratio).
- Controlled econometric regression plot displaying adjusted Odds Ratios with 95% confidence interval error bars.
- Paginated DataTable displaying bundle statistics with FDR-adjusted p-values.

### Skill Network (`/skill-network`)
- Force-directed topological network visualization with precomputed layout.
- Filter by Louvain community cluster or minimum edge weight.
- Color nodes by Louvain Community, High-Earner Rate, or Bridge Score.
- Interactive hover cards detailing degree centrality, betweenness, and median hourly rate.
- Top Bridge Skills leaderboard ranking nodes by cross-community bridging capacity.

### Profile Language (`/profile-language`)
- Comparative horizontal bar charts showing top differential unigrams/bigrams for high earners vs non-high earners.
- Interactive LDA topic cards showing keyword weights, high-earner proportion, and dominant freelancer count.

### Geography (`/geography`)
- Interactive global choropleth map illustrating regional variation in high-earner rates.
- Top 15 country volume rankings with median hourly rates.
- City-level drill-down table for metropolitan freelance hubs.
