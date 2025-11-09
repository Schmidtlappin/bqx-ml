# BQX ML Quick Start Guide

Get started with BQX ML autoregressive prediction in minutes.

## Prerequisites

- Aurora PostgreSQL cluster running with BQX and REG data populated
- Python 3.8+
- Required packages: pandas, numpy, psycopg2, scikit-learn, pyyaml, joblib

## Installation

```bash
# Clone repository
cd bqx-ml

# Install dependencies
pip install -r requirements.txt

# Configure database connection
cp config/database.yaml.example config/database.yaml
# Edit config/database.yaml with your Aurora credentials
```

## Quick Training Example

### 1. Train Single Pair (EURUSD)

```bash
cd training
python train.py --pair eurusd --start-date 2024-07-01 --end-date 2024-12-31
```

**Output**:
- Trains Random Forest baseline model on EURUSD
- Shows train/val/test metrics (MAE, RMSE, R², Directional Accuracy)
- Displays top 15 most important features
- Saves model to `models/saved/baseline_eurusd_*.joblib`

### 2. Train Multiple Pairs

```bash
python train.py --pairs eurusd gbpusd usdjpy --start-date 2024-07-01 --end-date 2024-12-31
```

### 3. Train All 28 Pairs

```bash
python train.py --all --start-date 2024-07-01 --end-date 2024-12-31
```

**Note**: Training all pairs takes ~1-2 hours depending on data volume and hardware.

## Understanding the Output

```
Step 1/4: Extracting data from Aurora...
  ✓ BQX shape: (370000, 37)  # 37 BQX features
  ✓ REG shape: (370000, 42)  # 42 REG features

Step 2/4: Engineering features...
  ✓ Features: 120+ columns, 350,000+ samples
  ✓ Target: 350,000+ samples

  Feature breakdown:
    bqx_raw: 37 features          # Original BQX features
    bqx_lagged: 148 features      # Lagged BQX (t-60, t-120, t-180)
    reg_raw: 42 features          # Original REG features
    derived: 3 features           # momentum_alignment, volatility_regime, trend_strength
    causality_lagged: 15 features # 61-min lag for temporal causality

Step 3/4: Training Random Forest model...

Data split:
  Train: 245,000 samples (70%)
  Val:   52,500 samples (15%)
  Test:  52,500 samples (15%)

Training Random Forest...

Model Performance Metrics
============================================================

TRAIN:
  MAE:         0.000234
  RMSE:        0.000512
  R²:          0.8543
  Dir Acc:     68.42%

VAL:
  MAE:         0.000267
  RMSE:        0.000589
  R²:          0.8421
  Dir Acc:     66.35%

TEST:
  MAE:         0.000271
  RMSE:        0.000601
  R²:          0.8398
  Dir Acc:     65.87%

Top 15 Most Important Features
============================================================
  0.0823  w60_bqx_return_lag60
  0.0654  w60_bqx_return
  0.0432  momentum_alignment
  0.0398  w45_bqx_return_lag60
  0.0365  agg_bqx_return_lag60
  ...
```

## Key Metrics Explained

### Regression Metrics

- **MAE** (Mean Absolute Error): Average prediction error in BQX units
  - Lower is better
  - Typical range: 0.0002 - 0.0005 for good models

- **RMSE** (Root Mean Squared Error): Standard deviation of prediction errors
  - Lower is better
  - Penalizes large errors more than MAE

- **R²** (R-squared): Proportion of variance explained by model
  - Range: 0 to 1 (higher is better)
  - **Target**: > 0.84 (baseline), > 0.88 (good), > 0.95 (excellent)

### Trading Metrics

- **Directional Accuracy**: % of times model correctly predicts direction
  - Range: 50% (random) to 100% (perfect)
  - **Target**: > 55% (profitable), > 60% (very good), > 65% (excellent)
  - Important: Even 52-55% can be profitable with proper risk management

## Feature Importance

The model shows which features are most predictive:

1. **Lagged BQX features** (e.g., `w60_bqx_return_lag60`): BQX values 60 minutes ago
2. **Current BQX features** (e.g., `w60_bqx_return`): Current BQX momentum
3. **Derived features** (e.g., `momentum_alignment`): Multi-window alignment
4. **Regression features** (e.g., `w240_slope`): Longer-term trends

## Next Steps

### Improve Model Performance

1. **Hyperparameter Tuning**
   ```bash
   python train.py --pair eurusd --tune
   ```

2. **Feature Selection**
   - Edit `config/features.yaml`
   - Adjust lag windows, derived features

3. **Advanced Models**
   - Implement Gradient Boosting (XGBoost)
   - Implement Temporal Fusion Transformer (TFT)
   - Create ensemble of multiple models

### Backtesting

```python
# Coming soon: backtesting framework
python training/backtest.py --pair eurusd --strategy baseline
```

### Real-time Prediction

```python
# Coming soon: inference service
python inference/predict.py --pair eurusd --horizon 60
```

## Troubleshooting

### Connection Error

```
ERROR: could not connect to Aurora
```

**Solution**: Check `config/database.yaml` has correct credentials and cluster endpoint.

### Not Enough Data

```
ERROR: Insufficient data for training
```

**Solution**: Ensure BQX backfill is complete for the pair and date range.

### Memory Error

```
ERROR: MemoryError
```

**Solution**:
- Reduce date range
- Use fewer features
- Train pairs sequentially instead of `--all`

## Project Structure

```
bqx-ml/
├── config/              # Configuration files
│   ├── database.yaml    # Aurora connection
│   ├── features.yaml    # Feature engineering
│   └── models.yaml      # Model hyperparameters
├── data/                # Data pipeline
│   ├── extraction.py    # Load BQX/REG from Aurora
│   └── features.py      # Feature engineering
├── models/              # ML models
│   ├── baseline.py      # Random Forest baseline
│   └── saved/           # Trained models (gitignored)
├── training/            # Training scripts
│   └── train.py         # Main training script
└── docs/                # Documentation
    ├── architecture.md  # System architecture
    └── USER-EXPECTATIONS-BQX-ML.md  # Requirements
```

## Support

For issues or questions:
1. Check documentation in `docs/`
2. Review user expectations in `docs/USER-EXPECTATIONS-BQX-ML.md`
3. Examine architecture in `docs/architecture.md`

---

**Happy Trading! 📈**
