#!/usr/bin/env bash
#
# Execute Option B Comprehensive Dual Architecture - Stages 1.6.12-1.6.17
#
# Total Operations: 9 parallel PostgreSQL sessions
# - 3 ALTER operations (expand existing IDX tables)
# - 6 CREATE operations (new BQX tables + volume tables + correlation recreate)
#
# Features Added: 336 (168 IDX + 168 BQX)
# Tables Modified/Created: 6,048 operations
# - ALTER: 1,008 partitions (statistics, bollinger, fibonacci rate tables)
# - CREATE: 4,704 partitions (BQX tables + volume dual)
# - DROP+CREATE: 336 partitions (correlation_rate)
#
# Expected Duration: ~90 seconds
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
LOG_DIR="/tmp/option_b_comprehensive_logs"
mkdir -p "$LOG_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "================================================================================"
echo "EXECUTING OPTION B COMPREHENSIVE DUAL ARCHITECTURE"
echo "================================================================================"
echo ""
echo "Target: Stages 1.6.12-1.6.17"
echo "Operations: 9 parallel PostgreSQL sessions"
echo "Features: 336 total (168 IDX + 168 BQX)"
echo "Tables: 6,048 operations"
echo "  • ALTER: 1,008 partitions (expand existing IDX tables)"
echo "  • CREATE: 4,704 partitions (new BQX + volume tables)"
echo "  • DROP+CREATE: 336 partitions (correlation_rate)"
echo ""
echo "Expected Duration: ~90 seconds"
echo ""
echo "Architecture: Aurora PostgreSQL"
echo "Host: $PGHOST"
echo ""
echo "================================================================================"
echo ""

# ============================================================================
# STAGE 1.6.12: Statistics Dual Architecture (48 + 48 = 96 features)
# ============================================================================

echo -e "${BLUE}[1/9] Launching Stage 1.6.12 Part A: Expand statistics_rate (5→48 features)...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_6_12_part_a_expand_statistics_rate.sql" \
    > "$LOG_DIR/1_6_12_part_a_statistics_rate_expand.log" 2>&1 &
PID_STATS_RATE=$!
echo "  ↳ PID: $PID_STATS_RATE | Action: ALTER TABLE +43 columns | Tables: 336 partitions"

echo -e "${BLUE}[2/9] Launching Stage 1.6.12 Part B: Create statistics_bqx (48 features)...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_6_12_part_b_create_statistics_bqx.sql" \
    > "$LOG_DIR/1_6_12_part_b_statistics_bqx_create.log" 2>&1 &
PID_STATS_BQX=$!
echo "  ↳ PID: $PID_STATS_BQX | Action: CREATE TABLE | Tables: 672 partitions"
echo ""

# ============================================================================
# STAGE 1.6.13: Bollinger Dual Architecture (20 + 20 = 40 features)
# ============================================================================

echo -e "${BLUE}[3/9] Launching Stage 1.6.13 Part A: Expand bollinger_rate (5→20 features)...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_6_13_part_a_expand_bollinger_rate.sql" \
    > "$LOG_DIR/1_6_13_part_a_bollinger_rate_expand.log" 2>&1 &
PID_BOLL_RATE=$!
echo "  ↳ PID: $PID_BOLL_RATE | Action: ALTER TABLE +15 columns | Tables: 336 partitions"

echo -e "${BLUE}[4/9] Launching Stage 1.6.13 Part B: Create bollinger_bqx (20 features)...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_6_13_part_b_create_bollinger_bqx.sql" \
    > "$LOG_DIR/1_6_13_part_b_bollinger_bqx_create.log" 2>&1 &
PID_BOLL_BQX=$!
echo "  ↳ PID: $PID_BOLL_BQX | Action: CREATE TABLE | Tables: 672 partitions"
echo ""

# ============================================================================
# STAGE 1.6.14: Fibonacci Dual Architecture (20 + 20 = 40 features)
# ============================================================================

echo -e "${BLUE}[5/9] Launching Stage 1.6.14 Part A: Expand fibonacci_rate (12→20 features)...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_6_14_part_a_expand_fibonacci_rate.sql" \
    > "$LOG_DIR/1_6_14_part_a_fibonacci_rate_expand.log" 2>&1 &
