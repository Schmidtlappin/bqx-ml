#!/usr/bin/env python3
"""
Technical Indicators Worker (BQX-Centric) - Phase 1.6.7 Rebuild

Computes technical indicators on BQX momentum values instead of rates:
- RSI of BQX = momentum strength of momentum
- MACD of BQX = trend direction of momentum
- Stochastic of BQX = overbought/oversold in momentum space

Data Source: bqx.bqx_{pair} tables (w15_bqx_return as primary series)
Storage: bqx.technical_features_{pair} (truncate and repopulate)
Computation: Standard technical formulas applied to BQX momentum
Estimated Time: 4-6 hours (336 partitions / 8 threads)
"""

import psycopg2
import numpy as np
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

# Database configuration
DB_CONFIG = {
    'host': 'trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com',
    'port': 5432,
    'database': 'bqx',
    'user': 'postgres',
    'password': 'BQX_Aurora_2025_Secure'
}

# 28 currency pairs
CURRENCY_PAIRS = [
    'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
    'cadchf', 'cadjpy', 'chfjpy',
    'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
    'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
    'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
    'usdcad', 'usdchf', 'usdjpy'
]

# Thread-safe counters
progress_lock = threading.Lock()
partitions_completed = 0
total_partitions = len(CURRENCY_PAIRS) * 6  # 6 months (Jul-Dec 2024)

def ema(series, period):
    """Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()

def sma(series, period):
    """Simple Moving Average"""
    return series.rolling(window=period).mean()

def rsi(series, period=14):
    """Relative Strength Index on BQX momentum"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-10)
    return 100 - (100 / (1 + rs))

def macd(series, fast=12, slow=26, signal=9):
    """MACD on BQX momentum"""
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def stochastic(series, period=14, smooth=3):
    """Stochastic Oscillator on BQX momentum"""
    lowest = series.rolling(window=period).min()
    highest = series.rolling(window=period).max()
    stoch_k = 100 * (series - lowest) / (highest - lowest + 1e-10)
    stoch_d = stoch_k.rolling(window=smooth).mean()
    return stoch_k, stoch_d

def cci(series, period=20):
    """Commodity Channel Index on BQX"""
    sma_val = sma(series, period)
    mad = series.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
    return (series - sma_val) / (0.015 * mad + 1e-10)

def williams_r(series, period=14):
    """Williams %R on BQX"""
    highest = series.rolling(window=period).max()
    lowest = series.rolling(window=period).min()
    return -100 * (highest - series) / (highest - lowest + 1e-10)

def roc(series, period=12):
    """Rate of Change on BQX"""
    return ((series - series.shift(period)) / (series.shift(period) + 1e-10)) * 100

def atr_bqx(series, period=14):
    """Average True Range adapted for BQX (volatility of momentum)"""
    # For BQX, use absolute changes as "true range"
    tr = abs(series.diff())
    return tr.rolling(window=period).mean()

def bollinger_bands(series, period=20, std_dev=2):
    """Bollinger Bands on BQX"""
    middle = sma(series, period)
    std = series.rolling(window=period).std()
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)
    return upper, middle, lower

