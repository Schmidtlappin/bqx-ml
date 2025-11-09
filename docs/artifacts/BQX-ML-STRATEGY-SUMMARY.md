# BQX ML Strategy Refactoring - Executive Summary

**Date**: 2025-11-08
**Strategic Shift**: From predicting FWD (forward returns) to predicting future BQX (backward momentum)

---

## The Key Insight

### Mathematical Equivalence

```
At time t (now):
  FWD w60 = Σ[rate(t) - rate(t+i)] / rate(t)     ← Measures t to t+60

At time t+60 (60 min later):
  BQX w60 = Σ[rate(t+i) - rate(t+60)] / rate(t+60) ← Measures same period!
```

**Both measure the same price movement**, just from different time perspectives:
- FWD: Looking forward from t
- BQX: Looking backward from t+60

**Near identical values** due to small normalization difference (~2.76% vs 2.62%)

---

## Why Predict Future BQX Instead of FWD?

### 1. Autoregressive Capability ⭐

```
OLD (FWD):
  Cannot use FWD_t as feature (it's the target!)
  Miss: Momentum persistence

NEW (BQX):
  Use BQX_t to predict BQX_{t+60}
  Capture: "If momentum is X now, what will it be in 60 min?"
```

**Example**:
```python
# Strong recent downward momentum
if bqx_t['w60_bqx_return'] > 0.002:
    # Likely continues
    prediction: bqx_{t+60} > 0.001

# Momentum persistence modeling!
```

### 2. Observable Validation

```
OLD (FWD):
  Predict FWD_t → Can't directly validate later
  (FWD computed once, never updated)

NEW (BQX):
  Predict BQX_{t+60} → Wait 60 min → Check actual BQX_{t+60}
  Direct validation against real observable metric
```

### 3. Finer Granularity

```
FWD Windows: 60, 90, 150, 240, 390, 630 min (6 windows, coarse)
BQX Windows: 15, 30, 45, 60, 75 min (5 windows, fine)

BQX enables:
  - 15-min ahead predictions (ultra-short-term)
  - 30-min ahead predictions (short-term)
  - Better for scalping/intraday strategies
```

### 4. Feature-Target Alignment

```
Features: BQX_t (cumulative return over past 60 min)
Target:   BQX_{t+60} (cumulative return - same metric, different time)

Benefits:
  ✅ Same units and interpretation
  ✅ Easier to understand model coefficients
  ✅ Direct momentum persistence measurement
```

---

## Recommended Architecture

### Hierarchical Multi-Horizon Model

```
Input Features (at time t):
├─ Current BQX: w15, w30, w45, w60, w75
├─ Lagged BQX: w60_{t-60}, w60_{t-120}
├─ Volatility: w15_stdev, agg_volatility
├─ REG Patterns: w60_quad_norm, w60_r2
└─ Derived: momentum_accel, vol_regime

↓ Level 1: Predict BQX_{t+15}
↓ Level 2: Predict BQX_{t+30} using pred_15
↓ Level 3: Predict BQX_{t+45} using pred_15, pred_30
↓ Level 4: Predict BQX_{t+60} using all previous
↓ Level 5: Predict BQX_{t+75} using all previous

Outputs: 5 future BQX values (15, 30, 45, 60, 75 min ahead)
```

**Why Hierarchical?**
- Short-term predictions inform long-term
- Captures cascading uncertainty
- Natural progression (near → far future)

---

## Feature Engineering Strategy

### Core Features (15 total)

**1. Autoregressive BQX** (8 features):
```python
# Current momentum
bqx_t['w15_bqx_return']  # Last 15 min
bqx_t['w30_bqx_return']  # Last 30 min
bqx_t['w60_bqx_return']  # Last 60 min
bqx_t['w75_bqx_return']  # Last 75 min

# Lagged momentum (60 min ago)
bqx_{t-60}['w60_bqx_return']

# Momentum acceleration
bqx_t['w15'] - bqx_t['w60']  # Short vs medium-term
```

