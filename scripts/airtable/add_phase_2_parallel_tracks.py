#!/usr/bin/env python3
"""
Add Phase 2 Parallel Execution Plan to AirTable
Includes 3 parallel tracks within Stage 2.1 and all subsequent stages
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
print("ADDING PHASE 2: PARALLEL EXECUTION PLAN TO AIRTABLE")
print("=" * 80)
print()

# Phase 2 stages matching our parallel execution plan
stages = {
    '2.1.1': {
        'name': 'Track 1: Wave 1 Feature Population',
        'description': '''Implement bollinger_bqx, statistics_bqx, and technical indicators workers.

**Timeline:** 9 days
**Features Added:** 94 features
**Progress:** 159 → 253 features (23.9%)

**Components:**
- Day 1-2: Bollinger BQX Worker (10 features, 700 tables)
- Day 3-4: Statistics BQX Worker (24 features, 700 tables)
- Day 5-9: Technical Indicators Worker (60 features, 1,400 tables)

**Worker Scripts:**
- populate_bollinger_bqx_worker.py
- populate_statistics_bqx_worker.py
- populate_technical_indicators_worker.py

**Dependencies:** M1 BQX momentum data, rate_index data
**Resource Usage:** 2-3 workers, 5-8 GB RAM, 25-30% CPU avg''',
        'duration': '9 days',
        'status': 'Todo'
    },
    '2.1.2': {
        'name': 'Track 2: Regression Features',
        'description': '''Create and populate regression feature tables (reg_rate, reg_bqx).

**Timeline:** 11 days (1 day create + 10 days populate)
**Features Added:** 180 features
**Progress:** 253 → 433 features (40.8%)

**Components:**
- Day 1: Create 1,064 tables (28 pairs × 38 partitions)
- Day 2-11: Populate regression features (parabolic fits)

**Features per Domain:** 90 (6 windows × 15 metrics)
- Parabolic coefficients: a2, a1, b
- Fit quality: R², RMSE, residuals
- Prediction intervals and metrics

**Worker Scripts:**
- create_regression_tables.sql
- populate_regression_features_worker.py

**Dependencies:** M1 rate_index, M1 BQX momentum
**Resource Usage:** 3-4 workers, 8-12 GB RAM, 40-50% CPU avg (most intensive track)
**Complexity:** HIGH - polynomial regression, rolling windows''',
        'duration': '11 days',
        'status': 'Todo'
    },
    '2.1.3': {
        'name': 'Track 3: MVP Pipeline (159 Features)',
        'description': '''Build complete extraction/lagging/selection/dataset pipeline with existing 159 features.

**Timeline:** 18 days
**Output:** End-to-end ML pipeline validated

**Components:**
- Day 1-5: Feature Extraction (DB → Parquet, 28 pairs × 159 columns)
- Day 6-8: Lagging Strategy (159 → 576 features with 3 lags)
- Day 9-12: Feature Selection (Random Forest, 576 → 100 top features)
- Day 13-18: Dataset Creation + Validation (train/val/test splits)

**Pipeline Scripts:**
- extract_features_from_db.py
- apply_lagging_strategy.py
- select_features_rf.py
- create_datasets.py
- test_mvp_pipeline.py

**Dependencies:** Existing 159 populated features (bollinger_rate, statistics_rate, volume, spread, time)
**Resource Usage:** 1-2 workers, 5-8 GB RAM, 20-30% CPU avg
**Output:** Train/val/test Parquet files, baseline model, validated pipeline
**Validation:** No future leakage, R² > 0.1 on test set''',
        'duration': '18 days',
        'status': 'Todo'
    },
    '2.2': {
        'name': 'Feature Extraction (433 Features)',
        'description': '''Extract all 433 populated features from database into unified datasets.

**Timeline:** 2 weeks (14 days)
**Input:** 433 features in database (after Tracks 1-2 complete)
**Output:** 28 Parquet files (one per pair), 433 columns each

**Tasks:**
1. Database Query Optimization (2 days)
   - Efficient multi-table joins
   - Composite indexes for ts_utc + pair
   - Batch queries to minimize round-trips

2. Feature Extraction Pipeline (3 days)
   - Extract all features per pair
   - Handle missing values (forward fill, interpolation)
   - Validate temporal alignment

3. Data Validation (3 days)
   - Check for NaN/inf values
   - Verify temporal causality (no future leakage)
   - Statistical sanity checks

4. Feature Dataset Creation (4 days)
   - Combine into single dataframe per pair
   - Align timestamps across feature families
   - Handle different partition ranges (rate vs bqx)

**Dependencies:** Stage 2.1 complete (433 features populated)
**Output:** 28 feature datasets, ~433 columns each''',
        'duration': '14 days',
        'status': 'Todo'
    },
    '2.3': {
        'name': 'Lagging Strategy',
        'description': '''Apply temporal lags to create ~1,100 features from 433 base features.

**Timeline:** 1 week (7 days)
**Input:** 433 base features per pair
**Output:** ~1,100 features per pair

**Lagging Rules:**
- Laggable features (216): Apply 4 lags (60, 120, 180, 240 min)
  - Result: 216 × 5 (base + 4 lags) = 1,080 features
- Non-laggable features (217): Keep as-is
  - Time & calendar (categorical, current state only)
  - Some cross-sectional features
- Temporal causality: 61-min lag for w60/agg families
  - Prevents future information leakage

**Implementation:**
- Pandas shift operation
- Validate no future leakage
- Handle edge cases (start of series)

**Dependencies:** Stage 2.2 complete (feature extraction)
**Output:** ~1,100 features per pair with temporal dependencies''',
        'duration': '7 days',
        'status': 'Todo'
    },
    '2.4': {
        'name': 'Feature Selection',
        'description': '''Select top ~250 features from ~1,100 using Random Forest importance.

**Timeline:** 2 weeks (14 days)
**Input:** ~1,100 features per pair
**Output:** ~250 selected features per pair

**Method: Random Forest Feature Importance**

1. Train Random Forest (2 days)
   - Use all ~1,100 features
   - Target: BQX change at each horizon (15/30/45/60/75 min)
   - Multi-output Random Forest
   - 100 trees, max_depth=10

2. Compute Importance Scores (1 day)
   - Extract feature_importances_
   - Aggregate across all 5 target horizons
   - Rank features by cumulative importance

3. Select Top 250 (1 day)
   - Cumulative importance > 95% threshold
   - Ensure dual architecture balance (100 rate + 100 bqx minimum)

4. Validate Selection (3 days)
   - Retrain with selected 250 features
   - Compare R² to full model (should be >95% of full R²)
   - Check domain coverage

5. Cross-Validation (2 days)
   - 5-fold cross-validation
   - Verify feature importance stability

**Dependencies:** Stage 2.3 complete (lagging)
**Output:** 250 selected features per pair with importance scores''',
        'duration': '14 days',
        'status': 'Todo'
    },
    '2.5': {
        'name': 'Dataset Creation',
        'description': '''Create train/val/test datasets for model training.

**Timeline:** 1 week (7 days)
**Input:** 250 selected features per pair
**Output:** Production-ready datasets for 28 pairs

**Tasks:**

1. Split Strategy (1 day)
   - Temporal split: 70/15/15 (train/val/test)
   - No shuffling to maintain temporal causality
   - Train: First 70% of timeline
   - Val: Next 15%
   - Test: Last 15%

2. Target Engineering (2 days)
   - Multi-horizon targets: BQX change at 15/30/45/60/75 min
   - Classification targets: Direction (up/down/neutral)
   - Volatility-scaled targets: BQX_change / realized_volatility

3. Feature Scaling (1 day)
   - StandardScaler per feature
   - Fit on train, transform val/test
   - Save scalers for inference

4. Final Dataset Export (2 days)
   - Save as Parquet (compressed)
   - Structure: train/{pair}.parquet, val/{pair}.parquet, test/{pair}.parquet
   - Metadata: feature names, scaler parameters

**Dependencies:** Stage 2.4 complete (feature selection)
**Output:** Train/val/test Parquet files, scalers, metadata
**Deliverable:** READY FOR PHASE 3 MODEL TRAINING''',
        'duration': '7 days',
        'status': 'Todo'
    }
}

stages_url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}'

print("Step 1: Check existing Phase 2 stages")
print("-" * 80)

existing_stages = {}
for stage_id in stages.keys():
    params = {'filterByFormula': f"FIND('{stage_id}', {{Stage ID}}) > 0"}
    response = requests.get(stages_url, headers=headers, params=params)

    if response.status_code == 200:
        records = response.json()['records']
        if records:
            existing_stages[stage_id] = records[0]['id']
            print(f"✓ Stage {stage_id} already exists")
        else:
            print(f"✗ Stage {stage_id} needs to be created")
    else:
        print(f"❌ Error checking stage {stage_id}: {response.status_code}")

print()
print("Step 2: Create new Phase 2 stages")
print("-" * 80)

created_count = 0
skipped_count = 0

for stage_id, stage_info in stages.items():
    if stage_id in existing_stages:
        print(f"⏭️  Skipping Stage {stage_id} (already exists)")
        skipped_count += 1
        continue

    print(f"\nCreating Stage {stage_id}: {stage_info['name']}")
    print("-" * 40)

    stage_data = {
        'Stage ID': f"{stage_id} - {stage_info['name']}",
        'Stage Code': f"BQX-{stage_id}",
        'Description': stage_info['description'],
        'Status': stage_info['status'],
        'Duration': stage_info['duration'],
    }

    payload = {'fields': stage_data}

    try:
        create_response = requests.post(stages_url, headers=headers, json=payload)

        if create_response.status_code == 200:
            new_record = create_response.json()
            new_record_id = new_record['id']
            print(f"✅ Stage {stage_id} created successfully!")
            print(f"   Record ID: {new_record_id}")
            print(f"   Duration: {stage_info['duration']}")
            created_count += 1
        else:
            print(f"❌ Error creating stage: {create_response.status_code}")
            print(f"   Response: {create_response.text}")
    except Exception as e:
        print(f"❌ Exception creating stage: {str(e)}")

print()
print("=" * 80)
print("UPDATE COMPLETE")
print("=" * 80)
print()
print(f"Stages created: {created_count}")
print(f"Stages skipped (already exist): {skipped_count}")
print()
print("PHASE 2: PARALLEL EXECUTION PLAN SUMMARY")
print("=" * 80)
print()
print("Stage 2.1: Feature Population Workers (3 Parallel Tracks)")
print("  └─ Track 1: Wave 1 features (9 days, 94 features)")
print("  └─ Track 2: Regression features (11 days, 180 features)")
print("  └─ Track 3: MVP pipeline (18 days, validated pipeline)")
print("  CONVERGENCE: Day 21 → 433 features + operational pipeline")
print()
print("Stage 2.2: Feature Extraction (14 days)")
print("  └─ Extract 433 features → 28 Parquet files")
print()
print("Stage 2.3: Lagging Strategy (7 days)")
print("  └─ Apply temporal lags → ~1,100 features")
print()
print("Stage 2.4: Feature Selection (14 days)")
print("  └─ Random Forest selection → ~250 features")
print()
print("Stage 2.5: Dataset Creation (7 days)")
print("  └─ Train/val/test splits → Ready for Phase 3")
print()
print("=" * 80)
print("TOTAL PHASE 2 DURATION: 21 days (parallel) + 42 days (sequential)")
print("DELIVERABLE: Production-ready ML pipeline with 250 selected features")
print("=" * 80)
