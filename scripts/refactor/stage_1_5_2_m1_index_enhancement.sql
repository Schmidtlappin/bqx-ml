-- ============================================================================
-- Stage 1.5.2: M1 Table Enhancement
-- Add rate_index column and calculate index values for all M1 tables
-- ============================================================================

-- TSK-1.5.2.1: Add rate_index column to all 28 M1 tables
-- ============================================================================

ALTER TABLE bqx.m1_audcad ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_audchf ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_audjpy ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_audnzd ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_audusd ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_cadchf ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_cadjpy ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_chfjpy ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_euraud ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_eurcad ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_eurchf ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_eurgbp ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_eurjpy ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_eurnzd ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_eurusd ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_gbpaud ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_gbpcad ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_gbpchf ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_gbpjpy ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_gbpnzd ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_gbpusd ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_nzdcad ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_nzdchf ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_nzdjpy ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_nzdusd ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_usdcad ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_usdchf ADD COLUMN IF NOT EXISTS rate_index NUMERIC;
ALTER TABLE bqx.m1_usdjpy ADD COLUMN IF NOT EXISTS rate_index NUMERIC;

\echo 'TSK-1.5.2.1 Complete: rate_index column added to all 28 M1 tables'

-- TSK-1.5.2.2: Calculate rate_index for all M1 rows
-- Formula: (close / baseline_rate) * 100
-- This will take ~2 hours for 3GB of M1 data
-- ============================================================================

\echo 'TSK-1.5.2.2 Starting: Calculating rate_index values (estimated 2 hours)...'

-- audcad
UPDATE bqx.m1_audcad m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'audcad';

\echo 'audcad complete (1/28)'

-- audchf
UPDATE bqx.m1_audchf m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'audchf';

\echo 'audchf complete (2/28)'

-- audjpy
UPDATE bqx.m1_audjpy m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'audjpy';

\echo 'audjpy complete (3/28)'

-- audnzd
UPDATE bqx.m1_audnzd m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'audnzd';

\echo 'audnzd complete (4/28)'

-- audusd
UPDATE bqx.m1_audusd m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'audusd';

\echo 'audusd complete (5/28)'

-- cadchf
UPDATE bqx.m1_cadchf m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'cadchf';

\echo 'cadchf complete (6/28)'

-- cadjpy
UPDATE bqx.m1_cadjpy m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'cadjpy';

\echo 'cadjpy complete (7/28)'

-- chfjpy
UPDATE bqx.m1_chfjpy m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'chfjpy';

\echo 'chfjpy complete (8/28)'

-- euraud
UPDATE bqx.m1_euraud m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'euraud';

\echo 'euraud complete (9/28)'

-- eurcad
UPDATE bqx.m1_eurcad m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'eurcad';

\echo 'eurcad complete (10/28)'

-- eurchf
UPDATE bqx.m1_eurchf m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'eurchf';

\echo 'eurchf complete (11/28)'

-- eurgbp
UPDATE bqx.m1_eurgbp m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'eurgbp';

\echo 'eurchf complete (12/28)'

-- eurjpy
UPDATE bqx.m1_eurjpy m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'eurjpy';

\echo 'eurjpy complete (13/28)'

-- eurnzd
UPDATE bqx.m1_eurnzd m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'eurnzd';

\echo 'eurnzd complete (14/28)'

-- eurusd
UPDATE bqx.m1_eurusd m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'eurusd';

\echo 'eurusd complete (15/28)'

-- gbpaud
UPDATE bqx.m1_gbpaud m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'gbpaud';

\echo 'gbpaud complete (16/28)'

-- gbpcad
UPDATE bqx.m1_gbpcad m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'gbpcad';

\echo 'gbpcad complete (17/28)'

-- gbpchf
UPDATE bqx.m1_gbpchf m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'gbpchf';

\echo 'gbpchf complete (18/28)'

-- gbpjpy
UPDATE bqx.m1_gbpjpy m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'gbpjpy';

\echo 'gbpjpy complete (19/28)'

-- gbpnzd
UPDATE bqx.m1_gbpnzd m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'gbpnzd';

\echo 'gbpnzd complete (20/28)'

