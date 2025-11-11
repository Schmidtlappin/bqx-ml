# BQX ML SageMaker Architecture

**Version:** 1.0
**Date:** 2025-01-11
**Status:** Production Architecture Design

---

## Overview

This document describes the production architecture for the BQX ML system built on AWS SageMaker. The architecture supports real-time predictions for 28 forex pairs with <200ms latency, automated retraining, and comprehensive monitoring.

---

## System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER (Aurora PostgreSQL)                    │
│                                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │  BQX Tables  │  │  REG Tables  │  │Feature Tables│                   │
│  │  (40 feat)   │  │  (57 feat)   │  │  (131 feat)  │                   │
│  │   28 pairs   │  │   28 pairs   │  │   28 pairs   │                   │
│  │ 336 partitions│  │ 336 partitions│  │ 336 partitions│                   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                   │
│         │                  │                  │                            │
│         └──────────────────┴──────────────────┘                            │
│                            │                                                │
│                    228 Base Features                                       │
└────────────────────────────┼──────────────────────────────────────────────┘
                             │
                             ↓
┌──────────────────────────────────────────────────────────────────────────┐
│                      TRAINING PIPELINE (SageMaker)                        │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  STAGE 1: Feature Engineering (Processing Job)                      │  │
│  │  ┌─────────────────────────────────────────────────────────────┐   │  │
│  │  │  Aurora Query → Feature Engineering → Lagging → Causality   │   │  │
│  │  │  228 base → Apply 4 lags → Add causality → 809 features     │   │  │
│  │  └─────────────────────────┬───────────────────────────────────┘   │  │
│  │                            ↓                                         │  │
│  │                    S3: train.parquet                                 │  │
│  │                    (809 features × N samples)                        │  │
│  └────────────────────────────┬─────────────────────────────────────────┘  │
│                               ↓                                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  STAGE 2: Feature Selection                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────┐   │  │
│  │  │  Train RF on 809 → Compute importance → Select top 70       │   │  │
│  │  └─────────────────────────┬───────────────────────────────────┘   │  │
│  │                            ↓                                         │  │
│  │                    S3: selected_features.json                        │  │
│  │                    (70 feature names)                                │  │
│  └────────────────────────────┬─────────────────────────────────────────┘  │
│                               ↓                                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  STAGE 3: Model Training (28 parallel jobs)                         │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       ┌──────────┐     │  │
│  │  │ EURUSD   │  │ GBPUSD   │  │ USDJPY   │  ...  │ AUDCAD   │     │  │
│  │  │   Job    │  │   Job    │  │   Job    │       │   Job    │     │  │
│  │  │ (5 min)  │  │ (5 min)  │  │ (5 min)  │       │ (5 min)  │     │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘       └────┬─────┘     │  │
│  │       │             │             │                    │            │  │
│  │       └─────────────┴─────────────┴────────────────────┘            │  │
│  │                            ↓                                         │  │
│  │                    S3: model.tar.gz × 28                             │  │
│  │                    (model + scaler + selected_features.json)         │  │
│  └────────────────────────────┬─────────────────────────────────────────┘  │
│                               ↓                                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  STAGE 4: Model Registry                                            │  │
│  │  ┌─────────────────────────────────────────────────────────────┐   │  │
│  │  │  Register 28 models → Approval workflow → Production tag    │   │  │
│  │  └─────────────────────────────────────────────────────────────┘   │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
                             │
                             ↓
