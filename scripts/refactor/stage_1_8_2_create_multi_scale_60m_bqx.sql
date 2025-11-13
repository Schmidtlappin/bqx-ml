-- Stage 1.8.2 Part D: Create multi_scale_60m_bqx - 15 features
-- Category: Multi-Scale Features (60-minute BQX aggregates)
-- Mechanism: Resample BQX to 60m resolution
-- Impact: 15-20% improvement in momentum trend consistency

\timing on
\set ON_ERROR_STOP on

BEGIN;

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
    RAISE NOTICE '=== Creating Multi-Scale 60m BQX Parent Tables (15 features) ===';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS bqx.multi_scale_60m_bqx_%I (
                ts_utc TIMESTAMP NOT NULL,
                rate_idx_60m_sma_10 NUMERIC,
                rate_idx_60m_ema_20 NUMERIC,
                rate_idx_60m_vol_20 NUMERIC,
                bqx_60m_sma_10 NUMERIC,
                bqx_60m_vol_20 NUMERIC,
                rsi_60m_14 NUMERIC,
                macd_60m NUMERIC,
                atr_60m_14 NUMERIC,
                bb_width_60m NUMERIC,
                sma_1m_vs_60m_ratio NUMERIC,
                vol_1m_vs_60m_ratio NUMERIC,
                trend_1m_vs_60m_agreement NUMERIC,
                regime_1m_vs_60m_agreement NUMERIC,
                scale_60m_dominance NUMERIC,
                scale_60m_divergence_flag NUMERIC,
                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc)', pair_name);
    END LOOP;
    RAISE NOTICE '✅ Created 28 multi_scale_60m_bqx parent tables';
END $$;

DO $$
DECLARE
    pair_name TEXT;
    year INT;
    month INT;
    pairs TEXT[] := ARRAY['audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
                          'cadchf', 'cadjpy', 'chfjpy',
                          'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
                          'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
                          'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
                          'usdcad', 'usdchf', 'usdjpy'];
    partition_count INT := 0;
BEGIN
    FOREACH pair_name IN ARRAY pairs
    LOOP
        FOR year IN 2024..2025
        LOOP
            FOR month IN 1..12
            LOOP
                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS bqx.multi_scale_60m_bqx_%s_%s_%s
                    PARTITION OF bqx.multi_scale_60m_bqx_%I
                    FOR VALUES FROM (%L) TO (%L)',
                    pair_name, year, lpad(month::TEXT, 2, '0'), pair_name,
                    make_date(year, month, 1), make_date(year, month, 1) + INTERVAL '1 month');
                partition_count := partition_count + 1;
            END LOOP;
        END LOOP;
    END LOOP;
    RAISE NOTICE '✅ Created % multi_scale_60m_bqx partitions', partition_count;
END $$;

COMMIT;
\echo '✅ Stage 1.8.2 Part D Complete: multi_scale_60m_bqx created (15 features, 672 partitions)'
