# BQX ML Strategy Refactoring - Complete Analysis

**Date**: 2025-11-08
**Request**: Refactor ML strategy from predicting FWD values to predicting future BQX values

---

## Executive Summary

User requests a **paradigm shift** in ML strategy:

**OLD Strategy**: Predict FWD (forward returns) directly
```
X_t → Y_t where Y_t = FWD_t (what will happen from t to t+60)
```

**NEW Strategy**: Predict future BQX (backward returns that will be observed later)
```
X_t → Y_t where Y_t = BQX_{t+60} (what BQX will show at t+60)
```

**Key Insight**: These are **mathematically equivalent** but conceptually different:
- FWD_t measures future movement from time t's perspective
- BQX_{t+60} measures past movement from time (t+60)'s perspective
- **Both measure the same price movement**: t to t+60

**Strategic Advantage**: BQX-based approach enables **autoregressive momentum modeling** with shorter prediction horizons.

---

## The Critical Mathematical Relationship

### Understanding the Equivalence

**At Time t** (now):
```
FWD w60_fwd_return = Σ(i=1 to 60)[rate(t) - rate(t+i)] / rate(t)
                     ↑                                    ↑
                  Measures movement from t to t+60 (future)
```

**At Time t+60** (60 minutes later):
```
BQX w60_bqx_return = Σ(i=1 to 60)[rate(t+60-i) - rate(t+60)] / rate(t+60)
                     ↑                                        ↑
                  Measures movement from t to t+60 (past, but same period!)
```

### Concrete Example

**Scenario**: Price movement from 00:00 to 01:00
```
00:00 (t):     rate = 1.0880
00:01 (t+1):   rate = 1.0879
00:02 (t+2):   rate = 1.0878
...
00:59 (t+59):  rate = 1.0871
01:00 (t+60):  rate = 1.0870
```

**FWD Calculation (at 00:00)**:
```
w60_fwd_return = [(1.0880 - 1.0879) + (1.0880 - 1.0878) + ... + (1.0880 - 1.0870)] / 1.0880
                = [0.0001 + 0.0002 + ... + 0.0010] / 1.0880
                = 0.0300 / 1.0880
                = 0.0276 (2.76%)

Interpretation: "Price will cumulatively decline by 2.76% over next 60 minutes"
```

**BQX Calculation (at 01:00, looking back)**:
```
w60_bqx_return = [(1.0870 - 1.0870) + (1.0871 - 1.0870) + ... + (1.0879 - 1.0870)] / 1.0870
                = [0.0000 + 0.0001 + ... + 0.0009] / 1.0870
                = 0.0285 / 1.0870
                = 0.0262 (2.62%)

Interpretation: "Price cumulatively declined by 2.62% over past 60 minutes"
```

**Near Equivalence**: 0.0276 vs 0.0262 (small difference due to normalization by different rates)

### Normalization Difference

**FWD normalizes by rate(t)**:
```
Σ differences / rate(t)
```

**BQX normalizes by rate(t+60)**:
```
Σ differences / rate(t+60)
```

If rate(t) ≈ rate(t+60) (small total movement), then FWD_t ≈ BQX_{t+60}

**Exact Relationship**:
```
BQX_{t+60} ≈ FWD_t × [rate(t) / rate(t+60)]

If rate changed 1%:  ratio ≈ 0.99 or 1.01
If rate changed 0.1%: ratio ≈ 0.999 or 1.001

For typical forex movements (<1%), FWD and future BQX are nearly identical.
```

---

## Why Predict Future BQX Instead of FWD?

### Conceptual Advantages

**1. Observable Validation**
```
OLD (FWD):
  Predict: FWD_t (forward return)
  Validate: ??? (FWD is computed once, never updated)
  Problem: Can't directly observe if prediction was right

NEW (BQX):
  Predict: BQX_{t+60} (what BQX will show at t+60)
  Validate: Wait 60 min, check actual BQX_{t+60}
  Benefit: Direct validation against observable metric
```

