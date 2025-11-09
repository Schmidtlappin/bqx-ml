# BQX Table Request - Logic Analysis & Rationale

**Date**: 2025-11-08
**Request**: Create "bqx" tables mirroring "fwd" tables with backward-looking formulas and shorter windows

---

## Executive Summary

User requests creating **BQX (Backward Cumulative) tables** that provide a **symmetric counterpart** to FWD (Forward) tables. This creates a balanced feature architecture:

- **REG Tables**: Complex regression features (quadratic patterns)
- **BQX Tables** (NEW): Simple backward momentum features
- **FWD Tables**: Forward-looking prediction targets

**Key Innovation**: BQX fills the gap between complex regression and simple recent momentum.

---

## Request Breakdown

### What User Asked For

1. **Create "bqx" tables** for all 28 preferred forex pairs
2. **Mirror "fwd" table structure** but with two key deviations:

**Deviation 1 - Reversed Formula**:
```
FWD (Forward):  w{W}_fwd_return = Σ(i=1 to W)[rate(t) - rate(t+i)] / rate(t)
BQX (Backward): w{W}_bqx_return = Σ(i=1 to W)[rate(t-i) - rate(t)] / rate(t)
```

**Deviation 2 - Different Windows**:
```
FWD: 60, 90, 150, 240, 390, 630 minutes (1h to 10.5h)
BQX: 15, 30, 45, 60, 75 minutes (15min to 75min)
```

---

## Formula Analysis

### Forward Return Formula (FWD)

```
w{W}_fwd_return = Σ(i=1 to W)[rate(t) - rate(t+i)] / rate(t)
```

**What it calculates**:
- Sums: [current rate] - [each future rate]
- For each minute from t+1 to t+W
- Normalized by current rate

**Example** (w60):
```
t+0:  1.0880 (current)
t+1:  1.0879
t+2:  1.0878
...
t+60: 1.0870

Calculation:
= [(1.0880 - 1.0879) + (1.0880 - 1.0878) + ... + (1.0880 - 1.0870)] / 1.0880
= [0.0001 + 0.0002 + ... + 0.0010] / 1.0880
= 0.0300 / 1.0880
= 0.0276 (2.76% cumulative forward movement)
```

**Interpretation**:
- Positive: Price will decline (current > future)
- Negative: Price will increase (current < future)

---

### Backward Return Formula (BQX - Proposed)

```
w{W}_bqx_return = Σ(i=1 to W)[rate(t-i) - rate(t)] / rate(t)
```

**What it calculates**:
- Sums: [each past rate] - [current rate]
- For each minute from t-1 to t-W
- Normalized by current rate

**Example** (w60):
```
t-60: 1.0870
t-59: 1.0871
...
t-2:  1.0878
t-1:  1.0879
t+0:  1.0880 (current)

Calculation:
= [(1.0870 - 1.0880) + (1.0871 - 1.0880) + ... + (1.0879 - 1.0880)] / 1.0880
= [-0.0010 + -0.0009 + ... + -0.0001] / 1.0880
= -0.0300 / 1.0880
= -0.0276 (price increased 2.76% over past 60 min)
```

**Interpretation**:
- Positive: Price has declined (past > current)
- Negative: Price has increased (past < current)

---

## Mathematical Symmetry

### The Beautiful Symmetry

If we have continuous data and look at the same time point:

```
At time t:
  FWD w60_fwd_return = cumulative change from t to t+60 (future)
  BQX w60_bqx_return = cumulative change from t-60 to t (past)

At time t+60:
  BQX w60_bqx_return = cumulative change from t to t+60 (same period as FWD above!)
```

**This creates time-lagged symmetry**:
- FWD at time t predicts what BQX will show at time t+60
- If FWD is a good predictor, then: `FWD(t) ≈ BQX(t+60)`

### Sign Convention Comparison

| Scenario | FWD Sign | BQX Sign |
|----------|----------|----------|
| Price declining | Positive | Positive |
| Price increasing | Negative | Negative |

✅ **Same sign convention** - Both use (higher_price - lower_price) / current_rate

---

## Window Size Analysis

### FWD Windows (Long-term)

```
60  minutes =  1.0 hours  (short-term)
90  minutes =  1.5 hours
150 minutes =  2.5 hours
240 minutes =  4.0 hours  (session-level)
390 minutes =  6.5 hours
630 minutes = 10.5 hours  (long-term trends)
```

**Characteristics**:
- Wide range (1h to 10.5h)
- Variable granularity (gaps of 30, 60, 90, 150, 240 minutes)
- Focus: Medium to long-term predictions

### BQX Windows (Short-term)

