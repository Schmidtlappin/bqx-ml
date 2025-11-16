# Cloud Credentials Inventory & Audit
**Date:** 2025-11-15
**Purpose:** Comprehensive audit of all cloud credentials stored in AWS Secrets Manager
**Scope:** AWS, Azure, GCP credentials for BQX ML Phase 2
**Auditor:** Automated credential consolidation process

---

## Executive Summary

**Total Secrets in AWS Secrets Manager:** 123 secrets across all categories

**Multi-Cloud Credentials Status:**

| Cloud Provider | Status | Location | Purpose | Ready for Compute? |
|---------------|--------|----------|---------|-------------------|
| **AWS** | ✅ Active | `trillium/aws/iam-user-access-keys` | Trillium account access | ✅ Yes (quota pending) |
| **Azure** | ✅ Active | `trillium/azure/compute-credentials` | BQX ML compute | ✅ Yes |
| **GCP** | ⚠️ Expired | `trillium/gcp/bigquery-adc-credentials` | BigQuery + Compute | ❌ Requires re-auth |

---

## 1. AWS Credentials

### Primary Trillium Account Access

**Secret ID:** `trillium/aws/iam-user-access-keys`
**Status:** ✅ **ACTIVE**
**Created:** 2025-11-02

**Credentials:**
```json
{
  "AccessKeyId": "AKIAX5EZDEJOPJL6HC47",
  "SecretAccessKey": "[REDACTED]",
  "AccountId": "543634432604",
  "UserName": "trillium",
  "UserArn": "arn:aws:iam::543634432604:user/trillium",
  "Permissions": "AdministratorAccess",
  "CreatedDate": "2025-11-02T11:32:15Z"
}
```

**Usage:**
- AWS CLI: `export AWS_PROFILE=trillium-global`
- Boto3: Uses profile `trillium-global` from `~/.aws/credentials`
- Purpose: Full administrative access to Trillium AWS account

**Compute Status:**
- ✅ Credentials working
- ⏳ c7i.8xlarge quota pending (32 → 64 vCPUs request)
- ✅ Spot instances available (c7i.8xlarge)
- ✅ On-Demand fallback available

**Additional AWS Secrets:**
- `bqx-mirror/bqx/aws/apa-credentials` - Arrow Peak Analytics root account
- `bqx-mirror/bqx/aws/robkei-credentials-new` - Post-security incident credentials
- `robkei-engine/automation/aws-credentials` - Robkei Engine IAM user

---

## 2. Azure Credentials

### Service Principal for BQX ML Compute

**Secret ID:** `trillium/azure/compute-credentials`
**Status:** ✅ **ACTIVE** (Created 2025-11-15)
**Last Verified:** 2025-11-15 (compute access confirmed)

**Credentials:**
```json
{
  "subscription_id": "d5a8a1c4-8dfb-49a1-99b1-8316ae1d3520",
  "subscription_name": "AZURE_BQX_ML",
  "tenant_id": "4bd6e18b-cfcb-4d3f-bee4-3755908b480a",
  "client_id": "614e830d-30f1-44a8-8b8e-8fc677cc356c",
  "client_secret": "[REDACTED]",
  "email": "michael.stevenson@arrow-peak.com",
  "service_principal_name": "bqx-ml-compute",
  "tenant_domain": "arrow-peak.com"
}
```

**Service Principal Details:**
- **Name:** bqx-ml-compute
- **Role:** Contributor (subscription-wide)
- **Permissions:** Full VM creation, management, deletion
- **Account Type:** Office 365 managed (arrow-peak.com)

**Usage:**
```python
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient

credential = ClientSecretCredential(
    tenant_id="4bd6e18b-cfcb-4d3f-bee4-3755908b480a",
    client_id="614e830d-30f1-44a8-8b8e-8fc677cc356c",
    client_secret=creds['client_secret']
)

compute_client = ComputeManagementClient(
    credential=credential,
    subscription_id="d5a8a1c4-8dfb-49a1-99b1-8316ae1d3520"
)
```

