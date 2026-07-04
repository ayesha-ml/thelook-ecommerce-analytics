-- =============================================================
-- monthly_revenue.sql
-- Purpose: Calculate Month-over-Month (MoM) revenue growth
--          using window functions and safe division.
-- Dataset: bigquery-public-data.thelook_ecommerce
-- Author:  Ayesha Amer
-- =============================================================

WITH monthly_sales AS(
    SELECT DATE_TRUNC(o.created_at,MONTH) as month,
    SUM (oi.sale_price) AS revenue

    FROM `bigquery-public-data.thelook_ecommerce.orders` o
    JOIN `bigquery-public-data.thelook_ecommerce.order_items` oi
    ON o.order_id = oi.order_id

    WHERE o.status IN ('Complete', 'Shipped')
    GROUP BY month
)
SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) as prev_month_revenue,
    ROUND(
        SAFE_DIVIDE(
            revenue - LAG(revenue) OVER (ORDER BY month),
            LAG(revenue) OVER (ORDER BY month)
        ) *100,2
    ) AS MOM_growth_pct
FROM monthly_sales
ORDER BY month;

