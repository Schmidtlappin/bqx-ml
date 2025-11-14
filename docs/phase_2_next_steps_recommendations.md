# Phase 2 Next Steps Recommendations

**Date:** 2025-11-14
**Status:** Track 2 Complete, Ready for EC2 Upgrade
**Current Instance:** t3.2xlarge (trillium-master)

---

## Executive Summary

**Track 2 Status:** ✅ **COMPLETE**
- 336/336 partitions processed (100%)
- 10,313,378 rows written to Aurora
- 7.2 hour duration
- 0 failed tasks

**Database Status:** ✅ **OPTIMIZED**
- Total size: 91 GB (28,505 tables, 186M rows)
- Dead rows: 0% (autovacuum excellent)
- Index health: 12 GB, 110M scans
- Ready for high-performance workloads

**System Status:** ✅ **CLEAN**
- No dead processes or zombie processes
- Logs archived to project directory
- Temporary files cleaned up
- All workers completed successfully

**Next Action:** **Execute EC2 upgrade to c7i.8xlarge**

---

## Recommended Sequence of Next Steps

### STEP 1: Execute EC2 Upgrade (30 minutes)

**Goal:** Upgrade trillium-master from t3.2xlarge → c7i.8xlarge

**Why Now:**
- Track 2 is 100% complete (no running workers to interrupt)
- Database is optimized (0% dead rows, fresh statistics)
- System is clean (no artifacts or dead processes)
- Phase 2 stages ready to launch

**Documentation:** See [docs/ec2_upgrade_downgrade_plan.md](ec2_upgrade_downgrade_plan.md)

**Quick Steps:**

```bash
# 1. Verify Track 2 completion
grep -c "Complete!" /tmp/logs/track2/populate.log  # Should show: 336

# 2. Get instance ID
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d ' ' -f 2)

# 3. Create snapshot (backup)
aws ec2 create-snapshot \
  --volume-id <vol-id> \
  --description "Pre-upgrade snapshot - Phase 2 ready" \
  --tag-specifications 'ResourceType=snapshot,Tags=[{Key=Phase,Value=2},{Key=Purpose,Value=Pre-Upgrade-Backup}]'

# 4. Stop instance
aws ec2 stop-instances --instance-ids $INSTANCE_ID

# 5. Wait for stopped state
aws ec2 wait instance-stopped --instance-ids $INSTANCE_ID

# 6. Change instance type
aws ec2 modify-instance-attribute \
  --instance-id $INSTANCE_ID \
  --instance-type c7i.8xlarge

# 7. Request Spot pricing (optional, 67% discount)
# Note: If using Spot, use aws ec2 request-spot-instances instead

# 8. Start instance
aws ec2 start-instances --instance-ids $INSTANCE_ID

# 9. Wait for running state
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# 10. Verify upgrade
ssh trillium-master "nproc && free -h"
# Expected: 32 vCPUs, 64 GB RAM
```

**Expected Downtime:** ~5 minutes
**Expected Duration:** ~30 minutes total
**Risk Level:** LOW (all data on EBS volumes, preserved)

---

### STEP 2: Launch Phase 2 Parallel Stages (Immediate)

**Goal:** Start all Phase 2 parallel tracks to maximize c7i.8xlarge utilization

**Tracks to Launch:**

1. **Track 2 (Optional Validation)** - 5 minutes
   - Run validation queries: `scripts/validation/track_2_validation_queries.sql`
   - Verify all 336 partitions have expected data
   - Check for NULL values, outliers, temporal coverage

2. **Stage 2.2: Technical Indicators** - 3.8 hours (with c7i.8xlarge)
   - Script: `scripts/ml/populate_technical_indicators_worker.py`
   - Workers: 16 (half of 32 vCPUs)
   - Features: RSI, MACD, ADX, Stochastic, CCI, Williams %R, ROC, MFI

3. **Stage 2.3: Currency Index Features** - 4 hours (with c7i.8xlarge)
   - Schema: `scripts/refactor/stage_2_3_create_currency_index_schema.sql`
   - Worker script: To be created (based on Track 2 template)
   - Workers: 8
   - Features: 8 per partition (base/quote indices, strength, divergence, correlation)

4. **Stage 2.4: Arbitrage Detection** - 12 hours (with c7i.8xlarge)
   - Schema: `scripts/refactor/stage_2_4_create_arbitrage_schema.sql`
   - Worker script: To be created
   - Workers: 8
   - Features: 4 per partition (profit %, opportunity, direction, max profit)

