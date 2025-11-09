# BQX Aurora Database - Pair Comparison Summary

**Analysis Date**: 2025-11-08
**Database**: Trillium BQX Aurora Cluster
**Comparison**: Repository (bqx-db) vs Aurora Database

---

## Executive Summary

| Metric | Repository | Aurora | Status |
|--------|------------|--------|--------|
| **Total Pairs** | 28 | 45 | ❌ Mismatch |
| **Preferred Pairs** | 28 | 28 | ✅ All exist |
| **Non-Preferred Pairs** | 0 | 17 | ⚠️ Need cleanup |
| **Tables (Total)** | ~84 (28×3) | 105 (45 pairs) | ❌ Excess |
| **Storage Impact** | - | 0 bytes | ✅ Safe to remove |

---

## Detailed Comparison

### ✅ Preferred 28 Pairs (KEEP - In Both Repository & Aurora)

| # | Pair | Currency Description | Status |
|---|------|---------------------|--------|
| 1 | audcad | Australian Dollar / Canadian Dollar | ✅ Match |
| 2 | audchf | Australian Dollar / Swiss Franc | ✅ Match |
| 3 | audjpy | Australian Dollar / Japanese Yen | ✅ Match |
| 4 | audnzd | Australian Dollar / New Zealand Dollar | ✅ Match |
| 5 | audusd | Australian Dollar / US Dollar | ✅ Match |
| 6 | cadchf | Canadian Dollar / Swiss Franc | ✅ Match |
| 7 | cadjpy | Canadian Dollar / Japanese Yen | ✅ Match |
| 8 | chfjpy | Swiss Franc / Japanese Yen | ✅ Match |
| 9 | euraud | Euro / Australian Dollar | ✅ Match |
| 10 | eurcad | Euro / Canadian Dollar | ✅ Match |
| 11 | eurchf | Euro / Swiss Franc | ✅ Match |
| 12 | eurgbp | Euro / British Pound | ✅ Match |
| 13 | eurjpy | Euro / Japanese Yen | ✅ Match |
| 14 | eurnzd | Euro / New Zealand Dollar | ✅ Match |
| 15 | eurusd | Euro / US Dollar | ✅ Match |
| 16 | gbpaud | British Pound / Australian Dollar | ✅ Match |
| 17 | gbpcad | British Pound / Canadian Dollar | ✅ Match |
| 18 | gbpchf | British Pound / Swiss Franc | ✅ Match |
| 19 | gbpjpy | British Pound / Japanese Yen | ✅ Match |
| 20 | gbpnzd | British Pound / New Zealand Dollar | ✅ Match |
| 21 | gbpusd | British Pound / US Dollar | ✅ Match |
| 22 | nzdcad | New Zealand Dollar / Canadian Dollar | ✅ Match |
| 23 | nzdchf | New Zealand Dollar / Swiss Franc | ✅ Match |
| 24 | nzdjpy | New Zealand Dollar / Japanese Yen | ✅ Match |
| 25 | nzdusd | New Zealand Dollar / US Dollar | ✅ Match |
| 26 | usdcad | US Dollar / Canadian Dollar | ✅ Match |
| 27 | usdchf | US Dollar / Swiss Franc | ✅ Match |
| 28 | usdjpy | US Dollar / Japanese Yen | ✅ Match |

**Result**: ✅ **100% match** - All 28 preferred pairs exist in Aurora

---

### ❌ Non-Preferred 17 Pairs (REMOVE - In Aurora Only)

#### SGD Pairs (Singapore Dollar) - 9 Pairs

| # | Pair | Currency Description | Tables | Status |
|---|------|---------------------|--------|--------|
| 1 | audsgd | Australian Dollar / Singapore Dollar | m1 | ❌ Remove |
| 2 | cadsgd | Canadian Dollar / Singapore Dollar | m1 | ❌ Remove |
| 3 | eursgd | Euro / Singapore Dollar | m1 | ❌ Remove |
| 4 | gbpsgd | British Pound / Singapore Dollar | m1 | ❌ Remove |
| 5 | nzdsgd | New Zealand Dollar / Singapore Dollar | m1 | ❌ Remove |
| 6 | sgdchf | Singapore Dollar / Swiss Franc | m1 | ❌ Remove |
| 7 | sgdhkd | Singapore Dollar / Hong Kong Dollar | m1 | ❌ Remove |
| 8 | sgdjpy | Singapore Dollar / Japanese Yen | m1 | ❌ Remove |
| 9 | usdsgd | US Dollar / Singapore Dollar | m1, reg, fwd | ❌ Remove |

