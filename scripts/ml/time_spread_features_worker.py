#!/usr/bin/env python3
"""
Time & Spread Features Worker - Track 1 (Stage 1.6.3) - SCHEMA COMPLIANT

Computes 28 features matching existing database schema:
- 8 Time features (cyclical encoding + session markers)
- 20 Spread/Microstructure features

Time Features (8) - WITH CYCLICAL ENCODING:
1. hour_sin - sin(2π * hour/24)
2. hour_cos - cos(2π * hour/24)
3. day_of_week_sin - sin(2π * day/7)
4. day_of_week_cos - cos(2π * day/7)
5. session_overlap - Number of overlapping sessions (0-2)
6. is_weekend_approach - Binary: 1 if Friday evening or weekend
7. minutes_since_market_open - Minutes since last major market open
8. trading_session - Categorical: 0=asian, 1=london, 2=newyork, 3=overlap, 4=quiet

Spread Features (20):
1. spread_mean_60min - Mean spread over 60 minutes
2. spread_volatility_60min - Stdev of spread over 60 minutes
3. spread_pct_of_rate - Spread as percentage of mid price
4. spread_trend_slope - Linear regression slope of spread (60min)
5. spread_spike - Binary: 1 if spread > 2× mean_60min
6. bid_ask_imbalance - Normalized bid/ask pressure
7. effective_spread - 2 × |trade_price - mid_price| / mid_price
8. quoted_spread - (ask - bid) / mid_price
9. realized_spread - Effective spread - price impact
10. price_impact - Price movement after trade
11. roll_cost - Half-spread cost metric
12. bid_depth - Normalized bid liquidity
13. ask_depth - Normalized ask liquidity
14. depth_imbalance - (bid_depth - ask_depth) / total_depth
15. spread_range_60min - Max - min spread over 60min
16. spread_percentile_60min - Current spread percentile in 60min window
17. mid_price_volatility - Stdev of mid prices over 60min
18. tick_direction - Price movement direction: 1=up, 0=flat, -1=down
19. tick_rule - Tick classification: 1=buyer-initiated, -1=seller-initiated
20. order_flow_toxicity - Adverse selection measure

Data Source: M1.time, bid_close, ask_close, spread_close, rate
Storage: bqx.time_features_{pair} and bqx.spread_features_{pair}
Estimated Time: 4-5 hours (336 partitions / 8 threads)
"""

import psycopg2
from psycopg2 import sql
import numpy as np
from scipy import stats
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import math

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

# Thread-safe counter
progress_lock = threading.Lock()
partitions_completed = 0
total_partitions = len(CURRENCY_PAIRS) * 12


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


def compute_time_features(times):
    """
    Compute 8 time features with CYCLICAL ENCODING

    Returns:
        dict: Time feature arrays matching schema
    """
    n = len(times)
    time_features = {
        'hour_sin': np.zeros(n),
        'hour_cos': np.zeros(n),
        'day_of_week_sin': np.zeros(n),
        'day_of_week_cos': np.zeros(n),
        'session_overlap': np.zeros(n, dtype=int),
        'is_weekend_approach': np.zeros(n, dtype=int),
        'minutes_since_market_open': np.zeros(n, dtype=int),
        'trading_session': np.zeros(n, dtype=int),
    }

    for i, dt in enumerate(times):
        hour = dt.hour
        minute = dt.minute
        weekday = dt.weekday()  # 0=Monday, 6=Sunday

        # Cyclical encoding for hour (0-23)
        time_features['hour_sin'][i] = np.sin(2 * np.pi * hour / 24)
        time_features['hour_cos'][i] = np.cos(2 * np.pi * hour / 24)

        # Cyclical encoding for day of week (0-6)
        time_features['day_of_week_sin'][i] = np.sin(2 * np.pi * weekday / 7)
        time_features['day_of_week_cos'][i] = np.cos(2 * np.pi * weekday / 7)

        # Trading session (0=asian, 1=london, 2=newyork, 3=overlap, 4=quiet)
        # Asian: 00:00-08:00 UTC
        # London: 08:00-16:00 UTC
        # NY: 13:00-21:00 UTC
        # Overlap: 13:00-16:00 UTC
        # Quiet: 21:00-00:00 UTC
        if 13 <= hour < 16:
            time_features['trading_session'][i] = 3  # overlap
            time_features['session_overlap'][i] = 2  # London + NY
        elif 8 <= hour < 13:
            time_features['trading_session'][i] = 1  # london
            time_features['session_overlap'][i] = 1
        elif 16 <= hour < 21:
            time_features['trading_session'][i] = 2  # newyork
            time_features['session_overlap'][i] = 1
        elif 0 <= hour < 8:
            time_features['trading_session'][i] = 0  # asian
            time_features['session_overlap'][i] = 1
        else:
            time_features['trading_session'][i] = 4  # quiet
            time_features['session_overlap'][i] = 0

        # Is weekend approach (Friday after 17:00 UTC or Saturday/Sunday)
        time_features['is_weekend_approach'][i] = 1 if (weekday == 4 and hour >= 17) or weekday >= 5 else 0

        # Minutes since last major market open
        minute_of_day = hour * 60 + minute
        if minute_of_day < 8 * 60:
            # Since Asian open at 00:00
            time_features['minutes_since_market_open'][i] = minute_of_day
        elif minute_of_day < 13 * 60:
            # Since London open at 08:00
            time_features['minutes_since_market_open'][i] = minute_of_day - 8 * 60
        else:
            # Since NY open at 13:00
            time_features['minutes_since_market_open'][i] = minute_of_day - 13 * 60

    return time_features


