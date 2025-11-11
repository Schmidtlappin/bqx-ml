#!/usr/bin/env python3
"""
Add Phase 2: ML Feature Engineering to BQX ML Airtable Plan

Adds:
- 1 Phase record (Phase 2)
- 3 Stage records (2.1, 2.2, 2.3)
- 11 Task records (4 + 4 + 3)

Total: 111 new features across 3 stages, 35 hours
"""

import requests
import json
import sys

BASE_ID = 'appR3PPnrNkVo48mO'
PHASES_TABLE = 'Phases'
STAGES_TABLE = 'Stages'
TASKS_TABLE = 'Tasks'

# Known record IDs
MASTER_PLAN_ID = 'recSb2RvwT60eSu8U'


def get_headers(api_token):
    return {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }


def create_phase_2(api_token):
    """Create Phase 2: ML Feature Engineering"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{PHASES_TABLE}'

    phase_data = {
        "Phase ID": "Phase 2: ML Feature Engineering",
        "Description": """Add 111 predictive features from existing M1 data (volume, OHLC, rate_index, bid/ask/spread). All features normalized for cross-pair comparability using rate_index (~100 scale), percentage normalization, or dimensionless ratios.

NO EXTERNAL APIs REQUIRED - All computed from 28 existing forex pairs in M1 tables.

STAGES:
- Stage 2.1: Quick Win Features (volume, time, indices, spreads) - 41 features, 13h
- Stage 2.2: Technical Indicators (TA-Lib: momentum, trend, volatility) - 45 features, 15h
- Stage 2.3: Advanced Features (cross-pair, regimes, statistics) - 25 features, 7h

NORMALIZATION STRATEGY:
- Price-based features: Use rate_index (all pairs ~100 scale)
- Returns/changes: Percentage normalization ((close - open) / open × 100)
- Volume/spread: Ratios (dimensionless)
- Correlations: Inherently -1 to +1

EXPECTED IMPACT:
- R² improvement: +0.06-0.08 (from 0.88-0.90 → 0.94-0.98)
- Storage increase: +21 GB (+33%, managed with feature selection)
- Zero external dependencies""",
        "Duration": "35 hours",
        "Status": "Not Started",
        "Plan (Link)": [MASTER_PLAN_ID]
    }

    payload = {'fields': phase_data}
    response = requests.post(url, json=payload, headers=get_headers(api_token))

    if response.status_code == 200:
        return response.json()['id']
    else:
        print(f"Error creating Phase 2: {response.status_code}")
        print(response.text)
        return None


def create_stage_2_1(api_token, phase_2_id):
    """Create Stage 2.1: Quick Win Features"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}'

    stage_data = {
        "Stage ID": "Stage 2.1: Quick Win Features",
        "Description": """Add 41 high-impact features from existing M1 data (NO external APIs):

FEATURES:
1. Volume Features (10): volume_ratio, volume_spike, volume_trend_slope, cumulative_volume, volume_weighted_return
   - Data source: M1 volume field (currently unused!)
   - Normalization: Ratios (dimensionless, comparable across pairs)

2. Time Features (8): hour_sin/cos, day_of_week_sin/cos, session_overlap, is_weekend_approach
   - Data source: Timestamp (existing)
   - Normalization: Cyclical encoding (sin/cos), binary indicators

3. Currency Indices (3): base_currency_index, quote_currency_index, currency_index_differential
   - Data source: Weighted average of existing pairs (synthetic DXY-like, no Bloomberg API)
   - Normalization: Computed from rate_index (all ~100 scale)

4. Spread/Microstructure (20): spread_mean, spread_volatility, spread_pct_of_rate, bid_ask_imbalance
   - Data source: M1 bid/ask/spread fields (confirmed available in schema)
   - Normalization: Percentage of rate

DELIVERABLES:
- 41 new features per pair (total 1,148 features across 28 pairs)
- Volume extraction module
- Currency index calculation module
- Spread analysis module
- Updated BQX table schema
- Documentation: feature_engineering_phase2_1.md

STORAGE IMPACT: +8 GB""",
        "Duration": "13 hours",
        "Status": "Todo",
        "Phase (Link)": phase_2_id,
        "Plan (Link)": [MASTER_PLAN_ID]
    }

    payload = {'fields': stage_data}
    response = requests.post(url, json=payload, headers=get_headers(api_token))

    if response.status_code == 200:
        return response.json()['id']
    else:
        print(f"Error creating Stage 2.1: {response.status_code}")
        print(response.text)
        return None


