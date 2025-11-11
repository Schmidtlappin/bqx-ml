# BQX ML Gap Remediation - Comprehensive Plan

**⚠️ SUPERSEDED BY:** See [gap_remediation_corrected.md](gap_remediation_corrected.md) for corrected version
**⚠️ FEATURE COUNT CORRECTED:** 228 base features (not 111) - See [feature_count_reconciliation.md](feature_count_reconciliation.md)

**Plan Date:** 2025-11-11
**Current Status:** 50% Complete (56/228 base features implemented, excluding BQX 40 + REG 57)
**Critical Path:** Track 1 Completion → Track 2 Parallel Execution → Validation & QA
**Estimated Completion:** 30 hours (2-3 days with parallel execution)

**IMPORTANT CORRECTIONS:**
- Original "111 features" excluded BQX (40), REG (57), and derived (3) features
- Arithmetic error: Stated 55 missing, actually 72 (15 + 45 + 12 = 72)
- With lagging: 809 total features (4 lag windows + causality)
- After selection: 70 features used for model training
- See Phase 3 SageMaker plan for complete ML pipeline: [sagemaker_phase3_deployment_plan.md](sagemaker_phase3_deployment_plan.md)

---

## EXECUTIVE SUMMARY

### Gap Analysis Summary

**COMPLETED:**
- 18/111 features (16%): Volume (10), Currency Indices (8)
- OHLC index columns in all M1 tables (CRITICAL BLOCKER REMOVED)
- Infrastructure: 2,251 tables created (~96%)

**IN PROGRESS:**
- 38/111 features (34%): Statistics (5), Bollinger (5), Time (8), Spread (20)
- Current workers: 24.7% and 35.4% complete respectively

**GAPS IDENTIFIED:**
- 55/111 features (50%): Correlation (15), Technical Indicators (45), Fibonacci (12)
- Missing 3 worker scripts
- Missing 250+ storage tables
- Incomplete validation and documentation

### Critical Path to 100%

```
PHASE 1: Complete Track 1 (12 hours)
  Current Workers Complete (6h) → Correlation Worker (4h dev + 6h run) = 16h total

PHASE 2-3: Parallel Execution (23 hours)
  ├─ Track 2: Technical Indicators (1h tables + 6h dev + 17h run) = 24h
  └─ Track 3: Fibonacci Features (0.5h tables + 4h dev + 5h run) = 9.5h

PHASE 4: Validation & QA (8 hours)
  Feature Catalog (2h) + Validation Suite (4h) + ML Integration Guide (2h)

PHASE 5: Final Certification (2 hours)

TOTAL WALL TIME: ~30 hours (with parallel execution)
```

---

## PHASE 1: COMPLETE TRACK 1 - CRITICAL PRIORITY

**Objective:** Finish all 66 unblocked features
**Timeline:** 16 hours (6h wait + 4h dev + 6h run)
**Blocker Status:** CRITICAL (blocks all downstream work)

### Stage 1.6.6: Correlation Features Implementation

**Duration:** 10 hours (4h dev + 6h backfill)
**Dependencies:** Statistics/Bollinger and Time/Spread workers complete
**Priority:** CRITICAL

#### Tasks:

**TSK-1.6.6.1: Design Correlation Features Specification (2 hours)**
- Document 15 cross-pair correlation features
- Define correlation windows (15min, 60min, 240min)
- Specify related pair selection (13 related pairs per target using MV filtering)
- Algorithm: Rolling Pearson correlation on rate_index
- Storage schema: correlation_features_{pair} tables

**TSK-1.6.6.2: Develop correlation_features_worker.py (4 hours)**
- Input: BQX filtered pair MVs (13 related pairs per target)
- Features: 15 correlation metrics at different windows and lags
- Correlation algorithm: Pandas rolling correlation on rate_index
- ThreadPoolExecutor: 4 threads (requires multi-pair joins, higher memory)
- Progress tracking: 336 partitions (28 pairs × 12 months)
- Expected throughput: ~2,000 rows/sec (complex joins)

**TSK-1.6.6.3: Execute Correlation Features Backfill (6 hours)**
- Run worker across 336 partitions
- Monitor: `/tmp/correlation_worker.log`
- Expected output: ~10M rows per pair
- Validation: Check correlation values in [-1, +1] range

