-- ============================================================================
-- Track 2 (Regression Features) - Data Validation Queries
-- ============================================================================
-- Comprehensive validation suite to verify Track 2 completion and data quality
-- Run these queries after Track 2 reaches 100% to ensure data integrity
-- ============================================================================

\echo '============================================================================'
\echo 'TRACK 2 VALIDATION REPORT'
\echo '============================================================================'
\echo ''

-- ============================================================================
-- 1. PARTITION COMPLETENESS CHECK
-- ============================================================================

\echo '1. PARTITION COMPLETENESS'
\echo '------------------------'

-- Count reg_rate partitions
SELECT
    'reg_rate' as table_type,
    COUNT(*) as total_partitions,
    336 as expected_partitions,
    CASE
        WHEN COUNT(*) = 336 THEN '✅ PASS'
        ELSE '❌ FAIL - Missing ' || (336 - COUNT(*))::TEXT || ' partitions'
    END as status
FROM pg_tables
WHERE schemaname = 'bqx'
  AND tablename LIKE 'reg_rate_%'
  AND tablename ~ '_[0-9]{4}_[0-9]{2}$';

-- Count reg_bqx partitions
SELECT
    'reg_bqx' as table_type,
    COUNT(*) as total_partitions,
    336 as expected_partitions,
    CASE
        WHEN COUNT(*) = 336 THEN '✅ PASS'
        ELSE '❌ FAIL - Missing ' || (336 - COUNT(*))::TEXT || ' partitions'
    END as status
FROM pg_tables
WHERE schemaname = 'bqx'
  AND tablename LIKE 'reg_bqx_%'
  AND tablename ~ '_[0-9]{4}_[0-9]{2}$';

\echo ''

-- ============================================================================
-- 2. ROW COUNT VALIDATION
-- ============================================================================

\echo '2. ROW COUNT VALIDATION'
\echo '-----------------------'

-- Check total row counts across all partitions
WITH partition_counts AS (
    SELECT
        schemaname,
        relname as table_name,
        n_live_tup as row_count
    FROM pg_stat_user_tables
    WHERE schemaname = 'bqx'
      AND (relname LIKE 'reg_rate_%' OR relname LIKE 'reg_bqx_%')
      AND relname ~ '_[0-9]{4}_[0-9]{2}$'
)
SELECT
    CASE
        WHEN table_name LIKE 'reg_rate_%' THEN 'reg_rate'
        ELSE 'reg_bqx'
    END as table_type,
    COUNT(*) as total_partitions,
    SUM(row_count) as total_rows,
    AVG(row_count)::BIGINT as avg_rows_per_partition,
    MIN(row_count) as min_rows,
    MAX(row_count) as max_rows,
    CASE
        WHEN SUM(row_count) > 0 THEN '✅ PASS'
        ELSE '❌ FAIL - No data'
    END as status
FROM partition_counts
GROUP BY
    CASE
        WHEN table_name LIKE 'reg_rate_%' THEN 'reg_rate'
        ELSE 'reg_bqx'
    END;

\echo ''

-- ============================================================================
-- 3. DATA COMPLETENESS BY PAIR
-- ============================================================================

\echo '3. DATA COMPLETENESS BY PAIR'
\echo '-----------------------------'

-- Check row counts for each pair
WITH pair_stats AS (
    SELECT
        SUBSTRING(relname FROM 'reg_rate_(.*)_[0-9]{4}_[0-9]{2}$') as pair,
        SUM(n_live_tup) as total_rows,
        COUNT(*) as partition_count
    FROM pg_stat_user_tables
    WHERE schemaname = 'bqx'
      AND relname LIKE 'reg_rate_%'
      AND relname ~ '_[0-9]{4}_[0-9]{2}$'
    GROUP BY SUBSTRING(relname FROM 'reg_rate_(.*)_[0-9]{4}_[0-9]{2}$')
)
SELECT
    pair,
    total_rows,
    partition_count,
    CASE
        WHEN partition_count = 12 THEN '✅ All 12 months'
        ELSE '⚠️  ' || (12 - partition_count)::TEXT || ' missing'
    END as month_coverage,
    CASE
        WHEN total_rows > 100000 THEN '✅ PASS'
        WHEN total_rows > 0 THEN '⚠️  LOW DATA'
        ELSE '❌ FAIL'
    END as data_status
FROM pair_stats
ORDER BY pair;

\echo ''

-- ============================================================================
-- 4. NULL VALUE CHECK
-- ============================================================================

\echo '4. NULL VALUE CHECK (Sample: EURUSD Jul 2024)'
\echo '----------------------------------------------'

-- Check for NULL values in key columns (sample partition)
SELECT
    'ts_utc' as column_name,
    COUNT(*) FILTER (WHERE ts_utc IS NULL) as null_count,
    COUNT(*) as total_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE ts_utc IS NULL) / COUNT(*), 2) as null_pct
FROM bqx.reg_rate_eurusd_2024_07
UNION ALL
SELECT 'w20_a2', COUNT(*) FILTER (WHERE w20_a2 IS NULL), COUNT(*),
    ROUND(100.0 * COUNT(*) FILTER (WHERE w20_a2 IS NULL) / COUNT(*), 2)