```
15 minutes = 0.25 hours  (micro-trend)
30 minutes = 0.50 hours  (short-term)
45 minutes = 0.75 hours  (intraday)
60 minutes = 1.00 hours  (matches FWD w60!)
75 minutes = 1.25 hours  (extended short-term)
```

**Characteristics**:
- Narrow range (15min to 75min)
- Uniform granularity (15-minute increments)
- Focus: Recent momentum and micro-patterns

### Rationale for Shorter Windows

**1. Recent Information is Most Predictive**
- Last 15-75 minutes of price action often most relevant for near-term predictions
- Forex markets react quickly to news/events
- Short-term momentum has strong autocorrelation

**2. Finer Granularity Captures Micro-Patterns**
- 15-minute increments reveal subtle momentum shifts
- Can detect acceleration/deceleration of trends
- Better for high-frequency trading strategies

**3. Overlap with FWD at w60**
- Both have w60 window → Direct comparison possible
- Can validate: Does recent 60-min momentum predict next 60-min movement?
- Bridge between BQX and FWD timeframes

**4. Practical Trading Horizons**
- 15-75 minutes aligns with scalping and intraday strategies
- REG already covers medium-term (60-630 min)
- BQX fills the ultra-short-term gap

---

## Why Create BQX When We Have REG?

### Current Backward-Looking Features (REG)

REG tables contain **72 regression features** per timestamp:
- Quadratic coefficients (a, b, c)
- Regression terms (a_term, b_term)
- Statistical measures (R², RMSE, residuals)
- Normalized values (quad_norm, lin_norm, resid_norm)

**Complexity**: 12 fields × 6 windows = 72 features

**Use case**: Capture complex non-linear patterns

### Proposed Backward-Looking Features (BQX)

BQX tables would contain **30 simple features** per timestamp:
- Cumulative returns (bqx_return)
- Price statistics (max, min, avg, stdev)
- Endpoint returns (bqx_endpoint)

**Simplicity**: 6 fields × 5 windows = 30 features

**Use case**: Capture simple momentum and recent stats

### Comparison Table

| Aspect | REG | BQX |
|--------|-----|-----|
| **Complexity** | High (quadratic regression) | Low (simple sums) |
| **Interpretability** | Low (coefficients hard to interpret) | High (returns are intuitive) |
| **Computation** | Expensive (matrix operations) | Cheap (simple sums) |
| **Windows** | 60, 90, 150, 240, 390, 630 | 15, 30, 45, 60, 75 |
| **Focus** | Non-linear patterns | Linear momentum |
| **Real-time** | Slower to compute | Faster to compute |
| **Overfitting Risk** | Higher (many parameters) | Lower (few parameters) |

### Why Both Are Valuable

**REG captures**: "Is the price following a quadratic curve?"
- Good for: Detecting trend reversals, parabolic moves, acceleration

**BQX captures**: "How much has price moved recently?"
- Good for: Momentum signals, simple trends, breakout detection

**Together**: Complementary feature set
- REG: Complex patterns
- BQX: Simple patterns
- Model can learn which is more predictive in different market regimes

---

## Proposed BQX Table Structure

### Core Fields (3)

```sql
ts_utc     TIMESTAMPTZ NOT NULL  -- Timestamp
rate       DOUBLE PRECISION      -- Current exchange rate
created_at TIMESTAMPTZ           -- Record creation time
```

### Window Fields (5 windows × 6 metrics = 30 fields)

For each window W ∈ {15, 30, 45, 60, 75}:

```sql
w{W}_bqx_return    DOUBLE PRECISION  -- Cumulative backward return
w{W}_bqx_max       DOUBLE PRECISION  -- Max rate in past W minutes
w{W}_bqx_min       DOUBLE PRECISION  -- Min rate in past W minutes
w{W}_bqx_avg       DOUBLE PRECISION  -- Avg rate in past W minutes
w{W}_bqx_stdev     DOUBLE PRECISION  -- Stdev of past W minutes
w{W}_bqx_endpoint  DOUBLE PRECISION  -- Simple return (t-W to t)
```

### Aggregate Fields (7) - Using w75 as longest window

```sql
agg_bqx_return      DOUBLE PRECISION  -- w75 cumulative return
agg_bqx_max         DOUBLE PRECISION  -- w75 max
agg_bqx_min         DOUBLE PRECISION  -- w75 min
agg_bqx_avg         DOUBLE PRECISION  -- w75 avg
agg_bqx_stdev       DOUBLE PRECISION  -- w75 stdev
agg_bqx_range       DOUBLE PRECISION  -- (max - min) / rate(t)
agg_bqx_volatility  DOUBLE PRECISION  -- stdev / rate(t)
```

### Total Fields: 40