**Compute Status:**
- ✅ Verified compute access (2025-11-15)
- ✅ Available VM sizes confirmed:
  - Standard_D32as_v5 (32 vCPUs, 128 GB RAM, AMD) - **$60 for 1.8 days**
  - Standard_D32s_v5 (32 vCPUs, 128 GB RAM, Intel) - $70 for 1.8 days
  - Standard_F32s_v2 (32 vCPUs, 64 GB RAM, Intel) - $66 for 1.8 days
- ✅ Quotas available (default: 10+ vCPUs in East US)
- ✅ Resource group created: `bqx-ml-phase2`

**Security:**
- ✅ Client secret stored securely in AWS Secrets Manager
- ⚠️ Rotation policy: 90 days recommended (not yet implemented)
- ✅ Scope: Limited to subscription `AZURE_BQX_ML`

---

## 3. Google Cloud Platform (GCP) Credentials

### Application Default Credentials (OAuth User)

**Secret ID:** `trillium/gcp/bigquery-adc-credentials`
**Status:** ⚠️ **EXPIRED** (Refresh token invalid)
**Last Updated:** 2025-11-03T16:24:54Z
**Authenticated Account:** michael@trillium.works

**Credentials:**
```json
{
  "account": "",
  "client_id": "764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com",
  "client_secret": "[REDACTED]",
  "quota_project_id": "bqx-ml-bigquery-2025",
  "refresh_token": "[EXPIRED]",
  "type": "authorized_user",
  "universe_domain": "googleapis.com",
  "updated_at": "2025-11-03T16:24:54.585645Z",
  "updated_by": "BQX Migration Automation",
  "projects": [
    "trillium-works-engine-mcp",
    "bqx-ml-bigquery-2025"
  ]
}
```

**Additional Secret:** `bqx-mirror/bqx/gcp/credentials-summary`
Contains comprehensive GCP project information and organization policies.

**Projects:**

#### Primary Project: trillium-works-engine-mcp
- **Project ID:** trillium-works-engine-mcp
- **Project Number:** 239333822722
- **Billing Account:** 01B18B-E43829-61F593
- **Enabled APIs:**
  - ✅ BigQuery (all variants)
  - ✅ Storage API
  - ✅ IAM API
  - ❌ Compute Engine API (not confirmed enabled)

#### BQX Dedicated Project: bqx-ml-bigquery-2025
- **Project ID:** bqx-ml-bigquery-2025
- **Project Number:** 297843314939
- **Purpose:** Backup/alternative BigQuery project
- **Status:** Created but service account blocked

**Organization Policies:**
```
iam.disableServiceAccountKeyCreation: ENFORCED
```
- **Impact:** Cannot create JSON keys for service accounts
- **Workaround:** Must use Application Default Credentials (ADC)
- **Blocker for automation:** Requires interactive OAuth authentication

**Current Issues:**

1. **OAuth Refresh Token Expired** ❌
   - Cannot refresh automatically
   - Requires manual re-authentication
   - Error: `RefreshError: Reauthentication is needed`

2. **Service Account Keys Blocked** ⚠️
   - Organization policy prevents JSON key creation
   - Cannot create automation-friendly service account
   - Must use user OAuth flow

3. **Compute Engine API Unknown** ⚠️
   - Not confirmed if enabled
   - Required for VM creation
   - Command to enable: `gcloud services enable compute.googleapis.com`

**Usage (when active):**
```python
from google.cloud import compute_v1

# Uses ADC from /home/ubuntu/.config/gcloud/application_default_credentials.json
client = compute_v1.InstancesClient()
```

**Compute Options (if re-authenticated):**
- c2-standard-32 (32 vCPUs, 128 GB RAM, 3.8 GHz) - **$64.37 for 1.8 days**
- n2-standard-32 (32 vCPUs, 128 GB RAM, 2.8 GHz) - $63.72 for 1.8 days

