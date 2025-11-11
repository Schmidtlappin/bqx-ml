# BQX ML Refactor Plan - Airtable Summary

**Created:** 2025-11-10
**Status:** AWAITING USER APPROVAL
**Airtable Base:** BQX-ML (appR3PPnrNkVo48mO)
**Master Plan:** MP-BQX_ML-001: BQX ML Production System (recSb2RvwT60eSu8U)

---

## Overview

A complete refactor plan has been created in Airtable for implementing the **Index-Based Architecture Refactor** for BQX ML. This refactor transitions the system from:

**FROM:**
- Absolute forex rates (EURUSD: 1.0700, USDJPY: 140.00)
- Per-pair models (28 separate models)
- Percentage-normalized features (_pct suffix)

**TO:**
- Forex rate indexes (base-100 with 2024-07-01 baseline)
- Unified multi-pair model (1 model for all 28 pairs)
- Index-based features (no normalization needed)
- Prediction target: Future BQX values at t+60 (i+60)

---

## Airtable Structure Created

### Phase 1.5: Index-Based Architecture Refactor
- **Record ID:** recl7nHgbrLjfjD5K
- **Duration:** 16 hours
- **Status:** Not Started
- **Description:** Refactor BQX ML pipeline to use forex rate indexes (base-100) and unified multi-pair model architecture. Predicts future BQX values at i+60.

### 7 Stages Created

| Stage ID | Stage Name | Duration | Record ID | Tasks |
|----------|------------|----------|-----------|-------|
| 1.5.1 | Baseline Rate Setup | 0.1 hours | recaVaKoNoD1WRjNw | 2 |
| 1.5.2 | M1 Table Enhancement | 3 hours | recs3h7OpwmiX9UH5 | 3 |
| 1.5.3 | BQX Calculation Refactor | 1 hour | recYqIuM6KhosfFG4 | 2 |
| 1.5.4 | BQX Table Recalculation | 8 hours | recXj9JyzCwi6XDhJ | 3 |
| 1.5.5 | REG Table Recalculation | 2 hours | recaRmYMIhlnmQYHV | 3 |
| 1.5.6 | Unified MV Creation | 1 hour | recP9sZC0SXWKnoM2 | 3 |
| 1.5.7 | Unified Model Implementation | 1 hour | rec4PvTPjlsl2B4Yn | 2 |
| **TOTAL** | | **16 hours** | | **18 tasks** |

### 18 Tasks Created

All tasks successfully created with:
- Task ID (TSK-1.5.X.Y)
- Task Name
- Description (with SQL/code examples)
- Status: "Todo"
- Priority: Critical/High/Medium
- Assigned To: Claude Code / Aurora PostgreSQL / backward_worker_threaded.py
- Estimated Hours
- Stage Link
- Plan Link
- Dependencies (noted in descriptions)

---

## Stage Details

### Stage 1.5.1: Baseline Rate Setup (0.1 hours)
**Purpose:** Establish 2024-07-01 baseline rates for all 28 pairs

**Tasks:**
1. TSK-1.5.1.1: Create bqx.baseline_rates table
2. TSK-1.5.1.2: Populate baseline rates from 2024-07-01

**Deliverables:**
- `bqx.baseline_rates` table with 28 rows
- Each pair has baseline_date and baseline_rate

---

### Stage 1.5.2: M1 Table Enhancement (3 hours)
**Purpose:** Add rate_index column to all M1 source tables

**Tasks:**
1. TSK-1.5.2.1: Add rate_index column to M1 tables (0.5h)
2. TSK-1.5.2.2: Calculate rate_index for all M1 rows (2h)
   - Formula: `(close / baseline_rate) * 100`
   - ~3GB of M1 data to update
3. TSK-1.5.2.3: Create indexes on rate_index column (0.5h)

**Deliverables:**
- All 28 M1 tables have `rate_index` column
- All M1 rows have calculated index values
- Performance indexes created

---

### Stage 1.5.3: BQX Calculation Refactor (1 hour)
**Purpose:** Modify BQX calculation logic to use indexes

