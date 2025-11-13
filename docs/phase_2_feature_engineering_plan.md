# Phase 2: Feature Engineering Pipeline - Execution Plan

**Date:** 2025-11-13
**Status:** Ready to Begin
**Prerequisite:** Phase 1 Complete (1,060 features, 98.1%)
**Duration:** 14-18 weeks (can be parallelized to 8-10 weeks)
**Objective:** Transform 1,060 base features → ~2,640 with lags → ~250 selected features

---

## Executive Summary

Phase 2 transforms the 1,060 feature schemas from Phase 1 into a production-ready ML pipeline by:
1. **Populating** all feature tables with computed values
2. **Extracting** features into datasets
3. **Applying** lagging strategy for temporal dependencies
4. **Selecting** top 250 features via importance ranking
5. **Creating** train/val/test datasets for model training

**Key Innovation:** Prioritized implementation allows quick wins while building comprehensive system.

---

## Phase 2 Structure

### Stage 2.1: Feature Population Workers (8-12 weeks)

**Objective:** Implement computation logic for all 1,060 features

#### Priority Tier 1: Core Features (Week 1-4, 500 features)

**Regression Features (180 features) - WEEK 1-2**
- Already populated from Phase 1: reg_rate_{pair}, reg_bqx_{pair}
- Action: Verify data quality, add missing windows
- Duration: 3 days
- Status: ✅ Mostly complete

**Statistical Moments (48 features) - WEEK 2**
- Tables: statistics_rate_{pair}, statistics_bqx_{pair}
- Computation: Rolling windows (15, 30, 45, 60, 75 min)
- Features: mean, std, skew, kurtosis, min, max
- Duration: 2 days
- Dependencies: M1 data (rate_index, BQX)

**Technical Indicators (60 features) - WEEK 2-3**
- Tables: technical_rate_{pair}, technical_bqx_{pair}
- Indicators: RSI, MACD, Stochastic, ADX, CCI, etc.
- Libraries: TA-Lib or pandas_ta
- Duration: 5 days

**Bollinger Bands (20 features) - WEEK 3**
- Tables: bollinger_rate_{pair}, bollinger_bqx_{pair}
- Computation: SMA ± k*std, band width, %B
- Duration: 2 days

**Fibonacci Levels (20 features) - WEEK 3**
- Tables: fibonacci_rate_{pair}, fibonacci_bqx_{pair}
- Computation: Swing high/low, retracement levels
- Duration: 2 days

**Volume & Spread (70 features) - WEEK 3-4**
- Tables: volume_features_{pair}, spread_features_{pair}
- Already partially populated
- Action: Complete missing features
- Duration: 3 days

**Time & Calendar (20 features) - WEEK 4**
- Table: time_features_{pair}
- Features: Hour, day of week, session, holidays
- Duration: 1 day
- Status: ✅ Likely complete

**Moving Averages (24 features) - WEEK 4**
- Computed features (no dedicated table)
- SMA/EMA on rate_index and BQX
- Duration: 1 day

**Correlation (90 features) - WEEK 4**
- Tables: correlation_rate_{pair}, correlation_bqx_{pair}
- Cross-window, cross-pair correlations
- Duration: 3 days

**Priority Tier 1 Total: ~500 features, 4 weeks**

#### Priority Tier 2: Advanced Features Wave 1 (Week 5-8, 130 features)

**Error Correction Models (24 features) - WEEK 5-6**
- Tables: error_correction_rate_{pair}, error_correction_bqx_{pair}
- Algorithm: Johansen cointegration
- Dependencies: Cross-pair data
- Complexity: HIGH
- Duration: 10 days

**Realized Volatility (30 features) - WEEK 6-7**
- Tables: realized_volatility_rate_{pair}, realized_volatility_bqx_{pair}
- Estimators: Parkinson, GK, RS, YZ, bipower variance
- Dependencies: OHLC data from M1 tables
- Complexity: MEDIUM
- Duration: 7 days

**HMM Regime Detection (30 features) - WEEK 7**
- Tables: hmm_regime_rate_{pair}, hmm_regime_bqx_{pair}
- Algorithm: K=3 Hidden Markov Model
- Libraries: hmmlearn
- Complexity: HIGH
- Duration: 5 days

