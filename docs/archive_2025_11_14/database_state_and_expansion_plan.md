# BQX Aurora Database State and Expansion Plan

**Date:** 2025-11-12
**Database:** BQX (trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com)
**Version:** PostgreSQL Aurora
**Purpose:** Complete database audit and expansion roadmap for dual-architecture ML feature system

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Database State](#current-state)
3. [Dual Architecture Overview](#dual-architecture)
4. [Schema Migration Plan](#schema-migration)
5. [New Table Requirements](#new-tables)
6. [Partitioning Strategy](#partitioning)
7. [Index Requirements](#indexes)
8. [Storage Estimates](#storage)
9. [Advanced Features Expansion](#advanced-features)
10. [Implementation Timeline](#timeline)
11. [SQL Examples](#sql-examples)

---

<a name="executive-summary"></a>
## Executive Summary

### Current State
- **Total Tables:** 6,596 tables in `bqx` schema
- **Total Database Size:** 61 GB
- **Currency Pairs:** 28 forex pairs
- **Time Range:** M1 data from 2020-01 through 2025-10 (5+ years)
- **Feature Coverage:** 8 feature types partially implemented

### Critical Findings
1. **Naming Inconsistency:** Existing rate-based feature tables need renaming to `*_idx_*` convention
2. **Missing BQX Features:** BQX-domain versions of all features need to be created
3. **Empty Tables:** Correlation features tables exist but are empty (0 rows)
4. **Partitioning Working Well:** Monthly partitioning strategy functioning correctly
5. **Index Coverage:** All tables have primary keys on `ts_utc`, but missing secondary indexes

### Expansion Requirements
- **Tables to Rename:** ~1,820 existing tables (7 feature types × ~260 avg partitions)
- **New Tables to Create:** ~2,016 tables (6 BQX feature types × 336 partitions)
- **Advanced Features:** 4 new feature categories (cointegration, realized volatility, HMM regime, cross-sectional)
- **Storage Impact:** +50-60 GB expected
- **Timeline:** 25-30 hours with parallel execution

---

<a name="current-state"></a>
## Current Database State

### 2.1 Database Overview

```sql
-- Connection Details
Host: trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com
Port: 5432
Database: bqx
User: postgres
Schema: bqx

-- Summary Statistics
Total Tables: 6,596
Total Size: 61 GB
Currency Pairs: 28
```

### 2.2 Table Inventory by Category

| Category | Table Count | Total Size | Status | Notes |
|----------|-------------|------------|--------|-------|
| **M1 Rates** | 2,000 | 28 GB | ✅ Complete | OHLCV data 2020-2025, 72 partitions/pair |
| **BQX Features** | 868 | 3.6 GB | ✅ Complete | Backward momentum indices, 31 partitions/pair |
| **Technical Features** | 364 | 4.5 GB | ✅ Populated | 47 indicators, needs rename to `technical_idx_*` |
| **Bollinger Features** | 364 | 1.2 GB | ✅ Populated | 6 features, needs rename to `bollinger_idx_*` |
| **Fibonacci Features** | 364 | 1.8 GB | ✅ Populated | 12 features, needs rename to `fibonacci_idx_*` |
| **Statistics Features** | 364 | 1.2 GB | ✅ Populated | 5 features, needs rename to `statistics_idx_*` |
| **Spread Features** | 364 | 3.5 GB | ✅ Populated | 20 features, needs rename to `spread_idx_*` |
| **Time Features** | 364 | 1.8 GB | ✅ Populated | 8 features, needs rename to `time_idx_*` |
| **Volume Features** | 364 | 1.4 GB | ✅ Populated | 11 features, needs rename to `volume_idx_*` |
| **Correlation Features** | 364 | 2.7 MB | ⚠️ Empty | 0 rows, needs population |
| **ML Features** | 54 | 2.6 GB | ✅ Populated | JSONB format, legacy structure |
| **ML Correlation** | 46 | 368 KB | ⚠️ Partial | Historical data only |
| **Other** | 716 | 12 GB | ℹ️ Legacy | Old correlation, vwap, momentum tables |

### 2.3 Currency Pairs Covered

```
28 Forex Pairs (All Majors + Crosses):
AUDCAD, AUDCHF, AUDJPY, AUDNZD, AUDUSD
CADCHF, CADJPY, CHFJPY
EURAUD, EURCAD, EURCHF, EURGBP, EURJPY, EURNZD, EURUSD
GBPAUD, GBPCAD, GBPCHF, GBPJPY, GBPNZD, GBPUSD
NZDCAD, NZDCHF, NZDJPY, NZDUSD
USDCAD, USDCHF, USDJPY
```

### 2.4 Detailed Schema Analysis

#### 2.4.1 M1 Rate Tables (`m1_{pair}`)

**Structure:** Partitioned by time (monthly, `y{YYYY}m{MM}` format)

```sql
-- Schema (m1_eurusd example)
Column          | Type                        | Notes
----------------|----------------------------|----------------------------------
time            | timestamp without time zone | PRIMARY KEY, partition key
open            | numeric(10,5)               | OHLC prices
high            | numeric(10,5)               |
low             | numeric(10,5)               |
close           | numeric(10,5)               |
volume          | integer                     |
bid_open        | numeric(10,5)               | Bid prices
bid_high        | numeric(10,5)               |
bid_low         | numeric(10,5)               |
bid_close       | numeric(10,5)               |
ask_open        | numeric(10,5)               | Ask prices
ask_high        | numeric(10,5)               |
ask_low         | numeric(10,5)               |
ask_close       | numeric(10,5)               |
spread_open     | numeric(10,5)               | Spread metrics
spread_high     | numeric(10,5)               |
spread_low      | numeric(10,5)               |
spread_close    | numeric(10,5)               |
created_at      | timestamp without time zone |
rate            | numeric(10,5)               | Mid-price
rate_index      | numeric                     | Base-100 normalized (CRITICAL!)
high_index      | double precision            | Normalized OHLC
low_index       | double precision            |
open_index      | double precision            |

-- Partitioning
Partition Key: RANGE(time)
Partitions per Pair: 60-72 (2020-01 to 2025-10)
Total Partitions: ~2,000

-- Data Completeness (EURUSD example)
Earliest: 2020-01-01 22:00:00+00
Latest:   2025-10-27 20:58:00+00
Rows:     2,138,799

-- Indexes
PRIMARY KEY: time (unique, btree)
INDEX: rate_index (btree)
```

#### 2.4.2 BQX Feature Tables (`bqx_{pair}`)

**Structure:** Backward momentum indices for 5 windows

```sql
-- Schema (bqx_eurusd example)
Column               | Type                     | Notes
---------------------|--------------------------|---------------------------
ts_utc               | timestamptz              | PRIMARY KEY, partition key
rate_index           | double precision         | Current rate index
w15_bqx_return       | double precision         | 15-min backward momentum
w15_bqx_max_index    | double precision         | Stats for w15 window
w15_bqx_min_index    | double precision         |
w15_bqx_avg_index    | double precision         |
w15_bqx_stdev_index  | double precision         |
w15_bqx_endpoint     | double precision         |
w30_bqx_return       | double precision         | 30-min backward momentum
w30_bqx_max_index    | double precision         | Stats for w30 window
w30_bqx_min_index    | double precision         |
w30_bqx_avg_index    | double precision         |
w30_bqx_stdev_index  | double precision         |
w30_bqx_endpoint     | double precision         |
w45_bqx_return       | double precision         | 45-min backward momentum
w45_bqx_max_index    | double precision         |
w45_bqx_min_index    | double precision         |
w45_bqx_avg_index    | double precision         |
w45_bqx_stdev_index  | double precision         |
w45_bqx_endpoint     | double precision         |
w60_bqx_return       | double precision         | 60-min backward momentum
w60_bqx_max_index    | double precision         |
w60_bqx_min_index    | double precision         |
w60_bqx_avg_index    | double precision         |
w60_bqx_stdev_index  | double precision         |
w60_bqx_endpoint     | double precision         |
w75_bqx_return       | double precision         | 75-min backward momentum
w75_bqx_max_index    | double precision         |
w75_bqx_min_index    | double precision         |
w75_bqx_avg_index    | double precision         |
w75_bqx_stdev_index  | double precision         |
w75_bqx_endpoint     | double precision         |
agg_bqx_return       | double precision         | Aggregate metrics
agg_bqx_max_index    | double precision         |
agg_bqx_min_index    | double precision         |
agg_bqx_avg_index    | double precision         |
agg_bqx_stdev_index  | double precision         |
agg_bqx_range        | double precision         |
agg_bqx_volatility   | double precision         |

-- Partitioning
Partition Key: RANGE(ts_utc)
Partitions per Pair: 30 (2024-07 to 2026-12)
Total Partitions: 868 (28 pairs × 31 months)

-- Data Completeness (EURUSD example)
Earliest: 2024-07-01 00:00:00+00
Latest:   2025-06-30 23:59:00+00
Rows:     370,075

-- Indexes
PRIMARY KEY: ts_utc (btree)
```

#### 2.4.3 Technical Features Tables (`technical_features_{pair}`)

**Note:** Currently named `technical_features_*`, will be renamed to `technical_idx_*`

```sql
-- Schema (technical_features_eurusd example - 47 columns)
Column                   | Type         | Description
-------------------------|--------------|----------------------------------
ts_utc                   | timestamptz  | PRIMARY KEY, partition key
ema_10                   | float8       | Exponential Moving Average (10)
ema_20                   | float8       | Exponential Moving Average (20)
ema_50                   | float8       | Exponential Moving Average (50)
ema_100                  | float8       | Exponential Moving Average (100)
ema_200                  | float8       | Exponential Moving Average (200)
sma_10                   | float8       | Simple Moving Average (10)
sma_20                   | float8       | Simple Moving Average (20)
sma_50                   | float8       | Simple Moving Average (50)
sma_100                  | float8       | Simple Moving Average (100)
sma_200                  | float8       | Simple Moving Average (200)
rsi_14                   | float8       | Relative Strength Index (14)
macd                     | float8       | MACD line
macd_signal              | float8       | MACD signal line
macd_histogram           | float8       | MACD histogram
stoch_k                  | float8       | Stochastic %K
stoch_d                  | float8       | Stochastic %D
cci_20                   | float8       | Commodity Channel Index (20)
williams_r_14            | float8       | Williams %R (14)
roc_12                   | float8       | Rate of Change (12)
momentum_10              | float8       | Momentum (10)
momentum_20              | float8       | Momentum (20)
trix                     | float8       | TRIX indicator
ultimate_oscillator      | float8       | Ultimate Oscillator
awesome_oscillator       | float8       | Awesome Oscillator
keltner_channel_upper    | float8       | Keltner Channel Upper
keltner_channel_lower    | float8       | Keltner Channel Lower
atr_14                   | float8       | Average True Range (14)
historical_volatility_20 | float8       | Historical Volatility (20)
chaikin_volatility       | float8       | Chaikin Volatility
donchian_channel_upper   | float8       | Donchian Channel Upper
donchian_channel_middle  | float8       | Donchian Channel Middle
donchian_channel_lower   | float8       | Donchian Channel Lower
mass_index               | float8       | Mass Index
vortex_indicator_plus    | float8       | Vortex Indicator +
vortex_indicator_minus   | float8       | Vortex Indicator -
ulcer_index              | float8       | Ulcer Index
obv                      | float8       | On-Balance Volume
adl                      | float8       | Accumulation/Distribution Line
cmf_20                   | float8       | Chaikin Money Flow (20)
fi_13                    | float8       | Force Index (13)
eom_14                   | float8       | Ease of Movement (14)
vpt                      | float8       | Volume Price Trend
nvi                      | float8       | Negative Volume Index
pvi                      | float8       | Positive Volume Index
mfi_14                   | float8       | Money Flow Index (14)
vwap                     | float8       | Volume Weighted Average Price

-- Partitioning
Partition Key: RANGE(ts_utc)
Partitions per Pair: 12 (2024-07 to 2025-06)
Total Partitions: 364 (28 pairs × 13 months)

-- Data Completeness (EURUSD example)
Earliest: 2024-07-01 03:19:00+00
Latest:   2025-06-30 23:59:00+00
Rows:     367,776

-- Sample Data
ts_utc               | ema_10  | rsi_14 | macd      | atr_14
---------------------|---------|--------|-----------|--------
2024-07-01 03:19:00 | 1.07553 | 66.67  | 0.000106  | 0.000069

-- Indexes
PRIMARY KEY: ts_utc (btree)
```

#### 2.4.4 Bollinger Features (`bollinger_features_{pair}`)

**Note:** Will be renamed to `bollinger_idx_*`

```sql
-- Schema (6 columns)
Column               | Type         | Description
---------------------|--------------|----------------------------------
ts_utc               | timestamptz  | PRIMARY KEY
bollinger_upper_20   | float8       | Upper band (20-period, 2σ)
bollinger_lower_20   | float8       | Lower band (20-period, 2σ)
bollinger_middle_20  | float8       | Middle band (20-period SMA)
bollinger_width_20   | float8       | Band width (upper - lower)
bollinger_percent_b  | float8       | %B (position within bands)

-- Partitioning
Partitions per Pair: 13 (2024-07 to 2025-06)
Total Partitions: 364

-- Data Completeness (EURUSD example)
Rows: 370,165 (complete coverage)
Storage per Partition: ~3.7 MB
```

#### 2.4.5 Correlation Features (`correlation_features_{pair}`)

**Status:** ⚠️ EMPTY - Tables exist but have 0 rows
**Action Required:** Populate with correlation_idx_worker.py

```sql
-- Schema (16 columns)
Column                           | Type         | Description
---------------------------------|--------------|---------------------------
ts_utc                           | timestamptz  | PRIMARY KEY
corr_base_pairs_15min            | float8       | Base pair correlation (15min)
corr_base_pairs_60min            | float8       | Base pair correlation (60min)
corr_quote_pairs_15min           | float8       | Quote pair correlation (15min)
corr_quote_pairs_60min           | float8       | Quote pair correlation (60min)
relative_strength_vs_base_pairs  | float8       | Relative strength metric
relative_strength_vs_quote_pairs | float8       | Relative strength metric
base_pair_divergence             | float8       | Divergence from base pairs
quote_pair_divergence            | float8       | Divergence from quote pairs
triangular_arb_divergence        | float8       | Triangular arbitrage metric
cross_pair_momentum_divergence   | int4         | Momentum divergence flag
correlation_stability            | float8       | Correlation stability metric
lead_lag_indicator               | float8       | Lead-lag relationship
cointegration_residual           | float8       | Cointegration residual
pair_spread_z_score              | float8       | Z-score of pair spread
cross_pair_volatility_ratio      | float8       | Volatility ratio

-- Current Status
Rows: 0 (EMPTY!)
Partitions: 364 (created but unpopulated)

-- To Be Renamed
correlation_features_{pair} → correlation_idx_{pair}
```

#### 2.4.6 Statistics Features (`statistics_features_{pair}`)

```sql
-- Schema (5 columns)
Column                          | Type         | Description
--------------------------------|--------------|---------------------------
ts_utc                          | timestamptz  | PRIMARY KEY
skewness_60min                  | float8       | 60-min skewness
kurtosis_60min                  | float8       | 60-min kurtosis
median_absolute_deviation_60min | float8       | 60-min MAD
entropy_60min                   | float8       | 60-min entropy
autocorrelation_lag1            | float8       | Lag-1 autocorrelation

-- Partitions: 364
-- Data: Complete (370,165 rows for EURUSD)
```

#### 2.4.7 Fibonacci Features (`fibonacci_features_{pair}`)

```sql
-- Schema (12 columns)
Column               | Type         | Description
---------------------|--------------|----------------------------------
ts_utc               | timestamptz  | PRIMARY KEY
fib_retracement_236  | float8       | 23.6% Fibonacci retracement
fib_retracement_382  | float8       | 38.2% Fibonacci retracement
fib_retracement_500  | float8       | 50.0% Fibonacci retracement
fib_retracement_618  | float8       | 61.8% Fibonacci retracement
fib_retracement_786  | float8       | 78.6% Fibonacci retracement
fib_extension_1618   | float8       | 161.8% Fibonacci extension
fib_extension_2618   | float8       | 261.8% Fibonacci extension
fib_extension_4236   | float8       | 423.6% Fibonacci extension
fib_fan_upper        | float8       | Fibonacci fan upper line
fib_fan_middle       | float8       | Fibonacci fan middle line
fib_fan_lower        | float8       | Fibonacci fan lower line
fib_arc_radius       | float8       | Fibonacci arc radius

-- Partitions: 364
-- Data: Nearly complete (367,285 rows for EURUSD)
```

#### 2.4.8 Spread Features (`spread_features_{pair}`)

```sql
-- Schema (20 columns)
Column                   | Type         | Description
-------------------------|--------------|----------------------------------
ts_utc                   | timestamptz  | PRIMARY KEY
spread_mean_60min        | float8       | 60-min mean spread
spread_volatility_60min  | float8       | 60-min spread volatility
spread_pct_of_rate       | float8       | Spread as % of rate
spread_trend_slope       | float8       | Spread trend slope
spread_spike             | int4         | Spread spike flag
bid_ask_imbalance        | float8       | Bid-ask imbalance
effective_spread         | float8       | Effective spread
quoted_spread            | float8       | Quoted spread
realized_spread          | float8       | Realized spread
price_impact             | float8       | Price impact estimate
roll_cost                | float8       | Roll cost
bid_depth                | float8       | Bid depth
ask_depth                | float8       | Ask depth
depth_imbalance          | float8       | Depth imbalance
spread_range_60min       | float8       | 60-min spread range
spread_percentile_60min  | float8       | 60-min spread percentile
mid_price_volatility     | float8       | Mid-price volatility
tick_direction           | int4         | Tick direction
tick_rule                | int4         | Tick rule classification
order_flow_toxicity      | float8       | Order flow toxicity

-- Partitions: 364
-- Data: Complete (370,165 rows for EURUSD)
```

#### 2.4.9 Time Features (`time_features_{pair}`)

```sql
-- Schema (8 columns)
Column                    | Type         | Description
--------------------------|--------------|----------------------------------
ts_utc                    | timestamptz  | PRIMARY KEY
hour_sin                  | float8       | Hour of day (sin encoding)
hour_cos                  | float8       | Hour of day (cos encoding)
day_of_week_sin           | float8       | Day of week (sin encoding)
day_of_week_cos           | float8       | Day of week (cos encoding)
session_overlap           | int4         | Trading session overlap count
is_weekend_approach       | int4         | Weekend approach flag
minutes_since_market_open | int4         | Minutes since session open
trading_session           | int4         | Trading session ID

-- Partitions: 364
-- Data: Complete (370,165 rows for EURUSD)
```

#### 2.4.10 Volume Features (`volume_features_{pair}`)

```sql
-- Schema (11 columns)
Column                         | Type         | Description
-------------------------------|--------------|---------------------------
ts_utc                         | timestamptz  | PRIMARY KEY
w15_volume_ratio               | float8       | 15-min volume ratio
w30_volume_ratio               | float8       | 30-min volume ratio
w60_volume_ratio               | float8       | 60-min volume ratio
volume_spike                   | int4         | Volume spike flag
volume_trend_slope             | float8       | Volume trend slope
cumulative_volume_60min        | int8         | 60-min cumulative volume
volume_weighted_return         | float8       | Volume-weighted return
volume_price_correlation_60min | float8       | 60-min vol-price correlation
relative_volume_position       | float8       | Relative volume position
volume_volatility_60min        | float8       | 60-min volume volatility

-- Partitions: 364
-- Data: Complete (370,165 rows for EURUSD)
```

### 2.5 Storage Analysis

#### Per-Partition Storage (EURUSD Example)

| Feature Type | Partition Size | Columns | Rows/Partition | Bytes/Row |
|--------------|----------------|---------|----------------|-----------|
| Bollinger    | 3.7 MB         | 6       | ~30,850        | ~126      |
| Correlation  | 0 bytes        | 16      | 0              | N/A       |
| Fibonacci    | ~150 MB        | 12      | ~30,600        | ~5,128    |
| Statistics   | ~100 MB        | 5       | ~30,850        | ~3,395    |
| Spread       | ~290 MB        | 20      | ~30,850        | ~9,850    |
| Technical    | ~370 MB        | 47      | ~30,650        | ~12,634   |
| Time         | ~150 MB        | 8       | ~30,850        | ~5,090    |
| Volume       | ~115 MB        | 11      | ~30,850        | ~3,903    |
| M1 Rates     | 15 MB          | 24      | ~30,000        | ~523      |
| BQX          | ~120 MB        | 39      | ~12,300        | ~10,211   |

**Total Storage per Pair per Month:** ~1.3 GB (all features + M1 data)

---

<a name="dual-architecture"></a>
## Dual Architecture Overview

### 3.1 Concept

The BQX ML system uses a **dual-domain feature architecture** where all features exist in two versions:

1. **Rate Index Domain (`*_idx_*`)** - Features computed on price (rate_index)
   - Captures price dynamics, trends, volatility
   - Traditional technical analysis perspective
   - SOURCE: M1 tables `rate_index` column

2. **BQX Momentum Domain (`*_bqx_*`)** - Features computed on backward momentum
   - Captures momentum persistence, acceleration, regime shifts
   - Second-derivative perspective (momentum of momentum)
   - SOURCE: BQX tables `w15_bqx_return`, etc.

### 3.2 Why Dual Architecture?

**Example: RSI Indicator**

```
RSI_idx (on rate_index):
- RSI_idx > 70 → Price is overbought
- Measures: Price momentum relative to recent price changes

RSI_bqx (on bqx_w15_return):
- RSI_bqx > 70 → Momentum acceleration is overbought
- Measures: Momentum-of-momentum (2nd derivative!)

Combined Signal:
- RSI_idx = 75, RSI_bqx = 30 → Price rising fast but momentum slowing (reversal?)
- RSI_idx = 30, RSI_bqx = 70 → Price falling but momentum accelerating down (trend continuation)
```

### 3.3 Feature Parity Requirements

For every rate-index feature table, there must be a corresponding BQX feature table:

| Rate Index Table | BQX Momentum Table | Status |
|------------------|-------------------|--------|
| `reg_idx_{pair}` | `reg_bqx_{pair}` | ✅ Both exist |
| `technical_idx_{pair}` | `technical_bqx_{pair}` | ⚠️ Rate exists, BQX to build |
| `bollinger_idx_{pair}` | `bollinger_bqx_{pair}` | ⚠️ Rate exists, BQX to build |
| `fibonacci_idx_{pair}` | `fibonacci_bqx_{pair}` | ⚠️ Rate exists, BQX to build |
| `statistics_idx_{pair}` | `statistics_bqx_{pair}` | ⚠️ Rate exists, BQX to build |
| `volume_idx_{pair}` | `volume_bqx_{pair}` | ⚠️ Rate exists, BQX to build |
| `spread_idx_{pair}` | `spread_bqx_{pair}` | ✅ Spread is rate-only (no BQX version) |
| `time_idx_{pair}` | `time_bqx_{pair}` | ✅ Time is universal (no BQX version) |
| `correlation_idx_{pair}` | `correlation_bqx_{pair}` | ⚠️ Both empty, both to build |

**Note:** Spread and Time features are domain-agnostic and only have one version.

---

<a name="schema-migration"></a>
## Schema Migration Plan (Phase 1.6.9)

### 4.1 Overview

**Objective:** Rename existing rate-based feature tables to follow `*_idx_*` naming convention.

**Duration:** 1 hour
**Risk:** Low (ALTER TABLE is atomic and instant for renaming)
**Blocks:** All subsequent feature builds (must be completed first)

### 4.2 Tables to Rename

| Current Name | New Name | Tables | Rows | Status |
|--------------|----------|--------|------|--------|
| `reg_{pair}` | `reg_idx_{pair}` | 336 | 10.3M | ✅ Script ready |
| `statistics_features_{pair}` | `statistics_idx_{pair}` | 364 | 10.3M | ✅ Script ready |
| `bollinger_features_{pair}` | `bollinger_idx_{pair}` | 364 | 10.3M | ✅ Script ready |
| `fibonacci_features_{pair}` | `fibonacci_idx_{pair}` | 364 | 10.2M | ✅ Script ready |
| `volume_features_{pair}` | `volume_idx_{pair}` | 336 | 10M | ✅ Script ready |
| `spread_features_{pair}` | `spread_idx_{pair}` | 336 | 10M | ✅ Script ready |
| `correlation_features_{pair}` | `correlation_idx_{pair}` | 364 | 0 | ✅ Script ready |
| `technical_features_{pair}` | `technical_idx_{pair}` | 364 | 10.2M | ⚠️ Needs script |

**Total Tables to Rename:** ~2,628 (including all partitions)

### 4.3 Rename SQL Template

```sql
-- Parent table rename
ALTER TABLE bqx.technical_features_{pair}
RENAME TO technical_idx_{pair};

-- Partition renames (automated loop)
ALTER TABLE bqx.technical_features_{pair}_2024_07
RENAME TO technical_idx_{pair}_2024_07;

ALTER TABLE bqx.technical_features_{pair}_2024_08
RENAME TO technical_idx_{pair}_2024_08;
-- ... (repeat for all partitions)
```

### 4.4 Verification Queries

```sql
-- Pre-rename count
SELECT COUNT(*) FROM bqx.technical_features_eurusd;

-- Post-rename count (should match)
SELECT COUNT(*) FROM bqx.technical_idx_eurusd;

-- Verify all renames complete
SELECT
    tablename
FROM pg_tables
WHERE schemaname = 'bqx'
    AND tablename LIKE 'technical_features%'
ORDER BY tablename;
-- Should return 0 rows after rename
```

### 4.5 Rollback Plan

```sql
-- If issues arise, reverse the rename
ALTER TABLE bqx.technical_idx_{pair}
RENAME TO technical_features_{pair};

-- Partitions
ALTER TABLE bqx.technical_idx_{pair}_2024_07
RENAME TO technical_features_{pair}_2024_07;
-- ... etc
```

---

<a name="new-tables"></a>
## New Table Requirements

### 5.1 BQX Feature Tables (Core Dual Architecture)

#### 5.1.1 Technical BQX (`technical_bqx_{pair}`)

**Purpose:** Technical indicators on BQX momentum
**Source Data:** `bqx_{pair}.w15_bqx_return`
**Tables:** 28 parent tables
**Partitions:** 336 (28 pairs × 12 months)

```sql
-- Schema (15 indicators, optimized for momentum)
CREATE TABLE bqx.technical_bqx_eurusd (
    ts_utc TIMESTAMPTZ NOT NULL,

    -- Momentum oscillators
    rsi_14 DOUBLE PRECISION,              -- RSI on BQX returns
    rsi_21 DOUBLE PRECISION,
    stoch_k DOUBLE PRECISION,             -- Stochastic on BQX
    stoch_d DOUBLE PRECISION,

    -- Trend indicators
    macd DOUBLE PRECISION,                -- MACD on BQX
    macd_signal DOUBLE PRECISION,
    macd_histogram DOUBLE PRECISION,

    -- Momentum strength
    cci_20 DOUBLE PRECISION,              -- CCI on BQX
    williams_r_14 DOUBLE PRECISION,
    roc_12 DOUBLE PRECISION,

    -- Volatility
    atr_14 DOUBLE PRECISION,              -- ATR on BQX changes
    atr_pct DOUBLE PRECISION,             -- ATR as % of BQX

    -- Directional movement
    adx_14 DOUBLE PRECISION,              -- ADX on BQX
    plus_di DOUBLE PRECISION,
    minus_di DOUBLE PRECISION,

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);

-- Create partitions (2024-07 to 2025-06)
CREATE TABLE bqx.technical_bqx_eurusd_2024_07
PARTITION OF bqx.technical_bqx_eurusd
FOR VALUES FROM ('2024-07-01 00:00:00+00') TO ('2024-08-01 00:00:00+00');
-- ... (repeat for each month)
```

**Storage Estimate:** ~150 MB per pair (15 columns × 370K rows × 8 bytes)
**Total:** 4.2 GB for 28 pairs

#### 5.1.2 Bollinger BQX (`bollinger_bqx_{pair}`)

**Purpose:** Bollinger Bands on BQX momentum
**Interpretation:** Overbought/oversold conditions in momentum space

```sql
CREATE TABLE bqx.bollinger_bqx_eurusd (
    ts_utc TIMESTAMPTZ NOT NULL,

    -- 20-period Bollinger Bands
    bb_upper_20 DOUBLE PRECISION,         -- Upper band (mean + 2σ)
    bb_middle_20 DOUBLE PRECISION,        -- Middle band (SMA)
    bb_lower_20 DOUBLE PRECISION,         -- Lower band (mean - 2σ)
    bb_width_20 DOUBLE PRECISION,         -- Band width
    bb_percent_b DOUBLE PRECISION,        -- %B position

    -- 50-period Bollinger Bands
    bb_upper_50 DOUBLE PRECISION,
    bb_middle_50 DOUBLE PRECISION,
    bb_lower_50 DOUBLE PRECISION,
    bb_width_50 DOUBLE PRECISION,
    bb_percent_b_50 DOUBLE PRECISION,

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

**Storage Estimate:** ~80 MB per pair
**Total:** 2.2 GB for 28 pairs

#### 5.1.3 Fibonacci BQX (`fibonacci_bqx_{pair}`)

**Purpose:** Fibonacci retracements in BQX momentum space
**Use Case:** Support/resistance levels for momentum values

```sql
CREATE TABLE bqx.fibonacci_bqx_eurusd (
    ts_utc TIMESTAMPTZ NOT NULL,

    -- Retracement levels (based on recent BQX range)
    fib_retracement_236 DOUBLE PRECISION,  -- 23.6%
    fib_retracement_382 DOUBLE PRECISION,  -- 38.2%
    fib_retracement_500 DOUBLE PRECISION,  -- 50.0%
    fib_retracement_618 DOUBLE PRECISION,  -- 61.8%
    fib_retracement_786 DOUBLE PRECISION,  -- 78.6%

    -- Extension levels
    fib_extension_1618 DOUBLE PRECISION,   -- 161.8%
    fib_extension_2618 DOUBLE PRECISION,   -- 261.8%
    fib_extension_4236 DOUBLE PRECISION,   -- 423.6%

    -- Distance to nearest level
    distance_to_nearest_fib DOUBLE PRECISION,
    nearest_fib_level DOUBLE PRECISION,

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

**Storage Estimate:** ~80 MB per pair
**Total:** 2.2 GB for 28 pairs

#### 5.1.4 Statistics BQX (`statistics_bqx_{pair}`)

**Purpose:** Statistical moments of BQX momentum distribution

```sql
CREATE TABLE bqx.statistics_bqx_eurusd (
    ts_utc TIMESTAMPTZ NOT NULL,

    -- 20-period statistics
    mean_20 DOUBLE PRECISION,
    std_20 DOUBLE PRECISION,
    skew_20 DOUBLE PRECISION,
    kurt_20 DOUBLE PRECISION,

    -- 50-period statistics
    mean_50 DOUBLE PRECISION,
    std_50 DOUBLE PRECISION,
    skew_50 DOUBLE PRECISION,
    kurt_50 DOUBLE PRECISION,

    -- 120-period statistics
    mean_120 DOUBLE PRECISION,
    std_120 DOUBLE PRECISION,
    skew_120 DOUBLE PRECISION,
    kurt_120 DOUBLE PRECISION,

    -- Range and extremes
    min_60 DOUBLE PRECISION,
    max_60 DOUBLE PRECISION,
    range_60 DOUBLE PRECISION,

    -- Z-scores
    z_score_20 DOUBLE PRECISION,
    z_score_60 DOUBLE PRECISION,

    -- Autocorrelation
    autocorr_lag1 DOUBLE PRECISION,
    autocorr_lag5 DOUBLE PRECISION,
    autocorr_lag15 DOUBLE PRECISION,

    -- Entropy
    entropy_60 DOUBLE PRECISION,

    -- MAD
    mad_60 DOUBLE PRECISION,

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

**Storage Estimate:** ~150 MB per pair
**Total:** 4.2 GB for 28 pairs

#### 5.1.5 Volume BQX (`volume_bqx_{pair}`)

**Purpose:** Volume-momentum interaction features

```sql
CREATE TABLE bqx.volume_bqx_eurusd (
    ts_utc TIMESTAMPTZ NOT NULL,

    -- Volume-momentum correlations
    vol_bqx_corr_20 DOUBLE PRECISION,      -- 20-period correlation
    vol_bqx_corr_60 DOUBLE PRECISION,      -- 60-period correlation

    -- Volume during BQX events
    volume_on_bqx_surge DOUBLE PRECISION,  -- Avg vol when BQX > +1σ
    volume_on_bqx_drop DOUBLE PRECISION,   -- Avg vol when BQX < -1σ

    -- BQX per unit volume
    bqx_per_volume DOUBLE PRECISION,       -- Momentum efficiency

    -- Confirmation/divergence flags
    bqx_volume_confirm INT,                -- 1 if vol confirms BQX direction
    bqx_volume_diverge INT,                -- 1 if vol diverges from BQX

    -- Relative BQX strength by volume tercile
    bqx_high_vol_avg DOUBLE PRECISION,     -- Avg BQX in high vol periods
    bqx_low_vol_avg DOUBLE PRECISION,      -- Avg BQX in low vol periods

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

**Storage Estimate:** ~70 MB per pair
**Total:** 2.0 GB for 28 pairs

#### 5.1.6 Correlation BQX (`correlation_bqx_{pair}`)

**Purpose:** Cross-pair and cross-window BQX correlations
**Critical:** Must be built LAST (depends on all other BQX features)

```sql
CREATE TABLE bqx.correlation_bqx_eurusd (
    ts_utc TIMESTAMPTZ NOT NULL,

    -- Cross-pair BQX correlations (EUR-related pairs)
    corr_bqx_eurusd_eurgbp_15 DOUBLE PRECISION,
    corr_bqx_eurusd_eurjpy_15 DOUBLE PRECISION,
    corr_bqx_eurusd_eurcad_15 DOUBLE PRECISION,

    -- USD basket correlation
    corr_bqx_usd_basket_60 DOUBLE PRECISION,

    -- Cross-window term structure (CRITICAL!)
    bqx_term_w15_w30 DOUBLE PRECISION,     -- Correlation(w15, w30)
    bqx_term_w30_w60 DOUBLE PRECISION,     -- Correlation(w30, w60)
    bqx_term_w60_w75 DOUBLE PRECISION,     -- Correlation(w60, w75)

    -- Term structure slope
    term_slope DOUBLE PRECISION,           -- Slope of w15→w75
    term_curvature DOUBLE PRECISION,       -- Curvature
    term_inversion_flag INT,               -- 1 if inverted

    -- Momentum variance decomposition
    bqx_systematic_var DOUBLE PRECISION,   -- Variance from systematic factors
    bqx_idiosyncratic_var DOUBLE PRECISION,-- Pair-specific variance
    variance_decomp_ratio DOUBLE PRECISION,

    -- Lead-lag relationships
    bqx_leads_rate_idx INT,                -- 1 if BQX leads rate changes
    lead_lag_correlation DOUBLE PRECISION,

    -- Triangular momentum parity
    tri_bqx_residual DOUBLE PRECISION,     -- EUR/USD vs EUR/GBP × GBP/USD
    tri_bqx_z_score DOUBLE PRECISION,

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

**Storage Estimate:** ~120 MB per pair
**Total:** 3.4 GB for 28 pairs

### 5.2 Advanced Feature Tables (New Categories)

#### 5.2.1 Cointegration Features (`cointegration_{pair}`)

**Purpose:** Detect cointegration relationships between currency pairs
**Use Case:** Pairs trading, mean reversion strategies

```sql
CREATE TABLE bqx.cointegration_eurusd (
    ts_utc TIMESTAMPTZ NOT NULL,

    -- Primary cointegration relationships
    coint_eurusd_gbpusd_adf DOUBLE PRECISION,  -- ADF statistic
    coint_eurusd_gbpusd_pvalue DOUBLE PRECISION,
    coint_eurusd_gbpusd_residual DOUBLE PRECISION,
    coint_eurusd_gbpusd_halflife DOUBLE PRECISION,

    coint_eurusd_eurjpy_adf DOUBLE PRECISION,
    coint_eurusd_eurjpy_pvalue DOUBLE PRECISION,
    coint_eurusd_eurjpy_residual DOUBLE PRECISION,
    coint_eurusd_eurjpy_halflife DOUBLE PRECISION,

    -- Rolling cointegration
    coint_window_60_count INT,             -- # of cointegrated pairs in 60min
    coint_strength_avg DOUBLE PRECISION,   -- Avg cointegration strength

    -- Spread metrics
    spread_z_score DOUBLE PRECISION,       -- Z-score of cointegration spread
    spread_percentile_90d DOUBLE PRECISION,-- Percentile vs 90-day history

    -- Mean reversion speed
    reversion_speed DOUBLE PRECISION,      -- Speed of mean reversion
    time_since_reversion INT,              -- Minutes since last reversion

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

**Tables:** 28 pairs
**Partitions:** 336
**Storage Estimate:** ~100 MB per pair → 2.8 GB total

#### 5.2.2 Realized Volatility (`realized_volatility_{pair}`)

**Purpose:** High-frequency volatility measures
**Method:** Realized variance from intraday returns

```sql
CREATE TABLE bqx.realized_volatility_eurusd (
    ts_utc TIMESTAMPTZ NOT NULL,

    -- Realized variance (sum of squared returns)
    rv_5min DOUBLE PRECISION,              -- 5-min realized variance
    rv_15min DOUBLE PRECISION,             -- 15-min realized variance
    rv_30min DOUBLE PRECISION,             -- 30-min realized variance
    rv_60min DOUBLE PRECISION,             -- 60-min realized variance

    -- Realized volatility (sqrt of RV)
    rvol_5min DOUBLE PRECISION,
    rvol_15min DOUBLE PRECISION,
    rvol_30min DOUBLE PRECISION,
    rvol_60min DOUBLE PRECISION,

    -- Bipower variation (jump-robust volatility)
    bpv_15min DOUBLE PRECISION,
    bpv_60min DOUBLE PRECISION,

    -- Jump detection
    jump_component_15min DOUBLE PRECISION, -- RV - BPV
    jump_ratio_15min DOUBLE PRECISION,     -- Jump / Total variance
    jump_flag INT,                         -- 1 if significant jump detected

    -- Volatility regime
    vol_regime INT,                        -- 1=low, 2=mid, 3=high
    vol_percentile_30d DOUBLE PRECISION,   -- Percentile vs 30-day history

    -- HAR model components
    har_daily DOUBLE PRECISION,            -- Daily RV component
    har_weekly DOUBLE PRECISION,           -- Weekly RV component
    har_monthly DOUBLE PRECISION,          -- Monthly RV component

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

**Tables:** 28 pairs
**Partitions:** 336
**Storage Estimate:** ~130 MB per pair → 3.6 GB total

#### 5.2.3 HMM Regime Features (`hmm_regime_{pair}`)

**Purpose:** Hidden Markov Model regime classification
**States:** Trending, Mean-Reverting, High-Volatility, Low-Volatility

```sql
CREATE TABLE bqx.hmm_regime_eurusd (
    ts_utc TIMESTAMPTZ NOT NULL,

    -- Current regime (from HMM)
    regime INT,                            -- 1=trend, 2=mean-rev, 3=high-vol, 4=low-vol
    regime_probability DOUBLE PRECISION,   -- P(current regime | data)

    -- Regime probabilities (all states)
    prob_trend DOUBLE PRECISION,
    prob_mean_rev DOUBLE PRECISION,
    prob_high_vol DOUBLE PRECISION,
    prob_low_vol DOUBLE PRECISION,

    -- Regime stability
    regime_duration INT,                   -- Minutes in current regime
    regime_transition_flag INT,            -- 1 if regime changed in last 5min

    -- Expected regime duration
    expected_duration_current DOUBLE PRECISION,
    transition_prob_next DOUBLE PRECISION, -- P(transition in next period)

    -- Regime-conditional statistics
    regime_mean_return DOUBLE PRECISION,   -- Mean return in current regime
    regime_volatility DOUBLE PRECISION,    -- Volatility in current regime

    -- Multi-regime features
    regime_diversity_60 DOUBLE PRECISION,  -- Entropy of regime distribution (60min)
    regime_flip_count_60 INT,              -- # of regime changes (60min)

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

**Tables:** 28 pairs
**Partitions:** 336
**Storage Estimate:** ~100 MB per pair → 2.8 GB total

#### 5.2.4 Cross-Sectional Features (`cross_sectional`)

**Purpose:** Cross-pair ranking and relative value
**Note:** Single table covering all pairs at each timestamp

```sql
CREATE TABLE bqx.cross_sectional (
    ts_utc TIMESTAMPTZ NOT NULL,
    pair VARCHAR(10) NOT NULL,

    -- Cross-sectional ranks (1-28)
    rank_return_15min INT,                 -- Rank by 15-min return
    rank_return_60min INT,                 -- Rank by 60-min return
    rank_volatility INT,                   -- Rank by realized volatility
    rank_volume INT,                       -- Rank by volume
    rank_bqx_w15 INT,                      -- Rank by BQX w15

    -- Percentile scores (0-100)
    pct_return_15min DOUBLE PRECISION,
    pct_return_60min DOUBLE PRECISION,
    pct_volatility DOUBLE PRECISION,
    pct_bqx_w15 DOUBLE PRECISION,

    -- Z-scores vs cross-section
    z_return_15min DOUBLE PRECISION,       -- (return - mean) / std across pairs
    z_volatility DOUBLE PRECISION,
    z_bqx_w15 DOUBLE PRECISION,

    -- Relative strength
    relative_strength_usd DOUBLE PRECISION,-- Strength vs USD pairs
    relative_strength_eur DOUBLE PRECISION,-- Strength vs EUR pairs
    relative_strength_all DOUBLE PRECISION,-- Strength vs all pairs

    -- Outlier flags
    outlier_return INT,                    -- 1 if |z_return| > 2.5
    outlier_volatility INT,                -- 1 if z_vol > 2.5

    -- Sector/basket aggregates
    usd_basket_avg_return DOUBLE PRECISION,
    eur_basket_avg_return DOUBLE PRECISION,
    jpy_basket_avg_return DOUBLE PRECISION,

    PRIMARY KEY (ts_utc, pair)
) PARTITION BY RANGE (ts_utc);
```

**Partitions:** 12 months
**Rows:** 370K timestamps × 28 pairs = 10.4M rows
**Storage Estimate:** ~800 MB total

---

<a name="partitioning"></a>
## Partitioning Strategy

### 6.1 Current Strategy (Proven Effective)

**Method:** Range partitioning by `ts_utc` (timestamp)
**Interval:** Monthly (`YYYY_MM` format)
**Retention:** Rolling 24-month window

### 6.2 Partition Naming Convention

```
Format: {table_name}_{YYYY}_{MM}

Examples:
- technical_idx_eurusd_2024_07
- technical_idx_eurusd_2024_08
- technical_bqx_eurusd_2024_07
- correlation_bqx_eurusd_2025_01
```

### 6.3 Partition Creation SQL

```sql
-- Parent table (partitioned)
CREATE TABLE bqx.technical_bqx_eurusd (
    ts_utc TIMESTAMPTZ NOT NULL,
    -- ... columns ...
    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);

-- Create 12 monthly partitions (2024-07 to 2025-06)
CREATE TABLE bqx.technical_bqx_eurusd_2024_07
PARTITION OF bqx.technical_bqx_eurusd
FOR VALUES FROM ('2024-07-01 00:00:00+00') TO ('2024-08-01 00:00:00+00');

CREATE TABLE bqx.technical_bqx_eurusd_2024_08
PARTITION OF bqx.technical_bqx_eurusd
FOR VALUES FROM ('2024-08-01 00:00:00+00') TO ('2024-09-01 00:00:00+00');

-- ... repeat for each month ...

CREATE TABLE bqx.technical_bqx_eurusd_2025_06
PARTITION OF bqx.technical_bqx_eurusd
FOR VALUES FROM ('2025-06-01 00:00:00+00') TO ('2025-07-01 00:00:00+00');
```

### 6.4 Automated Partition Management

```sql
-- Function to auto-create next month's partition
CREATE OR REPLACE FUNCTION bqx.create_next_partition(
    table_name TEXT,
    pair TEXT
) RETURNS VOID AS $$
DECLARE
    next_month DATE;
    month_after DATE;
    partition_name TEXT;
BEGIN
    -- Get first day of next month
    next_month := DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month');
    month_after := next_month + INTERVAL '1 month';

    -- Build partition name
    partition_name := format('%s_%s_%s',
        table_name,
        pair,
        TO_CHAR(next_month, 'YYYY_MM')
    );

    -- Create partition
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS bqx.%s
        PARTITION OF bqx.%s_%s
        FOR VALUES FROM (%L) TO (%L)',
        partition_name,
        table_name,
        pair,
        next_month,
        month_after
    );
END;
$$ LANGUAGE plpgsql;

-- Example usage
SELECT bqx.create_next_partition('technical_bqx', 'eurusd');
```

### 6.5 Partition Pruning Verification

```sql
-- Verify partition pruning is working
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM bqx.technical_idx_eurusd
WHERE ts_utc >= '2024-10-01' AND ts_utc < '2024-11-01';

-- Expected output should show:
-- "Partitions scanned: 1" (only 2024_10 partition)
-- NOT "Partitions scanned: 12" (would indicate no pruning)
```

### 6.6 Partition Drop Strategy (Data Retention)

```sql
-- Drop partitions older than 24 months
DO $$
DECLARE
    cutoff_date DATE := CURRENT_DATE - INTERVAL '24 months';
    partition_record RECORD;
BEGIN
    FOR partition_record IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'bqx'
            AND tablename LIKE '%_eurusd_%'
            AND tablename ~ '_[0-9]{4}_[0-9]{2}$'
    LOOP
        -- Extract date from partition name
        IF partition_record.tablename ~ '_2020_|_2021_|_2022_' THEN
            EXECUTE 'DROP TABLE IF EXISTS bqx.' || partition_record.tablename;
            RAISE NOTICE 'Dropped old partition: %', partition_record.tablename;
        END IF;
    END LOOP;
END $$;
```

---

<a name="indexes"></a>
## Index Requirements

### 7.1 Current Index Coverage

**Status:** All tables have PRIMARY KEY on `ts_utc` (btree)
**Gap:** Missing secondary indexes for common query patterns

### 7.2 Required Indexes by Table Type

#### 7.2.1 M1 Rate Tables

```sql
-- Already exists
CREATE INDEX idx_m1_eurusd_rate_index ON bqx.m1_eurusd(rate_index);

-- Additional recommended indexes
CREATE INDEX idx_m1_eurusd_time_rate ON bqx.m1_eurusd(time, rate_index);
CREATE INDEX idx_m1_eurusd_volume ON bqx.m1_eurusd(volume) WHERE volume > 0;
```

#### 7.2.2 Feature Tables (General Pattern)

```sql
-- Primary key (already exists on all tables)
CREATE UNIQUE INDEX {table}_pkey ON bqx.{table} (ts_utc);

-- Composite index for time-range queries with filters
CREATE INDEX idx_{table}_ts_features
ON bqx.{table} (ts_utc, {key_feature_1}, {key_feature_2});

-- Example for technical_idx_eurusd
CREATE INDEX idx_technical_idx_eurusd_ts_rsi
ON bqx.technical_idx_eurusd (ts_utc, rsi_14, macd);
```

#### 7.2.3 Correlation Tables (Cross-Pair Queries)

```sql
-- Index for correlation lookups
CREATE INDEX idx_correlation_idx_eurusd_base_quote
ON bqx.correlation_idx_eurusd (
    ts_utc,
    corr_base_pairs_15min,
    corr_quote_pairs_15min
);

-- Index for cointegration queries
CREATE INDEX idx_cointegration_eurusd_residual
ON bqx.cointegration_eurusd (
    ts_utc,
    coint_eurusd_gbpusd_residual
) WHERE coint_eurusd_gbpusd_residual IS NOT NULL;
```

#### 7.2.4 Cross-Sectional Table

```sql
-- Multi-column index for ranking queries
CREATE INDEX idx_cross_sectional_ts_pair
ON bqx.cross_sectional (ts_utc, pair);

CREATE INDEX idx_cross_sectional_ranks
ON bqx.cross_sectional (
    ts_utc,
    rank_return_15min,
    rank_bqx_w15
);
```

### 7.3 Index Maintenance

```sql
-- Monthly index rebuild (optional, for performance)
REINDEX TABLE CONCURRENTLY bqx.technical_idx_eurusd;

-- Analyze tables after bulk inserts
ANALYZE bqx.technical_idx_eurusd;

-- Check index usage statistics
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'bqx'
ORDER BY idx_scan DESC
LIMIT 50;

-- Drop unused indexes
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_stat_user_indexes
WHERE schemaname = 'bqx'
    AND idx_scan = 0
    AND indexname NOT LIKE '%_pkey';
```

### 7.4 Partial Indexes (Space Optimization)

```sql
-- Index only non-NULL values (common for derived features)
CREATE INDEX idx_technical_bqx_eurusd_rsi_nonnull
ON bqx.technical_bqx_eurusd (ts_utc, rsi_14)
WHERE rsi_14 IS NOT NULL;

-- Index only extreme values (outlier detection)
CREATE INDEX idx_realized_volatility_jumps
ON bqx.realized_volatility_eurusd (ts_utc, jump_component_15min)
WHERE jump_flag = 1;
```

---

<a name="storage"></a>
## Storage Estimates

### 8.1 Current Storage (61 GB)

| Category | Size | % of Total |
|----------|------|------------|
| M1 Rates | 28 GB | 45.9% |
| Other (legacy) | 12 GB | 19.7% |
| Technical Idx | 4.5 GB | 7.4% |
| Spread Idx | 3.5 GB | 5.7% |
| BQX Features | 3.6 GB | 5.9% |
| ML Features | 2.6 GB | 4.3% |
| Fibonacci Idx | 1.8 GB | 3.0% |
| Time Idx | 1.8 GB | 3.0% |
| Volume Idx | 1.4 GB | 2.3% |
| Bollinger Idx | 1.2 GB | 2.0% |
| Statistics Idx | 1.2 GB | 2.0% |
| Correlation Idx | 2.7 MB | 0.004% |
| **Total** | **61 GB** | **100%** |

### 8.2 Expansion Storage Estimates

#### New BQX Feature Tables

| Feature Type | Storage/Pair | Total (28 pairs) | Partitions |
|--------------|--------------|------------------|------------|
| Technical BQX | 150 MB | 4.2 GB | 336 |
| Bollinger BQX | 80 MB | 2.2 GB | 336 |
| Fibonacci BQX | 80 MB | 2.2 GB | 336 |
| Statistics BQX | 150 MB | 4.2 GB | 336 |
| Volume BQX | 70 MB | 2.0 GB | 336 |
| Correlation BQX | 120 MB | 3.4 GB | 336 |
| **BQX Subtotal** | **650 MB** | **18.2 GB** | **2,016** |

#### Advanced Feature Tables

| Feature Type | Storage/Pair | Total (28 pairs) | Partitions |
|--------------|--------------|------------------|------------|
| Cointegration | 100 MB | 2.8 GB | 336 |
| Realized Volatility | 130 MB | 3.6 GB | 336 |
| HMM Regime | 100 MB | 2.8 GB | 336 |
| Cross-Sectional | N/A | 0.8 GB | 12 |
| **Advanced Subtotal** | **330 MB** | **10.0 GB** | **1,020** |

#### Correlation Idx Population

| Feature Type | Current | After Population | Increase |
|--------------|---------|------------------|----------|
| Correlation Idx | 2.7 MB | ~3.4 GB | +3.4 GB |

### 8.3 Total Expansion Impact

```
Current Database:           61.0 GB
+ BQX Features:            +18.2 GB
+ Advanced Features:       +10.0 GB
+ Correlation Idx:         + 3.4 GB
+ Index Overhead (15%):    + 4.7 GB
=====================================
Projected Total:           97.3 GB

Storage Increase: 36.3 GB (59.5%)
```

### 8.4 Storage Growth Projections

**Monthly Growth Rate:**
- New data ingestion: ~2.5 GB/month (all pairs, all features)
- Index growth: ~0.4 GB/month

**Annual Projection:**
- Year 1 (full feature set): 97.3 GB + (12 × 2.9 GB) = ~132 GB
- Year 2 (with retention policy): ~150 GB (old partitions dropped)

**Recommended RDS Instance:**
- Current: Sufficient for 61 GB
- After expansion: Plan for 150-200 GB allocated storage
- With retention: Can maintain <200 GB indefinitely

---

<a name="advanced-features"></a>
## Advanced Features Expansion

### 9.1 Priority Ranking

| Priority | Feature Category | Impact | Complexity | Timeline |
|----------|------------------|--------|------------|----------|
| 1 | BQX Features | High | Medium | 25-30 hrs |
| 2 | Correlation Idx Population | High | Low | 8 hrs |
| 3 | Realized Volatility | Medium | Low | 6 hrs |
| 4 | Cointegration | Medium | Medium | 10 hrs |
| 5 | HMM Regime | Medium | High | 15 hrs |
| 6 | Cross-Sectional | Low | Low | 4 hrs |

### 9.2 Implementation Sequence

**Phase 1.6.9:** Table Renaming (1 hour) → **BLOCKS ALL**

**Phase 1.6.10-16:** Core Dual Architecture (Parallel)
1. Technical Idx (8 hrs) + Technical BQX (8 hrs) = 8 hrs parallel
2. Statistics BQX (6 hrs)
3. Bollinger BQX (6 hrs)
4. Fibonacci BQX (6 hrs)
5. Volume BQX (4 hrs)
6. Correlation Idx (8 hrs)
7. Correlation BQX (8 hrs) → **MUST BE LAST**

**Wall Time:** ~30 hours (with 4 parallel workers)

**Phase 1.7:** Advanced Features (Sequential)
1. Realized Volatility (6 hrs)
2. Cointegration (10 hrs)
3. Cross-Sectional (4 hrs)
4. HMM Regime (15 hrs)

**Wall Time:** ~35 hours

**Total: 66 hours wall time (~11 days at 6 hrs/day)**

---

<a name="timeline"></a>
## Implementation Timeline

### 10.1 Gantt Chart

```
Week 1:
Mon: [Phase 1.6.9: Rename] (1hr)
Tue-Thu: [Phase 1.6.10-11: Technical Idx + BQX] (parallel, 8hrs)
Fri: [Phase 1.6.12: Statistics BQX] (6hrs)

Week 2:
Mon: [Phase 1.6.13: Bollinger BQX] (6hrs)
Tue: [Phase 1.6.14: Fibonacci BQX] (6hrs)
Wed: [Phase 1.6.15: Volume BQX] (4hrs)
Thu: [Phase 1.6.16: Correlation Idx] (8hrs)
Fri: [Phase 1.6.17: Correlation BQX] (8hrs)

Week 3:
Mon: [Phase 1.7.1: Realized Volatility] (6hrs)
Tue-Wed: [Phase 1.7.2: Cointegration] (10hrs)
Thu: [Phase 1.7.3: Cross-Sectional] (4hrs)
Fri-Mon: [Phase 1.7.4: HMM Regime] (15hrs)

Week 4:
Tue: [Validation & Testing]
Wed: [Documentation Update]
Thu: [Performance Tuning]
Fri: [Phase 2 Kickoff: Feature Engineering Pipeline]
```

### 10.2 Critical Path

```
Phase 1.6.9 (Rename)
    ↓
Phase 1.6.10-16 (Core BQX, parallel)
    ↓
Phase 1.6.17 (Correlation BQX) ← DEPENDS ON ALL ABOVE
    ↓
Phase 1.7 (Advanced Features, sequential)
    ↓
Phase 2 (Feature Engineering Pipeline)
```

### 10.3 Resource Allocation

**Compute:**
- EC2 t3.2xlarge (already running): Feature computation workers
- Aurora RDS: Database writes (parallelized across pairs)

**Personnel:**
- Data Engineer: Full-time (40 hrs/week)
- Optional: ML Engineer (review, validation)

**Timeline:**
- Optimistic: 2.5 weeks
- Realistic: 3.5 weeks
- Pessimistic: 5 weeks (with debugging/rework)

---

<a name="sql-examples"></a>
## SQL Examples

### 11.1 Table Renaming (Phase 1.6.9)

```sql
-- Rename parent table
ALTER TABLE bqx.technical_features_eurusd
RENAME TO technical_idx_eurusd;

-- Rename all partitions (loop for all months)
DO $$
DECLARE
    pair TEXT := 'eurusd';
    month_suffix TEXT;
    old_name TEXT;
    new_name TEXT;
BEGIN
    FOR month_suffix IN
        SELECT TO_CHAR(d, 'YYYY_MM')
        FROM generate_series(
            '2024-07-01'::date,
            '2025-06-01'::date,
            '1 month'::interval
        ) AS d
    LOOP
        old_name := 'technical_features_' || pair || '_' || month_suffix;
        new_name := 'technical_idx_' || pair || '_' || month_suffix;

        EXECUTE 'ALTER TABLE IF EXISTS bqx.' || old_name ||
                ' RENAME TO ' || new_name;

        RAISE NOTICE 'Renamed % to %', old_name, new_name;
    END LOOP;
END $$;

-- Verify rename complete
SELECT COUNT(*)
FROM pg_tables
WHERE schemaname = 'bqx'
    AND tablename LIKE 'technical_features%';
-- Should return 0

SELECT COUNT(*)
FROM pg_tables
WHERE schemaname = 'bqx'
    AND tablename LIKE 'technical_idx%';
-- Should return 364 (28 pairs × 13 months)
```

### 11.2 Create BQX Feature Table

```sql
-- Create parent table
CREATE TABLE bqx.technical_bqx_eurusd (
    ts_utc TIMESTAMPTZ NOT NULL,
    rsi_14 DOUBLE PRECISION,
    rsi_21 DOUBLE PRECISION,
    stoch_k DOUBLE PRECISION,
    stoch_d DOUBLE PRECISION,
    macd DOUBLE PRECISION,
    macd_signal DOUBLE PRECISION,
    macd_histogram DOUBLE PRECISION,
    cci_20 DOUBLE PRECISION,
    williams_r_14 DOUBLE PRECISION,
    roc_12 DOUBLE PRECISION,
    atr_14 DOUBLE PRECISION,
    atr_pct DOUBLE PRECISION,
    adx_14 DOUBLE PRECISION,
    plus_di DOUBLE PRECISION,
    minus_di DOUBLE PRECISION,
    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);

-- Create monthly partitions
DO $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
BEGIN
    FOR start_date IN
        SELECT d::date
        FROM generate_series(
            '2024-07-01'::timestamp,
            '2025-06-01'::timestamp,
            '1 month'::interval
        ) AS d
    LOOP
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'technical_bqx_eurusd_' || TO_CHAR(start_date, 'YYYY_MM');

        EXECUTE format('
            CREATE TABLE bqx.%I
            PARTITION OF bqx.technical_bqx_eurusd
            FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            start_date,
            end_date
        );

        RAISE NOTICE 'Created partition: %', partition_name;
    END LOOP;
END $$;

-- Verify creation
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size('bqx.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'bqx'
    AND tablename LIKE 'technical_bqx_eurusd%'
ORDER BY tablename;
```

### 11.3 Populate Correlation Idx Table

```sql
-- Example: Compute cross-pair correlations for EURUSD
INSERT INTO bqx.correlation_idx_eurusd (
    ts_utc,
    corr_base_pairs_15min,
    corr_base_pairs_60min,
    corr_quote_pairs_15min,
    corr_quote_pairs_60min
)
SELECT
    e.ts_utc,

    -- Base pair correlation (EUR-related pairs, 15min window)
    CORR(
        e.rate_index - LAG(e.rate_index, 15) OVER (ORDER BY e.ts_utc),
        eg.rate_index - LAG(eg.rate_index, 15) OVER (ORDER BY eg.ts_utc)
    ) OVER (ORDER BY e.ts_utc ROWS BETWEEN 14 PRECEDING AND CURRENT ROW),

    -- Base pair correlation (60min window)
    CORR(
        e.rate_index - LAG(e.rate_index, 60) OVER (ORDER BY e.ts_utc),
        eg.rate_index - LAG(eg.rate_index, 60) OVER (ORDER BY eg.ts_utc)
    ) OVER (ORDER BY e.ts_utc ROWS BETWEEN 59 PRECEDING AND CURRENT ROW),

    -- Quote pair correlation (USD-related pairs, 15min)
    CORR(
        e.rate_index - LAG(e.rate_index, 15) OVER (ORDER BY e.ts_utc),
        gu.rate_index - LAG(gu.rate_index, 15) OVER (ORDER BY gu.ts_utc)
    ) OVER (ORDER BY e.ts_utc ROWS BETWEEN 14 PRECEDING AND CURRENT ROW),

    -- Quote pair correlation (60min)
    CORR(
        e.rate_index - LAG(e.rate_index, 60) OVER (ORDER BY e.ts_utc),
        gu.rate_index - LAG(gu.rate_index, 60) OVER (ORDER BY gu.ts_utc)
    ) OVER (ORDER BY e.ts_utc ROWS BETWEEN 59 PRECEDING AND CURRENT ROW)

FROM bqx.m1_eurusd e
JOIN bqx.m1_eurgbp eg ON e.time = eg.time
JOIN bqx.m1_gbpusd gu ON e.time = gu.time
WHERE e.time >= '2024-07-01'
    AND e.time < '2024-08-01'
ORDER BY e.time;

-- Verify population
SELECT
    COUNT(*) as row_count,
    MIN(ts_utc) as earliest,
    MAX(ts_utc) as latest,
    COUNT(*) FILTER (WHERE corr_base_pairs_15min IS NOT NULL) as non_null_corr
FROM bqx.correlation_idx_eurusd
WHERE ts_utc >= '2024-07-01' AND ts_utc < '2024-08-01';
```

### 11.4 Query Optimization Examples

```sql
-- Efficient time-range query (uses partition pruning)
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    ts_utc,
    rsi_14,
    macd,
    atr_14
FROM bqx.technical_idx_eurusd
WHERE ts_utc >= '2024-10-01 00:00:00+00'
    AND ts_utc < '2024-11-01 00:00:00+00'
    AND rsi_14 > 70
ORDER BY ts_utc;

-- Expected: "Partitions scanned: 1" (only Oct 2024)

-- Join rate index and BQX features
SELECT
    ti.ts_utc,
    ti.rsi_14 AS rsi_rate,
    tb.rsi_14 AS rsi_bqx,
    ti.rsi_14 - tb.rsi_14 AS rsi_divergence,
    b.w15_bqx_return,
    b.rate_index
FROM bqx.technical_idx_eurusd ti
JOIN bqx.technical_bqx_eurusd tb ON ti.ts_utc = tb.ts_utc
JOIN bqx.bqx_eurusd b ON ti.ts_utc = b.ts_utc
WHERE ti.ts_utc >= '2024-10-01'
    AND ti.ts_utc < '2024-11-01'
    AND ABS(ti.rsi_14 - tb.rsi_14) > 20  -- Significant divergence
ORDER BY ti.ts_utc;

-- Aggregate statistics across all pairs
SELECT
    DATE_TRUNC('hour', ts_utc) AS hour,
    AVG(rsi_14) AS avg_rsi,
    STDDEV(rsi_14) AS std_rsi,
    COUNT(*) FILTER (WHERE rsi_14 > 70) AS overbought_count,
    COUNT(*) FILTER (WHERE rsi_14 < 30) AS oversold_count
FROM (
    SELECT ts_utc, rsi_14 FROM bqx.technical_idx_eurusd
    UNION ALL
    SELECT ts_utc, rsi_14 FROM bqx.technical_idx_gbpusd
    UNION ALL
    SELECT ts_utc, rsi_14 FROM bqx.technical_idx_usdjpy
    -- ... (add other pairs as needed)
) AS all_pairs
WHERE ts_utc >= '2024-10-01'
    AND ts_utc < '2024-11-01'
GROUP BY hour
ORDER BY hour;
```

### 11.5 Data Quality Checks

```sql
-- Check for missing data (gaps in time series)
WITH time_series AS (
    SELECT
        ts_utc,
        LAG(ts_utc) OVER (ORDER BY ts_utc) AS prev_ts,
        EXTRACT(EPOCH FROM (ts_utc - LAG(ts_utc) OVER (ORDER BY ts_utc))) / 60 AS gap_minutes
    FROM bqx.technical_idx_eurusd
    WHERE ts_utc >= '2024-10-01'
        AND ts_utc < '2024-11-01'
)
SELECT
    prev_ts,
    ts_utc,
    gap_minutes
FROM time_series
WHERE gap_minutes > 1  -- Gaps larger than 1 minute
ORDER BY gap_minutes DESC
LIMIT 100;

-- Check for NULL values in critical features
SELECT
    'technical_idx_eurusd' AS table_name,
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE rsi_14 IS NULL) AS rsi_null,
    COUNT(*) FILTER (WHERE macd IS NULL) AS macd_null,
    COUNT(*) FILTER (WHERE atr_14 IS NULL) AS atr_null,
    ROUND(100.0 * COUNT(*) FILTER (WHERE rsi_14 IS NULL) / COUNT(*), 2) AS rsi_null_pct
FROM bqx.technical_idx_eurusd
WHERE ts_utc >= '2024-10-01'
    AND ts_utc < '2024-11-01';

-- Check for outliers (values beyond expected ranges)
SELECT
    ts_utc,
    rsi_14,
    macd,
    atr_14
FROM bqx.technical_idx_eurusd
WHERE ts_utc >= '2024-10-01'
    AND ts_utc < '2024-11-01'
    AND (
        rsi_14 NOT BETWEEN 0 AND 100  -- RSI should be 0-100
        OR atr_14 < 0  -- ATR should be positive
        OR ABS(macd) > 0.1  -- MACD outlier threshold
    )
ORDER BY ts_utc;

-- Verify row counts match across feature types
SELECT
    'technical_idx' AS feature_type,
    COUNT(*) AS row_count
FROM bqx.technical_idx_eurusd
WHERE ts_utc >= '2024-10-01' AND ts_utc < '2024-11-01'

UNION ALL

SELECT
    'bollinger_idx',
    COUNT(*)
FROM bqx.bollinger_idx_eurusd
WHERE ts_utc >= '2024-10-01' AND ts_utc < '2024-11-01'

UNION ALL

SELECT
    'bqx',
    COUNT(*)
FROM bqx.bqx_eurusd
WHERE ts_utc >= '2024-10-01' AND ts_utc < '2024-11-01';

-- All counts should be similar (within expected variance due to lookback periods)
```

---

## Summary and Next Steps

### Current State
- **Database:** 61 GB, 6,596 tables, 28 currency pairs
- **Feature Coverage:** 8 feature types (rate-based), BQX features complete
- **Issues:** Naming inconsistency, empty correlation tables

### Required Actions

**Immediate (Week 1):**
1. Execute Phase 1.6.9 table renaming (1 hour, CRITICAL)
2. Begin parallel BQX feature builds (Technical, Statistics, Bollinger)
3. Verify renamed tables and update documentation

**Short-term (Weeks 2-3):**
4. Complete remaining BQX features (Fibonacci, Volume)
5. Populate Correlation Idx tables (currently empty)
6. Build Correlation BQX tables (MUST BE LAST)

**Medium-term (Week 4):**
7. Add advanced features (Realized Volatility, Cointegration)
8. Implement HMM Regime and Cross-Sectional features
9. Performance tuning and index optimization

**Long-term:**
10. Develop Phase 2 Feature Engineering Pipeline
11. Begin Phase 3 Model Development
12. Establish monitoring and maintenance procedures

### Success Criteria
- [ ] All 2,628 tables renamed to `*_idx_*` convention
- [ ] 2,016 new BQX feature tables created and populated
- [ ] Correlation tables populated (currently 0 rows)
- [ ] Storage expansion to ~97 GB (59% increase)
- [ ] All indexes created and verified
- [ ] Data quality checks passing (>99% completeness)
- [ ] Query performance maintained (partition pruning working)
- [ ] Documentation updated

### Risk Mitigation
- **Rename failure:** Test on single pair first, rollback plan ready
- **Storage overflow:** Monitor Aurora storage, allocate buffer
- **Performance degradation:** Index coverage, partition pruning verification
- **Data quality issues:** Implement validation checks in workers

---

**Document Version:** 1.0
**Last Updated:** 2025-11-12
**Next Review:** After Phase 1.6.9 completion
