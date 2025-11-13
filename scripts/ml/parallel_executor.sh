#!/bin/bash
#
# Phase 2: Parallel Execution Orchestrator
# Launches all 3 tracks in parallel on trillium-master EC2
#
# Track 1: Wave 1 Feature Population (9 days, 94 features)
# Track 2: Regression Features (11 days, 180 features)
# Track 3: MVP Pipeline (18 days, validated pipeline)
#
# Convergence: Day 21 → 433 features + operational pipeline
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "================================================================================"
echo "PHASE 2: PARALLEL EXECUTION - ALL 3 TRACKS"
echo "================================================================================"
echo ""
echo "Instance: $(hostname)"
echo "CPUs: $(nproc)"
echo "Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "Disk: $(df -h /home/ubuntu | tail -1 | awk '{print $4}') free"
echo ""
echo "================================================================================"
echo ""

# Create log directories
echo "Creating log directories..."
mkdir -p /tmp/logs/track{1,2,3}
mkdir -p /home/ubuntu/bqx-ml/data/extracted
mkdir -p /home/ubuntu/bqx-ml/scripts/ml

echo -e "${GREEN}✓${NC} Log directories created"
echo ""

# Database connection
DB_HOST="trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com"
DB_USER="postgres"
DB_NAME="bqx"
export PGPASSWORD='BQX_Aurora_2025_Secure'

# Test database connection
echo "Testing database connection..."
if timeout 5 psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Database connection successful"
else
    echo -e "${RED}✗${NC} Database connection failed"
    exit 1
fi
echo ""

# Function to check if process is running
check_process() {
    local pid=$1
    if ps -p $pid > /dev/null 2>&1; then
        return 0  # Running
    else
        return 1  # Not running
    fi
}

# ============================================================================
# TRACK 2: Create Regression Tables (prerequisite)
# ============================================================================

echo "================================================================================"
echo "TRACK 2: CREATING REGRESSION TABLES"
echo "================================================================================"
echo ""
echo "This will create 1,064 tables (28 pairs × 38 partitions)"
echo "Expected duration: 3-5 minutes"
echo ""

START_TIME=$(date +%s)

psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
    -f /home/ubuntu/bqx-ml/scripts/ml/create_regression_tables.sql \
    > /tmp/logs/track2/create_tables.log 2>&1

if [ $? -eq 0 ]; then
    ELAPSED=$(($(date +%s) - START_TIME))
    echo -e "${GREEN}✓${NC} Regression tables created successfully (${ELAPSED}s)"
    echo ""
else
    echo -e "${RED}✗${NC} Failed to create regression tables"
    echo "Check log: /tmp/logs/track2/create_tables.log"
    exit 1
fi

# ============================================================================
# LAUNCH ALL 3 TRACKS IN PARALLEL
# ============================================================================

echo "================================================================================"
echo "LAUNCHING ALL 3 TRACKS IN PARALLEL"
echo "================================================================================"
echo ""

# Track 3: Feature Extraction (longest duration)
echo -e "${BLUE}Starting Track 3: Feature Extraction${NC}"
echo "  Duration: 18 days"
echo "  Output: 159 features × 28 pairs → Parquet files"
echo "  Log: /tmp/logs/track3/extract.log"
echo ""

nohup python3 /home/ubuntu/bqx-ml/scripts/ml/extract_features_from_db.py \
    > /tmp/logs/track3/extract.log 2>&1 &
TRACK3_PID=$!
echo "  PID: $TRACK3_PID"
sleep 2

if check_process $TRACK3_PID; then
    echo -e "  ${GREEN}✓${NC} Track 3 started successfully"
else
    echo -e "  ${RED}✗${NC} Track 3 failed to start"
    exit 1
fi
echo ""

# Track 2: Regression Population (most compute-intensive)
echo -e "${BLUE}Starting Track 2: Regression Population${NC}"
echo "  Duration: 11 days"
echo "  Features: 180 (90 rate + 90 bqx)"
echo "  Log: /tmp/logs/track2/populate.log"
echo ""

nohup python3 /home/ubuntu/bqx-ml/scripts/ml/populate_regression_features_worker.py \
    > /tmp/logs/track2/populate.log 2>&1 &
