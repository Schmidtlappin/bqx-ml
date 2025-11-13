# Phase 2.1: Feature Population Workers - Execution Plan (Based on Audit)

**Date:** 2025-11-13
**Status:** Ready to Execute
**Audit Completion:** Feature population audit complete
**Current State:** 159/1,060 features populated (15.0%)

---

## Executive Summary

**Audit Results:**
- ✅ **Populated:** 159 features (15.0%) - bollinger_rate, statistics_rate, volume_features, spread_features, time_features
- ❌ **Empty Schemas:** 901 features (85.0%) - All other feature families

**Critical Finding:** Regression features (reg_rate, reg_bqx) that were expected to be populated from previous work **DO NOT EXIST**. These tables were never created.

**Impact:** We need to implement 901 features from scratch, not 500 as originally planned.

---

## Current Populated Features (159 features, 10.3M rows each)

| Feature Family | Features | Tables | Rows | Status |
|---------------|----------|--------|------|--------|
| bollinger_rate | 10 | 364 | 10,315,898 | ✅ POPULATED |
| statistics_rate | 24 | 364 | 10,315,898 | ✅ POPULATED |
| volume_features | 70 | 364 | 10,315,898 | ✅ POPULATED |
| spread_features | 35 | 364 | 10,315,898 | ✅ POPULATED |
| time_features | 20 | 364 | 10,315,896 | ✅ POPULATED |
| **Total** | **159** | **1,820** | **51,579,488** | **15.0%** |

**Note:** All populated features are from the **rate domain only**. No BQX features are populated.

---

## Priority Execution Plan

### Wave 1: Critical Missing Features (Week 1-2)

**Objective:** Complete the populated feature families by adding their BQX counterparts

#### 1.1 Bollinger BQX (10 features, 2 days)

**Status:** bollinger_rate populated, bollinger_bqx EMPTY
**Tables:** 700 (28 pairs × 25 monthly partitions)
**Computation:** Apply same logic as bollinger_rate but to BQX momentum
**Dependencies:** BQX data from m1 tables
**Worker:** `scripts/ml/populate_bollinger_bqx_worker.py`

**Implementation:**
```python
# For each partition:
1. Read BQX momentum (w15, w30, w45, w60, w75)
2. Compute SMA ± k*std for each window
3. Calculate band width, %B
4. Insert into bollinger_bqx_{pair}_{YYYY_MM}
```

#### 1.2 Statistics BQX (24 features, 2 days)

**Status:** statistics_rate populated, statistics_bqx EMPTY
**Tables:** 700
**Computation:** Rolling statistical moments on BQX
**Worker:** `scripts/ml/populate_statistics_bqx_worker.py`

#### 1.3 Technical Indicators Rate + BQX (60 features, 5 days)

**Status:** Both EMPTY (schemas created but not populated)
**Tables:** 1,400 (700 rate + 700 bqx)
**Computation:** RSI, MACD, Stochastic, ADX, CCI using TA-Lib
**Worker:** `scripts/ml/populate_technical_indicators_worker.py`

**Wave 1 Total:** 94 features, 9 days → 253 features populated (23.9%)

---

### Wave 2: Regression Features (Week 3-4)

**CRITICAL:** These features don't exist and need to be created

#### 2.1 Regression Rate + BQX (180 features, 10 days)

**Status:** Tables DO NOT EXIST (contrary to previous assumptions)
**Tables:** 0 → Need to create 1,064 tables (28 pairs × 38 partitions)
**Features per family:** 90 (regression coefficients across 6 windows × 15 metrics)

**Implementation Steps:**
1. **Create tables** (if not exist): Use Phase 1.6 schemas
2. **Compute regression features:**
   - Parabolic fits (a2, a1, b) for windows: w15, w30, w45, w60, w75, agg
   - R², RMSE, residuals, prediction intervals
   - Compute for both rate_index and BQX momentum
3. **Populate partitions** in parallel

**Worker:** `scripts/ml/populate_regression_features_worker.py`

**Wave 2 Total:** 180 features, 10 days → 433 features populated (40.8%)

---

### Wave 3: Core Feature Expansion (Week 5-6)

#### 3.1 Fibonacci Levels (20 features, 3 days)

**Status:** Tables DO NOT EXIST
**Tables:** 0 → Need to create 728 tables
**Computation:** Swing high/low detection, retracement levels (23.6%, 38.2%, 50%, 61.8%, 78.6%)

#### 3.2 Correlation Features (90 features, 5 days)

**Status:** Tables DO NOT EXIST
**Tables:** 0 → Need to create 728 tables
**Computation:** Cross-window correlations, cross-pair correlations

**Wave 3 Total:** 110 features, 8 days → 543 features populated (51.2%)

---

### Wave 4: Advanced Features Wave 1 (Week 7-10)

#### 4.1 Error Correction Models (24 features, 10 days)

**Tables:** 1,064 (schemas exist, EMPTY)
**Complexity:** HIGH - Requires Johansen cointegration
**Worker:** `scripts/ml/populate_error_correction_worker.py`

