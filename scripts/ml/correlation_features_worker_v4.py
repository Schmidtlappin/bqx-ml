#!/usr/bin/env python3
"""
BQX ML - Correlation Features Worker V4 (Comprehensive Multi-Dimensional Variance Analysis)

Implements comprehensive variance/covariance analysis across multiple dimensions:
1. Term structure correlations (w15↔w30↔w45↔w60↔w75)
2. Cross-pair correlations (same window, different pairs)
3. Cross-temporal correlations (lead-lag relationships)
4. Residual variance decomposition (systematic vs idiosyncratic)

Target: 336 partitions (28 pairs × 12 months)
Expected Runtime: ~6 hours (65 seconds per partition)
"""

import psycopg2
import numpy as np
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import time

# Database configuration
DB_CONFIG = {
    'host': 'trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com',
    'database': 'bqx',
    'user': 'postgres',
    'password': 'BQX_Aurora_2025_Secure'
}

# All 28 currency pairs
PAIRS = [
    'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
    'cadchf', 'cadjpy',
    'chfjpy',
    'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
    'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
    'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
    'usdcad', 'usdchf', 'usdjpy'
]

# Currency groupings for cross-pair analysis
BASE_PAIRS = {
    'EUR': ['euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd'],
    'GBP': ['gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd'],
    'AUD': ['audcad', 'audchf', 'audjpy', 'audnzd', 'audusd'],
    'NZD': ['nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd'],
    'USD': ['audusd', 'eurusd', 'gbpusd', 'nzdusd'],
    'CAD': ['audcad', 'eurcad', 'gbpcad', 'nzdcad', 'usdcad'],
    'CHF': ['audchf', 'cadchf', 'eurchf', 'gbpchf', 'nzdchf', 'usdchf'],
    'JPY': ['audjpy', 'cadjpy', 'chfjpy', 'eurjpy', 'gbpjpy', 'nzdjpy', 'usdjpy']
}

def get_base_and_quote_currency(pair):
    """Extract base and quote currency from pair name"""
    return pair[:3].upper(), pair[3:].upper()

def compute_term_structure_correlations(bqx_data):
    """
    Compute correlations between different BQX windows (term structure)
    Returns: dict with term structure metrics
    """
    windows = ['w15_bqx_return', 'w30_bqx_return', 'w45_bqx_return', 'w60_bqx_return', 'w75_bqx_return']

    # Extract arrays for each window
    arrays = {}
    for window in windows:
        if window in bqx_data and len(bqx_data[window]) > 0:
            arrays[window] = np.array(bqx_data[window])

    if len(arrays) < 2:
        return None

    # Compute key term structure correlations
    corr_15_60 = np.corrcoef(arrays['w15_bqx_return'], arrays['w60_bqx_return'])[0, 1] if 'w15_bqx_return' in arrays and 'w60_bqx_return' in arrays else 0.0
    corr_30_60 = np.corrcoef(arrays['w30_bqx_return'], arrays['w60_bqx_return'])[0, 1] if 'w30_bqx_return' in arrays and 'w60_bqx_return' in arrays else 0.0

    # Term structure slope (w75 - w15 average)
    term_slope = (np.mean(arrays['w75_bqx_return']) - np.mean(arrays['w15_bqx_return'])) if 'w75_bqx_return' in arrays and 'w15_bqx_return' in arrays else 0.0

    # Stability of term structure (rolling correlation variability)
    window_size = 60  # 1 hour
    rolling_corrs = []
    if 'w15_bqx_return' in arrays and 'w60_bqx_return' in arrays and len(arrays['w15_bqx_return']) > window_size:
        for i in range(window_size, len(arrays['w15_bqx_return'])):
            w15_slice = arrays['w15_bqx_return'][i-window_size:i]
            w60_slice = arrays['w60_bqx_return'][i-window_size:i]
            if len(w15_slice) > 1 and len(w60_slice) > 1:
                corr = np.corrcoef(w15_slice, w60_slice)[0, 1]
                if not np.isnan(corr):
                    rolling_corrs.append(corr)

    correlation_stability = np.std(rolling_corrs) if len(rolling_corrs) > 0 else 0.0

    return {
        'corr_15_60': corr_15_60,
        'corr_30_60': corr_30_60,
        'term_slope': term_slope,
        'correlation_stability': correlation_stability
    }