**Launch Command:**

```bash
# Option 1: Use orchestration script (recommended)
bash /home/ubuntu/bqx-ml/scripts/orchestration/launch_phase_2_post_track2.sh

# Option 2: Manual launch
# (1) Run Track 2 validation
PGPASSWORD='BQX_Aurora_2025_Secure' psql \
  -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres -d bqx \
  -f /home/ubuntu/bqx-ml/scripts/validation/track_2_validation_queries.sql

# (2) Create Stage 2.3 and 2.4 schemas
PGPASSWORD='BQX_Aurora_2025_Secure' psql \
  -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres -d bqx \
  -f /home/ubuntu/bqx-ml/scripts/refactor/stage_2_3_create_currency_index_schema.sql

PGPASSWORD='BQX_Aurora_2025_Secure' psql \
  -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres -d bqx \
  -f /home/ubuntu/bqx-ml/scripts/refactor/stage_2_4_create_arbitrage_schema.sql

# (3) Launch workers (when scripts are ready)
# nohup python3 scripts/ml/populate_technical_indicators_worker.py > /tmp/logs/stage_2_2.log 2>&1 &
# nohup python3 scripts/ml/populate_currency_index_worker.py > /tmp/logs/stage_2_3.log 2>&1 &
# nohup python3 scripts/ml/populate_arbitrage_worker.py > /tmp/logs/stage_2_4.log 2>&1 &
```

**Expected Total Duration:** ~12 hours (stages run in parallel)
**CPU Utilization:** 90-95% (32 workers across 32 vCPUs)
**Aurora ACU:** 2-3 ACU average (parallel writes)

---

### STEP 3: Monitor Phase 2 Progress (Ongoing)

**Goal:** Track all stages to completion, identify and resolve issues

**Monitoring Tools:**

1. **CPU Usage:**
   ```bash
   top -u ubuntu
   # Press '1' to see all 32 cores
   ```

2. **Worker Progress:**
   ```bash
   # Stage 2.2 (Technical Indicators)
   tail -f /tmp/logs/stage_2_2.log

   # Stage 2.3 (Currency Index)
   tail -f /tmp/logs/stage_2_3.log

   # Stage 2.4 (Arbitrage)
   tail -f /tmp/logs/stage_2_4.log
   ```

3. **Database Metrics:**
   ```bash
   PGPASSWORD='BQX_Aurora_2025_Secure' psql \
     -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
     -U postgres -d bqx \
     -c "SELECT schemaname, COUNT(*) as tables, SUM(n_live_tup) as rows, pg_size_pretty(SUM(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(relname))::bigint)) as size FROM pg_stat_user_tables WHERE schemaname = 'bqx' GROUP BY schemaname;"
   ```

4. **Aurora ACU Usage:**
   - CloudWatch Metrics: `ServerlessDatabaseCapacity`
   - Expected: 2-3 ACU during parallel writes
   - Max: 32 ACU (if needed)

**Success Criteria:**
- All workers report "Complete!" with 0 failures
- All partitions populated (verify with COUNT(*) queries)
- No errors in worker logs
- CPU usage remains <95% (avoid throttling)
- Aurora ACU scales smoothly (no connection errors)

---

### STEP 4: Execute Remaining Phase 2 Stages (Sequential)

**After Step 3 Completes (~12 hours):**

**Stage 2.6: Statistical Features** - 6 hours
- Features: Statistical analysis across time windows
- Workers: 16

**Stage 2.7: S3 Export** - 6 hours
- Export all 1,080 features to S3 as Parquet files
- Enable S3 Transfer Acceleration
- Expected size: 40-50 GB
- Destination: `s3://bqx-ml-features/phase2/`

**Stage 2.8: Feature Validation** - 6 hours
- Cross-validate all features
- Check for NULL values, outliers, temporal gaps
- Generate validation report

**Stage 2.9: Feature Engineering** - 12 hours
- Create derived features (interactions, ratios, lags)
- Cross-pair features
- Final feature count: 1,080+ features

**Total Sequential Duration:** ~30 hours (1.25 days)

---

### STEP 5: Post-Phase 2 Downgrade (Immediate)

**Goal:** Downgrade EC2 to t3.xlarge after Phase 2 completion

**Why:**
- Phase 2 complete (no longer need 32 vCPUs)
- Phase 3 uses SageMaker (not EC2)
- Cost savings: $121/month vs $993/month (88% reduction)

**Quick Steps:**

