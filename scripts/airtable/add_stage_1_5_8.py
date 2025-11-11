#!/usr/bin/env python3
"""
Add Stage 1.5.8: ML Correlation Recalculation to existing refactor plan
"""

import requests
import os

# Airtable configuration
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
BASE_ID = 'appR3PPnrNkVo48mO'
PHASES_TABLE = 'Phases'
STAGES_TABLE = 'Stages'
TASKS_TABLE = 'Tasks'

HEADERS = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}

# Find Phase 1.5 and Plan record IDs
PHASE_1_5_ID = 'recl7nHgbrLjfjD5K'  # From previous creation
MASTER_PLAN_ID = 'recSb2RvwT60eSu8U'  # MP-BQX_ML-001


def create_stage(stage_data):
    """Create a stage in Airtable"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}'

    payload = {
        'fields': stage_data
    }

    response = requests.post(url, json=payload, headers=HEADERS)

    if response.status_code == 200:
        return response.json()['id']
    else:
        print(f"Error creating stage: {response.status_code}")
        print(response.text)
        return None


def create_task(task_data):
    """Create a task in Airtable"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TASKS_TABLE}'

    payload = {
        'fields': task_data
    }

    response = requests.post(url, json=payload, headers=HEADERS)

    if response.status_code == 200:
        return response.json()['id']
    else:
        print(f"Error creating task: {response.status_code}")
        print(response.text)
        return None


def main():
    print("=" * 100)
    print("ADDING STAGE 1.5.8: ML CORRELATION RECALCULATION")
    print("=" * 100)
    print()

    # Stage 1.5.8: ML Correlation Recalculation
    stage_data = {
        "Stage ID": "Stage 1.5.8: ML Correlation Recalculation",
        "Description": "Recreate ml_corr* tables with correlations calculated against new target (w60_bqx_return at t+60)",
        "Status": "Todo",
        "Duration": "6 hours",
        "Phase (Link)": [PHASE_1_5_ID],
        "Plan (Link)": [MASTER_PLAN_ID]
    }

    print(f"Creating Stage: {stage_data['Stage ID']}...")
    stage_id = create_stage(stage_data)

    if not stage_id:
        print("  ✗ Failed to create stage")
        return

    print(f"  ✓ Created Stage: {stage_id}")
    print()

    # Tasks for Stage 1.5.8
    tasks = [
        {
            "Task ID": "TSK-1.5.8.1",
            "Task Name": "Recreate ml_corr_triangulation_partitioned table",
            "Description": "CREATE TABLE ml_corr_triangulation_partitioned with monthly partitioning. Create 85 child partitions (2020-01 through 2026-12).",
            "Status": "Pending",
            "Priority": "High",
            "Assignee Type": "Claude (AI)",
            "Assignee Name": "Claude Code",
            "Duration (hours)": 0.25,
            "Progress %": 0,
            "Dependencies": "TSK-1.5.4.3 (BQX recalculation complete), TSK-1.5.6.2 (Unified MV created)"
        },
        {
            "Task ID": "TSK-1.5.8.2",
            "Task Name": "Calculate feature-to-target correlations",
            "Description": "For each pair (28), each BQX feature (~40), each correlation window (60, 240, 390 min), calculate correlation against NEW target: w60_bqx_return at t+60. Expected output: ~2.4 TB.",
            "Status": "Pending",
            "Priority": "High",
            "Assignee Type": "Python Script",
            "Assignee Name": "calculate_ml_corr.py",
            "Duration (hours)": 5,
            "Progress %": 0,
            "Dependencies": "TSK-1.5.8.1"
        },
        {
            "Task ID": "TSK-1.5.8.3",
            "Task Name": "Create indexes on ml_corr tables",
            "Description": "CREATE INDEX on (source_mv, ts_utc), (correlation_window), (source_mv) for all 85 partitions.",
            "Status": "Pending",
            "Priority": "Medium",
            "Assignee Type": "Aurora PostgreSQL",
            "Assignee Name": "trillium-bqx-cluster",
            "Duration (hours)": 0.5,
            "Progress %": 0,
            "Dependencies": "TSK-1.5.8.2"
        },
        {
            "Task ID": "TSK-1.5.8.4",
            "Task Name": "Verify correlation calculations",
            "Description": "Verify correlations against known relationships. Check correlation value ranges (-1 to 1). Verify all pairs/features populated. Confirm target is w60_bqx_return at t+60.",
            "Status": "Pending",
            "Priority": "High",
            "Assignee Type": "Claude (AI)",
            "Assignee Name": "Claude Code",
            "Duration (hours)": 0.25,
            "Progress %": 0,
            "Dependencies": "TSK-1.5.8.3"
        }
    ]

    # Create all tasks
    for task in tasks:
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
    print("STAGE 1.5.8 ADDED SUCCESSFULLY")
    print("=" * 100)
    print()
    print(f"Stage created: Stage 1.5.8: ML Correlation Recalculation")
    print(f"Tasks created: 4")
    print(f"Total duration: 6 hours")
    print()
    print("Updated refactor timeline:")
    print("  - Original: 16 hours (Stages 1.5.1-1.5.7)")
    print("  - NEW: 22 hours (Stages 1.5.1-1.5.8)")
    print()
    print("View in Airtable: https://airtable.com/appR3PPnrNkVo48mO")


if __name__ == "__main__":
    main()
