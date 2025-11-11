# Track 1: Unblocked Features Specification - Stage 1.6.3

**Date:** 2025-11-11
**Status:** Specification Complete - Ready for Implementation
**Dependencies:** M1 tables with rate_index (Phase 1.5 COMPLETE)
**Blocks:** None - can execute in parallel with OHLC backfill and REG backfill

---

## Executive Summary

Track 1 implements **66 features** that have NO dependencies on OHLC index columns (high_index, low_index, open_index). These features can be computed immediately using existing M1 table fields and will execute in parallel with ongoing backfills.

**Key Characteristics:**
- ✅ Zero blocking dependencies
- ✅ Uses existing M1 fields only (rate, rate_index, volume, bid/ask/spread, time)
- ✅ Can run parallel with OHLC backfill (40% CPU available)
- ✅ Expected completion: 18 hours wall time
- ✅ 59% of Phase 2 features (66/111)

---

## Feature Breakdown

### Category 1: Volume Features (10 features)

**Data Source:** `M1.volume` field (currently unused but exists in all M1 tables)

| Feature | Formula | Normalization | Description |
|---------|---------|---------------|-------------|
| `w15_volume_ratio` | `volume / rolling_mean(volume, 15min)` | Ratio (dimensionless) | Short-term volume spike detector |
| `w30_volume_ratio` | `volume / rolling_mean(volume, 30min)` | Ratio (dimensionless) | Medium-term volume trend |
| `w60_volume_ratio` | `volume / rolling_mean(volume, 60min)` | Ratio (dimensionless) | Long-term volume trend |
| `volume_spike` | `1 if volume > 2 × rolling_mean(volume, 60min) else 0` | Binary (0/1) | Abnormal volume event |
| `volume_trend_slope` | `linregress(volume[-60:]).slope` | Slope (units/min) | Volume acceleration |
| `cumulative_volume_60min` | `sum(volume[-60:])` | Count | Total activity |
| `volume_weighted_return` | `Σ(return_i × volume_i) / Σ(volume_i)` | Percentage | VWAP-adjusted return |
| `volume_price_correlation_60min` | `corr(volume[-60:], abs(return)[-60:])` | Correlation (-1 to +1) | Volume-volatility relationship |
| `relative_volume_position` | `(volume - min_60) / (max_60 - min_60)` | Ratio (0-1) | Normalized volume percentile |
| `volume_volatility_60min` | `stdev(volume[-60:])` | StdDev | Volume consistency |

**Implementation Notes:**
- All features computed per M1 row (minute-level granularity)
- Rolling windows use preceding data (causal, no lookahead)
- `return_i` = `(rate_i - rate_{i-1}) / rate_{i-1}` (already available or trivially computed)

**Storage Table:** `bqx.volume_features_{pair}` (28 tables, one per currency pair)

---

### Category 2: Time Features (8 features)

**Data Source:** `M1.time` field (timestamp of minute candle)

| Feature | Formula | Range | Description |
|---------|---------|-------|-------------|
| `hour_sin` | `sin(2π × hour / 24)` | [-1, +1] | Cyclical hour (continuous) |
| `hour_cos` | `cos(2π × hour / 24)` | [-1, +1] | Cyclical hour (continuous) |
| `day_of_week_sin` | `sin(2π × dow / 7)` | [-1, +1] | Cyclical day (continuous) |
| `day_of_week_cos` | `cos(2π × dow / 7)` | [-1, +1] | Cyclical day (continuous) |
| `session_overlap` | `1 if 13:00 ≤ hour_utc < 16:00 else 0` | Binary (0/1) | London-NY overlap (high liquidity) |
| `is_weekend_approach` | `1 if dow=4 AND hour ≥ 16 else 0` | Binary (0/1) | Friday close (position unwinding) |
| `minutes_since_market_open` | `(hour × 60 + minute) mod 1440` | [0, 1439] | Time within 24h cycle |
| `trading_session` | Categorical: `{0: Asian, 1: European, 2: US, 3: Overlap}` | {0,1,2,3} | Active market session |

