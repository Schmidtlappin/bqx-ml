# BQX ML Enhancement Stages 2.16-2.19: Complete Implementation Plan

**Date:** 2025-11-16
**Status:** Approved for Implementation
**Purpose:** Achieve "Aggressive and Robust" ML prediction performance
**Expected Impact:** +47% Sharpe Ratio improvement (1.5 → 2.2)

---

## Executive Summary

This document defines four new enhancement stages (2.16-2.19) that implement the Tier 1-4 recommendations from the deep dive analysis. These stages transform the BQX ML system from "excellent" (8/10) to "state-of-the-art aggressive and robust" (9.5/10).

**Performance Trajectory:**
```
Baseline (Current):     R² = 0.82, Directional = 65%, Sharpe = 1.5
+ Stage 2.16:           R² = 0.85, Directional = 70%, Sharpe = 1.75
+ Stage 2.17:           R² = 0.88, Directional = 75%, Sharpe = 2.0
+ Stage 2.18:           R² = 0.90, Directional = 77%, Sharpe = 2.1
+ Stage 2.19:           R² = 0.90 (maintained), Sharpe = 2.2
```

---

## Stage 2.16: Cross-Pair Interaction Features

### Overview

**Tier:** 1 (Highest Priority)
**Duration:** 1 week (40 hours)
**Cost:** $20 (EC2 compute)
**ROI:** +30% performance improvement
**Dependencies:** Stages 2.14 (term covariances), 2.15 (validation complete)

### Rationale

Forex pairs are NOT independent - they're interconnected through shared currencies (USD, EUR, GBP, JPY). Current strategy only captures linear correlations (44 features). This stage adds **non-linear interaction features** that exploit cross-pair dependencies.

**Example:**
```
EUR/USD and GBP/USD both share USD
When both pairs accelerate together → Strong USD move (high predictive value)
When EUR/USD rises but GBP/USD falls → EUR-specific event (divergence opportunity)
```

### Technical Specification

#### 1. Momentum Products (24 features)

**Purpose:** Capture joint acceleration patterns

**Implementation:**
```sql
-- For each sister pair (e.g., EURUSD-GBPUSD, EURJPY-GBPJPY)
CREATE TABLE bqx.cross_pair_momentum_{pair} AS
SELECT
    e.ts_utc,
    -- 60-minute window
    e.w60_quadratic_term * g.w60_quadratic_term AS momentum_product_w60_quad,
    e.w60_linear_term * g.w60_linear_term AS momentum_product_w60_lin,

    -- 90-minute window
    e.w90_quadratic_term * g.w90_quadratic_term AS momentum_product_w90_quad,
    e.w90_linear_term * g.w90_linear_term AS momentum_product_w90_lin,

    -- Repeat for w150, w240, w390, w630
    ...
FROM bqx.reg_bqx_eurusd e
JOIN bqx.reg_bqx_gbpusd g ON e.ts_utc = g.ts_utc;
```

**Sister Pairs:**
- EUR pairs: EURUSD, EURGBP, EURJPY, EURCHF, EURAUD, EURCAD, EURNZD
- GBP pairs: GBPUSD, GBPJPY, GBPCHF, GBPAUD, GBPCAD, GBPNZD
- JPY pairs: USDJPY, EURJPY, GBPJPY, AUDJPY, CADJPY, CHFJPY, NZDJPY
- Total: 12 sister pair groups × 2 features per window × 6 windows = 144 features (select top 24)

#### 2. Relative Volatility Ratios (12 features)

**Purpose:** Detect pair-specific events (divergence)

**Implementation:**
```sql
SELECT
    ts_utc,
    -- Volatility ratios
    vol_eurusd_30 / NULLIF(vol_gbpusd_30, 0) AS rel_vol_eurusd_gbpusd_30,
    vol_eurusd_60 / NULLIF(vol_gbpusd_60, 0) AS rel_vol_eurusd_gbpusd_60,

    -- Threshold features
    CASE WHEN vol_eurusd_30 / NULLIF(vol_gbpusd_30, 0) > 1.5 THEN 1 ELSE 0 END AS divergence_flag_30
FROM volatility_features;
```

**Interpretation:**
- Ratio > 1.5: EUR-specific event (EUR news, ECB announcement)
- Ratio < 0.67: GBP-specific event (BOE announcement, Brexit news)
- Ratio ≈ 1.0: Shared USD move (no divergence)

#### 3. Correlation Drift (12 features)

**Purpose:** Detect pairs decoupling (risk event)

