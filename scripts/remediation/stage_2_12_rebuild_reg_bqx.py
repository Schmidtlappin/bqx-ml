#!/usr/bin/env python3
"""
Stage 2.12: Rebuild reg_bqx with Aligned Windows
Rebuilds all 336 reg_bqx_* partitions with:
- Aligned windows: {60, 90, 150, 240, 390, 630} (matching reg_rate)
- Term-based architecture: quadratic_term, linear_term, constant_term, residual
- NOT coefficient-based (a2, a1, b)

Estimated Duration: 3-4 hours
Estimated Cost: $1.20
Risk: MEDIUM (requires re-computation, backup recommended)
"""

import psycopg2
import pandas as pd
import numpy as np
import logging
import sys
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from sqlalchemy import create_engine
from urllib.parse import quote_plus

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com'),
    'database': 'bqx',
    'user': 'postgres',
    'password': os.environ.get('DB_PASSWORD', 'BQX_Aurora_2025_Secure')
}

# Create SQLAlchemy engine for pandas (eliminates UserWarning)
DB_URL = f"postgresql://{DB_CONFIG['user']}:{quote_plus(DB_CONFIG['password'])}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
ENGINE = create_engine(DB_URL, pool_pre_ping=True)

# All 28 currency pairs
PAIRS = [
    'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
    'cadchf', 'cadjpy', 'chfjpy',
    'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
    'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
    'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
    'usdcad', 'usdchf', 'usdjpy'
]

# All 12 months (July 2024 - June 2025)
MONTHS = [
    '2024_07', '2024_08', '2024_09', '2024_10', '2024_11', '2024_12',
    '2025_01', '2025_02', '2025_03', '2025_04', '2025_05', '2025_06'
]

# NEW ALIGNED WINDOWS (matching reg_rate)
WINDOWS = [60, 90, 150, 240, 390, 630]

