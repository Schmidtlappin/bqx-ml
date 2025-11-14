# Backward Worker Refactor Analysis (Stage 1.5.3)

**Date:** 2025-11-10
**File:** `/home/ubuntu/bqx-ml/scripts/backfill/backward_worker.py`
**Purpose:** Convert BQX calculations from absolute rates to rate_index

---

## Current Implementation (Absolute Rates)

### Data Source (Line 139-146)
```python
cur.execute(
    f"""
    SELECT time, close as rate
    FROM bqx.m1_{pair}
    WHERE time >= %s::timestamp - interval '{MAX_WINDOW} minutes' AND time < %s
    ORDER BY time
""",
    (start_date, end_date),
)
```

**Problem:** Fetches `close` (absolute rate), not `rate_index`

---

### BQX Calculation (Lines 54-76)
```python
def compute_backward_metrics(rates, window_size, current_idx):
    rate_t = rates[current_idx]
    past_rates = rates[current_idx - window_size : current_idx]

    # Cumulative return: Σ(i=1 to W)[rate(t-i) - rate(t)] / rate(t)
    cumulative_diffs = past_rates - rate_t
    bqx_return = np.sum(cumulative_diffs) / rate_t

    # Statistical measures
    bqx_max = np.max(past_rates)        ← Absolute rate
    bqx_min = np.min(past_rates)        ← Absolute rate
    bqx_avg = np.mean(past_rates)       ← Absolute rate
    bqx_stdev = np.std(past_rates, ddof=1)

    # Endpoint return
    bqx_endpoint = (past_rates[0] - rate_t) / rate_t

    return {
        "bqx_return": float(bqx_return),
        "bqx_max": float(bqx_max),          ← Stores absolute rate
        "bqx_min": float(bqx_min),          ← Stores absolute rate
        "bqx_avg": float(bqx_avg),          ← Stores absolute rate
        "bqx_stdev": float(bqx_stdev),
        "bqx_endpoint": float(bqx_endpoint),
    }
```

**Problems:**
1. Uses absolute rates (e.g., 0.91246 for AUDCAD)
2. Stores absolute rate values (bqx_max, bqx_min, bqx_avg)
3. Percentage calculations use `/ rate_t` normalization

---

### Aggregate Metrics (Lines 94-119)
```python
def compute_aggregate_metrics(rates, current_idx):
    rate_t = rates[current_idx]
    past_rates = rates[current_idx - 75 : current_idx]

    # Similar structure as compute_backward_metrics
    agg_bqx_max = np.max(past_rates)    ← Absolute rate
    agg_bqx_min = np.min(past_rates)    ← Absolute rate
    agg_bqx_avg = np.mean(past_rates)   ← Absolute rate
    agg_bqx_range = (agg_bqx_max - agg_bqx_min) / rate_t
    agg_bqx_volatility = agg_bqx_stdev / rate_t
```

**Problems:** Same as compute_backward_metrics

---

### Output Columns (Lines 221-243)
```python
columns = ["ts_utc", "rate"]
for window in WINDOWS:
    columns.extend([
        f"w{window}_bqx_return",
        f"w{window}_bqx_max",      ← Absolute rate
        f"w{window}_bqx_min",      ← Absolute rate
        f"w{window}_bqx_avg",      ← Absolute rate
        f"w{window}_bqx_stdev",
        f"w{window}_bqx_endpoint",
    ])
columns.extend([
    "agg_bqx_return",
    "agg_bqx_max",                 ← Absolute rate
    "agg_bqx_min",                 ← Absolute rate
    "agg_bqx_avg",                 ← Absolute rate
    "agg_bqx_stdev",
    "agg_bqx_range",
    "agg_bqx_volatility",
])
```

**Problem:** Column names reference absolute rates, not indexes

---

## New Implementation (Rate Index)

### Data Source (Modified)
```python
cur.execute(
    f"""
    SELECT time, rate_index
    FROM bqx.m1_{pair}
    WHERE time >= %s::timestamp - interval '{MAX_WINDOW} minutes' AND time < %s
    ORDER BY time
""",
    (start_date, end_date),
)
```

**Change:** Fetch `rate_index` (populated in Stage 1.5.2) instead of `close`

---

