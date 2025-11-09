# BQX Aurora - CRITICAL PARTITION DATA ANALYSIS

**Date**: 2025-11-08
**Status**: ⚠️ **UPDATED - NON-PREFERRED PAIRS CONTAIN REAL DATA**

---

## ⚠️ CRITICAL FINDING

**Initial Assessment**: Tables appeared empty (0 bytes)
**Reality**: Tables are **PARTITIONED** and contain **ACTUAL DATA**

---

## Data Discovery

### Storage Analysis

| Metric | Value |
|--------|-------|
| **Parent Tables** | 21 tables |
| **Child Partitions** | 872 partitions |
| **Total Storage** | **5.37 GB** (5,632,122,880 bytes) |
| **Data Status** | ✅ REAL DATA (not empty!) |

### Why Initial Check Showed 0 Bytes

PostgreSQL partitioned tables:
- **Parent table**: Contains only metadata (0 bytes)
- **Child partitions**: Contain all actual data

**Initial query** checked parent tables only → showed 0 bytes
**Corrected query** checked child partitions → found 5.37 GB

---

## Detailed Partition Breakdown

### Non-Preferred Pairs - Complete Storage Analysis

| Parent Table | Partitions | Total Storage | Bytes | Sample Row Count |
|--------------|------------|---------------|-------|------------------|
| m1_eurhkd | 71 | 454 MB | 476,250,112 | ~1.8M (estimated) |
| m1_usdsgd | 66 | 403 MB | 422,338,560 | 1,660,235 ✅ |
| m1_audsgd | 69 | 390 MB | 409,313,280 | 1,796,482 ✅ |
| m1_cadsgd | 65 | 382 MB | 400,596,992 | ~1.7M (estimated) |
| m1_sgdjpy | 69 | 382 MB | 400,318,464 | ~1.7M (estimated) |
| m1_eursgd | 59 | 365 MB | 382,631,936 | ~1.6M (estimated) |
| m1_cadhkd | 57 | 345 MB | 362,061,824 | ~1.5M (estimated) |
| m1_gbphkd | 55 | 337 MB | 353,665,024 | ~1.5M (estimated) |
| m1_hkdjpy | 55 | 335 MB | 350,961,664 | ~1.5M (estimated) |
| m1_sgdchf | 59 | 305 MB | 319,881,216 | ~1.4M (estimated) |
| reg_usdsek | 12 | 241 MB | 252,674,048 | 364,463 ✅ |
| m1_chfhkd | 40 | 216 MB | 226,549,760 | ~950K (estimated) |
| m1_nzdsgd | 44 | 216 MB | 226,533,376 | ~950K (estimated) |
| m1_gbpsgd | 38 | 208 MB | 217,661,440 | ~900K (estimated) |
| m1_nzdhkd | 36 | 181 MB | 189,964,288 | ~800K (estimated) |
| fwd_usdsgd | 12 | 164 MB | 171,696,128 | 361,585 ✅ |
| reg_usdsgd | 7 | 143 MB | 149,938,176 | ~300K (estimated) |
| fwd_usdsek | 9 | 123 MB | 128,450,560 | ~250K (estimated) |
| m1_usdsek | 18 | 73 MB | 76,374,016 | ~320K (estimated) |
| m1_sgdhkd | 17 | 65 MB | 68,452,352 | ~285K (estimated) |
| m1_audhkd | 14 | 44 MB | 45,809,664 | 184,210 ✅ |

**TOTAL**: 872 partitions, 5.37 GB, **estimated 20-25 million rows**

---

## Sample Partition Details

### Example: m1_audsgd (AUD/SGD M1 data)

**Partition Structure** (69 partitions):
```
m1_audsgd_y2020m01  (16 kB - empty/minimal)
m1_audsgd_y2020m02  (16 kB - empty/minimal)
...
m1_audsgd_y2020m08  (88 kB - sparse data)
m1_audsgd_y2020m09  (6.8 MB - full data)
m1_audsgd_y2020m10  (6.7 MB - full data)
m1_audsgd_y2020m11  (6.7 MB - full data)
m1_audsgd_y2020m12  (7.2 MB - full data)
m1_audsgd_y2021m01  (7.2 MB - full data)
...
m1_audsgd_y2024m11  (7.3 MB - full data)
```