**Cross-Sectional Panel (46 features) - WEEK 7-8**
- Table: cross_sectional_panel
- Computation: Ranks, percentiles, dispersion across 8 major pairs
- Dependencies: All pairs simultaneously
- Complexity: MEDIUM
- Duration: 7 days

**Priority Tier 2 Total: ~130 features, 4 weeks**

#### Priority Tier 3: Spectral Features (Week 9-11, 164 features)

**Parabolic Comparisons (44 features) - WEEK 9**
- Tables: parabolic_comparison_rate_{pair}, parabolic_comparison_bqx_{pair}
- Computation: Cross-window ratio analysis
- Dependencies: Regression features
- Complexity: LOW
- Duration: 3 days

**Multi-Scale Features (60 features) - WEEK 9-10**
- Tables: multi_scale_30m/60m_{rate/bqx}_{pair}
- Computation: Resample to 30m/60m, compute aggregates
- Libraries: pandas resample
- Complexity: MEDIUM
- Duration: 5 days

**Spectral Features (60 features) - WEEK 10-11**
- FFT (24 features): scipy.fft
- Wavelets (20 features): pywt (Daubechies db4)
- SSA (16 features): Custom implementation
- Complexity: HIGH
- Duration: 10 days

**Priority Tier 3 Total: ~164 features, 3 weeks**

#### Priority Tier 4: Final Advanced Features (Week 12, 162 features)

**Advanced Microstructure (40 features) - WEEK 12**
- Tables: advanced_microstructure_{rate/bqx}_{pair}
- Features: Amihud, Kyle λ, VPIN
- Dependencies: Order book data (may not be available)
- Complexity: VERY HIGH
- Fallback: Use proxy metrics from available data
- Duration: 7 days (with fallbacks)

**Lagged Cross-Window (50 features) - WEEK 12**
- Tables: lagged_cross_window_{rate/bqx}_{pair}
- Computation: Temporal dependencies across windows
- Complexity: MEDIUM
- Duration: 3 days

**Volatility Surface (30 features) - WEEK 12**
- Tables: volatility_surface_{rate/bqx}_{pair}
- Features: Term structure, GARCH forecasts
- Complexity: HIGH
- Duration: 5 days

**Market Regime + Liquidity (42 features) - WEEK 12**
- Tables: market_regime_{rate/bqx}_{pair}, liquidity_metrics_{rate/bqx}_{pair}
- Computation: Regime classification, liquidity indicators
- Complexity: MEDIUM
- Duration: 4 days

**Priority Tier 4 Total: ~162 features, 1 week (aggressive)**

### Stage 2.2: Feature Extraction (Week 13-14, 2 weeks)

**Objective:** Extract all computed features into datasets

**Task 2.2.1: Database Query Optimization**
- Create efficient SQL queries for feature extraction
- Use composite indexes for ts_utc + pair
- Batch queries to minimize database round-trips
- Duration: 2 days

**Task 2.2.2: Feature Extraction Pipeline**
- Python script to extract all features per pair
- Handle missing values (forward fill, interpolation)
- Validate temporal alignment
- Output: Parquet files per pair
- Duration: 3 days

**Task 2.2.3: Data Validation**
- Check for NaN/inf values
- Verify temporal causality (no future data leakage)
- Statistical sanity checks
- Duration: 3 days

**Task 2.2.4: Feature Dataset Creation**
- Combine all features into single dataframe per pair
- Align timestamps across all feature families
- Handle different partition ranges (rate vs bqx)
- Duration: 4 days

**Stage 2.2 Output:** 28 feature datasets (one per pair), ~1,060 columns each

### Stage 2.3: Lagging Strategy (Week 15, 1 week)

**Objective:** Apply temporal lags to create ~2,640 features

**Lagging Rules:**
- **Laggable features** (520 features): Apply 4 lags (60, 120, 180, 240 min)
  - Regression features
  - Technical indicators
  - Statistical moments
  - Volatility metrics
  - Result: 520 × 5 (base + 4 lags) = 2,600 features

