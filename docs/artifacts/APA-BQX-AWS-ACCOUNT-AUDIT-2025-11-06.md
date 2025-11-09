# APA/BQX AWS Account Comprehensive Audit
**Date**: November 6, 2025
**Account**: 242201274849 (BQX/APA AWS)
**Status**: 🔴 **CRITICAL - FULL PRODUCTION INFRASTRUCTURE STILL ACTIVE**
**Analyst**: RM-001 (RobkeiRingMaster)

---

## Executive Summary

**CRITICAL FINDING**: User's request to "terminate APA AWS account" reveals that the BQX/APA AWS account (242201274849) is **NOT terminated** as documentation suggested. The ENTIRE Robkei-Engine production infrastructure is **STILL RUNNING** in this account, costing approximately **$4,110/month**.

**Account Identification**: "APA" refers to BQX AWS account 242201274849.

**Documentation Discrepancy**:
- BQX_OXO_TERMINATION_COMPLETE.md (Nov 5, 2025) claims "100% TERMINATED"
- **Reality**: Only OXO ECS services were terminated. Robkei-Engine infrastructure remains fully operational.

**Impact**:
- Duplicate infrastructure costs across BQX and Trillium accounts
- Production workloads running in account user intends to terminate
- Approximately $4,110/month waste in BQX account
- MP-META-001 remediation plan based on false assumption that production is in Trillium

---

## Account Summary

| Metric | Value |
|--------|-------|
| **Account ID** | 242201274849 |
| **Account Name** | BQX AWS (also referred to as "APA") |
| **Account Type** | Root account credentials available |
| **Region** | us-east-1 |
| **Current Daily Cost** | $137.11 (Nov 5, 2025) |
| **Estimated Monthly Cost** | ~$4,110/month |
| **Status** | ACTIVE (not terminated) |
| **User Intent** | TERMINATE (per request) |

---

## Active Resources Inventory

### 1. Compute Resources ⚠️ CRITICAL

#### ECS Cluster: robkei-engine-cluster
**Status**: ACTIVE
**Running Tasks**: 8 tasks
**Active Services**: 12 agent services

**Agent Services**:
```
✅ robkei-agent-RM-001 (RingMaster) - 0/0 tasks (service exists)
✅ robkei-agent-PROMPTER-001 - 1/1 tasks RUNNING
✅ robkei-agent-MON-001 - 0/0 tasks (service exists)
✅ robkei-agent-ARCH-001
✅ robkei-agent-COORD-001
✅ robkei-agent-DATA-001
✅ robkei-agent-INFRA-001
✅ robkei-agent-INTEL-001
✅ robkei-agent-MANDATE-001
✅ robkei-agent-QA-001
✅ robkei-agent-SECRET-001
✅ robkei-agent-UP-001
```

**Significance**: This is the PRIMARY Robkei-Engine agent infrastructure, NOT migrated to Trillium.

#### Other ECS Clusters
```
✅ oxo-prod-cluster - ACTIVE (0 tasks running)
✅ BQX-Phase2-Compute_Batch - ACTIVE
✅ AWSBatch-BQX-Phase2-ComputeEnv - ACTIVE
```

#### EC2 Instances (2 running)
| Instance ID | Type | State | Name | Monthly Cost |
|-------------|------|-------|------|--------------|
| i-08570d6a274740283 | m7i.xlarge | running | BQX-Master | ~$175/mo |
| i-05f893173876e67cb | t3.micro | running | Robkei-Engine-Bastion | ~$7/mo |

**Total EC2 Cost**: ~$182/month

---

### 2. Database Resources ⚠️ CRITICAL

#### Aurora PostgreSQL Clusters (3 active)

**bqx-aurora-cluster**:
- Status: available (NOT stopped as documentation claimed)
- Engine: aurora-postgresql 16.8
- Scaling: Serverless v2 (0.5-16 ACU)
- Instances: bqx-aurora-writer
- Estimated Cost: $50-300/month (depending on usage)

**nwbb-aurora-cluster**:
- Status: available (NOT stopped)
- Engine: aurora-postgresql 16.8
- Scaling: Serverless v2 (0.5-2 ACU)
- Instances: nwbb-aurora-instance-1
- Estimated Cost: $20-100/month

**oxo-aurora-cluster**:
- Status: available (NOT stopped)
- Engine: aurora-postgresql 15.12
- Scaling: Serverless v2 (16-64 ACU)
- Instances: None (serverless)
- Estimated Cost: $500-2,000/month (high ACU range)

