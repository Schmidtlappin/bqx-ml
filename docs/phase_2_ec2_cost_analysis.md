# Phase 2 EC2 Cost Analysis

**Date:** 2025-11-14 (Updated)
**Region:** US East (N. Virginia) - us-east-1
**Architecture:** ✅ **Temporary EC2 Approach (APPROVED)**

---

## ✅ APPROVED ARCHITECTURE: Temporary EC2 (NOT In-Place Upgrade)

**Decision Date:** 2025-11-14

### Architecture Overview

**OLD APPROACH (Rejected):**
- Upgrade trillium-master in-place: t3.2xlarge → c7i.8xlarge → t3.xlarge
- 10 minutes downtime (2 stop/start cycles)
- Ongoing cost: $121/month (t3.xlarge)

**NEW APPROACH (Approved):**
- **trillium-master:** Keep running (optional downgrade to t3.small)
- **NEW: trillium-phase2-worker:** Spin up c7i.8xlarge Spot (TEMPORARY)
- **Post-Phase 2:** TERMINATE temporary worker
- Zero downtime, isolated failure domain
- Ongoing cost: $15/month (t3.small)

**Rationale:** See [docs/architecture_decision_temporary_ec2.md](architecture_decision_temporary_ec2.md)

### Cost Comparison

| Approach | Phase 2 Cost | Ongoing (Annual) | Total (1 Year) | Annual Savings |
|----------|--------------|------------------|----------------|----------------|
| **Current (t3.2xlarge)** | $60.86 | $2,916.00 | $2,976.86 | - |
| **In-Place Upgrade** | $19.13 | $1,454.40 | $1,473.53 | $1,503.33 |
| **Temporary EC2** | $19.13 | $181.80 | $200.93 | **$2,775.93** |

**Winner:** ✅ Temporary EC2 saves **$1,272.60/year MORE** than in-place upgrade!

---

## Current Infrastructure Baseline

### Current EC2: t3.2xlarge
- **Specification:** 8 vCPUs, 32 GB RAM
- **Hourly Rate:** $0.3328/hour
- **Monthly Cost (730 hours):** $242.94/month
- **Phase 2 Duration:** 130 hours (5.4 days)
- **Phase 2 Total Cost:** $43.26

### Current Aurora Serverless v2
- **Configuration:** Min 0.5 ACU, Max 32 ACU
- **Average Usage:** ~1 ACU
- **Hourly Rate:** $0.12/ACU-hour
- **Phase 2 Cost:** $0.12 × 1 ACU × 130 hours = $15.60

### Current S3 Costs
- **Storage:** 50 GB @ $0.023/GB = $1.15/month
- **Transfer:** Minimal (<$2)
- **Phase 2 Export:** ~$2

**Current Phase 2 Total: $43.26 (EC2) + $15.60 (Aurora) + $2 (S3) = $60.86**

---

## Option 1: c7i.4xlarge (RECOMMENDED)

### EC2 Specifications
- **vCPUs:** 16 (2x current)
- **Memory:** 32 GB (same)
- **Network:** Up to 12.5 Gbps
- **Instance Family:** Compute Optimized (7th gen Intel)
- **Processor:** Intel Xeon Scalable (Sapphire Rapids)

### Pricing Breakdown

**Hourly Rate:** $0.68/hour

**Phase 2 Duration:** 62 hours (2.6 days)
- Track 2 remaining: 5.5 hours
- Stage 2.2: 7.5 hours
- Stage 2.9: 24 hours
- Stage 2.6: 12 hours
- Stage 2.7: 12 hours
- Parallel stages: Overlap reduces total time

**Phase 2 Total EC2 Cost:** $0.68 × 62 hours = **$42.16**

**Aurora Upgrade (Min 2 ACU):**
- Hourly: $0.12 × 2 ACU = $0.24/hour
- Phase 2: $0.24 × 62 hours = **$14.88**

**S3 Costs:** $2 (no change)

**Phase 2 Total:** $42.16 + $14.88 + $2 = **$59.04**

### Cost Comparison vs Current
- **Current:** $60.86
- **Option 1:** $59.04
- **Savings:** $1.82 (3% cheaper!)
- **Time Saved:** 68 hours (52% reduction)

### Monthly Cost (if kept running)
- **EC2:** $0.68 × 730 = $496.40/month
- **Aurora:** $0.24 × 730 = $175.20/month
- **Total:** $671.60/month (vs $242.94 current)
- **Increase:** +$428.66/month

