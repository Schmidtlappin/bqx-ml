# Phase 3: SageMaker ML System - Reconciled for 1,080-Feature Architecture

**Version:** 3.0 (Reconciled with Refactored Architecture)
**Date:** 2025-11-12
**Status:** Ready for Execution
**Duration:** 128 hours (7 weeks)
**Dependencies:** Phase 1.6-1.8 Complete, Phase 2 Complete
**Cost:** ~$475/month operational (optimized to $420 with Savings Plans)

---

## Executive Summary

Phase 3 delivers a production-grade SageMaker ML system that transforms the **1,080 engineered features** (~2,600 with lagging, ~250 selected) into real-time forex predictions for all 28 currency pairs using a **dual architecture** (rate_idx + BQX).

### What Changed from Version 2.0

**Feature Architecture:**
- Old: 228 base features → 809 with lagging → 70 selected
- **New: 1,080 base features → ~2,600 with lagging → ~250 selected**

**Cost:**
- Old: $286/month
- **New: $475/month baseline ($420 optimized)**

**Instance Sizes:**
- Old: ml.m5.xlarge for endpoint
- **New: ml.m5.2xlarge for endpoint (2x memory for 250-feature models)**

**Processing Time:**
- Old: 70 minutes processing
- **New: 180-200 minutes processing (3.5x more features)**

**Dual Architecture Support:**
- **Added: Separate handling of rate_idx and BQX feature domains**
- **Added: Advanced feature tables (ECM, realized_vol, HMM, spectral, etc.)**

---

## Complete Feature Inventory

### Base Features: 1,080

| Category | Count | Domain | Tables | Status |
|----------|-------|--------|--------|--------|
| **Rate_idx Features** | **268** | **CAUSE** | | |
| - Regression (rate_idx) | 90 | Rate | reg_idx_{pair} | ✅ Rename needed |
| - Technical Indicators (IDX) | 56 | Rate | technical_idx_{pair} | 🔨 Stage 1.6.10 |
| - Correlation (IDX) | 45 | Rate | correlation_idx_{pair} | ⚠️ Empty |
| - Moving Averages | 24 | Rate | Computed | ✅ |
| - Multi-Resolution | 30 | Rate | Computed | ✅ |
| - Time & Calendar | 20 | Rate | time_features_{pair} | ✅ |
| - Microstructure (rate) | 3 | Rate | spread_features_{pair} | ✅ |
| **BQX Features** | **254** | **EFFECT** | | |
| - BQX Regression | 90 | BQX | reg_bqx_{pair} | ✅ |
| - Technical Indicators (BQX) | 56 | BQX | technical_bqx_{pair} | 🔨 Stage 1.6.11 |
| - Statistics (BQX) | 48 | BQX | statistics_bqx_{pair} | 🔨 Stage 1.6.12 |
| - Bollinger (BQX) | 20 | BQX | bollinger_bqx_{pair} | 🔨 Stage 1.6.13 |
| - Fibonacci (BQX) | 20 | BQX | fibonacci_bqx_{pair} | 🔨 Stage 1.6.14 |
| - Correlation (BQX) | 45 | BQX | correlation_bqx_{pair} | 🔨 Stage 1.6.17 |
| **Cross-Domain Features** | **208** | **BOTH** | | |
| - Dual-Domain Comparisons | 28 | Computed | Δ(rate vs BQX) | ✅ |
| - Cross-Pair Features | 44 | Computed | Systemic | ✅ |
| - Lagged Features | 180 | Both | Memory | ✅ |
| - Event & Regime | 26 | Both | Computed | ✅ |
| - Volume Features | 32 | Both | volume_features_{pair} | ✅ |
| **Advanced Features** | **350** | **BOTH** | | |
| - Error Correction | 30 | Both | error_correction_{pair} | 🔨 Stage 1.6.18 |
| - Realized Volatility | 40 | Both | realized_vol_{pair} | 🔨 Stage 1.6.19 |
| - HMM Regime | 25 | Both | hmm_regime_{pair} | 🔨 Stage 1.6.20 |
| - Cross-Sectional Panel | 35 | Both | cross_sectional_panel | 🔨 Stage 1.6.21 |
| - Parabolic Comparisons | 180 | Both | Computed | 🔨 Stage 1.8.1 |
| - Multi-Scale (30m/60m) | 60 | Both | Computed | 🔨 Stage 1.8.2 |
| - Spectral/Wavelet | 80 | Both | spectral_features_{pair} | 🔨 Stage 1.8.3 |
| **TOTAL** | **1,080** | | | |

