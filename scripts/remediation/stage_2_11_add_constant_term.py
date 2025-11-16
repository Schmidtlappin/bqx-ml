#!/usr/bin/env python3
"""
Stage 2.11: Add constant_term to reg_rate Partitions
Adds missing constant_term columns to all 336 reg_rate_* partitions for term-based architecture.

Schema Enhancement:
- Add 6 constant_term columns (one per window: 60, 90, 150, 240, 390, 630)
- Populate from existing w*_c_coef columns
- Validate data integrity

Estimated Duration: 30 minutes
Estimated Cost: $0.16
Risk: LOW (additive only, no data loss)
"""

import psycopg2
import logging
import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

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

# All 12 months (July 2024 - June 2025)
MONTHS = [
    '2024_07', '2024_08', '2024_09', '2024_10', '2024_11', '2024_12',
    '2025_01', '2025_02', '2025_03', '2025_04', '2025_05', '2025_06'
]

# Windows to process
WINDOWS = [60, 90, 150, 240, 390, 630]

# Create logs directory
os.makedirs('/tmp/logs/remediation/stage_2_11', exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/logs/remediation/stage_2_11/migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def add_constant_term_columns(pair):
    """
    Add constant_term columns to a single reg_rate parent table.
    This automatically applies to all child partitions.

    Args:
        pair: Currency pair (e.g., 'eurusd')

    Returns:
        tuple: (pair, success, error_msg)
    """
    start_time = time.time()
    table_name = f"reg_{pair}"

    try:
        logger.info(f"{pair.upper()}: Starting constant_term addition to parent table...")

        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Check if parent table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'bqx'
                AND table_name = %s
            )
        """, (table_name,))

        if not cur.fetchone()[0]:
            logger.warning(f"{pair.upper()}: Parent table does not exist, skipping")
            cur.close()
            conn.close()
            return (pair, True, "Table does not exist")

        # Add constant_term columns for each window
        for window in WINDOWS:
            col_name = f"w{window}_constant_term"

            # Check if column already exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_schema = 'bqx'
                    AND table_name = %s
                    AND column_name = %s
                )
            """, (table_name, col_name))

            if cur.fetchone()[0]:
                logger.info(f"{pair.upper()}: {col_name} already exists, skipping")
                continue

            # Add column to parent table (automatically applies to partitions)
            logger.info(f"{pair.upper()}: Adding {col_name} to parent table...")
            cur.execute(f"""
                ALTER TABLE bqx.{table_name}
                ADD COLUMN {col_name} DOUBLE PRECISION
            """)
            logger.info(f"{pair.upper()}: {col_name} added to parent and all partitions")

        # Populate constant_term from c_coef across all partitions
        logger.info(f"{pair.upper()}: Populating constant_term columns across all partitions...")
        for window in WINDOWS:
            cur.execute(f"""
                UPDATE bqx.{table_name}
                SET w{window}_constant_term = w{window}_c_coef
                WHERE w{window}_c_coef IS NOT NULL
            """)
            rows_updated = cur.rowcount
            logger.info(f"{pair.upper()}: w{window}_constant_term populated ({rows_updated:,} rows across all partitions)")

        # Add table comment
        cur.execute(f"""
            COMMENT ON TABLE bqx.{table_name} IS
            'Regression features calculated from rate_index (normalized forex rate).
            Source: rate_index column from m1_{pair} table (normalized to 100 at t=0).
            NOT calculated from absolute rate values.
            Migration: constant_term columns added 2025-11-16 (Stage 2.11).'
        """)

        # Validate data integrity across all partitions
        logger.info(f"{pair.upper()}: Validating data integrity across all partitions...")
        validation_errors = 0

        for window in WINDOWS:
            cur.execute(f"""
                SELECT COUNT(*)
                FROM bqx.{table_name}
                WHERE w{window}_c_coef IS NOT NULL
                AND ABS(w{window}_constant_term - w{window}_c_coef) > 0.000001
            """)
            error_count = cur.fetchone()[0]
            if error_count > 0:
                validation_errors += error_count
                logger.error(f"{pair.upper()}: w{window}_constant_term validation failed ({error_count} mismatches)")

        if validation_errors > 0:
            conn.rollback()
            cur.close()
            conn.close()
            return (pair, False, f"Validation failed: {validation_errors} mismatches")

        # Commit changes
        conn.commit()
        cur.close()
        conn.close()

        elapsed = time.time() - start_time
        logger.info(f"✅ {pair.upper()}: Complete! All partitions updated ({elapsed:.1f}s)")

        return (pair, True, None)

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        logger.error(f"❌ {pair.upper()}: Failed after {elapsed:.1f}s - {error_msg}")
        return (pair, False, error_msg)


