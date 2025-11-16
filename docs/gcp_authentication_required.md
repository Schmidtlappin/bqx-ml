# GCP Authentication Required - Manual Step

## Status
⚠️ **ACTION REQUIRED:** GCP OAuth credentials expired, needs manual re-authentication

## Why Manual Authentication is Needed

**Root Cause:** OAuth 2.0 refresh token has expired (last authenticated: 2025-11-03)

**Organization Policy Blocker:**
- `iam.disableServiceAccountKeyCreation: ENFORCED`
- Cannot create service account with JSON key
- Must use user OAuth authentication (Application Default Credentials)

## Quick Steps (15 minutes)

### 1. Connect via SSH with Proper Terminal

Use a terminal that supports interactive input:

```bash
# From your local machine
ssh -i ~/.ssh/your-key.pem ubuntu@<trillium-master-ip>
```

### 2. Run Authentication Command

```bash
/home/ubuntu/google-cloud-sdk/bin/gcloud auth application-default login --no-launch-browser
```

### 3. Complete OAuth Flow

The command will output:
```
Go to the following link in your browser:
    https://accounts.google.com/o/oauth2/auth?client_id=...&redirect_uri=...

Enter authorization code:
```

**Steps:**
1. **Copy the entire URL** from the terminal
2. **Open it in your browser** (on your local machine)
3. **Sign in** with: michael@trillium.works
4. **Grant permissions** when prompted
5. **Copy the authorization code** from the browser
6. **Paste it back into the terminal** (at the "Enter authorization code:" prompt)
7. Press Enter

### 4. Verify Authentication

```bash
/home/ubuntu/google-cloud-sdk/bin/gcloud auth list
```

**Expected output:**
```
           Credentialed Accounts
ACTIVE  ACCOUNT
*       michael@trillium.works

To set the active account, run:
    $ gcloud config set account `ACCOUNT`
```

### 5. Set Default Project

```bash
/home/ubuntu/google-cloud-sdk/bin/gcloud config set project trillium-works-engine-mcp
```

### 6. Enable Compute Engine API

```bash
/home/ubuntu/google-cloud-sdk/bin/gcloud services enable compute.googleapis.com
```

### 7. Test Compute Access

```bash
# List available machine types
/home/ubuntu/google-cloud-sdk/bin/gcloud compute machine-types list \
  --zones=us-central1-a \
  --filter="name=c2-standard-32"
```

**Expected output:**
```
NAME            ZONE           CPUS  MEMORY_GB  DEPRECATED
c2-standard-32  us-central1-a  32    128.00
```

### 8. Update AWS Secrets Manager

After successful authentication, the credentials will be automatically updated at:
```
/home/ubuntu/.config/gcloud/application_default_credentials.json
```

**To sync to AWS Secrets Manager:**
```bash
AWS_PROFILE=trillium-global aws secretsmanager update-secret \
  --secret-id "trillium/gcp/bigquery-adc-credentials" \
  --secret-string "$(cat /home/ubuntu/.config/gcloud/application_default_credentials.json)" \
  --region us-east-1
```

## After Authentication Completes

✅ GCP credentials will be active
✅ Can create c2-standard-32 instances
✅ Python google-cloud-* libraries will work automatically
✅ Compute Engine API enabled

**Estimated Time:** 15 minutes
**Difficulty:** Easy (just need browser + terminal access)

---

## Why This Can't Be Automated

**Technical Limitations:**
1. OAuth 2.0 requires **interactive browser** authentication
2. SSH environment doesn't support automatic browser launching
3. Each authentication attempt generates a **unique session token**
4. Cannot reuse verification codes between sessions
5. Organization policy prevents service account automation

**Attempted Solutions (all failed):**
- ❌ Piping verification code directly
- ❌ Using expired refresh token
- ❌ Creating service account (blocked by org policy)
- ❌ Multiple OAuth sessions (each expires independently)

## Alternative: Request Org Policy Exception

**If you need permanent automation (no manual steps):**

1. **Contact GCP Organization Admin:**
   - Email: admin@trillium.works or IT department
   - Request: Per-project override for `iam.disableServiceAccountKeyCreation`
   - Project: `trillium-works-engine-mcp`

2. **After approval, create service account:**
   ```bash
   gcloud iam service-accounts create bqx-ml-compute \
     --display-name="BQX ML Compute Service Account" \
     --project=trillium-works-engine-mcp

   gcloud iam service-accounts keys create ~/bqx-ml-sa-key.json \
     --iam-account=bqx-ml-compute@trillium-works-engine-mcp.iam.gserviceaccount.com

   # Grant Compute Admin role
   gcloud projects add-iam-policy-binding trillium-works-engine-mcp \
     --member="serviceAccount:bqx-ml-compute@trillium-works-engine-mcp.iam.gserviceaccount.com" \
     --role="roles/compute.admin"
   ```

3. **Store in AWS Secrets Manager:**
   ```bash
   AWS_PROFILE=trillium-global aws secretsmanager create-secret \
     --name "trillium/gcp/compute-service-account" \
     --description "GCP service account for BQX ML compute automation" \
     --secret-string "$(cat ~/bqx-ml-sa-key.json)" \
     --region us-east-1
   ```

**Benefits of Service Account:**
- ✅ No expiration (permanent)
- ✅ No browser authentication needed
- ✅ Fully automation-friendly
- ✅ Can be used in scripts and CI/CD

**Drawback:**
- Requires org admin approval (may take days)

---

## Current State Summary

**What's Working:**
- ✅ gcloud CLI installed (version 547.0.0)
- ✅ GCP credentials file exists (but expired)
- ✅ Project configuration set
- ✅ Python google-cloud-* libraries installed

**What Needs Manual Action:**
- ⚠️ OAuth re-authentication (15 min, requires browser)
- ⚠️ Enable Compute Engine API (5 min, after auth)
- ⚠️ Verify quotas (5 min, after API enabled)

**Timeline:**
- **With manual auth:** 25 minutes to GCP compute ready
- **With service account:** 2-5 days (depends on org admin response)

---

## Recommendation

**For immediate BQX ML Phase 2 deployment:**
1. Use **Azure** (already fully configured and tested)
   - Cost: $60 for 1.8 days
   - Instance: Standard_D32as_v5 (32 vCPUs, 128 GB RAM)
   - Zero setup time remaining

2. **In parallel,** complete GCP manual authentication
   - Enables future GCP deployments
   - Provides cost comparison data
   - Backup option if Azure has issues

**For long-term automation:**
- Request GCP org policy exception
- Create service account
- Store in AWS Secrets Manager
- Update deployment scripts to use service account

---

**Status:** Waiting for manual user action
**Priority:** Medium (Azure already available)
**Estimated Time:** 15 minutes
**Next Step:** SSH to trillium-master and complete OAuth flow
