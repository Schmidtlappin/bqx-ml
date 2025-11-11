# BQX ML Feature Lagging Strategy

**Version:** 1.0
**Date:** 2025-01-11
**Purpose:** Define which features get lagged and why

---

## Overview

Lagging creates historical context by adding features from previous timestamps. The strategy determines which of the 228 base features should be lagged and which shouldn't.

**Summary:**
- **Lagged:** 142 features × 4 lag windows = 568 + 142 base = 710 features
- **Non-Lagged:** 86 features (remain as-is)
- **Causality:** 13 features (61-minute lag applied)
- **Total:** 710 + 86 + 13 = **809 features**

---

## Lag Windows

**4 Lag Windows:**
1. **60 minutes (t-60):** Recent history, captures short-term momentum
2. **120 minutes (t-120):** Medium-term patterns
3. **180 minutes (t-180):** Longer-term trends
4. **240 minutes (t-240):** 4-hour lookback, captures session patterns

**Why 4 Windows?**
- Captures multi-scale temporal patterns
- Random Forest can learn which lag is most predictive per feature
- Trade-off: More features vs model complexity

---

## Lagged Features: 142 Total

### 1. BQX Features (40) - ALL LAGGED

**Rationale:** BQX represents backward momentum. Historical values provide trend context.

**Example:**
```
Original: w60_bqx_return_t0 = 0.00043
Lagged:   w60_bqx_return_t0_lag60 = 0.00038   (value 60 min ago)
          w60_bqx_return_t0_lag120 = 0.00041  (value 120 min ago)
          w60_bqx_return_t0_lag180 = 0.00039  (value 180 min ago)
          w60_bqx_return_t0_lag240 = 0.00042  (value 240 min ago)

Total: 1 feature → 5 features (original + 4 lags)
```

**40 BQX features × 4 lags = 160 lagged + 40 base = 200 total BQX features**

### 2. REG Features (57) - ALL LAGGED

**Rationale:** Regression coefficients (a_coef, b_coef, c_coef) and fit metrics (r2, rmse) show how price trend has evolved. Lagged versions capture trend changes.

**Example:**
```
Original: w60_r2_t0 = 0.87  (current 60-min trend strength)
Lagged:   w60_r2_t0_lag60 = 0.82   (trend strength 60 min ago)
          w60_r2_t0_lag120 = 0.79  (trend strength 120 min ago)
          ...

Insight: If r2 increasing (0.79 → 0.82 → 0.87), trend strengthening
```

**57 REG features × 4 lags = 228 lagged + 57 base = 285 total REG features**

### 3. Volume Features (10) - ALL LAGGED

**Rationale:** Volume patterns (spikes, trends) are predictive. Lagging shows volume evolution.

**Lagged Features:**
1. w15_volume_ratio
2. w30_volume_ratio
3. w60_volume_ratio
4. volume_spike
5. volume_trend_slope
6. cumulative_volume_60min
7. volume_weighted_return
8. volume_price_correlation_60min
9. relative_volume_position
10. volume_volatility_60min

**10 Volume × 4 lags = 40 lagged + 10 base = 50 total Volume features**

### 4. Spread Features (20) - ALL LAGGED

**Rationale:** Spread (bid-ask) dynamics change over time. Lagging captures liquidity evolution.

**Lagged Features:**
- spread_mean_60min, spread_volatility_60min, spread_pct_of_rate
- spread_trend_slope, spread_spike
- bid_ask_imbalance, effective_spread, quoted_spread, realized_spread
- price_impact, roll_cost
- bid_depth, ask_depth, depth_imbalance
- spread_range_60min, spread_percentile_60min
- mid_price_volatility, tick_direction, tick_rule
- order_flow_toxicity

**20 Spread × 4 lags = 80 lagged + 20 base = 100 total Spread features**

### 5. Correlation Features (15) - ALL LAGGED

**Rationale:** Cross-pair correlations shift over time (correlation regimes). Lagging detects regime changes.

**Lagged Features:**
- Short-term correlations (5): corr_related_15min, corr_related_60min, etc.
- Lagged correlations (5): corr_related_60min_lag1, etc.
- Meta features (5): corr_strength_60min, corr_direction_change, etc.

