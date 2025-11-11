#!/usr/bin/env python3
"""
Add Phase 1.6 (Gap Remediation) to BQX ML Airtable

Simplified version - adds only the Phase record with correct Airtable schema.
Stages and tasks can be added separately later.
"""

import os
import requests

# Airtable configuration
BASE_ID = "appR3PPnrNkVo48mO"
API_KEY = os.environ.get("AIRTABLE_API_KEY")

if not API_KEY:
    print("ERROR: AIRTABLE_API_KEY environment variable not set")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def create_phase_1_6():
    """Create Phase 1.6: Gap Remediation"""

    phase_data = {
        "fields": {
            "Phase ID": "Phase 1.6: Gap Remediation & OHLC Index Enhancement",
            "Description": (
                "Strategic remediation plan addressing 111-feature gap analysis. "
                "Executes in parallel with REG backfill (Stage 1.5.5) to maximize CPU utilization.\n\n"
                "**Dependencies:** Phase 1.5 (REG backfill in progress)\n\n"
                "**Parallel Execution Tracks:**\n"
                "• Track 1: 66 unblocked features (40% CPU) - Immediate execution\n"
                "• Track 2: OHLC index columns (low CPU) - Unblocks 45 features\n"
                "• Track 3: REG backfill continues (50-60% CPU) - In progress\n"
                "• Track 4: 45 blocked features - After OHLC index ready\n\n"
                "**Critical Path:** OHLC index blocks 41% of Phase 2 features (ADX, ATR, Stochastic, etc.)\n\n"
                "**Gap Analysis Summary:**\n"
                "- Total features planned: 111\n"
                "- Unblocked (can compute now): 66 (59%)\n"
                "- Blocked by OHLC index: 45 (41%)\n\n"
                "**Time Savings:** Sequential: 50h → Parallel: 28h (44% savings)"
            ),
            "Status": "Not Started",
            "Duration": "28 hours",
            "Objectives": (
                "1. Add OHLC index columns to all 28 M1 pairs (unblocks 45 features)\n"
                "2. Create 197 feature storage tables\n"
                "3. Compute 66 unblocked features immediately\n"
                "4. Compute 45 blocked features after OHLC ready\n"
                "5. Validate all 111 features\n"
                "6. Certify Phase 2 readiness"
            ),
            "Success Criteria": (
                "1. OHLC index columns added to all 28 M1 pairs\n"
                "2. 66 unblocked features computed and stored\n"
                "3. All feature storage tables created\n"
                "4. Feature computation workers tested\n"
                "5. Zero blocking gaps remaining for Phase 2\n"
                "6. Cross-pair feature comparability verified"
            )
        }
    }

    url = f"https://api.airtable.com/v0/{BASE_ID}/Phases"
    response = requests.post(url, headers=HEADERS, json=phase_data)

    if response.status_code == 200:
        phase_record = response.json()
        print(f"✓ Created Phase 1.6: {phase_record['id']}")
        print(f"\nPhase 1.6 successfully added to Airtable!")
        print(f"\nNext steps:")
        print(f"  1. Add stages to Phase 1.6 (can be done manually in Airtable)")
        print(f"  2. Begin Track 2: OHLC Index Schema Enhancement")
        print(f"  3. Begin Track 1: Unblocked Features Computation")
        return phase_record['id']
    else:
        print(f"✗ Failed to create Phase 1.6: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    print("=" * 80)
    print("ADDING PHASE 1.6 TO BQX ML AIRTABLE")
    print("=" * 80)
    print()
    create_phase_1_6()
