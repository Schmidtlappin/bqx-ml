# Feature Normalization Analysis for BQX ML

**Status:** ⚠️ PARTIALLY NORMALIZED - ACTION REQUIRED
**Date:** 2025-11-09

---

## Executive Summary

**Current State:** BQX features are **partially normalized**. Some features are normalized as percentages (returns, volatility), but many are stored as absolute values (rates, max, min, avg, stdev).

**Impact:** This creates **scale inconsistency** across currency pairs, which will degrade ML model performance.

**Recommendation:** Either normalize all features during preprocessing OR add pre-normalized versions to MVs.

---

## Current Normalization Status

### ✅ NORMALIZED Features (9 features per window)

These are already normalized as **percentage of current rate**:

| Feature | Formula | Normalization |
|---------|---------|---------------|
| `w{W}_bqx_return` | `Σ(rate(t-i) - rate(t)) / rate(t)` | ✅ Divided by rate(t) |
| `w{W}_bqx_endpoint` | `(rate(t-W) - rate(t)) / rate(t)` | ✅ Divided by rate(t) |
| `agg_bqx_return` | `Σ(rate(t-i) - rate(t)) / rate(t)` | ✅ Divided by rate(t) |
| `agg_bqx_range` | `(max - min) / rate(t)` | ✅ Divided by rate(t) |
| `agg_bqx_volatility` | `stdev / rate(t)` | ✅ Divided by rate(t) |

**Interpretation:** These are **dimensionless percentages** - comparable across all pairs.

Example:
- EURUSD `w75_bqx_return` = 0.0015 means 0.15% cumulative return
- USDJPY `w75_bqx_return` = 0.0015 means 0.15% cumulative return
- **Directly comparable!** ✅

---

### ❌ NOT NORMALIZED Features (28 features per window)

These are stored as **absolute values** in the pair's quote currency:

| Feature | Formula | Normalization |
|---------|---------|---------------|
| `rate` | Current exchange rate | ❌ Absolute value |
| `w{W}_bqx_max` | `max(rates in window)` | ❌ Absolute value |
| `w{W}_bqx_min` | `min(rates in window)` | ❌ Absolute value |
| `w{W}_bqx_avg` | `mean(rates in window)` | ❌ Absolute value |
| `w{W}_bqx_stdev` | `std(rates in window)` | ❌ Absolute value |
| `agg_bqx_max` | `max(rates in window)` | ❌ Absolute value |
| `agg_bqx_min` | `min(rates in window)` | ❌ Absolute value |
| `agg_bqx_avg` | `mean(rates in window)` | ❌ Absolute value |
| `agg_bqx_stdev` | `std(rates in window)` | ❌ Absolute value |

**Problem:** These values have **vastly different scales** across currency pairs.

---

## The Scale Problem

### Example: Cross-Pair Comparison

| Pair | Typical Rate | w75_bqx_max | w75_bqx_stdev |
|------|-------------|-------------|---------------|
| EURUSD | 1.10 | 1.102 | 0.0012 |
| USDJPY | 150.00 | 150.30 | 0.15 |
| GBPUSD | 1.27 | 1.272 | 0.0015 |

**Observation:** USDJPY values are **100-150x larger** than EURUSD/GBPUSD values!

### Impact on ML Models

#### 1. **Feature Importance Distortion**
```python
# Neural network weights initialization
# Model sees:
X = [
    [1.10, 1.102, 0.0012],  # EURUSD features
    [150.0, 150.3, 0.15],   # USDJPY features
]

# Without normalization, model will:
# - Give 100x more weight to USDJPY features
# - Underweight EURUSD features
# - Learn incorrect relationships
```

#### 2. **Gradient Explosion/Vanishing**
```python
# Loss function gradient with respect to unnormalized features
∂L/∂w_usdjpy ≈ 150 × (prediction_error)  # Large gradient
∂L/∂w_eurusd ≈ 1.1 × (prediction_error)  # Small gradient

# Result:
# - USDJPY weights update 100x faster
# - EURUSD weights barely update
# - Model fails to learn EURUSD patterns
```

#### 3. **Regularization Failure**
```python
# L2 regularization: λ Σ w²
# USDJPY features force larger weights
# Regularization penalizes USDJPY disproportionately
# Model underfits USDJPY, overfits EURUSD
```

