# Forex Rate Index Analysis: Should We Index-Normalize Rates?

**Date:** 2025-11-10
**Question:** Should we calculate forex pair rate indexes (base-100 normalization) to further normalize data for ML?

---

## TL;DR: NOT NECESSARY (But Has Specific Use Cases)

**Recommendation:** Index normalization is **redundant** for our current approach but **valuable** for multi-pair unified models.

**Current approach (per-pair models):** ✅ Use existing percentage features
**Alternative approach (unified cross-pair model):** ✅ Consider rate indexing

---

## What is a Forex Rate Index?

A **rate index** converts absolute forex rates to percentage changes from a baseline date.

### Example: Base-100 Index

**Setup:**
- Baseline date: 2024-07-01 00:00 UTC
- All pairs start at index = 100
- Index tracks cumulative % change from baseline

**EURUSD:**
```
Date           Rate      Index    Calculation
2024-07-01    1.0700    100.00   (baseline)
2024-07-15    1.0750    100.47   (1.0750/1.0700) × 100 = 100.47
2024-08-01    1.0650     99.53   (1.0650/1.0700) × 100 = 99.53
2024-12-31    1.0800    100.93   (1.0800/1.0700) × 100 = 100.93
```

**USDJPY:**
```
Date           Rate      Index    Calculation
2024-07-01   140.00    100.00   (baseline)
2024-07-15   140.50    100.36   (140.50/140.00) × 100 = 100.36
2024-08-01   139.50     99.64   (139.50/140.00) × 100 = 99.64
2024-12-31   141.00    100.71   (141.00/140.00) × 100 = 100.71
```

**Result:** Both pairs now on same scale (around 100), tracking % changes

---

## Current Normalization Status

### What We Already Have

#### 1. Absolute Rate (NOT normalized)
```python
rate = 1.0700  # EURUSD
rate = 140.00  # USDJPY
```
- Different scales (1.07 vs 140)
- Provides absolute price context
- Useful for support/resistance levels

#### 2. Percentage Return Features (ALREADY normalized)
```python
bqx_return = Σ(past_rates - rate_t) / rate_t
# EURUSD: 0.0150 (1.50%)
# USDJPY: 0.0150 (1.50%)
# ✅ Comparable across pairs
```

#### 3. Percentage Endpoint Features (ALREADY normalized)
```python
bqx_endpoint = (rate_start - rate_t) / rate_t
# EURUSD: 0.0047 (0.47%)
# USDJPY: 0.0036 (0.36%)
# ✅ Comparable across pairs
```

#### 4. Percentage-Normalized Features (NEW - added in implementation)
```python
bqx_max_pct = (bqx_max - rate_t) / rate_t
bqx_min_pct = (bqx_min - rate_t) / rate_t
bqx_avg_pct = (bqx_avg - rate_t) / rate_t
bqx_stdev_pct = bqx_stdev / rate_t
# ✅ All comparable across pairs
```

---

## Rate Index vs Current Approach

### Scenario 1: Per-Pair Models (Current Approach)

**Model:** Train separate model for each pair (28 models total)

**Training data for EURUSD:**
```
Features: [rate, w15_bqx_return, w15_bqx_max_pct, ...]
Target: future_return (e.g., 15-min ahead return)

Row 1: [1.0700, 0.0012, 0.0008, ...]
Row 2: [1.0705, 0.0015, 0.0010, ...]
Row 3: [1.0710, 0.0009, 0.0007, ...]
```

**Does rate scale matter?**
- ❌ No - Model only sees EURUSD rates (all around 1.05-1.15)
- ✅ Percentage features already normalized
- ✅ Model learns patterns specific to EURUSD

**Conclusion:** Rate indexing is **UNNECESSARY** for per-pair models

---

### Scenario 2: Unified Multi-Pair Model

**Model:** Single model trained on all 28 pairs simultaneously

