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
        EXECUTE format('CREATE TABLE IF NOT EXISTS bqx.volatility_surface_rate_%I (
            ts_utc TIMESTAMP NOT NULL,
            feature_1_rate NUMERIC, feature_2_rate NUMERIC, feature_3_rate NUMERIC,
            feature_4_rate NUMERIC, feature_5_rate NUMERIC, feature_6_rate NUMERIC,
            feature_7_rate NUMERIC, feature_8_rate NUMERIC, feature_9_rate NUMERIC,
            feature_10_rate NUMERIC, feature_11_rate NUMERIC,
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
            IF (year = 2024 AND month < 7) THEN CONTINUE; END IF;
            IF (year = 2025 AND month > 6) THEN CONTINUE; END IF;
            EXECUTE format('CREATE TABLE IF NOT EXISTS bqx.volatility_surface_rate_%s_%s_%s
            PARTITION OF bqx.volatility_surface_rate_%I FOR VALUES FROM (%L) TO (%L)',
            pair_name, year, lpad(month::TEXT, 2, '0'), pair_name,
            make_date(year, month, 1), make_date(year, month, 1) + INTERVAL '1 month');
            partition_count := partition_count + 1;
        END LOOP; END LOOP;
    END LOOP;
    RAISE NOTICE '✅ Created % volatility_surface_rate partitions', partition_count;
END $$;
COMMIT;
\echo '✅ Stage 1_9_3 Complete: volatility_surface_rate created (15 features, 336 partitions)'
