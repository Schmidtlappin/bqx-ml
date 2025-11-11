#!/usr/bin/env python3
"""
Volume Features Worker - Track 1 (Stage 1.6.3)

Computes 10 volume-based features for all 28 currency pairs.
Executes in parallel with REG backfill using 8 threads (30-40% CPU).

Features:
1. w15_volume_ratio - Short-term volume spike detector
2. w30_volume_ratio - Medium-term volume trend
3. w60_volume_ratio - Long-term volume trend
4. volume_spike - Binary: abnormal volume event
5. volume_trend_slope - Volume acceleration (linear regression slope)
6. cumulative_volume_60min - Total activity over 60 minutes
7. volume_weighted_return - VWAP-adjusted return
8. volume_price_correlation_60min - Volume-volatility relationship
9. relative_volume_position - Normalized volume percentile (0-1)
10. volume_volatility_60min - Volume consistency (stdev)

Data Source: M1.volume column (currently unused but exists)
Storage: bqx.volume_features_{pair} tables

Estimated Time: 4 hours (336 partitions × 28 pairs / 8 threads)
"""

import psycopg2
from psycopg2 import sql
import numpy as np
from scipy import stats
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Database configuration
DB_CONFIG = {
    "host": "trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com",
    "port": 5432,
    "database": "bqx",
    "user": "postgres",
    "password": "BQX_Aurora_2025_Secure",
    "sslmode": "require",
}

# All 28 preferred pairs
CURRENCY_PAIRS = [
    'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
    'cadchf', 'cadjpy', 'chfjpy',
    'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
    'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
    'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
    'usdcad', 'usdchf', 'usdjpy'
]

# Date range: 2024-07 to 2025-06 (12 months)
START_DATE = datetime(2024, 7, 1)
END_DATE = datetime(2025, 7, 1)  # Exclusive

# Thread-safe counter for progress tracking
progress_lock = threading.Lock()
partitions_completed = 0
total_partitions = len(CURRENCY_PAIRS) * 12


def generate_month_ranges():
    """Generate list of (year, month) tuples for backfill period"""
    months = []
    current = START_DATE
    while current < END_DATE:
        months.append((current.year, current.month))
        # Move to next month
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)
    return months


