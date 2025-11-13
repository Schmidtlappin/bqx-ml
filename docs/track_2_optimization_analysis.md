# Track 2 Regression Features - Performance Optimization Analysis

**Date:** 2025-11-13
**Current Status:** 4 workers at 99.6% CPU, 0/336 partitions complete
**Goal:** Maximize throughput to complete 336 partitions faster

---

## Current Performance Metrics

### System Capacity
```
CPU:        4/8 cores utilized (50% capacity)
Load Avg:   3.90 (could handle 8.0)
Memory:     5.2Gi / 30Gi used (17% - plenty of headroom)
Disk I/O:   Not bottlenecked
```

### Aurora Database
```
Connections:     5 / 2000 (0.25% utilization)
Max Connections: 2000
Connection Pool: Enormous headroom available
```

### Track 2 Workers
```
Current Workers:  4
Worker CPU:       99.6-99.7% each
Worker Memory:    ~250-300 MB each
State:            Computing w60, w75, agg windows (longest windows)
```

---

## Bottleneck Analysis

### 1. **CPU Underutilization** ⚠️ PRIMARY BOTTLENECK
**Impact:** HIGH
**Current:** 4/8 cores at 100%
**Potential:** 2x throughput by using all 8 cores

**Root Cause:**
```python
# populate_regression_features_worker.py:314
max_workers = 4  # ❌ Hardcoded to 4
```

**Issue:** Worker count set to 4, leaving 4 cores idle while Track 2 is the slowest track.

**Evidence:**
- Load average: 3.90 (room for 4.1 more)
- 4 cores at ~0% utilization
- Memory has 25Gi available

---

### 2. **DataFrame Fragmentation** ⚠️ SECONDARY BOTTLENECK
**Impact:** MEDIUM
**Current:** Repeated `results[col_name] = None` causing fragmentation
**Penalty:** ~20-30% slower than optimal

**Root Cause:**
```python
# populate_regression_features_worker.py:213-238
for i in range(len(df)):
    for metric in [...]:
        col_name = f"{metric}_idx_{window_name}"
        if col_name not in results.columns:
            results[col_name] = None  # ❌ Fragments DataFrame
        results.at[i, col_name] = metric_value
```

**Performance Warning:**
```
PerformanceWarning: DataFrame is highly fragmented.
This is usually the result of calling `frame.insert` many times, which has poor performance.
Consider joining all columns at once using pd.concat(axis=1) instead.
```

**Issue:**
- Creating columns dynamically during iteration
- Each `.at[]` assignment on fragmented DataFrame is slow
- Happens for 6 windows × 15 metrics × 2 domains = 180 columns

---

### 3. **Row-by-Row Database Insertion** ⚠️ TERTIARY BOTTLENECK
**Impact:** LOW (but fixable)
**Current:** Individual INSERT statements per row
**Penalty:** ~2-3x slower than batch insert

**Root Cause:**
```python
# populate_regression_features_worker.py:272-277
for _, row in reg_rate_data.iterrows():
    placeholders = ','.join(['%s'] * len(reg_rate_cols))
    cursor.execute(
        f"INSERT INTO bqx.{partition_name} ({','.join(reg_rate_cols)}) VALUES ({placeholders})",
        tuple(row)
    )
```

**Issue:**
- ~30,000 rows × 2 tables = 60,000 individual INSERT statements per partition
- Each INSERT is a round-trip to Aurora
- No batching or bulk loading

---

## Optimization Recommendations

### Priority 1: Increase Worker Count (IMMEDIATE - 2x speedup)

**Change:**
```python
# Before:
max_workers = 4

# After:
max_workers = 8  # Use all available cores
```

**Expected Impact:**
- Throughput: 4 → 8 partitions processing simultaneously
- ETA: 8-12 hours → 4-6 hours
- CPU Load: 3.90 → ~7.50 (still safe)
- Memory: 5.2Gi → ~10Gi (still plenty of headroom)

**Risk:** LOW - System has capacity
**Effort:** 1 line change

---

### Priority 2: Fix DataFrame Fragmentation (30% speedup per worker)

**Change:**
```python
# Before: Create columns dynamically
for i in range(len(df)):
    if i < window_size - 1:
        for metric in ['a2', 'a1', 'b', ...]:
            col_name = f"{metric}_idx_{window_name}"
            if col_name not in results.columns:
                results[col_name] = None
    # ... compute and assign

# After: Pre-allocate all columns
# 1. Create all column names upfront
all_metrics = ['a2', 'a1', 'b', 'r2', 'rmse', 'residual_mean',
               'residual_std', 'pred_interval_lower', 'pred_interval_upper',
               'prediction', 'vertex_x', 'vertex_y', 'curvature',
               'fit_quality', 'extrapolation_error']

for window_name in WINDOWS.keys():
    for metric in all_metrics:
        results[f"{metric}_idx_{window_name}"] = None
        results[f"{metric}_bqx_{window_name}"] = None

# 2. Then populate (no fragmentation)
for window_name, window_size in WINDOWS.items():
    for i in range(len(df)):
        if i < window_size - 1:
            continue
        # ... compute
        for metric_name, metric_value in metrics.items():
            results.at[i, f"{metric_name}_idx_{window_name}"] = metric_value
```

