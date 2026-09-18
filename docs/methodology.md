# Analytical Methodology & Mathematical Formulations

This document provides the formal mathematical formulations and statistical frameworks implemented across the pipeline.

---

## 1. High-Earner Classification

The baseline population threshold $\tau_{90}$ is defined as the empirical 90th percentile of total lifetime platform earnings across all valid unique profiles:

$$\tau_{90} = \text{Percentile}_{90}(\{ \text{total\_earnings}_i \}_{i=1}^N)$$

A freelancer $i$ is labeled a high earner if:

$$Y_i = \begin{cases} 1 & \text{if } \text{total\_earnings}_i \ge \tau_{90} \text{ and } \text{total\_earnings}_i > 0 \\ 0 & \text{otherwise} \end{cases}$$

---

## 2. Skill Combinations & Association Mining

Let $C = \{S_1, S_2, \dots, S_k\}$ denote a skill bundle (pair or triple).

### 2.1 Support and Expected Prevalence
- **Empirical Support**:
  $$P(C) = \frac{N_C}{N}$$
  where $N_C$ is the count of freelancers listing all skills in $C$, and $N$ is total freelancers.

- **Independent Expected Prevalence**:
  $$\mathbb{E}[P(C)] = \prod_{j=1}^k P(S_j)$$

- **Co-occurrence Lift**:
  $$\text{Lift}(C) = \frac{P(C)}{\prod_{j=1}^k P(S_j)}$$
  $\text{Lift} > 1$ indicates synergistic co-selection above random chance.

### 2.2 High-Earner Disproportion
- **High-Earner Proportion in Bundle**:
  $$P(\text{High} \mid C) = \frac{N_{C \cap \text{High}}}{N_C}$$

- **High-Earner Lift**:
  $$\text{High-Earner Lift}(C) = \frac{P(\text{High} \mid C)}{P(\text{High})}$$

---

## 3. Contingency Tables, Odds Ratios, and FDR

For each candidate bundle $C$, construct the $2 \times 2$ contingency table:

| | High Earner ($Y=1$) | Non-High Earner ($Y=0$) | Total |
|---|---|---|---|
| **Bundle Present ($C=1$)** | $a = N_{C \cap \text{High}}$ | $b = N_{C \setminus \text{High}}$ | $N_C$ |
| **Bundle Absent ($C=0$)** | $c = N_{\neg C \cap \text{High}}$ | $d = N_{\neg C \setminus \text{High}}$ | $N - N_C$ |

### 3.1 Haldane-Anscombe Corrected Odds Ratio
To prevent division by zero or extreme variance in sparse cells, add continuity correction $\delta = 0.5$ if $\min(a, b, c, d) = 0$:

$$\text{OR} = \frac{\tilde{a} \cdot \tilde{d}}{\tilde{b} \cdot \tilde{c}}$$

$$\text{SE}(\ln \text{OR}) = \sqrt{\frac{1}{\tilde{a}} + \frac{1}{\tilde{b}} + \frac{1}{\tilde{c}} + \frac{1}{\tilde{d}}}$$

$$95\% \text{ CI} = \exp\left(\ln \text{OR} \pm 1.96 \cdot \text{SE}(\ln \text{OR})\right)$$

### 3.2 Chi-Square Test with Yates Continuity Correction
$$\chi^2 = \frac{N \left(|ad - bc| - \frac{N}{2}\right)^2}{(a+b)(c+d)(a+c)(b+d)}$$

$$\text{p-value} = 1 - F_{\chi^2_1}(\chi^2)$$

### 3.3 Benjamini-Hochberg False Discovery Rate (FDR)
Given $M$ hypothesis tests with ordered raw p-values $p_{(1)} \le p_{(2)} \le \dots \le p_{(M)}$:

$$p_{(i)}^{\text{adj}} = \min_{j \ge i} \left( \min\left(1, \frac{M \cdot p_{(j)}}{j}\right) \right)$$

Reject $H_0$ if $p_{(i)}^{\text{adj}} < \alpha$ (with $\alpha = 0.05$).

---

## 4. Controlled Econometric Regressions

To confirm that the skill bundle effect is not an artifact of simply having more skills, longer tenure, or location:

1. **Multivariable Logistic Regression**:
   $$\text{logit}(P(Y_i = 1)) = \beta_0 + \beta_1 \cdot \mathbb{I}_{C, i} + \beta_2 \cdot \text{skill\_count}_i + \beta_3 \cdot \ln(\text{reviews}_i + 1) + \sum_{k} \gamma_k \cdot \text{Country}_{ik}$$

   Adjusted Odds Ratio: $\text{OR}_{\text{adj}} = \exp(\beta_1)$.

2. **Log-Earnings OLS Regression**:
   $$\ln(\text{total\_earnings}_i + 1) = \alpha_0 + \alpha_1 \cdot \mathbb{I}_{C, i} + \alpha_2 \cdot \text{skill\_count}_i + \alpha_3 \cdot \ln(\text{reviews}_i + 1) + \sum_{k} \delta_k \cdot \text{Country}_{ik} + \varepsilon_i$$

---

## 5. Topological Network & Louvain Modularity

- Graph $G = (V, E, W)$ where vertices $V$ are skills and edge weight $W_{uv}$ is co-occurrence frequency.
- **Betweenness Centrality**:
  $$C_B(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$$
- **Bridge Score**:
  $$\text{BridgeScore}(v) = \frac{C_B(v)}{C_D(v) + \epsilon}$$
- **Louvain Modularity Optimization**:
  $$Q = \frac{1}{2m} \sum_{i,j} \left[ W_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)$$

---

## 6. Differential TF-IDF & Topic Modeling

### 6.1 Log-Odds Differential Prominence
$$\text{LogDiff}(w) = \ln \left( \frac{\bar{\text{TFIDF}}_{\text{High}}(w) + \epsilon}{\bar{\text{TFIDF}}_{\text{Non-High}}(w) + \epsilon} \right)$$

### 6.2 Latent Dirichlet Allocation (LDA)
Generative model decomposing document-term matrix $X$ into topic distributions $\theta_d \sim \text{Dir}(\alpha)$ and term distributions $\phi_k \sim \text{Dir}(\beta)$.
