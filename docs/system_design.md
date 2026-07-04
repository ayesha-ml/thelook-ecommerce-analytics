# TheLook eCommerce: Data & System Design Reference

**Project:** Product Analytics & Experimentation Engine  
**Dataset:** `bigquery-public-data.thelook_ecommerce`  
**Author:** Ayesha Amer

---

## Dataset Overview & Scope

The Look is a synthetic eCommerce dataset hosted on Google BigQuery. The data architecture consists of 7 tables, scoped based on the structural requirements of our four analytical modules. Production-grade logic is strictly restricted to modular `.py` and `.sql` files; notebooks are used exclusively for scratch work and mathematical prototyping.

### Core Tables & Project Relevance

| Table                  | Row Count | Scope & Utility                                                                                     |
| :--------------------- | :-------- | :-------------------------------------------------------------------------------------------------- |
| `events`               | 2,416,574 | **In Scope**: Primary clickstream source for Funnel Analysis & Experimentation (Modules 1 & 3).     |
| `orders`               | 124,690   | **In Scope**: Order placement logs used for Retention & Experimentation outcomes (Modules 2 & 3).   |
| `order_items`          | 180,520   | **In Scope**: Line-item transaction details for RFM Segmentation & Cohort analysis (Modules 2 & 4). |
| `users`                | 100,000   | **In Scope**: Customer profiles used for identity resolution and cohort mapping (Modules 1 & 2).    |
| `products`             | 29,120    | **Deferred**: Product catalog (deferred to Module 4 category deep dives).                           |
| `inventory_items`      | 487,585   | **Out of Scope**: Individual unit costs and real-time inventory tracking.                           |
| `distribution_centers` | 10        | **Out of Scope**: Warehouse fulfillment locations.                                                  |

---

## Clickstream & Funnel Architecture (`events`)

The `events` table captures granular web interactions. It is the core data asset for user sessionization, identity resolution, and behavioral funnels.

### Schema Attributes & Constraints

- **`id`** (INTEGER): Unique row identifier.
- **`session_id`** (STRING): Session tracking token. Acts as the primary partition key for sessionization.
- **`sequence_number`** (INTEGER): Chronological order of user actions within a single session.
- **`created_at`** (TIMESTAMP): Event timestamp (UTC). Inactivity gaps exceeding 30 minutes define session boundaries (Google Analytics standard).
- **`event_type`** (STRING): User action type (`home`, `department`, `product`, `cart`, `purchase`, `cancel`).
- **`user_id`** (INTEGER): Customer identifier. **Note: 46.54% of rows are NULL**, representing unauthenticated browsing before account authentication.

### Module 1: Sessionization and Identity Resolution Findings

#### Sessionization

The sessionization logic was verified using four automated unit tests against real users, and all of them passed successfully. The test results showed:

- Every user's very first recorded event was correctly initialized with a `session_sequence` of 1.
- The query caught all 41 real session boundaries where a user was inactive for more than 30 minutes.
- All 313 events that happened within that active 30-minute window were correctly grouped together without falsely spinning up new sessions.
- The total session count perfectly matched the number of boundary flags for the test users.

#### Identity Resolution

For the user stitching layer, the logic was implemented using `FIRST_VALUE(user_id IGNORE NULLS)` partitioned strictly by the `session_id`.

During development, an interesting design challenge came up. The initial plan considered partitioning by both `session_id` and the verified `session_sequence`. However, tracing through the data revealed that this would completely orphan any anonymous events that happened right before a user authenticated within that same window. Those early events would never get resolved. Keeping the partition solely on `session_id` fixed this, because identity (tracking who someone is) and session boundaries (counting individual visits) are two entirely different concepts that shouldn't share a partition key.

Testing this on real mixed sessions uncovered a major characteristic of this specific dataset: TheLook's tracking system never lets a single `session_id` cross the anonymous-to-authenticated boundary. Every single `session_id` in the raw data is either entirely anonymous or entirely authenticated, never a mix of both. Because of how the data is generated, the identity resolution query doesn't actually have any unauthenticated rows to stitch backward.

Even though the dataset doesn't trigger the stitching behavior, the module was kept exactly as it is. The SQL architecture is completely correct, computationally sound, and represents a standard data engineering pattern. On a real production clickstream where an anonymous cookie gets linked to a user profile at checkout, this exact query handles the backward propagation flawlessly. Documenting this constraint clearly in the system design shows a solid, honest understanding of data quality auditing, which makes for a great technical talking point.

## Clickstream Funnel & Leakage Analytics (`events`)

### Methodology & Data Grain

To map the user conversion journey, the clickstream event grain (2.4M rows) was aggregated into an order-agnostic Milestone Prevalence Matrix at a strict session grain (`session_id`), yielding 682,025 unique sessions.

Instead of forcing a rigid, linear timestamp sequence, which breaks down under non-linear browsing behaviors like page refreshes and multi-tabbing, the architecture evaluates the total footprint of a session. Binary flags track whether a milestone was reached at any point during the session.

To isolate the exact drop-off point, a derived categorical metric named `abandonment_stage` uses top-down conditional prioritization to tag each session by the highest-intent milestone achieved before termination. The evaluation filters rows sequentially, prioritizing completed purchases first, followed by checkout entries, product views, department browsing, and home page landings.

### Funnel Metrics & Diagnostic Findings

The distribution analysis of milestone flags and final abandonment states yielded the following matrix:

| Milestone / Stage    | Total Sessions | Traffic Exposure (% of Total) | Resulting Abandonment Stage | Share of Total Sessions (%) |
| :------------------- | :------------- | :---------------------------- | :-------------------------- | :-------------------------- |
| `reached_home`       | 88,179         | 12.9%                         | _Abandoned at Department_   | 0.0%                        |
| `reached_department` | 431,551        | 63.3%                         | _Abandoned at Product_      | 0.0%                        |
| `reached_product`    | 682,025        | 100.0%                        | **Abandoned at Cart**       | **36.6%**                   |
| `reached_cart`       | 432,205        | 63.4%                         | **Abandoned at Checkout**   | **36.7%**                   |
| `reached_purchase`   | 182,025        | 26.7%                         | **Completed Purchase**      | **26.7%**                   |

### Data Quality & Architectural Insights

1. **Inverted Funnel Anomaly:** Standard e-commerce funnels exhibit a wide-top pyramid starting at the homepage. Here, product reach sits at exactly 100.0%, while homepage traffic is captured at only 12.9%. In a production ecosystem, this pattern implies a highly optimized deep-linking or performance-marketing model where traffic completely bypasses the landing page. In this specific environment, it highlights a hardcoded constraint within the synthetic data generation engine, which mandates at least one product view per valid session.
2. **Impact on Leakage Math:** Because a product interaction is a universal constant across all sessions, the conditional sorting logic naturally terminates before hitting lower-tier stages. Consequently, "Abandoned at Home," "Abandoned at Department," and "Bounced Immediately" mathematically resolve to 0.0%.
3. **Primary Growth Friction Points:** Growth analytics and optimization efforts should focus entirely on the two true leakage buckets:
   - **Cart Abandonment (36.6%):** High product interest that failed to clear the "Add to Cart" intent barrier. Points to pricing friction, missing reviews, or weak product-page layouts.
   - **Checkout Leakage (36.7%):** High-intent users who built a cart but dropped out during the shipping configuration, account creation, or payment collection phases.
