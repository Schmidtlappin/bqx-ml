#!/bin/bash
# ============================================================================
# TERMINATE TEMPORARY PHASE 2 EC2
# ============================================================================
# Purpose: Terminate temporary Phase 2 worker after completion
# IMPORTANT: Run ONLY after Phase 2 is 100% complete and validated
# ============================================================================

set -e

echo "================================================================================"
echo "TERMINATE TEMPORARY PHASE 2 EC2 WORKER"
echo "================================================================================"
echo ""
echo "⚠️  WARNING: This will TERMINATE the temporary Phase 2 worker instance."
echo "⚠️  This action is IRREVERSIBLE. All data on the instance will be lost."
echo ""
echo "Prerequisites (verify ALL before proceeding):"
echo "  [ ] Phase 2 is 100% complete (all stages done)"
echo "  [ ] S3 export validated (40-50 GB Parquet files)"
echo "  [ ] All features in Aurora verified"
echo "  [ ] Worker logs archived (if needed)"
echo "  [ ] No active processes running"
echo ""

# Try to read instance ID from saved file
if [ -f /tmp/phase2-worker-instance-id.txt ]; then
    WORKER_ID=$(cat /tmp/phase2-worker-instance-id.txt)
    echo "Found saved instance ID: $WORKER_ID"
else
    echo "Instance ID file not found. Searching for trillium-phase2-worker..."
    WORKER_ID=$(aws ec2 describe-instances \
      --filters "Name=tag:Name,Values=trillium-phase2-worker" "Name=instance-state-name,Values=running" \
      --query 'Reservations[0].Instances[0].InstanceId' \
      --output text)

    if [ -z "$WORKER_ID" ] || [ "$WORKER_ID" = "None" ]; then
        echo "❌ Could not find running trillium-phase2-worker instance"
        echo "Please provide instance ID manually:"
        read -p "Instance ID: " WORKER_ID
    fi
fi

if [ -z "$WORKER_ID" ]; then
    echo "❌ No instance ID provided. Aborting."
    exit 1
fi

echo ""
echo "Instance to be terminated: $WORKER_ID"

# Get instance details
INSTANCE_DETAILS=$(aws ec2 describe-instances --instance-ids "$WORKER_ID" --output json)
INSTANCE_TYPE=$(echo "$INSTANCE_DETAILS" | jq -r '.Reservations[0].Instances[0].InstanceType')
INSTANCE_STATE=$(echo "$INSTANCE_DETAILS" | jq -r '.Reservations[0].Instances[0].State.Name')
INSTANCE_IP=$(echo "$INSTANCE_DETAILS" | jq -r '.Reservations[0].Instances[0].PublicIpAddress')
LAUNCH_TIME=$(echo "$INSTANCE_DETAILS" | jq -r '.Reservations[0].Instances[0].LaunchTime')

echo ""
echo "Instance Details:"
echo "  Instance ID: $WORKER_ID"
echo "  Instance Type: $INSTANCE_TYPE"
echo "  State: $INSTANCE_STATE"
echo "  Public IP: $INSTANCE_IP"
echo "  Launch Time: $LAUNCH_TIME"
echo ""

# Calculate runtime
LAUNCH_EPOCH=$(date -d "$LAUNCH_TIME" +%s)
NOW_EPOCH=$(date +%s)
RUNTIME_SECONDS=$((NOW_EPOCH - LAUNCH_EPOCH))
RUNTIME_HOURS=$(echo "scale=2; $RUNTIME_SECONDS / 3600" | bc)

echo "Runtime: $RUNTIME_HOURS hours"
echo "Estimated Cost: \$$(echo "scale=2; $RUNTIME_HOURS * 0.45" | bc) (assuming Spot pricing)"
echo ""

# Ask for confirmation
echo ""
echo "⚠️  FINAL CONFIRMATION"
echo ""
read -p "Type 'TERMINATE' to confirm termination: " CONFIRM

if [ "$CONFIRM" != "TERMINATE" ]; then
    echo "Aborted. Instance NOT terminated."
    exit 0
fi

echo ""
echo "Creating final snapshot (optional, for debugging)..."
read -p "Create snapshot before terminating? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    VOLUME_ID=$(echo "$INSTANCE_DETAILS" | jq -r '.Reservations[0].Instances[0].BlockDeviceMappings[0].Ebs.VolumeId')

    echo "Creating snapshot of volume $VOLUME_ID..."
    SNAPSHOT_ID=$(aws ec2 create-snapshot \
      --volume-id "$VOLUME_ID" \
      --description "trillium-phase2-worker final snapshot - Phase 2 complete" \
      --tag-specifications "ResourceType=snapshot,Tags=[
        {Key=Name,Value=trillium-phase2-worker-final},
        {Key=Phase,Value=2},
        {Key=Purpose,Value=Post-Phase2-Debugging}
      ]" \
      --query 'SnapshotId' \
      --output text)

    echo "✅ Snapshot created: $SNAPSHOT_ID"
    echo "   Snapshot will be available for debugging if needed"
    echo ""
fi

echo "Terminating instance $WORKER_ID..."
aws ec2 terminate-instances --instance-ids "$WORKER_ID" > /dev/null

echo ""
echo "================================================================================"
echo "INSTANCE TERMINATION INITIATED"
echo "================================================================================"
echo ""
echo "✅ Instance $WORKER_ID is being terminated"
echo ""
echo "The instance will:"
echo "  1. Stop accepting new connections"
echo "  2. Shut down within 1-2 minutes"
echo "  3. Be removed from EC2 console"
echo "  4. Stop incurring charges immediately"
echo ""
echo "Waiting for termination to complete..."

# Wait for terminated state
aws ec2 wait instance-terminated --instance-ids "$WORKER_ID" 2>/dev/null || true

# Verify termination
FINAL_STATE=$(aws ec2 describe-instances \
  --instance-ids "$WORKER_ID" \
  --query 'Reservations[0].Instances[0].State.Name' \
  --output text 2>/dev/null || echo "not-found")

echo ""
echo "================================================================================"
echo "TERMINATION COMPLETE"
echo "================================================================================"
echo ""
echo "Final Status: $FINAL_STATE"
echo ""
echo "Summary:"
echo "  Instance ID: $WORKER_ID"
echo "  Runtime: $RUNTIME_HOURS hours"
echo "  Estimated Cost: \$$(echo "scale=2; $RUNTIME_HOURS * 0.45" | bc)"
echo ""
echo "Next Steps:"
echo "  1. ✅ Phase 2 complete (all features in Aurora + S3)"
echo "  2. ✅ Temporary EC2 terminated (no ongoing charges)"
echo "  3. ⏳ Verify trillium-master is running (permanent monitoring)"
echo "  4. ⏳ Begin Phase 3 (SageMaker setup)"
echo ""
echo "trillium-master ongoing cost: \$15/month (t3.small)"
echo "Total Phase 2 cost: \$$(echo "scale=2; $RUNTIME_HOURS * 0.45" | bc)"
echo ""
echo "================================================================================"
