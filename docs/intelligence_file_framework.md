# BQX ML Intelligence File Framework

**Created:** 2025-11-11
**Based on:** Robkei-Ring 7-Layer Cognitive Framework
**Purpose:** Establish systematic intelligence capture and institutional knowledge management for BQX ML project

---

## Executive Summary

This framework defines a **7-Layer Cognitive Intelligence System** adapted from the Robkei-Ring multi-agent autonomous system. The framework ensures institutional knowledge is systematically captured, maintained, and accessible throughout the project lifecycle.

**Core Principle:** Intelligence files are living documents that evolve through experience, capture the "WHY" behind decisions, and ensure knowledge persistence beyond individual contributors.

**Integration:** This framework integrates with [Airtable Operational Cadence](airtable_operational_cadence.md) and [Git Commit Strategy](git_commit_cadence.md) to provide complete project knowledge management.

---

## Overview: 7-Layer Cognitive Framework

The BQX ML intelligence system is organized into **8 layers** (L0-L7), each serving a specific cognitive function:

```
L7: REFLECTION     - Meta-cognition, learning from experience, adaptation
L6: CONTEXT        - Situational awareness, project state, environmental factors
L5: SEMANTICS      - Meaning disambiguation, terminology consistency
L4: PRAGMATICS     - Context-driven interpretation, goal alignment
L3: AGENCY         - Decision authority, autonomy levels, accountability
L2: ONTOLOGY       - Data models, relationships, system structure
L1: SYNTAX         - Glossary, definitions, organizational vocabulary
L0: FOUNDATION     - Core principles, values, mandates
```

**Hierarchical Intelligence Access:**

Additionally, intelligence is organized by **access level** (separate from cognitive layers):

- **L0 - Project Foundation:** Core project goals, requirements, constraints (universal access)
- **L1 - Global Knowledge:** Project-wide intelligence (all team members)
- **L2 - Phase-Specific Knowledge:** Current phase context and patterns
- **L3 - Task-Specific Knowledge:** Individual task documentation
- **L4 - Personal Knowledge:** Individual contributor notes and learnings

---

## L0: Foundation Intelligence

**Purpose:** Immutable project foundation - core values, goals, and mandates

### Files

#### 1. `intelligence/L0-FOUNDATION/project_charter.md`

**Content:**
- Project vision and strategic objectives
- Success criteria and key results
- Stakeholder requirements and expectations
- Non-negotiable constraints
- Core principles guiding all decisions

**Update Frequency:** Rarely (only for fundamental scope changes)
**Owner:** Project Lead

**Template:**
```markdown
# BQX ML Project Charter

## Vision
[3-5 sentence vision statement]

## Strategic Objectives
1. [Objective 1]: [Success criteria]
2. [Objective 2]: [Success criteria]

## Key Results
| Result | Target | Measurement | Timeline |
|--------|--------|-------------|----------|
| ...    | ...    | ...         | ...      |

## Stakeholder Requirements
- [Stakeholder 1]: [Requirements]
- [Stakeholder 2]: [Requirements]

## Non-Negotiable Constraints
1. [Constraint 1]: [Rationale]
2. [Constraint 2]: [Rationale]

## Core Principles
1. **[Principle 1]**: [Description and implications]
2. **[Principle 2]**: [Description and implications]
```

#### 2. `intelligence/L0-FOUNDATION/user_mandates.md`

**Content:**
- User values and priorities
- Resource constraints (budget, time, infrastructure)
- Quality standards and expectations
- Risk tolerance levels
- Escalation triggers

**Update Frequency:** Quarterly or when priorities shift
**Owner:** Project Lead

**Template:**
```markdown
# User Mandates

## UM-001: [Mandate Category]
**Priority:** [Critical | High | Medium]
**Scope:** [What this applies to]
**Mandate:** [Clear statement]
**Rationale:** [Why this matters]
**Implications:** [How this affects decisions]
**Validation:** [How compliance is measured]

[Repeat for each mandate]
```

---

## L1: Syntax Intelligence

**Purpose:** Shared vocabulary and definitions for consistent communication

### Files

#### 1. `intelligence/L1-SYNTAX/glossary.md`

**Content:**
- Project-specific terminology
- Acronyms and abbreviations
- Technical terms with precise definitions
- Cross-references to related concepts

