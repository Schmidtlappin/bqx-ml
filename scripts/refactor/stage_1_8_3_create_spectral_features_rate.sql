-- Stage 1.8.3 Part A: Create spectral_features_rate - 12 features
-- Category: FFT Spectral Features (Frequency Domain Analysis)
-- Mechanism: Fast Fourier Transform on rolling windows
-- Impact: 10-15% improvement in cyclic pattern detection

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
    RAISE NOTICE '=== Creating Spectral Features Rate Parent Tables (12 features) ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.spectral_features_rate_%I (
                ts_utc TIMESTAMP NOT NULL,
                fft_dominant_freq_idx NUMERIC,
                fft_dominant_power_idx NUMERIC,
                fft_secondary_freq_idx NUMERIC,
                fft_harmonic_ratio_idx NUMERIC,
                fft_low_freq_power_idx NUMERIC,
                fft_high_freq_power_idx NUMERIC,
                fft_spectral_entropy_idx NUMERIC,
                fft_spectral_edge_freq_idx NUMERIC,
                fft_power_trend_idx NUMERIC,
                fft_freq_stability_idx NUMERIC,
                fft_noise_ratio_idx NUMERIC,
                fft_cyclic_strength_idx NUMERIC,
                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc)', pair_name);
    END LOOP;
    RAISE NOTICE '✅ Created 28 spectral_features_rate parent tables';
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
                    CREATE TABLE IF NOT EXISTS bqx.spectral_features_rate_%s_%s_%s
                    PARTITION OF bqx.spectral_features_rate_%I
                    FOR VALUES FROM (%L) TO (%L)',
                    pair_name, year, lpad(month::TEXT, 2, '0'), pair_name,
                    make_date(year, month, 1), make_date(year, month, 1) + INTERVAL '1 month');
                partition_count := partition_count + 1;
            END LOOP;
        END LOOP;
    END LOOP;
    RAISE NOTICE '✅ Created % spectral_features_rate partitions', partition_count;
END $$;

COMMIT;
\echo '✅ Stage 1.8.3 Part A Complete: spectral_features_rate created (12 features, 336 partitions)'
