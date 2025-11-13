# Phase 1.6 Remaining Stages Execution Plan (1.6.18-1.6.21)

**Date:** November 13, 2025
**Status:** Ready for Execution
**Current Progress:** 9/13 stages complete (69%)
**Remaining:** 4 stages (all HIGH ROI)

---

## Executive Summary

After successful Option B execution (Stages 1.6.12-1.6.17), 4 high-impact stages remain in Phase 1.6:

| Stage | Feature Type | Features | Tables | ROI | Priority |
|-------|--------------|----------|--------|-----|----------|
| **1.6.18** | Error Correction Models | 24 (12 rate + 12 bqx) | 672 | HIGH | 1 |
| **1.6.19** | Realized Volatility Family | 30 (15 rate + 15 bqx) | 672 | HIGH | 2 |
| **1.6.20** | HMM Regime Detection | 30 (15 rate + 15 bqx) | 672 | HIGH | 3 |
| **1.6.21** | Cross-Sectional Panel | 46 (single panel) | 24 | HIGH | 4 |
| **TOTAL** | | **130 features** | **2,040 tables** | | |

**Total Execution Time:** ~40 hours (parallel execution possible)
**Feature Progress After Completion:** 734/1,080 (68%)

---

## Stage 1.6.18: Error Correction Models

### Overview
**Category:** FX Structure & Error-Correction (from advanced_features doc A)
**Mechanism:** Johansen cointegration captures mean-reversion equilibrium relationships
**Impact:** ECT predicts 30-60% of 45-75 minute movements

### Feature Breakdown (24 total)

#### Rate_idx Features (12)
```python
# Cointegration Error Correction Terms
coint_ect_idx_eurusd_triangle      # EUR/USD/GBP triangle equilibrium error
coint_ect_idx_audusd_cluster       # AUD/NZD/USD cluster error
coint_ect_idx_euraud_cross         # EUR/AUD cross-rate error
coint_ect_idx_usd_majors           # USD major pairs equilibrium

# ECT Dynamics
coint_ect_velocity_idx_20          # ΔECT speed of correction
coint_ect_accel_idx_20             # Δ²ECT acceleration
coint_half_life_idx                # Mean-reversion half-life

# Cointegration Vectors
coint_vec_weight_idx_eur           # EUR weight in vector
coint_vec_weight_idx_gbp           # GBP weight in vector
coint_vec_weight_idx_aud           # AUD weight in vector

# Equilibrium Metrics
coint_deviation_zscore_idx         # Standardized deviation
coint_regime_inbound_idx           # Binary: moving toward equilibrium
```

#### BQX Features (12)
```python
# Same structure for BQX momentum domain
coint_ect_bqx_eurusd_triangle      # Momentum equilibrium error
coint_ect_bqx_audusd_cluster
coint_ect_bqx_euraud_cross
coint_ect_bqx_usd_majors

coint_ect_velocity_bqx_20
coint_ect_accel_bqx_20
coint_half_life_bqx

coint_vec_weight_bqx_eur
coint_vec_weight_bqx_gbp
coint_vec_weight_bqx_aud

coint_deviation_zscore_bqx
coint_regime_inbound_bqx
```

### Schema
```sql
CREATE TABLE bqx.error_correction_rate_{pair} (
    ts_utc TIMESTAMP NOT NULL,

    -- Cointegration ECTs (4 features)
    coint_ect_idx_eurusd_triangle NUMERIC,
    coint_ect_idx_audusd_cluster NUMERIC,
    coint_ect_idx_euraud_cross NUMERIC,
    coint_ect_idx_usd_majors NUMERIC,

    -- ECT Dynamics (3 features)
    coint_ect_velocity_idx_20 NUMERIC,
    coint_ect_accel_idx_20 NUMERIC,
    coint_half_life_idx NUMERIC,

    -- Cointegration Vectors (3 features)
    coint_vec_weight_idx_eur NUMERIC,
    coint_vec_weight_idx_gbp NUMERIC,
    coint_vec_weight_idx_aud NUMERIC,

    -- Equilibrium Metrics (2 features)
    coint_deviation_zscore_idx NUMERIC,
    coint_regime_inbound_idx NUMERIC,

    PRIMARY KEY (ts_utc)
) PARTITION BY RANGE (ts_utc);

CREATE TABLE bqx.error_correction_bqx_{pair} (
    -- Identical 12-feature structure for BQX domain
    ...
);
```

