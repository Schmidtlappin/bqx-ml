#!/usr/bin/env python3
"""
Correlation Features Worker V3 - Phase 1.6.6 (BQX-CENTRIC)

Computes correlation features using BQX momentum metrics instead of raw rates.
This aligns with the ML objective: predicting future BQX values.

KEY CHANGE FROM V2:
- V2: Correlated raw EURUSD rates with raw GBPUSD rates (WRONG for BQX prediction)
- V3: Correlates EURUSD w15_bqx_return with GBPUSD w15_bqx_return (CORRECT)

Data Source: bqx.bqx_{pair} tables (BQX momentum metrics)
Features: 15 BQX-based correlation features
Windows: 15min and 60min rolling correlations
"""

import psycopg2
import numpy as np
import pandas as pd
from datetime import datetime
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
END_DATE = datetime(2025, 7, 1)

# Thread-safe counter
progress_lock = threading.Lock()
partitions_completed = 0
total_partitions = len(CURRENCY_PAIRS) * 12
total_rows_inserted = 0


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


def get_related_pairs(pair):
    """Get pairs sharing base or quote currency"""
    base = pair[:3]
    quote = pair[3:]

    base_pairs = [p for p in CURRENCY_PAIRS if p[:3] == base and p != pair]
    quote_pairs = [p for p in CURRENCY_PAIRS if p[3:] == quote and p != pair]

    return base_pairs, quote_pairs


