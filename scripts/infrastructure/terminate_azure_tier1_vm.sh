#!/bin/bash
##
## Terminate Azure F72s_v2 TIER 1 VM After Completion
##
## This script terminates the Azure Spot VM used for TIER 1 execution
## and cleans up associated resources.
##
## Prerequisites:
##   - Azure CLI authenticated
##   - TIER 1 stages complete
##
## Usage: bash terminate_azure_tier1_vm.sh
##

set -e

# Configuration
RESOURCE_GROUP="tier1-rg"
VM_NAME="tier1-bqx-worker"

echo "========================================="
echo "TERMINATE AZURE TIER 1 VM"
echo "========================================="
echo ""
echo "This will delete:"
echo "  • VM: $VM_NAME"
echo "  • Associated disks"
echo "  • Network interfaces"
echo "  • Public IP"
echo ""
echo "⚠️  WARNING: This action cannot be undone!"
echo ""

# Check if VM exists
if ! az vm show --resource-group $RESOURCE_GROUP --name $VM_NAME &>/dev/null; then
    echo "❌ VM '$VM_NAME' not found in resource group '$RESOURCE_GROUP'"
    echo ""
    echo "Available VMs:"
    az vm list --resource-group $RESOURCE_GROUP --output table 2>/dev/null || echo "No VMs found"
    exit 1
fi

echo "Step 1: Verify TIER 1 Completion..."
echo ""
echo "Please confirm the following TIER 1 stages are complete:"
echo "  • Stage 2.3: Currency Indices (336/336 partitions)"
echo "  • Stage 2.4: Triangular Arbitrage (336/336 partitions)"
echo "  • Stage 2.16B: Expand Currency Blocs (336/336 partitions)"
echo ""
read -p "All TIER 1 stages complete? (yes/no): " stages_complete

if [ "$stages_complete" != "yes" ]; then
    echo "❌ Cannot terminate until TIER 1 is complete"
    echo "Continue running TIER 1 stages before terminating"
    exit 1
fi

echo ""
echo "Step 2: Show VM details..."
az vm show \
    --resource-group $RESOURCE_GROUP \
    --name $VM_NAME \
    --show-details \
    --output table

echo ""
read -p "Proceed with termination? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Termination cancelled"
    exit 1
fi

echo ""
echo "Step 3: Deleting VM..."
az vm delete \
    --resource-group $RESOURCE_GROUP \
    --name $VM_NAME \
    --yes \
    --no-wait

echo "✅ VM deletion initiated (running in background)"

echo ""
echo "Step 4: Waiting for VM deletion to complete..."
echo "This may take 2-3 minutes..."

# Wait for VM to be fully deleted
while az vm show --resource-group $RESOURCE_GROUP --name $VM_NAME &>/dev/null; do
    echo -n "."
    sleep 10
done

echo ""
echo "✅ VM deleted"

echo ""
echo "Step 5: Remove Aurora Security Group Rule..."
echo ""
echo "IMPORTANT: Manually remove Azure IP from AWS Aurora security group:"
echo ""
echo "  AWS Console → RDS → trillium-bqx-cluster → Security Group"
echo "  Remove Rule: Source matching Azure VM IP"
echo ""
echo "OR use AWS CLI (if you know the rule ID):"
echo "  AURORA_SG_ID=\"sg-0513e6cd4874f8c6b\""
echo "  aws ec2 revoke-security-group-ingress \\"
echo "      --group-id \$AURORA_SG_ID \\"
echo "      --protocol tcp \\"
echo "      --port 5432 \\"
echo "      --cidr <AZURE_IP>/32"
echo ""

echo ""
echo "Step 6: (Optional) Delete Resource Group..."
echo ""
echo "To completely remove all TIER 1 Azure resources:"
echo "  az group delete --name $RESOURCE_GROUP --yes --no-wait"
echo ""
echo "⚠️  This will delete ALL resources in the resource group"
echo ""
read -p "Delete entire resource group now? (yes/no): " delete_rg

if [ "$delete_rg" = "yes" ]; then
    echo "Deleting resource group..."
    az group delete --name $RESOURCE_GROUP --yes --no-wait
    echo "✅ Resource group deletion initiated"
else
    echo "Skipping resource group deletion"
    echo "You can delete it later with:"
    echo "  az group delete --name $RESOURCE_GROUP --yes"
fi

echo ""
echo "========================================="
echo "TIER 1 AZURE VM TERMINATED"
echo "========================================="
echo ""
echo "Cleanup Summary:"
echo "  ✅ VM deleted: $VM_NAME"
echo "  ✅ Associated resources cleaned up"
echo "  ⚠️  Verify Aurora security group rule removed"
echo ""
echo "Cost Summary:"
echo "  Review Azure billing for actual TIER 1 costs"
echo "  Expected: ~$23-25 total"
echo ""
echo "Next Steps:"
echo "  1. Verify all TIER 1 data in Aurora RDS"
echo "  2. Update AirTable stages to 'Done'"
echo "  3. Create TIER 1 completion report"
echo "  4. (Optional) Proceed to TIER 2 enhancements"
echo ""
