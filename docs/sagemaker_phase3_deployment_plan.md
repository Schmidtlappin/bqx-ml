# Phase 3: SageMaker ML System - Complete Deployment Plan

**Version:** 2.0 (Gap Remediation Integrated)
**Status:** Ready for Execution
**Duration:** 113 hours (6 weeks)
**Dependencies:** Phase 1.6 Complete, Phase 2 Complete
**Cost:** ~$350/month operational

---

## Executive Summary

Phase 3 delivers a production-grade SageMaker ML system that transforms the 228 engineered features (809 with lagging, 70 selected) into real-time forex predictions for all 28 currency pairs.

**What Phase 3 Delivers:**
- ✅ Automated training pipeline (28 models in parallel, <15 minutes)
- ✅ Multi-model inference endpoint (ml.m5.xlarge, auto-scaling 1-4 instances)
- ✅ Real-time prediction API (<200ms P99 latency)
- ✅ Batch prediction system (1 month of data in <30 minutes)
- ✅ Comprehensive monitoring (drift detection, performance tracking, automated retraining)
- ✅ Production validation (backtesting, paper trading, load testing)

**Architecture Highlights:**
- **Training:** SageMaker Processing Jobs + Training Jobs on ml.m5.xlarge
- **Inference:** Multi-model endpoint serving 28 pairs from single instance
- **Features:** Direct Aurora integration (111 base + 117 derived = 228 features)
- **Monitoring:** SageMaker Model Monitor + CloudWatch + SNS alerts
- **Cost:** $1.89 per training run, $280/month inference baseline

---

## Feature Count Summary (Corrected)

### Base Features: 228 Features

| Category | Count | Status | Source |
|----------|-------|--------|--------|
| BQX Features | 40 | ✅ IMPLEMENTED | stage_1_5_4 schema |
| REG Features | 57 | ✅ IMPLEMENTED | stage_1_5_5 schema |
| Volume Features | 10 | ✅ COMPLETE | volume_features_worker.py |
| Currency Indices | 8 | ✅ COMPLETE | currency_indices_worker.py |
| Statistics | 5 | 🔄 IN PROGRESS | statistics_bollinger_worker.py |
| Bollinger | 5 | 🔄 IN PROGRESS | statistics_bollinger_worker.py |
| Time Features | 8 | 🔄 IN PROGRESS | time_spread_features_worker.py |
| Spread Features | 20 | 🔄 IN PROGRESS | time_spread_features_worker.py |
| Correlation | 15 | ⏳ PLANNED | Gap plan Stage 1.6.6 |
| Technical Indicators | 45 | ⏳ PLANNED | Gap plan Stage 1.6.7 |
| Fibonacci | 12 | ⏳ PLANNED | Gap plan Stage 1.6.8 |
| Derived (features.py) | 3 | ✅ IMPLEMENTED | momentum_alignment, volatility_regime, trend_strength |
| **TOTAL BASE** | **228** | **56 done, 38 in progress, 134 planned** | |

### With Lagging: 809 Features

**Lagging Strategy (See feature_lagging_strategy.md):**
- Lagged features: 142 features × 4 lags (60, 120, 180, 240 min) = 568 + 142 base = 710
- Non-lagged features: 86 features (time, currency indices, etc.)
- Temporal causality features: 13 additional (61-min lag for w60_ and agg_)
- **Total: 710 + 86 + 13 = 809 features**

### After Feature Selection: 70 Features

**Selection Strategy (Task 3.1.6):**
- Train Random Forest on all 809 features
- Compute feature importance scores
- Select top 70 features by cumulative importance (>95% threshold)
- **Model input: 70 selected features per pair**

---

## Phase 3 Structure

**6 Stages, 33 Tasks, 113 Hours**

| Stage | Duration | Tasks | Priority |
|-------|----------|-------|----------|
| **3.1: Training Pipeline Development** | 22 hours | 6 tasks | Critical Path |
| **3.2: Hyperparameter Optimization & Model Registry** | 14 hours | 3 tasks | High |
| **3.3: Model Deployment Infrastructure** | 16 hours | 5 tasks | Critical Path |
| **3.4: Real-Time Inference System** | 18 hours | 5 tasks | Critical Path |
| **3.5: Monitoring & MLOps Infrastructure** | 19 hours | 6 tasks | High |
| **3.6: Validation & Production Readiness** | 24 hours | 8 tasks | Critical Path |

---

## Stage 3.1: Training Pipeline Development

**Duration:** 22 hours
**Owner:** ML Engineering Team
**Priority:** Critical Path

### Stage 3.1 Overview

Convert existing local training code to SageMaker-compatible format with distributed training for all 28 pairs and feature selection pipeline.

### Tasks

#### TSK-3.1.1: Create SageMaker Training Container

**Duration:** 3.5 hours

**Description:**
Dockerize training code with all dependencies (sklearn, psycopg2, joblib, pandas, numpy).

**Subtasks:**
1. Create Dockerfile based on SageMaker sklearn container (1h)
2. Install additional dependencies (psycopg2, pyyaml) (0.5h)
3. Copy training code into container (/opt/ml/code/) (0.5h)
4. Test container locally with docker run (1h)
5. Push to ECR (bqx-ml-training:latest) (0.5h)

**Success Criteria:**
Container runs train.py successfully with sample data

**Deliverables:**
- ECR image URI: {account}.dkr.ecr.us-east-1.amazonaws.com/bqx-ml-training:latest
- Dockerfile
- build_training_container.sh

---