**2. Consistent Framework**
```
OLD:
  Features: Backward-looking (REG, M1)
  Targets: Forward-looking (FWD)
  Issue: Conceptual mismatch (backward → forward)

NEW:
  Features: Backward-looking (REG, BQX_t)
  Targets: Future backward-looking (BQX_{t+60})
  Benefit: Consistent framework (all are cumulative returns)
```

**3. Autoregressive Capability**
```
OLD:
  Cannot use FWD as a feature (it's the target!)
  Miss: Momentum persistence patterns

NEW:
  Can use BQX_t to predict BQX_{t+60}
  Captures: "If momentum is X now, what will it be later?"
  Example: Strong positive BQX_t → likely positive BQX_{t+60} (momentum persistence)
```

### Technical Advantages

**1. Multiple Prediction Horizons**
```
BQX Windows: 15, 30, 45, 60, 75 minutes

Can predict:
  BQX_{t+15} using BQX_t  (15-min ahead)
  BQX_{t+30} using BQX_t  (30-min ahead)
  BQX_{t+45} using BQX_t  (45-min ahead)
  BQX_{t+60} using BQX_t  (60-min ahead)
  BQX_{t+75} using BQX_t  (75-min ahead)

Finer granularity than FWD (which only has 60, 90, 150, 240, 390, 630)
```

**2. Feature-Target Alignment**
```
Feature: w60_bqx_return (cumulative return over 60 min)
Target:  w60_bqx_return at t+60 (same metric, different time)

Benefit:
  - Same units
  - Same interpretation
  - Easier to understand model coefficients
  - Can measure momentum persistence directly
```

**3. Ensemble Opportunities**
```
Can create ensemble of predictions:

Model 1: Predict BQX_{t+15} from BQX_t (very short-term)
Model 2: Predict BQX_{t+30} from BQX_t (short-term)
Model 3: Predict BQX_{t+60} from BQX_t (medium-term)

Combine: Weighted average based on prediction horizon
```

---

## The Autoregressive Strategy

### Core Concept

**Autoregression**: Use past values of a variable to predict future values of the same variable

**Traditional Time Series**:
```
Price_t = f(Price_{t-1}, Price_{t-2}, ...)
```

**BQX Autoregression**:
```
BQX_{t+60} = f(BQX_t, BQX_{t-60}, BQX_{t-120}, ...)
```

### Why This Works

**1. Momentum Persistence**
```
If BQX_t > 0 (downward momentum):
  → Likely BQX_{t+60} > 0 (momentum continues)

If BQX_t < 0 (upward momentum):
  → Likely BQX_{t+60} < 0 (momentum continues)

Autocorrelation in price movements!
```

**2. Mean Reversion**
```
If BQX_t >> 0 (extreme downward momentum):
  → Likely BQX_{t+60} closer to 0 (mean reversion)

If BQX_t << 0 (extreme upward momentum):
  → Likely BQX_{t+60} closer to 0 (mean reversion)

Capture regime shifts!
```

**3. Momentum Acceleration/Deceleration**
```
If BQX_t > BQX_{t-60} (accelerating decline):
  → Likely BQX_{t+60} > BQX_t (acceleration continues)

If BQX_t < BQX_{t-60} (decelerating):
  → Likely BQX_{t+60} < BQX_t (trend weakening)
```

---

## Feature Engineering for BQX Prediction

### Category 1: Autoregressive BQX Features

**Current Momentum**:
```python
# Current window momentum
features['bqx_w15_current'] = bqx_t['w15_bqx_return']
features['bqx_w30_current'] = bqx_t['w30_bqx_return']
features['bqx_w60_current'] = bqx_t['w60_bqx_return']
```

**Lagged Momentum**:
```python
# Momentum 60 minutes ago
features['bqx_w60_lag60'] = bqx_{t-60}['w60_bqx_return']

# Momentum 120 minutes ago
features['bqx_w60_lag120'] = bqx_{t-120}['w60_bqx_return']
```

**Momentum Change**:
```python
# Acceleration: Current vs previous
features['bqx_accel_60'] = (
    bqx_t['w60_bqx_return'] - bqx_{t-60}['w60_bqx_return']
)

# Cross-window acceleration
features['bqx_accel_cross'] = (
    bqx_t['w15_bqx_return'] - bqx_t['w60_bqx_return']
)
```

