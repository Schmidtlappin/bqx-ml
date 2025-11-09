# BQX Table Structure - Complete Documentation

**Date**: 2025-11-09
**Database**: trillium-bqx-cluster (Aurora PostgreSQL Serverless v2)
**Schema**: bqx
**Status**: ✅ CREATED (Empty, Ready for Data Population)

---

## Executive Summary

Successfully created **28 BQX (Backward Cumulative Returns) tables** for all preferred forex pairs in the Aurora database. Each table contains **40 fields** capturing backward-looking momentum metrics across **5 window sizes** (15, 30, 45, 60, 75 minutes).

**Verification Results**:
- ✅ 28 parent BQX tables
- ✅ 336 monthly partitions (12 per pair: 2024-07 through 2025-06)
- ✅ 28 indexes (ts_utc timestamp indexes)
- ✅ 40 columns per table (verified)
- ✅ All tables empty (0 rows, ready for population)

---

## Table Inventory

### BQX Parent Tables (28 Total)

| Pair | Table Name | Columns | Partitions | Index |
|------|-----------|---------|-----------|-------|
| AUDCAD | bqx_audcad | 40 | 12 | idx_bqx_audcad_ts |
| AUDCHF | bqx_audchf | 40 | 12 | idx_bqx_audchf_ts |
| AUDJPY | bqx_audjpy | 40 | 12 | idx_bqx_audjpy_ts |
| AUDNZD | bqx_audnzd | 40 | 12 | idx_bqx_audnzd_ts |
| AUDUSD | bqx_audusd | 40 | 12 | idx_bqx_audusd_ts |
| CADCHF | bqx_cadchf | 40 | 12 | idx_bqx_cadchf_ts |
| CADJPY | bqx_cadjpy | 40 | 12 | idx_bqx_cadjpy_ts |
| CHFJPY | bqx_chfjpy | 40 | 12 | idx_bqx_chfjpy_ts |
| EURAUD | bqx_euraud | 40 | 12 | idx_bqx_euraud_ts |
| EURCAD | bqx_eurcad | 40 | 12 | idx_bqx_eurcad_ts |
| EURCHF | bqx_eurchf | 40 | 12 | idx_bqx_eurchf_ts |
| EURGBP | bqx_eurgbp | 40 | 12 | idx_bqx_eurgbp_ts |
| EURJPY | bqx_eurjpy | 40 | 12 | idx_bqx_eurjpy_ts |
| EURNZD | bqx_eurnzd | 40 | 12 | idx_bqx_eurnzd_ts |
| EURUSD | bqx_eurusd | 40 | 12 | idx_bqx_eurusd_ts |
| GBPAUD | bqx_gbpaud | 40 | 12 | idx_bqx_gbpaud_ts |
| GBPCAD | bqx_gbpcad | 40 | 12 | idx_bqx_gbpcad_ts |
| GBPCHF | bqx_gbpchf | 40 | 12 | idx_bqx_gbpchf_ts |
| GBPJPY | bqx_gbpjpy | 40 | 12 | idx_bqx_gbpjpy_ts |
| GBPNZD | bqx_gbpnzd | 40 | 12 | idx_bqx_gbpnzd_ts |
| GBPUSD | bqx_gbpusd | 40 | 12 | idx_bqx_gbpusd_ts |
| NZDCAD | bqx_nzdcad | 40 | 12 | idx_bqx_nzdcad_ts |
| NZDCHF | bqx_nzdchf | 40 | 12 | idx_bqx_nzdchf_ts |
| NZDJPY | bqx_nzdjpy | 40 | 12 | idx_bqx_nzdjpy_ts |
| NZDUSD | bqx_nzdusd | 40 | 12 | idx_bqx_nzdusd_ts |
| USDCAD | bqx_usdcad | 40 | 12 | idx_bqx_usdcad_ts |
| USDCHF | bqx_usdchf | 40 | 12 | idx_bqx_usdchf_ts |
| USDJPY | bqx_usdjpy | 40 | 12 | idx_bqx_usdjpy_ts |

---

## Schema Structure

### Complete Field List (40 Fields)

#### Core Fields (3)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `ts_utc` | TIMESTAMPTZ | NO | Timestamp (UTC), Primary Key |
| `rate` | DOUBLE PRECISION | NO | Exchange rate at timestamp |
| `created_at` | TIMESTAMPTZ | NO | Row creation timestamp (default: now()) |

#### Window 15 Minutes (6 Fields)

