# TheLook eCommerce — Data & System Design Reference

**Project:** Product Analytics & Experimentation Engine  
**Dataset:** bigquery-public-data.thelook_ecommerce  
**Last Updated:** Day 2 EDA  
**Author:** Ayesha Amer

---

## How to Use This Document

This is the single source of truth for everything we learned about
the data on Day 2. Before writing any analysis query, come back here
first. It tells you which tables to use, what the columns mean, what
we found that was unexpected, and what decisions we made because of it.

---

## 1. What Data Do We Have?

TheLook is a synthetic e-commerce dataset built by Google's Looker
team. It simulates a real online retail business — customers browsing
a website, adding things to cart, placing orders. It lives on Google
BigQuery as a public dataset, meaning anyone can query it for free.

**Important:** TheLook is synthetic, meaning the data was
programmatically generated to look realistic, not pulled from a real
company's database. This does not affect the validity of our analysis
techniques — the SQL, statistics, and ML we apply are identical to
what you would do on real data. We disclose this honestly in our
README.

### The 7 Tables and What They Are

| Table                | Row Count | What It Is                                                                                                          |
| -------------------- | --------- | ------------------------------------------------------------------------------------------------------------------- |
| users                | 100,000   | Every customer who has ever signed up. One row per person.                                                          |
| orders               | 124,690   | Every order ever placed. One row per order.                                                                         |
| order_items          | 180,520   | Every individual item within every order. More rows than orders because one order can contain multiple products.    |
| products             | 29,120    | The product catalog — names, categories, brands, retail prices.                                                     |
| events               | 2,416,574 | Every single click, page view, cart add, and purchase on the website. This is our biggest and most important table. |
| inventory_items      | 487,585   | Individual units of inventory with cost price and sold timestamp.                                                   |
| distribution_centers | 10        | The 10 warehouse locations TheLook ships from.                                                                      |

---

## 2. Which Tables Does Our Project Actually Use?

We are building three analytical modules. Here is exactly which
tables each one depends on:

| Module                            | Tables Needed              | Why                                                                                                                     |
| --------------------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Module 1 — Clickstream & Funnel   | events, users              | events has every user action on the website. users lets us connect anonymous browsers to real customers.                |
| Module 2 — Retention Analytics    | orders, order_items, users | orders tells us when each customer purchased. users tells us when they signed up. Together they build cohort retention. |
| Module 3 — Experimentation Engine | events, orders             | We define experiment groups from events data and measure conversion outcomes from orders.                               |
| Module 4 — Customer Segmentation  | orders, order_items        | RFM scoring needs purchase recency, frequency, and total spend — all from these two tables.                             |

**This is why we focused our Day 2 exploration on events and orders.**
Products, inventory_items, and distribution_centers are not needed
for any of our four modules. We noted their row counts for
completeness and moved on. A data scientist does not explore data
they do not need — it wastes time and creates noise.

---

## 3. The Events Table — Deep Dive

This is the most complex and most important table in our project.
Module 1 is built entirely on it. Here is every column we will use
and exactly what it means.

### Column Reference

| Column          | Data Type | Can Be Null?          | What It Means                                                                                                                                                                                                  |
| --------------- | --------- | --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| id              | INTEGER   | No                    | Unique identifier for this specific event row. Not particularly useful for analysis — just a row ID.                                                                                                           |
| user_id         | INTEGER   | **YES — 46.54% null** | The ID of the logged-in customer who performed this action. NULL means the person was browsing anonymously — they had not logged in yet. This is expected and by design, not a data quality problem.           |
| session_id      | STRING    | No                    | A unique identifier for the browsing session. Think of a session as one continuous visit to the website. One user can have many sessions across many days.                                                     |
| sequence_number | INTEGER   | No                    | The order of this event within its session. Event 1 happened first, event 2 happened second, and so on.                                                                                                        |
| created_at      | TIMESTAMP | No                    | Exactly when this event happened, in UTC. This is the most important column for sessionization — we use time gaps between consecutive created_at values to detect where one session ends and a new one begins. |
| event_type      | STRING    | No                    | What the user actually did. See the Funnel section below for the full breakdown.                                                                                                                               |
| traffic_source  | STRING    | No                    | How the user arrived at the website — Adwords, Email, Organic, Facebook, etc. Useful for segmentation in Module 4.                                                                                             |
| browser         | STRING    | No                    | Which browser they used — Chrome, Firefox, IE, Safari, etc.                                                                                                                                                    |
| uri             | STRING    | No                    | The specific page URL they visited, e.g. /product/1234 or /cart.                                                                                                                                               |

### The user_id Null Problem — And Why It Is Not Actually a Problem

Nearly half of all events (46.54%, or 1,124,750 rows) have a null
user_id. This happens because people browse the website before logging
in. They land on the homepage, click through products, add things to
cart — all without an account. Only when they go to purchase do they
log in, and at that point their user_id appears.

This means a single real customer's journey within one session looks
like this in the raw data:
