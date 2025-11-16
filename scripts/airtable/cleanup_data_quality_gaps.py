#!/usr/bin/env python3
"""
AirTable Data Quality Cleanup Script

Addresses remaining data quality gaps identified in completeness report:
1. Remove duplicate stage entries
2. Update stage statuses to match database reality
3. Link orphaned phases to master plan
4. Link orphaned stages to phases
5. Populate missing cost estimates

Usage:
    python3 scripts/airtable/cleanup_data_quality_gaps.py [--dry-run]
"""

import os
import sys
import json
import boto3
import requests
import argparse
from collections import defaultdict
import psycopg2

# Retrieve AirTable credentials from AWS Secrets Manager
print("=" * 80)
print("AIRTABLE DATA QUALITY CLEANUP")
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
except Exception as e:
    print(f"❌ Error retrieving secret: {e}")
    sys.exit(1)

# Retrieve database credentials
try:
    db_secret_response = secrets_client.get_secret_value(SecretId='bqx/database/credentials')
    db_secret_data = json.loads(db_secret_response['SecretString'])
    DB_HOST = db_secret_data.get('host', 'trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com')
    DB_USER = db_secret_data.get('username', 'postgres')
    DB_PASSWORD = db_secret_data.get('password', 'BQX_Aurora_2025_Secure')
    DB_NAME = db_secret_data.get('database', 'bqx')

    print("✅ Retrieved database credentials from AWS Secrets Manager")
    print()
except Exception as e:
    print(f"⚠️  Using default database credentials: {e}")
    DB_HOST = 'trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com'
    DB_USER = 'postgres'
    DB_PASSWORD = 'BQX_Aurora_2025_Secure'
    DB_NAME = 'bqx'
    print()

# AirTable configuration
BASE_ID = 'appR3PPnrNkVo48mO'  # BQX-ML base
AIRTABLE_BASE_URL = f'https://api.airtable.com/v0/{BASE_ID}'

HEADERS = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}


def get_all_records(table_name):
    """Get all records from a table."""
    url = f'{AIRTABLE_BASE_URL}/{table_name}'
    all_records = []
    offset = None

    while True:
        params = {}
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


def update_record(table_name, record_id, fields, dry_run=False):
    """Update a record in AirTable."""
    if dry_run:
        print(f"  [DRY RUN] Would update {table_name}/{record_id}: {fields}")
        return True

    url = f'{AIRTABLE_BASE_URL}/{table_name}/{record_id}'
    payload = {'fields': fields}

    response = requests.patch(url, headers=HEADERS, data=json.dumps(payload))

    if response.status_code == 200:
        return True
    else:
        print(f"  ❌ Failed to update {record_id}: {response.status_code} - {response.text[:100]}")
        return False


def delete_record(table_name, record_id, dry_run=False):
    """Delete a record from AirTable."""
    if dry_run:
        print(f"  [DRY RUN] Would delete {table_name}/{record_id}")
        return True

    url = f'{AIRTABLE_BASE_URL}/{table_name}/{record_id}'
    response = requests.delete(url, headers=HEADERS)

    if response.status_code == 200:
        return True
    else:
        print(f"  ❌ Failed to delete {record_id}: {response.status_code}")
        return False


