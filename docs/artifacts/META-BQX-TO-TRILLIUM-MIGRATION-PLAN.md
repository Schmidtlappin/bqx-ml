# META Project: Trillium AWS to Trillium AWS Migration Plan

**Date:** 2025-11-04
**Owner:** RM-001 (RobkeiRingMaster)
**Priority:** CRITICAL
**Status:** IN PROGRESS

---

## Executive Summary

**CRITICAL ISSUE:** Trillium AWS account (543634432604) is scheduled for deletion. All META project work (MP-META-001, WP-4.1, WP-4.2) has been occurring in the deprecated Trillium AWS account. Additionally, WP-4.1 gang tables were created in the wrong Airtable base (Robkei-Ring instead of Robkei-Engine). This document provides the complete migration plan to Trillium AWS (543634432604) with Robkei-Engine base (appIjM4NtqxkM0rcr) and sanitization of all planning documents.

**IMPACT:**
- **AWS Account:** Current session runs in Trillium AWS (543634432604) ❌ → Must switch to Trillium AWS (543634432604) ✅
- **Airtable Base:** WP-4.1 tables created in Robkei-Ring (appIjM4NtqxkM0rcr) ❌ → Must migrate to Robkei-Engine (appIjM4NtqxkM0rcr) ✅
- **Credentials:** Already synced to Trillium AWS ✅
- **Planning Docs:** 29+ files reference Trillium AWS ❌

**OUTCOME:** 100% Trillium AWS + Robkei-Engine base centric operations for all future META work.

---

## Current State Assessment

### ⚠️ AT RISK: Airtable Data in Wrong Base

WP-4.1 gang tables were created in **Robkei-Engine base** (appIjM4NtqxkM0rcr):
- **Gangs table** (29 fields, pre-existing)
- **GangMemberships table** (13 fields, created 2025-11-04)
- **GangCapabilities table** (9 fields, created 2025-11-04)
- **GangCoordination table** (14 fields, created 2025-11-04)

**PROBLEM:** Production agents use **Robkei-Engine base** (appIjM4NtqxkM0rcr), NOT Robkei-Engine base.

**Evidence:**
- Agent runtime code (`/home/ubuntu/Robkei-Ring/agent-runtime/airtable_client.py:28`) configured for Robkei-Engine base
- Robkei-Engine base already has: Plans, Phases, Stages, Tasks, Todos, Gangs, Mandates, Resources tables
- 8 Trillium agents (RM-001, MON-001, UP-001, etc.) running against Robkei-Engine base

**Status:** ❌ Gang tables in wrong base. Must migrate to Robkei-Engine base for production consistency.

### ✅ SAFE: Credentials Synced to Trillium

Per [CREDENTIAL-SYNC-SUMMARY.md](CREDENTIAL-SYNC-SUMMARY.md) (2025-11-03):
- `robkei-engine/airtable/api-token` → **EXISTS in Trillium AWS** ✅
- `robkei-engine/airtable/api-token` → **EXISTS in Trillium AWS** ✅
- All 13 critical credentials synced → **100% success**

**Verification (2025-11-04):**
```bash
AWS Account: 543634432604 (Trillium)
✅ robkei-engine/airtable/api-token EXISTS
✅ robkei-engine/airtable/api-token EXISTS
```

### ❌ AT RISK: Current Session Context

**Current Session:**
```json
{
  "Account": "543634432604",
  "Arn": "arn:aws:sts::543634432604:assumed-role/Robkei-DeveloperRole/i-0e0ae4a81437a9bca"
}
```

**Status:** ❌ Running in deprecated Trillium AWS account.

### ❌ AT RISK: Planning Documents

**29 files contain Trillium AWS references:**
- Account ID: 543634432604
- Secret paths: `bqx/airtable/*`, `bqx/api/*`
- "Trillium AWS" text references

**Status:** ❌ Requires sanitization.

---

## Migration Plan

### Phase 1: Immediate Context Switch ⚡ CRITICAL

**Objective:** Stop using Trillium AWS immediately for all META operations.

#### Action 1.1: Switch to Trillium AWS Context

**Create context switch script:**

