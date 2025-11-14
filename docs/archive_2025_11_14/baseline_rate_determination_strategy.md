# Baseline Rate Determination Strategy for Forex Rate Indexing

**Date:** 2025-11-10
**Context:** If implementing rate indexing, how should we determine the baseline rate?
**User Preference:** Peg baseline to a specific date

---

## TL;DR: Recommended Approach

**Use dataset start date with fallback logic**

```sql
-- Baseline: First timestamp on or after 2024-07-01 00:00 UTC
-- Fallback: If not available, use first available timestamp for that pair
```

**Rationale:**
- ✅ Consistent reference point across pairs
- ✅ Handles missing data gracefully
- ✅ Reproducible and explainable
- ✅ Aligned with dataset boundaries

---

## Baseline Date Options

### Option 1: Dataset Start Date (Recommended)

**Approach:** Use first date in your dataset (2024-07-01 00:00:00 UTC)

**Implementation:**
```sql
-- For each pair, get rate at dataset start
WITH baseline_rates AS (
  SELECT
    'eurusd' as pair,
    rate as baseline_rate
  FROM bqx.bqx_eurusd
  WHERE ts_utc >= '2024-07-01 00:00:00+00'
  ORDER BY ts_utc ASC
  LIMIT 1
)
SELECT
  t.ts_utc,
  t.rate,
  (t.rate / b.baseline_rate) * 100 as rate_index
FROM bqx.bqx_eurusd t
CROSS JOIN baseline_rates b
```

**Pros:**
- ✅ Natural boundary (start of dataset)
- ✅ All training data relative to same point
- ✅ Easy to explain: "Index tracks change since dataset start"
- ✅ Consistent across all pairs (same date)
- ✅ Works with monthly partitions (2024-07-01 is partition boundary)

**Cons:**
- ⚠️ Some pairs might not have data at exact 00:00:00 timestamp
- ⚠️ If extending dataset backward later, baseline would shift

**Example Results:**
```
EURUSD:
  2024-07-01 00:00 - rate: 1.0700, index: 100.00 (baseline)
  2024-07-01 01:00 - rate: 1.0705, index: 100.05
  2024-12-31 23:59 - rate: 1.0800, index: 100.93

USDJPY:
  2024-07-01 00:00 - rate: 140.00, index: 100.00 (baseline)
  2024-07-01 01:00 - rate: 140.14, index: 100.10
  2024-12-31 23:59 - rate: 141.00, index: 100.71
```

---

### Option 2: Specific Market Date (Alternative)

**Approach:** Use a significant market date (e.g., start of quarter, year, or major event)

**Examples:**
- 2024-01-01 00:00 UTC (start of year)
- 2024-07-01 00:00 UTC (start of Q3)
- 2024-06-01 00:00 UTC (start of month before dataset)

**Implementation:**
```sql
WITH baseline_rates AS (
  SELECT
    'eurusd' as pair,
    rate as baseline_rate
  FROM bqx.bqx_eurusd
  WHERE ts_utc = '2024-07-01 00:00:00+00'::timestamptz
  LIMIT 1
)
```

**Pros:**
- ✅ Meaningful reference point
- ✅ Consistent across pairs (everyone uses same timestamp)
- ✅ Easy to remember and communicate

**Cons:**
- ⚠️ Exact timestamp might not exist for all pairs (gaps in data)
- ⚠️ Requires exact match, no flexibility
- ⚠️ If chosen date is before dataset start, not in database

**Handling Missing Data:**
```sql
-- Fallback to nearest timestamp if exact match not found
WITH baseline_rates AS (
  SELECT
    'eurusd' as pair,
    rate as baseline_rate,
    ts_utc as baseline_ts
  FROM bqx.bqx_eurusd
  WHERE ts_utc >= '2024-07-01 00:00:00+00'
  ORDER BY ts_utc ASC
  LIMIT 1
)
```

---

### Option 3: First Available Timestamp Per Pair (Most Robust)

**Approach:** Each pair uses its own first available timestamp as baseline

**Implementation:**
```sql
WITH baseline_rates AS (
  SELECT
    'eurusd' as pair,
    rate as baseline_rate,
    ts_utc as baseline_ts
  FROM bqx.bqx_eurusd
  ORDER BY ts_utc ASC
  LIMIT 1
)
```

**Pros:**
- ✅ Always works (no missing data issues)
- ✅ Maximizes data utilization
- ✅ Robust to data gaps

**Cons:**
- ❌ Different baseline timestamps per pair
- ❌ Indexes not directly comparable across pairs
- ❌ Loses meaning: "100 = baseline" but baseline is different time for each pair