- Core: 3
- Windows: 5 × 6 = 30
- Aggregates: 7
- **Total**: 40 fields per row

### Partitioning

Monthly partitions (same as FWD):
```sql
CREATE TABLE bqx.bqx_eurusd (...)
PARTITION BY RANGE (ts_utc);

CREATE TABLE bqx.bqx_eurusd_2024m11
PARTITION OF bqx.bqx_eurusd
FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');
```

---

## BQX Calculation Formulas

### 1. Cumulative Backward Return (PRIMARY)

```
w{W}_bqx_return = Σ(i=1 to W)[rate(t-i) - rate(t)] / rate(t)
```

**Python**:
```python
rate_t = rates[i]  # Current rate at index i
past_rates = rates[i-W:i]  # rates from t-W to t-1 (W points)
cumulative_diffs = past_rates - rate_t
bqx_return = np.sum(cumulative_diffs) / rate_t
```

### 2. Endpoint Return

```
w{W}_bqx_endpoint = [rate(t-W) - rate(t)] / rate(t)
```

**Python**:
```python
bqx_endpoint = (past_rates[0] - rate_t) / rate_t
```

### 3. Statistical Measures

```
w{W}_bqx_max    = max(rate(t-W), ..., rate(t-1))
w{W}_bqx_min    = min(rate(t-W), ..., rate(t-1))
w{W}_bqx_avg    = mean(rate(t-W), ..., rate(t-1))
w{W}_bqx_stdev  = stdev(rate(t-W), ..., rate(t-1))
```

**Python**:
```python
bqx_max = np.max(past_rates)
bqx_min = np.min(past_rates)
bqx_avg = np.mean(past_rates)
bqx_stdev = np.std(past_rates, ddof=1)
```

### 4. Aggregate Metrics (w75 window)

```
agg_bqx_return     = w75_bqx_return
agg_bqx_max        = w75_bqx_max
agg_bqx_min        = w75_bqx_min
agg_bqx_avg        = w75_bqx_avg
agg_bqx_stdev      = w75_bqx_stdev
agg_bqx_range      = (agg_bqx_max - agg_bqx_min) / rate(t)
agg_bqx_volatility = agg_bqx_stdev / rate(t)
```

---

## Edge Effects and NULL Values

### When BQX Values Are NULL

BQX requires **past data** to calculate:

```
For w75 window at timestamp t:
- Need rates from t-75 to t-1 (75 past points)
- If insufficient past data → NULL
```

**Edge Cases**:
- First 15 minutes of data: w15 is NULL
- First 75 minutes of data: w75 is NULL
- Beginning of each partition: May have NULLs

**Different from FWD**:
- FWD has NULLs at the END of data (no future)
- BQX has NULLs at the START of data (no past)

---

## Use Cases

### 1. ML Feature Engineering

**Momentum Features**:
```python
# Recent momentum (last 15 min)
features['momentum_micro'] = bqx['w15_bqx_return']

# Short-term trend (last 30-60 min)
features['momentum_short'] = bqx['w60_bqx_return']

# Momentum acceleration
features['momentum_accel'] = (
    bqx['w15_bqx_return'] - bqx['w60_bqx_return']
)
```

**Volatility Features**:
```python
# Recent volatility
features['vol_recent'] = bqx['w15_bqx_stdev']

# Volatility regime change
features['vol_regime'] = (
    bqx['w15_bqx_stdev'] / bqx['w75_bqx_stdev']
)
```

### 2. Prediction Modeling

**Feature Set**:
```python
X = [
    BQX features (15, 30, 45, 60, 75 min backward),  # Simple momentum
    REG features (60, 90, 150, ... min backward),     # Complex patterns
]

Y = [
    FWD features (60, 90, 150, ... min forward)       # Prediction targets
]

model.fit(X, Y)
```

**Example Model**:
```python
# Predict next 60 minutes from recent momentum + regression
model = RandomForestRegressor()

features = pd.concat([
    bqx[['w15_bqx_return', 'w30_bqx_return', 'w60_bqx_return']],
    reg[['w60_quad_norm', 'w60_r2']],
], axis=1)

target = fwd['w60_fwd_return']

model.fit(features, target)
```

### 3. Trading Strategies

**Momentum Strategy**:
```python
# Long signal: Strong recent upward momentum
if bqx['w15_bqx_return'] < -0.001:  # Negative = price increased
    if bqx['w30_bqx_return'] < bqx['w15_bqx_return']:  # Accelerating
        enter_long()

# Short signal: Strong recent downward momentum
if bqx['w15_bqx_return'] > 0.001:  # Positive = price declined
    if bqx['w30_bqx_return'] > bqx['w15_bqx_return']:  # Accelerating
        enter_short()
```

