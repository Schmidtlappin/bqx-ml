"""
BQX ML Baseline Model
Random Forest baseline for autoregressive BQX prediction
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import yaml
from pathlib import Path
from typing import Tuple, Dict, Optional
import warnings
warnings.filterwarnings('ignore')


class BQXBaselineModel:
    """
    Baseline Random Forest model for BQX autoregressive prediction

    Strategy:
    - Predict BQX_{t+60} from current BQX_t and lagged features
    - Use Random Forest for non-linear pattern detection
    - Hyperparameter tuning with TimeSeriesSplit
    - Standard scaling for features
    """

    def __init__(self, config_path: str = "config/models.yaml"):
        """
        Initialize baseline model

        Args:
            config_path: Path to model configuration file
        """
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                self.config = config.get('baseline', {})
                self.training_config = config.get('training', {})
        else:
            # Default configuration
            self.config = {
                'type': 'random_forest',
                'params': {
                    'n_estimators': 100,
                    'max_depth': 10,
                    'min_samples_split': 20,
                    'min_samples_leaf': 10,
                    'random_state': 42
                },
                'target': 'w60_bqx_return',
                'horizon': 60
            }
            self.training_config = {
                'cv': {'method': 'time_series_split', 'n_splits': 5},
                'hyperparameter_tuning': {'enabled': False}
            }

        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.is_trained = False

    def create_model(self, params: Optional[Dict] = None) -> RandomForestRegressor:
        """
        Create Random Forest model with specified parameters

        Args:
            params: Model hyperparameters (uses config if None)

        Returns:
            RandomForestRegressor instance
        """
        if params is None:
            params = self.config['params']

        model = RandomForestRegressor(
            n_estimators=params.get('n_estimators', 100),
            max_depth=params.get('max_depth', 10),
            min_samples_split=params.get('min_samples_split', 20),
            min_samples_leaf=params.get('min_samples_leaf', 10),
            random_state=params.get('random_state', 42),
            n_jobs=-1,  # Use all cores
            verbose=0
        )

        return model

    def prepare_data(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
        """
        Split data into train/val/test sets (time-based split)

        Args:
            X: Features dataframe
            y: Target series
            train_ratio: Proportion for training
            val_ratio: Proportion for validation

        Returns:
            Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        n = len(X)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        X_train = X.iloc[:train_end]
        X_val = X.iloc[train_end:val_end]
        X_test = X.iloc[val_end:]

        y_train = y.iloc[:train_end]
        y_val = y.iloc[train_end:val_end]
        y_test = y.iloc[val_end:]

        print(f"Data split:")
        print(f"  Train: {len(X_train):,} samples ({train_ratio*100:.1f}%)")
        print(f"  Val:   {len(X_val):,} samples ({val_ratio*100:.1f}%)")
        print(f"  Test:  {len(X_test):,} samples ({(1-train_ratio-val_ratio)*100:.1f}%)")

        return X_train, X_val, X_test, y_train, y_val, y_test

    def scale_features(
        self,
        X_train: pd.DataFrame,
        X_val: pd.DataFrame,
        X_test: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Scale features using StandardScaler

        Fit on training data, transform all sets

        Args:
            X_train, X_val, X_test: Feature dataframes

        Returns:
            Tuple of (X_train_scaled, X_val_scaled, X_test_scaled) as numpy arrays
        """
        # Fit scaler on training data
        X_train_scaled = self.scaler.fit_transform(X_train)

        # Transform validation and test sets
        X_val_scaled = self.scaler.transform(X_val)
        X_test_scaled = self.scaler.transform(X_test)

        # Store feature names
        self.feature_names = X_train.columns.tolist()

        return X_train_scaled, X_val_scaled, X_test_scaled

    def tune_hyperparameters(
        self,
        X_train: np.ndarray,
        y_train: pd.Series,
        n_iter: int = 50,
        cv_splits: int = 3
    ) -> Dict:
        """
        Tune hyperparameters using RandomizedSearchCV

        Args:
            X_train: Scaled training features
            y_train: Training target
            n_iter: Number of random parameter combinations
            cv_splits: Number of CV splits

        Returns:
            Best parameters dictionary
        """
        print(f"\nTuning hyperparameters ({n_iter} iterations, {cv_splits}-fold CV)...")

        # Parameter search space
        param_distributions = {
            'n_estimators': [50, 100, 150, 200],
            'max_depth': [5, 8, 10, 12, 15, None],
            'min_samples_split': [10, 20, 30, 40],
            'min_samples_leaf': [5, 10, 15, 20],
            'max_features': ['sqrt', 'log2', None]
        }

        # Base model
        base_model = RandomForestRegressor(random_state=42, n_jobs=-1)

        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=cv_splits)

        # Randomized search
        search = RandomizedSearchCV(
            base_model,
            param_distributions,
            n_iter=n_iter,
            cv=tscv,
            scoring='r2',
            n_jobs=-1,
            verbose=1,
            random_state=42
        )

        search.fit(X_train, y_train)

        print(f"Best R² (CV): {search.best_score_:.4f}")
        print(f"Best parameters: {search.best_params_}")

        return search.best_params_

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        tune_hyperparams: bool = False,
        verbose: bool = True
    ) -> Dict:
        """
        Train baseline model

        Args:
            X: Features dataframe
            y: Target series
            tune_hyperparams: Whether to tune hyperparameters
            verbose: Print training progress

        Returns:
            Dictionary with training metrics
        """
        if verbose:
            print("=" * 60)
            print("BQX ML Baseline Model Training")
            print("=" * 60)

        # 1. Split data
        X_train, X_val, X_test, y_train, y_val, y_test = self.prepare_data(X, y)

        # 2. Scale features
        X_train_scaled, X_val_scaled, X_test_scaled = self.scale_features(
            X_train, X_val, X_test
        )

        # 3. Hyperparameter tuning (optional)
        if tune_hyperparams and self.training_config.get('hyperparameter_tuning', {}).get('enabled', False):
            best_params = self.tune_hyperparameters(
                X_train_scaled,
                y_train,
                n_iter=self.training_config['hyperparameter_tuning'].get('n_iter', 50),
                cv_folds=self.training_config['hyperparameter_tuning'].get('cv_folds', 3)
            )
            self.model = self.create_model(best_params)
        else:
            self.model = self.create_model()

        # 4. Train model
        if verbose:
            print(f"\nTraining Random Forest...")
            print(f"  Features: {X_train_scaled.shape[1]}")
            print(f"  Training samples: {len(X_train):,}")

        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True

        # 5. Evaluate on all sets
        metrics = {}

        # Training set
        y_train_pred = self.model.predict(X_train_scaled)
        metrics['train'] = {
            'mae': mean_absolute_error(y_train, y_train_pred),
            'rmse': np.sqrt(mean_squared_error(y_train, y_train_pred)),
            'r2': r2_score(y_train, y_train_pred)
        }

        # Validation set
        y_val_pred = self.model.predict(X_val_scaled)
        metrics['val'] = {
            'mae': mean_absolute_error(y_val, y_val_pred),
            'rmse': np.sqrt(mean_squared_error(y_val, y_val_pred)),
            'r2': r2_score(y_val, y_val_pred)
        }

        # Test set
        y_test_pred = self.model.predict(X_test_scaled)
        metrics['test'] = {
            'mae': mean_absolute_error(y_test, y_test_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_test_pred)),
            'r2': r2_score(y_test, y_test_pred)
        }

        # Directional accuracy
        metrics['train']['dir_acc'] = self._directional_accuracy(y_train, y_train_pred)
        metrics['val']['dir_acc'] = self._directional_accuracy(y_val, y_val_pred)
        metrics['test']['dir_acc'] = self._directional_accuracy(y_test, y_test_pred)

        if verbose:
            self._print_metrics(metrics)

        return metrics

    def _directional_accuracy(self, y_true: pd.Series, y_pred: np.ndarray) -> float:
        """
        Calculate directional accuracy (% of correct direction predictions)

        Args:
            y_true: True values
            y_pred: Predicted values

        Returns:
            Directional accuracy (0 to 1)
        """
        direction_true = np.sign(y_true)
        direction_pred = np.sign(y_pred)
        correct = (direction_true == direction_pred).sum()
        return correct / len(y_true)

    def _print_metrics(self, metrics: Dict):
        """Print formatted metrics"""
        print("\n" + "=" * 60)
        print("Model Performance Metrics")
        print("=" * 60)

        for split in ['train', 'val', 'test']:
            m = metrics[split]
            print(f"\n{split.upper()}:")
            print(f"  MAE:         {m['mae']:.6f}")
            print(f"  RMSE:        {m['rmse']:.6f}")
            print(f"  R²:          {m['r2']:.4f}")
            print(f"  Dir Acc:     {m['dir_acc']:.2%}")

    def get_feature_importance(self, top_n: int = 20) -> pd.DataFrame:
        """
        Get feature importance from trained model

        Args:
            top_n: Number of top features to return

        Returns:
            DataFrame with feature importance
        """
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        })

        importance = importance.sort_values('importance', ascending=False)

        return importance.head(top_n)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions on new data

        Args:
            X: Features dataframe

        Returns:
            Predicted BQX values
        """
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        # Scale features
        X_scaled = self.scaler.transform(X)

        # Predict
        predictions = self.model.predict(X_scaled)

        return predictions

    def save(self, save_dir: str = "models/saved", model_name: str = "baseline"):
        """
        Save trained model and scaler

        Args:
            save_dir: Directory to save model
            model_name: Name prefix for saved files
        """
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        # Save model
        model_file = save_path / f"{model_name}_model.joblib"
        joblib.dump(self.model, model_file)

        # Save scaler
        scaler_file = save_path / f"{model_name}_scaler.joblib"
        joblib.dump(self.scaler, scaler_file)

        # Save feature names
        features_file = save_path / f"{model_name}_features.joblib"
        joblib.dump(self.feature_names, features_file)

        print(f"\nModel saved to {save_path}/")
        print(f"  - {model_name}_model.joblib")
        print(f"  - {model_name}_scaler.joblib")
        print(f"  - {model_name}_features.joblib")

    def load(self, save_dir: str = "models/saved", model_name: str = "baseline"):
        """
        Load trained model and scaler

        Args:
            save_dir: Directory containing saved model
            model_name: Name prefix for saved files
        """
        save_path = Path(save_dir)

        # Load model
        model_file = save_path / f"{model_name}_model.joblib"
        self.model = joblib.load(model_file)

        # Load scaler
        scaler_file = save_path / f"{model_name}_scaler.joblib"
        self.scaler = joblib.load(scaler_file)

        # Load feature names
        features_file = save_path / f"{model_name}_features.joblib"
        self.feature_names = joblib.load(features_file)

        self.is_trained = True

        print(f"Model loaded from {save_path}/")


if __name__ == "__main__":
    """
    Example usage: Train baseline model on EURUSD
    """
    import sys
    sys.path.append('..')

    from data.extraction import AuroraExtractor
    from data.features import FeatureEngineer

    print("BQX ML Baseline Model - Example Training\n")

    # 1. Load data
    print("Loading data from Aurora...")
    extractor = AuroraExtractor()
    bqx, reg = extractor.load(
        pair='eurusd',
        start_date='2024-07-01',
        end_date='2024-10-01'  # 3 months for example
    )
    extractor.disconnect()

    print(f"  BQX shape: {bqx.shape}")
    print(f"  REG shape: {reg.shape}")

    # 2. Engineer features
    print("\nEngineering features...")
    engineer = FeatureEngineer()
    X, y = engineer.engineer_features(
        bqx,
        reg,
        target_col='w60_bqx_return',
        target_horizon=60,
        apply_causality=True
    )

    print(f"  Features: {X.shape}")
    print(f"  Target: {y.shape}")

    # 3. Train model
    model = BQXBaselineModel()
    metrics = model.train(X, y, tune_hyperparams=False)

    # 4. Feature importance
    print("\n" + "=" * 60)
    print("Top 20 Most Important Features")
    print("=" * 60)
    importance = model.get_feature_importance(top_n=20)
    print(importance.to_string(index=False))

    # 5. Save model
    model.save(save_dir="../models/saved", model_name="baseline_eurusd")

    print("\n✓ Training complete!")
