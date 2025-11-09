# BQX Aurora Cleanup - DECISION REQUIRED

**Date**: 2025-11-08
**Status**: ⚠️ **CRITICAL UPDATE - USER DECISION REQUIRED**

---

## CRITICAL FINDING

### Initial Assessment (INCORRECT)

When I first analyzed the non-preferred forex pair tables, I checked the parent tables only, which showed:
- ❌ **0 bytes storage**
- ❌ **0 rows**
- ❌ Risk Level: LOW

**This was INCORRECT.**

### Corrected Assessment (ACCURATE)

After checking partitions, I discovered:
- ✅ **5.37 GB of real data** (5,632,122,880 bytes)
- ✅ **20-25 million rows** (estimated)
- ✅ **872 child partitions** containing actual forex data
- ⚠️ Risk Level: **MEDIUM-HIGH**

---

## What Happened?

PostgreSQL partitioned tables store data in **child partitions**, not the parent table.

**Parent table**: `bqx.m1_audsgd` → 0 bytes (only metadata)
**Child partitions**: `m1_audsgd_y2020m09`, `m1_audsgd_y2020m10`, etc. → Contains actual data

My initial query checked parent tables only → showed 0 bytes
**Reality**: 872 partitions contain 5.37 GB of real forex data

---

## Data to Be Deleted

### Summary

| Metric | Value |
|--------|-------|
| **Storage** | 5.37 GB |
| **Rows** | ~20-25 million (estimated) |
| **Partitions** | 872 child partitions |
| **Parent Tables** | 21 tables |
| **Time Range** | 2020-2025 (50+ months) |
| **Data Type** | Minute-level forex prices + analysis |

### Forex Pairs (17 pairs)

**SGD (Singapore Dollar) - 9 pairs**:
- audsgd, cadsgd, eursgd, gbpsgd, nzdsgd, sgdchf, sgdhkd, sgdjpy, usdsgd

**HKD (Hong Kong Dollar) - 7 pairs**:
- audhkd, cadhkd, chfhkd, eurhkd, gbphkd, hkdjpy, nzdhkd

**SEK (Swedish Krona) - 1 pair**:
- usdsek

### Sample Data Points

| Table | Rows | Storage | Data Range |
|-------|------|---------|------------|
| m1_audsgd | 1,796,482 | 390 MB | Sep 2020 - Nov 2024 |
| m1_usdsgd | 1,660,235 | 403 MB | 2020-2024 |
| fwd_usdsgd | 361,585 | 164 MB | Jul 2024 - Jun 2025 |
| reg_usdsek | 364,463 | 241 MB | Recent months |
| m1_audhkd | 184,210 | 44 MB | Jun-Nov 2024 |

---

## Critical Questions

### Before Making a Decision

1. **Why does this data exist?**
   - It was collected from Oanda API
   - Tables were created during setup
   - Data was populated over 2020-2024
   - But: NOT used in bqx-db repository code

2. **Is this data needed?**
   - ❓ Used for backtesting or analysis?
   - ❓ Required for any current workflows?
   - ❓ Plans to use SGD/HKD/SEK pairs in future?
   - ❓ Historical value for research?

3. **Can it be recreated?**
   - ✅ Yes: Can re-download from Oanda API
   - ⚠️ But: Takes time + API calls
   - ⚠️ May hit historical data limits
   - ⚠️ Some data may no longer be available

4. **What's the impact of deletion?**
   - ✅ Aligns database with repository code (28 pairs only)
   - ✅ Saves 5.37 GB storage
   - ✅ Reduces maintenance (872 fewer partitions)
   - ❌ **PERMANENT data loss** (cannot undo without backup)
   - ❌ Loses historical forex data for 17 pairs

---

## Decision Options

### Option A: DELETE (Align with Repository)

**Execute cleanup → Remove all 17 non-preferred pairs**

**✅ Pros**:
- Database matches repository code 100%
- Saves 5.37 GB storage
- Removes 872 unused partitions
- Cleaner, more maintainable schema

**❌ Cons**:
- **PERMANENT data deletion**
- Loses 50+ months of SGD/HKD/SEK forex data
- Cannot recreate without significant effort
- May lose research/analysis capability

**Required Actions**:
1. Create Aurora snapshot (MANDATORY)
2. (Optional) Export to S3 before deletion
3. Execute cleanup SQL script
4. Verify 28 preferred pairs remain

