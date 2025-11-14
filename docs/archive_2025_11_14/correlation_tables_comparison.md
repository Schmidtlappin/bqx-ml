# Correlation Tables Comparison: correlation_* vs ml_corr_*

**Date:** 2025-11-10
**Status:** Analysis Complete

---

## Overview

The BQX database has two distinct types of correlation tables serving different purposes:

1. **correlation_*** - Pair-to-pair correlations (28 tables, ~10.2 GB, EMPTY)
2. **ml_corr_*** - Feature-to-target correlations (85 partitions, 2.4 TB, DROPPED)

---

## Table 1: correlation_* Tables

### Purpose
**Pair-to-pair correlation tracking** - measures how different forex pairs correlate with each other.

### Schema
```sql
CREATE TABLE bqx.correlation_<pair> (
    ts_utc TIMESTAMP WITH TIME ZONE,
    pair TEXT,                          -- Base pair (e.g., "audcad")
    corr_pair TEXT,                     -- Correlated pair (e.g., "eurusd")
    window_minutes INTEGER,             -- Correlation window
    correlation DOUBLE PRECISION,       -- Correlation coefficient
    correlation_matrix DOUBLE PRECISION,
    correlation_momentum DOUBLE PRECISION,
    correlation_acceleration DOUBLE PRECISION,
    base_volatility DOUBLE PRECISION,
    corr_volatility DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE
);
```

### Example Use Cases
- Detect currency basket movements (e.g., EUR strength across EUR/USD, EUR/GBP, EUR/JPY)
- Identify diversification opportunities (low correlation = better diversification)
- Detect multi-pair arbitrage opportunities
- Risk management (high correlation = concentrated risk)

### Current Status
- **Tables:** 28 (one per pair)
- **Total Size:** ~10.2 GB (allocated but empty)
- **Row Count:** 0 (all tables empty)
- **Impact from Index Refactor:** NONE - scale-independent, no recalculation needed

### Sample Query Pattern
```sql
-- Find pairs that correlate strongly with AUDCAD
SELECT
    ts_utc,
    pair,           -- audcad
    corr_pair,      -- eurusd, gbpusd, etc.
    correlation     -- 0.85 (strong positive correlation)
FROM bqx.correlation_audcad
WHERE correlation > 0.7
  AND window_minutes = 60
ORDER BY ts_utc DESC;
```

---

## Table 2: ml_corr_* Tables

### Purpose
**Feature-to-target correlation tracking** - measures how well each BQX feature predicts the target (future return).

### Schema
```sql
CREATE TABLE bqx.ml_corr_triangulation_partitioned (
    ts_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    source_mv TEXT NOT NULL,               -- Source pair (e.g., "audcad")
    feature_name TEXT NOT NULL,            -- Feature (e.g., "w150_lin_norm")
    correlation_window INTEGER NOT NULL,   -- Time window (60, 240, 390 min)
    correlation_value DOUBLE PRECISION NOT NULL  -- Correlation coefficient
) PARTITION BY RANGE (ts_utc);
```

### Example Data (before dropping)
```
ts_utc               | source_mv | feature_name    | correlation_window | correlation_value
---------------------+-----------+-----------------+--------------------+-------------------
2024-07-01 05:17:00  | audcad    | rate            | 60                 | 0.850
2024-07-01 05:17:00  | audcad    | volatility      | 60                 | 0.895
2024-07-01 05:17:00  | audcad    | w150_lin_norm   | 60                 | 0.898  ← High predictive value!
2024-07-01 05:17:00  | audcad    | w150_quad_norm  | 60                 | -0.275
2024-07-01 05:17:00  | audcad    | w150_r2         | 60                 | -0.922
```

### Example Use Cases
- **Feature selection:** Include only features with high correlation to target
- **Model optimization:** Remove low-correlation features to reduce noise
- **Feature importance:** Identify which technical indicators are most predictive
- **Model debugging:** Verify expected relationships (e.g., momentum should correlate with future returns)

