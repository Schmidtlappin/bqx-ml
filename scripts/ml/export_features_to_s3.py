#!/usr/bin/env python3
"""
Stage 2.7: Export Features to S3
Exports all BQX ML features to S3 in Parquet format for model training.

Export Strategy:
- Exports all feature tables for all pairs and months
- Joins features by timestamp for each pair/month
- Stores as compressed Parquet files in S3
- Partitioned by pair and year_month

Tables Exported (per pair):
1. m1_{pair} - Base OHLCV and rate_index
2. reg_{pair} - Regression features (rate_index domain)
3. reg_bqx_{pair} - Regression features (BQX domain)
4. technical_indicators_{pair} - RSI, MACD, Stochastic, etc.
5. currency_index_{pair} - Currency strength indices
6. arbitrage_{pair} - Triangular arbitrage opportunities
7. correlation_bqx_{pair} - Cross-pair correlations
8. enhanced_rmse_{pair} - Enhanced regression metrics
9. regime_{pair} - Market regime classification

Output Format:
- S3 Path: s3://bqx-ml-features/{pair}/{year_month}.parquet
- Compression: Snappy
- Estimated Size: 40-50 GB total (28 pairs × 12 months × ~50 MB)

Estimated Runtime: 3 hours with 8 workers on D64as_v5
"""

import psycopg2
import pandas as pd
import boto3
import pyarrow as pa
import pyarrow.parquet as pq
import logging
import sys
import os
import time
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from io import BytesIO

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com'),
    'database': 'bqx',
    'user': 'postgres',
    'password': os.environ.get('DB_PASSWORD', 'BQX_Aurora_2025_Secure')
}

