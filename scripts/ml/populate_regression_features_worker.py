#!/usr/bin/env python3
"""
Track 2: Regression Features Population Worker
Populates reg_rate and reg_bqx tables with parabolic regression features.

Features per domain: 90 (6 windows × 15 metrics)
Windows: w15, w30, w45, w60, w75, agg
Metrics: a2, a1, b, R², RMSE, residuals, prediction intervals, etc.

This is the most compute-intensive track (polynomial regression on 10M+ rows).
"""

import psycopg2
import pandas as pd
import numpy as np
from scipy import stats
import logging
import sys
from pathlib import Path
from datetime import datetime
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

# Database configuration
DB_CONFIG = {
    'host': 'trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com',
    'database': 'bqx',
    'user': 'postgres',
    'password': 'BQX_Aurora_2025_Secure'
}

# All 28 currency pairs
PAIRS = [
    'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
    'cadchf', 'cadjpy', 'chfjpy',
    'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
    'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
    'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
    'usdcad', 'usdchf', 'usdjpy'
]

# Windows for regression
WINDOWS = {
    'w15': 15,
    'w30': 30,
    'w45': 45,
    'w60': 60,
    'w75': 75,
    'agg': 90  # Aggregate window
}

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/logs/track2/populate.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def fit_parabola(x, y):
    """
    Fit parabola y = a2*x^2 + a1*x + b and calculate metrics.

    Returns:
        dict: All 15 metrics for this window
    """
    try:
        n = len(x)
        if n < 3:
            return {k: None for k in ['a2', 'a1', 'b', 'r2', 'rmse', 'residual_mean',
                                      'residual_std', 'pred_interval_lower', 'pred_interval_upper',
                                      'prediction', 'vertex_x', 'vertex_y', 'curvature',
                                      'fit_quality', 'extrapolation_error']}

        # Normalize x to avoid numerical issues
        x_norm = (x - x.mean()) / (x.std() + 1e-10)

        # Polynomial fit (degree 2)
        coeffs = np.polyfit(x_norm, y, 2)
        a2, a1, b = coeffs

        # Predictions
        y_pred = np.polyval(coeffs, x_norm)

        # R² and RMSE
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r2 = 1 - (ss_res / (ss_tot + 1e-10))
        rmse = np.sqrt(ss_res / n)

        # Residuals
        residuals = y - y_pred
        residual_mean = residuals.mean()
        residual_std = residuals.std()

        # Prediction intervals (95%)
        pred_interval_lower = y_pred[-1] - 1.96 * residual_std
        pred_interval_upper = y_pred[-1] + 1.96 * residual_std
        prediction = y_pred[-1]

        # Parabola properties
        vertex_x = -a1 / (2 * a2 + 1e-10)
        vertex_y = a2 * vertex_x**2 + a1 * vertex_x + b

        # Curvature (how bent is the parabola)
        curvature = abs(a2)

        # Fit quality (normalized R²)
        fit_quality = max(0, min(1, r2))

        # Extrapolation error (prediction uncertainty)
        extrapolation_error = abs(residual_std / (abs(prediction) + 1e-10))

        return {
            'a2': float(a2),
            'a1': float(a1),
            'b': float(b),
            'r2': float(r2),
            'rmse': float(rmse),
            'residual_mean': float(residual_mean),
            'residual_std': float(residual_std),
            'pred_interval_lower': float(pred_interval_lower),
            'pred_interval_upper': float(pred_interval_upper),
            'prediction': float(prediction),
            'vertex_x': float(vertex_x),
            'vertex_y': float(vertex_y),
            'curvature': float(curvature),
            'fit_quality': float(fit_quality),
            'extrapolation_error': float(extrapolation_error)
        }

    except Exception as e:
        logger.warning(f"Regression fit failed: {e}")
        return {k: None for k in ['a2', 'a1', 'b', 'r2', 'rmse', 'residual_mean',
                                  'residual_std', 'pred_interval_lower', 'pred_interval_upper',
                                  'prediction', 'vertex_x', 'vertex_y', 'curvature',
                                  'fit_quality', 'extrapolation_error']}