def validate_all_partitions():
    """
    Validate that all partitions have constant_term columns properly populated.

    Returns:
        dict: Validation results
    """
    logger.info("=" * 80)
    logger.info("VALIDATION PHASE: Checking all partitions")
    logger.info("=" * 80)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    results = {
        'total_partitions': 0,
        'valid_partitions': 0,
        'missing_columns': 0,
        'validation_errors': 0
    }

    for pair in PAIRS:
        for year_month in MONTHS:
            table_name = f"reg_{pair}_{year_month}"

            # Check if table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'bqx'
                    AND table_name = %s
                )
            """, (table_name,))

            if not cur.fetchone()[0]:
                continue

            results['total_partitions'] += 1

            # Check for constant_term columns
            missing_cols = []
            for window in WINDOWS:
                col_name = f"w{window}_constant_term"
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_schema = 'bqx'
                        AND table_name = %s
                        AND column_name = %s
                    )
                """, (table_name, col_name))

                if not cur.fetchone()[0]:
                    missing_cols.append(col_name)

            if missing_cols:
                results['missing_columns'] += 1
                logger.warning(f"{pair.upper()} {year_month}: Missing columns: {', '.join(missing_cols)}")
                continue

            # Validate constant_term = c_coef
            validation_ok = True
            for window in WINDOWS:
                cur.execute(f"""
                    SELECT COUNT(*)
                    FROM bqx.{table_name}
                    WHERE w{window}_c_coef IS NOT NULL
                    AND ABS(w{window}_constant_term - w{window}_c_coef) > 0.000001
                """)
                error_count = cur.fetchone()[0]
                if error_count > 0:
                    validation_ok = False
                    logger.error(f"{pair.upper()} {year_month}: w{window}_constant_term mismatch ({error_count} rows)")

            if validation_ok:
                results['valid_partitions'] += 1
            else:
                results['validation_errors'] += 1

    cur.close()
    conn.close()

    return results


def main():
    """Main execution: Add constant_term to all reg_rate parent tables."""
    logger.info("=" * 80)
    logger.info("STAGE 2.11: ADD constant_term TO reg_rate PARENT TABLES")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Currency pairs: {len(PAIRS)}")
    logger.info(f"Parent tables to modify: {len(PAIRS)}")
    logger.info(f"Columns per table: {len(WINDOWS)}")
    logger.info(f"Total columns to add: {len(PAIRS) * len(WINDOWS)}")
    logger.info(f"Partitions affected: {len(PAIRS) * len(MONTHS)} (automatically)")
    logger.info("")

    start_time = time.time()
    results = {'success': 0, 'failed': 0, 'skipped': 0}

    # Process all parent tables (single-threaded for safety)
    for pair in PAIRS:
        pair_name, success, error_msg = add_constant_term_columns(pair)

        if success:
            if error_msg and "does not exist" in error_msg:
                results['skipped'] += 1
            else:
                results['success'] += 1
        else:
            results['failed'] += 1

    # Validation phase
    logger.info("")
    validation_results = validate_all_partitions()

    elapsed = time.time() - start_time

    logger.info("")
    logger.info("=" * 80)
    logger.info("STAGE 2.11 COMPLETE")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Duration: {elapsed/60:.1f} minutes")
    logger.info(f"Successful: {results['success']}/{len(PAIRS)} parent tables")
    logger.info(f"Failed: {results['failed']}/{len(PAIRS)} parent tables")
    logger.info(f"Skipped: {results['skipped']}/{len(PAIRS)} parent tables")
    logger.info("")
    logger.info("Validation Results:")
    logger.info(f"  Total partitions checked: {validation_results['total_partitions']}")
    logger.info(f"  Valid partitions: {validation_results['valid_partitions']}")
    logger.info(f"  Missing columns: {validation_results['missing_columns']}")
    logger.info(f"  Validation errors: {validation_results['validation_errors']}")
    logger.info("")

    if results['failed'] > 0 or validation_results['validation_errors'] > 0:
        logger.error("❌ Stage 2.11 completed with errors")
        logger.info("=" * 80)
        return 1
    else:
        logger.info("✅ Stage 2.11 completed successfully - All partitions validated")
        logger.info("=" * 80)
        return 0


if __name__ == '__main__':
    sys.exit(main())
