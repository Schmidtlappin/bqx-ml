#!/usr/bin/env python3
"""
Add Gap Remediation Plan to BQX ML Airtable

Strategic plan to address 111-feature gap analysis with parallel execution tracks:
- Track 1: Unblocked features (66) - can start immediately
- Track 2: OHLC index columns (blocker for 45 features)
- Track 3: Blocked features (45) - after OHLC index ready

Integrates with ongoing REG backfill for maximum CPU utilization.
"""

import os
import requests
from datetime import datetime

# Airtable configuration
BASE_ID = "appR3PPnrNkVo48mO"
API_KEY = os.environ.get("AIRTABLE_API_KEY")

if not API_KEY:
    print("ERROR: AIRTABLE_API_KEY environment variable not set")
    print("Set with: export AIRTABLE_API_KEY='your_key_here'")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def get_phase_1_5_record():
    """Get Phase 1.5 record ID for dependency linking"""
    url = f"https://api.airtable.com/v0/{BASE_ID}/Phases"
    params = {
        "filterByFormula": "FIND('Phase 1.5', {Phase ID}) > 0",
        "maxRecords": 1
    }

    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code == 200:
        data = response.json()
        if data.get("records"):
            return data["records"][0]["id"]

    return None

def create_phase_1_6():
    """Create Phase 1.6: Gap Remediation (Parallel Execution)"""

    phase_data = {
        "fields": {
            "Phase ID": "Phase 1.6: Gap Remediation & OHLC Index Enhancement",
            "Description": (
                "Strategic remediation plan addressing 111-feature gap analysis. "
                "Executes in parallel with REG backfill (Stage 1.5.5) to maximize CPU utilization. "
                "\n\n"
                "**Dependencies:** Phase 1.5 (REG backfill in progress)\n\n"
                "**Parallel Tracks:**\n"
                "• Track 1: 66 unblocked features (40% CPU) - Immediate execution\n"
                "• Track 2: OHLC index columns (low CPU) - Unblocks 45 features\n"
                "• Track 3: REG backfill continues (50-60% CPU) - In progress\n"
                "• Track 4: 45 blocked features - After OHLC index ready\n"
                "\n"
                "**Critical Path:** OHLC index blocks 41% of Phase 2 features (ADX, ATR, Stochastic, etc.)"
            ),
            "Status": "Not Started",
            "Duration": "28 hours",
            "Success Criteria": (
                "1. OHLC index columns added to all 28 M1 pairs\n"
                "2. 66 unblocked features computed and stored\n"
                "3. All feature storage tables created\n"
                "4. Feature computation workers tested\n"
                "5. Zero blocking gaps remaining for Phase 2"
            ),
            "Objectives": (
                "**Gap Analysis Summary:**\n"
                "- Total features planned: 111\n"
                "- Unblocked (can compute now): 66 (59%)\n"
                "- Blocked by OHLC index: 45 (41%)\n"
                "\n"
                "**Resource Optimization:**\n"
                "- Sequential execution: ~50 hours wall time\n"
                "- Parallel execution: ~28 hours wall time (44% time savings)\n"
                "- CPU utilization: 90% (Track 1: 40% + REG: 50%)\n"
                "\n"
                "**Risk Mitigation:**\n"
                "- Multiple independent tracks\n"
                "- If Track 1 fails, Track 2 progresses\n"
                "- OHLC index is separate from feature computation\n"
                "- Can rollback OHLC schema if needed"
            )
        }
    }

    url = f"https://api.airtable.com/v0/{BASE_ID}/Phases"
    response = requests.post(url, headers=HEADERS, json=phase_data)

    if response.status_code == 200:
        phase_record = response.json()
        print(f"✓ Created Phase 1.6: {phase_record['id']}")
        return phase_record['id']
    else:
        print(f"✗ Failed to create Phase 1.6: {response.status_code}")
        print(response.text)
        return None

