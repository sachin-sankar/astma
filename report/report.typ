
#set page(paper: "a4", margin: (
  top: 2.5cm,
  bottom: 2.5cm,
  left: 3cm,
  right: 2.5cm,
))
#set heading(numbering: "1.")

#let project-title = [Skill Bundles and Freelancer Earnings: A Multidimensional Analytics Dashboard]

// Define authors as an array of dictionaries
#let authors = (
  (name: "Sachin Sankar", reg: "23BBS0177"),
  (name: "Nikin Mahesh Kumar", reg: "23BBS0174"),
  (name: "Hriday Singh Sobti", reg: "23BBS0171"),
  (name: "Rahul Joseph Thomas", reg: "23BBS0169"),
)

#align(center)[
  #v(1.8cm)
  #text(size: 16pt, weight: "bold")[#project-title]
  #v(1.1cm)
  #text(
    size: 12pt,
    weight: "bold",
  )[Advanced Social, Text & Media Analytics (CBS3009)]
  #v(0.5cm)
  #text(size: 14pt, weight: "bold")[PROJECT REPORT]
  #v(0.4cm)
  Fall Semester 2026–2027
  #v(1.1cm)
  Submitted by
  #v(0.2cm)

  // Dynamically map and render all authors line by line
  #text(size: 12pt, weight: "bold")[
    #authors.map(a => [#a.name (#a.reg)]).join([\ ])
  ]

]
#pagebreak()

#outline(title: [CONTENTS], depth: 2)
#pagebreak()

= Project Topic

#project-title

= Abstract

Freelance marketplaces contain large numbers of profiles with heterogeneous skill selections, reported earnings, reviews, profile text, and geographic information. This project develops an analytical pipeline and interactive dashboard to investigate how individual skills and combinations of skills are associated with freelancer earnings. The implementation uses a collection of Freelancer.in directory profiles and converts raw JSON records into normalized Parquet datasets for repeatable analysis. The repository's current analytical artifacts report 10,002 deduplicated profiles, 350,811 freelancer–skill links, and 3,195 unique skills. The empirical 90th-percentile earnings threshold is approximately \$79,497.80; 1,001 profiles are classified in the high-earner group in the stored overview metrics.

The system combines descriptive skill statistics, pair/triple combination mining, contingency-table tests, Benjamini–Hochberg false-discovery-rate correction, multivariable logistic and ordinary least-squares regression, skill co-occurrence network analysis, profile-text analysis using differential TF–IDF and latent Dirichlet allocation, and country/city aggregation. Analytical outputs are persisted as Parquet and JSON artifacts and exposed through a five-page Plotly Dash application: Overview, Skill Bundles, Skill Network, Profile Language, and Geography. This separation of data preparation, analysis, and presentation makes the results reproducible and allows the dashboard to load precomputed outputs rather than repeatedly fit models during user interaction.

The stored results suggest that some uncommon bundles are strongly associated with the high-earner tier, while network communities and profile language provide complementary views of skill structure and professional positioning. These findings are observational, not causal. Sparse bundles, wide confidence intervals, marketplace selection effects, and the difference between lifetime earnings and hourly rates require cautious interpretation. The project provides a practical framework for exploring these relationships and identifying patterns for further validation.

= Introduction

== Context and motivation

Online freelance marketplaces bring together workers who describe their services through skill tags, profile summaries, hourly rates, reviews, portfolios, and accumulated earnings. These signals provide a useful setting for social, text, and media analytics because they combine structured categorical data with free text and geographic attributes. A freelancer may list many skills, but the market value of a profile cannot be understood solely by counting them. A more informative question is whether particular combinations of skills occur together more often than expected and whether those combinations are associated with higher earnings after accounting for basic profile differences.

The project addresses this question using profile data collected from the Freelancer.in public directory endpoint. The implemented repository includes a resumable collection script, a profiling stage, a normalization and deduplication stage, several independent analytical modules, an integrated insight generator, and a browser-based dashboard. It is therefore more than a single statistical model: it is an end-to-end workflow from acquisition to exploratory interpretation.

== Problem statement

