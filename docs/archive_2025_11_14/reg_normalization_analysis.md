# REG Table Normalization Analysis: _norm Fields With Rate Index

**Date:** 2025-11-10
**Question:** Are `*_quad_norm`, `*_lin_norm`, and `*_resid_norm` fields necessary when using rate_index?
**Hypothesis:** With rate_index, `_a_term`, `_b_term`, and `_resid_end` are already normalized and cross-pair comparable.

---

## Current Normalization Formula (Verified)

```sql
quad_norm = a_term / rate
lin_norm = b_term / rate
resid_norm = resid_end / rate
```

**Purpose:** Make regression terms comparable across pairs with vastly different absolute rate scales.

---

## Problem: Absolute Rate Scale Differences

### Example: AUDCAD vs USDJPY

**AUDCAD (rate ~0.91):**
- Absolute rate: 0.91246
- a_term: -0.0005 (quadratic contribution in absolute units)
- **NOT comparable to USDJPY!**

**USDJPY (rate ~150):**
- Absolute rate: 150.45
- a_term: -0.075 (quadratic contribution in absolute units)
- **150x larger scale!**

**With Normalization:**
- AUDCAD quad_norm = -0.0005 / 0.91 = -0.000549 (-0.0549%)
- USDJPY quad_norm = -0.075 / 150 = -0.0005 (-0.05%)
- **NOW comparable!** Both ~-0.05%

---

## Analysis With Rate Index

### Scenario: Both Pairs Use Rate Index

**AUDCAD with rate_index:**
- rate_index: 100.02 (at baseline)
- a_term_index: -0.05 (quadratic term in index units)
- quad_norm_index = -0.05 / 100.02 = -0.0004999 (-0.04999%)

**USDJPY with rate_index:**
- rate_index: 100.01 (at baseline)
- a_term_index: -0.05 (quadratic term in index units)
- quad_norm_index = -0.05 / 100.01 = -0.0004999 (-0.04999%)

**Observation:**
1. `a_term_index` values are ALREADY comparable (-0.05 vs -0.05) ✓
2. `quad_norm_index` is just dividing by ~100 (adds minimal information)

---

## Mathematical Analysis

### With Absolute Rates (Current)

Regression fitted on absolute rate data:
```
rate(t) = a*t² + b*t + c
```

Terms:
```
a_term = a * t²    (in absolute rate units)
b_term = b * t     (in absolute rate units)
```

**Scale varies by 150x** between AUDCAD and USDJPY!

Normalization:
```
quad_norm = a_term / rate  (percentage)
lin_norm = b_term / rate   (percentage)
```

**Result:** Cross-pair comparable percentages.

---

### With Rate Index (Proposed)

Regression fitted on rate_index data:
```
rate_index(t) = a*t² + b*t + c
```

Terms:
```
a_term_index = a * t²  (in index units, ~100 scale)
b_term_index = b * t   (in index units, ~100 scale)
```

**Scale varies by only ~1%** (all pairs centered at 100)!

If we normalize:
```
quad_norm_index = a_term_index / rate_index
                = a_term_index / ~100
                ≈ a_term_index / 100  (constant scaling!)
```

**Key Insight:** The normalization is mostly just dividing by 100 (constant).

---

## Concrete Example

### AUDCAD at t=0 (Baseline)

**With Absolute Rate:**
```
rate = 0.91246
a_term = -0.000398
quad_norm = -0.000398 / 0.91246 = -0.000436  (-0.0436%)
```

**With Rate Index:**
```
rate_index = 100.00
a_term_index = -0.0436  (already in percentage-like scale)
quad_norm_index = -0.0436 / 100.00 = -0.000436  (-0.0436%)
```

**Comparison:**
- `a_term_index` (-0.0436) already captures the magnitude
- `quad_norm_index` (-0.000436) is just `a_term_index / 100`
- They convey the SAME information (one is 100x the other)

---

### AUDCAD vs USDJPY Comparison

**With Absolute Rates (NEED normalization):**
```
AUDCAD: a_term = -0.0005  (NOT comparable)
USDJPY: a_term = -0.075   (NOT comparable)
Scale differs by 150x!

AUDCAD: quad_norm = -0.000549  (comparable)
USDJPY: quad_norm = -0.0005    (comparable)
NOW comparable!
```

**With Rate Index (ALREADY comparable):**
```
AUDCAD: a_term_index = -0.05  (comparable!)
USDJPY: a_term_index = -0.05  (comparable!)
Same scale! No normalization needed!

AUDCAD: quad_norm_index = -0.0005  (just a_term/100)
USDJPY: quad_norm_index = -0.0005  (just a_term/100)
Redundant information!
```

---

## Edge Case: Rate Index Variation

**Question:** What if rate_index varies significantly from 100?

**Example:**
```
At time t1: rate_index = 95
a_term_index = 0.05
quad_norm_index = 0.05 / 95 = 0.000526

At time t2: rate_index = 105
a_term_index = 0.05
quad_norm_index = 0.05 / 105 = 0.000476
```

**Difference:** 10% variation in quad_norm despite same a_term.

**Interpretation:** The quadratic term is relatively more significant when index is at 95 vs 105.

**Counterargument:** This is a second-order effect. Machine learning models can learn this relationship:
```python
effect = a_term_index / rate_index
```

Pre-computing doesn't add substantial value.

---

## Storage Impact

### Current Schema (75 fields)
- Core: 2 fields (ts_utc, rate)
- Regression: 72 fields (6 windows × 12 fields)
- Metadata: 1 field (created_at)

