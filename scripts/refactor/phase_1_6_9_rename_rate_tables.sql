-- Phase 1.6.9: Rename Rate-Centric Feature Tables
-- Rename existing *_features_* tables to *_rate_* naming convention
-- Estimated Time: 30-45 minutes
-- Author: BQX ML Team
-- Date: 2025-11-12

\timing on
\set ON_ERROR_STOP on

-- Begin transaction for safety
BEGIN;

-- ============================================================================
-- STATISTICS FEATURES → STATISTICS RATE
-- ============================================================================

DO $$
DECLARE
    pair_name TEXT;
    partition_suffix TEXT;
    old_name TEXT;
    new_name TEXT;
    rename_count INT := 0;
BEGIN
    RAISE NOTICE '=== Renaming Statistics Features → Statistics Rate ===';

    -- Get all statistics_features partitions
    FOR old_name, new_name IN
        SELECT
            tablename AS old_name,
            REPLACE(tablename, 'statistics_features_', 'statistics_rate_') AS new_name
        FROM pg_tables
        WHERE schemaname = 'bqx'
          AND tablename LIKE 'statistics_features_%'
        ORDER BY tablename
    LOOP
        -- Rename table
        EXECUTE format('ALTER TABLE IF EXISTS bqx.%I RENAME TO %I', old_name, new_name);
        rename_count := rename_count + 1;

        IF rename_count % 10 = 0 THEN
            RAISE NOTICE 'Renamed % statistics tables...', rename_count;
        END IF;
    END LOOP;

    RAISE NOTICE '✅ Renamed % statistics tables total', rename_count;
END $$;

-- ============================================================================
-- BOLLINGER FEATURES → BOLLINGER RATE
-- ============================================================================

DO $$
DECLARE
    old_name TEXT;
    new_name TEXT;
    rename_count INT := 0;
BEGIN
    RAISE NOTICE '=== Renaming Bollinger Features → Bollinger Rate ===';

    FOR old_name, new_name IN
        SELECT
            tablename AS old_name,
            REPLACE(tablename, 'bollinger_features_', 'bollinger_rate_') AS new_name
        FROM pg_tables
        WHERE schemaname = 'bqx'
          AND tablename LIKE 'bollinger_features_%'
        ORDER BY tablename
    LOOP
        EXECUTE format('ALTER TABLE IF EXISTS bqx.%I RENAME TO %I', old_name, new_name);
        rename_count := rename_count + 1;

        IF rename_count % 10 = 0 THEN
            RAISE NOTICE 'Renamed % bollinger tables...', rename_count;
        END IF;
    END LOOP;

    RAISE NOTICE '✅ Renamed % bollinger tables total', rename_count;
END $$;

-- ============================================================================
-- FIBONACCI FEATURES → FIBONACCI RATE
-- ============================================================================

DO $$
DECLARE
    old_name TEXT;
    new_name TEXT;
    rename_count INT := 0;
BEGIN
    RAISE NOTICE '=== Renaming Fibonacci Features → Fibonacci Rate ===';

    FOR old_name, new_name IN
        SELECT
            tablename AS old_name,
            REPLACE(tablename, 'fibonacci_features_', 'fibonacci_rate_') AS new_name
        FROM pg_tables
        WHERE schemaname = 'bqx'
          AND tablename LIKE 'fibonacci_features_%'
        ORDER BY tablename
    LOOP
        EXECUTE format('ALTER TABLE IF EXISTS bqx.%I RENAME TO %I', old_name, new_name);
        rename_count := rename_count + 1;

        IF rename_count % 10 = 0 THEN
            RAISE NOTICE 'Renamed % fibonacci tables...', rename_count;
        END IF;
    END LOOP;

    RAISE NOTICE '✅ Renamed % fibonacci tables total', rename_count;
END $$;

-- ============================================================================
-- CORRELATION FEATURES → CORRELATION RATE
-- ============================================================================

DO $$
DECLARE
    old_name TEXT;
    new_name TEXT;
    rename_count INT := 0;
BEGIN
    RAISE NOTICE '=== Renaming Correlation Features → Correlation Rate ===';

    FOR old_name, new_name IN
        SELECT
            tablename AS old_name,
            REPLACE(tablename, 'correlation_features_', 'correlation_rate_') AS new_name
        FROM pg_tables
        WHERE schemaname = 'bqx'
          AND tablename LIKE 'correlation_features_%'
        ORDER BY tablename
    LOOP
        EXECUTE format('ALTER TABLE IF EXISTS bqx.%I RENAME TO %I', old_name, new_name);
        rename_count := rename_count + 1;

        IF rename_count % 10 = 0 THEN
            RAISE NOTICE 'Renamed % correlation tables...', rename_count;
        END IF;
    END LOOP;

    RAISE NOTICE '✅ Renamed % correlation tables total', rename_count;
END $$;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Count renamed tables
SELECT
    'Statistics Rate' AS table_type,
    COUNT(*) AS table_count,
    SUM(n_live_tup) AS total_rows
FROM pg_stat_user_tables
WHERE schemaname = 'bqx'
  AND relname LIKE 'statistics_rate_%'

UNION ALL

SELECT
    'Bollinger Rate' AS table_type,
    COUNT(*),
    SUM(n_live_tup)
FROM pg_stat_user_tables
WHERE schemaname = 'bqx'
  AND relname LIKE 'bollinger_rate_%'

UNION ALL

SELECT
    'Fibonacci Rate' AS table_type,
    COUNT(*),
    SUM(n_live_tup)
FROM pg_stat_user_tables
WHERE schemaname = 'bqx'
  AND relname LIKE 'fibonacci_rate_%'

UNION ALL

SELECT
    'Correlation Rate' AS table_type,
    COUNT(*),
    SUM(n_live_tup)
FROM pg_stat_user_tables
WHERE schemaname = 'bqx'
  AND relname LIKE 'correlation_rate_%'

ORDER BY table_type;

-- Check for any remaining old-named tables (should be 0)
SELECT
    COUNT(*) AS remaining_old_tables,
    STRING_AGG(tablename, ', ') AS table_names
FROM pg_tables
WHERE schemaname = 'bqx'
  AND (
    tablename LIKE 'statistics_features_%'
    OR tablename LIKE 'bollinger_features_%'
    OR tablename LIKE 'fibonacci_features_%'
    OR tablename LIKE 'correlation_features_%'
  );

-- Expected results:
-- - statistics_rate: 364 tables, ~10.3M rows
-- - bollinger_rate: 364 tables, ~10.3M rows
-- - fibonacci_rate: 364 tables, ~10.2M rows
-- - correlation_rate: 364 tables, ~0 rows
-- - remaining_old_tables: 0

COMMIT;

\echo '✅ Phase 1.6.9 Complete: All rate-centric tables renamed successfully'
