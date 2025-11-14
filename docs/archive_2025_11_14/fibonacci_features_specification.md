# Fibonacci Features Specification - Track 2

## Overview

This document specifies 12 Fibonacci retracement and extension features using Williams Fractals (n=3) for swing detection. These features will be added to Track 2 (Stage 1.6.1: OHLC Index Schema Enhancement) as they depend on OHLC index columns.

**Track**: Track 2 (OHLC-dependent features)
**Stage**: 1.6.1 - OHLC Index Schema Enhancement
**Dependencies**: M1 OHLC index columns (high_index, low_index, open_index)
**Target Tables**: `fibonacci_features_{pair}` (28 tables, monthly partitions)
**Estimated Development Time**: 3-4 hours
**Estimated Backfill Time**: 4-5 hours (336 partitions, 8 threads)

## Feature Categories

### 1. Fibonacci Retracement Levels (5 features)
Measures current rate position relative to recent swing range:

1. **fib_retracement_23_6** - Distance to 23.6% retracement level
2. **fib_retracement_38_2** - Distance to 38.2% retracement level (Golden Ratio conjugate)
3. **fib_retracement_50_0** - Distance to 50% retracement level (midpoint)
4. **fib_retracement_61_8** - Distance to 61.8% retracement level (Golden Ratio)
5. **fib_retracement_78_6** - Distance to 78.6% retracement level (deep retracement)

**Formula**:
```
swing_range = swing_high_index - swing_low_index
fib_level_index = swing_high_index - (swing_range × fib_ratio)
fib_retracement_X = current_rate_index - fib_level_index
```

### 2. Fibonacci Extension Levels (3 features)
Measures breakout targets beyond swing range:

1. **fib_extension_127_2** - Distance to 127.2% extension (minor extension)
2. **fib_extension_161_8** - Distance to 161.8% extension (Golden Ratio extension)
3. **fib_extension_261_8** - Distance to 261.8% extension (major target)

**Formula**:
```
swing_range = swing_high_index - swing_low_index
fib_level_index = swing_high_index + (swing_range × (fib_ratio - 1.0))
fib_extension_X = current_rate_index - fib_level_index
```

### 3. Meta Features (4 features)
Contextual information about Fibonacci grid:

1. **fib_nearest_level** - Distance to nearest Fibonacci level (any retracement or extension)
2. **fib_grid_position** - Normalized position within grid (0.0 = swing low, 1.0 = swing high)
3. **fib_time_since_swing** - Minutes elapsed since most recent swing point detected
4. **fib_grid_strength** - Confidence score based on swing magnitude and age

**Formulas**:
```
fib_nearest_level = min(|current_index - fib_level_index| for all 8 levels)

fib_grid_position = (current_rate_index - swing_low_index) / swing_range
                   # Clipped to [-0.5, 1.5] to handle breakouts

fib_time_since_swing = current_time - max(swing_high_time, swing_low_time)
                      # In minutes

fib_grid_strength = (swing_range / mean_atr_20) × exp(-age_hours / 24)
                   # Range normalized by ATR, decayed by age
```

## Swing Detection: Williams Fractals (n=3)

### Algorithm
Williams Fractals detect local highs and lows using a 5-bar pattern:

**Swing High (Fractal Up)**:
```
high[i-2] < high[i-1] < high[i] > high[i+1] > high[i+2]
```
Confirmed 2 bars after the peak.

**Swing Low (Fractal Down)**:
```
low[i-2] > low[i-1] > low[i] < low[i+1] < low[i+2]
```
Confirmed 2 bars after the trough.

### Implementation Details

**Input Data**: M1 OHLC index columns (high_index, low_index)
**Lookback Window**: 100 bars minimum for fractal detection
**Swing Validity**: Minimum 2-bar confirmation delay
**Grid Update**: New grid established when both swing high and swing low are detected

### Data Schema

```sql
CREATE TABLE IF NOT EXISTS bqx.fibonacci_features_eurusd PARTITION OF bqx.fibonacci_features
FOR VALUES FROM ('2024-07-01') TO ('2024-08-01')
WITH (
    autovacuum_enabled = true,
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.05
);

-- Columns (all DOUBLE PRECISION except time fields)
ts_utc TIMESTAMP NOT NULL,  -- Primary key
fib_retracement_23_6 DOUBLE PRECISION,
fib_retracement_38_2 DOUBLE PRECISION,
fib_retracement_50_0 DOUBLE PRECISION,
fib_retracement_61_8 DOUBLE PRECISION,
fib_retracement_78_6 DOUBLE PRECISION,
fib_extension_127_2 DOUBLE PRECISION,
fib_extension_161_8 DOUBLE PRECISION,
fib_extension_261_8 DOUBLE PRECISION,
fib_nearest_level DOUBLE PRECISION,
fib_grid_position DOUBLE PRECISION,
fib_time_since_swing INTEGER,  -- Minutes
fib_grid_strength DOUBLE PRECISION,

UNIQUE (ts_utc)
```

