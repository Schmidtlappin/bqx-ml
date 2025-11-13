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
        EXECUTE format('CREATE TABLE IF NOT EXISTS bqx.lagged_cross_window_rate_%I (ts_utc TIMESTAMP NOT NULL,
        momentum_persistence_w15_w60_idx NUMERIC, momentum_transfer_w30_w75_idx NUMERIC,
        momentum_acceleration_w45_w90_idx NUMERIC, momentum_divergence_idx NUMERIC,
        momentum_clustering_idx NUMERIC, vol_transmission_short_long_idx NUMERIC,
        vol_spillover_idx NUMERIC, vol_ratio_cascade_idx NUMERIC, vol_term_structure_change_idx NUMERIC,
        r2_stability_cross_window_idx NUMERIC, prediction_error_propagation_idx NUMERIC,
        curvature_consistency_idx NUMERIC, slope_evolution_idx NUMERIC,
        cross_window_cointegration_idx NUMERIC, temporal_dependency_strength_idx NUMERIC,
        lag_structure_optimal_idx NUMERIC, granger_causality_w15_w60_idx NUMERIC,
        information_flow_idx NUMERIC, predictive_power_decay_idx NUMERIC,
        cross_window_synchrony_idx NUMERIC, temporal_regime_consistency_idx NUMERIC,
        window_dominance_idx NUMERIC, adaptive_window_weight_idx NUMERIC,
        cross_window_shock_transmission_idx NUMERIC, multi_horizon_forecast_consistency_idx NUMERIC,
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
            EXECUTE format('CREATE TABLE IF NOT EXISTS bqx.lagged_cross_window_rate_%s_%s_%s
            PARTITION OF bqx.lagged_cross_window_rate_%I FOR VALUES FROM (%L) TO (%L)',
            pair_name, year, lpad(month::TEXT, 2, '0'), pair_name,
            make_date(year, month, 1), make_date(year, month, 1) + INTERVAL '1 month');
            partition_count := partition_count + 1;
        END LOOP; END LOOP;
    END LOOP;
    RAISE NOTICE '✅ Created % lagged_cross_window_rate partitions', partition_count;
END $$;
COMMIT;
\echo '✅ Stage 1.9.2 Part A Complete: lagged_cross_window_rate created (25 features, 336 partitions)'
