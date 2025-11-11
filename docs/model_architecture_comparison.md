# Model Architecture Comparison: Per-Pair vs Unified Multi-Pair

**Date:** 2025-11-10
**Purpose:** Explain the fundamental difference between current per-pair model approach and unified multi-pair model architecture

---

## TL;DR: Key Differences

| Aspect | Per-Pair Model (Current) | Unified Multi-Pair Model |
|--------|-------------------------|--------------------------|
| **Number of models** | 28 separate models | 1 single model |
| **Training data** | One pair only (e.g., EURUSD) | All 28 pairs combined |
| **Model sees** | Only EURUSD patterns | Patterns across all pairs |
| **Deployment** | 28 models to deploy | 1 model to deploy |
| **Rate scale issue** | Not a problem | Problem (needs rate_index) |
| **Knowledge sharing** | None (each model independent) | Yes (learns cross-pair patterns) |
| **Specialization** | High (pair-specific) | Lower (generalized) |

---

## Current Approach: Per-Pair Models

### Architecture Overview

**Concept:** Train a separate, independent model for each forex pair.

**Example:**
```
Model 1: EURUSD Predictor
  - Trained only on EURUSD data
  - Input: EURUSD features
  - Output: EURUSD future return

Model 2: USDJPY Predictor
  - Trained only on USDJPY data
  - Input: USDJPY features
  - Output: USDJPY future return

...

Model 28: NZDUSD Predictor
  - Trained only on NZDUSD data
  - Input: NZDUSD features
  - Output: NZDUSD future return
```

### Training Process

**Step 1: Extract data for EURUSD**
```python
# Load EURUSD materialized view
query = """
SELECT
    ts_utc,
    target_rate,                    # EURUSD rate (~1.05-1.15)
    target_w15_bqx_return,          # EURUSD 15-min return
    target_w15_bqx_max_pct,         # EURUSD max deviation
    euraud_w15_bqx_return,          # EURAUD feature
    gbpusd_w15_bqx_return,          # GBPUSD feature
    -- ... 12 EUR/USD related pairs
FROM bqx_ml.features_eurusd
WHERE ts_utc >= '2024-07-01'
"""

df_eurusd = pd.read_sql(query, conn)
# Shape: (370,000 rows, 794 features) - Only EURUSD timeseries
```

**Step 2: Create target variable**
```python
# Predict 15-minute forward return
df_eurusd['target'] = df_eurusd['target_rate'].pct_change(15).shift(-15)
# Values: -0.02 to +0.02 (percentage)
```

**Step 3: Train EURUSD model**
```python
X_eurusd = df_eurusd[feature_columns]  # (370k, 793)
y_eurusd = df_eurusd['target']         # (370k,)

model_eurusd = Ridge(alpha=1.0)
model_eurusd.fit(X_eurusd, y_eurusd)   # Sees only EURUSD data
```

**Step 4: Repeat for all 28 pairs**
```python
# Train separate model for each pair
models = {}
for pair in ALL_PAIRS:
    X_pair, y_pair = load_data(pair)
    models[pair] = Ridge(alpha=1.0)
    models[pair].fit(X_pair, y_pair)

# Result: 28 independent models
```

### Prediction at Runtime

```python
# To predict EURUSD:
eurusd_features = get_current_features('eurusd')  # Shape: (1, 793)
eurusd_prediction = models['eurusd'].predict(eurusd_features)
# Output: 0.0015 (0.15% predicted return)

# To predict USDJPY:
usdjpy_features = get_current_features('usdjpy')  # Shape: (1, 793)
usdjpy_prediction = models['usdjpy'].predict(usdjpy_features)
# Output: 0.0012 (0.12% predicted return)

# Each model independent, no knowledge sharing
```

### Characteristics

