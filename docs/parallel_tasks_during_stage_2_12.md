# Productive Tasks During Stage 2.12 Execution

**Stage 2.12 Status:** Running in background (ETA: ~20:30 UTC / 3:30 PM PST)
**Duration:** 3-4 hours
**Current Progress:** Processing AUDCAD (pair 1 of 28)

This document lists all productive activities that can be performed in parallel while Stage 2.12 executes.

---

## ✅ COMPLETED TASKS (During This Session)

### High Priority Scripts ✅

1. **✅ Stage 2.14 Worker Script Created**
   - File: [scripts/remediation/stage_2_14_add_covariance_features.py](../scripts/remediation/stage_2_14_add_covariance_features.py)
   - Purpose: Add 6 term covariance features to correlation_bqx tables
   - Status: Ready to execute after Stage 2.12 completes
   - Duration: 2-3 hours

2. **✅ Stage 2.15 Validation Script Created**
   - File: [scripts/remediation/stage_2_15_comprehensive_validation.py](../scripts/remediation/stage_2_15_comprehensive_validation.py)
   - Purpose: Comprehensive validation of schema alignment
   - Status: Ready to execute after Stages 2.12 & 2.14 complete
   - Duration: 1 hour

---

## 📋 RECOMMENDED NEXT TASKS

### 🔴 HIGH PRIORITY (Do These Next)

#### 3. Update S3 Export Script (30 minutes)

**Task:** Add missing feature families to Stage 2.7 export script

**Current Status:** Export script only includes 3 of 9 feature families

**Missing Families:**
- technical_indicators_{pair}
- currency_index_{pair}
- arbitrage_{pair}
- correlation_bqx_{pair}
- enhanced_rmse_{pair}
- regime_{pair}

**Action Items:**
1. Update export query to include all 9 families
2. Add JOIN clauses for missing tables
3. Test on single pair (eurusd 2024_07)
4. Document complete feature list

**Files to Modify:**
- [scripts/ml/export_features_to_s3.py](../scripts/ml/export_features_to_s3.py)

**Why Important:** Ensures complete feature set available for ML training

---

#### 4. Create Monitoring Dashboard Script (20 minutes)

**Task:** Create real-time monitoring script for Stage 2.12 progress

**Purpose:**
- Track pairs completed (X/28)
- Track partitions completed (X/336)
- Show current pair being processed
- Estimate time remaining
- Display recent errors/warnings

**File to Create:**
- `scripts/remediation/monitor_stage_2_12.sh`

**Example Output:**
```
╔══════════════════════════════════════════════════════╗
║    STAGE 2.12: REBUILD reg_bqx - LIVE MONITOR       ║
╚══════════════════════════════════════════════════════╝

Progress:       [████████░░░░░░░░░░░░░░░░] 28.6% (8/28 pairs)
Current Pair:   EURCHF
Partitions:     96/336 complete
Estimated ETA:  19:45 UTC (2:45 PM PST)

Recent Activity:
  ✅ EURJPY: Complete! (8 min 23 sec)
  ✅ EURGBP: Complete! (7 min 45 sec)
  ⏳ EURCHF: Processing partition 2024_09...

Last 5 Minutes:
  - 2 pairs completed
  - 24 partitions populated
  - 780,450 rows inserted
```

---

#### 5. Prepare AirTable Update Script (15 minutes)

**Task:** Create script to update all stages (2.11-2.15) when complete

**Purpose:**
- Mark Stage 2.12 as "Done" with actual metrics
- Mark Stage 2.14 as "Done" with actual metrics
- Mark Stage 2.15 as "Done" with actual metrics
- Update validation report

**File to Create:**
- `scripts/airtable/update_remediation_complete.py`

**Data to Collect:**
- Stage 2.12: Actual duration, pairs processed, partitions created, rows inserted
- Stage 2.14: Actual duration, rows updated, coverage percentage
- Stage 2.15: Validation results (6/6 tests passed)

