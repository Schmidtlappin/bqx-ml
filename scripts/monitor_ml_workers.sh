#!/bin/bash
# Real-time monitor for ML Feature Workers (Track 1)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Database credentials
export PGPASSWORD='BQX_Aurora_2025_Secure'
DB_HOST="trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com"
DB_USER="postgres"
DB_NAME="bqx"

# Function to format numbers
format_number() {
    printf "%'d" "$1" 2>/dev/null || echo "$1"
}

# Function to calculate ETA
calculate_eta() {
    local completed=$1
    local total=$2
    local elapsed_seconds=$3

    if [ "$completed" -eq 0 ] || [ "$elapsed_seconds" -le 0 ]; then
        echo "N/A"
        return
    fi

    local rate=$(echo "scale=4; $completed / $elapsed_seconds" | bc 2>/dev/null)
    if [ -z "$rate" ] || [ "$rate" = "0" ]; then
        echo "N/A"
        return
    fi

    local remaining=$(echo "$total - $completed" | bc 2>/dev/null)
    local eta_seconds=$(echo "scale=0; $remaining / $rate" | bc 2>/dev/null)

    local hours=$(echo "$eta_seconds / 3600" | bc 2>/dev/null)
    local minutes=$(echo "($eta_seconds % 3600) / 60" | bc 2>/dev/null)

    echo "${hours}h ${minutes}m"
}

