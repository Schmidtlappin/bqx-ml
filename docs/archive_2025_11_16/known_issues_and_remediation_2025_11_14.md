# Known Issues and Remediation Plan
**Date:** 2025-11-14
**Status:** Complete Analysis
**Phase:** Phase 2 Infrastructure & Preparation

---

## Executive Summary

**Total Issues Identified:** 7
**Critical (Blockers):** 1
**High Priority:** 3
**Medium Priority:** 2
**Low Priority:** 1

**Overall Status:** ✅ All issues have identified remediation plans

---

## Issue 1: vCPU Quota Limitation (CRITICAL - BLOCKER)

### Description
AWS account vCPU limit is 8, but Phase 2 temporary worker requires 32 vCPUs.

### Current State
- **vCPU Limit:** 8
- **Current Usage:** 8 (trillium-master t3.2xlarge)
- **Required:** 32 (c7i.8xlarge temporary worker)
- **Total Needed:** 40+ vCPUs

### Impact
- **Severity:** CRITICAL
- **Blocks:** Phase 2 temporary EC2 launch
- **Affects:** Entire Phase 2 timeline

### Root Cause
Default AWS account vCPU quota for Standard instances (A, C, D, H, I, M, R, T, Z) is 8 vCPUs in us-east-1 region.

### Remediation
**Status:** ✅ IN PROGRESS (Auto-resolving)

**Actions Taken:**
1. ✅ Quota increase requested via Service Quotas API
   - Request ID: `066226bd19bc4d73b9c59b6a6917b625qDZsNuIg`
   - Support Case ID: `176315597600934`
   - Requested Quota: 64 vCPUs (from 8)
   - Profile Used: `trillium-global` (root credentials)
   - Submitted: 2025-11-14 21:32:54 UTC
   - Status: CASE_OPENED

2. ✅ Automated monitoring deployed
   - Script: `/home/ubuntu/bqx-ml/scripts/infrastructure/monitor_and_launch_phase2_worker.sh`
   - Check Interval: 60 seconds
   - Max Wait: 120 minutes
   - Action: Auto-launch c7i.8xlarge when quota ≥ 40

**Expected Resolution:**
- Auto-approval: Minutes to hours (most common)
- Manual review: Up to 2 business days (if needed)

**Verification:**
```bash
# Check quota status
AWS_PROFILE=trillium-global aws service-quotas get-service-quota \
  --service-code ec2 \
  --quota-code L-1216C47A \
  --region us-east-1 \
  --query 'Quota.Value'

# Monitor auto-launch
tail -f /tmp/quota_monitor.log
```

**Owner:** AWS (Auto-approval system)
**ETA:** Hours to 2 business days
**Risk:** LOW (standard quota increase, routinely approved)

---

## Issue 2: Cost Documentation Mismatch (HIGH PRIORITY)

### Description
All documentation and AirTable references Spot pricing ($19.13), but deployment changed to On-Demand ($57.80) due to Spot capacity issues.

### Current State
- **Documented Cost:** $19.13 (Spot c7i.8xlarge @ $0.45/hr)
- **Actual Cost:** $57.80 (On-Demand c7i.8xlarge @ $1.36/hr)
- **Discrepancy:** +$38.67 (202% increase)

### Impact
- **Severity:** HIGH
- **Affects:** Budget tracking, cost reporting, stakeholder expectations
- **Financial Impact:** +$38.67 for Phase 2 execution

### Files Affected
1. `docs/REFACTORED_PLAN_SUMMARY.md` - References $19.13
2. `docs/architecture_decision_temporary_ec2.md` - References Spot pricing
3. `docs/temporary_ec2_implementation_guide.md` - References $19.13
4. `docs/phase_2_ec2_cost_analysis.md` - References $19.13
5. `scripts/airtable/add_phase_2_infrastructure_stage.py` - Cost: 19.13
6. `scripts/infrastructure/launch_temporary_phase2_ec2.sh` - Comments reference Spot

### Remediation
**Status:** ⏳ PENDING

**Required Updates:**

1. **AirTable Stage 2.10:**
   - Update `Estimated Cost`: 19.13 → 57.80
   - Update Notes: Change "Spot" to "On-Demand"
   - Add explanation: "On-Demand used for guaranteed capacity"

