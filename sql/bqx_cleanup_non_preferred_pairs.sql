-- ============================================================================
-- BQX AURORA DATABASE CLEANUP - NON-PREFERRED FOREX PAIRS
-- ============================================================================
-- Date: 2025-11-08
-- Database: bqx (Trillium Aurora Cluster)
-- Cluster: trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com
--
-- Purpose: Remove 17 non-preferred forex pairs (SGD, HKD, SEK)
-- Tables to drop: 21 tables (all empty, 0 bytes)
-- Risk Level: LOW (all tables empty, no dependencies)
--
-- IMPORTANT: Create Aurora snapshot before execution!
-- aws rds create-db-cluster-snapshot \
--   --db-cluster-identifier trillium-bqx-cluster \
--   --db-cluster-snapshot-identifier trillium-bqx-pre-cleanup-20251108
-- ============================================================================

-- Start transaction (allows rollback if needed)
BEGIN;

-- Set client encoding
SET client_encoding = 'UTF8';

-- Display start time
\echo '============================================================================'
\echo 'BQX FOREX PAIR CLEANUP - EXECUTION STARTED'
\echo '============================================================================'
SELECT 'Start time: ' || NOW()::TEXT as execution_log;
\echo ''

-- ============================================================================
-- PRE-FLIGHT VERIFICATION
-- ============================================================================

\echo 'PRE-FLIGHT CHECK 1: Verify preferred pairs exist...'
SELECT
    CASE
        WHEN COUNT(*) = 28 THEN '✅ PASS: All 28 preferred m1 tables exist'
        ELSE '❌ FAIL: Expected 28 preferred m1 tables, found ' || COUNT(*)
    END as verification_result
FROM pg_tables
WHERE schemaname = 'bqx'
  AND tablename ~ '^m1_(audcad|audchf|audjpy|audnzd|audusd|cadchf|cadjpy|chfjpy|euraud|eurcad|eurchf|eurgbp|eurjpy|eurnzd|eurusd|gbpaud|gbpcad|gbpchf|gbpjpy|gbpnzd|gbpusd|nzdcad|nzdchf|nzdjpy|nzdusd|usdcad|usdchf|usdjpy)$';

\echo ''
\echo 'PRE-FLIGHT CHECK 2: Verify non-preferred tables are empty...'
SELECT
    CASE
        WHEN COUNT(*) = 0 THEN '✅ PASS: All non-preferred tables are empty (0 bytes)'
        ELSE '❌ FAIL: ' || COUNT(*) || ' non-preferred tables have data (STOP IMMEDIATELY!)'
    END as verification_result
FROM pg_tables
WHERE schemaname = 'bqx'
  AND (
    tablename ~ '^m1_(audhkd|audsgd|cadhkd|cadsgd|chfhkd|eurhkd|eursgd|gbphkd|gbpsgd|hkdjpy|nzdhkd|nzdsgd|sgdchf|sgdhkd|sgdjpy|usdsek|usdsgd)$' OR
    tablename ~ '^reg_(usdsek|usdsgd)$' OR
    tablename ~ '^fwd_(usdsek|usdsgd)$'
  )
  AND pg_total_relation_size('bqx.'||tablename) > 0;

\echo ''
\echo 'PRE-FLIGHT CHECK 3: Verify no foreign key dependencies...'
SELECT
    CASE
        WHEN COUNT(*) = 0 THEN '✅ PASS: No foreign key constraints to break'
        ELSE '❌ FAIL: ' || COUNT(*) || ' foreign key constraints found (STOP IMMEDIATELY!)'
    END as verification_result
FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY'
  AND table_schema = 'bqx'
  AND (
    table_name ~ '^m1_(audhkd|audsgd|cadhkd|cadsgd|chfhkd|eurhkd|eursgd|gbphkd|gbpsgd|hkdjpy|nzdhkd|nzdsgd|sgdchf|sgdhkd|sgdjpy|usdsek|usdsgd)$' OR
    table_name ~ '^reg_(usdsek|usdsgd)$' OR
    table_name ~ '^fwd_(usdsek|usdsgd)$'
  );