def create_stage_2_2(api_token, phase_2_id):
    """Create Stage 2.2: Technical Indicators"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}'

    stage_data = {
        "Stage ID": "Stage 2.2: Technical Indicators",
        "Description": """Add 45 technical indicators using TA-Lib library on M1 OHLC + rate_index:

MOMENTUM INDICATORS (15):
- RSI (14, 21 period) - Overbought/oversold (0-100 scale, inherently normalized)
- Stochastic (%K, %D) - Momentum oscillator
- Williams %R, Momentum, ROC - Additional momentum measures

TREND INDICATORS (15):
- MACD (line, signal, histogram) - Trend direction + strength
- ADX + DI - Trend strength (>25 trending, <20 ranging)
- Parabolic SAR, Ichimoku, MA slopes
- CRITICAL: Compute on rate_index (not rate) for cross-pair comparability

VOLATILITY INDICATORS (15):
- Bollinger Bands (upper, lower, %B, width) - Volatility expansion/contraction
- ATR (Average True Range) - Absolute volatility in index points
- Keltner Channels, Donchian Channels
- CRITICAL: Compute on rate_index for same-scale results across pairs

NORMALIZATION STRATEGY:
- Momentum: 0-100 output by design (already normalized)
- Trend: Computed on rate_index (EURUSD ~100, USDJPY ~100 = comparable)
- Volatility: Computed on rate_index (band widths comparable across pairs)

DELIVERABLES:
- TA-Lib library installed and configured
- 45 technical indicator fields per pair
- technical_indicators.py module (wrapper functions)
- Backfilled for all 28 pairs × 16 months
- Unit tests and validation
- Documentation: technical_indicators_specification.md

STORAGE IMPACT: +10 GB

DEPENDENCIES: Stage 1.5.4 complete (need rate_index in M1 tables)""",
        "Duration": "15 hours",
        "Status": "Todo",
        "Phase (Link)": phase_2_id,
        "Plan (Link)": [MASTER_PLAN_ID]
    }

    payload = {'fields': stage_data}
    response = requests.post(url, json=payload, headers=get_headers(api_token))

    if response.status_code == 200:
        return response.json()['id']
    else:
        print(f"Error creating Stage 2.2: {response.status_code}")
        print(response.text)
        return None


def create_stage_2_3(api_token, phase_2_id):
    """Create Stage 2.3: Advanced Features"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{STAGES_TABLE}'

    stage_data = {
        "Stage ID": "Stage 2.3: Advanced Features",
        "Description": """Add 25 advanced features for cross-pair analysis, regime detection, and distribution modeling:

CROSS-PAIR FEATURES (15):
- Rolling correlations: corr_base_pairs_60min, corr_quote_pairs_60min
- Relative strength: relative_strength_vs_base_pairs (z-score vs peers)
- Divergence indicators: pair_divergence, triangular_arb_divergence
- Data source: MV with 13 related pairs (currency-filtered)
- Normalization: Correlation coefficients (-1 to +1, inherently normalized)

ENHANCED REGIME DETECTION (5):
- Trend regime: strong_up/weak_up/ranging/weak_down/strong_down (using ADX + DI)
- Regime stability: Time since last regime change
- Consolidation breakout: Low ATR → high ATR transition
- Data source: Computed from technical indicators (Stage 2.2)
- Dependencies: Requires ADX from Stage 2.2

HIGHER-ORDER STATISTICS (5):
- Skewness, kurtosis of returns (distribution shape beyond mean/stdev)
- Median absolute deviation (robust volatility)
- Data source: Computed from percentage returns
- Normalization: Computed on normalized returns (already dimensionless)

DELIVERABLES:
- cross_pair_features.py module
- regime_detection.py module (ADX-based trend classification)
- Higher-order statistics in feature engineering pipeline
- 25 new features per pair
- Documentation: advanced_features_specification.md

STORAGE IMPACT: +3 GB

DEPENDENCIES: Stage 2.2 complete (needs ADX for regime detection)""",
        "Duration": "7 hours",
        "Status": "Todo",
        "Phase (Link)": phase_2_id,
        "Plan (Link)": [MASTER_PLAN_ID]
    }

    payload = {'fields': stage_data}
    response = requests.post(url, json=payload, headers=get_headers(api_token))

    if response.status_code == 200:
        return response.json()['id']
    else:
        print(f"Error creating Stage 2.3: {response.status_code}")
        print(response.text)
        return None