def compute_bqx_technical_indicators(df):
    """
    Compute technical indicators on BQX momentum values

    Args:
        df: DataFrame with columns [ts_utc, w15_bqx_return, w30_bqx_return, w45_bqx_return, w60_bqx_return, w75_bqx_return]

    Returns:
        DataFrame with 45 technical indicator columns computed on w15_bqx_return
    """
    # Use w15_bqx_return as primary series (shortest window, most data points)
    bqx_series = df['w15_bqx_return']

    indicators = pd.DataFrame(index=df.index)
    indicators['ts_utc'] = df['ts_utc']

    # Trend Indicators (10) - EMAs and SMAs of BQX momentum
    indicators['ema_10'] = ema(bqx_series, 10)
    indicators['ema_20'] = ema(bqx_series, 20)
    indicators['ema_50'] = ema(bqx_series, 50)
    indicators['ema_100'] = ema(bqx_series, 100)
    indicators['ema_200'] = ema(bqx_series, 200)

    indicators['sma_10'] = sma(bqx_series, 10)
    indicators['sma_20'] = sma(bqx_series, 20)
    indicators['sma_50'] = sma(bqx_series, 50)
    indicators['sma_100'] = sma(bqx_series, 100)
    indicators['sma_200'] = sma(bqx_series, 200)

    # Momentum Indicators (15) - RSI, MACD, Stochastic on BQX
    indicators['rsi_14'] = rsi(bqx_series, 14)
    indicators['rsi_9'] = rsi(bqx_series, 9)
    indicators['rsi_25'] = rsi(bqx_series, 25)

    macd_line, signal_line, histogram = macd(bqx_series)
    indicators['macd'] = macd_line
    indicators['macd_signal'] = signal_line
    indicators['macd_histogram'] = histogram

    stoch_k, stoch_d = stochastic(bqx_series, 14, 3)
    indicators['stoch_k'] = stoch_k
    indicators['stoch_d'] = stoch_d

    indicators['cci'] = cci(bqx_series, 20)
    indicators['williams_r'] = williams_r(bqx_series, 14)

    indicators['roc_12'] = roc(bqx_series, 12)
    indicators['roc_25'] = roc(bqx_series, 25)

    indicators['momentum_10'] = bqx_series - bqx_series.shift(10)
    indicators['momentum_20'] = bqx_series - bqx_series.shift(20)

    # Volatility Indicators (10) - Bollinger Bands, ATR on BQX
    bb_upper, bb_middle, bb_lower = bollinger_bands(bqx_series, 20, 2)
    indicators['bb_upper'] = bb_upper
    indicators['bb_middle'] = bb_middle
    indicators['bb_lower'] = bb_lower
    indicators['bb_width'] = bb_upper - bb_lower
    indicators['bb_pct'] = (bqx_series - bb_lower) / (bb_upper - bb_lower + 1e-10)

    indicators['atr_14'] = atr_bqx(bqx_series, 14)
    indicators['atr_28'] = atr_bqx(bqx_series, 28)

    # Standard deviation (volatility of BQX momentum)
    indicators['std_dev_20'] = bqx_series.rolling(window=20).std()
    indicators['std_dev_50'] = bqx_series.rolling(window=50).std()
    indicators['std_dev_100'] = bqx_series.rolling(window=100).std()

    # Volume Indicators (10) - Use term structure as "volume" proxy
    # Higher BQX variance across windows = higher "activity"
    term_structure_variance = (df['w15_bqx_return'] - df['w60_bqx_return']).abs()

    indicators['obv'] = (np.sign(bqx_series.diff()) * term_structure_variance).fillna(0).cumsum()
    indicators['adl'] = term_structure_variance.cumsum()  # Simplified
    indicators['cmf'] = (term_structure_variance * bqx_series).rolling(window=20).sum() / (term_structure_variance.rolling(window=20).sum() + 1e-10)
    indicators['mfi'] = rsi(bqx_series * term_structure_variance, 14)  # Simplified MFI
    indicators['vwap'] = (bqx_series * term_structure_variance).cumsum() / (term_structure_variance.cumsum() + 1e-10)

    indicators['force_index'] = bqx_series.diff() * term_structure_variance
    indicators['ease_of_movement'] = bqx_series.diff() / (term_structure_variance + 1e-10)
    indicators['volume_oscillator'] = sma(term_structure_variance, 5) - sma(term_structure_variance, 10)
    indicators['volume_roc'] = roc(term_structure_variance, 12)
    indicators['nvi'] = (bqx_series.where(term_structure_variance < term_structure_variance.shift(), 0)).cumsum()

    return indicators

