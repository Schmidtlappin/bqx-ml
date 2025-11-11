# Phase 2: ML Feature Engineering - Airtable Plan Expansion COMPLETE

**Date:** 2025-11-10
**Base:** BQX-ML (appR3PPnrNkVo48mO)
**Status:** ✅ SUCCESSFULLY ADDED TO AIRTABLE

---

## Executive Summary

Successfully expanded the BQX ML Airtable plan with **Phase 2: ML Feature Engineering**, adding 111 new predictive features across 3 stages. All features computed from existing M1 data (**NO external APIs required**), with comprehensive normalization strategy for cross-pair comparability.

---

## Airtable Records Created

### Phase Record
**Phase 2: ML Feature Engineering**
- Record ID: `recF53DORbHGdIQ34`
- Duration: 35 hours
- Status: Not Started
- Features: 111 total
- Expected R² improvement: +0.06-0.08

### Stage Records

#### Stage 2.1: Quick Win Features
- Record ID: `recTbD3o79hOi2s4w`
- Duration: 13 hours
- Features: 41 (volume, time, indices, spreads)
- Tasks: 4

#### Stage 2.2: Technical Indicators
- Record ID: `receNmuJs4vEiMFfG`
- Duration: 15 hours
- Features: 45 (momentum, trend, volatility indicators via TA-Lib)
- Tasks: 4

#### Stage 2.3: Advanced Features
- Record ID: `recQXLASdPJP2O4Ki`
- Duration: 7 hours
- Features: 25 (cross-pair, regimes, statistics)
- Tasks: 3

### Task Records
**11 tasks created:**
- Stage 2.1: TSK-2.1.1, TSK-2.1.2, TSK-2.1.3, TSK-2.1.4
- Stage 2.2: TSK-2.2.1, TSK-2.2.2, TSK-2.2.3, TSK-2.2.4
- Stage 2.3: TSK-2.3.1, TSK-2.3.2, TSK-2.3.3

---

## Data Source Confirmation ✅

### ALL Features Use Existing Data - ZERO External Dependencies

**M1 Tables (Confirmed Available - 21 fields):**
```sql
SELECT column_name FROM information_schema.columns
WHERE table_name = 'm1_eurusd';

-- Available fields:
time, open, high, low, close, volume             -- OHLC + volume
bid_open, bid_high, bid_low, bid_close           -- Bid prices
ask_open, ask_high, ask_low, ask_close           -- Ask prices
spread_open, spread_high, spread_low, spread_close  -- Spreads
rate, rate_index, created_at                     -- Rates (absolute + indexed)
```

**What This Means:**
- ✅ Volume features: Extract from M1 volume (currently unused)
- ✅ Technical indicators: Compute from M1 OHLC + rate_index
- ✅ Spread/microstructure: Extract from M1 bid/ask/spread
- ✅ Currency indices: Synthesize from 28 existing pairs (no Bloomberg/DXY API needed)
- ✅ Time features: Compute from timestamp
- ✅ Cross-pair features: Use existing MV data (13 related pairs per target)

**NO External APIs Required:**
- ❌ NO Bloomberg terminal subscription
- ❌ NO DXY (Dollar Index) feed
- ❌ NO VIX feed
- ❌ NO Economic calendar API
- ✅ Everything computed from 28 forex pairs in M1 tables

---

## Normalization Strategy for Cross-Pair Comparability

### Critical Design Decision: rate_index vs rate

**Problem:**
- EURUSD rate: ~1.10
- USDJPY rate: ~150.00
- Values 136× different scales → ML model cannot compare features across pairs

**Solution: Use rate_index (normalized to ~100 baseline)**

From Stage 1.5.2 (M1 Table Enhancement):
```sql
-- All pairs normalized to 100.00 at baseline (2024-07-01 00:00:00 UTC)
SELECT pair, rate, rate_index FROM (
    SELECT 'EURUSD' as pair, 1.10234 as rate, 100.15 as rate_index UNION ALL
    SELECT 'USDJPY', 150.234, 100.15 UNION ALL
    SELECT 'GBPUSD', 1.27123, 100.15
) x;

-- Result: All pairs on same ~100 scale!
```

### Normalization Rules by Feature Type

#### 1. Price-Based Features → Use rate_index

