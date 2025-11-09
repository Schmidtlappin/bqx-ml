-- BQX (Backward Cumulative Returns) Tables DDL
-- Generated for all 28 preferred forex pairs
-- Date: 2025-11-09
--
-- Formula: w{W}_bqx_return = Σ(i=1 to W)[rate(t-i) - rate(t)] / rate(t)
-- Windows: 15, 30, 45, 60, 75 minutes
-- Fields per table: 40 (3 core + 30 window metrics + 7 aggregates)

-- ============================================================================
-- BQX Table for AUDCAD
-- ============================================================================
CREATE TABLE bqx.bqx_audcad (
    ts_utc TIMESTAMPTZ NOT NULL,
    rate DOUBLE PRECISION NOT NULL,

    -- Window 15 minutes
    w15_bqx_return DOUBLE PRECISION,
    w15_bqx_max DOUBLE PRECISION,
    w15_bqx_min DOUBLE PRECISION,
    w15_bqx_avg DOUBLE PRECISION,
    w15_bqx_stdev DOUBLE PRECISION,
    w15_bqx_endpoint DOUBLE PRECISION,

    -- Window 30 minutes
    w30_bqx_return DOUBLE PRECISION,
    w30_bqx_max DOUBLE PRECISION,
    w30_bqx_min DOUBLE PRECISION,
    w30_bqx_avg DOUBLE PRECISION,
    w30_bqx_stdev DOUBLE PRECISION,
    w30_bqx_endpoint DOUBLE PRECISION,

    -- Window 45 minutes
    w45_bqx_return DOUBLE PRECISION,
    w45_bqx_max DOUBLE PRECISION,
    w45_bqx_min DOUBLE PRECISION,
    w45_bqx_avg DOUBLE PRECISION,
    w45_bqx_stdev DOUBLE PRECISION,
    w45_bqx_endpoint DOUBLE PRECISION,

    -- Window 60 minutes
    w60_bqx_return DOUBLE PRECISION,
    w60_bqx_max DOUBLE PRECISION,
    w60_bqx_min DOUBLE PRECISION,
    w60_bqx_avg DOUBLE PRECISION,
    w60_bqx_stdev DOUBLE PRECISION,
    w60_bqx_endpoint DOUBLE PRECISION,

    -- Window 75 minutes
    w75_bqx_return DOUBLE PRECISION,
    w75_bqx_max DOUBLE PRECISION,
    w75_bqx_min DOUBLE PRECISION,
    w75_bqx_avg DOUBLE PRECISION,
    w75_bqx_stdev DOUBLE PRECISION,
    w75_bqx_endpoint DOUBLE PRECISION,

    -- Aggregate fields (using w75 window)
    agg_bqx_return DOUBLE PRECISION,
    agg_bqx_max DOUBLE PRECISION,
    agg_bqx_min DOUBLE PRECISION,
    agg_bqx_avg DOUBLE PRECISION,
    agg_bqx_stdev DOUBLE PRECISION,
    agg_bqx_range DOUBLE PRECISION,
    agg_bqx_volatility DOUBLE PRECISION,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);

-- Create monthly partitions for 2024-2025
CREATE TABLE bqx.bqx_audcad_2024m07 PARTITION OF bqx.bqx_audcad FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');
CREATE TABLE bqx.bqx_audcad_2024m08 PARTITION OF bqx.bqx_audcad FOR VALUES FROM ('2024-08-01') TO ('2024-09-01');
CREATE TABLE bqx.bqx_audcad_2024m09 PARTITION OF bqx.bqx_audcad FOR VALUES FROM ('2024-09-01') TO ('2024-10-01');
CREATE TABLE bqx.bqx_audcad_2024m10 PARTITION OF bqx.bqx_audcad FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');
CREATE TABLE bqx.bqx_audcad_2024m11 PARTITION OF bqx.bqx_audcad FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');
CREATE TABLE bqx.bqx_audcad_2024m12 PARTITION OF bqx.bqx_audcad FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');
CREATE TABLE bqx.bqx_audcad_2025m01 PARTITION OF bqx.bqx_audcad FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE bqx.bqx_audcad_2025m02 PARTITION OF bqx.bqx_audcad FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
CREATE TABLE bqx.bqx_audcad_2025m03 PARTITION OF bqx.bqx_audcad FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');
CREATE TABLE bqx.bqx_audcad_2025m04 PARTITION OF bqx.bqx_audcad FOR VALUES FROM ('2025-04-01') TO ('2025-05-01');
CREATE TABLE bqx.bqx_audcad_2025m05 PARTITION OF bqx.bqx_audcad FOR VALUES FROM ('2025-05-01') TO ('2025-06-01');
CREATE TABLE bqx.bqx_audcad_2025m06 PARTITION OF bqx.bqx_audcad FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');

