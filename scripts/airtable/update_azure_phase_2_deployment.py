#!/usr/bin/env python3
"""
Update AirTable with Azure Phase 2 deployment progress in real-time.
Tracks stage completion, costs, runtime, and performance metrics.

Usage:
    # Start a stage
    python3 update_azure_phase_2_deployment.py --event stage_start --stage 2.2

    # Complete a stage
    python3 update_azure_phase_2_deployment.py --event stage_complete --stage 2.2 --runtime 3.5 --cost 13.42

    # Update multiple stages
    python3 update_azure_phase_2_deployment.py --event stage_start --stages 2.2,2.3,2.4,2.8

    # Mark Phase 2 complete
    python3 update_azure_phase_2_deployment.py --event phase_complete
"""

import os
import sys
import argparse
import requests
import json
import boto3
from datetime import datetime, timezone

# Configuration
BASE_ID = 'appR3PPnrNkVo48mO'
STAGES_TABLE = 'Stages'
PHASES_TABLE = 'Phases'

# Stage mapping
STAGE_MAPPING = {
    '2.2': {
        'stage_id': '2.2 - Technical Indicators',
        'stage_code': 'BQX-2.2',
        'description': 'Calculate RSI, MACD, Stochastic, ATR, CCI on rate_index and BQX values',
        'estimated_duration': '3.5 hours',
        'estimated_cost': 13.42,
        'workers': 32,
        'features': 180
    },
    '2.3': {
        'stage_id': '2.3 - Currency Indices',
        'stage_code': 'BQX-2.3',
        'description': 'Calculate currency strength indices for 8 major currencies',
        'estimated_duration': '2 hours',
        'estimated_cost': 3.07,
        'workers': 8,
        'features': 8
    },
    '2.4': {
        'stage_id': '2.4 - Arbitrage Detection',
        'stage_code': 'BQX-2.4',
        'description': 'Detect triangular arbitrage opportunities and consistency metrics',
        'estimated_duration': '6 hours',
        'estimated_cost': 9.20,
        'workers': 8,
        'features': 4
    },
    '2.8': {
        'stage_id': '2.8 - Enhanced RMSE Features',
        'stage_code': 'BQX-2.8',
        'description': 'Advanced regression analysis with RMSE improvement metrics',
        'estimated_duration': '3 hours',
        'estimated_cost': 4.60,
        'workers': 8,
        'features': 60
    },
    '2.9': {
        'stage_id': '2.9 - Regime Detection',
        'stage_code': 'BQX-2.9',
        'description': 'Market regime classification (trending, ranging, volatile)',
        'estimated_duration': '6 hours',
        'estimated_cost': 9.20,
        'workers': 32,
        'features': 30
    },
    '2.6': {
        'stage_id': '2.6 - Temporal Causality Validation',
        'stage_code': 'BQX-2.6',
        'description': 'Validate no lookahead bias in all features',
        'estimated_duration': '3 hours',
        'estimated_cost': 4.60,
        'workers': 16,
        'features': 0
    },
    '2.7': {
        'stage_id': '2.7 - S3 Export',
        'stage_code': 'BQX-2.7',
        'description': 'Export all features to S3 Parquet format (40-50 GB)',
        'estimated_duration': '3 hours',
        'estimated_cost': 4.60,
        'workers': 8,
        'features': 0
    }
}


def get_airtable_token():
    """Retrieve AirTable API token from AWS Secrets Manager."""
    try:
        client = boto3.client('secretsmanager', region_name='us-east-1')
        response = client.get_secret_value(SecretId='bqx-mirror/bqx/airtable/api-token')
        data = json.loads(response['SecretString'])
        return data['token']
    except Exception as e:
        print(f"❌ Error getting AirTable token: {e}")
        print("ℹ️  Using environment variable AIRTABLE_API_KEY as fallback")
        return os.environ.get('AIRTABLE_API_KEY')


