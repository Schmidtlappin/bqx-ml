# Complete Remediation Plan - 100% Schema Alignment
**Date:** 2025-11-15
**Goal:** Achieve 100% alignment between reg_rate and reg_bqx for maximum ML effectiveness
**Status:** COMPREHENSIVE PLAN - READY FOR EXECUTION

---

## Executive Summary

**Current State: 40% Aligned**
- ✅ Both use normalized data sources (rate_index, BQX)
- ❌ Window misalignment (only 1 of 6 windows overlap)
- ❌ Missing term-based architecture (coefficients instead of terms)
- ❌ Missing constant_term in reg_rate
- ❌ Missing residual in reg_bqx
- ❌ Covariance features not implemented

**Target State: 100% Aligned**
- ✅ Identical window structure (w60, w90, w150, w240, w390, w630)
- ✅ Identical term-based architecture (quadratic_term, linear_term, constant_term, residual)
- ✅ Identical schema structure (7 features per window)
- ✅ Covariance features implemented (6 features per domain)
- ✅ Full cross-domain, cross-pair, cross-window comparability

**Remediation Stages:** 5 stages (2.11 - 2.15)
**Total Duration:** 8-10 hours
**Total Cost:** $2-3 (on trillium-master t3.2xlarge)
**Risk Level:** MEDIUM (requires data rebuild)

---

## Part 1: Remediation Stages

### Stage 2.11: Schema Migration - reg_rate_* Enhancement

**Objective:** Add missing constant_term column to all reg_rate_* partitions

**Duration:** 30 minutes
**Cost:** $0.16
**Risk:** LOW (additive only, no data loss)

**Actions:**
1. Add w*_constant_term columns (6 windows × 28 pairs × 12 months = 336 partitions)
2. Populate constant_term from w*_c_coef (constant_term = c_coef)
3. Add schema comments documenting rate_index source
4. Validate data integrity (constant_term matches c_coef)

**SQL Migration:**
```sql
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

            -- Add constant_term columns
            EXECUTE format('
                ALTER TABLE bqx.%I
                ADD COLUMN IF NOT EXISTS w60_constant_term DOUBLE PRECISION,
                ADD COLUMN IF NOT EXISTS w90_constant_term DOUBLE PRECISION,
                ADD COLUMN IF NOT EXISTS w150_constant_term DOUBLE PRECISION,
                ADD COLUMN IF NOT EXISTS w240_constant_term DOUBLE PRECISION,
                ADD COLUMN IF NOT EXISTS w390_constant_term DOUBLE PRECISION,
                ADD COLUMN IF NOT EXISTS w630_constant_term DOUBLE PRECISION
            ', partition_name);

            -- Populate from c_coef
            EXECUTE format('
                UPDATE bqx.%I SET
                w60_constant_term = w60_c_coef,
                w90_constant_term = w90_c_coef,
                w150_constant_term = w150_c_coef,
                w240_constant_term = w240_c_coef,
                w390_constant_term = w390_c_coef,
                w630_constant_term = w630_c_coef
            ', partition_name);

            RAISE NOTICE 'Updated: %', partition_name;
        END LOOP;
    END LOOP;
END $$;

-- Add table comments
DO $$
DECLARE pair_name TEXT;
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
        EXECUTE format('
            COMMENT ON TABLE bqx.reg_%s IS
            ''Regression features calculated from rate_index (normalized forex rate).
            Source: rate_index column from m1_%s table (normalized to 100 at t=0).
            Term-based architecture: quadratic_term, linear_term, constant_term, residual.
            NOT calculated from absolute rate values.''
        ', pair_name, pair_name);
    END LOOP;
END $$;
```

**Validation:**
```sql
-- Verify constant_term = c_coef
SELECT COUNT(*) FROM bqx.reg_eurusd_2024_07
WHERE ABS(w60_constant_term - w60_c_coef) > 0.000001;
-- Expected: 0

-- Verify prediction integrity
SELECT COUNT(*) FROM bqx.reg_eurusd_2024_07
WHERE ABS(w60_yhat_end - (w60_a_term + w60_b_term + w60_constant_term)) > 0.001;
-- Expected: 0
```