def populate_regression_for_pair(pair, year_month):
    """
    Populate regression features for one pair and one month.

    Args:
        pair: Currency pair (e.g., 'eurusd')
        year_month: Month partition (e.g., '2024_07')

    Returns:
        tuple: (pair, year_month, success, row_count, error_msg)
    """
    start_time = time.time()

    try:
        logger.info(f"{pair.upper()} {year_month}: Starting regression computation...")

        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Fetch data from both M1 and BQX tables for this month
        year, month = year_month.split('_')

        # Fetch rate_index from M1 table
        m1_query = f"""
        SELECT time AS ts_utc, rate_index
        FROM bqx.m1_{pair}
        WHERE EXTRACT(YEAR FROM time) = {year}
          AND EXTRACT(MONTH FROM time) = {month}
        ORDER BY time;
        """

        # Fetch BQX data
        bqx_query = f"""
        SELECT ts_utc, w15_bqx_return
        FROM bqx.bqx_{pair}
        WHERE EXTRACT(YEAR FROM ts_utc) = {year}
          AND EXTRACT(MONTH FROM ts_utc) = {month}
        ORDER BY ts_utc;
        """

        df_m1 = pd.read_sql(m1_query, conn)
        df_bqx = pd.read_sql(bqx_query, conn)

        if df_m1.empty:
            logger.warning(f"{pair.upper()} {year_month}: No M1 data found")
            conn.close()
            return (pair, year_month, True, 0, "No data")

        # Convert M1 timestamps to UTC-aware to match BQX table
        df_m1['ts_utc'] = pd.to_datetime(df_m1['ts_utc'], utc=True)

        # Merge M1 and BQX data on timestamp
        df = pd.merge(df_m1, df_bqx, on='ts_utc', how='inner')

        if df.empty:
            logger.warning(f"{pair.upper()} {year_month}: No merged data after join")
            conn.close()
            return (pair, year_month, True, 0, "No data after join")

        logger.info(f"{pair.upper()} {year_month}: Loaded {len(df):,} rows (M1: {len(df_m1):,}, BQX: {len(df_bqx):,})")

        # Prepare results DataFrame
        results = pd.DataFrame({'ts_utc': df['ts_utc']})

        # Compute regression features for each window
        for window_name, window_size in WINDOWS.items():
            logger.info(f"{pair.upper()} {year_month}: Computing {window_name} (size={window_size})...")

            # Rate domain (rate_index)
            for i in range(len(df)):
                if i < window_size - 1:
                    # Not enough data for this window yet
                    for metric in ['a2', 'a1', 'b', 'r2', 'rmse', 'residual_mean',
                                   'residual_std', 'pred_interval_lower', 'pred_interval_upper',
                                   'prediction', 'vertex_x', 'vertex_y', 'curvature',
                                   'fit_quality', 'extrapolation_error']:
                        col_name = f"{metric}_idx_{window_name}"
                        if col_name not in results.columns:
                            results[col_name] = None
                    continue

                # Get window data
                window_data = df.iloc[i - window_size + 1:i + 1]['rate_index'].values
                x = np.arange(window_size)

                # Fit parabola
                metrics = fit_parabola(x, window_data)

                # Store metrics
                for metric_name, metric_value in metrics.items():
                    col_name = f"{metric_name}_idx_{window_name}"
                    if col_name not in results.columns:
                        results[col_name] = None
                    results.at[i, col_name] = metric_value

            # BQX domain (BQX momentum)
            for i in range(len(df)):
                if i < window_size - 1:
                    for metric in ['a2', 'a1', 'b', 'r2', 'rmse', 'residual_mean',
                                   'residual_std', 'pred_interval_lower', 'pred_interval_upper',
                                   'prediction', 'vertex_x', 'vertex_y', 'curvature',
                                   'fit_quality', 'extrapolation_error']:
                        col_name = f"{metric}_bqx_{window_name}"
                        if col_name not in results.columns:
                            results[col_name] = None
                    continue

                window_data = df.iloc[i - window_size + 1:i + 1]['w15_bqx_return'].values
                x = np.arange(window_size)

                metrics = fit_parabola(x, window_data)

                for metric_name, metric_value in metrics.items():
                    col_name = f"{metric_name}_bqx_{window_name}"
                    if col_name not in results.columns:
                        results[col_name] = None
                    results.at[i, col_name] = metric_value

        # Remove rows with NaT timestamps (cannot insert into database)
        initial_count = len(results)
        results = results[results['ts_utc'].notna()].copy()
        if len(results) < initial_count:
            logger.warning(f"{pair.upper()} {year_month}: Removed {initial_count - len(results)} rows with NaT timestamps")

        if results.empty:
            logger.warning(f"{pair.upper()} {year_month}: No valid data after filtering NaT")
            conn.close()
            return (pair, year_month, True, 0, "No valid data")

        # Insert into reg_rate table
        reg_rate_cols = ['ts_utc'] + [col for col in results.columns if '_idx_' in col]
        reg_rate_data = results[reg_rate_cols]

        partition_name = f"reg_rate_{pair}_{year_month}"
        # Bulk insert
        # (simplified - in production would use COPY for speed)
        cursor.execute(f"DELETE FROM bqx.{partition_name}")

        for _, row in reg_rate_data.iterrows():
            placeholders = ','.join(['%s'] * len(reg_rate_cols))
            cursor.execute(
                f"INSERT INTO bqx.{partition_name} ({','.join(reg_rate_cols)}) VALUES ({placeholders})",
                tuple(row)
            )

        conn.commit()

        # Insert into reg_bqx table
        reg_bqx_cols = ['ts_utc'] + [col for col in results.columns if '_bqx_' in col]
        reg_bqx_data = results[reg_bqx_cols]

        partition_name = f"reg_bqx_{pair}_{year_month}"
        cursor.execute(f"DELETE FROM bqx.{partition_name}")

        for _, row in reg_bqx_data.iterrows():
            placeholders = ','.join(['%s'] * len(reg_bqx_cols))
            cursor.execute(
                f"INSERT INTO bqx.{partition_name} ({','.join(reg_bqx_cols)}) VALUES ({placeholders})",
                tuple(row)
            )

        conn.commit()
        conn.close()

        elapsed = time.time() - start_time
        logger.info(f"✅ {pair.upper()} {year_month}: Complete! {len(results):,} rows, {elapsed:.1f}s")

        return (pair, year_month, True, len(results), None)

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        logger.error(f"❌ {pair.upper()} {year_month}: Failed after {elapsed:.1f}s - {error_msg}")
        return (pair, year_month, False, 0, error_msg)