def create_stages(phase_record_id):
    """Create 5 strategic stages"""

    stages = [
        {
            "Stage ID": "Stage 1.6.1",
            # Stage name merged into Stage ID and Description,
            "Description": (
                "Add high_index, low_index, open_index columns to all 28 M1 tables. "
                "This UNBLOCKS 45 technical indicators (41% of Phase 2 features).\n\n"
                "**What:** Add 3 normalized index columns per M1 table\n"
                "**Why:** Technical indicators (ADX, ATR, Stochastic, Ichimoku, etc.) require OHLC index data\n"
                "**Impact:** Unblocks $45/111$ features\n\n"
                "**Formula:**\n"
                "• high_index = (high / baseline_rate) × 100\n"
                "• low_index = (low / baseline_rate) × 100\n"
                "• open_index = (open / baseline_rate) × 100\n\n"
                "**Execution:** Parallel with REG backfill, minimal CPU impact"
            ),
            "Duration": "3 hours"",
            "Phase": [phase_record_id]
        },
        {
            "Stage ID": "Stage 1.6.2",
            # Stage name merged into Stage ID and Description,
            "Description": (
                "Create database tables and schemas for storing computed Phase 2 features.\n\n"
                "**Tables to Create:**\n"
                "• volume_features_{pair} (28 tables) - Volume-based features\n"
                "• time_features_{pair} (28 tables) - Temporal/cyclical features\n"
                "• currency_indices (1 table) - Synthetic currency strength indices\n"
                "• spread_features_{pair} (28 tables) - Bid/ask microstructure\n"
                "• technical_indicators_{pair} (28 tables) - TA-Lib indicators\n"
                "• correlation_features_{pair} (28 tables) - Cross-pair correlations\n"
                "• statistics_features_{pair} (28 tables) - Higher-order stats\n\n"
                "**Total:** 197 new tables\n\n"
                "**Schema Design:**\n"
                "• Partitioned by month (same as BQX/REG)\n"
                "• Indexed on ts_utc (primary key)\n"
                "• Foreign key to M1 tables (referential integrity)\n"
                "• Optimized for time-series queries"
            ),
            "Duration": "4 hours"",
            "Phase": [phase_record_id]
        },
        {
            "Stage ID": "Stage 1.6.3",
            # Stage name merged into Stage ID and Description,
            "Description": (
                "Compute 66 features that have NO dependencies on OHLC index columns. "
                "Executes in PARALLEL with REG backfill using 40% CPU.\n\n"
                "**Feature Breakdown:**\n"
                "• Volume features: 10 (from M1.volume)\n"
                "• Time features: 8 (cyclical encoding of timestamps)\n"
                "• Currency strength indices: 3 (synthetic from 28 pairs)\n"
                "• Spread/microstructure: 20 (from M1 bid/ask/spread)\n"
                "• Cross-pair correlations: 15 (from completed BQX tables)\n"
                "• Higher-order statistics: 5 (skewness, kurtosis, etc.)\n"
                "• Bollinger Bands: 5 (only needs rate_index)\n\n"
                "**Parallel Execution Strategy:**\n"
                "• Worker uses 8-10 threads (40% CPU)\n"
                "• REG backfill continues (50-60% CPU)\n"
                "• Total CPU: ~90% utilization\n"
                "• I/O independent (reads from different tables)"
            ),
            "Duration": "18 hours", Storage tables created (Stage 1.6.2)"\n"
                "5. Feature catalog documentation"
            ),
            "Phase": [phase_record_id]
        },
        {
            "Stage ID": "Stage 1.6.4",
            # Stage name merged into Stage ID and Description,
            "Description": (
                "Compute 45 features that REQUIRE OHLC index columns. "
                "Executes AFTER Stage 1.6.1 (OHLC index) completes.\n\n"
                "**Feature Breakdown:**\n"
                "• Momentum indicators: 11 (RSI works with rate_index, but Stochastic needs high/low_index)\n"
                "• Trend indicators: 13 (ADX, Parabolic SAR, Ichimoku all need OHLC index)\n"
                "• Volatility indicators: 10 (ATR, Keltner, Donchian need high/low_index)\n"
                "• Regime features: 3 (trend_regime, consolidation_breakout depend on ADX/ATR)\n"
                "• Partial features: 8 (various TA-Lib indicators)\n\n"
                "**Critical Dependency:**\n"
                "• MUST wait for Stage 1.6.1 to complete\n"
                "• Cannot parallelize with Track 1 (different data source)\n\n"
                "**TA-Lib Integration:**\n"
                "• Install TA-Lib library\n"
                "• Compute all indicators on *_index columns (not raw rates)\n"
                "• Ensures cross-pair comparability"
            ),
            "Duration": "17 hours", Storage tables (Stage 1.6.2)"\n"
                "5. Feature importance preliminary analysis"
            ),
            "Phase": [phase_record_id]
        },
        {
            "Stage ID": "Stage 1.6.5",
            # Stage name merged into Stage ID and Description,
            "Description": (
                "Comprehensive validation that ALL gaps from gap analysis are addressed. "
                "Prepare Phase 2 for immediate execution.\n\n"
                "**Validation Checklist:**\n"
                "1. OHLC index columns exist in all 28 M1 tables (84 columns total)\n"
                "2. All 111 features computed and stored\n"
                "3. Feature values within expected ranges\n"
                "4. No NULL values except at partition starts (expected lookback NULLs)\n"
                "5. Cross-pair comparison works (EURUSD vs USDJPY features comparable)\n"
                "6. Storage tables optimized (indexes, partitions)\n"
                "7. Worker scripts tested and documented\n\n"
                "**Documentation Deliverables:**\n"
                "• Gap remediation completion report\n"
                "• Feature catalog (all 111 features documented)\n"
                "• Schema documentation updates\n"
                "• Worker script documentation\n"
                "• Phase 2 readiness assessment"
            ),
            "Duration": "6 hours"\n"
                "2. Feature catalog with 111 features fully documented\n"
                "3. Validation test suite (automated checks)\n"
                "4. Phase 2 readiness certification\n"
                "5. Lessons learned from gap remediation"
            ),
            "Phase": [phase_record_id]
        }
    ]

    created_stage_ids = []

    for stage in stages:
        url = f"https://api.airtable.com/v0/{BASE_ID}/Stages"
        response = requests.post(url, headers=HEADERS, json={"fields": stage})

        if response.status_code == 200:
            stage_record = response.json()
            created_stage_ids.append(stage_record['id'])
            print(f"✓ Created {stage['Stage ID']}: {stage_record['id']}")
        else:
            print(f"✗ Failed to create {stage['Stage ID']}: {response.status_code}")
            print(response.text)

    return created_stage_ids