```bash
#!/bin/bash
# /tmp/switch-to-trillium.sh
# Purpose: Switch current shell to Trillium AWS context

set -e

echo "=== Switching to Trillium AWS ==="

# Load Trillium credentials from BQX Secrets Manager (one last time)
TRILLIUM_CREDS=$(aws secretsmanager get-secret-value \
  --secret-id trillium/aws/iam-user-access-keys \
  --query SecretString \
  --output text)

export AWS_ACCESS_KEY_ID=$(echo "$TRILLIUM_CREDS" | jq -r '.AccessKeyId')
export AWS_SECRET_ACCESS_KEY=$(echo "$TRILLIUM_CREDS" | jq -r '.SecretAccessKey')
export AWS_DEFAULT_REGION=us-east-1

# Verify context
IDENTITY=$(aws sts get-caller-identity)
ACCOUNT=$(echo "$IDENTITY" | jq -r '.Account')

if [ "$ACCOUNT" = "543634432604" ]; then
    echo "✅ Successfully switched to Trillium AWS (543634432604)"
    echo "$IDENTITY" | jq .
else
    echo "❌ Failed to switch to Trillium AWS"
    echo "Current account: $ACCOUNT"
    exit 1
fi

# Test Airtable credentials access
echo ""
echo "Testing Airtable credentials..."
aws secretsmanager get-secret-value \
  --secret-id robkei-engine/airtable/api-token \
  --query SecretString \
  --output text > /tmp/airtable_key.txt

echo "✅ Airtable credentials loaded from Trillium AWS"
echo ""
echo "🎉 Now operating in Trillium AWS"
echo "   Account: 543634432604"
echo "   Region: us-east-1"
```

**Execute:**
```bash
chmod +x /tmp/switch-to-trillium.sh
source /tmp/switch-to-trillium.sh
```

**Verification:**
- `aws sts get-caller-identity` should show Account: 543634432604
- `/tmp/airtable_key.txt` should contain credentials from Trillium AWS

**Duration:** 5 minutes
**Owner:** RM-001
**Status:** TO DO NOW

#### Action 1.2: Update Airtable Credentials Source

**Current:** Credentials loaded from Trillium AWS `robkei-engine/airtable/api-token`
**New:** Credentials loaded from Trillium AWS `robkei-engine/airtable/api-token`

**Update all scripts to use:**
```bash
# OLD (Trillium AWS) - DO NOT USE
aws secretsmanager get-secret-value --secret-id robkei-engine/airtable/api-token

# NEW (Trillium AWS) - USE THIS
aws secretsmanager get-secret-value --secret-id robkei-engine/airtable/api-token
```

**Duration:** 10 minutes
**Owner:** RM-001
**Status:** TO DO NOW

---

### Phase 2: Airtable Base Migration 🔄 CRITICAL

**Objective:** Migrate WP-4.1 gang tables from Robkei-Engine base to Robkei-Engine base.

#### Action 2.1: Verify Robkei-Engine Base Structure

**Verify existing infrastructure in Robkei-Engine base:**

```bash
# Switch to Trillium AWS context first
source /tmp/switch-to-trillium.sh

# Load Airtable credentials
AIRTABLE_TOKEN=$(aws secretsmanager get-secret-value \
  --secret-id robkei-engine/airtable/api-token \
  --query SecretString --output text | jq -r '.token')

# List tables in Robkei-Engine base
curl -H "Authorization: Bearer $AIRTABLE_TOKEN" \
  "https://api.airtable.com/v0/meta/bases/appIjM4NtqxkM0rcr/tables" | jq '.tables[] | {id, name}'
```

**Expected findings:**
- ✅ Gangs table already exists (ID: tblXXXXXXXXXXXXXX)
- ✅ Plans, Phases, Stages, Tasks, Todos tables exist
- ✅ Mandates, Resources tables exist

**Duration:** 15 minutes
**Owner:** RM-001
**Status:** TO DO AFTER PHASE 1

#### Action 2.2: Create Gang Management Tables in Robkei-Engine Base

**Tables to create in Robkei-Engine base:**

1. **GangMemberships** (13 fields)
   - Link to existing Gangs table in Robkei-Engine
   - Same schema as created in Robkei-Ring

2. **GangCapabilities** (9 fields)
   - Link to existing Gangs table in Robkei-Engine
   - Same schema as created in Robkei-Ring