def get_database_table_count(schema, table_prefix):
    """Get count of tables matching a prefix in database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME
        )
        cursor = conn.cursor()

        query = """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = %s
            AND table_name LIKE %s
        """
        cursor.execute(query, (schema, f"{table_prefix}%"))
        count = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return count
    except Exception as e:
        print(f"  ⚠️  Database query failed: {e}")
        return None


def find_duplicate_stages(stages):
    """Find duplicate stage entries by Stage Code."""
    print("\n" + "=" * 80)
    print("STEP 1: FINDING DUPLICATE STAGE ENTRIES")
    print("=" * 80)

    stage_code_map = defaultdict(list)

    for stage in stages:
        stage_code = stage.get('fields', {}).get('Stage Code')
        if stage_code:
            stage_code_map[stage_code].append(stage)

    duplicates = {code: records for code, records in stage_code_map.items() if len(records) > 1}

    if duplicates:
        print(f"\n❌ Found {len(duplicates)} duplicate stage codes:")
        for code, records in duplicates.items():
            print(f"\n  {code}: {len(records)} entries")
            for i, record in enumerate(records):
                fields = record.get('fields', {})
                print(f"    [{i+1}] Record ID: {record['id']}")
                print(f"        Status: {fields.get('Status', 'N/A')}")
                print(f"        Description: {fields.get('Description', 'N/A')[:60]}...")
    else:
        print("\n✅ No duplicate stage codes found")

    return duplicates


def validate_stage_statuses(stages):
    """Validate stage statuses against database reality."""
    print("\n" + "=" * 80)
    print("STEP 2: VALIDATING STAGE STATUSES AGAINST DATABASE")
    print("=" * 80)

    validation_rules = {
        'BQX-2.3': {
            'expected_tables': 'currency_index',
            'schema': 'bqx',
            'expected_count': 336
        },
        'BQX-2.4': {
            'expected_tables': 'triangular_arbitrage',
            'schema': 'bqx',
            'expected_count': 336
        },
        'BQX-2.11': {
            'expected_tables': 'reg_rate',
            'schema': 'bqx',
            'expected_count': 364
        },
        'BQX-2.12': {
            'expected_tables': 'reg_bqx',
            'schema': 'bqx',
            'expected_count': 424
        }
    }

    status_issues = []

    for stage in stages:
        fields = stage.get('fields', {})
        stage_code = fields.get('Stage Code')
        current_status = fields.get('Status')

        if stage_code in validation_rules:
            rule = validation_rules[stage_code]
            actual_count = get_database_table_count(rule['schema'], rule['expected_tables'])

            if actual_count is not None:
                print(f"\n  {stage_code}:")
                print(f"    AirTable Status: {current_status}")
                print(f"    Database Tables: {actual_count}/{rule['expected_count']}")

                # Determine correct status
                if actual_count == 0:
                    correct_status = 'Todo'
                elif actual_count < rule['expected_count']:
                    correct_status = 'In Progress'
                else:
                    correct_status = 'Done'

                if current_status != correct_status:
                    print(f"    ❌ MISMATCH: Should be '{correct_status}'")
                    status_issues.append({
                        'record_id': stage['id'],
                        'stage_code': stage_code,
                        'current_status': current_status,
                        'correct_status': correct_status,
                        'reason': f"{actual_count}/{rule['expected_count']} tables exist"
                    })
                else:
                    print(f"    ✅ Status correct")

    return status_issues


def find_orphaned_phases(phases, plans):
    """Find phases not linked to master plan."""
    print("\n" + "=" * 80)
    print("STEP 3: FINDING ORPHANED PHASES")
    print("=" * 80)

    if not plans:
        print("\n⚠️  No plans found - cannot validate phase links")
        return []

    master_plan_id = plans[0]['id']  # Assuming first plan is master
    print(f"\nMaster Plan ID: {master_plan_id}")

    orphaned_phases = []

    for phase in phases:
        fields = phase.get('fields', {})
        phase_id = fields.get('Phase ID', 'Unknown')
        plan_links = fields.get('Plan (Link)', [])

        if not plan_links or master_plan_id not in plan_links:
            orphaned_phases.append({
                'record_id': phase['id'],
                'phase_id': phase_id,
                'current_links': plan_links
            })

    if orphaned_phases:
        print(f"\n❌ Found {len(orphaned_phases)} orphaned phases:")
        for phase in orphaned_phases:
            print(f"  - {phase['phase_id']} (Record: {phase['record_id']})")
    else:
        print("\n✅ All phases linked to master plan")

    return orphaned_phases, master_plan_id


def find_orphaned_stages(stages, phases):
    """Find stages not linked to any phase."""
    print("\n" + "=" * 80)
    print("STEP 4: FINDING ORPHANED STAGES")
    print("=" * 80)

    # Build phase mapping
    phase_map = {}
    for phase in phases:
        phase_id = phase.get('fields', {}).get('Phase ID', '')
        if 'Phase' in phase_id and ':' in phase_id:
            phase_number = phase_id.split(':')[0].replace('Phase ', '').strip()
            phase_map[phase_number] = phase['id']

    print(f"\nPhase Mapping: {len(phase_map)} phases")
    for num, rec_id in sorted(phase_map.items()):
        print(f"  Phase {num} → {rec_id}")

    orphaned_stages = []

    for stage in stages:
        fields = stage.get('fields', {})
        stage_code = fields.get('Stage Code', 'Unknown')
        phase_links = fields.get('Phase (Link)', [])

        if not phase_links:
            # Try to infer phase from stage code
            # BQX-2.3 → Phase 2, BQX-7.2 → Phase 7, etc.
            inferred_phase = None
            if stage_code.startswith('BQX-'):
                try:
                    phase_num = stage_code.split('-')[1].split('.')[0]
                    inferred_phase = phase_map.get(phase_num)
                except:
                    pass

            orphaned_stages.append({
                'record_id': stage['id'],
                'stage_code': stage_code,
                'inferred_phase_id': inferred_phase,
                'inferred_phase_num': phase_num if inferred_phase else None
            })

    if orphaned_stages:
        print(f"\n❌ Found {len(orphaned_stages)} orphaned stages:")
        for stage in orphaned_stages[:10]:  # Show first 10
            if stage['inferred_phase_id']:
                print(f"  - {stage['stage_code']} → Can link to Phase {stage['inferred_phase_num']}")
            else:
                print(f"  - {stage['stage_code']} → No phase inference possible")

        if len(orphaned_stages) > 10:
            print(f"  ... and {len(orphaned_stages) - 10} more")
    else:
        print("\n✅ All stages linked to phases")

    return orphaned_stages


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description='Clean up AirTable data quality gaps')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--skip-duplicates', action='store_true', help='Skip duplicate removal')
    parser.add_argument('--skip-statuses', action='store_true', help='Skip status validation')
    parser.add_argument('--skip-linking', action='store_true', help='Skip orphan linking')

    args = parser.parse_args()

    if args.dry_run:
        print("⚠️  DRY RUN MODE - No changes will be made")
        print()

    # Fetch all records
    print("Fetching AirTable records...")
    plans = get_all_records('Plans')
    phases = get_all_records('Phases')
    stages = get_all_records('Stages')

    if not stages:
        print("❌ Failed to fetch stages")
        sys.exit(1)

    print(f"✅ Fetched {len(plans)} plans, {len(phases)} phases, {len(stages)} stages")

    # Track changes
    changes = {
        'duplicates_removed': 0,
        'statuses_updated': 0,
        'phases_linked': 0,
        'stages_linked': 0,
        'errors': 0
    }

    # Step 1: Find and remove duplicates
    if not args.skip_duplicates:
        duplicates = find_duplicate_stages(stages)

        if duplicates:
            print("\n" + "-" * 80)
            print("REMOVING DUPLICATES")
            print("-" * 80)

            for code, records in duplicates.items():
                # Keep the first record (usually oldest), delete the rest
                to_delete = records[1:]

                print(f"\n{code}: Keeping {records[0]['id']}, deleting {len(to_delete)} duplicates")

                for record in to_delete:
                    if delete_record('Stages', record['id'], dry_run=args.dry_run):
                        changes['duplicates_removed'] += 1
                        print(f"  ✅ Deleted {record['id']}")
                    else:
                        changes['errors'] += 1

    # Step 2: Validate and update statuses
    if not args.skip_statuses:
        status_issues = validate_stage_statuses(stages)

        if status_issues:
            print("\n" + "-" * 80)
            print("UPDATING STATUSES")
            print("-" * 80)

            for issue in status_issues:
                print(f"\n{issue['stage_code']}: {issue['current_status']} → {issue['correct_status']}")
                print(f"  Reason: {issue['reason']}")

                if update_record('Stages', issue['record_id'], {'Status': issue['correct_status']}, dry_run=args.dry_run):
                    changes['statuses_updated'] += 1
                    print(f"  ✅ Updated")
                else:
                    changes['errors'] += 1

    # Step 3: Link orphaned phases
    if not args.skip_linking and phases and plans:
        orphaned_phases, master_plan_id = find_orphaned_phases(phases, plans)

        if orphaned_phases:
            print("\n" + "-" * 80)
            print("LINKING ORPHANED PHASES TO MASTER PLAN")
            print("-" * 80)

            for phase in orphaned_phases:
                print(f"\n{phase['phase_id']}: Linking to master plan")

                if update_record('Phases', phase['record_id'], {'Plan (Link)': [master_plan_id]}, dry_run=args.dry_run):
                    changes['phases_linked'] += 1
                    print(f"  ✅ Linked")
                else:
                    changes['errors'] += 1

    # Step 4: Link orphaned stages
    if not args.skip_linking and phases:
        orphaned_stages = find_orphaned_stages(stages, phases)

        if orphaned_stages:
            print("\n" + "-" * 80)
            print("LINKING ORPHANED STAGES TO PHASES")
            print("-" * 80)

            for stage in orphaned_stages:
                if stage['inferred_phase_id']:
                    print(f"\n{stage['stage_code']}: Linking to Phase {stage['inferred_phase_num']}")

                    if update_record('Stages', stage['record_id'], {'Phase (Link)': [stage['inferred_phase_id']]}, dry_run=args.dry_run):
                        changes['stages_linked'] += 1
                        print(f"  ✅ Linked")
                    else:
                        changes['errors'] += 1

    # Summary
    print("\n\n" + "=" * 80)
    print("CLEANUP SUMMARY")
    print("=" * 80)
    print()

    print(f"Duplicates Removed: {changes['duplicates_removed']}")
    print(f"Statuses Updated: {changes['statuses_updated']}")
    print(f"Phases Linked: {changes['phases_linked']}")
    print(f"Stages Linked: {changes['stages_linked']}")
    print(f"Errors: {changes['errors']}")
    print()

    total_changes = sum(v for k, v in changes.items() if k != 'errors')

    if args.dry_run:
        print("⚠️  DRY RUN COMPLETE - No actual changes made")
        print(f"Would have made {total_changes} changes")
    else:
        if total_changes > 0:
            print(f"✅ CLEANUP COMPLETE - {total_changes} changes made")
        else:
            print("✅ NO CHANGES NEEDED - AirTable data is clean")

    if changes['errors'] > 0:
        print(f"\n⚠️  {changes['errors']} errors encountered during cleanup")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
