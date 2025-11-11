# BQX ML Major Refactor: Unified Model with Index-Based Features

**Date:** 2025-11-10
**Status:** Planning Phase - Architectural Analysis
**Scope:** Complete pipeline refactor from source data through modeling

---

## TL;DR: What's Changing

| Aspect | Current (Per-Pair) | Proposed (Unified Index-Based) |
|--------|-------------------|-------------------------------|
| **Base data** | Absolute forex rates | Forex rate indexes (base-100) |
| **BQX calculation** | From absolute rates | From index values |
| **Normalization** | Post-hoc (_pct fields) | Built-in (index already normalized) |
| **Model architecture** | 28 separate models | 1 unified model |
| **Prediction target** | Future forex rate | Future BQX value (i+60) |
| **Tables affected** | MVs only | M1, BQX, MVs (entire pipeline) |

---

## User Requirements

### 1. Unified Multi-Pair Model
- **Single model** handles all 28 forex pairs
- Uses pair embeddings or encodings
- Shares knowledge across correlated pairs

### 2. Predict Future BQX Values (i+60)
- **Target:** BQX metrics 60 minutes ahead
- **Example:** Predict `w15_bqx_return` at t+60
- **Not:** Predict future forex rate

### 3. Convert Forex Rates to Indexes
- **Baseline date:** 2024-07-01 00:00 UTC
- **Formula:** index = (rate / baseline_rate) × 100
- **Applies to:** All 28 pairs

### 4. Recalculate All Tables Using Indexes
- **M1 tables:** Add index column
- **BQX tables:** Recalculate from index values
- **Formulas:** Simplified (no division by rate needed)

---

## Rationale: Why This Approach?

### Problem with Current Approach

**1. Scale Mismatch in Unified Model**
```python
# Current: Absolute rates
EURUSD: rate = 1.0700  (scale ~1)
USDJPY: rate = 140.00  (scale ~140)  # 127× larger!

# Unified model struggles:
# - Gradients dominated by USDJPY
# - Feature importance distorted
# - Hard to learn shared patterns
```

**2. Redundant Normalization**
```python
# Current: Calculate absolute, then normalize
bqx_max = np.max(past_rates)  # Absolute value
bqx_max_pct = (bqx_max - rate) / rate  # Then normalize

# Problem: Two-step process, storage redundancy
```

**3. Per-Pair Models Don't Share Knowledge**
```python
# Current: 28 independent models
# EURUSD model learns: "When EUR strong, EURUSD rises"
# GBPUSD model independently learns: "When USD weak, GBPUSD rises"
# Reality: These are the same pattern (USD weakness)!
```

### Solution: Index-Based Unified Model

**1. Uniform Scale from Start**
```python
# Proposed: Index values
EURUSD: index = 100.47  (scale 95-105)
USDJPY: index = 100.36  (scale 95-105)  # Same scale!

# Unified model benefits:
# - Equal gradients across pairs
# - Fair feature importance
# - Learns shared patterns easily
```

**2. Simplified Calculation**
```python
# Proposed: Calculate on index directly
bqx_max_index = np.max(past_indexes)  # Already normalized scale
# No second normalization step needed
# All pairs comparable by design
```

**3. Cross-Pair Knowledge Sharing**
```python
# Proposed: Single model learns
# "When index rises across USD pairs, USD weakening"
# Applies learning from EURUSD to GBPUSD automatically
# Transfer learning built-in
```

---

## Architectural Changes

### Phase 1: Source Data Conversion (M1 Tables)

#### Current M1 Structure
```sql
-- bqx.m1_eurusd
time         | close (rate)
-------------|-------------
2024-07-01   | 1.0700
2024-07-02   | 1.0750
2024-07-03   | 1.0650
```

#### Proposed M1 Structure
```sql
-- bqx.m1_eurusd (add index column)
time         | close (rate) | rate_index | baseline_rate
-------------|--------------|-----------|---------------
2024-07-01   | 1.0700       | 100.00    | 1.0700
2024-07-02   | 1.0750       | 100.47    | 1.0700
2024-07-03   | 1.0650       |  99.53    | 1.0700
```

