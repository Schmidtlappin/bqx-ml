# Schema Migration Analysis - Term-Based Architecture
**Date:** 2025-11-15
**Database:** trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com
**Status:** ✅ Aurora credentials retrieved, schema analyzed

---

## Executive Summary

**Current State:** Database contains BOTH coefficients and partial terms (inconsistent implementation)

**Required State:** Term-based architecture (quadratic_term, linear_term, constant_term, residual)

**Migration Impact:**
- **reg_rate_* tables:** Add constant_term, rename columns (minor changes)
- **reg_bqx_* tables:** Complete rebuild (coefficients → terms)
- **Total partitions:** 336 (reg_rate) + 336 (reg_bqx) = 672 partitions

---

## 1. Current Schema Analysis

### ✅ reg_rate_* Tables (Rate Index Domain)

**Connection Test:**
```bash
✅ Connected successfully to Aurora cluster
✅ Database: bqx, User: postgres
✅ Password retrieved from: bqx-mirror/bqx/aurora/master
```

**Sample Table:** bqx.reg_eurusd_2024_07
**Row Count:** 32,687 rows (July 2024)

**Current Schema (per window):**
```sql
-- Example for w60 window
w60_a_coef     DOUBLE PRECISION,   -- Quadratic coefficient (a₂)
w60_b_coef     DOUBLE PRECISION,   -- Linear coefficient (a₁)
w60_c_coef     DOUBLE PRECISION,   -- Constant coefficient (a₀)
w60_a_term     DOUBLE PRECISION,   -- Quadratic term (a₂ · x_end²)
w60_b_term     DOUBLE PRECISION,   -- Linear term (a₁ · x_end)
w60_r2         DOUBLE PRECISION,   -- R² (fit quality)
w60_rmse       DOUBLE PRECISION,   -- Root mean squared error
w60_yhat_end   DOUBLE PRECISION,   -- Prediction at end of window
w60_resid_end  DOUBLE PRECISION    -- Residual (y_actual - yhat_end)
```

**Sample Data:**
```
ts_utc: 2024-07-01 00:00:00+00
w60_a_coef:     -1.74e-05   (coefficient)
w60_b_coef:      6.78e-04   (coefficient)
w60_c_coef:      100.0156   (coefficient = constant)
w60_a_term:      -0.0606    (evaluated term)
w60_b_term:       0.0400    (evaluated term)
w60_yhat_end:     99.9950   (prediction)
w60_resid_end:    -0.000559 (residual)
```

**Validation:**
```
a_term + b_term + c_coef = -0.0606 + 0.0400 + 100.0156 = 99.9950 ✅
Matches w60_yhat_end!
```

**Issues:**
1. ✅ Has coefficients (a_coef, b_coef, c_coef) - **NOT NEEDED** (abstract, not interpretable)
2. ✅ Has quadratic_term (a_term) and linear_term (b_term) - **GOOD**
3. ❌ Missing constant_term (c_coef is coefficient, not evaluated term)
4. ✅ Has prediction (yhat_end) and residual (resid_end) - **GOOD**
5. ⚠️  Column names use technical notation (a_term, b_term) instead of semantic names

### ✅ reg_bqx_* Tables (BQX Domain)

**Sample Table:** bqx.reg_bqx_eurusd_2024_07
**Windows:** w15, w30, w45, w60, w75, agg (different from reg_rate!)

**Current Schema (per window):**
```sql
-- Example for w15 window
a2_bqx_w15                  NUMERIC,   -- Quadratic coefficient (a₂)
a1_bqx_w15                  NUMERIC,   -- Linear coefficient (a₁)
b_bqx_w15                   NUMERIC,   -- Constant coefficient (a₀)
r2_bqx_w15                  NUMERIC,   -- R² (fit quality)
rmse_bqx_w15                NUMERIC,   -- Root mean squared error
prediction_bqx_w15          NUMERIC,   -- Prediction
residual_mean_bqx_w15       NUMERIC,   -- Mean of residuals
residual_std_bqx_w15        NUMERIC,   -- Std dev of residuals
pred_interval_lower_bqx_w15 NUMERIC,   -- Prediction interval lower bound
pred_interval_upper_bqx_w15 NUMERIC,   -- Prediction interval upper bound
vertex_x_bqx_w15            NUMERIC,   -- Parabola vertex X coordinate
vertex_y_bqx_w15            NUMERIC,   -- Parabola vertex Y coordinate
curvature_bqx_w15           NUMERIC,   -- Curvature metric
fit_quality_bqx_w15         NUMERIC,   -- Combined fit quality score
extrapolation_error_bqx_w15 NUMERIC    -- Extrapolation error estimate
```