**Risk**: MEDIUM-HIGH (data deletion)
**Time**: 15 minutes (without export) or 2 hours (with export)

---

### Option B: EXPORT THEN DELETE (Conservative)

**Export data to S3 → Then execute cleanup**

**✅ Pros**:
- Safety net: Data preserved in S3
- Can restore if needed later
- Still achieves database alignment
- Insurance against future needs

**❌ Cons**:
- Takes longer (~2 hours for export)
- Requires S3 storage (~$0.12/month for 5.37 GB)
- More complex procedure

**Required Actions**:
1. Create Aurora snapshot
2. Export all 17 pairs to S3 (Parquet or CSV)
3. Verify export completeness
4. Execute cleanup SQL script
5. Retain S3 export for 1+ year

**Risk**: LOW-MEDIUM (data backed up)
**Time**: ~2 hours
**Cost**: ~$0.12/month S3 storage

---

### Option C: KEEP DATA (Status Quo)

**Do nothing → Keep all data**

**✅ Pros**:
- Zero risk of data loss
- No action required
- Data available for future use
- Reversible decision (can delete later)

**❌ Cons**:
- Database/repository mismatch continues
- Extra 872 partitions to maintain
- 5.37 GB "orphaned" data
- Schema complexity

**Required Actions**:
- None

**Risk**: ZERO (no changes)
**Time**: 0 minutes

---

## My Recommendation

**OPTION B: Export Then Delete** (Conservative Approach)

**Rationale**:
1. **Preserves data**: S3 export provides insurance
2. **Achieves alignment**: Database matches repository
3. **Manageable risk**: Can restore if needed
4. **Low cost**: ~$0.12/month for S3 storage
5. **Best of both worlds**: Clean database + data backup

**Why NOT Option A** (Delete without export):
- Too risky given 5.37 GB of real data
- 50+ months of forex data has value
- Unknown if data might be needed later
- Export cost is negligible

**Why NOT Option C** (Keep data):
- Database/code mismatch is problematic
- Data appears unused (not in repository code)
- Maintenance overhead for 872 partitions
- Can always keep export in S3 instead

---

## Export Procedure (Option B)

### Step 1: Create Aurora Snapshot

```bash
aws rds create-db-cluster-snapshot \
  --db-cluster-identifier trillium-bqx-cluster \
  --db-cluster-snapshot-identifier trillium-bqx-pre-cleanup-20251108
```

### Step 2: Export to S3

```bash
# Export each non-preferred pair to S3
PAIRS=("audhkd" "audsgd" "cadhkd" "cadsgd" "chfhkd" "eurhkd" "eursgd"
       "gbphkd" "gbpsgd" "hkdjpy" "nzdhkd" "nzdsgd" "sgdchf" "sgdhkd"
       "sgdjpy" "usdsek" "usdsgd")

for pair in "${PAIRS[@]}"; do
    echo "Exporting ${pair}..."
    # Export M1 data
    psql -h trillium-bqx-cluster... -c "\COPY (SELECT * FROM bqx.m1_${pair}) TO STDOUT CSV HEADER" \
        | gzip | aws s3 cp - s3://bqx-archive/non-preferred-pairs/m1_${pair}.csv.gz

    # Export REG/FWD if they exist
    if [[ "$pair" == "usdsek" || "$pair" == "usdsgd" ]]; then
        psql ... -c "\COPY (SELECT * FROM bqx.reg_${pair}) TO STDOUT CSV HEADER" \
            | gzip | aws s3 cp - s3://bqx-archive/non-preferred-pairs/reg_${pair}.csv.gz
        psql ... -c "\COPY (SELECT * FROM bqx.fwd_${pair}) TO STDOUT CSV HEADER" \
            | gzip | aws s3 cp - s3://bqx-archive/non-preferred-pairs/fwd_${pair}.csv.gz
    fi
done
```

**Time**: ~1-2 hours
**Storage**: ~2-3 GB compressed (vs 5.37 GB uncompressed)

### Step 3: Verify Export

```bash
# Check all files exported
aws s3 ls s3://bqx-archive/non-preferred-pairs/ --human-readable
# Expected: 21 files (17 m1, 2 reg, 2 fwd)
```

### Step 4: Execute Cleanup

