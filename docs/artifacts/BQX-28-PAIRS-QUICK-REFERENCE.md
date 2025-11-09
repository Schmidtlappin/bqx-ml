# BQX 28 Forex Pairs - Quick Reference

**Date**: 2025-11-08
**Source**: bqx-db repository analysis

---

## The 28 Pairs (Alphabetical)

```
1.  audcad  (AUD/CAD)    15. gbpaud  (GBP/AUD)
2.  audchf  (AUD/CHF)    16. gbpcad  (GBP/CAD)
3.  audjpy  (AUD/JPY)    17. gbpchf  (GBP/CHF)
4.  audnzd  (AUD/NZD)    18. gbpjpy  (GBP/JPY)
5.  audusd  (AUD/USD)    19. gbpnzd  (GBP/NZD)
6.  cadchf  (CAD/CHF)    20. gbpusd  (GBP/USD)
7.  cadjpy  (CAD/JPY)    21. nzdcad  (NZD/CAD)
8.  chfjpy  (CHF/JPY)    22. nzdchf  (NZD/CHF)
9.  euraud  (EUR/AUD)    23. nzdjpy  (NZD/JPY)
10. eurcad  (EUR/CAD)    24. nzdusd  (NZD/USD)
11. eurchf  (EUR/CHF)    25. usdcad  (USD/CAD)
12. eurgbp  (EUR/GBP)    26. usdchf  (USD/CHF)
13. eurjpy  (EUR/JPY)    27. usdjpy  (USD/JPY)
14. eurnzd  (EUR/NZD)    28. eurusd  (EUR/USD)
```

---

## Python List (Copy-Paste Ready)

```python
PAIRS = [
    "audcad", "audchf", "audjpy", "audnzd", "audusd",
    "cadchf", "cadjpy", "chfjpy",
    "euraud", "eurcad", "eurchf", "eurgbp", "eurjpy", "eurnzd", "eurusd",
    "gbpaud", "gbpcad", "gbpchf", "gbpjpy", "gbpnzd", "gbpusd",
    "nzdcad", "nzdchf", "nzdjpy", "nzdusd",
    "usdcad", "usdchf", "usdjpy",
]
```

---

## Currency Coverage (8 Currencies, Perfect Balance)

| Currency | Count | Pairs |
|----------|-------|-------|
| **AUD** | 7 | audcad, audchf, audjpy, audnzd, audusd, euraud, gbpaud |
| **CAD** | 7 | audcad, cadchf, cadjpy, eurcad, gbpcad, nzdcad, usdcad |
| **CHF** | 7 | audchf, cadchf, chfjpy, eurchf, gbpchf, nzdchf, usdchf |
| **EUR** | 7 | euraud, eurcad, eurchf, eurgbp, eurjpy, eurnzd, eurusd |
| **GBP** | 7 | eurgbp, gbpaud, gbpcad, gbpchf, gbpjpy, gbpnzd, gbpusd |
| **JPY** | 7 | audjpy, cadjpy, chfjpy, eurjpy, gbpjpy, nzdjpy, usdjpy |
| **NZD** | 7 | audnzd, eurnzd, gbpnzd, nzdcad, nzdchf, nzdjpy, nzdusd |
| **USD** | 7 | audusd, eurusd, gbpusd, nzdusd, usdcad, usdchf, usdjpy |

---

## Categorization

### Major Pairs (7) - Involve USD
```
audusd, eurusd, gbpusd, nzdusd, usdcad, usdchf, usdjpy
```

### EUR Crosses (6)
```
euraud, eurcad, eurchf, eurgbp, eurjpy, eurnzd
```

### GBP Crosses (5)
```
gbpaud, gbpcad, gbpchf, gbpjpy, gbpnzd
```

### JPY Crosses (4)
```
audjpy, cadjpy, chfjpy, nzdjpy
```

### Other Crosses (6)
```
audcad, audchf, audnzd, cadchf, nzdcad, nzdchf
```

---

## Top 10 by Liquidity

1. eurusd (EUR/USD)
2. usdjpy (USD/JPY)
3. gbpusd (GBP/USD)
4. audusd (AUD/USD)
5. usdcad (USD/CAD)
6. usdchf (USD/CHF)
7. nzdusd (NZD/USD)
8. eurgbp (EUR/GBP)
9. eurjpy (EUR/JPY)
10. gbpjpy (GBP/JPY)

---

## Data Volume (Per Pair)

| Metric | Value |
|--------|-------|
| M1 Rows (5+ years) | ~1.87 million |
| ML Correlation Rows | ~985 million |
| Storage (ML corr) | ~69 GB |
| Total Features (Phase 2) | ~470 |

---

## System Totals (28 Pairs)

| Metric | Value |
|--------|-------|
| Total Rows | 27.6 billion |
| Total Storage | 2.485 TB |
| Database Tables | 4,609 |
| Materialized Views | 28 |
| Parquet Files (Phase 2) | 336 files (28 pairs × 12 stages) |

---

## Database Tables (Per Pair)

- **m1_{pair}** - Minute-level OHLC data
- **reg_{pair}** - Regression features (6 windows)
- **fwd_{pair}** - Forward return features (6 windows)
- **mv_{pair}_merged** - Materialized view (aggregated)

---

## AWS Configuration

**Aurora Database**:
- Cluster: trillium-bqx-cluster
- Database: bqx
- ACU: 0.5-16 (auto-scaling)

**AWS Batch (Phase 2)**:
- Compute: 2560 vCPU
- Parallel: 28 pairs simultaneously

**SageMaker (Phase 4)**:
- Instances: 28× p4d.24xlarge (A100)
- Training: 2 hours (parallel)

**S3 Storage**:
- bqx-ml-features (Phase 2-3 output)
- bqx-ml-models (Phase 4-5 models)

---

## Files Containing PAIRS List

**Critical Files** (50+ total):
- `scripts/ml/phase2/phase2_executor.py` (line 98)
- `scripts/ml/refresh_all_28_mvs_parallel.py` (line 11)
- `scripts/ml/generate_all_pair_jsons.py` (line 24)
- `scripts/ml/correlation_calculation_worker_v2_optimized.py` (line 37)
- `scripts/analytics/create_forward_workplan.py` (line 14)
- `scripts/ml/phase5/cross_pair_attention.py` (line 57)

---

## Verification Status

✅ **100% Consistent** across 50+ files
✅ **Always alphabetical** order
✅ **No variations** in the codebase
✅ **Production verified** (all infrastructure)

---

**For detailed analysis**, see: [BQX-28-FOREX-PAIRS.md](BQX-28-FOREX-PAIRS.md)
