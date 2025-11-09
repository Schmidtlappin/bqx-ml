#!/usr/bin/env python3
"""
Threaded Backward Analysis Worker
Uses threading to process multiple pairs concurrently
Estimated completion: 1-2 hours with 6 threads
"""

import sys
import time
import threading
from queue import Queue
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

# Shared state
results_lock = threading.Lock()
results = []
jobs_completed = 0
total_jobs = len(PAIRS) * len(MONTHS)


def worker_thread(thread_id, job_queue):
    """
    Worker thread that processes jobs from the queue
    """
    global jobs_completed

    while True:
        try:
            job = job_queue.get(timeout=1)
        except:
            # Queue is empty
            break

        pair, start_date, end_date = job
        month_label = start_date[:7]

        try:
            start_time = time.time()
            rows = process_backward_analysis(pair, start_date, end_date)
            elapsed = time.time() - start_time

            with results_lock:
                jobs_completed += 1
                progress_pct = (jobs_completed / total_jobs) * 100
                results.append({
                    'pair': pair,
                    'month': month_label,
                    'rows': rows,
                    'elapsed': elapsed
                })
                print(f"[T{thread_id:02d}] {pair.upper()} [{month_label}] {rows:6,} rows | {elapsed:5.1f}s | Progress: {progress_pct:5.1f}%")

        except Exception as e:
            with results_lock:
                jobs_completed += 1
                print(f"[T{thread_id:02d}] {pair.upper()} [{month_label}] ERROR: {e}")

        finally:
            job_queue.task_done()


def main():
    print("=" * 80)
    print("BQX Backward Analysis - THREADED CONCURRENT PROCESSING")
    print("=" * 80)
    print(f"Pairs: {len(PAIRS)}")
    print(f"Months per pair: {len(MONTHS)}")
    print(f"Total jobs: {total_jobs}")

    # Use 6 threads for optimal Aurora connection usage
    num_threads = 6
    print(f"Threads: {num_threads}")
    print("=" * 80)
    print()

    # Create job queue
    job_queue = Queue()

    # Enqueue all jobs (pair, month combinations)
    for pair in PAIRS:
        for start_date, end_date in MONTHS:
            job_queue.put((pair, start_date, end_date))

    # Start threads
    threads = []
    start_time = time.time()

    for i in range(num_threads):
        t = threading.Thread(target=worker_thread, args=(i, job_queue))
        t.daemon = True
        t.start()
        threads.append(t)

    # Wait for all jobs to complete
    job_queue.join()

    # Wait for all threads to finish
    for t in threads:
        t.join()

    total_elapsed = time.time() - start_time

    # Aggregate results
    total_rows = sum(r['rows'] for r in results)
    pair_totals = {}

    for r in results:
        pair = r['pair']
        if pair not in pair_totals:
            pair_totals[pair] = 0
        pair_totals[pair] += r['rows']

    print("\n" + "=" * 80)
    print("THREADED BACKFILL COMPLETE")
    print("=" * 80)
    print(f"Total jobs: {len(results)}/{total_jobs}")
    print(f"Total rows inserted: {total_rows:,}")
    print(f"Total time: {total_elapsed / 60:.1f} minutes")
    print(f"Processing rate: {total_rows / total_elapsed:.0f} rows/sec")
    print("=" * 80)

    # Print per-pair summary
    print("\nPer-Pair Summary:")
    print("-" * 80)
    print(f"{'Pair':<8} {'Rows':>12} {'Months':>8}")
    print("-" * 80)

    for pair in sorted(PAIRS):
        if pair in pair_totals:
            rows = pair_totals[pair]
            months = sum(1 for r in results if r['pair'] == pair)
            print(f"{pair.upper():<8} {rows:>12,} {months:>8}/12")

    print("-" * 80)


if __name__ == "__main__":
    main()
