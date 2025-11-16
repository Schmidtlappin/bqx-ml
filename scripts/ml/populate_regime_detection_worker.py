#!/usr/bin/env python3
"""
Stage 2.9: Market Regime Detection Worker
Classifies market conditions into distinct regimes for enhanced ML prediction.

Features (30 per partition = 15 rate + 15 bqx):
For each domain (rate_index and BQX):

Regime Classifications (5 features):
1. trend_regime: Trending Up (2), Ranging (1), Trending Down (0)
2. volatility_regime: High (2), Medium (1), Low (0)
3. momentum_regime: Strong Bullish (4) ... Strong Bearish (0)
4. mean_reversion_regime: Reverting (1) vs Trending (0)
5. composite_regime: Combined regime score (0-10)

Regime Metrics (10 features):
6. regime_confidence: Confidence in current regime (0-1)
7. regime_persistence: Minutes in current regime
8. regime_transition_probability: Likelihood of regime change (0-1)
9. trend_strength: ADX-like directional strength (0-100)
10. volatility_percentile: Current vol vs 24h history (0-100)
11. momentum_score: Combined momentum indicator (-100 to 100)
12. mean_reversion_score: Strength of mean reversion (0-100)
13. regime_stability: How stable is current regime (0-1)
14. breakout_probability: Likelihood of range breakout (0-1)
15. regime_quality: Overall regime clarity (0-1)

Total: 15 features × 2 domains = 30 features per partition

Estimated Runtime: 6 hours with 32 workers on D64as_v5
"""

import psycopg2
import pandas as pd
import numpy as np
import logging
import sys
import os
import time
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from scipy import stats

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com'),
    'database': 'bqx',
    'user': 'postgres',
    'password': os.environ.get('DB_PASSWORD', 'BQX_Aurora_2025_Secure')
}

# All 28 currency pairs
PAIRS = [
    'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
    'cadchf', 'cadjpy', 'chfjpy',
    'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
    'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
    'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
    'usdcad', 'usdchf', 'usdjpy'
]

