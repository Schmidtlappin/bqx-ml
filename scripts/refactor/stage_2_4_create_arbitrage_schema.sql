-- ============================================================================
-- Stage 2.4: Arbitrage Detection Features - Database Schema
-- ============================================================================
-- Creates tables for triangular arbitrage opportunity detection
-- Uses 56 valid currency triplets (e.g., EUR-USD-GBP)
--
-- Features (4 total):
--   1. arbitrage_profit_pct: Percentage profit from round-trip arbitrage
--   2. arbitrage_opportunity: Boolean flag if profit > threshold
--   3. arbitrage_direction: Optimal direction (1=clockwise, -1=counter-clockwise, 0=none)
--   4. arbitrage_max_profit: Maximum profit considering both directions
--
-- Algorithm:
--   For each timestamp, compute round-trip conversion through 3 currencies
--   Example: EUR → USD → GBP → EUR
--   If final amount > initial (after costs), arbitrage exists
--
-- Partitioning: Monthly partitions (year_month) for each pair
-- Retention: Jul 2024 - Jun 2025 (12 months)
-- ============================================================================

-- Drop existing tables if they exist
DO $$
DECLARE
    pair_name TEXT;
    year_month TEXT;
    partition_name TEXT;
BEGIN
    -- Drop all arbitrage partitions
    FOR pair_name IN SELECT unnest(ARRAY[
        'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
        'cadchf', 'cadjpy', 'chfjpy',
        'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
        'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
        'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
        'usdcad', 'usdchf', 'usdjpy'
    ])
    LOOP
        FOR year_month IN SELECT unnest(ARRAY[
            '2024_07', '2024_08', '2024_09', '2024_10', '2024_11', '2024_12',
            '2025_01', '2025_02', '2025_03', '2025_04', '2025_05', '2025_06'
        ])
        LOOP
            partition_name := 'arbitrage_' || pair_name || '_' || year_month;
            EXECUTE format('DROP TABLE IF EXISTS bqx.%I CASCADE', partition_name);
        END LOOP;
    END LOOP;

    -- Drop parent table
    DROP TABLE IF EXISTS bqx.arbitrage CASCADE;
END $$;

-- ============================================================================
-- Create Parent Table: arbitrage
-- ============================================================================

CREATE TABLE bqx.arbitrage (
    ts_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    pair VARCHAR(10) NOT NULL,

    -- Arbitrage Opportunity Metrics
    arbitrage_profit_pct DOUBLE PRECISION,        -- % profit from round-trip (can be negative)
    arbitrage_opportunity BOOLEAN,                -- TRUE if profit > threshold (0.5%)
    arbitrage_direction SMALLINT,                 -- 1=clockwise, -1=counter-clockwise, 0=no opportunity
    arbitrage_max_profit DOUBLE PRECISION,        -- Maximum profit considering both directions

    -- Metadata
    year_month VARCHAR(7) NOT NULL,

    PRIMARY KEY (ts_utc, pair)
) PARTITION BY LIST (pair);

-- Create indexes on parent table
CREATE INDEX idx_arbitrage_ts ON bqx.arbitrage (ts_utc);
CREATE INDEX idx_arbitrage_pair ON bqx.arbitrage (pair);
CREATE INDEX idx_arbitrage_opportunity ON bqx.arbitrage (arbitrage_opportunity);
CREATE INDEX idx_arbitrage_profit ON bqx.arbitrage (arbitrage_profit_pct);

COMMENT ON TABLE bqx.arbitrage IS 'Triangular arbitrage opportunity detection across currency triplets';
COMMENT ON COLUMN bqx.arbitrage.arbitrage_profit_pct IS 'Percentage profit from round-trip arbitrage (after transaction costs)';
COMMENT ON COLUMN bqx.arbitrage.arbitrage_opportunity IS 'TRUE if arbitrage profit exceeds threshold (0.5%)';
COMMENT ON COLUMN bqx.arbitrage.arbitrage_direction IS 'Optimal arbitrage direction: 1=clockwise, -1=counter-clockwise, 0=none';
COMMENT ON COLUMN bqx.arbitrage.arbitrage_max_profit IS 'Maximum profit percentage considering both clockwise and counter-clockwise paths';

-- ============================================================================
-- Create Monthly Partitions for All 28 Pairs
-- ============================================================================

DO $$
DECLARE
    pair_name TEXT;
    year_month TEXT;
    partition_name TEXT;