**Recommendation:** Upgrade only for Phase 2, then downgrade back to t3.2xlarge or smaller

---

## Option 2: c7i.8xlarge (MAXIMUM PERFORMANCE)

### EC2 Specifications
- **vCPUs:** 32 (4x current)
- **Memory:** 64 GB (2x current)
- **Network:** 12.5 Gbps
- **Instance Family:** Compute Optimized (7th gen Intel)
- **Processor:** Intel Xeon Scalable (Sapphire Rapids)

### Pricing Breakdown

**Hourly Rate:** $1.36/hour

**Phase 2 Duration:** 31 hours (1.3 days)
- Track 2 remaining: 2.8 hours
- Stage 2.2: 3.8 hours
- Stage 2.9: 12 hours
- Stage 2.6: 6 hours
- Stage 2.7: 6 hours
- Parallel stages: Maximum overlap

**Phase 2 Total EC2 Cost:** $1.36 × 31 hours = **$42.16**

**Aurora Upgrade (Min 2 ACU, Max 64 ACU):**
- Average usage: 2-3 ACU (parallel queries)
- Hourly: $0.12 × 2.5 ACU = $0.30/hour
- Phase 2: $0.30 × 31 hours = **$9.30**

**S3 Transfer Acceleration:**
- Base transfer: 50 GB
- Acceleration fee: $0.04/GB
- Cost: 50 × $0.04 = **$2.00**

**S3 Standard Transfer:** $2

**Phase 2 Total:** $42.16 + $9.30 + $2 + $2 = **$55.46**

### Cost Comparison vs Current
- **Current:** $60.86
- **Option 2:** $55.46
- **Savings:** $5.40 (9% cheaper!)
- **Time Saved:** 99 hours (76% reduction)

### Monthly Cost (if kept running)
- **EC2:** $1.36 × 730 = $992.80/month
- **Aurora:** $0.30 × 730 = $219/month
- **Total:** $1,211.80/month
- **Increase:** +$968.86/month vs current

**Recommendation:** Upgrade only for Phase 2, immediate downgrade after

---

## Option 3: c6i.4xlarge (COST-OPTIMIZED)

### EC2 Specifications
- **vCPUs:** 16 (2x current)
- **Memory:** 32 GB (same)
- **Network:** Up to 12.5 Gbps
- **Instance Family:** Compute Optimized (6th gen Intel - previous generation)
- **Processor:** Intel Xeon Scalable (Ice Lake)

### Pricing Breakdown

**Hourly Rate:** $0.544/hour (20% cheaper than c7i.4xlarge)

**Phase 2 Duration:** 65 hours (2.7 days)
- Slightly slower than c7i due to older CPU architecture
- Track 2: 5.8 hours
- Stage 2.2: 8 hours
- Stage 2.9: 25 hours
- Stage 2.6: 13 hours
- Stage 2.7: 13 hours

**Phase 2 Total EC2 Cost:** $0.544 × 65 hours = **$35.36**

**Aurora Upgrade (Min 1 ACU):**
- Hourly: $0.12 × 1 = $0.12/hour
- Phase 2: $0.12 × 65 hours = **$7.80**

**S3 Costs:** $2

**Phase 2 Total:** $35.36 + $7.80 + $2 = **$45.16**

### Cost Comparison vs Current
- **Current:** $60.86
- **Option 3:** $45.16
- **Savings:** $15.70 (26% cheaper!)
- **Time Saved:** 65 hours (50% reduction)

### Monthly Cost (if kept running)
- **EC2:** $0.544 × 730 = $397.12/month
- **Aurora:** $0.12 × 730 = $87.60/month
- **Total:** $484.72/month
- **Increase:** +$241.78/month vs current

---

## Spot Instance Pricing (60-70% Discount)

### Option 2 with Spot Instances: c7i.8xlarge

**Spot Price (typical):** ~$0.45/hour (67% discount from $1.36)

**Phase 2 Total EC2 Cost:** $0.45 × 31 hours = **$13.95**

**Total Phase 2:** $13.95 + $9.30 + $4 = **$27.25**

**Savings vs Current:** $60.86 - $27.25 = **$33.61 (55% cheaper!)**

**Risk:** Spot instances can be interrupted with 2-minute warning
- Mitigation: Use Spot blocks or checkpointing
- For Phase 2 workload: LOW risk (1-3 day duration, stateful workers)

---

## Cost Summary Table

