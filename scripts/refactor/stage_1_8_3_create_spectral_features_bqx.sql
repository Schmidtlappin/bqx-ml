-- Stage 1.8.3 Part D: Create spectral_features_bqx - 12 features
\timing on
\set ON_ERROR_STOP on
BEGIN;
DO $$
DECLARE pair_name TEXT; pairs TEXT[] := ARRAY['audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
'cadchf', 'cadjpy', 'chfjpy', 'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd', 'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
'usdcad', 'usdchf', 'usdjpy'];
BEGIN
    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('CREATE TABLE IF NOT EXISTS bqx.spectral_features_bqx_%I (ts_utc TIMESTAMP NOT NULL,
        fft_dominant_freq_bqx NUMERIC, fft_dominant_power_bqx NUMERIC, fft_secondary_freq_bqx NUMERIC,
        fft_harmonic_ratio_bqx NUMERIC, fft_low_freq_power_bqx NUMERIC, fft_high_freq_power_bqx NUMERIC,
        fft_spectral_entropy_bqx NUMERIC, fft_spectral_edge_freq_bqx NUMERIC, fft_power_trend_bqx NUMERIC,
        fft_freq_stability_bqx NUMERIC, fft_noise_ratio_bqx NUMERIC, fft_cyclic_strength_bqx NUMERIC,
        PRIMARY KEY (ts_utc)) PARTITION BY RANGE (ts_utc)', pair_name);
    END LOOP;
END $$;
DO $$
DECLARE pair_name TEXT; year INT; month INT; pairs TEXT[] := ARRAY['audcad', 'audchf', 'audjpy', 'audnzd',
'audusd', 'cadchf', 'cadjpy', 'chfjpy', 'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd',
'eurusd', 'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd', 'nzdcad', 'nzdchf', 'nzdjpy',
'nzdusd', 'usdcad', 'usdchf', 'usdjpy']; partition_count INT := 0;
BEGIN
    FOREACH pair_name IN ARRAY pairs
    LOOP
        FOR year IN 2024..2025 LOOP FOR month IN 1..12 LOOP
            EXECUTE format('CREATE TABLE IF NOT EXISTS bqx.spectral_features_bqx_%s_%s_%s PARTITION OF bqx.spectral_features_bqx_%I
            FOR VALUES FROM (%L) TO (%L)', pair_name, year, lpad(month::TEXT, 2, '0'), pair_name,
            make_date(year, month, 1), make_date(year, month, 1) + INTERVAL '1 month');
            partition_count := partition_count + 1;
        END LOOP; END LOOP;
    END LOOP;
    RAISE NOTICE '✅ Created % spectral_features_bqx partitions', partition_count;
END $$;
COMMIT;
\echo '✅ Stage 1.8.3 Part D Complete: spectral_features_bqx created (12 features, 672 partitions)'