**Pros:**
- ✅ **Simple architecture** - Standard regression/ML workflow
- ✅ **Pair-specific learning** - Captures unique patterns per pair
- ✅ **No scale issues** - EURUSD model only sees EURUSD rates
- ✅ **Easy debugging** - Isolate issues to specific pair
- ✅ **Parallel training** - Can train all 28 models simultaneously
- ✅ **Independent updates** - Retrain one pair without affecting others

**Cons:**
- ❌ **Limited training data** - Each model sees only ~370k rows
- ❌ **No knowledge transfer** - Can't learn from correlated pairs
- ❌ **Maintenance overhead** - Must deploy/monitor 28 models
- ❌ **Cold start problem** - New pairs need separate training
- ❌ **Redundant patterns** - Models relearn similar dynamics

**When to use:**
- Starting point for baseline models
- Pairs have unique, non-transferable patterns
- Computational resources not a constraint
- Want maximum specialization per pair

---

## Alternative Approach: Unified Multi-Pair Model

### Architecture Overview

**Concept:** Train a single model that handles all forex pairs simultaneously.

**Example:**
```
Model: Universal Forex Predictor
  - Trained on ALL 28 pairs combined
  - Input: Features + pair identifier
  - Output: Future return (for any pair)
```

### Training Process

**Step 1: Combine data from all pairs**
```python
# Load all 28 materialized views
data_frames = []

for pair in ALL_PAIRS:
    query = f"""
    SELECT
        '{pair}' as pair_id,             # NEW: Pair identifier
        ts_utc,
        target_rate,                      # Different scales!
        target_w15_bqx_return,
        target_w15_bqx_max_pct,
        -- ... all features
    FROM bqx_ml.features_{pair}
    WHERE ts_utc >= '2024-07-01'
    """
    df = pd.read_sql(query, conn)
    data_frames.append(df)

# Combine all pairs
df_all = pd.concat(data_frames, ignore_index=True)
# Shape: (10,360,000 rows, 794 features)
#        28 pairs × 370k rows each
```

**Step 2: Handle pair identity**
```python
# Option A: One-hot encoding
df_all = pd.get_dummies(df_all, columns=['pair_id'])
# Creates 28 binary columns: pair_id_eurusd, pair_id_usdjpy, ...

# Option B: Embedding (neural networks)
pair_embedding = Embedding(input_dim=28, output_dim=8)
# Learns 8-dimensional representation of each pair
```

**Step 3: Handle rate scale problem**
```python
# Problem: Different pairs have different rate scales
# EURUSD rates: 1.05-1.15 (range ~0.10)
# USDJPY rates: 135-145 (range ~10)

# Solution 1: Add rate_index
df_all['target_rate_index'] = df_all.groupby('pair_id')['target_rate'].transform(
    lambda x: (x / x.iloc[0]) * 100
)
# Now all pairs: 95-105 scale

# Solution 2: Normalize per-pair
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
df_all['target_rate_scaled'] = df_all.groupby('pair_id')['target_rate'].transform(
    lambda x: scaler.fit_transform(x.values.reshape(-1, 1)).flatten()
)
```

**Step 4: Train unified model**
```python
# All pairs in single dataset
X_all = df_all[feature_columns + pair_encoding_columns]  # (10.36M, 821)
y_all = df_all['target']                                  # (10.36M,)

# Single model sees all pairs
model_unified = Ridge(alpha=1.0)
model_unified.fit(X_all, y_all)  # Learns from all 28 pairs simultaneously
```

### Prediction at Runtime

```python
# To predict EURUSD:
eurusd_features = get_current_features('eurusd')  # Shape: (1, 793)
eurusd_encoded = encode_pair('eurusd')            # Shape: (1, 28) one-hot
eurusd_input = np.concatenate([eurusd_features, eurusd_encoded], axis=1)
eurusd_prediction = model_unified.predict(eurusd_input)
# Output: 0.0015 (0.15% predicted return)

# To predict USDJPY:
usdjpy_features = get_current_features('usdjpy')
usdjpy_encoded = encode_pair('usdjpy')
usdjpy_input = np.concatenate([usdjpy_features, usdjpy_encoded], axis=1)
usdjpy_prediction = model_unified.predict(usdjpy_input)
# Output: 0.0012 (0.12% predicted return)

# Same model, different pair encodings
```

