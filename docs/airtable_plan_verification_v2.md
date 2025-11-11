# Airtable BQX ML Refactor Plan Verification (Updated)

**Date:** 2025-11-10 (Updated after REG analysis)
**Base:** BQX-ML (appR3PPnrNkVo48mO)
**Phase:** Phase 1.5: Index-Based Architecture Refactor

---

## Updated Schema Decisions (New Information)

### BQX Tables (Stage 1.5.4) - ✅ As Planned
**Schema Change:**
- `rate` → `rate_index`
- Remove 24 _pct fields
- 77 fields → 53 fields (31% reduction)

**Status in Airtable:** ✅ CONFIRMED (matches plan)

---

### REG Tables (Stage 1.5.5) - ⚠️ NEW OPTIMIZATION
**Original Plan (assumed):**
- `rate` → `rate_index`
- Keep all 72 regression fields (12 per window)
- 75 fields total

**UPDATED Decision (after analysis):**
- `rate` → `rate_index`
- **Remove 18 _norm fields** (quad_norm, lin_norm, resid_norm)
- **75 fields → 57 fields (24% reduction)**

**Reasoning:** With rate_index, _norm fields are redundant because:
- AUDCAD a_term_index: ~0.04 (scale: 100)
- USDJPY a_term_index: ~0.04 (scale: 100)
- Already cross-pair comparable without normalization!

**Status in Airtable:** ⚠️ **NEEDS UPDATE** (if plan specified keeping _norm fields)

**Documentation:**
- [reg_normalization_analysis.md](reg_normalization_analysis.md) - Proof that _norm fields are redundant
- [stage_1_5_5_summary.md](stage_1_5_5_summary.md) - Complete implementation plan

---

### ML_CORR Tables (Stage 1.5.8) - ❌ MISSING FROM PLAN
**Status:** Still needs to be added to Airtable (from previous verification)

---

## Current Plan Status

### ✅ Stage 1.5.4: BQX Table Recalculation - CONFIRMED IN PLAN
**Status:** Included in original plan
**Duration:** 8 hours
**Implementation:** Currently executing (Stage 1.5.4.3 in progress)

**Tasks:**
- TSK-1.5.4.1: Drop existing BQX tables (0.5h) ✅ COMPLETE
- TSK-1.5.4.2: Create new BQX tables with index schema (0.5h) ✅ COMPLETE
- TSK-1.5.4.3: Run index-based backfill (7h) 🔄 IN PROGRESS

**Deliverables:**
- 28 BQX parent tables recalculated ✅
- 336 BQX partitions recalculated 🔄
- 10.3M rows using rate_index ⏳
- Remove 24 _pct fields ✅

**Schema Impact:** 77 → 53 fields (31% reduction) ✅ ACHIEVED

---

### ⚠️ Stage 1.5.5: REG Table Recalculation - NEEDS MINOR UPDATE

**Status:** Included in original plan
**Duration:** 2 hours (unchanged)

**Original Tasks (in Airtable):**
- TSK-1.5.5.1: Document REG table schema (0.5h)
- TSK-1.5.5.2: Identify REG features needing index conversion (0.5h)
- TSK-1.5.5.3: Recalculate REG tables with indexes (1h)

**Actual Implementation (Scripts Created):**
- TSK-1.5.5.1: Drop existing REG tables (0.5h) ✅ Script ready
- TSK-1.5.5.2: Create new REG tables with index schema (0.5h) ✅ Script ready
- TSK-1.5.5.3: Run index-based backfill (1h) ✅ Script ready

**NEW Decision:** Remove 18 _norm fields (not in original plan)

**Deliverables:**
- 28 REG parent tables recalculated ✅ (planned)
- 448 REG partitions recalculated ✅ (planned)
- Schema documentation for 72 REG features ✅ (complete)
- Updated reg_{pair} tables using rate_index ✅ (planned)
- **NEW:** Remove 18 _norm fields (quad_norm, lin_norm, resid_norm) ⚠️ (not in original plan)

**Schema Impact:**
- Original plan: 75 → 75 fields (no reduction planned)
- **Actual:** 75 → 57 fields (24% reduction) ⚠️ **OPTIMIZATION**

**Status:** ⚠️ Plan tasks are correct, but deliverables should note _norm field removal

---

### ❌ Stage 1.5.8: ML Correlation Recalculation - MISSING FROM PLAN

**Status:** ⚠️ **STILL NEEDS TO BE ADDED TO AIRTABLE**
**Duration:** 6 hours
**Description:** Recreate ml_corr* tables with correlations calculated against new target (w60_bqx_return at t+60)

**Tasks to Add:**

