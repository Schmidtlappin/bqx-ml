# .claude/ Directory - Session Continuity Files

**Purpose**: Enable seamless session handoff when Claude Code sessions terminate and new sessions start.

**Created**: 2025-11-09
**Last Updated**: 2025-11-09

---

## Overview

This directory contains JSON files that preserve the state, context, and critical information needed for a new Claude Code session to continue work on the BQX-ML project without requiring re-discovery or re-analysis.

When a session terminates and a new session starts from the `/home/ubuntu/bqx-ml` directory, these files provide complete project context.

---

## Files

### 1. `project-state.json`
**What**: Current state of the BQX-ML project

**Contains**:
- Project metadata (name, ID, description, repository)
- Timeline and progress tracking
- Phase/stage completion status
- Database and Airtable state
- Recent milestones and activities
- Success criteria tracking

**Use**: Get high-level overview of where the project stands.

**Example**:
```json
{
  "project": {
    "name": "BQX-ML",
    "status": "In Progress",
    "progress_percentage": 12
  },
  "database": {
    "total_rows": 3530479,
    "completion_percentage": 34.3
  }
}
```

---

### 2. `session-context.json`
**What**: Context from the previous session for handoff

**Contains**:
- Session metadata (start/end time, agent, working directory)
- Session objectives (what was being worked on)
- Critical context (blockers, key decisions, architecture choices)
- Conversation summary
- Handoff notes (what next session should do)
- Environment state (active processes, connections)
- Lessons learned

**Use**: Understand what the previous session accomplished and what needs to happen next.

**Example**:
```json
{
  "critical_context": {
    "immediate_blocker": {
      "issue": "BQX backfill process hung at 34.3%",
      "resolution": "Kill PID 216204, fix import path, restart"
    }
  },
  "handoff_notes": {
    "immediate_action": "Kill hung backfill process and restart"
  }
}
```

---

### 3. `active-tasks.json`
**What**: Tasks currently in progress or pending

**Contains**:
- Priority tasks (Critical, High, Medium, Low)
- Task details (ID, title, description, steps, success criteria)
- Blocking relationships
- Estimated hours and completion times
- Backlog items
- Completed tasks from this session

**Use**: Know exactly what to work on next and in what order.

**Example**:
```json
{
  "priority_tasks": {
    "critical": [
      {
        "id": "TASK-001",
        "title": "Restart BQX backfill process",
        "blocking": true,
        "steps": ["Kill PID 216204", "Fix import path", "Restart"]
      }
    ]
  }
}
```

---

### 4. `known-issues.json`
**What**: All known issues, problems, and blockers

**Contains**:
- Critical/High/Medium/Low severity issues
- Issue details (root cause, symptoms, impact)
- Resolution plans
- Estimated fix times
- Resolved issues (for reference)
- Watching list (potential issues)

**Use**: Avoid re-discovering known problems, understand what's broken and how to fix it.

**Example**:
```json
{
  "critical_issues": [
    {
      "id": "ISSUE-001",
      "title": "BQX backfill process hung at 34.3%",
      "root_cause": "Import path broken after migration",
      "resolution": "Kill process, fix path, restart"
    }
  ]
}
```

---

### 5. `key-resources.json`
**What**: All critical paths, credentials, endpoints, and reference information

**Contains**:
- Database connections (Aurora PostgreSQL)
- Airtable API details (bases, tables, field conventions)
- AWS credentials and services
- GitHub repositories and structure
- File locations (docs, scripts, logs)
- Data schema details
- Monitoring commands
- Quick reference commands

**Use**: Find any resource, credential, or path without searching.

**Example**:
```json
{
  "databases": {
    "aurora_postgresql": {
      "endpoint": "trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com",
      "credentials": {
        "username": "postgres",
        "password": "<REDACTED>"
      }
    }
  }
}
```

---

## Usage Patterns

### Starting a New Session

1. **Read `session-context.json` first**
   - Understand what the previous session was doing
   - Identify immediate blockers
   - Note critical decisions made

2. **Check `active-tasks.json`**
   - See what needs to be done next
   - Understand task dependencies
   - Prioritize work

3. **Review `known-issues.json`**
   - Be aware of existing problems
   - Don't waste time re-discovering issues
   - Use documented solutions

4. **Reference `key-resources.json` as needed**
   - Look up credentials
   - Find file paths
   - Copy monitoring commands

5. **Check `project-state.json` for context**
   - Understand overall progress
   - Know which phases are active
   - Track milestones

