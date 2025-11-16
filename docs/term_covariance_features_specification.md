# Term Covariance Features - Complete Specification
**Date:** 2025-11-15
**Purpose:** Variance decomposition of regression components for enhanced BQX prediction

---

## Executive Summary

**Feature Type**: Rolling covariances/correlations between regression term components

**Where Calculated**: correlation_features_worker_v5.py (new Stage 2.X)

**Where Stored**: correlation_bqx_{pair} tables (6 new features)

**ML Value**: Detects trend exhaustion, breakouts, and regime changes

---

## Mathematical Foundation

### Regression Term Decomposition

For any timestamp t with window w:
```
ŷ(t) = quadratic_term(t) + linear_term(t) + constant_term(t)
residual(t) = y_actual(t) - ŷ(t)
```

### Three Key Covariances (Rolling 60-minute window)

**1. Quadratic-Linear Covariance**
```
cov(quad, lin) = E[(quad - μ_quad)(lin - μ_lin)]
```
**Meaning**: How curvature and trend move together
- **Positive**: Trend and curvature aligned (momentum building)
- **Negative**: Trend opposed by curvature (trend exhaustion)
- **Zero**: Independent (linear trend, no curve)

**2. Residual-Quadratic Covariance**
```
cov(resid, quad) = E[(resid - μ_resid)(quad - μ_quad)]
```
**Meaning**: Do errors correlate with curvature?
- **Positive**: Model underestimates when curvature increases
- **Negative**: Model overestimates when curvature increases  
- **High magnitude**: Quadratic term insufficient (regime change)

**3. Residual-Linear Covariance**
```
cov(resid, lin) = E[(resid - μ_resid)(lin - μ_lin)]
```
**Meaning**: Do errors correlate with trend?
- **Positive**: Model underestimates during uptrends (breakout)
- **Negative**: Model overestimates during uptrends (exhaustion)
- **High magnitude**: Linear trend stronger than model expects

---

## Dual-Domain Implementation

### Rate Domain (rate_index)
```python
# From reg_rate_{pair} table
quadratic_term_idx_w15  # Curvature in rate trajectory
linear_term_idx_w15     # Linear price trend
residual_idx_w15        # Price model error

# Calculate covariances
cov_quad_lin_idx_60min = rolling_cov(
    quadratic_term_idx_w15, 
    linear_term_idx_w15, 
    window=60
)
```

### BQX Domain (momentum)
```python
# From reg_bqx_{pair} table  
quadratic_term_bqx_w15  # Momentum curvature
linear_term_bqx_w15     # Linear momentum trend
residual_bqx_w15        # Momentum model error

# Calculate covariances
cov_quad_lin_bqx_60min = rolling_cov(
    quadratic_term_bqx_w15,
    linear_term_bqx_w15,
    window=60
)
```

---

## Predictive Scenarios

### Scenario 1: Trend Exhaustion Signal

**Market State**:
```
t=1000: linear_term_bqx = +0.15 (strong uptrend)
        quadratic_term_bqx = -0.12 (negative curvature)
        cov(quad, lin)_60min = -0.85 (highly negative!)
```

**Interpretation**:
- Over past 60 minutes, whenever trend strengthens, curvature becomes more negative
- This is classic momentum exhaustion pattern
- **Prediction**: BQX will reverse in next 15-30 minutes

**ML Feature Importance**: HIGH for trend reversal prediction

### Scenario 2: Breakout Detection

**Market State**:
```
t=1500: linear_term_bqx = +0.18 (very strong trend)
        residual_bqx = +0.08 (large positive error)
        cov(resid, lin)_60min = +0.92 (highly positive!)
```

**Interpretation**:
- Model consistently underestimates during strong trends
- Actual momentum exceeds parabolic model expectations
- **Prediction**: Trend continuation (breakout in progress)

**ML Feature Importance**: HIGH for breakout/continuation prediction

### Scenario 3: Regime Change

**Market State**:
```
t=2000: quadratic_term_bqx = -0.20 (extreme curvature)
        residual_bqx = +0.15 (very large error)
        cov(resid, quad)_60min = +0.88 (high positive!)
```

**Interpretation**:
- Parabolic model breaking down
- Market entered new regime (volatile, non-parabolic)
- **Prediction**: High uncertainty, reduce position size

