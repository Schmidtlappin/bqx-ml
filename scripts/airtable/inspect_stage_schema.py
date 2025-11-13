#!/usr/bin/env python3
"""
Inspect AirTable Stages schema by examining existing stage records
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
print("INSPECTING AIRTABLE STAGES SCHEMA")
print("=" * 80)
print()

# Get a few example stages
stages_url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}'
params = {'maxRecords': 3}
response = requests.get(stages_url, headers=headers, params=params)

if response.status_code == 200:
    records = response.json()['records']

    if records:
        print(f"Found {len(records)} example stages")
        print()

        for i, record in enumerate(records, 1):
            print(f"Example Stage {i}:")
            print("-" * 80)
            print(f"Record ID: {record['id']}")
            print(f"Created Time: {record.get('createdTime', 'N/A')}")
            print()
            print("Fields:")
            for field_name, field_value in sorted(record['fields'].items()):
                print(f"  {field_name}: {field_value}")
            print()
            print()
    else:
        print("No stages found in table")
else:
    print(f"Error fetching stages: {response.status_code}")
    print(response.text)

# Also check the Phases table for comparison
print()
print("=" * 80)
print("INSPECTING AIRTABLE PHASES SCHEMA")
print("=" * 80)
print()

phases_url = f'https://api.airtable.com/v0/{BASE_ID}/Phases'
params = {'maxRecords': 2}
response = requests.get(phases_url, headers=headers, params=params)

if response.status_code == 200:
    records = response.json()['records']

    if records:
        print(f"Found {len(records)} example phases")
        print()

        for i, record in enumerate(records, 1):
            print(f"Example Phase {i}:")
            print("-" * 80)
            print(f"Record ID: {record['id']}")
            print()
            print("Fields:")
            for field_name, field_value in sorted(record['fields'].items()):
                print(f"  {field_name}: {field_value}")
            print()
            print()
    else:
        print("No phases found in table")
else:
    print(f"Error fetching phases: {response.status_code}")
    print(response.text)