#### 4.2 Realized Volatility (30 features, 7 days)

**Tables:** 1,064 (schemas exist, EMPTY)
**Estimators:** Parkinson, Garman-Klass, Rogers-Satchell, Yang-Zhang
**Worker:** `scripts/ml/populate_realized_volatility_worker.py`

#### 4.3 HMM Regime Detection (30 features, 7 days)

**Tables:** 1,064 (schemas exist, EMPTY)
**Complexity:** HIGH - K=3 Hidden Markov Model
**Libraries:** hmmlearn
**Worker:** `scripts/ml/populate_hmm_regime_worker.py`

#### 4.4 Cross-Sectional Panel (46 features, 7 days)

**Tables:** 13 (schemas exist, EMPTY)
**Computation:** Ranks, percentiles, dispersion across 8 major pairs
**Worker:** `scripts/ml/populate_cross_sectional_worker.py`

**Wave 4 Total:** 130 features, 31 days → 673 features populated (63.5%)

---

### Wave 5: Spectral Features (Week 11-14)

#### 5.1 Parabolic Comparisons (44 features, 3 days)

**Tables:** 1,064 (schemas exist, EMPTY)
**Complexity:** LOW - Ratios of regression coefficients
**Dependencies:** Regression features from Wave 2
**Worker:** `scripts/ml/populate_parabolic_comparison_worker.py`

#### 5.2 Multi-Scale Features (60 features, 5 days)

**Tables:** 2,128 (30m and 60m, schemas exist, EMPTY)
**Computation:** Resample to 30m/60m, compute aggregates
**Worker:** `scripts/ml/populate_multi_scale_worker.py`

#### 5.3 Spectral: FFT + Wavelets + SSA (60 features, 14 days)

**Tables:** 3,192 (schemas exist, EMPTY)
**Complexity:** HIGH
- FFT: scipy.fft for frequency analysis
- Wavelets: PyWavelets (Daubechies db4)
- SSA: Custom Singular Spectrum Analysis
**Workers:**
- `scripts/ml/populate_spectral_fft_worker.py`
- `scripts/ml/populate_wavelet_worker.py`
- `scripts/ml/populate_ssa_worker.py`

**Wave 5 Total:** 164 features, 22 days → 837 features populated (79.0%)

---

### Wave 6: Final Advanced Features (Week 15-18)

#### 6.1 Advanced Microstructure (40 features, 10 days)

**Tables:** 1,064 (schemas exist, EMPTY)
**Complexity:** VERY HIGH
**Features:** Amihud illiquidity, Kyle λ, VPIN
**Fallback:** Use proxy metrics if order book data unavailable
**Worker:** `scripts/ml/populate_microstructure_worker.py`

#### 6.2 Lagged Cross-Window (50 features, 5 days)

**Tables:** 1,064 (schemas exist, EMPTY)
**Computation:** Temporal dependencies across windows
**Worker:** `scripts/ml/populate_lagged_cross_window_worker.py`

#### 6.3 Volatility Surface + GARCH (30 features, 7 days)

**Tables:** 1,064 (schemas exist, EMPTY)
**Computation:** Term structure, GARCH forecasts
**Libraries:** statsmodels.tsa.garch
**Worker:** `scripts/ml/populate_volatility_surface_worker.py`

#### 6.4 Market Regime + Liquidity (42 features, 7 days)

**Tables:** 2,128 (schemas exist, EMPTY)
**Computation:** Regime classification, liquidity indicators
**Worker:** `scripts/ml/populate_regime_liquidity_worker.py`

**Wave 6 Total:** 162 features, 29 days → 999 features populated (94.2%)

---

## Revised Timeline

### Conservative Timeline: 18 weeks (126 days)

| Wave | Features | Duration | Cumulative | % Complete |
|------|----------|----------|------------|------------|
| Wave 0 (Current) | 159 | - | 159 | 15.0% |
| Wave 1 | 94 | 9 days | 253 | 23.9% |
| Wave 2 | 180 | 10 days | 433 | 40.8% |
| Wave 3 | 110 | 8 days | 543 | 51.2% |
| Wave 4 | 130 | 31 days | 673 | 63.5% |
| Wave 5 | 164 | 22 days | 837 | 79.0% |
| Wave 6 | 162 | 29 days | 999 | 94.2% |
| **Total** | **840** | **109 days** | **999** | **94.2%** |

**Note:** Timeline excludes final 61 features (remaining 5.8%) pending specification

### Aggressive Parallel Timeline: 10-12 weeks

**Assumptions:** 3 parallel development teams

- Team 1: Core features (Waves 1-3)
- Team 2: Advanced features (Wave 4)
- Team 3: Spectral features (Wave 5-6)

---

## Implementation Priority

### Phase 2.1a: MVP Quick Wins (Week 1-4)

**Goal:** Get to 50% populated ASAP

1. **Wave 1:** Complete BQX counterparts + Technical indicators → 253 features (23.9%)
2. **Wave 2:** Regression features → 433 features (40.8%)
3. **Wave 3:** Fibonacci + Correlation → 543 features (51.2%)

