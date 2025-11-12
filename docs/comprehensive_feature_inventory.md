# Comprehensive BQX ML Feature Inventory
**Aggregated from AirTable Plan + User Expectations Document**

**Date:** 2025-11-12
**Status:** Complete Feature Specification for Dual Architecture
**Purpose:** Predict future BQX at horizons i+15, i+30, i+45, i+60, i+75 (1-minute intervals)

---

## Executive Summary

### ML Objective
**Target Variables:**
- `bqx_{i+15}`, `bqx_{i+30}`, `bqx_{i+45}`, `bqx_{i+60}`, `bqx_{i+75}`
- Optionally: Vol-scaled Δbqx: `(bqx_{i+h} - bqx_i) / σ_w`
- Multi-task: Direction (classification) + Magnitude (regression)

### Critical Architecture: DUAL FEATURE DOMAINS

**Rate Index Domain** (rate_idx):
- Source: `rate_index` from M1 tables (base-100 normalized)
- Captures: Price dynamics, structural patterns, macro position
- Purpose: The CAUSE of momentum changes

**BQX Domain** (bqx):
- Source: `bqx_{pair}` tables (backward momentum indices)
- Captures: Momentum patterns, momentum-of-momentum (2nd derivative)
- Purpose: The EFFECT and momentum persistence signals

---

## Feature Categories & Complete Inventory

### CATEGORY 1: Regression Features (Quadratic Parabolic Terms)

**Purpose:** Capture trajectory quality and curvature (acceleration/deceleration)

#### 1.1 REG_IDX Features (Rate Index Regression)
**Table:** `reg_idx_{pair}` (RENAME from current `reg_{pair}`)
**Source:** rate_index from M1 tables
**Windows:** w15, w30, w45, w60, w75, w90

**Features per window (12 features × 6 windows = 72 total):**
```
# Parabolic coefficients (normalized)
{window}_a2_norm          # Curvature (2nd derivative, acceleration)
{window}_a1_norm          # Slope (1st derivative, velocity)
{window}_b_norm           # Baseline (intercept)

# Regression quality
{window}_r2               # Fit quality (predictability)
{window}_rmse_norm        # Residual magnitude
{window}_resid_norm       # Current residual position

# Derivatives
{window}_lin_slope        # Linear approximation
{window}_quad_apex        # Turning point location
{window}_accel            # Rate of acceleration

# Residual patterns
{window}_resid_mean       # Systematic bias
{window}_resid_std        # Residual volatility
{window}_resid_z          # Z-score position
```

**Cross-window comparisons (18 features):**
```
# Term ratios (curvature/slope/baseline across windows)
a2_ratio_15_60            # Short vs long curvature
a1_ratio_30_75            # Slope momentum
b_gap_15_45               # Baseline drift

# Quality comparisons
r2_spread_30_90           # Predictability divergence
rmse_ratio_15_60          # Error scaling
```

**Total REG_IDX Features:** 72 + 18 = **90 features**

#### 1.2 REG_BQX Features (BQX Regression)
**Table:** `reg_bqx_{pair}` (✅ ALREADY EXISTS!)
**Source:** bqx w15, w30, w45, w60, w75 values
**Windows:** Same as above

**Features:** Identical structure to REG_IDX (90 features)
- Captures: Momentum trajectory quality
- Interpretation: High R² on BQX → momentum trend is strong

**Total REG_BQX Features:** **90 features**

**REG CATEGORY TOTAL:** 90 (idx) + 90 (bqx) = **180 features**

---

### CATEGORY 2: Statistical Moments

**Purpose:** Distribution characteristics, volatility, tail risk

#### 2.1 STATISTICS_IDX Features (Rate Index Statistics)
**Table:** `statistics_idx_{pair}` (RENAME from `statistics_features_{pair}`)
**Source:** rate_index from M1 tables
**Windows:** 20, 50, 120 periods

**Features per window (8 features × 3 windows = 24 total):**
```
mean_{window}             # Rolling mean
std_{window}              # Rolling standard deviation
skew_{window}             # Distribution asymmetry
kurt_{window}             # Tail risk / fat tails
min_{window}              # Range minimum
max_{window}              # Range maximum
range_{window}            # max - min
z_score_{window}          # (current - mean) / std
```

**Total STATISTICS_IDX Features:** **24 features**

#### 2.2 STATISTICS_BQX Features (BQX Statistics)
**Table:** `statistics_bqx_{pair}` (NEW - TO BUILD)
**Source:** bqx w15_bqx_return
**Windows:** 20, 50, 120 periods

