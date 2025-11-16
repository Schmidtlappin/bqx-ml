# Azure Account Setup Guide for Arrow Peak Analytics
**Email:** michael.stevenson@arrow-peak.com
**Date:** 2025-11-15
**Purpose:** Setup Azure account and compute access for BQX ML Phase 2

---

## Overview

Since `michael.stevenson@arrow-peak.com` is managed by Office 365, you already have a Microsoft account. This makes Azure setup faster and easier - you can use your existing O365 credentials.

**Total Time:** ~1-1.5 hours
**Cost:** $0 setup, ~$60 for Phase 2 compute (1.8 days)

---

## Part 1: Create Azure Account (15-30 minutes)

### Step 1: Sign Up for Azure

**Option A: Use Existing O365 Account (Recommended)** ⭐
1. Go to: https://azure.microsoft.com/free/
2. Click **"Start free"** or **"Try Azure for free"**
3. Sign in with: `michael.stevenson@arrow-peak.com`
4. Use your Office 365 password

**Benefits of O365 Account:**
- ✅ Instant authentication (no email verification)
- ✅ May be linked to Arrow Peak's Azure organization (check with IT)
- ✅ Can request organization billing if company has Azure tenant
- ✅ Single sign-on across Microsoft services

### Step 2: Verify Identity

Azure requires identity verification:
1. **Phone Verification:**
   - Enter mobile phone number
   - Receive and enter verification code

2. **Credit Card Verification:**
   - Required even for free tier
   - **No charges unless you explicitly upgrade to Pay-As-You-Go**
   - Card is only for identity verification
   - Free tier includes $200 credit for 30 days

**Important:**
- You get $200 free credit for 30 days
- After 30 days OR $200 spent, you must upgrade to Pay-As-You-Go
- For BQX ML, we need Pay-As-You-Go ($60 cost for Phase 2)

### Step 3: Complete Registration

Fill out the form:
- **Country/Region:** United States
- **First Name:** Michael
- **Last Name:** Stevenson
- **Email:** michael.stevenson@arrow-peak.com (pre-filled)
- **Phone:** Your mobile number
- **Company:** Arrow Peak Analytics, LLC (optional)
- **Agreement:** Check "I agree to customer agreement..."

### Step 4: Create Subscription

After registration:
1. You'll be redirected to Azure Portal
2. Azure will create a default subscription (usually named "Azure subscription 1")
3. **IMPORTANT:** Note your Subscription ID (looks like: `12345678-1234-1234-1234-123456789abc`)

**To find Subscription ID:**
- Azure Portal → Search "Subscriptions" → Copy the ID

### Step 5: Check for Existing Azure Organization

Since you're using O365 email, check if Arrow Peak already has Azure:

1. Azure Portal → Azure Active Directory
2. Look for organization name
3. **If you see "Arrow Peak Analytics" or similar:**
   - ✅ You're in organization's tenant
   - Contact your IT admin about billing
   - May be able to use company subscription

**If Organization Exists:**
- Ask IT for permission to create VMs
- May need "Contributor" role on subscription
- Could use company's billing instead of personal credit card

---

## Part 2: Install Azure CLI (10 minutes)

### Step 1: Install Azure CLI on Trillium-Master

Run these commands on trillium-master EC2:

```bash
# Update package list
sudo apt-get update

# Install prerequisites
sudo apt-get install -y ca-certificates curl apt-transport-https lsb-release gnupg

# Download and install Microsoft signing key
sudo mkdir -p /etc/apt/keyrings
curl -sLS https://packages.microsoft.com/keys/microsoft.asc | \
  gpg --dearmor | \
  sudo tee /etc/apt/keyrings/microsoft.gpg > /dev/null
sudo chmod go+r /etc/apt/keyrings/microsoft.gpg

# Add Azure CLI repository
AZ_REPO=$(lsb_release -cs)
echo "deb [arch=`dpkg --print-architecture` signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/azure-cli/ $AZ_REPO main" | \
  sudo tee /etc/apt/sources.list.d/azure-cli.list

# Update package list and install Azure CLI
sudo apt-get update
sudo apt-get install -y azure-cli
```

