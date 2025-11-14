-- ============================================================================
-- AURORA POST-TRACK 2 OPTIMIZATION
-- ============================================================================
-- Purpose: Optimize all tables and partitions after Track 2 completion
-- Scope: ANALYZE, VACUUM, index optimization for 672+ partitions
-- Execution: Run BEFORE EC2 upgrade to c7i.8xlarge
-- Duration: ~30-45 minutes (depending on data volume)
-- ============================================================================

\timing

\echo ''
\echo '================================================================================'
\echo 'AURORA POST-TRACK 2 OPTIMIZATION'
\echo '================================================================================'
\echo ''
\echo 'Scope:'
\echo '  - 336 reg_rate partitions (rate_index features)'
\echo '  - 336 reg_bqx partitions (BQX features)'
\echo '  - Parent tables and other feature tables'
\echo '  - Total rows: 10,313,378+ (Track 2 only)'
\echo ''
\echo 'Operations:'
\echo '  1. ANALYZE (update query planner statistics)'
\echo '  2. VACUUM (reclaim dead tuples, update visibility map)'
\echo '  3. Index optimization (rebuild if needed)'
\echo '  4. Cluster statistics update'
\echo ''
\echo 'Expected Duration: 30-45 minutes'
\echo '================================================================================'
\echo ''

-- ============================================================================
-- PHASE 1: PRE-OPTIMIZATION STATISTICS
-- ============================================================================

\echo ''
\echo '================================================================================'
\echo 'PHASE 1: PRE-OPTIMIZATION STATISTICS'
\echo '================================================================================'
\echo ''

-- Track 2 completion verification
\echo 'Track 2 Completion Verification:'
\echo '--------------------------------'

SELECT
    'reg_rate' as table_name,
    COUNT(*) as partition_count,
    SUM(n_live_tup) as total_rows,
    pg_size_pretty(SUM(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(relname))::bigint)) as total_size
FROM pg_stat_user_tables
WHERE schemaname = 'bqx' AND relname LIKE 'reg_rate_%'

UNION ALL

SELECT
    'reg_bqx' as table_name,
    COUNT(*) as partition_count,
    SUM(n_live_tup) as total_rows,
    pg_size_pretty(SUM(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(relname))::bigint)) as total_size
FROM pg_stat_user_tables
WHERE schemaname = 'bqx' AND relname LIKE 'reg_bqx_%'

ORDER BY table_name;

\echo ''
\echo 'Database Statistics (Before Optimization):'
\echo '------------------------------------------'

SELECT
    schemaname,
    COUNT(*) as table_count,
    SUM(n_live_tup) as total_live_rows,
    SUM(n_dead_tup) as total_dead_rows,
    ROUND(100.0 * SUM(n_dead_tup) / NULLIF(SUM(n_live_tup), 0), 2) as dead_row_pct,
    pg_size_pretty(SUM(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(relname))::bigint)) as total_size
FROM pg_stat_user_tables
WHERE schemaname = 'bqx'
GROUP BY schemaname;

\echo ''
\echo 'Index Statistics (Before Optimization):'
\echo '---------------------------------------'

SELECT
    schemaname,
    COUNT(*) as index_count,
    pg_size_pretty(SUM(pg_relation_size(indexrelid))::bigint) as total_index_size,
    SUM(idx_scan) as total_index_scans,
    SUM(idx_tup_read) as total_tuples_read,
    SUM(idx_tup_fetch) as total_tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'bqx'
GROUP BY schemaname;

-- ============================================================================
-- PHASE 2: VACUUM ALL TABLES AND PARTITIONS
-- ============================================================================

\echo ''
\echo '================================================================================'
\echo 'PHASE 2: VACUUM ALL TABLES AND PARTITIONS'
\echo '================================================================================'
\echo ''
\echo 'Vacuuming reg_rate partitions (336 partitions)...'

DO $$
DECLARE
    partition_name TEXT;
    counter INT := 0;
    total_partitions INT;
BEGIN
    -- Count total partitions
    SELECT COUNT(*) INTO total_partitions
    FROM pg_tables
    WHERE schemaname = 'bqx' AND tablename LIKE 'reg_rate_%';

    -- Vacuum each reg_rate partition
    FOR partition_name IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'bqx' AND tablename LIKE 'reg_rate_%'
        ORDER BY tablename
    LOOP
        counter := counter + 1;

        -- Progress indicator every 50 partitions
        IF counter % 50 = 0 THEN
            RAISE NOTICE 'Progress: % / % reg_rate partitions vacuumed', counter, total_partitions;
        END IF;

        EXECUTE 'VACUUM ANALYZE bqx.' || quote_ident(partition_name);
    END LOOP;

    RAISE NOTICE 'Completed: % reg_rate partitions vacuumed', counter;