# S3 configuration
S3_BUCKET = os.environ.get('S3_BUCKET', 'bqx-ml-features')
S3_PREFIX = 'features'

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
os.makedirs('/tmp/logs/stage_2_7', exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/logs/stage_2_7/export.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize S3 client
s3_client = boto3.client('s3', region_name='us-east-1')


def export_pair_month_to_s3(pair, year_month):
    """
    Export all features for one pair and one month to S3 Parquet.

    Args:
        pair: Currency pair (e.g., 'eurusd')
        year_month: Month partition (e.g., '2024_07')

    Returns:
        tuple: (pair, year_month, success, row_count, file_size_mb, error_msg)
    """
    start_time = time.time()

    try:
        logger.info(f"{pair.upper()} {year_month}: Starting feature export...")

        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)

        year, month = year_month.split('_')

        # Build comprehensive feature query joining all tables
        # NOTE: Updated to new term-based schema (quadratic_term, linear_term, constant_term, residual)
        # as of Stage 2.11 (reg_rate) and Stage 2.12 (reg_bqx)
        query = f"""
        WITH base AS (
            SELECT
                time AS ts_utc,
                open, high, low, close, volume,
                rate_index, bqx
            FROM bqx.m1_{pair}
            WHERE EXTRACT(YEAR FROM time) = {year}
              AND EXTRACT(MONTH FROM time) = {month}
        ),
        reg_rate AS (
            -- Regression features from rate_index domain (term-based)
            SELECT
                ts_utc,
                -- 60-minute window
                w60_quadratic_term AS reg_rate_w60_quad,
                w60_linear_term AS reg_rate_w60_lin,
                w60_constant_term AS reg_rate_w60_const,
                w60_residual AS reg_rate_w60_resid,
                w60_prediction AS reg_rate_w60_pred,
                w60_r2 AS reg_rate_w60_r2,
                w60_rmse AS reg_rate_w60_rmse,
                -- 90-minute window
                w90_quadratic_term AS reg_rate_w90_quad,
                w90_linear_term AS reg_rate_w90_lin,
                w90_constant_term AS reg_rate_w90_const,
                w90_residual AS reg_rate_w90_resid,
                w90_prediction AS reg_rate_w90_pred,
                w90_r2 AS reg_rate_w90_r2,
                w90_rmse AS reg_rate_w90_rmse,
                -- 150-minute window
                w150_quadratic_term AS reg_rate_w150_quad,
                w150_linear_term AS reg_rate_w150_lin,
                w150_constant_term AS reg_rate_w150_const,
                w150_residual AS reg_rate_w150_resid,
                w150_prediction AS reg_rate_w150_pred,
                w150_r2 AS reg_rate_w150_r2,
                w150_rmse AS reg_rate_w150_rmse,
                -- 240-minute window
                w240_quadratic_term AS reg_rate_w240_quad,
                w240_linear_term AS reg_rate_w240_lin,
                w240_constant_term AS reg_rate_w240_const,
                w240_residual AS reg_rate_w240_resid,
                w240_prediction AS reg_rate_w240_pred,
                w240_r2 AS reg_rate_w240_r2,
                w240_rmse AS reg_rate_w240_rmse,
                -- 390-minute window
                w390_quadratic_term AS reg_rate_w390_quad,
                w390_linear_term AS reg_rate_w390_lin,
                w390_constant_term AS reg_rate_w390_const,
                w390_residual AS reg_rate_w390_resid,
                w390_prediction AS reg_rate_w390_pred,
                w390_r2 AS reg_rate_w390_r2,
                w390_rmse AS reg_rate_w390_rmse,
                -- 630-minute window
                w630_quadratic_term AS reg_rate_w630_quad,
                w630_linear_term AS reg_rate_w630_lin,
                w630_constant_term AS reg_rate_w630_const,
                w630_residual AS reg_rate_w630_resid,
                w630_prediction AS reg_rate_w630_pred,
                w630_r2 AS reg_rate_w630_r2,
                w630_rmse AS reg_rate_w630_rmse
            FROM bqx.reg_{pair}_{year_month}
        ),
        reg_bqx AS (
            -- Regression features from BQX domain (term-based)
            SELECT
                ts_utc,
                -- 60-minute window
                w60_quadratic_term AS reg_bqx_w60_quad,
                w60_linear_term AS reg_bqx_w60_lin,
                w60_constant_term AS reg_bqx_w60_const,
                w60_residual AS reg_bqx_w60_resid,
                w60_prediction AS reg_bqx_w60_pred,
                w60_r2 AS reg_bqx_w60_r2,
                w60_rmse AS reg_bqx_w60_rmse,
                -- 90-minute window
                w90_quadratic_term AS reg_bqx_w90_quad,
                w90_linear_term AS reg_bqx_w90_lin,
                w90_constant_term AS reg_bqx_w90_const,
                w90_residual AS reg_bqx_w90_resid,
                w90_prediction AS reg_bqx_w90_pred,
                w90_r2 AS reg_bqx_w90_r2,
                w90_rmse AS reg_bqx_w90_rmse,
                -- 150-minute window
                w150_quadratic_term AS reg_bqx_w150_quad,
                w150_linear_term AS reg_bqx_w150_lin,
                w150_constant_term AS reg_bqx_w150_const,
                w150_residual AS reg_bqx_w150_resid,
                w150_prediction AS reg_bqx_w150_pred,
                w150_r2 AS reg_bqx_w150_r2,
                w150_rmse AS reg_bqx_w150_rmse,
                -- 240-minute window
                w240_quadratic_term AS reg_bqx_w240_quad,
                w240_linear_term AS reg_bqx_w240_lin,
                w240_constant_term AS reg_bqx_w240_const,
                w240_residual AS reg_bqx_w240_resid,
                w240_prediction AS reg_bqx_w240_pred,
                w240_r2 AS reg_bqx_w240_r2,
                w240_rmse AS reg_bqx_w240_rmse,
                -- 390-minute window
                w390_quadratic_term AS reg_bqx_w390_quad,
                w390_linear_term AS reg_bqx_w390_lin,
                w390_constant_term AS reg_bqx_w390_const,
                w390_residual AS reg_bqx_w390_resid,
                w390_prediction AS reg_bqx_w390_pred,
                w390_r2 AS reg_bqx_w390_r2,
                w390_rmse AS reg_bqx_w390_rmse,
                -- 630-minute window
                w630_quadratic_term AS reg_bqx_w630_quad,
                w630_linear_term AS reg_bqx_w630_lin,
                w630_constant_term AS reg_bqx_w630_const,
                w630_residual AS reg_bqx_w630_resid,
                w630_prediction AS reg_bqx_w630_pred,
                w630_r2 AS reg_bqx_w630_r2,
                w630_rmse AS reg_bqx_w630_rmse
            FROM bqx.reg_bqx_{pair}_{year_month}
        ),
        tech_indicators AS (
            -- Technical indicators (RSI, MACD, Stochastic, etc.)
            -- Select all columns with 'ti_' prefix for namespacing
            SELECT
                ts_utc,
                rsi_14 AS ti_rsi_14,
                macd_line AS ti_macd_line,
                macd_signal AS ti_macd_signal,
                macd_histogram AS ti_macd_histogram,
                stoch_k AS ti_stoch_k,
                stoch_d AS ti_stoch_d,
                bb_upper AS ti_bb_upper,
                bb_middle AS ti_bb_middle,
                bb_lower AS ti_bb_lower,
                atr_14 AS ti_atr_14
            FROM bqx.technical_indicators_{pair}_{year_month}
        ),
        currency_idx AS (
            -- Currency strength indices
            SELECT
                ts_utc,
                base_currency_strength AS ci_base_strength,
                quote_currency_strength AS ci_quote_strength,
                strength_divergence AS ci_strength_div
            FROM bqx.currency_index_{pair}_{year_month}
        ),
        arbitrage AS (
            -- Triangular arbitrage opportunities
            SELECT
                ts_utc,
                arbitrage_opportunity AS arb_opportunity,
                arbitrage_profit_bps AS arb_profit_bps,
                arbitrage_path AS arb_path
            FROM bqx.arbitrage_{pair}_{year_month}
        ),
        correlation AS (
            -- Cross-pair correlations + term covariances (added in Stage 2.14)
            SELECT
                ts_utc,
                correlation_score AS corr_score,
                correlation_rank AS corr_rank,
                -- Term covariances (added in Stage 2.14)
                cov_quad_lin_bqx_60min AS corr_cov_quad_lin,
                cov_resid_quad_bqx_60min AS corr_cov_resid_quad,
                cov_resid_lin_bqx_60min AS corr_cov_resid_lin,
                corr_quad_lin_bqx_60min AS corr_corr_quad_lin,
                corr_resid_quad_bqx_60min AS corr_corr_resid_quad,
                corr_resid_lin_bqx_60min AS corr_corr_resid_lin
            FROM bqx.correlation_bqx_{pair}_{year_month}
        ),
        enhanced_rmse AS (
            -- Enhanced regression metrics
            SELECT
                ts_utc,
                enhanced_rmse_score AS rmse_enhanced_score,
                rmse_trend AS rmse_trend,
                rmse_volatility AS rmse_volatility
            FROM bqx.enhanced_rmse_{pair}_{year_month}
        ),
        regime AS (
            -- Market regime classification
            SELECT
                ts_utc,
                regime_type AS regime_type,
                regime_confidence AS regime_confidence,
                regime_duration_minutes AS regime_duration
            FROM bqx.regime_{pair}_{year_month}
        )
        SELECT
            base.ts_utc,
            base.open, base.high, base.low, base.close, base.volume,
            base.rate_index, base.bqx,
            -- Regression features (both domains)
            reg_rate.* EXCEPT (ts_utc),
            reg_bqx.* EXCEPT (ts_utc),
            -- Additional feature families
            tech_indicators.* EXCEPT (ts_utc),
            currency_idx.* EXCEPT (ts_utc),
            arbitrage.* EXCEPT (ts_utc),
            correlation.* EXCEPT (ts_utc),
            enhanced_rmse.* EXCEPT (ts_utc),
            regime.* EXCEPT (ts_utc)
        FROM base
        LEFT JOIN reg_rate USING (ts_utc)
        LEFT JOIN reg_bqx USING (ts_utc)
        LEFT JOIN tech_indicators USING (ts_utc)
        LEFT JOIN currency_idx USING (ts_utc)
        LEFT JOIN arbitrage USING (ts_utc)
        LEFT JOIN correlation USING (ts_utc)
        LEFT JOIN enhanced_rmse USING (ts_utc)
        LEFT JOIN regime USING (ts_utc)
        ORDER BY base.ts_utc;
        """

        # Execute query
        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            logger.warning(f"{pair.upper()} {year_month}: No data found")
            return (pair, year_month, True, 0, 0, "No data")

        # Convert timestamp to proper datetime
        df['ts_utc'] = pd.to_datetime(df['ts_utc'], utc=True)

        # Add metadata columns
        df['pair'] = pair
        df['year'] = int(year)
        df['month'] = int(month)

        logger.info(f"{pair.upper()} {year_month}: Loaded {len(df):,} rows, {len(df.columns)} columns")

        # Convert to PyArrow Table for efficient Parquet writing
        table = pa.Table.from_pandas(df)

        # Write to in-memory buffer
        buffer = BytesIO()
        pq.write_table(
            table,
            buffer,
            compression='snappy',
            use_dictionary=True,
            version='2.6'
        )

        # Get buffer size
        buffer.seek(0, 2)  # Seek to end
        file_size_bytes = buffer.tell()
        file_size_mb = file_size_bytes / (1024 * 1024)
        buffer.seek(0)  # Reset to beginning

        # Upload to S3
        s3_key = f"{S3_PREFIX}/{pair}/{year_month}.parquet"

        logger.info(f"{pair.upper()} {year_month}: Uploading to s3://{S3_BUCKET}/{s3_key} ({file_size_mb:.2f} MB)...")

        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=buffer.getvalue(),
            ContentType='application/octet-stream',
            Metadata={
                'pair': pair,
                'year_month': year_month,
                'row_count': str(len(df)),
                'column_count': str(len(df.columns))
            }
        )

        elapsed = time.time() - start_time
        logger.info(f"✅ {pair.upper()} {year_month}: Complete! {len(df):,} rows, "
                   f"{file_size_mb:.2f} MB, {elapsed:.1f}s")

        return (pair, year_month, True, len(df), file_size_mb, None)

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        logger.error(f"❌ {pair.upper()} {year_month}: Failed after {elapsed:.1f}s - {error_msg}")
        return (pair, year_month, False, 0, 0, error_msg)