**TSK-1.6.6.4: Validate Correlation Features (1 hour)**
- Verify correlation values: -1 ≤ r ≤ +1
- Check for perfect correlations (may indicate data leakage)
- Validate lag correlations: lag-1 should be highest for trending pairs
- Create completion report

**Success Criteria:**
- ✅ 15/15 correlation features computed
- ✅ 336/336 partitions populated
- ✅ ~10M rows per pair
- ✅ Correlation values within valid range
- ✅ Track 1 completion report published

---

## PHASE 2: TRACK 2 - TECHNICAL INDICATORS (HIGH PRIORITY)

**Objective:** Implement 45 OHLC-dependent features (NOW UNBLOCKED)
**Timeline:** 24 hours (1h tables + 6h dev + 17h backfill)
**Blocker Status:** UNBLOCKED (OHLC index columns present)
**Parallel Execution:** Can run with Fibonacci features

### Stage 1.6.7: Technical Indicators Implementation

**Duration:** 24 hours
**Dependencies:** M1 OHLC index columns (COMPLETE)
**Priority:** HIGH

#### Tasks:

**TSK-1.6.7.1: Install and Test TA-Lib (30 minutes)**
- Install TA-Lib C library: `sudo apt-get install ta-lib`
- Install Python wrapper: `pip install TA-Lib`
- Test TA-Lib functions: RSI, MACD, ADX, ATR
- Verify compatibility with numpy arrays

**TSK-1.6.7.2: Create Technical Indicators Storage Tables (1 hour)**
- File: `scripts/ml/create_technical_indicators_tables.sql`
- Tables: technical_indicators_{pair} (28 parent + 336 partitions)
- Schema: 45 DOUBLE PRECISION columns:
  - Momentum (11): RSI, Stochastic, Williams %R, ROC, MFI, CMO, etc.
  - Trend (13): MACD, ADX, Parabolic SAR, Ichimoku, Aroon, CCI, etc.
  - Volatility (10): ATR, Keltner, Donchian, Bollinger Width, etc.
  - Partial (11): TRIX, Ultimate Oscillator, Chaikin, etc.
- Monthly partitions: 2024-07 to 2025-06
- Indexes: UNIQUE BTREE on ts_utc

**TSK-1.6.7.3: Design Technical Indicators Specification (2 hours)**
- Document all 45 TA-Lib indicators with parameters
- Justify parameter choices (e.g., RSI period=14, why?)
- Expected value ranges for each indicator
- Normalization strategy: Use *_index columns for cross-pair comparability
- Literature references for indicator effectiveness in forex

**TSK-1.6.7.4: Develop technical_indicators_worker.py (6 hours)**
- Input: M1 tables with OHLC index columns
- TA-Lib integration: Wrap all 45 indicator functions
- Error handling: TA-Lib functions can return NaN for insufficient data
- Lookback windows: Varies by indicator (ADX needs 14-28 periods)
- ThreadPoolExecutor: 8 threads (TA-Lib functions are CPU-intensive)
- Progress tracking: 336 partitions
- Expected throughput: ~1,200 rows/sec (TA-Lib overhead)

**TSK-1.6.7.5: Execute Technical Indicators Backfill (17 hours)**
- Run worker across 336 partitions
- Monitor: `/tmp/technical_indicators_worker.log`
- Expected output: ~10M rows per pair
- Watch for: Memory usage (TA-Lib can spike), CPU at 90%+

**TSK-1.6.7.6: Validate Technical Indicators (2 hours)**
- RSI: Verify 0 ≤ RSI ≤ 100
- ADX: Verify ADX > 0
- Stochastic: Verify 0 ≤ %K, %D ≤ 100
- MACD: Check signal crossovers are reasonable
- Cross-pair comparability: EURUSD RSI should be comparable to USDJPY RSI
- Create completion report with indicator effectiveness analysis

**Success Criteria:**
- ✅ 45/45 technical indicators computed
- ✅ TA-Lib integration validated
- ✅ All indicators within expected ranges
- ✅ Cross-pair comparability verified
- ✅ Completion report published

---

## PHASE 3: FIBONACCI FEATURES (MEDIUM PRIORITY - PARALLEL)