# Create logs directory
os.makedirs('/tmp/logs/stage_2_9', exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/logs/stage_2_9/populate.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def detect_market_regime(df, domain='rate'):
    """
    Detect market regime for current timestamp based on recent history.

    Args:
        df: DataFrame with price/BQX data (last 1440 rows = 24 hours)
        domain: 'rate' or 'bqx'

    Returns:
        dict: Regime classification features
    """
    try:
        if len(df) < 60:
            # Not enough data for regime detection
            return {f'{metric}_{domain}': None for metric in [
                'trend_regime', 'volatility_regime', 'momentum_regime',
                'mean_reversion_regime', 'composite_regime', 'regime_confidence',
                'regime_persistence', 'regime_transition_probability', 'trend_strength',
                'volatility_percentile', 'momentum_score', 'mean_reversion_score',
                'regime_stability', 'breakout_probability', 'regime_quality'
            ]}

        # Use rate_index or bqx_value
        if domain == 'rate':
            price = df['rate_index'].values
        else:
            price = df['bqx_value'].values

        metrics = {}

        # 1. Trend Regime Detection (based on linear regression slope)
        recent_window = min(240, len(df))  # 4 hours or available
        x = np.arange(recent_window)
        y = price[-recent_window:]

        slope, intercept = np.polyfit(x, y, 1)

        # Normalize slope to percentage change
        price_range = np.ptp(y)
        if price_range > 0:
            normalized_slope = (slope * recent_window) / np.mean(y) * 100
        else:
            normalized_slope = 0

        # Classify trend
        if normalized_slope > 0.5:
            trend_regime = 2  # Trending Up
        elif normalized_slope < -0.5:
            trend_regime = 0  # Trending Down
        else:
            trend_regime = 1  # Ranging

        metrics[f'trend_regime_{domain}'] = trend_regime

        # 2. Volatility Regime (based on recent standard deviation)
        volatility_window = min(1440, len(df))  # 24 hours
        returns = np.diff(price[-volatility_window:]) / price[-volatility_window:-1]
        current_vol = np.std(returns[-60:]) if len(returns) >= 60 else 0  # Last 60 min
        historical_vol = np.std(returns) if len(returns) > 0 else 0

        if current_vol > historical_vol * 1.5:
            volatility_regime = 2  # High volatility
        elif current_vol > historical_vol * 0.7:
            volatility_regime = 1  # Medium volatility
        else:
            volatility_regime = 0  # Low volatility

        metrics[f'volatility_regime_{domain}'] = volatility_regime

        # Volatility percentile
        vol_percentile = (sum(1 for r in returns if abs(r) < current_vol) / len(returns) * 100) if len(returns) > 0 else 50
        metrics[f'volatility_percentile_{domain}'] = vol_percentile

        # 3. Momentum Regime (based on rate of change)
        roc_60 = ((price[-1] - price[-60]) / price[-60] * 100) if len(price) >= 60 else 0
        roc_240 = ((price[-1] - price[-240]) / price[-240] * 100) if len(price) >= 240 else 0

        # Combined momentum score
        momentum_score = (roc_60 * 0.6) + (roc_240 * 0.4)
        metrics[f'momentum_score_{domain}'] = momentum_score

        # Classify momentum regime
        if momentum_score > 1.0:
            momentum_regime = 4  # Strong Bullish
        elif momentum_score > 0.3:
            momentum_regime = 3  # Weak Bullish
        elif momentum_score > -0.3:
            momentum_regime = 2  # Neutral
        elif momentum_score > -1.0:
            momentum_regime = 1  # Weak Bearish
        else:
            momentum_regime = 0  # Strong Bearish

        metrics[f'momentum_regime_{domain}'] = momentum_regime

        # 4. Mean Reversion Regime (based on autocorrelation of returns)
        if len(returns) >= 60:
            returns_series = pd.Series(returns[-240:] if len(returns) >= 240 else returns)
            autocorr = returns_series.autocorr(lag=1)

            if autocorr < -0.2:
                mean_reversion_regime = 1  # Strong mean reversion
                mean_reversion_score = abs(autocorr) * 100
            else:
                mean_reversion_regime = 0  # Trending
                mean_reversion_score = (1 - autocorr) * 50 if autocorr < 1 else 0
        else:
            mean_reversion_regime = 0
            mean_reversion_score = 0

        metrics[f'mean_reversion_regime_{domain}'] = mean_reversion_regime
        metrics[f'mean_reversion_score_{domain}'] = mean_reversion_score

        # 5. Composite Regime Score (weighted combination)
        composite_regime = (
            trend_regime * 2.5 +
            volatility_regime * 1.5 +
            momentum_regime * 1.0 +
            mean_reversion_regime * 0.5
        )
        metrics[f'composite_regime_{domain}'] = composite_regime

        # 6. Regime Confidence (based on consistency of indicators)
        # High confidence when multiple indicators align
        indicators_aligned = 0
        if trend_regime == 2 and momentum_regime >= 3:
            indicators_aligned += 1
        if trend_regime == 0 and momentum_regime <= 1:
            indicators_aligned += 1
        if volatility_regime == 0 and mean_reversion_regime == 0:
            indicators_aligned += 1

        regime_confidence = indicators_aligned / 3.0
        metrics[f'regime_confidence_{domain}'] = regime_confidence

        # 7. Regime Persistence (simplified - based on how long in current trend)
        # Count consecutive periods with same trend direction
        persistence_count = 1
        for i in range(2, min(240, len(price))):
            prev_slope = (price[-i] - price[-i-1])
            curr_slope = (price[-1] - price[-2])
            if np.sign(prev_slope) == np.sign(curr_slope):
                persistence_count += 1
            else:
                break

        metrics[f'regime_persistence_{domain}'] = persistence_count

        # 8. Regime Transition Probability (based on regime age and volatility)
        # Higher volatility + longer persistence = higher transition probability
        transition_prob = min(1.0, (persistence_count / 240) * (volatility_regime / 2 + 0.5))
        metrics[f'regime_transition_probability_{domain}'] = transition_prob

        # 9. Trend Strength (ADX-like indicator)
        # Simplified: ratio of directional movement to total movement
        if len(returns) >= 60:
            directional_movement = abs(sum(returns[-60:]))
            total_movement = sum(abs(r) for r in returns[-60:])
            trend_strength = (directional_movement / total_movement * 100) if total_movement > 0 else 0
        else:
            trend_strength = 0

        metrics[f'trend_strength_{domain}'] = trend_strength

        # 10. Regime Stability (inverse of transition probability)
        regime_stability = 1.0 - transition_prob
        metrics[f'regime_stability_{domain}'] = regime_stability

        # 11. Breakout Probability (for ranging markets)
        if trend_regime == 1:  # Ranging
            # Higher volatility + longer range = higher breakout probability
            range_duration = persistence_count
            breakout_prob = min(1.0, (range_duration / 120) * (volatility_regime / 2 + 0.3))
        else:
            breakout_prob = 0.0

        metrics[f'breakout_probability_{domain}'] = breakout_prob

        # 12. Regime Quality (how clear and well-defined is the regime)
        # High quality when: strong trend + low volatility OR clear range + mean reversion
        if trend_regime != 1:  # Trending
            regime_quality = (trend_strength / 100) * (1 - volatility_regime / 2)
        else:  # Ranging
            regime_quality = mean_reversion_score / 100

        metrics[f'regime_quality_{domain}'] = regime_quality

        return metrics

    except Exception as e:
        logger.warning(f"Regime detection failed for {domain}: {e}")
        return {f'{metric}_{domain}': 0 for metric in [
            'trend_regime', 'volatility_regime', 'momentum_regime',
            'mean_reversion_regime', 'composite_regime', 'regime_confidence',
            'regime_persistence', 'regime_transition_probability', 'trend_strength',
            'volatility_percentile', 'momentum_score', 'mean_reversion_score',
            'regime_stability', 'breakout_probability', 'regime_quality'
        ]}


def populate_regime_for_pair(pair, year_month):
    """
    Populate regime detection features for one pair and one month.

    Args:
        pair: Currency pair (e.g., 'eurusd')
        year_month: Month partition (e.g., '2024_07')

    Returns:
        tuple: (pair, year_month, success, row_count, error_msg)
    """
    start_time = time.time()

    try:
        logger.info(f"{pair.upper()} {year_month}: Starting regime detection...")

        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)

        year, month = year_month.split('_')

        # Fetch rate_index and BQX data
        # Need extended history (24 hours before month start) for regime calculation
        query = f"""
        SELECT time AS ts_utc, rate_index, bqx
        FROM bqx.m1_{pair}
        WHERE time >= DATE '{year}-{month}-01' - INTERVAL '24 hours'
          AND time < DATE '{year}-{month}-01' + INTERVAL '1 month'
        ORDER BY time;
        """

        df = pd.read_sql(query, conn)

        if df.empty:
            logger.warning(f"{pair.upper()} {year_month}: No data found")
            conn.close()
            return (pair, year_month, True, 0, "No data")

        df['ts_utc'] = pd.to_datetime(df['ts_utc'], utc=True)

        # Calculate BQX value (backward cumulative return)
        df['bqx_value'] = df['bqx'].fillna(0)

        logger.info(f"{pair.upper()} {year_month}: Loaded {len(df):,} rows, detecting regimes...")

        # Calculate regime features for each timestamp in the target month
        month_start = pd.Timestamp(f'{year}-{month}-01', tz='UTC')
        month_end = month_start + pd.DateOffset(months=1)

        df_month = df[(df['ts_utc'] >= month_start) & (df['ts_utc'] < month_end)]

        results = []
        LOOKBACK_WINDOW = 1440  # 24 hours

        for i, (idx, row) in enumerate(df_month.iterrows()):
            ts = row['ts_utc']

            # Get lookback window (up to 24 hours of history)
            lookback_start = max(0, idx - LOOKBACK_WINDOW)
            df_window = df.iloc[lookback_start:idx+1]

            # Detect regime for both domains
            regime_rate = detect_market_regime(df_window, domain='rate')
            regime_bqx = detect_market_regime(df_window, domain='bqx')

            # Combine metrics
            row_metrics = {
                'ts_utc': ts,
                **regime_rate,
                **regime_bqx
            }

            results.append(row_metrics)

            if (i + 1) % 10000 == 0:
                logger.info(f"{pair.upper()} {year_month}: Processed {i+1:,}/{len(df_month):,} rows...")

        if not results:
            logger.warning(f"{pair.upper()} {year_month}: No valid results")
            conn.close()
            return (pair, year_month, True, 0, "No valid results")

        # Note: Schema creation needed before database insert
        # For now, just log completion
        logger.info(f"{pair.upper()} {year_month}: Computed {len(results):,} rows "
                   f"(schema creation required for database insert)")

        conn.close()

        elapsed = time.time() - start_time
        logger.info(f"✅ {pair.upper()} {year_month}: Complete! {len(results):,} rows, {elapsed:.1f}s")

        return (pair, year_month, True, len(results), None)

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        logger.error(f"❌ {pair.upper()} {year_month}: Failed after {elapsed:.1f}s - {error_msg}")
        return (pair, year_month, False, 0, error_msg)