**Cyclical Encoding Rationale:**
- Prevents discontinuity: 23:59 and 00:00 are 1 minute apart, but 1439 units apart numerically
- Using sin/cos: `distance(23:59, 00:00) ≈ 0` (continuous representation)
- ML model can learn periodic patterns (e.g., volatility spikes at session opens)

**Trading Session Rules:**
- Asian: 00:00-08:00 UTC (Tokyo, Sydney)
- European: 08:00-13:00 UTC (London)
- US: 13:00-21:00 UTC (New York)
- Overlap: 13:00-16:00 UTC (London+NY, highest liquidity)

**Storage Table:** `bqx.time_features_{pair}` (28 tables)

---

### Category 3: Currency Strength Indices (3 features)

**Data Source:** All 28 M1 tables (synthesize indices from existing pairs)

| Feature | Formula | Description |
|---------|---------|-------------|
| `base_currency_index` | Weighted avg of all pairs with base currency | EUR strength for EURUSD |
| `quote_currency_index` | Weighted avg of all pairs with quote currency | USD strength for EURUSD |
| `currency_index_differential` | `base_currency_index - quote_currency_index` | Relative strength |

**Calculation Method:**

For **EURUSD** (base=EUR, quote=USD):

```python
# EUR Index (base currency strength)
eur_pairs = ['euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd']
eur_index = weighted_avg([m1_{pair}.rate_index for pair in eur_pairs])

# USD Index (quote currency strength - synthetic DXY)
usd_pairs = ['audusd', 'eurusd', 'gbpusd', 'nzdusd', 'usdcad', 'usdchf', 'usdjpy']
usd_index = weighted_avg([
    1 / m1_audusd.rate_index,  # Invert AUD/USD to get USD/AUD
    1 / m1_eurusd.rate_index,  # Invert EUR/USD to get USD/EUR
    1 / m1_gbpusd.rate_index,
    1 / m1_nzdusd.rate_index,
    m1_usdcad.rate_index,      # Already USD/CAD
    m1_usdchf.rate_index,      # Already USD/CHF
    m1_usdjpy.rate_index       # Already USD/JPY
])

# Differential (positive = EUR strengthening vs USD)
currency_index_differential = eur_index - usd_index
```

**Weighting Scheme:** Equal weighting (1/N) for simplicity. Future enhancement: use liquidity-weighted average.

**Normalization:** All indices use rate_index (~100 scale), inherently normalized.

**Storage Table:** `bqx.currency_indices` (1 table, 8 currency indices × 28 pairs = 224 index values per minute)

---

### Category 4: Spread & Microstructure Features (20 features)

**Data Source:** M1 bid/ask/spread fields (16 fields available: bid_open/high/low/close, ask_*, spread_*)

| Feature | Formula | Normalization | Description |
|---------|---------|---------------|-------------|
| `spread_mean_60min` | `mean(spread_close[-60:])` | Absolute (pips) | Average spread |
| `spread_volatility_60min` | `stdev(spread_close[-60:])` | StdDev (pips) | Spread consistency |
| `spread_pct_of_rate` | `(spread_close / rate) × 100` | Percentage | Normalized spread cost |
| `spread_trend_slope` | `linregress(spread_close[-60:]).slope` | Slope (pips/min) | Spread widening/tightening |
| `spread_spike` | `1 if spread > 2 × spread_mean_60min else 0` | Binary (0/1) | Abnormal spread event |
| `bid_ask_imbalance` | `(ask_volume - bid_volume) / (ask_volume + bid_volume)` | Ratio [-1, +1] | Order flow direction (if volume available) |
| `effective_spread` | `2 × abs(mid_price - trade_price) / mid_price × 100` | Percentage | Realized trading cost |
| `quoted_spread` | `(ask_close - bid_close) / mid_price × 100` | Percentage | Posted spread |
| `realized_spread` | `sign(trade) × (mid_price_t+5 - trade_price) / trade_price × 100` | Percentage | Maker profitability |
| `price_impact` | `abs(trade_price - mid_price_t-1) / mid_price_t-1 × 100` | Percentage | Market impact |
| `roll_cost` | `(bid_close + ask_close) / 2 - close` | Absolute (pips) | Mid-price vs close deviation |
| `bid_depth` | From order book if available, else NaN | Absolute | Liquidity at best bid |
| `ask_depth` | From order book if available, else NaN | Absolute | Liquidity at best ask |
| `depth_imbalance` | `(ask_depth - bid_depth) / (ask_depth + bid_depth)` | Ratio [-1, +1] | Book pressure |
| `spread_range_60min` | `max(spread[-60:]) - min(spread[-60:])` | Absolute (pips) | Spread volatility range |
| `spread_percentile_60min` | Percentile of current spread in 60min window | [0, 100] | Spread ranking |
| `mid_price_volatility` | `stdev((bid_close + ask_close) / 2, 60min)` | StdDev | True price volatility |
| `tick_direction` | `sign(close - close_{t-1})` | {-1, 0, +1} | Price direction |
| `tick_rule` | `sign(trade_price - mid_price)` | {-1, +1} | Trade initiator (buy/sell) |
| `order_flow_toxicity` | Volume-weighted price impact metric | Ratio | Adverse selection risk |