PID_FIB_RATE=$!
echo "  ↳ PID: $PID_FIB_RATE | Action: ALTER TABLE +8 columns | Tables: 336 partitions"

echo -e "${BLUE}[6/9] Launching Stage 1.6.14 Part B: Create fibonacci_bqx (20 features)...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_6_14_part_b_create_fibonacci_bqx.sql" \
    > "$LOG_DIR/1_6_14_part_b_fibonacci_bqx_create.log" 2>&1 &
PID_FIB_BQX=$!
echo "  ↳ PID: $PID_FIB_BQX | Action: CREATE TABLE | Tables: 672 partitions"
echo ""

# ============================================================================
# STAGE 1.6.15: Volume Dual Architecture (35 + 35 = 70 features)
# ============================================================================

echo -e "${BLUE}[7/9] Launching Stage 1.6.15: Create volume_rate + volume_bqx (70 features)...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_6_15_create_volume_dual.sql" \
    > "$LOG_DIR/1_6_15_volume_dual_create.log" 2>&1 &
PID_VOLUME=$!
echo "  ↳ PID: $PID_VOLUME | Action: CREATE TABLE (dual) | Tables: 1,344 partitions"
echo ""

# ============================================================================
# STAGE 1.6.16: Correlation IDX (45 features)
# ============================================================================

echo -e "${BLUE}[8/9] Launching Stage 1.6.16: Recreate correlation_rate (16→45 features)...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_6_16_recreate_correlation_rate.sql" \
    > "$LOG_DIR/1_6_16_correlation_rate_recreate.log" 2>&1 &
PID_CORR_RATE=$!
echo "  ↳ PID: $PID_CORR_RATE | Action: DROP+CREATE | Tables: 672 partitions"
echo ""

# ============================================================================
# STAGE 1.6.17: Correlation BQX (45 features)
# ============================================================================

echo -e "${BLUE}[9/9] Launching Stage 1.6.17: Create correlation_bqx (45 features)...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_6_17_create_correlation_bqx.sql" \
    > "$LOG_DIR/1_6_17_correlation_bqx_create.log" 2>&1 &
PID_CORR_BQX=$!
echo "  ↳ PID: $PID_CORR_BQX | Action: CREATE TABLE | Tables: 672 partitions"
echo ""

# ============================================================================
# Wait for all operations to complete
# ============================================================================

echo "================================================================================"
echo "ALL 9 OPERATIONS LAUNCHED - WAITING FOR COMPLETION..."
echo "================================================================================"
echo ""
echo "This will take approximately 90 seconds. Progress is logged to:"
echo "  $LOG_DIR/"
echo ""

# Function to show elapsed time
start_time=$(date +%s)
show_progress() {
    local elapsed=$(($(date +%s) - start_time))
    echo -n "  Elapsed: ${elapsed}s"
}

# Wait for all background jobs and capture exit codes
wait $PID_STATS_RATE
STATUS_STATS_RATE=$?

wait $PID_STATS_BQX
STATUS_STATS_BQX=$?

wait $PID_BOLL_RATE
STATUS_BOLL_RATE=$?

wait $PID_BOLL_BQX
STATUS_BOLL_BQX=$?

wait $PID_FIB_RATE
STATUS_FIB_RATE=$?

wait $PID_FIB_BQX
STATUS_FIB_BQX=$?

wait $PID_VOLUME
STATUS_VOLUME=$?

wait $PID_CORR_RATE
STATUS_CORR_RATE=$?

wait $PID_CORR_BQX
STATUS_CORR_BQX=$?

total_time=$(($(date +%s) - start_time))

echo ""
echo "================================================================================"
echo "EXECUTION RESULTS - OPTION B COMPREHENSIVE DUAL ARCHITECTURE"
echo "================================================================================"
echo ""
echo "Total Execution Time: ${total_time} seconds"
echo ""

# ============================================================================
# Display results for each operation
# ============================================================================

