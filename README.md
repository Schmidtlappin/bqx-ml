# BQX Machine Learning

Autoregressive forex prediction using backward momentum features from Aurora RDS.

## Overview

BQX ML is a machine learning system for forex prediction that uses **backward-looking momentum features** (BQX) instead of traditional forward-looking returns. This autoregressive approach predicts future BQX values using current BQX patterns.

### Key Innovation

Traditional forex ML models predict future returns (FWD):
```
Features: [REG_t, FWD_t] → Target: FWD_{t+60}
Problem: Requires future data, not real-time deployable
```

BQX ML predicts future backward momentum:
```
Features: [BQX_t, REG_t] → Target: BQX_{t+60}
Advantage: All features observable in real-time, mathematically equivalent predictions
```

**Mathematical Equivalence**: `FWD_t ≈ BQX_{t+60}` (both measure price movement from t to t+60)

## Data Architecture

### Aurora PostgreSQL Database
- **Cluster**: `trillium-bqx-cluster` (Serverless v2)
- **Schema**: `bqx`
- **Forex Pairs**: 28 preferred pairs (EUR, USD, GBP, JPY, AUD, CAD, CHF, NZD)

### Tables

#### M1 Tables (Source Data)
- 1-minute OHLC bars
- 28 tables: `m1_eurusd`, `m1_gbpusd`, etc.
- Time range: 2024-07 through 2025-06
- Monthly partitioning

#### BQX Tables (Backward Momentum)
- Backward-looking cumulative returns
- Formula: `w{W}_bqx_return = Σ(i=1 to W)[rate(t-i) - rate(t)] / rate(t)`
- Windows: 15, 30, 45, 60, 75 minutes
- 28 tables: `bqx_eurusd`, `bqx_gbpusd`, etc.
- 40 fields per table (3 core + 30 window metrics + 7 aggregates)
- ~370,000 rows per pair (12 months of minute-level data)

#### REG Tables (Regression Features)
- Linear regression patterns
- Windows: 60, 90, 150, 240, 390, 630 minutes
- Metrics: slope, intercept, r², quadratic coefficients
- 28 tables: `reg_eurusd`, `reg_gbpusd`, etc.

## Project Structure

```
bqx-ml/
├── config/                 # Configuration files
│   ├── database.yaml       # Aurora connection settings
│   ├── features.yaml       # Feature engineering config
│   └── models.yaml         # Model hyperparameters
├── data/                   # Data pipeline
│   ├── extraction.py       # Extract from Aurora
│   ├── features.py         # Feature engineering
│   └── validation.py       # Data quality checks
├── models/                 # ML models
│   ├── baseline.py         # Baseline autoregressive model
│   ├── hierarchical.py     # Multi-horizon predictions
│   └── ensemble.py         # Ensemble strategies
├── training/               # Training pipeline
│   ├── train.py           # Main training script
│   ├── backtest.py        # Backtesting framework
│   └── evaluation.py      # Performance metrics
├── inference/              # Real-time inference
│   ├── predict.py         # Prediction service
│   └── deploy.py          # Deployment utilities
├── notebooks/              # Jupyter notebooks
│   └── exploratory/       # Exploratory analysis
├── tests/                  # Unit tests
│   ├── test_features.py
│   ├── test_models.py
│   └── test_pipeline.py
└── docs/                   # Documentation
    ├── architecture.md     # System architecture
    ├── features.md         # Feature documentation
    └── deployment.md       # Deployment guide
```

## BQX Feature Set

### Window Metrics (5 windows × 6 metrics = 30 features)

Each window (15, 30, 45, 60, 75 minutes) provides:
- `w{W}_bqx_return` - Cumulative return over window
- `w{W}_bqx_max` - Maximum rate in window
- `w{W}_bqx_min` - Minimum rate in window
- `w{W}_bqx_avg` - Average rate in window
- `w{W}_bqx_stdev` - Standard deviation in window
- `w{W}_bqx_endpoint` - Endpoint return (first to last in window)

### Aggregate Metrics (7 features)

- `agg_bqx_return` - Return over longest window (75 min)
- `agg_bqx_max` - Maximum across all windows
- `agg_bqx_min` - Minimum across all windows
- `agg_bqx_avg` - Average across all windows
- `agg_bqx_stdev` - Standard deviation across all windows
- `agg_bqx_range` - Range (max - min)
- `agg_bqx_volatility` - Normalized volatility (stdev / avg)

### Total Features

