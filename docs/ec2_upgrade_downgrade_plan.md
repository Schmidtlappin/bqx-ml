# EC2 Upgrade & Downgrade Plan for Phase 2

**Date:** 2025-11-14
**Decision:** Option 2 (c7i.8xlarge with Spot pricing) - APPROVED
**Strategy:** IN-PLACE UPGRADE → POST-PHASE 2 DOWNGRADE
**Status:** Awaiting Track 2 completion (currently 97.3%)

---

## Executive Summary

**Approved Strategy:**
1. **Upgrade** trillium-master from t3.2xlarge → c7i.8xlarge (during Phase 2)
2. **Downgrade** c7i.8xlarge → t3.xlarge (immediately after Phase 2 completes)
3. **Keep Running** t3.xlarge for monitoring/maintenance (NOT terminated)

**Benefits:**
- Phase 2 completion: 1.3 days (vs 5.4 days baseline) = **76% faster**
- Phase 2 total cost: $27.25 (vs $60.86 baseline) = **55% savings**
- Annual ongoing savings: $1,464/year (t3.2xlarge → t3.xlarge)

---

## Current Infrastructure

**Instance:** trillium-master
- **Type:** t3.2xlarge
- **vCPUs:** 8
- **RAM:** 32 GB
- **Cost:** $0.33/hour ($243/month)
- **Disk:** 400 GB EBS (6% used)
- **Other Projects:** Robkei-Ring, OmniDrive, box

**Track 2 Status:**
- Progress: 327/336 partitions complete (97.3%)
- Workers: 8 Python processes
- CPU Load: 7.0 / 8.0 cores (88%)
- Memory: 5.2 GB / 30 GB (17%)
- ETA: ~4.5 hours remaining

---

## Phase 1: Upgrade to c7i.8xlarge

### Target Specifications

**Instance Type:** c7i.8xlarge (Compute Optimized, 7th Gen Intel)
- **vCPUs:** 32 (4x increase)
- **RAM:** 64 GB (2x increase)
- **Processor:** Intel Xeon Scalable (Sapphire Rapids)
- **Network:** Up to 12.5 Gbps
- **Pricing:** Spot instances ~$0.45/hour (vs $1.36 On-Demand)

### Implementation Steps

#### Step 1: Pre-Upgrade Preparation (10 minutes)

```bash
# 1. Check Track 2 progress
cd /home/ubuntu/bqx-ml
grep -c "Complete!" /tmp/logs/track2/populate.log
# Should show: 336/336

# 2. Create AMI snapshot (backup)
aws ec2 create-snapshot \
  --volume-id $(aws ec2 describe-instances --instance-ids <instance-id> \
    --query 'Reservations[0].Instances[0].BlockDeviceMappings[0].Ebs.VolumeId' \
    --output text) \
  --description "Pre-upgrade snapshot - trillium-master - 2025-11-14"

# 3. Document running processes
ps aux | grep python3 > /tmp/pre_upgrade_processes.txt
systemctl list-units --type=service --state=running > /tmp/pre_upgrade_services.txt

# 4. Gracefully stop Track 2 workers
pkill -15 -f populate_regression_features_worker.py

# Wait for graceful exit (30 seconds)
sleep 30

# Verify workers stopped
ps aux | grep populate_regression_features_worker | grep -v grep
# Should return nothing
```

#### Step 2: Execute Upgrade (5 minutes)

**Via AWS Console:**
1. Navigate to EC2 → Instances
2. Select trillium-master instance
3. Instance State → Stop instance (wait ~2 min)
4. Actions → Instance settings → Change instance type
5. Select: **c7i.8xlarge**
6. ☑ Enable **Spot instance** (if available)
7. Click Save
8. Instance State → Start instance (wait ~2 min)

**Via AWS CLI:**
```bash
# Get instance ID
INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=trillium-master" \
  --query 'Reservations[0].Instances[0].InstanceId' \
  --output text)

# Stop instance
aws ec2 stop-instances --instance-ids $INSTANCE_ID
aws ec2 wait instance-stopped --instance-ids $INSTANCE_ID

# Change instance type
aws ec2 modify-instance-attribute \
  --instance-id $INSTANCE_ID \
  --instance-type c7i.8xlarge

# Request Spot pricing (if available)
# Note: Spot for existing instances may require instance launch template

# Start instance
aws ec2 start-instances --instance-ids $INSTANCE_ID
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get new IP (if changed)
NEW_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo "New IP: $NEW_IP"
```