**Features:** Identical structure (24 features)
- Captures: Momentum volatility, momentum distribution
- Interpretation: High BQX std → unstable momentum regime

**Total STATISTICS_BQX Features:** **24 features**

**STATISTICS CATEGORY TOTAL:** 24 (idx) + 24 (bqx) = **48 features**

---

### CATEGORY 3: Volatility Bands (Bollinger)

**Purpose:** Overbought/oversold detection, volatility regimes

#### 3.1 BOLLINGER_IDX Features (Rate Index Bollinger)
**Table:** `bollinger_idx_{pair}` (RENAME from `bollinger_features_{pair}`)
**Source:** rate_index from M1 tables
**Windows:** 20, 50 periods

**Features per window (5 features × 2 windows = 10 total):**
```
bb_upper_{window}         # Upper band (mean + 2*std)
bb_middle_{window}        # Middle band (mean)
bb_lower_{window}         # Lower band (mean - 2*std)
bb_bandwidth_{window}     # (upper - lower) / middle
bb_percent_b_{window}     # (price - lower) / (upper - lower)
```

**Total BOLLINGER_IDX Features:** **10 features**

#### 3.2 BOLLINGER_BQX Features (BQX Bollinger)
**Table:** `bollinger_bqx_{pair}` (NEW - TO BUILD)
**Source:** bqx w15_bqx_return
**Windows:** 20, 50 periods

**Features:** Identical structure (10 features)
- Captures: Momentum volatility bands
- Interpretation: BQX at upper band → momentum acceleration is extreme

**Total BOLLINGER_BQX Features:** **10 features**

**BOLLINGER CATEGORY TOTAL:** 10 (idx) + 10 (bqx) = **20 features**

---

### CATEGORY 4: Technical Momentum Indicators

**Purpose:** Momentum oscillators, trend direction, overbought/oversold

#### 4.1 TECHNICAL_IDX Features (Rate Index Technical)
**Table:** `technical_idx_{pair}` (NEW - TO BUILD)
**Source:** rate_index from M1 tables

**Features (15 total):**
```
# RSI (Relative Strength Index)
rsi_14                    # 14-period RSI
rsi_21                    # 21-period RSI

# MACD (Moving Average Convergence Divergence)
macd_line                 # EMA(12) - EMA(26)
macd_signal               # EMA(9) of MACD line
macd_histogram            # MACD line - signal

# Stochastic Oscillator
stoch_k_14                # %K (14 period)
stoch_d_3                 # %D (3-period SMA of %K)

# Other Momentum
cci_20                    # Commodity Channel Index (20)
williams_r_14             # Williams %R (14)
roc_12                    # Rate of Change (12)

# Trend
adx_14                    # Average Directional Index
plus_di_14                # +DI
minus_di_14               # -DI

# Volatility
atr_14                    # Average True Range (14)
atr_pct_14                # ATR as % of price
```

**Total TECHNICAL_IDX Features:** **15 features**

#### 4.2 TECHNICAL_BQX Features (BQX Technical)
**Table:** `technical_bqx_{pair}` (NEW - TO BUILD)
**Source:** bqx w15_bqx_return

**Features:** Identical structure (15 features)
- Captures: Momentum-of-momentum, 2nd derivative signals
- Interpretation: RSI_BQX > 70 → momentum acceleration is overbought

**Total TECHNICAL_BQX Features:** **15 features**

**TECHNICAL CATEGORY TOTAL:** 15 (idx) + 15 (bqx) = **30 features**

---

### CATEGORY 5: Support/Resistance Levels (Fibonacci)

**Purpose:** Retracement/extension levels, support/resistance zones

#### 5.1 FIBONACCI_IDX Features (Rate Index Fibonacci)
**Table:** `fibonacci_idx_{pair}` (RENAME from `fibonacci_features_{pair}`)
**Source:** rate_index from M1 tables
**Lookback:** 100 periods

**Features (10 total):**
```
# Retracement levels
fib_23_6                  # 23.6% retracement from high-low
fib_38_2                  # 38.2% retracement
fib_50_0                  # 50% retracement
fib_61_8                  # 61.8% retracement

# Extension levels
fib_ext_127_2             # 127.2% extension
fib_ext_161_8             # 161.8% extension

# Distance to levels
dist_to_fib_38_2          # Current position relative to 38.2%
dist_to_fib_61_8          # Current position relative to 61.8%

# Range context
fib_range_high            # Range high used for calculation
fib_range_low             # Range low used for calculation
```

**Total FIBONACCI_IDX Features:** **10 features**

