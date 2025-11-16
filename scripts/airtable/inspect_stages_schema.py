#!/usr/bin/env python3
"""
Inspect Stages table schema to find correct field names.
"""

import json
import boto3
import requests

# Retrieve credentials
secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
secret_response = secrets_client.get_secret_value(SecretId='bqx/airtable/api-token')
secret_data = json.loads(secret_response['SecretString'])
AIRTABLE_API_KEY = secret_data.get('token') or secret_data.get('api_key')

BASE_ID = 'appR3PPnrNkVo48mO'

HEADERS = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}

# Get table schema via metadata API
url = f'https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables'
response = requests.get(url, headers=HEADERS)

if response.status_code == 200:
    tables = response.json().get('tables', [])

    # Find Stages table
    stages_table = None
    for table in tables:
        if table['name'] == 'Stages':
            stages_table = table
            break

    if stages_table:
        print("Stages Table Schema:")
        print("=" * 80)
        print(f"Table ID: {stages_table['id']}")
        print(f"Table Name: {stages_table['name']}")
        print()
        print("Fields:")
        for field in stages_table['fields']:
            field_type = field['type']
            print(f"  - {field['name']} ({field_type})")
            if field_type == 'multipleRecordLinks':
                print(f"    → Links to: {field.get('options', {}).get('linkedTableId', 'unknown')}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