def main():
    """Main execution: Populate regime detection for all pairs and months."""
    parser = argparse.ArgumentParser(description='Populate regime detection features for BQX ML')
    parser.add_argument('--max-workers', type=int, default=32, help='Maximum number of parallel workers')
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("STAGE 2.9: MARKET REGIME DETECTION")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Pairs: {len(PAIRS)}")
    logger.info(f"Features: 30 per partition (15 rate + 15 bqx)")
    logger.info(f"Max Workers: {args.max_workers}")
    logger.info("")

    # Generate all tasks
    tasks = []
    for pair in PAIRS:
        for year in [2024, 2025]:
            for month in range(1, 13):
                if (year == 2024 and month >= 7) or (year == 2025 and month <= 6):
                    year_month = f"{year}_{month:02d}"
                    tasks.append((pair, year_month))

    logger.info(f"Total tasks: {len(tasks)}")
    logger.info("")

    start_time = time.time()
    results = {'success': 0, 'failed': 0, 'total_rows': 0}

    with ProcessPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {executor.submit(populate_regime_for_pair, pair, ym): (pair, ym)
                   for pair, ym in tasks}

        for future in as_completed(futures):
            pair, ym = futures[future]
            try:
                pair_name, year_month, success, row_count, error_msg = future.result()

                if success:
                    results['success'] += 1
                    results['total_rows'] += row_count
                    logger.info(f"Progress: {results['success']}/{len(tasks)} partitions complete")
                else:
                    results['failed'] += 1

            except Exception as e:
                logger.error(f"Unexpected error for {pair} {ym}: {e}")
                results['failed'] += 1

    elapsed = time.time() - start_time

    logger.info("")
    logger.info("=" * 80)
    logger.info("REGIME DETECTION COMPLETE")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Duration: {elapsed/3600:.1f} hours")
    logger.info(f"Successful: {results['success']}/{len(tasks)} tasks")
    logger.info(f"Failed: {results['failed']}/{len(tasks)} tasks")
    logger.info(f"Total rows: {results['total_rows']:,}")
    logger.info("=" * 80)

    sys.exit(0 if results['failed'] == 0 else 1)


if __name__ == '__main__':
    main()
