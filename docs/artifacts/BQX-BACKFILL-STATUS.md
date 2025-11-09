# BQX Historical Data Backfill - Status Report

**Date**: 2025-11-09
**Status**: IN PROGRESS
**Database**: trillium-bqx-cluster (Aurora PostgreSQL)

---

## Current Progress

### Test Run (Completed)
- **Pair**: EURUSD
- **Period**: 2024-07-01 to 2024-08-01
- **Rows**: 32,687
- **Time**: 82.84s
- **Rate**: 395 rows/sec
- **Result**: ✅ PASSED

### Full Backfill (In Progress)

**Scope**:
- Pairs: 28 (all preferred forex pairs)
- Months: 12 (2024-07 through 2025-06)
- Total jobs: 336

**Current Status** (as of 00:43 UTC):
- **AUDCAD**: 3/12 months complete (93,386 rows)
  - 2024-07: 32,434 rows (80.3s)
  - 2024-08: 31,099 rows (75.6s)
  - 2024-09: 29,853 rows (68.4s)
- **Progress**: 0.9% (3/336 jobs)

**Performance**:
- Average: ~31,000 rows/month
- Processing time: 70-80 seconds/month
- Rate: ~390-440 rows/sec

---

## Projections

### Time Estimates

```
Jobs remaining: 333
Average time: 75 seconds/job
Total time remaining: 333 × 75 = 24,975 seconds

Estimated completion: ~6.9 hours from 00:43 UTC
Expected finish: ~07:35 UTC (November 9, 2025)
```

### Storage Estimates

```
Average rows/pair: 31,000 rows/month × 12 months = 372,000 rows
Total rows (28 pairs): 28 × 372,000 = 10,416,000 rows
Row size: ~320 bytes
Total storage: 10,416,000 × 320 = ~3.33 GB
With indexes (~30% overhead): ~4.3 GB
```

---

## Monitoring

### Live Progress

**Background process ID**: cbcbbf

**Monitor with**:
```bash
# View live progress (updates every ~75 seconds)
tail -f /tmp/bqx_backfill.log

# Check database row counts
psql -h trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com \
  -U postgres -d bqx \
  -c "SELECT 'audcad' as pair, COUNT(*) FROM bqx.bqx_audcad
      UNION ALL SELECT 'eurusd', COUNT(*) FROM bqx.bqx_eurusd
      ORDER BY pair;"
```

### Expected Log Format

```
================================================================================
Processing: {PAIR}
================================================================================
  [2024-07]  32,434 rows |  80.3s | Progress:   0.3%
  [2024-08]  31,099 rows |  75.6s | Progress:   0.6%
  [2024-09]  29,853 rows |  68.4s | Progress:   0.9%
  ...
  [2025-06]  31,500 rows |  77.2s | Progress:   3.6%

  {PAIR} Total: 372,000 rows in 920.5s
```

---

## Data Verification

### Edge Effects (Expected)

First 75 rows of each partition should have NULLs:
- First 15 rows: w15, w30, w45, w60, w75 = NULL
- Rows 15-29: w30, w45, w60, w75 = NULL
- Rows 30-44: w45, w60, w75 = NULL
- Rows 45-59: w60, w75 = NULL
- Rows 60-74: w75 = NULL
- Row 75+: All windows populated

### Sample Verification Query

```sql
-- Check AUDCAD August 2024 (should be complete now)
SELECT
    ts_utc,
    rate,
    w15_bqx_return,
    w30_bqx_return,
    w60_bqx_return,
    w75_bqx_return
FROM bqx.bqx_audcad
WHERE ts_utc >= '2024-08-01' AND ts_utc < '2024-09-01'
ORDER BY ts_utc
LIMIT 100;
```

---

## Completion Checklist

When backfill completes, verify:

- [ ] All 28 pairs have ~372,000 rows each
- [ ] No processing errors in log
- [ ] NULL distribution matches edge effect pattern
- [ ] BQX formulas produce expected values (positive/negative)
- [ ] Storage usage ~4-5 GB for all BQX tables
- [ ] All 336 monthly partitions populated

---

## Next Steps After Backfill

1. **Verify data integrity**
   - Check row counts for all pairs
   - Validate NULL patterns (edge effects)
   - Sample calculations to verify formulas

2. **Recreate materialized views**
   - Design new schema: M1 + REG + BQX
   - Create 28 mv_{pair}_merged tables
   - Populate with historical data

3. **Update ML pipeline**
   - Implement BQX feature extraction
   - Test autoregressive model (BQX_t → BQX_{t+60})
   - Baseline performance evaluation

4. **Real-time integration**
   - Update data ingestion to compute BQX metrics live
   - Add monitoring/alerting
   - Performance optimization

---

## Current System State

```
M1 Tables:  28 ✅ (source data for BQX calculation)
REG Tables: 28 ✅ (intact)
BQX Tables: 28 🔄 (backfilling: 0.9% complete)
FWD Tables: 0 (deleted 2025-11-09)
MV Tables:  0 (need recreation after BQX backfill)
```

---

**Backfill Script**: `/home/ubuntu/Robkei-Ring/sandbox/scripts/backward_worker.py`
**Log File**: `/tmp/bqx_backfill.log`
**Process Status**: RUNNING (background ID: cbcbbf)

---

**Note**: This process will run for approximately 7 hours. It can safely run unattended. Progress will be logged to `/tmp/bqx_backfill.log` with updates every ~75 seconds.