**Fix Required:**
```bash
# Manual SSH session required
/home/ubuntu/google-cloud-sdk/bin/gcloud auth application-default login
# User completes OAuth flow in browser
# Verification code entered in terminal
```

**Alternative:** Create service account via GCP Console (if org policy allows per-project override):
1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Select project: trillium-works-engine-mcp
3. Create service account: bqx-ml-compute
4. Grant role: Compute Admin
5. Attempt to create JSON key (may fail due to org policy)
6. If successful, store in `trillium/gcp/compute-service-account`

---

## 4. Database Credentials

### Aurora PostgreSQL Clusters

**BQX Cluster:**
- **Secret:** `trillium/aurora/bqx-connection`
- **Status:** ✅ Active
- **Endpoint:** bqx-cluster.cluster-cazfzgzsnfva.us-east-1.rds.amazonaws.com
- **Port:** 5432
- **Database:** bqx_ml

**OXO Cluster:**
- **Secret:** `trillium/aurora/oxo-connection`
- **Status:** ✅ Active
- **Endpoint:** oxo-cluster.cluster-cazfzgzsnfva.us-east-1.rds.amazonaws.com

**NWBB Cluster:**
- **Secret:** `trillium/aurora/nwbb-connection`
- **Status:** ✅ Active (password reset 2025-11-08)
- **Endpoint:** nwbb-cluster.cluster-cazfzgzsnfva.us-east-1.rds.amazonaws.com

**Migration Credentials:**
- `bqx-migration/kms/cross-account-key` - Cross-account KMS key
- `bqx-migration/kms/source-cluster-keys` - Source cluster KMS keys

---

## 5. API Credentials

### AI/ML APIs (From BQX Account)

**Anthropic Claude:**
- **Secrets:** `bqx/api/anthropic`, `bqx-mirror/bqx/api/anthropic`
- **Status:** ✅ Active
- **Usage:** Claude API for AI agents

**OpenAI:**
- **Secrets:** `bqx/api/openai`, `robkei-engine-openai-key`
- **Status:** ✅ Active
- **Scopes:** Admin key and restricted agent key

**Google Gemini:**
- **Secret:** `bqx/api/google-gemini`
- **Status:** ✅ Active
- **Project:** gen-lang-client-0055694509

**Other AI APIs:**
- Groq: `bqx/api/groq`
- Mistral: `bqx/api/mistral`
- XAI: `bqx/api/xai`

### Search & Data APIs

**Brave Search:**
- **Secret:** `bqx-mirror/bqx/api/brave-search`
- **Recommended:** Use via MCP server `@modelcontextprotocol/server-brave-search`

**Serper (Google Search):**
- **Secret:** `bqx-mirror/bqx/api/serper`
- **Recommended:** Use via MCP server `@modelcontextprotocol/server-google-search`

**DiffBot:**
- **Secret:** `bqx-mirror/bqx/api/diffbot`
- **Usage:** Knowledge graph extraction

**US Census:**
- **Secret:** `bqx-mirror/bqx/api/census`
- **Usage:** Geocoding API

**Oanda:**
- **Secret:** `bqx-mirror/bqx/api/oanda`
- **Account:** 001-001-689473-002 (Real account)
- **Usage:** Forex M1 data download

### Automation & Integration APIs

**Airtable:**
- **Secrets:** `bqx/airtable/api-token`, `bqx-mirror/bqx/airtable/api-token`
- **Base IDs:** `bqx-mirror/bqx/airtable/bases`
- **Status:** ✅ Active with full workspace permissions

**GitHub:**
- **Secret:** `bqx-mirror/bqx/github/robkei-control-github-access`
- **Purpose:** Robkei-Control repository access
- **Repo:** bqx-db repository