**Deliverable:** 543 features in 4 weeks → Enables early ML experimentation

### Phase 2.1b: Production Features (Week 5-18)

**Goal:** Complete all advanced features

4. **Wave 4-6:** Advanced, spectral, and final features → 999 features (94.2%)

**Deliverable:** Production-ready 1,000-feature database

---

## Worker Architecture

### Generic Worker Template

Each worker follows this pattern:

```python
#!/usr/bin/env python3
"""
Feature Population Worker: {FEATURE_FAMILY}
Populates {TABLE_PREFIX}_{pair}_{YYYY_MM} tables
"""

import psycopg2
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import logging

class FeaturePopulationWorker:
    def __init__(self, feature_family, pairs, date_range):
        self.feature_family = feature_family
        self.pairs = pairs
        self.date_range = date_range
        self.conn = self.get_db_connection()

    def get_db_connection(self):
        return psycopg2.connect(...)

    def compute_features(self, pair, year_month):
        """
        Main computation logic for feature family.
        Returns: DataFrame with ts_utc + feature columns
        """
        # 1. Fetch source data (M1 tables)
        df = self.fetch_source_data(pair, year_month)

        # 2. Compute features
        features = self.calculate_features(df)

        # 3. Validate
        self.validate_features(features)

        return features

    def calculate_features(self, df):
        """
        Feature-specific computation logic.
        Implement in subclass.
        """
        raise NotImplementedError

    def populate_partition(self, pair, year_month):
        """
        Populate single partition with features.
        """
        try:
            features = self.compute_features(pair, year_month)

            # Bulk insert
            table_name = f"{self.feature_family}_{pair}_{year_month}"
            self.bulk_insert(table_name, features)

            logging.info(f"✅ {table_name}: {len(features)} rows")
        except Exception as e:
            logging.error(f"❌ {table_name}: {str(e)}")

    def run(self, max_workers=6):
        """
        Populate all partitions in parallel.
        """
        tasks = [(pair, ym) for pair in self.pairs
                           for ym in self.date_range]

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            executor.map(self.populate_partition_wrapper, tasks)

if __name__ == '__main__':
    worker = FeaturePopulationWorker(
        feature_family='bollinger_bqx',
        pairs=['audcad', 'audchf', ...],  # 28 pairs
        date_range=['2024_07', '2024_08', ...]  # 12-25 months
    )
    worker.run()
```

---

## Success Criteria

✅ **Wave 1 (MVP):** 253 features (23.9%) in 9 days
✅ **Wave 2-3 (50% Goal):** 543 features (51.2%) in 27 days
✅ **Wave 4-6 (Production):** 999 features (94.2%) in 109 days
✅ **Data Quality:** <1% missing values per feature
✅ **Performance:** <5 min per partition per feature family
✅ **Validation:** All features pass sanity checks

---

## Risks and Mitigation

### High Risks

**1. Regression Features Don't Exist**
- **Impact:** 180 features (17%) missing foundation
- **Mitigation:** Create tables first using Phase 1.6 schemas
- **Timeline:** Add 1 day for table creation

**2. Missing Source Data**
- **Impact:** Some advanced features require data not in M1 tables
- **Mitigation:** Implement proxy metrics, graceful degradation
- **Example:** Use spread/volume proxies for microstructure features

**3. Computation Performance**
- **Impact:** Some features (HMM, FFT, wavelets) computationally expensive
- **Mitigation:** Parallel processing (6 workers), vectorization, Cython
- **Fallback:** Reduce frequency, use sampling

---

## Recommended Next Action

**Option A: Begin Wave 1 Immediately**
- Start with bollinger_bqx, statistics_bqx, technical indicators
- Quick wins: 94 features in 9 days
- Low risk, high confidence

**Option B: Create Regression Tables First**
- Critical missing foundation (180 features)
- Blocks Wave 5 (parabolic comparisons depend on regression)
- Medium risk, high priority

**Option C: Build MVP Pipeline with Existing 159 Features**
- Skip population, build Stages 2.2-2.5 with 159 features
- Validate pipeline architecture
- Add features incrementally

---

## Conclusion

The feature population audit revealed that **only 159/1,060 features (15.0%) are populated**, significantly less than expected. The regression features that were assumed populated **do not exist**.

**Phase 2.1 now requires ~18 weeks to populate all 1,060 features**, not the originally planned 8-12 weeks.

**Recommended Path:**
1. **Weeks 1-4:** MVP (Waves 1-3) → 543 features (51.2%)
2. **Weeks 5-18:** Production (Waves 4-6) → 999 features (94.2%)
3. **Parallel Track:** Build extraction pipeline (Stage 2.2) using MVP features

This allows early ML experimentation while systematically building the full feature database.

---

**Status:** Ready to begin Wave 1 - Core Feature Expansion
**Next Step:** Implement `populate_bollinger_bqx_worker.py`

🚀 **Phase 2.1 Execution Ready** 🚀