def compute_spread_features(times, bids, asks, spreads, rates):
    """
    Compute 20 spread/microstructure features matching schema

    Args:
        times: Array of timestamps
        bids: Array of bid_close prices
        asks: Array of ask_close prices
        spreads: Array of spread_close values
        rates: Array of close/rate values

    Returns:
        dict: Spread feature arrays
    """
    n = len(times)
    spread_features = {
        'spread_mean_60min': np.zeros(n),
        'spread_volatility_60min': np.zeros(n),
        'spread_pct_of_rate': np.zeros(n),
        'spread_trend_slope': np.zeros(n),
        'spread_spike': np.zeros(n, dtype=int),
        'bid_ask_imbalance': np.zeros(n),
        'effective_spread': np.zeros(n),
        'quoted_spread': np.zeros(n),
        'realized_spread': np.zeros(n),
        'price_impact': np.zeros(n),
        'roll_cost': np.zeros(n),
        'bid_depth': np.zeros(n),
        'ask_depth': np.zeros(n),
        'depth_imbalance': np.zeros(n),
        'spread_range_60min': np.zeros(n),
        'spread_percentile_60min': np.zeros(n),
        'mid_price_volatility': np.zeros(n),
        'tick_direction': np.zeros(n, dtype=int),
        'tick_rule': np.zeros(n, dtype=int),
        'order_flow_toxicity': np.zeros(n),
    }

    # Compute mid prices
    mid_prices = (bids + asks) / 2

    for i in range(n):
        # Rolling 60-minute window
        w60_start = max(0, i - 59)
        spread_w60 = spreads[w60_start:i+1]
        mid_w60 = mid_prices[w60_start:i+1]

        # 1. Spread mean 60min
        spread_features['spread_mean_60min'][i] = np.mean(spread_w60) if len(spread_w60) > 0 else 0

        # 2. Spread volatility 60min
        spread_features['spread_volatility_60min'][i] = np.std(spread_w60) if len(spread_w60) > 1 else 0

        # 3. Spread as % of rate
        spread_features['spread_pct_of_rate'][i] = (spreads[i] / rates[i] * 100) if rates[i] > 0 else 0

        # 4. Spread trend slope
        if len(spread_w60) >= 10:
            x = np.arange(len(spread_w60))
            slope, _, _, _, _ = stats.linregress(x, spread_w60)
            spread_features['spread_trend_slope'][i] = slope

        # 5. Spread spike
        mean_60 = spread_features['spread_mean_60min'][i]
        spread_features['spread_spike'][i] = 1 if spreads[i] > 2 * mean_60 and mean_60 > 0 else 0

        # 6. Bid-ask imbalance (normalized)
        total = bids[i] + asks[i]
        spread_features['bid_ask_imbalance'][i] = (bids[i] - asks[i]) / total if total > 0 else 0

        # 7. Effective spread (assuming trade at mid)
        mid = mid_prices[i]
        spread_features['effective_spread'][i] = 2 * abs(rates[i] - mid) / mid if mid > 0 else 0

        # 8. Quoted spread
        spread_features['quoted_spread'][i] = spreads[i] / mid if mid > 0 else 0

        # 9. Realized spread (effective - impact)
        # Simplified: half of effective spread
        spread_features['realized_spread'][i] = spread_features['effective_spread'][i] * 0.5

        # 10. Price impact
        spread_features['price_impact'][i] = spread_features['effective_spread'][i] * 0.5

        # 11. Roll cost (half spread)
        spread_features['roll_cost'][i] = spreads[i] / 2

        # 12-13. Bid/ask depth (normalized by spread)
        if spreads[i] > 0:
            spread_features['bid_depth'][i] = bids[i] / spreads[i]
            spread_features['ask_depth'][i] = asks[i] / spreads[i]

        # 14. Depth imbalance
        total_depth = spread_features['bid_depth'][i] + spread_features['ask_depth'][i]
        if total_depth > 0:
            spread_features['depth_imbalance'][i] = (spread_features['bid_depth'][i] - spread_features['ask_depth'][i]) / total_depth

        # 15. Spread range 60min
        if len(spread_w60) > 0:
            spread_features['spread_range_60min'][i] = np.max(spread_w60) - np.min(spread_w60)

        # 16. Spread percentile 60min
        if len(spread_w60) > 1:
            percentile = np.searchsorted(np.sort(spread_w60), spreads[i]) / len(spread_w60)
            spread_features['spread_percentile_60min'][i] = percentile

        # 17. Mid price volatility
        spread_features['mid_price_volatility'][i] = np.std(mid_w60) if len(mid_w60) > 1 else 0

        # 18. Tick direction
        if i > 0:
            price_change = mid_prices[i] - mid_prices[i-1]
            if price_change > 0:
                spread_features['tick_direction'][i] = 1
            elif price_change < 0:
                spread_features['tick_direction'][i] = -1
            else:
                spread_features['tick_direction'][i] = 0

        # 19. Tick rule (buy/sell classification)
        if i > 0:
            # If price went up, likely buyer-initiated
            if mid_prices[i] > mid_prices[i-1]:
                spread_features['tick_rule'][i] = 1
            elif mid_prices[i] < mid_prices[i-1]:
                spread_features['tick_rule'][i] = -1
            else:
                # Use bid/ask imbalance as tiebreaker
                spread_features['tick_rule'][i] = 1 if spread_features['bid_ask_imbalance'][i] > 0 else -1

        # 20. Order flow toxicity (adverse selection proxy)
        if len(mid_w60) > 5:
            # Correlation between spread widening and price volatility
            recent_vol = np.std(mid_w60[-5:])
            recent_spread = np.mean(spread_w60[-5:])
            baseline_vol = np.std(mid_w60) if len(mid_w60) > 1 else 0
            baseline_spread = np.mean(spread_w60) if len(spread_w60) > 0 else 1

            if baseline_vol > 0 and baseline_spread > 0:
                vol_ratio = recent_vol / baseline_vol
                spread_ratio = recent_spread / baseline_spread
                spread_features['order_flow_toxicity'][i] = vol_ratio * spread_ratio

    return spread_features