**Box.com:**
- **Secret:** `bqx-mirror/oxo/box/jwt-config`
- **Account:** OXO Cloud enterprise (48209)
- **Type:** OAuth 2.0 JWT configuration

---

## 6. Infrastructure Credentials

### SSH Keys

**Trillium-Master:**
- **Secret:** `trillium/ssh/trillium-master-key`
- **Instance:** i-01f95df13bdd8deec (t3.2xlarge)
- **Purpose:** Primary compute and database management

**OXO-Master:**
- **Secret:** `bqx-mirror/oxo/ssh/oxo-ec2-key`
- **Instance:** i-08a8fa9a42491827c (c7i.2xlarge)
- **IP:** 3.89.72.229 (restored 2025-10-28)

**eors-master:**
- **Secret:** `bqx-mirror/bqx/ssh/eors-aws-us-east-1`
- **Type:** Lightsail instance
- **Additional:** `bqx-mirror/bqx/ssh/eors-master-direct`

**BQX ML GPU:**
- **Secret:** `bqx-mirror/bqx/ssh/bqx-ml-gpu-key`
- **Purpose:** GPU instance access

**Robkei-Control:**
- **Secret:** `trillium/ssh/robkei-control`
- **Purpose:** Tunnel jump host

**Redis Tunnels:**
- **Secrets:**
  - `trillium/ssh/redis-tunnel-config`
  - `trillium/ssh/redis-tunnel-instructions`
  - `bqx-mirror/oxo/ssh/redis-tunnel-config`

### ElastiCache Redis

**Trillium Redis:**
- **Endpoint Secret:** `robkei-engine/infrastructure/redis`
- **Auth Token:** `robkei-engine/infrastructure/redis-auth`
- **Status:** ✅ Active

**OXO Redis:**
- **Secret:** `bqx-mirror/oxo/cache/redis-config`
- **Auth:** `bqx-mirror/oxo/cache/redis/auth`

### KMS Keys

**Aurora Encryption:**
- **Secret:** `trillium/kms/aurora-encryption-key`
- **Purpose:** Aurora cluster encryption

**Cross-Account Migration:**
- **Secret:** `bqx-migration/kms/cross-account-key`
- **Purpose:** BQX → Trillium migration

---

## 7. Robkei Engine Infrastructure

### ECS & Container Infrastructure

**ECS Cluster:**
- **Secret:** `robkei-engine/infrastructure/ecs-cluster`
- **Task Definitions:** `robkei-engine/infrastructure/task-definitions`
- **ECR Repositories:** `robkei-engine/infrastructure/ecr`

**IAM Roles:**
- **Secret:** `robkei-engine/infrastructure/iam-roles`
- **Purpose:** ECS task execution and bastion access

**VPC Infrastructure:**
- **Secret:** `robkei-engine/infrastructure/vpc`
- **Source:** CloudFormation stack `robkei-engine-vpc`

### Storage & Messaging

**S3 Buckets:**
- **Secret:** `robkei-engine/infrastructure/s3`
- **Purposes:** Workspaces, intelligence, deliverables

**SQS Queues:**
- **Secret:** `robkei-engine/infrastructure/sqs`
- **Purpose:** Task distribution and messaging

**DynamoDB:**
- **Secret:** `robkei-engine/infrastructure/dynamodb`
- **Purpose:** State management and streams

### API & Webhooks

**API Gateway:**
- **Secret:** `robkei-engine/api-gateway/config`
- **Endpoints:** All Lambda functions

**Webhook Secrets:**
- **Secret:** `robkei-engine/webhooks/secrets`
- **Purpose:** External integration verification

---

## 8. Security & Encryption

### Application Security

**Security Keys:**
- **Secret:** `bqx-mirror/bqx/app/security-keys`
- **Source:** eors-master

**JWT Authentication:**
- **Secret:** `bqx-mirror/oxo/auth/jwt-secret`
- **Purpose:** OXO Cloud API authentication