**AirTable Entry:**
```python
{
    'stage_id': '2.11 - reg_rate Schema Enhancement',
    'stage_code': 'BQX-2.11',
    'status': 'Todo',
    'description': 'Add constant_term columns to all reg_rate_* partitions for term-based architecture completion',
    'duration': '30 minutes',
    'estimated_cost': 0.16,
    'workers': 1,
    'features_added': 6,  # 6 constant_term columns (one per window)
    'partitions_affected': 336
}
```

---

### Stage 2.12: Schema Rebuild - reg_bqx_* Complete Overhaul

**Objective:** Rebuild all reg_bqx_* tables with aligned windows and term-based architecture

**Duration:** 3-4 hours
**Cost:** $1.00-1.30
**Risk:** MEDIUM (requires re-computation, backup recommended)

**Current Issues:**
- ❌ Wrong windows: {15, 30, 45, 60, 75, agg}
- ❌ Stores coefficients: {a2, a1, b}
- ❌ Missing terms: {quadratic_term, linear_term, constant_term}
- ❌ Missing residual column
- ❌ Extra derived metrics not needed (vertex, curvature, extrapolation_error)

**Target Schema (per window):**
```sql
CREATE TABLE bqx.reg_bqx_{pair} (
    ts_utc TIMESTAMPTZ NOT NULL,

    -- Window 60 (60 minutes)
    w60_quadratic_term DOUBLE PRECISION,   -- a₂ · x_end²
    w60_linear_term DOUBLE PRECISION,      -- a₁ · x_end
    w60_constant_term DOUBLE PRECISION,    -- a₀
    w60_residual DOUBLE PRECISION,         -- y_actual - ŷ
    w60_r2 DOUBLE PRECISION,               -- R² fit quality
    w60_rmse DOUBLE PRECISION,             -- Root mean squared error
    w60_prediction DOUBLE PRECISION,       -- ŷ = quad + lin + const

    -- Repeat for w90, w150, w240, w390, w630

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

**Migration Steps:**

1. **Backup existing reg_bqx_* tables:**
```sql
-- Create backup schema
CREATE SCHEMA IF NOT EXISTS bqx_backup_2025_11_15;

-- Backup each partition
DO $$
DECLARE
    pair_name TEXT;
    year_month TEXT;