| Option | Instance | Hours | EC2 Cost | Aurora | S3 | Total | vs Current | Time Saved | $/Hour Saved |
|--------|----------|-------|----------|--------|----|----|------------|------------|--------------|
| **Current** | t3.2xlarge | 130h | $43.26 | $15.60 | $2 | **$60.86** | - | 0h | - |
| **Option 1** | c7i.4xlarge | 62h | $42.16 | $14.88 | $2 | **$59.04** | -$1.82 | 68h | -$0.03/h |
| **Option 2** | c7i.8xlarge | 31h | $42.16 | $9.30 | $4 | **$55.46** | -$5.40 | 99h | -$0.05/h |
| **Option 3** | c6i.4xlarge | 65h | $35.36 | $7.80 | $2 | **$45.16** | -$15.70 | 65h | -$0.24/h |
| **Spot (Opt 2)** | c7i.8xlarge Spot | 31h | $13.95 | $9.30 | $4 | **$27.25** | -$33.61 | 99h | -$0.34/h |

---

## Key Insights

### 1. All Upgrades Are CHEAPER Than Current
- Faster instances complete Phase 2 in less total time
- Total cost decreases despite higher hourly rates
- **Counterintuitive but true:** More expensive instances = lower total cost

### 2. Best Value: Option 3 (c6i.4xlarge)
- **Lowest total cost:** $45.16 (26% cheaper)
- **Achieves 50% time reduction goal**
- **Previous-gen CPU is sufficient** for Phase 2 workloads

### 3. Best Performance: Option 2 with Spot
- **Fastest completion:** 1.3 days vs 5.4 days
- **Lowest cost with Spot:** $27.25 (55% cheaper!)
- **Highest risk:** Spot interruption (but low probability)

### 4. Recommended: Option 1 (c7i.4xlarge)
- **Balanced approach:** 52% time reduction
- **Near-identical cost:** $59.04 vs $60.86 current
- **Latest-gen CPU:** Better single-thread performance
- **Low risk:** On-demand availability guaranteed

---

## Post-Phase 2 Downgrade Strategy

### After Phase 2 Completes, Downgrade To:

**Option A: t3.xlarge (Cost Savings)**
- 4 vCPUs, 16 GB RAM
- $0.1664/hour = $121.47/month
- **Savings:** $121.47/month vs current $242.94
- Sufficient for Phase 3 monitoring/maintenance

**Option B: t3.2xlarge (Keep Current)**
- 8 vCPUs, 32 GB RAM
- $0.3328/hour = $242.94/month
- Same as current

**Option C: Stop Instance When Not Needed**
- Phase 3 uses SageMaker (not EC2)
- Only need EC2 for ad-hoc analysis
- **Savings:** ~$200/month

---

## Recommendation Summary

### For Budget-Conscious: Option 3 (c6i.4xlarge)
- **Total Cost:** $45.16 (CHEAPEST)
- **Time:** 2.7 days
- **Savings:** $15.70 vs current

### For Balanced Approach: Option 1 (c7i.4xlarge)
- **Total Cost:** $59.04 (nearly same as current)
- **Time:** 2.6 days
- **Latest hardware:** Better future-proofing

### For Maximum Speed: Option 2 with Spot (c7i.8xlarge)
- **Total Cost:** $27.25 (FASTEST + CHEAPEST with Spot)
- **Time:** 1.3 days (FASTEST)
- **Risk:** Low but non-zero Spot interruption

---

## Implementation Cost Breakdown

### One-Time Costs
- AMI Snapshot: $0.05/GB-month × 50 GB = $2.50
- EBS Snapshot: Included
- **Total:** ~$3

### Upgrade Process (Zero Cost)
- Instance type change: FREE (no charge for stopped instance)
- Aurora scaling: Automatic, no charge

### Total Project Cost

**Option 1 (c7i.4xlarge) Full Cost:**
- AMI Snapshot: $3
- Phase 2 Execution: $59.04
- **Total:** $62.04

**Option 2 (c7i.8xlarge Spot) Full Cost:**
- AMI Snapshot: $3
- Phase 2 Execution: $27.25
- **Total:** $30.25 (BEST VALUE!)

---

**Conclusion:** All upgrade options are cost-effective. Even the "most expensive" option (c7i.8xlarge) costs LESS than the current approach due to dramatically reduced runtime. Option 2 with Spot pricing offers the best combination of speed and cost savings.

---

## USER APPROVED STRATEGY: Option 2 with Post-Phase 2 Downgrade

**Date Approved:** 2025-11-14
**Decision:** IN-PLACE UPGRADE → DOWNGRADE (NOT TERMINATE)

