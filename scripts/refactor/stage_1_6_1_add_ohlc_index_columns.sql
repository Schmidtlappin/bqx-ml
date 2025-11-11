-- ============================================================================
-- Stage 1.6.1: OHLC Index Schema Enhancement
-- ============================================================================
-- Purpose: Add high_index, low_index, open_index columns to all 28 M1 tables
-- Rationale: Technical indicators (ADX, ATR, Stochastic, Ichimoku, etc.)
--            require OHLC index data for cross-pair comparability
-- Impact: Unblocks 45 technical indicator features (41% of Phase 2)
-- Execution: ~3 hours (schema change + indexing, backfill separate)
-- Date: 2025-11-11
-- ============================================================================

-- Strategy:
-- 1. Add columns to parent M1 tables (propagates to all partitions automatically)
-- 2. Columns use DOUBLE PRECISION (same as rate_index for consistency)
-- 3. Values will be backfilled by separate worker script
-- 4. Formula: {ohlc}_index = ({ohlc} / baseline_rate) * 100
--    where baseline_rate = first rate in each monthly partition
--
-- Benefits:
-- - Cross-pair comparability (all pairs normalized to ~100 scale)
-- - Enables 45 TA-Lib technical indicators
-- - Consistent with existing rate_index architecture
-- - Small storage overhead (~12 bytes * 3 columns * 10.3M rows = ~370 MB)

\timing on
\set ON_ERROR_STOP on

-- Begin transaction for atomic schema changes
BEGIN;

-- ============================================================================
-- Add OHLC Index Columns to All 28 M1 Tables
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
BEGIN
    FOREACH pair_name IN ARRAY pair_list
    LOOP
        RAISE NOTICE 'Adding OHLC index columns to m1_%', pair_name;

        -- Add high_index column
        EXECUTE format('
            ALTER TABLE bqx.m1_%I
            ADD COLUMN IF NOT EXISTS high_index DOUBLE PRECISION;
        ', pair_name);

        -- Add low_index column
        EXECUTE format('
            ALTER TABLE bqx.m1_%I
            ADD COLUMN IF NOT EXISTS low_index DOUBLE PRECISION;
        ', pair_name);

        -- Add open_index column
        EXECUTE format('
            ALTER TABLE bqx.m1_%I
            ADD COLUMN IF NOT EXISTS open_index DOUBLE PRECISION;
        ', pair_name);

        RAISE NOTICE '✓ Added OHLC index columns to m1_%', pair_name;
    END LOOP;
END $$;

-- ============================================================================
-- Create Indexes on OHLC Index Columns (Optional - For Query Performance)
-- ============================================================================
-- Note: These indexes are optional. They improve query performance when
-- filtering or sorting by OHLC index values, but add ~5% storage overhead.
-- Decision: SKIP for now - can add later if query patterns require them.
-- Reasoning: Primary access pattern is sequential time-series (already indexed on time)

-- Uncomment below if query performance requires OHLC index filtering:
/*
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
BEGIN
    FOREACH pair_name IN ARRAY pair_list
    LOOP
        RAISE NOTICE 'Creating index on m1_% high_index', pair_name;
        EXECUTE format('
            CREATE INDEX IF NOT EXISTS idx_m1_%I_high_index
            ON bqx.m1_%I(high_index);
        ', pair_name, pair_name);

        RAISE NOTICE 'Creating index on m1_% low_index', pair_name;
        EXECUTE format('
            CREATE INDEX IF NOT EXISTS idx_m1_%I_low_index
            ON bqx.m1_%I(low_index);
        ', pair_name, pair_name);

        RAISE NOTICE 'Creating index on m1_% open_index', pair_name;
        EXECUTE format('
            CREATE INDEX IF NOT EXISTS idx_m1_%I_open_index
            ON bqx.m1_%I(open_index);
        ', pair_name, pair_name);
    END LOOP;
END $$;
*/

COMMIT;

-- ============================================================================
-- Verification Query (Run After Commit)
-- ============================================================================

\echo ''
\echo '============================================================================'
\echo 'VERIFICATION: OHLC Index Columns Added'
\echo '============================================================================'
\echo ''

-- Check columns added to EURUSD (sample verification)
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'bqx'
  AND table_name = 'm1_eurusd'
  AND column_name IN ('high_index', 'low_index', 'open_index')
ORDER BY column_name;

\echo ''
\echo 'Expected: 3 rows (high_index, low_index, open_index) - DOUBLE PRECISION'
\echo ''

-- Count total OHLC index columns across all M1 tables
SELECT
    COUNT(*) as total_ohlc_index_columns,
    COUNT(*) / 3 as pairs_with_columns
FROM information_schema.columns
WHERE table_schema = 'bqx'
  AND table_name LIKE 'm1_%'
  AND column_name IN ('high_index', 'low_index', 'open_index');

\echo ''
\echo 'Expected: 84 total columns (28 pairs × 3 columns)'
\echo ''

-- ============================================================================
-- Next Steps
-- ============================================================================

\echo ''
\echo '============================================================================'
\echo 'SCHEMA ENHANCEMENT COMPLETE'
\echo '============================================================================'
\echo ''
\echo 'Status: OHLC index columns added to all 28 M1 tables'
\echo 'Columns: high_index, low_index, open_index (DOUBLE PRECISION)'
\echo 'Next: Run ohlc_index_backfill_worker.py to populate values'
\echo ''
\echo 'Backfill Command:'
\echo '  python3 scripts/backfill/ohlc_index_backfill_worker.py'
\echo ''
\echo 'Estimated Backfill Time: 2-3 hours (10.3M rows × 3 calculations)'
\echo 'CPU Impact: Low (10-15% CPU, sequential updates)'
\echo '============================================================================'
\echo ''
