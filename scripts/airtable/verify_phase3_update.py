#!/usr/bin/env python3
"""Verify Phase 3 update in AirTable"""

import requests
import json
import boto3

def get_airtable_token():
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId='bqx-mirror/bqx/airtable/api-token')
    data = json.loads(response['SecretString'])
    return data['token']

token = get_airtable_token()
url = 'https://api.airtable.com/v0/appR3PPnrNkVo48mO/Phases/recORxvEECPHkKdcS'
headers = {'Authorization': f'Bearer {token}'}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    data = response.json()
    fields = data['fields']

    print("✅ Phase 3 Verification:")
    print(f"  Phase ID: {fields.get('Phase ID', 'N/A')}")
    print(f"  Duration: {fields.get('Duration', 'N/A')}")
    print(f"  Status: {fields.get('Status', 'N/A')}")
    print()
    print("Description preview:")
    desc = fields.get('Description', '')
    lines = desc.split('\n')[:10]
    for line in lines:
        print(f"  {line}")
    print(f"  ... ({len(desc)} total characters)")
    print()

    # Check for key reconciliation markers
    if '1,080' in desc and 'ml.m5.2xlarge' in desc and '$475/month' in desc:
        print("✅ Reconciliation markers confirmed:")
        print("  • 1,080 features: ✅")
        print("  • ml.m5.2xlarge: ✅")
        print("  • $475/month: ✅")
        print("  • Dual architecture: ✅" if 'Dual Architecture' in desc else "  • Dual architecture: ❌")
    else:
        print("⚠️ Some reconciliation markers missing")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