#### 4. **Optimizer Inefficiency**
```python
# Adam/SGD learning rate must be:
# - Too small for USDJPY (slow convergence)
# - Too large for EURUSD (instability)
# No single learning rate works well
```

---

## Why Normalized Data is Best

### 1. **Scale Invariance** ✅

**Problem Without Normalization:**
```python
# EURUSD: 1.10 → 1.11 = 0.01 absolute change
# USDJPY: 150.0 → 151.0 = 1.0 absolute change
# Model treats 1.0 change as 100x more important!
```

**Solution With Normalization:**
```python
# EURUSD: 0.01 / 1.10 = 0.0091 = 0.91% change
# USDJPY: 1.0 / 150.0 = 0.0067 = 0.67% change
# Model correctly compares percentage changes
```

### 2. **Feature Comparability** ✅

**Without Normalization:**
```python
# Cannot compare features across pairs
eurusd_stdev = 0.0012  # What does this mean?
usdjpy_stdev = 0.15    # Is this more or less volatile?
# WRONG: Looks like USDJPY is 125x more volatile
```

**With Normalization:**
```python
# Percentage-based volatility
eurusd_volatility = 0.0012 / 1.10 = 0.0011 = 0.11%
usdjpy_volatility = 0.15 / 150.0 = 0.001 = 0.10%
# CORRECT: EURUSD is actually 10% more volatile
```

### 3. **Model Convergence** ✅

**Without Normalization:**
- Gradient descent takes **10-100x more iterations**
- Training loss oscillates
- Validation loss diverges

**With Normalization:**
- **Faster convergence** (3-10x speedup)
- Stable training
- Better generalization

### 4. **Transfer Learning** ✅

**Without Normalization:**
- Model trained on EURUSD cannot predict USDJPY
- Must retrain from scratch for each pair
- No knowledge transfer

**With Normalization:**
- Model learns percentage-based patterns
- Transfers to new pairs
- Can fine-tune instead of full retrain

### 5. **Interpretability** ✅

**Without Normalization:**
```python
feature_importance = [0.001, 0.15, 0.002]
# What do these numbers mean?
```

**With Normalization:**
```python
feature_importance = [0.35, 0.42, 0.23]
# Clear: Feature 2 (42%) is most important
```

---

## Normalization Strategies

### Strategy 1: Per-Pair Percentage Normalization (RECOMMENDED)

**Formula:** `normalized_value = (value - rate) / rate`

**Advantages:**
- ✅ **Interpretable:** Results are percentages
- ✅ **Scale-invariant:** Works across all pairs
- ✅ **Economically meaningful:** Traders think in percentages
- ✅ **No training data leakage:** Uses current rate only

**Example:**
```python
# EURUSD
rate = 1.10
w75_max = 1.102
w75_max_pct = (1.102 - 1.10) / 1.10 = 0.0018 = 0.18%

# USDJPY
rate = 150.0
w75_max = 150.3
w75_max_pct = (150.3 - 150.0) / 150.0 = 0.002 = 0.20%

# Now comparable!
```

### Strategy 2: Z-Score Normalization

**Formula:** `z = (x - μ) / σ`

**Advantages:**
- ✅ Zero mean, unit variance
- ✅ Works well with many ML algorithms

**Disadvantages:**
- ❌ Requires computing μ and σ from training data
- ❌ Risk of data leakage if not careful
- ❌ Less interpretable

### Strategy 3: Min-Max Normalization

**Formula:** `x_norm = (x - min) / (max - min)`

**Advantages:**
- ✅ Scales to [0, 1] range
- ✅ Easy to implement

**Disadvantages:**
- ❌ Sensitive to outliers
- ❌ Requires knowing min/max from training data
- ❌ Not interpretable

---

## Recommendation

### Option A: Add Normalized Features to MVs (BEST)

Add percentage-normalized versions of all absolute-value features:

```python
# Additional fields to add:
w{W}_bqx_max_pct = (w{W}_bqx_max - rate) / rate
w{W}_bqx_min_pct = (w{W}_bqx_min - rate) / rate
w{W}_bqx_avg_pct = (w{W}_bqx_avg - rate) / rate
w{W}_bqx_stdev_pct = w{W}_bqx_stdev / rate
agg_bqx_max_pct = (agg_bqx_max - rate) / rate
agg_bqx_min_pct = (agg_bqx_min - rate) / rate
agg_bqx_avg_pct = (agg_bqx_avg - rate) / rate
agg_bqx_stdev_pct = agg_bqx_stdev / rate
```

