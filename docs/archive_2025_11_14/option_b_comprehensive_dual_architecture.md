# Option B: Comprehensive Dual Architecture Plan (IDX Expansion + BQX Creation)

**Date:** November 13, 2025
**Version:** 2.0 (Comprehensive)
**Purpose:** Complete dual architecture with expanded schemas in BOTH rate_idx and BQX domains
**Total Features:** 426 features across 6 stages (213 IDX + 213 BQX)

---

## Overview

Option B (Comprehensive) expands BOTH domains to match the 1,080-feature refactored architecture:

1. **Expand existing rate (IDX) tables** - Add columns to existing populated tables
2. **Create new BQX tables** - Build matching comprehensive schemas

This ensures true **dual architecture parity** where both CAUSE (rate_idx) and EFFECT (BQX) domains have identical comprehensive feature sets.

---

## Stage-by-Stage Comprehensive Plan

### Stage 1.6.12: Statistics Dual Architecture (48 + 48 = 96 features)

#### Part A: Expand statistics_rate (IDX)
**Current Schema:** 5 features (skewness_60min, kurtosis_60min, MAD_60min, entropy_60min, autocorr_lag1)
**Target Schema:** 48 features

**Action:** ALTER TABLE to ADD 43 new columns

**New Columns to Add:**
- Mean (5): mean_5min, mean_15min, mean_30min, mean_60min, mean_120min
- Std (5): std_5min, std_15min, std_30min, std_60min, std_120min
- Skewness (4 more): skew_5min, skew_15min, skew_30min, skew_120min
- Kurtosis (4 more): kurt_5min, kurt_15min, kurt_30min, kurt_120min
- Percentiles (10): p5_15min through p90_60min
- Range (3): range_15min, range_30min, range_60min
- IQR (3): iqr_15min, iqr_30min, iqr_60min
- MAD (2 more): mad_15min, mad_30min
- CV (3): cv_15min, cv_30min, cv_60min
- Entropy (2 more): entropy_15min, entropy_30min
- Autocorr (2 more): autocorr_lag5, autocorr_lag15
- Jarque-Bera (2): jb_stat_30min, jb_stat_60min

**Tables Affected:** 336 existing statistics_rate partitions (with 10.3M rows)

#### Part B: Create statistics_bqx
**Schema:** 48 features (identical to expanded statistics_rate)
**Tables Created:** 672 new partitions (28 pairs × 24 months)

**Total Stage 1.6.12:** 96 features (48 expanded + 48 created)

---

### Stage 1.6.13: Bollinger Dual Architecture (20 + 20 = 40 features)

#### Part A: Expand bollinger_rate (IDX)
**Current Schema:** 5 features (bb_upper_20, bb_lower_20, bb_middle_20, bb_width_20, bb_percent_b)
**Target Schema:** 20 features

**Action:** ALTER TABLE to ADD 15 new columns

**New Columns to Add:**
- Upper Band (3 more): bb_upper_30, bb_upper_60, bb_upper_120
- Middle Band (3 more): bb_middle_30, bb_middle_60, bb_middle_120
- Lower Band (3 more): bb_lower_30, bb_lower_60, bb_lower_120
- Bandwidth (3 more): bb_width_30, bb_width_60, bb_width_120
- %B (1 more): bb_percent_b_60
- Slope (2): bb_slope_20, bb_slope_60

**Tables Affected:** 336 existing bollinger_rate partitions (with 10.3M rows)

#### Part B: Create bollinger_bqx
**Schema:** 20 features (identical to expanded bollinger_rate)
**Tables Created:** 672 new partitions

**Total Stage 1.6.13:** 40 features (20 expanded + 20 created)

---

### Stage 1.6.14: Fibonacci Dual Architecture (20 + 20 = 40 features)

