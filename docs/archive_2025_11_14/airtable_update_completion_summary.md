# Airtable Plan Update to 100% Current - COMPLETE

**Date:** 2025-11-10
**Base:** BQX-ML (appR3PPnrNkVo48mO)
**Status:** ✅ 100% CURRENT

---

## Summary

Successfully updated the BQX ML Refactor Plan in Airtable to reflect all current refactor dynamics, including the new REG table optimization and ML_CORR recreation requirements.

---

## Updates Completed

### 1. ✅ Stage 1.5.5: REG Table Recalculation - ENHANCED
**Record ID:** recaRmYMIhlnmQYHV
**Action:** Updated Description field

**New Information Added:**
- Rate → rate_index conversion
- **OPTIMIZATION:** Remove 18 *_norm fields (quad_norm, lin_norm, resid_norm for all windows)
- **Schema reduction:** 75 → 57 fields (24% storage savings, ~2.2 GB)
- Detailed deliverables and reasoning

**Reasoning:**
With rate_index, all pairs are on same ~100 scale, making normalization fields redundant:
- AUDCAD a_term_index: ~0.04 (scale: 100)
- USDJPY a_term_index: ~0.04 (scale: 100)
- Already cross-pair comparable without normalization!

**Documentation:** [reg_normalization_analysis.md](reg_normalization_analysis.md)

---

### 2. ✅ Stage 1.5.8: ML Correlation Recalculation - ADDED
**Record ID:** recAXjq4UeDDEWru5
**Action:** Created new stage
**Duration:** 6 hours
**Status:** Todo

**Reasoning:**
- Old ml_corr data used pre-BQX target metric
- Target changed to w60_bqx_return at t+60
- corr(Feature, OldTarget) ≠ corr(Feature, NewTarget)
- Must recalculate ALL feature-to-target correlations

**Deliverables:**
- ml_corr_triangulation_partitioned table created
- 85 monthly partitions (2020-01 through 2026-12)
- Feature-to-target correlations: 28 pairs × ~40 BQX features × 3 windows (60, 240, 390 min)
- Indexes on (source_mv, ts_utc), (correlation_window), (source_mv)
- Verification: correlations in [-1, 1], target = w60_bqx_return at t+60
- Expected size: ~2.4 TB

**Documentation:** [ml_corr_recreation_plan.md](ml_corr_recreation_plan.md)

---

### 3. ✅ Stage 1.5.8 Tasks - CREATED

#### TSK-1.5.8.1: Recreate ml_corr_triangulation_partitioned table
**Record ID:** recCS35vwRh00Umyp
**Duration:** 0.25 hours
**Priority:** High
**Assigned To:** Claude Code
**Dependencies:** TSK-1.5.4.3 (BQX complete), TSK-1.5.6.2 (Unified MV)

#### TSK-1.5.8.2: Calculate feature-to-target correlations
**Record ID:** rec50cxor8LxCqydD
**Duration:** 5 hours
**Priority:** High
**Assigned To:** calculate_ml_corr.py
**Dependencies:** TSK-1.5.8.1

#### TSK-1.5.8.3: Create indexes on ml_corr tables
**Record ID:** recwN2ml5NVCJfbOJ
**Duration:** 0.5 hours
**Priority:** Medium
**Assigned To:** Aurora PostgreSQL
**Dependencies:** TSK-1.5.8.2

#### TSK-1.5.8.4: Verify correlation calculations
**Record ID:** recSTUTcYlg9uRCAo
**Duration:** 0.25 hours
**Priority:** High
**Assigned To:** Claude Code
**Dependencies:** TSK-1.5.8.3

---

### 4. ✅ Phase 1.5 Duration - UPDATED
**Record ID:** recl7nHgbrLjfjD5K
**Action:** Updated Duration field
**Old Value:** 16 hours
**New Value:** 22 hours

**Breakdown:**
- Stage 1.5.1: Baseline Rate Setup - 0.1h ✅ COMPLETE
- Stage 1.5.2: M1 Table Enhancement - 3h ✅ COMPLETE
- Stage 1.5.3: BQX Calculation Refactor - 1h ✅ COMPLETE
- Stage 1.5.4: BQX Table Recalculation - 8h 🔄 IN PROGRESS
- Stage 1.5.5: REG Table Recalculation - 2h (enhanced with _norm removal)
- Stage 1.5.6: Unified MV Creation - 1h
- Stage 1.5.7: Unified Model Implementation - 1h
- **Stage 1.5.8: ML Correlation Recalculation - 6h** (NEW)
- **TOTAL:** 22 hours

---

## Technical Implementation Notes

### Airtable Schema Discoveries

**Stages Table Fields:**
- Stage ID (text)
- Description (long text)
- Status (select: "Todo", "Done")
- Duration (text)
- Phase (Link) - **STRING format**, not array!
- Plan (Link) - **Array format**

**Tasks Table Fields:**
- Task ID (text)
- Task Name (text)
- Description (long text)
- Status (select: "Todo", "Done")
- Priority (select: "High", "Medium")
- Assigned To (text)
- Estimated Hours (number)
- Estimated Cost (number)
- Stage (Link) - **STRING format**, not array!
- Plan (Link) - **Array format**

**Key Insights:**
- Link field formats are inconsistent - some expect strings, some expect arrays
- Status field only accepts predefined values ("Todo", "Done" - NOT "Pending")
- No "Deliverables" field in Stages table - use Description instead
- No "Dependencies" or "Progress %" fields in Tasks table - include in Description

---

## Verification

### View in Airtable
**URL:** https://airtable.com/appR3PPnrNkVo48mO

### Verification Queries