#### TSK-3.1.2: Create SageMaker Processing Job for Feature Engineering

**Duration:** 6.5 hours

**Description:**
Convert data extraction + feature engineering to SageMaker Processing job. Includes application of temporal causality rule (61-minute lag).

**Subtasks:**
1. Create processing script (processing.py) that queries Aurora (2h)
2. Handle Aurora credentials via AWS Secrets Manager (1h)
3. Apply temporal causality rule to w60_ and agg_ features (1h)
4. Output features to S3 as Parquet (train/val/test splits) (1h)
5. Create processing job Python script (submit_processing.py) (1h)
6. Test end-to-end: Aurora → Processing Job → S3 (1.5h)

**Success Criteria:**
- Processing job completes for 1 pair
- Outputs valid Parquet files with 809 features
- Temporal causality rule correctly applied (13 causality-lagged features)

**Deliverables:**
- processing.py
- submit_processing.py
- S3 dataset: s3://bqx-ml-datasets/{pair}/train.parquet

---

#### TSK-3.1.3: Adapt Training Script for SageMaker

**Duration:** 5 hours

**Description:**
Modify train.py to read from S3 and write to /opt/ml/model/ with feature lagging strategy implemented.

**Subtasks:**
1. Replace Aurora extraction with S3 Parquet reading (1h)
2. Implement feature lagging strategy (142 features × 4 lags) (1.5h)
3. Modify save path to /opt/ml/model/ (SageMaker convention) (0.5h)
4. Add hyperparameters from environment variables (1h)
5. Add metrics logging to CloudWatch (0.5h)
6. Test with sagemaker.sklearn.SKLearn() estimator (2h)

**Success Criteria:**
- Training job completes
- Model saved to S3 with 809 feature inputs
- Metrics visible in CloudWatch (R², MAE, directional_accuracy)

**Deliverables:**
- train_sagemaker.py
- test_training_job.py

---

#### TSK-3.1.4: Implement Parallel Training for 28 Pairs

**Duration:** 5 hours

**Description:**
Launch 28 training jobs in parallel, one per pair.

**Subtasks:**
1. Create training orchestrator script (train_all_pairs.py) (1.5h)
2. Use ThreadPoolExecutor to launch jobs in parallel (1h)
3. Pass pair name as hyperparameter (0.5h)
4. Collect all model artifacts to S3 (0.5h)
5. Test with 3 pairs, then full 28 pairs (1.5h)

**Success Criteria:**
28 training jobs complete in <10 minutes (parallel), all models in S3

**Deliverables:**
- train_all_pairs.py
- Execution logs
- 28 model artifacts: s3://bqx-ml-models/{pair}/model.tar.gz

---

#### TSK-3.1.5: Set Up Experiment Tracking

**Duration:** 3.5 hours

**Description:**
Use SageMaker Experiments to track training runs.

**Subtasks:**
1. Create experiment (bqx-ml-training) and trial groups (1h)
2. Log hyperparameters, metrics, and model locations (1h)
3. Create dashboard notebook to compare trials (1h)
4. Document experiment tracking usage (0.5h)

**Success Criteria:**
Training runs appear in SageMaker Studio, metrics queryable

**Deliverables:**
- experiments_setup.py
- dashboard.ipynb
- docs/experiment_tracking.md

---

#### TSK-3.1.6: Implement Feature Selection Pipeline (NEW)

**Duration:** 4 hours

**Description:**
Implement feature selection to reduce 809 features to top 70 by Random Forest importance.

**Subtasks:**
1. Train initial Random Forest on all 809 features (1h)
2. Compute feature importance scores (0.5h)
3. Select top 70 features by cumulative importance (>95% threshold) (1h)
4. Save feature selection mask to S3 (0.5h)
5. Apply mask in training and inference pipelines (1h)

**Success Criteria:**
- Feature selection identifies top 70 features
- Selected features saved: s3://bqx-ml-models/{pair}/selected_features.json
- Training uses only 70 features (verify input dimensions)

**Deliverables:**
- feature_selection.py
- selected_features.json (per pair)
- docs/feature_selection_methodology.md

---

## Stage 3.2: Hyperparameter Optimization & Model Registry

**Duration:** 14 hours
**Owner:** ML Engineering Team
**Priority:** High

### Stage 3.2 Overview

Implement automated hyperparameter tuning and model versioning with approval workflow.

### Tasks

#### TSK-3.2.1: Configure SageMaker Hyperparameter Tuning

**Duration:** 5 hours

**Description:**
Set up HPO for Random Forest hyperparameters.

**Subtasks:**
1. Define hyperparameter search space (n_estimators, max_depth, min_samples_split) (1h)
2. Configure tuning job with 50 trials, Bayesian optimization (1h)
3. Set objective metric: maximize R² on validation set (0.5h)
4. Test HPO on 1 pair (EURUSD) (2h)
5. Document best hyperparameters found (0.5h)

**Success Criteria:**
HPO completes, best model has R² > baseline, parameters logged

**Deliverables:**
- hpo_config.py
- best_hyperparameters.json
- docs/hpo_results.md

---

#### TSK-3.2.2: Implement Model Registry Integration

**Duration:** 5 hours

**Description:**
Register trained models with metadata and versioning.

**Subtasks:**
1. Create model package group (bqx-ml-models) (0.5h)
2. Register models with metadata (pair, R², MAE, training_date, feature_count=70) (1.5h)
3. Add approval workflow (PendingManualApproval → Approved) (1h)
4. Create script to bulk-register 28 pair models (1h)
5. Test retrieval of latest approved model per pair (1h)

