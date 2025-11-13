#!/usr/bin/env python3
"""
Audit all 1,060 feature tables to determine which are populated vs empty schemas.
This helps prioritize Phase 2.1 feature population work.
"""

import psycopg2
from collections import defaultdict
import sys

# Database connection
DB_CONFIG = {
    'host': 'trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com',
    'database': 'bqx',
    'user': 'postgres',
    'password': 'BQX_Aurora_2025_Secure'
}

# Feature families from Phase 1 (1,060 features)
FEATURE_FAMILIES = {
    # Phase 1.6 Core Features (628 features)
    'reg_rate': {'features': 90, 'description': 'Regression rate features'},
    'reg_bqx': {'features': 90, 'description': 'Regression BQX features'},
    'statistics_rate': {'features': 24, 'description': 'Statistical moments rate'},
    'statistics_bqx': {'features': 24, 'description': 'Statistical moments BQX'},
    'technical_rate': {'features': 30, 'description': 'Technical indicators rate'},
    'technical_bqx': {'features': 30, 'description': 'Technical indicators BQX'},
    'bollinger_rate': {'features': 10, 'description': 'Bollinger bands rate'},
    'bollinger_bqx': {'features': 10, 'description': 'Bollinger bands BQX'},
    'fibonacci_features_rate': {'features': 10, 'description': 'Fibonacci levels rate'},
    'fibonacci_features_bqx': {'features': 10, 'description': 'Fibonacci levels BQX'},
    'volume_features': {'features': 70, 'description': 'Volume-based features'},
    'spread_features': {'features': 35, 'description': 'Spread-based features'},
    'time_features': {'features': 20, 'description': 'Time & calendar features'},
    'correlation_features_rate': {'features': 45, 'description': 'Correlation rate'},
    'correlation_features_bqx': {'features': 45, 'description': 'Correlation BQX'},

    # Phase 1.6 Advanced (106 features)
    'error_correction_rate': {'features': 12, 'description': 'Error correction rate'},
    'error_correction_bqx': {'features': 12, 'description': 'Error correction BQX'},
    'realized_volatility_rate': {'features': 15, 'description': 'Realized volatility rate'},
    'realized_volatility_bqx': {'features': 15, 'description': 'Realized volatility BQX'},
    'hmm_regime_rate': {'features': 15, 'description': 'HMM regime detection rate'},
    'hmm_regime_bqx': {'features': 15, 'description': 'HMM regime detection BQX'},
    'cross_sectional_panel': {'features': 46, 'description': 'Cross-sectional panel'},

    # Phase 1.8 (164 features)
    'parabolic_comparison_rate': {'features': 24, 'description': 'Parabolic comparisons rate'},
    'parabolic_comparison_bqx': {'features': 20, 'description': 'Parabolic comparisons BQX'},
    'multi_scale_30m_rate': {'features': 15, 'description': 'Multi-scale 30m rate'},
    'multi_scale_30m_bqx': {'features': 15, 'description': 'Multi-scale 30m BQX'},
    'multi_scale_60m_rate': {'features': 15, 'description': 'Multi-scale 60m rate'},
    'multi_scale_60m_bqx': {'features': 15, 'description': 'Multi-scale 60m BQX'},
    'spectral_features_rate': {'features': 12, 'description': 'FFT spectral features rate'},
    'spectral_features_bqx': {'features': 12, 'description': 'FFT spectral features BQX'},
    'wavelet_features_rate': {'features': 10, 'description': 'Wavelet features rate'},
    'wavelet_features_bqx': {'features': 10, 'description': 'Wavelet features BQX'},
    'ssa_features_rate': {'features': 8, 'description': 'SSA features rate'},
    'ssa_features_bqx': {'features': 8, 'description': 'SSA features BQX'},

    # Phase 1.9 (162 features)
    'advanced_microstructure_rate': {'features': 20, 'description': 'Advanced microstructure rate'},
    'advanced_microstructure_bqx': {'features': 20, 'description': 'Advanced microstructure BQX'},
    'lagged_cross_window_rate': {'features': 25, 'description': 'Lagged cross-window rate'},
    'lagged_cross_window_bqx': {'features': 25, 'description': 'Lagged cross-window BQX'},
    'volatility_surface_rate': {'features': 15, 'description': 'Volatility surface rate'},
    'volatility_surface_bqx': {'features': 15, 'description': 'Volatility surface BQX'},
    'market_regime_rate': {'features': 10, 'description': 'Market regime rate'},
    'market_regime_bqx': {'features': 10, 'description': 'Market regime BQX'},
    'liquidity_metrics_rate': {'features': 11, 'description': 'Liquidity metrics rate'},
    'liquidity_metrics_bqx': {'features': 11, 'description': 'Liquidity metrics BQX'},
}

def check_table_population(conn, table_prefix):
    """
    Check if tables with given prefix exist and have data.
    Returns: (table_count, total_rows, sample_tables)
    """
    cursor = conn.cursor()

    # Find all tables matching prefix
    query = """
        SELECT
            schemaname,
            relname,
            n_live_tup as row_count
        FROM pg_stat_user_tables
        WHERE schemaname = 'bqx'
          AND relname LIKE %s
        ORDER BY relname;
    """

    cursor.execute(query, (f"{table_prefix}%",))
    results = cursor.fetchall()

    table_count = len(results)
    total_rows = sum(r[2] for r in results)

    # Get sample of first 3 tables
    sample_tables = [(r[1], r[2]) for r in results[:3]]

    cursor.close()
    return table_count, total_rows, sample_tables

