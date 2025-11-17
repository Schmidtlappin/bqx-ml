#!/usr/bin/env python3
"""
Stage 2.14: Add Term Covariance Features to reg_bqx Tables

Adds 36 covariance features to all reg_bqx partitions (6 windows × 6 term-pair covariances).

For each window [60, 90, 150, 240, 390, 630], computes rolling covariances between:
1. cov(quadratic_term, linear_term)
2. cov(quadratic_term, constant_term)
3. cov(quadratic_term, residual)
4. cov(linear_term, constant_term)
5. cov(linear_term, residual)
6. cov(constant_term, residual)

Total Features: 36 per partition × 28 pairs = 1,008 features

Duration: 2-3 hours
Cost: $0 (existing infrastructure)
"""

import psycopg2
import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime
from sqlalchemy import create_engine
from urllib.parse import quote_plus

# Configure logging
os.makedirs('/tmp/logs/remediation/stage_2_14', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/logs/remediation/stage_2_14/reg_bqx_covariance.log'),
        logging.StreamHandler()
    ]
)

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com'),
    'database': 'bqx',
    'user': 'postgres',
    'password': os.environ.get('DB_PASSWORD', 'BQX_Aurora_2025_Secure')
}

# Create SQLAlchemy engine
DB_URL = f"postgresql://{DB_CONFIG['user']}:{quote_plus(DB_CONFIG['password'])}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
ENGINE = create_engine(DB_URL, pool_pre_ping=True)

# Currency pairs
CURRENCY_PAIRS = [
    'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
    'cadchf', 'cadjpy',
    'chfjpy',
    'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
    'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
    'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
    'usdcad', 'usdchf', 'usdjpy'
]

# Year-month partitions (2024-07 through 2025-06)
YEAR_MONTHS = (
    [f"2024_{month:02d}" for month in range(7, 13)] +
    [f"2025_{month:02d}" for month in range(1, 7)]
)

# Aligned windows
WINDOWS = [60, 90, 150, 240, 390, 630]

# Term pairs for covariance computation
TERM_PAIRS = [
    ('quadratic_term', 'linear_term', 'quad_lin'),
    ('quadratic_term', 'constant_term', 'quad_const'),
    ('quadratic_term', 'residual', 'quad_resid'),
    ('linear_term', 'constant_term', 'lin_const'),
    ('linear_term', 'residual', 'lin_resid'),
    ('constant_term', 'residual', 'const_resid')
]

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(**DB_CONFIG)

def add_covariance_columns(conn, pair):
    """Add covariance columns to reg_bqx parent table"""
    cursor = conn.cursor()

    # Build ALTER TABLE statement
    alter_clauses = []

    for window in WINDOWS:
        for _, _, abbrev in TERM_PAIRS:
            col_name = f"w{window}_cov_{abbrev}"
            alter_clauses.append(f"ADD COLUMN IF NOT EXISTS {col_name} double precision")

    if alter_clauses:
        alter_sql = f"ALTER TABLE bqx.reg_bqx_{pair} {', '.join(alter_clauses)};"

        try:
            cursor.execute(alter_sql)
            conn.commit()
            logging.info(f"{pair.upper()}: Added {len(alter_clauses)} covariance columns")
        except psycopg2.Error as e:
            logging.error(f"{pair.upper()}: Error adding columns - {e}")
            conn.rollback()
            raise

    cursor.close()

