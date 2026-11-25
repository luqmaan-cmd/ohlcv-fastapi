# Production API Endpoint Reference

Snapshot of the live `ohlcv-api` surface (Cloud Run revision `ohlcv-api-00050-ng2`)
before the consolidated-API retirement work.

- **Paths:** 62
- **Operations:** 68 (60 `GET`, 4 `POST`, 2 `PUT`, 2 `DELETE`)
- **Auth:** every route requires `X-API-Key: <key>` or `?api_key=<key>`

---

## Unified OHLCV (new consolidated surface)

| Method | Path | What it does |
|---|---|---|
| GET | `/ohlcv/` | Paginated OHLCV for any asset class from `ohlcv_unified`, addressed by `TICKER.EXCHANGE`. Filters: ticker(s), exchange, asset type, date range, year, month, price/volume bounds; sortable and pageable. Also serves realtime quotes via `realtime=true`. |
| POST | `/ohlcv/` | Insert one OHLCV row. Returns `201` with the stored record. |
| POST | `/ohlcv/bulk/` | Insert many rows in one request. Returns `201` with `inserted` / `failed` / `errors`. |
| GET | `/ohlcv/latest/` | Realtime OHLCV straight from EODHD for the given tickers (not the stored table). |
| GET | `/ohlcv/latest_close/` | Latest stored row per ticker, searched back over the last 7 days. Optional exchange/asset-type filters. |
| GET | `/ohlcv/latest_close/{ticker}` | Latest stored row for a single ticker. |
| GET | `/ohlcv/stats/{ticker}` | Aggregate statistics for a ticker: count, earliest/latest date, average volume, min/max/average close, 52-week high/low. |
| GET | `/ohlcv/{ohlcv_id}` | Fetch a single row by internal UUID. |
| PUT | `/ohlcv/{ohlcv_id}` | Update a row by internal UUID. |
| DELETE | `/ohlcv/{ohlcv_id}` | Delete a row by internal UUID. |

---

## Reference data

| Method | Path | What it does |
|---|---|---|
| GET | `/tickers/` | Flat list of every ticker held (from the `tickers` lookup table), sorted ascending. |
| GET | `/assets/{ticker}` | Asset metadata by ticker across all asset tables: name, exchange, type, ISIN, currency, sector, industry, country. |

---

## Class-specific routes (superseded by `/ohlcv/` filters)

### UK / LSE

| Method | Path | What it does |
|---|---|---|
| GET | `/uk/` | Paginated OHLCV for UK stocks (LSE). |
| GET | `/uk/latest_close/` | Latest stored row per UK stock. |
| GET | `/uk/latest_close/{ticker}` | Latest stored row for one UK stock. |
| GET | `/uk/latest/` | Realtime EODHD quotes for UK tickers. |
| GET | `/uk/assets/` | UK asset metadata list. |

### ETFs and indices

| Method | Path | What it does |
|---|---|---|
| GET | `/etf/` | Paginated OHLCV for ETFs. |
| GET | `/etf/latest_close/` | Latest stored row per ETF. |
| GET | `/etf/latest_close/{ticker}` | Latest stored row for one ETF, enriched with metadata. |
| GET | `/etf/latest/` | Realtime EODHD quotes for ETF tickers. |
| GET | `/etf/assets/` | ETF asset metadata list. |
| GET | `/index/` | Paginated OHLCV for indices. |
| GET | `/index/latest_close/` | Latest stored row per index. |
| GET | `/index/latest_close/{ticker}` | Latest stored row for one index, enriched with metadata. |
| GET | `/index/latest/` | Realtime EODHD quotes for index tickers. |
| GET | `/index/assets/` | Index asset metadata list. |

### Foreign exchange

| Method | Path | What it does |
|---|---|---|
| GET | `/fx/` | Paginated OHLCV for FX pairs. |
| GET | `/fx/latest_close/` | Latest stored row per FX pair. |
| GET | `/fx/latest_close/{ticker}` | Latest stored row for one FX pair. |
| GET | `/fx/latest/` | Realtime EODHD quotes for FX tickers. |
| GET | `/fx/assets/` | FX asset metadata list. |

### Crypto

| Method | Path | What it does |
|---|---|---|
| GET | `/crypto/` | Paginated OHLCV for crypto assets. |
| GET | `/crypto/latest_close/` | Latest stored row per crypto asset. |
| GET | `/crypto/latest_close/{ticker}` | Latest stored row for one crypto asset. |
| GET | `/crypto/latest/` | Realtime EODHD quotes for crypto tickers. |
| GET | `/crypto/history/` | Paginated historical OHLCV for crypto assets. |
| GET | `/crypto/top100/` | Top 100 crypto assets by latest volume, descending. |
| GET | `/crypto/assets/` | Crypto asset metadata list (name, base/quote currency). |

