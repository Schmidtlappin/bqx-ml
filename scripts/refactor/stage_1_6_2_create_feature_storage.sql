-- Stage 1.6.2: Create Feature Storage Infrastructure
-- Creates all storage tables for Track 1 (66 unblocked features)
--
-- Total tables to create:
--   - Volume features: 28 parent + 336 partitions
--   - Time features: 28 parent + 336 partitions
--   - Spread features: 28 parent + 336 partitions
--   - Correlation features: 28 parent + 336 partitions
--   - Statistics features: 28 parent + 336 partitions
--   - Bollinger features: 28 parent + 336 partitions
--   - Currency indices: 1 parent + 12 partitions
-- Total: 197 parent + 2,197 partitions = 2,394 tables
--
-- Partitioning: Monthly RANGE partitions (2024-07 to 2025-06, same as M1/BQX/REG)

\timing on

-- ============================================================================
-- 1. VOLUME FEATURES TABLES (28 pairs × 12 partitions = 364 tables)
-- ============================================================================

DO $$
DECLARE
    pair_name TEXT;
    pair_list TEXT[] := ARRAY[
        'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
        'cadchf', 'cadjpy', 'chfjpy',
        'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
        'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
        'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
        'usdcad', 'usdchf', 'usdjpy'
    ];
    year INT;
    month INT;
    partition_name TEXT;
    partition_start TEXT;
    partition_end TEXT;
BEGIN
    RAISE NOTICE 'Creating volume features tables...';

    -- Create parent tables for each pair
    FOREACH pair_name IN ARRAY pair_list
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.volume_features_%I (
                ts_utc TIMESTAMPTZ NOT NULL,
                w15_volume_ratio DOUBLE PRECISION,
                w30_volume_ratio DOUBLE PRECISION,
                w60_volume_ratio DOUBLE PRECISION,
                volume_spike INTEGER,  -- 0 or 1
                volume_trend_slope DOUBLE PRECISION,
                cumulative_volume_60min BIGINT,
                volume_weighted_return DOUBLE PRECISION,
                volume_price_correlation_60min DOUBLE PRECISION,
                relative_volume_position DOUBLE PRECISION,
                volume_volatility_60min DOUBLE PRECISION,
                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc);
        ', pair_name);

        -- Create monthly partitions (2024-07 to 2025-06)
        FOR year IN 2024..2025 LOOP
            FOR month IN 1..12 LOOP
                -- Skip months outside our range
                IF (year = 2024 AND month < 7) OR (year = 2025 AND month > 6) THEN
                    CONTINUE;
                END IF;

                partition_name := format('volume_features_%s_%s_%s',
                    pair_name, year, LPAD(month::TEXT, 2, '0'));
                partition_start := format('%s-%s-01', year, LPAD(month::TEXT, 2, '0'));

                -- Calculate partition end (first day of next month)
                IF month = 12 THEN
                    partition_end := format('%s-01-01', year + 1);
                ELSE
                    partition_end := format('%s-%s-01', year, LPAD((month + 1)::TEXT, 2, '0'));
                END IF;

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I PARTITION OF bqx.volume_features_%I
                    FOR VALUES FROM (%L) TO (%L);
                ', partition_name, pair_name, partition_start, partition_end);
            END LOOP;
        END LOOP;

        RAISE NOTICE 'Created volume_features_% with 12 partitions', pair_name;
    END LOOP;

    RAISE NOTICE 'Volume features tables created: 28 parent + 336 partitions';
END $$;

-- ============================================================================
-- 2. TIME FEATURES TABLES (28 pairs × 12 partitions = 364 tables)
-- ============================================================================

DO $$
DECLARE
    pair_name TEXT;
    pair_list TEXT[] := ARRAY[
        'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
        'cadchf', 'cadjpy', 'chfjpy',
        'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
        'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
        'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
        'usdcad', 'usdchf', 'usdjpy'
    ];
    year INT;
    month INT;
    partition_name TEXT;
    partition_start TEXT;
    partition_end TEXT;