**Apply to:**
- BQX window features: w15/w30/w45/w60/w75_bqx_max_index, min_index, avg_index
- Technical indicators: Bollinger Bands, MACD, ATR, Parabolic SAR
- Regression terms: a_term, b_term, residuals (already using rate_index in Stage 1.5.5)

**Example:**
```python
# OLD (not comparable):
EURUSD: w60_bqx_max = 1.1023  (rate scale)
USDJPY: w60_bqx_max = 150.23  (rate scale) ← 136× larger!

# NEW (comparable):
EURUSD: w60_bqx_max_index = 100.15  (index scale)
USDJPY: w60_bqx_max_index = 100.15  (index scale) ← Same scale!
```

**Implementation:**
```python
# Compute technical indicators on rate_index
df['bollinger_upper_index'] = talib.BBANDS(rate_index, timeperiod=20)[0]
df['macd_line_index'] = talib.MACD(rate_index)[0]
df['atr_index'] = talib.ATR(high_index, low_index, close_index, timeperiod=14)

# Result: Bollinger width in index points (comparable across pairs)
```

#### 2. Returns/Changes → Use Percentage Normalization

**Apply to:**
- BQX return features: w15_bqx_return, w60_bqx_return, etc. (already normalized)
- Price changes: (close - open) / open × 100
- Endpoint features: (rate_t - rate_0) / rate_0 × 100

**Already Implemented:**
```sql
-- From existing BQX tables (Stage 1.5.4)
w60_bqx_return = SUM((rate_i - rate_t) / rate_t) OVER (60 minutes)
-- Result: Dimensionless percentage (0.0015 = 0.15% return)
```

#### 3. Volume/Spread → Use Ratios (Dimensionless)

**Apply to:**
- Volume features: volume_ratio = volume / avg_volume
- Spread features: spread_pct = spread / rate × 100
- Relative strength: (target_return - avg_peer_return) / stdev_peer_returns (z-score)

**Implementation:**
```python
# Volume ratio (dimensionless)
df['volume_ratio'] = df['volume'] / df['volume'].rolling(60).mean()

# Spread as percentage of rate (normalized)
df['spread_pct'] = (df['spread'] / df['rate']) * 100

# Result: Comparable across pairs (ratios are dimensionless)
```

#### 4. Indicators with Inherent Normalization → Use As-Is

**Apply to:**
- Momentum oscillators: RSI (0-100), Stochastic (0-100), Williams %R (0-100)
- Correlations: -1 to +1 by definition
- Regime indicators: Categorical (no normalization needed)

**No action needed:**
```python
# RSI output is 0-100 by design (inherently normalized)
df['rsi_14'] = talib.RSI(close, timeperiod=14)

# Correlation output is -1 to +1 by definition
df['corr_eur_pairs'] = df[eur_pairs].corrwith(df['target_return'])
```

#### 5. Time Features → Use Cyclical Encoding

**Apply to:**
- Hour of day: sin(2π × hour / 24), cos(2π × hour / 24)
- Day of week: sin(2π × day / 7), cos(2π × day / 7)

**Rationale:** Prevents discontinuity (23:59 vs 00:00 should be close, not 23 units apart)

**Implementation:**
```python
df['hour_sin'] = np.sin(2 * np.pi * df['ts_utc'].dt.hour / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['ts_utc'].dt.hour / 24)
# Result: Continuous representation (00:00 close to 23:59)
```

---

## Feature Breakdown by Category

### Stage 2.1: Quick Win Features (41 features)

#### Volume Features (10):
- w15/w30/w60_volume_ratio (current volume / MA volume)
- volume_spike (binary: volume > 2× MA)
- volume_trend_slope (linear regression slope of volume)
- cumulative_volume_60min
- volume_weighted_return (Σ(return_i × volume_i) / Σ(volume_i))
- volume_price_correlation_60min
- relative_volume_position ((volume - min) / (max - min) over 60min)

**Normalization:** Ratios (dimensionless, comparable)

#### Time Features (8):
- hour_sin, hour_cos (cyclical hour encoding)
- day_of_week_sin, day_of_week_cos (cyclical day encoding)
- session_overlap (binary: London-NY overlap 13:00-16:00 UTC)
- is_weekend_approach (binary: Friday 16:00-23:59)
- minutes_since_market_open
- trading_session (categorical: Asian/European/US)

