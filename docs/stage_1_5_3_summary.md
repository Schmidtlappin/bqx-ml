# Stage 1.5.3: BQX Calculation Refactor - COMPLETE

**Date:** 2025-11-10
**Duration:** 1 hour (planned)
**Status:** ✅ COMPLETE

---

## Summary

Modified BQX calculation logic to use **rate_index** (forex index around 100) instead of **absolute rates** (e.g., 0.91246 for AUDCAD).

---

## Changes Made

### 1. Created Index-Based Worker Script

**File:** `/home/ubuntu/bqx-ml/scripts/backfill/backward_worker_index.py`

**Key Changes:**
```python
# OLD (backward_worker.py):
SELECT time, close as rate                   ← Absolute rate
FROM bqx.m1_{pair}

# NEW (backward_worker_index.py):
SELECT time, rate_index                      ← Forex index
FROM bqx.m1_{pair}
```

**Variable Naming:**
- `rates` → `rate_indexes` (clarity)
- `rate_t` → `index_t` (clarity)
- `past_rates` → `past_indexes` (clarity)

**Output Fields:**
- `rate` → `rate_index`
- `bqx_max` → `bqx_max_index`
- `bqx_min` → `bqx_min_index`
- `bqx_avg` → `bqx_avg_index`
- `bqx_stdev` → `bqx_stdev_index`

**Formulas:** UNCHANGED (correlation/percentage calculations are scale-independent)

---

### 2. Created BQX Table Drop Script

**File:** `/home/ubuntu/bqx-ml/scripts/refactor/stage_1_5_4_1_drop_bqx_tables.sql`

**Purpose:** Drop existing bqx_* tables (28 tables + 336 partitions, ~5.3 GB)

**Usage:**
```bash
PGPASSWORD='BQX_Aurora_2025_Secure' psql \
    -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
    -U postgres \
    -d bqx \
    -f /home/ubuntu/bqx-ml/scripts/refactor/stage_1_5_4_1_drop_bqx_tables.sql
```

---

### 3. Created BQX Table Creation Script

**File:** `/home/ubuntu/bqx-ml/scripts/refactor/stage_1_5_4_2_create_bqx_tables_index_schema.sql`

**Purpose:** Create new bqx_* tables with index-based schema

**Schema Changes:**
```sql
-- OLD Schema (77 columns):
rate DOUBLE PRECISION,              -- Absolute rate
w15_bqx_max DOUBLE PRECISION,       -- Absolute rate
w15_bqx_min DOUBLE PRECISION,       -- Absolute rate
w15_bqx_max_pct DOUBLE PRECISION,   -- Percentage field
-- ... 24 _pct fields

-- NEW Schema (53 columns):
rate_index DOUBLE PRECISION,        -- Index value (around 100)
w15_bqx_max_index DOUBLE PRECISION, -- Index value (around 100)
w15_bqx_min_index DOUBLE PRECISION, -- Index value (around 100)
-- ... NO _pct fields (24 fields removed)
```

**Partitioning:** 84 monthly partitions per pair (2020-01 through 2026-12)

**Total:** 28 pairs × 84 partitions = 2,352 partitions

**Usage:**
```bash
PGPASSWORD='BQX_Aurora_2025_Secure' psql \
    -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
    -U postgres \
    -d bqx \
    -f /home/ubuntu/bqx-ml/scripts/refactor/stage_1_5_4_2_create_bqx_tables_index_schema.sql
```

---

## Mathematical Equivalence

### Percentage Changes (Scale-Independent)

```python
# OLD (absolute rates):
bqx_return = Σ[(rate(t-i) - rate(t)) / rate(t)]

# NEW (rate index):
bqx_return = Σ[(index(t-i) - index(t)) / index(t)]

# These are IDENTICAL because:
index = (rate / baseline) * 100
(index_A - index_B) / index_B = (rate_A - rate_B) / rate_B  ✓
```

### Statistical Measures (Scale-Dependent but Comparable)

```python
# OLD (absolute rates):
bqx_max = 0.92632  # AUDCAD absolute rate
bqx_max = 1.08754  # EURUSD absolute rate (not comparable!)

# NEW (rate index):
bqx_max_index = 101.52  # AUDCAD (1.52% above baseline)
bqx_max_index = 102.18  # EURUSD (2.18% above baseline)
# ✓ Directly comparable!
```

---

## Why This Matters

### 1. Cross-Pair Comparability
- **OLD:** AUDCAD (0.91) and EURUSD (1.08) on different scales
- **NEW:** Both centered at 100, directly comparable