┌──────────────────────────────────────────────────────────────────────────┐
│                     INFERENCE SYSTEM (SageMaker)                          │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  Multi-Model Endpoint                                               │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │  Instance: ml.m5.xlarge (4 vCPU, 16 GB RAM)                   │  │  │
│  │  │  ┌────────┐  ┌────────┐  ┌────────┐       ┌────────┐         │  │  │
│  │  │  │ EURUSD │  │ GBPUSD │  │ USDJPY │  ...  │ AUDCAD │         │  │  │
│  │  │  │ Model  │  │ Model  │  │ Model  │       │ Model  │         │  │  │
│  │  │  │ (50MB) │  │ (50MB) │  │ (50MB) │       │ (50MB) │         │  │  │
│  │  │  └────────┘  └────────┘  └────────┘       └────────┘         │  │  │
│  │  │                                                                 │  │  │
│  │  │  LRU Cache: On-demand loading, keep 10 most recent            │  │  │
│  │  │  Latency: ~10ms inference (after model loaded)                │  │  │
│  │  └──────────────────────────────────────────────────────────────┘  │  │
│  │                                                                      │  │
│  │  Auto-Scaling: 1-4 instances                                        │  │
│  │  Target: 400 invocations/minute per instance                        │  │
│  └────────────────────────────┬─────────────────────────────────────────┘  │
└────────────────────────────────┼──────────────────────────────────────────┘
                                │
                                ↓
┌──────────────────────────────────────────────────────────────────────────┐
│                        PREDICTION API (Lambda + API Gateway)              │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  API Gateway: /predict (POST)                                       │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │  Authentication: API Key                                       │  │  │
│  │  │  Throttling: 100 req/sec                                       │  │  │
│  │  │  Request: {"pair": "eurusd", "timestamp": "2025-01-11T10:00"}│  │  │
│  │  └─────────────────────────┬────────────────────────────────────┘  │  │
│  │                            ↓                                         │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │  Prediction Lambda                                              │  │  │
│  │  │  ┌──────────────────────────────────────────────────────────┐ │  │  │
│  │  │  │  1. Call Feature Extraction Lambda                        │ │  │  │
│  │  │  │  2. Apply feature selection (filter to 70 features)       │ │  │  │
│  │  │  │  3. Invoke SageMaker endpoint                             │ │  │  │
│  │  │  │  4. Generate trading signal                               │ │  │  │
│  │  │  │  5. Return prediction + signal + metadata                 │ │  │  │
│  │  │  └──────────────────────────────────────────────────────────┘ │  │  │
│  │  └────────────────────────┬───────────────────────────────────────┘  │  │
│  │                            ↓                                         │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │  Feature Extraction Lambda                                      │  │  │
│  │  │  ┌──────────────────────────────────────────────────────────┐ │  │  │
│  │  │  │  1. Query Aurora (BQX + REG + Feature tables)            │ │  │  │
│  │  │  │     → 228 base features                                   │ │  │  │
│  │  │  │  2. Apply lagging (4 windows)                            │ │  │  │
│  │  │  │     → 710 lagged features                                 │ │  │  │
│  │  │  │  3. Apply temporal causality (61-min lag)                │ │  │  │
│  │  │  │     → 13 causality features                               │ │  │  │
│  │  │  │  4. Add non-lagged features                              │ │  │  │
│  │  │  │     → 86 features                                         │ │  │  │
│  │  │  │  5. Return 809 features                                  │ │  │  │
│  │  │  └──────────────────────────────────────────────────────────┘ │  │  │
│  │  │  Latency: <100ms (with connection pooling)                   │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  Response:                                                                 │
│  {                                                                         │
│    "pair": "eurusd",                                                      │
│    "prediction": 0.00043,  // BQX value at t+60                           │
│    "confidence_interval": [0.00035, 0.00051],                            │
│    "signal": "BUY",  // BUY/SELL/HOLD                                    │
│    "signal_strength": 0.75,                                               │
│    "features_used": 70,                                                   │
│    "model_version": "v1.2.3",                                             │
│    "latency_ms": 185                                                      │
│  }                                                                         │
└──────────────────────────────────────────────────────────────────────────┘
                                │
                                ↓