#### 5.2 FIBONACCI_BQX Features (BQX Fibonacci)
**Table:** `fibonacci_bqx_{pair}` (NEW - TO BUILD)
**Source:** bqx w15_bqx_return
**Lookback:** 100 periods

**Features:** Identical structure (10 features)
- Captures: Support/resistance in momentum space
- Interpretation: BQX near fib level → momentum retracement zone

**Total FIBONACCI_BQX Features:** **10 features**

**FIBONACCI CATEGORY TOTAL:** 10 (idx) + 10 (bqx) = **20 features**

---

### CATEGORY 6: Lagged Features (Memory)

**Purpose:** Capture autocorrelation, persistence, short-term memory

**Source:** Both rate_index and bqx values
**Lags:** 1, 2, 3, 5, 10, 15, 30, 45, 60 (1-60 minutes)

#### 6.1 Lagged Rate Index
**Features (60 total):**
```
rate_idx_lag_{1...60}     # 60 individual lags
```

#### 6.2 Lagged BQX
**Features (60 total):**
```
bqx_lag_{1...60}          # 60 individual lags of w15_bqx_return
```

#### 6.3 Lagged Returns
**Features (60 total):**
```
return_lag_{1...60}       # 1-min return lags
```

**LAGGED CATEGORY TOTAL:** 60 (idx) + 60 (bqx) + 60 (returns) = **180 features**

---

### CATEGORY 7: Moving Averages (EMAs/SMAs)

**Purpose:** Smooth trends, momentum tracking

**Windows:** 5, 10, 20, 50, 100, 200 periods

#### 7.1 Rate Index MAs
**Features (12 total):**
```
sma_{5,10,20,50,100,200}  # Simple moving averages
ema_{5,10,20,50,100,200}  # Exponential moving averages
```

#### 7.2 BQX MAs
**Features (12 total):**
```
bqx_sma_{5,10,20,50,100,200}
bqx_ema_{5,10,20,50,100,200}
```

**MA CATEGORY TOTAL:** 12 (idx) + 12 (bqx) = **24 features**

---

### CATEGORY 8: Cross-Pair Features

**Purpose:** Systemic risk, correlation structure, triangular parity

#### 8.1 Sister-Pair Features
**Pairs:** For each target pair, include 4-5 most related pairs
**Features per sister pair (6 features × 5 pairs = 30 total):**
```
{sister}_return_lag_1     # Immediate return
{sister}_return_lag_5     # 5-min lag
{sister}_return_lag_15    # 15-min lag
{sister}_vol_30           # 30-min volatility
{sister}_corr_60          # 60-min correlation with target
{sister}_beta_60          # 60-min regression beta
```

**Total Sister-Pair Features:** **30 features**

#### 8.2 Triangular Parity
**For applicable triangles (e.g., EUR/USD = EUR/GBP × GBP/USD):**
**Features (8 total):**
```
tri_resid_level           # Current parity residual
tri_resid_z_20            # Z-score (20-period)
tri_resid_change_5        # 5-min change
tri_resid_vol_30          # 30-min volatility
tri_bqx_resid             # BQX momentum parity residual
tri_bqx_resid_z_20        # BQX momentum parity z-score
tri_bqx_change_5          # BQX parity 5-min change
tri_alignment_flag        # Binary: aligned or misaligned
```

**Total Triangular Parity Features:** **8 features**

#### 8.3 USD Factor (Synthetic Dollar Index)
**Features (6 total):**
```
usd_factor_level          # PC1 of USD-majors
usd_factor_change_5       # 5-min change
usd_factor_change_15      # 15-min change
usd_factor_vol_30         # 30-min volatility
usd_factor_z_60           # Z-score (60 period)
usd_factor_trend_20       # 20-period trend slope
```

**Total USD Factor Features:** **6 features**

**CROSS-PAIR CATEGORY TOTAL:** 30 + 8 + 6 = **44 features**

---

### CATEGORY 9: Dual-Domain Comparison Features

**Purpose:** Quantify relationship between rate and BQX, detect decoupling

#### 9.1 Regression Comparisons
**Features (12 total):**
```
# Rate → BQX regression (30-period rolling)
reg_rate_bqx_beta_30      # Slope coefficient
reg_rate_bqx_r2_30        # Fit quality
reg_rate_bqx_resid_z_30   # Residual z-score

# BQX → Rate regression (30-period rolling)
reg_bqx_rate_beta_30      # Reverse slope
reg_bqx_rate_r2_30        # Reverse fit quality
reg_bqx_rate_resid_z_30   # Reverse residual z-score

# Cross-window comparisons
reg_coupling_15_60        # Coupling strength change
reg_decoupling_flag       # Binary: decoupled or not

# Term comparisons (from REG features)
a2_diff_idx_bqx           # Curvature difference
a1_diff_idx_bqx           # Slope difference
b_diff_idx_bqx            # Baseline difference
r2_diff_idx_bqx           # Predictability difference
```

