#!/bin/bash
# Real-time monitoring dashboard for Stage 2.12 execution
# Shows progress, current pair, ETA, and recent activity

# Set TERM if not set (for non-interactive shells)
export TERM=${TERM:-xterm}

LOG_FILE="/tmp/logs/remediation/stage_2_12/rebuild.log"
TOTAL_PAIRS=28
REFRESH_INTERVAL=10  # seconds

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

while true; do
    clear

    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║            STAGE 2.12: REBUILD reg_bqx - LIVE MONITOR                       ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo ""

    # Check if log file exists
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${RED}❌ Log file not found: $LOG_FILE${NC}"
        echo "Stage 2.12 may not have started yet."
        sleep $REFRESH_INTERVAL
        continue
    fi

    # Get pairs completed (trim whitespace)
    PAIRS_COMPLETE=$(grep -c "rebuild complete" "$LOG_FILE" 2>/dev/null | tr -d '\n\r' || echo "0")
    PAIRS_COMPLETE=${PAIRS_COMPLETE:-0}

    # Get partitions completed (trim whitespace)
    PARTITIONS_COMPLETE=$(grep -c "✅.*Complete!" "$LOG_FILE" 2>/dev/null | tr -d '\n\r' || echo "0")
    PARTITIONS_COMPLETE=${PARTITIONS_COMPLETE:-0}

    # Get current pair
    CURRENT_PAIR=$(tail -50 "$LOG_FILE" 2>/dev/null | grep "Starting rebuild" | tail -1 | awk '{print $4}' | tr -d ':' || echo "")

    # Get latest activity
    LATEST_COMPLETE=$(tail -20 "$LOG_FILE" 2>/dev/null | grep "✅.*Complete!" | tail -1 || echo "")

    # Calculate progress (ensure valid integers)
    if [ "$PAIRS_COMPLETE" -eq 0 ] 2>/dev/null; then
        PROGRESS_PCT="0.0"
    else
        PROGRESS_PCT=$(echo "scale=1; $PAIRS_COMPLETE * 100 / $TOTAL_PAIRS" | bc 2>/dev/null || echo "0.0")
    fi

    # Estimate ETA (if we have enough data)
    if [ "$PAIRS_COMPLETE" -gt 0 ]; then
        START_TIME=$(head -20 "$LOG_FILE" | grep "STAGE 2.12" | head -1 | awk '{print $1, $2}')
        CURRENT_TIME=$(date '+%Y-%m-%d %H:%M:%S')

        # Calculate pairs remaining
        PAIRS_REMAINING=$((TOTAL_PAIRS - PAIRS_COMPLETE))

        # Simple ETA calculation (pairs remaining * avg time per pair)
        if [ "$PAIRS_COMPLETE" -gt 2 ]; then
            AVG_TIME_PER_PAIR=8  # minutes (rough estimate)
            ETA_MINUTES=$((PAIRS_REMAINING * AVG_TIME_PER_PAIR))
            ETA_HOURS=$((ETA_MINUTES / 60))
            ETA_MINS=$((ETA_MINUTES % 60))

            # Calculate finish time
            FINISH_TIME=$(date -d "+${ETA_MINUTES} minutes" '+%H:%M UTC' 2>/dev/null || echo "Unknown")
        else
            FINISH_TIME="Calculating..."
        fi
    else
        FINISH_TIME="Calculating..."
    fi

    # Display progress bar (convert float to int safely)
    PROGRESS_INT=$(echo "$PROGRESS_PCT / 1" | bc 2>/dev/null || echo "0")
    PROGRESS_BARS=$((PROGRESS_INT / 4))  # Scale to 25 bars max
    PROGRESS_BARS=${PROGRESS_BARS:-0}
    EMPTY_BARS=$((25 - PROGRESS_BARS))
    EMPTY_BARS=${EMPTY_BARS:-25}

    echo -e "${BLUE}▶ OVERALL PROGRESS${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    printf "  Progress:       ["
    printf "${GREEN}█${NC}%.0s" $(seq 1 $PROGRESS_BARS)
    printf "░%.0s" $(seq 1 $EMPTY_BARS)
    printf "] ${YELLOW}%.1f%%${NC} (%d/%d pairs)\n" "$PROGRESS_PCT" "$PAIRS_COMPLETE" "$TOTAL_PAIRS"

    if [ -n "$CURRENT_PAIR" ]; then
        echo -e "  Current Pair:   ${YELLOW}$CURRENT_PAIR${NC}"
    else
        echo -e "  Current Pair:   ${YELLOW}Starting...${NC}"
    fi

    echo "  Partitions:     $PARTITIONS_COMPLETE/336 complete"
    echo -e "  Estimated ETA:  ${GREEN}$FINISH_TIME${NC}"
    echo ""

    # Display system resources
    echo -e "${BLUE}▶ SYSTEM RESOURCES${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # CPU load
    LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}')
    echo "  CPU Load:       $LOAD"

    # Memory usage
    MEM_INFO=$(free -h | grep Mem)
    MEM_USED=$(echo $MEM_INFO | awk '{print $3}')
    MEM_TOTAL=$(echo $MEM_INFO | awk '{print $2}')
    echo "  Memory:         $MEM_USED / $MEM_TOTAL"

    # Check if process is running
    if ps aux | grep -q "[s]tage_2_12_rebuild_reg_bqx.py"; then
        echo -e "  Status:         ${GREEN}✅ Running${NC}"
    else
        echo -e "  Status:         ${RED}⚠ Not running (may have completed or failed)${NC}"
    fi

    echo ""

    # Display recent activity
    echo -e "${BLUE}▶ RECENT ACTIVITY (Last 10 lines)${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tail -10 "$LOG_FILE" | while read line; do
        if echo "$line" | grep -q "✅"; then
            echo -e "  ${GREEN}$line${NC}"
        elif echo "$line" | grep -q "❌"; then
            echo -e "  ${RED}$line${NC}"
        elif echo "$line" | grep -q "WARNING"; then
            echo -e "  ${YELLOW}$line${NC}"
        else
            echo "  $line"
        fi
    done

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "  Refreshing every ${REFRESH_INTERVAL} seconds... Press Ctrl+C to exit"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${BLUE}Quick Commands:${NC}"
    echo "  View full log:     tail -f $LOG_FILE"
    echo "  Check process:     ps aux | grep stage_2_12"
    echo "  Kill process:      pkill -f stage_2_12_rebuild_reg_bqx.py"
    echo ""

    sleep $REFRESH_INTERVAL
done