┌──────────────────────────────────────────────────────────────────────────┐
│                      MONITORING & MLOPS (CloudWatch + SNS)                │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  SageMaker Model Monitor                                            │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │  Data Quality Monitor (Hourly)                                │  │  │
│  │  │  - Baseline: 70 feature statistics                            │  │  │
│  │  │  - Check: Mean, std, percentiles vs baseline                  │  │  │
│  │  │  - Alert: Feature drift (KL > 0.1)                            │  │  │
│  │  └──────────────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │  Model Quality Monitor (Daily)                                │  │  │
│  │  │  - Compare predictions vs actuals                             │  │  │
│  │  │  - Track R², MAE, directional accuracy                        │  │  │
│  │  │  - Alert: R² drop > 0.05                                      │  │  │
│  │  └──────────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────┬─────────────────────────────────────────┘  │
│                               ↓                                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  CloudWatch Dashboard                                               │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │  │
│  │  │ Invocations│  │  Latency   │  │ Error Rate │  │  R² Score  │  │  │
│  │  │  /minute   │  │ P50/95/99  │  │   (%)      │  │  (rolling) │  │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │  │
│  │  ┌────────────┐  ┌────────────┐                                    │  │
│  │  │Feature Drift│ │Auto-Scaling│                                    │  │
│  │  │   Status   │  │  Activity  │                                    │  │
│  │  └────────────┘  └────────────┘                                    │  │
│  └────────────────────────────┬─────────────────────────────────────────┘  │
│                               ↓                                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  Alerting System (SNS → Slack)                                      │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │  Critical Alarms:                                             │  │  │
│  │  │  - Error rate > 5%                                            │  │  │
│  │  │  - Training job failure                                       │  │  │
│  │  │  - R² drop > 0.05                                             │  │  │
│  │  │                                                                │  │  │
│  │  │  Warning Alarms:                                              │  │  │
│  │  │  - Latency P99 > 500ms                                        │  │  │
│  │  │  - Feature drift detected                                     │  │  │
│  │  │  - Cost > $400/month                                          │  │  │
│  │  └──────────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────┬─────────────────────────────────────────┘  │
│                               ↓                                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  Automated Retraining Trigger                                       │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │  Conditions:                                                   │  │  │
│  │  │  - R² drop > 0.05 (weekly check)                              │  │  │
│  │  │  - Feature drift KL > 0.3 (daily check)                       │  │  │
│  │  │  - Monthly scheduled retrain                                  │  │  │
│  │  │                                                                │  │  │
│  │  │  Action:                                                       │  │  │
│  │  │  - Trigger training pipeline                                  │  │  │
│  │  │  - Use latest 6 months of data                                │  │  │
│  │  │  - Register new models                                        │  │  │
│  │  │  - Deploy with blue/green                                     │  │  │
│  │  └──────────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Data Layer (Aurora PostgreSQL)

**Tables:**
- **BQX Tables:** 40 backward momentum features per pair
- **REG Tables:** 57 quadratic regression features per pair
- **Feature Tables:** 131 engineered features (Volume, Currency, Stats, Bollinger, Time, Spread, Correlation, Technical, Fibonacci)

**Partitioning:**
- Monthly partitions: 12 partitions/table × 28 pairs = 336 partitions per table type
- Total partitions: 336 (BQX) + 336 (REG) + ~336 (Feature tables) = ~1,000 partitions

**Indexes:**
- PRIMARY KEY on (pair, ts_utc) for time-range queries
- BTREE indexes on ts_utc for partition pruning
- Query performance: <100ms for single timestamp (all 228 features)

**Connection:**
- Endpoint: trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com
- SSL/TLS encryption required
- Credentials: AWS Secrets Manager
- Connection pooling: psycopg2 pool (min=2, max=10)

---

### 2. Training Pipeline (SageMaker)

#### Stage 1: Feature Engineering (Processing Job)

**Instance:** ml.m5.2xlarge (8 vCPU, 32 GB RAM)
**Duration:** ~70 minutes (28 pairs in 4 batches of 7)

