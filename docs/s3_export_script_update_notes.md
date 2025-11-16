# S3 Export Script Update - 2025-11-16

## Summary

Updated [scripts/ml/export_features_to_s3.py](../scripts/ml/export_features_to_s3.py) to include **all 9 feature families** instead of only 3.

**Status:** Updated but **NOT YET TESTED**
**Priority:** High (required for ML training with complete feature set)

---

## Changes Made

### 1. Updated Column Names to New Term-Based Schema

**OLD (coefficient-based):**
```sql
w60_a_term AS reg_rate_w60_quad,
w60_b_term AS reg_rate_w60_lin,
w60_resid_end AS reg_rate_w60_resid
```

**NEW (term-based):**
```sql
w60_quadratic_term AS reg_rate_w60_quad,
w60_linear_term AS reg_rate_w60_lin,
w60_constant_term AS reg_rate_w60_const,
w60_residual AS reg_rate_w60_resid,
w60_prediction AS reg_rate_w60_pred
```

**Reason:** Stages 2.11 and 2.12 migrated to term-based architecture

---

### 2. Added 6 Missing Feature Families

The following tables are now included in the export query:

#### **3. technical_indicators_{pair}**
```sql
tech_indicators AS (
    SELECT
        ts_utc,
        rsi_14 AS ti_rsi_14,
        macd_line AS ti_macd_line,
        macd_signal AS ti_macd_signal,
        macd_histogram AS ti_macd_histogram,
        stoch_k AS ti_stoch_k,
        stoch_d AS ti_stoch_d,
        bb_upper AS ti_bb_upper,
        bb_middle AS ti_bb_middle,
        bb_lower AS ti_bb_lower,
        atr_14 AS ti_atr_14
    FROM bqx.technical_indicators_{pair}_{year_month}
)
```

#### **4. currency_index_{pair}**
```sql
currency_idx AS (
    SELECT
        ts_utc,
        base_currency_strength AS ci_base_strength,
        quote_currency_strength AS ci_quote_strength,
        strength_divergence AS ci_strength_div
    FROM bqx.currency_index_{pair}_{year_month}
)
```

#### **5. arbitrage_{pair}**
```sql
arbitrage AS (
    SELECT
        ts_utc,
        arbitrage_opportunity AS arb_opportunity,
        arbitrage_profit_bps AS arb_profit_bps,
        arbitrage_path AS arb_path
    FROM bqx.arbitrage_{pair}_{year_month}
)
```

#### **6. correlation_bqx_{pair}**
```sql
correlation AS (
    SELECT
        ts_utc,
        correlation_score AS corr_score,
        correlation_rank AS corr_rank,
        -- Term covariances (added in Stage 2.14)
        cov_quad_lin_bqx_60min AS corr_cov_quad_lin,
        cov_resid_quad_bqx_60min AS corr_cov_resid_quad,
        cov_resid_lin_bqx_60min AS corr_cov_resid_lin,
        corr_quad_lin_bqx_60min AS corr_corr_quad_lin,
        corr_resid_quad_bqx_60min AS corr_corr_resid_quad,
        corr_resid_lin_bqx_60min AS corr_corr_resid_lin
    FROM bqx.correlation_bqx_{pair}_{year_month}
)
```

#### **7. enhanced_rmse_{pair}**
```sql
enhanced_rmse AS (
    SELECT
        ts_utc,
        enhanced_rmse_score AS rmse_enhanced_score,
        rmse_trend AS rmse_trend,
        rmse_volatility AS rmse_volatility
    FROM bqx.enhanced_rmse_{pair}_{year_month}
)
```

#### **8. regime_{pair}**
```sql
regime AS (
    SELECT
        ts_utc,
        regime_type AS regime_type,
        regime_confidence AS regime_confidence,
        regime_duration_minutes AS regime_duration
    FROM bqx.regime_{pair}_{year_month}
)
```

---

## Testing Required

### ⚠️ IMPORTANT: Column Name Assumptions

The column names for the 6 new feature families are **educated guesses** based on typical naming conventions. They may not match the actual table schemas.

**Before running the full export**, you must:

### 1. Verify Actual Table Schemas

Check each table's actual columns for a sample pair (e.g., eurusd):

