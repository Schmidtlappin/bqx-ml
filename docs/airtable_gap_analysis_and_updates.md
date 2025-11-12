# AirTable Gap Analysis & Update Plan
**Reconciliation of Current vs Refactored BQX ML Plan**

**Date:** 2025-11-12
**Status:** Gap Analysis Complete
**Purpose:** Identify gaps, optimize structure, and update AirTable

---

## Executive Summary

### Major Gaps Identified
1. **Missing Dual Feature Architecture** - Current plan doesn't reflect rate_idx + BQX dualing
2. **Incomplete Feature Specification** - Only ~200 features vs 730 in refactored plan
3. **Missing Phase 1.6.9-1.6.17** - Table renaming and BQX dual builds not in AirTable
4. **Outdated Timeline** - Doesn't account for parallelization opportunities
5. **Missing Operational Details** - Phase 5 (Production Operations) not fully specified

---

## Gap Analysis by Phase

### Phase 0: Infrastructure ✅ COMPLETE (No Updates Needed)
- GitHub repo exists
- SageMaker Studio configured
- AWS Secrets Manager operational
- **AirTable Status:** Accurate

### Phase 1: Data Foundation ✅ COMPLETE (Minor Updates)
**Current AirTable:**
- Shows BQX backfill complete
- Missing rate_index details

**Updates Needed:**
- Add note about rate_index normalization (base-100)
- Document 10.4M rows across 28 pairs
- Confirm 336 partitions populated

### Phase 1.5: Index Architecture ✅ COMPLETE (Documentation Update)
**Current AirTable:**
- Shows REG backfill complete
- Missing REG_BQX specification

**Updates Needed:**
- Document that REG_BQX already exists (336 partitions)
- Add note about dual architecture foundation

### Phase 1.6: Feature Development 🔨 MAJOR UPDATES NEEDED

**Current AirTable Stages:**
- 1.6.1: Volume ✅
- 1.6.2: Time & Spread ✅
- 1.6.3: OHLC Index ✅
- 1.6.4: Statistics & Bollinger ✅
- 1.6.5: Momentum & Trend ✅
- 1.6.6: Correlation ❌ (empty)
- 1.6.7: Technical (ATR, CCI) ✅
- 1.6.8: Fibonacci ✅

**MISSING CRITICAL STAGES (Must Add):**

#### NEW Stage 1.6.9: Table Renaming & Migration
**Duration:** 1 hour
**Priority:** ⚠️ CRITICAL - Blocks all others
**Description:** Rename all rate-based tables to rate_idx convention
**Tables to Rename:**
- reg_{pair} → reg_idx_{pair}
- statistics_features_{pair} → statistics_idx_{pair}
- bollinger_features_{pair} → bollinger_idx_{pair}
- fibonacci_features_{pair} → fibonacci_idx_{pair}
- volume_features_{pair} → volume_idx_{pair}
- spread_features_{pair} → spread_idx_{pair}
- correlation_features_{pair} → correlation_idx_{pair}

**Tasks:**
- TSK-1.6.9.1: Execute rename SQL script (0.5h)
- TSK-1.6.9.2: Verify row counts unchanged (0.25h)
- TSK-1.6.9.3: Update documentation (0.25h)

#### NEW Stage 1.6.10: Technical IDX Build
**Duration:** 8 hours
**Description:** Build technical indicators on rate_index
**Features:** RSI, MACD, Stochastic, CCI, Williams %R, ROC, ATR, ADX
**Tables:** technical_idx_{pair} (336 partitions)

**Tasks:**
- TSK-1.6.10.1: Create schemas (0.5h)
- TSK-1.6.10.2: Implement technical_idx_worker.py (3h)
- TSK-1.6.10.3: Execute backfill (4h)
- TSK-1.6.10.4: Validate data quality (0.5h)

