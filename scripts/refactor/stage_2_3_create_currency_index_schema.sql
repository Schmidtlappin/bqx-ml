-- ============================================================================
-- Stage 2.3: Cross-Pair Currency Indices - Database Schema
-- ============================================================================
-- Creates tables for currency strength indices calculated from all pairs
-- containing each currency (8 currencies: EUR, USD, GBP, JPY, AUD, NZD, CAD, CHF)
--
-- Features (8 total):
--   1. base_currency_index: Strength index of base currency
--   2. quote_currency_index: Strength index of quote currency
--   3. currency_index_differential: Difference between base and quote indices
--   4. base_currency_strength_percentile: Percentile rank of base currency
--   5. quote_currency_strength_percentile: Percentile rank of quote currency
--   6. pair_divergence_from_index: How much pair deviates from currency indices
--   7. related_pairs_correlation_60min: Correlation with related pairs (60-min window)
--   8. triangular_consistency_score: How consistent with triangular relationships
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
    -- Drop all currency_index partitions
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
            partition_name := 'currency_index_' || pair_name || '_' || year_month;
            EXECUTE format('DROP TABLE IF EXISTS bqx.%I CASCADE', partition_name);
        END LOOP;
    END LOOP;

    -- Drop parent table
    DROP TABLE IF EXISTS bqx.currency_index CASCADE;
END $$;

-- ============================================================================
-- Create Parent Table: currency_index
-- ============================================================================

CREATE TABLE bqx.currency_index (
    ts_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    pair VARCHAR(10) NOT NULL,

    -- Currency Strength Indices (calculated from all pairs containing currency)
    base_currency_index DOUBLE PRECISION,      -- Weighted average of base currency across all pairs
    quote_currency_index DOUBLE PRECISION,     -- Weighted average of quote currency across all pairs
    currency_index_differential DOUBLE PRECISION, -- base_index - quote_index

    -- Currency Strength Percentiles (0-100)
    base_currency_strength_percentile DOUBLE PRECISION,  -- Rank of base currency (0-100)
    quote_currency_strength_percentile DOUBLE PRECISION, -- Rank of quote currency (0-100)

    -- Pair Divergence from Currency Indices
    pair_divergence_from_index DOUBLE PRECISION, -- How much actual pair rate differs from index-implied rate

    -- Cross-Pair Correlations
    related_pairs_correlation_60min DOUBLE PRECISION, -- Rolling correlation with related pairs (60-min window)

    -- Triangular Consistency
    triangular_consistency_score DOUBLE PRECISION, -- Deviation from triangular arbitrage equilibrium

    -- Metadata
    year_month VARCHAR(7) NOT NULL,

    PRIMARY KEY (ts_utc, pair)
) PARTITION BY LIST (pair);

-- Create indexes on parent table
CREATE INDEX idx_currency_index_ts ON bqx.currency_index (ts_utc);
CREATE INDEX idx_currency_index_pair ON bqx.currency_index (pair);
CREATE INDEX idx_currency_index_year_month ON bqx.currency_index (year_month);

COMMENT ON TABLE bqx.currency_index IS 'Currency strength indices calculated from cross-pair relationships';
COMMENT ON COLUMN bqx.currency_index.base_currency_index IS 'Strength index of base currency (weighted avg across all pairs)';
COMMENT ON COLUMN bqx.currency_index.quote_currency_index IS 'Strength index of quote currency (weighted avg across all pairs)';
COMMENT ON COLUMN bqx.currency_index.currency_index_differential IS 'Difference between base and quote currency indices';
COMMENT ON COLUMN bqx.currency_index.base_currency_strength_percentile IS 'Percentile rank (0-100) of base currency strength';
COMMENT ON COLUMN bqx.currency_index.quote_currency_strength_percentile IS 'Percentile rank (0-100) of quote currency strength';
COMMENT ON COLUMN bqx.currency_index.pair_divergence_from_index IS 'Deviation of pair from index-implied rate';
COMMENT ON COLUMN bqx.currency_index.related_pairs_correlation_60min IS 'Correlation with related pairs (60-min rolling window)';
COMMENT ON COLUMN bqx.currency_index.triangular_consistency_score IS 'Consistency score for triangular arbitrage relationships';

-- ============================================================================
-- Create Monthly Partitions for All 28 Pairs
-- ============================================================================

DO $$
DECLARE
    pair_name TEXT;
    year_month TEXT;
    partition_name TEXT;
    start_date TIMESTAMP WITH TIME ZONE;
    end_date TIMESTAMP WITH TIME ZONE;
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
            partition_name := 'currency_index_' || pair_name || '_' || year_month;

            -- Create partition
            EXECUTE format('
                CREATE TABLE bqx.%I PARTITION OF bqx.currency_index
                FOR VALUES IN (%L)
            ', partition_name, UPPER(pair_name));

            -- Create indexes on partition
            EXECUTE format('CREATE INDEX idx_%I_ts ON bqx.%I (ts_utc)', partition_name, partition_name);
            EXECUTE format('CREATE INDEX idx_%I_base_idx ON bqx.%I (base_currency_index)', partition_name, partition_name);
            EXECUTE format('CREATE INDEX idx_%I_quote_idx ON bqx.%I (quote_currency_index)', partition_name, partition_name);

            RAISE NOTICE 'Created partition: %', partition_name;
        END LOOP;
    END LOOP;
END $$;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Count total partitions created
SELECT COUNT(*) as total_partitions
FROM pg_tables
WHERE schemaname = 'bqx'
  AND tablename LIKE 'currency_index_%'
  AND tablename ~ '_[0-9]{4}_[0-9]{2}$';
-- Expected: 336 partitions (28 pairs × 12 months)

-- List sample partitions
SELECT tablename
FROM pg_tables
WHERE schemaname = 'bqx'
  AND tablename LIKE 'currency_index_%'
ORDER BY tablename
LIMIT 10;

-- Show parent table structure
\d bqx.currency_index;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA bqx TO postgres;

RAISE NOTICE 'Stage 2.3 schema creation complete. Total partitions: 336 (28 pairs × 12 months)';