**Note:** Some features (bid/ask_volume, order book depth) may require additional data collection if not available in M1 tables. Use NaN/NULL if missing.

**Storage Table:** `bqx.spread_features_{pair}` (28 tables)

---

### Category 5: Cross-Pair Correlation Features (15 features)

**Data Source:** Existing MV data (13 related pairs per target pair already filtered)

**For EURUSD (base=EUR, quote=USD), related pairs:**
- EUR-pairs: EURAUD, EURCAD, EURCHF, EURGBP, EURJPY, EURNZD (6 pairs)
- USD-pairs: AUDUSD, GBPUSD, NZDUSD, USDCAD, USDCHF, USDJPY (6 pairs)
- Direct related: GBPUSD (EUR and USD overlap) (1 pair)

| Feature | Formula | Range | Description |
|---------|---------|-------|-------------|
| `corr_base_pairs_15min` | `mean(corr(target_return, base_pair_return, 15min))` | [-1, +1] | Short-term EUR-pair correlation |
| `corr_base_pairs_60min` | `mean(corr(target_return, base_pair_return, 60min))` | [-1, +1] | Long-term EUR-pair correlation |
| `corr_quote_pairs_15min` | `mean(corr(target_return, quote_pair_return, 15min))` | [-1, +1] | Short-term USD-pair correlation |
| `corr_quote_pairs_60min` | `mean(corr(target_return, quote_pair_return, 60min))` | [-1, +1] | Long-term USD-pair correlation |
| `relative_strength_vs_base_pairs` | `(target_return - mean(base_returns)) / stdev(base_returns)` | Z-score | EURUSD performance vs EUR-pairs |
| `relative_strength_vs_quote_pairs` | `(target_return - mean(quote_returns)) / stdev(quote_returns)` | Z-score | EURUSD performance vs USD-pairs |
| `base_pair_divergence` | `stdev([base_pair_returns])` | StdDev | EUR-pair disagreement |
| `quote_pair_divergence` | `stdev([quote_pair_returns])` | StdDev | USD-pair disagreement |
| `triangular_arb_divergence` | `eurusd_rate - (eurgbp_rate × gbpusd_rate)` | Absolute | Arbitrage opportunity |
| `cross_pair_momentum_divergence` | Categorical: target up, peers flat/down | {-1,0,+1} | Divergence signal |
| `correlation_stability` | `stdev(corr_60min[-4h:])` | StdDev | Correlation regime stability |
| `lead_lag_indicator` | Cross-correlation at lag -5 to +5 minutes | [-1, +1] | Which pair leads |
| `cointegration_residual` | `target - β × base_pair` (from OLS) | Absolute | Mean reversion signal |
| `pair_spread_z_score` | `(pair_spread - mean_spread) / stdev_spread` | Z-score | Pair trading signal |
| `cross_pair_volatility_ratio` | `target_volatility / mean(peer_volatility)` | Ratio | Relative volatility |