### Characteristics

**Pros:**
- ✅ **More training data** - 10.36M rows (28× more than per-pair)
- ✅ **Knowledge sharing** - Learns patterns across correlated pairs
- ✅ **Single deployment** - One model to deploy/monitor
- ✅ **Transfer learning** - Can predict new pairs with minimal training
- ✅ **Unified updates** - One retraining process
- ✅ **Cross-pair insights** - Can learn "when USD strong, all *USD pairs move similarly"

**Cons:**
- ❌ **Complex architecture** - Requires pair embeddings or encoding
- ❌ **Scale normalization required** - Need rate_index or standardization
- ❌ **Less specialization** - May miss pair-specific patterns
- ❌ **Larger model size** - More parameters to learn
- ❌ **Debugging harder** - Errors affect all pairs
- ❌ **Training time** - Longer to train on 10M+ rows

**When to use:**
- Want to leverage cross-pair correlations
- Have limited data per pair
- Want to predict new/exotic pairs
- Prefer single deployment
- Building production system at scale

---

## Concrete Example: Linear Regression

### Per-Pair Model (Current)

**Training EURUSD:**
```python
# EURUSD data only
X_eurusd = np.array([
    [1.0700, 0.0012, 0.0008, ...],  # Row 1: 2024-07-01 00:00
    [1.0705, 0.0015, 0.0010, ...],  # Row 2: 2024-07-01 00:01
    [1.0710, 0.0009, 0.0007, ...],  # Row 3: 2024-07-01 00:02
    # ... 369,997 more rows
])  # Shape: (370,000, 793)

y_eurusd = np.array([0.0015, 0.0012, 0.0018, ...])  # Shape: (370,000,)

# Train EURUSD-specific model
model_eurusd = LinearRegression()
model_eurusd.fit(X_eurusd, y_eurusd)

# Learned coefficients (example):
# coef_target_w15_bqx_return = 0.45
# "1% increase in bqx_return → 0.45% increase in future return"
# Only valid for EURUSD!
```

**Training USDJPY:**
```python
# USDJPY data only (completely separate)
X_usdjpy = np.array([
    [140.00, 0.0012, 0.0008, ...],  # Row 1: 2024-07-01 00:00
    [140.14, 0.0015, 0.0010, ...],  # Row 2: 2024-07-01 00:01
    [140.20, 0.0009, 0.0007, ...],  # Row 3: 2024-07-01 00:02
    # ... 369,997 more rows
])  # Shape: (370,000, 793)

y_usdjpy = np.array([0.0012, 0.0010, 0.0015, ...])  # Shape: (370,000,)

# Train USDJPY-specific model
model_usdjpy = LinearRegression()
model_usdjpy.fit(X_usdjpy, y_usdjpy)

# Learned coefficients (example):
# coef_target_w15_bqx_return = 0.38
# Different from EURUSD! Each pair learns independently.
```

**Prediction:**
```python
# Predict EURUSD
eurusd_features = np.array([[1.0720, 0.0018, 0.0012, ...]])
eurusd_pred = model_eurusd.predict(eurusd_features)
# Output: 0.0016

# Predict USDJPY
usdjpy_features = np.array([[141.00, 0.0018, 0.0012, ...]])
usdjpy_pred = model_usdjpy.predict(usdjpy_features)
# Output: 0.0014

# Different models, independent predictions
```

---

### Unified Multi-Pair Model

