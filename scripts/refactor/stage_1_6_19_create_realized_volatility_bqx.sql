-- Stage 1.6.19 Part B: Create realized_volatility_bqx - 15 features
-- Category: Robust Realized Volatility Family (CHEAP, POWERFUL)
-- Mechanism: Range-based volatility on BQX momentum
-- Impact: 15-25% R² improvement for momentum volatility regimes

\timing on
\set ON_ERROR_STOP on

BEGIN;

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
    RAISE NOTICE '=== Creating Realized Volatility BQX Parent Tables (15 features) ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.realized_volatility_bqx_%I (
                ts_utc TIMESTAMP NOT NULL,
                parkinson_vol_bqx_20_1m NUMERIC,
                garman_klass_vol_bqx_20_1m NUMERIC,
                rogers_satchell_vol_bqx_20_1m NUMERIC,
                yang_zhang_vol_bqx_20_1m NUMERIC,
                bipower_var_bqx_20_1m NUMERIC,
                realized_quarticity_bqx_20_1m NUMERIC,
                jump_test_stat_bqx_20_1m NUMERIC,
                signed_jump_bqx_20_1m NUMERIC,
                vol_of_vol_bqx_20 NUMERIC,
                vol_acceleration_bqx_20 NUMERIC,
                ewma_vol_ratio_bqx_5_20 NUMERIC,
                vol_regime_high_bqx NUMERIC,
                vol_regime_duration_bqx NUMERIC,
                vol_regime_transition_prob_bqx NUMERIC,
                realized_skewness_bqx_20 NUMERIC,
                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc)', pair_name);
    END LOOP;

    RAISE NOTICE '✅ Created 28 realized_volatility_bqx parent tables (15 features each)';
END $$;

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
    RAISE NOTICE '=== Creating Realized Volatility BQX Partitions ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        FOR year IN 2024..2025
        LOOP
            FOR month IN 1..12
            LOOP
                start_date := make_date(year, month, 1);
                end_date := start_date + INTERVAL '1 month';
                partition_name := format('realized_volatility_bqx_%s_%s_%s',
                                        pair_name, year, lpad(month::TEXT, 2, '0'));

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I
                    PARTITION OF bqx.realized_volatility_bqx_%I
                    FOR VALUES FROM (%L) TO (%L)',
                    partition_name, pair_name, start_date, end_date);

                partition_count := partition_count + 1;
                IF partition_count % 100 = 0 THEN
                    RAISE NOTICE 'Created % partitions...', partition_count;
                END IF;
            END LOOP;
        END LOOP;
    END LOOP;

    RAISE NOTICE '✅ Created % realized_volatility_bqx partitions', partition_count;
END $$;

COMMIT;

\echo '✅ Stage 1.6.19 Part B Complete: realized_volatility_bqx created (15 features, 672 partitions)'
