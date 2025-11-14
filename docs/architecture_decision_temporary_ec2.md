# Architecture Decision: Temporary EC2 for Phase 2

**Date:** 2025-11-14
**Decision:** Use independent temporary EC2 for Phase 2 instead of upgrading trillium-master
**Status:** Approved

---

## Decision Summary

**OLD APPROACH (In-Place Upgrade):**
- Upgrade trillium-master: t3.2xlarge → c7i.8xlarge
- Run Phase 2 on upgraded trillium-master
- Downgrade trillium-master: c7i.8xlarge → t3.xlarge
- trillium-master continues as monitoring instance

**NEW APPROACH (Temporary EC2):**
- Keep trillium-master running (downgrade to t3.small for cost optimization)
- Spin up NEW temporary EC2: c7i.8xlarge Spot
- Run Phase 2 on temporary EC2
- TERMINATE temporary EC2 after Phase 2 completes
- trillium-master continues as permanent monitoring/operations instance

---

## Rationale: Why Independent Temporary EC2?

### 1. **Separation of Concerns**

**Principle:** Separate permanent infrastructure from disposable compute workloads

| Aspect | trillium-master (Permanent) | Phase 2 Worker (Temporary) |
|--------|----------------------------|---------------------------|
| **Purpose** | Monitoring, maintenance, ad-hoc queries | Phase 2 batch processing ONLY |
| **Lifecycle** | Always-on, persistent | 1.8 days, then terminate |
| **State** | Stateful (logs, scripts, configs) | Stateless (all data in Aurora) |
| **Cost Model** | Ongoing operational expense | One-time project expense |
| **Risk Profile** | Production stability critical | Disposable, can fail/restart |

**Benefit:** Clear architectural boundaries between operational infrastructure and compute-intensive batch jobs.

---

### 2. **Zero-Downtime Operations**

**OLD APPROACH:**
- Stop trillium-master (5 min downtime)
- Upgrade instance type (5 min)
- Start trillium-master
- Run Phase 2
- Stop trillium-master (5 min downtime)
- Downgrade instance type (5 min)
- Start trillium-master
- **Total downtime: 10 minutes** (2 stop/start cycles)

**NEW APPROACH:**
- trillium-master NEVER stops
- Spin up temporary EC2 (independent)
- Run Phase 2 on temporary EC2
- Terminate temporary EC2
- **Total downtime: 0 minutes**

**Benefit:** No interruption to monitoring, ad-hoc queries, or other operational tasks.

---

### 3. **Cost Optimization**

#### Monthly Ongoing Costs Comparison

| Approach | Instance Type | Monthly Cost | Annual Cost |
|----------|--------------|--------------|-------------|
| **OLD: In-Place Upgrade** | t3.xlarge | $121.20 | $1,454.40 |
| **NEW: Temporary EC2** | t3.small | $15.15 | $181.80 |
| **Savings** | - | **$106.05/mo** | **$1,272.60/yr** |

#### Total Cost Analysis (Phase 2 + 1 Year)

| Approach | Phase 2 Cost | 1 Year Ongoing | Total (1 Year) |
|----------|--------------|----------------|----------------|
| **OLD: In-Place Upgrade** | $21.53 | $1,454.40 | $1,475.93 |
| **NEW: Temporary EC2** | $21.53 | $181.80 | $203.33 |
| **Savings** | $0.00 | $1,272.60 | **$1,272.60** |

**Benefit:** 87% reduction in ongoing infrastructure costs (t3.small vs t3.xlarge).

**Rationale:** Phase 3 uses SageMaker (serverless), so trillium-master only needs light compute for monitoring/maintenance.

---

### 4. **Risk Mitigation**

| Risk | In-Place Upgrade | Temporary EC2 | Mitigation Improvement |
|------|------------------|---------------|------------------------|
| **Upgrade fails** | trillium-master offline | trillium-master unaffected | ✅ Production unaffected |
| **Downgrade fails** | trillium-master offline | No downgrade needed | ✅ Eliminates risk |
| **Phase 2 worker crashes** | Restart on production instance | Restart/replace temp EC2 | ✅ Isolated failure domain |
| **Spot interruption** | Production affected | Only temp EC2 affected | ✅ Production unaffected |
| **Data corruption** | Affects production instance | Isolated to temp EC2 | ✅ Easy rollback (terminate) |
| **Need to rollback** | 2 instance type changes | Just terminate temp EC2 | ✅ Simpler rollback |