The central problem is to identify skill bundles and related profile characteristics that are disproportionately associated with a high-earning freelancer tier. The analysis must account for the fact that skills are not independent, popular skills can dominate raw counts, and testing hundreds of thousands of combinations creates a multiple-comparisons problem. It should also preserve complementary signals from profile text, network structure, and geography without treating any one view as a complete explanation of earnings.

== Objectives

The project has the following objectives:

- Build a resumable JSON collection and profiling workflow for freelancer profiles.
- Clean, deduplicate, normalize, and persist the records in columnar Parquet datasets.
- Define a reproducible high-earner label from the empirical 90th percentile of total earnings.
- Measure baseline skill prevalence and earnings distributions.
- Mine skill pairs and triples and calculate support, lift, odds ratios, confidence intervals, significance tests, and adjusted p-values.
- Estimate adjusted bundle associations using logistic regression and log-earnings OLS models with profile controls.
- Construct a weighted skill co-occurrence network and detect communities and bridge skills.
- Compare profile language between high-earner and other profiles and fit an eight-topic LDA model.
- Summarize country and city differences and combine the outputs into a single insight artifact.
- Present the outputs through an interactive dashboard and validate core data invariants with tests.

== Scope

The implemented system focuses on profile-level data and observational associations. It does not estimate causal returns to acquiring a skill, track changes in individual earnings over time, or measure the quality of completed projects. The repository includes four normalized Parquet tables for freelancers, skill links, profile text, and portfolios, as well as analytical artifacts for skills, bundles, networks, text, and geography. The dashboard presents precomputed results and exposes filters appropriate to each analytical view.

The codebase is configured for Python 3.12 or later and uses `uv` for dependency management. The analytical stack includes DuckDB, PyArrow, Pandas, NumPy, SciPy, scikit-learn, Statsmodels, NetworkX, python-louvain, Plotly, and Dash. A `justfile` provides commands for running the stages, launching the dashboard, and executing tests.

= Background study

== Association-rule and frequent-itemset mining

Association analysis is commonly used to discover items that occur together in transaction-like records. Agrawal, Imieliński and Swami (1993) introduced association rules for discovering relationships among items in large databases. In this project, each freelancer's explicit skill list can be treated as a set of items. Support measures how frequently a bundle occurs, while lift compares observed co-occurrence with the value expected if its component skills were independent. Lift above one indicates positive co-occurrence relative to that independence baseline; it does not by itself imply higher earnings.

The project extends simple co-occurrence analysis by examining whether a bundle is associated with the high-earner label. This distinction matters: a bundle can be common because its skills are broadly popular, yet have little relationship with the upper earnings tier. Conversely, a rare bundle can show a high observed high-earner proportion but be statistically unstable because it occurs in very few profiles. The implementation therefore records bundle counts and applies minimum-count/support filters before inference.

== Multiple testing and statistical inference

Mining a large number of pairs and triples generates a large family of statistical tests. If every test were judged only by a nominal p-value threshold, many apparently significant findings could arise by chance. Benjamini and Hochberg (1995) proposed a false discovery rate procedure that controls the expected proportion of false discoveries among rejected hypotheses under its stated assumptions. The project's combination analysis applies Benjamini–Hochberg adjustment and uses an alpha threshold of 0.05 in its configuration.

Effect sizes and uncertainty are as important as adjusted p-values. Odds ratios express the relative odds of being in the high-earner tier for profiles with a bundle versus profiles without it. Confidence intervals indicate how imprecise that estimate may be. In small or sparse cells, odds ratios can become very large and confidence intervals extremely wide; such values should be interpreted as candidate signals, not stable market premiums.

== Regression adjustment

A bivariate association may reflect other profile characteristics. For example, freelancers listing more skills may also have more reviews, different country distributions, or different platform histories. Logistic regression models the probability of a binary outcome through the logit link (Hosmer, Lemeshow and Sturdivant, 2013). The project uses a multivariable logistic model to estimate the bundle association while controlling for skill count, log-transformed review count, and selected country indicators. Exponentiating the bundle coefficient yields an adjusted odds ratio.

The project also fits an ordinary least-squares model with log-transformed total earnings as the outcome. This gives a complementary continuous-outcome analysis. Neither model removes all confounding: the data do not establish time order, work quality, client budgets, or the details of each freelancer's project history. Regression adjustment should therefore be described as conditional association rather than causal effect.

