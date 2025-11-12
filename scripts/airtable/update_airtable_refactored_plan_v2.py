#!/usr/bin/env python3
"""
Update AirTable with refactored BQX ML plan - Fixed version
Uses AWS Secrets Manager for credentials
"""

import requests
import json
import boto3
from typing import Dict, List
import time

# AirTable configuration
BASE_ID = 'appR3PPnrNkVo48mO'
PHASES_TABLE = 'Phases'
STAGES_TABLE = 'Stages'
TASKS_TABLE = 'Tasks'

def get_airtable_credentials() -> str:
    """Get AirTable credentials from AWS Secrets Manager"""
    client = boto3.client('secretsmanager', region_name='us-east-1')

    try:
        # Get API token from AWS Secrets Manager
        token_response = client.get_secret_value(SecretId='bqx-mirror/bqx/airtable/api-token')
        token_data = json.loads(token_response['SecretString'])
        return token_data['token']
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve AirTable token from AWS Secrets Manager: {e}")

def create_record(table: str, fields: Dict, api_key: str) -> str:
    """Create a record in AirTable"""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table}"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    payload = {'fields': fields}

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        return result['id']
    else:
        print(f"❌ Error creating record: {response.status_code} - {response.text}")
        return None

def get_phase_record_id(phase_name: str, api_key: str) -> str:
    """Get the record ID for a phase by name"""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{PHASES_TABLE}?maxRecords=100"
    headers = {'Authorization': f'Bearer {api_key}'}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        for record in data.get('records', []):
            if phase_name in record['fields'].get('Phase', ''):
                return record['id']
    return None