### Category 2: Volatility Features

**Current Volatility**:
```python
features['bqx_vol_w15'] = bqx_t['w15_bqx_stdev']
features['bqx_vol_w60'] = bqx_t['w60_bqx_stdev']
```

**Volatility Regime**:
```python
# High volatility = unstable, low predictability
features['vol_regime'] = (
    bqx_t['w15_bqx_stdev'] / bqx_t['w60_bqx_stdev']
)

# Range as % of current rate
features['vol_range'] = (
    (bqx_t['w60_bqx_max'] - bqx_t['w60_bqx_min']) / rate_t
)
```

### Category 3: REG Pattern Features

**Quadratic Curvature**:
```python
# Parabolic patterns indicate reversals
features['reg_quad_w60'] = reg_t['w60_quad_norm']
features['reg_quad_w240'] = reg_t['w240_quad_norm']
```

**Trend Strength**:
```python
# R² indicates how well price follows quadratic pattern
features['reg_r2_w60'] = reg_t['w60_r2']
features['reg_r2_w240'] = reg_t['w240_r2']
```

### Category 4: Cross-Window Relationships

**Momentum Convergence/Divergence**:
```python
# Short-term vs long-term momentum
features['bqx_div_short_long'] = (
    bqx_t['w15_bqx_return'] - bqx_t['w75_bqx_return']
)

# If positive: Short-term stronger than long-term (divergence)
# If negative: Convergence
```

**Multi-Timeframe Alignment**:
```python
# All windows pointing same direction = strong signal
features['bqx_alignment'] = np.sign([
    bqx_t['w15_bqx_return'],
    bqx_t['w30_bqx_return'],
    bqx_t['w45_bqx_return'],
    bqx_t['w60_bqx_return'],
    bqx_t['w75_bqx_return']
]).sum()  # Range: -5 to +5
```

---

## Prediction Architecture

### Multi-Horizon Prediction Framework

**Predict 5 future BQX values simultaneously**:

```python
# At time t, predict BQX at multiple future times
targets = {
    'BQX_{t+15}': bqx_{t+15}['w15_bqx_return'],
    'BQX_{t+30}': bqx_{t+30}['w30_bqx_return'],
    'BQX_{t+45}': bqx_{t+45}['w45_bqx_return'],
    'BQX_{t+60}': bqx_{t+60}['w60_bqx_return'],
    'BQX_{t+75}': bqx_{t+75}['w75_bqx_return'],
}

# Features (all at time t)
features = {
    'BQX_current': [bqx_t['w15'], bqx_t['w30'], ..., bqx_t['w75']],
    'BQX_lagged': [bqx_{t-15}['w15'], ..., bqx_{t-75}['w75']],
    'REG': [reg_t['w60_quad_norm'], reg_t['w60_r2'], ...],
    'Volatility': [bqx_t['w15_stdev'], bqx_t['agg_volatility'], ...],
}

# Model
model = MultiOutputRegressor(...)
model.fit(features, targets)
```

### Model Architecture Options

**Option 1: Separate Models per Horizon**
```python
# 5 independent models
model_15 = RandomForestRegressor()
model_30 = RandomForestRegressor()
model_45 = RandomForestRegressor()
model_60 = RandomForestRegressor()
model_75 = RandomForestRegressor()

# Train separately
model_15.fit(X, Y_15)
model_30.fit(X, Y_30)
...

Pros: Specialized per horizon
Cons: No shared learning across horizons
```

**Option 2: Multi-Output Model**
```python
# Single model, multiple outputs
from sklearn.multioutput import MultiOutputRegressor

model = MultiOutputRegressor(
    XGBRegressor(...)
)

# Predict all horizons simultaneously
predictions = model.predict(X)  # Shape: (n_samples, 5)

Pros: Shares learning across horizons
Cons: All horizons treated equally
```

