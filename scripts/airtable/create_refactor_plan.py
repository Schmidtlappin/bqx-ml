#!/usr/bin/env python3
"""
Create BQX ML Index-Based Refactor Plan in Airtable

This script creates a new Phase 1.5 for the Index-Based Architecture Refactor
with detailed stages and tasks for implementing:
1. Forex rate indexing (base-100 with 2024-07-01 baseline)
2. Unified multi-pair model architecture
3. Prediction of future BQX values at i+60
"""

import json
import os
import requests
from datetime import datetime

# Airtable configuration
AIRTABLE_TOKEN = os.environ.get('AIRTABLE_API_KEY')
BASE_ID = "appR3PPnrNkVo48mO"
MASTER_PLAN_ID = "recSb2RvwT60eSu8U"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

API_URL = f"https://api.airtable.com/v0/{BASE_ID}"


def create_phase(phase_data):
    """Create a new phase in Airtable"""
    url = f"{API_URL}/Phases"
    response = requests.post(url, headers=HEADERS, json={"fields": phase_data})
    if response.status_code == 200:
        return response.json()['id']
    else:
        print(f"Error creating phase: {response.text}")
        return None


def create_stage(stage_data):
    """Create a new stage in Airtable"""
    url = f"{API_URL}/Stages"
    response = requests.post(url, headers=HEADERS, json={"fields": stage_data})
    if response.status_code == 200:
        return response.json()['id']
    else:
        print(f"Error creating stage: {response.text}")
        return None


def create_task(task_data):
    """Create a new task in Airtable"""
    url = f"{API_URL}/Tasks"
    response = requests.post(url, headers=HEADERS, json={"fields": task_data})
    if response.status_code == 200:
        return response.json()['id']
    else:
        print(f"Error creating task: {response.text}")
        return None


