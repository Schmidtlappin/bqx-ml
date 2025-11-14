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
            'Description': 'Temporary EC2 (c7i.8xlarge) for Phase 2 acceleration, then terminate. Optional downgrade of trillium-master to t3.small for cost optimization.',
            'Duration': '1.8 days (Phase 2 accelerated)',
            'Estimated Cost': 19.13,
            'Notes': '''🚀 **TEMPORARY EC2 APPROVED: 2025-11-14**

## Decision: Temporary EC2 (c7i.8xlarge Spot) - NOT In-Place Upgrade

**Architecture:**
- **trillium-master:** Keep running (optional downgrade to t3.small)
- **NEW: trillium-phase2-worker:** c7i.8xlarge Spot (TEMPORARY)
- **Post-Phase 2:** TERMINATE trillium-phase2-worker

**Rationale:** See docs/architecture_decision_temporary_ec2.md
- Zero downtime on trillium-master
- Lower risk (isolated failure domain)
- 87% lower ongoing costs (t3.small vs t3.xlarge)
- Cleaner separation of concerns

---

## Infrastructure Plan

**trillium-master (Permanent):**
- **Current:** t3.2xlarge (8 vCPUs, 32GB RAM, $0.33/hr)
- **Recommended:** t3.small (2 vCPUs, 2GB RAM, $0.0208/hr)
- **Role:** Monitoring, maintenance, ad-hoc queries
- **Lifecycle:** Always-on
- **Monthly Cost:** $15.15 (vs $121 for t3.xlarge = 87% savings)

**trillium-phase2-worker (Temporary):**
- **Type:** c7i.8xlarge Spot (32 vCPUs, 64GB RAM, ~$0.45/hr)
- **Role:** Phase 2 parallel processing ONLY
- **Lifecycle:** 1.8 days, then TERMINATE
- **Total Cost:** $19.13 (Spot pricing)

---

## Phase 2 Timeline Impact

**Baseline (t3.2xlarge):**
- Total Duration: 130 hours (5.4 days)
- Total Cost: $60.86

**Temporary EC2 (c7i.8xlarge Spot):**
- Total Duration: 42.5 hours (1.8 days)
- Total Cost: $19.13
- **Savings: $41.73 (69%) + 87.5 hours (67% faster)**

**Stage-by-Stage Impact:**
- Stage 2.2: 3.8 hours (vs 15 hours)
- Stage 2.3: 4 hours (vs 48 hours)
- Stage 2.4: 12 hours (vs 48 hours)
- Stage 2.6: 6 hours (vs 24 hours)
- Stage 2.7: 6 hours (vs 24 hours)
- Stage 2.8: 6 hours (vs 24 hours)
- Stage 2.9: 12 hours (vs 48 hours) - BIGGEST IMPACT

---

## Cost Analysis

| Instance | Role | Duration | Cost |
|----------|------|----------|------|
| **trillium-master** | Monitoring (permanent) | Ongoing | $15/month |
| **trillium-phase2-worker** | Phase 2 compute (temp) | 42.5 hours | $19.13 |
| **Total Phase 2** | - | 1.8 days | **$19.13** |

**Annual Cost Comparison:**

| Approach | Phase 2 Cost | Ongoing (Annual) | Total (1 Year) |
|----------|--------------|------------------|----------------|
| **In-Place Upgrade (OLD)** | $19.13 | $1,454.40 | $1,473.53 |
| **Temporary EC2 (NEW)** | $19.13 | $181.80 | $200.93 |
| **Savings** | $0.00 | **$1,272.60** | **$1,272.60** |

**Cost Breakdown:**
- trillium-master (t3.small): $15.15/month × 12 = $181.80/year
- trillium-phase2-worker: $19.13 one-time
- **Total 1-year cost:** $200.93 (vs $1,473.53 = 86% savings)

---

## Implementation Checklist

**Step 1: Downgrade trillium-master (Optional)**
- [ ] Create pre-downgrade snapshot
- [ ] Stop trillium-master
- [ ] Change type: t3.2xlarge → t3.small
- [ ] Start trillium-master
- [ ] Verify: 2 vCPUs, 2GB RAM
- **Duration:** 30 min (5 min downtime)
- **Savings:** $106/month

**Step 2: Spin Up Temporary Worker**
- [ ] Launch c7i.8xlarge Spot instance
- [ ] Tag: Name=trillium-phase2-worker, Lifecycle=temporary
- [ ] Configure security groups, key pair
- [ ] Clone bqx-ml repository
- [ ] Install dependencies
- [ ] Configure Aurora credentials
- **Duration:** 15 min
- **Cost:** $0.11

**Step 3: Run Phase 2 Stages**
- [ ] Execute launch_phase_2_post_track2.sh
- [ ] Monitor progress (Stages 2.2-2.9)
- [ ] Verify all partitions populated
- [ ] Validate S3 export (40-50 GB)
- **Duration:** 42.5 hours
- **Cost:** $19.13

**Step 4: Terminate Temporary Worker**
- [ ] Verify Phase 2 100% complete
- [ ] Create final snapshot (optional)
- [ ] TERMINATE trillium-phase2-worker
- [ ] Verify termination (not stopped)
- [ ] Update cost tracking
- **Duration:** 5 min
- **Ongoing Cost:** $0.00

---

## Risk Assessment

**Technical Risk:** LOW
- ✅ trillium-master: Zero downtime (stays running)
- ✅ Temporary EC2: Isolated failure domain
- ✅ All data in Aurora (stateless workers)
- ✅ Easy rollback (just terminate temp EC2)

**Cost Risk:** VERY LOW
- ✅ Phase 2 limited to 1.8 days
- ✅ Immediate termination after completion
- ✅ Ongoing cost: $15/month (vs $121/month)
- ✅ Total cost $19.13 (cheaper than baseline!)

**Operational Risk:** VERY LOW
- ✅ trillium-master unaffected by Phase 2
- ✅ Can run both instances simultaneously
- ✅ No production dependencies
- ✅ Clear cost attribution (separate instances)

---

## Comparison: In-Place vs Temporary EC2

| Criteria | In-Place Upgrade | Temporary EC2 | Winner |
|----------|------------------|---------------|--------|
| **Phase 2 Cost** | $19.13 | $19.13 | TIE |
| **Ongoing Cost** | $121/mo | $15/mo | ✅ **Temp EC2** (-87%) |
| **Annual Savings** | $1,464 | $2,737 | ✅ **Temp EC2** (+87%) |
| **trillium-master Downtime** | 10 min | 0 min | ✅ **Temp EC2** |
| **Production Risk** | Medium | Low | ✅ **Temp EC2** |
| **Rollback** | Hard | Easy | ✅ **Temp EC2** |

**Winner:** ✅ Temporary EC2 (5 wins, 0 losses, 1 tie)

---

## Phase 3 Considerations

**EC2 Role in Phase 3:**
- Phase 3 uses SageMaker (serverless architecture)
- trillium-master (t3.small) provides:
  - SageMaker experiment monitoring
  - Ad-hoc database queries
  - Script development/testing
  - Emergency maintenance access

**Phase 3 Costs:**
- SageMaker Training: $9.46/month
- SageMaker Inference: $391.86/month
- Storage & Monitoring: $111.06/month
- EC2 (t3.small): $15.15/month
- **Total: ~$527/month** (vs $633 with t3.xlarge = $106/month savings)

---

## Timeline

**Estimated Dates:**
- trillium-master Downgrade: 2025-11-14 (optional, 30 min)
- Spin Up temp EC2: 2025-11-14 (15 min)
- Phase 2 Execution: 2025-11-14 to 2025-11-16 (1.8 days)
- Terminate temp EC2: 2025-11-16 (5 min)
- Phase 3 Start: 2025-11-16

---

**Status:** ✅ APPROVED - Ready for implementation
**Next Action:** Downgrade trillium-master (optional), then spin up temporary EC2
**Architecture:** Temporary EC2 approach (NOT in-place upgrade)
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
            print("✅ Duration: 1.8 days")
            print("✅ Cost: $19.13")
            print()
            print("Key Details:")
            print("  - Architecture: Temporary EC2 (NOT in-place upgrade)")
            print("  - trillium-master: Optional downgrade to t3.small")
            print("  - trillium-phase2-worker: c7i.8xlarge Spot (TEMPORARY)")
            print("  - Post-Phase 2: TERMINATE temporary worker")
            print("  - Annual savings: $1,272.60/year (vs in-place upgrade)")
            print("  - Annual savings: $2,736.60/year (vs current t3.2xlarge)")
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
