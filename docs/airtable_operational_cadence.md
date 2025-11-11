# Airtable Operational Cadence

**Purpose:** Establish recurring processes to keep Airtable plan current, identify gaps, track issues, and ensure 100% alignment with actual project state.

**Created:** 2025-11-10
**Owner:** BQX ML Team

---

## Overview

This document defines the operational cadence for maintaining the BQX ML Airtable plan as a living, accurate representation of project status. It establishes regular gap assessments, issue tracking workflows, and automated update procedures.

### Core Principles

1. **Always Current:** Airtable reflects real-time project status
2. **Gap Visibility:** Issues and blockers are immediately documented
3. **Proactive Planning:** Regular assessments identify future needs
4. **Audit Trail:** All changes documented with rationale
5. **Automated Updates:** Scripts minimize manual overhead

---

## Cadence Schedule

### Daily Updates (End of Active Work)
**Frequency:** Every working day at end of development session
**Duration:** 5-10 minutes
**Owner:** Active developer

**Activities:**
1. Run progress update script for any in-progress stages
2. Mark completed tasks as "Complete" with actual duration
3. Create new tasks for discovered work
4. Log any blockers or issues encountered

**Scripts:**
- `scripts/airtable/daily_progress_update.py` (to be created)
- Automatically updates stage progress percentages
- Creates task entries for new work discovered
- Logs issue records for blockers

**Example:**
```bash
# End of day update
export AIRTABLE_API_KEY="..."
python3 scripts/airtable/daily_progress_update.py \
  --stage "1.5.4" \
  --progress 38.3 \
  --notes "BQX backfill progressing, 129/336 partitions complete"
```

---

### Weekly Gap Assessment (Every Monday)
**Frequency:** Weekly, Monday morning
**Duration:** 30-60 minutes
**Owner:** Technical lead

**Activities:**
1. **Completeness Check:**
   - Review all "In Progress" stages for accurate status
   - Identify any undocumented work completed last week
   - Verify all tasks have estimates and assignments

2. **Gap Identification:**
   - Compare actual work with planned work
   - Document any new technical debt discovered
   - Identify missing stages or tasks for upcoming work

3. **Issue Review:**
   - Review all open issues/blockers
   - Update status of issue remediation efforts
   - Create remediation tasks if needed

4. **Forecast Update:**
   - Adjust ETAs based on actual progress rates
   - Update phase completion dates
   - Flag any at-risk deliverables

**Deliverables:**
- Gap assessment report (stored in `docs/gap_assessments/YYYY-MM-DD_gap_assessment.md`)
- Updated Airtable with discovered gaps
- Issue remediation plan (if critical issues found)

**Scripts:**
- `scripts/airtable/weekly_gap_assessment.py` (to be created)
- Generates gap report by comparing Airtable to git commits
- Identifies stages marked "In Progress" for >2 weeks
- Flags tasks without estimates or assignments

**Template:** See Appendix A

---

### Biweekly Phase Review (Every Other Friday)
**Frequency:** Biweekly, Friday afternoon
**Duration:** 1-2 hours
**Owner:** Project stakeholders

**Activities:**
1. **Phase Completion Review:**
   - Review completed phases for lessons learned
   - Document actual vs. estimated effort variances
   - Archive phase documentation

2. **Upcoming Phase Planning:**
   - Break down next phase into detailed stages
   - Create all tasks for next phase with estimates
   - Identify dependencies and critical paths

3. **Risk Assessment:**
   - Review risks identified in gap assessments
   - Update risk mitigation strategies
   - Escalate critical risks to stakeholders

4. **Metrics Review:**
   - R² improvement trends
   - Storage utilization vs. estimates
   - Development velocity (tasks/week)

**Deliverables:**
- Phase completion report
- Next phase detailed plan in Airtable
- Updated risk register

**Scripts:**
- `scripts/airtable/phase_completion_report.py` (to be created)
- Generates metrics on completed phase
- Calculates variance between estimated and actual
- Exports to markdown report

---

### Monthly Architecture Review (First Monday of Month)
**Frequency:** Monthly
**Duration:** 2-3 hours
**Owner:** Architecture team

**Activities:**
1. **Technical Debt Assessment:**
   - Review accumulated technical debt
   - Prioritize debt items for remediation
   - Create dedicated stages/tasks for debt paydown

2. **Architecture Evolution:**
   - Assess if current architecture meets evolving needs
   - Identify refactoring opportunities
   - Plan major architectural changes as new phases