**15 Correlation × 4 lags = 60 lagged + 15 base = 75 total Correlation features**

### Summary: Lagged Features

| Category | Base | Lags | Total |
|----------|------|------|-------|
| BQX | 40 | 160 | 200 |
| REG | 57 | 228 | 285 |
| Volume | 10 | 40 | 50 |
| Spread | 20 | 80 | 100 |
| Correlation | 15 | 60 | 75 |
| **TOTAL** | **142** | **568** | **710** |

---

## Non-Lagged Features: 86 Total

### 1. Time Features (8) - NOT LAGGED

**Rationale:** Time features are cyclical and context-dependent. Lagging doesn't add information.

**Why Not Lag:**
- `hour_sin, hour_cos`: Cyclical (24-hour period). Lag doesn't help (hour_sin at t-60 is predictable from hour_sin at t0).
- `day_of_week_sin, day_of_week_cos`: Weekly cycle. Same reasoning.
- `session_overlap`: Boolean (e.g., London + NY overlap). Lag is deterministic from current time.
- `is_weekend_approach`: Boolean. Lag is deterministic.
- `minutes_since_market_open`: Linear time since event. Lag is t0_value + 60.
- `trading_session`: Categorical (Asian/London/NY/Off). Lag is deterministic.

**Decision:** Use only current values (t0). Model learns time patterns directly.

### 2. Currency Indices (8) - NOT LAGGED

**Rationale:** Currency strength indices (USD, EUR, etc.) are GLOBAL measures, not pair-specific. They're already computed across all pairs and capture multi-timeframe information.

**Why Not Lag:**
- Indices already incorporate historical price movements (computed from BQX across all pairs)
- Lagging would duplicate information already in lagged BQX features
- Model can learn to combine current index with lagged pair-specific features

**Decision:** Use only current values (t0).

### 3. Statistics Features (5) - NOT LAGGED

**Rationale:** Already computed over 60-minute windows (historical aggregates).

**Features:**
- skewness_60min: Distribution shape over past 60 min
- kurtosis_60min: Tail heaviness over past 60 min
- median_absolute_deviation_60min: Robust volatility over past 60 min
- entropy_60min: Price distribution randomness over past 60 min
- autocorrelation_lag1: Correlation with t-1 (already a lag!)

**Why Not Lag:**
- Each feature already looks back 60 minutes
- Lagging would create 60-120 min lookback (less relevant for short-term prediction)
- Diminishing returns vs increased dimensionality

**Decision:** Use only current values (t0). Consider lagging in future if proven useful.

### 4. Bollinger Bands (5) - NOT LAGGED

**Rationale:** Bollinger bands are computed over 20-period windows (inherently historical).

**Features:**
- bollinger_upper_20: Upper band (mean + 2×std over 20 periods)
- bollinger_lower_20: Lower band (mean - 2×std over 20 periods)
- bollinger_middle_20: Middle band (20-period moving average)
- bollinger_width_20: Band width (upper - lower)
- bollinger_percent_b: Price position within bands

**Why Not Lag:**
- Each feature already incorporates 20-period history
- Model can learn band dynamics from current values
- Lagging adds complexity without proven benefit

**Decision:** Use only current values (t0).

### 5. Technical Indicators (45) - NOT LAGGED

**Rationale:** Technical indicators (RSI, MACD, ADX, etc.) are computed over historical windows.

**Examples:**
- RSI_14: Relative Strength Index (14-period)
- MACD: Moving Average Convergence Divergence (12/26/9 periods)
- ADX_14: Average Directional Index (14-period)
- ATR_14: Average True Range (14-period)

**Why Not Lag:**
- Each indicator already incorporates historical data (14-26 periods)
- Lagging would create very long lookbacks (14-period RSI lagged 240 min → 254-period equivalent)
- Technical traders use current indicator values, not historical

**Decision:** Use only current values (t0).

### 6. Fibonacci Features (12) - NOT LAGGED

**Rationale:** Fibonacci levels are based on swing highs/lows (historical anchor points). Current levels are most relevant.