TRACK2_PID=$!
echo "  PID: $TRACK2_PID"
sleep 2

if check_process $TRACK2_PID; then
    echo -e "  ${GREEN}✓${NC} Track 2 started successfully"
else
    echo -e "  ${RED}✗${NC} Track 2 failed to start"
    echo -e "  ${YELLOW}Note:${NC} Check log for errors"
fi
echo ""

# Track 1: Bollinger BQX (quick win)
echo -e "${BLUE}Starting Track 1: Bollinger BQX${NC}"
echo "  Duration: 2-3 days"
echo "  Features: 10 (Bollinger bands on BQX momentum)"
echo "  Log: /tmp/logs/track1/bollinger.log"
echo ""

nohup python3 /home/ubuntu/bqx-ml/scripts/ml/populate_bollinger_bqx_worker.py \
    > /tmp/logs/track1/bollinger.log 2>&1 &
TRACK1_PID=$!
echo "  PID: $TRACK1_PID"
sleep 2

if check_process $TRACK1_PID; then
    echo -e "  ${GREEN}✓${NC} Track 1 started successfully"
else
    echo -e "  ${RED}✗${NC} Track 1 failed to start"
    echo -e "  ${YELLOW}Note:${NC} Check log for errors"
fi
echo ""

# ============================================================================
# MONITORING INFORMATION
# ============================================================================

echo "================================================================================"
echo "ALL 3 TRACKS RUNNING IN PARALLEL"
echo "================================================================================"
echo ""
echo "Track PIDs:"
echo "  Track 1 (Bollinger BQX):     $TRACK1_PID"
echo "  Track 2 (Regression):        $TRACK2_PID"
echo "  Track 3 (MVP Pipeline):      $TRACK3_PID"
echo ""
echo "================================================================================"
echo "MONITORING COMMANDS"
echo "================================================================================"
echo ""
echo "Watch all logs:"
echo "  tail -f /tmp/logs/track{1,2,3}/*.log"
echo ""
echo "Monitor Track 1 progress:"
echo "  tail -f /tmp/logs/track1/bollinger.log"
echo ""
echo "Monitor Track 2 progress:"
echo "  tail -f /tmp/logs/track2/populate.log"
echo ""
echo "Monitor Track 3 progress:"
echo "  tail -f /tmp/logs/track3/extract.log"
echo ""
echo "Check process status:"
echo "  ps aux | grep python3"
echo ""
echo "Monitor system resources:"
echo "  htop"
echo "  free -h"
echo "  df -h"
echo ""
echo "Check database connections:"
echo "  PGPASSWORD='BQX_Aurora_2025_Secure' psql -h $DB_HOST -U $DB_USER -d $DB_NAME \\"
echo "    -c \"SELECT count(*) FROM pg_stat_activity WHERE datname='bqx';\""
echo ""
echo "================================================================================"
echo "EXPECTED MILESTONES"
echo "================================================================================"
echo ""
echo "Day 1-2:   Track 1 completes Bollinger BQX (10 features)"
echo "Day 3:     Track 3 completes extraction (159 features → Parquet)"
echo "Day 9:     Track 1 COMPLETE (94 features total)"
echo "Day 11:    Track 2 COMPLETE (180 features total)"
echo "Day 18:    Track 3 COMPLETE (pipeline validated)"
echo "Day 21:    CONVERGENCE - 433 features + operational pipeline"
echo ""
echo "================================================================================"
echo "NEXT STEPS"
echo "================================================================================"
echo ""
echo "1. Monitor logs for errors"
echo "2. Check memory usage (should stay under 25 GB)"
echo "3. Check CPU load (should stay under 8.0)"
echo "4. Update AirTable when stages complete"
echo "5. Commit progress to git weekly"
echo ""
echo "================================================================================"
echo "To stop all tracks:"
echo "  kill $TRACK1_PID $TRACK2_PID $TRACK3_PID"
echo "================================================================================"
echo ""

# Save PIDs to file for later reference
echo "$TRACK1_PID" > /tmp/track1.pid
echo "$TRACK2_PID" > /tmp/track2.pid
echo "$TRACK3_PID" > /tmp/track3.pid

echo -e "${GREEN}All tracks launched successfully!${NC}"
echo ""
echo "Parallel execution started at: $(date)"
echo ""
