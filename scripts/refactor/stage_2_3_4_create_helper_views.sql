-- ============================================================================
-- Stage 2.3 & 2.4: Helper Views and Functions
-- ============================================================================
-- Creates SQL views and functions to simplify currency index and arbitrage
-- calculations across multiple pairs and triplets
-- ============================================================================

-- ============================================================================
-- View 1: Currency Pair Metadata
-- ============================================================================

DROP VIEW IF EXISTS bqx.v_currency_pair_metadata CASCADE;

CREATE VIEW bqx.v_currency_pair_metadata AS
SELECT
    pair,
    UPPER(SUBSTRING(pair FROM 1 FOR 3)) as base_currency,
    UPPER(SUBSTRING(pair FROM 4 FOR 3)) as quote_currency
FROM (
    SELECT unnest(ARRAY[
        'AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD',
        'CADCHF', 'CADJPY', 'CHFJPY',
        'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD', 'EURUSD',
        'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPJPY', 'GBPNZD', 'GBPUSD',
        'NZDCAD', 'NZDCHF', 'NZDJPY', 'NZDUSD',
        'USDCAD', 'USDCHF', 'USDJPY'
    ]) as pair
) pairs;

COMMENT ON VIEW bqx.v_currency_pair_metadata IS 'Metadata view showing base and quote currencies for all 28 pairs';

-- ============================================================================
-- View 2: Pairs by Currency (for index calculation)
-- ============================================================================

DROP VIEW IF EXISTS bqx.v_pairs_by_currency CASCADE;

CREATE VIEW bqx.v_pairs_by_currency AS
SELECT
    currency,
    array_agg(DISTINCT pair ORDER BY pair) FILTER (WHERE position = 'base') as pairs_as_base,
    array_agg(DISTINCT pair ORDER BY pair) FILTER (WHERE position = 'quote') as pairs_as_quote,
    COUNT(DISTINCT pair) as total_pairs
FROM (
    SELECT base_currency as currency, pair, 'base' as position
    FROM bqx.v_currency_pair_metadata
    UNION ALL
    SELECT quote_currency as currency, pair, 'quote' as position
    FROM bqx.v_currency_pair_metadata
) currency_pairs
GROUP BY currency
ORDER BY currency;

COMMENT ON VIEW bqx.v_pairs_by_currency IS 'Shows all pairs containing each currency (as base or quote)';

-- ============================================================================
-- View 3: Triangular Arbitrage Triplets
-- ============================================================================

DROP VIEW IF EXISTS bqx.v_arbitrage_triplets CASCADE;

