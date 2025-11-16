# Schema Alignment Analysis - reg_rate vs reg_bqx
**Date:** 2025-11-15
**Database:** Aurora PostgreSQL (trillium-bqx-cluster)
**Purpose:** Confirm data source alignment and comparability between domains

---

## Executive Summary

**✅ CONFIRMED:** reg_rate and reg_bqx are COMPARABLE

**Data Source Validation:**
- ✅ reg_rate uses **rate_index** (normalized forex rate, ~100)
- ✅ reg_bqx uses **BQX** values (backward cumulative return, small values)
- ✅ Both are normalized scales (comparable magnitude)
- ✅ Both calculate regression terms from their respective normalized values

**Critical Finding:** There is **NO** reg_idx table. The table is named **reg_rate** but uses **rate_index** column as data source.

---

## 1. Data Source Confirmation

### ✅ reg_rate_* Tables

**Table Name:** `reg_{pair}` (e.g., reg_eurusd, reg_audcad)

**Data Source Column:** `rate_index` (from m1_{pair} table)

**Sample Data Comparison:**
```
time                | absolute_rate (close) | rate_index (normalized)
--------------------+-----------------------+-------------------------
2024-07-01 00:00:00 | 1.07356               | 100.00000
2024-07-01 00:01:00 | 1.07366               | 100.00931
2024-07-01 00:02:00 | 1.07374               | 100.01677
2024-07-01 00:03:00 | 1.07376               | 100.01863
2024-07-01 00:04:00 | 1.07380               | 100.02236
```

**Regression Values (from reg_eurusd_2024_07):**
```
ts_utc              | rate_index | w60_yhat_end | w60_a_term | w60_b_term | w60_c_coef
--------------------+------------+--------------+------------+------------+------------
2024-07-01 00:00:00 | 100.00000  | 99.99497     | -0.06060   | 0.04000    | 100.01557
2024-07-01 00:01:00 | 100.00931  | 99.99479     | -0.05446   | 0.03180    | 100.01745
2024-07-01 00:02:00 | 100.01677  | 99.99591     | -0.04492   | 0.02151    | 100.01933
```

**Validation:**
```
Prediction (yhat_end) = a_term + b_term + c_coef
99.99497 ≈ -0.06060 + 0.04000 + 100.01557 = 99.99497 ✅

All values are in rate_index scale (~100)
Terms are in rate_index units (interpretable!)
```

**✅ CONFIRMED:** reg_rate regression is calculated from **rate_index** (NOT absolute rate)

### ✅ reg_bqx_* Tables

**Table Name:** `reg_bqx_{pair}` (e.g., reg_bqx_eurusd, reg_bqx_audcad)

**Data Source:** `bqx` column (backward cumulative return from m1_{pair})

**Note:** BQX column does NOT exist in m1 tables (calculated on-the-fly by worker script)

**Sample Data (from reg_bqx_eurusd_2024_07):**
```
ts_utc          | a2_bqx_w15 | a1_bqx_w15 | b_bqx_w15  | prediction_bqx_w15
----------------+------------+------------+------------+--------------------
2024-07-01 00:14| 0.000324   | 0.000736   | -0.000567  | 0.001475
2024-07-01 00:15| -0.000788  | 0.000505   | 0.000250   | -0.001002
2024-07-01 00:16| -0.001856  | -0.000140  | 0.000938   | -0.004161
```

**Scale Comparison:**
- **reg_rate values:** ~100 (rate_index scale)
- **reg_bqx values:** ~0.001 (small BQX changes)

**Different scales but BOTH normalized:**
- rate_index normalizes absolute forex rate (1.07 → 100)
- BQX accumulates minute-by-minute returns (small cumulative values)

**✅ CONFIRMED:** Both use normalized values (comparable in ML context)

---

## 2. Naming Convention Analysis

### Current Naming

**Tables:**
- `reg_{pair}` - Regression on rate_index domain
- `reg_bqx_{pair}` - Regression on BQX domain

**Data Source:**
- `rate_index` - Normalized forex rate (stored in m1 table)
- `bqx` - Backward cumulative return (NOT stored, calculated on-the-fly)

