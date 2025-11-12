# Comprehensive Feature Development Plan
**Date:** 2025-11-12
**Version:** 2.0 - Dual Architecture (Rate + BQX)
**Status:** Planning Complete - Ready for Implementation

---

## Executive Summary

### Strategic Objective
Build **dual parallel feature architectures** to enable ML model comparison:
1. **Rate-Centric Features**: Computed from forex rates (price dynamics)
2. **BQX-Centric Features**: Computed from BQX momentum indices (momentum dynamics)

### Rationale
- **Hypothesis Testing**: Determine which data representation produces more predictive features
- **Feature Complementarity**: Rate dynamics ≠ momentum dynamics; both may provide unique signals
- **Model Ensemble**: ML can learn optimal representation per market regime
- **Normalization**: BQX indices normalize cross-pair movements for better comparability

### Total Scope
- **8 Feature Types** × 2 Architectures = 16 Feature Table Sets
- **336 Partitions** per feature type (28 pairs × 12 months)
- **Estimated Timeline**: 45-60 hours implementation + 60-80 hours computation
- **Storage Impact**: ~62 GB additional (31 GB rate + 31 GB BQX)

---

## Table of Contents
1. [Current State Analysis](#current-state-analysis)
2. [Naming Convention & Renaming Strategy](#naming-convention--renaming-strategy)
3. [Feature Type Specifications](#feature-type-specifications)
4. [Schema Definitions](#schema-definitions)
5. [Phased Implementation Plan](#phased-implementation-plan)
6. [Worker Specifications](#worker-specifications)
7. [Validation & Quality Assurance](#validation--quality-assurance)
8. [AirTable Integration](#airtable-integration)
9. [Success Criteria](#success-criteria)

---

## 1. Current State Analysis

### Existing Tables (To Be Renamed)
| Current Name | Rows | Status | New Name | Type |
|-------------|------|--------|----------|------|
| statistics_features_{pair} | 10.3M | ✅ Populated | statistics_rate_{pair} | Rate-centric |
| bollinger_features_{pair} | 10.3M | ✅ Populated | bollinger_rate_{pair} | Rate-centric |
| fibonacci_features_{pair} | 10.2M | ✅ Populated | fibonacci_rate_{pair} | Rate-centric |
| correlation_features_{pair} | 0 | ❌ Empty | correlation_rate_{pair} | Rate-centric |

### Missing Rate-Centric Tables (To Be Built)
| Table Name | Type | Status |
|-----------|------|--------|
| technical_rate_{pair} | Rate-centric | 🔨 To Build |

### BQX-Centric Tables (All To Be Built)
| Table Name | Type | Status |
|-----------|------|--------|
| technical_bqx_{pair} | BQX-centric | 🔨 To Build |
| statistics_bqx_{pair} | BQX-centric | 🔨 To Build |
| bollinger_bqx_{pair} | BQX-centric | 🔨 To Build |
| fibonacci_bqx_{pair} | BQX-centric | 🔨 To Build |
| correlation_bqx_{pair} | BQX-centric | 🔨 To Build (final step) |

---

## 2. Naming Convention & Renaming Strategy

### Naming Standard
```
{feature_type}_{data_source}_{pair}_{yyyy_mm}

feature_type: technical | statistics | bollinger | fibonacci | correlation
data_source: rate | bqx
pair: audcad | audchf | ... | usdjpy (28 pairs)
yyyy_mm: 2024_01 | 2024_02 | ... | 2025_12
```

### Examples
- **Rate-centric**: `technical_rate_eurusd_2024_07`
- **BQX-centric**: `technical_bqx_eurusd_2024_07`

### Renaming Migration Plan

**Phase 1: Rename Existing Tables (Est: 30 minutes)**
```sql
-- Statistics
ALTER TABLE bqx.statistics_features_audcad RENAME TO statistics_rate_audcad;
-- (Repeat for all 364 partitions across 28 pairs × 13 months)

-- Bollinger
ALTER TABLE bqx.bollinger_features_audcad RENAME TO bollinger_rate_audcad;

-- Fibonacci
ALTER TABLE bqx.fibonacci_features_audcad RENAME TO fibonacci_rate_audcad;

-- Correlation
ALTER TABLE bqx.correlation_features_audcad RENAME TO correlation_rate_audcad;
```

**Phase 2: Update Dependencies (Est: 15 minutes)**
- Update any existing views/materialized views
- Update worker scripts to reference new names
- Update documentation

**Total Renaming Time**: 45 minutes

---

## 3. Feature Type Specifications

### 3.1 Technical Indicators

**Purpose**: Momentum, trend, and volatility indicators

| Indicator | Windows/Params | Output Columns | Rate Source | BQX Source |
|-----------|---------------|----------------|-------------|------------|
| RSI (Relative Strength Index) | 14, 21 | rsi_14, rsi_21 | M1.close | bqx.w15_bqx_return |
| MACD (Moving Avg Convergence) | 12/26/9 | macd_line, macd_signal, macd_histogram | M1.close | bqx.w15_bqx_return |
| Stochastic Oscillator | 14/3 | stoch_k, stoch_d | M1.close | bqx.w15_bqx_return |
| CCI (Commodity Channel Index) | 20 | cci_20 | M1.close | bqx.w15_bqx_return |
| Williams %R | 14 | williams_r_14 | M1.close | bqx.w15_bqx_return |
| ROC (Rate of Change) | 12 | roc_12 | M1.close | bqx.w15_bqx_return |
| ATR (Average True Range) | 14 | atr_14 | M1 high/low/close | bqx.w15_bqx_return diff |

**Total Columns**: 10 per table

### 3.2 Statistics Features

**Purpose**: Statistical moments and distributions

| Feature | Window | Output Columns | Rate Source | BQX Source |
|---------|--------|----------------|-------------|------------|
| Mean | 20, 50 | mean_20, mean_50 | M1.close | bqx.w15_bqx_return |
| Std Deviation | 20, 50 | std_20, std_50 | M1.close | bqx.w15_bqx_return |
| Skewness | 20, 50 | skew_20, skew_50 | M1.close | bqx.w15_bqx_return |
| Kurtosis | 20, 50 | kurt_20, kurt_50 | M1.close | bqx.w15_bqx_return |
| Min/Max | 20, 50 | min_20, max_20, min_50, max_50 | M1.close | bqx.w15_bqx_return |

**Total Columns**: 12 per table

### 3.3 Bollinger Bands

**Purpose**: Volatility bands and mean reversion signals

| Feature | Params | Output Columns | Rate Source | BQX Source |
|---------|--------|----------------|-------------|------------|
| Bollinger Bands | 20/2σ | bb_upper, bb_middle, bb_lower | M1.close | bqx.w15_bqx_return |
| Bandwidth | 20 | bb_bandwidth | M1.close | bqx.w15_bqx_return |
| %B Indicator | 20 | bb_percent_b | M1.close | bqx.w15_bqx_return |

**Total Columns**: 5 per table

### 3.4 Fibonacci Levels

**Purpose**: Support/resistance based on Fibonacci ratios

| Feature | Lookback | Output Columns | Rate Source | BQX Source |
|---------|----------|----------------|-------------|------------|
| Retracement Levels | 100 | fib_23_6, fib_38_2, fib_50_0, fib_61_8 | M1 high/low | bqx.w15_bqx_return high/low |
| Extension Levels | 100 | fib_ext_127_2, fib_ext_161_8 | M1 high/low | bqx.w15_bqx_return high/low |
| Distance to Levels | 100 | dist_to_fib_38_2, dist_to_fib_61_8 | M1.close | bqx.w15_bqx_return |

**Total Columns**: 10 per table

### 3.5 Correlation Features

**Purpose**: Cross-pair and cross-window relationships

| Feature | Windows | Output Columns | Rate Source | BQX Source |
|---------|---------|----------------|-------------|------------|
| Cross-Pair Correlation | 20, 50 | corr_eur_usd_20, corr_gbp_usd_20, ... | M1.close (all pairs) | bqx.w15 (all pairs) |
| Cross-Window Correlation | w15↔w60 | corr_w15_w60, corr_w30_w60 | M1.close | bqx (all windows) |
| Residual Variance | 20 | resid_var_sys, resid_var_idio | M1.close | bqx.w15_bqx_return |
| Term Structure | 20 | term_slope, term_curvature | M1.close | bqx (all windows) |

**Total Columns**: 15 per table

---

## 4. Schema Definitions

### 4.1 Technical Indicators Schema

```sql
-- Parent table (example: technical_rate_eurusd)
CREATE TABLE bqx.technical_rate_eurusd (
    ts_utc TIMESTAMP NOT NULL,

    -- RSI (Relative Strength Index)
    rsi_14 NUMERIC,
    rsi_21 NUMERIC,

    -- MACD (Moving Average Convergence Divergence)
    macd_line NUMERIC,
    macd_signal NUMERIC,
    macd_histogram NUMERIC,

    -- Stochastic Oscillator
    stoch_k NUMERIC,
    stoch_d NUMERIC,

    -- Additional Momentum Indicators
    cci_20 NUMERIC,            -- Commodity Channel Index
    williams_r_14 NUMERIC,      -- Williams %R
    roc_12 NUMERIC,             -- Rate of Change

    -- Volatility
    atr_14 NUMERIC,             -- Average True Range

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);

-- Partition example
CREATE TABLE bqx.technical_rate_eurusd_2024_07 PARTITION OF bqx.technical_rate_eurusd
FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');

-- BQX version (same schema, different data source)
CREATE TABLE bqx.technical_bqx_eurusd (
    -- Identical schema to technical_rate_eurusd
    -- Data source: bqx.w15_bqx_return instead of M1.close
    ...
) PARTITION BY RANGE (ts_utc);
```

### 4.2 Statistics Features Schema

```sql
CREATE TABLE bqx.statistics_rate_eurusd (
    ts_utc TIMESTAMP NOT NULL,

    -- Rolling Mean
    mean_20 NUMERIC,
    mean_50 NUMERIC,

    -- Rolling Standard Deviation
    std_20 NUMERIC,
    std_50 NUMERIC,

    -- Rolling Skewness
    skew_20 NUMERIC,
    skew_50 NUMERIC,

    -- Rolling Kurtosis
    kurt_20 NUMERIC,
    kurt_50 NUMERIC,

    -- Rolling Min/Max
    min_20 NUMERIC,
    max_20 NUMERIC,
    min_50 NUMERIC,
    max_50 NUMERIC,

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

### 4.3 Bollinger Bands Schema

```sql
CREATE TABLE bqx.bollinger_rate_eurusd (
    ts_utc TIMESTAMP NOT NULL,

    -- Bollinger Bands (20 period, 2 std dev)
    bb_upper NUMERIC,
    bb_middle NUMERIC,
    bb_lower NUMERIC,

    -- Bandwidth
    bb_bandwidth NUMERIC,

    -- %B (position within bands)
    bb_percent_b NUMERIC,

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

### 4.4 Fibonacci Levels Schema

```sql
CREATE TABLE bqx.fibonacci_rate_eurusd (
    ts_utc TIMESTAMP NOT NULL,

    -- Retracement Levels (based on 100-period high/low)
    fib_23_6 NUMERIC,
    fib_38_2 NUMERIC,
    fib_50_0 NUMERIC,
    fib_61_8 NUMERIC,

    -- Extension Levels
    fib_ext_127_2 NUMERIC,
    fib_ext_161_8 NUMERIC,

    -- Distance to Key Levels
    dist_to_fib_38_2 NUMERIC,
    dist_to_fib_61_8 NUMERIC,

    -- Current Range
    fib_range_high NUMERIC,
    fib_range_low NUMERIC,

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

### 4.5 Correlation Features Schema

```sql
CREATE TABLE bqx.correlation_rate_eurusd (
    ts_utc TIMESTAMP NOT NULL,

    -- Cross-Pair Correlations (20-period rolling)
    corr_eur_usd_20 NUMERIC,
    corr_gbp_usd_20 NUMERIC,
    corr_aud_usd_20 NUMERIC,
    corr_nzd_usd_20 NUMERIC,
    corr_usd_jpy_20 NUMERIC,

    -- Cross-Window Correlations (BQX only)
    corr_w15_w60 NUMERIC,
    corr_w30_w60 NUMERIC,
    corr_w45_w60 NUMERIC,

    -- Variance Decomposition
    resid_var_systematic NUMERIC,
    resid_var_idiosyncratic NUMERIC,

    -- Term Structure (BQX momentum curve)
    term_structure_slope NUMERIC,
    term_structure_curvature NUMERIC,

    -- Covariance Matrix Metrics
    cov_determinant NUMERIC,
    cov_trace NUMERIC,
    cov_eigenvalue_max NUMERIC,

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

---

## 5. Phased Implementation Plan

### Phase 1.6.9: Table Renaming & Schema Migration (Est: 1 hour)

**Objective**: Rename existing rate-centric tables to new naming convention

**Tasks:**
1. **Rename Statistics Tables** (15 min)
   - Rename all 364 statistics_features_* partitions to statistics_rate_*
   - Update parent table references
   - Verify data integrity (row counts match)

2. **Rename Bollinger Tables** (15 min)
   - Rename all 364 bollinger_features_* partitions to bollinger_rate_*
   - Update parent table references

3. **Rename Fibonacci Tables** (15 min)
   - Rename all 364 fibonacci_features_* partitions to fibonacci_rate_*
   - Update parent table references

4. **Rename Correlation Tables** (5 min)
   - Rename all 364 correlation_features_* partitions to correlation_rate_*
   - Note: These are empty, so quick operation

5. **Update Dependencies** (10 min)
   - Update any views/materialized views
   - Update worker scripts to reference new names
   - Update documentation

**Deliverables:**
- SQL migration script: `scripts/refactor/phase_1_6_9_rename_rate_tables.sql`
- Verification script: `scripts/refactor/verify_rename_migration.py`
- Documentation update

**Success Criteria:**
- All tables renamed successfully
- Row counts match pre-rename state
- No broken dependencies

---

### Phase 1.6.10: Rate-Centric Technical Indicators (Est: 8 hours)

**Objective**: Build technical_rate_{pair} tables for all 28 pairs

**Data Source**: M1 tables (close, high, low, volume)

**Implementation:**
1. **Create Schema** (30 min)
   - Create 28 parent tables: technical_rate_{pair}
   - Create 336 partitions (28 pairs × 12 months)
   - Add indexes on ts_utc

2. **Implement Worker** (3 hours)
   - Script: `scripts/ml/technical_rate_worker.py`
   - Features: RSI, MACD, Stochastic, CCI, Williams %R, ROC, ATR
   - Threading: 8 concurrent threads
   - Progress logging

3. **Execute Backfill** (4-6 hours)
   - Process all 336 partitions
   - ~30,700 rows per partition (10.3M total)
   - Monitor progress, handle errors

4. **Validation** (30 min)
   - Verify row counts
   - Check value ranges (RSI: 0-100, etc.)
   - Validate NULL patterns

**Deliverables:**
- 336 technical_rate partitions populated
- Worker script with monitoring
- Validation report

**Success Criteria:**
- 10.3M rows populated across all partitions
- All indicators within expected value ranges
- NULL only in initial lookback periods

---

### Phase 1.6.11: BQX-Centric Technical Indicators (Est: 8 hours)

**Objective**: Build technical_bqx_{pair} tables for all 28 pairs

**Data Source**: bqx.bqx_{pair}.w15_bqx_return

**Implementation:**
- Same as Phase 1.6.10, but using BQX momentum data
- Script: `scripts/ml/technical_bqx_worker.py`
- Identical schema, different computation source

**Deliverables:**
- 336 technical_bqx partitions populated
- Worker script
- Comparison analysis (rate vs BQX technical indicators)

---

### Phase 1.6.12: BQX-Centric Statistics Features (Est: 6 hours)

**Objective**: Build statistics_bqx_{pair} tables

**Data Source**: bqx.bqx_{pair}.w15_bqx_return

**Implementation:**
1. **Create Schema** (30 min)
2. **Implement Worker** (2 hours)
   - Script: `scripts/ml/statistics_bqx_worker.py`
   - Features: mean, std, skew, kurtosis, min, max (windows: 20, 50)
3. **Execute Backfill** (3-4 hours)
4. **Validation** (30 min)

**Note**: Rate-centric version already exists (renamed statistics_rate_{pair})

---

### Phase 1.6.13: BQX-Centric Bollinger Bands (Est: 6 hours)

**Objective**: Build bollinger_bqx_{pair} tables

**Data Source**: bqx.bqx_{pair}.w15_bqx_return

**Implementation:**
- Script: `scripts/ml/bollinger_bqx_worker.py`
- Features: Bollinger bands on BQX momentum
- Interpretation: Overbought/oversold in momentum space

**Note**: Rate-centric version already exists (renamed bollinger_rate_{pair})

---

### Phase 1.6.14: BQX-Centric Fibonacci Levels (Est: 6 hours)

**Objective**: Build fibonacci_bqx_{pair} tables

**Data Source**: bqx.bqx_{pair}.w15_bqx_return

**Implementation:**
- Script: `scripts/ml/fibonacci_bqx_worker.py`
- Features: Fibonacci retracements in momentum space
- Interpretation: Support/resistance in BQX values

**Note**: Rate-centric version already exists (renamed fibonacci_rate_{pair})

---

### Phase 1.6.15: Rate-Centric Correlation Features (Est: 8 hours)

**Objective**: Populate correlation_rate_{pair} tables (currently empty)

**Data Source**: M1.close (all 28 pairs)

**Implementation:**
1. **Implement Worker** (3 hours)
   - Script: `scripts/ml/correlation_rate_worker.py`
   - Features: Cross-pair correlations, term structure
2. **Execute Backfill** (4-6 hours)
   - 168 partitions (28 pairs × 6 months relevant data)
3. **Validation** (1 hour)

---

### Phase 1.6.16: BQX-Centric Correlation Features (Est: 8 hours)

**Objective**: Build correlation_bqx_{pair} tables (FINAL STEP)

**Data Source**: bqx.bqx_{pair} (all windows: w15, w30, w45, w60, w75)

**Implementation:**
- Script: `scripts/ml/correlation_bqx_worker.py`
- Features:
  - Cross-pair BQX correlations (EUR momentum ↔ USD momentum)
  - Cross-window term structure (w15 ↔ w60 correlation)
  - Variance decomposition (systematic vs idiosyncratic momentum)

**Critical**: This is the final step after all other BQX features complete

---

## 6. Worker Specifications

### 6.1 Worker Template Structure

```python
#!/usr/bin/env python3
"""
{Feature Type} Worker ({Rate|BQX}-Centric) - Phase 1.6.X

Computes {feature_type} features on {rate|BQX momentum} values.
Data Source: {M1 tables | bqx.bqx_{pair}}
Storage: bqx.{feature_type}_{rate|bqx}_{pair}
Estimated Time: X-Y hours (336 partitions / 8 threads)
"""

import psycopg2
import numpy as np
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import logging

# Database configuration
DB_CONFIG = {
    'host': 'trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com',
    'port': 5432,
    'database': 'bqx',
    'user': 'postgres',
    'password': 'BQX_Aurora_2025_Secure'
}

# 28 currency pairs
CURRENCY_PAIRS = [
    'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
    'cadchf', 'cadjpy', 'chfjpy',
    'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
    'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
    'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
    'usdcad', 'usdchf', 'usdjpy'
]

# Months to process
MONTHS = [
    '2024_01', '2024_02', '2024_03', '2024_04', '2024_05', '2024_06',
    '2024_07', '2024_08', '2024_09', '2024_10', '2024_11', '2024_12'
]

# Thread-safe progress tracking
progress_lock = threading.Lock()
partitions_completed = 0
total_partitions = len(CURRENCY_PAIRS) * len(MONTHS)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'/tmp/{feature_type}_{data_source}_worker.log'),
        logging.StreamHandler()
    ]
)

def compute_features(df):
    """
    Compute {feature_type} features on input DataFrame

    Args:
        df: DataFrame with {ts_utc, close/w15_bqx_return} columns

    Returns:
        DataFrame with computed features
    """
    # Feature computation logic here
    pass

def process_partition(pair, month):
    """Process a single partition"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)

        # Load source data
        query = f"""
        SELECT ts_utc, {source_column}
        FROM bqx.{source_table}_{pair}_{month}
        ORDER BY ts_utc
        """

        df = pd.read_sql(query, conn)

        # Compute features
        features = compute_features(df)

        # Insert into target table
        insert_query = f"""
        INSERT INTO bqx.{feature_type}_{data_source}_{pair}_{month}
        (ts_utc, {feature_columns})
        VALUES (%s, {value_placeholders})
        ON CONFLICT (ts_utc) DO NOTHING
        """

        with conn.cursor() as cur:
            for _, row in features.iterrows():
                cur.execute(insert_query, tuple(row))

        conn.commit()
        conn.close()

        # Update progress
        global partitions_completed
        with progress_lock:
            partitions_completed += 1
            progress_pct = (partitions_completed / total_partitions) * 100
            logging.info(f"✅ {pair}_{month} complete | Progress: {partitions_completed}/{total_partitions} ({progress_pct:.1f}%)")

        return True

    except Exception as e:
        logging.error(f"❌ Error processing {pair}_{month}: {e}")
        return False

def main():
    start_time = datetime.now()
    logging.info(f"Starting {feature_type}_{data_source} worker")
    logging.info(f"Total partitions: {total_partitions}")

    # Create list of (pair, month) tuples
    partitions = [(pair, month) for pair in CURRENCY_PAIRS for month in MONTHS]

    # Process with thread pool
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(process_partition, pair, month) for pair, month in partitions]

        for future in as_completed(futures):
            future.result()

    elapsed = datetime.now() - start_time
    logging.info(f"✅ All partitions complete in {elapsed}")

if __name__ == '__main__':
    main()
```

### 6.2 Monitoring Script Template

```bash
#!/bin/bash
# Monitor {feature_type}_{data_source} worker progress

LOG_FILE="/tmp/{feature_type}_{data_source}_worker.log"

echo "=== {Feature Type} {Rate|BQX} Worker Monitor ==="
echo

# Show last 20 log lines
echo "Recent Progress:"
tail -20 "$LOG_FILE"

echo
echo "=== Database Status ==="

PGPASSWORD='BQX_Aurora_2025_Secure' psql \
  -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres \
  -d bqx \
  -c "
SELECT
  COUNT(*) as partitions_populated,
  SUM(n_live_tup) as total_rows
FROM pg_stat_user_tables
WHERE schemaname = 'bqx'
  AND relname LIKE '{feature_type}_{data_source}_%'
  AND n_live_tup > 0;
"
```

---

## 7. Validation & Quality Assurance

### 7.1 Validation Checklist (Per Feature Type)

**Row Count Validation:**
```sql
-- Verify row counts match source tables
SELECT
  '{feature_type}_{data_source}' as feature_type,
  COUNT(DISTINCT relname) as partition_count,
  SUM(n_live_tup) as total_rows,
  AVG(n_live_tup) as avg_rows_per_partition
FROM pg_stat_user_tables
WHERE schemaname = 'bqx'
  AND relname LIKE '{feature_type}_{data_source}_%'
  AND relname ~ '_[0-9]{4}_[0-9]{2}';

-- Expected: 336 partitions, ~10.3M total rows
```

**Value Range Validation:**
```sql
-- Technical indicators value range check
SELECT
  'rsi_14' as indicator,
  MIN(rsi_14) as min_value,
  MAX(rsi_14) as max_value,
  AVG(rsi_14) as avg_value
FROM bqx.technical_{data_source}_eurusd
WHERE rsi_14 IS NOT NULL;

-- Expected: RSI between 0-100, MACD reasonable range, etc.
```

**NULL Pattern Validation:**
```sql
-- Check NULL distribution (should only be in initial lookback periods)
SELECT
  COUNT(*) as total_rows,
  COUNT(rsi_14) as non_null_rsi,
  COUNT(*) - COUNT(rsi_14) as null_rsi,
  (COUNT(*) - COUNT(rsi_14))::FLOAT / COUNT(*) * 100 as null_pct
FROM bqx.technical_{data_source}_eurusd_2024_07;

-- Expected: ~14 rows NULL for RSI-14 (initial lookback)
```

### 7.2 Cross-Architecture Comparison

```sql
-- Compare rate vs BQX feature distributions
SELECT
  'rate' as source,
  AVG(rsi_14) as avg_rsi,
  STDDEV(rsi_14) as std_rsi
FROM bqx.technical_rate_eurusd
WHERE rsi_14 IS NOT NULL

UNION ALL

SELECT
  'bqx' as source,
  AVG(rsi_14),
  STDDEV(rsi_14)
FROM bqx.technical_bqx_eurusd
WHERE rsi_14 IS NOT NULL;

-- Analyze: Do rate and BQX RSI have different distributions?
```

---

## 8. AirTable Integration

### 8.1 Phase Structure

**New Phase: Phase 1.6.9-1.6.16 (Feature Architecture Dual Build)**

### 8.2 Stages to Add

| Stage ID | Stage Name | Duration | Dependencies |
|----------|-----------|----------|--------------|
| 1.6.9 | Table Renaming & Migration | 1h | None |
| 1.6.10 | Technical Rate Build | 8h | 1.6.9 complete |
| 1.6.11 | Technical BQX Build | 8h | 1.6.9 complete |
| 1.6.12 | Statistics BQX Build | 6h | 1.6.9 complete |
| 1.6.13 | Bollinger BQX Build | 6h | 1.6.9 complete |
| 1.6.14 | Fibonacci BQX Build | 6h | 1.6.9 complete |
| 1.6.15 | Correlation Rate Build | 8h | 1.6.9 complete |
| 1.6.16 | Correlation BQX Build | 8h | 1.6.11-1.6.14 complete |

**Total Duration**: 51 hours (can run some in parallel)

### 8.3 Tasks per Stage (Example: Stage 1.6.10)

| Task ID | Task Name | Hours | Status |
|---------|-----------|-------|--------|
| TSK-1.6.10.1 | Create technical_rate schemas (28 parent + 336 partitions) | 0.5 | Todo |
| TSK-1.6.10.2 | Implement technical_rate_worker.py | 3 | Todo |
| TSK-1.6.10.3 | Execute technical_rate backfill (336 partitions) | 4.5 | Todo |
| TSK-1.6.10.4 | Validate technical_rate data quality | 0.5 | Todo |

---

## 9. Success Criteria

### 9.1 Completion Checklist

**Table Renaming:**
- [ ] All statistics_features_* renamed to statistics_rate_*
- [ ] All bollinger_features_* renamed to bollinger_rate_*
- [ ] All fibonacci_features_* renamed to fibonacci_rate_*
- [ ] All correlation_features_* renamed to correlation_rate_*

**Rate-Centric Tables:**
- [ ] technical_rate_{pair} - 336 partitions, 10.3M rows
- [ ] statistics_rate_{pair} - 336 partitions, 10.3M rows (renamed, verified)
- [ ] bollinger_rate_{pair} - 336 partitions, 10.3M rows (renamed, verified)
- [ ] fibonacci_rate_{pair} - 336 partitions, 10.2M rows (renamed, verified)
- [ ] correlation_rate_{pair} - 168 partitions, ~5M rows

**BQX-Centric Tables:**
- [ ] technical_bqx_{pair} - 336 partitions, 10.3M rows
- [ ] statistics_bqx_{pair} - 336 partitions, 10.3M rows
- [ ] bollinger_bqx_{pair} - 336 partitions, 10.3M rows
- [ ] fibonacci_bqx_{pair} - 336 partitions, 10.2M rows
- [ ] correlation_bqx_{pair} - 168 partitions, ~5M rows

**Quality Assurance:**
- [ ] All value ranges validated (RSI: 0-100, etc.)
- [ ] NULL patterns correct (only initial lookback periods)
- [ ] Row counts match expected values
- [ ] Cross-architecture comparison complete

### 9.2 ML Readiness Criteria

- [ ] All 10 feature types available (5 rate + 5 BQX)
- [ ] Feature comparison analysis complete
- [ ] Documentation updated
- [ ] Ready for Phase 3 ML training experiments

---

## Timeline Summary

| Phase | Task | Duration | Can Parallelize? |
|-------|------|----------|------------------|
| 1.6.9 | Table renaming | 1h | No |
| 1.6.10 | Technical Rate | 8h | Yes (with BQX tasks) |
| 1.6.11 | Technical BQX | 8h | Yes (with Rate tasks) |
| 1.6.12 | Statistics BQX | 6h | Yes |
| 1.6.13 | Bollinger BQX | 6h | Yes |
| 1.6.14 | Fibonacci BQX | 6h | Yes |
| 1.6.15 | Correlation Rate | 8h | Yes |
| 1.6.16 | Correlation BQX | 8h | No (depends on 1.6.11-1.6.14) |

**Sequential Execution**: 51 hours
**Parallel Execution** (4 workers): ~20-25 hours
**Recommended**: 2-3 days with overnight runs

---

## References

- [BQX-Centric Rebuild Plan](./bqx_centric_rebuild_plan.md) - Original BQX-only approach
- [Feature Architecture Analysis](./feature_architecture_analysis.md) - Hybrid approach rationale
- [Database Schema Documentation](./bqx_schema_analysis.md) - Current database structure

---

**Status**: Ready for implementation
**Next Step**: Create Stage 1.6.9 migration scripts and begin table renaming
**Approval Required**: User confirmation to proceed with dual architecture build