**Training data (without rate index):**
```
Features: [pair_id, rate, w15_bqx_return, w15_bqx_max_pct, ...]
Target: future_return

Row 1: [EURUSD, 1.0700, 0.0012, 0.0008, ...]
Row 2: [EURUSD, 1.0705, 0.0015, 0.0010, ...]
Row 3: [USDJPY, 140.00, 0.0012, 0.0008, ...]  # Problem: rate scale 127× different!
Row 4: [USDJPY, 140.50, 0.0015, 0.0010, ...]
```

**Problem:**
- `rate` feature has different scales per pair
- USDJPY rates 127× larger than EURUSD
- Model must learn "ignore rate scale, it's pair-dependent"
- Gradient descent struggles with multi-scale inputs

**Training data (with rate index):**
```
Features: [pair_id, rate_index, w15_bqx_return, w15_bqx_max_pct, ...]
Target: future_return

Row 1: [EURUSD, 100.00, 0.0012, 0.0008, ...]
Row 2: [EURUSD, 100.47, 0.0015, 0.0010, ...]
Row 3: [USDJPY, 100.00, 0.0012, 0.0008, ...]  # ✅ Same scale as EURUSD!
Row 4: [USDJPY, 100.36, 0.0015, 0.0010, ...]
```

**Benefit:**
- All rate_index values on comparable scale (~99-101)
- Model learns: "rate_index above 100 = uptrend, below 100 = downtrend"
- Easier for model to generalize across pairs

**Conclusion:** Rate indexing is **VALUABLE** for unified multi-pair models

---

## Implementation Options

### Option A: No Rate Index (Current - Recommended for Per-Pair Models)

**Features per pair:**
- `rate` - absolute current rate
- `w{W}_bqx_return` - percentage returns
- `w{W}_bqx_max_pct` - percentage-normalized max
- ... (all other normalized features)

**Model strategy:** Train 28 separate models

**Pros:**
- ✅ Simpler implementation
- ✅ Retains absolute rate information
- ✅ Each model specialized to one pair
- ✅ No arbitrary baseline date needed

**Cons:**
- ❌ Must train/deploy 28 models
- ❌ Can't share knowledge across pairs
- ❌ Harder to ensemble

---

### Option B: Add Rate Index (Recommended for Unified Models)

**New feature:** `rate_index` = (current_rate / baseline_rate) × 100

**Implementation:**
```sql
-- Add to MV creation
-- Pick first rate in dataset as baseline for each pair
WITH baselines AS (
  SELECT
    '{pair}' as pair_name,
    rate as baseline_rate
  FROM bqx.bqx_{pair}
  WHERE ts_utc >= '2024-07-01'
  ORDER BY ts_utc
  LIMIT 1
)
SELECT
  target.ts_utc,
  target.rate,
  (target.rate / baselines.baseline_rate) * 100 as target_rate_index,
  ...
FROM bqx.bqx_{pair} target
CROSS JOIN baselines
```

**Model strategy:** Train 1 unified model with pair embeddings

**Pros:**
- ✅ Single model handles all pairs
- ✅ Shares knowledge across pairs
- ✅ Rate_index on comparable scale
- ✅ Easier to deploy/maintain

**Cons:**
- ❌ More complex model architecture
- ❌ Arbitrary baseline date
- ❌ May not capture pair-specific patterns as well

---

### Option C: Hybrid Approach

**Features:**
- Keep `rate` for absolute context
- Add `rate_index` for normalized trends
- Keep all percentage features

**Model strategy:** Try both per-pair and unified models

**Pros:**
- ✅ Maximum flexibility
- ✅ Can experiment with different architectures
- ✅ No information loss

**Cons:**
- ❌ Slightly higher dimensionality
- ❌ Some redundancy between features

---

## When Rate Indexing Makes Sense

### ✅ USE RATE INDEX when:

1. **Training unified multi-pair model**
   - Single model for all 28 pairs
   - Pair ID as feature or embedding
   - Want to share patterns across pairs

2. **Ensemble predictions across pairs**
   - Predict "best pair to trade right now"
   - Compare relative strength across pairs
   - Need comparable "momentum" metric

3. **Transfer learning**
   - Pre-train on major pairs (EURUSD, GBPUSD)
   - Fine-tune on exotic pairs
   - Rate index helps model generalize