### BQX Calculation (Modified)
```python
def compute_backward_metrics(rate_indexes, window_size, current_idx):
    """
    Compute backward-looking metrics using rate_index

    Args:
        rate_indexes: numpy array of historical rate_index values (around 100)
        window_size: number of minutes in window
        current_idx: index of current timestamp

    Returns:
        dict with backward metrics (all in index form)
    """
    index_t = rate_indexes[current_idx]
    past_indexes = rate_indexes[current_idx - window_size : current_idx]

    # Cumulative return: Σ(i=1 to W)[index(t-i) - index(t)] / index(t)
    # Formula structure unchanged - just using index instead of rate
    cumulative_diffs = past_indexes - index_t
    bqx_return = np.sum(cumulative_diffs) / index_t

    # Statistical measures (now in index space, around 100)
    bqx_max_index = np.max(past_indexes)      ← Index value
    bqx_min_index = np.min(past_indexes)      ← Index value
    bqx_avg_index = np.mean(past_indexes)     ← Index value
    bqx_stdev_index = np.std(past_indexes, ddof=1)

    # Endpoint return
    bqx_endpoint = (past_indexes[0] - index_t) / index_t

    return {
        "bqx_return": float(bqx_return),
        "bqx_max_index": float(bqx_max_index),    ← Now stores index
        "bqx_min_index": float(bqx_min_index),    ← Now stores index
        "bqx_avg_index": float(bqx_avg_index),    ← Now stores index
        "bqx_stdev_index": float(bqx_stdev_index),
        "bqx_endpoint": float(bqx_endpoint),
    }
```

**Key Changes:**
1. Rename `rates` → `rate_indexes` (clarity)
2. Rename `rate_t` → `index_t` (clarity)
3. **Column names:** `bqx_max` → `bqx_max_index`
4. **Values stored:** Index values (around 100) instead of absolute rates

---

### Output Columns (Modified)
```python
columns = ["ts_utc", "rate_index"]  # ← Changed from "rate"
for window in WINDOWS:
    columns.extend([
        f"w{window}_bqx_return",
        f"w{window}_bqx_max_index",     ← Added "_index" suffix
        f"w{window}_bqx_min_index",     ← Added "_index" suffix
        f"w{window}_bqx_avg_index",     ← Added "_index" suffix
        f"w{window}_bqx_stdev_index",   ← Added "_index" suffix
        f"w{window}_bqx_endpoint",
    ])
columns.extend([
    "agg_bqx_return",
    "agg_bqx_max_index",                ← Added "_index" suffix
    "agg_bqx_min_index",                ← Added "_index" suffix
    "agg_bqx_avg_index",                ← Added "_index" suffix
    "agg_bqx_stdev_index",              ← Added "_index" suffix
    "agg_bqx_range",                    # Range formula stays same
    "agg_bqx_volatility",               # Volatility formula stays same
])
```

---

## Mathematical Equivalence

### Percentage Changes (Scale-Independent)
```
Old (absolute rates):
bqx_return = Σ[(rate(t-i) - rate(t)) / rate(t)]

New (rate index):
bqx_return = Σ[(index(t-i) - index(t)) / index(t)]

Proof of equivalence:
index = (rate / baseline) * 100
So: (index_A - index_B) / index_B
  = ((rate_A/baseline)*100 - (rate_B/baseline)*100) / ((rate_B/baseline)*100)
  = (rate_A - rate_B) / rate_B  ✓ SAME

Therefore: Percentage change calculations are IDENTICAL
```

### Statistical Measures (Scale-Dependent)
```
Old (absolute rates):
bqx_max = 0.92632 (absolute rate for AUDCAD)

New (rate index):
bqx_max_index = 101.52 (index value)

Why the change matters:
- Index values are cross-pair comparable (all centered at 100)
- Example: bqx_max_index = 101.52 means "1.52% above baseline"
- This is more intuitive than absolute rate 0.92632
```

---

## Changes Summary

| Aspect | Old (Absolute Rates) | New (Rate Index) |
|--------|---------------------|------------------|
| **Data source** | `close as rate` | `rate_index` |
| **Variable naming** | `rate_t`, `past_rates` | `index_t`, `past_indexes` |
| **Column prefix** | `rate`, `bqx_max` | `rate_index`, `bqx_max_index` |
| **Stored values** | 0.91246 (absolute) | 100.00 (index) |
| **Formulas** | `(past - current) / current` | `(past - current) / current` (SAME) |
| **Cross-pair comparable** | ❌ No (different scales) | ✅ Yes (all around 100) |

---

## Files to Modify

### 1. backward_worker.py
- Change data fetch: `rate_index` instead of `close`
- Rename variables: `rates` → `rate_indexes`, `rate_t` → `index_t`
- Update return keys: `bqx_max` → `bqx_max_index`
- Update column names: Add `_index` suffix to max/min/avg/stdev

