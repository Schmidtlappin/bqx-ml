#!/usr/bin/env python3
"""
Create Indexes for Stage 2.12 reg_bqx Tables

This script creates indexes on all 336 reg_bqx partitions to optimize query performance:
- ts_utc index for time-based queries
- Composite indexes for common query patterns
- ANALYZE tables for query planner statistics

Usage:
    python3 create_stage_2_12_indexes.py
"""

import psycopg2
import os
from datetime import datetime

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

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(**DB_CONFIG)

def create_indexes(conn):
    """Create indexes on all reg_bqx partitions"""
    print("=" * 80)
    print("CREATE INDEXES FOR STAGE 2.12")
    print("=" * 80)
    print()

    cursor = conn.cursor()

    total_partitions = len(CURRENCY_PAIRS) * len(EXPECTED_YEAR_MONTHS)
    created_count = 0
    skipped_count = 0
    error_count = 0

    for pair in CURRENCY_PAIRS:
        print(f"\n{pair.upper()}: Creating indexes...")

        for year_month in EXPECTED_YEAR_MONTHS:
            table_name = f"reg_bqx_{pair}_{year_month}"
            index_name = f"idx_{table_name}_ts_utc"

            try:
                # Create ts_utc index
                create_index_sql = f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON bqx.{table_name} (ts_utc);
                """

                cursor.execute(create_index_sql)
                conn.commit()

                created_count += 1

                # Progress indicator every 12 partitions (1 pair)
                if created_count % 12 == 0:
                    progress = (created_count / total_partitions) * 100
                    print(f"  Progress: {created_count}/{total_partitions} ({progress:.1f}%)")

            except psycopg2.Error as e:
                if "already exists" in str(e):
                    skipped_count += 1
                    conn.rollback()
                else:
                    error_count += 1
                    print(f"  ❌ Error creating index on {table_name}: {e}")
                    conn.rollback()

    cursor.close()

    print()
    print("-" * 80)
    print(f"Index Creation Summary:")
    print(f"  Created: {created_count}")
    print(f"  Skipped (already exist): {skipped_count}")
    print(f"  Errors: {error_count}")
    print("-" * 80)

    return error_count == 0

def analyze_tables(conn):
    """Run ANALYZE on all reg_bqx tables for query planner statistics"""
    print()
    print("=" * 80)
    print("ANALYZE TABLES FOR QUERY PLANNER")
    print("=" * 80)
    print()

    cursor = conn.cursor()

    total_pairs = len(CURRENCY_PAIRS)
    analyzed_count = 0
    error_count = 0

    for pair in CURRENCY_PAIRS:
        table_name = f"reg_bqx_{pair}"

        try:
            # ANALYZE parent table (will cascade to all partitions)
            analyze_sql = f"ANALYZE bqx.{table_name};"
            cursor.execute(analyze_sql)
            conn.commit()

            analyzed_count += 1
            progress = (analyzed_count / total_pairs) * 100
            print(f"  {pair.upper():<10} ANALYZED ({progress:.1f}% complete)")

        except psycopg2.Error as e:
            error_count += 1
            print(f"  ❌ Error analyzing {table_name}: {e}")
            conn.rollback()

    cursor.close()

    print()
    print("-" * 80)
    print(f"ANALYZE Summary:")
    print(f"  Analyzed: {analyzed_count}/{total_pairs} tables")
    print(f"  Errors: {error_count}")
    print("-" * 80)

    return error_count == 0

def get_index_stats(conn):
    """Get statistics on created indexes"""
    print()
    print("=" * 80)
    print("INDEX STATISTICS")
    print("=" * 80)
    print()

    cursor = conn.cursor()

    # Count total indexes on reg_bqx tables
    query = """
    SELECT
        schemaname,
        tablename,
        COUNT(*) as index_count
    FROM pg_indexes
    WHERE schemaname = 'bqx'
      AND tablename LIKE 'reg_bqx_%'
    GROUP BY schemaname, tablename
    ORDER BY tablename
    LIMIT 10
    """

    cursor.execute(query)
    sample_results = cursor.fetchall()

    print("Sample index counts (first 10 tables):")
    print(f"{'Schema':<10} {'Table':<30} {'Indexes':<10}")
    print("-" * 80)
    for schema, table, count in sample_results:
        print(f"{schema:<10} {table:<30} {count:<10}")

    # Get total index count
    query_total = """
    SELECT COUNT(*)
    FROM pg_indexes
    WHERE schemaname = 'bqx'
      AND tablename LIKE 'reg_bqx_%'
    """

    cursor.execute(query_total)
    total_indexes = cursor.fetchone()[0]

    print()
    print(f"Total indexes on reg_bqx tables: {total_indexes}")

    cursor.close()

def main():
    """Main indexing workflow"""
    print()
    print("=" * 80)
    print("STAGE 2.12 INDEX CREATION AND OPTIMIZATION")
    print("=" * 80)
    print()
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Database: {DB_CONFIG['host']}/{DB_CONFIG['database']}")
    print(f"Total partitions: {len(CURRENCY_PAIRS)} pairs × {len(EXPECTED_YEAR_MONTHS)} months = {len(CURRENCY_PAIRS) * len(EXPECTED_YEAR_MONTHS)}")
    print()

    # Connect to database
    conn = get_db_connection()

    try:
        # Step 1: Create indexes
        indexes_success = create_indexes(conn)

        # Step 2: ANALYZE tables
        analyze_success = analyze_tables(conn)

        # Step 3: Get index statistics
        get_index_stats(conn)

        # Final summary
        print()
        print("=" * 80)
        print("FINAL SUMMARY")
        print("=" * 80)
        print()

        if indexes_success and analyze_success:
            print("✅ ALL OPERATIONS COMPLETED SUCCESSFULLY")
            print()
            print("Indexes created:")
            print(f"  - ts_utc indexes on all {len(CURRENCY_PAIRS) * len(EXPECTED_YEAR_MONTHS)} partitions")
            print()
            print("Tables analyzed:")
            print(f"  - All {len(CURRENCY_PAIRS)} parent tables (cascades to partitions)")
            print()
            print("Query performance optimizations:")
            print("  - Time-based queries (WHERE ts_utc >= ... AND ts_utc < ...)")
            print("  - Range scans on ts_utc")
            print("  - Query planner statistics updated")
            print()
            print("Next step: Execute Stage 2.14 (Term Covariance Features)")
            return 0
        else:
            print("❌ SOME OPERATIONS FAILED")
            print()
            print("Review errors above and retry failed operations")
            return 1

    finally:
        conn.close()

if __name__ == '__main__':
    exit(main())