**Objective:** Implement 12 Fibonacci retracement/extension features
**Timeline:** 9.5 hours (0.5h tables + 4h dev + 5h backfill)
**Blocker Status:** UNBLOCKED (OHLC index columns present)
**Parallel Execution:** Run concurrently with Technical Indicators

### Stage 1.6.8: Fibonacci Features Implementation

**Duration:** 9.5 hours
**Dependencies:** M1 OHLC index columns (COMPLETE)
**Priority:** MEDIUM
**Specification:** `/home/ubuntu/bqx-ml/docs/fibonacci_features_specification.md`

#### Tasks:

**TSK-1.6.8.1: Create Fibonacci Storage Tables (30 minutes)**
- File: `scripts/ml/create_fibonacci_tables.sql`
- Tables: fibonacci_features_{pair} (28 parent + 336 partitions)
- Schema: 12 DOUBLE PRECISION columns:
  - Retracement (5): 23.6%, 38.2%, 50%, 61.8%, 78.6%
  - Extension (3): 127.2%, 161.8%, 261.8%
  - Meta (4): nearest_level, grid_position, time_since_swing, grid_strength
- Monthly partitions: 2024-07 to 2025-06
- Indexes: UNIQUE BTREE on ts_utc

**TSK-1.6.8.2: Develop Williams Fractals Algorithm (2 hours)**
- Algorithm: 5-bar pattern for swing detection (n=3)
- Swing High: high[i-2] < high[i-1] < high[i] > high[i+1] > high[i+2]
- Swing Low: low[i-2] > low[i-1] > low[i] < low[i+1] < low[i+2]
- Confirmation: 2-bar delay after peak/trough
- Test cases: Verify detection on known swing points

**TSK-1.6.8.3: Develop fibonacci_features_worker.py (4 hours)**
- Input: M1 tables with high_index, low_index
- Swing detection: Williams Fractals (n=3)
- Fibonacci calculations: Distance to retracement/extension levels
- Meta features: Grid position, strength (ATR-normalized), time since swing
- ThreadPoolExecutor: 8 threads
- Progress tracking: 336 partitions
- Expected throughput: ~3,000 rows/sec (simpler than TA-Lib)

**TSK-1.6.8.4: Execute Fibonacci Features Backfill (5 hours)**
- Run worker across 336 partitions
- Monitor: `/tmp/fibonacci_worker.log`
- Expected output: ~10M rows per pair
- Validation: Swing frequency 5-15 per 1000 bars

**TSK-1.6.8.5: Validate Fibonacci Features (1 hour)**
- Verify swing detection frequency: 5-15 swings per 1000 bars (typical)
- Grid strength distribution: 0.3-2.5 (ATR-normalized range)
- Check Fibonacci level spacing: levels should be ordered correctly
- Manual spot-check: Compare detected swings to chart analysis
- Create completion report

**Success Criteria:**
- ✅ 12/12 Fibonacci features computed
- ✅ Williams Fractals algorithm validated
- ✅ Swing detection frequency within expected range
- ✅ Grid strength distribution reasonable
- ✅ Completion report published

---

## PHASE 4: VALIDATION & QUALITY ASSURANCE (MEDIUM PRIORITY)

**Objective:** Systematic validation of all 111 features + comprehensive documentation
**Timeline:** 8 hours
**Priority:** MEDIUM (can start as features complete)

### Stage 1.6.9: Comprehensive Feature Validation

**Duration:** 4 hours
**Dependencies:** All features implemented
**Priority:** MEDIUM

#### Tasks:

**TSK-1.6.9.1: Create Automated Validation Suite (2 hours)**
- File: `scripts/ml/validate_all_features.py`
- Checks:
  - Feature value range validation (RSI 0-100, correlations -1 to +1, etc.)
  - NULL value audit (0% NULL after warmup period)
  - Cross-feature correlation matrix (detect redundancy)
  - Normalization verification (rate_index comparability across pairs)
  - Cyclical encoding continuity (hour_sin/cos, day_of_week_sin/cos)
- Output: Validation report with pass/fail per feature type

**TSK-1.6.9.2: Execute Full Validation Suite (1 hour)**
- Run validation across all 111 features
- Sample 10,000 rows per feature type for statistical tests
- Generate validation dashboard (pass/fail summary)
- Flag any features with anomalies for investigation