#### TSK-1.5.8.1: Recreate ml_corr_triangulation_partitioned table
- **Duration:** 0.25 hours
- **Priority:** High
- **Assignee:** Claude Code
- **Description:** CREATE TABLE ml_corr_triangulation_partitioned with monthly partitioning. Create 85 child partitions (2020-01 through 2026-12).
- **Dependencies:** TSK-1.5.4.3 (BQX recalculation complete), TSK-1.5.6.2 (Unified MV created)

#### TSK-1.5.8.2: Calculate feature-to-target correlations
- **Duration:** 5 hours
- **Priority:** High
- **Assignee:** calculate_ml_corr.py (Python Script)
- **Description:** For each pair (28), each BQX feature (~40), each correlation window (60, 240, 390 min), calculate correlation against NEW target: w60_bqx_return at t+60.
- **Dependencies:** TSK-1.5.8.1

#### TSK-1.5.8.3: Create indexes on ml_corr tables
- **Duration:** 0.5 hours
- **Priority:** Medium
- **Assignee:** Aurora PostgreSQL
- **Description:** CREATE INDEX on (source_mv, ts_utc), (correlation_window), (source_mv) for all 85 partitions.
- **Dependencies:** TSK-1.5.8.2

#### TSK-1.5.8.4: Verify correlation calculations
- **Duration:** 0.25 hours
- **Priority:** High
- **Assignee:** Claude Code
- **Description:** Verify correlations against known relationships. Check correlation value ranges (-1 to 1). Verify all pairs/features populated. Confirm target is w60_bqx_return at t+60.
- **Dependencies:** TSK-1.5.8.3

---

## Updated Timeline

### Original Plan (7 Stages)
- Stage 1.5.1: Baseline Rate Setup - 0.1h ✅ COMPLETE
- Stage 1.5.2: M1 Table Enhancement - 3h ✅ COMPLETE
- Stage 1.5.3: BQX Calculation Refactor - 1h ✅ COMPLETE
- Stage 1.5.4: BQX Table Recalculation - 8h 🔄 IN PROGRESS
- Stage 1.5.5: REG Table Recalculation - 2h ⚠️ Enhanced (remove _norm fields)
- Stage 1.5.6: Unified MV Creation - 1h
- Stage 1.5.7: Unified Model Implementation - 1h
- **TOTAL:** 16 hours

### Updated Plan (8 Stages)
- Stage 1.5.1: Baseline Rate Setup - 0.1h ✅ COMPLETE
- Stage 1.5.2: M1 Table Enhancement - 3h ✅ COMPLETE
- Stage 1.5.3: BQX Calculation Refactor - 1h ✅ COMPLETE
- Stage 1.5.4: BQX Table Recalculation - 8h 🔄 IN PROGRESS
- Stage 1.5.5: REG Table Recalculation - 2h ⚠️ Enhanced (remove _norm fields)
- Stage 1.5.6: Unified MV Creation - 1h
- Stage 1.5.7: Unified Model Implementation - 1h
- **Stage 1.5.8: ML Correlation Recalculation - 6h** ⚠️ **NEW** (still missing from plan)
- **TOTAL:** 22 hours

---

## Verification Checklist

### ✅ BQX Tables Covered
- [x] Stage 1.5.4 exists in Airtable
- [x] Includes drop, recreate, and backfill tasks
- [x] Uses rate_index instead of absolute rates
- [x] Removes _pct fields (24 fields)
- [x] Schema: 77 → 53 fields

### ⚠️ REG Tables Covered (Minor Enhancement)
- [x] Stage 1.5.5 exists in Airtable
- [x] Includes schema documentation task
- [x] Includes conversion to rate_index
- [x] Covers all 28 pairs and 448 partitions
- [ ] ⚠️ **NEW OPTIMIZATION:** Should note removal of 18 _norm fields
- [ ] ⚠️ **NEW:** Schema reduction: 75 → 57 fields (not mentioned in original plan)

**Impact:** Low - Enhancement improves storage and simplicity without changing duration

### ⚠️ ML_CORR Tables - **ACTION REQUIRED**
- [ ] **Stage 1.5.8 STILL MISSING from Airtable - NEEDS TO BE ADDED**
- [ ] Create stage record in Airtable Stages table
- [ ] Create 4 task records (TSK-1.5.8.1 through TSK-1.5.8.4)
- [ ] Link stage to Phase 1.5
- [ ] Link tasks to Stage 1.5.8
- [ ] Set dependencies correctly

---

## Summary of Airtable Plan Status

