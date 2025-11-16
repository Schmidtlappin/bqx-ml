#!/usr/bin/env python3
"""
Test script to verify SQLAlchemy fix eliminates Pandas UserWarning.

This script tests the fixed approach without interfering with running processes.
"""

import pandas as pd
import warnings
import os
from sqlalchemy import create_engine
from urllib.parse import quote_plus

# Capture warnings
warnings.filterwarnings('error', category=UserWarning)

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

# Test query (small result set)
test_query = """
SELECT ts_utc, w15_bqx_return
FROM bqx.bqx_eurusd
WHERE ts_utc >= '2024-07-01'::timestamp
AND ts_utc < '2024-07-01 01:00:00'::timestamp
AND w15_bqx_return IS NOT NULL
ORDER BY ts_utc
LIMIT 10
"""

print("Testing SQLAlchemy fix for Pandas UserWarning...")
print("=" * 60)

try:
    # This should NOT raise UserWarning
    df = pd.read_sql(test_query, ENGINE)

    print(f"✅ SUCCESS: Query executed without UserWarning")
    print(f"   Rows returned: {len(df)}")
    print(f"   Columns: {list(df.columns)}")
    print(f"   SQLAlchemy engine: {ENGINE}")
    print()
    print("Fix verified: pd.read_sql() with SQLAlchemy engine works correctly")
    print("=" * 60)

except UserWarning as e:
    print(f"❌ FAILED: UserWarning still raised")
    print(f"   Error: {e}")
    print("=" * 60)
    exit(1)

except Exception as e:
    print(f"❌ ERROR: {e}")
    print("=" * 60)
    exit(1)

print()
print("Test complete. The fix is ready for deployment.")
print("NOTE: This fix will be used automatically when Stage 2.12 reruns")
print("      or when other scripts use the updated pattern.")
