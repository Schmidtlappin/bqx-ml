# BQX vs FWD Tables - Side-by-Side Comparison

**Date**: 2025-11-08

---

## Core Formula Comparison

### FWD (Forward-Looking) - EXISTING

```
w{W}_fwd_return = Σ(i=1 to W)[rate(t) - rate(t+i)] / rate(t)
                              ↑           ↑
                           CURRENT    FUTURE
```

**Direction**: Current → Future
**Data Required**: Needs future W minutes of data
**Use Case**: ML prediction targets (what will happen)

---

### BQX (Backward-Looking) - PROPOSED

```
w{W}_bqx_return = Σ(i=1 to W)[rate(t-i) - rate(t)] / rate(t)
                              ↑           ↑
                            PAST      CURRENT
```

**Direction**: Past → Current
**Data Required**: Needs past W minutes of data
**Use Case**: ML features (what just happened)

---

## Concrete Example (w60 Window)

### Scenario
```
Time    | Rate
--------|-------
t-60    | 1.0870  ← 60 min ago
t-59    | 1.0871
t-58    | 1.0872
  ...   |  ...
t-2     | 1.0878
t-1     | 1.0879
t+0     | 1.0880  ← CURRENT (now)
t+1     | 1.0879
t+2     | 1.0878
  ...   |  ...
t+59    | 1.0871
t+60    | 1.0870  ← 60 min ahead
```

### FWD Calculation (t+0)

```
w60_fwd_return = [(1.0880 - 1.0879) + (1.0880 - 1.0878) + ... + (1.0880 - 1.0870)] / 1.0880
                = [0.0001 + 0.0002 + ... + 0.0010] / 1.0880
                = 0.0300 / 1.0880
                = 0.0276 (2.76%)
```

**Interpretation**: Price will decline by 2.76% cumulatively over next 60 minutes

---

### BQX Calculation (t+0)

```
w60_bqx_return = [(1.0870 - 1.0880) + (1.0871 - 1.0880) + ... + (1.0879 - 1.0880)] / 1.0880
                = [-0.0010 + -0.0009 + ... + -0.0001] / 1.0880
                = -0.0300 / 1.0880
                = -0.0276 (-2.76%)
```

**Interpretation**: Price has increased by 2.76% cumulatively over past 60 minutes

---

## Window Size Comparison

| | FWD Windows | BQX Windows |
|---|-------------|-------------|
| **Count** | 6 | 5 |
| **Sizes** | 60, 90, 150, 240, 390, 630 min | 15, 30, 45, 60, 75 min |
| **Range** | 1h to 10.5h | 15min to 75min |
| **Granularity** | Variable (30-240 min gaps) | Uniform (15 min increments) |
| **Focus** | Medium to long-term | Ultra-short to short-term |
| **Overlap** | w60 matches | w60 matches |

**Rationale for BQX's Shorter Windows**:
- Recent momentum (last 15-75 min) is highly predictive
- Finer granularity captures micro-patterns
- Complements REG's medium-term windows (60-630 min)

---

## Field Structure Comparison

### FWD Table (46 fields total)

**Core** (3):
- ts_utc, rate, created_at

**Per Window** (6 × 6 = 36):
- w{W}_fwd_return
- w{W}_fwd_max
- w{W}_fwd_min
- w{W}_fwd_avg
- w{W}_fwd_stdev
- w{W}_fwd_endpoint

**Aggregates** (7):
- agg_fwd_return, max, min, avg, stdev, range, volatility

---

### BQX Table (40 fields total)

**Core** (3):
- ts_utc, rate, created_at

**Per Window** (5 × 6 = 30):
- w{W}_bqx_return
- w{W}_bqx_max
- w{W}_bqx_min
- w{W}_bqx_avg
- w{W}_bqx_stdev
- w{W}_bqx_endpoint

**Aggregates** (7):
- agg_bqx_return, max, min, avg, stdev, range, volatility

---

## Sign Convention

### Both Use Same Convention ✅

| Scenario | FWD Return | BQX Return |
|----------|------------|------------|
| Price declining | **Positive** | **Positive** |
| Price increasing | **Negative** | **Negative** |
| Stable price | ~0 | ~0 |

**Formula Pattern**: (higher_rate - lower_rate) / current_rate

---

## Edge Effects (NULL Values)

### FWD - NULLs at END of Data

```
Timeline:
[------- Data Available -------][XX No Future Data XX]
                                 ↑
                              Last 630 min
                              have NULL w630
```

**Reason**: Cannot compute forward metrics without future data

---

### BQX - NULLs at START of Data

```
Timeline:
[XX No Past Data XX][------- Data Available -------]
 ↑
First 75 min
have NULL w75
```

**Reason**: Cannot compute backward metrics without past data

---

## Time-Lagged Symmetry

### The Beautiful Relationship

```
At time t:
  BQX w60 = cumulative change from (t-60) to t
  FWD w60 = cumulative change from t to (t+60)

At time (t+60):
  BQX w60 = cumulative change from t to (t+60)  ← Same period as FWD above!
```

**This means**:
```python
# Today's forward return predicts tomorrow's backward return
fwd['w60_fwd_return'][t] ≈ bqx['w60_bqx_return'][t+60]

# Can validate predictions!
correlation = np.corrcoef(
    fwd['w60_fwd_return'][:-60],
    bqx['w60_bqx_return'][60:]
)
```