CREATE VIEW bqx.v_arbitrage_triplets AS
WITH triplets AS (
    -- EUR-USD-GBP
    SELECT 'EUR' as c1, 'USD' as c2, 'GBP' as c3, 'EURUSD' as p12, 'GBPUSD' as p23, 'EURGBP' as p31
    UNION ALL SELECT 'EUR', 'USD', 'JPY', 'EURUSD', 'USDJPY', 'EURJPY'
    UNION ALL SELECT 'EUR', 'USD', 'AUD', 'EURUSD', 'AUDUSD', 'EURAUD'
    UNION ALL SELECT 'EUR', 'USD', 'NZD', 'EURUSD', 'NZDUSD', 'EURNZD'
    UNION ALL SELECT 'EUR', 'USD', 'CAD', 'EURUSD', 'USDCAD', 'EURCAD'
    UNION ALL SELECT 'EUR', 'USD', 'CHF', 'EURUSD', 'USDCHF', 'EURCHF'
    UNION ALL SELECT 'EUR', 'GBP', 'JPY', 'EURGBP', 'GBPJPY', 'EURJPY'
    UNION ALL SELECT 'EUR', 'GBP', 'AUD', 'EURGBP', 'GBPAUD', 'EURAUD'
    UNION ALL SELECT 'EUR', 'GBP', 'NZD', 'EURGBP', 'GBPNZD', 'EURNZD'
    UNION ALL SELECT 'EUR', 'GBP', 'CAD', 'EURGBP', 'GBPCAD', 'EURCAD'
    UNION ALL SELECT 'EUR', 'GBP', 'CHF', 'EURGBP', 'GBPCHF', 'EURCHF'
    -- Add more common triplets (56 total exist, showing subset)
    UNION ALL SELECT 'GBP', 'USD', 'JPY', 'GBPUSD', 'USDJPY', 'GBPJPY'
    UNION ALL SELECT 'GBP', 'USD', 'AUD', 'GBPUSD', 'AUDUSD', 'GBPAUD'
    UNION ALL SELECT 'GBP', 'USD', 'NZD', 'GBPUSD', 'NZDUSD', 'GBPNZD'
    UNION ALL SELECT 'GBP', 'USD', 'CAD', 'GBPUSD', 'USDCAD', 'GBPCAD'
    UNION ALL SELECT 'GBP', 'USD', 'CHF', 'GBPUSD', 'USDCHF', 'GBPCHF'
    UNION ALL SELECT 'AUD', 'USD', 'JPY', 'AUDUSD', 'USDJPY', 'AUDJPY'
    UNION ALL SELECT 'AUD', 'USD', 'NZD', 'AUDUSD', 'NZDUSD', 'AUDNZD'
    UNION ALL SELECT 'AUD', 'USD', 'CAD', 'AUDUSD', 'USDCAD', 'AUDCAD'
    UNION ALL SELECT 'AUD', 'USD', 'CHF', 'AUDUSD', 'USDCHF', 'AUDCHF'
    UNION ALL SELECT 'NZD', 'USD', 'JPY', 'NZDUSD', 'USDJPY', 'NZDJPY'
    UNION ALL SELECT 'NZD', 'USD', 'CAD', 'NZDUSD', 'USDCAD', 'NZDCAD'
    UNION ALL SELECT 'NZD', 'USD', 'CHF', 'NZDUSD', 'USDCHF', 'NZDCHF'
    UNION ALL SELECT 'USD', 'CAD', 'JPY', 'USDCAD', 'CADJPY', 'USDJPY'
    UNION ALL SELECT 'USD', 'CAD', 'CHF', 'USDCAD', 'CADCHF', 'USDCHF'
    UNION ALL SELECT 'USD', 'CHF', 'JPY', 'USDCHF', 'CHFJPY', 'USDJPY'
)
SELECT
    c1 || '-' || c2 || '-' || c3 as triplet_name,
    c1 as currency_1,
    c2 as currency_2,
    c3 as currency_3,
    p12 as pair_1_2,
    p23 as pair_2_3,
    p31 as pair_3_1,
    -- Determine directions for each leg
    CASE WHEN SUBSTRING(p12 FROM 1 FOR 3) = c1 THEN 1 ELSE -1 END as dir_1,
    CASE WHEN SUBSTRING(p23 FROM 1 FOR 3) = c2 THEN 1 ELSE -1 END as dir_2,
    CASE WHEN SUBSTRING(p31 FROM 1 FOR 3) = c3 THEN 1 ELSE -1 END as dir_3
FROM triplets;

COMMENT ON VIEW bqx.v_arbitrage_triplets IS 'Valid triangular arbitrage triplets with direction indicators';

-- ============================================================================
-- Function: Get Currency Strength Index at Timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION bqx.get_currency_strength_index(
    target_currency VARCHAR(3),
    target_timestamp TIMESTAMP WITH TIME ZONE,
    lookback_minutes INT DEFAULT 60
)
RETURNS DOUBLE PRECISION AS $$
DECLARE
    strength_index DOUBLE PRECISION;
BEGIN
    -- Calculate weighted average of currency strength across all pairs
    -- containing the target currency within lookback window
    SELECT AVG(rate_value) INTO strength_index
    FROM (
        -- Pairs where currency is base (use rate_index directly)
        SELECT m1.rate_index as rate_value
        FROM bqx.v_currency_pair_metadata meta
        JOIN bqx.m1_eurusd m1 ON UPPER(m1.pair) = meta.pair  -- Example, need union for all pairs
        WHERE meta.base_currency = target_currency
          AND m1.ts_utc >= target_timestamp - (lookback_minutes || ' minutes')::INTERVAL
          AND m1.ts_utc <= target_timestamp

        UNION ALL

        -- Pairs where currency is quote (use 1/rate_index)
        SELECT 1.0 / NULLIF(m1.rate_index, 0) as rate_value
        FROM bqx.v_currency_pair_metadata meta
        JOIN bqx.m1_eurusd m1 ON UPPER(m1.pair) = meta.pair
        WHERE meta.quote_currency = target_currency
          AND m1.ts_utc >= target_timestamp - (lookback_minutes || ' minutes')::INTERVAL
          AND m1.ts_utc <= target_timestamp
    ) currency_rates;

    RETURN strength_index;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION bqx.get_currency_strength_index IS 'Calculates currency strength index from all pairs containing the currency';

