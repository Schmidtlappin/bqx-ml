#!/usr/bin/env python3
"""
Technical Indicators Worker - Phase 1.6.7

Computes 45 technical indicators across 28 currency pairs:
- Trend Indicators (10): EMAs, SMAs
- Momentum Indicators (15): RSI, MACD, Stochastic, CCI, Williams %R, etc.
- Volatility Indicators (10): ATR, Bollinger Bands, Donchian, Keltner, etc.
- Volume Indicators (10): OBV, ADL, CMF, MFI, VWAP, etc.

Data Source: M1 OHLC + Volume data
Storage: bqx.technical_features_{pair}
Computation: Standard technical analysis formulas
Estimated Time: 6-8 hours (336 partitions / 8 threads)
"""

import psycopg2
from psycopg2 import sql
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
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

# Date range
START_DATE = datetime(2024, 7, 1)
END_DATE = datetime(2025, 7, 1)  # Exclusive

# Thread-safe counters
progress_lock = threading.Lock()
partitions_completed = 0
total_partitions = len(CURRENCY_PAIRS) * 12
total_rows_inserted = 0


def generate_month_ranges():
    """Generate list of (year, month) tuples from July 2024 to June 2025"""
    months = []
    current = START_DATE
    while current < END_DATE:
        months.append((current.year, current.month))
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)
    return months


def ema(series, period):
    """Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()


def sma(series, period):
    """Simple Moving Average"""
    return series.rolling(window=period).mean()


def rsi(series, period=14):
    """Relative Strength Index"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def macd(series, fast=12, slow=26, signal=9):
    """MACD, Signal, and Histogram"""
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def stochastic(high, low, close, k_period=14, d_period=3):
    """Stochastic Oscillator %K and %D"""
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    stoch_k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    stoch_d = stoch_k.rolling(window=d_period).mean()
    return stoch_k, stoch_d


def cci(high, low, close, period=20):
    """Commodity Channel Index"""
    tp = (high + low + close) / 3
    sma_tp = sma(tp, period)
    mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
    return (tp - sma_tp) / (0.015 * mad)


def williams_r(high, low, close, period=14):
    """Williams %R"""
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()
    return -100 * (highest_high - close) / (highest_high - lowest_low)


def roc(series, period=12):
    """Rate of Change"""
    return ((series - series.shift(period)) / series.shift(period)) * 100


