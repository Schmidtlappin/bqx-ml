#!/bin/bash
# Monitor Stage 1.5.2 progress

LOG_FILE="/tmp/stage_1_5_2_execution.log"

echo "==========================================="
echo "Stage 1.5.2 Progress Monitor"
echo "==========================================="
echo ""

if [ ! -f "$LOG_FILE" ]; then
    echo "Log file not found: $LOG_FILE"
    exit 1
fi

echo "Latest output:"
echo "-------------------------------------------"
tail -20 "$LOG_FILE"
echo "-------------------------------------------"
echo ""

# Count completed pairs
COMPLETED=$(grep -c "complete (" "$LOG_FILE" || echo "0")
echo "Progress: $COMPLETED/28 pairs processed"
echo ""

# Check for any errors
ERRORS=$(grep -i "error" "$LOG_FILE" | wc -l)
if [ "$ERRORS" -gt 0 ]; then
    echo "⚠️  Errors detected: $ERRORS"
    echo "Last error:"
    grep -i "error" "$LOG_FILE" | tail -1
else
    echo "✓ No errors detected"
fi

echo ""
echo "To monitor continuously: watch -n 30 $0"