def verify_s3_export(pair, year_month):
    """
    Verify that exported Parquet file is readable and valid.

    Args:
        pair: Currency pair
        year_month: Month partition

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        s3_key = f"{S3_PREFIX}/{pair}/{year_month}.parquet"

        # Read from S3
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
        buffer = BytesIO(response['Body'].read())

        # Read Parquet
        table = pq.read_table(buffer)
        df = table.to_pandas()

        # Basic validation
        if len(df) == 0:
            logger.error(f"Validation failed: {pair} {year_month} - Empty DataFrame")
            return False

        if 'ts_utc' not in df.columns:
            logger.error(f"Validation failed: {pair} {year_month} - Missing ts_utc column")
            return False

        logger.info(f"✅ Validation passed: {pair} {year_month} - {len(df):,} rows, {len(df.columns)} columns")
        return True

    except Exception as e:
        logger.error(f"Validation failed: {pair} {year_month} - {e}")
        return False


def main():
    """Main execution: Export all features to S3."""
    parser = argparse.ArgumentParser(description='Export BQX ML features to S3')
    parser.add_argument('--max-workers', type=int, default=8, help='Maximum number of parallel workers')
    parser.add_argument('--verify', action='store_true', help='Verify exported files after export')
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("STAGE 2.7: EXPORT FEATURES TO S3")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Pairs: {len(PAIRS)}")
    logger.info(f"S3 Bucket: s3://{S3_BUCKET}/{S3_PREFIX}/")
    logger.info(f"Format: Parquet (Snappy compression)")
    logger.info(f"Max Workers: {args.max_workers}")
    logger.info(f"Verification: {'Enabled' if args.verify else 'Disabled'}")
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
    results = {'success': 0, 'failed': 0, 'total_rows': 0, 'total_size_mb': 0}

    with ProcessPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {executor.submit(export_pair_month_to_s3, pair, ym): (pair, ym)
                   for pair, ym in tasks}

        for future in as_completed(futures):
            pair, ym = futures[future]
            try:
                pair_name, year_month, success, row_count, file_size_mb, error_msg = future.result()

                if success:
                    results['success'] += 1
                    results['total_rows'] += row_count
                    results['total_size_mb'] += file_size_mb
                    logger.info(f"Progress: {results['success']}/{len(tasks)} exports complete "
                               f"({results['total_size_mb']:.1f} MB)")
                else:
                    results['failed'] += 1

            except Exception as e:
                logger.error(f"Unexpected error for {pair} {ym}: {e}")
                results['failed'] += 1

    # Verification phase
    if args.verify and results['failed'] == 0:
        logger.info("")
        logger.info("=" * 80)
        logger.info("VERIFICATION PHASE")
        logger.info("=" * 80)
        logger.info("")

        verification_failed = 0
        for pair, ym in tasks:
            if not verify_s3_export(pair, ym):
                verification_failed += 1

        logger.info(f"Verification: {len(tasks) - verification_failed}/{len(tasks)} files valid")

    elapsed = time.time() - start_time

    logger.info("")
    logger.info("=" * 80)
    logger.info("S3 EXPORT COMPLETE")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Duration: {elapsed/3600:.1f} hours")
    logger.info(f"Successful: {results['success']}/{len(tasks)} tasks")
    logger.info(f"Failed: {results['failed']}/{len(tasks)} tasks")
    logger.info(f"Total rows: {results['total_rows']:,}")
    logger.info(f"Total size: {results['total_size_mb']/1024:.2f} GB")
    logger.info(f"Average file size: {results['total_size_mb']/results['success']:.2f} MB"
               if results['success'] > 0 else "N/A")
    logger.info("=" * 80)

    sys.exit(0 if results['failed'] == 0 else 1)


if __name__ == '__main__':
    main()