| Column | Type | Nullable | Formula |
|--------|------|----------|---------|
| `w15_bqx_return` | DOUBLE PRECISION | YES | Σ(i=1 to 15)[rate(t-i) - rate(t)] / rate(t) |
| `w15_bqx_max` | DOUBLE PRECISION | YES | MAX(rate(t-15) to rate(t-1)) |
| `w15_bqx_min` | DOUBLE PRECISION | YES | MIN(rate(t-15) to rate(t-1)) |
| `w15_bqx_avg` | DOUBLE PRECISION | YES | AVG(rate(t-15) to rate(t-1)) |
| `w15_bqx_stdev` | DOUBLE PRECISION | YES | STDEV(rate(t-15) to rate(t-1)) |
| `w15_bqx_endpoint` | DOUBLE PRECISION | YES | (rate(t-15) - rate(t)) / rate(t) |

#### Window 30 Minutes (6 Fields)

| Column | Type | Nullable | Formula |
|--------|------|----------|---------|
| `w30_bqx_return` | DOUBLE PRECISION | YES | Σ(i=1 to 30)[rate(t-i) - rate(t)] / rate(t) |
| `w30_bqx_max` | DOUBLE PRECISION | YES | MAX(rate(t-30) to rate(t-1)) |
| `w30_bqx_min` | DOUBLE PRECISION | YES | MIN(rate(t-30) to rate(t-1)) |
| `w30_bqx_avg` | DOUBLE PRECISION | YES | AVG(rate(t-30) to rate(t-1)) |
| `w30_bqx_stdev` | DOUBLE PRECISION | YES | STDEV(rate(t-30) to rate(t-1)) |
| `w30_bqx_endpoint` | DOUBLE PRECISION | YES | (rate(t-30) - rate(t)) / rate(t) |

#### Window 45 Minutes (6 Fields)

| Column | Type | Nullable | Formula |
|--------|------|----------|---------|
| `w45_bqx_return` | DOUBLE PRECISION | YES | Σ(i=1 to 45)[rate(t-i) - rate(t)] / rate(t) |
| `w45_bqx_max` | DOUBLE PRECISION | YES | MAX(rate(t-45) to rate(t-1)) |
| `w45_bqx_min` | DOUBLE PRECISION | YES | MIN(rate(t-45) to rate(t-1)) |
| `w45_bqx_avg` | DOUBLE PRECISION | YES | AVG(rate(t-45) to rate(t-1)) |
| `w45_bqx_stdev` | DOUBLE PRECISION | YES | STDEV(rate(t-45) to rate(t-1)) |
| `w45_bqx_endpoint` | DOUBLE PRECISION | YES | (rate(t-45) - rate(t)) / rate(t) |

#### Window 60 Minutes (6 Fields)

| Column | Type | Nullable | Formula |
|--------|------|----------|---------|
| `w60_bqx_return` | DOUBLE PRECISION | YES | Σ(i=1 to 60)[rate(t-i) - rate(t)] / rate(t) |
| `w60_bqx_max` | DOUBLE PRECISION | YES | MAX(rate(t-60) to rate(t-1)) |
| `w60_bqx_min` | DOUBLE PRECISION | YES | MIN(rate(t-60) to rate(t-1)) |
| `w60_bqx_avg` | DOUBLE PRECISION | YES | AVG(rate(t-60) to rate(t-1)) |
| `w60_bqx_stdev` | DOUBLE PRECISION | YES | STDEV(rate(t-60) to rate(t-1)) |
| `w60_bqx_endpoint` | DOUBLE PRECISION | YES | (rate(t-60) - rate(t)) / rate(t) |

#### Window 75 Minutes (6 Fields)

| Column | Type | Nullable | Formula |
|--------|------|----------|---------|
| `w75_bqx_return` | DOUBLE PRECISION | YES | Σ(i=1 to 75)[rate(t-i) - rate(t)] / rate(t) |
| `w75_bqx_max` | DOUBLE PRECISION | YES | MAX(rate(t-75) to rate(t-1)) |
| `w75_bqx_min` | DOUBLE PRECISION | YES | MIN(rate(t-75) to rate(t-1)) |
| `w75_bqx_avg` | DOUBLE PRECISION | YES | AVG(rate(t-75) to rate(t-1)) |
| `w75_bqx_stdev` | DOUBLE PRECISION | YES | STDEV(rate(t-75) to rate(t-1)) |
| `w75_bqx_endpoint` | DOUBLE PRECISION | YES | (rate(t-75) - rate(t)) / rate(t) |

#### Aggregate Fields (7)