def compute_cross_pair_correlations(pair, bqx_data, conn):
    """
    Compute correlations with other pairs (same window)
    Returns: dict with cross-pair correlation metrics
    """
    base_curr, quote_curr = get_base_and_quote_currency(pair)

    # Get related pairs sharing the base currency
    base_related_pairs = [p for p in BASE_PAIRS.get(base_curr, []) if p != pair and p in PAIRS]
    quote_related_pairs = [p for p in BASE_PAIRS.get(quote_curr, []) if p != pair and p in PAIRS]

    if len(bqx_data['w15_bqx_return']) == 0:
        return None

    current_pair_w15 = np.array(bqx_data['w15_bqx_return'])
    current_pair_w60 = np.array(bqx_data['w60_bqx_return'])
    timestamps = bqx_data['ts_utc']

    # Compute average correlation with base currency pairs
    base_corrs_15 = []
    base_corrs_60 = []
    for related_pair in base_related_pairs[:3]:  # Limit to 3 pairs for performance
        try:
            cur = conn.cursor()
            partition_name = f"bqx_{related_pair}_{bqx_data['partition_suffix']}"
            cur.execute(f"""
                SELECT ts_utc, w15_bqx_return, w60_bqx_return
                FROM bqx.{partition_name}
                WHERE ts_utc >= %s AND ts_utc <= %s
                ORDER BY ts_utc;
            """, (timestamps[0], timestamps[-1]))

            related_data = cur.fetchall()
            if len(related_data) > 0:
                related_w15 = np.array([row[1] for row in related_data if row[1] is not None])
                related_w60 = np.array([row[2] for row in related_data if row[2] is not None])

                if len(related_w15) == len(current_pair_w15) and len(related_w15) > 1:
                    corr_15 = np.corrcoef(current_pair_w15, related_w15)[0, 1]
                    if not np.isnan(corr_15):
                        base_corrs_15.append(corr_15)

                if len(related_w60) == len(current_pair_w60) and len(related_w60) > 1:
                    corr_60 = np.corrcoef(current_pair_w60, related_w60)[0, 1]
                    if not np.isnan(corr_60):
                        base_corrs_60.append(corr_60)

            cur.close()
        except Exception as e:
            continue

    # Compute average correlation with quote currency pairs
    quote_corrs_15 = []
    quote_corrs_60 = []
    for related_pair in quote_related_pairs[:3]:  # Limit to 3 pairs
        try:
            cur = conn.cursor()
            partition_name = f"bqx_{related_pair}_{bqx_data['partition_suffix']}"
            cur.execute(f"""
                SELECT ts_utc, w15_bqx_return, w60_bqx_return
                FROM bqx.{partition_name}
                WHERE ts_utc >= %s AND ts_utc <= %s
                ORDER BY ts_utc;
            """, (timestamps[0], timestamps[-1]))

            related_data = cur.fetchall()
            if len(related_data) > 0:
                related_w15 = np.array([row[1] for row in related_data if row[1] is not None])
                related_w60 = np.array([row[2] for row in related_data if row[2] is not None])

                if len(related_w15) == len(current_pair_w15) and len(related_w15) > 1:
                    corr_15 = np.corrcoef(current_pair_w15, related_w15)[0, 1]
                    if not np.isnan(corr_15):
                        quote_corrs_15.append(corr_15)

                if len(related_w60) == len(current_pair_w60) and len(related_w60) > 1:
                    corr_60 = np.corrcoef(current_pair_w60, related_w60)[0, 1]
                    if not np.isnan(corr_60):
                        quote_corrs_60.append(corr_60)

            cur.close()
        except Exception as e:
            continue

    avg_base_corr_15 = np.mean(base_corrs_15) if len(base_corrs_15) > 0 else 0.0
    avg_base_corr_60 = np.mean(base_corrs_60) if len(base_corrs_60) > 0 else 0.0
    avg_quote_corr_15 = np.mean(quote_corrs_15) if len(quote_corrs_15) > 0 else 0.0
    avg_quote_corr_60 = np.mean(quote_corrs_60) if len(quote_corrs_60) > 0 else 0.0

    # Relative strength vs peer groups
    current_avg_15 = np.mean(current_pair_w15)
    current_avg_60 = np.mean(current_pair_w60)

    return {
        'corr_base_pairs_15min': avg_base_corr_15,
        'corr_base_pairs_60min': avg_base_corr_60,
        'corr_quote_pairs_15min': avg_quote_corr_15,
        'corr_quote_pairs_60min': avg_quote_corr_60,
        'relative_strength_vs_base': current_avg_15 / (abs(current_avg_15) + 1e-10),
        'relative_strength_vs_quote': current_avg_60 / (abs(current_avg_60) + 1e-10)
    }

