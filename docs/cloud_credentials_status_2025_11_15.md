# Cloud Credentials Status Report
**Date:** 2025-11-15
**Purpose:** Verify Azure and GCP credentials for potential BQX ML migration
**Status:** GCP credentials exist but expired, Azure credentials not configured

---

## Executive Summary

| Cloud | Credentials Status | Access Status | Compute Ready? | Action Required |
|-------|-------------------|---------------|----------------|-----------------|
| **GCP** | ✅ Found (expired) | ❌ Needs re-auth | ❌ No | Re-authenticate + enable Compute API |
| **Azure** | ❌ Not found | ❌ Not configured | ❌ No | Full setup required |
| **AWS** | ✅ Active | ✅ Working | ⏳ Quota pending | Wait for quota or request 32 vCPUs |

---

## Google Cloud Platform (GCP)

### Credentials Found ✅

**Location in AWS Secrets Manager:**
- `trillium/gcp/bigquery-adc-credentials` (Primary)
- `bqx-mirror/bqx/gcp/credentials-summary` (Detailed info)

**Credential Details:**
```json
{
  "type": "authorized_user",
  "authenticated_account": "michael@trillium.works",
  "authentication_method": "Application Default Credentials (ADC)",
  "projects": {
    "primary": "trillium-works-engine-mcp",
    "bqx_dedicated": "bqx-ml-bigquery-2025"
  }
}
```

### Current Access Status ❌

**Authentication Test Results:**
```
✅ Credentials file exists in Secrets Manager
✅ Can load credentials locally
❌ Credentials expired - needs reauthentication
```

**Error Message:**
```
Reauthentication is needed. Please run `gcloud auth application-default login` to reauthenticate.
```

### What's Missing for Compute Access

#### 1. Expired Credentials (CRITICAL)
**Status:** ❌ Blocked
**Issue:** OAuth 2.0 user credentials expired (typical lifetime: 1 hour)
**Fix Required:**
```bash
# Option A: Re-authenticate interactively (requires browser)
gcloud auth application-default login

# Option B: Create service account with key (if org policy allows)
gcloud iam service-accounts create bqx-ml-compute \
  --display-name="BQX ML Compute Service Account"

gcloud iam service-accounts keys create ~/bqx-ml-sa-key.json \
  --iam-account=bqx-ml-compute@PROJECT_ID.iam.gserviceaccount.com
```

**Blocker:** Organization policy `iam.disableServiceAccountKeyCreation` is ENFORCED
**Workaround:** Must use user authentication (gcloud auth login)

#### 2. gcloud CLI Not Installed
**Status:** ❌ Not installed
**Install Command:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

**Alternative:** Use Python SDK directly (but still need auth)

#### 3. Compute Engine API Not Enabled (Assumed)
**Status:** ⚠️ Unknown (likely not enabled)
**Current Enabled APIs:**
- BigQuery APIs (all variants)
- Storage API
- IAM API

**Required for Compute:**
```bash
gcloud services enable compute.googleapis.com --project=trillium-works-engine-mcp
```

#### 4. Python Libraries Not Installed
**Status:** ❌ Missing
**Required:**
```bash
pip install google-cloud-compute
pip install google-auth google-auth-oauthlib google-auth-httplib2
```

### GCP Compute Access Verification Steps

**To confirm Compute Engine access:**

1. **Install gcloud CLI**
2. **Re-authenticate:**
   ```bash
   gcloud auth application-default login
   # Follow browser prompts
   ```

3. **Set project:**
   ```bash
   gcloud config set project trillium-works-engine-mcp
   ```

4. **Enable Compute Engine API:**
   ```bash
   gcloud services enable compute.googleapis.com
   ```

5. **Test compute access:**
   ```bash
   # List available machine types in us-central1
   gcloud compute machine-types list --zones=us-central1-a --filter="name=c2-standard-32"

   # Check quotas
   gcloud compute project-info describe --project=trillium-works-engine-mcp
   ```

6. **Test via Python:**
   ```python
   from google.cloud import compute_v1

   client = compute_v1.InstancesClient()
   project = "trillium-works-engine-mcp"
   zone = "us-central1-a"

   # List instances (should return empty list if none exist)
   instances = client.list(project=project, zone=zone)
   print(f"GCP Compute access: ✅ Working")
   ```

