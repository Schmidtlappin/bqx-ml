# Term-Based Regression Architecture - Implementation Plan
**Date:** 2025-11-15
**Decision:** Store regression TERMS instead of raw COEFFICIENTS
**Rationale:** Terms are interpretable, comparable, and ML-valuable

---

## Executive Summary

**DECISION**: Update BQX ML regression schema to store **evaluated terms** instead of raw coefficients.

**Changes**:
- OLD: Store `a2, a1, b` (coefficients on normalized x)
- NEW: Store `quadratic_term, linear_term, constant_term, residual` (evaluated at window end)

**Benefits**:
- ✅ All values in rate_index units (~100) - interpretable
- ✅ Cross-window comparable (same units)
- ✅ ML-ready (decomposed contributions)
- ✅ Residuals capture model uncertainty and regime changes

---

## Mathematical Foundation

### Parabolic Regression Model

```
y(x) = a₂·x² + a₁·x + a₀
```

**At window end (x = window_size - 1)**:
```python
# For w15 window: x_end = 14
quadratic_term = a₂ × (14)²
linear_term = a₁ × 14
constant_term = a₀
predicted = quadratic_term + linear_term + constant_term

# Actual value
y_actual = rate_index[current_timestamp]

# Residual (fit error)
residual = y_actual - predicted
```

### Terms vs Coefficients

| Concept | Coefficient | Term (Evaluated) |
|---------|------------|------------------|
| **Quadratic** | a₂ = -0.0001 | a₂·(14)² = -0.0196 |
| **Linear** | a₁ = 0.005 | a₁·14 = 0.07 |
| **Constant** | a₀ = 100.0 | a₀ = 100.0 |
| **Units** | Abstract | rate_index units |
| **Interpretable?** | ❌ No | ✅ Yes |

---

## Schema Updates Required

### Current Schema (WRONG)

```sql
-- reg_rate_eurusd_2024_07
a2_idx_w15 NUMERIC,  -- Coefficient (not interpretable)
a1_idx_w15 NUMERIC,  -- Coefficient (not interpretable)
b_idx_w15 NUMERIC,   -- Coefficient
```

### Updated Schema (CORRECT)

```sql
-- reg_rate_eurusd_2024_07
quadratic_term_idx_w15 DOUBLE PRECISION,  -- a₂·x² at x=14
linear_term_idx_w15 DOUBLE PRECISION,     -- a₁·x at x=14
constant_term_idx_w15 DOUBLE PRECISION,   -- a₀
residual_idx_w15 DOUBLE PRECISION,        -- y - ŷ

-- Additional quality metrics
r2_idx_w15 DOUBLE PRECISION,
rmse_idx_w15 DOUBLE PRECISION,
prediction_idx_w15 DOUBLE PRECISION,  -- Sum of terms
```

### Full Schema (All Windows)

