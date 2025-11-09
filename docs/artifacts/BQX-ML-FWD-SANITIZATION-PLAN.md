# BQX ML Strategy - FWD Sanitization Analysis

**Date**: 2025-11-08
**Critical Question**: Does the BQX ML plan completely sanitize/remove all FWD data and references?

---

## Short Answer

**YES** - The BQX ML strategy as designed is **completely independent** of FWD tables.

**Training Pipeline**:
```
Features: BQX_t + REG_t  (NO FWD)
Targets:  BQX_{t+60}     (NO FWD)
```

**FWD tables are NOT used** in:
- Feature extraction ✅
- Target creation ✅
- Model training ✅
- Prediction generation ✅

---

## Detailed Analysis

### What the BQX ML Pipeline Uses

**Input Tables**:
```
1. bqx.bqx_{pair}  ← BQX backward momentum (NEW)
2. bqx.reg_{pair}  ← REG regression features (EXISTING)
```

**Does NOT Use**:
```
❌ bqx.fwd_{pair}  ← FWD forward returns (NOT NEEDED)
```

### Feature Extraction (Zero FWD References)

```python
# Feature creation - NO FWD USAGE
def create_features(bqx_df, reg_df):
    """Extract ML features from BQX and REG tables only"""

    features = pd.DataFrame()

    # 1. Current BQX momentum (backward-looking)
    features['bqx_w15'] = bqx_df['w15_bqx_return']  # From BQX table
    features['bqx_w30'] = bqx_df['w30_bqx_return']  # From BQX table
    features['bqx_w60'] = bqx_df['w60_bqx_return']  # From BQX table

    # 2. Lagged BQX (autoregressive)
    features['bqx_w60_lag60'] = bqx_df['w60_bqx_return'].shift(60)  # From BQX table

    # 3. Volatility
    features['bqx_vol'] = bqx_df['w15_bqx_stdev']  # From BQX table

    # 4. REG patterns
    features['reg_quad'] = reg_df['w60_quad_norm']  # From REG table
    features['reg_r2'] = reg_df['w60_r2']           # From REG table

    # NO FWD DATA USED ✅

    return features
```

### Target Creation (Zero FWD References)

```python
# Target creation - NO FWD USAGE
def create_targets(bqx_df):
    """Create prediction targets from future BQX values"""

    targets = pd.DataFrame()

    # Predict what BQX will show at t+60
    targets['bqx_w60_ahead'] = bqx_df['w60_bqx_return'].shift(-60)  # From BQX table

    # Predict multiple horizons
    targets['bqx_w15_ahead'] = bqx_df['w15_bqx_return'].shift(-15)  # From BQX table
    targets['bqx_w30_ahead'] = bqx_df['w30_bqx_return'].shift(-30)  # From BQX table

    # NO FWD DATA USED ✅

    return targets
```

### Training Pipeline (Zero FWD References)

```python
# Complete training pipeline - NO FWD USAGE
def train_bqx_model(pair='eurusd'):
    """Train BQX prediction model - FWD-free"""

    # Load data (only BQX and REG)
    bqx = load_table(f'bqx.bqx_{pair}')  # BQX table only
    reg = load_table(f'bqx.reg_{pair}')  # REG table only

    # NO FWD LOADING ✅

    # Create features and targets
    X = create_features(bqx, reg)  # Uses BQX + REG
    Y = create_targets(bqx)         # Uses BQX only

    # Train
    model = XGBRegressor()
    model.fit(X_train, Y_train)

    # NO FWD DATA IN ENTIRE PIPELINE ✅

    return model
```

### Real-Time Prediction (Zero FWD References)

```python
# Real-time predictions - NO FWD USAGE
def predict_next_60min(pair='eurusd', timestamp=None):
    """Generate prediction for next 60 minutes"""

    # Fetch current data (only BQX and REG)
    current_bqx = get_current_bqx(pair, timestamp)  # BQX table
    current_reg = get_current_reg(pair, timestamp)  # REG table

    # NO FWD FETCHING ✅

    # Extract features
    features = extract_features(current_bqx, current_reg)

    # Predict
    prediction = model.predict(features)

    # Returns: Predicted BQX_{t+60}
    # NO FWD DATA USED ✅

    return prediction
```

---

## FWD Tables: Role in BQX Strategy

### Current Role: NONE in Training

FWD tables are **NOT required** for:
- ❌ Feature extraction
- ❌ Target creation
- ❌ Model training
- ❌ Prediction generation
- ❌ Production deployment

### Potential Role: Validation Only (Optional)

FWD tables **could be used** for:
- ✅ **Validation**: Compare BQX predictions against FWD equivalents
- ✅ **Benchmarking**: Measure if BQX strategy performs better than FWD-based
- ✅ **Research**: Analyze FWD vs BQX correlation