**Total Aurora Cost**: ~$570-2,400/month (highly variable based on usage)

**Migration Status**: Trillium has equivalent clusters:
- trillium-bqx-cluster (stopping)
- trillium-nwbb-cluster (stopping)
- trillium-oxo-cluster (available)
- trillium-oxo-prod-cluster (available)

#### DynamoDB Tables (4 production tables)
```
✅ RobkeiEngine-AgentState
✅ RobkeiEngine-ExecutionHistory
✅ RobkeiEngine-TaskQueue
✅ RobkeiEngine-WorkspaceMetadata
```

**Status**: All ACTIVE
**Configuration**: On-demand billing
**Estimated Cost**: $10-50/month
**Significance**: These are the PRODUCTION DynamoDB tables for agent orchestration

**Migration Status**: MP-META-001 remediation plan assumes these don't exist and need to be created. **This is FALSE** - they exist in BQX, not Trillium.

---

### 3. Cache/Queue Resources

#### ElastiCache Redis
**Replication Group**: robkei-engine-redis
**Status**: available
**Endpoint**: master.robkei-engine-redis.94ys1u.use1.cache.amazonaws.com:6379
**Node Type**: cache.t4g.micro (2 nodes)
**Estimated Cost**: ~$25/month

**Additional Redis Clusters**:
- robkei-engine-redis-001 (cache.t4g.micro) - available
- robkei-engine-redis-002 (cache.t4g.micro) - available

**Total Redis Cost**: ~$37/month

#### SQS Queues (3 active)
```
✅ robkei-engine-agent-messages
✅ robkei-engine-agent-tasks
✅ robkei-engine-agent-tasks-dlq
```

**Estimated Cost**: $0-5/month (usage-based)

---

### 4. Storage Resources

#### S3 Buckets (12 buckets)
```
Production Robkei-Engine:
✅ robkei-engine-workspaces (2025-11-01)
✅ robkei-engine-intelligence (2025-11-01)
✅ robkei-engine-cloudtrail-logs (2025-11-02)

OXO/Production:
✅ oxo-master-s3
✅ oxo-migration-archive

BQX/ML:
✅ bqx-ml-code
✅ bqx-ml-data-2025
✅ bqx-ml-features
✅ bqx-consolidated-backups

Archive:
✅ robkei-archive
✅ robkei-control-s3
✅ robkei-snaps
```

**Estimated Total Size**: Unknown (need detailed audit)
**Estimated Cost**: $50-200/month (depends on size + requests)

---

### 5. Container Registry

#### ECR Repositories (7 repositories)
```
✅ robkei-engine/agent-worker (production agent images)
✅ robkei-engine/agent-master
✅ robkei-engine/agent-base
✅ robkei-engine/agent-compliance
✅ oxo-api
✅ oxo-worker
✅ bqx-phase2-executor
```

**Estimated Cost**: $5-20/month (storage + data transfer)

---

### 6. Serverless Functions

#### Lambda Functions (2 functions)
```
✅ robkei-ecs-task-invoker (python3.11, updated 2025-11-02)
✅ robkei-webhook-handler (python3.11, updated 2025-11-02)
```

**Estimated Cost**: $0-10/month (invocation-based)

---

### 7. Network Resources

#### VPCs (2 active)
```
✅ vpc-0dacd03e7d72faa0e (10.0.0.0/16) - Robkei-Engine-VPC
✅ vpc-012f36964abcf0bd4 (10.0.0.0/16) - oxo-vpc
✅ vpc-0d4634e85c94e5d2e (172.31.0.0/16) - default VPC
```

#### NAT Gateway (1 active)
```
✅ nat-0ed8dbbdb4e0942c7 - available
   Subnet: subnet-07a1e20b501d99cf9
```

**Estimated Cost**: ~$32/month (fixed) + data transfer costs (~$10-50/month)

---

## Cost Analysis

### Current Monthly Burn Rate: ~$4,110/month