**Implementation:**
```sql
-- Add baseline_rates reference table
CREATE TABLE bqx.baseline_rates (
    pair VARCHAR(10) PRIMARY KEY,
    baseline_rate DOUBLE PRECISION NOT NULL,
    baseline_ts TIMESTAMPTZ NOT NULL
);

-- Populate baselines (2024-07-01)
INSERT INTO bqx.baseline_rates
SELECT
    'eurusd' as pair,
    close as baseline_rate,
    time as baseline_ts
FROM bqx.m1_eurusd
WHERE time >= '2024-07-01 00:00:00+00'
ORDER BY time ASC
LIMIT 1;
-- Repeat for all 28 pairs

-- Add rate_index column to M1 tables
ALTER TABLE bqx.m1_eurusd ADD COLUMN rate_index DOUBLE PRECISION;

-- Calculate index values
UPDATE bqx.m1_eurusd
SET rate_index = (close / (SELECT baseline_rate FROM bqx.baseline_rates WHERE pair = 'eurusd')) * 100;

-- Add index for performance
CREATE INDEX idx_m1_eurusd_rate_index ON bqx.m1_eurusd(rate_index);
```

---

### Phase 2: BQX Formula Refactor

#### Current BQX Formulas (Absolute Rate)

```python
def compute_backward_metrics(rates, window_size, current_idx):
    """Current implementation using absolute rates"""
    rate_t = rates[current_idx]  # e.g., 1.0700 or 140.00
    past_rates = rates[current_idx - window_size : current_idx]

    # Cumulative return (NORMALIZED by rate_t)
    cumulative_diffs = past_rates - rate_t
    bqx_return = np.sum(cumulative_diffs) / rate_t  # ✅ Already normalized

    # Statistical measures (NOT NORMALIZED)
    bqx_max = np.max(past_rates)      # ❌ Absolute: 1.0710 or 140.50
    bqx_min = np.min(past_rates)      # ❌ Absolute: 1.0695 or 139.88
    bqx_avg = np.mean(past_rates)     # ❌ Absolute: 1.0702 or 140.14
    bqx_stdev = np.std(past_rates)    # ❌ Absolute: 0.0005 or 0.20

    # Endpoint return (NORMALIZED by rate_t)
    bqx_endpoint = (past_rates[0] - rate_t) / rate_t  # ✅ Already normalized

    return {
        "bqx_return": float(bqx_return),       # ✅ Normalized
        "bqx_max": float(bqx_max),             # ❌ NOT normalized
        "bqx_min": float(bqx_min),             # ❌ NOT normalized
        "bqx_avg": float(bqx_avg),             # ❌ NOT normalized
        "bqx_stdev": float(bqx_stdev),         # ❌ NOT normalized
        "bqx_endpoint": float(bqx_endpoint),   # ✅ Normalized
    }
```

#### Proposed BQX Formulas (Index)

```python
def compute_backward_metrics_index(indexes, window_size, current_idx):
    """Proposed implementation using index values"""
    index_t = indexes[current_idx]  # e.g., 100.47 for both EURUSD and USDJPY
    past_indexes = indexes[current_idx - window_size : current_idx]

    # Cumulative return (same formula, but on index scale)
    cumulative_diffs = past_indexes - index_t
    bqx_return = np.sum(cumulative_diffs) / index_t  # ✅ Still normalized

    # Statistical measures (NOW ON COMPARABLE SCALE)
    bqx_max = np.max(past_indexes)    # ✅ Comparable: 100.65 for both pairs
    bqx_min = np.min(past_indexes)    # ✅ Comparable: 100.32 for both pairs
    bqx_avg = np.mean(past_indexes)   # ✅ Comparable: 100.48 for both pairs
    bqx_stdev = np.std(past_indexes)  # ✅ Comparable: 0.12 for both pairs

    # Endpoint return (same formula)
    bqx_endpoint = (past_indexes[0] - index_t) / index_t  # ✅ Still normalized

    return {
        "bqx_return": float(bqx_return),       # ✅ Normalized
        "bqx_max": float(bqx_max),             # ✅ NOW comparable across pairs!
        "bqx_min": float(bqx_min),             # ✅ NOW comparable across pairs!
        "bqx_avg": float(bqx_avg),             # ✅ NOW comparable across pairs!
        "bqx_stdev": float(bqx_stdev),         # ✅ NOW comparable across pairs!
        "bqx_endpoint": float(bqx_endpoint),   # ✅ Normalized
    }
```