**Advantages:**
- ✅ Normalization done once in database
- ✅ No preprocessing needed in training code
- ✅ Consistent across all uses
- ✅ Faster training (pre-computed)

**Disadvantages:**
- ❌ More storage (2x features)
- ❌ Requires MV recreation

**New Field Count:** 482 + 40 = **522 fields per MV**

### Option B: Normalize During Preprocessing (ACCEPTABLE)

Keep MVs as-is, normalize in Python during feature extraction:

```python
import pandas as pd

# Load data
df = pd.read_parquet('features_eurusd.parquet')

# Normalize absolute features
for window in [15, 30, 45, 60, 75]:
    df[f'w{window}_bqx_max_pct'] = (df[f'w{window}_bqx_max'] - df['target_rate']) / df['target_rate']
    df[f'w{window}_bqx_min_pct'] = (df[f'w{window}_bqx_min'] - df['target_rate']) / df['target_rate']
    df[f'w{window}_bqx_avg_pct'] = (df[f'w{window}_bqx_avg'] - df['target_rate']) / df['target_rate']
    df[f'w{window}_bqx_stdev_pct'] = df[f'w{window}_bqx_stdev'] / df['target_rate']

# Similar for aggregate features
# Similar for all feature pairs
```

**Advantages:**
- ✅ No database changes needed
- ✅ Flexible (can try different normalizations)
- ✅ Less storage

**Disadvantages:**
- ❌ Must normalize every time data is loaded
- ❌ Slower training pipeline
- ❌ Risk of inconsistency across experiments

---

## Impact Analysis

### Current State (Unnormalized)
```python
# Feature matrix for EURUSD prediction
X_eurusd = [
    [1.10, 1.102, 0.0012],  # EURUSD absolute values
    [150.0, 150.3, 0.15],   # USDJPY absolute values (100x larger)
]

# Model learns:
# "USDJPY features are 100x more important" ❌ WRONG
```

### After Normalization
```python
# Feature matrix for EURUSD prediction
X_eurusd = [
    [0.0018, 0.0018, 0.0011],  # EURUSD percentages
    [0.0020, 0.0020, 0.0010],  # USDJPY percentages (similar scale)
]

# Model learns:
# "Both features equally important, let me learn their relationships" ✅ CORRECT
```

---

## Decision Matrix

| Approach | Storage | Performance | Flexibility | Consistency | Recommendation |
|----------|---------|-------------|-------------|-------------|----------------|
| **Option A: Add to MVs** | +40 GB | Fast | Low | High | ⭐⭐⭐⭐⭐ BEST |
| **Option B: Preprocess** | Unchanged | Slower | High | Medium | ⭐⭐⭐ OK |

---

## Next Steps

### Immediate Action Required

1. **Decide on normalization strategy** (A or B)
2. If Option A:
   - Modify `create_filtered_feature_mvs.py` to add `_pct` fields
   - Recreate MVs with normalized features
3. If Option B:
   - Document normalization in preprocessing pipeline
   - Add normalization function to training code

### Verification

```python
# After normalization, verify:
import pandas as pd

# Load features for multiple pairs
eurusd = pd.read_parquet('features_eurusd.parquet')
usdjpy = pd.read_parquet('features_usdjpy.parquet')

# Check that percentage features have similar scales
print(eurusd['target_w75_bqx_max_pct'].describe())
print(usdjpy['target_w75_bqx_max_pct'].describe())

# Should see similar ranges (e.g., -0.05 to +0.05)
# Not 1.0 vs 150.0!
```

---

## Summary

**Question:** Are all features normalized as a percentage of pair value?

**Answer:** ⚠️ **PARTIALLY**
- ✅ Returns and volatility: Normalized
- ❌ Rates, max, min, avg, stdev: NOT normalized

**Recommendation:** Add percentage-normalized versions of absolute-value features to MVs.

**Rationale:**
1. **Scale invariance:** Makes features comparable across pairs
2. **Model performance:** Prevents feature importance distortion
3. **Training efficiency:** Faster convergence, stable gradients
4. **Interpretability:** Percentages are economically meaningful
5. **Transfer learning:** Enables cross-pair generalization

**Action:** Implement Option A (add `_pct` fields to MVs) for optimal ML performance.

---

**Date:** 2025-11-09
**Status:** Analysis complete, awaiting decision
**Recommendation:** Option A (add normalized features to MVs)
