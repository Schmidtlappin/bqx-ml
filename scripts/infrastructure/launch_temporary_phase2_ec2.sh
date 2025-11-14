#!/bin/bash
# ============================================================================
# LAUNCH TEMPORARY EC2 FOR PHASE 2
# ============================================================================
# Purpose: Spin up temporary c7i.8xlarge Spot instance for Phase 2 processing
# Duration: 1.8 days, then terminate
# Cost: $19.13 total (Spot pricing)
# ============================================================================

set -e

echo "================================================================================"
echo "LAUNCH TEMPORARY PHASE 2 EC2 WORKER"
echo "================================================================================"
echo ""
echo "This script will:"
echo "  1. Launch c7i.8xlarge Spot instance (32 vCPUs, 64 GB RAM)"
echo "  2. Tag as temporary infrastructure (trillium-phase2-worker)"
echo "  3. Configure security groups and networking"
echo "  4. Wait for instance to be running"
echo ""
echo "Cost: ~$0.45/hour Spot (~$1.36/hour On-Demand)"
echo "Duration: 1.8 days (42.5 hours)"
echo "Total Cost: $19.13"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Configuration
AMI_ID="ami-0161740617dac346b"  # Same AMI as trillium-master
KEY_NAME="trillium-master-key"
SECURITY_GROUP="sg-0513e6cd4874f8c6b"  # Same as trillium-master
SUBNET_ID="subnet-0aa48fbf275ef3e2f"   # Same as trillium-master (us-east-1a)
INSTANCE_TYPE="c7i.8xlarge"
MAX_SPOT_PRICE="1.00"  # $1.00/hour (vs ~$0.45 spot price)

echo ""
echo "Configuration:"
echo "  Instance Type: $INSTANCE_TYPE"
echo "  AMI: $AMI_ID"
echo "  Max Spot Price: \$$MAX_SPOT_PRICE/hour"
echo "  Key Pair: $KEY_NAME"
echo ""

# Create user data script
cat > /tmp/phase2-worker-init.sh <<'EOF'
#!/bin/bash
# User data script for Phase 2 worker

# Update system
apt-get update && apt-get upgrade -y

# Install dependencies
apt-get install -y \
    python3-pip \
    python3-venv \
    postgresql-client \
    git \
    htop \
    awscli

# Configure swap (for memory-intensive operations)
fallocate -l 16G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Create ubuntu user (if not exists)
if ! id -u ubuntu > /dev/null 2>&1; then
    useradd -m -s /bin/bash ubuntu
    usermod -aG sudo ubuntu
    echo "ubuntu ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
fi

# Clone repository (as ubuntu user)
su - ubuntu -c "git clone https://github.com/Schmidtlappin/bqx-ml.git /home/ubuntu/bqx-ml"

# Install Python dependencies
su - ubuntu -c "cd /home/ubuntu/bqx-ml && pip3 install --user -r requirements.txt"

# Create log directories
su - ubuntu -c "mkdir -p /tmp/logs/{stage_2_2,stage_2_3,stage_2_4,stage_2_6,stage_2_7,stage_2_8,stage_2_9}"

# Set Aurora credentials (environment variables)
cat >> /home/ubuntu/.bashrc <<'BASHRC'
export AURORA_HOST="trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com"
export AURORA_USER="postgres"
export AURORA_DB="bqx"
# Note: AURORA_PASSWORD should be set manually or via Secrets Manager
BASHRC

# Mark initialization complete
touch /tmp/phase2-worker-init-complete
EOF

# Launch Spot instance
echo ""
echo "Launching Spot instance..."
LAUNCH_RESPONSE=$(aws ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type "$INSTANCE_TYPE" \
  --key-name "$KEY_NAME" \
  --security-group-ids "$SECURITY_GROUP" \
  --subnet-id "$SUBNET_ID" \
  --instance-market-options "{
    \"MarketType\": \"spot\",
    \"SpotOptions\": {
      \"SpotInstanceType\": \"one-time\",
      \"MaxPrice\": \"$MAX_SPOT_PRICE\"
    }
  }" \
  --tag-specifications "ResourceType=instance,Tags=[
    {Key=Name,Value=trillium-phase2-worker},
    {Key=Phase,Value=2},
    {Key=Lifecycle,Value=temporary},
    {Key=Purpose,Value=Phase2-Parallel-Processing},
    {Key=TerminateAfter,Value=Phase-2-Complete}
  ]" \
  --block-device-mappings "[
    {
      \"DeviceName\": \"/dev/sda1\",
      \"Ebs\": {
        \"VolumeSize\": 100,
        \"VolumeType\": \"gp3\",
        \"DeleteOnTermination\": true
      }
    }
  ]" \
  --user-data file:///tmp/phase2-worker-init.sh \
  --output json)

# Extract instance ID
WORKER_ID=$(echo "$LAUNCH_RESPONSE" | jq -r '.Instances[0].InstanceId')

if [ -z "$WORKER_ID" ] || [ "$WORKER_ID" = "null" ]; then
    echo "❌ Failed to launch instance"
    echo "$LAUNCH_RESPONSE" | jq '.'
    exit 1
fi

echo "✅ Instance launched: $WORKER_ID"
echo ""

# Wait for instance to be running
echo "Waiting for instance to be running (this may take 2-3 minutes)..."
aws ec2 wait instance-running --instance-ids "$WORKER_ID"

echo "✅ Instance is running"
echo ""

# Get public IP
WORKER_IP=$(aws ec2 describe-instances \
  --instance-ids "$WORKER_ID" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "================================================================================"
echo "TEMPORARY EC2 WORKER LAUNCHED SUCCESSFULLY"
echo "================================================================================"
echo ""
echo "Instance Details:"
echo "  Instance ID: $WORKER_ID"
echo "  Instance Type: $INSTANCE_TYPE"
echo "  Public IP: $WORKER_IP"
echo "  Pricing: Spot (~\$0.45/hour)"
echo "  Status: Running"
echo ""
echo "Next Steps:"
echo "  1. Wait 3-5 minutes for user data script to complete"
echo "  2. SSH to instance:"
echo "     ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@${WORKER_IP}"
echo ""
echo "  3. Verify initialization:"
echo "     ls -l /tmp/phase2-worker-init-complete"
echo ""
echo "  4. Set Aurora password:"
echo "     export AURORA_PASSWORD='BQX_Aurora_2025_Secure'"
echo ""
echo "  5. Test Aurora connectivity:"
echo "     PGPASSWORD=\$AURORA_PASSWORD psql -h \$AURORA_HOST -U \$AURORA_USER -d \$AURORA_DB -c 'SELECT version();'"
echo ""
echo "  6. Launch Phase 2 stages:"
echo "     cd /home/ubuntu/bqx-ml"
echo "     bash scripts/orchestration/launch_phase_2_post_track2.sh"
echo ""
echo "IMPORTANT: Remember to TERMINATE this instance after Phase 2 completes!"
echo "           aws ec2 terminate-instances --instance-ids $WORKER_ID"
echo ""
echo "================================================================================"
echo ""

# Save instance ID for later reference
echo "$WORKER_ID" > /tmp/phase2-worker-instance-id.txt
echo "Instance ID saved to: /tmp/phase2-worker-instance-id.txt"