### During Session

- **Update files as you go**
  - Add new tasks to `active-tasks.json`
  - Document new issues in `known-issues.json`
  - Update progress in `project-state.json`
  - Add important context to `session-context.json`

- **Maintain accuracy**
  - Mark tasks complete when done
  - Update issue status as resolved
  - Keep timestamps current

### Ending Session

- **Update `session-context.json`**
  - Add handoff notes for next session
  - Document any new critical context
  - Update environment state

- **Clean up `active-tasks.json`**
  - Mark completed tasks
  - Update priorities
  - Add new tasks discovered

- **Document lessons**
  - Add to `session-context.json` lessons_learned
  - Prevent future mistakes

---

## File Maintenance

### When to Update

**Continuously**:
- `active-tasks.json` (as tasks complete/change)
- `known-issues.json` (as issues arise/resolve)

**Daily**:
- `project-state.json` (progress updates)
- `session-context.json` (context updates)

**As Needed**:
- `key-resources.json` (when resources change)

### Version Control

These files **should be committed to git** so they persist across:
- Session terminations
- System restarts
- Repository clones

**Important**: Be careful with credentials. Current files include passwords for development convenience, but for production:
- Move credentials to AWS Secrets Manager
- Reference secrets by ARN/name, not plaintext
- Use environment variables

---

## Integration with Claude Code

### How Claude Code Uses These Files

1. **Session Start**: New Claude Code instance reads these JSON files to understand project state
2. **Context Loading**: Parses structured data to build mental model
3. **Task Execution**: References files for credentials, paths, commands
4. **Progress Tracking**: Updates files as work progresses
5. **Session End**: Prepares handoff notes for next session

### Benefits

- **No context loss** between sessions
- **Faster ramp-up** (no re-discovery)
- **Consistent knowledge** (all sessions reference same source of truth)
- **Better decision making** (access to historical context)
- **Reduced errors** (documented lessons prevent repeats)

---

## Example Workflow

### Session 1 (Initial Work)
```
1. Create BQX tables ✓
2. Start backfill process ✓
3. Gap analysis ✓
4. Session terminates (hung process discovered)
   → Write to session-context.json: "Backfill hung, needs restart"
   → Write to known-issues.json: ISSUE-001
   → Write to active-tasks.json: TASK-001 (restart backfill)
```

### Session 2 (Continuation)
```
1. Read session-context.json → See "Backfill hung"
2. Read active-tasks.json → See TASK-001 is critical
3. Read known-issues.json → Understand root cause
4. Read key-resources.json → Get restart command
5. Execute: Kill process, fix import, restart
6. Monitor progress
7. Update files: Mark TASK-001 complete, resolve ISSUE-001
```

### Session 3 (Next Work)
```
1. Read active-tasks.json → See TASK-002, TASK-003 next
2. Read project-state.json → Phase 1 now 100% complete
3. Begin Phase 2 work
4. Document progress
```

---

## Best Practices

1. **Keep JSON Valid**: Always ensure proper JSON syntax
2. **Use Timestamps**: ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
3. **Be Specific**: Don't say "soon", say "2025-11-10T09:00:00Z"
4. **Document Decisions**: Record why, not just what
5. **Update Atomically**: Complete one logical update before moving on
6. **Test Readability**: Can someone else understand without asking questions?
7. **Link Related Info**: Cross-reference between files (e.g., "See TASK-001 in active-tasks.json")

---

## Troubleshooting

### Files Not Found
- Check you're in `/home/ubuntu/bqx-ml/.claude/`
- Verify files exist: `ls -la /home/ubuntu/bqx-ml/.claude/`

### JSON Parse Errors
- Validate JSON: `python3 -m json.tool < file.json`
- Check for trailing commas, missing quotes, unescaped characters

### Stale Information
- Check "last_updated" timestamps
- If > 24 hours old, regenerate from current state

### Missing Context
- Read all 5 files, not just one
- Check cross-references
- Look in git history if needed

---

## Future Enhancements

Potential additions to this system:

- **session-history.json**: Archive of previous sessions
- **metrics.json**: KPIs and performance tracking
- **decisions-log.json**: ADR-style decision records
- **risk-register.json**: Identified risks and mitigations
- **architecture.json**: System architecture documentation
- **test-results.json**: Test execution history

---

**Created by**: RobkeiRingMaster (RM-001)
**Purpose**: Session continuity and knowledge preservation
**Status**: Active and maintained
**Next Update**: When next session starts