#### Part A: Expand fibonacci_rate (IDX)
**Current Schema:** 12 features (fib_retracement_236, 382, 500, 618, 786, fib_extension_1618, 2618, 4236, fib_fan_upper/middle/lower, fib_arc_radius)
**Target Schema:** 20 features

**Action:** ALTER TABLE to ADD 8 new columns

**New Columns to Add:**
- Extension (1 more): fib_ext_1272 (replace fib_extension_1618 with fib_ext_1272, fib_ext_1618, fib_ext_2618)
- Pivot Points (3): pivot_point, resistance_1, support_1
- Distance to Levels (4): dist_to_382, dist_to_500, dist_to_618, dist_to_pivot
- **Note:** May need to rename existing columns for consistency

**Tables Affected:** 336 existing fibonacci_rate partitions (with 10.2M rows)

#### Part B: Create fibonacci_bqx
**Schema:** 20 features (standardized Fibonacci schema)
**Tables Created:** 672 new partitions

**Total Stage 1.6.14:** 40 features (20 expanded + 20 created)

---

### Stage 1.6.15: Volume Dual Architecture (35 + 35 = 70 features)

#### Part A: Create volume_rate (IDX) - NEW
**Schema:** 35 volume-rate_idx interaction features
**Tables Created:** 672 new partitions

**Features:**
- Volume-weighted rate (5 windows)
- Rate-volume correlations (3 windows)
- Volume momentum divergence (4 windows)
- Up/down-tick ratios (8 features)
- Volume × volatility (3)
- Volume trend (3)
- Spike detection (3)
- Cumulative delta (3)
- Imbalance (3)

#### Part B: Create volume_bqx
**Schema:** 35 volume-BQX interaction features (identical structure)
**Tables Created:** 672 new partitions

**Total Stage 1.6.15:** 70 features (35 + 35 new)

---

### Stage 1.6.16: Correlation IDX Architecture (45 features)

#### Part A: Expand correlation_rate (IDX)
**Current Schema:** 16 features (corr_base/quote_pairs_15/60min, rel_strength, divergences, etc.)
**Current Data:** 336 partitions with 0 rows (EMPTY)
**Target Schema:** 45 features

**Action:** Since tables are EMPTY, DROP and RECREATE with expanded schema

**New Schema:** 45 comprehensive correlation features (detailed in previous spec)

**Tables Affected:** 336 correlation_rate partitions (currently empty, will be recreated)

**Total Stage 1.6.16:** 45 features (recreated with expansion)

---

### Stage 1.6.17: Correlation BQX Architecture (45 features)

#### Part A: Create correlation_bqx
**Schema:** 45 features (identical to expanded correlation_rate)
**Tables Created:** 672 new partitions

**Total Stage 1.6.17:** 45 features (new creation)

---

## Comprehensive Summary

### Total Feature Count

| Stage | IDX (rate) | BQX | Total | Action |
|-------|------------|-----|-------|--------|
| 1.6.12 | 48 (expand) | 48 (create) | 96 | ALTER + CREATE |
| 1.6.13 | 20 (expand) | 20 (create) | 40 | ALTER + CREATE |
| 1.6.14 | 20 (expand) | 20 (create) | 40 | ALTER + CREATE |
| 1.6.15 | 35 (create) | 35 (create) | 70 | CREATE + CREATE |
| 1.6.16 | 45 (recreate) | 0 | 45 | DROP + CREATE |
| 1.6.17 | 0 | 45 (create) | 45 | CREATE |
| **TOTAL** | **168** | **168** | **336** | |

**Note:** Total is 336 instead of 426 because:
- Stage 1.6.16: Only IDX (no BQX in this stage)
- Stage 1.6.17: Only BQX (no IDX in this stage)
- Correlation features are split across two stages for clarity

### Table Count

