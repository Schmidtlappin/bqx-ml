# Refactored BQX ML Master Plan
**Complete Implementation Roadmap with Dual Feature Architecture**

**Date:** 2025-11-12
**Version:** 2.0 - Comprehensive Refactor
**Status:** Ready for Implementation
**Total Features:** 730 (268 idx + 254 bqx + 208 shared/cross-domain)

---

## Executive Summary

### Mission
Build a production-grade multi-horizon BQX forecasting system that predicts future momentum at 5 horizons (i+15, i+30, i+45, i+60, i+75 minutes) using dual-domain feature architecture across 28 forex pairs.

### Core Innovation: Dual Feature Architecture
**Rate Index Domain** + **BQX Momentum Domain** = Complete predictive feature space
- Rate features capture CAUSE (price dynamics driving momentum)
- BQX features capture EFFECT (momentum patterns and persistence)
- Dual-domain comparisons detect regime transitions and decoupling events

### Success Metrics
- **Model Performance:** R² > 0.85 across all horizons, directional accuracy > 60%
- **Latency:** P99 inference < 200ms for all 28 pairs
- **Cost:** Total AWS monthly cost < $400
- **Robustness:** Stable performance across volatility regimes

---

## Table of Contents
1. [Phase 0: Infrastructure & Setup](#phase-0)
2. [Phase 1: Data Foundation](#phase-1)
3. [Phase 1.5: Index Architecture](#phase-15)
4. [Phase 1.6: Feature Development (Dual Architecture)](#phase-16)
5. [Phase 2: Feature Engineering Pipeline](#phase-2)
6. [Phase 3: Model Development & Training](#phase-3)
7. [Phase 4: SageMaker Deployment](#phase-4)
8. [Phase 5: Production Operations](#phase-5)
9. [Resource Requirements & Timeline](#resources)
10. [Risk Mitigation](#risks)

---

<a name="phase-0"></a>
## Phase 0: Infrastructure Setup

**Duration:** 3 days
**Status:** ✅ Complete
**Dependencies:** None

### 0.1 GitHub Repository
- ✅ Repository: `robkei-control/bqx-ml`
- ✅ Structure: data/, models/, scripts/, training/, inference/, docs/
- ✅ CI/CD: GitHub Actions configured

### 0.2 SageMaker Studio
- ✅ Domain created in us-east-1
- ✅ VPC connectivity to Aurora RDS
- ✅ Security groups allow SageMaker → Aurora (port 5432)

### 0.3 AWS Secrets Manager
- ✅ Secret: `bqx-ml/airtable-token`
- ✅ Secret: `bqx-ml/aurora-credentials`
- ✅ IAM roles configured for access

---

<a name="phase-1"></a>
## Phase 1: Data Foundation

**Duration:** 1-2 days
**Status:** ✅ Complete
**Dependencies:** Phase 0

### 1.1 M1 Tables (Source Data)
- ✅ 28 forex pairs with 1-minute OHLCV data
- ✅ Time range: 2024-01 through 2025-06 (18 months)
- ✅ ~370K rows per pair = 10.4M total rows
- ✅ Schema: ts_utc, open, high, low, close, volume, rate_index

**Key Field:** `rate_index` - Base-100 normalized price for cross-pair comparability

### 1.2 BQX Tables (Backward Momentum Indices)
- ✅ 28 pairs with monthly partitioning
- ✅ 336 partitions (28 pairs × 12 months)
- ✅ Windows: w15, w30, w45, w60, w75 (backward cumulative momentum)
- ✅ Storage: 4.3 GB

---

<a name="phase-15"></a>
## Phase 1.5: Index-Based Architecture Refactor

**Duration:** 22 hours
**Status:** ✅ Complete (REG tables exist)
**Dependencies:** Phase 1

### 1.5.1 Rate Index Calculation
- ✅ Added `rate_index` column to all M1 tables
- ✅ Base-100 normalization: rate_index = (rate / initial_rate) × 100
- ✅ Purpose: Cross-pair price comparability

### 1.5.2 Regression Features (REG)
- ✅ Table: `reg_{pair}` (to be renamed to `reg_idx_{pair}`)
- ✅ 336 partitions populated
- ✅ Features: Quadratic regression coefficients (a2, a1, b), R², RMSE, residuals
- ✅ Windows: w15, w30, w45, w60, w75, w90

### 1.5.3 REG_BQX Features
- ✅ Table: `reg_bqx_{pair}` (ALREADY EXISTS!)
- ✅ Same structure as REG_IDX but computed on BQX values
- ✅ Captures: Momentum trajectory quality

---

<a name="phase-16"></a>
## Phase 1.6: Feature Development (Dual Architecture)

**Total Duration:** 80-100 hours (25-30 hours wall time with parallelization)
**Status:** 🔄 In Progress
**Dependencies:** Phase 1.5

**Critical Change:** All features now have dual representations (rate_idx + bqx)

### Phase 1.6.9: Table Renaming & Schema Migration ⚠️ CRITICAL FIRST STEP

**Duration:** 1 hour
**Status:** 🔨 Ready to Execute
**Blocks:** All subsequent stages

**Purpose:** Rename existing rate-based tables to rate_index naming convention

**Tables to Rename:**
```sql
reg_{pair}                  → reg_idx_{pair}                (336 partitions, 10.3M rows)
statistics_features_{pair}  → statistics_idx_{pair}         (364 partitions, 10.3M rows)
bollinger_features_{pair}   → bollinger_idx_{pair}          (364 partitions, 10.3M rows)
fibonacci_features_{pair}   → fibonacci_idx_{pair}          (364 partitions, 10.2M rows)
volume_features_{pair}      → volume_idx_{pair}             (336 partitions, estimated 10M rows)
spread_features_{pair}      → spread_idx_{pair}             (336 partitions, estimated 10M rows)
correlation_features_{pair} → correlation_idx_{pair}        (364 partitions, 0 rows - empty)
```

**Execution:**
```bash
PGPASSWORD='BQX_Aurora_2025_Secure' psql \
  -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres \
  -d bqx \
  -f scripts/refactor/phase_1_6_9_rename_rate_tables.sql
```

**Deliverables:**
- ✅ SQL script: `phase_1_6_9_rename_rate_tables.sql` (already created)
- [ ] Verification report confirming row counts unchanged
- [ ] Updated documentation

**Success Criteria:**
- All 1,820 tables renamed (7 types × 260 average partitions)
- Row counts match pre-rename state
- Zero downtime (ALTER TABLE is atomic)

---

### Phase 1.6.10: Technical Rate Build

**Duration:** 8 hours
**Status:** 🔨 To Build
**Dependencies:** 1.6.9 complete
**Parallelizable:** Yes (can run concurrently with 1.6.11)

**Objective:** Build technical indicators on rate_index

**Schema Creation:**
- 28 parent tables: `technical_idx_{pair}`
- 336 partitions (28 pairs × 12 months)

**Features (15 per table):**
- RSI (14, 21 periods)
- MACD (line, signal, histogram)
- Stochastic (%K, %D)
- CCI, Williams %R, ROC
- ADX, +DI, -DI
- ATR, ATR%

**Worker:** `scripts/ml/technical_idx_worker.py`
- Threading: 8 concurrent
- Source: M1 `rate_index` column
- Progress logging: `/tmp/technical_idx_worker.log`

**Expected Output:**
- 10.3M rows across 336 partitions
- ~8 GB storage

**Validation:**
- RSI: 0-100 range
- MACD: Reasonable values
- NULLs: Only initial lookback periods (first 14-26 rows)

---

### Phase 1.6.11: Technical BQX Build

**Duration:** 8 hours
**Status:** 🔨 To Build
**Dependencies:** 1.6.9 complete
**Parallelizable:** Yes (can run concurrently with 1.6.10)

**Objective:** Build technical indicators on BQX momentum

**Schema:** Same as 1.6.10 but table name `technical_bqx_{pair}`

**Worker:** `scripts/ml/technical_bqx_worker.py`
- Source: `bqx_{pair}.w15_bqx_return`
- Interpretation: Momentum-of-momentum signals

**Key Insight:**
- RSI_idx > 70: Price overbought
- RSI_bqx > 70: Momentum acceleration overbought (2nd derivative!)
- Different signals, complementary information

---

### Phase 1.6.12: Statistics BQX Build

**Duration:** 6 hours
**Status:** 🔨 To Build
**Dependencies:** 1.6.9 complete
**Parallelizable:** Yes

**Objective:** Statistical moments on BQX momentum

**Schema:** `statistics_bqx_{pair}`
**Features (24 per table):**
- mean, std, skew, kurt (windows: 20, 50, 120)
- min, max, range, z_score

**Worker:** `scripts/ml/statistics_bqx_worker.py`

**Note:** Rate version already exists (renamed `statistics_idx_{pair}`)

---

### Phase 1.6.13: Bollinger BQX Build

**Duration:** 6 hours  
**Status:** 🔨 To Build
**Dependencies:** 1.6.9 complete
**Parallelizable:** Yes

**Objective:** Bollinger Bands on BQX momentum

**Schema:** `bollinger_bqx_{pair}`
**Features (10 per table):**
- bb_upper, bb_middle, bb_lower (windows: 20, 50)
- bb_bandwidth, bb_percent_b

**Worker:** `scripts/ml/bollinger_bqx_worker.py`

**Interpretation:** Overbought/oversold in momentum space

---

### Phase 1.6.14: Fibonacci BQX Build

**Duration:** 6 hours
**Status:** 🔨 To Build
**Dependencies:** 1.6.9 complete
**Parallelizable:** Yes

**Objective:** Fibonacci retracements in momentum space

**Schema:** `fibonacci_bqx_{pair}`
**Features (10 per table):**
- Retracement: 23.6%, 38.2%, 50%, 61.8%
- Extension: 127.2%, 161.8%
- Distance to levels, range high/low

**Worker:** `scripts/ml/fibonacci_bqx_worker.py`

**Interpretation:** Support/resistance in BQX values

---

### Phase 1.6.15: Volume BQX Build

**Duration:** 4 hours
**Status:** 🔨 To Build
**Dependencies:** 1.6.9 complete
**Parallelizable:** Yes

**Objective:** Volume-momentum interaction features

**Schema:** `volume_bqx_{pair}`
**Features (8 per table):**
- vol_bqx_corr (20, 60 periods)
- Volume during BQX surge/drop
- BQX per unit volume
- Confirmation/divergence flags

**Worker:** `scripts/ml/volume_bqx_worker.py`

---

### Phase 1.6.16: Correlation Rate Build

**Duration:** 8 hours
**Status:** 🔨 To Build
**Dependencies:** 1.6.9 complete
**Parallelizable:** Yes

**Objective:** Populate empty correlation_idx tables

**Schema:** `correlation_idx_{pair}` (already renamed, currently empty)
**Features (20 per table):**
- Cross-pair correlations (EUR-USD, GBP-USD, etc.)
- Variance decomposition
- Covariance matrix metrics
- Correlation regime classification

**Worker:** `scripts/ml/correlation_idx_worker.py`

---

### Phase 1.6.17: Correlation BQX Build ⚠️ FINAL STEP

**Duration:** 8 hours
**Status:** 🔨 To Build
**Dependencies:** 1.6.11, 1.6.12, 1.6.13, 1.6.14 ALL complete
**Parallelizable:** NO (must be last)

**Objective:** Cross-pair and cross-window BQX momentum correlations

**Schema:** `correlation_bqx_{pair}`
**Features (25 per table):**
- Cross-pair BQX correlations
- **Cross-window term structure** (w15 ↔ w60) - CRITICAL!
- Term slope, curvature, inversion flags
- Momentum variance decomposition
- Lead-lag relationships
- Triangular momentum parity

**Worker:** `scripts/ml/correlation_bqx_worker.py`

**Why This is Last:** Requires all other BQX features to compute full correlation matrix

---

### Phase 1.6 Summary

**Total Tables to Build/Rename:**
- Rename: 7 feature types × ~260 avg partitions = 1,820 tables
- Build new: 6 feature types × 336 partitions = 2,016 tables
- **Grand Total: 3,836 table operations**

**Storage Impact:** +50-60 GB

**Timeline:**
- Sequential: 80-100 hours
- Parallel (4 workers): 25-30 hours wall time

**Execution Strategy:**
1. Stage 1.6.9 (rename) - 1 hour, blocks everything
2. Stages 1.6.10-1.6.16 - Run 4-5 in parallel
3. Stage 1.6.17 (correlation_bqx) - Final step after others complete

---

<a name="phase-2"></a>
## Phase 2: Feature Engineering Pipeline

**Duration:** 15-20 hours
**Status:** 🔨 To Build
**Dependencies:** Phase 1.6 complete

### 2.1 Pipeline Architecture

**Input:** Raw feature tables (730 base features from Phase 1.6)
**Output:** Training-ready datasets with derived features
**Platform:** SageMaker Processing Jobs

### 2.2 Feature Categories to Implement

#### 2.2.1 Lagged Features (180 features)
**Purpose:** Capture autocorrelation and short-term memory

```python
# Rate index lags (60 features)
rate_idx_lag_{1...60}

# BQX lags (60 features)
bqx_lag_{1...60}

# Return lags (60 features)
return_lag_{1...60}
```

**Implementation:** `scripts/ml/compute_lagged_features.py`
- Window: 60-minute lookback
- Leakage-safe: All lags use data at or before time i

#### 2.2.2 Moving Averages (24 features)
**Purpose:** Trend smoothing and momentum tracking

```python
# Rate index MAs (12 features)
sma_{5,10,20,50,100,200}
ema_{5,10,20,50,100,200}

# BQX MAs (12 features)
bqx_sma_{5,10,20,50,100,200}
bqx_ema_{5,10,20,50,100,200}
```

**Implementation:** `scripts/ml/compute_moving_averages.py`

#### 2.2.3 Cross-Pair Features (44 features)
**Purpose:** Systemic risk and correlation structure

```python
# Sister-pair features (30 features)
{sister}_return_lag_{1,5,15}
{sister}_vol_30
{sister}_corr_60
{sister}_beta_60

# Triangular parity (8 features)
tri_resid_level, tri_resid_z_20
tri_bqx_resid, tri_bqx_resid_z_20

# USD factor (6 features)
usd_factor_level, usd_factor_change_{5,15}
usd_factor_vol_30, usd_factor_z_60
```

**Implementation:** `scripts/ml/compute_cross_pair_features.py`

#### 2.2.4 Dual-Domain Comparisons (28 features)
**Purpose:** Detect rate-momentum decoupling

```python
# Regression comparisons (12 features)
reg_rate_bqx_beta_30, reg_rate_bqx_r2_30
a2_diff_idx_bqx, a1_diff_idx_bqx

# Statistical comparisons (10 features)
var_ratio_bqx_idx_{20,60}
xcorr_idx_bqx_lag_{0,1,5,15}

# Bollinger comparisons (6 features)
bb_z_diff_bqx_idx_20
bb_bandwidth_ratio_20
```

**Implementation:** `scripts/ml/compute_dual_domain_features.py`

#### 2.2.5 Event & Regime Detection (26 features)
**Purpose:** Volatility spikes, jumps, regime transitions

```python
# Jump detection (8 features)
jump_flag_{2_5,3}_sigma
jump_count_{20,60}
time_since_last_jump

# Volatility regime (10 features)
vol_regime_{20,60}
vol_z_score_20
ewma_vol_30

# Trend regime (8 features)
trend_regime_{20,60}
trend_strength_{20,60}
trend_consistency_20
```

**Implementation:** `scripts/ml/compute_regime_features.py`

#### 2.2.6 Multi-Resolution Features (30 features)
**Purpose:** Multi-scale pattern detection

```python
# 5-minute aggregates (20 features)
rate_idx_5m_sma_10, rate_idx_5m_vol_20
bqx_5m_sma_10, rsi_5m_14

# 15-minute aggregates (10 features)
rate_idx_15m_sma_8, bqx_15m_sma_8
scale_cascade_aligned
```

**Implementation:** `scripts/ml/compute_multiresolution_features.py`
- Resample to 5-min and 15-min bars (UP TO TIME i ONLY)
- Compute core statistics at each resolution
- Compare across scales

### 2.3 Feature Engineering Pipeline Workflow

```
┌─────────────────────────────────────────────────────┐
│ SageMaker Processing Job: Feature Engineering      │
├─────────────────────────────────────────────────────┤
│ Input: Aurora feature tables (Phase 1.6)           │
│   • reg_idx, reg_bqx                                │
│   • statistics_idx, statistics_bqx                  │
│   • bollinger_idx, bollinger_bqx                    │
│   • technical_idx, technical_bqx                    │
│   • fibonacci_idx, fibonacci_bqx                    │
│   • volume_idx, volume_bqx                          │
│   • correlation_idx, correlation_bqx                │
│                                                     │
│ Processing Steps:                                   │
│   1. Load base features (730 features)             │
│   2. Compute lagged features (180 features)        │
│   3. Compute moving averages (24 features)         │
│   4. Compute cross-pair features (44 features)     │
│   5. Compute dual-domain comparisons (28 features) │
│   6. Compute event/regime features (26 features)   │
│   7. Compute multi-resolution features (30 features)│
│   8. Join all features on (pair, ts_utc)          │
│   9. Handle missing data (forward-fill, add flags) │
│  10. Feature selection (top 150-200 features)      │
│  11. Normalize features (StandardScaler)           │
│  12. Create targets (bqx_{i+15,30,45,60,75})      │
│  13. Vol-scale targets: (bqx_future - bqx_i) / σ   │
│  14. Train/val/test split (chronological, 70/15/15)│
│                                                     │
│ Output: S3 Parquet datasets                        │
│   • train.parquet (70% oldest data)                │
│   • val.parquet (15%)                              │
│   • test.parquet (15% newest data)                 │
│   • feature_metadata.json (column names, types)    │
│   • scaler.pkl (normalization parameters)          │
└─────────────────────────────────────────────────────┘
```

**Instance Type:** ml.m5.2xlarge (8 vCPU, 32 GB RAM)
**Duration:** 60-90 minutes for all 28 pairs
**Cost:** ~$0.40-0.60 per run

### 2.4 Feature Selection Strategy

**Initial:** 730 base + 332 derived = 1,062 total features
**Target:** 150-200 features (reduce dimensionality, prevent overfitting)

**Method:**
1. Random Forest feature importance (baseline model)
2. Remove features with importance < 0.001
3. Remove highly correlated features (ρ > 0.95)
4. Domain knowledge curation (ensure dual-domain coverage)

**Expected Distribution After Selection:**
- Rate index features: ~70
- BQX features: ~60
- Dual-domain comparisons: ~20
- Cross-pair features: ~25
- Time/regime features: ~20
- **Total: ~195 features**

### 2.5 Target Engineering

**Multi-Horizon Targets (5 per pair):**
```python
# Raw targets
target_15 = bqx_{i+15}
target_30 = bqx_{i+30}
target_45 = bqx_{i+45}
target_60 = bqx_{i+60}
target_75 = bqx_{i+75}

# Vol-scaled targets (RECOMMENDED for training)
target_15_scaled = (bqx_{i+15} - bqx_i) / ewma_vol_60
target_30_scaled = (bqx_{i+30} - bqx_i) / ewma_vol_60
# ... (same for 45, 60, 75)

# Direction targets (for multi-task learning)
direction_15 = sign(bqx_{i+15} - bqx_i)  # {-1, 0, 1}
# ... (same for 30, 45, 60, 75)
```

**Why Vol-Scaling:**
- Stabilizes variance across different volatility regimes
- Makes targets comparable across pairs
- Improves model convergence

### 2.6 Leakage Prevention

**Critical Rules:**
1. All features computed using data at or before time i
2. No forward-looking features
3. Train/val/test split chronologically (no shuffling)
4. 61-minute causality lag enforced where applicable
5. Unit tests verify no future data in features

**Validation:**
```python
# Test: Ensure no feature at time i uses data from i+1 or later
def test_no_leakage(features_df, target_df):
    assert features_df['ts_utc'].max() <= target_df['ts_utc'].min() - timedelta(minutes=1)
```

### 2.7 Deliverables

- [ ] Feature engineering pipeline code (`scripts/ml/feature_engineering_pipeline.py`)
- [ ] SageMaker Processing Job definition
- [ ] Training datasets in S3 (train/val/test.parquet)
- [ ] Feature metadata and scaler files
- [ ] Data quality report (missing data, outliers, distributions)
- [ ] Feature importance analysis
- [ ] Leakage validation test results

---

<a name="phase-3"></a>
## Phase 3: Model Development & Training

**Duration:** 30-40 hours
**Status:** 🔨 To Build
**Dependencies:** Phase 2 complete

### 3.1 Baseline Models (Week 1)

**Objective:** Establish performance baseline with simple models

#### 3.1.1 Random Forest Baseline
**Purpose:** Fast baseline, feature importance analysis

```python
# Model per horizon
model_15 = RandomForestRegressor(n_estimators=200, max_depth=15)
model_30 = RandomForestRegressor(n_estimators=200, max_depth=15)
# ... (45, 60, 75)

# Or multi-output
model_all = RandomForestRegressor(n_estimators=200, max_depth=15)
model_all.fit(X_train, y_train_all_horizons)  # 5 targets
```

**Training:**
- Instance: ml.m5.xlarge
- Duration: ~10 minutes per pair
- Total: ~5 hours for 28 pairs

**Expected Performance:**
- R² on test: 0.75-0.82 (based on existing REG/BQX baseline)
- Directional accuracy: 55-60%

**Key Outputs:**
- Feature importance rankings
- Per-horizon performance metrics
- Worst/best performing pairs identified

#### 3.1.2 XGBoost Baseline
**Purpose:** Gradient boosting comparison

```python
model = xgb.XGBRegressor(
    n_estimators=500,
    max_depth=8,
    learning_rate=0.05,
    subsample=0.8
)
```

**Expected Performance:**
- R² on test: 0.78-0.85 (typically +3-5% over Random Forest)

### 3.2 Advanced Models (Week 2-3)

#### 3.2.1 Temporal Fusion Transformer (TFT)
**Purpose:** State-of-the-art time series forecasting

**Architecture:**
- Shared encoder over lagged features
- Horizon embeddings (learned vectors per horizon)
- Multi-task head for 5 horizons
- Attention mechanism over past timesteps

**Training:**
- Instance: ml.p3.2xlarge (GPU)
- Duration: ~2-4 hours per pair
- Total: ~56-112 hours for 28 pairs (or 7-14 hours with 8 parallel jobs)

**Expected Performance:**
- R² on test: 0.85-0.92 (if TFT adds value over XGBoost)
- Especially strong on longer horizons (i+60, i+75)

**Implementation:**
```python
from pytorch_forecasting import TemporalFusionTransformer

model = TemporalFusionTransformer.from_dataset(
    dataset,
    learning_rate=0.001,
    hidden_size=64,
    attention_head_size=4,
    dropout=0.1,
    hidden_continuous_size=16,
    output_size=5,  # 5 horizons
    loss=QuantileLoss(),
)
```

#### 3.2.2 Multi-Task Learning
**Purpose:** Share representations across horizons

**Architecture:**
```
Input Features (195)
    ↓
Shared Dense Layers (256 → 128 → 64)
    ↓
  ┌─────┬─────┬─────┬─────┬─────┐
  │ H15 │ H30 │ H45 │ H60 │ H75 │  (Horizon-specific heads)
  └─────┴─────┴─────┴─────┴─────┘
    ↓     ↓     ↓     ↓     ↓
 Out15  Out30  Out45  Out60  Out75
```

**Loss Function:**
```python
# Weighted sum across horizons
loss = 0.1*loss_15 + 0.15*loss_30 + 0.2*loss_45 + 0.25*loss_60 + 0.3*loss_75
# (Up-weight farther horizons)
```

### 3.3 Model Selection Criteria

**Primary Metrics:**
1. **R² (test set):** Proportion of variance explained
2. **MAE (vol-scaled):** Mean absolute error
3. **Directional Accuracy:** % of correct sign predictions
4. **Calibration:** Quantile coverage (if using quantile loss)

**Secondary Metrics:**
5. **Inference latency:** P99 < 200ms
6. **Training time:** Cost efficiency
7. **Robustness:** Performance across volatility regimes

**Decision Tree:**
```
IF XGBoost R² > RandomForest R² + 0.03:
    Use XGBoost as baseline
IF TFT R² > XGBoost R² + 0.04:
    Use TFT (justify GPU cost)
ELSE:
    Use XGBoost (cost-effective)
```

### 3.4 Hyperparameter Tuning

**Method:** SageMaker Hyperparameter Tuning Jobs

**Parameters to Tune (XGBoost example):**
```python
hyperparameter_ranges = {
    'max_depth': IntegerParameter(6, 12),
    'learning_rate': ContinuousParameter(0.01, 0.1, scaling_type='Logarithmic'),
    'subsample': ContinuousParameter(0.7, 0.9),
    'n_estimators': IntegerParameter(300, 700),
    'min_child_weight': IntegerParameter(1, 10)
}
```

**Budget:** 20-30 trials per pair (or 5-10 trials for 4 major pairs, then apply best config to all)

**Cost:** ~$5-10 per pair (with ml.m5.xlarge)

### 3.5 Validation Strategy

**Splitting:**
- Train: 70% (oldest data, e.g., 2024-01 to 2024-08)
- Validation: 15% (2024-09 to 2024-10)
- Test: 15% (newest data, 2024-11 to 2024-12)

**Rolling-Origin Backtest:**
- Window: 60 days train, 30 days test
- Step: 7 days
- Embargo: 2 hours (prevent label bleed)

**Regime-Specific Evaluation:**
- Report metrics by:
  - Session (Tokyo, London, NY)
  - Volatility tercile (low, mid, high)
  - Trend state (up, sideways, down)

### 3.6 Model Training Pipeline

```
┌───────────────────────────────────────────────────┐
│ SageMaker Training Jobs (Per Pair)               │
├───────────────────────────────────────────────────┤
│ Input: S3 training datasets                      │
│                                                   │
│ Steps:                                            │
│  1. Load train/val data from S3                  │
│  2. Initialize model (RF, XGBoost, or TFT)       │
│  3. Train with early stopping (val loss)         │
│  4. Evaluate on validation set                   │
│  5. If performance meets threshold:              │
│       - Save model to S3                         │
│       - Log metrics to SageMaker Experiments     │
│  6. Generate prediction plots and diagnostics    │
│                                                   │
│ Output:                                           │
│  • Trained model artifacts (S3)                  │
│  • Model metrics (Experiments)                   │
│  • Feature importance (JSON)                     │
│  • Validation predictions (CSV)                  │
└───────────────────────────────────────────────────┘
```

**Parallel Execution:**
- Launch 8-10 training jobs simultaneously
- Each job trains one pair
- Total wall time: ~4-6 hours for all 28 pairs (XGBoost)

### 3.7 Ensemble Strategy (Optional)

**If multiple models perform well:**

**Weighted Average Ensemble:**
```python
pred_final = 0.4 * pred_xgboost + 0.35 * pred_tft + 0.25 * pred_rf
```

**Stacking:**
```python
# Level 1: Base models
pred_xgb = xgb_model.predict(X)
pred_tft = tft_model.predict(X)
pred_rf = rf_model.predict(X)

# Level 2: Meta-learner
meta_features = np.column_stack([pred_xgb, pred_tft, pred_rf, X_key_features])
pred_final = meta_model.predict(meta_features)
```

**When to Ensemble:**
- If base models have low correlation (< 0.85)
- If ensemble validation R² > best single model + 0.02

### 3.8 Deliverables

- [ ] Trained models for all 28 pairs (S3)
- [ ] Model performance report (R², MAE, directional accuracy per horizon)
- [ ] Feature importance analysis
- [ ] Hyperparameter tuning results
- [ ] Validation prediction files
- [ ] Model selection decision document

---

<a name="phase-4"></a>
## Phase 4: SageMaker Deployment

**Duration:** 20-25 hours
**Status:** 🔨 To Build
**Dependencies:** Phase 3 complete

### 4.1 Multi-Model Endpoint

**Purpose:** Serve all 28 pairs from single endpoint

**Configuration:**
```python
from sagemaker.multidatamodel import MultiDataModel

mdm = MultiDataModel(
    name='bqx-ml-multi-model',
    model_data_prefix='s3://bqx-ml-models/production/',
    container_image_uri=container_uri,
    role=sagemaker_role
)

endpoint = mdm.deploy(
    initial_instance_count=2,
    instance_type='ml.m5.xlarge',
    endpoint_name='bqx-ml-endpoint'
)
```

**Model Loading:**
- Models loaded on-demand (first request)
- LRU cache (keep most recently used models in memory)
- Cold start latency: ~500ms
- Warm latency: <100ms

**Scaling:**
- Auto-scaling: 1-4 instances based on CPU utilization
- Target: 70% CPU utilization

### 4.2 Lambda Prediction API

**Purpose:** REST API for real-time predictions

**Architecture:**
```
API Gateway (REST API)
    ↓
Lambda Function (Python 3.11)
    ↓
SageMaker Endpoint (invoke_endpoint)
    ↓
Returns: {
    "pair": "eurusd",
    "timestamp": "2024-11-12T10:30:00Z",
    "predictions": {
        "horizon_15": {"value": 0.0023, "confidence": [0.0015, 0.0031]},
        "horizon_30": {"value": 0.0041, "confidence": [0.0028, 0.0054]},
        "horizon_45": {"value": 0.0052, "confidence": [0.0035, 0.0069]},
        "horizon_60": {"value": 0.0059, "confidence": [0.0039, 0.0079]},
        "horizon_75": {"value": 0.0063, "confidence": [0.0041, 0.0085]}
    }
}
```

**Lambda Function:**
```python
import boto3
import json

sagemaker_runtime = boto3.client('sagemaker-runtime')

def lambda_handler(event, context):
    pair = event['pair']
    features = event['features']  # 195 features
    
    # Invoke endpoint
    response = sagemaker_runtime.invoke_endpoint(
        EndpointName='bqx-ml-endpoint',
        TargetModel=f'{pair}.tar.gz',
        Body=json.dumps(features),
        ContentType='application/json'
    )
    
    predictions = json.loads(response['Body'].read())
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'pair': pair,
            'predictions': predictions
        })
    }
```

**Latency Requirements:**
- P50: <100ms
- P95: <150ms
- P99: <200ms

### 4.3 Batch Prediction Pipeline

**Purpose:** Generate predictions for all pairs, all timestamps

**Use Cases:**
- Backtesting
- Offline model evaluation
- Historical analysis

**Implementation:**
```python
# SageMaker Batch Transform Job
transformer = model.transformer(
    instance_count=4,
    instance_type='ml.m5.2xlarge',
    output_path='s3://bqx-ml-predictions/batch/',
    strategy='MultiRecord',
    max_payload=10  # MB
)

transformer.transform(
    data='s3://bqx-ml-features/batch_input.csv',
    content_type='text/csv',
    split_type='Line'
)
```

**Schedule:** Daily at 00:00 UTC
**Duration:** ~30-45 minutes for full historical dataset
**Cost:** ~$2-3 per run

### 4.4 Model Monitor & Drift Detection

**Purpose:** Detect model performance degradation

**Metrics to Monitor:**
1. **Data Drift:** Distribution shift in input features
2. **Model Drift:** Prediction distribution shift
3. **Performance Drift:** MAE/R² degradation
4. **Latency Drift:** P99 latency increase

**SageMaker Model Monitor Setup:**
```python
from sagemaker.model_monitor import ModelMonitor, DataCaptureConfig

# Enable data capture
data_capture_config = DataCaptureConfig(
    enable_capture=True,
    sampling_percentage=20,
    destination_s3_uri='s3://bqx-ml-monitoring/data-capture'
)

# Create monitoring schedule
model_monitor = ModelMonitor(
    role=sagemaker_role,
    instance_count=1,
    instance_type='ml.m5.xlarge',
    volume_size_in_gb=20,
    max_runtime_in_seconds=3600
)

model_monitor.create_monitoring_schedule(
    monitor_schedule_name='bqx-ml-monitor',
    endpoint_input=endpoint_name,
    schedule_cron_expression='cron(0 */4 * * ? *)',  # Every 4 hours
    statistics=baseline_statistics,
    constraints=baseline_constraints
)
```

**Alert Thresholds:**
- Data drift: Feature distribution shift > 0.2 (KL divergence)
- Model drift: Prediction mean shift > 0.05
- Performance drift: MAE increase > 20%
- Latency drift: P99 > 300ms

**Alert Mechanism:** SNS topic → Email/Slack

### 4.5 Automated Retraining

**Trigger:** Drift detection alert OR weekly schedule

**Pipeline:**
```
CloudWatch Event (weekly OR drift alert)
    ↓
Lambda: Trigger Retraining
    ↓
SageMaker Pipeline:
  1. Fetch latest data from Aurora
  2. Run feature engineering (Processing Job)
  3. Train new model (Training Job)
  4. Evaluate on validation set
  5. If new_model_r2 > current_model_r2:
      - Deploy new model to endpoint
      - Archive old model
      - Send success notification
  6. Else:
      - Keep current model
      - Send investigation alert
```

**Frequency:** Weekly retraining (or on-demand when drift detected)

**Cost:** ~$10-15 per retraining cycle (all 28 pairs)

### 4.6 Deployment Deliverables

- [ ] Multi-model SageMaker endpoint deployed
- [ ] Lambda API function deployed with API Gateway
- [ ] Batch prediction pipeline operational
- [ ] Model Monitor configured with alerts
- [ ] Automated retraining pipeline tested
- [ ] Deployment documentation and runbook

---

<a name="phase-5"></a>
## Phase 5: Production Operations

**Duration:** Ongoing
**Status:** 🔨 To Build
**Dependencies:** Phase 4 complete

### 5.1 Monitoring Dashboards

**CloudWatch Dashboard:**
```
┌─────────────────────────────────────────────────┐
│ BQX ML Production Dashboard                    │
├─────────────────────────────────────────────────┤
│ Model Performance                               │
│  • R² (test set): 0.87  ▲ +0.02 vs last week   │
│  • MAE (vol-scaled): 0.15                       │
│  • Directional Accuracy: 62%                    │
│                                                 │
│ API Performance                                 │
│  • Request rate: 120/min                        │
│  • P50 latency: 85ms                            │
│  • P95 latency: 145ms                           │
│  • P99 latency: 189ms  ⚠ Approaching limit     │
│  • Error rate: 0.2%                             │
│                                                 │
│ Endpoint Health                                 │
│  • Instance count: 2 (auto-scaled)              │
│  • CPU utilization: 68%                         │
│  • Memory utilization: 52%                      │
│  • Model cache hit rate: 94%                    │
│                                                 │
│ Data Quality                                    │
│  • Missing features: 0.3% (within threshold)    │
│  • Outlier rate: 1.2%                           │
│  • Feature drift: No alerts                     │
│                                                 │
│ Cost (MTD)                                      │
│  • Training: $45                                │
│  • Inference: $180                              │
│  • Storage: $12                                 │
│  • Total: $237 / $400 budget (59%)              │
└─────────────────────────────────────────────────┘
```

### 5.2 Alerting Rules

**Critical Alerts (immediate action):**
1. **Endpoint Down:** API unavailable > 5 minutes
2. **Error Rate Spike:** Error rate > 5%
3. **Latency Degradation:** P99 > 500ms for 10 minutes
4. **Model Drift:** MAE increase > 50%

**Warning Alerts (investigate within 24h):**
5. **Moderate Drift:** MAE increase > 20%
6. **Feature Drift:** Distribution shift detected
7. **Cost Overrun:** Monthly cost > $350 (87.5% of budget)
8. **Low Cache Hit Rate:** < 80% (may need more instances)

### 5.3 Operational Runbook

#### 5.3.1 Incident: High Latency

**Symptom:** P99 latency > 300ms

**Investigation Steps:**
1. Check CloudWatch: Is CPU > 80%?
   - Yes → Auto-scaling should trigger, wait 10 minutes
   - No → Check model loading times (cold starts?)
2. Check model cache hit rate
   - <70% → Models being evicted, increase instance count
3. Check Aurora database response time
   - Slow queries → Add indexes or optimize queries

**Resolution:**
- Short-term: Manually increase instance count
- Long-term: Review feature extraction queries, optimize

#### 5.3.2 Incident: Model Drift Detected

**Symptom:** MAE increased by >20% vs baseline

**Investigation Steps:**
1. Check data quality: Are features correct?
2. Check market regime: Unusual volatility event?
3. Compare predictions vs actuals: Systematic bias?
4. Check feature distributions: Drift in specific features?

**Resolution:**
- Immediate: Trigger retraining with latest data
- If retraining doesn't help: Investigate feature engineering logic
- If market regime shift: Consider ensemble with regime-specific models

#### 5.3.3 Routine: Weekly Retraining

**Schedule:** Every Monday 02:00 UTC

**Steps:**
1. Automated pipeline fetches data from previous week
2. Retrain models on updated data
3. Validate on holdout set
4. If improved OR within 2% of current model:
   - Deploy to production
   - Archive old model
5. Send email report with metrics comparison

**Manual Review Trigger:**
- If new model R² < current model R² - 0.05
- If any critical feature missing

### 5.4 Cost Optimization

**Monthly Budget:** $400
**Current Estimated Cost:** ~$286

**Breakdown:**
- Training (monthly): $45
- Inference (24/7): $180
- Storage (S3): $12
- Monitoring: $49
- **Total:** $286 (72% of budget)

**Optimization Strategies:**
1. **Use Savings Plans:** 30-50% discount on compute (already applied)
2. **Reduce monitoring frequency:** Every 6 hours instead of 4 ($49 → $33)
3. **Use Spot Instances for training:** 70% discount ($45 → $14)
4. **Implement model pruning:** Reduce model size, faster inference

**Target Cost:** <$250/month (62.5% of budget, leaves 37.5% buffer)

### 5.5 Continuous Improvement

**Quarterly Reviews:**
1. **Feature Analysis:** Which features contribute most?
2. **Model Architecture:** Can we improve with newer techniques?
3. **Data Quality:** Any systematic issues?
4. **Cost Efficiency:** Optimization opportunities?

**Experiment Pipeline:**
- Test new features on 4 major pairs
- If R² improvement > 0.03 → Roll out to all pairs
- If no improvement → Archive experiment

---

<a name="resources"></a>
## Resource Requirements & Timeline

### Overall Timeline

| Phase | Duration | Wall Time (Parallel) | Status |
|-------|----------|---------------------|--------|
| Phase 0: Infrastructure | 3 days | 3 days | ✅ Complete |
| Phase 1: Data Foundation | 2 days | 2 days | ✅ Complete |
| Phase 1.5: Index Architecture | 22 hours | 22 hours | ✅ Complete |
| Phase 1.6: Feature Development | 80-100 hours | 25-30 hours | 🔄 In Progress |
| Phase 2: Feature Engineering | 15-20 hours | 15-20 hours | 🔨 To Build |
| Phase 3: Model Training | 30-40 hours | 10-15 hours | 🔨 To Build |
| Phase 4: Deployment | 20-25 hours | 20-25 hours | 🔨 To Build |
| Phase 5: Operations | Ongoing | Ongoing | 🔨 To Build |
| **TOTAL TO PRODUCTION** | **~200 hours** | **~80 hours** | **40% Complete** |

**Note:** Wall time assumes 4-6 parallel workers where applicable

### AWS Resource Requirements

**Compute:**
- **EC2 (current):** t3.2xlarge (already running)
- **SageMaker Processing:** ml.m5.2xlarge (on-demand, ~1-2 hours/day)
- **SageMaker Training:** ml.m5.xlarge or ml.p3.2xlarge (GPU for TFT)
- **SageMaker Endpoint:** ml.m5.xlarge (2-4 instances, auto-scaling)

**Storage:**
- **Aurora RDS:** Current + 60 GB (feature tables)
- **S3:** ~100 GB (models, datasets, logs)

**Cost Summary:**
- **Development (one-time):** ~$200-300 (training experiments)
- **Production (monthly):** ~$286 (inference + monitoring + retraining)
- **Total Year 1:** ~$3,700

### Team Requirements

**Phase 1-2 (Data & Features):**
- Data Engineer: 80 hours
- Skills: SQL, Python, psycopg2, pandas

**Phase 3 (Modeling):**
- ML Engineer: 40 hours
- Skills: scikit-learn, XGBoost, PyTorch, SageMaker

**Phase 4-5 (Deployment & Ops):**
- ML Platform Engineer: 40 hours
- Skills: SageMaker, Lambda, CloudWatch, DevOps

**Total: ~160 hours = 4 weeks @ 40 hours/week (1 person)**
**Or: 2 weeks with 2 people in parallel**

---

<a name="risks"></a>
## Risk Mitigation

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Model underperformance** (R² < 0.80) | High | Medium | Start with proven XGBoost; iterate with TFT only if needed |
| **Latency exceeds 200ms** | Medium | Low | Optimize feature extraction; use model caching; add instances |
| **Data quality issues** | High | Medium | Implement data validation pipeline; monitor feature distributions |
| **Cost overrun** (>$400/month) | Medium | Low | Use Savings Plans; monitor costs daily; optimize monitoring frequency |
| **Model drift not detected** | High | Low | Model Monitor with conservative thresholds; weekly manual review |

### Operational Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Endpoint downtime** | High | Low | Multi-AZ deployment; health checks; automated recovery |
| **Training pipeline failure** | Medium | Medium | Automated retries; alert on failure; keep previous model |
| **Feature engineering bugs** | High | Medium | Unit tests; integration tests; compare with baseline features |
| **AWS service outage** | High | Very Low | Multi-region failover (if critical); accept downtime for MVP |

### Schedule Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Feature build takes longer than expected** | Medium | Medium | Prioritize critical features; parallelize work; defer advanced features |
| **Model training needs more iterations** | Medium | Medium | Start with simple XGBoost; allocate 2-week buffer for tuning |
| **Deployment complexity** | Low | Low | Use SageMaker templates; follow AWS best practices |

---

## Appendices

### Appendix A: Database Schema Reference

**Tables:**
- M1 tables: `m1_{pair}` (28 tables)
- BQX tables: `bqx_{pair}` (28 parent, 336 partitions)
- REG_IDX: `reg_idx_{pair}` (28 parent, 336 partitions)
- REG_BQX: `reg_bqx_{pair}` (28 parent, 336 partitions)
- STATISTICS_IDX: `statistics_idx_{pair}` (28 parent, 364 partitions)
- STATISTICS_BQX: `statistics_bqx_{pair}` (to build)
- ... (see comprehensive_feature_inventory.md for full list)

### Appendix B: Feature Catalog

See: [docs/comprehensive_feature_inventory.md](./comprehensive_feature_inventory.md)

**Total: 730 base features + 332 derived features = 1,062 features**
**After selection: ~195 features for training**

### Appendix C: Model Comparison Matrix

| Model | R² (expected) | Training Time | Inference Latency | Cost (monthly) | Complexity |
|-------|--------------|---------------|-------------------|----------------|------------|
| Random Forest | 0.75-0.82 | 5 hours | 50ms | $150 | Low |
| XGBoost | 0.78-0.85 | 8 hours | 60ms | $180 | Medium |
| TFT (GPU) | 0.85-0.92 | 60 hours | 80ms | $350 | High |
| Ensemble (XGB+TFT) | 0.86-0.93 | 68 hours | 100ms | $400 | High |

**Recommendation:** Start with XGBoost, evaluate TFT if budget allows

### Appendix D: References

1. [User Expectations Document](./docs/BQX ML User Expectations 2025 1112.docx)
2. [Comprehensive Feature Inventory](./docs/comprehensive_feature_inventory.md)
3. [Dual Feature Architecture Rationalization](./docs/dual_feature_architecture_rationalization.md)
4. [AirTable Project Plan](https://airtable.com/appR3PPnrNkVo48mO)

---

## Approval & Sign-off

**Plan Author:** BQX ML Team (AI-Assisted)
**Date:** 2025-11-12
**Version:** 2.0 - Comprehensive Refactor

**Approval Required From:**
- [ ] Project Sponsor (User)
- [ ] Technical Lead
- [ ] Cost Manager

**Next Steps After Approval:**
1. Execute Phase 1.6.9 (table renaming) - 1 hour
2. Begin parallel Phase 1.6 feature builds - 25-30 hours
3. Develop feature engineering pipeline - 15-20 hours
4. Start model training experiments - 10-15 hours

**Estimated Time to First Production Model:** 6-8 weeks

---

**END OF MASTER PLAN**
