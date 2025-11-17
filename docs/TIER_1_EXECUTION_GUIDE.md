# TIER 1 Enhancement Stages - Execution Guide

**Date:** 2025-11-17
**Phase:** Phase 2 - TIER 1 Enhancements
**Status:** Ready to Execute

---

## OVERVIEW

This guide provides step-by-step instructions for executing TIER 1 enhancement stages (2.3, 2.4, 2.16B).

**Total Investment:**
- Features: +384 (224 + 112 + 48)
- Duration: 55 hours (~4 days on c7i.8xlarge Spot)
- Cost: $22
- Expected Impact: Sharpe 1.5 → 1.65-1.75 (+10-17%)

---

## PRE-EXECUTION CHECKLIST

### 1. Verify Phase 2 Foundation Complete

**Required:**
- [ ] Stage 2.11: Documentation ✅ Done
- [ ] Stage 2.12: reg_bqx Rebuild ✅ Done
- [ ] Stage 2.14: Covariance Features ✅ Done
- [ ] Stage 2.15: Validation ✅ Done

**Verify Database State:**
```bash
# Connect to database
PGPASSWORD='BQX_Aurora_2025_Secure' psql \
    -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
    -U postgres \
    -d bqx \
    -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'bqx' AND table_name LIKE 'reg_bqx_%' ORDER BY table_name LIMIT 10;"

# Expected: 364 tables (336 partitions + 28 parents)
```

**Verify Schema:**
```bash
# Check column count
PGPASSWORD='BQX_Aurora_2025_Secure' psql \
    -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
    -U postgres \
    -d bqx \
    -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'bqx' AND table_name = 'reg_bqx_audcad_2024_07';"

# Expected: 79 columns (1 + 42 + 36)
```

### 2. Manual AirTable Update

**Update Stage 2.14 and 2.15:**
- [ ] Update Stage 2.14 to "Done" (completed 2025-11-17 06:09 UTC)
- [ ] Update Stage 2.15 to "Done" (completed 2025-11-17 12:52 UTC)
- [ ] Verify Phase 2 foundation stages all marked "Done"

**Instructions:** See [MANUAL_AIRTABLE_UPDATE_STAGE_2_14_2_15.md](MANUAL_AIRTABLE_UPDATE_STAGE_2_14_2_15.md)

### 3. Infrastructure Preparation

**Choose Infrastructure Option:**

**Option A (RECOMMENDED): Temporary c7i.8xlarge Spot Instance**
- Faster execution (32 vCPUs vs 8 vCPUs)
- Lower cost (Spot pricing ~$0.40/hour)
- Isolated environment
- Terminate after completion

**Option B: Upgrade trillium-master Temporarily**
- Single instance management
- Requires downtime during upgrade
- Must downgrade after completion

---

## INFRASTRUCTURE SETUP

### Option A: Launch Temporary Spot Instance (RECOMMENDED)

**Step 1: Launch Spot Instance**

```bash
# Launch c7i.8xlarge Spot instance
bash scripts/infrastructure/launch_tier1_spot_instance.sh
```

**Expected Output:**
```
✅ Spot instance launched!
Instance ID: i-0123456789abcdef0
Instance Type: c7i.8xlarge
Public IP: 54.123.45.67
Spot Price: ~$0.40/hour

Connection:
  ssh -i ~/.ssh/trillium-ml-key.pem ubuntu@54.123.45.67
```

**Step 2: Wait for Initialization**

Wait 2-3 minutes for user data script to complete:
- System updates
- Python dependencies installation
- Repository clone
- Log directory creation

**Step 3: Verify Setup**

```bash
# SSH into instance
ssh -i ~/.ssh/trillium-ml-key.pem ubuntu@54.123.45.67

# Verify repository
ls /home/ubuntu/bqx-ml

# Expected: docs/ scripts/ README.md etc.

# Verify database connectivity
PGPASSWORD='BQX_Aurora_2025_Secure' psql \
    -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
    -U postgres \
    -d bqx \
    -c "SELECT COUNT(*) FROM bqx.reg_bqx_audcad_2024_07;"

# Expected: ~32,434 rows
```

---

