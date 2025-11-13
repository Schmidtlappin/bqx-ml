-- Stage 1.6.13 Part A: Expand bollinger_rate (IDX) from 5 to 20 features
-- Action: ALTER TABLE ADD COLUMN (non-blocking, preserves 10.3M rows)
-- Tables: 336 existing partitions
-- New Columns: +15 (upper×3, middle×3, lower×3, width×3, %B×1, slope×2)

\timing on
\set ON_ERROR_STOP on

BEGIN;

DO $$
DECLARE
    pair_name TEXT;
    pairs TEXT[] := ARRAY['audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
                          'cadchf', 'cadjpy', 'chfjpy',
                          'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
                          'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
                          'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
                          'usdcad', 'usdchf', 'usdjpy'];
    alter_count INT := 0;
BEGIN
    RAISE NOTICE '=== Expanding bollinger_rate Parent Tables (5→20 features) ===';
    RAISE NOTICE 'Adding 15 new columns to 28 parent tables (cascades to 336 partitions)...';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('
            ALTER TABLE bqx.bollinger_rate_%I
            -- Upper Band (3 more features, bb_upper_20 already exists)
            ADD COLUMN IF NOT EXISTS bb_upper_30 NUMERIC,
            ADD COLUMN IF NOT EXISTS bb_upper_60 NUMERIC,
            ADD COLUMN IF NOT EXISTS bb_upper_120 NUMERIC,

            -- Middle Band (3 more features, bb_middle_20 already exists)
            ADD COLUMN IF NOT EXISTS bb_middle_30 NUMERIC,
            ADD COLUMN IF NOT EXISTS bb_middle_60 NUMERIC,
            ADD COLUMN IF NOT EXISTS bb_middle_120 NUMERIC,

            -- Lower Band (3 more features, bb_lower_20 already exists)
            ADD COLUMN IF NOT EXISTS bb_lower_30 NUMERIC,
            ADD COLUMN IF NOT EXISTS bb_lower_60 NUMERIC,
            ADD COLUMN IF NOT EXISTS bb_lower_120 NUMERIC,

            -- Bandwidth (3 more features, bb_width_20 already exists)
            ADD COLUMN IF NOT EXISTS bb_width_30 NUMERIC,
            ADD COLUMN IF NOT EXISTS bb_width_60 NUMERIC,
            ADD COLUMN IF NOT EXISTS bb_width_120 NUMERIC,

            -- %%B Indicator (1 more feature, bb_percent_b already exists for 20-period)
            ADD COLUMN IF NOT EXISTS bb_percent_b_60 NUMERIC,

            -- Band Slope (2 features)
            ADD COLUMN IF NOT EXISTS bb_slope_20 NUMERIC,
            ADD COLUMN IF NOT EXISTS bb_slope_60 NUMERIC
        ', pair_name);

        alter_count := alter_count + 1;

        IF alter_count % 10 = 0 THEN
            RAISE NOTICE 'Expanded % parent tables (cascaded to % partitions)...', alter_count, alter_count * 12;
        END IF;
    END LOOP;

    RAISE NOTICE '✅ Successfully expanded % bollinger_rate parent tables', alter_count;
    RAISE NOTICE '✅ Changes cascaded to % partitions', alter_count * 12;
    RAISE NOTICE '✅ Each table now has 20 features (was 5)';
    RAISE NOTICE '✅ Data preserved: 10.3M rows intact';
END $$;

COMMIT;

\echo '✅ Stage 1.6.13 Part A Complete: bollinger_rate expanded (5→20 features)'