def main():
    """
    Main execution: Populate regression features for all pairs and months.
    """
    logger.info("=" * 80)
    logger.info("TRACK 2: REGRESSION FEATURES POPULATION")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Pairs: {len(PAIRS)}")
    logger.info(f"Months per pair: ~18 (Jul 2024 - Jun 2025 for rate, full 2024-2025 for bqx)")
    logger.info(f"Features: 180 (90 per domain × 2 domains)")
    logger.info("")

    # Generate all tasks (pair, year_month combinations)
    tasks = []
    for pair in PAIRS:
        for year in [2024, 2025]:
            for month in range(1, 13):
                # Rate domain: Jul 2024 - Jun 2025
                if (year == 2024 and month >= 7) or (year == 2025 and month <= 6):
                    year_month = f"{year}_{month:02d}"
                    tasks.append((pair, year_month))

    logger.info(f"Total tasks: {len(tasks)} (pair × month combinations)")
    logger.info("")

    # Process tasks in parallel (4 workers for compute-intensive work)
    max_workers = 4
    logger.info(f"Processing with {max_workers} parallel workers...")
    logger.info("")

    start_time = time.time()
    results = {'success': 0, 'failed': 0, 'total_rows': 0}

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(populate_regression_for_pair, pair, ym): (pair, ym)
                   for pair, ym in tasks}

        for future in as_completed(futures):
            pair, ym = futures[future]
            try:
                pair_name, year_month, success, row_count, error_msg = future.result()

                if success:
                    results['success'] += 1
                    results['total_rows'] += row_count
                else:
                    results['failed'] += 1

            except Exception as e:
                logger.error(f"Unexpected error for {pair} {ym}: {e}")
                results['failed'] += 1

    elapsed = time.time() - start_time

    logger.info("")
    logger.info("=" * 80)
    logger.info("REGRESSION POPULATION COMPLETE")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Duration: {elapsed/3600:.1f} hours")
    logger.info(f"Successful: {results['success']}/{len(tasks)} tasks")
    logger.info(f"Failed: {results['failed']}/{len(tasks)} tasks")
    logger.info(f"Total rows: {results['total_rows']:,}")
    logger.info("=" * 80)

    sys.exit(0 if results['failed'] == 0 else 1)


if __name__ == '__main__':
    main()