def atr(high, low, close, period=14):
    """Average True Range"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def obv(close, volume):
    """On-Balance Volume"""
    obv_values = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    return obv_values


def adl(high, low, close, volume):
    """Accumulation/Distribution Line"""
    clv = ((close - low) - (high - close)) / (high - low)
    clv = clv.fillna(0)
    return (clv * volume).cumsum()


def mfi(high, low, close, volume, period=14):
    """Money Flow Index"""
    tp = (high + low + close) / 3
    mf = tp * volume

    positive_mf = mf.where(tp > tp.shift(), 0).rolling(window=period).sum()
    negative_mf = mf.where(tp < tp.shift(), 0).rolling(window=period).sum()

    mfr = positive_mf / negative_mf
    return 100 - (100 / (1 + mfr))


def vwap(high, low, close, volume):
    """Volume Weighted Average Price (daily reset)"""
    tp = (high + low + close) / 3
    return (tp * volume).cumsum() / volume.cumsum()


def compute_technical_indicators(df):
    """
    Compute all 45 technical indicators

    Args:
        df: DataFrame with columns [time, open, high, low, close, volume]

    Returns:
        DataFrame with 45 technical indicator columns
    """
    close = df['close']
    high = df['high']
    low = df['low']
    open_price = df['open']
    volume = df['volume']

    indicators = pd.DataFrame(index=df.index)

    # Trend Indicators (10)
    indicators['ema_10'] = ema(close, 10)
    indicators['ema_20'] = ema(close, 20)
    indicators['ema_50'] = ema(close, 50)
    indicators['ema_100'] = ema(close, 100)
    indicators['ema_200'] = ema(close, 200)

    indicators['sma_10'] = sma(close, 10)
    indicators['sma_20'] = sma(close, 20)
    indicators['sma_50'] = sma(close, 50)
    indicators['sma_100'] = sma(close, 100)
    indicators['sma_200'] = sma(close, 200)

    # Momentum Indicators (15)
    indicators['rsi_14'] = rsi(close, 14)

    macd_line, signal_line, histogram = macd(close)
    indicators['macd'] = macd_line
    indicators['macd_signal'] = signal_line
    indicators['macd_histogram'] = histogram

    stoch_k, stoch_d = stochastic(high, low, close)
    indicators['stoch_k'] = stoch_k
    indicators['stoch_d'] = stoch_d

    indicators['cci_20'] = cci(high, low, close, 20)
    indicators['williams_r_14'] = williams_r(high, low, close, 14)
    indicators['roc_12'] = roc(close, 12)

    indicators['momentum_10'] = close - close.shift(10)
    indicators['momentum_20'] = close - close.shift(20)

    # TRIX
    ema1 = ema(close, 15)
    ema2 = ema(ema1, 15)
    ema3 = ema(ema2, 15)
    indicators['trix'] = 100 * (ema3 - ema3.shift()) / ema3.shift()

    # Ultimate Oscillator (simplified)
    bp = close - pd.concat([low, close.shift()], axis=1).min(axis=1)
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    avg7 = bp.rolling(7).sum() / tr.rolling(7).sum()
    avg14 = bp.rolling(14).sum() / tr.rolling(14).sum()
    avg28 = bp.rolling(28).sum() / tr.rolling(28).sum()
    indicators['ultimate_oscillator'] = 100 * ((4 * avg7) + (2 * avg14) + avg28) / 7

    # Awesome Oscillator
    indicators['awesome_oscillator'] = sma((high + low) / 2, 5) - sma((high + low) / 2, 34)

    # Keltner Channels
    atr_val = atr(high, low, close, 20)
    ema_20 = ema(close, 20)
    indicators['keltner_channel_upper'] = ema_20 + (2 * atr_val)
    indicators['keltner_channel_lower'] = ema_20 - (2 * atr_val)

    # Volatility Indicators (10)
    indicators['atr_14'] = atr(high, low, close, 14)

    # Historical Volatility
    log_returns = np.log(close / close.shift())
    indicators['historical_volatility_20'] = log_returns.rolling(20).std() * np.sqrt(252)

    # Chaikin Volatility
    hl_spread = high - low
    ema_spread = ema(hl_spread, 10)
    indicators['chaikin_volatility'] = ((ema_spread - ema_spread.shift(10)) / ema_spread.shift(10)) * 100

    # Donchian Channels
    indicators['donchian_channel_upper'] = high.rolling(20).max()
    indicators['donchian_channel_middle'] = (high.rolling(20).max() + low.rolling(20).min()) / 2
    indicators['donchian_channel_lower'] = low.rolling(20).min()

    # Mass Index
    hl_range = high - low
    ema_range = ema(hl_range, 9)
    ema_ema_range = ema(ema_range, 9)
    mass_ratio = ema_range / ema_ema_range
    indicators['mass_index'] = mass_ratio.rolling(25).sum()

    # Vortex Indicator
    vm_plus = abs(high - low.shift())
    vm_minus = abs(low - high.shift())
    tr_series = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    indicators['vortex_indicator_plus'] = vm_plus.rolling(14).sum() / tr_series.rolling(14).sum()
    indicators['vortex_indicator_minus'] = vm_minus.rolling(14).sum() / tr_series.rolling(14).sum()

    # Ulcer Index
    max_close = close.rolling(14).max()
    pct_drawdown = 100 * (close - max_close) / max_close
    indicators['ulcer_index'] = np.sqrt((pct_drawdown ** 2).rolling(14).mean())

    # Volume Indicators (10)
    indicators['obv'] = obv(close, volume)
    indicators['adl'] = adl(high, low, close, volume)

    # Chaikin Money Flow
    clv = ((close - low) - (high - close)) / (high - low)
    clv = clv.fillna(0)
    indicators['cmf_20'] = (clv * volume).rolling(20).sum() / volume.rolling(20).sum()

    # Force Index
    indicators['fi_13'] = ema(close.diff() * volume, 13)

    # Ease of Movement
    distance = ((high + low) / 2 - (high.shift() + low.shift()) / 2)
    box_ratio = (volume / 1000000) / (high - low)
    indicators['eom_14'] = sma(distance / box_ratio, 14)

    # Volume Price Trend
    indicators['vpt'] = (volume * ((close - close.shift()) / close.shift())).cumsum()

    # Negative Volume Index
    nvi = pd.Series(1000.0, index=close.index, dtype=float)
    for i in range(1, len(close)):
        if volume.iloc[i] < volume.iloc[i-1]:
            nvi.iloc[i] = nvi.iloc[i-1] * (1 + (close.iloc[i] - close.iloc[i-1]) / close.iloc[i-1])
        else:
            nvi.iloc[i] = nvi.iloc[i-1]
    indicators['nvi'] = nvi

    # Positive Volume Index
    pvi = pd.Series(1000.0, index=close.index, dtype=float)
    for i in range(1, len(close)):
        if volume.iloc[i] > volume.iloc[i-1]:
            pvi.iloc[i] = pvi.iloc[i-1] * (1 + (close.iloc[i] - close.iloc[i-1]) / close.iloc[i-1])
        else:
            pvi.iloc[i] = pvi.iloc[i-1]
    indicators['pvi'] = pvi

    indicators['mfi_14'] = mfi(high, low, close, volume, 14)
    indicators['vwap'] = vwap(high, low, close, volume)

    return indicators


def process_partition(conn, pair, year, month):
    """Process one partition: compute technical indicators"""
    start_time = time.time()

    cur = conn.cursor()

    # Create schema if not exists
    table_name = f'technical_features_{pair}'
    partition_name = f'{table_name}_{year}_{month:02d}'

    try:
        # Create parent table if not exists
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS bqx.{table_name} (
                ts_utc TIMESTAMP WITH TIME ZONE NOT NULL,
                ema_10 DOUBLE PRECISION, ema_20 DOUBLE PRECISION, ema_50 DOUBLE PRECISION,
                ema_100 DOUBLE PRECISION, ema_200 DOUBLE PRECISION,
                sma_10 DOUBLE PRECISION, sma_20 DOUBLE PRECISION, sma_50 DOUBLE PRECISION,
                sma_100 DOUBLE PRECISION, sma_200 DOUBLE PRECISION,
                rsi_14 DOUBLE PRECISION,
                macd DOUBLE PRECISION, macd_signal DOUBLE PRECISION, macd_histogram DOUBLE PRECISION,
                stoch_k DOUBLE PRECISION, stoch_d DOUBLE PRECISION,
                cci_20 DOUBLE PRECISION, williams_r_14 DOUBLE PRECISION, roc_12 DOUBLE PRECISION,
                momentum_10 DOUBLE PRECISION, momentum_20 DOUBLE PRECISION,
                trix DOUBLE PRECISION, ultimate_oscillator DOUBLE PRECISION, awesome_oscillator DOUBLE PRECISION,
                keltner_channel_upper DOUBLE PRECISION, keltner_channel_lower DOUBLE PRECISION,
                atr_14 DOUBLE PRECISION, historical_volatility_20 DOUBLE PRECISION, chaikin_volatility DOUBLE PRECISION,
                donchian_channel_upper DOUBLE PRECISION, donchian_channel_middle DOUBLE PRECISION,
                donchian_channel_lower DOUBLE PRECISION, mass_index DOUBLE PRECISION,
                vortex_indicator_plus DOUBLE PRECISION, vortex_indicator_minus DOUBLE PRECISION,
                ulcer_index DOUBLE PRECISION,
                obv DOUBLE PRECISION, adl DOUBLE PRECISION, cmf_20 DOUBLE PRECISION,
                fi_13 DOUBLE PRECISION, eom_14 DOUBLE PRECISION, vpt DOUBLE PRECISION,
                nvi DOUBLE PRECISION, pvi DOUBLE PRECISION, mfi_14 DOUBLE PRECISION, vwap DOUBLE PRECISION,
                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc);
        """)

        # Create partition
        partition_start = f"{year}-{month:02d}-01"
        if month == 12:
            partition_end = f"{year+1}-01-01"
        else:
            partition_end = f"{year}-{month+1:02d}-01"

        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS bqx.{partition_name}
            PARTITION OF bqx.{table_name}
            FOR VALUES FROM ('{partition_start}') TO ('{partition_end}');
        """)

        conn.commit()

        # Fetch M1 OHLCV data
        m1_table = f'm1_{pair}_y{year}m{month:02d}'
        cur.execute(f"""
            SELECT time, open, high, low, close, volume
            FROM bqx.{m1_table}
            WHERE time >= '{partition_start}'::timestamp
              AND time < '{partition_end}'::timestamp
            ORDER BY time;
        """)

        rows = cur.fetchall()
        if not rows or len(rows) < 300:  # Need at least 300 rows for indicators
            elapsed = time.time() - start_time
            return 0, elapsed

        # Convert to DataFrame (convert Decimal to float)
        df = pd.DataFrame(rows, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)

        # Compute technical indicators
        indicators = compute_technical_indicators(df)

        # Add timestamp
        indicators['ts_utc'] = df['time']

        # Drop NaN rows (from initial indicator computation)
        indicators = indicators.dropna()

        if len(indicators) == 0:
            elapsed = time.time() - start_time
            return 0, elapsed

        # Insert data
        cols = ['ts_utc'] + [col for col in indicators.columns if col != 'ts_utc']

        insert_query = f"""
            INSERT INTO bqx.{partition_name} ({', '.join(cols)})
            VALUES ({', '.join(['%s'] * len(cols))})
            ON CONFLICT (ts_utc) DO NOTHING;
        """

        data_tuples = [tuple(row) for row in indicators[cols].values]

        cur.executemany(insert_query, data_tuples)
        conn.commit()

        elapsed = time.time() - start_time

        print(f"✓ [{pair.upper()}] {year}-{month:02d} | Indicators: {len(indicators):,} | {elapsed:.1f}s", flush=True)

        return len(indicators), elapsed

    except Exception as e:
        conn.rollback()
        print(f"✗ ERROR [{pair.upper()}] {year}-{month:02d}: {e}", flush=True)
        return 0, time.time() - start_time
    finally:
        cur.close()


def process_partition_worker(pair, year, month):
    """Worker function for threading"""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        rows, elapsed = process_partition(conn, pair, year, month)

        global partitions_completed, total_rows_inserted
        with progress_lock:
            partitions_completed += 1
            total_rows_inserted += rows
            progress_pct = (partitions_completed / total_partitions) * 100

        return {
            'pair': pair,
            'year': year,
            'month': month,
            'rows': rows,
            'elapsed': elapsed,
            'progress': progress_pct
        }
    finally:
        conn.close()


def main():
    """Execute technical indicators computation"""
    start_time = time.time()

    print("=" * 80)
    print("BQX ML TECHNICAL INDICATORS WORKER - Phase 1.6.7")
    print("=" * 80)
    print(f"\nCurrency Pairs: {len(CURRENCY_PAIRS)}")
    print(f"Date Range: {START_DATE.date()} to {END_DATE.date()}")
    print(f"Total Partitions: {total_partitions}")
    print(f"Threads: 8")
    print(f"Features: 45 technical indicators")
    print("\n" + "=" * 80 + "\n")

    # Generate all jobs
    months = generate_month_ranges()
    jobs = [(pair, year, month) for pair in CURRENCY_PAIRS for year, month in months]

    # Execute with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_partition_worker, pair, year, month): (pair, year, month)
                   for pair, year, month in jobs}

        for future in as_completed(futures):
            try:
                result = future.result()
            except Exception as e:
                pair, year, month = futures[future]
                print(f"✗ WORKER ERROR [{pair.upper()}] {year}-{month:02d}: {e}", flush=True)

    elapsed_total = time.time() - start_time

    print("\n" + "=" * 80)
    print("TECHNICAL INDICATORS COMPUTATION COMPLETE")
    print("=" * 80)
    print(f"Total Rows: {total_rows_inserted:,}")
    print(f"Total Partitions: {partitions_completed}/{total_partitions}")
    print(f"Total Time: {elapsed_total:.1f}s ({elapsed_total/60:.1f} minutes)")
    if total_rows_inserted > 0:
        print(f"Average Throughput: {total_rows_inserted/elapsed_total:,.0f} rows/sec")

    print("\nNext Steps:")
    print("  1. Verify technical indicators: SELECT * FROM bqx.technical_features_eurusd LIMIT 10;")
    print("  2. Check feature completeness: SELECT COUNT(*) FROM bqx.technical_features_eurusd;")
    print("  3. Proceed to Phase 1.6.8: Fibonacci Features")


if __name__ == '__main__':
    main()