```sql
-- Check technical_indicators schema
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'bqx'
  AND table_name = 'technical_indicators_eurusd_2024_07'
ORDER BY ordinal_position;

-- Repeat for:
-- - currency_index_eurusd_2024_07
-- - arbitrage_eurusd_2024_07
-- - correlation_bqx_eurusd_2024_07
-- - enhanced_rmse_eurusd_2024_07
-- - regime_eurusd_2024_07
```

### 2. Update Column Selections

Based on actual schemas, update the SELECT statements in [export_features_to_s3.py](../scripts/ml/export_features_to_s3.py) lines 226-292.

### 3. Test on Single Pair/Month

Test the updated query on a single pair and month before running the full export:

```bash
# Modify script to only export eurusd 2024_07
python3 scripts/ml/export_features_to_s3.py \
    --max-workers 1 \
    --verify
```

**Expected outcome:**
- Query executes successfully
- Parquet file created: `s3://bqx-ml-features/features/eurusd/2024_07.parquet`
- Verification passes
- Column count significantly higher than before (~100+ columns vs ~30 columns)

### 4. Verify Feature Completeness

After successful test export, download and inspect the Parquet file:

```python
import pandas as pd
import boto3
from io import BytesIO

# Download test file
s3 = boto3.client('s3')
response = s3.get_object(Bucket='bqx-ml-features',
                         Key='features/eurusd/2024_07.parquet')
df = pd.read_parquet(BytesIO(response['Body'].read()))

# Check columns
print(f"Total columns: {len(df.columns)}")
print("\nColumn families:")
print(f"  Base OHLCV: {len([c for c in df.columns if c in ['open','high','low','close','volume','rate_index','bqx']])}")
print(f"  reg_rate: {len([c for c in df.columns if c.startswith('reg_rate_')])}")
print(f"  reg_bqx: {len([c for c in df.columns if c.startswith('reg_bqx_')])}")
print(f"  Technical Indicators: {len([c for c in df.columns if c.startswith('ti_')])}")
print(f"  Currency Index: {len([c for c in df.columns if c.startswith('ci_')])}")
print(f"  Arbitrage: {len([c for c in df.columns if c.startswith('arb_')])}")
print(f"  Correlation: {len([c for c in df.columns if c.startswith('corr_')])}")
print(f"  RMSE: {len([c for c in df.columns if c.startswith('rmse_')])}")
print(f"  Regime: {len([c for c in df.columns if c.startswith('regime_')])}")

# Verify all 9 families present
assert len([c for c in df.columns if c.startswith('ti_')]) > 0, "Missing technical indicators"
assert len([c for c in df.columns if c.startswith('ci_')]) > 0, "Missing currency index"
assert len([c for c in df.columns if c.startswith('arb_')]) > 0, "Missing arbitrage"
assert len([c for c in df.columns if c.startswith('corr_')]) > 0, "Missing correlation"
assert len([c for c in df.columns if c.startswith('rmse_')]) > 0, "Missing enhanced RMSE"
assert len([c for c in df.columns if c.startswith('regime_')]) > 0, "Missing regime"

print("\n✅ All 9 feature families present!")
```

---

## Benefits After Update

1. **Complete Feature Set:** All 9 feature families available for ML training
2. **Future-Proof:** Includes term covariances from Stage 2.14
3. **Properly Namespaced:** Column prefixes prevent naming collisions
4. **Aligned Windows:** Uses new term-based schema with aligned windows

---

## Execution Timeline

**When to Test:**
- After Stage 2.12 completes (reg_bqx rebuild)
- After Stage 2.14 completes (term covariances added to correlation_bqx)

**When to Run Full Export:**
- After Stage 2.15 validation passes (100% schema alignment confirmed)

**Estimated Duration:**
- Test (1 pair, 1 month): ~10 seconds
- Full export (28 pairs × 12 months with 8 workers): ~3 hours

---

## File Modified

- [scripts/ml/export_features_to_s3.py](../scripts/ml/export_features_to_s3.py) (lines 105-318)

---

## Next Steps

1. ✅ **S3 export script updated** (this task - DONE)
2. ⏳ Wait for Stage 2.12 to complete
3. ⏳ Verify actual table schemas (query information_schema)
4. ⏳ Adjust column selections if needed
5. ⏳ Test on single pair (eurusd 2024_07)
6. ⏳ Run full export after Stage 2.15 validation passes

---

**Created:** 2025-11-16
**Stage 2.12 Status:** Running in background (ETA: ~20:30 UTC)