**Data Range**: September 2020 → November 2024 (50+ months)
**Total Rows**: 1,796,482 rows
**Total Storage**: 390 MB across 69 partitions

### Example: fwd_usdsgd (USD/SGD Forward Returns)

**Partition Structure** (12 partitions):
```
fwd_usdsgd_2024m07  (15 MB)
fwd_usdsgd_2024m08  (14 MB)
fwd_usdsgd_2024m09  (13 MB)
fwd_usdsgd_2024m10  (15 MB)
fwd_usdsgd_2024m11  (13 MB)
fwd_usdsgd_2024m12  (13 MB)
fwd_usdsgd_2025m01  (14 MB)
fwd_usdsgd_2025m02  (13 MB)
fwd_usdsgd_2025m03  (13 MB)
fwd_usdsgd_2025m04  (14 MB)
fwd_usdsgd_2025m05  (14 MB)
fwd_usdsgd_2025m06  (13 MB)
```

**Data Range**: July 2024 → June 2025 (12 months)
**Total Rows**: 361,585 rows
**Total Storage**: 164 MB across 12 partitions

---

## Data Timeline Analysis

### M1 Tables (Minute Data)

**Common Pattern**:
- **Early partitions (2020m01-2020m08)**: Empty or minimal (16-88 kB)
- **Active partitions (2020m09-2024m11)**: Full data (5-8 MB per month)
- **Duration**: ~50-70 months of data
- **Estimated rows per pair**: 1.5-2 million rows

### REG/FWD Tables (Regression/Forward Returns)

**Common Pattern**:
- **Active partitions (2024m07-2025m06)**: Recent data (13-15 MB per month)
- **Duration**: ~9-12 months of data
- **Estimated rows per pair**: 250K-365K rows

---

## Updated Risk Assessment

### Previous Assessment (INCORRECT)

❌ **Risk Level**: LOW
❌ **Rationale**: All tables empty (0 bytes, 0 rows)
❌ **Impact**: No data loss

### CORRECTED Assessment

⚠️ **Risk Level**: **MEDIUM-HIGH**
⚠️ **Rationale**: Tables contain 5.37 GB of real forex data
⚠️ **Impact**: **PERMANENT DATA DELETION**

---

## Data Loss Impact

### What Will Be Deleted

**Historical Forex Data**:
- ✅ 5.37 GB of minute-level (M1) forex data
- ✅ Regression analysis features
- ✅ Forward return calculations
- ✅ 20-25 million rows estimated
- ✅ Data spanning 2020-2025 (50+ months)

**Affected Currency Pairs**:
- **SGD pairs**: 9 pairs (audsgd, cadsgd, eursgd, gbpsgd, nzdsgd, sgdchf, sgdhkd, sgdjpy, usdsgd)
- **HKD pairs**: 7 pairs (audhkd, cadhkd, chfhkd, eurhkd, gbphkd, hkdjpy, nzdhkd)
- **SEK pairs**: 1 pair (usdsek)

### What Will Be Kept

**Preferred 28 Pairs**:
- All M1, REG, FWD, and MV data intact
- 2.479 TB of data (unchanged)
- 27.6 billion rows (unchanged)

---

## Critical Questions for User

### Before Proceeding with Cleanup

1. **Is this SGD/HKD/SEK data needed?**
   - Was it intentionally collected?
   - Is it used for analysis or backtesting?
   - Any future plans to use these pairs?

2. **Why does this data exist if not in repository?**
   - May have been collected during initial setup
   - May have been part of exploratory analysis
   - Repository code doesn't reference these pairs

3. **Can this data be recreated?**
   - If from Oanda API: Yes (can re-download)
   - Cost: Time + API calls
   - Historical data limits may apply

4. **Is there a backup strategy?**
   - Aurora snapshot captures all data
   - Can export to S3 before deletion
   - Can restore from snapshot if needed

---

## Recommended Actions

### Option 1: PROCEED WITH CLEANUP (Aggressive)

**Pros**:
- Database aligns with repository code
- Saves 5.37 GB storage
- Reduces maintenance overhead
- Cleans up unused data

**Cons**:
- ⚠️ **PERMANENT data loss** (5.37 GB)
- Cannot easily recreate (would need API re-download)
- May lose historical analysis capability

