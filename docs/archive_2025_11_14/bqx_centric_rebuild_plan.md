# BQX-Centric Feature Rebuild Plan
**Date:** 2025-11-12
**Status:** Planning Complete - Ready for Execution
**Objective:** Rebuild technical indicators, statistics, bollinger, and fibonacci features using BQX momentum values instead of rates

---

## Executive Summary

### User Directive Rationalization

The user has identified a critical architectural improvement: **create parallel BQX-centric feature tables** alongside existing rate-centric tables to enable ML model comparison between two approaches:

1. **Rate-Centric Approach** (existing): Features computed from raw forex rates
2. **BQX-Centric Approach** (new): Features computed from BQX momentum indices

### Strategic Rationale

**Why Build Both Versions?**

1. **Hypothesis Testing**: Which data representation (rates vs BQX indices) produces more predictive features?
2. **Feature Complementarity**: Rate dynamics ≠ momentum dynamics; both may provide unique signals
3. **Model Ensemble**: ML can learn which representation works best for different market regimes
4. **Normalization Benefits**: BQX indices normalize cross-pair movements, making features more comparable

**Example - RSI Comparison:**
- **RSI on Rate**: Overbought/oversold based on price movements (EUR/USD at 1.0850 vs 1.0800)
- **RSI on BQX**: Overbought/oversold based on momentum accumulation (BQX w15 = 0.0045 vs 0.0010)
- Different regimes, potentially different predictive power

---

## Current State Analysis

### Existing Rate-Centric Tables (PRESERVE)
| Feature Type | Tables | Rows | Source | Keep? |
|-------------|--------|------|--------|-------|
| statistics_features | 364 | 10.3M | M1 rates (OHLC) | ✅ YES |
| bollinger_features | 364 | 10.3M | M1 rates (close) | ✅ YES |
| fibonacci_features | 364 | 10.2M | M1 rates (OHLC) | ✅ YES |
| technical_indicators | 0 | 0 | N/A | ❌ Does not exist |

### Tables to Build (BQX-Centric)
| Feature Type | Target Name | Source | Status |
|-------------|------------|--------|--------|
| Technical Indicators | technical_bqx_{pair} | bqx.bqx_{pair}.w15_bqx_return | 🔨 To Build |
| Statistics | statistics_bqx_{pair} | bqx.bqx_{pair}.w15_bqx_return | 🔨 To Build |
| Bollinger Bands | bollinger_bqx_{pair} | bqx.bqx_{pair}.w15_bqx_return | 🔨 To Build |
| Fibonacci Levels | fibonacci_bqx_{pair} | bqx.bqx_{pair}.w15_bqx_return | 🔨 To Build |
| Correlation Matrix | correlation_bqx_{pair} | All BQX features | 🔨 Final Step |

**Naming Convention:**
- Rate-centric: `{feature_type}_features_{pair}`
- BQX-centric: `{feature_type}_bqx_{pair}`

---

## Implementation Plan

### Phase 1: Schema Creation (Est: 15 minutes)

**Create partitioned table schemas for:**
1. `technical_bqx_{pair}_{yyyy_mm}` - 336 partitions (28 pairs × 12 months)
2. `statistics_bqx_{pair}_{yyyy_mm}` - 336 partitions
3. `bollinger_bqx_{pair}_{yyyy_mm}` - 336 partitions
4. `fibonacci_bqx_{pair}_{yyyy_mm}` - 336 partitions

**Schema Structure:**
```sql
-- Example: technical_bqx_eurusd
CREATE TABLE bqx.technical_bqx_eurusd (
    ts_utc TIMESTAMP NOT NULL,

    -- RSI (Relative Strength Index on BQX)
    rsi_14 NUMERIC,
    rsi_21 NUMERIC,

    -- MACD (Moving Average Convergence Divergence on BQX)
    macd_line NUMERIC,
    macd_signal NUMERIC,
    macd_histogram NUMERIC,

    -- Stochastic Oscillator (on BQX)
    stoch_k NUMERIC,
    stoch_d NUMERIC,

    -- Momentum Indicators (on BQX)
    cci_20 NUMERIC,  -- Commodity Channel Index
    williams_r_14 NUMERIC,  -- Williams %R
    roc_12 NUMERIC,  -- Rate of Change

    -- Volatility (on BQX - momentum volatility)
    atr_14 NUMERIC,  -- Average True Range of BQX

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

### Phase 2: Worker Implementation (Est: 2 hours)

**Worker Scripts:**
1. `technical_bqx_worker.py` - Compute RSI, MACD, Stochastic, CCI, Williams %R, ROC, ATR on BQX
2. `statistics_bollinger_bqx_worker.py` - Compute mean, std dev, skewness, kurtosis, Bollinger bands on BQX
3. `fibonacci_bqx_worker.py` - Compute Fibonacci retracement/extension levels in BQX momentum space

**Data Flow:**
```
bqx.bqx_{pair} (w15_bqx_return column)
     ↓
  Technical Calculations (RSI, MACD, etc.)
     ↓