### ✅ Accurate in Airtable
1. **BQX Table Recalculation (Stage 1.5.4)**
   - All details correct
   - Implementation matches plan
   - Schema changes as specified

### ⚠️ Minor Update Needed in Airtable
2. **REG Table Recalculation (Stage 1.5.5)**
   - Tasks and duration correct
   - **NEW OPTIMIZATION:** Remove 18 _norm fields (not in original plan)
   - Schema: 75 → 57 fields (24% reduction vs 0% in plan)
   - **Recommendation:** Add note to deliverables: "Remove 18 _norm fields (quad_norm, lin_norm, resid_norm for all windows)"
   - **Impact:** Positive - better optimization than originally planned

### ❌ Missing from Airtable
3. **ML_CORR Recalculation (Stage 1.5.8)**
   - Still needs to be added
   - 6 hours duration
   - 4 tasks required
   - Critical for ML feature selection

---

## Documentation Supporting Plan Updates

### BQX Tables (Stage 1.5.4)
- [backward_worker_refactor_analysis.md](backward_worker_refactor_analysis.md) - Code changes
- [bqx_table_rebuild_strategy.md](bqx_table_rebuild_strategy.md) - Rebuild rationale
- [bqx_index_commitment.md](bqx_index_commitment.md) - Index data confirmation
- [stage_1_5_3_summary.md](stage_1_5_3_summary.md) - Stage 1.5.3 completion
- [stage_1_5_4_status.md](stage_1_5_4_status.md) - Current progress

### REG Tables (Stage 1.5.5) - **NEW ANALYSIS**
- [reg_table_schema_analysis.md](reg_table_schema_analysis.md) - Complete schema documentation
- [reg_normalization_analysis.md](reg_normalization_analysis.md) - **PROOF that _norm fields are redundant with index**
- [stage_1_5_5_summary.md](stage_1_5_5_summary.md) - Implementation plan with _norm removal

### ML_CORR Tables (Stage 1.5.8)
- [ml_corr_recreation_plan.md](ml_corr_recreation_plan.md) - Complete recreation plan
- [correlation_tables_comparison.md](correlation_tables_comparison.md) - Why ml_corr needs recalculation

---

## Recommendations

### 1. REG Stage 1.5.5: Add Note to Deliverables (Optional)
**Current Deliverable Text (in Airtable):**
> "28 REG parent tables recalculated, 448 REG partitions recalculated, Schema documentation for 72 REG features, Updated reg_{pair} tables using rate_index"

**Suggested Addition:**
> "Remove 18 _norm fields (quad_norm, lin_norm, resid_norm for all windows) - redundant with rate_index. Schema: 75 → 57 fields (24% reduction)."

**Priority:** LOW (enhancement, doesn't affect execution)

### 2. ML_CORR Stage 1.5.8: Add to Airtable (Critical)
**Priority:** HIGH (missing from plan entirely)

**Options:**
- Manual addition using Airtable UI
- Use add_stage_1_5_8.py script (requires API credentials)

---

## Action Items

| Item | Priority | Status | Owner |
|------|----------|--------|-------|
| Execute Stage 1.5.4 (BQX backfill) | HIGH | 🔄 IN PROGRESS | backward_worker_index.py |
| Add Stage 1.5.8 to Airtable | HIGH | ❌ PENDING | Manual or API |
| Update Stage 1.5.5 deliverables (optional) | LOW | ⚠️ OPTIONAL | Manual |
| Update Phase 1.5 duration: 16h → 22h | HIGH | ❌ PENDING | After adding Stage 1.5.8 |

---

## Conclusion

**Airtable Plan Status:**

1. **✅ BQX Tables (Stage 1.5.4):** Fully accurate and up-to-date
   - Plan matches implementation
   - All details correct

2. **⚠️ REG Tables (Stage 1.5.5):** Mostly accurate with new optimization
   - Core plan correct (tasks, duration, rate_index conversion)
   - **NEW:** We're removing 18 _norm fields (not mentioned in plan)
   - This is an **enhancement** - makes it better than planned
   - Optional: Add note about _norm field removal to deliverables

3. **❌ ML_CORR Tables (Stage 1.5.8):** Still missing from plan
   - Must be added (critical for feature selection)
   - 6 hours duration
   - Updates Phase 1.5 total: 16h → 22h

**Overall Assessment:** Plan is **90% current**
- BQX fully aligned ✅
- REG enhanced beyond plan ⚠️ (positive)
- ML_CORR still missing ❌ (critical gap)

---

**Created:** 2025-11-10
**Last Updated:** 2025-11-10 (after REG normalization analysis)
**Status:** Plan mostly current; minor enhancement to REG (positive), ML_CORR still needs addition