**Key Changes:**
1. Input `rates` → `indexes`
2. `rate_t` → `index_t`
3. `past_rates` → `past_indexes`
4. **Formula structure unchanged** (division by current value still needed)
5. **Output values now comparable across all pairs**

#### What About Aggregate Features?

```python
def compute_aggregate_metrics_index(indexes, current_idx):
    """Aggregate metrics on index scale"""
    index_t = indexes[current_idx]
    past_indexes = indexes[current_idx - 75 : current_idx]

    # Cumulative return
    cumulative_diffs = past_indexes - index_t
    agg_bqx_return = np.sum(cumulative_diffs) / index_t

    # Statistical measures (comparable scale)
    agg_bqx_max = np.max(past_indexes)
    agg_bqx_min = np.min(past_indexes)
    agg_bqx_avg = np.mean(past_indexes)
    agg_bqx_stdev = np.std(past_indexes)

    # Range and volatility (FORMULAS SIMPLIFY!)
    # OLD: agg_bqx_range = (max - min) / rate_t
    # NEW: agg_bqx_range = (max - min) / index_t  # Same formula
    agg_bqx_range = (agg_bqx_max - agg_bqx_min) / index_t

    # OLD: agg_bqx_volatility = stdev / rate_t
    # NEW: agg_bqx_volatility = stdev / index_t  # Same formula
    agg_bqx_volatility = agg_bqx_stdev / index_t

    return {
        "agg_bqx_return": float(agg_bqx_return),
        "agg_bqx_max": float(agg_bqx_max),         # ✅ Comparable
        "agg_bqx_min": float(agg_bqx_min),         # ✅ Comparable
        "agg_bqx_avg": float(agg_bqx_avg),         # ✅ Comparable
        "agg_bqx_stdev": float(agg_bqx_stdev),     # ✅ Comparable
        "agg_bqx_range": float(agg_bqx_range),     # ✅ Normalized
        "agg_bqx_volatility": float(agg_bqx_volatility),  # ✅ Normalized
    }
```

**Important Insight:**
- Formulas **don't actually simplify** much
- We still divide by current value for returns/ranges/volatility
- **Main benefit:** Output values are comparable across pairs without extra normalization

---

### Phase 3: BQX Table Restructure

#### Current BQX Table Structure
```sql
-- bqx.bqx_eurusd
ts_utc       | rate   | w15_bqx_return | w15_bqx_max | w15_bqx_min | ...
-------------|--------|----------------|-------------|-------------|----
2024-07-01   | 1.0700 | 0.0012         | 1.0710      | 1.0695      | ...
2024-07-02   | 1.0750 | 0.0015         | 1.0760      | 1.0740      | ...
```

#### Proposed BQX Table Structure
```sql
-- bqx.bqx_eurusd (index-based)
ts_utc       | rate_index | w15_bqx_return | w15_bqx_max | w15_bqx_min | ...
-------------|------------|----------------|-------------|-------------|----
2024-07-01   | 100.00     | 0.0012         | 100.09      | 99.95       | ...
2024-07-02   | 100.47     | 0.0015         | 100.56      | 100.38      | ...
```

**Changes:**
- `rate` column renamed to `rate_index`
- All BQX metrics (max/min/avg) now index values
- Returns (return, endpoint, range, volatility) still percentages

**Implementation:**