**Training ALL pairs together:**
```python
# Combined data from all 28 pairs
X_all = np.array([
    # EURUSD data (370k rows)
    [1.0700, 0.0012, 0.0008, ..., 1, 0, 0, ..., 0],  # EURUSD encoding
    [1.0705, 0.0015, 0.0010, ..., 1, 0, 0, ..., 0],
    [1.0710, 0.0009, 0.0007, ..., 1, 0, 0, ..., 0],

    # USDJPY data (370k rows)
    [140.00, 0.0012, 0.0008, ..., 0, 1, 0, ..., 0],  # USDJPY encoding
    [140.14, 0.0015, 0.0010, ..., 0, 1, 0, ..., 0],
    [140.20, 0.0009, 0.0007, ..., 0, 1, 0, ..., 0],

    # ... 26 more pairs (9.62M more rows)
])  # Shape: (10,360,000, 821)
#              793 features + 28 pair encodings

y_all = np.array([
    0.0015, 0.0012, 0.0018,  # EURUSD targets
    0.0012, 0.0010, 0.0015,  # USDJPY targets
    # ... targets for all 28 pairs
])  # Shape: (10,360,000,)

# Train single unified model
model_unified = LinearRegression()
model_unified.fit(X_all, y_all)

# Learned coefficients (example):
# coef_target_w15_bqx_return = 0.41
# "On average across all pairs, 1% increase in bqx_return → 0.41% future return"
# Applies to all pairs, but modified by pair encoding!
```

**Prediction:**
```python
# Predict EURUSD
eurusd_features = np.array([[1.0720, 0.0018, 0.0012, ..., 1, 0, 0, ..., 0]])
#                                                            ^ EURUSD encoding
eurusd_pred = model_unified.predict(eurusd_features)
# Output: 0.0016

# Predict USDJPY (same model!)
usdjpy_features = np.array([[141.00, 0.0018, 0.0012, ..., 0, 1, 0, ..., 0]])
#                                                            ^ USDJPY encoding
usdjpy_pred = model_unified.predict(usdjpy_features)
# Output: 0.0014

# Same model, different pair encodings modify predictions
```

---

## Why Rate Scale Matters in Unified Model

### Problem Demonstration

**Without rate normalization:**
```python
# Training data (simplified)
X_all = np.array([
    [1.0700, 0.0012],  # EURUSD: rate=1.07, return=0.12%
    [1.0705, 0.0015],  # EURUSD: rate=1.07, return=0.15%
    [140.00, 0.0012],  # USDJPY: rate=140, return=0.12% (same return!)
    [140.50, 0.0015],  # USDJPY: rate=140, return=0.15% (same return!)
])

# Model learns coefficient for 'rate' column
# Problem: USDJPY rates dominate due to scale (140 >> 1.07)
# Gradient descent: ∂Loss/∂coef_rate is 127× larger for USDJPY rows!
# Model incorrectly learns: "rate is very important for USDJPY, not for EURUSD"
# Reality: Both pairs have same relationship, just different scales
```

**With rate_index normalization:**
```python
# Training data (simplified)
X_all = np.array([
    [100.00, 0.0012],  # EURUSD: rate_index=100, return=0.12%
    [100.47, 0.0015],  # EURUSD: rate_index=100.47, return=0.15%
    [100.00, 0.0012],  # USDJPY: rate_index=100, return=0.12% (same return!)
    [100.36, 0.0015],  # USDJPY: rate_index=100.36, return=0.15% (same return!)
])

# Now model learns consistent coefficient for 'rate_index'
# All pairs on same scale (95-105)
# Gradient descent treats all pairs equally
# Model correctly learns: "rate_index matters equally for all pairs"
```

---

## Neural Network Example

### Per-Pair Model

```python
# Separate neural network for EURUSD
model_eurusd = Sequential([
    Dense(64, activation='relu', input_shape=(793,)),
    Dense(32, activation='relu'),
    Dense(16, activation='relu'),
    Dense(1)  # Output: future return
])

model_eurusd.compile(optimizer='adam', loss='mse')
model_eurusd.fit(X_eurusd, y_eurusd, epochs=50, batch_size=32)

# Repeat for all 28 pairs (28 separate networks)
```

### Unified Multi-Pair Model

