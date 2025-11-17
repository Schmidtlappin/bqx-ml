# Manual AirTable Update - TIER 1 Azure F72s_v2 Plan

**Date:** 2025-11-17
**Purpose:** Update AirTable PM table with approved Azure F72s_v2 infrastructure plan for TIER 1
**Reason:** API token lacks write permissions (403 error)

---

## APPROVED PLAN SUMMARY

**Infrastructure:** Azure Standard_F72s_v2 Spot
- **vCPUs:** 72 (2.25x AWS baseline)
- **RAM:** 144 GB
- **Region:** East US
- **Pricing:** ~$0.75/hour Spot (~75% discount)

**Performance:**
- **Total Duration:** ~28.6 hours (vs 55h AWS = **48% faster**)
- **Total Cost:** ~$23.45 (vs $22 AWS = +7%)
- **Value:** $0.055 per hour saved

**Rationale:**
- Embarrassingly parallel workload (336 independent partitions)
- 72 vCPUs reduces batches from 10.5 → 4.67
- Network latency (97 min) is fixed; shorter compute time overcomes it
- Finish in ~1.2 days instead of 2.3 days

---

## AIRTABLE UPDATES REQUIRED

### 1. UPDATE STAGE 2.3 - Currency Indices

**Navigate to:** BQX ML Phase 2 base → PM table → Stage BQX-2.3

**Fields to Update:**

| Field | OLD Value | NEW Value |
|-------|-----------|-----------|
| **Infrastructure** | c7i.8xlarge Spot (32 vCPUs) | Azure F72s_v2 Spot (72 vCPUs, East US) |
| **Duration** | 20 hours | 9-10 hours |
| **Duration (numeric)** | 20 | 9.5 |
| **Cost** | $8 | $7 |
| **Notes/Description** | Add: "Executing on Azure F72s_v2 Spot (72 vCPUs, 144 GB RAM). 2.25x faster than AWS baseline due to higher parallelization (4.67 batches vs 10.5). Network latency offset by compute speed." |

**Keep Unchanged:**
- Features: 224
- Scope: Currency-Related
- Status: Todo (or update as needed)

---

### 2. UPDATE STAGE 2.4 - Triangular Arbitrage

**Navigate to:** BQX ML Phase 2 base → PM table → Stage BQX-2.4

**Fields to Update:**

| Field | OLD Value | NEW Value |
|-------|-----------|-----------|
| **Infrastructure** | c7i.8xlarge Spot (32 vCPUs) | Azure F72s_v2 Spot (72 vCPUs, East US) |
| **Duration** | 20 hours | 9-10 hours |
| **Duration (numeric)** | 20 | 9.5 |
| **Cost** | $8 | $7 |
| **Notes/Description** | Add: "Executing on Azure F72s_v2 Spot (same instance as Stage 2.3). Cross-pair arbitrage features benefit from high parallelization." |

**Keep Unchanged:**
- Features: 112
- Scope: Currency-Related
- Status: Todo

---

### 3. UPDATE STAGE 2.16B - Expand Currency Blocs

**Navigate to:** BQX ML Phase 2 base → PM table → Stage BQX-2.16B

**Fields to Update:**

| Field | OLD Value | NEW Value |
|-------|-----------|-----------|
| **Infrastructure** | c7i.8xlarge Spot (32 vCPUs) | Azure F72s_v2 Spot (72 vCPUs, East US) |
| **Duration** | 15 hours | 7-8 hours |
| **Duration (numeric)** | 15 | 7.5 |
| **Cost** | $6 | $5 |
| **Notes/Description** | Add: "Executing on Azure F72s_v2 Spot. USD-centric, commodity, and safe-haven bloc features." |

**Keep Unchanged:**
- Features: 48
- Scope: Currency-Related
- Status: Todo

---

### 4. UPDATE OR ADD INFRASTRUCTURE STAGE

**Option A:** Update existing Stage 2.10 (Infrastructure Management)

**Navigate to:** BQX ML Phase 2 base → PM table → Stage BQX-2.10

**Fields to Update:**

| Field | OLD Value | NEW Value |
|-------|-----------|-----------|
| **Stage Name** | Infrastructure Management | TIER 1 Azure Infrastructure Setup |
| **Description** | Update to: "Launch Azure Standard_F72s_v2 Spot instance (72 vCPUs, 144 GB RAM) in East US region. Configure cross-cloud connectivity to AWS Aurora RDS. Install dependencies and prepare environment for TIER 1 execution. Instance will run for ~29 hours total." |
| **Infrastructure** | Various | Azure F72s_v2 Spot (72 vCPUs, 144 GB, East US) |
| **Duration** | Variable | 2-3 hours (setup) + 28.6 hours (execution) = 30.6h total |
| **Cost** | Variable | $23 (compute) + $2 (network) = $25 total |
| **Notes** | Update to include: "Cross-cloud setup: Configure Aurora security group to allow Azure IP. Test connectivity. Total TIER 1 cost: $23.45 (48% faster than AWS baseline)." |