```sql
-- Option A: Drop and recreate (clean slate)
DROP TABLE IF EXISTS bqx.bqx_eurusd CASCADE;

-- Recreate with index-based schema
CREATE TABLE bqx.bqx_eurusd (
    ts_utc TIMESTAMPTZ NOT NULL,
    rate_index DOUBLE PRECISION NOT NULL,  -- Changed from 'rate'
    w15_bqx_return DOUBLE PRECISION,
    w15_bqx_max DOUBLE PRECISION,          -- Now index values
    w15_bqx_min DOUBLE PRECISION,          -- Now index values
    w15_bqx_avg DOUBLE PRECISION,          -- Now index values
    w15_bqx_stdev DOUBLE PRECISION,        -- Now index values
    w15_bqx_endpoint DOUBLE PRECISION,
    -- ... all other windows and aggregate features
    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);

-- Recreate partitions
CREATE TABLE bqx.bqx_eurusd_2024_07 PARTITION OF bqx.bqx_eurusd
FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');
-- ... repeat for all 12 months
```

**Backfill Process:**
1. Update `backward_worker.py` to use index values
2. Run backfill script for all 28 pairs
3. Verify data integrity

---

### Phase 4: Materialized View Refactor

#### Current MV Approach
- 28 separate MVs (one per target pair)
- Currency-filtered features (12-13 pairs per MV)
- Post-hoc normalization (_pct fields)

#### Proposed MV Approach
- **Single unified MV** for all pairs
- **All 28 pairs** included (no currency filtering)
- **No _pct fields** (already normalized by index)

#### Unified MV Structure

```sql
-- bqx_ml.features_unified (single MV for all pairs)
CREATE MATERIALIZED VIEW bqx_ml.features_unified AS
SELECT
    ts_utc,
    pair_id,                          -- NEW: Pair identifier

    -- Current values (index-based)
    rate_index,                       -- e.g., 100.47

    -- Window features (all comparable)
    w15_bqx_return,                   -- Still percentage
    w15_bqx_max,                      -- Now comparable (100.56 vs 100.52)
    w15_bqx_min,                      -- Now comparable (99.95 vs 99.88)
    w15_bqx_avg,                      -- Now comparable (100.23 vs 100.18)
    w15_bqx_stdev,                    -- Now comparable (0.12 vs 0.15)
    w15_bqx_endpoint,                 -- Still percentage

    -- ... all other windows (w30, w45, w60, w75)

    -- Aggregate features
    agg_bqx_return,
    agg_bqx_max,
    agg_bqx_min,
    agg_bqx_avg,
    agg_bqx_stdev,
    agg_bqx_range,
    agg_bqx_volatility,

    -- Features from ALL 28 pairs (flattened)
    eurusd_rate_index,
    eurusd_w15_bqx_return,
    eurusd_w15_bqx_max,
    -- ... all EURUSD features

    usdjpy_rate_index,
    usdjpy_w15_bqx_return,
    usdjpy_w15_bqx_max,
    -- ... all USDJPY features

    -- ... all 28 pairs × 37 features = 1,036 feature columns

FROM (
    -- UNION ALL approach: combine all pairs
    SELECT 'eurusd' as pair_id, * FROM bqx.bqx_eurusd
    UNION ALL
    SELECT 'usdjpy' as pair_id, * FROM bqx.bqx_usdjpy
    UNION ALL
    -- ... all 28 pairs
) all_pairs
-- Cross-join to get features from all pairs at each timestamp
-- Complex SQL, but creates unified feature matrix
```