---

## Microsoft Azure

### Credentials Found ❌

**Search Results:**
```
❌ No Azure credentials found in AWS Secrets Manager
❌ Azure CLI not installed
❌ Azure Python SDK not installed
❌ No Azure environment variables
```

### What's Required for Azure Setup

#### 1. Create Azure Account
**Steps:**
1. Go to https://portal.azure.com/
2. Sign up for Azure account (free tier available)
3. Verify identity (credit card required, not charged)
4. Create subscription

**Estimated Time:** 15-30 minutes

#### 2. Install Azure CLI
**Ubuntu/Debian:**
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

**Verify:**
```bash
az --version
```

#### 3. Authenticate
```bash
az login
# Opens browser for authentication
```

#### 4. Install Python SDK
```bash
pip install azure-identity azure-mgmt-compute azure-mgmt-resource azure-mgmt-network
```

#### 5. Create Service Principal (for automation)
```bash
# Create service principal with Contributor role
az ad sp create-for-rbac --name "bqx-ml-compute" \
  --role Contributor \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID

# Output will include:
# {
#   "appId": "...",
#   "displayName": "bqx-ml-compute",
#   "password": "...",
#   "tenant": "..."
# }
```

#### 6. Store Credentials in AWS Secrets Manager
```bash
aws secretsmanager create-secret \
  --name "trillium/azure/compute-credentials" \
  --description "Azure service principal for BQX ML compute" \
  --secret-string '{
    "subscription_id": "YOUR_SUBSCRIPTION_ID",
    "tenant_id": "YOUR_TENANT_ID",
    "client_id": "YOUR_APP_ID",
    "client_secret": "YOUR_PASSWORD"
  }' \
  --region us-east-1
```

#### 7. Test Compute Access
```python
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient

credentials = ClientSecretCredential(
    tenant_id="YOUR_TENANT_ID",
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET"
)

compute_client = ComputeManagementClient(
    credential=credentials,
    subscription_id="YOUR_SUBSCRIPTION_ID"
)

# List available VM sizes in East US
vm_sizes = compute_client.virtual_machine_sizes.list(location="eastus")
for size in vm_sizes:
    if size.name == "Standard_D32as_v5":
        print(f"✅ Azure Compute access working")
        print(f"   VM: {size.name}")
        print(f"   vCPUs: {size.number_of_cores}")
        print(f"   Memory: {size.memory_in_mb / 1024} GB")
        break
```

---

## Implementation Timeline

### If Choosing GCP (Fastest Path with Existing Creds)

| Task | Duration | Difficulty | Status |
|------|----------|------------|--------|
| Install gcloud CLI | 10 min | Easy | ❌ Pending |
| Re-authenticate (gcloud auth) | 5 min | Easy | ❌ Pending |
| Enable Compute Engine API | 5 min | Easy | ❌ Pending |
| Install Python libraries | 5 min | Easy | ❌ Pending |
| Test compute access | 10 min | Easy | ❌ Pending |
| **Total** | **35 min** | **Easy** | **❌ Not Ready** |

**After Setup:**
- Create c2-standard-32 instance: 15 min
- Deploy code & test: 2-3 hours
- **Ready to run Phase 2:** ~4 hours

### If Choosing Azure (Full Setup Required)

| Task | Duration | Difficulty | Status |
|------|----------|------------|--------|
| Create Azure account | 15-30 min | Easy | ❌ Pending |
| Install Azure CLI | 10 min | Easy | ❌ Pending |
| Authenticate (az login) | 5 min | Easy | ❌ Pending |
| Install Python SDK | 5 min | Easy | ❌ Pending |
| Create service principal | 10 min | Medium | ❌ Pending |
| Store credentials in Secrets Manager | 5 min | Easy | ❌ Pending |
| Test compute access | 10 min | Easy | ❌ Pending |
| **Total** | **1-1.5 hours** | **Easy-Medium** | **❌ Not Ready** |

**After Setup:**
- Create D32as_v5 instance: 15 min
- Deploy code & test: 2-3 hours
- **Ready to run Phase 2:** ~5 hours