== Text mining and topic modelling

Term frequency–inverse document frequency (TF–IDF) gives greater weight to terms that are frequent in a document but relatively uncommon across the corpus. It is useful for identifying words and phrases that distinguish one group of profiles from another. The project's language module calculates differential prominence for unigrams and bigrams in high-earner versus non-high-earner profiles.

Latent Dirichlet allocation (LDA), introduced by Blei, Ng and Jordan (2003), models documents as mixtures of latent topics and topics as distributions over words. The implementation fits eight topics and stores topic labels, prominent terms, and earnings breakdowns for dashboard inspection. Topics are descriptive summaries of language patterns; they should not be interpreted as objectively discovered occupational categories without qualitative validation.

== Network analysis and community detection

A skill co-occurrence network represents each skill as a node and connects two skills when they appear together in freelancer profiles. Edge weights reflect the strength or count of co-occurrence. Network measures can reveal skills that are frequent, central, or positioned between otherwise distinct groups. Community detection can identify dense groups of skills, while betweenness centrality helps identify potential bridges between clusters. Newman (2010) provides a broad foundation for network measures and community structure.

The repository uses NetworkX for graph construction and centrality calculations and Louvain community detection to partition the weighted network. A community is a structural grouping in the observed data, not necessarily a formal job family. Results depend on the selected nodes, edge threshold, and profile population.

== Geographic comparisons

Aggregating profile metrics by country and city makes it possible to compare profile counts, median earnings, hourly rates, and high-earner rates across locations. Such summaries can expose variation that would be hidden in a global average. They can also be misleading when groups have different sample sizes, skill mixes, or platform participation. The code uses minimum-count thresholds for country and city summaries; the dashboard should still be read as exploratory rather than as a ranking of worker ability by geography.

= Methodology

== Dataset and data fields

The data acquisition script `collection.py` requests directory records from the Freelancer.in AJAX directory endpoint using an offset parameter. It stores each successful page as a JSON file under `artifacts/raw_json`, increments the offset by ten, reuses a `requests.Session`, applies a one-second delay between successful requests, and resumes from the largest numeric offset file already present. Network failures are logged and retried after a delay. An empty response terminates collection. This design supports interruption and resumption without requiring a single monolithic output file.

The source records contain profile identifiers, earnings, hourly rates, reviews, skill lists, country/city fields, profile text, taglines, and portfolio information. The profiling accumulator measures field completeness, duplicate identifiers, earnings/rate distributions, skill frequencies, geographic coverage, text lengths, and portfolio availability. It processes files one by one rather than requiring all raw records to be held in memory simultaneously.

The current repository artifacts report 10,002 deduplicated freelancer profiles, 350,811 skill links, and 3,195 unique skills. These values describe the checked-in analytical snapshot, not a guarantee about all profiles on the live marketplace. The dataset also contains profile attributes that may be missing, stale, user-entered, or unevenly populated.

== Cleaning and normalization

The ingestion pipeline reads JSON files, validates record shapes, cleans strings and numeric values, and skips records without a usable user identifier. When a user identifier appears more than once, the pipeline records a conflict and chooses the record with the higher total earnings; when earnings tie, the record with more skills is preferred. This is a deterministic practical rule, but it can favor a particular snapshot when duplicate records disagree.

The pipeline derives the high-earner threshold from the 90th percentile of total earnings across the deduplicated profiles. A profile is marked as a high earner when total earnings are at least this threshold and are positive. The configured percentile is 0.90, the minimum skill frequency is 15, the minimum combination count is 20, and the default random seed is 42. The threshold recorded by the project documentation is approximately \$79,497.80.

Normalized data is written to four Parquet tables: `freelancers.parquet`, `freelancer_skills.parquet`, `profile_text.parquet`, and `portfolios.parquet`. Parquet supports column-oriented analytical access and compact typed storage. DuckDB and Pandas are used to query and transform these files, while JSON is used for compact summary artifacts and model outputs.

== Baseline descriptive analytics