**ML Feature Importance**: HIGH for regime detection and risk management

---

## Feature Schema

### Updated correlation_bqx_{pair} Table

```sql
CREATE TABLE bqx.correlation_bqx_{pair} (
    ts_utc TIMESTAMPTZ NOT NULL,
    
    -- Existing cross-pair correlations (45 features)
    corr_base_pairs_15min DOUBLE PRECISION,
    corr_quote_pairs_15min DOUBLE PRECISION,
    -- ... (43 more existing features)
    
    -- NEW: Term interaction covariances (6 features)
    cov_quad_lin_bqx_60min DOUBLE PRECISION,      -- Trend-curvature interaction
    cov_resid_quad_bqx_60min DOUBLE PRECISION,    -- Error-curvature relationship
    cov_resid_lin_bqx_60min DOUBLE PRECISION,     -- Error-trend relationship
    
    -- NEW: Normalized correlations (6 features)
    corr_quad_lin_bqx_60min DOUBLE PRECISION,     -- Normalized [-1, 1]
    corr_resid_quad_bqx_60min DOUBLE PRECISION,
    corr_resid_lin_bqx_60min DOUBLE PRECISION,
    
    PRIMARY KEY (ts_utc)
);
```

**Total Features**: 45 (existing) + 6 (new) = **51 features per partition**

---

## Implementation

### Worker Function

```python
def calculate_term_covariances(df, window_size=60):
    """
    Calculate rolling covariances between regression term components.
    
    Args:
        df: DataFrame with columns:
            - quadratic_term_bqx_w15
            - linear_term_bqx_w15
            - residual_bqx_w15
        window_size: Rolling window in minutes (default 60)
        
    Returns:
        dict: 6 covariance/correlation features at current timestamp
    """
    try:
        # Ensure we have enough data
        if len(df) < window_size:
            return {k: None for k in [
                'cov_quad_lin_bqx_60min', 'cov_resid_quad_bqx_60min',
                'cov_resid_lin_bqx_60min', 'corr_quad_lin_bqx_60min',
                'corr_resid_quad_bqx_60min', 'corr_resid_lin_bqx_60min'
            ]}
        
        # Get last window_size rows
        window_df = df.tail(window_size)
        
        # Calculate covariances
        cov_quad_lin = window_df['quadratic_term_bqx_w15'].cov(
            window_df['linear_term_bqx_w15']
        )
        
        cov_resid_quad = window_df['residual_bqx_w15'].cov(
            window_df['quadratic_term_bqx_w15']
        )
        
        cov_resid_lin = window_df['residual_bqx_w15'].cov(
            window_df['linear_term_bqx_w15']
        )
        
        # Calculate correlations (normalized covariances)
        corr_quad_lin = window_df['quadratic_term_bqx_w15'].corr(
            window_df['linear_term_bqx_w15']
        )
        
        corr_resid_quad = window_df['residual_bqx_w15'].corr(
            window_df['quadratic_term_bqx_w15']
        )
        
        corr_resid_lin = window_df['residual_bqx_w15'].corr(
            window_df['linear_term_bqx_w15']
        )
        
        return {
            'cov_quad_lin_bqx_60min': float(cov_quad_lin) if not pd.isna(cov_quad_lin) else None,
            'cov_resid_quad_bqx_60min': float(cov_resid_quad) if not pd.isna(cov_resid_quad) else None,
            'cov_resid_lin_bqx_60min': float(cov_resid_lin) if not pd.isna(cov_resid_lin) else None,
            'corr_quad_lin_bqx_60min': float(corr_quad_lin) if not pd.isna(corr_quad_lin) else None,
            'corr_resid_quad_bqx_60min': float(corr_resid_quad) if not pd.isna(corr_resid_quad) else None,
            'corr_resid_lin_bqx_60min': float(corr_resid_lin) if not pd.isna(corr_resid_lin) else None
        }
        
    except Exception as e:
        logger.warning(f"Term covariance calculation failed: {e}")
        return {k: None for k in [
            'cov_quad_lin_bqx_60min', 'cov_resid_quad_bqx_60min',
            'cov_resid_lin_bqx_60min', 'corr_quad_lin_bqx_60min',
            'corr_resid_quad_bqx_60min', 'corr_resid_lin_bqx_60min'
        ]}
```

