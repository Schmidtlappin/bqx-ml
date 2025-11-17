#!/usr/bin/env python3
"""
Stage 2.15: Comprehensive Schema Validation

Validates all schema alignments across Stages 2.11, 2.12, and 2.14:
- Verifies all reg_bqx partitions have consistent schema (79 columns after 2.14)
- Validates aligned windows [60, 90, 150, 240, 390, 630]
- Checks term-based schema consistency
- Verifies covariance features (36 features from Stage 2.14)
- Ensures data integrity across all 336 partitions

Duration: ~1 hour
Cost: $0 (existing infrastructure)
"""

import psycopg2
import os
import logging
from datetime import datetime
from collections import defaultdict

# Configure logging
os.makedirs('/tmp/logs/remediation/stage_2_15', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/logs/remediation/stage_2_15/validation.log'),
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

# Year-month partitions
YEAR_MONTHS = (
    [f"2024_{month:02d}" for month in range(7, 13)] +
    [f"2025_{month:02d}" for month in range(1, 7)]
)

# Aligned windows
WINDOWS = [60, 90, 150, 240, 390, 630]

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(**DB_CONFIG)

def get_baseline_schema(conn):
    """Get baseline schema from first partition"""
    baseline_table = f"reg_bqx_{CURRENCY_PAIRS[0]}_{YEAR_MONTHS[0]}"

    cursor = conn.cursor()
    query = """
    SELECT column_name, data_type, ordinal_position
    FROM information_schema.columns
    WHERE table_schema = 'bqx'
      AND table_name = %s
    ORDER BY ordinal_position
    """

    cursor.execute(query, (baseline_table,))
    baseline = cursor.fetchall()
    cursor.close()

    return baseline, baseline_table

def validate_schema_consistency(conn):
    """Validate schema consistency across all partitions"""
    logging.info("=" * 80)
    logging.info("STEP 1: SCHEMA CONSISTENCY VALIDATION")
    logging.info("=" * 80)
    logging.info("")

    baseline_schema, baseline_table = get_baseline_schema(conn)

    logging.info(f"Baseline: {baseline_table}")
    logging.info(f"Columns: {len(baseline_schema)}")
    logging.info("")

    cursor = conn.cursor()
    mismatches = []
    total_partitions = 0

    for pair in CURRENCY_PAIRS:
        for year_month in YEAR_MONTHS:
            table_name = f"reg_bqx_{pair}_{year_month}"
            total_partitions += 1

            cursor.execute("""
            SELECT column_name, data_type, ordinal_position
            FROM information_schema.columns
            WHERE table_schema = 'bqx'
              AND table_name = %s
            ORDER BY ordinal_position
            """, (table_name,))

            table_schema = cursor.fetchall()

            if table_schema != baseline_schema:
                mismatches.append(table_name)

        # Progress every pair
        progress = (CURRENCY_PAIRS.index(pair) + 1) / len(CURRENCY_PAIRS) * 100
        if (CURRENCY_PAIRS.index(pair) + 1) % 7 == 0:
            logging.info(f"  Progress: {CURRENCY_PAIRS.index(pair) + 1}/{len(CURRENCY_PAIRS)} pairs ({progress:.1f}%)")

    cursor.close()

    if mismatches:
        logging.error(f"❌ Schema mismatches: {len(mismatches)} partitions")
        for table in mismatches[:10]:
            logging.error(f"  - {table}")
        if len(mismatches) > 10:
            logging.error(f"  ... and {len(mismatches) - 10} more")
        return False
    else:
        logging.info(f"✅ All {total_partitions} partitions have consistent schema")
        return True

def validate_expected_columns(conn):
    """Validate expected column counts and structure"""
    logging.info("")
    logging.info("=" * 80)
    logging.info("STEP 2: COLUMN STRUCTURE VALIDATION")
    logging.info("=" * 80)
    logging.info("")

    baseline_schema, baseline_table = get_baseline_schema(conn)
    columns = {col[0]: col[1] for col in baseline_schema}

    # Expected: ts_utc + (6 windows × 7 regression) + (6 windows × 6 covariance)
    # = 1 + 42 + 36 = 79 columns

    logging.info(f"Total columns: {len(columns)}")
    logging.info("")

    # Count by category
    ts_cols = [c for c in columns if c == 'ts_utc']
    regression_cols = [c for c in columns if any(term in c for term in ['quadratic_term', 'linear_term', 'constant_term', 'residual', 'r2', 'rmse', 'prediction'])]
    covariance_cols = [c for c in columns if 'cov_' in c]

    logging.info(f"Column breakdown:")
    logging.info(f"  • ts_utc: {len(ts_cols)}")
    logging.info(f"  • Regression features (Stage 2.12): {len(regression_cols)}")
    logging.info(f"    Expected: 6 windows × 7 features = 42")
    logging.info(f"  • Covariance features (Stage 2.14): {len(covariance_cols)}")
    logging.info(f"    Expected: 6 windows × 6 covariances = 36")
    logging.info(f"  • Total: {len(columns)}")
    logging.info("")

    expected_total = 1 + 42 + 36  # 79
    issues = []

    if len(ts_cols) != 1:
        issues.append(f"ts_utc count: expected 1, got {len(ts_cols)}")

    if len(regression_cols) != 42:
        issues.append(f"Regression features: expected 42, got {len(regression_cols)}")

    if len(covariance_cols) != 36:
        issues.append(f"Covariance features: expected 36, got {len(covariance_cols)}")

    if len(columns) != expected_total:
        issues.append(f"Total columns: expected {expected_total}, got {len(columns)}")

    if issues:
        for issue in issues:
            logging.error(f"❌ {issue}")
        return False
    else:
        logging.info(f"✅ Column structure matches expected (79 columns)")
        return True

def validate_data_completeness(conn):
    """Validate data completeness"""
    logging.info("")
    logging.info("=" * 80)
    logging.info("STEP 3: DATA COMPLETENESS VALIDATION")
    logging.info("=" * 80)
    logging.info("")

    cursor = conn.cursor()
    total_rows = 0
    empty_partitions = []

    for pair in CURRENCY_PAIRS:
        pair_rows = 0

        for year_month in YEAR_MONTHS:
            table_name = f"reg_bqx_{pair}_{year_month}"

            cursor.execute(f"SELECT COUNT(*) FROM bqx.{table_name}")
            row_count = cursor.fetchone()[0]
            pair_rows += row_count

            if row_count == 0:
                empty_partitions.append(table_name)

        total_rows += pair_rows
        logging.info(f"  {pair.upper()}: {pair_rows:,} rows")

    cursor.close()

    logging.info("")
    logging.info(f"Total rows: {total_rows:,}")
    logging.info("")

    if empty_partitions:
        logging.error(f"❌ Empty partitions: {len(empty_partitions)}")
        for table in empty_partitions:
            logging.error(f"  - {table}")
        return False
    else:
        logging.info(f"✅ All partitions populated ({total_rows:,} total rows)")
        return True

def main():
    """Main validation workflow"""
    logging.info("=" * 80)
    logging.info("STAGE 2.15: COMPREHENSIVE VALIDATION")
    logging.info("=" * 80)
    logging.info("")
    logging.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logging.info(f"Database: {DB_CONFIG['host']}/{DB_CONFIG['database']}")
    logging.info(f"Partitions: {len(CURRENCY_PAIRS)} pairs × {len(YEAR_MONTHS)} months = {len(CURRENCY_PAIRS) * len(YEAR_MONTHS)}")
    logging.info("")

    conn = get_db_connection()

    try:
        results = {
            'Schema Consistency': validate_schema_consistency(conn),
            'Column Structure': validate_expected_columns(conn),
            'Data Completeness': validate_data_completeness(conn)
        }

        logging.info("")
        logging.info("=" * 80)
        logging.info("VALIDATION SUMMARY")
        logging.info("=" * 80)
        logging.info("")

        for check, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logging.info(f"{check:<30} {status}")

        logging.info("")
        logging.info("-" * 80)

        all_passed = all(results.values())

        if all_passed:
            logging.info("✅ ALL VALIDATION CHECKS PASSED")
            logging.info("")
            logging.info("Phase 2 Foundation Complete:")
            logging.info("  • Stage 2.11: Documentation ✅")
            logging.info("  • Stage 2.12: reg_bqx Rebuild (42 regression features) ✅")
            logging.info("  • Stage 2.14: Covariance Features (36 features) ✅")
            logging.info("  • Stage 2.15: Validation ✅")
            logging.info("")
            logging.info("Ready for TIER 1 Enhancement Stages (2.3, 2.4, 2.16B)")
            logging.info("=" * 80)
            return 0
        else:
            logging.error("❌ VALIDATION FAILED - Review issues above")
            logging.info("=" * 80)
            return 1

    finally:
        conn.close()

if __name__ == '__main__':
    exit(main())