| Column | Type | Nullable | Formula |
|--------|------|----------|---------|
| `agg_bqx_return` | DOUBLE PRECISION | YES | w75_bqx_return (aggregate uses longest window) |
| `agg_bqx_max` | DOUBLE PRECISION | YES | MAX across all windows |
| `agg_bqx_min` | DOUBLE PRECISION | YES | MIN across all windows |
| `agg_bqx_avg` | DOUBLE PRECISION | YES | AVG across all windows |
| `agg_bqx_stdev` | DOUBLE PRECISION | YES | STDEV across all windows |
| `agg_bqx_range` | DOUBLE PRECISION | YES | agg_bqx_max - agg_bqx_min |
| `agg_bqx_volatility` | DOUBLE PRECISION | YES | agg_bqx_stdev / agg_bqx_avg (normalized) |

---

## Field Breakdown Summary

```
Total Fields: 40
├─ Core: 3 (ts_utc, rate, created_at)
├─ Window Metrics: 30 (5 windows × 6 metrics)
│   ├─ w15: 6 fields (return, max, min, avg, stdev, endpoint)
│   ├─ w30: 6 fields
│   ├─ w45: 6 fields
│   ├─ w60: 6 fields
│   └─ w75: 6 fields
└─ Aggregates: 7 (return, max, min, avg, stdev, range, volatility)
```

---

## Partition Structure

### Monthly Partitions (12 per Pair)

Each BQX table is partitioned by `ts_utc` using range partitioning:

| Partition Suffix | Date Range | Example Table |
|------------------|------------|---------------|
| `_2024m07` | 2024-07-01 to 2024-08-01 | bqx_eurusd_2024m07 |
| `_2024m08` | 2024-08-01 to 2024-09-01 | bqx_eurusd_2024m08 |
| `_2024m09` | 2024-09-01 to 2024-10-01 | bqx_eurusd_2024m09 |
| `_2024m10` | 2024-10-01 to 2024-11-01 | bqx_eurusd_2024m10 |
| `_2024m11` | 2024-11-01 to 2024-12-01 | bqx_eurusd_2024m11 |
| `_2024m12` | 2024-12-01 to 2025-01-01 | bqx_eurusd_2024m12 |
| `_2025m01` | 2025-01-01 to 2025-02-01 | bqx_eurusd_2025m01 |
| `_2025m02` | 2025-02-01 to 2025-03-01 | bqx_eurusd_2025m02 |
| `_2025m03` | 2025-03-01 to 2025-04-01 | bqx_eurusd_2025m03 |
| `_2025m04` | 2025-04-01 to 2025-05-01 | bqx_eurusd_2025m04 |
| `_2025m05` | 2025-05-01 to 2025-06-01 | bqx_eurusd_2025m05 |
| `_2025m06` | 2025-06-01 to 2025-07-01 | bqx_eurusd_2025m06 |

**Total Partitions**: 28 pairs × 12 months = **336 partitions**

---

## Index Structure

Each parent BQX table has a single index on `ts_utc`:

```sql
CREATE INDEX idx_bqx_{pair}_ts ON bqx.bqx_{pair} (ts_utc);
```

**Purpose**: Optimize time-based queries (most common access pattern)

---

## Storage Estimates

### Empty Tables (Current State)

```
Parent Tables: 28 × ~8 KB = 224 KB
Partitions:    336 × 0 bytes = 0 bytes (empty)
Indexes:       28 × ~8 KB = 224 KB
Total:         ~450 KB (metadata only)
```

### Populated Tables (Projected)

**Assumptions**:
- Time range: 12 months (2024-07 through 2025-06)
- Data granularity: 1-minute bars
- Row count per pair: ~525,600 rows (12 months × 30 days × 1440 min/day)
- Row size: ~320 bytes (40 fields × 8 bytes per DOUBLE PRECISION)

**Per Pair**:
```
525,600 rows × 320 bytes = ~168 MB per pair
```

**All 28 Pairs**:
```
168 MB × 28 pairs = ~4.7 GB
```

**With Indexes** (~30% overhead):
```
4.7 GB × 1.3 = ~6.1 GB total
```

**Database Impact**:
- Current Aurora storage: 2.461 TB
- BQX addition: 6.1 GB
- Percentage: 0.24% increase

---

## Edge Effects (NULL Values)

### First 75 Minutes of Data

BQX tables compute backward-looking metrics. The first rows in the dataset will have NULLs:

