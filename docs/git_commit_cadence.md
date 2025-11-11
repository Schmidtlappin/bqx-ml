# Git Commit & Push Cadence Strategy

**Purpose:** Establish strategic, recurring git commit and push actions aligned with Airtable updates and development milestones.

**Created:** 2025-11-10
**Owner:** BQX ML Team

---

## Overview

This document defines when and how to commit and push code to git as part of the operational workflow. Git commits serve as:
1. **Progress Checkpoints:** Snapshot work at meaningful milestones
2. **Audit Trail:** Document evolution of codebase and decisions
3. **Synchronization Points:** Align git history with Airtable updates
4. **Recovery Points:** Enable rollback if issues discovered

**Core Principle:** Every Airtable update should have a corresponding git commit, creating bidirectional traceability.

---

## Commit Cadence Levels

### Level 1: Micro-Commits (Optional, Developer Discretion)
**Frequency:** As needed during active development
**Scope:** Work-in-progress, experimental changes
**Push:** Local only (no push to remote)

**Purpose:**
- Save incremental progress
- Enable local experimentation
- Quick rollback during development

**Guidelines:**
- Use descriptive branch names: `feature/stage-1-5-4-bqx-backfill`
- Commit messages can be informal: "wip: testing decimal conversion fix"
- DO NOT push to main branch
- These are collapsed/squashed before pushing

**Example:**
```bash
git checkout -b feature/stage-1-5-5-reg-backfill
git add scripts/backfill/regression_worker_index.py
git commit -m "wip: add decimal to float conversion"
# NO PUSH - local only
```

---

### Level 2: Task Completion Commits (Required)
**Frequency:** When completing each Airtable task
**Scope:** Single task deliverable
**Push:** To remote after task verified

**Purpose:**
- Document completion of atomic work units
- Enable task-level rollback
- Provide granular history

**Trigger Events:**
- Task marked "Complete" in Airtable
- Bug fix verified with tests
- Script/tool completed and tested
- Documentation section finished

**Commit Message Format:**
```
<type>(<task-id>): <description>

<detailed explanation>

Task: [Task ID or link]
Duration: [Actual time spent]
Testing: [Verification performed]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types:**
- `feat`: New feature or capability
- `fix`: Bug fix
- `refactor`: Code restructuring without behavior change
- `docs`: Documentation only
- `test`: Test additions or modifications
- `chore`: Maintenance tasks (dependencies, config)

**Example:**
```bash
# Task: Fix REG backfill Decimal type incompatibility (TSK-155)
git add scripts/backfill/regression_worker_index.py
git commit -m "fix(TSK-155): Convert PostgreSQL Decimal to float for numpy polyfit

PostgreSQL returns rate_index as Decimal type, causing numpy polyfit
to fail with 'unsupported operand type' error. Convert to float array
before regression calculations.

Task: https://airtable.com/appR3PPnrNkVo48mO/tblTasks/TSK-155
Duration: 2 hours (discovery + fix + verification)
Testing: Verified 32,434 rows written to reg_audcad_2024_07

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
```

**Airtable Sync:**
After push, update task in Airtable:
- Status: "Complete"
- Actual Duration: 2 hours
- Notes: "Commit: <commit-hash>"
- Deliverables: Link to GitHub commit

---

### Level 3: Stage Milestone Commits (Required)
**Frequency:** At stage completion or significant milestones (25%, 50%, 75%, 100%)
**Scope:** All work completed in stage so far
**Push:** To remote immediately after verification

**Purpose:**
- Create recovery points for large work efforts
- Align with Airtable stage progress updates
- Enable stage-level rollback if needed

**Trigger Events:**
- Stage reaches 25%, 50%, 75%, or 100% completion
- Critical bug fix applied to running process
- Major refactoring completed
- Database schema changes deployed

**Commit Message Format:**
```
<type>: <stage description> - <milestone>

<comprehensive summary of work>