**Implementation:**
```python
# Calculate correlation drift
corr_t = rolling_correlation(bqx_eurusd, bqx_gbpusd, window=60)
corr_t_60 = lag(corr_t, 60)  # Correlation 60 minutes ago
corr_drift = (corr_t - corr_t_60) / corr_t_60

# Feature engineering
features['corr_drift_eurusd_gbpusd_60'] = corr_drift
features['corr_drift_abs'] = abs(corr_drift)
features['decoupling_flag'] = (corr_drift < -0.3).astype(int)  # Rapid decrease
```

**Interpretation:**
- corr_drift < -0.3: Pairs rapidly decoupling (risk event, uncertainty)
- corr_drift > 0.3: Pairs rapidly coupling (shared directional move)

#### 4. Lead-Lag Features (24 features)

**Purpose:** Exploit predictive relationships between pairs

**Implementation:**
```python
# Granger causality test to identify lead-lag relationships
from statsmodels.tsa.stattools import grangercausalitytests

# Test if GBP/USD leads EUR/USD
results = grangercausalitytests(
    data[['bqx_eurusd', 'bqx_gbpusd']],
    maxlag=15,  # Test lags 1-15 minutes
    verbose=False
)

# If GBP/USD leads EUR/USD by 5 minutes (p-value < 0.05)
# Add lagged features to EUR/USD model
features['gbpusd_bqx_w60_lag5'] = lag(bqx_gbpusd_w60, 5)
features['gbpusd_quad_term_lag5'] = lag(gbpusd_w60_quadratic_term, 5)
```

**Known Lead-Lag Relationships:**
- GBP/USD often leads EUR/USD by 3-7 minutes (London market)
- USD/JPY often leads other JPY pairs by 2-5 minutes (Tokyo market)
- AUD/USD often leads NZD/USD by 5-10 minutes (commodity currencies)

### Deliverables

1. **Database Tables:**
   - `bqx.cross_pair_momentum_{pair}` (28 tables, 12 partitions each)
   - `bqx.cross_pair_volatility_{pair}` (28 tables)
   - `bqx.cross_pair_correlation_drift_{pair}` (28 tables)
   - `bqx.cross_pair_lead_lag_{pair}` (28 tables)

2. **Python Scripts:**
   - `scripts/features/stage_2_16_cross_pair_interactions.py` (main worker)
   - `scripts/analysis/granger_causality_analysis.py` (lead-lag discovery)

3. **Documentation:**
   - Sister pair mapping (which pairs to compare)
   - Lead-lag relationship analysis report
   - Feature importance ranking (post-training)

4. **Updated S3 Export:**
   - Modify `export_features_to_s3.py` to include cross-pair features

### Validation Criteria

- ✅ All 28 pairs have cross-pair tables created
- ✅ 72 features successfully computed for all 336 partitions
- ✅ No NULL values in interaction features (handle division by zero)
- ✅ Lead-lag relationships validated with Granger causality (p < 0.05)
- ✅ Performance improvement: Directional accuracy 65% → 70% on test set

### Expected Impact

**Before Stage 2.16:**
- R² = 0.82
- Directional Accuracy = 65%
- Sharpe Ratio = 1.5

**After Stage 2.16:**
- R² = 0.85 (+3.7%)
- Directional Accuracy = 70% (+7.7%)
- Sharpe Ratio = 1.75 (+16.7%)

---

## Stage 2.17: Autoencoder Learned Representations

### Overview

**Tier:** 2 (Very High Priority)
**Duration:** 1 week (40 hours)
**Cost:** $50 (GPU instance for training)
**ROI:** +45% performance improvement
**Dependencies:** Stage 2.16 (needs all features)

**Architecture Decision:** **ONE shared autoencoder** trained on pooled data from all 28 pairs, then applied independently to each pair

### Rationale

Hand-crafted features miss **non-linear patterns** that machines can discover. Autoencoders learn compressed representations (embeddings) that capture latent structure in data.

**Why ONE Shared Autoencoder?**

1. **Superior Generalization:** Training on 10M+ samples (all pairs) vs. 370K (single pair) learns better latent representations
2. **Universal Feature Space:** Same embedding dimensions capture similar patterns across pairs (e.g., "momentum exhaustion" applies to all)
3. **Efficiency:** Train once, apply 28 times (vs. training 28 separate autoencoders)
4. **Cross-Pair Transfer:** Patterns learned from high-liquidity pairs (EURUSD) benefit lower-liquidity pairs (AUDCAD)

**Example:**
```
Human Engineer: Creates 730 explicit features (quadratic_term, linear_term, etc.)
Autoencoder: Learns embedding_23 = f(quadratic_term, volatility, residual, regime)
              ↳ Discovers "choppy momentum regime" pattern automatically
```