### Tables
- 28 parent tables × 2 (rate + bqx) = 56 parent tables
- 336 partitions × 2 = **672 total partitions**

### Dependencies
- Requires cross-pair data (EUR/USD/GBP triangles, AUD/NZD clusters)
- Johansen cointegration test implementation
- 200+ period lookback for stable cointegration vectors

### Execution Strategy
1. Implement Johansen test function (statsmodels)
2. Create error_correction_rate tables (28 pairs, 336 partitions)
3. Create error_correction_bqx tables (28 pairs, 336 partitions)
4. Build worker to compute ECT features from cross-pair relationships
5. Verify cointegration stability across time periods

---

## Stage 1.6.19: Realized Volatility Family

### Overview
**Category:** Robust Realized Volatility (from advanced_features doc B)
**Mechanism:** Range-based volatility estimators 5-8x more efficient than close-to-close
**Impact:** 15-25% improvement in R² for volatile periods

### Feature Breakdown (30 total)

#### Rate_idx Features (15)
```python
# Range-Based Estimators
parkinson_vol_idx_20_1m            # High-low range
garman_klass_vol_idx_20_1m         # OHLC estimator
rogers_satchell_vol_idx_20_1m      # Drift-independent
yang_zhang_vol_idx_20_1m           # Overnight + intraday

# Jump-Robust Estimators
bipower_var_idx_20_1m              # Robust to jumps
realized_quarticity_idx_20_1m      # Fourth moment (tail risk)
jump_test_stat_idx_20_1m           # Z-stat for jump detection
signed_jump_idx_20_1m              # Direction of jump

# Vol Dynamics
vol_of_vol_idx_20                  # Volatility of volatility
vol_acceleration_idx_20            # d²(vol)/dt²
ewma_vol_ratio_idx_5_20            # Short/long vol ratio

# Regime Metrics
vol_regime_high_idx                # Binary: high vol regime
vol_regime_duration_idx            # Periods in current regime
vol_regime_transition_prob_idx     # P(regime change)
realized_skewness_idx_20           # Return skewness
```

#### BQX Features (15)
```python
# Same structure for BQX momentum
parkinson_vol_bqx_20_1m
garman_klass_vol_bqx_20_1m
rogers_satchell_vol_bqx_20_1m
yang_zhang_vol_bqx_20_1m

bipower_var_bqx_20_1m
realized_quarticity_bqx_20_1m
jump_test_stat_bqx_20_1m
signed_jump_bqx_20_1m

vol_of_vol_bqx_20
vol_acceleration_bqx_20
ewma_vol_ratio_bqx_5_20

vol_regime_high_bqx
vol_regime_duration_bqx
vol_regime_transition_prob_bqx
realized_skewness_bqx_20
```

### Tables
- 28 parent tables × 2 (rate + bqx) = 56 parent tables
- 336 partitions × 2 = **672 total partitions**

### Dependencies
- Requires OHLC data (m1 tables)
- Parkinson, Garman-Klass, Rogers-Satchell, Yang-Zhang formulas
- Jump test statistics

---

## Stage 1.6.20: HMM Regime Detection

### Overview
**Category:** Regime & Change-Point Detection (from advanced_features doc C)
**Mechanism:** Hidden Markov Models detect calm/trend/shock regimes
**Impact:** 20-30% reduction in forecast error at regime boundaries

### Feature Breakdown (30 total)

#### Rate_idx Features (15)
```python
# HMM State Probabilities (K=3: calm/trend/shock)
hmm_state_prob_calm_idx            # P(calm regime)
hmm_state_prob_trend_idx           # P(trending regime)
hmm_state_prob_shock_idx           # P(shock/volatile regime)
hmm_state_duration_idx             # Time in current state
hmm_state_transition_prob_idx      # P(state change next period)

# Bayesian Online Change Point Detection
bocpd_run_length_idx               # Periods since last change point
bocpd_hazard_rate_idx              # P(change point now)
bocpd_growth_prob_idx              # P(variance increasing)
bocpd_decay_prob_idx               # P(variance decreasing)

# CUSUM Statistics
cusum_returns_idx                  # Cumulative sum on returns
cusum_a2_idx                       # CUSUM on parabolic curvature
cusum_alarm_flag_idx               # Binary: CUSUM exceeds threshold
cusum_reset_periods_idx            # Periods since last reset

# Regime Metrics
regime_entropy_idx                 # State uncertainty
regime_persistence_idx             # Regime stability metric
```