| Category | Estimated Monthly Cost | Percentage |
|----------|----------------------|------------|
| Aurora Databases (3 clusters) | $570-2,400 | 14-58% |
| EC2 Instances (2) | $182 | 4% |
| NAT Gateway | $32 + data | 1-2% |
| ECS Fargate Tasks (8 running) | $50-100 | 1-2% |
| S3 Storage + Requests | $50-200 | 1-5% |
| ElastiCache Redis (3 nodes) | $37 | 1% |
| DynamoDB (4 tables) | $10-50 | <1% |
| ECR Storage | $5-20 | <1% |
| Lambda Functions | $0-10 | <1% |
| VPC/Networking | $20-50 | <1% |
| **TOTAL** | **~$956-3,099** | **100%** |

**Note**: Daily cost of $137.11 (Nov 5) suggests actual monthly cost is closer to **$4,110/month**, indicating high Aurora usage.

---

## Migration Status Analysis

### What Documentation Claims

**BQX_OXO_TERMINATION_COMPLETE.md (Nov 5, 2025)**:
> "All OXO infrastructure in BQX AWS has been successfully terminated following 100% validation of operational services in Trillium AWS."
>
> "Status: ✅ MIGRATION & TERMINATION COMPLETE"
>
> "Result: 88.5% Cost Reduction ($1,628/mo savings)"

**TRILLIUM-SESSION-HANDOFF.md**:
> "This session completes the CRITICAL migration from deprecated BQX AWS infrastructure to production Trillium AWS infrastructure."
>
> "Switched from BQX AWS (242201274849) to Trillium AWS (543634432604)"

**MP-META-001-PRODUCTION-INFRASTRUCTURE-REMEDIATION.md**:
> "Production Infrastructure Status (CONFIRMED OPERATIONAL)"
>
> "AWS ECS Fargate - ACTIVE"
> "Cluster: robkei-engine-cluster (Account: 543634432604 - Trillium)"
> "Operational Agents (11 services, 13 tasks)"

### What Actually Happened

**Reality**:
1. **OXO services** were migrated/terminated from BQX to Trillium (Nov 4-5, 2025) ✅
2. **Robkei-Engine infrastructure** was NEVER migrated - still 100% in BQX ❌
3. **Documentation describes Trillium as production**, but actual production is BQX ❌
4. **DynamoDB tables exist in BQX**, not Trillium (remediation plan assumes they need creation) ❌

**What Was Migrated**:
- ✅ OXO API services (2 tasks)
- ✅ OXO worker services (2 tasks)
- ✅ OXO Redis cluster (oxo-redis-repl in Trillium)
- ✅ Aurora database connections (cross-account access configured)

**What Was NOT Migrated** (still in BQX):
- ❌ Robkei-Engine ECS cluster (12 agent services)
- ❌ DynamoDB tables (4 production tables)
- ❌ Robkei-Engine Redis cluster
- ❌ SQS queues (3 queues)
- ❌ ECR repositories (7 repos)
- ❌ S3 buckets (robkei-engine-*)
- ❌ Lambda functions (2 functions)
- ❌ BQX-Master EC2 instance
- ❌ Robkei-Engine-Bastion EC2
- ❌ bqx-aurora-cluster, nwbb-aurora-cluster, oxo-aurora-cluster (all still running in BQX)

---

## Impact Assessment

### 1. Cost Impact ⚠️ CRITICAL
- **Current Waste**: $4,110/month in BQX account user intends to terminate
- **Duplicate Infrastructure**: Some services running in both BQX and Trillium
- **Opportunity Cost**: Could reduce to $0/month in BQX if fully migrated

### 2. Operational Impact ⚠️ CRITICAL
- **Production Workloads at Risk**: All Robkei-Engine agents running in account marked for termination
- **Data Loss Risk**: 4 DynamoDB tables with production agent state in BQX
- **Service Disruption**: Terminating BQX account would break all agent operations

### 3. Documentation Impact ⚠️ HIGH
- **MP-META-001 Remediation Plan**: Based on FALSE assumption that production is in Trillium
- **Infrastructure Diagrams**: All show Trillium as production, but BQX is actual production
- **Airtable Records**: MP-ROBKEI-001 assumes starting from zero infrastructure in Trillium

### 4. Strategic Impact ⚠️ HIGH
- **Account Termination Blocked**: Cannot terminate BQX without migrating Robkei-Engine first
- **Timeline Impact**: Migration work not planned in MP-ROBKEI-001
- **Budget Impact**: Migration will cost $500-1,000 in engineering time + testing

---

## Required Actions Before Termination

### Phase 1: Complete Robkei-Engine Migration to Trillium (6-8 hours)