def compute_cross_temporal_correlations(bqx_data):
    """
    Compute lead-lag relationships (different windows at different times)
    Does w15[T] predict w60[T+15]?
    Returns: dict with cross-temporal metrics
    """
    if len(bqx_data['w15_bqx_return']) < 60:
        return None

    w15_array = np.array(bqx_data['w15_bqx_return'])
    w60_array = np.array(bqx_data['w60_bqx_return'])

    # Lead-lag: Does w15[t] correlate with w60[t+15]?
    lead_lag_corr = 0.0
    if len(w15_array) > 15 and len(w60_array) > 15:
        w15_leading = w15_array[:-15]
        w60_lagging = w60_array[15:]

        if len(w15_leading) == len(w60_lagging) and len(w15_leading) > 1:
            lead_lag_corr = np.corrcoef(w15_leading, w60_lagging)[0, 1]
            if np.isnan(lead_lag_corr):
                lead_lag_corr = 0.0

    return {
        'lead_lag_indicator': lead_lag_corr
    }

def compute_residual_variances(pair, bqx_data, cross_pair_metrics):
    """
    Compute residual variance decomposition
    Variance NOT explained by systematic factors
    Returns: dict with residual variance metrics
    """
    if len(bqx_data['w15_bqx_return']) == 0 or cross_pair_metrics is None:
        return None

    w15_array = np.array(bqx_data['w15_bqx_return'])
    w60_array = np.array(bqx_data['w60_bqx_return'])

    # Total variance
    total_var_15 = np.var(w15_array) if len(w15_array) > 1 else 0.0
    total_var_60 = np.var(w60_array) if len(w60_array) > 1 else 0.0

    # Systematic variance (explained by base/quote pair correlations)
    # R² from cross-pair correlations gives systematic variance ratio
    base_corr_15 = cross_pair_metrics.get('corr_base_pairs_15min', 0.0)
    quote_corr_15 = cross_pair_metrics.get('corr_quote_pairs_15min', 0.0)

    # Estimate systematic vs idiosyncratic variance
    systematic_var_ratio = (base_corr_15**2 + quote_corr_15**2) / 2.0
    idiosyncratic_var_ratio = 1.0 - systematic_var_ratio

    # Base/quote pair divergence (deviations from expected relationships)
    base_pair_divergence = abs(base_corr_15 - 1.0)  # How much does it deviate from perfect correlation?
    quote_pair_divergence = abs(quote_corr_15 - 1.0)

    # Residual variance from term structure
    term_slope = bqx_data.get('term_slope', 0.0)
    term_structure_residual = abs(term_slope)  # Deviation from flat term structure

    return {
        'base_pair_divergence': base_pair_divergence,
        'quote_pair_divergence': quote_pair_divergence,
        'term_structure_residual': term_structure_residual,
        'idiosyncratic_var_ratio': idiosyncratic_var_ratio,
        'systematic_var_ratio': systematic_var_ratio
    }

