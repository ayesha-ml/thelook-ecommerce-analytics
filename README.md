# Product Analytics & Experimentation Engine

An end-to-end product analytics platform built on Google BigQuery's `thelook_ecommerce` dataset. This repository demonstrates the core technical and analytical workflow of a Growth Data Scientist: architecting high-performance SQL pipelines, modeling user clickstreams, running statistical experiments, and building predictive behavioral segments to drive product-led growth.

---

## Architecture

- BigQuery (TheLook eCommerce public dataset)

- SQL Window Functions (sessionization, cohort generation, RFM)

- Python Engine (scipy, statsmodels, scikit-learn)

- Streamlit Dashboard (Multi-page app with cached BigQuery connections)

---

## The Four Business Questions

| Module                 | Business Question                                      | Core Technique                                                                |
| :--------------------- | :----------------------------------------------------- | :---------------------------------------------------------------------------- |
| **1. Funnel**          | Where are users dropping off in the purchase journey?  | Clickstream sessionization, identity resolution, funnel milestone aggregation |
| **2. Retention**       | Are we keeping the customers we acquire?               | Monthly cohort retention matrix, MoM revenue trend with `LAG()`               |
| **3. Experimentation** | Did our product change drive a measurable improvement? | Power analysis, SRM detection, two-sample pooled Z-test                       |
| **4. Segmentation**    | Which customers are worth investing in?                | RFM NTILE scoring, RobustScaler, K-Means clustering                           |

---

## Dashboard Walkthrough

### 1. Funnel Analysis

_Where are we losing users in the purchase journey?_
![Funnel Analysis](assets/funnel.png)

### 2. Cohort Retention Analytics

_Are we retaining the cohorts we acquire, and how is it impacting growth trends?_
![Retention Analytics](assets/retention.png)

### 3. Experimentation Engine

_Rigorous frequentist framework to evaluate product changes._
![Experimentation Engine](assets/experimentation.PNG)

### 4. Customer Segmentation

_ML-driven behavioral clustering to target high-value customer cohorts._

#### Segment Distribution

The K-Means pipeline ($K=4$) segregates users based on their scaled Recency and Monetary features, drawing clear boundaries between active spenders and decaying cohorts:

![Customer Segments - Recency vs Monetary Value](assets/segmentation_scatter.png)

#### Cohort Profiles & Revenue Impact

By mapping cluster assignments back to raw business metrics, we translate mathematical centroids into targetable financial buckets, identifying over **$1.1M in high-yield revenue at risk**:

![Customer Segment Profiles Table](assets/segmentation_table.png)

![Total Revenue at Stake by Segment](assets/segmentation_revenue_bar.png)

- **Champions:** Reward with loyalty perks, early product access, and referral incentives.
- **Promising:** Onboard with targeted cross-category recommendations and upsell flows.
- **At Risk:** Target immediately with win-back campaigns, personalized discounts, and churn feedback surveys.
- **Lost:** Relegate to low-cost automated email reactivation flows to preserve marketing ad spend.

---

## Key Business Insights

- **Funnel Bottlenecks:** $26.6\%$ of all sessions result in a completed purchase. While $63.3\%$ of users successfully populate a shopping cart, only $42.0\%$ of those cart-sessions convert to checkout. This means **$58.0\%$ of high-intent shopping carts are abandoned** before transaction completion, signaling major checkout friction.
- **Acquisition Dependence:** Average Month-1 retention sits at an incredibly low **$2.4\%$**, and Month-3 drops to **$2.2\%$**. The revenue growth curve is highly structurally fragile-driven almost entirely by compounding top-of-funnel acquisition of new customers, rather than sustainable cohort retention.
- **Experiment Null-Finding:** In our signup-date cohort experiment, the treatment and control convert at statistically indistinguishable rates ($53.06\%$ vs $52.84\%$, $p = 0.493$). Backed by a sample size $5\times$ greater than our minimum required power threshold, we confirm this is a robust null finding with zero meaningful conversion impact.
- **Segment Target:** Our K-Means clustering identified a high-priority "At Risk" segment representing **2,222 customers who hold 1.1 M in historical revenue ($19\%$ of total volume)**. Despite an industry-leading average order value of $508$, these customers have not transacted in an average of $497$ days, making them our prime target for win-back campaigns.