| Category | Tables Affected | Type |
|----------|----------------|------|
| Statistics expansion | 336 partitions | ALTER existing |
| Statistics creation | 672 partitions | CREATE new |
| Bollinger expansion | 336 partitions | ALTER existing |
| Bollinger creation | 672 partitions | CREATE new |
| Fibonacci expansion | 336 partitions | ALTER existing |
| Fibonacci creation | 672 partitions | CREATE new |
| Volume_rate creation | 672 partitions | CREATE new |
| Volume_bqx creation | 672 partitions | CREATE new |
| Correlation_rate recreation | 336 partitions | DROP + CREATE |
| Correlation_bqx creation | 672 partitions | CREATE new |
| **TOTAL** | **5,376 tables** | 1,008 ALTER, 4,704 CREATE, 336 DROP+CREATE |

### Architecture Progress

**Before Option B:**
- Features: 268/1,080 (24.8%)
- Tables: 2,856/11,760 (24.3%)

**After Option B (Comprehensive):**
- Features: 604/1,080 (55.9%) ← **+336 features**
- Tables: 7,896/11,760 (67.1%) ← **+5,040 net new tables**

---

## Implementation Strategy

### Phase 1: Expand Existing IDX Tables (Statistics, Bollinger, Fibonacci)

**Method:** ALTER TABLE ADD COLUMN for each partition
- **Advantage:** Preserves 30.8M existing rows
- **Risk:** Must ensure ALTERs don't lock tables during population
- **Duration:** ~5 minutes per stage (fast ALTER on partitions)

```sql
-- Example: Expand statistics_rate
DO $$
DECLARE
    partition_name TEXT;
BEGIN
    FOR partition_name IN
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'bqx' AND tablename LIKE 'statistics_rate_%'
    LOOP
        EXECUTE format('
            ALTER TABLE bqx.%I
            ADD COLUMN IF NOT EXISTS mean_5min NUMERIC,
            ADD COLUMN IF NOT EXISTS mean_15min NUMERIC,
            -- ... (43 total new columns)
        ', partition_name);
    END LOOP;
END $$;
```

### Phase 2: Create BQX Tables (All Stages)

**Method:** Standard CREATE TABLE + CREATE PARTITION (672 partitions per type)
- **Advantage:** Clean new tables, no risk to existing data
- **Duration:** ~30 seconds per stage (based on technical_bqx performance)

### Phase 3: Recreate Correlation_rate (Empty Tables)

**Method:** DROP existing empty tables, CREATE with expanded schema
- **Advantage:** No data loss (tables are empty), clean schema
- **Duration:** ~30 seconds

---

## Risk Mitigation

### Risk 1: ALTER TABLE Performance on Large Tables

**Mitigation:**
- ALTER TABLE ADD COLUMN is non-blocking (adds NULL values instantly)
- PostgreSQL partitions allow parallel ALTERs
- Tables remain queryable during ALTER

### Risk 2: Existing Data Compatibility

**Mitigation:**
- All new columns are NUMERIC (same type as existing)
- NULL values are acceptable (features will be populated by workers)
- Existing worker scripts continue to work (ignore new columns)

### Risk 3: Execution Time

**Mitigation:**
- Run ALTERs and CREATEs in parallel (6 stages concurrently)
- Expected total time: ~90 seconds (vs. 360+ seconds sequential)

---

## Execution Plan

### Parallel Execution Groups

**Group 1: Expansions (can run in parallel)**
- Stage 1.6.12 Part A: ALTER statistics_rate (43 columns × 336 partitions)
- Stage 1.6.13 Part A: ALTER bollinger_rate (15 columns × 336 partitions)
- Stage 1.6.14 Part A: ALTER fibonacci_rate (8 columns × 336 partitions)

**Group 2: Creations (can run in parallel with Group 1)**
- Stage 1.6.12 Part B: CREATE statistics_bqx (672 partitions)
- Stage 1.6.13 Part B: CREATE bollinger_bqx (672 partitions)
- Stage 1.6.14 Part B: CREATE fibonacci_bqx (672 partitions)
- Stage 1.6.15: CREATE volume_rate + volume_bqx (1,344 partitions)
- Stage 1.6.16: DROP + CREATE correlation_rate (336 partitions)
- Stage 1.6.17: CREATE correlation_bqx (672 partitions)