**Total Regression Comparison Features:** **12 features**

#### 9.2 Statistical Comparisons
**Features (10 total):**
```
# Variance ratios
var_ratio_bqx_idx_20      # var(bqx) / var(idx) over 20 periods
var_ratio_bqx_idx_60      # Over 60 periods

# Moment differences
skew_diff_bqx_idx_20      # Skewness difference
kurt_diff_bqx_idx_20      # Kurtosis difference

# Cross-correlations
xcorr_idx_bqx_lag_0       # Contemporaneous correlation
xcorr_idx_bqx_lag_1       # 1-lag cross-correlation
xcorr_idx_bqx_lag_5       # 5-lag cross-correlation
xcorr_idx_bqx_lag_15      # 15-lag cross-correlation

# Volatility comparison
vol_ratio_bqx_idx_30      # BQX vol / idx vol
vol_diff_bqx_idx_30       # Absolute difference
```

**Total Statistical Comparison Features:** **10 features**

#### 9.3 Bollinger Comparisons
**Features (6 total):**
```
bb_z_diff_bqx_idx_20      # Bollinger %B difference
bb_bandwidth_ratio_20     # BQX bandwidth / idx bandwidth
bb_compression_diff_20    # Compression state difference
bb_breakout_divergence    # Breakout timing divergence
bb_slope_diff_20          # Band slope difference
bb_regime_mismatch_flag   # Binary: different regimes
```

**Total Bollinger Comparison Features:** **6 features**

**DUAL-DOMAIN CATEGORY TOTAL:** 12 + 10 + 6 = **28 features**

---

### CATEGORY 10: Time & Calendar Features

**Purpose:** Session effects, intraday patterns, calendar anomalies

#### 10.1 Session Features
**Features (8 total):**
```
session_tokyo             # Binary: Tokyo session active
session_london            # Binary: London session active
session_ny                # Binary: NY session active
session_overlap_ldn_ny    # Binary: London-NY overlap
session_vol_regime        # Categorical: session volatility state
session_hour              # Hour of day (0-23)
session_is_open           # Binary: major session open
session_minutes_to_close  # Minutes until session close
```

**Total Session Features:** **8 features**

#### 10.2 Cyclical Time
**Features (6 total):**
```
time_sin_hour             # sin(2π * hour / 24)
time_cos_hour             # cos(2π * hour / 24)
time_sin_minute           # sin(2π * minute / 1440)
time_cos_minute           # cos(2π * minute / 1440)
time_sin_dow              # sin(2π * day_of_week / 7)
time_cos_dow              # cos(2π * day_of_week / 7)
```

**Total Cyclical Time Features:** **6 features**

#### 10.3 Calendar
**Features (6 total):**
```
dow_monday...friday       # Day of week one-hots (5)
is_month_end              # Binary: within 3 days of month end
is_week_roll              # Binary: week transition
days_to_holiday_us        # Days to next US holiday
days_to_holiday_uk        # Days to next UK holiday
days_to_holiday_jp        # Days to next JP holiday
```

**Total Calendar Features:** **6 features**

**TIME CATEGORY TOTAL:** 8 + 6 + 6 = **20 features**

---

### CATEGORY 11: Microstructure Features

**Purpose:** Liquidity, order flow, spread dynamics

#### 11.1 Spread Features
**Table:** `spread_idx_{pair}` (RENAME from `spread_features_{pair}`)
**Features (12 total):**
```
spread_level              # Current bid-ask spread
spread_pct                # Spread as % of mid
spread_z_20               # Z-score (20 period)
spread_change_5           # 5-min change
spread_vol_30             # 30-min volatility
spread_mean_20            # 20-period mean
spread_max_20             # 20-period max
spread_spike_flag         # Binary: >2σ spike
spread_compression_flag   # Binary: <0.5σ compression
spread_trend_20           # 20-period trend slope
spread_regime             # Categorical: tight/normal/wide
spread_percentile_60      # Percentile in 60-period range
```

**Total Spread Features:** **12 features**