**Tasks:**
1. TSK-1.5.3.1: Modify backward_worker.py for indexes (0.5h)
   - Update `compute_backward_metrics()` to use `rate_index` instead of `rate`
   - Remove percentage normalization (already normalized by index)
   - Formulas: max/min/avg/stdev directly (no division by rate)
2. TSK-1.5.3.2: Update BQX table schema for indexes (0.5h)
   - Add `rate_index` field
   - Remove `_pct` fields (24 fields removed)
   - Update field definitions

**Deliverables:**
- Modified [backward_worker.py](/home/ubuntu/bqx-ml/scripts/backfill/backward_worker.py)
- Updated BQX table schemas

---

### Stage 1.5.4: BQX Table Recalculation (8 hours)
**Purpose:** Recalculate all BQX tables using index-based formulas

**Tasks:**
1. TSK-1.5.4.1: Drop existing BQX tables (0.5h)
   - Drop all 28 pairs + 336 partitions
2. TSK-1.5.4.2: Create new BQX tables with index schema (0.5h)
   - 37 fields per pair (no _pct fields)
   - Monthly partitioning (2024-07 through 2025-06)
3. TSK-1.5.4.3: Run index-based backfill (7h)
   - Execute `backward_worker_threaded.py`
   - Recalculate 10.3M rows across 28 pairs
   - Expected duration: 6-8 hours

**Deliverables:**
- New BQX tables with index-based calculations
- 10.3M rows recalculated
- All 336 partitions recreated

---

### Stage 1.5.5: REG Table Recalculation (2 hours)
**Purpose:** Update REG tables to use index values

**Tasks:**
1. TSK-1.5.5.1: Document REG table schema (0.5h)
   - Discover schema for reg_{pair} tables
   - Document all 72 features and calculation logic
2. TSK-1.5.5.2: Identify REG features needing index conversion (0.5h)
   - Analyze which features use absolute rates
   - Plan conversion strategy
3. TSK-1.5.5.3: Recalculate REG tables with indexes (1h)
   - Drop and recreate reg_{pair} tables
   - Update calculation scripts

**Deliverables:**
- Documentation of REG table schema
- Updated reg_{pair} tables using indexes

---

### Stage 1.5.6: Unified MV Creation (1 hour)
**Purpose:** Create single materialized view for all 28 pairs

**Tasks:**
1. TSK-1.5.6.1: Design unified MV schema (0.25h)
   - Schema: `(ts_utc, target_pair, target_rate_index, 28 pairs × 37 BQX features = 1,036 columns)`
   - No _pct fields needed (index normalization handles it)
2. TSK-1.5.6.2: Create bqx_ml.features_unified MV (0.5h)
   - UNION ALL of 28 pairs
   - ~10.36M rows total
3. TSK-1.5.6.3: Create indexes on unified MV (0.25h)
   - Index on (target_pair, ts_utc)

**Deliverables:**
- `bqx_ml.features_unified` materialized view
- 1,036 feature columns
- 10.36M rows combining all pairs

---

### Stage 1.5.7: Unified Model Implementation (1 hour)
**Purpose:** Implement unified multi-pair model architecture

**Tasks:**
1. TSK-1.5.7.1: Design unified model architecture (0.5h)
   - Neural network with pair embeddings
   - Input: pair_id (embedded) + 1,036 features
   - Output: future BQX value at t+60 (w60_bqx_return)
   - Document architecture
2. TSK-1.5.7.2: Implement unified model training script (0.5h)
   - Create `scripts/ml/train_unified_model.py`
   - Train single model on all 28 pairs
   - Target: w60_bqx_return at t+60

**Deliverables:**
- Unified model architecture documentation
- [train_unified_model.py](/home/ubuntu/bqx-ml/scripts/ml/train_unified_model.py)
- Trained unified model

---

## Key Technical Changes

### 1. Forex Rate Indexing

**Before:**
```python
# EURUSD
rate = 1.0700  # Absolute rate
rate = 1.0750  # +0.005 (different scale than USDJPY)

# USDJPY
rate = 140.00  # Absolute rate (127× larger scale)
rate = 140.50  # +0.50 (different scale than EURUSD)
```

