-- ============================================================================
-- Stage 1.5.4.2: Create BQX Tables with Index Schema
-- Duration: 0.5 hours
-- Purpose: Create new bqx_* tables using rate_index (not absolute rates)
-- ============================================================================

\echo ''
\echo '============================================================================'
\echo 'Stage 1.5.4.2: Creating BQX Tables (Index Schema)'
\echo '============================================================================'
\echo ''
\echo 'Schema Changes from Old:'
\echo '- rate → rate_index (forex index around 100)'
\echo '- bqx_max → bqx_max_index'
\echo '- bqx_min → bqx_min_index'
\echo '- bqx_avg → bqx_avg_index'
\echo '- bqx_stdev → bqx_stdev_index'
\echo '- REMOVED: 24 _pct fields (no longer needed with index)'
\echo ''

-- ============================================================================
-- Template BQX Table Schema (Index-Based)
-- ============================================================================

-- We'll create a function to generate tables for all 28 pairs
CREATE OR REPLACE FUNCTION create_bqx_table_index_schema(pair_name TEXT) RETURNS void AS $$
BEGIN
    EXECUTE format('
        CREATE TABLE bqx.bqx_%s (
            ts_utc TIMESTAMP WITH TIME ZONE NOT NULL,
            rate_index DOUBLE PRECISION,

            -- Window 15 metrics
            w15_bqx_return DOUBLE PRECISION,
            w15_bqx_max_index DOUBLE PRECISION,
            w15_bqx_min_index DOUBLE PRECISION,
            w15_bqx_avg_index DOUBLE PRECISION,
            w15_bqx_stdev_index DOUBLE PRECISION,
            w15_bqx_endpoint DOUBLE PRECISION,

            -- Window 30 metrics
            w30_bqx_return DOUBLE PRECISION,
            w30_bqx_max_index DOUBLE PRECISION,
            w30_bqx_min_index DOUBLE PRECISION,
            w30_bqx_avg_index DOUBLE PRECISION,
            w30_bqx_stdev_index DOUBLE PRECISION,
            w30_bqx_endpoint DOUBLE PRECISION,

            -- Window 45 metrics
            w45_bqx_return DOUBLE PRECISION,
            w45_bqx_max_index DOUBLE PRECISION,
            w45_bqx_min_index DOUBLE PRECISION,
            w45_bqx_avg_index DOUBLE PRECISION,
            w45_bqx_stdev_index DOUBLE PRECISION,
            w45_bqx_endpoint DOUBLE PRECISION,

            -- Window 60 metrics
            w60_bqx_return DOUBLE PRECISION,
            w60_bqx_max_index DOUBLE PRECISION,
            w60_bqx_min_index DOUBLE PRECISION,
            w60_bqx_avg_index DOUBLE PRECISION,
            w60_bqx_stdev_index DOUBLE PRECISION,
            w60_bqx_endpoint DOUBLE PRECISION,

            -- Window 75 metrics
            w75_bqx_return DOUBLE PRECISION,
            w75_bqx_max_index DOUBLE PRECISION,
            w75_bqx_min_index DOUBLE PRECISION,
            w75_bqx_avg_index DOUBLE PRECISION,
            w75_bqx_stdev_index DOUBLE PRECISION,
            w75_bqx_endpoint DOUBLE PRECISION,

            -- Aggregate metrics (using w75)
            agg_bqx_return DOUBLE PRECISION,
            agg_bqx_max_index DOUBLE PRECISION,
            agg_bqx_min_index DOUBLE PRECISION,
            agg_bqx_avg_index DOUBLE PRECISION,
            agg_bqx_stdev_index DOUBLE PRECISION,
            agg_bqx_range DOUBLE PRECISION,
            agg_bqx_volatility DOUBLE PRECISION,

            PRIMARY KEY (ts_utc)
        ) PARTITION BY RANGE (ts_utc);
    ', pair_name);

    -- Create monthly partitions (2020-01 through 2026-12)
    -- This covers historical + future data
    FOR year IN 2020..2026 LOOP
        FOR month IN 1..12 LOOP
            EXECUTE format('
                CREATE TABLE bqx.bqx_%s_y%sm%s PARTITION OF bqx.bqx_%s
                FOR VALUES FROM (''%s-%s-01'') TO (''%s-%s-01'');
            ',
            pair_name,
            year,
            LPAD(month::text, 2, ''0''),
            pair_name,
            year,
            LPAD(month::text, 2, ''0''),
            CASE WHEN month = 12 THEN year + 1 ELSE year END,
            CASE WHEN month = 12 THEN ''01'' ELSE LPAD((month + 1)::text, 2, ''0'') END
            );
        END LOOP;
    END LOOP;

    RAISE NOTICE 'Created bqx_% with 84 monthly partitions (2020-01 through 2026-12)', pair_name;
END;
$$ LANGUAGE plpgsql;

\echo 'Creating BQX tables for all 28 pairs...'
\echo ''

-- Create tables for all 28 pairs
SELECT create_bqx_table_index_schema('audcad');
SELECT create_bqx_table_index_schema('audchf');
SELECT create_bqx_table_index_schema('audjpy');
SELECT create_bqx_table_index_schema('audnzd');
SELECT create_bqx_table_index_schema('audusd');
SELECT create_bqx_table_index_schema('cadchf');
SELECT create_bqx_table_index_schema('cadjpy');
SELECT create_bqx_table_index_schema('chfjpy');
SELECT create_bqx_table_index_schema('euraud');
SELECT create_bqx_table_index_schema('eurcad');
SELECT create_bqx_table_index_schema('eurchf');
SELECT create_bqx_table_index_schema('eurgbp');
SELECT create_bqx_table_index_schema('eurjpy');
SELECT create_bqx_table_index_schema('eurnzd');
SELECT create_bqx_table_index_schema('eurusd');
SELECT create_bqx_table_index_schema('gbpaud');
SELECT create_bqx_table_index_schema('gbpcad');
SELECT create_bqx_table_index_schema('gbpchf');
SELECT create_bqx_table_index_schema('gbpjpy');
SELECT create_bqx_table_index_schema('gbpnzd');
SELECT create_bqx_table_index_schema('gbpusd');
SELECT create_bqx_table_index_schema('nzdcad');
SELECT create_bqx_table_index_schema('nzdchf');
SELECT create_bqx_table_index_schema('nzdjpy');
SELECT create_bqx_table_index_schema('nzdusd');
SELECT create_bqx_table_index_schema('usdcad');
SELECT create_bqx_table_index_schema('usdchf');
SELECT create_bqx_table_index_schema('usdjpy');

-- Clean up function
DROP FUNCTION create_bqx_table_index_schema(TEXT);

\echo ''
\echo '============================================================================'
\echo 'Stage 1.5.4.2 Complete: BQX Tables Created with Index Schema'
\echo '============================================================================'
\echo ''
\echo 'Summary:'
\echo '- 28 parent tables created'
\echo '- 2,352 partitions created (28 pairs × 84 months)'
\echo '- Schema uses rate_index (not absolute rates)'
\echo '- All max/min/avg fields have _index suffix'
\echo '- No _pct fields (24 fields removed from old schema)'
\echo ''
\echo 'Next Steps:'
\echo '1. Run Stage 1.5.4.3: Backfill using backward_worker_index.py'
\echo '2. Estimated time: 7 hours (parallel execution)'
\echo ''
