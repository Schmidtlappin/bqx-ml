#!/bin/bash
# Quick BQX Backfill Status Check

# Find the most recent restart log
LOG_FILE=$(ls -t /tmp/bqx_backfill_restart_*.log 2>/dev/null | head -1)

if [ -z "$LOG_FILE" ]; then
    echo "ERROR: No backfill restart log found!"
    exit 1
fi

# Get process info
PROCESS=$(ps aux | grep backward_worker_threaded.py | grep -v grep)

echo "=========================================="
echo "BQX Backfill Status"
echo "=========================================="
echo "Log file: $LOG_FILE"
echo "Started: $(stat -c %y "$LOG_FILE" | cut -d'.' -f1)"
echo ""

if [ -n "$PROCESS" ]; then
    PID=$(echo "$PROCESS" | head -1 | awk '{print $2}')
    CPU=$(echo "$PROCESS" | head -1 | awk '{print $3}')
    MEM=$(echo "$PROCESS" | head -1 | awk '{print $4}')
    echo "Status: RUNNING"
    echo "PID: $PID"
    echo "CPU: ${CPU}%"
    echo "Memory: ${MEM}%"
else
    echo "Status: NOT RUNNING"
fi

echo ""
echo "Latest Progress (last 10 lines):"
echo "=========================================="
tail -10 "$LOG_FILE" | grep -E "Progress|ERROR|COMPLETE" | tail -5

echo ""
echo "=========================================="

# Extract and show current progress percentage
LATEST_PROGRESS=$(tail -50 "$LOG_FILE" | grep -oP 'Progress:\s+\K[\d.]+(?=%)' | tail -1)
if [ -n "$LATEST_PROGRESS" ]; then
    echo "Current Progress: ${LATEST_PROGRESS}%"

    # Calculate jobs completed (336 total)
    JOBS_DONE=$(echo "$LATEST_PROGRESS * 336 / 100" | bc)
    echo "Jobs Completed: ${JOBS_DONE}/336"

    # Calculate estimated time remaining
    ELAPSED_SEC=$(($(date +%s) - $(stat -c %Y "$LOG_FILE")))
    ELAPSED_MIN=$((ELAPSED_SEC / 60))

    if [ $ELAPSED_MIN -eq 0 ]; then
        ELAPSED_MIN=1  # Minimum 1 minute for calculation
    fi

    echo "Elapsed Time: ${ELAPSED_MIN} minutes"

    if (( $(echo "$LATEST_PROGRESS > 1" | bc -l) )); then
        TOTAL_MIN=$(echo "scale=0; $ELAPSED_MIN / ($LATEST_PROGRESS / 100)" | bc 2>/dev/null)
        if [ -n "$TOTAL_MIN" ] && [ "$TOTAL_MIN" -gt 0 ]; then
            REMAINING_MIN=$(echo "$TOTAL_MIN - $ELAPSED_MIN" | bc)
            REMAINING_HOURS=$(echo "scale=1; $REMAINING_MIN / 60" | bc)
            echo "Estimated Remaining: ${REMAINING_MIN} minutes (~${REMAINING_HOURS} hours)"
        fi
    fi
fi

echo "=========================================="
echo ""
echo "Commands:"
echo "  Monitor live: /home/ubuntu/bqx-ml/scripts/backfill/monitor_backfill.sh"
echo "  Or simply: tail -f $LOG_FILE"