### Government bonds

| Method | Path | What it does |
|---|---|---|
| GET | `/gov-bond/` | Paginated OHLCV for government bonds. |
| GET | `/gov-bond/latest_close/` | Latest stored row per government bond. |
| GET | `/gov-bond/latest_close/{ticker}` | Latest stored row for one government bond. |
| GET | `/gov-bond/latest/` | Realtime EODHD quotes for government bond tickers. |
| GET | `/gov-bond/assets/` | Government bond metadata list. |

### Index constituents

| Method | Path | What it does |
|---|---|---|
| GET | `/sp500/` | List S&P 500 constituents with enriched metadata (name, sector, industry, weight). **Constituents, not OHLCV.** |
| GET | `/sp500/latest/` | Latest OHLCV for S&P 500 constituents that have a mapped ticker. |
| GET | `/sp500/history/` | Paginated historical OHLCV for S&P 500 constituents. |
| GET | `/ftse100/` | Paginated OHLCV for FTSE 100 constituents. |
| GET | `/ftse100/latest/` | Latest OHLCV for FTSE 100 constituents. |
| GET | `/ftse100/constituents/` | FTSE 100 constituent list with metadata. |

### Ticker aliases

| Method | Path | What it does |
|---|---|---|
| GET | `/aliases/` | List ticker aliases mapping S&P 500 tickers to OHLCV tickers. |
| GET | `/aliases/{sp500_ticker}` | Fetch one alias by its S&P 500 ticker. |
| POST | `/aliases/` | Create an alias mapping. |
| PUT | `/aliases/{sp500_ticker}` | Update the OHLCV ticker for an alias. |
| DELETE | `/aliases/{sp500_ticker}` | Delete an alias. |

---

## Commodities (separate table, not part of the unified OHLCV surface)

| Method | Path | What it does |
|---|---|---|
| GET | `/commodity/` | Paginated OHLCV from `commodities_eod`. Filters: symbol(s), category, date range, year, month, price/volume bounds. |
| GET | `/commodity/latest/` | Latest bar per symbol, optionally filtered by symbols and/or category. |
| GET | `/commodity/symbols/` | Symbol list with name and category metadata. |
| GET | `/commodity/categories/` | Distinct commodity categories, sorted ascending. |

---

## US Treasury rates (legacy per-series routes)

| Method | Path | What it does |
|---|---|---|
| GET | `/ust/bill/` | Paginated US Treasury bill rates: tenor(s), date range, discount/coupon bounds. |
| GET | `/ust/bill/latest/` | Latest bill rate per tenor. |
| GET | `/ust/long-term/` | Paginated long-term rate records: rate type(s), date range, rate bounds. |
| GET | `/ust/long-term/latest/` | Latest long-term rate per rate type. |
| GET | `/ust/real-yield/` | Paginated real yield rates: tenor(s), date range, rate bounds. |
| GET | `/ust/real-yield/latest/` | Latest real yield per tenor. |
| GET | `/ust/yield/` | Paginated Treasury yield rates: tenor(s), date range, rate bounds. |
| GET | `/ust/yield/latest/` | Latest yield per tenor. |

---

## Utilities

| Method | Path | What it does |
|---|---|---|
| POST | `/sql/` | Run a read-only SQL query in the request body. `SELECT`/`WITH` only, whitelisted tables, 30 s timeout, 5,000-row cap. Returns `columns`, `rows`, `row_count`, `truncated`. |

---

## Notes

- `TICKER.EXCHANGE` is the addressing convention for `/ohlcv/` and the class routes; a bare ticker currently falls back to exchange `US`.
- `/sp500/` and `/ftse100/constituents/` return constituent lists, not price series.
- `/tickers/` returns bare ticker strings only, so a code listed on multiple venues is indistinguishable (11,861 such codes in 2026).
- `/ohlcv/stats/{ticker}` accepts only `start_date` / `end_date`; a `year` parameter is silently ignored.
- `/ohlcv/latest/` requires `tickers=`; `ticker=` is rejected with `422`.
- Legacy class routes read their own per-class tables (`ohlcv_data_uk`, `ohlcv_data_etf_index`, `ohlcv_data_fx`, `ohlcv_data_crypto`, `ohlcv_data_gov_bonds`, `ohlcv_data`), not `ohlcv_unified`.
