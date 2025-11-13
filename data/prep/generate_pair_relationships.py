#!/usr/bin/env python3
"""
Generate 28×28 Pair Relationship Matrix for Cross-Pair Analysis
Identifies shared currencies and relationship types between all pairs.
"""

import json
from pathlib import Path

# Load currency mappings
with open('/home/ubuntu/bqx-ml/data/prep/currency_mappings.json', 'r') as f:
    mappings = json.load(f)

all_pairs = mappings['all_pairs']

def get_pair_currencies(pair):
    """Extract base and quote currencies from pair name"""
    # All pairs are 6 characters: XXXYYY (base=XXX, quote=YYY)
    base = pair[:3].upper()
    quote = pair[3:].upper()
    return base, quote

def analyze_relationship(pair1, pair2):
    """Analyze relationship between two currency pairs"""
    base1, quote1 = get_pair_currencies(pair1)
    base2, quote2 = get_pair_currencies(pair2)

    # Same pair
    if pair1 == pair2:
        return {
            'relationship_type': 'identical',
            'shared_currency': None,
            'can_compute_cross_rate': False,
            'correlation_expected': 1.0
        }

    # Share base currency
    if base1 == base2:
        return {
            'relationship_type': 'base_base',
            'shared_currency': base1,
            'can_compute_cross_rate': True,
            'implied_pair': f"{quote1}{quote2}" if quote1 != quote2 else None,
            'correlation_expected': 'high_positive'
        }

    # Share quote currency
    if quote1 == quote2:
        return {
            'relationship_type': 'quote_quote',
            'shared_currency': quote1,
            'can_compute_cross_rate': True,
            'implied_pair': f"{base1}{base2}" if base1 != base2 else None,
            'correlation_expected': 'high_positive'
        }

    # Pair 1 base = Pair 2 quote (direct cross)
    if base1 == quote2:
        return {
            'relationship_type': 'base_quote_cross',
            'shared_currency': base1,
            'can_compute_cross_rate': True,
            'cross_pair': f"{base2}{quote1}",
            'formula': f"{pair1} × {pair2} = {base2}{quote1}",
            'correlation_expected': 'inverse'
        }

    # Pair 1 quote = Pair 2 base (direct cross)
    if quote1 == base2:
        return {
            'relationship_type': 'quote_base_cross',
            'shared_currency': quote1,
            'can_compute_cross_rate': True,
            'cross_pair': f"{base1}{quote2}",
            'formula': f"{pair1} × {pair2} = {base1}{quote2}",
            'correlation_expected': 'moderate_positive'
        }

    # No shared currency
    return {
        'relationship_type': 'independent',
        'shared_currency': None,
        'can_compute_cross_rate': False,
        'correlation_expected': 'low'
    }

# Generate 28×28 matrix
print("Generating 28×28 pair relationship matrix...")
relationship_matrix = {}

for pair1 in all_pairs:
    for pair2 in all_pairs:
        key = f"{pair1.upper()}_{pair2.upper()}"
        relationship_matrix[key] = analyze_relationship(pair1, pair2)

# Count relationship types
relationship_counts = {}
for rel in relationship_matrix.values():
    rel_type = rel['relationship_type']
    relationship_counts[rel_type] = relationship_counts.get(rel_type, 0) + 1

# Extract interesting examples
examples = {
    'identical': {},
    'base_base': {},
    'quote_quote': {},
    'base_quote_cross': {},
    'quote_base_cross': {},
    'independent': {}
}

for key, rel in relationship_matrix.items():
    rel_type = rel['relationship_type']
    if len(examples[rel_type]) < 3:  # Store up to 3 examples of each type
        examples[rel_type][key] = rel

# Create output
output = {
    'description': '28×28 matrix indicating shared currencies and relationship types between all currency pairs',
    'total_pairs': len(all_pairs),
    'total_relationships': len(relationship_matrix),
    'created': '2025-11-13',
    'purpose': 'Preparation for Stage 2.3 (Cross-Pair Currency Indices)',

    'relationship_type_counts': relationship_counts,

    'relationship_types_explained': {
        'identical': 'Same pair (diagonal)',
        'base_base': 'Share base currency (e.g., EURUSD & EURGBP share EUR)',
        'quote_quote': 'Share quote currency (e.g., EURUSD & GBPUSD share USD)',
        'base_quote_cross': 'Pair1 base = Pair2 quote (e.g., EUR in EURUSD & GBPEUR)',
        'quote_base_cross': 'Pair1 quote = Pair2 base (e.g., USD in EURUSD & USDCAD)',
        'independent': 'No shared currencies (e.g., EURUSD & AUDJPY)'
    },

    'examples': examples,

    'matrix': relationship_matrix
}

# Save to file
output_path = Path('/home/ubuntu/bqx-ml/data/prep/pair_relationship_matrix.json')
with open(output_path, 'w') as f:
    json.dump(output, f, indent=2)

print(f"✅ Pair relationship matrix saved: {output_path}")
print()
print("Summary:")
for rel_type, count in sorted(relationship_counts.items()):
    print(f"  {rel_type}: {count} relationships")
print()
print(f"Total: {len(relationship_matrix)} relationships (28×28 = 784)")
