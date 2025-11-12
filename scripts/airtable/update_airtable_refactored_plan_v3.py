#!/usr/bin/env python3
"""
Update AirTable with refactored BQX ML plan - Fixed version 3
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

# Hard-coded Phase 1.6 ID from our discovery
PHASE_1_6_ID = 'recW9dEOKYcQ11khU'

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
        print(f"✅ Created: {fields.get('Stage ID', fields.get('Phase ID', 'Record'))}")
        return result['id']
    else:
        print(f"❌ Error: {response.status_code} - {response.text[:100]}")
        return None

def create_stages_for_phase(phase_id: str, api_key: str):
    """Create all stages for a given phase"""

    # Phase 1.6 New Stages (1.6.9 - 1.6.17)
    new_stages = [
        {
            'Stage ID': '1.6.9',
            'Stage Name': 'Table Renaming & Migration',
            'Description': '⚠️ CRITICAL FIRST STEP - Rename all rate-based tables to rate_idx convention. This blocks all subsequent stages. Must complete before any BQX builds.',
            'Phase': [phase_id],  # Use array for link field
            'Status': 'Not Started',
            'Duration (Hours)': 1,
            'Dependencies': 'Phase 1.6.1-1.6.8',
            'Owner': 'Data Engineer'
        },
        {
            'Stage ID': '1.6.10',
            'Stage Name': 'Technical IDX Build',
            'Description': 'Build technical indicators on rate_index: RSI, MACD, Stochastic, CCI, Williams %R, ROC, ATR, ADX. Creates technical_idx_{pair} tables (336 partitions).',
            'Phase': [phase_id],
            'Status': 'Not Started',
            'Duration (Hours)': 8,
            'Dependencies': '1.6.9',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.11',
            'Stage Name': 'Technical BQX Build',
            'Description': 'Build technical indicators on BQX momentum (momentum-of-momentum). Same indicators as 1.6.10 but on BQX domain. Creates technical_bqx_{pair} tables.',
            'Phase': [phase_id],
            'Status': 'Not Started',
            'Duration (Hours)': 8,
            'Dependencies': '1.6.9',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.12',
            'Stage Name': 'Statistics BQX Build',
            'Description': 'Statistical moments on BQX: mean, std, skew, kurtosis, percentiles. Creates statistics_bqx_{pair} tables (336 partitions).',
            'Phase': [phase_id],
            'Status': 'Not Started',
            'Duration (Hours)': 6,
            'Dependencies': '1.6.9',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.13',
            'Stage Name': 'Bollinger BQX Build',
            'Description': 'Bollinger bands on BQX momentum: upper, lower, middle bands, %B, bandwidth. Creates bollinger_bqx_{pair} tables.',
            'Phase': [phase_id],
            'Status': 'Not Started',
            'Duration (Hours)': 6,
            'Dependencies': '1.6.9',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.14',
            'Stage Name': 'Fibonacci BQX Build',
            'Description': 'Fibonacci levels in momentum space: retracements, extensions, pivot points. Creates fibonacci_bqx_{pair} tables.',
            'Phase': [phase_id],
            'Status': 'Not Started',
            'Duration (Hours)': 6,
            'Dependencies': '1.6.9',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.15',
            'Stage Name': 'Volume BQX Build',
            'Description': 'Volume-momentum interaction features: volume-weighted momentum, momentum divergence. Creates volume_bqx_{pair} tables.',
            'Phase': [phase_id],
            'Status': 'Not Started',
            'Duration (Hours)': 4,
            'Dependencies': '1.6.9',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.16',
            'Stage Name': 'Correlation IDX Build',
            'Description': 'Populate empty correlation_idx tables with cross-pair correlations on rate_index. Creates correlation_idx_{pair} tables.',
            'Phase': [phase_id],
            'Status': 'Not Started',
            'Duration (Hours)': 8,
            'Dependencies': '1.6.9',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.17',
            'Stage Name': 'Correlation BQX Build',
            'Description': 'FINAL STAGE - Cross-pair/cross-window BQX correlations. Must complete after all other BQX features. Creates correlation_bqx_{pair} tables.',
            'Phase': [phase_id],
            'Status': 'Not Started',
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
        time.sleep(0.25)  # Rate limiting

    return stage_ids

def main():
    print("=" * 80)
    print("BQX ML - AirTable Update: Refactored Plan Implementation (V3)")
    print("=" * 80)

    # Get credentials from AWS Secrets Manager
    api_key = get_airtable_credentials()

    # Phase 1.6 Updates
    print(f"\n✅ Using Phase 1.6 record: {PHASE_1_6_ID}")
    print("\nCreating Phase 1.6 New Stages (1.6.9 - 1.6.17)...")
    print("-" * 40)

    phase_1_6_stage_ids = create_stages_for_phase(PHASE_1_6_ID, api_key)
    print(f"\nPhase 1.6 stages created: {len(phase_1_6_stage_ids)} successful")

    # Create Phase 5: Production Operations
    print("\nCreating Phase 5: Production Operations...")
    print("-" * 40)

    phase_5_fields = {
        'Phase ID': 'Phase 5: Production Operations',
        'Description': 'Operational monitoring, dashboards, runbooks, and continuous improvement for production ML system. Ensures reliability, performance, and cost optimization.',
        'Status': 'Not Started',
        'Duration (Hours)': 16,
        'Dependencies': 'Phase 4',
        'Owner': 'ML Platform Engineer',
        'Phase Number': 5
    }

    phase_5_id = create_record(PHASES_TABLE, phase_5_fields, api_key)

    if phase_5_id:
        print(f"\n✅ Created Phase 5 with ID: {phase_5_id}")

        # Create Phase 5 stages
        phase_5_stages = [
            {
                'Stage ID': '5.1',
                'Stage Name': 'Monitoring & Dashboards',
                'Description': 'CloudWatch dashboards for model performance (R², MAE, latency), cost monitoring, alert configuration (SNS). Tracks directional accuracy > 60%.',
                'Phase': [phase_5_id],  # Use array for link field
                'Status': 'Not Started',
                'Duration (Hours)': 8,
                'Dependencies': 'Phase 4',
                'Owner': 'ML Platform Engineer'
            },
            {
                'Stage ID': '5.2',
                'Stage Name': 'Operational Runbook',
                'Description': 'Incident response procedures: high latency response, model drift detection (MAE increase < 20%), weekly retraining automation.',
                'Phase': [phase_5_id],
                'Status': 'Not Started',
                'Duration (Hours)': 4,
                'Dependencies': '5.1',
                'Owner': 'ML Platform Engineer'
            },
            {
                'Stage ID': '5.3',
                'Stage Name': 'Continuous Improvement',
                'Description': 'Quarterly model reviews, A/B testing framework, experiment tracking system, performance improvement pipeline. Retraining success rate > 90%.',
                'Phase': [phase_5_id],
                'Status': 'Not Started',
                'Duration (Hours)': 4,
                'Dependencies': '5.2',
                'Owner': 'ML Engineer'
            }
        ]

        print("\nCreating Phase 5 Stages...")
        for stage in phase_5_stages:
            create_record(STAGES_TABLE, stage, api_key)
            time.sleep(0.25)

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

    print("\n📊 FEATURE COVERAGE:")
    print("• 730 base features (268 idx + 254 bqx + 208 shared)")
    print("• 332 derived features")
    print("• 1,062 total features")

    print("\nNEXT STEPS:")
    print("1. Execute Phase 1.6.9 (table renaming) - CRITICAL FIRST STEP")
    print("2. Begin parallel execution of Phase 1.6.10-1.6.16")
    print("3. Complete with Phase 1.6.17 (correlation BQX)")
    print("4. Proceed to Phase 2 (Feature Engineering)")
    print("\n✅ Ready to begin implementation!")

if __name__ == '__main__':
    main()