**Option 3: Sequence Model (LSTM/GRU)**
```python
# Treat as sequence prediction
from keras.models import Sequential
from keras.layers import LSTM, Dense

model = Sequential([
    LSTM(64, input_shape=(lookback, n_features)),
    Dense(32, activation='relu'),
    Dense(5)  # 5 future BQX values
])

model.compile(loss='mse', optimizer='adam')
model.fit(X_seq, Y_multi)

Pros: Captures temporal dependencies
Cons: More complex, needs more data
```

**Option 4: Hierarchical Model** ⭐ **RECOMMENDED**
```python
# First: Predict short-term (15 min)
model_l1 = XGBRegressor()
model_l1.fit(X, Y_15)

# Second: Use short-term prediction to predict medium-term
X_l2 = concat([X, pred_15])
model_l2 = XGBRegressor()
model_l2.fit(X_l2, Y_30)

# Third: Use all previous predictions for long-term
X_l3 = concat([X, pred_15, pred_30])
model_l3 = XGBRegressor()
model_l3.fit(X_l3, Y_60)

Pros: Captures cascading uncertainty
Cons: Sequential (can't parallelize)
```

---

## Data Preparation Strategy

### Time Alignment

**Critical**: Align features at time t with targets at time t+W

```python
import pandas as pd

# Load data
bqx = pd.read_sql("SELECT * FROM bqx.bqx_eurusd ORDER BY ts_utc", conn)
reg = pd.read_sql("SELECT * FROM bqx.reg_eurusd ORDER BY ts_utc", conn)

# Create time-shifted targets
horizons = [15, 30, 45, 60, 75]
for h in horizons:
    # Shift BQX backwards to align with features
    bqx[f'target_bqx_w{h}_ahead'] = bqx[f'w{h}_bqx_return'].shift(-h)

# Merge features and targets
df = bqx.merge(reg, on='ts_utc', how='inner')

# Feature columns (at time t)
feature_cols = [
    'w15_bqx_return', 'w30_bqx_return', 'w45_bqx_return',
    'w60_bqx_return', 'w75_bqx_return',
    'w60_quad_norm', 'w60_r2', 'w240_quad_norm',
]

# Target columns (at time t+h)
target_cols = [
    'target_bqx_w15_ahead',
    'target_bqx_w30_ahead',
    'target_bqx_w45_ahead',
    'target_bqx_w60_ahead',
    'target_bqx_w75_ahead',
]

# Remove rows with NaN targets (edge effects)
df = df.dropna(subset=target_cols)

X = df[feature_cols]
Y = df[target_cols]
```

### Train/Test Split

**IMPORTANT**: Must respect time series ordering!

```python
from sklearn.model_selection import TimeSeriesSplit

# Option 1: Simple time-based split
split_date = '2024-10-01'
train = df[df['ts_utc'] < split_date]
test = df[df['ts_utc'] >= split_date]

X_train, Y_train = train[feature_cols], train[target_cols]
X_test, Y_test = test[feature_cols], test[target_cols]

# Option 2: Walk-forward cross-validation
tscv = TimeSeriesSplit(n_splits=5)
for train_idx, val_idx in tscv.split(df):
    X_train = X.iloc[train_idx]
    Y_train = Y.iloc[train_idx]
    X_val = X.iloc[val_idx]
    Y_val = Y.iloc[val_idx]

    model.fit(X_train, Y_train)
    score = model.score(X_val, Y_val)
```

---

## Model Training Pipeline

### Complete Example

