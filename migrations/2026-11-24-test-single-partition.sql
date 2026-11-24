-- Dry-run a single partition before running the full index migration.
-- Builds (exchange, date) on ONE partition only, verifies the index is usable,
-- then removes it again so the real migration starts clean.
--
-- Target: ohlcv_unified_1962 -- the oldest partition (7,847 rows, ~1.8 MB,
-- exchanges US + INDX), so lock time and disk churn are negligible.
--
-- Run with psql (no wrapping transaction):
--   psql "$DATABASE_URL" -f migrations/2026-11-24-test-single-partition.sql
--
-- Reads continue throughout; only writes to this one partition wait
-- (well under a second at this size). Nothing else is affected.

\set target 'ohlcv_unified_1962'

-- 1. How big is the partition, and what is actually in it?
SELECT relname, pg_size_pretty(pg_relation_size(oid)) AS heap
FROM pg_class
WHERE relname = :'target';

SELECT count(*) AS rows, min(date), max(date) FROM ohlcv_unified_1962;

SELECT exchange, count(*) FROM ohlcv_unified_1962 GROUP BY 1 ORDER BY 2 DESC;

\timing on

-- 2. Build the index on this partition only (SHARE lock, reads unaffected).
CREATE INDEX IF NOT EXISTS ohlcv_unified_1962_exchange_date_idx
    ON ohlcv_unified_1962 (exchange, date);

\timing off

-- 3. At 1.8 MB the whole partition fits in a few pages, so the planner will
--    normally prefer a Seq Scan. Disable it to prove the index can serve the
--    predicate and the ordering -- that is what matters on the large years.
SET enable_seqscan = off;

EXPLAIN (COSTS OFF)
SELECT * FROM ohlcv_unified_1962
WHERE exchange = 'US'
  AND date >= '1962-01-01' AND date <= '1962-12-31'
ORDER BY date DESC
LIMIT 2;

EXPLAIN (COSTS OFF)
SELECT count(*) FROM ohlcv_unified_1962
WHERE exchange = 'US'
  AND date >= '1962-01-01' AND date <= '1962-12-31';

-- Expect: Index Scan / Index Only Scan using ohlcv_unified_1962_exchange_date_idx
-- with Index Cond on BOTH exchange and date, and no "Filter: exchange".

\timing on

-- 4. Real timings with the index chosen (seqscan still disabled).
EXPLAIN ANALYZE
SELECT * FROM ohlcv_unified_1962
WHERE exchange = 'US'
  AND date >= '1962-01-01' AND date <= '1962-12-31'
ORDER BY date DESC
LIMIT 2;

EXPLAIN ANALYZE
SELECT count(*) FROM ohlcv_unified_1962
WHERE exchange = 'US'
  AND date >= '1962-01-01' AND date <= '1962-12-31';

\timing off

-- 5. Same shape on the other exchange present here, with the planner free to
--    choose. A Seq Scan is expected at this size and is NOT a failure.
RESET enable_seqscan;

EXPLAIN ANALYZE
SELECT * FROM ohlcv_unified_1962
WHERE exchange = 'INDX'
  AND date >= '1962-01-01' AND date <= '1962-12-31'
ORDER BY date DESC
LIMIT 2;

-- 6. Clean up so the real migration builds it (and attaches it) itself.
DROP INDEX IF EXISTS ohlcv_unified_1962_exchange_date_idx;

-- If step 3 used the new index with Index Cond on both columns, the migration is
-- safe to run: migrations/2026-11-24-ohlcv-unified-exchange-date-index.sql
-- If step 3 still shows a Seq Scan or Bitmap Heap Scan, stop and report.
