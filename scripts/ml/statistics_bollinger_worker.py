#!/usr/bin/env python3
"""
Statistics & Bollinger Worker - Track 1 (Stage 1.6.3)

Computes 10 features: 5 higher-order statistics + 5 Bollinger Bands indicators.
Uses rate_index from M1 tables for all 28 currency pairs.

Statistics Features (5):
1. skewness_60min - Distribution asymmetry (3rd moment)
2. kurtosis_60min - Tail heaviness (4th moment)
3. median_absolute_deviation_60min - Robust variability measure
4. entropy_60min - Information content/randomness
5. autocorrelation_lag1 - 1-period serial correlation

Bollinger Features (5):
1. bollinger_upper_20 - Upper band (MA + 2*std)
2. bollinger_lower_20 - Lower band (MA - 2*std)
3. bollinger_middle_20 - Middle band (20-period MA)
4. bollinger_width_20 - Band width
5. bollinger_percent_b - Price position within bands

Data Source: M1.rate_index
Storage: statistics_features_{pair} + bollinger_features_{pair} tables
Estimated Time: 3-4 hours (336 partitions, 8 threads)
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

# Thread-safe counter
progress_lock = threading.Lock()
partitions_completed = 0
total_partitions = len(CURRENCY_PAIRS) * 12


def generate_month_ranges():
    """Generate list of (year, month) tuples"""
    months = []
    current = START_DATE
    while current < END_DATE:
        months.append((current.year, current.month))
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)
    return months


def compute_entropy(data):
    """Compute Shannon entropy of discretized data"""
    if len(data) < 2:
        return 0.0

    # Discretize into 10 bins
    hist, _ = np.histogram(data, bins=10)
    hist = hist[hist > 0]  # Remove zero bins
    probs = hist / np.sum(hist)
    return -np.sum(probs * np.log2(probs + 1e-10))


def compute_statistics_features(rate_indices):
    """Compute 5 statistical features with 60-minute rolling window"""
    n = len(rate_indices)
    stats_features = {
        'skewness_60min': np.zeros(n),
        'kurtosis_60min': np.zeros(n),
        'median_absolute_deviation_60min': np.zeros(n),
        'entropy_60min': np.zeros(n),
        'autocorrelation_lag1': np.zeros(n),
    }

    for i in range(n):
        w60_start = max(0, i - 59)
        window = rate_indices[w60_start:i+1]

        if len(window) >= 10:
            # Skewness and Kurtosis
            stats_features['skewness_60min'][i] = stats.skew(window)
            stats_features['kurtosis_60min'][i] = stats.kurtosis(window)

            # Median Absolute Deviation
            median = np.median(window)
            mad = np.median(np.abs(window - median))
            stats_features['median_absolute_deviation_60min'][i] = mad

            # Entropy
            stats_features['entropy_60min'][i] = compute_entropy(window)

            # Autocorrelation lag-1
            if len(window) >= 2:
                lag1_corr = np.corrcoef(window[:-1], window[1:])[0, 1]
                stats_features['autocorrelation_lag1'][i] = lag1_corr if not np.isnan(lag1_corr) else 0.0

    return stats_features


def compute_bollinger_features(rate_indices):
    """Compute 5 Bollinger Bands features with 20-period window"""
    n = len(rate_indices)
    bollinger_features = {
        'bollinger_upper_20': np.zeros(n),
        'bollinger_lower_20': np.zeros(n),
        'bollinger_middle_20': np.zeros(n),
        'bollinger_width_20': np.zeros(n),
        'bollinger_percent_b': np.zeros(n),
    }

    for i in range(n):
        w20_start = max(0, i - 19)
        window = rate_indices[w20_start:i+1]

        if len(window) >= 10:
            mean = np.mean(window)
            std = np.std(window)

            bollinger_features['bollinger_middle_20'][i] = mean
            bollinger_features['bollinger_upper_20'][i] = mean + 2 * std
            bollinger_features['bollinger_lower_20'][i] = mean - 2 * std
            bollinger_features['bollinger_width_20'][i] = 4 * std  # upper - lower

            # %B indicator: (price - lower) / (upper - lower)
            if std > 0:
                percent_b = (rate_indices[i] - (mean - 2*std)) / (4 * std)
                bollinger_features['bollinger_percent_b'][i] = percent_b
            else:
                bollinger_features['bollinger_percent_b'][i] = 0.5

    return bollinger_features


def process_partition(conn, pair, year, month):
    """Process one partition: compute statistics and Bollinger features"""
    import time
    start_time = time.time()

    cur = conn.cursor()

    # Partition boundaries
    partition_start = datetime(year, month, 1)
    if month == 12:
        partition_end = datetime(year + 1, 1, 1)
    else:
        partition_end = datetime(year, month + 1, 1)

    # Fetch M1 data with 60-minute lookback for rolling windows
    m1_table = sql.Identifier('bqx', f'm1_{pair}')
    fetch_query = sql.SQL("""
        SELECT time, rate_index
        FROM {}
        WHERE time >= %s - INTERVAL '60 minutes' AND time < %s
        ORDER BY time
    """).format(m1_table)

    cur.execute(fetch_query, (partition_start, partition_end))
    rows = cur.fetchall()

    if len(rows) < 60:
        cur.close()
        return 0, 0, 0

    # Convert to arrays
    times = np.array([r[0] for r in rows])
    rate_indices = np.array([float(r[1]) if r[1] is not None else 100.0 for r in rows])

    # Find partition start index
    partition_start_idx = np.searchsorted(times, partition_start)

    # Compute features (on full data including lookback)
    stats_features = compute_statistics_features(rate_indices)
    bollinger_features = compute_bollinger_features(rate_indices)

    # Extract only partition data
    partition_times = times[partition_start_idx:]
    n_partition = len(partition_times)

    # Insert statistics features
    stats_table = sql.Identifier('bqx', f'statistics_features_{pair}')
    stats_insert = sql.SQL("""
        INSERT INTO {} (
            ts_utc, skewness_60min, kurtosis_60min, median_absolute_deviation_60min,
            entropy_60min, autocorrelation_lag1
        ) VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (ts_utc) DO UPDATE SET
            skewness_60min = EXCLUDED.skewness_60min,
            kurtosis_60min = EXCLUDED.kurtosis_60min,
            median_absolute_deviation_60min = EXCLUDED.median_absolute_deviation_60min,
            entropy_60min = EXCLUDED.entropy_60min,
            autocorrelation_lag1 = EXCLUDED.autocorrelation_lag1
    """).format(stats_table)

    stats_data = []
    for i in range(n_partition):
        idx = partition_start_idx + i
        stats_data.append((
            partition_times[i],
            float(stats_features['skewness_60min'][idx]),
            float(stats_features['kurtosis_60min'][idx]),
            float(stats_features['median_absolute_deviation_60min'][idx]),
            float(stats_features['entropy_60min'][idx]),
            float(stats_features['autocorrelation_lag1'][idx])
        ))

    cur.executemany(stats_insert, stats_data)

    # Insert Bollinger features
    boll_table = sql.Identifier('bqx', f'bollinger_features_{pair}')
    boll_insert = sql.SQL("""
        INSERT INTO {} (
            ts_utc, bollinger_upper_20, bollinger_lower_20, bollinger_middle_20,
            bollinger_width_20, bollinger_percent_b
        ) VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (ts_utc) DO UPDATE SET
            bollinger_upper_20 = EXCLUDED.bollinger_upper_20,
            bollinger_lower_20 = EXCLUDED.bollinger_lower_20,
            bollinger_middle_20 = EXCLUDED.bollinger_middle_20,
            bollinger_width_20 = EXCLUDED.bollinger_width_20,
            bollinger_percent_b = EXCLUDED.bollinger_percent_b
    """).format(boll_table)

    boll_data = []
    for i in range(n_partition):
        idx = partition_start_idx + i
        boll_data.append((
            partition_times[i],
            float(bollinger_features['bollinger_upper_20'][idx]),
            float(bollinger_features['bollinger_lower_20'][idx]),
            float(bollinger_features['bollinger_middle_20'][idx]),
            float(bollinger_features['bollinger_width_20'][idx]),
            float(bollinger_features['bollinger_percent_b'][idx])
        ))

    cur.executemany(boll_insert, boll_data)

    conn.commit()
    cur.close()

    elapsed = time.time() - start_time
    return len(stats_data), len(boll_data), elapsed


def process_partition_worker(pair, year, month):
    """Worker function for threading"""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        stats_rows, boll_rows, elapsed = process_partition(conn, pair, year, month)

        global partitions_completed
        with progress_lock:
            partitions_completed += 1
            progress_pct = (partitions_completed / total_partitions) * 100

        return {
            'pair': pair,
            'year': year,
            'month': month,
            'stats_rows': stats_rows,
            'boll_rows': boll_rows,
            'elapsed': elapsed,
            'progress': progress_pct
        }
    finally:
        conn.close()


def main():
    """Main execution"""
    import time

    print("=" * 80)
    print("STATISTICS & BOLLINGER WORKER - TRACK 1 (STAGE 1.6.3)")
    print("=" * 80)
    print()
    print(f"Pairs: {len(CURRENCY_PAIRS)}")
    print(f"Months per pair: {len(generate_month_ranges())}")
    print(f"Total partitions: {total_partitions}")
    print(f"Threads: 8")
    print(f"Date range: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print()
    print("Features: 10 total")
    print("  Statistics: 5 (skewness, kurtosis, MAD, entropy, autocorr)")
    print("  Bollinger: 5 (upper, lower, middle, width, %B)")
    print()

    total_start = time.time()
    total_stats_rows = 0
    total_boll_rows = 0

    # Create list of all partition jobs
    jobs = []
    for pair in CURRENCY_PAIRS:
        for year, month in generate_month_ranges():
            jobs.append((pair, year, month))

    print(f"Processing {len(jobs)} partitions with 8 threads...")
    print()

    # Execute with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_partition_worker, pair, year, month): (pair, year, month)
                   for pair, year, month in jobs}

        for future in as_completed(futures):
            pair, year, month = futures[future]
            try:
                result = future.result()
                total_stats_rows += result['stats_rows']
                total_boll_rows += result['boll_rows']

                print(f"[{result['pair'].upper()}] {result['year']}-{result['month']:02d} | "
                      f"Stats: {result['stats_rows']:,} | Boll: {result['boll_rows']:,} | "
                      f"{result['elapsed']:.1f}s | Progress: {result['progress']:5.1f}%")

            except Exception as e:
                print(f"✗ ERROR [{pair.upper()}] {year}-{month:02d}: {e}")

    total_elapsed = time.time() - total_start

    # Final summary
    print()
    print("=" * 80)
    print("STATISTICS & BOLLINGER COMPUTATION COMPLETE")
    print("=" * 80)
    print(f"Statistics Rows: {total_stats_rows:,}")
    print(f"Bollinger Rows: {total_boll_rows:,}")
    print(f"Total Partitions: {partitions_completed}/{total_partitions}")
    print(f"Total Time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} minutes)")
    print(f"Average Throughput: {(total_stats_rows + total_boll_rows)/total_elapsed:.0f} rows/sec")
    print()
    print("Next Steps:")
    print("  1. Verify features: SELECT * FROM bqx.statistics_features_eurusd LIMIT 10;")
    print("  2. Verify Bollinger: SELECT * FROM bqx.bollinger_features_eurusd LIMIT 10;")
    print("  3. Proceed to Correlation Features Worker")
    print()


if __name__ == "__main__":
    main()
