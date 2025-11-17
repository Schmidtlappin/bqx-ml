#!/bin/bash
##
## Stage 2.14 Real-Time Progress Monitor
##
## Usage: bash monitor_stage_2_14.sh
##

LOG_FILE="/tmp/logs/remediation/stage_2_14/reg_bqx_covariance.log"
TOTAL_PARTITIONS=336
TOTAL_PAIRS=28

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Function to print header
print_header() {
    clear
    echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${BLUE}                    STAGE 2.14: TERM COVARIANCE FEATURES                        ${NC}"
    echo -e "${BOLD}${BLUE}                         Real-Time Progress Monitor                             ${NC}"
    echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Function to format duration
format_duration() {
    local seconds=$1
    local hours=$((seconds / 3600))
    local minutes=$(((seconds % 3600) / 60))
    local secs=$((seconds % 60))
    printf "%02d:%02d:%02d" $hours $minutes $secs
}

# Function to get progress stats
get_stats() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "Waiting for log file..."
        return
    fi

    # Count completed partitions
    local completed=$(grep -c "✅.*Complete!" "$LOG_FILE" 2>/dev/null || echo "0")

    # Count errors
    local errors=$(grep -c "❌.*Error" "$LOG_FILE" 2>/dev/null || echo "0")

    # Get current pair
    local current_pair=$(grep "Starting$" "$LOG_FILE" | tail -1 | awk '{print $4}' | tr -d ':')

    # Get current partition
    local current_partition=$(grep "Loaded.*rows" "$LOG_FILE" | tail -1 | awk '{print $4}')

    # Get rows updated
    local rows_updated=$(grep "Updated.*rows" "$LOG_FILE" | tail -1 | awk '{print $5}' | cut -d'/' -f1)
    local total_rows=$(grep "Updated.*rows" "$LOG_FILE" | tail -1 | awk '{print $5}' | cut -d'/' -f2)

    # Calculate progress percentage
    local progress_pct=0
    if [ "$completed" -gt 0 ]; then
        progress_pct=$((completed * 100 / TOTAL_PARTITIONS))
    fi

    # Get start time
    local start_time=$(head -1 "$LOG_FILE" | awk '{print $1, $2}')

    # Calculate elapsed time
    local start_epoch=$(date -d "$start_time" +%s 2>/dev/null || echo "0")
    local now_epoch=$(date +%s)
    local elapsed=$((now_epoch - start_epoch))

    # Estimate time remaining
    local eta="Calculating..."
    if [ "$completed" -gt 0 ] && [ "$elapsed" -gt 0 ]; then
        local avg_time_per_partition=$((elapsed / completed))
        local remaining_partitions=$((TOTAL_PARTITIONS - completed))
        local eta_seconds=$((avg_time_per_partition * remaining_partitions))
        eta=$(format_duration $eta_seconds)
    fi

    # Print statistics
    print_header

    echo -e "${BOLD}📊 OVERALL PROGRESS${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "Partitions:        ${GREEN}${completed}${NC} / ${TOTAL_PARTITIONS} (${progress_pct}%)"

    # Progress bar
    local bar_width=60
    local filled=$((progress_pct * bar_width / 100))
    local empty=$((bar_width - filled))
    printf "Progress:          ["
    printf "${GREEN}%${filled}s${NC}" | tr ' ' '█'
    printf "%${empty}s" | tr ' ' '░'
    printf "] ${progress_pct}%%\n"

    echo -e "Errors:            ${RED}${errors}${NC}"
    echo ""

    echo -e "${BOLD}⏱️  TIMING${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "Elapsed:           ${CYAN}$(format_duration $elapsed)${NC}"
    echo -e "Est. Remaining:    ${YELLOW}${eta}${NC}"
    echo ""

    if [ -n "$current_pair" ]; then
        echo -e "${BOLD}🔄 CURRENT ACTIVITY${NC}"
        echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "Pair:              ${BOLD}${current_pair}${NC}"
        echo -e "Partition:         ${current_partition}"

        if [ -n "$rows_updated" ] && [ -n "$total_rows" ]; then
            local row_pct=$((rows_updated * 100 / total_rows))
            echo -e "Rows Updated:      ${rows_updated} / ${total_rows} (${row_pct}%)"
        fi
        echo ""
    fi

    echo -e "${BOLD}📈 FEATURES${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "Per Partition:     ${CYAN}36${NC} (6 windows × 6 covariance pairs)"
    echo -e "Total Target:      ${CYAN}1,008${NC} (36 × 28 pairs)"
    local features_added=$((completed * 36))
    echo -e "Features Added:    ${GREEN}${features_added}${NC} / 1,008"
    echo ""

    # Recent activity (last 5 lines)
    echo -e "${BOLD}📋 RECENT ACTIVITY${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tail -5 "$LOG_FILE" | while IFS= read -r line; do
        if echo "$line" | grep -q "✅"; then
            echo -e "${GREEN}${line}${NC}"
        elif echo "$line" | grep -q "❌"; then
            echo -e "${RED}${line}${NC}"
        elif echo "$line" | grep -q "Starting"; then
            echo -e "${BOLD}${line}${NC}"
        else
            echo "$line"
        fi
    done
    echo ""

    echo -e "${BOLD}ℹ️  CONTROLS${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "Press ${BOLD}Ctrl+C${NC} to exit monitor (process continues in background)"
    echo -e "Log file: ${CYAN}${LOG_FILE}${NC}"
    echo ""

    # Check if complete
    if [ "$completed" -eq "$TOTAL_PARTITIONS" ]; then
        echo -e "${BOLD}${GREEN}════════════════════════════════════════════════════════════════════════════════${NC}"
        echo -e "${BOLD}${GREEN}                         🎉 STAGE 2.14 COMPLETE! 🎉                            ${NC}"
        echo -e "${BOLD}${GREEN}════════════════════════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo -e "Total Partitions:  ${completed}"
        echo -e "Total Duration:    $(format_duration $elapsed)"
        echo -e "Total Features:    1,008"
        echo ""
        exit 0
    fi
}

# Main monitoring loop
echo "Starting Stage 2.14 monitor..."
echo "Waiting for log file: $LOG_FILE"
echo ""

# Wait for log file to exist
while [ ! -f "$LOG_FILE" ]; do
    sleep 1
done

# Monitor loop - update every 3 seconds
while true; do
    get_stats
    sleep 3
done