def compute_volume_features_for_partition(conn, pair, year, month):
    """
    Compute all 10 volume features for a specific partition

    Args:
        conn: Database connection
        pair: Currency pair (e.g., 'eurusd')
        year: Year (e.g., 2024)
        month: Month (e.g., 7)

    Returns:
        int: Number of rows processed
    """
    import time
    start_time = time.time()

    cur = conn.cursor()

    # Partition boundaries
    partition_start = datetime(year, month, 1)
    if month == 12:
        partition_end = datetime(year + 1, 1, 1)
    else:
        partition_end = datetime(year, month + 1, 1)

    # Fetch M1 data with volume and rate for this partition
    # We need a lookback window for rolling calculations
    # Fetch from 60 minutes before partition start to handle edge cases
    lookback_start = datetime(year, month, 1) if month > 1 else datetime(year - 1, 12, 1)

    m1_table = sql.Identifier('bqx', f'm1_{pair}')
    fetch_query = sql.SQL("""
        SELECT time, volume, rate, close
        FROM {}
        WHERE time >= %s - INTERVAL '60 minutes' AND time < %s
        ORDER BY time
    """).format(m1_table)

    cur.execute(fetch_query, (partition_start, partition_end))
    rows = cur.fetchall()

    if len(rows) < 60:
        # Not enough data for rolling calculations
        cur.close()
        return 0

    # Convert to numpy arrays for vectorized calculations
    times = np.array([r[0] for r in rows])
    volumes = np.array([float(r[1]) if r[1] is not None else 0.0 for r in rows])
    rates = np.array([float(r[2]) for r in rows])
    closes = np.array([float(r[3]) for r in rows])

    # Calculate returns (percentage change)
    returns = np.diff(rates) / rates[:-1]
    returns = np.concatenate([[0], returns])  # Prepend 0 for first row

    # Find index where partition actually starts (after lookback)
    partition_start_idx = np.searchsorted(times, partition_start)

    # Prepare output arrays (only for partition data, not lookback)
    n_partition = len(times) - partition_start_idx
    output_data = {
        'ts_utc': times[partition_start_idx:],
        'w15_volume_ratio': np.zeros(n_partition),
        'w30_volume_ratio': np.zeros(n_partition),
        'w60_volume_ratio': np.zeros(n_partition),
        'volume_spike': np.zeros(n_partition, dtype=int),
        'volume_trend_slope': np.zeros(n_partition),
        'cumulative_volume_60min': np.zeros(n_partition),
        'volume_weighted_return': np.zeros(n_partition),
        'volume_price_correlation_60min': np.zeros(n_partition),
        'relative_volume_position': np.zeros(n_partition),
        'volume_volatility_60min': np.zeros(n_partition),
    }

    # Compute features for each minute in the partition
    for i in range(partition_start_idx, len(times)):
        partition_i = i - partition_start_idx

        # Rolling windows (15, 30, 60 minutes lookback)
        w15_start = max(0, i - 14)
        w30_start = max(0, i - 29)
        w60_start = max(0, i - 59)

        # 1-3. Volume ratios (w15, w30, w60)
        vol_w15 = volumes[w15_start:i+1]
        vol_w30 = volumes[w30_start:i+1]
        vol_w60 = volumes[w60_start:i+1]

        mean_w15 = np.mean(vol_w15) if len(vol_w15) > 0 else 1.0
        mean_w30 = np.mean(vol_w30) if len(vol_w30) > 0 else 1.0
        mean_w60 = np.mean(vol_w60) if len(vol_w60) > 0 else 1.0

        output_data['w15_volume_ratio'][partition_i] = volumes[i] / mean_w15 if mean_w15 > 0 else 1.0
        output_data['w30_volume_ratio'][partition_i] = volumes[i] / mean_w30 if mean_w30 > 0 else 1.0
        output_data['w60_volume_ratio'][partition_i] = volumes[i] / mean_w60 if mean_w60 > 0 else 1.0

        # 4. Volume spike (binary: 1 if > 2× mean_w60)
        output_data['volume_spike'][partition_i] = 1 if volumes[i] > 2 * mean_w60 else 0

        # 5. Volume trend slope (linear regression on w60)
        if len(vol_w60) >= 10:
            x = np.arange(len(vol_w60))
            slope, _, _, _, _ = stats.linregress(x, vol_w60)
            output_data['volume_trend_slope'][partition_i] = slope

        # 6. Cumulative volume (sum over w60)
        output_data['cumulative_volume_60min'][partition_i] = np.sum(vol_w60)

        # 7. Volume-weighted return
        ret_w60 = returns[w60_start:i+1]
        if len(ret_w60) > 0 and np.sum(vol_w60) > 0:
            vwap_return = np.sum(ret_w60 * vol_w60) / np.sum(vol_w60)
            output_data['volume_weighted_return'][partition_i] = vwap_return

        # 8. Volume-price correlation
        if len(vol_w60) >= 10 and len(ret_w60) >= 10:
            abs_returns = np.abs(ret_w60)
            if np.std(vol_w60) > 0 and np.std(abs_returns) > 0:
                corr = np.corrcoef(vol_w60, abs_returns)[0, 1]
                output_data['volume_price_correlation_60min'][partition_i] = corr if not np.isnan(corr) else 0.0

        # 9. Relative volume position (percentile in w60)
        if len(vol_w60) > 0:
            min_vol = np.min(vol_w60)
            max_vol = np.max(vol_w60)
            if max_vol > min_vol:
                output_data['relative_volume_position'][partition_i] = (volumes[i] - min_vol) / (max_vol - min_vol)
            else:
                output_data['relative_volume_position'][partition_i] = 0.5

        # 10. Volume volatility (stdev over w60)
        if len(vol_w60) > 1:
            output_data['volume_volatility_60min'][partition_i] = np.std(vol_w60)

    # Insert into volume_features table
    insert_table = sql.Identifier('bqx', f'volume_features_{pair}')
    insert_query = sql.SQL("""
        INSERT INTO {} (
            ts_utc, w15_volume_ratio, w30_volume_ratio, w60_volume_ratio,
            volume_spike, volume_trend_slope, cumulative_volume_60min,
            volume_weighted_return, volume_price_correlation_60min,
            relative_volume_position, volume_volatility_60min
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (ts_utc) DO UPDATE SET
            w15_volume_ratio = EXCLUDED.w15_volume_ratio,
            w30_volume_ratio = EXCLUDED.w30_volume_ratio,
            w60_volume_ratio = EXCLUDED.w60_volume_ratio,
            volume_spike = EXCLUDED.volume_spike,
            volume_trend_slope = EXCLUDED.volume_trend_slope,
            cumulative_volume_60min = EXCLUDED.cumulative_volume_60min,
            volume_weighted_return = EXCLUDED.volume_weighted_return,
            volume_price_correlation_60min = EXCLUDED.volume_price_correlation_60min,
            relative_volume_position = EXCLUDED.relative_volume_position,
            volume_volatility_60min = EXCLUDED.volume_volatility_60min
    """).format(insert_table)

    # Batch insert - convert numpy types to Python types for psycopg2 compatibility
    insert_data = []
    for i in range(len(output_data['ts_utc'])):
        insert_data.append((
            output_data['ts_utc'][i],
            float(output_data['w15_volume_ratio'][i]),
            float(output_data['w30_volume_ratio'][i]),
            float(output_data['w60_volume_ratio'][i]),
            int(output_data['volume_spike'][i]),  # Convert numpy.int64 to Python int
            float(output_data['volume_trend_slope'][i]),
            int(output_data['cumulative_volume_60min'][i]),  # Convert to Python int
            float(output_data['volume_weighted_return'][i]),
            float(output_data['volume_price_correlation_60min'][i]),
            float(output_data['relative_volume_position'][i]),
            float(output_data['volume_volatility_60min'][i])
        ))

    cur.executemany(insert_query, insert_data)
    conn.commit()
    cur.close()

    elapsed = time.time() - start_time

    return len(insert_data), elapsed


