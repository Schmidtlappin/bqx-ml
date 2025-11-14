#!/usr/bin/env python3
"""
Update Phase 3 Stages with Infrastructure Transition Notes
Clarifies EC2 downgrade (not termination) and serverless architecture
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
    print("AIRTABLE UPDATE: PHASE 3 INFRASTRUCTURE NOTES")
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

    # Define updates for Phase 3 stages
    stage_updates = {
        '3.3': {
            'Notes_Append': '''

**INFRASTRUCTURE TRANSITION:**

Phase 3 uses fully serverless SageMaker architecture.
**EC2 downgraded (not terminated)** after Phase 2 completion.

**Infrastructure Components:**
- ✅ **SageMaker Training Jobs:** ml.m5.2xlarge (on-demand compute)
- ✅ **SageMaker Endpoints:** ml.m5.2xlarge (auto-scaling 1-4 instances)
- ✅ **Lambda Functions:** Feature extraction + inference API
- ✅ **API Gateway:** REST API for predictions
- ✅ **Aurora Serverless v2:** Feature data (0.5-32 ACU)
- ℹ️  **EC2 (t3.xlarge):** Downgraded for monitoring/maintenance (optional)

**NO HIGH-PERFORMANCE EC2 REQUIRED**

The c7i.8xlarge instance used during Phase 2 is downgraded to t3.xlarge
after Phase 2 completes. Phase 3 workloads run on SageMaker infrastructure.

**EC2 Role in Phase 3:**
- Monitoring and troubleshooting
- Ad-hoc database queries
- Support for other projects (Robkei-Ring, OmniDrive, box)
- Emergency maintenance access

**Cost Structure:**
- SageMaker Training: $9.46/month
- SageMaker Inference: $391.86/month
- Storage & Monitoring: $111.06/month
- EC2 (t3.xlarge, optional): $121/month
- **Total: ~$633/month** (vs $840/month if c7i.8xlarge kept)
'''
        },
        '3.5': {
            'Notes_Append': '''

**INFRASTRUCTURE TRANSITION COMPLETE:**

**Phase 1-2 Infrastructure:**
- EC2: t3.2xlarge ($243/month)
- Upgraded to c7i.8xlarge for Phase 2 ($27.25 total)
- Downgraded to t3.xlarge after Phase 2 ($121/month)
- **Status:** Active (downgraded, not terminated)

**Phase 3 Infrastructure:**
- SageMaker Training: ml.m5.2xlarge (on-demand)
- SageMaker Inference: ml.m5.2xlarge (auto-scaling)
- Lambda: Feature extraction + API
- Aurora: Serverless v2 (0.5-32 ACU)
- EC2: t3.xlarge (monitoring only)

**Monthly Cost Summary:**
| Component | Cost |
|-----------|------|
| SageMaker Training | $9.46 |
| SageMaker Inference | $391.86 |
| Aurora Serverless | $87.60 |
| S3 + CloudWatch | $23.46 |
| EC2 (t3.xlarge, optional) | $121.00 |
| **Total** | **~$633/month** |

**Cost Savings vs Phase 2:**
- Phase 2 (c7i.8xlarge): $993/month (if kept running)
- Phase 3 (Serverless + t3.xlarge): $633/month
- **Savings: $360/month (36% reduction)**

**Annual Savings:**
- Phase 2 high-performance EC2 eliminated: $11,916/year savings
- Downgraded EC2 (t3.2xlarge → t3.xlarge): $1,464/year savings
- **Total Annual Savings: $13,380/year**

**Infrastructure Evolution:**
```
Phase 1-2:  EC2 (batch processing) → Aurora (storage)
            ↓
Phase 2:    EC2 upgraded for acceleration (temporary)
            ↓
Phase 3:    SageMaker (serverless ML) + Lambda (API) + Aurora (data)
            EC2 downgraded to minimal monitoring role
```

**Monitoring & Logging:**
- CloudWatch Dashboards: SageMaker metrics, inference latency
- SageMaker Model Monitor: Drift detection, data quality
- Lambda Logs: API request/response logging
- Aurora Performance Insights: Database query performance
- EC2 (t3.xlarge): Optional SSH access for troubleshooting
'''
        }
    }

    # Update Phase 3 stages
    updated_count = 0
    for stage in stages:
        stage_id = stage['fields'].get('Stage ID', '')

        # Extract numeric portion (e.g., "3.3" from "3.3 - Model Deployment Infrastructure")
        stage_id_short = stage_id.split(' ')[0] if ' ' in stage_id else stage_id

        # Also handle "Stage 3.3" format
        if stage_id.startswith('Stage '):
            stage_id_short = stage_id.replace('Stage ', '').split(' ')[0]

        if stage_id_short in stage_updates:
            print(f"Updating {stage_id}...")

            update_def = stage_updates[stage_id_short]
            current_notes = stage['fields'].get('Notes', '')
            updates = {
                'Notes': current_notes + update_def['Notes_Append']
            }

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
    print(f"✅ Updated {updated_count}/{len(stage_updates)} Phase 3 stages")
    print()
    print("Updated Stages:")
    print("  - Stage 3.3: Added serverless architecture notes")
    print("  - Stage 3.5: Added infrastructure transition summary")
    print()
    print("Summary:")
    print("  - Phase 3 clarified as fully serverless")
    print("  - EC2 downgrade (not termination) documented")
    print("  - Monthly cost breakdown provided")
    print("  - Annual savings: $13,380/year")

if __name__ == '__main__':
    main()
