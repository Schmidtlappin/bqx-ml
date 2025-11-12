#!/bin/bash
#
# Real-time Monitor for Phase 1.6 Workers
# Monitors: Fibonacci, Technical Indicators, and Correlation workers
#

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

clear

while true; do
    clear
    echo "================================================================================"
    echo "BQX ML - PHASE 1.6 WORKERS MONITOR"
    echo "================================================================================"
    echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # Worker 1: Fibonacci Features
    echo -e "${BLUE}[1] FIBONACCI FEATURES WORKER${NC}"
    echo "--------------------------------------------------------------------------------"
    FIB_PID=$(ps aux | grep "python3.*fibonacci_features_worker.py" | grep -v grep | grep -v "/bin/bash" | awk '{print $2}')
    if [ -n "$FIB_PID" ]; then
        FIB_CPU=$(ps -p $FIB_PID -o %cpu --no-headers 2>/dev/null | xargs)
        FIB_MEM=$(ps -p $FIB_PID -o %mem --no-headers 2>/dev/null | xargs)
        echo -e "Status: ${GREEN}RUNNING${NC} (PID: $FIB_PID)"
        echo "CPU: ${FIB_CPU}% | Memory: ${FIB_MEM}%"

        if [ -f /tmp/fibonacci_features_worker.log ]; then
            # Count completed partitions
            FIB_COMPLETED=$(grep -c "✓" /tmp/fibonacci_features_worker.log 2>/dev/null || echo "0")
            FIB_PROGRESS=$(echo "$FIB_COMPLETED" | awk '{printf "%.1f", $1 * 100 / 336}')
            FIB_LAST=$(tail -10 /tmp/fibonacci_features_worker.log | grep "✓" | tail -1)
            echo "Progress: ${FIB_COMPLETED}/336 partitions (${FIB_PROGRESS}%)"
            echo "Latest: $FIB_LAST"
        fi
    else
        echo -e "Status: ${RED}NOT RUNNING${NC}"
    fi
    echo ""

    # Worker 2: Technical Indicators
    echo -e "${BLUE}[2] TECHNICAL INDICATORS WORKER${NC}"
    echo "--------------------------------------------------------------------------------"
    TECH_PID=$(ps aux | grep "python3.*technical_indicators_worker.py" | grep -v grep | grep -v "/bin/bash" | awk '{print $2}')
    if [ -n "$TECH_PID" ]; then
        TECH_CPU=$(ps -p $TECH_PID -o %cpu --no-headers 2>/dev/null | xargs)
        TECH_MEM=$(ps -p $TECH_PID -o %mem --no-headers 2>/dev/null | xargs)
        echo -e "Status: ${GREEN}RUNNING${NC} (PID: $TECH_PID)"
        echo "CPU: ${TECH_CPU}% | Memory: ${TECH_MEM}%"

        if [ -f /tmp/technical_indicators_worker.log ]; then
            # Count completed partitions (exclude FutureWarning lines)
            TECH_COMPLETED=$(grep "✓" /tmp/technical_indicators_worker.log 2>/dev/null | grep -v "FutureWarning" | wc -l)
            TECH_PROGRESS=$(echo "$TECH_COMPLETED" | awk '{printf "%.1f", $1 * 100 / 336}')
            TECH_LAST=$(tail -20 /tmp/technical_indicators_worker.log | grep "✓" | grep -v "FutureWarning" | tail -1)
            echo "Progress: ${TECH_COMPLETED}/336 partitions (${TECH_PROGRESS}%)"
            echo "Latest: $TECH_LAST"
        fi
    else
        echo -e "Status: ${RED}NOT RUNNING${NC}"
    fi
    echo ""

    # Worker 3: Correlation Features
    echo -e "${BLUE}[3] CORRELATION FEATURES WORKER${NC}"
    echo "--------------------------------------------------------------------------------"
    CORR_PID=$(ps aux | grep "python3.*correlation_features_worker.py" | grep -v grep | grep -v "/bin/bash" | awk '{print $2}')
    if [ -n "$CORR_PID" ]; then
        CORR_CPU=$(ps -p $CORR_PID -o %cpu --no-headers 2>/dev/null | xargs)
        CORR_MEM=$(ps -p $CORR_PID -o %mem --no-headers 2>/dev/null | xargs)
        echo -e "Status: ${GREEN}RUNNING${NC} (PID: $CORR_PID)"
        echo "CPU: ${CORR_CPU}% | Memory: ${CORR_MEM}%"

        if [ -f /tmp/correlation_features_worker.log ]; then
            CORR_COMPLETED=$(grep -c "✓" /tmp/correlation_features_worker.log 2>/dev/null || echo "0")
            CORR_PROGRESS=$(echo "$CORR_COMPLETED" | awk '{printf "%.1f", $1 * 100 / 336}')
            CORR_LAST=$(tail -10 /tmp/correlation_features_worker.log | grep "✓" | tail -1)
            echo "Progress: ${CORR_COMPLETED}/336 partitions (${CORR_PROGRESS}%)"
            echo "Latest: $CORR_LAST"
        fi
    else
        echo -e "Status: ${YELLOW}NOT STARTED${NC}"
    fi
    echo ""

    # Overall System Stats
    echo -e "${BLUE}[SYSTEM RESOURCES]${NC}"
    echo "--------------------------------------------------------------------------------"
    CPU_TOTAL=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    MEM_TOTAL=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    echo "Total CPU Usage: ${CPU_TOTAL}%"
    echo "Total Memory Usage: ${MEM_TOTAL}%"
    echo ""

    # Database Connection Check
    echo -e "${BLUE}[DATABASE STATUS]${NC}"
    echo "--------------------------------------------------------------------------------"
    DB_CONN=$(PGPASSWORD='BQX_Aurora_2025_Secure' psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com -U postgres -d bqx -t -A -c "SELECT COUNT(*) FROM pg_stat_activity WHERE datname = 'bqx' AND state = 'active';" 2>/dev/null)
    if [ -n "$DB_CONN" ]; then
        echo -e "Active DB Connections: ${GREEN}${DB_CONN}${NC}"
    else
        echo -e "Active DB Connections: ${RED}ERROR${NC}"
    fi
    echo ""

    # Feature Completion Stats
    echo -e "${BLUE}[FEATURE COMPLETION]${NC}"
    echo "--------------------------------------------------------------------------------"

    # Count Fibonacci partitions with data
    FIB_COUNT=$(PGPASSWORD='BQX_Aurora_2025_Secure' psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com -U postgres -d bqx -t -A -c "SELECT COUNT(*) FROM pg_stat_user_tables WHERE schemaname = 'bqx' AND relname LIKE 'fibonacci_features_%' AND relname ~ '_[0-9]{4}_[0-9]{2}' AND n_live_tup > 0;" 2>/dev/null)
    FIB_ROWS=$(PGPASSWORD='BQX_Aurora_2025_Secure' psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com -U postgres -d bqx -t -A -c "SELECT COALESCE(SUM(n_live_tup), 0) FROM pg_stat_user_tables WHERE schemaname = 'bqx' AND relname LIKE 'fibonacci_features_%' AND relname ~ '_[0-9]{4}_[0-9]{2}';" 2>/dev/null)
    echo "Fibonacci: ${FIB_COUNT:-0}/336 partitions | ${FIB_ROWS:-0} rows"

    # Count Technical Indicators partitions with data
    TECH_COUNT=$(PGPASSWORD='BQX_Aurora_2025_Secure' psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com -U postgres -d bqx -t -A -c "SELECT COUNT(*) FROM pg_stat_user_tables WHERE schemaname = 'bqx' AND relname LIKE 'technical_features_%' AND relname ~ '_[0-9]{4}_[0-9]{2}' AND n_live_tup > 0;" 2>/dev/null)
    TECH_ROWS=$(PGPASSWORD='BQX_Aurora_2025_Secure' psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com -U postgres -d bqx -t -A -c "SELECT COALESCE(SUM(n_live_tup), 0) FROM pg_stat_user_tables WHERE schemaname = 'bqx' AND relname LIKE 'technical_features_%' AND relname ~ '_[0-9]{4}_[0-9]{2}';" 2>/dev/null)
    echo "Technical: ${TECH_COUNT:-0}/336 partitions | ${TECH_ROWS:-0} rows"

    # Count Correlation partitions with data
    CORR_COUNT=$(PGPASSWORD='BQX_Aurora_2025_Secure' psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com -U postgres -d bqx -t -A -c "SELECT COUNT(*) FROM pg_stat_user_tables WHERE schemaname = 'bqx' AND relname LIKE 'correlation_features_%' AND relname ~ '_[0-9]{4}_[0-9]{2}' AND n_live_tup > 0;" 2>/dev/null)
    CORR_ROWS=$(PGPASSWORD='BQX_Aurora_2025_Secure' psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com -U postgres -d bqx -t -A -c "SELECT COALESCE(SUM(n_live_tup), 0) FROM pg_stat_user_tables WHERE schemaname = 'bqx' AND relname LIKE 'correlation_features_%' AND relname ~ '_[0-9]{4}_[0-9]{2}';" 2>/dev/null)
    echo "Correlation: ${CORR_COUNT:-0}/336 partitions | ${CORR_ROWS:-0} rows"

    echo ""
    echo "================================================================================"
    echo "Press Ctrl+C to exit | Refreshing every 10 seconds..."
    echo "================================================================================"

    sleep 10
done