def process_partition(conn, pair, year, month):
    """Process one partition: compute time and spread features"""
    import time
    start_time = time.time()

    cur = conn.cursor()

    # Partition boundaries
    partition_start = datetime(year, month, 1)
    if month == 12:
        partition_end = datetime(year + 1, 1, 1)
    else:
        partition_end = datetime(year, month + 1, 1)

    # Fetch M1 data with 60-minute lookback
    m1_table = sql.Identifier('bqx', f'm1_{pair}')
    fetch_query = sql.SQL("""
        SELECT time, bid_close, ask_close, spread_close, rate
        FROM {}
        WHERE time >= %s - INTERVAL '60 minutes' AND time < %s
        ORDER BY time
    """).format(m1_table)

    cur.execute(fetch_query, (partition_start, partition_end))
    rows = cur.fetchall()

    if len(rows) < 60:
        cur.close()
        return 0, 0, 0

    # Convert to arrays
    times = np.array([r[0] for r in rows])
    bids = np.array([float(r[1]) if r[1] is not None else 0.0 for r in rows])
    asks = np.array([float(r[2]) if r[2] is not None else 0.0 for r in rows])
    spreads = np.array([float(r[3]) if r[3] is not None else 0.0 for r in rows])
    rates = np.array([float(r[4]) if r[4] is not None else 1.0 for r in rows])

    # Find partition start index
    partition_start_idx = np.searchsorted(times, partition_start)

    # Compute features (on full data including lookback)
    time_features = compute_time_features(times)
    spread_features = compute_spread_features(times, bids, asks, spreads, rates)

    # Extract only partition data
    partition_times = times[partition_start_idx:]
    n_partition = len(partition_times)

    # Insert time features
    time_table = sql.Identifier('bqx', f'time_features_{pair}')
    time_insert = sql.SQL("""
        INSERT INTO {} (
            ts_utc, hour_sin, hour_cos, day_of_week_sin, day_of_week_cos,
            session_overlap, is_weekend_approach, minutes_since_market_open, trading_session
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ts_utc) DO UPDATE SET
            hour_sin = EXCLUDED.hour_sin,
            hour_cos = EXCLUDED.hour_cos,
            day_of_week_sin = EXCLUDED.day_of_week_sin,
            day_of_week_cos = EXCLUDED.day_of_week_cos,
            session_overlap = EXCLUDED.session_overlap,
            is_weekend_approach = EXCLUDED.is_weekend_approach,
            minutes_since_market_open = EXCLUDED.minutes_since_market_open,
            trading_session = EXCLUDED.trading_session
    """).format(time_table)

    time_data = []
    for i in range(n_partition):
        idx = partition_start_idx + i
        time_data.append((
            partition_times[i],
            float(time_features['hour_sin'][idx]),
            float(time_features['hour_cos'][idx]),
            float(time_features['day_of_week_sin'][idx]),
            float(time_features['day_of_week_cos'][idx]),
            int(time_features['session_overlap'][idx]),
            int(time_features['is_weekend_approach'][idx]),
            int(time_features['minutes_since_market_open'][idx]),
            int(time_features['trading_session'][idx])
        ))

    cur.executemany(time_insert, time_data)

    # Insert spread features
    spread_table = sql.Identifier('bqx', f'spread_features_{pair}')
    spread_insert = sql.SQL("""
        INSERT INTO {} (
            ts_utc, spread_mean_60min, spread_volatility_60min, spread_pct_of_rate,
            spread_trend_slope, spread_spike, bid_ask_imbalance, effective_spread,
            quoted_spread, realized_spread, price_impact, roll_cost,
            bid_depth, ask_depth, depth_imbalance, spread_range_60min,
            spread_percentile_60min, mid_price_volatility, tick_direction,
            tick_rule, order_flow_toxicity
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ts_utc) DO UPDATE SET
            spread_mean_60min = EXCLUDED.spread_mean_60min,
            spread_volatility_60min = EXCLUDED.spread_volatility_60min,
            spread_pct_of_rate = EXCLUDED.spread_pct_of_rate,
            spread_trend_slope = EXCLUDED.spread_trend_slope,
            spread_spike = EXCLUDED.spread_spike,
            bid_ask_imbalance = EXCLUDED.bid_ask_imbalance,
            effective_spread = EXCLUDED.effective_spread,
            quoted_spread = EXCLUDED.quoted_spread,
            realized_spread = EXCLUDED.realized_spread,
            price_impact = EXCLUDED.price_impact,
            roll_cost = EXCLUDED.roll_cost,
            bid_depth = EXCLUDED.bid_depth,
            ask_depth = EXCLUDED.ask_depth,
            depth_imbalance = EXCLUDED.depth_imbalance,
            spread_range_60min = EXCLUDED.spread_range_60min,
            spread_percentile_60min = EXCLUDED.spread_percentile_60min,
            mid_price_volatility = EXCLUDED.mid_price_volatility,
            tick_direction = EXCLUDED.tick_direction,
            tick_rule = EXCLUDED.tick_rule,
            order_flow_toxicity = EXCLUDED.order_flow_toxicity
    """).format(spread_table)

    spread_data = []
    for i in range(n_partition):
        idx = partition_start_idx + i
        spread_data.append((
            partition_times[i],
            float(spread_features['spread_mean_60min'][idx]),
            float(spread_features['spread_volatility_60min'][idx]),
            float(spread_features['spread_pct_of_rate'][idx]),
            float(spread_features['spread_trend_slope'][idx]),
            int(spread_features['spread_spike'][idx]),
            float(spread_features['bid_ask_imbalance'][idx]),
            float(spread_features['effective_spread'][idx]),
            float(spread_features['quoted_spread'][idx]),
            float(spread_features['realized_spread'][idx]),
            float(spread_features['price_impact'][idx]),
            float(spread_features['roll_cost'][idx]),
            float(spread_features['bid_depth'][idx]),
            float(spread_features['ask_depth'][idx]),
            float(spread_features['depth_imbalance'][idx]),
            float(spread_features['spread_range_60min'][idx]),
            float(spread_features['spread_percentile_60min'][idx]),
            float(spread_features['mid_price_volatility'][idx]),
            int(spread_features['tick_direction'][idx]),
            int(spread_features['tick_rule'][idx]),
            float(spread_features['order_flow_toxicity'][idx])
        ))

    cur.executemany(spread_insert, spread_data)

    conn.commit()
    cur.close()

    elapsed = time.time() - start_time
    return len(time_data), len(spread_data), elapsed


