#!/bin/bash
##
## Downgrade trillium-master back to t3.2xlarge after TIER 1 Completion
##
## This script restores trillium-master to its original t3.2xlarge instance type
## after TIER 1 execution is complete.
##
## Duration: ~10 minutes (stop, modify, start)
## Cost Savings: ~$243/month → $121/month (50% savings)
##
## Usage: bash downgrade_trillium_master_after_tier1.sh
##

set -e

INSTANCE_ID="i-08a8fa9a42491827c"
ORIGINAL_TYPE="t3.2xlarge"
CURRENT_TYPE="c7i.8xlarge"

echo "========================================="
echo "DOWNGRADING TRILLIUM-MASTER AFTER TIER 1"
echo "========================================="
echo ""
echo "Instance: $INSTANCE_ID"
echo "Current: $CURRENT_TYPE (32 vCPUs, 64 GB RAM)"
echo "Target: $ORIGINAL_TYPE (8 vCPUs, 32 GB RAM)"
echo ""
echo "⚠️  WARNING: This will cause ~5 minutes of downtime"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Downgrade cancelled"
    exit 1
fi

echo ""
echo "Step 1: Verifying TIER 1 completion..."
echo ""
echo "Please confirm the following TIER 1 stages are complete:"
echo "  - Stage 2.3: Currency Indices (336/336 partitions)"
echo "  - Stage 2.4: Triangular Arbitrage (336/336 partitions)"
echo "  - Stage 2.16B: Expand Currency Blocs (336/336 partitions)"
echo ""
read -p "All TIER 1 stages complete? (yes/no): " stages_complete

if [ "$stages_complete" != "yes" ]; then
    echo "❌ Cannot downgrade until TIER 1 is complete"
    echo "Continue running TIER 1 stages before downgrading"
    exit 1
fi

echo ""
echo "Step 2: Stopping instance..."
aws ec2 stop-instances --instance-ids $INSTANCE_ID

echo "Waiting for instance to stop..."
aws ec2 wait instance-stopped --instance-ids $INSTANCE_ID

echo "✅ Instance stopped"
echo ""

echo "Step 3: Modifying instance type back to $ORIGINAL_TYPE..."
aws ec2 modify-instance-attribute \
    --instance-id $INSTANCE_ID \
    --instance-type "{\"Value\": \"$ORIGINAL_TYPE\"}"

echo "✅ Instance type modified"
echo ""

echo "Step 4: Starting instance..."
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
echo "DOWNGRADE COMPLETE!"
echo "========================================="
echo ""
echo "Instance Details:"
echo "  Instance ID: $INSTANCE_ID"
echo "  Instance Type: $ORIGINAL_TYPE"
echo "  Public IP: $NEW_IP"
echo "  vCPUs: 8"
echo "  RAM: 32 GB"
echo ""
echo "Connection:"
echo "  ssh -i ~/.ssh/trillium-master-key.pem ubuntu@$NEW_IP"
echo ""
echo "Cost Impact:"
echo "  Before: ~$243/month (c7i.8xlarge)"
echo "  After: ~$121/month (t3.2xlarge)"
echo "  Savings: ~$122/month (50%)"
echo ""
echo "✅ trillium-master restored to normal operation"
echo ""
