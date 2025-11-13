-- Stage 1.6.18 Part B: Create error_correction_bqx - 12 features
-- Category: FX Structure & Error-Correction Models (HIGH ROI)
-- Mechanism: Johansen cointegration on BQX momentum equilibrium
-- Impact: BQX momentum error correction predicts 30-60% of movements

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
    RAISE NOTICE '=== Creating Error Correction BQX Parent Tables (12 features) ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.error_correction_bqx_%I (
                ts_utc TIMESTAMP NOT NULL,

                -- Cointegration Error Correction Terms (4 features)
                coint_ect_bqx_eurusd_triangle NUMERIC,    -- Momentum equilibrium error (EUR/USD/GBP)
                coint_ect_bqx_audusd_cluster NUMERIC,     -- Momentum cluster error (AUD/NZD/USD)
                coint_ect_bqx_euraud_cross NUMERIC,       -- Momentum cross-rate error
                coint_ect_bqx_usd_majors NUMERIC,         -- USD majors momentum equilibrium

                -- ECT Dynamics (3 features)
                coint_ect_velocity_bqx_20 NUMERIC,        -- Momentum correction speed
                coint_ect_accel_bqx_20 NUMERIC,           -- Momentum correction acceleration
                coint_half_life_bqx NUMERIC,              -- Momentum mean-reversion half-life

                -- Cointegration Vectors (3 features)
                coint_vec_weight_bqx_eur NUMERIC,         -- EUR momentum weight in vector
                coint_vec_weight_bqx_gbp NUMERIC,         -- GBP momentum weight
                coint_vec_weight_bqx_aud NUMERIC,         -- AUD momentum weight

                -- Equilibrium Metrics (2 features)
                coint_deviation_zscore_bqx NUMERIC,       -- Standardized momentum deviation
                coint_regime_inbound_bqx NUMERIC,         -- Binary: momentum moving toward equilibrium

                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc)', pair_name);
    END LOOP;

    RAISE NOTICE '✅ Created 28 error_correction_bqx parent tables (12 features each)';
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
    RAISE NOTICE '=== Creating Error Correction BQX Partitions ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        FOR year IN 2024..2025
        LOOP
            FOR month IN 1..12
            LOOP
                start_date := make_date(year, month, 1);
                end_date := start_date + INTERVAL '1 month';
                partition_name := format('error_correction_bqx_%s_%s_%s',
                                        pair_name, year, lpad(month::TEXT, 2, '0'));

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I
                    PARTITION OF bqx.error_correction_bqx_%I
                    FOR VALUES FROM (%L) TO (%L)',
                    partition_name, pair_name, start_date, end_date);

                partition_count := partition_count + 1;

                IF partition_count % 100 = 0 THEN
                    RAISE NOTICE 'Created % partitions...', partition_count;
                END IF;
            END LOOP;
        END LOOP;
    END LOOP;

    RAISE NOTICE '✅ Created % error_correction_bqx partitions', partition_count;
END $$;

COMMIT;

\echo '✅ Stage 1.6.18 Part B Complete: error_correction_bqx created (12 features, 672 partitions)'
