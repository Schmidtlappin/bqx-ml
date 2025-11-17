# TIER 1 Infrastructure - Spot Instance Failure & Option B

**Date:** 2025-11-17
**Status:** Proceeding with Option B (Upgrade trillium-master)
**Reason:** AWS Spot instance quota exceeded

---

## SPOT INSTANCE LAUNCH FAILURE

### Error Details

**Error Message:**
```
MaxSpotInstanceCountExceeded
An error occurred (MaxSpotInstanceCountExceeded) when calling the RequestSpotInstances operation: Max spot instance count exceeded
```

**Attempted Configuration:**
- Instance Type: c7i.8xlarge (32 vCPUs, 64 GB RAM)
- Pricing: Spot ($0.40/hour estimated)
- Region: us-east-1
- VPC: vpc-00b81d77ae5d7f098
- Subnet: subnet-0aa48fbf275ef3e2f
- Security Group: sg-0513e6cd4874f8c6b
- Key: trillium-master-key

### Root Cause

AWS account has reached maximum Spot instance count quota. This is likely due to:
- Regional Spot instance limits (hard limit on number of Spot instances)
- Account-level restrictions
- vCPU quota for Spot instances (c7i.8xlarge requires 32 vCPUs)

### Current Environment

**Existing Instances:**
- trillium-master (i-08a8fa9a42491827c): t3.2xlarge, running

**Active Spot Requests:**
- None

**Quota Check:**
- Service quota API calls failed (requires support plan or additional permissions)
- Unable to determine exact Spot instance limits

---

## SOLUTION: OPTION B - UPGRADE TRILLIUM-MASTER

### Rationale

Since Option A (temporary Spot instance) failed due to quota limits, proceeding with Option B:
- Temporarily upgrade trillium-master from t3.2xlarge → c7i.8xlarge
- Execute TIER 1 stages (2.3, 2.4, 2.16B)
- Downgrade back to t3.2xlarge

### Comparison

| Aspect | Option A (Spot) | Option B (Upgrade) | Winner |
|--------|-----------------|-------------------|--------|
| **Cost** | ~$22 (4 days Spot) | ~$22 (4 days On-Demand) | TIE |
| **Performance** | c7i.8xlarge (32 vCPUs) | c7i.8xlarge (32 vCPUs) | TIE |
| **Downtime** | 0 (separate instance) | ~10 min (stop/modify/start) | Option A |
| **Complexity** | High (new instance) | Low (modify existing) | **Option B** |
| **Risk** | Spot interruption | Stable | **Option B** |
| **Quota Issues** | ❌ BLOCKED | ✅ AVAILABLE | **Option B** |

**Winner:** Option B (given Spot quota constraints)

---

## IMPLEMENTATION PLAN

### Phase 1: Upgrade (10 minutes)

**Script:** `scripts/infrastructure/upgrade_trillium_master_for_tier1.sh`

**Steps:**
1. Stop trillium-master (2 minutes)
2. Modify instance type to c7i.8xlarge (30 seconds)
3. Start trillium-master (2 minutes)
4. Verify connectivity (5 minutes)

**Downtime:** ~5 minutes

**Impact:**
- SSH connection will drop during stop
- Public IP may change
- Need to reconnect after restart

### Phase 2: Execute TIER 1 (55 hours)

**Stages:**
1. Stage 2.3: Currency Indices (~20 hours, $8)
2. Stage 2.4: Triangular Arbitrage (~20 hours, $8)
3. Stage 2.16B: Expand Currency Blocs (~15 hours, $6)

**Total:** 55 hours, ~$22

### Phase 3: Downgrade (10 minutes)

**Script:** `scripts/infrastructure/downgrade_trillium_master_after_tier1.sh`

**Steps:**
1. Verify TIER 1 completion
2. Stop trillium-master (2 minutes)
3. Modify instance type to t3.2xlarge (30 seconds)
4. Start trillium-master (2 minutes)
5. Verify connectivity (5 minutes)

**Downtime:** ~5 minutes

**Cost Savings:** $243/month → $121/month (50% reduction)

---

## COST ANALYSIS

### Option A (Spot) - BLOCKED

**One-Time:**
- 4 days c7i.8xlarge Spot: ~$22

**Ongoing:**
- trillium-master (t3.2xlarge): $121/month (unchanged)

**Total:** $22 one-time + $121/month ongoing

### Option B (Upgrade) - SELECTED

**One-Time:**
- 4 days c7i.8xlarge On-Demand: ~$22
- 5 min downtime (upgrade): $0
- 5 min downtime (downgrade): $0

**Ongoing:**
- trillium-master (t3.2xlarge): $121/month (unchanged)

**Total:** $22 one-time + $121/month ongoing

**Difference:** $0 (identical cost)

---

## RISK ASSESSMENT