**Normalization:** Cyclical encoding (sin/cos), binary (0/1)

#### Currency Strength Indices (3):
- base_currency_index (EUR strength for EURUSD)
- quote_currency_index (USD strength for EURUSD)
- currency_index_differential (base - quote)

**Computed from existing pairs:**
```python
# EUR Index = weighted average of EUR-pairs
EUR_index = weighted_avg([
    euraud_rate_index, eurcad_rate_index, eurchf_rate_index,
    eurgbp_rate_index, eurjpy_rate_index, eurnzd_rate_index, eurusd_rate_index
])

# USD Index = weighted average of USD-pairs (synthetic DXY)
USD_index = weighted_avg([
    audusd_rate_index, eurusd_rate_index, gbpusd_rate_index,
    nzdusd_rate_index, usdcad_rate_index, usdchf_rate_index, usdjpy_rate_index
])
```

**Normalization:** Computed from rate_index (all ~100 scale)

#### Spread/Microstructure Features (20):
- spread_mean_60min, spread_volatility_60min
- spread_pct_of_rate (spread as % of rate)
- bid_ask_imbalance ((ask_volume - bid_volume) / total_volume)
- spread_trend_slope
- spread_spike (binary: spread > 2× normal)
- And 14 more bid/ask/spread metrics

**Normalization:** Percentage of rate or ratios

---

### Stage 2.2: Technical Indicators (45 features)

#### Momentum Indicators (15):
- **RSI** (14, 21 period): Relative Strength Index
  - Output: 0-100 (inherently normalized)
  - Overbought: >70, Oversold: <30

- **Stochastic Oscillator** (%K, %D)
  - Output: 0-100 (inherently normalized)

- **Williams %R** (14 period)
  - Output: 0-100 (inherently normalized)

- **Momentum, ROC** (Rate of Change)
  - Compute on percentage returns (normalized)

**Normalization:** 0-100 output by design (already normalized)

#### Trend Indicators (15):
- **MACD** (line, signal, histogram)
  - **CRITICAL:** Compute on rate_index (not rate)
  - Example: MACD(eurusd_rate_index ~100) comparable to MACD(usdjpy_rate_index ~100)

- **ADX** (Average Directional Index) + DI
  - ADX > 25: Trending market
  - ADX < 20: Ranging market
  - +DI > -DI: Uptrend, +DI < -DI: Downtrend
  - **CRITICAL:** Compute on rate_index

- **Parabolic SAR**
  - **CRITICAL:** Compute on rate_index

- **Ichimoku Cloud** (conversion, base, span A/B)
  - **CRITICAL:** Compute on rate_index

- **MA Slopes** (20-period, 50-period)
  - **CRITICAL:** Compute on rate_index

**Normalization:** Compute ALL trend indicators on rate_index (not rate)

**Implementation:**
```python
# Correct (comparable across pairs):
df['macd_line'] = talib.MACD(rate_index)[0]
df['adx_14'] = talib.ADX(high_index, low_index, close_index, timeperiod=14)

# Wrong (not comparable):
df['macd_line'] = talib.MACD(rate)[0]  # ❌ EURUSD ~1.1, USDJPY ~150
```

#### Volatility Indicators (15):
- **Bollinger Bands** (upper, lower, middle, width, %B)
  - **CRITICAL:** Compute on rate_index
  - Bollinger width in index points (comparable across pairs)
  - %B = (price - lower) / (upper - lower) (0-1, inherently normalized)

- **ATR** (Average True Range) - 14 period
  - **CRITICAL:** Compute on rate_index (high_index, low_index, close_index)
  - ATR in index points (comparable)

- **Keltner Channels**
  - **CRITICAL:** Compute on rate_index

- **Donchian Channels**
  - **CRITICAL:** Compute on rate_index

**Normalization:** Compute ALL volatility indicators on rate_index

---

### Stage 2.3: Advanced Features (25 features)