2. **Documentation Files:**
   - Update all cost references: $19.13 → $57.80
   - Update all pricing references: Spot → On-Demand
   - Add note: "Originally planned for Spot, changed due to capacity constraints"

3. **Annual Cost Recalculation:**
   - Phase 2 cost: $19.13 → $57.80
   - 1-year total: $200.93 → $239.60
   - Annual savings vs current: $2,775.93 → $2,737.26
   - Annual savings vs in-place: $1,272.60 → $1,233.93

**Action Items:**
- [ ] Update AirTable Stage 2.10 cost and notes
- [ ] Update all 6 documentation files
- [ ] Recalculate and update all cost comparison tables
- [ ] Add "Cost Change Notice" section to key docs

**Owner:** Infrastructure Team
**ETA:** 30 minutes
**Risk:** LOW (documentation only, no technical impact)

---

## Issue 3: Missing Phase 2 Worker Scripts (HIGH PRIORITY)

### Description
Phase 2 orchestration script references worker scripts that don't exist yet.

### Current State
**Missing Scripts:**
1. `scripts/ml/populate_technical_indicators_worker.py` (Stage 2.2)
2. `scripts/ml/populate_arbitrage_detection_worker.py` (Stage 2.4)
3. `scripts/ml/populate_enhanced_rmse_worker.py` (Stage 2.8)
4. `scripts/ml/populate_regime_detection_worker.py` (Stage 2.9)
5. `scripts/ml/populate_temporal_causality_worker.py` (Stage 2.6)
6. `scripts/ml/populate_cross_pair_indices_worker.py` (Stage 2.3)

**Existing (from Track 2):**
- ✅ `scripts/ml/populate_regression_features_parallel.py` (Track 2)

### Impact
- **Severity:** HIGH
- **Blocks:** Phase 2 execution (after quota approval)
- **Affects:** Stages 2.2, 2.3, 2.4, 2.6, 2.8, 2.9

### Root Cause
Worker scripts were planned but not yet implemented. Current focus was infrastructure setup.

### Remediation
**Status:** ⏳ PENDING

**Pattern to Follow:**
Use Track 2 worker as template (`populate_regression_features_parallel.py`):
- Parallel execution with multiprocessing
- Partition-based processing (336 partitions)
- Progress logging with timestamps
- Error handling and retry logic
- Database connection pooling

**Implementation Plan:**

**Priority 1 (Critical Path):**
1. **Stage 2.2 - Technical Indicators** (15 hours, 8 cores)
   - RSI, MACD, Bollinger Bands, ATR, Stochastic
   - Template: Existing TA-Lib functions
   - Complexity: MEDIUM

**Priority 2 (Parallel Tracks):**
2. **Stage 2.4 - Arbitrage Detection** (2 days, 2 cores)
   - Triangle arbitrage opportunities
   - Complexity: HIGH

3. **Stage 2.8 - Enhanced R²/RMSE** (1 day, 2 cores)
   - Extended R² features from Track 2
   - Complexity: LOW (extend existing)

**Priority 3 (Sequential After 2.2):**
4. **Stage 2.3 - Cross-Pair Currency Indices** (2 days)
   - USD, EUR, GBP, JPY indices
   - Complexity: MEDIUM

5. **Stage 2.9 - Regime Detection** (2 days)
   - Trend/Range classification
   - Complexity: HIGH

6. **Stage 2.6 - Temporal Causality** (1 day)
   - Lead/lag relationships
   - Complexity: MEDIUM

**Action Items:**
- [ ] Create worker template based on Track 2
- [ ] Implement Stage 2.2 worker (Priority 1)
- [ ] Implement Stages 2.4, 2.8 workers (Priority 2)
- [ ] Implement Stages 2.3, 2.6, 2.9 workers (Priority 3)
- [ ] Create unit tests for each worker
- [ ] Add workers to orchestration script

**Owner:** ML Engineering Team
**ETA:** 2-3 days (staged implementation)
**Risk:** MEDIUM (well-defined requirements, proven pattern)

---