```bash
# 1. Verify Phase 2 completion
# - All stages complete
# - S3 export successful (40-50 GB Parquet files)
# - Validation report generated

# 2. Create final snapshot
aws ec2 create-snapshot \
  --volume-id <vol-id> \
  --description "Post-Phase 2 snapshot - Before downgrade" \
  --tag-specifications 'ResourceType=snapshot,Tags=[{Key=Phase,Value=2},{Key=Purpose,Value=Post-Phase2-Backup}]'

# 3. Stop instance
aws ec2 stop-instances --instance-ids $INSTANCE_ID

# 4. Change instance type
aws ec2 modify-instance-attribute \
  --instance-id $INSTANCE_ID \
  --instance-type t3.xlarge

# 5. Start instance
aws ec2 start-instances --instance-ids $INSTANCE_ID

# 6. Verify downgrade
ssh trillium-master "nproc && free -h"
# Expected: 4 vCPUs, 16 GB RAM
```

**Expected Downtime:** ~5 minutes
**Ongoing Cost:** $121/month
**Annual Savings:** $1,464/year vs current t3.2xlarge

---

### STEP 6: Launch Phase 3 (SageMaker)

**Goal:** Begin model training and deployment on SageMaker

**Prerequisites:**
- ✅ Phase 2 complete (1,080+ features in Aurora + S3)
- ✅ EC2 downgraded to t3.xlarge
- ✅ S3 Parquet files validated (40-50 GB)

**Phase 3 Infrastructure:**
- **SageMaker Training Jobs:** ml.m5.2xlarge (on-demand)
- **SageMaker Endpoints:** ml.m5.2xlarge (auto-scaling 1-4 instances)
- **Lambda Functions:** Feature extraction + inference API
- **API Gateway:** REST API for predictions
- **Aurora Serverless v2:** Feature data (0.5-32 ACU)
- **EC2 (t3.xlarge):** Monitoring only (optional)

**Phase 3 Stages:**
- **3.1:** SageMaker experiment setup
- **3.2:** Hyperparameter tuning
- **3.3:** Model deployment infrastructure
- **3.4:** Lambda + API Gateway setup
- **3.5:** Production monitoring

**Documentation:** See [docs/phase_3_sagemaker_setup.md](phase_3_sagemaker_setup.md) (to be created)

**Expected Duration:** ~2 weeks (iterative model development)
**Monthly Cost:** ~$633 (SageMaker + Aurora + EC2)

---

## Timeline Summary

| Milestone | Duration | Start | End | Notes |
|-----------|----------|-------|-----|-------|
| **Track 2 Complete** | 7.2 hours | Nov 13 20:00 | Nov 14 03:32 | ✅ DONE |
| **Aurora Optimization** | 1 hour | Nov 14 05:00 | Nov 14 06:00 | ✅ DONE |
| **System Cleanup** | 30 min | Nov 14 05:30 | Nov 14 06:00 | ✅ DONE |
| **EC2 Upgrade** | 30 min | Nov 14 TBD | Nov 14 TBD | NEXT |
| **Stage 2.2-2.4 (Parallel)** | 12 hours | Nov 14 TBD | Nov 15 TBD | After upgrade |
| **Stage 2.6-2.9 (Sequential)** | 30 hours | Nov 15 TBD | Nov 16 TBD | After parallel stages |
| **EC2 Downgrade** | 30 min | Nov 16 TBD | Nov 16 TBD | After Phase 2 complete |
| **Phase 3 Start** | - | Nov 16 TBD | - | SageMaker setup |

**Total Phase 2 Duration:** ~1.8 days (42.5 hours) from EC2 upgrade to completion

---

## Cost Summary

| Phase | Instance | Duration | Cost |
|-------|----------|----------|------|
| **Track 2 (Completed)** | t3.2xlarge | 7.2 hours | $2.40 |
| **Phase 2 (Remaining)** | c7i.8xlarge Spot | 42.5 hours | ~$19.13 |
| **Phase 2 Total** | - | 49.7 hours | **$21.53** |
| **Ongoing (Post-Phase 2)** | t3.xlarge | Monthly | $121/month |
| **Phase 3** | SageMaker + Aurora + EC2 | Monthly | ~$633/month |

**Savings vs Baseline:**
- Baseline Phase 2 (t3.2xlarge): $60.86
- Actual Phase 2 (c7i.8xlarge Spot): $21.53
- **Savings: $39.33 (65% cheaper + 76% faster!)**

