# REG Table Schema Analysis

**Date:** 2025-11-10
**Current Tables:** 504 (28 pairs × 18 partitions)
**Total Size:** ~8.9 GB

---

## Current REG Table Schema (75 columns)

### Core Fields (2 columns)
1. `ts_utc` - Timestamp with time zone (PRIMARY KEY)
2. `rate` - Current absolute rate (e.g., 0.90045 for AUDCAD)

### Regression Windows (6 windows)
- w60: 60-minute window
- w90: 90-minute window
- w150: 150-minute window (2.5 hours)
- w240: 240-minute window (4 hours)
- w390: 390-minute window (6.5 hours)
- w630: 630-minute window (10.5 hours)

### Per-Window Fields (12 fields × 6 windows = 72 columns)

Each window contains quadratic regression analysis of historical rates:

**Regression Coefficients (3 fields):**
- `w{N}_a_coef` - Quadratic term coefficient (a in ax² + bx + c)
- `w{N}_b_coef` - Linear term coefficient (b in ax² + bx + c)
- `w{N}_c_coef` - Constant term (c in ax² + bx + c)

**Regression Terms (2 fields):**
- `w{N}_a_term` - Computed quadratic contribution (a × x²)
- `w{N}_b_term` - Computed linear contribution (b × x)

**Goodness of Fit (2 fields):**
- `w{N}_r2` - R-squared (coefficient of determination, 0-1)
- `w{N}_rmse` - Root mean squared error

**Predictions (1 field):**
- `w{N}_yhat_end` - Predicted value at end of window

**Normalized Values (2 fields):**
- `w{N}_quad_norm` - Normalized quadratic term
- `w{N}_lin_norm` - Normalized linear term

**Residuals (2 fields):**
- `w{N}_resid_end` - Residual at end of window
- `w{N}_resid_norm` - Normalized residual

### Metadata (1 column)
73. `created_at` - Record creation timestamp

---

## Planned REG Table Schema (Index-Based)

### Option A: Full Index Conversion (Recommended)

**Changes:**
1. `rate` → `rate_index` (forex index around 100)
2. Keep all 72 regression fields (coefficients calculated from rate_index history)
3. Remove *_norm fields? (Need to analyze if normalization still needed)

**Total Columns:** 50-75 (depending on normalization decision)

---

## Field-by-Field Analysis

### Fields That MUST Change

| Current Field | New Field | Reason |
|---------------|-----------|--------|
| `rate` | `rate_index` | Switch from absolute rate to index |

### Fields That MAY Change

| Current Field | Keep/Remove | Reason |
|---------------|-------------|--------|
| `w{N}_quad_norm` | **KEEP** | Normalization helps cross-pair comparison |
| `w{N}_lin_norm` | **KEEP** | Normalization helps cross-pair comparison |
| `w{N}_resid_norm` | **KEEP** | Normalized residuals useful for model evaluation |

**Reasoning:** Unlike BQX's _pct fields (which were redundant with index), REG's _norm fields provide statistical normalization of regression terms, which is still valuable even with rate_index.

### Fields That DON'T Change

All coefficient, term, R², RMSE, prediction, and residual fields remain:
- Coefficients (a, b, c) are scale-independent relative measures
- R² is a ratio (0-1), inherently scale-independent
- Terms, predictions, and residuals will be in index space (around 100)

---

## Detailed Field List

### Window 60 (w60) - 12 fields
```
1.  w60_a_coef       - Quadratic coefficient
2.  w60_b_coef       - Linear coefficient
3.  w60_c_coef       - Constant term
4.  w60_a_term       - Quadratic contribution
5.  w60_b_term       - Linear contribution
6.  w60_r2           - R-squared
7.  w60_rmse         - Root mean squared error
8.  w60_yhat_end     - Predicted value at end
9.  w60_quad_norm    - Normalized quadratic term
10. w60_lin_norm     - Normalized linear term
11. w60_resid_end    - Residual at end
12. w60_resid_norm   - Normalized residual
```

### Window 90 (w90) - 12 fields
```
13. w90_a_coef
14. w90_b_coef
15. w90_c_coef
16. w90_a_term
17. w90_b_term
18. w90_r2
19. w90_rmse
20. w90_yhat_end
21. w90_quad_norm
22. w90_lin_norm
23. w90_resid_end
24. w90_resid_norm
```

### Window 150 (w150) - 12 fields
```
25. w150_a_coef
26. w150_b_coef
27. w150_c_coef
28. w150_a_term
29. w150_b_term
30. w150_r2
31. w150_rmse
32. w150_yhat_end
33. w150_quad_norm
34. w150_lin_norm
35. w150_resid_end
36. w150_resid_norm
```

### Window 240 (w240) - 12 fields
```
37. w240_a_coef
38. w240_b_coef
39. w240_c_coef
40. w240_a_term
41. w240_b_term
42. w240_r2
43. w240_rmse
44. w240_yhat_end
45. w240_quad_norm
46. w240_lin_norm
47. w240_resid_end
48. w240_resid_norm
```

### Window 390 (w390) - 12 fields
```
49. w390_a_coef
50. w390_b_coef
51. w390_c_coef
52. w390_a_term
53. w390_b_term
54. w390_r2
55. w390_rmse
56. w390_yhat_end
57. w390_quad_norm
58. w390_lin_norm
59. w390_resid_end
60. w390_resid_norm
```

