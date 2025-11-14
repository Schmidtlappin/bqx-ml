# Temporary EC2 Implementation Guide - Quick Reference

**Date:** 2025-11-14
**Architecture:** Temporary EC2 for Phase 2
**Approved:** ✅ Yes

---

## Executive Summary

**What:** Spin up temporary c7i.8xlarge Spot instance for Phase 2, then terminate
**Why:** 87% lower ongoing costs, zero downtime, lower risk
**Cost:** $19.13 (Phase 2) + $15/month (trillium-master)
**Savings:** $2,775.93/year vs current setup

---

## Implementation Steps

### Step 1: Optional - Downgrade trillium-master (30 min)

**Saves:** $106/month ongoing

```bash
# Get instance ID
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d ' ' -f 2)

# Create snapshot
aws ec2 create-snapshot \
  --volume-id $(aws ec2 describe-instances --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].BlockDeviceMappings[0].Ebs.VolumeId' --output text) \
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

**Downtime:** 5 minutes
**Result:** trillium-master now costs $15/month (vs $243/month = 94% savings)

---

### Step 2: Launch Temporary Phase 2 Worker (15 min)

**Prerequisites:**
- Update security group ID in script
- Update subnet ID in script
- Ensure key pair exists

```bash
# Edit configuration
nano /home/ubuntu/bqx-ml/scripts/infrastructure/launch_temporary_phase2_ec2.sh
# Update: SECURITY_GROUP, SUBNET_ID

# Launch temporary worker
bash /home/ubuntu/bqx-ml/scripts/infrastructure/launch_temporary_phase2_ec2.sh
```

**Output:**
- Instance ID saved to `/tmp/phase2-worker-instance-id.txt`
- Public IP displayed
- Wait 3-5 minutes for initialization

---

### Step 3: Configure Temporary Worker (10 min)

```bash
# SSH to temporary worker (use IP from Step 2)
ssh -i ~/.ssh/trillium-key.pem ubuntu@<WORKER_IP>

# Wait for initialization to complete
tail -f /var/log/cloud-init-output.log
# Wait for "Cloud-init ... finished"

# Verify repository cloned
ls -l /home/ubuntu/bqx-ml

# Set Aurora password
export PGPASSWORD='BQX_Aurora_2025_Secure'
echo "export PGPASSWORD='BQX_Aurora_2025_Secure'" >> ~/.bashrc

# Test Aurora connectivity
PGPASSWORD=$PGPASSWORD psql \
  -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres -d bqx \
  -c "SELECT COUNT(*) FROM bqx.reg_rate_audcad;"

# Expected: Row count displayed
```

---

### Step 4: Run Phase 2 Stages (1.8 days)

```bash
# On temporary worker
cd /home/ubuntu/bqx-ml

# Create Stage 2.3 and 2.4 schemas
PGPASSWORD=$PGPASSWORD psql \
  -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres -d bqx \
  -f scripts/refactor/stage_2_3_create_currency_index_schema.sql

PGPASSWORD=$PGPASSWORD psql \
  -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres -d bqx \
  -f scripts/refactor/stage_2_4_create_arbitrage_schema.sql

# Launch Phase 2 stages (when worker scripts are ready)
# bash scripts/orchestration/launch_phase_2_post_track2.sh
```

**Monitoring (from trillium-master):**

```bash
# SSH to temporary worker
ssh ubuntu@<WORKER_IP>

# Monitor progress
htop  # Watch CPU usage (should be ~90-95%)
tail -f /tmp/logs/stage_2_*/populate.log
```

---

### Step 5: Terminate Temporary Worker (5 min)

**IMPORTANT:** Only run after Phase 2 is 100% complete!

**Checklist:**
- [ ] All Phase 2 stages complete
- [ ] S3 export validated (40-50 GB)
- [ ] All features in Aurora verified
- [ ] Worker logs archived (if needed)

```bash
# From trillium-master (or any machine with AWS CLI)
bash /home/ubuntu/bqx-ml/scripts/infrastructure/terminate_phase2_ec2.sh
```

**Confirmation:** Type `TERMINATE` to confirm

**Result:**
- Temporary worker terminated
- No ongoing charges ($0.00/month)
- trillium-master continues running

---

## Cost Summary

| Component | Duration | Cost |
|-----------|----------|------|
| **trillium-master downgrade** | One-time (30 min) | $0.00 |
| **trillium-phase2-worker** | 1.8 days (42.5 hrs) | $19.13 |
| **Total Phase 2** | 1.8 days | **$19.13** |
| **Ongoing (trillium-master)** | Monthly | **$15.15** |

**Annual Comparison:**

| Scenario | Phase 2 | Annual Ongoing | Total (1 Year) |
|----------|---------|----------------|----------------|
| **Current (t3.2xlarge)** | $60.86 | $2,916.00 | $2,976.86 |
| **In-Place Upgrade** | $19.13 | $1,454.40 | $1,473.53 |
| **Temporary EC2** | $19.13 | $181.80 | **$200.93** |

**Savings:** $2,775.93/year (93% reduction vs current)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      PHASE 2 ARCHITECTURE                    │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────┐          ┌──────────────────────┐
│  trillium-master     │          │ trillium-phase2-     │
│  (t3.small)          │          │ worker (c7i.8xlarge) │
│                      │          │                      │
│  Role: Monitoring    │          │  Role: Phase 2       │
│  Lifecycle: Permanent│          │  Lifecycle: 1.8 days │
│  Cost: $15/month     │          │  Cost: $19.13 total  │
└──────────┬───────────┘          └──────────┬───────────┘
           │                                 │
           │         ┌───────────────────────┤
           │         │                       │
           └─────────┴───────────────────────┘
                     │
           ┌─────────▼────────────┐
           │  Aurora PostgreSQL   │
           │  (Serverless v2)     │
           │                      │
           │  - All Phase 2 data  │
           │  - 672+ partitions   │
           │  - 0.5-32 ACU        │
           └──────────────────────┘
```

