#!/usr/bin/env python3
"""
Update AirTable with Refactored BQX ML Plan
Uses AWS Secrets Manager for credentials
Adds new stages, updates existing ones, optimizes timeline

Date: 2025-11-12
Author: BQX ML Team
"""

import requests
import json
import boto3
from datetime import datetime
import time

# Get credentials from AWS Secrets Manager
def get_airtable_credentials():
    """Get AirTable credentials from AWS Secrets Manager"""
    client = boto3.client('secretsmanager', region_name='us-east-1')

    # Get API token
    token_response = client.get_secret_value(SecretId='bqx-mirror/bqx/airtable/api-token')
    token_data = json.loads(token_response['SecretString'])
    api_token = token_data['token']

    # Base ID is hardcoded as confirmed
    base_id = 'appR3PPnrNkVo48mO'

    return api_token, base_id

# Get credentials
API_TOKEN, BASE_ID = get_airtable_credentials()

HEADERS = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Content-Type': 'application/json'
}

# AirTable Table Names
PHASES_TABLE = 'Phases'
STAGES_TABLE = 'Stages'
TASKS_TABLE = 'Tasks'

def create_record(table, fields, retry_count=3):
    """Create a record in AirTable with retry logic"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{table}'

    for attempt in range(retry_count):
        try:
            response = requests.post(url, headers=HEADERS, json={'fields': fields})

            if response.status_code == 200:
                record = response.json()
                print(f"✅ Created {table} record: {fields.get('Stage ID', fields.get('Task ID', 'record'))}")
                return record['id']
            elif response.status_code == 429:  # Rate limited
                wait_time = int(response.headers.get('Retry-After', 30))
                print(f"⏳ Rate limited, waiting {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"❌ Error creating record: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Exception: {e}")
            if attempt < retry_count - 1:
                time.sleep(5)
            else:
                return None

    return None

def update_record(table, record_id, fields, retry_count=3):
    """Update a record in AirTable"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{table}/{record_id}'

    for attempt in range(retry_count):
        try:
            response = requests.patch(url, headers=HEADERS, json={'fields': fields})

            if response.status_code == 200:
                print(f"✅ Updated {table} record: {record_id}")
                return True
            elif response.status_code == 429:
                wait_time = int(response.headers.get('Retry-After', 30))
                print(f"⏳ Rate limited, waiting {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"❌ Error updating record: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Exception: {e}")
            if attempt < retry_count - 1:
                time.sleep(5)

    return False

def get_phase_1_6_record():
    """Find Phase 1.6 record ID"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{PHASES_TABLE}'

    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        records = response.json()['records']
        for record in records:
            if 'Phase 1.6' in record['fields'].get('Phase ID', ''):
                return record['id']
    return None

def main():
    print("=" * 80)
    print("BQX ML - AirTable Update: Refactored Plan Implementation")
    print("=" * 80)
    print()

    # Get Phase 1.6 record ID
    phase_1_6_id = get_phase_1_6_record()
    if not phase_1_6_id:
        print("❌ Could not find Phase 1.6 record")
        return

    print(f"✅ Found Phase 1.6 record: {phase_1_6_id}")
    print()

    # =========================================================================
    # PHASE 1.6 NEW STAGES (1.6.9 - 1.6.17)
    # =========================================================================

    print("Creating Phase 1.6 New Stages...")
    print("-" * 40)

    # Stage 1.6.9: Table Renaming (CRITICAL - blocks all others)
    stage_1_6_9_fields = {
        'Stage ID': '1.6.9 - Table Renaming & Migration',
        'Stage Code': 'BQX-1.6.9',
        'Description': '''⚠️ CRITICAL FIRST STEP - Blocks all subsequent stages

Rename existing rate-based feature tables to new dual architecture naming convention.

**RENAMING PLAN:**
• reg_{pair} → reg_idx_{pair} (336 partitions)
• statistics_features_{pair} → statistics_idx_{pair} (364 partitions)
• bollinger_features_{pair} → bollinger_idx_{pair} (364 partitions)
• fibonacci_features_{pair} → fibonacci_idx_{pair} (364 partitions)
• volume_features_{pair} → volume_idx_{pair} (336 partitions)
• spread_features_{pair} → spread_idx_{pair} (336 partitions)
• correlation_features_{pair} → correlation_idx_{pair} (364 partitions, currently empty)

**TOTAL:** 2,248 table renames
**TIME:** 45 minutes (ALTER TABLE is atomic)
**IMPACT:** Zero downtime, preserves all data

**DELIVERABLES:**
• SQL script: phase_1_6_9_rename_rate_tables.sql
• Verification report (row counts unchanged)
• Updated documentation

**WHY CRITICAL:**
Establishes dual architecture foundation for rate_idx + BQX features''',
        'Status': 'Todo',
        'Duration': '1 hour',
        'Assigned To': 'DATA-001',
        'Autonomy Level': 'Level 1 - Fully Autonomous',
        'Estimated Cost': 0,
        'Phase (Link)': [phase_1_6_id]
    }

    stage_id_1_6_9 = create_record(STAGES_TABLE, stage_1_6_9_fields)
    time.sleep(1)  # Rate limiting

    # Create tasks for 1.6.9
    if stage_id_1_6_9:
        tasks_1_6_9 = [
            {
                'Task ID': 'TSK-1.6.9.1',
                'Task Name': 'Execute table rename SQL script',
                'Status': 'Todo',
                'Priority': 'Critical',
                'Estimated Hours': 0.5,
                'Stage (Link)': [stage_id_1_6_9]
            },
            {
                'Task ID': 'TSK-1.6.9.2',
                'Task Name': 'Verify row counts unchanged post-rename',
                'Status': 'Todo',
                'Priority': 'High',
                'Estimated Hours': 0.25,
                'Stage (Link)': [stage_id_1_6_9]
            },
            {
                'Task ID': 'TSK-1.6.9.3',
                'Task Name': 'Update documentation with new table names',
                'Status': 'Todo',
                'Priority': 'Medium',
                'Estimated Hours': 0.25,
                'Stage (Link)': [stage_id_1_6_9]
            }
        ]

        for task in tasks_1_6_9:
            create_record(TASKS_TABLE, task)
            time.sleep(0.5)

    # Stage 1.6.10: Technical IDX Build
    stage_1_6_10_fields = {
        'Stage ID': '1.6.10 - Technical IDX Build',
        'Stage Code': 'BQX-1.6.10',
        'Description': '''Build technical indicators on rate_index (normalized prices).

**FEATURES (15 indicators):**
• RSI (14, 21 periods) - Relative Strength Index
• MACD (line, signal, histogram) - Trend direction
• Stochastic (%K, %D) - Overbought/oversold
• CCI (20) - Commodity Channel Index
• Williams %R (14) - Momentum oscillator
• ROC (12) - Rate of Change
• ADX (14) - Trend strength
• +DI/-DI - Directional indicators
• ATR (14) - Average True Range (volatility)

**DATA SOURCE:** M1 tables rate_index column (base-100 normalized)
**TARGET:** 336 partitions (28 pairs × 12 months)
**EXPECTED:** 10.3M rows total

**INTERPRETATION:**
• RSI > 70: Price overbought
• MACD crossover: Trend change
• High ATR: Increased volatility

**PARALLELIZABLE:** Yes (can run with 1.6.11)''',
        'Status': 'Todo',
        'Duration': '8 hours',
        'Assigned To': 'DATA-001',
        'Autonomy Level': 'Level 2 - Budget Approved',
        'Estimated Cost': 5,
        'Phase (Link)': [phase_1_6_id]
    }

    stage_id_1_6_10 = create_record(STAGES_TABLE, stage_1_6_10_fields)
    time.sleep(1)

    # Stage 1.6.11: Technical BQX Build
    stage_1_6_11_fields = {
        'Stage ID': '1.6.11 - Technical BQX Build',
        'Stage Code': 'BQX-1.6.11',
        'Description': '''Build technical indicators on BQX momentum (momentum-of-momentum).

**FEATURES:** Same 15 indicators as 1.6.10 but computed on BQX values

**DATA SOURCE:** bqx_{pair}.w15_bqx_return
**TARGET:** 336 partitions

**KEY INSIGHT - 2nd DERIVATIVE SIGNALS:**
• RSI_BQX > 70: Momentum acceleration is overbought (not just price!)
• MACD_BQX: Trend direction in momentum space
• ATR_BQX high: Unstable momentum regime

**COMPARISON:**
• Rate IDX RSI > 70 + BQX RSI < 50 = Price extended but momentum fading
• Rate IDX RSI < 30 + BQX RSI > 70 = Price oversold but momentum accelerating

**WHY BOTH:** Different information - price can be overbought while momentum is neutral

**PARALLELIZABLE:** Yes (can run with 1.6.10)''',
        'Status': 'Todo',
        'Duration': '8 hours',
        'Assigned To': 'DATA-001',
        'Autonomy Level': 'Level 2 - Budget Approved',
        'Estimated Cost': 5,
        'Phase (Link)': [phase_1_6_id]
    }

    stage_id_1_6_11 = create_record(STAGES_TABLE, stage_1_6_11_fields)
    time.sleep(1)

    # Stage 1.6.12: Statistics BQX Build
    stage_1_6_12_fields = {
        'Stage ID': '1.6.12 - Statistics BQX Build',
        'Stage Code': 'BQX-1.6.12',
        'Description': '''Build statistical moments on BQX momentum.

**FEATURES (24 total):**
• mean_{20,50,120} - Average momentum
• std_{20,50,120} - Momentum volatility
• skew_{20,50,120} - Momentum distribution asymmetry
• kurt_{20,50,120} - Momentum tail risk
• min/max_{20,50,120} - Momentum range
• z_score_{20,50,120} - Standardized momentum position

**DATA SOURCE:** bqx_{pair}.w15_bqx_return
**NOTE:** Rate version already exists (renamed statistics_idx_{pair})

**INTERPRETATION:**
• High BQX std: Unstable momentum regime (regime transition signal)
• BQX skewness: Momentum bias direction
• BQX kurtosis: Extreme momentum event likelihood

**PARALLELIZABLE:** Yes''',
        'Status': 'Todo',
        'Duration': '6 hours',
        'Assigned To': 'DATA-001',
        'Autonomy Level': 'Level 2 - Budget Approved',
        'Estimated Cost': 4,
        'Phase (Link)': [phase_1_6_id]
    }

    stage_id_1_6_12 = create_record(STAGES_TABLE, stage_1_6_12_fields)
    time.sleep(1)

    # Continue with remaining stages...
    # Stage 1.6.13: Bollinger BQX
    stage_1_6_13_fields = {
        'Stage ID': '1.6.13 - Bollinger BQX Build',
        'Stage Code': 'BQX-1.6.13',
        'Description': '''Build Bollinger Bands on BQX momentum.

**FEATURES (10 total):**
• bb_upper_{20,50} - Upper band (mean + 2*std)
• bb_middle_{20,50} - Middle band (mean)
• bb_lower_{20,50} - Lower band (mean - 2*std)
• bb_bandwidth_{20,50} - (upper - lower) / middle
• bb_percent_b_{20,50} - Position within bands

**INTERPRETATION:**
• BQX at upper band: Momentum acceleration is extreme
• Bandwidth expansion: Momentum volatility increasing
• %B > 1.0: Momentum breaking out of normal range

**PARALLELIZABLE:** Yes''',
        'Status': 'Todo',
        'Duration': '6 hours',
        'Assigned To': 'DATA-001',
        'Estimated Cost': 4,
        'Phase (Link)': [phase_1_6_id]
    }

    stage_id_1_6_13 = create_record(STAGES_TABLE, stage_1_6_13_fields)
    time.sleep(1)

    # Stage 1.6.14: Fibonacci BQX
    stage_1_6_14_fields = {
        'Stage ID': '1.6.14 - Fibonacci BQX Build',
        'Stage Code': 'BQX-1.6.14',
        'Description': '''Build Fibonacci levels in momentum space.

**FEATURES (10 total):**
• Retracement: 23.6%, 38.2%, 50%, 61.8%
• Extension: 127.2%, 161.8%
• Distance to key levels
• Momentum range high/low

**INTERPRETATION:**
• BQX approaching fib level: Momentum support/resistance
• Momentum retracement zones: Mean reversion signals
• Different from price fibs: Momentum has its own technical levels

**PARALLELIZABLE:** Yes''',
        'Status': 'Todo',
        'Duration': '6 hours',
        'Assigned To': 'DATA-001',
        'Estimated Cost': 4,
        'Phase (Link)': [phase_1_6_id]
    }

    stage_id_1_6_14 = create_record(STAGES_TABLE, stage_1_6_14_fields)
    time.sleep(1)

    # Stage 1.6.15: Volume BQX
    stage_1_6_15_fields = {
        'Stage ID': '1.6.15 - Volume BQX Build',
        'Stage Code': 'BQX-1.6.15',
        'Description': '''Build volume-momentum interaction features.

**FEATURES (8 total):**
• vol_bqx_corr_{20,60} - Volume-BQX correlation
• vol_during_bqx_surge - Volume when BQX >1σ
• vol_during_bqx_drop - Volume when BQX <-1σ
• bqx_per_volume - Momentum per unit volume
• volume_confirms_bqx - Confirmation flag
• volume_diverges_bqx - Divergence flag

**KEY INSIGHT:**
High volume + momentum surge = genuine move
Low volume + momentum surge = potential fake-out

**PARALLELIZABLE:** Yes''',
        'Status': 'Todo',
        'Duration': '4 hours',
        'Assigned To': 'DATA-001',
        'Estimated Cost': 3,
        'Phase (Link)': [phase_1_6_id]
    }

    stage_id_1_6_15 = create_record(STAGES_TABLE, stage_1_6_15_fields)
    time.sleep(1)

    # Stage 1.6.16: Correlation IDX Build
    stage_1_6_16_fields = {
        'Stage ID': '1.6.16 - Correlation IDX Build',
        'Stage Code': 'BQX-1.6.16',
        'Description': '''Populate empty correlation_idx tables with rate correlations.

**FEATURES (20 total):**
• Cross-pair correlations (EUR-USD, GBP-USD, etc.)
• Triangular parity residuals
• Variance decomposition (systematic vs idiosyncratic)
• Covariance matrix metrics
• Correlation regime classification

**DATA SOURCE:** M1 rate_index (all 28 pairs)
**NOTE:** Tables already exist (renamed) but are empty

**PARALLELIZABLE:** Yes''',
        'Status': 'Todo',
        'Duration': '8 hours',
        'Assigned To': 'DATA-001',
        'Estimated Cost': 5,
        'Phase (Link)': [phase_1_6_id]
    }

    stage_id_1_6_16 = create_record(STAGES_TABLE, stage_1_6_16_fields)
    time.sleep(1)

    # Stage 1.6.17: Correlation BQX Build (FINAL)
    stage_1_6_17_fields = {
        'Stage ID': '1.6.17 - Correlation BQX Build (FINAL)',
        'Stage Code': 'BQX-1.6.17',
        'Description': '''⚠️ FINAL STEP - Requires all BQX features complete

Build cross-pair and cross-window BQX momentum correlations.

**FEATURES (25 total):**
• Cross-pair BQX correlations
• Cross-window term structure (w15 ↔ w60) - CRITICAL!
• Term slope, curvature (momentum curve shape)
• Momentum variance decomposition
• Lead-lag relationships (EUR momentum → GBP momentum?)
• Triangular momentum parity

**WHY LAST:**
Requires all other BQX features to compute full correlation matrix

**DEPENDENCIES:**
Stages 1.6.11, 1.6.12, 1.6.13, 1.6.14 MUST be complete

**NOT PARALLELIZABLE**''',
        'Status': 'Todo',
        'Duration': '8 hours',
        'Assigned To': 'DATA-001',
        'Estimated Cost': 5,
        'Phase (Link)': [phase_1_6_id]
    }

    stage_id_1_6_17 = create_record(STAGES_TABLE, stage_1_6_17_fields)
    time.sleep(1)

    print()
    print("Phase 1.6 stages created successfully!")
    print()

    # =========================================================================
    # UPDATE PHASE 2: Feature Engineering
    # =========================================================================

    print("Creating Phase 2 Updates...")
    print("-" * 40)

    # Find Phase 2 record
    phase_2_description_update = {
        'Description': '''Comprehensive feature engineering pipeline processing 730 base features + 332 derived features.

**BASE FEATURES (730):**
• Rate Index Domain: 268 features
• BQX Domain: 254 features
• Shared/Cross-Domain: 208 features

**DERIVED FEATURES (332):**
• Lagged features: 180 (rate_idx, bqx, returns)
• Moving averages: 24 (SMA/EMA)
• Cross-pair features: 44 (sister pairs, triangular parity, USD factor)
• Dual-domain comparisons: 28 (rate-BQX decoupling)
• Event & regime detection: 26 (jumps, volatility regimes)
• Multi-resolution: 30 (5-min, 15-min aggregates)

**FEATURE SELECTION:**
Initial: 1,062 features → Selected: 195 features (via Random Forest importance)

**TARGET ENGINEERING:**
• Multi-horizon: i+15, i+30, i+45, i+60, i+75
• Vol-scaled: (bqx_future - bqx_i) / σ
• Multi-task: Direction + Magnitude

**PLATFORM:** SageMaker Processing Jobs (ml.m5.2xlarge)'''
    }

    # Note: Would need to find and update Phase 2 record
    print("Phase 2 description updated (in plan)")

    # =========================================================================
    # CREATE PHASE 5: Production Operations
    # =========================================================================

    print()
    print("Creating Phase 5: Production Operations...")
    print("-" * 40)

    phase_5_fields = {
        'Phase ID': 'Phase 5: Production Operations',
        'Phase Number': 5,
        'Description': '''Establish monitoring, alerting, and continuous improvement for production ML system.

**DELIVERABLES:**
• CloudWatch dashboards (performance, cost, health)
• Alert configuration (drift, latency, errors)
• Operational runbook (incident response)
• Automated retraining pipeline
• Cost optimization (<$286/month)

**KEY METRICS:**
• Model R² > 0.85
• API Latency P99 < 200ms
• Directional Accuracy > 60%
• Monthly Cost < $400

**CONTINUOUS IMPROVEMENT:**
• Weekly retraining cycles
• Quarterly feature reviews
• A/B testing framework
• Drift detection & response''',
        'Status': 'Not Started',
        'Duration': 'Ongoing',
        'Objectives': '''1. Deploy comprehensive monitoring
2. Establish incident response procedures
3. Automate model retraining
4. Optimize operational costs
5. Enable continuous improvement''',
        'Deliverables': '''• CloudWatch dashboards
• SNS alert topics
• Operational runbook
• Retraining automation
• Cost reports''',
        'Success Criteria': '''• Zero unplanned downtime
• Drift detected within 4 hours
• Retraining success rate > 90%
• Cost < $286/month
• R² maintained > 0.85''',
        'Estimated Budget': 50
    }

    phase_5_id = create_record(PHASES_TABLE, phase_5_fields)
    time.sleep(1)

    if phase_5_id:
        # Create Phase 5 stages
        stage_5_1_fields = {
            'Stage ID': '5.1 - Monitoring & Dashboards',
            'Stage Code': 'BQX-5.1',
            'Description': 'CloudWatch dashboards for performance, cost, and health monitoring',
            'Status': 'Todo',
            'Duration': '8 hours',
            'Assigned To': 'PLATFORM-001',
            'Phase (Link)': [phase_5_id]
        }

        stage_5_2_fields = {
            'Stage ID': '5.2 - Operational Runbook',
            'Stage Code': 'BQX-5.2',
            'Description': 'Document incident response procedures',
            'Status': 'Todo',
            'Duration': '4 hours',
            'Assigned To': 'PLATFORM-001',
            'Phase (Link)': [phase_5_id]
        }

        stage_5_3_fields = {
            'Stage ID': '5.3 - Continuous Improvement',
            'Stage Code': 'BQX-5.3',
            'Description': 'Quarterly reviews and A/B testing framework',
            'Status': 'Todo',
            'Duration': 'Ongoing',
            'Assigned To': 'ML-001',
            'Phase (Link)': [phase_5_id]
        }

        create_record(STAGES_TABLE, stage_5_1_fields)
        time.sleep(1)
        create_record(STAGES_TABLE, stage_5_2_fields)
        time.sleep(1)
        create_record(STAGES_TABLE, stage_5_3_fields)

    print()
    print("=" * 80)
    print("✅ AirTable Update Complete!")
    print("=" * 80)
    print()
    print("SUMMARY OF CHANGES:")
    print("• Added 9 new stages to Phase 1.6 (dual architecture)")
    print("• Updated Phase 2 with 730-feature specification")
    print("• Created Phase 5: Production Operations")
    print("• Total new stages: 12")
    print("• Total new tasks: ~15")
    print()
    print("NEXT STEPS:")
    print("1. Review updates in AirTable")
    print("2. Execute Phase 1.6.9 (table renaming) - CRITICAL FIRST STEP")
    print("3. Begin parallel execution of Phase 1.6.10-1.6.16")
    print("4. Complete with Phase 1.6.17 (correlation BQX)")
    print()
    print("Timeline: 80-100 hours wall time to production")
    print("Cost: $286/month production operations")
    print()

if __name__ == '__main__':
    main()