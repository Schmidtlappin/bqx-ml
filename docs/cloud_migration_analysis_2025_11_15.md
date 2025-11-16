# BQX ML Migration Analysis: AWS → Azure/GCP

**Date:** 2025-11-15
**Context:** AWS quota request denied (8 → 64 vCPUs), evaluating migration options
**Status:** Architecture highly portable, migration feasible

---

## Current AWS Architecture

### Core Components
1. **Database:** Aurora PostgreSQL Serverless v2 (0.5-32 ACU auto-scaling)
   - 96M rows populated (~10.3M per table family)
   - ~17,000 tables (parent + partitions)
   - Connection: Standard PostgreSQL protocol

2. **Compute:** EC2 instances
   - trillium-master: t3.2xlarge (8 vCPUs, 32 GB RAM) - permanent
   - Phase 2 worker: c7i.8xlarge (32 vCPUs, 64 GB RAM) - temporary

3. **Storage:** S3 (planned for Phase 2 export)
   - Parquet files: 40-50 GB

4. **Code:** Python scripts
   - Standard libraries: pandas, numpy, psycopg2, TA-Lib
   - No AWS SDK (boto3) dependencies detected
   - Only dependency: Database connection string

### AWS-Specific Dependencies
- ✅ **Zero AWS SDK usage** - No boto3, no AWS-specific APIs
- ✅ **Standard PostgreSQL** - No Aurora-specific features used
- ✅ **Portable Python** - Standard libraries only
- ❌ **Hardcoded endpoints** - Connection strings hardcoded in ~20 scripts

---

## Migration Difficulty Assessment

### ✅ EASY Components (1-2 days)

#### 1. Database Migration
**Complexity: LOW**
- **Method:** PostgreSQL dump/restore
- **Tool:** `pg_dump` + `pg_restore` (native PostgreSQL)
- **Duration:** 4-8 hours (96M rows)
- **Zero downtime possible:** Yes (replicate then cutover)

**Azure Option: Azure Database for PostgreSQL Flexible Server**
- Equivalent: Flexible Server with auto-scaling
- Compatibility: 100% (standard PostgreSQL)
- Migration tool: Azure Database Migration Service (free)

**GCP Option: Cloud SQL for PostgreSQL**
- Equivalent: Cloud SQL with auto-scaling
- Compatibility: 100% (standard PostgreSQL)
- Migration tool: Database Migration Service (free)

#### 2. Python Scripts
**Complexity: TRIVIAL**
- **Change required:** Update connection strings only
- **Files to modify:** ~20 Python scripts
- **Duration:** 1 hour (find/replace)
- **Tool:** `sed` or environment variables

```bash
# Example migration
sed -i 's/trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com/YOUR_NEW_DB_HOST/g' scripts/ml/*.py
```

#### 3. Storage (S3 → Blob/GCS)
**Complexity: LOW**
- **Azure:** Azure Blob Storage (S3-compatible APIs available)
- **GCP:** Google Cloud Storage (S3-compatible via interoperability API)
- **Code changes:** Minimal (same boto3 S3 API works with compatibility layers)
- **Duration:** 2-4 hours

---

### 🟡 MODERATE Components (1 week)

#### 4. Compute Instance Setup
**Complexity: MODERATE**
- **Why moderate:** Need to provision, configure, test
- **Duration:** 2-3 days

**Azure Option: Virtual Machines**
- Equivalent to c7i.8xlarge: **Standard_D8as_v5**
  - 8 vCPUs (AMD EPYC), 32 GB RAM
  - Price: ~$0.576/hr (~same as AWS c7i.8xlarge)
- Equivalent to t3.2xlarge: **Standard_D8s_v5**
  - 8 vCPUs, 32 GB RAM
  - Price: ~$0.384/hr

**GCP Option: Compute Engine**
- Equivalent to c7i.8xlarge: **c2-standard-8**
  - 8 vCPUs (Intel Cascade Lake), 32 GB RAM
  - Price: ~$0.447/hr
