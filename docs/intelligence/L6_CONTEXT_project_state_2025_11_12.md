# L6: CONTEXT - BQX ML Project State
**Layer:** L6 - Situational Awareness & Project Context
**Date:** 2025-11-12
**Status:** CRITICAL DECISION POINT
**Phase:** Pre-Phase 3 (SageMaker Deployment)

---

## Current Situation

### Project State Summary

**Completed:**
- ✅ Phase 0: Infrastructure (GitHub, SageMaker Studio, AWS, Aurora)
- ✅ Phase 1.1-1.5: M1 data, BQX indices, REG tables (336 partitions)
- ✅ Phase 1.6.1-1.6.8: 71 features (Volume, Time, OHLC, Statistics, Momentum, Technical, Fibonacci)

**In Progress:**
- 🔨 Phase 1.6.9-1.6.21: Dual architecture features (remaining 1,009 features)
- 🔨 Documentation reconciliation

**Blocked:**
- ⚠️ Phase 1.6.9 (Table Renaming) - CRITICAL - Blocks all subsequent feature work
- ⚠️ Phase 3 (SageMaker) - Plan incompatible with refactored 1,080-feature architecture

---

## Critical Context: Architecture Evolution

### Timeline of Architecture Changes

**Nov 11, 2025 - SageMaker Phase 3 Plan Created:**
- Based on 228-feature architecture
- Features: BQX (40) + REG (57) + 8 feature tables (131) = 228 base
- With lagging: 809 features
- After selection: 70 features
- Cost estimate: $286/month
- Single-domain approach

**Nov 12, 2025 - Refactored Architecture Finalized:**
- Comprehensive 1,080-feature plan created
- Dual architecture: rate_idx (268) + BQX (254) + cross-domain (208) + advanced (350)
- With lagging: ~2,600 features (estimated)
- After selection: ~250 features
- Cost estimate: $450-550/month (projected)
- Dual-domain approach with advanced features

**Result:** Plans are incompatible and require reconciliation.

---

## Environmental Factors

### Database State (Aurora PostgreSQL)
- **Current:** 6,596 tables, 61 GB
- **Projected:** 9,632 tables, 97 GB (after Phase 1.6-1.8 complete)
- **Host:** trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com
- **Critical finding:** Correlation_idx tables exist but are EMPTY (0 rows)

### Git Repository State
- **Branch:** main
- **Recent commits:** Feature documentation, gap analysis, SageMaker planning
- **Uncommitted:** CRITICAL_GAPS_AND_NEXT_ACTIONS.md (just created)

### AirTable State
- **Phases:** 10+ phases defined
- **Stages:** 78 total stages across all phases
- **Recent additions:** 19 stages for Phase 1.6/1.7/1.8 (feature engineering)
- **Phase 3 status:** Exists but based on OLD 228-feature architecture

### AWS Resources
- **Secrets Manager:** Credentials for AirTable API, Aurora DB
- **SageMaker:** Studio configured, no active resources yet
- **S3:** Buckets TBD for Phase 3
- **EC2:** bqx-ml instance running (this environment)

---

## Stakeholder Context

### User Expectations (from PDF analysis)

**PDF 1 of 2 - Core ML Framework:**
- Multi-horizon prediction (i+15, i+30, i+45, i+60, i+75)
- Vol-scaled targets for stable training
- Dual-domain features (rate vs BQX)
- Cross-pair systemic structure
- Multi-resolution rollups

**PDF 2 of 2 - 12 High-Leverage Gaps:**
1. ✅ Cointegration/ECM (Stage 1.6.18)
2. ✅ Regime detection (Stage 1.6.20)
3. ✅ Spectral features (Stage 1.8.3)
4. ✅ Realized volatility (Stage 1.6.19)
5. ✅ Microstructure proxies (advanced features)
6. ✅ Cross-sectional signals (Stage 1.6.21)
7. 🔨 Learned representations (Phase 2)
8. ✅ Target shaping (vol-scaled, multi-task)
9. ✅ 30m/60m layers (Stage 1.8.2)
10. ✅ Parabolic comparisons (Stage 1.8.1)
11. ✅ Data health features (Stage 1.7.3)
12. 🔨 Autoencoder embeddings (planned Phase 2)

**All 12 gaps addressed in planning, but not yet implemented.**

### Performance Targets
- **R²:** 0.82-0.88 (with advanced features)
- **Directional Accuracy:** 65-70%
- **API Latency:** P99 < 200ms
- **Cost:** $286-400/month (now needs revision to $450-550/month)
- **Sharpe Ratio:** >1.5 (backtesting)

---

## Constraints & Pressures

