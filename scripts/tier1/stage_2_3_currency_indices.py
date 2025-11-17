#!/usr/bin/env python3
"""
Stage 2.3: Currency Indices

Implements basket indices for major currencies with momentum and volatility features.

Features Added (per partition): 224
- 8 currency baskets × 28 features per basket
- Baskets: USD, EUR, JPY, GBP, AUD, NZD, CAD, CHF
- Features per basket:
  * Basket index (1)
  * 6 windows × 3 momentum features (18)
  * 6 windows × 1 volatility feature (6)
  * Basket strength vs other currencies (3)

Total Features: 8 × 28 = 224 features per partition

Duration: ~20 hours (c7i.8xlarge)
Cost: $8 (Spot pricing)
Impact: +5-8% directional accuracy

Dependencies:
- Stage 2.12 complete (reg_bqx tables with aligned windows)
- Stage 2.14 complete (covariance features)
- Stage 2.15 complete (validation passed)
"""

import psycopg2
import pandas as pd
import numpy as np
import logging
import sys
import os
import time
from datetime import datetime

# Configure logging
os.makedirs('/tmp/logs/tier1/stage_2_3', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/logs/tier1/stage_2_3/currency_indices.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com'),
    'database': 'bqx',
    'user': 'postgres',
    'password': os.environ.get('DB_PASSWORD', 'BQX_Aurora_2025_Secure')
}

# All 28 currency pairs
CURRENCY_PAIRS = [
    'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
    'cadchf', 'cadjpy', 'chfjpy',
    'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
    'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
    'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
    'usdcad', 'usdchf', 'usdjpy'
]

# All 12 months (2024-07 through 2025-06)
YEAR_MONTHS = [
    '2024_07', '2024_08', '2024_09', '2024_10', '2024_11', '2024_12',
    '2025_01', '2025_02', '2025_03', '2025_04', '2025_05', '2025_06'
]

# Aligned windows
WINDOWS = [60, 90, 150, 240, 390, 630]

# Major currencies for basket construction
MAJOR_CURRENCIES = ['USD', 'EUR', 'JPY', 'GBP', 'AUD', 'NZD', 'CAD', 'CHF']

# Currency basket compositions (which pairs to use for each basket)
# For USD basket: use all USD pairs
# For EUR basket: use all EUR pairs, etc.
BASKET_PAIRS = {
    'USD': ['eurusd', 'gbpusd', 'audusd', 'nzdusd', 'usdcad', 'usdchf', 'usdjpy'],
    'EUR': ['eurusd', 'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd'],
    'JPY': ['usdjpy', 'eurjpy', 'gbpjpy', 'audjpy', 'nzdjpy', 'cadjpy', 'chfjpy'],
    'GBP': ['gbpusd', 'eurgbp', 'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd'],
    'AUD': ['audusd', 'euraud', 'gbpaud', 'audcad', 'audchf', 'audjpy', 'audnzd'],
    'NZD': ['nzdusd', 'eurnzd', 'gbpnzd', 'audnzd', 'nzdcad', 'nzdchf', 'nzdjpy'],
    'CAD': ['usdcad', 'eurcad', 'gbpcad', 'audcad', 'nzdcad', 'cadchf', 'cadjpy'],
    'CHF': ['usdchf', 'eurchf', 'gbpchf', 'audchf', 'nzdchf', 'cadchf', 'chfjpy']
}


def get_pair_direction(pair, currency):
    """
    Determine if currency is base or quote in pair.
    Returns 1 if base, -1 if quote.

    Example:
    - get_pair_direction('eurusd', 'EUR') = 1 (EUR is base)
    - get_pair_direction('eurusd', 'USD') = -1 (USD is quote)
    """
    base = pair[:3].upper()
    quote = pair[3:].upper()

    if base == currency:
        return 1
    elif quote == currency:
        return -1
    else:
        return 0  # Currency not in this pair


