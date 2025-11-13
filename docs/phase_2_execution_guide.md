# Phase 2: Execution Guide & Dependency Map

**Date:** 2025-11-13
**Status:** Track 2 In Progress (18.2% complete)
**Purpose:** Comprehensive quick-reference guide for all 15 Phase 2 stages

---

## Executive Summary

Phase 2 consists of **15 stages** organized into two parallel numbering schemes:
- **Main Pipeline (2.X):** 12 stages - core feature engineering
- **Additional Features (Stage 2.X):** 3 stages - supplementary features

**Current Progress:**
- ✅ Completed: 5 stages (33.3%)
- 🔄 In Progress: 1 stage (6.7%) - Track 2 at 18.2%
- ⏳ Todo: 9 stages (60.0%)

**Total Feature Count Estimate:** 274 features across all stages

---

## Phase 2 Stage Overview

### Main Pipeline (Numeric 2.X)

| Stage | Name | Status | Duration | Features | Dependencies | Output |
|-------|------|--------|----------|----------|--------------|--------|
| 2.1 | Raw Feature Extraction | ✅ Done | 1 day | Parent stage | None | Launch 3 parallel tracks |
| 2.1.1 | Track 1: Bollinger BQX | ✅ Done | 9 days | 21 | 2.1 | 336 partitions |
| 2.1.2 | Track 2: Regression Features | 🔄 18.2% | 11 days | 180 | 2.1 | 336 partitions (61/336 done) |
| 2.1.3 | Track 3: Feature Extraction | ✅ Done | 18 days | 81 | 2.1 | 28 Parquet files (2.2 GB) |
| 2.2 | Lagged Feature Creation | ✅ Done | 1 day | TBD | 2.1 | Lagged features |
| 2.3 | Cross-Pair Currency Indices | ⏳ Todo | 2 days | 8 | 2.1 complete | Currency indices |
| 2.4 | Arbitrage Detection | ⏳ Todo | 2 days | 4 | None (uses M1) | Arbitrage features |
| 2.5 | Derived Features | ✅ Done | 1 day | TBD | 2.1 | Derived features |
| 2.6 | Temporal Causality Validation | ⏳ Todo | 1 day | 0 | All features | Validation report |
| 2.7 | Export to S3 Parquet | ⏳ Todo | 1 day | 0 | All features | S3 export (40-50 GB) |
| 2.8 | R²/RMSE Enhanced Features | ⏳ Todo | 1 day | TBD | 2.1.2 complete | Enhanced reg features |
| 2.9 | Regime Detection Features | ⏳ Todo | 2 days | TBD | Stage 2.2 | Regime features |

### Additional Features (Stage 2.X)

| Stage | Name | Status | Duration | Features | Dependencies | Output |
|-------|------|--------|----------|----------|--------------|--------|
| Stage 2.1 | Quick Win Features | ⏳ Todo | 13 hours | TBD | Phase 1.5.4 ✅ | Quick win features |
| Stage 2.2 | Technical Indicators | ⏳ Todo | 15 hours | TBD | Phase 1.5.4 ✅ | ADX, RSI, MACD, etc. |
| Stage 2.3 | Advanced Features | ⏳ Todo | 7 hours | TBD | Stage 2.2 | Advanced features |

---

## Dependency Visualization

