#!/bin/bash
##
## Launch Azure Standard_F72s_v2 Spot Instance for TIER 1 Execution
##
## This script launches an Azure F72s_v2 Spot VM (72 vCPUs, 144 GB RAM)
## for executing TIER 1 enhancement stages (2.3, 2.4, 2.16B).
##
## Performance: ~28.6 hours total (48% faster than AWS baseline)
## Cost: ~$23.45 total
## Termination: Manual (after TIER 1 completion)
##
## Prerequisites:
##   - Azure CLI installed (az)
##   - Azure account authenticated (az login)
##   - Resource group created or will be created by script
##
## Usage: bash launch_azure_f72s_v2_for_tier1.sh
##

set -e

# Configuration
RESOURCE_GROUP="tier1-rg"
LOCATION="eastus"
VM_NAME="tier1-bqx-worker"
VM_SIZE="Standard_F72s_v2"
IMAGE="Canonical:0001-com-ubuntu-server-jammy:22_04-lts:latest"
ADMIN_USER="azureuser"
MAX_SPOT_PRICE="0.80"  # Max $0.80/hour (typical Spot is ~$0.75/hour)

echo "========================================="
echo "TIER 1 AZURE F72s_v2 SPOT INSTANCE LAUNCH"
echo "========================================="
echo ""
echo "Configuration:"
echo "  VM Size: $VM_SIZE (72 vCPUs, 144 GB RAM)"
echo "  Location: $LOCATION"
echo "  Pricing: Spot (~$0.75/hour)"
echo "  Max Price: $MAX_SPOT_PRICE/hour"
echo "  Estimated Duration: ~29 hours"
echo "  Estimated Cost: ~$23"
echo ""
echo "Performance vs AWS baseline:"
echo "  Duration: 28.6h vs 55h (48% faster)"
echo "  Cost: $23.45 vs $22 (+7%)"
echo ""
read -p "Continue with launch? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Launch cancelled"
    exit 1
fi

echo ""
echo "Step 1: Check/Create Resource Group..."
if az group show --name $RESOURCE_GROUP &>/dev/null; then
    echo "✅ Resource group '$RESOURCE_GROUP' exists"
else
    echo "Creating resource group '$RESOURCE_GROUP'..."
    az group create \
        --name $RESOURCE_GROUP \
        --location $LOCATION
    echo "✅ Resource group created"
fi

echo ""
echo "Step 2: Create SSH key (if not exists)..."
SSH_KEY_PATH="$HOME/.ssh/azure_tier1_key"
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "Generating SSH key..."
    ssh-keygen -t rsa -b 4096 -f "$SSH_KEY_PATH" -N "" -C "tier1-azure-key"
    echo "✅ SSH key generated: $SSH_KEY_PATH"
else
    echo "✅ SSH key exists: $SSH_KEY_PATH"
fi

echo ""
echo "Step 3: Create cloud-init script..."
cat > /tmp/azure_tier1_cloud_init.yaml << 'EOF'
#cloud-config

package_update: true
package_upgrade: true

packages:
  - python3-pip
  - python3-venv
  - git
  - postgresql-client

runcmd:
  # Create working directory
  - mkdir -p /home/azureuser/bqx-ml
  - cd /home/azureuser/bqx-ml

  # Clone repository
  - git clone https://github.com/Schmidtlappin/bqx-ml.git .

  # Install Python dependencies
  - pip3 install psycopg2-binary pandas numpy sqlalchemy

  # Set database environment variables
  - echo "export DB_HOST=trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com" >> /home/azureuser/.bashrc
  - echo "export DB_PASSWORD=BQX_Aurora_2025_Secure" >> /home/azureuser/.bashrc
  - echo "export DB_USER=postgres" >> /home/azureuser/.bashrc
  - echo "export DB_NAME=bqx" >> /home/azureuser/.bashrc

  # Create log directories
  - mkdir -p /tmp/logs/tier1/stage_2_3
  - mkdir -p /tmp/logs/tier1/stage_2_4
  - mkdir -p /tmp/logs/tier1/stage_2_16b

  # Set ownership
  - chown -R azureuser:azureuser /home/azureuser/bqx-ml
  - chown -R azureuser:azureuser /tmp/logs

  # Mark initialization complete
  - echo "TIER 1 Azure VM initialization complete at $(date)" > /home/azureuser/init_complete.txt

final_message: "TIER 1 Azure F72s_v2 VM ready for execution"
EOF

echo "✅ Cloud-init script created"

echo ""
echo "Step 4: Launching Spot VM..."
echo "This may take 3-5 minutes..."

az vm create \
    --resource-group $RESOURCE_GROUP \
    --name $VM_NAME \
    --location $LOCATION \
    --size $VM_SIZE \
    --image $IMAGE \
    --admin-username $ADMIN_USER \
    --ssh-key-values "${SSH_KEY_PATH}.pub" \
    --priority Spot \
    --max-price $MAX_SPOT_PRICE \
    --eviction-policy Deallocate \
    --custom-data /tmp/azure_tier1_cloud_init.yaml \
    --public-ip-sku Standard \
    --output json > /tmp/azure_vm_output.json

echo "✅ VM created successfully"

