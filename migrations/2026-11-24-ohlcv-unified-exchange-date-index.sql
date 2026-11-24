-- Adds (exchange, date) to ohlcv_unified and drops the redundant (exchange) index.
--
-- Plain per-partition build. Each CREATE INDEX takes a SHARE lock on ONE
-- partition: reads keep working, only writes to that partition wait (seconds
-- on the big years). Other partitions and the parent stay fully available.
-- Partitions are ordered newest-first so the ones the API queries (default,
-- 2028, 2027, 2026, 2025...) are done in the first few minutes.
--
-- Run with psql (no wrapping transaction):
--   psql "$DATABASE_URL" -f migrations/2026-11-24-ohlcv-unified-exchange-date-index.sql
--
-- Resumable: every statement uses IF NOT EXISTS, so re-running skips finished work.
-- Expect ~60-90 min total and ~4.5 GB extra disk until the old index is dropped.

-- 1. Parent index shell. Metadata only, instant, no scan.
CREATE INDEX IF NOT EXISTS idx_ohlcv_unified_exchange_date
    ON ONLY ohlcv_unified (exchange, date);

-- 2. Build one index per partition, newest first.
CREATE INDEX IF NOT EXISTS ohlcv_unified_default_exchange_date_idx ON ohlcv_unified_default (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2028_exchange_date_idx ON ohlcv_unified_2028 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2027_exchange_date_idx ON ohlcv_unified_2027 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2026_exchange_date_idx ON ohlcv_unified_2026 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2025_exchange_date_idx ON ohlcv_unified_2025 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2024_exchange_date_idx ON ohlcv_unified_2024 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2023_exchange_date_idx ON ohlcv_unified_2023 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2022_exchange_date_idx ON ohlcv_unified_2022 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2021_exchange_date_idx ON ohlcv_unified_2021 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2020_exchange_date_idx ON ohlcv_unified_2020 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2019_exchange_date_idx ON ohlcv_unified_2019 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2018_exchange_date_idx ON ohlcv_unified_2018 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2017_exchange_date_idx ON ohlcv_unified_2017 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2016_exchange_date_idx ON ohlcv_unified_2016 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2015_exchange_date_idx ON ohlcv_unified_2015 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2014_exchange_date_idx ON ohlcv_unified_2014 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2013_exchange_date_idx ON ohlcv_unified_2013 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2012_exchange_date_idx ON ohlcv_unified_2012 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2011_exchange_date_idx ON ohlcv_unified_2011 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2010_exchange_date_idx ON ohlcv_unified_2010 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2009_exchange_date_idx ON ohlcv_unified_2009 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2008_exchange_date_idx ON ohlcv_unified_2008 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2007_exchange_date_idx ON ohlcv_unified_2007 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2006_exchange_date_idx ON ohlcv_unified_2006 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2005_exchange_date_idx ON ohlcv_unified_2005 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2004_exchange_date_idx ON ohlcv_unified_2004 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2003_exchange_date_idx ON ohlcv_unified_2003 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2002_exchange_date_idx ON ohlcv_unified_2002 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2001_exchange_date_idx ON ohlcv_unified_2001 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_2000_exchange_date_idx ON ohlcv_unified_2000 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1999_exchange_date_idx ON ohlcv_unified_1999 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1998_exchange_date_idx ON ohlcv_unified_1998 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1997_exchange_date_idx ON ohlcv_unified_1997 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1996_exchange_date_idx ON ohlcv_unified_1996 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1995_exchange_date_idx ON ohlcv_unified_1995 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1994_exchange_date_idx ON ohlcv_unified_1994 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1993_exchange_date_idx ON ohlcv_unified_1993 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1992_exchange_date_idx ON ohlcv_unified_1992 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1991_exchange_date_idx ON ohlcv_unified_1991 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1990_exchange_date_idx ON ohlcv_unified_1990 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1989_exchange_date_idx ON ohlcv_unified_1989 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1988_exchange_date_idx ON ohlcv_unified_1988 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1987_exchange_date_idx ON ohlcv_unified_1987 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1986_exchange_date_idx ON ohlcv_unified_1986 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1985_exchange_date_idx ON ohlcv_unified_1985 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1984_exchange_date_idx ON ohlcv_unified_1984 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1983_exchange_date_idx ON ohlcv_unified_1983 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1982_exchange_date_idx ON ohlcv_unified_1982 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1981_exchange_date_idx ON ohlcv_unified_1981 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1980_exchange_date_idx ON ohlcv_unified_1980 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1979_exchange_date_idx ON ohlcv_unified_1979 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1978_exchange_date_idx ON ohlcv_unified_1978 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1977_exchange_date_idx ON ohlcv_unified_1977 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1976_exchange_date_idx ON ohlcv_unified_1976 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1975_exchange_date_idx ON ohlcv_unified_1975 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1974_exchange_date_idx ON ohlcv_unified_1974 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1973_exchange_date_idx ON ohlcv_unified_1973 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1972_exchange_date_idx ON ohlcv_unified_1972 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1971_exchange_date_idx ON ohlcv_unified_1971 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1970_exchange_date_idx ON ohlcv_unified_1970 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1969_exchange_date_idx ON ohlcv_unified_1969 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1968_exchange_date_idx ON ohlcv_unified_1968 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1967_exchange_date_idx ON ohlcv_unified_1967 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1966_exchange_date_idx ON ohlcv_unified_1966 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1965_exchange_date_idx ON ohlcv_unified_1965 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1964_exchange_date_idx ON ohlcv_unified_1964 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1963_exchange_date_idx ON ohlcv_unified_1963 (exchange, date);
CREATE INDEX IF NOT EXISTS ohlcv_unified_1962_exchange_date_idx ON ohlcv_unified_1962 (exchange, date);

-- 3. Attach the partition indexes to the parent.
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_default_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2028_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2027_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2026_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2025_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2024_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2023_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2022_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2021_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2020_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2019_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2018_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2017_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2016_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2015_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2014_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2013_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2012_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2011_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2010_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2009_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2008_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2007_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2006_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2005_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2004_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2003_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2002_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2001_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_2000_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1999_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1998_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1997_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1996_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1995_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1994_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1993_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1992_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1991_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1990_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1989_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1988_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1987_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1986_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1985_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1984_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1983_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1982_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1981_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1980_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1979_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1978_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1977_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1976_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1975_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1974_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1973_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1972_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1971_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1970_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1969_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1968_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1967_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1966_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1965_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1964_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1963_exchange_date_idx;
ALTER INDEX idx_ohlcv_unified_exchange_date ATTACH PARTITION ohlcv_unified_1962_exchange_date_idx;

-- 4. Drop the redundant single-column index (lookups use the new prefix).
DROP INDEX IF EXISTS idx_ohlcv_unified_exchange;

ANALYZE ohlcv_unified;

-- Verify: both should show idx_ohlcv_unified_<year>_exchange_date
--   EXPLAIN SELECT * FROM ohlcv_unified
--    WHERE exchange = 'LSE' AND date >= '2026-11-01' AND date <= '2026-11-20'
--    ORDER BY date DESC LIMIT 2;
--   EXPLAIN SELECT count(*) FROM ohlcv_unified
--    WHERE exchange = 'LSE' AND date >= '2026-11-01' AND date <= '2026-11-20';
--
-- Rollback:
--   DROP INDEX IF EXISTS idx_ohlcv_unified_exchange_date;
--   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ohlcv_unified_exchange
--       ON ohlcv_unified (exchange);
