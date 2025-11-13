#!/usr/bin/env python3
"""
List all stages from AirTable - simple version
"""

import requests
import json
import boto3

def get_airtable_token():
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId='bqx-mirror/bqx/airtable/api-token')
    data = json.loads(response['SecretString'])
    return data['token']

token = get_airtable_token()
BASE_ID = 'appR3PPnrNkVo48mO'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

print("=" * 100)
print("BQX ML - ALL STAGES")
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

# Filter to Phase 1.6, 1.7, 1.8 stages
phase_1_6_stages = []
phase_1_7_stages = []
phase_1_8_stages = []
other_stages = []

for stage in all_stages:
    stage_id = stage['fields'].get('Stage ID', '')
    stage_name = stage['fields'].get('Stage Name', '')
    stage_status = stage['fields'].get('Status', 'Unknown')

    stage_info = {
        'id': stage_id,
        'name': stage_name,
        'status': stage_status
    }

    if stage_id.startswith('1.6'):
        phase_1_6_stages.append(stage_info)
    elif stage_id.startswith('1.7'):
        phase_1_7_stages.append(stage_info)
    elif stage_id.startswith('1.8'):
        phase_1_8_stages.append(stage_info)
    else:
        other_stages.append(stage_info)

# Display Phase 1.6 stages
print("PHASE 1.6: GAP REMEDIATION & ADVANCED FEATURES")
print("-" * 100)
if phase_1_6_stages:
    done_count = sum(1 for s in phase_1_6_stages if s['status'] == 'Done')
    print(f"Progress: {done_count}/{len(phase_1_6_stages)} complete")
    print()

    for stage in sorted(phase_1_6_stages, key=lambda x: x['id']):
        status_symbol = "✅" if stage['status'] == 'Done' else "⏳" if stage['status'] in ['In Progress', 'In progress'] else "📋"
        print(f"{status_symbol} {stage['id']}: {stage['name']} [{stage['status']}]")
else:
    print("No Phase 1.6 stages found")

print()
print()

# Display Phase 1.7 stages
print("PHASE 1.7: DATABASE EXPANSION")
print("-" * 100)
if phase_1_7_stages:
    done_count = sum(1 for s in phase_1_7_stages if s['status'] == 'Done')
    print(f"Progress: {done_count}/{len(phase_1_7_stages)} complete")
    print()

    for stage in sorted(phase_1_7_stages, key=lambda x: x['id']):
        status_symbol = "✅" if stage['status'] == 'Done' else "⏳" if stage['status'] in ['In Progress', 'In progress'] else "📋"
        print(f"{status_symbol} {stage['id']}: {stage['name']} [{stage['status']}]")
else:
    print("No Phase 1.7 stages found")

print()
print()

# Display Phase 1.8 stages
print("PHASE 1.8: SPECTRAL & ADVANCED FEATURES")
print("-" * 100)
if phase_1_8_stages:
    done_count = sum(1 for s in phase_1_8_stages if s['status'] == 'Done')
    print(f"Progress: {done_count}/{len(phase_1_8_stages)} complete")
    print()

    for stage in sorted(phase_1_8_stages, key=lambda x: x['id']):
        status_symbol = "✅" if stage['status'] == 'Done' else "⏳" if stage['status'] in ['In Progress', 'In progress'] else "📋"
        print(f"{status_symbol} {stage['id']}: {stage['name']} [{stage['status']}]")
else:
    print("No Phase 1.8 stages found")

print()
print()

# Summary
print("=" * 100)
print("SUMMARY")
print("=" * 100)
print()

total_stages = len(all_stages)
done_stages = sum(1 for s in all_stages if s['fields'].get('Status') == 'Done')

print(f"Total Stages in Database: {total_stages}")
print(f"Total Completed: {done_stages}")
print()
print(f"Phase 1.6: {len(phase_1_6_stages)} stages, {sum(1 for s in phase_1_6_stages if s['status'] == 'Done')} complete")
print(f"Phase 1.7: {len(phase_1_7_stages)} stages")
print(f"Phase 1.8: {len(phase_1_8_stages)} stages")
print()
