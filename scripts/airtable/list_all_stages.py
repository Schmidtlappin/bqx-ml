#!/usr/bin/env python3
"""
List all stages from AirTable grouped by Phase ID
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
print("BQX ML 1,080-FEATURE ARCHITECTURE - ALL STAGES")
print("=" * 100)
print()

# Fetch all stages
stages_url = f'https://api.airtable.com/v0/{BASE_ID}/Stages'
all_stages = []
offset = None

while True:
    params = {}
    if offset:
        params['offset'] = offset

    response = requests.get(stages_url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        all_stages.extend(data.get('records', []))

        offset = data.get('offset')
        if not offset:
            break
    else:
        print(f"Error fetching stages: {response.status_code}")
        break

# Group stages by Phase ID prefix
stages_by_phase = defaultdict(list)

for stage in all_stages:
    stage_id = stage['fields'].get('Stage ID', '')
    stage_name = stage['fields'].get('Stage Name', '')
    stage_status = stage['fields'].get('Status', 'Unknown')

    # Extract phase from stage ID (e.g., "1.6.19" -> "1.6")
    if stage_id:
        parts = stage_id.split('.')
        if len(parts) >= 2:
            phase_id = f"{parts[0]}.{parts[1]}"
        else:
            phase_id = parts[0]
    else:
        phase_id = "Unknown"

    stages_by_phase[phase_id].append({
        'id': stage_id,
        'name': stage_name,
        'status': stage_status
    })

# Display stages grouped by phase
sorted_phase_ids = sorted(stages_by_phase.keys(), key=lambda x: tuple(map(float, x.split('.'))) if x != 'Unknown' else (999,))

for phase_id in sorted_phase_ids:
    stages = stages_by_phase[phase_id]

    done_count = sum(1 for s in stages if s['status'] == 'Done')
    in_progress_count = sum(1 for s in stages if s['status'] in ['In Progress', 'In progress'])
    todo_count = sum(1 for s in stages if s['status'] in ['Todo', 'Not Started'])

    status_symbol = "✅" if done_count == len(stages) else "⏳" if in_progress_count > 0 else "📋"

    print(f"{status_symbol} PHASE {phase_id}")
    print(f"   Progress: {done_count}/{len(stages)} complete, {in_progress_count} in progress, {todo_count} todo")
    print()

    # Sort stages by stage ID
    sorted_stages = sorted(stages, key=lambda x: tuple(map(float, x['id'].split('.'))) if x['id'] else (999,))

    for stage in sorted_stages:
        stage_symbol = "✅" if stage['status'] == 'Done' else "⏳" if stage['status'] in ['In Progress', 'In progress'] else "📋"
        print(f"      {stage_symbol} {stage['id']}: {stage['name']}")
        print(f"         Status: {stage['status']}")

    print()
    print("-" * 100)
    print()

print()
print("=" * 100)
print("SUMMARY")
print("=" * 100)
print()

total_stages = len(all_stages)
done_stages = sum(1 for s in all_stages if s['fields'].get('Status') == 'Done')
in_progress_stages = sum(1 for s in all_stages if s['fields'].get('Status') in ['In Progress', 'In progress'])
todo_stages = total_stages - done_stages - in_progress_stages

print(f"Total Stages: {total_stages}")
print(f"✅ Completed: {done_stages}/{total_stages} ({done_stages/total_stages*100:.1f}%)")
print(f"⏳ In Progress: {in_progress_stages}/{total_stages} ({in_progress_stages/total_stages*100:.1f}%)")
print(f"📋 Todo: {todo_stages}/{total_stages} ({todo_stages/total_stages*100:.1f}%)")
print()
