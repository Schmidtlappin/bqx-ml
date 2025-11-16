#!/usr/bin/env python3
"""
Stage 2.14: Add Term Covariance Features
Adds 6 term covariance features to all correlation_bqx_* tables for:
- Trend exhaustion detection
- Breakout detection
- Regime change detection

Features Added (per partition):
1. cov_quad_lin_bqx_60min - Covariance between quadratic and linear terms
2. cov_resid_quad_bqx_60min - Covariance between residual and quadratic term
3. cov_resid_lin_bqx_60min - Covariance between residual and linear term
4. corr_quad_lin_bqx_60min - Correlation (normalized)
5. corr_resid_quad_bqx_60min - Correlation (normalized)
6. corr_resid_lin_bqx_60min - Correlation (normalized)

Estimated Duration: 2-3 hours
Estimated Cost: $0.80
Risk: LOW (additive only, non-destructive)
"""

import psycopg2
import pandas as pd
import numpy as np
import logging
import sys
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com'),
    'database': 'bqx',
    'user': 'postgres',
    'password': os.environ.get('DB_PASSWORD', 'BQX_Aurora_2025_Secure')
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

# All 12 months
MONTHS = [
    '2024_07', '2024_08', '2024_09', '2024_10', '2024_11', '2024_12',
    '2025_01', '2025_02', '2025_03', '2025_04', '2025_05', '2025_06'
]

# Window size for covariance calculation
COVARIANCE_WINDOW = 60  # 60 minutes (1 hour rolling window)

# Create logs directory
os.makedirs('/tmp/logs/remediation/stage_2_14', exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/logs/remediation/stage_2_14/covariance.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def add_covariance_columns_to_table(pair):
    """
    Add 6 covariance feature columns to correlation_bqx parent table.

    Args:
        pair: Currency pair (e.g., 'eurusd')

    Returns:
        bool: Success status
    """
    table_name = f"correlation_bqx_{pair}"

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Check if table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'bqx'
                AND table_name = %s
            )
        """, (table_name,))

        if not cur.fetchone()[0]:
            logger.warning(f"{pair.upper()}: Table {table_name} does not exist, skipping")
            cur.close()
            conn.close()
            return False

        logger.info(f"{pair.upper()}: Adding covariance columns to {table_name}...")

        # Add all 6 columns
        covariance_columns = [
            'cov_quad_lin_bqx_60min',
            'cov_resid_quad_bqx_60min',
            'cov_resid_lin_bqx_60min',
            'corr_quad_lin_bqx_60min',
            'corr_resid_quad_bqx_60min',
            'corr_resid_lin_bqx_60min'
        ]

        for col in covariance_columns:
            # Check if column exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_schema = 'bqx'
                    AND table_name = %s
                    AND column_name = %s
                )
            """, (table_name, col))

            if cur.fetchone()[0]:
                logger.info(f"{pair.upper()}: Column {col} already exists, skipping")
                continue

            # Add column
            cur.execute(f"""
                ALTER TABLE bqx.{table_name}
                ADD COLUMN {col} DOUBLE PRECISION
            """)
            logger.info(f"{pair.upper()}: Added {col}")

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ {pair.upper()}: Columns added successfully")
        return True

    except Exception as e:
        logger.error(f"❌ {pair.upper()}: Failed to add columns - {e}")
        return False


