#!/bin/bash
#
# Cleanup Orphaned AWS Resources
#
# This script removes orphaned EBS volumes and unassociated Elastic IPs
# identified in the AWS Infrastructure Audit (2025-11-16).
#
# SAVINGS: $90.80/month ($1,089.60/year)
#
# SAFETY: Creates EBS snapshots before deletion
#

set -e  # Exit on error

echo "========================================================================"
echo "AWS ORPHANED RESOURCE CLEANUP"
echo "========================================================================"
echo ""
echo "This script will remove the following orphaned resources:"
echo ""
echo "EBS Volumes (2):"
echo "  - vol-05e5ecc1f66f8b11b (trillium-migration-temp-500gb, 500 GB)"
echo "  - vol-0f036b55966d96139 (Trillium-BQX-Migration-500GB, 500 GB)"
echo "  Savings: \$80/month"
echo ""
echo "Elastic IPs (3):"
echo "  - 3.212.188.254 (eipalloc-0e762fc9fc08ac2d0)"
echo "  - 52.20.149.110 (eipalloc-0227c69074d842db5)"
echo "  - 98.94.149.241 (eipalloc-0bbc1ec97335c9a12)"
echo "  Savings: \$10.80/month"
echo ""
echo "TOTAL SAVINGS: \$90.80/month (\$1,089.60/year)"
echo ""
echo "========================================================================"
echo ""

# Prompt for confirmation
read -p "Do you want to proceed? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Cleanup cancelled by user"
    exit 0
fi

echo ""
echo "========================================================================"
echo "STEP 1: Create EBS Volume Snapshots (Safety Backup)"
echo "========================================================================"
echo ""

# Create snapshot for vol-05e5ecc1f66f8b11b
echo "Creating snapshot for vol-05e5ecc1f66f8b11b..."
SNAPSHOT1=$(AWS_PROFILE=trillium-global aws ec2 create-snapshot \
    --volume-id vol-05e5ecc1f66f8b11b \
    --description "Backup of trillium-migration-temp-500gb before deletion (2025-11-16)" \
    --tag-specifications 'ResourceType=snapshot,Tags=[{Key=Name,Value=trillium-migration-temp-500gb-backup},{Key=CreatedBy,Value=cleanup-script},{Key=Date,Value=2025-11-16}]' \
    --query 'SnapshotId' \
    --output text)
echo "✅ Created snapshot: $SNAPSHOT1"

# Create snapshot for vol-0f036b55966d96139
echo "Creating snapshot for vol-0f036b55966d96139..."
SNAPSHOT2=$(AWS_PROFILE=trillium-global aws ec2 create-snapshot \
    --volume-id vol-0f036b55966d96139 \
    --description "Backup of Trillium-BQX-Migration-500GB before deletion (2025-11-16)" \
    --tag-specifications 'ResourceType=snapshot,Tags=[{Key=Name,Value=Trillium-BQX-Migration-500GB-backup},{Key=CreatedBy,Value=cleanup-script},{Key=Date,Value=2025-11-16}]' \
    --query 'SnapshotId' \
    --output text)
echo "✅ Created snapshot: $SNAPSHOT2"

echo ""
echo "Waiting 30 seconds for snapshots to initiate..."
sleep 30

echo ""
echo "========================================================================"
echo "STEP 2: Delete Orphaned EBS Volumes"
echo "========================================================================"
echo ""

# Delete vol-05e5ecc1f66f8b11b
echo "Deleting vol-05e5ecc1f66f8b11b..."
AWS_PROFILE=trillium-global aws ec2 delete-volume --volume-id vol-05e5ecc1f66f8b11b
echo "✅ Deleted vol-05e5ecc1f66f8b11b (500 GB) - Savings: \$40/month"

# Delete vol-0f036b55966d96139
echo "Deleting vol-0f036b55966d96139..."
AWS_PROFILE=trillium-global aws ec2 delete-volume --volume-id vol-0f036b55966d96139
echo "✅ Deleted vol-0f036b55966d96139 (500 GB) - Savings: \$40/month"

echo ""
echo "========================================================================"
echo "STEP 3: Release Orphaned Elastic IPs"
echo "========================================================================"
echo ""

# Release eipalloc-0e762fc9fc08ac2d0
echo "Releasing 3.212.188.254 (eipalloc-0e762fc9fc08ac2d0)..."
AWS_PROFILE=trillium-global aws ec2 release-address --allocation-id eipalloc-0e762fc9fc08ac2d0
echo "✅ Released 3.212.188.254 - Savings: \$3.60/month"

# Release eipalloc-0227c69074d842db5
echo "Releasing 52.20.149.110 (eipalloc-0227c69074d842db5)..."
AWS_PROFILE=trillium-global aws ec2 release-address --allocation-id eipalloc-0227c69074d842db5
echo "✅ Released 52.20.149.110 - Savings: \$3.60/month"

# Release eipalloc-0bbc1ec97335c9a12
echo "Releasing 98.94.149.241 (eipalloc-0bbc1ec97335c9a12)..."
AWS_PROFILE=trillium-global aws ec2 release-address --allocation-id eipalloc-0bbc1ec97335c9a12
echo "✅ Released 98.94.149.241 - Savings: \$3.60/month"

echo ""
echo "========================================================================"
echo "CLEANUP COMPLETE"
echo "========================================================================"
echo ""
echo "Summary:"
echo "  ✅ Created 2 EBS snapshots: $SNAPSHOT1, $SNAPSHOT2"
echo "  ✅ Deleted 2 EBS volumes (1,000 GB total)"
echo "  ✅ Released 3 Elastic IPs"
echo ""
echo "Monthly Savings: \$90.80"
echo "Annual Savings: \$1,089.60"
echo ""
echo "Snapshots will be retained for 30 days and can be used to restore"
echo "volumes if needed. Delete snapshots after 30 days to save \$10/month."
echo ""
echo "Next Optimization: Downgrade Trillium-Master to t3.small after"
echo "Stage 2.12 completes (additional \$228/month savings)."
echo ""
echo "========================================================================"