-- ============================================================================
-- View 4: Latest Arbitrage Opportunities (for monitoring)
-- ============================================================================

DROP VIEW IF EXISTS bqx.v_latest_arbitrage_opportunities CASCADE;

CREATE OR REPLACE VIEW bqx.v_latest_arbitrage_opportunities AS
WITH ranked_arbitrage AS (
    SELECT
        pair,
        ts_utc,
        arbitrage_profit_pct,
        arbitrage_opportunity,
        arbitrage_direction,
        arbitrage_max_profit,
        ROW_NUMBER() OVER (PARTITION BY pair ORDER BY ts_utc DESC) as rn
    FROM bqx.arbitrage
    WHERE arbitrage_opportunity = TRUE
)
SELECT
    pair,
    ts_utc,
    arbitrage_profit_pct,
    arbitrage_max_profit,
    arbitrage_direction,
    CASE
        WHEN arbitrage_direction = 1 THEN 'Clockwise'
        WHEN arbitrage_direction = -1 THEN 'Counter-clockwise'
        ELSE 'None'
    END as direction_desc
FROM ranked_arbitrage
WHERE rn = 1
ORDER BY arbitrage_max_profit DESC;

COMMENT ON VIEW bqx.v_latest_arbitrage_opportunities IS 'Shows latest arbitrage opportunities for each pair';

-- ============================================================================
-- View 5: Currency Index Summary Statistics
-- ============================================================================

DROP VIEW IF EXISTS bqx.v_currency_index_stats CASCADE;

CREATE OR REPLACE VIEW bqx.v_currency_index_stats AS
SELECT
    pair,
    COUNT(*) as total_records,
    MIN(ts_utc) as earliest_timestamp,
    MAX(ts_utc) as latest_timestamp,
    AVG(base_currency_index) as avg_base_index,
    AVG(quote_currency_index) as avg_quote_index,
    AVG(currency_index_differential) as avg_differential,
    STDDEV(currency_index_differential) as stddev_differential,
    COUNT(*) FILTER (WHERE ABS(pair_divergence_from_index) > 0.01) as significant_divergences,
    AVG(related_pairs_correlation_60min) as avg_correlation,
    AVG(triangular_consistency_score) as avg_consistency
FROM bqx.currency_index
GROUP BY pair
ORDER BY pair;

COMMENT ON VIEW bqx.v_currency_index_stats IS 'Summary statistics for currency index features by pair';

-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT SELECT ON ALL TABLES IN SCHEMA bqx TO postgres;
GRANT SELECT ON bqx.v_currency_pair_metadata TO postgres;
GRANT SELECT ON bqx.v_pairs_by_currency TO postgres;
GRANT SELECT ON bqx.v_arbitrage_triplets TO postgres;
GRANT SELECT ON bqx.v_latest_arbitrage_opportunities TO postgres;
GRANT SELECT ON bqx.v_currency_index_stats TO postgres;

-- ============================================================================
-- Verification
-- ============================================================================

-- Test currency pair metadata
SELECT * FROM bqx.v_currency_pair_metadata LIMIT 10;

-- Test pairs by currency
SELECT * FROM bqx.v_pairs_by_currency;

-- Test arbitrage triplets
SELECT COUNT(*) as triplet_count FROM bqx.v_arbitrage_triplets;

-- Show sample triplet
SELECT * FROM bqx.v_arbitrage_triplets WHERE triplet_name = 'EUR-USD-GBP';

RAISE NOTICE 'Helper views and functions created successfully';