**Why This Works:**
- Markets are non-linear (momentum acceleration, regime shifts)
- Autoencoder finds combinations humans would never engineer
- 64 embeddings often outperform 730 hand-crafted features
- Proven ROI: 2-3x improvement in financial ML

### Technical Specification

#### Architecture

```python
import tensorflow as tf

# Input: 730 base features + 72 cross-pair = 802 features
input_dim = 802

# Autoencoder Architecture
autoencoder = tf.keras.Sequential([
    # ENCODER (compress)
    tf.keras.layers.Dense(512, activation='relu', input_dim=input_dim),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Dropout(0.2),

    tf.keras.layers.Dense(256, activation='relu'),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Dropout(0.2),

    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.BatchNormalization(),

    # BOTTLENECK (learned representations)
    tf.keras.layers.Dense(64, activation='relu', name='embedding'),

    # DECODER (reconstruct)
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.BatchNormalization(),

    tf.keras.layers.Dense(256, activation='relu'),
    tf.keras.layers.BatchNormalization(),

    tf.keras.layers.Dense(512, activation='relu'),
    tf.keras.layers.BatchNormalization(),

    # OUTPUT (reconstruct original 802 features)
    tf.keras.layers.Dense(input_dim, activation='linear')
])

# Loss: Reconstruction error (minimize difference between input and output)
autoencoder.compile(optimizer='adam', loss='mse', metrics=['mae'])
```

#### Training Strategy (Shared Autoencoder)

```python
# 1. Load ALL features from ALL 28 pairs (pooled training)
X_all_pairs = []
for pair in PAIRS:
    for year_month in YEAR_MONTHS:
        df = load_features(pair, year_month)
        X_all_pairs.append(df)

X_all_pairs = pd.concat(X_all_pairs)  # Shape: (~10M rows, 802 features)

# 2. Normalize features (critical for autoencoder)
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_normalized = scaler.fit_transform(X_all_pairs)

# 3. Train ONE shared autoencoder on pooled data
history = autoencoder.fit(
    X_normalized, X_normalized,  # Input = Output (reconstruction)
    epochs=50,
    batch_size=1024,
    validation_split=0.2,
    callbacks=[
        tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5),
        tf.keras.callbacks.ModelCheckpoint('autoencoder_best.h5', save_best_only=True)
    ]
)

# 4. Save SHARED autoencoder (used for all pairs)
autoencoder.save('autoencoder_802_to_64.h5')
scaler.save('feature_scaler.pkl')

# 5. Extract embedding model (encoder only)
embedding_model = tf.keras.Model(
    inputs=autoencoder.input,
    outputs=autoencoder.get_layer('embedding').output
)
embedding_model.save('embedding_extractor.h5')

# 6. Apply embeddings PER-PAIR (same encoder, different input data)
for pair in PAIRS:
    for year_month in YEAR_MONTHS:
        X_pair = load_features(pair, year_month)
        X_pair_normalized = scaler.transform(X_pair)  # Use SAME scaler
        embeddings_pair = embedding_model.predict(X_pair_normalized)  # 64-dim

        # Store per-pair embeddings (values differ, encoder is shared)
        save_to_db(embeddings_pair, f'bqx.autoencoder_embeddings_{pair}_{year_month}')
```

**Key Points:**
- **ONE model trained:** `autoencoder_802_to_64.h5` (shared)
- **28 embedding tables:** `autoencoder_embeddings_{pair}` (per-pair values)
- **Same encoder, different outputs:** EURUSD and GBPUSD get different embedding values from the same encoder

#### Embedding Interpretation

**Clustering Analysis:**
```python
from sklearn.cluster import KMeans

# Cluster embeddings to understand what patterns they capture
kmeans = KMeans(n_clusters=10)
clusters = kmeans.fit_predict(embeddings)

# Analyze cluster characteristics
for cluster_id in range(10):
    cluster_data = X_all_pairs[clusters == cluster_id]
    print(f"Cluster {cluster_id}:")
    print(f"  Avg volatility: {cluster_data['vol_60'].mean():.4f}")
    print(f"  Avg momentum: {cluster_data['bqx_w60'].mean():.4f}")
    print(f"  Dominant regime: {cluster_data['regime_type'].mode()[0]}")
```

**Example Discoveries:**
- `embedding_5`: Captures "high volatility + low R²" → Choppy regime
- `embedding_17`: Captures "positive quad + negative resid" → Momentum exhaustion
- `embedding_42`: Captures "EUR/GBP/JPY aligned" → USD strength move

### Deliverables

1. **Trained Models:**
   - `models/autoencoder_802_to_64.h5` (full autoencoder)
   - `models/embedding_extractor.h5` (encoder only, for inference)
   - `models/feature_scaler.pkl` (StandardScaler for normalization)

