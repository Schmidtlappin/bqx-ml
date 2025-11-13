-- Stage 1.8.3 Part E: Create wavelet_features_bqx - 10 features
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
        EXECUTE format('CREATE TABLE IF NOT EXISTS bqx.wavelet_features_bqx_%I (ts_utc TIMESTAMP NOT NULL,
        wavelet_detail_d1_energy_bqx NUMERIC, wavelet_detail_d2_energy_bqx NUMERIC, wavelet_detail_d3_energy_bqx NUMERIC,
        wavelet_approx_a3_energy_bqx NUMERIC, wavelet_energy_ratio_d1_d3_bqx NUMERIC, wavelet_trend_strength_bqx NUMERIC,
        wavelet_detail_entropy_bqx NUMERIC, wavelet_singularity_bqx NUMERIC, wavelet_scale_energy_max_bqx NUMERIC,
        wavelet_coherence_bqx NUMERIC, PRIMARY KEY (ts_utc)) PARTITION BY RANGE (ts_utc)', pair_name);
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
            EXECUTE format('CREATE TABLE IF NOT EXISTS bqx.wavelet_features_bqx_%s_%s_%s PARTITION OF bqx.wavelet_features_bqx_%I
            FOR VALUES FROM (%L) TO (%L)', pair_name, year, lpad(month::TEXT, 2, '0'), pair_name,
            make_date(year, month, 1), make_date(year, month, 1) + INTERVAL '1 month');
            partition_count := partition_count + 1;
        END LOOP; END LOOP;
    END LOOP;
    RAISE NOTICE '✅ Created % wavelet_features_bqx partitions', partition_count;
END $$;
COMMIT;
\echo '✅ Stage 1.8.3 Part E Complete: wavelet_features_bqx created (10 features, 672 partitions)'