Stage: [Stage ID]
Progress: [X% → Y%]
Key Deliverables:
- [Deliverable 1]
- [Deliverable 2]

Documentation: [Link to stage docs]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Example:**
```bash
git add scripts/backfill/ scripts/refactor/ docs/
git commit -m "feat: Complete Stage 1.5.4-1.5.5 index-based backfills - 38% milestone

Stage 1.5.4: BQX Index-Based Backfill
- Progress: 0% → 38.3% (129/336 partitions)
- Index-based schema reduces storage 24% (75→57 fields)
- Fixed monitoring script (process filtering, octal parsing)

Stage 1.5.5: REG Index-Based Backfill
- Progress: 0% → 5.5% (25/448 partitions)
- Fixed Decimal→float conversion bug
- Fixed numpy scalar serialization bug

Key Deliverables:
- backward_worker_index.py (BQX backfill script)
- regression_worker_index.py (REG backfill script)
- monitor_backfills.sh (real-time dashboard)
- 20+ documentation files

Stage: 1.5.4, 1.5.5
Progress: 1.5.4: 0%→38.3%, 1.5.5: 0%→5.5%
Documentation: docs/stage_1_5_4_5_progress_report.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
```

**Airtable Sync:**
After push, update stage in Airtable:
- Progress: Update percentage
- Notes: "Commit: <commit-hash> - <milestone>"
- Link latest commit in stage record

---

### Level 4: Phase Completion Commits (Required)
**Frequency:** When phase 100% complete
**Scope:** All phase deliverables, documentation, and metadata
**Push:** To remote, then create git tag

**Purpose:**
- Mark major project milestones
- Enable phase-level rollback
- Facilitate code reviews and audits
- Create stable release points

**Trigger Events:**
- Phase reaches 100% completion
- All phase tasks marked complete in Airtable
- Phase documentation finalized
- Phase metrics compiled

**Commit Message Format:**
```
feat: Complete Phase [X.Y] - [Phase Name]

<comprehensive phase summary>

COMPLETED STAGES:
- Stage X.Y.1: [Description] (Duration: Xh, Variance: ±Y%)
- Stage X.Y.2: [Description] (Duration: Xh, Variance: ±Y%)

KEY ACHIEVEMENTS:
- [Achievement 1]
- [Achievement 2]

METRICS:
- Total Duration: Xh planned, Yh actual (±Z% variance)
- Storage Impact: +N GB
- Performance Improvement: [Metric]

LESSONS LEARNED:
- [Lesson 1]
- [Lesson 2]

Phase Documentation: docs/phase_[x_y]_completion_report.md
Airtable Phase: [Link]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Example:**
```bash
git add docs/phase_1_5_completion_report.md scripts/ docs/
git commit -m "feat: Complete Phase 1.5 - Index-Based Architecture Refactor

Completed comprehensive refactor to index-based architecture, eliminating
pair-specific biases and enabling unified multi-pair model training.

COMPLETED STAGES:
- Stage 1.5.1: Baseline Rate Determination (2h planned, 1.5h actual, -25%)
- Stage 1.5.2: M1 Index Enhancement (3h planned, 2.8h actual, -7%)
- Stage 1.5.4: BQX Table Recalculation (6h planned, 7.2h actual, +20%)
- Stage 1.5.5: REG Table Recalculation (4h planned, 5.1h actual, +28%)

KEY ACHIEVEMENTS:
- 24% storage reduction (removed 18 _norm fields per table)
- Cross-pair comparability via base-100 indexing
- Fixed critical Decimal/numpy incompatibility
- Created comprehensive monitoring tools

METRICS:
- Total Duration: 22h planned, 24.5h actual (+11% variance)
- Storage Impact: -3.2 GB (schema reduction offset new data)
- Data Quality: 100% of 784 partitions verified
- R² Baseline: 0.88-0.90 (maintained after refactor)

LESSONS LEARNED:
- PostgreSQL Decimal types require explicit conversion for numpy
- pg_stat_user_tables can lag significantly, parse logs instead
- Parallel backfills maximize 2-core system utilization
- Real-time monitoring critical for long-running processes