```sql
CREATE TABLE bqx.reg_rate_{pair}_{year_month} (
    ts_utc TIMESTAMPTZ NOT NULL,
    
    -- Window w15 (15 minutes) - evaluated at x=14
    quadratic_term_idx_w15 DOUBLE PRECISION,
    linear_term_idx_w15 DOUBLE PRECISION,
    constant_term_idx_w15 DOUBLE PRECISION,
    residual_idx_w15 DOUBLE PRECISION,
    r2_idx_w15 DOUBLE PRECISION,
    rmse_idx_w15 DOUBLE PRECISION,
    prediction_idx_w15 DOUBLE PRECISION,
    
    -- Window w30 (30 minutes) - evaluated at x=29
    quadratic_term_idx_w30 DOUBLE PRECISION,
    linear_term_idx_w30 DOUBLE PRECISION,
    constant_term_idx_w30 DOUBLE PRECISION,
    residual_idx_w30 DOUBLE PRECISION,
    r2_idx_w30 DOUBLE PRECISION,
    rmse_idx_w30 DOUBLE PRECISION,
    prediction_idx_w30 DOUBLE PRECISION,
    
    -- Window w45 (45 minutes) - evaluated at x=44
    quadratic_term_idx_w45 DOUBLE PRECISION,
    linear_term_idx_w45 DOUBLE PRECISION,
    constant_term_idx_w45 DOUBLE PRECISION,
    residual_idx_w45 DOUBLE PRECISION,
    r2_idx_w45 DOUBLE PRECISION,
    rmse_idx_w45 DOUBLE PRECISION,
    prediction_idx_w45 DOUBLE PRECISION,
    
    -- Window w60 (60 minutes) - evaluated at x=59
    quadratic_term_idx_w60 DOUBLE PRECISION,
    linear_term_idx_w60 DOUBLE PRECISION,
    constant_term_idx_w60 DOUBLE PRECISION,
    residual_idx_w60 DOUBLE PRECISION,
    r2_idx_w60 DOUBLE PRECISION,
    rmse_idx_w60 DOUBLE PRECISION,
    prediction_idx_w60 DOUBLE PRECISION,
    
    -- Window w75 (75 minutes) - evaluated at x=74
    quadratic_term_idx_w75 DOUBLE PRECISION,
    linear_term_idx_w75 DOUBLE PRECISION,
    constant_term_idx_w75 DOUBLE PRECISION,
    residual_idx_w75 DOUBLE PRECISION,
    r2_idx_w75 DOUBLE PRECISION,
    rmse_idx_w75 DOUBLE PRECISION,
    prediction_idx_w75 DOUBLE PRECISION,
    
    -- Window agg (90 minutes) - evaluated at x=89
    quadratic_term_idx_agg DOUBLE PRECISION,
    linear_term_idx_agg DOUBLE PRECISION,
    constant_term_idx_agg DOUBLE PRECISION,
    residual_idx_agg DOUBLE PRECISION,
    r2_idx_agg DOUBLE PRECISION,
    rmse_idx_agg DOUBLE PRECISION,
    prediction_idx_agg DOUBLE PRECISION,
    
    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);

-- Same structure for reg_bqx_{pair}_{year_month} (BQX domain)
```

**Features per table**: 7 metrics × 6 windows = 42 features per domain

---

## Worker Script Updates

### Updated fit_parabola() Function

```python
def fit_parabola_with_terms(x, y):
    """
    Fit parabola and return TERMS (not just coefficients).
    
    Returns:
        dict: quadratic_term, linear_term, constant_term, residual, r2, rmse, prediction
    """
    try:
        n = len(x)
        if n < 3:
            return {k: None for k in ['quadratic_term', 'linear_term', 'constant_term',
                                      'residual', 'r2', 'rmse', 'prediction']}
        
        # DO NOT normalize x - we want terms in original scale
        # x should be [0, 1, 2, ..., window_size-1]
        
        # Fit parabola: y = a2·x² + a1·x + a0
        coeffs = np.polyfit(x, y, deg=2)
        a2, a1, a0 = coeffs
        
        # Evaluate at END of window (most recent point)
        x_end = x[-1]  # Last x value (e.g., 14 for w15)
        
        # Calculate TERMS (evaluated expressions)
        quadratic_term = a2 * (x_end ** 2)
        linear_term = a1 * x_end
        constant_term = a0  # No x, so term = coefficient
        
        # Prediction (sum of terms)
        prediction = quadratic_term + linear_term + constant_term
        
        # Residual (actual - predicted)
        y_actual = y[-1]
        residual = y_actual - prediction
        
        # Quality metrics
        y_pred_all = np.polyval(coeffs, x)
        ss_res = np.sum((y - y_pred_all) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r2 = 1 - (ss_res / (ss_tot + 1e-10))
        rmse = np.sqrt(ss_res / n)
        
        return {
            'quadratic_term': float(quadratic_term),
            'linear_term': float(linear_term),
            'constant_term': float(constant_term),
            'residual': float(residual),
            'r2': float(r2),
            'rmse': float(rmse),
            'prediction': float(prediction)
        }
        
    except Exception as e:
        logger.warning(f"Regression fit failed: {e}")
        return {k: None for k in ['quadratic_term', 'linear_term', 'constant_term',
                                  'residual', 'r2', 'rmse', 'prediction']}
```

### Key Changes

1. **Remove x normalization**: We want terms in original rate_index scale
2. **Evaluate at x_end**: Calculate terms at last point in window
3. **Add residual**: y_actual - prediction
4. **Return terms, not coefficients**: ML-ready features

---

## ML Feature Usage

### Feature Interpretation