def main():
    print("=" * 100)
    print("BQX ML INDEX-BASED REFACTOR PLAN - AIRTABLE CREATION")
    print("=" * 100)
    print()

    # Phase 1.5: Index-Based Architecture Refactor
    print("Creating Phase 1.5: Index-Based Architecture Refactor...")
    phase_data = {
        "Phase ID": "Phase 1.5: Index-Based Architecture Refactor",
        "Description": "Refactor BQX ML pipeline to use forex rate indexes (base-100) and unified multi-pair model architecture. Predicts future BQX values at i+60.",
        "Status": "Not Started",
        "Duration": "16 hours",  # Text field, not numeric
        "Plan (Link)": [MASTER_PLAN_ID]
    }

    phase_id = create_phase(phase_data)
    if not phase_id:
        print("Failed to create phase. Exiting.")
        return

    print(f"✓ Created Phase: {phase_id}")
    print()

    # Stages and Tasks
    stages_tasks = [
        {
            "stage": {
                "Stage ID": "Stage 1.5.1: Baseline Rate Setup",
                "Description": "Create baseline_rates table with 2024-07-01 rates for all 28 pairs",
                "Status": "Todo",
                "Duration": "0.1 hours",
                "Phase (Link)": phase_id,
                "Plan (Link)": [MASTER_PLAN_ID]
            },
            "tasks": [
                {
                    "Task ID": "TSK-1.5.1.1",
                    "Task Name": "Create bqx.baseline_rates table",
                    "Description": "CREATE TABLE bqx.baseline_rates (pair VARCHAR(10) PRIMARY KEY, baseline_date TIMESTAMP, baseline_rate NUMERIC)",
                    "Status": "Pending",
                    "Priority": "High",
                    "Assignee Type": "Claude (AI)",
                    "Assignee Name": "Claude Code",
                    "Duration (hours)": 0.05,
                    "Progress %": 0
                },
                {
                    "Task ID": "TSK-1.5.1.2",
                    "Task Name": "Populate baseline rates from 2024-07-01",
                    "Description": "INSERT INTO bqx.baseline_rates SELECT pair, '2024-07-01', rate FROM m1_{pair} WHERE ts_utc = '2024-07-01 00:00:00+00' for all 28 pairs",
                    "Status": "Pending",
                    "Priority": "High",
                    "Assignee Type": "Claude (AI)",
                    "Assignee Name": "Claude Code",
                    "Duration (hours)": 0.05,
                    "Progress %": 0
                }
            ]
        },
        {
            "stage": {
                "Stage ID": "Stage 1.5.2: M1 Table Enhancement",
                "Description": "Add rate_index column to all 28 M1 tables and calculate index values",
                "Status": "Todo",
                "Duration": "3 hours",
                "Phase (Link)": phase_id,
                "Plan (Link)": [MASTER_PLAN_ID]
            },
            "tasks": [
                {
                    "Task ID": "TSK-1.5.2.1",
                    "Task Name": "Add rate_index column to M1 tables",
                    "Description": "ALTER TABLE bqx.m1_{pair} ADD COLUMN rate_index NUMERIC for all 28 pairs",
                    "Status": "Pending",
                    "Priority": "High",
                    "Assignee Type": "Claude (AI)",
                    "Assignee Name": "Claude Code",
                    "Duration (hours)": 0.5,
                    "Progress %": 0
                },
                {
                    "Task ID": "TSK-1.5.2.2",
                    "Task Name": "Calculate rate_index for all M1 rows",
                    "Description": "UPDATE m1_{pair} SET rate_index = (close / baseline_rate) * 100 for all 28 pairs (~3GB of data)",
                    "Status": "Pending",
                    "Priority": "High",
                    "Assignee Type": "AWS Service",
                    "Assignee Name": "Aurora PostgreSQL",
                    "Duration (hours)": 2.0,
                    "Progress %": 0
                },
                {
                    "Task ID": "TSK-1.5.2.3",
                    "Task Name": "Create indexes on rate_index column",
                    "Description": "CREATE INDEX idx_m1_{pair}_rate_index ON m1_{pair}(rate_index) for all 28 pairs",
                    "Status": "Pending",
                    "Priority": "Medium",
                    "Assignee Type": "Claude (AI)",
                    "Assignee Name": "Claude Code",
                    "Duration (hours)": 0.5,
                    "Progress %": 0
                }
            ]
        },
        {
            "stage": {
                "Stage ID": "Stage 1.5.3: BQX Calculation Refactor",
                "Description": "Modify backward_worker.py to use index values instead of absolute rates",
                "Status": "Todo",
                "Duration": "1 hour",
                "Phase (Link)": phase_id,
                "Plan (Link)": [MASTER_PLAN_ID]
            },
            "tasks": [
                {
                    "Task ID": "TSK-1.5.3.1",
                    "Task Name": "Modify backward_worker.py for indexes",
                    "Description": "Update compute_backward_metrics() to use rate_index instead of rate. Formulas: max/min/avg directly (no normalization), stdev directly (no normalization)",
                    "Status": "Pending",
                    "Priority": "Critical",
                    "Assignee Type": "Claude (AI)",
                    "Assignee Name": "Claude Code",
                    "Duration (hours)": 0.5,
                    "Progress %": 0,
                    "Dependencies": "TSK-1.5.2.2"
                },
                {
                    "Task ID": "TSK-1.5.3.2",
                    "Task Name": "Update BQX table schema for indexes",
                    "Description": "Add rate_index field to BQX tables. Remove _pct fields (no longer needed). Update field definitions.",
                    "Status": "Pending",
                    "Priority": "High",
                    "Assignee Type": "Claude (AI)",
                    "Assignee Name": "Claude Code",
                    "Duration (hours)": 0.5,
                    "Progress %": 0
                }
            ]
        },
        {
            "stage": {
                "Stage ID": "Stage 1.5.4: BQX Table Recalculation",
                "Description": "Drop existing BQX tables and recalculate using index-based formulas",
                "Status": "Todo",
                "Duration": "8 hours",
                "Phase (Link)": phase_id,
                "Plan (Link)": [MASTER_PLAN_ID]
            },
            "tasks": [
                {
                    "Task ID": "TSK-1.5.4.1",
                    "Task Name": "Drop existing BQX tables",
                    "Description": "DROP TABLE IF EXISTS bqx.bqx_{pair} CASCADE for all 28 pairs (including 336 partitions)",
                    "Status": "Pending",
                    "Priority": "High",
                    "Assignee Type": "Claude (AI)",
                    "Assignee Name": "Claude Code",
                    "Duration (hours)": 0.5,
                    "Progress %": 0,
                    "Dependencies": "TSK-1.5.3.2"
                },
                {
                    "Task ID": "TSK-1.5.4.2",
                    "Task Name": "Create new BQX tables with index schema",
                    "Description": "CREATE TABLE with rate_index field, no _pct fields. Include monthly partitioning for 2024-07 through 2025-06.",
                    "Status": "Pending",
                    "Priority": "High",
                    "Assignee Type": "Claude (AI)",
                    "Assignee Name": "Claude Code",
                    "Duration (hours)": 0.5,
                    "Progress %": 0,
                    "Dependencies": "TSK-1.5.4.1"
                },
                {
                    "Task ID": "TSK-1.5.4.3",
                    "Task Name": "Run index-based backfill",
                    "Description": "python3 backward_worker_threaded.py - Recalculate all 28 pairs using rate_index values. Expected: 6-8 hours.",
                    "Status": "Pending",
                    "Priority": "Critical",
                    "Assignee Type": "Concurrent Worker",
                    "Assignee Name": "backward_worker_threaded.py",
                    "Duration (hours)": 7.0,
                    "Progress %": 0,
                    "Dependencies": "TSK-1.5.4.2, TSK-1.5.3.1"
                }
            ]
        },
        {
            "stage": {
                "Stage ID": "Stage 1.5.5: REG Table Recalculation",
                "Description": "Discover REG table schema and recalculate using index values",
                "Status": "Todo",
                "Duration": "2 hours",
                "Phase (Link)": phase_id,
                "Plan (Link)": [MASTER_PLAN_ID]
            },
            "tasks": [
                {
                    "Task ID": "TSK-1.5.5.1",
                    "Task Name": "Document REG table schema",
                    "Description": "\\d+ bqx.reg_{pair} for sample pairs. Document all 72 features and calculation logic.",
                    "Status": "Pending",
                    "Priority": "High",
                    "Assignee Type": "Claude (AI)",
                    "Assignee Name": "Claude Code",
                    "Duration (hours)": 0.5,
                    "Progress %": 0
                },
                {
                    "Task ID": "TSK-1.5.5.2",
                    "Task Name": "Identify REG features needing index conversion",
                    "Description": "Analyze which of 72 features use absolute rates vs percentage calculations. Plan conversion strategy.",
                    "Status": "Pending",
                    "Priority": "High",
                    "Assignee Type": "Claude (AI)",
                    "Assignee Name": "Claude Code",
                    "Duration (hours)": 0.5,
                    "Progress %": 0,
                    "Dependencies": "TSK-1.5.5.1"
                },
                {
                    "Task ID": "TSK-1.5.5.3",
                    "Task Name": "Recalculate REG tables with indexes",
                    "Description": "Drop and recreate reg_{pair} tables using rate_index. Update calculation scripts.",
                    "Status": "Pending",
                    "Priority": "Medium",
                    "Assignee Type": "Claude (AI)",
                    "Assignee Name": "Claude Code",
                    "Duration (hours)": 1.0,
                    "Progress %": 0,
                    "Dependencies": "TSK-1.5.5.2, TSK-1.5.4.3"
                }
            ]
        },
        {
            "stage": {
                "Stage ID": "Stage 1.5.6: Unified MV Creation",
                "Description": "Create single unified materialized view combining all 28 pairs",
                "Status": "Todo",
                "Duration": "1 hour",
                "Phase (Link)": phase_id,
                "Plan (Link)": [MASTER_PLAN_ID]
            },
            "tasks": [
                {
                    "Task ID": "TSK-1.5.6.1",
                    "Task Name": "Design unified MV schema",
                    "Description": "Schema: (ts_utc, target_pair, target_rate_index, 28 pairs × 37 BQX features = 1,036 columns). No _pct fields needed.",
                    "Status": "Pending",
                    "Priority": "High",
                    "Assignee Type": "Claude (AI)",
                    "Assignee Name": "Claude Code",
                    "Duration (hours)": 0.25,
                    "Progress %": 0
                },
                {
                    "Task ID": "TSK-1.5.6.2",
                    "Task Name": "Create bqx_ml.features_unified MV",
                    "Description": "CREATE MATERIALIZED VIEW bqx_ml.features_unified with UNION ALL of 28 pairs. ~10.36M rows total.",
                    "Status": "Pending",
                    "Priority": "High",
                    "Assignee Type": "Claude (AI)",
                    "Assignee Name": "Claude Code",
                    "Duration (hours)": 0.5,
                    "Progress %": 0,
                    "Dependencies": "TSK-1.5.6.1, TSK-1.5.4.3"
                },
                {
                    "Task ID": "TSK-1.5.6.3",
                    "Task Name": "Create indexes on unified MV",
                    "Description": "CREATE INDEX on (target_pair, ts_utc) for efficient querying by pair and time.",
                    "Status": "Pending",
                    "Priority": "Medium",
                    "Assignee Type": "Claude (AI)",
                    "Assignee Name": "Claude Code",
                    "Duration (hours)": 0.25,
                    "Progress %": 0,
                    "Dependencies": "TSK-1.5.6.2"
                }
            ]
        },
        {
            "stage": {
                "Stage ID": "Stage 1.5.7: Unified Model Implementation",
                "Description": "Implement unified multi-pair model architecture with pair embeddings",
                "Status": "Todo",
                "Duration": "1 hour",
                "Phase (Link)": phase_id,
                "Plan (Link)": [MASTER_PLAN_ID]
            },
            "tasks": [
                {
                    "Task ID": "TSK-1.5.7.1",
                    "Task Name": "Design unified model architecture",
                    "Description": "Neural network with pair embeddings. Input: pair_id (embedded) + 1,036 features. Output: future BQX value at t+60. Document architecture.",
                    "Status": "Pending",
                    "Priority": "High",
                    "Assignee Type": "Claude (AI)",
                    "Assignee Name": "Claude Code",
                    "Duration (hours)": 0.5,
                    "Progress %": 0
                },
                {
                    "Task ID": "TSK-1.5.7.2",
                    "Task Name": "Implement unified model training script",
                    "Description": "Create scripts/ml/train_unified_model.py. Train single model on all 28 pairs. Target: w60_bqx_return at t+60.",
                    "Status": "Pending",
                    "Priority": "High",
                    "Assignee Type": "Claude (AI)",
                    "Assignee Name": "Claude Code",
                    "Duration (hours)": 0.5,
                    "Progress %": 0,
                    "Dependencies": "TSK-1.5.7.1, TSK-1.5.6.2"
                }
            ]
        }
    ]

    # Create stages and tasks
    print("Creating stages and tasks...")
    print()

    for item in stages_tasks:
        stage_data = item["stage"]
        print(f"Creating Stage: {stage_data['Stage ID']}...")
        stage_id = create_stage(stage_data)

        if not stage_id:
            print(f"  ✗ Failed to create stage")
            continue

        print(f"  ✓ Created Stage: {stage_id}")

        # Create tasks for this stage
        for task in item["tasks"]:
            task["Stage (Link)"] = [stage_id]
            task["Plan (Link)"] = [MASTER_PLAN_ID]

            print(f"    Creating Task: {task['Task ID']}...")
            task_id = create_task(task)

            if task_id:
                print(f"      ✓ Created Task: {task_id}")
            else:
                print(f"      ✗ Failed to create task")

        print()

    print("=" * 100)
    print("REFACTOR PLAN CREATION COMPLETE")
    print("=" * 100)
    print()
    print(f"Phase created: Phase 1.5: Index-Based Architecture Refactor")
    print(f"Stages created: 7")
    print(f"Tasks created: ~18")
    print()
    print("Next steps:")
    print("  1. Review plan in Airtable BQX-ML base")
    print("  2. User approves the refactor approach")
    print("  3. Begin execution starting with Stage 1.5.1")
    print()
    print("View in Airtable: https://airtable.com/appR3PPnrNkVo48mO")


if __name__ == "__main__":
    main()