The baseline module computes profile-level earnings distributions and skill-level summaries. It reports the total number of profiles, high-earner count/rate, median and mean earnings, hourly-rate summaries, skill counts, and review counts. Skill-level statistics include the number of freelancers listing each skill, prevalence, median earnings, and high-earner rate. These baseline measures provide context for the more complex bundle results.

The stored overview metrics report a median total earning value of 876.5 and a mean of 37,349.72, while the standard deviation is 233,411.02. The difference between the mean and median, together with the high standard deviation, indicates a strongly right-skewed earnings distribution. Median hourly rate is 20.00 and mean hourly rate is approximately 24.98. The high-earner share is approximately 10%, as expected from the percentile-based definition apart from ties and the positive-earnings condition.

== Skill combination mining

The combination miner evaluates skill pairs and triples. For a bundle \(C\), support is the fraction of profiles containing all skills in that bundle:

$ "support"(C) = N_C / N $

Lift compares observed bundle support with the product of the marginal prevalence of each skill:

$ "lift"(C) = P(C) / product_(s in C) P(s) $

A high lift indicates that component skills co-occur more frequently than the independence baseline. The analysis also calculates the proportion of bundle members in the high-earner tier and the high-earner lift, defined as the bundle's high-earner rate divided by the overall high-earner rate.

For each bundle, a two-by-two contingency table compares bundle presence/absence with high-earner status. The odds ratio is computed from the four cells, using a 0.5 continuity correction when a cell is zero. The analysis stores 95% confidence intervals and chi-square p-values with continuity correction. Benjamini–Hochberg adjusted p-values are used to account for multiple comparisons. The configuration sets a minimum combination count of 20 and minimum support of 0.002; the checked-in analytical outputs document 428,795 evaluated pairs and triples.

== Controlled regression

The logistic model estimates the bundle's association with high-earner status after including control variables:


$
  "logit"(P_i) = beta_0 + beta_1 C_i + beta_2 S_i + beta_3 log(R_i) + gamma D_i
$


The adjusted odds ratio is \(exp(beta_1)\). The model controls for the number of skills, log review count, and selected country indicators. The OLS model uses \(log(total_earnings+1)\) as the outcome and analogous controls. The two models answer related but different questions: logistic regression concerns the odds of crossing the high-earner threshold, whereas OLS concerns conditional differences in log earnings.

The checked-in regression JSON includes examples with wide confidence intervals, demonstrating why effect sizes must be reported with sample counts and uncertainty. For example, the bundle “Landing Pages + OSCommerce” has a controlled odds ratio of 74.234, but its reported confidence interval ranges from 1.741 to 3164.786 and the bundle count is 26. The interval is very wide; the point estimate should not be presented as a precise estimate of a stable premium.

== Network analysis

The network module represents skills as nodes and skill co-occurrence as weighted edges. It limits the graph to the configured top 150 nodes and uses a minimum edge weight of 25 in the default configuration. It calculates degree-related and centrality measures, including betweenness and closeness, and derives a bridge score. Louvain community detection assigns community identifiers. The module saves node, edge, and community tables and includes two-dimensional layout coordinates for visualization.

Repository documentation reports a network of 150 selected skill nodes and 11,147 weighted co-occurrence edges, with modularity of 0.163 and three broad clusters described as Design and Creative, Web and Fullstack Engineering, and Data and Systems Engineering. These labels are interpretations of the resulting communities and should be verified against their constituent skills.

== Text analysis

The language module produces differential TF–IDF terms, including unigrams and bigrams, and fits an LDA model with eight topics. The resulting artifacts are `text_terms.parquet` and `topics.parquet`. The dashboard compares terms associated with high-earner profiles and displays topic-level keywords and earnings summaries. Text preprocessing and topic outputs are dependent on the profile text available in the collection; short, empty, or templated profiles can limit the signal.

== Geographic analysis and integrated insights

Country and city analysis aggregates profile counts, median earnings, hourly rates, and high-earner rates. Configured minimum sample thresholds are 15 profiles per country and five per city. The output tables are `geographic_statistics.parquet` and `city_statistics.parquet`. The integrated insights module combines overview metrics and selected findings from the other modules into `integrated_insights.json`, which can be used as a compact summary layer.

== Reproducibility and execution