**Example: EURUSD at 2024-07-01 12:00:00**

```python
# Window w15 regression features
quadratic_term_idx_w15 = -0.06    # Curved trajectory pulling DOWN
linear_term_idx_w15 = 0.12        # Linear trend pushing UP
constant_term_idx_w15 = 100.01    # Baseline level
residual_idx_w15 = 0.03           # Model underestimates slightly

# Interpretation:
# - Net trend: +0.12 - 0.06 = +0.06 (slightly bullish)
# - Model fit: Small residual (0.03) = clean trend
# - Prediction: 100.01 + 0.12 - 0.06 = 100.07
# - Actual: 100.07 + 0.03 = 100.10
```

### ML Feature Engineering

```python
# Primary features (most predictive)
features = [
    'quadratic_term_idx_w15',  # Short-term curve
    'linear_term_idx_w15',     # Short-term trend
    'quadratic_term_idx_w60',  # Medium-term curve
    'linear_term_idx_w60',     # Medium-term trend
    'residual_idx_w15',        # Model uncertainty
    'residual_idx_w60',        # Medium-term fit
]

# Derived features (combinations)
df['net_momentum_w15'] = df['linear_term_idx_w15'] + df['quadratic_term_idx_w15']
df['trend_quality_w15'] = abs(df['residual_idx_w15'])  # Lower = cleaner trend
df['acceleration_w15'] = df['quadratic_term_idx_w15']  # Positive = accelerating

# Cross-window features
df['momentum_consistency'] = df['linear_term_idx_w15'] / (df['linear_term_idx_w60'] + 1e-10)
df['term_structure_slope'] = df['quadratic_term_idx_w60'] - df['quadratic_term_idx_w15']
```

### Residual-Based Features

**Residuals detect**:
1. **Regime changes**: Sudden residual spike = new pattern
2. **Model uncertainty**: High residual = volatile, unpredictable
3. **Anomalies**: Residual > 3σ = outlier event

```python
# Residual quality indicator
df['fit_quality_w15'] = 1.0 / (abs(df['residual_idx_w15']) + 0.01)

# Regime change detector
df['regime_change_w15'] = (abs(df['residual_idx_w15']) > 
                           df['residual_idx_w15'].rolling(60).std() * 2)

# Prediction confidence
df['confidence_w15'] = np.where(
    abs(df['residual_idx_w15']) < 0.05,
    'high',
    np.where(abs(df['residual_idx_w15']) < 0.10, 'medium', 'low')
)
```

---

## Implementation Checklist

### Phase 1: Schema Migration

- [ ] Create new schema with term-based columns
- [ ] Drop old coefficient-based columns
- [ ] Migrate existing data (if any) to new schema
- [ ] Update partition creation scripts

### Phase 2: Worker Script Updates

- [ ] Update `populate_regression_features_worker.py`
  - Remove x normalization
  - Implement `fit_parabola_with_terms()`
  - Calculate and store 4 terms per window
- [ ] Test with 1 partition (eurusd_2024_07)
- [ ] Validate output values are in rate_index units

### Phase 3: Validation

- [ ] Verify term values are ~100 scale (rate_index)
- [ ] Confirm prediction = quad + lin + const
- [ ] Confirm residual = y_actual - prediction
- [ ] Check cross-window comparability

### Phase 4: Documentation

- [ ] Update feature engineering guide
- [ ] Add ML interpretation examples
- [ ] Document residual usage patterns

---

## Benefits Summary

| Aspect | Coefficient Schema (OLD) | Term Schema (NEW) |
|--------|-------------------------|-------------------|
| **Interpretability** | ❌ Low | ✅ High |
| **Units** | Abstract (normalized x) | Rate index (~100) |
| **Cross-window comparable** | ❌ No | ✅ Yes |
| **ML-ready** | Needs transformation | ✅ Direct use |
| **Residual included** | ❌ No | ✅ Yes |
| **Feature decomposition** | ❌ Hard | ✅ Easy |

**Conclusion**: Term-based schema is SUPERIOR for ML applications.

---

**Status**: Ready for implementation
**Priority**: HIGH (foundation for Phase 2)
**Estimated Effort**: 2-3 days (schema + worker + validation)
**Next Step**: Update regression worker script with term-based calculations