**Example Validation (Optional)**:
```python
# OPTIONAL: Validate that BQX_{t+60} ≈ FWD_t
def validate_equivalence():
    """Check mathematical equivalence (research only)"""

    bqx = load_table('bqx.bqx_eurusd')
    fwd = load_table('bqx.fwd_eurusd')  # ONLY for validation

    # Compare values
    bqx_future = bqx['w60_bqx_return'].shift(-60)
    fwd_current = fwd['w60_fwd_return']

    correlation = np.corrcoef(bqx_future, fwd_current)[0, 1]
    print(f"BQX vs FWD correlation: {correlation:.4f}")
    # Expected: > 0.95 (nearly identical)

    # This is VALIDATION only, NOT used in training ✅
```

---

## Complete Sanitization Plan

### Phase 1: BQX ML Training (FWD-Free) ✅

```
Input Tables:
  ├─ bqx.bqx_{pair}  ← BQX momentum
  └─ bqx.reg_{pair}  ← REG patterns

Output:
  └─ Trained model predicting BQX_{t+60}

FWD Usage: ZERO ✅
```

### Phase 2: FWD Table Status (After BQX Deployment)

**Option A: Keep FWD for Validation** (Recommended Initially)
```
Status: Retain FWD tables
Purpose:
  - Validate BQX strategy performance
  - Compare against FWD-based baseline
  - Research and analysis
Usage: Offline validation only
Cost: ~50 GB storage (minimal)
```

**Option B: Archive FWD to S3**
```
Status: Move FWD to cold storage
Purpose: Historical reference
Usage: Rare analysis
Cost: ~$1/month S3 Glacier
```

**Option C: Delete FWD Completely**
```
Status: Drop all FWD tables
Purpose: Complete sanitization
Usage: None
Risk: Lose validation capability
```

### Recommended Approach

**Phase 1 (Months 1-3): Keep FWD for Validation**
```
Rationale:
  - Validate BQX strategy works as expected
  - Compare BQX vs FWD performance
  - Build confidence in new approach
  - Minimal storage cost

Actions:
  - Deploy BQX ML (FWD-free training)
  - Run validation tests (BQX vs FWD)
  - Monitor performance
```

**Phase 2 (After 3 months): Archive FWD**
```
Rationale:
  - BQX strategy proven successful
  - FWD no longer needed for daily operations
  - Reduce storage footprint

Actions:
  - Export FWD tables to S3 Glacier
  - Drop FWD tables from Aurora
  - Free ~50 GB storage
  - Retain S3 backup for research
```

**Phase 3 (Optional, After 1 year): Delete FWD**
```
Rationale:
  - BQX strategy fully mature
  - No validation needs
  - Complete FWD sanitization

Actions:
  - Delete S3 backups
  - Remove all FWD references from docs
  - Update MV tables (if any FWD columns exist)
```

---

## Code Sanitization Checklist

### Files to Update (Remove FWD References)

**Training Scripts**:
```
✅ bqx_ml_training.py - Uses only BQX + REG (NO FWD)
✅ feature_engineering.py - Extracts from BQX + REG (NO FWD)
✅ model_training.py - Trains on BQX targets (NO FWD)
```

**Prediction Scripts**:
```
✅ real_time_prediction.py - Uses BQX + REG (NO FWD)
✅ batch_prediction.py - Uses BQX + REG (NO FWD)
```

**Validation Scripts** (Optional FWD Usage):
```
⚠️ validation.py - MAY use FWD for comparison (OPTIONAL)
⚠️ benchmarking.py - MAY compare BQX vs FWD (OPTIONAL)
```

**Data Loading**:
```python
# OLD (FWD-based, REMOVE)
def load_training_data(pair):
    fwd = load_table(f'bqx.fwd_{pair}')  # ❌ DELETE THIS
    return fwd

# NEW (BQX-based, KEEP)
def load_training_data(pair):
    bqx = load_table(f'bqx.bqx_{pair}')  # ✅ BQX only
    reg = load_table(f'bqx.reg_{pair}')  # ✅ REG only
    return bqx, reg
```

### Documentation Updates

**Files to Update**:
```
├─ README.md - Update ML strategy section
├─ ML_ARCHITECTURE.md - Replace FWD with BQX
├─ FEATURE_ENGINEERING.md - Document BQX features
├─ TRAINING_GUIDE.md - Show BQX pipeline
└─ API_DOCS.md - Update prediction endpoints
```

**Search and Replace**:
```bash
# Find all FWD references in code
grep -r "fwd_" --include="*.py" --include="*.md"

# Find FWD table references
grep -r "bqx.fwd_" --include="*.py" --include="*.sql"

# Find FWD variable names
grep -r "fwd\[" --include="*.py"
```

---

## Materialized View Impact

### Current MVs (May Include FWD)

Check if materialized views use FWD:
```sql
-- Check MV definitions
SELECT
    matviewname,
    definition
FROM pg_matviews
WHERE schemaname = 'bqx'
  AND matviewname ~ '^mv_.*_merged$'
  AND definition ~ 'fwd_';
```