### Window 630 (w630) - 12 fields
```
61. w630_a_coef
62. w630_b_coef
63. w630_c_coef
64. w630_a_term
65. w630_b_term
66. w630_r2
67. w630_rmse
68. w630_yhat_end
69. w630_quad_norm
70. w630_lin_norm
71. w630_resid_end
72. w630_resid_norm
```

---

## Complete New Schema (75 columns - SAME COUNT)

```sql
CREATE TABLE bqx.reg_audcad (
    -- Core fields
    ts_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    rate_index DOUBLE PRECISION,           -- CHANGED from 'rate'

    -- Window 60 (60 minutes)
    w60_a_coef DOUBLE PRECISION,
    w60_b_coef DOUBLE PRECISION,
    w60_c_coef DOUBLE PRECISION,
    w60_a_term DOUBLE PRECISION,
    w60_b_term DOUBLE PRECISION,
    w60_r2 DOUBLE PRECISION,
    w60_rmse DOUBLE PRECISION,
    w60_yhat_end DOUBLE PRECISION,
    w60_quad_norm DOUBLE PRECISION,
    w60_lin_norm DOUBLE PRECISION,
    w60_resid_end DOUBLE PRECISION,
    w60_resid_norm DOUBLE PRECISION,

    -- Window 90 (90 minutes)
    w90_a_coef DOUBLE PRECISION,
    w90_b_coef DOUBLE PRECISION,
    w90_c_coef DOUBLE PRECISION,
    w90_a_term DOUBLE PRECISION,
    w90_b_term DOUBLE PRECISION,
    w90_r2 DOUBLE PRECISION,
    w90_rmse DOUBLE PRECISION,
    w90_yhat_end DOUBLE PRECISION,
    w90_quad_norm DOUBLE PRECISION,
    w90_lin_norm DOUBLE PRECISION,
    w90_resid_end DOUBLE PRECISION,
    w90_resid_norm DOUBLE PRECISION,

    -- Window 150 (2.5 hours)
    w150_a_coef DOUBLE PRECISION,
    w150_b_coef DOUBLE PRECISION,
    w150_c_coef DOUBLE PRECISION,
    w150_a_term DOUBLE PRECISION,
    w150_b_term DOUBLE PRECISION,
    w150_r2 DOUBLE PRECISION,
    w150_rmse DOUBLE PRECISION,
    w150_yhat_end DOUBLE PRECISION,
    w150_quad_norm DOUBLE PRECISION,
    w150_lin_norm DOUBLE PRECISION,
    w150_resid_end DOUBLE PRECISION,
    w150_resid_norm DOUBLE PRECISION,

    -- Window 240 (4 hours)
    w240_a_coef DOUBLE PRECISION,
    w240_b_coef DOUBLE PRECISION,
    w240_c_coef DOUBLE PRECISION,
    w240_a_term DOUBLE PRECISION,
    w240_b_term DOUBLE PRECISION,
    w240_r2 DOUBLE PRECISION,
    w240_rmse DOUBLE PRECISION,
    w240_yhat_end DOUBLE PRECISION,
    w240_quad_norm DOUBLE PRECISION,
    w240_lin_norm DOUBLE PRECISION,
    w240_resid_end DOUBLE PRECISION,
    w240_resid_norm DOUBLE PRECISION,

    -- Window 390 (6.5 hours)
    w390_a_coef DOUBLE PRECISION,
    w390_b_coef DOUBLE PRECISION,
    w390_c_coef DOUBLE PRECISION,
    w390_a_term DOUBLE PRECISION,
    w390_b_term DOUBLE PRECISION,
    w390_r2 DOUBLE PRECISION,
    w390_rmse DOUBLE PRECISION,
    w390_yhat_end DOUBLE PRECISION,
    w390_quad_norm DOUBLE PRECISION,
    w390_lin_norm DOUBLE PRECISION,
    w390_resid_end DOUBLE PRECISION,
    w390_resid_norm DOUBLE PRECISION,

    -- Window 630 (10.5 hours)
    w630_a_coef DOUBLE PRECISION,
    w630_b_coef DOUBLE PRECISION,
    w630_c_coef DOUBLE PRECISION,
    w630_a_term DOUBLE PRECISION,
    w630_b_term DOUBLE PRECISION,
    w630_r2 DOUBLE PRECISION,
    w630_rmse DOUBLE PRECISION,
    w630_yhat_end DOUBLE PRECISION,
    w630_quad_norm DOUBLE PRECISION,
    w630_lin_norm DOUBLE PRECISION,
    w630_resid_end DOUBLE PRECISION,
    w630_resid_norm DOUBLE PRECISION,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

---

## Summary

**Total Columns:** 75 (unchanged from current schema)

**Changes:**
- ✅ 1 field renamed: `rate` → `rate_index`
- ✅ Keep all 72 regression fields (coefficients, terms, R², RMSE, predictions, residuals, normalized values)
- ✅ Keep created_at timestamp

**Reasoning:**
- REG's _norm fields provide statistical normalization of regression terms (different purpose than BQX's _pct fields)
- All regression calculations will use rate_index as input instead of absolute rate
- Output values (terms, predictions, residuals) will be in index space (around 100)

---

**Created:** 2025-11-10
**Author:** Claude Code
**Status:** Schema Documented - Ready for Stage 1.5.5