3. **GangCoordination** (14 fields)
   - Link to existing Gangs table in Robkei-Engine
   - Same schema as created in Robkei-Ring

**Process:**
- Use Airtable API (via Trillium AWS credentials)
- Target base: appIjM4NtqxkM0rcr (Robkei-Engine)
- Replicate exact schemas from WP-4.1 specifications
- Create relationships to existing Gangs table

**Duration:** 2 hours
**Owner:** RM-001
**Status:** TO DO AFTER 2.1

#### Action 2.3: Migrate GANG-META-INFRA-001 Test Data

**Migrate test data from Robkei-Ring to Robkei-Engine:**

1. Export data from Robkei-Engine base:
   - GANG-META-INFRA-001 gang record
   - 7 membership records (ARCH-001, DATA-001, INFRA-001, QA-001, COORD-001, SECRET-001, MON-001)
   - Capability records
   - Coordination records

2. Transform data (update record IDs to match new Robkei-Engine tables)

3. Import into Robkei-Engine base

**Duration:** 1 hour
**Owner:** RM-001
**Status:** TO DO AFTER 2.2

#### Action 2.4: Validate Migration

**Validation checklist:**
- [ ] All 3 gang management tables exist in Robkei-Engine base
- [ ] Relationships to Gangs table working
- [ ] GANG-META-INFRA-001 data migrated successfully
- [ ] 7 membership records present
- [ ] API queries work from Trillium AWS context

**Duration:** 30 minutes
**Owner:** RM-001
**Status:** TO DO AFTER 2.3

#### Action 2.5: Deprecate Robkei-Ring Gang Tables

**After successful migration:**
1. Add deprecation notice to Robkei-Ring tables
2. Mark tables as "READ-ONLY - MIGRATED TO ROBKEI-ENGINE"
3. Do NOT delete (keep for historical reference)

**Duration:** 15 minutes
**Owner:** RM-001
**Status:** TO DO AFTER 2.4

**Phase 2 Total Duration:** 4 hours

---

### Phase 3: Document Sanitization 📝

**Objective:** Remove all Trillium AWS references from planning documents.

#### Action 3.1: Sanitize Core META Planning Documents

**Files to Update (Priority 1 - META Core):**

1. **MP-META-001-ORCHESTRATION.md**
   - Remove: Account 543634432604 references
   - Add: Trillium AWS (543634432604) context
   - Add: "ALL META OPERATIONS IN TRILLIUM AWS ONLY" directive

2. **MP-META-001-EXECUTION-SEQUENCE.md**
   - Add: Trillium AWS context at top
   - Add: Credential source clarification

3. **WP-4.1-*.md** (8 files)
   - Update: Airtable credential source (BQX → Trillium)
   - Add: Trillium AWS context

4. **WP-4.2-EXECUTION-BRIEFING-COORD-QA.md**
   - Update: AWS account context
   - Update: Credential paths

**Search & Replace:**
```bash
# Account ID references
543634432604 → 543634432604

# Airtable base references
appIjM4NtqxkM0rcr → appIjM4NtqxkM0rcr
Robkei-Engine base → Robkei-Engine base
RobkeiRing base → Robkei-Engine base

# Credential paths
robkei-engine/airtable/api-token → robkei-engine/airtable/api-token
robkei-engine/api/anthropic → robkei-engine/api/anthropic

# Text references
"Trillium AWS" → "Trillium AWS"
"Trillium account" → "Trillium account"
```

**Duration:** 2 hours
**Owner:** RM-001
**Status:** TO DO AFTER PHASE 2

#### Action 3.2: Sanitize Historical/Reference Documents

**Files to Update (Priority 2 - Historical Context):**

Add deprecation notice at top of historical documents:

```markdown
> **HISTORICAL DOCUMENT NOTICE:**
> This document contains references to Trillium AWS account (543634432604), which is deprecated and scheduled for deletion.
> All current operations use Trillium AWS account (543634432604).
> Trillium AWS references preserved for historical accuracy only.
```