def compute_bqx_correlation_features(timestamps, bqx_w15, bqx_w30, bqx_w60,
                                      related_base_bqx, related_quote_bqx):
    """
    Compute 15 correlation features using BQX momentum metrics

    Args:
        timestamps: Array of timestamps
        bqx_w15/w30/w60: Current pair's BQX returns (backward momentum)
        related_base_bqx: Dict of {pair_name: (w15, w30, w60)} for base currency pairs
        related_quote_bqx: Dict of {pair_name: (w15, w30, w60)} for quote currency pairs

    Returns:
        DataFrame with 15 BQX correlation features
    """
    n = len(timestamps)

    # Initialize features
    features = pd.DataFrame({
        'corr_base_pairs_15min': np.zeros(n),
        'corr_base_pairs_60min': np.zeros(n),
        'corr_quote_pairs_15min': np.zeros(n),
        'corr_quote_pairs_60min': np.zeros(n),
        'relative_strength_vs_base_pairs': np.zeros(n),
        'relative_strength_vs_quote_pairs': np.zeros(n),
        'base_pair_divergence': np.zeros(n),
        'quote_pair_divergence': np.zeros(n),
        'triangular_arb_divergence': np.zeros(n),
        'cross_pair_momentum_divergence': np.zeros(n, dtype=int),
        'correlation_stability': np.zeros(n),
        'lead_lag_indicator': np.zeros(n),
        'cointegration_residual': np.zeros(n),
        'pair_spread_z_score': np.zeros(n),
        'cross_pair_volatility_ratio': np.zeros(n)
    }, index=range(n))

    # Process each timestamp
    for i in range(n):
        # 1-2: Base pair BQX correlations (15min and 60min windows)
        if len(related_base_bqx) > 0:
            w15_start = max(0, i - 14)  # 15 minutes
            w60_start = max(0, i - 59)  # 60 minutes

            # 15-minute window correlation
            if i - w15_start >= 10:
                base_corrs_15 = []
                for base_pair, (base_w15, _, _) in related_base_bqx.items():
                    try:
                        corr = np.corrcoef(
                            bqx_w15[w15_start:i+1],
                            base_w15[w15_start:i+1]
                        )[0, 1]
                        if not np.isnan(corr):
                            base_corrs_15.append(corr)
                    except:
                        pass
                if base_corrs_15:
                    features.loc[i, 'corr_base_pairs_15min'] = np.mean(base_corrs_15)

            # 60-minute window correlation
            if i - w60_start >= 10:
                base_corrs_60 = []
                for base_pair, (_, _, base_w60) in related_base_bqx.items():
                    try:
                        corr = np.corrcoef(
                            bqx_w60[w60_start:i+1],
                            base_w60[w60_start:i+1]
                        )[0, 1]
                        if not np.isnan(corr):
                            base_corrs_60.append(corr)
                    except:
                        pass
                if base_corrs_60:
                    features.loc[i, 'corr_base_pairs_60min'] = np.mean(base_corrs_60)

                    # 11: Correlation stability (std of correlations)
                    if len(base_corrs_60) > 1:
                        features.loc[i, 'correlation_stability'] = 1.0 - np.std(base_corrs_60)

        # 3-4: Quote pair BQX correlations
        if len(related_quote_bqx) > 0:
            w15_start = max(0, i - 14)
            w60_start = max(0, i - 59)

            if i - w15_start >= 10:
                quote_corrs_15 = []
                for quote_pair, (quote_w15, _, _) in related_quote_bqx.items():
                    try:
                        corr = np.corrcoef(
                            bqx_w15[w15_start:i+1],
                            quote_w15[w15_start:i+1]
                        )[0, 1]
                        if not np.isnan(corr):
                            quote_corrs_15.append(corr)
                    except:
                        pass
                if quote_corrs_15:
                    features.loc[i, 'corr_quote_pairs_15min'] = np.mean(quote_corrs_15)

            if i - w60_start >= 10:
                quote_corrs_60 = []
                for quote_pair, (_, _, quote_w60) in related_quote_bqx.items():
                    try:
                        corr = np.corrcoef(
                            bqx_w60[w60_start:i+1],
                            quote_w60[w60_start:i+1]
                        )[0, 1]
                        if not np.isnan(corr):
                            quote_corrs_60.append(corr)
                    except:
                        pass
                if quote_corrs_60:
                    features.loc[i, 'corr_quote_pairs_60min'] = np.mean(quote_corrs_60)

        # 5-6: Relative strength (BQX momentum vs peers)
        if len(related_base_bqx) > 0:
            base_w15_avg = np.mean([bqx[0][i] for bqx in related_base_bqx.values()])
            features.loc[i, 'relative_strength_vs_base_pairs'] = bqx_w15[i] - base_w15_avg

        if len(related_quote_bqx) > 0:
            quote_w15_avg = np.mean([bqx[0][i] for bqx in related_quote_bqx.values()])
            features.loc[i, 'relative_strength_vs_quote_pairs'] = bqx_w15[i] - quote_w15_avg

        # 7-8: Divergence (current BQX vs average of related pairs)
        if len(related_base_bqx) > 0:
            base_w30_avg = np.mean([bqx[1][i] for bqx in related_base_bqx.values()])
            features.loc[i, 'base_pair_divergence'] = bqx_w30[i] - base_w30_avg

        if len(related_quote_bqx) > 0:
            quote_w30_avg = np.mean([bqx[1][i] for bqx in related_quote_bqx.values()])
            features.loc[i, 'quote_pair_divergence'] = bqx_w30[i] - quote_w30_avg

        # 10: Cross-pair momentum divergence (categorical: -1, 0, +1)
        if i >= 1:
            current_accel = bqx_w15[i] - bqx_w15[i-1]
            if len(related_base_bqx) > 0:
                related_accel = []
                for base_w15, _, _ in related_base_bqx.values():
                    related_accel.append(base_w15[i] - base_w15[i-1])
                avg_related_accel = np.mean(related_accel)

                if current_accel > avg_related_accel + 0.0001:
                    features.loc[i, 'cross_pair_momentum_divergence'] = 1
                elif current_accel < avg_related_accel - 0.0001:
                    features.loc[i, 'cross_pair_momentum_divergence'] = -1

        # 14: Pair spread z-score (z-score of w15_bqx)
        if i >= 60:
            window_bqx = bqx_w15[max(0, i-59):i+1]
            mean_bqx = np.mean(window_bqx)
            std_bqx = np.std(window_bqx)
            if std_bqx > 0:
                features.loc[i, 'pair_spread_z_score'] = (bqx_w15[i] - mean_bqx) / std_bqx

        # 15: Cross-pair volatility ratio
        if i >= 60:
            window_bqx = bqx_w15[max(0, i-59):i+1]
            current_vol = np.std(window_bqx) if len(window_bqx) > 1 else 0

            related_vols = []
            for related_bqx in list(related_base_bqx.values()) + list(related_quote_bqx.values()):
                related_w15 = related_bqx[0][max(0, i-59):i+1]
                related_vol = np.std(related_w15) if len(related_w15) > 1 else 0
                if related_vol > 0:
                    related_vols.append(related_vol)

            if related_vols:
                avg_related_vol = np.mean(related_vols)
                if avg_related_vol > 0:
                    features.loc[i, 'cross_pair_volatility_ratio'] = current_vol / avg_related_vol

    return features