- **Non-laggable features** (540 features): Keep as-is
  - Time & calendar (categorical)
  - Index values (current state only)
  - Some cross-sectional features

- **Temporal causality features** (40 additional): 61-min lag for w60/agg families
  - Prevents using future information in 60-min window features

**Implementation:**
- Pandas shift operation
- Validate no future leakage
- Handle edge cases (start of series)

**Stage 2.3 Output:** ~2,640 features per pair

### Stage 2.4: Feature Selection (Week 16-17, 2 weeks)

**Objective:** Select top ~250 features from ~2,640

**Method: Random Forest Feature Importance**

**Step 1: Train Random Forest**
- Use all ~2,640 features
- Target: BQX change at each horizon (15/30/45/60/75 min)
- Multi-output Random Forest
- 100 trees, max_depth=10
- Duration: 2 days

**Step 2: Compute Importance Scores**
- Extract feature_importances_
- Aggregate across all 5 target horizons
- Rank features by cumulative importance
- Duration: 1 day

**Step 3: Select Top 250**
- Cumulative importance > 95% threshold
- Ensure dual architecture balance:
  - Minimum 100 rate_idx features
  - Minimum 100 BQX features
  - Remaining 50: highest importance
- Duration: 1 day

**Step 4: Validate Selection**
- Retrain model with selected 250 features
- Compare R² to full model (should be >95% of full model R²)
- Check for domain coverage
- Duration: 3 days

**Step 5: Cross-Validation**
- 5-fold cross-validation
- Verify feature importance stability
- Duration: 2 days

**Stage 2.4 Output:** 250 selected features per pair

### Stage 2.5: Dataset Creation (Week 18, 1 week)

**Objective:** Create train/val/test datasets for model training

**Task 2.5.1: Split Strategy**
- Temporal split (no shuffling): 70/15/15
- Train: First 70% of timeline
- Val: Next 15%
- Test: Last 15%
- Ensures temporal causality
- Duration: 1 day

**Task 2.5.2: Target Engineering**
- Multi-horizon targets: BQX change at 15/30/45/60/75 min
- Classification targets: Direction (up/down/neutral)
- Volatility-scaled targets: BQX_change / realized_volatility
- Duration: 2 days

**Task 2.5.3: Feature Scaling**
- StandardScaler per feature
- Fit on train, transform val/test
- Save scalers for inference
- Duration: 1 day

**Task 2.5.4: Final Dataset Export**
- Save as Parquet (compressed)
- Structure: train/{pair}.parquet, val/{pair}.parquet, test/{pair}.parquet
- Metadata: feature names, scaler parameters
- Duration: 2 days

**Stage 2.5 Output:** Production-ready datasets for 28 pairs

---

## Parallel Execution Strategy

**Aggressive Timeline: 8-10 weeks**

### Wave 1: Core Features (Parallel, Week 1-4)
- Team 1: Regression + Statistical (already done, verify only)
- Team 2: Technical indicators
- Team 3: Bollinger + Fibonacci
- Team 4: Volume + Spread + Time

### Wave 2: Advanced Wave 1 (Parallel, Week 5-8)
- Team 1: Error Correction Models
- Team 2: Realized Volatility + HMM
- Team 3: Cross-Sectional Panel

### Wave 3: Spectral (Parallel, Week 9-11)
- Team 1: Parabolic + Multi-Scale
- Team 2: FFT + Wavelets
- Team 3: SSA

### Wave 4: Final Features (Week 12)
- All teams: Remaining features with fallbacks

### Wave 5: Pipeline (Week 13-18)
- Extraction, lagging, selection, datasets (sequential)

---

## Technology Stack

### Languages & Frameworks
- **Python 3.9+**: Primary language
- **pandas**: Data manipulation
- **NumPy**: Numerical computations
- **psycopg2**: PostgreSQL connector
- **scikit-learn**: Feature selection, scaling
- **TA-Lib / pandas_ta**: Technical indicators