**Volatility-Based Position Sizing**:
```python
# Reduce position size in high volatility
position_size = base_size * (
    target_volatility / bqx['agg_bqx_volatility']
)
```

### 4. Feature Comparison Analysis

**BQX vs FWD Correlation**:
```python
# Does recent 60-min momentum predict next 60-min movement?
correlation = np.corrcoef(
    bqx['w60_bqx_return'],
    fwd['w60_fwd_return']
)

# If high correlation: Momentum persists
# If negative correlation: Mean reversion
# If low correlation: Random walk
```

---

## Advantages of BQX Tables

### 1. Simplicity
- ✅ Easy to understand (cumulative returns)
- ✅ Easy to compute (simple sums)
- ✅ Easy to interpret (higher = downward momentum)

### 2. Real-Time Capability
- ✅ Only needs past data (available in real-time)
- ✅ Fast computation (no matrix operations)
- ✅ Can update incrementally (rolling windows)

### 3. Complementarity
- ✅ Fills gap between REG (complex) and raw M1 (too simple)
- ✅ Shorter windows (15-75 min) vs REG (60-630 min)
- ✅ Different perspective: Simple sums vs quadratic regression

### 4. Symmetry with FWD
- ✅ Same structure (makes modeling easier)
- ✅ Same metrics (return, max, min, avg, stdev, endpoint)
- ✅ Time-lagged relationship (BQX today = FWD yesterday)

### 5. Specific Use Cases
- ✅ Momentum detection
- ✅ Trend strength measurement
- ✅ Breakout confirmation
- ✅ Volatility regime identification

---

## Implementation Complexity

### Compared to FWD Implementation

| Aspect | FWD | BQX | Complexity |
|--------|-----|-----|------------|
| **Data Direction** | Future (needs lookahead) | Past (already available) | ✅ Simpler |
| **Edge Effects** | End of data (no future) | Start of data (no past) | ✅ Same |
| **Calculation** | Same formulas | Same formulas (reversed) | ✅ Same |
| **Window Count** | 6 windows | 5 windows | ✅ Slightly simpler |
| **Table Count** | 28 tables | 28 tables | ✅ Same |
| **Partitioning** | Monthly | Monthly | ✅ Same |

**Estimated Effort**: ~80% of FWD implementation (can reuse most code)

---

## Data Architecture Impact

### Current State

```
M1 Tables (20 fields)
    ↓
    ├─→ REG Tables (75 fields) ─┐
    │                             ├─→ MV Tables (45 fields) → ML Models
    └─→ FWD Tables (46 fields) ─┘
```

### With BQX

```
M1 Tables (20 fields)
    ↓
    ├─→ REG Tables (75 fields) ─┐
    ├─→ BQX Tables (40 fields) ─┼─→ MV Tables (85+ fields) → ML Models
    └─→ FWD Tables (46 fields) ─┘
```

**Total Feature Expansion**:
- Before: 75 (REG) = 75 features
- After: 75 (REG) + 40 (BQX) = 115 backward-looking features
- **Increase**: +53% more features for ML training

---

## Recommendation

### ✅ **STRONGLY RECOMMEND IMPLEMENTATION**

**Rationale**:

1. **Fills Critical Gap**: Simple momentum features between M1 and REG
2. **Short-Term Focus**: 15-75 min windows capture recent micro-patterns
3. **Symmetric Design**: Mirrors FWD structure elegantly
4. **ML Value**: Provides complementary features to REG
5. **Low Complexity**: Reuses FWD logic with reversed direction
6. **Real-Time Ready**: Only uses past data (production-friendly)

**Implementation Priority**: HIGH

**Estimated Timeline**:
- Schema design: 2 hours
- Worker script: 4 hours
- Testing: 2 hours
- Historical population: 8 hours (parallel)
- **Total**: ~2 days (16 hours)

**Storage Impact**:
- ~40 fields × 28 pairs × 50 months × 30 days × 1440 min/day
- Estimated: ~500 GB additional storage
- **Acceptable** given 2.478 TB current size (~20% increase)

---

## Next Steps

1. **Review & Approve**: User confirms BQX table design
2. **Create DDL**: Generate SQL for all 28 bqx tables
3. **Implement Worker**: Write backward_worker.py (mirror forward_worker.py)
4. **Populate Historical**: Run backfill for existing M1 data
5. **Update MVs**: Add BQX features to materialized views
6. **Documentation**: Complete formula reference

---

**Analysis Complete**: BQX tables are a valuable, well-reasoned addition to the BQX data architecture.

**Key Innovation**: Symmetric backward/forward feature architecture enables time-lagged validation and momentum-based predictions.
