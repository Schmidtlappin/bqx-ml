# BQX Aurora Database - Forex Pair Cleanup Plan

**Date**: 2025-11-08
**Database**: Trillium BQX Aurora Cluster
**Cluster**: trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com
**Database**: bqx
**Engine**: PostgreSQL 16.8 (Aurora Serverless v2)

---

## Executive Summary

### Objective
Remove all database objects (tables, indexes, constraints) related to **17 non-preferred forex pairs** that are not part of the user's preferred 28-pair list.

### Key Findings

| Metric | Value |
|--------|-------|
| **Total pairs in Aurora** | 45 pairs |
| **Preferred pairs** | 28 pairs |
| **Non-preferred pairs** | 17 pairs |
| **Tables to remove** | 21 tables |
| **Storage to reclaim** | 0 bytes (all tables empty) |
| **Row count** | 0 rows (all tables empty) |
| **Foreign key constraints** | 0 (no dependencies) |

### Risk Assessment

**Risk Level**: ✅ **LOW**

**Rationale**:
- All non-preferred pair tables are **empty** (0 bytes, 0 rows)
- No foreign key constraints to break
- No materialized views reference these pairs
- Clean separation from preferred 28 pairs
- All preferred pairs verified to exist

### Impact

**Positive Impacts**:
- ✅ Database schema clarity (only preferred pairs remain)
- ✅ Reduced maintenance overhead (fewer tables to manage)
- ✅ Improved query performance (smaller metadata catalogs)
- ✅ Alignment with codebase (matches bqx-db repository)

**No Negative Impacts**:
- ❌ No data loss (tables are already empty)
- ❌ No application breakage (pairs not used in ML pipeline)
- ❌ No storage reclamation (already 0 bytes)

---

## Analysis: Non-Preferred Pairs

### 17 Pairs to Remove (Grouped by Currency)

#### SGD (Singapore Dollar) - 9 pairs
```
1. audsgd  (AUD/SGD)
2. cadsgd  (CAD/SGD)
3. eursgd  (EUR/SGD)
4. gbpsgd  (GBP/SGD)
5. nzdsgd  (NZD/SGD)
6. sgdchf  (SGD/CHF)
7. sgdhkd  (SGD/HKD)
8. sgdjpy  (SGD/JPY)
9. usdsgd  (USD/SGD)
```

#### HKD (Hong Kong Dollar) - 7 pairs
```
1. audhkd  (AUD/HKD)
2. cadhkd  (CAD/HKD)
3. chfhkd  (CHF/HKD)
4. eurhkd  (EUR/HKD)
5. gbphkd  (GBP/HKD)
6. hkdjpy  (HKD/JPY)
7. nzdhkd  (NZD/HKD)
```

#### SEK (Swedish Krona) - 1 pair
```
1. usdsek  (USD/SEK)
```

### Why These Pairs Were Excluded

**Reason**: The user's ML system is designed for **28 specific pairs** based on:
- Liquidity requirements (major USD pairs + key crosses)
- Complete currency network (8 currencies, 7 pairs each)
- Data availability (Oanda API coverage)
- Trading relevance (24-hour session coverage)

**SGD, HKD, SEK pairs**:
- Lower liquidity vs major pairs
- Not part of the core 8-currency network (EUR, USD, GBP, JPY, AUD, CAD, CHF, NZD)
- Not used in the ML pipeline (bqx-db repository)
- Tables created but never populated

---

## Tables Inventory

### Complete List of Tables to Remove (21 tables)

| Pair | M1 Table | REG Table | FWD Table | Total |
|------|----------|-----------|-----------|-------|
| audhkd | ✅ m1_audhkd | ❌ | ❌ | 1 |
| audsgd | ✅ m1_audsgd | ❌ | ❌ | 1 |
| cadhkd | ✅ m1_cadhkd | ❌ | ❌ | 1 |
| cadsgd | ✅ m1_cadsgd | ❌ | ❌ | 1 |
| chfhkd | ✅ m1_chfhkd | ❌ | ❌ | 1 |
| eurhkd | ✅ m1_eurhkd | ❌ | ❌ | 1 |
| eursgd | ✅ m1_eursgd | ❌ | ❌ | 1 |
| gbphkd | ✅ m1_gbphkd | ❌ | ❌ | 1 |
| gbpsgd | ✅ m1_gbpsgd | ❌ | ❌ | 1 |
| hkdjpy | ✅ m1_hkdjpy | ❌ | ❌ | 1 |
| nzdhkd | ✅ m1_nzdhkd | ❌ | ❌ | 1 |
| nzdsgd | ✅ m1_nzdsgd | ❌ | ❌ | 1 |
| sgdchf | ✅ m1_sgdchf | ❌ | ❌ | 1 |
| sgdhkd | ✅ m1_sgdhkd | ❌ | ❌ | 1 |
| sgdjpy | ✅ m1_sgdjpy | ❌ | ❌ | 1 |
| usdsek | ✅ m1_usdsek | ✅ reg_usdsek | ✅ fwd_usdsek | 3 |
| usdsgd | ✅ m1_usdsgd | ✅ reg_usdsgd | ✅ fwd_usdsgd | 3 |

