# Phase 2: Parallel Execution Plan - All Three Tracks

**Date:** 2025-11-13
**Status:** Ready to Execute
**Strategy:** 3 parallel tracks executing simultaneously
**Duration:** 3 weeks to first MVP, 18 weeks to completion

---

## Executive Summary

All three recommended options can be executed **in parallel** with no conflicts:

- **Track 1 (Feature Population - Wave 1):** Implement bollinger_bqx, statistics_bqx, technical_indicators workers
- **Track 2 (Regression Features):** Create reg_rate/reg_bqx schemas and populate
- **Track 3 (MVP Pipeline):** Build extraction/lagging/selection/dataset pipeline with existing 159 features

**Parallelization is Safe Because:**
1. Independent data sources (all read from M1 tables or existing features)
2. No write conflicts (different database tables)
3. Track 3 doesn't write to database at all (creates pipeline code and datasets)
4. No circular dependencies

---

## Parallel Tracks Overview

```
Week 1    Week 2    Week 3    Week 4    Week 5    Week 6    Week 7
|---------|---------|---------|---------|---------|---------|---------|
Track 1:  [Bollinger_BQX]--[Statistics_BQX]--[Technical Indicators]-->
          └─ 94 features in 9 days → 253 total (23.9%)

Track 2:  [Create Schemas]-[Regression Population (10 days)]--------->
          └─ 180 features in 11 days → 433 total (40.8%)

Track 3:  [Extraction]--[Lagging]--[Selection]--[Datasets]-[Test]-->
          └─ MVP Pipeline ready in 14-18 days with 159 features
```

**Convergence Point (Day 21):**
- Track 1: ✅ 253 features populated
- Track 2: ✅ 433 features populated
- Track 3: ✅ MVP pipeline operational
- **Combined:** 433 unique features + validated pipeline = Production-ready system

---

## Track 1: Wave 1 Feature Population (Option A)

**Owner:** Feature Engineering Team / Worker 1
**Duration:** 9 days
**Objective:** Complete BQX counterparts + technical indicators

### Week 1: Bollinger + Statistics BQX

#### Day 1-2: Bollinger BQX Worker
**Script:** `scripts/ml/populate_bollinger_bqx_worker.py`

```python
# Implementation
class BollingerBQXWorker(FeaturePopulationWorker):
    def calculate_features(self, df):
        # Read BQX momentum (w15, w30, w45, w60, w75)
        # For each window:
        #   - SMA ± k*std (upper/middle/lower bands)
        #   - Band width
        #   - %B (position within bands)
        # Return 10 features
```

**Input:** M1 BQX momentum columns
**Output:** 700 tables (28 pairs × 25 monthly partitions), 10 features
**Validation:** Compare to bollinger_rate patterns

#### Day 3-4: Statistics BQX Worker
**Script:** `scripts/ml/populate_statistics_bqx_worker.py`

```python
class StatisticsBQXWorker(FeaturePopulationWorker):
    def calculate_features(self, df):
        # For each window (w15, w30, w45, w60, w75):
        #   - Rolling mean, std, skew, kurtosis
        #   - Min, max
        # Return 24 features
```

**Input:** M1 BQX momentum
**Output:** 700 tables, 24 features
**Validation:** Statistical sanity checks (mean ≈ 0, std > 0)

### Week 2: Technical Indicators (Rate + BQX)

#### Day 5-9: Technical Indicators Worker
**Script:** `scripts/ml/populate_technical_indicators_worker.py`

```python
class TechnicalIndicatorsWorker(FeaturePopulationWorker):
    def calculate_features(self, df):
        # Rate domain (rate_index):
        #   - RSI (14, 21)
        #   - MACD (12, 26, 9)
        #   - Stochastic (14)
        #   - ADX (14)
        #   - CCI (20)
        # BQX domain (BQX momentum):
        #   - Same indicators
        # Return 30 features per domain (60 total)
```

**Library:** TA-Lib or pandas_ta
**Input:** M1 rate_index and BQX momentum
**Output:** 1,400 tables (700 rate + 700 bqx), 60 features
**Validation:** Indicator values within expected ranges (RSI 0-100, etc.)

### Track 1 Deliverables

