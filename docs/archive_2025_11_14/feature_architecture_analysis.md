# BQX ML Feature Architecture Analysis
## Target Variable & Feature Alignment

**Date:** 2025-11-12
**Status:** Architectural Clarification Complete
**Decision:** Hybrid Approach - Rate-based + BQX-centric Features

---

## Executive Summary

After confirming that the target variable is **future BQX values** (momentum), we analyzed whether all features should be recalculated using BQX values instead of rate values.

**Decision:** Implement a **hybrid architecture** where:
- Rate dynamics features (REG, Technical, Statistics, Volume, Time, Spread) predict the underlying price movements that drive BQX changes
- BQX-centric features (Correlation) capture momentum relationships directly

This approach provides richer predictive power than pure BQX-only features.

---

## Target Variable Confirmation

### What is BQX?
**BQX (Backward Exchange)** = Cumulative momentum metric calculated as:
```
BQX_w15 = Σ(rate_index[t-15:t-1] - rate_index[t]) / rate_index[t]
```

- **Temporal Direction:** Backward-looking (past 15/30/45/60/75 minutes)
- **Purpose:** Feature, not target
- **Target:** Future BQX values at horizons T+15, T+30, T+45, T+60, T+75

### ML Target
Predicting **future BQX momentum** at multiple horizons:
- `target_bqx_15 = BQX[T+15]`
- `target_bqx_30 = BQX[T+30]`
- etc.

---

## Feature Architecture Decision Matrix

| Feature Type | Phase | Current Source | Should Be BQX? | Final Decision | Reasoning |
|-------------|-------|----------------|----------------|----------------|-----------|
| **REG (Regression)** | 1.5 | rate_index | ❌ NO | ✅ **KEEP rate-based** | Quadratic regression on rate_index captures price trajectory that drives BQX |
| **BQX (Backward)** | 1.5 | rate_index | N/A | ✅ **Keep as-is** | These ARE the features (past momentum) |
| **Volume** | 1.6.1 | volume | ❌ NO | ✅ **KEEP rate-based** | Volume measures trading activity on rate movements |
| **Time** | 1.6.2 | timestamp | ❌ NO | ✅ **KEEP as-is** | Time-of-day patterns are independent of rate/BQX |
| **Spread** | 1.6.2 | bid-ask | ❌ NO | ✅ **KEEP rate-based** | Spread is a rate market microstructure concept |
| **OHLC Index** | 1.6.3 | rate_index | ❌ NO | ✅ **KEEP rate-based** | Foundation metric; BQX derives from this |
| **Statistics** | 1.6.4 | rate | ⚠️ MAYBE | ✅ **KEEP rate-based** | Rate volatility/skewness informs BQX changes |
| **Bollinger** | 1.6.4 | rate | ⚠️ MAYBE | ✅ **KEEP rate-based** | Rate volatility bands predict BQX regime changes |
| **Momentum Indicators** | 1.6.5 | rate | ⚠️ MAYBE | ✅ **KEEP rate-based** | RSI/Williams %R on rates predict BQX direction |
| **Trend Indicators** | 1.6.5 | rate | ⚠️ MAYBE | ✅ **KEEP rate-based** | MACD/ADX on rates forecast BQX trends |
| **Correlation** | 1.6.6 | rate → BQX | ✅ YES | ✅ **REBUILD BQX-centric** | Cross-pair BQX relationships critical |
| **Technical (ATR, CCI)** | 1.6.7 | rate | ⚠️ MAYBE | ✅ **KEEP rate-based** | Rate volatility/channel predicts BQX volatility |
| **Fibonacci** | 1.6.8 | rate | ⚠️ MAYBE | ✅ **KEEP rate-based** | Rate retracements predict BQX reversals |

---

## Rationale: Why Hybrid Architecture?

### 1. **Causal Relationship**
```
Rate Dynamics → Rate Changes → BQX Changes → Future BQX
      ↑                ↑             ↑
   REG Features   Technical/Stats  Current BQX
```

- **Rate features** capture the **cause** (price movements, volatility, trends)
- **BQX features** capture the **effect** (momentum accumulation)
- Predicting future BQX requires understanding BOTH the underlying rate dynamics AND current momentum state

### 2. **Information Content**
- **Rate-based features:** High-frequency price action, volatility regimes, order flow
- **BQX-based features:** Medium-frequency momentum relationships, cross-pair co-movement
- **Complementary, not redundant**

### 3. **Empirical ML Best Practices**
When predicting a derived metric (BQX), include features from:
- ✅ The source data (rates)
- ✅ The derived metric itself (past BQX)
- ✅ Relationships between instances (cross-pair correlations)

Example: Predicting stock returns
- Use price-based features (rate equivalent)
- Use past returns (BQX equivalent)
- Use cross-stock correlations (correlation features)

