#!/usr/bin/env python3
"""
Verify AirTable Project Management Structure Completeness

Checks all project management tables (Plans, Phases, Stages, Tasks, Todos)
and validates relationships, completeness, and identifies gaps.

Usage:
    python3 scripts/airtable/verify_project_management_structure.py
"""

import os
import sys
import json
import boto3
import requests
from collections import defaultdict

# Retrieve AirTable credentials from AWS Secrets Manager
print("=" * 80)
print("VERIFYING AIRTABLE PROJECT MANAGEMENT STRUCTURE")
print("=" * 80)
print()

try:
    secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
    secret_response = secrets_client.get_secret_value(SecretId='bqx/airtable/api-token')
    secret_data = json.loads(secret_response['SecretString'])
    AIRTABLE_API_KEY = secret_data.get('token') or secret_data.get('api_key')

    if not AIRTABLE_API_KEY:
        print("❌ Error: Could not find 'token' or 'api_key' field in secret")
        sys.exit(1)

    print("✅ Retrieved AirTable API token from AWS Secrets Manager")
    print()
except Exception as e:
    print(f"❌ Error retrieving secret: {e}")
    sys.exit(1)

# AirTable configuration
BASE_ID = 'appR3PPnrNkVo48mO'  # BQX-ML base
AIRTABLE_BASE_URL = f'https://api.airtable.com/v0/{BASE_ID}'

HEADERS = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}


def list_all_tables():
    """List all tables in the base via API metadata endpoint."""
    url = f'https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables'
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        return response.json().get('tables', [])
    else:
        print(f"❌ Failed to list tables: {response.status_code}")
        return None


def get_all_records(table_name, max_records=None):
    """Get all records from a table."""
    url = f'{AIRTABLE_BASE_URL}/{table_name}'
    params = {}
    if max_records:
        params['maxRecords'] = max_records

    all_records = []
    offset = None

    while True:
        if offset:
            params['offset'] = offset

        response = requests.get(url, headers=HEADERS, params=params)

        if response.status_code != 200:
            print(f"❌ Error fetching {table_name}: {response.status_code}")
            return None

        data = response.json()
        all_records.extend(data.get('records', []))

        offset = data.get('offset')
        if not offset:
            break

    return all_records


def analyze_table_structure(table_name, records, expected_fields=None):
    """Analyze a table's structure and completeness."""
    print(f"\n{'=' * 80}")
    print(f"TABLE: {table_name}")
    print(f"{'=' * 80}")

    if not records:
        print(f"⚠️  Empty table - no records found")
        return {
            'table': table_name,
            'count': 0,
            'status': 'EMPTY',
            'gaps': ['No records found']
        }

    print(f"Total Records: {len(records)}")

    # Analyze field coverage
    all_fields = set()
    field_coverage = defaultdict(int)

    for record in records:
        fields = record.get('fields', {})
        all_fields.update(fields.keys())
        for field in fields:
            if fields[field]:  # Non-empty value
                field_coverage[field] += 1

    print(f"\nFields Present: {len(all_fields)}")
    for field in sorted(all_fields):
        coverage = field_coverage[field]
        pct = (coverage / len(records)) * 100
        status = "✅" if pct >= 90 else "⚠️" if pct >= 50 else "❌"
        print(f"  {status} {field}: {coverage}/{len(records)} ({pct:.1f}%)")

    # Check for expected fields
    gaps = []
    if expected_fields:
        missing_fields = set(expected_fields) - all_fields
        if missing_fields:
            gaps.append(f"Missing fields: {', '.join(missing_fields)}")
            print(f"\n❌ Missing Expected Fields: {', '.join(missing_fields)}")

    # Sample first record
    print(f"\nSample Record (first):")
    sample = records[0].get('fields', {})
    for key, value in list(sample.items())[:5]:
        value_str = str(value)[:60] + "..." if len(str(value)) > 60 else str(value)
        print(f"  - {key}: {value_str}")

    return {
        'table': table_name,
        'count': len(records),
        'fields': list(all_fields),
        'field_coverage': dict(field_coverage),
        'gaps': gaps,
        'status': 'OK' if not gaps else 'GAPS_FOUND'
    }


def verify_relationships(plans, phases, stages, tasks, todos):
    """Verify hierarchical relationships between PM tables."""
    print(f"\n{'=' * 80}")
    print("RELATIONSHIP VERIFICATION")
    print(f"{'=' * 80}")

    issues = []

    # Plans → Phases
    if plans and phases:
        plan_ids = {r['id'] for r in plans}
        phase_plan_refs = set()
        for phase in phases:
            phase_links = phase.get('fields', {}).get('Plans', [])
            if isinstance(phase_links, list):
                phase_plan_refs.update(phase_links)

        orphaned_phases = phase_plan_refs - plan_ids
        if orphaned_phases:
            issues.append(f"Orphaned Phases: {len(orphaned_phases)} phases reference non-existent plans")
        else:
            print("✅ Plans → Phases: All references valid")

    # Phases → Stages
    if phases and stages:
        phase_ids = {r['id'] for r in phases}
        stage_phase_refs = set()
        for stage in stages:
            stage_links = stage.get('fields', {}).get('Phase', [])
            if isinstance(stage_links, list):
                stage_phase_refs.update(stage_links)

        orphaned_stages = stage_phase_refs - phase_ids
        if orphaned_stages:
            issues.append(f"Orphaned Stages: {len(orphaned_stages)} stages reference non-existent phases")
        else:
            print("✅ Phases → Stages: All references valid")

    # Stages → Tasks
    if stages and tasks:
        stage_ids = {r['id'] for r in stages}
        task_stage_refs = set()
        for task in tasks:
            task_links = task.get('fields', {}).get('Stage', [])
            if isinstance(task_links, list):
                task_stage_refs.update(task_links)

        orphaned_tasks = task_stage_refs - stage_ids
        if orphaned_tasks:
            issues.append(f"Orphaned Tasks: {len(orphaned_tasks)} tasks reference non-existent stages")
        else:
            print("✅ Stages → Tasks: All references valid")

    # Tasks → Todos
    if tasks and todos:
        task_ids = {r['id'] for r in tasks}
        todo_task_refs = set()
        for todo in todos:
            todo_links = todo.get('fields', {}).get('Task', [])
            if isinstance(todo_links, list):
                todo_task_refs.update(todo_links)

        orphaned_todos = todo_task_refs - task_ids
        if orphaned_todos:
            issues.append(f"Orphaned Todos: {len(orphaned_todos)} todos reference non-existent tasks")
        else:
            print("✅ Tasks → Todos: All references valid")

    return issues