#### BQX Features (15)
```python
# Same HMM structure for BQX momentum
hmm_state_prob_calm_bqx
hmm_state_prob_trend_bqx
hmm_state_prob_shock_bqx
hmm_state_duration_bqx
hmm_state_transition_prob_bqx

bocpd_run_length_bqx
bocpd_hazard_rate_bqx
bocpd_growth_prob_bqx
bocpd_decay_prob_bqx

cusum_momentum_bqx
cusum_velocity_bqx
cusum_alarm_flag_bqx
cusum_reset_periods_bqx

regime_entropy_bqx
regime_persistence_bqx
```

### Tables
- 28 parent tables × 2 (rate + bqx) = 56 parent tables
- 336 partitions × 2 = **672 total partitions**

### Dependencies
- HMM library (hmmlearn)
- Bayesian Online Change Point Detection algorithm
- CUSUM control charts
- Requires training period for HMM initialization

---

## Stage 1.6.21: Cross-Sectional Panel Features

### Overview
**Category:** Cross-Sectional Panel (from advanced_features doc F)
**Mechanism:** 8-pair context (ranks, percentiles, dispersion)
**Impact:** 20-25% systematic move detection improvement

### Feature Breakdown (46 features, single panel table)

```python
# Rank Features (8 features)
rank_momentum_15_panel             # Rank of 15-min momentum
rank_momentum_30_panel
rank_momentum_45_panel
rank_momentum_60_panel
rank_volatility_15_panel           # Rank of 15-min volatility
rank_volatility_30_panel
rank_volatility_60_panel
rank_spread_panel                  # Rank of spread

# Percentile Features (8 features)
pctile_momentum_15_panel           # Percentile of momentum
pctile_momentum_30_panel
pctile_momentum_45_panel
pctile_momentum_60_panel
pctile_volatility_15_panel
pctile_volatility_30_panel
pctile_volatility_60_panel
pctile_spread_panel

# Dispersion Features (6 features)
dispersion_momentum_15_panel       # Cross-sectional std of momentum
dispersion_momentum_30_panel
dispersion_momentum_60_panel
dispersion_volatility_15_panel
dispersion_volatility_30_panel
dispersion_volatility_60_panel

# Extremes (4 features)
extreme_high_momentum_panel        # Binary: in top 2
extreme_low_momentum_panel         # Binary: in bottom 2
extreme_high_volatility_panel
extreme_low_volatility_panel

# Divergence (6 features)
divergence_from_median_momentum_15_panel
divergence_from_median_momentum_30_panel
divergence_from_median_momentum_60_panel
divergence_from_median_volatility_15_panel
divergence_from_median_volatility_30_panel
divergence_from_median_volatility_60_panel

# Cross-Sectional Correlations (6 features)
xs_correlation_momentum_volatility_panel
xs_correlation_momentum_spread_panel
xs_correlation_volatility_spread_panel
xs_beta_to_panel_avg_momentum
xs_beta_to_panel_avg_volatility
xs_idiosyncratic_shock_panel       # Residual from panel regression

# Panel Dynamics (8 features)
panel_momentum_acceleration        # d²(avg_momentum)/dt²
panel_volatility_acceleration
panel_dispersion_change            # Δ(dispersion)
panel_rank_stability               # Rank correlation with t-1
panel_regime_coherence             # Fraction in same HMM state
panel_leadership_score             # How often this pair leads
panel_contagion_exposure           # Correlation with leaders
panel_isolation_score              # 1 - avg_correlation
```

### Schema
```sql
CREATE TABLE bqx.cross_sectional_panel (
    ts_utc TIMESTAMP NOT NULL,
    pair VARCHAR(10) NOT NULL,  -- One of 8 major pairs

    -- Rank Features (8)
    rank_momentum_15_panel NUMERIC,
    rank_momentum_30_panel NUMERIC,
    ...

    -- Percentile Features (8)
    pctile_momentum_15_panel NUMERIC,
    ...

    -- Dispersion Features (6)
    dispersion_momentum_15_panel NUMERIC,
    ...

    -- Extremes (4)
    extreme_high_momentum_panel NUMERIC,
    ...

    -- Divergence (6)
    divergence_from_median_momentum_15_panel NUMERIC,
    ...

    -- Cross-Sectional Correlations (6)
    xs_correlation_momentum_volatility_panel NUMERIC,
    ...

    -- Panel Dynamics (8)
    panel_momentum_acceleration NUMERIC,
    ...

    PRIMARY KEY (ts_utc, pair)
) PARTITION BY RANGE (ts_utc);
```