| Timestamp | w15_bqx_return | w30_bqx_return | w45_bqx_return | w60_bqx_return | w75_bqx_return |
|-----------|----------------|----------------|----------------|----------------|----------------|
| t=0       | NULL           | NULL           | NULL           | NULL           | NULL           |
| t=1       | NULL           | NULL           | NULL           | NULL           | NULL           |
| ...       | ...            | ...            | ...            | ...            | ...            |
| t=14      | NULL           | NULL           | NULL           | NULL           | NULL           |
| t=15      | ✅ Value       | NULL           | NULL           | NULL           | NULL           |
| t=30      | ✅ Value       | ✅ Value       | NULL           | NULL           | NULL           |
| t=45      | ✅ Value       | ✅ Value       | ✅ Value       | NULL           | NULL           |
| t=60      | ✅ Value       | ✅ Value       | ✅ Value       | ✅ Value       | NULL           |
| t=75+     | ✅ Value       | ✅ Value       | ✅ Value       | ✅ Value       | ✅ Value       |

**Reason**: Insufficient historical data to compute backward metrics.

---

## Formula Reference

### Core BQX Formula

```
w{W}_bqx_return = Σ(i=1 to W)[rate(t-i) - rate(t)] / rate(t)
```

**Where**:
- `W` = window size (15, 30, 45, 60, or 75 minutes)
- `rate(t)` = current exchange rate at time t
- `rate(t-i)` = historical rate i minutes ago
- `i` = 1, 2, 3, ..., W

### Sign Convention

| Scenario | BQX Return | Interpretation |
|----------|------------|----------------|
| Price declining over past W min | **Positive** | rate(t-i) > rate(t) → sum is positive |
| Price increasing over past W min | **Negative** | rate(t-i) < rate(t) → sum is negative |
| Price stable | ~0 | rate(t-i) ≈ rate(t) |

**Example**:
```
If EUR/USD rose from 1.0800 to 1.0900 over 60 min:
  w60_bqx_return = Σ[(1.08xx - 1.0900)] / 1.0900
                 = (negative sum) / 1.0900
                 = negative value (upward momentum)
```

---

## Comparison to FWD Tables (Deleted)

### Structural Similarities

| Aspect | FWD (Deleted) | BQX (Created) |
|--------|---------------|---------------|
| Parent Tables | 28 | 28 |
| Partitioning | Monthly (RANGE) | Monthly (RANGE) |
| Metrics per Window | 6 | 6 |
| Aggregate Fields | 7 | 7 |
| Primary Key | ts_utc | ts_utc |
| Index | ts_utc | ts_utc |

### Key Differences

| Aspect | FWD (Deleted) | BQX (Created) |
|--------|---------------|---------------|
| **Direction** | Forward-looking | Backward-looking |
| **Formula** | rate(t) - rate(t+i) | rate(t-i) - rate(t) |
| **Windows** | 60, 90, 150, 240, 390, 630 min | 15, 30, 45, 60, 75 min |
| **Window Count** | 6 | 5 |
| **Total Fields** | 46 | 40 |
| **Granularity** | Coarse (30-240 min gaps) | Fine (15 min increments) |
| **Focus** | Medium to long-term | Ultra-short to short-term |
| **Edge NULLs** | End of dataset | Start of dataset |
| **ML Role** | Targets (Y) | Features (X) |
| **Real-Time** | ❌ Needs future data | ✅ Uses past data only |

---

## Database Current State

### Table Counts (Post-BQX Creation)

```
M1 Tables:  28 parent + 336 partitions ✅
REG Tables: 28 parent + 336 partitions ✅
BQX Tables: 28 parent + 336 partitions ✅ (NEW, empty)
FWD Tables: 0 (deleted 2025-11-09) ❌
MV Tables:  0 (CASCADE deleted with FWD) ⚠️
```

**Total Active Tables**: 84 parent + 1,008 partitions = **1,092 tables**

---

## Usage Examples

### Query Recent Momentum

```sql
-- Get most recent backward momentum for EUR/USD
SELECT
    ts_utc,
    rate,
    w15_bqx_return as momentum_15m,
    w30_bqx_return as momentum_30m,
    w60_bqx_return as momentum_60m,
    w75_bqx_return as momentum_75m
FROM bqx.bqx_eurusd
WHERE ts_utc >= NOW() - INTERVAL '1 hour'
ORDER BY ts_utc DESC
LIMIT 10;
```

### Feature Extraction for ML

```sql
-- Extract BQX features for model training
SELECT
    ts_utc,
    -- Current momentum features
    w15_bqx_return,
    w30_bqx_return,
    w60_bqx_return,

    -- Volatility features
    w15_bqx_stdev,
    w60_bqx_stdev,

    -- Aggregate features
    agg_bqx_volatility,
    agg_bqx_range
FROM bqx.bqx_eurusd
WHERE ts_utc BETWEEN '2024-07-01' AND '2024-12-31'
  AND w75_bqx_return IS NOT NULL  -- Exclude edge effect rows
ORDER BY ts_utc;
```

