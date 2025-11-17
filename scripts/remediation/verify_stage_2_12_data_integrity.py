#!/usr/bin/env python3
"""
Verify Stage 2.12 Data Integrity

This script verifies that Stage 2.12 (reg_bqx rebuild) completed successfully
by checking:
- Row counts for all 336 partitions (28 pairs × 12 months)
- All year_month partitions exist for each pair
- No critical NULL values
- Schema consistency across all partitions

Usage:
    python3 verify_stage_2_12_data_integrity.py
"""

import psycopg2
import os
from datetime import datetime
from collections import defaultdict

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com'),
    'database': 'bqx',
    'user': 'postgres',
    'password': os.environ.get('DB_PASSWORD', 'BQX_Aurora_2025_Secure')
}

# Expected currency pairs
CURRENCY_PAIRS = [
    'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
    'cadchf', 'cadjpy',
    'chfjpy',
    'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
    'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
    'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
    'usdcad', 'usdchf', 'usdjpy'
]

# Expected year_month partitions (2024-07 through 2025-06)
EXPECTED_YEAR_MONTHS = (
    [f"2024_{month:02d}" for month in range(7, 13)] +  # 2024-07 through 2024-12
    [f"2025_{month:02d}" for month in range(1, 7)]      # 2025-01 through 2025-06
)

# Aligned windows
WINDOWS = [60, 90, 150, 240, 390, 630]

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(**DB_CONFIG)

def verify_partition_existence(conn):
    """Verify all expected partitions exist"""
    print("=" * 80)
    print("STEP 1: Verify Partition Existence")
    print("=" * 80)
    print()

    cursor = conn.cursor()

    # Get all reg_bqx partitions
    query = """
    SELECT tablename
    FROM pg_tables
    WHERE schemaname = 'bqx'
      AND tablename LIKE 'reg_bqx_%'
      AND tablename ~ '^reg_bqx_[a-z]+_\d{4}_\d{2}$'
    ORDER BY tablename
    """

    cursor.execute(query)
    existing_partitions = {row[0] for row in cursor.fetchall()}

    # Build expected partitions
    expected_partitions = set()
    for pair in CURRENCY_PAIRS:
        for year_month in EXPECTED_YEAR_MONTHS:
            expected_partitions.add(f"reg_bqx_{pair}_{year_month}")

    # Check for missing partitions
    missing = expected_partitions - existing_partitions
    extra = existing_partitions - expected_partitions

    print(f"Expected partitions: {len(expected_partitions)} (28 pairs × 12 months)")
    print(f"Existing partitions: {len(existing_partitions)}")
    print()

    if missing:
        print(f"⚠️  MISSING PARTITIONS ({len(missing)}):")
        for partition in sorted(missing):
            print(f"  - {partition}")
        print()
    else:
        print("✅ All expected partitions exist")
        print()

    if extra:
        print(f"ℹ️  EXTRA PARTITIONS ({len(extra)}):")
        for partition in sorted(extra):
            print(f"  - {partition}")
        print()

    cursor.close()
    return len(missing) == 0

def verify_row_counts(conn):
    """Verify row counts for all partitions"""
    print("=" * 80)
    print("STEP 2: Verify Row Counts")
    print("=" * 80)
    print()

    cursor = conn.cursor()

    # Get all partition row counts
    pair_stats = defaultdict(lambda: {'partitions': 0, 'total_rows': 0, 'empty_partitions': []})

    for pair in CURRENCY_PAIRS:
        for year_month in EXPECTED_YEAR_MONTHS:
            table_name = f"reg_bqx_{pair}_{year_month}"

            try:
                query = f"SELECT COUNT(*) FROM bqx.{table_name}"
                cursor.execute(query)
                row_count = cursor.fetchone()[0]

                pair_stats[pair]['partitions'] += 1
                pair_stats[pair]['total_rows'] += row_count

                if row_count == 0:
                    pair_stats[pair]['empty_partitions'].append(year_month)

            except psycopg2.Error as e:
                print(f"❌ Error querying {table_name}: {e}")

    # Print results
    total_rows = 0
    total_partitions = 0
    empty_count = 0

    print(f"{'Pair':<10} {'Partitions':<12} {'Total Rows':<15} {'Avg Rows/Month':<20} {'Empty':<10}")
    print("-" * 80)

    for pair in sorted(CURRENCY_PAIRS):
        stats = pair_stats[pair]
        avg_rows = stats['total_rows'] / stats['partitions'] if stats['partitions'] > 0 else 0
        empty_str = f"{len(stats['empty_partitions'])} months" if stats['empty_partitions'] else "None"

        print(f"{pair:<10} {stats['partitions']:<12} {stats['total_rows']:<15,} {avg_rows:<20,.0f} {empty_str:<10}")

        total_rows += stats['total_rows']
        total_partitions += stats['partitions']
        empty_count += len(stats['empty_partitions'])

    print("-" * 80)
    print(f"{'TOTAL':<10} {total_partitions:<12} {total_rows:<15,} {total_rows/total_partitions if total_partitions > 0 else 0:<20,.0f} {empty_count:<10}")
    print()

    # Report empty partitions
    if empty_count > 0:
        print(f"⚠️  EMPTY PARTITIONS FOUND ({empty_count}):")
        for pair in sorted(CURRENCY_PAIRS):
            if pair_stats[pair]['empty_partitions']:
                empty_months = ', '.join(pair_stats[pair]['empty_partitions'])
                print(f"  - {pair}: {empty_months}")
        print()
    else:
        print("✅ No empty partitions found")
        print()

    cursor.close()
    return empty_count == 0