#### HKD Pairs (Hong Kong Dollar) - 7 Pairs

| # | Pair | Currency Description | Tables | Status |
|---|------|---------------------|--------|--------|
| 10 | audhkd | Australian Dollar / Hong Kong Dollar | m1 | ❌ Remove |
| 11 | cadhkd | Canadian Dollar / Hong Kong Dollar | m1 | ❌ Remove |
| 12 | chfhkd | Swiss Franc / Hong Kong Dollar | m1 | ❌ Remove |
| 13 | eurhkd | Euro / Hong Kong Dollar | m1 | ❌ Remove |
| 14 | gbphkd | British Pound / Hong Kong Dollar | m1 | ❌ Remove |
| 15 | hkdjpy | Hong Kong Dollar / Japanese Yen | m1 | ❌ Remove |
| 16 | nzdhkd | New Zealand Dollar / Hong Kong Dollar | m1 | ❌ Remove |

#### SEK Pairs (Swedish Krona) - 1 Pair

| # | Pair | Currency Description | Tables | Status |
|---|------|---------------------|--------|--------|
| 17 | usdsek | US Dollar / Swedish Krona | m1, reg, fwd | ❌ Remove |

**Result**: ❌ **17 extra pairs** - Not in repository, should be removed from Aurora

---

## Table Breakdown

### Preferred Pairs - Table Distribution

| Table Type | Per Pair | Total (28 pairs) | Status |
|------------|----------|------------------|--------|
| m1_* | 1 | 28 | ✅ All exist |
| reg_* | 1 | 28 | ✅ All exist |
| fwd_* | 1 | 28 | ✅ All exist |
| mv_*_merged | 1 | 28 | ✅ All exist |
| **Subtotal** | 4 | **112 tables** | ✅ Complete |

### Non-Preferred Pairs - Table Distribution

| Table Type | Count | Pairs | Status |
|------------|-------|-------|--------|
| m1_* | 17 | All 17 pairs | ❌ Remove |
| reg_* | 2 | usdsek, usdsgd | ❌ Remove |
| fwd_* | 2 | usdsek, usdsgd | ❌ Remove |
| mv_*_merged | 0 | None | ✅ None exist |
| **Subtotal** | **21 tables** | **17 pairs** | ❌ To remove |

---

## Storage Impact Analysis

### Non-Preferred Pairs Storage

| Pair | M1 Table | REG Table | FWD Table | Total Size |
|------|----------|-----------|-----------|------------|
| audsgd | 0 bytes | - | - | 0 bytes |
| cadsgd | 0 bytes | - | - | 0 bytes |
| eursgd | 0 bytes | - | - | 0 bytes |
| gbpsgd | 0 bytes | - | - | 0 bytes |
| nzdsgd | 0 bytes | - | - | 0 bytes |
| sgdchf | 0 bytes | - | - | 0 bytes |
| sgdhkd | 0 bytes | - | - | 0 bytes |
| sgdjpy | 0 bytes | - | - | 0 bytes |
| audhkd | 0 bytes | - | - | 0 bytes |
| cadhkd | 0 bytes | - | - | 0 bytes |
| chfhkd | 0 bytes | - | - | 0 bytes |
| eurhkd | 0 bytes | - | - | 0 bytes |
| gbphkd | 0 bytes | - | - | 0 bytes |
| hkdjpy | 0 bytes | - | - | 0 bytes |
| nzdhkd | 0 bytes | - | - | 0 bytes |
| usdsek | 0 bytes | 0 bytes | 0 bytes | 0 bytes |
| usdsgd | 0 bytes | 0 bytes | 0 bytes | 0 bytes |

**Total Storage**: **0 bytes** (all tables empty)

---

## Why These Pairs Are Not in Repository

### Currency Analysis

**Repository uses 8 currencies**:
- EUR (Euro)
- USD (US Dollar)
- GBP (British Pound)
- JPY (Japanese Yen)
- AUD (Australian Dollar)
- CAD (Canadian Dollar)
- CHF (Swiss Franc)
- NZD (New Zealand Dollar)