### 4. **Computational Efficiency**
- Rate-based features already computed and populated (336 partitions × 6 feature types)
- Rebuilding all features for BQX = 12-18 additional hours
- Marginal predictive gain likely small vs hybrid approach

---

## BQX-Centric Features: Correlation (Phase 1.6.6)

### Why Correlation MUST be BQX-centric
Cross-pair correlations capture momentum co-movement that directly predicts future BQX:
- **EUR/USD BQX ↔ GBP/USD BQX:** Does EUR momentum predict USD momentum?
- **w15 BQX ↔ w60 BQX:** Term structure of momentum (momentum curve shape)
- **BQX residuals:** Unexplained momentum = regime changes

### Implementation: correlation_features_worker_v4.py
**Status:** ✅ Running (PID 1880452)
**Progress:** 30/168 partitions (17.9%), ETA 12 minutes
**Features:** 15 multi-dimensional variance/covariance metrics

**Dimensions:**
1. **Term Structure:** w15↔w30↔w45↔w60↔w75 correlations
2. **Cross-Pair:** Same window, different pairs (base/quote currency groups)
3. **Cross-Temporal:** Lead-lag relationships (w15[T] → w60[T+15])
4. **Residual Variance:** Systematic vs idiosyncratic momentum
5. **Triangulation:** Arbitrage deviations in momentum space

---

## Implementation Status

### ✅ Completed (Rate-Based - Keep As-Is)
| Phase | Feature Type | Partitions | Status |
|-------|-------------|-----------|--------|
| 1.5 | REG (Regression) | 336 | ✅ Populated, indexed |
| 1.5 | BQX (Backward) | 336 | ✅ Populated, indexed |
| 1.6.1 | Volume | 336 | ✅ Populated |
| 1.6.2 | Time & Spread | 336 | ✅ Populated |
| 1.6.3 | OHLC Index | 336 | ✅ Populated |
| 1.6.4 | Statistics & Bollinger | 336 | ✅ Populated |
| 1.6.5 | Momentum & Trend Indicators | 336 | ✅ Populated |
| 1.6.7 | Technical (ATR, CCI, Stochastic) | 336 | ✅ Populated |
| 1.6.8 | Fibonacci | 336 | ✅ Populated |

### 🔄 In Progress (BQX-Centric)
| Phase | Feature Type | Partitions | Status |
|-------|-------------|-----------|--------|
| 1.6.6 | Correlation | 168 | 🔄 Running V4 (17.9% complete) |

---

## Monitoring

**Correlation Worker V4:**
```bash
# Monitor progress
tail -f /tmp/correlation_v4.log

# Real-time dashboard
bash /home/ubuntu/bqx-ml/scripts/monitor_correlation_worker.sh

# Check database population
psql -h trillium-bqx-cluster... -c "
SELECT COUNT(*) FROM pg_stat_user_tables
WHERE schemaname = 'bqx'
  AND relname LIKE 'correlation_features_%'
  AND n_live_tup > 0;
"
```

---

## Future Considerations (Phase 1.6.9 - Optional)

If model performance analysis shows BQX-centric features would significantly improve predictions:

### Rebuild Candidates
1. **Technical Indicators on BQX**
   - RSI of BQX = momentum strength of momentum (second derivative)
   - MACD of BQX = trend direction in momentum space
   - Bollinger on BQX = momentum volatility bands

2. **Statistics on BQX**
   - Mean/std dev of BQX momentum
   - Skewness/kurtosis of momentum distribution
   - Rolling statistics on momentum changes

3. **Fibonacci on BQX**
   - Retracement levels in momentum space
   - Support/resistance in BQX values

### Decision Criteria
Rebuild if:
- Model R² < 0.7 with current features
- Residual analysis shows systematic BQX patterns not captured
- Cross-validation shows significant lift from BQX-based technical indicators

**Estimated Effort:** 12-18 hours (336 partitions × 3 feature types)

---

## Conclusion

**Adopted Architecture:** Hybrid Rate + BQX Features
- ✅ Rate-based features (REG, Technical, Statistics, Volume, etc.) capture price dynamics
- ✅ BQX-centric Correlation features capture momentum relationships
- ✅ Provides complementary information for predicting future BQX momentum

**Next Step:** Complete correlation_features_worker_v4 and proceed to model training (Phase 3).

---

## References
- [backward_worker_index.py](../scripts/backfill/backward_worker_index.py) - BQX calculation methodology
- [regression_worker_index.py](../scripts/backfill/regression_worker_index.py) - REG features (rate-based)
- [correlation_features_worker_v4.py](../scripts/ml/correlation_features_worker_v4.py) - BQX-centric correlations
- [monitor_correlation_worker.sh](../scripts/monitor_correlation_worker.sh) - Real-time monitoring