### Tables
**SPECIAL STRUCTURE:** Single panel table (not per-pair)
- 1 parent table: `cross_sectional_panel`
- 24 partitions (2024-07 to 2025-06)
- **Total: 24 tables**

### Dependencies
- Cross-pair access (8 major pairs: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD, EURJPY)
- Panel statistics computation
- Rolling correlation matrices

---

## Execution Sequence & Timeline

### Sequential Execution (Conservative)
```
Week 1:
  Days 1-3: Stage 1.6.18 (Error Correction) - 12 hours
  Days 4-6: Stage 1.6.19 (Realized Volatility) - 12 hours

Week 2:
  Days 1-3: Stage 1.6.20 (HMM Regime) - 12 hours
  Days 4-6: Stage 1.6.21 (Cross-Sectional) - 4 hours

Total: ~40 hours over 2 weeks
```

### Parallel Execution (Optimal)
```
Stage 1.6.18 + 1.6.19 in parallel (independent)
  → Duration: 12 hours (max of the two)

Stage 1.6.20 + 1.6.21 in parallel (independent)
  → Duration: 12 hours (max of the two)

Total: ~24 hours (60% time savings)
```

---

## Implementation Checklist

### Stage 1.6.18 (Error Correction)
- [ ] Implement Johansen cointegration test
- [ ] Create error_correction_rate tables (SQL)
- [ ] Create error_correction_bqx tables (SQL)
- [ ] Build error correction worker
- [ ] Verify cointegration stability
- [ ] Update AirTable to "Done"

### Stage 1.6.19 (Realized Volatility)
- [ ] Implement Parkinson/GK/RS/YZ estimators
- [ ] Create realized_volatility_rate tables (SQL)
- [ ] Create realized_volatility_bqx tables (SQL)
- [ ] Build volatility worker
- [ ] Verify jump detection accuracy
- [ ] Update AirTable to "Done"

### Stage 1.6.20 (HMM Regime)
- [ ] Implement HMM (hmmlearn)
- [ ] Implement Bayesian change point detection
- [ ] Create hmm_regime_rate tables (SQL)
- [ ] Create hmm_regime_bqx tables (SQL)
- [ ] Build regime detection worker
- [ ] Verify regime accuracy
- [ ] Update AirTable to "Done"

### Stage 1.6.21 (Cross-Sectional Panel)
- [ ] Create cross_sectional_panel table (SQL)
- [ ] Build panel statistics worker
- [ ] Compute ranks/percentiles/dispersion
- [ ] Verify panel consistency
- [ ] Update AirTable to "Done"

---

## Feature Progress Projection

**Current (After Option B):** 604/1,080 (55.9%)

**After Stage 1.6.18:** 628/1,080 (58.1%) +24 features
**After Stage 1.6.19:** 658/1,080 (60.9%) +30 features
**After Stage 1.6.20:** 688/1,080 (63.7%) +30 features
**After Stage 1.6.21:** 734/1,080 (68.0%) +46 features

**Phase 1.6 Complete:** 734/1,080 (68.0%)

**Remaining for 1,080 target:** 346 features (Phase 1.7-1.8, Phase 2, Phase 3)

---

## Risk Assessment

### High Risk
- **Cross-pair dependencies:** Error correction requires synchronized data access
- **HMM training stability:** Requires sufficient data for stable state estimation
- **Panel coherence:** Cross-sectional features need all 8 pairs available

### Mitigation
- Implement robust cross-pair data fetching with retries
- Use Baum-Welch with multiple initializations
- Gracefully handle missing pairs (interpolate or skip timestamp)

### Low Risk
- Volatility features are per-pair (no cross-dependencies)
- All features are leakage-safe (no lookahead)
- Table schemas follow established dual architecture pattern

---

## Success Criteria

✅ All 672 partitions created for stages 1.6.18-1.6.20
✅ All 24 panel partitions created for stage 1.6.21
✅ 100% dual architecture parity (rate = bqx features)
✅ Feature Progress: 734/1,080 (68%)
✅ Zero data loss or corruption
✅ All AirTable stages marked "Done"
✅ Git commit with comprehensive documentation

---

**Document Status:** ✅ READY FOR EXECUTION
**Next Action:** Begin Stage 1.6.18 (Error Correction Models)
**Author:** BQX ML Team
**Date:** November 13, 2025