**TSK-1.6.9.3: Query Performance Benchmarking (1 hour)**
- Test query: Fetch all 111 features for single timestamp
- Measure: Query latency with partition pruning
- Target: <5ms per partition (acceptable for ML training)
- Optimize: Add indexes if needed, analyze slow queries
- Document: Query patterns for ML integration

**Success Criteria:**
- ✅ Automated validation suite created
- ✅ All 111 features pass range/NULL checks
- ✅ Query performance acceptable (<5ms target)
- ✅ Validation dashboard published

### Stage 1.6.10: Documentation Completion

**Duration:** 4 hours
**Dependencies:** All features implemented
**Priority:** MEDIUM

#### Tasks:

**TSK-1.6.10.1: Create Feature Catalog (2 hours)**
- File: `docs/feature_catalog_comprehensive.md`
- Content for each of 111 features:
  - Feature name and description
  - Formula/algorithm
  - Normalization method
  - Expected value range
  - Interpretation guidelines (what does high/low value mean?)
  - Dependencies (which M1 columns required)
  - Typical values (mean, median, std dev)
- Organize by category: Volume, Time, Spread, Statistics, Bollinger, Correlation, Technical Indicators, Fibonacci

**TSK-1.6.10.2: Create ML Integration Guide (2 hours)**
- File: `docs/ml_integration_guide.md`
- Content:
  - How to query features for training data (example SQL)
  - Handling NULL values (strategies: drop, forward-fill, interpolate)
  - Feature selection by prediction horizon (15min, 30min, 60min)
  - Cross-pair training (using rate_index normalization)
  - Time-series cross-validation (respecting temporal order)
  - Feature importance analysis (which features matter most?)
  - Example training pipeline (end-to-end code)

**Success Criteria:**
- ✅ Feature catalog with all 111 features documented
- ✅ ML integration guide with code examples
- ✅ Documentation reviewed and published

---

## PHASE 5: FINAL CERTIFICATION (LOW PRIORITY)

**Objective:** Certify Phase 2 readiness and close out Phase 1.6
**Timeline:** 2 hours
**Priority:** LOW (final step)

### Stage 1.6.11: Phase 2 Readiness Certification

**Duration:** 2 hours
**Dependencies:** All previous stages complete
**Priority:** LOW

#### Tasks:

**TSK-1.6.11.1: Final Readiness Checklist (1 hour)**
- Verify: All 111 features implemented and validated
- Verify: All storage tables created (10 types × 28 pairs)
- Verify: All worker scripts tested and documented
- Verify: Feature catalog complete
- Verify: ML integration guide published
- Verify: Query performance acceptable
- Verify: Zero blocking dependencies for Phase 2

**TSK-1.6.11.2: Update Airtable and Publish Reports (1 hour)**
- Mark Phase 1.6 as COMPLETE in Airtable
- Update all stage statuses (11 stages)
- Add completion timestamps
- Publish gap remediation completion report
- Document lessons learned

**Success Criteria:**
- ✅ Phase 2 readiness certified
- ✅ Airtable plan updated
- ✅ All 111 features validated and documented
- ✅ Gap remediation completion report published

---

## RESOURCE ALLOCATION & SEQUENCING

### Critical Path Analysis

**SERIAL (must complete before next):**
1. Current workers finish (6 hours) → Cannot start correlation until complete
2. Correlation worker dev (4 hours) → Cannot backfill until developed
3. Correlation backfill (6 hours) → Track 1 blocks Track 2 conceptually

**PARALLEL (can run concurrently):**
1. Technical Indicators (24h) + Fibonacci (9.5h) = 24h wall time
2. Validation (4h) can start as features complete
3. Documentation (4h) can start as features complete

### Timeline Optimization

**Without Parallelization:**
- Track 1: 16h + Track 2: 24h + Fibonacci: 9.5h + Validation: 4h + Docs: 4h = **57.5 hours**

**With Parallelization:**
- Track 1: 16h
- Track 2 + Fibonacci (parallel): 24h (limited by slower track)
- Validation + Docs (overlap with backfills): 4h
- Final certification: 2h
- **TOTAL: ~30 hours wall time (48% time savings)**

### CPU Utilization Plan

**Phase 1 (Track 1):**
- Statistics & Bollinger: 90% CPU (running)
- Time & Spread: 90% CPU (running)
- Total: Can't add more workers until complete

