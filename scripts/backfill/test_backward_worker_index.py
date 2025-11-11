#!/usr/bin/env python3
"""
Test backward_worker_index.py on a single pair/month
"""
import sys
sys.path.insert(0, '/home/ubuntu/bqx-ml/scripts/backfill')
from backward_worker_index import process_backward_analysis

print("Testing backward_worker_index.py on AUDCAD 2024-07...")
print("="*60)

try:
    rows = process_backward_analysis('audcad', '2024-07-01', '2024-08-01')
    print(f"✓ Success: {rows:,} rows inserted")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
