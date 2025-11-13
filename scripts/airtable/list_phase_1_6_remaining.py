#!/usr/bin/env python3
"""
List all remaining Phase 1.6 stages after Option B completion
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
STAGES_TABLE = 'Stages'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

print("=" * 80)
print("PHASE 1.6 STAGES - COMPREHENSIVE STATUS")
print("=" * 80)
print()

# Get all Phase 1.6 stages
url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}'
params = {
    'filterByFormula': "FIND('1.6', {Stage ID}) > 0",
    'sort[0][field]': 'Stage ID',
    'sort[0][direction]': 'asc'
}

response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    records = response.json()['records']

    completed = []
    pending = []

    for record in records:
        fields = record['fields']
        stage_id = fields.get('Stage ID', 'N/A')
        name = fields.get('Name', 'N/A')
        status = fields.get('Status', 'Unknown')
        description = fields.get('Description', '')[:100] + '...' if fields.get('Description', '') else 'N/A'

        stage_info = {
            'id': stage_id,
            'name': name,
            'status': status,
            'description': description
        }

        if status in ['Done', 'Complete', 'Completed']:
            completed.append(stage_info)
        else:
            pending.append(stage_info)

    print(f"COMPLETED STAGES: {len(completed)}")
    print("-" * 80)
    for stage in completed:
        print(f"✅ {stage['id']:8} | {stage['name']}")

    print()
    print(f"PENDING STAGES: {len(pending)}")
    print("-" * 80)
    for stage in pending:
        print(f"⏳ {stage['id']:8} | {stage['status']:12} | {stage['name']}")
        if stage['description'] != 'N/A':
            print(f"   Description: {stage['description']}")

    print()
    print("=" * 80)
    print(f"TOTAL PHASE 1.6 STAGES: {len(records)}")
    print(f"  Completed: {len(completed)}/{len(records)} ({len(completed)*100//len(records)}%)")
    print(f"  Remaining: {len(pending)}/{len(records)} ({len(pending)*100//len(records)}%)")
    print("=" * 80)

    if pending:
        print()
        print("NEXT IMMEDIATE STEP:")
        next_stage = pending[0]
        print(f"  Stage: {next_stage['id']} - {next_stage['name']}")
        print(f"  Status: {next_stage['status']}")

else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