**Total**: 21 tables (15 m1 tables, 3 reg tables, 3 fwd tables)

### Notes

- **Most pairs** have only M1 tables (raw minute data)
- **usdsek and usdsgd** have full table sets (m1, reg, fwd)
- **No materialized views** exist for these pairs
- **All tables are empty** (0 bytes, 0 rows)

---

## Storage & Performance Impact

### Current State

| Metric | Value |
|--------|-------|
| Total tables (non-preferred) | 21 |
| Total storage | 0 bytes |
| Total rows | 0 rows |
| Index storage | 0 bytes |
| Toast storage | 0 bytes |

### Post-Cleanup Expected State

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Tables in bqx schema | 4,609 | 4,588 | -21 tables |
| Storage used | 2.485 TB | 2.485 TB | 0 bytes |
| Catalog size | ~15 MB | ~14.9 MB | -0.1 MB |

### Performance Benefits

**Metadata Catalog**:
- Smaller `pg_class` table (21 fewer entries)
- Faster query planning (fewer tables to scan in metadata)
- Reduced schema dump/restore time

**Maintenance**:
- Fewer tables to VACUUM/ANALYZE
- Simplified backup operations
- Cleaner schema for developers

---

## Safety Procedures

### Pre-Cleanup Verification

**1. Verify all preferred pairs exist:**
```sql
SELECT COUNT(DISTINCT pair_name) as preferred_count
FROM (
    SELECT SUBSTRING(tablename FROM '^m1_(.+)$') as pair_name
    FROM pg_tables
    WHERE schemaname = 'bqx'
      AND tablename ~ '^m1_(audcad|audchf|audjpy|audnzd|audusd|cadchf|cadjpy|chfjpy|euraud|eurcad|eurchf|eurgbp|eurjpy|eurnzd|eurusd|gbpaud|gbpcad|gbpchf|gbpjpy|gbpnzd|gbpusd|nzdcad|nzdchf|nzdjpy|nzdusd|usdcad|usdchf|usdjpy)$'
) sub;
-- Expected: 28
```

**2. Verify non-preferred tables are empty:**
```sql
SELECT
    tablename,
    pg_total_relation_size('bqx.'||tablename) as bytes
FROM pg_tables
WHERE schemaname = 'bqx'
  AND (
    tablename ~ '^m1_(audhkd|audsgd|cadhkd|cadsgd|chfhkd|eurhkd|eursgd|gbphkd|gbpsgd|hkdjpy|nzdhkd|nzdsgd|sgdchf|sgdhkd|sgdjpy|usdsek|usdsgd)$' OR
    tablename ~ '^reg_(usdsek|usdsgd)$' OR
    tablename ~ '^fwd_(usdsek|usdsgd)$'
  )
  AND pg_total_relation_size('bqx.'||tablename) > 0;
-- Expected: 0 rows (all should be 0 bytes)
```

**3. Check for dependencies:**
```sql
-- Check foreign keys
SELECT COUNT(*) as fk_count
FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY'
  AND table_schema = 'bqx'
  AND (
    table_name ~ '^m1_(audhkd|audsgd|cadhkd|cadsgd|chfhkd|eurhkd|eursgd|gbphkd|gbpsgd|hkdjpy|nzdhkd|nzdsgd|sgdchf|sgdhkd|sgdjpy|usdsek|usdsgd)$' OR
    table_name ~ '^reg_(usdsek|usdsgd)$' OR
    table_name ~ '^fwd_(usdsek|usdsgd)$'
  );
-- Expected: 0

-- Check views
SELECT COUNT(*) as view_count
FROM information_schema.views
WHERE table_schema = 'bqx'
  AND view_definition ~ '(audhkd|audsgd|cadhkd|cadsgd|chfhkd|eurhkd|eursgd|gbphkd|gbpsgd|hkdjpy|nzdhkd|nzdsgd|sgdchf|sgdhkd|sgdjpy|usdsek|usdsgd)';
-- Expected: 0
```

