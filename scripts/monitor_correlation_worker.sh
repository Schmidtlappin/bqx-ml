#!/bin/bash
#
# Real-time Monitor for Correlation Features Worker
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
    echo "BQX ML - CORRELATION FEATURES WORKER MONITOR"
    echo "================================================================================"
    echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # Worker Status
    echo -e "${BLUE}[CORRELATION FEATURES WORKER]${NC}"
    echo "--------------------------------------------------------------------------------"
    CORR_PID=$(ps aux | grep "python3.*correlation_features_worker" | grep -v grep | awk '{print $2}')
    if [ -n "$CORR_PID" ]; then
        CORR_CPU=$(ps -p $CORR_PID -o %cpu --no-headers 2>/dev/null | xargs)
        CORR_MEM=$(ps -p $CORR_PID -o %mem --no-headers 2>/dev/null | xargs)
        CORR_TIME=$(ps -p $CORR_PID -o etime --no-headers 2>/dev/null | xargs)
        echo -e "Status: ${GREEN}RUNNING${NC} (PID: $CORR_PID)"
        echo "CPU: ${CORR_CPU}% | Memory: ${CORR_MEM}% | Runtime: ${CORR_TIME}"
    else
        echo -e "Status: ${RED}NOT RUNNING${NC}"
    fi
    echo ""

    # Database Progress
    echo -e "${BLUE}[DATABASE PROGRESS]${NC}"
    echo "--------------------------------------------------------------------------------"

    # Query populated partitions (all 28 pairs)
    # Total expected: 28 pairs × 12 months = 336 partitions
    CORR_COUNT=$(PGPASSWORD='BQX_Aurora_2025_Secure' psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com -U postgres -d bqx -t -A -c "SELECT COUNT(*) FROM pg_stat_user_tables WHERE schemaname = 'bqx' AND relname LIKE 'correlation_features_%' AND relname ~ '_[0-9]{4}_[0-9]{2}' AND n_live_tup > 0;" 2>/dev/null)
    CORR_ROWS=$(PGPASSWORD='BQX_Aurora_2025_Secure' psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com -U postgres -d bqx -t -A -c "SELECT COALESCE(SUM(n_live_tup), 0) FROM pg_stat_user_tables WHERE schemaname = 'bqx' AND relname LIKE 'correlation_features_%' AND relname ~ '_[0-9]{4}_[0-9]{2}';" 2>/dev/null)

    CORR_PROGRESS=$(echo "$CORR_COUNT" | awk '{printf "%.1f", $1 * 100 / 336}')

    echo "Populated Partitions: ${CORR_COUNT:-0}/336 (${CORR_PROGRESS}%)"
    echo "Total Rows: ${CORR_ROWS:-0}"
    echo ""

    # Pairs Progress (show which correlation groups are complete)
    echo -e "${BLUE}[PAIRS PROGRESS]${NC}"
    echo "--------------------------------------------------------------------------------"

    # EUR pairs
    EUR_PAIRS=$(PGPASSWORD='BQX_Aurora_2025_Secure' psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com -U postgres -d bqx -t -A -c "SELECT COUNT(DISTINCT SUBSTRING(relname FROM 'correlation_features_(.*)_[0-9]{4}')) FROM pg_stat_user_tables WHERE schemaname = 'bqx' AND relname ~ 'correlation_features_(euraud|eurcad|eurgbp|eurjpy|eurusd)_[0-9]{4}_[0-9]{2}' AND n_live_tup > 0;" 2>/dev/null)
    echo "EUR pairs: ${EUR_PAIRS:-0}/5 (euraud, eurcad, eurgbp, eurjpy, eurusd)"

    # GBP pairs
    GBP_PAIRS=$(PGPASSWORD='BQX_Aurora_2025_Secure' psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com -U postgres -d bqx -t -A -c "SELECT COUNT(DISTINCT SUBSTRING(relname FROM 'correlation_features_(.*)_[0-9]{4}')) FROM pg_stat_user_tables WHERE schemaname = 'bqx' AND relname ~ 'correlation_features_(gbpaud|gbpcad|gbpchf|gbpjpy|gbpusd)_[0-9]{4}_[0-9]{2}' AND n_live_tup > 0;" 2>/dev/null)
    echo "GBP pairs: ${GBP_PAIRS:-0}/5 (gbpaud, gbpcad, gbpchf, gbpjpy, gbpusd)"

    # USD pairs
    USD_PAIRS=$(PGPASSWORD='BQX_Aurora_2025_Secure' psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com -U postgres -d bqx -t -A -c "SELECT COUNT(DISTINCT SUBSTRING(relname FROM 'correlation_features_(.*)_[0-9]{4}')) FROM pg_stat_user_tables WHERE schemaname = 'bqx' AND relname ~ 'correlation_features_(usdcad|usdchf|usdjpy|audusd)_[0-9]{4}_[0-9]{2}' AND n_live_tup > 0;" 2>/dev/null)
    echo "USD pairs: ${USD_PAIRS:-0}/4 (usdcad, usdchf, usdjpy, audusd)"
    echo ""

    # Recent completions
    echo -e "${BLUE}[RECENT ACTIVITY]${NC}"
    echo "--------------------------------------------------------------------------------"
    RECENT_TABLES=$(PGPASSWORD='BQX_Aurora_2025_Secure' psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com -U postgres -d bqx -t -A -c "SELECT relname, n_live_tup FROM pg_stat_user_tables WHERE schemaname = 'bqx' AND relname LIKE 'correlation_features_%' AND relname ~ '_[0-9]{4}_[0-9]{2}' AND n_live_tup > 0 ORDER BY relname DESC LIMIT 5;" 2>/dev/null | awk -F'|' '{printf "  %-40s %10s rows\n", $1, $2}')
    if [ -n "$RECENT_TABLES" ]; then
        echo "$RECENT_TABLES"
    else
        echo "  No data yet..."
    fi
    echo ""

    # System Resources
    echo -e "${BLUE}[SYSTEM RESOURCES]${NC}"
    echo "--------------------------------------------------------------------------------"
    CPU_TOTAL=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    MEM_TOTAL=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    echo "Total CPU Usage: ${CPU_TOTAL}%"
    echo "Total Memory Usage: ${MEM_TOTAL}%"
    echo ""

    # Database Connections
    echo -e "${BLUE}[DATABASE STATUS]${NC}"
    echo "--------------------------------------------------------------------------------"
    DB_CONN=$(PGPASSWORD='BQX_Aurora_2025_Secure' psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com -U postgres -d bqx -t -A -c "SELECT COUNT(*) FROM pg_stat_activity WHERE datname = 'bqx' AND state = 'active';" 2>/dev/null)
    if [ -n "$DB_CONN" ]; then
        echo -e "Active DB Connections: ${GREEN}${DB_CONN}${NC}"
    else
        echo -e "Active DB Connections: ${RED}ERROR${NC}"
    fi
    echo ""

    echo "================================================================================"
    echo "Expected: 336 partitions (28 pairs × 12 months)"
    echo "Features: 15 correlation-based features per partition"
    echo "Estimated Time: ~6 hours (65 seconds per partition)"
    echo "Press Ctrl+C to exit | Refreshing every 10 seconds..."
    echo "================================================================================"

    sleep 10
done