### Resource Constraints
- **Budget:** Need approval for $450-550/month (vs $286 estimated)
- **Time:** User expects rapid execution
- **Compute:** EC2 instance, Aurora DB, limited to current AWS capacity

### Technical Constraints
- **Aurora latency budget:** 100ms for feature extraction
- **SageMaker latency budget:** 200ms P99 end-to-end
- **Feature count:** 1,080 base features confirmed (not 228)
- **Dual architecture:** Must support rate_idx and BQX domains separately

### Quality Constraints
- **Data completeness:** Some feature tables still being populated
- **Schema stability:** Need to freeze schema before Phase 3 starts
- **Testing requirements:** Backtesting, paper trading, load testing all required

---

## Recent Decisions & Their Impact

### Decision 1: Adopt Dual Architecture (Nov 12)
**Decision:** Implement rate_idx + BQX dual feature architecture with 1,080 features
**Rationale:** User PDF expectations, 10-30% performance improvement potential
**Impact:**
- ✅ Comprehensive feature coverage
- ✅ Aligns with user expectations
- ❌ SageMaker plan now incompatible
- ❌ Cost increase $286 → $450-550/month
- ❌ 10-12 hours reconciliation work required

### Decision 2: Add Advanced Features (Nov 12)
**Decision:** Include 350 advanced features (ECM, HMM, realized vol, spectral, etc.)
**Rationale:** 10-30% performance improvement, user PDF gaps
**Impact:**
- ✅ Addresses all 12 user-identified gaps
- ✅ Highest ROI features included
- ❌ Increases complexity
- ❌ Extends Phase 1.6 timeline (140 hours)

### Decision 3: Create 19 AirTable Stages for Phase 1.6-1.8 (Nov 12)
**Decision:** Detailed stage breakdown for feature engineering
**Rationale:** Clear implementation path, progress tracking
**Impact:**
- ✅ Complete transparency
- ✅ Enables parallel execution
- ✅ Clear dependencies mapped
- ⚠️ Phase 3 not updated to match

---

## Pending Decisions

### DECISION REQUIRED 1: SageMaker Reconciliation Approach

**Question:** How to reconcile SageMaker Phase 3 plan with 1,080-feature architecture?

**Option A: Full Reconciliation (Recommended)**
- Update all 33 tasks in Phase 3
- Recalculate costs ($450-550/month)
- Increase instance sizes
- Optimize for 250-feature models
- Effort: 10-12 hours
- Timeline: 2-3 days

**Option B: Phased MVP**
- Phase 3a: Deploy with base 730 features only
- Phase 3b: Add advanced 350 features later
- Effort: 6-8 hours (Phase 3a only)
- Timeline: 1-2 days
- Risk: Delayed full feature set

**Option C: Proceed as-is (NOT RECOMMENDED)**
- High failure risk
- Budget overrun guaranteed
- Architecture mismatch

**Status:** Awaiting user decision
**Impact:** Blocks Phase 3 start
**Urgency:** HIGH - decision needed before Phase 1.6.9 execution

### DECISION REQUIRED 2: Budget Approval

**Question:** Approve increased operational cost?

**Current estimate:** $286/month (based on 228 features, 70 selected)
**Revised estimate:** $450-550/month (based on 1,080 features, 250 selected)
**Annual difference:** ~$2,400-3,200

**Breakdown:**
- Processing: $0.94 → $2.50/run
- Training: $0.93 → $1.20/run
- Endpoint: $193.68 → $270/month
- Storage: $0.58 → $2.30/month

**Status:** Awaiting approval
**Impact:** Affects Phase 3 design decisions
**Urgency:** HIGH

### DECISION REQUIRED 3: Feature Implementation Priority

**Question:** If phased approach, which advanced features first?

**Candidates (by ROI):**
1. **Error Correction (30-60% improvement)** - Highest priority
2. **Realized Volatility (15-25%)** - High priority
3. **HMM Regime (20-30% at boundaries)** - High priority
4. **Cross-Sectional (20-25%)** - High priority
5. Spectral/Wavelet (10-15%) - Medium priority

**Status:** Only relevant if Option B (Phased MVP) chosen
**Impact:** Determines Phase 3a vs 3b scope

---

## Risk Landscape

### Critical Risks (Immediate)

**RISK-001: SageMaker Plan Incompatibility**
- **Probability:** 100% (confirmed)
- **Impact:** Critical (project failure if not addressed)
- **Mitigation:** Execute reconciliation (Option A or B)
- **Status:** Open, requires decision

**RISK-002: Budget Overrun**
- **Probability:** High (70% increase vs estimate)
- **Impact:** High (project viability)
- **Mitigation:** Get budget approval for $450-550/month
- **Status:** Open, requires approval