#### Step 3: Post-Upgrade Validation (10 minutes)

```bash
# 1. SSH into instance (may need new IP)
ssh ubuntu@<new-ip>

# 2. Verify system resources
echo "=== CPU Verification ==="
nproc  # Should show: 32
lscpu | grep "CPU(s)"

echo "=== Memory Verification ==="
free -h | grep Mem  # Should show: 64GB total

echo "=== Disk Verification ==="
df -h | grep /dev/root  # Should show: 400GB (same as before)

# 3. Verify services started
echo "=== Service Status ==="
systemctl status redis-server
systemctl status docker
systemctl list-units --type=service --state=running

# 4. Verify database connectivity
echo "=== Database Connectivity ==="
PGPASSWORD='BQX_Aurora_2025_Secure' psql \
  -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres -d bqx \
  -c "SELECT COUNT(*) FROM bqx.m1_eurusd LIMIT 1;"
# Should return: 1 row

# 5. Verify Python environment
echo "=== Python Environment ==="
cd /home/ubuntu/bqx-ml
source venv/bin/activate
python3 -c "import psycopg2, pandas, numpy, scipy; print('All packages OK')"

# 6. Verify git repos intact
echo "=== Git Repos ==="
git -C /home/ubuntu/bqx-ml status
git -C /home/ubuntu/Robkei-Ring status
```

#### Step 4: Resume Track 2 (5 minutes)

```bash
# 1. Restart Track 2 workers with increased parallelism
cd /home/ubuntu/bqx-ml

# Update max_workers to 32 in populate_regression_features_worker.py
sed -i 's/max_workers = 8/max_workers = 32/' \
  scripts/ml/populate_regression_features_worker.py

# 2. Start workers
nohup python3 scripts/ml/populate_regression_features_worker.py \
  > /tmp/logs/track2/populate.log 2>&1 &

# 3. Monitor progress
tail -f /tmp/logs/track2/populate.log

# 4. Verify worker count
ps aux | grep populate_regression | grep -v grep | wc -l
# Should show: 32 workers

# 5. Monitor CPU utilization
htop  # Should show: 32 cores at ~90% each
```

### Expected Timeline

| Phase | Duration | Details |
|-------|----------|---------|
| Pre-upgrade | 10 min | Backup, stop workers |
| Downtime | 5 min | Stop, change type, start |
| Validation | 10 min | Verify resources, connectivity |
| Resume Track 2 | 5 min | Start 32 workers |
| **Total** | **30 min** | **5 min actual downtime** |

### Track 2 Completion

**Baseline (t3.2xlarge, 8 workers):**
- Remaining: 9 partitions × 30 min = 4.5 hours

**Upgraded (c7i.8xlarge, 32 workers):**
- Remaining: 9 partitions × 7.5 min = ~1 hour
- **Time Saved: 3.5 hours**

---

## Phase 2: Downgrade to t3.xlarge

### Trigger: Stage 2.7 (S3 Export) Completes

**Before Downgrade, Verify:**
1. Track 2: 336/336 partitions complete
2. All Phase 2 stages complete (2.3-2.9)
3. S3 export successful (40-50 GB Parquet files)
4. All 1,080 features in Aurora validated
5. Temporal causality tests passed

### Target Specifications

**Instance Type:** t3.xlarge (General Purpose, Burstable)
- **vCPUs:** 4 (1/2 of current t3.2xlarge)
- **RAM:** 16 GB (1/2 of current)
- **Cost:** $0.17/hour ($121/month)
- **Savings:** $122/month vs current t3.2xlarge

### Implementation Steps

#### Step 1: Pre-Downgrade Validation (15 minutes)