### Multi-Timeframe Alignment

```sql
-- Check momentum alignment across timeframes
SELECT
    ts_utc,
    rate,
    CASE
        WHEN w15_bqx_return > 0 THEN 'DOWN'
        WHEN w15_bqx_return < 0 THEN 'UP'
        ELSE 'FLAT'
    END as trend_15m,
    CASE
        WHEN w60_bqx_return > 0 THEN 'DOWN'
        WHEN w60_bqx_return < 0 THEN 'UP'
        ELSE 'FLAT'
    END as trend_60m,
    -- Count aligned windows
    (SIGN(w15_bqx_return) + SIGN(w30_bqx_return) +
     SIGN(w45_bqx_return) + SIGN(w60_bqx_return) +
     SIGN(w75_bqx_return)) as alignment_score
FROM bqx.bqx_eurusd
WHERE ts_utc >= NOW() - INTERVAL '1 day'
ORDER BY ts_utc DESC;
```

---

## Next Steps

### Immediate (Required for Functionality)

1. **Create backward_worker.py**
   - Mirror structure of forward_worker.py
   - Implement reversed formula: `Σ[rate(t-i) - rate(t)] / rate(t)`
   - Process M1 data to populate BQX tables

2. **Populate Historical Data**
   - Process all M1 data from 2024-07 through 2025-06
   - Expected output: ~525,600 rows per pair
   - Estimated runtime: 4-6 hours (parallel processing)

3. **Verify Data Integrity**
   - Check for NULL patterns (first 75 min of each partition)
   - Validate formula correctness against sample calculations
   - Compare storage usage to projections

### Short-Term (ML Pipeline)

4. **Update Feature Extraction**
   - Modify ML pipeline to use BQX instead of FWD
   - Implement autoregressive features (BQX_t → BQX_{t+60})
   - Test with small dataset

5. **Recreate Materialized Views**
   - Design new MV schema: M1 + REG + BQX (no FWD)
   - Create 28 mv_{pair}_merged tables
   - Populate with existing data

### Medium-Term (Production)

6. **Real-Time Data Pipeline**
   - Update ingestion to compute BQX metrics in real-time
   - Add monitoring for BQX table population lag
   - Implement alerting for anomalies

7. **Documentation Updates**
   - Update README with BQX architecture
   - Document BQX-based ML strategy
   - Create data dictionary

---

## Verification Results (2025-11-09)

### Query Results

**BQX Table Counts**:
```
BQX Parent Tables:  28 ✅
BQX Partitions:     336 ✅
BQX Indexes:        28 ✅
```

**Column Verification**:
```
All 28 tables have exactly 40 columns ✅
```

**Partition Distribution**:
```
All 28 pairs have exactly 12 partitions each ✅
```

**Sample Row Counts**:
```
bqx_eurusd: 0 rows ✅ (expected - just created)
bqx_gbpusd: 0 rows ✅
bqx_usdjpy: 0 rows ✅
```

**Schema Validation** (bqx_eurusd sample):
```
✅ ts_utc (TIMESTAMPTZ, NOT NULL, PK)
✅ rate (DOUBLE PRECISION, NOT NULL)
✅ w15_bqx_return through w75_bqx_endpoint (30 fields)
✅ agg_bqx_return through agg_bqx_volatility (7 fields)
✅ created_at (TIMESTAMPTZ, NOT NULL, DEFAULT now())
```

---

## Related Documentation

- **Design Analysis**: [BQX-TABLE-REQUEST-ANALYSIS.md](BQX-TABLE-REQUEST-ANALYSIS.md)
- **Formula Comparison**: [BQX-VS-FWD-COMPARISON.md](BQX-VS-FWD-COMPARISON.md)
- **ML Strategy**: [BQX-ML-STRATEGY-SUMMARY.md](BQX-ML-STRATEGY-SUMMARY.md)
- **DDL Script**: [create_all_bqx_tables.sql](create_all_bqx_tables.sql)
- **FWD Deletion**: [FWD-DELETION-COMPLETE.md](FWD-DELETION-COMPLETE.md)

---

## Conclusion

BQX table creation is **100% complete and verified**. All 28 tables with 336 partitions and proper schema are ready for data population. The backward-looking momentum metrics will provide critical features for the new autoregressive ML strategy, filling the gap between ultra-short-term M1 data and medium-term REG patterns.

**Status**: ✅ READY FOR DATA POPULATION

---

**Document Version**: 1.0
**Last Updated**: 2025-11-09
**Author**: Claude Code (RM-001)
