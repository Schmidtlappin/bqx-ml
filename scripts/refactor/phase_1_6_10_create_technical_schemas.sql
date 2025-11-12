-- Phase 1.6.10-1.6.11: Create Technical Indicators Schemas (Rate & BQX)
-- Creates parent tables and partitions for both rate-centric and BQX-centric technical indicators
-- 28 pairs × 12 months × 2 architectures = 672 total tables
-- Estimated Time: 30 minutes
-- Author: BQX ML Team
-- Date: 2025-11-12

\timing on
\set ON_ERROR_STOP on

BEGIN;

-- ============================================================================
-- CREATE PARENT TABLES FOR TECHNICAL_RATE
-- ============================================================================

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
    RAISE NOTICE '=== Creating Technical Rate Parent Tables ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.technical_rate_%I (
                ts_utc TIMESTAMP NOT NULL,

                -- RSI (Relative Strength Index)
                rsi_14 NUMERIC,
                rsi_21 NUMERIC,

                -- MACD (Moving Average Convergence Divergence)
                macd_line NUMERIC,
                macd_signal NUMERIC,
                macd_histogram NUMERIC,

                -- Stochastic Oscillator
                stoch_k NUMERIC,
                stoch_d NUMERIC,

                -- Additional Momentum Indicators
                cci_20 NUMERIC,            -- Commodity Channel Index
                williams_r_14 NUMERIC,      -- Williams %%R
                roc_12 NUMERIC,             -- Rate of Change

                -- Volatility
                atr_14 NUMERIC,             -- Average True Range

                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc)', pair_name);

        RAISE NOTICE 'Created technical_rate_% parent table', pair_name;
    END LOOP;

    RAISE NOTICE '✅ Created % technical_rate parent tables', array_length(pairs, 1);
END $$;

-- ============================================================================
-- CREATE PARTITIONS FOR TECHNICAL_RATE (2024-01 through 2024-12)
-- ============================================================================

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
    RAISE NOTICE '=== Creating Technical Rate Partitions ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        FOR year IN 2024..2024  -- Extend to 2025 if needed
        LOOP
            FOR month IN 1..12
            LOOP
                start_date := make_date(year, month, 1);
                end_date := start_date + INTERVAL '1 month';
                partition_name := format('technical_rate_%s_%s_%s',
                                        pair_name,
                                        year,
                                        lpad(month::TEXT, 2, '0'));

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I
                    PARTITION OF bqx.technical_rate_%I
                    FOR VALUES FROM (%L) TO (%L)',
                    partition_name,
                    pair_name,
                    start_date,
                    end_date);

                partition_count := partition_count + 1;

                IF partition_count % 50 = 0 THEN
                    RAISE NOTICE 'Created % partitions...', partition_count;
                END IF;
            END LOOP;
        END LOOP;
    END LOOP;

    RAISE NOTICE '✅ Created % technical_rate partitions', partition_count;
END $$;

-- ============================================================================
-- CREATE PARENT TABLES FOR TECHNICAL_BQX
-- ============================================================================

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
    RAISE NOTICE '=== Creating Technical BQX Parent Tables ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.technical_bqx_%I (
                ts_utc TIMESTAMP NOT NULL,

                -- RSI (Relative Strength Index on BQX momentum)
                rsi_14 NUMERIC,
                rsi_21 NUMERIC,

                -- MACD (Moving Average Convergence Divergence on BQX)
                macd_line NUMERIC,
                macd_signal NUMERIC,
                macd_histogram NUMERIC,

                -- Stochastic Oscillator (on BQX)
                stoch_k NUMERIC,
                stoch_d NUMERIC,

                -- Additional Momentum Indicators (on BQX)
                cci_20 NUMERIC,            -- Commodity Channel Index
                williams_r_14 NUMERIC,      -- Williams %%R
                roc_12 NUMERIC,             -- Rate of Change

                -- Volatility (of BQX momentum)
                atr_14 NUMERIC,             -- Average True Range

                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc)', pair_name);

        RAISE NOTICE 'Created technical_bqx_% parent table', pair_name;
    END LOOP;

    RAISE NOTICE '✅ Created % technical_bqx parent tables', array_length(pairs, 1);
END $$;

-- ============================================================================
-- CREATE PARTITIONS FOR TECHNICAL_BQX (2024-01 through 2024-12)
-- ============================================================================

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
    RAISE NOTICE '=== Creating Technical BQX Partitions ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        FOR year IN 2024..2024
        LOOP
            FOR month IN 1..12
            LOOP
                start_date := make_date(year, month, 1);
                end_date := start_date + INTERVAL '1 month';
                partition_name := format('technical_bqx_%s_%s_%s',
                                        pair_name,
                                        year,
                                        lpad(month::TEXT, 2, '0'));

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I
                    PARTITION OF bqx.technical_bqx_%I
                    FOR VALUES FROM (%L) TO (%L)',
                    partition_name,
                    pair_name,
                    start_date,
                    end_date);

                partition_count := partition_count + 1;

                IF partition_count % 50 = 0 THEN
                    RAISE NOTICE 'Created % partitions...', partition_count;
                END IF;
            END LOOP;
        END LOOP;
    END LOOP;

    RAISE NOTICE '✅ Created % technical_bqx partitions', partition_count;
END $$;

-- ============================================================================
-- CREATE INDEXES
-- ============================================================================

-- Indexes will be created per partition as data is populated
-- (Worker scripts will handle index creation)

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 'technical_rate parent tables' AS description, COUNT(*) AS count
FROM pg_tables
WHERE schemaname = 'bqx' AND tablename LIKE 'technical_rate_%' AND tablename !~ '_[0-9]{4}_[0-9]{2}'

UNION ALL

SELECT 'technical_rate partitions', COUNT(*)
FROM pg_tables
WHERE schemaname = 'bqx' AND tablename LIKE 'technical_rate_%' AND tablename ~ '_[0-9]{4}_[0-9]{2}'

UNION ALL

SELECT 'technical_bqx parent tables', COUNT(*)
FROM pg_tables
WHERE schemaname = 'bqx' AND tablename LIKE 'technical_bqx_%' AND tablename !~ '_[0-9]{4}_[0-9]{2}'

UNION ALL

SELECT 'technical_bqx partitions', COUNT(*)
FROM pg_tables
WHERE schemaname = 'bqx' AND tablename LIKE 'technical_bqx_%' AND tablename ~ '_[0-9]{4}_[0-9]{2}'

ORDER BY description;

-- Expected results:
-- - technical_rate parent tables: 28
-- - technical_rate partitions: 336
-- - technical_bqx parent tables: 28
-- - technical_bqx partitions: 336

COMMIT;

\echo '✅ Phase 1.6.10-1.6.11 Complete: Technical indicator schemas created successfully'