BEGIN
    FOR pair_name IN SELECT unnest(ARRAY[
        'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
        'cadchf', 'cadjpy', 'chfjpy',
        'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
        'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
        'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
        'usdcad', 'usdchf', 'usdjpy'
    ])
    LOOP
        FOR year_month IN SELECT unnest(ARRAY[
            '2024_07', '2024_08', '2024_09', '2024_10', '2024_11', '2024_12',
            '2025_01', '2025_02', '2025_03', '2025_04', '2025_05', '2025_06'
        ])
        LOOP
            partition_name := 'arbitrage_' || pair_name || '_' || year_month;

            -- Create partition
            EXECUTE format('
                CREATE TABLE bqx.%I PARTITION OF bqx.arbitrage
                FOR VALUES IN (%L)
            ', partition_name, UPPER(pair_name));

            -- Create indexes on partition
            EXECUTE format('CREATE INDEX idx_%I_ts ON bqx.%I (ts_utc)', partition_name, partition_name);
            EXECUTE format('CREATE INDEX idx_%I_opp ON bqx.%I (arbitrage_opportunity)', partition_name, partition_name);
            EXECUTE format('CREATE INDEX idx_%I_profit ON bqx.%I (arbitrage_profit_pct) WHERE arbitrage_opportunity = TRUE', partition_name, partition_name);

            RAISE NOTICE 'Created partition: %', partition_name;
        END LOOP;
    END LOOP;
END $$;

-- ============================================================================
-- Create Helper Function: Calculate Triangular Arbitrage
-- ============================================================================

CREATE OR REPLACE FUNCTION bqx.calculate_triangular_arbitrage(
    rate_1 DOUBLE PRECISION,  -- First leg exchange rate
    rate_2 DOUBLE PRECISION,  -- Second leg exchange rate
    rate_3 DOUBLE PRECISION,  -- Third leg exchange rate
    direction_1 SMALLINT,     -- 1=direct, -1=inverse
    direction_2 SMALLINT,
    direction_3 SMALLINT,
    transaction_cost_pct DOUBLE PRECISION DEFAULT 0.3  -- 0.3% per round trip (3 trades)
)
RETURNS DOUBLE PRECISION AS $$
DECLARE
    amount DOUBLE PRECISION := 1.0;  -- Start with 1 unit
BEGIN
    -- Leg 1
    IF direction_1 = 1 THEN
        amount := amount * rate_1;
    ELSE
        amount := amount / rate_1;
    END IF;

    -- Leg 2
    IF direction_2 = 1 THEN
        amount := amount * rate_2;
    ELSE
        amount := amount / rate_2;
    END IF;

    -- Leg 3
    IF direction_3 = 1 THEN
        amount := amount * rate_3;
    ELSE
        amount := amount / rate_3;
    END IF;

    -- Subtract transaction costs
    amount := amount * (1 - transaction_cost_pct / 100.0);

    -- Return profit percentage
    RETURN (amount - 1.0) * 100.0;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION bqx.calculate_triangular_arbitrage IS 'Calculates arbitrage profit % for a triangular currency path';

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Count total partitions created
SELECT COUNT(*) as total_partitions
FROM pg_tables
WHERE schemaname = 'bqx'
  AND tablename LIKE 'arbitrage_%'
  AND tablename ~ '_[0-9]{4}_[0-9]{2}$';
-- Expected: 336 partitions (28 pairs × 12 months)

-- List sample partitions
SELECT tablename
FROM pg_tables
WHERE schemaname = 'bqx'
  AND tablename LIKE 'arbitrage_%'
ORDER BY tablename
LIMIT 10;

-- Show parent table structure
\d bqx.arbitrage;

-- Test arbitrage calculation function
-- Example: EUR → USD → GBP → EUR
-- EURUSD = 1.1000, GBPUSD = 1.2500, EURGBP = 0.8800
SELECT bqx.calculate_triangular_arbitrage(
    1.1000,  -- EURUSD (direct)
    1.2500,  -- GBPUSD (inverse, so we divide)
    0.8800,  -- EURGBP (direct)
    1,       -- EURUSD direction (multiply)
    -1,      -- GBPUSD direction (divide)
    1,       -- EURGBP direction (multiply)
    0.3      -- 0.3% transaction cost
) as arbitrage_profit_pct;
-- Expected: Negative (no arbitrage in this example)

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA bqx TO postgres;

RAISE NOTICE 'Stage 2.4 schema creation complete. Total partitions: 336 (28 pairs × 12 months)';