```python
# List all Phase 1.5 stages
GET https://api.airtable.com/v0/appR3PPnrNkVo48mO/Stages
filterByFormula: FIND('Stage 1.5', {Stage ID}) > 0

# Expected: 8 stages (1.5.1 through 1.5.8)
```

```python
# List all Stage 1.5.8 tasks
GET https://api.airtable.com/v0/appR3PPnrNkVo48mO/Tasks
filterByFormula: FIND('TSK-1.5.8', {Task ID}) > 0

# Expected: 4 tasks (TSK-1.5.8.1 through TSK-1.5.8.4)
```

---

## Impact Analysis

### Before Update
- **Plan Status:** 90% current
- **Missing:** Stage 1.5.8 (ML_CORR recalculation)
- **Incomplete:** Stage 1.5.5 (no mention of _norm field removal)
- **Phase 1.5 Duration:** 16 hours (inaccurate)

### After Update
- **Plan Status:** ✅ 100% CURRENT
- **Complete:** All 8 stages documented (1.5.1 through 1.5.8)
- **Accurate:** Stage 1.5.5 includes _norm optimization details
- **Phase 1.5 Duration:** 22 hours (accurate)

### Storage Impact
- **REG optimization:** -2.2 GB (24% reduction from 75→57 fields)
- **ML_CORR recreation:** +2.4 TB (necessary for correct ML feature selection)
- **Net impact:** +2.4 TB (one-time cost for correct correlations)

---

## Current Refactor Status

### ✅ Completed Stages
1. **Stage 1.5.1:** Baseline Rate Setup (0.1h)
2. **Stage 1.5.2:** M1 Table Enhancement (3h)
3. **Stage 1.5.3:** BQX Calculation Refactor (1h)

### 🔄 In Progress
4. **Stage 1.5.4:** BQX Table Recalculation (8h)
   - Stage 1.5.4.1: Drop BQX tables ✅ COMPLETE
   - Stage 1.5.4.2: Create new schema ✅ COMPLETE
   - Stage 1.5.4.3: Backfill data 🔄 IN PROGRESS (PID 390636)

### ⏳ Pending (Scripts Ready)
5. **Stage 1.5.5:** REG Table Recalculation (2h)
   - Scripts: [stage_1_5_5_1_drop_reg_tables.sql](../scripts/refactor/stage_1_5_5_1_drop_reg_tables.sql)
   - Scripts: [stage_1_5_5_2_create_reg_tables_index_schema.sql](../scripts/refactor/stage_1_5_5_2_create_reg_tables_index_schema.sql)
   - Scripts: [regression_worker_index.py](../scripts/backfill/regression_worker_index.py)

### ⏳ Pending (Not Started)
6. **Stage 1.5.6:** Unified MV Creation (1h)
7. **Stage 1.5.7:** Unified Model Implementation (1h)
8. **Stage 1.5.8:** ML Correlation Recalculation (6h) - **NEW**

---

## Next Steps

1. **Monitor Stage 1.5.4.3:** BQX backfill completion (~6-7 hours remaining)
   ```bash
   # Check progress
   tail -f /tmp/stage_1_5_4_3_backfill.log

   # Or check database directly
   SELECT COUNT(*) FROM bqx.bqx_audcad;  # Should be ~380,000
   ```

2. **Execute Stage 1.5.5:** After BQX backfill completes
   ```bash
   # Step 1: Drop old REG tables (0.5h)
   psql -f scripts/refactor/stage_1_5_5_1_drop_reg_tables.sql

   # Step 2: Create new schema (0.5h)
   psql -f scripts/refactor/stage_1_5_5_2_create_reg_tables_index_schema.sql

   # Step 3: Backfill (2h)
   python3 scripts/backfill/regression_worker_index.py
   ```

3. **Proceed with Stages 1.5.6-1.5.8:** After Stage 1.5.5 completes

---

## Files Created/Modified

### Documentation
- [airtable_update_completion_summary.md](airtable_update_completion_summary.md) - This file
- [airtable_plan_verification_v2.md](airtable_plan_verification_v2.md) - Pre-update verification
- [reg_normalization_analysis.md](reg_normalization_analysis.md) - _norm field redundancy proof
- [stage_1_5_5_summary.md](stage_1_5_5_summary.md) - REG refactor execution guide

### Scripts
- [update_plan_to_100_percent.py](../scripts/airtable/update_plan_to_100_percent.py) - Update script

### Airtable Records Created/Modified
- **Modified:** Stage 1.5.5 Description (recaRmYMIhlnmQYHV)
- **Modified:** Phase 1.5 Duration (recl7nHgbrLjfjD5K)
- **Created:** Stage 1.5.8 (recAXjq4UeDDEWru5)
- **Created:** TSK-1.5.8.1 (recCS35vwRh00Umyp)
- **Created:** TSK-1.5.8.2 (rec50cxor8LxCqydD)
- **Created:** TSK-1.5.8.3 (recwN2ml5NVCJfbOJ)
- **Created:** TSK-1.5.8.4 (recSTUTcYlg9uRCAo)

---

## Conclusion

**BQX ML Refactor Plan Status: ✅ 100% CURRENT**

All stages, tasks, and durations in Airtable now accurately reflect:
1. ✅ BQX table recalculation with index data (Stage 1.5.4)
2. ✅ REG table recalculation with index data + _norm removal optimization (Stage 1.5.5)
3. ✅ ML_CORR recalculation with new target (Stage 1.5.8)
4. ✅ Phase 1.5 duration updated: 16h → 22h

The plan is now complete, accurate, and ready to guide execution through the remainder of Phase 1.5.

---

**Created:** 2025-11-10
**Author:** Claude Code
**Status:** COMPLETE - Plan is 100% current