**Update Frequency:** Bi-weekly (as new terms emerge)
**Owner:** Team (collaborative)

**Template:**
```markdown
# BQX ML Glossary

## A

**[Term]**
- **Definition:** [Clear, precise definition]
- **Context:** [When/where used]
- **Example:** [Usage example]
- **Related Terms:** [Cross-references]
- **Added:** [Date]

[Alphabetical listing...]
```

#### 2. `intelligence/L1-SYNTAX/metrics_definitions.md`

**Content:**
- Performance metrics and how they're calculated
- Quality indicators and thresholds
- Success criteria definitions
- Measurement methodologies

**Update Frequency:** Monthly
**Owner:** Technical Lead

**Template:**
```markdown
# Metrics Definitions

## [Metric Name]
**Category:** [Performance | Quality | Efficiency | Cost]
**Formula:** [Mathematical definition]
**Units:** [Unit of measurement]
**Calculation Method:** [Step-by-step]
**Data Sources:** [Where data comes from]
**Interpretation:**
- **Excellent:** [Threshold and meaning]
- **Acceptable:** [Threshold and meaning]
- **Concerning:** [Threshold and escalation]
**Historical Baseline:** [Context from past data]
**Updated:** [Date]
```

---

## L2: Ontology Intelligence

**Purpose:** System structure, data models, and relationships

### Files

#### 1. `intelligence/L2-ONTOLOGY/data_models.md`

**Content:**
- Database schema design and rationale
- Entity relationships and cardinality
- Indexing strategy and performance implications
- Partitioning scheme and benefits
- Schema evolution history

**Update Frequency:** After every schema change
**Owner:** Database Lead

**Template:**
```markdown
# BQX ML Data Models

## [Table/Entity Name]

### Purpose
[What this entity represents and why it exists]

### Schema
| Field | Type | Constraints | Purpose | Rationale |
|-------|------|-------------|---------|-----------|
| ...   | ...  | ...         | ...     | ...       |

### Indexes
| Index Name | Columns | Type | Rationale | Performance Impact |
|------------|---------|------|-----------|-------------------|
| ...        | ...     | ...  | ...       | ...               |

### Partitioning
**Strategy:** [RANGE | HASH | LIST]
**Key:** [Partition column]
**Granularity:** [e.g., Monthly]
**Rationale:** [Why this approach]
**Benefits:** [Performance gains, maintenance advantages]

### Relationships
- **[Related Entity]**: [Relationship type] - [Rationale]

### Evolution History
| Date | Change | Rationale | Migration Impact |
|------|--------|-----------|------------------|
| ...  | ...    | ...       | ...              |
```

#### 2. `intelligence/L2-ONTOLOGY/system_architecture.md`

**Content:**
- System components and their responsibilities
- Integration points and data flows
- Technology stack decisions and rationale
- Scalability considerations
- Infrastructure topology

**Update Frequency:** After major architecture changes
**Owner:** System Architect

**Template:**
```markdown
# System Architecture

## Component: [Name]

### Responsibility
[What this component does]

### Technology Choice
**Selected:** [Technology/Framework]
**Alternatives Considered:** [Other options]
**Decision Rationale:**
- **Advantage 1:** [Explanation]
- **Advantage 2:** [Explanation]
- **Trade-off:** [What we sacrificed and why acceptable]

### Integration Points
| Upstream System | Interface | Data Format | Reliability | Rationale |
|----------------|-----------|-------------|-------------|-----------|
| ...            | ...       | ...         | ...         | ...       |

### Scalability
**Current Capacity:** [Metrics]
**Scaling Triggers:** [When to scale]
**Scaling Strategy:** [Horizontal | Vertical | Hybrid]
**Cost Model:** [How costs scale]

### Failure Modes
| Failure Type | Impact | Detection | Recovery | Prevention |
|--------------|--------|-----------|----------|------------|
| ...          | ...    | ...       | ...      | ...        |
```

---

## L3: Agency Intelligence

**Purpose:** Decision authority, autonomy, and accountability

### Files

#### 1. `intelligence/L3-AGENCY/decision_authority_matrix.md`

**Content:**
- Who can make which decisions autonomously
- Approval requirements for different decision types
- Escalation paths and criteria
- Decision documentation requirements