```python
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb

# Step 1: Load and prepare data
def load_data(pair='eurusd'):
    """Load BQX and REG data for a pair"""
    bqx = pd.read_sql(
        f"SELECT * FROM bqx.bqx_{pair} ORDER BY ts_utc",
        conn
    )
    reg = pd.read_sql(
        f"SELECT * FROM bqx.reg_{pair} ORDER BY ts_utc",
        conn
    )

    # Merge on timestamp
    df = bqx.merge(reg, on='ts_utc', suffixes=('_bqx', '_reg'))
    return df

# Step 2: Feature engineering
def create_features(df):
    """Create autoregressive and derived features"""
    features = pd.DataFrame(index=df.index)

    # Current BQX momentum (all windows)
    for w in [15, 30, 45, 60, 75]:
        features[f'bqx_w{w}'] = df[f'w{w}_bqx_return']
        features[f'bqx_w{w}_stdev'] = df[f'w{w}_bqx_stdev']

    # Lagged BQX (60 min ago)
    for w in [15, 30, 60]:
        features[f'bqx_w{w}_lag60'] = df[f'w{w}_bqx_return'].shift(60)

    # Momentum acceleration
    features['bqx_accel'] = (
        df['w15_bqx_return'] - df['w60_bqx_return']
    )

    # REG features (pattern detection)
    features['reg_quad_w60'] = df['w60_quad_norm']
    features['reg_r2_w60'] = df['w60_r2']
    features['reg_quad_w240'] = df['w240_quad_norm']

    # Volatility features
    features['vol_regime'] = (
        df['w15_bqx_stdev'] / df['w60_bqx_stdev']
    )
    features['agg_volatility'] = df['agg_bqx_volatility']

    return features.dropna()

# Step 3: Create targets
def create_targets(df):
    """Create time-shifted BQX targets"""
    targets = pd.DataFrame(index=df.index)

    for w in [15, 30, 45, 60, 75]:
        # Shift negative to get future values
        targets[f'bqx_w{w}_ahead'] = df[f'w{w}_bqx_return'].shift(-w)

    return targets.dropna()

# Step 4: Train model
def train_bqx_predictor(pair='eurusd'):
    """Train multi-horizon BQX predictor"""

    # Load data
    df = load_data(pair)

    # Create features and targets
    X = create_features(df)
    Y = create_targets(df)

    # Align indices
    common_idx = X.index.intersection(Y.index)
    X = X.loc[common_idx]
    Y = Y.loc[common_idx]

    # Train/test split (80/20, time-based)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    Y_train, Y_test = Y.iloc[:split_idx], Y.iloc[split_idx:]

    # Train multi-output model
    model = MultiOutputRegressor(
        xgb.XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
        )
    )

    print(f"Training on {len(X_train)} samples...")
    model.fit(X_train, Y_train)

    # Evaluate
    Y_pred = model.predict(X_test)

    for i, col in enumerate(Y.columns):
        r2 = r2_score(Y_test.iloc[:, i], Y_pred[:, i])
        rmse = np.sqrt(mean_squared_error(Y_test.iloc[:, i], Y_pred[:, i]))
        print(f"{col}: R²={r2:.4f}, RMSE={rmse:.6f}")

    return model, X_test, Y_test, Y_pred

# Step 5: Run training
model, X_test, Y_test, Y_pred = train_bqx_predictor('eurusd')
```

---

## Evaluation Metrics

### Regression Metrics

**1. R² Score** (Coefficient of Determination)
```python
from sklearn.metrics import r2_score

for horizon in [15, 30, 45, 60, 75]:
    r2 = r2_score(Y_test[f'bqx_w{horizon}_ahead'],
                   Y_pred[:, horizons.index(horizon)])
    print(f"w{horizon} R² = {r2:.4f}")

Interpretation:
  R² > 0.5: Good predictive power
  R² > 0.3: Moderate predictive power
  R² < 0.1: Weak predictive power
```

**2. RMSE** (Root Mean Squared Error)
```python
from sklearn.metrics import mean_squared_error

for horizon in [15, 30, 45, 60, 75]:
    rmse = np.sqrt(mean_squared_error(
        Y_test[f'bqx_w{horizon}_ahead'],
        Y_pred[:, horizons.index(horizon)]
    ))
    print(f"w{horizon} RMSE = {rmse:.6f}")

Interpretation:
  Lower is better
  Compare to std(Y_test) as baseline
```

**3. Directional Accuracy**
```python
def directional_accuracy(y_true, y_pred):
    """% of times sign is correct"""
    return np.mean(np.sign(y_true) == np.sign(y_pred))

for horizon in [15, 30, 45, 60, 75]:
    acc = directional_accuracy(
        Y_test[f'bqx_w{horizon}_ahead'],
        Y_pred[:, horizons.index(horizon)]
    )
    print(f"w{horizon} Directional Accuracy = {acc:.2%}")

Interpretation:
  > 50%: Better than random
  > 60%: Good signal
  > 70%: Excellent signal
```

