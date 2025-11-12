#!/usr/bin/env python3
"""
Correlation Features Worker - Track 1 (Phase 1.6.6)

Computes 15 correlation features across currency pairs:
- EUR pairs correlations (5): EUR vs AUD, CAD, GBP, JPY, USD
- GBP pairs correlations (5): GBP vs AUD, CAD, CHF, JPY, USD
- USD pairs correlations (5): USD vs AUD, CAD, CHF, JPY, EUR

Data Source: M1 source tables (rate column)
Storage: bqx.correlation_features_{pair}
Computation: 60-minute rolling window Pearson correlation
Estimated Time: 5-6 hours (336 partitions / 8 threads)
"""

import psycopg2
from psycopg2 import sql
import numpy as np
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

# Correlation pair groups
CORRELATION_GROUPS = {
    # EUR pairs (5 correlations)
    'eur': ['euraud', 'eurcad', 'eurgbp', 'eurjpy', 'eurusd'],
    # GBP pairs (5 correlations)
    'gbp': ['gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpusd'],
    # USD pairs (5 correlations)
    'usd': ['usdcad', 'usdchf', 'usdjpy', 'eurusd', 'audusd']
}

# Date range
START_DATE = datetime(2024, 7, 1)
END_DATE = datetime(2025, 7, 1)  # Exclusive

# Thread-safe counter
progress_lock = threading.Lock()
partitions_completed = 0
total_partitions = len(CURRENCY_PAIRS) * 12


def generate_month_ranges():
    """Generate list of (year, month) tuples from July 2024 to June 2025"""
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


def compute_correlation_features(timestamps, pair_rates, corr_group_rates):
    """
    Compute correlation features using 60-minute rolling window

    Args:
        timestamps: Array of timestamps
        pair_rates: Rates for the current pair
        corr_group_rates: Dict of {pair_name: rates_array} for correlation group

    Returns:
        Dict of correlation features
    """
    n = len(timestamps)
    window_size = 60  # 60 minutes

    # Initialize correlation features
    corr_features = {}
    for corr_pair in corr_group_rates.keys():
        feature_name = f'corr_{corr_pair[:3]}' if corr_pair[:3] in ['eur', 'gbp', 'usd'] else f'corr_{corr_pair}'
        corr_features[feature_name] = np.zeros(n)

    # Compute rolling correlation
    for i in range(n):
        # 60-minute window
        w_start = max(0, i - window_size + 1)
        w_end = i + 1

        if w_end - w_start < 10:  # Need at least 10 points
            continue

        window_pair_rates = pair_rates[w_start:w_end]

        # Compute correlation with each pair in the group
        for corr_pair, corr_rates in corr_group_rates.items():
            window_corr_rates = corr_rates[w_start:w_end]

            # Pearson correlation
            if len(window_pair_rates) >= 10 and len(window_corr_rates) >= 10:
                try:
                    corr_coef = np.corrcoef(window_pair_rates, window_corr_rates)[0, 1]
                    if not np.isnan(corr_coef):
                        feature_name = f'corr_{corr_pair[:3]}' if corr_pair[:3] in ['eur', 'gbp', 'usd'] else f'corr_{corr_pair}'
                        corr_features[feature_name][i] = corr_coef
                except:
                    pass

    return corr_features