-- gbpusd
UPDATE bqx.m1_gbpusd m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'gbpusd';

\echo 'gbpusd complete (21/28)'

-- nzdcad
UPDATE bqx.m1_nzdcad m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'nzdcad';

\echo 'nzdcad complete (22/28)'

-- nzdchf
UPDATE bqx.m1_nzdchf m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'nzdchf';

\echo 'nzdchf complete (23/28)'

-- nzdjpy
UPDATE bqx.m1_nzdjpy m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'nzdjpy';

\echo 'nzdjpy complete (24/28)'

-- nzdusd
UPDATE bqx.m1_nzdusd m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'nzdusd';

\echo 'nzdusd complete (25/28)'

-- usdcad
UPDATE bqx.m1_usdcad m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'usdcad';

\echo 'usdcad complete (26/28)'

-- usdchf
UPDATE bqx.m1_usdchf m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'usdchf';

\echo 'usdchf complete (27/28)'

-- usdjpy
UPDATE bqx.m1_usdjpy m
SET rate_index = (m.close / b.baseline_rate) * 100
FROM bqx.baseline_rates b
WHERE b.pair = 'usdjpy';

\echo 'usdjpy complete (28/28)'
\echo 'TSK-1.5.2.2 Complete: rate_index calculated for all M1 tables'

-- TSK-1.5.2.3: Create indexes on rate_index column
-- ============================================================================

\echo 'TSK-1.5.2.3 Starting: Creating indexes on rate_index column...'

CREATE INDEX IF NOT EXISTS idx_m1_audcad_rate_index ON bqx.m1_audcad(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_audchf_rate_index ON bqx.m1_audchf(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_audjpy_rate_index ON bqx.m1_audjpy(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_audnzd_rate_index ON bqx.m1_audnzd(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_audusd_rate_index ON bqx.m1_audusd(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_cadchf_rate_index ON bqx.m1_cadchf(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_cadjpy_rate_index ON bqx.m1_cadjpy(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_chfjpy_rate_index ON bqx.m1_chfjpy(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_euraud_rate_index ON bqx.m1_euraud(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_eurcad_rate_index ON bqx.m1_eurcad(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_eurchf_rate_index ON bqx.m1_eurchf(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_eurgbp_rate_index ON bqx.m1_eurgbp(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_eurjpy_rate_index ON bqx.m1_eurjpy(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_eurnzd_rate_index ON bqx.m1_eurnzd(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_eurusd_rate_index ON bqx.m1_eurusd(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_gbpaud_rate_index ON bqx.m1_gbpaud(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_gbpcad_rate_index ON bqx.m1_gbpcad(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_gbpchf_rate_index ON bqx.m1_gbpchf(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_gbpjpy_rate_index ON bqx.m1_gbpjpy(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_gbpnzd_rate_index ON bqx.m1_gbpnzd(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_gbpusd_rate_index ON bqx.m1_gbpusd(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_nzdcad_rate_index ON bqx.m1_nzdcad(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_nzdchf_rate_index ON bqx.m1_nzdchf(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_nzdjpy_rate_index ON bqx.m1_nzdjpy(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_nzdusd_rate_index ON bqx.m1_nzdusd(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_usdcad_rate_index ON bqx.m1_usdcad(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_usdchf_rate_index ON bqx.m1_usdchf(rate_index);
CREATE INDEX IF NOT EXISTS idx_m1_usdjpy_rate_index ON bqx.m1_usdjpy(rate_index);

\echo 'TSK-1.5.2.3 Complete: Indexes created on rate_index column for all 28 M1 tables'

-- Verify results
\echo ''
\echo '==================================================================='
\echo 'STAGE 1.5.2 VERIFICATION'
\echo '==================================================================='

-- Sample verification query
SELECT
    'eurusd' as pair,
    time,
    close as absolute_rate,
    rate_index,
    ROUND((rate_index - 100.0)::numeric, 2) as pct_change_from_baseline
FROM bqx.m1_eurusd
WHERE time >= '2024-07-01 00:00:00'
ORDER BY time
LIMIT 10;

\echo ''
\echo 'Stage 1.5.2 complete: M1 tables enhanced with rate_index'