**Update Frequency:** When team structure changes
**Owner:** Project Lead

**Template:**
```markdown
# Decision Authority Matrix

## Decision Type: [Category]

### Level 1: Autonomous
**Who:** [Roles that can decide independently]
**Scope:** [What decisions fall in this category]
**Documentation Required:** [What must be recorded]
**Example Decisions:**
- [Example 1]
- [Example 2]

### Level 2: Consultation Required
**Who Can Decide:** [Final decision maker]
**Must Consult:** [Who must be consulted]
**Consultation Method:** [How consultation happens]
**Timeline:** [Response time expected]

### Level 3: Approval Required
**Who Must Approve:** [Approval authority]
**Approval Criteria:** [What's evaluated]
**Escalation Path:** [If approval denied]

### Level 4: Escalation to Stakeholders
**Trigger Conditions:**
- [Condition 1]: [Rationale]
- [Condition 2]: [Rationale]
**Escalation Process:** [Steps to follow]
```

#### 2. `intelligence/L3-AGENCY/responsibility_assignment.md`

**Content:**
- Component ownership (who is responsible)
- Backup assignments for continuity
- Knowledge transfer requirements
- Handoff protocols

**Update Frequency:** Monthly or when roles change
**Owner:** Project Lead

---

## L4: Pragmatics Intelligence

**Purpose:** Context-driven interpretation and goal alignment

### Files

#### 1. `intelligence/L4-PRAGMATICS/goal_alignment.md`

**Content:**
- How technical decisions align with business goals
- Trade-off evaluation framework
- Priority resolution when goals conflict
- Context-specific interpretation rules

**Update Frequency:** Per project phase
**Owner:** Project Lead

**Template:**
```markdown
# Goal Alignment Framework

## Current Phase: [Phase Name]

### Primary Goals
1. **[Goal 1]**: [Description]
   - **Business Value:** [Why this matters]
   - **Technical Expression:** [How this manifests in code/architecture]
   - **Success Metric:** [How we measure]
   - **Trade-offs Accepted:** [What we sacrifice for this]

### Goal Conflict Resolution
**Scenario:** [Goal A] vs [Goal B]
**Context:** [When this conflict arises]
**Resolution Rule:** [Which takes priority and why]
**Example:** [Concrete case]

### Phase-Specific Interpretation
**Term:** [Ambiguous term]
**Standard Meaning:** [General definition]
**Phase-Specific Meaning:** [How we interpret in this phase]
**Rationale:** [Why this interpretation serves phase goals]
```

#### 2. `intelligence/L4-PRAGMATICS/context_patterns.md`

**Content:**
- Common contexts and how they affect decisions
- Pattern library of situational responses
- Crisis mode vs standard operations differences
- Deadline pressure interpretation rules

**Update Frequency:** Monthly
**Owner:** Technical Lead

---

## L5: Semantics Intelligence

**Purpose:** Meaning disambiguation and terminology consistency

### Files

#### 1. `intelligence/L5-SEMANTICS/semantic_rules.md`

**Content:**
- Disambiguation rules for ambiguous terms
- Domain-specific vocabulary standards
- Cross-component semantic alignment
- Hierarchical semantic resolution (project > global > domain)

**Update Frequency:** Monthly or when conflicts arise
**Owner:** Technical Lead

**Template:**
```markdown
# Semantic Disambiguation Rules

## Term: [Ambiguous Term]

### Disambiguation Matrix

| Context | Interpretation | Success Criteria | Example |
|---------|----------------|------------------|---------|
| **Database Design** | [Meaning in this context] | [How to verify correct interpretation] | [Concrete example] |
| **ML Pipeline** | [Meaning in this context] | [How to verify] | [Example] |
| **API Design** | [Meaning in this context] | [How to verify] | [Example] |

### Hierarchical Resolution
**Global Standard:** [Organization-wide meaning]
**Project Specialization:** [BQX ML specific meaning]
**Domain Expertise:** [Expert interpretation per domain]

**Conflict Resolution:**
1. User mandate alignment (highest priority)
2. Project goals alignment
3. Domain expertise
4. Historical precedent

### Evolution History
| Date | Previous Meaning | Updated Meaning | Trigger | Rationale |
|------|------------------|-----------------|---------|-----------|
| ...  | ...              | ...             | ...     | ...       |
```