# Create logs directory
os.makedirs('/tmp/logs/remediation/stage_2_12', exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/logs/remediation/stage_2_12/rebuild.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def fit_parabola_with_terms_bqx(x, y):
    """
    Fit parabola to BQX data and return TERM-BASED results (not coefficients).

    CRITICAL: DO NOT normalize x for BQX data (already normalized).

    Args:
        x: Array of time indices
        y: Array of BQX return values

    Returns:
        dict: Term-based features (quadratic_term, linear_term, constant_term, residual, etc.)
    """
    try:
        n = len(x)
        if n < 3:
            return None

        # DO NOT NORMALIZE X (BQX is already normalized)
        # This is critical - we use raw x values

        # Polynomial fit (degree 2)
        coeffs = np.polyfit(x, y, deg=2)
        a2, a1, a0 = coeffs

        # Get the last x value for term evaluation
        x_end = x[-1]

        # TERM-BASED CALCULATION (not coefficient-based)
        quadratic_term = a2 * (x_end ** 2)
        linear_term = a1 * x_end
        constant_term = a0

        # Prediction at x_end
        prediction = quadratic_term + linear_term + constant_term

        # Residual (actual - predicted)
        y_end = y[-1]
        residual = y_end - prediction

        # Calculate R² and RMSE
        y_pred = np.polyval(coeffs, x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r2 = 1 - (ss_res / (ss_tot + 1e-10))
        rmse = np.sqrt(ss_res / n)

        return {
            'quadratic_term': float(quadratic_term),
            'linear_term': float(linear_term),
            'constant_term': float(constant_term),
            'residual': float(residual),
            'r2': float(r2),
            'rmse': float(rmse),
            'prediction': float(prediction)
        }

    except Exception as e:
        logger.error(f"Error in fit_parabola_with_terms_bqx: {e}")
        return None


def create_reg_bqx_table_schema(pair):
    """
    Create new reg_bqx parent table with term-based schema and aligned windows.

    Args:
        pair: Currency pair (e.g., 'eurusd')
    """
    table_name = f"reg_bqx_{pair}"

    # Build column definitions for all windows
    column_defs = []
    for window in WINDOWS:
        column_defs.extend([
            f"w{window}_quadratic_term DOUBLE PRECISION",
            f"w{window}_linear_term DOUBLE PRECISION",
            f"w{window}_constant_term DOUBLE PRECISION",
            f"w{window}_residual DOUBLE PRECISION",
            f"w{window}_r2 DOUBLE PRECISION",
            f"w{window}_rmse DOUBLE PRECISION",
            f"w{window}_prediction DOUBLE PRECISION"
        ])

    columns_sql = ",\n    ".join(column_defs)

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS bqx.{table_name} (
        ts_utc TIMESTAMP WITHOUT TIME ZONE NOT NULL,
        {columns_sql}
    ) PARTITION BY RANGE (ts_utc);
    """

    comment_sql = f"""
    COMMENT ON TABLE bqx.{table_name} IS
    'Regression features calculated from BQX (normalized forex returns).
    Source: BQX columns from bqx_{pair} table.
    Windows: {{60, 90, 150, 240, 390, 630}} (ALIGNED with reg_rate).
    Architecture: Term-based (quadratic_term, linear_term, constant_term, residual).
    NOT coefficient-based.
    Rebuilt: 2025-11-16 (Stage 2.12).';
    """

    return create_table_sql, comment_sql


def create_partition(pair, year_month):
    """
    Create a single partition for reg_bqx table.

    Args:
        pair: Currency pair
        year_month: Month partition (e.g., '2024_07')
    """
    table_name = f"reg_bqx_{pair}"
    partition_name = f"reg_bqx_{pair}_{year_month}"

    # Determine date range from year_month
    year, month = year_month.split('_')
    year = int(year)
    month = int(month)

    # Calculate next month
    if month == 12:
        next_year = year + 1
        next_month = 1
    else:
        next_year = year
        next_month = month + 1

    start_date = f"{year}-{month:02d}-01"
    end_date = f"{next_year}-{next_month:02d}-01"

    create_partition_sql = f"""
    CREATE TABLE IF NOT EXISTS bqx.{partition_name}
    PARTITION OF bqx.{table_name}
    FOR VALUES FROM ('{start_date}') TO ('{end_date}');
    """

    create_index_sql = f"""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_{partition_name}_ts_utc
    ON bqx.{partition_name} (ts_utc);
    """

    return create_partition_sql, create_index_sql


def populate_reg_bqx_partition(pair, year_month):
    """
    Populate a single reg_bqx partition with term-based regression features.

    Args:
        pair: Currency pair (e.g., 'eurusd')
        year_month: Month partition (e.g., '2024_07')

    Returns:
        tuple: (pair, year_month, success, rows_inserted, error_msg)
    """
    start_time = time.time()
    partition_name = f"reg_bqx_{pair}_{year_month}"

    try:
        logger.info(f"{pair.upper()} {year_month}: Starting regression computation...")

        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Load BQX data for this month
        year, month = year_month.split('_')
        start_date = f"{year}-{month}-01"

        query = f"""
        SELECT ts_utc, w15_bqx_return
        FROM bqx.bqx_{pair}
        WHERE ts_utc >= '{start_date}'::timestamp
        AND ts_utc < ('{start_date}'::timestamp + INTERVAL '1 month')
        AND w15_bqx_return IS NOT NULL
        ORDER BY ts_utc
        """

        # Use SQLAlchemy engine for pandas (eliminates UserWarning)
        df = pd.read_sql(query, ENGINE)

        if len(df) == 0:
            logger.warning(f"{pair.upper()} {year_month}: No data found, skipping")
            cur.close()
            conn.close()
            return (pair, year_month, True, 0, "No data")

        logger.info(f"{pair.upper()} {year_month}: Loaded {len(df):,} rows")

        # Prepare results DataFrame
        results = df[['ts_utc']].copy()

        # Compute regression for each window
        for window in WINDOWS:
            logger.info(f"{pair.upper()} {year_month}: Computing w{window}...")

            window_features = []

            for i in range(len(df)):
                if i < window - 1:
                    # Not enough data yet
                    window_features.append({
                        'quadratic_term': None,
                        'linear_term': None,
                        'constant_term': None,
                        'residual': None,
                        'r2': None,
                        'rmse': None,
                        'prediction': None
                    })
                else:
                    # Get window data
                    window_data = df.iloc[i - window + 1:i + 1]
                    x = np.arange(len(window_data))
                    y = window_data['w15_bqx_return'].values

                    # Fit parabola with term-based calculation
                    features = fit_parabola_with_terms_bqx(x, y)

                    if features is None:
                        features = {
                            'quadratic_term': None,
                            'linear_term': None,
                            'constant_term': None,
                            'residual': None,
                            'r2': None,
                            'rmse': None,
                            'prediction': None
                        }

                    window_features.append(features)

            # Add features to results DataFrame
            for key in ['quadratic_term', 'linear_term', 'constant_term', 'residual', 'r2', 'rmse', 'prediction']:
                col_name = f"w{window}_{key}"
                results[col_name] = [f[key] for f in window_features]

        # Remove rows with NaT timestamps
        initial_count = len(results)
        results = results[results['ts_utc'].notna()].copy()
        if len(results) < initial_count:
            logger.warning(f"{pair.upper()} {year_month}: Removed {initial_count - len(results)} rows with NaT timestamps")

        # Insert results into partition
        if len(results) > 0:
            logger.info(f"{pair.upper()} {year_month}: Inserting {len(results):,} rows...")

            # Build column list
            columns = ['ts_utc']
            for window in WINDOWS:
                for key in ['quadratic_term', 'linear_term', 'constant_term', 'residual', 'r2', 'rmse', 'prediction']:
                    columns.append(f"w{window}_{key}")

            # Build values for bulk insert
            values_list = []
            for _, row in results.iterrows():
                row_values = []
                for col in columns:
                    val = row[col]
                    if pd.isna(val):
                        row_values.append('NULL')
                    elif isinstance(val, (pd.Timestamp, datetime)):
                        row_values.append(f"'{val}'")
                    else:
                        row_values.append(str(val))
                values_list.append(f"({','.join(row_values)})")

            # Execute bulk insert (in batches of 1000)
            batch_size = 1000
            for i in range(0, len(values_list), batch_size):
                batch = values_list[i:i + batch_size]
                insert_sql = f"""
                INSERT INTO bqx.{partition_name} ({','.join(columns)})
                VALUES {','.join(batch)}
                ON CONFLICT (ts_utc) DO NOTHING
                """
                cur.execute(insert_sql)

            conn.commit()

            rows_inserted = len(results)
            logger.info(f"{pair.upper()} {year_month}: Inserted {rows_inserted:,} rows")
        else:
            rows_inserted = 0

        cur.close()
        conn.close()

        elapsed = time.time() - start_time
        logger.info(f"✅ {pair.upper()} {year_month}: Complete! ({elapsed:.1f}s)")

        return (pair, year_month, True, rows_inserted, None)

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        logger.error(f"❌ {pair.upper()} {year_month}: Failed after {elapsed:.1f}s - {error_msg}")
        return (pair, year_month, False, 0, error_msg)


def rebuild_reg_bqx_for_pair(pair):
    """
    Rebuild all partitions for a single pair.

    Args:
        pair: Currency pair

    Returns:
        dict: Results summary
    """
    logger.info(f"=" * 80)
    logger.info(f"{pair.upper()}: Starting rebuild")
    logger.info(f"=" * 80)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Drop old table if exists
        table_name = f"reg_bqx_{pair}"
        logger.info(f"{pair.upper()}: Dropping old table...")
        cur.execute(f"DROP TABLE IF EXISTS bqx.{table_name} CASCADE")
        conn.commit()

        # Create new parent table
        logger.info(f"{pair.upper()}: Creating new table with term-based schema...")
        create_table_sql, comment_sql = create_reg_bqx_table_schema(pair)
        cur.execute(create_table_sql)
        cur.execute(comment_sql)
        conn.commit()

        # Create all partitions
        logger.info(f"{pair.upper()}: Creating {len(MONTHS)} partitions...")
        for year_month in MONTHS:
            create_partition_sql, create_index_sql = create_partition(pair, year_month)
            cur.execute(create_partition_sql)
            cur.execute(create_index_sql)
        conn.commit()

        cur.close()
        conn.close()

        logger.info(f"{pair.upper()}: Table structure created successfully")

        # Populate all partitions
        results = {'success': 0, 'failed': 0, 'no_data': 0, 'total_rows': 0}

        for year_month in MONTHS:
            pair_name, ym, success, rows, error_msg = populate_reg_bqx_partition(pair, year_month)

            if success:
                if error_msg and "No data" in error_msg:
                    results['no_data'] += 1
                else:
                    results['success'] += 1
                    results['total_rows'] += rows
            else:
                results['failed'] += 1

        logger.info(f"{pair.upper()}: Rebuild complete - {results['success']}/{len(MONTHS)} partitions populated, {results['total_rows']:,} total rows")

        return results

    except Exception as e:
        logger.error(f"❌ {pair.upper()}: Rebuild failed - {e}")
        return {'success': 0, 'failed': len(MONTHS), 'no_data': 0, 'total_rows': 0}


def main():
    """Main execution: Rebuild all reg_bqx tables."""
    logger.info("=" * 80)
    logger.info("STAGE 2.12: REBUILD reg_bqx WITH ALIGNED WINDOWS")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Currency pairs: {len(PAIRS)}")
    logger.info(f"Months per pair: {len(MONTHS)}")
    logger.info(f"Total partitions: {len(PAIRS) * len(MONTHS)}")
    logger.info(f"NEW Windows: {WINDOWS}")
    logger.info(f"Features per window: 7 (quadratic_term, linear_term, constant_term, residual, r2, rmse, prediction)")
    logger.info(f"Total features per partition: {len(WINDOWS) * 7}")
    logger.info("")

    start_time = time.time()

    # Process pairs sequentially (can parallelize if needed)
    all_results = {'pairs_success': 0, 'pairs_failed': 0, 'total_partitions': 0, 'total_rows': 0}

    for pair in PAIRS:
        results = rebuild_reg_bqx_for_pair(pair)

        if results['failed'] == 0:
            all_results['pairs_success'] += 1
        else:
            all_results['pairs_failed'] += 1

        all_results['total_partitions'] += results['success']
        all_results['total_rows'] += results['total_rows']

    elapsed = time.time() - start_time

    logger.info("")
    logger.info("=" * 80)
    logger.info("STAGE 2.12 COMPLETE")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Duration: {elapsed/60:.1f} minutes ({elapsed/3600:.2f} hours)")
    logger.info(f"Pairs processed: {all_results['pairs_success']}/{len(PAIRS)}")
    logger.info(f"Pairs failed: {all_results['pairs_failed']}/{len(PAIRS)}")
    logger.info(f"Partitions populated: {all_results['total_partitions']}/{len(PAIRS) * len(MONTHS)}")
    logger.info(f"Total rows: {all_results['total_rows']:,}")
    logger.info("")

    if all_results['pairs_failed'] > 0:
        logger.error("❌ Stage 2.12 completed with errors")
        logger.info("=" * 80)
        return 1
    else:
        logger.info("✅ Stage 2.12 completed successfully - All reg_bqx tables rebuilt with aligned windows")
        logger.info("=" * 80)
        return 0


if __name__ == '__main__':
    sys.exit(main())