# Extract details
PUBLIC_IP=$(az vm show \
    --resource-group $RESOURCE_GROUP \
    --name $VM_NAME \
    --show-details \
    --query publicIps \
    --output tsv)

PRIVATE_IP=$(az vm show \
    --resource-group $RESOURCE_GROUP \
    --name $VM_NAME \
    --show-details \
    --query privateIps \
    --output tsv)

VM_ID=$(az vm show \
    --resource-group $RESOURCE_GROUP \
    --name $VM_NAME \
    --query id \
    --output tsv)

echo ""
echo "Step 5: Configure Network Security Group..."
echo "Opening port 22 for SSH..."

# Get NSG name (usually automatically created)
NSG_NAME="${VM_NAME}NSG"

# Create SSH rule if doesn't exist
az network nsg rule create \
    --resource-group $RESOURCE_GROUP \
    --nsg-name $NSG_NAME \
    --name AllowSSH \
    --priority 1000 \
    --source-address-prefixes '*' \
    --source-port-ranges '*' \
    --destination-address-prefixes '*' \
    --destination-port-ranges 22 \
    --access Allow \
    --protocol Tcp \
    --description "Allow SSH" \
    &>/dev/null || echo "SSH rule may already exist"

echo "✅ Network security configured"

echo ""
echo "Step 6: Configure AWS Aurora Security Group..."
echo ""
echo "IMPORTANT: You must manually update AWS Aurora security group to allow Azure VM IP:"
echo ""
echo "  AWS Console → RDS → trillium-bqx-cluster → Security Group"
echo "  Add Inbound Rule:"
echo "    Type: PostgreSQL (5432)"
echo "    Source: $PUBLIC_IP/32"
echo "    Description: TIER 1 Azure F72s_v2 temporary access"
echo ""
echo "OR use AWS CLI:"
echo "  AURORA_SG_ID=\"sg-0513e6cd4874f8c6b\"  # Replace with actual Aurora SG ID"
echo "  aws ec2 authorize-security-group-ingress \\"
echo "      --group-id \$AURORA_SG_ID \\"
echo "      --protocol tcp \\"
echo "      --port 5432 \\"
echo "      --cidr ${PUBLIC_IP}/32 \\"
echo "      --description \"TIER 1 Azure F72s_v2 temp access\""
echo ""
read -p "Press Enter after Aurora security group updated..."

echo ""
echo "========================================="
echo "AZURE F72s_v2 VM LAUNCHED SUCCESSFULLY!"
echo "========================================="
echo ""
echo "VM Details:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  VM Name: $VM_NAME"
echo "  VM Size: $VM_SIZE (72 vCPUs, 144 GB RAM)"
echo "  Location: $LOCATION"
echo "  Public IP: $PUBLIC_IP"
echo "  Private IP: $PRIVATE_IP"
echo "  Spot Max Price: $MAX_SPOT_PRICE/hour"
echo ""
echo "Connection:"
echo "  ssh -i $SSH_KEY_PATH $ADMIN_USER@$PUBLIC_IP"
echo ""
echo "Next Steps:"
echo "  1. Wait 2-3 minutes for cloud-init to complete"
echo "  2. SSH into VM: ssh -i $SSH_KEY_PATH $ADMIN_USER@$PUBLIC_IP"
echo "  3. Verify initialization: cat ~/init_complete.txt"
echo "  4. Test database connection:"
echo "     PGPASSWORD='BQX_Aurora_2025_Secure' psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com -U postgres -d bqx -c 'SELECT COUNT(*) FROM bqx.reg_bqx_audcad_2024_07;'"
echo "  5. Execute Stage 2.3:"
echo "     cd ~/bqx-ml"
echo "     nohup python3 scripts/tier1/stage_2_3_currency_indices.py > /tmp/logs/tier1/stage_2_3/execution.log 2>&1 &"
echo "  6. Monitor progress:"
echo "     tail -f /tmp/logs/tier1/stage_2_3/currency_indices.log"
echo ""
echo "Estimated Timeline:"
echo "  Stage 2.3: ~9.5 hours"
echo "  Stage 2.4: ~9.5 hours"
echo "  Stage 2.16B: ~7.5 hours"
echo "  Total: ~28.6 hours"
echo ""
echo "Estimated Cost: ~$23.45"
echo ""
echo "⚠️  IMPORTANT: Terminate VM after TIER 1 completion!"
echo "  Terminate command: az vm delete --resource-group $RESOURCE_GROUP --name $VM_NAME --yes"
echo ""
echo "VM connection details saved to: /tmp/azure_tier1_connection.txt"

# Save connection details
cat > /tmp/azure_tier1_connection.txt << EOF
Resource Group: $RESOURCE_GROUP
VM Name: $VM_NAME
VM Size: $VM_SIZE
Public IP: $PUBLIC_IP
Private IP: $PRIVATE_IP
SSH Command: ssh -i $SSH_KEY_PATH $ADMIN_USER@$PUBLIC_IP
VM ID: $VM_ID

Created: $(date)
EOF

echo ""
echo "========================================="
echo "TIER 1 AZURE F72s_v2 VM READY!"
echo "========================================="