#### 11.2 Volume Features
**Table:** `volume_idx_{pair}` (RENAME from `volume_features_{pair}`)
**Features (15 total):**
```
volume_level              # Current volume
volume_sma_20             # 20-period SMA
volume_std_20             # 20-period std
volume_z_20               # Z-score
volume_spike_flag         # Binary: >2σ spike
volume_change_5           # 5-min change
volume_trend_20           # 20-period trend
volume_regime             # Categorical: low/normal/high

# Volume-price interaction
vol_price_corr_20         # 20-period correlation
vol_return_corr_20        # Volume-return correlation
vol_weighted_price_20     # VWAP approximation

# Volume imbalance (if tick data available)
uptick_ratio_20           # Uptick volume / total volume
downtick_ratio_20         # Downtick volume / total volume
net_flow_20               # Net order flow proxy

# Activity
trade_count_20            # Trades per period (if available)
```

**Total Volume Features:** **15 features**

#### 11.3 Volume-BQX Interaction
**Table:** `volume_bqx_{pair}` (NEW - TO BUILD)
**Features (8 total):**
```
vol_bqx_corr_20           # Volume-BQX correlation (20)
vol_bqx_corr_60           # Volume-BQX correlation (60)
vol_during_bqx_surge      # Volume when BQX >1σ
vol_during_bqx_drop       # Volume when BQX <-1σ
bqx_per_volume_20         # BQX change per unit volume
volume_confirms_bqx_flag  # Binary: volume confirms momentum
volume_diverges_bqx_flag  # Binary: volume diverges from momentum
high_vol_high_bqx_flag    # Binary: both elevated
```

**Total Volume-BQX Features:** **8 features**

**MICROSTRUCTURE CATEGORY TOTAL:** 12 (spread) + 15 (volume) + 8 (vol-bqx) = **35 features**

---

### CATEGORY 12: Event & Regime Detection

**Purpose:** Detect volatility spikes, jumps, regime transitions

#### 12.1 Jump Detection
**Features (8 total):**
```
jump_flag_2_5_sigma       # Binary: |return| > 2.5σ
jump_flag_3_sigma         # Binary: |return| > 3σ
jump_count_20             # Count of jumps in last 20 periods
jump_count_60             # Count of jumps in last 60 periods
time_since_last_jump      # Periods since last jump
jump_direction            # Categorical: up/down/none
jump_magnitude_z          # Z-score of jump size
post_jump_decay_20        # Vol decay after jump (20 periods)
```

**Total Jump Features:** **8 features**

#### 12.2 Volatility Regime
**Features (10 total):**
```
vol_regime_20             # Categorical: low/med/high (20 period)
vol_regime_60             # Categorical (60 period)
vol_regime_transition     # Binary: regime changed recently
vol_z_score_20            # Volatility z-score
vol_percentile_100        # Volatility percentile (100 period)
vol_acceleration_20       # d(volatility)/dt
vol_expansion_flag        # Binary: volatility expanding
vol_compression_flag      # Binary: volatility contracting
ewma_vol_30               # EWMA volatility (30 period)
garch_vol_estimate        # GARCH(1,1) vol estimate (if computed)
```

**Total Volatility Regime Features:** **10 features**

#### 12.3 Trend Regime
**Features (8 total):**
```
trend_regime_20           # Categorical: strong_up/weak_up/range/weak_down/strong_down
trend_regime_60           # Categorical (60 period)
trend_strength_20         # R² of linear fit (20)
trend_strength_60         # R² of linear fit (60)
trend_consistency_20      # Sign agreement across windows
trend_reversal_flag       # Binary: trend direction changed
trend_acceleration_20     # d(trend_slope)/dt
sideways_flag_20          # Binary: low trend strength + low vol
```

**Total Trend Regime Features:** **8 features**

**EVENT & REGIME CATEGORY TOTAL:** 8 + 10 + 8 = **26 features**

---

### CATEGORY 13: Multi-Resolution Features

**Purpose:** Capture patterns at different time scales (1-min, 5-min, 15-min)

**Note:** Resample to 5-min and 15-min aggregates (UP TO TIME i ONLY)