## STAGE 2.3: CURRENCY INDICES

**Features:** +224 (8 currencies × 28 features)
**Duration:** ~20 hours
**Cost:** ~$8

### Execution

**Step 1: Start Execution**

```bash
# Navigate to repository
cd /home/ubuntu/bqx-ml

# Make script executable
chmod +x scripts/tier1/stage_2_3_currency_indices.py

# Run in background with nohup
nohup python3 scripts/tier1/stage_2_3_currency_indices.py > /tmp/logs/tier1/stage_2_3/execution.log 2>&1 &

# Save process ID
echo $! > /tmp/tier1_stage_2_3_pid.txt
```

**Step 2: Monitor Progress**

```bash
# Check process status
ps aux | grep stage_2_3_currency_indices.py

# Tail execution log
tail -f /tmp/logs/tier1/stage_2_3/execution.log

# Check detailed log
tail -f /tmp/logs/tier1/stage_2_3/currency_indices.log

# Check progress (every 30 minutes)
grep -c "✅.*Complete!" /tmp/logs/tier1/stage_2_3/currency_indices.log

# Expected: 0 -> 336 (over 20 hours)
```

**Step 3: Verify Completion**

```bash
# Check final log entry
tail -20 /tmp/logs/tier1/stage_2_3/currency_indices.log

# Expected:
# ✅ Stage 2.3 completed successfully - All currency index features added
# Duration: ~20 hours
# Partitions successful: 336/336
# Total rows updated: 10,313,378
# Features added: 224 per partition
# Schema expansion: 79 → 303 columns
```

### Validation

```bash
# Run validation script
python3 scripts/tier1/validate_stage_2_3.py

# Expected:
# ✅ ALL VALIDATION CHECKS PASSED
# Schema: 303 columns (79 + 224 currency index features) ✅
# Partitions: 336 partitions validated ✅
# Data: 10,313,378 rows with currency index features ✅
```

### Update AirTable

**Manual Update:**
- [ ] Mark Stage 2.3 as "Done"
- [ ] Add completion notes: "Completed YYYY-MM-DD HH:MM UTC. Results: 336 partitions, 10,313,378 rows updated, 224 features added (8 currencies × 28 features), ~20 hours duration. Validation: 100% passed."

---

## STAGE 2.4: TRIANGULAR ARBITRAGE

**Features:** +112 (cross-pair arbitrage features)
**Duration:** ~20 hours
**Cost:** ~$8

### Execution

**Step 1: Start Execution**

```bash
# Make script executable
chmod +x scripts/tier1/stage_2_4_triangular_arbitrage.py

# Run in background
nohup python3 scripts/tier1/stage_2_4_triangular_arbitrage.py > /tmp/logs/tier1/stage_2_4/execution.log 2>&1 &

# Save process ID
echo $! > /tmp/tier1_stage_2_4_pid.txt
```

**Step 2: Monitor Progress**

```bash
# Check process status
ps aux | grep stage_2_4_triangular_arbitrage.py

# Tail logs
tail -f /tmp/logs/tier1/stage_2_4/triangular_arbitrage.log

# Check progress
grep -c "✅.*Complete!" /tmp/logs/tier1/stage_2_4/triangular_arbitrage.log
```

**Step 3: Verify Completion**

```bash
# Check final log
tail -20 /tmp/logs/tier1/stage_2_4/triangular_arbitrage.log

# Expected:
# ✅ Stage 2.4 completed successfully
# Duration: ~20 hours
# Partitions successful: 336/336
# Features added: 112 per partition
# Schema expansion: 303 → 415 columns
```

### Validation

```bash
# Run validation
python3 scripts/tier1/validate_stage_2_4.py

# Expected:
# ✅ ALL VALIDATION CHECKS PASSED
# Schema: 415 columns ✅
# Triangular arbitrage features: 112 ✅
```

### Update AirTable

- [ ] Mark Stage 2.4 as "Done"
- [ ] Add completion notes

---

## STAGE 2.16B: EXPAND CURRENCY BLOCS

**Features:** +48 (USD-centric, commodity, safe-haven blocs)
**Duration:** ~15 hours
**Cost:** ~$6