def create_tasks_2_1(api_token, stage_2_1_id):
    """Create 4 tasks for Stage 2.1"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TASKS_TABLE}'

    tasks = [
        {
            "Task ID": "TSK-2.1.1",
            "Task Name": "Add Volume Features to BQX Tables",
            "Description": "Extract volume from M1 tables, add 10 volume fields: w15/w30/w60_volume_ratio, volume_spike, volume_trend_slope, cumulative_volume, volume_weighted_return. Use ratios (dimensionless). Backfill 28 pairs × 16 months. Dependencies: Stage 1.5.4.3 complete.",
            "Status": "Todo",
            "Priority": "High",
            "Assigned To": "BQX Worker Script",
            "Estimated Hours": 4.0,
            "Estimated Cost": 0
        },
        {
            "Task ID": "TSK-2.1.2",
            "Task Name": "Add Time & Seasonality Features",
            "Description": "Add 8 time features: hour_sin/cos, day_of_week_sin/cos, session_overlap, is_weekend_approach. Cyclical encoding for continuity. Add to feature engineering pipeline (on-the-fly, no backfill). Dependencies: None.",
            "Status": "Todo",
            "Priority": "High",
            "Assigned To": "Feature Engineering Pipeline",
            "Estimated Hours": 2.0,
            "Estimated Cost": 0
        },
        {
            "Task ID": "TSK-2.1.3",
            "Task Name": "Compute Currency Strength Indices",
            "Description": "Create currency_indices.py. Compute EUR/USD/GBP/JPY/AUD/CAD/CHF/NZD indices from weighted avg of pairs. Use rate_index (all ~100). Add base_currency_index, quote_currency_index, differential. No external API needed. Dependencies: Stage 1.5.4.3 (need rate_index).",
            "Status": "Todo",
            "Priority": "High",
            "Assigned To": "Currency Index Module",
            "Estimated Hours": 3.0,
            "Estimated Cost": 0
        },
        {
            "Task ID": "TSK-2.1.4",
            "Task Name": "Add Spread/Microstructure Features",
            "Description": "Extract bid/ask/spread from M1 tables (confirmed available). Add 20 features: spread_mean, spread_volatility, spread_pct_of_rate, bid_ask_imbalance. Normalize as % of rate. Backfill 28 pairs × 16 months. Dependencies: Stage 1.5.4.3 complete.",
            "Status": "Todo",
            "Priority": "Medium",
            "Assigned To": "BQX Worker Script",
            "Estimated Hours": 4.0,
            "Estimated Cost": 0
        }
    ]

    created_count = 0
    for task in tasks:
        task["Stage (Link)"] = stage_2_1_id
        task["Plan (Link)"] = [MASTER_PLAN_ID]

        payload = {'fields': task}
        response = requests.post(url, json=payload, headers=get_headers(api_token))

        if response.status_code == 200:
            created_count += 1
            print(f"  ✓ {task['Task ID']}: {task['Task Name']}")
        else:
            print(f"  ✗ {task['Task ID']}: {response.status_code}")
            print(f"    {response.text[:150]}")

    return created_count


def create_tasks_2_2(api_token, stage_2_2_id):
    """Create 4 tasks for Stage 2.2"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TASKS_TABLE}'

    tasks = [
        {
            "Task ID": "TSK-2.2.1",
            "Task Name": "Install TA-Lib and Create Indicator Module",
            "Description": "Install TA-Lib library (pip install TA-Lib). Create technical_indicators.py with wrapper functions for 45 indicators. Unit tests on sample data. Dependencies: None.",
            "Status": "Todo",
            "Priority": "High",
            "Assigned To": "Development Environment",
            "Estimated Hours": 2.0,
            "Estimated Cost": 0
        },
        {
            "Task ID": "TSK-2.2.2",
            "Task Name": "Add Momentum Indicators",
            "Description": "Add RSI (14, 21), Stochastic, Williams %R, Momentum, ROC. Compute on M1 close. Output 0-100 (inherently normalized). Backfill all pairs. Dependencies: TSK-2.2.1.",
            "Status": "Todo",
            "Priority": "High",
            "Assigned To": "Technical Indicators Module",
            "Estimated Hours": 5.0,
            "Estimated Cost": 0
        },
        {
            "Task ID": "TSK-2.2.3",
            "Task Name": "Add Trend Indicators",
            "Description": "Add MACD, ADX+DI, Parabolic SAR, Ichimoku, MA slopes. CRITICAL: Compute on rate_index (not rate) for cross-pair comparability. Backfill all pairs. Dependencies: TSK-2.2.1, Stage 1.5.4.3 (need rate_index).",
            "Status": "Todo",
            "Priority": "High",
            "Assigned To": "Technical Indicators Module",
            "Estimated Hours": 5.0,
            "Estimated Cost": 0
        },
        {
            "Task ID": "TSK-2.2.4",
            "Task Name": "Add Volatility Indicators",
            "Description": "Add Bollinger Bands, ATR, Keltner, Donchian. CRITICAL: Compute on rate_index (all pairs same scale). Example: Bollinger width in index points (comparable). Backfill all pairs. Dependencies: TSK-2.2.1, Stage 1.5.4.3.",
            "Status": "Todo",
            "Priority": "High",
            "Assigned To": "Technical Indicators Module",
            "Estimated Hours": 3.0,
            "Estimated Cost": 0
        }
    ]

    created_count = 0
    for task in tasks:
        task["Stage (Link)"] = stage_2_2_id
        task["Plan (Link)"] = [MASTER_PLAN_ID]

        payload = {'fields': task}
        response = requests.post(url, json=payload, headers=get_headers(api_token))

        if response.status_code == 200:
            created_count += 1
            print(f"  ✓ {task['Task ID']}: {task['Task Name']}")
        else:
            print(f"  ✗ {task['Task ID']}: {response.status_code}")
            print(f"    {response.text[:150]}")

    return created_count


