-- Stage 1.9.1 Part A: Create advanced_microstructure_rate - 20 features
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
        EXECUTE format('CREATE TABLE IF NOT EXISTS bqx.advanced_microstructure_rate_%I (ts_utc TIMESTAMP NOT NULL,
        amihud_illiquidity_idx NUMERIC, kyle_lambda_idx NUMERIC, hasbrouck_info_share_idx NUMERIC,
        effective_spread_idx NUMERIC, realized_spread_idx NUMERIC, price_impact_idx NUMERIC,
        vpin_idx NUMERIC, order_flow_toxicity_idx NUMERIC, trade_clustering_idx NUMERIC,
        volume_imbalance_idx NUMERIC, tick_rule_idx NUMERIC, bid_ask_bounce_idx NUMERIC,
        quoted_spread_stability_idx NUMERIC, depth_weighted_spread_idx NUMERIC,
        price_resilience_idx NUMERIC, market_efficiency_idx NUMERIC, adverse_selection_idx NUMERIC,
        inventory_risk_idx NUMERIC, price_discovery_idx NUMERIC, microstructure_noise_idx NUMERIC,
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
            EXECUTE format('CREATE TABLE IF NOT EXISTS bqx.advanced_microstructure_rate_%s_%s_%s
            PARTITION OF bqx.advanced_microstructure_rate_%I FOR VALUES FROM (%L) TO (%L)',
            pair_name, year, lpad(month::TEXT, 2, '0'), pair_name,
            make_date(year, month, 1), make_date(year, month, 1) + INTERVAL '1 month');
            partition_count := partition_count + 1;
        END LOOP; END LOOP;
    END LOOP;
    RAISE NOTICE '✅ Created % advanced_microstructure_rate partitions', partition_count;
END $$;
COMMIT;
\echo '✅ Stage 1.9.1 Part A Complete: advanced_microstructure_rate created (20 features, 336 partitions)'