**OR Option B:** Create new Stage 2.10A for Azure infrastructure

**If creating new stage:**

| Field | Value |
|-------|-------|
| **Stage ID** | BQX-2.10A |
| **Stage Name** | TIER 1 Azure F72s_v2 Setup |
| **Phase** | Phase 2 |
| **Type** | Infrastructure |
| **Description** | "Launch and configure Azure Standard_F72s_v2 Spot instance for TIER 1 execution. Setup cross-cloud connectivity to AWS Aurora RDS. Install Python dependencies and prepare execution environment." |
| **Infrastructure** | Azure F72s_v2 Spot (72 vCPUs, 144 GB RAM, East US) |
| **Duration** | 2-3 hours |
| **Cost** | $2-3 |
| **Dependencies** | Stage 2.15 (validation complete) |
| **Deliverables** | "Azure VM ready, Aurora connectivity verified, TIER 1 scripts deployed" |
| **Status** | Todo |

---

### 5. UPDATE STAGE 2.14 and 2.15 (Previously Pending)

**Stage 2.14 - Term Covariance Features:**

| Field | Update Value |
|-------|--------------|
| **Status** | Done |
| **Completion Date** | 2025-11-17 |
| **Notes** | "Completed 2025-11-17 06:09 UTC. Results: 336 partitions (28 pairs × 12 months), 10,313,378 rows updated, 1,008 features added (36 per pair), 4.54 hours duration. All 13 initial errors recovered and reprocessed successfully." |

**Stage 2.15 - Comprehensive Validation:**

| Field | Update Value |
|-------|--------------|
| **Status** | Done |
| **Completion Date** | 2025-11-17 |
| **Notes** | "Completed 2025-11-17 12:52 UTC. Results: All 3 validation checks passed (Schema Consistency, Column Structure, Data Completeness). Validated 336 partitions with 79 columns (1 + 42 regression + 36 covariance), 10,313,378 total rows. Phase 2 Foundation Complete." |

---

## SUMMARY OF TIER 1 CHANGES

### Before (AWS c7i.8xlarge Plan):

| Stage | Duration | Cost | Infrastructure |
|-------|----------|------|----------------|
| 2.3 - Currency Indices | 20h | $8 | c7i.8xlarge Spot (32 vCPUs) |
| 2.4 - Triangular Arbitrage | 20h | $8 | c7i.8xlarge Spot (32 vCPUs) |
| 2.16B - Currency Blocs | 15h | $6 | c7i.8xlarge Spot (32 vCPUs) |
| **TOTAL** | **55h** | **$22** | AWS us-east-1 |

### After (Azure F72s_v2 Plan):

| Stage | Duration | Cost | Infrastructure |
|-------|----------|------|----------------|
| 2.10A - Azure Setup | 2-3h | $2-3 | Azure F72s_v2 Spot setup |
| 2.3 - Currency Indices | 9.5h | $7 | Azure F72s_v2 Spot (72 vCPUs) |
| 2.4 - Triangular Arbitrage | 9.5h | $7 | Azure F72s_v2 Spot (72 vCPUs) |
| 2.16B - Currency Blocs | 7.5h | $5 | Azure F72s_v2 Spot (72 vCPUs) |
| **TOTAL** | **28.6h** | **$23.45** | Azure East US |

### Improvements:

- **Duration:** 55h → 28.6h (**-48%** faster)
- **Cost:** $22 → $23.45 (+7%, only $1.45 more)
- **Time Savings:** 26.4 hours
- **Value:** $0.055 per hour saved
- **Completion:** ~1.2 days instead of 2.3 days

---

## STEP-BY-STEP UPDATE INSTRUCTIONS

### Step 1: Navigate to AirTable

1. Open browser
2. Navigate to: https://airtable.com
3. Login to account
4. Select workspace: "BQX ML"
5. Open base: "BQX ML Phase 2 Stages" (app6VBiQlnq6yv0D7)
6. Open table: "PM"

### Step 2: Update Stage 2.14

1. Find record: "BQX-2.14"
2. Click to open full record
3. Update fields as shown above
4. Save changes

### Step 3: Update Stage 2.15

1. Find record: "BQX-2.15"
2. Click to open full record
3. Update fields as shown above
4. Save changes

### Step 4: Update Stage 2.3

1. Find record: "BQX-2.3"
2. Click to open full record
3. Update all fields per table above
4. Special attention to:
   - Duration: 9.5 hours
   - Cost: $7
   - Infrastructure: Azure F72s_v2 Spot (72 vCPUs, East US)
