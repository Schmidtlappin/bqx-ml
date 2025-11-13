#!/usr/bin/env python3
"""
Generate Arbitrage Triplet Mappings for Stage 2.4 (Arbitrage Detection)
Identifies all valid currency triplets for triangular arbitrage detection.
"""

import json
from pathlib import Path
from itertools import combinations

# Load currency mappings
with open('/home/ubuntu/bqx-ml/data/prep/currency_mappings.json', 'r') as f:
    mappings = json.load(f)

all_pairs = [p.upper() for p in mappings['all_pairs']]
currencies = list(mappings['currencies'].keys())

def get_pair_currencies(pair):
    """Extract base and quote currencies from pair name"""
    base = pair[:3]
    quote = pair[3:]
    return base, quote

def find_pair(base, quote):
    """Find pair name for given base and quote currencies"""
    # Try direct pair
    direct = f"{base}{quote}"
    if direct in all_pairs:
        return direct, 'direct'

    # Try inverse pair
    inverse = f"{quote}{base}"
    if inverse in all_pairs:
        return inverse, 'inverse'

    return None, None

def generate_triplets():
    """Generate all valid triangular arbitrage triplets"""
    valid_triplets = []

    # For each combination of 3 currencies
    for curr_trio in combinations(currencies, 3):
        c1, c2, c3 = curr_trio

        # Try to form a triplet: c1->c2, c2->c3, c3->c1
        pair_12, dir_12 = find_pair(c1, c2)
        pair_23, dir_23 = find_pair(c2, c3)
        pair_31, dir_31 = find_pair(c3, c1)

        if pair_12 and pair_23 and pair_31:
            # Calculate arbitrage formula
            # Start with 1 unit of c1
            formula_parts = []

            # c1 -> c2
            if dir_12 == 'direct':
                formula_parts.append(f"1 {c1} × {pair_12}_rate = X {c2}")
            else:
                formula_parts.append(f"1 {c1} ÷ {pair_12}_rate = X {c2}")

            # c2 -> c3
            if dir_23 == 'direct':
                formula_parts.append(f"X {c2} × {pair_23}_rate = Y {c3}")
            else:
                formula_parts.append(f"X {c2} ÷ {pair_23}_rate = Y {c3}")

            # c3 -> c1
            if dir_31 == 'direct':
                formula_parts.append(f"Y {c3} × {pair_31}_rate = Z {c1}")
            else:
                formula_parts.append(f"Y {c3} ÷ {pair_31}_rate = Z {c1}")

            # Arbitrage exists if Z > 1 (after transaction costs)
            triplet = {
                'currencies': [c1, c2, c3],
                'pairs': [pair_12, pair_23, pair_31],
                'directions': [dir_12, dir_23, dir_31],
                'formula': formula_parts,
                'arbitrage_condition': 'Z > 1.0 (after transaction costs)',
                'triplet_name': f"{c1}-{c2}-{c3}"
            }

            valid_triplets.append(triplet)

    return valid_triplets

print("Generating arbitrage triplets...")
triplets = generate_triplets()

# Group by currency
triplets_by_currency = {}
for triplet in triplets:
    for curr in triplet['currencies']:
        if curr not in triplets_by_currency:
            triplets_by_currency[curr] = []
        triplets_by_currency[curr].append(triplet['triplet_name'])

# Create fast lookup index
triplet_index = {}
for i, triplet in enumerate(triplets):
    triplet_index[triplet['triplet_name']] = i
    # Also index by pairs (for quick lookup when new prices arrive)
    for pair in triplet['pairs']:
        if pair not in triplet_index:
            triplet_index[pair] = []
        if isinstance(triplet_index[pair], list):
            triplet_index[pair].append(i)

# Example arbitrage calculation
example = {
    'triplet': 'EUR-USD-GBP',
    'pairs': ['EURUSD', 'GBPUSD', 'EURGBP'],
    'calculation': {
        'step_1': '1 EUR × EURUSD_rate = X USD',
        'step_2': 'X USD ÷ GBPUSD_rate = Y GBP',
        'step_3': 'Y GBP × EURGBP_rate = Z EUR',
        'arbitrage_profit': '(Z - 1) × 100 = profit %',
        'example_values': {
            'EURUSD': 1.1000,
            'GBPUSD': 1.2500,
            'EURGBP': 0.8800,
            'calculation': [
                '1 EUR × 1.1000 = 1.1000 USD',
                '1.1000 USD ÷ 1.2500 = 0.8800 GBP',
                '0.8800 GBP × 0.8800 = 0.7744 EUR',
                'Arbitrage profit: (0.7744 - 1) × 100 = -22.56% LOSS (no arbitrage)'
            ]
        }
    }
}

# Arbitrage detection algorithm
algorithm = {
    'method': 'triangular_arbitrage',
    'description': 'Detect arbitrage opportunities by computing round-trip exchange rates',
    'steps': [
        '1. For each triplet, fetch current M1 rates for all 3 pairs',
        '2. Convert 1 unit of base currency through the triplet',
        '3. Calculate final amount after round trip',
        '4. Arbitrage exists if final > 1.0 (before transaction costs)',
        '5. Subtract typical transaction costs (0.1-0.5% per trade)',
        '6. Flag as arbitrage opportunity if net profit > threshold (e.g., 0.5%)'
    ],
    'transaction_cost_model': {
        'bid_ask_spread': '0.0001 - 0.0005 per trade (1-5 pips)',
        'typical_cost': '0.3% per round trip (3 trades)',
        'min_profit_threshold': '0.5% (to justify execution)'
    },
    'feature_output': {
        'arbitrage_profit_pct': 'Percentage profit from round-trip',
        'arbitrage_opportunity': 'Boolean flag if profit > threshold',
        'arbitrage_direction': 'Optimal direction (clockwise or counter-clockwise)',
        'arbitrage_max_profit': 'Maximum profit considering both directions'
    }
}

# Create output
output = {
    'description': 'Valid currency triplets for triangular arbitrage detection',
    'total_triplets': len(triplets),
    'total_currencies': len(currencies),
    'total_pairs': len(all_pairs),
    'created': '2025-11-13',
    'purpose': 'Preparation for Stage 2.4 (Arbitrage Detection)',

    'triplet_count_by_currency': {curr: len(trips) for curr, trips in triplets_by_currency.items()},

    'example': example,

    'arbitrage_detection_algorithm': algorithm,

    'triplets': triplets,

    'triplets_by_currency': triplets_by_currency,

    'triplet_index': {k: v for k, v in triplet_index.items() if isinstance(v, int)}
}

# Save to file
output_path = Path('/home/ubuntu/bqx-ml/data/prep/arbitrage_triplets.json')
with open(output_path, 'w') as f:
    json.dump(output, f, indent=2)

print(f"✅ Arbitrage triplets saved: {output_path}")
print()
print("Summary:")
print(f"  Total valid triplets: {len(triplets)}")
print()
print("Triplets per currency:")
for curr in sorted(triplets_by_currency.keys()):
    count = len(set(triplets_by_currency[curr]))
    print(f"  {curr}: {count} triplets")
print()
print("Example triplet:")
ex_triplet = triplets[0]
print(f"  {ex_triplet['triplet_name']}")
print(f"  Pairs: {', '.join(ex_triplet['pairs'])}")
print(f"  Formula: {' → '.join(ex_triplet['currencies'])}")