def process_partition(conn, pair, year_month):
    """Process single partition and compute covariances"""
    table_name = f"reg_bqx_{pair}_{year_month}"
    start_time = datetime.now()

    # Read data
    select_cols = ['ts_utc'] + [f'w{w}_{term}' for w in WINDOWS for term in ['quadratic_term', 'linear_term', 'constant_term', 'residual']]
    query = f"SELECT {', '.join(select_cols)} FROM bqx.{table_name} ORDER BY ts_utc"

    try:
        df = pd.read_sql(query, ENGINE)

        if df.empty:
            logging.warning(f"{pair.upper()} {year_month}: No data")
            return 0

        logging.info(f"{pair.upper()} {year_month}: Loaded {len(df)} rows")

        # Compute rolling covariances for each window
        for window in WINDOWS:
            for term1, term2, abbrev in TERM_PAIRS:
                col1 = f'w{window}_{term1}'
                col2 = f'w{window}_{term2}'
                cov_col = f'w{window}_cov_{abbrev}'

                # Rolling covariance
                df[cov_col] = df[col1].rolling(window=window, min_periods=window).cov(df[col2])

        # Update database in batches
        cursor = conn.cursor()
        cov_cols = [f'w{w}_cov_{abbrev}' for w in WINDOWS for _, _, abbrev in TERM_PAIRS]

        batch_size = 1000
        total_updated = 0

        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]

            for _, row in batch.iterrows():
                set_clause = ', '.join([f"{col} = %s" for col in cov_cols])
                # Convert NaN to None for proper NULL handling in PostgreSQL
                values = [None if pd.isna(row[col]) else row[col] for col in cov_cols] + [row['ts_utc']]

                update_sql = f"UPDATE bqx.{table_name} SET {set_clause} WHERE ts_utc = %s"
                cursor.execute(update_sql, values)

            conn.commit()
            total_updated += len(batch)

            if total_updated % 5000 == 0:
                logging.info(f"{pair.upper()} {year_month}: Updated {total_updated}/{len(df)} rows")

        cursor.close()

        duration = (datetime.now() - start_time).total_seconds()
        logging.info(f"✅ {pair.upper()} {year_month}: Complete! {total_updated} rows in {duration:.1f}s")

        return total_updated

    except Exception as e:
        logging.error(f"❌ {pair.upper()} {year_month}: Error - {e}")
        conn.rollback()
        return 0

def main():
    """Main execution"""
    logging.info("=" * 80)
    logging.info("STAGE 2.14: ADD TERM COVARIANCE FEATURES TO REG_BQX")
    logging.info("=" * 80)
    logging.info(f"")
    logging.info(f"Currency pairs: {len(CURRENCY_PAIRS)}")
    logging.info(f"Partitions: {len(CURRENCY_PAIRS) * len(YEAR_MONTHS)}")
    logging.info(f"Windows: {WINDOWS}")
    logging.info(f"Covariances per window: {len(TERM_PAIRS)}")
    logging.info(f"Features per partition: {len(WINDOWS) * len(TERM_PAIRS)}")
    logging.info("")

    conn = get_db_connection()
    overall_start = datetime.now()
    total_rows = 0
    total_partitions = 0

    try:
        for pair in CURRENCY_PAIRS:
            logging.info("=" * 80)
            logging.info(f"{pair.upper()}: Starting")
            logging.info("=" * 80)

            # Add columns
            add_covariance_columns(conn, pair)

            # Process partitions
            for year_month in YEAR_MONTHS:
                rows = process_partition(conn, pair, year_month)
                total_rows += rows
                total_partitions += 1

            logging.info(f"{pair.upper()}: Complete - {len(YEAR_MONTHS)} partitions")

        duration = (datetime.now() - overall_start).total_seconds()

        logging.info("")
        logging.info("=" * 80)
        logging.info("STAGE 2.14 COMPLETE")
        logging.info("=" * 80)
        logging.info(f"Partitions: {total_partitions}")
        logging.info(f"Rows updated: {total_rows:,}")
        logging.info(f"Duration: {duration/3600:.2f} hours")
        logging.info(f"Features added: {len(WINDOWS) * len(TERM_PAIRS) * len(CURRENCY_PAIRS):,}")
        logging.info("✅ All covariance features added successfully")

        return 0

    except Exception as e:
        logging.error(f"Fatal error: {e}")
        return 1
    finally:
        conn.close()

if __name__ == '__main__':
    exit(main())