4. **Time-series analysis across pairs**
   - Compare trends: "EURUSD up 2%, USDJPY down 1%"
   - Portfolio allocation based on relative performance
   - Cross-pair correlation analysis

### ❌ DON'T USE RATE INDEX when:

1. **Training per-pair models** (current approach)
   - Each model only sees one pair's rates
   - Scale doesn't matter within a single pair
   - Percentage features already sufficient

2. **Absolute price levels matter**
   - Support/resistance at specific rates
   - Round number psychology (USDJPY at 150.00)
   - Historical price memory

3. **Short training period**
   - Baseline becomes arbitrary
   - Index doesn't add information

---

## Comparison to Existing Features

### Rate Index vs bqx_return

**bqx_return:**
```
w15_bqx_return = Σ(past_15_rates - rate_t) / rate_t
```
- Percentage change over last 15 minutes
- Resets every timestamp (relative to current rate)
- Short-term momentum

**rate_index:**
```
rate_index = (rate_t / rate_baseline) × 100
```
- Cumulative percentage change from baseline
- Tracks long-term trend from start of dataset
- Absolute position relative to starting point

**Difference:**
- bqx_return: "How much did price move in last 15 min?" (short-term)
- rate_index: "How much has price moved since July 1?" (long-term)

**Redundancy:** Low - they capture different time horizons

---

### Rate Index vs Absolute Rate

**Absolute rate:**
- EURUSD: 1.0700, 1.0705, 1.0710
- USDJPY: 140.00, 140.50, 141.00
- Different scales, not directly comparable

**Rate index:**
- EURUSD: 100.00, 100.47, 100.93
- USDJPY: 100.00, 100.36, 100.71
- Same scale, directly comparable

**Use case for absolute rate:**
- Support/resistance: "EURUSD struggling at 1.1000"
- Round numbers: "USDJPY bounced off 150.00"
- Historical context: "Highest since 2022"

**Use case for rate index:**
- Relative performance: "EURUSD up 0.93%, USDJPY up 0.71%"
- Cross-pair comparison: "EUR stronger than JPY vs USD"
- Unified model input: All pairs on same scale

---

## Calculation Details

### Baseline Date Selection

**Option 1: Fixed date (Simple)**
```sql
-- Use 2024-07-01 00:00 UTC as baseline for all pairs
WHERE ts_utc = '2024-07-01 00:00:00+00'
```

**Pros:** Simple, reproducible
**Cons:** Some pairs might not have data at exact time

**Option 2: First available timestamp (Robust)**
```sql
-- Use first timestamp in dataset for each pair
SELECT rate FROM bqx.bqx_{pair} ORDER BY ts_utc LIMIT 1
```

**Pros:** Always works, no missing data
**Cons:** Different baseline times for different pairs

**Option 3: Rolling baseline (Complex)**
```sql
-- Use rate from N days ago as baseline
rate_index = (rate_t / rate_{t-30days}) × 100
```

**Pros:** Captures recent trend, adapts over time
**Cons:** Complex, index changes meaning over time

**Recommendation:** Option 2 (first available timestamp) for simplicity

---

### Formula

**Index calculation:**
```python
def calculate_rate_index(rate_current, rate_baseline):
    """
    Calculate base-100 index

    Args:
        rate_current: current forex rate
        rate_baseline: baseline rate at starting point

    Returns:
        index value (100 = no change from baseline)
    """
    return (rate_current / rate_baseline) * 100
```

**Examples:**
```python
# EURUSD baseline = 1.0700
calculate_rate_index(1.0700, 1.0700)  # 100.00 (no change)
calculate_rate_index(1.0750, 1.0700)  # 100.47 (up 0.47%)
calculate_rate_index(1.0650, 1.0700)  #  99.53 (down 0.47%)
calculate_rate_index(1.1770, 1.0700)  # 110.00 (up 10%)

# USDJPY baseline = 140.00
calculate_rate_index(140.00, 140.00)  # 100.00 (no change)
calculate_rate_index(140.50, 140.00)  # 100.36 (up 0.36%)
calculate_rate_index(139.50, 140.00)  #  99.64 (down 0.36%)
calculate_rate_index(154.00, 140.00)  # 110.00 (up 10%)
```

