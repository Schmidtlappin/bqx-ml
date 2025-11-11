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
6. **Intelligence Integration:** Airtable links to intelligence files for institutional knowledge

### Intelligence Framework Integration

This operational cadence integrates with the **4-Layer ML Intelligence Framework** for institutional knowledge management:

- **L1: ML Foundation** - Project goals, metrics glossary, constraints
- **L2: Data Intelligence** - Schemas, feature catalog, data pipeline
- **L3: Decision History** - ADRs, lessons learned
- **L4: Operational State** - Current status, SageMaker config

See [Intelligence File Framework](intelligence_file_framework.md) for complete framework documentation.

### Key Documentation References

This operational cadence works in conjunction with several key project documents:

**Stage Completion Reports:**
- [BQX Backfill Completion Report](backfill_completion_report.md) - Stage 1.5.4.3 verification and production readiness
  - Data integrity verification (10.3M rows, 28 currency pairs)
  - Database optimization analysis (2,352 partitions, 100% indexed)
  - Production readiness assessment (all tests PASSED)
  - Updated 2025-11-11 with comprehensive verification results

**Process Documentation:**
- [Git Commit Cadence Strategy](git_commit_cadence.md) - Commit levels and automation procedures
- [Intelligence File Framework](intelligence_file_framework.md) - 4-layer ML knowledge management system

**Operational Intelligence Files** (to be created):
- `docs/ml_intelligence/operations/current_status.md` - Weekly project status snapshots
- `docs/ml_intelligence/decisions/architecture_decisions.md` - ADR log for major technical choices
- `docs/ml_intelligence/decisions/lessons_learned.md` - Bug root cause analysis and patterns

These documents should be referenced during daily updates, weekly assessments, and phase reviews to ensure comprehensive project tracking and knowledge capture.

---

## Cadence Schedule

### Daily Updates (End of Active Work)
**Frequency:** Every working day at end of development session
**Duration:** 5-10 minutes
**Owner:** Active developer

**Activities:**
1. **Git Commit:** Run end-of-day commit script (Level 5 commit)
2. Run progress update script for any in-progress stages
3. Mark completed tasks as "Complete" with actual duration
4. Create new tasks for discovered work
5. Log any blockers or issues encountered
6. **Intelligence Files:** Update `current_status.md` if significant progress/blockers
7. **Lessons Learned:** Create entry if bugs/issues encountered

**Scripts:**
- `scripts/git/end_of_day_commit.sh` - Automated daily git commit
- `scripts/airtable/daily_progress_update.py` (to be created)
  - Automatically updates stage progress percentages
  - Creates task entries for new work discovered
  - Logs issue records for blockers
- `scripts/intelligence/update_current_status.py` (to be created)
  - Updates `docs/ml_intelligence/operations/current_status.md`
  - Syncs progress from Airtable and git commits
  - Identifies blockers and upcoming milestones

**Example:**
```bash
# End of day git commit + Airtable update
/home/ubuntu/bqx-ml/scripts/git/end_of_day_commit.sh

# Then update Airtable
export AIRTABLE_API_KEY="..."
python3 scripts/airtable/daily_progress_update.py \
  --stage "1.5.4" \
  --progress 38.3 \
  --notes "BQX backfill progressing, 129/336 partitions complete"

# Update intelligence files
python3 scripts/intelligence/update_current_status.py
```

