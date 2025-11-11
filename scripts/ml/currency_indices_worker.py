#!/usr/bin/env python3
"""
Currency Indices Worker - Track 1 (Stage 1.6.3)

Computes 8 synthetic currency strength indices from cross-pair analysis.
Uses rate_index from all 28 M1 pairs to derive individual currency strength.

Currency Indices (8):
1. USD_index - US Dollar strength index
2. EUR_index - Euro strength index
3. GBP_index - British Pound strength index
4. AUD_index - Australian Dollar strength index
5. CAD_index - Canadian Dollar strength index
6. JPY_index - Japanese Yen strength index
7. CHF_index - Swiss Franc strength index
8. NZD_index - New Zealand Dollar strength index

Methodology:
- Each index is derived from pairs where that currency appears
- Formula: index = geometric mean of normalized pair indices
- Example: USD_index from EURUSD (inverse), GBPUSD (inverse), USDJPY, USDCHF, USDCAD

Data Source: M1.rate_index from all 28 pairs
Storage: bqx.currency_indices table (single table, 12 monthly partitions)

Estimated Time: 2-3 hours (12 months, cross-pair analysis)
"""

import psycopg2
from psycopg2 import sql
import numpy as np
from datetime import datetime, timezone
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

# Currency pair groups for each major currency
# Format: (pair, is_base_currency)
# If is_base_currency=True: currency is base (e.g., EUR in EURUSD)
# If is_base_currency=False: currency is quote (e.g., USD in EURUSD, inverse relationship)

CURRENCY_GROUPS = {
    'USD': [
        # USD as quote (inverse relationship)
        ('eurusd', False),
        ('gbpusd', False),
        ('audusd', False),
        ('nzdusd', False),
        # USD as base
        ('usdjpy', True),
        ('usdchf', True),
        ('usdcad', True),
    ],
    'EUR': [
        # EUR as base
        ('eurusd', True),
        ('eurjpy', True),
        ('eurgbp', True),
        ('eurchf', True),
        ('eurcad', True),
        ('euraud', True),
        ('eurnzd', True),
    ],
    'GBP': [
        # GBP as base
        ('gbpusd', True),
        ('gbpjpy', True),
        ('gbpchf', True),
        ('gbpcad', True),
        ('gbpaud', True),
        ('gbpnzd', True),
        # GBP as quote (inverse)
        ('eurgbp', False),
    ],
    'AUD': [
        # AUD as base
        ('audcad', True),
        ('audchf', True),
        ('audjpy', True),
        ('audnzd', True),
        ('audusd', True),
        # AUD as quote (inverse)
        ('euraud', False),
        ('gbpaud', False),
    ],
    'CAD': [
        # CAD as base
        ('cadchf', True),
        ('cadjpy', True),
        # CAD as quote (inverse)
        ('audcad', False),
        ('eurcad', False),
        ('gbpcad', False),
        ('nzdcad', False),
        ('usdcad', False),
    ],
    'JPY': [
        # JPY as quote (inverse - higher index = stronger JPY)
        ('audjpy', False),
        ('cadjpy', False),
        ('chfjpy', False),
        ('eurjpy', False),
        ('gbpjpy', False),
        ('nzdjpy', False),
        ('usdjpy', False),
    ],
    'CHF': [
        # CHF as quote (inverse)
        ('audchf', False),
        ('cadchf', False),
        ('chfjpy', True),  # CHF is base
        ('eurchf', False),
        ('gbpchf', False),
        ('nzdchf', False),
        ('usdchf', False),
    ],
    'NZD': [
        # NZD as base
        ('nzdcad', True),
        ('nzdchf', True),
        ('nzdjpy', True),
        ('nzdusd', True),
        # NZD as quote (inverse)
        ('audnzd', False),
        ('eurnzd', False),
        ('gbpnzd', False),
    ],
}

# Date range: 2024-07 to 2025-06 (12 months)
START_DATE = datetime(2024, 7, 1)
END_DATE = datetime(2025, 7, 1)  # Exclusive

# Thread-safe counter
progress_lock = threading.Lock()
months_completed = 0
total_months = 12


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