### Step 2: Verify Installation

```bash
az --version
```

**Expected Output:**
```
azure-cli                         2.xx.x

Your CLI is up-to-date.
```

---

## Part 3: Authenticate Azure CLI (5 minutes)

### Option A: Interactive Login (From Local Machine) ⭐

**If you have SSH access with port forwarding:**
```bash
az login
```

This will:
1. Open your browser
2. Prompt for microsoft.stevenson@arrow-peak.com login
3. Ask you to sign in with O365 password
4. Return to CLI with success message

### Option B: Device Code Login (For SSH-Only Access)

**If running from remote server without browser:**
```bash
az login --use-device-code
```

This will:
1. Show a code (like: `ABCDEFGH`)
2. Show URL: https://microsoft.com/devicelogin
3. You open URL on your local computer
4. Enter the code
5. Sign in with michael.stevenson@arrow-peak.com
6. Return to CLI - it will auto-complete

**Recommended for trillium-master:** Use device code method

### Step 3: Verify Authentication

```bash
az account show
```

**Expected Output:**
```json
{
  "environmentName": "AzureCloud",
  "id": "YOUR-SUBSCRIPTION-ID",
  "name": "Azure subscription 1",
  "state": "Enabled",
  "user": {
    "name": "michael.stevenson@arrow-peak.com",
    "type": "user"
  }
}
```

### Step 4: Set Default Subscription (if multiple)

```bash
# List all subscriptions
az account list --output table

# Set default (replace with your Subscription ID)
az account set --subscription "YOUR-SUBSCRIPTION-ID"
```

---

## Part 4: Create Service Principal (15 minutes)

Service principal = Azure's version of AWS IAM user (for programmatic access)

### Step 1: Create Service Principal

```bash
# Create service principal with Contributor role on your subscription
az ad sp create-for-rbac \
  --name "bqx-ml-compute" \
  --role Contributor \
  --scopes /subscriptions/YOUR-SUBSCRIPTION-ID \
  --output json
```

**Replace `YOUR-SUBSCRIPTION-ID`** with your actual subscription ID from `az account show`

**Expected Output:**
```json
{
  "appId": "12345678-1234-1234-1234-123456789abc",
  "displayName": "bqx-ml-compute",
  "password": "SUPER-SECRET-PASSWORD-GENERATED-BY-AZURE",
  "tenant": "87654321-4321-4321-4321-cba987654321"
}
```

**⚠️ IMPORTANT:** Save this output! You'll need:
- `appId` (client ID)
- `password` (client secret) - **CANNOT BE RETRIEVED LATER**
- `tenant` (tenant ID)

### Step 2: Get Subscription ID

```bash
az account show --query id --output tsv
```

Save this as well!

### Step 3: Store All Credentials

You should now have:
- ✅ Subscription ID
- ✅ Tenant ID
- ✅ Client ID (appId)
- ✅ Client Secret (password)

**Write these down securely!**

---

## Part 5: Store Credentials in AWS Secrets Manager (5 minutes)

### Create Secret in AWS

```bash
# Replace the placeholder values with your actual credentials
AWS_PROFILE=trillium-global aws secretsmanager create-secret \
  --name "trillium/azure/compute-credentials" \
  --description "Azure service principal for BQX ML compute - michael.stevenson@arrow-peak.com" \
  --secret-string '{
    "subscription_id": "YOUR-SUBSCRIPTION-ID",
    "tenant_id": "YOUR-TENANT-ID",
    "client_id": "YOUR-CLIENT-ID",
    "client_secret": "YOUR-CLIENT-SECRET",
    "email": "michael.stevenson@arrow-peak.com",
    "service_principal_name": "bqx-ml-compute"
  }' \
  --region us-east-1
```