**Features:**
- 5 retracement levels: Based on recent swing high/low
- 3 extension levels: Based on recent swing points
- 4 meta features: Distance to levels, grid position, time since swing

**Why Not Lag:**
- Levels are anchored to historical swings (already historical)
- Current price position vs levels is what matters
- Lagged levels would be outdated (swing points change)

**Decision:** Use only current values (t0).

### 7. Derived Features (3) - NOT LAGGED

**Rationale:** Derived features aggregate multiple base features. Lagging the aggregates duplicates lagged base features.

**Features:**
1. momentum_alignment: Counts aligned BQX windows (already uses multiple timeframes)
2. volatility_regime: Tertile classification (aggregate measure)
3. trend_strength: Average R² across REG windows (aggregate measure)

**Why Not Lag:**
- Each is an aggregate of lagged base features
- Lagging would duplicate information
- Model learns from lagged base features directly

**Decision:** Use only current values (t0).

### Summary: Non-Lagged Features

| Category | Count | Reasoning |
|----------|-------|-----------|
| Time | 8 | Cyclical/deterministic |
| Currency Indices | 8 | Global measures, already historical |
| Statistics | 5 | Already 60-min windows |
| Bollinger | 5 | Already 20-period windows |
| Technical Indicators | 45 | Already multi-period (14-26) |
| Fibonacci | 12 | Anchored to historical swings |
| Derived | 3 | Aggregates of lagged features |
| **TOTAL** | **86** | |

---

## Temporal Causality Features: 13

### Special 61-Minute Lag

**Purpose:** Enforce temporal causality rule to prevent data leakage.

**Rule:** Features computed over 60-minute windows may use data from t-60 to t0. To ensure prediction at t+60 doesn't use future data, apply 61-minute lag to w60_ and agg_ features.

**Features Affected:**

**w60_ Features (6):**
1. w60_bqx_return_causality_lag61
2. w60_bqx_max_index_causality_lag61
3. w60_bqx_min_index_causality_lag61
4. w60_bqx_avg_index_causality_lag61
5. w60_bqx_stdev_index_causality_lag61
6. w60_bqx_endpoint_causality_lag61

**agg_ Features (7):**
7. agg_bqx_return_causality_lag61
8. agg_bqx_max_index_causality_lag61
9. agg_bqx_min_index_causality_lag61
10. agg_bqx_avg_index_causality_lag61
11. agg_bqx_stdev_index_causality_lag61
12. agg_bqx_range_causality_lag61
13. agg_bqx_volatility_causality_lag61

**Total:** 13 causality-lagged features

**Implementation:**
```python
# In features.py
def apply_temporal_causality_rule(df, lag_minutes=61):
    causality_features = []
    for col in df.columns:
        if col.startswith('w60_') or col.startswith('agg_'):
            df[f'{col}_causality_lag61'] = df[col].shift(61)
            causality_features.append(f'{col}_causality_lag61')
    return df, causality_features
```

---

## Implementation in SageMaker

### Processing Job (Task 3.1.2)

```python
# processing.py
def apply_lagging_strategy(df, config):
    # Lagged feature categories
    lagged_categories = ['bqx', 'reg', 'volume', 'spread', 'correlation']
    
    # Non-lagged feature categories
    non_lagged_categories = ['time', 'currency', 'statistics', 'bollinger', 
                              'technical', 'fibonacci', 'derived']
    
    lagged_features = []
    for col in df.columns:
        # Check if column belongs to lagged category
        if any(cat in col.lower() for cat in lagged_categories):
            # Apply 4 lags
            for lag in [60, 120, 180, 240]:
                df[f'{col}_lag{lag}'] = df[col].shift(lag)
                lagged_features.append(f'{col}_lag{lag}')
    
    # Apply temporal causality
    df, causality_features = apply_temporal_causality_rule(df, lag_minutes=61)
    
    return df, lagged_features, causality_features
```

### Feature Extraction Lambda (Task 3.4.1)

