-- =============================================================
-- identity_resolution.sql
-- Purpose: Propagate authenticated user_id to anonymous events
--          sharing the same raw tracking cookie (session_id).
-- Dataset: bigquery-public-data.thelook_ecommerce.events
-- Author:  Ayesha Amer
-- =============================================================

WITH identity_resolution AS (
    SELECT 
        session_id AS raw_session_id,
        event_type,
        created_at,
        user_id AS raw_user_id,
        FIRST_VALUE(user_id IGNORE NULLS) OVER(
            PARTITION BY session_id
            ORDER BY created_at
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS resolved_user_id,
        traffic_source,
        browser,
        uri
    FROM `bigquery-public-data.thelook_ecommerce.events`
)
SELECT 
    raw_session_id,
    resolved_user_id,
    raw_user_id,
    event_type,
    created_at,
    traffic_source,
    browser,
    uri,
    CASE 
        WHEN raw_user_id IS NULL AND resolved_user_id IS NOT NULL THEN 'anonymous resolved'
        WHEN raw_user_id IS NOT NULL THEN 'authenticated'  
        ELSE 'anonymous unresolved'
    END AS resolution_status
FROM identity_resolution;