BEGIN
    FOR pair_name IN SELECT unnest(ARRAY[...]) LOOP
        FOR year_month IN SELECT unnest(ARRAY[...]) LOOP
            EXECUTE format('
                CREATE TABLE bqx_backup_2025_11_15.reg_bqx_%s_%s AS
                SELECT * FROM bqx.reg_bqx_%s_%s
            ', pair_name, year_month, pair_name, year_month);
        END LOOP;
    END LOOP;
END $$;
```

2. **Drop existing reg_bqx_* tables:**
```sql
DROP TABLE IF EXISTS bqx.reg_bqx_audcad CASCADE;
DROP TABLE IF EXISTS bqx.reg_bqx_audchf CASCADE;
-- ... (all 28 pairs)
```

3. **Create new schema:**
```bash
psql -h <host> -U postgres -d bqx -f scripts/refactor/create_reg_bqx_term_based_schema.sql
```

4. **Re-run worker script with updated windows:**
```python
# Update populate_regression_features_worker.py
WINDOWS_BQX = [60, 90, 150, 240, 390, 630]  # Aligned with reg_rate

def fit_parabola_with_terms_bqx(x, y):
    """
    Fit parabola on BQX data and return TERMS (not coefficients).
    """
    # DO NOT normalize x
    coeffs = np.polyfit(x, y, deg=2)
    a2, a1, a0 = coeffs

    x_end = x[-1]

    # Calculate TERMS in BQX units
    quadratic_term = a2 * (x_end ** 2)
    linear_term = a1 * x_end
    constant_term = a0

    # Prediction and residual
    prediction = quadratic_term + linear_term + constant_term
    y_actual = y[-1]
    residual = y_actual - prediction

    return {
        'quadratic_term': float(quadratic_term),
        'linear_term': float(linear_term),
        'constant_term': float(constant_term),
        'residual': float(residual),
        'r2': calculate_r2(y, coeffs),
        'rmse': calculate_rmse(y, coeffs),
        'prediction': float(prediction)
    }
```

5. **Execute parallel population:**
```bash
# Run with 8 parallel workers
python3 scripts/ml/populate_regression_features_worker.py \
    --domain bqx \
    --max-workers 8 \
    --windows 60,90,150,240,390,630 \
    --all-pairs \
    --all-months
```

**Validation:**
```sql
-- Check window alignment
SELECT COUNT(DISTINCT column_name)
FROM information_schema.columns
WHERE table_name = 'reg_bqx_eurusd_2024_07'
AND column_name ~ '^w(60|90|150|240|390|630)_';
-- Expected: 42 (7 features × 6 windows)

-- Verify term-based calculations
SELECT ts_utc,
       w60_quadratic_term, w60_linear_term, w60_constant_term,
       w60_prediction,
       ABS(w60_prediction - (w60_quadratic_term + w60_linear_term + w60_constant_term)) AS calc_error
FROM bqx.reg_bqx_eurusd_2024_07
WHERE w60_prediction IS NOT NULL
LIMIT 10;
-- Expected: calc_error < 0.000001
```

**AirTable Entry:**
```python
{
    'stage_id': '2.12 - reg_bqx Complete Rebuild',
    'stage_code': 'BQX-2.12',
    'status': 'Todo',
    'description': 'Rebuild all reg_bqx_* tables with aligned windows (60,90,150,240,390,630) and term-based architecture',
    'duration': '3-4 hours',
    'estimated_cost': 1.20,
    'workers': 8,
    'features_added': 42,  # 7 features × 6 windows per partition
    'partitions_affected': 336,
    'backup_required': True
}
```

---

### Stage 2.13: Column Rename for Clarity (Optional)

**Objective:** Rename columns to use semantic names (quadratic_term, linear_term vs a_term, b_term)

**Duration:** 1 hour
**Cost:** $0.33
**Risk:** MEDIUM (schema change, requires application updates)

**Recommended:** SKIP (keep existing names for backward compatibility)

**Alternative:** Add column aliases in views:
```sql
-- Create view with semantic names
CREATE OR REPLACE VIEW bqx.reg_eurusd_semantic AS
SELECT
    ts_utc,
    rate_index,
    w60_a_term AS w60_quadratic_term,
    w60_b_term AS w60_linear_term,
    w60_constant_term,
    w60_resid_end AS w60_residual,
    w60_r2,
    w60_rmse,
    w60_yhat_end AS w60_prediction
FROM bqx.reg_eurusd_2024_07;
```

**AirTable Entry:** SKIP (optional stage)

---

### Stage 2.14: Covariance Features Implementation

**Objective:** Add 6 term covariance features to all correlation_bqx_* tables

**Duration:** 2-3 hours
**Cost:** $0.66-1.00
**Risk:** LOW (new features, non-destructive)

**Schema Update:**
```sql
-- Add covariance columns to correlation_bqx_* tables
DO $$
DECLARE
    pair_name TEXT;
    year_month TEXT;
    partition_name TEXT;
BEGIN
    FOR pair_name IN SELECT unnest(ARRAY[...]) LOOP
        FOR year_month IN SELECT unnest(ARRAY[...]) LOOP
            partition_name := 'correlation_bqx_' || pair_name || '_' || year_month;

            EXECUTE format('
                ALTER TABLE bqx.%I
                ADD COLUMN IF NOT EXISTS cov_quad_lin_bqx_60min DOUBLE PRECISION,
                ADD COLUMN IF NOT EXISTS cov_resid_quad_bqx_60min DOUBLE PRECISION,
                ADD COLUMN IF NOT EXISTS cov_resid_lin_bqx_60min DOUBLE PRECISION,
                ADD COLUMN IF NOT EXISTS corr_quad_lin_bqx_60min DOUBLE PRECISION,
                ADD COLUMN IF NOT EXISTS corr_resid_quad_bqx_60min DOUBLE PRECISION,
                ADD COLUMN IF NOT EXISTS corr_resid_lin_bqx_60min DOUBLE PRECISION
            ', partition_name);
        END LOOP;
    END LOOP;
END $$;
```

**Worker Update:**
```python
# In correlation_features_worker_v5.py

def calculate_term_covariances(df_reg_bqx, window_size=60):
    """
    Calculate rolling covariances between regression term components.

    Args:
        df_reg_bqx: DataFrame with reg_bqx data for past 60+ minutes
        window_size: Rolling window (default 60 minutes)

    Returns:
        dict: 6 covariance/correlation features
    """
    if len(df_reg_bqx) < window_size:
        return {k: None for k in [
            'cov_quad_lin_bqx_60min', 'cov_resid_quad_bqx_60min',
            'cov_resid_lin_bqx_60min', 'corr_quad_lin_bqx_60min',
            'corr_resid_quad_bqx_60min', 'corr_resid_lin_bqx_60min'
        ]}

    # Use last 60 minutes
    window_df = df_reg_bqx.tail(window_size)

    # Calculate covariances (using w60 window terms)
    cov_quad_lin = window_df['w60_quadratic_term'].cov(
        window_df['w60_linear_term']
    )

    cov_resid_quad = window_df['w60_residual'].cov(
        window_df['w60_quadratic_term']
    )

    cov_resid_lin = window_df['w60_residual'].cov(
        window_df['w60_linear_term']
    )

    # Calculate correlations (normalized [-1, 1])
    corr_quad_lin = window_df['w60_quadratic_term'].corr(
        window_df['w60_linear_term']
    )

    corr_resid_quad = window_df['w60_residual'].corr(
        window_df['w60_quadratic_term']
    )

    corr_resid_lin = window_df['w60_residual'].corr(
        window_df['w60_linear_term']
    )

    return {
        'cov_quad_lin_bqx_60min': float(cov_quad_lin) if not pd.isna(cov_quad_lin) else None,
        'cov_resid_quad_bqx_60min': float(cov_resid_quad) if not pd.isna(cov_resid_quad) else None,
        'cov_resid_lin_bqx_60min': float(cov_resid_lin) if not pd.isna(cov_resid_lin) else None,
        'corr_quad_lin_bqx_60min': float(corr_quad_lin) if not pd.isna(corr_quad_lin) else None,
        'corr_resid_quad_bqx_60min': float(corr_resid_quad) if not pd.isna(corr_resid_quad) else None,
        'corr_resid_lin_bqx_60min': float(corr_resid_lin) if not pd.isna(corr_resid_lin) else None
    }

def populate_correlation_for_pair(pair, year_month):
    """Update to include covariance features."""

    # ... existing code to load cross-pair correlations ...

    # Load reg_bqx data for term covariances
    reg_bqx_query = f"""
    SELECT ts_utc,
           w60_quadratic_term, w60_linear_term, w60_constant_term, w60_residual
    FROM bqx.reg_bqx_{pair}_{year_month}
    ORDER BY ts_utc;
    """
    df_reg_bqx = pd.read_sql(reg_bqx_query, conn)

    # Calculate features for each timestamp
    results = []
    for i in range(len(df_reg_bqx)):
        # Existing 45 correlation features
        existing_features = calculate_cross_pair_correlations(...)

        # NEW: 6 term covariance features
        term_cov_features = calculate_term_covariances(
            df_reg_bqx.iloc[:i+1],  # All data up to current timestamp
            window_size=60
        )

        # Combine
        row_features = {**existing_features, **term_cov_features}
        results.append(row_features)

    # Insert into correlation_bqx table
    # ...
```

**Execution:**
```bash
python3 scripts/ml/correlation_features_worker_v5.py \
    --max-workers 8 \
    --all-pairs \
    --all-months \
    --include-term-covariances
```

**Validation:**
```sql
-- Check covariance features populated
SELECT COUNT(*) FROM bqx.correlation_bqx_eurusd_2024_07
WHERE cov_quad_lin_bqx_60min IS NOT NULL;
-- Expected: ~32000 (most rows)

-- Check correlation range [-1, 1]
SELECT MIN(corr_quad_lin_bqx_60min), MAX(corr_quad_lin_bqx_60min)
FROM bqx.correlation_bqx_eurusd_2024_07;
-- Expected: -1 to 1
```

**AirTable Entry:**
```python
{
    'stage_id': '2.14 - Term Covariance Features',
    'stage_code': 'BQX-2.14',
    'status': 'Todo',
    'description': 'Add 6 term covariance features to all correlation_bqx_* tables for trend exhaustion, breakout, and regime change detection',
    'duration': '2-3 hours',
    'estimated_cost': 0.80,
    'workers': 8,
    'features_added': 6,  # Per partition
    'partitions_affected': 336
}
```

---

### Stage 2.15: Validation & Documentation

**Objective:** Comprehensive validation of 100% alignment and documentation updates

**Duration:** 1 hour
**Cost:** $0.33
**Risk:** NONE (read-only validation)

**Validation Queries:**

1. **Schema Alignment:**
```sql
-- Verify reg_rate and reg_bqx have same columns per window
SELECT
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_name = 'reg_eurusd_2024_07' AND column_name ~ '^w60_') AS reg_rate_w60_cols,
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_name = 'reg_bqx_eurusd_2024_07' AND column_name ~ '^w60_') AS reg_bqx_w60_cols;
-- Expected: Same count (7 columns each)
```

2. **Window Alignment:**
```sql
-- Extract windows from both tables
WITH reg_rate_windows AS (
    SELECT DISTINCT regexp_replace(column_name, '_.*', '') AS window
    FROM information_schema.columns
    WHERE table_name = 'reg_eurusd_2024_07' AND column_name ~ '^w[0-9]+'
),
reg_bqx_windows AS (
    SELECT DISTINCT regexp_replace(column_name, '_.*', '') AS window
    FROM information_schema.columns
    WHERE table_name = 'reg_bqx_eurusd_2024_07' AND column_name ~ '^w[0-9]+'
)
SELECT
    r.window AS reg_rate_window,
    b.window AS reg_bqx_window,
    CASE WHEN r.window = b.window THEN '✅ Aligned' ELSE '❌ Misaligned' END AS status