2. **Database Tables:**
   - `bqx.autoencoder_embeddings_{pair}` (28 tables, 64 columns each)
   - Partitioned by month (12 partitions per pair)

3. **Python Scripts:**
   - `scripts/ml/stage_2_17_train_autoencoder.py` (training)
   - `scripts/ml/extract_embeddings.py` (inference)
   - `scripts/analysis/embedding_interpretation.py` (clustering analysis)

4. **Documentation:**
   - Autoencoder architecture diagram
   - Training loss curves (reconstruction error over epochs)
   - Embedding interpretation report (what each embedding captures)
   - Feature importance comparison (embeddings vs hand-crafted)

### Validation Criteria

- ✅ Reconstruction error (MAE) < 0.05 on validation set
- ✅ Embeddings show clear clustering structure (silhouette score > 0.4)
- ✅ All 28 pairs have embeddings extracted for 336 partitions
- ✅ Embeddings rank high in feature importance (top 20%)
- ✅ Performance improvement: Directional accuracy 70% → 75% on test set

### Expected Impact

**Before Stage 2.17:**
- R² = 0.85
- Directional Accuracy = 70%
- Sharpe Ratio = 1.75
- Feature Count: 802

**After Stage 2.17:**
- R² = 0.88 (+3.5%)
- Directional Accuracy = 75% (+7.1%)
- Sharpe Ratio = 2.0 (+14.3%)
- Feature Count: 866 (802 base + 64 embeddings)

---

## Stage 2.18: Multi-Task Neural Network Architecture

### Overview

**Tier:** 4 (Medium Priority)
**Duration:** 1 week (40 hours)
**Cost:** $40 (SageMaker notebook)
**ROI:** +10% performance improvement (on top of Stage 2.17)
**Dependencies:** Stage 2.17 (uses embeddings)

**Architecture Decision:** **28 per-pair multi-task neural networks** (one per pair, maintains independence)

### Rationale

BQX prediction, volatility prediction, and regime classification are **correlated tasks** within each pair. Training them jointly per-pair:
1. Shared layers learn better universal representations
2. Auxiliary tasks regularize the primary task (prevent overfitting)
3. Improves all tasks simultaneously (synergy)

**Example:**
```
Traditional: Train separate model for BQX prediction
Multi-Task: Train joint model for BQX + volatility + regime
            ↳ Model learns vol-sensitive features that also help BQX
            ↳ Model learns regime-discriminative features that also help BQX
```

### Technical Specification

#### Architecture

```python
import tensorflow as tf

# Input: 866 features (802 base + 64 embeddings)
inputs = tf.keras.Input(shape=(866,), name='input')

# SHARED HIDDEN LAYERS (learn universal representations)
shared = tf.keras.layers.Dense(256, activation='relu', name='shared_1')(inputs)
shared = tf.keras.layers.BatchNormalization()(shared)
shared = tf.keras.layers.Dropout(0.3)(shared)

shared = tf.keras.layers.Dense(128, activation='relu', name='shared_2')(shared)
shared = tf.keras.layers.BatchNormalization()(shared)
shared = tf.keras.layers.Dropout(0.3)(shared)

# TASK-SPECIFIC HEADS

# Task 1: BQX_t+60 Prediction (PRIMARY TASK)
bqx_head = tf.keras.layers.Dense(64, activation='relu')(shared)
bqx_head = tf.keras.layers.Dropout(0.2)(bqx_head)
bqx_output = tf.keras.layers.Dense(1, activation='linear', name='bqx_t60')(bqx_head)

# Task 2: Volatility_t+60 Prediction (AUXILIARY)
vol_head = tf.keras.layers.Dense(32, activation='relu')(shared)
vol_head = tf.keras.layers.Dropout(0.2)(vol_head)
vol_output = tf.keras.layers.Dense(1, activation='linear', name='vol_t60')(vol_head)

# Task 3: Regime_t+60 Classification (AUXILIARY)
regime_head = tf.keras.layers.Dense(32, activation='relu')(shared)
regime_head = tf.keras.layers.Dropout(0.2)(regime_head)
regime_output = tf.keras.layers.Dense(5, activation='softmax', name='regime_t60')(regime_head)

# Multi-Task Model
model = tf.keras.Model(
    inputs=inputs,
    outputs=[bqx_output, vol_output, regime_output]
)
```

#### Training Strategy (Per-Pair Multi-Task Training)

