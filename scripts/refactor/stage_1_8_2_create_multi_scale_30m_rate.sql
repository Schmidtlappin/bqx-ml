-- Stage 1.8.2 Part A: Create multi_scale_30m_rate - 15 features
-- Category: Multi-Scale Features (30-minute aggregates)
-- Mechanism: Resample to 30m resolution, compare with 1m scale
-- Impact: 15-20% improvement in long-term trend consistency

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
    RAISE NOTICE '=== Creating Multi-Scale 30m Rate (IDX) Parent Tables (15 features) ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.multi_scale_30m_rate_%I (
                ts_utc TIMESTAMP NOT NULL,

                -- 30-Minute Core Stats (5 features)
                rate_idx_30m_sma_10 NUMERIC,            -- 10-period SMA on 30-min bars
                rate_idx_30m_ema_20 NUMERIC,            -- 20-period EMA on 30-min bars
                rate_idx_30m_vol_20 NUMERIC,            -- 20-period volatility
                bqx_30m_sma_10 NUMERIC,                 -- BQX 30-min SMA
                bqx_30m_vol_20 NUMERIC,                 -- BQX 30-min volatility

                -- 30-Minute Technical (4 features)
                rsi_30m_14 NUMERIC,                     -- RSI on 30-min bars
                macd_30m NUMERIC,                       -- MACD on 30-min bars
                atr_30m_14 NUMERIC,                     -- ATR on 30-min bars
                bb_width_30m NUMERIC,                   -- Bollinger band width

                -- Multi-Scale Comparisons 1m vs 30m (6 features)
                sma_1m_vs_30m_ratio NUMERIC,            -- 1-min / 30-min SMA
                vol_1m_vs_30m_ratio NUMERIC,            -- Volatility ratio
                trend_1m_vs_30m_agreement NUMERIC,      -- Binary: trends agree
                regime_1m_vs_30m_agreement NUMERIC,     -- Binary: regimes agree
                scale_30m_dominance NUMERIC,            -- 30m trend strength vs 1m
                scale_30m_divergence_flag NUMERIC,      -- Binary: scales diverging

                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc)', pair_name);
    END LOOP;

    RAISE NOTICE '✅ Created 28 multi_scale_30m_rate parent tables (15 features each)';
END $$;

-- Create Partitions (336 for existing data range)
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
    RAISE NOTICE '=== Creating Multi-Scale 30m Rate Partitions ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        FOR year IN 2024..2025
        LOOP
            FOR month IN 1..12
            LOOP
                IF (year = 2024 AND month < 7) THEN CONTINUE; END IF;
                IF (year = 2025 AND month > 6) THEN CONTINUE; END IF;

                start_date := make_date(year, month, 1);
                end_date := start_date + INTERVAL '1 month';
                partition_name := format('multi_scale_30m_rate_%s_%s_%s',
                                        pair_name, year, lpad(month::TEXT, 2, '0'));

                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.%I
                    PARTITION OF bqx.multi_scale_30m_rate_%I
                    FOR VALUES FROM (%L) TO (%L)',
                    partition_name, pair_name, start_date, end_date);

                partition_count := partition_count + 1;

                IF partition_count % 100 = 0 THEN
                    RAISE NOTICE 'Created % partitions...', partition_count;
                END IF;
            END LOOP;
        END LOOP;
    END LOOP;

    RAISE NOTICE '✅ Created % multi_scale_30m_rate partitions', partition_count;
END $$;

COMMIT;

\echo '✅ Stage 1.8.2 Part A Complete: multi_scale_30m_rate created (15 features, 336 partitions)'