**Encryption Keys:**
- **Secret:** `robkei-engine/encryption/keys`
- **Purpose:** Data protection for Robkei Engine

### Application Passwords

**pgAdmin 4:**
- **Secret:** `bqx-mirror/bqx/apps/pgadmin-password`
- **Purpose:** Web interface access

**VS Code Server:**
- **Secret:** `bqx-mirror/bqx/apps/vscode-password`
- **Instance:** BQX-Master

**RDP:**
- **Secret:** `bqx-mirror/bqx/apps/rdp-password`
- **Instance:** BQX-Master

---

## 9. Missing Credentials

### GCP Service Account (High Priority)

**Status:** ❌ **NOT CREATED**
**Reason:** Organization policy blocks service account key creation
**Impact:** Cannot automate GCP compute operations

**Workaround Options:**

1. **Re-authenticate existing ADC (temporary solution):**
   ```bash
   # Requires interactive SSH session
   /home/ubuntu/google-cloud-sdk/bin/gcloud auth application-default login
   ```
   - ✅ Works immediately
   - ❌ Expires periodically (requires re-auth)
   - ❌ Not suitable for automation

2. **Request org policy exception (permanent solution):**
   - Contact GCP organization admin
   - Request per-project override for `trillium-works-engine-mcp`
   - Create service account with JSON key
   - Store in `trillium/gcp/compute-service-account`
   - ✅ Permanent, automation-friendly
   - ❌ Requires org admin approval

3. **Use Workload Identity Federation (advanced):**
   - Configure AWS → GCP identity federation
   - No JSON keys needed
   - ✅ Most secure option
   - ❌ Complex setup (2-3 hours)

**Recommended:** Option 1 for immediate needs, Option 2 for long-term automation

---

## 10. Credential Health & Rotation Status

### Active & Healthy ✅

- **AWS Trillium:** Active since 2025-11-02 (13 days old)
- **Azure Service Principal:** Active since 2025-11-15 (< 1 day old)
- **Aurora Databases:** All active and tested
- **API Keys:** All AI/ML APIs active
- **SSH Keys:** All instances accessible

### Expired or Requires Attention ⚠️

- **GCP ADC:** Refresh token expired (last updated 2025-11-03)
- **Rotation Needed:**
  - AWS IAM user access keys (13 days old, rotate at 90 days)
  - Azure service principal secret (< 1 day old, rotate at 90 days)

### Rotation Policy Recommendations

**AWS IAM User Access Keys:**
- Current age: 13 days
- Recommended rotation: Every 90 days
- Next rotation: 2026-02-01

**Azure Service Principal:**
- Current age: < 1 day
- Recommended rotation: Every 90 days
- Next rotation: 2026-02-13

**GCP ADC:**
- Current status: Expired
- Type: OAuth user credentials
- Rotation: Automatic (after re-authentication)

**Database Passwords:**
- Last rotation: NWBB cluster (2025-11-08)
- Recommended: Rotate annually or after security events
- Next review: 2026-11-08

**API Keys:**
- Status: No known expiration dates
- Action: Monitor usage, rotate if compromised
- Recommendation: Enable key rotation alerts if available

---

## 11. Recommendations

### Immediate Actions (Next 24 Hours)

1. **Re-authenticate GCP** (15 min)
   - Manual SSH session required
   - Run: `gcloud auth application-default login`
   - Complete OAuth flow in browser
   - Verify: `gcloud auth list`

2. **Enable GCP Compute Engine API** (5 min)
   - Run: `gcloud services enable compute.googleapis.com --project=trillium-works-engine-mcp`
   - Verify quotas: `gcloud compute project-info describe`

3. **Test GCP Compute Access** (10 min)
   - List VM sizes: `gcloud compute machine-types list --zones=us-central1-a`
   - Verify Python SDK access

### Short-Term Actions (Next 7 Days)

1. **Document GCP Quota Limits**
   - Check vCPU quotas for c2-standard-32
   - Request increase if needed (default: 24-32 vCPUs)

