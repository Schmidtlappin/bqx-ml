#!/usr/bin/env python3
"""
Add Issue Remediation Stages to AirTable
Tracks all identified issues and their remediation plans
"""

import os
import requests
import json
from datetime import datetime

# AirTable configuration
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
BASE_ID = 'appR3PPnrNkVo48mO'
STAGES_TABLE = 'Stages'

def create_issue_stages():
    """Create issue remediation stages"""

    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }

    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}'

    stages = []

    # Issue 2: Cost Documentation Update
    stages.append({
        'fields': {
            'Stage ID': '2.11 - Cost Documentation Update',
            'Stage Code': 'BQX-2.11',
            'Status': 'In Progress',
            'Description': 'Update all documentation and AirTable to reflect On-Demand pricing ($57.80) instead of Spot ($19.13)',
            'Duration': '30 minutes',
            'Estimated Cost': 0.00,
            'Notes': '''## Issue: Cost Documentation Mismatch

**Problem:** All docs reference Spot pricing ($19.13), but deployment uses On-Demand ($57.80).

**Impact:** Budget tracking, stakeholder expectations

**Remediation:**
1. Update AirTable Stage 2.10 cost: 19.13 → 57.80
2. Update 6 documentation files
3. Recalculate annual cost comparisons
4. Add "Cost Change Notice" to key docs

**Updated Costs:**
- Phase 2: $19.13 → $57.80
- 1-year total: $200.93 → $239.60
- Annual savings vs current: $2,775.93 → $2,737.26
- Annual savings vs in-place: $1,272.60 → $1,233.93

**Files to Update:**
- docs/REFACTORED_PLAN_SUMMARY.md
- docs/architecture_decision_temporary_ec2.md
- docs/temporary_ec2_implementation_guide.md
- docs/phase_2_ec2_cost_analysis.md
- scripts/airtable/add_phase_2_infrastructure_stage.py
- scripts/infrastructure/launch_temporary_phase2_ec2.sh

**Priority:** HIGH
**Risk:** LOW (documentation only)
**Owner:** Infrastructure Team
'''
        }
    })

    # Issue 3: Phase 2 Worker Scripts Development
    stages.append({
        'fields': {
            'Stage ID': '2.12 - Phase 2 Worker Scripts Development',
            'Stage Code': 'BQX-2.12',
            'Status': 'In Progress',
            'Description': 'Develop 6 missing worker scripts for Phase 2 parallel execution (Stages 2.2, 2.3, 2.4, 2.6, 2.8, 2.9)',
            'Duration': '2-3 days',
            'Estimated Cost': 0.00,
            'Notes': '''## Issue: Missing Phase 2 Worker Scripts

**Problem:** Orchestration script references 6 workers that don't exist yet.

**Impact:** Blocks Phase 2 execution after quota approval

**Missing Workers:**
1. ✅ Stage 2.2 - Technical Indicators (15 hrs, 8 cores) - PRIORITY 1
2. ⏳ Stage 2.4 - Arbitrage Detection (2 days, 2 cores)
3. ⏳ Stage 2.8 - Enhanced R²/RMSE (1 day, 2 cores)
4. ⏳ Stage 2.3 - Cross-Pair Indices (2 days)
5. ⏳ Stage 2.6 - Temporal Causality (1 day)
6. ⏳ Stage 2.9 - Regime Detection (2 days)

**Development Plan:**

**Phase 1 (Critical Path):**
- Stage 2.2: Technical Indicators
  - RSI, MACD, Bollinger Bands, ATR, Stochastic
  - Template: Track 2 parallel worker
  - Complexity: MEDIUM
  - Duration: 1 day development

**Phase 2 (Parallel Tracks):**
- Stage 2.4: Arbitrage Detection (HIGH complexity)
- Stage 2.8: Enhanced R²/RMSE (LOW complexity)
- Duration: 1 day each

**Phase 3 (Sequential):**
- Stage 2.3: Cross-Pair Currency Indices (MEDIUM)
- Stage 2.6: Temporal Causality (MEDIUM)
- Stage 2.9: Regime Detection (HIGH)
- Duration: 1 day each

**Pattern (from Track 2):**
- Parallel execution with multiprocessing
- Partition-based (336 partitions)
- Progress logging
- Error handling and retry
- Connection pooling

**Action Items:**
- [ ] Create worker template
- [ ] Implement Stage 2.2 (Priority 1)
- [ ] Implement Stages 2.4, 2.8 (Priority 2)
- [ ] Implement Stages 2.3, 2.6, 2.9 (Priority 3)
- [ ] Create unit tests
- [ ] Update orchestration script

**Priority:** HIGH
**Risk:** MEDIUM (well-defined, proven pattern)
**Owner:** ML Engineering Team
'''
        }
    })

    # Issue 4: Validation Scripts Creation
    stages.append({
        'fields': {
            'Stage ID': '2.13 - Validation Scripts Creation',
            'Stage Code': 'BQX-2.13',
            'Status': 'In Progress',
            'Description': 'Create missing validation and helper SQL scripts for Phase 2 data quality assurance',
            'Duration': '1 day',
            'Estimated Cost': 0.00,
            'Notes': '''## Issue: Missing Validation Scripts

**Problem:** Orchestration references validation scripts that don't exist.

**Impact:** Manual validation required, automated QA missing

**Missing Scripts:**
1. scripts/validation/track_2_validation_queries.sql
2. scripts/refactor/stage_2_3_4_create_helper_views.sql

**Validation Script Requirements:**
- Row count validation (2,016,000 rows/partition expected)
- NULL value checks
- Range validation (R², RMSE bounds)
- Partition completeness checks
- Timestamp consistency verification

**Helper Views Requirements:**
- Materialized views for currency indices
- Helper views for arbitrage calculations
- Performance optimization views
- Cross-partition aggregation views

**Action Items:**
- [ ] Extract validation queries from documentation
- [ ] Create consolidated validation SQL script
- [ ] Create helper views SQL script
- [ ] Test validation on Track 2 data
- [ ] Document expected outputs
- [ ] Add to orchestration script

**Priority:** MEDIUM
**Risk:** LOW (queries exist, need consolidation)
**Owner:** Data Engineering Team
'''
        }
    })

    # Issue 5: S3 Export Script Development
    stages.append({
        'fields': {
            'Stage ID': '2.14 - S3 Export Script Development',
            'Stage Code': 'BQX-2.14',
            'Status': 'In Progress',
            'Description': 'Develop S3 Parquet export script for Phase 2 final deliverable (Stage 2.7)',
            'Duration': '1-2 days',
            'Estimated Cost': 5.00,
            'Notes': '''## Issue: S3 Export Script Missing

**Problem:** Phase 2 final stage (2.7) requires S3 export that doesn't exist yet.

**Impact:** Blocks Phase 2 final deliverable and Phase 3 data ingestion

**Requirements:**
- Export format: Parquet (Snappy compression)
- Volume: 40-50 GB
- Partitioning: By currency pair + date
- Schema: Preserve all 1080 features
- Validation: Row counts, schema checks

**Implementation:**
- Use: pandas.to_parquet() or pyarrow
- Parallelization: Export by partition (336 partitions)
- Progress: Real-time logging
- Validation: Automated checks
- Duration: 4-6 hours execution

**S3 Configuration:**
- Bucket: TBD (identify or create)
- Path structure: s3://bucket/bqx-features/v1/{pair}/{date}/
- Access: IAM role for trillium-phase2-worker
- Lifecycle: Retain indefinitely

**Action Items:**
- [ ] Identify or create S3 bucket
- [ ] Configure IAM permissions
- [ ] Create export script (Python)
- [ ] Test with sample data
- [ ] Optimize for 40-50 GB dataset
- [ ] Add to Stage 2.7 orchestration
- [ ] Create validation script

**Estimated Cost:**
- S3 Storage: $1.15/month (50 GB @ $0.023/GB)
- Data Transfer: $0.00 (within AWS)
- Requests: $0.05 (PUT/LIST)
- **Total:** ~$5.00 (one-time setup + 1 month)

**Priority:** MEDIUM
**Risk:** LOW (standard export operation)
**Owner:** Data Engineering Team
'''
        }
    })

    # Issue 6: Documentation Cleanup
    stages.append({
        'fields': {
            'Stage ID': '2.15 - Documentation Cleanup',
            'Stage Code': 'BQX-2.15',
            'Status': 'In Progress',
            'Description': 'Archive outdated documentation and create index for active docs',
            'Duration': '1 hour',
            'Estimated Cost': 0.00,
            'Notes': '''## Issue: Workspace Documentation Clutter

**Problem:** 80+ markdown files with overlapping content and outdated references.

**Impact:** Developer productivity, documentation clarity

**Cleanup Plan:**

**Archive Criteria:**
- Pre-Phase 1 planning docs (historical reference)
- Superseded plans (old Phase 2 strategies)
- Interim reports (already consolidated)
- Dated gap analyses (issues resolved)

**Files to Archive (~40 files):**
- Old feature development plans (pre-consolidation)
- Interim gap assessments (superseded)
- Historical phase completion reports
- Deprecated architecture docs

**Keep Active (~30 files):**
- Current architecture decisions
- Phase 2/3 execution plans
- Infrastructure guides (temporary EC2, etc.)
- SageMaker deployment plans
- Active issue tracking
- Cost analysis (current)

**Action Items:**
- [ ] Create docs/archive_2025_11_14 directory
- [ ] Move 40+ outdated docs to archive
- [ ] Create docs/README.md with active doc index
- [ ] Update cross-references to archived docs
- [ ] Add archive policy to README

**Priority:** LOW
**Risk:** VERY LOW (archival only, no deletion)
**Owner:** Documentation Team
'''
        }
    })

    # Create all stages
    created_stages = []
    for i, stage in enumerate(stages, 1):
        try:
            response = requests.post(url, headers=headers, json=stage)

            if response.status_code in [200, 201]:
                result = response.json()
                created_stages.append(result)
                print(f"✅ Created Stage {stage['fields']['Stage ID']}")
            else:
                print(f"❌ Failed to create Stage {stage['fields']['Stage ID']}: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Error creating stage {i}: {e}")

    return created_stages

