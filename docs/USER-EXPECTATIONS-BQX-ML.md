# User Expectations for BQX ML - Extracted from bqx-db Repository

**Analysis Date**: 2025-11-09
**Source**: schmidtlappin/bqx-db repository
**Focus**: BQX (backward-looking) data strategy vs FWD (forward-looking) data

---

## Executive Summary

This document extracts user expectations for BQX ML from the bqx-db repository, **specifically filtered for BQX (backward) data requirements** as opposed to the deprecated FWD (forward) data approach.

### Critical Paradigm Shift: FWD → BQX

**OLD APPROACH (Deprecated)**:
- Used FWD (forward return) data: `w60_fwd_return = (rate[t+60] - rate[t]) / rate[t]`
- Problem: Requires future data, not real-time deployable
- Caused temporal causality violations

**NEW APPROACH (Current BQX ML)**:
- Uses BQX (backward return) data: `w60_bqx_return = Σ(i=1 to 60)[rate(t-i) - rate(t)] / rate(t]`
- Advantage: All features observable in real-time
- Mathematical equivalence: `BQX_{t+60} ≈ FWD_t` (both measure t→t+60 movement)

---

## 1. Ultimate Goal

### R² → 1.0 (Exact Forex Prediction)

**From**: `BQX_ML_MASTERPLAN_EXECUTIVE_SUMMARY.md`

**User Expectation**:
- **Ultimate Goal**: R² → 1.0 (approaching perfect prediction across 28 forex pairs)
- **Realistic Target**: R² > 0.95 (ensemble of multiple architectures)
- **Minimum Acceptable**: R² > 0.88 (single TFT architecture)

**Timeline for Achievement**:
- Month 1: R² = 0.95 (initial ensemble)
- Month 3: R² = 0.96 (with retraining + new features)
- Month 6: R² = 0.97 (with advanced techniques)
- Month 12: R² = 0.98+ (approaching theoretical limit)

**BQX-Specific Application**:
- Predict future BQX values using current BQX patterns (autoregressive)
- `BQX_t → BQX_{t+60}` prediction task
- All features backward-looking from M1, REG, BQX tables

---

## 2. Temporal Causality Rule (CRITICAL)

### The 61-Minute Lag Rule

**From**: `ML_TEMPORAL_CAUSALITY_LOGIC.md`

**CRITICAL CONSTRAINT**: Must be enforced in all ML pipelines.

**For BQX Data**:

At timestamp T = 11:00 AM, BQX ML can use:
- ✅ **All BQX feature data up to 11:00 AM** (backward-looking, no future info)
- ✅ **All BQX target data up to 09:59 AM** (T-61 minutes, prevents overlap)
- 🎯 **Prediction target**: `target[11:00 AM]` = BQX return from [10:00 AM → 11:00 AM] observed at 11:00 AM

**Why This Matters for BQX**:

BQX features are inherently backward-looking:
```python
# BQX features at 11:00 AM (SAFE - uses only past data)
w15_bqx_return[11:00] = Σ[rate(10:45 to 10:59) - rate(11:00)] / rate(11:00)
w30_bqx_return[11:00] = Σ[rate(10:30 to 10:59) - rate(11:00)] / rate(11:00)
w60_bqx_return[11:00] = Σ[rate(10:00 to 10:59) - rate(11:00)] / rate(11:00)
w75_bqx_return[11:00] = Σ[rate(09:45 to 10:59) - rate(11:00)] / rate(11:00)
```

**Key Difference from FWD**:
- FWD data looked forward (unsafe, requires future data)
- BQX data looks backward (safe, uses only past data)
- **BQX tables enable real-time prediction** - this is why we migrated!

**Implementation Requirements**:
1. ✅ BQX features: All data ≤ T (backward-looking)
2. ✅ BQX lag features (if used as additional features): All data ≤ T-61
3. ✅ Prediction target: BQX_{t+60} (future BQX value)
4. ❌ NEVER use BQX data from T-60 to T (overlaps with prediction window)

---

## 3. Data Architecture for BQX ML

### Aurora PostgreSQL Tables