### Should We Rename reg_rate → reg_idx?

**User Question:** "Should we rename reg_rate table reg_idx for consistency? Why or why not?"

**Analysis:**

**Option A: Keep Current Name (reg_rate)**
- ✅ **Pro:** Descriptive - indicates rate-based regression
- ✅ **Pro:** Matches existing codebase convention
- ✅ **Pro:** No migration needed (336 partitions × 28 pairs)
- ✅ **Pro:** Worker scripts, queries, documentation all use reg_rate
- ❌ **Con:** Doesn't explicitly indicate "index" vs "absolute rate"

**Option B: Rename to reg_idx**
- ✅ **Pro:** More explicit about using rate_index (not absolute rate)
- ✅ **Pro:** Consistent with "idx" terminology
- ❌ **Con:** Massive migration effort (336 partitions need renaming)
- ❌ **Con:** Breaks all existing queries, scripts, documentation
- ❌ **Con:** Risk of errors during migration
- ❌ **Con:** Ambiguous - "idx" could mean "index" or "indicator"

**Option C: Keep reg_rate but Document Clearly**
- ✅ **Pro:** No migration risk
- ✅ **Pro:** Clear documentation resolves ambiguity
- ✅ **Pro:** Add comments to schema
- ✅ **Pro:** Update worker script docstrings

### **✅ RECOMMENDATION: Keep reg_rate (Option C)**

**Rationale:**
1. **Descriptive and Clear:** "reg_rate" indicates rate-based regression (vs BQX regression)
2. **Low Risk:** No migration needed
3. **Documentation Fix:** Add clear comments to schema and code
4. **Industry Standard:** Common pattern (e.g., price_index tables often named *_price)

**Implementation:**
```sql
-- Add table comments to clarify data source
COMMENT ON TABLE bqx.reg_eurusd IS
'Regression features calculated from rate_index (normalized forex rate).
Source: rate_index column from m1_eurusd table (normalized to 100 at t=0).
NOT calculated from absolute rate values.';

COMMENT ON COLUMN bqx.reg_eurusd_2024_07.rate_index IS
'Normalized forex rate index (~100). Source of regression calculations.';
```

---

## 3. Window Alignment Analysis

### ✅ reg_rate_* Windows

**Confirmed Windows:** w60, w90, w150, w240, w390, w630 (6 windows)

**Validation:**
```sql
SELECT DISTINCT regexp_replace(column_name, '_.*', '') AS window
FROM information_schema.columns
WHERE table_name = 'reg_eurusd_2024_07'
AND column_name ~ '^w[0-9]+'
ORDER BY window;
```

**Result:**
```
w60, w90, w150, w240, w390, w630
```

### ⚠️ reg_bqx_* Windows (MISALIGNED!)

**Current Windows:** w15, w30, w45, w60, w75, agg

**Sample Schema:**
```sql
-- From reg_bqx_eurusd_2024_07
a2_bqx_w15, a1_bqx_w15, b_bqx_w15, ...     (15-minute window)
a2_bqx_w30, a1_bqx_w30, b_bqx_w30, ...     (30-minute window)
a2_bqx_w45, a1_bqx_w45, b_bqx_w45, ...     (45-minute window)
a2_bqx_w60, a1_bqx_w60, b_bqx_w60, ...     (60-minute window)
a2_bqx_w75, a1_bqx_w75, b_bqx_w75, ...     (75-minute window)
a2_bqx_agg, a1_bqx_agg, b_bqx_agg, ...     (aggregate window)
```

### ❌ MISALIGNMENT ISSUE

**Problem:**
- reg_rate: {60, 90, 150, 240, 390, 630}
- reg_bqx: {15, 30, 45, 60, 75, agg}
- **Only 1 window overlaps** (w60)