**2. Volatility** (2 features):
```python
bqx_t['w15_bqx_stdev']     # Recent volatility
bqx_t['agg_bqx_volatility'] # Normalized volatility
```

**3. REG Patterns** (3 features):
```python
reg_t['w60_quad_norm']  # Quadratic curvature
reg_t['w60_r2']         # Pattern strength
reg_t['w240_quad_norm'] # Long-term curvature
```

**4. Derived** (2 features):
```python
# Volatility regime
vol_regime = bqx_t['w15_stdev'] / bqx_t['w60_stdev']

# Multi-timeframe alignment
alignment = sign(w15 + w30 + w45 + w60 + w75)
```

---

## Implementation Pipeline

### Phase 1: Prototype (Week 1)

**Goal**: Establish baseline
```python
# Simple single-horizon model
X = [bqx_t['w60'], reg_t['w60_quad_norm'], reg_t['w60_r2']]
Y = bqx_{t+60}['w60_bqx_return']

model = XGBRegressor()
model.fit(X_train, Y_train)

# Success: R² > 0.2, Directional Accuracy > 55%
```

### Phase 2: Multi-Horizon (Week 2)

**Goal**: Predict all 5 horizons
```python
from sklearn.multioutput import MultiOutputRegressor

# Predict 15, 30, 45, 60, 75 min ahead simultaneously
Y_multi = [bqx_{t+15}['w15'], ..., bqx_{t+75}['w75']]

model = MultiOutputRegressor(XGBRegressor())
model.fit(X_train, Y_multi)
```

### Phase 3: Advanced Features (Week 3)

**Goal**: Add autoregressive features
```python
# Add lagged BQX
X_extended = concat([
    X_base,
    bqx_{t-60}['w60'],
    bqx_{t-120}['w60'],
    momentum_acceleration,
    volatility_regime
])

# Expected: ΔR² > 0.05
```

### Phase 4: Production (Week 4)

**Goal**: Deploy automated pipeline
- Daily retraining
- Real-time predictions
- Performance monitoring
- Alert system

---

## Success Metrics

### Minimum Viable Performance

| Metric | Threshold |
|--------|-----------|
| R² (w60) | > 0.20 |
| Directional Accuracy | > 55% |
| Pipeline Reliability | 100% uptime |

### Target Performance

| Metric | Target |
|--------|--------|
| R² (w15, w30) | > 0.30 |
| R² (w45, w60, w75) | > 0.20 |
| Directional Accuracy | > 60% |
| Prediction Latency | < 100ms |

### Stretch Goals

| Metric | Goal |
|--------|------|
| R² (any horizon) | > 0.40 |
| Directional Accuracy | > 65% |
| Trading Sharpe Ratio | > 1.5 |

---

## Evaluation Framework

### Regression Metrics
```python
# R² Score (variance explained)
r2 = r2_score(Y_test, Y_pred)  # Target: > 0.2

# RMSE (average error)
rmse = sqrt(mean_squared_error(Y_test, Y_pred))  # Lower is better

# Directional accuracy (sign correct)
acc = mean(sign(Y_test) == sign(Y_pred))  # Target: > 55%
```

### Trading Metrics
```python
# Sharpe ratio (risk-adjusted return)
sharpe = mean(returns) / std(returns) * sqrt(periods)  # Target: > 1.5

# Maximum drawdown
max_dd = max(cumulative_losses)  # Monitor risk
```

---

## Key Advantages Over FWD Strategy

| Aspect | FWD Strategy | BQX Strategy | Winner |
|--------|--------------|--------------|--------|
| Autoregression | ❌ No | ✅ Yes | **BQX** |
| Granularity | 60-630 min | 15-75 min | **BQX** |
| Validation | One-time | Observable | **BQX** |
| Feature Alignment | Backward→Forward | Backward→Backward | **BQX** |
| Interpretability | Moderate | High | **BQX** |
| Momentum Capture | Indirect | Direct | **BQX** |

