#!/usr/bin/env python3
"""
Create Currency-Filtered Feature Materialized Views for BQX ML Training

Strategy: For each target pair, include only features from pairs that share
a currency with the target (base or quote currency).

Example: EURUSD target includes:
  - EUR-pairs: EURAUD, EURCAD, EURCHF, EURGBP, EURJPY, EURNZD, EURUSD
  - USD-pairs: AUDUSD, EURUSD, GBPUSD, NZDUSD, USDCAD, USDCHF, USDJPY
  - Total: 13 unique pairs (EURUSD appears in both)

This reduces dimensionality by ~53% while maintaining relevant signal.
"""

import psycopg2
from datetime import datetime

# Database connection
DB_HOST = "trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com"
DB_PORT = 5432
DB_NAME = "bqx"
DB_USER = "postgres"
DB_PASSWORD = "BQX_Aurora_2025_Secure"

# All 28 preferred pairs
ALL_PAIRS = [
    'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
    'cadchf', 'cadjpy', 'chfjpy',
    'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
    'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
    'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
    'usdcad', 'usdchf', 'usdjpy'
]

# BQX features to extract (37 base features per pair + 24 normalized features)
BQX_FEATURES = [
    'rate',
    # Window features (5 windows × 6 metrics = 30 features)
    'w15_bqx_return', 'w15_bqx_max', 'w15_bqx_min', 'w15_bqx_avg', 'w15_bqx_stdev', 'w15_bqx_endpoint',
    'w30_bqx_return', 'w30_bqx_max', 'w30_bqx_min', 'w30_bqx_avg', 'w30_bqx_stdev', 'w30_bqx_endpoint',
    'w45_bqx_return', 'w45_bqx_max', 'w45_bqx_min', 'w45_bqx_avg', 'w45_bqx_stdev', 'w45_bqx_endpoint',
    'w60_bqx_return', 'w60_bqx_max', 'w60_bqx_min', 'w60_bqx_avg', 'w60_bqx_stdev', 'w60_bqx_endpoint',
    'w75_bqx_return', 'w75_bqx_max', 'w75_bqx_min', 'w75_bqx_avg', 'w75_bqx_stdev', 'w75_bqx_endpoint',
    # Aggregate features (7 features)
    'agg_bqx_return', 'agg_bqx_max', 'agg_bqx_min', 'agg_bqx_avg',
    'agg_bqx_stdev', 'agg_bqx_range', 'agg_bqx_volatility'
]

# Features that need percentage normalization (max, min, avg, stdev)
# These will be computed as: (value - rate) / rate for max/min/avg
#                           value / rate for stdev
NORMALIZE_FEATURES = {
    'w15_bqx_max', 'w15_bqx_min', 'w15_bqx_avg', 'w15_bqx_stdev',
    'w30_bqx_max', 'w30_bqx_min', 'w30_bqx_avg', 'w30_bqx_stdev',
    'w45_bqx_max', 'w45_bqx_min', 'w45_bqx_avg', 'w45_bqx_stdev',
    'w60_bqx_max', 'w60_bqx_min', 'w60_bqx_avg', 'w60_bqx_stdev',
    'w75_bqx_max', 'w75_bqx_min', 'w75_bqx_avg', 'w75_bqx_stdev',
    'agg_bqx_max', 'agg_bqx_min', 'agg_bqx_avg', 'agg_bqx_stdev'
}


def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode="require",
    )


def get_relevant_pairs(target_pair):
    """
    Get relevant pairs for a target based on currency composition

    Args:
        target_pair: e.g., 'eurusd'

    Returns:
        List of relevant pairs (includes target itself)
    """
    base_currency = target_pair[:3]   # e.g., 'eur'
    quote_currency = target_pair[3:]  # e.g., 'usd'

    relevant = []
    for pair in ALL_PAIRS:
        if base_currency in pair or quote_currency in pair:
            relevant.append(pair)

    return relevant


def generate_feature_columns(pair, is_target=False):
    """
    Generate SQL column definitions for a pair's features

    Includes both base features and percentage-normalized features.
    Normalized features use _pct suffix and are computed as:
    - For max/min/avg: (value - rate) / rate
    - For stdev: value / rate

    Args:
        pair: forex pair name
        is_target: if True, prefix with 'target_', else use pair name

    Returns:
        List of SQL column definitions
    """
    columns = []
    prefix = "target" if is_target else pair
    alias_prefix = "target" if is_target else pair

    # Add rate first
    if is_target:
        columns.append(f"{prefix}.rate as {alias_prefix}_rate")
    else:
        columns.append(f"{prefix}.rate as {alias_prefix}_rate")

    # Add base features (excluding rate which was already added)
    for feature in BQX_FEATURES[1:]:  # Skip 'rate'
        columns.append(f"{prefix}.{feature} as {alias_prefix}_{feature}")

    # Add normalized percentage features
    for feature in NORMALIZE_FEATURES:
        feature_pct = f"{feature}_pct"

        # Determine normalization formula based on feature type
        if 'stdev' in feature:
            # For standard deviation: just divide by rate
            # Formula: stdev / rate
            formula = f"{prefix}.{feature} / NULLIF({prefix}.rate, 0)"
        else:
            # For max/min/avg: compute percentage difference from current rate
            # Formula: (value - rate) / rate
            formula = f"({prefix}.{feature} - {prefix}.rate) / NULLIF({prefix}.rate, 0)"

        columns.append(f"{formula} as {alias_prefix}_{feature_pct}")

    return columns


