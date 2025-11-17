# AirTable API Investigation - 2025-11-17

**Date:** 2025-11-17 13:30 UTC
**Status:** ❌ **API Access Not Available for BQX ML Base**

---

## INVESTIGATION SUMMARY

Attempted to update AirTable programmatically using credentials from AWS Secrets Manager.

**Result:** Token lacks access to BQX ML Phase 2 base (app6VBiQlnq6yv0D7)

---

## AWS SECRETS MANAGER FINDINGS

### Available AirTable Secrets

| Secret Path | Contents |
|-------------|----------|
| `bqx/airtable/api-token` | Admin token (robkei-ringmaster-airtable-adminaccess-token) |
| `bqx-mirror/bqx/airtable/api-token` | Same admin token (duplicate) |
| `bqx-mirror/bqx/airtable/bases` | List of 3 accessible bases |
| `bqx-mirror/bqx-ml/airtable/base` | BQX-ML base metadata (unverified) |

### Token Details

**Token:** `pat***...***` (redacted - stored in AWS Secrets Manager)

**Name:** robkei-ringmaster-airtable-adminaccess-token

**Scopes:**
- all_workspaces_and_bases
- data.records:read
- data.records:write
- data.recordComments:read
- data.recordComments:write
- schema.bases:read
- schema.bases:write
- webhook:manage

**Created:** 2025-10-31

**Verified Working:** Yes (for specific bases only)

---

## BASE ACCESS TEST RESULTS

### Base 1: Robkei-Engine (appIjM4NtqxkM0rcr)

**Access:** ✅ **GRANTED**
**Status:** Verified working (2025-11-16)
**Tables:** 16
- Plans
- Phases
- Stages (contains WP-* work packages for Robkei Engine)
- Tasks
- Todos
- Others

**Content:** Robkei Engine project management (NOT BQX ML)

### Base 2: BQX-ML (appTkS66h75UwQJAh)

**Access:** ❌ **DENIED (403)**
**Status:** Unverified
**Error:** `INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND`

**Note from Secrets:**
> "Admin token from bqx-mirror/bqx/airtable/api-token returned 403. May need different token or base ID verification."

### Base 3: Robkei-Ring (appkKH0u1BhAHUao6)

**Access:** ❌ **DENIED (403)**
**Status:** Legacy base (unverified)
**Error:** `INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND`

### Base 4: BQX ML Phase 2 (app6VBiQlnq6yv0D7) - TARGET BASE

**Access:** ❌ **DENIED (403)**
**Status:** Target base for Stages 2.14, 2.15
**Error:** `INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND`

**Content:** BQX ML Phase 2 project stages (BQX-2.1 through BQX-2.20, etc.)

---

## FINDINGS

### Token Has Broad Scopes But Limited Base Access

The token claims to have `all_workspaces_and_bases` scope, but in practice only has access to:
- ✅ Robkei-Engine (appIjM4NtqxkM0rcr)

And **lacks access** to:
- ❌ BQX-ML (appTkS66h75UwQJAh)
- ❌ Robkei-Ring (appkKH0u1BhAHUao6)
- ❌ BQX ML Phase 2 (app6VBiQlnq6yv0D7)

### Possible Explanations

1. **Base Permissions:** Token may have been granted access to specific bases only
2. **Workspace Separation:** BQX ML bases may be in a different workspace
3. **Token Revocation:** Access may have been revoked after token creation
4. **Base Ownership:** Bases may be owned by a different account

### Base ID Discrepancy

**From AWS Secrets Manager:**
- BQX-ML base ID: `appTkS66h75UwQJAh`

**From Previous Sessions:**
- BQX ML Phase 2 base ID: `app6VBiQlnq6yv0D7`
- Table: `PM` (Project Management)

**Conclusion:** Two different bases exist:
1. `appTkS66h75UwQJAh` - General BQX-ML (unverified, no access)
2. `app6VBiQlnq6yv0D7` - BQX ML Phase 2 Stages (no access)

---

## ATTEMPTED SOLUTIONS

### Solution 1: Check All Secrets ✅ Done

**Action:** Searched AWS Secrets Manager for all AirTable-related secrets

**Result:** Found 9 AirTable secrets, all reference the same token

**Conclusion:** No alternative token available in AWS Secrets Manager