### Verify Secret Stored

```bash
AWS_PROFILE=trillium-global aws secretsmanager get-secret-value \
  --secret-id "trillium/azure/compute-credentials" \
  --region us-east-1 \
  --query 'SecretString' \
  --output text | python3 -m json.tool
```

---

## Part 6: Install Azure Python SDK (5 minutes)

```bash
pip install azure-identity azure-mgmt-compute azure-mgmt-resource azure-mgmt-network
```

### Verify Installation

```bash
python3 << 'EOF'
try:
    from azure.identity import ClientSecretCredential
    from azure.mgmt.compute import ComputeManagementClient
    print("✅ Azure Python SDK installed successfully")
except ImportError as e:
    print(f"❌ Installation failed: {e}")
EOF
```

---

## Part 7: Test Azure Compute Access (10 minutes)

### Step 1: Test Authentication

```bash
python3 << 'EOF'
import json
import subprocess

# Get credentials from AWS Secrets Manager
result = subprocess.run([
    'aws', 'secretsmanager', 'get-secret-value',
    '--secret-id', 'trillium/azure/compute-credentials',
    '--region', 'us-east-1',
    '--query', 'SecretString',
    '--output', 'text'
], capture_output=True, text=True, env={'AWS_PROFILE': 'trillium-global'})

creds = json.loads(result.stdout)

# Test Azure authentication
from azure.identity import ClientSecretCredential

credential = ClientSecretCredential(
    tenant_id=creds['tenant_id'],
    client_id=creds['client_id'],
    client_secret=creds['client_secret']
)

# Get access token
token = credential.get_token("https://management.azure.com/.default")
print("✅ Azure authentication successful!")
print(f"Token expires: {token.expires_on}")
EOF
```

### Step 2: Test Compute Access

```bash
python3 << 'EOF'
import json
import subprocess

# Get credentials
result = subprocess.run([
    'aws', 'secretsmanager', 'get-secret-value',
    '--secret-id', 'trillium/azure/compute-credentials',
    '--region', 'us-east-1',
    '--query', 'SecretString',
    '--output', 'text'
], capture_output=True, text=True, env={'AWS_PROFILE': 'trillium-global'})

creds = json.loads(result.stdout)

# Test compute access
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient

credential = ClientSecretCredential(
    tenant_id=creds['tenant_id'],
    client_id=creds['client_id'],
    client_secret=creds['client_secret']
)

compute_client = ComputeManagementClient(
    credential=credential,
    subscription_id=creds['subscription_id']
)

# List available VM sizes in East US
print("✅ Testing Azure Compute access...")
print("\nAvailable VM sizes for BQX ML Phase 2:")

vm_sizes = compute_client.virtual_machine_sizes.list(location="eastus")
for size in vm_sizes:
    if size.name in ['Standard_D32as_v5', 'Standard_D32s_v5', 'Standard_F32s_v2']:
        print(f"\n  ✅ {size.name}")
        print(f"     vCPUs: {size.number_of_cores}")
        print(f"     Memory: {size.memory_in_mb / 1024:.0f} GB")
        print(f"     Max Data Disks: {size.max_data_disk_count}")

print("\n✅ Azure Compute access verified!")
EOF
```

### Step 3: Check Quotas

```bash
az vm list-usage --location eastus --output table
```

Look for:
- **Standard DASv5 Family vCPUs:** Should show quota (often 10-100 by default)
- **Total Regional vCPUs:** Total vCPU limit in East US

**If you see 0 or low quotas:**
```bash
# Request quota increase
az support quota create \
  --quota-name "Standard DASv5 Family vCPUs" \
  --limit 32 \
  --location eastus
```

---

## Part 8: Create Resource Group (5 minutes)

Resource groups organize Azure resources.

```bash
# Create resource group in East US
az group create \
  --name bqx-ml-phase2 \
  --location eastus \
  --tags project=bqx-ml phase=2 owner=michael.stevenson@arrow-peak.com
```