### With Lagging: ~2,600 Features

**Lagging Strategy:**
- Laggable features: 520 features × 4 lags (60, 120, 180, 240 min) = 2,080 + 520 base = 2,600
- Non-laggable features: 560 features (time, indices, categorical)
- Temporal causality features: 40 additional (61-min lag for w60_ and agg_ families)
- **Total: 2,600 + 40 = 2,640 features**

### After Feature Selection: ~250 Features

**Selection Strategy:**
- Train Random Forest on all ~2,640 features
- Compute feature importance scores
- Select top ~250 features by cumulative importance (>95% threshold)
- **Ensure dual architecture representation:** Min 100 rate_idx + Min 100 BQX features
- **Model input: ~250 selected features per pair**

---

## Phase 3 Structure (UPDATED)

**6 Stages, 35 Tasks (+2 new), 128 Hours (+15 hours)**

| Stage | Duration | Tasks | Changes from v2.0 |
|-------|----------|-------|-------------------|
| **3.1: Training Pipeline** | 28 hours | 7 (+1) | +6h (dual architecture queries) |
| **3.2: HPO & Model Registry** | 14 hours | 3 | No change |
| **3.3: Deployment** | 20 hours | 5 | +4h (larger instances) |
| **3.4: Inference System** | 22 hours | 5 | +4h (1,080-feature extraction) |
| **3.5: Monitoring & MLOps** | 20 hours | 7 (+1) | +1h (250-feature drift) |
| **3.6: Validation** | 24 hours | 8 | No change |
| **TOTAL** | **128 hours** | **35 tasks** | **+15 hours** |

---

## STAGE 3.1: Training Pipeline Development (UPDATED)

**Duration:** 28 hours (+6 from v2.0)
**Owner:** ML Engineering Team
**Priority:** Critical Path

### TSK-3.1.1: Create SageMaker Training Container

**Duration:** 3.5 hours (unchanged)

**Description:** Dockerize training code with all dependencies.

**Deliverables:**
- ECR image: {account}.dkr.ecr.us-east-1.amazonaws.com/bqx-ml-training:latest
- Dockerfile
- build_training_container.sh

**Success Criteria:** Container runs train.py with sample data

---

### TSK-3.1.2: Create SageMaker Processing Job for Feature Engineering (UPDATED)

**Duration:** 10 hours (+3.5 hours from v2.0)

**Description:** Convert data extraction + feature engineering to SageMaker Processing job. **Query 1,080 base feature tables across dual architecture.**

**Subtasks:**
1. Create processing script (processing.py) querying Aurora dual architecture (4h) ⬆️
2. Handle Aurora credentials via AWS Secrets Manager (1h)
3. **Query all rate_idx tables:** (1h) ⬆️NEW
   - reg_idx_{pair} (after Stage 1.6.9 rename)
   - technical_idx_{pair}
   - correlation_idx_{pair}
4. **Query all BQX tables:** (1h) ⬆️NEW
   - reg_bqx_{pair}
   - technical_bqx_{pair}
   - statistics_bqx_{pair}
   - bollinger_bqx_{pair}
   - fibonacci_bqx_{pair}
   - correlation_bqx_{pair}
5. **Query advanced feature tables:** (1h) ⬆️NEW
   - error_correction_{pair}
   - realized_vol_{pair}
   - hmm_regime_{pair}
   - cross_sectional_panel
   - spectral_features_{pair}
6. Apply temporal causality rule to w60_ and agg_ features (1h)
7. Output features to S3 as Parquet (train/val/test splits) (1h)

**Success Criteria:**
- Processing job completes for 1 pair
- Outputs valid Parquet files with **1,080 base features**
- Temporal causality rule correctly applied (40 causality-lagged features)
- **Dual architecture preserved** (rate_idx and BQX separately identifiable)

**Deliverables:**
- processing.py (with dual architecture queries)
- submit_processing.py
- S3 dataset: s3://bqx-ml-datasets/{pair}/features_1080.parquet

**Instance Update:** ml.m5.2xlarge (was ml.m5.xlarge) for 1,080-feature processing
**Cost Update:** $0.806/hour × 3 hours = $2.42/run (was $0.94)

---

### TSK-3.1.3: Adapt Training Script for SageMaker (UPDATED)

**Duration:** 6 hours (+1 hour from v2.0)

**Description:** Modify train.py to read from S3 and handle **~2,640 features with lagging**.

