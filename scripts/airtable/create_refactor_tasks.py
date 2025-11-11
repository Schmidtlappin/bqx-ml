#!/usr/bin/env python3
"""
Create tasks for BQX ML Index-Based Refactor Plan in Airtable
"""

import json
import os
import requests

# Airtable configuration
AIRTABLE_TOKEN = os.environ.get('AIRTABLE_API_KEY')
BASE_ID = "appR3PPnrNkVo48mO"
MASTER_PLAN_ID = "recSb2RvwT60eSu8U"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

API_URL = f"https://api.airtable.com/v0/{BASE_ID}"

# Stage record IDs (from previous creation)
STAGES = {
    "1.5.1": "recaVaKoNoD1WRjNw",
    "1.5.2": "recs3h7OpwmiX9UH5",
    "1.5.3": "recYqIuM6KhosfFG4",
    "1.5.4": "recXj9JyzCwi6XDhJ",
    "1.5.5": "recaRmYMIhlnmQYHV",
    "1.5.6": "recP9sZC0SXWKnoM2",
    "1.5.7": "rec4PvTPjlsl2B4Yn"
}

def create_task(task_data):
    """Create a new task in Airtable"""
    url = f"{API_URL}/Tasks"
    response = requests.post(url, headers=HEADERS, json={"fields": task_data})
    if response.status_code == 200:
        return response.json()['id']
    else:
        print(f"Error creating task: {response.text}")
        return None