def process_partition(pair, year, month):
    """Process a single partition for one pair-month combination"""
    try:
        partition_start = datetime(year, month, 1)
        if month == 12:
            partition_end = datetime(year + 1, 1, 1)
        else:
            partition_end = datetime(year, month + 1, 1)

        bqx_table = f"bqx_{pair}_y{year}m{month:02d}"
        tech_table = f"technical_features_{pair}_y{year}m{month:02d}"

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Fetch BQX data with extra lookback for indicator computation
        lookback_start = datetime(year, month, 1) if month > 1 else datetime(year - 1, 12, 1)
        if month > 1:
            lookback_start = datetime(year, month - 1, 1) if month > 2 else datetime(year - 1, 12, 1)

        cur.execute(f"""
            SELECT ts_utc, w15_bqx_return, w30_bqx_return, w45_bqx_return, w60_bqx_return, w75_bqx_return
            FROM bqx.{bqx_table}
            WHERE ts_utc >= %s AND ts_utc < %s
            ORDER BY ts_utc;
        """, (lookback_start, partition_end))

        rows = cur.fetchall()

        if len(rows) < 200:  # Need at least 200 data points for indicators
            cur.close()
            conn.close()
            return f"SKIP: {pair}_y{year}m{month:02d} (insufficient data)"

        # Create DataFrame
        df = pd.DataFrame(rows, columns=['ts_utc', 'w15_bqx_return', 'w30_bqx_return', 'w45_bqx_return', 'w60_bqx_return', 'w75_bqx_return'])

        # Compute technical indicators
        indicators = compute_bqx_technical_indicators(df)

        # Filter to partition range only
        indicators = indicators[
            (indicators['ts_utc'] >= partition_start) &
            (indicators['ts_utc'] < partition_end)
        ].copy()

        if len(indicators) == 0:
            cur.close()
            conn.close()
            return f"SKIP: {pair}_y{year}m{month:02d} (no data in range)"

        # Truncate existing data
        cur.execute(f"TRUNCATE TABLE bqx.{tech_table};")

        # Insert indicators
        insert_count = 0
        for _, row in indicators.iterrows():
            try:
                cur.execute(f"""
                    INSERT INTO bqx.{tech_table} (
                        ts_utc,
                        ema_10, ema_20, ema_50, ema_100, ema_200,
                        sma_10, sma_20, sma_50, sma_100, sma_200,
                        rsi_14, rsi_9, rsi_25,
                        macd, macd_signal, macd_histogram,
                        stoch_k, stoch_d,
                        cci, williams_r,
                        roc_12, roc_25,
                        momentum_10, momentum_20,
                        bb_upper, bb_middle, bb_lower, bb_width, bb_pct,
                        atr_14, atr_28,
                        std_dev_20, std_dev_50, std_dev_100,
                        obv, adl, cmf, mfi, vwap,
                        force_index, ease_of_movement, volume_oscillator, volume_roc, nvi
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s
                    ) ON CONFLICT (ts_utc) DO NOTHING;
                """, tuple(row))
                insert_count += 1
            except Exception as e:
                continue

        conn.commit()
        cur.close()
        conn.close()

        global partitions_completed
        with progress_lock:
            partitions_completed += 1
            progress = (partitions_completed / total_partitions) * 100

        return f"SUCCESS: {pair}_y{year}m{month:02d} ({insert_count} rows, {progress:.1f}%)"

    except Exception as e:
        return f"ERROR: {pair}_y{year}m{month:02d} - {str(e)}"

def main():
    """Main execution"""
    print("=" * 80)
    print("BQX ML - Technical Indicators Worker (BQX-Centric Rebuild)")
    print("=" * 80)
    print(f"Start Time: {datetime.now()}")
    print(f"Target: {total_partitions} partitions (28 pairs × 6 months)")
    print(f"Data Source: BQX momentum values (w15_bqx_return)")
    print(f"Features: 45 technical indicators on BQX momentum")
    print("=" * 80)
    print()

    # Generate all partition jobs
    jobs = []
    for pair in CURRENCY_PAIRS:
        for month in range(7, 13):  # Jul-Dec 2024
            jobs.append((pair, 2024, month))

    print(f"Total jobs: {len(jobs)}")
    print()

    # Process partitions in parallel (8 threads)
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_partition, pair, year, month): (pair, year, month)
                   for pair, year, month in jobs}

        for future in as_completed(futures):
            result = future.result()
            print(result)

    total_time = time.time() - start_time
    print()
    print("=" * 80)
    print(f"COMPLETED: {partitions_completed}/{total_partitions} partitions in {total_time/3600:.2f} hours")
    print(f"End Time: {datetime.now()}")
    print("=" * 80)

if __name__ == "__main__":
    main()