### Backup Strategy

**Option 1: Aurora Snapshot (Recommended)**
```bash
# Create cluster snapshot before cleanup
aws rds create-db-cluster-snapshot \
  --db-cluster-identifier trillium-bqx-cluster \
  --db-cluster-snapshot-identifier trillium-bqx-pre-cleanup-20251108 \
  --tags Key=Purpose,Value=PrePairCleanup Key=Date,Value=2025-11-08
```

**Option 2: pg_dump (Table-level backup)**
```bash
# Backup non-preferred tables (paranoid option, but they're empty)
export PGPASSWORD='BQX_Aurora_2025_Secure'
pg_dump -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres -d bqx \
  -t 'bqx.m1_audhkd' -t 'bqx.m1_audsgd' -t 'bqx.m1_cadhkd' \
  -t 'bqx.m1_cadsgd' -t 'bqx.m1_chfhkd' -t 'bqx.m1_eurhkd' \
  -t 'bqx.m1_eursgd' -t 'bqx.m1_gbphkd' -t 'bqx.m1_gbpsgd' \
  -t 'bqx.m1_hkdjpy' -t 'bqx.m1_nzdhkd' -t 'bqx.m1_nzdsgd' \
  -t 'bqx.m1_sgdchf' -t 'bqx.m1_sgdhkd' -t 'bqx.m1_sgdjpy' \
  -t 'bqx.m1_usdsek' -t 'bqx.reg_usdsek' -t 'bqx.fwd_usdsek' \
  -t 'bqx.m1_usdsgd' -t 'bqx.reg_usdsgd' -t 'bqx.fwd_usdsgd' \
  --schema-only \
  -f /tmp/bqx_non_preferred_pairs_schema_backup_20251108.sql
```

**Option 3: Schema-Only Export**
```bash
# Export DDL for non-preferred tables
export PGPASSWORD='BQX_Aurora_2025_Secure'
pg_dump -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres -d bqx \
  --schema-only \
  --table='bqx.m1_*' --table='bqx.reg_*' --table='bqx.fwd_*' \
  | grep -E "(audhkd|audsgd|cadhkd|cadsgd|chfhkd|eurhkd|eursgd|gbphkd|gbpsgd|hkdjpy|nzdhkd|nzdsgd|sgdchf|sgdhkd|sgdjpy|usdsek|usdsgd)" \
  > /tmp/bqx_non_preferred_ddl_backup_20251108.sql
```

**Recommendation**: **Option 1 (Aurora Snapshot)** is the safest and fastest recovery option.

---

## Cleanup Execution Plan

### Phase 1: Pre-Flight Checks (5 minutes)

**Step 1.1**: Verify Aurora cluster status
```bash
aws rds describe-db-clusters \
  --db-cluster-identifier trillium-bqx-cluster \
  --query 'DBClusters[0].Status' \
  --output text
# Expected: available
```

**Step 1.2**: Run verification queries (see Safety Procedures above)

**Step 1.3**: Create Aurora snapshot
```bash
aws rds create-db-cluster-snapshot \
  --db-cluster-identifier trillium-bqx-cluster \
  --db-cluster-snapshot-identifier trillium-bqx-pre-cleanup-20251108 \
  --tags Key=Purpose,Value=PrePairCleanup Key=Date,Value=2025-11-08

# Wait for snapshot completion
aws rds wait db-cluster-snapshot-available \
  --db-cluster-snapshot-identifier trillium-bqx-pre-cleanup-20251108
```

### Phase 2: Cleanup Execution (2 minutes)

**Step 2.1**: Connect to database
```bash
export PGPASSWORD='BQX_Aurora_2025_Secure'
psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres -d bqx
```

