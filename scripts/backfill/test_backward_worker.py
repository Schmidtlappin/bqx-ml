#!/usr/bin/env python3
"""
Test Backward Worker - Single Pair, Single Month
Tests BQX calculation on eurusd for 2024-07 before full backfill
"""

import sys
import time

# Add sandbox/scripts to path to import backward_worker
sys.path.insert(0, '/home/ubuntu/Robkei-Ring/sandbox/scripts')

from backward_worker import process_backward_analysis, get_db_connection

def main():
    print("=" * 80)
    print("BQX Backward Worker - TEST RUN")
    print("=" * 80)
    print("Pair: EURUSD")
    print("Period: 2024-07-01 to 2024-08-01")
    print("=" * 80)

    start_time = time.time()

    try:
        rows = process_backward_analysis('eurusd', '2024-07-01', '2024-08-01')
        elapsed = time.time() - start_time

        print(f"\n✓ Test completed successfully")
        print(f"  Rows inserted: {rows:,}")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Rate: {rows/elapsed:.0f} rows/sec")

        # Verify data in database
        print(f"\nVerifying data in database...")
        conn = get_db_connection()
        cur = conn.cursor()

        # Check row count
        cur.execute("SELECT COUNT(*) FROM bqx.bqx_eurusd WHERE ts_utc >= '2024-07-01' AND ts_utc < '2024-08-01'")
        db_count = cur.fetchone()[0]
        print(f"  Database row count: {db_count:,}")

        # Sample first 5 rows
        cur.execute("""
            SELECT
                ts_utc,
                rate,
                w15_bqx_return,
                w30_bqx_return,
                w60_bqx_return,
                w75_bqx_return,
                agg_bqx_return
            FROM bqx.bqx_eurusd
            WHERE ts_utc >= '2024-07-01' AND ts_utc < '2024-08-01'
            ORDER BY ts_utc
            LIMIT 5
        """)

        print(f"\n  Sample rows (first 5):")
        print(f"  {'Timestamp':<20} {'Rate':>10} {'w15_bqx':>12} {'w30_bqx':>12} {'w60_bqx':>12} {'w75_bqx':>12}")
        print(f"  {'-'*20} {'-'*10} {'-'*12} {'-'*12} {'-'*12} {'-'*12}")

        for row in cur.fetchall():
            ts, rate, w15, w30, w60, w75, agg = row
            w15_str = f"{w15:.6f}" if w15 is not None else "NULL"
            w30_str = f"{w30:.6f}" if w30 is not None else "NULL"
            w60_str = f"{w60:.6f}" if w60 is not None else "NULL"
            w75_str = f"{w75:.6f}" if w75 is not None else "NULL"
            print(f"  {ts} {rate:10.5f} {w15_str:>12} {w30_str:>12} {w60_str:>12} {w75_str:>12}")

        # Check NULL distribution (edge effects)
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(w15_bqx_return) as w15_count,
                COUNT(w30_bqx_return) as w30_count,
                COUNT(w60_bqx_return) as w60_count,
                COUNT(w75_bqx_return) as w75_count
            FROM bqx.bqx_eurusd
            WHERE ts_utc >= '2024-07-01' AND ts_utc < '2024-08-01'
        """)

        total, w15_c, w30_c, w60_c, w75_c = cur.fetchone()
        print(f"\n  NULL distribution (edge effects):")
        print(f"    Total rows: {total:,}")
        print(f"    w15 non-NULL: {w15_c:,} ({w15_c/total*100:.1f}%)")
        print(f"    w30 non-NULL: {w30_c:,} ({w30_c/total*100:.1f}%)")
        print(f"    w60 non-NULL: {w60_c:,} ({w60_c/total*100:.1f}%)")
        print(f"    w75 non-NULL: {w75_c:,} ({w75_c/total*100:.1f}%)")

        cur.close()
        conn.close()

        print("\n" + "=" * 80)
        print("TEST PASSED ✓")
        print("=" * 80)

        return 0

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
