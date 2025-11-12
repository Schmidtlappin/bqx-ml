#!/usr/bin/env python3
"""
Fibonacci Features Worker - Phase 1.6.8

Computes 12 Fibonacci-based features across 28 currency pairs:
- Fibonacci Retracements (5): 23.6%, 38.2%, 50%, 61.8%, 78.6%
- Fibonacci Extensions (3): 161.8%, 261.8%, 423.6%
- Fibonacci Fan Levels (3): Upper, Middle, Lower
- Fibonacci Arc Radius (1)

Data Source: M1 OHLC data
Storage: bqx.fibonacci_features_{pair}
Computation: Rolling 240-minute (4-hour) high/low swing points
Estimated Time: 3-4 hours (336 partitions / 8 threads)
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


def compute_fibonacci_features(df, lookback=240):
    """
    Compute Fibonacci features based on recent swing high/low

    Args:
        df: DataFrame with columns [time, high, low, close]
        lookback: Rolling window for swing point identification (default 240 = 4 hours)

    Returns:
        DataFrame with 12 Fibonacci feature columns
    """
    high = df['high']
    low = df['low']
    close = df['close']

    # Find rolling swing high and low
    swing_high = high.rolling(window=lookback, center=False).max()
    swing_low = low.rolling(window=lookback, center=False).min()

    # Fibonacci range
    fib_range = swing_high - swing_low

    # Fibonacci Retracements (from swing high DOWN)
    fib_236 = swing_high - (fib_range * 0.236)
    fib_382 = swing_high - (fib_range * 0.382)
    fib_500 = swing_high - (fib_range * 0.500)
    fib_618 = swing_high - (fib_range * 0.618)
    fib_786 = swing_high - (fib_range * 0.786)

    # Fibonacci Extensions (from swing high UP)
    fib_ext_1618 = swing_high + (fib_range * 0.618)
    fib_ext_2618 = swing_high + (fib_range * 1.618)
    fib_ext_4236 = swing_high + (fib_range * 2.618)

    # Fibonacci Fan Levels (angled support/resistance)
    # Simplified: use time-based slope from swing low to current
    time_elapsed = pd.Series(range(len(df)), index=df.index)
    slope_38 = (fib_382 - swing_low) / (time_elapsed - time_elapsed.shift(lookback)).replace(0, 1)
    slope_50 = (fib_500 - swing_low) / (time_elapsed - time_elapsed.shift(lookback)).replace(0, 1)
    slope_62 = (fib_618 - swing_low) / (time_elapsed - time_elapsed.shift(lookback)).replace(0, 1)

    fib_fan_upper = swing_low + (slope_38 * (time_elapsed - time_elapsed.shift(lookback)))
    fib_fan_middle = swing_low + (slope_50 * (time_elapsed - time_elapsed.shift(lookback)))
    fib_fan_lower = swing_low + (slope_62 * (time_elapsed - time_elapsed.shift(lookback)))

    # Fibonacci Arc Radius (distance from swing low to current price)
    fib_arc_radius = np.sqrt((close - swing_low)**2 + (time_elapsed - time_elapsed.shift(lookback))**2)

    # Create output DataFrame
    fib_features = pd.DataFrame({
        'fib_retracement_236': fib_236,
        'fib_retracement_382': fib_382,
        'fib_retracement_500': fib_500,
        'fib_retracement_618': fib_618,
        'fib_retracement_786': fib_786,
        'fib_extension_1618': fib_ext_1618,
        'fib_extension_2618': fib_ext_2618,
        'fib_extension_4236': fib_ext_4236,
        'fib_fan_upper': fib_fan_upper,
        'fib_fan_middle': fib_fan_middle,
        'fib_fan_lower': fib_fan_lower,
        'fib_arc_radius': fib_arc_radius
    }, index=df.index)

    return fib_features


def process_partition(conn, pair, year, month):
    """Process one partition: compute Fibonacci features"""
    start_time = time.time()

    cur = conn.cursor()

    # Create schema if not exists
    table_name = f'fibonacci_features_{pair}'
    partition_name = f'{table_name}_{year}_{month:02d}'

    try:
        # Create parent table if not exists
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS bqx.{table_name} (
                ts_utc TIMESTAMP WITH TIME ZONE NOT NULL,
                fib_retracement_236 DOUBLE PRECISION,
                fib_retracement_382 DOUBLE PRECISION,
                fib_retracement_500 DOUBLE PRECISION,
                fib_retracement_618 DOUBLE PRECISION,
                fib_retracement_786 DOUBLE PRECISION,
                fib_extension_1618 DOUBLE PRECISION,
                fib_extension_2618 DOUBLE PRECISION,
                fib_extension_4236 DOUBLE PRECISION,
                fib_fan_upper DOUBLE PRECISION,
                fib_fan_middle DOUBLE PRECISION,
                fib_fan_lower DOUBLE PRECISION,
                fib_arc_radius DOUBLE PRECISION,
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

        # Fetch M1 OHLC data
        m1_table = f'm1_{pair}_y{year}m{month:02d}'
        cur.execute(f"""
            SELECT time, high, low, close
            FROM bqx.{m1_table}
            WHERE time >= '{partition_start}'::timestamp
              AND time < '{partition_end}'::timestamp
            ORDER BY time;
        """)

        rows = cur.fetchall()
        if not rows or len(rows) < 240:  # Need at least 240 rows for 4-hour lookback
            elapsed = time.time() - start_time
            return 0, elapsed

        # Convert to DataFrame (convert Decimal to float)
        df = pd.DataFrame(rows, columns=['time', 'high', 'low', 'close'])
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)

        # Compute Fibonacci features
        fib_features = compute_fibonacci_features(df, lookback=240)

        # Add timestamp
        fib_features['ts_utc'] = df['time']

        # Drop NaN rows (from initial lookback period)
        fib_features = fib_features.dropna()

        if len(fib_features) == 0:
            elapsed = time.time() - start_time
            return 0, elapsed

        # Insert data
        cols = ['ts_utc', 'fib_retracement_236', 'fib_retracement_382', 'fib_retracement_500',
                'fib_retracement_618', 'fib_retracement_786', 'fib_extension_1618',
                'fib_extension_2618', 'fib_extension_4236', 'fib_fan_upper', 'fib_fan_middle',
                'fib_fan_lower', 'fib_arc_radius']

        insert_query = f"""
            INSERT INTO bqx.{partition_name} ({', '.join(cols)})
            VALUES ({', '.join(['%s'] * len(cols))})
            ON CONFLICT (ts_utc) DO NOTHING;
        """

        data_tuples = [tuple(row) for row in fib_features[cols].values]

        cur.executemany(insert_query, data_tuples)
        conn.commit()

        elapsed = time.time() - start_time

        print(f"✓ [{pair.upper()}] {year}-{month:02d} | Fibonacci: {len(fib_features):,} | {elapsed:.1f}s", flush=True)

        return len(fib_features), elapsed

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
    """Execute Fibonacci features computation"""
    start_time = time.time()

    print("=" * 80)
    print("BQX ML FIBONACCI FEATURES WORKER - Phase 1.6.8")
    print("=" * 80)
    print(f"\nCurrency Pairs: {len(CURRENCY_PAIRS)}")
    print(f"Date Range: {START_DATE.date()} to {END_DATE.date()}")
    print(f"Total Partitions: {total_partitions}")
    print(f"Threads: 8")
    print(f"Features: 12 Fibonacci features")
    print(f"Lookback: 240 minutes (4 hours)")
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
    print("FIBONACCI FEATURES COMPUTATION COMPLETE")
    print("=" * 80)
    print(f"Total Rows: {total_rows_inserted:,}")
    print(f"Total Partitions: {partitions_completed}/{total_partitions}")
    print(f"Total Time: {elapsed_total:.1f}s ({elapsed_total/60:.1f} minutes)")
    if total_rows_inserted > 0:
        print(f"Average Throughput: {total_rows_inserted/elapsed_total:,.0f} rows/sec")

    print("\nNext Steps:")
    print("  1. Verify Fibonacci features: SELECT * FROM bqx.fibonacci_features_eurusd LIMIT 10;")
    print("  2. Check feature completeness: SELECT COUNT(*) FROM bqx.fibonacci_features_eurusd;")
    print("  3. All Phase 1.6 features complete!")


if __name__ == '__main__':
    main()