**Intelligence File Updates (Daily):**
- **Read:** `docs/ml_intelligence/operations/current_status.md` (morning orientation)
- **Update:** If progress >10% or blocker encountered
- **Create:** Lesson learned entry for any bug (format: LL-YYYYMMDD-##)

**Git Integration:**
See [Git Commit Cadence Strategy](git_commit_cadence.md) for detailed commit levels and procedures.

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

5. **Intelligence File Review:**
   - Review `lessons_learned.md` entries from past week
   - Update `current_status.md` with new week's milestones
   - Verify `feature_catalog.md` includes all new features
   - Check all ADRs still valid and linked in Airtable

**Deliverables:**
- Gap assessment report (stored in `docs/gap_assessments/YYYY-MM-DD_gap_assessment.md`)
- Updated Airtable with discovered gaps
- Issue remediation plan (if critical issues found)

**Scripts:**
- `scripts/airtable/weekly_gap_assessment.py` (to be created)
  - Generates gap report by comparing Airtable to git commits
  - Identifies stages marked "In Progress" for >2 weeks
  - Flags tasks without estimates or assignments
- `scripts/intelligence/weekly_intelligence_audit.py` (to be created)
  - Checks `current_status.md` updated in past 7 days
  - Verifies all lessons learned from past week documented
  - Validates feature catalog completeness
  - Generates intelligence freshness report

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

5. **Intelligence File Consolidation:**
   - Compile all lessons learned into phase retrospective
   - Create phase completion ADR if major decisions made
   - Update `project_goals.md` if success metrics changed
   - Archive phase-specific intelligence files

**Deliverables:**
- Phase completion report
- Next phase detailed plan in Airtable
- Updated risk register
- **Intelligence Deliverables:**
  - Phase lessons learned summary in `lessons_learned.md`
  - Phase completion ADR (if applicable)
  - Updated `metrics_glossary.md` with new metrics
  - Archived intelligence files (phase-specific context)

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

5. **Intelligence Framework Review:**
   - Audit all 10 intelligence files for freshness
   - Review ADR validity (are past decisions still correct?)
   - Update `schema_documentation.md` with any schema changes
   - Validate `feature_catalog.md` completeness
   - Review `data_pipeline.md` accuracy
   - Update `sagemaker_config.md` with latest configs

**Deliverables:**
- Technical debt register
- Architecture evolution roadmap
- Documentation completeness report
- **Intelligence Deliverables:**
  - Intelligence freshness report (all 10 files)
  - ADR review summary (which are still valid, which superseded)
  - Schema documentation update (if changes occurred)
  - Updated constraints document (if resource limits changed)

---

## Intelligence File Management

### 4-Layer ML Intelligence Framework

**Framework Purpose:** Systematic institutional knowledge capture for human ML team

**Layers:**
- **L1: ML Foundation** (3 files) - Project goals, metrics, constraints
- **L2: Data Intelligence** (3 files) - Schemas, features, pipeline
- **L3: Decision History** (2 files) - ADRs, lessons learned
- **L4: Operational State** (2 files) - Current status, SageMaker

**Total:** 10 intelligence files (manageable for human team)

See [Intelligence File Framework](intelligence_file_framework.md) for detailed templates and usage patterns.

### Intelligence File Types and Update Cadence

#### L1: ML Foundation (Updated Quarterly or When Requirements Change)

**1. `docs/ml_intelligence/foundation/project_goals.md`**
- **Purpose:** Define success metrics, evaluation criteria, target R²
- **Update Trigger:** Quarterly review or stakeholder requirement change
- **Owner:** Project Lead
- **Linked in Airtable:** Project phases table (Notes field)

**2. `docs/ml_intelligence/foundation/metrics_glossary.md`**
- **Purpose:** Define all metrics (R², rate_index, BQX, REG features)
- **Update Trigger:** When new metric introduced (immediate)
- **Owner:** Technical Lead
- **Linked in Airtable:** Feature engineering stages (Documentation field)

**3. `docs/ml_intelligence/foundation/constraints.md`**
- **Purpose:** Resource limits, technical constraints, quality requirements
- **Update Trigger:** Monthly or when constraint changes
- **Owner:** Project Lead
- **Linked in Airtable:** Project phases table (Constraints field)

#### L2: Data Intelligence (Updated After Schema/Feature Changes)

**4. `docs/ml_intelligence/data/schema_documentation.md`**
- **Purpose:** Database schema, indexes, partitions with rationale
- **Update Trigger:** After every schema change (immediate)
- **Owner:** Database Lead
- **Linked in Airtable:** Database stages (Documentation field)

**5. `docs/ml_intelligence/data/feature_catalog.md`**
- **Purpose:** Every feature definition, formula, expected range
- **Update Trigger:** When new feature created (immediate)
- **Owner:** ML Engineer
- **Linked in Airtable:** Feature engineering stages (Features field)

**6. `docs/ml_intelligence/data/data_pipeline.md`**
- **Purpose:** Data flow from source → features → model
- **Update Trigger:** After pipeline architecture changes
- **Owner:** Technical Lead
- **Linked in Airtable:** Pipeline stages (Documentation field)

#### L3: Decision History (Updated When Decisions Made or Issues Occur)

**7. `docs/ml_intelligence/decisions/architecture_decisions.md`**
- **Purpose:** ADRs for significant choices (rate_index, partitioning, etc.)
- **Update Trigger:** After every major decision (immediate)
- **Owner:** System Architect
- **Linked in Airtable:** All stages (Reference ADR-### in Notes)

**8. `docs/ml_intelligence/decisions/lessons_learned.md`**
- **Purpose:** Bug root causes, what worked/didn't, patterns
- **Update Trigger:** After every bug or significant issue (immediate)
- **Owner:** Team (whoever encountered issue)
- **Linked in Airtable:** Issues table (Lesson Learned ID field)

#### L4: Operational State (Updated Weekly)

**9. `docs/ml_intelligence/operations/current_status.md`**
- **Purpose:** Current phase, blockers, milestones, resource status
- **Update Trigger:** Weekly (Monday) or when significant change
- **Owner:** Project Lead
- **Linked in Airtable:** Project dashboard (embedded link)

**10. `docs/ml_intelligence/operations/sagemaker_config.md`**
- **Purpose:** SageMaker deployment and training configurations
- **Update Trigger:** When SageMaker configs change
- **Owner:** ML Ops
- **Linked in Airtable:** Deployment stages (Configuration field)

### Airtable Schema Updates for Intelligence Integration

**Stages Table - Add Fields:**
- **Intelligence Files** (Multiple Links) - Link to intelligence file records
- **ADR References** (Text) - e.g., "ADR-001, ADR-005"
- **Lesson Learned References** (Text) - e.g., "LL-20251111-01"

**Tasks Table - Add Fields:**
- **Lesson Learned** (Link) - Link to specific lesson if task is remediation

**Issues Table - Add Fields:**
- **Lesson Learned ID** (Formula) - Auto-generate LL-YYYYMMDD-## format
- **Intelligence File Updated** (Checkbox) - Mark when lesson documented

**New Table: Intelligence Files**
- **File Name** (Text, Primary)
- **Layer** (Single Select: L1, L2, L3, L4)
- **Purpose** (Long Text)
- **Last Updated** (Date)
- **Update Frequency** (Single Select: Daily, Weekly, Per Change, Monthly, Quarterly)
- **Owner** (Person)
- **File Path** (Text) - docs/ml_intelligence/...
- **Freshness Status** (Formula) - Overdue if past update frequency
- **Linked Stages** (Multiple Links) - Stages referencing this file

### Intelligence File Creation Workflow

**When Creating New Intelligence File:**

1. **Create File:** Use template from intelligence_file_framework.md
2. **Populate Content:** Fill in relevant sections
3. **Create Airtable Record:**
   ```python
   # Example: scripts/intelligence/create_intelligence_record.py
   create_intelligence_file_record(
       file_name="architecture_decisions.md",
       layer="L3",
       purpose="Document ADRs for major technical decisions",
       update_frequency="Per Change",
       owner="System Architect",
       file_path="docs/ml_intelligence/decisions/architecture_decisions.md"
   )
   ```
4. **Link to Relevant Stages:** In Airtable, link intelligence file to stages
5. **Reference in Documentation:** Add link in stage notes

**When Updating Existing Intelligence File:**

1. **Update File:** Edit content with new information
2. **Update Airtable Record:** Automatic via script or manual
3. **Update Stage Links:** If new stages should reference this file
4. **Git Commit:** Reference intelligence file in commit message

### Intelligence File Automation Scripts

#### 1. `scripts/intelligence/create_intelligence_record.py`
**Purpose:** Create Airtable record when new intelligence file created
**Cadence:** On-demand (when new file created)

```python
#!/usr/bin/env python3
"""Create Airtable record for intelligence file"""

def create_intelligence_file_record(file_name, layer, purpose,
                                     update_frequency, owner, file_path):
    """
    Create Intelligence Files table record

    Args:
        file_name: Name of file (e.g., "project_goals.md")
        layer: L1, L2, L3, or L4
        purpose: Brief description
        update_frequency: Daily, Weekly, Per Change, Monthly, Quarterly
        owner: Person responsible
        file_path: Full path to file
    """
    # Implementation
    pass
```

#### 2. `scripts/intelligence/update_current_status.py`
**Purpose:** Auto-update current_status.md from Airtable and git
**Cadence:** Daily (end of day)

```python
#!/usr/bin/env python3
"""Update current_status.md with latest project state"""

def update_current_status():
    """
    Automatically update operational state intelligence file

    Gathers:
    - Current phase from Airtable
    - Active stages and progress from Airtable
    - Blockers from Issues table
    - Resource status from Aurora/git
    - Recent changes from git log
    """
    # Implementation
    pass
```

#### 3. `scripts/intelligence/weekly_intelligence_audit.py`
**Purpose:** Check intelligence file freshness and completeness
**Cadence:** Weekly (Monday morning)

```python
#!/usr/bin/env python3
"""Audit intelligence files for freshness and completeness"""

def audit_intelligence_files():
    """
    Check all 10 intelligence files:
    - Last modified date vs update frequency
    - File exists and not empty
    - Linked properly in Airtable
    - Cross-references valid

    Output:
    - Freshness report (which files stale)
    - Completeness score
    - Action items for updates
    """
    # Implementation
    pass
```

#### 4. `scripts/intelligence/extract_lesson_learned.py`
**Purpose:** Generate lesson learned entry from issue
**Cadence:** On-demand (when bug resolved)

```python
#!/usr/bin/env python3
"""Generate lesson learned entry from Airtable issue"""

def extract_lesson_learned(issue_id):
    """
    Create lesson learned entry from issue

    Inputs:
    - Airtable issue record
    - Root cause analysis
    - Resolution approach

    Outputs:
    - Formatted lesson learned entry
    - Appended to lessons_learned.md
    - Issue record updated with LL ID
    """
    # Implementation
    pass
```

#### 5. `scripts/intelligence/link_adr_to_stages.py`
**Purpose:** Link ADR to relevant Airtable stages
**Cadence:** When ADR created

```python
#!/usr/bin/env python3
"""Link ADR to affected stages in Airtable"""

def link_adr_to_stages(adr_id, stage_ids):
    """
    Update stages with ADR reference

    Args:
        adr_id: e.g., "ADR-001"
        stage_ids: List of stage record IDs

    Updates:
        - Stage "ADR References" field
        - Stage "Notes" with ADR context
    """
    # Implementation
    pass
```

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

### Intelligence File KPIs

6. **Intelligence File Freshness:**
   - Formula: (Files updated per schedule / Total files) × 100%
   - Target: >90%
   - Measured: Weekly

7. **Lesson Learned Capture Rate:**
   - Formula: (Bugs with LL entry / Total bugs resolved) × 100%
   - Target: 100% for Level 1-2 issues
   - Measured: Weekly

8. **ADR Coverage:**
   - Formula: (Major decisions with ADR / Total major decisions) × 100%
   - Target: 100%
   - Measured: Per phase

9. **Intelligence File Usage:**
   - Formula: (Git commits referencing intelligence files / Total commits) × 100%
   - Target: >50%
   - Measured: Weekly

10. **Feature Catalog Completeness:**
    - Formula: (Features documented / Features in database) × 100%
    - Target: 100%
    - Measured: Weekly

### Dashboard (Future Enhancement)

Create Airtable dashboard extension showing:
- Real-time completeness rate
- Stale stage alerts
- Open issues by severity
- Phase progress vs. plan
- Upcoming milestones
- **Intelligence file freshness status**
- **Lesson learned capture rate**
- **ADR reference coverage**
- **Feature catalog completeness**

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
- [ ] **`scripts/intelligence/update_current_status.py`** - Auto-update operational state
- [ ] **Intelligence Files table** - Create in Airtable

### Priority 2 (Week 2)
- [ ] Issues Airtable table schema creation
- [ ] `issue_tracker_sync.py` - Issue management automation
- [ ] Documentation for gap assessment process
- [ ] **`scripts/intelligence/weekly_intelligence_audit.py`** - Freshness checking
- [ ] **`scripts/intelligence/extract_lesson_learned.py`** - LL automation

### Priority 3 (Week 3-4)
- [ ] `phase_completion_report.py` - Metrics and reporting
- [ ] `documentation_audit.py` - Doc completeness checking
- [ ] Dashboard setup in Airtable
- [ ] **`scripts/intelligence/create_intelligence_record.py`** - Airtable integration
- [ ] **`scripts/intelligence/link_adr_to_stages.py`** - ADR linking

---

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-11 | 2.0 | Integrated 4-layer ML intelligence framework | Claude Code |
| 2025-11-10 | 1.0 | Initial operational cadence framework | Claude Code |

---

## Next Steps

1. **Immediate (This Week):**
   - Create Issues table in Airtable base
   - **Create Intelligence Files table in Airtable**
   - **Create `docs/ml_intelligence/` directory structure**
   - **Create initial intelligence files:**
     - `foundation/project_goals.md`
     - `foundation/metrics_glossary.md`
     - `operations/current_status.md`
   - Run `update_stage_1_5_4_5_progress.py` to update current state
   - Generate first gap assessment report
   - **Create first lesson learned:** LL-20251111-01 (PostgreSQL Decimal bug)
   - **Create first ADR:** ADR-001 (Rate Index Architecture)

2. **Short-Term (Next 2 Weeks):**
   - Implement weekly gap assessment script
   - **Implement weekly intelligence audit script**
   - Document first set of discovered gaps
   - Create remediation tasks for any critical issues
   - **Populate all L1 and L2 intelligence files**
   - **Add ADR/LL reference fields to Airtable Stages table**
   - **Create lesson learned extraction automation**

3. **Long-Term (Next Month):**
   - Full automation of daily/weekly updates
   - Dashboard implementation
   - Training session on operational cadence
   - **Full team adoption of intelligence framework**
   - **Intelligence file automation operational**
   - **Monthly intelligence audit process established**

4. **Strategic (Next Quarter):**
   - Integrate with CI/CD pipeline for automatic updates
   - Machine learning for effort estimation improvement
   - Cross-project Airtable synchronization
   - **95%+ intelligence file freshness achieved**
   - **Measurable reduction in repeat issues (60% target)**
   - **Faster decision-making cycles (30% improvement)**