**Sample Data:**
```
ts_utc: 2024-07-01 00:14:00
a2_bqx_w15:        0.000324 (coefficient)
a1_bqx_w15:        0.000736 (coefficient)
b_bqx_w15:        -0.000567 (coefficient)
prediction_bqx_w15: 0.001475 (prediction)
```

**Issues:**
1. ❌ Stores ONLY coefficients (a2, a1, b) - **NOT INTERPRETABLE**
2. ❌ Missing ALL terms (quadratic_term, linear_term, constant_term)
3. ✅ Has prediction - **GOOD**
4. ❌ Missing residual column
5. ⚠️  Different windows than reg_rate (w15, w30, w45 vs w60, w90, w150)
6. ⚠️  Has many derived metrics (vertex, curvature, etc.) that can be calculated on-the-fly

---

## 2. Term-Based Architecture Requirements

### ✅ Target Schema (Unified for both reg_rate_* and reg_bqx_*)

**Per Window Features (7 fields):**
```sql
-- Example for w60 window
w60_quadratic_term  DOUBLE PRECISION,   -- a₂ · x_end² (in rate_index units)
w60_linear_term     DOUBLE PRECISION,   -- a₁ · x_end (in rate_index units)
w60_constant_term   DOUBLE PRECISION,   -- a₀ (baseline rate_index)
w60_residual        DOUBLE PRECISION,   -- y_actual - ŷ (model error)
w60_r2              DOUBLE PRECISION,   -- R² (fit quality)
w60_rmse            DOUBLE PRECISION,   -- Root mean squared error
w60_prediction      DOUBLE PRECISION    -- ŷ = quad + lin + const
```

**Why Terms (Not Coefficients):**
- **Interpretable:** Terms are in rate_index units (~100), directly understandable
- **Comparable:** Can compare quadratic_term across windows and pairs
- **ML-Ready:** Terms capture shape of trajectory in original scale
- **Residual:** Reveals model fit error magnitude

**Window Alignment:**
- **reg_rate_*:** w60, w90, w150, w240, w390, w630 (6 windows)
- **reg_bqx_*:** Align to match reg_rate windows (currently misaligned)

---

## 3. Migration Plan

### Strategy A: In-Place Column Addition (Recommended for reg_rate_*)

**For reg_rate_* tables:**
1. Add missing constant_term column
2. Populate from c_coef (since constant_term = c_coef)
3. Rename columns for clarity (optional)
4. Keep coefficients for backward compatibility (optional)

**Migration SQL:**
```sql
-- Add constant_term column to all reg_* partitions
DO $$
DECLARE
    pair_name TEXT;
    year_month TEXT;
    partition_name TEXT;
BEGIN
    FOR pair_name IN SELECT unnest(ARRAY[
        'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
        'cadchf', 'cadjpy', 'chfjpy',
        'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
        'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
        'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
        'usdcad', 'usdchf', 'usdjpy'
    ])
    LOOP
        FOR year_month IN SELECT unnest(ARRAY[
            '2024_07', '2024_08', '2024_09', '2024_10', '2024_11', '2024_12',
            '2025_01', '2025_02', '2025_03', '2025_04', '2025_05', '2025_06'
        ])
        LOOP
            partition_name := 'reg_' || pair_name || '_' || year_month;

            -- Add constant_term columns for each window
            EXECUTE format('
                ALTER TABLE bqx.%I
                ADD COLUMN IF NOT EXISTS w60_constant_term DOUBLE PRECISION,
                ADD COLUMN IF NOT EXISTS w90_constant_term DOUBLE PRECISION,
                ADD COLUMN IF NOT EXISTS w150_constant_term DOUBLE PRECISION,
                ADD COLUMN IF NOT EXISTS w240_constant_term DOUBLE PRECISION,
                ADD COLUMN IF NOT EXISTS w390_constant_term DOUBLE PRECISION,
                ADD COLUMN IF NOT EXISTS w630_constant_term DOUBLE PRECISION
            ', partition_name);

            -- Populate constant_term from c_coef
            EXECUTE format('
                UPDATE bqx.%I SET
                w60_constant_term = w60_c_coef,
                w90_constant_term = w90_c_coef,
                w150_constant_term = w150_c_coef,
                w240_constant_term = w240_c_coef,
                w390_constant_term = w390_c_coef,
                w630_constant_term = w630_c_coef
            ', partition_name);

            RAISE NOTICE 'Updated partition: %', partition_name;
        END LOOP;
    END LOOP;
END $$;
```