def main():
    """Main execution."""

    # Step 1: List all tables in base
    print("\nSTEP 1: Listing all tables in BQX-ML base...")
    print("-" * 80)

    all_tables = list_all_tables()
    if not all_tables:
        print("❌ Failed to list tables")
        sys.exit(1)

    print(f"Found {len(all_tables)} tables:")
    for table in all_tables:
        print(f"  - {table['name']} ({table['id']})")

    table_names = [t['name'] for t in all_tables]

    # Step 2: Identify PM tables
    print("\n\nSTEP 2: Identifying Project Management tables...")
    print("-" * 80)

    pm_tables = {
        'Plans': 'Plans' in table_names,
        'Phases': 'Phases' in table_names,
        'Stages': 'Stages' in table_names,
        'Tasks': 'Tasks' in table_names,
        'Todos': 'Todos' in table_names,
        'Resources': 'Resources' in table_names,
        'Agents': 'Agents' in table_names,
        'Gangs': 'Gangs' in table_names
    }

    for table, exists in pm_tables.items():
        status = "✅" if exists else "❌"
        print(f"{status} {table}: {'EXISTS' if exists else 'MISSING'}")

    # Step 3: Fetch and analyze each PM table
    print("\n\nSTEP 3: Analyzing each Project Management table...")
    print("-" * 80)

    results = {}

    # Core PM tables
    core_pm_tables = ['Plans', 'Phases', 'Stages', 'Tasks', 'Todos']

    for table_name in core_pm_tables:
        if table_name in table_names:
            records = get_all_records(table_name)
            results[table_name] = analyze_table_structure(table_name, records)
        else:
            print(f"\n❌ TABLE: {table_name} - DOES NOT EXIST")
            results[table_name] = {
                'table': table_name,
                'count': 0,
                'status': 'MISSING',
                'gaps': ['Table does not exist']
            }

    # Step 4: Verify relationships
    plans_records = get_all_records('Plans') if 'Plans' in table_names else []
    phases_records = get_all_records('Phases') if 'Phases' in table_names else []
    stages_records = get_all_records('Stages') if 'Stages' in table_names else []
    tasks_records = get_all_records('Tasks') if 'Tasks' in table_names else []
    todos_records = get_all_records('Todos') if 'Todos' in table_names else []

    relationship_issues = verify_relationships(
        plans_records, phases_records, stages_records, tasks_records, todos_records
    )

    # Step 5: Generate summary report
    print("\n\n" + "=" * 80)
    print("COMPLETENESS SUMMARY")
    print("=" * 80)
    print()

    print("Project Management Tables:")
    for table_name in core_pm_tables:
        result = results.get(table_name, {})
        count = result.get('count', 0)
        status = result.get('status', 'UNKNOWN')

        if status == 'MISSING':
            print(f"  ❌ {table_name}: DOES NOT EXIST")
        elif status == 'EMPTY':
            print(f"  ⚠️  {table_name}: EXISTS but EMPTY (0 records)")
        elif status == 'GAPS_FOUND':
            print(f"  ⚠️  {table_name}: {count} records, but has GAPS")
        else:
            print(f"  ✅ {table_name}: {count} records, COMPLETE")

    print()
    print("Relationship Integrity:")
    if relationship_issues:
        for issue in relationship_issues:
            print(f"  ❌ {issue}")
    else:
        print("  ✅ All relationships valid (no orphaned records)")

    print()
    print("Overall Assessment:")

    total_gaps = sum(1 for r in results.values() if r.get('gaps'))
    total_gaps += len(relationship_issues)

    if total_gaps == 0 and all(r.get('status') in ['OK', 'COMPLETE'] for r in results.values()):
        print("  ✅ COMPLETE - No gaps found")
        print()
        print("The AirTable project management structure is complete and properly configured.")
        sys.exit(0)
    else:
        print(f"  ❌ INCOMPLETE - {total_gaps} issues found")
        print()
        print("Critical Issues:")
        for table_name, result in results.items():
            if result.get('gaps'):
                print(f"\n  {table_name}:")
                for gap in result['gaps']:
                    print(f"    - {gap}")

        if relationship_issues:
            print("\n  Relationship Issues:")
            for issue in relationship_issues:
                print(f"    - {issue}")

        print()
        print("Recommendations:")
        print("  1. Create missing PM tables if needed")
        print("  2. Populate empty tables with initial records")
        print("  3. Fix orphaned relationships")
        print("  4. Ensure all core fields are present")

        sys.exit(1)


if __name__ == '__main__':
    main()