```python
# Train 28 independent multi-task NNs (one per pair)
for pair in PAIRS:
    # Load pair-specific data with embeddings
    X_pair = load_features_with_embeddings(pair)  # 866 features
    y_bqx_pair = load_target(pair, 'bqx', horizon=60)
    y_vol_pair = load_target(pair, 'volatility', horizon=60)
    y_regime_pair = load_target(pair, 'regime', horizon=60)

    # Build pair-specific multi-task model
    model = build_multi_task_nn(input_dim=866)

    # Multi-Task Loss (weighted)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss={
            'bqx_t60': 'mse',                       # Primary (weight = 1.0)
            'vol_t60': 'mse',                       # Auxiliary (weight = 0.3)
            'regime_t60': 'categorical_crossentropy' # Auxiliary (weight = 0.3)
        },
        loss_weights={
            'bqx_t60': 1.0,
            'vol_t60': 0.3,
            'regime_t60': 0.3
        },
        metrics={
            'bqx_t60': ['mae', 'mse'],
            'vol_t60': ['mae'],
            'regime_t60': ['accuracy']
        }
    )

    # Train jointly on pair-specific data
    history = model.fit(
        X_pair_train,
        {
            'bqx_t60': y_bqx_train,
            'vol_t60': y_vol_train,
            'regime_t60': y_regime_train
        },
        validation_data=(
            X_pair_val,
            {
                'bqx_t60': y_bqx_val,
                'vol_t60': y_vol_val,
                'regime_t60': y_regime_val
            }
        ),
        epochs=100,
        batch_size=512,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(monitor='val_bqx_t60_mae', patience=10),
            tf.keras.callbacks.ReduceLROnPlateau(monitor='val_bqx_t60_mae', factor=0.5, patience=5)
        ]
    )

    # Save pair-specific multi-task model
    model.save(f'multi_task_nn_{pair}.h5')

# Result: 28 independent multi-task models (one per pair)
```

**Key Points:**

- **28 separate models:** Each pair gets its own multi-task NN
- **Per-pair optimization:** EURUSD's BQX-volatility-regime relationships differ from GBPUSD's
- **Maintains independence:** Consistent with overall per-pair strategy
- **Shared architecture, different weights:** Same NN structure, pair-specific learned parameters

#### Target Engineering

```python
# Primary Target: BQX_t+60
y_bqx = df['bqx'].shift(-60)  # 60 minutes ahead

# Auxiliary Target 1: Volatility_t+60
rolling_std = df['bqx'].rolling(60).std()
y_vol = rolling_std.shift(-60)

# Auxiliary Target 2: Regime_t+60 (5 classes)
def classify_regime(bqx_value, volatility):
    if volatility > 0.5:
        return 'high_vol'
    elif bqx_value > 0.3:
        return 'strong_bull'
    elif bqx_value > 0.1:
        return 'bull'
    elif bqx_value < -0.3:
        return 'strong_bear'
    elif bqx_value < -0.1:
        return 'bear'
    else:
        return 'neutral'

y_regime = df.apply(lambda row: classify_regime(row['bqx'], row['vol_60']), axis=1)
y_regime_encoded = pd.get_dummies(y_regime.shift(-60))  # One-hot encoding
```

### Deliverables

1. **Trained Models (28 per-pair models):**
   - `models/multi_task_nn_{pair}.h5` (28 models: eurusd, gbpusd, ..., nzdusd)
   - Each model: BQX+volatility+regime prediction for its specific pair

2. **SageMaker Notebooks:**
   - `notebooks/stage_2_18_multi_task_training.ipynb` (training loop for all pairs)
   - `notebooks/multi_task_evaluation.ipynb` (comparative analysis across pairs)

3. **Python Scripts:**
   - `scripts/ml/stage_2_18_multi_task_train.py` (trains all 28 models)
   - `scripts/ml/multi_task_predict.py` (inference for all pairs)

4. **Documentation:**
   - Multi-task architecture diagram
   - Training loss curves for all 3 tasks (averaged across pairs)
   - Task correlation analysis (how auxiliary tasks help primary per-pair)
   - Ablation study (multi-task vs single-task performance)
   - Per-pair performance comparison (which pairs benefit most from multi-task)

### Validation Criteria

- ✅ BQX prediction MAE < baseline single-task model
- ✅ Volatility prediction R² > 0.7
- ✅ Regime classification accuracy > 70%
- ✅ Shared layer activations show universal patterns (visualization)
- ✅ Performance improvement: Directional accuracy 75% → 77% on test set

### Expected Impact

**Before Stage 2.18:**
- R² = 0.88
- Directional Accuracy = 75%
- Sharpe Ratio = 2.0

**After Stage 2.18:**
- R² = 0.90 (+2.3%)
- Directional Accuracy = 77% (+2.7%)
- Sharpe Ratio = 2.1 (+5.0%)

