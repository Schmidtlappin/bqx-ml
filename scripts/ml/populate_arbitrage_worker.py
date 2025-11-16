#!/usr/bin/env python3
"""
Stage 2.4: Arbitrage Detection Worker
Detects triangular arbitrage opportunities across currency triplets.

Features (4 per partition):
1. arbitrage_profit_pct: Percentage profit from round-trip arbitrage
2. arbitrage_opportunity: Boolean flag if profit > threshold (0.5%)
3. arbitrage_direction: Optimal direction (1=clockwise, -1=counter-clockwise, 0=none)
4. arbitrage_max_profit: Maximum profit considering both directions

Algorithm:
  For each pair, finds valid triangular paths through a third currency
  Example for EURUSD: EUR → USD → GBP → EUR
  Calculates round-trip conversion and detects arbitrage opportunities

Estimated Runtime: 6 hours with 8 workers on D64as_v5
"""

import psycopg2
import pandas as pd
import numpy as np
import logging
import sys
import os
import time
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import combinations

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

# All 8 currencies
CURRENCIES = ['EUR', 'USD', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF']

# Create logs directory
os.makedirs('/tmp/logs/stage_2_4', exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/logs/stage_2_4/populate.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def get_pair_name(base, quote):
    """Get pair name for two currencies (e.g., 'EUR', 'USD' -> 'eurusd')."""
    pair_forward = base.lower() + quote.lower()
    pair_reverse = quote.lower() + base.lower()

    if pair_forward in PAIRS:
        return pair_forward, 1  # Direct (multiply)
    elif pair_reverse in PAIRS:
        return pair_reverse, -1  # Inverse (divide)
    else:
        return None, 0


def calculate_triangular_arbitrage(rate_1, rate_2, rate_3, dir_1, dir_2, dir_3, transaction_cost_pct=0.3):
    """
    Calculate arbitrage profit % for a triangular currency path.

    Args:
        rate_1, rate_2, rate_3: Exchange rates for 3 legs
        dir_1, dir_2, dir_3: Directions (1=multiply, -1=divide)
        transaction_cost_pct: Total cost % for round-trip (default 0.3%)

    Returns:
        float: Profit percentage (positive = arbitrage opportunity)
    """
    try:
        amount = 1.0  # Start with 1 unit

        # Leg 1
        if dir_1 == 1:
            amount *= rate_1
        else:
            amount /= rate_1

        # Leg 2
        if dir_2 == 1:
            amount *= rate_2
        else:
            amount /= rate_2

        # Leg 3
        if dir_3 == 1:
            amount *= rate_3
        else:
            amount /= rate_3

        # Subtract transaction costs
        amount *= (1 - transaction_cost_pct / 100.0)

        # Return profit percentage
        return (amount - 1.0) * 100.0

    except Exception as e:
        return 0.0


def find_triangular_paths(pair):
    """
    Find all valid triangular arbitrage paths for a given pair.

    Args:
        pair: Currency pair (e.g., 'eurusd')

    Returns:
        list: List of triangular paths (tuples of currencies)
    """
    base = pair[:3].upper()
    quote = pair[3:].upper()

    paths = []

    # For each third currency, check if triangular path exists
    for third in CURRENCIES:
        if third != base and third != quote:
            # Path: base → quote → third → base
            # Need: base/quote, quote/third, third/base

            pair_1, dir_1 = get_pair_name(base, quote)
            pair_2, dir_2 = get_pair_name(quote, third)
            pair_3, dir_3 = get_pair_name(third, base)

            if pair_1 and pair_2 and pair_3:
                paths.append({
                    'currencies': (base, quote, third),
                    'pairs': (pair_1, pair_2, pair_3),
                    'directions': (dir_1, dir_2, dir_3)
                })

    return paths


def populate_arbitrage_for_pair(pair, year_month):
    """
    Populate arbitrage features for one pair and one month.

    Args:
        pair: Currency pair (e.g., 'eurusd')
        year_month: Month partition (e.g., '2024_07')

    Returns:
        tuple: (pair, year_month, success, row_count, error_msg)
    """
    start_time = time.time()

    try:
        logger.info(f"{pair.upper()} {year_month}: Starting arbitrage detection...")

        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        year, month = year_month.split('_')

        # Fetch rate_index for THIS pair
        pair_query = f"""
        SELECT time AS ts_utc, rate_index
        FROM bqx.m1_{pair}
        WHERE EXTRACT(YEAR FROM time) = {year}
          AND EXTRACT(MONTH FROM time) = {month}
        ORDER BY time;
        """

        df_pair = pd.read_sql(pair_query, conn)

        if df_pair.empty:
            logger.warning(f"{pair.upper()} {year_month}: No data found")
            conn.close()
            return (pair, year_month, True, 0, "No data")

        df_pair['ts_utc'] = pd.to_datetime(df_pair['ts_utc'], utc=True)
        df_pair.set_index('ts_utc', inplace=True)

        # Find all triangular paths for this pair
        triangular_paths = find_triangular_paths(pair)

        if not triangular_paths:
            logger.warning(f"{pair.upper()} {year_month}: No valid triangular paths found")
            conn.close()
            return (pair, year_month, True, 0, "No triangular paths")

        logger.info(f"{pair.upper()} {year_month}: Found {len(triangular_paths)} triangular paths")

        # Load rate_index for all pairs needed in triangular paths
        all_pairs_needed = set()
        for path in triangular_paths:
            all_pairs_needed.update(path['pairs'])

        all_rates = {}
        for other_pair in all_pairs_needed:
            try:
                query = f"""
                SELECT time AS ts_utc, rate_index
                FROM bqx.m1_{other_pair}
                WHERE EXTRACT(YEAR FROM time) = {year}
                  AND EXTRACT(MONTH FROM time) = {month}
                ORDER BY time;
                """
                df_other = pd.read_sql(query, conn)
                df_other['ts_utc'] = pd.to_datetime(df_other['ts_utc'], utc=True)
                df_other.set_index('ts_utc', inplace=True)
                all_rates[other_pair] = df_other['rate_index']
            except Exception as e:
                logger.warning(f"Could not load {other_pair}: {e}")

        logger.info(f"{pair.upper()} {year_month}: Loaded {len(df_pair):,} rows, computing arbitrage...")

        # Calculate arbitrage features for each timestamp
        results = []
        ARBITRAGE_THRESHOLD = 0.5  # 0.5% profit threshold

        for ts in df_pair.index:
            # For each triangular path, calculate arbitrage
            max_profit = 0.0
            best_direction = 0

            for path in triangular_paths:
                pair_1, pair_2, pair_3 = path['pairs']
                dir_1, dir_2, dir_3 = path['directions']

                # Check if all rates available at this timestamp
                if (pair_1 in all_rates and ts in all_rates[pair_1].index and
                    pair_2 in all_rates and ts in all_rates[pair_2].index and
                    pair_3 in all_rates and ts in all_rates[pair_3].index):

                    rate_1 = all_rates[pair_1].at[ts]
                    rate_2 = all_rates[pair_2].at[ts]
                    rate_3 = all_rates[pair_3].at[ts]

                    if pd.notna(rate_1) and pd.notna(rate_2) and pd.notna(rate_3):
                        # Calculate clockwise profit
                        profit_cw = calculate_triangular_arbitrage(
                            rate_1, rate_2, rate_3,
                            dir_1, dir_2, dir_3,
                            transaction_cost_pct=0.3
                        )

                        # Calculate counter-clockwise profit (reverse all directions)
                        profit_ccw = calculate_triangular_arbitrage(
                            rate_3, rate_2, rate_1,
                            -dir_3, -dir_2, -dir_1,
                            transaction_cost_pct=0.3
                        )

                        # Track best opportunity
                        if profit_cw > max_profit:
                            max_profit = profit_cw
                            best_direction = 1  # Clockwise

                        if profit_ccw > max_profit:
                            max_profit = profit_ccw
                            best_direction = -1  # Counter-clockwise

            # Determine if arbitrage opportunity exists
            arbitrage_exists = max_profit > ARBITRAGE_THRESHOLD

            results.append({
                'ts_utc': ts,
                'arbitrage_profit_pct': max_profit if arbitrage_exists else 0.0,
                'arbitrage_opportunity': arbitrage_exists,
                'arbitrage_direction': best_direction if arbitrage_exists else 0,
                'arbitrage_max_profit': max_profit
            })

        if not results:
            logger.warning(f"{pair.upper()} {year_month}: No valid results")
            conn.close()
            return (pair, year_month, True, 0, "No valid results")

        # Insert into arbitrage table
        partition_name = f"arbitrage_{pair}_{year_month}"
        cursor.execute(f"DELETE FROM bqx.{partition_name}")

        for row in results:
            cursor.execute(f"""
                INSERT INTO bqx.{partition_name}
                (ts_utc, pair, arbitrage_profit_pct, arbitrage_opportunity,
                 arbitrage_direction, arbitrage_max_profit, year_month)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (row['ts_utc'], pair, row['arbitrage_profit_pct'], row['arbitrage_opportunity'],
                  row['arbitrage_direction'], row['arbitrage_max_profit'], year_month))

        conn.commit()

        # Calculate statistics
        opportunities = sum(1 for r in results if r['arbitrage_opportunity'])

        conn.close()

        elapsed = time.time() - start_time
        logger.info(f"✅ {pair.upper()} {year_month}: Complete! {len(results):,} rows, "
                   f"{opportunities} arbitrage opportunities, {elapsed:.1f}s")

        return (pair, year_month, True, len(results), None)

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        logger.error(f"❌ {pair.upper()} {year_month}: Failed after {elapsed:.1f}s - {error_msg}")
        return (pair, year_month, False, 0, error_msg)


def main():
    """Main execution: Populate arbitrage features for all pairs and months."""
    parser = argparse.ArgumentParser(description='Populate arbitrage features for BQX ML')
    parser.add_argument('--max-workers', type=int, default=8, help='Maximum number of parallel workers')
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("STAGE 2.4: ARBITRAGE DETECTION")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Pairs: {len(PAIRS)}")
    logger.info(f"Currencies: {CURRENCIES}")
    logger.info(f"Features: 4 per partition")
    logger.info(f"Max Workers: {args.max_workers}")
    logger.info("")

    # Generate all tasks
    tasks = []
    for pair in PAIRS:
        for year in [2024, 2025]:
            for month in range(1, 13):
                if (year == 2024 and month >= 7) or (year == 2025 and month <= 6):
                    year_month = f"{year}_{month:02d}"
                    tasks.append((pair, year_month))

    logger.info(f"Total tasks: {len(tasks)}")
    logger.info("")

    start_time = time.time()
    results = {'success': 0, 'failed': 0, 'total_rows': 0}

    with ProcessPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {executor.submit(populate_arbitrage_for_pair, pair, ym): (pair, ym)
                   for pair, ym in tasks}

        for future in as_completed(futures):
            pair, ym = futures[future]
            try:
                pair_name, year_month, success, row_count, error_msg = future.result()

                if success:
                    results['success'] += 1
                    results['total_rows'] += row_count
                    logger.info(f"Progress: {results['success']}/{len(tasks)} partitions complete")
                else:
                    results['failed'] += 1

            except Exception as e:
                logger.error(f"Unexpected error for {pair} {ym}: {e}")
                results['failed'] += 1

    elapsed = time.time() - start_time

    logger.info("")
    logger.info("=" * 80)
    logger.info("ARBITRAGE DETECTION COMPLETE")
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
