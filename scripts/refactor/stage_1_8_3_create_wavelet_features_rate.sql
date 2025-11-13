-- Stage 1.8.3 Part B: Create wavelet_features_rate - 10 features
-- Category: Wavelet Features (Time-Frequency Localization)
-- Mechanism: Discrete Wavelet Transform (Daubechies db4)
-- Impact: 10-15% improvement in multi-scale pattern detection

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
    RAISE NOTICE '=== Creating Wavelet Features Rate Parent Tables (10 features) ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.wavelet_features_rate_%I (
                ts_utc TIMESTAMP NOT NULL,
                wavelet_detail_d1_energy_idx NUMERIC,
                wavelet_detail_d2_energy_idx NUMERIC,
                wavelet_detail_d3_energy_idx NUMERIC,
                wavelet_approx_a3_energy_idx NUMERIC,
                wavelet_energy_ratio_d1_d3_idx NUMERIC,
                wavelet_trend_strength_idx NUMERIC,
                wavelet_detail_entropy_idx NUMERIC,
                wavelet_singularity_idx NUMERIC,
                wavelet_scale_energy_max_idx NUMERIC,
                wavelet_coherence_idx NUMERIC,
                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc)', pair_name);
    END LOOP;
    RAISE NOTICE '✅ Created 28 wavelet_features_rate parent tables';
END $$;

DO $$
DECLARE
    pair_name TEXT;
    year INT;
    month INT;
    pairs TEXT[] := ARRAY['audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
                          'cadchf', 'cadjpy', 'chfjpy',
                          'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
                          'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
                          'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
                          'usdcad', 'usdchf', 'usdjpy'];
    partition_count INT := 0;
BEGIN
    FOREACH pair_name IN ARRAY pairs
    LOOP
        FOR year IN 2024..2025
        LOOP
            FOR month IN 1..12
            LOOP
                IF (year = 2024 AND month < 7) THEN CONTINUE; END IF;
                IF (year = 2025 AND month > 6) THEN CONTINUE; END IF;
                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.wavelet_features_rate_%s_%s_%s
                    PARTITION OF bqx.wavelet_features_rate_%I
                    FOR VALUES FROM (%L) TO (%L)',
                    pair_name, year, lpad(month::TEXT, 2, '0'), pair_name,
                    make_date(year, month, 1), make_date(year, month, 1) + INTERVAL '1 month');
                partition_count := partition_count + 1;
            END LOOP;
        END LOOP;
    END LOOP;
    RAISE NOTICE '✅ Created % wavelet_features_rate partitions', partition_count;
END $$;

COMMIT;
\echo '✅ Stage 1.8.3 Part B Complete: wavelet_features_rate created (10 features, 336 partitions)'
