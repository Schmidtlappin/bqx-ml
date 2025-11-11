#!/bin/bash
# Monitor Stage 1.5.4.3 BQX backfill progress

LOG_FILE="/tmp/stage_1_5_4_3_backfill.log"

echo "=========================================="
echo "Stage 1.5.4.3 Backfill Progress Monitor"
echo "=========================================="
echo ""

if [ ! -f "$LOG_FILE" ]; then
    echo "Log file not found: $LOG_FILE"
    exit 1
fi

echo "Latest output:"
echo "------------------------------------------"
tail -30 "$LOG_FILE"
echo "------------------------------------------"
echo ""

# Extract progress information
if grep -q "Progress:" "$LOG_FILE"; then
    LAST_PROGRESS=$(grep "Progress:" "$LOG_FILE" | tail -1)
    echo "Current Status: $LAST_PROGRESS"
fi

echo ""
echo "To monitor continuously: watch -n 30 $0"
echo "To view full log: tail -f $LOG_FILE"