### 2. Cleaner Schema
- **OLD:** 77 columns per table (including 24 _pct fields)
- **NEW:** 53 columns per table (24 fewer columns)

### 3. Percentage Calculations Built-In
- **OLD:** Need separate _pct fields: `(bqx_max - rate) / rate`
- **NEW:** Calculate on-demand: `(bqx_max_index - rate_index) / rate_index`

### 4. Consistent with Target
- Target is `w60_bqx_return` (index-based)
- Features are now index-based
- All on same scale (around 100)

---

## Verification Strategy

After Stage 1.5.4 (rebuild), verify correctness:

### Test 1: Baseline Check
```sql
-- At baseline (2024-07-01 00:00:00), rate_index should be 100.00
SELECT ts_utc, rate_index, w15_bqx_max_index, w15_bqx_min_index
FROM bqx.bqx_audcad
WHERE ts_utc = '2024-07-01 00:00:00+00';

-- Expected: rate_index = 100.00 exactly
```

### Test 2: Range Check
```sql
-- Index values should be in reasonable range (around 100)
SELECT
    MIN(rate_index) as min_index,
    MAX(rate_index) as max_index,
    AVG(rate_index) as avg_index
FROM bqx.bqx_audcad;

-- Expected for AUDCAD: min ~97, max ~103, avg ~100
```

### Test 3: No Absolute Rate Columns
```sql
-- Verify schema uses rate_index, not rate
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'bqx_audcad' AND column_name LIKE '%rate%';

-- Expected: rate_index (NOT rate)
```

### Test 4: Cross-Pair Comparison
```sql
-- Verify all pairs are on same scale
SELECT
    'audcad' as pair,
    AVG(rate_index) as avg_index,
    STDDEV(rate_index) as stdev_index
FROM bqx.bqx_audcad
WHERE ts_utc BETWEEN '2024-07-01' AND '2024-08-01'

UNION ALL

SELECT
    'eurusd' as pair,
    AVG(rate_index) as avg_index,
    STDDEV(rate_index) as stdev_index
FROM bqx.bqx_eurusd
WHERE ts_utc BETWEEN '2024-07-01' AND '2024-08-01';

-- Expected: Both around 100, comparable volatility
```

---

## Next Steps (Stage 1.5.4)

### Stage 1.5.4.1: Drop BQX Tables (0.5h)
```bash
psql -f scripts/refactor/stage_1_5_4_1_drop_bqx_tables.sql
```

### Stage 1.5.4.2: Create BQX Tables (0.5h)
```bash
psql -f scripts/refactor/stage_1_5_4_2_create_bqx_tables_index_schema.sql
```

### Stage 1.5.4.3: Backfill BQX Tables (7h)
```bash
python3 scripts/backfill/backward_worker_index.py
```

---

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `backward_worker_index.py` | Index-based BQX calculation worker | 392 |
| `stage_1_5_4_1_drop_bqx_tables.sql` | Drop old bqx_* tables | 98 |
| `stage_1_5_4_2_create_bqx_tables_index_schema.sql` | Create new index-based schema | 144 |
| `stage_1_5_3_summary.md` | This summary document | - |

---

## Related Documentation

- [backward_worker_refactor_analysis.md](backward_worker_refactor_analysis.md) - Detailed refactor analysis
- [bqx_table_rebuild_strategy.md](bqx_table_rebuild_strategy.md) - Rebuild vs recalculate decision
- [bqx_index_commitment.md](bqx_index_commitment.md) - Confirmation that index data will be used
- [correlation_tables_comparison.md](correlation_tables_comparison.md) - Why correlation_* tables don't need recalc

---

## Impact Summary

**Schema Optimization:**
- ✅ Remove 24 _pct fields per table (24 × 28 = 672 total columns removed)
- ✅ Reduce storage: 77 columns → 53 columns (31% reduction)

**Cross-Pair Comparability:**
- ✅ All pairs centered at 100
- ✅ Direct comparison possible (e.g., AUDCAD vs EURUSD)

**ML Pipeline Consistency:**
- ✅ Features and target on same scale
- ✅ Simplified feature engineering
- ✅ Better model interpretability

**Calculation Performance:**
- ✅ No change (formulas identical)
- ✅ 7 hour backfill (parallel execution)

---

**Created:** 2025-11-10
**Author:** Claude Code
**Stage:** 1.5.3 (BQX Calculation Refactor)
**Status:** ✅ COMPLETE - Ready for Stage 1.5.4