def verify_schema_consistency(conn):
    """Verify schema consistency across all partitions"""
    print("=" * 80)
    print("STEP 3: Verify Schema Consistency")
    print("=" * 80)
    print()

    cursor = conn.cursor()

    # Get schema for first partition as baseline
    baseline_table = f"reg_bqx_{CURRENCY_PAIRS[0]}_{EXPECTED_YEAR_MONTHS[0]}"

    query = """
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'bqx'
      AND table_name = %s
    ORDER BY ordinal_position
    """

    cursor.execute(query, (baseline_table,))
    baseline_schema = cursor.fetchall()

    print(f"Baseline schema (from {baseline_table}):")
    print(f"  Columns: {len(baseline_schema)}")
    print()

    # Check all partitions match baseline
    schema_mismatches = []

    for pair in CURRENCY_PAIRS:
        for year_month in EXPECTED_YEAR_MONTHS:
            table_name = f"reg_bqx_{pair}_{year_month}"

            cursor.execute(query, (table_name,))
            table_schema = cursor.fetchall()

            if table_schema != baseline_schema:
                schema_mismatches.append(table_name)

    if schema_mismatches:
        print(f"❌ SCHEMA MISMATCHES FOUND ({len(schema_mismatches)}):")
        for table in schema_mismatches:
            print(f"  - {table}")
        print()
    else:
        print(f"✅ All {len(CURRENCY_PAIRS) * len(EXPECTED_YEAR_MONTHS)} partitions have consistent schema")
        print()

    # Display expected columns
    print("Expected columns:")
    for col_name, data_type, is_nullable in baseline_schema:
        print(f"  - {col_name:<30} {data_type:<20} {'NULL' if is_nullable == 'YES' else 'NOT NULL'}")
    print()

    cursor.close()
    return len(schema_mismatches) == 0

def verify_null_values(conn):
    """Verify no unexpected NULL values in critical columns"""
    print("=" * 80)
    print("STEP 4: Verify NULL Values in Critical Columns")
    print("=" * 80)
    print()

    cursor = conn.cursor()

    # Critical columns that should not be NULL
    critical_columns = ['ts_utc'] + [
        f'w{w}_{col}'
        for w in WINDOWS
        for col in ['quadratic_term', 'linear_term', 'constant_term', 'r2', 'rmse']
    ]

    null_issues = []

    # Sample 3 partitions per pair (first, middle, last month)
    sample_months = [EXPECTED_YEAR_MONTHS[0], EXPECTED_YEAR_MONTHS[5], EXPECTED_YEAR_MONTHS[11]]

    for pair in CURRENCY_PAIRS:
        for year_month in sample_months:
            table_name = f"reg_bqx_{pair}_{year_month}"

            for column in critical_columns:
                query = f"SELECT COUNT(*) FROM bqx.{table_name} WHERE {column} IS NULL"

                try:
                    cursor.execute(query)
                    null_count = cursor.fetchone()[0]

                    if null_count > 0:
                        null_issues.append({
                            'table': table_name,
                            'column': column,
                            'null_count': null_count
                        })
                except psycopg2.Error as e:
                    print(f"⚠️  Error checking {table_name}.{column}: {e}")

    if null_issues:
        print(f"⚠️  NULL VALUES FOUND ({len(null_issues)} issues):")
        for issue in null_issues[:20]:  # Show first 20
            print(f"  - {issue['table']}.{issue['column']}: {issue['null_count']} NULLs")
        if len(null_issues) > 20:
            print(f"  ... and {len(null_issues) - 20} more issues")
        print()
    else:
        print(f"✅ No NULL values found in critical columns (sampled {len(CURRENCY_PAIRS) * len(sample_months)} partitions)")
        print()

    cursor.close()
    return len(null_issues) == 0

def main():
    """Main verification workflow"""
    print()
    print("=" * 80)
    print("STAGE 2.12 DATA INTEGRITY VERIFICATION")
    print("=" * 80)
    print()
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Database: {DB_CONFIG['host']}/{DB_CONFIG['database']}")
    print(f"Expected partitions: {len(CURRENCY_PAIRS)} pairs × {len(EXPECTED_YEAR_MONTHS)} months = {len(CURRENCY_PAIRS) * len(EXPECTED_YEAR_MONTHS)}")
    print()

    # Connect to database
    conn = get_db_connection()

    try:
        # Run all verification steps
        results = {
            'partition_existence': verify_partition_existence(conn),
            'row_counts': verify_row_counts(conn),
            'schema_consistency': verify_schema_consistency(conn),
            'null_values': verify_null_values(conn)
        }

        # Final summary
        print("=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)
        print()

        all_passed = all(results.values())

        for check, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{check.replace('_', ' ').title():<30} {status}")

        print()
        print("-" * 80)

        if all_passed:
            print("✅ ALL CHECKS PASSED - Stage 2.12 data integrity verified")
            print()
            print("Next step: Create indexes and optimize tables")
        else:
            print("❌ SOME CHECKS FAILED - Review issues above")
            print()
            print("Action required: Investigate and remediate failed checks")

        print("=" * 80)
        print()

        return 0 if all_passed else 1

    finally:
        conn.close()

if __name__ == '__main__':
    exit(main())