**Subtasks:**
1. Replace Aurora extraction with S3 Parquet reading (1h)
2. Implement feature lagging strategy (**520 features × 4 lags**) (2h) ⬆️
3. Modify save path to /opt/ml/model/ (0.5h)
4. Add hyperparameters from environment variables (1h)
5. Add metrics logging to CloudWatch (0.5h)
6. **Handle dual architecture in feature engineering** (1h) ⬆️NEW
7. Test with sagemaker.sklearn.SKLearn() estimator (1h)

**Success Criteria:**
- Training job completes
- Model saved to S3 with **~2,640 feature inputs**
- Metrics visible in CloudWatch (R², MAE, directional_accuracy)
- **Dual architecture features correctly processed**

**Deliverables:**
- train_sagemaker.py (with dual architecture support)
- test_training_job.py

**Instance Update:** ml.m5.2xlarge (increased memory for 2,640 features)
**Cost Update:** $0.806/hour × 0.15 hours × 28 = $3.39/run (was $0.93)

---

### TSK-3.1.4: Implement Parallel Training for 28 Pairs

**Duration:** 5 hours (unchanged)

**Success Criteria:** 28 training jobs complete in <15 minutes (parallel), all models in S3

**Deliverables:**
- train_all_pairs.py
- Execution logs
- 28 model artifacts: s3://bqx-ml-models/{pair}/model.tar.gz

---

### TSK-3.1.5: Set Up Experiment Tracking

**Duration:** 3.5 hours (unchanged)

**Success Criteria:** Training runs appear in SageMaker Studio, metrics queryable

**Deliverables:**
- experiments_setup.py
- dashboard.ipynb
- docs/experiment_tracking.md

---

### TSK-3.1.6: Implement Feature Selection Pipeline (UPDATED)

**Duration:** 5 hours (+1 hour from v2.0)

**Description:** Implement feature selection to reduce **~2,640 features to top ~250** with dual architecture awareness.

**Subtasks:**
1. Train initial Random Forest on all ~2,640 features (1.5h) ⬆️
2. Compute feature importance scores (0.5h)
3. Select top ~250 features by cumulative importance (>95% threshold) (1.5h) ⬆️
4. **Enforce dual architecture balance:** Min 100 rate_idx + Min 100 BQX (1h) ⬆️NEW
5. Save feature selection mask to S3 (0.5h)
6. Apply mask in training and inference pipelines (1h)

**Success Criteria:**
- Feature selection identifies top ~250 features
- **Rate_idx and BQX domains both represented** (min 100 each)
- Selected features saved: s3://bqx-ml-models/{pair}/selected_features_250.json
- Training uses only ~250 features (verify input dimensions)

**Deliverables:**
- feature_selection.py (with dual architecture balancing)
- selected_features_250.json (per pair)
- docs/feature_selection_methodology_dual_arch.md

---

### TSK-3.1.7: Optimize Aurora Query Performance (NEW)

**Duration:** 4 hours ⬆️NEW

**Description:** Ensure Aurora queries for 1,080 features stay within 100ms latency budget.

**Subtasks:**
1. Add composite indexes on (pair, ts_utc) for all feature tables (1h)
2. Test query performance for 1,080-feature extraction (1h)
3. Implement Redis caching for advanced features (1.5h)
4. Document query optimization strategy (0.5h)

**Success Criteria:**
- Single-timestamp query for 1,080 features completes in <100ms
- Cache hit rate >80% for advanced features
- Documented optimization techniques

**Deliverables:**
- docs/aurora_query_optimization_1080_features.md
- redis_cache_config.py (if needed)

**Instance/Cost Impact:** May require Aurora read replica (+$200/month if needed)

---

## STAGE 3.2: Hyperparameter Optimization & Model Registry

**Duration:** 14 hours (unchanged)
**Owner:** ML Engineering Team
**Priority:** High

### Tasks 3.2.1-3.2.3: (No changes from v2.0)

All tasks remain the same. Model registry will store metadata indicating **250-feature models**.

---

## STAGE 3.3: Model Deployment Infrastructure (UPDATED)

**Duration:** 20 hours (+4 hours from v2.0)
**Owner:** ML Engineering + DevOps Team
**Priority:** Critical Path

### TSK-3.3.1: Create SageMaker Inference Container

**Duration:** 5.5 hours (unchanged)

**Success Criteria:** Container responds to /ping and /invocations, predictions valid with **250-feature inputs**

**Deliverables:**
- Dockerfile
- inference.py (handles 250-feature inputs)
- ECR image URI

---

