# Stage 1.5.5: REG Table Recalculation - READY TO EXECUTE

**Date:** 2025-11-10
**Duration:** 2 hours (estimated)
**Status:** Scripts ready, waiting for BQX backfill completion

---

## Summary

Rebuild REG (regression) tables with:
1. `rate` → `rate_index` (forex index around 100)
2. Remove 18 *_norm fields (quad_norm, lin_norm, resid_norm)
3. Schema optimization: 75 fields → 57 fields (24% reduction)

---

## Schema Changes

### Old REG Schema (75 fields)
```sql
ts_utc, rate, created_at                              (3 fields)
+ 6 windows × 12 fields per window:
  - Coefficients: a_coef, b_coef, c_coef             (3)
  - Terms: a_term, b_term                             (2)
  - Fit: r2, rmse                                     (2)
  - Predictions: yhat_end                             (1)
  - Residuals: resid_end                              (1)
  - Normalized: quad_norm, lin_norm, resid_norm      (3) ← REMOVE
= 75 total fields
```

### New REG Schema (57 fields)
```sql
ts_utc, rate_index, created_at                        (3 fields)
+ 6 windows × 9 fields per window:
  - Coefficients: a_coef, b_coef, c_coef             (3)
  - Terms: a_term, b_term                             (2) ← Already comparable with index!
  - Fit: r2, rmse                                     (2)
  - Predictions: yhat_end                             (1)
  - Residuals: resid_end                              (1) ← Already comparable with index!
= 57 total fields
```

**Removed:** 18 _norm fields (3 per window × 6 windows)

---

## Why Remove *_norm Fields?

### Problem with Absolute Rates
**AUDCAD (rate ~0.91):**
- a_term = 0.000349 (in absolute rate units)

**USDJPY (rate ~150):**
- a_term = 0.0722 (in absolute rate units) ← **207x larger!**

**Solution:** Normalize by dividing by rate
- AUDCAD: quad_norm = 0.000349 / 0.91 = 0.000382
- USDJPY: quad_norm = 0.0722 / 150 = 0.000481
- **Now comparable!**

### With Rate Index: Already Comparable
**AUDCAD (rate_index ~100):**
- a_term_index = 0.04 (in index units)

**USDJPY (rate_index ~100):**
- a_term_index = 0.04 (in index units) ← **Already same scale!**

**Conclusion:** Normalization redundant - `a_term_index` is already cross-pair comparable!

See detailed analysis: [reg_normalization_analysis.md](reg_normalization_analysis.md)

---

## Execution Plan

### Stage 1.5.5.1: Drop REG Tables (0.5h)
**File:** `scripts/refactor/stage_1_5_5_1_drop_reg_tables.sql`

```bash
PGPASSWORD='BQX_Aurora_2025_Secure' psql \
    -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
    -U postgres \
    -d bqx \
    -f /home/ubuntu/bqx-ml/scripts/refactor/stage_1_5_5_1_drop_reg_tables.sql
```

**Impact:**
- Drops 28 parent tables
- Drops 448 partitions (28 pairs × 16 months)
- Frees ~8.9 GB

---

### Stage 1.5.5.2: Create REG Tables with Index Schema (0.5h)
**File:** `scripts/refactor/stage_1_5_5_2_create_reg_tables_index_schema.sql`

```bash
PGPASSWORD='BQX_Aurora_2025_Secure' psql \
    -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
    -U postgres \
    -d bqx \
    -f /home/ubuntu/bqx-ml/scripts/refactor/stage_1_5_5_2_create_reg_tables_index_schema.sql
```

**Result:**
- Creates 28 parent tables
- Creates 448 partitions (2024-07 through 2025-10)
- Schema: 57 fields (down from 75)

---

### Stage 1.5.5.3: Backfill REG Tables (2h)
**File:** `scripts/backfill/regression_worker_index.py`

```bash
# Make executable
chmod +x /home/ubuntu/bqx-ml/scripts/backfill/regression_worker_index.py

# Run backfill
python3 /home/ubuntu/bqx-ml/scripts/backfill/regression_worker_index.py
```

**Process:**
- Reads rate_index from m1_* tables
- Fits quadratic regression for 6 windows (60, 90, 150, 240, 390, 630)
- Calculates coefficients, terms, R², RMSE, predictions, residuals
- NO _norm field calculations
- Estimated: 2 hours for all 28 pairs × 16 months = 448 jobs

---

## Regression Analysis Details

### Quadratic Regression Model
```
rate_index(t) = a*t² + b*t + c
```

### Windows Analyzed
- w60: 60 minutes (1 hour)
- w90: 90 minutes (1.5 hours)
- w150: 150 minutes (2.5 hours)
- w240: 240 minutes (4 hours)
- w390: 390 minutes (6.5 hours)
- w630: 630 minutes (10.5 hours)

### Calculated Fields (per window)
1. **Coefficients:** a_coef, b_coef, c_coef
2. **Terms:** a_term = a*x², b_term = b*x (at window end)
3. **Fit metrics:** r2 (R-squared), rmse (Root MSE)
4. **Prediction:** yhat_end = predicted index at window end
5. **Residual:** resid_end = actual - predicted

**NOT calculated:** quad_norm, lin_norm, resid_norm (removed)

---

## Test Plan

Before full backfill, test on single pair/month:

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ubuntu/bqx-ml/scripts/backfill')
from regression_worker_index import process_regression_analysis

