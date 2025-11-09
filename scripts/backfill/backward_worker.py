#!/usr/bin/env python3
"""
Backward Analysis Worker
Computes backward-looking (BQX) metrics for forex pairs using past M1 data
"""

import os
import sys
import time
import psycopg2
import numpy as np
from datetime import datetime

# Windows configuration (BQX uses shorter, finer granularity windows)
WINDOWS = [15, 30, 45, 60, 75]
MAX_WINDOW = max(WINDOWS)  # 75 minutes

# Aurora credentials (Trillium BQX cluster)
DB_HOST = "trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com"
DB_PORT = 5432
DB_NAME = "bqx"
DB_USER = "postgres"
DB_PASSWORD = "BQX_Aurora_2025_Secure"


def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode="require",
    )


def compute_backward_metrics(rates, window_size, current_idx):
    """
    Compute backward-looking metrics for a given window

    Args:
        rates: numpy array of historical rates
        window_size: number of minutes in window (15, 30, 45, 60, 75)
        current_idx: index of current timestamp in rates array

    Returns:
        dict with backward metrics or None if insufficient past data
    """
    if current_idx < window_size:
        # Insufficient past data (edge effect)
        return None

    rate_t = rates[current_idx]
    past_rates = rates[current_idx - window_size : current_idx]  # rate(t-window) to rate(t-1)

    # Cumulative return: Σ(i=1 to W)[rate(t-i) - rate(t)] / rate(t)
    cumulative_diffs = past_rates - rate_t
    bqx_return = np.sum(cumulative_diffs) / rate_t

    # Statistical measures of past rates
    bqx_max = np.max(past_rates)
    bqx_min = np.min(past_rates)
    bqx_avg = np.mean(past_rates)
    bqx_stdev = np.std(past_rates, ddof=1) if len(past_rates) > 1 else 0.0

    # Endpoint return: (rate(t-window) - rate(t)) / rate(t)
    bqx_endpoint = (past_rates[0] - rate_t) / rate_t

    return {
        "bqx_return": float(bqx_return),
        "bqx_max": float(bqx_max),
        "bqx_min": float(bqx_min),
        "bqx_avg": float(bqx_avg),
        "bqx_stdev": float(bqx_stdev),
        "bqx_endpoint": float(bqx_endpoint),
    }


def compute_aggregate_metrics(rates, current_idx):
    """
    Compute aggregate metrics using w75 window (longest window)

    Args:
        rates: numpy array of historical rates
        current_idx: index of current timestamp

    Returns:
        dict with aggregate metrics or None if insufficient past data
    """
    if current_idx < 75:  # Need 75 past rates
        return None

    rate_t = rates[current_idx]
    past_rates = rates[current_idx - 75 : current_idx]  # rate(t-75) to rate(t-1)

    # Cumulative return for w75
    cumulative_diffs = past_rates - rate_t
    agg_bqx_return = np.sum(cumulative_diffs) / rate_t

    # Statistical measures
    agg_bqx_max = np.max(past_rates)
    agg_bqx_min = np.min(past_rates)
    agg_bqx_avg = np.mean(past_rates)
    agg_bqx_stdev = np.std(past_rates, ddof=1)

    # Range and volatility
    agg_bqx_range = (agg_bqx_max - agg_bqx_min) / rate_t
    agg_bqx_volatility = agg_bqx_stdev / rate_t

    return {
        "agg_bqx_return": float(agg_bqx_return),
        "agg_bqx_max": float(agg_bqx_max),
        "agg_bqx_min": float(agg_bqx_min),
        "agg_bqx_avg": float(agg_bqx_avg),
        "agg_bqx_stdev": float(agg_bqx_stdev),
        "agg_bqx_range": float(agg_bqx_range),
        "agg_bqx_volatility": float(agg_bqx_volatility),
    }


