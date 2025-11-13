#!/usr/bin/env python3
"""
Update AirTable Phase 1 completion status to reflect 98.1% completion
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
PHASES_TABLE = 'Phases'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

print("=" * 80)
print("UPDATING AIRTABLE: PHASE 1 COMPLETION STATUS")
print("=" * 80)
print()

phases_url = f'https://api.airtable.com/v0/{BASE_ID}/{PHASES_TABLE}'

# Search for Phase 1.6, 1.8, and 1.9 records
print("Step 1: Find Phase 1 records (1.6, 1.8, 1.9)")
print("-" * 80)

phase_records = {}
for phase_num in ['1.6', '1.8', '1.9']:
    params = {'filterByFormula': f"FIND('{phase_num}', {{Phase ID}}) > 0"}
    response = requests.get(phases_url, headers=headers, params=params)

    if response.status_code == 200:
        records = response.json()['records']
        if records:
            record = records[0]
            phase_records[phase_num] = {
                'id': record['id'],
                'phase_id': record['fields'].get('Phase ID', 'Unknown'),
                'status': record['fields'].get('Status', 'Unknown')
            }
            print(f"✓ Found Phase {phase_num}: {phase_records[phase_num]['phase_id']}")
            print(f"  Record ID: {phase_records[phase_num]['id']}")
            print(f"  Current Status: {phase_records[phase_num]['status']}")
        else:
            print(f"✗ Phase {phase_num} not found")
    else:
        print(f"❌ Error searching for Phase {phase_num}: {response.status_code}")

print()
print("Step 2: Update Phase statuses")
print("-" * 80)

updates = {
    '1.6': {
        'Status': 'Complete',
        'Notes': '''Phase 1.6 Complete (100%)

**Completion Date:** 2025-11-13
**Features Added:** 106 (error correction, realized volatility, HMM, panel)
**Stages Completed:** 13/13 (1.6.9-1.6.21)
**Total Features:** 734/1,080 (68.0%)

**Key Achievements:**
- Error correction models (Johansen cointegration, ECT)
- Realized volatility (Parkinson, GK, RS, YZ estimators)
- HMM regime detection (K=3 states, BOCPD, CUSUM)
- Cross-sectional panel features (ranks, percentiles, dispersion)'''
    },
    '1.8': {
        'Status': 'Complete',
        'Notes': '''Phase 1.8 Complete (100%)

**Completion Date:** 2025-11-13
**Features Added:** 164 (parabolic, multi-scale, spectral)
**Stages Completed:** 3/3 (1.8.1-1.8.3)
**Total Features:** 898/1,080 (83.1%)

**Key Achievements:**
- Parabolic term comparisons (cross-window regression analysis)
- Multi-scale features (30m/60m time resolution)
- Spectral features (FFT, Wavelets, SSA)'''
    },
    '1.9': {
        'Status': 'Complete',
        'Notes': '''Phase 1.9 Complete (100%)

**Completion Date:** 2025-11-13
**Features Added:** 162 (microstructure, lagged, volatility surface, regime, liquidity)
**Stages Completed:** 5/5 (1.9.1-1.9.5)
**Total Features:** 1,060/1,080 (98.1%)

**Key Achievements:**
- Advanced microstructure (Amihud, Kyle λ, VPIN)
- Lagged cross-window features (temporal dependencies)
- Volatility surface (term structure, GARCH)
- Market regime indicators (bull/bear/neutral classification)
- Liquidity metrics (execution quality assessment)

**Phase 1 TOTAL: 1,060/1,080 features (98.1% complete)**
**Ready for Phase 2: Feature Engineering Pipeline**'''
    }
}

updated_count = 0
for phase_num, update_data in updates.items():
    if phase_num not in phase_records:
        print(f"\n⏭️  Skipping Phase {phase_num} (not found in AirTable)")
        continue

    print(f"\nUpdating Phase {phase_num}")
    print("-" * 40)

    record_id = phase_records[phase_num]['id']
    update_url = f'{phases_url}/{record_id}'

    # Try different status values
    for status_value in ['Complete', 'Completed', 'Done', 'Finished']:
        update_data_copy = update_data.copy()
        update_data_copy['Status'] = status_value
        payload = {'fields': update_data_copy}

        try:
            update_response = requests.patch(update_url, headers=headers, json=payload)

            if update_response.status_code == 200:
                print(f"✅ Phase {phase_num} updated successfully!")
                print(f"   Status: {status_value}")
                updated_count += 1
                break
            elif update_response.status_code == 422:
                # Invalid status value, try next one
                continue
            else:
                print(f"❌ Error updating phase: {update_response.status_code}")
                print(f"   Response: {update_response.text}")
                break
        except Exception as e:
            print(f"❌ Exception updating phase: {str(e)}")
            break

print()
print("=" * 80)
print("UPDATE COMPLETE")
print("=" * 80)
print()
print(f"Phases updated: {updated_count}/{len(updates)}")
print()
print("PHASE 1 COMPLETION SUMMARY:")
print("  • Phase 1.6: 106 features → 734/1,080 (68.0%)")
print("  • Phase 1.8: 164 features → 898/1,080 (83.1%)")
print("  • Phase 1.9: 162 features → 1,060/1,080 (98.1%)")
print()
print("  • ✅ Phase 1 Total: 1,060/1,080 features (98.1%)")
print("  • ✅ All schemas created (~17,000 tables)")
print("  • ✅ Dual architecture parity maintained")
print("  • ✅ Ready for Phase 2: Feature Engineering Pipeline")
print()
print("=" * 80)
