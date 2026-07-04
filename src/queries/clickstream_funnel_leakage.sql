-- =====================================================================
-- clickstream_funnel_leakage.sql
-- Purpose: Tracks which pages users visit during a single session to 
--          see exactly where they drop off and stop browsing.
-- Dataset: bigquery-public-data.thelook_ecommerce.events
-- Author:  Ayesha Amer
-- =====================================================================

WITH session_flags AS (
    SELECT
        session_id,
        MIN(created_at) AS session_start,
        COUNT(*) AS total_events,
        -- Mark 1 if they hit the page at any point during the session, 0 if they didn't
        MAX(CASE WHEN event_type = 'home'       THEN 1 ELSE 0 END) AS reached_home,
        MAX(CASE WHEN event_type = 'department' THEN 1 ELSE 0 END) AS reached_department,
        MAX(CASE WHEN event_type = 'product'    THEN 1 ELSE 0 END) AS reached_product,
        MAX(CASE WHEN event_type = 'cart'       THEN 1 ELSE 0 END) AS reached_cart,
        MAX(CASE WHEN event_type = 'purchase'   THEN 1 ELSE 0 END) AS reached_purchase
    FROM `bigquery-public-data.thelook_ecommerce.events`
    GROUP BY session_id
)

SELECT 
    *,
    -- Find the last step the user reached before giving up
    CASE 
        WHEN reached_purchase   = 1 THEN 'Completed Purchase'
        WHEN reached_cart       = 1 THEN 'Abandoned at Checkout'
        WHEN reached_product    = 1 THEN 'Abandoned at Cart'
        WHEN reached_department = 1 THEN 'Abandoned at Product'
        WHEN reached_home       = 1 THEN 'Abandoned at Department'
        ELSE 'Bounced Immediately'
    END AS abandonment_stage
FROM session_flags;