**Alternative: Wide Format (Simpler)**
```sql
-- bqx_ml.features_unified_wide
CREATE MATERIALIZED VIEW bqx_ml.features_unified_wide AS
SELECT
    e.ts_utc,

    -- EURUSD features
    e.rate_index as eurusd_rate_index,
    e.w15_bqx_return as eurusd_w15_bqx_return,
    e.w15_bqx_max as eurusd_w15_bqx_max,
    -- ... all EURUSD features

    -- USDJPY features
    u.rate_index as usdjpy_rate_index,
    u.w15_bqx_return as usdjpy_w15_bqx_return,
    u.w15_bqx_max as usdjpy_w15_bqx_max,
    -- ... all USDJPY features

    -- ... all 28 pairs

FROM bqx.bqx_eurusd e
LEFT JOIN bqx.bqx_usdjpy u ON e.ts_utc = u.ts_utc
LEFT JOIN bqx.bqx_gbpusd g ON e.ts_utc = g.ts_utc
-- ... LEFT JOIN all 28 pairs

WHERE e.ts_utc >= '2024-07-01' AND e.ts_utc < '2025-07-01'
  AND e.w75_bqx_return IS NOT NULL;  -- Sufficient lookback

-- Result: Each row = one timestamp with features from ALL 28 pairs
-- Columns: 1 (ts) + 28 pairs × 37 features = 1,037 columns
```

---

### Phase 5: Target Variable Definition

**Critical Decision:** What are we predicting?

#### Option A: Predict Future Index Value (i+60)
```python
# Target: index value 60 minutes ahead
target = rate_index.shift(-60)

# Example:
# Current: index = 100.47
# Target: index at t+60 = 100.65
# Interpretation: "Will index be 100.65 in 60 min?"
```

**Pros:**
- Direct prediction of future state
- Can derive future rate: `rate_future = (index_future / 100) * baseline_rate`
- Absolute target value

**Cons:**
- Doesn't capture relative change (100.47 → 100.65 is different % change than 95.00 → 95.18)
- Model might learn to predict "index usually around 100"

#### Option B: Predict Future Index Return (i+60)
```python
# Target: percentage change over next 60 minutes
target = (rate_index.shift(-60) - rate_index) / rate_index

# Example:
# Current: index = 100.47
# Future: index at t+60 = 100.65
# Target: (100.65 - 100.47) / 100.47 = 0.0018 (0.18%)
# Interpretation: "Will index rise 0.18% in next 60 min?"
```

**Pros:**
- Captures relative change (percentage)
- Comparable across different index levels
- Standard approach for time-series forecasting

**Cons:**
- Need current index to recover future index
- Two-step calculation to get future rate

#### Option C: Predict Future BQX Value (i+60) ← **USER'S STATED PREFERENCE**

```python
# Target: specific BQX metric 60 minutes ahead
# Example: Predict w15_bqx_return at t+60
target = w15_bqx_return.shift(-60)

# Example:
# Current: w15_bqx_return = 0.0012 (0.12%)
# Future: w15_bqx_return at t+60 = 0.0018 (0.18%)
# Target: 0.0018
# Interpretation: "Will 15-min return be 0.18% in 60 min?"
```

**Pros:**
- Directly predicts momentum/pattern continuation
- BQX values already capture market dynamics
- Can predict multiple BQX metrics simultaneously

**Cons:**
- Doesn't directly predict future rate or index
- Harder to interpret for trading decisions
- Need to choose which BQX metric(s) to predict

**Recommendation:** Option B (predict future index return) is most standard and useful for trading.

---

### Phase 6: Unified Model Architecture

#### Model Input Structure

```python
# Training data shape
X_train.shape  # (10,360,000 rows, 1,036 features + 1 pair_id)
#                28 pairs × 370k timestamps
#                Features: 28 pairs × 37 BQX metrics

y_train.shape  # (10,360,000,)
#                Target: future index return (i+60)
```

#### Neural Network Architecture (Recommended)