**RISK-003: Phase 1.6.9 Blocking**
- **Probability:** Medium (manual operation, 1 hour)
- **Impact:** Critical (blocks all subsequent feature work)
- **Mitigation:** Execute immediately after decision
- **Status:** Open, ready to execute

### High Risks (Near-term)

**RISK-004: Aurora Query Latency**
- **Probability:** Medium (1,080 feature queries)
- **Impact:** High (breaks <100ms latency budget)
- **Mitigation:** Caching, query optimization, read replicas
- **Status:** To be tested after Phase 1.6 complete

**RISK-005: Feature Correlation/Redundancy**
- **Probability:** Medium (250 selected from 2,600)
- **Impact:** Medium (model performance, interpretability)
- **Mitigation:** Robust feature selection with correlation removal
- **Status:** Planned in Phase 2

---

## Opportunity Landscape

### Strategic Opportunities

**OPP-001: Advanced Features ROI**
- **Potential:** 10-30% performance improvement
- **Effort:** 140 hours Phase 1.6 + reconciliation
- **Payoff:** Meets/exceeds user expectations
- **Status:** Included in refactored plan

**OPP-002: Dual Architecture Insights**
- **Potential:** Separate rate vs momentum dynamics analysis
- **Value:** Better interpretability, targeted interventions
- **Status:** Core design principle

**OPP-003: Cost Optimization**
- **Potential:** Reduce $550 → $450/month via Savings Plans, optimized monitoring
- **Savings:** $1,200/year
- **Status:** Planned in Stage 3.5.6

---

## Lessons Learned (Reflection)

### What Worked Well

1. **Comprehensive Planning:** Detailed 1,080-feature inventory prevents scope creep
2. **User PDF Analysis:** Uncovered 12 critical gaps early
3. **AirTable Integration:** Clear stage/task tracking enables progress monitoring
4. **Documentation:** Extensive docs ensure knowledge persistence

### What Didn't Work

1. **Sequential Planning:** SageMaker plan created before architecture finalized → incompatibility
2. **Cost Estimation:** Underestimated by 70% due to feature count mismatch
3. **Feature Count Confusion:** 228 vs 1,080 confusion persisted too long

### Improvements for Next Phase

1. **Freeze Architecture Early:** Lock feature list before downstream planning
2. **Parallel Reviews:** Have multiple reviewers validate assumptions
3. **Cost Buffers:** Add 50% contingency to initial estimates
4. **Dependency Mapping:** Clearer visualization of plan dependencies

---

## Action Items (Immediate)

### Priority 1 - Critical Path
- [ ] **User decision:** SageMaker reconciliation approach (Option A or B)
- [ ] **User approval:** $450-550/month budget
- [ ] **Execute:** Stage 1.6.9 table renaming (1 hour, blocks all work)

### Priority 2 - Reconciliation
- [ ] Update SageMaker Phase 3 plan (10-12 hours if Option A)
- [ ] Recalculate all costs with 1,080-feature architecture
- [ ] Update AirTable Phase 3 stages
- [ ] Revise timeline estimates

### Priority 3 - Documentation
- [ ] Update intelligence files (this file)
- [ ] Archive outdated plans
- [ ] Commit reconciled documentation to git

---

## Context for Future Readers

**What happened:** Between Nov 11-12, 2025, the BQX ML architecture evolved from a 228-feature system to a comprehensive 1,080-feature dual architecture. The SageMaker deployment plan created on Nov 11 became incompatible with the refactored architecture finalized on Nov 12.

**Why it matters:** The incompatibility blocks Phase 3 (SageMaker deployment) until reconciled. Costs are 70% higher than estimated. Feature counts, instance sizes, processing times, and storage all require revision.

**What to do:** Before starting Phase 3 implementation, reconcile the SageMaker plan with the 1,080-feature architecture (Option A recommended) and get budget approval for $450-550/month operational cost.

**Key documents:**
- `/home/ubuntu/bqx-ml/docs/CRITICAL_GAPS_AND_NEXT_ACTIONS.md` - Detailed gap analysis
- `/home/ubuntu/bqx-ml/docs/airtable_feature_coverage_verification.md` - Feature inventory
- `/home/ubuntu/bqx-ml/docs/sagemaker_phase3_deployment_plan.md` - Current (incompatible) plan
- `/home/ubuntu/bqx-ml/docs/final_bqx_ml_refactored_plan_summary.md` - New architecture

---

**Next Update:** After user decision on reconciliation approach
**Owner:** Project Lead / Claude AI Assistant
**Audience:** All project stakeholders, future team members