# Define all tasks with proper field names
TASKS = [
    # Stage 1.5.1: Baseline Rate Setup
    {
        "Task ID": "TSK-1.5.1.1",
        "Task Name": "Create bqx.baseline_rates table",
        "Description": "CREATE TABLE bqx.baseline_rates (pair VARCHAR(10) PRIMARY KEY, baseline_date TIMESTAMP, baseline_rate NUMERIC)",
        "Status": "Todo",
        "Priority": "High",
        "Assigned To": "Claude Code",
        "Estimated Hours": 0.05,
        "Estimated Cost": 0,
        "Stage (Link)": "recaVaKoNoD1WRjNw",
        "Plan (Link)": [MASTER_PLAN_ID]
    },
    {
        "Task ID": "TSK-1.5.1.2",
        "Task Name": "Populate baseline rates from 2024-07-01",
        "Description": "INSERT INTO bqx.baseline_rates SELECT pair, '2024-07-01', rate FROM m1_{pair} WHERE ts_utc = '2024-07-01 00:00:00+00' for all 28 pairs",
        "Status": "Todo",
        "Priority": "High",
        "Assigned To": "Claude Code",
        "Estimated Hours": 0.05,
        "Estimated Cost": 0,
        "Stage (Link)": "recaVaKoNoD1WRjNw",
        "Plan (Link)": [MASTER_PLAN_ID]
    },

    # Stage 1.5.2: M1 Table Enhancement
    {
        "Task ID": "TSK-1.5.2.1",
        "Task Name": "Add rate_index column to M1 tables",
        "Description": "ALTER TABLE bqx.m1_{pair} ADD COLUMN rate_index NUMERIC for all 28 pairs",
        "Status": "Todo",
        "Priority": "High",
        "Assigned To": "Claude Code",
        "Estimated Hours": 0.5,
        "Estimated Cost": 0,
        "Stage (Link)": "recs3h7OpwmiX9UH5",
        "Plan (Link)": [MASTER_PLAN_ID]
    },
    {
        "Task ID": "TSK-1.5.2.2",
        "Task Name": "Calculate rate_index for all M1 rows",
        "Description": "UPDATE m1_{pair} SET rate_index = (close / baseline_rate) * 100 for all 28 pairs (~3GB of data)",
        "Status": "Todo",
        "Priority": "High",
        "Assigned To": "Aurora PostgreSQL",
        "Estimated Hours": 2.0,
        "Estimated Cost": 0,
        "Stage (Link)": "recs3h7OpwmiX9UH5",
        "Plan (Link)": [MASTER_PLAN_ID]
    },
    {
        "Task ID": "TSK-1.5.2.3",
        "Task Name": "Create indexes on rate_index column",
        "Description": "CREATE INDEX idx_m1_{pair}_rate_index ON m1_{pair}(rate_index) for all 28 pairs",
        "Status": "Todo",
        "Priority": "Medium",
        "Assigned To": "Claude Code",
        "Estimated Hours": 0.5,
        "Estimated Cost": 0,
        "Stage (Link)": "recs3h7OpwmiX9UH5",
        "Plan (Link)": [MASTER_PLAN_ID]
    },

    # Stage 1.5.3: BQX Calculation Refactor
    {
        "Task ID": "TSK-1.5.3.1",
        "Task Name": "Modify backward_worker.py for indexes",
        "Description": "Update compute_backward_metrics() to use rate_index instead of rate. Formulas: max/min/avg directly (no normalization), stdev directly (no normalization). Dependencies: TSK-1.5.2.2",
        "Status": "Todo",
        "Priority": "Critical",
        "Assigned To": "Claude Code",
        "Estimated Hours": 0.5,
        "Estimated Cost": 0,
        "Stage (Link)": "recYqIuM6KhosfFG4",
        "Plan (Link)": [MASTER_PLAN_ID]
    },
    {
        "Task ID": "TSK-1.5.3.2",
        "Task Name": "Update BQX table schema for indexes",
        "Description": "Add rate_index field to BQX tables. Remove _pct fields (no longer needed). Update field definitions.",
        "Status": "Todo",
        "Priority": "High",
        "Assigned To": "Claude Code",
        "Estimated Hours": 0.5,
        "Estimated Cost": 0,
        "Stage (Link)": "recYqIuM6KhosfFG4",
        "Plan (Link)": [MASTER_PLAN_ID]
    },

    # Stage 1.5.4: BQX Table Recalculation
    {
        "Task ID": "TSK-1.5.4.1",
        "Task Name": "Drop existing BQX tables",
        "Description": "DROP TABLE IF EXISTS bqx.bqx_{pair} CASCADE for all 28 pairs (including 336 partitions). Dependencies: TSK-1.5.3.2",
        "Status": "Todo",
        "Priority": "High",
        "Assigned To": "Claude Code",
        "Estimated Hours": 0.5,
        "Estimated Cost": 0,
        "Stage (Link)": "recXj9JyzCwi6XDhJ",
        "Plan (Link)": [MASTER_PLAN_ID]
    },
    {
        "Task ID": "TSK-1.5.4.2",
        "Task Name": "Create new BQX tables with index schema",
        "Description": "CREATE TABLE with rate_index field, no _pct fields. Include monthly partitioning for 2024-07 through 2025-06. Dependencies: TSK-1.5.4.1",
        "Status": "Todo",
        "Priority": "High",
        "Assigned To": "Claude Code",
        "Estimated Hours": 0.5,
        "Estimated Cost": 0,
        "Stage (Link)": "recXj9JyzCwi6XDhJ",
        "Plan (Link)": [MASTER_PLAN_ID]
    },
    {
        "Task ID": "TSK-1.5.4.3",
        "Task Name": "Run index-based backfill",
        "Description": "python3 backward_worker_threaded.py - Recalculate all 28 pairs using rate_index values. Expected: 6-8 hours. Dependencies: TSK-1.5.4.2, TSK-1.5.3.1",
        "Status": "Todo",
        "Priority": "Critical",
        "Assigned To": "backward_worker_threaded.py",
        "Estimated Hours": 7.0,
        "Estimated Cost": 0,
        "Stage (Link)": "recXj9JyzCwi6XDhJ",
        "Plan (Link)": [MASTER_PLAN_ID]
    },

    # Stage 1.5.5: REG Table Recalculation
    {
        "Task ID": "TSK-1.5.5.1",
        "Task Name": "Document REG table schema",
        "Description": "\\d+ bqx.reg_{pair} for sample pairs. Document all 72 features and calculation logic.",
        "Status": "Todo",
        "Priority": "High",
        "Assigned To": "Claude Code",
        "Estimated Hours": 0.5,
        "Estimated Cost": 0,
        "Stage (Link)": "recaRmYMIhlnmQYHV",
        "Plan (Link)": [MASTER_PLAN_ID]
    },
    {
        "Task ID": "TSK-1.5.5.2",
        "Task Name": "Identify REG features needing index conversion",
        "Description": "Analyze which of 72 features use absolute rates vs percentage calculations. Plan conversion strategy. Dependencies: TSK-1.5.5.1",
        "Status": "Todo",
        "Priority": "High",
        "Assigned To": "Claude Code",
        "Estimated Hours": 0.5,
        "Estimated Cost": 0,
        "Stage (Link)": "recaRmYMIhlnmQYHV",
        "Plan (Link)": [MASTER_PLAN_ID]
    },
    {
        "Task ID": "TSK-1.5.5.3",
        "Task Name": "Recalculate REG tables with indexes",
        "Description": "Drop and recreate reg_{pair} tables using rate_index. Update calculation scripts. Dependencies: TSK-1.5.5.2, TSK-1.5.4.3",
        "Status": "Todo",
        "Priority": "Medium",
        "Assigned To": "Claude Code",
        "Estimated Hours": 1.0,
        "Estimated Cost": 0,
        "Stage (Link)": "recaRmYMIhlnmQYHV",
        "Plan (Link)": [MASTER_PLAN_ID]
    },

    # Stage 1.5.6: Unified MV Creation
    {
        "Task ID": "TSK-1.5.6.1",
        "Task Name": "Design unified MV schema",
        "Description": "Schema: (ts_utc, target_pair, target_rate_index, 28 pairs × 37 BQX features = 1,036 columns). No _pct fields needed.",
        "Status": "Todo",
        "Priority": "High",
        "Assigned To": "Claude Code",
        "Estimated Hours": 0.25,
        "Estimated Cost": 0,
        "Stage (Link)": "recP9sZC0SXWKnoM2",
        "Plan (Link)": [MASTER_PLAN_ID]
    },
    {
        "Task ID": "TSK-1.5.6.2",
        "Task Name": "Create bqx_ml.features_unified MV",
        "Description": "CREATE MATERIALIZED VIEW bqx_ml.features_unified with UNION ALL of 28 pairs. ~10.36M rows total. Dependencies: TSK-1.5.6.1, TSK-1.5.4.3",
        "Status": "Todo",
        "Priority": "High",
        "Assigned To": "Claude Code",
        "Estimated Hours": 0.5,
        "Estimated Cost": 0,
        "Stage (Link)": "recP9sZC0SXWKnoM2",
        "Plan (Link)": [MASTER_PLAN_ID]
    },
    {
        "Task ID": "TSK-1.5.6.3",
        "Task Name": "Create indexes on unified MV",
        "Description": "CREATE INDEX on (target_pair, ts_utc) for efficient querying by pair and time. Dependencies: TSK-1.5.6.2",
        "Status": "Todo",
        "Priority": "Medium",
        "Assigned To": "Claude Code",
        "Estimated Hours": 0.25,
        "Estimated Cost": 0,
        "Stage (Link)": "recP9sZC0SXWKnoM2",
        "Plan (Link)": [MASTER_PLAN_ID]
    },

    # Stage 1.5.7: Unified Model Implementation
    {
        "Task ID": "TSK-1.5.7.1",
        "Task Name": "Design unified model architecture",
        "Description": "Neural network with pair embeddings. Input: pair_id (embedded) + 1,036 features. Output: future BQX value at t+60. Document architecture.",
        "Status": "Todo",
        "Priority": "High",
        "Assigned To": "Claude Code",
        "Estimated Hours": 0.5,
        "Estimated Cost": 0,
        "Stage (Link)": "rec4PvTPjlsl2B4Yn",
        "Plan (Link)": [MASTER_PLAN_ID]
    },
    {
        "Task ID": "TSK-1.5.7.2",
        "Task Name": "Implement unified model training script",
        "Description": "Create scripts/ml/train_unified_model.py. Train single model on all 28 pairs. Target: w60_bqx_return at t+60. Dependencies: TSK-1.5.7.1, TSK-1.5.6.2",
        "Status": "Todo",
        "Priority": "High",
        "Assigned To": "Claude Code",
        "Estimated Hours": 0.5,
        "Estimated Cost": 0,
        "Stage (Link)": "rec4PvTPjlsl2B4Yn",
        "Plan (Link)": [MASTER_PLAN_ID]
    }
]

def main():
    print("=" * 100)
    print("CREATE REFACTOR TASKS IN AIRTABLE")
    print("=" * 100)
    print()

    created_count = 0
    failed_count = 0

    for task in TASKS:
        print(f"Creating Task: {task['Task ID']}...")
        task_id = create_task(task)

        if task_id:
            print(f"  ✓ Created: {task_id}")
            created_count += 1
        else:
            print(f"  ✗ Failed")
            failed_count += 1

    print()
    print("=" * 100)
    print(f"COMPLETE: {created_count} tasks created, {failed_count} failed")
    print("=" * 100)
    print()
    print("View in Airtable: https://airtable.com/appR3PPnrNkVo48mO")

if __name__ == "__main__":
    main()