#### NEW Stage 1.6.11: Technical BQX Build
**Duration:** 8 hours
**Description:** Build technical indicators on BQX momentum
**Features:** Same as 1.6.10 but on BQX (momentum-of-momentum)
**Tables:** technical_bqx_{pair} (336 partitions)

#### NEW Stage 1.6.12: Statistics BQX Build
**Duration:** 6 hours
**Description:** Statistical moments on BQX
**Tables:** statistics_bqx_{pair} (336 partitions)

#### NEW Stage 1.6.13: Bollinger BQX Build
**Duration:** 6 hours
**Description:** Bollinger bands on BQX momentum
**Tables:** bollinger_bqx_{pair} (336 partitions)

#### NEW Stage 1.6.14: Fibonacci BQX Build
**Duration:** 6 hours
**Description:** Fibonacci levels in momentum space
**Tables:** fibonacci_bqx_{pair} (336 partitions)

#### NEW Stage 1.6.15: Volume BQX Build
**Duration:** 4 hours
**Description:** Volume-momentum interaction features
**Tables:** volume_bqx_{pair} (336 partitions)

#### NEW Stage 1.6.16: Correlation IDX Build
**Duration:** 8 hours
**Description:** Populate empty correlation_idx tables
**Tables:** correlation_idx_{pair} (336 partitions)

#### NEW Stage 1.6.17: Correlation BQX Build (FINAL)
**Duration:** 8 hours
**Description:** Cross-pair/cross-window BQX correlations
**Dependencies:** All other BQX features must be complete
**Tables:** correlation_bqx_{pair} (336 partitions)

---

### Phase 2: Feature Engineering Pipeline 🔨 NEEDS MAJOR EXPANSION

**Current AirTable:**
- Shows basic feature extraction (109 raw + 148 lagged)
- Missing comprehensive 730-feature specification

**Updates Needed:**

#### Stage 2.1: Base Feature Extraction
**Update Description to include:**
- 730 base features from dual architecture tables
- Rate_idx domain: 268 features
- BQX domain: 254 features
- Shared/cross-domain: 208 features

#### NEW Stage 2.2: Derived Feature Computation
**Add these feature categories:**
- Lagged features (180)
- Moving averages (24)
- Cross-pair features (44)
- Dual-domain comparisons (28)
- Event & regime detection (26)
- Multi-resolution features (30)

#### Stage 2.3: Feature Selection & Dataset Creation
**Update to include:**
- Feature selection (730 → 195 features)
- Vol-scaled target engineering
- Chronological train/val/test split (70/15/15)
- S3 Parquet dataset creation

---

### Phase 3: Model Development 🔨 NEEDS TIMELINE UPDATE

**Current AirTable:**
- Shows TFT as primary model
- Duration: 113 hours (too long)

**Optimizations:**
1. **Start with XGBoost** (8 hours total)
2. **TFT only if XGBoost R² < 0.85** (saves 60+ hours)
3. **Parallel training** (8 pairs simultaneously)
4. **Reduced Duration:** 113h → 30-40h

**Updated Stages:**

#### Stage 3.1: Baseline Models (NEW)
- Random Forest baseline (5h)
- XGBoost baseline (8h)
- Feature importance analysis (2h)

#### Stage 3.2: Advanced Models (CONDITIONAL)
- Only if XGBoost R² < 0.85
- TFT with GPU (60h if needed)
- Multi-task learning architecture

#### Stage 3.3: Model Selection
- Compare RF vs XGBoost vs TFT (if built)
- Select best model per pair
- Document decision rationale

---

### Phase 4: SageMaker Deployment ✅ WELL SPECIFIED

**Current AirTable:** Good coverage
**Minor Updates:**
- Add multi-model endpoint details
- Specify auto-scaling configuration (1-4 instances)
- Add latency requirements (P99 < 200ms)

---

### Phase 5: Production Operations 🔨 NEEDS ADDITION

**Currently Missing from AirTable**