### Trading-Specific Metrics

**4. Sharpe Ratio** (if used for trading)
```python
def trading_sharpe(y_true, y_pred, threshold=0.0005):
    """Sharpe ratio of strategy based on predictions"""
    # Trade when prediction exceeds threshold
    signals = np.where(y_pred > threshold, -1,  # Short (pred decline)
                 np.where(y_pred < -threshold, 1,  # Long (pred increase)
                 0))  # No trade

    # Returns = actual_return * signal
    returns = y_true * signals

    # Sharpe = mean / std * sqrt(periods)
    sharpe = np.mean(returns) / np.std(returns) * np.sqrt(365 * 24 * 60 / 60)
    return sharpe

sharpe = trading_sharpe(Y_test['bqx_w60_ahead'], Y_pred[:, 3])
print(f"Trading Sharpe (w60): {sharpe:.2f}")
```

---

## Implementation Plan

### Phase 1: Prototype (Week 1)

**Deliverables**:
1. Data pipeline for time-aligned features/targets
2. Simple baseline model (single horizon w60)
3. Evaluation framework

**Tasks**:
- [ ] Write SQL queries to extract BQX, REG data
- [ ] Implement time-shifting for targets
- [ ] Create train/test split (time-based)
- [ ] Train baseline XGBoost model (w60 only)
- [ ] Calculate R², RMSE, directional accuracy
- [ ] Document baseline results

**Success Criteria**:
- R² > 0.2 on test set (w60 prediction)
- Directional accuracy > 55%
- Pipeline runs end-to-end

---

### Phase 2: Multi-Horizon Models (Week 2)

**Deliverables**:
1. Multi-output model for all 5 horizons
2. Feature engineering pipeline
3. Cross-validation framework

**Tasks**:
- [ ] Implement multi-output XGBoost wrapper
- [ ] Add autoregressive features (lagged BQX)
- [ ] Add derived features (acceleration, volatility regime)
- [ ] Implement walk-forward cross-validation
- [ ] Compare multi-output vs separate models
- [ ] Tune hyperparameters (grid search)

**Success Criteria**:
- All 5 horizons R² > 0.15
- Shorter horizons (w15, w30) R² > longer ones
- Consistent performance across CV folds

---

### Phase 3: Advanced Features (Week 3)

**Deliverables**:
1. Extended feature set (20+ features)
2. Feature importance analysis
3. Model interpretability report

**Tasks**:
- [ ] Add cross-window features (momentum divergence)
- [ ] Add multi-timeframe alignment features
- [ ] Add volatility regime indicators
- [ ] Run feature importance analysis (SHAP values)
- [ ] Remove low-importance features
- [ ] Document feature engineering rationale

**Success Criteria**:
- Improvement over baseline (ΔR² > 0.05)
- Feature importance makes economic sense
- Top 10 features account for 80%+ importance

---

### Phase 4: Production Pipeline (Week 4)

**Deliverables**:
1. Automated retraining pipeline
2. Real-time prediction service
3. Monitoring dashboard

**Tasks**:
- [ ] Create daily retraining script
- [ ] Build prediction API endpoint
- [ ] Implement model versioning
- [ ] Create performance monitoring dashboard
- [ ] Set up alerts for model degradation
- [ ] Document deployment procedure

**Success Criteria**:
- Predictions available < 100ms latency
- Model retrains daily on new data
- Monitoring tracks R², accuracy, drift
- Alert system functional

---

## Comparison: BQX Strategy vs FWD Strategy

| Aspect | FWD Strategy | BQX Strategy |
|--------|--------------|--------------|
| **Target** | FWD_t (future movement) | BQX_{t+60} (future momentum) |
| **Validation** | One-time check | Continuous (observable) |
| **Autoregression** | ❌ Cannot use FWD_t | ✅ Can use BQX_t |
| **Horizons** | 6 (60-630 min) | 5 (15-75 min) |
| **Granularity** | Coarse (60 min steps) | Fine (15 min steps) |
| **Interpretability** | "Predict future" | "Predict momentum" |
| **Feature Alignment** | Backward → Forward | Backward → Backward |
| **Momentum Capture** | Indirect | Direct |
| **Implementation** | Standard regression | Autoregressive time series |

