# BQX Table Strategy: Rebuild vs Recalculate

**Date:** 2025-11-10
**Decision:** REBUILD (Drop/Create/Backfill)
**Airtable Stage:** 1.5.4

---

## Question: Should BQX tables be recalculated (UPDATE) or rebuilt (DROP/CREATE)?

**Answer:** **REBUILD** - Drop existing tables, create new schema, backfill from scratch.

---

## Two Approaches Compared

### Option A: Recalculate (UPDATE existing tables)

**Method:**
```sql
-- Update existing rows in-place
UPDATE bqx.bqx_audcad
SET rate_index = (rate / baseline_rate) * 100,
    w15_bqx_max_index = (w15_bqx_max / baseline_rate) * 100,
    w15_bqx_min_index = (w15_bqx_min / baseline_rate) * 100,
    -- ... convert all fields to index
    -- BUT: Cannot remove _pct fields without ALTER TABLE
WHERE TRUE;

-- Remove _pct columns (expensive!)
ALTER TABLE bqx.bqx_audcad
DROP COLUMN w15_bqx_max_pct,
DROP COLUMN w15_bqx_min_pct,
-- ... 24 columns to drop
```

**Pros:**
- Preserves table structure
- No need to recreate partitions
- Existing indexes remain

**Cons:**
- Cannot easily remove 24 _pct fields (requires ALTER TABLE)
- UPDATE on 10.3M rows = slow (multiple hours per table)
- Residual data remains (old values, bloat)
- Cannot optimize partition structure
- Risk of partial updates if process fails

---

### Option B: Rebuild (DROP/CREATE/BACKFILL) ← **CHOSEN APPROACH**

**Method:**
```sql
-- 1. Drop existing table
DROP TABLE IF EXISTS bqx.bqx_audcad CASCADE;

-- 2. Create new table with optimized schema
CREATE TABLE bqx.bqx_audcad (
    ts_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    pair TEXT NOT NULL,

    -- Index-based fields (NEW)
    rate_index DOUBLE PRECISION,
    w15_bqx_max_index DOUBLE PRECISION,
    w15_bqx_min_index DOUBLE PRECISION,
    w15_bqx_range_index DOUBLE PRECISION,
    -- ... 36 total index fields

    -- Target field
    w60_bqx_return DOUBLE PRECISION,

    -- REMOVED: 24 _pct fields (no longer needed)

    PRIMARY KEY (ts_utc, pair)
) PARTITION BY RANGE (ts_utc);

-- 3. Create partitions
CREATE TABLE bqx.bqx_audcad_y2020m01 PARTITION OF bqx.bqx_audcad
    FOR VALUES FROM ('2020-01-01') TO ('2020-02-01');
-- ... create all 85 partitions

-- 4. Backfill from m1_* source data
INSERT INTO bqx.bqx_audcad
SELECT
    ts_utc,
    'audcad' as pair,
    rate_index,  -- Already populated in Stage 1.5.2!
    -- ... calculate all BQX features using rate_index
FROM bqx.m1_audcad
WHERE ts_utc >= '2020-01-01';
```

**Pros:**
- ✅ Clean slate - no residual data
- ✅ Remove 24 _pct fields (schema optimization)
- ✅ Optimize partition structure
- ✅ Optimize indexes from the start
- ✅ All data guaranteed consistent
- ✅ Can verify backfill completeness
- ✅ Rollback strategy (keep old tables until verified)

**Cons:**
- More disruptive (brief downtime)
- Need to recreate all indexes
- Longer total time (but parallelizable)

---

## Airtable Plan: Stage 1.5.4

According to the official plan, **Stage 1.5.4** uses the REBUILD approach:

### TSK-1.5.4.1: Drop existing BQX tables
**Duration:** 0.5 hours
**Method:**
```sql
DROP TABLE IF EXISTS bqx.bqx_audcad CASCADE;
DROP TABLE IF EXISTS bqx.bqx_audchf CASCADE;
-- ... drop all 28 BQX tables
```

### TSK-1.5.4.2: Create new BQX tables with index schema
**Duration:** 0.5 hours
**Method:**
- CREATE TABLE with new schema (index fields, no _pct fields)
- Create 336 partitions (12 partitions × 28 pairs)
- Create PRIMARY KEY indexes

### TSK-1.5.4.3: Run index-based backfill
**Duration:** 7 hours
**Method:**
- Read from m1_* tables (which now have rate_index populated!)
- Calculate BQX features using rate_index
- INSERT into new bqx_* tables
- Parallel execution (4-8 pairs at a time)

---

## Why REBUILD is Better for BQX Tables

### 1. Schema Changes Required
**Problem:** Need to remove 24 _pct fields

```sql
-- Old schema (77 columns):
rate, rate_index,
w15_bqx_max, w15_bqx_max_index, w15_bqx_max_pct,  ← 3 versions per feature
w15_bqx_min, w15_bqx_min_index, w15_bqx_min_pct,
-- ... 24 _pct fields to remove

-- New schema (53 columns):
rate_index,  ← Only index version
w15_bqx_max_index,
w15_bqx_min_index,
-- ... No _pct fields
```

**Solution:** REBUILD makes schema changes trivial (just define new schema).

---