BEGIN
    RAISE NOTICE 'Creating time features tables...';

    FOREACH pair_name IN ARRAY pair_list
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.time_features_%I (
                ts_utc TIMESTAMPTZ NOT NULL,
                hour_sin DOUBLE PRECISION,
                hour_cos DOUBLE PRECISION,
                day_of_week_sin DOUBLE PRECISION,
                day_of_week_cos DOUBLE PRECISION,
                session_overlap INTEGER,  -- 0 or 1
                is_weekend_approach INTEGER,  -- 0 or 1
                minutes_since_market_open INTEGER,
                trading_session INTEGER,  -- 0=Asian, 1=European, 2=US, 3=Overlap
                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc);
        ', pair_name);

        FOR year IN 2024..2025 LOOP
            FOR month IN 1..12 LOOP
                IF (year = 2024 AND month < 7) OR (year = 2025 AND month > 6) THEN
                    CONTINUE;
                END IF;

                partition_name := format('time_features_%s_%s_%s',
                    pair_name, year, LPAD(month::TEXT, 2, '0'));
                partition_start := format('%s-%s-01', year, LPAD(month::TEXT, 2, '0'));

                IF month = 12 THEN
                    partition_end := format('%s-01-01', year + 1);
                ELSE
                    partition_end := format('%s-%s-01', year, LPAD((month + 1)::TEXT, 2, '0'));
                END IF;

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I PARTITION OF bqx.time_features_%I
                    FOR VALUES FROM (%L) TO (%L);
                ', partition_name, pair_name, partition_start, partition_end);
            END LOOP;
        END LOOP;

        RAISE NOTICE 'Created time_features_% with 12 partitions', pair_name;
    END LOOP;

    RAISE NOTICE 'Time features tables created: 28 parent + 336 partitions';
END $$;

-- ============================================================================
-- 3. SPREAD FEATURES TABLES (28 pairs × 12 partitions = 364 tables)
-- ============================================================================

DO $$
DECLARE
    pair_name TEXT;
    pair_list TEXT[] := ARRAY[
        'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
        'cadchf', 'cadjpy', 'chfjpy',
        'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
        'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
        'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
        'usdcad', 'usdchf', 'usdjpy'
    ];
    year INT;
    month INT;
    partition_name TEXT;
    partition_start TEXT;
    partition_end TEXT;
BEGIN
    RAISE NOTICE 'Creating spread features tables...';

    FOREACH pair_name IN ARRAY pair_list
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.spread_features_%I (
                ts_utc TIMESTAMPTZ NOT NULL,
                spread_mean_60min DOUBLE PRECISION,
                spread_volatility_60min DOUBLE PRECISION,
                spread_pct_of_rate DOUBLE PRECISION,
                spread_trend_slope DOUBLE PRECISION,
                spread_spike INTEGER,  -- 0 or 1
                bid_ask_imbalance DOUBLE PRECISION,
                effective_spread DOUBLE PRECISION,
                quoted_spread DOUBLE PRECISION,
                realized_spread DOUBLE PRECISION,
                price_impact DOUBLE PRECISION,
                roll_cost DOUBLE PRECISION,
                bid_depth DOUBLE PRECISION,
                ask_depth DOUBLE PRECISION,
                depth_imbalance DOUBLE PRECISION,
                spread_range_60min DOUBLE PRECISION,
                spread_percentile_60min DOUBLE PRECISION,
                mid_price_volatility DOUBLE PRECISION,
                tick_direction INTEGER,  -- -1, 0, +1
                tick_rule INTEGER,  -- -1, +1
                order_flow_toxicity DOUBLE PRECISION,
                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc);
        ', pair_name);

        FOR year IN 2024..2025 LOOP
            FOR month IN 1..12 LOOP
                IF (year = 2024 AND month < 7) OR (year = 2025 AND month > 6) THEN
                    CONTINUE;
                END IF;

                partition_name := format('spread_features_%s_%s_%s',
                    pair_name, year, LPAD(month::TEXT, 2, '0'));
                partition_start := format('%s-%s-01', year, LPAD(month::TEXT, 2, '0'));

                IF month = 12 THEN
                    partition_end := format('%s-01-01', year + 1);
                ELSE
                    partition_end := format('%s-%s-01', year, LPAD((month + 1)::TEXT, 2, '0'));
                END IF;

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I PARTITION OF bqx.spread_features_%I
                    FOR VALUES FROM (%L) TO (%L);
                ', partition_name, pair_name, partition_start, partition_end);
            END LOOP;
        END LOOP;

        RAISE NOTICE 'Created spread_features_% with 12 partitions', pair_name;
    END LOOP;

    RAISE NOTICE 'Spread features tables created: 28 parent + 336 partitions';
END $$;

-- ============================================================================
-- 4. CORRELATION FEATURES TABLES (28 pairs × 12 partitions = 364 tables)
-- ============================================================================

DO $$
DECLARE
    pair_name TEXT;
    pair_list TEXT[] := ARRAY[
        'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
        'cadchf', 'cadjpy', 'chfjpy',
        'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
        'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
        'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
        'usdcad', 'usdchf', 'usdjpy'
    ];
    year INT;
    month INT;
    partition_name TEXT;
    partition_start TEXT;
    partition_end TEXT;