**Owner**: GANG-META-INFRA-001 (ARCH-001 lead)
**Priority**: 🔴 CRITICAL BLOCKER

#### Task 1.1: Migrate DynamoDB Tables (1 hour)
- Export 4 tables from BQX (AgentState, ExecutionHistory, TaskQueue, WorkspaceMetadata)
- Create identical tables in Trillium
- Import data with zero downtime
- Validate data consistency
- **Cost**: $0 (free tier)

#### Task 1.2: Migrate ECS Services (2 hours)
- Copy 12 agent task definitions to Trillium
- Create 12 ECS services in Trillium cluster
- Update all references from BQX Redis → Trillium Redis
- Validate agent startup and health checks
- **Cost**: Same as current ($50-100/mo)

#### Task 1.3: Migrate S3 Buckets (2 hours)
- Create robkei-engine-* buckets in Trillium
- Copy data from BQX → Trillium (use S3 replication or aws s3 sync)
- Update agent configs to point to Trillium buckets
- Validate data accessibility
- **Cost**: $50-200/mo (same as current)

#### Task 1.4: Migrate SQS Queues (30 min)
- Create 3 queues in Trillium (agent-messages, agent-tasks, agent-tasks-dlq)
- Update Lambda functions to publish to Trillium queues
- Update agents to poll Trillium queues
- **Cost**: $0-5/mo (same as current)

#### Task 1.5: Migrate Lambda Functions (30 min)
- Copy robkei-ecs-task-invoker to Trillium
- Copy robkei-webhook-handler to Trillium
- Update IAM roles and permissions
- Update Airtable webhook URLs
- **Cost**: $0-10/mo (same as current)

#### Task 1.6: Migrate ECR Repositories (1 hour)
- Copy 7 Docker images from BQX ECR → Trillium ECR
- Update ECS task definitions to reference Trillium ECR
- Validate image pulls work correctly
- **Cost**: $5-20/mo (same as current)

#### Task 1.7: Update Intelligence Files (30 min)
- Update all intelligence files with Trillium endpoints
- Update agent charges with new resource ARNs
- Commit changes to git
- **Cost**: $0

#### Task 1.8: Cutover & Validation (1 hour)
- Stop all BQX agent services simultaneously
- Start all Trillium agent services
- Validate: agents connect to Redis, poll SQS, process tasks
- Monitor CloudWatch Logs for errors
- **Rollback Plan**: Restart BQX services if any critical failures

**Total Phase 1 Duration**: 8 hours
**Total Phase 1 Cost**: $0 (migration) + $350/mo (ongoing Trillium infrastructure)

---

### Phase 2: Migrate Aurora Databases to Trillium (4-6 hours)

**Owner**: DATA-001
**Priority**: 🟡 HIGH (if databases contain production data)

**Current Status**:
- Trillium already has connections to BQX Aurora clusters (cross-account access)
- trillium-bqx-cluster and trillium-nwbb-cluster status: "stopping"
- Decision required: Migrate or keep cross-account access?

**Option A: Full Migration** (6 hours, $500-2,400/mo cost)
- Use AWS Database Migration Service (DMS)
- Create Aurora clusters in Trillium matching BQX specs
- Migrate data with minimal downtime
- Update connection strings in secrets manager
- Validate application connectivity

**Option B: Keep Cross-Account Access** (0 hours, $570-2,400/mo cost stays in BQX)
- **Blocker**: Cannot terminate BQX account
- **Risk**: Cross-account dependency

**Option C: Export and Terminate** (2 hours, $0/mo)
- Export all data to S3
- Archive for compliance/auditing
- Terminate BQX Aurora clusters
- **Risk**: Data not accessible for queries

**Recommended**: Option A (Full Migration) to enable BQX termination

---

### Phase 3: Final Cleanup & BQX Termination (2 hours)

**Owner**: INFRA-001
**Priority**: 🟢 MEDIUM (only after Phase 1-2 complete)