def main():
    print("=" * 100)
    print("FEATURE POPULATION AUDIT - Phase 1 (1,060 features)")
    print("=" * 100)
    print()
    print("Checking which feature tables are populated vs empty schemas...")
    print()

    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to database")
        print()

        # Results tracking
        results = {
            'populated': [],
            'empty': [],
            'partial': []
        }

        total_features = 0
        populated_features = 0

        # Check each feature family
        for table_prefix, info in sorted(FEATURE_FAMILIES.items()):
            table_count, total_rows, sample_tables = check_table_population(conn, table_prefix)

            status = "EMPTY"
            if total_rows > 1000000:
                status = "POPULATED"
                populated_features += info['features']
                results['populated'].append((table_prefix, info['features'], total_rows, table_count))
            elif total_rows > 0:
                status = "PARTIAL"
                results['partial'].append((table_prefix, info['features'], total_rows, table_count))
            else:
                status = "EMPTY"
                results['empty'].append((table_prefix, info['features'], total_rows, table_count))

            total_features += info['features']

            print(f"{status:12} | {table_prefix:35} | {info['features']:3} features | {table_count:4} tables | {total_rows:12,} rows")

            # Show sample for populated tables
            if total_rows > 0 and len(sample_tables) > 0:
                for tbl, rows in sample_tables[:1]:
                    print(f"             └─ Sample: {tbl:50} ({rows:,} rows)")

        conn.close()

        # Summary
        print()
        print("=" * 100)
        print("SUMMARY")
        print("=" * 100)
        print()

        print(f"📊 POPULATED FEATURES ({len(results['populated'])} families):")
        print("-" * 100)
        if results['populated']:
            for prefix, features, rows, tables in sorted(results['populated'], key=lambda x: x[2], reverse=True):
                print(f"  ✅ {prefix:35} | {features:3} features | {tables:4} tables | {rows:12,} rows")
            populated_count = sum(f[1] for f in results['populated'])
            populated_rows = sum(f[2] for f in results['populated'])
            print(f"\n  Total: {populated_count} features, {populated_rows:,} rows")
        else:
            print("  None")

        print()
        print(f"⚠️  PARTIALLY POPULATED ({len(results['partial'])} families):")
        print("-" * 100)
        if results['partial']:
            for prefix, features, rows, tables in results['partial']:
                print(f"  ⚠️  {prefix:35} | {features:3} features | {tables:4} tables | {rows:12,} rows")
            partial_count = sum(f[1] for f in results['partial'])
            partial_rows = sum(f[2] for f in results['partial'])
            print(f"\n  Total: {partial_count} features, {partial_rows:,} rows")
        else:
            print("  None")

        print()
        print(f"❌ EMPTY SCHEMAS ({len(results['empty'])} families):")
        print("-" * 100)
        if results['empty']:
            for prefix, features, rows, tables in results['empty']:
                print(f"  ❌ {prefix:35} | {features:3} features | {tables:4} tables | {rows:12,} rows")
            empty_count = sum(f[1] for f in results['empty'])
            print(f"\n  Total: {empty_count} features (schemas only)")
        else:
            print("  None - All features populated!")

        print()
        print("=" * 100)
        print("PHASE 2.1 PRIORITY RECOMMENDATIONS")
        print("=" * 100)
        print()

        populated_pct = (populated_features / total_features) * 100 if total_features > 0 else 0

        print(f"Current Status: {populated_features}/{total_features} features ({populated_pct:.1f}%)")
        print()

        if results['empty']:
            print("🔧 IMMEDIATE PRIORITIES (Empty Schemas):")
            print("-" * 100)

            # Group by complexity
            core_empty = [f for f in results['empty'] if any(x in f[0] for x in ['statistics', 'technical', 'bollinger', 'fibonacci', 'volume', 'spread', 'time'])]
            advanced_empty = [f for f in results['empty'] if any(x in f[0] for x in ['error_correction', 'realized_volatility', 'hmm', 'cross_sectional'])]
            spectral_empty = [f for f in results['empty'] if any(x in f[0] for x in ['parabolic', 'multi_scale', 'spectral', 'wavelet', 'ssa'])]
            very_advanced_empty = [f for f in results['empty'] if any(x in f[0] for x in ['advanced_microstructure', 'lagged_cross', 'volatility_surface', 'market_regime', 'liquidity'])]

            if core_empty:
                print("\n  Priority Tier 1: Core Features (Quick Wins)")
                for prefix, features, _, tables in core_empty:
                    print(f"    • {prefix:35} | {features:3} features | {tables:4} tables")

            if advanced_empty:
                print("\n  Priority Tier 2: Advanced Features Wave 1")
                for prefix, features, _, tables in advanced_empty:
                    print(f"    • {prefix:35} | {features:3} features | {tables:4} tables")

            if spectral_empty:
                print("\n  Priority Tier 3: Spectral Features")
                for prefix, features, _, tables in spectral_empty:
                    print(f"    • {prefix:35} | {features:3} features | {tables:4} tables")

            if very_advanced_empty:
                print("\n  Priority Tier 4: Very Advanced Features (Complex)")
                for prefix, features, _, tables in very_advanced_empty:
                    print(f"    • {prefix:35} | {features:3} features | {tables:4} tables")

        print()
        print("=" * 100)
        print(f"✅ Audit Complete - {populated_features}/{total_features} features populated ({populated_pct:.1f}%)")
        print("=" * 100)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