3. **Dependency Review:**
   - Review external dependencies (libraries, services)
   - Check for updates or security vulnerabilities
   - Plan upgrade paths if needed

4. **Documentation Audit:**
   - Verify all stages have documentation links
   - Check documentation completeness and accuracy
   - Identify documentation gaps

**Deliverables:**
- Technical debt register
- Architecture evolution roadmap
- Documentation completeness report

---

## Issue and Error Tracking

### Issue Classification

**Level 1: Blocker**
- Stops all progress on critical path
- Immediate attention required
- Escalated to all stakeholders

**Level 2: Major Issue**
- Impacts timeline or quality significantly
- Resolution required within 1 week
- Tracked in weekly gap assessment

**Level 3: Minor Issue**
- Workaround available
- Address in regular development flow
- Tracked but not blocking

**Level 4: Technical Debt**
- Non-urgent improvement
- Scheduled during dedicated debt paydown
- Tracked in technical debt register

### Issue Workflow

1. **Discovery → Immediate Documentation**
   - Create issue record in Airtable "Issues" table
   - Link to affected stages/tasks
   - Assign severity level and owner

2. **Triage → Remediation Planning**
   - Within 24 hours for Level 1-2
   - During weekly gap assessment for Level 3-4
   - Create remediation tasks with estimates

3. **Remediation → Verification**
   - Execute remediation tasks
   - Verify fix with tests/validation
   - Update issue status to "Resolved"

4. **Retrospective → Prevention**
   - Document root cause
   - Update processes to prevent recurrence
   - Share learnings with team

### Issue Airtable Schema

**Issues Table:**
- Issue ID (auto-generated)
- Title (text)
- Description (long text)
- Severity (Level 1-4)
- Status (Open, In Progress, Resolved, Closed)
- Affected Stages (link to Stages table)
- Root Cause (long text)
- Remediation Tasks (link to Tasks table)
- Discovered Date (date)
- Resolved Date (date)
- Owner (person)
- Prevention Actions (long text)

---

## Automation Scripts

### Script Architecture

All Airtable update scripts follow this pattern:

```python
#!/usr/bin/env python3
"""
Script Purpose: [Description]
Cadence: [Daily/Weekly/Biweekly/Monthly]
"""

import os
import requests
from datetime import datetime

# Configuration
BASE_ID = 'appR3PPnrNkVo48mO'
API_TOKEN = os.environ.get('AIRTABLE_API_KEY')

def main():
    """Main execution logic"""
    # 1. Gather data (git, database, logs)
    # 2. Compare with Airtable current state
    # 3. Identify gaps or updates needed
    # 4. Apply updates via Airtable API
    # 5. Generate report
    pass

if __name__ == '__main__':
    main()
```

### Planned Scripts

1. **`daily_progress_update.py`** ✅ EXISTS (partial)
   - Current: `update_stage_1_5_4_5_progress.py`
   - Enhancement needed: Generalize to any stage
   - Auto-detect progress from logs and git

2. **`weekly_gap_assessment.py`** ⚠️ TO CREATE
   - Compare git commits to Airtable tasks
   - Identify work done but not documented
   - Flag stale "In Progress" stages
   - Generate gap assessment report

3. **`phase_completion_report.py`** ⚠️ TO CREATE
   - Calculate phase metrics (duration, variance)
   - Export completed tasks with actuals
   - Generate lessons learned template

4. **`issue_tracker_sync.py`** ⚠️ TO CREATE
   - Sync between Airtable Issues table and code issues
   - Auto-create remediation tasks for Level 1-2
   - Generate issue status dashboard

5. **`documentation_audit.py`** ⚠️ TO CREATE
   - Check all stages have documentation links
   - Verify documentation files exist in repo
   - Generate completeness report

---

## Gap Assessment Template

### Weekly Gap Assessment Report

**Date:** YYYY-MM-DD
**Assessor:** [Name]
**Period Covered:** [Start Date] to [End Date]

#### 1. Completeness Check

**Stages Review:**
- [ ] All "In Progress" stages have accurate progress percentages
- [ ] All "Complete" stages marked correctly
- [ ] No stages in "In Progress" for >2 weeks without updates

**Findings:**
- [List any discrepancies found]

**Actions:**
- [List corrective actions taken]

#### 2. Gap Identification

**Undocumented Work:**
- [List git commits not reflected in Airtable]
- [List completed tasks not marked Complete]

**Missing Stages/Tasks:**
- [List planned work not yet in Airtable]
- [List new work discovered this week]

**Actions:**
- [List stages/tasks created]

#### 3. Issue Review

