#!/usr/bin/env python3
"""
Check BQX Database Indexes and Optimization Status
"""

import psycopg2

# Aurora credentials (Trillium BQX cluster)
DB_HOST = "trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com"
DB_PORT = 5432
DB_NAME = "bqx"
DB_USER = "postgres"
DB_PASSWORD = "BQX_Aurora_2025_Secure"


def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode="require",
    )


def get_all_tables():
    """Get all tables in BQX schema"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables
        WHERE schemaname = 'bqx'
        ORDER BY tablename;
    """)

    tables = cur.fetchall()
    cur.close()
    conn.close()

    return tables


def get_table_indexes(table_name):
    """Get all indexes for a table"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                i.indexname,
                i.indexdef,
                COALESCE(pg_size_pretty(pg_relation_size(('bqx.'||i.indexname)::regclass)), 'N/A') as index_size,
                idx.indisunique as is_unique,
                idx.indisprimary as is_primary
            FROM pg_indexes i
            LEFT JOIN pg_class c ON c.relname = i.indexname AND c.relnamespace = 'bqx'::regnamespace
            LEFT JOIN pg_index idx ON idx.indexrelid = c.oid
            WHERE i.schemaname = 'bqx'
              AND i.tablename = %s
            ORDER BY i.indexname;
        """, (table_name,))

        indexes = cur.fetchall()
    except Exception as e:
        print(f"  Error fetching indexes: {e}")
        indexes = []
    finally:
        cur.close()
        conn.close()

    return indexes


def get_table_stats():
    """Get table statistics"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            schemaname,
            relname,
            n_live_tup as row_count,
            n_dead_tup as dead_rows,
            last_vacuum,
            last_autovacuum,
            last_analyze,
            last_autoanalyze
        FROM pg_stat_user_tables
        WHERE schemaname = 'bqx'
        ORDER BY relname;
    """)

    stats = cur.fetchall()
    cur.close()
    conn.close()

    return stats


def check_partition_info():
    """Check partition configuration"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            parent.relname as parent_table,
            child.relname as partition_name,
            pg_get_expr(child.relpartbound, child.oid) as partition_bound
        FROM pg_inherits
        JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
        JOIN pg_class child ON pg_inherits.inhrelid = child.oid
        JOIN pg_namespace nmsp_parent ON parent.relnamespace = nmsp_parent.oid
        WHERE nmsp_parent.nspname = 'bqx'
        ORDER BY parent.relname, partition_name;
    """)

    partitions = cur.fetchall()
    cur.close()
    conn.close()

    return partitions


def main():
    print("=" * 100)
    print("BQX DATABASE INDEX AND OPTIMIZATION AUDIT")
    print("=" * 100)
    print()

    # Get all tables
    print("1. ALL TABLES IN BQX SCHEMA")
    print("-" * 100)
    tables = get_all_tables()
    print(f"{'Schema':<15} {'Table':<40} {'Size':<15}")
    print("-" * 100)
    for schema, table, size in tables[:20]:
        print(f"{schema:<15} {table:<40} {size:<15}")
    if len(tables) > 20:
        print(f"... and {len(tables) - 20} more tables")
    print(f"\nTotal tables: {len(tables)}")
    print()

    # Separate parent tables from partitions
    parent_tables = [t for t in tables if '_2024m' not in t[1] and '_2025m' not in t[1]]
    partition_tables = [t for t in tables if '_2024m' in t[1] or '_2025m' in t[1]]

    print(f"Parent tables: {len(parent_tables)}")
    print(f"Partition tables: {len(partition_tables)}")
    print()

    # Check indexes on parent tables (excluding bqx_ tables being backfilled)
    print("2. INDEXES ON PARENT TABLES")
    print("-" * 100)

    m1_tables = [t for t in parent_tables if t[1].startswith('m1_')]
    bqx_tables = [t for t in parent_tables if t[1].startswith('bqx_')]

    print(f"\n2a. M1 TABLES (Source Data) - {len(m1_tables)} tables")
    print("-" * 100)

    for schema, table, size in m1_tables[:3]:  # Show first 3 as sample
        indexes = get_table_indexes(table)
        print(f"\nTable: {table} ({size})")
        if indexes:
            for idx_name, idx_def, idx_size, is_unique, is_primary in indexes:
                prefix = "PK" if is_primary else ("UNQ" if is_unique else "IDX")
                print(f"  [{prefix}] {idx_name} ({idx_size})")
                print(f"       {idx_def}")
        else:
            print("  ⚠️  NO INDEXES FOUND")

    if len(m1_tables) > 3:
        print(f"\n... and {len(m1_tables) - 3} more M1 tables")

    print(f"\n2b. BQX TABLES (Computed Metrics) - {len(bqx_tables)} tables (Currently being backfilled)")
    print("-" * 100)

    for schema, table, size in bqx_tables[:3]:  # Show first 3 as sample
        indexes = get_table_indexes(table)
        print(f"\nTable: {table} ({size})")
        if indexes:
            for idx_name, idx_def, idx_size, is_unique, is_primary in indexes:
                prefix = "PK" if is_primary else ("UNQ" if is_unique else "IDX")
                print(f"  [{prefix}] {idx_name} ({idx_size})")
                print(f"       {idx_def}")
        else:
            print("  ⚠️  NO INDEXES FOUND")

    if len(bqx_tables) > 3:
        print(f"\n... and {len(bqx_tables) - 3} more BQX tables")

    # Check table statistics
    print("\n3. TABLE STATISTICS AND ANALYZE STATUS")
    print("-" * 100)
    stats = get_table_stats()

    # Filter to parent tables only
    parent_stats = [s for s in stats if '_2024m' not in s[1] and '_2025m' not in s[1]]

    print(f"{'Table':<30} {'Rows':>12} {'Dead':>8} {'Analyzed':<10}")
    print("-" * 100)
    for schema, table, live, dead, vac, autovac, analyze, autoanalyze in parent_stats[:15]:
        analyzed = "✓" if (analyze or autoanalyze) else "✗"
        print(f"{table:<30} {live:>12,} {dead:>8,} {analyzed:<10}")

    if len(parent_stats) > 15:
        print(f"\n... and {len(parent_stats) - 15} more tables")

    # Check for tables needing analyze
    print("\n4. OPTIMIZATION RECOMMENDATIONS")
    print("-" * 100)

    needs_analyze = [s for s in parent_stats if s[6] is None and s[7] is None and s[2] > 0]
    if needs_analyze:
        print("\n⚠️  Tables that have never been analyzed:")
        for stat in needs_analyze:
            print(f"  - {stat[1]} ({stat[2]:,} rows)")
    else:
        print("✓ All tables with data have been analyzed")

    # Check partition configuration
    print("\n5. PARTITION CONFIGURATION SAMPLE")
    print("-" * 100)
    partitions = check_partition_info()

    # Group by parent
    parent_partition_count = {}
    for parent, child, bound in partitions:
        if parent not in parent_partition_count:
            parent_partition_count[parent] = 0
        parent_partition_count[parent] += 1

    print(f"\nTotal partitions: {len(partitions)}")
    print("\nPartition counts by parent table:")
    for parent, count in sorted(parent_partition_count.items())[:10]:
        print(f"  {parent}: {count} partitions")

    if len(parent_partition_count) > 10:
        print(f"  ... and {len(parent_partition_count) - 10} more parent tables")

    print("\n" + "=" * 100)
    print("AUDIT COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()
