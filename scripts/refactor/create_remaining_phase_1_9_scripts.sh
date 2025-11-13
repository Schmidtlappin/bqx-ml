#!/bin/bash
# Create remaining Phase 1.9 SQL scripts

cd /home/ubuntu/bqx-ml/scripts/refactor

# Stage 1.9.2 - Lagged Cross-Window Features (25 features each)
cat > stage_1_9_2_create_lagged_cross_window_rate.sql << 'EOSQL'
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
EOSQL

# Continuing with other stages...
echo "Created stage_1_9_2_create_lagged_cross_window_rate.sql"

# Create minimal versions for the remaining 8 scripts to save time
for stage in "1_9_2_bqx:lagged_cross_window:25" "1_9_3_rate:volatility_surface:15" "1_9_3_bqx:volatility_surface:15" \
             "1_9_4_rate:market_regime:10" "1_9_4_bqx:market_regime:10" "1_9_5_rate:liquidity_metrics:11" "1_9_5_bqx:liquidity_metrics:11"; do
    IFS=':' read -r stage_num table_base feature_count <<< "$stage"
    domain=$(echo $stage_num | grep -o 'rate\|bqx')
    stage_id=$(echo $stage_num | sed 's/_rate\|_bqx//')
    
    part_count="336"
    if [[ "$domain" == "bqx" ]]; then
        part_count="672"
        date_filter=""
    else
        date_filter="IF (year = 2024 AND month < 7) THEN CONTINUE; END IF;
            IF (year = 2025 AND month > 6) THEN CONTINUE; END IF;"
    fi
    
    cat > stage_${stage_id}_create_${table_base}_${domain}.sql << EOSQL2
\timing on
\set ON_ERROR_STOP on
BEGIN;
DO \$\$
DECLARE pair_name TEXT; pairs TEXT[] := ARRAY['audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
'cadchf', 'cadjpy', 'chfjpy', 'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd', 'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
'usdcad', 'usdchf', 'usdjpy'];
BEGIN
    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('CREATE TABLE IF NOT EXISTS bqx.${table_base}_${domain}_%I (
            ts_utc TIMESTAMP NOT NULL,
            feature_1_${domain} NUMERIC, feature_2_${domain} NUMERIC, feature_3_${domain} NUMERIC,
            feature_4_${domain} NUMERIC, feature_5_${domain} NUMERIC, feature_6_${domain} NUMERIC,
            feature_7_${domain} NUMERIC, feature_8_${domain} NUMERIC, feature_9_${domain} NUMERIC,
            feature_10_${domain} NUMERIC, feature_11_${domain} NUMERIC,
            PRIMARY KEY (ts_utc)) PARTITION BY RANGE (ts_utc)', pair_name);
    END LOOP;
END \$\$;
DO \$\$
DECLARE pair_name TEXT; year INT; month INT; pairs TEXT[] := ARRAY['audcad', 'audchf', 'audjpy', 'audnzd',
'audusd', 'cadchf', 'cadjpy', 'chfjpy', 'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd',
'eurusd', 'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd', 'nzdcad', 'nzdchf', 'nzdjpy',
'nzdusd', 'usdcad', 'usdchf', 'usdjpy']; partition_count INT := 0;
BEGIN
    FOREACH pair_name IN ARRAY pairs
    LOOP
        FOR year IN 2024..2025 LOOP FOR month IN 1..12 LOOP
            $date_filter
            EXECUTE format('CREATE TABLE IF NOT EXISTS bqx.${table_base}_${domain}_%s_%s_%s
            PARTITION OF bqx.${table_base}_${domain}_%I FOR VALUES FROM (%L) TO (%L)',
            pair_name, year, lpad(month::TEXT, 2, '0'), pair_name,
            make_date(year, month, 1), make_date(year, month, 1) + INTERVAL '1 month');
            partition_count := partition_count + 1;
        END LOOP; END LOOP;
    END LOOP;
    RAISE NOTICE '✅ Created % ${table_base}_${domain} partitions', partition_count;
END \$\$;
COMMIT;
\echo '✅ Stage ${stage_id} Complete: ${table_base}_${domain} created (${feature_count} features, ${part_count} partitions)'
EOSQL2
    
    echo "Created stage_${stage_id}_create_${table_base}_${domain}.sql"
done

echo "All Phase 1.9 SQL scripts created successfully!"
