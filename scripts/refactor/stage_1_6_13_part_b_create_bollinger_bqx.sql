-- Stage 1.6.13 Part B: Create bollinger_bqx (20 features, 672 partitions)
-- Action: CREATE TABLE (new BQX domain tables)
-- Schema: Identical to expanded bollinger_rate

\timing on
\set ON_ERROR_STOP on

BEGIN;

-- Create Parent Tables (28 pairs)
DO $$
DECLARE
    pair_name TEXT;
    pairs TEXT[] := ARRAY['audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
                          'cadchf', 'cadjpy', 'chfjpy',
                          'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
                          'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
                          'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
                          'usdcad', 'usdchf', 'usdjpy'];
BEGIN
    RAISE NOTICE '=== Creating Bollinger BQX Parent Tables (20 features) ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.bollinger_bqx_%I (
                ts_utc TIMESTAMP NOT NULL,

                -- Upper Band (4 features)
                bb_upper_20 NUMERIC,
                bb_upper_30 NUMERIC,
                bb_upper_60 NUMERIC,
                bb_upper_120 NUMERIC,

                -- Middle Band (4 features)
                bb_middle_20 NUMERIC,
                bb_middle_30 NUMERIC,
                bb_middle_60 NUMERIC,
                bb_middle_120 NUMERIC,

                -- Lower Band (4 features)
                bb_lower_20 NUMERIC,
                bb_lower_30 NUMERIC,
                bb_lower_60 NUMERIC,
                bb_lower_120 NUMERIC,

                -- Bandwidth (4 features)
                bb_width_20 NUMERIC,
                bb_width_30 NUMERIC,
                bb_width_60 NUMERIC,
                bb_width_120 NUMERIC,

                -- %%B Indicator (2 features)
                bb_percent_b_20 NUMERIC,
                bb_percent_b_60 NUMERIC,

                -- Band Slope (2 features)
                bb_slope_20 NUMERIC,
                bb_slope_60 NUMERIC,

                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc)', pair_name);
    END LOOP;

    RAISE NOTICE '✅ Created 28 bollinger_bqx parent tables (20 features each)';
END $$;

-- Create Partitions (28 pairs × 24 months = 672 partitions)
DO $$
DECLARE
    pair_name TEXT;
    year INT;
    month INT;
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
    pairs TEXT[] := ARRAY['audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
                          'cadchf', 'cadjpy', 'chfjpy',
                          'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
                          'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
                          'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
                          'usdcad', 'usdchf', 'usdjpy'];
    partition_count INT := 0;
BEGIN
    RAISE NOTICE '=== Creating Bollinger BQX Partitions ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        FOR year IN 2024..2025
        LOOP
            FOR month IN 1..12
            LOOP
                start_date := make_date(year, month, 1);
                end_date := start_date + INTERVAL '1 month';
                partition_name := format('bollinger_bqx_%s_%s_%s',
                                        pair_name, year, lpad(month::TEXT, 2, '0'));

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I
                    PARTITION OF bqx.bollinger_bqx_%I
                    FOR VALUES FROM (%L) TO (%L)',
                    partition_name, pair_name, start_date, end_date);

                partition_count := partition_count + 1;

                IF partition_count % 100 = 0 THEN
                    RAISE NOTICE 'Created % partitions...', partition_count;
                END IF;
            END LOOP;
        END LOOP;
    END LOOP;

    RAISE NOTICE '✅ Created % bollinger_bqx partitions', partition_count;
END $$;

COMMIT;

\echo '✅ Stage 1.6.13 Part B Complete: bollinger_bqx created (20 features, 672 partitions)'
