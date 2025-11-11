#!/bin/bash
# Real-time monitor for BQX and REG backfill processes

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

    if [ "$completed" -eq 0 ]; then
        echo "N/A"
        return
    fi

    local rate=$(echo "scale=4; $completed / $elapsed_seconds" | bc)
    local remaining=$(echo "$total - $completed" | bc)
    local eta_seconds=$(echo "scale=0; $remaining / $rate" | bc)

    local hours=$(echo "$eta_seconds / 3600" | bc)
    local minutes=$(echo "($eta_seconds % 3600) / 60" | bc)

    echo "${hours}h ${minutes}m"
}

# Function to get BQX status
get_bqx_status() {
    # Process info - get only the main python process, not nohup wrappers
    local bqx_proc=$(ps aux | grep '[p]ython.*backward_worker_index.py' | grep -v 'nohup' | head -1)

    if [ -z "$bqx_proc" ]; then
        echo -e "${RED}❌ NOT RUNNING${NC}"
        return
    fi

    local pid=$(echo "$bqx_proc" | awk '{print $2}')
    local cpu=$(echo "$bqx_proc" | awk '{print $3}')
    local mem=$(echo "$bqx_proc" | awk '{print $4}')
    local time=$(echo "$bqx_proc" | awk '{print $10}')

    # Parse CPU time to seconds (strip leading zeros to avoid octal interpretation)
    local time_parts=(${time//:/ })
    if [ ${#time_parts[@]} -eq 2 ]; then
        local mins=$((10#${time_parts[0]}))
        local secs=$((10#${time_parts[1]}))
        elapsed_seconds=$(( mins * 60 + secs ))
    else
        elapsed_seconds=60
    fi

    # Database stats with -A flag for unaligned output
    local db_stats=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -A -c "
        SELECT
            COUNT(*) FILTER (WHERE n_live_tup > 0),
            COALESCE(SUM(n_live_tup), 0),
            pg_size_pretty(COALESCE(SUM(pg_total_relation_size('bqx.' || relname)), 0))
        FROM pg_stat_user_tables
        WHERE relname LIKE 'bqx_%_y%_m%';
    " 2>/dev/null)

    local populated=$(echo "$db_stats" | cut -d'|' -f1)
    local rows=$(echo "$db_stats" | cut -d'|' -f2)
    local size=$(echo "$db_stats" | cut -d'|' -f3)

    # Handle empty values
    populated=${populated:-0}
    rows=${rows:-0}
    size=${size:-0 bytes}

    local total_partitions=336
    local progress=$(echo "scale=1; ($populated * 100) / $total_partitions" | bc 2>/dev/null || echo "0.0")
    local eta=$(calculate_eta "$populated" "$total_partitions" "$elapsed_seconds")

    echo -e "${GREEN}✓ RUNNING${NC} (PID: ${CYAN}$pid${NC})"
    echo -e "  CPU: ${YELLOW}${cpu}%${NC}  |  Memory: ${YELLOW}${mem}%${NC}  |  Runtime: ${CYAN}${time}${NC}"
    echo -e "  Progress: ${BOLD}${populated}/${total_partitions}${NC} partitions (${GREEN}${progress}%${NC})"
    echo -e "  Rows: ${BOLD}$(format_number $rows)${NC}  |  Size: ${CYAN}${size}${NC}"
    echo -e "  ETA: ${YELLOW}${eta}${NC}"
}

# Function to get REG status
get_reg_status() {
    # Process info - get only the main python process, not nohup wrappers
    local reg_proc=$(ps aux | grep '[p]ython.*regression_worker_index.py' | grep -v 'nohup' | head -1)

    if [ -z "$reg_proc" ]; then
        echo -e "${RED}❌ NOT RUNNING${NC}"
        return
    fi

    local pid=$(echo "$reg_proc" | awk '{print $2}')
    local cpu=$(echo "$reg_proc" | awk '{print $3}')
    local mem=$(echo "$reg_proc" | awk '{print $4}')
    local time=$(echo "$reg_proc" | awk '{print $10}')

    # Parse CPU time to seconds (strip leading zeros to avoid octal interpretation)
    local time_parts=(${time//:/ })
    if [ ${#time_parts[@]} -eq 2 ]; then
        local mins=$((10#${time_parts[0]}))
        local secs=$((10#${time_parts[1]}))
        elapsed_seconds=$(( mins * 60 + secs ))
    else
        elapsed_seconds=60
    fi

    # Parse progress from log file (more accurate than pg_stat which lags)
    local log_file="/tmp/stage_1_5_5_3_backfill.log"
    local last_progress=""

    if [ -f "$log_file" ]; then
        last_progress=$(grep -o "Progress:[[:space:]]*[0-9.]*%" "$log_file" | tail -1 | grep -o "[0-9.]*")
    fi

    # Calculate partitions from progress percentage
    local total_jobs=448
    local populated=0
    if [ -n "$last_progress" ]; then
        populated=$(echo "scale=0; ($last_progress * $total_jobs) / 100" | bc 2>/dev/null)
    fi

    # Get approximate row count from log
    local rows=0
    if [ -f "$log_file" ]; then
        rows=$(grep -o "[0-9,]*[0-9] rows" "$log_file" | tr -d ',' | awk '{sum+=$1} END {print sum}')
    fi
    rows=${rows:-0}

    # Get actual size from database (query partition tables directly, not parent tables)
    local size=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -A -c "
        SELECT pg_size_pretty(
            COALESCE(SUM(pg_total_relation_size('bqx.' || tablename)), 0)
        )
        FROM pg_tables
        WHERE schemaname = 'bqx' AND tablename ~ '^reg_[a-z]+_[0-9]{4}_[0-9]{2}$';
    " 2>/dev/null | tr -d ' ')
    size=${size:-0 bytes}

    local total_jobs=448
    local progress=$(echo "scale=1; ($populated * 100) / $total_jobs" | bc 2>/dev/null || echo "0.0")
    local eta=$(calculate_eta "$populated" "$total_jobs" "$elapsed_seconds")

    echo -e "${GREEN}✓ RUNNING${NC} (PID: ${CYAN}$pid${NC})"
    echo -e "  CPU: ${YELLOW}${cpu}%${NC}  |  Memory: ${YELLOW}${mem}%${NC}  |  Runtime: ${CYAN}${time}${NC}"
    echo -e "  Progress: ${BOLD}${populated}/${total_jobs}${NC} partitions (${GREEN}${progress}%${NC})"
    echo -e "  Rows: ${BOLD}$(format_number $rows)${NC}  |  Size: ${CYAN}${size}${NC}"
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
    echo -e "${BOLD}${BLUE}║${NC}  ${BOLD}BQX ML BACKFILL MONITOR${NC}                                $(date '+%Y-%m-%d %H:%M:%S')  ${BOLD}${BLUE}║${NC}"
    echo -e "${BOLD}${BLUE}╚════════════════════════════════════════════════════════════════════════════╝${NC}"

    echo ""
    echo -e "${BOLD}${CYAN}┌─ BQX Backfill (Stage 1.5.4.3) ────────────────────────────────────────────┐${NC}"
    get_bqx_status
    echo -e "${BOLD}${CYAN}└────────────────────────────────────────────────────────────────────────────┘${NC}"

    echo ""
    echo -e "${BOLD}${YELLOW}Recent BQX Log (last 3 lines):${NC}"
    echo -e "${BLUE}────────────────────────────────────────────────────────────────────────────${NC}"
    get_recent_logs "/tmp/stage_1_5_4_3_backfill.log" 3

    echo ""
    echo -e "${BOLD}${CYAN}┌─ REG Backfill (Stage 1.5.5.3) ────────────────────────────────────────────┐${NC}"
    get_reg_status
    echo -e "${BOLD}${CYAN}└────────────────────────────────────────────────────────────────────────────┘${NC}"

    echo ""
    echo -e "${BOLD}${YELLOW}Recent REG Log (last 3 lines):${NC}"
    echo -e "${BLUE}────────────────────────────────────────────────────────────────────────────${NC}"
    get_recent_logs "/tmp/stage_1_5_5_3_backfill.log" 3

    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}Press Ctrl+C to exit${NC}  |  Refreshing every 10 seconds..."

    sleep 10
done