**Post-Phase 2:**

```
┌──────────────────────┐
│  trillium-master     │
│  (t3.small)          │
│                      │
│  Role: Monitoring    │          ┌──────────────────────┐
│  Lifecycle: Permanent│          │ trillium-phase2-     │
│  Cost: $15/month     │          │ worker               │
└──────────┬───────────┘          │                      │
           │                      │  Status: TERMINATED  │
           │                      │  Cost: $0/month      │
           │                      └──────────────────────┘
           │
           │
           │
           │
┌──────────▼────────────┐
│  Aurora PostgreSQL    │
│  + S3 (Parquet)       │
│                       │
│  Ready for Phase 3    │
│  (SageMaker)          │
└───────────────────────┘
```

---

## Troubleshooting

### Issue: Temporary worker launch fails

**Check:**
1. Security group allows SSH (port 22)
2. Subnet has internet gateway
3. Spot price not exceeded
4. Instance quota not reached

**Solution:**
```bash
# Check Spot price history
aws ec2 describe-spot-price-history \
  --instance-types c7i.8xlarge \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --product-descriptions "Linux/UNIX" \
  --query 'SpotPriceHistory[*].[Timestamp,SpotPrice]' \
  --output table

# If Spot too expensive, use On-Demand
# Edit launch script: Remove --instance-market-options
```

### Issue: Cannot SSH to temporary worker

**Check:**
1. Security group inbound rules (port 22)
2. Public IP assigned
3. Key pair correct

**Solution:**
```bash
# Check security group
aws ec2 describe-security-groups --group-ids <SG_ID>

# Check instance public IP
aws ec2 describe-instances --instance-ids <INSTANCE_ID> \
  --query 'Reservations[0].Instances[0].PublicIpAddress'

# Try SSH with verbose
ssh -v -i ~/.ssh/trillium-key.pem ubuntu@<WORKER_IP>
```

### Issue: Aurora connection timeout

**Check:**
1. Security group allows PostgreSQL (port 5432)
2. Aurora cluster accessible from EC2 subnet
3. Password correct

**Solution:**
```bash
# Test connectivity
telnet trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com 5432

# Check Aurora security group
# Ensure it allows inbound from temporary worker's security group
```

---

## Key Files

| File | Purpose |
|------|---------|
| [docs/architecture_decision_temporary_ec2.md](architecture_decision_temporary_ec2.md) | Full rationale and comparison |
| [docs/phase_2_ec2_cost_analysis.md](phase_2_ec2_cost_analysis.md) | Detailed cost analysis |
| [scripts/infrastructure/launch_temporary_phase2_ec2.sh](../scripts/infrastructure/launch_temporary_phase2_ec2.sh) | Launch temporary worker |
| [scripts/infrastructure/terminate_phase2_ec2.sh](../scripts/infrastructure/terminate_phase2_ec2.sh) | Terminate temporary worker |
| [scripts/airtable/add_phase_2_infrastructure_stage.py](../scripts/airtable/add_phase_2_infrastructure_stage.py) | AirTable Stage 2.10 update |

---

## Next Steps After Phase 2

1. ✅ Phase 2 complete (all features in Aurora + S3)
2. ✅ Temporary EC2 terminated ($0 ongoing cost)
3. ✅ trillium-master running (t3.small, $15/month)
4. ⏳ Begin Phase 3 (SageMaker setup)

**Phase 3 Architecture:**
- SageMaker for model training/inference
- Lambda for feature extraction
- API Gateway for predictions
- Aurora Serverless v2 (data storage)
- trillium-master (optional monitoring)

**Phase 3 Monthly Cost:** ~$527 (SageMaker $401 + Aurora $111 + EC2 $15)

---

**Last Updated:** 2025-11-14
**Status:** ✅ Ready for Implementation
**Approved:** User (2025-11-14)