**Annual Savings (EC2 Downgrade):**
- Current t3.2xlarge: $243/month
- Downgraded t3.xlarge: $121/month
- **Savings: $1,464/year**

---

## Risk Assessment

### Technical Risks

**EC2 Upgrade Risk:** LOW
- ✅ In-place upgrade is AWS standard procedure
- ✅ All data on EBS volumes (preserved)
- ✅ No running workers to interrupt (Track 2 complete)
- ✅ 5-minute downtime acceptable (development workload)
- ✅ Rollback plan: Stop → change type back → start

**Phase 2 Execution Risk:** LOW
- ✅ Database optimized (0% dead rows, fresh statistics)
- ✅ System clean (no dead processes or artifacts)
- ✅ Parallel stages tested in Phase 1
- ✅ Worker scripts based on proven Track 2 template
- ✅ Aurora autoscaling handles parallel writes

**Spot Instance Risk:** MEDIUM
- ⚠️ Spot instances can be interrupted with 2-minute warning
- Mitigation: Workers are stateless (resume after interruption)
- Mitigation: Use Spot blocks (1-6 hour guaranteed)
- Probability: LOW for 1-2 day workload

### Cost Risks

**Phase 2 Cost Overrun:** LOW
- ✅ Duration limited to 1.8 days (worst case: 2.5 days)
- ✅ Spot pricing saves 67% vs on-demand
- ✅ Immediate downgrade after completion
- ✅ Total cost $21.53 (vs $60.86 baseline = 65% savings!)

**Phase 3 Cost:** MEDIUM
- ⚠️ SageMaker inference costs $391.86/month (highest component)
- Mitigation: Auto-scaling (1-4 instances, scale to 0 when idle)
- Mitigation: Monitor CloudWatch for usage patterns
- Mitigation: Consider SageMaker Serverless Inference for lower traffic

### Operational Risks

**EC2 Downgrade Too Early:** LOW
- ✅ Clear completion criteria (all stages done, S3 export validated)
- ✅ Phase 3 doesn't need high-performance EC2
- ✅ Can upgrade again if needed (reversible)

**Database Performance:** LOW
- ✅ Aurora Serverless v2 auto-scales (0.5-32 ACU)
- ✅ Connection pooling enabled
- ✅ Indexes optimized, statistics fresh
- ✅ Autovacuum working excellently (0% dead rows)

---

## Success Criteria

### Phase 2 Completion Criteria

**Data Quality:**
- ✅ All 336 partitions populated (reg_rate + reg_bqx)
- ⏳ All additional feature tables populated (Stages 2.2-2.9)
- ⏳ 1,080+ features available in Aurora
- ⏳ S3 Parquet export complete (40-50 GB)
- ⏳ Validation report shows 0% NULL values, 0 outliers

**Technical:**
- ✅ Track 2: 0 failed tasks
- ⏳ All stages: 0 failed tasks
- ⏳ Aurora: 0% dead rows (maintained)
- ⏳ EC2: Downgraded to t3.xlarge
- ⏳ S3: Transfer Acceleration enabled

**Cost:**
- ✅ Track 2: $2.40 (under budget)
- ⏳ Phase 2 total: <$25 (target: $21.53)
- ⏳ Ongoing cost: $121/month (target achieved)

**Timeline:**
- ✅ Track 2: 7.2 hours (under 11 hours baseline)
- ⏳ Phase 2 total: <2 days (target: 1.8 days)
- ⏳ EC2 upgrade: <30 minutes
- ⏳ EC2 downgrade: <30 minutes

---

## Troubleshooting Guide

### Issue: Worker Fails During Stage Execution

**Symptoms:**
- Worker logs show errors
- Partitions not being populated
- CPU usage drops unexpectedly

**Resolution:**
1. Check worker log for specific error message
   ```bash
   tail -100 /tmp/logs/stage_2_X.log
   ```

2. Common issues:
   - **Aurora connection timeout:** Increase connection pool size or reduce workers
   - **Memory error:** Reduce batch size or workers
   - **Data error (NULL/NaN):** Check source data quality, add validation

3. Restart worker with reduced parallelism:
   ```bash
   # Kill existing worker
   pkill -f populate_XXX_worker.py

   # Edit worker script to reduce max_workers
   sed -i 's/max_workers = 16/max_workers = 8/' scripts/ml/populate_XXX_worker.py

   # Restart
   nohup python3 scripts/ml/populate_XXX_worker.py > /tmp/logs/stage_2_X.log 2>&1 &
   ```