```
COMPLETED PREREQUISITES
========================
Phase 1.5.4 (rate_index) ✅ DONE
    │
    ├─── M1 Source Data (Jul 2024 - Jun 2025) ✅ AVAILABLE
    └─── BQX Data (336 partitions) ✅ AVAILABLE

COMPLETED STAGES
================
2.1 (Raw Feature Extraction) ✅ DONE
    ├── 2.1.1 (Bollinger BQX) ✅ DONE → 21 features
    ├── 2.1.2 (Regression) 🔄 IN PROGRESS (18.2%) → 180 features
    └── 2.1.3 (Extraction) ✅ DONE → 81 features

2.2 (Lagged Features) ✅ DONE
2.5 (Derived Features) ✅ DONE

READY TO START (After Track 2 completes)
=========================================
Stage 2.1 (Quick Win) ⏳ CAN START NOW
Stage 2.2 (Technical Indicators) ⏳ CAN START NOW
    │
    ├── Stage 2.3 (Advanced Features) ⏳ BLOCKED (needs ADX from Stage 2.2)
    └── 2.9 (Regime Detection) ⏳ BLOCKED (needs ADX from Stage 2.2)

INDEPENDENT (can start after Track 2)
======================================
2.3 (Cross-Pair Indices) ⏳ CAN START AFTER 2.1.2
2.4 (Arbitrage Detection) ⏳ CAN START NOW (uses M1 directly)
2.8 (R²/RMSE Enhanced) ⏳ CAN START AFTER 2.1.2

FINAL STAGES (require all features)
====================================
2.6 (Temporal Causality) ⏳ WAIT FOR ALL
2.7 (Export S3) ⏳ WAIT FOR ALL
```

---

## Feature Count Progression

### Current State (After Track 2 Completion)
```
Base Features (from Phase 1):
  - rate_index: 1 feature (target variable)
  - timestamp: 1 feature
  - metadata: 2 features (pair, year_month)
  SUBTOTAL: 4 features

Phase 2 Features (completed so far):
  - Bollinger (2.1.1): 21 features
  - Regression (2.1.2): 180 features (IN PROGRESS)
  - Statistics (2.1.3): 23 features
  - Volume (2.1.3): 10 features
  - Spread (2.1.3): 20 features
  - Time (2.1.3): 8 features
  SUBTOTAL: 262 features

Remaining Phase 2 Features (to be added):
  - Lagged (2.2): TBD
  - Currency Indices (2.3): 8 features
  - Arbitrage (2.4): 4 features
  - Derived (2.5): TBD
  - Quick Win (Stage 2.1): TBD
  - Technical Indicators (Stage 2.2): TBD
  - Advanced (Stage 2.3): TBD
  - R²/RMSE Enhanced (2.8): TBD
  - Regime Detection (2.9): TBD

TOTAL ESTIMATED: 274+ features
```

---

## Execution Timeline

### Historical Progress
```
Phase 1: Jul 2024 - Nov 2024
  ├── 1.1 - 1.5.3: Database schema & M1 ingestion
  ├── 1.5.4: Rate index calculation (complete)
  └── 1.6 - 1.9: Feature population (Bollinger, Stats, Volume, etc.)

Phase 2 Start: 2025-11-13
  ├── 2.1: Launched parallel tracks
  │   ├── Track 1 (Bollinger BQX): ✅ Complete (4 hours)
  │   ├── Track 2 (Regression): 🔄 In Progress (ETA: ~4 hours remaining)
  │   └── Track 3 (Extraction): ✅ Complete (25 minutes)
  │
  ├── 2.2: ✅ Complete
  └── 2.5: ✅ Complete
```

### Projected Timeline (Post-Track 2)
```
Day 1 (Track 2 completes ~02:00 AM)
  ├── Launch Stage 2.2 (Technical Indicators) - 15 hours
  └── Launch 2.8 (R²/RMSE Enhanced) - 1 day (parallel)

Day 2
  ├── Stage 2.2 completes
  ├── Launch Stage 2.3 (Advanced Features) - 7 hours
  └── Launch 2.9 (Regime Detection) - 2 days

Day 3
  ├── Launch 2.3 (Cross-Pair Indices) - 2 days
  └── Launch 2.4 (Arbitrage Detection) - 2 days

Day 5
  ├── All features complete
  ├── Launch 2.6 (Temporal Causality) - 1 day
  └── Launch 2.7 (Export S3) - 1 day

Day 6-7
  ├── Phase 2 COMPLETE 🎉
  └── Ready for Phase 3 (SageMaker Training)
```