**Estimated Duration:** 30 minutes (336 partitions × ~5 seconds)

### Strategy B: Full Rebuild (Required for reg_bqx_*)

**For reg_bqx_* tables:**
1. Drop existing reg_bqx_* tables
2. Create new schema with term-based columns
3. Re-run populate_regression_features_worker.py with updated calculation
4. Align windows to match reg_rate_* (w60, w90, w150, w240, w390, w630)

**Rationale:**
- Current reg_bqx stores only coefficients (not usable for term-based approach)
- Different window sizes (need alignment)
- Simpler to rebuild than migrate complex coefficient → term conversion

**Estimated Duration:** 2-3 hours (re-run worker script with 8 parallel workers)

---

## 4. Column Rename Mapping (Optional)

**For Clarity (Semantic Naming):**

| Old Name | New Name | Reason |
|----------|----------|--------|
| w60_a_term | w60_quadratic_term | Clearer semantic meaning |
| w60_b_term | w60_linear_term | Clearer semantic meaning |
| w60_c_coef | w60_constant_term | Now a term, not coefficient |
| w60_yhat_end | w60_prediction | Standard ML terminology |
| w60_resid_end | w60_residual | Standard ML terminology |

**Note:** Column renaming is OPTIONAL. Can keep existing names if preferred.

---

## 5. Validation Approach

### ✅ Data Integrity Checks

**After Migration:**
```sql
-- Verify constant_term = c_coef (for reg_rate_*)
SELECT COUNT(*) FROM bqx.reg_eurusd_2024_07
WHERE ABS(w60_constant_term - w60_c_coef) > 0.000001;
-- Expected: 0 (all match)

-- Verify prediction = quadratic_term + linear_term + constant_term
SELECT COUNT(*) FROM bqx.reg_eurusd_2024_07
WHERE ABS(w60_yhat_end - (w60_a_term + w60_b_term + w60_constant_term)) > 0.001;
-- Expected: 0 (all match)

-- Verify residual = y_actual - prediction
SELECT ts_utc, rate_index, w60_yhat_end, w60_resid_end,
       (rate_index - w60_yhat_end) AS calculated_resid,
       ABS(w60_resid_end - (rate_index - w60_yhat_end)) AS diff
FROM bqx.reg_eurusd_2024_07
WHERE w60_resid_end IS NOT NULL
LIMIT 10;
-- Expected: diff < 0.001
```

---

## 6. Implementation Checklist

### ✅ Phase 1: reg_rate_* Migration (Low Risk)

- [ ] **Backup:** Create snapshot of Aurora cluster
- [ ] **Test on single partition:** reg_eurusd_2024_07
  - [ ] Add constant_term column
  - [ ] Populate from c_coef
  - [ ] Validate data integrity
  - [ ] Test queries using new columns
- [ ] **Roll out to all partitions:** 336 partitions (28 pairs × 12 months)
- [ ] **Validation:** Run data integrity checks on all partitions
- [ ] **Duration:** 30-45 minutes

### ✅ Phase 2: reg_bqx_* Rebuild (Higher Risk)

- [ ] **Update worker script:** populate_regression_features_worker.py
  - [ ] Implement fit_parabola_with_terms() function
  - [ ] Update to calculate quadratic_term, linear_term, constant_term, residual
  - [ ] Align windows: w60, w90, w150, w240, w390, w630
- [ ] **Update schema:** Create new reg_bqx_* tables with term-based columns
- [ ] **Test on single partition:** reg_bqx_eurusd_2024_07
  - [ ] Run worker script
  - [ ] Validate term values are interpretable
  - [ ] Verify prediction = sum of terms