Phase Documentation: docs/phase_1_5_completion_report.md
Airtable Phase: https://airtable.com/appR3PPnrNkVo48mO/tblPhases/recl7nHgbrLjfjD5K

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com)"

git push origin main
git tag -a phase-1.5-complete -m "Phase 1.5: Index-Based Architecture Refactor"
git push origin phase-1.5-complete
```

**Airtable Sync:**
After push:
1. Update phase status to "Complete"
2. Set actual duration and variance
3. Link git tag in phase record
4. Generate phase completion report
5. Archive phase documentation

---

### Level 5: Daily End-of-Session Commits (Required if work done)
**Frequency:** End of each active development session
**Scope:** All uncommitted work from the session
**Push:** To remote after quick verification

**Purpose:**
- Prevent work loss overnight
- Synchronize with daily Airtable updates
- Enable next-day continuity
- Provide audit trail of daily progress

**Trigger Events:**
- End of work day (manual trigger)
- Automated via cron job at specified time
- Before system shutdown/maintenance
- When switching contexts (different project)

**Commit Message Format:**
```
chore: End-of-day commit - [Date] - [Brief summary]

PROGRESS TODAY:
- [Work item 1 completed/in progress]
- [Work item 2 completed/in progress]

NEXT STEPS:
- [Next action 1]
- [Next action 2]

Airtable Updated: [Yes/No]
Monitor Status: [Brief status of running processes]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Example:**
```bash
git add docs/ scripts/airtable/
git commit -m "chore: End-of-day commit - 2025-11-10 - Airtable operational cadence

PROGRESS TODAY:
- Created comprehensive Airtable operational cadence framework
- Added weekly gap assessment template
- Designed automation script architecture
- Updated Stage 1.5.4 & 1.5.5 progress in Airtable

NEXT STEPS:
- Monitor BQX backfill completion (ETA 2h)
- Monitor REG backfill completion (ETA 8h)
- Run first weekly gap assessment on Monday
- Implement daily_progress_update.py script

Airtable Updated: Yes (Stage 1.5.4 @ 38.3%, Stage 1.5.5 @ 5.5%)
Monitor Status: BQX 38.3% (2h ETA), REG 5.5% (8h ETA), both healthy

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
```

**Automation Script:**
```bash
#!/bin/bash
# /home/ubuntu/bqx-ml/scripts/git/end_of_day_commit.sh

cd /home/ubuntu/bqx-ml

# Check if there are uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo "Uncommitted changes found. Creating end-of-day commit..."

    # Get brief status of running processes
    BQX_STATUS="Not running"
    REG_STATUS="Not running"

    if pgrep -f "backward_worker_index.py" > /dev/null; then
        BQX_STATUS="Running"
    fi

    if pgrep -f "regression_worker_index.py" > /dev/null; then
        REG_STATUS="Running"
    fi

    # Create commit
    git add -A
    git commit -m "chore: End-of-day commit - $(date +%Y-%m-%d)

PROGRESS TODAY:
- [Auto-generated from git diff summary]

Monitor Status: BQX: $BQX_STATUS, REG: $REG_STATUS

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com)"

    git push origin main

    echo "✓ End-of-day commit pushed successfully"
else
    echo "No uncommitted changes. Skipping end-of-day commit."
fi
```

**Cron Schedule:**
```bash
# Run end-of-day commit at 6 PM daily
0 18 * * * /home/ubuntu/bqx-ml/scripts/git/end_of_day_commit.sh >> /tmp/eod_commit.log 2>&1
```

---

## Git + Airtable Synchronization Matrix