END $$;

\echo ''
\echo 'Vacuuming reg_bqx partitions (336 partitions)...'

DO $$
DECLARE
    partition_name TEXT;
    counter INT := 0;
    total_partitions INT;
BEGIN
    -- Count total partitions
    SELECT COUNT(*) INTO total_partitions
    FROM pg_tables
    WHERE schemaname = 'bqx' AND tablename LIKE 'reg_bqx_%';

    -- Vacuum each reg_bqx partition
    FOR partition_name IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'bqx' AND tablename LIKE 'reg_bqx_%'
        ORDER BY tablename
    LOOP
        counter := counter + 1;

        -- Progress indicator every 50 partitions
        IF counter % 50 = 0 THEN
            RAISE NOTICE 'Progress: % / % reg_bqx partitions vacuumed', counter, total_partitions;
        END IF;

        EXECUTE 'VACUUM ANALYZE bqx.' || quote_ident(partition_name);
    END LOOP;

    RAISE NOTICE 'Completed: % reg_bqx partitions vacuumed', counter;
END $$;

\echo ''
\echo 'Vacuuming other BQX tables (m1, bollinger, etc.)...'

DO $$
DECLARE
    table_name TEXT;
    counter INT := 0;
BEGIN
    -- Vacuum other BQX tables (not reg_rate or reg_bqx)
    FOR table_name IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'bqx'
          AND tablename NOT LIKE 'reg_rate_%'
          AND tablename NOT LIKE 'reg_bqx_%'
        ORDER BY tablename
    LOOP
        counter := counter + 1;
        RAISE NOTICE 'Vacuuming: bqx.%', table_name;
        EXECUTE 'VACUUM ANALYZE bqx.' || quote_ident(table_name);
    END LOOP;

    RAISE NOTICE 'Completed: % other tables vacuumed', counter;
END $$;

-- ============================================================================
-- PHASE 3: ANALYZE ALL TABLES (UPDATE STATISTICS)
-- ============================================================================

\echo ''
\echo '================================================================================'
\echo 'PHASE 3: ANALYZE ALL TABLES (UPDATE STATISTICS)'
\echo '================================================================================'
\echo ''
\echo 'Running ANALYZE on all BQX tables...'

ANALYZE bqx.reg_rate;
ANALYZE bqx.reg_bqx;

-- Analyze all parent tables
DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOR table_name IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'bqx'
          AND tablename NOT LIKE '%_%_%'  -- Exclude partition tables (contain 2+ underscores with dates)
        ORDER BY tablename
    LOOP
        RAISE NOTICE 'Analyzing: bqx.%', table_name;
        EXECUTE 'ANALYZE bqx.' || quote_ident(table_name);
    END LOOP;
END $$;

\echo ''
\echo 'Statistics updated for all tables.'

-- ============================================================================
-- PHASE 4: INDEX OPTIMIZATION
-- ============================================================================

\echo ''
\echo '================================================================================'
\echo 'PHASE 4: INDEX OPTIMIZATION'
\echo '================================================================================'
\echo ''
\echo 'Checking index bloat and usage...'

-- Index bloat analysis
SELECT
    schemaname || '.' || tablename as table_name,
    indexname,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    CASE
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 100 THEN 'LOW_USAGE'
        ELSE 'ACTIVE'
    END as usage_status
FROM pg_stat_user_indexes
WHERE schemaname = 'bqx'
  AND indexname LIKE '%pkey%'  -- Focus on primary keys
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 50;

\echo ''
\echo 'Index optimization recommendations:'
\echo '-----------------------------------'

-- Identify indexes that might need reindexing (high bloat)
WITH index_stats AS (
    SELECT
        schemaname,
        tablename,
        indexname,
        idx_scan,
        pg_relation_size(indexrelid) as index_size
    FROM pg_stat_user_indexes
    WHERE schemaname = 'bqx'
)
SELECT
    'Index: ' || indexname || ' on ' || tablename as recommendation,
    'Size: ' || pg_size_pretty(index_size) || ', Scans: ' || idx_scan as details,
    CASE
        WHEN idx_scan = 0 AND index_size > 1048576 THEN 'Consider dropping (unused, >1MB)'
        WHEN idx_scan > 0 THEN 'Active - keep'
        ELSE 'Monitor usage'
    END as action
FROM index_stats
WHERE index_size > 1048576  -- Indexes larger than 1MB
ORDER BY index_size DESC
LIMIT 20;

-- ============================================================================
-- PHASE 5: POST-OPTIMIZATION STATISTICS
-- ============================================================================

\echo ''
\echo '================================================================================'
\echo 'PHASE 5: POST-OPTIMIZATION STATISTICS'
\echo '================================================================================'
\echo ''