#### Task 3.1: Terminate Remaining Resources (1 hour)
```bash
# Terminate EC2 instances
aws ec2 terminate-instances --instance-ids i-08570d6a274740283 i-05f893173876e67cb

# Delete ECS clusters
aws ecs delete-cluster --cluster robkei-engine-cluster
aws ecs delete-cluster --cluster oxo-prod-cluster

# Delete ElastiCache Redis
aws elasticache delete-replication-group --replication-group-id robkei-engine-redis

# Delete NAT Gateway
aws ec2 delete-nat-gateway --nat-gateway-id nat-0ed8dbbdb4e0942c7

# Empty and delete S3 buckets
for bucket in $(aws s3 ls | grep -E 'robkei|bqx|oxo' | awk '{print $3}'); do
    aws s3 rb s3://$bucket --force
done

# Delete Lambda functions
aws lambda delete-function --function-name robkei-ecs-task-invoker
aws lambda delete-function --function-name robkei-webhook-handler

# Delete SQS queues
aws sqs delete-queue --queue-url https://sqs.us-east-1.amazonaws.com/242201274849/robkei-engine-agent-messages
# ... (repeat for other queues)

# Delete DynamoDB tables
aws dynamodb delete-table --table-name RobkeiEngine-AgentState
# ... (repeat for other tables)

# Delete ECR repositories
aws ecr delete-repository --repository-name robkei-engine/agent-worker --force
# ... (repeat for other repos)

# Delete VPCs (requires manual cleanup of ENIs, subnets, etc.)
```

#### Task 3.2: Final Cost Verification (30 min)
- Wait 24-48 hours after resource deletion
- Check AWS Cost Explorer for $0/day spend
- Verify no orphaned resources (EBS volumes, snapshots, etc.)

#### Task 3.3: Account Closure (30 min)
- Export final billing reports
- Archive CloudWatch logs to S3 (in Trillium)
- Document final resource inventory
- Close AWS account via AWS Console

**Estimated Savings After Full Termination**: **$4,110/month → $0/month**

---

## Recommended Migration Plan

### Timeline: 2-3 Days (12-16 hours total work)

| Day | Phase | Duration | Owner | Cost Impact |
|-----|-------|----------|-------|-------------|
| Day 1 | Robkei-Engine Migration | 8 hours | ARCH-001, INFRA-001, DATA-001 | +$350/mo (Trillium) |
| Day 2 | Aurora Database Migration | 6 hours | DATA-001 | +$500-2,400/mo (Trillium) |
| Day 3 | BQX Cleanup & Termination | 2 hours | INFRA-001 | -$4,110/mo (BQX terminated) |
| **Total** | **3 phases** | **16 hours** | **GANG-META-INFRA-001** | **Net: -$1,260 to -$3,260/mo** |

### Cost-Benefit Analysis

**Migration Cost**: $500-1,000 (engineering time at $32-64/hour)
**Monthly Savings**: $1,260-3,260/month
**Break-Even**: 7-30 days
**Annual Savings**: $15,120-39,120/year

**ROI**: 1,512% - 3,912% annually

---

## Critical Gaps in Current Documentation

### 1. MP-META-001-PRODUCTION-INFRASTRUCTURE-REMEDIATION.md
**Issue**: Claims production infrastructure is in Trillium (543634432604)
**Reality**: Production infrastructure is in BQX (242201274849)
**Impact**: Entire remediation plan addresses non-existent gaps in Trillium

**FALSE CLAIMS**:
- "Missing: RobkeiEngine-AgentState" → Actually exists in BQX
- "Missing: RobkeiEngine-TaskQueue" → Actually exists in BQX
- "Missing: RobkeiEngine-ExecutionHistory" → Actually exists in BQX
- "Missing: RobkeiEngine-WorkspaceMetadata" → Actually exists in BQX
- "Not Deployed to ECS: PROMPTER-001" → Actually deployed and RUNNING in BQX

### 2. MP-ROBKEI-001 (Airtable Plan)
**Issue**: Assumes starting from zero infrastructure in Trillium
**Reality**: Full infrastructure exists in BQX, needs migration not creation
**Impact**: All 61 tasks, 14 stages, 4 phases assume greenfield deployment

### 3. BQX_OXO_TERMINATION_COMPLETE.md
**Issue**: Claims "100% TERMINATED" for BQX account
**Reality**: Only OXO services terminated, Robkei-Engine still 100% active
**Impact**: User believes BQX account is ready for closure when it's not

### 4. TRILLIUM-SESSION-HANDOFF.md
**Issue**: Claims migration complete from BQX to Trillium
**Reality**: Only context switch and Airtable migration, no infrastructure migration
**Impact**: All subsequent work assumes Trillium is production

---

## Immediate Next Steps