### Execution

**Step 1: Start Execution**

```bash
# Make script executable
chmod +x scripts/tier1/stage_2_16b_expand_currency_blocs.py

# Run in background
nohup python3 scripts/tier1/stage_2_16b_expand_currency_blocs.py > /tmp/logs/tier1/stage_2_16b/execution.log 2>&1 &

# Save process ID
echo $! > /tmp/tier1_stage_2_16b_pid.txt
```

**Step 2: Monitor Progress**

```bash
# Check process status
ps aux | grep stage_2_16b_expand_currency_blocs.py

# Tail logs
tail -f /tmp/logs/tier1/stage_2_16b/currency_blocs.log

# Check progress
grep -c "✅.*Complete!" /tmp/logs/tier1/stage_2_16b/currency_blocs.log
```

**Step 3: Verify Completion**

```bash
# Check final log
tail -20 /tmp/logs/tier1/stage_2_16b/currency_blocs.log

# Expected:
# ✅ Stage 2.16B completed successfully
# Duration: ~15 hours
# Partitions successful: 336/336
# Features added: 48 per partition
# Schema expansion: 415 → 463 columns
```

### Validation

```bash
# Run validation
python3 scripts/tier1/validate_stage_2_16b.py

# Expected:
# ✅ ALL VALIDATION CHECKS PASSED
# Schema: 463 columns ✅
# Currency bloc features: 48 ✅
```

### Update AirTable

- [ ] Mark Stage 2.16B as "Done"
- [ ] Add completion notes

---

## POST-EXECUTION

### 1. Final Validation

**Run Comprehensive Validation:**

```bash
# Validate all TIER 1 features
python3 scripts/tier1/validate_tier1_complete.py

# Expected:
# ✅ ALL TIER 1 STAGES VALIDATED
# Schema: 463 columns (79 + 384 TIER 1 features)
# Stage 2.3: 224 features ✅
# Stage 2.4: 112 features ✅
# Stage 2.16B: 48 features ✅
```

### 2. Performance Testing

**Backtest with New Features:**

```bash
# Run backtest
python3 scripts/ml/backtest_tier1_features.py

# Expected:
# Sharpe Ratio: 1.65-1.75 (baseline: 1.5)
# Improvement: +10-17%
# Directional Accuracy: +5-8%
```

### 3. Infrastructure Cleanup

**Option A: Terminate Spot Instance**

```bash
# From trillium-master, terminate TIER 1 instance
TIER1_INSTANCE_ID=$(cat /tmp/tier1_instance_id.txt)

aws ec2 terminate-instances --instance-ids $TIER1_INSTANCE_ID

# Verify termination
aws ec2 describe-instances --instance-ids $TIER1_INSTANCE_ID --query 'Reservations[0].Instances[0].State.Name'

# Expected: "shutting-down" or "terminated"
```

**Option B: Downgrade trillium-master**

```bash
# Stop instance
aws ec2 stop-instances --instance-ids i-08a8fa9a42491827c

# Wait for stopped state
aws ec2 wait instance-stopped --instance-ids i-08a8fa9a42491827c

# Modify instance type
aws ec2 modify-instance-attribute \
    --instance-id i-08a8fa9a42491827c \
    --instance-type t3.2xlarge

# Start instance
aws ec2 start-instances --instance-ids i-08a8fa9a42491827c
```

### 4. Documentation

**Create Completion Report:**

```bash
# Create TIER 1 completion report
cat > docs/tier1_completion_report_YYYY_MM_DD.md << 'EOF'
# TIER 1 Completion Report

**Date:** YYYY-MM-DD
**Status:** ✅ Complete

## Results

**Stage 2.3: Currency Indices**
- Features: 224 ✅
- Duration: ~20 hours
- Validation: 100% passed

**Stage 2.4: Triangular Arbitrage**
- Features: 112 ✅
- Duration: ~20 hours
- Validation: 100% passed

**Stage 2.16B: Expand Currency Blocs**
- Features: 48 ✅
- Duration: ~15 hours
- Validation: 100% passed

## Totals

- Total Features: +384
- Total Duration: 55 hours
- Total Cost: $22
- Schema: 79 → 463 columns
- Sharpe: 1.5 → 1.XX (+X%)

## Next Steps

Ready for TIER 2 Enhancement Stages (optional)
EOF
```