**Day 9 Completion:**
- ✅ 94 new features populated
- ✅ 253 total features (159 existing + 94 new)
- ✅ 23.9% feature coverage
- ✅ 3 production workers deployed
- ✅ 2,100 new database tables with data

---

## Track 2: Regression Features (Option B)

**Owner:** Advanced Features Team / Worker 2
**Duration:** 11 days
**Objective:** Create missing regression foundation

### Day 1: Create Regression Schemas

**Issue:** reg_rate and reg_bqx tables don't exist (audit finding)

#### Script: `scripts/ml/create_regression_tables.sql`

```sql
-- For each of 28 pairs, create parent + partitions:

CREATE TABLE IF NOT EXISTS bqx.reg_rate_{pair} (
    ts_utc TIMESTAMP NOT NULL,
    -- Window w15 (15 features)
    a2_idx_w15 NUMERIC, a1_idx_w15 NUMERIC, b_idx_w15 NUMERIC,
    r2_idx_w15 NUMERIC, rmse_idx_w15 NUMERIC,
    -- ... repeat for w30, w45, w60, w75, agg
    -- 6 windows × 15 metrics = 90 features
    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);

-- Create 336 partitions for rate (Jul 2024 - Jun 2025)
-- Create 672 partitions for bqx (Full 2024-2025)
```

**Output:** 1,064 tables created (28 pairs × 38 partitions)
**Duration:** 4 hours execution

### Day 2-11: Populate Regression Features

#### Script: `scripts/ml/populate_regression_features_worker.py`

```python
class RegressionFeaturesWorker(FeaturePopulationWorker):
    def calculate_features(self, df):
        features = {}

        for window in ['w15', 'w30', 'w45', 'w60', 'w75', 'agg']:
            # Parabolic regression: y = a2*x^2 + a1*x + b
            # For rate_index:
            x, y = self.get_window_data(df['rate_index'], window)
            a2, a1, b, r2, rmse = self.fit_parabola(x, y)

            features[f'a2_idx_{window}'] = a2
            features[f'a1_idx_{window}'] = a1
            features[f'b_idx_{window}'] = b
            features[f'r2_idx_{window}'] = r2
            features[f'rmse_idx_{window}'] = rmse
            # ... + 10 more metrics per window

        # Repeat for BQX momentum (reg_bqx)
        # Return 90 features per domain
```

**Complexity:** Medium - polynomial fitting, rolling windows
**Input:** M1 rate_index and BQX momentum
**Output:** 1,064 tables populated, 180 features
**Parallel Processing:** 6 workers per partition batch
**Duration:** 10 days (large dataset, complex computation)

### Track 2 Deliverables

**Day 11 Completion:**
- ✅ 180 regression features created and populated
- ✅ 433 total features (253 from Track 1 + 180 new)
- ✅ 40.8% feature coverage
- ✅ Critical foundation for Wave 5 (parabolic comparisons)
- ✅ 1,064 new tables with regression coefficients

---

## Track 3: MVP Pipeline with 159 Features (Option C)

**Owner:** ML Pipeline Team / Worker 3
**Duration:** 14-18 days
**Objective:** Validate end-to-end pipeline architecture

### Week 1: Feature Extraction (Day 1-5)

#### Task 3.1: Database Query Optimization

**Script:** `scripts/ml/extract_features_from_db.py`

```python
def extract_features_for_pair(pair, start_date, end_date):
    """
    Extract all 159 populated features for given pair and date range.
    """
    # Efficient query joining:
    # - bollinger_rate_{pair}
    # - statistics_rate_{pair}
    # - volume_features_{pair}
    # - spread_features_{pair}
    # - time_features_{pair}

    query = """
        SELECT
            b.ts_utc,
            -- 10 bollinger features
            b.bb_upper_20_idx, b.bb_middle_20_idx, ...,
            -- 24 statistics features
            s.mean_idx_w15, s.std_idx_w15, ...,
            -- 70 volume features
            v.volume_mean_w15, v.volume_std_w15, ...,
            -- 35 spread features
            sp.spread_mean_w15, sp.spread_std_w15, ...,
            -- 20 time features
            t.hour, t.day_of_week, t.session, ...
        FROM bqx.bollinger_rate_{pair} b
        JOIN bqx.statistics_rate_{pair} s ON b.ts_utc = s.ts_utc
        JOIN bqx.volume_features_{pair} v ON b.ts_utc = v.ts_utc
        JOIN bqx.spread_features_{pair} sp ON b.ts_utc = sp.ts_utc
        JOIN bqx.time_features_{pair} t ON b.ts_utc = t.ts_utc
        WHERE b.ts_utc BETWEEN %s AND %s
        ORDER BY b.ts_utc;
    """

    df = pd.read_sql(query, conn, params=[start_date, end_date])
    return df
```