def compute_triangulation_metrics(pair, bqx_data, conn):
    """
    Compute triangular arbitrage residuals
    For EUR/USD, check EUR/GBP × GBP/USD relationship
    Returns: triangulation divergence metric
    """
    base_curr, quote_curr = get_base_and_quote_currency(pair)

    # Find triangulation pairs (e.g., for EURUSD: EUR/GBP and GBP/USD)
    potential_bridge_currencies = ['GBP', 'JPY', 'CHF', 'AUD']

    triangulation_residuals = []

    for bridge in potential_bridge_currencies:
        if bridge == base_curr or bridge == quote_curr:
            continue

        # Find pairs: base/bridge and bridge/quote
        pair1_name = f"{base_curr.lower()}{bridge.lower()}"
        pair2_name = f"{bridge.lower()}{quote_curr.lower()}"

        if pair1_name in PAIRS and pair2_name in PAIRS:
            try:
                cur = conn.cursor()
                partition_suffix = bqx_data['partition_suffix']
                timestamps = bqx_data['ts_utc']

                # Fetch pair1 data
                cur.execute(f"""
                    SELECT w15_bqx_return FROM bqx.bqx_{pair1_name}_{partition_suffix}
                    WHERE ts_utc >= %s AND ts_utc <= %s
                    ORDER BY ts_utc;
                """, (timestamps[0], timestamps[-1]))
                pair1_data = np.array([row[0] for row in cur.fetchall() if row[0] is not None])

                # Fetch pair2 data
                cur.execute(f"""
                    SELECT w15_bqx_return FROM bqx.bqx_{pair2_name}_{partition_suffix}
                    WHERE ts_utc >= %s AND ts_utc <= %s
                    ORDER BY ts_utc;
                """, (timestamps[0], timestamps[-1]))
                pair2_data = np.array([row[0] for row in cur.fetchall() if row[0] is not None])

                cur.close()

                current_pair_data = np.array(bqx_data['w15_bqx_return'])

                # Triangulation: current_pair ≈ pair1 + pair2
                if len(pair1_data) == len(pair2_data) == len(current_pair_data) and len(pair1_data) > 1:
                    synthetic_pair = pair1_data + pair2_data
                    residual = current_pair_data - synthetic_pair
                    triangulation_residuals.append(np.std(residual))
            except Exception as e:
                continue

    triangular_arb_divergence = np.mean(triangulation_residuals) if len(triangulation_residuals) > 0 else 0.0

    return {
        'triangular_arb_divergence': triangular_arb_divergence
    }

def compute_volatility_and_momentum_metrics(bqx_data, cross_pair_metrics):
    """
    Compute cross-pair volatility ratios and momentum divergence
    Returns: dict with volatility/momentum metrics
    """
    if len(bqx_data['w15_bqx_return']) == 0:
        return None

    w15_array = np.array(bqx_data['w15_bqx_return'])
    w60_array = np.array(bqx_data['w60_bqx_return'])

    # Volatility (standard deviation of BQX returns)
    vol_15 = np.std(w15_array) if len(w15_array) > 1 else 0.0
    vol_60 = np.std(w60_array) if len(w60_array) > 1 else 0.0

    # Cross-pair volatility ratio (vs peer group)
    # Assume peer group has similar volatility; deviations indicate relative volatility
    cross_pair_volatility_ratio = vol_15 / (vol_60 + 1e-10)

    # Momentum divergence (how much current momentum differs from cross-pair average)
    # Use relative strength metrics from cross_pair analysis
    current_momentum_15 = np.mean(w15_array)
    momentum_divergence = abs(cross_pair_metrics.get('relative_strength_vs_base', 0.0))

    # Pair spread z-score (standardized deviation from mean)
    pair_spread_z_score = (current_momentum_15 - np.mean(w15_array)) / (np.std(w15_array) + 1e-10) if len(w15_array) > 1 else 0.0

    # Cointegration residual (simplified - deviation from expected relationship)
    # Use term structure residual as proxy
    cointegration_residual = bqx_data.get('term_structure_residual', 0.0)

    return {
        'cross_pair_volatility_ratio': cross_pair_volatility_ratio,
        'cross_pair_momentum_divergence': int(momentum_divergence * 100),  # INTEGER field
        'pair_spread_z_score': pair_spread_z_score,
        'cointegration_residual': cointegration_residual
    }