def fetch_pair_data(conn, pair, start_time, end_time):
    """
    Fetch rate_index data for a specific pair and time range

    Args:
        conn: Database connection
        pair: Currency pair (e.g., 'eurusd')
        start_time: Start datetime
        end_time: End datetime

    Returns:
        tuple: (times array, rate_index array)
    """
    cur = conn.cursor()

    m1_table = sql.Identifier('bqx', f'm1_{pair}')
    query = sql.SQL("""
        SELECT time, rate_index
        FROM {}
        WHERE time >= %s AND time < %s
        ORDER BY time
    """).format(m1_table)

    cur.execute(query, (start_time, end_time))
    rows = cur.fetchall()
    cur.close()

    if not rows:
        return np.array([]), np.array([])

    times = np.array([r[0] for r in rows])
    rate_indices = np.array([float(r[1]) if r[1] is not None else 100.0 for r in rows])

    return times, rate_indices


def compute_currency_index(pair_data_list):
    """
    Compute currency strength index from multiple pairs

    Args:
        pair_data_list: List of tuples: (rate_index_array, is_base_currency)

    Returns:
        numpy array: Currency strength index
    """
    if not pair_data_list:
        return np.array([])

    # Geometric mean of normalized indices
    # For base currency: use rate_index as is
    # For quote currency: use inverse (200 - rate_index to keep scale)

    # Find minimum length across all arrays to ensure alignment
    min_len = min(len(rate_index) for rate_index, _ in pair_data_list)
    if min_len == 0:
        return np.array([])

    adjusted_indices = []
    for rate_index, is_base in pair_data_list:
        # Truncate to minimum length for alignment
        rate_index_aligned = rate_index[:min_len]

        if is_base:
            adjusted_indices.append(rate_index_aligned)
        else:
            # Inverse relationship: if pair goes up, quote currency is weaker
            adjusted_indices.append(200.0 - rate_index_aligned)

    # Geometric mean
    if len(adjusted_indices) > 0:
        # Stack arrays and compute geometric mean
        stacked = np.stack(adjusted_indices, axis=0)
        # Geometric mean: (product)^(1/n)
        currency_index = np.exp(np.mean(np.log(stacked + 1e-10), axis=0))  # Add small epsilon to avoid log(0)
        return currency_index
    else:
        return np.array([])


def compute_currency_indices_for_month(conn, year, month):
    """
    Compute all currency indices for a specific month

    Args:
        conn: Database connection
        year: Year (e.g., 2024)
        month: Month (e.g., 7)

    Returns:
        int: Number of rows processed
    """
    import time
    start_time = time.time()

    # Month boundaries
    month_start = datetime(year, month, 1)
    if month == 12:
        month_end = datetime(year + 1, 1, 1)
    else:
        month_end = datetime(year, month + 1, 1)

    # Fetch data for all relevant pairs
    print(f"  Fetching data for {year}-{month:02d}...")

    all_pair_data = {}
    reference_times = None

    # Fetch data for all currencies
    for currency in CURRENCY_GROUPS.keys():
        pair_data_list = []
        for pair, is_base in CURRENCY_GROUPS[currency]:
            times, rate_indices = fetch_pair_data(conn, pair, month_start, month_end)
            if len(times) > 0:
                pair_data_list.append((rate_indices, is_base))
                # Use first pair's times as reference
                if reference_times is None:
                    reference_times = times

        all_pair_data[currency] = pair_data_list

    if reference_times is None or len(reference_times) == 0:
        print(f"  ✗ No data found for {year}-{month:02d}")
        return 0

    # Compute indices for each currency
    print(f"  Computing indices...")
    currency_indices = {}
    for currency in CURRENCY_GROUPS.keys():
        currency_indices[currency] = compute_currency_index(all_pair_data[currency])

    # Ensure all indices have same length
    lengths = [len(idx) for idx in currency_indices.values()] + [len(reference_times)]
    min_len = min(lengths) if lengths else 0

    if min_len == 0:
        print(f"  ✗ Failed to compute indices for {year}-{month:02d}")
        return 0

    # Truncate all to minimum length
    reference_times = reference_times[:min_len]
    for currency in currency_indices.keys():
        currency_indices[currency] = currency_indices[currency][:min_len]

    # Insert into database
    cur = conn.cursor()

    indices_table = sql.Identifier('bqx', 'currency_indices')
    insert_query = sql.SQL("""
        INSERT INTO {} (
            ts_utc, usd_index, eur_index, gbp_index, aud_index,
            cad_index, jpy_index, chf_index, nzd_index
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ts_utc) DO UPDATE SET
            usd_index = EXCLUDED.usd_index,
            eur_index = EXCLUDED.eur_index,
            gbp_index = EXCLUDED.gbp_index,
            aud_index = EXCLUDED.aud_index,
            cad_index = EXCLUDED.cad_index,
            jpy_index = EXCLUDED.jpy_index,
            chf_index = EXCLUDED.chf_index,
            nzd_index = EXCLUDED.nzd_index
    """).format(indices_table)

    # Prepare insert data
    insert_data = []
    for i in range(min_len):
        insert_data.append((
            reference_times[i],
            float(currency_indices['USD'][i]),
            float(currency_indices['EUR'][i]),
            float(currency_indices['GBP'][i]),
            float(currency_indices['AUD'][i]),
            float(currency_indices['CAD'][i]),
            float(currency_indices['JPY'][i]),
            float(currency_indices['CHF'][i]),
            float(currency_indices['NZD'][i])
        ))

    cur.executemany(insert_query, insert_data)
    conn.commit()
    cur.close()

    elapsed = time.time() - start_time
    print(f"  ✓ Inserted {len(insert_data):,} rows in {elapsed:.1f}s")

    return len(insert_data)


