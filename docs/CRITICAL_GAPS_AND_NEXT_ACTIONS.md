# Critical Gaps and Next Actions
**Date:** 2025-11-12
**Status:** URGENT - Action Required Before Implementation

---

## 🚨 CRITICAL GAP: SageMaker Plan Not Reconciled with 1,080-Feature Architecture

### The Problem

**Two incompatible plans exist:**

1. **SageMaker Phase 3 Plan** (created Nov 11, 2025)
   - Based on OLD architecture
   - 228 base features → 809 with lagging → 70 selected
   - Cost: $286/month
   - Single-domain approach

2. **Refactored BQX ML Plan** (finalized Nov 12, 2025)
   - NEW dual architecture (rate_idx + BQX)
   - 1,080 base features → ~2,600 with lagging → 250 selected
   - Cost: $450-550/month (estimated)
   - Dual-domain approach

**These plans are fundamentally incompatible and MUST be reconciled before starting Phase 3.**

---

## Impact Analysis

### What Breaks if Not Reconciled

| Component | Current (Wrong) | Required (Correct) | Risk Level |
|-----------|-----------------|-------------------|------------|
| **Feature Extraction** | Query 228 features | Query 1,080 features | 🔴 CRITICAL |
| **Processing Pipeline** | Process 809 features | Process ~2,600 features | 🔴 CRITICAL |
| **Feature Selection** | Select 70 from 809 | Select 250 from 2,600 | 🔴 CRITICAL |
| **Instance Size** | ml.m5.xlarge | ml.m5.2xlarge or larger | 🟡 HIGH |
| **Storage** | 25 GB | 80-100 GB | 🟡 HIGH |
| **Cost** | $286/month | $450-550/month | 🟡 HIGH |
| **Latency** | <200ms assumed | May exceed budget | 🟡 HIGH |

### Financial Impact

**Budget underestimated by ~70%:**
- Current estimate: $286/month
- Realistic estimate: $450-550/month
- Annual difference: ~$2,400-3,200

---

## Specific Tasks Requiring Updates

### Stage 3.1: Training Pipeline Development

**TSK-3.1.2: Feature Engineering Processing Job**
```python
# CURRENT (WRONG):
# Queries: BQX (40) + REG (57) + 8 feature tables = 228 features

# REQUIRED (CORRECT):
# Queries: ALL dual architecture tables
# - technical_idx_{pair} (56 features)
# - technical_bqx_{pair} (56 features)
# - statistics_bqx_{pair} (48 features)
# - bollinger_bqx_{pair} (20 features)
# - fibonacci_bqx_{pair} (20 features)
# - correlation_idx_{pair} (45 features)
# - correlation_bqx_{pair} (45 features)
# - error_correction_{pair} (30 features)
# - realized_vol_{pair} (40 features)
# - hmm_regime_{pair} (25 features)
# - cross_sectional_panel (35 features)
# - spectral_features_{pair} (80 features)
# - PLUS all existing BQX, REG, volume, time, spread tables
# = 1,080 base features
```

**TSK-3.1.3: Training Script**
- Update to handle ~2,600 features (with lagging)
- Increase memory allocation
- Adjust processing time estimate: 70 min → 180-200 min

**TSK-3.1.6: Feature Selection**
- Update to select 250 features (not 70)
- Recalibrate importance thresholds
- Add dual-architecture awareness (ensure both rate_idx and BQX represented)

### Stage 3.3: Model Deployment

**TSK-3.3.2: Multi-Model Endpoint**
- Increase instance size: ml.m5.xlarge → ml.m5.2xlarge
- Reason: 250 features × 28 models = higher memory requirements

### Stage 3.4: Real-Time Inference

**TSK-3.4.1: Feature Extraction Lambda**
- Update to query all 1,080 feature tables
- Add caching strategy for advanced features (computed less frequently)
- Optimize query to stay under 100ms latency budget

### Stage 3.5: Monitoring

**TSK-3.5.2: Feature Drift Detection**
- Update baseline: 250 features (not 70)
- Monitor dual architecture separately (rate_idx vs BQX drift)

### Cost Analysis (All Stages)

**Recalculate ALL costs:**

| Component | Old Estimate | New Estimate | Difference |
|-----------|--------------|--------------|------------|
| Processing Job | $0.94 | $2.50 | +$1.56 |
| Training Jobs | $0.93 | $1.20 | +$0.27 |
| Endpoint (baseline) | $193.68 | $270.00 | +$76.32 |
| Storage (S3) | $0.58 | $2.30 | +$1.72 |
| **Monthly Total** | **$286** | **$450-550** | **+$164-264** |

---

## Recommended Action Plan

### Option 1: Full Reconciliation (Recommended)

**Create:** `sagemaker_phase3_reconciled_1080_features.md`

**Update all 33 tasks with:**
1. Correct feature counts (1,080 base, ~2,600 with lagging, 250 selected)
2. Dual architecture table queries
3. Increased instance sizes
4. Realistic cost estimates
5. Optimized latency strategy

**Effort:** 10-12 hours
**Timeline:** 2-3 days
**Deliverable:** Production-ready SageMaker plan aligned with refactored architecture

