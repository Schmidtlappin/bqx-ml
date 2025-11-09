# BQX ML System Architecture

## Overview

BQX ML is an autoregressive forex prediction system that uses backward-looking momentum features (BQX) to predict future price movements. The system is designed for real-time deployment and leverages Aurora PostgreSQL for feature storage.

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         Data Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  M1 Tables   │  │  BQX Tables  │  │  REG Tables  │         │
│  │              │  │              │  │              │         │
│  │ 1-min OHLC   │  │ Backward     │  │ Regression   │         │
│  │ Source data  │  │ Momentum     │  │ Patterns     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         Aurora PostgreSQL (trillium-bqx-cluster)               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Feature Pipeline                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Extraction   │→ │ Engineering  │→ │ Selection    │         │
│  │              │  │              │  │              │         │
│  │ SQL queries  │  │ Lags,        │  │ Correlation, │         │
│  │ from Aurora  │  │ Derived,     │  │ Importance   │         │
│  └──────────────┘  │ Scaling      │  └──────────────┘         │
│                     └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       ML Models                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Baseline    │  │ Hierarchical │  │   Ensemble   │         │
│  │              │  │              │  │              │         │
│  │ Single       │  │ Multi-       │  │ Weighted     │         │
│  │ Horizon      │  │ Horizon      │  │ Combination  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Inference & Deployment                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Real-time    │  │  Backtesting │  │  Monitoring  │         │
│  │ Prediction   │  │              │  │              │         │
│  │ Service      │  │ Walk-forward │  │ Performance  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Raw Data (M1 Tables)
- **Source**: 1-minute OHLC forex bars
- **Storage**: `bqx.m1_{pair}` tables in Aurora
- **Update**: Real-time ingestion from forex data provider
- **Volume**: ~525,000 rows/pair/year

### 2. Feature Tables

#### BQX Tables (Backward Momentum)
- **Computation**: Backward-looking cumulative returns
- **Windows**: 15, 30, 45, 60, 75 minutes
- **Formula**: `Σ(i=1 to W)[rate(t-i) - rate(t)] / rate(t)`
- **Storage**: `bqx.bqx_{pair}` tables
- **Update**: Computed from M1 data via backward_worker.py
- **Size**: 40 fields × 370K rows/pair = ~15 MB/pair

#### REG Tables (Regression Features)
- **Computation**: Linear/quadratic regression over windows
- **Windows**: 60, 90, 150, 240, 390, 630 minutes
- **Metrics**: slope, intercept, r², quadratic coefficients
- **Storage**: `bqx.reg_{pair}` tables
- **Update**: Computed from M1 data via regression_worker.py

### 3. Feature Engineering

```python
# Pseudocode
features = []

# Load raw features
bqx = extract_bqx(pair, start_date, end_date)
reg = extract_reg(pair, start_date, end_date)

# Create lagged features
bqx_lag_60 = bqx.shift(60)  # BQX values 60 minutes ago
bqx_lag_120 = bqx.shift(120)

# Derived features
momentum_alignment = count_aligned_windows(bqx)
volatility_regime = classify_volatility(bqx.agg_bqx_stdev)

# Combine
X = concat([bqx, reg, bqx_lag_60, bqx_lag_120, derived])

# Create target (autoregressive)
y = bqx.w60_bqx_return.shift(-60)  # Future BQX value
```

### 4. Training Pipeline

```
┌─────────────────────────────────────────────────────┐
│ Historical Data (2024-07 to 2025-06)                │
└─────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│ Split: Train (6mo) | Validation (3mo) | Test (3mo) │
└─────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│ Feature Engineering                                  │
│ • Lagged BQX features                               │
│ • Derived momentum features                         │
│ • Feature selection (top 50)                        │
│ • Scaling (StandardScaler)                          │
└─────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│ Model Training                                       │
│ • Hyperparameter tuning (RandomizedSearchCV)        │
│ • Cross-validation (TimeSeriesSplit)                │
│ • Model persistence (joblib)                        │
└─────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│ Evaluation                                           │
│ • Regression metrics (MAE, RMSE, R²)                │
│ • Directional accuracy                              │
│ • Trading metrics (Sharpe, drawdown)                │
└─────────────────────────────────────────────────────┘
```