**Why This is Problematic:**
```
EURUSD baseline: 2024-07-01 00:00 (rate: 1.0700, index: 100.00)
USDJPY baseline: 2024-07-01 00:05 (rate: 140.14, index: 100.00)

Both have index 100, but:
- EURUSD measures change from 00:00
- USDJPY measures change from 00:05
- Can't compare: "EURUSD up 2%, USDJPY up 1%" meaningless if different start points
```

---

### Option 4: Rolling Baseline (Complex, Not Recommended)

**Approach:** Baseline updates over time (e.g., rate from 30 days ago)

**Implementation:**
```sql
SELECT
  t.ts_utc,
  t.rate,
  (t.rate / lag_rate.rate) * 100 as rate_index
FROM bqx.bqx_eurusd t
LEFT JOIN LATERAL (
  SELECT rate
  FROM bqx.bqx_eurusd
  WHERE ts_utc = t.ts_utc - interval '30 days'
  ORDER BY ts_utc DESC
  LIMIT 1
) lag_rate ON true
```

**Pros:**
- ✅ Captures recent trend
- ✅ Adapts to market conditions

**Cons:**
- ❌ Index meaning changes over time
- ❌ Not reproducible (depends on window size)
- ❌ Complex to explain
- ❌ Can't compare indexes from different dates
- ❌ Not suitable for ML training (non-stationary baseline)

---

## Recommended Implementation

### Strategy: Dataset Start with Fallback

**Best of both worlds:**
1. Target a specific date (2024-07-01 00:00:00 UTC)
2. If not available, use first timestamp after that date
3. Store baseline rate and timestamp for reproducibility

**SQL Implementation:**

```sql
-- Step 1: Calculate baseline rates (one-time, store results)
CREATE TABLE IF NOT EXISTS bqx_ml.baseline_rates (
  pair VARCHAR(10) PRIMARY KEY,
  baseline_rate DOUBLE PRECISION NOT NULL,
  baseline_ts TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Step 2: Populate baseline rates
INSERT INTO bqx_ml.baseline_rates (pair, baseline_rate, baseline_ts)
VALUES
  ('eurusd',
   (SELECT rate FROM bqx.bqx_eurusd
    WHERE ts_utc >= '2024-07-01 00:00:00+00'
    ORDER BY ts_utc ASC LIMIT 1),
   (SELECT ts_utc FROM bqx.bqx_eurusd
    WHERE ts_utc >= '2024-07-01 00:00:00+00'
    ORDER BY ts_utc ASC LIMIT 1)
  ),
  ('usdjpy',
   (SELECT rate FROM bqx.bqx_usdjpy
    WHERE ts_utc >= '2024-07-01 00:00:00+00'
    ORDER BY ts_utc ASC LIMIT 1),
   (SELECT ts_utc FROM bqx.bqx_usdjpy
    WHERE ts_utc >= '2024-07-01 00:00:00+00'
    ORDER BY ts_utc ASC LIMIT 1)
  );
  -- ... repeat for all 28 pairs

-- Step 3: Use in materialized view creation
CREATE MATERIALIZED VIEW bqx_ml.features_eurusd AS
SELECT
  t.ts_utc,
  t.rate as target_rate,
  (t.rate / b.baseline_rate) * 100 as target_rate_index,
  -- ... other features
FROM bqx.bqx_eurusd t
CROSS JOIN bqx_ml.baseline_rates b
WHERE b.pair = 'eurusd'
  AND t.ts_utc >= '2024-07-01';
```

**Python Implementation for MV Script:**

```python
def get_baseline_rate(pair, target_date='2024-07-01 00:00:00+00'):
    """
    Get baseline rate for a pair at or after target date

    Args:
        pair: forex pair (e.g., 'eurusd')
        target_date: target baseline date (default: dataset start)

    Returns:
        tuple: (baseline_rate, baseline_timestamp)
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(f"""
        SELECT rate, ts_utc
        FROM bqx.bqx_{pair}
        WHERE ts_utc >= %s::timestamptz
        ORDER BY ts_utc ASC
        LIMIT 1
    """, (target_date,))

    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        return result[0], result[1]
    else:
        raise ValueError(f"No data found for {pair} at or after {target_date}")


def create_baseline_rates_table():
    """Create and populate baseline_rates reference table"""
    conn = get_db_connection()
    cur = conn.cursor()

    # Create table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bqx_ml.baseline_rates (
            pair VARCHAR(10) PRIMARY KEY,
            baseline_rate DOUBLE PRECISION NOT NULL,
            baseline_ts TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Populate for all pairs
    target_date = '2024-07-01 00:00:00+00'

    for pair in ALL_PAIRS:
        try:
            baseline_rate, baseline_ts = get_baseline_rate(pair, target_date)

            cur.execute("""
                INSERT INTO bqx_ml.baseline_rates (pair, baseline_rate, baseline_ts)
                VALUES (%s, %s, %s)
                ON CONFLICT (pair) DO UPDATE
                SET baseline_rate = EXCLUDED.baseline_rate,
                    baseline_ts = EXCLUDED.baseline_ts,
                    created_at = NOW()
            """, (pair, baseline_rate, baseline_ts))

            print(f"✓ {pair.upper()}: baseline_rate={baseline_rate:.5f}, "
                  f"baseline_ts={baseline_ts}")

        except Exception as e:
            print(f"✗ {pair.upper()}: Error - {e}")

    conn.commit()
    cur.close()
    conn.close()

    print("\n✓ Baseline rates table created and populated")
```

