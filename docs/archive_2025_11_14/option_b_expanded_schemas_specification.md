# Option B: Expanded Schemas Specification (1,080-Feature Plan)

**Date:** November 13, 2025
**Purpose:** Complete expanded schema definitions for Stages 1.6.12-1.6.17
**Architecture:** Dual (rate_idx + BQX domains)
**Total Features:** 213 new features across 6 stages

---

## Overview

This specification defines the **Option B** expanded schemas that align with the official 1,080-feature refactored architecture plan. These schemas significantly expand beyond the minimal "rate" tables to provide comprehensive feature coverage.

**Key Differences from Option A (minimal replication):**
- Statistics: 6 columns → **48 features**
- Bollinger: 6 columns → **20 features**
- Fibonacci: 13 columns → **20 features**
- Volume: NEW → **35 features**
- Correlation IDX: 16 columns → **45 features**
- Correlation BQX: NEW → **45 features**

---

## Stage 1.6.12: Statistics BQX (48 Features)

### Feature Specification

**Computed from:** BQX momentum (w15_bqx_return, w30_bqx_return, etc.)

| Category | Features | Windows/Params | Column Names |
|----------|----------|----------------|--------------|
| **Mean** | 5 | 5, 15, 30, 60, 120 min | mean_5min, mean_15min, mean_30min, mean_60min, mean_120min |
| **Std Deviation** | 5 | 5, 15, 30, 60, 120 min | std_5min, std_15min, std_30min, std_60min, std_120min |
| **Skewness** | 5 | 5, 15, 30, 60, 120 min | skew_5min, skew_15min, skew_30min, skew_60min, skew_120min |
| **Kurtosis** | 5 | 5, 15, 30, 60, 120 min | kurt_5min, kurt_15min, kurt_30min, kurt_60min, kurt_120min |
| **Percentiles** | 10 | 5th, 10th, 25th, 50th, 75th, 90th, 95th (15min, 60min) | p5_15min, p10_15min, p25_15min, p50_15min, p75_15min, p90_15min, p95_15min, p50_60min, p75_60min, p90_60min |
| **Range** | 3 | 15, 30, 60 min | range_15min, range_30min, range_60min |
| **IQR** | 3 | 15, 30, 60 min | iqr_15min, iqr_30min, iqr_60min |
| **MAD** | 3 | 15, 30, 60 min | mad_15min, mad_30min, mad_60min |
| **Coefficient of Variation** | 3 | 15, 30, 60 min | cv_15min, cv_30min, cv_60min |
| **Entropy** | 3 | 15, 30, 60 min | entropy_15min, entropy_30min, entropy_60min |
| **Autocorrelation** | 3 | Lag 1, 5, 15 | autocorr_lag1, autocorr_lag5, autocorr_lag15 |
| **Jarque-Bera** | 2 | 30, 60 min | jb_stat_30min, jb_stat_60min |

**Total:** 48 features + 1 timestamp = **49 columns**

### SQL Schema