FROM reg_rate_windows r
FULL OUTER JOIN reg_bqx_windows b ON r.window = b.window
ORDER BY r.window;
-- Expected: All ✅ Aligned
```

3. **Data Integrity:**
```sql
-- Verify term calculations
SELECT
    ts_utc,
    w60_quadratic_term, w60_linear_term, w60_constant_term,
    w60_prediction,
    w60_residual,
    rate_index,
    -- Check prediction = sum of terms
    ABS(w60_prediction - (w60_quadratic_term + w60_linear_term + w60_constant_term)) AS pred_error,
    -- Check residual = actual - prediction
    ABS(w60_residual - (rate_index - w60_prediction)) AS resid_error
FROM bqx.reg_eurusd_2024_07
WHERE w60_prediction IS NOT NULL
LIMIT 100;
-- Expected: pred_error < 0.001, resid_error < 0.001
```

4. **Covariance Features:**
```sql
-- Check covariance coverage
SELECT
    COUNT(*) AS total_rows,
    COUNT(cov_quad_lin_bqx_60min) AS cov_quad_lin_count,
    COUNT(corr_quad_lin_bqx_60min) AS corr_quad_lin_count,
    ROUND(100.0 * COUNT(cov_quad_lin_bqx_60min) / COUNT(*), 2) AS coverage_pct