**Process:**
1. Query Aurora for 6 months of data per pair
2. Extract 228 base features (BQX + REG + Feature tables)
3. Apply lagging strategy:
   - Lag 142 features × 4 windows (60, 120, 180, 240 min) = 568 lagged + 142 base = 710
   - Keep 86 non-lagged features (Time, Currency Indices, etc.)
4. Apply temporal causality rule:
   - Add 61-minute lag to w60_ features (6) and agg_ features (7) = 13 causality features
5. **Output:** 809 total features (710 + 86 + 13)
6. Split: 70% train, 15% validation, 15% test
7. Save to S3 as Parquet: s3://bqx-ml-datasets/{pair}/{train,val,test}.parquet

**Cost:** $0.806/hour × 1.2 hours = $0.97 per run

#### Stage 2: Feature Selection

**Instance:** Runs within training job (no separate instance)
**Duration:** ~5 minutes per pair

**Process:**
1. Train initial Random Forest on all 809 features
2. Compute feature importance using .feature_importances_
3. Sort features by importance descending
4. Calculate cumulative importance
5. Select top 70 features where cumulative importance > 95%
6. Save selected_features.json to S3
7. Retrain model on only 70 selected features

**Output:** s3://bqx-ml-models/{pair}/selected_features.json

#### Stage 3: Model Training (Parallel)

**Instance:** ml.m5.xlarge (4 vCPU, 16 GB RAM) × 28 parallel jobs
**Duration:** 5 minutes per pair (parallel execution)
**Total Wall Time:** ~5-10 minutes for all 28 pairs

**Algorithm:** Random Forest Regressor (sklearn)
**Hyperparameters (default):**
```python
{
  'n_estimators': 100,
  'max_depth': 10,
  'min_samples_split': 20,
  'min_samples_leaf': 10,
  'max_features': 'sqrt',
  'random_state': 42
}
```

**Training Process:**
1. Load train/val/test Parquet from S3
2. Load selected_features.json (70 features)
3. Filter features to selected 70
4. Fit StandardScaler on train set
5. Train Random Forest on scaled train data
6. Evaluate on validation set (R², MAE, directional accuracy)
7. Package: model.pkl + scaler.pkl + selected_features.json → model.tar.gz
8. Save to S3: s3://bqx-ml-models/{pair}/model.tar.gz

**Metrics Logged:**
- R² (validation)
- MAE (validation)
- RMSE (validation)
- Directional Accuracy (validation)
- Training time

**Cost:** $0.403/hour × 0.083 hours × 28 jobs = $0.93 per run

#### Stage 4: Model Registry

**Process:**
1. Create model package group: bqx-ml-models
2. For each pair, register model package with metadata:
   - Model artifact S3 URI
   - Pair name
   - R², MAE, directional_accuracy
   - Training date
   - Feature count (70)
   - Model version (semantic versioning)
3. Set approval status: PendingManualApproval
4. Approval workflow: Manual or automated (R² > 0.85 → Approved)
5. Production tag applied to approved models

**Metadata Example:**
```json
{
  "pair": "eurusd",
  "model_version": "1.2.3",
  "r2_score": 0.87,
  "mae": 0.00012,
  "directional_accuracy": 0.54,
  "training_date": "2025-01-11",
  "feature_count": 70,
  "training_samples": 260000,
  "approval_status": "Approved"
}
```

---

### 3. Inference System (SageMaker Multi-Model Endpoint)

#### Multi-Model Endpoint Configuration

**Instance:** ml.m5.xlarge (4 vCPU, 16 GB RAM)
**Endpoint Name:** bqx-ml-multi-model-production

**Multi-Model Setup:**
- S3 model location: s3://bqx-ml-models/
- Structure:
  ```
  s3://bqx-ml-models/
    ├── eurusd/
    │   └── model.tar.gz  (model.pkl + scaler.pkl + selected_features.json)
    ├── gbpusd/
    │   └── model.tar.gz
    └── ... (28 pairs)
  ```