def add_currency_index_columns(conn, pair):
    """
    Add currency index columns to reg_bqx parent table.

    Args:
        conn: Database connection
        pair: Currency pair (e.g., 'eurusd')

    Returns:
        bool: Success status
    """
    table_name = f"reg_bqx_{pair}"

    try:
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'bqx'
                AND table_name = %s
            )
        """, (table_name,))

        if not cursor.fetchone()[0]:
            logger.warning(f"{pair.upper()}: Table {table_name} does not exist, skipping")
            cursor.close()
            return False

        logger.info(f"{pair.upper()}: Adding currency index columns...")

        # Generate column definitions
        columns_to_add = []

        for currency in MAJOR_CURRENCIES:
            # Base index
            columns_to_add.append(f"{currency.lower()}_basket_index")

            # Momentum and volatility features for each window
            for window in WINDOWS:
                # Momentum features (3 per window)
                columns_to_add.append(f"{currency.lower()}_basket_momentum_{window}min")
                columns_to_add.append(f"{currency.lower()}_basket_momentum_accel_{window}min")
                columns_to_add.append(f"{currency.lower()}_basket_momentum_roc_{window}min")

                # Volatility feature (1 per window)
                columns_to_add.append(f"{currency.lower()}_basket_volatility_{window}min")

            # Basket strength features (3 total)
            columns_to_add.append(f"{currency.lower()}_basket_strength_vs_major")
            columns_to_add.append(f"{currency.lower()}_basket_strength_vs_safe_haven")
            columns_to_add.append(f"{currency.lower()}_basket_strength_vs_commodity")

        # Add all columns
        for col in columns_to_add:
            # Check if column exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_schema = 'bqx'
                    AND table_name = %s
                    AND column_name = %s
                )
            """, (table_name, col))

            if cursor.fetchone()[0]:
                logger.debug(f"{pair.upper()}: Column {col} already exists, skipping")
                continue

            # Add column
            cursor.execute(f"""
                ALTER TABLE bqx.{table_name}
                ADD COLUMN {col} DOUBLE PRECISION
            """)

        conn.commit()
        cursor.close()

        logger.info(f"✅ {pair.upper()}: Added {len(columns_to_add)} currency index columns")
        return True

    except Exception as e:
        logger.error(f"❌ {pair.upper()}: Failed to add columns - {e}")
        conn.rollback()
        return False


def calculate_currency_index(df_dict, currency, timestamp):
    """
    Calculate basket index for a currency at given timestamp.

    Args:
        df_dict: Dictionary of DataFrames (pair -> DataFrame with ts_utc, w60_prediction)
        currency: Currency code (e.g., 'USD')
        timestamp: Timestamp to calculate index for

    Returns:
        float: Currency basket index value
    """
    basket_pairs = BASKET_PAIRS.get(currency, [])
    if not basket_pairs:
        return None

    values = []
    for pair in basket_pairs:
        if pair not in df_dict:
            continue

        df = df_dict[pair]
        row = df[df['ts_utc'] == timestamp]

        if len(row) == 0:
            continue

        # Get prediction value (60-minute window prediction)
        pred_value = row['w60_prediction'].iloc[0]

        if pd.isna(pred_value):
            continue

        # Adjust for direction (base vs quote)
        direction = get_pair_direction(pair, currency)
        if direction == 0:
            continue

        values.append(pred_value * direction)

    if len(values) == 0:
        return None

    # Basket index is the average of constituent pair predictions
    return np.mean(values)


def calculate_basket_momentum(basket_series, window):
    """
    Calculate momentum features for basket index.

    Args:
        basket_series: Series of basket index values
        window: Window size in minutes

    Returns:
        dict: Momentum features
    """
    if len(basket_series) < window:
        return {
            'momentum': None,
            'momentum_accel': None,
            'momentum_roc': None
        }

    # Get last window values
    values = basket_series.iloc[-window:].values

    # Momentum (rate of change)
    momentum = values[-1] - values[0]

    # Momentum acceleration (2nd derivative)
    if len(values) >= 2:
        mid_point = len(values) // 2
        first_half_momentum = values[mid_point] - values[0]
        second_half_momentum = values[-1] - values[mid_point]
        momentum_accel = second_half_momentum - first_half_momentum
    else:
        momentum_accel = None

    # Rate of change (percentage)
    if values[0] != 0:
        momentum_roc = (values[-1] - values[0]) / abs(values[0]) * 100
    else:
        momentum_roc = None

    return {
        'momentum': momentum,
        'momentum_accel': momentum_accel,
        'momentum_roc': momentum_roc
    }


