-- =============================================================
-- rfm_scoring.sql
-- Purpose : Compute Recency, Frequency, and Monetary scores
--           per customer using NTILE quintile ranking.
-- Filter  : Complete and Shipped orders only.
-- Author  : Ayesha Amer
-- =============================================================

WITH order_data AS (
    SELECT
        o.user_id,
        o.created_at,
        oi.sale_price
    FROM `bigquery-public-data.thelook_ecommerce.orders` o
    JOIN `bigquery-public-data.thelook_ecommerce.order_items` oi
        ON o.order_id = oi.order_id
    WHERE o.status IN ('Complete', 'Shipped')
),

dataset_anchor AS (
    SELECT DATE(MAX(created_at)) AS max_date FROM order_data
),

rfm_base AS (
    SELECT
        o.user_id,
        DATE_DIFF(
            (SELECT max_date FROM dataset_anchor),
            DATE(MAX(o.created_at)),
            DAY
        )  AS recency_days,
        COUNT(DISTINCT DATE(o.created_at)) AS frequency,
        ROUND(SUM(o.sale_price), 2)     AS monetary_value
    FROM order_data o
    GROUP BY o.user_id
)

SELECT
    user_id,
    recency_days,
    frequency,
    monetary_value,
    NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
    NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
    NTILE(5) OVER (ORDER BY monetary_value ASC) AS m_score
FROM rfm_base;