-- Stage 2.12: Backup reg_bqx Tables Before Rebuild
-- Date: 2025-11-16
-- Purpose: Create backups of all existing reg_bqx tables before dropping and rebuilding
-- Backup schema: bqx_backup_2025_11_16

-- Create backup schema
CREATE SCHEMA IF NOT EXISTS bqx_backup_2025_11_16;

-- Backup all 28 reg_bqx parent tables
-- Note: This will backup the parent table structure and all child partitions

-- Sample backup for one pair (EURUSD)
-- Uncomment and run for each pair as needed
-- CREATE TABLE bqx_backup_2025_11_16.reg_bqx_eurusd AS SELECT * FROM bqx.reg_bqx_eurusd;

-- Full backup script for all 28 pairs:
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_audcad AS SELECT * FROM bqx.reg_bqx_audcad;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_audchf AS SELECT * FROM bqx.reg_bqx_audchf;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_audjpy AS SELECT * FROM bqx.reg_bqx_audjpy;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_audnzd AS SELECT * FROM bqx.reg_bqx_audnzd;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_audusd AS SELECT * FROM bqx.reg_bqx_audusd;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_cadchf AS SELECT * FROM bqx.reg_bqx_cadchf;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_cadjpy AS SELECT * FROM bqx.reg_bqx_cadjpy;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_chfjpy AS SELECT * FROM bqx.reg_bqx_chfjpy;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_euraud AS SELECT * FROM bqx.reg_bqx_euraud;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_eurcad AS SELECT * FROM bqx.reg_bqx_eurcad;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_eurchf AS SELECT * FROM bqx.reg_bqx_eurchf;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_eurgbp AS SELECT * FROM bqx.reg_bqx_eurgbp;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_eurjpy AS SELECT * FROM bqx.reg_bqx_eurjpy;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_eurnzd AS SELECT * FROM bqx.reg_bqx_eurnzd;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_eurusd AS SELECT * FROM bqx.reg_bqx_eurusd;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_gbpaud AS SELECT * FROM bqx.reg_bqx_gbpaud;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_gbpcad AS SELECT * FROM bqx.reg_bqx_gbpcad;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_gbpchf AS SELECT * FROM bqx.reg_bqx_gbpchf;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_gbpjpy AS SELECT * FROM bqx.reg_bqx_gbpjpy;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_gbpnzd AS SELECT * FROM bqx.reg_bqx_gbpnzd;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_gbpusd AS SELECT * FROM bqx.reg_bqx_gbpusd;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_nzdcad AS SELECT * FROM bqx.reg_bqx_nzdcad;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_nzdchf AS SELECT * FROM bqx.reg_bqx_nzdchf;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_nzdjpy AS SELECT * FROM bqx.reg_bqx_nzdjpy;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_nzdusd AS SELECT * FROM bqx.reg_bqx_nzdusd;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_usdcad AS SELECT * FROM bqx.reg_bqx_usdcad;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_usdchf AS SELECT * FROM bqx.reg_bqx_usdchf;
CREATE TABLE bqx_backup_2025_11_16.reg_bqx_usdjpy AS SELECT * FROM bqx.reg_bqx_usdjpy;

-- Verify backup
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'bqx_backup_2025_11_16'
ORDER BY tablename;

-- To restore a table if needed:
-- DROP TABLE bqx.reg_bqx_eurusd CASCADE;
-- CREATE TABLE bqx.reg_bqx_eurusd AS SELECT * FROM bqx_backup_2025_11_16.reg_bqx_eurusd;