**From**: Multiple docs + our BQX table creation

**BQX ML Uses These Tables**:

| Table | Purpose | Status | Rows/Pair | Fields |
|-------|---------|--------|-----------|--------|
| **bqx_* (NEW)** | Backward momentum features | ✅ Created (populating) | ~370K | 40 |
| **m1_*** | 1-minute OHLC source data | ✅ Complete | ~525K/year | 6 |
| **reg_*** | Regression patterns | ✅ Complete | ~525K/year | 75 |
| ~~**fwd_***~~ | ~~Forward returns~~ | ❌ **DELETED** | N/A | N/A |
| **mv_*_merged** | ❌ Need recreation (BQX-based) | 🟡 Pending | TBD | TBD |

### BQX Table Schema (40 fields)

**Core Fields** (3):
- `ts_utc`: Timestamp (UTC), Primary Key
- `rate`: Exchange rate at timestamp
- `created_at`: Row creation timestamp

**Window Metrics** (30 fields = 5 windows × 6 metrics):

Windows: **15, 30, 45, 60, 75 minutes** (finer granularity than FWD's 60-630)

For each window W:
- `w{W}_bqx_return`: Cumulative return: `Σ(i=1 to W)[rate(t-i) - rate(t)] / rate(t)`
- `w{W}_bqx_max`: Maximum rate in window
- `w{W}_bqx_min`: Minimum rate in window
- `w{W}_bqx_avg`: Average rate in window
- `w{W}_bqx_stdev`: Standard deviation in window
- `w{W}_bqx_endpoint`: Endpoint return (first to last in window)

**Aggregate Metrics** (7 fields):
- `agg_bqx_return`: Return over longest window (75 min)
- `agg_bqx_max`, `agg_bqx_min`, `agg_bqx_avg`, `agg_bqx_stdev`
- `agg_bqx_range`: max - min
- `agg_bqx_volatility`: stdev / avg (normalized)

**Key Difference from FWD**:
- FWD windows: 60, 90, 150, 240, 390, 630 minutes (medium to long-term)
- BQX windows: 15, 30, 45, 60, 75 minutes (ultra-short to short-term)
- **BQX focuses on recent momentum** (last 15-75 min) vs FWD's longer outlook

---

## 4. Feature Engineering Strategy for BQX

### Feature Categories

**From**: `PHASE2_FEATURE_ENGINEERING_DESIGN.md` + BQX adaptation

**BQX ML Feature Set** (~120+ total features per pair):

#### A. BQX Window Features (37 features)
- 30 window metrics (5 windows × 6 metrics)
- 7 aggregate metrics
- **Purpose**: Capture recent backward momentum patterns

#### B. REG Pattern Features (~42 features)
- 6 windows (60, 90, 150, 240, 390, 630 min)
- 7 metrics per window (slope, intercept, r², quad_a, quad_b, quad_c, quad_norm)
- **Purpose**: Capture medium-term regression patterns

#### C. Lagged BQX Features (~12 features)
- BQX values at t-60, t-120, t-180 (autoregressive features)
- **Purpose**: Use past BQX to predict future BQX
- **CRITICAL**: Respect 61-minute lag rule (no overlap)

#### D. Derived Momentum Features (~20 features)
- Momentum alignment: Count of aligned window directions
- Volatility regime: Low, medium, high classification
- Multi-timeframe divergence: Divergence between windows
- **Purpose**: Higher-level patterns from raw BQX data

#### E. Statistical Features (~15 features)
- Rolling statistics over safe windows
- Trend indicators
- Volatility measures
- **Purpose**: Temporal dynamics of BQX patterns

**Total**: ~120+ features (vs FWD's similar count, but fundamentally different source)

### Feature Selection

**From**: `PHASE2_FEATURE_ENGINEERING_DESIGN.md`

**User Expectation**: Top 50 features per pair (after selection)

**Selection Methods**:
1. Mutual Information (non-linear relationships)
2. Correlation with target
3. Random Forest importance
4. XGBoost SHAP values
5. Lasso L1 regularization

**Ensemble Ranking**: Borda count aggregation across 5 methods

---

## 5. ML Architecture & Training

### Model Architectures

**From**: `BQX_ML_MASTERPLAN_EXECUTIVE_SUMMARY.md` + `BQX_ML_MASTERPLAN_GAPS_ANALYSIS.md`

**User Expectation**: 6 SOTA architectures (reduced to realistic approach)

**Original Plan** (6 architectures):
1. Temporal Fusion Transformer (TFT) - ✅ Available
2. Informer - ❌ Needs implementation
3. Autoformer - ❌ Needs implementation
4. FEDformer - ❌ Needs implementation
5. PatchTST - ❌ Needs implementation
6. TimesNet - ❌ Needs implementation

**Recommended for BQX ML MVP**:
- **Phase 1**: TFT only (R² = 0.88-0.92)
- **If successful**: Add LSTM, GRU (R² = 0.90-0.94)
- **Post-production**: Implement remaining architectures incrementally

**BQX-Specific Training**:
```python
# Autoregressive prediction task
Features: [BQX_t, REG_t, BQX_{t-60}, BQX_{t-120}]
Target: BQX_{t+60}

# Example for EURUSD at 11:00 AM:
X = {
    'w15_bqx_return': 0.0002,      # Current 15-min momentum
    'w30_bqx_return': 0.0005,      # Current 30-min momentum
    'w60_bqx_return': 0.0012,      # Current 60-min momentum
    'w75_bqx_return': 0.0015,      # Current 75-min momentum
    'w60_slope': 0.00001,          # REG pattern
    'bqx_lag_60': 0.0010,          # BQX 60 min ago (at 10:00)
    ... (120+ features)
}

y = BQX_{11:60} = 0.0018           # BQX value at 12:00 (future)
```

### Training Strategy

**From**: Masterplan + Gaps Analysis

**Phase 4 Training (Weeks 1-3)**:

**Week 1: Architecture Selection**
- Train EURUSD + 3 major pairs (GBPUSD, USDJPY, EURJPY)
- Test TFT (and optionally LSTM, GRU if time allows)
- Identify best architecture by R² performance
- **Expected**: TFT R² > 0.88

**Week 2: Scale to All Pairs**
- Train best architecture(s) × 28 pairs = 28-84 models
- Parallel execution: 12 training jobs concurrently
- **Expected**: Individual model R² > 0.88

**Week 3: Ensemble Creation**
- For each pair, create weighted ensemble of top models
- Optimize weights using validation set
- **Target**: Ensemble R² > 0.95

**BQX-Specific Hyperparameters** (from gaps analysis):
```yaml
tft:
  learning_rate: [0.0001, 0.01]        # Log uniform
  hidden_size: [64, 128, 256]          # Categorical
  attention_head_size: [1, 2, 4]       # Categorical
  dropout: [0.1, 0.3]                  # Uniform
  batch_size: [128, 256, 512]          # Categorical
  max_epochs: [50, 200]                # With early stopping
```

### Evaluation Metrics

**User Expectation**: Multi-metric validation (not just R²)

**Regression Metrics**:
- R² (primary)
- RMSE
- MAE
- MAPE

**Directional Metrics**:
- Directional Accuracy (should be > 52-55%)
- Hit Rate

**Trading Metrics**:
- Sharpe Ratio
- Sortino Ratio
- Maximum Drawdown
- Profit Factor

**Quality Gates**:
- R² > 0.85 (minimum)
- Directional Accuracy > 0.55 (better than random + edge)
- Std dev ratio 0.8-1.2 (predictions match actual variance)
- Mean error < 0.0001 (no systematic bias)

---

## 6. Production Deployment

### Real-Time Inference Pipeline

**From**: `BQX_ML_MASTERPLAN_EXECUTIVE_SUMMARY.md` + Gaps Analysis

**User Expectation**: <100ms API latency

**BQX-Specific Challenge**: Calculate features in real-time

**Solution**: Redis caching layer (from gaps analysis)

```python
# Background worker (runs every 60 seconds)
def calculate_and_cache_bqx_features():
    for pair in pairs_28:
        # Query latest 75 minutes of M1 data from Aurora
        df = query_latest_data(pair, minutes=75)

        # Calculate BQX metrics (15, 30, 45, 60, 75 min windows)
        bqx_features = calculate_bqx_windows(df)

        # Calculate REG features (needs 630 min history)
        reg_features = query_reg_features(pair)

        # Combine
        features = {**bqx_features, **reg_features}

        # Cache in Redis (5-min TTL)
        redis.setex(f"bqx_features:{pair}", 300, json.dumps(features))

# API endpoint
def predict(pair, timestamp):
    # Read from cache (latency: <5ms)
    cached_features = redis.get(f"bqx_features:{pair}")

    if cached_features:
        features = json.loads(cached_features)
    else:
        # Fallback to real-time calculation (~200ms)
        features = calculate_features_realtime(pair, timestamp)

    # Invoke SageMaker endpoint
    prediction = sagemaker_endpoint.predict(features)
    return prediction
```

**Architecture Components**:
- Redis ElastiCache cluster ($15/month)
- Background worker Lambda (runs every 1 minute)
- SageMaker multi-model endpoint (all 28 pairs)
- API Gateway + Lambda (REST API)

### API Specification

**From**: Masterplan

```http
POST /predict
Authorization: Bearer <API_KEY>

Request:
{
  "pair": "EURUSD",
  "timestamp": "2025-11-09T14:30:00Z"
}

Response:
{
  "pair": "EURUSD",
  "timestamp": "2025-11-09T14:30:00Z",
  "current_rate": 1.08543,
  "predicted_bqx_t60": 0.00074,          # Predicted BQX value 60 min ahead
  "predicted_rate_t60": 1.08551,         # Derived future rate
  "confidence_r2": 0.96,
  "model_version": "tft-ensemble-v1.2",
  "latency_ms": 45
}
```

**BQX-Specific**: Prediction returns `predicted_bqx_t60` (autoregressive prediction of future BQX value)

---

## 7. Data Storage & Format

### Training Data Export

**From**: Gaps Analysis

**User Expectation**: Parquet files in S3, formatted for time series models

**BQX-Specific Format**:
```python
# Export structure
df_schema = {
    'time_idx': int,           # Sequential index (0, 1, 2, ...)
    'group_id': str,           # Pair identifier ('eurusd', 'gbpusd', ...)
    'date': datetime,          # Timestamp

    # BQX features (37 features)
    'w15_bqx_return': float,
    'w15_bqx_max': float,
    ... (30 more BQX window features)
    'agg_bqx_return': float,
    ... (7 aggregate features)

    # REG features (~42 features)
    'w60_slope': float,
    'w60_r2': float,
    ... (40 more REG features)

    # Lagged BQX features (~12 features)
    'bqx_lag_60': float,
    'bqx_lag_120': float,
    'bqx_lag_180': float,

    # Derived features (~20 features)
    'momentum_alignment': int,
    'volatility_regime': str,
    ...

    # Target (autoregressive)
    'target_bqx_t60': float    # BQX value 60 minutes ahead
}
```

**Feature Scaling** (CRITICAL):
```python
from sklearn.preprocessing import StandardScaler

# Scale all features (neural networks require normalization)
feature_cols = [col for col in df.columns if col not in ['time_idx', 'group_id', 'date', 'target_bqx_t60']]
scaler = StandardScaler()
df[feature_cols] = scaler.fit_transform(df[feature_cols])

# Save scaler for inference (MUST use same scaler at prediction time)
joblib.dump(scaler, f's3://bqx-ml-models/scalers/{pair}_scaler.pkl')
```

**Data Splits**:
- Training: 2024-07 to 2024-12 (6 months)
- Validation: 2025-01 to 2025-03 (3 months)
- Test: 2025-04 to 2025-06 (3 months)

**Storage Location**:
```
s3://bqx-ml-features/
├── eurusd/
│   ├── train/
│   │   └── data.parquet
│   ├── val/
│   │   └── data.parquet
│   └── test/
│       └── data.parquet
├── gbpusd/
│   └── ...
... (28 pairs total)
```

**Expected Size**: ~500 GB total (28 pairs × ~18 GB each)

---

## 8. Cost & Timeline

### Budget

**From**: Masterplan + Gaps Analysis

**One-Time Costs**:
- Phase 2 (Data foundation): $100
- Phase 3 (ML infrastructure): $150
- Phase 4 (Model training): $1,040 (with spot instances)
- Phase 5 (Deployment): $50
- **Total One-Time**: $1,340

**Recurring Costs** (Monthly):
- Aurora database: $159 (shared with bqx-db)
- S3 storage: $13 (training data + models)
- SageMaker multi-model endpoint: $116
- API Gateway + Lambda: $50
- Monitoring (QuickSight): $50
- Redis ElastiCache: $15 (for BQX feature caching)
- Retraining compute: $100
- Airtable: $10
- Secrets Manager: $1
- **Total Recurring**: $544/month

**Grand Total**:
- First Month: $1,340 + $544 = $1,884
- Months 2+: $544/month

### Timeline

**From**: Masterplan + Gaps Analysis (with critical fixes)

**Recommended Path**: TFT-only + critical fixes

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **Pre-Start** | 1 day | VPC connectivity, regression table validation |
| **Phase 0** | 3 days | GitHub, Airtable, SageMaker setup |
| **Phase 1** | 2 days | Context migration |
| **Phase 2** | 12 days | BQX data complete, features exported to S3 |
| **Phase 3** | 8 days | TFT implemented, proof-of-concept R² > 0.88 |
| **Phase 4** | 17 days | 28 TFT models trained, ensemble R² > 0.95 |
| **Phase 5** | 7 days | Production API live, <100ms latency |
| **Phase 6** | 3 days | Monitoring active, automated retraining |
| **TOTAL** | **53 days** | Production-ready BQX ML system |

**Note**: BQX data backfill is currently in progress (33.9% complete as of report time)

---

## 9. Key Differences: BQX ML vs FWD-Based ML

### Why BQX is Superior to FWD

| Aspect | FWD (Deprecated) | BQX (Current) |
|--------|------------------|---------------|
| **Data Direction** | Forward-looking | Backward-looking |
| **Formula** | `(rate[t+60] - rate[t]) / rate[t]` | `Σ(rate[t-i] - rate[t]) / rate[t]` |
| **Real-Time Deployable** | ❌ No (needs future data) | ✅ Yes (uses only past data) |
| **Temporal Causality** | ❌ Violates (uses future) | ✅ Safe (uses only past) |
| **Windows** | 60, 90, 150, 240, 390, 630 min | 15, 30, 45, 60, 75 min |
| **Focus** | Medium to long-term | Ultra-short to short-term |
| **Prediction Task** | FWD_t (requires t+60 data) | BQX_{t+60} (observable) |
| **Mathematical Equivalence** | FWD_t ≈ BQX_{t+60} | BQX_{t+60} ≈ FWD_t |
| **Edge Effect** | End of dataset (can't predict last 60 min) | Start of dataset (first 75 min NULL) |
| **ML Role** | Targets only (Y variable) | Both features (X) and targets (Y) |
| **Validation** | ❌ Can't validate in real-time | ✅ Can validate immediately |
| **Database Status** | ❌ DELETED from Aurora | ✅ Active, populating |

**User's Strategic Decision**: Migrate from FWD to BQX for real-time deployment capability

---

## 10. Critical Success Criteria

### Phase Completion Criteria

**From**: Masterplan

**Phase 2 Success** (BQX Data Foundation):
- ✅ BQX tables populated (12 months of data)
- ✅ ~370K rows per pair × 28 pairs = 10.4M total rows
- ✅ All 40 fields per row
- ✅ No NULLs in row 75+ (edge effects handled correctly)
- ✅ Exported to S3 Parquet (~500 GB)
- ✅ Data validated (no anomalies, no data leakage)

**Phase 3 Success** (ML Infrastructure):
- ✅ Proof-of-concept EURUSD R² > 0.85 (using BQX features)
- ✅ TFT architecture implemented
- ✅ Experiment tracking functional (Airtable integration)

**Phase 4 Success** (Model Training):
- ✅ 28 TFT models trained (1 per pair)
- ✅ Individual model R² > 0.88
- ✅ **Ensemble R² > 0.95** ← CRITICAL GOAL

**Phase 5 Success** (Production API):
- ✅ Production API live (<100ms latency)
- ✅ All 28 pairs accessible via `/predict` endpoint
- ✅ BQX feature caching operational (Redis)
- ✅ Model Monitor active (drift detection)

**Phase 6 Success** (Monitoring):
- ✅ Automated retraining functional (weekly + drift-triggered)
- ✅ Performance dashboard tracking R² drift
- ✅ Operational cost <$600/month

### Ultimate Success Metric

**R² → 1.0 Trajectory**:
- Month 1: R² = 0.95 (initial ensemble)
- Month 3: R² = 0.96 (retraining + new features)
- Month 6: R² = 0.97 (advanced techniques)
- Month 12: R² = 0.98+ (approaching theoretical limit)

**User Acknowledgement**: R² = 1.0 is aspirational, but **R² > 0.95 is world-class** and production-ready.

---

## 11. Implementation Requirements for BQX ML

### Database Access

**Aurora Connection**:
```python
DB_CONFIG = {
    'host': 'trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com',
    'port': 5432,
    'database': 'bqx',
    'user': 'postgres',
    'password': get_secret('trillium/aurora/bqx-connection'),
    'sslmode': 'require'
}
```

### Feature Extraction Query Template

```sql
-- Extract BQX features for EURUSD
SELECT
    b.ts_utc,
    b.rate,

    -- BQX window features (30 fields)
    b.w15_bqx_return, b.w15_bqx_max, b.w15_bqx_min,
    b.w15_bqx_avg, b.w15_bqx_stdev, b.w15_bqx_endpoint,
    b.w30_bqx_return, ... (continue for all 5 windows)

    -- BQX aggregate features (7 fields)
    b.agg_bqx_return, b.agg_bqx_max, b.agg_bqx_min,
    b.agg_bqx_avg, b.agg_bqx_stdev, b.agg_bqx_range,
    b.agg_bqx_volatility,

    -- REG pattern features (42 fields)
    r.w60_slope, r.w60_intercept, r.w60_r2,
    r.w60_quad_a, r.w60_quad_b, r.w60_quad_c, r.w60_quad_norm,
    ... (continue for all 6 REG windows)

    -- Target (autoregressive)
    LEAD(b.w60_bqx_return, 60) OVER (ORDER BY b.ts_utc) as target_bqx_t60

FROM bqx.bqx_eurusd b
JOIN bqx.reg_eurusd r ON b.ts_utc = r.time
WHERE b.ts_utc >= '2024-07-01' AND b.ts_utc < '2025-07-01'
  AND b.w75_bqx_return IS NOT NULL  -- Exclude edge effects
ORDER BY b.ts_utc;
```

### Model Training Template (BQX-Specific)

```python
from pytorch_forecasting import TemporalFusionTransformer

# Prepare BQX data
training_data = TimeSeriesDataSet(
    df,
    time_idx="time_idx",
    target="target_bqx_t60",           # Autoregressive BQX prediction
    group_ids=["pair"],

    # All BQX features as time-varying
    time_varying_unknown_reals=[
        "w15_bqx_return", "w30_bqx_return", "w60_bqx_return", "w75_bqx_return",
        "w60_slope", "w60_r2", "w60_quad_norm",
        ... (120+ features)
    ],

    max_encoder_length=60,             # Use last 60 minutes
    max_prediction_length=1,           # Predict 1 step ahead (t+60)

    # Feature scaling
    scalers={
        col: StandardScaler() for col in feature_cols
    }
)

# Train TFT
tft = TemporalFusionTransformer.from_dataset(
    training_data,
    learning_rate=0.001,
    hidden_size=128,
    attention_head_size=4,
    dropout=0.2,
    hidden_continuous_size=64,
    output_size=7,  # Quantiles for uncertainty
    loss=QuantileLoss(),
    log_interval=100
)

# Train with early stopping
trainer = pl.Trainer(
    max_epochs=200,
    callbacks=[
        EarlyStopping(monitor="val_loss", patience=10, mode="min"),
        ModelCheckpoint(monitor="val_r2", mode="max", save_top_k=3)
    ]
)

trainer.fit(tft, train_dataloader, val_dataloader)

# Evaluate
predictions = tft.predict(test_dataloader)
r2 = r2_score(actuals, predictions)
print(f"Test R²: {r2:.3f}")  # Target: > 0.88
```

---

## 12. Materialized Views (BQX-Based) - TODO

### Current Status

**From**: Our work + bqx-db comparison doc

**Problem**:
- Original MVs included FWD columns (28 materialized views CASCADE deleted when FWD tables dropped)
- Need to recreate MVs with BQX schema (no FWD references)

**New MV Schema** (proposed):
```sql
CREATE MATERIALIZED VIEW bqx.mv_eurusd_merged AS
SELECT
    m.time as ts_utc,
    m.close as rate,

    -- M1 data (6 fields)
    m.open, m.high, m.low, m.close, m.volume,

    -- REG features (42 fields)
    r.w60_slope, r.w60_r2, ... (all 6 windows × 7 metrics)

    -- BQX features (37 fields)
    b.w15_bqx_return, b.w30_bqx_return, b.w60_bqx_return, b.w75_bqx_return,
    b.agg_bqx_return, b.agg_bqx_volatility, ... (all BQX features)

FROM bqx.m1_eurusd m
JOIN bqx.reg_eurusd r ON m.time = r.time
JOIN bqx.bqx_eurusd b ON m.time = b.ts_utc;

CREATE INDEX idx_mv_eurusd_merged_ts ON bqx.mv_eurusd_merged(ts_utc);
```

**Total Fields**: ~85 per MV (6 M1 + 42 REG + 37 BQX)

**User Expectation**:
- 28 MVs (1 per pair)
- Auto-refresh on M1/REG/BQX data updates
- Primary interface for ML feature extraction

---

## Summary: Core BQX ML Expectations

### 1. **Use BQX (backward) data, NOT FWD (forward) data**
   - BQX tables are the foundation
   - All features backward-looking
   - Real-time deployment capable

### 2. **Achieve R² > 0.95 (ensemble target)**
   - Single TFT model: R² > 0.88 minimum
   - Ensemble of 3+ models: R² > 0.95 goal
   - Long-term trajectory toward R² → 1.0

### 3. **Autoregressive prediction task**
   - Predict: `BQX_{t+60}` (future BQX value)
   - Using: `BQX_t + REG_t + BQX_{t-61}` (current + lagged features)
   - Mathematically equivalent to predicting FWD_t

### 4. **Enforce 61-minute lag rule**
   - Features: All data ≤ T (backward-looking, safe)
   - Lagged BQX features: Data ≤ T-61 (no overlap)
   - Never use data from T-60 to T (temporal causality violation)

### 5. **Production API <100ms latency**
   - Redis caching layer for BQX features
   - SageMaker multi-model endpoint
   - API Gateway + Lambda
   - Real-time feature calculation

### 6. **Complete in 53 days, $1,340 one-time + $544/month**
   - Currently in Phase 2 (BQX data backfill 33.9% complete)
   - TFT-only approach (fastest to production)
   - Can add more architectures post-launch

### 7. **28 forex pairs, 120+ features per pair**
   - BQX features: 37 (15/30/45/60/75 min windows)
   - REG features: 42 (60-630 min patterns)
   - Lagged + derived: 40+
   - After feature selection: Top 50 per pair

### 8. **Recreate materialized views with BQX schema**
   - 28 MVs (M1 + REG + BQX)
   - No FWD references
   - Primary data interface for ML

---

**Status**: BQX ML expectations extracted and documented.
**Next Step**: Implement feature extraction pipeline from BQX tables when backfill completes.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-09
**Source Analysis**: bqx-db repository (Schmidtlappin/bqx-db)