- **BQX Features**: 37 (30 window + 7 aggregate)
- **REG Features**: ~42 (6 windows × 7 metrics)
- **Lagged Features**: BQX at t-60, t-120, t-180
- **Total Input Features**: ~120+

## ML Strategy

### Autoregressive Model

**Objective**: Predict `BQX_{t+60}` using `BQX_t` and `REG_t`

**Architecture**:
1. Feature extraction from Aurora
2. Multi-horizon prediction (15, 30, 60, 90, 120 minute horizons)
3. Hierarchical model (short-term → medium-term → long-term)
4. Ensemble with uncertainty quantification

### Training

- **Training Window**: 2024-07 through 2024-12 (6 months)
- **Validation**: 2025-01 through 2025-03 (3 months)
- **Test**: 2025-04 through 2025-06 (3 months)
- **Walk-Forward Optimization**: Rolling window retraining

### Metrics

- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- Directional Accuracy (DA)
- Sharpe Ratio (trading performance)
- Maximum Drawdown

## Installation

```bash
# Clone repository
git clone https://github.com/Schmidtlappin/bqx-ml.git
cd bqx-ml

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure database connection
cp config/database.yaml.example config/database.yaml
# Edit database.yaml with Aurora credentials
```

## Quick Start

```python
from data.extraction import AuroraExtractor
from data.features import BQXFeatureEngine
from models.baseline import AutoregressiveModel

# Extract data from Aurora
extractor = AuroraExtractor(pair='eurusd', start='2024-07-01', end='2024-12-31')
bqx_data, reg_data = extractor.load()

# Engineer features
feature_engine = BQXFeatureEngine()
X, y = feature_engine.create_features(bqx_data, reg_data, horizon=60)

# Train model
model = AutoregressiveModel()
model.fit(X, y)

# Predict
X_new = feature_engine.transform(bqx_data.tail(1), reg_data.tail(1))
prediction = model.predict(X_new)
print(f"Predicted BQX_{t+60}: {prediction}")
```

## Database Connection

### Aurora Credentials

Stored in AWS Secrets Manager:
- Secret: `trillium/aurora/bqx-connection`
- Host: `trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com`
- Database: `bqx`
- User: `postgres`

### Example Query

```python
import psycopg2

conn = psycopg2.connect(
    host="trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com",
    database="bqx",
    user="postgres",
    password=get_secret("trillium/aurora/bqx-connection"),
    sslmode="require"
)

# Query BQX features
query = """
SELECT
    ts_utc,
    w15_bqx_return,
    w30_bqx_return,
    w60_bqx_return,
    w75_bqx_return,
    agg_bqx_volatility
FROM bqx.bqx_eurusd
WHERE ts_utc >= %s AND ts_utc < %s
ORDER BY ts_utc
"""

df = pd.read_sql(query, conn, params=('2024-07-01', '2024-08-01'))
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Linting
flake8 bqx_ml/

# Type checking
mypy bqx_ml/

# Formatting
black bqx_ml/
```

## Deployment

### Real-time Inference

The inference service connects to Aurora, extracts latest BQX features, and generates predictions in real-time.

```bash
# Start prediction service
python inference/predict.py --pair eurusd --horizon 60
```

## Documentation

- [Architecture](docs/architecture.md) - System design and data flow
- [Features](docs/features.md) - Complete feature documentation
- [Deployment](docs/deployment.md) - Production deployment guide
- [BQX Formulas](../Robkei-Ring/sandbox/artifacts/BQX-FORWARD-RETURN-FORMULAS.md) - Mathematical reference

## Related Projects

- **bqx-db**: Aurora database schema and backfill scripts
- **Robkei-Ring**: Infrastructure and agent framework

## Key Advantages

✅ **Real-time deployable**: All features observable at time t
✅ **Mathematically equivalent**: BQX_{t+60} ≈ FWD_t (same prediction)
✅ **Autoregressive**: Uses momentum persistence patterns
✅ **Finer granularity**: 15-75 min windows vs 60-630 min
✅ **Observable validation**: Can verify predictions in real-time

## Status

**Current Phase**: Data backfill in progress
**BQX Tables**: Populating historical data (2024-07 through 2025-06)
**Next Steps**:
1. Complete BQX backfill (~4 hours remaining)
2. Feature engineering pipeline
3. Baseline model training
4. Backtesting framework

## License

Proprietary - Schmidtlappin

## Contact

For questions or access requests, contact: noreply@schmidtlappin.com

---

**Last Updated**: 2025-11-09
**Repository**: https://github.com/Schmidtlappin/bqx-ml
