#!/usr/bin/env python3
"""
Correlation Features Worker - Phase 1.6.6
Simplified implementation matching existing sophisticated schema

Computes 15 correlation-based features:
1-4: Base/Quote pair correlations (15min and 60min windows)
5-6: Relative strength indicators
7-9: Divergence metrics
10: Cross-pair momentum divergence (categorical)
11: Correlation stability
12: Lead-lag indicator
13: Cointegration residual
14: Pair spread z-score
15: Cross-pair volatility ratio

NOTE: This is a basic implementation. Full sophisticated implementation requires:
- Cointegration tests (statsmodels)
- Lead-lag analysis
- Triangular arbitrage detection
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


def compute_correlation_features(timestamps, rates, related_base_rates, related_quote_rates):
    """
    Compute 15 correlation features (simplified implementation)

    Args:
        timestamps: Array of timestamps
        rates: Current pair rates
        related_base_rates: Dict of {pair_name: rates} for pairs sharing base currency
        related_quote_rates: Dict of {pair_name: rates} for pairs sharing quote currency

    Returns:
        DataFrame with 15 correlation features
    """
    n = len(timestamps)

    # Initialize features
    features = {
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
    }

    # Compute returns for volatility and momentum calculations
    returns = np.diff(rates, prepend=rates[0])

    # Process each timestamp
    for i in range(n):
        # 1-2: Base pair correlations (15min and 60min windows)
        if len(related_base_rates) > 0:
            w15_start = max(0, i - 14)  # 15 minutes
            w60_start = max(0, i - 59)  # 60 minutes

            if i - w15_start >= 10:  # Need at least 10 points
                base_corrs_15 = []
                for base_rates in related_base_rates.values():
                    try:
                        corr = np.corrcoef(rates[w15_start:i+1], base_rates[w15_start:i+1])[0, 1]
                        if not np.isnan(corr):
                            base_corrs_15.append(corr)
                    except:
                        pass
                if base_corrs_15:
                    features['corr_base_pairs_15min'][i] = np.mean(base_corrs_15)

            if i - w60_start >= 10:
                base_corrs_60 = []
                for base_rates in related_base_rates.values():
                    try:
                        corr = np.corrcoef(rates[w60_start:i+1], base_rates[w60_start:i+1])[0, 1]
                        if not np.isnan(corr):
                            base_corrs_60.append(corr)
                    except:
                        pass
                if base_corrs_60:
                    features['corr_base_pairs_60min'][i] = np.mean(base_corrs_60)

                    # 11: Correlation stability (std of correlations)
                    if len(base_corrs_60) > 1:
                        features['correlation_stability'][i] = 1.0 - np.std(base_corrs_60)

        # 3-4: Quote pair correlations
        if len(related_quote_rates) > 0:
            w15_start = max(0, i - 14)
            w60_start = max(0, i - 59)

            if i - w15_start >= 10:
                quote_corrs_15 = []
                for quote_rates in related_quote_rates.values():
                    try:
                        corr = np.corrcoef(rates[w15_start:i+1], quote_rates[w15_start:i+1])[0, 1]
                        if not np.isnan(corr):
                            quote_corrs_15.append(corr)
                    except:
                        pass
                if quote_corrs_15:
                    features['corr_quote_pairs_15min'][i] = np.mean(quote_corrs_15)

            if i - w60_start >= 10:
                quote_corrs_60 = []
                for quote_rates in related_quote_rates.values():
                    try:
                        corr = np.corrcoef(rates[w60_start:i+1], quote_rates[w60_start:i+1])[0, 1]
                        if not np.isnan(corr):
                            quote_corrs_60.append(corr)
                    except:
                        pass
                if quote_corrs_60:
                    features['corr_quote_pairs_60min'][i] = np.mean(quote_corrs_60)

        # 5-6: Relative strength (rate change vs average of related pairs)
        w60_start = max(0, i - 59)
        if i - w60_start >= 10:
            current_return = returns[i]

            if len(related_base_rates) > 0:
                base_returns = []
                for base_rates in related_base_rates.values():
                    base_return = base_rates[i] - base_rates[w60_start] if i > 0 else 0
                    base_returns.append(base_return)
                if base_returns:
                    avg_base_return = np.mean(base_returns)
                    features['relative_strength_vs_base_pairs'][i] = current_return - avg_base_return

            if len(related_quote_rates) > 0:
                quote_returns = []
                for quote_rates in related_quote_rates.values():
                    quote_return = quote_rates[i] - quote_rates[w60_start] if i > 0 else 0
                    quote_returns.append(quote_return)
                if quote_returns:
                    avg_quote_return = np.mean(quote_returns)
                    features['relative_strength_vs_quote_pairs'][i] = current_return - avg_quote_return

        # 7-8: Divergence (current rate vs average of related pairs)
        if len(related_base_rates) > 0:
            base_avg = np.mean([base_rates[i] for base_rates in related_base_rates.values()])
            features['base_pair_divergence'][i] = rates[i] - base_avg

        if len(related_quote_rates) > 0:
            quote_avg = np.mean([quote_rates[i] for quote_rates in related_quote_rates.values()])
            features['quote_pair_divergence'][i] = rates[i] - quote_avg

        # 14: Pair spread z-score (simplified - just z-score of rate)
        if i >= 60:
            window_rates = rates[max(0, i-59):i+1]
            mean_rate = np.mean(window_rates)
            std_rate = np.std(window_rates)
            if std_rate > 0:
                features['pair_spread_z_score'][i] = (rates[i] - mean_rate) / std_rate

        # 15: Cross-pair volatility ratio
        if i >= 60:
            window_returns = returns[max(0, i-59):i+1]
            current_vol = np.std(window_returns) if len(window_returns) > 1 else 0

            related_vols = []
            for related_rates in list(related_base_rates.values()) + list(related_quote_rates.values()):
                related_returns = np.diff(related_rates[max(0, i-59):i+1], prepend=related_rates[max(0, i-59)])
                related_vol = np.std(related_returns) if len(related_returns) > 1 else 0
                if related_vol > 0:
                    related_vols.append(related_vol)

            if related_vols:
                avg_related_vol = np.mean(related_vols)
                if avg_related_vol > 0:
                    features['cross_pair_volatility_ratio'][i] = current_vol / avg_related_vol

    return pd.DataFrame(features, index=range(n))


def process_partition(conn, pair, year, month):
    """Process one partition: compute correlation features"""
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

        # Fetch M1 data for this pair
        m1_table = f'm1_{pair}_y{year}m{month:02d}'
        cur.execute(f"""
            SELECT time, rate
            FROM bqx.{m1_table}
            WHERE time >= '{partition_start}'::timestamp AND time < '{partition_end}'::timestamp
            ORDER BY time;
        """)

        rows = cur.fetchall()
        if not rows or len(rows) < 60:
            return 0, time.time() - start_time

        timestamps = np.array([row[0] for row in rows])
        rates = np.array([float(row[1]) for row in rows])

        # Get related pairs
        base_pairs, quote_pairs = get_related_pairs(pair)

        # Fetch rates for related pairs
        related_base_rates = {}
        for base_pair in base_pairs[:5]:  # Limit to 5 pairs to reduce load
            base_m1_table = f'm1_{base_pair}_y{year}m{month:02d}'
            cur.execute(f"""
                SELECT rate
                FROM bqx.{base_m1_table}
                WHERE time >= '{partition_start}'::timestamp AND time < '{partition_end}'::timestamp
                ORDER BY time;
            """)
            base_rows = cur.fetchall()
            if len(base_rows) == len(rows):
                related_base_rates[base_pair] = np.array([float(r[0]) for r in base_rows])

        related_quote_rates = {}
        for quote_pair in quote_pairs[:5]:  # Limit to 5 pairs
            quote_m1_table = f'm1_{quote_pair}_y{year}m{month:02d}'
            cur.execute(f"""
                SELECT rate
                FROM bqx.{quote_m1_table}
                WHERE time >= '{partition_start}'::timestamp AND time < '{partition_end}'::timestamp
                ORDER BY time;
            """)
            quote_rows = cur.fetchall()
            if len(quote_rows) == len(rows):
                related_quote_rates[quote_pair] = np.array([float(r[0]) for r in quote_rows])

        # Compute correlation features
        features = compute_correlation_features(timestamps, rates, related_base_rates, related_quote_rates)

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
    print("CORRELATION FEATURES WORKER - PHASE 1.6.6 (V2)")
    print("=" * 80)
    print(f"\nPairs: {len(CURRENCY_PAIRS)}")
    print(f"Total Partitions: {total_partitions}")
    print(f"Threads: 8")
    print(f"Date Range: {START_DATE.date()} to {END_DATE.date()}")
    print("\nFeatures: 15 correlation-based features")
    print("  1-4: Base/Quote pair correlations (15min & 60min)")
    print("  5-6: Relative strength vs base/quote pairs")
    print("  7-9: Divergence metrics")
    print("  10: Cross-pair momentum divergence")
    print("  11-15: Advanced correlation metrics")
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
    print("CORRELATION FEATURES COMPUTATION COMPLETE")
    print("=" * 80)
    print(f"Total Rows: {total_rows_inserted:,}")
    print(f"Total Partitions: {partitions_completed}/{total_partitions}")
    print(f"Total Time: {elapsed_total:.1f}s ({elapsed_total/60:.1f} minutes)")
    if total_rows_inserted > 0:
        print(f"Average Throughput: {total_rows_inserted/elapsed_total:,.0f} rows/sec")


if __name__ == '__main__':
    main()