### Option 2: Phased MVP Approach

**Phase 3a:** Deploy with base features only (730 features)
- Skip advanced features initially
- Validate architecture first
- Cost: $350-400/month

**Phase 3b:** Add advanced features (350 features)
- Error Correction, Realized Vol, HMM, etc.
- After base system proven
- Additional cost: +$100-150/month

**Effort:** 6-8 hours (update Phase 3a only)
**Timeline:** 1-2 days
**Risk:** Delays full feature set, but reduces initial complexity

---

## Decision Required

**BEFORE starting Phase 3 implementation, user must decide:**

1. ✅ **Full reconciliation** (Option 1) - Get it right from the start
   - Pros: Complete system, no rework, accurate costs
   - Cons: 10-12 hours additional planning

2. ⚠️ **Phased MVP** (Option 2) - Launch faster with base features
   - Pros: Faster to production, lower initial cost
   - Cons: Delayed advanced features, potential rework

3. ❌ **Proceed with current plan** (NOT RECOMMENDED)
   - Will fail when trying to load 1,080 features
   - Budget will exceed by 70%
   - Architecture mismatch will cause errors

---

## Files Requiring Updates

### Documentation
- [ ] `/home/ubuntu/bqx-ml/docs/sagemaker_phase3_deployment_plan.md` - MAJOR UPDATE
- [ ] `/home/ubuntu/bqx-ml/docs/sagemaker_architecture.md` - Add dual architecture
- [ ] `/home/ubuntu/bqx-ml/docs/feature_count_reconciliation.md` - Update counts
- [ ] `/home/ubuntu/bqx-ml/docs/bqx_ml_sagemaker_integration_summary.md` - Revise

### AirTable
- [ ] Phase 3 description (update feature counts, costs)
- [ ] Stage 3.1 tasks (6 tasks)
- [ ] Stage 3.3 tasks (instance sizes)
- [ ] Stage 3.4 tasks (feature extraction)
- [ ] Stage 3.5 tasks (drift monitoring)

### Code (Future)
- [ ] `processing.py` - Update feature queries
- [ ] `train_sagemaker.py` - Handle 2,600 features
- [ ] `feature_selection.py` - Select 250 not 70
- [ ] `inference.py` - Load 250-feature models
- [ ] `feature_extraction_lambda.py` - Query 1,080 features

---

## Current Status

**Phase 1.6 (Feature Engineering):**
- ✅ Stages 1.6.1-1.6.8 complete (71 features)
- ⚠️ Stage 1.6.9 CRITICAL - Table renaming (blocks all work)
- 🔨 Stages 1.6.10-1.6.17 planned (325 features)
- 🔨 Stages 1.6.18-1.6.21 planned (130 features)
- 🔨 Stages 1.8.1-1.8.3 planned (320 features)

**Phase 2 (Feature Engineering Pipeline):**
- ⏳ Not started

**Phase 3 (SageMaker):**
- ❌ Plan exists but INCOMPATIBLE with refactored architecture
- ⚠️ MUST reconcile before implementation

---

## Next Immediate Actions

**Priority 1 (CRITICAL):**
1. User decides: Option 1 (full reconciliation) or Option 2 (phased MVP)
2. Execute Stage 1.6.9 (table renaming) - 1 hour, BLOCKS ALL WORK
3. Complete Phase 1.6 feature development (140 hours, can parallelize to 35-40)

**Priority 2 (HIGH):**
1. Reconcile SageMaker Phase 3 plan (10-12 hours)
2. Update AirTable with reconciled plan
3. Update cost estimates and budget
4. Revise timeline for Phase 3

**Priority 3 (MEDIUM):**
1. Update intelligence files
2. Archive outdated documentation
3. Commit reconciled plans to git

---

## Questions for User

1. **Which approach?** Full reconciliation (Option 1) or Phased MVP (Option 2)?

2. **Budget approval?** Can we proceed with $450-550/month operational cost (vs $286 estimated)?

3. **Timeline?** Can we allocate 10-12 hours for SageMaker plan reconciliation before implementation?

4. **Feature priority?** If phased, which advanced features are highest priority?
   - Error Correction (30-60% improvement on 45-75 min horizons)
   - Realized Volatility (15-25% improvement)
   - HMM Regime Detection (20-30% at regime boundaries)
   - Cross-Sectional Panel (20-25% on systematic moves)

---

## Conclusion

**The SageMaker Phase 3 plan MUST be reconciled with the 1,080-feature refactored architecture before implementation begins.**

Proceeding with the current plan will result in:
- ❌ Feature extraction failures (wrong tables queried)
- ❌ Processing pipeline errors (insufficient memory)
- ❌ Model failures (wrong feature counts)
- ❌ Budget overruns (70% higher than estimated)

**Recommendation:** Execute Option 1 (full reconciliation) to ensure successful Phase 3 deployment aligned with the complete refactored architecture.

---

**Created:** 2025-11-12
**Priority:** URGENT
**Owner:** Project Lead
**Action Required:** Decision + 10-12 hours reconciliation work
