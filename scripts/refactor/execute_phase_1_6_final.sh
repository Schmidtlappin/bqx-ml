#!/usr/bin/env bash
#
# Execute Phase 1.6 Final Stages: 1.6.19-1.6.21
#
# Stage 1.6.19: Realized Volatility Family - 30 features (2 operations)
# Stage 1.6.20: HMM Regime Detection - 30 features (2 operations)
# Stage 1.6.21: Cross-Sectional Panel - 46 features (1 operation)
#
# Total: 106 features, 2,040 tables, 5 parallel operations
# Expected Duration: ~30 seconds
#
# Author: BQX ML Team
# Date: 2025-11-13

set -euo pipefail

# Database connection
export PGPASSWORD='BQX_Aurora_2025_Secure'
PGHOST='trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com'
PGUSER='postgres'
PGDATABASE='bqx'

# Script directory
SCRIPT_DIR="/home/ubuntu/bqx-ml/scripts/refactor"

# Logging
LOG_DIR="/tmp/phase_1_6_final_logs"
mkdir -p "$LOG_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "================================================================================"
echo "EXECUTING PHASE 1.6 FINAL STAGES: 1.6.19-1.6.21"
echo "================================================================================"
echo ""
echo "Features: 106 total (30 + 30 + 46)"
echo "Tables: 2,040 total"
echo "Operations: 5 parallel (2 per stage for 1.6.19-1.6.20, 1 for 1.6.21)"
echo ""
echo "STAGE 1.6.19: Realized Volatility Family (30 features, 1,008 tables)"
echo "  [1/5] realized_volatility_rate: 336 partitions"
echo "  [2/5] realized_volatility_bqx: 672 partitions"
echo ""
echo "STAGE 1.6.20: HMM Regime Detection (30 features, 1,008 tables)"
echo "  [3/5] hmm_regime_rate: 336 partitions"
echo "  [4/5] hmm_regime_bqx: 672 partitions"
echo ""
echo "STAGE 1.6.21: Cross-Sectional Panel (46 features, 24 partitions)"
echo "  [5/5] cross_sectional_panel: 24 partitions (single panel)"
echo ""
echo "Architecture: Aurora PostgreSQL"
echo "Host: $PGHOST"
echo ""
echo "================================================================================"
echo ""

# Start time
start_time=$(date +%s)

# ============================================================================
# Launch all 5 operations in parallel
# ============================================================================

echo -e "${BLUE}[1/5] Launching realized_volatility_rate...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_6_19_create_realized_volatility_rate.sql" \
    > "$LOG_DIR/realized_volatility_rate.log" 2>&1 &
PID_VOL_RATE=$!
echo "  ↳ PID: $PID_VOL_RATE | Features: 15 | Partitions: 336"

echo -e "${BLUE}[2/5] Launching realized_volatility_bqx...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_6_19_create_realized_volatility_bqx.sql" \
    > "$LOG_DIR/realized_volatility_bqx.log" 2>&1 &
PID_VOL_BQX=$!
echo "  ↳ PID: $PID_VOL_BQX | Features: 15 | Partitions: 672"

echo -e "${BLUE}[3/5] Launching hmm_regime_rate...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_6_20_create_hmm_regime_rate.sql" \
    > "$LOG_DIR/hmm_regime_rate.log" 2>&1 &
PID_HMM_RATE=$!
echo "  ↳ PID: $PID_HMM_RATE | Features: 15 | Partitions: 336"

echo -e "${BLUE}[4/5] Launching hmm_regime_bqx...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_6_20_create_hmm_regime_bqx.sql" \
    > "$LOG_DIR/hmm_regime_bqx.log" 2>&1 &
PID_HMM_BQX=$!
echo "  ↳ PID: $PID_HMM_BQX | Features: 15 | Partitions: 672"

echo -e "${BLUE}[5/5] Launching cross_sectional_panel...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_6_21_create_cross_sectional_panel.sql" \
    > "$LOG_DIR/cross_sectional_panel.log" 2>&1 &
PID_PANEL=$!
echo "  ↳ PID: $PID_PANEL | Features: 46 | Partitions: 24"

echo ""
echo "================================================================================"
echo "ALL 5 OPERATIONS LAUNCHED - WAITING FOR COMPLETION..."
echo "================================================================================"
echo ""

# Wait for all operations
wait $PID_VOL_RATE
STATUS_VOL_RATE=$?

wait $PID_VOL_BQX
STATUS_VOL_BQX=$?

wait $PID_HMM_RATE
STATUS_HMM_RATE=$?

wait $PID_HMM_BQX
STATUS_HMM_BQX=$?

wait $PID_PANEL
STATUS_PANEL=$?

# Calculate execution time
total_time=$(($(date +%s) - start_time))

echo ""
echo "================================================================================"
echo "EXECUTION RESULTS - PHASE 1.6 FINAL STAGES"
echo "================================================================================"
echo ""
echo "Total Execution Time: ${total_time} seconds"
echo ""