---

## Stage 2.19: Online Adaptive Learning Pipeline

### Overview

**Tier:** 3 (Long-Term Priority)
**Duration:** 2 weeks (80 hours)
**Cost:** $100/month (Lambda + DynamoDB)
**ROI:** +10% long-term robustness
**Dependencies:** Stage 2.18 (needs base models)

### Rationale

Static models **degrade over time** due to concept drift (market regimes change). Online learning:
1. Updates model weights incrementally with new data
2. Detects concept drift (sudden performance degradation)
3. Maintains performance over months/years without full retraining
4. Adapts ensemble weights based on recent performance

**Example:**
```
2023: Low volatility, trending regime → XGBoost performs best
2024: High volatility, choppy regime → Random Forest performs best
Online Learning: Automatically shifts weight from XGBoost to RF
```

### Technical Specification

#### Architecture

```python
from river import ensemble, tree, drift

# Online Random Forest (incrementally updates with each new data point)
online_rf = ensemble.AdaptiveRandomForestRegressor(
    n_models=100,
    max_features='sqrt',
    lambda_value=6,  # Exponential decay for old data (half-life = 6 hours)
    drift_detector=drift.ADWIN(delta=0.002),  # Detect concept drift
    warning_detector=drift.ADWIN(delta=0.01)  # Warn before drift occurs
)

# Online Gradient Boosting
online_gb = ensemble.AdaBoostRegressor(
    model=tree.HoeffdingTreeRegressor(),
    n_models=50,
    learning_rate=0.05
)

# Adaptive Ensemble (meta-learner)
class AdaptiveEnsemble:
    def __init__(self, models):
        self.models = models  # {'rf': online_rf, 'gb': online_gb, 'xgb': ..., 'nn': ...}
        self.recent_errors = {name: deque(maxlen=100) for name in models}
        self.weights = {name: 0.25 for name in models}  # Equal weights initially

    def predict(self, X):
        # Get predictions from all models
        predictions = {name: model.predict_one(X) for name, model in self.models.items()}

        # Weighted average
        ensemble_pred = sum(w * predictions[name] for name, w in self.weights.items())
        return ensemble_pred

    def learn(self, X, y_true):
        # Update all models
        for name, model in self.models.items():
            y_pred = model.predict_one(X)
            error = abs(y_true - y_pred)
            self.recent_errors[name].append(error)
            model.learn_one(X, y_true)

        # Update ensemble weights (softmax based on recent errors)
        avg_errors = {name: np.mean(errors) for name, errors in self.recent_errors.items()}
        exp_negative_errors = {name: np.exp(-err) for name, err in avg_errors.items()}
        total = sum(exp_negative_errors.values())
        self.weights = {name: val / total for name, val in exp_negative_errors.items()}
```

#### Real-Time Pipeline

```python
# AWS Lambda function (triggered every minute)
def lambda_handler(event, context):
    # 1. Fetch new data from Aurora
    new_data = fetch_latest_minute_data()
    X_new = extract_features(new_data)

    # 2. Load current model from S3
    ensemble = load_model_from_s3('s3://bqx-ml-models/online_ensemble.pkl')

    # 3. Make prediction
    y_pred = ensemble.predict(X_new)

    # 4. Store prediction in DynamoDB
    store_prediction(timestamp=new_data['time'], prediction=y_pred)

    # 5. After 60 minutes, observe actual BQX value
    if actual_value_available():
        y_actual = fetch_actual_bqx(timestamp=new_data['time'] + timedelta(minutes=60))

        # 6. Update model with observed value
        ensemble.learn(X_new, y_actual)

        # 7. Detect concept drift
        if ensemble.drift_detected:
            send_alert('Concept drift detected! Consider full retrain.')
            log_drift_event()

        # 8. Save updated model to S3
        save_model_to_s3(ensemble, 's3://bqx-ml-models/online_ensemble.pkl')

    return {'statusCode': 200, 'prediction': y_pred}
```

#### Drift Detection

```python
# ADWIN (Adaptive Windowing) Algorithm
# Detects when error distribution changes significantly

class ConceptDriftMonitor:
    def __init__(self):
        self.error_window = deque(maxlen=1000)  # Last 1000 predictions
        self.baseline_mae = None

    def update(self, error):
        self.error_window.append(error)

        if len(self.error_window) < 100:
            return False  # Need baseline

        # Calculate baseline (first 100 errors)
        if self.baseline_mae is None:
            self.baseline_mae = np.mean(list(self.error_window)[:100])

        # Calculate recent performance (last 100 errors)
        recent_mae = np.mean(list(self.error_window)[-100:])

        # Drift detected if recent error > 1.5× baseline
        if recent_mae > self.baseline_mae * 1.5:
            return True

        return False
```