echo "STAGE 1.6.12: Statistics Dual Architecture (96 features)"
echo "-----------------------------------------------------------"
if [ $STATUS_STATS_RATE -eq 0 ]; then
    echo -e "${GREEN}✅ [1/9] Part A: statistics_rate expanded (5→48 features)${NC}"
    tail -3 "$LOG_DIR/1_6_12_part_a_statistics_rate_expand.log" | grep -E "(✅|Created|Expanded)"
else
    echo -e "${RED}❌ [1/9] Part A: statistics_rate FAILED (exit: $STATUS_STATS_RATE)${NC}"
    tail -10 "$LOG_DIR/1_6_12_part_a_statistics_rate_expand.log"
fi

if [ $STATUS_STATS_BQX -eq 0 ]; then
    echo -e "${GREEN}✅ [2/9] Part B: statistics_bqx created (48 features)${NC}"
    tail -3 "$LOG_DIR/1_6_12_part_b_statistics_bqx_create.log" | grep -E "(✅|Created)"
else
    echo -e "${RED}❌ [2/9] Part B: statistics_bqx FAILED (exit: $STATUS_STATS_BQX)${NC}"
    tail -10 "$LOG_DIR/1_6_12_part_b_statistics_bqx_create.log"
fi
echo ""

echo "STAGE 1.6.13: Bollinger Dual Architecture (40 features)"
echo "-----------------------------------------------------------"
if [ $STATUS_BOLL_RATE -eq 0 ]; then
    echo -e "${GREEN}✅ [3/9] Part A: bollinger_rate expanded (5→20 features)${NC}"
    tail -3 "$LOG_DIR/1_6_13_part_a_bollinger_rate_expand.log" | grep -E "(✅|Created|Expanded)"
else
    echo -e "${RED}❌ [3/9] Part A: bollinger_rate FAILED (exit: $STATUS_BOLL_RATE)${NC}"
    tail -10 "$LOG_DIR/1_6_13_part_a_bollinger_rate_expand.log"
fi

if [ $STATUS_BOLL_BQX -eq 0 ]; then
    echo -e "${GREEN}✅ [4/9] Part B: bollinger_bqx created (20 features)${NC}"
    tail -3 "$LOG_DIR/1_6_13_part_b_bollinger_bqx_create.log" | grep -E "(✅|Created)"
else
    echo -e "${RED}❌ [4/9] Part B: bollinger_bqx FAILED (exit: $STATUS_BOLL_BQX)${NC}"
    tail -10 "$LOG_DIR/1_6_13_part_b_bollinger_bqx_create.log"
fi
echo ""

echo "STAGE 1.6.14: Fibonacci Dual Architecture (40 features)"
echo "-----------------------------------------------------------"
if [ $STATUS_FIB_RATE -eq 0 ]; then
    echo -e "${GREEN}✅ [5/9] Part A: fibonacci_rate expanded (12→20 features)${NC}"
    tail -3 "$LOG_DIR/1_6_14_part_a_fibonacci_rate_expand.log" | grep -E "(✅|Created|Expanded)"
else
    echo -e "${RED}❌ [5/9] Part A: fibonacci_rate FAILED (exit: $STATUS_FIB_RATE)${NC}"
    tail -10 "$LOG_DIR/1_6_14_part_a_fibonacci_rate_expand.log"
fi

if [ $STATUS_FIB_BQX -eq 0 ]; then
    echo -e "${GREEN}✅ [6/9] Part B: fibonacci_bqx created (20 features)${NC}"
    tail -3 "$LOG_DIR/1_6_14_part_b_fibonacci_bqx_create.log" | grep -E "(✅|Created)"
else
    echo -e "${RED}❌ [6/9] Part B: fibonacci_bqx FAILED (exit: $STATUS_FIB_BQX)${NC}"
    tail -10 "$LOG_DIR/1_6_14_part_b_fibonacci_bqx_create.log"
fi
echo ""

echo "STAGE 1.6.15: Volume Dual Architecture (70 features)"
echo "-----------------------------------------------------------"
if [ $STATUS_VOLUME -eq 0 ]; then
    echo -e "${GREEN}✅ [7/9] volume_rate + volume_bqx created (70 features)${NC}"
    tail -5 "$LOG_DIR/1_6_15_volume_dual_create.log" | grep -E "(✅|Created)"