#### 13.1 5-Minute Aggregates
**Features (20 total):**
```
# Compute core stats at 5-min resolution
rate_idx_5m_sma_10        # 10-period SMA on 5-min bars
rate_idx_5m_vol_20        # 20-period vol on 5-min bars
bqx_5m_sma_10             # BQX 5-min SMA
bqx_5m_vol_20             # BQX 5-min vol
return_5m_lag_{1,2,3,5}   # 5-min return lags

# Technical on 5-min
rsi_5m_14                 # RSI on 5-min bars
macd_5m                   # MACD on 5-min bars
atr_5m_14                 # ATR on 5-min bars

# Cross-domain on 5-min
var_ratio_5m_bqx_idx      # Variance ratio on 5-min
xcorr_5m_idx_bqx          # Cross-correlation on 5-min

# Additional
volume_5m_sma_10          # Volume 5-min SMA
spread_5m_mean_10         # Spread 5-min mean
vol_regime_5m             # Volatility regime on 5-min
trend_regime_5m           # Trend regime on 5-min
jump_count_5m_12          # Jump count on 5-min (12 bars = 1 hour)

# Multi-scale comparisons
sma_1m_vs_5m_ratio        # 1-min SMA / 5-min SMA
vol_1m_vs_5m_ratio        # 1-min vol / 5-min vol
trend_1m_vs_5m_agreement  # Binary: trends agree
regime_1m_vs_5m_agreement # Binary: regimes agree
scale_divergence_flag     # Binary: 1m and 5m diverging
```

**Total 5-Minute Features:** **20 features**

#### 13.2 15-Minute Aggregates
**Features (10 total):**
```
# Core stats at 15-min
rate_idx_15m_sma_8        # 8-period SMA on 15-min
bqx_15m_sma_8             # BQX 15-min SMA
rate_idx_15m_vol_12       # Volatility on 15-min
bqx_15m_vol_12            # BQX vol on 15-min
rsi_15m_14                # RSI on 15-min
macd_15m                  # MACD on 15-min

# Multi-scale alignment
sma_5m_vs_15m_ratio       # 5-min SMA / 15-min SMA
trend_5m_vs_15m_agreement # Trend agreement
scale_cascade_aligned     # Binary: 1m, 5m, 15m all aligned
scale_cascade_diverged    # Binary: scales diverging
```

**Total 15-Minute Features:** **10 features**

**MULTI-RESOLUTION CATEGORY TOTAL:** 20 + 10 = **30 features**

---

### CATEGORY 14: Correlation Features (Cross-Pair & Cross-Window)

**Purpose:** Capture co-movement, lead-lag, term structure

#### 14.1 CORRELATION_IDX (Rate Index Correlations)
**Table:** `correlation_idx_{pair}` (RENAME from `correlation_features_{pair}`)
**Features (20 total):**
```
# Cross-pair correlations (20-period rolling)
corr_eur_usd_20
corr_gbp_usd_20
corr_aud_usd_20
corr_nzd_usd_20
corr_usd_jpy_20
# ... (additional major pairs)

# Cross-pair correlations (60-period rolling)
corr_eur_usd_60
corr_gbp_usd_60
# ... (key pairs)

# Variance decomposition
resid_var_systematic      # Explained by common factors
resid_var_idiosyncratic   # Pair-specific variance

# Covariance matrix metrics
cov_determinant_20        # Matrix determinant
cov_trace_20              # Matrix trace
cov_eigenvalue_max_20     # Max eigenvalue (systemic risk)
cov_eigenvalue_ratio_20   # λ1/λ2 (factor concentration)

# Correlation regime
corr_regime_20            # Categorical: high/normal/low correlation
corr_breakout_flag        # Binary: correlation spike/crash
avg_pairwise_corr_20      # Average across all pairs
corr_dispersion_20        # Std dev of pairwise correlations
```

**Total CORRELATION_IDX Features:** **20 features**

#### 14.2 CORRELATION_BQX (BQX Momentum Correlations)
**Table:** `correlation_bqx_{pair}` (NEW - TO BUILD, FINAL STEP)
**Features (25 total):**
```
# Cross-pair BQX correlations (20-period)
bqx_corr_eur_usd_20
bqx_corr_gbp_usd_20
# ... (major pairs)

# Cross-pair BQX correlations (60-period)
bqx_corr_eur_usd_60
# ...

# Cross-window BQX term structure (CRITICAL!)
bqx_corr_w15_w60          # Short vs long momentum correlation
bqx_corr_w30_w60          # Medium vs long
bqx_corr_w45_w60          # 45 vs 60

# Term structure shape
term_slope_bqx            # (w15 - w60) / 45 (momentum curve slope)
term_curvature_bqx        # Parabolic fit of w15,w30,w45,w60,w75
term_inversion_flag       # Binary: w15 < w60 (backwardation)
term_steepness_z          # Z-score of slope

# Momentum variance decomposition
bqx_var_systematic        # Explained by common momentum factors
bqx_var_idiosyncratic     # Pair-specific momentum variance

# Cross-temporal (lead-lag momentum)
bqx_eur_leads_gbp_flag    # Binary: EUR momentum predicts GBP
bqx_eur_gbp_lag_corr_5    # 5-period lead-lag correlation
bqx_eur_gbp_lag_corr_15   # 15-period lead-lag correlation

# Momentum regime
momentum_regime_cluster   # Categorical: risk-on/risk-off/neutral
momentum_dispersion_20    # Cross-pair momentum dispersion
momentum_synchrony_20     # How synchronized are momentums?
momentum_decoupling_flag  # Binary: pairs decoupling

# Triangulation (momentum arbitrage)
bqx_tri_resid_eurusd      # Momentum triangular residual
bqx_tri_resid_z_20        # Z-score of momentum arbitrage
```

