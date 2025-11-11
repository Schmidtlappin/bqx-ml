#!/usr/bin/env python3
"""
Update Airtable with Stage 1.5.4 and 1.5.5 progress

Updates:
1. Stage 1.5.4 status to "In Progress" with progress notes
2. Stage 1.5.5 status to "In Progress" with sub-stage breakdown
3. Adds documentation link to progress report
"""

import requests
import json
import os
import sys

# Airtable configuration
BASE_ID = 'appR3PPnrNkVo48mO'  # BQX-ML base
PHASES_TABLE = 'Phases'
STAGES_TABLE = 'Stages'
TASKS_TABLE = 'Tasks'

# Known record IDs
PHASE_1_5_ID = 'recl7nHgbrLjfjD5K'
MASTER_PLAN_ID = 'recSb2RvwT60eSu8U'

# Documentation links
PROGRESS_REPORT_URL = "https://github.com/Schmidtlappin/bqx-ml/blob/main/docs/stage_1_5_4_5_progress_report.md"


def get_headers(api_token):
    """Create request headers"""
    return {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }


def find_stage(api_token, stage_id_text):
    """Find stage by stage ID text"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}'
    params = {
        'filterByFormula': f"FIND('{stage_id_text}', {{Stage ID}})"
    }

    response = requests.get(url, params=params, headers=get_headers(api_token))

    if response.status_code == 200:
        records = response.json().get('records', [])
        if records:
            return records[0]['id']
    else:
        print(f"Error finding {stage_id_text}: {response.status_code}")
        print(response.text)

    return None


def update_stage_1_5_4(api_token, stage_id):
    """Update Stage 1.5.4 to In Progress with current metrics"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}/{stage_id}'

    notes = f"""STATUS: IN PROGRESS (38.3% complete)

Progress as of 2025-11-10 23:00 UTC:
- Partitions: 129/336 (38.3%)
- Rows: 3,957,150
- Size: 1,416 MB
- ETA: 2h 45m (~01:00 AM completion)

Pairs Completed (9/28):
✓ AUDCAD, AUDCHF, AUDJPY, AUDNZD, AUDUSD
✓ CADCHF, CADJPY, CHFJPY
⏳ EURAUD (in progress)

Critical Improvements:
- Schema reduction: 75 → 57 fields (removed 18 _norm fields, 24% savings)
- All metrics now use rate_index (base-100, cross-pair comparable)
- Real-time monitoring dashboard created

Running in parallel with Stage 1.5.5 (REG backfill)
System resources: Healthy (54.5% CPU, 2.2% memory)

Documentation: {PROGRESS_REPORT_URL}"""

    payload = {
        'fields': {
            'Status': 'In Progress',
            'Notes': notes
        }
    }

    response = requests.patch(url, json=payload, headers=get_headers(api_token))

    if response.status_code == 200:
        print("✓ Stage 1.5.4 updated successfully")
        return True
    else:
        print(f"✗ Error updating Stage 1.5.4: {response.status_code}")
        print(response.text)
        return False


def update_stage_1_5_5(api_token, stage_id):
    """Update Stage 1.5.5 to In Progress with sub-stage breakdown"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}/{stage_id}'

    notes = f"""STATUS: IN PROGRESS (5.5% complete)

SUB-STAGES:
✅ Stage 1.5.5.1: Drop REG Tables (COMPLETE)
   - Removed 28 parent tables + 476 partitions (~8.9 GB)
   - Duration: <1 minute

✅ Stage 1.5.5.2: Create New REG Schema (COMPLETE)
   - Created 57-field schema (removed 18 _norm fields)
   - 448 monthly partitions defined
   - Duration: <1 minute

⏳ Stage 1.5.5.3: REG Backfill (IN PROGRESS - 5.5%)
   - Partitions: 25/448 (5.5%)
   - Rows: 1,242,948
   - Size: 397 MB
   - ETA: 8h 50m (~08:00 AM completion)

Progress as of 2025-11-10 23:00 UTC:
- Pairs completed: AUDCAD (16 partitions)
- Pairs in progress: AUDCHF (9/16 partitions)

Critical Bug Fixes Applied:
1. Decimal→float conversion (PostgreSQL Decimal incompatible with numpy polyfit)
2. Numpy scalar→Python float (psycopg2 serialization issue)

Regression Analysis:
- Quadratic model: rate_index(t) = a*t² + b*t + c
- Windows: [60, 90, 150, 240, 390, 630 minutes]
- Metrics: reg_a, reg_b, reg_c, reg_r2, reg_endpoint

Running in parallel with Stage 1.5.4 (BQX backfill)
System resources: Healthy (61.7% CPU, 4.5% memory)

Documentation: {PROGRESS_REPORT_URL}"""

    payload = {
        'fields': {
            'Status': 'In Progress',
            'Notes': notes
        }
    }

    response = requests.patch(url, json=payload, headers=get_headers(api_token))

    if response.status_code == 200:
        print("✓ Stage 1.5.5 updated successfully")
        return True
    else:
        print(f"✗ Error updating Stage 1.5.5: {response.status_code}")
        print(response.text)
        return False


def main():
    """Main execution"""
    api_token = os.environ.get('AIRTABLE_API_KEY')

    if not api_token:
        print("Error: AIRTABLE_API_KEY environment variable not set")
        sys.exit(1)

    print("Updating Airtable with Stage 1.5.4 & 1.5.5 progress...")
    print()

    # Find Stage 1.5.4
    print("Finding Stage 1.5.4...")
    stage_1_5_4_id = find_stage(api_token, 'Stage 1.5.4')

    if not stage_1_5_4_id:
        print("Error: Could not find Stage 1.5.4")
        sys.exit(1)

    print(f"  Found: {stage_1_5_4_id}")

    # Find Stage 1.5.5
    print("Finding Stage 1.5.5...")
    stage_1_5_5_id = find_stage(api_token, 'Stage 1.5.5')

    if not stage_1_5_5_id:
        print("Error: Could not find Stage 1.5.5")
        sys.exit(1)

    print(f"  Found: {stage_1_5_5_id}")
    print()

    # Update Stage 1.5.4
    print("Updating Stage 1.5.4 status...")
    success_1_5_4 = update_stage_1_5_4(api_token, stage_1_5_4_id)

    # Update Stage 1.5.5
    print("Updating Stage 1.5.5 status...")
    success_1_5_5 = update_stage_1_5_5(api_token, stage_1_5_5_id)

    print()
    if success_1_5_4 and success_1_5_5:
        print("✓ All updates completed successfully")
        print()
        print("Summary:")
        print("- Stage 1.5.4: IN PROGRESS (38.3%, ETA 2h 45m)")
        print("- Stage 1.5.5: IN PROGRESS (5.5%, ETA 8h 50m)")
        print(f"- Documentation: {PROGRESS_REPORT_URL}")
        return 0
    else:
        print("✗ Some updates failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
