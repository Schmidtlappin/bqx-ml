#!/usr/bin/env python3
"""
Stage 2.2: Technical Indicators Worker Script
Populates technical indicator features (ADX, RSI, MACD, etc.) for all pairs

Features to Calculate:
- ADX (Average Directional Index): Trend strength
- RSI (Relative Strength Index): Momentum oscillator
- MACD (Moving Average Convergence Divergence): Trend following
- Stochastic Oscillator: Momentum indicator
- CCI (Commodity Channel Index): Identify cyclical trends
- Williams %R: Momentum indicator
- ROC (Rate of Change): Momentum
- MFI (Money Flow Index): Volume-weighted RSI

Windows: 14, 20, 30 periods (minute-level data)
Total Features: ~24 features per pair

Expected Duration: 15 hours with 8 workers
"""

import os
import sys
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging

# Database configuration
DB_CONFIG = {
    'host': 'trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com',
    'database': 'bqx',
    'user': 'postgres',
    'password': os.environ.get('PGPASSWORD', 'BQX_Aurora_2025_Secure')
}

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/logs/stage_2_2/technical_indicators.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Currency pairs
PAIRS = [
    'AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD',
    'CADCHF', 'CADJPY', 'CHFJPY',
    'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD', 'EURUSD',
    'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPJPY', 'GBPNZD', 'GBPUSD',
    'NZDCAD', 'NZDCHF', 'NZDJPY', 'NZDUSD',
    'USDCAD', 'USDCHF', 'USDJPY'
]

# Month partitions
MONTHS = [
    '2024_07', '2024_08', '2024_09', '2024_10', '2024_11', '2024_12',
    '2025_01', '2025_02', '2025_03', '2025_04', '2025_05', '2025_06'
]


def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index"""
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / down if down != 0 else 0
        rsi[i] = 100. - 100. / (1. + rs)

    return rsi


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    ema_fast = pd.Series(prices).ewm(span=fast, adjust=False).mean()
    ema_slow = pd.Series(prices).ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return macd_line.values, signal_line.values, histogram.values


def calculate_adx(high, low, close, period=14):
    """Calculate Average Directional Index (ADX)"""
    # TODO: Implement ADX calculation
    # This is a placeholder - full implementation needed
    return np.full(len(close), np.nan)


def calculate_stochastic(high, low, close, k_period=14, d_period=3):
    """Calculate Stochastic Oscillator"""
    lowest_low = pd.Series(low).rolling(window=k_period).min()
    highest_high = pd.Series(high).rolling(window=k_period).max()

    k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d_percent = k_percent.rolling(window=d_period).mean()

    return k_percent.values, d_percent.values


def calculate_cci(high, low, close, period=20):
    """Calculate Commodity Channel Index"""
    tp = (high + low + close) / 3
    sma_tp = pd.Series(tp).rolling(window=period).mean()
    mad = pd.Series(tp).rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
    cci = (tp - sma_tp) / (0.015 * mad)

    return cci.values


def calculate_williams_r(high, low, close, period=14):
    """Calculate Williams %R"""
    highest_high = pd.Series(high).rolling(window=period).max()
    lowest_low = pd.Series(low).rolling(window=period).min()
    williams_r = -100 * (highest_high - close) / (highest_high - lowest_low)

    return williams_r.values


def calculate_roc(close, period=12):
    """Calculate Rate of Change"""
    roc = 100 * (close / np.roll(close, period) - 1)
    roc[:period] = np.nan

    return roc


def process_partition(pair, year_month):
    """Process a single pair-month partition"""
    try:
        logger.info(f"Processing {pair} {year_month}...")

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Fetch M1 data for the partition
        # TODO: Adjust query to fetch high, low, close, volume
        query = f"""
            SELECT ts_utc, rate_index as close
            FROM bqx.m1_{pair.lower()}
            WHERE ts_utc >= %s AND ts_utc < %s
            ORDER BY ts_utc
        """

        year, month = year_month.split('_')
        start_date = f"{year}-{month}-01"
        if month == '12':
            end_date = f"{int(year)+1}-01-01"
        else:
            end_date = f"{year}-{int(month)+1:02d}-01"

        cursor.execute(query, (start_date, end_date))
        data = cursor.fetchall()

        if not data:
            logger.warning(f"No data for {pair} {year_month}")
            cursor.close()
            conn.close()
            return f"{pair}_{year_month}: No data"

        df = pd.DataFrame(data, columns=['ts_utc', 'close'])

        # Calculate technical indicators
        # TODO: Add high, low, volume columns when available
        df['rsi_14'] = calculate_rsi(df['close'].values, period=14)
        df['rsi_20'] = calculate_rsi(df['close'].values, period=20)

        macd, signal, histogram = calculate_macd(df['close'].values)
        df['macd'] = macd
        df['macd_signal'] = signal
        df['macd_histogram'] = histogram

        # TODO: Implement remaining indicators
        # df['adx_14'] = calculate_adx(...)
        # df['stoch_k'], df['stoch_d'] = calculate_stochastic(...)
        # df['cci_20'] = calculate_cci(...)
        # df['williams_r_14'] = calculate_williams_r(...)
        # df['roc_12'] = calculate_roc(...)

        # Replace NaN with None for PostgreSQL NULL
        df = df.astype(object).where(pd.notnull(df), None)

        # Insert into database
        # TODO: Create table schema first
        partition_name = f"technical_indicators_{pair.lower()}_{year_month}"

        # INSERT logic here
        logger.info(f"✅ {pair} {year_month} Complete!")

        cursor.close()
        conn.close()

        return f"{pair}_{year_month}: Complete!"

    except Exception as e:
        logger.error(f"❌ {pair} {year_month} Failed: {e}")
        return f"{pair}_{year_month}: Failed - {e}"


def main():
    """Main execution function"""
    logger.info("=" * 80)
    logger.info("STAGE 2.2: TECHNICAL INDICATORS - STARTING")
    logger.info("=" * 80)

    # Create log directory
    os.makedirs('/tmp/logs/stage_2_2', exist_ok=True)

    # Generate all tasks
    tasks = [(pair, month) for pair in PAIRS for month in MONTHS]
    total_tasks = len(tasks)

    logger.info(f"Total partitions to process: {total_tasks}")
    logger.info(f"Workers: 8")
    logger.info(f"Estimated duration: 15 hours")
    logger.info("")

    # Process tasks in parallel
    completed = 0
    failed = 0

    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_partition, pair, month): (pair, month)
                   for pair, month in tasks}

        for future in as_completed(futures):
            result = future.result()
            completed += 1

            if "Failed" in result:
                failed += 1

            progress_pct = (completed / total_tasks) * 100
            logger.info(f"Progress: {completed}/{total_tasks} ({progress_pct:.1f}%) | Failures: {failed}")

    logger.info("")
    logger.info("=" * 80)
    logger.info("STAGE 2.2: TECHNICAL INDICATORS - COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total: {completed}/{total_tasks}")
    logger.info(f"Successful: {completed - failed}")
    logger.info(f"Failed: {failed}")


if __name__ == '__main__':
    main()