2. **Setup Credential Rotation Alerts**
   - AWS: Create CloudWatch alarm for IAM key age
   - Azure: Setup Key Vault expiration notifications
   - Calendar reminder: 2026-02-01 (AWS rotation)

3. **Create Credential Access Audit Log**
   - Enable CloudTrail for Secrets Manager access
   - Monitor who accesses multi-cloud credentials
   - Setup alerts for unusual access patterns

### Long-Term Actions (Next 30 Days)

1. **Request GCP Org Policy Exception**
   - Contact michael@trillium.works GCP admin
   - Request service account key creation for `trillium-works-engine-mcp`
   - Create permanent compute service account

2. **Implement Secrets Rotation Automation**
   - Create Lambda function to rotate AWS keys every 90 days
   - Setup Azure Key Vault for automatic secret rotation
   - Document rotation procedures

3. **Consolidate Duplicate Secrets**
   - Merge `bqx/*` and `bqx-mirror/bqx/*` secrets
   - Remove deprecated credentials
   - Archive terminated service credentials

4. **Setup Cross-Cloud Monitoring**
   - Create unified dashboard for all cloud credentials
   - Monitor credential usage across AWS, Azure, GCP
   - Alert on failed authentication attempts

---

## 12. Credential Inventory Summary

### Total Secrets: 123

**By Category:**
- **Multi-Cloud Access:** 3 (AWS, Azure, GCP)
- **Database Credentials:** 12 (Aurora clusters, RDS instances)
- **SSH Keys:** 8 (EC2 instances, tunnels)
- **API Keys:** 25+ (AI/ML, search, data providers)
- **Infrastructure:** 15+ (ECS, Redis, S3, SQS, DynamoDB)
- **BQX Mirror:** 80+ (mirrored from BQX account)
- **Application Passwords:** 3 (pgAdmin, VS Code, RDP)
- **Security & Encryption:** 5 (JWT, app keys, KMS)

**By Cloud Provider:**
- **AWS-specific:** 100+ secrets
- **Azure-specific:** 1 secret (newly created)
- **GCP-specific:** 2 secrets (1 expired, 1 summary)
- **Cross-cloud:** 20+ secrets (mirrored/synced)

**By Status:**
- **Active & Working:** 120 secrets (97.6%)
- **Expired/Needs Attention:** 1 secret (0.8%) - GCP ADC
- **Deprecated/Archived:** 2 secrets (1.6%) - terminated services

---

## 13. Compliance & Security Notes

### Secrets Manager Best Practices

✅ **Implemented:**
- All production credentials stored in AWS Secrets Manager
- Encryption at rest (AWS KMS)
- Version control enabled (can rollback)
- IAM access control (restricted to trillium user)
- Secrets tagged with purpose and owner

⚠️ **Needs Improvement:**
- Automatic rotation not enabled (manual rotation only)
- No expiration alerts configured
- Cross-region replication not enabled
- Backup/DR strategy not documented

### Multi-Cloud Security Considerations

**AWS:**
- ✅ IAM user with AdministratorAccess
- ✅ MFA not enabled (consider enabling)
- ✅ Access keys stored securely
- ⚠️ No key rotation automation

**Azure:**
- ✅ Service principal with Contributor role
- ✅ Scope limited to subscription
- ✅ Secret stored in AWS Secrets Manager
- ⚠️ No MFA on user account (recommend enabling)

**GCP:**
- ⚠️ OAuth user credentials (less secure than service account)
- ⚠️ Expired refresh token
- ❌ Service account blocked by org policy
- ⚠️ No MFA verification during last auth

### Access Audit Trail

**Who can access these credentials:**
- AWS IAM user: `trillium` (AdministratorAccess)
- EC2 instances: trillium-master (via IAM instance profile)
- Local development: michael@trillium.works (via AWS CLI profile)

