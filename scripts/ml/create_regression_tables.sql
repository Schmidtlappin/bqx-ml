--
-- Track 2: Create Regression Feature Tables
-- Creates reg_rate and reg_bqx tables for all 28 pairs
-- Each table: 90 features (6 windows × 15 metrics)
--

-- Set schema
SET search_path TO bqx, public;

\echo '================================================================================'
\echo 'CREATING REGRESSION FEATURE TABLES (reg_rate, reg_bqx)'
\echo '================================================================================'
\echo ''
\echo 'Tables to create: 1,064 (28 pairs × 2 domains × 19 partitions)'
\echo 'Features per domain: 90 (6 windows × 15 metrics each)'
\echo ''

DO $$
DECLARE
    pair_name TEXT;
    year_month TEXT;
    partition_name TEXT;
    year_val INT;
    month_val INT;
    start_date DATE;
    end_date DATE;
    pair_counter INT := 0;
    total_pairs INT := 28;
BEGIN
    -- Array of all 28 pairs
    FOR pair_name IN
        SELECT unnest(ARRAY[
            'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
            'cadchf', 'cadjpy', 'chfjpy',
            'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
            'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
            'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
            'usdcad', 'usdchf', 'usdjpy'
        ])
    LOOP
        pair_counter := pair_counter + 1;
        RAISE NOTICE '[%/%] Processing pair: %', pair_counter, total_pairs, UPPER(pair_name);

        --
        -- Create reg_rate parent table (RATE domain)
        --
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS bqx.reg_rate_%I (
                ts_utc TIMESTAMP NOT NULL,

                -- Window w15 (15 features)
                a2_idx_w15 NUMERIC,
                a1_idx_w15 NUMERIC,
                b_idx_w15 NUMERIC,
                r2_idx_w15 NUMERIC,
                rmse_idx_w15 NUMERIC,
                residual_mean_idx_w15 NUMERIC,
                residual_std_idx_w15 NUMERIC,
                pred_interval_lower_idx_w15 NUMERIC,
                pred_interval_upper_idx_w15 NUMERIC,
                prediction_idx_w15 NUMERIC,
                vertex_x_idx_w15 NUMERIC,
                vertex_y_idx_w15 NUMERIC,
                curvature_idx_w15 NUMERIC,
                fit_quality_idx_w15 NUMERIC,
                extrapolation_error_idx_w15 NUMERIC,

                -- Window w30 (15 features)
                a2_idx_w30 NUMERIC,
                a1_idx_w30 NUMERIC,
                b_idx_w30 NUMERIC,
                r2_idx_w30 NUMERIC,
                rmse_idx_w30 NUMERIC,
                residual_mean_idx_w30 NUMERIC,
                residual_std_idx_w30 NUMERIC,
                pred_interval_lower_idx_w30 NUMERIC,
                pred_interval_upper_idx_w30 NUMERIC,
                prediction_idx_w30 NUMERIC,
                vertex_x_idx_w30 NUMERIC,
                vertex_y_idx_w30 NUMERIC,
                curvature_idx_w30 NUMERIC,
                fit_quality_idx_w30 NUMERIC,
                extrapolation_error_idx_w30 NUMERIC,

                -- Window w45 (15 features)
                a2_idx_w45 NUMERIC,
                a1_idx_w45 NUMERIC,
                b_idx_w45 NUMERIC,
                r2_idx_w45 NUMERIC,
                rmse_idx_w45 NUMERIC,
                residual_mean_idx_w45 NUMERIC,
                residual_std_idx_w45 NUMERIC,
                pred_interval_lower_idx_w45 NUMERIC,
                pred_interval_upper_idx_w45 NUMERIC,
                prediction_idx_w45 NUMERIC,
                vertex_x_idx_w45 NUMERIC,
                vertex_y_idx_w45 NUMERIC,
                curvature_idx_w45 NUMERIC,
                fit_quality_idx_w45 NUMERIC,
                extrapolation_error_idx_w45 NUMERIC,

                -- Window w60 (15 features)
                a2_idx_w60 NUMERIC,
                a1_idx_w60 NUMERIC,
                b_idx_w60 NUMERIC,
                r2_idx_w60 NUMERIC,
                rmse_idx_w60 NUMERIC,
                residual_mean_idx_w60 NUMERIC,
                residual_std_idx_w60 NUMERIC,
                pred_interval_lower_idx_w60 NUMERIC,
                pred_interval_upper_idx_w60 NUMERIC,
                prediction_idx_w60 NUMERIC,
                vertex_x_idx_w60 NUMERIC,
                vertex_y_idx_w60 NUMERIC,
                curvature_idx_w60 NUMERIC,
                fit_quality_idx_w60 NUMERIC,
                extrapolation_error_idx_w60 NUMERIC,

                -- Window w75 (15 features)
                a2_idx_w75 NUMERIC,
                a1_idx_w75 NUMERIC,
                b_idx_w75 NUMERIC,
                r2_idx_w75 NUMERIC,
                rmse_idx_w75 NUMERIC,
                residual_mean_idx_w75 NUMERIC,
                residual_std_idx_w75 NUMERIC,
                pred_interval_lower_idx_w75 NUMERIC,
                pred_interval_upper_idx_w75 NUMERIC,
                prediction_idx_w75 NUMERIC,
                vertex_x_idx_w75 NUMERIC,
                vertex_y_idx_w75 NUMERIC,
                curvature_idx_w75 NUMERIC,
                fit_quality_idx_w75 NUMERIC,
                extrapolation_error_idx_w75 NUMERIC,

                -- Window agg (aggregate, 15 features)
                a2_idx_agg NUMERIC,
                a1_idx_agg NUMERIC,
                b_idx_agg NUMERIC,
                r2_idx_agg NUMERIC,
                rmse_idx_agg NUMERIC,
                residual_mean_idx_agg NUMERIC,
                residual_std_idx_agg NUMERIC,
                pred_interval_lower_idx_agg NUMERIC,
                pred_interval_upper_idx_agg NUMERIC,
                prediction_idx_agg NUMERIC,
                vertex_x_idx_agg NUMERIC,
                vertex_y_idx_agg NUMERIC,
                curvature_idx_agg NUMERIC,
                fit_quality_idx_agg NUMERIC,
                extrapolation_error_idx_agg NUMERIC,

                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc)',
            pair_name
        );

        -- Create partitions for reg_rate (Jul 2024 - Jun 2025, 12 months)
        FOR year_val IN 2024..2025 LOOP
            FOR month_val IN 1..12 LOOP
                -- Skip months outside our range
                IF (year_val = 2024 AND month_val < 7) OR (year_val = 2025 AND month_val > 6) THEN
                    CONTINUE;
                END IF;

                year_month := year_val || '_' || LPAD(month_val::TEXT, 2, '0');
                partition_name := 'reg_rate_' || pair_name || '_' || year_month;
                start_date := make_date(year_val, month_val, 1);
                end_date := start_date + INTERVAL '1 month';

                EXECUTE format(
                    'CREATE TABLE IF NOT EXISTS bqx.%I PARTITION OF bqx.reg_rate_%I
                     FOR VALUES FROM (%L) TO (%L)',
                    partition_name, pair_name, start_date, end_date
                );
            END LOOP;
        END LOOP;

        --
        -- Create reg_bqx parent table (BQX domain)
        --
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS bqx.reg_bqx_%I (
                ts_utc TIMESTAMP NOT NULL,

                -- Window w15 (15 features)
                a2_bqx_w15 NUMERIC,
                a1_bqx_w15 NUMERIC,
                b_bqx_w15 NUMERIC,
                r2_bqx_w15 NUMERIC,
                rmse_bqx_w15 NUMERIC,
                residual_mean_bqx_w15 NUMERIC,
                residual_std_bqx_w15 NUMERIC,
                pred_interval_lower_bqx_w15 NUMERIC,
                pred_interval_upper_bqx_w15 NUMERIC,
                prediction_bqx_w15 NUMERIC,
                vertex_x_bqx_w15 NUMERIC,
                vertex_y_bqx_w15 NUMERIC,
                curvature_bqx_w15 NUMERIC,
                fit_quality_bqx_w15 NUMERIC,
                extrapolation_error_bqx_w15 NUMERIC,

                -- Window w30 (15 features)
                a2_bqx_w30 NUMERIC,
                a1_bqx_w30 NUMERIC,
                b_bqx_w30 NUMERIC,
                r2_bqx_w30 NUMERIC,
                rmse_bqx_w30 NUMERIC,
                residual_mean_bqx_w30 NUMERIC,
                residual_std_bqx_w30 NUMERIC,
                pred_interval_lower_bqx_w30 NUMERIC,
                pred_interval_upper_bqx_w30 NUMERIC,
                prediction_bqx_w30 NUMERIC,
                vertex_x_bqx_w30 NUMERIC,
                vertex_y_bqx_w30 NUMERIC,
                curvature_bqx_w30 NUMERIC,
                fit_quality_bqx_w30 NUMERIC,
                extrapolation_error_bqx_w30 NUMERIC,

                -- Window w45 (15 features)
                a2_bqx_w45 NUMERIC,
                a1_bqx_w45 NUMERIC,
                b_bqx_w45 NUMERIC,
                r2_bqx_w45 NUMERIC,
                rmse_bqx_w45 NUMERIC,
                residual_mean_bqx_w45 NUMERIC,
                residual_std_bqx_w45 NUMERIC,
                pred_interval_lower_bqx_w45 NUMERIC,
                pred_interval_upper_bqx_w45 NUMERIC,
                prediction_bqx_w45 NUMERIC,
                vertex_x_bqx_w45 NUMERIC,
                vertex_y_bqx_w45 NUMERIC,
                curvature_bqx_w45 NUMERIC,
                fit_quality_bqx_w45 NUMERIC,
                extrapolation_error_bqx_w45 NUMERIC,

                -- Window w60 (15 features)
                a2_bqx_w60 NUMERIC,
                a1_bqx_w60 NUMERIC,
                b_bqx_w60 NUMERIC,
                r2_bqx_w60 NUMERIC,
                rmse_bqx_w60 NUMERIC,
                residual_mean_bqx_w60 NUMERIC,
                residual_std_bqx_w60 NUMERIC,
                pred_interval_lower_bqx_w60 NUMERIC,
                pred_interval_upper_bqx_w60 NUMERIC,
                prediction_bqx_w60 NUMERIC,
                vertex_x_bqx_w60 NUMERIC,
                vertex_y_bqx_w60 NUMERIC,
                curvature_bqx_w60 NUMERIC,
                fit_quality_bqx_w60 NUMERIC,
                extrapolation_error_bqx_w60 NUMERIC,

                -- Window w75 (15 features)
                a2_bqx_w75 NUMERIC,
                a1_bqx_w75 NUMERIC,
                b_bqx_w75 NUMERIC,
                r2_bqx_w75 NUMERIC,
                rmse_bqx_w75 NUMERIC,
                residual_mean_bqx_w75 NUMERIC,
                residual_std_bqx_w75 NUMERIC,
                pred_interval_lower_bqx_w75 NUMERIC,
                pred_interval_upper_bqx_w75 NUMERIC,
                prediction_bqx_w75 NUMERIC,
                vertex_x_bqx_w75 NUMERIC,
                vertex_y_bqx_w75 NUMERIC,
                curvature_bqx_w75 NUMERIC,
                fit_quality_bqx_w75 NUMERIC,
                extrapolation_error_bqx_w75 NUMERIC,

                -- Window agg (aggregate, 15 features)
                a2_bqx_agg NUMERIC,
                a1_bqx_agg NUMERIC,
                b_bqx_agg NUMERIC,
                r2_bqx_agg NUMERIC,
                rmse_bqx_agg NUMERIC,
                residual_mean_bqx_agg NUMERIC,
                residual_std_bqx_agg NUMERIC,
                pred_interval_lower_bqx_agg NUMERIC,
                pred_interval_upper_bqx_agg NUMERIC,
                prediction_bqx_agg NUMERIC,
                vertex_x_bqx_agg NUMERIC,
                vertex_y_bqx_agg NUMERIC,
                curvature_bqx_agg NUMERIC,
                fit_quality_bqx_agg NUMERIC,
                extrapolation_error_bqx_agg NUMERIC,

                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc)',
            pair_name
        );

        -- Create partitions for reg_bqx (Full 2024-2025, 24 months)
        FOR year_val IN 2024..2025 LOOP
            FOR month_val IN 1..12 LOOP
                year_month := year_val || '_' || LPAD(month_val::TEXT, 2, '0');
                partition_name := 'reg_bqx_' || pair_name || '_' || year_month;
                start_date := make_date(year_val, month_val, 1);
                end_date := start_date + INTERVAL '1 month';

                EXECUTE format(
                    'CREATE TABLE IF NOT EXISTS bqx.%I PARTITION OF bqx.reg_bqx_%I
                     FOR VALUES FROM (%L) TO (%L)',
                    partition_name, pair_name, start_date, end_date
                );
            END LOOP;
        END LOOP;

        RAISE NOTICE '  ✅ Created tables for %: reg_rate_% (12 partitions), reg_bqx_% (24 partitions)', UPPER(pair_name), pair_name, pair_name;

    END LOOP;

    RAISE NOTICE '';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'REGRESSION TABLE CREATION COMPLETE';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Tables created: % parent tables', pair_counter * 2;
    RAISE NOTICE 'Partitions created: % (12 rate + 24 bqx per pair)', pair_counter * 36;
    RAISE NOTICE 'Features per table: 90 (6 windows × 15 metrics)';
    RAISE NOTICE '';
    RAISE NOTICE 'Ready for feature population!';
    RAISE NOTICE '================================================================================';

END $$;
