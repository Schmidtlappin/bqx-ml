#!/usr/bin/env bash
#
# Execute Phase 1.8 Complete: Advanced Spectral & Multi-Scale Features
#
# Stage 1.8.1: Parabolic Term Comparisons - 44 features (24 rate + 20 bqx)
# Stage 1.8.2: Multi-Scale Features (30m/60m) - 60 features (30 rate + 30 bqx)
# Stage 1.8.3: Spectral Features (FFT/Wavelet/SSA) - 60 features (30 rate + 30 bqx)
#
# Total: ~164 features, 6,048 tables
# Expected Duration: ~60 seconds (3 batches, parallel execution)
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
LOG_DIR="/tmp/phase_1_8_logs"
mkdir -p "$LOG_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "================================================================================"
echo "EXECUTING PHASE 1.8 COMPLETE: ADVANCED SPECTRAL & MULTI-SCALE FEATURES"
echo "================================================================================"
echo ""
echo "Features: ~164 total (44 + 60 + 60)"
echo "Tables: 6,048 total"
echo "Execution: 3 batches with parallel operations"
echo ""
echo "STAGE 1.8.1: Parabolic Term Comparisons (44 features, 1,008 tables)"
echo "  [1-2] parabolic_comparison: rate (336) + bqx (672)"
echo ""
echo "STAGE 1.8.2: Multi-Scale Features (60 features, 3,024 tables)"
echo "  [3-6] multi_scale 30m/60m: rate (672) + bqx (1,344) + rate (672) + bqx (1,344)"
echo ""
echo "STAGE 1.8.3: Spectral Features (60 features, 3,024 tables)"
echo "  [7-12] spectral/wavelet/ssa: rate (1,008) + bqx (2,016)"
echo ""
echo "Architecture: Aurora PostgreSQL"
echo "Host: $PGHOST"
echo ""
echo "================================================================================"
echo ""

# Start time
start_time=$(date +%s)

# ============================================================================
# BATCH 1: Stage 1.8.1 - Parabolic Term Comparisons (2 parallel operations)
# ============================================================================

echo -e "${YELLOW}BATCH 1: STAGE 1.8.1 - PARABOLIC TERM COMPARISONS${NC}"
echo "================================================================================"
echo ""

echo -e "${BLUE}[1/2] Launching parabolic_comparison_rate...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_8_1_create_parabolic_comparison_rate.sql" \
    > "$LOG_DIR/parabolic_comparison_rate.log" 2>&1 &
PID_PARA_RATE=$!
echo "  ↳ PID: $PID_PARA_RATE | Features: 24 | Partitions: 336"

echo -e "${BLUE}[2/2] Launching parabolic_comparison_bqx...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_8_1_create_parabolic_comparison_bqx.sql" \
    > "$LOG_DIR/parabolic_comparison_bqx.log" 2>&1 &
PID_PARA_BQX=$!
echo "  ↳ PID: $PID_PARA_BQX | Features: 20 | Partitions: 672"

echo ""
echo "Waiting for Batch 1 to complete..."
wait $PID_PARA_RATE
STATUS_PARA_RATE=$?
wait $PID_PARA_BQX
STATUS_PARA_BQX=$?

batch1_time=$(($(date +%s) - start_time))
echo -e "${GREEN}✅ Batch 1 Complete (${batch1_time}s)${NC}"
echo ""

# ============================================================================
# BATCH 2: Stage 1.8.2 - Multi-Scale Features (4 parallel operations)
# ============================================================================

echo -e "${YELLOW}BATCH 2: STAGE 1.8.2 - MULTI-SCALE FEATURES${NC}"
echo "================================================================================"
echo ""

batch2_start=$(date +%s)

echo -e "${BLUE}[3/4] Launching multi_scale_30m_rate...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_8_2_create_multi_scale_30m_rate.sql" \
    > "$LOG_DIR/multi_scale_30m_rate.log" 2>&1 &
PID_MS_30_RATE=$!
echo "  ↳ PID: $PID_MS_30_RATE | Features: 15 | Partitions: 336"