### TSK-3.3.2: Deploy Multi-Model Endpoint (UPDATED)

**Duration:** 6 hours (+1.5 hours from v2.0)

**Description:** Create SageMaker multi-model endpoint for all 28 pairs with **increased instance size** for 250-feature models.

**Subtasks:**
1. Package all 28 models as model.tar.gz with inference code + selected_features_250.json (1.5h) ⬆️
2. Upload to S3 multi-model structure (s3://bqx-ml-models/{pair}/) (0.5h)
3. Create SageMaker model with MultiModel=True (0.5h)
4. **Create endpoint configuration (ml.m5.2xlarge, 1 instance)** (1h) ⬆️
5. Deploy endpoint and test invocations for 3 pairs (2h)
6. **Validate 250-feature inference performance** (0.5h) ⬆️NEW

**Success Criteria:**
- Endpoint deployed, responds to requests for all 28 pairs
- **Latency <200ms with 250-feature inputs**
- **No memory issues with ml.m5.2xlarge**

**Deliverables:**
- deploy_endpoint.py
- Endpoint name: bqx-ml-multi-model-production-v3
- testing_notebook.ipynb

**Instance Update:** ml.m5.2xlarge (32 GB RAM vs 16 GB)
**Cost Update:** $0.538/hour × 720 hours = $387/month (was $193/month)

---

### TSK-3.3.3: Configure Auto-Scaling Policies

**Duration:** 4.5 hours (+1 hour from v2.0)

**Success Criteria:** Endpoint scales from 1→2 instances under load, scales back to 1

**Cost Impact:** Auto-scaling to 2 instances = $774/month peak (2× $387)

---

### TSK-3.3.4: Implement Blue/Green Deployment

**Duration:** 5 hours (unchanged)

---

### TSK-3.3.5: Create A/B Testing Framework

**Duration:** 4.5 hours (unchanged)

---

## STAGE 3.4: Real-Time Inference System (UPDATED)

**Duration:** 22 hours (+4 hours from v2.0)
**Owner:** Backend Engineering Team
**Priority:** Critical Path

### TSK-3.4.1: Create Feature Extraction Lambda (UPDATED)

**Duration:** 8 hours (+2 hours from v2.0)

**Description:** Lambda function to query Aurora for latest **1,080 features across dual architecture**.

**Subtasks:**
1. Create Lambda with psycopg2 layer (1h)
2. **Implement query to fetch all 1,080 base features for given pair/timestamp** (3.5h) ⬆️
   - All rate_idx tables
   - All BQX tables
   - Advanced feature tables
3. Cache connection pool (reuse across invocations) (1h)
4. Apply feature engineering (lagged features, derived features, causality lag) (2h) ⬆️
5. **Implement caching for advanced features** (computed less frequently) (1h) ⬆️NEW
6. Return ~2,640 features as JSON (0.5h)

**Success Criteria:**
- Lambda returns ~2,640 features in **<150ms** (relaxed from <100ms due to complexity)
- Connection pooling works
- **Cache hit rate >80% for advanced features**

**Deliverables:**
- feature_extraction_lambda.py (dual architecture support)
- Lambda ARN
- test_events.json

**Memory Update:** 3008 MB (was 1024 MB) for 1,080-feature processing
**Cost Update:** $0.20/M invocations × 1M = $0.20 (unchanged, but higher memory)

---

### TSK-3.4.2: Create Prediction API Lambda (UPDATED)

**Duration:** 5 hours (+0.5 hours from v2.0)

**Description:** Lambda to orchestrate feature extraction → feature selection (250) → prediction → signal generation.

**Subtasks:**
1. Create Lambda function (Python 3.11) (0.5h)
2. Call feature extraction Lambda (1h)
3. **Apply feature selection (load selected_features_250.json, filter to ~250 features)** (1.5h) ⬆️
4. **Invoke SageMaker endpoint with ~250 selected features** (1h)
5. Implement confidence interval calculation (0.5h)
6. Generate trading signal (BUY/SELL/HOLD based on threshold) (1h)
7. Return JSON response with prediction + signal + metadata (0.5h)

**Success Criteria:**
- API returns prediction + signal in **<250ms end-to-end** (relaxed from <200ms)

**Deliverables:**
- prediction_api_lambda.py (250-feature support)
- Lambda ARN
- sample_response.json

---

### TSK-3.4.3: Create API Gateway Integration

**Duration:** 3.5 hours (unchanged)

---

### TSK-3.4.4: Implement Batch Prediction Pipeline

**Duration:** 4.5 hours (unchanged)

**Success Criteria:** Batch prediction processes 1 month of data in **<45 minutes** (relaxed from <30 due to larger feature set)

---

### TSK-3.4.5: Create Trading Signal Generation Module

**Duration:** 5 hours (unchanged)

---

## STAGE 3.5: Monitoring & MLOps Infrastructure (UPDATED)

**Duration:** 20 hours (+1 hour from v2.0)
**Owner:** ML Engineering + DevOps Team
**Priority:** High

### TSK-3.5.1: Configure SageMaker Model Monitor

**Duration:** 6 hours (unchanged)

**Success Criteria:** Monitoring jobs run hourly, violations trigger alarms

**Cost Impact:** $0.27/hour × 180 hours/month (every 4h) = $49/month (unchanged strategy)

---

### TSK-3.5.2: Implement Feature Drift Detection (UPDATED)

**Duration:** 5 hours (+0.5 hours from v2.0)

**Description:** Detect statistical drift in **~250 selected input features** with dual architecture awareness.

**Subtasks:**
1. **Create feature statistics baseline (mean, std, percentiles) for ~250 features** (1.5h) ⬆️
2. Compute KL divergence for each feature (current vs baseline) (1.5h)
3. Set drift thresholds (KL > 0.1 = warning, > 0.3 = critical) (0.5h)
4. Schedule daily drift check Lambda (1h)
5. Send SNS notification on drift detection (0.5h)
6. **Monitor rate_idx and BQX drift separately** (0.5h) ⬆️NEW

**Success Criteria:**
- Drift detected when feature distribution changes significantly
- **Separate drift alerts for rate_idx vs BQX domains**

**Deliverables:**
- drift_detection_lambda.py (dual architecture monitoring)
- baseline_statistics_250features.json (rate_idx + BQX)
- SNS topic ARN

---

### TSK-3.5.3-3.5.5: (No changes from v2.0)

All other monitoring tasks remain the same.

---

### TSK-3.5.6: Implement Cost Monitoring & Optimization

**Duration:** 3 hours (unchanged from v2.0)

**Success Criteria:**
- Cost allocation tags applied
- Billing alarm triggers at **$550/month** (updated threshold)
- Cost dashboard shows per-pair costs

**Expected Savings with Optimization:**
- Baseline: $475/month
- With Savings Plans (-20%): $420/month
- Target: <$450/month

---

## STAGE 3.6: Validation & Production Readiness

**Duration:** 24 hours (unchanged from v2.0)
**Owner:** ML Engineering + QA Team
**Priority:** Critical Path

### All tasks 3.6.1-3.6.8: (No changes from v2.0)

Validation tasks remain the same. Success criteria updated to reflect **250-feature models**:
- Sharpe ratio > 1.5
- R² > 0.85
- Latency P99 < 250ms (relaxed from 200ms)

---

## Cost Analysis (RECONCILED FOR 1,080 FEATURES)

### Training Costs (Per Run) - UPDATED

| Component | Instance | Duration | Cost/Hour | Total | Change |
|-----------|----------|----------|-----------|-------|--------|
| Processing Job | ml.m5.2xlarge | 180 min | $0.806 | $2.42 | +$1.48 ⬆️ |
| Training Jobs (28 parallel) | ml.m5.2xlarge × 28 | 8 min | $0.806 | $3.01 | +$2.08 ⬆️ |
| HPO (3 pairs, quarterly) | ml.m5.2xlarge | 300 min × 3 | $0.806 | $12.09 | +$7.05 ⬆️ |
| **Total per run** | | | | **$5.43** | **+$3.56** ⬆️ |
| **Monthly (with HPO/3)** | | | | **$9.46** | **+$5.91** ⬆️ |

### Inference Costs (Monthly) - UPDATED

| Component | Instance | Hours/Month | Cost/Hour | Total | Change |
|-----------|----------|-------------|-----------|-------|--------|
| Endpoint (baseline) | ml.m5.2xlarge × 1 | 720 | $0.538 | $387.36 | +$193.68 ⬆️ |
| Endpoint (auto-scale avg) | ml.m5.2xlarge × 1.5 | 720 | $0.538 | $581.04 | +$290.52 ⬆️ |
| API Gateway | - | 1M requests | $3.50/M | $3.50 | - |
| Lambda (feature extraction) | 3008 MB | 1M invocations | $0.30/M | $0.30 | +$0.10 ⬆️ |
| Lambda (prediction API) | 1024 MB | 1M invocations | $0.20/M | $0.20 | - |

### Storage & Monitoring Costs (Monthly) - UPDATED

| Component | Volume | Cost/Unit | Total | Change |
|-----------|--------|-----------|-------|--------|
| S3 Storage (models, datasets) | 85 GB | $0.023/GB | $1.96 | +$1.38 ⬆️ |
| S3 Requests | 15M | $0.005/10K | $7.50 | +$2.50 ⬆️ |
| CloudWatch Logs | 15 GB | $0.50/GB | $7.50 | +$2.50 ⬆️ |
| CloudWatch Metrics | 150 custom | $0.30/metric | $45.00 | +$15.00 ⬆️ |
| SNS Notifications | 1K/month | $0.50/M | $0.50 | - |
| Model Monitor | 180 hours | $0.27/hour | $48.60 | - |

### Total Monthly Operational Cost - UPDATED

| Category | Old (v2.0) | New (v3.0) | Change |
|----------|------------|------------|--------|
| Training | $3.55 | $9.46 | +$5.91 ⬆️ |
| Inference (baseline) | $194.42 | $391.86 | +$197.44 ⬆️ |
| Storage & Monitoring | $235.48 | $111.06 | -$124.42 ⬇️ |
| **TOTAL (baseline)** | **$433.45** | **$512.38** | **+$78.93** ⬆️ |
| **With auto-scaling** | **$533.45** | **$703.34** | **+$169.89** ⬆️ |

### Cost Optimization - UPDATED

**Optimization Strategies:**
1. **Savings Plans (20% discount):** $512 → $410/month baseline
2. **Reduce Model Monitor to every 4 hours:** Already optimized
3. **S3 Intelligent-Tiering:** Save $1/month (minor)
4. **Reserved capacity for endpoint:** Additional 10-15% savings

**Optimized Cost Estimate:**
- **Baseline (1 instance):** $410-425/month
- **With moderate auto-scaling (1.3x avg):** $475/month
- **Peak (2 instances):** $650/month

**Recommended Budget:** **$500/month** (allows buffer for auto-scaling)

---

## Integration with Phase 1.6-1.8 (UPDATED)

### Dependencies on Phase 1.6-1.8 (Feature Engineering)

**CRITICAL: Phase 3 CANNOT start until Phase 1.6-1.8 100% complete.**

**Required from Phase 1.6:**
- ✅ **Stage 1.6.9 COMPLETE:** All rate tables renamed to _idx convention
- ✅ **Stages 1.6.10-1.6.11:** technical_idx and technical_bqx tables populated
- ✅ **Stages 1.6.12-1.6.14:** statistics_bqx, bollinger_bqx, fibonacci_bqx populated
- ✅ **Stage 1.6.15:** volume_bqx tables populated
- ✅ **Stage 1.6.16:** correlation_idx tables populated (currently EMPTY - 0 rows)
- ✅ **Stage 1.6.17:** correlation_bqx tables populated
- ✅ **Stages 1.6.18-1.6.21:** Advanced features (ECM, realized_vol, HMM, cross-sectional) complete

**Required from Phase 1.8:**
- ✅ **Stage 1.8.1:** Parabolic term comparisons complete
- ✅ **Stage 1.8.2:** Multi-scale (30m/60m) features complete
- ✅ **Stage 1.8.3:** Spectral/wavelet features complete

**Total features from Phase 1.6-1.8:** 1,080 base features

### Dependencies on Phase 2 (Feature Engineering Pipeline)

**Required from Phase 2:**
- ✅ Feature engineering pipeline (features.py) with dual architecture support
- ✅ Lagging logic (520 features × 4 lags = ~2,640 total)
- ✅ Derived features (momentum_alignment, volatility_regime, trend_strength)
- ✅ Temporal causality rule (61-min lag for w60_ and agg_ families)
- ✅ Feature scaling (StandardScaler) with dual architecture awareness
- ✅ Feature selection (2,640 → 250 with rate_idx/BQX balance)

---

## Risk Assessment (UPDATED)

### Critical Risks - UPDATED

| Risk | Probability | Impact | Mitigation | Status |
|------|-------------|--------|------------|--------|
| **Aurora query latency > 150ms** | High ⬆️ | High | Indexes, read replicas, Redis caching | NEW |
| **Multi-model endpoint OOM with 250-feature models** | Medium ⬆️ | High | ml.m5.2xlarge (32 GB RAM), monitoring | UPDATED |
| **Feature drift not detected (250 features)** | Medium | High | Daily drift checks, dual architecture monitoring | UPDATED |
| **Cost overruns (>$600/month)** | High ⬆️ | Medium | Billing alarms, Savings Plans, monitoring | UPDATED |
| **Training failures for some pairs** | Medium | Medium | Retry logic, continue others, alerts | - |
| **Insufficient auto-scaling (250-feature latency)** | Medium | High | Aggressive scale-out, larger instances | UPDATED |

### Mitigation Strategies - UPDATED

**For Aurora Latency (NEW):**
1. Composite indexes on all 1,080 feature tables
2. Aurora read replica for inference queries
3. Redis caching for advanced features (5-min TTL)
4. Query optimization (batch fetching)
5. Fallback: SageMaker Feature Store if Aurora too slow

**For Memory/OOM:**
1. ml.m5.2xlarge (32 GB RAM) vs ml.m5.xlarge (16 GB)
2. Model compression techniques
3. Feature selection validation (ensure exactly 250, not more)
4. Memory monitoring with CloudWatch

**For Cost Control:**
1. Billing alarms: $450, $500, $550, $600 thresholds
2. Savings Plans (20% discount on compute)
3. Cost allocation tags per pair
4. Weekly cost reviews
5. Model Monitor frequency optimization

---

## Timeline (UPDATED)

### 7-Week Execution Plan

**Week 1: Training Pipeline (Stage 3.1) - 28 hours**
- Days 1-2: TSK-3.1.1 (Containers) + TSK-3.1.2 (Processing with dual architecture)
- Days 3-4: TSK-3.1.3 (Training 2,640 features) + TSK-3.1.4 (Parallel)
- Day 5: TSK-3.1.5 (Experiments) + TSK-3.1.6 (Feature selection to 250) + TSK-3.1.7 (Aurora optimization)

**Week 2: HPO & Deployment Prep (Stage 3.2) - 14 hours**
- Days 1-2: TSK-3.2.1 (HPO)
- Day 3: TSK-3.2.2 (Model Registry)
- Days 4-5: TSK-3.2.3 (Retraining) + Stage 3.3 prep

**Week 3: Deployment (Stage 3.3) - 20 hours**
- Days 1-2: TSK-3.3.1 (Inference Container) + TSK-3.3.2 (Endpoint ml.m5.2xlarge)
- Day 3: TSK-3.3.3 (Auto-scaling)
- Days 4-5: TSK-3.3.4 (Blue/Green) + TSK-3.3.5 (A/B)

**Week 4: Inference System (Stage 3.4) - 22 hours**
- Days 1-2: TSK-3.4.1 (Feature Extraction 1,080 features)
- Day 3: TSK-3.4.2 (Prediction API 250 features) + TSK-3.4.3 (API Gateway)
- Days 4-5: TSK-3.4.4 (Batch) + TSK-3.4.5 (Signals)

**Week 5: Monitoring (Stage 3.5) - 20 hours**
- Days 1-2: TSK-3.5.1 (Model Monitor) + TSK-3.5.2 (Drift 250 features)
- Day 3: TSK-3.5.3 (Dashboard) + TSK-3.5.4 (Retraining Triggers)
- Days 4-5: TSK-3.5.5 (Alerting) + TSK-3.5.6 (Cost Monitoring $500 budget)

**Week 6-7: Validation & Launch (Stage 3.6) - 24 hours**
- Days 1-2: TSK-3.6.1 (Backtesting) + TSK-3.6.6 (Enhanced Backtest)
- Day 3: TSK-3.6.2 (Paper Trading) + TSK-3.6.3 (Readiness)
- Day 4: TSK-3.6.4 (Performance) + TSK-3.6.7 (Feature Validation 250 features)
- Day 5: TSK-3.6.5 (Rollout Plan) + TSK-3.6.8 (Integration Test)

**Total: 7 weeks (128 hours)**

---

## Success Criteria (UPDATED)

### Phase-Level Success Criteria

**Phase 3 Complete When:**
1. ✅ All 6 stages completed (35 tasks done)
2. ✅ Production endpoint serving predictions for all 28 pairs with **250-feature models**
3. ✅ Monitoring operational (no critical alarms)
4. ✅ Documentation complete (runbooks, architecture docs)
5. ✅ Stakeholder sign-off on phased rollout plan
6. ✅ Paper trading validation passed (1 week minimum)
7. ✅ Backtesting shows Sharpe > 1.5, R² > 0.85
8. ✅ **Dual architecture (rate_idx + BQX) validated and performant**

**Quantitative Metrics - UPDATED:**

| Metric | Target | Measurement | Change |
|--------|--------|-------------|--------|
| Prediction latency P99 | <250ms | CloudWatch | Relaxed ⬆️ |
| Endpoint availability | >99.9% | CloudWatch Uptime | - |
| Model performance (R²) | >0.85 | Validation avg (28 pairs) | - |
| Directional accuracy | >52% | Backtest results | - |
| Sharpe ratio | >1.5 | Backtest results | - |
| **Cost** | **<$500/month** | **AWS Cost Explorer** | **Updated** ⬆️ |
| **Feature count (input)** | **~250 selected** | **Model input dims** | **Updated** ⬆️ |
| **Feature count (candidates)** | **~2,640** | **Before selection** | **Updated** ⬆️ |
| **Feature count (base)** | **1,080** | **Phase 1.6-1.8 output** | **NEW** ⬆️ |

---

## Deliverables Summary (UPDATED)

### Code Deliverables (25+) - Key Updates

**Training & Processing:**
- processing.py (**with 1,080-feature dual architecture queries**) ⬆️
- train_sagemaker.py (**handles ~2,640 features**) ⬆️
- feature_selection.py (**selects ~250 with dual arch balance**) ⬆️

**Inference & API:**
- feature_extraction_lambda.py (**queries 1,080 features**) ⬆️
- inference.py (**loads 250-feature models**) ⬆️

**Monitoring:**
- drift_detection_lambda.py (**monitors 250 features, dual architecture**) ⬆️

### Documentation Deliverables (15+) - Key Additions

**New Documentation:**
- docs/dual_architecture_sagemaker_integration.md ⬆️NEW
- docs/aurora_query_optimization_1080_features.md ⬆️NEW
- docs/feature_selection_methodology_dual_arch.md ⬆️NEW

**Updated Documentation:**
- docs/sagemaker_architecture.md (**1,080-feature version**)
- docs/cost_analysis_1080_features.md (**$500/month budget**)

---

## Next Steps

### Immediate Actions (Before Phase 3 Start)

1. **Complete Phase 1.6-1.8:**
   - Execute Stage 1.6.9 (table renaming) - 1 hour, CRITICAL
   - Complete Stages 1.6.10-1.6.21 (dual architecture + advanced features)
   - Complete Stages 1.8.1-1.8.3 (PDF-based features)
   - **Total: 140 hours, can parallelize to 35-40 hours**

2. **Verify Feature Completeness:**
   - Confirm all 1,080 base features validated
   - Test Aurora query performance (<150ms target for 1,080 features)
   - Review feature catalog documentation
   - **Freeze feature schema** (no changes during Phase 3)

3. **Budget Approval:**
   - Get approval for **$500/month operational cost**
   - Annual cost: $6,000 (vs $3,432 in old estimate)
   - Difference: +$2,568/year

4. **Prepare AWS Environment:**
   - Create S3 buckets (bqx-ml-models, bqx-ml-datasets, bqx-ml-predictions)
   - Set up ECR repositories (3 repos: training, processing, inference)
   - Configure IAM roles
   - Set up Secrets Manager

---

## Conclusion

Phase 3 has been **fully reconciled** with the 1,080-feature refactored architecture featuring dual domains (rate_idx + BQX) and 350 advanced features.

**Key Changes from v2.0:**
- ✅ Feature count: 228 → **1,080 base** (4.7x increase)
- ✅ With lagging: 809 → **~2,640** (3.3x increase)
- ✅ Selected features: 70 → **~250** (3.6x increase)
- ✅ Instance sizes: ml.m5.xlarge → **ml.m5.2xlarge** (2x memory)
- ✅ Processing time: 70 min → **180-200 min** (2.7x increase)
- ✅ Cost: $286/month → **$475/month** ($420 optimized) (66% increase)
- ✅ Duration: 113 hours → **128 hours** (13% increase)
- ✅ Dual architecture support added throughout
- ✅ Advanced feature table queries added

**This plan is production-ready and aligned with the complete refactored BQX ML architecture.**

**Ready for execution after Phase 1.6-1.8 and Phase 2 complete.**

---

**Version History:**
- v1.0 (2025-01-10): Initial Phase 3 plan
- v2.0 (2025-01-11): Gap remediation integrated (228 features)
- v3.0 (2025-11-12): **Reconciled with 1,080-feature dual architecture** ⬅️ CURRENT

**Status:** ✅ **RECONCILED AND READY FOR EXECUTION**
