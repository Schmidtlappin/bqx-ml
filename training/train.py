"""
BQX ML Training Script
End-to-end training pipeline for autoregressive BQX prediction
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from data.extraction import AuroraExtractor
from data.features import FeatureEngineer
from models.baseline import BQXBaselineModel


def train_baseline(
    pair: str,
    start_date: str,
    end_date: str,
    save_model: bool = True,
    tune_hyperparams: bool = False
):
    """
    Train baseline model for a single pair

    Args:
        pair: Forex pair (e.g., 'eurusd')
        start_date: Training start date (YYYY-MM-DD)
        end_date: Training end date (YYYY-MM-DD)
        save_model: Whether to save trained model
        tune_hyperparams: Whether to tune hyperparameters
    """
    print("=" * 80)
    print(f"BQX ML Baseline Training: {pair.upper()}")
    print("=" * 80)
    print(f"Date range: {start_date} to {end_date}")
    print()

    # 1. Extract data from Aurora
    print("Step 1/4: Extracting data from Aurora...")
    extractor = AuroraExtractor()
    try:
        bqx, reg = extractor.load(pair, start_date, end_date)
        print(f"  ✓ BQX shape: {bqx.shape}")
        print(f"  ✓ REG shape: {reg.shape}")
    finally:
        extractor.disconnect()

    # 2. Engineer features
    print("\nStep 2/4: Engineering features...")
    engineer = FeatureEngineer()
    X, y = engineer.engineer_features(
        bqx,
        reg,
        target_col='w60_bqx_return',
        target_horizon=60,
        apply_causality=True
    )
    print(f"  ✓ Features: {X.shape[1]} columns, {X.shape[0]:,} samples")
    print(f"  ✓ Target: {y.shape[0]:,} samples")

    # Get feature categories
    categories = engineer.get_feature_names(X)
    print("\n  Feature breakdown:")
    for cat, cols in categories.items():
        if cols:
            print(f"    {cat}: {len(cols)} features")

    # 3. Train model
    print("\nStep 3/4: Training Random Forest model...")
    model = BQXBaselineModel()
    metrics = model.train(X, y, tune_hyperparams=tune_hyperparams)

    # 4. Feature importance
    print("\n" + "=" * 80)
    print("Top 15 Most Important Features")
    print("=" * 80)
    importance = model.get_feature_importance(top_n=15)
    for idx, row in importance.iterrows():
        print(f"  {row['importance']:6.4f}  {row['feature']}")

    # 5. Save model
    if save_model:
        print("\nStep 4/4: Saving model...")
        model_name = f"baseline_{pair}"
        model.save(save_dir="models/saved", model_name=model_name)
        print(f"  ✓ Model saved as {model_name}")

    print("\n" + "=" * 80)
    print("✓ Training Complete!")
    print("=" * 80)

    return model, metrics


def train_all_pairs(
    pairs: list,
    start_date: str,
    end_date: str,
    save_models: bool = True
):
    """
    Train baseline models for multiple pairs

    Args:
        pairs: List of forex pairs
        start_date: Training start date
        end_date: Training end date
        save_models: Whether to save trained models
    """
    print("=" * 80)
    print(f"BQX ML Baseline Training: {len(pairs)} Pairs")
    print("=" * 80)

    results = {}

    for i, pair in enumerate(pairs, 1):
        print(f"\n[{i}/{len(pairs)}] Training {pair.upper()}...")
        print("-" * 80)

        try:
            model, metrics = train_baseline(
                pair,
                start_date,
                end_date,
                save_model=save_models,
                tune_hyperparams=False
            )
            results[pair] = metrics['test']  # Store test metrics
            print(f"✓ {pair.upper()} complete")

        except Exception as e:
            print(f"✗ {pair.upper()} failed: {e}")
            results[pair] = None

    # Summary
    print("\n" + "=" * 80)
    print("Training Summary")
    print("=" * 80)

    for pair, metrics in results.items():
        if metrics:
            print(f"{pair.upper():8} - R²: {metrics['r2']:6.4f} | "
                  f"MAE: {metrics['mae']:.6f} | "
                  f"Dir Acc: {metrics['dir_acc']:5.2%}")
        else:
            print(f"{pair.upper():8} - FAILED")

    # Average metrics
    valid_results = [m for m in results.values() if m is not None]
    if valid_results:
        avg_r2 = sum(m['r2'] for m in valid_results) / len(valid_results)
        avg_mae = sum(m['mae'] for m in valid_results) / len(valid_results)
        avg_dir = sum(m['dir_acc'] for m in valid_results) / len(valid_results)

        print("\n" + "=" * 80)
        print(f"Average Performance ({len(valid_results)} pairs)")
        print("=" * 80)
        print(f"  R²:          {avg_r2:.4f}")
        print(f"  MAE:         {avg_mae:.6f}")
        print(f"  Dir Acc:     {avg_dir:.2%}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BQX ML Baseline Training")

    parser.add_argument(
        '--pair',
        type=str,
        help='Single forex pair to train (e.g., eurusd)'
    )

    parser.add_argument(
        '--pairs',
        type=str,
        nargs='+',
        help='Multiple forex pairs to train (e.g., eurusd gbpusd)'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Train all 28 preferred pairs'
    )

    parser.add_argument(
        '--start-date',
        type=str,
        default='2024-07-01',
        help='Training start date (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--end-date',
        type=str,
        default='2025-01-01',
        help='Training end date (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--tune',
        action='store_true',
        help='Enable hyperparameter tuning'
    )

    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save trained models'
    )

    args = parser.parse_args()

    # All 28 preferred pairs
    ALL_PAIRS = [
        'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
        'cadchf', 'cadjpy', 'chfjpy',
        'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
        'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
        'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
        'usdcad', 'usdchf', 'usdjpy'
    ]

    # Determine which pairs to train
    if args.all:
        pairs_to_train = ALL_PAIRS
        train_all_pairs(
            pairs_to_train,
            args.start_date,
            args.end_date,
            save_models=not args.no_save
        )

    elif args.pairs:
        pairs_to_train = args.pairs
        train_all_pairs(
            pairs_to_train,
            args.start_date,
            args.end_date,
            save_models=not args.no_save
        )

    elif args.pair:
        train_baseline(
            args.pair,
            args.start_date,
            args.end_date,
            save_model=not args.no_save,
            tune_hyperparams=args.tune
        )

    else:
        # Default: Train EURUSD as example
        print("No pair specified. Training EURUSD as example.")
        print("Use --pair, --pairs, or --all to train specific pairs.\n")

        train_baseline(
            'eurusd',
            args.start_date,
            args.end_date,
            save_model=not args.no_save,
            tune_hyperparams=args.tune
        )