def calculate_term_covariances(quadratic_term, linear_term, residual, window_size=60):
    """
    Calculate covariances and correlations between regression terms.

    Args:
        quadratic_term: Series of quadratic term values
        linear_term: Series of linear term values
        residual: Series of residual values
        window_size: Rolling window size (default 60 minutes)

    Returns:
        dict: Covariance and correlation values
    """
    try:
        # Need at least window_size points
        if len(quadratic_term) < window_size:
            return {
                'cov_quad_lin': None,
                'cov_resid_quad': None,
                'cov_resid_lin': None,
                'corr_quad_lin': None,
                'corr_resid_quad': None,
                'corr_resid_lin': None
            }

        # Get last window_size values
        quad_window = quadratic_term[-window_size:]
        lin_window = linear_term[-window_size:]
        resid_window = residual[-window_size:]

        # Calculate covariances
        cov_quad_lin = np.cov(quad_window, lin_window)[0, 1]
        cov_resid_quad = np.cov(resid_window, quad_window)[0, 1]
        cov_resid_lin = np.cov(resid_window, lin_window)[0, 1]

        # Calculate correlations (normalized to [-1, 1])
        corr_quad_lin = np.corrcoef(quad_window, lin_window)[0, 1]
        corr_resid_quad = np.corrcoef(resid_window, quad_window)[0, 1]
        corr_resid_lin = np.corrcoef(resid_window, lin_window)[0, 1]

        return {
            'cov_quad_lin': float(cov_quad_lin) if not np.isnan(cov_quad_lin) else None,
            'cov_resid_quad': float(cov_resid_quad) if not np.isnan(cov_resid_quad) else None,
            'cov_resid_lin': float(cov_resid_lin) if not np.isnan(cov_resid_lin) else None,
            'corr_quad_lin': float(corr_quad_lin) if not np.isnan(corr_quad_lin) else None,
            'corr_resid_quad': float(corr_resid_quad) if not np.isnan(corr_resid_quad) else None,
            'corr_resid_lin': float(corr_resid_lin) if not np.isnan(corr_resid_lin) else None
        }

    except Exception as e:
        logger.error(f"Error calculating covariances: {e}")
        return {
            'cov_quad_lin': None,
            'cov_resid_quad': None,
            'cov_resid_lin': None,
            'corr_quad_lin': None,
            'corr_resid_quad': None,
            'corr_resid_lin': None
        }


def populate_covariance_features(pair, year_month):
    """
    Populate covariance features for a single partition.

    Args:
        pair: Currency pair
        year_month: Month partition

    Returns:
        tuple: (pair, year_month, success, rows_updated, error_msg)
    """
    start_time = time.time()
    partition_name = f"correlation_bqx_{pair}_{year_month}"

    try:
        logger.info(f"{pair.upper()} {year_month}: Starting covariance calculation...")

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Load regression term data from reg_bqx table
        year, month = year_month.split('_')
        start_date = f"{year}-{month}-01"

        query = f"""
        SELECT ts_utc,
               w60_quadratic_term,
               w60_linear_term,
               w60_residual
        FROM bqx.reg_bqx_{pair}_{year_month}
        WHERE w60_quadratic_term IS NOT NULL
        AND w60_linear_term IS NOT NULL
        AND w60_residual IS NOT NULL
        ORDER BY ts_utc
        """

        df = pd.read_sql(query, conn)

        if len(df) == 0:
            logger.warning(f"{pair.upper()} {year_month}: No data found, skipping")
            cur.close()
            conn.close()
            return (pair, year_month, True, 0, "No data")

        logger.info(f"{pair.upper()} {year_month}: Loaded {len(df):,} rows")

        # Calculate covariances for each row
        covariance_features = []
        for i in range(len(df)):
            if i < COVARIANCE_WINDOW - 1:
                # Not enough data yet
                covariance_features.append({
                    'cov_quad_lin': None,
                    'cov_resid_quad': None,
                    'cov_resid_lin': None,
                    'corr_quad_lin': None,
                    'corr_resid_quad': None,
                    'corr_resid_lin': None
                })
            else:
                # Calculate covariances using rolling window
                features = calculate_term_covariances(
                    df['w60_quadratic_term'].iloc[:i+1],
                    df['w60_linear_term'].iloc[:i+1],
                    df['w60_residual'].iloc[:i+1],
                    window_size=COVARIANCE_WINDOW
                )
                covariance_features.append(features)

        # Update correlation_bqx table with covariance features
        logger.info(f"{pair.upper()} {year_month}: Updating {len(df):,} rows...")

        rows_updated = 0
        for idx, row in df.iterrows():
            ts_utc = row['ts_utc']
            features = covariance_features[idx]

            update_sql = f"""
            UPDATE bqx.{partition_name}
            SET cov_quad_lin_bqx_60min = %s,
                cov_resid_quad_bqx_60min = %s,
                cov_resid_lin_bqx_60min = %s,
                corr_quad_lin_bqx_60min = %s,
                corr_resid_quad_bqx_60min = %s,
                corr_resid_lin_bqx_60min = %s
            WHERE ts_utc = %s
            """

            cur.execute(update_sql, (
                features['cov_quad_lin'],
                features['cov_resid_quad'],
                features['cov_resid_lin'],
                features['corr_quad_lin'],
                features['corr_resid_quad'],
                features['corr_resid_lin'],
                ts_utc
            ))
            rows_updated += cur.rowcount

        conn.commit()
        cur.close()
        conn.close()

        elapsed = time.time() - start_time
        logger.info(f"✅ {pair.upper()} {year_month}: Complete! Updated {rows_updated:,} rows ({elapsed:.1f}s)")

        return (pair, year_month, True, rows_updated, None)

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        logger.error(f"❌ {pair.upper()} {year_month}: Failed after {elapsed:.1f}s - {error_msg}")
        return (pair, year_month, False, 0, error_msg)