def create_tasks(stage_ids):
    """Create detailed tasks for each stage"""

    # Map stage IDs to stage numbers
    stage_map = {
        "1.6.1": stage_ids[0] if len(stage_ids) > 0 else None,
        "1.6.2": stage_ids[1] if len(stage_ids) > 1 else None,
        "1.6.3": stage_ids[2] if len(stage_ids) > 2 else None,
        "1.6.4": stage_ids[3] if len(stage_ids) > 3 else None,
        "1.6.5": stage_ids[4] if len(stage_ids) > 4 else None,
    }

    tasks = [
        # Stage 1.6.1 tasks (OHLC Index)
        {
            "Task ID": "TSK-1.6.1.1",
            "Task Name": "Create OHLC index SQL schema script",
            "Description": "Write SQL to add high_index, low_index, open_index columns to all 28 M1 tables",
            "Estimated Duration (hours)": 1,
            "Status": "Not Started",
            "Stage": [stage_map["1.6.1"]] if stage_map["1.6.1"] else []
        },
        {
            "Task ID": "TSK-1.6.1.2",
            "Task Name": "Backfill OHLC index values",
            "Description": "Populate new index columns from existing M1.high/low/open using baseline_rate normalization",
            "Estimated Duration (hours)": 1.5,
            "Status": "Not Started",
            "Stage": [stage_map["1.6.1"]] if stage_map["1.6.1"] else []
        },
        {
            "Task ID": "TSK-1.6.1.3",
            "Task Name": "Create indexes on OHLC index columns",
            "Description": "Add BTREE indexes for query optimization on high_index, low_index, open_index",
            "Estimated Duration (hours)": 0.5,
            "Status": "Not Started",
            "Stage": [stage_map["1.6.1"]] if stage_map["1.6.1"] else []
        },

        # Stage 1.6.2 tasks (Storage Infrastructure)
        {
            "Task ID": "TSK-1.6.2.1",
            "Task Name": "Design feature storage schemas",
            "Description": "Create SQL schemas for 7 feature table types with partitioning and indexing",
            "Estimated Duration (hours)": 2,
            "Status": "Not Started",
            "Stage": [stage_map["1.6.2"]] if stage_map["1.6.2"] else []
        },
        {
            "Task ID": "TSK-1.6.2.2",
            "Task Name": "Create 197 feature tables",
            "Description": "Execute SQL to create all feature storage tables (28 pairs × 7 types)",
            "Estimated Duration (hours)": 1.5,
            "Status": "Not Started",
            "Stage": [stage_map["1.6.2"]] if stage_map["1.6.2"] else []
        },
        {
            "Task ID": "TSK-1.6.2.3",
            "Task Name": "Verify table creation and storage",
            "Description": "Check all tables exist, have correct partitions, and storage estimates are accurate",
            "Estimated Duration (hours)": 0.5,
            "Status": "Not Started",
            "Stage": [stage_map["1.6.2"]] if stage_map["1.6.2"] else []
        },

        # Stage 1.6.3 tasks (Unblocked Features)
        {
            "Task ID": "TSK-1.6.3.1",
            "Task Name": "Develop volume features worker",
            "Description": "Create worker to compute 10 volume-based features from M1.volume",
            "Estimated Duration (hours)": 3,
            "Status": "Not Started",
            "Stage": [stage_map["1.6.3"]] if stage_map["1.6.3"] else []
        },
        {
            "Task ID": "TSK-1.6.3.2",
            "Task Name": "Develop time & spread features worker",
            "Description": "Compute 8 time features (cyclical encoding) and 20 spread features (bid/ask/spread)",
            "Estimated Duration (hours)": 4,
            "Status": "Not Started",
            "Stage": [stage_map["1.6.3"]] if stage_map["1.6.3"] else []
        },
        {
            "Task ID": "TSK-1.6.3.3",
            "Task Name": "Develop currency indices & correlation worker",
            "Description": "Synthesize 3 currency strength indices and compute 15 cross-pair correlations",
            "Estimated Duration (hours)": 5,
            "Status": "Not Started",
            "Stage": [stage_map["1.6.3"]] if stage_map["1.6.3"] else []
        },
        {
            "Task ID": "TSK-1.6.3.4",
            "Task Name": "Develop statistics & Bollinger worker",
            "Description": "Compute 5 higher-order statistics and 5 Bollinger Band metrics",
            "Estimated Duration (hours)": 3,
            "Status": "Not Started",
            "Stage": [stage_map["1.6.3"]] if stage_map["1.6.3"] else []
        },
        {
            "Task ID": "TSK-1.6.3.5",
            "Task Name": "Execute unblocked features backfill",
            "Description": "Run workers in parallel (40% CPU) to compute 66 features for 28 pairs",
            "Estimated Duration (hours)": 3,
            "Status": "Not Started",
            "Stage": [stage_map["1.6.3"]] if stage_map["1.6.3"] else []
        },

        # Stage 1.6.4 tasks (Blocked Features)
        {
            "Task ID": "TSK-1.6.4.1",
            "Task Name": "Install and test TA-Lib integration",
            "Description": "Setup TA-Lib library, create wrapper functions for index-based computation",
            "Estimated Duration (hours)": 2,
            "Status": "Not Started",
            "Stage": [stage_map["1.6.4"]] if stage_map["1.6.4"] else []
        },
        {
            "Task ID": "TSK-1.6.4.2",
            "Task Name": "Develop technical indicators worker",
            "Description": "Create worker for 34 TA-Lib indicators (momentum, trend, volatility)",
            "Estimated Duration (hours)": 6,
            "Status": "Not Started",
            "Stage": [stage_map["1.6.4"]] if stage_map["1.6.4"] else []
        },
        {
            "Task ID": "TSK-1.6.4.3",
            "Task Name": "Develop regime features worker",
            "Description": "Compute 3 regime classification features (depends on ADX/ATR from TSK-1.6.4.2)",
            "Estimated Duration (hours)": 3,
            "Status": "Not Started",
            "Stage": [stage_map["1.6.4"]] if stage_map["1.6.4"] else []
        },
        {
            "Task ID": "TSK-1.6.4.4",
            "Task Name": "Execute blocked features backfill",
            "Description": "Run workers to compute 45 features for 28 pairs (after OHLC index ready)",
            "Estimated Duration (hours)": 6,
            "Status": "Not Started",
            "Stage": [stage_map["1.6.4"]] if stage_map["1.6.4"] else []
        },

        # Stage 1.6.5 tasks (Validation)
        {
            "Task ID": "TSK-1.6.5.1",
            "Task Name": "Validate OHLC index columns",
            "Description": "Verify 84 new columns exist, have correct values, and are indexed",
            "Estimated Duration (hours)": 1,
            "Status": "Not Started",
            "Stage": [stage_map["1.6.5"]] if stage_map["1.6.5"] else []
        },
        {
            "Task ID": "TSK-1.6.5.2",
            "Task Name": "Validate all 111 features",
            "Description": "Check feature values within expected ranges, no unexpected NULLs, cross-pair comparability",
            "Estimated Duration (hours)": 2,
            "Status": "Not Started",
            "Stage": [stage_map["1.6.5"]] if stage_map["1.6.5"] else []
        },
        {
            "Task ID": "TSK-1.6.5.3",
            "Task Name": "Create gap remediation completion report",
            "Description": "Document all gaps addressed, feature catalog, schema updates, worker documentation",
            "Estimated Duration (hours)": 2,
            "Status": "Not Started",
            "Stage": [stage_map["1.6.5"]] if stage_map["1.6.5"] else []
        },
        {
            "Task ID": "TSK-1.6.5.4",
            "Task Name": "Certify Phase 2 readiness",
            "Description": "Final checklist: all blockers removed, all features available, Phase 2 can start immediately",
            "Estimated Duration (hours)": 1,
            "Status": "Not Started",
            "Stage": [stage_map["1.6.5"]] if stage_map["1.6.5"] else []
        }
    ]

    created_task_ids = []

    for task in tasks:
        url = f"https://api.airtable.com/v0/{BASE_ID}/Tasks"
        response = requests.post(url, headers=HEADERS, json={"fields": task})

        if response.status_code == 200:
            task_record = response.json()
            created_task_ids.append(task_record['id'])
            print(f"✓ Created {task['Task ID']}")
        else:
            print(f"✗ Failed to create {task['Task ID']}: {response.status_code}")

    return created_task_ids