The project targets Python 3.12 or later and declares dependencies in `pyproject.toml`. Typical execution uses:

```bash
uv sync
just pipeline
just test
just dashboard
```

The `pipeline` recipe runs profiling, ingestion, baseline analytics, combination mining, network analysis, text analysis, geography, and integrated insight generation. Stages can also be run individually using the commands documented in `docs/pipeline.md`. The test suite checks cleaning helpers, profile invariants, artifact existence, combination statistics, network outputs, and text/topic outputs.

#figure(
  image("diagrams/pipeline.svg", width: 100%),
  caption: [End-to-end data and analytics pipeline (PlantUML source supplied separately).],
) <pipeline-figure>

= Proposed model

== Model overview

The proposed model is an analytical system rather than a predictive service that returns an earnings forecast for an individual. It has four layers: acquisition and profiling, normalized storage, specialized analysis, and dashboard presentation. The design keeps source collection and cleaning separate from feature derivation and statistical testing. Persisted analytical artifacts allow the dashboard to be responsive and make the results inspectable outside the UI.

#figure(
  image("diagrams/proposed_model.svg", width: 100%),
  caption: [Proposed layered architecture and data flow.],
)

== Acquisition and preparation layer

The acquisition component fetches directory profiles in offset-based batches and writes independent JSON files. This reduces the risk of losing all progress if collection stops. The profiler generates summaries of data quality and coverage before analysis. The ingestion component cleans fields, resolves duplicate identifiers, derives the outcome label, and writes the normalized Parquet tables.

This layer is responsible for preserving data lineage and making the definition of the outcome explicit. The percentile threshold is calculated from the observed sample, so it can change when the dataset is refreshed. The report's numerical findings are therefore tied to the checked-in snapshot and should be regenerated when new profiles are collected.

== Analytical layer

The analytical layer comprises six main domains. Baseline skill analysis gives a reference point for prevalence and earnings. Combination mining tests skill pairs and triples. Regression models examine whether bundle associations remain after controlling for selected profile attributes. Network analysis captures co-occurrence structure beyond isolated combinations. Text analysis extracts differential terms and latent topics. Geographic aggregation explores regional variation. The integrated insight generator joins selected results into a concise machine-readable summary.

These domains are complementary rather than interchangeable. A skill may be popular but not particularly associated with the high-earner tier. A bundle may have high lift but a low count. A term may distinguish profile descriptions without being a reliable indicator of earnings. A central network node may connect communities without being an earnings driver. The proposed model therefore encourages triangulation across outputs rather than relying on a single ranking.

== Statistical safeguards

The design incorporates several safeguards. Minimum frequency and combination-count thresholds reduce extremely sparse comparisons. Continuity correction prevents infinite odds ratios when a contingency-table cell is zero. Confidence intervals communicate uncertainty around odds ratios. False-discovery-rate correction addresses the large number of simultaneous bundle tests. Controlled regressions include skill count, review volume, and selected country indicators to reduce some observed confounding.

These safeguards do not eliminate all sources of bias. A minimum count of 20 still allows unstable estimates; very wide confidence intervals are evidence of this instability. The high-earner outcome is based on lifetime earnings, which can reflect tenure and opportunity as well as skill. Country indicators may not capture local cost of living, currency reporting, or marketplace access. The model should therefore be used for exploratory research and hypothesis generation.

== Dashboard presentation layer

The Dash application is divided into five pages. The Overview page provides headline metrics, earnings distributions, skill-count distributions, popular skills, and skills with high high-earner rates. The Skill Bundles page exposes bundle filters and visualizes lift, high-earner rates, adjusted odds ratios, confidence intervals, and adjusted p-values. The Skill Network page presents the co-occurrence graph with community and bridge-skill views. The Profile Language page displays differential terms and LDA topics. The Geography page shows a country choropleth, country rankings, and a city-level table.

#figure(
  image("diagrams/dashboard_modules.svg", width: 100%),
  caption: [Dashboard modules and the analytical artifacts consumed by each page.],
)

== User workflow