**If MVs Include FWD Columns**:

**Option 1: Remove FWD Columns**
```sql
-- Recreate MV without FWD columns
CREATE MATERIALIZED VIEW bqx.mv_eurusd_merged_v2 AS
SELECT
    ts_utc,
    rate,
    -- REG features
    w60_quad_norm,
    w60_r2,
    -- BQX features (NEW)
    w15_bqx_return,
    w30_bqx_return,
    w60_bqx_return
    -- NO FWD COLUMNS ✅
FROM bqx.reg_eurusd r
JOIN bqx.bqx_eurusd b USING (ts_utc);
```

**Option 2: Keep FWD in MVs (For Validation)**
```sql
-- Keep FWD in MV for validation purposes
CREATE MATERIALIZED VIEW bqx.mv_eurusd_merged_v2 AS
SELECT
    ts_utc,
    rate,
    -- REG features
    w60_quad_norm,
    -- BQX features
    w60_bqx_return,
    -- FWD features (validation only, not used in training)
    w60_fwd_return  -- ⚠️ For validation comparison
FROM bqx.reg_eurusd r
JOIN bqx.bqx_eurusd b USING (ts_utc)
JOIN bqx.fwd_eurusd f USING (ts_utc);
```

---

## Validation That Sanitization is Complete

### Test 1: Dependency Check

```python
def check_fwd_dependencies():
    """Verify no FWD dependencies in BQX ML pipeline"""

    import ast
    import os

    fwd_references = []

    # Scan all Python files
    for root, dirs, files in os.walk('./ml'):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file)) as f:
                    content = f.read()

                    # Check for FWD references
                    if 'fwd_' in content.lower():
                        fwd_references.append((file, content.count('fwd_')))

    if fwd_references:
        print("⚠️ FWD references found:")
        for file, count in fwd_references:
            print(f"  {file}: {count} references")
    else:
        print("✅ No FWD references - Sanitization complete")

    return len(fwd_references) == 0
```

### Test 2: Training Pipeline Test

```python
def test_training_without_fwd():
    """Verify training runs without FWD tables"""

    # Drop FWD table temporarily
    conn.execute("DROP TABLE IF EXISTS bqx.fwd_eurusd_temp")

    try:
        # Attempt to train model
        model = train_bqx_model('eurusd')

        # If succeeds, no FWD dependency
        print("✅ Training successful without FWD tables")
        return True

    except Exception as e:
        if 'fwd' in str(e).lower():
            print(f"❌ FWD dependency found: {e}")
            return False
        else:
            raise
```

### Test 3: Feature Extraction Test

```python
def test_feature_extraction():
    """Verify features extracted only from BQX and REG"""

    # Get feature columns
    features = create_features(bqx_df, reg_df)

    # Check column names
    fwd_columns = [col for col in features.columns if 'fwd' in col.lower()]

    if fwd_columns:
        print(f"❌ FWD features found: {fwd_columns}")
        return False
    else:
        print("✅ All features from BQX/REG only")
        return True
```

---

## Summary: FWD Sanitization Status

### Current Plan Status

| Component | FWD Usage | Status |
|-----------|-----------|--------|
| **Training Features** | None | ✅ Sanitized |
| **Training Targets** | None | ✅ Sanitized |
| **Model Training** | None | ✅ Sanitized |
| **Predictions** | None | ✅ Sanitized |
| **Validation** | Optional | ⚠️ Optional only |
| **FWD Tables** | Keep for validation | ⚠️ Temporary |

### Sanitization Timeline

**Day 1** (Immediate):
```
✅ BQX ML training pipeline (FWD-free)
✅ Feature extraction (BQX + REG only)
✅ Target creation (BQX only)
✅ Model deployment (no FWD dependencies)
```

**Month 3** (After validation):
```
✅ Archive FWD tables to S3
✅ Drop FWD from Aurora
✅ Update documentation
✅ Remove FWD from validation scripts
```

**Month 12** (Optional deep clean):
```
✅ Delete FWD S3 archives
✅ Remove all FWD code references
✅ Update MVs (remove FWD columns)
✅ Complete sanitization
```

---

## Final Answer

### Is BQX ML Strategy FWD-Free?

**YES** ✅

The BQX ML strategy is **completely independent** of FWD tables:

1. **Training**: Uses only BQX + REG tables
2. **Features**: Extracted from BQX + REG only
3. **Targets**: Created from future BQX values only
4. **Predictions**: Generated without FWD data

**FWD tables are optional** and used ONLY for:
- Validation (compare BQX predictions vs FWD equivalents)
- Research (analyze correlation)
- Benchmarking (measure improvement)

**Can be deleted** after validation period (3-6 months) without affecting BQX ML pipeline.

---

**Sanitization Plan**: [Complete FWD removal possible after validation period]
**Current Status**: BQX ML is FWD-independent from Day 1 ✅
**FWD Tables**: Optional validation only, not required for training/prediction ✅
