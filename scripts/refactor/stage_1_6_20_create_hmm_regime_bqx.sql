-- Stage 1.6.20 Part B: Create hmm_regime_bqx - 15 features
-- Category: Regime & Change-Point Detection (CRITICAL)
-- Mechanism: HMM on BQX momentum regimes
-- Impact: 20-30% error reduction at momentum regime boundaries

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
    RAISE NOTICE '=== Creating HMM Regime BQX Parent Tables (15 features) ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.hmm_regime_bqx_%I (
                ts_utc TIMESTAMP NOT NULL,
                hmm_state_prob_calm_bqx NUMERIC,
                hmm_state_prob_trend_bqx NUMERIC,
                hmm_state_prob_shock_bqx NUMERIC,
                hmm_state_duration_bqx NUMERIC,
                hmm_state_transition_prob_bqx NUMERIC,
                bocpd_run_length_bqx NUMERIC,
                bocpd_hazard_rate_bqx NUMERIC,
                bocpd_growth_prob_bqx NUMERIC,
                bocpd_decay_prob_bqx NUMERIC,
                cusum_momentum_bqx NUMERIC,
                cusum_velocity_bqx NUMERIC,
                cusum_alarm_flag_bqx NUMERIC,
                cusum_reset_periods_bqx NUMERIC,
                regime_entropy_bqx NUMERIC,
                regime_persistence_bqx NUMERIC,
                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc)', pair_name);
    END LOOP;

    RAISE NOTICE '✅ Created 28 hmm_regime_bqx parent tables (15 features each)';
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
    RAISE NOTICE '=== Creating HMM Regime BQX Partitions ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        FOR year IN 2024..2025
        LOOP
            FOR month IN 1..12
            LOOP
                start_date := make_date(year, month, 1);
                end_date := start_date + INTERVAL '1 month';
                partition_name := format('hmm_regime_bqx_%s_%s_%s',
                                        pair_name, year, lpad(month::TEXT, 2, '0'));

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I
                    PARTITION OF bqx.hmm_regime_bqx_%I
                    FOR VALUES FROM (%L) TO (%L)',
                    partition_name, pair_name, start_date, end_date);

                partition_count := partition_count + 1;
                IF partition_count % 100 = 0 THEN
                    RAISE NOTICE 'Created % partitions...', partition_count;
                END IF;
            END LOOP;
        END LOOP;
    END LOOP;

    RAISE NOTICE '✅ Created % hmm_regime_bqx partitions', partition_count;
END $$;

COMMIT;

\echo '✅ Stage 1.6.20 Part B Complete: hmm_regime_bqx created (15 features, 672 partitions)'