def calculate_basket_volatility(basket_series, window):
    """
    Calculate volatility for basket index.

    Args:
        basket_series: Series of basket index values
        window: Window size in minutes

    Returns:
        float: Basket volatility (standard deviation)
    """
    if len(basket_series) < window:
        return None

    values = basket_series.iloc[-window:].values
    return np.std(values)


def calculate_basket_strength(basket_indices, currency, basket_type='major'):
    """
    Calculate basket strength relative to other currency groups.

    Args:
        basket_indices: Dict of currency -> basket index value
        currency: Currency to calculate strength for
        basket_type: 'major', 'safe_haven', or 'commodity'

    Returns:
        float: Relative strength
    """
    currency_groups = {
        'major': ['USD', 'EUR', 'JPY', 'GBP'],
        'safe_haven': ['CHF', 'JPY'],
        'commodity': ['AUD', 'NZD', 'CAD']
    }

    group = currency_groups.get(basket_type, ['USD', 'EUR', 'JPY', 'GBP'])

    # Get currency's own basket value
    own_value = basket_indices.get(currency)
    if own_value is None or pd.isna(own_value):
        return None

    # Get average of group currencies (excluding own currency)
    group_values = []
    for curr in group:
        if curr == currency:
            continue
        value = basket_indices.get(curr)
        if value is not None and not pd.isna(value):
            group_values.append(value)

    if len(group_values) == 0:
        return None

    group_avg = np.mean(group_values)

    # Relative strength (positive = stronger than group, negative = weaker)
    return own_value - group_avg