BEGIN
    RAISE NOTICE 'Creating correlation features tables...';

    FOREACH pair_name IN ARRAY pair_list
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.correlation_features_%I (
                ts_utc TIMESTAMPTZ NOT NULL,
                corr_base_pairs_15min DOUBLE PRECISION,
                corr_base_pairs_60min DOUBLE PRECISION,
                corr_quote_pairs_15min DOUBLE PRECISION,
                corr_quote_pairs_60min DOUBLE PRECISION,
                relative_strength_vs_base_pairs DOUBLE PRECISION,
                relative_strength_vs_quote_pairs DOUBLE PRECISION,
                base_pair_divergence DOUBLE PRECISION,
                quote_pair_divergence DOUBLE PRECISION,
                triangular_arb_divergence DOUBLE PRECISION,
                cross_pair_momentum_divergence INTEGER,  -- -1, 0, +1
                correlation_stability DOUBLE PRECISION,
                lead_lag_indicator DOUBLE PRECISION,
                cointegration_residual DOUBLE PRECISION,
                pair_spread_z_score DOUBLE PRECISION,
                cross_pair_volatility_ratio DOUBLE PRECISION,
                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc);
        ', pair_name);

        FOR year IN 2024..2025 LOOP
            FOR month IN 1..12 LOOP
                IF (year = 2024 AND month < 7) OR (year = 2025 AND month > 6) THEN
                    CONTINUE;
                END IF;

                partition_name := format('correlation_features_%s_%s_%s',
                    pair_name, year, LPAD(month::TEXT, 2, '0'));
                partition_start := format('%s-%s-01', year, LPAD(month::TEXT, 2, '0'));

                IF month = 12 THEN
                    partition_end := format('%s-01-01', year + 1);
                ELSE
                    partition_end := format('%s-%s-01', year, LPAD((month + 1)::TEXT, 2, '0'));
                END IF;

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I PARTITION OF bqx.correlation_features_%I
                    FOR VALUES FROM (%L) TO (%L);
                ', partition_name, pair_name, partition_start, partition_end);
            END LOOP;
        END LOOP;

        RAISE NOTICE 'Created correlation_features_% with 12 partitions', pair_name;
    END LOOP;

    RAISE NOTICE 'Correlation features tables created: 28 parent + 336 partitions';
END $$;

-- ============================================================================
-- 5. STATISTICS FEATURES TABLES (28 pairs × 12 partitions = 364 tables)
-- ============================================================================

DO $$
DECLARE
    pair_name TEXT;
    pair_list TEXT[] := ARRAY[
        'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
        'cadchf', 'cadjpy', 'chfjpy',
        'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
        'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
        'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
        'usdcad', 'usdchf', 'usdjpy'
    ];
    year INT;
    month INT;
    partition_name TEXT;
    partition_start TEXT;
    partition_end TEXT;
BEGIN
    RAISE NOTICE 'Creating statistics features tables...';

    FOREACH pair_name IN ARRAY pair_list
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.statistics_features_%I (
                ts_utc TIMESTAMPTZ NOT NULL,
                skewness_60min DOUBLE PRECISION,
                kurtosis_60min DOUBLE PRECISION,
                median_absolute_deviation_60min DOUBLE PRECISION,
                entropy_60min DOUBLE PRECISION,
                autocorrelation_lag1 DOUBLE PRECISION,
                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc);
        ', pair_name);

        FOR year IN 2024..2025 LOOP
            FOR month IN 1..12 LOOP
                IF (year = 2024 AND month < 7) OR (year = 2025 AND month > 6) THEN
                    CONTINUE;
                END IF;

                partition_name := format('statistics_features_%s_%s_%s',
                    pair_name, year, LPAD(month::TEXT, 2, '0'));
                partition_start := format('%s-%s-01', year, LPAD(month::TEXT, 2, '0'));

                IF month = 12 THEN
                    partition_end := format('%s-01-01', year + 1);
                ELSE
                    partition_end := format('%s-%s-01', year, LPAD((month + 1)::TEXT, 2, '0'));
                END IF;

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I PARTITION OF bqx.statistics_features_%I
                    FOR VALUES FROM (%L) TO (%L);
                ', partition_name, pair_name, partition_start, partition_end);
            END LOOP;
        END LOOP;

        RAISE NOTICE 'Created statistics_features_% with 12 partitions', pair_name;
    END LOOP;

    RAISE NOTICE 'Statistics features tables created: 28 parent + 336 partitions';
END $$;

-- ============================================================================
-- 6. BOLLINGER FEATURES TABLES (28 pairs × 12 partitions = 364 tables)
-- ============================================================================

DO $$
DECLARE
    pair_name TEXT;
    pair_list TEXT[] := ARRAY[
        'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
        'cadchf', 'cadjpy', 'chfjpy',
        'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
        'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
        'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
        'usdcad', 'usdchf', 'usdjpy'
    ];
    year INT;
    month INT;
    partition_name TEXT;
    partition_start TEXT;
    partition_end TEXT;
