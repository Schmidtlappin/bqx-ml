# BQX Repository Analysis and Comparison

**Date**: 2025-11-08
**Source**: Trillium AWS Secrets Manager + GitHub (Schmidtlappin)
**Analysis**: Repository Structure, Content, and Architecture

---

## Executive Summary

**Key Finding**: There is only **ONE GitHub repository** for BQX FOREX ML system.

- **Repository**: `Schmidtlappin/bqx-db` (private)
- **bqx-ml**: NOT a separate repository, but a deployment directory name on BQX-Master

The confusion arises from the dual deployment model:
- **Development**: Robkei-Control → `/home/ubuntu/workspace/bqx-db/`
- **Production**: BQX-Master → `/home/ubuntu/bqx-ml/` (clone of same repo)

---

## Architecture: Development vs Production Separation

### Single Repository, Two Deployment Locations

```
GitHub: Schmidtlappin/bqx-db (private repository)
            │
            ├─── Clone to: /home/ubuntu/workspace/bqx-db/ (Robkei-Control)
            │    Purpose: Development, code editing, git operations
            │    Instance: i-0e0ae4a81437a9bca (m7i.2xlarge)
            │    IP: 35.175.128.172
            │
            └─── Clone to: /home/ubuntu/bqx-ml/ (BQX-Master)
                 Purpose: Production ML execution
                 Instance: i-08570d6a274740283 (m7i.4xlarge)
                 IP: 34.226.198.212
```

### Why Two Deployment Locations?

**Robkei-Control (Development)**:
- Universal development workstation for ALL projects
- VS Code Remote-SSH, GUI, RDP access
- Git operations (commit, push, pull)
- Local testing & debugging
- IAM Group: Robkei (AdministratorAccess)

**BQX-Master (Production)**:
- BQX ML production execution only
- PostgreSQL 18.0 database (28.6B rows, 2.3TB)
- Pure database server (no code editing)
- IAM Group: BQX (project-specific access)

---

## Repository Content Analysis: bqx-db

### Repository Statistics

| Metric | Value |
|--------|-------|
| **Total Python Files** | 150+ files |
| **Total Lines of Code** | 57,835 lines |
| **Primary Language** | Python 3.10+ |
| **Database** | PostgreSQL 18 / Aurora Serverless v2 |
| **ML Framework** | PyTorch 2.9.0, DuckDB 1.4.1 |
| **Data Source** | Oanda API (M1 forex data) |
| **Currency Pairs** | 28 pairs |
| **Data Volume** | 28.6 billion rows, 2.3TB |

### Repository Structure

```
bqx-db/
├── README.md                           # Main documentation
├── requirements.txt                    # Python dependencies
├── pyproject.toml                      # Project configuration
│
├── bqx/                               # Core configuration
│   ├── ontology.jsonld                # System ontology (v5.1.0)
│   ├── semantics.json                 # System semantics (v5.1.0)
│   ├── CHANGELOG.md                   # Version history
│   └── README.md                      # BQX documentation
│
├── src/                               # Source code
│   ├── database/                      # Database utilities
│   ├── datafeed/                      # Oanda API data feed
│   │   ├── ideal_fx_feed.py          # Primary forex data collection
│   │   └── monitor_feed.py           # Feed monitoring
│   ├── workplan/                      # Task management
│   │   ├── manager.py                # Workplan orchestration
│   │   ├── worker.py                 # Worker execution
│   │   └── task_router.py            # Task routing
│   ├── agents/                        # Agent orchestration
│   │   └── master_orchestrator.py    # Master coordination
│   └── utils/                         # Utilities
│       └── file_manager.py           # File operations
│
├── scripts/                           # Execution scripts
│   ├── ml/                           # ML pipeline scripts
│   │   ├── phase2/                   # Feature engineering
│   │   ├── phase3/                   # Feature merging
│   │   ├── phase4/                   # TFT model training
│   │   └── phase5/                   # Ensemble models
│   ├── analytics/                    # Analytics scripts
│   │   ├── regression_worker.py      # Regression analysis
│   │   ├── forward_worker.py         # Forward returns
│   │   └── create_*_workplan.py      # Workplan generators
│   ├── deployment/                   # AWS deployment
│   └── utils/                        # Utility scripts
│       └── bqx_aurora_utils.py       # Aurora connection library
│
├── docs/                             # Documentation (extensive)
│   ├── phase_docs/                   # Phase-specific docs
│   │   ├── MASTER_PLAN_DL_EXACT_PREDICTION.md
│   │   ├── PHASE1_TO_PRODUCTION_ROADMAP.md
│   │   ├── PHASE2_READY_TO_EXECUTE.md
│   │   └── PHASE3_PYTORCH_READY.md
│   ├── ml_infrastructure/            # Infrastructure docs
│   │   └── AWS_GPU_RECOMMENDATIONS_PHASE4_5.md
│   └── [50+ additional docs]
│
├── tools/                            # Automation tools
│   ├── ai_agent_orchestrator.py      # AI agent coordination
│   ├── aurora_acu_manager.py         # Aurora scaling
│   ├── get_secret.py                 # Secrets Manager access
│   ├── sync_documentation.py         # Doc synchronization
│   └── validate_data_layer.py        # Data validation
│
├── tests/                            # Test suite
│   ├── test_workplan_system.py       # Workplan tests
│   └── __init__.py
│
├── config/                           # Configuration files
├── iam/                              # IAM policies
├── tmp/                              # Temporary files
│
└── [AWS Integration Files]
    ├── buildspec-phase2.yml          # CodeBuild Phase 2
    ├── buildspec-phase4.yml          # CodeBuild Phase 4
    ├── buildspec-phase5-*.yml        # CodeBuild Phase 5 variants
    └── Dockerfile.phase2             # Docker configurations
```