### Option A Risks (Spot)

❌ **Quota Limits:** Already blocked, cannot proceed
⚠️ **Spot Interruption:** Instance can be terminated anytime (2-hour notice)
⚠️ **Network Complexity:** Separate instance, additional security group rules
⚠️ **Data Transfer:** Need to ensure database access from new instance

### Option B Risks (Upgrade)

✅ **Quota Limits:** No issues (modifying existing instance)
✅ **Stability:** On-Demand instance, no interruption risk
⚠️ **Downtime:** 2× ~5 minutes (upgrade + downgrade)
⚠️ **IP Change:** Public IP may change on restart

**Risk Winner:** Option B (lower overall risk)

---

## EXECUTION TIMELINE

### Immediate (Now)

**Action:** Upgrade trillium-master
**Command:** `bash scripts/infrastructure/upgrade_trillium_master_for_tier1.sh`
**Duration:** 10 minutes
**Downtime:** 5 minutes

### Day 1-2 (Stage 2.3)

**Action:** Execute Currency Indices
**Command:** `nohup python3 scripts/tier1/stage_2_3_currency_indices.py > /tmp/logs/tier1/stage_2_3/execution.log 2>&1 &`
**Duration:** ~20 hours
**Cost:** ~$8

### Day 2-3 (Stage 2.4)

**Action:** Execute Triangular Arbitrage
**Duration:** ~20 hours
**Cost:** ~$8

### Day 3-4 (Stage 2.16B)

**Action:** Execute Currency Blocs
**Duration:** ~15 hours
**Cost:** ~$6

### Day 4 (Downgrade)

**Action:** Downgrade trillium-master
**Command:** `bash scripts/infrastructure/downgrade_trillium_master_after_tier1.sh`
**Duration:** 10 minutes
**Downtime:** 5 minutes
**Savings:** $122/month

---

## FILES CREATED

**Upgrade Script:**
- `scripts/infrastructure/upgrade_trillium_master_for_tier1.sh`
- Interactive confirmation
- Automatic instance stop/modify/start
- Connection instructions

**Downgrade Script:**
- `scripts/infrastructure/downgrade_trillium_master_after_tier1.sh`
- TIER 1 completion verification
- Interactive confirmation
- Automatic instance stop/modify/start
- Cost savings summary

**Documentation:**
- This file: `docs/tier1_infrastructure_spot_failure_2025_11_17.md`

---

## NEXT ACTIONS

### Immediate

1. **Review upgrade plan** (this document)
2. **Execute upgrade script**
   ```bash
   bash scripts/infrastructure/upgrade_trillium_master_for_tier1.sh
   ```
3. **Reconnect to upgraded instance**
4. **Verify database connectivity**

### TIER 1 Execution

5. **Create log directories**
   ```bash
   mkdir -p /tmp/logs/tier1/stage_2_3
   mkdir -p /tmp/logs/tier1/stage_2_4
   mkdir -p /tmp/logs/tier1/stage_2_16b
   ```

6. **Execute Stage 2.3**
   ```bash
   nohup python3 scripts/tier1/stage_2_3_currency_indices.py > /tmp/logs/tier1/stage_2_3/execution.log 2>&1 &
   echo $! > /tmp/tier1_stage_2_3_pid.txt
   ```

7. **Monitor progress**
   ```bash
   tail -f /tmp/logs/tier1/stage_2_3/currency_indices.log
   ```

### Post-TIER 1

8. **Validate completion**
   ```bash
   python3 scripts/tier1/validate_tier1_complete.py
   ```

9. **Downgrade instance**
   ```bash
   bash scripts/infrastructure/downgrade_trillium_master_after_tier1.sh
   ```

10. **Document results**
    ```bash
    # Create TIER 1 completion report
    ```

---

## LESSONS LEARNED

### Spot Instance Quotas

- AWS accounts have hard limits on Spot instance count
- Limits may be regional or account-wide
- Quota API requires support plan to check programmatically
- Always have fallback option (On-Demand) for production workloads

### Infrastructure Planning

- Option A (Spot) and Option B (Upgrade) had identical costs
- Flexibility in approach critical when quotas are unknown
- Temporary instance upgrade is viable alternative to separate instances
- Document both approaches before execution

### Automation

- Created reusable upgrade/downgrade scripts
- Interactive confirmations prevent accidental modifications
- Clear cost impact and rollback procedures documented

---

**Status:** Ready to proceed with Option B
**Action Required:** Execute upgrade script
**Expected Duration:** 10 minutes (upgrade) + 55 hours (TIER 1) + 10 minutes (downgrade)
**Expected Cost:** ~$22
**Expected Outcome:** +384 features, Sharpe +10-17%

---

**Document Created:** 2025-11-17
**Author:** Claude Code
**Purpose:** Document Spot failure and Option B implementation plan