**Output:** 28 Parquet files (one per pair), 159 columns each
**Duration:** 3 days

#### Task 3.2: Data Validation

**Script:** `scripts/ml/validate_extracted_features.py`

```python
def validate_features(df):
    # Check for NaN/inf
    # Verify temporal ordering
    # Statistical sanity checks
    # Check for future leakage
```

**Duration:** 2 days

### Week 2: Lagging + Selection (Day 6-12)

#### Task 3.3: Lagging Strategy

**Script:** `scripts/ml/apply_lagging_strategy.py`

```python
def apply_lags(df):
    """
    Apply temporal lags to create ~400 features from 159 base.
    """
    laggable_features = [
        # Bollinger (10), Statistics (24), Volume (70), Spread (35)
        # Total: 139 laggable features
    ]
    non_laggable_features = [
        # Time features (20) - categorical, current state only
    ]

    lagged_df = df[non_laggable_features].copy()

    # Apply 3 lags (60, 120, 180 min) to laggable features
    for feature in laggable_features:
        lagged_df[feature] = df[feature]  # Base (t=0)
        lagged_df[f'{feature}_lag60'] = df[feature].shift(60)
        lagged_df[f'{feature}_lag120'] = df[feature].shift(120)
        lagged_df[f'{feature}_lag180'] = df[feature].shift(180)

    # Result: 139 × 4 (base + 3 lags) + 20 (non-laggable) = 576 features
    return lagged_df
```

**Output:** ~576 features per pair (159 base → 576 with lags)
**Duration:** 2 days

#### Task 3.4: Feature Selection (Random Forest)

**Script:** `scripts/ml/select_features_rf.py`

```python
def select_top_features(X, y, n_features=100):
    """
    Select top N features using Random Forest importance.
    """
    # Train Random Forest
    rf = RandomForestRegressor(n_estimators=100, max_depth=10)
    rf.fit(X, y)

    # Get feature importance
    importances = rf.feature_importances_

    # Select top N
    top_indices = np.argsort(importances)[-n_features:]
    selected_features = X.columns[top_indices]

    return selected_features, importances
```

**Target:** Select top 100 features from 576 (MVP subset)
**Duration:** 3 days

### Week 3: Dataset Creation + Testing (Day 13-18)

#### Task 3.5: Train/Val/Test Split

**Script:** `scripts/ml/create_datasets.py`

```python
def create_datasets(df, selected_features):
    # Temporal split: 70/15/15
    n = len(df)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    X_train = df[selected_features].iloc[:train_end]
    X_val = df[selected_features].iloc[train_end:val_end]
    X_test = df[selected_features].iloc[val_end:]

    # Create targets (BQX change at 15/30/45/60 min horizons)
    y_train = create_targets(df.iloc[:train_end])
    y_val = create_targets(df.iloc[train_end:val_end])
    y_test = create_targets(df.iloc[val_end:])

    return (X_train, y_train), (X_val, y_val), (X_test, y_test)
```

**Output:** Train/val/test Parquet files for 28 pairs
**Duration:** 2 days

#### Task 3.6: End-to-End Validation

**Script:** `scripts/ml/test_mvp_pipeline.py`

```python
def test_pipeline():
    # 1. Extract features from DB
    # 2. Apply lagging
    # 3. Select features
    # 4. Create datasets
    # 5. Train simple baseline model
    # 6. Evaluate on test set
    # 7. Generate report
```

**Validation Criteria:**
- ✅ Pipeline runs end-to-end without errors
- ✅ No future data leakage (validate timestamps)
- ✅ Baseline model achieves reasonable R² (>0.1)
- ✅ Dataset sizes correct (70/15/15 split)
- ✅ All features have valid values (no NaN/inf)