def generate_mv_sql(target_pair):
    """
    Generate SQL to create materialized view for a target pair

    Args:
        target_pair: forex pair to create MV for

    Returns:
        SQL CREATE MATERIALIZED VIEW statement
    """
    relevant_pairs = get_relevant_pairs(target_pair)

    # Remove target from relevant pairs (will add separately)
    feature_pairs = [p for p in relevant_pairs if p != target_pair]

    # Generate column lists
    columns = []

    # 1. Timestamp
    columns.append("target.ts_utc")

    # 2. Target pair features (37 features with 'target_' prefix)
    columns.extend(generate_feature_columns(target_pair, is_target=True))

    # 3. Feature pair columns (37 features per pair × N pairs)
    for pair in sorted(feature_pairs):
        columns.extend(generate_feature_columns(pair, is_target=False))

    # Generate JOIN clauses
    joins = []
    for pair in sorted(feature_pairs):
        joins.append(
            f"LEFT JOIN bqx.bqx_{pair} {pair} ON target.ts_utc = {pair}.ts_utc"
        )

    # Construct SQL
    columns_str = ',\n    '.join(columns)
    joins_str = '\n'.join(joins)
    pairs_list = ', '.join(sorted(relevant_pairs)).upper()

    # Calculate feature counts
    features_per_pair = 37 + 24  # 37 base + 24 normalized
    target_features = features_per_pair  # 61 features for target
    feature_pair_features = len(feature_pairs) * features_per_pair
    total_fields = 1 + target_features + feature_pair_features

    sql = f"""
-- ============================================================================
-- Materialized View: features_{target_pair}
-- Target: {target_pair.upper()}
-- Relevant Pairs: {len(relevant_pairs)} ({pairs_list})
-- Features: {features_per_pair} per pair (37 base + 24 normalized percentage)
-- Total Fields: {total_fields} (1 timestamp + {target_features} target + {len(feature_pairs)} pairs × {features_per_pair})
-- Normalization: max/min/avg as (value-rate)/rate, stdev as value/rate
-- Created: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS bqx_ml.features_{target_pair} AS
SELECT
    {columns_str}
FROM bqx.bqx_{target_pair} target
{joins_str}
WHERE target.ts_utc >= '2024-07-01' AND target.ts_utc < '2025-07-01'
  AND target.w75_bqx_return IS NOT NULL;

-- Create index on timestamp for efficient queries
CREATE INDEX IF NOT EXISTS idx_features_{target_pair}_ts
ON bqx_ml.features_{target_pair}(ts_utc);

-- Analyze for query optimization
ANALYZE bqx_ml.features_{target_pair};
"""

    return sql