**Total Parallel Processes:** 9 concurrent operations
**Expected Duration:** ~90 seconds

---

## AirTable Updates Required

For each stage, update with:

**Stage 1.6.12:**
- **Description:** "Statistics Dual Architecture (Option B): Expand existing statistics_rate (5→48 features, 336 partitions, 10.3M rows) + Create statistics_bqx (48 features, 672 partitions). Total: 96 features."
- **Notes:** "ALTER adds 43 columns to existing tables. BQX tables are new."

**Stage 1.6.13:**
- **Description:** "Bollinger Dual Architecture (Option B): Expand existing bollinger_rate (5→20 features, 336 partitions, 10.3M rows) + Create bollinger_bqx (20 features, 672 partitions). Total: 40 features."
- **Notes:** "ALTER adds 15 columns to existing tables. BQX tables are new."

**Stage 1.6.14:**
- **Description:** "Fibonacci Dual Architecture (Option B): Expand existing fibonacci_rate (12→20 features, 336 partitions, 10.2M rows) + Create fibonacci_bqx (20 features, 672 partitions). Total: 40 features."
- **Notes:** "ALTER adds 8 columns to existing tables. BQX tables are new."

**Stage 1.6.15:**
- **Description:** "Volume Dual Architecture (Option B): Create volume_rate (35 features, 672 partitions) + Create volume_bqx (35 features, 672 partitions). Total: 70 features."
- **Notes:** "Both IDX and BQX tables are new (no existing volume tables)."

**Stage 1.6.16:**
- **Description:** "Correlation IDX Architecture (Option B): Recreate correlation_rate with expanded schema (16→45 features, 336 partitions). Tables currently empty."
- **Notes:** "DROP existing empty tables, CREATE with 45-feature schema."

**Stage 1.6.17:**
- **Description:** "Correlation BQX Architecture (Option B): Create correlation_bqx (45 features, 672 partitions)."
- **Notes:** "New BQX correlation tables matching expanded IDX schema."

---

## Verification Queries

### After Execution, Verify:

```sql
-- Check expanded statistics_rate columns
SELECT COUNT(*) as column_count
FROM information_schema.columns
WHERE table_schema = 'bqx' AND table_name = 'statistics_rate_eurusd';
-- Expected: 49 (48 features + ts_utc)

-- Check new statistics_bqx tables
SELECT COUNT(*) as table_count
FROM pg_tables
WHERE schemaname = 'bqx' AND tablename LIKE 'statistics_bqx_%';
-- Expected: 700 (28 parent + 672 partitions)

-- Verify dual architecture parity
SELECT
    'statistics' as feature_type,
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = 'bqx' AND table_name = 'statistics_rate_eurusd') as rate_columns,
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = 'bqx' AND table_name = 'statistics_bqx_eurusd') as bqx_columns,
    CASE
        WHEN rate_columns = bqx_columns THEN '✅ PARITY'
        ELSE '⚠️ MISMATCH'
    END as status;
```

---

## Success Criteria

✅ **All IDX tables expanded** to comprehensive schemas
✅ **All BQX tables created** with matching schemas
✅ **Dual architecture parity** confirmed (IDX columns = BQX columns for each feature type)
✅ **Existing data preserved** (30.8M rows in statistics/bollinger/fibonacci_rate)
✅ **Zero errors** during parallel execution
✅ **Feature count:** 604/1,080 (55.9%)
✅ **Table count:** 7,896/11,760 (67.1%)

---

**Document Version:** 2.0 (Comprehensive Dual Architecture)
**Author:** BQX ML Team
**Date:** November 13, 2025
**Status:** ✅ READY FOR AIRTABLE UPDATE AND EXECUTION