#### NEW Stage 5.1: Monitoring & Dashboards
**Duration:** 8 hours
**Description:** CloudWatch dashboards, metrics, alerts
**Deliverables:**
- Performance dashboard (R², MAE, latency)
- Cost monitoring dashboard
- Alert configuration (SNS)

#### NEW Stage 5.2: Operational Runbook
**Duration:** 4 hours
**Description:** Incident response procedures
**Deliverables:**
- High latency response procedure
- Model drift response procedure
- Weekly retraining automation

#### NEW Stage 5.3: Continuous Improvement
**Duration:** Ongoing
**Description:** Quarterly model reviews, A/B testing
**Deliverables:**
- Experiment tracking system
- Performance improvement pipeline

---

## Timeline Optimization

### Current AirTable Timeline
- Total: ~300 hours (sequential)
- No parallelization specified

### Optimized Timeline
**With Parallelization:**
- Phase 1.6: 80-100h → 25-30h (4 parallel workers)
- Phase 2: 20h → 15h (optimized queries)
- Phase 3: 113h → 30-40h (XGBoost first, TFT conditional)
- **Total: 300h → 80-100h wall time**

**Cost Optimization:**
- Original estimate: $535/month
- Optimized: $286/month (47% reduction)
- Achieved through:
  - Savings Plans (30% discount)
  - Reduced monitoring frequency
  - Spot instances for training

---

## Resource Updates

### Current AirTable Resources
- Shows generic ML engineer allocation
- Missing specific skill requirements

### Updated Resource Plan
**Phase-Specific Skills:**
- Phase 1.6: Data Engineer (SQL, Python, pandas)
- Phase 2: ML Engineer (feature engineering)
- Phase 3: ML Engineer (XGBoost, TFT)
- Phase 4-5: ML Platform Engineer (SageMaker, Lambda)

**Total Effort:**
- 160 engineering hours
- Can complete in 4 weeks (1 person) or 2 weeks (2 people)

---

## Success Metrics Updates

### Current AirTable Metrics
- R² > 0.85 ✅
- Latency P99 < 200ms ✅
- Cost < $400/month ✅

### Additional Metrics to Add
- **Directional accuracy > 60%** (critical for trading)
- **Feature importance stability** (top 50 features consistent)
- **Model drift threshold** (MAE increase < 20%)
- **Retraining success rate > 90%**

---

## Priority Updates for AirTable

### CRITICAL (Do First)
1. **Add Phase 1.6.9** - Table renaming (blocks everything)
2. **Add Stages 1.6.10-1.6.17** - BQX dual architecture
3. **Update Phase 2** - 730 feature specification

### HIGH (Do Second)
4. **Optimize Phase 3** - XGBoost first, reduce timeline
5. **Add Phase 5 stages** - Operations & monitoring
6. **Update timelines** - Show parallelization

### MEDIUM (Do Third)
7. **Update resource allocations** - Skill-specific
8. **Add success metrics** - Directional accuracy, drift
9. **Document cost optimizations** - $286/month target

---

## Implementation Plan

### Step 1: Create AirTable Update Scripts
```python
# Updates to create:
1. Add 9 new stages to Phase 1.6
2. Add ~40 new tasks across stages
3. Update existing stage descriptions
4. Add Phase 5 operational stages
5. Update timelines with parallelization
```

### Step 2: Execute Updates
- Use AWS Secrets Manager for AirTable credentials
- Update in batches to avoid API limits
- Validate each update before proceeding

### Step 3: Verification
- Confirm all 730 features represented
- Verify timeline adds up to 80-100h wall time
- Check cost projections = $286/month

---

## Summary of Changes

**Stages to Add:** 12 new stages
**Tasks to Add:** ~50 new tasks
**Stages to Update:** 8 existing stages
**Timeline Reduction:** 300h → 80-100h (67% reduction)
**Cost Reduction:** $535 → $286/month (47% reduction)

**Next Step:** Execute AirTable updates using AWS Secrets Manager credentials

---

**Status:** Ready to execute updates
**Approval:** Pending user review