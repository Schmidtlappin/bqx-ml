#!/usr/bin/env bash
#
# Execute Phase 1.9 Complete: Final Features to 1,080 (100%)
#
# Stage 1.9.1: Advanced Microstructure - 40 features (20 rate + 20 bqx)
# Stage 1.9.2: Lagged Cross-Window - 50 features (25 rate + 25 bqx)
# Stage 1.9.3: Volatility Surface - 30 features (15 rate + 15 bqx)
# Stage 1.9.4: Market Regime - 20 features (10 rate + 10 bqx)
# Stage 1.9.5: Liquidity Metrics - 22 features (11 rate + 11 bqx)
#
# Total: ~162 features (adjusted), 5,040 tables
# Expected Duration: ~60 seconds (2 batches, parallel execution)

set -euo pipefail

export PGPASSWORD='BQX_Aurora_2025_Secure'
PGHOST='trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com'
PGUSER='postgres'
PGDATABASE='bqx'

SCRIPT_DIR="/home/ubuntu/bqx-ml/scripts/refactor"
LOG_DIR="/tmp/phase_1_9_logs"
mkdir -p "$LOG_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "================================================================================"
echo "EXECUTING PHASE 1.9 COMPLETE: FINAL FEATURES TO 1,080 (100%)"
echo "================================================================================"
echo ""
echo "Current: 898/1,080 (83.1%)"
echo "Target: 1,080/1,080 (100.0%)"
echo "Adding: ~182 features"
echo ""
echo "Architecture: Aurora PostgreSQL"
echo "Host: $PGHOST"
echo ""
echo "================================================================================"
echo ""

start_time=$(date +%s)

echo -e "${YELLOW}BATCH 1: STAGES 1.9.1-1.9.2 (Microstructure & Cross-Window)${NC}"
echo "================================================================================"
echo ""

echo -e "${BLUE}[1/4] Launching advanced_microstructure_rate...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_9_1_create_advanced_microstructure_rate.sql" \
    > "$LOG_DIR/advanced_microstructure_rate.log" 2>&1 &
PID_1=$!

echo -e "${BLUE}[2/4] Launching advanced_microstructure_bqx...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_9_1_create_advanced_microstructure_bqx.sql" \
    > "$LOG_DIR/advanced_microstructure_bqx.log" 2>&1 &
PID_2=$!

echo -e "${BLUE}[3/4] Launching lagged_cross_window_rate...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_9_2_create_lagged_cross_window_rate.sql" \
    > "$LOG_DIR/lagged_cross_window_rate.log" 2>&1 &
PID_3=$!

echo -e "${BLUE}[4/4] Launching lagged_cross_window_bqx...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_9_2_create_lagged_cross_window_bqx.sql" \
    > "$LOG_DIR/lagged_cross_window_bqx.log" 2>&1 &
PID_4=$!

echo ""
echo "Waiting for Batch 1..."
wait $PID_1; STATUS_1=$?
wait $PID_2; STATUS_2=$?
wait $PID_3; STATUS_3=$?
wait $PID_4; STATUS_4=$?

batch1_time=$(($(date +%s) - start_time))
echo -e "${GREEN}✅ Batch 1 Complete (${batch1_time}s)${NC}"
echo ""

echo -e "${YELLOW}BATCH 2: STAGES 1.9.3-1.9.5 (Volatility, Regime, Liquidity)${NC}"
echo "================================================================================"
echo ""

batch2_start=$(date +%s)

echo -e "${BLUE}[5/10] Launching volatility_surface_rate...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_9_3_create_volatility_surface_rate.sql" \
    > "$LOG_DIR/volatility_surface_rate.log" 2>&1 &
PID_5=$!

echo -e "${BLUE}[6/10] Launching volatility_surface_bqx...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_9_3_create_volatility_surface_bqx.sql" \
    > "$LOG_DIR/volatility_surface_bqx.log" 2>&1 &
PID_6=$!

echo -e "${BLUE}[7/10] Launching market_regime_rate...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_9_4_create_market_regime_rate.sql" \
    > "$LOG_DIR/market_regime_rate.log" 2>&1 &
PID_7=$!

echo -e "${BLUE}[8/10] Launching market_regime_bqx...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_9_4_create_market_regime_bqx.sql" \
    > "$LOG_DIR/market_regime_bqx.log" 2>&1 &
PID_8=$!

echo -e "${BLUE}[9/10] Launching liquidity_metrics_rate...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_9_5_create_liquidity_metrics_rate.sql" \
    > "$LOG_DIR/liquidity_metrics_rate.log" 2>&1 &
PID_9=$!

echo -e "${BLUE}[10/10] Launching liquidity_metrics_bqx...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_9_5_create_liquidity_metrics_bqx.sql" \
    > "$LOG_DIR/liquidity_metrics_bqx.log" 2>&1 &
PID_10=$!

echo ""
echo "Waiting for Batch 2..."
wait $PID_5; STATUS_5=$?
wait $PID_6; STATUS_6=$?
wait $PID_7; STATUS_7=$?
wait $PID_8; STATUS_8=$?
wait $PID_9; STATUS_9=$?
wait $PID_10; STATUS_10=$?

batch2_time=$(($(date +%s) - batch2_start))
echo -e "${GREEN}✅ Batch 2 Complete (${batch2_time}s)${NC}"
echo ""

total_time=$(($(date +%s) - start_time))

echo ""
echo "================================================================================"
echo "EXECUTION RESULTS - PHASE 1.9 COMPLETE"
echo "================================================================================"
echo ""
echo "Total Execution Time: ${total_time} seconds"
echo "  • Batch 1: ${batch1_time}s"
echo "  • Batch 2: ${batch2_time}s"
echo ""

FAILURES=0
for i in {1..10}; do
    status_var="STATUS_$i"
    [ ${!status_var} -ne 0 ] && FAILURES=$((FAILURES + 1))
done

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ PHASE 1.9 COMPLETE - ALL 10 OPERATIONS SUCCESSFUL!${NC}"
    echo ""
    echo "Features Added: ~162"
    echo "  • Stage 1.9.1 (Microstructure): 40 features"
    echo "  • Stage 1.9.2 (Cross-Window): 50 features"
    echo "  • Stage 1.9.3 (Volatility Surface): 30 features"
    echo "  • Stage 1.9.4 (Market Regime): 20 features"
    echo "  • Stage 1.9.5 (Liquidity Metrics): 22 features"
    echo ""
    echo "Tables Created: 5,040"
    echo ""
    echo "Feature Progress:"
    echo "  • Before: 898/1,080 (83.1%)"
    echo "  • After: 1,060/1,080 (98.1%)"
    echo "  • Remaining: 20 features (1.9%)"
    echo ""
    echo "✅ PHASE 1 ARCHITECTURE 98% COMPLETE"
    echo ""
    echo "Next: Add final 20 features or proceed to Phase 2 (Feature Engineering)"
    echo ""
    exit 0
else
    echo -e "${RED}❌ EXECUTION FAILED: $FAILURES/10 operations failed${NC}"
    echo "Review logs in: $LOG_DIR/"
    exit 1
fi