### Specialized Libraries
- **scipy**: FFT, signal processing
- **PyWavelets (pywt)**: Wavelet transforms
- **statsmodels**: Statistical models, GARCH
- **hmmlearn**: Hidden Markov Models
- **pykalman**: Kalman filters (optional)

### Infrastructure
- **Aurora PostgreSQL**: Feature database
- **S3**: Dataset storage
- **EC2**: Computation workers
- **SageMaker**: Model training (Phase 3)

---

## Risk Assessment

### High Risks

**1. Data Availability for Advanced Features**
- Issue: Some features require data not in M1 tables (order book, implied volatility)
- Mitigation: Implement proxy metrics using available data
- Fallback: Skip features if critical data unavailable

**2. Computation Time for Complex Features**
- Issue: FFT, wavelets, HMM can be slow on large datasets
- Mitigation: Parallel processing, vectorization, Cython
- Fallback: Sample-based computation, reduce frequency

**3. Feature Selection Instability**
- Issue: Different runs may select different features
- Mitigation: Cross-validation, ensemble selection
- Fallback: Use domain knowledge to force key features

### Medium Risks

**4. Memory Constraints**
- Issue: 2,640 features × millions of rows
- Mitigation: Process pairs separately, use chunking
- Fallback: Use larger EC2 instances

**5. Temporal Leakage**
- Issue: Accidentally using future information
- Mitigation: Rigorous validation, causal graph analysis
- Testing: Backtesting with strict timeline

---

## Success Criteria

✅ **Feature Population:** All 1,060 features computed
✅ **Data Quality:** <1% missing values, no temporal leakage
✅ **Feature Selection:** 250 features identified with >95% R² retention
✅ **Dataset Creation:** Train/val/test splits for all 28 pairs
✅ **Validation:** Cross-validation R² matches expectations
✅ **Performance:** Feature extraction <10 min per pair

---

## Phase 2 Deliverables

1. **Feature Population Workers** (Python scripts)
   - 10-15 worker scripts for different feature families
   - Documented, tested, production-ready

2. **Populated Feature Database**
   - All 1,060 features with actual values
   - Validated data quality

3. **Feature Extraction Pipeline**
   - Efficient SQL queries + Python pipeline
   - Handles all 28 pairs

4. **Selected Features List**
   - 250 features per pair (or shared across pairs)
   - Importance scores, descriptions

5. **Training Datasets**
   - Train/val/test Parquet files
   - Metadata, scalers, documentation

6. **Documentation**
   - Feature engineering guide
   - API documentation
   - Troubleshooting guide

---

## Recommended Next Action

**Option A: Begin Priority Tier 1 (Core Features)**
- Start with regression, statistical, technical features
- Quick wins: 500 features in 4 weeks
- Enables early ML experimentation

**Option B: Audit Existing Features First**
- Check which Phase 1.6 tables are already populated
- May have 300-400 features ready to use
- Build pipeline with available features immediately

**Option C: Create MVP Pipeline**
- Use minimal feature set (100-200 features)
- Build end-to-end pipeline quickly
- Validate approach before full implementation

---

## Transition to Phase 3

After Phase 2 completion, transition to:

**Phase 3: Model Training & Deployment**
- Train models for all 28 pairs
- Deploy to SageMaker endpoints
- Real-time inference pipeline
- Production monitoring

**Estimated Timeline:** Phase 2 (14-18 weeks) → Phase 3 (8-12 weeks) → Production (Month 7-8)

---

## Conclusion

Phase 2 transforms the 1,060-feature schema architecture into a production ML pipeline through systematic feature population, extraction, lagging, selection, and dataset creation.

**Key Phases:**
- 🔧 Stage 2.1: Feature Population (8-12 weeks)
- 📊 Stage 2.2: Feature Extraction (2 weeks)
- ⏱️ Stage 2.3: Lagging Strategy (1 week)
- 🎯 Stage 2.4: Feature Selection (2 weeks)
- 📦 Stage 2.5: Dataset Creation (1 week)

**Total Duration:** 14-18 weeks (can parallelize to 8-10 weeks)

**Next Step:** Begin Stage 2.1 - Feature Population Workers (Priority Tier 1)

🚀 **Phase 2 Ready to Begin** 🚀