echo -e "${BLUE}[4/4] Launching multi_scale_60m_rate...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_8_2_create_multi_scale_60m_rate.sql" \
    > "$LOG_DIR/multi_scale_60m_rate.log" 2>&1 &
PID_MS_60_RATE=$!
echo "  ↳ PID: $PID_MS_60_RATE | Features: 15 | Partitions: 336"

echo -e "${BLUE}[5/6] Launching multi_scale_30m_bqx...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_8_2_create_multi_scale_30m_bqx.sql" \
    > "$LOG_DIR/multi_scale_30m_bqx.log" 2>&1 &
PID_MS_30_BQX=$!
echo "  ↳ PID: $PID_MS_30_BQX | Features: 15 | Partitions: 672"

echo -e "${BLUE}[6/6] Launching multi_scale_60m_bqx...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_8_2_create_multi_scale_60m_bqx.sql" \
    > "$LOG_DIR/multi_scale_60m_bqx.log" 2>&1 &
PID_MS_60_BQX=$!
echo "  ↳ PID: $PID_MS_60_BQX | Features: 15 | Partitions: 672"

echo ""
echo "Waiting for Batch 2 to complete..."
wait $PID_MS_30_RATE
STATUS_MS_30_RATE=$?
wait $PID_MS_60_RATE
STATUS_MS_60_RATE=$?
wait $PID_MS_30_BQX
STATUS_MS_30_BQX=$?
wait $PID_MS_60_BQX
STATUS_MS_60_BQX=$?

batch2_time=$(($(date +%s) - batch2_start))
echo -e "${GREEN}✅ Batch 2 Complete (${batch2_time}s)${NC}"
echo ""

# ============================================================================
# BATCH 3: Stage 1.8.3 - Spectral Features (6 parallel operations)
# ============================================================================

echo -e "${YELLOW}BATCH 3: STAGE 1.8.3 - SPECTRAL FEATURES${NC}"
echo "================================================================================"
echo ""

batch3_start=$(date +%s)

echo -e "${BLUE}[7/12] Launching spectral_features_rate...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_8_3_create_spectral_features_rate.sql" \
    > "$LOG_DIR/spectral_features_rate.log" 2>&1 &
PID_SPEC_RATE=$!
echo "  ↳ PID: $PID_SPEC_RATE | FFT Features: 12 | Partitions: 336"

echo -e "${BLUE}[8/12] Launching wavelet_features_rate...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_8_3_create_wavelet_features_rate.sql" \
    > "$LOG_DIR/wavelet_features_rate.log" 2>&1 &
PID_WAVE_RATE=$!
echo "  ↳ PID: $PID_WAVE_RATE | Wavelet Features: 10 | Partitions: 336"

echo -e "${BLUE}[9/12] Launching ssa_features_rate...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_8_3_create_ssa_features_rate.sql" \
    > "$LOG_DIR/ssa_features_rate.log" 2>&1 &
PID_SSA_RATE=$!
echo "  ↳ PID: $PID_SSA_RATE | SSA Features: 8 | Partitions: 336"

echo -e "${BLUE}[10/12] Launching spectral_features_bqx...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_8_3_create_spectral_features_bqx.sql" \
    > "$LOG_DIR/spectral_features_bqx.log" 2>&1 &
PID_SPEC_BQX=$!
echo "  ↳ PID: $PID_SPEC_BQX | FFT Features: 12 | Partitions: 672"

echo -e "${BLUE}[11/12] Launching wavelet_features_bqx...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_8_3_create_wavelet_features_bqx.sql" \
    > "$LOG_DIR/wavelet_features_bqx.log" 2>&1 &
PID_WAVE_BQX=$!
echo "  ↳ PID: $PID_WAVE_BQX | Wavelet Features: 10 | Partitions: 672"

echo -e "${BLUE}[12/12] Launching ssa_features_bqx...${NC}"
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
    -f "$SCRIPT_DIR/stage_1_8_3_create_ssa_features_bqx.sql" \
    > "$LOG_DIR/ssa_features_bqx.log" 2>&1 &
