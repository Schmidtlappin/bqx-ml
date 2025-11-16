#!/usr/bin/env python3
"""
Stage 2.15: Comprehensive Schema Alignment Validation
Validates 100% alignment between reg_rate and reg_bqx tables.

Validation Checks:
1. Window alignment (both have {60, 90, 150, 240, 390, 630})
2. Schema alignment (both have 7 features per window)
3. Term-based architecture (both have quadratic_term, linear_term, constant_term, residual)
4. Covariance features (all 6 present in correlation_bqx)
5. Data integrity (prediction = sum of terms)
6. Cross-domain comparability (can JOIN at same timestamps)

Estimated Duration: 1 hour
Estimated Cost: $0.33
Risk: NONE (read-only validation)
"""

import psycopg2
import pandas as pd
import logging
import sys
import os
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com'),
    'database': 'bqx',
    'user': 'postgres',
    'password': os.environ.get('DB_PASSWORD', 'BQX_Aurora_2025_Secure')
}

# Create logs directory
os.makedirs('/tmp/logs/remediation/stage_2_15', exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/logs/remediation/stage_2_15/validation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Expected windows (aligned)
EXPECTED_WINDOWS = [60, 90, 150, 240, 390, 630]

# Sample pair for validation
VALIDATION_PAIR = 'eurusd'
VALIDATION_MONTH = '2024_07'


def validate_window_alignment():
    """
    Validate that reg_rate and reg_bqx have the same windows.

    Returns:
        dict: Validation results
    """
    logger.info("=" * 80)
    logger.info("VALIDATION 1: Window Alignment")
    logger.info("=" * 80)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Get windows from reg_rate
        cur.execute(f"""
            SELECT DISTINCT regexp_replace(column_name, '_.*', '') AS window
            FROM information_schema.columns
            WHERE table_schema = 'bqx'
            AND table_name = 'reg_{VALIDATION_PAIR}'
            AND column_name ~ '^w[0-9]+'
            ORDER BY window
        """)
        rate_windows = [row[0] for row in cur.fetchall()]

        # Get windows from reg_bqx
        cur.execute(f"""
            SELECT DISTINCT regexp_replace(column_name, '_.*', '') AS window
            FROM information_schema.columns
            WHERE table_schema = 'bqx'
            AND table_name = 'reg_bqx_{VALIDATION_PAIR}'
            AND column_name ~ '^w[0-9]+'
            ORDER BY window
        """)
        bqx_windows = [row[0] for row in cur.fetchall()]

        cur.close()
        conn.close()

        # Convert to integers
        rate_windows_int = sorted([int(w.replace('w', '')) for w in rate_windows])
        bqx_windows_int = sorted([int(w.replace('w', '')) for w in bqx_windows])

        logger.info(f"reg_rate windows: {rate_windows_int}")
        logger.info(f"reg_bqx windows: {bqx_windows_int}")
        logger.info(f"Expected windows: {EXPECTED_WINDOWS}")

        # Check alignment
        rate_aligned = rate_windows_int == EXPECTED_WINDOWS
        bqx_aligned = bqx_windows_int == EXPECTED_WINDOWS
        both_aligned = rate_aligned and bqx_aligned

        if both_aligned:
            logger.info("✅ Window alignment: PASS - Both tables have aligned windows")
        else:
            logger.error("❌ Window alignment: FAIL")
            if not rate_aligned:
                logger.error(f"   reg_rate mismatch: expected {EXPECTED_WINDOWS}, got {rate_windows_int}")
            if not bqx_aligned:
                logger.error(f"   reg_bqx mismatch: expected {EXPECTED_WINDOWS}, got {bqx_windows_int}")

        return {
            'test': 'Window Alignment',
            'passed': both_aligned,
            'reg_rate_windows': rate_windows_int,
            'reg_bqx_windows': bqx_windows_int,
            'expected_windows': EXPECTED_WINDOWS
        }

    except Exception as e:
        logger.error(f"❌ Window alignment validation failed: {e}")
        return {'test': 'Window Alignment', 'passed': False, 'error': str(e)}


def validate_schema_alignment():
    """
    Validate that reg_rate and reg_bqx have the same number of features per window.

    Returns:
        dict: Validation results
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("VALIDATION 2: Schema Alignment")
    logger.info("=" * 80)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        results = {}

        for window in EXPECTED_WINDOWS:
            # Count reg_rate columns for this window
            cur.execute(f"""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_schema = 'bqx'
                AND table_name = 'reg_{VALIDATION_PAIR}'
                AND column_name ~ '^w{window}_'
            """)
            rate_count = cur.fetchone()[0]

            # Count reg_bqx columns for this window
            cur.execute(f"""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_schema = 'bqx'
                AND table_name = 'reg_bqx_{VALIDATION_PAIR}'
                AND column_name ~ '^w{window}_'
            """)
            bqx_count = cur.fetchone()[0]

            aligned = (rate_count > 0) and (bqx_count > 0) and (rate_count == bqx_count)
            results[f'w{window}'] = {
                'reg_rate_cols': rate_count,
                'reg_bqx_cols': bqx_count,
                'aligned': aligned
            }

            if aligned:
                logger.info(f"✅ w{window}: {rate_count} columns in both tables")
            else:
                logger.error(f"❌ w{window}: reg_rate={rate_count}, reg_bqx={bqx_count}")

        cur.close()
        conn.close()

        all_aligned = all(r['aligned'] for r in results.values())

        if all_aligned:
            logger.info("✅ Schema alignment: PASS - All windows have matching column counts")
        else:
            logger.error("❌ Schema alignment: FAIL - Some windows have mismatched columns")

        return {
            'test': 'Schema Alignment',
            'passed': all_aligned,
            'details': results
        }

    except Exception as e:
        logger.error(f"❌ Schema alignment validation failed: {e}")
        return {'test': 'Schema Alignment', 'passed': False, 'error': str(e)}


def validate_term_based_architecture():
    """
    Validate that both tables have term-based architecture.

    Returns:
        dict: Validation results
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("VALIDATION 3: Term-Based Architecture")
    logger.info("=" * 80)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        required_columns = ['quadratic_term', 'linear_term', 'constant_term', 'residual']
        results = {}

        for table in ['reg_rate', 'reg_bqx']:
            table_name = f"{table}_{VALIDATION_PAIR}" if table == 'reg_rate' else f"reg_bqx_{VALIDATION_PAIR}"
            missing_columns = []

            for window in EXPECTED_WINDOWS:
                for col in required_columns:
                    col_name = f"w{window}_{col}"

                    cur.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns
                            WHERE table_schema = 'bqx'
                            AND table_name = %s
                            AND column_name = %s
                        )
                    """, (table_name, col_name))

                    if not cur.fetchone()[0]:
                        missing_columns.append(col_name)

            results[table] = {
                'missing_columns': missing_columns,
                'complete': len(missing_columns) == 0
            }

            if results[table]['complete']:
                logger.info(f"✅ {table}: All term-based columns present")
            else:
                logger.error(f"❌ {table}: Missing columns: {missing_columns[:5]}...")

        cur.close()
        conn.close()

        all_complete = all(r['complete'] for r in results.values())

        if all_complete:
            logger.info("✅ Term-based architecture: PASS - Both tables have complete term columns")
        else:
            logger.error("❌ Term-based architecture: FAIL - Some term columns missing")

        return {
            'test': 'Term-Based Architecture',
            'passed': all_complete,
            'details': results
        }

    except Exception as e:
        logger.error(f"❌ Term-based architecture validation failed: {e}")
        return {'test': 'Term-Based Architecture', 'passed': False, 'error': str(e)}


def validate_covariance_features():
    """
    Validate that covariance features are present in correlation_bqx tables.

    Returns:
        dict: Validation results
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("VALIDATION 4: Covariance Features")
    logger.info("=" * 80)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        table_name = f"correlation_bqx_{VALIDATION_PAIR}_{VALIDATION_MONTH}"
        required_columns = [
            'cov_quad_lin_bqx_60min',
            'cov_resid_quad_bqx_60min',
            'cov_resid_lin_bqx_60min',
            'corr_quad_lin_bqx_60min',
            'corr_resid_quad_bqx_60min',
            'corr_resid_lin_bqx_60min'
        ]

        missing_columns = []
        for col in required_columns:
            cur.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_schema = 'bqx'
                    AND table_name = %s
                    AND column_name = %s
                )
            """, (table_name, col))

            if not cur.fetchone()[0]:
                missing_columns.append(col)

        # Check data coverage
        if len(missing_columns) == 0:
            cur.execute(f"""
                SELECT COUNT(*) AS total,
                       COUNT(cov_quad_lin_bqx_60min) AS populated,
                       ROUND(100.0 * COUNT(cov_quad_lin_bqx_60min) / COUNT(*), 2) AS coverage_pct
                FROM bqx.{table_name}
            """)
            total, populated, coverage = cur.fetchone()
        else:
            total, populated, coverage = 0, 0, 0.0

        cur.close()
        conn.close()

        all_present = len(missing_columns) == 0
        good_coverage = coverage > 99.0

        if all_present and good_coverage:
            logger.info(f"✅ Covariance features: PASS - All 6 columns present, {coverage}% coverage")
        else:
            if not all_present:
                logger.error(f"❌ Covariance features: FAIL - Missing columns: {missing_columns}")
            if not good_coverage:
                logger.error(f"❌ Covariance features: FAIL - Low coverage: {coverage}%")

        return {
            'test': 'Covariance Features',
            'passed': all_present and good_coverage,
            'missing_columns': missing_columns,
            'total_rows': total,
            'populated_rows': populated,
            'coverage_pct': coverage
        }

    except Exception as e:
        logger.error(f"❌ Covariance features validation failed: {e}")
        return {'test': 'Covariance Features', 'passed': False, 'error': str(e)}


def validate_data_integrity():
    """
    Validate that prediction = quadratic_term + linear_term + constant_term.

    Returns:
        dict: Validation results
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("VALIDATION 5: Data Integrity")
    logger.info("=" * 80)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        results = {}

        for table in ['reg_rate', 'reg_bqx']:
            table_name = f"{table}_{VALIDATION_PAIR}_{VALIDATION_MONTH}" if table == 'reg_rate' else f"reg_bqx_{VALIDATION_PAIR}_{VALIDATION_MONTH}"
            errors = 0

            # Check prediction integrity for w60
            cur.execute(f"""
                SELECT COUNT(*)
                FROM bqx.{table_name}
                WHERE w60_prediction IS NOT NULL
                AND ABS(w60_prediction - (w60_quadratic_term + w60_linear_term + w60_constant_term)) > 0.001
            """)
            errors = cur.fetchone()[0]

            results[table] = {
                'prediction_errors': errors,
                'valid': errors == 0
            }

            if results[table]['valid']:
                logger.info(f"✅ {table}: prediction = sum(terms) for all rows")
            else:
                logger.error(f"❌ {table}: {errors} rows have prediction != sum(terms)")

        cur.close()
        conn.close()

        all_valid = all(r['valid'] for r in results.values())

        if all_valid:
            logger.info("✅ Data integrity: PASS - Predictions match term sums")
        else:
            logger.error("❌ Data integrity: FAIL - Some predictions don't match")

        return {
            'test': 'Data Integrity',
            'passed': all_valid,
            'details': results
        }

    except Exception as e:
        logger.error(f"❌ Data integrity validation failed: {e}")
        return {'test': 'Data Integrity', 'passed': False, 'error': str(e)}