bqx.technical_bqx_{pair}_{yyyy_mm}
```

**Threading:** 8 concurrent threads, ~42 partitions per thread

### Phase 3: Execution & Monitoring (Est: 12-16 hours)

**Execution Order:**
1. **Technical BQX** (4-6 hours) - 336 partitions
2. **Statistics & Bollinger BQX** (4-6 hours) - 336 partitions
3. **Fibonacci BQX** (4-6 hours) - 336 partitions

**Total Estimated Time:** 12-18 hours for all three feature types

### Phase 4: Correlation BQX (Final Step, Est: 6-8 hours)

**After all BQX feature tables complete:**
- Build `correlation_bqx_{pair}` tables
- Compute cross-pair, cross-window, term structure correlations
- Include technical_bqx, statistics_bqx, bollinger_bqx, fibonacci_bqx in correlation matrix

---

## Data Source Clarification

### BQX Table Schema
```sql
bqx.bqx_eurusd:
- ts_utc (timestamp)
- w15_bqx_return (primary momentum metric)
- w30_bqx_return
- w45_bqx_return
- w60_bqx_return
- w75_bqx_return
```

**Primary Series:** `w15_bqx_return` (15-minute backward momentum)
**Rationale:** Highest frequency momentum signal, captures near-term dynamics

**Alternative:** Could compute features on ALL windows (w15, w30, w45, w60, w75) for multi-timeframe analysis, but starting with w15 for consistency with Phase 1 architecture.

---

## Feature Computation Examples

### Technical Indicators on BQX

**RSI on BQX (w15_bqx_return):**
```python
# Traditional RSI on price:
delta = close_price.diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = -delta.where(delta < 0, 0).rolling(14).mean()
rsi = 100 - (100 / (1 + gain/loss))

# BQX-centric RSI on momentum:
delta = w15_bqx_return.diff()  # Change in momentum
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = -delta.where(delta < 0, 0).rolling(14).mean()
rsi_bqx = 100 - (100 / (1 + gain/loss))
```

**Interpretation:**
- **Rate RSI > 70**: Price overbought
- **BQX RSI > 70**: Momentum acceleration overbought (second derivative signal)

### Statistics on BQX

**Volatility of BQX (momentum volatility):**
```python
# Rate volatility (price uncertainty):
rate_std = close_price.rolling(20).std()

# BQX volatility (momentum uncertainty):
bqx_std = w15_bqx_return.rolling(20).std()
```

**Interpretation:**
- **High rate volatility**: Large price swings
- **High BQX volatility**: Unstable momentum regime (regime transition?)

### Fibonacci on BQX

**Retracement Levels in Momentum Space:**
```python
# Rate Fibonacci (price retracements):
high_price = rate.rolling(100).max()
low_price = rate.rolling(100).min()
fib_38_2 = low_price + 0.382 * (high_price - low_price)

# BQX Fibonacci (momentum retracements):
high_momentum = w15_bqx_return.rolling(100).max()
low_momentum = w15_bqx_return.rolling(100).min()
fib_bqx_38_2 = low_momentum + 0.382 * (high_momentum - low_momentum)
```

**Interpretation:**
- **Rate Fib level**: Price support/resistance
- **BQX Fib level**: Momentum support/resistance (reversal zones)

---

## Validation & Quality Checks

### Post-Computation Validation

**For each feature table:**
1. **Row Count Check:** Should match BQX source table row counts
2. **NULL Analysis:** Expected NULLs for initial lookback periods (e.g., first 14 rows for RSI-14)
3. **Value Range Check:**
   - RSI: 0-100
   - MACD: reasonable range based on BQX scale
   - Stochastic: 0-100
4. **Correlation with Source:** Features should correlate with w15_bqx_return but not be redundant

### Sample Validation Query
```sql
-- Check technical_bqx population
SELECT
    COUNT(*) as total_rows,
    COUNT(rsi_14) as rsi_count,
    COUNT(macd_line) as macd_count,
    AVG(rsi_14) as avg_rsi,
    MIN(rsi_14) as min_rsi,
    MAX(rsi_14) as max_rsi