---

### 🟡 MEDIUM PRIORITY (Optional But Useful)

#### 6. Create Quick Validation Queries (15 minutes)

**Task:** Create SQL script with quick validation queries

**Purpose:** Spot-check Stage 2.12 progress without full validation

**File to Create:**
- `scripts/remediation/quick_validation_queries.sql`

**Queries to Include:**
```sql
-- 1. Check rebuilt tables count
SELECT COUNT(*) FROM pg_tables
WHERE schemaname='bqx' AND tablename ~ '^reg_bqx_[a-z]+$';
-- Expected: 28

-- 2. Check windows in rebuilt table
SELECT DISTINCT regexp_replace(column_name, '_.*', '') AS window
FROM information_schema.columns
WHERE table_name = 'reg_bqx_eurusd' AND column_name ~ '^w[0-9]+';
-- Expected: w60, w90, w150, w240, w390, w630

-- 3. Check sample row count
SELECT COUNT(*) FROM bqx.reg_bqx_eurusd_2024_07;
-- Expected: ~30,000-40,000

-- 4. Check term-based columns exist
SELECT column_name FROM information_schema.columns
WHERE table_name = 'reg_bqx_eurusd'
AND column_name ~ 'quadratic_term|linear_term|constant_term|residual'
LIMIT 10;
-- Expected: All 4 term types present

-- 5. Check data integrity sample
SELECT ts_utc, w60_prediction,
       (w60_quadratic_term + w60_linear_term + w60_constant_term) AS calculated
FROM bqx.reg_bqx_eurusd_2024_07
WHERE w60_prediction IS NOT NULL
LIMIT 5;
-- Expected: prediction ≈ calculated (within 0.001)
```

---

#### 7. Document Schema Changes (20 minutes)

**Task:** Create comprehensive schema change documentation

**File to Create:**
- `docs/schema_changes_2025_11_16.md`

**Content:**
- Before/after schema comparison
- Window alignment details
- Term-based architecture explanation
- Migration rationale
- Rollback procedures

**Sections:**
1. Overview of Changes
2. OLD Schema (coefficient-based, misaligned windows)
3. NEW Schema (term-based, aligned windows)
4. Migration Steps Taken
5. Validation Results
6. Impact on ML Pipeline

---

#### 8. Create Rollback Script (15 minutes)

**Task:** Document rollback procedure if Stage 2.12 fails

**File to Create:**
- `scripts/remediation/rollback_stage_2_12.sql`

**Content:**
```sql
-- Rollback Stage 2.12: Restore from backup
-- Only use if Stage 2.12 fails catastrophically

-- Step 1: Drop failed tables
DROP TABLE IF EXISTS bqx.reg_bqx_eurusd CASCADE;
-- ... repeat for all 28 pairs

-- Step 2: Restore from backup
CREATE TABLE bqx.reg_bqx_eurusd AS
SELECT * FROM bqx_backup_2025_11_16.reg_bqx_eurusd;
-- ... repeat for all 28 pairs

-- Step 3: Verify restoration
SELECT COUNT(*) FROM bqx.reg_bqx_eurusd;
-- Expected: Original row count
```

---

### 🟢 LOW PRIORITY (Nice to Have)

#### 9. Create Performance Analysis Report (30 minutes)

**Task:** Analyze Stage 2.11 & 2.12 performance metrics

**File to Create:**
- `docs/remediation_performance_analysis.md`

**Metrics to Analyze:**
- Stage 2.11: 26.6 minutes for 28 tables, 336 partitions
- Stage 2.12: TBD (collect after completion)
- Rows per second processed
- Cost per million rows
- Comparison to estimates

**Why Useful:** Helps estimate future migration/remediation tasks

---

#### 10. Update README with Schema Architecture (20 minutes)

**Task:** Update project README with final schema architecture

**File to Modify:**
- `README.md` (if exists) or create new

