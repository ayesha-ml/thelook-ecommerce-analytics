-- =============================================================
-- cohort_retention.sql
-- Purpose: Build monthly cohort retention matrix using true 
--          acquisition tracking to isolate repeat buyer behavior.
-- Dataset: bigquery-public-data.thelook_ecommerce.orders
-- Author:  Ayesha Amer
-- =============================================================

WITH user_acquisition AS (
    -- Grouping by user_id means we MUST aggregate the created_at column using MIN()
    SELECT 
        user_id,
        DATE_TRUNC(MIN(DATE(created_at)), MONTH) AS cohort_month 
    FROM `bigquery-public-data.thelook_ecommerce.orders`
    GROUP BY user_id
), 

orders_with_cohort AS (
    SELECT 
        o.user_id,
        c.cohort_month,
        DATE_TRUNC(DATE(o.created_at), MONTH) AS order_month,
        DATE_DIFF(
            DATE_TRUNC(DATE(o.created_at), MONTH), 
            c.cohort_month, 
            MONTH
        ) AS months_since_first
    FROM `bigquery-public-data.thelook_ecommerce.orders` o 
    JOIN user_acquisition c ON o.user_id = c.user_id
    WHERE o.status IN ('Complete','Shipped')
)

SELECT
    cohort_month,
    COUNT(DISTINCT CASE WHEN months_since_first = 0 THEN user_id END) AS m0,
    COUNT(DISTINCT CASE WHEN months_since_first = 1 THEN user_id END) AS m1,
    COUNT(DISTINCT CASE WHEN months_since_first = 2 THEN user_id END) AS m2,
    COUNT(DISTINCT CASE WHEN months_since_first = 3 THEN user_id END) AS m3,
    COUNT(DISTINCT CASE WHEN months_since_first = 6 THEN user_id END) AS m6
FROM orders_with_cohort
GROUP BY cohort_month
ORDER BY cohort_month;