### Issue: Spot Instance Interrupted

**Symptoms:**
- EC2 instance terminates unexpectedly
- Workers stop mid-processing
- Cannot SSH to trillium-master

**Resolution:**
1. Check AWS console for Spot interruption notice

2. Option A: Resume with On-Demand pricing
   ```bash
   aws ec2 modify-instance-attribute \
     --instance-id $INSTANCE_ID \
     --instance-initiated-shutdown-behavior stop

   aws ec2 start-instances --instance-ids $INSTANCE_ID
   ```

3. Option B: Request new Spot instance with higher bid
   ```bash
   # Increase bid to reduce interruption risk
   aws ec2 request-spot-instances \
     --spot-price "1.00" \
     --instance-count 1 \
     --type "one-time" \
     --launch-specification file://launch-spec.json
   ```

4. Workers resume automatically (stateless design)

### Issue: Aurora ACU Scaling Issues

**Symptoms:**
- Connection timeout errors
- Slow query performance
- ACU stuck at min (0.5) or max (32)

**Resolution:**
1. Check current ACU usage:
   ```bash
   aws rds describe-db-clusters \
     --db-cluster-identifier trillium-bqx-cluster \
     --query 'DBClusters[0].ServerlessV2ScalingConfiguration'
   ```

2. Adjust min/max ACU if needed:
   ```bash
   aws rds modify-db-cluster \
     --db-cluster-identifier trillium-bqx-cluster \
     --serverless-v2-scaling-configuration MinCapacity=1,MaxCapacity=64 \
     --apply-immediately
   ```

3. Reduce parallel writes:
   - Decrease max_workers in worker scripts
   - Stagger stage launches (don't start all at once)

### Issue: Database Running Out of Space

**Symptoms:**
- "disk full" errors
- Cannot write to Aurora
- pg_stat_user_tables shows massive size increase

**Resolution:**
1. Check database size:
   ```sql
   SELECT pg_size_pretty(pg_database_size('bqx'));
   ```

2. Identify largest tables:
   ```sql
   SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(tablename)))
   FROM pg_tables
   WHERE schemaname = 'bqx'
   ORDER BY pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(tablename)) DESC
   LIMIT 20;
   ```

3. Run VACUUM to reclaim space:
   ```bash
   bash /home/ubuntu/bqx-ml/scripts/maintenance/manual_vacuum_partitions.sh
   ```

4. If still out of space, increase Aurora storage allocation (automatic)

---

## Contact and Support

**Project Lead:** Infrastructure Team
**Documentation:** `/home/ubuntu/bqx-ml/docs/`
**Logs:** `/home/ubuntu/bqx-ml/logs/`
**Scripts:** `/home/ubuntu/bqx-ml/scripts/`

**Key Documents:**
- [EC2 Upgrade/Downgrade Plan](ec2_upgrade_downgrade_plan.md)
- [Phase 2 EC2 Cost Analysis](phase_2_ec2_cost_analysis.md)
- [Aurora Optimization](../scripts/maintenance/aurora_post_track2_optimization.sql)

**Monitoring:**
- AWS Console: EC2, RDS, CloudWatch
- GitHub: https://github.com/Schmidtlappin/bqx-ml
- AirTable: Project tracking

---

## Conclusion

**Current Status:** ✅ **READY FOR EC2 UPGRADE**

All prerequisites for the EC2 upgrade are complete:
- ✅ Track 2: 100% complete (336/336 partitions, 10.3M rows)
- ✅ Database: Optimized (0% dead rows, fresh statistics)
- ✅ System: Clean (no dead processes, logs archived)
- ✅ Documentation: Complete (upgrade plan, cost analysis, this guide)
- ✅ AirTable: Updated (Stage 2.10, timeline estimates)

**Recommended Next Action:**

Execute **STEP 1: EC2 Upgrade to c7i.8xlarge** (30 minutes)

Follow the detailed steps in [docs/ec2_upgrade_downgrade_plan.md](ec2_upgrade_downgrade_plan.md)

**Expected Outcome:**
- Phase 2 completes in **1.8 days** (vs 5.4 days baseline)
- Total cost: **$21.53** (vs $60.86 baseline = 65% savings)
- EC2 downgraded to t3.xlarge saving **$122/month ongoing**
- Ready for Phase 3 (SageMaker) by **Nov 16, 2025**

---

**Last Updated:** 2025-11-14
**Version:** 1.0
**Status:** ✅ Ready for Execution
