#!/bin/bash
# Real-time BQX Backfill Monitor

# Find the most recent restart log
LOG_FILE=$(ls -t /tmp/bqx_backfill_restart_*.log 2>/dev/null | head -1)

if [ -z "$LOG_FILE" ]; then
    echo "ERROR: No backfill restart log found!"
    echo "Looking for: /tmp/bqx_backfill_restart_*.log"
    exit 1
fi

echo "=========================================="
echo "BQX Backfill Real-time Monitor"
echo "=========================================="
echo "Log file: $LOG_FILE"
echo "Started: $(stat -c %y "$LOG_FILE" | cut -d'.' -f1)"
echo ""
echo "Press Ctrl+C to exit"
echo "=========================================="
echo ""

# Use tail -f to follow the log in real-time
# Add line numbers and highlight progress lines
tail -f "$LOG_FILE" | while read line; do
    if [[ "$line" =~ Progress ]]; then
        # Highlight progress lines in green
        echo -e "\033[1;32m$line\033[0m"
    elif [[ "$line" =~ ERROR ]]; then
        # Highlight errors in red
        echo -e "\033[1;31m$line\033[0m"
    elif [[ "$line" =~ COMPLETE ]]; then
        # Highlight completion in cyan
        echo -e "\033[1;36m$line\033[0m"
    else
        echo "$line"
    fi
done