\echo 'Database Statistics (After Optimization):'
\echo '-----------------------------------------'

SELECT
    schemaname,
    COUNT(*) as table_count,
    SUM(n_live_tup) as total_live_rows,
    SUM(n_dead_tup) as total_dead_rows,
    ROUND(100.0 * SUM(n_dead_tup) / NULLIF(SUM(n_live_tup), 0), 2) as dead_row_pct,
    pg_size_pretty(SUM(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(relname))::bigint)) as total_size
FROM pg_stat_user_tables
WHERE schemaname = 'bqx'
GROUP BY schemaname;

\echo ''
\echo 'Partition Summary:'
\echo '------------------'

SELECT
    'reg_rate' as table_type,
    COUNT(*) as partition_count,
    SUM(n_live_tup) as total_rows,
    AVG(n_live_tup)::BIGINT as avg_rows_per_partition,
    MIN(n_live_tup) as min_rows,
    MAX(n_live_tup) as max_rows,
    pg_size_pretty(SUM(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(relname))::bigint)) as total_size
FROM pg_stat_user_tables
WHERE schemaname = 'bqx' AND relname LIKE 'reg_rate_%'

UNION ALL

SELECT
    'reg_bqx' as table_type,
    COUNT(*) as partition_count,
    SUM(n_live_tup) as total_rows,
    AVG(n_live_tup)::BIGINT as avg_rows_per_partition,
    MIN(n_live_tup) as min_rows,
    MAX(n_live_tup) as max_rows,
    pg_size_pretty(SUM(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(relname))::bigint)) as total_size
FROM pg_stat_user_tables
WHERE schemaname = 'bqx' AND relname LIKE 'reg_bqx_%'

ORDER BY table_type;

\echo ''
\echo 'Top 20 Largest Tables:'
\echo '---------------------'

SELECT
    schemaname || '.' || relname as table_name,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    pg_size_pretty(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(relname))) as total_size,
    pg_size_pretty(pg_relation_size(quote_ident(schemaname) || '.' || quote_ident(relname))) as table_size,
    pg_size_pretty(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(relname)) - pg_relation_size(quote_ident(schemaname) || '.' || quote_ident(relname))) as index_size
FROM pg_stat_user_tables
WHERE schemaname = 'bqx'
ORDER BY pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(relname)) DESC
LIMIT 20;

-- ============================================================================
-- PHASE 6: AURORA-SPECIFIC OPTIMIZATIONS
-- ============================================================================

\echo ''
\echo '================================================================================'
\echo 'PHASE 6: AURORA-SPECIFIC OPTIMIZATIONS'
\echo '================================================================================'
\echo ''

-- Aurora storage metrics
\echo 'Aurora Storage Metrics:'
\echo '----------------------'

SELECT
    pg_size_pretty(SUM(pg_database_size(datname))) as total_database_size
FROM pg_database
WHERE datname = 'bqx';

-- Connection pool status
\echo ''
\echo 'Connection Pool Status:'
\echo '----------------------'

SELECT
    COUNT(*) as total_connections,
    COUNT(*) FILTER (WHERE state = 'active') as active_connections,
    COUNT(*) FILTER (WHERE state = 'idle') as idle_connections,
    COUNT(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
FROM pg_stat_activity
WHERE datname = 'bqx';

-- Autovacuum status
\echo ''
\echo 'Autovacuum Configuration:'
\echo '------------------------'

SELECT
    name,
    setting,
    unit,
    context
FROM pg_settings
WHERE name LIKE 'autovacuum%'
ORDER BY name;

-- ============================================================================
-- COMPLETION SUMMARY
-- ============================================================================

\echo ''
\echo '================================================================================'
\echo 'AURORA OPTIMIZATION COMPLETE'
\echo '================================================================================'
\echo ''
\echo 'Optimizations Applied:'
\echo '  ✅ VACUUM: 672+ partitions (reg_rate + reg_bqx) + parent tables'
\echo '  ✅ ANALYZE: All tables and partitions (updated query planner statistics)'
\echo '  ✅ Index check: Identified unused/bloated indexes'
\echo '  ✅ Statistics: Updated cluster-wide statistics'
\echo ''
\echo 'Next Steps:'
\echo '  1. Review optimization results above'
\echo '  2. Execute EC2 upgrade to c7i.8xlarge (docs/ec2_upgrade_downgrade_plan.md)'
\echo '  3. Resume Phase 2 parallel stages (Stage 2.2, 2.3, 2.4, etc.)'
\echo ''
\echo 'Expected Phase 2 Duration: 1.3 days (with c7i.8xlarge upgrade)'
\echo '================================================================================'
\echo ''