---

## SQL Design Decisions

This platform intentionally pushes heavy computation down to Google BigQuery, keeping the Python application layer fast, clean, and highly scalable:

- `ROW_NUMBER()`: Used for deterministic cohort assignment to isolate and tag a user’s absolute first-order purchase timestamp, avoiding aggregation bias.
- `LAG()`: Utilized to calculate Month-over-Month (MoM) revenue growth rates by referencing the previous chronological row without costly self-joins.
- `NTILE(5)`: Applied directly in-warehouse to generate equal-sized quintile bins for RFM scoring, mitigating the skewness of standard linear binning on heavily right-skewed transaction data.
- `FIRST_VALUE(IGNORE NULLS)`: Implemented for session-level identity resolution, allowing anonymous pre-login page views to be correctly back-attributed to a user once they authenticate.

---

## Statistical Methodology

### Three-Stage Experimentation Pipeline

To prevent common industry errors like "p-hacking" or ignoring selection bias, the A/B testing engine enforces a strict chronological flow:

1.  **Pre-Test Power Analysis:** Calculates the Minimum Detectable Effect (MDE) and the corresponding required sample size per variant _before_ the experiment is run. This ensures the test is statistically empowered to register true performance changes.
2.  **SRM (Sample Ratio Mismatch) Check:** A chi-square ($\chi^2$) goodness-of-fit test evaluates whether the observed group split matches the intended experimental split. A mismatch flags selection bias or traffic assignment corruption, immediately aborting downstream statistical tests.
3.  **Two-Sample Proportion Z-Test:** Implements a pooled standard error to calculate the test's $Z$-statistic (under the null hypothesis $H_0: p_{\text{control}} = p_{\text{treatment}}$), but uses an unpooled standard error to construct the $95\%$ confidence interval around the absolute lift.

---

## Technical Stack

- **Cloud Data Warehouse:** Google BigQuery (GoogleSQL)
- **Statistical Analysis:** `scipy.stats`, `statsmodels`
- **Machine Learning Pipeline:** `scikit-learn` (`RobustScaler`, `KMeans`)
- **Interactive Interface:** Streamlit (Cached BigQuery Clients)
- **Data Visualization:** Plotly Express

---

## Local Setup

### Requirements

- Python 3.11+
- GCP Service Account credentials with BigQuery Data Viewer permissions

```bash
# Clone the repository
git clone [https://github.com/ayesha-ml/thelook-ecommerce-analytics](https://github.com/ayesha-ml/thelook-ecommerce-analytics)
cd thelook-ecommerce-analytics

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install package dependencies
pip install -r requirements.txt

# Launch the Streamlit application
streamlit run app/dashboard.py
Note: On your initial run, Streamlit will request GCP OAuth authentication via your browser to securely query the BigQuery public dataset on-the-fly.Analytical LimitationsSynthetic Data Bias: The Looker team generated TheLook dataset algorithmically. This explains certain synthetic characteristics, such as the flat, extremely low customer retention curve ($2.4\%$ month-to-month), which deviates from real-world e-commerce dynamics.Quasi-Experimental Design: The experimentation engine uses a signup-date cohort split as a proxy experiment. Since traffic was not strictly randomized at the session level, findings represent association rather than direct, clean causality.Synthetic Session Identity: While the SQL code for anonymous-to-authenticated session identity resolution is production-ready, TheLook's synthetic schema does not bridge user actions across anonymous boundaries, resulting in zero naturally resolvable events.
- --

Author: Ayesha Amer
GitHub: https://github.com/ayesha-ml
```