---

## Use Case Comparison

| Aspect | FWD | BQX |
|--------|-----|-----|
| **ML Role** | Targets (Y) | Features (X) |
| **Prediction** | What to predict | What to use for prediction |
| **Real-Time** | ❌ Not computable (needs future) | ✅ Computable (uses past) |
| **Training** | Labels for supervised learning | Recent momentum features |
| **Trading** | Profit/loss targets | Entry signal indicators |
| **Validation** | Model output | Model input + time-lagged validation |

---

## Combined Feature Architecture

### Current State (Without BQX)

```
Backward-Looking Features:
├─ REG (75 fields): Complex quadratic regression
│   └─ Windows: 60, 90, 150, 240, 390, 630 min
│
Forward-Looking Targets:
└─ FWD (46 fields): Prediction targets
    └─ Windows: 60, 90, 150, 240, 390, 630 min
```

**Gap**: No simple recent momentum features (< 60 min)

---

### Proposed State (With BQX)

```
Backward-Looking Features:
├─ REG (75 fields): Complex patterns
│   └─ Windows: 60, 90, 150, 240, 390, 630 min
│
├─ BQX (40 fields): Simple momentum  ← NEW!
│   └─ Windows: 15, 30, 45, 60, 75 min
│
Forward-Looking Targets:
└─ FWD (46 fields): Prediction targets
    └─ Windows: 60, 90, 150, 240, 390, 630 min
```

**Filled Gap**: Ultra-short-term simple momentum (15-75 min)

---

## Feature Complementarity

### REG vs BQX (Both Backward-Looking)

| Aspect | REG | BQX |
|--------|-----|-----|
| **Pattern Type** | Non-linear (quadratic curves) | Linear (cumulative sums) |
| **Complexity** | High (12 fields/window) | Low (6 fields/window) |
| **Interpretability** | Low (coefficients) | High (simple returns) |
| **Computation** | Expensive (matrix ops) | Cheap (sums) |
| **Best For** | Trend reversals, acceleration | Momentum, breakouts |
| **Overfitting Risk** | Higher | Lower |

**Together**: Complete picture
- REG: "Is price accelerating/decelerating?"
- BQX: "How much has price moved recently?"

---

## ML Model Example

### Feature Set Construction

```python
# Combine BQX + REG for comprehensive features
X_backward = pd.concat([
    # Ultra-short-term momentum (BQX)
    bqx[['w15_bqx_return', 'w30_bqx_return', 'w45_bqx_return',
         'w60_bqx_return', 'w75_bqx_return']],

    # Short-term volatility (BQX)
    bqx[['w15_bqx_stdev', 'w60_bqx_stdev']],

    # Medium-term patterns (REG)
    reg[['w60_quad_norm', 'w60_lin_norm', 'w60_r2',
         'w240_quad_norm', 'w240_r2']],
], axis=1)

# Use FWD as targets
Y_forward = fwd[['w60_fwd_return', 'w240_fwd_return']]

# Train
model.fit(X_backward, Y_forward)
```

---

## Storage Impact

### Per Table Storage Estimate

```
Fields: 40 per row
Time range: 50 months × 30 days × 1440 min/day = 2,160,000 rows
Row size: ~320 bytes (40 doubles @ 8 bytes)
Per table: 2,160,000 × 320 = ~690 MB

28 pairs: 690 MB × 28 = ~19.3 GB
```

**Total BQX Storage**: ~20 GB (< 1% of current 2.478 TB)

**Acceptable**: Yes ✅

---

## Implementation Effort

### Code Reuse from FWD

| Component | FWD | BQX | Reuse % |
|-----------|-----|-----|---------|
| Table DDL | ✅ | Adapt | 90% |
| Partition creation | ✅ | Same | 100% |
| Worker loop structure | ✅ | Same | 100% |
| Formula direction | → | ← | 80% (just reverse) |
| Window configuration | 6 windows | 5 windows | 90% |
| Batch insert logic | ✅ | Same | 100% |

**Overall Code Reuse**: ~92%

**Estimated Development Time**: 16 hours (2 days)

---

## Recommendation Summary

### ✅ **APPROVE BQX TABLE CREATION**

**Key Benefits**:
1. **Fills critical gap**: Ultra-short-term momentum (15-75 min)
2. **Symmetric design**: Mirrors FWD elegantly
3. **Low complexity**: Simple formulas, easy to interpret
4. **Real-time ready**: Only uses past data
5. **ML value**: +40 features for model training
6. **Minimal cost**: ~20 GB storage, 2 days development

**Risks**: Minimal
- Low storage impact (<1%)
- Reuses proven FWD architecture
- No breaking changes to existing tables

**Priority**: HIGH

---

## Next Steps

1. ✅ User approval of BQX design
2. Generate SQL DDL for 28 bqx tables
3. Create backward_worker.py (mirror forward_worker.py)
4. Test on single pair (eurusd)
5. Backfill historical data (parallel)
6. Update materialized views with BQX features
7. Document formulas and usage

---

**Analysis Complete**: BQX tables are a strategic enhancement that completes the feature architecture with minimal implementation cost.