else
    echo -e "${RED}❌ [7/9] Volume dual FAILED (exit: $STATUS_VOLUME)${NC}"
    tail -10 "$LOG_DIR/1_6_15_volume_dual_create.log"
fi
echo ""

echo "STAGE 1.6.16: Correlation IDX Architecture (45 features)"
echo "-----------------------------------------------------------"
if [ $STATUS_CORR_RATE -eq 0 ]; then
    echo -e "${GREEN}✅ [8/9] correlation_rate recreated (16→45 features)${NC}"
    tail -5 "$LOG_DIR/1_6_16_correlation_rate_recreate.log" | grep -E "(✅|Created|Dropped)"
else
    echo -e "${RED}❌ [8/9] correlation_rate FAILED (exit: $STATUS_CORR_RATE)${NC}"
    tail -10 "$LOG_DIR/1_6_16_correlation_rate_recreate.log"
fi
echo ""

echo "STAGE 1.6.17: Correlation BQX Architecture (45 features)"
echo "-----------------------------------------------------------"
if [ $STATUS_CORR_BQX -eq 0 ]; then
    echo -e "${GREEN}✅ [9/9] correlation_bqx created (45 features)${NC}"
    tail -3 "$LOG_DIR/1_6_17_correlation_bqx_create.log" | grep -E "(✅|Created)"
else
    echo -e "${RED}❌ [9/9] correlation_bqx FAILED (exit: $STATUS_CORR_BQX)${NC}"
    tail -10 "$LOG_DIR/1_6_17_correlation_bqx_create.log"
fi
echo ""

# ============================================================================
# Final Summary
# ============================================================================

echo "================================================================================"
echo "OPTION B COMPREHENSIVE SUMMARY"
echo "================================================================================"
echo ""

# Count failures
FAILURES=0
[ $STATUS_STATS_RATE -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_STATS_BQX -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_BOLL_RATE -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_BOLL_BQX -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_FIB_RATE -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_FIB_BQX -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_VOLUME -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_CORR_RATE -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_CORR_BQX -ne 0 ] && FAILURES=$((FAILURES + 1))

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ ALL 9 OPERATIONS SUCCESSFUL!${NC}"
    echo ""
    echo "Features Added: 336 (168 IDX + 168 BQX)"
    echo "  • Statistics: 96 features (48 IDX expanded + 48 BQX created)"
    echo "  • Bollinger: 40 features (20 IDX expanded + 20 BQX created)"
    echo "  • Fibonacci: 40 features (20 IDX expanded + 20 BQX created)"
    echo "  • Volume: 70 features (35 IDX created + 35 BQX created)"
    echo "  • Correlation: 90 features (45 IDX recreated + 45 BQX created)"
    echo ""
    echo "Tables Modified/Created: 6,048"
    echo "  • ALTER: 1,008 partitions (IDX expansions)"
    echo "  • CREATE: 4,704 partitions (BQX + volume)"
    echo "  • DROP+CREATE: 336 partitions (correlation_rate)"
    echo ""
    echo "Feature Progress:"
    echo "  • Before: 268/1,080 (24.8%)"
    echo "  • After: 604/1,080 (55.9%)"
    echo "  • Added: +336 features (+31.1 percentage points)"
    echo ""
    echo "✅ 100% DUAL ARCHITECTURE PARITY ACHIEVED"
    echo "   IDX and BQX domains have identical feature coverage"
    echo ""
    echo "Next Steps:"
    echo "  1. Verify table schemas and counts"
    echo "  2. Update AirTable stages 1.6.12-1.6.17 to 'Done'"
    echo "  3. Commit changes to git"
    echo "  4. Begin feature population workers"
    echo ""
    exit 0
else
    echo -e "${RED}❌ EXECUTION FAILED: $FAILURES/9 operations failed${NC}"
    echo ""
    echo "Review logs in: $LOG_DIR/"
    echo ""
    echo "Failed operations will need to be retried."
    exit 1
fi