PID_SSA_BQX=$!
echo "  ↳ PID: $PID_SSA_BQX | SSA Features: 8 | Partitions: 672"

echo ""
echo "Waiting for Batch 3 to complete..."
wait $PID_SPEC_RATE
STATUS_SPEC_RATE=$?
wait $PID_WAVE_RATE
STATUS_WAVE_RATE=$?
wait $PID_SSA_RATE
STATUS_SSA_RATE=$?
wait $PID_SPEC_BQX
STATUS_SPEC_BQX=$?
wait $PID_WAVE_BQX
STATUS_WAVE_BQX=$?
wait $PID_SSA_BQX
STATUS_SSA_BQX=$?

batch3_time=$(($(date +%s) - batch3_start))
echo -e "${GREEN}✅ Batch 3 Complete (${batch3_time}s)${NC}"
echo ""

# Calculate total execution time
total_time=$(($(date +%s) - start_time))

echo ""
echo "================================================================================"
echo "EXECUTION RESULTS - PHASE 1.8 COMPLETE"
echo "================================================================================"
echo ""
echo "Total Execution Time: ${total_time} seconds"
echo "  • Batch 1 (Stage 1.8.1): ${batch1_time}s"
echo "  • Batch 2 (Stage 1.8.2): ${batch2_time}s"
echo "  • Batch 3 (Stage 1.8.3): ${batch3_time}s"
echo ""

# Count failures
FAILURES=0
[ $STATUS_PARA_RATE -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_PARA_BQX -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_MS_30_RATE -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_MS_60_RATE -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_MS_30_BQX -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_MS_60_BQX -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_SPEC_RATE -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_WAVE_RATE -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_SSA_RATE -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_SPEC_BQX -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_WAVE_BQX -ne 0 ] && FAILURES=$((FAILURES + 1))
[ $STATUS_SSA_BQX -ne 0 ] && FAILURES=$((FAILURES + 1))

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ PHASE 1.8 COMPLETE - ALL 12 OPERATIONS SUCCESSFUL!${NC}"
    echo ""
    echo "Features Added: ~164 (44 + 60 + 60)"
    echo "  • Stage 1.8.1 (Parabolic): 44 features (24 rate + 20 bqx)"
    echo "  • Stage 1.8.2 (Multi-Scale): 60 features (30 rate + 30 bqx)"
    echo "  • Stage 1.8.3 (Spectral): 60 features (30 rate + 30 bqx)"
    echo ""
    echo "Tables Created: 6,048"
    echo "  • parabolic_comparison: 1,008 (336 rate + 672 bqx)"
    echo "  • multi_scale: 3,024 (672 rate 30m + 672 rate 60m + 672 bqx 30m + 672 bqx 60m)"
    echo "  • spectral: 3,024 (1,008 rate + 2,016 bqx, across FFT/wavelet/SSA)"
    echo ""
    echo "Feature Progress:"
    echo "  • Before (after Phase 1.6): 734/1,080 (68.0%)"
    echo "  • After (Phase 1.8 COMPLETE): 898/1,080 (83.1%)"
    echo "  • Added: +164 features (+15.2 percentage points)"
    echo ""
    echo "✅ PHASE 1.8 100% COMPLETE - 3/3 STAGES DONE"
    echo ""
    echo "Next Steps:"
    echo "  1. Update AirTable: Mark stages 1.8.1-1.8.3 as 'Done'"
    echo "  2. Commit Phase 1.8 completion to git"
    echo "  3. Implement feature population workers (FFT, wavelets, SSA, multi-scale aggregates)"
    echo "  4. Proceed to Phase 1.9 (Remaining Advanced Features: +182 features → 1,080 total)"
    echo ""
    exit 0
else
    echo -e "${RED}❌ EXECUTION FAILED: $FAILURES/12 operations failed${NC}"
    echo ""
    echo "Review logs in: $LOG_DIR/"
    echo ""
    exit 1
fi