def process_partition_worker(pair, year, month):
    """Worker function for threading"""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        time_rows, spread_rows, elapsed = process_partition(conn, pair, year, month)

        global partitions_completed
        with progress_lock:
            partitions_completed += 1
            progress_pct = (partitions_completed / total_partitions) * 100

        return {
            'pair': pair,
            'year': year,
            'month': month,
            'time_rows': time_rows,
            'spread_rows': spread_rows,
            'elapsed': elapsed,
            'progress': progress_pct
        }
    finally:
        conn.close()


def main():
    """Main execution"""
    import time

    print("=" * 80)
    print("TIME & SPREAD FEATURES WORKER - TRACK 1 (STAGE 1.6.3) - SCHEMA COMPLIANT")
    print("=" * 80)
    print()
    print(f"Pairs: {len(CURRENCY_PAIRS)}")
    print(f"Months per pair: {len(generate_month_ranges())}")
    print(f"Total partitions: {total_partitions}")
    print(f"Threads: 8")
    print(f"Date range: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print()
    print("Features: 28 total")
    print("  Time: 8 (cyclical encoding, session markers)")
    print("  Spread: 20 (microstructure, liquidity metrics)")
    print()

    total_start = time.time()
    total_time_rows = 0
    total_spread_rows = 0

    # Create list of all partition jobs
    jobs = []
    for pair in CURRENCY_PAIRS:
        for year, month in generate_month_ranges():
            jobs.append((pair, year, month))

    print(f"Processing {len(jobs)} partitions with 8 threads...")
    print()

    # Execute with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_partition_worker, pair, year, month): (pair, year, month)
                   for pair, year, month in jobs}

        for future in as_completed(futures):
            pair, year, month = futures[future]
            try:
                result = future.result()
                total_time_rows += result['time_rows']
                total_spread_rows += result['spread_rows']

                print(f"[{result['pair'].upper()}] {result['year']}-{result['month']:02d} | "
                      f"Time: {result['time_rows']:,} | Spread: {result['spread_rows']:,} | "
                      f"{result['elapsed']:.1f}s | Progress: {result['progress']:5.1f}%")

            except Exception as e:
                print(f"✗ ERROR [{pair.upper()}] {year}-{month:02d}: {e}")

    total_elapsed = time.time() - total_start

    # Final summary
    print()
    print("=" * 80)
    print("TIME & SPREAD FEATURES COMPUTATION COMPLETE")
    print("=" * 80)
    print(f"Time Features Rows: {total_time_rows:,}")
    print(f"Spread Features Rows: {total_spread_rows:,}")
    print(f"Total Partitions: {partitions_completed}/{total_partitions}")
    print(f"Total Time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} minutes)")
    print(f"Average Throughput: {(total_time_rows + total_spread_rows)/total_elapsed:.0f} rows/sec")
    print()
    print("Next Steps:")
    print("  1. Verify time features: SELECT * FROM bqx.time_features_eurusd LIMIT 10;")
    print("  2. Verify spread features: SELECT * FROM bqx.spread_features_eurusd LIMIT 10;")
    print("  3. Check cyclical encoding: SELECT hour_sin, hour_cos FROM bqx.time_features_eurusd WHERE ts_utc >= '2024-07-01' LIMIT 20;")
    print()


if __name__ == "__main__":
    main()