### AWS (Current Platform)

| Task | Duration | Status |
|------|----------|--------|
| Wait for quota decision | 1-24 hours | ⏳ In Progress |
| Submit 32 vCPU request (if denied) | 5 min + 1-24 hours | ⏳ Pending |
| Launch c7i.8xlarge | 5 min | ✅ Script ready |
| **Total** | **1-48 hours** | **⏳ Waiting** |

---

## Recommendations

### Option 1: Wait for AWS Quota ⭐ (RECOMMENDED if <24 hours)
**Timeline:** 1-24 hours
**Effort:** Zero (automated monitoring active)
**Cost:** $61.61 (On-Demand) or retry Spot later
**Risk:** Low

**Action:**
- Let auto-monitor continue running
- If denied, submit 32 vCPU request immediately
- Start Phase 2 within hours of approval

### Option 2: Setup GCP Immediately ⭐ (RECOMMENDED if AWS quota takes >24 hours)
**Timeline:** 35 min setup + 4 hours deployment = ~4.5 hours to Phase 2 start
**Effort:** Low (credentials already exist)
**Cost:** $64.37
**Risk:** Low

**Action:**
1. Install gcloud CLI (10 min)
2. Run `gcloud auth application-default login` (5 min)
3. Enable Compute Engine API (5 min)
4. Test access (10 min)
5. Create c2-standard-32 instance (15 min)
6. Deploy code (2-3 hours)
7. **Start Phase 2** (~7 hours faster than waiting)

### Option 3: Setup Azure from Scratch
**Timeline:** 1.5 hours setup + 5 hours deployment = ~6.5 hours
**Effort:** Medium (full account setup)
**Cost:** $60.00
**Risk:** Low-Medium

**Action:**
- Only if you want to compare all three clouds
- Or if GCP auth fails for some reason
- Best value ($60) but most setup time

---

## Decision Matrix

| Criteria | AWS (Wait) | GCP (Setup) | Azure (Setup) |
|----------|------------|-------------|---------------|
| **Time to Phase 2** | 1-48 hours | ~4.5 hours | ~6.5 hours |
| **Setup Effort** | Zero | 35 min | 1.5 hours |
| **Cost** | $61.61 | $64.37 | $60.00 |
| **Credentials** | ✅ Working | ⚠️ Expired (fixable) | ❌ None |
| **Risk** | Low | Low | Low-Medium |
| **Migration Effort** | Zero | 2-3 days | 2-3 days |

---

## Next Steps

### Immediate Actions (Choose One)

**Path A: Continue AWS Path** (if quota likely within 24 hours)
```bash
# Just wait - monitoring script is running
tail -f /tmp/quota_monitor.log
```

**Path B: Setup GCP** (if impatient, want guaranteed progress)
```bash
# 1. Install gcloud
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# 2. Authenticate
gcloud auth application-default login

# 3. Set project
gcloud config set project trillium-works-engine-mcp

# 4. Enable Compute API
gcloud services enable compute.googleapis.com

# 5. Test
gcloud compute machine-types list --zones=us-central1-a --filter="name=c2-standard-32"
```

**Path C: Setup Azure** (if you want best value, willing to wait)
```bash
# 1. Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# 2. Authenticate
az login

# 3. Test
az vm list-sizes --location eastus --query "[?name=='Standard_D32as_v5']"
```

---

## Summary

**GCP Status:** 🟡 **Credentials exist but expired**
- **Fixable in:** 35 minutes
- **Blocker:** Need to re-authenticate via browser
- **Ready for compute:** After re-auth + API enable

**Azure Status:** 🔴 **No credentials configured**
- **Setup time:** 1-1.5 hours
- **Blocker:** Need Azure account
- **Ready for compute:** After full setup

**Recommendation:**
1. If AWS quota arrives within 24 hours → **Stay on AWS**
2. If AWS quota delayed beyond 24 hours → **Setup GCP** (fastest with existing creds)
3. If you want best value and can wait → **Setup Azure** (cheapest at $60)

**Current State:** Waiting for AWS quota decision, can pivot to GCP in <1 hour if needed.