**Success Criteria:**
All 28 models registered, approval workflow functional

**Deliverables:**
- register_models.py
- get_latest_model.py
- docs/model_registry.md

---

#### TSK-3.2.3: Create Automated Retraining Pipeline

**Duration:** 6 hours

**Description:**
Schedule monthly retraining with latest data.

**Subtasks:**
1. Create Lambda function to trigger training pipeline (2h)
2. Set up EventBridge rule (monthly schedule) (0.5h)
3. Implement data drift check before retraining (1.5h)
4. Add notification (SNS) on training completion (0.5h)
5. Test end-to-end retraining flow (1.5h)

**Success Criteria:**
Monthly retraining triggers automatically, new models registered

**Deliverables:**
- retrain_lambda.py
- eventbridge_rule.json
- docs/retraining_cadence.md

---

## Stage 3.3: Model Deployment Infrastructure

**Duration:** 16 hours
**Owner:** ML Engineering + DevOps Team
**Priority:** Critical Path

### Stage 3.3 Overview

Deploy multi-model endpoint with auto-scaling and blue/green deployment capability.

### Tasks

#### TSK-3.3.1: Create SageMaker Inference Container

**Duration:** 5.5 hours

**Description:**
Custom container for model serving with preprocessing (feature selection applied).

**Subtasks:**
1. Create Dockerfile based on SageMaker sklearn-inference (1h)
2. Add inference script (inference.py) with preprocess/predict/postprocess (2h)
3. Load model + scaler + selected_features.json from /opt/ml/model/ (1h)
4. Test container locally with Flask (1h)
5. Push to ECR (bqx-ml-inference:latest) (0.5h)

**Success Criteria:**
Container responds to /ping and /invocations, predictions valid

**Deliverables:**
- Dockerfile
- inference.py
- ECR image URI

---

#### TSK-3.3.2: Deploy Multi-Model Endpoint

**Duration:** 4.5 hours

**Description:**
Create SageMaker multi-model endpoint for all 28 pairs.