### Current Status
- **Tables:** 85 partitions (2020-01 through 2026-12)
- **Populated:** 16 partitions (2024-07 through 2025-10)
- **Total Size:** 2.4 TB (before dropping)
- **Row Count:** Billions (28 pairs × ~40 features × 3 windows × millions of timestamps)
- **Current Status:** ✅ **DROPPED** (2025-11-10)
- **Reason for Drop:** Target changed from pre-BQX metric to w60_bqx_return at t+60
- **Impact from Index Refactor:** **CRITICAL** - must recalculate with new target

### Sample Query Pattern
```sql
-- Find most predictive features for AUDCAD at 60-minute horizon
SELECT
    feature_name,
    AVG(correlation_value) as avg_correlation
FROM bqx.ml_corr_2024_07
WHERE source_mv = 'audcad'
  AND correlation_window = 60
GROUP BY feature_name
HAVING AVG(correlation_value) > 0.7
ORDER BY avg_correlation DESC;
```

---

## Key Differences

| Aspect | correlation_* | ml_corr_* |
|--------|---------------|-----------|
| **Purpose** | Pair-to-pair correlation | Feature-to-target correlation |
| **Measures** | How pairs move together | How features predict target |
| **Size** | 10.2 GB (28 tables) | 2.4 TB (85 partitions) |
| **Status** | Empty (never populated) | Dropped (was populated, now deleted) |
| **Use Case** | Diversification, risk management | Feature selection, model optimization |
| **Data Pattern** | `corr(AUDCAD_rate, EURUSD_rate)` | `corr(w150_lin_norm, w60_bqx_return@t+60)` |
| **Scale Independence** | Yes (correlation is scale-independent) | Yes, BUT target changed |
| **Recalc Needed?** | No (empty anyway) | **YES** (target changed) |
| **Rebuild Stage** | N/A | Stage 1.5.8 (6 hours) |

---

## Why ml_corr_* Needs Recalculation

### Mathematical Explanation
```
correlation_* tables:
corr(AUDCAD_rate, EURUSD_rate) = corr(AUDCAD_index, EURUSD_index)  ✓ SAME
Reason: Both inputs scaled uniformly → correlation unchanged

ml_corr_* tables:
corr(feature, OldTarget) ≠ corr(feature, NewTarget)  ❌ DIFFERENT
Reason: TARGET changed (not just scaled) → correlation MUST change

Old: corr(w150_lin_norm, UnknownTarget)  ← Wrong target
New: corr(w150_lin_norm, w60_bqx_return@t+60)  ← Correct target
```

### Example Impact
```python
# Old ml_corr data (incorrect target):
corr(w150_lin_norm, old_target) = 0.45  ← Low correlation

# New ml_corr data (correct target):
corr(w150_lin_norm, w60_bqx_return@t+60) = 0.89  ← High correlation!

# Decision impact:
# Old: Exclude w150_lin_norm (low correlation) ❌ WRONG
# New: Include w150_lin_norm (high correlation) ✓ CORRECT
```

---

## Summary

### correlation_* Tables
- ✅ **No action needed** - Empty, scale-independent, not used yet
- Purpose: Measure pair-to-pair relationships
- Impact: None from index refactor

### ml_corr_* Tables
- ❌ **Action required** - Dropped due to target change
- Purpose: Measure feature-to-target relationships
- Impact: Critical for feature selection
- Next Step: Stage 1.5.8 (recreate with correct target)

---

## Timeline

1. ✅ **2025-11-10:** ml_corr_* dropped (2.4 TB freed)
2. ⏳ **Stage 1.5.4:** BQX tables recalculated with rate_index
3. ⏳ **Stage 1.5.6:** Unified MV created
4. 🔜 **Stage 1.5.8:** Recreate ml_corr_* with w60_bqx_return@t+60 target

---

**Created:** 2025-11-10
**Author:** Claude Code
**Status:** Documentation Complete
