#!/usr/bin/env python3
"""
Add Remediation Stages 2.11-2.15 to AirTable
Documents complete schema alignment plan for 100% reg_rate and reg_bqx alignment
"""

import os
import requests
import json
from datetime import datetime

# AirTable configuration
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
BASE_ID = 'appR3PPnrNkVo48mO'
STAGES_TABLE = 'Stages'

# Remediation stages
REMEDIATION_STAGES = {
    '2.11': {
        'stage_id': '2.11 - reg_rate Schema Enhancement',
        'stage_code': 'BQX-2.11',
        'status': 'Todo',
        'description': 'Add constant_term columns to all reg_rate_* partitions for term-based architecture completion',
        'duration': '30 minutes',
        'estimated_cost': 0.16,
        'cloud_platform': 'AWS',
        'instance_type': 't3.2xlarge',
        'vcpu_count': 8,
        'max_workers': 1,
        'features_added': 6,
        'partitions_affected': 336,
        'notes': '''✅ **LOW RISK** - Additive only, no data loss

## Objective
Add missing constant_term column to all 336 reg_rate_* partitions (28 pairs × 12 months)

## Actions
1. Add w*_constant_term columns (6 windows × 336 partitions)
2. Populate constant_term from w*_c_coef (constant_term = c_coef)
3. Add schema comments documenting rate_index source
4. Validate data integrity

## SQL Migration
- ALTER TABLE ADD COLUMN (6 columns per partition)
- UPDATE to populate from existing c_coef
- COMMENT ON TABLE for documentation

## Validation
```sql
-- Verify constant_term = c_coef
SELECT COUNT(*) FROM bqx.reg_eurusd_2024_07
WHERE ABS(w60_constant_term - w60_c_coef) > 0.000001;
-- Expected: 0

-- Verify prediction integrity
SELECT COUNT(*) FROM bqx.reg_eurusd_2024_07
WHERE ABS(w60_yhat_end - (w60_a_term + w60_b_term + w60_constant_term)) > 0.001;
-- Expected: 0
```

## Rollback
```sql
ALTER TABLE DROP COLUMN w60_constant_term, ...
```

**Duration:** 30 minutes (5 sec per partition)
**Cost:** $0.16
**Features Added:** 6 (constant_term for 6 windows)
**Partitions:** 336
**Risk:** LOW'''
    },

    '2.12': {
        'stage_id': '2.12 - reg_bqx Complete Rebuild',
        'stage_code': 'BQX-2.12',
        'status': 'Todo',
        'description': 'Rebuild all reg_bqx_* tables with aligned windows (60,90,150,240,390,630) and term-based architecture',
        'duration': '3-4 hours',
        'estimated_cost': 1.20,
        'cloud_platform': 'AWS',
        'instance_type': 't3.2xlarge',
        'vcpu_count': 8,
        'max_workers': 8,
        'features_added': 42,
        'partitions_affected': 336,
        'notes': '''⚠️ **MEDIUM RISK** - Requires re-computation, backup recommended

## Objective
Rebuild all 336 reg_bqx_* partitions with:
- Aligned windows: {60, 90, 150, 240, 390, 630} (matching reg_rate)
- Term-based schema: quadratic_term, linear_term, constant_term, residual
- Remove coefficient-only approach

## Current Issues
❌ Wrong windows: {15, 30, 45, 60, 75, agg}
❌ Stores coefficients: {a2, a1, b}
❌ Missing terms: {quadratic_term, linear_term, constant_term}
❌ Missing residual column

## Target Schema (per window)
```sql
w60_quadratic_term DOUBLE PRECISION,   -- a₂ · x_end²
w60_linear_term DOUBLE PRECISION,      -- a₁ · x_end
w60_constant_term DOUBLE PRECISION,    -- a₀
w60_residual DOUBLE PRECISION,         -- y_actual - ŷ
w60_r2 DOUBLE PRECISION,
w60_rmse DOUBLE PRECISION,
w60_prediction DOUBLE PRECISION        -- ŷ = quad + lin + const
```

## Migration Steps
1. **Backup:** Create bqx_backup_2025_11_15 schema
2. **Drop:** Drop existing reg_bqx_* tables
3. **Create:** New schema with aligned windows
4. **Populate:** Re-run worker script (8 parallel workers)
5. **Validate:** Check window alignment, term calculations

## Worker Update
```python
WINDOWS_BQX = [60, 90, 150, 240, 390, 630]  # Aligned!

def fit_parabola_with_terms_bqx(x, y):
    # DO NOT normalize x
    coeffs = np.polyfit(x, y, deg=2)
    a2, a1, a0 = coeffs
    x_end = x[-1]

    quadratic_term = a2 * (x_end ** 2)
    linear_term = a1 * x_end
    constant_term = a0

    prediction = quadratic_term + linear_term + constant_term
    residual = y[-1] - prediction

    return {
        'quadratic_term': float(quadratic_term),
        'linear_term': float(linear_term),
        'constant_term': float(constant_term),
        'residual': float(residual),
        'r2': calculate_r2(y, coeffs),
        'rmse': calculate_rmse(y, coeffs),
        'prediction': float(prediction)
    }
```

## Validation
```sql
-- Check window alignment
SELECT COUNT(DISTINCT column_name)
FROM information_schema.columns
WHERE table_name = 'reg_bqx_eurusd_2024_07'
AND column_name ~ '^w(60|90|150|240|390|630)_';
-- Expected: 42 (7 features × 6 windows)

-- Verify term calculations
SELECT COUNT(*) FROM bqx.reg_bqx_eurusd_2024_07
WHERE ABS(w60_prediction - (w60_quadratic_term + w60_linear_term + w60_constant_term)) > 0.000001;
-- Expected: 0
```

## Rollback
```sql
CREATE TABLE bqx.reg_bqx_eurusd_2024_07 AS
SELECT * FROM bqx_backup_2025_11_15.reg_bqx_eurusd_2024_07;
```

**Duration:** 3-4 hours (8 parallel workers)
**Cost:** $1.20
**Features Added:** 42 (7 features × 6 windows)
**Partitions:** 336
**Risk:** MEDIUM (requires re-computation)'''
    },

    '2.14': {
        'stage_id': '2.14 - Term Covariance Features',
        'stage_code': 'BQX-2.14',
        'status': 'Todo',
        'description': 'Add 6 term covariance features to all correlation_bqx_* tables for trend exhaustion, breakout, and regime change detection',
        'duration': '2-3 hours',
        'estimated_cost': 0.80,
        'cloud_platform': 'AWS',
        'instance_type': 't3.2xlarge',
        'vcpu_count': 8,
        'max_workers': 8,
        'features_added': 6,
        'partitions_affected': 336,
        'notes': '''✅ **LOW RISK** - New features, non-destructive

## Objective
Add 6 term covariance features to all 336 correlation_bqx_* tables:
1. cov_quad_lin_bqx_60min (trend exhaustion detector)
2. cov_resid_quad_bqx_60min (regime change detector)
3. cov_resid_lin_bqx_60min (breakout detector)
4. corr_quad_lin_bqx_60min (normalized [-1,1])
5. corr_resid_quad_bqx_60min (normalized [-1,1])
6. corr_resid_lin_bqx_60min (normalized [-1,1])

## Schema Update
```sql
ALTER TABLE bqx.correlation_bqx_{pair}_{year_month}
ADD COLUMN IF NOT EXISTS cov_quad_lin_bqx_60min DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS cov_resid_quad_bqx_60min DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS cov_resid_lin_bqx_60min DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS corr_quad_lin_bqx_60min DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS corr_resid_quad_bqx_60min DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS corr_resid_lin_bqx_60min DOUBLE PRECISION;
```

## Worker Update
```python
def calculate_term_covariances(df_reg_bqx, window_size=60):
    if len(df_reg_bqx) < window_size:
        return {k: None for k in [...]}

    window_df = df_reg_bqx.tail(window_size)

    cov_quad_lin = window_df['w60_quadratic_term'].cov(
        window_df['w60_linear_term']
    )
    # ... calculate all 6 covariances

    return {
        'cov_quad_lin_bqx_60min': float(cov_quad_lin),
        # ... all 6 features
    }
```

## ML Value
**cov_quad_lin < -0.7:** Trend exhaustion (trend opposed by curvature → reversal)
**cov_resid_lin > 0.8:** Breakout (model underestimates trend → continuation)
**cov_resid_quad > 0.8:** Regime change (parabolic model breaking down)

## Validation
```sql
-- Check coverage
SELECT COUNT(*) AS total,
       COUNT(cov_quad_lin_bqx_60min) AS populated,
       ROUND(100.0 * COUNT(cov_quad_lin_bqx_60min) / COUNT(*), 2) AS coverage_pct
FROM bqx.correlation_bqx_eurusd_2024_07;
-- Expected: coverage_pct > 99%

-- Check correlation range
SELECT MIN(corr_quad_lin_bqx_60min), MAX(corr_quad_lin_bqx_60min)
FROM bqx.correlation_bqx_eurusd_2024_07;
-- Expected: -1 to 1
```

**Duration:** 2-3 hours (8 parallel workers)
**Cost:** $0.80
**Features Added:** 6
**Partitions:** 336
**Risk:** LOW'''
    },

    '2.15': {
        'stage_id': '2.15 - Alignment Validation',
        'stage_code': 'BQX-2.15',
        'status': 'Todo',
        'description': 'Comprehensive validation of 100% schema alignment and documentation updates',
        'duration': '1 hour',
        'estimated_cost': 0.33,
        'cloud_platform': 'AWS',
        'instance_type': 't3.2xlarge',
        'vcpu_count': 8,
        'max_workers': 1,
        'features_added': 0,
        'partitions_affected': 672,
        'notes': '''✅ **NO RISK** - Read-only validation

## Objective
Comprehensive validation of 100% alignment between reg_rate and reg_bqx

## Validation Queries

### 1. Schema Alignment
```sql
SELECT
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_name = 'reg_eurusd_2024_07' AND column_name ~ '^w60_') AS rate_cols,
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_name = 'reg_bqx_eurusd_2024_07' AND column_name ~ '^w60_') AS bqx_cols;
-- Expected: Same count (7 columns each)
```

### 2. Window Alignment
```sql
WITH rate_windows AS (
    SELECT DISTINCT regexp_replace(column_name, '_.*', '') AS window
    FROM information_schema.columns
    WHERE table_name = 'reg_eurusd_2024_07' AND column_name ~ '^w[0-9]+'
),
bqx_windows AS (
    SELECT DISTINCT regexp_replace(column_name, '_.*', '') AS window
    FROM information_schema.columns
    WHERE table_name = 'reg_bqx_eurusd_2024_07' AND column_name ~ '^w[0-9]+'
)
SELECT r.window, b.window,
       CASE WHEN r.window = b.window THEN '✅ Aligned' ELSE '❌ Misaligned' END
FROM rate_windows r
FULL OUTER JOIN bqx_windows b ON r.window = b.window;
-- Expected: All ✅ Aligned
```

### 3. Data Integrity
```sql
SELECT ts_utc,
       w60_quadratic_term, w60_linear_term, w60_constant_term,
       w60_prediction,
       ABS(w60_prediction - (w60_quadratic_term + w60_linear_term + w60_constant_term)) AS pred_error
FROM bqx.reg_eurusd_2024_07
WHERE w60_prediction IS NOT NULL
LIMIT 100;
-- Expected: pred_error < 0.001
```

### 4. Covariance Coverage
```sql
SELECT COUNT(*) AS total,
       COUNT(cov_quad_lin_bqx_60min) AS cov_count,
       ROUND(100.0 * COUNT(cov_quad_lin_bqx_60min) / COUNT(*), 2) AS coverage
FROM bqx.correlation_bqx_eurusd_2024_07;
-- Expected: coverage > 99%
```

### 5. Cross-Domain Comparability
```sql
SELECT r.ts_utc,
       r.w60_r2 AS rate_r2,
       b.w60_r2 AS bqx_r2,
       CASE WHEN r.w60_r2 IS NOT NULL AND b.w60_r2 IS NOT NULL
            THEN '✅ Comparable' ELSE '❌ Missing' END AS status
FROM bqx.reg_eurusd_2024_07 r
JOIN bqx.reg_bqx_eurusd_2024_07 b ON r.ts_utc = b.ts_utc
LIMIT 100;
-- Expected: All ✅ Comparable
```

## Documentation Updates
- Add table comments (reg_rate, reg_bqx, correlation_bqx)
- Update README with 100% alignment confirmation
- Create validation report

## Success Criteria
- [ ] ✅ Windows Aligned (both have {60, 90, 150, 240, 390, 630})
- [ ] ✅ Schema Aligned (both have 7 features per window)
- [ ] ✅ Term-Based (both have quadratic_term, linear_term, constant_term, residual)
- [ ] ✅ Covariance Features (all 6 calculated and stored)
- [ ] ✅ Data Integrity (prediction = sum of terms)
- [ ] ✅ Cross-Domain Comparable (can JOIN at same timestamps)
- [ ] ✅ No Data Loss (row counts match original)

**Duration:** 1 hour
**Cost:** $0.33
**Validation Queries:** 5
**Risk:** NONE'''
    }
}