**Phase 2-3 (Parallel Tracks):**
- Technical Indicators: 90% CPU (8 threads)
- Fibonacci: Can run on separate instance OR stagger start by 12 hours
- Recommended: Stagger to avoid resource contention

**Phase 4-5 (Validation):**
- Validation suite: 20-30% CPU (sampling)
- Documentation: Minimal CPU

---

## RISK MITIGATION

### High-Risk Items

**RISK 1: Correlation Worker Complexity**
- **Mitigation:** Start development NOW (parallel with current workers)
- **Fallback:** If correlation is too complex, defer 15 features to Phase 2.1

**RISK 2: TA-Lib Memory Usage**
- **Mitigation:** Monitor memory during backfill, reduce threads if needed
- **Fallback:** Process in smaller batches (quarterly instead of monthly)

**RISK 3: Worker Failures Mid-Backfill**
- **Mitigation:** Implement checkpoint/resume in next worker iteration
- **Current:** ON CONFLICT DO UPDATE makes restarts idempotent

### Medium-Risk Items

**RISK 4: Fibonacci Swing Detection Issues**
- **Mitigation:** Extensive testing on known swing points before backfill
- **Fallback:** Adjust n parameter (n=2 for more swings, n=4 for fewer)

**RISK 5: Feature Validation Failures**
- **Mitigation:** Fix any anomalies discovered during validation
- **Timeline Impact:** +2-4 hours if major issues found

---

## SUCCESS METRICS & DELIVERABLES

### Quantitative Metrics

| Metric | Start | Target | Current | Gap |
|--------|-------|--------|---------|-----|
| **Features Implemented** | 18 | 111 | 56 | 55 |
| **Feature Types Complete** | 2 | 10 | 7 | 3 |
| **Storage Tables** | 2,251 | 2,500 | 2,251 | 250 |
| **Worker Scripts** | 5 | 8 | 5 | 3 |
| **Validation Reports** | 2 | 10 | 3 | 7 |
| **Documentation** | 5 | 10 | 5 | 5 |

### Qualitative Deliverables

**Phase 1.6 Complete When:**
1. ✅ All 111 features implemented across 10 feature types
2. ✅ All 8 worker scripts tested and documented
3. ✅ Feature catalog published (111 features with formulas)
4. ✅ ML integration guide published
5. ✅ Comprehensive validation suite passing
6. ✅ Zero blocking dependencies for Phase 2

**Track 1 Complete When:**
1. ✅ 66/66 features computed and stored
2. ✅ 6/6 workers complete (including correlation)
3. ✅ ~10M rows per feature type per pair
4. ✅ Validation reports for all 6 feature types

**Track 2 Complete When:**
1. ✅ 45/45 technical indicators implemented
2. ✅ TA-Lib integration validated
3. ✅ Cross-pair comparability verified
4. ✅ Indicator effectiveness analysis published

---

## APPENDIX A: DETAILED TASK BREAKDOWN

### Correlation Features (15 Total)

**Short-Term Correlations (5):**
1. corr_related_15min_lag0 - 15-min correlation with related pairs (no lag)
2. corr_related_60min_lag0 - 60-min correlation with related pairs
3. corr_related_240min_lag0 - 4-hour correlation with related pairs
4. corr_inverse_15min_lag0 - 15-min correlation with inverse pairs (EURUSD vs USDEUR)
5. corr_inverse_60min_lag0 - 60-min correlation with inverse pairs

**Lagged Correlations (5):**
6. corr_related_60min_lag1 - 1-bar lag correlation (leading indicator)
7. corr_related_60min_lag5 - 5-bar lag correlation
8. corr_inverse_60min_lag1 - Inverse lag-1 correlation
9. corr_major_pairs_60min - Average correlation with 7 major pairs
10. corr_exotic_pairs_60min - Average correlation with exotic pairs

**Meta Features (5):**
11. corr_strength_60min - Absolute correlation strength (|r|)
12. corr_direction_change - Correlation direction change frequency
13. corr_divergence_score - Divergence from expected correlation
14. corr_cluster_id - Correlation-based pair clustering
15. corr_regime - High/medium/low correlation regime

### Technical Indicators (45 Total)

