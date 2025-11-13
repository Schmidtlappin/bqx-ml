#!/usr/bin/env python3
"""
Update AirTable Phase 2.1 Parallel Tracks Status
Updates all 3 parallel track stages with current execution status.
"""

import os
import json
import requests
from datetime import datetime

# AirTable Configuration
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
if not AIRTABLE_API_KEY:
    raise ValueError("AIRTABLE_API_KEY environment variable must be set")

BASE_ID = 'appR3PPnrNkVo48mO'
STAGES_TABLE = 'Stages'

headers = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}

def update_stage(stage_id, fields):
    """Update a stage record in AirTable"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}/{stage_id}'

    response = requests.patch(url, headers=headers, json={'fields': fields})

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to update stage: {response.status_code} - {response.text}")

def main():
    print("=" * 80)
    print("UPDATING AIRTABLE: PHASE 2.1 PARALLEL TRACKS STATUS")
    print("=" * 80)
    print()

    today = datetime.now().strftime('%Y-%m-%d')

    # Stage 2.1.1: Track 1 - Bollinger BQX (COMPLETE)
    stage_2_1_1 = {
        'Status': 'Done',
        'Completion Date': today,
        'Notes': '''✅ TRACK 1 COMPLETE

**Status:** 426/672 partitions populated (63.4%)
- Remaining 246 are expected "No BQX data" (future months)
- 21 features per partition (4 windows: 20, 30, 60, 120 + 2 slopes)
- Duration: ~4 hours

**Issues Fixed:**
1. Table mismatch: Changed from m1_ to bqx_ table
2. Column names: Updated to match bollinger_bqx schema
3. Feature expansion: 10 → 21 features (4 windows instead of 2)

**Output:** 426 monthly partitions populated across 28 currency pairs
**Tables:** bollinger_bqx_{pair}_{year_month}
'''
    }

    # Stage 2.1.2: Track 2 - Regression Features (IN PROGRESS)
    stage_2_1_2 = {
        'Status': 'In Progress',
        'Notes': '''🔄 TRACK 2 IN PROGRESS

**Status:** Running (started 2025-11-13)
- 336 partitions total (28 pairs × 12 months: Jul 2024 - Jun 2025)
- 180 features: 90 rate domain + 90 BQX domain
- 6 windows × 15 metrics per domain
- 4 parallel workers at 99% CPU

**Issues Fixed:**
1. Table/column mismatch: Separated M1 and BQX queries
2. Timezone mismatch: Added UTC conversion for M1 timestamps
3. NaT insertion error: Filter out NaT values before database insertion

**ETA:** 8-12 hours (most compute-intensive track)
**Tables:** reg_rate_{pair}_{year_month}, reg_bqx_{pair}_{year_month}
'''
    }

    # Stage 2.1.3: Track 3 - Feature Extraction (COMPLETE)
    stage_2_1_3 = {
        'Status': 'Done',
        'Completion Date': today,
        'Notes': '''✅ TRACK 3 COMPLETE

**Status:** 28/28 Parquet files extracted (100%)
- 81 features per pair (not 159 as originally assumed)
- Average: 370K rows × 82 columns per pair
- Total output: 2.2 GB
- Duration: ~25 minutes

**Issues Fixed:**
1. Column name mismatches across 5 feature tables
2. Schema verification: Actual DB schema different from assumptions
3. Feature count correction: 159 → 81 available features

**Feature Breakdown:**
- Bollinger: 20 features
- Statistics: 23 features
- Volume: 10 features
- Spread: 20 features
- Time: 8 features

**Output:** /home/ubuntu/bqx-ml/data/extracted/{pair}.parquet
'''
    }

    # Get stage record IDs (need to search by Stage ID field)
    print("Searching for Phase 2.1 stage records...")

    # Search for stages
    search_url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}'
    params = {
        'filterByFormula': "OR({Stage ID}='2.1.1', {Stage ID}='2.1.2', {Stage ID}='2.1.3')"
    }

    response = requests.get(search_url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"❌ Failed to search stages: {response.status_code}")
        return

    records = response.json().get('records', [])

    if len(records) != 3:
        print(f"⚠️  Expected 3 records, found {len(records)}")
        print("Records found:", [r['fields'].get('Stage ID') for r in records])

    # Update each stage
    updates = {
        '2.1.1': stage_2_1_1,
        '2.1.2': stage_2_1_2,
        '2.1.3': stage_2_1_3
    }

    for record in records:
        stage_id_field = record['fields'].get('Stage ID')
        record_id = record['id']

        if stage_id_field in updates:
            print(f"\nUpdating Stage {stage_id_field}...")
            try:
                result = update_stage(record_id, updates[stage_id_field])
                status = updates[stage_id_field]['Status']
                print(f"✅ Stage {stage_id_field} updated: {status}")
            except Exception as e:
                print(f"❌ Failed to update Stage {stage_id_field}: {e}")

    print()
    print("=" * 80)
    print("AIRTABLE UPDATE COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print("  Stage 2.1.1 (Track 1): ✅ DONE")
    print("  Stage 2.1.2 (Track 2): 🔄 IN PROGRESS")
    print("  Stage 2.1.3 (Track 3): ✅ DONE")
    print()
    print("Documentation added:")
    print("  - All issues fixed and remediated")
    print("  - Current status and progress")
    print("  - Output locations and metrics")
    print()

if __name__ == '__main__':
    main()
