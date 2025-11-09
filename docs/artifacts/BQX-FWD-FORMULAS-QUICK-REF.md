# BQX Forward Return Formulas - Quick Reference

**Date**: 2025-11-08

---

## Core Formulas (6 Windows: 60, 90, 150, 240, 390, 630 minutes)

### 1. Cumulative Forward Return ⭐ **PRIMARY METRIC**

```
w{W}_fwd_return = Σ(i=1 to W)[rate(t) - rate(t+i)] / rate(t)
```

**What it means**: Sum of all price differences over the window, normalized by current rate

**Example** (w60):
- Current rate: 1.08837
- Sum of 60 future diffs: 0.003569
- Result: 0.003569 / 1.08837 = **0.00328** (0.328% cumulative movement)

---

### 2. Endpoint Return

```
w{W}_fwd_endpoint = [rate(t) - rate(t+W)] / rate(t)
```

**What it means**: Simple return from current to end of window (ignores middle)

---

### 3. Statistical Measures

```
w{W}_fwd_max    = max(rate(t+1), ..., rate(t+W))
w{W}_fwd_min    = min(rate(t+1), ..., rate(t+W))
w{W}_fwd_avg    = mean(rate(t+1), ..., rate(t+W))
w{W}_fwd_stdev  = stdev(rate(t+1), ..., rate(t+W))
```

**What it means**: Basic statistics of future rates within the window

---

## Aggregate Metrics (630-minute window)

```
agg_fwd_return     = Σ(i=1 to 630)[rate(t) - rate(t+i)] / rate(t)
agg_fwd_max        = max(future 630 rates)
agg_fwd_min        = min(future 630 rates)
agg_fwd_avg        = mean(future 630 rates)
agg_fwd_stdev      = stdev(future 630 rates)
agg_fwd_range      = [max - min] / rate(t)
agg_fwd_volatility = stdev / rate(t)
```

---

## Sign Convention ⚠️

**IMPORTANT**: Positive return means price **DECLINED** (profitable for shorts)

```
✅ fwd_return > 0  →  Price went DOWN  →  Good for SHORT
✅ fwd_return < 0  →  Price went UP    →  Good for LONG
```

This is **opposite** to typical financial conventions!

---

## Window Sizes

| Window | Minutes | Hours | Use Case |
|--------|---------|-------|----------|
| w60 | 60 | 1h | Short-term scalping |
| w90 | 90 | 1.5h | Intraday swings |
| w150 | 150 | 2.5h | Session transitions |
| w240 | 240 | 4h | Session trends |
| w390 | 390 | 6.5h | Daily patterns |
| w630 | 630 | 10.5h | Long-term trends |

---

## Example Calculation

**Given** (w60 window at t=0):
```
t+0:  1.08837 (current)
t+1:  1.08831
t+2:  1.08828
...
t+60: 1.08808
```

**Calculate**:
```
Step 1: Differences from current
  0.00006, 0.00009, ..., 0.00029

Step 2: Sum all differences
  Σ = 0.003569

Step 3: Normalize by current rate
  fwd_return = 0.003569 / 1.08837 = 0.00328
```

**Result**: `w60_fwd_return = 0.00328` (0.328% cumulative movement)

---

## ML Use Cases

**As Target Variables**:
- **Regression**: Predict `w60_fwd_return` for price direction
- **Classification**: Predict `sign(w60_fwd_return)` for buy/sell signals
- **Risk Models**: Predict `agg_fwd_volatility` for position sizing

**Combined with REG Features**:
```python
X = REG features  # Past patterns (what happened)
Y = FWD returns   # Future outcomes (what will happen)

model.fit(X, Y)   # Learn past → future mapping
```

---

## NULL Values

Forward metrics are **NULL** when insufficient future data:
- Last 60 minutes: w60 is NULL
- Last 630 minutes: w630 is NULL
- Edge effect handled explicitly

---

## Quick Verification Query

```sql
-- Verify formulas work correctly
SELECT
    ts_utc,
    rate,
    w60_fwd_return,    -- Cumulative return (sum of diffs)
    w60_fwd_endpoint,  -- Simple return (start to end)
    w60_fwd_max,       -- Highest future rate
    w60_fwd_min,       -- Lowest future rate
    w60_fwd_avg,       -- Average future rate
    w60_fwd_stdev      -- Volatility of future rates
FROM bqx.fwd_eurusd
WHERE ts_utc = '2024-11-01 00:00:00+00';
```

---

## Key Insights

1. **Cumulative vs Endpoint**:
   - Cumulative captures the full path (~12x larger)
   - Endpoint only captures start/end change

2. **Normalized Metrics**:
   - All returns divided by current rate
   - Scale-independent (works for all pairs)

3. **Forward-Looking**:
   - Uses **actual future M1 data** (not predictions)
   - Ground truth for ML model training

---

**Full Documentation**: [BQX-FORWARD-RETURN-FORMULAS.md](BQX-FORWARD-RETURN-FORMULAS.md)
**Source Code**: [forward_worker.py](https://github.com/Schmidtlappin/bqx-db/blob/main/scripts/analytics/forward_worker.py)