#### 2. `intelligence/L5-SEMANTICS/terminology_consistency.md`

**Content:**
- Preferred terms and deprecated alternatives
- Cross-file terminology alignment
- API naming conventions
- Documentation language standards

**Update Frequency:** Bi-weekly
**Owner:** Technical Writer / Team Lead

---

## L6: Context Intelligence

**Purpose:** Situational awareness, project state, environmental factors

### Files

#### 1. `intelligence/L6-CONTEXT/project_state.md`

**Content:**
- Current project phase and objectives
- Active constraints and their implications
- Recent changes affecting decisions
- Upcoming milestones and their requirements
- Team capacity and resource availability

**Update Frequency:** Weekly
**Owner:** Project Lead

**Template:**
```markdown
# Project State Context

**Updated:** [Date]
**Phase:** [Current phase]
**Week:** [Week number in project]

## Current State Summary
[2-3 paragraph executive summary of where we are]

## Active Constraints
| Constraint | Type | Impact | Mitigation | Expiration |
|------------|------|--------|------------|------------|
| [e.g., "Database migration freeze"] | [Technical | Resource | Timeline] | [How this affects decisions] | [How we're addressing] | [When constraint lifts] |

## Recent Changes (Last 7 Days)
1. **[Change]**: [What happened] → [How this affects ongoing work]
2. **[Change]**: [What happened] → [Impact]

## Upcoming Milestones (Next 14 Days)
| Date | Milestone | Requirements | Risk Level | Owner |
|------|-----------|--------------|------------|-------|
| ...  | ...       | ...          | ...        | ...   |

## Team Capacity
**Available Hours This Week:** [Number]
**Committed Hours:** [Number]
**Buffer:** [Percentage]
**Blocking Issues:** [List]

## Decision Context
**Current priorities favor:** [Performance | Cost | Speed | Quality | Reliability]
**Rationale:** [Why these priorities right now]
**Expected Duration:** [How long this context lasts]
```

#### 2. `intelligence/L6-CONTEXT/environmental_factors.md`

**Content:**
- External dependencies and their status
- Infrastructure limitations and workarounds
- Third-party service constraints
- Seasonal or temporal factors

**Update Frequency:** Weekly
**Owner:** Technical Lead

---

## L7: Reflection Intelligence

**Purpose:** Meta-cognition, learning from experience, continuous adaptation

### Files

#### 1. `intelligence/L7-REFLECTION/lessons_learned.md`

**Content:**
- What worked well and why
- What didn't work and why
- Pattern recognition across failures
- Proactive improvements based on experience
- Root cause analysis of issues

**Update Frequency:** After each major milestone or issue
**Owner:** Team (collaborative)

**Template:**
```markdown
# Lessons Learned

## Lesson ID: LL-[YYYYMMDD]-[SEQ]
**Date:** [When learned]
**Phase:** [Project phase]
**Category:** [Technical | Process | Communication | Estimation]
**Trigger:** [What event prompted this lesson]

### What Happened
[Objective description of the situation]

### What Worked Well
- **[Aspect 1]**: [Why this was effective]
  - **Root Cause of Success:** [Underlying reason]
  - **Replication Strategy:** [How to repeat this success]

### What Didn't Work
- **[Aspect 1]**: [Why this failed]
  - **Root Cause:** [Underlying reason - go deep]
  - **Early Warning Signs:** [What we should have caught earlier]

### Pattern Recognition
**Similar Past Incidents:**
- [Incident 1]: [Date] - [Similarity]
- [Incident 2]: [Date] - [Similarity]

**Emerging Pattern:** [If this is part of a larger pattern]

### Changes Implemented
1. **[Change 1]**: [What we changed]
   - **Rationale:** [Why this addresses root cause]
   - **Validation:** [How we'll know this works]
   - **Rollback Plan:** [If this change causes problems]

### Proactive Improvements
**Future Scenarios This Prepares Us For:**
- [Scenario 1]: [How we're now better prepared]
- [Scenario 2]: [Prevention capability gained]

### Knowledge Distribution
- **Team Communication:** [How team was informed]
- **Documentation Updated:** [Links to updated docs]
- **Process Changes:** [Links to updated procedures]
```

#### 2. `intelligence/L7-REFLECTION/architecture_decisions.md`