---

## Verifying Baseline Selection

### Query Current Baselines

```sql
-- Check what baseline was used for each pair
SELECT
  pair,
  baseline_rate,
  baseline_ts,
  baseline_ts::date as baseline_date,
  created_at
FROM bqx_ml.baseline_rates
ORDER BY pair;
```

**Expected Output:**
```
pair     baseline_rate  baseline_ts              baseline_date  created_at
------   -------------  -----------------------  -------------  ---------------------
audcad   0.91234        2024-07-01 00:01:00+00   2024-07-01    2025-11-10 18:00:00+00
eurusd   1.07000        2024-07-01 00:00:00+00   2024-07-01    2025-11-10 18:00:00+00
usdjpy   140.00         2024-07-01 00:02:00+00   2024-07-01    2025-11-10 18:00:00+00
...
```

**Validation:**
- ✅ All timestamps on 2024-07-01 (or very close)
- ✅ Rates look reasonable (within expected range for each pair)
- ✅ No NULL values

---

## Handling Edge Cases

### Case 1: Missing Data at Target Date

**Problem:** Pair has no data at 2024-07-01 00:00:00

**Solution:** Use first available timestamp after target date

```sql
WHERE ts_utc >= '2024-07-01 00:00:00+00'  -- ">=" not "="
ORDER BY ts_utc ASC
LIMIT 1
```

**Result:** Might be 00:01, 00:05, or 01:00 - acceptable tolerance

---

### Case 2: Data Starts Before Target Date

**Problem:** Dataset extended backward to 2024-01-01, but baseline still 2024-07-01

**Decision:** Keep baseline at 2024-07-01 or recalculate?

**Option A: Keep existing baseline**
- ✅ Consistent with previous analyses
- ✅ No need to regenerate MVs
- ⚠️ Index doesn't cover full dataset history

**Option B: Recalculate baseline to new start**
- ✅ Index covers full dataset
- ✅ More complete history
- ❌ Breaks consistency with previous indexes
- ❌ Must regenerate all MVs

**Recommendation:** Keep existing baseline unless you need full history

---

### Case 3: Target Date in Future

**Problem:** Accidentally set target date to 2025-07-01 (future)

**Detection:**
```sql
SELECT pair, baseline_ts
FROM bqx_ml.baseline_rates
WHERE baseline_ts > NOW();
```

**Prevention:** Add validation in Python script
```python
if pd.to_datetime(target_date) > pd.Timestamp.now():
    raise ValueError(f"Target date {target_date} is in the future")
```

---

### Case 4: Timezone Confusion

**Problem:** Are we using UTC consistently?

**Best Practice:**
```python
# Always explicit UTC
target_date = '2024-07-01 00:00:00+00'  # ✅ Explicit UTC

# NOT this:
target_date = '2024-07-01'  # ❌ Ambiguous timezone
```

**Verification:**
```sql
-- Ensure all timestamps are UTC
SELECT pair, baseline_ts, EXTRACT(TIMEZONE FROM baseline_ts) as tz_offset
FROM bqx_ml.baseline_rates;

-- tz_offset should be 0 (UTC) for all rows
```

---

## Baseline Rate Characteristics

### What Makes a Good Baseline?

1. **Representative of "Normal" Market Conditions**
   - Not during extreme volatility
   - Not at market open/close anomalies
   - Not during major news events

2. **Data Availability**
   - All pairs have data at or near baseline date
   - Minimal gaps or missing timestamps

3. **Alignment with Analysis Goals**
   - Start of dataset: Good for analyzing full period
   - Start of quarter/year: Good for economic analysis
   - Pre-event date: Good for studying event impact

### Checking Baseline Quality

```sql
-- Check if baseline date had normal volatility
WITH baseline_volatility AS (
  SELECT
    ts_utc::date as date,
    pair,
    AVG(agg_bqx_volatility) as avg_volatility,
    MAX(agg_bqx_volatility) as max_volatility
  FROM bqx.bqx_eurusd
  WHERE ts_utc::date BETWEEN '2024-06-25' AND '2024-07-05'
  GROUP BY ts_utc::date, pair
)
SELECT * FROM baseline_volatility
ORDER BY date;

-- Baseline date (2024-07-01) should have "normal" volatility
-- Not an outlier spike or crash day
```