**Duration:** 3 days

### Track 3 Deliverables

**Day 18 Completion:**
- ✅ Complete extraction pipeline (DB → Parquet)
- ✅ Lagging strategy implemented and validated
- ✅ Feature selection pipeline operational
- ✅ Train/val/test datasets for 28 pairs
- ✅ End-to-end pipeline validated with 100-feature MVP
- ✅ Baseline model trained and evaluated
- ✅ Pipeline ready to scale to 250+ features

---

## Parallel Execution Timeline

### Week 1 (Day 1-7)

| Day | Track 1 (Wave 1) | Track 2 (Regression) | Track 3 (Pipeline) |
|-----|------------------|----------------------|-------------------|
| 1 | Bollinger BQX (start) | Create reg schemas | Extract features (start) |
| 2 | Bollinger BQX (complete) | Regression worker (start) | Extract features |
| 3 | Statistics BQX (start) | Regression population | Extract features |
| 4 | Statistics BQX (complete) | Regression population | Extract features |
| 5 | Technical indicators (start) | Regression population | Extract features (complete) |
| 6 | Technical indicators | Regression population | Validate extraction |
| 7 | Technical indicators | Regression population | Validate extraction |

### Week 2 (Day 8-14)

| Day | Track 1 (Wave 1) | Track 2 (Regression) | Track 3 (Pipeline) |
|-----|------------------|----------------------|-------------------|
| 8 | Technical indicators | Regression population | Apply lagging |
| 9 | Technical indicators (complete) | Regression population | Apply lagging |
| 10 | **Track 1 DONE: 253 features** | Regression population | Feature selection |
| 11 | — | Regression population (complete) | Feature selection |
| 12 | — | **Track 2 DONE: 433 features** | Feature selection |
| 13 | — | — | Create datasets |
| 14 | — | — | Create datasets |

### Week 3 (Day 15-21)

| Day | Track 1 (Wave 1) | Track 2 (Regression) | Track 3 (Pipeline) |
|-----|------------------|----------------------|-------------------|
| 15 | — | — | Test pipeline |
| 16 | — | — | Test pipeline |
| 17 | — | — | Test pipeline |
| 18 | — | — | **Track 3 DONE: MVP Pipeline** |
| 19 | — | — | Documentation |
| 20 | — | — | Documentation |
| 21 | **CONVERGENCE** | **CONVERGENCE** | **CONVERGENCE** |

---

## Convergence Point (Day 21)

### Combined Deliverables

**Feature Database:**
- ✅ 433 features populated (40.8%)
  - 159 existing (bollinger_rate, statistics_rate, volume, spread, time)
  - 94 from Track 1 (bollinger_bqx, statistics_bqx, technical_rate/bqx)
  - 180 from Track 2 (reg_rate, reg_bqx)

**ML Pipeline:**
- ✅ Extraction pipeline operational
- ✅ Lagging strategy validated
- ✅ Feature selection working
- ✅ Dataset creation automated
- ✅ Baseline model trained

**Production Readiness:**
- ✅ Can now scale pipeline to 433 features
- ✅ Can run full feature selection (433 → ~150 selected)
- ✅ Can train production models
- ✅ Can continue Wave 2-6 feature population (543 → 999 features)

---

## Resource Allocation

### Team Structure (3 parallel workers)

**Worker 1: Feature Population Specialist**
- Responsible for: Track 1 (Wave 1 workers)
- Skills: Python, pandas, NumPy, TA-Lib, database operations
- Tools: psycopg2, parallel processing, data validation

**Worker 2: Advanced Features Engineer**
- Responsible for: Track 2 (Regression features)
- Skills: Statistical modeling, polynomial regression, optimization
- Tools: NumPy, scipy, statsmodels, parallel processing

**Worker 3: ML Pipeline Engineer**
- Responsible for: Track 3 (MVP pipeline)
- Skills: ML pipelines, feature engineering, model training
- Tools: pandas, scikit-learn, Random Forest, dataset creation

### Infrastructure Requirements

**Compute:**
- 3 EC2 instances (one per track)
- Recommended: r6i.2xlarge (8 vCPU, 64 GB RAM)
- Storage: 500 GB SSD per instance

