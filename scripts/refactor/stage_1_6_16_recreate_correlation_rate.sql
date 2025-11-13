-- Stage 1.6.16: Recreate correlation_rate (IDX) with expanded schema (16→45 features, 336 partitions)
-- Action: DROP existing empty tables, CREATE with expanded schema
-- Current State: 336 partitions with 0 rows (safe to drop)
-- Target: 45 comprehensive correlation features

\timing on
\set ON_ERROR_STOP on

BEGIN;

-- ============================================================================
-- STEP 1: Drop existing correlation_rate tables (currently empty)
-- ============================================================================

DO $$
DECLARE
    table_name TEXT;
    drop_count INT := 0;
BEGIN
    RAISE NOTICE '=== Dropping Existing Empty correlation_rate Tables ===';

    -- Drop all partitions first
    FOR table_name IN
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'bqx'
        AND tablename LIKE 'correlation_rate_%'
        AND tablename ~ '_[0-9]{4}_[0-9]{2}$'
        ORDER BY tablename
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS bqx.%I CASCADE', table_name);
        drop_count := drop_count + 1;

        IF drop_count % 50 = 0 THEN
            RAISE NOTICE 'Dropped % partitions...', drop_count;
        END IF;
    END LOOP;

    RAISE NOTICE '✅ Dropped % empty correlation_rate partitions', drop_count;

    -- Drop parent tables
    FOR table_name IN
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'bqx'
        AND tablename LIKE 'correlation_rate_%'
        AND tablename !~ '_[0-9]{4}_[0-9]{2}$'
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS bqx.%I CASCADE', table_name);
    END LOOP;

    RAISE NOTICE '✅ Dropped correlation_rate parent tables';
END $$;

-- ============================================================================
-- STEP 2: Create correlation_rate with expanded 45-feature schema
-- ============================================================================

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
    RAISE NOTICE '=== Creating Correlation Rate Parent Tables (45 features) ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.correlation_rate_%I (
                ts_utc TIMESTAMP NOT NULL,

                -- Base/Quote Pair Correlations (12 features)
                corr_base_pairs_15min NUMERIC,
                corr_base_pairs_30min NUMERIC,
                corr_base_pairs_60min NUMERIC,
                corr_base_pairs_120min NUMERIC,
                corr_quote_pairs_15min NUMERIC,
                corr_quote_pairs_30min NUMERIC,
                corr_quote_pairs_60min NUMERIC,
                corr_quote_pairs_120min NUMERIC,
                corr_cross_pairs_15min NUMERIC,
                corr_cross_pairs_30min NUMERIC,
                corr_cross_pairs_60min NUMERIC,
                corr_cross_pairs_120min NUMERIC,

                -- Correlation Changes (6 features)
                corr_change_5min NUMERIC,
                corr_change_15min NUMERIC,
                corr_change_30min NUMERIC,
                corr_change_60min NUMERIC,
                corr_change_120min NUMERIC,
                corr_change_240min NUMERIC,

                -- Z-scores (6 features)
                corr_zscore_base_15min NUMERIC,
                corr_zscore_base_60min NUMERIC,
                corr_zscore_quote_15min NUMERIC,
                corr_zscore_quote_60min NUMERIC,
                corr_zscore_cross_15min NUMERIC,
                corr_zscore_cross_60min NUMERIC,

                -- Relative Strength (2 features)
                rel_strength_base NUMERIC,
                rel_strength_quote NUMERIC,

                -- Divergence Metrics (4 features)
                divergence_base_15min NUMERIC,
                divergence_base_60min NUMERIC,
                divergence_quote_15min NUMERIC,
                divergence_quote_60min NUMERIC,

                -- Correlation Stability (3 features)
                corr_stability_15min NUMERIC,
                corr_stability_60min NUMERIC,
                corr_stability_240min NUMERIC,

                -- Lead-Lag (3 features)
                lead_lag_base NUMERIC,
                lead_lag_quote NUMERIC,
                lead_lag_cross NUMERIC,

                -- Cointegration (3 features)
                cointegration_base NUMERIC,
                cointegration_quote NUMERIC,
                cointegration_cross NUMERIC,

                -- Pair Spread (3 features)
                pair_spread_15min NUMERIC,
                pair_spread_60min NUMERIC,
                pair_spread_240min NUMERIC,

                -- Volatility Ratios (3 features)
                vol_ratio_base NUMERIC,
                vol_ratio_quote NUMERIC,
                vol_ratio_cross NUMERIC,

                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc)', pair_name);
    END LOOP;

    RAISE NOTICE '✅ Created 28 correlation_rate parent tables (45 features each)';
END $$;

-- Create Partitions (28 pairs × 12 months (2024-07 to 2025-06) = 336 partitions)
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
    RAISE NOTICE '=== Creating Correlation Rate Partitions ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        FOR year IN 2024..2025
        LOOP
            FOR month IN 1..12
            LOOP
                start_date := make_date(year, month, 1);
                end_date := start_date + INTERVAL '1 month';
                partition_name := format('correlation_rate_%s_%s_%s',
                                        pair_name, year, lpad(month::TEXT, 2, '0'));

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I
                    PARTITION OF bqx.correlation_rate_%I
                    FOR VALUES FROM (%L) TO (%L)',
                    partition_name, pair_name, start_date, end_date);

                partition_count := partition_count + 1;

                IF partition_count % 100 = 0 THEN
                    RAISE NOTICE 'Created % partitions...', partition_count;
                END IF;
            END LOOP;
        END LOOP;
    END LOOP;

    RAISE NOTICE '✅ Created % correlation_rate partitions', partition_count;
END $$;

COMMIT;

\echo '✅ Stage 1.6.16 Complete: correlation_rate recreated (45 features, 672 partitions)'
