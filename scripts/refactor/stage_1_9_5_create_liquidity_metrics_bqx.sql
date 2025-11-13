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
        EXECUTE format('CREATE TABLE IF NOT EXISTS bqx.liquidity_metrics_bqx_%I (
            ts_utc TIMESTAMP NOT NULL,
            feature_1_bqx NUMERIC, feature_2_bqx NUMERIC, feature_3_bqx NUMERIC,
            feature_4_bqx NUMERIC, feature_5_bqx NUMERIC, feature_6_bqx NUMERIC,
            feature_7_bqx NUMERIC, feature_8_bqx NUMERIC, feature_9_bqx NUMERIC,
            feature_10_bqx NUMERIC, feature_11_bqx NUMERIC,
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
            
            EXECUTE format('CREATE TABLE IF NOT EXISTS bqx.liquidity_metrics_bqx_%s_%s_%s
            PARTITION OF bqx.liquidity_metrics_bqx_%I FOR VALUES FROM (%L) TO (%L)',
            pair_name, year, lpad(month::TEXT, 2, '0'), pair_name,
            make_date(year, month, 1), make_date(year, month, 1) + INTERVAL '1 month');
            partition_count := partition_count + 1;
        END LOOP; END LOOP;
    END LOOP;
    RAISE NOTICE '✅ Created % liquidity_metrics_bqx partitions', partition_count;
END $$;
COMMIT;
\echo '✅ Stage 1_9_5 Complete: liquidity_metrics_bqx created (11 features, 672 partitions)'