```python
# Single neural network for all pairs with embedding
from tensorflow.keras.layers import Input, Embedding, Concatenate, Dense

# Input layers
features_input = Input(shape=(793,), name='features')
pair_input = Input(shape=(1,), name='pair_id', dtype='int32')

# Pair embedding (learns 8D representation of each pair)
pair_embedding = Embedding(input_dim=28, output_dim=8)(pair_input)
pair_embedding = Flatten()(pair_embedding)

# Concatenate features + pair embedding
combined = Concatenate()([features_input, pair_embedding])

# Shared layers
x = Dense(64, activation='relu')(combined)
x = Dense(32, activation='relu')(x)
x = Dense(16, activation='relu')(x)
output = Dense(1)(x)  # Output: future return

model_unified = Model(inputs=[features_input, pair_input], outputs=output)
model_unified.compile(optimizer='adam', loss='mse')

# Train on all pairs
model_unified.fit(
    [X_all_features, X_all_pair_ids],  # Combined inputs
    y_all,
    epochs=50,
    batch_size=32
)

# Single network handles all pairs via learned embeddings
```

**Key difference:** Unified model learns that EURUSD, GBPUSD, AUDUSD share "USD" component and may move similarly when USD strengthens/weakens.

---

## Decision Matrix

| Use Case | Recommended Architecture |
|----------|-------------------------|
| **Baseline/initial models** | Per-Pair (simpler, faster to implement) |
| **Production system (28 pairs)** | Per-Pair (easier maintenance) |
| **Limited data per pair (<50k rows)** | Unified (leverage cross-pair data) |
| **Want transfer learning** | Unified (learns generalizable patterns) |
| **Pairs highly correlated** | Unified (shares knowledge) |
| **Pairs independent** | Per-Pair (specialized learning) |
| **Adding new pairs frequently** | Unified (warm-start from existing model) |
| **Maximum performance per pair** | Per-Pair (pair-specific optimization) |

---

## Current Project Recommendation

### Why Per-Pair is Better for Your Project

1. **You have sufficient data**
   - 370k rows per pair (1 year × 1-min bars)
   - Enough for robust per-pair training

2. **Simpler implementation**
   - Standard scikit-learn/XGBoost workflow
   - No pair encoding complexity
   - No rate_index required

3. **Easier debugging**
   - Isolate poor performance to specific pair
   - Inspect pair-specific feature importance
   - Retrain without affecting others

4. **Parallel deployment**
   - 28 models can run independently
   - If one fails, others unaffected
   - Can gradually roll out improvements

5. **Baseline establishment**
   - Start with per-pair to establish baseline
   - Measure performance per pair
   - Later experiment with unified if needed

### When to Revisit Unified Model

Consider switching to unified model if:
- Per-pair models show similar patterns (redundant learning)
- Want to add 50+ pairs (deployment becomes expensive)
- Limited data for new/exotic pairs
- Need to predict cross-pair relationships
- Building research platform for experiments

---

## Summary Table

| Feature | Per-Pair (Current) | Unified Multi-Pair |
|---------|-------------------|-------------------|
| **Models** | 28 separate | 1 combined |
| **Training data per model** | 370k rows | 10.36M rows |
| **Training time** | Fast (parallel) | Slow (sequential) |
| **Deployment** | 28 endpoints | 1 endpoint |
| **Maintenance** | 28× work | 1× work |
| **Specialization** | High | Medium |
| **Knowledge sharing** | None | High |
| **Rate_index needed?** | No | Yes |
| **Cold start (new pair)** | Need full training | Can transfer learn |
| **Debugging** | Easy (isolated) | Hard (entangled) |
| **Best for** | Baseline, production | Research, limited data |

---

**Current Recommendation:** Proceed with **per-pair models** using current percentage-normalized features. No rate_index needed.

**Future Enhancement:** Experiment with **unified model** after establishing per-pair baseline to measure if knowledge sharing improves performance.

---

**Document Date:** 2025-11-10
**Status:** Per-pair architecture recommended for initial implementation
**Rate Indexing:** Not required for per-pair models