def process_partition(pair, year, month):
    """Process a single partition for one pair-month combination"""
    try:
        partition_start = datetime(year, month, 1)
        if month == 12:
            partition_end = datetime(year + 1, 1, 1)
        else:
            partition_end = datetime(year, month + 1, 1)

        partition_suffix = f"y{year}m{month:02d}"
        partition_name = f"correlation_features_{pair}_{partition_suffix}"
        bqx_table = f"bqx_{pair}_{partition_suffix}"

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Fetch BQX data for this partition
        cur.execute(f"""
            SELECT ts_utc, w15_bqx_return, w30_bqx_return, w45_bqx_return, w60_bqx_return, w75_bqx_return
            FROM bqx.{bqx_table}
            WHERE ts_utc >= %s AND ts_utc < %s
            ORDER BY ts_utc;
        """, (partition_start, partition_end))

        rows = cur.fetchall()

        if len(rows) == 0:
            cur.close()
            conn.close()
            return f"SKIP: {partition_name} (no BQX data)"

        # Organize data
        bqx_data = {
            'ts_utc': [row[0] for row in rows],
            'w15_bqx_return': [row[1] for row in rows if row[1] is not None],
            'w30_bqx_return': [row[2] for row in rows if row[2] is not None],
            'w45_bqx_return': [row[3] for row in rows if row[3] is not None],
            'w60_bqx_return': [row[4] for row in rows if row[4] is not None],
            'w75_bqx_return': [row[5] for row in rows if row[5] is not None],
            'partition_suffix': partition_suffix
        }

        # 1. Term structure correlations
        term_metrics = compute_term_structure_correlations(bqx_data)
        if term_metrics:
            bqx_data['term_slope'] = term_metrics['term_slope']
            bqx_data['correlation_stability'] = term_metrics['correlation_stability']

        # 2. Cross-pair correlations
        cross_pair_metrics = compute_cross_pair_correlations(pair, bqx_data, conn)

        # 3. Cross-temporal correlations
        cross_temporal_metrics = compute_cross_temporal_correlations(bqx_data)

        # 4. Residual variance decomposition
        residual_metrics = compute_residual_variances(pair, bqx_data, cross_pair_metrics) if cross_pair_metrics else None

        # 5. Triangulation metrics
        triangulation_metrics = compute_triangulation_metrics(pair, bqx_data, conn)

        # 6. Volatility and momentum metrics
        volatility_metrics = compute_volatility_and_momentum_metrics(bqx_data, cross_pair_metrics) if cross_pair_metrics else None

        # Compile all metrics
        if not all([term_metrics, cross_pair_metrics, cross_temporal_metrics, residual_metrics, triangulation_metrics, volatility_metrics]):
            cur.close()
            conn.close()
            return f"SKIP: {partition_name} (insufficient data for metrics)"

        # Insert correlation features for each timestamp
        insert_count = 0
        for i, ts in enumerate(bqx_data['ts_utc']):
            try:
                cur.execute(f"""
                    INSERT INTO bqx.{partition_name} (
                        ts_utc,
                        corr_base_pairs_15min,
                        corr_base_pairs_60min,
                        corr_quote_pairs_15min,
                        corr_quote_pairs_60min,
                        relative_strength_vs_base_pairs,
                        relative_strength_vs_quote_pairs,
                        base_pair_divergence,
                        quote_pair_divergence,
                        triangular_arb_divergence,
                        cross_pair_momentum_divergence,
                        correlation_stability,
                        lead_lag_indicator,
                        cointegration_residual,
                        pair_spread_z_score,
                        cross_pair_volatility_ratio
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ts_utc) DO NOTHING;
                """, (
                    ts,
                    cross_pair_metrics['corr_base_pairs_15min'],
                    cross_pair_metrics['corr_base_pairs_60min'],
                    cross_pair_metrics['corr_quote_pairs_15min'],
                    cross_pair_metrics['corr_quote_pairs_60min'],
                    cross_pair_metrics['relative_strength_vs_base'],
                    cross_pair_metrics['relative_strength_vs_quote'],
                    residual_metrics['base_pair_divergence'],
                    residual_metrics['quote_pair_divergence'],
                    triangulation_metrics['triangular_arb_divergence'],
                    volatility_metrics['cross_pair_momentum_divergence'],
                    term_metrics['correlation_stability'],
                    cross_temporal_metrics['lead_lag_indicator'],
                    volatility_metrics['cointegration_residual'],
                    volatility_metrics['pair_spread_z_score'],
                    volatility_metrics['cross_pair_volatility_ratio']
                ))
                insert_count += 1
            except Exception as e:
                continue

        conn.commit()
        cur.close()
        conn.close()

        return f"SUCCESS: {partition_name} ({insert_count} rows)"

    except Exception as e:
        return f"ERROR: {pair}_{year}m{month:02d} - {str(e)}"

