#!/usr/bin/env python3
"""
Working AirTable update script - uses only valid fields
"""

import requests
import json
import boto3
import time

BASE_ID = 'appR3PPnrNkVo48mO'
STAGES_TABLE = 'Stages'

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
    print("BQX ML - Working AirTable Update (Valid Fields Only)")
    print("=" * 80)

    api_key = get_airtable_token()
    print(f"✅ Using token: {api_key[:20]}...")

    # New stages with ONLY valid fields (Stage ID, Stage Code, Description, Status, Duration)
    new_stages = [
        {
            'Stage ID': '1.6.9 - Table Renaming & Migration',
            'Stage Code': 'BQX-1.6.9',
            'Description': '⚠️ CRITICAL FIRST STEP - Rename 2,628 rate tables to rate_idx convention. Blocks all subsequent work. 1 hour operation.',
            'Status': 'Todo',
            'Duration': '1 hour'
        },
        {
            'Stage ID': '1.6.10 - Technical IDX Build',
            'Stage Code': 'BQX-1.6.10',
            'Description': 'Build technical indicators on rate_index: RSI, MACD, Stochastic, CCI, Williams %R, ROC, ATR, ADX. 336 partitions.',
            'Status': 'Todo',
            'Duration': '8 hours'
        },
        {
            'Stage ID': '1.6.11 - Technical BQX Build',
            'Stage Code': 'BQX-1.6.11',
            'Description': 'Build technical indicators on BQX momentum. Same indicators but momentum-of-momentum. 336 partitions.',
            'Status': 'Todo',
            'Duration': '8 hours'
        },
        {
            'Stage ID': '1.6.12 - Statistics BQX Build',
            'Stage Code': 'BQX-1.6.12',
            'Description': 'Statistical moments on BQX: mean, std, skew, kurtosis, percentiles. 336 partitions.',
            'Status': 'Todo',
            'Duration': '6 hours'
        },
        {
            'Stage ID': '1.6.13 - Bollinger BQX Build',
            'Stage Code': 'BQX-1.6.13',
            'Description': 'Bollinger bands on BQX momentum: upper, lower, middle bands, %B, bandwidth. 336 partitions.',
            'Status': 'Todo',
            'Duration': '6 hours'
        },
        {
            'Stage ID': '1.6.14 - Fibonacci BQX Build',
            'Stage Code': 'BQX-1.6.14',
            'Description': 'Fibonacci levels in momentum space: retracements, extensions, pivot points. 336 partitions.',
            'Status': 'Todo',
            'Duration': '6 hours'
        },
        {
            'Stage ID': '1.6.15 - Volume BQX Build',
            'Stage Code': 'BQX-1.6.15',
            'Description': 'Volume-momentum interaction: volume-weighted momentum, momentum divergence. 336 partitions.',
            'Status': 'Todo',
            'Duration': '4 hours'
        },
        {
            'Stage ID': '1.6.16 - Correlation IDX Build',
            'Stage Code': 'BQX-1.6.16',
            'Description': 'Populate empty correlation_idx tables with cross-pair correlations on rate_index. 336 partitions.',
            'Status': 'Todo',
            'Duration': '8 hours'
        },
        {
            'Stage ID': '1.6.17 - Correlation BQX Build',
            'Stage Code': 'BQX-1.6.17',
            'Description': 'FINAL - Cross-pair/cross-window BQX correlations. Must complete after all other BQX features.',
            'Status': 'Todo',
            'Duration': '8 hours'
        }
    ]

    # Advanced feature stages (Tier 1 High-ROI)
    advanced_stages = [
        {
            'Stage ID': '1.6.18 - Error Correction Models',
            'Stage Code': 'BQX-1.6.18',
            'Description': '🎯 HIGH ROI - Johansen cointegration. ECT predicts 30-60% of 45-75 min movements. 672 partitions.',
            'Status': 'Todo',
            'Duration': '12 hours'
        },
        {
            'Stage ID': '1.6.19 - Realized Volatility Family',
            'Stage Code': 'BQX-1.6.19',
            'Description': '🎯 HIGH ROI - Parkinson, Garman-Klass, Rogers-Satchell, Yang-Zhang. 15-25% improvement. 672 partitions.',
            'Status': 'Todo',
            'Duration': '10 hours'
        },
        {
            'Stage ID': '1.6.20 - HMM Regime Detection',
            'Stage Code': 'BQX-1.6.20',
            'Description': '🎯 HIGH ROI - Hidden Markov Models (calm/trend/shock). 20-30% regime boundary improvement. 672 partitions.',
            'Status': 'Todo',
            'Duration': '10 hours'
        },
        {
            'Stage ID': '1.6.21 - Cross-Sectional Panel',
            'Stage Code': 'BQX-1.6.21',
            'Description': '🎯 HIGH ROI - Panel ranks, percentiles, dispersion. 20-25% systematic move detection. Single panel table.',
            'Status': 'Todo',
            'Duration': '8 hours'
        }
    ]

    # Database expansion stages
    db_stages = [
        {
            'Stage ID': '1.7.1 - Database Schema Expansion',
            'Stage Code': 'BQX-1.7.1',
            'Description': 'Expand Aurora RDB for 1,080 features. Add 3,036 new tables. Current 61GB → 97GB projected.',
            'Status': 'Todo',
            'Duration': '4 hours'
        },
        {
            'Stage ID': '1.7.2 - Database Optimization',
            'Stage Code': 'BQX-1.7.2',
            'Description': 'Add indexes for new features. Optimize query patterns. Vacuum and analyze all tables.',
            'Status': 'Todo',
            'Duration': '3 hours'
        },
        {
            'Stage ID': '1.7.3 - Data Quality Validation',
            'Stage Code': 'BQX-1.7.3',
            'Description': 'Validate all feature tables. Check completeness. Verify dual architecture consistency.',
            'Status': 'Todo',
            'Duration': '2 hours'
        }
    ]

    # PDF Comparison stages (from user expectations documents)
    pdf_stages = [
        {
            'Stage ID': '1.8.1 - Parabolic Term Comparisons',
            'Stage Code': 'BQX-1.8.1',
            'Description': 'Implement normalized parabolic regression terms (a2, a1, b) comparisons cross-pair, cross-window, cross-domain.',
            'Status': 'Todo',
            'Duration': '6 hours'
        },
        {
            'Stage ID': '1.8.2 - Multi-Scale Features',
            'Stage Code': 'BQX-1.8.2',
            'Description': 'Add 30m and 60m timeframe features for 60-75 min horizons. Cascade alignment metrics.',
            'Status': 'Todo',
            'Duration': '5 hours'
        },
        {
            'Stage ID': '1.8.3 - Spectral Features',
            'Stage Code': 'BQX-1.8.3',
            'Description': 'FFT band energies (2-4m, 5-15m, 20-60m). Wavelet decomposition. SSA components.',
            'Status': 'Todo',
            'Duration': '8 hours'
        }
    ]

    print("\n📝 Creating Basic Dual Architecture Stages (1.6.9-1.6.17)...")
    created_count = 0
    for stage in new_stages:
        if create_stage(stage, api_key):
            created_count += 1
        time.sleep(0.25)

    print(f"\n✅ Created {created_count}/{len(new_stages)} basic stages")

    print("\n🚀 Creating Advanced Feature Stages (1.6.18-1.6.21)...")
    created_count = 0
    for stage in advanced_stages:
        if create_stage(stage, api_key):
            created_count += 1
        time.sleep(0.25)

    print(f"\n✅ Created {created_count}/{len(advanced_stages)} advanced stages")

    print("\n💾 Creating Database Expansion Stages (1.7.x)...")
    created_count = 0
    for stage in db_stages:
        if create_stage(stage, api_key):
            created_count += 1
        time.sleep(0.25)

    print(f"\n✅ Created {created_count}/{len(db_stages)} database stages")

    print("\n📚 Creating PDF-Based Feature Stages (1.8.x)...")
    created_count = 0
    for stage in pdf_stages:
        if create_stage(stage, api_key):
            created_count += 1
        time.sleep(0.25)

    print(f"\n✅ Created {created_count}/{len(pdf_stages)} PDF-based stages")

    print("\n" + "=" * 80)
    print("✅ AirTable Update Complete!")
    print("=" * 80)

    print("\n📊 SUMMARY:")
    print("• Total features: 1,080 (730 base + 350 advanced)")
    print("• Database growth: 61GB → 97GB (59.5% increase)")
    print("• Timeline: 66 hours wall time (~11 days)")
    print("• Expected R²: 0.82-0.88")
    print("• Expected directional accuracy: 65-70%")

    print("\n🚨 CRITICAL PATH:")
    print("1. Execute Stage 1.6.9 (table renaming) - BLOCKS ALL WORK")
    print("2. Parallel execution of 1.6.10-1.6.16")
    print("3. Stage 1.6.17 (Correlation BQX) after all others")
    print("4. Advanced features (1.6.18-1.6.21) for maximum ROI")

if __name__ == '__main__':
    main()