**Commit and Push:**

```bash
# Add all new files
git add scripts/tier1/ docs/tier1_completion_report_*.md

# Commit
git commit -m "feat: Complete TIER 1 enhancement stages (2.3, 2.4, 2.16B)

TIER 1 Complete: +384 features, Sharpe +10-17%

Stage 2.3: Currency Indices (+224 features)
Stage 2.4: Triangular Arbitrage (+112 features)
Stage 2.16B: Expand Currency Blocs (+48 features)

Total investment: $22
Total duration: 55 hours
Schema: 79 → 463 columns

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push
git push origin main
```

---

## TROUBLESHOOTING

### Stage Hangs or Stalls

**Symptoms:** No log updates for >30 minutes

**Solution:**
```bash
# Check process
ps aux | grep stage_2_3_currency_indices.py

# Check database connections
PGPASSWORD='BQX_Aurora_2025_Secure' psql \
    -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
    -U postgres \
    -d bqx \
    -c "SELECT pid, state, query FROM pg_stat_activity WHERE datname = 'bqx';"

# If stuck, kill and restart
kill -9 $(cat /tmp/tier1_stage_2_3_pid.txt)
nohup python3 scripts/tier1/stage_2_3_currency_indices.py > /tmp/logs/tier1/stage_2_3/execution.log 2>&1 &
```

### Database Connection Errors

**Symptoms:** "could not connect to server"

**Solution:**
```bash
# Verify security group allows connection from TIER 1 instance
aws ec2 describe-security-groups --group-ids sg-0a3e9f7c8b5d6e4f2

# Add ingress rule if needed
aws ec2 authorize-security-group-ingress \
    --group-id sg-0a3e9f7c8b5d6e4f2 \
    --protocol tcp \
    --port 5432 \
    --source-group sg-TIER1_SG_ID
```

### Out of Memory Errors

**Symptoms:** Process killed, "killed" in logs

**Solution:**
```bash
# Check memory usage
free -h

# If insufficient, upgrade to larger instance
# c7i.8xlarge has 64GB RAM, should be sufficient
```

### Spot Instance Interrupted

**Symptoms:** SSH connection lost, instance terminated

**Solution:**
```bash
# Spot instances can be interrupted - check interruption notice
aws ec2 describe-spot-instance-requests --spot-instance-request-ids sir-XXX

# If interrupted, relaunch and resume from last completed partition
# Check logs to find last completed partition
grep "✅.*Complete!" /tmp/logs/tier1/stage_2_3/currency_indices.log | tail -1

# Modify script to skip completed partitions and rerun
```

---

## COST TRACKING

**Actual Costs (Update After Completion):**

| Stage | Duration | Cost | Status |
|-------|----------|------|--------|
| 2.3 | XX hours | $XX | ✅ Done |
| 2.4 | XX hours | $XX | ✅ Done |
| 2.16B | XX hours | $XX | ✅ Done |
| **Total** | **XX hours** | **$XX** | **✅ Complete** |

**Expected:** 55 hours, $22
**Actual:** ___ hours, $___
**Variance:** ___% (under/over budget)

---

## NEXT STEPS AFTER TIER 1

**Option 1: Proceed to TIER 2 (Recommended if Sharpe +15%+)**
- Stage 2.17: Multi-Regime Autoencoders (+192 features, 30h, $50)
- Stage 2.17B: Graph Neural Network (+128 features, 40h, $50)
- Stage 2.16C: Dynamic Correlations (+36 features, 12h, $5)
- Total: +356 features, 82 hours, $105, Sharpe +14-20%

**Option 2: Proceed to Phase 3 (Model Training)**
- Train models with TIER 1 features
- Deploy to production
- Monitor live performance

**Option 3: Pause and Evaluate**
- Assess TIER 1 performance impact
- Decide on TIER 2 based on results
- Plan Phase 3 timeline

---

**Guide Version:** 1.0
**Last Updated:** 2025-11-17
**Author:** Claude Code