CREATE INDEX idx_bqx_audcad_ts ON bqx.bqx_audcad (ts_utc);

-- Note: Repeat above structure for all 28 preferred pairs
-- For brevity, generating remaining tables with DO block

DO $$
DECLARE
    pair TEXT;
    pairs TEXT[] := ARRAY[
        'audchf', 'audjpy', 'audnzd', 'audusd',
        'cadchf', 'cadjpy', 'chfjpy',
        'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
        'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
        'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
        'usdcad', 'usdchf', 'usdjpy'
    ];
    month_start TEXT;
    month_end TEXT;
BEGIN
    FOREACH pair IN ARRAY pairs
    LOOP
        -- Create parent table
        EXECUTE format('
            CREATE TABLE bqx.bqx_%s (
                ts_utc TIMESTAMPTZ NOT NULL,
                rate DOUBLE PRECISION NOT NULL,

                w15_bqx_return DOUBLE PRECISION,
                w15_bqx_max DOUBLE PRECISION,
                w15_bqx_min DOUBLE PRECISION,
                w15_bqx_avg DOUBLE PRECISION,
                w15_bqx_stdev DOUBLE PRECISION,
                w15_bqx_endpoint DOUBLE PRECISION,

                w30_bqx_return DOUBLE PRECISION,
                w30_bqx_max DOUBLE PRECISION,
                w30_bqx_min DOUBLE PRECISION,
                w30_bqx_avg DOUBLE PRECISION,
                w30_bqx_stdev DOUBLE PRECISION,
                w30_bqx_endpoint DOUBLE PRECISION,

                w45_bqx_return DOUBLE PRECISION,
                w45_bqx_max DOUBLE PRECISION,
                w45_bqx_min DOUBLE PRECISION,
                w45_bqx_avg DOUBLE PRECISION,
                w45_bqx_stdev DOUBLE PRECISION,
                w45_bqx_endpoint DOUBLE PRECISION,

                w60_bqx_return DOUBLE PRECISION,
                w60_bqx_max DOUBLE PRECISION,
                w60_bqx_min DOUBLE PRECISION,
                w60_bqx_avg DOUBLE PRECISION,
                w60_bqx_stdev DOUBLE PRECISION,
                w60_bqx_endpoint DOUBLE PRECISION,

                w75_bqx_return DOUBLE PRECISION,
                w75_bqx_max DOUBLE PRECISION,
                w75_bqx_min DOUBLE PRECISION,
                w75_bqx_avg DOUBLE PRECISION,
                w75_bqx_stdev DOUBLE PRECISION,
                w75_bqx_endpoint DOUBLE PRECISION,

                agg_bqx_return DOUBLE PRECISION,
                agg_bqx_max DOUBLE PRECISION,
                agg_bqx_min DOUBLE PRECISION,
                agg_bqx_avg DOUBLE PRECISION,
                agg_bqx_stdev DOUBLE PRECISION,
                agg_bqx_range DOUBLE PRECISION,
                agg_bqx_volatility DOUBLE PRECISION,

                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc);
        ', pair);

        -- Create monthly partitions (2024-07 through 2025-06)
        FOR i IN 7..12 LOOP
            month_start := format('2024-%s-01', lpad(i::TEXT, 2, '0'));
            IF i = 12 THEN
                month_end := '2025-01-01';
            ELSE
                month_end := format('2024-%s-01', lpad((i+1)::TEXT, 2, '0'));
            END IF;

            EXECUTE format('
                CREATE TABLE bqx.bqx_%s_2024m%s
                PARTITION OF bqx.bqx_%s
                FOR VALUES FROM (%L) TO (%L);
            ', pair, lpad(i::TEXT, 2, '0'), pair, month_start, month_end);
        END LOOP;

        FOR i IN 1..6 LOOP
            month_start := format('2025-%s-01', lpad(i::TEXT, 2, '0'));
            month_end := format('2025-%s-01', lpad((i+1)::TEXT, 2, '0'));

            EXECUTE format('
                CREATE TABLE bqx.bqx_%s_2025m%s
                PARTITION OF bqx.bqx_%s
                FOR VALUES FROM (%L) TO (%L);
            ', pair, lpad(i::TEXT, 2, '0'), pair, month_start, month_end);
        END LOOP;

        -- Create index
        EXECUTE format('
            CREATE INDEX idx_bqx_%s_ts ON bqx.bqx_%s (ts_utc);
        ', pair, pair);

        RAISE NOTICE 'Created BQX table and partitions for %', pair;
    END LOOP;
END $$;

-- Summary
SELECT
    'BQX Table Creation Complete' as status,
    COUNT(*) as total_tables
FROM pg_tables
WHERE schemaname = 'bqx'
  AND tablename ~ '^bqx_[a-z]+$';
