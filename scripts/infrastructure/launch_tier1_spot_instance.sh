#!/bin/bash
##
## Launch c7i.8xlarge Spot Instance for TIER 1 Execution
##
## This script launches a temporary EC2 Spot instance for running
## TIER 1 enhancement stages (2.3, 2.4, 2.16B).
##
## Duration: ~4 days
## Cost: ~$22 (Spot pricing)
## Termination: Manual (after TIER 1 completion)
##
## Usage: bash launch_tier1_spot_instance.sh
##

set -e

# Configuration
INSTANCE_TYPE="c7i.8xlarge"
SPOT_PRICE="0.50"  # Max price (actual Spot price is ~$0.40/hour)
AMI_ID="ami-0c7217cdde317cfec"  # Ubuntu 22.04 LTS (us-east-1)

# Get current instance info
echo "Getting configuration from trillium-master..."
INSTANCE_ID="i-08a8fa9a42491827c"

VPC_ID=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].VpcId' \
    --output text)

SUBNET_ID=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].SubnetId' \
    --output text)

SECURITY_GROUP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
    --output text)

KEY_NAME=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].KeyName' \
    --output text)

echo "VPC ID: $VPC_ID"
echo "Subnet ID: $SUBNET_ID"
echo "Security Group: $SECURITY_GROUP"
echo "Key Name: $KEY_NAME"
echo ""

# Create user data script for instance initialization
cat > /tmp/tier1_user_data.sh << 'EOF'
#!/bin/bash

# Update system
apt-get update
apt-get install -y python3-pip python3-venv git postgresql-client

# Create working directory
mkdir -p /home/ubuntu/bqx-ml
cd /home/ubuntu/bqx-ml

# Clone repository
git clone https://github.com/Schmidtlappin/bqx-ml.git .

# Install Python dependencies
pip3 install -r requirements.txt

# Set database credentials
echo "export DB_HOST=trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com" >> /home/ubuntu/.bashrc
echo "export DB_PASSWORD=BQX_Aurora_2025_Secure" >> /home/ubuntu/.bashrc

# Create log directory
mkdir -p /tmp/logs/tier1

# Set ownership
chown -R ubuntu:ubuntu /home/ubuntu/bqx-ml

echo "TIER 1 instance initialization complete"
EOF

# Launch Spot instance
echo "Launching c7i.8xlarge Spot instance..."
echo ""

LAUNCH_SPEC=$(cat <<JSON
{
  "ImageId": "$AMI_ID",
  "KeyName": "$KEY_NAME",
  "InstanceType": "$INSTANCE_TYPE",
  "SubnetId": "$SUBNET_ID",
  "SecurityGroupIds": ["$SECURITY_GROUP"],
  "UserData": "$(base64 -w 0 /tmp/tier1_user_data.sh)"
}
JSON
)

# Request Spot instance
SPOT_REQUEST=$(aws ec2 request-spot-instances \
    --spot-price "$SPOT_PRICE" \
    --instance-count 1 \
    --type "one-time" \
    --launch-specification "$LAUNCH_SPEC" \
    --output json)

SPOT_REQUEST_ID=$(echo $SPOT_REQUEST | jq -r '.SpotInstanceRequests[0].SpotInstanceRequestId')

echo "Spot request ID: $SPOT_REQUEST_ID"
echo "Waiting for Spot instance to launch..."
echo ""

# Wait for Spot request to be fulfilled
aws ec2 wait spot-instance-request-fulfilled \
    --spot-instance-request-ids $SPOT_REQUEST_ID

# Get instance ID
TIER1_INSTANCE_ID=$(aws ec2 describe-spot-instance-requests \
    --spot-instance-request-ids $SPOT_REQUEST_ID \
    --query 'SpotInstanceRequests[0].InstanceId' \
    --output text)

echo "✅ Spot instance launched!"
echo "Instance ID: $TIER1_INSTANCE_ID"
echo ""

# Tag the instance
echo "Tagging instance..."
aws ec2 create-tags \
    --resources $TIER1_INSTANCE_ID \
    --tags \
        "Key=Name,Value=trillium-tier1-worker" \
        "Key=Purpose,Value=TIER 1 Enhancement Execution" \
        "Key=Phase,Value=Phase 2 - TIER 1" \
        "Key=Temporary,Value=true" \
        "Key=MaxRuntime,Value=4 days"
echo ""

# Wait for instance to be running
echo "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $TIER1_INSTANCE_ID

# Get instance details
INSTANCE_DETAILS=$(aws ec2 describe-instances \
    --instance-ids $TIER1_INSTANCE_ID \
    --output json)

PUBLIC_IP=$(echo $INSTANCE_DETAILS | jq -r '.Reservations[0].Instances[0].PublicIpAddress')
PRIVATE_IP=$(echo $INSTANCE_DETAILS | jq -r '.Reservations[0].Instances[0].PrivateIpAddress')

echo "✅ Instance is running!"
echo ""
echo "Instance Details:"
echo "  Instance ID: $TIER1_INSTANCE_ID"
echo "  Instance Type: $INSTANCE_TYPE"
echo "  Public IP: $PUBLIC_IP"
echo "  Private IP: $PRIVATE_IP"
echo "  Spot Price: ~$0.40/hour (max $SPOT_PRICE/hour)"
echo ""
echo "Connection:"
echo "  ssh -i ~/.ssh/$KEY_NAME.pem ubuntu@$PUBLIC_IP"
echo ""
echo "Next Steps:"
echo "  1. Wait 2-3 minutes for user data script to complete"
echo "  2. SSH into instance"
echo "  3. Verify setup: ls /home/ubuntu/bqx-ml"
echo "  4. Run Stage 2.3: python3 scripts/tier1/stage_2_3_currency_indices.py"
echo ""
echo "Estimated Runtime: ~4 days (55 hours)"
echo "Estimated Cost: ~$22"
echo ""
echo "⚠️  IMPORTANT: Terminate instance after TIER 1 completion!"
echo "  Terminate command: aws ec2 terminate-instances --instance-ids $TIER1_INSTANCE_ID"
echo ""

# Save instance ID for later reference
echo $TIER1_INSTANCE_ID > /tmp/tier1_instance_id.txt

echo "Instance ID saved to /tmp/tier1_instance_id.txt"
echo ""
echo "=" * 80
echo "TIER 1 Spot Instance Ready!"
echo "=" * 80