**Non-preferred currencies**:
- SGD (Singapore Dollar) - Lower liquidity
- HKD (Hong Kong Dollar) - Lower liquidity
- SEK (Swedish Krona) - Lower liquidity

### Selection Rationale

The repository's 28 pairs were chosen for:
1. ✅ **High liquidity** (all major USD pairs + key crosses)
2. ✅ **Complete network** (8 currencies, 7 pairs each - perfect balance)
3. ✅ **Trading relevance** (24-hour session coverage)
4. ✅ **Data availability** (Oanda API M1 granularity)
5. ✅ **ML optimization** (sized for AWS infrastructure)

**SGD, HKD, SEK pairs**:
- ❌ Lower liquidity vs G7 currencies
- ❌ Not part of core 8-currency network
- ❌ Tables created but never populated
- ❌ Not used in ML pipeline code

---

## Cleanup Impact

### Before Cleanup

| Metric | Value |
|--------|-------|
| Total unique pairs | 45 |
| Total base tables | 105 |
| Total MVs | 28 |
| Schema size | 2.485 TB |

### After Cleanup

| Metric | Value | Change |
|--------|-------|--------|
| Total unique pairs | 28 | -17 pairs |
| Total base tables | 84 | -21 tables |
| Total MVs | 28 | No change |
| Schema size | 2.485 TB | 0 bytes (no data loss) |

### Benefits

✅ **Alignment**: Database matches repository (100%)
✅ **Clarity**: Only preferred pairs remain
✅ **Maintenance**: Fewer tables to manage
✅ **Performance**: Smaller metadata catalogs
✅ **Safety**: All removed tables are empty

---

## Verification Queries

### Count Preferred Pairs in Repository
```python
# From bqx-db/scripts/ml/refresh_all_28_mvs_parallel.py
PAIRS = [
    "audcad", "audchf", "audjpy", "audnzd", "audusd",
    "cadchf", "cadjpy", "chfjpy",
    "euraud", "eurcad", "eurchf", "eurgbp", "eurjpy", "eurnzd", "eurusd",
    "gbpaud", "gbpcad", "gbpchf", "gbpjpy", "gbpnzd", "gbpusd",
    "nzdcad", "nzdchf", "nzdjpy", "nzdusd",
    "usdcad", "usdchf", "usdjpy",
]
print(f"Preferred pairs: {len(PAIRS)}")
# Output: 28
```

### Count All Pairs in Aurora
```sql
SELECT COUNT(DISTINCT SUBSTRING(tablename FROM '^m1_(.+)$'))
FROM pg_tables
WHERE schemaname = 'bqx' AND tablename ~ '^m1_[a-z]+$';
-- Output: 45 (before cleanup)
-- Expected: 28 (after cleanup)
```

### Verify Non-Preferred Pairs
```sql
SELECT SUBSTRING(tablename FROM '^m1_(.+)$') as pair_name
FROM pg_tables
WHERE schemaname = 'bqx'
  AND tablename ~ '^m1_[a-z]+$'
  AND tablename !~ '^m1_(audcad|audchf|audjpy|audnzd|audusd|cadchf|cadjpy|chfjpy|euraud|eurcad|eurchf|eurgbp|eurjpy|eurnzd|eurusd|gbpaud|gbpcad|gbpchf|gbpjpy|gbpnzd|gbpusd|nzdcad|nzdchf|nzdjpy|nzdusd|usdcad|usdchf|usdjpy)$'
ORDER BY pair_name;
-- Output: 17 rows (non-preferred pairs)
```

---

## Recommendation

**Action**: ✅ **EXECUTE CLEANUP**

**Rationale**:
1. All non-preferred tables are empty (0 bytes, 0 rows)
2. No risk of data loss
3. No foreign key dependencies
4. Perfect alignment with repository code
5. Aurora snapshot provides rollback safety

**Next Steps**:
1. Review [cleanup plan](BQX-FOREX-PAIR-CLEANUP-PLAN.md)
2. Create Aurora snapshot
3. Execute [cleanup SQL script](bqx_cleanup_non_preferred_pairs.sql)
4. Verify 28 preferred pairs remain

---

**Analysis Completed**: 2025-11-08
**Status**: ✅ Ready for Cleanup Execution
**Risk**: LOW
**Estimated Time**: 15 minutes