### 2. Database Schema (Stage 1.5.4.2)
```sql
CREATE TABLE bqx.bqx_audcad (
    ts_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    rate_index DOUBLE PRECISION,     ← Changed from "rate"

    -- Window metrics (w15, w30, w45, w60, w75)
    w15_bqx_return DOUBLE PRECISION,
    w15_bqx_max_index DOUBLE PRECISION,    ← Added "_index"
    w15_bqx_min_index DOUBLE PRECISION,    ← Added "_index"
    w15_bqx_avg_index DOUBLE PRECISION,    ← Added "_index"
    w15_bqx_stdev_index DOUBLE PRECISION,  ← Added "_index"
    w15_bqx_endpoint DOUBLE PRECISION,

    -- ... repeat for w30, w45, w60, w75

    -- Aggregate metrics
    agg_bqx_return DOUBLE PRECISION,
    agg_bqx_max_index DOUBLE PRECISION,    ← Added "_index"
    agg_bqx_min_index DOUBLE PRECISION,    ← Added "_index"
    agg_bqx_avg_index DOUBLE PRECISION,    ← Added "_index"
    agg_bqx_stdev_index DOUBLE PRECISION,  ← Added "_index"
    agg_bqx_range DOUBLE PRECISION,
    agg_bqx_volatility DOUBLE PRECISION,

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

**Removed fields (from old schema):**
- 24 `_pct` fields (no longer needed with index)
- Example: `w15_bqx_max_pct` - percentage was `(bqx_max - rate) / rate`
- With index: just use `(bqx_max_index - rate_index) / rate_index` directly

---

## Percentage Normalization Removal

### Old Approach (Percentage Fields)
```sql
-- Old schema had both absolute and percentage fields
w15_bqx_max DOUBLE PRECISION,           -- Absolute: 0.92632
w15_bqx_max_pct DOUBLE PRECISION,       -- Percentage: 0.0152 (1.52%)

-- Calculated as:
w15_bqx_max_pct = (w15_bqx_max - rate) / rate
```

### New Approach (Index Only)
```sql
-- New schema uses index only
rate_index DOUBLE PRECISION,            -- 100.00 at baseline
w15_bqx_max_index DOUBLE PRECISION,     -- 101.52 (1.52% above baseline)

-- Percentage change calculation (if needed):
percentage = (w15_bqx_max_index - rate_index) / rate_index
-- Example: (101.52 - 100.00) / 100.00 = 0.0152 (1.52%)
```

**Advantages:**
1. **Fewer columns:** Remove 24 _pct fields
2. **On-demand calculation:** Calculate percentages in queries when needed
3. **Cleaner schema:** One index field instead of three (absolute, index, pct)

---

## Verification Strategy

After modifying backward_worker.py, verify correctness:

### Test 1: Baseline Date Check
```sql
-- At baseline date (2024-07-01 00:00:00), rate_index should be ~100
SELECT
    ts_utc,
    rate_index,
    w15_bqx_max_index,
    w15_bqx_min_index
FROM bqx.bqx_audcad
WHERE ts_utc = '2024-07-01 00:00:00+00';

-- Expected: All index values near 100.00
```

### Test 2: Range Check
```sql
-- Index values should be within reasonable range
SELECT
    MIN(rate_index) as min_index,
    MAX(rate_index) as max_index,
    AVG(rate_index) as avg_index
FROM bqx.bqx_audcad;

-- Expected for AUDCAD: 97-102 range (typical forex volatility)
```

### Test 3: Cross-Pair Comparison
```sql
-- Index values should be comparable across pairs
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

-- Expected: Both pairs around 100, comparable volatility
```

---

## Implementation Timeline

**Stage 1.5.3: BQX Calculation Refactor (1 hour)**

1. Modify backward_worker.py (0.5h)
   - Change data fetch to use rate_index
   - Update variable names and column names
   - Add _index suffixes

2. Test modifications (0.25h)
   - Run on single pair/month
   - Verify output values
   - Check column names

3. Document changes (0.25h)
   - Update docstrings
   - Update comments
   - Create migration notes

**Stage 1.5.4: BQX Table Recalculation (8 hours)**

1. Drop existing bqx_* tables (0.5h)
2. Create new schema with index fields (0.5h)
3. Run modified backward_worker.py backfill (7h)

---

## Next Steps

1. ✅ Document analysis complete
2. 🔜 Create modified backward_worker.py
3. 🔜 Create BQX table schema (index-based)
4. 🔜 Test on single pair
5. 🔜 Full backfill (Stage 1.5.4)

---

**Created:** 2025-11-10
**Author:** Claude Code
**Status:** Analysis Complete - Ready for Implementation