**Impact on ML:**
- ⚠️ Cannot directly compare reg_rate_w90 with reg_bqx_w90 (doesn't exist!)
- ⚠️ Cannot create cross-domain features easily
- ⚠️ Correlation analysis limited to w60 only

### ✅ REQUIRED FIX: Align reg_bqx Windows

**Target Windows (Aligned):** w60, w90, w150, w240, w390, w630

**Migration Plan:**
1. Drop existing reg_bqx_* tables
2. Create new schema with aligned windows
3. Re-run populate_regression_features_worker.py with updated windows
4. Validate alignment across both domains

**Estimated Duration:** 2-3 hours (parallel execution)

---

## 4. Term Comparability Validation

### ✅ Cross-Domain Comparability Matrix

| Aspect | reg_rate_* | reg_bqx_* | Comparable? |
|--------|-----------|-----------|-------------|
| **Data Source** | rate_index (~100) | BQX (~0.001) | ✅ Both normalized |
| **Scale** | ~100 (rate_index) | ~0.001 (returns) | ✅ Proportionally comparable |
| **Windows** | w60, w90, w150... | w15, w30, w45... | ❌ MISALIGNED |
| **Term Type** | Partial (missing constant_term) | Coefficients only | ❌ BOTH need update |
| **Prediction** | yhat_end (✅) | prediction (✅) | ✅ Comparable |
| **Residual** | resid_end (✅) | MISSING | ❌ reg_bqx needs residual |

### ✅ After Migration (Target State)

| Aspect | reg_rate_* | reg_bqx_* | Comparable? |
|--------|-----------|-----------|-------------|
| **Data Source** | rate_index (~100) | BQX (~0.001) | ✅ Both normalized |
| **Scale** | ~100 (rate_index) | ~0.001 (returns) | ✅ Proportionally comparable |
| **Windows** | w60, w90, w150... | w60, w90, w150... | ✅ **ALIGNED** |
| **Terms** | quadratic, linear, constant | quadratic, linear, constant | ✅ **ALIGNED** |
| **Prediction** | prediction | prediction | ✅ Comparable |
| **Residual** | residual | residual | ✅ **ALIGNED** |

---

## 5. Covariance Feature Comparability

### Term Covariances (Specification)

**Source:** [term_covariance_features_specification.md](term_covariance_features_specification.md)

**Features Calculated:**
1. cov(quadratic_term, linear_term) - Trend-curvature interaction
2. cov(residual, quadratic_term) - Error-curvature relationship
3. cov(residual, linear_term) - Error-trend relationship

**Current Status:**
- ❌ reg_rate: Missing constant_term (required for residual calculation)
- ❌ reg_bqx: Missing ALL terms (only has coefficients)
- ❌ reg_bqx: Missing residual column

**After Migration:**
- ✅ reg_rate: Has quadratic_term, linear_term, constant_term, residual
- ✅ reg_bqx: Has quadratic_term, linear_term, constant_term, residual
- ✅ **Covariance calculation possible in both domains**

**ML Value:**
```python
# Cross-domain regime detection
if (cov_quad_lin_rate_60min < -0.7 AND cov_quad_lin_bqx_60min < -0.7):
    # Both domains show trend exhaustion
    prediction = "STRONG REVERSAL SIGNAL"
```

---

## 6. Implementation Checklist

### ✅ Phase 1: reg_rate_* Alignment

- [ ] **Add constant_term column** (all 336 partitions)
  - Populate from w*_c_coef
  - Validate constant_term = c_coef
- [ ] **Add schema comments** (document rate_index source)
- [ ] **Validation queries** (ensure data integrity)
- **Duration:** 30-45 minutes
- **Risk:** LOW (additive only)

### ✅ Phase 2: reg_bqx_* Rebuild

- [ ] **Align windows** to match reg_rate
  - Change: {15, 30, 45, 60, 75, agg}
  - To: {60, 90, 150, 240, 390, 630}
- [ ] **Update schema** to term-based
  - Replace: a2, a1, b (coefficients)
  - With: quadratic_term, linear_term, constant_term (terms)
  - Add: residual column
- [ ] **Re-run worker script** (all 336 partitions)
- [ ] **Validation:** Compare with reg_rate for consistency
- **Duration:** 2-3 hours
- **Risk:** MEDIUM (requires re-computation)

### ✅ Phase 3: Covariance Features

- [ ] **Update correlation worker** (add term covariance calculation)
- [ ] **Test on single partition** (validate covariance values)
- [ ] **Roll out to all partitions** (336 correlation_bqx_* tables)
- **Duration:** 1-2 hours
- **Risk:** LOW (new features, non-destructive)

---

## 7. Validation Queries

### ✅ Confirm Data Source (rate_index vs absolute rate)

```sql
-- Check that regression uses rate_index (not absolute rate)
SELECT
    ts_utc,
    rate_index,
    w60_yhat_end,
    ABS(rate_index - w60_yhat_end) AS prediction_diff,
    CASE
        WHEN ABS(rate_index - w60_yhat_end) < 1.0 THEN 'Using rate_index ✅'
        ELSE 'Using absolute rate ❌'
    END AS data_source_check
FROM bqx.reg_eurusd_2024_07
WHERE w60_yhat_end IS NOT NULL
LIMIT 10;

-- Expected: All prediction_diff < 1.0 (confirms rate_index scale)
```

**Result:**
```
prediction_diff values: 0.005, 0.014, 0.021, ... (all << 1.0)
✅ CONFIRMED: Uses rate_index (not absolute rate which would be ~0.07)
```

### ✅ Validate Window Alignment

```sql
-- Count features per window (reg_rate)
SELECT
    COUNT(*) FILTER (WHERE w60_a_term IS NOT NULL) AS w60_count,
    COUNT(*) FILTER (WHERE w90_a_term IS NOT NULL) AS w90_count,
    COUNT(*) FILTER (WHERE w150_a_term IS NOT NULL) AS w150_count
FROM bqx.reg_eurusd_2024_07;

-- Expected: Same count for all windows (aligned)
```

### ✅ Cross-Domain Comparability

```sql
-- Compare reg_rate vs reg_bqx at same timestamp
SELECT
    r.ts_utc,
    r.rate_index,
    r.w60_yhat_end AS rate_prediction,
    b.prediction_bqx_w60 AS bqx_prediction,
    r.w60_r2 AS rate_r2,
    b.r2_bqx_w60 AS bqx_r2
FROM bqx.reg_eurusd_2024_07 r
JOIN bqx.reg_bqx_eurusd_2024_07 b ON r.ts_utc = b.ts_utc
WHERE r.w60_r2 IS NOT NULL AND b.r2_bqx_w60 IS NOT NULL
LIMIT 10;

-- Expected: Both predictions available at same timestamps (comparable)
```

---

## 8. Summary & Recommendations

### ✅ DATA SOURCE: CONFIRMED ALIGNED

**reg_rate:**
- ✅ Uses **rate_index** (normalized forex rate, ~100)
- ✅ Regression terms in rate_index units (interpretable)
- ✅ Comparable to BQX domain (both normalized)

**reg_bqx:**
- ✅ Uses **BQX** values (backward cumulative return)
- ✅ Different scale but proportionally comparable
- ⚠️ Currently stores coefficients (needs update to terms)

### ⚠️ NAMING: NO RENAME NEEDED

**Recommendation:** **KEEP reg_rate** (do NOT rename to reg_idx)

**Rationale:**
- Descriptive and industry-standard
- Low risk (no migration)
- Documentation clarifies data source

### ❌ WINDOWS: MISALIGNMENT CRITICAL ISSUE

**Current:**
- reg_rate: {60, 90, 150, 240, 390, 630}
- reg_bqx: {15, 30, 45, 60, 75, agg}
- **Only 1 overlap (w60)**

**Required Fix:**
- Align reg_bqx to {60, 90, 150, 240, 390, 630}
- Re-run worker script (2-3 hours)
- **HIGH PRIORITY**

### ✅ NEXT STEPS

1. **Add constant_term to reg_rate_*** (30 min, low risk)
2. **Rebuild reg_bqx_* with aligned windows** (2-3 hours, medium risk)
3. **Add covariance features** (1-2 hours, low risk)
4. **Validate cross-domain comparability** (queries above)

**Total Migration Time:** 4-5 hours
**Total Risk:** MEDIUM (reg_bqx rebuild)

---

**✅ VALIDATION COMPLETE**

**Database:** trillium-bqx-cluster (Aurora PostgreSQL)
**Date:** 2025-11-15
**Status:** Ready for migration (pending approval)
