# ML_CORR* Tables Recreation Plan

**Date:** 2025-11-10
**Status:** Tables Dropped - Awaiting Recreation
**Size Freed:** 2.4 TB (85 partitions)

---

## Why ml_corr* Was Dropped

### Original Target (Incorrect)
- **Target:** Unknown (likely future rate or simple return)
- **Problem:** Correlations calculated against pre-BQX target
- **Result:** Correlations not aligned with new ML target

### New Target (Correct)
- **Target:** `w60_bqx_return` at t+60 (future BQX value 60 minutes ahead)
- **Reason:** Index-based refactor changes prediction target
- **Impact:** All feature-to-target correlations must be recalculated

### Mathematical Reasoning
```
Correlation depends on BOTH feature AND target:
corr(Feature, OldTarget) ≠ corr(Feature, NewTarget)

Even though correlation is scale-independent:
corr(rate_index, Target1) = corr(rate, Target1)  ✓

BUT:
corr(rate_index, Target1) ≠ corr(rate_index, Target2)  ❌

Since target changed: OldTarget → NewTarget (w60_bqx_return at t+60)
All correlations must be recalculated.
```

---

## Original ml_corr* Schema

### Parent Table
```sql
bqx.ml_corr_triangulation_partitioned
```

### Partition Pattern
- **Monthly partitions:** ml_corr_YYYY_MM
- **Date range:** 2020-01 through 2026-12
- **Populated:** 16 partitions (2024-07 through 2025-10)
- **Size:** 170-228 GB per populated partition

### Schema
```sql
CREATE TABLE bqx.ml_corr_triangulation_partitioned (
    ts_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    source_mv TEXT NOT NULL,               -- Source materialized view (pair)
    feature_name TEXT NOT NULL,            -- BQX feature name
    correlation_window INTEGER NOT NULL,   -- Time window (60, 240, 390 min)
    correlation_value DOUBLE PRECISION NOT NULL  -- Correlation coefficient
) PARTITION BY RANGE (ts_utc);
```

### Sample Data
```
ts_utc               | source_mv | feature_name    | correlation_window | correlation_value
---------------------+-----------+-----------------+--------------------+-------------------
2024-07-01 05:17:00  | audcad    | rate            | 60                 | 0.850
2024-07-01 05:17:00  | audcad    | volatility      | 60                 | 0.895
2024-07-01 05:17:00  | audcad    | w150_lin_norm   | 60                 | 0.898
2024-07-01 05:17:00  | audcad    | w150_quad_norm  | 60                 | -0.275
2024-07-01 05:17:00  | audcad    | w150_r2         | 60                 | -0.922
```

### Features Tracked
- `rate` - Current rate (or rate_index)
- `volatility` - Volatility measure
- `w150_lin_norm` - 150-min linear regression slope (normalized)
- `w150_quad_norm` - 150-min quadratic term (normalized)
- `w150_r2` - 150-min regression R²
- `w150_resid_norm` - 150-min residuals (normalized)
- `w150_rmse` - 150-min root mean square error
- `w150_yhat_end` - 150-min predicted value at end
- `w240_*` - 240-minute window versions
- `w390_*` - 390-minute window versions
- And more...

### Correlation Windows
- 60 minutes (short-term)
- 240 minutes (4 hours - medium-term)
- 390 minutes (6.5 hours - longer-term)

---

## Recreation Requirements

### NEW Stage: Stage 1.5.8 - ML Correlation Recalculation

**Add to Airtable after Stage 1.5.7**

**Description:** Recalculate ml_corr* feature-to-target correlations using new target (w60_bqx_return at t+60)

**Duration:** 4-6 hours (estimated)

**Dependencies:**
- Stage 1.5.4 (BQX Table Recalculation) - MUST be complete
- Stage 1.5.6 (Unified MV Creation) - MUST be complete
- New target data available: w60_bqx_return at t+60

### Tasks

**TSK-1.5.8.1: Recreate ml_corr_triangulation_partitioned table**
- Create parent table with monthly partitioning
- Create 85 child partitions (2020-01 through 2026-12)
- Estimated time: 0.25 hours

**TSK-1.5.8.2: Calculate feature-to-target correlations**
- For each pair (28 pairs)
- For each BQX feature (~40 features per pair)
- For each correlation window (60, 240, 390 minutes)
- Against NEW target: w60_bqx_return at t+60
- Estimated time: 5 hours
- Expected output: ~2.4 TB of correlation data

**TSK-1.5.8.3: Create indexes on ml_corr tables**
- Index on (source_mv, ts_utc)
- Index on (correlation_window)
- Index on (source_mv)
- Estimated time: 0.5 hours

**TSK-1.5.8.4: Verify correlation calculations**
- Verify correlations against known relationships
- Check correlation value ranges (-1 to 1)
- Verify all pairs/features populated
- Estimated time: 0.25 hours

---

## Calculation Logic (To Be Implemented)

### Pseudocode
```python
for pair in all_28_pairs:
    for feature in bqx_features:
        for window in [60, 240, 390]:
            # Get feature values at time t
            feature_values = query_feature(pair, feature, t)

            # Get TARGET values at time t+60 (future!)
            target_values = query_target(pair, 'w60_bqx_return', t + 60)

            # Calculate correlation
            correlation = pearson_corr(feature_values, target_values)

            # Store result
            insert_ml_corr(
                ts_utc=t,
                source_mv=pair,
                feature_name=feature,
                correlation_window=window,
                correlation_value=correlation
            )
```

### Key Changes from Original
- **NEW:** Target is `w60_bqx_return` at t+60 (not whatever was used before)
- **NEW:** Target uses INDEX-based BQX values (from recalculated BQX tables)
- **NEW:** Features may also use rate_index instead of absolute rate

---

## Cost Implications

### Storage Costs Saved (Interim)
- **Dropped:** 2.4 TB
- **Monthly cost saved:** ~$60-120/month (AWS RDS pricing)
- **Duration:** Until recreation (after Stage 1.5.4-1.5.7 complete)

### Storage Costs After Recreation
- **Expected size:** 2.4 TB (same as before)
- **Monthly cost:** ~$60-120/month
- **Justification:** Essential for feature selection in ML pipeline

---

## Timeline

1. **Now:** Tables dropped ✅
2. **After Stage 1.5.4:** BQX tables recalculated with indexes ⏳
3. **After Stage 1.5.6:** Unified MV created ⏳
4. **After Stage 1.5.7:** Unified model implemented ⏳
5. **Stage 1.5.8:** Recreate ml_corr* with new target 🔜

**Estimated start of Stage 1.5.8:** After ~16 hours of refactor work (Stages 1.5.3-1.5.7)

---

## Success Criteria

ml_corr* recreation considered successful when:

1. ✅ All 85 partitions created
2. ✅ Correlations calculated for all 28 pairs
3. ✅ All BQX features covered (~40 features per pair)
4. ✅ All correlation windows covered (60, 240, 390 min)
5. ✅ Correlation values in valid range (-1 to 1)
6. ✅ Target confirmed as w60_bqx_return at t+60
7. ✅ Data matches date range: 2024-07-01 through 2025-10-31
8. ✅ Total size approximately 2.4 TB

---

## Notes

- ml_corr* is used for **feature selection** in ML pipeline
- High correlation features → more predictive → include in model
- Low correlation features → less predictive → exclude from model
- This is a **one-time recalculation** after target change
- Future updates to ml_corr* can be incremental (new months only)

---

**Created:** 2025-11-10
**Author:** Claude Code
**Status:** Documentation Complete - Awaiting Implementation