**Content:**
- Architecture Decision Records (ADRs)
- Why we chose approach A over B
- Trade-offs accepted and rationale
- Future review triggers

**Update Frequency:** After every significant architecture decision
**Owner:** System Architect

**Template:**
```markdown
# Architecture Decision Record

## ADR-[NUMBER]: [Short Title]

**Date:** [Date]
**Status:** [Proposed | Accepted | Deprecated | Superseded]
**Deciders:** [Names]
**Related Decisions:** [Links to related ADRs]

### Context
[Describe the forces at play: technical, political, social, project]

**Problem Statement:**
[What problem are we solving?]

**Constraints:**
- [Constraint 1]
- [Constraint 2]

### Decision Drivers
1. **[Driver 1]**: [Importance: High | Medium | Low]
2. **[Driver 2]**: [Importance]

### Options Considered

#### Option 1: [Name]
**Description:** [How this works]
**Pros:**
- [Pro 1]
- [Pro 2]
**Cons:**
- [Con 1]
- [Con 2]
**Estimated Cost/Effort:** [Quantified if possible]

[Repeat for each option]

### Decision
**Chosen:** [Option X]

**Rationale:**
[Why this option best satisfies decision drivers]

**Trade-offs Accepted:**
- **Sacrificed:** [What we're giving up]
- **Why Acceptable:** [Justification]

### Consequences

**Positive:**
- [Benefit 1]
- [Benefit 2]

**Negative:**
- [Drawback 1]: [How we'll mitigate]
- [Drawback 2]: [Mitigation strategy]

**Risks:**
| Risk | Likelihood | Impact | Mitigation | Trigger for Review |
|------|------------|--------|------------|-------------------|
| ...  | ...        | ...    | ...        | ...               |

### Validation
**How We'll Know This Was Right:**
- [Metric 1]: [Target]
- [Metric 2]: [Target]

**Review Trigger:**
- [Condition 1 that would make us reconsider]
- [Condition 2]

**Review Date:** [Date to revisit this decision]

### Implementation Notes
[Technical details, gotchas, things to watch for]
```

#### 3. `intelligence/L7-REFLECTION/improvement_log.md`

**Content:**
- Continuous improvement initiatives
- Process refinements
- Automation opportunities identified
- Technical debt remediation tracking

**Update Frequency:** Weekly
**Owner:** Technical Lead

**Template:**
```markdown
# Improvement Log

## Improvement ID: IMP-[YYYYMMDD]-[SEQ]
**Date Identified:** [Date]
**Category:** [Performance | Code Quality | Process | Tooling | Documentation]
**Priority:** [Critical | High | Medium | Low]
**Status:** [Identified | Planned | In Progress | Completed | Deferred]

### Current State
**Problem/Inefficiency:** [What's suboptimal]
**Impact:** [How this affects team/project]
**Quantified Cost:** [Time/money/quality impact]

### Proposed Improvement
**Description:** [What to change]
**Expected Benefit:** [Improvement anticipated]
**Estimated Effort:** [Hours/days]
**ROI:** [Benefit/Effort ratio]

### Implementation Plan
1. **[Step 1]**: [Duration: X hours]
2. **[Step 2]**: [Duration: Y hours]

**Dependencies:** [What needs to happen first]
**Risk:** [What could go wrong]

### Success Criteria
- [Measurable outcome 1]
- [Measurable outcome 2]

### Post-Implementation Review
**Date Completed:** [Date]
**Actual Benefit:** [What we gained]
**Lessons:** [What we learned]
**Further Improvements:** [What else this enables]
```

---

## Integration with Project Workflows

### Daily Workflow Integration

**Morning:** Read `L6-CONTEXT/project_state.md` to understand current situation

**During Work:**
- Consult `L1-SYNTAX/glossary.md` and `L5-SEMANTICS/semantic_rules.md` for terminology
- Check `L2-ONTOLOGY/data_models.md` before schema changes
- Reference `L3-AGENCY/decision_authority_matrix.md` before major decisions
- Review `L7-REFLECTION/architecture_decisions.md` for precedent

**End of Day:**
- Update `L6-CONTEXT/project_state.md` if significant changes
- Create `L7-REFLECTION/lessons_learned.md` entries for issues encountered

### Weekly Cycle

