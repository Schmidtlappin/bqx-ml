-- Stage 1.8.3 Part F: Create ssa_features_bqx - 8 features
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
        EXECUTE format('CREATE TABLE IF NOT EXISTS bqx.ssa_features_bqx_%I (ts_utc TIMESTAMP NOT NULL,
        ssa_trend_component_bqx NUMERIC, ssa_oscillatory_component_bqx NUMERIC, ssa_noise_component_bqx NUMERIC,
        ssa_trend_variance_explained_bqx NUMERIC, ssa_osc_variance_explained_bqx NUMERIC, ssa_noise_variance_bqx NUMERIC,
        ssa_separability_bqx NUMERIC, ssa_reconstruction_error_bqx NUMERIC,
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
            EXECUTE format('CREATE TABLE IF NOT EXISTS bqx.ssa_features_bqx_%s_%s_%s PARTITION OF bqx.ssa_features_bqx_%I
            FOR VALUES FROM (%L) TO (%L)', pair_name, year, lpad(month::TEXT, 2, '0'), pair_name,
            make_date(year, month, 1), make_date(year, month, 1) + INTERVAL '1 month');
            partition_count := partition_count + 1;
        END LOOP; END LOOP;
    END LOOP;
    RAISE NOTICE '✅ Created % ssa_features_bqx partitions', partition_count;
END $$;
COMMIT;
\echo '✅ Stage 1.8.3 Part F Complete: ssa_features_bqx created (8 features, 672 partitions)'