## Rationale

### Why Williams Fractals (n=3)?

1. **Deterministic**: No subjective parameters (unlike percentage-based methods)
2. **Fast Computation**: Simple 5-bar pattern check, no iterative optimization
3. **Pair-Agnostic**: Works across all volatility regimes without calibration
4. **Market-Proven**: Widely used by traders, reflects actual support/resistance
5. **Balanced Sensitivity**: n=3 provides good signal quality vs responsiveness tradeoff

### Why Fibonacci Features?

1. **Widely Used**: Professional traders use Fibonacci levels for entry/exit decisions
2. **Self-Fulfilling**: Market participants clustering orders at these levels creates actual support/resistance
3. **Objective Measurement**: Our implementation removes subjectivity by automating swing detection
4. **Complementary**: Adds price-level context to existing momentum/volume features

## Implementation Phases

### Phase 1: Schema Creation (Stage 1.6.2)
- Create `fibonacci_features` parent table with 28 partitioned child tables
- Add indexes on ts_utc for each partition
- Verify schema compliance with Track 2 standards

### Phase 2: Worker Development (Stage 1.6.3)
- Develop `fibonacci_features_worker.py` with:
  - Williams Fractals detection algorithm
  - Fibonacci level calculation engine
  - Meta feature computation
  - ThreadPoolExecutor for parallel processing
- Unit tests for fractal detection accuracy

### Phase 3: Backfill Execution (Stage 1.6.4)
- Execute worker across 336 partitions (28 pairs × 12 months)
- Monitor progress with enhanced monitor script
- Verify data quality with sample queries

### Phase 4: Validation (Stage 1.6.5)
- Statistical validation of swing detection frequency
- Verify Fibonacci level calculations against manual samples
- Performance testing for query optimization

## Success Criteria

1. All 336 partitions populated with valid Fibonacci features
2. Swing detection frequency: 5-15 swings per 1000 bars (typical range)
3. Grid strength distribution: 0.3-2.5 (ATR-normalized range)
4. Query performance: <5ms for single-day queries with partition pruning
5. Zero NULL values in feature columns (default to 0.0 when no swing detected)

## Dependencies

**Hard Dependencies**:
- M1 tables with OHLC index columns (high_index, low_index, open_index)
- Stage 1.6.1 completion: OHLC Index Schema Enhancement

**Soft Dependencies**:
- ATR calculation for grid strength normalization (can use simplified volatility measure if unavailable)

## Integration with Track 2

This feature set extends Track 2's OHLC index enhancement by adding price-level analysis:

- **Track 2 Foundation**: OHLC index columns provide the raw data
- **Fibonacci Analysis**: Converts OHLC patterns into actionable support/resistance levels
- **Unified Storage**: Same schema pattern as other Track 2 features
- **Parallel Development**: Can be developed while Track 1 features complete

## Alternative Approaches Considered

1. **ATR-Based Zigzag**: More responsive but requires per-pair calibration (rejected for lack of standardization)
2. **Percentage-Based Zigzag**: Simple but fails in low-volatility periods (rejected for instability)
3. **N-Period High/Low**: Fast but misses intra-period swings (rejected for lower accuracy)
4. **Williams Fractals (n=5)**: Higher confirmation but lags market structure (rejected for delayed signals)

## References

- Williams, B. (1995). "Trading Chaos: Maximize Profits with Proven Technical Techniques"
- Fibonacci Trading: How to Master the Time and Price Advantage (Fischer, 2008)
- Technical Analysis of Financial Markets (Murphy, 1999)

## Next Steps

1. Update Airtable Stage 1.6.1 to include Fibonacci features task
2. Schedule implementation after Track 1 completion
3. Coordinate with OHLC backfill completion
4. Develop fibonacci_features_worker.py with Williams Fractals algorithm

---

**Document Version**: 1.0
**Last Updated**: 2025-11-11
**Author**: BQX ML Team (Claude Code)
**Status**: Specification Complete - Awaiting Implementation