### 2. Data Cleanliness
**Problem:** Old BQX values calculated from absolute rates (incorrect)

**UPDATE approach:** Mixed data (some old, some new, risk of partial updates)

**REBUILD approach:** All data freshly calculated from rate_index (guaranteed consistent)

---

### 3. Performance Optimization
**Problem:** Existing tables may have bloat, suboptimal indexes

**UPDATE approach:** Keeps existing table bloat, index fragmentation

**REBUILD approach:**
- Fresh tables (no bloat)
- Optimal index creation
- Better query performance

---

### 4. Rollback Safety
**Problem:** What if something goes wrong?

**UPDATE approach:** Data is overwritten (hard to rollback)

**REBUILD approach:**
```bash
# Keep old tables during rebuild
mv bqx.bqx_audcad bqx.bqx_audcad_old

# Create new table
CREATE TABLE bqx.bqx_audcad ...

# If successful: drop old
DROP TABLE bqx.bqx_audcad_old;

# If failed: restore old
DROP TABLE bqx.bqx_audcad;
ALTER TABLE bqx.bqx_audcad_old RENAME TO bqx.bqx_audcad;
```

---

### 5. Parallelization
**Problem:** Processing 28 pairs takes time

**UPDATE approach:**
- Must update each partition sequentially (lock contention)
- 10.3M rows × 28 pairs = 288M rows to update

**REBUILD approach:**
- Backfill multiple pairs in parallel (no lock contention)
- Can run 4-8 pairs simultaneously
- Estimated: 7 hours for all 28 pairs

---

## Timeline Comparison

### UPDATE Approach (Recalculate)
```
1. Modify bqx_* calculation logic (1h)
2. UPDATE all 28 bqx_* tables (12h) - sequential, slow
3. ALTER TABLE to drop 24 _pct columns (2h)
4. VACUUM tables (1h)
TOTAL: 16 hours
```

### REBUILD Approach (Drop/Create) ← **CHOSEN**
```
1. Modify bqx_* calculation logic (1h) - Stage 1.5.3
2. Drop existing bqx_* tables (0.5h) - Stage 1.5.4.1
3. Create new bqx_* schema (0.5h) - Stage 1.5.4.2
4. Backfill from m1_* (7h) - Stage 1.5.4.3, parallel
TOTAL: 9 hours
```

**Winner:** REBUILD is 7 hours faster and cleaner!

---

## Implementation Plan (Stage 1.5.4)

### Before Starting
- ✅ Stage 1.5.2 complete (m1_* tables have rate_index)
- ✅ Stage 1.5.3 complete (backward_worker.py uses rate_index)
- ✅ Backup strategy in place

### Step 1: Drop (TSK-1.5.4.1)
```bash
# Run drop script
psql -f scripts/refactor/drop_bqx_tables.sql
```

### Step 2: Create (TSK-1.5.4.2)
```bash
# Create new schema
psql -f scripts/refactor/create_bqx_tables_index_schema.sql
```

### Step 3: Backfill (TSK-1.5.4.3)
```bash
# Run backfill (parallel execution)
python scripts/backfill/backward_worker_threaded.py \
    --pairs audcad,audchf,audjpy,audnzd \
    --start-date 2020-01-01 \
    --end-date 2025-12-31 \
    --parallel 4
```

### Step 4: Verify
```sql
-- Check row counts
SELECT COUNT(*) FROM bqx.bqx_audcad;  -- Should match m1_audcad

-- Check data quality
SELECT * FROM bqx.bqx_audcad
WHERE rate_index IS NULL OR w60_bqx_return IS NULL;  -- Should be 0 rows

-- Check baseline
SELECT * FROM bqx.bqx_audcad
WHERE ts_utc = '2024-07-01 00:00:00+00';
-- rate_index should be ~100.00
```

---

## Summary

| Aspect | UPDATE (Recalculate) | REBUILD (Drop/Create) |
|--------|---------------------|----------------------|
| **Duration** | 16 hours | 9 hours ✓ |
| **Schema Changes** | Difficult (ALTER TABLE) | Easy (CREATE TABLE) ✓ |
| **Data Consistency** | Risk of partial updates | Guaranteed fresh ✓ |
| **Parallelization** | Limited (lock contention) | Full (no locks) ✓ |
| **Rollback** | Difficult | Easy (keep old tables) ✓ |
| **Optimization** | Keeps bloat | Fresh, optimal ✓ |
| **Airtable Plan** | ❌ Not planned | ✅ Stage 1.5.4 |

**Decision:** **REBUILD** (Drop/Create/Backfill)

---

## Next Steps

1. ✅ Stage 1.5.2 complete (rate_index in m1_* tables)
2. 🔜 Stage 1.5.3: Modify backward_worker.py to use rate_index
3. 🔜 Stage 1.5.4.1: Drop existing bqx_* tables
4. 🔜 Stage 1.5.4.2: Create new bqx_* tables (index schema)
5. 🔜 Stage 1.5.4.3: Backfill from m1_* (7 hours, parallel)
6. 🔜 Stage 1.5.4.4: Verify and index

---

**Created:** 2025-11-10
**Author:** Claude Code
**Status:** Strategy Confirmed - Ready for Stage 1.5.3