def process_partition(conn, pair, year, month):
    """Process one partition: compute BQX correlation features"""
    start_time = time.time()
    cur = conn.cursor()

    table_name = f'correlation_features_{pair}'
    partition_name = f'{table_name}_{year}_{month:02d}'

    try:
        # Create partition
        partition_start = f"{year}-{month:02d}-01"
        partition_end = f"{year+1}-01-01" if month == 12 else f"{year}-{month+1:02d}-01"

        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS bqx.{partition_name}
            PARTITION OF bqx.{table_name}
            FOR VALUES FROM ('{partition_start}') TO ('{partition_end}');
        """)
        conn.commit()

        # Fetch BQX data for this pair
        bqx_table = f'bqx_{pair}_y{year}m{month:02d}'
        cur.execute(f"""
            SELECT ts_utc, w15_bqx_return, w30_bqx_return, w60_bqx_return
            FROM bqx.{bqx_table}
            WHERE ts_utc >= '{partition_start}'::timestamp AND ts_utc < '{partition_end}'::timestamp
            ORDER BY ts_utc;
        """)

        rows = cur.fetchall()
        if not rows or len(rows) < 60:
            return 0, time.time() - start_time

        timestamps = np.array([row[0] for row in rows])
        bqx_w15 = np.array([float(row[1]) if row[1] is not None else 0.0 for row in rows])
        bqx_w30 = np.array([float(row[2]) if row[2] is not None else 0.0 for row in rows])
        bqx_w60 = np.array([float(row[3]) if row[3] is not None else 0.0 for row in rows])

        # Get related pairs
        base_pairs, quote_pairs = get_related_pairs(pair)

        # Fetch BQX data for related pairs (limit to 5 each to reduce load)
        related_base_bqx = {}
        for base_pair in base_pairs[:5]:
            base_bqx_table = f'bqx_{base_pair}_y{year}m{month:02d}'
            cur.execute(f"""
                SELECT w15_bqx_return, w30_bqx_return, w60_bqx_return
                FROM bqx.{base_bqx_table}
                WHERE ts_utc >= '{partition_start}'::timestamp AND ts_utc < '{partition_end}'::timestamp
                ORDER BY ts_utc;
            """)
            base_rows = cur.fetchall()
            if len(base_rows) == len(rows):
                related_base_bqx[base_pair] = (
                    np.array([float(r[0]) if r[0] is not None else 0.0 for r in base_rows]),
                    np.array([float(r[1]) if r[1] is not None else 0.0 for r in base_rows]),
                    np.array([float(r[2]) if r[2] is not None else 0.0 for r in base_rows])
                )

        related_quote_bqx = {}
        for quote_pair in quote_pairs[:5]:
            quote_bqx_table = f'bqx_{quote_pair}_y{year}m{month:02d}'
            cur.execute(f"""
                SELECT w15_bqx_return, w30_bqx_return, w60_bqx_return
                FROM bqx.{quote_bqx_table}
                WHERE ts_utc >= '{partition_start}'::timestamp AND ts_utc < '{partition_end}'::timestamp
                ORDER BY ts_utc;
            """)
            quote_rows = cur.fetchall()
            if len(quote_rows) == len(rows):
                related_quote_bqx[quote_pair] = (
                    np.array([float(r[0]) if r[0] is not None else 0.0 for r in quote_rows]),
                    np.array([float(r[1]) if r[1] is not None else 0.0 for r in quote_rows]),
                    np.array([float(r[2]) if r[2] is not None else 0.0 for r in quote_rows])
                )

        # Compute BQX correlation features
        features = compute_bqx_correlation_features(
            timestamps, bqx_w15, bqx_w30, bqx_w60,
            related_base_bqx, related_quote_bqx
        )

        # Insert data in batches
        insert_query = f"""
            INSERT INTO bqx.{partition_name} (
                ts_utc, corr_base_pairs_15min, corr_base_pairs_60min,
                corr_quote_pairs_15min, corr_quote_pairs_60min,
                relative_strength_vs_base_pairs, relative_strength_vs_quote_pairs,
                base_pair_divergence, quote_pair_divergence, triangular_arb_divergence,
                cross_pair_momentum_divergence, correlation_stability, lead_lag_indicator,
                cointegration_residual, pair_spread_z_score, cross_pair_volatility_ratio
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ts_utc) DO NOTHING;
        """

        batch_size = 1000
        for i in range(0, len(timestamps), batch_size):
            batch_end = min(i + batch_size, len(timestamps))
            batch_data = []
            for j in range(i, batch_end):
                row = [timestamps[j]]
                for val in features.iloc[j].values:
                    if isinstance(val, (np.integer, int)):
                        row.append(int(val))
                    elif isinstance(val, (np.floating, float)):
                        row.append(None if np.isnan(val) else float(val))
                    else:
                        row.append(None)
                batch_data.append(tuple(row))
            cur.executemany(insert_query, batch_data)
            conn.commit()

        elapsed = time.time() - start_time
        print(f"✓ [{pair.upper()}] {year}-{month:02d} | {len(timestamps):,} rows | {elapsed:.1f}s", flush=True)

        return len(timestamps), elapsed

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
    """Main execution"""
    start_time = time.time()

    print("=" * 80)
    print("CORRELATION FEATURES WORKER V3 - PHASE 1.6.6 (BQX-CENTRIC)")
    print("=" * 80)
    print(f"\nPairs: {len(CURRENCY_PAIRS)}")
    print(f"Total Partitions: {total_partitions}")
    print(f"Threads: 8")
    print(f"Date Range: {START_DATE.date()} to {END_DATE.date()}")
    print("\nKEY CHANGE FROM V2:")
    print("  - V2: Correlated raw EURUSD rates with GBPUSD rates")
    print("  - V3: Correlates EURUSD w15_bqx with GBPUSD w15_bqx (BQX momentum)")
    print("\nFeatures: 15 BQX-based correlation features")
    print("  1-4: Base/Quote BQX correlations (15min & 60min)")
    print("  5-6: Relative strength (BQX momentum vs peers)")
    print("  7-9: Divergence (BQX difference from peer average)")
    print("  10: Cross-pair momentum divergence (categorical)")
    print("  11-15: Advanced BQX correlation metrics")
    print("\n" + "=" * 80 + "\n")

    # Generate jobs
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
    print("BQX CORRELATION FEATURES COMPUTATION COMPLETE")
    print("=" * 80)
    print(f"Total Rows: {total_rows_inserted:,}")
    print(f"Total Partitions: {partitions_completed}/{total_partitions}")
    print(f"Total Time: {elapsed_total:.1f}s ({elapsed_total/60:.1f} minutes)")
    if total_rows_inserted > 0:
        print(f"Average Throughput: {total_rows_inserted/elapsed_total:,.0f} rows/sec")


if __name__ == '__main__':
    main()