FROM bqx.technical_bqx_eurusd_2024_07;
```

---

## ML Comparison Framework (Phase 3)

### Feature Set A: Rate-Centric
- statistics_features (mean, std, skew, kurtosis of rates)
- bollinger_features (bands on rates)
- fibonacci_features (price retracements)
- technical_indicators (if built on rates in future)

### Feature Set B: BQX-Centric
- statistics_bqx (mean, std, skew, kurtosis of BQX)
- bollinger_bqx (bands on BQX)
- fibonacci_bqx (momentum retracements)
- technical_bqx (RSI, MACD, etc. on BQX)

### Feature Set C: Hybrid
- All rate-centric features
- All BQX-centric features
- Interaction terms (rate × BQX features)

### Model Training Experiments
1. **Train on Feature Set A** → R² score, residual analysis
2. **Train on Feature Set B** → R² score, residual analysis
3. **Train on Feature Set C** → R² score, feature importance (which features matter most?)

**Hypothesis:** Feature Set C (hybrid) will outperform A or B alone, but feature importance analysis will reveal which representation is more predictive for different target horizons.

---

## Success Criteria

### Completion Checklist
- [ ] All 336 technical_bqx partitions populated (28 pairs × 12 months)
- [ ] All 336 statistics_bqx partitions populated
- [ ] All 336 bollinger_bqx partitions populated
- [ ] All 336 fibonacci_bqx partitions populated
- [ ] All 168 correlation_bqx partitions populated (28 pairs × 6 months)
- [ ] Validation checks pass (row counts, value ranges, NULL patterns)
- [ ] Documentation complete (this file + worker logs)
- [ ] Ready for Phase 3 ML training

### Storage Impact
**Estimated Disk Usage:**
- technical_bqx: ~8 GB (10 columns × 10M rows)
- statistics_bqx: ~5 GB (6 columns × 10M rows)
- bollinger_bqx: ~4 GB (5 columns × 10M rows)
- fibonacci_bqx: ~6 GB (8 columns × 10M rows)
- correlation_bqx: ~8 GB (15 columns × 5M rows)

**Total:** ~31 GB additional storage

---

## Timeline

| Phase | Task | Duration | Start | End |
|-------|------|----------|-------|-----|
| 1 | Schema creation | 15 min | Now | +15m |
| 2 | Worker implementation | 2 hours | +15m | +2h15m |
| 3.1 | Technical BQX execution | 4-6 hours | +2h15m | +8h15m |
| 3.2 | Statistics/Bollinger BQX | 4-6 hours | +8h15m | +14h15m |
| 3.3 | Fibonacci BQX execution | 4-6 hours | +14h15m | +20h15m |
| 4 | Correlation BQX (final) | 6-8 hours | +20h15m | +28h15m |

**Total Estimated Time:** 20-28 hours (can run overnight/multi-day)

---

## Next Steps

1. ✅ Review and approve this plan
2. 🔨 Create SQL schemas for all BQX-centric tables
3. 🔨 Implement worker scripts
4. 🔨 Execute workers with monitoring
5. 🔨 Validate results
6. 🔨 Build correlation_bqx (final step)
7. 🚀 Proceed to Phase 3 ML training

---

## References

- [Feature Architecture Analysis](./feature_architecture_analysis.md) - Original hybrid approach decision
- [technical_indicators_worker_bqx.py](../scripts/ml/technical_indicators_worker_bqx.py) - Draft BQX technical worker
- [BQX Schema Analysis](./bqx_schema_analysis.md) - Database structure documentation
- [Data Completeness Report](./data_completeness_report.md) - Source data validation

---

**Author:** BQX ML Team
**Reviewed:** User directive - rebuild with BQX-centric data for ML comparison
**Status:** Ready for execution
