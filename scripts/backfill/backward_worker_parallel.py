#!/usr/bin/env python3
"""
Parallel Backward Analysis Worker
Computes BQX metrics for all 28 pairs using multiprocessing
Estimated completion: 45-90 minutes (vs 7 hours sequential)
"""

import sys
import time
import multiprocessing as mp
from datetime import datetime

# Add backward_worker to path
sys.path.insert(0, '/home/ubuntu/Robkei-Ring/sandbox/scripts')
from backward_worker import process_backward_analysis

# Preferred forex pairs (28 total)
PAIRS = [
    'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
    'cadchf', 'cadjpy', 'chfjpy',
    'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
    'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
    'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
    'usdcad', 'usdchf', 'usdjpy'
]

# Monthly partitions (2024-07 through 2025-06)
MONTHS = [
    ('2024-07-01', '2024-08-01'),
    ('2024-08-01', '2024-09-01'),
    ('2024-09-01', '2024-10-01'),
    ('2024-10-01', '2024-11-01'),
    ('2024-11-01', '2024-12-01'),
    ('2024-12-01', '2025-01-01'),
    ('2025-01-01', '2025-02-01'),
    ('2025-02-01', '2025-03-01'),
    ('2025-03-01', '2025-04-01'),
    ('2025-04-01', '2025-05-01'),
    ('2025-05-01', '2025-06-01'),
    ('2025-06-01', '2025-07-01'),
]


def process_pair_worker(pair):
    """
    Process all months for a single pair
    This function runs in a separate process
    """
    worker_id = mp.current_process().name
    pair_start = time.time()
    pair_rows = 0

    print(f"[{worker_id}] Starting {pair.upper()}")

    for i, (start_date, end_date) in enumerate(MONTHS, 1):
        try:
            month_start = time.time()
            rows = process_backward_analysis(pair, start_date, end_date)
            month_elapsed = time.time() - month_start

            pair_rows += rows
            print(f"[{worker_id}] {pair.upper()} [{start_date[:7]}] {rows:6,} rows | {month_elapsed:5.1f}s | {i}/12 months")

        except Exception as e:
            print(f"[{worker_id}] {pair.upper()} [{start_date[:7]}] ERROR: {e}")

    pair_elapsed = time.time() - pair_start
    print(f"[{worker_id}] ✓ {pair.upper()} COMPLETE: {pair_rows:,} rows in {pair_elapsed:.1f}s")

    return {
        'pair': pair,
        'rows': pair_rows,
        'elapsed': pair_elapsed
    }


def main():
    print("=" * 80)
    print("BQX Backward Analysis - PARALLEL PROCESSING")
    print("=" * 80)
    print(f"Pairs: {len(PAIRS)}")
    print(f"Months per pair: {len(MONTHS)}")
    print(f"Total jobs: {len(PAIRS) * len(MONTHS)}")

    # Determine number of workers
    cpu_count = mp.cpu_count()
    # Use 75% of CPUs, minimum 4, maximum 8
    num_workers = min(max(int(cpu_count * 0.75), 4), 8)

    print(f"CPUs available: {cpu_count}")
    print(f"Workers: {num_workers}")
    print("=" * 80)

    start_time = time.time()

    # Create pool and process pairs in parallel
    with mp.Pool(processes=num_workers) as pool:
        results = pool.map(process_pair_worker, PAIRS)

    total_elapsed = time.time() - start_time

    # Aggregate results
    total_rows = sum(r['rows'] for r in results)
    avg_time_per_pair = sum(r['elapsed'] for r in results) / len(results)

    print("\n" + "=" * 80)
    print("PARALLEL BACKFILL COMPLETE")
    print("=" * 80)
    print(f"Total pairs processed: {len(results)}")
    print(f"Total rows inserted: {total_rows:,}")
    print(f"Total wall time: {total_elapsed / 60:.1f} minutes")
    print(f"Average per pair: {avg_time_per_pair:.1f}s")
    print(f"Processing rate: {total_rows / total_elapsed:.0f} rows/sec")
    print(f"Speedup: {avg_time_per_pair * len(PAIRS) / total_elapsed:.1f}x")
    print("=" * 80)

    # Print per-pair summary
    print("\nPer-Pair Summary:")
    print("-" * 80)
    print(f"{'Pair':<8} {'Rows':>12} {'Time (s)':>10} {'Rate (rows/s)':>15}")
    print("-" * 80)

    for result in sorted(results, key=lambda x: x['pair']):
        pair = result['pair'].upper()
        rows = result['rows']
        elapsed = result['elapsed']
        rate = rows / elapsed if elapsed > 0 else 0
        print(f"{pair:<8} {rows:>12,} {elapsed:>10.1f} {rate:>15.0f}")

    print("-" * 80)


if __name__ == "__main__":
    # Required for multiprocessing on some systems
    mp.set_start_method('spawn', force=True)
    main()
