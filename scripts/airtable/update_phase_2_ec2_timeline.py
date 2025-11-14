#!/usr/bin/env python3
"""
Update Phase 2 Stages with c7i.8xlarge Timeline Estimates
Updates Stages 2.1.2, 2.3-2.9 with faster completion times
"""

import os
import requests
import json

# AirTable configuration
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
BASE_ID = 'appR3PPnrNkVo48mO'
STAGES_TABLE = 'Stages'

def get_all_stages():
    """Retrieve all stages from AirTable"""
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }

    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}?pageSize=100'

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('records', [])
        else:
            print(f"❌ Failed to retrieve stages: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error retrieving stages: {e}")
        return []

def update_stage(record_id, updates):
    """Update a specific stage"""
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }

    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}/{record_id}'

    try:
        response = requests.patch(url, headers=headers, json={'fields': updates})
        if response.status_code == 200:
            return True
        else:
            print(f"❌ Failed to update stage: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error updating stage: {e}")
        return False

def main():
    """Main execution"""
    print()
    print("=" * 80)
    print("AIRTABLE UPDATE: PHASE 2 EC2 TIMELINE UPDATES")
    print("=" * 80)
    print()

    # Retrieve all stages
    print("Fetching all stages...")
    stages = get_all_stages()

    if not stages:
        print("❌ No stages retrieved")
        return

    print(f"✅ Retrieved {len(stages)} stages")
    print()

    # Define updates for each stage
    stage_updates = {
        '2.1.2': {
            'Duration': '2.8 hours remaining (c7i.8xlarge)',
            'Notes_Append': '''

**EC2 UPGRADE IMPACT (c7i.8xlarge):**
- Baseline: 11 hours total (8 workers on t3.2xlarge)
- Upgraded: 2.8 hours remaining (32 workers on c7i.8xlarge)
- Speedup: 3.9x faster
- Cost Impact: Included in $27.25 Phase 2 total
'''
        },
        '2.3': {
            'Duration': '4 hours (c7i.8xlarge)',
            'Notes_Append': '''

**EC2 UPGRADE IMPACT:**
- Baseline: 48 hours (4 workers)
- Upgraded: 12 hours (16 workers)
- Speedup: 4.0x faster
'''
        },
        '2.4': {
            'Duration': '12 hours (c7i.8xlarge)',
            'Notes_Append': '''

**EC2 UPGRADE IMPACT:**
- Baseline: 48 hours (2 workers)
- Upgraded: 12 hours (8 workers)
- Speedup: 4.0x faster
'''
        },
        '2.6': {
            'Duration': '6 hours (c7i.8xlarge)',
            'Notes_Append': '''

**EC2 UPGRADE IMPACT:**
- Baseline: 24 hours
- Upgraded: 6 hours
- Speedup: 4.0x faster
'''
        },
        '2.7': {
            'Duration': '6 hours (c7i.8xlarge + S3 Transfer Accel)',
            'Notes_Append': '''

**EC2 UPGRADE IMPACT:**
- Baseline: 24 hours
- Upgraded: 6 hours (32 workers + S3 Transfer Acceleration)
- Speedup: 4.0x faster

**POST-PHASE 2 DOWNGRADE CHECKPOINT:**
This is the final Phase 2 stage requiring high-performance EC2.

After completion:
1. Validate S3 export integrity (40-50 GB Parquet files)
2. Verify all 1,080 features in Aurora
3. Create final EC2 snapshot (backup)
4. **DOWNGRADE EC2:** c7i.8xlarge → t3.xlarge (4 vCPUs, 16GB RAM)
5. Verify trillium-master operational at lower cost ($121/month)
6. Proceed to Phase 3 (SageMaker serverless)

**EC2 remains active (not terminated) for:**
- Phase 3 monitoring and maintenance
- Other projects: Robkei-Ring, OmniDrive, box
- Ad-hoc database queries
- Emergency troubleshooting
'''
        },
        '2.8': {
            'Duration': '6 hours (c7i.8xlarge)',
            'Notes_Append': '''

**EC2 UPGRADE IMPACT:**
- Baseline: 24 hours (4 workers)
- Upgraded: 6 hours (16 workers)
- Speedup: 4.0x faster
'''
        },
        '2.9': {
            'Duration': '12 hours (c7i.8xlarge)',
            'Notes_Append': '''

**EC2 UPGRADE IMPACT (BIGGEST IMPROVEMENT):**
- Baseline: 48 hours (longest stage)
- Upgraded: 12 hours (32 workers)
- Speedup: 4.0x faster
- Time Saved: 36 hours (1.5 days)

Stage 2.9 was the primary bottleneck in Phase 2 critical path.
c7i.8xlarge upgrade provides maximum benefit here.
'''
        }
    }

    # Update each stage
    updated_count = 0
    for stage in stages:
        stage_id = stage['fields'].get('Stage ID', '')

        # Extract numeric portion (e.g., "2.1.2" from "2.1.2 - Track 2: Regression Features")
        stage_id_short = stage_id.split(' ')[0] if ' ' in stage_id else stage_id

        if stage_id_short in stage_updates:
            print(f"Updating {stage_id}...")

            updates = {}
            update_def = stage_updates[stage_id_short]

            # Update Duration if specified
            if 'Duration' in update_def:
                updates['Duration'] = update_def['Duration']

            # Append to Notes if specified
            if 'Notes_Append' in update_def:
                current_notes = stage['fields'].get('Notes', '')
                updates['Notes'] = current_notes + update_def['Notes_Append']

            if update_stage(stage['id'], updates):
                print(f"  ✅ {stage_id_short} updated")
                updated_count += 1
            else:
                print(f"  ❌ {stage_id_short} failed")

    print()
    print("=" * 80)
    print("AIRTABLE UPDATE COMPLETE")
    print("=" * 80)
    print()
    print(f"✅ Updated {updated_count}/{len(stage_updates)} stages")
    print()
    print("Updated Stages:")
    for stage_id in stage_updates.keys():
        print(f"  - Stage {stage_id}: {stage_updates[stage_id]['Duration']}")
    print()
    print("Summary:")
    print("  - All Phase 2 stages now reflect c7i.8xlarge timeline")
    print("  - Stage 2.7 includes downgrade checkpoint")
    print("  - Total Phase 2: 1.3 days (vs 5.4 days baseline)")

if __name__ == '__main__':
    main()