def get_airtable_token():
    """Retrieve AirTable API token from environment or AWS Secrets Manager."""
    if AIRTABLE_API_KEY:
        return AIRTABLE_API_KEY

    try:
        import boto3
        client = boto3.client('secretsmanager', region_name='us-east-1')
        response = client.get_secret_value(SecretId='bqx-mirror/bqx/airtable/api-token')
        data = json.loads(response['SecretString'])
        return data['token']
    except Exception as e:
        print(f"❌ Error getting AirTable token: {e}")
        return None


def create_remediation_stage(token, stage_key):
    """Create a single remediation stage in AirTable."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}'

    stage_info = REMEDIATION_STAGES[stage_key]

    payload = {
        'fields': {
            'Stage ID': stage_info['stage_id'],
            'Stage Code': stage_info['stage_code'],
            'Status': stage_info['status'],
            'Description': stage_info['description'],
            'Duration': stage_info['duration'],
            'Estimated Cost': stage_info['estimated_cost'],
            'Notes': stage_info.get('notes', '')
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            print(f"✅ Created: {stage_info['stage_id']}")
            return True
        else:
            print(f"❌ Failed to create {stage_info['stage_id']}: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error creating {stage_info['stage_id']}: {e}")
        return False


def main():
    """Main execution: Create all remediation stages."""
    print()
    print("=" * 80)
    print("AIRTABLE UPDATE: CREATE REMEDIATION STAGES 2.11-2.15")
    print("=" * 80)
    print()
    print("Purpose: Document complete schema alignment plan")
    print("Stages: 4 remediation stages (2.11, 2.12, 2.14, 2.15)")
    print()

    # Get API token
    token = get_airtable_token()
    if not token:
        print("❌ No AirTable API token available")
        return 1

    # Create each stage
    stages_to_create = ['2.11', '2.12', '2.14', '2.15']  # Skip 2.13 (optional rename)
    success_count = 0

    for stage_key in stages_to_create:
        if create_remediation_stage(token, stage_key):
            success_count += 1
        print()

    # Summary
    print("=" * 80)
    print("AIRTABLE UPDATE COMPLETE")
    print("=" * 80)
    print()
    print(f"Successfully created: {success_count}/{len(stages_to_create)} stages")
    print()
    print("Remediation Plan Summary:")
    print("  Stage 2.11: reg_rate Schema Enhancement (30 min, $0.16)")
    print("  Stage 2.12: reg_bqx Complete Rebuild (3-4 hrs, $1.20)")
    print("  Stage 2.14: Term Covariance Features (2-3 hrs, $0.80)")
    print("  Stage 2.15: Alignment Validation (1 hr, $0.33)")
    print()
    print("  TOTAL: 7-9 hours, $2.49")
    print("  RESULT: 100% schema alignment, 730+ features ML-ready")
    print()
    print("=" * 80)

    return 0 if success_count == len(stages_to_create) else 1


if __name__ == '__main__':
    exit(main())