**Benefit:** Isolates all Phase 2 risks from production infrastructure.

---

### 5. **Operational Flexibility**

**NEW APPROACH enables:**

1. **Parallel Operations:**
   - Run Phase 2 on temp EC2
   - Simultaneously run validation/testing on trillium-master
   - No resource contention

2. **Independent Configuration:**
   - Temp EC2 optimized for Phase 2 (max workers, memory, swap)
   - trillium-master optimized for monitoring (lightweight)
   - Different AMIs/packages if needed

3. **Easier Debugging:**
   - Temp EC2 logs isolated from production
   - Can snapshot temp EC2 state independently
   - Can keep temp EC2 alive for debugging (if needed)

4. **Simpler Termination:**
   - No downgrade procedure (just terminate)
   - No risk of leaving instance in wrong state
   - Clean accounting (separate instance IDs)

**Benefit:** Greater flexibility for testing, debugging, and optimization.

---

### 6. **Infrastructure as Code Alignment**

**Temporary EC2 approach aligns with modern cloud best practices:**

- ✅ **Immutable Infrastructure:** Spin up clean instance, terminate when done
- ✅ **Ephemeral Compute:** Compute is temporary, data is persistent (Aurora)
- ✅ **Separation of State:** Stateful (trillium-master) vs stateless (temp worker)
- ✅ **Cost Attribution:** Clear project cost (temp EC2) vs operational cost (trillium-master)
- ✅ **Blast Radius:** Limit impact of failures to isolated compute

**Benefit:** Follows cloud-native patterns, easier to automate and scale.

---

## Architecture Comparison

### OLD: In-Place Upgrade Approach

```
trillium-master (t3.2xlarge)
    ↓ STOP (5 min downtime)
    ↓ UPGRADE to c7i.8xlarge
    ↓ START
    ↓
[Phase 2 Processing - 1.8 days]
    ↓
    ↓ STOP (5 min downtime)
    ↓ DOWNGRADE to t3.xlarge
    ↓ START
    ↓
trillium-master (t3.xlarge) - ongoing monitoring
    - Cost: $121/month
    - Downtime: 10 minutes total
```

### NEW: Temporary EC2 Approach

```
trillium-master (t3.2xlarge)
    ↓ OPTIONAL: Downgrade to t3.small (one-time, 5 min downtime)
    ↓
trillium-master (t3.small) - ongoing monitoring
    - Cost: $15/month
    - Downtime: 0 minutes (runs continuously)

PARALLEL:
    ↓
    Spin up NEW: trillium-phase2-worker (c7i.8xlarge Spot)
    ↓
    [Phase 2 Processing - 1.8 days]
    ↓
    TERMINATE trillium-phase2-worker
    ↓
    (temp EC2 cost: $19.13 one-time)
```

---

## Cost Breakdown

### Phase 2 Execution Cost

| Component | In-Place Upgrade | Temporary EC2 | Difference |
|-----------|------------------|---------------|------------|
| **c7i.8xlarge Spot** | 42.5 hrs @ $0.45/hr | 42.5 hrs @ $0.45/hr | $0.00 |
| **Total Phase 2** | $19.13 | $19.13 | **$0.00** |

**Note:** Phase 2 execution cost is IDENTICAL (same instance type, same duration).

### Ongoing Infrastructure Cost (Post-Phase 2)

| Component | In-Place Upgrade | Temporary EC2 | Difference |
|-----------|------------------|---------------|------------|
| **trillium-master** | t3.xlarge @ $0.1664/hr | t3.small @ $0.0208/hr | -87% |
| **Monthly** | $121.20 | $15.15 | **-$106.05** |
| **Annual** | $1,454.40 | $181.80 | **-$1,272.60** |

### Total Cost of Ownership (1 Year)

| Approach | Phase 2 | Year 1 Ongoing | Total | Savings |
|----------|---------|----------------|-------|---------|
| **In-Place Upgrade** | $19.13 | $1,454.40 | $1,473.53 | - |
| **Temporary EC2** | $19.13 | $181.80 | $200.93 | **$1,272.60** |

**ROI:** 86% cost reduction over 1 year