**Monday:**
- Review and update `L6-CONTEXT/project_state.md`
- Review open improvements in `L7-REFLECTION/improvement_log.md`

**Friday:**
- Create week's lesson learned entries
- Update metrics in `L1-SYNTAX/metrics_definitions.md`
- Review upcoming milestones in `L6-CONTEXT/project_state.md`

### Phase Transitions

**Phase Start:**
- Update `L4-PRAGMATICS/goal_alignment.md` with phase objectives
- Review `L0-FOUNDATION/project_charter.md` for alignment
- Update `L6-CONTEXT/project_state.md` with new constraints

**Phase End:**
- Comprehensive `L7-REFLECTION/lessons_learned.md` update
- Archive phase-specific context
- Review all ADRs for validity going forward

### Integration with Git Commits

Reference intelligence files in commit messages:

```
Type(scope): Subject

Body explaining changes

Intelligence References:
- Aligns with ADR-015 (caching strategy)
- Updates documented in L2-ONTOLOGY/data_models.md
- Addresses LL-20251110-03 (index performance)

Task/Stage: Stage 1.5.4
Duration: 3 hours
Testing: Verified with 3.9M row dataset
```

### Integration with Airtable Updates

Link intelligence files to Airtable stages/tasks:

- **Task Notes:** Reference ADRs and lessons learned
- **Stage Documentation:** Link to L2-ONTOLOGY and L6-CONTEXT files
- **Phase Completion:** Comprehensive L7-REFLECTION summary

---

## File Naming Conventions

```
intelligence/
├── L0-FOUNDATION/
│   ├── project_charter.md
│   └── user_mandates.md
├── L1-SYNTAX/
│   ├── glossary.md
│   └── metrics_definitions.md
├── L2-ONTOLOGY/
│   ├── data_models.md
│   └── system_architecture.md
├── L3-AGENCY/
│   ├── decision_authority_matrix.md
│   └── responsibility_assignment.md
├── L4-PRAGMATICS/
│   ├── goal_alignment.md
│   └── context_patterns.md
├── L5-SEMANTICS/
│   ├── semantic_rules.md
│   └── terminology_consistency.md
├── L6-CONTEXT/
│   ├── project_state.md
│   └── environmental_factors.md
└── L7-REFLECTION/
    ├── lessons_learned.md
    ├── architecture_decisions.md
    └── improvement_log.md
```

**ID Conventions:**
- **ADR:** `ADR-[001-999]` (Architecture Decision Records)
- **LL:** `LL-[YYYYMMDD]-[01-99]` (Lessons Learned)
- **IMP:** `IMP-[YYYYMMDD]-[01-99]` (Improvements)
- **UM:** `UM-[001-999]` (User Mandates)

---

## Intelligence Governance

### Modification Rights

| Layer | Who Can Modify | Approval Required | Notification |
|-------|----------------|-------------------|--------------|
| **L0** | Project Lead only | Stakeholders | All team |
| **L1** | All team (recommend) | Technical Lead | All team |
| **L2** | Component owners | Technical Lead | Affected teams |
| **L3** | Project Lead | None | All team |
| **L4** | Technical Lead | None | All team |
| **L5** | Technical Lead | None | All team |
| **L6** | All team | None | Daily standup |
| **L7** | All team | None | Weekly review |

### Quality Standards

**All intelligence files must:**
1. Include creation/update date
2. Specify owner/maintainer
3. Define update frequency
4. Use consistent templates
5. Link to related files
6. Provide concrete examples
7. Explain "WHY" not just "WHAT"

### Review Cycles

**Monthly Intelligence Audit:**
1. Check all files updated per schedule
2. Validate cross-references still accurate
3. Identify stale or outdated content
4. Review and consolidate redundant information
5. Ensure examples are current

**Quarterly Intelligence Evolution:**
1. Assess framework effectiveness
2. Identify missing intelligence types
3. Propose structure improvements
4. Archive obsolete intelligence
5. Update templates based on learnings

---

## Automation Scripts

### Planned Intelligence Management Scripts

#### 1. `scripts/intelligence/audit_intelligence_files.py`

**Purpose:** Check intelligence file freshness and completeness
**Cadence:** Weekly (automated via cron)
**Output:** Report of stale/missing files

#### 2. `scripts/intelligence/extract_adr_from_commit.py`