**Total Estimated Duration:** 6-7 days from Track 2 completion

---

## Storage Impact Summary

| Stage | Storage Impact | Cumulative |
|-------|---------------|------------|
| Phase 1 Baseline | ~50 GB | 50 GB |
| 2.1.1 (Bollinger BQX) | Included in baseline | 50 GB |
| 2.1.2 (Regression) | Included in baseline | 50 GB |
| 2.1.3 (Extraction) | +2.2 GB (Parquet) | 52.2 GB |
| Stage 2.1 (Quick Win) | +8 GB | 60.2 GB |
| Stage 2.2 (Technical Indicators) | +10 GB | 70.2 GB |
| Stage 2.3 (Advanced Features) | +3 GB | 73.2 GB |
| 2.3 (Cross-Pair Indices) | +2 GB | 75.2 GB |
| 2.4 (Arbitrage Detection) | +1 GB | 76.2 GB |
| 2.8 (R²/RMSE Enhanced) | +0.5 GB | 76.7 GB |
| 2.9 (Regime Detection) | +2 GB | 78.7 GB |
| 2.7 (S3 Export) | +40-50 GB (Parquet) | 128.7 GB |

**Aurora Cluster Capacity:** 100+ GB available ✅ Sufficient

---

## Critical Paths

### Path 1: Technical Indicators → Advanced Features
```
Track 2 (2.1.2) → Stage 2.2 → Stage 2.3
BOTTLENECK: Stage 2.2 (15 hours, CPU-intensive)
```

### Path 2: Regression → Cross-Pair Indices
```
Track 2 (2.1.2) → 2.3 (Cross-Pair Indices)
BOTTLENECK: Track 2 (ETA: 4 hours remaining)
```

### Path 3: Technical Indicators → Regime Detection
```
Track 2 (2.1.2) → Stage 2.2 → 2.9 (Regime Detection)
BOTTLENECK: Stage 2.2 (15 hours)
```

**Critical Path Duration:** Track 2 (4h) + Stage 2.2 (15h) + 2.9 (2d) = ~3 days

---

## Resource Requirements

### CPU Utilization
```
Current (Track 2 running):
  - CPU Load: 8.92 / 8.0 cores (101% - SATURATED)
  - 8 workers at 90-95% CPU each
  - CANNOT run additional work until Track 2 completes

After Track 2:
  - Stage 2.2 (Technical Indicators): 8 cores recommended
  - 2.3 (Cross-Pair Indices): 2-4 cores (can run in parallel)
  - 2.4 (Arbitrage Detection): 2 cores (lightweight)
```

### Memory
```
Current: 5.7 GiB / 30 GiB (19% - PLENTY OF HEADROOM)
Expected Peak: ~15 GiB (during Stage 2.2 + 2.3 parallel)
```

### Aurora Database
```
Current Connections: 21 / 2000 (1.05% - ABUNDANT CAPACITY)
Expected Peak: ~50 connections (during parallel execution)
```

---

## Preparation Artifacts (Lightweight Tasks)

### ✅ Task 1: Cross-Pair Data Preparation
**Status:** COMPLETE
**Deliverables:**
- [currency_mappings.json](../data/prep/currency_mappings.json) - Currency groupings for 8 currencies
- [pair_relationship_matrix.json](../data/prep/pair_relationship_matrix.json) - 28×28 relationship matrix
- 784 relationships analyzed (112 base_base, 112 quote_quote, 420 independent, etc.)

### ✅ Task 2: Arbitrage Triplet Preparation
**Status:** COMPLETE
**Deliverables:**
- [arbitrage_triplets.json](../data/prep/arbitrage_triplets.json) - 56 valid triangular arbitrage triplets
- 21 triplets per currency (8 currencies × 21 = 168 total triplet memberships)
- Arbitrage detection algorithm documented

