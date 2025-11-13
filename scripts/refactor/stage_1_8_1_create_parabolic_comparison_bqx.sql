-- Stage 1.8.1 Part B: Create parabolic_comparison_bqx - 20 features
-- Category: Parabolic Term Comparisons (Cross-Window BQX Momentum Analysis)
-- Mechanism: Compare BQX regression coefficients across time windows
-- Impact: 10-15% improvement in momentum reversal detection

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
    RAISE NOTICE '=== Creating Parabolic Comparison BQX Parent Tables (20 features) ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.parabolic_comparison_bqx_%I (
                ts_utc TIMESTAMP NOT NULL,

                -- Curvature Ratios (6 features)
                a2_ratio_w15_w60_bqx NUMERIC,           -- Short vs long curvature
                a2_ratio_w30_w75_bqx NUMERIC,           -- Medium vs extended curvature
                a2_ratio_w45_w90_bqx NUMERIC,           -- 45 vs 90 curvature
                a2_consistency_bqx NUMERIC,             -- Std dev of a2 across windows
                a2_trend_slope_bqx NUMERIC,             -- Linear trend of a2
                a2_regime_shift_bqx NUMERIC,            -- Binary: curvature flipping sign

                -- Slope Ratios (6 features)
                a1_ratio_w15_w60_bqx NUMERIC,           -- Short vs long slope
                a1_ratio_w30_w75_bqx NUMERIC,           -- Medium vs extended slope
                a1_ratio_w45_w90_bqx NUMERIC,           -- 45 vs 90 slope
                a1_consistency_bqx NUMERIC,             -- Std dev of a1 across windows
                a1_acceleration_bqx NUMERIC,            -- Rate of slope change
                a1_momentum_bqx NUMERIC,                -- Weighted avg of slopes

                -- Baseline Gaps (4 features)
                b_gap_w15_w45_bqx NUMERIC,              -- Short-medium baseline gap
                b_gap_w30_w60_bqx NUMERIC,              -- Medium-long baseline gap
                b_drift_rate_bqx NUMERIC,               -- Rate of baseline drift
                b_reversion_tendency_bqx NUMERIC,       -- Mean reversion strength

                -- Quality Comparisons (4 features)
                r2_spread_w30_w90_bqx NUMERIC,          -- Predictability divergence
                r2_consistency_bqx NUMERIC,             -- Consistency of fit quality
                rmse_ratio_w15_w60_bqx NUMERIC,         -- Error scaling
                quality_degradation_flag_bqx NUMERIC,   -- Binary: quality declining

                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc)', pair_name);
    END LOOP;

    RAISE NOTICE '✅ Created 28 parabolic_comparison_bqx parent tables (20 features each)';
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
    RAISE NOTICE '=== Creating Parabolic Comparison BQX Partitions ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        FOR year IN 2024..2025
        LOOP
            FOR month IN 1..12
            LOOP
                start_date := make_date(year, month, 1);
                end_date := start_date + INTERVAL '1 month';
                partition_name := format('parabolic_comparison_bqx_%s_%s_%s',
                                        pair_name, year, lpad(month::TEXT, 2, '0'));

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I
                    PARTITION OF bqx.parabolic_comparison_bqx_%I
                    FOR VALUES FROM (%L) TO (%L)',
                    partition_name, pair_name, start_date, end_date);

                partition_count := partition_count + 1;

                IF partition_count % 100 = 0 THEN
                    RAISE NOTICE 'Created % partitions...', partition_count;
                END IF;
            END LOOP;
        END LOOP;
    END LOOP;

    RAISE NOTICE '✅ Created % parabolic_comparison_bqx partitions', partition_count;
END $$;

COMMIT;

\echo '✅ Stage 1.8.1 Part B Complete: parabolic_comparison_bqx created (20 features, 672 partitions)'
