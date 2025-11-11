-- ============================================================================
-- Stage 1.5.4.1: Drop Existing BQX Tables
-- Duration: 0.5 hours
-- Purpose: Remove old bqx_* tables that use absolute rates
-- ============================================================================

\echo ''
\echo '============================================================================'
\echo 'Stage 1.5.4.1: Dropping BQX Tables (Absolute Rate Schema)'
\echo '============================================================================'
\echo ''
\echo 'Reason: Rebuild with index-based schema (rate_index instead of rate)'
\echo 'Impact: Removes 28 parent tables + 336 partitions (~5.3 GB)'
\echo ''

-- Drop all 28 BQX tables (CASCADE will drop all partitions)
\echo 'Dropping audcad...'
DROP TABLE IF EXISTS bqx.bqx_audcad CASCADE;

\echo 'Dropping audchf...'
DROP TABLE IF EXISTS bqx.bqx_audchf CASCADE;

\echo 'Dropping audjpy...'
DROP TABLE IF EXISTS bqx.bqx_audjpy CASCADE;

\echo 'Dropping audnzd...'
DROP TABLE IF EXISTS bqx.bqx_audnzd CASCADE;

\echo 'Dropping audusd...'
DROP TABLE IF EXISTS bqx.bqx_audusd CASCADE;

\echo 'Dropping cadchf...'
DROP TABLE IF EXISTS bqx.bqx_cadchf CASCADE;

\echo 'Dropping cadjpy...'
DROP TABLE IF EXISTS bqx.bqx_cadjpy CASCADE;

\echo 'Dropping chfjpy...'
DROP TABLE IF EXISTS bqx.bqx_chfjpy CASCADE;

\echo 'Dropping euraud...'
DROP TABLE IF EXISTS bqx.bqx_euraud CASCADE;

\echo 'Dropping eurcad...'
DROP TABLE IF EXISTS bqx.bqx_eurcad CASCADE;

\echo 'Dropping eurchf...'
DROP TABLE IF EXISTS bqx.bqx_eurchf CASCADE;

\echo 'Dropping eurgbp...'
DROP TABLE IF EXISTS bqx.bqx_eurgbp CASCADE;

\echo 'Dropping eurjpy...'
DROP TABLE IF EXISTS bqx.bqx_eurjpy CASCADE;

\echo 'Dropping eurnzd...'
DROP TABLE IF EXISTS bqx.bqx_eurnzd CASCADE;

\echo 'Dropping eurusd...'
DROP TABLE IF EXISTS bqx.bqx_eurusd CASCADE;

\echo 'Dropping gbpaud...'
DROP TABLE IF EXISTS bqx.bqx_gbpaud CASCADE;

\echo 'Dropping gbpcad...'
DROP TABLE IF EXISTS bqx.bqx_gbpcad CASCADE;

\echo 'Dropping gbpchf...'
DROP TABLE IF EXISTS bqx.bqx_gbpchf CASCADE;

\echo 'Dropping gbpjpy...'
DROP TABLE IF EXISTS bqx.bqx_gbpjpy CASCADE;

\echo 'Dropping gbpnzd...'
DROP TABLE IF EXISTS bqx.bqx_gbpnzd CASCADE;

\echo 'Dropping gbpusd...'
DROP TABLE IF EXISTS bqx.bqx_gbpusd CASCADE;

\echo 'Dropping nzdcad...'
DROP TABLE IF EXISTS bqx.bqx_nzdcad CASCADE;

\echo 'Dropping nzdchf...'
DROP TABLE IF EXISTS bqx.bqx_nzdchf CASCADE;

\echo 'Dropping nzdjpy...'
DROP TABLE IF EXISTS bqx.bqx_nzdjpy CASCADE;

\echo 'Dropping nzdusd...'
DROP TABLE IF EXISTS bqx.bqx_nzdusd CASCADE;

\echo 'Dropping usdcad...'
DROP TABLE IF EXISTS bqx.bqx_usdcad CASCADE;

\echo 'Dropping usdchf...'
DROP TABLE IF EXISTS bqx.bqx_usdchf CASCADE;

\echo 'Dropping usdjpy...'
DROP TABLE IF EXISTS bqx.bqx_usdjpy CASCADE;

\echo ''
\echo '============================================================================'
\echo 'Stage 1.5.4.1 Complete: All BQX Tables Dropped'
\echo '============================================================================'
\echo ''
\echo 'Next Steps:'
\echo '1. Run Stage 1.5.4.2: Create new BQX tables with index schema'
\echo '2. Run Stage 1.5.4.3: Backfill using backward_worker_index.py'
\echo ''