5. Save changes

### Step 5: Update Stage 2.4

1. Find record: "BQX-2.4"
2. Update all fields per table above
3. Save changes

### Step 6: Update Stage 2.16B

1. Find record: "BQX-2.16B"
2. Update all fields per table above
3. Save changes

### Step 7: Update or Create Infrastructure Stage

Choose Option A (update 2.10) OR Option B (create 2.10A)

**If Option A:**
1. Find record: "BQX-2.10"
2. Update all fields per table above
3. Save changes

**If Option B:**
1. Click "+" to add new record
2. Fill in all fields per table above
3. Save changes

### Step 8: Verify Updates

1. Filter view: Phase = "Phase 2"
2. Sort by: Stage ID
3. Verify all TIER 1 stages show updated values:
   - BQX-2.3: 9.5h, $7, Azure F72s_v2
   - BQX-2.4: 9.5h, $7, Azure F72s_v2
   - BQX-2.16B: 7.5h, $5, Azure F72s_v2
4. Verify Phase 2 foundation stages marked Done:
   - BQX-2.14: Status = "Done"
   - BQX-2.15: Status = "Done"

---

## OPTIONAL: ADD COMPARISON NOTE

**Consider adding a note field or comment:**

```
TIER 1 Infrastructure Decision (2025-11-17):

EVALUATED OPTIONS:
- AWS c7i.8xlarge Spot (32 vCPUs): 55h, $22 (baseline)
- Azure F48s_v2 Spot (48 vCPUs): 42h, $21.32 (-24% time, -3% cost)
- Azure F72s_v2 Spot (72 vCPUs): 28.6h, $23.45 (-48% time, +7% cost) ✅ SELECTED
- GCP n2-standard-80 Spot (80 vCPUs): 26.6h, $23.04 (-52% time, +5% cost)

SELECTED: Azure F72s_v2 Spot
RATIONALE: Best balance of speed and cost. 48% faster execution for only $1.45 more. Stable Azure Spot pricing. Finish in ~1.2 days vs 2.3 days.

ANALYSIS: docs/large_vcpu_tier1_analysis_2025_11_17.md
```

---

## COMPLETION CHECKLIST

- [ ] Stage 2.14 updated to "Done" with completion notes
- [ ] Stage 2.15 updated to "Done" with completion notes
- [ ] Stage 2.3 duration updated to 9.5 hours
- [ ] Stage 2.3 cost updated to $7
- [ ] Stage 2.3 infrastructure updated to Azure F72s_v2 Spot
- [ ] Stage 2.4 duration updated to 9.5 hours
- [ ] Stage 2.4 cost updated to $7
- [ ] Stage 2.4 infrastructure updated to Azure F72s_v2 Spot
- [ ] Stage 2.16B duration updated to 7.5 hours
- [ ] Stage 2.16B cost updated to $5
- [ ] Stage 2.16B infrastructure updated to Azure F72s_v2 Spot
- [ ] Infrastructure stage (2.10 or 2.10A) updated/created
- [ ] All updates verified in PM table view
- [ ] (Optional) Comparison note added

---

## ESTIMATED TIME

**Total manual update time:** 10-15 minutes

**Breakdown:**
- Stage 2.14 update: 2 min
- Stage 2.15 update: 2 min
- Stage 2.3 update: 2 min
- Stage 2.4 update: 2 min
- Stage 2.16B update: 2 min
- Infrastructure stage: 3 min
- Verification: 2 min

---

## NEXT STEPS AFTER AIRTABLE UPDATE

1. **Create Azure infrastructure scripts**
   - Launch Azure F72s_v2 Spot instance
   - Configure cross-cloud connectivity
   - Install dependencies

2. **Test connectivity**
   - Verify Azure → AWS Aurora connection
   - Test database queries
   - Validate performance

3. **Execute TIER 1**
   - Stage 2.3: Currency Indices (~9.5h)
   - Stage 2.4: Triangular Arbitrage (~9.5h)
   - Stage 2.16B: Currency Blocs (~7.5h)

4. **Update AirTable progress**
   - Mark stages "In Progress" when started
   - Mark stages "Done" when completed
   - Add completion notes

5. **Terminate Azure instance**
   - After TIER 1 completion
   - Document final costs
   - Create completion report

---

**Document Created:** 2025-11-17
**Purpose:** Manual AirTable update for approved Azure F72s_v2 TIER 1 plan
**Approval:** Azure F72s_v2 Spot (72 vCPUs) - Best Balance recommendation approved by user
**Impact:** 48% faster TIER 1 execution (~1.2 days vs 2.3 days) for +$1.45