- [ ] **Roll out to all partitions:** 336 partitions
- [ ] **Validation:** Compare with reg_rate_* for consistency
- [ ] **Duration:** 2-3 hours (parallel execution)

### ✅ Phase 3: Covariance Features

- [ ] **Update correlation worker:** correlation_features_worker_v5.py
  - [ ] Add calculate_term_covariances() function
  - [ ] Use quadratic_term, linear_term, residual from reg_bqx_*
  - [ ] Calculate rolling 60-min covariances
- [ ] **Update schema:** Add 6 covariance columns to correlation_bqx_* tables
- [ ] **Test:** Single partition validation
- [ ] **Roll out:** All 336 partitions
- [ ] **Duration:** 1-2 hours

---

## 7. Risk Assessment

### ✅ Low Risk Items

**reg_rate_* migration:**
- ✅ Additive only (adding columns, not removing)
- ✅ Preserves existing data
- ✅ Can rollback easily (drop added columns)
- ✅ No worker script changes needed
- **Risk Level:** LOW

### ⚠️ Medium Risk Items

**reg_bqx_* rebuild:**
- ⚠️ Requires re-running worker script
- ⚠️ Drops and recreates tables
- ⚠️ 2-3 hours of computation
- ⚠️ Potential data loss if not backed up
- **Risk Level:** MEDIUM

**Mitigation:**
- Snapshot before rebuild
- Test on single partition first
- Keep old tables until validation complete
- Parallel validation queries

---

## 8. Cost Analysis

### Aurora Storage Impact

**Current Schema:**
- reg_rate_*: 9 columns × 6 windows = 54 columns per partition
- Adding: 6 constant_term columns
- **New Total:** 60 columns per partition
- **Storage Increase:** ~11% (6/54 = 11.1%)

**reg_bqx_* Schema:**
- Current: 15 columns × 6 windows = 90 columns
- New: 7 columns × 6 windows = 42 columns
- **Storage Decrease:** ~53% (48/90 = 53.3%)

**Net Impact:** Minimal (slight reduction overall)

### Compute Cost

**Migration Execution:**
- reg_rate_* update: ~30 min (on trillium-master t3.2xlarge = $0.16)
- reg_bqx_* rebuild: ~2-3 hours (8 workers = $0.50-0.75)
- **Total:** ~$1

**Ongoing:** No additional cost (same feature calculation)

---

## 9. Next Steps

### Immediate Actions

1. **Test Migration on Single Partition:**
   ```bash
   # Add constant_term to reg_eurusd_2024_07
   psql -h <host> -U postgres -d bqx -f scripts/migration/add_constant_term_single_partition.sql

   # Validate
   psql -h <host> -U postgres -d bqx -f scripts/migration/validate_constant_term.sql
   ```

2. **Update Worker Script:**
   ```bash
   # Edit populate_regression_features_worker.py
   # Implement fit_parabola_with_terms()
   # Test on single pair/month
   python3 scripts/ml/populate_regression_features_worker.py --pair eurusd --month 2024_07 --test
   ```

3. **Full Migration:**
   ```bash
   # Roll out to all partitions (after testing)
   bash scripts/migration/migrate_all_reg_tables.sh
   ```

---

## Summary

**Current State:**
- ✅ Aurora credentials retrieved
- ✅ Schema analyzed (both reg_rate_* and reg_bqx_*)
- ✅ Sample data validated
- ✅ Migration plan documented

**Current Issues:**
- ⚠️ reg_rate_*: Missing constant_term
- ❌ reg_bqx_*: Stores coefficients (not terms)
- ⚠️ Window misalignment between reg_rate and reg_bqx

**Required Changes:**
1. Add constant_term to reg_rate_* (30 min migration)
2. Rebuild reg_bqx_* with term-based schema (2-3 hours)
3. Align windows across both domains
4. Add covariance features to correlation_bqx_* (1-2 hours)

**Total Migration Time:** ~4-5 hours

**Ready to Proceed:** ✅ YES (pending user approval)

---

**Database Connection:**
- Host: trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com
- Database: bqx
- User: postgres
- Password: Retrieved from bqx-mirror/bqx/aurora/master
- Status: ✅ CONNECTED

**Validation Date:** 2025-11-15