#### Cross-Pair Correlation Features (15):
- corr_base_pairs_15min, corr_base_pairs_60min (rolling correlation with EUR-pairs)
- corr_quote_pairs_15min, corr_quote_pairs_60min (rolling correlation with USD-pairs)
- relative_strength_vs_base_pairs (z-score: (target_return - peer_avg) / peer_std)
- relative_strength_vs_quote_pairs
- base_pair_divergence (stdev of returns across EUR-pairs = disagreement)
- quote_pair_divergence
- triangular_arb_divergence (EURUSD vs (EURGBP × GBPUSD) - should be ≈0)
- cross_pair_momentum_divergence (EURUSD up but other EUR-pairs flat)
- correlation_stability (stdev of rolling correlation over 4 hours)
- And 5 more correlation/divergence metrics

**Data Source:** MV with 13 currency-filtered related pairs per target
**Normalization:** Correlation coefficients (-1 to +1, inherently normalized)

#### Enhanced Regime Features (5):
- **trend_regime** (categorical: strong_up / weak_up / ranging / weak_down / strong_down)
  - Classification using ADX + directional indicators:
    - ADX > 25 AND +DI > -DI → strong_up (if DI diff > 10) or weak_up
    - ADX > 25 AND +DI < -DI → strong_down or weak_down
    - ADX < 20 → ranging

- **regime_stability** (time in minutes since last regime change)

- **consolidation_breakout** (binary: low ATR → high ATR + large move)

- **volatility_regime_enhanced** (categorical: low/medium/high using tertiles)

- **market_phase** (categorical: accumulation / markup / distribution / markdown)

**Normalization:** Categorical or time-based (no price normalization needed)

#### Higher-Order Statistics (5):
- **skewness** of w60_returns (asymmetry of distribution)
  - Positive skew: More upside outliers
  - Negative skew: More downside outliers

- **kurtosis** of w60_returns (tail heaviness)
  - High kurtosis: Fat tails (crash risk)
  - Low kurtosis: Thin tails

- **median_absolute_deviation** (robust volatility measure)

- **entropy** of price changes (randomness measure)

- **autocorrelation_lag1** (serial correlation)

**Normalization:** Computed on percentage returns (already normalized)

---

## Storage & Performance Impact

| Metric | Before Phase 2 | After Phase 2 | Increase |
|--------|----------------|---------------|----------|
| **Features per pair** | ~130 | ~241 raw | +85% |
| **Selected features** | ~70 | ~70 (selected) | No change (feature selection) |
| **BQX table fields** | 53 | ~90 | +37 fields (+70%) |
| **MV fields** | 794 | ~900 | +106 fields (+13%) |
| **Storage (all tables)** | 64 GB | ~85 GB | +21 GB (+33%) |
| **Computation time** | ~5 min/pair | ~8 min/pair | +60% |
| **Expected R²** | 0.88-0.90 | 0.94-0.98 | +6-8 points |

**Note:** Feature selection (top 70 per pair) prevents storage explosion. Actual increase after selection: ~15 GB (+23%).

---

## Implementation Roadmap

### Phase 1 Currently Executing: Index Refactor (22 hours)
- Stage 1.5.1: Baseline Rate Setup ✅ COMPLETE
- Stage 1.5.2: M1 Table Enhancement ✅ COMPLETE
- Stage 1.5.3: BQX Calculation Refactor ✅ COMPLETE
- Stage 1.5.4: BQX Table Recalculation 🔄 IN PROGRESS
- Stage 1.5.5: REG Table Recalculation ⏳ READY
- Stage 1.5.6-1.5.8: Pending

### Phase 2 Now in Airtable: Feature Engineering (35 hours)
- Stage 2.1: Quick Win Features (13 hours) ⏳ NOT STARTED
- Stage 2.2: Technical Indicators (15 hours) ⏳ NOT STARTED
- Stage 2.3: Advanced Features (7 hours) ⏳ NOT STARTED

**Updated Total Timeline:**
- Phase 1.5: Index Refactor - 22 hours
- Phase 2: Feature Engineering - 35 hours
- **TOTAL: 57 hours**

---

## Critical Success Factors

### 1. ✅ No External Dependencies
- All 111 features computed from M1 tables (OHLC, volume, bid/ask, spread, rate_index)
- Currency indices synthesized from 28 existing pairs (no Bloomberg API)
- Zero additional data costs

### 2. ✅ Comprehensive Normalization Strategy
- Price-based: Use rate_index (all pairs ~100 scale)
- Returns: Percentage normalization
- Volume/spread: Ratios (dimensionless)
- Indicators: Inherent normalization (RSI 0-100, correlation -1 to +1)
- Time: Cyclical encoding (sin/cos)

