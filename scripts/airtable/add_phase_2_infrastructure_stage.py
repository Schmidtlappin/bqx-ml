#!/usr/bin/env python3
"""
Add Stage 2.10 - Infrastructure Management to AirTable
Documents EC2 upgrade/downgrade strategy for Phase 2
"""

import os
import requests
import json
from datetime import datetime

# AirTable configuration
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
BASE_ID = 'appR3PPnrNkVo48mO'
STAGES_TABLE = 'Stages'

def create_stage_2_10():
    """Create Stage 2.10 - Infrastructure Management"""

    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }

    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}'

    # Stage 2.10 content
    stage_data = {
        'fields': {
            'Stage ID': '2.10 - Infrastructure Management',
            'Stage Code': 'BQX-2.10',
            'Status': 'In Progress',
            'Description': 'EC2 upgrade for Phase 2 acceleration, followed by downgrade to cost-effective instance for ongoing operations',
            'Duration': '1.3 days (Phase 2 accelerated)',
            'Estimated Cost': 27.25,
            'Notes': '''🚀 **EC2 UPGRADE APPROVED: 2025-11-14**

## Decision: Option 2 (c7i.8xlarge with Spot Pricing)

**Upgrade Strategy:**
- **Current:** t3.2xlarge (8 vCPUs, 32GB RAM, $0.33/hour)
- **Phase 2 Upgrade:** c7i.8xlarge (32 vCPUs, 64GB RAM, ~$0.45/hour Spot)
- **Post-Phase 2 Downgrade:** t3.xlarge (4 vCPUs, 16GB RAM, $0.17/hour)

**Implementation Method:** IN-PLACE UPGRADE
- Stop trillium-master instance
- Change instance type to c7i.8xlarge
- Start instance (5-minute downtime)
- Track 2 workers resume automatically

---

## Phase 2 Timeline Impact

**Baseline (t3.2xlarge):**
- Total Duration: 130 hours (5.4 days)
- Total Cost: $60.86

**Upgraded (c7i.8xlarge Spot):**
- Total Duration: 31 hours (1.3 days)
- Total Cost: $27.25
- **Savings: $33.61 (55%) + 99 hours (76% faster)**

**Stage-by-Stage Impact:**
- Track 2 (2.1.2): 2.8 hours (vs 11 hours baseline)
- Stage 2.2: 3.8 hours (vs 15 hours)
- Stage 2.9: 12 hours (vs 48 hours) - BIGGEST IMPACT
- Stage 2.6: 6 hours (vs 24 hours)
- Stage 2.7: 6 hours (vs 24 hours)

---

## Post-Phase 2 Downgrade Plan

**IMPORTANT: EC2 NOT TERMINATED**

After Stage 2.7 (S3 Export) completes:
1. Stop c7i.8xlarge instance
2. Change instance type to **t3.xlarge** (4 vCPUs, 16GB RAM)
3. Start instance
4. Instance remains active for:
   - Phase 3 monitoring and maintenance
   - Other projects: Robkei-Ring, OmniDrive, box
   - Ad-hoc database queries
   - Emergency troubleshooting

**Monthly Cost Reduction:**
- Phase 2 (c7i.8xlarge Spot): ~$330/month (if kept running - NOT RECOMMENDED)
- Post-Downgrade (t3.xlarge): $121/month
- **Savings vs Current:** $121/month (50% reduction from $243/month)

---

## Cost Analysis

| Phase | Instance | Duration | Cost |
|-------|----------|----------|------|
| **Phase 2** | c7i.8xlarge Spot | 31 hours | $27.25 |
| **Post-Phase 2** | t3.xlarge | Ongoing | $121/month |

**Phase 2 Breakdown:**
- EC2 (Spot): ~$14/month
- Aurora (2.5 ACU avg): $9.30
- S3 + Transfer Accel: $4
- **Total: $27.25** (vs $60.86 baseline = 55% savings)

**Annual Savings (Post-Downgrade):**
- Current t3.2xlarge: $243/month × 12 = $2,916/year
- Downgraded t3.xlarge: $121/month × 12 = $1,452/year
- **Annual Savings: $1,464/year**

---

## Implementation Checklist

**Pre-Upgrade:**
- [x] EC2 upgrade Option 2 approved by user (2025-11-14)
- [ ] Track 2 current progress verified (97.3% complete)
- [ ] Create AMI snapshot (backup)
- [ ] Document running processes
- [ ] Gracefully stop Track 2 workers

**Upgrade Execution:**
- [ ] Stop trillium-master instance
- [ ] Change instance type to c7i.8xlarge
- [ ] Request Spot pricing (~$0.45/hour)
- [ ] Start instance
- [ ] Verify 32 vCPUs, 64GB RAM available

**Post-Upgrade Validation:**
- [ ] Test Aurora database connectivity
- [ ] Verify Python environment intact
- [ ] Restart Track 2 with 32 workers
- [ ] Monitor worker parallelization
- [ ] Verify 4x speedup achieved

**Post-Phase 2 Downgrade:**
- [ ] Validate Stage 2.7 (S3 Export) complete
- [ ] Verify all 1,080 features in Aurora
- [ ] Verify Parquet files in S3 (40-50 GB)
- [ ] Stop c7i.8xlarge instance
- [ ] Change instance type to t3.xlarge
- [ ] Start instance
- [ ] Verify other projects operational
- [ ] Update monthly cost tracking

---

## Risk Assessment

**Technical Risk:** LOW
- ✅ In-place upgrade is AWS standard procedure
- ✅ All data on EBS volumes (preserved)
- ✅ Track 2 workers are stateless (resume automatically)
- ✅ 5-minute downtime acceptable (development workload)

**Cost Risk:** LOW
- ✅ Phase 2 duration limited to 1.3 days
- ✅ Immediate downgrade after completion
- ✅ Total cost $27.25 (cheaper than baseline!)

**Operational Risk:** LOW
- ✅ trillium-master hosts other projects (will briefly stop)
- ✅ Other projects auto-restart after downtime
- ✅ No production traffic dependencies

---

## Phase 3 Considerations

**EC2 Role in Phase 3:**
- Phase 3 uses SageMaker (serverless architecture)
- EC2 NOT required for Phase 3 operations
- EC2 kept active (downgraded) for:
  - Monitoring and troubleshooting
  - Ad-hoc database queries
  - Support for other projects
  - Emergency maintenance access

**Phase 3 Costs (No EC2 Dependency):**
- SageMaker Training: $9.46/month
- SageMaker Inference: $391.86/month
- Storage & Monitoring: $111.06/month
- EC2 (t3.xlarge, optional): $121/month
- **Total: ~$633/month** (Phase 3 + downgraded EC2)

---

## Timeline

**Estimated Dates:**
- Upgrade Execution: 2025-11-14 (pending Track 2 completion)
- Phase 2 Completion: 2025-11-15 (~1.3 days after upgrade)
- Downgrade Execution: 2025-11-15 (immediately after Phase 2)
- Phase 3 Start: 2025-11-16

---

**Status:** ⏳ APPROVED - Awaiting Track 2 completion for upgrade execution
**Next Action:** Execute upgrade when Track 2 reaches 100% (currently 97.3%)
**Owner:** Infrastructure Team
**Updated:** 2025-11-14
'''
        }
    }

    try:
        response = requests.post(url, headers=headers, json=stage_data)

        if response.status_code in [200, 201]:
            print("=" * 80)
            print("STAGE 2.10 CREATED SUCCESSFULLY")
            print("=" * 80)
            print()
            print("✅ Stage ID: 2.10 - Infrastructure Management")
            print("✅ Status: In Progress")
            print("✅ Duration: 1.3 days")
            print("✅ Cost: $27.25")
            print()
            print("Key Details:")
            print("  - Upgrade: t3.2xlarge → c7i.8xlarge (Phase 2)")
            print("  - Downgrade: c7i.8xlarge → t3.xlarge (Post-Phase 2)")
            print("  - EC2 remains active (not terminated)")
            print("  - Annual savings: $1,464/year")
            print()
            return response.json()
        else:
            print(f"❌ Failed to create Stage 2.10: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error creating Stage 2.10: {e}")
        return None

def main():
    """Main execution"""
    print()
    print("=" * 80)
    print("AIRTABLE UPDATE: CREATE STAGE 2.10 - INFRASTRUCTURE MANAGEMENT")
    print("=" * 80)
    print()

    result = create_stage_2_10()

    if result:
        print("=" * 80)
        print("AIRTABLE UPDATE COMPLETE")
        print("=" * 80)
    else:
        print("=" * 80)
        print("AIRTABLE UPDATE FAILED")
        print("=" * 80)

if __name__ == '__main__':
    main()