---

## Key Components and Features

### 1. Data Pipeline (Oanda API → PostgreSQL/Aurora)

**Primary Scripts**:
- `src/datafeed/datafeed/ideal_fx_feed.py` - M1 candlestick data collection
- `scripts/ml/backfill_m1_gaps_oanda.py` - Historical data backfill

**Coverage**:
- 28 currency pairs (EUR/USD, GBP/USD, USD/JPY, etc.)
- M1 granularity (1-minute OHLC)
- 5+ years historical data
- 28.6 billion rows total

### 2. ML Feature Engineering (Phase 2)

**Core Features**:
- **Momentum**: RSI, MACD, Stochastic
- **VWAP**: Volume-weighted average price
- **Regression**: Linear regression slopes
- **Forward Analysis**: Future return calculations
- **Cross-Currency Correlations**: 4-category triangulation

**Scripts**:
- `scripts/ml/phase2/phase2_executor.py` - Main feature engineering
- `scripts/ml/correlation_calculation_worker_v2_optimized.py` - Correlation calculation
- `scripts/ml/triangulation_correlation.py` - 807 lines of correlation logic

**Output**:
- 1,937 GB feature dataset (oxo.ml_corr_triangulation table)
- Parquet files exported to S3: `s3://bqx-ml-features/`

### 3. ML Training Pipeline (Phase 3-5)

**Phase 3**: Feature merging with DuckDB + Lambda
**Phase 4**: TFT (Temporal Fusion Transformer) training on SageMaker
**Phase 5**: Ensemble models (CrossPair, MoE, NBEATS, MetaLearner)

**Infrastructure**:
- AWS Batch (Phase 2 - 2560 vCPU)
- AWS Lambda (Phase 3 - DuckDB merging)
- SageMaker (Phase 4-5 - 32 A100 GPUs)

### 4. Database Management

**PostgreSQL 18.0** (BQX-Master local):
- 28.6 billion rows
- 2.3 TB data
- 6TB EBS storage @ 39% utilization

**Aurora Serverless v2** (Production):
- Migration 24.74% complete (as of Oct 24)
- Auto-scaling 0.5-16 ACU
- Connection pooling via `bqx_aurora_utils.py`

**Key Tables**:
- `m1_*` tables (28 currency pairs, OHLC data)
- `oxo.ml_corr_triangulation` (1,937 GB, feature dataset)
- `regression_*` tables (forward returns, regression slopes)

### 5. Workplan Management System

**Purpose**: Parallel task execution and tracking

**Components**:
- `src/workplan/manager.py` - Workplan orchestration
- `src/workplan/worker.py` - Worker execution
- `src/workplan/task_router.py` - Task distribution

**Use Cases**:
- Phase 2 parallel feature engineering (17-28 pairs)
- Correlation calculation (3,376 jobs)
- Data backfill (gap detection and filling)

### 6. AWS Integration & CI/CD

**AWS CodeBuild**:
- Triggered by git push to main branch
- Builds Docker images for Phase 2, 4, 5
- Pushes to Amazon ECR