**Database:**
- Aurora PostgreSQL cluster (existing)
- Read replicas for parallel extraction (Track 3)
- Connection pooling for concurrent workers

**Coordination:**
- Daily sync meetings (15 min)
- Shared progress tracking (AirTable or similar)
- Code reviews before merging

---

## Risk Management

### Potential Conflicts

**❌ Database Connection Limits**
- **Risk:** 3 parallel tracks × 6 workers each = 18 concurrent connections
- **Mitigation:** Connection pooling, stagger heavy operations
- **Max connections:** Aurora default = 100+, sufficient for 18 workers

**❌ Disk Space on Database**
- **Risk:** 433 features × 10.3M rows × 28 pairs = large storage
- **Current:** ~51M rows (159 features) = ~10 GB
- **Projected:** 433 features × ~27 GB = reasonable
- **Mitigation:** Monitor disk usage, partition cleanup if needed

**❌ Worker Dependencies**
- **Risk:** Track 3 extraction might need features from Track 1/2
- **Mitigation:** Track 3 uses existing 159 features only (independent)
- **Future:** Can re-run Track 3 with 433 features after convergence

### Success Criteria per Track

**Track 1:**
- ✅ 94 features populated within 9 days
- ✅ <1% missing values per feature
- ✅ Data quality validation passes
- ✅ Worker scripts production-ready

**Track 2:**
- ✅ 180 regression features created and populated within 11 days
- ✅ Regression R² > 0.7 for majority of fits
- ✅ Schema creation successful
- ✅ Backward compatibility maintained

**Track 3:**
- ✅ End-to-end pipeline functional within 18 days
- ✅ Baseline model R² > 0.1 on test set
- ✅ No future data leakage detected
- ✅ Pipeline scales to 433+ features

---

## Post-Convergence Plan (Day 22+)

### Phase 2.1b: Continue Feature Population

**Weeks 4-6 (Wave 3):**
- Fibonacci features (20)
- Correlation features (90)
- **Goal:** 543 features (51.2%) - **50% milestone**

**Weeks 7-18 (Waves 4-6):**
- Advanced features (error correction, HMM, volatility)
- Spectral features (FFT, wavelets, SSA)
- Final features (microstructure, regime, liquidity)
- **Goal:** 999 features (94.2%)

### Phase 2.2-2.5: Scale Pipeline

**Re-run Track 3 with 433 features:**
1. Extract 433 features from database
2. Apply lagging → ~1,100 features
3. Select top 250 features
4. Create production datasets
5. Train production models

---

## Monitoring and Reporting

### Daily Metrics

**Track 1:**
- Features populated today / total
- Tables created / total
- Average rows per table
- Execution time per partition

**Track 2:**
- Regression fits completed / total
- Average R² per window
- Tables populated / total
- Errors encountered

**Track 3:**
- Pipeline stages completed
- Features extracted / validated
- Model baseline R²
- Dataset sizes

### Weekly Milestones

**Week 1:**
- Track 1: 34 features (bollinger_bqx + statistics_bqx)
- Track 2: Regression schemas created
- Track 3: Feature extraction complete

**Week 2:**
- Track 1: 94 features complete (technical indicators done)
- Track 2: 50% regression population
- Track 3: Lagging + selection complete

**Week 3:**
- Track 1: ✅ Complete
- Track 2: ✅ Complete
- Track 3: ✅ MVP pipeline operational

---

## Conclusion

All three options (A, B, C) can execute **in parallel** with no conflicts, delivering:

**Day 21 Results:**
- ✅ 433 features populated (40.8% coverage)
- ✅ Production-ready ML pipeline validated
- ✅ Baseline model trained and evaluated
- ✅ 3 feature population workers deployed
- ✅ Ready to scale to 1,000 features

**Next Phase:**
- Continue Waves 3-6 feature population (543 → 999 features)
- Scale pipeline to full 250-feature production system
- Begin Phase 3: Model training and deployment

🚀 **Ready to Begin 3-Track Parallel Execution** 🚀

---

**Execution Command:**
```bash
# Start all three tracks simultaneously:
./scripts/ml/parallel_executor.sh \
  --track1-start \
  --track2-start \
  --track3-start \
  --duration 21 \
  --sync-daily
```