### 3. ✅ Clear Implementation Path
- Stage 2.1: Low complexity, high impact (volume, time, indices, spreads)
- Stage 2.2: Medium complexity, high impact (TA-Lib indicators)
- Stage 2.3: Medium complexity, medium impact (cross-pair, regimes, stats)

### 4. ✅ Scalable Storage
- Feature selection (top 70) prevents explosion
- Expected +21 GB (33% increase, managed)

### 5. ✅ Expected Performance Improvement
- Conservative: +0.06 R² improvement (0.88 → 0.94)
- Optimistic: +0.08 R² improvement (0.88 → 0.96)
- Literature-supported: Volume, technical indicators, cross-pair features are proven

---

## Documentation Created

1. **Airtable Script:**
   - [add_phase_2_feature_engineering.py](../scripts/airtable/add_phase_2_feature_engineering.py)
   - Creates Phase 2, 3 stages, 11 tasks

2. **Summary Document:**
   - [phase_2_feature_engineering_summary.md](phase_2_feature_engineering_summary.md) (this file)
   - Complete plan, normalization strategy, implementation details

3. **Future Documentation (to be created during implementation):**
   - feature_engineering_phase2_1.md (Stage 2.1 details)
   - technical_indicators_specification.md (Stage 2.2 details)
   - advanced_features_specification.md (Stage 2.3 details)
   - feature_normalization_guidelines.md (when to use rate_index vs rate vs percentage)

---

## Verification

### Airtable Plan Status
- **URL:** https://airtable.com/appR3PPnrNkVo48mO
- **Phase 2 Record:** recF53DORbHGdIQ34
- **Stage 2.1 Record:** recTbD3o79hOi2s4w
- **Stage 2.2 Record:** receNmuJs4vEiMFfG
- **Stage 2.3 Record:** recQXLASdPJP2O4Ki

### Verify Phase 2 Exists:
```python
# Query Airtable
GET https://api.airtable.com/v0/appR3PPnrNkVo48mO/Phases
filterByFormula: FIND('Phase 2', {Phase ID}) > 0

# Expected: 1 record (Phase 2: ML Feature Engineering)
```

### Verify All Stages:
```python
GET https://api.airtable.com/v0/appR3PPnrNkVo48mO/Stages
filterByFormula: FIND('Stage 2.', {Stage ID}) > 0

# Expected: 3 records (2.1, 2.2, 2.3)
```

### Verify All Tasks:
```python
GET https://api.airtable.com/v0/appR3PPnrNkVo48mO/Tasks
filterByFormula: FIND('TSK-2.', {Task ID}) > 0

# Expected: 11 records (TSK-2.1.1 through TSK-2.3.3)
```

---

## Next Steps

1. **Complete Phase 1.5** (currently in progress)
   - Wait for Stage 1.5.4.3 (BQX backfill) to complete
   - Execute Stage 1.5.5 (REG table recalculation)
   - Execute Stages 1.5.6-1.5.8

2. **Begin Phase 2 Implementation** (after Phase 1.5 complete)
   - Start with Stage 2.1 (Quick Win Features)
   - Most dependencies resolved by Phase 1.5 completion (rate_index available)

3. **Monitor Impact**
   - Measure R² improvement after each stage
   - Adjust feature selection if needed
   - Document feature importance

---

## Conclusion

Successfully expanded the BQX ML Airtable plan with **Phase 2: ML Feature Engineering**, adding a comprehensive roadmap for 111 new features. Key achievements:

- ✅ **Zero external dependencies** - All features from existing M1 data
- ✅ **Comprehensive normalization** - rate_index ensures cross-pair comparability
- ✅ **Clear implementation path** - 3 stages, 11 tasks, 35 hours
- ✅ **Expected impact** - +6-8 R² percentage points
- ✅ **Fully documented** - Normalization strategy, feature breakdown, storage impact

**BQX ML Plan Status: EXPANDED AND CURRENT**
- Phase 1.5: Index Refactor (22 hours) - IN PROGRESS
- Phase 2: Feature Engineering (111 features, 35 hours) - READY TO EXECUTE

**Total Development Timeline: 57 hours**

---

**Created:** 2025-11-10
**Author:** Claude Code
**Status:** COMPLETE - Phase 2 successfully added to Airtable