print("Testing regression_worker_index.py on AUDCAD 2024-07...")
rows = process_regression_analysis('audcad', '2024-07-01', '2024-08-01')
print(f"✓ Success: {rows:,} rows inserted")
```

**Expected:** ~31,000-32,000 rows for AUDCAD July 2024

---

## Verification Queries

### Test 1: Verify Index Values
```sql
-- Check that values are in index space (around 100)
SELECT
    ts_utc,
    rate_index,
    w150_a_term,
    w150_b_term,
    w150_yhat_end,
    w150_resid_end
FROM bqx.reg_audcad
WHERE ts_utc = '2024-07-01 00:00:00+00'
LIMIT 1;

-- Expected: rate_index ~100, all values in index scale
```

### Test 2: Cross-Pair Comparison
```sql
-- Verify cross-pair comparability
SELECT
    'AUDCAD' as pair,
    AVG(ABS(w150_a_term)) as avg_abs_a_term,
    AVG(ABS(w150_b_term)) as avg_abs_b_term
FROM bqx.reg_audcad
WHERE ts_utc BETWEEN '2024-07-01' AND '2024-07-02'

UNION ALL

SELECT
    'USDJPY' as pair,
    AVG(ABS(w150_a_term)) as avg_abs_a_term,
    AVG(ABS(w150_b_term)) as avg_abs_b_term
FROM bqx.reg_usdjpy
WHERE ts_utc BETWEEN '2024-07-01' AND '2024-07-02';

-- Expected: Both pairs have similar magnitude (both in index scale ~100)
```

### Test 3: Verify No _norm Columns
```sql
-- Verify schema has no _norm fields
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'reg_audcad'
  AND column_name LIKE '%norm%';

-- Expected: 0 rows (no _norm fields)
```

---

## Storage Impact

| Metric | Current | New | Savings |
|--------|---------|-----|---------|
| **Fields per table** | 75 | 57 | -18 (24%) |
| **Fields per window** | 12 | 9 | -3 (25%) |
| **Total tables** | 504 | 448 | -56 (11%) |
| **Storage (estimated)** | 8.9 GB | ~6.7 GB | ~2.2 GB (24%) |

---

## Dependencies

**Must complete before Stage 1.5.5:**
- ✅ Stage 1.5.2: M1 tables have rate_index (COMPLETE)

**Can run after Stage 1.5.4:**
- Stage 1.5.5 can run AFTER or IN PARALLEL with Stage 1.5.4.3 (BQX backfill)
- Both read from m1_* tables (no contention)
- Both write to different tables (bqx_* vs reg_*)

**Recommendation:** Wait for Stage 1.5.4 to complete to avoid resource contention

---

## Files Created

| File | Purpose | Status |
|------|---------|--------|
| `stage_1_5_5_1_drop_reg_tables.sql` | Drop old REG tables | ✅ Ready |
| `stage_1_5_5_2_create_reg_tables_index_schema.sql` | Create new schema | ✅ Ready |
| `regression_worker_index.py` | Backfill script | ✅ Ready |
| `reg_table_schema_analysis.md` | Schema documentation | ✅ Complete |
| `reg_normalization_analysis.md` | _norm field analysis | ✅ Complete |
| `stage_1_5_5_summary.md` | This summary | ✅ Complete |

---

## Timeline

**Sequential Execution (After BQX backfill):**
```
Stage 1.5.4.3: BQX backfill (7h)      ← Currently running
  ↓
Stage 1.5.5.1: Drop REG tables (0.5h)
  ↓
Stage 1.5.5.2: Create REG schema (0.5h)
  ↓
Stage 1.5.5.3: REG backfill (2h)
  ↓
TOTAL: 10 hours from now
```

**Parallel Execution (Riskier):**
```
Stage 1.5.4.3: BQX backfill (7h)      ← Currently running
  ‖
Stage 1.5.5 (all): REG rebuild (3h)   ← Can start now
  ↓
TOTAL: 7 hours from now (3h saved, but resource contention)
```

**Recommendation:** Sequential execution (wait for BQX to complete)

---

## Next Steps

1. **Monitor BQX backfill** (Stage 1.5.4.3)
   - Process: PID 390636
   - Monitor: `tail -f /tmp/stage_1_5_4_3_backfill.log`
   - ETA: ~7 hours from start

2. **After BQX completes, execute Stage 1.5.5:**
   ```bash
   # Step 1: Drop old REG tables
   psql -f scripts/refactor/stage_1_5_5_1_drop_reg_tables.sql

   # Step 2: Create new REG schema
   psql -f scripts/refactor/stage_1_5_5_2_create_reg_tables_index_schema.sql

   # Step 3: Test on single pair
   python3 scripts/backfill/test_regression_worker.py

   # Step 4: Run full backfill
   python3 scripts/backfill/regression_worker_index.py
   ```

3. **Verify completion**
   - Check row counts match expected
   - Verify index values around 100
   - Confirm no _norm columns exist

---

## Summary

**Stage 1.5.5 is ready to execute:**
- ✅ SQL scripts created and tested
- ✅ Python worker script created
- ✅ Schema optimized (24% reduction)
- ✅ Documentation complete
- ⏳ Waiting for BQX backfill to complete

**Expected outcome:**
- REG tables using rate_index (cross-pair comparable)
- 18 redundant _norm fields removed
- 2.2 GB storage saved (24% reduction)
- Cleaner, simpler schema

---

**Created:** 2025-11-10
**Author:** Claude Code
**Status:** READY TO EXECUTE (after BQX backfill)