**Open Issues:**
| Issue ID | Title | Severity | Age (days) | Status |
|----------|-------|----------|------------|--------|
| ISS-001  | ...   | Level 2  | 5          | In Progress |

**Resolved Issues This Week:**
| Issue ID | Title | Resolution Time | Prevention Actions |
|----------|-------|-----------------|-------------------|
| ISS-005  | ...   | 3 days          | Added validation check |

**Actions:**
- [List new remediation tasks created]

#### 4. Forecast Update

**Progress Against Plan:**
- Phase 1.5: X% complete (planned: Y%)
- Current velocity: N tasks/week
- Projected completion: [Date] (planned: [Date])

**At-Risk Deliverables:**
- [List any deliverables at risk]
- [List mitigation plans]

**Actions:**
- [List ETA adjustments made]

#### 5. Recommendations

**Immediate Actions:**
1. [Action 1]
2. [Action 2]

**Process Improvements:**
1. [Improvement 1]
2. [Improvement 2]

---

## Key Performance Indicators

### Airtable Accuracy KPIs

1. **Completeness Rate:**
   - Formula: (Tasks in Airtable / Tasks in Git Commits) × 100%
   - Target: >95%
   - Measured: Weekly

2. **Staleness Rate:**
   - Formula: (Stages "In Progress" >2 weeks / Total Stages) × 100%
   - Target: <5%
   - Measured: Weekly

3. **Issue Resolution Time:**
   - Formula: Average days from Open → Resolved
   - Target: Level 1: <1 day, Level 2: <7 days
   - Measured: Weekly

4. **Documentation Coverage:**
   - Formula: (Stages with Docs / Total Stages) × 100%
   - Target: 100%
   - Measured: Monthly

5. **Forecast Accuracy:**
   - Formula: |Actual Completion - Estimated Completion| / Estimated
   - Target: <20% variance
   - Measured: Per phase

### Dashboard (Future Enhancement)

Create Airtable dashboard extension showing:
- Real-time completeness rate
- Stale stage alerts
- Open issues by severity
- Phase progress vs. plan
- Upcoming milestones

---

## Escalation Procedures

### When to Escalate

**Immediate Escalation (Level 1 Issues):**
- Production outage or data loss
- Security vulnerability discovered
- Critical dependency failure
- Blocker on critical path with no workaround

**Weekly Escalation (Level 2 Issues):**
- Timeline slippage >1 week on critical path
- Resource bottleneck affecting multiple stages
- Technical approach proving infeasible
- Budget overrun >20% on phase

### Escalation Channels

1. **Slack:** `#bqx-ml-critical` (Level 1 immediate)
2. **Email:** Project stakeholders (Level 2 within 24h)
3. **Weekly Standup:** Level 3 issues and status updates
4. **Monthly Review:** Strategic concerns and architecture changes

---

## Appendix A: Templates

### Gap Assessment Template Location
`docs/gap_assessments/template_gap_assessment.md`

### Issue Report Template Location
`docs/issues/template_issue_report.md`

### Phase Completion Report Template Location
`docs/phase_completions/template_phase_completion.md`

---

## Appendix B: Script Implementation Plan

### Priority 1 (Week 1)
- [x] `update_stage_1_5_4_5_progress.py` - Created, tested
- [ ] `daily_progress_update.py` - Generalize stage update script
- [ ] `weekly_gap_assessment.py` - Create gap detection logic

### Priority 2 (Week 2)
- [ ] Issues Airtable table schema creation
- [ ] `issue_tracker_sync.py` - Issue management automation
- [ ] Documentation for gap assessment process

### Priority 3 (Week 3-4)
- [ ] `phase_completion_report.py` - Metrics and reporting
- [ ] `documentation_audit.py` - Doc completeness checking
- [ ] Dashboard setup in Airtable

---

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-10 | 1.0 | Initial operational cadence framework | Claude Code |

---

## Next Steps

1. **Immediate (This Week):**
   - Create Issues table in Airtable base
   - Run `update_stage_1_5_4_5_progress.py` to update current state
   - Generate first gap assessment report

2. **Short-Term (Next 2 Weeks):**
   - Implement weekly gap assessment script
   - Document first set of discovered gaps
   - Create remediation tasks for any critical issues

3. **Long-Term (Next Month):**
   - Full automation of daily/weekly updates
   - Dashboard implementation
   - Training session on operational cadence

4. **Strategic (Next Quarter):**
   - Integrate with CI/CD pipeline for automatic updates
   - Machine learning for effort estimation improvement
   - Cross-project Airtable synchronization