def create_tasks_2_3(api_token, stage_2_3_id):
    """Create 3 tasks for Stage 2.3"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TASKS_TABLE}'

    tasks = [
        {
            "Task ID": "TSK-2.3.1",
            "Task Name": "Add Cross-Pair Correlation Features",
            "Description": "Compute rolling correlations between target and 13 related pairs. Features: corr_base_pairs_60min, relative_strength_vs_base_pairs, pair_divergence. Use MV data (currency-filtered). Correlation of rate_index returns. Dependencies: Stage 2.1 complete.",
            "Status": "Todo",
            "Priority": "Medium",
            "Assigned To": "Cross-Pair Features Module",
            "Estimated Hours": 3.0,
            "Estimated Cost": 0
        },
        {
            "Task ID": "TSK-2.3.2",
            "Task Name": "Add Enhanced Regime Detection",
            "Description": "Create regime_detection.py. Trend regime using ADX+DI: strong_up/weak_up/ranging/weak_down/strong_down. Add regime_stability (time since change), consolidation_breakout. Dependencies: TSK-2.2.3 (needs ADX).",
            "Status": "Todo",
            "Priority": "Medium",
            "Assigned To": "Regime Detection Module",
            "Estimated Hours": 2.0,
            "Estimated Cost": 0
        },
        {
            "Task ID": "TSK-2.3.3",
            "Task Name": "Add Higher-Order Statistics",
            "Description": "Add skewness, kurtosis, median absolute deviation. Compute on percentage returns (normalized). Captures distribution shape. Add to feature engineering pipeline. Dependencies: None.",
            "Status": "Todo",
            "Priority": "Low",
            "Assigned To": "Feature Engineering Pipeline",
            "Estimated Hours": 2.0,
            "Estimated Cost": 0
        }
    ]

    created_count = 0
    for task in tasks:
        task["Stage (Link)"] = stage_2_3_id
        task["Plan (Link)"] = [MASTER_PLAN_ID]

        payload = {'fields': task}
        response = requests.post(url, json=payload, headers=get_headers(api_token))

        if response.status_code == 200:
            created_count += 1
            print(f"  ✓ {task['Task ID']}: {task['Task Name']}")
        else:
            print(f"  ✗ {task['Task ID']}: {response.status_code}")
            print(f"    {response.text[:150]}")

    return created_count


def main():
    if len(sys.argv) > 1:
        api_token = sys.argv[1]
    else:
        print("Usage: python3 add_phase_2_feature_engineering.py <AIRTABLE_API_TOKEN>")
        sys.exit(1)

    print("=" * 100)
    print("ADDING PHASE 2: ML FEATURE ENGINEERING TO AIRTABLE")
    print("=" * 100)
    print()

    # Step 1: Create Phase 2
    print("[1/5] Creating Phase 2: ML Feature Engineering...")
    phase_2_id = create_phase_2(api_token)

    if not phase_2_id:
        print("  ✗ Failed to create Phase 2 - aborting")
        return

    print(f"  ✓ Created Phase 2: {phase_2_id}")
    print()

    # Step 2: Create Stage 2.1
    print("[2/5] Creating Stage 2.1: Quick Win Features...")
    stage_2_1_id = create_stage_2_1(api_token, phase_2_id)

    if not stage_2_1_id:
        print("  ✗ Failed to create Stage 2.1")
        return

    print(f"  ✓ Created Stage 2.1: {stage_2_1_id}")
    print()
    print("  Creating 4 tasks for Stage 2.1...")
    tasks_2_1_count = create_tasks_2_1(api_token, stage_2_1_id)
    print(f"  ✓ Created {tasks_2_1_count}/4 tasks for Stage 2.1")
    print()

    # Step 3: Create Stage 2.2
    print("[3/5] Creating Stage 2.2: Technical Indicators...")
    stage_2_2_id = create_stage_2_2(api_token, phase_2_id)

    if not stage_2_2_id:
        print("  ✗ Failed to create Stage 2.2")
        return

    print(f"  ✓ Created Stage 2.2: {stage_2_2_id}")
    print()
    print("  Creating 4 tasks for Stage 2.2...")
    tasks_2_2_count = create_tasks_2_2(api_token, stage_2_2_id)
    print(f"  ✓ Created {tasks_2_2_count}/4 tasks for Stage 2.2")
    print()

    # Step 4: Create Stage 2.3
    print("[4/5] Creating Stage 2.3: Advanced Features...")
    stage_2_3_id = create_stage_2_3(api_token, phase_2_id)

    if not stage_2_3_id:
        print("  ✗ Failed to create Stage 2.3")
        return

    print(f"  ✓ Created Stage 2.3: {stage_2_3_id}")
    print()
    print("  Creating 3 tasks for Stage 2.3...")
    tasks_2_3_count = create_tasks_2_3(api_token, stage_2_3_id)
    print(f"  ✓ Created {tasks_2_3_count}/3 tasks for Stage 2.3")
    print()

    # Step 5: Summary
    print("[5/5] Summary")
    print("=" * 100)
    print("PHASE 2 ADDED SUCCESSFULLY")
    print("=" * 100)
    print()
    print("Created:")
    print(f"  - 1 Phase: Phase 2 (ML Feature Engineering)")
    print(f"  - 3 Stages: 2.1 (Quick Wins), 2.2 (Technical Indicators), 2.3 (Advanced)")
    print(f"  - {tasks_2_1_count + tasks_2_2_count + tasks_2_3_count} Tasks: {tasks_2_1_count} + {tasks_2_2_count} + {tasks_2_3_count}")
    print()
    print("Features: 111 total (41 + 45 + 25)")
    print("Duration: 35 hours (13h + 15h + 7h)")
    print("Storage Impact: +21 GB")
    print("Expected R² Improvement: +0.06-0.08")
    print()
    print(f"View in Airtable: https://airtable.com/{BASE_ID}")
    print()


if __name__ == "__main__":
    main()