**Step 2.2**: Execute cleanup SQL script
```sql
-- ============================================================================
-- BQX AURORA DATABASE CLEANUP - NON-PREFERRED FOREX PAIRS
-- Date: 2025-11-08
-- Pairs to remove: 17 pairs (SGD, HKD, SEK)
-- Tables to drop: 21 tables (m1, reg, fwd)
-- ============================================================================

BEGIN;

-- Set client encoding
SET client_encoding = 'UTF8';

-- Display start time
SELECT 'Cleanup started at: ' || NOW()::TEXT;

-- ============================================================================
-- STEP 1: Drop tables for non-preferred pairs
-- ============================================================================

-- SGD pairs (9 pairs, 9 m1 tables)
DROP TABLE IF EXISTS bqx.m1_audsgd CASCADE;
DROP TABLE IF EXISTS bqx.m1_cadsgd CASCADE;
DROP TABLE IF EXISTS bqx.m1_eursgd CASCADE;
DROP TABLE IF EXISTS bqx.m1_gbpsgd CASCADE;
DROP TABLE IF EXISTS bqx.m1_nzdsgd CASCADE;
DROP TABLE IF EXISTS bqx.m1_sgdchf CASCADE;
DROP TABLE IF EXISTS bqx.m1_sgdhkd CASCADE;
DROP TABLE IF EXISTS bqx.m1_sgdjpy CASCADE;
DROP TABLE IF EXISTS bqx.m1_usdsgd CASCADE;

-- HKD pairs (7 pairs, 7 m1 tables)
DROP TABLE IF EXISTS bqx.m1_audhkd CASCADE;
DROP TABLE IF EXISTS bqx.m1_cadhkd CASCADE;
DROP TABLE IF EXISTS bqx.m1_chfhkd CASCADE;
DROP TABLE IF EXISTS bqx.m1_eurhkd CASCADE;
DROP TABLE IF EXISTS bqx.m1_gbphkd CASCADE;
DROP TABLE IF EXISTS bqx.m1_hkdjpy CASCADE;
DROP TABLE IF EXISTS bqx.m1_nzdhkd CASCADE;

-- SEK pair (1 pair, 1 m1 table)
DROP TABLE IF EXISTS bqx.m1_usdsek CASCADE;

-- ============================================================================
-- STEP 2: Drop regression and forward tables (usdsek, usdsgd)
-- ============================================================================

-- usdsek tables (reg + fwd)
DROP TABLE IF EXISTS bqx.reg_usdsek CASCADE;
DROP TABLE IF EXISTS bqx.fwd_usdsek CASCADE;

-- usdsgd tables (reg + fwd)
DROP TABLE IF EXISTS bqx.reg_usdsgd CASCADE;
DROP TABLE IF EXISTS bqx.fwd_usdsgd CASCADE;

-- ============================================================================
-- STEP 3: Verification
-- ============================================================================

-- Verify tables are dropped
SELECT
    'Non-preferred tables remaining: ' || COUNT(*) as status
FROM pg_tables
WHERE schemaname = 'bqx'
  AND (
    tablename ~ '^m1_(audhkd|audsgd|cadhkd|cadsgd|chfhkd|eurhkd|eursgd|gbphkd|gbpsgd|hkdjpy|nzdhkd|nzdsgd|sgdchf|sgdhkd|sgdjpy|usdsek|usdsgd)$' OR
    tablename ~ '^reg_(usdsek|usdsgd)$' OR
    tablename ~ '^fwd_(usdsek|usdsgd)$'
  );
-- Expected: 0

-- Verify preferred pairs still exist
SELECT
    'Preferred m1 tables remaining: ' || COUNT(*) as status
FROM pg_tables
WHERE schemaname = 'bqx'
  AND tablename ~ '^m1_(audcad|audchf|audjpy|audnzd|audusd|cadchf|cadjpy|chfjpy|euraud|eurcad|eurchf|eurgbp|eurjpy|eurnzd|eurusd|gbpaud|gbpcad|gbpchf|gbpjpy|gbpnzd|gbpusd|nzdcad|nzdchf|nzdjpy|nzdusd|usdcad|usdchf|usdjpy)$';
-- Expected: 28

-- Display completion time
SELECT 'Cleanup completed at: ' || NOW()::TEXT;

-- ============================================================================
-- COMMIT or ROLLBACK
-- ============================================================================

-- IMPORTANT: Review verification output before committing!
-- If everything looks good, execute: COMMIT;
-- If there are issues, execute: ROLLBACK;

-- Uncommitted transaction - MUST manually COMMIT or ROLLBACK
SELECT 'Transaction uncommitted - awaiting manual COMMIT or ROLLBACK';
```

