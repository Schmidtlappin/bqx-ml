# BQX Aurora Cleanup - Quick Start Guide

**Date**: 2025-11-08
**Time Required**: 15 minutes
**Risk Level**: ✅ LOW (all tables empty)

---

## What This Does

Removes **17 non-preferred forex pairs** from the BQX Aurora database:
- **9 SGD pairs** (Singapore Dollar)
- **7 HKD pairs** (Hong Kong Dollar)
- **1 SEK pair** (Swedish Krona)

**Total**: 21 empty tables (0 bytes, 0 rows)

---

## Pre-Requisites

✅ Aurora cluster is running (trillium-bqx-cluster)
✅ AWS CLI configured with Trillium account credentials
✅ PostgreSQL client (psql) installed
✅ Network access to Aurora endpoint

---

## Quick Execution Steps

### Step 1: Create Aurora Snapshot (2 minutes)

```bash
# Create safety snapshot
AWS_ACCESS_KEY_ID="AKIAXXXXXXXXXXXXXXXX" \
AWS_SECRET_ACCESS_KEY="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" \
aws rds create-db-cluster-snapshot \
  --db-cluster-identifier trillium-bqx-cluster \
  --db-cluster-snapshot-identifier trillium-bqx-pre-cleanup-20251108 \
  --tags Key=Purpose,Value=PrePairCleanup Key=Date,Value=2025-11-08

# Wait for snapshot completion (1-2 minutes)
AWS_ACCESS_KEY_ID="AKIAXXXXXXXXXXXXXXXX" \
AWS_SECRET_ACCESS_KEY="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" \
aws rds wait db-cluster-snapshot-available \
  --db-cluster-snapshot-identifier trillium-bqx-pre-cleanup-20251108

echo "✅ Snapshot created successfully"
```

### Step 2: Execute Cleanup SQL (5 minutes)

```bash
# Connect to Aurora and run cleanup script
export PGPASSWORD='BQX_Aurora_2025_Secure'
psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres \
  -d bqx \
  -f /home/ubuntu/Robkei-Ring/sandbox/artifacts/bqx_cleanup_non_preferred_pairs.sql
```

**What happens**:
1. Pre-flight verification (checks preferred pairs exist)
2. Drops 17 m1 tables (SGD/HKD/SEK pairs)
3. Drops 4 reg/fwd tables (usdsek, usdsgd)
4. Post-cleanup verification
5. **Waits for manual COMMIT or ROLLBACK**

### Step 3: Review & Commit (1 minute)

**Review verification output**:
- ✅ All checks show "PASS"
- ✅ Non-preferred tables = 0
- ✅ Preferred tables = 28

**If all verifications passed**:
```sql
COMMIT;
```

**If any verification failed**:
```sql
ROLLBACK;
```

### Step 4: Final Verification (2 minutes)

```bash
# Verify cleanup success
export PGPASSWORD='BQX_Aurora_2025_Secure'
psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres \
  -d bqx \
  -c "
SELECT
    'Total m1 tables: ' || COUNT(*) as status
FROM pg_tables
WHERE schemaname = 'bqx'
  AND tablename ~ '^m1_[a-z]+$';
"
# Expected: 28
```

---

## One-Liner Execution (For Experienced Users)

```bash
# Create snapshot + execute cleanup (requires manual COMMIT)
AWS_ACCESS_KEY_ID="AKIAXXXXXXXXXXXXXXXX" \
AWS_SECRET_ACCESS_KEY="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" \
aws rds create-db-cluster-snapshot \
  --db-cluster-identifier trillium-bqx-cluster \
  --db-cluster-snapshot-identifier trillium-bqx-pre-cleanup-20251108 && \
aws rds wait db-cluster-snapshot-available \
  --db-cluster-snapshot-identifier trillium-bqx-pre-cleanup-20251108 && \
echo "✅ Snapshot ready - executing cleanup..." && \
PGPASSWORD='BQX_Aurora_2025_Secure' \
psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres -d bqx \
  -f /home/ubuntu/Robkei-Ring/sandbox/artifacts/bqx_cleanup_non_preferred_pairs.sql
```

---

## Rollback Instructions

### If Cleanup Needs to be Reversed

**Option 1: Transaction Rollback (during execution)**
```sql
-- If script hasn't been committed yet
ROLLBACK;
```

**Option 2: Restore from Snapshot (after commit)**
```bash
# Restore entire cluster from snapshot
AWS_ACCESS_KEY_ID="AKIAXXXXXXXXXXXXXXXX" \
AWS_SECRET_ACCESS_KEY="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" \
aws rds restore-db-cluster-from-snapshot \
  --db-cluster-identifier trillium-bqx-cluster-restored \
  --snapshot-identifier trillium-bqx-pre-cleanup-20251108 \
  --engine aurora-postgresql \
  --engine-version 16.8 \
  --db-subnet-group-name trillium-aurora-subnet-group \
  --vpc-security-group-ids sg-0236c25f1aca4aa56
```

---

## What Gets Removed

### 17 Forex Pairs (21 Tables)

**SGD Pairs** (9):
```
audsgd, cadsgd, eursgd, gbpsgd, nzdsgd,
sgdchf, sgdhkd, sgdjpy, usdsgd
```

**HKD Pairs** (7):
```
audhkd, cadhkd, chfhkd, eurhkd, gbphkd,
hkdjpy, nzdhkd
```

**SEK Pairs** (1):
```
usdsek
```

**Tables**:
- 17 m1 tables (minute data)
- 2 reg tables (usdsek, usdsgd)
- 2 fwd tables (usdsek, usdsgd)

---

## What Stays (28 Preferred Pairs)

```
audcad, audchf, audjpy, audnzd, audusd,
cadchf, cadjpy, chfjpy,
euraud, eurcad, eurchf, eurgbp, eurjpy, eurnzd, eurusd,
gbpaud, gbpcad, gbpchf, gbpjpy, gbpnzd, gbpusd,
nzdcad, nzdchf, nzdjpy, nzdusd,
usdcad, usdchf, usdjpy
```

All m1, reg, fwd, and mv_*_merged tables for these 28 pairs remain intact.

---

## Safety Features

✅ **Transaction-based**: Can ROLLBACK before commit
✅ **Aurora snapshot**: Full recovery option
✅ **Pre/post verification**: Automated checks
✅ **No data loss risk**: All tables empty (0 bytes)
✅ **No dependencies**: No foreign keys to break
✅ **Explicit DROP**: Each table named explicitly (no wildcards)

---

## Post-Cleanup Checklist

- [ ] Cleanup executed successfully
- [ ] All verifications passed
- [ ] Transaction committed
- [ ] Final verification confirmed 28 m1 tables
- [ ] Aurora cluster healthy (check AWS console)
- [ ] Snapshot retained for 30 days
- [ ] Documentation updated

---

## Support

**Detailed Plan**: [BQX-FOREX-PAIR-CLEANUP-PLAN.md](BQX-FOREX-PAIR-CLEANUP-PLAN.md)
**SQL Script**: [bqx_cleanup_non_preferred_pairs.sql](bqx_cleanup_non_preferred_pairs.sql)
**Analysis**: [BQX-28-FOREX-PAIRS.md](BQX-28-FOREX-PAIRS.md)

---

**Status**: ✅ Ready to Execute
**Estimated Time**: 15 minutes
**Risk**: LOW