def process_month_worker(year, month):
    """Worker function for threading (creates own DB connection)"""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        rows = compute_currency_indices_for_month(conn, year, month)

        # Update progress
        global months_completed
        with progress_lock:
            months_completed += 1
            progress_pct = (months_completed / total_months) * 100

        return {
            'year': year,
            'month': month,
            'rows': rows,
            'progress': progress_pct
        }
    finally:
        conn.close()


def main():
    """Main execution"""
    import time

    print("=" * 80)
    print("CURRENCY INDICES WORKER - TRACK 1 (STAGE 1.6.3)")
    print("=" * 80)
    print()
    print(f"Currency Indices: 8 (USD, EUR, GBP, AUD, CAD, JPY, CHF, NZD)")
    print(f"Months: {total_months}")
    print(f"Threads: 4")
    print(f"Date range: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print()
    print("Methodology: Compute strength index for each currency using ALL pairs where it appears")
    print(f"  - USD: {len(CURRENCY_GROUPS['USD'])} pairs")
    print(f"  - EUR: {len(CURRENCY_GROUPS['EUR'])} pairs")
    print(f"  - GBP: {len(CURRENCY_GROUPS['GBP'])} pairs")
    print(f"  - AUD: {len(CURRENCY_GROUPS['AUD'])} pairs")
    print(f"  - CAD: {len(CURRENCY_GROUPS['CAD'])} pairs")
    print(f"  - JPY: {len(CURRENCY_GROUPS['JPY'])} pairs")
    print(f"  - CHF: {len(CURRENCY_GROUPS['CHF'])} pairs")
    print(f"  - NZD: {len(CURRENCY_GROUPS['NZD'])} pairs")
    print()

    total_start = time.time()
    total_rows = 0

    # Get month ranges
    months = generate_month_ranges()

    print(f"Processing {len(months)} months with 4 threads...")
    print()

    # Execute with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all jobs
        futures = {executor.submit(process_month_worker, year, month): (year, month)
                   for year, month in months}

        # Process results as they complete
        for future in as_completed(futures):
            year, month = futures[future]
            try:
                result = future.result()
                total_rows += result['rows']

                print(f"[{result['year']}-{result['month']:02d}] {result['rows']:,} rows | "
                      f"Progress: {result['progress']:5.1f}%")

            except Exception as e:
                print(f"✗ ERROR [{year}-{month:02d}]: {e}")

    total_elapsed = time.time() - total_start

    # Final summary
    print()
    print("=" * 80)
    print("CURRENCY INDICES COMPUTATION COMPLETE")
    print("=" * 80)
    print(f"Total Rows: {total_rows:,}")
    print(f"Months Processed: {months_completed}/{total_months}")
    print(f"Total Time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} minutes)")
    print(f"Average Throughput: {total_rows/total_elapsed:.0f} rows/sec")
    print()
    print("Next Steps:")
    print("  1. Verify currency indices: SELECT * FROM bqx.currency_indices WHERE ts_utc >= '2024-07-01' LIMIT 10;")
    print("  2. Analyze currency correlations and divergences")
    print("  3. Proceed to Statistics & Bollinger Worker")
    print()


if __name__ == "__main__":
    main()