**Step 2.3**: Review verification output
- Verify "Non-preferred tables remaining: 0"
- Verify "Preferred m1 tables remaining: 28"

**Step 2.4**: Commit or rollback
```sql
-- If verification passed:
COMMIT;

-- If verification failed:
ROLLBACK;
```

### Phase 3: Post-Cleanup Verification (3 minutes)

**Step 3.1**: Verify table count
```sql
-- Check total table count
SELECT
    'Total tables in bqx schema: ' || COUNT(*) as status
FROM pg_tables
WHERE schemaname = 'bqx';
-- Expected: 4,588 (was 4,609)
```

**Step 3.2**: Verify preferred pairs
```sql
-- List all m1 tables to confirm only preferred 28 remain
SELECT
    tablename,
    SUBSTRING(tablename FROM '^m1_(.+)$') as pair_name,
    pg_size_pretty(pg_total_relation_size('bqx.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'bqx'
  AND tablename ~ '^m1_[a-z]+$'
ORDER BY pair_name;
-- Expected: 28 rows
```

**Step 3.3**: Verify no non-preferred pairs remain
```sql
SELECT tablename
FROM pg_tables
WHERE schemaname = 'bqx'
  AND tablename ~ '(audhkd|audsgd|cadhkd|cadsgd|chfhkd|eurhkd|eursgd|gbphkd|gbpsgd|hkdjpy|nzdhkd|nzdsgd|sgdchf|sgdhkd|sgdjpy|usdsek|usdsgd)';
-- Expected: 0 rows
```

**Step 3.4**: VACUUM ANALYZE (optional, for catalog cleanup)
```sql
-- Reclaim space in system catalogs
VACUUM ANALYZE pg_class;
VACUUM ANALYZE pg_attribute;
VACUUM ANALYZE pg_index;
```

### Phase 4: Documentation Update (5 minutes)

**Step 4.1**: Document cleanup execution
- Record snapshot ID
- Record completion timestamp
- Save verification query results

**Step 4.2**: Update system documentation
- Update schema diagrams
- Update table inventories
- Update application configurations (if any)

---

## Rollback Plan

### If Cleanup Needs to be Reversed

**Scenario 1**: Transaction rollback (during Step 2.4)
```sql
-- If still in transaction, simply rollback
ROLLBACK;
```

**Scenario 2**: Restore from Aurora snapshot (after COMMIT)
```bash
# List available snapshots
aws rds describe-db-cluster-snapshots \
  --db-cluster-identifier trillium-bqx-cluster \
  --query 'DBClusterSnapshots[*].[DBClusterSnapshotIdentifier,SnapshotCreateTime,Status]' \
  --output table

# Restore from snapshot to new cluster
aws rds restore-db-cluster-from-snapshot \
  --db-cluster-identifier trillium-bqx-cluster-restored \
  --snapshot-identifier trillium-bqx-pre-cleanup-20251108 \
  --engine aurora-postgresql \
  --engine-version 16.8 \
  --db-subnet-group-name trillium-aurora-subnet-group \
  --vpc-security-group-ids sg-0236c25f1aca4aa56

# Wait for restoration
aws rds wait db-cluster-available \
  --db-cluster-identifier trillium-bqx-cluster-restored
```

**Scenario 3**: Recreate tables from DDL backup
```bash
# If you saved DDL backup, restore tables
export PGPASSWORD='BQX_Aurora_2025_Secure'
psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres -d bqx \
  -f /tmp/bqx_non_preferred_ddl_backup_20251108.sql
```

---

## Execution Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| **Phase 1** | 5 min | Pre-flight checks + snapshot |
| **Phase 2** | 2 min | SQL execution + verification |
| **Phase 3** | 3 min | Post-cleanup verification |
| **Phase 4** | 5 min | Documentation update |
| **Total** | **15 min** | End-to-end execution |

---

## Risk Mitigation

### Low-Risk Factors

✅ **All tables are empty** (0 bytes, 0 rows)
✅ **No foreign key constraints** to break
✅ **No dependent views** or materialized views
✅ **Preferred pairs unaffected** (complete separation)
✅ **Aurora snapshot** available for rollback
✅ **Transaction-based** cleanup (can rollback before commit)

### Potential Issues & Mitigations