**Purpose:** Auto-generate ADR drafts from significant commits
**Cadence:** Triggered by git hook on commits >500 lines
**Output:** ADR template with commit context pre-filled

#### 3. `scripts/intelligence/link_intelligence_to_airtable.py`

**Purpose:** Sync intelligence file references to Airtable
**Cadence:** After each intelligence file update
**Output:** Updated Airtable stage/task notes with links

#### 4. `scripts/intelligence/generate_intelligence_index.py`

**Purpose:** Create searchable index of all intelligence
**Cadence:** Daily
**Output:** `intelligence/INDEX.md` with full-text search

---

## Success Metrics

### Intelligence Framework Health

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Completeness** | 100% of prescribed files exist | File count audit |
| **Freshness** | 95%+ files updated per schedule | Last modified date check |
| **Usage** | 80%+ of commits reference intelligence | Git commit analysis |
| **Cross-linking** | 90%+ files have valid internal links | Link validation script |
| **Team Adoption** | 100% of team uses weekly | Survey + usage tracking |

### Impact Metrics

| Outcome | Baseline | Target | Measurement |
|---------|----------|--------|-------------|
| **Onboarding Time** | [Current] days | -40% | Time to productivity |
| **Decision Cycle Time** | [Current] hours | -30% | Time from question to decision |
| **Repeat Issues** | [Current] per month | -60% | Issue tracker analysis |
| **Knowledge Loss (turnover)** | [Current] recovery time | -70% | Handoff time measurement |
| **Alignment Score** | [Current]% | 95% | Team survey on shared understanding |

---

## Appendices

### Appendix A: Template Library Location

All templates referenced in this document are available at:
`/home/ubuntu/bqx-ml/intelligence/templates/`

### Appendix B: Robkei-Ring Reference

This framework is adapted from the Robkei-Ring multi-agent system intelligence architecture:
`/home/ubuntu/Robkei-Ring/intelligence/`
`/home/ubuntu/Robkei-Ring/sandbox/intelligence/`

Key reference documents:
- `L1-GLOBAL-INTELLIGENCE-INDEX.md`: Hierarchical intelligence organization
- `L5-SEMANTICS/semantics.md`: Comprehensive semantic framework (1750 lines)
- `SEVEN-COGNITIVE-LAYERS-GAP-ANALYSIS.md`: Cognitive layer assessment methodology

### Appendix C: Integration with Existing Frameworks

**Airtable Operational Cadence:**
- Daily updates: L6-CONTEXT files
- Weekly gap assessment: L7-REFLECTION review
- Monthly architecture review: L2-ONTOLOGY and L7-REFLECTION/ADR audit

**Git Commit Cadence:**
- Level 2 (Task): Reference L7 lessons learned
- Level 3 (Stage): Update L2 and L6
- Level 4 (Phase): Comprehensive L7 update
- Level 5 (Daily EOD): L6 current state

**Gap Assessment Process:**
- Identify gaps in intelligence coverage
- Create remediation tasks
- Track completion in Airtable
- Review effectiveness quarterly

---

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-11 | 2.0 | Comprehensive rewrite based on Robkei-Ring 7-layer framework | Claude Code |
| 2025-11-10 | 1.0 | Initial intelligence file framework | Claude Code |

---

## Next Steps

### Immediate (This Week)
1. Create `intelligence/` directory structure with all L0-L7 subdirectories
2. Create initial files: `project_charter.md`, `glossary.md`, `project_state.md`
3. Begin populating `L2-ONTOLOGY/data_models.md` with current schema
4. Create first ADR for index-based architecture decision

### Short-Term (Next 2 Weeks)
1. Complete all L0-L2 files with current project knowledge
2. Establish weekly L6-CONTEXT update ritual
3. Create first lessons learned entries for recent issues (REG Decimal bug, monitor script fixes)
4. Integrate intelligence references into git commit messages

### Long-Term (Next Month)
1. Full team adoption of intelligence framework
2. Automation scripts operational
3. Monthly intelligence audit process established
4. Quarterly evolution review scheduled

### Strategic (Next Quarter)
1. 95%+ intelligence file freshness achieved
2. Measurable reduction in repeat issues
3. Faster decision-making cycle demonstrated
4. Knowledge transfer on team changes < 1 week