**Model Loading:**
- On-demand loading: Model loaded when first requested
- LRU cache: Keep 10 most recently used models in memory
- Cold start latency: ~500ms first request
- Warm latency: ~10ms subsequent requests
- Memory per model: ~50 MB (Random Forest + scaler + metadata)
- Total memory: 28 models × 50 MB = 1.4 GB (fits in 16 GB RAM)

**Auto-Scaling:**
- Min instances: 1
- Max instances: 4
- Target metric: InvocationsPerInstance = 400/minute
- Scale-out cooldown: 60 seconds
- Scale-in cooldown: 300 seconds

**Invocation Process:**
```python
import boto3
runtime = boto3.client('sagemaker-runtime')

response = runtime.invoke_endpoint(
    EndpointName='bqx-ml-multi-model-production',
    TargetModel='eurusd/model.tar.gz',  # Specify which pair's model
    ContentType='application/json',
    Body=json.dumps({
        'features': [...]  # 70 features
    })
)

prediction = json.loads(response['Body'].read())
# Returns: {"prediction": 0.00043, "confidence_interval": [0.00035, 0.00051]}
```

**Cost:** $0.269/hour × 24 × 30 × 1.5 instances (avg) = $291/month

---

### 4. Prediction API (Lambda + API Gateway)

#### API Gateway Configuration

**Endpoint:** https://{api-id}.execute-api.us-east-1.amazonaws.com/prod/predict
**Method:** POST
**Authentication:** API Key (x-api-key header)
**Throttling:** 100 requests/second
**CORS:** Enabled

**Request Format:**
```json
POST /predict
{
  "pair": "eurusd",
  "timestamp": "2025-01-11T10:00:00Z"  // Optional, defaults to current time
}
```

**Response Format:**
```json
{
  "pair": "eurusd",
  "prediction": 0.00043,
  "confidence_interval": [0.00035, 0.00051],
  "signal": "BUY",
  "signal_strength": 0.75,
  "features_used": 70,
  "model_version": "1.2.3",
  "latency_ms": 185,
  "timestamp": "2025-01-11T10:00:00Z"
}
```

#### Feature Extraction Lambda

**Function Name:** bqx-ml-feature-extraction
**Runtime:** Python 3.11
**Memory:** 1024 MB
**Timeout:** 30 seconds
**Concurrency:** 100

**Layers:**
- psycopg2-layer (PostgreSQL client)
- pandas-numpy-layer

**Process:**
1. Connect to Aurora (connection pooling)
2. Query BQX table: `SELECT * FROM bqx.bqx_{pair} WHERE ts_utc = '{timestamp}'`
3. Query REG table: `SELECT * FROM bqx.reg_{pair} WHERE time = '{timestamp}'`
4. Query Feature tables: 8 queries for each feature table
5. Combine into 228 base features
6. Apply lagging:
   - For each of 142 lagable features, fetch values at t-60, t-120, t-180, t-240
   - Total: 142 × 4 = 568 additional queries (batched)
7. Apply temporal causality:
   - For w60_ and agg_ features, fetch value at t-61
   - Total: 13 additional features
8. Add non-lagged features: 86 features (Time, Currency Indices, etc.)
9. Return 809 features as JSON

**Optimization:**
- Single transaction for all queries
- Batch queries using JOIN where possible
- Connection pool (min=2, max=5 per Lambda instance)
- Result caching: 5-minute TTL in Lambda memory

**Target Latency:** <100ms

**Cost:** $0.20 per 1M requests

#### Prediction Lambda

**Function Name:** bqx-ml-prediction-api
**Runtime:** Python 3.11
**Memory:** 512 MB
**Timeout:** 30 seconds
**Concurrency:** 100