**Total CORRELATION_BQX Features:** **25 features**

**CORRELATION CATEGORY TOTAL:** 20 (idx) + 25 (bqx) = **45 features**

---

## COMPLETE FEATURE COUNT SUMMARY

| Category | Rate Index (idx) | BQX | Shared/Other | Total |
|----------|-----------------|-----|--------------|-------|
| 1. Regression (Quadratic Terms) | 90 | 90 | - | **180** |
| 2. Statistical Moments | 24 | 24 | - | **48** |
| 3. Bollinger Bands | 10 | 10 | - | **20** |
| 4. Technical Momentum Indicators | 15 | 15 | - | **30** |
| 5. Fibonacci Levels | 10 | 10 | - | **20** |
| 6. Lagged Features | 60 | 60 | 60 (returns) | **180** |
| 7. Moving Averages (EMA/SMA) | 12 | 12 | - | **24** |
| 8. Cross-Pair Features | - | - | 44 | **44** |
| 9. Dual-Domain Comparisons | - | - | 28 | **28** |
| 10. Time & Calendar | - | - | 20 | **20** |
| 11. Microstructure (Spread/Volume) | 27 | 8 | - | **35** |
| 12. Event & Regime Detection | - | - | 26 | **26** |
| 13. Multi-Resolution (5m, 15m) | - | - | 30 | **30** |
| 14. Correlation Features | 20 | 25 | - | **45** |
| **GRAND TOTAL** | **268** | **254** | **208** | **730** |

---

## Feature Implementation Priority

### Phase 1: Foundation (Already Exists or In Progress)
✅ REG_IDX (rename from reg_{pair})
✅ REG_BQX (already exists)
✅ STATISTICS_IDX (rename from statistics_features)
✅ BOLLINGER_IDX (rename from bollinger_features)
✅ FIBONACCI_IDX (rename from fibonacci_features)
✅ Volume_IDX (rename from volume_features)
✅ Spread_IDX (rename from spread_features)
✅ Time features (already exists)

### Phase 2: BQX Duals (High Priority - TO BUILD)
🔨 STATISTICS_BQX
🔨 BOLLINGER_BQX
🔨 TECHNICAL_IDX (new)
🔨 TECHNICAL_BQX (new)
🔨 FIBONACCI_BQX
🔨 VOLUME_BQX

### Phase 3: Advanced Features (Medium Priority)
🔨 Dual-domain comparisons
🔨 Cross-pair features
🔨 Multi-resolution features
🔨 Event & regime detection

### Phase 4: Correlation Features (FINAL STEP)
🔨 CORRELATION_IDX (populate, currently empty)
🔨 CORRELATION_BQX (build after all BQX features complete)

---

## Database Table Inventory (Complete)

### Tables to RENAME (Already Populated)
```sql
reg_{pair}                  → reg_idx_{pair}                (336 partitions)
statistics_features_{pair}  → statistics_idx_{pair}         (336 partitions)
bollinger_features_{pair}   → bollinger_idx_{pair}          (336 partitions)
fibonacci_features_{pair}   → fibonacci_idx_{pair}          (336 partitions)
volume_features_{pair}      → volume_idx_{pair}             (336 partitions)
spread_features_{pair}      → spread_idx_{pair}             (336 partitions)
correlation_features_{pair} → correlation_idx_{pair}        (336 partitions, EMPTY)
```

### Tables to BUILD (New BQX Duals)
```sql
statistics_bqx_{pair}       (336 partitions)
bollinger_bqx_{pair}        (336 partitions)
technical_idx_{pair}        (336 partitions) - NEW
technical_bqx_{pair}        (336 partitions)
fibonacci_bqx_{pair}        (336 partitions)
volume_bqx_{pair}           (336 partitions)
correlation_bqx_{pair}      (336 partitions)
```