def update_stage_2_10_cost():
    """Update Stage 2.10 cost from $19.13 to $57.80"""

    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }

    # First, find Stage 2.10
    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}'
    params = {
        'filterByFormula': "{{Stage ID}} = '2.10 - Infrastructure Management'"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            records = response.json().get('records', [])

            if records:
                record_id = records[0]['id']
                update_url = f'{url}/{record_id}'

                # Update cost and add note about On-Demand pricing
                update_data = {
                    'fields': {
                        'Estimated Cost': 57.80,
                        'Notes': records[0]['fields']['Notes'] + '''

---

## COST UPDATE: 2025-11-14

**Original Plan:** c7i.8xlarge Spot (~$0.45/hr) = $19.13
**Actual Deployment:** c7i.8xlarge On-Demand ($1.36/hr) = $57.80
**Reason:** Spot capacity unavailable in us-east-1a, us-east-1b, us-east-1c

**Updated Costs:**
- Phase 2 execution: $57.80 (On-Demand guaranteed capacity)
- Ongoing (trillium-master): $15/month
- Annual total: $239.60 (vs $200.93 with Spot = +$38.67)
- Annual savings vs current: $2,737.26 (vs $2,775.93 with Spot)
- Annual savings vs in-place: $1,233.93 (vs $1,272.60 with Spot)

**Trade-off Analysis:**
- Reliability: HIGHER (guaranteed capacity vs. Spot interruption risk)
- Cost: +$38.67 one-time (+202%)
- Annual impact: Minimal (+$38.67 vs. $2,737 total savings = 1.4%)
- Decision: Acceptable trade-off for guaranteed Phase 2 completion
'''
                    }
                }

                update_response = requests.patch(update_url, headers=headers, json=update_data)

                if update_response.status_code == 200:
                    print("✅ Updated Stage 2.10 cost: $19.13 → $57.80")
                    print("✅ Added On-Demand pricing explanation")
                    return True
                else:
                    print(f"❌ Failed to update Stage 2.10: {update_response.status_code}")
                    print(f"   Response: {update_response.text}")
                    return False
            else:
                print("❌ Stage 2.10 not found in AirTable")
                return False
        else:
            print(f"❌ Failed to query Stage 2.10: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error updating Stage 2.10: {e}")
        return False

def main():
    """Main execution"""
    print()
    print("=" * 80)
    print("AIRTABLE UPDATE: ISSUE REMEDIATION STAGES")
    print("=" * 80)
    print()

    print("Creating issue remediation stages...")
    print()

    created = create_issue_stages()

    print()
    print("=" * 80)
    print(f"CREATED {len(created)} ISSUE REMEDIATION STAGES")
    print("=" * 80)
    print()

    for stage in created:
        print(f"  - {stage['fields']['Stage ID']}")

    print()
    print("Updating Stage 2.10 cost...")
    print()

    if update_stage_2_10_cost():
        print()
        print("=" * 80)
        print("AIRTABLE UPDATE COMPLETE")
        print("=" * 80)
        print()
        print("Summary:")
        print(f"  ✅ Created {len(created)} issue remediation stages")
        print("  ✅ Updated Stage 2.10 cost ($19.13 → $57.80)")
        print()
    else:
        print()
        print("=" * 80)
        print("AIRTABLE UPDATE PARTIAL")
        print("=" * 80)
        print()
        print(f"  ✅ Created {len(created)} issue remediation stages")
        print("  ❌ Failed to update Stage 2.10 cost")
        print()

if __name__ == '__main__':
    main()