def main():
    """Main execution"""
    print("=" * 80)
    print("STRATEGIC GAP REMEDIATION PLAN - AIRTABLE INTEGRATION")
    print("=" * 80)
    print()

    print("Context:")
    print("• Gap Analysis Identified: 111 features planned, ZERO implemented")
    print("• Critical Blocker: 45 features (41%) blocked by missing OHLC index")
    print("• Opportunity: 66 features (59%) can compute NOW (parallel with REG)")
    print("• Strategy: 4 parallel tracks for 44% time savings (50h → 28h)")
    print()

    # Create Phase 1.6
    print("Creating Phase 1.6: Gap Remediation...")
    phase_id = create_phase_1_6()

    if not phase_id:
        print("\n✗ Failed to create phase. Aborting.")
        return

    print()

    # Create 5 stages
    print("Creating 5 strategic stages...")
    stage_ids = create_stages(phase_id)
    print(f"\n✓ Created {len(stage_ids)}/5 stages")
    print()

    # Create tasks
    print("Creating 19 detailed tasks...")
    task_ids = create_tasks(stage_ids)
    print(f"\n✓ Created {len(task_ids)}/19 tasks")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Phase 1.6 Record ID: {phase_id}")
    print(f"Stages Created: {len(stage_ids)}")
    print(f"Tasks Created: {len(task_ids)}")
    print()

    print("Strategic Execution Plan:")
    print()
    print("PARALLEL TRACK 1 (Start immediately, 40% CPU):")
    print("  → Stage 1.6.2: Feature Storage Infrastructure (4 hours)")
    print("  → Stage 1.6.3: Unblocked Features Computation (18 hours)")
    print("     • 66 features: volume, time, indices, spreads, correlations, stats")
    print()

    print("PARALLEL TRACK 2 (Start immediately, low CPU):")
    print("  → Stage 1.6.1: OHLC Index Schema Enhancement (3 hours)")
    print("     • CRITICAL: Unblocks 45 features (41% of Phase 2)")
    print()

    print("PARALLEL TRACK 3 (Already running, 50-60% CPU):")
    print("  → Stage 1.5.5: REG Backfill (continues, ~12 hours remaining)")
    print()

    print("SEQUENTIAL TRACK 4 (After OHLC index ready):")
    print("  → Stage 1.6.4: Blocked Features Computation (17 hours)")
    print("     • 45 features: technical indicators requiring OHLC index")
    print()

    print("QUALITY GATE:")
    print("  → Stage 1.6.5: Gap Remediation Validation (6 hours)")
    print("     • Certifies Phase 2 readiness")
    print()

    print("=" * 80)
    print("RESOURCE OPTIMIZATION")
    print("=" * 80)
    print("CPU Utilization During Parallel Execution:")
    print("  • Track 1 (Unblocked features): 40%")
    print("  • Track 3 (REG backfill): 50-60%")
    print("  • TOTAL: ~90% CPU utilization (vs 50-60% with REG alone)")
    print()
    print("Time Savings:")
    print("  • Sequential execution: ~50 hours wall time")
    print("  • Parallel execution: ~28 hours wall time")
    print("  • Savings: 22 hours (44% reduction)")
    print()

    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("1. Review Phase 1.6 plan in Airtable")
    print("2. Start Track 1 (Stage 1.6.2) - Feature storage tables")
    print("3. Start Track 2 (Stage 1.6.1) - OHLC index columns")
    print("4. Monitor REG backfill (Track 3) - should complete in ~12 hours")
    print("5. Once OHLC ready, start Track 4 (Stage 1.6.4)")
    print()
    print("✓ Gap remediation plan successfully added to Airtable")
    print()

if __name__ == "__main__":
    main()