```python
from tensorflow.keras import Model, Input, Embedding, Concatenate, Dense, Dropout
from tensorflow.keras.layers import BatchNormalization

# Input layers
features_input = Input(shape=(1036,), name='features')  # All BQX features
pair_input = Input(shape=(1,), name='pair_id', dtype='int32')

# Pair embedding (learns 16D representation of each pair)
pair_embedding = Embedding(input_dim=28, output_dim=16, name='pair_embedding')(pair_input)
pair_embedding = Flatten()(pair_embedding)

# Concatenate features + pair embedding
combined = Concatenate()([features_input, pair_embedding])

# Shared encoder layers
x = Dense(512, activation='relu')(combined)
x = BatchNormalization()(x)
x = Dropout(0.3)(x)

x = Dense(256, activation='relu')(x)
x = BatchNormalization()(x)
x = Dropout(0.3)(x)

x = Dense(128, activation='relu')(x)
x = BatchNormalization()(x)
x = Dropout(0.2)(x)

x = Dense(64, activation='relu')(x)
x = BatchNormalization()(x)

# Output layer
output = Dense(1, name='future_return')(x)  # Predict future index return

# Build model
model = Model(inputs=[features_input, pair_input], outputs=output)
model.compile(optimizer='adam', loss='mse', metrics=['mae'])

# Train on all pairs
history = model.fit(
    [X_train_features, X_train_pair_ids],
    y_train,
    validation_split=0.2,
    epochs=50,
    batch_size=1024,
    verbose=1
)
```

**Key Components:**
1. **Pair embedding:** Learns that EURUSD, GBPUSD, AUDUSD share "USD" component
2. **Shared layers:** Learn patterns common across all pairs
3. **Single output:** Predicts future return for any pair

#### Alternative: Gradient Boosting (Simpler)

```python
from xgboost import XGBRegressor

# One-hot encode pair_id
pair_onehot = pd.get_dummies(df['pair_id'], prefix='pair')
X_train = pd.concat([X_train_features, pair_onehot], axis=1)

# Train unified model
model = XGBRegressor(
    n_estimators=1000,
    max_depth=8,
    learning_rate=0.01,
    subsample=0.8,
    colsample_bytree=0.8,
    objective='reg:squarederror'
)

model.fit(
    X_train,
    y_train,
    eval_set=[(X_val, y_val)],
    early_stopping_rounds=50,
    verbose=100
)
```

---

## Implementation Impact Analysis

### Data Volume Changes

| Table | Current Rows | Current Storage | New Rows | New Storage | Change |
|-------|-------------|-----------------|----------|-------------|--------|
| M1 tables (28) | ~10.3M each | ~800 MB each | Same | ~850 MB each | +6% (index col) |
| BQX tables (28) | ~10.3M each | ~5 GB each | Same | Same | 0% (rename col) |
| MVs | 28 MVs × 370k | ~40 GB total | 1 MV × 10.36M | ~50 GB | +25% |

### Processing Time Estimates

| Task | Estimated Time | Notes |
|------|----------------|-------|
| Calculate baselines | 5 minutes | One-time query per pair |
| Update M1 indexes | 2-3 hours | UPDATE on 290M rows |
| Recreate BQX tables | 6-8 hours | Rerun backfill (same as original) |
| Create unified MV | 30-60 minutes | Single large MV creation |
| **Total downtime** | **8-12 hours** | Can do offline |

### Code Changes Required

| File/Script | Changes | Complexity |
|------------|---------|------------|
| `backward_worker.py` | Input: index, formulas unchanged | Low |
| `backward_worker_threaded.py` | Read from M1 index column | Low |
| `create_filtered_feature_mvs.py` | Complete rewrite for unified MV | High |
| `extract_training_data.py` | New script for unified data | Medium |
| `train_baseline.py` | New unified model architecture | High |

---

## Pros and Cons Analysis

### Advantages ✅

1. **Unified Scale from Source**
   - All pairs on 95-105 scale throughout pipeline
   - No post-hoc normalization needed
   - Simpler data flow

2. **Knowledge Sharing**
   - Single model learns cross-pair correlations
   - "USD weakness" pattern applies to all *USD pairs
   - Better generalization

3. **Deployment Simplification**
   - 1 model instead of 28
   - Single endpoint for all predictions
   - Easier monitoring

4. **Transfer Learning**
   - Can add new pairs with minimal retraining
   - Model already knows currency dynamics
   - Warm-start capability