| Event | Git Action | Airtable Action | Timing |
|-------|-----------|-----------------|--------|
| Task completed | Level 2 commit + push | Mark task "Complete" | Immediate |
| Stage milestone (25/50/75/100%) | Level 3 commit + push | Update stage progress % | Immediate |
| Critical bug fix | Level 2 or 3 commit + push | Create issue record, link commit | Immediate |
| Daily work session end | Level 5 commit + push | Run daily progress update script | End of day |
| Weekly gap assessment | No commit (unless gaps found) | Generate gap report | Monday AM |
| Phase completion | Level 4 commit + tag | Mark phase "Complete", archive | Phase 100% |
| Biweekly phase review | No commit (planning only) | Create tasks for next phase | Every other Friday |
| Monthly architecture review | Create RFC if changes needed | Update technical debt register | First Monday |

---

## Commit Best Practices

### DO ✅

1. **Commit Atomically:**
   - One logical change per commit
   - If task includes bug fix + feature, split into 2 commits

2. **Write Descriptive Messages:**
   - First line: <50 chars, imperative mood ("Add" not "Added")
   - Body: Explain WHY, not just WHAT
   - Reference Airtable task/stage IDs

3. **Verify Before Pushing:**
   - Run relevant tests
   - Check monitoring dashboard if long-running processes
   - Verify documentation links work

4. **Link to Airtable:**
   - Include task/stage IDs in commit messages
   - Update Airtable with commit hash after push
   - Create bidirectional traceability

5. **Use Semantic Commit Types:**
   - `feat`: New feature
   - `fix`: Bug fix
   - `docs`: Documentation only
   - `refactor`: Code restructuring
   - `test`: Test changes
   - `chore`: Maintenance

### DON'T ❌

1. **Don't Commit Secrets:**
   - No API keys, passwords, tokens
   - Use environment variables
   - GitHub push protection will block

2. **Don't Force Push to Main:**
   - Use branches for experimental work
   - Rebase/squash before merging to main
   - Force push only on feature branches

3. **Don't Commit WIP to Main:**
   - Use feature branches for work-in-progress
   - Squash commits before merging
   - Main branch = production-ready code

4. **Don't Skip Verification:**
   - Always test before committing critical code
   - Don't push broken code to main
   - Use draft commits locally if unsure

5. **Don't Batch Unrelated Changes:**
   - Multiple tasks = multiple commits
   - Easier rollback if issues found
   - Clearer git history

---

## Automated Commit Scripts

### 1. Task Completion Commit
**Script:** `scripts/git/commit_task.sh`
**Usage:** `./scripts/git/commit_task.sh TSK-155 "Fix REG Decimal conversion"`

```bash
#!/bin/bash
# Automate Level 2 (Task Completion) commits

TASK_ID=$1
TASK_DESC=$2

if [ -z "$TASK_ID" ] || [ -z "$TASK_DESC" ]; then
    echo "Usage: $0 <task-id> <description>"
    exit 1
fi

# Prompt for commit type
echo "Select commit type:"
echo "1) feat - New feature"
echo "2) fix - Bug fix"
echo "3) docs - Documentation"
echo "4) refactor - Code restructuring"
echo "5) test - Tests"
echo "6) chore - Maintenance"
read -p "Enter choice (1-6): " choice

case $choice in
    1) TYPE="feat";;
    2) TYPE="fix";;
    3) TYPE="docs";;
    4) TYPE="refactor";;
    5) TYPE="test";;
    6) TYPE="chore";;
    *) echo "Invalid choice"; exit 1;;
esac

# Prompt for files to include
echo "Files changed:"
git status -s
read -p "Add all changed files? (y/n): " add_all

if [ "$add_all" = "y" ]; then
    git add -A
else
    read -p "Enter files to add (space-separated): " files
    git add $files
fi

# Get detailed description
read -p "Detailed explanation (press Enter to skip): " details
read -p "Duration (e.g., '2 hours'): " duration
read -p "Testing performed: " testing

# Create commit message
COMMIT_MSG="${TYPE}(${TASK_ID}): ${TASK_DESC}"

if [ -n "$details" ]; then
    COMMIT_MSG="${COMMIT_MSG}\n\n${details}"
fi

COMMIT_MSG="${COMMIT_MSG}\n\nTask: ${TASK_ID}"
COMMIT_MSG="${COMMIT_MSG}\nDuration: ${duration}"
COMMIT_MSG="${COMMIT_MSG}\nTesting: ${testing}"
COMMIT_MSG="${COMMIT_MSG}\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"

# Commit
git commit -m "$(echo -e "$COMMIT_MSG")"

# Push
read -p "Push to remote? (y/n): " push_it
if [ "$push_it" = "y" ]; then
    git push origin main
    echo "✓ Committed and pushed successfully"

    # Get commit hash
    COMMIT_HASH=$(git rev-parse --short HEAD)
    echo "Commit hash: $COMMIT_HASH"
    echo "Remember to update Airtable task with commit hash!"
else
    echo "✓ Committed locally (not pushed)"
fi
```