**Sections to Add/Update:**
- Schema architecture overview
- Window alignment explanation
- Term-based vs coefficient-based comparison
- Cross-domain feature integration strategy

---

#### 11. Create Stage 2.12 Progress Tracker (Python) (30 minutes)

**Task:** Create Python script that tracks and visualizes progress

**File to Create:**
- `scripts/remediation/track_stage_2_12_progress.py`

**Features:**
- Parse log file in real-time
- Calculate completion percentage
- Estimate time remaining
- Send notifications on completion
- Generate progress chart

---

#### 12. Prepare ML Integration Examples (30 minutes)

**Task:** Create example code showing how to use aligned features

**File to Create:**
- `docs/ml_integration_examples.md`

**Examples:**
```python
# Example 1: Cross-domain comparison
SELECT r.ts_utc,
       r.w60_quadratic_term AS rate_quad,
       b.w60_quadratic_term AS bqx_quad,
       (r.w60_quadratic_term - b.w60_quadratic_term) AS quad_diff
FROM reg_eurusd_2024_07 r
JOIN reg_bqx_eurusd_2024_07 b USING (ts_utc)
WHERE r.w60_quadratic_term IS NOT NULL;

# Example 2: Covariance-based signals
SELECT ts_utc,
       cov_quad_lin_bqx_60min,
       CASE
         WHEN cov_quad_lin_bqx_60min < -0.7 THEN 'Trend Exhaustion'
         WHEN cov_resid_lin_bqx_60min > 0.8 THEN 'Breakout'
         WHEN cov_resid_quad_bqx_60min > 0.8 THEN 'Regime Change'
         ELSE 'Normal'
       END AS signal_type
FROM correlation_bqx_eurusd_2024_07;
```

---

## 📊 MONITORING STAGE 2.12

### Quick Status Checks

**1. Check if still running:**
```bash
ps aux | grep stage_2_12
```

**2. View recent log (last 20 lines):**
```bash
tail -20 /tmp/logs/remediation/stage_2_12/rebuild.log
```

**3. Count completed pairs:**
```bash
grep "rebuild complete" /tmp/logs/remediation/stage_2_12/rebuild.log | wc -l
```

**4. Count completed partitions:**
```bash
grep "✅.*Complete!" /tmp/logs/remediation/stage_2_12/rebuild.log | wc -l
```

**5. Check current pair:**
```bash
tail -20 /tmp/logs/remediation/stage_2_12/rebuild.log | grep "Starting rebuild"
```

---

## ⏰ TIMELINE

| Time (UTC) | Activity |
|------------|----------|
| 16:38 | Stage 2.12 started |
| 16:38-20:30 | **DO PARALLEL TASKS** (this document) |
| ~20:30 | Stage 2.12 completes |
| 20:30-20:45 | Validate Stage 2.12 results |
| 20:45 | Start Stage 2.14 |
| 20:45-23:00 | Stage 2.14 executes (2-3 hours) |
| ~23:00 | Stage 2.14 completes |
| 23:00-00:00 | Start & complete Stage 2.15 (1 hour) |
| 00:00 | **100% Schema Alignment Achieved** |

---

## 🎯 PRIORITIES SUMMARY

**Must Do (High Priority):**
1. ✅ Stage 2.14 script created
2. ✅ Stage 2.15 script created
3. ⏳ Update S3 export script
4. ⏳ Create monitoring dashboard
5. ⏳ Prepare AirTable update script

**Should Do (Medium Priority):**
6. ⏳ Quick validation queries
7. ⏳ Schema change documentation
8. ⏳ Rollback script

**Nice to Have (Low Priority):**
9. Performance analysis
10. README updates
11. Progress tracker (Python)
12. ML integration examples

---

**Current Status:** Stage 2.12 running, productive parallel work in progress

**Next Immediate Action:** Create monitoring dashboard or update S3 export script