**Interpretation:**
- Index = 100: Same as baseline
- Index > 100: Currency strengthened vs baseline
- Index < 100: Currency weakened vs baseline
- Index = 105: 5% stronger than baseline
- Index = 95: 5% weaker than baseline

---

## ML Model Implications

### With Rate Index (Unified Model)

**Architecture:**
```python
# Single model for all pairs
model = Sequential([
    Input(shape=(features,)),  # includes rate_index
    Dense(128, activation='relu'),
    Dense(64, activation='relu'),
    Dense(1)  # predict future return
])

# Training data shape: (N_samples_all_pairs, features)
X_train.shape  # (10.3M rows × 28 pairs, 794 features)
```

**Benefits:**
- ✅ Model sees patterns across all pairs
- ✅ Can learn "when rate_index > 102, momentum strong"
- ✅ Generalizes better to unseen market conditions
- ✅ More training data (all pairs combined)

**Challenges:**
- ❌ Must learn pair-specific patterns via embeddings
- ❌ More complex architecture
- ❌ Slower training (larger dataset)

---

### Without Rate Index (Per-Pair Models)

**Architecture:**
```python
# Separate model for each pair (×28)
model_eurusd = Sequential([
    Input(shape=(features,)),  # includes absolute rate
    Dense(64, activation='relu'),
    Dense(32, activation='relu'),
    Dense(1)
])

# Training data shape: (N_samples_one_pair, features)
X_train_eurusd.shape  # (~370k rows, 794 features)
```

**Benefits:**
- ✅ Model specialized to EURUSD patterns
- ✅ Simpler architecture
- ✅ Faster training per model
- ✅ Can use absolute rate for support/resistance

**Challenges:**
- ❌ Must train 28 separate models
- ❌ Less training data per model
- ❌ Can't share knowledge across pairs
- ❌ Harder to ensemble

---

## Storage Impact

### With Rate Index

**Additional fields per MV:**
- 1 new field: `target_rate_index`
- 12 new fields: `{pair}_rate_index` for each feature pair

**Total:** +13 fields per MV = +364 fields across 28 MVs

**Storage:** ~1-2 GB additional across all MVs

**Is it worth it?** Depends on whether you'll use unified models

---

## Recommendation

### ✅ CURRENT APPROACH IS OPTIMAL for Per-Pair Models

**Don't add rate index if:**
- Training separate model per pair ✅ (current plan)
- Want simpler implementation ✅
- Absolute rate provides value ✅
- Percentage features sufficient ✅ (they are!)

**Why it's unnecessary:**
1. All percentage features (bqx_return, bqx_endpoint, _pct) already normalized
2. Absolute rate only compared within single pair
3. Scale difference doesn't matter for per-pair models
4. Rate provides useful context (support/resistance, round numbers)

---

### ✅ ADD RATE INDEX if Planning Unified Model

**Consider rate index if:**
- Want to train single model across all pairs
- Planning transfer learning experiments
- Need to compare relative performance across pairs
- Building portfolio allocation system

**Implementation:**
- Add `rate_index` calculation to MV script
- Store alongside `rate` (keep both)
- Use rate_index for model input
- Keep rate for interpretability

---

## Conclusion

### Question: "Should we calculate forex pair rate indexes to further normalize data for ML?"

**Answer: NO for current per-pair approach, YES for future unified model**

**Current Status:**
- ✅ We have comprehensive percentage normalization (_pct features)
- ✅ All features comparable across pairs
- ✅ Rate index would be redundant for per-pair models

**If you switch to unified model in the future:**
- ✅ Add rate_index calculation
- ✅ Use as input feature
- ✅ Enables knowledge sharing across pairs

**Recommendation:**
**Proceed with current implementation (no rate index)**. The percentage-normalized features we added are sufficient for ML training. Rate indexing only adds value if you later decide to train a single unified model across all pairs.

---

**Analysis Date:** 2025-11-10
**Status:** Rate indexing not necessary for current architecture
**Future consideration:** Revisit if switching to unified multi-pair models
