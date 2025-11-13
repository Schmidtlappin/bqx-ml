#!/bin/bash
################################################################################
# Parallel Execution Monitor - Real-Time Progress Tracking
# Monitors all 3 tracks (Bollinger BQX, Regression Features, Feature Extraction)
################################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Clear screen and hide cursor
clear
tput civis

# Trap to restore cursor on exit
trap 'tput cnorm; exit' INT TERM EXIT

while true; do
    clear
    echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║           PHASE 2: PARALLEL EXECUTION - REAL-TIME MONITOR                      ║${NC}"
    echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Timestamp
    echo -e "${BOLD}Last Updated:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # ============================================================================
    # SYSTEM RESOURCES
    # ============================================================================
    echo -e "${BOLD}${YELLOW}▶ SYSTEM RESOURCES${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # CPU Load
    load=$(uptime | awk -F'load average:' '{print $2}')
    echo -e "  ${CYAN}CPU Load:${NC}      $load (8 cores available)"

    # Memory
    mem_info=$(free -h | awk '/^Mem:/ {print $3 " / " $2 " (" int($3/$2 * 100) "%)"}')
    echo -e "  ${CYAN}Memory:${NC}        $mem_info"

    # Disk
    disk_info=$(df -h /home/ubuntu | awk 'NR==2 {print $3 " / " $2 " (" $5 " used)"}')
    echo -e "  ${CYAN}Disk:${NC}          $disk_info"

    # Active Python processes
    python_procs=$(ps aux | grep python3 | grep -E "(extract_features|populate_bollinger|populate_regression)" | grep -v grep | wc -l)
    echo -e "  ${CYAN}Python Workers:${NC} $python_procs processes running"
    echo ""

    # ============================================================================
    # TRACK 3: FEATURE EXTRACTION (FASTEST)
    # ============================================================================
    echo -e "${BOLD}${GREEN}▶ TRACK 3: FEATURE EXTRACTION${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if [ -f /tmp/logs/track3/extract.log ]; then
        # Count completed extractions
        track3_complete=$(grep -c "✅.*Complete!" /tmp/logs/track3/extract.log 2>/dev/null || echo 0)
        track3_failed=$(grep -c "❌.*Failed" /tmp/logs/track3/extract.log 2>/dev/null || echo 0)
        track3_total=28
        track3_pct=$(echo "scale=1; $track3_complete * 100 / $track3_total" | bc 2>/dev/null || echo "0")

        # Progress bar
        track3_filled=$(echo "$track3_complete * 50 / $track3_total" | bc 2>/dev/null || echo 0)
        track3_empty=$((50 - track3_filled))
        track3_bar=$(printf "%${track3_filled}s" | tr ' ' '█')$(printf "%${track3_empty}s" | tr ' ' '░')

        echo -e "  ${CYAN}Progress:${NC}      [${GREEN}${track3_bar}${NC}] ${BOLD}${track3_pct}%${NC}"
        echo -e "  ${CYAN}Completed:${NC}     ${GREEN}${track3_complete}${NC}/${track3_total} pairs"
        if [ $track3_failed -gt 0 ]; then
            echo -e "  ${CYAN}Failed:${NC}        ${RED}${track3_failed}${NC} pairs"
        fi

        # Latest activity
        latest_t3=$(tail -3 /tmp/logs/track3/extract.log 2>/dev/null | grep -E "(Starting extraction|Complete|Failed)" | tail -1)
        if [ ! -z "$latest_t3" ]; then
            echo -e "  ${CYAN}Latest:${NC}        $latest_t3"
        fi

        # Check if complete
        if [ $track3_complete -eq $track3_total ]; then
            echo -e "  ${GREEN}${BOLD}✓ TRACK 3 COMPLETE!${NC}"

            # List Parquet files
            parquet_count=$(ls -1 /home/ubuntu/bqx-ml/data/extracted/*.parquet 2>/dev/null | wc -l)
            parquet_size=$(du -sh /home/ubuntu/bqx-ml/data/extracted/ 2>/dev/null | awk '{print $1}')
            echo -e "  ${CYAN}Output:${NC}        $parquet_count Parquet files ($parquet_size)"
        fi
    else
        echo -e "  ${YELLOW}⚠ Log file not found${NC}"
    fi
    echo ""

    # ============================================================================
    # TRACK 1: BOLLINGER BQX FEATURES
    # ============================================================================
    echo -e "${BOLD}${GREEN}▶ TRACK 1: BOLLINGER BQX FEATURES${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if [ -f /tmp/logs/track1/bollinger.log ]; then
        # Count completed tasks
        track1_complete=$(grep -c "✅.*Complete!" /tmp/logs/track1/bollinger.log 2>/dev/null || echo 0)
        track1_failed=$(grep -c "❌.*Failed" /tmp/logs/track1/bollinger.log 2>/dev/null || echo 0)
        track1_nodata=$(grep -c "No BQX data found" /tmp/logs/track1/bollinger.log 2>/dev/null || echo 0)
        track1_total=672  # 28 pairs × 24 months
        track1_pct=$(echo "scale=1; $track1_complete * 100 / $track1_total" | bc 2>/dev/null || echo "0")

        # Progress bar
        track1_filled=$(echo "$track1_complete * 50 / $track1_total" | bc 2>/dev/null || echo 0)
        track1_empty=$((50 - track1_filled))
        track1_bar=$(printf "%${track1_filled}s" | tr ' ' '█')$(printf "%${track1_empty}s" | tr ' ' '░')

        echo -e "  ${CYAN}Progress:${NC}      [${GREEN}${track1_bar}${NC}] ${BOLD}${track1_pct}%${NC}"
        echo -e "  ${CYAN}Completed:${NC}     ${GREEN}${track1_complete}${NC}/${track1_total} partitions"
        if [ $track1_failed -gt 0 ]; then
            echo -e "  ${CYAN}Failed:${NC}        ${RED}${track1_failed}${NC} partitions"
        fi
        if [ $track1_nodata -gt 0 ]; then
            echo -e "  ${CYAN}No Data:${NC}       ${YELLOW}${track1_nodata}${NC} partitions (expected for future months)"
        fi

        # Latest activity
        latest_t1=$(tail -5 /tmp/logs/track1/bollinger.log 2>/dev/null | grep -E "(Starting|Complete|Failed)" | tail -1)
        if [ ! -z "$latest_t1" ]; then
            echo -e "  ${CYAN}Latest:${NC}        $latest_t1"
        fi

        # Check if still running
        track1_running=$(ps aux | grep populate_bollinger | grep -v grep | wc -l)
        if [ $track1_running -eq 0 ] && [ $track1_complete -lt $track1_total ]; then
            echo -e "  ${RED}${BOLD}⚠ TRACK 1 STOPPED UNEXPECTEDLY${NC}"
        elif [ $track1_complete -ge $((track1_total - track1_nodata)) ]; then
            echo -e "  ${GREEN}${BOLD}✓ TRACK 1 COMPLETE!${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠ Log file not found${NC}"
    fi
    echo ""

    # ============================================================================
    # TRACK 2: REGRESSION FEATURES (SLOWEST)
    # ============================================================================
    echo -e "${BOLD}${GREEN}▶ TRACK 2: REGRESSION FEATURES (MOST COMPUTE-INTENSIVE)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if [ -f /tmp/logs/track2/populate.log ]; then
        # Count completed tasks
        track2_complete=$(grep -c "✅.*Complete!" /tmp/logs/track2/populate.log 2>/dev/null || echo 0)
        track2_failed=$(grep -c "❌.*Failed" /tmp/logs/track2/populate.log 2>/dev/null || echo 0)
        track2_nodata=$(grep -c "No.*data" /tmp/logs/track2/populate.log 2>/dev/null || echo 0)
        track2_total=336  # 28 pairs × 12 months (Jul 2024 - Jun 2025)
        track2_pct=$(echo "scale=1; $track2_complete * 100 / $track2_total" | bc 2>/dev/null || echo "0")

        # Progress bar
        track2_filled=$(echo "$track2_complete * 50 / $track2_total" | bc 2>/dev/null || echo 0)
        track2_empty=$((50 - track2_filled))
        track2_bar=$(printf "%${track2_filled}s" | tr ' ' '█')$(printf "%${track2_empty}s" | tr ' ' '░')

        echo -e "  ${CYAN}Progress:${NC}      [${GREEN}${track2_bar}${NC}] ${BOLD}${track2_pct}%${NC}"
        echo -e "  ${CYAN}Completed:${NC}     ${GREEN}${track2_complete}${NC}/${track2_total} partitions"
        if [ $track2_failed -gt 0 ]; then
            echo -e "  ${CYAN}Failed:${NC}        ${RED}${track2_failed}${NC} partitions"
        fi

        # Latest activity (show what's being computed)
        latest_t2=$(tail -5 /tmp/logs/track2/populate.log 2>/dev/null | grep -E "(Starting|Computing|Complete|Failed)" | tail -2)
        if [ ! -z "$latest_t2" ]; then
            echo -e "  ${CYAN}Latest:${NC}"
            echo "$latest_t2" | while read line; do
                echo -e "                 $line"
            done
        fi

        # Check if still running
        track2_running=$(ps aux | grep populate_regression | grep -v grep | wc -l)
        if [ $track2_running -eq 0 ] && [ $track2_complete -lt $track2_total ]; then
            echo -e "  ${RED}${BOLD}⚠ TRACK 2 STOPPED UNEXPECTEDLY${NC}"
        elif [ $track2_complete -eq $track2_total ]; then
            echo -e "  ${GREEN}${BOLD}✓ TRACK 2 COMPLETE!${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠ Log file not found${NC}"
    fi
    echo ""

    # ============================================================================
    # OVERALL STATUS
    # ============================================================================
    echo -e "${BOLD}${YELLOW}▶ OVERALL STATUS${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Calculate overall progress
    total_tasks=$((track3_total + track1_total + track2_total))
    completed_tasks=$((track3_complete + track1_complete + track2_complete))
    overall_pct=$(echo "scale=1; $completed_tasks * 100 / $total_tasks" | bc 2>/dev/null || echo "0")

    echo -e "  ${CYAN}Total Progress:${NC} ${BOLD}${overall_pct}%${NC} (${completed_tasks}/${total_tasks} tasks)"
    echo ""

    # Estimated completion (rough estimate based on current progress)
    if [ $completed_tasks -gt 0 ]; then
        # Track 3 ETA
        if [ $track3_complete -lt $track3_total ]; then
            track3_remaining=$((track3_total - track3_complete))
            track3_eta=$((track3_remaining * 55 / 60))  # ~55 seconds per pair
            echo -e "  ${CYAN}Track 3 ETA:${NC}    ~${track3_eta} minutes"
        fi

        # Track 1 ETA
        if [ $track1_complete -lt $((track1_total - track1_nodata)) ]; then
            track1_remaining=$((track1_total - track1_nodata - track1_complete))
            track1_eta=$((track1_remaining * 7 / 60))  # ~7 seconds per partition
            echo -e "  ${CYAN}Track 1 ETA:${NC}    ~${track1_eta} minutes"
        fi

        # Track 2 ETA (slowest)
        if [ $track2_complete -lt $track2_total ]; then
            track2_remaining=$((track2_total - track2_complete))
            track2_eta=$((track2_remaining * 8))  # ~8 minutes per partition (4 workers)
            track2_eta_hours=$((track2_eta / 60))
            echo -e "  ${CYAN}Track 2 ETA:${NC}    ~${track2_eta} minutes (~${track2_eta_hours} hours)"
        fi
    fi
    echo ""

    # ============================================================================
    # QUICK ACTIONS
    # ============================================================================
    echo -e "${BOLD}${MAGENTA}▶ QUICK ACTIONS${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  ${CYAN}View Track 1 Log:${NC}  tail -f /tmp/logs/track1/bollinger.log"
    echo -e "  ${CYAN}View Track 2 Log:${NC}  tail -f /tmp/logs/track2/populate.log"
    echo -e "  ${CYAN}View Track 3 Log:${NC}  tail -f /tmp/logs/track3/extract.log"
    echo -e "  ${CYAN}Stop All Tracks:${NC}   pkill -f 'populate_bollinger|populate_regression|extract_features'"
    echo -e "  ${CYAN}System Monitor:${NC}     htop"
    echo ""
    echo -e "${BOLD}Press Ctrl+C to exit${NC}"

    # Refresh every 5 seconds
    sleep 5
done