def create_schema():
    """Create bqx_ml schema if it doesn't exist"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("CREATE SCHEMA IF NOT EXISTS bqx_ml;")
        conn.commit()
        print("✓ Created/verified bqx_ml schema")
    except Exception as e:
        print(f"✗ Error creating schema: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def create_mv(target_pair, dry_run=False):
    """
    Create materialized view for a target pair

    Args:
        target_pair: forex pair to create MV for
        dry_run: if True, only generate SQL without executing

    Returns:
        tuple: (success: bool, message: str, sql: str)
    """
    sql = generate_mv_sql(target_pair)

    if dry_run:
        return (True, "Dry run - SQL generated", sql)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Execute the SQL
        cur.execute(sql)
        conn.commit()

        # Get row count
        cur.execute(f"SELECT COUNT(*) FROM bqx_ml.features_{target_pair};")
        row_count = cur.fetchone()[0]

        message = f"✓ Created features_{target_pair} ({row_count:,} rows)"
        return (True, message, sql)

    except Exception as e:
        conn.rollback()
        message = f"✗ Error creating features_{target_pair}: {e}"
        return (False, message, sql)

    finally:
        cur.close()
        conn.close()


def generate_feature_summary():
    """Generate summary of feature configuration"""
    print("=" * 100)
    print("CURRENCY-FILTERED FEATURE MATERIALIZED VIEWS - CONFIGURATION SUMMARY")
    print("=" * 100)
    print()

    print("Strategy: Include only pairs that share a currency with the target")
    print()

    total_features_all_pairs = len(ALL_PAIRS) * len(BQX_FEATURES)

    print(f"All-Pairs Approach (not used):")
    print(f"  - Pairs per target: {len(ALL_PAIRS)}")
    print(f"  - Features per target: {total_features_all_pairs:,}")
    print()

    print("Currency-Filtered Approach (implemented):")
    print("-" * 100)
    print(f"{'Target':<10} {'Relevant Pairs':<15} {'Total Fields':<15} {'Reduction':<15}")
    print("-" * 100)

    # With normalization: 61 features per pair (37 base + 24 normalized)
    features_per_pair = 61

    for target in ALL_PAIRS[:10]:  # Sample first 10
        relevant = get_relevant_pairs(target)
        # 1 timestamp + target (61) + feature_pairs (N-1) × 61
        num_fields = 1 + features_per_pair + (len(relevant) - 1) * features_per_pair
        # Compare to all-pairs approach: 1 + 28 × 61
        all_pairs_fields = 1 + len(ALL_PAIRS) * features_per_pair
        reduction = (1 - num_fields / all_pairs_fields) * 100

        print(f"{target.upper():<10} {len(relevant):<15} {num_fields:<15,} {reduction:<15.1f}%")

    if len(ALL_PAIRS) > 10:
        print(f"... and {len(ALL_PAIRS) - 10} more targets")

    print("-" * 100)

    # Average statistics
    avg_pairs = sum(len(get_relevant_pairs(t)) for t in ALL_PAIRS) / len(ALL_PAIRS)
    avg_fields = 1 + features_per_pair + (avg_pairs - 1) * features_per_pair
    all_pairs_fields = 1 + len(ALL_PAIRS) * features_per_pair
    avg_reduction = (1 - avg_fields / all_pairs_fields) * 100

    print(f"{'AVERAGE':<10} {avg_pairs:<15.1f} {avg_fields:<15,.0f} {avg_reduction:<15.1f}%")
    print()
    print(f"Note: Each pair contributes {features_per_pair} features (37 base + 24 normalized percentage)")
    print()


def main():
    """Main execution"""
    print("=" * 100)
    print("BQX ML - CREATE CURRENCY-FILTERED FEATURE MATERIALIZED VIEWS")
    print("=" * 100)
    print()

    # Show configuration summary
    generate_feature_summary()

    # Create schema
    print("Creating bqx_ml schema...")
    create_schema()
    print()

    # Ask for confirmation
    print("=" * 100)
    print("This will create 28 materialized views in the database.")
    print("Each MV will contain ~13-15 relevant pairs with ~730-850 fields.")
    print("Fields include: 61 per pair (37 base + 24 percentage-normalized)")
    print("Normalization: max/min/avg as (value-rate)/rate, stdev as value/rate")
    print("Estimated creation time: 5-10 minutes for all views.")
    print("=" * 100)

    response = input("\nProceed with creation? (yes/no/dry-run): ").strip().lower()

    if response == 'no':
        print("Aborted.")
        return

    dry_run = (response == 'dry-run')

    print()
    print("=" * 100)
    print("CREATING MATERIALIZED VIEWS")
    print("=" * 100)
    print()

    results = []

    for i, target in enumerate(ALL_PAIRS, 1):
        print(f"[{i}/{len(ALL_PAIRS)}] Processing {target.upper()}...")

        success, message, sql = create_mv(target, dry_run=dry_run)
        results.append((target, success, message))

        print(f"    {message}")

        if dry_run and i <= 2:  # Show SQL for first 2 in dry-run
            print()
            print("    Generated SQL:")
            print("    " + "\n    ".join(sql.split('\n')[:20]))
            print("    ... (truncated)")
            print()

    # Summary
    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)

    successes = sum(1 for _, success, _ in results if success)
    failures = len(results) - successes

    print(f"Total MVs: {len(results)}")
    print(f"Successful: {successes}")
    print(f"Failed: {failures}")

    if failures > 0:
        print()
        print("Failed targets:")
        for target, success, message in results:
            if not success:
                print(f"  - {target.upper()}: {message}")

    if dry_run:
        print()
        print("DRY RUN - No changes made to database")
    else:
        print()
        print("✓ All materialized views created successfully")
        print()
        print("Next steps:")
        print("  1. Verify MV creation: SELECT * FROM bqx_ml.features_eurusd LIMIT 10;")
        print("  2. Extract features for training: See scripts/ml/extract_training_data.py")
        print("  3. Begin model training: See scripts/ml/train_baseline.py")


if __name__ == "__main__":
    main()