FROM bqx.correlation_bqx_eurusd_2024_07;
-- Expected: coverage_pct > 99%
```

5. **Cross-Domain Comparability:**
```sql
-- Join reg_rate and reg_bqx at same timestamp
SELECT
    r.ts_utc,
    r.w60_quadratic_term AS rate_quad,
    b.w60_quadratic_term AS bqx_quad,
    r.w60_r2 AS rate_r2,
    b.w60_r2 AS bqx_r2,
    CASE
        WHEN r.w60_r2 IS NOT NULL AND b.w60_r2 IS NOT NULL THEN '✅ Comparable'
        ELSE '❌ Missing data'
    END AS comparability
FROM bqx.reg_eurusd_2024_07 r
JOIN bqx.reg_bqx_eurusd_2024_07 b ON r.ts_utc = b.ts_utc
LIMIT 100;
-- Expected: All ✅ Comparable
```

**Documentation Updates:**

1. **Schema Documentation:**
```sql
-- Add comprehensive table comments
COMMENT ON TABLE bqx.reg_eurusd IS
'Regression features calculated from rate_index (normalized forex rate ~100).
Term-based architecture with 6 windows: w60, w90, w150, w240, w390, w630.
Features per window: quadratic_term, linear_term, constant_term, residual, r2, rmse, prediction.
Fully aligned with reg_bqx for cross-domain ML analysis.';