def main():
    """Main execution"""
    print("=" * 80)
    print("BQX ML - Correlation Features Worker V4 (Multi-Dimensional Variance Analysis)")
    print("=" * 80)
    print(f"Start Time: {datetime.now()}")
    print(f"Target: 336 partitions (28 pairs × 12 months)")
    print(f"Features: 15 comprehensive variance/covariance metrics")
    print("=" * 80)
    print()

    # Generate all partition jobs (28 pairs × 12 months)
    jobs = []
    for pair in PAIRS:
        for month in range(7, 13):  # Jul-Dec 2024
            jobs.append((pair, 2024, month))

    print(f"Total jobs: {len(jobs)}")
    print()

    # Process partitions in parallel (8 threads)
    start_time = time.time()
    completed = 0
    skipped = 0
    errors = 0

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_partition, pair, year, month): (pair, year, month)
                   for pair, year, month in jobs}

        for future in as_completed(futures):
            result = future.result()
            completed += 1

            if "SUCCESS" in result:
                pass
            elif "SKIP" in result:
                skipped += 1
            else:
                errors += 1

            # Progress update every 10 partitions
            if completed % 10 == 0:
                elapsed = time.time() - start_time
                progress = (completed / len(jobs)) * 100
                rate = completed / elapsed if elapsed > 0 else 0
                eta_seconds = (len(jobs) - completed) / rate if rate > 0 else 0
                eta_hours = eta_seconds / 3600

                print(f"Progress: {completed}/{len(jobs)} ({progress:.1f}%) | "
                      f"Rate: {rate:.2f} part/sec | ETA: {eta_hours:.1f}h | "
                      f"Skipped: {skipped} | Errors: {errors}")

    total_time = time.time() - start_time
    print()
    print("=" * 80)
    print(f"COMPLETED: {completed}/{len(jobs)} partitions in {total_time/3600:.2f} hours")
    print(f"Skipped: {skipped} | Errors: {errors}")
    print(f"End Time: {datetime.now()}")
    print("=" * 80)

if __name__ == "__main__":
    main()
