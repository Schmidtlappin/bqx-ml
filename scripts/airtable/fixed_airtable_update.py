#!/usr/bin/env python3
"""
Fixed AirTable update script with correct field structure
"""

import requests
import json
import boto3
import time

BASE_ID = 'appR3PPnrNkVo48mO'
STAGES_TABLE = 'Stages'
PHASE_1_6_ID = 'recW9dEOKYcQ11khU'

def get_airtable_token():
    """Get AirTable token from AWS Secrets Manager"""
    try:
        client = boto3.client('secretsmanager', region_name='us-east-1')
        response = client.get_secret_value(SecretId='bqx-mirror/bqx/airtable/api-token')
        data = json.loads(response['SecretString'])
        return data['token']
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve AirTable token from AWS Secrets Manager: {e}")

def create_stage(fields, api_key):
    """Create a stage record with correct field structure"""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    payload = {'fields': fields}
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Created: {fields['Stage ID']}")
        return result['id']
    else:
        print(f"❌ Failed: {fields['Stage ID']}")
        print(f"   Error: {response.text[:200]}")
        return None

def main():
    print("=" * 80)
    print("BQX ML - Fixed AirTable Update")
    print("=" * 80)

    api_key = get_airtable_token()
    print(f"✅ Using token: {api_key[:20]}...")

    # New stages for Phase 1.6 with CORRECT field structure
    new_stages = [
        {
            'Stage ID': '1.6.9 - Table Renaming & Migration',
            'Stage Code': 'BQX-1.6.9',
            'Description': '⚠️ CRITICAL FIRST STEP - Rename all rate-based tables to rate_idx convention. Must complete before any BQX builds.',
            'Status': 'Todo',
            'Duration': '1 hour',
            'Owner': 'Data Engineer',
            'Priority': 'Critical'
        },
        {
            'Stage ID': '1.6.10 - Technical IDX Build',
            'Stage Code': 'BQX-1.6.10',
            'Description': 'Build technical indicators on rate_index: RSI, MACD, Stochastic, CCI, Williams %R, ROC, ATR, ADX.',
            'Status': 'Todo',
            'Duration': '8 hours',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.11 - Technical BQX Build',
            'Stage Code': 'BQX-1.6.11',
            'Description': 'Build technical indicators on BQX momentum (momentum-of-momentum). Same indicators as 1.6.10 but on BQX domain.',
            'Status': 'Todo',
            'Duration': '8 hours',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.12 - Statistics BQX Build',
            'Stage Code': 'BQX-1.6.12',
            'Description': 'Statistical moments on BQX: mean, std, skew, kurtosis, percentiles. Creates statistics_bqx_{pair} tables.',
            'Status': 'Todo',
            'Duration': '6 hours',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.13 - Bollinger BQX Build',
            'Stage Code': 'BQX-1.6.13',
            'Description': 'Bollinger bands on BQX momentum: upper, lower, middle bands, %B, bandwidth.',
            'Status': 'Todo',
            'Duration': '6 hours',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.14 - Fibonacci BQX Build',
            'Stage Code': 'BQX-1.6.14',
            'Description': 'Fibonacci levels in momentum space: retracements, extensions, pivot points.',
            'Status': 'Todo',
            'Duration': '6 hours',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.15 - Volume BQX Build',
            'Stage Code': 'BQX-1.6.15',
            'Description': 'Volume-momentum interaction features: volume-weighted momentum, momentum divergence.',
            'Status': 'Todo',
            'Duration': '4 hours',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.16 - Correlation IDX Build',
            'Stage Code': 'BQX-1.6.16',
            'Description': 'Populate empty correlation_idx tables with cross-pair correlations on rate_index.',
            'Status': 'Todo',
            'Duration': '8 hours',
            'Owner': 'ML Engineer'
        },
        {
            'Stage ID': '1.6.17 - Correlation BQX Build',
            'Stage Code': 'BQX-1.6.17',
            'Description': 'FINAL STAGE - Cross-pair/cross-window BQX correlations. Must complete after all other BQX features.',
            'Status': 'Todo',
            'Duration': '8 hours',
            'Owner': 'ML Engineer'
        }
    ]

    # Advanced feature stages
    advanced_stages = [
        {
            'Stage ID': '1.6.18 - Error Correction Models',
            'Stage Code': 'BQX-1.6.18',
            'Description': '🎯 HIGH ROI - Johansen cointegration on FX triangles. ECT predicts 30-60% of 45-75 min movements.',
            'Status': 'Todo',
            'Duration': '12 hours',
            'Owner': 'ML Engineer',
            'Priority': 'Critical'
        },
        {
            'Stage ID': '1.6.19 - Realized Volatility Family',
            'Stage Code': 'BQX-1.6.19',
            'Description': '🎯 HIGH ROI - Parkinson, Garman-Klass, Rogers-Satchell, Yang-Zhang estimators. 15-25% improvement.',
            'Status': 'Todo',
            'Duration': '10 hours',
            'Owner': 'ML Engineer',
            'Priority': 'Critical'
        },
        {
            'Stage ID': '1.6.20 - HMM Regime Detection',
            'Stage Code': 'BQX-1.6.20',
            'Description': '🎯 HIGH ROI - Hidden Markov Model regime detection (calm/trend/shock). 20-30% regime boundary improvement.',
            'Status': 'Todo',
            'Duration': '10 hours',
            'Owner': 'ML Engineer',
            'Priority': 'Critical'
        },
        {
            'Stage ID': '1.6.21 - Cross-Sectional Panel Features',
            'Stage Code': 'BQX-1.6.21',
            'Description': '🎯 HIGH ROI - Cross-sectional ranks, percentiles, dispersion across 8-pair panel. 20-25% improvement.',
            'Status': 'Todo',
            'Duration': '8 hours',
            'Owner': 'ML Engineer',
            'Priority': 'Critical'
        }
    ]

    # Database expansion stages
    db_stages = [
        {
            'Stage ID': '1.7.1 - Database Schema Expansion',
            'Stage Code': 'BQX-1.7.1',
            'Description': 'Expand Aurora RDB schema for 1,080 features. Add partitions for advanced features.',
            'Status': 'Todo',
            'Duration': '4 hours',
            'Owner': 'Data Engineer'
        },
        {
            'Stage ID': '1.7.2 - Database Performance Optimization',
            'Stage Code': 'BQX-1.7.2',
            'Description': 'Add indexes for new feature tables. Optimize query patterns for ML training.',
            'Status': 'Todo',
            'Duration': '3 hours',
            'Owner': 'Data Engineer'
        }
    ]

    print("\n📝 Creating Basic Dual Architecture Stages...")
    for stage in new_stages:
        create_stage(stage, api_key)
        time.sleep(0.25)

    print("\n🚀 Creating Advanced Feature Stages...")
    for stage in advanced_stages:
        create_stage(stage, api_key)
        time.sleep(0.25)

    print("\n💾 Creating Database Expansion Stages...")
    for stage in db_stages:
        create_stage(stage, api_key)
        time.sleep(0.25)

    print("\n" + "=" * 80)
    print("✅ Update Complete!")
    print("=" * 80)

if __name__ == '__main__':
    main()