### ✅ Task 3: Temporal Causality Test Preparation
**Status:** COMPLETE
**Deliverables:**
- [temporal_causality_tests.py](../tests/temporal_causality_tests.py) - Full test suite
- [temporal_validation_config.json](../tests/temporal_validation_config.json) - 80/10/10 split config
- [leak_detection_samples.json](../tests/leak_detection_samples.json) - 1000 random timestamps

### ✅ Task 4: S3 Export Schema Preparation
**Status:** COMPLETE
**Deliverables:**
- [s3_export_config.json](../scripts/export/s3_export_config.json) - Complete S3 export configuration
- Directory structure for s3://bqx-ml-features/
- Parquet partitioning strategy (by pair + year_month)
- StandardScaler configuration for normalization

### ✅ Task 5: Documentation & Dependency Audit
**Status:** COMPLETE
**Deliverables:**
- [This document](phase_2_execution_guide.md) - Comprehensive execution guide

---

## Quick Reference Commands

### Monitor Track 2 Progress
```bash
# Real-time completion count
watch -n 10 'grep -c "Complete!" /tmp/logs/track2/populate.log'

# Detailed progress (last 20 completions)
tail -100 /tmp/logs/track2/populate.log | grep "Complete!" | tail -20

# Check for failures
grep -c "Failed" /tmp/logs/track2/populate.log

# System resource monitoring
watch -n 5 'uptime && free -h | grep Mem && echo && ps aux | grep populate_regression | grep -v grep | wc -l'
```

### Check Feature Completeness
```bash
# Bollinger BQX partitions
PGPASSWORD='BQX_Aurora_2025_Secure' psql \
  -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres -d bqx \
  -c "SELECT COUNT(*) FROM pg_tables WHERE schemaname='bqx' AND tablename LIKE 'bollinger_bqx_%';"

# Regression partitions
PGPASSWORD='BQX_Aurora_2025_Secure' psql \
  -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres -d bqx \
  -c "SELECT COUNT(*) FROM pg_tables WHERE schemaname='bqx' AND tablename LIKE 'reg_%';"

# Parquet files
ls -lh /home/ubuntu/bqx-ml/data/extracted/*.parquet | wc -l
```

### Launch Next Stages (After Track 2)
```bash
# Stage 2.2 (Technical Indicators) - placeholder
# python3 /home/ubuntu/bqx-ml/scripts/ml/populate_technical_indicators.py

# 2.3 (Cross-Pair Indices) - placeholder
# python3 /home/ubuntu/bqx-ml/scripts/ml/populate_currency_indices.py

# 2.4 (Arbitrage Detection) - placeholder
# python3 /home/ubuntu/bqx-ml/scripts/ml/populate_arbitrage_features.py
```

---

## Next Actions

### IMMEDIATE (While Track 2 runs)
- ✅ All 5 lightweight tasks completed
- ✅ Preparation artifacts ready
- ⏳ Monitor Track 2 completion (ETA: ~4 hours)

### AFTER Track 2 Completes
1. **Launch parallel execution:**
   - Stage 2.2 (Technical Indicators) - 8 cores
   - 2.8 (R²/RMSE Enhanced) - 2 cores
   - 2.4 (Arbitrage Detection) - 2 cores (if capacity)

2. **Sequential execution after Stage 2.2:**
   - Stage 2.3 (Advanced Features) - 7 hours
   - 2.9 (Regime Detection) - 2 days

3. **Final stages:**
   - 2.6 (Temporal Causality Validation) - 1 day
   - 2.7 (Export to S3 Parquet) - 1 day

---

**Last Updated:** 2025-11-13 22:00:00
**Track 2 Progress:** 61/336 partitions (18.2%)
**Next Milestone:** Track 2 completion (~02:00 AM Nov 14)
**Phase 2 Estimated Completion:** Nov 19-20, 2025