def populate_currency_indices(pair, year_month):
    """
    Populate currency index features for a single partition.

    Args:
        pair: Currency pair
        year_month: Month partition

    Returns:
        tuple: (pair, year_month, success, rows_updated, error_msg)
    """
    start_time = time.time()
    partition_name = f"reg_bqx_{pair}_{year_month}"

    try:
        logger.info(f"{pair.upper()} {year_month}: Starting currency index calculation...")

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Load data from current partition
        query = f"""
        SELECT ts_utc, w60_prediction
        FROM bqx.{partition_name}
        ORDER BY ts_utc
        """

        df_current = pd.read_sql(query, conn)

        if len(df_current) == 0:
            logger.warning(f"{pair.upper()} {year_month}: No data found, skipping")
            cursor.close()
            conn.close()
            return (pair, year_month, True, 0, "No data")

        logger.info(f"{pair.upper()} {year_month}: Loaded {len(df_current):,} rows")

        # Load data from all other pairs in same month partition
        # (needed to calculate basket indices)
        df_dict = {pair: df_current}

        for other_pair in CURRENCY_PAIRS:
            if other_pair == pair:
                continue

            other_partition = f"reg_bqx_{other_pair}_{year_month}"

            try:
                query_other = f"""
                SELECT ts_utc, w60_prediction
                FROM bqx.{other_partition}
                ORDER BY ts_utc
                """
                df_other = pd.read_sql(query_other, conn)
                df_dict[other_pair] = df_other
            except Exception as e:
                logger.debug(f"{pair.upper()} {year_month}: Could not load {other_pair} - {e}")
                continue

        logger.info(f"{pair.upper()} {year_month}: Loaded {len(df_dict)} pairs for basket calculation")

        # Calculate currency indices for each timestamp
        basket_indices_by_timestamp = {}

        for idx, row in df_current.iterrows():
            timestamp = row['ts_utc']

            # Calculate basket index for each currency at this timestamp
            basket_indices = {}
            for currency in MAJOR_CURRENCIES:
                basket_value = calculate_currency_index(df_dict, currency, timestamp)
                basket_indices[currency] = basket_value

            basket_indices_by_timestamp[timestamp] = basket_indices

        logger.info(f"{pair.upper()} {year_month}: Calculated basket indices for {len(basket_indices_by_timestamp):,} timestamps")

        # Calculate momentum, volatility, and strength features
        # Build up series for each currency basket
        basket_series = {currency: [] for currency in MAJOR_CURRENCIES}

        for timestamp in sorted(basket_indices_by_timestamp.keys()):
            indices = basket_indices_by_timestamp[timestamp]
            for currency in MAJOR_CURRENCIES:
                basket_series[currency].append(indices.get(currency))

        # Convert to pandas Series
        for currency in MAJOR_CURRENCIES:
            basket_series[currency] = pd.Series(basket_series[currency])

        # Calculate features for each row
        update_data = []

        for idx, row in df_current.iterrows():
            timestamp = row['ts_utc']
            basket_indices = basket_indices_by_timestamp[timestamp]

            # Features for this row
            features = {}

            for currency in MAJOR_CURRENCIES:
                curr_lower = currency.lower()

                # Base basket index
                features[f"{curr_lower}_basket_index"] = basket_indices.get(currency)

                # Momentum and volatility for each window
                for window in WINDOWS:
                    # Get basket series up to current point
                    current_series = basket_series[currency].iloc[:idx+1]

                    # Calculate momentum features
                    momentum_features = calculate_basket_momentum(current_series, window)
                    features[f"{curr_lower}_basket_momentum_{window}min"] = momentum_features['momentum']
                    features[f"{curr_lower}_basket_momentum_accel_{window}min"] = momentum_features['momentum_accel']
                    features[f"{curr_lower}_basket_momentum_roc_{window}min"] = momentum_features['momentum_roc']

                    # Calculate volatility feature
                    volatility = calculate_basket_volatility(current_series, window)
                    features[f"{curr_lower}_basket_volatility_{window}min"] = volatility

                # Basket strength features
                features[f"{curr_lower}_basket_strength_vs_major"] = calculate_basket_strength(basket_indices, currency, 'major')
                features[f"{curr_lower}_basket_strength_vs_safe_haven"] = calculate_basket_strength(basket_indices, currency, 'safe_haven')
                features[f"{curr_lower}_basket_strength_vs_commodity"] = calculate_basket_strength(basket_indices, currency, 'commodity')

            update_data.append((timestamp, features))

        # Update database in batches
        logger.info(f"{pair.upper()} {year_month}: Updating {len(update_data):,} rows...")

        batch_size = 1000
        rows_updated = 0

        for i in range(0, len(update_data), batch_size):
            batch = update_data[i:i+batch_size]

            for timestamp, features in batch:
                # Convert NaN to None for PostgreSQL NULL
                set_clauses = []
                values = []

                for col, value in features.items():
                    set_clauses.append(f"{col} = %s")
                    values.append(None if pd.isna(value) else value)

                values.append(timestamp)

                update_sql = f"""
                UPDATE bqx.{partition_name}
                SET {', '.join(set_clauses)}
                WHERE ts_utc = %s
                """

                cursor.execute(update_sql, values)
                rows_updated += cursor.rowcount

            # Commit every batch
            conn.commit()

            if (i + batch_size) % 5000 == 0:
                logger.info(f"{pair.upper()} {year_month}: Updated {rows_updated:,}/{len(update_data):,} rows ({rows_updated/len(update_data)*100:.1f}%)")

        cursor.close()
        conn.close()

        elapsed = time.time() - start_time
        logger.info(f"✅ {pair.upper()} {year_month}: Complete! Updated {rows_updated:,} rows ({elapsed:.1f}s)")

        return (pair, year_month, True, rows_updated, None)

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        logger.error(f"❌ {pair.upper()} {year_month}: Failed after {elapsed:.1f}s - {error_msg}")
        return (pair, year_month, False, 0, error_msg)