def main():
    print("=" * 80)
    print("BQX ML - AirTable Update: Refactored Plan Implementation (V2)")
    print("=" * 80)

    # Get credentials from AWS Secrets Manager
    api_key = get_airtable_credentials()

    # Get Phase 1.6 record ID
    phase_1_6_id = get_phase_record_id('1.6', api_key)
    print(f"\n✅ Found Phase 1.6 record: {phase_1_6_id}")

    # Create Phase 1.6 New Stages (1.6.9 - 1.6.17)
    print("\nCreating Phase 1.6 New Stages...")
    print("-" * 40)

    new_stages = [
        {
            'Stage ID': '1.6.9 - Table Renaming & Migration',
            'Description': '⚠️ CRITICAL FIRST STEP - Rename all rate-based tables to rate_idx convention. This blocks all subsequent stages. Must complete before any BQX builds.',
            'Phase (Link)': [phase_1_6_id],  # Use array for link field
            'Status': 'Pending',
            'Duration (Hours)': 1,
            'Dependencies': 'Phase 1.6.1-1.6.8',
            'Owner': 'Data Engineer'
        },
        {
            'Stage ID': '1.6.10 - Technical IDX Build',
            'Description': 'Build technical indicators on rate_index: RSI, MACD, Stochastic, CCI, Williams %R, ROC, ATR, ADX. Creates technical_idx_{pair} tables (336 partitions).',
            'Phase (Link)': [phase_1_6_id],
            'Status': 'Pending',
            'Duration (Hours)': 8,
            'Dependencies': '1.6.9',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.11 - Technical BQX Build',
            'Description': 'Build technical indicators on BQX momentum (momentum-of-momentum). Same indicators as 1.6.10 but on BQX domain. Creates technical_bqx_{pair} tables.',
            'Phase (Link)': [phase_1_6_id],
            'Status': 'Pending',
            'Duration (Hours)': 8,
            'Dependencies': '1.6.9',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.12 - Statistics BQX Build',
            'Description': 'Statistical moments on BQX: mean, std, skew, kurtosis, percentiles. Creates statistics_bqx_{pair} tables (336 partitions).',
            'Phase (Link)': [phase_1_6_id],
            'Status': 'Pending',
            'Duration (Hours)': 6,
            'Dependencies': '1.6.9',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.13 - Bollinger BQX Build',
            'Description': 'Bollinger bands on BQX momentum: upper, lower, middle bands, %B, bandwidth. Creates bollinger_bqx_{pair} tables.',
            'Phase (Link)': [phase_1_6_id],
            'Status': 'Pending',
            'Duration (Hours)': 6,
            'Dependencies': '1.6.9',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.14 - Fibonacci BQX Build',
            'Description': 'Fibonacci levels in momentum space: retracements, extensions, pivot points. Creates fibonacci_bqx_{pair} tables.',
            'Phase (Link)': [phase_1_6_id],
            'Status': 'Pending',
            'Duration (Hours)': 6,
            'Dependencies': '1.6.9',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.15 - Volume BQX Build',
            'Description': 'Volume-momentum interaction features: volume-weighted momentum, momentum divergence. Creates volume_bqx_{pair} tables.',
            'Phase (Link)': [phase_1_6_id],
            'Status': 'Pending',
            'Duration (Hours)': 4,
            'Dependencies': '1.6.9',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.16 - Correlation IDX Build',
            'Description': 'Populate empty correlation_idx tables with cross-pair correlations on rate_index. Creates correlation_idx_{pair} tables.',
            'Phase (Link)': [phase_1_6_id],
            'Status': 'Pending',
            'Duration (Hours)': 8,
            'Dependencies': '1.6.9',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.17 - Correlation BQX Build',
            'Description': 'FINAL STAGE - Cross-pair/cross-window BQX correlations. Must complete after all other BQX features. Creates correlation_bqx_{pair} tables.',
            'Phase (Link)': [phase_1_6_id],
            'Status': 'Pending',
            'Duration (Hours)': 8,
            'Dependencies': '1.6.10-1.6.16',
            'Owner': 'ML Engineer'
        }
    ]

    stage_ids = []
    for stage in new_stages:
        stage_id = create_record(STAGES_TABLE, stage, api_key)
        if stage_id:
            stage_ids.append(stage_id)
            print(f"✅ Created stage: {stage['Stage ID']}")
        time.sleep(0.2)  # Rate limiting

    print(f"\nPhase 1.6 stages created: {len(stage_ids)} successful")

    # Create Phase 5: Production Operations
    print("\nCreating Phase 5: Production Operations...")
    print("-" * 40)

    phase_5_fields = {
        'Phase': 'Phase 5: Production Operations',
        'Description': 'Operational monitoring, dashboards, runbooks, and continuous improvement for production ML system. Ensures reliability, performance, and cost optimization.',
        'Status': 'Pending',
        'Duration (Hours)': 16,
        'Dependencies': 'Phase 4',
        'Owner': 'ML Platform Engineer'
    }

    phase_5_id = create_record(PHASES_TABLE, phase_5_fields, api_key)

    if phase_5_id:
        print(f"✅ Created Phase 5 record: {phase_5_id}")

        # Create Phase 5 stages
        phase_5_stages = [
            {
                'Stage ID': '5.1 - Monitoring & Dashboards',
                'Description': 'CloudWatch dashboards for model performance (R², MAE, latency), cost monitoring, alert configuration (SNS). Tracks directional accuracy > 60%.',
                'Phase (Link)': [phase_5_id],  # Use array for link field
                'Status': 'Pending',
                'Duration (Hours)': 8,
                'Dependencies': 'Phase 4',
                'Owner': 'ML Platform Engineer'
            },
            {
                'Stage ID': '5.2 - Operational Runbook',
                'Description': 'Incident response procedures: high latency response, model drift detection (MAE increase < 20%), weekly retraining automation.',
                'Phase (Link)': [phase_5_id],
                'Status': 'Pending',
                'Duration (Hours)': 4,
                'Dependencies': '5.1',
                'Owner': 'ML Platform Engineer'
            },
            {
                'Stage ID': '5.3 - Continuous Improvement',
                'Description': 'Quarterly model reviews, A/B testing framework, experiment tracking system, performance improvement pipeline. Retraining success rate > 90%.',
                'Phase (Link)': [phase_5_id],
                'Status': 'Pending',
                'Duration (Hours)': 4,
                'Dependencies': '5.2',
                'Owner': 'ML Engineer'
            }
        ]

        for stage in phase_5_stages:
            stage_id = create_record(STAGES_TABLE, stage, api_key)
            if stage_id:
                print(f"✅ Created stage: {stage['Stage ID']}")
            time.sleep(0.2)

    # Summary
    print("\n" + "=" * 80)
    print("✅ AirTable Update Complete!")
    print("=" * 80)

    print("\nSUMMARY OF CHANGES:")
    print("• Added 9 new stages to Phase 1.6 (dual architecture)")
    print("• Created Phase 5: Production Operations with 3 stages")
    print("• Total new stages: 12")
    print("• Timeline: 80-100 hours wall time to production")
    print("• Cost: $286/month production operations")

    print("\nNEXT STEPS:")
    print("1. Review updates in AirTable")
    print("2. Execute Phase 1.6.9 (table renaming) - CRITICAL FIRST STEP")
    print("3. Begin parallel execution of Phase 1.6.10-1.6.16")
    print("4. Complete with Phase 1.6.17 (correlation BQX)")
    print("\n✅ Ready to begin implementation!")

if __name__ == '__main__':
    main()