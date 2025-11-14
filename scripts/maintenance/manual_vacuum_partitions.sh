#!/bin/bash
# ============================================================================
# MANUAL VACUUM SCRIPT FOR BQX PARTITIONS
# ============================================================================
# Purpose: Manually vacuum all reg_rate and reg_bqx partitions
# Note: Only run if autovacuum is insufficient (currently not needed - 0% dead rows)
# Usage: ./manual_vacuum_partitions.sh
# ============================================================================

set -e

PGHOST="trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com"
PGUSER="postgres"
PGDATABASE="bqx"
export PGPASSWORD='BQX_Aurora_2025_Secure'

echo "================================================================================"
echo "MANUAL VACUUM: BQX PARTITIONS"
echo "================================================================================"
echo ""
echo "NOTE: This script manually vacuums all reg_rate and reg_bqx partitions."
echo "      Current dead row percentage: 0% (autovacuum is working well)"
echo "      Only run if explicitly needed for maintenance."
echo ""
read -p "Continue with manual vacuum? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Starting manual vacuum..."
echo ""

# Get list of all reg_rate partitions
echo "Vacuuming reg_rate partitions..."
PARTITIONS=$(psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -t -A -c \
    "SELECT tablename FROM pg_tables WHERE schemaname = 'bqx' AND tablename LIKE 'reg_rate_%' ORDER BY tablename;")

counter=0
total=$(echo "$PARTITIONS" | wc -l)

for partition in $PARTITIONS; do
    counter=$((counter + 1))
    if [ $((counter % 50)) -eq 0 ]; then
        echo "  Progress: $counter / $total reg_rate partitions"
    fi
    psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -c "VACUUM ANALYZE bqx.$partition;" > /dev/null 2>&1
done

echo "  ✅ Completed: $counter reg_rate partitions vacuumed"
echo ""

# Get list of all reg_bqx partitions
echo "Vacuuming reg_bqx partitions..."
PARTITIONS=$(psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -t -A -c \
    "SELECT tablename FROM pg_tables WHERE schemaname = 'bqx' AND tablename LIKE 'reg_bqx_%' ORDER BY tablename;")

counter=0
total=$(echo "$PARTITIONS" | wc -l)

for partition in $PARTITIONS; do
    counter=$((counter + 1))
    if [ $((counter % 50)) -eq 0 ]; then
        echo "  Progress: $counter / $total reg_bqx partitions"
    fi
    psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -c "VACUUM ANALYZE bqx.$partition;" > /dev/null 2>&1
done

echo "  ✅ Completed: $counter reg_bqx partitions vacuumed"
echo ""

echo "================================================================================"
echo "MANUAL VACUUM COMPLETE"
echo "================================================================================"
echo ""
echo "Summary:"
echo "  - All reg_rate and reg_bqx partitions vacuumed"
echo "  - Query planner statistics updated (ANALYZE)"
echo "  - Dead tuples reclaimed"
echo ""
