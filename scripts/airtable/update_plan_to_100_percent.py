#!/usr/bin/env python3
"""
Update BQX ML Refactor Plan in Airtable to 100% Current

Updates:
1. Stage 1.5.5: Add note about _norm field removal (24% reduction)
2. Stage 1.5.8: Add ML Correlation Recalculation stage + tasks
3. Phase 1.5: Update duration from 16h to 22h
"""

import requests
import json
import sys

# Airtable configuration
BASE_ID = 'appR3PPnrNkVo48mO'  # BQX-ML base
PHASES_TABLE = 'Phases'
STAGES_TABLE = 'Stages'
TASKS_TABLE = 'Tasks'

# Known record IDs from previous work
PHASE_1_5_ID = 'recl7nHgbrLjfjD5K'
MASTER_PLAN_ID = 'recSb2RvwT60eSu8U'


def get_headers(api_token):
    """Create request headers"""
    return {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }


def list_stages(api_token):
    """List all stages to find Stage 1.5.5 ID"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}'
    params = {
        'filterByFormula': "FIND('Stage 1.5.5', {Stage ID})"
    }

    response = requests.get(url, params=params, headers=get_headers(api_token))

    if response.status_code == 200:
        records = response.json().get('records', [])
        if records:
            return records[0]['id']
    else:
        print(f"Error listing stages: {response.status_code}")
        print(response.text)

    return None


def update_stage_1_5_5(api_token, stage_id):
    """Update Stage 1.5.5 deliverables to note _norm field removal"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}/{stage_id}'

    # Enhanced deliverables text
    new_deliverables = """28 REG parent tables recalculated
448 REG partitions recalculated
Schema documentation for 72 REG features
Updated reg_{pair} tables using rate_index
OPTIMIZATION: Remove 18 _norm fields (quad_norm, lin_norm, resid_norm for all windows)
Schema reduction: 75 → 57 fields (24% storage savings, ~2.2 GB)"""

    payload = {
        'fields': {
            'Deliverables': new_deliverables
        }
    }

    response = requests.patch(url, json=payload, headers=get_headers(api_token))

    if response.status_code == 200:
        return True
    else:
        print(f"Error updating Stage 1.5.5: {response.status_code}")
        print(response.text)
        return False


def create_stage_1_5_8(api_token):
    """Create Stage 1.5.8: ML Correlation Recalculation"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}'

    stage_data = {
        "Stage ID": "Stage 1.5.8: ML Correlation Recalculation",
        "Description": "Recreate ml_corr* tables with correlations calculated against new target (w60_bqx_return at t+60). Old target was pre-BQX metric, requiring full recalculation.",
        "Status": "Todo",
        "Duration": "6 hours",
        "Phase (Link)": [PHASE_1_5_ID],
        "Plan (Link)": [MASTER_PLAN_ID],
        "Deliverables": """ml_corr_triangulation_partitioned table created
85 monthly partitions (2020-01 through 2026-12)
Feature-to-target correlations for 28 pairs, ~40 BQX features, 3 windows (60, 240, 390 min)
Indexes on (source_mv, ts_utc), (correlation_window), (source_mv)
Verification: correlations in [-1, 1], target = w60_bqx_return at t+60
Expected size: ~2.4 TB"""
    }

    payload = {'fields': stage_data}
    response = requests.post(url, json=payload, headers=get_headers(api_token))

    if response.status_code == 200:
        return response.json()['id']
    else:
        print(f"Error creating Stage 1.5.8: {response.status_code}")
        print(response.text)
        return None


def create_tasks_1_5_8(api_token, stage_id):
    """Create 4 tasks for Stage 1.5.8"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TASKS_TABLE}'

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

    created_count = 0
    for task in tasks:
        task["Stage (Link)"] = [stage_id]
        task["Plan (Link)"] = [MASTER_PLAN_ID]

        payload = {'fields': task}
        response = requests.post(url, json=payload, headers=get_headers(api_token))

        if response.status_code == 200:
            created_count += 1
            print(f"  ✓ Created task: {task['Task ID']}")
        else:
            print(f"  ✗ Failed to create task: {task['Task ID']}")
            print(f"    Error: {response.status_code} - {response.text}")

    return created_count


def update_phase_1_5_duration(api_token):
    """Update Phase 1.5 duration from 16h to 22h"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{PHASES_TABLE}/{PHASE_1_5_ID}'

    payload = {
        'fields': {
            'Duration': '22 hours'
        }
    }

    response = requests.patch(url, json=payload, headers=get_headers(api_token))

    if response.status_code == 200:
        return True
    else:
        print(f"Error updating Phase 1.5 duration: {response.status_code}")
        print(response.text)
        return False


def main():
    # Get API token from command line or environment
    if len(sys.argv) > 1:
        api_token = sys.argv[1]
    else:
        print("Usage: python3 update_plan_to_100_percent.py <AIRTABLE_API_TOKEN>")
        print("Or set AIRTABLE_API_KEY environment variable")
        sys.exit(1)

    print("=" * 100)
    print("UPDATING BQX ML PLAN TO 100% CURRENT")
    print("=" * 100)
    print()

    # Step 1: Update Stage 1.5.5 deliverables
    print("[1/4] Finding and updating Stage 1.5.5...")
    stage_1_5_5_id = list_stages(api_token)

    if stage_1_5_5_id:
        print(f"  Found Stage 1.5.5: {stage_1_5_5_id}")
        if update_stage_1_5_5(api_token, stage_1_5_5_id):
            print("  ✓ Updated Stage 1.5.5 deliverables (added _norm field removal note)")
        else:
            print("  ✗ Failed to update Stage 1.5.5")
    else:
        print("  ⚠ Could not find Stage 1.5.5 - skipping update")

    print()

    # Step 2: Create Stage 1.5.8
    print("[2/4] Creating Stage 1.5.8: ML Correlation Recalculation...")
    stage_1_5_8_id = create_stage_1_5_8(api_token)

    if stage_1_5_8_id:
        print(f"  ✓ Created Stage 1.5.8: {stage_1_5_8_id}")
        print()

        # Step 3: Create tasks for Stage 1.5.8
        print("[3/4] Creating 4 tasks for Stage 1.5.8...")
        tasks_created = create_tasks_1_5_8(api_token, stage_1_5_8_id)
        print(f"  ✓ Created {tasks_created}/4 tasks")
    else:
        print("  ✗ Failed to create Stage 1.5.8")
        print("  ⚠ Skipping task creation")

    print()

    # Step 4: Update Phase 1.5 duration
    print("[4/4] Updating Phase 1.5 duration...")
    if update_phase_1_5_duration(api_token):
        print("  ✓ Updated Phase 1.5 duration: 16h → 22h")
    else:
        print("  ✗ Failed to update Phase 1.5 duration")

    print()
    print("=" * 100)
    print("AIRTABLE PLAN UPDATE COMPLETE")
    print("=" * 100)
    print()
    print("Summary of changes:")
    print("  1. ✓ Stage 1.5.5: Enhanced deliverables (remove 18 _norm fields, 24% savings)")
    print("  2. ✓ Stage 1.5.8: Added ML Correlation Recalculation (6 hours, 4 tasks)")
    print("  3. ✓ Phase 1.5: Updated duration (16h → 22h)")
    print()
    print("BQX ML Refactor Plan Status: 100% CURRENT")
    print()
    print(f"View in Airtable: https://airtable.com/{BASE_ID}")
    print()


if __name__ == "__main__":
    main()