### Integration into Correlation Worker

```python
# In correlation_features_worker_v5.py (updated version)

def populate_correlation_for_pair(pair, year_month):
    """Populate correlation features including term covariances."""
    
    # ... existing code to load data ...
    
    # Load regression terms from reg_bqx table
    reg_bqx_query = f"""
    SELECT ts_utc, 
           quadratic_term_bqx_w15,
           linear_term_bqx_w15,
           constant_term_bqx_w15,
           residual_bqx_w15
    FROM bqx.reg_bqx_{pair}_{year_month}
    ORDER BY ts_utc;
    """
    
    df_reg = pd.read_sql(reg_bqx_query, conn)
    df = pd.merge(df, df_reg, on='ts_utc', how='inner')
    
    # Calculate term covariances for each timestamp
    results = []
    for i in range(len(df)):
        # Calculate existing 45 correlation features
        existing_features = calculate_cross_pair_correlations(...)
        
        # Calculate new 6 term covariance features
        term_cov_features = calculate_term_covariances(
            df.iloc[:i+1],  # All data up to current timestamp
            window_size=60
        )
        
        # Combine all features
        row_features = {**existing_features, **term_cov_features}
        results.append(row_features)
    
    # Insert into correlation_bqx table
    # ...
```

---

## ML Feature Engineering

### Primary Features

```python
# Most predictive term covariance features
features = [
    'corr_quad_lin_bqx_60min',     # Trend exhaustion detector
    'corr_resid_quad_bqx_60min',   # Regime change detector
    'corr_resid_lin_bqx_60min',    # Breakout detector
]
```

### Derived Features

```python
# Momentum quality score
df['momentum_quality'] = 1.0 / (abs(df['cov_resid_lin_bqx_60min']) + 0.01)

# Trend exhaustion indicator
df['trend_exhaustion'] = (df['corr_quad_lin_bqx_60min'] < -0.7).astype(int)

# Breakout probability
df['breakout_prob'] = (df['corr_resid_lin_bqx_60min'] > 0.8).astype(float)

# Regime stability
df['regime_stable'] = (abs(df['corr_resid_quad_bqx_60min']) < 0.3).astype(int)
```

### Cross-Domain Comparison

```python
# Compare rate domain vs BQX domain covariances
df['domain_alignment'] = (
    df['corr_quad_lin_idx_60min'] * 
    df['corr_quad_lin_bqx_60min']
)

# When positive: Both domains agree (strong signal)
# When negative: Domains disagree (uncertainty)
```

---

## Expected Feature Importance Rankings

Based on BQX ML prediction task (predict w60_bqx_return at t+60):

| Rank | Feature | Importance | Use Case |
|------|---------|------------|----------|
| 1 | corr_resid_lin_bqx_60min | Very High | Breakout detection |
| 2 | corr_quad_lin_bqx_60min | Very High | Trend exhaustion |
| 3 | corr_resid_quad_bqx_60min | High | Regime change |
| 4 | cov_resid_lin_bqx_60min | Medium | Momentum magnitude |
| 5 | cov_quad_lin_bqx_60min | Medium | Acceleration |
| 6 | cov_resid_quad_bqx_60min | Medium | Model quality |

---

## Summary

### Answer to User Questions

**1. Will terms be calculated for both BQX and rate_index?**
✅ YES - Both domains (reg_rate_* and reg_bqx_* tables)

**2. What to call var(quadratic_term, linear_term)?**
**Answer**: `cov_quad_lin` (covariance) or `corr_quad_lin` (correlation)

**3. Why valuable for BQX prediction?**
- Detects trend exhaustion (momentum reversals)
- Identifies breakouts (continuation signals)
- Signals regime changes (model breakdown)

**4. Calculate as features or during correlation?**
**Answer**: Calculate during **correlation phase** (Stage 2.X)
- Store in correlation_bqx_{pair} tables
- Rolling window calculation (60 minutes)
- 6 new features per partition

---

**Status**: Specification complete, ready for implementation
**Priority**: HIGH (enhances predictive power significantly)
**Implementation**: Add to correlation_features_worker_v5.py
**Storage**: correlation_bqx_{pair} tables (45 → 51 features)