COMMENT ON TABLE bqx.reg_bqx_eurusd IS
'Regression features calculated from BQX values (backward cumulative return).
Term-based architecture with 6 windows: w60, w90, w150, w240, w390, w630.
Features per window: quadratic_term, linear_term, constant_term, residual, r2, rmse, prediction.
Fully aligned with reg_rate for cross-domain ML analysis.';

COMMENT ON TABLE bqx.correlation_bqx_eurusd IS
'Cross-pair correlations (45 features) + term covariances (6 features) = 51 features total.
Term covariances detect: trend exhaustion, breakouts, regime changes.
Calculated on 60-minute rolling window from reg_bqx term components.';
```

2. **README Updates:**
```markdown
# BQX ML - Term-Based Regression Architecture

## Schema Alignment (100% Complete ✅)

### Dual-Domain Architecture
- **reg_rate_***: Rate index domain (~100 scale)
- **reg_bqx_***: BQX domain (~0.001 scale)
- **100% Aligned**: Same windows, same features, fully comparable

### Windows (Aligned)
w60, w90, w150, w240, w390, w630

### Features per Window (7 features)
1. quadratic_term (a₂ · x_end²)
2. linear_term (a₁ · x_end)
3. constant_term (a₀)
4. residual (y_actual - ŷ)
5. r2 (fit quality)
6. rmse (error magnitude)
7. prediction (ŷ = quad + lin + const)

### Term Covariance Features (6 features)
1. cov_quad_lin_bqx_60min (trend exhaustion detector)
2. cov_resid_quad_bqx_60min (regime change detector)
3. cov_resid_lin_bqx_60min (breakout detector)
4. corr_quad_lin_bqx_60min (normalized [-1,1])
5. corr_resid_quad_bqx_60min (normalized [-1,1])
6. corr_resid_lin_bqx_60min (normalized [-1,1])
```

**AirTable Entry:**
```python
{
    'stage_id': '2.15 - Alignment Validation',
    'stage_code': 'BQX-2.15',
    'status': 'Todo',
    'description': 'Comprehensive validation of 100% schema alignment and documentation updates',
    'duration': '1 hour',
    'estimated_cost': 0.33,
    'workers': 1,
    'features_added': 0,
    'validation_queries': 5
}
```

---

## Part 2: Summary of Remediation Stages

| Stage | Description | Duration | Cost | Risk | Features | Partitions |
|-------|-------------|----------|------|------|----------|------------|
| **2.11** | reg_rate Enhancement | 30 min | $0.16 | LOW | 6 | 336 |
| **2.12** | reg_bqx Complete Rebuild | 3-4 hrs | $1.20 | MEDIUM | 42 | 336 |
| **2.13** | Column Rename (SKIP) | - | - | - | - | - |
| **2.14** | Covariance Features | 2-3 hrs | $0.80 | LOW | 6 | 336 |
| **2.15** | Validation | 1 hr | $0.33 | NONE | 0 | 672 |
| **TOTAL** | **Complete Remediation** | **7-9 hrs** | **$2.49** | **MEDIUM** | **54** | **1,344** |

---

## Part 3: Execution Plan

### Pre-Execution Checklist

- [ ] **Backup Aurora cluster** (automated snapshot)
- [ ] **Test on single partition** (reg_eurusd_2024_07, reg_bqx_eurusd_2024_07)
- [ ] **Validate test partition** (run all validation queries)
- [ ] **Review worker scripts** (ensure term-based calculations correct)
- [ ] **Set maintenance window** (7-9 hours, minimal impact)

### Execution Sequence

**Phase 1: reg_rate Enhancement (30 min)**
```bash
# Run Stage 2.11
psql -h <host> -U postgres -d bqx -f scripts/remediation/stage_2_11_add_constant_term.sql

# Validate
psql -h <host> -U postgres -d bqx -f scripts/remediation/validate_stage_2_11.sql
```

**Phase 2: reg_bqx Rebuild (3-4 hours)**
```bash
# Backup existing tables
psql -h <host> -U postgres -d bqx -f scripts/remediation/backup_reg_bqx_tables.sql

# Drop and recreate schema
psql -h <host> -U postgres -d bqx -f scripts/remediation/create_reg_bqx_term_based_schema.sql

# Re-run worker (parallel execution)
python3 scripts/ml/populate_regression_features_worker.py \
    --domain bqx \
    --max-workers 8 \
    --windows 60,90,150,240,390,630 \
    --all-pairs \
    --all-months