| Issue | Likelihood | Impact | Mitigation |
|-------|------------|--------|------------|
| Accidental drop of preferred table | Very Low | High | Use explicit table names (not wildcards) |
| Application breakage | Very Low | Medium | Tables not used in ML pipeline |
| Snapshot failure | Low | Low | Verify snapshot before cleanup |
| Network disconnect during DROP | Low | Low | Use transaction (auto-rollback) |

---

## Post-Cleanup Actions

### Immediate Actions (Day 1)

1. ✅ Verify Aurora cluster health
2. ✅ Run application smoke tests
3. ✅ Monitor ACU scaling (ensure normal behavior)
4. ✅ Check CloudWatch metrics (connections, CPU, memory)

### Short-Term Actions (Week 1)

1. ✅ Keep snapshot for 30 days (safety period)
2. ✅ Monitor ML pipeline execution
3. ✅ Verify Phase 2-5 runs successfully
4. ✅ Update system documentation

### Long-Term Actions (Month 1)

1. ✅ Delete pre-cleanup snapshot (if no issues)
2. ✅ Archive cleanup documentation
3. ✅ Update operational runbooks

---

## Appendix A: Complete Table List

### Tables to Remove (21 tables)

```
bqx.m1_audhkd      (AUD/HKD - M1)
bqx.m1_audsgd      (AUD/SGD - M1)
bqx.m1_cadhkd      (CAD/HKD - M1)
bqx.m1_cadsgd      (CAD/SGD - M1)
bqx.m1_chfhkd      (CHF/HKD - M1)
bqx.m1_eurhkd      (EUR/HKD - M1)
bqx.m1_eursgd      (EUR/SGD - M1)
bqx.m1_gbphkd      (GBP/HKD - M1)
bqx.m1_gbpsgd      (GBP/SGD - M1)
bqx.m1_hkdjpy      (HKD/JPY - M1)
bqx.m1_nzdhkd      (NZD/HKD - M1)
bqx.m1_nzdsgd      (NZD/SGD - M1)
bqx.m1_sgdchf      (SGD/CHF - M1)
bqx.m1_sgdhkd      (SGD/HKD - M1)
bqx.m1_sgdjpy      (SGD/JPY - M1)
bqx.m1_usdsek      (USD/SEK - M1)
bqx.m1_usdsgd      (USD/SGD - M1)
bqx.reg_usdsek     (USD/SEK - Regression)
bqx.reg_usdsgd     (USD/SGD - Regression)
bqx.fwd_usdsek     (USD/SEK - Forward Returns)
bqx.fwd_usdsgd     (USD/SGD - Forward Returns)
```

---

## Appendix B: Preferred 28 Pairs (Retained)

```
audcad, audchf, audjpy, audnzd, audusd,
cadchf, cadjpy, chfjpy,
euraud, eurcad, eurchf, eurgbp, eurjpy, eurnzd, eurusd,
gbpaud, gbpcad, gbpchf, gbpjpy, gbpnzd, gbpusd,
nzdcad, nzdchf, nzdjpy, nzdusd,
usdcad, usdchf, usdjpy
```

**Total**: 28 pairs (all verified to exist in Aurora)

---

## Appendix C: Aurora Cluster Information

**Cluster Details**:
- **Identifier**: trillium-bqx-cluster
- **Endpoint**: trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com
- **Engine**: aurora-postgresql 16.8
- **Mode**: Serverless v2 (0.5-32 ACU)
- **Storage**: 2.485 TB
- **Encryption**: Enabled (KMS)
- **Backup Retention**: 35 days
- **Multi-AZ**: us-east-1b, us-east-1c, us-east-1d

**Connection Details**:
- **Database**: bqx
- **User**: postgres
- **Password**: BQX_Aurora_2025_Secure
- **Port**: 5432
- **SSL Mode**: require

---

## Approval & Sign-Off

**Plan Prepared By**: Claude (RobkeiRingMaster)
**Date Prepared**: 2025-11-08
**Review Required**: Yes
**Approval Required**: Yes

**Approval Checklist**:
- [ ] Pre-flight verification completed
- [ ] Aurora snapshot created
- [ ] Cleanup SQL script reviewed
- [ ] Rollback plan understood
- [ ] Post-cleanup verification steps ready
- [ ] Authorized to execute

**Approved By**: _________________
**Date**: _________________

---

**Document Status**: ✅ Ready for Review and Execution
**Next Step**: Review plan → Create snapshot → Execute cleanup