**Implementation Notes:**
- `target_return` = `(rate_index_t - rate_index_{t-1}) / rate_index_{t-1}` (already exists in BQX/REG tables or trivially computed)
- Related pairs identified from MV currency filtering (already implemented in Phase 1.5)
- Compute per target pair (28 MVs, each with 13 related pairs)

**Storage Table:** `bqx.correlation_features_{pair}` (28 tables)

---

### Category 6: Higher-Order Statistics (5 features)

**Data Source:** `M1.rate_index` (compute statistics on returns)

| Feature | Formula | Description |
|---------|---------|-------------|
| `skewness_60min` | `skew(returns[-60:])` | Distribution asymmetry |
| `kurtosis_60min` | `kurt(returns[-60:])` | Tail heaviness (crash risk) |
| `median_absolute_deviation_60min` | `median(abs(returns - median(returns)))` | Robust volatility |
| `entropy_60min` | `-Σ(p_i × log(p_i))` where p_i = histogram bins | Randomness measure |
| `autocorrelation_lag1` | `corr(returns[t], returns[t-1])` | Serial correlation |

**Return Calculation:**
```python
returns = (rate_index[t] - rate_index[t-1]) / rate_index[t-1]
# Result: percentage return (dimensionless, normalized)
```

**Statistical Interpretations:**
- **Skewness:**
  - Positive (> 0): More frequent small losses, occasional large gains (bullish tail)
  - Negative (< 0): More frequent small gains, occasional large losses (crash risk)
  - Near 0: Symmetric distribution

- **Kurtosis:**
  - High (> 3): Fat tails, frequent extreme moves (high crash risk)
  - Low (< 3): Thin tails, fewer outliers
  - Normal distribution: kurtosis = 3

- **Entropy:**
  - High entropy: Random, unpredictable price action
  - Low entropy: Structured, trending price action

- **Autocorrelation:**
  - Positive: Momentum (trends continue)
  - Negative: Mean reversion (reversals likely)
  - Near 0: Random walk

**Storage Table:** `bqx.statistics_features_{pair}` (28 tables)

---

### Category 7: Bollinger Bands (5 features)

**Data Source:** `M1.rate_index` (NOT M1.rate - uses normalized index)

| Feature | Formula | Description |
|---------|---------|-------------|
| `bollinger_upper_20` | `SMA(rate_index, 20) + 2 × STDEV(rate_index, 20)` | Upper band (index points) |
| `bollinger_lower_20` | `SMA(rate_index, 20) - 2 × STDEV(rate_index, 20)` | Lower band (index points) |
| `bollinger_middle_20` | `SMA(rate_index, 20)` | Middle band (20-period MA) |
| `bollinger_width_20` | `(bollinger_upper - bollinger_lower) / bollinger_middle × 100` | Bandwidth (percentage) |
| `bollinger_percent_b` | `(rate_index - bollinger_lower) / (bollinger_upper - bollinger_lower)` | Position in band (0-1) |

**Why rate_index (not rate):**
- EURUSD rate ~1.10 → Bollinger width ~0.005 (0.5% of price)
- USDJPY rate ~150 → Bollinger width ~0.75 (0.5% of price)
- **Not comparable!** 0.005 vs 0.75 are 150× different scales.

**With rate_index (~100):**
- EURUSD rate_index ~100 → Bollinger width ~0.5 index points (0.5% of index)
- USDJPY rate_index ~100 → Bollinger width ~0.5 index points (0.5% of index)
- **Directly comparable!** Same volatility = same bandwidth.

**Bollinger Percent B Interpretation:**
- %B > 1: Price above upper band (overbought)
- %B < 0: Price below lower band (oversold)
- %B = 0.5: Price at middle band (neutral)

**Storage Table:** `bqx.bollinger_features_{pair}` (28 tables)

---

## Normalization Summary

| Feature Category | Normalization Method | Rationale |
|------------------|----------------------|-----------|
| Volume | Ratios (volume / MA volume) | Dimensionless, comparable |
| Time | Cyclical encoding (sin/cos) | Continuous, periodic |
| Currency Indices | Computed from rate_index (~100) | Inherently normalized |
| Spread | Percentage of rate | Normalized to price |
| Correlation | Inherent (-1 to +1) | Already dimensionless |
| Statistics | Computed on percentage returns | Dimensionless |
| Bollinger | Computed on rate_index (~100) | Cross-pair comparable |