**Required**:
- ✅ Create Aurora snapshot (MANDATORY)
- ✅ Export data to S3 (RECOMMENDED)
- ✅ User confirmation (REQUIRED)

### Option 2: EXPORT THEN CLEANUP (Conservative)

**Steps**:
1. Create Aurora snapshot
2. Export all non-preferred pair data to S3/Parquet
3. Verify export completeness
4. Execute cleanup
5. Retain export for 1+ year

**Pros**:
- Data preserved in S3 (can restore if needed)
- Database still cleaned up
- Safety net for future needs

**Cons**:
- Takes longer (~1 hour export time)
- Requires S3 storage (~5.37 GB)
- Additional complexity

### Option 3: KEEP DATA (Status Quo)

**Pros**:
- No risk of data loss
- No action required
- Data available for future use

**Cons**:
- Database/repository mismatch remains
- Extra 872 partitions to maintain
- 5.37 GB "orphaned" data

---

## Export Procedure (If Chosen)

### S3 Export Script

```bash
#!/bin/bash
# Export non-preferred pair data to S3 before deletion

PAIRS=("audhkd" "audsgd" "cadhkd" "cadsgd" "chfhkd" "eurhkd" "eursgd"
       "gbphkd" "gbpsgd" "hkdjpy" "nzdhkd" "nzdsgd" "sgdchf" "sgdhkd"
       "sgdjpy" "usdsek" "usdsgd")

for pair in "${PAIRS[@]}"; do
    echo "Exporting m1_${pair}..."
    psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
         -U postgres -d bqx \
         -c "\COPY (SELECT * FROM bqx.m1_${pair}) TO STDOUT WITH (FORMAT CSV, HEADER)" \
         | aws s3 cp - s3://bqx-archive/non-preferred-pairs/m1_${pair}.csv

    # Export reg/fwd if they exist
    if [[ "$pair" == "usdsek" || "$pair" == "usdsgd" ]]; then
        psql ... -c "\COPY (SELECT * FROM bqx.reg_${pair}) ..." \
            | aws s3 cp - s3://bqx-archive/non-preferred-pairs/reg_${pair}.csv
        psql ... -c "\COPY (SELECT * FROM bqx.fwd_${pair}) ..." \
            | aws s3 cp - s3://bqx-archive/non-preferred-pairs/fwd_${pair}.csv
    fi
done
```

**Estimated Time**: 1-2 hours
**S3 Cost**: ~$0.12/month for 5.37 GB

---

## Updated Cleanup Plan Requirements

### MANDATORY Pre-Requisites

1. **Aurora Snapshot**: ✅ REQUIRED
2. **User Confirmation**: ✅ REQUIRED (acknowledge data deletion)
3. **S3 Export**: ⚠️ RECOMMENDED (safety net)
4. **Impact Review**: ✅ REQUIRED (read this document)

### Updated Safety Checklist

- [ ] Understand this deletes 5.37 GB of real data
- [ ] Confirm SGD/HKD/SEK pairs are not needed
- [ ] Aurora snapshot created successfully
- [ ] S3 export completed (if chosen)
- [ ] Rollback plan understood
- [ ] Authorized to delete data

---

## Rollback Capability

### Can Data Be Restored?

**Yes, via**:
1. **Aurora Snapshot** (complete cluster restore)
   - Restores ALL data as of snapshot time
   - Requires creating new cluster
   - Time: ~30 minutes

2. **S3 Export** (if created)
   - Restores only non-preferred pair data
   - Requires re-importing from CSV/Parquet
   - Time: ~2 hours

3. **Oanda API Re-Download** (fallback)
   - Re-downloads M1 data from Oanda
   - May have historical data limits
   - Time: Several hours
   - Cost: API rate limits apply

---

## Recommendation

⚠️ **DO NOT PROCEED WITHOUT**:
1. User confirmation that SGD/HKD/SEK data is not needed
2. Aurora snapshot creation
3. Understanding this is PERMANENT data deletion

**Suggested Approach**:
1. Review this analysis with user
2. Confirm data is truly not needed
3. Create Aurora snapshot
4. (Optional but recommended) Export to S3
5. Execute cleanup only after explicit user approval

---

**Analysis Date**: 2025-11-08
**Status**: ⚠️ CRITICAL UPDATE - Cleanup plan must be revised
**Next Action**: USER DECISION REQUIRED