def process_pair(pair):
    """
    Process all partitions for a single pair.

    Args:
        pair: Currency pair

    Returns:
        dict: Results summary
    """
    logger.info(f"=" * 80)
    logger.info(f"{pair.upper()}: Starting covariance feature addition")
    logger.info(f"=" * 80)

    # First, add columns to parent table
    if not add_covariance_columns_to_table(pair):
        return {'success': 0, 'failed': 12, 'no_data': 0, 'total_rows': 0}

    # Then populate all partitions
    results = {'success': 0, 'failed': 0, 'no_data': 0, 'total_rows': 0}

    for year_month in MONTHS:
        pair_name, ym, success, rows, error_msg = populate_covariance_features(pair, year_month)

        if success:
            if error_msg and "No data" in error_msg:
                results['no_data'] += 1
            else:
                results['success'] += 1
                results['total_rows'] += rows
        else:
            results['failed'] += 1

    logger.info(f"{pair.upper()}: Complete - {results['success']}/{len(MONTHS)} partitions, {results['total_rows']:,} rows updated")

    return results


def main():
    """Main execution: Add covariance features to all correlation_bqx tables."""
    logger.info("=" * 80)
    logger.info("STAGE 2.14: ADD TERM COVARIANCE FEATURES")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Currency pairs: {len(PAIRS)}")
    logger.info(f"Months per pair: {len(MONTHS)}")
    logger.info(f"Total partitions: {len(PAIRS) * len(MONTHS)}")
    logger.info(f"Features to add: 6 per partition")
    logger.info(f"Covariance window: {COVARIANCE_WINDOW} minutes")
    logger.info("")

    start_time = time.time()

    # Process pairs sequentially
    all_results = {'pairs_success': 0, 'pairs_failed': 0, 'total_partitions': 0, 'total_rows': 0}

    for pair in PAIRS:
        results = process_pair(pair)

        if results['failed'] == 0:
            all_results['pairs_success'] += 1
        else:
            all_results['pairs_failed'] += 1

        all_results['total_partitions'] += results['success']
        all_results['total_rows'] += results['total_rows']

    elapsed = time.time() - start_time

    logger.info("")
    logger.info("=" * 80)
    logger.info("STAGE 2.14 COMPLETE")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Duration: {elapsed/60:.1f} minutes ({elapsed/3600:.2f} hours)")
    logger.info(f"Pairs processed: {all_results['pairs_success']}/{len(PAIRS)}")
    logger.info(f"Pairs failed: {all_results['pairs_failed']}/{len(PAIRS)}")
    logger.info(f"Partitions updated: {all_results['total_partitions']}/{len(PAIRS) * len(MONTHS)}")
    logger.info(f"Total rows updated: {all_results['total_rows']:,}")
    logger.info("")

    if all_results['pairs_failed'] > 0:
        logger.error("❌ Stage 2.14 completed with errors")
        logger.info("=" * 80)
        return 1
    else:
        logger.info("✅ Stage 2.14 completed successfully - All covariance features added")
        logger.info("=" * 80)
        return 0


if __name__ == '__main__':
    sys.exit(main())