**After:**
```python
# EURUSD (baseline: 1.0700)
rate_index = 100.00  # Baseline
rate_index = 100.47  # +0.47% (same scale as USDJPY)

# USDJPY (baseline: 140.00)
rate_index = 100.00  # Baseline
rate_index = 100.36  # +0.36% (same scale as EURUSD)
```

### 2. Feature Normalization

**Before (Percentage Normalization):**
```python
# Needed _pct fields for max/min/avg/stdev
w15_bqx_max_pct = (w15_bqx_max - rate) / rate
w15_bqx_min_pct = (w15_bqx_min - rate) / rate
w15_bqx_avg_pct = (w15_bqx_avg - rate) / rate
w15_bqx_stdev_pct = w15_bqx_stdev / rate
# 24 additional _pct fields required
```

**After (Index Normalization):**
```python
# Already normalized by index calculation
w15_bqx_max  # Directly comparable across pairs (around 99-101)
w15_bqx_min  # Directly comparable across pairs (around 99-101)
w15_bqx_avg  # Directly comparable across pairs (around 99-101)
w15_bqx_stdev  # Already scale-independent
# No _pct fields needed
```

### 3. Model Architecture

**Before (Per-Pair Models):**
```python
# 28 separate models
model_eurusd = train_model(data_eurusd)  # ~370k rows
model_usdjpy = train_model(data_usdjpy)  # ~370k rows
# ... 26 more models

# Deployment: 28 model files, 28 endpoints
```

**After (Unified Multi-Pair Model):**
```python
# 1 unified model
model_unified = train_model(data_all_pairs)  # 10.36M rows

# Input features include pair embedding
pair_embedding = embed_pair('EURUSD')  # Learned representation
prediction = model_unified(pair_embedding + features)

# Deployment: 1 model file, 1 endpoint
```

### 4. Prediction Target

**Before (Implicit):**
- Future rate (unclear)
- Future return (percentage)

**After (Explicit):**
- **Future BQX value at t+60** (i+60)
- Specifically: `w60_bqx_return` 60 minutes in the future
- Example: At 10:00, predict w60_bqx_return at 11:00

---

## Benefits of Refactor

### 1. Scale Normalization
- ✅ All pairs on comparable scale (index around 100)
- ✅ No more 127× scale differences
- ✅ Easier for ML model to learn patterns

### 2. Simplified Features
- ✅ Remove 24 _pct fields (794 → 770 fields per MV)
- ✅ Cleaner schema
- ✅ Faster query performance

### 3. Unified Model Advantages
- ✅ Single model learns from all 28 pairs
- ✅ Knowledge sharing across pairs (EUR patterns help USD patterns)
- ✅ More training data (10.36M rows vs ~370k per pair)
- ✅ Easier deployment (1 model vs 28 models)
- ✅ Better generalization to unseen market conditions

### 4. Clear Prediction Target
- ✅ Explicit: Predict w60_bqx_return at t+60
- ✅ Actionable: Know future momentum 60 minutes ahead
- ✅ Testable: Clear success metrics

---

## Risks and Considerations

### 1. Baseline Date Dependency
- ⚠️ All indexes depend on 2024-07-01 baseline
- ⚠️ If baseline is wrong, all indexes are wrong
- ✅ Mitigation: Verify baseline rates before proceeding

### 2. Historical Context Loss
- ⚠️ Absolute rate provides support/resistance context
- ⚠️ Round number psychology lost (USDJPY at 150.00)
- ✅ Mitigation: Keep `rate` field alongside `rate_index`

### 3. Model Complexity
- ⚠️ Unified model more complex than per-pair models
- ⚠️ Pair embeddings add parameters
- ✅ Mitigation: Start with simple architecture, iterate

### 4. Backfill Time
- ⚠️ 6-8 hour backfill required
- ⚠️ Database unavailable during recalculation
- ✅ Mitigation: Run during off-hours, monitor closely

---

## Integration with Existing Plan

### Current Plan Status (Phases 0-10)

**Completed/In Progress:**
- Phase 0: Infrastructure Setup - Not Started
- Phase 1: Data Foundation & BQX Backfill - **In Progress** ✓
- Phase 2: Feature Engineering - **In Progress** ✓