**Momentum Indicators (11):**
1. rsi_14 - Relative Strength Index (period=14)
2. stochastic_k_14 - Stochastic %K
3. stochastic_d_3 - Stochastic %D (3-period SMA of %K)
4. williams_r_14 - Williams %R
5. roc_10 - Rate of Change (10-period)
6. mfi_14 - Money Flow Index (requires volume)
7. cmo_14 - Chande Momentum Oscillator
8. ppo - Percentage Price Oscillator
9. ultimate_oscillator - Ultimate Oscillator (combines 3 timeframes)
10. tsi - True Strength Index
11. bop - Balance of Power

**Trend Indicators (13):**
12. macd - MACD line
13. macd_signal - MACD signal line
14. macd_histogram - MACD histogram
15. adx_14 - Average Directional Index (trend strength)
16. plus_di_14 - +DI (positive directional indicator)
17. minus_di_14 - -DI (negative directional indicator)
18. parabolic_sar - Parabolic SAR (stop and reverse)
19. aroon_up_25 - Aroon Up
20. aroon_down_25 - Aroon Down
21. aroon_oscillator - Aroon Oscillator
22. cci_20 - Commodity Channel Index
23. dpo_20 - Detrended Price Oscillator
24. ichimoku_conversion - Ichimoku Conversion Line

**Volatility Indicators (10):**
25. atr_14 - Average True Range
26. natr_14 - Normalized ATR
27. keltner_upper_20 - Keltner Channel Upper
28. keltner_lower_20 - Keltner Channel Lower
29. donchian_upper_20 - Donchian Channel Upper
30. donchian_lower_20 - Donchian Channel Lower
31. bollinger_bandwidth - Bollinger Bandwidth (from Track 1, verification)
32. historical_volatility_20 - Historical Volatility (20-period std dev)
33. average_range_20 - Average Range (high - low)
34. true_range - True Range (current bar)

**Partial Indicators (11):**
35. trix_15 - Triple Exponential Moving Average
36. vortex_positive_14 - Vortex Indicator Positive
37. vortex_negative_14 - Vortex Indicator Negative
38. chaikin_oscillator - Chaikin Oscillator
39. obv - On Balance Volume (cumulative)
40. adl - Accumulation/Distribution Line
41. cmf_20 - Chaikin Money Flow
42. force_index_13 - Force Index
43. elder_ray_bull - Elder Ray Bull Power
44. elder_ray_bear - Elder Ray Bear Power
45. mass_index_25 - Mass Index

---

## APPENDIX B: AIRTABLE INTEGRATION PLAN

### New Stages to Add

1. **Stage 1.6.6:** Correlation Features Implementation
2. **Stage 1.6.7:** Technical Indicators Implementation (Track 2)
3. **Stage 1.6.8:** Fibonacci Features Implementation
4. **Stage 1.6.9:** Comprehensive Feature Validation
5. **Stage 1.6.10:** Documentation Completion
6. **Stage 1.6.11:** Phase 2 Readiness Certification

### Task Count Summary

- Stage 1.6.6: 4 tasks (correlation)
- Stage 1.6.7: 6 tasks (technical indicators)
- Stage 1.6.8: 5 tasks (fibonacci)
- Stage 1.6.9: 3 tasks (validation)
- Stage 1.6.10: 2 tasks (documentation)
- Stage 1.6.11: 2 tasks (certification)

**Total New Tasks:** 22 tasks across 6 stages

---

## CONCLUSION

This comprehensive gap remediation plan addresses all identified gaps:
- **55 missing features** → Implemented in 3 parallel tracks
- **3 missing workers** → Developed with proper specifications
- **250 missing tables** → Created with consistent schema
- **Validation gaps** → Automated suite with comprehensive checks
- **Documentation gaps** → Feature catalog + ML integration guide

**Timeline:** 30 hours with parallel execution (vs 57.5 hours sequential)
**Risk Level:** Medium (manageable with mitigation strategies)
**Resource Efficiency:** 90% CPU utilization, minimal idle time

**Recommendation:** Proceed immediately with Phase 1 (correlation worker development) while current workers finish. Track 2 and 3 can execute in parallel, maximizing throughput and minimizing time to Phase 2 readiness.

---

**Document Version:** 1.0
**Last Updated:** 2025-11-11
**Author:** BQX ML Team (Claude Code)
**Status:** Ready for Execution