A typical analyst first reviews the global distribution and the earnings threshold, then explores popular skills and high-earner rates. The analyst can move to bundle analysis to distinguish co-occurrence from earnings association, examine adjusted effects and uncertainty, and use the network page to understand how skills cluster. The language page adds evidence from profile descriptions, while geography adds context on regional variation. This workflow supports comparison and interpretation rather than automated career recommendations.

== Design choices and rationale

Parquet was selected for typed, columnar analytical datasets, while JSON is used for compact summary and regression artifacts. DuckDB supports analytical SQL over Parquet, and Pandas provides convenient dataframe transformations. Python allows the statistical, NLP, network, and dashboard components to share a common data layer. Dash and Plotly provide interactive filtering and visualizations without requiring a separate frontend application.

Precomputing artifacts is a practical choice for a project with multiple analyses and many combinations. It separates computationally expensive stages from the interactive dashboard and provides durable outputs for tests and inspection. The trade-off is that the dashboard reflects the latest completed pipeline run; it does not automatically update when raw data changes. Re-running the pipeline is necessary after collecting a new snapshot.

= Results and Discussion

== Dataset-level findings

The stored overview artifact contains 10,002 deduplicated profiles and 3,195 unique skills. It reports 1,001 high-earner profiles, a high-earner rate of approximately 10.01%, median earnings of 876.50, mean earnings of 37,349.72, and median hourly rate of 20.00. The mean earnings value is much larger than the median, and the standard deviation is approximately 233,411.02. This indicates substantial dispersion and a right-skewed distribution, so the median is a more representative measure of the typical profile than the mean alone.

#table(
  columns: (1.6fr, 1fr),
  [*Metric*], [*Stored result*],
  [Deduplicated profiles], [10,002],
  [High-earner profiles], [1,001],
  [High-earner rate], [10.01%],
  [Unique skills], [3,195],
  [Freelancer–skill links], [350,811],
  [Median total earnings], [876.50],
  [Mean total earnings], [37,349.72],
  [Median hourly rate], [20.00],
  [Mean hourly rate], [24.98],
  [Median skills per profile], [20],
  [Mean skills per profile], [35.07],
  [Median review count], [1],
)

The figures above are taken from the repository's analytical outputs and overview documentation. Monetary values are shown in the units recorded by the source artifacts; currency conversion and cross-country purchasing-power adjustment are not documented in the codebase and are not assumed here.

== Skill prevalence and earnings

The most prevalent skills in the integrated output include Graphic Design (3,670 profiles), Logo Design (2,737), Website Design (2,703), and HTML (2,617). The stored high-earner rates for these skills are 16.32%, 15.27%, 21.64%, and 18.99%, respectively. These results illustrate why popularity and earnings association should be examined separately. Website Design and HTML have higher high-earner rates than the overall rate, while still being common skills with large profile counts.

#table(
  columns: (1.5fr, 1fr, 1fr, 1fr),
  [*Skill*], [*Profiles*], [*Prevalence*], [*High-earner rate*],
  [Graphic Design], [3,670], [36.69%], [16.32%],
  [Logo Design], [2,737], [27.37%], [15.27%],
  [Website Design], [2,703], [27.03%], [21.64%],
  [HTML], [2,617], [26.17%], [18.99%],
)

== Skill bundles

The repository's analytical documentation reports 428,795 evaluated skill pairs and triples, of which 404,773 are recorded as statistically significant after Benjamini–Hochberg adjustment. This high proportion should not be interpreted as proof that almost every bundle has a practically meaningful earnings premium. Statistical significance is influenced by sample size and the tested hypotheses, while practical interpretation requires effect sizes, confidence intervals, counts, and the adjustment procedure.

The integrated summary ranks “Landing Pages + OSCommerce” among the leading bundles. It appears in 26 profiles, has support of 0.0026, a reported high-earner rate of 96.15%, and a raw odds ratio of 230.533. In the controlled regression artifact, its adjusted odds ratio is 74.234, with a 95% confidence interval from 1.741 to 3164.786 and a logistic p-value of approximately 0.0245. The very wide interval indicates considerable uncertainty. The estimate is best treated as a hypothesis for further study, not as evidence that learning these skills would cause earnings to increase by a specific amount.