\echo ''
\echo '============================================================================'
\echo 'PRE-FLIGHT CHECKS COMPLETE - Review results above before proceeding'
\echo '============================================================================'
\echo ''
\echo 'If all checks passed (✅), you may proceed with cleanup.'
\echo 'If any check failed (❌), execute ROLLBACK; immediately!'
\echo ''
\echo 'To proceed: Continue with script execution'
\echo 'To abort:   Execute ROLLBACK; now'
\echo ''
\echo 'Waiting 5 seconds before cleanup begins...'
SELECT pg_sleep(5);
\echo ''

-- ============================================================================
-- STEP 1: Drop M1 tables for SGD pairs (9 tables)
-- ============================================================================

\echo '============================================================================'
\echo 'STEP 1: Dropping M1 tables for SGD pairs (9 tables)...'
\echo '============================================================================'

DROP TABLE IF EXISTS bqx.m1_audsgd CASCADE;
\echo 'Dropped: bqx.m1_audsgd'

DROP TABLE IF EXISTS bqx.m1_cadsgd CASCADE;
\echo 'Dropped: bqx.m1_cadsgd'

DROP TABLE IF EXISTS bqx.m1_eursgd CASCADE;
\echo 'Dropped: bqx.m1_eursgd'

DROP TABLE IF EXISTS bqx.m1_gbpsgd CASCADE;
\echo 'Dropped: bqx.m1_gbpsgd'

DROP TABLE IF EXISTS bqx.m1_nzdsgd CASCADE;
\echo 'Dropped: bqx.m1_nzdsgd'

DROP TABLE IF EXISTS bqx.m1_sgdchf CASCADE;
\echo 'Dropped: bqx.m1_sgdchf'

DROP TABLE IF EXISTS bqx.m1_sgdhkd CASCADE;
\echo 'Dropped: bqx.m1_sgdhkd'

DROP TABLE IF EXISTS bqx.m1_sgdjpy CASCADE;
\echo 'Dropped: bqx.m1_sgdjpy'

DROP TABLE IF EXISTS bqx.m1_usdsgd CASCADE;
\echo 'Dropped: bqx.m1_usdsgd'

\echo 'SGD pairs cleanup complete (9 m1 tables dropped)'
\echo ''

-- ============================================================================
-- STEP 2: Drop M1 tables for HKD pairs (7 tables)
-- ============================================================================

\echo '============================================================================'
\echo 'STEP 2: Dropping M1 tables for HKD pairs (7 tables)...'
\echo '============================================================================'

DROP TABLE IF EXISTS bqx.m1_audhkd CASCADE;
\echo 'Dropped: bqx.m1_audhkd'

DROP TABLE IF EXISTS bqx.m1_cadhkd CASCADE;
\echo 'Dropped: bqx.m1_cadhkd'

DROP TABLE IF EXISTS bqx.m1_chfhkd CASCADE;
\echo 'Dropped: bqx.m1_chfhkd'

DROP TABLE IF EXISTS bqx.m1_eurhkd CASCADE;
\echo 'Dropped: bqx.m1_eurhkd'

DROP TABLE IF EXISTS bqx.m1_gbphkd CASCADE;
\echo 'Dropped: bqx.m1_gbphkd'

DROP TABLE IF EXISTS bqx.m1_hkdjpy CASCADE;
\echo 'Dropped: bqx.m1_hkdjpy'

DROP TABLE IF EXISTS bqx.m1_nzdhkd CASCADE;
\echo 'Dropped: bqx.m1_nzdhkd'

\echo 'HKD pairs cleanup complete (7 m1 tables dropped)'
\echo ''

-- ============================================================================
-- STEP 3: Drop M1 tables for SEK pairs (1 table)
-- ============================================================================

\echo '============================================================================'
\echo 'STEP 3: Dropping M1 tables for SEK pairs (1 table)...'
\echo '============================================================================'

DROP TABLE IF EXISTS bqx.m1_usdsek CASCADE;
\echo 'Dropped: bqx.m1_usdsek'

\echo 'SEK pairs cleanup complete (1 m1 table dropped)'
\echo ''

-- ============================================================================
-- STEP 4: Drop regression and forward tables (usdsek, usdsgd)
-- ============================================================================