FROM bqx.reg_rate_eurusd_2024_07
UNION ALL
SELECT 'w20_r2', COUNT(*) FILTER (WHERE w20_r2 IS NULL), COUNT(*),
    ROUND(100.0 * COUNT(*) FILTER (WHERE w20_r2 IS NULL) / COUNT(*), 2)
FROM bqx.reg_rate_eurusd_2024_07
UNION ALL
SELECT 'w60_prediction', COUNT(*) FILTER (WHERE w60_prediction IS NULL), COUNT(*),
    ROUND(100.0 * COUNT(*) FILTER (WHERE w60_prediction IS NULL) / COUNT(*), 2)
FROM bqx.reg_rate_eurusd_2024_07
UNION ALL
SELECT 'agg_curvature', COUNT(*) FILTER (WHERE agg_curvature IS NULL), COUNT(*),
    ROUND(100.0 * COUNT(*) FILTER (WHERE agg_curvature IS NULL) / COUNT(*), 2)
FROM bqx.reg_rate_eurusd_2024_07;

\echo ''

-- ============================================================================
-- 5. NaT VALUE CHECK (Critical Bug Verification)
-- ============================================================================

\echo '5. NaT VALUE CHECK (Verify Bug Fix)'
\echo '------------------------------------'

-- Check for string 'NaT' in timestamp columns (should be 0)
WITH nat_check AS (
    SELECT
        'reg_rate' as table_type,
        COUNT(*) FILTER (WHERE ts_utc::TEXT = 'NaT') as nat_count
    FROM bqx.reg_rate_eurusd_2024_07
    UNION ALL
    SELECT
        'reg_bqx' as table_type,
        COUNT(*) FILTER (WHERE ts_utc::TEXT = 'NaT') as nat_count
    FROM bqx.reg_bqx_eurusd_2024_07
)
SELECT
    table_type,
    nat_count,
    CASE
        WHEN nat_count = 0 THEN '✅ PASS - No NaT values'
        ELSE '❌ FAIL - NaT bug still present!'
    END as status
FROM nat_check;

\echo ''

-- ============================================================================
-- 6. FEATURE STATISTICS (Sample: w20 window)
-- ============================================================================

\echo '6. FEATURE STATISTICS (Sample: w20 rate_index features)'
\echo '--------------------------------------------------------'

SELECT
    'w20_a2' as feature,
    ROUND(AVG(w20_a2)::NUMERIC, 6) as mean,
    ROUND(STDDEV(w20_a2)::NUMERIC, 6) as stddev,
    ROUND(MIN(w20_a2)::NUMERIC, 6) as min,
    ROUND(MAX(w20_a2)::NUMERIC, 6) as max
FROM bqx.reg_rate_eurusd_2024_07
WHERE w20_a2 IS NOT NULL
UNION ALL
SELECT
    'w20_r2',
    ROUND(AVG(w20_r2)::NUMERIC, 6),
    ROUND(STDDEV(w20_r2)::NUMERIC, 6),
    ROUND(MIN(w20_r2)::NUMERIC, 6),
    ROUND(MAX(w20_r2)::NUMERIC, 6)
FROM bqx.reg_rate_eurusd_2024_07
WHERE w20_r2 IS NOT NULL
UNION ALL
SELECT
    'w20_rmse',
    ROUND(AVG(w20_rmse)::NUMERIC, 6),
    ROUND(STDDEV(w20_rmse)::NUMERIC, 6),
    ROUND(MIN(w20_rmse)::NUMERIC, 6),
    ROUND(MAX(w20_rmse)::NUMERIC, 6)
FROM bqx.reg_rate_eurusd_2024_07
WHERE w20_rmse IS NOT NULL;

\echo ''

-- ============================================================================
-- 7. TEMPORAL COVERAGE CHECK
-- ============================================================================

\echo '7. TEMPORAL COVERAGE (Jul 2024 - Jun 2025)'
\echo '-------------------------------------------'

-- Check date range coverage for each pair
WITH date_coverage AS (
    SELECT
        'EURUSD' as pair,
        MIN(ts_utc) as earliest,
        MAX(ts_utc) as latest,
        COUNT(DISTINCT ts_utc::DATE) as unique_dates
    FROM bqx.reg_rate_eurusd_2024_07
    UNION ALL
    SELECT
        'EURUSD (Aug)',
        MIN(ts_utc),
        MAX(ts_utc),
        COUNT(DISTINCT ts_utc::DATE)
    FROM bqx.reg_rate_eurusd_2024_08
    UNION ALL
    SELECT
        'EURUSD (Sep)',
        MIN(ts_utc),
        MAX(ts_utc),
        COUNT(DISTINCT ts_utc::DATE)
    FROM bqx.reg_rate_eurusd_2024_09
)
SELECT
    pair,
    earliest::DATE as start_date,
    latest::DATE as end_date,
    unique_dates as days_with_data,
    CASE
        WHEN unique_dates >= 25 THEN '✅ PASS'
        WHEN unique_dates > 0 THEN '⚠️  PARTIAL'
        ELSE '❌ FAIL'
    END as coverage_status