BEGIN
    RAISE NOTICE 'Creating Bollinger features tables...';

    FOREACH pair_name IN ARRAY pair_list
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.bollinger_features_%I (
                ts_utc TIMESTAMPTZ NOT NULL,
                bollinger_upper_20 DOUBLE PRECISION,
                bollinger_lower_20 DOUBLE PRECISION,
                bollinger_middle_20 DOUBLE PRECISION,
                bollinger_width_20 DOUBLE PRECISION,
                bollinger_percent_b DOUBLE PRECISION,
                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc);
        ', pair_name);

        FOR year IN 2024..2025 LOOP
            FOR month IN 1..12 LOOP
                IF (year = 2024 AND month < 7) OR (year = 2025 AND month > 6) THEN
                    CONTINUE;
                END IF;

                partition_name := format('bollinger_features_%s_%s_%s',
                    pair_name, year, LPAD(month::TEXT, 2, '0'));
                partition_start := format('%s-%s-01', year, LPAD(month::TEXT, 2, '0'));

                IF month = 12 THEN
                    partition_end := format('%s-01-01', year + 1);
                ELSE
                    partition_end := format('%s-%s-01', year, LPAD((month + 1)::TEXT, 2, '0'));
                END IF;

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I PARTITION OF bqx.bollinger_features_%I
                    FOR VALUES FROM (%L) TO (%L);
                ', partition_name, pair_name, partition_start, partition_end);
            END LOOP;
        END LOOP;

        RAISE NOTICE 'Created bollinger_features_% with 12 partitions', pair_name;
    END LOOP;

    RAISE NOTICE 'Bollinger features tables created: 28 parent + 336 partitions';
END $$;

-- ============================================================================
-- 7. CURRENCY INDICES TABLE (1 parent + 12 partitions = 13 tables)
-- ============================================================================

DO $$
DECLARE
    year INT;
    month INT;
    partition_name TEXT;
    partition_start TEXT;
    partition_end TEXT;
BEGIN
    RAISE NOTICE 'Creating currency indices table...';

    -- Create parent table
    CREATE TABLE IF NOT EXISTS bqx.currency_indices (
        ts_utc TIMESTAMPTZ NOT NULL,
        aud_index DOUBLE PRECISION,
        cad_index DOUBLE PRECISION,
        chf_index DOUBLE PRECISION,
        eur_index DOUBLE PRECISION,
        gbp_index DOUBLE PRECISION,
        jpy_index DOUBLE PRECISION,
        nzd_index DOUBLE PRECISION,
        usd_index DOUBLE PRECISION,
        PRIMARY KEY (ts_utc)
    ) PARTITION BY RANGE (ts_utc);

    -- Create monthly partitions
    FOR year IN 2024..2025 LOOP
        FOR month IN 1..12 LOOP
            IF (year = 2024 AND month < 7) OR (year = 2025 AND month > 6) THEN
                CONTINUE;
            END IF;

            partition_name := format('currency_indices_%s_%s',
                year, LPAD(month::TEXT, 2, '0'));
            partition_start := format('%s-%s-01', year, LPAD(month::TEXT, 2, '0'));

            IF month = 12 THEN
                partition_end := format('%s-01-01', year + 1);
            ELSE
                partition_end := format('%s-%s-01', year, LPAD((month + 1)::TEXT, 2, '0'));
            END IF;

            EXECUTE format('
                CREATE TABLE IF NOT EXISTS bqx.%I PARTITION OF bqx.currency_indices
                FOR VALUES FROM (%L) TO (%L);
            ', partition_name, partition_start, partition_end);

            RAISE NOTICE 'Created partition currency_indices_%_%', year, LPAD(month::TEXT, 2, '0');
        END LOOP;
    END LOOP;

    RAISE NOTICE 'Currency indices table created: 1 parent + 12 partitions';
END $$;

-- ============================================================================
-- SUMMARY
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'FEATURE STORAGE INFRASTRUCTURE COMPLETE';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Tables created:';
    RAISE NOTICE '  - Volume features: 28 parent + 336 partitions';
    RAISE NOTICE '  - Time features: 28 parent + 336 partitions';
    RAISE NOTICE '  - Spread features: 28 parent + 336 partitions';
    RAISE NOTICE '  - Correlation features: 28 parent + 336 partitions';
    RAISE NOTICE '  - Statistics features: 28 parent + 336 partitions';
    RAISE NOTICE '  - Bollinger features: 28 parent + 336 partitions';
    RAISE NOTICE '  - Currency indices: 1 parent + 12 partitions';
    RAISE NOTICE '';
    RAISE NOTICE 'Total: 197 parent tables + 2,197 partition tables = 2,394 tables';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Implement Track 1 workers (5 workers for 66 features)';
    RAISE NOTICE '  2. Execute workers in parallel with REG backfill';
    RAISE NOTICE '  3. Estimated completion: 18 hours wall time';
    RAISE NOTICE '';
END $$;

\timing off