**Expected Impact:**
- Computation speed: +20-30% per partition
- Memory: Slightly better (consolidated DataFrame)
- ETA: 4-6 hours → 3-5 hours

**Risk:** LOW - Standard pandas optimization
**Effort:** ~20 lines change

---

### Priority 3: Use Bulk INSERT (3x faster database writes)

**Change:**
```python
# Before: Row-by-row
for _, row in reg_rate_data.iterrows():
    cursor.execute(f"INSERT INTO ... VALUES (...)", tuple(row))

# After: Bulk insert with execute_values
from psycopg2.extras import execute_values

values = [tuple(row) for row in reg_rate_data.values]
execute_values(
    cursor,
    f"INSERT INTO bqx.{partition_name} ({','.join(reg_rate_cols)}) VALUES %s",
    values,
    page_size=1000  # Batch size
)
```

**Expected Impact:**
- Database insertion: 60,000 INSERTs → 30-60 batch calls
- Time per partition: -2-3 minutes
- ETA: 3-5 hours → 2.5-4 hours

**Risk:** LOW - Already used in Track 1 successfully
**Effort:** ~10 lines change

---

## Combined Impact

### Current State
```
Workers:        4
Time/partition: ~8-10 minutes (estimated)
Total time:     336 × 8 / 4 = 672 minutes = 11.2 hours
```

### After All Optimizations
```
Workers:          8 (2x)
Time/partition:   ~4-5 minutes (1.8x faster per worker)
Total time:       336 × 4.5 / 8 = 189 minutes = 3.1 hours
```

**Overall Speedup: 3.6x** (11.2 hours → 3.1 hours)

---

## Implementation Strategy

### Phase 1: Immediate (Restart with 8 workers)
1. Stop current Track 2 workers
2. Update `max_workers = 4` → `max_workers = 8`
3. Restart Track 2
4. Monitor: CPU should go to ~7.5 load, memory to ~10Gi
5. **ETA: 6-8 hours** (instead of 11-12)

### Phase 2: DataFrame Optimization (Can be done separately)
1. Pre-allocate all columns before computation loop
2. Remove dynamic column creation
3. Test on single partition
4. Deploy and restart
5. **Additional speedup: 20-30%**

### Phase 3: Bulk INSERT (Can be done separately)
1. Replace row-by-row INSERT with execute_values
2. Test on single partition
3. Deploy and restart
4. **Additional speedup: 2-3 minutes per partition**

---

## Aurora Capacity Analysis

### Current Usage
```
Connections:  5 / 2000 (0.25%)
Workers:      4
Conn/Worker:  ~1.25 average
```

### With 8 Workers
```
Connections:  ~10 / 2000 (0.5%)
Workers:      8
Conn/Worker:  ~1.25 average
Risk:         NONE - still 1,990 connections available
```

### With 16 Workers (Future consideration)
```
Connections:  ~20 / 2000 (1%)
Workers:      16
Bottleneck:   Would shift to EC2 CPU (8 cores max)
Recommendation: Not worth it - EC2 would bottleneck
```

**Conclusion:** Aurora can easily handle 8 workers, or even 16+. EC2 CPU is the limiting factor.

---

## Memory Analysis

### Current Usage
```
Total:        30Gi
Used:         5.2Gi (17%)
Available:    25Gi
Per Worker:   ~300 MB average
```

### With 8 Workers
```
Expected:     8 workers × 300 MB = 2.4Gi
Total Used:   5.2Gi + 2.4Gi = 7.6Gi
Available:    22.4Gi (still plenty)
Risk:         NONE
```

### Maximum Theoretical
```
Max Workers:  ~80 (30Gi / 300MB = 100, leave 20Gi for OS)
Bottleneck:   CPU (only 8 cores)
```

**Conclusion:** Memory is NOT a constraint. CPU is the constraint.

---

## Recommended Action Plan

### Immediate (Now)
✅ **Stop current Track 2 workers**
✅ **Update max_workers from 4 to 8**
✅ **Restart Track 2**
✅ **Monitor system resources**

**Expected Outcome:**
- ETA: 11-12 hours → 6-8 hours
- CPU Load: 3.90 → ~7.50
- Memory: 5.2Gi → ~10Gi
- Aurora Connections: 5 → ~10

### Next Session (After Track 2 completes)
- Implement DataFrame pre-allocation
- Implement bulk INSERT with execute_values
- Test optimizations on smaller dataset
- Deploy for future runs

---

## Risk Assessment

### Increasing to 8 Workers
- **Risk:** LOW
- **Bottleneck:** None identified
- **Monitoring:** Watch load average (should stay < 8.0)
- **Rollback:** Easy - kill processes and restart with 4

### DataFrame Optimization
- **Risk:** LOW
- **Testing:** Required on single partition first
- **Impact:** Positive only

### Bulk INSERT
- **Risk:** LOW
- **Testing:** Already proven in Track 1
- **Impact:** Faster writes, same data

---

**Analysis Date:** 2025-11-13
**Analyst:** Phase 2 Optimization Review
**Status:** ✅ Ready for immediate optimization (8 workers)
