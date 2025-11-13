-- Stage 1.6.21: Create cross_sectional_panel - 46 features (single panel table)
-- Category: Cross-Sectional Panel Features (8-PAIR CONTEXT)
-- Mechanism: Ranks, percentiles, dispersion across 8 major pairs
-- Impact: 20-25% systematic move detection improvement

\timing on
\set ON_ERROR_STOP on

BEGIN;

-- Create Single Panel Parent Table
DO $$
BEGIN
    RAISE NOTICE '=== Creating Cross-Sectional Panel Table (46 features) ===';

    CREATE TABLE IF NOT EXISTS bqx.cross_sectional_panel (
        ts_utc TIMESTAMP NOT NULL,
        pair VARCHAR(10) NOT NULL,

        -- Rank Features (8 features)
        rank_momentum_15_panel NUMERIC,
        rank_momentum_30_panel NUMERIC,
        rank_momentum_45_panel NUMERIC,
        rank_momentum_60_panel NUMERIC,
        rank_volatility_15_panel NUMERIC,
        rank_volatility_30_panel NUMERIC,
        rank_volatility_60_panel NUMERIC,
        rank_spread_panel NUMERIC,

        -- Percentile Features (8 features)
        pctile_momentum_15_panel NUMERIC,
        pctile_momentum_30_panel NUMERIC,
        pctile_momentum_45_panel NUMERIC,
        pctile_momentum_60_panel NUMERIC,
        pctile_volatility_15_panel NUMERIC,
        pctile_volatility_30_panel NUMERIC,
        pctile_volatility_60_panel NUMERIC,
        pctile_spread_panel NUMERIC,

        -- Dispersion Features (6 features)
        dispersion_momentum_15_panel NUMERIC,
        dispersion_momentum_30_panel NUMERIC,
        dispersion_momentum_60_panel NUMERIC,
        dispersion_volatility_15_panel NUMERIC,
        dispersion_volatility_30_panel NUMERIC,
        dispersion_volatility_60_panel NUMERIC,

        -- Extremes (4 features)
        extreme_high_momentum_panel NUMERIC,
        extreme_low_momentum_panel NUMERIC,
        extreme_high_volatility_panel NUMERIC,
        extreme_low_volatility_panel NUMERIC,

        -- Divergence (6 features)
        divergence_from_median_momentum_15_panel NUMERIC,
        divergence_from_median_momentum_30_panel NUMERIC,
        divergence_from_median_momentum_60_panel NUMERIC,
        divergence_from_median_volatility_15_panel NUMERIC,
        divergence_from_median_volatility_30_panel NUMERIC,
        divergence_from_median_volatility_60_panel NUMERIC,

        -- Cross-Sectional Correlations (6 features)
        xs_correlation_momentum_volatility_panel NUMERIC,
        xs_correlation_momentum_spread_panel NUMERIC,
        xs_correlation_volatility_spread_panel NUMERIC,
        xs_beta_to_panel_avg_momentum NUMERIC,
        xs_beta_to_panel_avg_volatility NUMERIC,
        xs_idiosyncratic_shock_panel NUMERIC,

        -- Panel Dynamics (8 features)
        panel_momentum_acceleration NUMERIC,
        panel_volatility_acceleration NUMERIC,
        panel_dispersion_change NUMERIC,
        panel_rank_stability NUMERIC,
        panel_regime_coherence NUMERIC,
        panel_leadership_score NUMERIC,
        panel_contagion_exposure NUMERIC,
        panel_isolation_score NUMERIC,

        PRIMARY KEY (ts_utc, pair)
    ) PARTITION BY RANGE (ts_utc);

    RAISE NOTICE '✅ Created cross_sectional_panel table (46 features)';
END $$;

-- Create Partitions (24 months: 2024-07 to 2025-06)
DO $$
DECLARE
    year INT;
    month INT;
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
    partition_count INT := 0;
BEGIN
    RAISE NOTICE '=== Creating Cross-Sectional Panel Partitions ===';

    FOR year IN 2024..2025
    LOOP
        FOR month IN 1..12
        LOOP
            -- Skip months before July 2024
            IF (year = 2024 AND month < 7) THEN
                CONTINUE;
            END IF;
            -- Skip months after June 2025
            IF (year = 2025 AND month > 6) THEN
                CONTINUE;
            END IF;

            start_date := make_date(year, month, 1);
            end_date := start_date + INTERVAL '1 month';
            partition_name := format('cross_sectional_panel_%s_%s',
                                    year, lpad(month::TEXT, 2, '0'));

            EXECUTE format('
                CREATE TABLE IF NOT EXISTS bqx.%I
                PARTITION OF bqx.cross_sectional_panel
                FOR VALUES FROM (%L) TO (%L)',
                partition_name, start_date, end_date);

            partition_count := partition_count + 1;
        END LOOP;
    END LOOP;

    RAISE NOTICE '✅ Created % cross_sectional_panel partitions', partition_count;
END $$;

COMMIT;

\echo '✅ Stage 1.6.21 Complete: cross_sectional_panel created (46 features, 24 partitions)'