def process_backward_analysis(pair, start_date, end_date):
    """
    Process backward analysis for a single pair and date range

    Args:
        pair: forex pair (e.g., 'eurusd')
        start_date: start of month (e.g., '2024-07-01')
        end_date: end of month (e.g., '2024-08-01')

    Returns:
        Number of rows inserted
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch M1 data including past lookback
    # Need to fetch before start_date to compute backward metrics
    cur.execute(
        f"""
        SELECT time, close as rate
        FROM bqx.m1_{pair}
        WHERE time >= %s::timestamp - interval '{MAX_WINDOW} minutes' AND time < %s
        ORDER BY time
    """,
        (start_date, end_date),
    )

    rows = cur.fetchall()

    if not rows:
        cur.close()
        conn.close()
        return 0

    # Convert to arrays
    timestamps = [row[0] for row in rows]
    rates = np.array([row[1] for row in rows])

    # Parse dates for comparison
    start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")

    # Process each timestamp in the target month
    inserts = []

    for i, ts in enumerate(timestamps):
        # Only process timestamps within the target month
        if ts < start_date_dt or ts >= end_date_dt:
            continue

        # Base values
        rate_t = rates[i]

        # Compute metrics for each window
        metrics = {"ts_utc": ts, "rate": rate_t}

        has_data = False
        for window in WINDOWS:
            result = compute_backward_metrics(rates, window, i)

            if result:
                has_data = True
                for key, value in result.items():
                    metrics[f"w{window}_{key}"] = value
            else:
                # Set window fields to NULL (edge effect - insufficient past data)
                for key in [
                    "bqx_return",
                    "bqx_max",
                    "bqx_min",
                    "bqx_avg",
                    "bqx_stdev",
                    "bqx_endpoint",
                ]:
                    metrics[f"w{window}_{key}"] = None

        # Compute aggregate metrics
        agg_result = compute_aggregate_metrics(rates, i)
        if agg_result:
            metrics.update(agg_result)
        else:
            # Set aggregate fields to NULL
            for key in [
                "agg_bqx_return",
                "agg_bqx_max",
                "agg_bqx_min",
                "agg_bqx_avg",
                "agg_bqx_stdev",
                "agg_bqx_range",
                "agg_bqx_volatility",
            ]:
                metrics[key] = None

        if has_data:
            inserts.append(metrics)

    # Batch insert
    if inserts:
        # Build column lists
        columns = ["ts_utc", "rate"]
        for window in WINDOWS:
            columns.extend(
                [
                    f"w{window}_bqx_return",
                    f"w{window}_bqx_max",
                    f"w{window}_bqx_min",
                    f"w{window}_bqx_avg",
                    f"w{window}_bqx_stdev",
                    f"w{window}_bqx_endpoint",
                ]
            )
        columns.extend(
            [
                "agg_bqx_return",
                "agg_bqx_max",
                "agg_bqx_min",
                "agg_bqx_avg",
                "agg_bqx_stdev",
                "agg_bqx_range",
                "agg_bqx_volatility",
            ]
        )

        # Build INSERT statement with ON CONFLICT DO UPDATE
        placeholders = ", ".join(["%s"] * len(columns))
        col_str = ", ".join(columns)
        update_str = ", ".join(
            [f"{col} = EXCLUDED.{col}" for col in columns if col != "ts_utc"]
        )

        insert_sql = f"""
            INSERT INTO bqx.bqx_{pair} ({col_str})
            VALUES ({placeholders})
            ON CONFLICT (ts_utc) DO UPDATE SET {update_str}
        """

        # Execute batch insert
        values = []
        for row in inserts:
            values.append(tuple(row.get(col) for col in columns))

        cur.executemany(insert_sql, values)
        conn.commit()

    rows_inserted = len(inserts)

    cur.close()
    conn.close()

    return rows_inserted


def main():
    """Main execution - process all pairs and months"""

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

    print("=" * 80)
    print("BQX Backward Analysis - Historical Data Population")
    print("=" * 80)
    print(f"Pairs: {len(PAIRS)}")
    print(f"Months: {len(MONTHS)}")
    print(f"Total jobs: {len(PAIRS) * len(MONTHS)}")
    print(f"Windows: {WINDOWS}")
    print("=" * 80)

    total_rows = 0
    total_jobs = len(PAIRS) * len(MONTHS)
    completed_jobs = 0

    start_time = time.time()

    for pair in PAIRS:
        print(f"\n{'=' * 80}")
        print(f"Processing: {pair.upper()}")
        print(f"{'=' * 80}")

        pair_rows = 0
        pair_start = time.time()

        for start_date, end_date in MONTHS:
            job_start = time.time()

            try:
                rows = process_backward_analysis(pair, start_date, end_date)
                job_elapsed = time.time() - job_start

                pair_rows += rows
                total_rows += rows
                completed_jobs += 1

                progress_pct = (completed_jobs / total_jobs) * 100

                print(f"  [{start_date[:7]}] {rows:6,} rows | {job_elapsed:5.1f}s | Progress: {progress_pct:5.1f}%")

            except Exception as e:
                print(f"  [{start_date[:7]}] ERROR: {e}")
                completed_jobs += 1

        pair_elapsed = time.time() - pair_start
        print(f"\n  {pair.upper()} Total: {pair_rows:,} rows in {pair_elapsed:.1f}s")

    total_elapsed = time.time() - start_time

    print("\n" + "=" * 80)
    print("BACKFILL COMPLETE")
    print("=" * 80)
    print(f"Total rows inserted: {total_rows:,}")
    print(f"Total time: {total_elapsed / 60:.1f} minutes")
    print(f"Average: {total_rows / total_elapsed:.0f} rows/sec")
    print("=" * 80)


if __name__ == "__main__":
    main()
