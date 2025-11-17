#!/bin/bash
##
## Upgrade trillium-master to c7i.8xlarge for TIER 1 Execution
##
## This script temporarily upgrades trillium-master from t3.2xlarge to c7i.8xlarge
## for faster TIER 1 stage execution.
##
## Duration: ~10 minutes (stop, modify, start)
## Cost: ~$22 for 4 days (same as Spot option)
## Downgrade: Use downgrade_trillium_master_after_tier1.sh when done
##
## Usage: bash upgrade_trillium_master_for_tier1.sh
##

set -e

INSTANCE_ID="i-08a8fa9a42491827c"
TARGET_TYPE="c7i.8xlarge"
ORIGINAL_TYPE="t3.2xlarge"

echo "========================================="
echo "UPGRADING TRILLIUM-MASTER FOR TIER 1"
echo "========================================="
echo ""
echo "Instance: $INSTANCE_ID"
echo "Current: $ORIGINAL_TYPE (8 vCPUs, 32 GB RAM)"
echo "Target: $TARGET_TYPE (32 vCPUs, 64 GB RAM)"
echo ""
echo "⚠️  WARNING: This will cause ~5 minutes of downtime"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Upgrade cancelled"
    exit 1
fi

echo ""
echo "Step 1: Stopping instance..."
aws ec2 stop-instances --instance-ids $INSTANCE_ID

echo "Waiting for instance to stop..."
aws ec2 wait instance-stopped --instance-ids $INSTANCE_ID

echo "✅ Instance stopped"
echo ""

echo "Step 2: Modifying instance type to $TARGET_TYPE..."
aws ec2 modify-instance-attribute \
    --instance-id $INSTANCE_ID \
    --instance-type "{\"Value\": \"$TARGET_TYPE\"}"

echo "✅ Instance type modified"
echo ""

echo "Step 3: Starting instance..."
aws ec2 start-instances --instance-ids $INSTANCE_ID

echo "Waiting for instance to start..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get new IP (may have changed)
NEW_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "✅ Instance running"
echo ""
echo "========================================="
echo "UPGRADE COMPLETE!"
echo "========================================="
echo ""
echo "Instance Details:"
echo "  Instance ID: $INSTANCE_ID"
echo "  Instance Type: $TARGET_TYPE"
echo "  Public IP: $NEW_IP"
echo "  vCPUs: 32"
echo "  RAM: 64 GB"
echo ""
echo "Connection:"
echo "  ssh -i ~/.ssh/trillium-master-key.pem ubuntu@$NEW_IP"
echo ""
echo "Next Steps:"
echo "  1. Wait 2-3 minutes for system to fully initialize"
echo "  2. Execute TIER 1 Stage 2.3: nohup python3 scripts/tier1/stage_2_3_currency_indices.py > /tmp/logs/tier1/stage_2_3/execution.log 2>&1 &"
echo "  3. Monitor progress: tail -f /tmp/logs/tier1/stage_2_3/currency_indices.log"
echo "  4. After TIER 1 complete: bash scripts/infrastructure/downgrade_trillium_master_after_tier1.sh"
echo ""
echo "Estimated TIER 1 Duration: ~55 hours (4 days)"
echo "Estimated Cost: ~$22"
echo ""
echo "⚠️  IMPORTANT: Downgrade back to t3.2xlarge when done!"
echo ""