- For 32 vCPUs: **c2-standard-32** (32 vCPUs, 128 GB RAM)
  - Price: ~$1.788/hr

**Migration Steps:**
1. Create VM images
2. Install Python dependencies
3. Clone git repo
4. Update connection strings
5. Test workers

#### 5. Network Configuration
**Complexity: LOW-MODERATE**
- VPC/VNet setup: 2-4 hours
- Security groups/NSGs: 2-4 hours
- Private endpoints: 2-4 hours

---

## Cost Comparison

### AWS Current/Planned
| Component | Type | Monthly Cost |
|-----------|------|--------------|
| Aurora Serverless v2 | 0.5-32 ACU | ~$50-200 |
| trillium-master | t3.2xlarge (always-on) | $243 |
| Phase 2 worker | c7i.8xlarge (1.8 days) | $58 one-time |
| **Total** | | **~$293-443/mo** |

### Azure Equivalent
| Component | Type | Monthly Cost |
|-----------|------|--------------|
| PostgreSQL Flexible | 8 vCores, auto-scale storage | ~$150-250 |
| Master VM | Standard_D8s_v5 (always-on) | ~$277 |
| Phase 2 worker | Standard_D8as_v5 (1.8 days) | ~$50 one-time |
| **Total** | | **~$427-527/mo** |

**Cost Impact:** +$134-84/mo (+46-19%)

### GCP Equivalent
| Component | Type | Monthly Cost |
|-----------|------|--------------|
| Cloud SQL PostgreSQL | 8 vCPUs, 30 GB RAM, auto-scale | ~$200-300 |
| Master VM | n2-standard-8 (always-on) | ~$245 |
| Phase 2 worker | c2-standard-32 (1.8 days) | ~$154 one-time |
| **Total** | | **~$445-545/mo** |

**Cost Impact:** +$152-102/mo (+52-23%)

---

## Migration Timeline

### Parallel Migration (Recommended)
**Total: 5-7 days**

**Day 1-2: Database Migration**
- Set up Azure PostgreSQL / Cloud SQL
- Configure replication from AWS
- Validate data integrity

**Day 2-3: Compute Setup**
- Create VMs
- Install dependencies
- Configure networking

**Day 3-4: Code Migration**
- Update connection strings
- Test workers
- Validate feature generation

**Day 4-5: Testing**
- Run Phase 2 workers on new platform
- Validate output
- Performance testing

**Day 5-7: Cutover**
- Stop AWS workers
- Point production to new platform
- Monitor

### Sequential Migration (Conservative)
**Total: 2-3 weeks**
- Week 1: Database migration + validation
- Week 2: Compute setup + testing
- Week 3: Cutover + monitoring

---

## Risk Analysis

### LOW RISK ✅
- **Database compatibility:** 100% (standard PostgreSQL)
- **Code portability:** 99% (only connection strings change)
- **Data migration:** Low risk (standard pg_dump/restore)

### MEDIUM RISK 🟡
- **Performance differences:** May need tuning for different cloud
- **Networking complexity:** VPC peering, private endpoints
- **Cost overrun:** Azure/GCP ~20-50% more expensive

### HIGH RISK ❌
- **None identified** - This is a highly portable architecture

---

## Recommendation

### If Staying with AWS
**Wait for Quota Approval (Recommended)**
- Current wait: 19h 42m (normal for manual review)
- Expected approval: Within 24-48 hours
- Try 32 vCPU request once current case closes
- **Fastest path:** 2-3 days total

### If Migrating

**Best Choice: Google Cloud Platform (GCP)**
- **Why:**
  - Better quota defaults (no pre-approval needed for standard VMs)
  - c2-standard-32 available immediately (32 vCPUs)
  - Cloud SQL for PostgreSQL proven at scale
  - Migration tooling mature

- **Cost:** ~$100-200/mo more than AWS
- **Timeline:** 5-7 days for full migration
- **Risk:** Low
- **Benefit:** Immediate quota availability

**Second Choice: Azure**
- **Why:**
  - Good PostgreSQL offering (Flexible Server)
  - Competitive pricing
  - Enterprise support