```sql
CREATE TABLE bqx.statistics_bqx_{pair} (
    ts_utc TIMESTAMP NOT NULL,

    -- Mean (5 features)
    mean_5min NUMERIC,
    mean_15min NUMERIC,
    mean_30min NUMERIC,
    mean_60min NUMERIC,
    mean_120min NUMERIC,

    -- Std Deviation (5 features)
    std_5min NUMERIC,
    std_15min NUMERIC,
    std_30min NUMERIC,
    std_60min NUMERIC,
    std_120min NUMERIC,

    -- Skewness (5 features)
    skew_5min NUMERIC,
    skew_15min NUMERIC,
    skew_30min NUMERIC,
    skew_60min NUMERIC,
    skew_120min NUMERIC,

    -- Kurtosis (5 features)
    kurt_5min NUMERIC,
    kurt_15min NUMERIC,
    kurt_30min NUMERIC,
    kurt_60min NUMERIC,
    kurt_120min NUMERIC,

    -- Percentiles (10 features)
    p5_15min NUMERIC,
    p10_15min NUMERIC,
    p25_15min NUMERIC,
    p50_15min NUMERIC,
    p75_15min NUMERIC,
    p90_15min NUMERIC,
    p95_15min NUMERIC,
    p50_60min NUMERIC,
    p75_60min NUMERIC,
    p90_60min NUMERIC,

    -- Range (3 features)
    range_15min NUMERIC,
    range_30min NUMERIC,
    range_60min NUMERIC,

    -- IQR (3 features)
    iqr_15min NUMERIC,
    iqr_30min NUMERIC,
    iqr_60min NUMERIC,

    -- MAD (3 features)
    mad_15min NUMERIC,
    mad_30min NUMERIC,
    mad_60min NUMERIC,

    -- Coefficient of Variation (3 features)
    cv_15min NUMERIC,
    cv_30min NUMERIC,
    cv_60min NUMERIC,

    -- Entropy (3 features)
    entropy_15min NUMERIC,
    entropy_30min NUMERIC,
    entropy_60min NUMERIC,

    -- Autocorrelation (3 features)
    autocorr_lag1 NUMERIC,
    autocorr_lag5 NUMERIC,
    autocorr_lag15 NUMERIC,

    -- Jarque-Bera (2 features)
    jb_stat_30min NUMERIC,
    jb_stat_60min NUMERIC,

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

---

## Stage 1.6.13: Bollinger BQX (20 Features)

### Feature Specification

**Computed from:** BQX momentum rolling windows

| Category | Features | Windows | Column Names |
|----------|----------|---------|--------------|
| **Upper Band** | 4 | 20, 30, 60, 120 periods | bb_upper_20, bb_upper_30, bb_upper_60, bb_upper_120 |
| **Middle Band** | 4 | 20, 30, 60, 120 periods | bb_middle_20, bb_middle_30, bb_middle_60, bb_middle_120 |
| **Lower Band** | 4 | 20, 30, 60, 120 periods | bb_lower_20, bb_lower_30, bb_lower_60, bb_lower_120 |
| **Bandwidth** | 4 | 20, 30, 60, 120 periods | bb_width_20, bb_width_30, bb_width_60, bb_width_120 |
| **%B Indicator** | 2 | 20, 60 periods | bb_percent_b_20, bb_percent_b_60 |
| **Band Slope** | 2 | 20, 60 periods (upper band) | bb_slope_20, bb_slope_60 |

**Total:** 20 features + 1 timestamp = **21 columns**

### SQL Schema

```sql
CREATE TABLE bqx.bollinger_bqx_{pair} (
    ts_utc TIMESTAMP NOT NULL,

    -- Upper Band (4 features)
    bb_upper_20 NUMERIC,
    bb_upper_30 NUMERIC,
    bb_upper_60 NUMERIC,
    bb_upper_120 NUMERIC,

    -- Middle Band (4 features)
    bb_middle_20 NUMERIC,
    bb_middle_30 NUMERIC,
    bb_middle_60 NUMERIC,
    bb_middle_120 NUMERIC,

    -- Lower Band (4 features)
    bb_lower_20 NUMERIC,
    bb_lower_30 NUMERIC,
    bb_lower_60 NUMERIC,
    bb_lower_120 NUMERIC,

    -- Bandwidth (4 features)
    bb_width_20 NUMERIC,
    bb_width_30 NUMERIC,
    bb_width_60 NUMERIC,
    bb_width_120 NUMERIC,

    -- %B Indicator (2 features)
    bb_percent_b_20 NUMERIC,
    bb_percent_b_60 NUMERIC,

    -- Band Slope (2 features)
    bb_slope_20 NUMERIC,
    bb_slope_60 NUMERIC,

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

---

## Stage 1.6.14: Fibonacci BQX (20 Features)

### Feature Specification

**Computed from:** BQX momentum swing highs/lows (100-period lookback)

| Category | Features | Levels/Params | Column Names |
|----------|----------|---------------|--------------|
| **Retracement Levels** | 5 | 23.6%, 38.2%, 50%, 61.8%, 78.6% | fib_ret_236, fib_ret_382, fib_ret_500, fib_ret_618, fib_ret_786 |
| **Extension Levels** | 3 | 127.2%, 161.8%, 261.8% | fib_ext_1272, fib_ext_1618, fib_ext_2618 |
| **Pivot Points** | 3 | Pivot, R1, S1 | pivot_point, resistance_1, support_1 |
| **Distance to Levels** | 4 | Dist to 38.2%, 50%, 61.8%, pivot | dist_to_382, dist_to_500, dist_to_618, dist_to_pivot |
| **Level Breaks** | 3 | Above 61.8%, Below 38.2%, At 50% | above_618, below_382, at_500 |
| **Swing Range** | 2 | Range, Normalized range | swing_range, swing_range_norm |

**Total:** 20 features + 1 timestamp = **21 columns**

### SQL Schema

```sql
CREATE TABLE bqx.fibonacci_bqx_{pair} (
    ts_utc TIMESTAMP NOT NULL,

    -- Retracement Levels (5 features)
    fib_ret_236 NUMERIC,
    fib_ret_382 NUMERIC,
    fib_ret_500 NUMERIC,
    fib_ret_618 NUMERIC,
    fib_ret_786 NUMERIC,

    -- Extension Levels (3 features)
    fib_ext_1272 NUMERIC,
    fib_ext_1618 NUMERIC,
    fib_ext_2618 NUMERIC,

    -- Pivot Points (3 features)
    pivot_point NUMERIC,
    resistance_1 NUMERIC,
    support_1 NUMERIC,

    -- Distance to Levels (4 features)
    dist_to_382 NUMERIC,
    dist_to_500 NUMERIC,
    dist_to_618 NUMERIC,
    dist_to_pivot NUMERIC,

    -- Level Breaks (3 features - binary flags)
    above_618 INTEGER,
    below_382 INTEGER,
    at_500 INTEGER,

    -- Swing Range (2 features)
    swing_range NUMERIC,
    swing_range_norm NUMERIC,

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

---

## Stage 1.6.15: Volume BQX (35 Features)

### Feature Specification

**Computed from:** BQX momentum + volume data interactions

| Category | Features | Windows/Params | Column Names |
|----------|----------|----------------|--------------|
| **Volume-Weighted BQX** | 5 | 5, 15, 30, 60, 120 min | vw_bqx_5min, vw_bqx_15min, vw_bqx_30min, vw_bqx_60min, vw_bqx_120min |
| **BQX-Volume Correlation** | 3 | 15, 30, 60 min | corr_bqx_vol_15min, corr_bqx_vol_30min, corr_bqx_vol_60min |
| **Volume Momentum Divergence** | 4 | 15, 30, 60, 120 min | vol_mom_div_15min, vol_mom_div_30min, vol_mom_div_60min, vol_mom_div_120min |
| **Up-Tick Volume Ratio** | 4 | 5, 15, 30, 60 min | uptick_ratio_5min, uptick_ratio_15min, uptick_ratio_30min, uptick_ratio_60min |
| **Down-Tick Volume Ratio** | 4 | 5, 15, 30, 60 min | downtick_ratio_5min, downtick_ratio_15min, downtick_ratio_30min, downtick_ratio_60min |
| **Volume × Volatility** | 3 | 15, 30, 60 min | vol_x_volatility_15min, vol_x_volatility_30min, vol_x_volatility_60min |
| **Volume Trend** | 3 | 15, 30, 60 min | vol_trend_15min, vol_trend_30min, vol_trend_60min |
| **Volume Spike Detection** | 3 | 15, 30, 60 min (z-score > 2) | vol_spike_15min, vol_spike_30min, vol_spike_60min |
| **Cumulative Volume Delta** | 3 | 15, 30, 60 min | cum_vol_delta_15min, cum_vol_delta_30min, cum_vol_delta_60min |
| **Volume Imbalance** | 3 | 15, 30, 60 min | vol_imbalance_15min, vol_imbalance_30min, vol_imbalance_60min |

**Total:** 35 features + 1 timestamp = **36 columns**

### SQL Schema

```sql
CREATE TABLE bqx.volume_bqx_{pair} (
    ts_utc TIMESTAMP NOT NULL,

    -- Volume-Weighted BQX (5 features)
    vw_bqx_5min NUMERIC,
    vw_bqx_15min NUMERIC,
    vw_bqx_30min NUMERIC,
    vw_bqx_60min NUMERIC,
    vw_bqx_120min NUMERIC,

    -- BQX-Volume Correlation (3 features)
    corr_bqx_vol_15min NUMERIC,
    corr_bqx_vol_30min NUMERIC,
    corr_bqx_vol_60min NUMERIC,

    -- Volume Momentum Divergence (4 features)
    vol_mom_div_15min NUMERIC,
    vol_mom_div_30min NUMERIC,
    vol_mom_div_60min NUMERIC,
    vol_mom_div_120min NUMERIC,

    -- Up-Tick Volume Ratio (4 features)
    uptick_ratio_5min NUMERIC,
    uptick_ratio_15min NUMERIC,
    uptick_ratio_30min NUMERIC,
    uptick_ratio_60min NUMERIC,

    -- Down-Tick Volume Ratio (4 features)
    downtick_ratio_5min NUMERIC,
    downtick_ratio_15min NUMERIC,
    downtick_ratio_30min NUMERIC,
    downtick_ratio_60min NUMERIC,

    -- Volume × Volatility (3 features)
    vol_x_volatility_15min NUMERIC,
    vol_x_volatility_30min NUMERIC,
    vol_x_volatility_60min NUMERIC,

    -- Volume Trend (3 features)
    vol_trend_15min NUMERIC,
    vol_trend_30min NUMERIC,
    vol_trend_60min NUMERIC,

    -- Volume Spike Detection (3 features - z-score)
    vol_spike_15min NUMERIC,
    vol_spike_30min NUMERIC,
    vol_spike_60min NUMERIC,

    -- Cumulative Volume Delta (3 features)
    cum_vol_delta_15min NUMERIC,
    cum_vol_delta_30min NUMERIC,
    cum_vol_delta_60min NUMERIC,

    -- Volume Imbalance (3 features)
    vol_imbalance_15min NUMERIC,
    vol_imbalance_30min NUMERIC,
    vol_imbalance_60min NUMERIC,

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

---

## Stage 1.6.16: Correlation IDX (45 Features)

### Feature Specification

**Computed from:** rate_idx cross-pair correlations

| Category | Features | Windows/Params | Column Names |
|----------|----------|----------------|--------------|
| **Base Pair Correlations** | 6 | 15, 30, 60 min (2 related pairs each) | corr_base_15min_1, corr_base_15min_2, corr_base_30min_1, corr_base_30min_2, corr_base_60min_1, corr_base_60min_2 |
| **Quote Pair Correlations** | 6 | 15, 30, 60 min (2 related pairs each) | corr_quote_15min_1, corr_quote_15min_2, corr_quote_30min_1, corr_quote_30min_2, corr_quote_60min_1, corr_quote_60min_2 |
| **Correlation Changes** | 6 | Δcorr (15min, 30min, 60min) for base/quote | delta_corr_base_15min, delta_corr_base_30min, delta_corr_base_60min, delta_corr_quote_15min, delta_corr_quote_30min, delta_corr_quote_60min |
| **Correlation Z-Scores** | 6 | Z-score (15, 30, 60 min) for base/quote | z_corr_base_15min, z_corr_base_30min, z_corr_base_60min, z_corr_quote_15min, z_corr_quote_30min, z_corr_quote_60min |
| **Relative Strength** | 2 | vs base pairs, vs quote pairs | rel_str_base, rel_str_quote |
| **Divergence Metrics** | 4 | Base, quote, triangular arb, cross-pair mom | div_base, div_quote, div_tri_arb, div_cross_mom |
| **Correlation Stability** | 3 | 15, 30, 60 min (rolling std of correlations) | corr_stability_15min, corr_stability_30min, corr_stability_60min |
| **Lead-Lag Indicators** | 3 | 15, 30, 60 min | lead_lag_15min, lead_lag_30min, lead_lag_60min |
| **Cointegration** | 3 | Residual, half-life, z-score | coint_residual, coint_halflife, coint_zscore |
| **Pair Spread** | 3 | Z-score (15, 30, 60 min) | spread_zscore_15min, spread_zscore_30min, spread_zscore_60min |
| **Cross-Pair Volatility** | 3 | Ratio (15, 30, 60 min) | vol_ratio_15min, vol_ratio_30min, vol_ratio_60min |

**Total:** 45 features + 1 timestamp = **46 columns**

### SQL Schema

```sql
CREATE TABLE bqx.correlation_idx_{pair} (
    ts_utc TIMESTAMP NOT NULL,

    -- Base Pair Correlations (6 features)
    corr_base_15min_1 NUMERIC,
    corr_base_15min_2 NUMERIC,
    corr_base_30min_1 NUMERIC,
    corr_base_30min_2 NUMERIC,
    corr_base_60min_1 NUMERIC,
    corr_base_60min_2 NUMERIC,

    -- Quote Pair Correlations (6 features)
    corr_quote_15min_1 NUMERIC,
    corr_quote_15min_2 NUMERIC,
    corr_quote_30min_1 NUMERIC,
    corr_quote_30min_2 NUMERIC,
    corr_quote_60min_1 NUMERIC,
    corr_quote_60min_2 NUMERIC,

    -- Correlation Changes (6 features)
    delta_corr_base_15min NUMERIC,
    delta_corr_base_30min NUMERIC,
    delta_corr_base_60min NUMERIC,
    delta_corr_quote_15min NUMERIC,
    delta_corr_quote_30min NUMERIC,
    delta_corr_quote_60min NUMERIC,

    -- Correlation Z-Scores (6 features)
    z_corr_base_15min NUMERIC,
    z_corr_base_30min NUMERIC,
    z_corr_base_60min NUMERIC,
    z_corr_quote_15min NUMERIC,
    z_corr_quote_30min NUMERIC,
    z_corr_quote_60min NUMERIC,

    -- Relative Strength (2 features)
    rel_str_base NUMERIC,
    rel_str_quote NUMERIC,

    -- Divergence Metrics (4 features)
    div_base NUMERIC,
    div_quote NUMERIC,
    div_tri_arb NUMERIC,
    div_cross_mom NUMERIC,

    -- Correlation Stability (3 features)
    corr_stability_15min NUMERIC,
    corr_stability_30min NUMERIC,
    corr_stability_60min NUMERIC,

    -- Lead-Lag Indicators (3 features)
    lead_lag_15min NUMERIC,
    lead_lag_30min NUMERIC,
    lead_lag_60min NUMERIC,

    -- Cointegration (3 features)
    coint_residual NUMERIC,
    coint_halflife NUMERIC,
    coint_zscore NUMERIC,

    -- Pair Spread (3 features)
    spread_zscore_15min NUMERIC,
    spread_zscore_30min NUMERIC,
    spread_zscore_60min NUMERIC,

    -- Cross-Pair Volatility (3 features)
    vol_ratio_15min NUMERIC,
    vol_ratio_30min NUMERIC,
    vol_ratio_60min NUMERIC,

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

---

## Stage 1.6.17: Correlation BQX (45 Features)

### Feature Specification

**Computed from:** BQX momentum cross-pair correlations (same structure as 1.6.16 but for BQX domain)

**Schema:** Identical to correlation_idx_{pair} but named `correlation_bqx_{pair}`

**Total:** 45 features + 1 timestamp = **46 columns**

### SQL Schema

```sql
CREATE TABLE bqx.correlation_bqx_{pair} (
    ts_utc TIMESTAMP NOT NULL,

    -- (Same 45 columns as correlation_idx but computed from BQX)

    -- Base Pair Correlations (6 features)
    corr_base_15min_1 NUMERIC,
    corr_base_15min_2 NUMERIC,
    corr_base_30min_1 NUMERIC,
    corr_base_30min_2 NUMERIC,
    corr_base_60min_1 NUMERIC,
    corr_base_60min_2 NUMERIC,

    -- Quote Pair Correlations (6 features)
    corr_quote_15min_1 NUMERIC,
    corr_quote_15min_2 NUMERIC,
    corr_quote_30min_1 NUMERIC,
    corr_quote_30min_2 NUMERIC,
    corr_quote_60min_1 NUMERIC,
    corr_quote_60min_2 NUMERIC,

    -- Correlation Changes (6 features)
    delta_corr_base_15min NUMERIC,
    delta_corr_base_30min NUMERIC,
    delta_corr_base_60min NUMERIC,
    delta_corr_quote_15min NUMERIC,
    delta_corr_quote_30min NUMERIC,
    delta_corr_quote_60min NUMERIC,

    -- Correlation Z-Scores (6 features)
    z_corr_base_15min NUMERIC,
    z_corr_base_30min NUMERIC,
    z_corr_base_60min NUMERIC,
    z_corr_quote_15min NUMERIC,
    z_corr_quote_30min NUMERIC,
    z_corr_quote_60min NUMERIC,

    -- Relative Strength (2 features)
    rel_str_base NUMERIC,
    rel_str_quote NUMERIC,

    -- Divergence Metrics (4 features)
    div_base NUMERIC,
    div_quote NUMERIC,
    div_tri_arb NUMERIC,
    div_cross_mom NUMERIC,

    -- Correlation Stability (3 features)
    corr_stability_15min NUMERIC,
    corr_stability_30min NUMERIC,
    corr_stability_60min NUMERIC,

    -- Lead-Lag Indicators (3 features)
    lead_lag_15min NUMERIC,
    lead_lag_30min NUMERIC,
    lead_lag_60min NUMERIC,

    -- Cointegration (3 features)
    coint_residual NUMERIC,
    coint_halflife NUMERIC,
    coint_zscore NUMERIC,
    -- Pair Spread (3 features)
    spread_zscore_15min NUMERIC,
    spread_zscore_30min NUMERIC,
    spread_zscore_60min NUMERIC,

    -- Cross-Pair Volatility (3 features)
    vol_ratio_15min NUMERIC,
    vol_ratio_30min NUMERIC,
    vol_ratio_60min NUMERIC,

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);
```

---

## Summary

### Feature Count Reconciliation

| Stage | Feature Type | Features | Tables | Column Count |
|-------|-------------|----------|--------|--------------|
| 1.6.12 | Statistics BQX | 48 | 672 | 49 (48 + ts_utc) |
| 1.6.13 | Bollinger BQX | 20 | 672 | 21 (20 + ts_utc) |
| 1.6.14 | Fibonacci BQX | 20 | 672 | 21 (20 + ts_utc) |
| 1.6.15 | Volume BQX | 35 | 672 | 36 (35 + ts_utc) |
| 1.6.16 | Correlation IDX | 45 | 672 | 46 (45 + ts_utc) |
| 1.6.17 | Correlation BQX | 45 | 672 | 46 (45 + ts_utc) |
| **TOTAL** | | **213** | **4,032** | **219 total columns** |

### Coverage Verification

✅ **Statistics BQX:** 48 features (matches 1,080-plan specification)
✅ **Bollinger BQX:** 20 features (matches 1,080-plan specification)
✅ **Fibonacci BQX:** 20 features (matches 1,080-plan specification)
✅ **Volume BQX:** 35 features (matches 1,080-plan specification)
✅ **Correlation IDX:** 45 features (matches 1,080-plan specification)
✅ **Correlation BQX:** 45 features (matches 1,080-plan specification)

**Grand Total:** 213 new features across 6 stages, 4,032 new partition tables

### Integration with Existing Architecture

**Before Stages 1.6.12-1.6.17:**
- Features: 268/1,080 (24.8%)
- Tables: 2,856/11,760 (24.3%)

**After Stages 1.6.12-1.6.17:**
- Features: 481/1,080 (44.5%)
- Tables: 6,888/11,760 (58.6%)

### Next Stages After 1.6.17

**Remaining Work:**
- Stages 1.6.18-1.6.21: Advanced features (130 features, 40 hours)
- Stages 1.7.1-1.7.3: Database expansion (336 features, 36 hours)
- Stages 1.8.1-1.8.3: Spectral/advanced (320 features, 12 hours)

**Total Remaining:** 786 features (72.8%), 88 hours

---

## Implementation Notes

### Computational Considerations

1. **Statistics BQX (48 features):**
   - Computation: NumPy/SciPy statistical functions
   - Windows: Rolling calculations on BQX momentum
   - Complexity: O(n × w) where w = window size

2. **Bollinger BQX (20 features):**
   - Computation: Rolling mean + standard deviation
   - Multiple periods: 20, 30, 60, 120
   - Complexity: O(n × p) where p = periods

3. **Fibonacci BQX (20 features):**
   - Computation: Swing high/low detection (100-period lookback)
   - Level calculations: Linear interpolation
   - Complexity: O(n × 100)

4. **Volume BQX (35 features):**
   - Computation: Cross-domain correlations, ratios
   - Requires: Volume data + BQX momentum sync
   - Complexity: O(n × w) for correlations

5. **Correlation IDX/BQX (45 features each):**
   - Computation: Cross-pair correlation matrices
   - Windows: 15, 30, 60 min rolling
   - Complexity: O(n × pairs × w)

### Parallel Execution Strategy

**6 stages can run in parallel** (no dependencies between them):
- Each stage creates 672 partition tables
- Each stage operates on independent column set
- Total execution time: ~MAX(stage durations) not SUM(stage durations)

**Estimated Parallel Execution Time:** 45-60 seconds (based on technical_idx performance)

---

**Document Version:** 1.0
**Author:** BQX ML Team
**Date:** November 13, 2025
**Status:** ✅ READY FOR EXECUTION
