-- ============================================================================
-- Stage 1.5.5.2: Create REG Tables with Index Schema (No _norm fields)
-- Duration: 0.5 hours
-- Purpose: Create new reg_* tables using rate_index (not absolute rates)
-- ============================================================================

\echo ''
\echo '============================================================================'
\echo 'Stage 1.5.5.2: Creating REG Tables (Index Schema - No _norm fields)'
\echo '============================================================================'
\echo ''
\echo 'Schema Changes from Old:'
\echo '- rate → rate_index (forex index around 100)'
\echo '- REMOVED: 18 _norm fields (quad_norm, lin_norm, resid_norm for all windows)'
\echo '- Field count: 75 → 57 (24% reduction)'
\echo ''

-- Create REG tables with index-based schema
DO $$
DECLARE
    pair_name TEXT;
    year INT;
    month INT;
    partition_name TEXT;
    start_date TEXT;
    end_date TEXT;
BEGIN
    -- Array of all 28 pairs
    FOR pair_name IN
        SELECT unnest(ARRAY[
            'audcad', 'audchf', 'audjpy', 'audnzd', 'audusd',
            'cadchf', 'cadjpy', 'chfjpy',
            'euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd',
            'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd',
            'nzdcad', 'nzdchf', 'nzdjpy', 'nzdusd',
            'usdcad', 'usdchf', 'usdjpy'
        ])
    LOOP
        -- Create parent table
        EXECUTE format($f$
            CREATE TABLE bqx.reg_%s (
                -- Core fields
                ts_utc TIMESTAMP WITH TIME ZONE NOT NULL,
                rate_index DOUBLE PRECISION,

                -- Window 60 (60 minutes) - 9 fields (removed 3 _norm fields)
                w60_a_coef DOUBLE PRECISION,
                w60_b_coef DOUBLE PRECISION,
                w60_c_coef DOUBLE PRECISION,
                w60_a_term DOUBLE PRECISION,
                w60_b_term DOUBLE PRECISION,
                w60_r2 DOUBLE PRECISION,
                w60_rmse DOUBLE PRECISION,
                w60_yhat_end DOUBLE PRECISION,
                w60_resid_end DOUBLE PRECISION,

                -- Window 90 (90 minutes) - 9 fields
                w90_a_coef DOUBLE PRECISION,
                w90_b_coef DOUBLE PRECISION,
                w90_c_coef DOUBLE PRECISION,
                w90_a_term DOUBLE PRECISION,
                w90_b_term DOUBLE PRECISION,
                w90_r2 DOUBLE PRECISION,
                w90_rmse DOUBLE PRECISION,
                w90_yhat_end DOUBLE PRECISION,
                w90_resid_end DOUBLE PRECISION,

                -- Window 150 (2.5 hours) - 9 fields
                w150_a_coef DOUBLE PRECISION,
                w150_b_coef DOUBLE PRECISION,
                w150_c_coef DOUBLE PRECISION,
                w150_a_term DOUBLE PRECISION,
                w150_b_term DOUBLE PRECISION,
                w150_r2 DOUBLE PRECISION,
                w150_rmse DOUBLE PRECISION,
                w150_yhat_end DOUBLE PRECISION,
                w150_resid_end DOUBLE PRECISION,

                -- Window 240 (4 hours) - 9 fields
                w240_a_coef DOUBLE PRECISION,
                w240_b_coef DOUBLE PRECISION,
                w240_c_coef DOUBLE PRECISION,
                w240_a_term DOUBLE PRECISION,
                w240_b_term DOUBLE PRECISION,
                w240_r2 DOUBLE PRECISION,
                w240_rmse DOUBLE PRECISION,
                w240_yhat_end DOUBLE PRECISION,
                w240_resid_end DOUBLE PRECISION,

                -- Window 390 (6.5 hours) - 9 fields
                w390_a_coef DOUBLE PRECISION,
                w390_b_coef DOUBLE PRECISION,
                w390_c_coef DOUBLE PRECISION,
                w390_a_term DOUBLE PRECISION,
                w390_b_term DOUBLE PRECISION,
                w390_r2 DOUBLE PRECISION,
                w390_rmse DOUBLE PRECISION,
                w390_yhat_end DOUBLE PRECISION,
                w390_resid_end DOUBLE PRECISION,

                -- Window 630 (10.5 hours) - 9 fields
                w630_a_coef DOUBLE PRECISION,
                w630_b_coef DOUBLE PRECISION,
                w630_c_coef DOUBLE PRECISION,
                w630_a_term DOUBLE PRECISION,
                w630_b_term DOUBLE PRECISION,
                w630_r2 DOUBLE PRECISION,
                w630_rmse DOUBLE PRECISION,
                w630_yhat_end DOUBLE PRECISION,
                w630_resid_end DOUBLE PRECISION,

                -- Metadata
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

                PRIMARY KEY (ts_utc)
            ) PARTITION BY RANGE (ts_utc);
        $f$, pair_name);

        -- Create monthly partitions (2024-07 through 2025-10)
        -- REG tables have 16 months of data
        FOR year IN 2024..2025 LOOP
            FOR month IN 1..12 LOOP
                -- Only create partitions for 2024-07 through 2025-10
                IF (year = 2024 AND month >= 7) OR (year = 2025 AND month <= 10) THEN
                    partition_name := format('reg_%s_%s_%s',
                        pair_name,
                        year,
                        LPAD(month::text, 2, '0')
                    );
                    start_date := format('%s-%s-01', year, LPAD(month::text, 2, '0'));

                    IF month = 12 THEN
                        end_date := format('%s-01-01', year + 1);
                    ELSE
                        end_date := format('%s-%s-01', year, LPAD((month + 1)::text, 2, '0'));
                    END IF;

                    EXECUTE format($f$
                        CREATE TABLE bqx.%s PARTITION OF bqx.reg_%s
                        FOR VALUES FROM (%L) TO (%L);
                    $f$, partition_name, pair_name, start_date, end_date);
                END IF;
            END LOOP;
        END LOOP;

        RAISE NOTICE 'Created reg_% with 16 monthly partitions (2024-07 through 2025-10)', pair_name;
    END LOOP;
END $$;

\echo ''
\echo '============================================================================'
\echo 'Stage 1.5.5.2 Complete: REG Tables Created with Index Schema'
\echo '============================================================================'
\echo ''
\echo 'Summary:'
\echo '- 28 parent tables created'
\echo '- 448 partitions created (28 pairs × 16 months)'
\echo '- Schema uses rate_index (not absolute rates)'
\echo '- Removed 18 _norm fields (24% reduction: 75 → 57 fields)'
\echo ''
\echo 'Fields per window: 9 (was 12)'
\echo '  - Coefficients: a_coef, b_coef, c_coef'
\echo '  - Terms: a_term, b_term (in index units, already comparable)'
\echo '  - Fit metrics: r2, rmse'
\echo '  - Predictions: yhat_end'
\echo '  - Residuals: resid_end (in index units, already comparable)'
\echo ''
\echo 'REMOVED per window (3 fields):'
\echo '  - quad_norm (redundant: a_term already in index units)'
\echo '  - lin_norm (redundant: b_term already in index units)'
\echo '  - resid_norm (redundant: resid_end already in index units)'
\echo ''
\echo 'Next Steps:'
\echo '1. Run Stage 1.5.5.3: Backfill using regression_worker_index.py'
\echo '2. Estimated time: 2 hours (parallel execution)'
\echo ''