**Result:** All 66 features are cross-pair comparable, scale-invariant, and ML-ready.

---

## Storage Schema

### Table Structure

Each feature category gets its own set of partitioned tables:

```sql
-- Example: Volume features for EURUSD
CREATE TABLE bqx.volume_features_eurusd (
    ts_utc TIMESTAMPTZ NOT NULL,
    w15_volume_ratio DOUBLE PRECISION,
    w30_volume_ratio DOUBLE PRECISION,
    w60_volume_ratio DOUBLE PRECISION,
    volume_spike INTEGER,  -- 0 or 1
    volume_trend_slope DOUBLE PRECISION,
    cumulative_volume_60min BIGINT,
    volume_weighted_return DOUBLE PRECISION,
    volume_price_correlation_60min DOUBLE PRECISION,
    relative_volume_position DOUBLE PRECISION,
    volume_volatility_60min DOUBLE PRECISION,
    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);

-- Monthly partitions (same as M1, BQX, REG)
CREATE TABLE bqx.volume_features_eurusd_2024_07 PARTITION OF bqx.volume_features_eurusd
    FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');
-- ... 12 partitions per pair
```

**Total Tables:**
- Volume features: 28 parent + 336 partitions = 364 tables
- Time features: 28 parent + 336 partitions = 364 tables
- Currency indices: 1 parent + 12 partitions = 13 tables
- Spread features: 28 parent + 336 partitions = 364 tables
- Correlation features: 28 parent + 336 partitions = 364 tables
- Statistics features: 28 parent + 336 partitions = 364 tables
- Bollinger features: 28 parent + 336 partitions = 364 tables

**Total: 197 parent tables + 2,197 partition tables = 2,394 tables**

---

## Worker Architecture

### Worker 1: Volume Features Worker
- **File:** `scripts/ml/volume_features_worker.py`
- **Input:** M1 tables (volume column)
- **Output:** `bqx.volume_features_{pair}` tables
- **Parallelism:** 8 threads (process 8 pairs simultaneously)
- **Estimated time:** 4 hours (336 partitions × 28 pairs / 8 threads)

### Worker 2: Time & Spread Features Worker
- **File:** `scripts/ml/time_spread_features_worker.py`
- **Input:** M1 tables (time, bid/ask/spread columns)
- **Output:** `bqx.time_features_{pair}` + `bqx.spread_features_{pair}` tables
- **Parallelism:** 8 threads
- **Estimated time:** 5 hours (more complex calculations)

### Worker 3: Currency Indices Worker
- **File:** `scripts/ml/currency_indices_worker.py`
- **Input:** All 28 M1 tables (rate_index)
- **Output:** `bqx.currency_indices` table
- **Parallelism:** Sequential (requires all pairs)
- **Estimated time:** 2 hours (only 12 partitions, but complex joins)

### Worker 4: Statistics & Bollinger Worker
- **File:** `scripts/ml/statistics_bollinger_worker.py`
- **Input:** M1 tables (rate_index)
- **Output:** `bqx.statistics_features_{pair}` + `bqx.bollinger_features_{pair}` tables
- **Parallelism:** 8 threads
- **Estimated time:** 5 hours (higher-order stats are compute-intensive)

### Worker 5: Correlation Features Worker
- **File:** `scripts/ml/correlation_features_worker.py`
- **Input:** All 28 M1 tables (rate_index for rolling correlations)
- **Output:** `bqx.correlation_features_{pair}` tables
- **Parallelism:** 4 threads (requires multi-pair joins)
- **Estimated time:** 6 hours (complex cross-pair calculations)

**Total Track 1 Time:** 4 + 5 + 2 + 5 + 6 = **22 hours sequential**, **~18 hours parallel** (some workers can overlap)

---

## Parallel Execution Strategy

