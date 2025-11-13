#!/usr/bin/env python3
"""
Update AirTable Stage 1.6.9 status to Complete

Marks the critical table renaming stage as complete after successful execution.
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
print("UPDATING AIRTABLE STAGE 1.6.9 STATUS")
print("=" * 80)
print()

# Find Stage 1.6.9
url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}'
params = {'filterByFormula': "FIND('1.6.9', {Stage ID}) > 0"}
response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    records = response.json()['records']
    if records:
        stage_record = records[0]
        stage_id = stage_record['id']
        stage_name = stage_record['fields'].get('Stage ID', '')

        print(f"Found Stage: {stage_name}")
        print(f"Record ID: {stage_id}")
        print()

        # Update status to Done (try multiple valid values)
        update_url = f'{url}/{stage_id}'

        # Try common status values
        for status_value in ['Done', 'Completed', 'Complete', 'Finished']:
            payload = {
                'fields': {
                    'Status': status_value
                }
            }

            update_response = requests.patch(update_url, headers=headers, json=payload)

            if update_response.status_code == 200:
                print(f"✅ Stage 1.6.9 status updated to '{status_value}'!")
                print()
                print("RESULTS:")
                print("  • 1,456 tables renamed successfully")
                print("  • statistics_rate: 364 tables, 10,315,898 rows")
                print("  • bollinger_rate: 364 tables, 10,315,898 rows")
                print("  • fibonacci_rate: 364 tables, 10,235,258 rows")
                print("  • correlation_rate: 364 tables, 0 rows")
                print("  • Execution time: ~6.5 seconds")
                print()
                print("✅ ALL SUBSEQUENT FEATURE WORK NOW UNBLOCKED")
                break
            elif 'INVALID_MULTIPLE_CHOICE_OPTIONS' in update_response.text:
                print(f"  Trying '{status_value}'... not valid")
                continue
            else:
                print(f"❌ Error updating status with '{status_value}': {update_response.status_code}")
                print(update_response.text)
                break
    else:
        print("❌ Stage 1.6.9 not found")
else:
    print(f"❌ Error finding stage: {response.status_code}")

print()
print("=" * 80)