5. **More Training Data**
   - 10.36M rows instead of 370k per model
   - Better statistical power
   - Reduced overfitting risk

### Disadvantages ❌

1. **Complete Pipeline Rebuild**
   - Must recalculate all BQX tables (~8 hours)
   - High risk of errors during migration
   - No easy rollback

2. **Formula Interpretation Changes**
   - bqx_max now index (100.56) not rate (1.0756)
   - May confuse analysis/visualization
   - Documentation must be updated everywhere

3. **Less Pair-Specific Learning**
   - Model might miss unique EURUSD patterns
   - Optimizes for average, not individual pairs
   - May reduce per-pair accuracy

4. **Computational Complexity**
   - Training on 10M rows slower than 370k
   - Larger model size
   - More GPU memory needed

5. **Debugging Difficulty**
   - Errors affect all 28 pairs
   - Harder to isolate pair-specific issues
   - More complex architecture

6. **Baseline Dependency**
   - All predictions relative to 2024-07-01
   - If baseline chosen poorly, affects everything
   - Hard to change later

---

## Risk Assessment

### High Risk Issues

1. **Data Integrity**
   - **Risk:** Errors in index calculation propagate through entire pipeline
   - **Mitigation:** Extensive validation, spot-check all 28 pairs

2. **Formula Bugs**
   - **Risk:** Subtle errors in BQX calculations on index data
   - **Mitigation:** Unit tests, compare subset to current calculation

3. **Model Performance**
   - **Risk:** Unified model performs worse than per-pair models
   - **Mitigation:** Keep per-pair models as baseline, A/B test

### Medium Risk Issues

1. **Training Time**
   - **Risk:** 10M rows too large, training too slow
   - **Mitigation:** Use sampling, gradient accumulation, cloud GPUs

2. **Overfitting**
   - **Risk:** Model memorizes patterns, doesn't generalize
   - **Mitigation:** Strong regularization, dropout, early stopping

3. **Baseline Shift**
   - **Risk:** Market conditions change drastically from 2024-07-01
   - **Mitigation:** Monitor index drift, consider rolling baseline

---

## Alternative: Hybrid Approach

**Compromise:** Index data + Keep per-pair models

1. Convert to index-based BQX tables (benefits: comparable scale)
2. Create per-pair MVs from index data (no unified MV)
3. Train per-pair models on index features (simpler than unified)
4. Later experiment with unified model

**Pros:**
- Gets benefits of index normalization
- Lower risk (keeps proven architecture)
- Easier to implement incrementally

**Cons:**
- Doesn't get knowledge sharing benefits
- Still 28 models to deploy

---

## Recommendation

### Phase 1 (Lower Risk): Index Data + Per-Pair Models
1. Add index columns to M1 tables
2. Recalculate BQX tables using indexes
3. Create per-pair MVs (no _pct fields needed)
4. Train per-pair models on index features
5. **Validate performance matches current approach**

### Phase 2 (Higher Risk): Unified Model
6. Create unified MV combining all pairs
7. Implement unified model architecture
8. A/B test against per-pair baseline
9. If successful, switch to unified deployment

**Rationale:** Incremental migration reduces risk, allows validation at each step

---

## Open Questions

1. **Which BQX metric to predict?**
   - Future index value?
   - Future index return?
   - Future w15_bqx_return?

2. **i+60 horizon only or multiple?**
   - Just 60-min ahead?
   - Or i+15, i+30, i+60, i+120?

3. **Currency filtering in unified model?**
   - Use all 28 pairs' features?
   - Or still filter to relevant currencies?

4. **Baseline update frequency?**
   - Fixed at 2024-07-01 forever?
   - Recalculate monthly/quarterly?

5. **Preserve absolute rate data?**
   - Keep original rate column?
   - Or replace entirely with index?

---

**Status:** Awaiting user confirmation on:
1. Proceed with full refactor vs incremental?
2. Which prediction target (index return recommended)?
3. Risk tolerance for pipeline rebuild
4. Timeline expectations (8-12 hours minimum)