def process_partition_worker(pair, year, month):
    """Worker function for threading (creates own DB connection)"""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        rows, elapsed = compute_volume_features_for_partition(conn, pair, year, month)

        # Update progress
        global partitions_completed
        with progress_lock:
            partitions_completed += 1
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
    """Main execution"""
    import time

    print("=" * 80)
    print("VOLUME FEATURES WORKER - TRACK 1 (STAGE 1.6.3)")
    print("=" * 80)
    print()
    print(f"Pairs: {len(CURRENCY_PAIRS)}")
    print(f"Months per pair: {len(generate_month_ranges())}")
    print(f"Total partitions: {total_partitions}")
    print(f"Threads: 8")
    print(f"Date range: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print()

    total_start = time.time()
    total_rows = 0

    # Create list of all partition jobs
    jobs = []
    for pair in CURRENCY_PAIRS:
        for year, month in generate_month_ranges():
            jobs.append((pair, year, month))

    print(f"Processing {len(jobs)} partitions with 8 threads...")
    print()

    # Execute with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as executor:
        # Submit all jobs
        futures = {executor.submit(process_partition_worker, pair, year, month): (pair, year, month)
                   for pair, year, month in jobs}

        # Process results as they complete
        for future in as_completed(futures):
            pair, year, month = futures[future]
            try:
                result = future.result()
                total_rows += result['rows']

                print(f"[{result['pair'].upper()}] {result['year']}-{result['month']:02d} | "
                      f"{result['rows']:,} rows | {result['elapsed']:.1f}s | "
                      f"Progress: {result['progress']:5.1f}%")

            except Exception as e:
                print(f"✗ ERROR [{pair.upper()}] {year}-{month:02d}: {e}")

    total_elapsed = time.time() - total_start

    # Final summary
    print()
    print("=" * 80)
    print("VOLUME FEATURES COMPUTATION COMPLETE")
    print("=" * 80)
    print(f"Total Rows Processed: {total_rows:,}")
    print(f"Total Partitions: {partitions_completed}/{total_partitions}")
    print(f"Total Time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} minutes)")
    print(f"Average Throughput: {total_rows/total_elapsed:.0f} rows/sec")
    print()
    print("Next Steps:")
    print("  1. Verify volume features: SELECT * FROM bqx.volume_features_eurusd_2024_07 LIMIT 10;")
    print("  2. Proceed to Time & Spread Features Worker")
    print()


if __name__ == "__main__":
    main()