**Verify:**
```bash
az group show --name bqx-ml-phase2 --output table
```

---

## Setup Complete! ✅

### What You Now Have

✅ Azure account (michael.stevenson@arrow-peak.com)
✅ Active subscription
✅ Azure CLI installed and authenticated
✅ Service principal created (bqx-ml-compute)
✅ Credentials stored in AWS Secrets Manager
✅ Python SDK installed
✅ Compute access verified
✅ Resource group created

### Credentials Summary

All credentials are stored in:
```
AWS Secrets Manager: trillium/azure/compute-credentials
```

Contains:
- Subscription ID
- Tenant ID
- Client ID (App ID)
- Client Secret (Password)

### Next Steps

**Ready to create VM for Phase 2:**

```bash
# Create D32as_v5 VM (AMD, 32 vCPUs, 128 GB RAM, best value)
az vm create \
  --resource-group bqx-ml-phase2 \
  --name bqx-phase2-worker \
  --location eastus \
  --size Standard_D32as_v5 \
  --image Ubuntu2204 \
  --admin-username ubuntu \
  --ssh-key-values "$(cat ~/.ssh/id_rsa.pub)" \
  --public-ip-address-allocation static \
  --tags project=bqx-ml phase=2 purpose=feature-engineering
```

**Estimated cost:** $60 for 1.8 days (1.7-1.8 days actual runtime)

---

## Troubleshooting

### Issue: "Subscription not found"
**Solution:** Verify subscription ID
```bash
az account list --output table
az account set --subscription "YOUR-SUBSCRIPTION-ID"
```

### Issue: "Insufficient permissions"
**Solution:** Verify service principal has Contributor role
```bash
az role assignment list --assignee YOUR-CLIENT-ID --output table
```

### Issue: "Quota exceeded"
**Solution:** Request quota increase
```bash
az vm list-usage --location eastus --output table
# Contact support if quota is 0
```

### Issue: "Device code expired"
**Solution:** Login again
```bash
az login --use-device-code
```

### Issue: "Cannot find subscription"
**Solution:** May be in organization tenant - contact IT
```bash
az account tenant list
az account set --subscription "SUBSCRIPTION-NAME"
```

---

## Cost Management

### View Current Costs

```bash
# View current month costs
az consumption usage list \
  --start-date 2025-11-01 \
  --end-date 2025-11-15 \
  --output table
```

### Set Spending Alerts

In Azure Portal:
1. Cost Management + Billing
2. Budgets
3. Add budget: $100/month
4. Set alerts at 80%, 90%, 100%

---

## Security Best Practices

### Rotate Service Principal Credentials (Every 90 days)

```bash
# Create new credential
az ad sp credential reset \
  --name bqx-ml-compute \
  --years 1

# Update AWS Secrets Manager with new password
```

### Restrict Service Principal Scope

```bash
# Limit to specific resource group
az role assignment create \
  --assignee YOUR-CLIENT-ID \
  --role Contributor \
  --scope /subscriptions/SUB-ID/resourceGroups/bqx-ml-phase2
```

### Enable MFA on Account

In Azure Portal:
1. Azure Active Directory
2. Users → michael.stevenson@arrow-peak.com
3. Multi-Factor Authentication → Enable

---

## Support Resources

**Azure Documentation:**
- Compute: https://docs.microsoft.com/azure/virtual-machines/
- Pricing: https://azure.microsoft.com/pricing/calculator/

**Arrow Peak O365 Admin:**
- If you need organization billing, contact your O365 administrator
- They may have existing Azure tenant with better quotas

**Azure Support:**
- Free tier: Community support only
- Developer support: $29/month (includes ticket support)
- Quota increases: Usually approved within hours

---

**Setup Status:** Ready to proceed with Azure D32as_v5 deployment
**Total Setup Time:** ~1 hour
**Next Action:** Create VM for Phase 2