\echo '============================================================================'
\echo 'STEP 4: Dropping regression and forward tables (4 tables)...'
\echo '============================================================================'

DROP TABLE IF EXISTS bqx.reg_usdsek CASCADE;
\echo 'Dropped: bqx.reg_usdsek'

DROP TABLE IF EXISTS bqx.fwd_usdsek CASCADE;
\echo 'Dropped: bqx.fwd_usdsek'

DROP TABLE IF EXISTS bqx.reg_usdsgd CASCADE;
\echo 'Dropped: bqx.reg_usdsgd'

DROP TABLE IF EXISTS bqx.fwd_usdsgd CASCADE;
\echo 'Dropped: bqx.fwd_usdsgd'

\echo 'Regression/forward tables cleanup complete (4 tables dropped)'
\echo ''

-- ============================================================================
-- POST-CLEANUP VERIFICATION
-- ============================================================================

\echo '============================================================================'
\echo 'POST-CLEANUP VERIFICATION'
\echo '============================================================================'

\echo 'VERIFICATION 1: Confirm non-preferred tables are gone...'
SELECT
    CASE
        WHEN COUNT(*) = 0 THEN '✅ PASS: All 21 non-preferred tables successfully dropped'
        ELSE '❌ FAIL: ' || COUNT(*) || ' non-preferred tables still exist (ROLLBACK!)'
    END as verification_result,
    COUNT(*) as remaining_tables
FROM pg_tables
WHERE schemaname = 'bqx'
  AND (
    tablename ~ '^m1_(audhkd|audsgd|cadhkd|cadsgd|chfhkd|eurhkd|eursgd|gbphkd|gbpsgd|hkdjpy|nzdhkd|nzdsgd|sgdchf|sgdhkd|sgdjpy|usdsek|usdsgd)$' OR
    tablename ~ '^reg_(usdsek|usdsgd)$' OR
    tablename ~ '^fwd_(usdsek|usdsgd)$'
  );

\echo ''
\echo 'VERIFICATION 2: Confirm all 28 preferred pairs still exist...'
SELECT
    CASE
        WHEN COUNT(*) = 28 THEN '✅ PASS: All 28 preferred m1 tables intact'
        ELSE '❌ FAIL: Expected 28 preferred m1 tables, found ' || COUNT(*) || ' (ROLLBACK!)'
    END as verification_result,
    COUNT(*) as preferred_tables
FROM pg_tables
WHERE schemaname = 'bqx'
  AND tablename ~ '^m1_(audcad|audchf|audjpy|audnzd|audusd|cadchf|cadjpy|chfjpy|euraud|eurcad|eurchf|eurgbp|eurjpy|eurnzd|eurusd|gbpaud|gbpcad|gbpchf|gbpjpy|gbpnzd|gbpusd|nzdcad|nzdchf|nzdjpy|nzdusd|usdcad|usdchf|usdjpy)$';

\echo ''
\echo 'VERIFICATION 3: Count total tables in bqx schema...'
SELECT
    'Total tables in bqx schema: ' || COUNT(*) as status,
    '(expected: 4,588 = 4,609 - 21)' as note
FROM pg_tables
WHERE schemaname = 'bqx';

\echo ''
\echo '============================================================================'
\echo 'CLEANUP EXECUTION COMPLETE'
\echo '============================================================================'
SELECT 'End time: ' || NOW()::TEXT as execution_log;
\echo ''
\echo 'Transaction status: UNCOMMITTED (awaiting manual decision)'
\echo ''
\echo '============================================================================'
\echo 'NEXT STEPS:'
\echo '============================================================================'
\echo '1. Review all verification results above'
\echo '2. Confirm all checks show ✅ PASS'
\echo '3. If all verifications passed, execute: COMMIT;'
\echo '4. If any verification failed, execute: ROLLBACK;'
\echo ''
\echo 'To commit changes:   COMMIT;'
\echo 'To rollback changes: ROLLBACK;'
\echo '============================================================================'

-- DO NOT AUTO-COMMIT - Require manual review and decision
-- User must execute COMMIT; or ROLLBACK; manually