def process_partition(conn, pair, year, month):
    """Process one partition: compute correlation features"""
    start_time = time.time()

    cur = conn.cursor()

    # Create schema if not exists
    table_name = f'correlation_features_{pair}'
    partition_name = f'{table_name}_{year}_{month:02d}'

    try:
        # Create parent table if not exists
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS bqx.{table_name} (
                ts_utc TIMESTAMP WITH TIME ZONE NOT NULL,
                pair VARCHAR(6) NOT NULL,
                corr_eur_aud DOUBLE PRECISION,
                corr_eur_cad DOUBLE PRECISION,
                corr_eur_gbp DOUBLE PRECISION,
                corr_eur_jpy DOUBLE PRECISION,
                corr_eur_usd DOUBLE PRECISION,
                corr_gbp_aud DOUBLE PRECISION,
                corr_gbp_cad DOUBLE PRECISION,
                corr_gbp_chf DOUBLE PRECISION,
                corr_gbp_jpy DOUBLE PRECISION,
                corr_gbp_usd DOUBLE PRECISION,
                corr_usd_aud DOUBLE PRECISION,
                corr_usd_cad DOUBLE PRECISION,
                corr_usd_chf DOUBLE PRECISION,
                corr_usd_jpy DOUBLE PRECISION,
                corr_usd_eur DOUBLE PRECISION,
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

        # Fetch M1 data for this pair (M1 tables use 'time' not 'ts_utc')
        m1_table = f'm1_{pair}_y{year}m{month:02d}'
        cur.execute(f"""
            SELECT time, rate
            FROM bqx.{m1_table}
            WHERE time >= '{partition_start}'::timestamp
              AND time < '{partition_end}'::timestamp
            ORDER BY time;
        """)

        rows = cur.fetchall()
        if not rows:
            elapsed = time.time() - start_time
            return 0, elapsed

        timestamps = np.array([row[0] for row in rows])
        pair_rates = np.array([float(row[1]) for row in rows])  # Convert Decimal to float

        # Determine which correlation group this pair belongs to
        corr_group_rates = {}
        for group_name, group_pairs in CORRELATION_GROUPS.items():
            if pair in group_pairs:
                # Fetch rates for all pairs in this group (except current pair)
                for corr_pair in group_pairs:
                    if corr_pair != pair:
                        corr_m1_table = f'm1_{corr_pair}_y{year}m{month:02d}'
                        cur.execute(f"""
                            SELECT rate
                            FROM bqx.{corr_m1_table}
                            WHERE time >= '{partition_start}'::timestamp
                              AND time < '{partition_end}'::timestamp
                            ORDER BY time;
                        """)
                        corr_rows = cur.fetchall()
                        if len(corr_rows) == len(rows):  # Must have same length
                            corr_group_rates[corr_pair] = np.array([float(r[0]) for r in corr_rows])  # Convert Decimal to float
                break

        if not corr_group_rates:
            elapsed = time.time() - start_time
            return 0, elapsed

        # Compute correlation features
        corr_features = compute_correlation_features(timestamps, pair_rates, corr_group_rates)

        # Insert data
        insert_query = f"""
            INSERT INTO bqx.{partition_name} (
                ts_utc, pair, corr_eur_aud, corr_eur_cad, corr_eur_gbp, corr_eur_jpy, corr_eur_usd,
                corr_gbp_aud, corr_gbp_cad, corr_gbp_chf, corr_gbp_jpy, corr_gbp_usd,
                corr_usd_aud, corr_usd_cad, corr_usd_chf, corr_usd_jpy, corr_usd_eur
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ts_utc) DO UPDATE SET
                corr_eur_aud = EXCLUDED.corr_eur_aud,
                corr_eur_cad = EXCLUDED.corr_eur_cad,
                corr_eur_gbp = EXCLUDED.corr_eur_gbp,
                corr_eur_jpy = EXCLUDED.corr_eur_jpy,
                corr_eur_usd = EXCLUDED.corr_eur_usd,
                corr_gbp_aud = EXCLUDED.corr_gbp_aud,
                corr_gbp_cad = EXCLUDED.corr_gbp_cad,
                corr_gbp_chf = EXCLUDED.corr_gbp_chf,
                corr_gbp_jpy = EXCLUDED.corr_gbp_jpy,
                corr_gbp_usd = EXCLUDED.corr_gbp_usd,
                corr_usd_aud = EXCLUDED.corr_usd_aud,
                corr_usd_cad = EXCLUDED.corr_usd_cad,
                corr_usd_chf = EXCLUDED.corr_usd_chf,
                corr_usd_jpy = EXCLUDED.corr_usd_jpy,
                corr_usd_eur = EXCLUDED.corr_usd_eur;
        """

        batch_size = 1000
        for i in range(0, len(timestamps), batch_size):
            batch_end = min(i + batch_size, len(timestamps))
            batch_data = []

            for j in range(i, batch_end):
                row = [
                    timestamps[j],
                    pair,
                    corr_features.get('corr_eur_aud', np.zeros(len(timestamps)))[j] if 'corr_eur_aud' in corr_features else None,
                    corr_features.get('corr_eur_cad', np.zeros(len(timestamps)))[j] if 'corr_eur_cad' in corr_features else None,
                    corr_features.get('corr_eur_gbp', np.zeros(len(timestamps)))[j] if 'corr_eur_gbp' in corr_features else None,
                    corr_features.get('corr_eur_jpy', np.zeros(len(timestamps)))[j] if 'corr_eur_jpy' in corr_features else None,
                    corr_features.get('corr_eur_usd', np.zeros(len(timestamps)))[j] if 'corr_eur_usd' in corr_features else None,
                    corr_features.get('corr_gbp_aud', np.zeros(len(timestamps)))[j] if 'corr_gbp_aud' in corr_features else None,
                    corr_features.get('corr_gbp_cad', np.zeros(len(timestamps)))[j] if 'corr_gbp_cad' in corr_features else None,
                    corr_features.get('corr_gbp_chf', np.zeros(len(timestamps)))[j] if 'corr_gbp_chf' in corr_features else None,
                    corr_features.get('corr_gbp_jpy', np.zeros(len(timestamps)))[j] if 'corr_gbp_jpy' in corr_features else None,
                    corr_features.get('corr_gbp_usd', np.zeros(len(timestamps)))[j] if 'corr_gbp_usd' in corr_features else None,
                    corr_features.get('corr_usd_aud', np.zeros(len(timestamps)))[j] if 'corr_usd_aud' in corr_features else None,
                    corr_features.get('corr_usd_cad', np.zeros(len(timestamps)))[j] if 'corr_usd_cad' in corr_features else None,
                    corr_features.get('corr_usd_chf', np.zeros(len(timestamps)))[j] if 'corr_usd_chf' in corr_features else None,
                    corr_features.get('corr_usd_jpy', np.zeros(len(timestamps)))[j] if 'corr_usd_jpy' in corr_features else None,
                    corr_features.get('corr_usd_eur', np.zeros(len(timestamps)))[j] if 'corr_usd_eur' in corr_features else None,
                ]
                batch_data.append(row)

            cur.executemany(insert_query, batch_data)
            conn.commit()

        elapsed = time.time() - start_time
        return len(timestamps), elapsed

    except Exception as e:
        conn.rollback()
        print(f"✗ ERROR [{pair.upper()}] {year}-{month:02d}: {e}")
        raise
    finally:
        cur.close()


def process_partition_worker(pair, year, month):
    """Worker function for threading"""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        rows, elapsed = process_partition(conn, pair, year, month)

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
    print("=" * 80)
    print("CORRELATION FEATURES WORKER - TRACK 1 (PHASE 1.6.6)")
    print("=" * 80)
    print()
    print(f"Pairs: {len(CURRENCY_PAIRS)}")
    print(f"Months per pair: 12")
    print(f"Total partitions: {total_partitions}")
    print(f"Threads: 8")
    print(f"Date range: {START_DATE.date()} to {END_DATE.date()}")
    print()
    print("Features: 15 correlation features")
    print("  EUR pairs: corr_eur_aud, corr_eur_cad, corr_eur_gbp, corr_eur_jpy, corr_eur_usd (5)")
    print("  GBP pairs: corr_gbp_aud, corr_gbp_cad, corr_gbp_chf, corr_gbp_jpy, corr_gbp_usd (5)")
    print("  USD pairs: corr_usd_aud, corr_usd_cad, corr_usd_chf, corr_usd_jpy, corr_usd_eur (5)")
    print()
    print(f"Processing {total_partitions} partitions with 8 threads...")
    print()

    total_start = time.time()
    total_rows = 0

    # Generate all partition jobs
    months = generate_month_ranges()
    jobs = []
    for pair in CURRENCY_PAIRS:
        for year, month in months:
            jobs.append((pair, year, month))

    # Execute with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_partition_worker, pair, year, month): (pair, year, month)
                   for pair, year, month in jobs}

        for future in as_completed(futures):
            pair, year, month = futures[future]
            try:
                result = future.result()
                total_rows += result['rows']

                print(f"[{result['pair'].upper()}] {result['year']}-{result['month']:02d} | "
                      f"Rows: {result['rows']:,} | "
                      f"{result['elapsed']:.1f}s | Progress: {result['progress']:5.1f}%")

            except Exception as e:
                print(f"✗ ERROR [{pair.upper()}] {year}-{month:02d}: {e}")

    total_elapsed = time.time() - total_start

    # Final summary
    print()
    print("=" * 80)
    print("CORRELATION FEATURES COMPUTATION COMPLETE")
    print("=" * 80)
    print(f"Total Rows: {total_rows:,}")
    print(f"Total Partitions: {partitions_completed}/{total_partitions}")
    print(f"Total Time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} minutes)")
    print(f"Average Throughput: {total_rows/total_elapsed:.0f} rows/sec")
    print()
    print("Next Steps:")
    print("  1. Verify correlation features: SELECT * FROM bqx.correlation_features_eurusd LIMIT 10;")
    print("  2. Check feature completeness: SELECT COUNT(*) FROM bqx.correlation_features_eurusd;")
    print("  3. Proceed to Phase 1.6.7: Technical Indicators")


if __name__ == '__main__':
    main()