---

## Technical Requirements

### trillium-master (t3.small) - Permanent

**Specifications:**
- **Instance Type:** t3.small
- **vCPUs:** 2
- **Memory:** 2 GB
- **Cost:** $0.0208/hour ($15.15/month)
- **Lifecycle:** Always-on

**Role:**
- Monitoring Phase 2 progress (log tailing)
- Ad-hoc Aurora queries
- Script development/testing
- SageMaker experiment tracking (Phase 3)
- Cron jobs, alerting, backups

**Sufficient Because:**
- Phase 2 compute on separate instance (temp EC2)
- Phase 3 compute on SageMaker (serverless)
- trillium-master only needs light monitoring/admin tasks

### trillium-phase2-worker (c7i.8xlarge Spot) - Temporary

**Specifications:**
- **Instance Type:** c7i.8xlarge
- **vCPUs:** 32
- **Memory:** 64 GB
- **Cost:** $0.45/hour Spot (~$1.36/hour On-Demand)
- **Lifecycle:** 1.8 days, then TERMINATE

**Role:**
- Phase 2 parallel processing ONLY
- 32 workers across 32 vCPUs
- Heavy Aurora writes (Stage 2.2-2.9)
- S3 exports (Stage 2.7)

**Terminated After:**
- All Phase 2 stages complete
- S3 export validated
- Final database optimization run

---

## Implementation Plan

### Step 1: Downgrade trillium-master (Optional, One-Time)

**When:** Before spinning up temp EC2 (cost optimization)

```bash
# Get instance ID
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d ' ' -f 2)

# Create pre-downgrade snapshot
aws ec2 create-snapshot \
  --volume-id vol-xxxxxxxxx \
  --description "trillium-master pre-downgrade to t3.small"

# Stop instance
aws ec2 stop-instances --instance-ids $INSTANCE_ID
aws ec2 wait instance-stopped --instance-ids $INSTANCE_ID

# Downgrade to t3.small
aws ec2 modify-instance-attribute \
  --instance-id $INSTANCE_ID \
  --instance-type t3.small

# Start instance
aws ec2 start-instances --instance-ids $INSTANCE_ID
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Verify
ssh trillium-master "nproc && free -h"
# Expected: 2 vCPUs, 2 GB RAM
```

**Duration:** 30 minutes (5 min downtime)
**Savings:** $106/month ongoing

---

### Step 2: Spin Up Temporary Phase 2 Worker

**When:** Immediately after trillium-master downgrade (or keep current size)

```bash
# Launch Spot instance
aws ec2 run-instances \
  --image-id ami-xxxxxxxxx \
  --instance-type c7i.8xlarge \
  --key-name trillium-key \
  --security-group-ids sg-xxxxxxxxx \
  --subnet-id subnet-xxxxxxxxx \
  --instance-market-options 'MarketType=spot,SpotOptions={SpotInstanceType=one-time,MaxPrice=1.00}' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=trillium-phase2-worker},{Key=Phase,Value=2},{Key=Lifecycle,Value=temporary}]' \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":100,"VolumeType":"gp3"}}]' \
  --user-data file://phase2-worker-init.sh

# Get new instance ID
WORKER_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=trillium-phase2-worker" \
  --query 'Reservations[0].Instances[0].InstanceId' \
  --output text)

# Wait for running
aws ec2 wait instance-running --instance-ids $WORKER_ID

# Get public IP
WORKER_IP=$(aws ec2 describe-instances \
  --instance-ids $WORKER_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

# SSH to worker
ssh -i ~/.ssh/trillium-key.pem ubuntu@$WORKER_IP
```

**Duration:** 10 minutes
**Cost:** $0.00 (not yet running workloads)

---

### Step 3: Configure Temporary Worker

**On trillium-phase2-worker:**

```bash
# Clone repository
git clone https://github.com/Schmidtlappin/bqx-ml.git
cd bqx-ml

# Install dependencies
pip3 install -r requirements.txt

# Configure Aurora credentials (read-only from trillium-master)
export AURORA_HOST="trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com"
export AURORA_USER="postgres"
export AURORA_PASSWORD="BQX_Aurora_2025_Secure"
export AURORA_DB="bqx"

# Verify Aurora connectivity
PGPASSWORD=$AURORA_PASSWORD psql -h $AURORA_HOST -U $AURORA_USER -d $AURORA_DB -c "SELECT COUNT(*) FROM bqx.reg_rate_audcad;"

# Create log directories
mkdir -p /tmp/logs/{stage_2_2,stage_2_3,stage_2_4}
```