Another reported bundle, “Figma + Website Design + Yii,” appears in 26 profiles and has a controlled odds ratio of 15.07 with a confidence interval from 1.888 to 120.277. Its log-earnings OLS coefficient is 0.516, but the associated p-value is approximately 0.093. The two model results are not identical because they represent different outcomes and model assumptions. They reinforce the need to report model type and uncertainty with every bundle result.

#table(
  columns: (1.7fr, 0.65fr, 0.8fr, 1fr, 1.2fr),
  [*Bundle*], [*N*], [*Raw OR*], [*Adjusted OR*], [*Adjusted-model 95% CI*],
  [Landing Pages + OSCommerce], [26], [230.533], [74.234], [1.741–3164.786],
  [Figma + Website Design + Yii], [26], [230.533], [15.070], [1.888–120.277],
  [OSCommerce + UX / User Experience],
  [22],
  [192.857],
  [83.111],
  [2.195–3147.115],
)

The results suggest that certain small skill bundles are strongly associated with high-earner status in this snapshot. However, bundle counts are modest, confidence intervals are wide, and some component skills may be associated with particular profile types or marketplace niches. The findings do not establish that these skills are causal drivers of income, and results may change under a different sample or threshold.

== Network structure

The network artifacts contain 150 selected skill nodes and 11,147 edges, according to the analytical documentation. Louvain community detection is reported to produce modularity of 0.163 and three broad clusters: Design and Creative, Web and Fullstack Engineering, and Data and Systems Engineering. The result is consistent with the idea that skill tags form overlapping professional ecosystems rather than isolated independent items.

Bridge skills are of interest because they connect clusters that otherwise have relatively fewer links. Their value in the analysis is structural: they may identify combinations of expertise that span domains. They should not be confused with the most profitable skills. The interpretation depends on the network's node selection, edge threshold, and how co-occurrence is counted.

== Profile language and topics

The profile-language module extracts 4,000 differential TF–IDF terms, including unigrams and bigrams, and stores eight LDA topics. The project documentation describes high-earner language as more focused on system architecture, optimization, and project delivery than generic task listings. This is an interpretation of language patterns in the collected profiles. It can be affected by profile length, English proficiency, templates, and differences in how users market themselves. Topic labels should be manually reviewed before they are treated as definitive occupational categories.

== Geography

The geographic artifacts report 59 country-level summaries and 262 metropolitan city summaries. The dashboard maps country high-earner rates and provides a country ranking by freelancer population, along with a city table showing profile counts, high-earner rates, median earnings, and hourly rates. The country and city minimum-count filters reduce the influence of extremely small groups, but they do not make all groups directly comparable. Regional differences may reflect skill composition, currency conventions, platform participation, or the number of observations as well as economic conditions.

== Implementation and validation

The repository includes a pytest suite that tests numeric/string cleaning helpers, profiling behavior, artifact existence, high-earner proportions, the log-earnings transformation, bundle-statistic bounds, network columns, and the expected number of LDA topics. The checks provide useful regression protection for core invariants. They do not, on their own, prove the correctness of every statistical assumption or the representativeness of the dataset.

The following excerpt illustrates the core outcome-label concept used by the ingestion pipeline. It is explanatory pseudocode consistent with the documented implementation; the project source remains authoritative.

```python
threshold = np.percentile(all_earnings, 90)
freelancers["high_earner"] = (
    (freelancers["total_earnings"] >= threshold)
    & (freelancers["total_earnings"] > 0)
)
freelancers["log_earnings"] = np.log1p(
    freelancers["total_earnings"]
)
```

== Dashboard screenshots

The template requests screenshots of all modules. The repository snapshot contains the dashboard source code but does not include rendered browser screenshots, so the boxes below are intentional placeholders. Capture each page from the running application at `http://localhost:8050` and replace the corresponding placeholder with the screenshot file. Suggested paths are relative to this report: `screenshots/overview.png`, `screenshots/skill-bundles.png`, `screenshots/skill-network.png`, `screenshots/profile-language.png`, and `screenshots/geography.png`.