**Audit Logging:**
- ✅ AWS CloudTrail enabled (Secrets Manager API calls logged)
- ❌ Azure Key Vault audit logs not configured
- ❌ GCP Cloud Audit Logs not verified

---

## 14. Emergency Procedures

### If Credentials Are Compromised

**AWS:**
1. Immediately disable access key: `aws iam update-access-key --access-key-id AKIAX5EZDEJOPJL6HC47 --status Inactive`
2. Create new access key: `aws iam create-access-key --user-name trillium`
3. Update Secrets Manager: `aws secretsmanager update-secret --secret-id trillium/aws/iam-user-access-keys`
4. Update local `~/.aws/credentials`
5. Review CloudTrail logs for unauthorized activity

**Azure:**
1. Reset service principal secret: `az ad sp credential reset --name bqx-ml-compute`
2. Update Secrets Manager with new secret
3. Review Azure Activity Log for unauthorized VM creation

**GCP:**
1. Revoke OAuth token: `gcloud auth revoke michael@trillium.works`
2. Re-authenticate: `gcloud auth application-default login`
3. Update Secrets Manager with new credentials
4. Review Cloud Audit Logs for unauthorized API calls

### Credential Recovery

If AWS Secrets Manager becomes inaccessible:
- **Backup location:** Local file `/home/ubuntu/.aws/credentials` (AWS only)
- **GCP backup:** `/home/ubuntu/.config/gcloud/application_default_credentials.json`
- **Azure:** No local backup (re-create service principal if needed)

**Recovery Steps:**
1. Verify AWS CLI profile: `aws sts get-caller-identity --profile trillium-global`
2. If profile works, retrieve secrets: `aws secretsmanager get-secret-value --secret-id SECRET_NAME`
3. If profile broken, use root account to create new IAM user
4. Document incident and update procedures

---

## Appendix A: Quick Reference

### Retrieve Multi-Cloud Credentials

**AWS:**
```bash
AWS_PROFILE=trillium-global aws secretsmanager get-secret-value \
  --secret-id "trillium/aws/iam-user-access-keys" \
  --region us-east-1 --query 'SecretString' --output text | python3 -m json.tool
```

**Azure:**
```bash
AWS_PROFILE=trillium-global aws secretsmanager get-secret-value \
  --secret-id "trillium/azure/compute-credentials" \
  --region us-east-1 --query 'SecretString' --output text | python3 -m json.tool
```

**GCP:**
```bash
AWS_PROFILE=trillium-global aws secretsmanager get-secret-value \
  --secret-id "trillium/gcp/bigquery-adc-credentials" \
  --region us-east-1 --query 'SecretString' --output text | python3 -m json.tool
```

### Test Cloud Access

**AWS:**
```bash
AWS_PROFILE=trillium-global aws sts get-caller-identity
```

**Azure:**
```bash
az login --service-principal \
  -u 614e830d-30f1-44a8-8b8e-8fc677cc356c \
  -p [SECRET] \
  --tenant 4bd6e18b-cfcb-4d3f-bee4-3755908b480a

az account show
```

**GCP:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/home/ubuntu/.config/gcloud/application_default_credentials.json"
gcloud auth list
gcloud config get-value project
```

---

## Appendix B: Credential Creation Dates

| Credential | Created | Age (Days) | Next Rotation |
|-----------|---------|------------|---------------|
| AWS Trillium IAM | 2025-11-02 | 13 | 2026-02-01 |
| Azure Service Principal | 2025-11-15 | 0 | 2026-02-13 |
| GCP ADC | 2025-11-03 | 12 (expired) | Re-auth needed |
| NWBB Aurora Password | 2025-11-08 | 7 | 2026-11-08 |

---

**Document Status:** ✅ Complete
**Last Updated:** 2025-11-15
**Next Review:** 2026-02-01 (align with AWS key rotation)
**Owner:** BQX ML Infrastructure Team
**Contact:** michael@trillium.works
