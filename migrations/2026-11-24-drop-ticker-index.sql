-- Drops idx_ohlcv_unified_ticker, which is redundant.
--
-- ticker is the leading column of both idx_ohlcv_unified_ticker_date
-- (ticker, date) and the primary key (ticker, exchange, asset_type, date),
-- so every lookup that could use it is already served by those indexes.
-- Removing it saves ~5.5 GB and one index write per insert.
--
-- DROP INDEX CONCURRENTLY is not supported on partitioned indexes, so this
-- takes a brief ACCESS EXCLUSIVE lock on the parent while it drops the
-- parent and its 68 children. Fast (metadata only), but run off-peak anyway.
--
-- Run:
--   psql "$DATABASE_URL" -f migrations/2026-11-24-drop-ticker-index.sql

DROP INDEX IF EXISTS idx_ohlcv_unified_ticker;

-- Verify: the old index is gone and ticker-prefixed indexes remain.
--   SELECT indexname FROM pg_indexes
--    WHERE tablename IN ('ohlcv_unified', 'ohlcv_unified_2026')
--      AND indexname LIKE '%ticker%'
--    ORDER BY indexname;
--
-- Rollback (rebuilds ~5.5 GB, several minutes):
--   CREATE INDEX IF NOT EXISTS idx_ohlcv_unified_ticker
--       ON ohlcv_unified (ticker);