## Issue 4: Missing Validation Scripts (MEDIUM PRIORITY)

### Description
Orchestration script references validation scripts that don't exist.

### Current State
**Missing Scripts:**
1. `scripts/validation/track_2_validation_queries.sql`
2. `scripts/refactor/stage_2_3_4_create_helper_views.sql`

**Existing Validations:**
- Manual queries in various docs
- Ad-hoc validation in notebooks

### Impact
- **Severity:** MEDIUM
- **Affects:** Data quality assurance, automated validation
- **Workaround:** Manual validation queries

### Remediation
**Status:** ⏳ PENDING

**Required Scripts:**

1. **track_2_validation_queries.sql**
   - Row count validation (expect 2,016,000 rows per partition)
   - NULL value checks
   - Range validation (R², RMSE bounds)
   - Partition completeness
   - Timestamp consistency

2. **stage_2_3_4_create_helper_views.sql**
   - Materialized views for currency indices
   - Helper views for arbitrage calculations
   - Performance optimization views

**Action Items:**
- [ ] Extract validation queries from docs
- [ ] Create consolidated validation SQL script
- [ ] Create helper views SQL script
- [ ] Test validation scripts on Track 2 data
- [ ] Document expected validation outputs

**Owner:** Data Engineering Team
**ETA:** 1 day
**Risk:** LOW (queries already exist, just need consolidation)

---

## Issue 5: S3 Export Script Missing (MEDIUM PRIORITY)

### Description
Phase 2 final stage (2.7) requires S3 export script for Parquet output.

### Current State
- **Requirement:** Export 40-50 GB of features to S3 in Parquet format
- **Script Status:** Not yet created
- **S3 Bucket:** TBD (needs creation or identification)

### Impact
- **Severity:** MEDIUM
- **Blocks:** Final Phase 2 deliverable
- **Affects:** Phase 3 SageMaker data ingestion

### Remediation
**Status:** ⏳ PENDING

**Requirements:**
1. S3 bucket configuration
2. Parquet export optimization (partitioning strategy)
3. Compression (Snappy recommended)
4. Schema preservation
5. Progress reporting

**Implementation:**
- Use `pandas.to_parquet()` or `pyarrow`
- Parallel export (by partition or feature group)
- Validation: Row counts, schema checks
- Estimated duration: 4-6 hours

**Action Items:**
- [ ] Identify or create S3 bucket
- [ ] Create export script (Python)
- [ ] Test export with sample data
- [ ] Optimize for 40-50 GB dataset
- [ ] Add to Stage 2.7 orchestration

**Owner:** Data Engineering Team
**ETA:** 1-2 days
**Risk:** LOW (standard export operation)

---

## Issue 6: Aurora Serverless Scaling Validation (LOW PRIORITY)

### Description
Need to verify Aurora Serverless v2 can handle Phase 2 peak load with temporary EC2.

### Current State
- **Aurora Capacity:** 0.5-32 ACU (configured)
- **Expected Peak:** Unknown for 32-vCPU worker
- **Current Usage:** Track 2 baseline (8 vCPUs)

### Impact
- **Severity:** LOW
- **Affects:** Phase 2 performance, cost optimization
- **Risk:** Potential throttling or slow queries

### Remediation
**Status:** ⏳ MONITORING

**Validation Plan:**
1. Monitor Aurora ACU during initial Phase 2 stages
2. Track query latency and throughput
3. Adjust worker concurrency if needed
4. Document optimal worker configuration

**Monitoring:**
```bash
# Aurora CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name ServerlessDatabaseCapacity \
  --dimensions Name=DBClusterIdentifier,Value=trillium-bqx-cluster \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Maximum
```

**Action Items:**
- [ ] Set up CloudWatch alarms for ACU scaling
- [ ] Monitor first 6 hours of Phase 2 execution
- [ ] Adjust worker count if throttling detected
- [ ] Document optimal configuration

**Owner:** Infrastructure Team
**ETA:** During Phase 2 execution
**Risk:** VERY LOW (Aurora auto-scales, can adjust workers)

---

## Issue 7: Workspace Documentation Clutter (LOW PRIORITY)

### Description
Multiple documentation files with overlapping content and outdated references.