### Implementation Plan

**Phase 1: Upgrade to c7i.8xlarge (Phase 2 Acceleration)**
- **When:** After Track 2 reaches 100% (currently 97.3%)
- **Method:** In-place upgrade (stop → change type → start)
- **Duration:** 30 minutes (5 min downtime)
- **Cost:** $27.25 total for Phase 2 (1.3 days)

**Phase 2: Downgrade to t3.xlarge (Post-Phase 2)**
- **When:** Immediately after Stage 2.7 (S3 Export) completes
- **Method:** In-place downgrade (stop → change type → start)
- **Duration:** 30 minutes (5 min downtime)
- **Ongoing Cost:** $121/month (vs $243/month current)

### Cost Summary with Downgrade Strategy

| Phase | Instance | Duration | Total Cost |
|-------|----------|----------|------------|
| **Phase 2** | c7i.8xlarge Spot | 31 hours (1.3 days) | $27.25 |
| **Post-Phase 2** | t3.xlarge | Ongoing | $121/month |

**Phase 2 Savings:** $60.86 - $27.25 = **$33.61 (55% savings)**
**Ongoing Savings:** $243/month - $121/month = **$122/month (50% savings)**
**Annual Savings:** $122 × 12 = **$1,464/year**

### Why Downgrade (Not Terminate)?

**EC2 Remains Active for:**
1. Phase 3 monitoring and troubleshooting
2. Ad-hoc database queries and analysis
3. Other projects: Robkei-Ring, OmniDrive, box
4. Emergency maintenance access

**Phase 3 Architecture:**
- Primary compute: SageMaker (serverless) - $512/month
- EC2 role: Monitoring only (t3.xlarge) - $121/month
- Total Phase 3 cost: ~$633/month (no high-performance EC2 required)

### Downgrade Specifications

**Target Instance: t3.xlarge**
- **vCPUs:** 4 (half of current t3.2xlarge)
- **RAM:** 16 GB (half of current)
- **Cost:** $0.17/hour ($121/month)
- **Purpose:** Monitoring, maintenance, support for other projects
- **Sufficient For:** All Phase 3 operational needs

### Total Project Savings

**Phase 2 Acceleration:**
- Baseline duration: 5.4 days
- Upgraded duration: 1.3 days
- Time saved: 4.1 days (76% faster)
- Cost saved: $33.61

**Ongoing Operations:**
- Current: $243/month (t3.2xlarge)
- Downgraded: $121/month (t3.xlarge)
- Annual savings: $1,464/year

**Combined:**
- Phase 2: Save $33.61 + 4.1 days
- Year 1: Save $1,464
- 5-Year Savings: **$7,320**

### Alternative Downgrade Options

If t3.xlarge proves oversized after Phase 3 launch:

| Instance | vCPUs | RAM | Monthly Cost | Annual Savings vs Current |
|----------|-------|-----|--------------|----------------------------|
| **t3.xlarge** | 4 | 16 GB | $121 | $1,464 |
| t3.medium | 2 | 4 GB | $30 | $2,556 |
| t3.small | 2 | 2 GB | $15 | $2,736 |
| Stopped (EBS only) | - | - | $5 | $2,856 |

**Recommendation:** Start with t3.xlarge, monitor usage, downgrade further if underutilized.

---

## Implementation Timeline

```
Today (2025-11-14):
├─ Track 2: 97.3% complete (327/336 partitions)
└─ Awaiting 100% completion

Track 2 100% (estimated +4.5 hours):
├─ Execute upgrade to c7i.8xlarge (30 min)
├─ Resume Track 2 with 32 workers
└─ Begin parallel Phase 2 stages

Phase 2 Complete (estimated +1.3 days):
├─ Validate all features in Aurora
├─ Verify S3 export (40-50 GB)
├─ Execute downgrade to t3.xlarge (30 min)
└─ Begin Phase 3 (SageMaker)

Ongoing (Phase 3+):
└─ t3.xlarge runs at $121/month
    Saving $122/month vs current
```

---

## Approval Status

✅ **Option 2 (c7i.8xlarge) APPROVED** - 2025-11-14
✅ **In-place upgrade strategy APPROVED**
✅ **Post-Phase 2 downgrade to t3.xlarge APPROVED**
✅ **EC2 remains active (not terminated) APPROVED**

**Next Action:** Execute upgrade when Track 2 reaches 336/336 partitions
**Owner:** Infrastructure Team
**Status:** Awaiting Track 2 completion (currently 97.3%)
