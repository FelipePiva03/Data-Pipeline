-- NYC Taxi Trips - Silver Layer
-- This table is populated by the Spark transformer script
-- dbt will ensure the table exists with the correct schema

{{
    config(
        materialized='table',
        schema='silver',
        indexes=[
            {'columns': ['tpep_pickup_datetime']},
            {'columns': ['tpep_dropoff_datetime']},
            {'columns': ['PULocationID']},
            {'columns': ['DOLocationID']},
            {'columns': ['pickup_borough']},
            {'columns': ['dropoff_borough']},
            {'columns': ['partition_year', 'partition_month']},
            {'columns': ['payment_type']}
        ]
    )
}}

-- This creates an empty table with the correct schema
-- The Spark transformer will insert data using mode='append' or 'overwrite'

SELECT
    NULL::BIGINT as trip_id,
    NULL::INTEGER as VendorID,
    NULL::TIMESTAMP as tpep_pickup_datetime,
    NULL::TIMESTAMP as tpep_dropoff_datetime,
    NULL::DOUBLE PRECISION as passenger_count,
    NULL::DOUBLE PRECISION as trip_distance,
    NULL::DOUBLE PRECISION as RatecodeID,
    NULL::VARCHAR(1) as store_and_fwd_flag,
    NULL::INTEGER as PULocationID,
    NULL::INTEGER as DOLocationID,
    NULL::INTEGER as payment_type,
    NULL::DOUBLE PRECISION as fare_amount,
    NULL::DOUBLE PRECISION as extra,
    NULL::DOUBLE PRECISION as mta_tax,
    NULL::DOUBLE PRECISION as tip_amount,
    NULL::DOUBLE PRECISION as tolls_amount,
    NULL::DOUBLE PRECISION as improvement_surcharge,
    NULL::DOUBLE PRECISION as total_amount,
    NULL::DOUBLE PRECISION as congestion_surcharge,
    NULL::DOUBLE PRECISION as Airport_fee,

    -- Pickup Location Enrichment
    NULL::VARCHAR(100) as pickup_borough,
    NULL::VARCHAR(255) as pickup_zone,
    NULL::VARCHAR(50) as pickup_service_zone,

    -- Dropoff Location Enrichment
    NULL::VARCHAR(100) as dropoff_borough,
    NULL::VARCHAR(255) as dropoff_zone,
    NULL::VARCHAR(50) as dropoff_service_zone,

    -- Metadata
    NULL::TIMESTAMP as processing_ts,
    NULL::INTEGER as partition_year,
    NULL::INTEGER as partition_month,

    CURRENT_TIMESTAMP as created_at,
    CURRENT_TIMESTAMP as updated_at

WHERE FALSE  -- This ensures no rows are inserted by dbt