### Current State
- **Total Docs:** 80+ markdown files in `/docs`
- **Archived:** 1 directory (`archive_2025_11_12`)
- **Active:** ~70 files (many outdated)
- **Overlap:** High (multiple plans for same phases)

### Impact
- **Severity:** LOW
- **Affects:** Developer productivity, documentation clarity
- **Risk:** Confusion from outdated information

### Remediation
**Status:** ⏳ PENDING (Part of cleanup task)

**Cleanup Strategy:**

**Archive Criteria:**
1. Pre-Phase 1 planning docs (historical)
2. Superseded plans (e.g., old Phase 2 plans)
3. Interim reports (already consolidated)

**Keep Active:**
1. Current architecture decisions
2. Phase 2/3 execution plans
3. Infrastructure guides
4. SageMaker deployment plans

**Action Items:**
- [ ] Create `docs/archive_2025_11_14` directory
- [ ] Move 40+ outdated docs to archive
- [ ] Create `docs/README.md` with doc index
- [ ] Update references to archived docs

**Owner:** Documentation Team
**ETA:** 1 hour
**Risk:** VERY LOW (archival only, no deletion)

---

## Summary Matrix

| Issue | Severity | Status | Owner | ETA | Risk |
|-------|----------|--------|-------|-----|------|
| 1. vCPU Quota | CRITICAL | IN PROGRESS | AWS | Hours-2 days | LOW |
| 2. Cost Docs | HIGH | PENDING | Infra | 30 min | LOW |
| 3. Worker Scripts | HIGH | PENDING | ML Eng | 2-3 days | MEDIUM |
| 4. Validation Scripts | MEDIUM | PENDING | Data Eng | 1 day | LOW |
| 5. S3 Export | MEDIUM | PENDING | Data Eng | 1-2 days | LOW |
| 6. Aurora Scaling | LOW | MONITORING | Infra | During exec | VERY LOW |
| 7. Doc Cleanup | LOW | PENDING | Docs | 1 hour | VERY LOW |

---

## Critical Path Analysis

**Phase 2 Readiness:**
```
vCPU Quota (BLOCKER)
    ↓
Launch Temporary EC2 (15 min)
    ↓
Configure Worker (10 min)
    ↓
Worker Scripts Ready? ←────┐
    ↓                      │
    NO ─────────────────────┘
    YES
    ↓
Phase 2 Execution (1.8 days)
```

**Current Blockers:**
1. ✅ vCPU Quota (IN PROGRESS, auto-resolving)
2. ❌ Worker Scripts (PENDING, 2-3 days development)

**Parallel Work (During Quota Wait):**
- Update cost documentation (30 min)
- Create validation scripts (1 day)
- Develop worker scripts (2-3 days)
- Plan S3 export (1-2 days)
- Cleanup documentation (1 hour)

**Estimated Phase 2 Start:**
- Quota approved: Hours to 2 days
- Worker scripts ready: 2-3 days
- **Earliest Phase 2 start:** 2-3 days from now

---

## Recommendations

### Immediate Actions (Today)
1. ✅ vCPU quota increase requested (DONE)
2. ⏳ Update cost documentation (30 min)
3. ⏳ Create AirTable issue remediation stages (1 hour)
4. ⏳ Cleanup workspace documentation (1 hour)

### Short Term (1-3 Days)
1. Develop Stage 2.2 worker (technical indicators)
2. Create validation scripts
3. Plan and test S3 export
4. Develop Stages 2.4, 2.8 workers

### Medium Term (During Phase 2)
1. Monitor Aurora scaling
2. Develop remaining workers (2.3, 2.6, 2.9)
3. Optimize worker concurrency
4. Prepare Phase 3 infrastructure

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-11-14 21:30 | Initial issue analysis | Infrastructure Team |
| 2025-11-14 21:45 | vCPU quota increase submitted | Infrastructure Team |
| 2025-11-14 22:00 | Cost documentation identified | Infrastructure Team |

---

**Status:** ✅ Complete Analysis
**Next Review:** 2025-11-15 (after quota approval)
**Owner:** Infrastructure Team
**Approval:** Pending user review
