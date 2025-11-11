-- ============================================================================
-- Drop ml_corr* Tables
-- Reason: Target changed from pre-BQX to future BQX values at t+60
-- Must recalculate correlations against new target: w60_bqx_return at t+60
-- ============================================================================

-- Cost Savings: Dropping 2.4 TB of outdated correlation data
-- Will be recreated after Stage 1.5.4 (BQX recalculation) completes

\echo 'Dropping ml_corr_triangulation_partitioned (parent table)...'
DROP TABLE IF EXISTS bqx.ml_corr_triangulation_partitioned CASCADE;

\echo 'Successfully dropped ml_corr* tables and all 85 partitions'
\echo 'Cost savings: ~2.4 TB storage freed'
\echo ''
\echo 'Note: ml_corr* tables will be recreated in new stage after BQX recalculation'
\echo 'New target: w60_bqx_return at t+60 (future BQX value)'