### Option 1: Migrate Then Terminate (RECOMMENDED)
1. **Create Migration Plan**: Update MP-ROBKEI-001 with migration tasks (16 hours, $500-1,000)
2. **Execute Migration**: GANG-META-INFRA-001 executes Robkei-Engine + Aurora migration (2-3 days)
3. **Validate Trillium**: 48-hour soak test in production (QA-001)
4. **Terminate BQX**: Full resource cleanup and account closure (saves $4,110/mo)
5. **Update Documentation**: Correct all false claims about infrastructure location

**Timeline**: 1 week
**Cost**: $500-1,000 (one-time) + $850-2,750/mo (ongoing Trillium)
**Savings**: $1,260-3,260/mo (net savings)

### Option 2: Defer Migration, Keep BQX Active
1. **Cancel Termination Plan**: Do not close BQX account
2. **Update Documentation**: Clarify that BQX is production, Trillium is backup/OXO
3. **Accept Cost**: Continue paying $4,110/mo for BQX
4. **Future Migration**: Plan for later date when resources available

**Timeline**: Immediate
**Cost**: $0 (one-time), $4,110/mo (ongoing BQX) + $212/mo (Trillium for OXO)
**Savings**: $0

### Option 3: Emergency Termination (NOT RECOMMENDED - HIGH RISK)
1. **Backup Critical Data**: Export DynamoDB, S3, Aurora to Trillium
2. **Terminate BQX Immediately**: Delete all resources without migration
3. **Rebuild in Trillium**: Recreate Robkei-Engine from backups
4. **Accept Downtime**: 2-5 days of agent unavailability

**Timeline**: 3-5 days (with 2-3 days downtime)
**Cost**: $1,000-2,000 (emergency work) + data loss risk
**Savings**: $4,110/mo (but with service disruption cost)

---

## Decision Matrix

| Criteria | Option 1: Migrate | Option 2: Defer | Option 3: Emergency |
|----------|------------------|-----------------|-------------------|
| **Cost (1-month)** | -$760 to -$2,260 | +$4,322 | -$2,110 to -$4,110 |
| **Cost (12-month)** | -$14,120 to -$38,120 | +$51,864 | -$27,320 to -$51,320 |
| **Risk** | Low | None | Very High |
| **Downtime** | <1 hour | 0 hours | 48-72 hours |
| **Data Loss Risk** | None | None | Medium-High |
| **Timeline** | 1 week | Immediate | 3-5 days |
| **Effort** | 16 hours | 0 hours | 40+ hours |
| **User Intent** | ✅ Meets intent | ❌ Ignores intent | ⚠️ Risky compliance |

**Recommendation**: **Option 1 - Migrate Then Terminate**

---

## Conclusion

**User's Request**: "User is terminating APA AWS account. Robkei Engine will be build exclusively in Trillium AWS account. Audit APA AWS active services and determine what needs to be migrated, if anything, to Trillium."

**Answer**:
1. **APA = BQX AWS account 242201274849**
2. **Current Status**: FULLY ACTIVE with $4,110/month production infrastructure
3. **What Needs Migration**: EVERYTHING except OXO services
   - 12 ECS agent services
   - 4 DynamoDB tables
   - 3 Aurora clusters
   - Redis cluster
   - 3 SQS queues
   - 12 S3 buckets
   - 7 ECR repositories
   - 2 Lambda functions
   - 2 EC2 instances
   - Network infrastructure

4. **Can Terminate Now**: ❌ NO - Would cause complete Robkei-Engine service outage
5. **Required Work**: 16-hour migration project (2-3 days)
6. **Estimated Savings**: $1,260-3,260/month after migration
7. **Risk**: Medium (with proper testing and rollback plan)

**Critical Action Required**: User must approve migration plan BEFORE any termination activities.

---

**Document Status**: ✅ AUDIT COMPLETE
**Recommendation**: APPROVE MIGRATION PLAN - DO NOT TERMINATE WITHOUT MIGRATION
**Next Action**: Present migration plan to user for approval
**Owner**: RM-001 → Delegate migration to GANG-META-INFRA-001

---

**References**:
- BQX_OXO_TERMINATION_COMPLETE.md (contains false "100% terminated" claim)
- TRILLIUM-SESSION-HANDOFF.md (documents OXO migration only)
- MP-META-001-PRODUCTION-INFRASTRUCTURE-REMEDIATION.md (based on false Trillium assumption)
- AWS Account Credentials: bqx-mirror/bqx/aws/apa-credentials (Secrets Manager)