---

## Real-World Example: Your Dataset

### Current Dataset
- **Start:** 2024-07-01
- **End:** 2025-06-30
- **Duration:** 12 months (365 days)
- **Pairs:** 28 preferred pairs
- **Granularity:** 1-minute bars

### Recommended Baseline

**Date:** 2024-07-01 00:00:00 UTC

**Rationale:**
1. ✅ Aligns with dataset start
2. ✅ Aligns with monthly partition boundaries
3. ✅ Covers full 12-month period
4. ✅ Easy to explain: "Index shows % change from dataset start"

**Expected Baseline Rates (approximate):**
```
EURUSD:  ~1.0700
GBPUSD:  ~1.2700
USDJPY:  ~140.00
AUDUSD:  ~0.6700
USDCAD:  ~1.3700
...
```

### Verification Query

```sql
-- Check actual rates at baseline for your dataset
SELECT
  'eurusd' as pair, rate, ts_utc
FROM bqx.bqx_eurusd
WHERE ts_utc >= '2024-07-01 00:00:00+00'
ORDER BY ts_utc ASC
LIMIT 1;

-- Repeat for all pairs or use UNION ALL
```

---

## Index Interpretation

### With Baseline = 2024-07-01

**Index = 100:** Rate same as July 1, 2024
**Index = 105:** Rate 5% higher than July 1, 2024
**Index = 95:** Rate 5% lower than July 1, 2024

**Example Scenarios:**

**EURUSD (baseline rate = 1.0700):**
```
Current Rate  Index   Interpretation
-----------   -----   --------------
1.0700        100.0   No change from baseline
1.0807        101.0   EUR strengthened 1% vs USD
1.0593         99.0   EUR weakened 1% vs USD
1.1770        110.0   EUR strengthened 10% vs USD
```

**USDJPY (baseline rate = 140.00):**
```
Current Rate  Index   Interpretation
-----------   -----   --------------
140.00        100.0   No change from baseline
141.40        101.0   USD strengthened 1% vs JPY
138.60         99.0   USD weakened 1% vs JPY
154.00        110.0   USD strengthened 10% vs JPY
```

---

## Storage and Documentation

### Store Baseline Metadata

**Table: bqx_ml.baseline_rates**
```sql
CREATE TABLE bqx_ml.baseline_rates (
  pair VARCHAR(10) PRIMARY KEY,
  baseline_rate DOUBLE PRECISION NOT NULL,
  baseline_ts TIMESTAMPTZ NOT NULL,
  target_date VARCHAR(30) DEFAULT '2024-07-01 00:00:00+00',
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add notes for documentation
UPDATE bqx_ml.baseline_rates
SET notes = 'Baseline set to dataset start date (2024-07-01).
             All rate indexes measure % change from this date.
             Used for unified multi-pair model training.'
WHERE pair = 'eurusd';
```

### Document in Code

```python
# At top of create_filtered_feature_mvs.py

# BASELINE CONFIGURATION
# =====================
# Baseline date for rate indexing: 2024-07-01 00:00:00 UTC
# Rationale: Aligns with dataset start, partition boundaries
# Index interpretation: 100 = baseline rate, 105 = +5%, 95 = -5%
#
# To change baseline:
# 1. Update BASELINE_DATE constant below
# 2. Run create_baseline_rates_table()
# 3. Regenerate all materialized views

BASELINE_DATE = '2024-07-01 00:00:00+00'
```

---

## Recommendation Summary

### For Your Use Case

**Baseline Strategy:** Dataset start date with fallback

**Implementation:**
1. Target date: 2024-07-01 00:00:00 UTC
2. Fallback: First timestamp >= target date
3. Store in bqx_ml.baseline_rates table
4. Reference in MV creation via JOIN

**Code Changes Needed:**
1. Add `create_baseline_rates_table()` function
2. Add `get_baseline_rate()` helper
3. Modify MV SQL to include rate_index calculation
4. Add baseline_rates table JOIN

**Benefits:**
- ✅ Consistent across all pairs
- ✅ Handles missing data gracefully
- ✅ Reproducible and documented
- ✅ Aligned with natural dataset boundaries
- ✅ Easy to explain and interpret

**Next Steps:**
1. Confirm 2024-07-01 as baseline date (or choose alternative)
2. Implement baseline_rates table creation
3. Add rate_index to MV generation
4. Document baseline choice in project docs

---

**Analysis Date:** 2025-11-10
**Recommendation:** Use dataset start (2024-07-01) as baseline with fallback logic
**Status:** Ready for implementation if rate indexing is desired