---

### 2. Stage Milestone Commit
**Script:** `scripts/git/commit_stage_milestone.sh`
**Usage:** `./scripts/git/commit_stage_milestone.sh 1.5.4 38.3 "BQX backfill 38% complete"`

```bash
#!/bin/bash
# Automate Level 3 (Stage Milestone) commits

STAGE_ID=$1
PROGRESS=$2
DESCRIPTION=$3

if [ -z "$STAGE_ID" ] || [ -z "$PROGRESS" ] || [ -z "$DESCRIPTION" ]; then
    echo "Usage: $0 <stage-id> <progress-%> <description>"
    exit 1
fi

echo "Creating Stage $STAGE_ID milestone commit ($PROGRESS% progress)..."

# Prompt for key deliverables
echo "Enter key deliverables (one per line, empty line to finish):"
DELIVERABLES=""
while read -p "- " deliverable; do
    [ -z "$deliverable" ] && break
    DELIVERABLES="${DELIVERABLES}- ${deliverable}\n"
done

# Prompt for documentation link
read -p "Documentation link (relative path from repo root): " doc_link

# Add files
git add -A

# Create commit message
COMMIT_MSG="feat: ${DESCRIPTION}\n\n"
COMMIT_MSG="${COMMIT_MSG}Stage: ${STAGE_ID}\n"
COMMIT_MSG="${COMMIT_MSG}Progress: ${PROGRESS}%\n\n"

if [ -n "$DELIVERABLES" ]; then
    COMMIT_MSG="${COMMIT_MSG}Key Deliverables:\n${DELIVERABLES}\n"
fi

if [ -n "$doc_link" ]; then
    COMMIT_MSG="${COMMIT_MSG}Documentation: ${doc_link}\n"
fi

COMMIT_MSG="${COMMIT_MSG}\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"

# Commit and push
git commit -m "$(echo -e "$COMMIT_MSG")"
git push origin main

COMMIT_HASH=$(git rev-parse --short HEAD)
echo "✓ Stage milestone committed and pushed"
echo "Commit hash: $COMMIT_HASH"
echo "Remember to update Airtable Stage ${STAGE_ID} with:"
echo "  - Progress: ${PROGRESS}%"
echo "  - Commit: ${COMMIT_HASH}"
```

---

### 3. Sync Airtable After Commit
**Script:** `scripts/git/sync_airtable_after_commit.py`
**Purpose:** Automatically update Airtable with latest commit info

