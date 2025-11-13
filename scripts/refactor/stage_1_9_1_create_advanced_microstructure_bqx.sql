-- Stage 1.9.1 Part B: Create advanced_microstructure_bqx - 20 features
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
        EXECUTE format('CREATE TABLE IF NOT EXISTS bqx.advanced_microstructure_bqx_%I (ts_utc TIMESTAMP NOT NULL,
        amihud_illiquidity_bqx NUMERIC, kyle_lambda_bqx NUMERIC, hasbrouck_info_share_bqx NUMERIC,
        effective_spread_bqx NUMERIC, realized_spread_bqx NUMERIC, price_impact_bqx NUMERIC,
        vpin_bqx NUMERIC, order_flow_toxicity_bqx NUMERIC, trade_clustering_bqx NUMERIC,
        volume_imbalance_bqx NUMERIC, tick_rule_bqx NUMERIC, bid_ask_bounce_bqx NUMERIC,
        quoted_spread_stability_bqx NUMERIC, depth_weighted_spread_bqx NUMERIC,
        price_resilience_bqx NUMERIC, market_efficiency_bqx NUMERIC, adverse_selection_bqx NUMERIC,
        inventory_risk_bqx NUMERIC, price_discovery_bqx NUMERIC, microstructure_noise_bqx NUMERIC,
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
            EXECUTE format('CREATE TABLE IF NOT EXISTS bqx.advanced_microstructure_bqx_%s_%s_%s
            PARTITION OF bqx.advanced_microstructure_bqx_%I FOR VALUES FROM (%L) TO (%L)',
            pair_name, year, lpad(month::TEXT, 2, '0'), pair_name,
            make_date(year, month, 1), make_date(year, month, 1) + INTERVAL '1 month');
            partition_count := partition_count + 1;
        END LOOP; END LOOP;
    END LOOP;
    RAISE NOTICE '✅ Created % advanced_microstructure_bqx partitions', partition_count;
END $$;
COMMIT;
\echo '✅ Stage 1.9.1 Part B Complete: advanced_microstructure_bqx created (20 features, 672 partitions)'
