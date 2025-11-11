#!/usr/bin/env python3
"""
Regression Analysis Worker (Index-Based)
Computes regression (REG) features using rate_index instead of absolute rates

CHANGES FROM ORIGINAL:
- Uses rate_index from m1_* tables (populated in Stage 1.5.2)
- Outputs regression features in index space (around 100)
- Removes *_norm fields (no longer needed with rate_index)
- Schema: 75 fields → 57 fields (24% reduction)
"""

import os
import sys
import time
import psycopg2
import numpy as np
from datetime import datetime
from scipy import stats

# Regression windows configuration
WINDOWS = [60, 90, 150, 240, 390, 630]
MAX_WINDOW = max(WINDOWS)  # 630 minutes

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


def fit_quadratic_regression(rate_indexes, window_size, current_idx):
    """
    Fit quadratic regression on historical rate_index data

    Model: y = a*x² + b*x + c
    where y = rate_index values, x = time points

    Args:
        rate_indexes: numpy array of historical rate_index values (around 100)
        window_size: number of minutes in window (60, 90, 150, 240, 390, 630)
        current_idx: index of current timestamp in rate_indexes array

    Returns:
        dict with regression metrics or None if insufficient past data
    """
    if current_idx < window_size:
        # Insufficient past data (edge effect)
        return None

    # Get past rate_index values for this window
    past_indexes = rate_indexes[current_idx - window_size : current_idx]

    if len(past_indexes) < 3:
        # Need at least 3 points for quadratic regression
        return None

    # Create time points (0, 1, 2, ..., window_size-1)
    x = np.arange(len(past_indexes))
    y = past_indexes

    try:
        # Fit quadratic polynomial: y = a*x² + b*x + c
        # Returns coefficients [a, b, c] from highest to lowest degree
        coeffs = np.polyfit(x, y, deg=2)
        a_coef, b_coef, c_coef = coeffs[0], coeffs[1], coeffs[2]

        # Calculate terms at end of window (x = window_size - 1)
        x_end = len(past_indexes) - 1
        a_term = a_coef * (x_end ** 2)
        b_term = b_coef * x_end

        # Predicted value at end of window
        yhat_end = a_term + b_term + c_coef

        # Residual at end of window
        resid_end = y[-1] - yhat_end

        # Calculate R² and RMSE
        y_pred = np.polyval(coeffs, x)

        # R-squared
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # RMSE
        rmse = np.sqrt(np.mean((y - y_pred) ** 2))

        return {
            "a_coef": float(a_coef),
            "b_coef": float(b_coef),
            "c_coef": float(c_coef),
            "a_term": float(a_term),
            "b_term": float(b_term),
            "r2": float(r2),
            "rmse": float(rmse),
            "yhat_end": float(yhat_end),
            "resid_end": float(resid_end),
            # NOTE: quad_norm, lin_norm, resid_norm REMOVED (not needed with index)
        }

    except Exception as e:
        # Regression failed (e.g., singular matrix)
        return None


def process_regression_analysis(pair, start_date, end_date):
    """
    Process regression analysis for a single pair and date range using rate_index

    Args:
        pair: forex pair (e.g., 'eurusd')
        start_date: start of month (e.g., '2024-07-01')
        end_date: end of month (e.g., '2024-08-01')

    Returns:
        Number of rows inserted
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch M1 rate_index data including past lookback
    # CHANGED: Fetch rate_index instead of close
    cur.execute(
        f"""
        SELECT time, rate_index
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
    # Convert Decimal to float to avoid numpy polyfit issues
    rate_indexes = np.array([float(row[1]) for row in rows])

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
        index_t = rate_indexes[i]

        # Compute regression for each window
        # Convert numpy scalar to Python float to avoid psycopg2 type issues
        metrics = {"ts_utc": ts, "rate_index": float(index_t)}

        has_data = False
        for window in WINDOWS:
            result = fit_quadratic_regression(rate_indexes, window, i)

            if result:
                has_data = True
                for key, value in result.items():
                    metrics[f"w{window}_{key}"] = value
            else:
                # Set window fields to NULL (edge effect - insufficient past data)
                for key in [
                    "a_coef", "b_coef", "c_coef",
                    "a_term", "b_term",
                    "r2", "rmse",
                    "yhat_end", "resid_end"
                ]:
                    metrics[f"w{window}_{key}"] = None

        if has_data:
            inserts.append(metrics)

    # Batch insert
    if inserts:
        # Build column lists (NO _norm fields)
        columns = ["ts_utc", "rate_index"]
        for window in WINDOWS:
            columns.extend([
                f"w{window}_a_coef",
                f"w{window}_b_coef",
                f"w{window}_c_coef",
                f"w{window}_a_term",
                f"w{window}_b_term",
                f"w{window}_r2",
                f"w{window}_rmse",
                f"w{window}_yhat_end",
                f"w{window}_resid_end",
            ])

        # Build INSERT statement with ON CONFLICT DO UPDATE
        placeholders = ", ".join(["%s"] * len(columns))
        col_str = ", ".join(columns)
        update_str = ", ".join(
            [f"{col} = EXCLUDED.{col}" for col in columns if col != "ts_utc"]
        )

        insert_sql = f"""
            INSERT INTO bqx.reg_{pair} ({col_str})
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

    # Monthly partitions (2024-07 through 2025-10)
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
        ('2025-07-01', '2025-08-01'),
        ('2025-08-01', '2025-09-01'),
        ('2025-09-01', '2025-10-01'),
        ('2025-10-01', '2025-11-01'),
    ]

    print("=" * 80)
    print("REG Regression Analysis - INDEX-BASED Historical Data Population")
    print("=" * 80)
    print(f"Pairs: {len(PAIRS)}")
    print(f"Months: {len(MONTHS)}")
    print(f"Total jobs: {len(PAIRS) * len(MONTHS)}")
    print(f"Windows: {WINDOWS}")
    print("=" * 80)
    print("USING RATE_INDEX (not absolute rates)")
    print("REMOVED: *_norm fields (18 fields total)")
    print("Schema: 75 fields → 57 fields (24% reduction)")
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
                rows = process_regression_analysis(pair, start_date, end_date)
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
    print("BACKFILL COMPLETE (INDEX-BASED, NO _norm fields)")
    print("=" * 80)
    print(f"Total rows inserted: {total_rows:,}")
    print(f"Total time: {total_elapsed / 60:.1f} minutes")
    print(f"Average: {total_rows / total_elapsed:.0f} rows/sec")
    print("=" * 80)


if __name__ == "__main__":
    main()