**Process:**
1. Parse request (pair, timestamp)
2. Invoke Feature Extraction Lambda → 809 features
3. Load selected_features.json from S3 (cached)
4. Filter to 70 selected features
5. Invoke SageMaker endpoint with 70 features
6. Receive prediction and confidence interval
7. Generate trading signal:
   - BUY if prediction > +0.0005
   - SELL if prediction < -0.0005
   - HOLD otherwise
8. Adjust signal strength based on confidence interval width
9. Return JSON response

**Target Latency:** <200ms total
- Feature extraction: 100ms
- Feature selection: 5ms
- SageMaker invocation: 50ms (network + inference)
- Signal generation: 10ms
- Response formatting: 10ms
- Network overhead: 25ms

**Cost:** $0.20 per 1M requests

---

### 5. Monitoring & MLOps

#### SageMaker Model Monitor

**Data Quality Monitor:**
- Schedule: Hourly
- Baseline: 70 feature statistics (mean, std, min, max, percentiles)
- Metrics monitored:
  - Feature mean drift
  - Feature std drift
  - Missing value rate
  - Data type violations
- Threshold: KL divergence > 0.1 triggers warning

**Model Quality Monitor:**
- Schedule: Daily
- Metrics monitored:
  - R² (compare predictions vs actuals after 60 minutes)
  - MAE
  - Directional accuracy
- Threshold: R² drop > 0.05 triggers critical alarm

**Cost:** $0.27/hour × 720 hours = $194.40/month (can reduce by monitoring every 4 hours)

#### CloudWatch Dashboard

**Panels:**
1. **Invocations per minute:** Sum(Invocations) per minute
2. **Latency:** P50, P95, P99 (ModelLatency metric)
3. **Error rate:** (4XXError + 5XXError) / Invocations × 100
4. **Model performance:** Rolling 24-hour R² (custom metric)
5. **Feature drift status:** Latest KL divergence (custom metric)
6. **Auto-scaling activity:** DesiredInstanceCount, CurrentInstanceCount

**Cost:** Free (within first 3 dashboards)

#### Alerting System

**SNS Topics:**
- bqx-ml-critical (email + Slack)
- bqx-ml-warning (Slack only)
- bqx-ml-info (log only)

**Alarms:**
- **Critical:**
  - Error rate > 5% for 5 minutes
  - Training job failure
  - R² drop > 0.05
- **Warning:**
  - Latency P99 > 500ms for 10 minutes
  - Feature drift KL > 0.1
  - Cost > $400/month
- **Info:**
  - Retraining initiated
  - Model deployed

**Cost:** $0.50 per 1M notifications (~$1/month)

#### Cost Monitoring

**Cost Allocation Tags:**
- Project: bqx-ml
- Environment: production
- Pair: {pair_name}
- Component: training | inference | storage | monitoring

**Cost Explorer Dashboard:**
- Filter by Project=bqx-ml
- Group by: Component, Pair
- Daily cost trend
- Monthly forecast

**Billing Alarms:**
- Warning: $400/month
- Critical: $500/month
- Emergency: $600/month

---

## Latency Budget

**Target: <200ms P99 end-to-end**

| Component | Target | Actual (Expected) |
|-----------|--------|-------------------|
| API Gateway ingress | 5ms | 3-7ms |
| Prediction Lambda cold start | N/A | ~500ms (rare) |
| Prediction Lambda warm | 10ms | 5-15ms |
| Feature Extraction Lambda invoke | 100ms | 80-120ms |
| Aurora query (228 base) | 50ms | 30-60ms |
| Aurora query (lagged 568) | 50ms | 40-70ms |
| Feature selection filtering | 5ms | 2-8ms |
| SageMaker endpoint invoke | 50ms | 40-80ms |
| Network (Lambda → SageMaker) | 20ms | 15-30ms |
| Model inference (warm) | 10ms | 5-15ms |
| Signal generation | 10ms | 5-15ms |
| Response serialization | 10ms | 5-15ms |
| **TOTAL** | **200ms** | **150-250ms (P99)** |