---

## Recommended Strategy

### ✅ **ADOPT BQX-BASED PREDICTION STRATEGY**

**Rationale**:

1. **Mathematically Equivalent** to FWD but conceptually cleaner
2. **Autoregressive** enables momentum persistence modeling
3. **Finer Granularity** (15 min vs 60 min minimum)
4. **Observable Validation** (can check predictions against actual BQX later)
5. **Feature-Target Consistency** (all are cumulative returns)
6. **Multiple Horizons** enables ensemble modeling

### Recommended Architecture

**Hierarchical Multi-Horizon Model**:

```
Level 1: Predict BQX_{t+15} from current features
    ↓
Level 2: Predict BQX_{t+30} using (features + pred_15)
    ↓
Level 3: Predict BQX_{t+45} using (features + pred_15 + pred_30)
    ↓
Level 4: Predict BQX_{t+60} using (features + pred_15 + pred_30 + pred_45)
    ↓
Level 5: Predict BQX_{t+75} using (features + all previous)
```

**Benefits**:
- Captures cascading uncertainty
- Short-term predictions inform long-term
- Natural progression from near to far future

### Feature Set

**Core Features** (15 features):
1. Current BQX (5): w15, w30, w45, w60, w75
2. Lagged BQX (3): w60 at t-60, t-120, t-180
3. Volatility (2): w15_stdev, agg_volatility
4. REG (3): w60_quad_norm, w60_r2, w240_quad_norm
5. Derived (2): momentum_accel, vol_regime

**Extended Features** (add if helpful):
- Multi-timeframe alignment score
- Cross-window momentum divergence
- Range-based features (max - min)

### Training Approach

1. **Data**: Last 12 months of M1 data
2. **Split**: 80% train, 20% test (time-based)
3. **Model**: XGBoost MultiOutputRegressor
4. **Validation**: Walk-forward cross-validation (5 folds)
5. **Retraining**: Daily with rolling 12-month window
6. **Monitoring**: Track R² and directional accuracy daily

---

## Next Steps

### Immediate Actions

1. **Create BQX tables** (prerequisite)
   - Generate SQL DDL for 28 pairs
   - Populate historical data

2. **Build data pipeline**
   - Extract BQX + REG data
   - Implement time-shifting
   - Create feature/target DataFrames

3. **Train baseline model**
   - Single horizon (w60)
   - Simple feature set
   - Establish performance baseline

4. **Evaluate and iterate**
   - Measure R², RMSE, directional accuracy
   - Add features incrementally
   - Compare multi-horizon strategies

### Success Metrics

**Minimum Viable**:
- R² > 0.20 for w60 prediction
- Directional accuracy > 55%
- Pipeline runs reliably

**Target Performance**:
- R² > 0.30 for short horizons (w15, w30)
- R² > 0.20 for medium horizons (w45, w60, w75)
- Directional accuracy > 60%

**Stretch Goal**:
- R² > 0.40 for any horizon
- Directional accuracy > 65%
- Trading Sharpe > 1.5

---

## Conclusion

The shift from FWD-based to BQX-based prediction is a **strategic improvement** that:

1. ✅ Maintains mathematical equivalence to FWD predictions
2. ✅ Enables autoregressive momentum modeling
3. ✅ Provides finer prediction granularity (15-min vs 60-min)
4. ✅ Creates observable validation framework
5. ✅ Aligns features and targets conceptually

**Recommendation**: **STRONGLY APPROVE** refactoring to BQX-based strategy

**Estimated Timeline**: 4 weeks from BQX table creation to production deployment

**Expected Impact**:
- Improved short-term prediction accuracy
- Better momentum capture
- More actionable trading signals

---

**Analysis Complete**: BQX-based ML strategy is superior to FWD-based approach for autoregressive momentum modeling.