### Derived/Computed Features (Not separate tables)
- Lagged features: Computed in feature engineering pipeline
- Moving averages: Computed in pipeline
- Cross-pair features: Computed by joining tables
- Dual-domain comparisons: Computed from idx + bqx tables
- Time features: Already exist
- Event/regime features: Computed in pipeline
- Multi-resolution: Computed by resampling

**Total Tables:** 
- Rename: 7 feature types × 28 pairs = 196 parent tables
- Build new: 7 feature types × 28 pairs = 196 parent tables
- **Grand Total: 392 parent tables + partitions**

---

## Validation & Quality Checks

### Per Feature Type Validation
```sql
-- Row counts should match
SELECT 
  'statistics_idx' as type, COUNT(*) as partitions, SUM(n_live_tup) as rows
FROM pg_stat_user_tables 
WHERE schemaname = 'bqx' AND relname LIKE 'statistics_idx_%'
UNION ALL
SELECT 
  'statistics_bqx', COUNT(*), SUM(n_live_tup)
FROM pg_stat_user_tables 
WHERE schemaname = 'bqx' AND relname LIKE 'statistics_bqx_%';

-- Expected: Same row counts for idx and bqx versions
```

### Value Range Validation
```sql
-- RSI should be 0-100 for both idx and bqx
SELECT 
  'technical_idx' as type,
  MIN(rsi_14) as min_rsi, 
  MAX(rsi_14) as max_rsi
FROM bqx.technical_idx_eurusd
UNION ALL
SELECT 
  'technical_bqx',
  MIN(rsi_14), 
  MAX(rsi_14)
FROM bqx.technical_bqx_eurusd;
```

### Cross-Architecture Correlation Check
```sql
-- Verify idx and bqx features are not perfectly correlated (information redundancy check)
-- Expect correlation < 0.95 (if higher, one representation may be redundant)
```

---

## Feature Engineering Pipeline Notes

### Window Computation Rules
1. **All windows end at time i** (no look-ahead)
2. **Consistent normalization**: Learn normalization params on train set, apply to val/test
3. **Handle missing data**: Forward-fill small gaps (<5 mins), add filled_flag features
4. **Cross-pair alignment**: Left-join on timestamp, forward-fill, keep missing_rate features

### Target Engineering
```python
# Vol-scaled targets (recommended)
target_15 = (bqx_{i+15} - bqx_i) / ewma_vol_60
target_30 = (bqx_{i+30} - bqx_i) / ewma_vol_60
target_45 = (bqx_{i+45} - bqx_i) / ewma_vol_60
target_60 = (bqx_{i+60} - bqx_i) / ewma_vol_60
target_75 = (bqx_{i+75} - bqx_i) / ewma_vol_60

# Optional: direction targets for multi-task
direction_15 = sign(bqx_{i+15} - bqx_i)  # {-1, 0, 1}
# ... (for each horizon)
```

### Feature Selection Strategy
**Initial: 730 features → Select top 150-200 via:**
1. Random Forest feature importance (Phase 3)
2. Remove features with importance < threshold
3. Remove highly correlated features (ρ > 0.95)
4. Domain knowledge curation (keep key dual-domain features)

---

## Success Criteria

### Completeness
- [ ] All 392 parent tables exist (196 renamed + 196 new)
- [ ] All ~5,712 partitions populated (336 × 17 feature types)
- [ ] Row counts validated (idx = bqx = ~10.3M rows per feature type)
- [ ] Value ranges validated (RSI 0-100, z-scores reasonable, etc.)

### Quality
- [ ] No NULL values except initial lookback periods
- [ ] Cross-architecture correlations measured
- [ ] Feature importance analysis complete
- [ ] Leakage validation tests pass (no future data in features)

### ML Readiness
- [ ] Feature engineering pipeline operational
- [ ] Training datasets exported (S3 Parquet)
- [ ] Feature selection complete
- [ ] Ready for Phase 3 model training

---

## References

- [User Expectations Document](../BQX ML User Expectations 2025 1112.docx)
- [Comprehensive Feature Development Plan](./comprehensive_feature_development_plan.md)
- [Dual Feature Architecture Rationalization](./dual_feature_architecture_rationalization.md)
- [AirTable Project Plan](https://airtable.com/appR3PPnrNkVo48mO)

---

**Status:** Complete feature inventory - Ready for implementation
**Next Step:** Begin Phase 1.6.9 (table renaming) + Phase 2 (build BQX duals)
**Estimated Total Implementation Time:** 60-80 hours (can parallelize to 20-25 hours wall time)