**Subtasks:**
1. Package all 28 models as model.tar.gz with inference code + selected_features.json (1h)
2. Upload to S3 multi-model structure (s3://bqx-ml-models/{pair}/) (0.5h)
3. Create SageMaker model with MultiModel=True (0.5h)
4. Create endpoint configuration (ml.m5.xlarge, 1 instance) (0.5h)
5. Deploy endpoint and test invocations for 3 pairs (2h)

**Success Criteria:**
Endpoint deployed, responds to requests for all 28 pairs, latency <200ms

**Deliverables:**
- deploy_endpoint.py
- Endpoint name: bqx-ml-multi-model-production
- testing_notebook.ipynb

---

#### TSK-3.3.3: Configure Auto-Scaling Policies

**Duration:** 3.75 hours

**Description:**
Set up auto-scaling based on invocations per instance.

**Subtasks:**
1. Register endpoint as scalable target (0.5h)
2. Create scaling policy (target=400 invocations/minute) (0.5h)
3. Set min=1, max=4 instances (0.25h)
4. Test scale-out with load generation (1.5h)
5. Verify scale-in after load decreases (1h)

**Success Criteria:**
Endpoint scales from 1→2 instances under load, scales back to 1

**Deliverables:**
- autoscaling_config.py
- load_test_results.md

---

#### TSK-3.3.4: Implement Blue/Green Deployment

**Duration:** 5 hours

**Description:**
Zero-downtime deployment with traffic shifting.

**Subtasks:**
1. Create new endpoint configuration (green) with updated models (0.5h)
2. Implement traffic shifting script (blue 100% → green 10% → 50% → 100%) (1.5h)
3. Add rollback capability (shift back to blue if errors) (1h)
4. Test deployment with canary metrics (error rate, latency) (1.5h)
5. Document deployment runbook (0.5h)

**Success Criteria:**
New model deployed with gradual traffic shift, rollback functional

**Deliverables:**
- blue_green_deploy.py
- rollback.py
- docs/deployment_runbook.md

---

#### TSK-3.3.5: Create A/B Testing Framework

**Duration:** 4.5 hours

**Description:**
Support A/B testing of model variants.

**Subtasks:**
1. Modify inference.py to log model variant (A/B) to CloudWatch (1h)
2. Deploy 2 endpoint configurations (control, treatment) (0.5h)
3. Create traffic splitting Lambda (50/50 split based on request hash) (1.5h)
4. Create analysis notebook for A/B results (1h)
5. Document A/B testing process (0.5h)

**Success Criteria:**
Traffic split between variants, metrics logged per variant

**Deliverables:**
- ab_test_lambda.py
- ab_analysis.ipynb
- docs/ab_testing.md

---

## Stage 3.4: Real-Time Inference System

**Duration:** 18 hours
**Owner:** Backend Engineering Team
**Priority:** Critical Path

### Stage 3.4 Overview

Build end-to-end prediction API with feature extraction from Aurora and trading signal generation.

### Tasks

#### TSK-3.4.1: Create Feature Extraction Lambda

**Duration:** 6 hours

**Description:**
Lambda function to query Aurora for latest 809 features.

**Subtasks:**
1. Create Lambda with psycopg2 layer (1h)
2. Implement query to fetch BQX + REG + all Track 1/2 features for given pair/timestamp (2h)
3. Cache connection pool (reuse across invocations) (1h)
4. Apply feature engineering (lagged features, derived features, causality lag) (1.5h)
5. Return 809 features as JSON (0.5h)

**Success Criteria:**
Lambda returns 809 features in <100ms, connection pooling works

**Deliverables:**
- feature_extraction_lambda.py
- Lambda ARN
- test_events.json

---

#### TSK-3.4.2: Create Prediction API Lambda

**Duration:** 4.5 hours

**Description:**
Lambda to orchestrate feature extraction → feature selection → prediction → signal generation.

**Subtasks:**
1. Create Lambda function (Python 3.11) (0.5h)
2. Call feature extraction Lambda (1h)
3. Apply feature selection (load selected_features.json, filter to 70 features) (1h)
4. Invoke SageMaker endpoint with 70 selected features (1h)
5. Implement confidence interval calculation (0.5h)
6. Generate trading signal (BUY/SELL/HOLD based on threshold) (1h)
7. Return JSON response with prediction + signal + metadata (0.5h)

**Success Criteria:**
API returns prediction + signal in <200ms end-to-end

**Deliverables:**
- prediction_api_lambda.py
- Lambda ARN
- sample_response.json

---

#### TSK-3.4.3: Create API Gateway Integration

**Duration:** 3.5 hours

**Description:**
REST API for prediction service.

**Subtasks:**
1. Create API Gateway REST API (0.5h)
2. Add /predict endpoint (POST) with request validation (1h)
3. Integrate with prediction Lambda (0.5h)
4. Add API key authentication (0.5h)
5. Configure throttling (100 req/sec) and CORS (0.5h)
6. Deploy to production stage (0.5h)

**Success Criteria:**
API accessible via HTTPS, authentication works, throttling enforced

**Deliverables:**
- API Gateway URL: https://{id}.execute-api.us-east-1.amazonaws.com/prod/predict
- API key
- postman_collection.json

---

#### TSK-3.4.4: Implement Batch Prediction Pipeline

**Duration:** 4.5 hours

**Description:**
Batch prediction for backtesting and historical analysis.

**Subtasks:**
1. Create SageMaker Batch Transform job script (1.5h)
2. Prepare batch input: query Aurora for date range, save to S3 (1h)
3. Run batch transform with all 28 models (0.5h)
4. Output predictions to S3 as CSV (0.5h)
5. Create analysis notebook for batch results (1h)

**Success Criteria:**
Batch prediction processes 1 month of data in <30 minutes

**Deliverables:**
- batch_predict.py
- batch_analysis.ipynb
- S3 output path: s3://bqx-ml-predictions/batch/

---

#### TSK-3.4.5: Create Trading Signal Generation Module

**Duration:** 5 hours

**Description:**
Convert predictions to actionable trading signals.

**Subtasks:**
1. Define signal thresholds (e.g., BUY if prediction > +0.0005, SELL if < -0.0005) (1h)
2. Implement confidence-weighted signals (stronger signal if CI narrow) (1.5h)
3. Add regime-based signal adjustment (high volatility → reduce signal strength) (1h)
4. Create signal validation logic (no-trade zones, market hours) (1h)
5. Document signal generation rules (0.5h)

**Success Criteria:**
Signals generated correctly, validated against backtest

**Deliverables:**
- signal_generator.py
- docs/signal_generation_rules.md

---

## Stage 3.5: Monitoring & MLOps Infrastructure

**Duration:** 19 hours
**Owner:** ML Engineering + DevOps Team
**Priority:** High

### Stage 3.5 Overview

Comprehensive monitoring with drift detection, performance tracking, automated alerting, and cost monitoring.

### Tasks

#### TSK-3.5.1: Configure SageMaker Model Monitor

**Duration:** 6 hours

**Description:**
Set up data quality and model quality monitoring.

**Subtasks:**
1. Create baseline dataset (statistics, constraints) for 70 features (1.5h)
2. Schedule data quality monitoring job (hourly) (1h)
3. Configure model quality monitoring (compare predictions vs actuals) (1.5h)
4. Set up CloudWatch alarms for violations (1h)
5. Test monitoring with injected drift (1h)

**Success Criteria:**
Monitoring jobs run hourly, violations trigger alarms

**Deliverables:**
- monitoring_config.py
- baseline_statistics.json (70 features)
- alarm_definitions.json

---

#### TSK-3.5.2: Implement Feature Drift Detection

**Duration:** 4.5 hours

**Description:**
Detect statistical drift in 70 selected input features.

**Subtasks:**
1. Create feature statistics baseline (mean, std, percentiles) for 70 features (1h)
2. Compute KL divergence for each feature (current vs baseline) (1.5h)
3. Set drift thresholds (KL > 0.1 = warning, > 0.3 = critical) (0.5h)
4. Schedule daily drift check Lambda (1h)
5. Send SNS notification on drift detection (0.5h)

**Success Criteria:**
Drift detected when feature distribution changes significantly

**Deliverables:**
- drift_detection_lambda.py
- baseline_statistics_70features.json
- SNS topic ARN

---

#### TSK-3.5.3: Create Performance Dashboard

**Duration:** 4 hours

**Description:**
Real-time dashboard for prediction performance.

**Subtasks:**
1. Set up CloudWatch custom metrics (R², MAE, latency) (1h)
2. Create CloudWatch dashboard with 6 panels (1.5h)
   - Invocations per minute
   - Prediction latency (P50, P95, P99)
   - Error rate
   - Model performance (rolling R²)
   - Feature drift status (70 features)
   - Auto-scaling activity
3. Add dashboard sharing via URL (0.5h)
4. Test dashboard with live traffic (1h)

**Success Criteria:**
Dashboard shows real-time metrics, updates every minute

**Deliverables:**
- CloudWatch dashboard URL
- dashboard_config.json

---

#### TSK-3.5.4: Set Up Automated Retraining Triggers

**Duration:** 4 hours

**Description:**
Trigger retraining when performance degrades.

**Subtasks:**
1. Create Lambda to check model performance weekly (1.5h)
2. Compare current R² vs baseline (if drop > 0.05, trigger retrain) (1h)
3. Trigger Step Functions workflow for retraining (1h)
4. Send notification on retraining initiation (0.5h)

**Success Criteria:**
Retraining automatically triggered when R² drops below threshold

**Deliverables:**
- performance_check_lambda.py
- retrain_trigger.py
- Step Functions ARN

---

#### TSK-3.5.5: Implement Alerting System

**Duration:** 3.5 hours

**Description:**
Comprehensive alerting for failures and degradation.

**Subtasks:**
1. Create SNS topics (critical, warning, info) (0.5h)
2. Configure alarms (1.5h):
   - Endpoint error rate > 5% (critical)
   - Latency P99 > 500ms (warning)
   - Model drift detected (warning)
   - Training job failure (critical)
3. Add email + Slack integration (1h)
4. Test alarms with synthetic failures (1h)

**Success Criteria:**
Alarms trigger correctly, notifications delivered to Slack

**Deliverables:**
- alarm_config.py
- SNS topic ARNs
- Slack webhook integration

---

#### TSK-3.5.6: Implement Cost Monitoring & Optimization (NEW)

**Duration:** 3 hours

**Description:**
Monitor and optimize AWS costs for SageMaker ML system.

**Subtasks:**
1. Enable cost allocation tags (pair, model_version, environment) (0.5h)
2. Create Cost Explorer dashboard filtering by BQX ML resources (1h)
3. Set up billing alarms ($400/month threshold) (0.5h)
4. Implement Savings Plans for baseline compute (research 20% discount) (0.5h)
5. Document cost optimization playbook (0.5h)

**Success Criteria:**
- Cost allocation tags applied to all resources
- Billing alarm triggers at $400/month
- Cost dashboard shows per-pair costs

**Deliverables:**
- cost_monitoring_config.py
- Cost Explorer dashboard URL
- docs/cost_optimization_playbook.md

---

## Stage 3.6: Validation & Production Readiness

**Duration:** 24 hours
**Owner:** ML Engineering + QA Team
**Priority:** Critical Path

### Stage 3.6 Overview

Comprehensive testing, backtesting validation, paper trading, and production readiness certification.

### Tasks

#### TSK-3.6.1: Implement Walk-Forward Backtesting Framework

**Duration:** 6 hours

**Description:**
Walk-forward backtesting on historical data.

**Subtasks:**
1. Create backtesting script (walk_forward_backtest.py) (2h)
2. Split data into 12 monthly windows (train on 6 months, test on 1 month) (1h)
3. Compute metrics per window (R², Sharpe, max drawdown) (1.5h)
4. Aggregate results across all windows (0.5h)
5. Create visualization of backtest results (1h)

**Success Criteria:**
Backtest shows consistent R² > 0.85 across all windows

**Deliverables:**
- walk_forward_backtest.py
- backtest_results.ipynb
- backtest_report.md

---

#### TSK-3.6.2: Conduct Paper Trading Validation

**Duration:** 4 hours

**Description:**
Live testing without real capital.

**Subtasks:**
1. Set up paper trading environment (Alpaca paper account) (1h)
2. Run predictions in real-time for 1 week (0.5h setup)
3. Execute paper trades based on signals (1h)
4. Track P&L, Sharpe ratio, win rate (0.5h)
5. Compare paper trading results vs backtest (1h)

**Success Criteria:**
Paper trading performance matches backtest (within ±10%)

**Deliverables:**
- paper_trading_results.md
- performance_comparison.ipynb

---

#### TSK-3.6.3: Production Readiness Checklist

**Duration:** 3.5 hours

**Description:**
Comprehensive pre-launch checklist.

**Subtasks:**
1. Verify all 28 models deployed and tested (0.5h)
2. Confirm endpoint latency < 200ms for all pairs (0.5h)
3. Test auto-scaling under 3x peak load (0.5h)
4. Verify monitoring and alerting working (0.5h)
5. Review security (IAM roles, VPC, encryption) (0.5h)
6. Document runbooks (deployment, rollback, troubleshooting) (1h)

**Success Criteria:**
All checklist items pass, documentation complete

**Deliverables:**
- production_readiness_checklist.md
- runbooks/ (deployment.md, rollback.md, troubleshooting.md)

---

#### TSK-3.6.4: Performance Benchmarking

**Duration:** 3 hours

**Description:**
Comprehensive performance testing.

**Subtasks:**
1. Load test with 100 req/sec for 10 minutes (1h)
2. Measure latency percentiles (P50, P95, P99) (0.5h)
3. Verify auto-scaling triggers at expected threshold (0.5h)
4. Test multi-pair concurrent requests (0.5h)
5. Document performance characteristics (0.5h)

**Success Criteria:**
P99 latency < 200ms, auto-scaling works, no errors

**Deliverables:**
- load_test_report.md
- performance_benchmarks.json

---

#### TSK-3.6.5: Create Rollout Plan

**Duration:** 2.5 hours

**Description:**
Phased rollout strategy for production launch.

**Subtasks:**
1. Define rollout phases (0.5h):
   - Phase 1: 3 pairs (EURUSD, GBPUSD, USDJPY) for 1 week
   - Phase 2: 10 pairs for 1 week
   - Phase 3: All 28 pairs
2. Set success criteria for each phase (0.5h)
3. Create rollout execution checklist (0.5h)
4. Document rollback procedures (0.5h)
5. Get stakeholder sign-off (0.5h)

**Success Criteria:**
Rollout plan approved, phased approach documented

**Deliverables:**
- rollout_plan.md
- phase_success_criteria.md

---

#### TSK-3.6.6: Enhanced Backtesting Framework (NEW)

**Duration:** 12 hours

**Description:**
Comprehensive backtesting framework with trading strategy implementation and SageMaker Batch Transform integration.

**Subtasks:**
1. Design trading strategy rules (2h):
   - Entry: BUY if prediction > +0.0005, SELL if < -0.0005
   - Exit: Take profit 1%, stop loss 0.5%
   - Position sizing: Kelly criterion based on win rate
2. Implement P&L calculation engine (2h):
   - Track entry/exit prices
   - Calculate per-trade P&L
   - Account for spread costs (bid-ask)
   - Compute cumulative returns
3. Integrate with SageMaker Batch Transform (2h):
   - Use batch predictions as signal source
   - Process month-by-month
   - Output: trades.csv with entry/exit/pnl
4. Compute performance metrics (2h):
   - Sharpe ratio (risk-adjusted return)
   - Maximum drawdown (worst peak-to-trough)
   - Win rate (% profitable trades)
   - Profit factor (gross profit / gross loss)
   - Calmar ratio (return / max drawdown)
5. Compare vs buy-and-hold baseline (1h):
   - Buy-and-hold strategy for each pair
   - Relative performance metrics
   - Statistical significance tests
6. Generate comprehensive backtest report (3h):
   - Summary statistics
   - Equity curves
   - Trade distribution analysis
   - Monthly returns heatmap
   - Pair-by-pair performance breakdown

**Success Criteria:**
- Backtest processes 12 months of data for all 28 pairs
- Sharpe ratio > 1.5 (target for profitability)
- Max drawdown < 20%
- Win rate > 52% (above random)
- Performance statistically significant vs buy-and-hold

**Deliverables:**
- enhanced_backtest_framework.py
- trading_strategy.py
- pnl_calculator.py
- batch_transform_integration.py
- backtest_report_generator.py
- docs/backtesting_methodology.md
- comprehensive_backtest_results.html

---

#### TSK-3.6.7: Feature Importance Validation

**Duration:** 2 hours

**Description:**
Validate that 70 selected features are optimal and interpret importance.

**Subtasks:**
1. Visualize feature importance distribution (0.5h)
2. Verify top 70 features capture >95% cumulative importance (0.5h)
3. Interpret top 10 features (which categories dominate?) (0.5h)
4. Document feature selection results per pair (0.5h)

**Success Criteria:**
Top 70 features clearly dominate, interpretation documented

**Deliverables:**
- feature_importance_analysis.ipynb
- docs/selected_features_interpretation.md

---

#### TSK-3.6.8: End-to-End Integration Test

**Duration:** 3 hours

**Description:**
Test complete pipeline from feature extraction to trading signal.

**Subtasks:**
1. Test real-time prediction flow (API Gateway → Lambda → SageMaker → Signal) (1h)
2. Test batch prediction flow (Aurora → Batch Transform → S3) (0.5h)
3. Test monitoring flow (prediction → CloudWatch → alarm → SNS) (0.5h)
4. Test retraining flow (drift detected → Lambda → Training Job → Registry) (1h)

**Success Criteria:**
All flows complete successfully, no errors

**Deliverables:**
- integration_test_results.md
- test_scripts/ (test_realtime.py, test_batch.py, test_monitoring.py, test_retraining.py)

---

## Success Criteria

### Phase-Level Success Criteria

**Phase 3 Complete When:**

1. ✅ All 6 stages completed (33 tasks done)
2. ✅ Production endpoint serving predictions for all 28 pairs
3. ✅ Monitoring operational (no critical alarms)
4. ✅ Documentation complete (runbooks, architecture docs, 8 docs created)
5. ✅ Stakeholder sign-off on phased rollout plan
6. ✅ Paper trading validation passed (1 week minimum)
7. ✅ Backtesting shows Sharpe > 1.5, R² > 0.85

**Quantitative Metrics:**

| Metric | Target | Measurement |
|--------|--------|-------------|
| Prediction latency P99 | <200ms | CloudWatch Metrics |
| Endpoint availability | >99.9% | CloudWatch Uptime |
| Model performance (R²) | >0.85 | Validation set average (28 pairs) |
| Directional accuracy | >52% | Backtest results |
| Sharpe ratio | >1.5 | Backtest results |
| Cost | <$400/month | AWS Cost Explorer |
| Feature count (input) | 70 selected | Model input dimensions |
| Feature count (candidates) | 809 | Before selection |

---

## Cost Analysis

### Training Costs (Per Run)

| Component | Instance | Duration | Cost/Hour | Total |
|-----------|----------|----------|-----------|-------|
| Processing Job | ml.m5.2xlarge | 70 min | $0.806 | $0.94 |
| Training Jobs (28 parallel) | ml.m5.xlarge × 28 | 5 min | $0.403 | $0.93 |
| HPO (3 pairs, quarterly) | ml.m5.xlarge | 250 min × 3 | $0.403 | $5.04 |
| **Total per run** | | | | **$1.87** |
| **Monthly (with HPO/3)** | | | | **$3.55** |

### Inference Costs (Monthly)

| Component | Instance | Hours/Month | Cost/Hour | Total |
|-----------|----------|-------------|-----------|-------|
| Endpoint (baseline) | ml.m5.xlarge × 1 | 720 | $0.269 | $193.68 |
| Endpoint (auto-scale avg) | ml.m5.xlarge × 1.5 | 720 | $0.269 | $290.52 |
| API Gateway | - | 1M requests | $3.50/M | $3.50 |
| Lambda (feature extraction) | - | 1M invocations | $0.20/M | $0.20 |
| Lambda (prediction API) | - | 1M invocations | $0.20/M | $0.20 |

### Storage & Monitoring Costs (Monthly)

| Component | Volume | Cost/Unit | Total |
|-----------|--------|-----------|-------|
| S3 Storage (models, datasets) | 25 GB | $0.023/GB | $0.58 |
| S3 Requests | 10M | $0.005/10K | $5.00 |
| CloudWatch Logs | 10 GB | $0.50/GB | $5.00 |
| CloudWatch Metrics | 100 custom | $0.30/metric | $30.00 |
| SNS Notifications | 1K/month | $0.50/M | $0.50 |
| Model Monitor | 720 hours | $0.27/hour | $194.40 |

### Total Monthly Operational Cost

| Category | Cost |
|----------|------|
| Training | $3.55 |
| Inference | $294.42 |
| Storage & Monitoring | $235.48 |
| **TOTAL** | **$533.45/month** |

**Revised Cost Estimate:** ~$535/month (higher than initial $350 due to Model Monitor costs)

**Cost Optimization Opportunities:**
- Use Savings Plans: -20% ($107/month savings) → **$428/month**
- Reduce Model Monitor frequency: hourly → every 4 hours (-$145/month) → **$388/month**
- Target with optimization: **~$390-430/month**

---

## Integration with Previous Phases

### Dependencies on Phase 1.6 (Feature Infrastructure)

**Required from Phase 1.6:**
- ✅ All 228 base features validated and available in Aurora
- ✅ Feature tables: bqx_{pair} (40), reg_{pair} (57), plus 8 feature tables (131 features)
- ✅ Schema stability: No breaking changes to column names/types
- ✅ Query performance: <100ms for single timestamp query
- ✅ Documentation: Feature catalog with descriptions, ranges, interpretations

**Phase 1.6 Completion Checklist:**
1. Statistics & Bollinger worker complete (TSK-1.6.6.4)
2. Time & Spread worker complete (TSK-1.6.6.5)
3. Correlation worker complete (TSK-1.6.6)
4. Technical indicators complete (TSK-1.6.7)
5. Fibonacci features complete (TSK-1.6.8)
6. Feature validation suite passing (TSK-1.6.9)

**Phase 3 cannot start until Phase 1.6 is 100% complete.**

### Dependencies on Phase 2 (Feature Engineering)

**Required from Phase 2:**
- ✅ Feature engineering pipeline (features.py)
- ✅ Lagged feature generation (4 windows: 60, 120, 180, 240 min)
- ✅ Derived features (momentum_alignment, volatility_regime, trend_strength)
- ✅ Temporal causality rule (61-minute lag for w60_ and agg_)
- ✅ Feature scaling (StandardScaler)

**Integration Points:**
1. **Processing Job (TSK-3.1.2):** Uses FeatureEngineer class from features.py
2. **Training Script (TSK-3.1.3):** Applies feature lagging strategy (142 features × 4 lags)
3. **Feature Selection (TSK-3.1.6):** Selects 70 from 809 generated features
4. **Inference Lambda (TSK-3.4.1):** Applies same feature engineering to real-time data

---

## Risk Assessment

### Critical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Aurora query latency > 100ms | Medium | High | Add indexes, use read replicas, implement Redis caching |
| Multi-model endpoint OOM | Low | High | Monitor memory, compress models, increase instance size if needed |
| Feature drift not detected early | Medium | High | Daily drift checks, lower thresholds, multiple metrics |
| Cost overruns (>$600/month) | High | Medium | Billing alarms, cost allocation tags, optimize Model Monitor frequency |
| Training failures for some pairs | Medium | Medium | Retry logic, continue training others, alert on failures |
| Insufficient auto-scaling | Medium | High | Aggressive scale-out, pre-warm before market open, increase max capacity |

### Mitigation Strategies

**For Latency Issues:**
1. Database indexing on (pair, ts_utc)
2. Read replicas for inference queries
3. Redis caching (5-minute TTL)
4. Fallback: SageMaker Feature Store if Aurora too slow

**For Cost Control:**
1. CloudWatch billing alarms ($400, $500, $600 thresholds)
2. Use Savings Plans (20% discount)
3. Cost allocation tags per pair
4. Weekly cost reviews

**For Feature Drift:**
1. Daily drift detection (not just weekly)
2. Multiple metrics (KL + PSI + Wasserstein)
3. Lower thresholds (KL > 0.05)
4. Automated retraining on drift

---

## Timeline

### 6-Week Execution Plan

**Week 1: Training Pipeline (Stage 3.1)**
- Days 1-2: TSK-3.1.1 (Containers) + TSK-3.1.2 (Processing)
- Days 3-4: TSK-3.1.3 (Training) + TSK-3.1.4 (Parallel)
- Day 5: TSK-3.1.5 (Experiments) + TSK-3.1.6 (Feature Selection)

**Week 2: HPO & Deployment Prep (Stage 3.2)**
- Days 1-2: TSK-3.2.1 (HPO)
- Day 3: TSK-3.2.2 (Model Registry)
- Days 4-5: TSK-3.2.3 (Retraining) + Stage 3.3 prep

**Week 3: Deployment (Stage 3.3)**
- Days 1-2: TSK-3.3.1 (Inference Container) + TSK-3.3.2 (Endpoint)
- Day 3: TSK-3.3.3 (Auto-scaling)
- Days 4-5: TSK-3.3.4 (Blue/Green) + TSK-3.3.5 (A/B)

**Week 4: Inference System (Stage 3.4)**
- Days 1-2: TSK-3.4.1 (Feature Extraction)
- Day 3: TSK-3.4.2 (Prediction API) + TSK-3.4.3 (API Gateway)
- Days 4-5: TSK-3.4.4 (Batch) + TSK-3.4.5 (Signals)

**Week 5: Monitoring (Stage 3.5)**
- Days 1-2: TSK-3.5.1 (Model Monitor) + TSK-3.5.2 (Drift)
- Day 3: TSK-3.5.3 (Dashboard) + TSK-3.5.4 (Retraining Triggers)
- Days 4-5: TSK-3.5.5 (Alerting) + TSK-3.5.6 (Cost Monitoring)

**Week 6: Validation & Launch (Stage 3.6)**
- Days 1-2: TSK-3.6.1 (Backtesting) + TSK-3.6.6 (Enhanced Backtest)
- Day 3: TSK-3.6.2 (Paper Trading) + TSK-3.6.3 (Readiness)
- Day 4: TSK-3.6.4 (Performance) + TSK-3.6.7 (Feature Validation)
- Day 5: TSK-3.6.5 (Rollout Plan) + TSK-3.6.8 (Integration Test)

---

## Deliverables Summary

### Code Deliverables (25+)

**Training & Processing:**
- Dockerfile.training, Dockerfile.processing
- train_sagemaker.py, processing.py
- train_all_pairs.py, feature_selection.py
- hpo_config.py, register_models.py

**Inference & API:**
- Dockerfile.inference, inference.py
- deploy_endpoint.py
- feature_extraction_lambda.py, prediction_api_lambda.py
- signal_generator.py, batch_predict.py

**Monitoring & MLOps:**
- monitoring_config.py, drift_detection_lambda.py
- performance_check_lambda.py, retrain_lambda.py
- alarm_config.py, cost_monitoring_config.py

**Validation & Testing:**
- walk_forward_backtest.py, enhanced_backtest_framework.py
- trading_strategy.py, pnl_calculator.py
- load_test.py, validate_causality.py

### Documentation Deliverables (15+)

**Architecture & Design:**
- docs/sagemaker_architecture.md
- docs/multi_model_endpoint_design.md
- docs/feature_extraction_strategy.md
- docs/feature_lagging_strategy.md
- docs/temporal_causality_integration.md

**Operations:**
- docs/deployment_runbook.md
- docs/rollback_procedures.md
- docs/troubleshooting_guide.md
- docs/cost_optimization_playbook.md

**Development:**
- docs/experiment_tracking.md
- docs/feature_selection_methodology.md
- docs/signal_generation_rules.md

**Validation:**
- docs/backtesting_methodology.md
- docs/backtest_results.md
- docs/paper_trading_results.md
- docs/selected_features_interpretation.md

---

## Next Steps

### Immediate Actions (Before Phase 3 Start)

1. **Verify Phase 1.6 Completion:**
   - Confirm all 228 base features validated
   - Test Aurora query performance (<100ms target)
   - Review feature catalog documentation
   - Freeze feature schema (no changes during Phase 3)

2. **Prepare AWS Environment:**
   - Create S3 buckets (bqx-ml-models, bqx-ml-datasets, bqx-ml-predictions)
   - Set up ECR repositories (3 repos: training, processing, inference)
   - Configure IAM roles with least privilege
   - Set up Secrets Manager for Aurora credentials

3. **Team Preparation:**
   - Assign owners for each stage
   - Schedule kick-off meeting (review architecture)
   - Set up Slack channel (#bqx-ml-sagemaker)
   - Create project management epic for Phase 3 with all 33 tasks

### After Phase 3 Complete

**Phase 4: Live Trading Integration (Next Priority)**
- Connect to Alpaca/IBKR API
- Implement order execution logic
- Add position management (risk limits)
- Real-time P&L tracking

**Phase 5: Model Improvements**
- Replace Random Forest with XGBoost
- Implement ensemble (RF + XGB + LightGBM)
- Explore TFT (Temporal Fusion Transformer)
- Multi-horizon predictions (15, 30, 60, 90, 120 min)

---

## Conclusion

Phase 3 transforms the BQX ML project from a feature engineering platform into a production ML system capable of real-time forex predictions. With 33 tasks across 6 stages, 113 hours of work, and ~$430/month operational cost (optimized), this plan provides a complete blueprint for deploying a SageMaker-powered prediction system.

**Key Success Factors:**
1. Accurate feature count (228 base, 809 with lagging, 70 selected)
2. Comprehensive gap remediation (all 7 gaps addressed)
3. Production-grade architecture (training, inference, monitoring)
4. Clear integration with Phase 1.6 and Phase 2
5. Phased validation (backtesting, paper trading, load testing)
6. Cost optimization and monitoring

**Ready for execution after Phase 1.6 and Phase 2 complete.**