## Autoregressive Strategy

### Traditional Approach (Problematic)
```
Time t:
  Features: [BQX_t, REG_t]
  Target: FWD_t

Problem: FWD_t requires future data (t to t+60)
         Not observable in real-time
```

### BQX ML Approach (Solution)
```
Time t:
  Features: [BQX_t, REG_t]
  Target: BQX_{t+60}

Advantage: BQX_{t+60} ≈ FWD_t mathematically
           All features observable at time t
           Prediction validates in real-time
```

### Mathematical Equivalence

```
FWD_t = Σ(i=1 to 60)[rate(t) - rate(t+i)] / rate(t)
      ≈ Σ(i=1 to 60)[rate(t+60-i) - rate(t+60)] / rate(t+60)
      = BQX_{t+60}

Both measure price movement from t to t+60
```

## Real-time Inference

### Prediction Service Flow

```
1. Extract latest features from Aurora
   ├─ BQX_t (current backward momentum)
   ├─ REG_t (current regression patterns)
   └─ BQX_{t-60}, BQX_{t-120} (lagged)

2. Engineer features
   ├─ Derived momentum alignment
   ├─ Volatility regime classification
   └─ Feature scaling

3. Load trained model
   └─ model.pkl from S3 or local storage

4. Generate prediction
   └─ BQX_{t+60} prediction

5. Convert to trading signal
   ├─ If BQX_{t+60} > threshold: BUY
   ├─ If BQX_{t+60} < -threshold: SELL
   └─ Otherwise: HOLD

6. Return prediction + confidence interval
```

### Latency Requirements

- **Feature extraction**: < 100ms
- **Feature engineering**: < 50ms
- **Model inference**: < 50ms
- **Total latency**: < 200ms

## Deployment Architecture

### Option 1: Lambda + Aurora
```
API Gateway → Lambda → Aurora RDS → S3 (models)
```
- Serverless, auto-scaling
- Pay-per-request
- Cold start: 1-2 seconds

### Option 2: ECS + Aurora
```
ALB → ECS Fargate → Aurora RDS → S3 (models)
```
- Always warm, low latency
- Fixed cost
- Better for high-frequency predictions

### Option 3: EC2 + Local Cache
```
Client → EC2 instance → Aurora (periodic sync) → Local Redis cache
```
- Lowest latency (~50ms total)
- Model cached in memory
- Features cached in Redis (5-min TTL)

## Monitoring & Observability

### Metrics to Track

**Model Performance**:
- Prediction MAE/RMSE (drift detection)
- Directional accuracy (should stay > 52%)
- Feature distribution shifts

**System Performance**:
- Inference latency (p50, p95, p99)
- Aurora query time
- Cache hit rate

**Trading Performance**:
- Sharpe ratio (rolling 30 days)
- Win rate
- Maximum drawdown

### Alerting

- MAE drift > 20% from baseline → retrain model
- Directional accuracy < 50% → investigate data quality
- Inference latency > 500ms → scale resources

## Security

### Data Access
- Aurora credentials in AWS Secrets Manager
- IAM roles for service-to-service auth
- SSL/TLS for all connections

### Model Security
- Models versioned and stored in S3
- Checksums verified before loading
- No direct internet access from inference service

## Scalability

### Current Scale
- 28 forex pairs
- 1-minute resolution
- 370K rows/pair (12 months)
- ~10M total rows

### Future Scale (1 year)
- 28 pairs × 525K rows/year = 14.7M rows/year
- Query optimization: partition by month
- Read replicas for inference
- Cache frequent queries (last 24 hours)

## Disaster Recovery

### Backups
- Aurora automated backups (7-day retention)
- Manual snapshots before major changes
- Model artifacts versioned in S3 (versioning enabled)

### Recovery
- Point-in-time restore (Aurora)
- Redeploy from S3 (models)
- Rebuild features from M1 tables if needed

---

**Last Updated**: 2025-11-09