# Display results for each operation
echo "STAGE 1.6.19: Realized Volatility Family"
echo "-----------------------------------------------------------"
if [ $STATUS_VOL_RATE -eq 0 ]; then
    echo -e "${GREEN}✅ [1/5] realized_volatility_rate: SUCCESS${NC}"
    tail -2 "$LOG_DIR/realized_volatility_rate.log" | grep -E "(✅|Created)"
else
    echo -e "${RED}❌ [1/5] realized_volatility_rate: FAILED (exit: $STATUS_VOL_RATE)${NC}"
    tail -10 "$LOG_DIR/realized_volatility_rate.log"
fi

if [ $STATUS_VOL_BQX -eq 0 ]; then
    echo -e "${GREEN}✅ [2/5] realized_volatility_bqx: SUCCESS${NC}"
    tail -2 "$LOG_DIR/realized_volatility_bqx.log" | grep -E "(✅|Created)"
else
    echo -e "${RED}❌ [2/5] realized_volatility_bqx: FAILED (exit: $STATUS_VOL_BQX)${NC}"
    tail -10 "$LOG_DIR/realized_volatility_bqx.log"
fi
echo ""

echo "STAGE 1.6.20: HMM Regime Detection"
echo "-----------------------------------------------------------"
if [ $STATUS_HMM_RATE -eq 0 ]; then
    echo -e "${GREEN}✅ [3/5] hmm_regime_rate: SUCCESS${NC}"
    tail -2 "$LOG_DIR/hmm_regime_rate.log" | grep -E "(✅|Created)"
else
    echo -e "${RED}❌ [3/5] hmm_regime_rate: FAILED (exit: $STATUS_HMM_RATE)${NC}"
    tail -10 "$LOG_DIR/hmm_regime_rate.log"
fi

if [ $STATUS_HMM_BQX -eq 0 ]; then
    echo -e "${GREEN}✅ [4/5] hmm_regime_bqx: SUCCESS${NC}"
    tail -2 "$LOG_DIR/hmm_regime_bqx.log" | grep -E "(✅|Created)"
else
    echo -e "${RED}❌ [4/5] hmm_regime_bqx: FAILED (exit: $STATUS_HMM_BQX)${NC}"
    tail -10 "$LOG_DIR/hmm_regime_bqx.log"
fi
echo ""

echo "STAGE 1.6.21: Cross-Sectional Panel"
echo "-----------------------------------------------------------"
if [ $STATUS_PANEL -eq 0 ]; then
    echo -e "${GREEN}✅ [5/5] cross_sectional_panel: SUCCESS${NC}"
    tail -2 "$LOG_DIR/cross_sectional_panel.log" | grep -E "(✅|Created)"
else
    echo -e "${RED}❌ [5/5] cross_sectional_panel: FAILED (exit: $STATUS_PANEL)${NC}"
    tail -10 "$LOG_DIR/cross_sectional_panel.log"
fi

echo ""
echo "================================================================================"
echo "PHASE 1.6 FINAL STAGES SUMMARY"
echo "================================================================================"
echo ""

# Count failures
FAILURES=0
[ $STATUS_VOL_RATE -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_VOL_BQX -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_HMM_RATE -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_HMM_BQX -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_PANEL -ne 0 ] && FAILURES=$((FAILURES + 1))

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ PHASE 1.6 FINAL STAGES COMPLETE - ALL 5 OPERATIONS SUCCESSFUL!${NC}"
    echo ""
    echo "Features Added: 106 (30 + 30 + 46)"
    echo "  • Stage 1.6.19 (Realized Volatility): 30 features (15 rate + 15 bqx)"
    echo "  • Stage 1.6.20 (HMM Regime): 30 features (15 rate + 15 bqx)"
    echo "  • Stage 1.6.21 (Panel): 46 features (single panel)"
    echo ""
    echo "Tables Created: 2,040"
    echo "  • realized_volatility: 1,008 (336 rate + 672 bqx)"
    echo "  • hmm_regime: 1,008 (336 rate + 672 bqx)"
    echo "  • cross_sectional_panel: 24 (single panel structure)"
    echo ""
    echo "Feature Progress:"
    echo "  • Before (after 1.6.18): 628/1,080 (58.1%)"
    echo "  • After (Phase 1.6 COMPLETE): 734/1,080 (68.0%)"
    echo "  • Added: +106 features (+9.8 percentage points)"
    echo ""
    echo "✅ PHASE 1.6 100% COMPLETE - 13/13 STAGES DONE"
    echo ""
    echo "Next Steps:"
    echo "  1. Update AirTable: Mark stages 1.6.19-1.6.21 as 'Done'"
    echo "  2. Commit Phase 1.6 completion to git"
    echo "  3. Proceed to Phase 1.7 (Database Expansion) or Phase 1.8 (Spectral/Advanced)"
    echo ""
    exit 0
else
    echo -e "${RED}❌ EXECUTION FAILED: $FAILURES/5 operations failed${NC}"
    echo ""
    echo "Review logs in: $LOG_DIR/"
    echo ""
    exit 1
fi