```python
#!/usr/bin/env python3
"""
Sync Airtable with latest git commit information
Runs after each push to update task/stage records with commit hash
"""

import os
import sys
import subprocess
import requests

BASE_ID = 'appR3PPnrNkVo48mO'
API_TOKEN = os.environ.get('AIRTABLE_API_KEY')

def get_latest_commit():
    """Get latest commit hash and message"""
    hash_result = subprocess.run(
        ['git', 'rev-parse', '--short', 'HEAD'],
        capture_output=True, text=True
    )
    commit_hash = hash_result.stdout.strip()

    msg_result = subprocess.run(
        ['git', 'log', '-1', '--pretty=%B'],
        capture_output=True, text=True
    )
    commit_msg = msg_result.stdout.strip()

    return commit_hash, commit_msg

def extract_task_id(commit_msg):
    """Extract task ID from commit message (e.g., TSK-155)"""
    import re
    match = re.search(r'TSK-\d+', commit_msg)
    return match.group(0) if match else None

def extract_stage_id(commit_msg):
    """Extract stage ID from commit message (e.g., Stage: 1.5.4)"""
    import re
    match = re.search(r'Stage:\s*([\d.]+)', commit_msg)
    return match.group(1) if match else None

def update_task(task_id, commit_hash, commit_msg):
    """Update Airtable task with commit information"""
    # Find task by ID
    url = f'https://api.airtable.com/v0/{BASE_ID}/Tasks'
    params = {'filterByFormula': f"{{Task ID}} = '{task_id}'"}
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json'
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200 or not response.json().get('records'):
        print(f"Task {task_id} not found in Airtable")
        return False

    record_id = response.json()['records'][0]['id']
    current_notes = response.json()['records'][0]['fields'].get('Notes', '')

    # Append commit info to notes
    new_notes = f"{current_notes}\n\nCommit: {commit_hash}\n{commit_msg}"

    # Update task
    update_url = f'{url}/{record_id}'
    payload = {'fields': {'Notes': new_notes}}

    response = requests.patch(update_url, json=payload, headers=headers)
    return response.status_code == 200

def main():
    """Main execution"""
    if not API_TOKEN:
        print("Error: AIRTABLE_API_KEY not set")
        return 1

    commit_hash, commit_msg = get_latest_commit()
    print(f"Latest commit: {commit_hash}")

    # Check for task ID
    task_id = extract_task_id(commit_msg)
    if task_id:
        print(f"Found task ID: {task_id}")
        if update_task(task_id, commit_hash, commit_msg):
            print(f"✓ Updated task {task_id} in Airtable")
        else:
            print(f"✗ Failed to update task {task_id}")

    # Check for stage ID
    stage_id = extract_stage_id(commit_msg)
    if stage_id:
        print(f"Found stage ID: {stage_id}")
        # Similar logic for stage updates

    return 0

if __name__ == '__main__':
    sys.exit(main())
```

---

## Git Hooks Integration

### Post-Commit Hook
**File:** `.git/hooks/post-commit`
**Purpose:** Remind to update Airtable after commit

```bash
#!/bin/bash
# .git/hooks/post-commit

COMMIT_MSG=$(git log -1 --pretty=%B)

# Check if commit message mentions task or stage
if echo "$COMMIT_MSG" | grep -qE "(TSK-|Stage:)"; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  REMINDER: Update Airtable"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if echo "$COMMIT_MSG" | grep -q "TSK-"; then
        TASK_ID=$(echo "$COMMIT_MSG" | grep -oE "TSK-[0-9]+" | head -1)
        echo "  Task: $TASK_ID"
        echo "  Action: Mark as Complete, add commit hash"
    fi

    if echo "$COMMIT_MSG" | grep -q "Stage:"; then
        STAGE_ID=$(echo "$COMMIT_MSG" | grep -oP "Stage:\s*\K[\d.]+" | head -1)
        echo "  Stage: $STAGE_ID"
        echo "  Action: Update progress %, add commit hash"
    fi

    echo ""
    echo "  Run: python3 scripts/git/sync_airtable_after_commit.py"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
fi
```

### Pre-Push Hook
**File:** `.git/hooks/pre-push`
**Purpose:** Verify no secrets, run quick tests

