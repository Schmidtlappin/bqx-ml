#!/usr/bin/env python3
"""
OHLC Index Backfill Worker - Stage 1.6.1

Backfills high_index, low_index, open_index columns in all M1 tables.
Formula: {ohlc}_index = ({ohlc} / baseline_rate) * 100

Where baseline_rate = first rate in each monthly partition.

Strategy:
- Process all 28 currency pairs sequentially
- For each pair, process 12 months (2024-07 to 2025-06)
- Total: 336 partition updates (28 pairs × 12 months)
- Low CPU impact: Sequential updates, no complex calculations
- Estimated time: 2-3 hours

Usage:
    python3 scripts/backfill/ohlc_index_backfill_worker.py
"""

import psycopg2
from psycopg2 import sql
from datetime import datetime, timedelta
import time

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


def get_partition_baseline(conn, pair, year, month):
    """
    Get baseline rate for a partition (first rate in the partition)

    Args:
        conn: Database connection
        pair: Currency pair (e.g., 'eurusd')
        year: Year (e.g., 2024)
        month: Month (e.g., 7)

    Returns:
        float: Baseline rate for the partition
    """
    cur = conn.cursor()

    table_name = sql.Identifier('bqx', f'm1_{pair}')
    query = sql.SQL("""
        SELECT rate
        FROM {}
        WHERE time >= %s AND time < %s
        ORDER BY time
        LIMIT 1
    """).format(table_name)

    # Partition start and end dates
    partition_start = datetime(year, month, 1)
    if month == 12:
        partition_end = datetime(year + 1, 1, 1)
    else:
        partition_end = datetime(year, month + 1, 1)

    cur.execute(query, (partition_start, partition_end))
    result = cur.fetchone()
    cur.close()

    if result is None:
        raise ValueError(f"No data found for {pair} in {year}-{month:02d}")

    return float(result[0])


def backfill_ohlc_index(conn, pair, year, month):
    """
    Backfill OHLC index columns for a specific partition

    Args:
        conn: Database connection
        pair: Currency pair
        year: Year
        month: Month

    Returns:
        int: Number of rows updated
    """
    start_time = time.time()

    # Get baseline rate for this partition
    baseline_rate = get_partition_baseline(conn, pair, year, month)

    cur = conn.cursor()

    # Update query: Calculate OHLC index values
    # Formula: {ohlc}_index = ({ohlc} / baseline_rate) * 100
    table_name = sql.Identifier('bqx', f'm1_{pair}')
    query = sql.SQL("""
        UPDATE {}
        SET
            high_index = (high / %s) * 100,
            low_index = (low / %s) * 100,
            open_index = (open / %s) * 100
        WHERE time >= %s AND time < %s
    """).format(table_name)

    # Partition boundaries
    partition_start = datetime(year, month, 1)
    if month == 12:
        partition_end = datetime(year + 1, 1, 1)
    else:
        partition_end = datetime(year, month + 1, 1)

    # Execute update
    cur.execute(query, (
        baseline_rate, baseline_rate, baseline_rate,
        partition_start, partition_end
    ))

    rows_updated = cur.rowcount
    conn.commit()
    cur.close()

    elapsed = time.time() - start_time

    return rows_updated, elapsed, baseline_rate


def verify_ohlc_index(conn, pair, year, month):
    """
    Verify OHLC index calculations for a partition

    Args:
        conn: Database connection
        pair: Currency pair
        year: Year
        month: Month

    Returns:
        bool: True if verification passed
    """
    cur = conn.cursor()

    # Check if any OHLC index values are NULL
    table_name = sql.Identifier('bqx', f'm1_{pair}')
    query = sql.SQL("""
        SELECT COUNT(*) as total_rows,
               COUNT(high_index) as high_count,
               COUNT(low_index) as low_count,
               COUNT(open_index) as open_count
        FROM {}
        WHERE time >= %s AND time < %s
    """).format(table_name)

    partition_start = datetime(year, month, 1)
    if month == 12:
        partition_end = datetime(year + 1, 1, 1)
    else:
        partition_end = datetime(year, month + 1, 1)

    cur.execute(query, (partition_start, partition_end))
    result = cur.fetchone()
    cur.close()

    total, high_count, low_count, open_count = result

    if total == 0:
        return False  # No data in partition

    # All counts should equal total (no NULLs)
    return high_count == total and low_count == total and open_count == total


def main():
    """Main backfill execution"""

    print("=" * 80)
    print("OHLC INDEX BACKFILL WORKER - STAGE 1.6.1")
    print("=" * 80)
    print()
    print(f"Pairs: {len(CURRENCY_PAIRS)}")
    print(f"Months per pair: {len(generate_month_ranges())}")
    print(f"Total partitions: {len(CURRENCY_PAIRS) * len(generate_month_ranges())}")
    print(f"Date range: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print()

    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)

    total_start = time.time()
    total_rows = 0
    partitions_processed = 0
    partitions_total = len(CURRENCY_PAIRS) * len(generate_month_ranges())

    # Process each currency pair
    for pair_idx, pair in enumerate(CURRENCY_PAIRS, 1):
        print("=" * 80)
        print(f"Processing: {pair.upper()} ({pair_idx}/{len(CURRENCY_PAIRS)})")
        print("=" * 80)

        pair_start = time.time()
        pair_rows = 0

        # Process each month
        for year, month in generate_month_ranges():
            try:
                # Backfill OHLC index
                rows_updated, elapsed, baseline = backfill_ohlc_index(conn, pair, year, month)

                # Verify
                verified = verify_ohlc_index(conn, pair, year, month)

                pair_rows += rows_updated
                total_rows += rows_updated
                partitions_processed += 1

                progress_pct = (partitions_processed / partitions_total) * 100

                status = "✓" if verified else "✗"
                print(f"  [{year}-{month:02d}] {rows_updated:,} rows | {elapsed:.1f}s | "
                      f"baseline={baseline:.5f} | {status} | Progress: {progress_pct:5.1f}%")

            except Exception as e:
                print(f"  ✗ ERROR [{year}-{month:02d}]: {e}")
                conn.rollback()

        pair_elapsed = time.time() - pair_start
        print()
        print(f"  {pair.upper()} Total: {pair_rows:,} rows in {pair_elapsed:.1f}s")
        print()

    total_elapsed = time.time() - total_start

    # Final summary
    print()
    print("=" * 80)
    print("BACKFILL COMPLETE")
    print("=" * 80)
    print(f"Total Rows Updated: {total_rows:,}")
    print(f"Total Partitions: {partitions_processed}/{partitions_total}")
    print(f"Total Time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} minutes)")
    print(f"Average Throughput: {total_rows/total_elapsed:.0f} rows/sec")
    print()
    print("Next Steps:")
    print("  1. Verify OHLC index columns: SELECT * FROM bqx.m1_eurusd LIMIT 10;")
    print("  2. Check for NULL values: See verification queries in SQL script")
    print("  3. Begin Track 4: Blocked Features Computation (45 technical indicators)")
    print()

    conn.close()


if __name__ == "__main__":
    main()