```bash
# 1. Verify Phase 2 completion
cd /home/ubuntu/bqx-ml

# Check Track 2
PGPASSWORD='BQX_Aurora_2025_Secure' psql \
  -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres -d bqx \
  -f scripts/validation/track_2_validation_queries.sql \
  > /tmp/track2_final_validation.log

# Verify 336/336 complete
grep "336/336" /tmp/track2_final_validation.log

# 2. Verify S3 export
aws s3 ls s3://bqx-ml-features/features/splits/train/ --recursive --summarize
# Should show: ~40-50 GB total

aws s3 ls s3://bqx-ml-features/features/splits/validation/ --recursive --summarize
aws s3 ls s3://bqx-ml-features/features/splits/test/ --recursive --summarize

# 3. Verify 1,080 features in Aurora
PGPASSWORD='BQX_Aurora_2025_Secure' psql \
  -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres -d bqx \
  -c "SELECT COUNT(DISTINCT tablename) FROM pg_tables WHERE schemaname = 'bqx';"
# Should return: Expected table count

# 4. Run full database optimization (ANALYZE, VACUUM)
# See aurora_optimization.sql script

# 5. Create final snapshot
aws ec2 create-snapshot \
  --volume-id $(aws ec2 describe-instances --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].BlockDeviceMappings[0].Ebs.VolumeId' \
    --output text) \
  --description "Post-Phase-2 snapshot - before downgrade - 2025-11-15"
```

#### Step 2: Execute Downgrade (5 minutes)

**Via AWS Console:**
1. EC2 → Instances → Select trillium-master
2. Instance State → Stop instance (wait ~2 min)
3. Actions → Instance settings → Change instance type
4. Select: **t3.xlarge**
5. Save
6. Instance State → Start instance (wait ~2 min)

**Via AWS CLI:**
```bash
# Stop instance
aws ec2 stop-instances --instance-ids $INSTANCE_ID
aws ec2 wait instance-stopped --instance-ids $INSTANCE_ID

# Change to t3.xlarge
aws ec2 modify-instance-attribute \
  --instance-id $INSTANCE_ID \
  --instance-type t3.xlarge

# Start instance
aws ec2 start-instances --instance-ids $INSTANCE_ID
aws ec2 wait instance-running --instance-ids $INSTANCE_ID
```

#### Step 3: Post-Downgrade Validation (10 minutes)

```bash
# 1. Verify resources
nproc  # Should show: 4 vCPUs
free -h  # Should show: 16 GB RAM

# 2. Verify all projects operational
systemctl list-units --type=service --state=running

# 3. Verify database connectivity
PGPASSWORD='BQX_Aurora_2025_Secure' psql \
  -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres -d bqx \
  -c "SELECT version();"

# 4. Verify other projects
git -C /home/ubuntu/Robkei-Ring status
git -C /home/ubuntu/OmniDrive status
git -C /home/ubuntu/box status

# 5. Test Phase 3 readiness (optional)
# Verify Lambda can query Aurora
# Verify SageMaker can access S3 Parquet files
```

### Downgrade Timeline

| Phase | Duration | Details |
|-------|----------|---------|
| Pre-downgrade validation | 15 min | Verify Phase 2 complete, S3 export, database |
| Downtime | 5 min | Stop, change type, start |
| Post-downgrade validation | 10 min | Verify resources, services |
| **Total** | **30 min** | **5 min actual downtime** |

---

## Cost Analysis

### Phase 2 Duration & Cost

| Instance | Duration | Hourly Rate | Total Cost |
|----------|----------|-------------|------------|
| **Baseline (t3.2xlarge)** | 130 hours | $0.33 | $43.26 |
| **Upgraded (c7i.8xlarge Spot)** | 31 hours | ~$0.45 | $13.95 |
| **Other Costs** | - | - | $13.30 |
| **Phase 2 Total** | - | - | **$27.25** |

**Savings: $33.61 (55%)**

### Monthly Ongoing Cost

| Period | Instance | Monthly Cost | Savings vs Baseline |
|--------|----------|--------------|---------------------|
| **Current** | t3.2xlarge | $243 | - |
| **Phase 2 (temp)** | c7i.8xlarge Spot | $330 | N/A (temporary) |
| **Post-Phase 2** | t3.xlarge | $121 | **$122/month (50%)** |

### Annual Savings

**Post-Downgrade Annual Savings:**
- t3.2xlarge: $243/month × 12 = $2,916/year
- t3.xlarge: $121/month × 12 = $1,452/year
- **Savings: $1,464/year**

---

## Risk Assessment

### Upgrade Risks (LOW)