FROM date_coverage;

\echo ''

-- ============================================================================
-- 8. CROSS-TABLE CONSISTENCY CHECK
-- ============================================================================

\echo '8. CROSS-TABLE CONSISTENCY (reg_rate vs reg_bqx)'
\echo '-------------------------------------------------'

-- Ensure same timestamps in both tables
WITH timestamp_comparison AS (
    SELECT
        COUNT(DISTINCT r.ts_utc) as rate_timestamps,
        COUNT(DISTINCT b.ts_utc) as bqx_timestamps,
        COUNT(DISTINCT r.ts_utc) FILTER (WHERE b.ts_utc IS NOT NULL) as matching_timestamps
    FROM bqx.reg_rate_eurusd_2024_07 r
    FULL OUTER JOIN bqx.reg_bqx_eurusd_2024_07 b USING (ts_utc)
)
SELECT
    rate_timestamps,
    bqx_timestamps,
    matching_timestamps,
    CASE
        WHEN rate_timestamps = bqx_timestamps
         AND rate_timestamps = matching_timestamps THEN '✅ PASS'
        ELSE '⚠️  MISMATCH'
    END as consistency_status
FROM timestamp_comparison;

\echo ''

-- ============================================================================
-- 9. OUTLIER DETECTION
-- ============================================================================

\echo '9. OUTLIER DETECTION (R² values)'
\echo '---------------------------------'

-- Check for invalid R² values (should be 0-1)
SELECT
    'w20_r2' as feature,
    COUNT(*) FILTER (WHERE w20_r2 < 0 OR w20_r2 > 1) as invalid_count,
    COUNT(*) as total_count,
    CASE
        WHEN COUNT(*) FILTER (WHERE w20_r2 < 0 OR w20_r2 > 1) = 0 THEN '✅ PASS'
        ELSE '⚠️  ' || COUNT(*) FILTER (WHERE w20_r2 < 0 OR w20_r2 > 1)::TEXT || ' outliers'
    END as status
FROM bqx.reg_rate_eurusd_2024_07
WHERE w20_r2 IS NOT NULL
UNION ALL
SELECT
    'w30_r2',
    COUNT(*) FILTER (WHERE w30_r2 < 0 OR w30_r2 > 1),
    COUNT(*),
    CASE
        WHEN COUNT(*) FILTER (WHERE w30_r2 < 0 OR w30_r2 > 1) = 0 THEN '✅ PASS'
        ELSE '⚠️  ' || COUNT(*) FILTER (WHERE w30_r2 < 0 OR w30_r2 > 1)::TEXT || ' outliers'
    END
FROM bqx.reg_rate_eurusd_2024_07
WHERE w30_r2 IS NOT NULL
UNION ALL
SELECT
    'w60_r2',
    COUNT(*) FILTER (WHERE w60_r2 < 0 OR w60_r2 > 1),
    COUNT(*),
    CASE
        WHEN COUNT(*) FILTER (WHERE w60_r2 < 0 OR w60_r2 > 1) = 0 THEN '✅ PASS'
        ELSE '⚠️  ' || COUNT(*) FILTER (WHERE w60_r2 < 0 OR w60_r2 > 1)::TEXT || ' outliers'
    END
FROM bqx.reg_rate_eurusd_2024_07
WHERE w60_r2 IS NOT NULL;

\echo ''

-- ============================================================================
-- 10. FINAL SUMMARY
-- ============================================================================

\echo '10. FINAL SUMMARY'
\echo '-----------------'

WITH summary AS (
    SELECT
        (SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'bqx' AND tablename LIKE 'reg_rate_%' AND tablename ~ '_[0-9]{4}_[0-9]{2}$') as rate_partitions,
        (SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'bqx' AND tablename LIKE 'reg_bqx_%' AND tablename ~ '_[0-9]{4}_[0-9]{2}$') as bqx_partitions,
        (SELECT SUM(n_live_tup) FROM pg_stat_user_tables WHERE schemaname = 'bqx' AND relname LIKE 'reg_rate_%') as total_rate_rows,
        (SELECT SUM(n_live_tup) FROM pg_stat_user_tables WHERE schemaname = 'bqx' AND relname LIKE 'reg_bqx_%') as total_bqx_rows
)
SELECT
    'Track 2 Status' as metric,
    CASE
        WHEN rate_partitions = 336 AND bqx_partitions = 336
         AND total_rate_rows > 0 AND total_bqx_rows > 0
        THEN '✅ COMPLETE'
        ELSE '⚠️  INCOMPLETE'
    END as status,
    rate_partitions || '/336 rate partitions' as detail_1,
    bqx_partitions || '/336 bqx partitions' as detail_2,
    total_rate_rows::TEXT || ' total rate rows' as detail_3,
    total_bqx_rows::TEXT || ' total bqx rows' as detail_4
FROM summary;

\echo ''
\echo '============================================================================'
\echo 'VALIDATION COMPLETE'
\echo '============================================================================'
