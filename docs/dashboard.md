# Dashboard Guide

Guide to the Dash application structure and interactive components.

## Application structure

```text
dashboard/
├── app.py                 # Dash application setup, navigation, layout
└── pages/
    ├── overview.py        # Dataset overview, earnings distribution, top skills
    ├── skill_bundles.py   # Skill combination explorer, lift scatter plot, regressions
    ├── skill_network.py   # Force-directed co-occurrence graph, Louvain clusters, bridge skills
    ├── profile_language.py# Differential TF-IDF terms and LDA topic models
    └── geography.py       # Global map and metropolitan drill-down
```

## Interactive features

### Overview (`/`)
- Summary metric cards showing total profiles, high-earner threshold, median earnings, and median hourly rate.
- Histogram of total earnings on log scale with high-earner tier coloring.
- Comparison chart of the most prevalent skills versus skills with the highest high-earner concentration.

### Skill bundles (`/skill-bundles`)
- Dropdown to filter by specific skills, radio buttons for pair versus triple bundle sizes, and a minimum sample size slider.
- Scatter plot showing co-occurrence lift against high-earner rate, sized by freelancer count and colored by odds ratio.
- Horizontal error-bar chart showing controlled odds ratios and 95% confidence intervals from multivariable logistic regression models.
- Paginated table of combination metrics with Benjamini-Hochberg FDR adjusted p-values.

### Skill network (`/skill-network`)
- Force-directed 2D network graph showing co-occurring skills, with node size reflecting freelancer volume and edge width reflecting co-occurrence count.
- Community filter dropdown and minimum edge weight slider.
- Color toggle for Louvain community cluster, high-earner rate, or bridge score.
- Node hover cards showing member counts, community ID, and median rates.
- Leaderboard table of bridge skills ranked by betweenness-to-degree ratio.

### Profile language (`/profile-language`)
- Horizontal bar charts displaying terms with the highest differential prominence in high-earner profiles compared to other profiles.
- Cards displaying top keywords, high-earner share, and member counts for each of the 8 LDA topics.

### Geography (`/geography`)
- Global map colored by country-level high-earner rate.
- Bar chart ranking top countries by profile count, colored by median hourly rate.
- Table detailing individual metropolitan hubs with median earnings and hourly rates.