```bash
psql -h trillium-bqx-cluster... -d bqx \
    -f /home/ubuntu/Robkei-Ring/sandbox/artifacts/bqx_cleanup_non_preferred_pairs.sql
# Review verification → COMMIT
```

---

## Cleanup Procedure (Option A - No Export)

### Fast Cleanup (15 minutes)

```bash
# Step 1: Create snapshot (2 min)
aws rds create-db-cluster-snapshot \
  --db-cluster-identifier trillium-bqx-cluster \
  --db-cluster-snapshot-identifier trillium-bqx-pre-cleanup-20251108

# Step 2: Execute cleanup (5 min)
psql -h trillium-bqx-cluster... -d bqx \
    -f /home/ubuntu/Robkei-Ring/sandbox/artifacts/bqx_cleanup_non_preferred_pairs.sql

# Step 3: Review & COMMIT (1 min)
# Script pauses for manual COMMIT or ROLLBACK
```

---

## Rollback Options

### If Data Needs to be Restored

**Method 1: Aurora Snapshot Restore** (Complete)
- Restores entire cluster to pre-cleanup state
- Time: ~30 minutes
- Restores ALL data (not just non-preferred pairs)

**Method 2: S3 Import** (Selective - Only if exported)
- Imports only non-preferred pair data
- Time: ~2 hours
- Requires export was performed

**Method 3: Oanda API Re-Download** (Fallback)
- Re-downloads M1 data from Oanda API
- Time: Several hours
- May have historical data limits

---

## Decision Matrix

| Criteria | Option A (Delete) | Option B (Export+Delete) | Option C (Keep) |
|----------|-------------------|--------------------------|-----------------|
| **Data Safety** | ⚠️ Snapshot only | ✅ Snapshot + S3 | ✅ Unchanged |
| **Time Required** | 15 min | 2 hours | 0 min |
| **Cost** | $0 | ~$0.12/mo | $0 |
| **Database Alignment** | ✅ Perfect | ✅ Perfect | ❌ Mismatch |
| **Reversibility** | ⚠️ Snapshot only | ✅ Easy restore | ✅ No change |
| **Risk Level** | MEDIUM-HIGH | LOW-MEDIUM | ZERO |
| **Maintenance** | ✅ Clean | ✅ Clean | ❌ 872 partitions |

---

## Required User Decisions

### Questions to Answer

1. **Do you need SGD/HKD/SEK forex data?**
   - [ ] Yes → Choose Option C (Keep data)
   - [ ] No → Proceed to question 2

2. **Are you comfortable with permanent deletion?**
   - [ ] Yes → Choose Option A (Delete)
   - [ ] No → Choose Option B (Export then delete)

3. **Do you want insurance via S3 export?**
   - [ ] Yes → Choose Option B (Export then delete)
   - [ ] No, snapshot is enough → Choose Option A (Delete)

4. **Can you commit 2 hours for export?**
   - [ ] Yes → Option B is feasible
   - [ ] No → Option A or Option C

---

## Next Steps

**WAIT FOR USER DECISION**

Based on user choice:
- **Option A**: Execute cleanup script (15 min)
- **Option B**: Export to S3 → Execute cleanup (2 hours)
- **Option C**: Do nothing (0 min)

**DO NOT PROCEED** without explicit user confirmation that:
1. User understands this deletes 5.37 GB of real data
2. User confirms SGD/HKD/SEK pairs are not needed
3. User has chosen Option A, B, or C
4. User has reviewed this document

---

## Supporting Documents

- **[BQX-PARTITION-DATA-ANALYSIS.md](BQX-PARTITION-DATA-ANALYSIS.md)** - Detailed partition analysis
- **[BQX-FOREX-PAIR-CLEANUP-PLAN.md](BQX-FOREX-PAIR-CLEANUP-PLAN.md)** - Original cleanup plan (needs update)
- **[bqx_cleanup_non_preferred_pairs.sql](bqx_cleanup_non_preferred_pairs.sql)** - Cleanup SQL script
- **[BQX-28-FOREX-PAIRS.md](BQX-28-FOREX-PAIRS.md)** - Preferred pairs analysis

---

**Status**: ⚠️ AWAITING USER DECISION
**Critical**: Do NOT execute cleanup without user confirmation
**Recommended**: Option B (Export then delete)
**Updated**: 2025-11-08
