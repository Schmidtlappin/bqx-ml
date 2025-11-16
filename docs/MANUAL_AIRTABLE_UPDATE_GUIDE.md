# Manual AirTable Update Guide - Enhancement Stages 2.16-2.19

**Date:** 2025-11-16
**Purpose:** Manual instructions to add enhancement stages to AirTable
**Reason:** API script encountered permissions error (403)

---

## Instructions

Manually add the following 4 stages to the AirTable "Phase 2 Stages" table:

---

## Stage 2.16: Cross-Pair Interaction Features

**Field Values:**

| Field | Value |
|-------|-------|
| **Stage** | 2.16 |
| **Name** | Cross-Pair Interaction Features |
| **Status** | Todo |
| **Priority** | High |
| **Duration (hours)** | 40 |
| **Estimated Cost** | $20 |
| **Dependencies** | 2.14, 2.15 |
| **Phase** | Phase 2 |
| **Tier** | Tier 1 (Highest Priority) |
| **ROI** | +30% performance improvement |

**Description:**
```
Implement cross-pair interaction features to exploit forex pair dependencies.

Components:
1. Momentum Products (24 features) - Joint acceleration patterns
2. Relative Volatility Ratios (12 features) - Divergence detection
3. Correlation Drift (12 features) - Pairs decoupling signals
4. Lead-Lag Features (24 features) - Granger causality exploitation

Total: +72 features

Deliverables:
- Database tables: cross_pair_momentum, cross_pair_volatility, cross_pair_correlation_drift, cross_pair_lead_lag
- Python scripts: stage_2_16_cross_pair_interactions.py, granger_causality_analysis.py
- Updated S3 export script

Expected Impact:
- R² improvement: 0.82 → 0.85 (+3.7%)
- Directional accuracy: 65% → 70% (+7.7%)
- Sharpe ratio: 1.5 → 1.75 (+16.7%)

Rationale: Forex pairs are interconnected through shared currencies (USD, EUR, GBP, JPY). Current strategy only captures linear correlations. This stage adds non-linear interaction features.
```

---

## Stage 2.17: Autoencoder Learned Representations

**Field Values:**

| Field | Value |
|-------|-------|
| **Stage** | 2.17 |
| **Name** | Autoencoder Learned Representations |
| **Status** | Todo |
| **Priority** | Very High |
| **Duration (hours)** | 40 |
| **Estimated Cost** | $50 |
| **Dependencies** | 2.16 |
| **Phase** | Phase 2 |
| **Tier** | Tier 2 (Very High Priority) |
| **ROI** | +45% performance improvement |

**Description:**
```
Train ONE shared autoencoder on pooled data from all 28 pairs, then apply independently to each pair.

Architecture Decision: Shared autoencoder trained on 10M+ samples (all pairs) for better generalization.

Train autoencoder to discover non-linear feature combinations.

Architecture:
- Input: 802 features (730 base + 72 cross-pair)
- Encoder: 802 → 512 → 256 → 128 → 64 (bottleneck)
- Decoder: 64 → 128 → 256 → 512 → 802 (reconstruction)
- Loss: MSE reconstruction error

Total: +64 embedding features

Deliverables:
- Trained models: autoencoder_802_to_64.h5 (ONE shared model), embedding_extractor.h5, feature_scaler.pkl
- Database tables: autoencoder_embeddings_{pair} (28 tables with per-pair embedding values, 64 columns each)
- Python scripts: stage_2_17_train_autoencoder.py, extract_embeddings.py, embedding_interpretation.py
- Documentation: Architecture diagram, embedding interpretation report

Note: ONE autoencoder model trained on all pairs' pooled data, then applied to each pair independently to generate 28 tables of pair-specific embedding values.

Expected Impact:
- R² improvement: 0.85 → 0.88 (+3.5%)
- Directional accuracy: 70% → 75% (+7.1%)
- Sharpe ratio: 1.75 → 2.0 (+14.3%)

Rationale: Hand-crafted features miss non-linear patterns. Autoencoder learns compressed representations that capture latent structure. Proven ROI: 2-3x improvement in financial ML.
```

---

## Stage 2.18: Multi-Task Neural Network Architecture

**Field Values:**

| Field | Value |
|-------|-------|
| **Stage** | 2.18 |
| **Name** | Multi-Task Neural Network Architecture |
| **Status** | Todo |
| **Priority** | Medium |
| **Duration (hours)** | 40 |
| **Estimated Cost** | $40 |
| **Dependencies** | 2.17 |
| **Phase** | Phase 2 |
| **Tier** | Tier 4 (Medium Priority) |
| **ROI** | +10% performance improvement |