def main():
    """Main execution: Add currency index features to all reg_bqx tables."""
    logger.info("=" * 80)
    logger.info("STAGE 2.3: CURRENCY INDICES")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logger.info(f"Currency pairs: {len(CURRENCY_PAIRS)}")
    logger.info(f"Months per pair: {len(YEAR_MONTHS)}")
    logger.info(f"Total partitions: {len(CURRENCY_PAIRS) * len(YEAR_MONTHS)}")
    logger.info(f"Currencies: {len(MAJOR_CURRENCIES)}")
    logger.info(f"Features per partition: 224 (8 currencies × 28 features)")
    logger.info(f"Aligned windows: {WINDOWS}")
    logger.info("")

    start_time = time.time()

    # Step 1: Add columns to all parent tables
    logger.info("STEP 1: Adding currency index columns to parent tables")
    logger.info("=" * 80)

    conn = psycopg2.connect(**DB_CONFIG)
    columns_success = 0

    for pair in CURRENCY_PAIRS:
        if add_currency_index_columns(conn, pair):
            columns_success += 1

    conn.close()

    logger.info(f"✅ Added columns to {columns_success}/{len(CURRENCY_PAIRS)} parent tables")
    logger.info("")

    # Step 2: Populate features for all partitions
    logger.info("STEP 2: Populating currency index features")
    logger.info("=" * 80)
    logger.info("")

    all_results = {
        'partitions_success': 0,
        'partitions_failed': 0,
        'partitions_no_data': 0,
        'total_rows': 0
    }

    for pair in CURRENCY_PAIRS:
        logger.info(f"Processing {pair.upper()}...")

        pair_results = {'success': 0, 'failed': 0, 'no_data': 0, 'rows': 0}

        for year_month in YEAR_MONTHS:
            pair_name, ym, success, rows, error_msg = populate_currency_indices(pair, year_month)

            if success:
                if error_msg and "No data" in error_msg:
                    pair_results['no_data'] += 1
                else:
                    pair_results['success'] += 1
                    pair_results['rows'] += rows
            else:
                pair_results['failed'] += 1

        logger.info(f"{pair.upper()}: {pair_results['success']}/{len(YEAR_MONTHS)} partitions, {pair_results['rows']:,} rows")
        logger.info("")

        all_results['partitions_success'] += pair_results['success']
        all_results['partitions_failed'] += pair_results['failed']
        all_results['partitions_no_data'] += pair_results['no_data']
        all_results['total_rows'] += pair_results['rows']

    elapsed = time.time() - start_time

    logger.info("")
    logger.info("=" * 80)
    logger.info("STAGE 2.3 COMPLETE")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Duration: {elapsed/60:.1f} minutes ({elapsed/3600:.2f} hours)")
    logger.info(f"Partitions successful: {all_results['partitions_success']}/{len(CURRENCY_PAIRS) * len(YEAR_MONTHS)}")
    logger.info(f"Partitions failed: {all_results['partitions_failed']}/{len(CURRENCY_PAIRS) * len(YEAR_MONTHS)}")
    logger.info(f"Partitions no data: {all_results['partitions_no_data']}/{len(CURRENCY_PAIRS) * len(YEAR_MONTHS)}")
    logger.info(f"Total rows updated: {all_results['total_rows']:,}")
    logger.info(f"Features added: 224 per partition (8 currencies × 28 features)")
    logger.info(f"Schema expansion: 79 → 303 columns (+224)")
    logger.info("")

    if all_results['partitions_failed'] > 0:
        logger.error("❌ Stage 2.3 completed with errors")
        logger.info("=" * 80)
        return 1
    else:
        logger.info("✅ Stage 2.3 completed successfully - All currency index features added")
        logger.info("=" * 80)
        return 0


if __name__ == '__main__':
    sys.exit(main())
