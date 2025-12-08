-- Daily Trip Statistics by Borough
-- This model aggregates silver data into daily statistics

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
    DATE(tpep_pickup_datetime) as trip_date,
    pickup_borough,
    dropoff_borough,

    -- Trip counts
    COUNT(*) as total_trips,

    -- Distance metrics
    SUM(trip_distance) as total_distance,
    AVG(trip_distance) as avg_trip_distance,

    -- Revenue metrics
    SUM(total_amount) as total_revenue,
    AVG(fare_amount) as avg_fare_amount,
    AVG(tip_amount) as avg_tip_amount,
    SUM(tip_amount) as total_tips,

    -- Passenger metrics
    AVG(passenger_count) as avg_passengers,

    -- Payment distribution
    SUM(CASE WHEN payment_type = 1 THEN 1 ELSE 0 END) as credit_card_trips,
    SUM(CASE WHEN payment_type = 2 THEN 1 ELSE 0 END) as cash_trips,

    CURRENT_TIMESTAMP as created_at

FROM silver_trips
GROUP BY
    DATE(tpep_pickup_datetime),
    pickup_borough,
    dropoff_borough
