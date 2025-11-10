# Materialized View Field Specification

**Strategy:** Currency-Filtered Feature Selection
**Created:** 2025-11-09
**Total MVs:** 28 (one per target pair)

---

## Overview

Each materialized view contains **482 fields** organized into 3 categories:

1. **Timestamp** (1 field)
2. **Target Pair Features** (37 fields with `target_` prefix)
3. **Feature Pair Fields** (12 pairs × 37 features = 444 fields)

**Total:** 1 + 37 + 444 = **482 fields per MV**

---

## Field Categories

### 1. Timestamp (1 field)

| Field | Type | Description |
|-------|------|-------------|
| `ts_utc` | TIMESTAMPTZ | UTC timestamp for the observation |

**Purpose:** Primary key for time-series alignment across all pairs

---

### 2. Target Pair Features (37 fields)

These are the BQX backward-looking metrics for the **target pair** (the pair we're trying to predict).

**Naming Convention:** `target_{feature_name}`

#### Feature Groups:

**A. Current Rate (1 field)**
- `target_rate` - Current exchange rate

**B. Window Features (30 fields = 5 windows × 6 metrics)**

For each window size (15, 30, 45, 60, 75 minutes):
- `target_w{W}_bqx_return` - Cumulative backward return
- `target_w{W}_bqx_max` - Maximum rate in lookback window
- `target_w{W}_bqx_min` - Minimum rate in lookback window
- `target_w{W}_bqx_avg` - Average rate in lookback window
- `target_w{W}_bqx_stdev` - Standard deviation in window
- `target_w{W}_bqx_endpoint` - Return from window start to current

**C. Aggregate Features (7 fields)**

Based on 75-minute window:
- `target_agg_bqx_return` - Aggregate cumulative return
- `target_agg_bqx_max` - Aggregate maximum
- `target_agg_bqx_min` - Aggregate minimum
- `target_agg_bqx_avg` - Aggregate average
- `target_agg_bqx_stdev` - Aggregate standard deviation
- `target_agg_bqx_range` - Aggregate range (max - min)
- `target_agg_bqx_volatility` - Aggregate volatility

**Total Target Features:** 37

---

### 3. Feature Pair Fields (444 fields)

These are BQX metrics from **related pairs** that share a currency with the target.

**Naming Convention:** `{pair}_{feature_name}`

#### Currency-Filtering Logic

For target pair `eurusd`:
- **Base currency:** `eur`
- **Quote currency:** `usd`
- **Included pairs:** All pairs containing `eur` OR `usd`

**Example for EURUSD:**
- EUR-pairs: EURAUD, EURCAD, EURCHF, EURGBP, EURJPY, EURNZD, EURUSD
- USD-pairs: AUDUSD, EURUSD, GBPUSD, NZDUSD, USDCAD, USDCHF, USDJPY
- **Unique pairs:** 13 (EURUSD counted once)
- **Feature pairs:** 12 (excluding target EURUSD)

#### Feature Structure per Pair

Each feature pair contributes **37 fields**:

```
{pair}_rate                     # Current rate
{pair}_w15_bqx_return          # 15-min window return
{pair}_w15_bqx_max             # 15-min max
{pair}_w15_bqx_min             # 15-min min
{pair}_w15_bqx_avg             # 15-min average
{pair}_w15_bqx_stdev           # 15-min std dev
{pair}_w15_bqx_endpoint        # 15-min endpoint return
{pair}_w30_bqx_return          # 30-min window return
... (6 metrics per window)
{pair}_w45_bqx_return
{pair}_w60_bqx_return
{pair}_w75_bqx_return
... (5 windows × 6 metrics = 30 fields)
{pair}_agg_bqx_return          # Aggregate return
{pair}_agg_bqx_max             # Aggregate max
{pair}_agg_bqx_min             # Aggregate min
{pair}_agg_bqx_avg             # Aggregate average
{pair}_agg_bqx_stdev           # Aggregate std dev
{pair}_agg_bqx_range           # Aggregate range
{pair}_agg_bqx_volatility      # Aggregate volatility
```

---

## Complete Field List - EURUSD Example

### Timestamp (1 field)
```
1. ts_utc
```

### Target Features (37 fields)
```
2. target_rate
3. target_w15_bqx_return
4. target_w15_bqx_max
5. target_w15_bqx_min
6. target_w15_bqx_avg
7. target_w15_bqx_stdev
8. target_w15_bqx_endpoint
... (continues for w30, w45, w60, w75)
32. target_agg_bqx_return
33. target_agg_bqx_max
34. target_agg_bqx_min
35. target_agg_bqx_avg
36. target_agg_bqx_stdev
37. target_agg_bqx_range
38. target_agg_bqx_volatility
```

### Feature Pair: AUDUSD (37 fields)
```
39. audusd_rate
40. audusd_w15_bqx_return
41. audusd_w15_bqx_max
... (37 fields total)
```

### Feature Pair: EURAUD (37 fields)
```
76. euraud_rate
77. euraud_w15_bqx_return
78. euraud_w15_bqx_max
... (37 fields total)
```

### Remaining 10 Feature Pairs
```
EURCAD (37 fields)
EURCHF (37 fields)
EURGBP (37 fields)
EURJPY (37 fields)
EURNZD (37 fields)
GBPUSD (37 fields)
NZDUSD (37 fields)
USDCAD (37 fields)
USDCHF (37 fields)
USDJPY (37 fields)
```

**Total:** 482 fields

---

## Field Counts by Target Pair

| Target | Relevant Pairs | Total Fields | Feature Pairs |
|--------|----------------|--------------|---------------|
| EURUSD | 13 | 482 | 12 |
| GBPUSD | 13 | 482 | 12 |
| USDJPY | 13 | 482 | 12 |
| AUDCAD | 13 | 482 | 12 |
| GBPJPY | 13 | 482 | 12 |
| ... | ... | ... | ... |

**All 28 targets:** 482 fields each (consistently)

---

## Rationale for Currency-Filtering

### Financial Logic
1. **EUR strength** affects all EUR* pairs
2. **USD strength** affects all *USD pairs
3. **EURUSD** = f(EUR_strength, USD_strength)
4. Non-related pairs (e.g., GBPJPY for EURUSD) provide minimal predictive signal

### ML Benefits
1. **53% dimensionality reduction** (482 vs 1,036 fields for all-pairs approach)
2. **Higher signal-to-noise ratio**
3. **Reduced overfitting risk**
4. **Faster training**
5. **Better interpretability**

---

## Data Types

| Field Pattern | PostgreSQL Type | NumPy/Pandas Type |
|---------------|----------------|-------------------|
| `ts_utc` | TIMESTAMPTZ | datetime64[ns, UTC] |
| `*_rate` | DOUBLE PRECISION | float64 |
| `*_bqx_*` | DOUBLE PRECISION | float64 |
| `*_agg_*` | DOUBLE PRECISION | float64 |

---

## NULL Handling

### Expected NULLs
- **Edge cases:** First 75 minutes of data have NULLs for w75 metrics (insufficient lookback)
- **Missing data:** If a feature pair has no data for a timestamp, its fields will be NULL

### Filtering Strategy
```sql
WHERE target.w75_bqx_return IS NOT NULL
```

This ensures we only include rows with complete lookback data for the target pair.

**Impact:**
- Removes ~75 rows at start of each partition
- Typical partition: ~32,600 rows → ~32,525 rows after filtering

---

## Storage Estimates

### Per Row
- **Fields:** 482
- **Numeric fields:** 481 (all except timestamp)
- **Storage:** ~3.8 KB per row (8 bytes per DOUBLE PRECISION × 481)

### Per MV (1 year of data)
- **Rows per pair:** ~370,000 (approximate)
- **Storage per MV:** 370,000 × 3.8 KB = ~1.4 GB
- **Total for 28 MVs:** ~39 GB

### With Indexes
- **Timestamp index:** ~10-20 MB per MV
- **Total with indexes:** ~40 GB

---

## Query Performance

### Index Strategy
```sql
CREATE INDEX idx_features_{pair}_ts ON bqx_ml.features_{pair}(ts_utc);
```

**Benefits:**
- Fast time-range queries
- Efficient JOIN operations
- Quick ORDER BY ts_utc

### Expected Query Times
| Query Type | Rows | Expected Time |
|------------|------|---------------|
| Single day | ~1,440 | <10ms |
| Single month | ~30,000 | <100ms |
| Full year | ~370,000 | <1s |

---

## Usage Examples

### Training Data Extraction
```sql
SELECT *
FROM bqx_ml.features_eurusd
WHERE ts_utc >= '2024-07-01' AND ts_utc < '2024-12-31'
ORDER BY ts_utc;
```

### Feature Selection
```sql
-- Get subset of features for lightweight model
SELECT
    ts_utc,
    target_rate,
    target_w75_bqx_return,
    target_agg_bqx_volatility,
    euraud_w75_bqx_return,
    gbpusd_w75_bqx_return,
    usdjpy_w75_bqx_return
FROM bqx_ml.features_eurusd
WHERE ts_utc >= '2024-07-01';
```

### Time-Series Split
```sql
-- Train/validation/test split
-- Train: Jul-Oct (4 months)
-- Validation: Nov-Dec (2 months)
-- Test: Jan-Jun (6 months)

-- Training set
SELECT * FROM bqx_ml.features_eurusd
WHERE ts_utc >= '2024-07-01' AND ts_utc < '2024-11-01';

-- Validation set
SELECT * FROM bqx_ml.features_eurusd
WHERE ts_utc >= '2024-11-01' AND ts_utc < '2025-01-01';

-- Test set
SELECT * FROM bqx_ml.features_eurusd
WHERE ts_utc >= '2025-01-01' AND ts_utc < '2025-07-01';
```

---

## Next Steps

1. **Create MVs:** Run `create_filtered_feature_mvs.py`
2. **Verify:** Check row counts and field structure
3. **Extract:** Export to Parquet/CSV for ML training
4. **Train:** Use in PyTorch/TensorFlow pipelines

---

## Maintenance

### Refresh MVs (when new BQX data added)
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY bqx_ml.features_eurusd;
```

### Rebuild MV (if structure changes)
```sql
DROP MATERIALIZED VIEW IF EXISTS bqx_ml.features_eurusd CASCADE;
-- Re-run create_filtered_feature_mvs.py
```

### Monitor Size
```sql
SELECT
    schemaname,
    matviewname,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) as size
FROM pg_matviews
WHERE schemaname = 'bqx_ml'
ORDER BY pg_total_relation_size(schemaname||'.'||matviewname) DESC;
```

---

**Created:** 2025-11-09
**Strategy:** Currency-filtered feature selection
**Status:** Specification complete, ready for implementation
