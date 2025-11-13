#!/usr/bin/env python3
"""
List all phases and their stages from AirTable
"""

import requests
import json
import boto3
from collections import defaultdict

def get_airtable_token():
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId='bqx-mirror/bqx/airtable/api-token')
    data = json.loads(response['SecretString'])
    return data['token']

token = get_airtable_token()
BASE_ID = 'appR3PPnrNkVo48mO'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

print("=" * 100)
print("BQX ML 1,080-FEATURE ARCHITECTURE - PHASE & STAGE OVERVIEW")
print("=" * 100)
print()

# Fetch all phases
phases_url = f'https://api.airtable.com/v0/{BASE_ID}/Phases'
phases_response = requests.get(phases_url, headers=headers)

phases_by_id = {}
if phases_response.status_code == 200:
    phases = phases_response.json().get('records', [])
    for phase in phases:
        phase_id = phase['fields'].get('Phase ID', '')
        phase_name = phase['fields'].get('Phase Name', '')
        phase_status = phase['fields'].get('Status', 'Unknown')
        phases_by_id[phase['id']] = {
            'id': phase_id,
            'name': phase_name,
            'status': phase_status,
            'stages': []
        }

# Fetch all stages
stages_url = f'https://api.airtable.com/v0/{BASE_ID}/Stages'
stages_response = requests.get(stages_url, headers=headers)

if stages_response.status_code == 200:
    stages = stages_response.json().get('records', [])

    # Group stages by phase
    for stage in stages:
        stage_id = stage['fields'].get('Stage ID', '')
        stage_name = stage['fields'].get('Stage Name', '')
        stage_status = stage['fields'].get('Status', 'Unknown')
        phase_link = stage['fields'].get('Phase', [])

        if phase_link:
            phase_record_id = phase_link[0]
            if phase_record_id in phases_by_id:
                phases_by_id[phase_record_id]['stages'].append({
                    'id': stage_id,
                    'name': stage_name,
                    'status': stage_status
                })

# Display phases and stages
sorted_phases = sorted(phases_by_id.values(), key=lambda x: x['id'])

for phase in sorted_phases:
    status_symbol = "✅" if phase['status'] == 'Done' else "⏳" if phase['status'] == 'In Progress' else "📋"

    print(f"{status_symbol} PHASE {phase['id']}: {phase['name']}")
    print(f"   Status: {phase['status']}")

    if phase['stages']:
        print(f"   Stages: {len(phase['stages'])}")

        # Count stage statuses
        done_count = sum(1 for s in phase['stages'] if s['status'] == 'Done')
        print(f"   Progress: {done_count}/{len(phase['stages'])} stages complete")
        print()

        # List stages
        sorted_stages = sorted(phase['stages'], key=lambda x: x['id'])
        for stage in sorted_stages:
            stage_symbol = "✅" if stage['status'] == 'Done' else "⏳" if stage['status'] in ['In Progress', 'In progress'] else "📋"
            print(f"      {stage_symbol} {stage['id']}: {stage['name']} [{stage['status']}]")
    else:
        print("   No stages found")

    print()
    print("-" * 100)
    print()

print()
print("=" * 100)
print("SUMMARY")
print("=" * 100)
print()

total_phases = len(sorted_phases)
done_phases = sum(1 for p in sorted_phases if p['status'] == 'Done')
total_stages = sum(len(p['stages']) for p in sorted_phases)
done_stages = sum(sum(1 for s in p['stages'] if s['status'] == 'Done') for p in sorted_phases)

print(f"Total Phases: {total_phases}")
print(f"Completed Phases: {done_phases}/{total_phases} ({done_phases/total_phases*100:.1f}%)")
print()
print(f"Total Stages: {total_stages}")
print(f"Completed Stages: {done_stages}/{total_stages} ({done_stages/total_stages*100:.1f}%)")
print()