**Optimization Strategies:**
1. Connection pooling (saves 20ms per Aurora query)
2. Feature caching (saves 100ms on repeated timestamps)
3. Model pre-warming (avoid cold starts)
4. Batch Aurora queries (reduce round trips)

---

## Throughput Capacity

**Single Instance Capacity:**
- Latency per request: 140ms (average)
- Max throughput: 1000ms / 140ms = 7.14 requests/second
- With overhead: ~6 requests/second sustained

**Expected Traffic:**
- Development: 0.5 req/sec (28 pairs × 1 req/min)
- Production off-peak: 1 req/sec
- Production market-open: 5 req/sec
- Peak: 10 req/sec (28 pairs × 20 req/min)

**Scaling:**
- 1 instance: handles 6 req/sec (sufficient for off-peak)
- 2 instances: handles 12 req/sec (sufficient for peak)
- 4 instances: handles 24 req/sec (4x peak capacity)

**Auto-scaling target:** 400 invocations/minute = 6.67 req/sec per instance (90% utilization)

---

## Security Architecture

**Network Security:**
- VPC: All resources in private subnets
- Security Groups: Least privilege (only required ports)
- Aurora: No public access, VPC-only
- SageMaker: VPC-enabled endpoints

**Authentication & Authorization:**
- IAM roles: Least privilege for all resources
- API Gateway: API key authentication
- Aurora: IAM database authentication + SSL/TLS
- Secrets Manager: Credentials rotation enabled

**Data Security:**
- Encryption at rest: S3 (SSE-S3), Aurora (AES-256)
- Encryption in transit: TLS 1.2+ for all connections
- Model artifacts: Encrypted in S3
- Logs: Encrypted in CloudWatch Logs

**Compliance:**
- Audit logging: CloudTrail for all API calls
- Access logging: API Gateway logs to S3
- Inference logging: CloudWatch Logs
- Cost tracking: Cost allocation tags

---

## Disaster Recovery

**RTO (Recovery Time Objective):** 15 minutes
**RPO (Recovery Point Objective):** 1 hour

**Backup Strategy:**
- **Aurora:** Automated backups (7-day retention)
- **S3 models:** Versioning enabled (30-day lifecycle)
- **Configuration:** Infrastructure as Code (CloudFormation/Terraform)

**Recovery Procedures:**
1. **Endpoint Failure:** Redeploy endpoint from latest model artifacts (5 min)
2. **Training Job Failure:** Retry with same data (10 min)
3. **Aurora Failure:** Failover to read replica (automatic, <1 min)
4. **Region Failure:** Deploy to backup region (15 min)

**Testing:**
- Monthly disaster recovery drills
- Quarterly chaos engineering exercises

---

## Cost Optimization Strategies

**Current Cost:** ~$535/month
**Optimized Cost:** ~$430/month

**Optimizations:**
1. **Savings Plans:** Commit to 1-year compute → -20% ($107/month savings)
2. **Model Monitor frequency:** Hourly → every 4 hours → -$145/month
3. **Spot instances for training:** Use spot → -50% training cost (minimal savings, $2/month)
4. **CloudWatch log retention:** 7 days instead of 30 days → -$3/month
5. **S3 Intelligent-Tiering:** Move old datasets → -$2/month

**Total Optimized:** $535 - $107 - $145 = $283/month (aggressive optimization)
**Recommended:** $430/month (with Savings Plans and reduced monitoring)

---

## Conclusion

This architecture provides a production-grade ML system capable of:
- Real-time predictions (<200ms latency)
- High availability (99.9% uptime)
- Auto-scaling (1-4 instances)
- Comprehensive monitoring (drift detection, performance tracking)
- Cost-effective operation (~$430/month optimized)

**Ready for production deployment after Phase 1.6 and Phase 2 complete.**
