#!/usr/bin/env python3
"""
Track 3: Feature Extraction from Database
Extract existing populated features into Parquet files for MVP pipeline.

Features extracted (using actual database schema):
- bollinger_rate: 20 features
- statistics_rate: 23 features
- volume_features: 10 features
- spread_features: 20 features
- time_features: 8 features
Total: 81 features per pair

Output: 28 Parquet files (one per pair) in data/extracted/
"""

import psycopg2
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

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

# Output directory
OUTPUT_DIR = Path('/home/ubuntu/bqx-ml/data/extracted')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/logs/track3/extract.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def extract_features_for_pair(pair):
    """
    Extract all 159 features for a single pair.

    Args:
        pair: Currency pair (e.g., 'eurusd')

    Returns:
        tuple: (pair, success, row_count, error_message)
    """
    start_time = time.time()

    try:
        logger.info(f"Starting extraction for {pair.upper()}")

        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)

        # Build query to join all 5 feature families (using actual column names)
        query = f"""
        SELECT
            b.ts_utc,

            -- Bollinger features (20 available)
            b.bollinger_upper_20,
            b.bollinger_middle_20,
            b.bollinger_lower_20,
            b.bollinger_width_20,
            b.bollinger_percent_b,
            b.bb_upper_30,
            b.bb_middle_30,
            b.bb_lower_30,
            b.bb_width_30,
            b.bb_upper_60,
            b.bb_middle_60,
            b.bb_lower_60,
            b.bb_width_60,
            b.bb_percent_b_60,
            b.bb_upper_120,
            b.bb_middle_120,
            b.bb_lower_120,
            b.bb_width_120,
            b.bb_slope_20,
            b.bb_slope_60,

            -- Statistics features (selecting key columns)
            s.skewness_60min,
            s.kurtosis_60min,
            s.median_absolute_deviation_60min,
            s.entropy_60min,
            s.autocorrelation_lag1,
            s.mean_5min,
            s.mean_15min,
            s.mean_30min,
            s.mean_60min,
            s.mean_120min,
            s.std_5min,
            s.std_15min,
            s.std_30min,
            s.std_60min,
            s.std_120min,
            s.skew_5min,
            s.skew_15min,
            s.skew_30min,
            s.skew_120min,
            s.kurt_5min,
            s.kurt_15min,
            s.kurt_30min,
            s.kurt_120min,

            -- Volume features (11 available)
            v.w15_volume_ratio,
            v.w30_volume_ratio,
            v.w60_volume_ratio,
            v.volume_spike,
            v.volume_trend_slope,
            v.cumulative_volume_60min,
            v.volume_weighted_return,
            v.volume_price_correlation_60min,
            v.relative_volume_position,
            v.volume_volatility_60min,

            -- Spread features (20 available)
            sp.spread_mean_60min,
            sp.spread_volatility_60min,
            sp.spread_pct_of_rate,
            sp.spread_trend_slope,
            sp.spread_spike,
            sp.bid_ask_imbalance,
            sp.effective_spread,
            sp.quoted_spread,
            sp.realized_spread,
            sp.price_impact,
            sp.roll_cost,
            sp.bid_depth,
            sp.ask_depth,
            sp.depth_imbalance,
            sp.spread_range_60min,
            sp.spread_percentile_60min,
            sp.mid_price_volatility,
            sp.tick_direction,
            sp.tick_rule,
            sp.order_flow_toxicity,

            -- Time features (8 available)
            t.hour_sin,
            t.hour_cos,
            t.day_of_week_sin,
            t.day_of_week_cos,
            t.session_overlap,
            t.is_weekend_approach,
            t.minutes_since_market_open,
            t.trading_session

        FROM bqx.bollinger_rate_{pair} b
        INNER JOIN bqx.statistics_rate_{pair} s ON b.ts_utc = s.ts_utc
        INNER JOIN bqx.volume_features_{pair} v ON b.ts_utc = v.ts_utc
        INNER JOIN bqx.spread_features_{pair} sp ON b.ts_utc = sp.ts_utc
        INNER JOIN bqx.time_features_{pair} t ON b.ts_utc = t.ts_utc
        ORDER BY b.ts_utc;
        """

        # Execute query and load into DataFrame
        logger.info(f"{pair.upper()}: Executing extraction query...")
        df = pd.read_sql_query(query, conn)

        conn.close()

        # Validate data
        if df.empty:
            raise ValueError(f"No data extracted for {pair}")

        row_count = len(df)
        col_count = len(df.columns)

        logger.info(f"{pair.upper()}: Extracted {row_count:,} rows, {col_count} columns")

        # Check for missing values
        missing_pct = (df.isnull().sum().sum() / (row_count * col_count)) * 100
        logger.info(f"{pair.upper()}: Missing values: {missing_pct:.2f}%")

        # Save to Parquet
        output_file = OUTPUT_DIR / f"{pair}.parquet"
        df.to_parquet(output_file, compression='snappy', index=False)

        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        elapsed = time.time() - start_time

        logger.info(f"✅ {pair.upper()}: Complete! {row_count:,} rows, {file_size_mb:.1f} MB, {elapsed:.1f}s")

        return (pair, True, row_count, None)

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        logger.error(f"❌ {pair.upper()}: Failed after {elapsed:.1f}s - {error_msg}")
        return (pair, False, 0, error_msg)


def main():
    """
    Main execution: Extract features for all 28 pairs in parallel.
    """
    logger.info("=" * 80)
    logger.info("TRACK 3: FEATURE EXTRACTION FROM DATABASE")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Extracting 81 features for {len(PAIRS)} pairs")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info("")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Track results
    start_time = time.time()
    results = {
        'success': [],
        'failed': [],
        'total_rows': 0
    }

    # Process pairs in parallel (2 workers to avoid overloading database)
    max_workers = 2
    logger.info(f"Processing {len(PAIRS)} pairs with {max_workers} parallel workers...")
    logger.info("")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = {executor.submit(extract_features_for_pair, pair): pair for pair in PAIRS}

        # Process results as they complete
        for future in as_completed(futures):
            pair = futures[future]
            try:
                pair_name, success, row_count, error_msg = future.result()

                if success:
                    results['success'].append(pair_name)
                    results['total_rows'] += row_count
                else:
                    results['failed'].append((pair_name, error_msg))

            except Exception as e:
                logger.error(f"Unexpected error processing {pair}: {e}")
                results['failed'].append((pair, str(e)))

    # Summary
    elapsed = time.time() - start_time

    logger.info("")
    logger.info("=" * 80)
    logger.info("EXTRACTION COMPLETE")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Duration: {elapsed/60:.1f} minutes")
    logger.info(f"Successful: {len(results['success'])}/{len(PAIRS)} pairs")
    logger.info(f"Failed: {len(results['failed'])}/{len(PAIRS)} pairs")
    logger.info(f"Total rows extracted: {results['total_rows']:,}")
    logger.info("")

    if results['success']:
        logger.info("✅ Successful extractions:")
        for pair in sorted(results['success']):
            logger.info(f"   {pair.upper()}")

    if results['failed']:
        logger.info("")
        logger.info("❌ Failed extractions:")
        for pair, error in results['failed']:
            logger.info(f"   {pair.upper()}: {error}")

    logger.info("")
    logger.info("=" * 80)
    logger.info(f"Output files: {OUTPUT_DIR}/*.parquet")
    logger.info("=" * 80)

    # Exit code
    if results['failed']:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
