-- Stage 1.6.14 Part B: Create fibonacci_bqx (20 features, 672 partitions)
-- Action: CREATE TABLE (new BQX domain tables)
-- Schema: Standardized Fibonacci schema (20 features)

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
    RAISE NOTICE '=== Creating Fibonacci BQX Parent Tables (20 features) ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.fibonacci_bqx_%I (
                ts_utc TIMESTAMP NOT NULL,

                -- Retracement Levels (5 features)
                fib_retracement_236 NUMERIC,
                fib_retracement_382 NUMERIC,
                fib_retracement_500 NUMERIC,
                fib_retracement_618 NUMERIC,
                fib_retracement_786 NUMERIC,

                -- Extension Levels (4 features)
                fib_ext_1272 NUMERIC,
                fib_ext_1618 NUMERIC,
                fib_ext_2618 NUMERIC,
                fib_ext_4236 NUMERIC,

                -- Fibonacci Fan (3 features)
                fib_fan_upper NUMERIC,
                fib_fan_middle NUMERIC,
                fib_fan_lower NUMERIC,

                -- Fibonacci Arc (1 feature)
                fib_arc_radius NUMERIC,

                -- Pivot Points (3 features)
                pivot_point NUMERIC,
                resistance_1 NUMERIC,
                support_1 NUMERIC,

                -- Distance to Key Levels (4 features)
                dist_to_382 NUMERIC,
                dist_to_500 NUMERIC,
                dist_to_618 NUMERIC,
                dist_to_pivot NUMERIC,

                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc)', pair_name);
    END LOOP;

    RAISE NOTICE '✅ Created 28 fibonacci_bqx parent tables (20 features each)';
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
    RAISE NOTICE '=== Creating Fibonacci BQX Partitions ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        FOR year IN 2024..2025
        LOOP
            FOR month IN 1..12
            LOOP
                start_date := make_date(year, month, 1);
                end_date := start_date + INTERVAL '1 month';
                partition_name := format('fibonacci_bqx_%s_%s_%s',
                                        pair_name, year, lpad(month::TEXT, 2, '0'));

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I
                    PARTITION OF bqx.fibonacci_bqx_%I
                    FOR VALUES FROM (%L) TO (%L)',
                    partition_name, pair_name, start_date, end_date);

                partition_count := partition_count + 1;

                IF partition_count % 100 = 0 THEN
                    RAISE NOTICE 'Created % partitions...', partition_count;
                END IF;
            END LOOP;
        END LOOP;
    END LOOP;

    RAISE NOTICE '✅ Created % fibonacci_bqx partitions', partition_count;
END $$;

COMMIT;

\echo '✅ Stage 1.6.14 Part B Complete: fibonacci_bqx created (20 features, 672 partitions)'
