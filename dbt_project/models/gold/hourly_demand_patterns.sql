-- Hourly Demand Patterns Analysis
-- Analyzes trip patterns by hour of day and day of week

{{
    config(
        materialized='table',
        schema='gold'
    )
}}

WITH silver_trips AS (
    SELECT *
    FROM {{ ref('nyc_trips_silver') }}
    WHERE tpep_pickup_datetime IS NOT NULL
)

SELECT
    pickup_borough,
    EXTRACT(HOUR FROM tpep_pickup_datetime) as hour_of_day,
    EXTRACT(DOW FROM tpep_pickup_datetime) as day_of_week,  -- 0=Sunday, 6=Saturday

    -- Trip metrics
    COUNT(*) as total_trips,
    AVG(trip_distance) as avg_distance,
    AVG(total_amount) as avg_fare,

    -- Duration (in minutes)
    AVG(EXTRACT(EPOCH FROM (tpep_dropoff_datetime - tpep_pickup_datetime)) / 60) as avg_duration_minutes,

    CURRENT_TIMESTAMP as created_at

FROM silver_trips
WHERE tpep_dropoff_datetime > tpep_pickup_datetime  -- Valid trips only
GROUP BY
    pickup_borough,
    EXTRACT(HOUR FROM tpep_pickup_datetime),
    EXTRACT(DOW FROM tpep_pickup_datetime)