# Validate
psql -h <host> -U postgres -d bqx -f scripts/remediation/validate_stage_2_12.sql
```

**Phase 3: Covariance Features (2-3 hours)**
```bash
# Add covariance columns
psql -h <host> -U postgres -d bqx -f scripts/remediation/stage_2_14_add_covariance_columns.sql

# Run correlation worker (parallel execution)
python3 scripts/ml/correlation_features_worker_v5.py \
    --max-workers 8 \
    --all-pairs \
    --all-months \
    --include-term-covariances

# Validate
psql -h <host> -U postgres -d bqx -f scripts/remediation/validate_stage_2_14.sql
```

**Phase 4: Final Validation (1 hour)**
```bash
# Run comprehensive validation
psql -h <host> -U postgres -d bqx -f scripts/remediation/validate_100_percent_alignment.sql

# Generate validation report
python3 scripts/remediation/generate_alignment_report.py
```

### Post-Execution Validation

- [ ] **All validation queries pass** (100% alignment confirmed)
- [ ] **No data loss** (row counts match original)
- [ ] **Cross-domain queries work** (reg_rate JOIN reg_bqx successful)
- [ ] **Covariance features populated** (>99% coverage)
- [ ] **Documentation updated** (README, schema comments)
- [ ] **AirTable updated** (all stages marked complete)

---

## Part 4: Rollback Plan

**If Stage 2.11 fails (reg_rate enhancement):**
```sql
-- Simple rollback: drop added columns
ALTER TABLE bqx.reg_eurusd_2024_07
DROP COLUMN w60_constant_term,
DROP COLUMN w90_constant_term,
-- ...
```
**Impact:** None (original data preserved)

**If Stage 2.12 fails (reg_bqx rebuild):**
```sql
-- Restore from backup
CREATE TABLE bqx.reg_bqx_eurusd_2024_07 AS
SELECT * FROM bqx_backup_2025_11_15.reg_bqx_eurusd_2024_07;
```
**Impact:** Revert to original schema (misaligned windows)

**If Stage 2.14 fails (covariance features):**
```sql
-- Drop added columns
ALTER TABLE bqx.correlation_bqx_eurusd_2024_07
DROP COLUMN cov_quad_lin_bqx_60min,
-- ...
```
**Impact:** None (original correlation features preserved)

---

## Part 5: Success Criteria

### 100% Alignment Checklist

- [ ] ✅ **Windows Aligned:** reg_rate and reg_bqx have identical windows {60, 90, 150, 240, 390, 630}
- [ ] ✅ **Schema Aligned:** Both have identical 7 features per window
- [ ] ✅ **Term-Based:** Both calculate quadratic_term, linear_term, constant_term (not coefficients)
- [ ] ✅ **Residual Added:** Both have residual column (y_actual - prediction)
- [ ] ✅ **Covariance Features:** All 6 term covariances calculated and stored
- [ ] ✅ **Data Integrity:** Prediction = sum of terms, Residual = actual - prediction
- [ ] ✅ **Cross-Domain Comparable:** Can JOIN reg_rate and reg_bqx at same timestamps
- [ ] ✅ **No Data Loss:** All original rows preserved
- [ ] ✅ **Documentation Complete:** Schema comments, README, validation queries
- [ ] ✅ **AirTable Updated:** All remediation stages documented

### ML-Ready Criteria

- [ ] ✅ **Feature Matrix Complete:** All 730+ features available
- [ ] ✅ **Cross-Feature Correlations:** Can calculate correlations across all features
- [ ] ✅ **Cross-Pair Correlations:** Can compare EURUSD vs GBPUSD features
- [ ] ✅ **Cross-Window Correlations:** Can compare w60 vs w90 features
- [ ] ✅ **Cross-Domain Correlations:** Can compare reg_rate vs reg_bqx features
- [ ] ✅ **Term Covariances:** Trend exhaustion, breakout, regime change detectors ready
- [ ] ✅ **Triangulation Ready:** Multiple domains, pairs, windows for robust ML

---

**Status:** Comprehensive remediation plan complete ✅
**Next Action:** Execute Stage 2.11 (test on single partition first)
**Expected Outcome:** 100% schema alignment, full ML feature matrix ready