### Deliverables

1. **AWS Infrastructure:**
   - Lambda function: `bqx-ml-online-learner` (triggered every minute)
   - DynamoDB table: `bqx_predictions` (store predictions + actual values)
   - S3 bucket: `bqx-ml-models/online/` (model checkpoints)
   - CloudWatch alarms: Drift detection alerts

2. **Python Scripts:**
   - `scripts/ml/stage_2_19_online_learning_setup.py` (infrastructure setup)
   - `scripts/ml/online_predict_and_learn.py` (Lambda function code)
   - `scripts/monitoring/drift_detector.py`

3. **Documentation:**
   - Online learning architecture diagram
   - Drift detection methodology
   - Performance monitoring dashboard (Grafana)
   - Incident response playbook (what to do when drift detected)

4. **Monitoring Dashboards:**
   - Real-time prediction accuracy (last hour, day, week)
   - Ensemble weight evolution over time
   - Drift detection events log
   - Model update frequency

### Validation Criteria

- ✅ Lambda function executes successfully every minute (99.9% uptime)
- ✅ Model updates within 5 seconds of new data arrival
- ✅ Drift detection triggers alert within 10 minutes of degradation
- ✅ Performance maintained over 3 months (R² > 0.88 consistently)
- ✅ Adaptive ensemble weights shift appropriately based on regime

### Expected Impact

**Before Stage 2.19 (Static Model):**
- R² = 0.90 (initial)
- R² = 0.72 (after 12 months, 20% degradation)
- Sharpe Ratio = 2.1 (initial) → 1.6 (after 12 months)

**After Stage 2.19 (Online Learning):**
- R² = 0.90 (initial)
- R² = 0.88 (after 12 months, only 2% degradation)
- Sharpe Ratio = 2.1 (initial) → 2.2 (after 12 months, IMPROVED)

**Key Benefit:** Long-term robustness (maintains performance over time)

---

## Integration with Existing Stages

### Modified Stages

#### Stage 2.7: S3 Export (ALREADY MODIFIED)
- ✅ Updated to include all 9 feature families
- ✅ Updated column names to term-based schema
- ➕ **New:** Add cross-pair features (Stage 2.16)
- ➕ **New:** Add autoencoder embeddings (Stage 2.17)

#### Stage 3.1: Training Pipeline Development
- ➕ **New:** Update to use 866 total features (802 base + 64 embeddings)
- ➕ **New:** Integrate multi-task neural network (Stage 2.18)
- ➕ **New:** Add online learning initialization (Stage 2.19)

#### Stage 3.4: Real-Time Inference System
- ➕ **New:** Integrate online learning updates (Stage 2.19)
- ➕ **New:** Add drift detection monitoring

---

## Dependency Graph

```
[Stage 2.15: Validation] ← Current position
          ↓
[Stage 2.16: Cross-Pair Interactions] (1 week)
          ↓
[Stage 2.17: Autoencoder Embeddings] (1 week)
          ↓
[Stage 2.18: Multi-Task Neural Network] (1 week)
          ↓
[Stage 2.19: Online Adaptive Learning] (2 weeks)
          ↓
[Stage 2.7: S3 Export - UPDATED] ← Final Phase 2 deliverable
          ↓
[Phase 3: SageMaker Deployment]
```

**Total Additional Time:** 5 weeks
**Can Parallelize:** Stages 2.16 and 2.17 (reduce to 4 weeks)

---

## Cost Analysis

### One-Time Costs

| Stage | Description | Cost |
|-------|-------------|------|
| 2.16 | EC2 compute for feature calculation | $20 |
| 2.17 | GPU instance for autoencoder training | $50 |
| 2.18 | SageMaker notebook for multi-task training | $40 |
| 2.19 | Initial setup (Lambda, DynamoDB) | $50 |
| **Total** | **One-time setup** | **$160** |

### Ongoing Costs

| Component | Monthly Cost |
|-----------|--------------|
| Lambda (2,592,000 invocations/month) | $50 |
| DynamoDB (write/read capacity) | $30 |
| S3 (model storage, 10 GB) | $2 |
| CloudWatch (logs, alarms) | $18 |
| **Total** | **$100/month** |

**Annual Cost:** $1,200/year for online learning infrastructure

---

## Performance Projection

### Baseline (Before Enhancements)
```
R² = 0.82
Directional Accuracy = 65%
Sharpe Ratio = 1.5
Annual Return = 45%
```