**Files:**
- CREDENTIAL-SYNC-SUMMARY.md (already documents the sync)
- PRODUCTION-RUNTIME-ARCHITECTURE.md
- MP-ENGINE-001-STATUS-REPORT-FINAL.md
- ROBKEI-ENGINE-*.md files
- agent-provisioning-*.md files
- planning-phase-summary.md
- implementation-plan-summary.md

**Duration:** 1 hour
**Owner:** RM-001
**Status:** TO DO AFTER 3.1

#### Action 3.3: Sanitize Repository Root Files

**Files to Check:**
- BQX-MASTER-COORDINATION-INSTRUCTIONS.md
- TRILLIUM-MIGRATION-PLAN.md (update status: "COMPLETE")
- HANDOFF.md
- .claude/commands/*.md

**Duration:** 30 minutes
**Owner:** RM-001
**Status:** TO DO AFTER 3.2

---

### Phase 4: Future-Proof Directives 🛡️

**Objective:** Ensure all future work uses Trillium AWS + Robkei-Engine base only.

#### Action 4.1: Create META-AWS-CONTEXT.md Directive

**Create new L1 Global Intelligence file:**

**File:** `/sandbox/artifacts/META-AWS-CONTEXT.md`

**Content:**
```markdown
# META Project AWS & Airtable Context

**CRITICAL DIRECTIVE:** All META project operations MUST use Trillium AWS account (543634432604) and Robkei-Engine Airtable base (appIjM4NtqxkM0rcr) ONLY.

## AWS Account for META Operations

**Trillium AWS (Production):**
- **Account ID:** 543634432604
- **Region:** us-east-1
- **Status:** ✅ ACTIVE - PRIMARY PRODUCTION ACCOUNT
- **Use Case:** ALL META operations (MP-META-001, all work packages)

**Trillium AWS (Deprecated):**
- **Account ID:** 543634432604
- **Status:** ❌ DEPRECATED - SCHEDULED FOR DELETION
- **Use Case:** NONE - DO NOT USE

## Airtable Base for META Operations

**Robkei-Engine Base (Production):**
- **Base ID:** appIjM4NtqxkM0rcr
- **Base Name:** Robkei-Engine
- **Status:** ✅ ACTIVE - PRIMARY PRODUCTION BASE
- **Use Case:** ALL META operations, production agents
- **Tables:** Plans, Phases, Stages, Tasks, Todos, Gangs, GangMemberships, GangCapabilities, GangCoordination, Mandates, Resources, Agents

**Robkei-Ring Base (Deprecated for META):**
- **Base ID:** appIjM4NtqxkM0rcr
- **Base Name:** Robkei-Ring
- **Status:** ❌ DEPRECATED FOR META - Use Robkei-Engine instead
- **Use Case:** Historical reference only, DO NOT USE for new META work

## Credential Sources

### Airtable API Token
**Primary:** `robkei-engine/airtable/api-token` (Trillium AWS Secrets Manager)

### AI API Keys
**Primary:** `robkei-engine/api/anthropic` (Trillium AWS Secrets Manager)

### All Other Credentials
**Primary:** `robkei-engine/*` prefix in Trillium AWS Secrets Manager

## Context Switching

**To switch to Trillium AWS:**
```bash
source /tmp/switch-to-trillium.sh
```

**To verify current context:**
```bash
aws sts get-caller-identity | jq -r '.Account'
# Expected output: 543634432604
```

## Enforcement

**ALL agents MUST:**
1. Verify AWS context before operations: `aws sts get-caller-identity`
2. Confirm Account ID = 543634432604 (Trillium)
3. Use `robkei-engine/*` credential paths
4. Report any Trillium AWS references found in documentation

**COMPLY-001 Validation:**
- Before any META operation: Verify Trillium AWS context
- Block operations in Trillium AWS (543634432604)

---

**Status:** ✅ ACTIVE - Effective 2025-11-04
**Authority:** RM-001, UP-001
**Compliance:** MANDATORY
```

**Duration:** 30 minutes
**Owner:** RM-001
**Status:** TO DO AFTER PHASE 3

#### Action 4.2: Update L1-GLOBAL-INTELLIGENCE-INDEX.md

**Add new section:**

```markdown
### 7. META Project AWS Context

**[META-AWS-CONTEXT.md](META-AWS-CONTEXT.md)** (✅ EXISTS - NEW)
- **Purpose:** CRITICAL directive for AWS account context in META operations
- **Content:**
  - Trillium AWS (543634432604) = PRIMARY PRODUCTION ACCOUNT
  - Trillium AWS (543634432604) = DEPRECATED, DO NOT USE
  - Credential sources (robkei-engine/* prefix)
  - Context switching procedure
  - Enforcement by COMPLY-001
- **Why Important:** Prevents accidental operations in deprecated Trillium AWS
- **Created:** 2025-11-04
- **Size:** ~2 KB
```

**Duration:** 10 minutes
**Owner:** RM-001
**Status:** TO DO AFTER 4.1

#### Action 4.3: Update MP-META-001-ORCHESTRATION.md Header

**Add at top (after title):**

```markdown
---

## AWS CONTEXT FOR META OPERATIONS

**CRITICAL:** All META operations MUST use Trillium AWS account (543634432604) ONLY.

**Primary Account:** Trillium AWS (543634432604)
**Credentials:** `robkei-engine/*` prefix in Trillium AWS Secrets Manager
**Status:** ✅ ACTIVE - PRIMARY PRODUCTION ACCOUNT

**Deprecated Account:** Trillium AWS (543634432604) - **DO NOT USE** ❌
**Status:** SCHEDULED FOR DELETION

**Compliance:** See [META-AWS-CONTEXT.md](../META-AWS-CONTEXT.md) for details.

---
```

**Duration:** 5 minutes
**Owner:** RM-001
**Status:** TO DO AFTER 4.2

---

### Phase 5: Validation & Testing ✅

**Objective:** Verify migration completeness, Trillium AWS operations, and Robkei-Engine base access.

#### Action 5.1: Test Airtable Operations in Trillium Context with Robkei-Engine Base

**Test Plan:**
1. Switch to Trillium AWS context: `source /tmp/switch-to-trillium.sh`
2. Load Airtable credentials from Trillium: `robkei-engine/airtable/api-token`
3. Target base: `appIjM4NtqxkM0rcr` (Robkei-Engine)
4. Query gang tables in Robkei-Engine base:
   - Gangs
   - GangMemberships (newly migrated)
   - GangCapabilities (newly migrated)
   - GangCoordination (newly migrated)
5. Verify GANG-META-INFRA-001 data accessible
6. Verify 7 membership records present
7. Perform test write operation (e.g., add test gang member record)
8. Verify write successful
9. Delete test record

**Expected Result:** 100% success accessing and modifying Airtable data in Robkei-Engine base from Trillium AWS context.

**Duration:** 30 minutes
**Owner:** RM-001
**Status:** TO DO AFTER PHASE 4

#### Action 5.2: Scan for Remaining Trillium AWS and Robkei-Ring References

**Scan command:**
```bash
cd /home/ubuntu/Robkei-Ring
# Scan for Trillium AWS references
grep -r "543634432604" sandbox/artifacts/projects/ sandbox/artifacts/WP-* 2>/dev/null | wc -l
grep -r "bqx/airtable" sandbox/artifacts/projects/ sandbox/artifacts/WP-* 2>/dev/null | wc -l

# Scan for Robkei-Engine base references
grep -r "appIjM4NtqxkM0rcr" sandbox/artifacts/projects/ sandbox/artifacts/WP-* 2>/dev/null | wc -l
grep -r "Robkei-Engine base\|RobkeiRing base" sandbox/artifacts/projects/ sandbox/artifacts/WP-* 2>/dev/null | wc -l
```

**Expected Result:** 0 matches in active planning documents (projects/, WP-*).

**If matches found:** Update those documents per Phase 3 procedures.

**Duration:** 15 minutes
**Owner:** RM-001
**Status:** TO DO AFTER PHASE 3

#### Action 5.3: Verify All Agents Can Access Trillium AWS + Robkei-Engine Base

**Once agent infrastructure is built:**
1. Test each agent can assume Trillium AWS context
2. Test each agent can access `robkei-engine/*` secrets
3. Test each agent can query/modify Airtable in Robkei-Engine base via Trillium credentials

**Duration:** 1 hour
**Owner:** INFRA-001, QA-001
**Status:** TO DO AFTER AGENT INFRASTRUCTURE COMPLETE

---

## Migration Checklist

### ⚡ Phase 1: Immediate (Do Now - 15 minutes)
- [ ] Execute `/tmp/switch-to-trillium.sh` to switch AWS context
- [ ] Verify AWS context: `aws sts get-caller-identity` → 543634432604
- [ ] Update Airtable credential source in current work
- [ ] Load credentials from `robkei-engine/airtable/api-token`

### 🔄 Phase 2: Airtable Base Migration (4 hours)
- [ ] Verify Robkei-Engine base structure
- [ ] Create GangMemberships table in Robkei-Engine base
- [ ] Create GangCapabilities table in Robkei-Engine base
- [ ] Create GangCoordination table in Robkei-Engine base
- [ ] Migrate GANG-META-INFRA-001 test data
- [ ] Validate migration (3 tables + data)
- [ ] Deprecate Robkei-Ring gang tables (mark READ-ONLY)

### 📝 Phase 3: Document Sanitization (3.5 hours)
- [ ] Sanitize MP-META-001-ORCHESTRATION.md (BQX → Trillium, Robkei-Ring → Robkei-Engine)
- [ ] Sanitize MP-META-001-EXECUTION-SEQUENCE.md
- [ ] Sanitize all WP-4.1-*.md files (8 files) - Update base references
- [ ] Sanitize WP-4.2-EXECUTION-BRIEFING-COORD-QA.md
- [ ] Add deprecation notices to historical documents (29 files)
- [ ] Sanitize repository root files (BQX-MASTER-*, HANDOFF.md, etc.)

### 🛡️ Phase 4: Future-Proof Directives (45 minutes)
- [ ] Create META-AWS-CONTEXT.md directive
- [ ] Update L1-GLOBAL-INTELLIGENCE-INDEX.md
- [ ] Update MP-META-001-ORCHESTRATION.md header

### ✅ Phase 5: Validation & Testing (1.25 hours)
- [ ] Test Airtable operations in Trillium context with Robkei-Engine base
- [ ] Scan for remaining Trillium AWS and Robkei-Ring references
- [ ] Verify all agents can access Trillium AWS + Robkei-Engine base (when built)

---

## Success Criteria

**Migration Complete When:**
1. ✅ All META operations use Trillium AWS (543634432604)
2. ✅ All META operations use Robkei-Engine base (appIjM4NtqxkM0rcr)
3. ✅ All credentials loaded from `robkei-engine/*` prefix
4. ✅ Gang management tables migrated to Robkei-Engine base
5. ✅ Core planning documents sanitized (0 BQX/Robkei-Ring references in active docs)
6. ✅ META-AWS-CONTEXT.md directive created and enforced
7. ✅ Airtable operations tested successfully in Trillium + Robkei-Engine context
8. ✅ All agents (when built) configured for Trillium AWS + Robkei-Engine base

**Verification:**
```bash
# Current AWS context
aws sts get-caller-identity | jq -r '.Account'
# Expected: 543634432604

# Current Airtable base (should be Robkei-Engine)
grep -r "appIjM4NtqxkM0rcr" sandbox/artifacts/WP-4.1*.md | head -1
# Expected: Multiple matches showing Robkei-Engine base

# Credential source
grep -r "robkei-engine/airtable" sandbox/artifacts/projects/MP-META-001*.md
# Expected: All instances use robkei-engine prefix

# Trillium AWS references in active planning
grep -r "543634432604\|bqx/airtable" sandbox/artifacts/projects/MP-META-001*.md sandbox/artifacts/WP-4*.md
# Expected: 0 matches (or only in historical notice comments)

# Robkei-Engine base references in active planning
grep -r "appIjM4NtqxkM0rcr\|Robkei-Engine base" sandbox/artifacts/projects/MP-META-001*.md sandbox/artifacts/WP-4*.md
# Expected: 0 matches (or only in historical notice comments)
```

---

## Rollback Plan

**If migration issues occur:**

1. **Immediate:** Revert to Trillium AWS context (NOT RECOMMENDED - temporary only)
   ```bash
   unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
   # This will revert to EC2 instance profile (Trillium AWS)
   ```

2. **Restore credentials:** Load from BQX Secrets Manager
   ```bash
   aws secretsmanager get-secret-value --secret-id robkei-engine/airtable/api-token
   ```

3. **Identify issue:** Why Trillium context failed
4. **Remediate:** Fix Trillium AWS access issue
5. **Re-attempt:** Switch back to Trillium AWS

**Note:** Rollback is TEMPORARY ONLY. Trillium AWS is scheduled for deletion. Trillium migration is MANDATORY.

---

## Timeline

**Total Effort:** ~9.5 hours across 5 phases

**Phase 1 - Immediate (Today, 2025-11-04):**
- Context switch to Trillium AWS: 15 minutes

**Phase 2 - Airtable Base Migration (Today/Tomorrow):**
- Verify + Create tables + Migrate data + Validate: 4 hours

**Phase 3 - Document Sanitization (This Week):**
- Core docs: 2 hours
- Historical docs: 1 hour
- Repository root: 30 minutes
- **Subtotal:** 3.5 hours

**Phase 4 - Future-Proof Directives (This Week):**
- META-AWS-CONTEXT.md + Updates: 45 minutes

**Phase 5 - Validation & Testing (This Week):**
- Airtable testing + Scanning: 1.25 hours

**Ongoing:**
- Agent verification (as agents are built)
- Monitoring & enforcement

---

## Risk Assessment

### HIGH RISK (Mitigated)
**Risk:** Lose access to Airtable data
**Mitigation:** ✅ Data is cloud-hosted (Airtable), independent of AWS account
**Status:** MITIGATED

### MEDIUM RISK (Mitigated)
**Risk:** Credentials not accessible in Trillium AWS
**Mitigation:** ✅ Verified all credentials exist in Trillium (2025-11-04)
**Status:** MITIGATED

### LOW RISK
**Risk:** Documentation references out of sync
**Mitigation:** Comprehensive sanitization plan (Phase 2)
**Status:** MANAGED

### LOW RISK
**Risk:** Accidental Trillium AWS usage
**Mitigation:** META-AWS-CONTEXT.md directive + COMPLY-001 enforcement
**Status:** MANAGED

---

## Communication Plan

**Inform:**
- All agents (when provisioned) via charge documents
- User (via this migration plan)
- Future RM-001 sessions (via handoff documents)

**Method:**
- Create META-AWS-CONTEXT.md (L1 Global Intelligence)
- Update MP-META-001-ORCHESTRATION.md header
- Add to L1-GLOBAL-INTELLIGENCE-INDEX.md
- Update .claude/handoff.md

---

## Appendix A: AWS Account Details

### Trillium AWS (Production)
- **Account ID:** 543634432604
- **Region:** us-east-1
- **Status:** ✅ ACTIVE
- **IAM User:** trillium
- **Credentials:** Available in Trillium AWS Secrets Manager (`trillium/aws/iam-user-access-keys`)
- **Use Case:** ALL META operations, primary production account

### Trillium AWS (Deprecated)
- **Account ID:** 543634432604
- **Region:** us-east-1
- **Status:** ❌ DEPRECATED - SCHEDULED FOR DELETION
- **Use Case:** NONE - Migration source only

---

## Appendix B: Credential Mapping

| Old (Trillium AWS) | New (Trillium AWS) | Status |
|---------------|-------------------|--------|
| `robkei-engine/airtable/api-token` | `robkei-engine/airtable/api-token` | ✅ Synced |
| `robkei-engine/api/anthropic` | `robkei-engine/api/anthropic` | ✅ Synced |
| `bqx/api/openai` | `robkei-engine/api/openai` | ✅ Synced |
| `bqx/api/groq` | `robkei-engine/api/groq` | ✅ Synced |
| `bqx/api/mistral` | `robkei-engine/api/mistral` | ✅ Synced |
| `bqx/api/xai` | `robkei-engine/api/xai` | ✅ Synced |
| `bqx/api/google-gemini` | `robkei-engine/api/google-gemini` | ✅ Synced |

**Naming Convention:**
- **Old:** `bqx/*` prefix (deprecated)
- **New:** `robkei-engine/*` prefix (production standard)

---

**Status:** 📋 PLAN READY - EXECUTE IMMEDIATELY
**Priority:** CRITICAL
**Owner:** RM-001
**Created:** 2025-11-04
**Version:** 1.0
