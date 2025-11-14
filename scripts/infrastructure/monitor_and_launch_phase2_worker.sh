#!/bin/bash
# ============================================================================
# MONITOR QUOTA AND LAUNCH PHASE 2 WORKER
# ============================================================================
# Purpose: Monitor vCPU quota increase and auto-launch worker when approved
# Request ID: 066226bd19bc4d73b9c59b6a6917b625qDZsNuIg
# ============================================================================

set -e

REQUEST_ID="066226bd19bc4d73b9c59b6a6917b625qDZsNuIg"
REQUIRED_VCPUS=40  # 8 for trillium-master + 32 for temporary worker
CHECK_INTERVAL=60  # Check every 60 seconds
MAX_WAIT=7200      # Maximum wait time: 2 hours

echo "================================================================================"
echo "MONITORING VCPU QUOTA INCREASE"
echo "================================================================================"
echo ""
echo "Request ID: $REQUEST_ID"
echo "Required vCPUs: $REQUIRED_VCPUS"
echo "Check Interval: ${CHECK_INTERVAL}s"
echo "Maximum Wait: $((MAX_WAIT / 60)) minutes"
echo ""

ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    echo "[$(date '+%H:%M:%S')] Checking quota status... (Elapsed: ${ELAPSED}s)"

    # Check quota value
    CURRENT_QUOTA=$(AWS_PROFILE=trillium-global aws service-quotas get-service-quota \
        --service-code ec2 \
        --quota-code L-1216C47A \
        --region us-east-1 \
        --query 'Quota.Value' \
        --output text 2>/dev/null || echo "8")

    # Check request status
    REQUEST_STATUS=$(AWS_PROFILE=trillium-global aws service-quotas get-requested-service-quota-change \
        --request-id $REQUEST_ID \
        --region us-east-1 \
        --query 'RequestedQuota.Status' \
        --output text 2>/dev/null || echo "UNKNOWN")

    echo "  Current Quota: $CURRENT_QUOTA vCPUs"
    echo "  Request Status: $REQUEST_STATUS"

    # Check if quota has been increased
    if [ "$CURRENT_QUOTA" != "8" ] && [ "$CURRENT_QUOTA" != "8.0" ]; then
        if (( $(echo "$CURRENT_QUOTA >= $REQUIRED_VCPUS" | bc -l) )); then
            echo ""
            echo "================================================================================"
            echo "✅ QUOTA INCREASE APPROVED!"
            echo "================================================================================"
            echo ""
            echo "New Quota: $CURRENT_QUOTA vCPUs"
            echo "Required: $REQUIRED_VCPUS vCPUs"
            echo ""
            echo "Proceeding to launch temporary Phase 2 worker..."
            echo ""

            # Launch temporary worker
            cd /home/ubuntu/bqx-ml
            bash scripts/infrastructure/launch_temporary_phase2_ec2.sh

            exit 0
        fi
    fi

    # Check if request was approved or denied
    if [ "$REQUEST_STATUS" = "APPROVED" ]; then
        echo ""
        echo "✅ Request approved! Quota should update within minutes."
        echo "   Continuing to monitor actual quota value..."
    elif [ "$REQUEST_STATUS" = "DENIED" ] || [ "$REQUEST_STATUS" = "CLOSED" ]; then
        echo ""
        echo "❌ Quota increase request was $REQUEST_STATUS"
        echo ""
        echo "Please review the request in AWS Console:"
        echo "https://console.aws.amazon.com/servicequotas/home/services/ec2/quotas/L-1216C47A"
        exit 1
    fi

    echo ""
    sleep $CHECK_INTERVAL
    ELAPSED=$((ELAPSED + CHECK_INTERVAL))
done

echo ""
echo "================================================================================"
echo "⏰ TIMEOUT REACHED"
echo "================================================================================"
echo ""
echo "Quota increase request is still pending after $((MAX_WAIT / 60)) minutes."
echo ""
echo "Current Status: $REQUEST_STATUS"
echo "Current Quota: $CURRENT_QUOTA vCPUs"
echo ""
echo "Options:"
echo "  1. Continue waiting (request may take up to 2 business days)"
echo "  2. Check AWS Support case: 176315597600934"
echo "  3. Manually launch once approved:"
echo "     bash /home/ubuntu/bqx-ml/scripts/infrastructure/launch_temporary_phase2_ec2.sh"
echo ""
echo "================================================================================"