#let screenshot-placeholder(label) = block(
  width: 100%,
  height: 4.2cm,
  stroke: 0.8pt + gray,
  inset: 8pt,
  align(center + horizon)[
    #text(weight: "bold")[Screenshot placeholder: #label]
    #v(0.25cm)
    #text(
      size: 10pt,
    )[Replace this box with a screenshot captured from the running dashboard.]
  ],
)
#figure(
  image("screenshots/overview.png"),
  caption: [Dashboard screenshot 1 — Overview.],
)
#figure(
  image("screenshots/bundle.png"),
  caption: [Dashboard screenshot 2 — Skill Bundles.],
)
#figure(
  image("screenshots/network.png"),
  caption: [Dashboard screenshot 3 — Skill Network.],
)
#figure(
  image("screenshots/lang.png"),
  caption: [Dashboard screenshot 4 — Profile Language.],
)
#figure(
  image("screenshots/wgeo.png"),
  caption: [Dashboard screenshot 5 — Geography.],
)

== Limitations and threats to validity

Several limitations affect interpretation. First, the dataset is a marketplace snapshot, not a random sample of all freelancers. Second, reported earnings may depend on account age, platform activity, client access, work history, and other unobserved variables. Third, the combination miner tests a large hypothesis family; FDR adjustment helps but does not guarantee that every selected finding will replicate. Fourth, sparse bundles can have extreme point estimates and wide intervals. Fifth, user-entered profile text and skills can be incomplete, strategic, or outdated. Finally, the analyses are cross-sectional and observational, so they cannot establish that a skill bundle causes higher earnings.

A further practical limitation is that the dashboard reads precomputed artifacts. Users should confirm that all pipeline stages completed successfully before interpreting dashboard outputs after a data refresh. The results tables in this report describe the currently supplied artifacts and should be regenerated if the underlying files change.

= Conclusion

This project implements a complete analytical workflow for studying associations between freelancer skills and earnings. It combines data collection and profiling, deduplicated Parquet storage, baseline statistics, skill-pair and skill-triple mining, multiple-testing correction, adjusted regression, network community analysis, profile-text modelling, geographic aggregation, and an interactive five-page dashboard. The checked-in results cover 10,002 profiles and 3,195 unique skills and show substantial variation in earnings and skill combinations.

The most important contribution is the combination of several analytical lenses. Bundle analysis identifies candidate combinations associated with the high-earner tier; regression adds limited adjustment for observed profile attributes; the network view describes relationships among skills; text modelling captures differences in profile language; and geography provides regional context. These perspectives help generate hypotheses that a single frequency table would miss.

The results must nevertheless be interpreted cautiously. High odds ratios from bundles represented by only a few dozen profiles can be unstable, and association is not causation. Future work should validate findings on a later data snapshot, examine sensitivity to the earnings threshold and minimum bundle support, report calibration and robustness diagnostics, improve missing-data analysis, and qualitatively review topic and community labels. With these extensions, the system can serve as a reproducible exploratory platform for studying skill-market relationships rather than as a prescriptive earnings predictor.

= References

Agrawal, R., Imieliński, T. and Swami, A. (1993) ‘Mining association rules between sets of items in large databases’, *Proceedings of the 1993 ACM SIGMOD International Conference on Management of Data*, pp. 207–216. doi: 10.1145/170035.170072.

Benjamini, Y. and Hochberg, Y. (1995) ‘Controlling the false discovery rate: a practical and powerful approach to multiple testing’, *Journal of the Royal Statistical Society: Series B (Methodological)*, 57(1), pp. 289–300. doi: 10.1111/j.2517-6161.1995.tb02031.x.

Blei, D.M., Ng, A.Y. and Jordan, M.I. (2003) ‘Latent Dirichlet allocation’, *Journal of Machine Learning Research*, 3, pp. 993–1022.

Freelancer.in (n.d.) *Freelancer directory*. Available at: https://www.freelancer.in/ (Accessed: October 2026).

Hosmer, D.W., Lemeshow, S. and Sturdivant, R.X. (2013) *Applied Logistic Regression*. 3rd edn. Hoboken, NJ: Wiley.

Newman, M.E.J. (2010) *Networks: An Introduction*. Oxford: Oxford University Press.

Pedregosa, F. et al. (2011) ‘Scikit-learn: machine learning in Python’, *Journal of Machine Learning Research*, 12, pp. 2825–2830.