```python
# feature_extraction_lambda.py
def extract_features_with_lags(pair, timestamp):
    # Query current features (t0)
    features_t0 = query_aurora(pair, timestamp)  # 228 features
    
    # Query lagged features
    lags = [60, 120, 180, 240]
    lagged_features = {}
    for lag in lags:
        timestamp_lagged = timestamp - timedelta(minutes=lag)
        features_lagged = query_aurora(pair, timestamp_lagged)
        
        # Only lag the 142 lagable features
        for feature in LAGGED_FEATURE_LIST:  # 142 features
            lagged_features[f'{feature}_lag{lag}'] = features_lagged[feature]
    
    # Query causality-lagged features (t-61)
    timestamp_causality = timestamp - timedelta(minutes=61)
    features_causality = query_aurora(pair, timestamp_causality)
    causality_features = {}
    for feature in CAUSALITY_FEATURE_LIST:  # 13 features
        causality_features[f'{feature}_causality_lag61'] = features_causality[feature]
    
    # Combine: 228 base + 568 lagged + 13 causality = 809 features
    all_features = {**features_t0, **lagged_features, **causality_features}
    return all_features  # 809 features
```

---

## Optimization Opportunities

### 1. Selective Lagging

**Current:** Lag 142 features × 4 windows = 568 lagged features
**Optimization:** Only lag features with high importance

**Process:**
1. Train model with all 809 features
2. Identify which lagged features have low importance
3. Remove low-importance lagged features
4. Retrain with reduced feature set

**Expected Reduction:** 568 → 300 lagged features (47% reduction)
**Benefit:** Faster feature extraction, lower storage

### 2. Adaptive Lag Windows

**Current:** Fixed 4 windows (60, 120, 180, 240)
**Optimization:** Learn optimal lag windows per feature

**Process:**
1. Try different lag window combinations
2. Use validation set to evaluate
3. Keep only windows that improve R²

**Expected:** Some features need only 1-2 lags, not 4

### 3. Feature Caching

**Problem:** Extracting 809 features requires many Aurora queries
**Solution:** Cache lagged features for 5 minutes

**Implementation:**
```python
# feature_extraction_lambda.py
cache = {}  # Lambda-level cache

def get_lagged_features(pair, timestamp):
    cache_key = f'{pair}_{timestamp}'
    if cache_key in cache and cache[cache_key]['age'] < 300:  # 5 min
        return cache[cache_key]['features']
    
    # Fetch from Aurora
    features = query_aurora(pair, timestamp)
    cache[cache_key] = {'features': features, 'age': 0}
    return features
```

**Benefit:** Reduce Aurora load, improve latency (<100ms → <50ms)

---

## Validation Tests

### Test 1: Causality Check

**Verify:** No feature uses data from t+1 to t+60

```python
def test_temporal_causality(df, target_col='w60_bqx_return_t60'):
    # Target is at t+60
    target_time = df.index.max()
    
    # Check all features are at t0 or earlier
    for col in df.columns:
        if 'lag' in col:
            lag = int(col.split('lag')[-1])
            assert lag >= 1, f"{col} has positive lag (future data)"
        elif 'causality' in col:
            assert 'lag61' in col, f"{col} missing causality lag"
```

### Test 2: Lag Correctness

**Verify:** Lagged values match historical values

```python
def test_lag_correctness(df):
    for col in df.columns:
        if '_lag60' in col:
            base_col = col.replace('_lag60', '')
            # Value at t0_lag60 should equal value at t-60
            for idx in df.index:
                t0 = df.loc[idx, base_col]
                t_lag60 = df.loc[idx - timedelta(minutes=60), base_col]
                assert abs(t0 - t_lag60) < 1e-6
```

---

## Conclusion

**Lagging Strategy Summary:**
- **Lag:** 142 features (BQX, REG, Volume, Spread, Correlation) × 4 windows = 710 total
- **Don't Lag:** 86 features (Time, Currency, Stats, Bollinger, Technical, Fibonacci, Derived)
- **Causality:** 13 features (w60_, agg_) with 61-minute lag

**Total:** 710 + 86 + 13 = **809 features** → Select top 70 → Train model

**Rationale:** Balance information gain (lagging) vs dimensionality (curse of dimensionality). Lag features where historical context is predictive, skip where current value sufficient.