### After All Enhancements (Stages 2.16-2.19)
```
R² = 0.90 (+9.8%)
Directional Accuracy = 77% (+18.5%)
Sharpe Ratio = 2.2 (+46.7%)
Annual Return = 66% (+46.7%)
```

### ROI Analysis
```
Additional Development Cost: 5 weeks @ $5,000/week = $25,000
Additional Infrastructure Cost: $1,200/year

Performance Improvement: +46.7% Sharpe Ratio
Expected Revenue Increase: +$50,000/year (based on $100K baseline)

ROI: ($50,000 - $1,200) / $25,000 = 195% first year
Break-even: 6 months
```

---

## Success Metrics

### Quantitative Metrics

| Metric | Baseline | Target | Actual (Post-Implementation) |
|--------|----------|--------|------------------------------|
| R² | 0.82 | 0.90 | TBD |
| Directional Accuracy | 65% | 77% | TBD |
| Sharpe Ratio | 1.5 | 2.2 | TBD |
| Feature Count | 730 | 866 | 866 |
| Model Degradation (12 months) | 20% | <5% | TBD |

### Qualitative Metrics

- ✅ **Aggressive:** Exploits cross-pair interactions, non-linear patterns via embeddings
- ✅ **Robust:** Multi-signal triangulation + online adaptation + multi-task regularization
- ✅ **Spanning:** Features (866), Pairs (28 joint learning), Windows (6 multi-resolution)
- ✅ **Production-Ready:** Monitoring, drift detection, automated updates

---

## Risk Mitigation

### Risk 1: Overfitting with 866 Features

**Mitigation:**
- Feature selection reduces to ~280 features
- Regularization (dropout, L2) in neural networks
- Cross-validation on multiple time periods
- Ensemble diversity prevents single-model overfitting

### Risk 2: Concept Drift Despite Online Learning

**Mitigation:**
- Drift detection with ADWIN algorithm
- Manual retraining triggers when drift detected
- Maintain rolling baseline model for comparison
- A/B testing (online vs baseline)

### Risk 3: Autoencoder Embeddings Not Interpretable

**Mitigation:**
- Clustering analysis to understand patterns
- Feature importance ranking post-training
- Ablation studies (with/without embeddings)
- Visualization of embedding space (t-SNE)

### Risk 4: Infrastructure Costs Exceed Budget

**Mitigation:**
- Use Spot instances for GPU training (-70% cost)
- Optimize Lambda memory allocation (reduce cost)
- Use reserved DynamoDB capacity (-75% cost)
- Monitor spending with CloudWatch alarms

---

## Timeline

### Week-by-Week Breakdown

**Week 1: Stage 2.16 - Cross-Pair Interactions**
- Day 1-2: Sister pair analysis, Granger causality tests
- Day 3-4: Feature calculation scripts, database schema
- Day 5: Feature population (28 pairs × 12 months)

**Week 2: Stage 2.17 - Autoencoder Training**
- Day 1: Data preparation, normalization
- Day 2-3: Autoencoder training (50 epochs, GPU)
- Day 4: Embedding extraction, database population
- Day 5: Embedding interpretation, clustering analysis

**Week 3: Stage 2.18 - Multi-Task Neural Network**
- Day 1-2: Target engineering (BQX, volatility, regime)
- Day 3-4: Multi-task model training, hyperparameter tuning
- Day 5: Model evaluation, ablation studies

**Week 4-5: Stage 2.19 - Online Learning Pipeline**
- Week 4 Day 1-2: AWS infrastructure setup (Lambda, DynamoDB)
- Week 4 Day 3-4: Online learning algorithm implementation
- Week 4 Day 5: Drift detection implementation
- Week 5 Day 1-2: Integration testing, monitoring dashboards
- Week 5 Day 3-4: Production deployment, documentation
- Week 5 Day 5: Final validation, handoff

---

## Conclusion

These four enhancement stages (2.16-2.19) transform the BQX ML system from **"excellent"** to **"state-of-the-art aggressive and robust"**.

**Key Achievements:**
- ✅ Cross-pair interaction learning (non-linear dependencies)
- ✅ Learned representations (autoencoder embeddings)
- ✅ Multi-task learning (joint optimization)
- ✅ Online adaptive learning (long-term robustness)

**Performance Impact:**
- +47% Sharpe Ratio improvement (1.5 → 2.2)
- +18% Directional Accuracy improvement (65% → 77%)
- +10% R² improvement (0.82 → 0.90)

**Investment:**
- 5 weeks development time
- $160 one-time cost
- $100/month ongoing cost
- 195% first-year ROI

The project will be **production-ready** and **future-proof** with these enhancements fully implemented.