**Description:**
```
Implement 28 per-pair multi-task neural networks for joint optimization.

Architecture Decision: 28 independent multi-task NNs (one per pair) to maintain per-pair independence while leveraging multi-task learning benefits.

Implement multi-task neural network for joint optimization.

Architecture:
- Input: 866 features (802 base + 64 embeddings)
- Shared layers: 866 → 256 → 128 (universal representations)
- Task heads:
  * BQX_t+60 prediction (primary, weight=1.0)
  * Volatility_t+60 prediction (auxiliary, weight=0.3)
  * Regime_t+60 classification (auxiliary, weight=0.3)

Deliverables:
- Trained models: multi_task_nn_{pair}.h5 (28 models: one per pair)
- SageMaker notebooks: stage_2_18_multi_task_training.ipynb, multi_task_evaluation.ipynb
- Python scripts: stage_2_18_multi_task_train.py (trains all 28 models), multi_task_predict.py
- Documentation: Architecture diagram, ablation study, task correlation analysis, per-pair performance comparison

Note: 28 independent multi-task models (one per pair), each predicting BQX+volatility+regime for its specific pair.

Expected Impact:
- R² improvement: 0.88 → 0.90 (+2.3%)
- Directional accuracy: 75% → 77% (+2.7%)
- Sharpe ratio: 2.0 → 2.1 (+5.0%)

Rationale: BQX, volatility, and regime are correlated tasks. Joint training with shared layers learns better representations and regularizes the primary task.
```

---

## Stage 2.19: Online Adaptive Learning Pipeline

**Field Values:**

| Field | Value |
|-------|-------|
| **Stage** | 2.19 |
| **Name** | Online Adaptive Learning Pipeline |
| **Status** | Todo |
| **Priority** | Medium |
| **Duration (hours)** | 80 |
| **Estimated Cost** | $100/month |
| **Dependencies** | 2.18 |
| **Phase** | Phase 2 |
| **Tier** | Tier 3 (Long-Term Priority) |
| **ROI** | +10% long-term robustness |

**Description:**
```
Implement online learning system for long-term robustness.

Components:
1. Incremental Gradient Descent (River library)
   - Update model every minute with new data
   - Exponential decay for old data (half-life = 6 hours)

2. Concept Drift Detection (ADWIN algorithm)
   - Monitor prediction error distribution
   - Alert when degradation detected

3. Adaptive Ensemble Weighting
   - Adjust RF/GB/XGB/NN weights per regime
   - Softmax weighting based on recent performance

4. Real-Time Pipeline
   - Lambda function triggered every minute
   - DynamoDB for predictions/actuals storage
   - S3 for model checkpoints

Deliverables:
- AWS infrastructure: Lambda (bqx-ml-online-learner), DynamoDB (bqx_predictions), CloudWatch alarms
- Python scripts: stage_2_19_online_learning_setup.py, online_predict_and_learn.py, drift_detector.py
- Monitoring dashboards: Grafana for real-time accuracy, ensemble weights, drift events
- Documentation: Architecture diagram, incident response playbook

Expected Impact:
- Performance maintenance: R² = 0.90 (vs 0.72 after 12 months with static model)
- Sharpe ratio improvement: 2.1 → 2.2 (+4.8% from adaptation)
- Long-term robustness: <5% degradation vs 20% with static model

Rationale: Static models degrade 10-20% annually without retraining. Online learning maintains performance by adapting to regime changes continuously.
```

---

## Summary

After manually adding these 4 stages to AirTable:

**Total Enhancement Stages:** 4 (2.16-2.19)
**Total Duration:** 5 weeks (200 hours)
**Total Cost:** $160 one-time + $100/month ongoing
**Expected Performance Gain:** +47% Sharpe Ratio (1.5 → 2.2)

**Implementation Sequence:**
```
Stage 2.15 (Validation)
    ↓
Stage 2.16 (Week 1) - Cross-Pair Interactions
    ↓
Stage 2.17 (Week 2) - Autoencoder Embeddings
    ↓
Stage 2.18 (Week 3) - Multi-Task Neural Network
    ↓
Stage 2.19 (Weeks 4-5) - Online Adaptive Learning
    ↓
Stage 2.7 (Updated) - S3 Export
    ↓
Phase 3 - SageMaker Deployment
```

**Reference Documents:**
- Complete Implementation Plan: [docs/enhancement_stages_2_16_to_2_19_implementation_plan.md](enhancement_stages_2_16_to_2_19_implementation_plan.md)
- 100% Coverage Reconciliation: [docs/enhancement_reconciliation_100_percent_coverage.md](enhancement_reconciliation_100_percent_coverage.md)
- Executive Summary: [docs/ENHANCEMENT_PLAN_EXECUTIVE_SUMMARY.md](ENHANCEMENT_PLAN_EXECUTIVE_SUMMARY.md)
