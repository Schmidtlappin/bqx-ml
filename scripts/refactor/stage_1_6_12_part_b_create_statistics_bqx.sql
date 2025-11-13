-- Stage 1.6.12 Part B: Create statistics_bqx (48 features, 672 partitions)
-- Action: CREATE TABLE (new BQX domain tables)
-- Schema: Identical to expanded statistics_rate

\timing on
\set ON_ERROR_STOP on

BEGIN;

-- Create Parent Tables (28 pairs)
DO $$
DECLARE
    pair_name TEXT;
    pairs TEXT[] := ARRAY['audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
                          'cadchf', 'cadjpy', 'chfjpy',
                          'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
                          'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
                          'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
                          'usdcad', 'usdchf', 'usdjpy'];
BEGIN
    RAISE NOTICE '=== Creating Statistics BQX Parent Tables (48 features) ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.statistics_bqx_%I (
                ts_utc TIMESTAMP NOT NULL,

                -- Mean (5 features)
                mean_5min NUMERIC,
                mean_15min NUMERIC,
                mean_30min NUMERIC,
                mean_60min NUMERIC,
                mean_120min NUMERIC,

                -- Std Deviation (5 features)
                std_5min NUMERIC,
                std_15min NUMERIC,
                std_30min NUMERIC,
                std_60min NUMERIC,
                std_120min NUMERIC,

                -- Skewness (5 features)
                skew_5min NUMERIC,
                skew_15min NUMERIC,
                skew_30min NUMERIC,
                skew_60min NUMERIC,
                skew_120min NUMERIC,

                -- Kurtosis (5 features)
                kurt_5min NUMERIC,
                kurt_15min NUMERIC,
                kurt_30min NUMERIC,
                kurt_60min NUMERIC,
                kurt_120min NUMERIC,

                -- Percentiles (10 features)
                p5_15min NUMERIC,
                p10_15min NUMERIC,
                p25_15min NUMERIC,
                p50_15min NUMERIC,
                p75_15min NUMERIC,
                p90_15min NUMERIC,
                p95_15min NUMERIC,
                p50_60min NUMERIC,
                p75_60min NUMERIC,
                p90_60min NUMERIC,

                -- Range (3 features)
                range_15min NUMERIC,
                range_30min NUMERIC,
                range_60min NUMERIC,

                -- IQR (3 features)
                iqr_15min NUMERIC,
                iqr_30min NUMERIC,
                iqr_60min NUMERIC,

                -- MAD (3 features)
                mad_15min NUMERIC,
                mad_30min NUMERIC,
                mad_60min NUMERIC,

                -- Coefficient of Variation (3 features)
                cv_15min NUMERIC,
                cv_30min NUMERIC,
                cv_60min NUMERIC,

                -- Entropy (3 features)
                entropy_15min NUMERIC,
                entropy_30min NUMERIC,
                entropy_60min NUMERIC,

                -- Autocorrelation (3 features)
                autocorr_lag1 NUMERIC,
                autocorr_lag5 NUMERIC,
                autocorr_lag15 NUMERIC,

                -- Jarque-Bera (2 features)
                jb_stat_30min NUMERIC,
                jb_stat_60min NUMERIC,

                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc)', pair_name);
    END LOOP;

    RAISE NOTICE '✅ Created 28 statistics_bqx parent tables (48 features each)';
END $$;

-- Create Partitions (28 pairs × 24 months = 672 partitions)
DO $$
DECLARE
    pair_name TEXT;
    year INT;
    month INT;
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
    pairs TEXT[] := ARRAY['audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
                          'cadchf', 'cadjpy', 'chfjpy',
                          'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
                          'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
                          'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
                          'usdcad', 'usdchf', 'usdjpy'];
    partition_count INT := 0;
BEGIN
    RAISE NOTICE '=== Creating Statistics BQX Partitions ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        FOR year IN 2024..2025
        LOOP
            FOR month IN 1..12
            LOOP
                start_date := make_date(year, month, 1);
                end_date := start_date + INTERVAL '1 month';
                partition_name := format('statistics_bqx_%s_%s_%s',
                                        pair_name, year, lpad(month::TEXT, 2, '0'));

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I
                    PARTITION OF bqx.statistics_bqx_%I
                    FOR VALUES FROM (%L) TO (%L)',
                    partition_name, pair_name, start_date, end_date);

                partition_count := partition_count + 1;

                IF partition_count % 100 = 0 THEN
                    RAISE NOTICE 'Created % partitions...', partition_count;
                END IF;
            END LOOP;
        END LOOP;
    END LOOP;

    RAISE NOTICE '✅ Created % statistics_bqx partitions', partition_count;
END $$;

COMMIT;

\echo '✅ Stage 1.6.12 Part B Complete: statistics_bqx created (48 features, 672 partitions)'
