-- ============================================================================
-- Stage 1.5.1: Baseline Rate Setup
-- Creates baseline_rates table and populates with 2024-07-01 rates
-- ============================================================================

-- TSK-1.5.1.1: Create bqx.baseline_rates table
-- ============================================================================
CREATE TABLE IF NOT EXISTS bqx.baseline_rates (
    pair VARCHAR(10) PRIMARY KEY,
    baseline_date TIMESTAMP WITH TIME ZONE NOT NULL,
    baseline_rate NUMERIC NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE bqx.baseline_rates IS 'Baseline forex rates for index calculation (base-100)';
COMMENT ON COLUMN bqx.baseline_rates.pair IS 'Forex pair name (e.g., eurusd, usdjpy)';
COMMENT ON COLUMN bqx.baseline_rates.baseline_date IS 'Date and time of baseline rate';
COMMENT ON COLUMN bqx.baseline_rates.baseline_rate IS 'Absolute rate at baseline date';
COMMENT ON COLUMN bqx.baseline_rates.created_at IS 'Timestamp when record was created';

-- TSK-1.5.1.2: Populate baseline rates from 2024-07-01
-- ============================================================================

-- All 28 forex pairs
INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'audcad', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_audcad
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'audchf', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_audchf
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'audjpy', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_audjpy
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'audnzd', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_audnzd
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'audusd', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_audusd
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'cadchf', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_cadchf
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'cadjpy', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_cadjpy
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'chfjpy', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_chfjpy
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'euraud', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_euraud
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'eurcad', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_eurcad
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'eurchf', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_eurchf
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'eurgbp', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_eurgbp
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'eurjpy', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_eurjpy
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'eurnzd', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_eurnzd
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'eurusd', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_eurusd
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'gbpaud', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_gbpaud
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'gbpcad', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_gbpcad
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'gbpchf', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_gbpchf
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'gbpjpy', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_gbpjpy
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'gbpnzd', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_gbpnzd
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'gbpusd', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_gbpusd
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'nzdcad', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_nzdcad
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'nzdchf', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_nzdchf
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'nzdjpy', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_nzdjpy
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'nzdusd', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_nzdusd
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'usdcad', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_usdcad
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'usdchf', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_usdchf
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

INSERT INTO bqx.baseline_rates (pair, baseline_date, baseline_rate)
SELECT 'usdjpy', '2024-07-01 00:00:00+00'::TIMESTAMP WITH TIME ZONE, close
FROM bqx.m1_usdjpy
WHERE time = '2024-07-01 00:00:00'::TIMESTAMP
LIMIT 1;

-- Verify results
SELECT
    pair,
    baseline_date,
    baseline_rate,
    (100.0 / baseline_rate * 100) as index_at_baseline  -- Should be 100.00
FROM bqx.baseline_rates
ORDER BY pair;
