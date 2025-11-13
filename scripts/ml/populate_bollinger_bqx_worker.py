#!/usr/bin/env python3
"""
Track 1: Bollinger BQX Features Population Worker
Populates bollinger_bqx tables with Bollinger Band features on BQX w15 return.

Features: 21 (upper/middle/lower/width/percent_b for 4 windows + 2 slopes)
Windows: 20, 30, 60, 120
Tables: 672 (28 pairs × 24 monthly partitions)
"""

import psycopg2
import pandas as pd
import numpy as np
import logging
import sys
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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/logs/track1/bollinger.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def calculate_bollinger_bands(series, window=20, num_std=2):
    """
    Calculate Bollinger Bands for a series.

    Args:
        series: pandas Series
        window: SMA window size
        num_std: Number of standard deviations for bands

    Returns:
        dict: upper, middle, lower, width, percent_b
    """
    middle = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()

    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    width = upper - lower
    percent_b = (series - lower) / (width + 1e-10)  # Avoid division by zero

    return {
        'upper': upper,
        'middle': middle,
        'lower': lower,
        'width': width,
        'percent_b': percent_b
    }


def populate_bollinger_for_pair(pair, year_month):
    """
    Populate Bollinger BQX features for one pair and one month.

    Args:
        pair: Currency pair (e.g., 'eurusd')
        year_month: Month partition (e.g., '2024_07')

    Returns:
        tuple: (pair, year_month, success, row_count, error_msg)
    """
    start_time = time.time()

    try:
        logger.info(f"{pair.upper()} {year_month}: Starting Bollinger BQX computation...")

        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Fetch BQX data for this month
        year, month = year_month.split('_')
        query = f"""
        SELECT ts_utc, w15_bqx_return, agg_bqx_return
        FROM bqx.bqx_{pair}
        WHERE EXTRACT(YEAR FROM ts_utc) = {year}
          AND EXTRACT(MONTH FROM ts_utc) = {month}
        ORDER BY ts_utc;
        """

        df = pd.read_sql(query, conn)

        if df.empty:
            logger.warning(f"{pair.upper()} {year_month}: No BQX data found")
            conn.close()
            return (pair, year_month, True, 0, "No data")

        logger.info(f"{pair.upper()} {year_month}: Loaded {len(df):,} BQX rows")

        # Calculate Bollinger Bands for multiple windows on BQX w15 return
        bb_20 = calculate_bollinger_bands(df['w15_bqx_return'], window=20, num_std=2)
        bb_30 = calculate_bollinger_bands(df['w15_bqx_return'], window=30, num_std=2)
        bb_60 = calculate_bollinger_bands(df['w15_bqx_return'], window=60, num_std=2)
        bb_120 = calculate_bollinger_bands(df['w15_bqx_return'], window=120, num_std=2)

        # Prepare results DataFrame (matching actual bollinger_bqx table schema)
        results = pd.DataFrame({
            'ts_utc': df['ts_utc'],
            # Window 20
            'bb_upper_20': bb_20['upper'],
            'bb_middle_20': bb_20['middle'],
            'bb_lower_20': bb_20['lower'],
            'bb_width_20': bb_20['width'],
            'bb_percent_b_20': bb_20['percent_b'],
            # Window 30
            'bb_upper_30': bb_30['upper'],
            'bb_middle_30': bb_30['middle'],
            'bb_lower_30': bb_30['lower'],
            'bb_width_30': bb_30['width'],
            # Window 60
            'bb_upper_60': bb_60['upper'],
            'bb_middle_60': bb_60['middle'],
            'bb_lower_60': bb_60['lower'],
            'bb_width_60': bb_60['width'],
            'bb_percent_b_60': bb_60['percent_b'],
            # Window 120
            'bb_upper_120': bb_120['upper'],
            'bb_middle_120': bb_120['middle'],
            'bb_lower_120': bb_120['lower'],
            'bb_width_120': bb_120['width'],
            # Slopes (using width as proxy for slope)
            'bb_slope_20': bb_20['width'].diff(),
            'bb_slope_60': bb_60['width'].diff()
        })

        # Insert into bollinger_bqx table
        partition_name = f"bollinger_bqx_{pair}_{year_month}"

        # Check if partition exists
        cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM pg_tables
                WHERE schemaname = 'bqx'
                AND tablename = '{partition_name}'
            )
        """)

        if not cursor.fetchone()[0]:
            logger.warning(f"{pair.upper()} {year_month}: Partition {partition_name} does not exist, skipping")
            conn.close()
            return (pair, year_month, True, 0, "Partition not found")

        # Delete existing data
        cursor.execute(f"DELETE FROM bqx.{partition_name}")

        # Bulk insert using execute_values (faster than row-by-row)
        from psycopg2.extras import execute_values

        cols = list(results.columns)
        values = [tuple(row) for row in results.values]

        execute_values(
            cursor,
            f"INSERT INTO bqx.{partition_name} ({','.join(cols)}) VALUES %s",
            values
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
    Main execution: Populate Bollinger BQX features for all pairs and months.
    """
    logger.info("=" * 80)
    logger.info("TRACK 1: BOLLINGER BQX FEATURES POPULATION")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Pairs: {len(PAIRS)}")
    logger.info(f"Months per pair: 24 (Full 2024-2025)")
    logger.info(f"Features: 10 (Bollinger bands on BQX momentum)")
    logger.info("")

    # Generate all tasks (pair, year_month combinations)
    tasks = []
    for pair in PAIRS:
        for year in [2024, 2025]:
            for month in range(1, 13):
                year_month = f"{year}_{month:02d}"
                tasks.append((pair, year_month))

    logger.info(f"Total tasks: {len(tasks)} (pair × month combinations)")
    logger.info("")

    # Process tasks in parallel (2 workers - less intensive than regression)
    max_workers = 2
    logger.info(f"Processing with {max_workers} parallel workers...")
    logger.info("")

    start_time = time.time()
    results = {'success': 0, 'failed': 0, 'total_rows': 0}

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(populate_bollinger_for_pair, pair, ym): (pair, ym)
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
    logger.info("BOLLINGER BQX POPULATION COMPLETE")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Duration: {elapsed/60:.1f} minutes")
    logger.info(f"Successful: {results['success']}/{len(tasks)} tasks")
    logger.info(f"Failed: {results['failed']}/{len(tasks)} tasks")
    logger.info(f"Total rows: {results['total_rows']:,}")
    logger.info("=" * 80)

    sys.exit(0 if results['failed'] == 0 else 1)


if __name__ == '__main__':
    main()
