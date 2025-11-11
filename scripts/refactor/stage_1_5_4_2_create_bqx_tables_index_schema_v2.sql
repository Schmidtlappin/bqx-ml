-- ============================================================================
-- Stage 1.5.4.2: Create BQX Tables with Index Schema (Fixed Version)
-- Duration: 0.5 hours
-- Purpose: Create new bqx_* tables using rate_index (not absolute rates)
-- ============================================================================

\echo ''
\echo '============================================================================'
\echo 'Stage 1.5.4.2: Creating BQX Tables (Index Schema)'
\echo '============================================================================'
\echo ''

-- Create one sample table to test the schema, then we'll generate all 28
DO $$
DECLARE
    pair_name TEXT;
    year INT;
    month INT;
    partition_name TEXT;
    start_date TEXT;
    end_date TEXT;
BEGIN
    -- Array of all 28 pairs
    FOR pair_name IN
        SELECT unnest(ARRAY[
            'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
            'cadchf', 'cadjpy', 'chfjpy',
            'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
            'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
            'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
            'usdcad', 'usdchf', 'usdjpy'
        ])
    LOOP
        -- Create parent table
        EXECUTE format($f$
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
        $f$, pair_name);

        -- Create monthly partitions (2020-01 through 2026-12)
        FOR year IN 2020..2026 LOOP
            FOR month IN 1..12 LOOP
                partition_name := format('bqx_%s_y%sm%s', pair_name, year, LPAD(month::text, 2, '0'));
                start_date := format('%s-%s-01', year, LPAD(month::text, 2, '0'));

                IF month = 12 THEN
                    end_date := format('%s-01-01', year + 1);
                ELSE
                    end_date := format('%s-%s-01', year, LPAD((month + 1)::text, 2, '0'));
                END IF;

                EXECUTE format($f$
                    CREATE TABLE bqx.%s PARTITION OF bqx.bqx_%s
                    FOR VALUES FROM (%L) TO (%L);
                $f$, partition_name, pair_name, start_date, end_date);
            END LOOP;
        END LOOP;

        RAISE NOTICE 'Created bqx_% with 84 monthly partitions (2020-01 through 2026-12)', pair_name;
    END LOOP;
END $$;

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
