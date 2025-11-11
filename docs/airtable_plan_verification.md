# Airtable BQX ML Refactor Plan Verification

**Date:** 2025-11-10
**Base:** BQX-ML (appR3PPnrNkVo48mO)
**Phase:** Phase 1.5: Index-Based Architecture Refactor

---

## Current Plan Status

###  1.5.4: BQX Table Recalculation - ✅ CONFIRMED IN PLAN

**Status:** Included in original plan
**Duration:** 8 hours
**Description:** Drop existing BQX tables and recalculate using index-based formulas

**Tasks:**
- TSK-1.5.4.1: Drop existing BQX tables (0.5h)
- TSK-1.5.4.2: Create new BQX tables with index schema (0.5h)
- TSK-1.5.4.3: Run index-based backfill (7h)

**Deliverables:**
- 28 BQX parent tables recalculated
- 336 BQX partitions recalculated
- 10.3M rows using rate_index instead of absolute rates
- Remove 24 _pct fields (no longer needed)

---

### ✅ Stage 1.5.5: REG Table Recalculation - ✅ CONFIRMED IN PLAN

**Status:** Included in original plan
**Duration:** 2 hours
**Description:** Discover REG table schema and recalculate using index values

**Tasks:**
- TSK-1.5.5.1: Document REG table schema (0.5h)
- TSK-1.5.5.2: Identify REG features needing index conversion (0.5h)
- TSK-1.5.5.3: Recalculate REG tables with indexes (1h)

**Deliverables:**
- 28 REG parent tables recalculated
- 448 REG partitions recalculated
- Schema documentation for 72 REG features
- Updated reg_{pair} tables using rate_index

---

### ❌ Stage 1.5.8: ML Correlation Recalculation - **MISSING FROM PLAN**

**Status:** ⚠️ **NEEDS TO BE ADDED TO AIRTABLE**
**Duration:** 6 hours
**Description:** Recreate ml_corr* tables with correlations calculated against new target (w60_bqx_return at t+60)

**Why This Stage Is Critical:**
- Old ml_corr* data was dropped (saved 2.4 TB, ~$60-120/month)
- Reason: Target changed from pre-BQX metric to future BQX values
- Must recalculate correlations against NEW target
- Required for feature selection in ML pipeline

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
- **Description:** For each pair (28), each BQX feature (~40), each correlation window (60, 240, 390 min), calculate correlation against NEW target: w60_bqx_return at t+60. Expected output: ~2.4 TB.
- **Dependencies:** TSK-1.5.8.1

#### TSK-1.5.8.3: Create indexes on ml_corr tables
- **Duration:** 0.5 hours
- **Priority:** Medium
- **Assignee:** Aurora PostgreSQL (trillium-bqx-cluster)
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
- Stage 1.5.3: BQX Calculation Refactor - 1h 🔜 NEXT
- Stage 1.5.4: BQX Table Recalculation - 8h
- Stage 1.5.5: REG Table Recalculation - 2h
- Stage 1.5.6: Unified MV Creation - 1h
- Stage 1.5.7: Unified Model Implementation - 1h
- **TOTAL:** 16 hours

### Updated Plan (8 Stages)
- Stage 1.5.1: Baseline Rate Setup - 0.1h ✅ COMPLETE
- Stage 1.5.2: M1 Table Enhancement - 3h ✅ COMPLETE
- Stage 1.5.3: BQX Calculation Refactor - 1h 🔜 NEXT
- Stage 1.5.4: BQX Table Recalculation - 8h
- Stage 1.5.5: REG Table Recalculation - 2h
- Stage 1.5.6: Unified MV Creation - 1h
- Stage 1.5.7: Unified Model Implementation - 1h
- **Stage 1.5.8: ML Correlation Recalculation - 6h** ⚠️ **NEW**
- **TOTAL:** 22 hours

---

## Verification Checklist

### ✅ BQX Tables Covered
- [x] Stage 1.5.4 exists in Airtable
- [x] Includes drop, recreate, and backfill tasks
- [x] Uses rate_index instead of absolute rates
- [x] Removes _pct fields

### ✅ REG Tables Covered
- [x] Stage 1.5.5 exists in Airtable
- [x] Includes schema documentation task
- [x] Includes conversion to rate_index
- [x] Covers all 28 pairs and 448 partitions

### ⚠️ ML_CORR Tables - **ACTION REQUIRED**
- [ ] **Stage 1.5.8 MISSING from Airtable - NEEDS TO BE ADDED**
- [ ] Create stage record in Airtable Stages table
- [ ] Create 4 task records (TSK-1.5.8.1 through TSK-1.5.8.4)
- [ ] Link stage to Phase 1.5
- [ ] Link tasks to Stage 1.5.8
- [ ] Set dependencies correctly

---

## Summary

**What's Confirmed:**
- ✅ BQX table recalculation (Stage 1.5.4)
- ✅ REG table recalculation (Stage 1.5.5)

**What's Missing:**
- ❌ ML_CORR table recreation (Stage 1.5.8)

**Action Required:**
1. Manually add Stage 1.5.8 to Airtable (or use add_stage_1_5_8.py script with valid API credentials)
2. Update Phase 1.5 duration from 16 hours to 22 hours
3. Review dependencies between stages 1.5.8 and prior stages

**Cost Impact:**
- Temporary savings: ~$60-120/month (2.4 TB dropped)
- After Stage 1.5.8: Cost returns to baseline (necessary for ML feature selection)

---

**Next Steps:**
1. Add Stage 1.5.8 to Airtable manually or via API
2. Continue with Stage 1.5.3 (BQX Calculation Refactor)
3. Execute stages 1.5.4-1.5.7 as planned
4. Execute Stage 1.5.8 after Stage 1.5.7 completes

---

**Document Created:** 2025-11-10
**Status:** Pending Manual Update to Airtable
**View Plan:** https://airtable.com/appR3PPnrNkVo48mO/tblbNORPGr9fcOnsP/viwxXNGa8W3cKQIk5/recl7nHgbrLjfjD5K