**Not Started:**
- Phase 3: Baseline Model Development - Not Started
- Phase 4-10: Advanced models and deployment

### Refactor Positioning

**Phase 1.5 sits between Phase 1 and Phase 2:**

```
Phase 1: Data Foundation & BQX Backfill
  ↓
Phase 1.5: Index-Based Architecture Refactor ← NEW
  ↓
Phase 2: Feature Engineering (Modified)
  ↓
Phase 3: Baseline Model Development (Modified - unified model)
  ↓
Phase 4-10: Advanced models (will use unified architecture)
```

### Impact on Downstream Phases

**Phase 2: Feature Engineering**
- ✅ Simplified: No _pct calculations needed
- ✅ Change: Use unified MV instead of per-pair MVs
- ⚠️ May need to update cross-pair features

**Phase 3: Baseline Model Development**
- ✅ Simplified: 1 model instead of 28
- ✅ More data: 10.36M rows instead of ~370k
- ⚠️ New architecture: Need pair embeddings

**Phase 4-10: Advanced Models**
- ✅ Same unified architecture applies
- ✅ Transfer learning easier (pre-train on all pairs)
- ✅ Deployment simplified (1 endpoint)

---

## Approval Checklist

Before approving this refactor plan, please confirm:

### Technical Approach
- [ ] Baseline date 2024-07-01 is correct for all pairs
- [ ] Index formula `(rate / baseline_rate) * 100` is correct
- [ ] Prediction target w60_bqx_return at t+60 is correct
- [ ] Unified model architecture is preferred over per-pair models

### Scope and Impact
- [ ] Acceptable to drop and recreate BQX tables (10.3M rows)
- [ ] Acceptable to drop and recreate REG tables
- [ ] 6-8 hour backfill duration is acceptable
- [ ] Database downtime during backfill is acceptable

### Resource Requirements
- [ ] Aurora PostgreSQL has capacity for M1 index calculations
- [ ] SageMaker or local compute available for unified model training
- [ ] Monitoring in place for 6-8 hour backfill process

### Risk Mitigation
- [ ] Backup strategy for current BQX/REG tables
- [ ] Rollback plan if refactor fails
- [ ] Testing plan for index calculations
- [ ] Validation plan for unified model predictions

---

## Next Steps After Approval

1. **Immediate (Phase 1.5.1-1.5.2):**
   - Create baseline_rates table
   - Add rate_index to M1 tables
   - Calculate indexes for M1 data

2. **Short-term (Phase 1.5.3-1.5.4):**
   - Modify backward_worker.py
   - Run BQX backfill with indexes
   - Monitor progress

3. **Medium-term (Phase 1.5.5-1.5.6):**
   - Recalculate REG tables
   - Create unified MV

4. **Final (Phase 1.5.7):**
   - Implement unified model
   - Train on unified MV
   - Validate predictions

---

## Airtable Links

- **Base:** https://airtable.com/appR3PPnrNkVo48mO
- **Phase 1.5:** https://airtable.com/appR3PPnrNkVo48mO/tblbNORPGr9fcOnsP/viwxXNGa8W3cKQIk5/recl7nHgbrLjfjD5K
- **All Stages:** Filter Phases table by "Phase 1.5"
- **All Tasks:** Filter Tasks table by "TSK-1.5"

---

## Summary

A comprehensive refactor plan has been created in Airtable for transitioning BQX ML to an index-based, unified multi-pair architecture. The plan includes:

- **1 Phase** (Phase 1.5: Index-Based Architecture Refactor)
- **7 Stages** (Baseline Setup → M1 Enhancement → BQX Refactor → Recalculation → REG Update → Unified MV → Unified Model)
- **18 Tasks** (All with detailed descriptions, dependencies, and time estimates)
- **16 hours** total estimated duration
- **Integration** with existing Phases 0-10 plan

**AWAITING USER APPROVAL** to proceed with implementation.

---

**Document Created:** 2025-11-10
**Last Updated:** 2025-11-10
**Status:** Pending User Review
**Next Action:** User approval required before beginning Phase 1.5.1
