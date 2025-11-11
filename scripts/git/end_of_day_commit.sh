#!/bin/bash
# End-of-day automated commit script
# Usage: Run manually or via cron at end of work day

cd /home/ubuntu/bqx-ml

# Check if there are uncommitted changes
if [[ -z $(git status -s) ]]; then
    echo "No uncommitted changes. Skipping end-of-day commit."
    exit 0
fi

echo "Uncommitted changes found. Creating end-of-day commit..."

# Get brief status of running processes
BQX_STATUS="Not running"
REG_STATUS="Not running"
BQX_PROGRESS="N/A"
REG_PROGRESS="N/A"

if pgrep -f "backward_worker_index.py" > /dev/null; then
    BQX_STATUS="Running"
    # Try to extract progress from log
    if [ -f "/tmp/stage_1_5_4_3_backfill.log" ]; then
        BQX_PROGRESS=$(tail -5 /tmp/stage_1_5_4_3_backfill.log | grep -oP "Processing:.*" | tail -1 || echo "In progress")
    fi
fi

if pgrep -f "regression_worker_index.py" > /dev/null; then
    REG_STATUS="Running"
    if [ -f "/tmp/stage_1_5_5_3_backfill.log" ]; then
        REG_PROGRESS=$(tail -5 /tmp/stage_1_5_5_3_backfill.log | grep -oP "Progress:.*" | tail -1 || echo "In progress")
    fi
fi

# Get summary of changes
CHANGED_FILES=$(git status -s | wc -l)
ADDED_LINES=$(git diff --cached --numstat | awk '{s+=$1} END {print s}')
DELETED_LINES=$(git diff --cached --numstat | awk '{s+=$2} END {print s}')

# Create commit message
COMMIT_MSG="chore: End-of-day commit - $(date +%Y-%m-%d)

CHANGES SUMMARY:
- Files modified: ${CHANGED_FILES}
- Lines added: ${ADDED_LINES:-0}
- Lines deleted: ${DELETED_LINES:-0}

MONITOR STATUS:
- BQX Backfill: ${BQX_STATUS} (${BQX_PROGRESS})
- REG Backfill: ${REG_STATUS} (${REG_PROGRESS})

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Stage all changes
git add -A

# Commit
git commit -m "$COMMIT_MSG"

# Push
if git push origin main; then
    echo "✓ End-of-day commit pushed successfully"
    echo "Commit hash: $(git rev-parse --short HEAD)"
else
    echo "✗ Failed to push. Commit created locally."
    exit 1
fi