### Solution 2: Test All Base IDs ✅ Done

**Action:** Tested access to all known base IDs

**Result:** Only Robkei-Engine (appIjM4NtqxkM0rcr) accessible

**Conclusion:** Current token cannot access BQX ML bases

### Solution 3: Alternative Tokens ❌ Not Found

**Action:** Searched for additional tokens in AWS Secrets Manager

**Result:** All AirTable secrets reference the same token

**Conclusion:** No alternative token available

---

## RECOMMENDATIONS

### Immediate Solution: Manual Update (REQUIRED)

**Action:** Update AirTable via web UI

**Steps:**
1. Navigate to BQX ML Phase 2 base (app6VBiQlnq6yv0D7)
2. Open PM table
3. Update Stage 2.14:
   - Status → "Done"
   - Notes → "Completed 2025-11-17 06:09 UTC. Results: 336 partitions (28 pairs × 12 months), 10,313,378 rows updated, 1,008 features added (36 per pair), 4.54 hours duration. All 13 initial errors recovered and reprocessed successfully."
   - Completion Date → "2025-11-17"

4. Update Stage 2.15:
   - Status → "Done"
   - Notes → "Completed 2025-11-17 12:52 UTC. Results: All 3 validation checks passed (Schema Consistency, Column Structure, Data Completeness). Validated 336 partitions with 79 columns (1 + 42 regression + 36 covariance), 10,313,378 total rows. Phase 2 Foundation Complete."
   - Completion Date → "2025-11-17"

**Instructions:** [MANUAL_AIRTABLE_UPDATE_STAGE_2_14_2_15.md](MANUAL_AIRTABLE_UPDATE_STAGE_2_14_2_15.md)

**Time Required:** 5 minutes

### Long-Term Solution: Request New Token

**Action:** Generate new AirTable personal access token with access to BQX ML Phase 2 base

**Steps:**
1. Log into AirTable account that owns base app6VBiQlnq6yv0D7
2. Navigate to Account → Developer Hub → Personal Access Tokens
3. Create new token with:
   - Name: "BQX-ML-Phase2-Admin-Token"
   - Scopes:
     - data.records:read
     - data.records:write
     - schema.bases:read
   - Bases: Grant access to app6VBiQlnq6yv0D7 specifically

4. Store new token in AWS Secrets Manager:
   ```bash
   aws secretsmanager create-secret \
       --name bqx-ml-phase2/airtable/api-token \
       --description "AirTable API token with access to BQX ML Phase 2 base (app6VBiQlnq6yv0D7)" \
       --secret-string '{"token":"NEW_TOKEN_HERE","base_id":"app6VBiQlnq6yv0D7","base_name":"BQX ML Phase 2 Stages","scopes":"data.records:read,data.records:write,schema.bases:read","created":"2025-11-17"}'
   ```

5. Update scripts to use new secret path

**Time Required:** 15 minutes

**Benefit:** Enables programmatic AirTable updates for future stages

---

## IMPACT

### Current Impact: Low

**Manual workaround available:** Web UI updates take only 5 minutes

**No blocking issues:** All technical work complete (Stages 2.14, 2.15 done)

**Documentation complete:** Clear instructions for manual updates

### Future Impact: Medium

**For TIER 1 execution:**
- Manual updates needed for Stages 2.3, 2.4, 2.16B (3 updates)
- Total manual time: ~15 minutes over 6 weeks

**For TIER 2 & 3 execution:**
- Manual updates needed for 8 additional stages
- Total manual time: ~40 minutes over 12 weeks

**Alternative:** Generate new token (one-time 15 minute investment) to enable automation

---

## CONCLUSION

**API Access Status:** ❌ **NOT AVAILABLE**

**Current token:** Has broad scopes but lacks base-specific permissions for BQX ML Phase 2 base (app6VBiQlnq6yv0D7)

**Workaround:** ✅ **MANUAL UPDATE VIA WEB UI** (5 minutes)

**Long-term fix:** Generate new token with explicit access to BQX ML Phase 2 base

**Immediate action required:** Manual update for Stages 2.14 and 2.15

---

**Investigation Completed:** 2025-11-17 13:30 UTC
**Result:** Manual update required (API access not available)
**Next Step:** Proceed with manual update via web UI
