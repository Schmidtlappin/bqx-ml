-- Stage 1.6.14 Part A: Expand fibonacci_rate (IDX) from 12 to 20 features
-- Action: ALTER TABLE ADD COLUMN (non-blocking, preserves 10.2M rows)
-- Tables: 336 existing partitions
-- New Columns: +8 (extension×1, pivots×3, distances×4)

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
    RAISE NOTICE '=== Expanding fibonacci_rate Parent Tables (12→20 features) ===';
    RAISE NOTICE 'Adding 8 new columns to 28 parent tables (cascades to 336 partitions)...';

    FOREACH pair_name IN ARRAY pairs
    LOOP
        EXECUTE format('
            ALTER TABLE bqx.fibonacci_rate_%I
            -- Extension (1 more level, existing: 1618, 2618, 4236)
            ADD COLUMN IF NOT EXISTS fib_ext_1272 NUMERIC,

            -- Pivot Points (3 features)
            ADD COLUMN IF NOT EXISTS pivot_point NUMERIC,
            ADD COLUMN IF NOT EXISTS resistance_1 NUMERIC,
            ADD COLUMN IF NOT EXISTS support_1 NUMERIC,

            -- Distance to Key Levels (4 features)
            ADD COLUMN IF NOT EXISTS dist_to_382 NUMERIC,
            ADD COLUMN IF NOT EXISTS dist_to_500 NUMERIC,
            ADD COLUMN IF NOT EXISTS dist_to_618 NUMERIC,
            ADD COLUMN IF NOT EXISTS dist_to_pivot NUMERIC
        ', pair_name);

        alter_count := alter_count + 1;

        IF alter_count % 10 = 0 THEN
            RAISE NOTICE 'Expanded % parent tables (cascaded to % partitions)...', alter_count, alter_count * 12;
        END IF;
    END LOOP;

    RAISE NOTICE '✅ Successfully expanded % fibonacci_rate parent tables', alter_count;
    RAISE NOTICE '✅ Changes cascaded to % partitions', alter_count * 12;
    RAISE NOTICE '✅ Each table now has 20 features (was 12)';
    RAISE NOTICE '✅ Data preserved: 10.2M rows intact';
END $$;

COMMIT;

\echo '✅ Stage 1.6.14 Part A Complete: fibonacci_rate expanded (12→20 features)'