### Proposed Schema (57 fields - Remove 18 _norm fields)
- Core: 2 fields (ts_utc, rate_index)
- Regression: 54 fields (6 windows × 9 fields)
  - Per window: coefficients (3), terms (2), R²/RMSE (2), prediction (1), residual (1)
  - **Removed per window:** quad_norm, lin_norm, resid_norm (3 fields)
- Metadata: 1 field (created_at)

**Storage Savings:**
- Field reduction: 18 fields (24%)
- Estimated storage: 8.9 GB → 6.7 GB (~2.2 GB savings)
- Across 504 partitions: Significant reduction

---

## Arguments FOR Keeping _norm Fields

1. **Pre-computed convenience:** No need to compute `term / rate_index` at query time
2. **Relative significance:** Captures "is this term large relative to current index?"
3. **Model input ready:** ML models can use directly without transformation
4. **Historical consistency:** Matches existing schema patterns

---

## Arguments AGAINST Keeping _norm Fields (Recommended)

1. **Redundant with index:** `a_term_index` is already cross-pair comparable (all ~100 scale)
2. **Mostly constant scaling:** `quad_norm_index ≈ a_term_index / 100` (minimal info gain)
3. **Computable on-demand:** Can compute `term / rate_index` if needed
4. **Simpler schema:** 24% fewer fields (75 → 57)
5. **Storage savings:** ~2.2 GB saved (~24% reduction)
6. **Model learning:** ML models can learn `term / rate_index` relationship if important

---

## Recommendation: REMOVE _norm Fields

### Rationale

**With absolute rates:**
- AUDCAD a_term: -0.0005 (scale: 0.91)
- USDJPY a_term: -0.075 (scale: 150)
- **Problem:** 150x scale difference → normalization essential

**With rate_index:**
- AUDCAD a_term_index: -0.05 (scale: 100)
- USDJPY a_term_index: -0.05 (scale: 100)
- **Solution:** Already same scale → normalization redundant!

### Fields to Keep (9 per window)
```
w{N}_a_coef       - Quadratic coefficient
w{N}_b_coef       - Linear coefficient
w{N}_c_coef       - Constant term
w{N}_a_term       - Quadratic contribution (in index units)
w{N}_b_term       - Linear contribution (in index units)
w{N}_r2           - R-squared
w{N}_rmse         - RMSE
w{N}_yhat_end     - Predicted index value
w{N}_resid_end    - Residual (in index units)
```

### Fields to Remove (3 per window × 6 windows = 18 total)
```
w60_quad_norm, w60_lin_norm, w60_resid_norm
w90_quad_norm, w90_lin_norm, w90_resid_norm
w150_quad_norm, w150_lin_norm, w150_resid_norm
w240_quad_norm, w240_lin_norm, w240_resid_norm
w390_quad_norm, w390_lin_norm, w390_resid_norm
w630_quad_norm, w630_lin_norm, w630_resid_norm
```

**Why:** All can be computed as `term / rate_index` if needed.

---

## New REG Schema (57 fields)

```sql
CREATE TABLE bqx.reg_audcad (
    -- Core
    ts_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    rate_index DOUBLE PRECISION,

    -- Window 60 (9 fields instead of 12)
    w60_a_coef DOUBLE PRECISION,
    w60_b_coef DOUBLE PRECISION,
    w60_c_coef DOUBLE PRECISION,
    w60_a_term DOUBLE PRECISION,
    w60_b_term DOUBLE PRECISION,
    w60_r2 DOUBLE PRECISION,
    w60_rmse DOUBLE PRECISION,
    w60_yhat_end DOUBLE PRECISION,
    w60_resid_end DOUBLE PRECISION,
    -- REMOVED: w60_quad_norm, w60_lin_norm, w60_resid_norm

    -- Window 90 (9 fields)
    w90_a_coef DOUBLE PRECISION,
    w90_b_coef DOUBLE PRECISION,
    w90_c_coef DOUBLE PRECISION,
    w90_a_term DOUBLE PRECISION,
    w90_b_term DOUBLE PRECISION,
    w90_r2 DOUBLE PRECISION,
    w90_rmse DOUBLE PRECISION,
    w90_yhat_end DOUBLE PRECISION,
    w90_resid_end DOUBLE PRECISION,

    -- Windows 150, 240, 390, 630 (same pattern)
    -- ... (9 fields each)

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

---

## Impact Summary

| Metric | Current | Proposed | Change |
|--------|---------|----------|--------|
| **Fields per table** | 75 | 57 | -18 (24% reduction) |
| **Fields per window** | 12 | 9 | -3 (25% reduction) |
| **Storage (estimated)** | 8.9 GB | 6.7 GB | -2.2 GB (24% savings) |
| **Schema complexity** | High | Lower | Simpler |
| **Cross-pair comparable** | Yes (via _norm) | Yes (via index) | ✓ |

---

## Conclusion

**RECOMMENDATION: REMOVE *_norm fields from REG tables.**

**Why:**
1. ✅ With rate_index, `_term` and `_resid_end` fields are already cross-pair comparable
2. ✅ `*_norm` fields are mostly just `term / 100` (redundant)
3. ✅ Saves 24% storage and simplifies schema
4. ✅ If normalization needed, compute on-demand: `term / rate_index`
5. ✅ ML models can learn this ratio if it provides signal

**Result:** REG schema goes from 75 fields → 57 fields (24% reduction).

---

**Created:** 2025-11-10
**Author:** Claude Code
**Status:** Analysis Complete - Recommendation to Remove _norm Fields