**AWS Services Used**:
- ECR (Docker registry)
- Batch (Phase 2 execution)
- SageMaker (Phase 4-5 training)
- Lambda (Phase 3 merging)
- S3 (bqx-ml-features, bqx-ml-models, bqx-ml-code)
- Step Functions (pipeline orchestration)

---

## Documentation Highlights

The repository contains **extensive documentation** (50+ files):

### Critical Documents

1. **BQX_ARCHITECTURE_DEV_PROD_SEPARATION.md** (491 lines)
   - Comprehensive architecture guide
   - Robkei-Control vs BQX-Master separation
   - IAM group structure (Robkei vs BQX)
   - Workflow and security protocols

2. **MASTER_PLAN_DL_EXACT_PREDICTION.md**
   - 5-phase deep learning roadmap
   - Exact target prediction methodology

3. **BQX_COMPLETE_MASTERPLAN_v4.0_AURORA.md** (34,833 lines)
   - Complete system architecture
   - Aurora migration strategy
   - Cost optimization

4. **BQX_EXPEDITED_ML_DEPLOYMENT.md** (16,290 lines)
   - 39.5-hour deployment timeline
   - Phase 2-5 execution plan

5. **BQX_3TIER_STORAGE_STRATEGY.md** (17,588 lines)
   - io2 (hot) / gp3 (warm) / S3 (cold)
   - $297/month cost savings

6. **SESSION_CONTEXT_CURRENT.md** (292 lines)
   - Live project status
   - Migration progress tracking
   - Next steps and blockers

---

## S3 Bucket References

The repository integrates with these S3 buckets:

1. **bqx-ml-features** - Phase 2-3 feature storage
2. **bqx-ml-models** - Phase 4-5 model artifacts
3. **bqx-ml-code** - Training scripts and configs

---

## GitHub Access Details

**Repository**: `Schmidtlappin/bqx-db` (private)
**Access Token**: Stored in AWS Secrets Manager
**Secret ID**: `bqx-mirror/bqx/github/robkei-control-github-access`
**Token Value**: `ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`

**Clone Command**:
```bash
# Development (Robkei-Control)
git clone https://${TOKEN}@github.com/Schmidtlappin/bqx-db.git /home/ubuntu/workspace/bqx-db/

# Production (BQX-Master)
git clone https://${TOKEN}@github.com/Schmidtlappin/bqx-db.git /home/ubuntu/bqx-ml/
```

---

## Cost & Performance Metrics

### Infrastructure Costs (Monthly)

| Component | Cost |
|-----------|------|
| BQX-Master EC2 (m7i.4xlarge) | $1,375 |
| Robkei-Control EC2 (m7i.2xlarge) | $174 |
| Aurora Serverless v2 | $572-622 |
| Storage (3-tier optimized) | $233 |
| ML Training (avg) | $462 |
| **Total** | **$2,816-2,866** |

### Performance Metrics

| Metric | Value |
|--------|-------|
| Migration Rate | 118,000 rows/second |
| GP3 Throughput | 300-400 MB/s |
| Aurora ACU (migration) | 64 (fixed) |
| Aurora ACU (production) | 0.5-16 (auto-scale) |
| Phase 2 Execution | 3 hours (17 pairs parallel) |
| Phase 3 Execution | 5 minutes (Lambda) |
| Phase 4 Execution | 2 hours (28 pairs on GPU) |
| Phase 5 Execution | 4 hours (112 jobs on GPU) |
| **Total ML Pipeline** | **9 hours** |

---

## Conclusion

**bqx-db** is a comprehensive, production-grade forex ML system with:

✅ **Single GitHub repository** (bqx-db) deployed to two locations
✅ **Robust architecture** (dev/prod separation, clear IAM boundaries)
✅ **Extensive codebase** (57,835 lines Python, 150+ files)
✅ **Production-scale data** (28.6B rows, 2.3TB, 28 currency pairs)
✅ **Complete ML pipeline** (5 phases, automated CI/CD)
✅ **Comprehensive documentation** (50+ docs, >100K lines)
✅ **AWS-native integration** (Batch, SageMaker, Lambda, ECR, S3)
✅ **Cost-optimized** ($297/month saved via 3-tier storage)

**No separate "bqx-ml" repository exists** - it's the same codebase deployed to a production directory on BQX-Master.

---

**Analysis Date**: 2025-11-08
**Repository Version**: v5.1.0 (Ontology & Semantics)
**Aurora Migration**: 24.74% complete (as of last update)
**Status**: Production-ready, actively maintained