```bash
#!/bin/bash
# .git/hooks/pre-push

echo "Running pre-push checks..."

# Check for secrets (API keys, passwords)
if git diff origin/main --cached | grep -iE "(api[_-]?key|password|secret|token)" | grep -v "AIRTABLE_API_KEY"; then
    echo "⚠️  WARNING: Potential secret detected in commit"
    echo "Review the following lines:"
    git diff origin/main --cached | grep -iE "(api[_-]?key|password|secret|token)" | grep -v "AIRTABLE_API_KEY"
    read -p "Continue with push? (y/n): " continue
    if [ "$continue" != "y" ]; then
        echo "Push aborted"
        exit 1
    fi
fi

# Check for large files (>10MB)
LARGE_FILES=$(git diff origin/main --cached --numstat | awk '$1 > 10000 {print $3}')
if [ -n "$LARGE_FILES" ]; then
    echo "⚠️  WARNING: Large files detected (>10MB):"
    echo "$LARGE_FILES"
    read -p "Continue with push? (y/n): " continue
    if [ "$continue" != "y" ]; then
        echo "Push aborted"
        exit 1
    fi
fi

echo "✓ Pre-push checks passed"
```

---

## Commit Message Templates

### Template File Location
**File:** `.gitmessage`

```
<type>(<scope>): <subject>

<body>

Task/Stage: [ID or link]
Duration: [Time spent]
Testing: [Verification performed]

# Type: feat, fix, docs, refactor, test, chore
# Scope: TSK-XXX, Stage X.Y.Z, or component name
# Subject: Imperative mood, <50 chars, no period
#
# Body: Explain WHY, not WHAT. Reference issues/tasks.
#       Wrap at 72 chars.
#
# Footer: Task/Stage IDs, duration, testing notes

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Setup:**
```bash
git config --global commit.template /home/ubuntu/bqx-ml/.gitmessage
```

---

## Rollback Procedures

### Rolling Back Task-Level Changes
```bash
# Find the commit for the task
git log --grep="TSK-155" --oneline

# Revert specific commit
git revert <commit-hash>

# Or reset to before the commit (if not pushed)
git reset --hard <previous-commit-hash>
```

### Rolling Back Stage-Level Changes
```bash
# Find stage milestone commits
git log --grep="Stage: 1.5.4" --oneline

# Revert to previous milestone
git revert <milestone-commit-hash>

# Or create new branch from that point
git checkout -b revert-stage-1-5-4 <milestone-commit-hash>
```

### Rolling Back Phase-Level Changes
```bash
# List phase tags
git tag -l "phase-*"

# Checkout specific phase
git checkout phase-1.5-complete

# Or revert entire phase
git revert <phase-start-commit>..<phase-end-commit>
```

---

## Metrics & KPIs

### Git Activity Metrics

1. **Commit Frequency:**
   - Formula: Commits per day
   - Target: 3-5 commits per active day
   - Measured: Weekly

2. **Commit Granularity:**
   - Formula: Average files per commit
   - Target: 2-5 files (indicates atomic commits)
   - Measured: Weekly

3. **Git-Airtable Sync Rate:**
   - Formula: (Airtable tasks with commit links / Total completed tasks) × 100%
   - Target: >95%
   - Measured: Weekly

4. **Push Frequency:**
   - Formula: Pushes per day
   - Target: 2-4 pushes per active day
   - Measured: Weekly

5. **Branch Lifetime:**
   - Formula: Average days from branch creation to merge
   - Target: <3 days (encourages incremental work)
   - Measured: Monthly

---

## Next Steps

**Immediate (This Week):**
1. Create commit helper scripts (`commit_task.sh`, `commit_stage_milestone.sh`)
2. Set up git hooks (post-commit, pre-push)
3. Configure commit message template
4. Document current commit hash in Airtable for Stages 1.5.4 & 1.5.5

**Short-Term (Next 2 Weeks):**
1. Implement `sync_airtable_after_commit.py` automation
2. Add cron job for end-of-day commits
3. Train team on commit cadence levels
4. Generate first git activity metrics report

**Long-Term (Next Month):**
1. Integrate commit metrics with Airtable dashboard
2. Automate phase tagging on completion
3. Create commit quality linter (enforce message format)
4. Set up GitHub Actions for automated Airtable sync

---

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-10 | 1.0 | Initial git commit cadence strategy | Claude Code |