```
Timeline (wall time):
Hour 0-4:    Volume Worker (8 threads, 30% CPU)
             + REG backfill (50% CPU) [ongoing]
             + OHLC backfill (15% CPU) [finishing]
             = 95% CPU utilization

Hour 4-9:    Time/Spread Worker (8 threads, 35% CPU)
             + REG backfill (50% CPU)
             = 85% CPU utilization

Hour 9-11:   Currency Indices Worker (1 thread, 20% CPU)
             + REG backfill (50% CPU)
             = 70% CPU utilization

Hour 11-16:  Statistics/Bollinger Worker (8 threads, 30% CPU)
             + Correlation Worker (4 threads, 20% CPU) [start at Hour 11]
             + REG backfill (50% CPU)
             = 100% CPU utilization

Hour 16-18:  Correlation Worker continues (20% CPU)
             + REG backfill (50% CPU)
             = 70% CPU utilization

Total: 18 hours wall time
```

---

## Implementation Checklist

- [ ] Create storage schema SQL script (Stage 1.6.2)
- [ ] Implement Worker 1: Volume Features
- [ ] Implement Worker 2: Time & Spread Features
- [ ] Implement Worker 3: Currency Indices
- [ ] Implement Worker 4: Statistics & Bollinger
- [ ] Implement Worker 5: Correlation Features
- [ ] Execute all workers in parallel
- [ ] Verify feature values (sanity checks)
- [ ] Document feature importance (preliminary)
- [ ] Update Phase 2 readiness status

---

## Verification Queries

### Check Volume Features
```sql
SELECT ts_utc, w15_volume_ratio, w60_volume_ratio, volume_spike
FROM bqx.volume_features_eurusd_2024_07
ORDER BY ts_utc
LIMIT 10;

-- Expected: volume_ratio ~1.0 (ratio), volume_spike in {0, 1}
```

### Check Time Features
```sql
SELECT ts_utc, hour_sin, hour_cos, session_overlap, trading_session
FROM bqx.time_features_eurusd_2024_07
ORDER BY ts_utc
LIMIT 10;

-- Expected: hour_sin/cos in [-1, +1], session_overlap in {0, 1}, trading_session in {0,1,2,3}
```

### Check Bollinger Bands
```sql
SELECT ts_utc, bollinger_upper_20, bollinger_lower_20, bollinger_percent_b
FROM bqx.bollinger_features_eurusd_2024_07
ORDER BY ts_utc
LIMIT 10;

-- Expected: bollinger bands ~100 ± 2 (index scale), %B in [0, 1] usually
```

### Check Currency Indices
```sql
SELECT ts_utc, eur_index, usd_index, currency_index_differential
FROM bqx.currency_indices_2024_07
ORDER BY ts_utc
LIMIT 10;

-- Expected: indices ~100 (normalized), differential near 0 (balanced)
```

---

## Success Criteria

1. ✅ All 66 features computed for all 28 pairs
2. ✅ All 336 partitions × 7 feature categories = 2,352 partition tables populated
3. ✅ Feature values within expected ranges (no NaN/Inf except at partition starts)
4. ✅ Normalization validated (cross-pair values comparable)
5. ✅ Zero blocking dependencies on OHLC index (high/low/open_index)
6. ✅ Storage impact < 15 GB (manageable)
7. ✅ Computation time ≤ 18 hours (parallel execution)
8. ✅ Features ready for Phase 2 (Stage 2.1/2.3 unblocked portions)

---

## Next Steps After Track 1 Completion

1. **Verify OHLC Index Backfill** (Track 2 - Stage 1.6.1)
   - Check OHLC index columns exist and populated
   - Validate baseline normalization

2. **Execute Track 4: Blocked Features** (Stage 1.6.4)
   - 45 features requiring OHLC index
   - Includes: ADX, ATR, Stochastic, Parabolic SAR, Ichimoku, Keltner, Donchian
   - Estimated time: 17 hours

3. **Final Validation** (Stage 1.6.5)
   - All 111 features verified
   - Gap remediation completion report
   - Phase 2 readiness certification

---

**Created:** 2025-11-11
**Author:** Claude Code
**Status:** Specification Complete - Ready for Worker Implementation
**Next Action:** Create storage schema SQL script (Stage 1.6.2)
