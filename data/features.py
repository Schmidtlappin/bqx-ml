"""
BQX ML Feature Engineering
Create autoregressive features from BQX and REG data
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import yaml
from pathlib import Path


class FeatureEngineer:
    """
    Feature engineering for BQX ML autoregressive prediction

    Strategy:
    - Load BQX and REG features from Aurora
    - Create lagged features (BQX_t-60, BQX_t-120, etc.)
    - Create derived momentum features
    - Create target variable (BQX_t+60)
    - Apply 61-minute lag rule for temporal causality
    """

    def __init__(self, config_path: str = "config/features.yaml"):
        """
        Initialize feature engineer

        Args:
            config_path: Path to feature configuration file
        """
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            # Default configuration
            self.config = {
                'bqx': {
                    'windows': [15, 30, 45, 60, 75],
                    'metrics': ['bqx_return', 'bqx_max', 'bqx_min', 'bqx_avg', 'bqx_stdev', 'bqx_endpoint']
                },
                'reg': {
                    'windows': [60, 90, 150, 240, 390, 630],
                    'metrics': ['slope', 'intercept', 'r2', 'quad_a', 'quad_b', 'quad_c', 'quad_norm']
                },
                'lags': {
                    'enabled': True,
                    'windows': [60, 120, 180, 240]
                },
                'derived': {
                    'momentum_alignment': True,
                    'volatility_regime': True,
                    'trend_strength': True
                }
            }

    def create_lagged_features(
        self,
        df: pd.DataFrame,
        columns: List[str],
        lags: List[int]
    ) -> pd.DataFrame:
        """
        Create lagged features for specified columns

        Args:
            df: Input dataframe with time index
            columns: Columns to create lags for
            lags: List of lag periods in minutes (e.g., [60, 120])

        Returns:
            DataFrame with original + lagged features
        """
        result = df.copy()

        for col in columns:
            if col not in df.columns:
                continue

            for lag in lags:
                lag_col = f"{col}_lag{lag}"
                result[lag_col] = df[col].shift(lag)

        return result

    def create_momentum_alignment(self, bqx_df: pd.DataFrame) -> pd.Series:
        """
        Create momentum alignment feature

        Counts how many BQX windows are aligned (same direction)
        High alignment = strong directional momentum

        Args:
            bqx_df: DataFrame with BQX features

        Returns:
            Series with alignment scores (-5 to +5)
        """
        alignment = pd.Series(0, index=bqx_df.index)

        for window in self.config['bqx']['windows']:
            col = f"w{window}_bqx_return"
            if col in bqx_df.columns:
                # +1 if positive, -1 if negative
                alignment += np.sign(bqx_df[col])

        return alignment

    def create_volatility_regime(self, bqx_df: pd.DataFrame) -> pd.Series:
        """
        Classify volatility regime based on BQX standard deviations

        Args:
            bqx_df: DataFrame with BQX features

        Returns:
            Series with regime classification (0=low, 1=medium, 2=high)
        """
        # Use aggregate BQX volatility if available
        if 'agg_bqx_volatility' in bqx_df.columns:
            vol = bqx_df['agg_bqx_volatility']
        elif 'agg_bqx_stdev' in bqx_df.columns:
            vol = bqx_df['agg_bqx_stdev']
        else:
            # Fallback: average of window stdevs
            stdev_cols = [f"w{w}_bqx_stdev" for w in self.config['bqx']['windows']]
            available_cols = [c for c in stdev_cols if c in bqx_df.columns]
            vol = bqx_df[available_cols].mean(axis=1)

        # Classify into tertiles
        low_thresh = vol.quantile(0.33)
        high_thresh = vol.quantile(0.67)

        regime = pd.Series(1, index=bqx_df.index)  # Default medium
        regime[vol <= low_thresh] = 0  # Low volatility
        regime[vol >= high_thresh] = 2  # High volatility

        return regime

    def create_trend_strength(self, reg_df: pd.DataFrame) -> pd.Series:
        """
        Calculate trend strength from regression features

        Uses R² values to measure how linear the trend is
        High R² = strong linear trend

        Args:
            reg_df: DataFrame with REG features

        Returns:
            Series with trend strength (0 to 1)
        """
        r2_cols = [f"w{w}_r2" for w in self.config['reg']['windows']]
        available_cols = [c for c in r2_cols if c in reg_df.columns]

        if not available_cols:
            return pd.Series(0, index=reg_df.index)

        # Average R² across windows
        trend_strength = reg_df[available_cols].mean(axis=1)

        return trend_strength

    def create_target(
        self,
        bqx_df: pd.DataFrame,
        target_col: str = 'w60_bqx_return',
        horizon: int = 60
    ) -> pd.Series:
        """
        Create target variable for autoregressive prediction

        Target is BQX value at t+horizon (future)
        Uses shift(-horizon) to look ahead

        Args:
            bqx_df: DataFrame with BQX features
            target_col: BQX column to predict (default: w60_bqx_return)
            horizon: Prediction horizon in minutes (default: 60)

        Returns:
            Series with future BQX values
        """
        if target_col not in bqx_df.columns:
            raise ValueError(f"Target column {target_col} not found in BQX data")

        # Shift backward (negative) to get future values
        target = bqx_df[target_col].shift(-horizon)

        return target

    def apply_temporal_causality_rule(
        self,
        features_df: pd.DataFrame,
        lag_minutes: int = 61
    ) -> pd.DataFrame:
        """
        Apply 61-minute lag rule for temporal causality

        From USER-EXPECTATIONS: For any feature that uses target window data,
        must use data from t-61 or earlier to prevent overlap with target

        Args:
            features_df: DataFrame with all features
            lag_minutes: Minimum lag in minutes (default: 61)

        Returns:
            DataFrame with lagged features for target-window columns
        """
        result = features_df.copy()

        # Target window columns (60-minute windows and aggregates)
        # These need to be lagged by 61+ minutes
        target_window_patterns = [
            'w60_',  # 60-minute window features
            'agg_'   # Aggregate features (use overlapping data)
        ]

        for col in features_df.columns:
            needs_lag = any(pattern in col for pattern in target_window_patterns)

            if needs_lag and '_lag' not in col:  # Don't double-lag
                # Shift this feature by lag_minutes
                lagged_col = f"{col}_causality_lag{lag_minutes}"
                result[lagged_col] = features_df[col].shift(lag_minutes)
                # Optionally drop the unlagged version
                # result.drop(columns=[col], inplace=True)

        return result

    def engineer_features(
        self,
        bqx_df: pd.DataFrame,
        reg_df: pd.DataFrame,
        target_col: str = 'w60_bqx_return',
        target_horizon: int = 60,
        apply_causality: bool = True
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Full feature engineering pipeline

        Args:
            bqx_df: BQX features from Aurora
            reg_df: REG features from Aurora
            target_col: Column to predict
            target_horizon: Prediction horizon in minutes
            apply_causality: Whether to apply 61-min lag rule

        Returns:
            Tuple of (features_df, target_series)
        """
        # 1. Merge BQX and REG on timestamp
        features = bqx_df.merge(
            reg_df,
            left_index=True,
            right_index=True,
            how='inner',
            suffixes=('_bqx', '_reg')
        )

        # 2. Create lagged features
        if self.config['lags']['enabled']:
            # Lag BQX features
            bqx_cols = [c for c in features.columns if 'bqx' in c.lower()]
            features = self.create_lagged_features(
                features,
                bqx_cols,
                self.config['lags']['windows']
            )

            # Lag REG features (optional, usually less important)
            # reg_cols = [c for c in features.columns if any(f"w{w}_" in c for w in self.config['reg']['windows'])]
            # features = self.create_lagged_features(features, reg_cols, [60, 120])

        # 3. Create derived features
        if self.config['derived']['momentum_alignment']:
            features['momentum_alignment'] = self.create_momentum_alignment(bqx_df)

        if self.config['derived']['volatility_regime']:
            features['volatility_regime'] = self.create_volatility_regime(bqx_df)

        if self.config['derived']['trend_strength']:
            features['trend_strength'] = self.create_trend_strength(reg_df)

        # 4. Create target variable
        target = self.create_target(bqx_df, target_col, target_horizon)

        # 5. Apply temporal causality rule (optional but recommended)
        if apply_causality:
            features = self.apply_temporal_causality_rule(features, lag_minutes=61)

        # 6. Drop rows with NaN (due to lagging and target creation)
        valid_idx = target.notna() & features.notna().all(axis=1)
        features_clean = features[valid_idx]
        target_clean = target[valid_idx]

        return features_clean, target_clean

    def get_feature_names(self, features_df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Categorize features by type

        Args:
            features_df: Engineered features dataframe

        Returns:
            Dictionary with feature categories
        """
        categories = {
            'bqx_raw': [],
            'bqx_lagged': [],
            'reg_raw': [],
            'reg_lagged': [],
            'derived': [],
            'causality_lagged': []
        }

        for col in features_df.columns:
            if 'causality_lag' in col:
                categories['causality_lagged'].append(col)
            elif 'lag' in col and 'bqx' in col:
                categories['bqx_lagged'].append(col)
            elif 'lag' in col:
                categories['reg_lagged'].append(col)
            elif 'bqx' in col.lower():
                categories['bqx_raw'].append(col)
            elif any(f"w{w}_" in col for w in self.config['reg']['windows']):
                categories['reg_raw'].append(col)
            else:
                categories['derived'].append(col)

        return categories


if __name__ == "__main__":
    """
    Example usage
    """
    from extraction import AuroraExtractor

    # Load data
    extractor = AuroraExtractor()
    bqx, reg = extractor.load(
        pair='eurusd',
        start_date='2024-07-01',
        end_date='2024-08-01'
    )

    # Engineer features
    engineer = FeatureEngineer()
    features, target = engineer.engineer_features(
        bqx,
        reg,
        target_col='w60_bqx_return',
        target_horizon=60
    )

    print(f"Features shape: {features.shape}")
    print(f"Target shape: {target.shape}")

    # Categorize features
    categories = engineer.get_feature_names(features)
    for cat, cols in categories.items():
        print(f"\n{cat}: {len(cols)} features")
        if cols:
            print(f"  Examples: {cols[:3]}")

    print(f"\nFirst 5 target values:\n{target.head()}")

    extractor.disconnect()
