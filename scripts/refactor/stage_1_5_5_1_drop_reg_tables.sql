-- ============================================================================
-- Stage 1.5.5.1: Drop Existing REG Tables
-- Duration: 0.5 hours
-- Purpose: Remove old reg_* tables that use absolute rates and _norm fields
-- ============================================================================

\echo ''
\echo '============================================================================'
\echo 'Stage 1.5.5.1: Dropping REG Tables (Absolute Rate Schema with _norm fields)'
\echo '============================================================================'
\echo ''
\echo 'Reason: Rebuild with index-based schema (rate_index, no _norm fields)'
\echo 'Impact: Removes 28 parent tables + 476 partitions (~8.9 GB)'
\echo ''

-- Drop all 28 REG tables (CASCADE will drop all partitions)
\echo 'Dropping reg_audcad...'
DROP TABLE IF EXISTS bqx.reg_audcad CASCADE;

\echo 'Dropping reg_audchf...'
DROP TABLE IF EXISTS bqx.reg_audchf CASCADE;

\echo 'Dropping reg_audjpy...'
DROP TABLE IF EXISTS bqx.reg_audjpy CASCADE;

\echo 'Dropping reg_audnzd...'
DROP TABLE IF EXISTS bqx.reg_audnzd CASCADE;

\echo 'Dropping reg_audusd...'
DROP TABLE IF EXISTS bqx.reg_audusd CASCADE;

\echo 'Dropping reg_cadchf...'
DROP TABLE IF EXISTS bqx.reg_cadchf CASCADE;

\echo 'Dropping reg_cadjpy...'
DROP TABLE IF EXISTS bqx.reg_cadjpy CASCADE;

\echo 'Dropping reg_chfjpy...'
DROP TABLE IF EXISTS bqx.reg_chfjpy CASCADE;

\echo 'Dropping reg_euraud...'
DROP TABLE IF EXISTS bqx.reg_euraud CASCADE;

\echo 'Dropping reg_eurcad...'
DROP TABLE IF EXISTS bqx.reg_eurcad CASCADE;

\echo 'Dropping reg_eurchf...'
DROP TABLE IF EXISTS bqx.reg_eurchf CASCADE;

\echo 'Dropping reg_eurgbp...'
DROP TABLE IF EXISTS bqx.reg_eurgbp CASCADE;

\echo 'Dropping reg_eurjpy...'
DROP TABLE IF EXISTS bqx.reg_eurjpy CASCADE;

\echo 'Dropping reg_eurnzd...'
DROP TABLE IF EXISTS bqx.reg_eurnzd CASCADE;

\echo 'Dropping reg_eurusd...'
DROP TABLE IF EXISTS bqx.reg_eurusd CASCADE;

\echo 'Dropping reg_gbpaud...'
DROP TABLE IF EXISTS bqx.reg_gbpaud CASCADE;

\echo 'Dropping reg_gbpcad...'
DROP TABLE IF EXISTS bqx.reg_gbpcad CASCADE;

\echo 'Dropping reg_gbpchf...'
DROP TABLE IF EXISTS bqx.reg_gbpchf CASCADE;

\echo 'Dropping reg_gbpjpy...'
DROP TABLE IF EXISTS bqx.reg_gbpjpy CASCADE;

\echo 'Dropping reg_gbpnzd...'
DROP TABLE IF EXISTS bqx.reg_gbpnzd CASCADE;

\echo 'Dropping reg_gbpusd...'
DROP TABLE IF EXISTS bqx.reg_gbpusd CASCADE;

\echo 'Dropping reg_nzdcad...'
DROP TABLE IF EXISTS bqx.reg_nzdcad CASCADE;

\echo 'Dropping reg_nzdchf...'
DROP TABLE IF EXISTS bqx.reg_nzdchf CASCADE;

\echo 'Dropping reg_nzdjpy...'
DROP TABLE IF EXISTS bqx.reg_nzdjpy CASCADE;

\echo 'Dropping reg_nzdusd...'
DROP TABLE IF EXISTS bqx.reg_nzdusd CASCADE;

\echo 'Dropping reg_usdcad...'
DROP TABLE IF EXISTS bqx.reg_usdcad CASCADE;

\echo 'Dropping reg_usdchf...'
DROP TABLE IF EXISTS bqx.reg_usdchf CASCADE;

\echo 'Dropping reg_usdjpy...'
DROP TABLE IF EXISTS bqx.reg_usdjpy CASCADE;

\echo ''
\echo '============================================================================'
\echo 'Stage 1.5.5.1 Complete: All REG Tables Dropped'
\echo '============================================================================'
\echo ''
\echo 'Next Steps:'
\echo '1. Run Stage 1.5.5.2: Create new REG tables with index schema (no _norm fields)'
\echo '2. Run Stage 1.5.5.3: Backfill using regression_worker_index.py'
\echo ''