**Duration:** 15 minutes
**Cost:** $0.11 (15 min @ $0.45/hr)

---

### Step 4: Run Phase 2 Stages

**Execute Phase 2 parallel stages on temporary worker:**

```bash
# Launch all parallel stages
bash /home/ubuntu/bqx-ml/scripts/orchestration/launch_phase_2_post_track2.sh
```

**Duration:** 42.5 hours (1.8 days)
**Cost:** $19.13

---

### Step 5: Terminate Temporary Worker

**When:** Phase 2 100% complete, S3 export validated

```bash
# From trillium-master, verify Phase 2 completion
ssh trillium-phase2-worker "grep 'COMPLETE' /tmp/logs/stage_*/*.log"

# Create final snapshot (optional, for debugging)
aws ec2 create-snapshot \
  --volume-id vol-xxxxxxxxx \
  --description "trillium-phase2-worker final state - Phase 2 complete"

# TERMINATE instance (not stop - to avoid ongoing charges)
aws ec2 terminate-instances --instance-ids $WORKER_ID

# Verify termination
aws ec2 describe-instances --instance-ids $WORKER_ID \
  --query 'Reservations[0].Instances[0].State.Name'
# Expected: "terminated"
```

**Duration:** 5 minutes
**Ongoing Cost:** $0.00 (instance terminated)

---

## Comparison Matrix

| Criteria | In-Place Upgrade | Temporary EC2 | Winner |
|----------|------------------|---------------|--------|
| **Phase 2 Performance** | 32 vCPUs, 64 GB | 32 vCPUs, 64 GB | TIE |
| **Phase 2 Duration** | 1.8 days | 1.8 days | TIE |
| **Phase 2 Cost** | $19.13 | $19.13 | TIE |
| **Ongoing Cost (Monthly)** | $121.20 | $15.15 | ✅ **Temporary EC2** (-87%) |
| **Ongoing Cost (Annual)** | $1,454.40 | $181.80 | ✅ **Temporary EC2** (-87%) |
| **trillium-master Downtime** | 10 minutes | 0 minutes | ✅ **Temporary EC2** |
| **Production Risk** | Medium (2 type changes) | Low (isolated) | ✅ **Temporary EC2** |
| **Operational Complexity** | Medium (3 steps) | Medium (5 steps) | TIE |
| **Rollback Complexity** | High (reverse upgrade) | Low (just terminate) | ✅ **Temporary EC2** |
| **Infrastructure Separation** | No (shared instance) | Yes (dedicated worker) | ✅ **Temporary EC2** |
| **Cost Attribution** | Mixed (prod + batch) | Clear (separate instances) | ✅ **Temporary EC2** |

**Overall Winner:** ✅ **Temporary EC2** (7 wins vs 0 wins, 3 ties)

---

## Recommendation

**APPROVED: Use temporary EC2 approach**

**Rationale:**
1. **Identical Phase 2 performance** (same instance type, duration, cost)
2. **87% lower ongoing costs** ($15/mo vs $121/mo)
3. **Zero downtime** on trillium-master
4. **Lower risk** (isolated failure domain)
5. **Cleaner architecture** (separation of concerns)
6. **Easier rollback** (just terminate)

**Total Savings:** $1,272.60/year with no performance trade-offs

---

## Next Steps

1. ✅ Document architecture decision (this document)
2. ⏳ Refactor AirTable Stage 2.10 (Infrastructure Management)
3. ⏳ Update Phase 2 timeline with temporary EC2 approach
4. ⏳ Create temp EC2 launch script
5. ⏳ Create temp EC2 termination checklist
6. ⏳ Update cost analysis documentation
7. ⏳ Execute: Downgrade trillium-master to t3.small
8. ⏳ Execute: Spin up trillium-phase2-worker
9. ⏳ Execute: Run Phase 2 stages
10. ⏳ Execute: Terminate trillium-phase2-worker

---

**Decision Date:** 2025-11-14
**Approved By:** User
**Status:** ✅ Approved, Ready for Implementation