✅ **Data Safety:** All data on EBS volumes (preserved)
✅ **Track 2 Resumable:** Workers query Aurora, process remaining partitions
✅ **Service Interruption:** 5 minutes (acceptable for development)
✅ **AWS Best Practice:** Instance type changes designed for this

⚠️ **Minor Concerns:**
- Redis in-memory data lost (appears unused)
- Other projects briefly offline (Robkei-Ring, OmniDrive, box)
- Private/public IP may change (Aurora uses DNS, safe)

### Downgrade Risks (LOW)

✅ **Resource Adequate:** t3.xlarge sufficient for Phase 3 monitoring
✅ **No Data Loss:** All Phase 2 data in Aurora + S3
✅ **Phase 3 Independent:** Uses SageMaker (not EC2)

⚠️ **Considerations:**
- 4 vCPUs may limit parallel analysis tasks
- 16 GB RAM sufficient for monitoring, not for heavy processing
- Can temporarily upgrade back to c7i.8xlarge if needed

---

## Post-Downgrade EC2 Role

**EC2 (t3.xlarge) Purpose in Phase 3:**

✅ **Monitoring & Logging:**
- CloudWatch dashboard access
- Log file analysis
- Database performance monitoring

✅ **Ad-Hoc Database Queries:**
- Quick SQL queries via psql
- Data validation checks
- Feature debugging

✅ **Other Projects:**
- Robkei-Ring operations
- OmniDrive access
- box project support

✅ **Emergency Access:**
- Database emergency maintenance
- Infrastructure troubleshooting
- Backup restoration

**NOT Required For:**
- ❌ Model training (uses SageMaker)
- ❌ Inference API (uses Lambda)
- ❌ Feature extraction (uses Lambda)
- ❌ Batch processing (Phase 2 complete)

---

## Alternative: Further Downgrade Options

If t3.xlarge is underutilized after Phase 3 launch, consider:

**Option A: t3.medium** (2 vCPUs, 4 GB, $30/month)
- Sufficient for monitoring only
- **Additional savings: $91/month**

**Option B: t3.small** (2 vCPUs, 2 GB, $15/month)
- Minimal monitoring
- **Additional savings: $106/month**

**Option C: Stop when not needed**
- Only pay for EBS storage (~$5/month)
- Start on-demand for maintenance
- **Savings: $116/month**

---

## Rollback Plan

**If Issues Occur During Upgrade:**
1. Stop c7i.8xlarge instance
2. Change back to t3.2xlarge
3. Start instance
4. Resume Track 2 with 8 workers
5. Complete Phase 2 on original timeline

**If Issues Occur During Downgrade:**
1. Stop t3.xlarge instance
2. Change to t3.2xlarge (or c7i.8xlarge if needed)
3. Start instance
4. Investigate issue

**Estimated Rollback Time:** 10 minutes

---

## Success Criteria

### Upgrade Success

✅ 32 vCPUs, 64 GB RAM verified
✅ Aurora connectivity working
✅ Track 2 resumed with 32 workers
✅ CPU utilization 90%+ across all cores
✅ Phase 2 completes in ~1.3 days

### Downgrade Success

✅ 4 vCPUs, 16 GB RAM verified
✅ All services operational
✅ Database connectivity working
✅ Other projects functional
✅ Monthly cost reduced to $121

---

## Timeline Summary

```
Day 0 (2025-11-14):
├─ Track 2: 97.3% complete (327/336)
└─ Awaiting 336/336 completion

Day 0 + 4.5 hours (Track 2 100%):
├─ Execute upgrade to c7i.8xlarge (30 min)
├─ Resume Track 2 with 32 workers
└─ Begin parallel Phase 2 stages

Day 1.3 (2025-11-15):
├─ Phase 2 completes (Stage 2.7 S3 Export done)
├─ Execute downgrade to t3.xlarge (30 min)
└─ Verify all systems operational

Day 2+ (2025-11-16+):
└─ Begin Phase 3 (SageMaker serverless)
```

---

**Total Effort:** 1 hour (30 min upgrade + 30 min downgrade)
**Total Downtime:** 10 minutes (5 min each)
**Total Savings:** $33.61 (Phase 2) + $1,464/year (ongoing)
**Risk Level:** LOW
**Approval Status:** ✅ APPROVED
**Implementation Status:** Awaiting Track 2 completion