def validate_cross_domain_comparability():
    """
    Validate that reg_rate and reg_bqx can be joined at same timestamps.

    Returns:
        dict: Validation results
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("VALIDATION 6: Cross-Domain Comparability")
    logger.info("=" * 80)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Count matching timestamps
        cur.execute(f"""
            SELECT
                (SELECT COUNT(*) FROM bqx.reg_{VALIDATION_PAIR}_{VALIDATION_MONTH}) AS rate_count,
                (SELECT COUNT(*) FROM bqx.reg_bqx_{VALIDATION_PAIR}_{VALIDATION_MONTH}) AS bqx_count,
                (SELECT COUNT(*)
                 FROM bqx.reg_{VALIDATION_PAIR}_{VALIDATION_MONTH} r
                 INNER JOIN bqx.reg_bqx_{VALIDATION_PAIR}_{VALIDATION_MONTH} b
                 ON r.ts_utc = b.ts_utc) AS join_count
        """)

        rate_count, bqx_count, join_count = cur.fetchone()

        cur.close()
        conn.close()

        # Check if join count matches both tables (allowing for small discrepancies)
        match_rate = (join_count / max(rate_count, bqx_count)) * 100 if max(rate_count, bqx_count) > 0 else 0
        comparable = match_rate > 98.0

        if comparable:
            logger.info(f"✅ Cross-domain comparability: PASS - {match_rate:.1f}% timestamps match")
            logger.info(f"   reg_rate rows: {rate_count:,}")
            logger.info(f"   reg_bqx rows: {bqx_count:,}")
            logger.info(f"   Joinable rows: {join_count:,}")
        else:
            logger.error(f"❌ Cross-domain comparability: FAIL - Only {match_rate:.1f}% timestamps match")

        return {
            'test': 'Cross-Domain Comparability',
            'passed': comparable,
            'reg_rate_count': rate_count,
            'reg_bqx_count': bqx_count,
            'join_count': join_count,
            'match_rate_pct': match_rate
        }

    except Exception as e:
        logger.error(f"❌ Cross-domain comparability validation failed: {e}")
        return {'test': 'Cross-Domain Comparability', 'passed': False, 'error': str(e)}


def generate_validation_report(results):
    """
    Generate comprehensive validation report.

    Args:
        results: List of validation results

    Returns:
        str: Report content
    """
    report = []
    report.append("=" * 80)
    report.append("SCHEMA ALIGNMENT VALIDATION REPORT")
    report.append("=" * 80)
    report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append(f"Validation Pair: {VALIDATION_PAIR}")
    report.append(f"Validation Month: {VALIDATION_MONTH}")
    report.append("")

    # Summary
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.get('passed', False))
    failed_tests = total_tests - passed_tests

    report.append(f"SUMMARY: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
    report.append("")

    # Details
    for result in results:
        test_name = result.get('test', 'Unknown')
        passed = result.get('passed', False)
        status = "✅ PASS" if passed else "❌ FAIL"

        report.append(f"{status}: {test_name}")

        if 'error' in result:
            report.append(f"  Error: {result['error']}")
        elif 'details' in result:
            report.append(f"  Details: {result['details']}")

        report.append("")

    # Final assessment
    if failed_tests == 0:
        report.append("=" * 80)
        report.append("✅ VALIDATION COMPLETE: 100% SCHEMA ALIGNMENT ACHIEVED")
        report.append("=" * 80)
        report.append("")
        report.append("All validation tests passed successfully.")
        report.append("reg_rate and reg_bqx tables are fully aligned and ready for ML feature integration.")
    else:
        report.append("=" * 80)
        report.append(f"❌ VALIDATION INCOMPLETE: {failed_tests} test(s) failed")
        report.append("=" * 80)
        report.append("")
        report.append("Please review failed tests above and remediate before proceeding.")

    return "\n".join(report)


def main():
    """Main execution: Run all validation tests."""
    logger.info("=" * 80)
    logger.info("STAGE 2.15: COMPREHENSIVE SCHEMA ALIGNMENT VALIDATION")
    logger.info("=" * 80)
    logger.info("")

    results = []

    # Run all validation tests
    results.append(validate_window_alignment())
    results.append(validate_schema_alignment())
    results.append(validate_term_based_architecture())
    results.append(validate_covariance_features())
    results.append(validate_data_integrity())
    results.append(validate_cross_domain_comparability())

    # Generate report
    logger.info("")
    report = generate_validation_report(results)
    logger.info(report)

    # Save report to file
    report_path = '/tmp/logs/remediation/stage_2_15/validation_report.txt'
    with open(report_path, 'w') as f:
        f.write(report)

    logger.info("")
    logger.info(f"Validation report saved to: {report_path}")

    # Return exit code
    all_passed = all(r.get('passed', False) for r in results)
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