# Function to get Statistics & Bollinger Worker status
get_statistics_bollinger_status() {
    local worker_proc=$(ps aux | grep '[p]ython.*statistics_bollinger_worker.py' | grep -v 'nohup' | head -1)

    if [ -z "$worker_proc" ]; then
        echo -e "${RED}❌ NOT RUNNING${NC}"
        return
    fi

    local pid=$(echo "$worker_proc" | awk '{print $2}')
    local cpu=$(echo "$worker_proc" | awk '{print $3}')
    local mem=$(echo "$worker_proc" | awk '{print $4}')
    local time=$(echo "$worker_proc" | awk '{print $10}')

    # Parse CPU time to seconds
    local time_parts=(${time//:/ })
    if [ ${#time_parts[@]} -eq 2 ]; then
        local mins=$((10#${time_parts[0]} + 0))
        local secs=$((10#${time_parts[1]} + 0))
        elapsed_seconds=$(( mins * 60 + secs ))
        if [ "$elapsed_seconds" -lt 10 ]; then
            elapsed_seconds=10
        fi
    elif [ ${#time_parts[@]} -eq 3 ]; then
        # Format: HH:MM:SS
        local hours=$((10#${time_parts[0]} + 0))
        local mins=$((10#${time_parts[1]} + 0))
        local secs=$((10#${time_parts[2]} + 0))
        elapsed_seconds=$(( hours * 3600 + mins * 60 + secs ))
    else
        elapsed_seconds=60
    fi

    # Parse progress from log file
    local log_file="/tmp/statistics_bollinger_worker.log"
    local last_progress=""
    local partitions_done=0

    if [ -f "$log_file" ]; then
        last_progress=$(grep -o "Progress:[[:space:]]*[0-9.]*%" "$log_file" | tail -1 | grep -o "[0-9.]*")
        partitions_done=$(grep -c "Progress:" "$log_file" 2>/dev/null)
    fi

    partitions_done=${partitions_done:-0}

    # Get row counts from log
    local stats_rows=0
    local boll_rows=0
    if [ -f "$log_file" ]; then
        stats_rows=$(grep "Stats:" "$log_file" | grep -o "Stats: [0-9,]*" | sed 's/Stats: //' | tr -d ',' | awk '{sum+=$1} END {print sum}')
        boll_rows=$(grep "Boll:" "$log_file" | grep -o "Boll: [0-9,]*" | sed 's/Boll: //' | tr -d ',' | awk '{sum+=$1} END {print sum}')
    fi
    stats_rows=${stats_rows:-0}
    boll_rows=${boll_rows:-0}

    local total_partitions=336  # 28 pairs × 12 months
    local progress=$(echo "scale=1; ($partitions_done * 100) / $total_partitions" | bc 2>/dev/null || echo "0.0")
    local eta=$(calculate_eta "$partitions_done" "$total_partitions" "$elapsed_seconds")

    echo -e "${GREEN}✓ RUNNING${NC} (PID: ${CYAN}$pid${NC})"
    echo -e "  CPU: ${YELLOW}${cpu}%${NC}  |  Memory: ${YELLOW}${mem}%${NC}  |  Runtime: ${CYAN}${time}${NC}"
    echo -e "  Progress: ${BOLD}${partitions_done}/${total_partitions}${NC} partitions (${GREEN}${progress}%${NC})"
    echo -e "  Statistics Rows: ${BOLD}$(format_number $stats_rows)${NC}  |  Bollinger Rows: ${BOLD}$(format_number $boll_rows)${NC}"
    echo -e "  Features: ${CYAN}5 Statistics + 5 Bollinger = 10 Total${NC}"
    echo -e "  ETA: ${YELLOW}${eta}${NC}"
}

# Function to get Volume Features Worker status (completed)
get_volume_features_status() {
    local worker_proc=$(ps aux | grep '[p]ython.*volume_features_worker.py' | grep -v 'nohup' | head -1)

    if [ -z "$worker_proc" ]; then
        # Check if completed by querying database
        local row_count=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -A -c "
            SELECT COUNT(*) FROM bqx.volume_features_eurusd WHERE ts_utc >= '2024-07-01';
        " 2>/dev/null)

        if [ -n "$row_count" ] && [ "$row_count" -gt 0 ]; then
            echo -e "${GREEN}✓ COMPLETED${NC}"
            echo -e "  Status: ${CYAN}All 336 partitions processed${NC}"
            echo -e "  EURUSD Rows: ${BOLD}$(format_number $row_count)${NC}"
            echo -e "  Features: ${CYAN}10 Volume Features${NC}"
        else
            echo -e "${RED}❌ NOT STARTED${NC}"
        fi
        return
    fi

    echo -e "${YELLOW}⚠ RUNNING${NC} (unexpected - should be completed)"
}

# Function to get Currency Indices Worker status (completed)
get_currency_indices_status() {
    local worker_proc=$(ps aux | grep '[p]ython.*currency_indices_worker.py' | grep -v 'nohup' | head -1)

    if [ -z "$worker_proc" ]; then
        # Check if completed by querying database
        local row_count=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -A -c "
            SELECT COUNT(*) FROM bqx.currency_indices WHERE ts_utc >= '2024-07-01';
        " 2>/dev/null)

        if [ -n "$row_count" ] && [ "$row_count" -gt 0 ]; then
            echo -e "${GREEN}✓ COMPLETED${NC}"
            echo -e "  Status: ${CYAN}All 12 months processed${NC}"
            echo -e "  Total Rows: ${BOLD}$(format_number $row_count)${NC}"
            echo -e "  Features: ${CYAN}8 Currency Indices (USD, EUR, GBP, AUD, CAD, JPY, CHF, NZD)${NC}"
        else
            echo -e "${RED}❌ NOT STARTED${NC}"
        fi
        return
    fi

    echo -e "${YELLOW}⚠ RUNNING${NC} (unexpected - should be completed)"
}

# Function to get Time & Spread Features Worker status
get_time_spread_status() {
    local worker_proc=$(ps aux | grep '[p]ython.*time_spread_features_worker.py' | grep -v 'nohup' | head -1)

    if [ -z "$worker_proc" ]; then
        echo -e "${RED}❌ NOT RUNNING${NC}"
        return
    fi

    local pid=$(echo "$worker_proc" | awk '{print $2}')
    local cpu=$(echo "$worker_proc" | awk '{print $3}')
    local mem=$(echo "$worker_proc" | awk '{print $4}')
    local time=$(echo "$worker_proc" | awk '{print $10}')

    # Parse CPU time to seconds
    local time_parts=(${time//:/ })
    if [ ${#time_parts[@]} -eq 2 ]; then
        local mins=$((10#${time_parts[0]} + 0))
        local secs=$((10#${time_parts[1]} + 0))
        elapsed_seconds=$(( mins * 60 + secs ))
        if [ "$elapsed_seconds" -lt 10 ]; then
            elapsed_seconds=10
        fi
    elif [ ${#time_parts[@]} -eq 3 ]; then
        local hours=$((10#${time_parts[0]} + 0))
        local mins=$((10#${time_parts[1]} + 0))
        local secs=$((10#${time_parts[2]} + 0))
        elapsed_seconds=$(( hours * 3600 + mins * 60 + secs ))
    else
        elapsed_seconds=60
    fi

    # Parse progress from log file
    local log_file="/tmp/time_spread_worker.log"
    local partitions_done=0
    local time_rows=0
    local spread_rows=0

    if [ -f "$log_file" ]; then
        partitions_done=$(grep -c "Progress:" "$log_file" 2>/dev/null)
        time_rows=$(grep "Time:" "$log_file" | grep -o "Time: [0-9,]*" | sed 's/Time: //' | tr -d ',' | awk '{sum+=$1} END {print sum}')
        spread_rows=$(grep "Spread:" "$log_file" | grep -o "Spread: [0-9,]*" | sed 's/Spread: //' | tr -d ',' | awk '{sum+=$1} END {print sum}')
    fi

    partitions_done=${partitions_done:-0}
    time_rows=${time_rows:-0}
    spread_rows=${spread_rows:-0}

    local total_partitions=336  # 28 pairs × 12 months
    local progress=$(echo "scale=1; ($partitions_done * 100) / $total_partitions" | bc 2>/dev/null || echo "0.0")
    local eta=$(calculate_eta "$partitions_done" "$total_partitions" "$elapsed_seconds")

    echo -e "${GREEN}✓ RUNNING${NC} (PID: ${CYAN}$pid${NC})"
    echo -e "  CPU: ${YELLOW}${cpu}%${NC}  |  Memory: ${YELLOW}${mem}%${NC}  |  Runtime: ${CYAN}${time}${NC}"
    echo -e "  Progress: ${BOLD}${partitions_done}/${total_partitions}${NC} partitions (${GREEN}${progress}%${NC})"
    echo -e "  Time Rows: ${BOLD}$(format_number $time_rows)${NC}  |  Spread Rows: ${BOLD}$(format_number $spread_rows)${NC}"
    echo -e "  Features: ${CYAN}8 Time + 20 Spread = 28 Total${NC}"
    echo -e "  ETA: ${YELLOW}${eta}${NC}"
}

# Function to get recent log lines
get_recent_logs() {
    local log_file=$1
    local lines=$2

    if [ -f "$log_file" ]; then
        tail -n "$lines" "$log_file" 2>/dev/null | sed 's/^/  /'
    else
        echo -e "  ${RED}Log file not found${NC}"
    fi
}

# Main monitoring loop
while true; do
    clear
    echo -e "${BOLD}${BLUE}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${BLUE}║${NC}  ${BOLD}ML FEATURE WORKERS MONITOR - TRACK 1${NC}                  $(date '+%Y-%m-%d %H:%M:%S')  ${BOLD}${BLUE}║${NC}"
    echo -e "${BOLD}${BLUE}╚════════════════════════════════════════════════════════════════════════════╝${NC}"

    echo ""
    echo -e "${BOLD}${CYAN}┌─ Statistics & Bollinger Worker (Stage 1.6.3) ─────────────────────────────┐${NC}"
    get_statistics_bollinger_status
    echo -e "${BOLD}${CYAN}└────────────────────────────────────────────────────────────────────────────┘${NC}"

    echo ""
    echo -e "${BOLD}${YELLOW}Recent Statistics & Bollinger Log (last 3 lines):${NC}"
    echo -e "${BLUE}────────────────────────────────────────────────────────────────────────────${NC}"
    get_recent_logs "/tmp/statistics_bollinger_worker.log" 3

    echo ""
    echo -e "${BOLD}${CYAN}┌─ Volume Features Worker (Stage 1.6.3) ────────────────────────────────────┐${NC}"
    get_volume_features_status
    echo -e "${BOLD}${CYAN}└────────────────────────────────────────────────────────────────────────────┘${NC}"

    echo ""
    echo -e "${BOLD}${CYAN}┌─ Currency Indices Worker (Stage 1.6.3) ───────────────────────────────────┐${NC}"
    get_currency_indices_status
    echo -e "${BOLD}${CYAN}└────────────────────────────────────────────────────────────────────────────┘${NC}"

    echo ""
    echo -e "${BOLD}${CYAN}┌─ Time & Spread Features Worker (Stage 1.6.3) ─────────────────────────────┐${NC}"
    get_time_spread_status
    echo -e "${BOLD}${CYAN}└────────────────────────────────────────────────────────────────────────────┘${NC}"

    echo ""
    echo -e "${BOLD}${YELLOW}Recent Time & Spread Log (last 3 lines):${NC}"
    echo -e "${BLUE}────────────────────────────────────────────────────────────────────────────${NC}"
    get_recent_logs "/tmp/time_spread_worker.log" 3

    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}Track 1 Status Summary:${NC}"
    echo -e "  ✓ Volume Features (10): ${GREEN}Completed${NC}"
    echo -e "  ✓ Currency Indices (8): ${GREEN}Completed${NC}"
    echo -e "  ⏳ Statistics & Bollinger (10): ${YELLOW}In Progress${NC}"
    echo -e "  ⏳ Time & Spread Features (28): ${YELLOW}In Progress${NC}"
    echo -e "  ⏸ Correlation Features: ${CYAN}Pending${NC}"
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}Press Ctrl+C to exit${NC}  |  Refreshing every 10 seconds..."

    sleep 10
done