- **Cost:** ~$80-130/mo more than AWS
- **Timeline:** 5-7 days
- **Risk:** Low

---

## Quota Situation Analysis

### Why AWS Quota Was Denied (Speculation)
- New account or low usage history
- Large jump (8 → 64 vCPUs = 8x increase)
- May approve smaller increases (8 → 32 = 4x)

### Azure/GCP Quota Advantages
- **Azure:** Default quota often 20-100 vCPUs per region
- **GCP:** Default quota often 24-96 vCPUs per region
- **Both:** Less restrictive on new accounts

---

## Final Recommendation

**Short Answer:** Migration difficulty = **EASY** (5-7 days)

**My Advice:**
1. **Try AWS 32 vCPU request first** (wait for current case to close)
   - Timeline: 1-2 days
   - Cost: $0 (already on AWS)
   - Risk: Minimal

2. **If AWS denies 32 vCPUs, migrate to GCP**
   - Timeline: 5-7 days
   - Cost: +$100-200/mo
   - Risk: Low
   - Benefit: Immediate quota availability

3. **Don't migrate unless necessary**
   - AWS is working fine except quota issue
   - Migration adds complexity
   - You'll face quota limits on other clouds too (just higher defaults)

---

## Migration Checklist (If You Decide to Migrate)

### Pre-Migration (1 day)
- [ ] Create GCP/Azure account
- [ ] Set up billing
- [ ] Request quota if needed (proactive)
- [ ] Plan VPC/VNet architecture

### Database Migration (2 days)
- [ ] Create Cloud SQL / Azure PostgreSQL instance
- [ ] Configure networking (private IP, firewall)
- [ ] Set up replication from AWS Aurora
- [ ] Validate row counts match
- [ ] Test connection from new VMs

### Compute Migration (2 days)
- [ ] Create VM instances
- [ ] Install Python 3.10, pip, dependencies
- [ ] Clone git repo
- [ ] Update all connection strings
- [ ] Test one worker end-to-end

### Cutover (1 day)
- [ ] Stop AWS workers
- [ ] Update all scripts to new DB
- [ ] Run Phase 2 workers on new platform
- [ ] Monitor for 24 hours
- [ ] Decommission AWS resources

### Post-Migration (ongoing)
- [ ] Monitor costs
- [ ] Optimize instance sizes
- [ ] Set up alerting
- [ ] Document new architecture

---

## Immediate Next Steps

### While Waiting for AWS 64→32 vCPU Request Window

**Option A: Continue AWS Path**
1. Wait for API to update (current case shows CASE_OPENED but you say it was denied)
2. Submit 32 vCPU request once old case clears (15-60 minutes)
3. Expect faster approval (4x increase vs 8x)
4. Launch Phase 2 in 1-2 days

**Option B: Start GCP Migration in Parallel**
1. Create GCP account today
2. Set up Cloud SQL PostgreSQL (4-6 hours)
3. Begin database replication (overnight)
4. Test with one worker (1 day)
5. Decision point: Stay on AWS or complete GCP migration

**Option C: Hybrid Approach**
1. Keep Aurora on AWS (working fine, no quota issues)
2. Launch compute workers on GCP (no quota approval needed)
3. Connect GCP VMs to AWS Aurora via VPC peering or public endpoint
4. Minimal migration (just compute), lower risk
5. Timeline: 2-3 days

---

## Bottom Line

**Migration Difficulty:** ⭐⭐ (2/5 - Easy)

This is one of the **most portable cloud architectures** I've analyzed. You have:
- Standard PostgreSQL (not Aurora-specific features)
- Zero AWS SDK dependencies
- Python code with only connection string dependencies

**My Strong Recommendation:**
1. Try AWS 32 vCPU request first (may approve smaller increase)
2. If denied, **Option C (Hybrid)** is fastest: Keep Aurora, move compute to GCP
3. Full migration only if you want to leave AWS entirely

**Don't panic** - you have excellent options with low risk.
