-- Stage 1.6.18 Part A: Create error_correction_rate (IDX) - 12 features
-- Category: FX Structure & Error-Correction Models (HIGH ROI)
-- Mechanism: Johansen cointegration captures mean-reversion equilibrium relationships
-- Impact: ECT predicts 30-60% of 45-75 minute movements

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
    RAISE NOTICE '=== Creating Error Correction Rate (IDX) Parent Tables (12 features) ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.error_correction_rate_%I (
                ts_utc TIMESTAMP NOT NULL,

                -- Cointegration Error Correction Terms (4 features)
                coint_ect_idx_eurusd_triangle NUMERIC,    -- EUR/USD/GBP triangle equilibrium error
                coint_ect_idx_audusd_cluster NUMERIC,     -- AUD/NZD/USD cluster error
                coint_ect_idx_euraud_cross NUMERIC,       -- EUR/AUD cross-rate error
                coint_ect_idx_usd_majors NUMERIC,         -- USD major pairs equilibrium

                -- ECT Dynamics (3 features)
                coint_ect_velocity_idx_20 NUMERIC,        -- ΔECT speed of correction
                coint_ect_accel_idx_20 NUMERIC,           -- Δ²ECT acceleration
                coint_half_life_idx NUMERIC,              -- Mean-reversion half-life

                -- Cointegration Vectors (3 features)
                coint_vec_weight_idx_eur NUMERIC,         -- EUR weight in cointegration vector
                coint_vec_weight_idx_gbp NUMERIC,         -- GBP weight in vector
                coint_vec_weight_idx_aud NUMERIC,         -- AUD weight in vector

                -- Equilibrium Metrics (2 features)
                coint_deviation_zscore_idx NUMERIC,       -- Standardized deviation from equilibrium
                coint_regime_inbound_idx NUMERIC,         -- Binary: moving toward equilibrium

                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc)', pair_name);
    END LOOP;

    RAISE NOTICE '✅ Created 28 error_correction_rate parent tables (12 features each)';
END $$;

-- Create Partitions (28 pairs × 24 months = 672 partitions, but using 336 for existing data range)
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
    RAISE NOTICE '=== Creating Error Correction Rate Partitions ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        -- 2024-07 to 2025-06 (12 months, matching existing data range)
        FOR year IN 2024..2025
        LOOP
            FOR month IN 1..12
            LOOP
                -- Skip months before July 2024
                IF (year = 2024 AND month < 7) THEN
                    CONTINUE;
                END IF;
                -- Skip months after June 2025
                IF (year = 2025 AND month > 6) THEN
                    CONTINUE;
                END IF;

                start_date := make_date(year, month, 1);
                end_date := start_date + INTERVAL '1 month';
                partition_name := format('error_correction_rate_%s_%s_%s',
                                        pair_name, year, lpad(month::TEXT, 2, '0'));

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I
                    PARTITION OF bqx.error_correction_rate_%I
                    FOR VALUES FROM (%L) TO (%L)',
                    partition_name, pair_name, start_date, end_date);

                partition_count := partition_count + 1;

                IF partition_count % 100 = 0 THEN
                    RAISE NOTICE 'Created % partitions...', partition_count;
                END IF;
            END LOOP;
        END LOOP;
    END LOOP;

    RAISE NOTICE '✅ Created % error_correction_rate partitions', partition_count;
END $$;

COMMIT;

\echo '✅ Stage 1.6.18 Part A Complete: error_correction_rate created (12 features, 336 partitions)'