def find_stage_record(token, stage_id):
    """Find AirTable record for a given stage ID."""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Search for stage by ID
    params = {
        'filterByFormula': f"FIND('{stage_id}', {{Stage ID}}) > 0"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        records = response.json().get('records', [])

        if records:
            return records[0]['id']
        else:
            return None

    except Exception as e:
        print(f"❌ Error finding stage record: {e}")
        return None


def create_stage_record(token, stage_key):
    """Create a new stage record if it doesn't exist."""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    stage_info = STAGE_MAPPING[stage_key]

    payload = {
        'fields': {
            'Stage ID': stage_info['stage_id'],
            'Stage Code': stage_info['stage_code'],
            'Status': 'Todo',
            'Description': stage_info['description'],
            'Duration': stage_info['estimated_duration'],
            'Estimated Cost': stage_info['estimated_cost'],
            'Cloud Platform': 'Azure',
            'Instance Type': 'Standard_D64as_v5',
            'vCPU Count': 64,
            'Max Workers': stage_info['workers'],
            'Features Added': stage_info['features']
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        record_id = response.json()['id']
        print(f"✅ Created stage record: {stage_info['stage_id']}")
        return record_id

    except Exception as e:
        print(f"❌ Error creating stage record: {e}")
        return None


def update_stage(token, stage_key, event, runtime=None, cost=None, notes=None):
    """Update stage status in AirTable."""

    stage_info = STAGE_MAPPING.get(stage_key)
    if not stage_info:
        print(f"❌ Unknown stage: {stage_key}")
        return False

    stage_id = stage_info['stage_id']

    # Find or create record
    record_id = find_stage_record(token, stage_id)
    if not record_id:
        record_id = create_stage_record(token, stage_key)
        if not record_id:
            return False

    # Prepare update payload
    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}/{record_id}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    fields = {}

    if event == 'stage_start':
        fields['Status'] = 'In Progress'
        fields['Start Time'] = datetime.now(timezone.utc).isoformat()

    elif event == 'stage_complete':
        fields['Status'] = 'Done'
        fields['End Time'] = datetime.now(timezone.utc).isoformat()

        if runtime:
            fields['Actual Runtime'] = f"{runtime} hours"

        if cost:
            fields['Actual Cost'] = cost

        # Calculate variance
        if runtime and cost:
            est_runtime = float(stage_info['estimated_duration'].split()[0])
            est_cost = stage_info['estimated_cost']

            runtime_variance = ((runtime - est_runtime) / est_runtime) * 100
            cost_variance = ((cost - est_cost) / est_cost) * 100

            fields['Runtime Variance'] = f"{runtime_variance:+.1f}%"
            fields['Cost Variance'] = f"{cost_variance:+.1f}%"

    if notes:
        existing_notes = fields.get('Notes', '')
        fields['Notes'] = f"{existing_notes}\n\n[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}] {notes}"

    payload = {'fields': fields}

    try:
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()

        print(f"✅ Updated stage {stage_id}: {event}")
        if runtime:
            print(f"   Runtime: {runtime} hours (estimated: {stage_info['estimated_duration']})")
        if cost:
            print(f"   Cost: ${cost:.2f} (estimated: ${stage_info['estimated_cost']:.2f})")

        return True

    except Exception as e:
        print(f"❌ Error updating stage: {e}")
        return False


def update_phase_complete(token):
    """Mark Phase 2 as complete in AirTable."""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{PHASES_TABLE}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Find Phase 2 record
    params = {
        'filterByFormula': "FIND('Phase 2', {Phase Name}) > 0"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        records = response.json().get('records', [])

        if not records:
            print("❌ Phase 2 record not found")
            return False

        record_id = records[0]['id']

        # Update to Done
        update_url = f'{url}/{record_id}'
        payload = {
            'fields': {
                'Status': 'Done',
                'Completion Date': datetime.now(timezone.utc).isoformat(),
                'Notes': f"Phase 2 completed on Azure D64as_v5 at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
            }
        }

        response = requests.patch(update_url, headers=headers, json=payload)
        response.raise_for_status()

        print("✅ Phase 2 marked complete in AirTable")
        return True

    except Exception as e:
        print(f"❌ Error updating Phase 2: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Update AirTable with Azure Phase 2 deployment progress')
    parser.add_argument('--event', required=True, choices=['stage_start', 'stage_complete', 'phase_complete'],
                        help='Event type')
    parser.add_argument('--stage', help='Stage key (e.g., 2.2, 2.3)')
    parser.add_argument('--stages', help='Comma-separated stage keys (e.g., 2.2,2.3,2.4)')
    parser.add_argument('--runtime', type=float, help='Actual runtime in hours')
    parser.add_argument('--cost', type=float, help='Actual cost in USD')
    parser.add_argument('--notes', help='Additional notes to append')

    args = parser.parse_args()

    # Get AirTable token
    token = get_airtable_token()
    if not token:
        print("❌ No AirTable API token available")
        sys.exit(1)

    # Handle phase_complete event
    if args.event == 'phase_complete':
        success = update_phase_complete(token)
        sys.exit(0 if success else 1)

    # Handle stage events
    stages = []
    if args.stage:
        stages.append(args.stage)
    if args.stages:
        stages.extend(args.stages.split(','))

    if not stages:
        print("❌ No stages specified. Use --stage or --stages")
        sys.exit(1)

    # Update each stage
    all_success = True
    for stage in stages:
        stage = stage.strip()
        success = update_stage(token, stage, args.event, args.runtime, args.cost, args.notes)
        if not success:
            all_success = False

    sys.exit(0 if all_success else 1)


if __name__ == '__main__':
    main()
