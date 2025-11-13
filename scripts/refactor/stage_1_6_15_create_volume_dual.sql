-- Stage 1.6.15: Create Volume Dual Architecture (35 rate + 35 bqx = 70 features, 1,344 partitions)
-- Action: CREATE TABLE (both volume_rate and volume_bqx are NEW)
-- Tables: 672 volume_rate partitions + 672 volume_bqx partitions = 1,344 total

\timing on
\set ON_ERROR_STOP on

BEGIN;

-- ============================================================================
-- PART A: Create volume_rate (IDX domain, 35 features)
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
    RAISE NOTICE '=== Creating Volume Rate (IDX) Parent Tables (35 features) ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.volume_rate_%I (
                ts_utc TIMESTAMP NOT NULL,

                -- Volume-weighted Rate (5 features)
                vwap_5min NUMERIC,
                vwap_15min NUMERIC,
                vwap_30min NUMERIC,
                vwap_60min NUMERIC,
                vwap_120min NUMERIC,

                -- Rate-Volume Correlation (3 features)
                rate_vol_corr_15min NUMERIC,
                rate_vol_corr_30min NUMERIC,
                rate_vol_corr_60min NUMERIC,

                -- Volume Momentum Divergence (4 features)
                vol_momentum_div_5min NUMERIC,
                vol_momentum_div_15min NUMERIC,
                vol_momentum_div_30min NUMERIC,
                vol_momentum_div_60min NUMERIC,

                -- Up/Down-tick Ratios (8 features)
                uptick_ratio_5min NUMERIC,
                uptick_ratio_15min NUMERIC,
                uptick_ratio_30min NUMERIC,
                uptick_ratio_60min NUMERIC,
                downtick_ratio_5min NUMERIC,
                downtick_ratio_15min NUMERIC,
                downtick_ratio_30min NUMERIC,
                downtick_ratio_60min NUMERIC,

                -- Volume × Volatility (3 features)
                vol_volatility_15min NUMERIC,
                vol_volatility_30min NUMERIC,
                vol_volatility_60min NUMERIC,

                -- Volume Trend (3 features)
                vol_trend_15min NUMERIC,
                vol_trend_30min NUMERIC,
                vol_trend_60min NUMERIC,

                -- Spike Detection (3 features)
                vol_spike_15min NUMERIC,
                vol_spike_30min NUMERIC,
                vol_spike_60min NUMERIC,

                -- Cumulative Delta (3 features)
                cumulative_delta_15min NUMERIC,
                cumulative_delta_30min NUMERIC,
                cumulative_delta_60min NUMERIC,

                -- Volume Imbalance (3 features)
                vol_imbalance_15min NUMERIC,
                vol_imbalance_30min NUMERIC,
                vol_imbalance_60min NUMERIC,

                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc)', pair_name);
    END LOOP;

    RAISE NOTICE '✅ Created 28 volume_rate parent tables (35 features each)';
END $$;

-- Create volume_rate Partitions (28 pairs × 24 months = 672 partitions)
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
    RAISE NOTICE '=== Creating Volume Rate Partitions ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        FOR year IN 2024..2025
        LOOP
            FOR month IN 1..12
            LOOP
                start_date := make_date(year, month, 1);
                end_date := start_date + INTERVAL '1 month';
                partition_name := format('volume_rate_%s_%s_%s',
                                        pair_name, year, lpad(month::TEXT, 2, '0'));

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I
                    PARTITION OF bqx.volume_rate_%I
                    FOR VALUES FROM (%L) TO (%L)',
                    partition_name, pair_name, start_date, end_date);

                partition_count := partition_count + 1;

                IF partition_count % 100 = 0 THEN
                    RAISE NOTICE 'Created % volume_rate partitions...', partition_count;
                END IF;
            END LOOP;
        END LOOP;
    END LOOP;

    RAISE NOTICE '✅ Created % volume_rate partitions', partition_count;
END $$;

-- ============================================================================
-- PART B: Create volume_bqx (BQX domain, 35 features)
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
    RAISE NOTICE '=== Creating Volume BQX Parent Tables (35 features) ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.volume_bqx_%I (
                ts_utc TIMESTAMP NOT NULL,

                -- Volume-weighted BQX (5 features)
                vw_bqx_5min NUMERIC,
                vw_bqx_15min NUMERIC,
                vw_bqx_30min NUMERIC,
                vw_bqx_60min NUMERIC,
                vw_bqx_120min NUMERIC,

                -- BQX-Volume Correlation (3 features)
                bqx_vol_corr_15min NUMERIC,
                bqx_vol_corr_30min NUMERIC,
                bqx_vol_corr_60min NUMERIC,

                -- Volume Momentum Divergence (4 features)
                vol_momentum_div_5min NUMERIC,
                vol_momentum_div_15min NUMERIC,
                vol_momentum_div_30min NUMERIC,
                vol_momentum_div_60min NUMERIC,

                -- Up/Down-tick Ratios (8 features)
                uptick_ratio_5min NUMERIC,
                uptick_ratio_15min NUMERIC,
                uptick_ratio_30min NUMERIC,
                uptick_ratio_60min NUMERIC,
                downtick_ratio_5min NUMERIC,
                downtick_ratio_15min NUMERIC,
                downtick_ratio_30min NUMERIC,
                downtick_ratio_60min NUMERIC,

                -- Volume × Volatility (3 features)
                vol_volatility_15min NUMERIC,
                vol_volatility_30min NUMERIC,
                vol_volatility_60min NUMERIC,

                -- Volume Trend (3 features)
                vol_trend_15min NUMERIC,
                vol_trend_30min NUMERIC,
                vol_trend_60min NUMERIC,

                -- Spike Detection (3 features)
                vol_spike_15min NUMERIC,
                vol_spike_30min NUMERIC,
                vol_spike_60min NUMERIC,

                -- Cumulative Delta (3 features)
                cumulative_delta_15min NUMERIC,
                cumulative_delta_30min NUMERIC,
                cumulative_delta_60min NUMERIC,

                -- Volume Imbalance (3 features)
                vol_imbalance_15min NUMERIC,
                vol_imbalance_30min NUMERIC,
                vol_imbalance_60min NUMERIC,

                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc)', pair_name);
    END LOOP;

    RAISE NOTICE '✅ Created 28 volume_bqx parent tables (35 features each)';
END $$;

-- Create volume_bqx Partitions (28 pairs × 24 months = 672 partitions)
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
    RAISE NOTICE '=== Creating Volume BQX Partitions ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        FOR year IN 2024..2025
        LOOP
            FOR month IN 1..12
            LOOP
                start_date := make_date(year, month, 1);
                end_date := start_date + INTERVAL '1 month';
                partition_name := format('volume_bqx_%s_%s_%s',
                                        pair_name, year, lpad(month::TEXT, 2, '0'));

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I
                    PARTITION OF bqx.volume_bqx_%I
                    FOR VALUES FROM (%L) TO (%L)',
                    partition_name, pair_name, start_date, end_date);

                partition_count := partition_count + 1;

                IF partition_count % 100 = 0 THEN
                    RAISE NOTICE 'Created % volume_bqx partitions...', partition_count;
                END IF;
            END LOOP;
        END LOOP;
    END LOOP;

    RAISE NOTICE '✅ Created % volume_bqx partitions', partition_count;
END $$;

COMMIT;

\echo '✅ Stage 1.6.15 Complete: Volume Dual Architecture created (70 features, 1,344 partitions)'