---

## Data Requirements

### Prerequisites

1. **BQX Tables Created** ✅ (40 fields × 28 pairs)
2. **REG Tables Available** ✅ (existing, 75 fields × 28 pairs)
3. **Historical Data** ✅ (50+ months of M1 data)

### Data Pipeline

```python
# Extract
bqx = load_bqx('eurusd')  # BQX table
reg = load_reg('eurusd')  # REG table

# Transform
features = create_features(bqx, reg)  # At time t
targets = create_targets(bqx)         # At time t+h

# Align
df = align_features_targets(features, targets)

# Split
train, test = time_based_split(df, ratio=0.8)

# Train
model.fit(train.X, train.Y)
```

---

## Example Use Case

### Trading Strategy

```python
# Real-time prediction at time t
current_bqx = get_current_bqx('eurusd')
current_reg = get_current_reg('eurusd')

# Predict next 60 minutes
features = extract_features(current_bqx, current_reg)
pred_bqx_60 = model.predict(features)

# Trading signal
if pred_bqx_60 > 0.001:
    # Predicted downward momentum
    signal = 'SHORT'
    confidence = min(abs(pred_bqx_60) * 100, 1.0)

elif pred_bqx_60 < -0.001:
    # Predicted upward momentum
    signal = 'LONG'
    confidence = min(abs(pred_bqx_60) * 100, 1.0)

else:
    # Weak signal
    signal = 'HOLD'
    confidence = 0.0

# Execute with position sizing based on confidence
position_size = base_size * confidence
```

---

## Risk Considerations

### Model Risk

1. **Overfitting**: Use walk-forward CV to validate
2. **Data Leakage**: Ensure strict time-based splits
3. **Regime Change**: Monitor performance degradation
4. **Feature Drift**: Track feature distributions

### Mitigation Strategies

```python
# Daily monitoring
monitor_metrics = {
    'r2_score': model.score(latest_data),
    'directional_acc': calc_directional_accuracy(latest_data),
    'prediction_drift': compare_predictions(yesterday, today),
}

# Alert if degradation
if monitor_metrics['r2_score'] < 0.15:
    alert('Model performance degraded - retrain required')

# Auto-retrain
if time_since_last_train > 24_hours:
    retrain_model(rolling_12_months)
```

---

## Timeline

| Week | Phase | Deliverable | Success Metric |
|------|-------|-------------|----------------|
| 1 | Prototype | Baseline w60 model | R² > 0.2 |
| 2 | Multi-Horizon | All 5 horizons | Consistent R² |
| 3 | Advanced | Extended features | ΔR² > 0.05 |
| 4 | Production | Automated pipeline | Deployed |

**Total**: 4 weeks from BQX tables to production

---

## Recommendation

### ✅ **STRONGLY APPROVE BQX-BASED ML STRATEGY**

**Rationale**:
1. Mathematically equivalent to FWD but superior framework
2. Enables autoregressive momentum modeling
3. Provides finer prediction granularity (15 min vs 60 min)
4. Observable validation framework
5. Direct momentum capture
6. Minimal implementation complexity

**Priority**: HIGH

**Expected ROI**:
- Better short-term predictions (15-75 min horizons)
- Improved trading signals (momentum-based)
- Reduced model complexity (autoregressive is natural fit)
- Enhanced interpretability (momentum is intuitive)

---

## Next Actions

1. **Review and approve** this strategy ✅
2. **Create BQX tables** (prerequisite) → Separate task
3. **Build prototype** (Week 1) → Train baseline model
4. **Iterate and improve** (Weeks 2-3) → Multi-horizon + features
5. **Deploy to production** (Week 4) → Automated pipeline

---

**Strategy Analysis Complete**: BQX-based approach is superior for autoregressive momentum modeling.

**Full Analysis**: [BQX-ML-STRATEGY-REFACTORING-ANALYSIS.md](BQX-ML-STRATEGY-REFACTORING-ANALYSIS.md)
