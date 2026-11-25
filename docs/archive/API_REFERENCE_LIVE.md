# API Reference — Live (Deployed)

This document describes the API **as it is currently deployed in production**, not as it exists on any development branch.

| | |
|---|---|
| Base revision | `41829f9` |
| Auth hotfix | `0831fa9` |
| Cloud Run revision | `ohlcv-api-00050-ng2` (100% traffic) |
| Captured | 2026-11-23 |
| Operations | **67** across 62 paths |

Base URL: `https://ohlcv-api-832081557693.europe-west2.run.app`

Authentication: every endpoint requires an API key, supplied either as the `api_key` query parameter or the `X-API-Key` header. If both are supplied, a match on either is accepted. A missing or invalid key returns `401 {"detail": "Invalid or missing API key"}`.

```bash
API_KEY=<your-key>
BASE=https://ohlcv-api-832081557693.europe-west2.run.app
curl -H "X-API-Key: $API_KEY" "$BASE/tickers/"
curl "$BASE/tickers/?api_key=$API_KEY"
```

---

## Which doc is authoritative?

| Document | Scope |
|---|---|
| `API_REFERENCE_LIVE.md` (this file) | **Authoritative for the deployed API.** Every live endpoint and parameter. |
| `API_REFERENCE.md` | Legacy and partial. Predates this build; covers a subset of routes and omits several. |
| `DEVELOPER.md` | Narrative walkthrough with request/response bodies. Useful for examples, not an endpoint inventory. |
| `MIGRATION.md` | Internal tracker for the `ohlcv_unified` migration. Not an API reference. |
| `API_REFERENCE_V2.md` | Describes the `TICKER.EXCHANGE` build, which exists only on the `feature/ohlcv-unified-migration` branch and is **not deployed**. |

---

## Conventions

- **Pagination.** Paginated responses return `data`, `total`, `page`, `per_page`, `total_pages`, `has_next`, `has_prev`.
- **Errors.** Body is always `{"detail": "..."}`. Status codes used: `400`, `401`, `404`, `422`, `500`, `502`, `504`.
- **Dates.** `YYYY-MM-DD` for `start_date` / `end_date`; ranges are inclusive.
- **Sorting.** `sort_by` accepts `date` (default), `volume`, `close`, `open`, `high`, `low`; `sort_order` is `asc` or `desc` (default).
- **Page size.** OHLCV list endpoints default to `1000` and cap at `5000`; asset list endpoints default to `5000`.
- **Two kinds of "latest".** `*/latest/` proxies EODHD real-time (requires `EODHD_API_TOKEN`, 15s timeout, failures surface as `404`/`502`/`504`). `*/latest_close/` reads the database.

---

## 1. Unified OHLCV (`/ohlcv/`)

Historical OHLCV rows from the `ohlcv_unified` table. **US equities only** — the query is fixed to `exchange = 'US'`, so there is no exchange or asset-type filter and non-US listings are unreachable through this endpoint.

### Parameters — `GET /ohlcv/`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | No | Single ticker, bare only (e.g. `AAPL`). |
| `tickers` | string | No | Comma-separated bare tickers (e.g. `AAPL,MSFT`). |
| `asset_isin` | string | No | Filter by a single ISIN. |
| `asset_isins` | string | No | Comma-separated ISINs. |
| `start_date` / `end_date` | date | No | Inclusive date range. |
| `year` | integer | No | 1900-2100. |
| `month` | integer | No | 1-12. |
| `open_min` / `open_max` | number | No | Open price range. |
| `close_min` / `close_max` | number | No | Close price range. |
| `volume_min` / `volume_max` | integer | No | Volume range. |
| `sort_by` | string | No | `date` (default), `volume`, `close`, `open`, `high`, `low`. |
| `sort_order` | string | No | `asc` or `desc` (default). |
| `page` | integer | No | Default `1`. |
| `per_page` | integer | No | Default `1000`, max `5000`. |

### Historical rows

```bash
curl "$BASE/ohlcv/?tickers=AAPL,MSFT&start_date=2026-11-01&end_date=2026-11-20&api_key=$API_KEY"
curl "$BASE/ohlcv/?ticker=AAPL&year=2026&sort_by=close&sort_order=desc&per_page=500&api_key=$API_KEY"
```

### Latest close — single ticker

Returns the newest row for one ticker. `{ticker}` is a path parameter.

```bash
curl "$BASE/ohlcv/latest_close/AAPL?api_key=$API_KEY"
```

### Latest close — batch

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tickers` | string | No | Comma-separated tickers. If omitted, returns the latest row for every ticker in the lookup table. |

```bash
curl "$BASE/ohlcv/latest_close/?tickers=AAPL,MSFT&api_key=$API_KEY"
curl "$BASE/ohlcv/latest_close/?api_key=$API_KEY"
```

### Statistics — `/ohlcv/stats/{ticker}`

Returns `count`, `earliest_date`, `latest_date`, `avg_volume`, `min_close`, `max_close`, `avg_close`, `fifty_two_week_high`, `fifty_two_week_low`. Takes **no query parameters**.

```bash
curl "$BASE/ohlcv/stats/AAPL?api_key=$API_KEY"
```

### Real-time quote (EODHD)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tickers` | string | Yes | Comma-separated tickers. |

The ticker must also exist in the `assets` table, otherwise `404 No asset found with tickers: ...`.

```bash
curl "$BASE/ohlcv/latest/?tickers=AAPL,MSFT&api_key=$API_KEY"
```

### Create, update, delete

`POST /ohlcv/` accepts `ticker` and `date` (both required) plus optional `open`, `high`, `low`, `close`, `adjusted_close`, `volume`, `asset_isin`, `instrument_id`. `PUT /ohlcv/{ohlcv_id}` takes the same fields, all optional. `DELETE /ohlcv/{ohlcv_id}` returns `204`.

```bash
curl -X POST "$BASE/ohlcv/?api_key=$API_KEY" -H "Content-Type: application/json" \
  -d '{"ticker":"AAPL","date":"2026-11-20","close":342.37,"volume":44703806}'

curl -X PUT "$BASE/ohlcv/<ohlcv_id>?api_key=$API_KEY" -H "Content-Type: application/json" \
  -d '{"close":343.00}'

curl -X DELETE "$BASE/ohlcv/<ohlcv_id>?api_key=$API_KEY"
```

### Bulk insert

`POST /ohlcv/bulk/` accepts `{"records": [ ... ]}` where each record has the same shape as `POST /ohlcv/`. Returns `inserted`, `failed`, `errors`.

```bash
curl -X POST "$BASE/ohlcv/bulk/?api_key=$API_KEY" -H "Content-Type: application/json" \
  -d '{"records":[{"ticker":"AAPL","date":"2026-11-20","close":342.37}]}'
```

---

## 2. US Equities & S&P 500

S&P 500 constituents, their price history, and the full ticker list.

### List S&P 500 constituents

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sector` | string | No | Filter by GIC sector (e.g. `Information Technology`). |
| `is_active` | boolean | No | Filter by active status. |
| `page` | integer | No | Default `1`. |
| `per_page` | integer | No | Default `1000`, max `5000`. |

```bash
Returns `ticker`, `name`, `sector`, `industry`, `weight`, `is_active`, `isin`, `gic_sector`, `description` and `country`. This is the **only** endpoint on the deployed build that exposes index weights and sector metadata.

```bash
curl "$BASE/sp500/?sector=Information%20Technology&is_active=true&api_key=$API_KEY"
```

### S&P 500 history

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tickers` | string | No | Comma-separated tickers (e.g. `AAPL,MSFT`). If omitted, returns all constituents. |
| `start_date` / `end_date` | date | No | Inclusive date range. |
| `year` | integer | No | Filter by year. |
| `month` | integer | No | 1-12. |
| `sort_by` | string | No | `date` (default), `volume`, `close`, `open`, `high`, `low`. |
| `sort_order` | string | No | `asc` or `desc` (default). |
| `page` | integer | No | Default `1`. |
| `per_page` | integer | No | Default `1000`, max `5000`. |

```bash
curl "$BASE/sp500/history/?tickers=AAPL,MSFT&start_date=2026-11-01&end_date=2026-11-20&api_key=$API_KEY"
```

### S&P 500 latest

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tickers` | string | No | Comma-separated tickers. If omitted, returns latest for all constituents. |

```bash
curl "$BASE/sp500/latest/?tickers=AAPL,MSFT&api_key=$API_KEY"
```

### All supported tickers

Returns a flat JSON array of every ticker present in `ohlcv_unified`. No parameters.

```bash
curl "$BASE/tickers/?api_key=$API_KEY"
```

---

## 3. UK Stocks & FTSE 100

LSE-listed equities and the FTSE 100 constituent list, served from `ohlcv_data_uk`, `uk_assets` and `ftse100_constituents`.

### UK OHLCV

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | No | Single ticker (e.g. `AZN`). |
| `tickers` | string | No | Comma-separated tickers (e.g. `AZN,SHEL,HSBA`). |
| `sector` / `industry` | string | No | Filter by sector or industry. |
| `start_date` / `end_date` | date | No | Inclusive date range. |
| `year` | integer | No | Filter by year. |
| `month` | integer | No | 1-12. |
| `open_min` / `open_max` | number | No | Open price range. |
| `close_min` / `close_max` | number | No | Close price range. |
| `volume_min` / `volume_max` | integer | No | Volume range. |
| `sort_by` | string | No | `date` (default), `volume`, `close`, `open`, `high`, `low`. |
| `sort_order` | string | No | `asc` or `desc` (default). |
| `page` | integer | No | Default `1`. |
| `per_page` | integer | No | Default `1000`, max `5000`. |

```bash
curl "$BASE/uk/?tickers=AZN,SHEL&start_date=2026-10-01&end_date=2026-11-20&api_key=$API_KEY"
```

### UK assets

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sector` / `industry` / `type` | string | No | Metadata filters. |
| `search` | string | No | Case-insensitive match on code or name. |
| `sort` | string | No | `code` (default) or `name`. |
| `order` | string | No | `asc` (default) or `desc`. |
| `page` | integer | No | Default `1`. |
| `per_page` | integer | No | Default `5000`. |

```bash
curl "$BASE/uk/assets/?search=astra&api_key=$API_KEY"
```

### UK latest (EODHD real-time)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tickers` | string | Yes | Comma-separated tickers. |

```bash
curl "$BASE/uk/latest/?tickers=AZN,SHEL&api_key=$API_KEY"
```

### UK latest close (database)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tickers` | string | No | Comma-separated tickers. If omitted, returns latest for all. |
| `sector` / `industry` | string | No | Metadata filters. |

```bash
curl "$BASE/uk/latest_close/?tickers=AZN&api_key=$API_KEY"
curl "$BASE/uk/latest_close/AZN?api_key=$API_KEY"
```

### FTSE 100 OHLCV

Same parameter set as `/uk/`, plus `sector` and `industry`.

```bash
curl "$BASE/ftse100/?tickers=AZN,SHEL&start_date=2026-10-01&end_date=2026-11-20&api_key=$API_KEY"
```

### FTSE 100 constituents

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sector` / `industry` | string | No | Metadata filters. |
| `search` | string | No | Case-insensitive match on code or name. |
| `sort` / `order` | string | No | `code`/`name`, `asc`/`desc`. |
| `page` / `per_page` | integer | No | Defaults `1` / `5000`. |

Returns `code`, `name`, `sector`, `industry`, `isin` and `currency` for each constituent. `isin` and `currency` are currently `null` for every row; `sector` and `industry` are populated.

```bash
curl "$BASE/ftse100/constituents/?sector=Healthcare&api_key=$API_KEY"
```

### FTSE 100 latest

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tickers` | string | No | Comma-separated tickers. |
| `sector` / `industry` | string | No | Metadata filters. |

```bash
curl "$BASE/ftse100/latest/?tickers=AZN&api_key=$API_KEY"
```

---

## 4. ETFs & Indices

Both share the `ohlcv_data_etf_index` and `etf_index_assets` tables, so their parameter sets are identical.

### OHLCV — `/etf/` and `/index/`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | No | Single ticker (e.g. `SPY` or `GSPC`). |
| `tickers` | string | No | Comma-separated tickers. |
| `start_date` / `end_date` | date | No | Inclusive date range. |
| `year` / `month` | integer | No | Period filters. |
| `open_min` / `open_max` | number | No | Open price range. |
| `close_min` / `close_max` | number | No | Close price range. |
| `volume_min` / `volume_max` | integer | No | Volume range. |
| `sort_by` / `sort_order` | string | No | `date`/`asc`-`desc` defaults. |
| `page` / `per_page` | integer | No | Defaults `1` / `1000`. |

```bash
curl "$BASE/etf/?tickers=SPY,QQQ&start_date=2026-10-01&end_date=2026-11-20&api_key=$API_KEY"
curl "$BASE/index/?tickers=GSPC,DJI&start_date=2026-10-01&end_date=2026-11-20&api_key=$API_KEY"
```

### Assets — `/etf/assets/` and `/index/assets/`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `search` | string | No | Case-insensitive match on code or name. |
| `sort` / `order` | string | No | `code`/`name`, `asc`/`desc`. |
| `page` / `per_page` | integer | No | Defaults `1` / `5000`. |

```bash
Returns `code`, `name`, `exchange`, `type`, `isin` and `currency`. These lists carry **no index weights and no sector metadata**.

```bash
curl "$BASE/etf/assets/?search=spy&api_key=$API_KEY"
curl "$BASE/index/assets/?page=2&per_page=100&api_key=$API_KEY"
```

### Latest (EODHD real-time)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tickers` | string | Yes | Comma-separated tickers. |

```bash
curl "$BASE/etf/latest/?tickers=SPY&api_key=$API_KEY"
curl "$BASE/index/latest/?tickers=GSPC&api_key=$API_KEY"
```

### Latest close (database)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tickers` | string | No | Comma-separated tickers. If omitted, returns latest for all. |

```bash
curl "$BASE/etf/latest_close/?tickers=SPY,QQQ&api_key=$API_KEY"
curl "$BASE/etf/latest_close/SPY?api_key=$API_KEY"
curl "$BASE/index/latest_close/?tickers=GSPC&api_key=$API_KEY"
curl "$BASE/index/latest_close/GSPC?api_key=$API_KEY"
```

---

## 5. Government Bonds

### OHLCV — `/gov-bond/`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | No | Single bond ticker (e.g. `UK10Y`). |
| `tickers` | string | No | Comma-separated tickers (e.g. `UK10Y,US10Y,DE10Y`). |
| `country` | string | No | Single country code (e.g. `US`). |
| `countries` | string | No | Comma-separated country codes (e.g. `US,DE,JP`). |
| `start_date` / `end_date` | date | No | Inclusive date range. |
| `year` / `month` | integer | No | Period filters. |
| `open_min` / `open_max` | number | No | Open price range. |
| `close_min` / `close_max` | number | No | Close price range. |
| `volume_min` / `volume_max` | integer | No | Volume range. |
| `sort_by` / `sort_order` | string | No | `date`/`asc`-`desc` defaults. |
| `page` / `per_page` | integer | No | Defaults `1` / `1000`. |

```bash
curl "$BASE/gov-bond/?countries=US,DE&start_date=2026-10-01&end_date=2026-11-20&api_key=$API_KEY"
```

### Assets — `/gov-bond/assets/`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `country` | string | No | Filter by country. |
| `type` | string | No | Filter by bond type. |
| `search` | string | No | Case-insensitive match on code or name. |
| `sort` / `order` | string | No | `code`/`name`, `asc`/`desc`. |
| `page` / `per_page` | integer | No | Defaults `1` / `5000`. |

```bash
Returns `code`, `name`, `exchange`, `type`, `currency` and `country`.

```bash
curl "$BASE/gov-bond/assets/?country=US&api_key=$API_KEY"
```

### Latest (EODHD real-time)

```bash
curl "$BASE/gov-bond/latest/?tickers=US10Y,UK10Y&api_key=$API_KEY"
```

### Latest close (database)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tickers` | string | No | Comma-separated tickers. |
| `country` / `countries` | string | No | Country filters. |

```bash
curl "$BASE/gov-bond/latest_close/?tickers=US10Y&api_key=$API_KEY"
curl "$BASE/gov-bond/latest_close/US10Y?api_key=$API_KEY"
```

---

## 6. Foreign Exchange

### OHLCV — `/fx/`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | No | Single pair (e.g. `EURUSD`). |
| `tickers` | string | No | Comma-separated pairs (e.g. `EURUSD,GBPUSD`). |
| `base_currency` / `quote_currency` | string | No | Currency filters. |
| `start_date` / `end_date` | date | No | Inclusive date range. |
| `year` / `month` | integer | No | Period filters. |
| `open_min` / `open_max` | number | No | Open price range. |
| `close_min` / `close_max` | number | No | Close price range. |
| `volume_min` / `volume_max` | integer | No | Volume range. |
| `sort_by` / `sort_order` | string | No | `date`/`asc`-`desc` defaults. |
| `page` / `per_page` | integer | No | Defaults `1` / `1000`. |

```bash
curl "$BASE/fx/?tickers=EURUSD,GBPUSD&start_date=2026-10-01&end_date=2026-11-20&api_key=$API_KEY"
```

### Assets — `/fx/assets/`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `base_currency` / `quote_currency` | string | No | Currency filters. |
| `type` | string | No | Asset type filter. |
| `search` | string | No | Case-insensitive match on code or name. |
| `sort` / `order` | string | No | `code`/`name`, `asc`/`desc`. |
| `page` / `per_page` | integer | No | Defaults `1` / `5000`. |

```bash
curl "$BASE/fx/assets/?base_currency=EUR&api_key=$API_KEY"
```

### Latest (EODHD real-time)

```bash
curl "$BASE/fx/latest/?tickers=EURUSD,GBPUSD&api_key=$API_KEY"
```

### Latest close (database)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tickers` | string | No | Comma-separated pairs. |
| `base_currency` / `quote_currency` | string | No | Currency filters. |

```bash
curl "$BASE/fx/latest_close/?tickers=EURUSD&api_key=$API_KEY"
curl "$BASE/fx/latest_close/EURUSD?api_key=$API_KEY"
```

---

## 7. Crypto

### OHLCV — `/crypto/`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | No | Single pair (e.g. `BTC-USD`). |
| `tickers` | string | No | Comma-separated pairs. |
| `base_currency` / `quote_currency` | string | No | Currency filters (e.g. `BTC`, `USD`). |
| `start_date` / `end_date` | date | No | Inclusive date range. |
| `year` / `month` | integer | No | Period filters. |
| `open_min` / `open_max` | number | No | Open price range. |
| `close_min` / `close_max` | number | No | Close price range. |
| `volume_min` / `volume_max` | integer | No | Volume range. |
| `sort_by` / `sort_order` | string | No | `date`/`asc`-`desc` defaults. |
| `page` / `per_page` | integer | No | Defaults `1` / `1000`. |

```bash
curl "$BASE/crypto/?tickers=BTC-USD,ETH-USD&start_date=2026-10-01&end_date=2026-11-20&api_key=$API_KEY"
```

### History — `/crypto/history/`

Same filters as `/crypto/` minus the price-range filters: `tickers`, `base_currency`, `quote_currency`, `start_date`, `end_date`, `year`, `month`, `sort_by`, `sort_order`, `page`, `per_page`.

```bash
curl "$BASE/crypto/history/?tickers=BTC-USD&year=2026&api_key=$API_KEY"
```

### Assets — `/crypto/assets/`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `base_currency` / `quote_currency` | string | No | Currency filters. |
| `type` | string | No | Asset type filter. |
| `search` | string | No | Case-insensitive match on code or name. |
| `sort` / `order` | string | No | `code`/`name`, `asc`/`desc`. |
| `page` / `per_page` | integer | No | Defaults `1` / `5000`. |

```bash
curl "$BASE/crypto/assets/?search=bitcoin&api_key=$API_KEY"
```

### Top 100

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `base_currency` / `quote_currency` | string | No | Currency filters (e.g. `USD`). |

```bash
curl "$BASE/crypto/top100/?quote_currency=USD&api_key=$API_KEY"
```

### Latest (EODHD real-time)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tickers` | string | Yes | Comma-separated pairs. |

```bash
curl "$BASE/crypto/latest/?tickers=BTC-USD,ETH-USD&api_key=$API_KEY"
```

### Latest close (database)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tickers` | string | No | Comma-separated pairs. |
| `base_currency` / `quote_currency` | string | No | Currency filters. |

```bash
curl "$BASE/crypto/latest_close/?tickers=BTC-USD&api_key=$API_KEY"
curl "$BASE/crypto/latest_close/BTC-USD?api_key=$API_KEY"
```

---

## 8. Commodities

Served from `commodities_eod`, which is **not** part of `ohlcv_unified`. Symbols use commodity codes (e.g. `LGOc3`, `NICKEL`).

### OHLCV — `/commodity/`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | string | No | Single symbol (e.g. `LGOc3`). |
| `symbols` | string | No | Comma-separated symbols. |
| `category` | string | No | Filter by category (e.g. `Energy`, `Metals`). |
| `start_date` / `end_date` | date | No | Inclusive date range. |
| `year` / `month` | integer | No | Period filters. |
| `open_min` / `open_max` | number | No | Open price range. |
| `close_min` / `close_max` | number | No | Close price range. |
| `volume_min` / `volume_max` | integer | No | Volume range. |
| `sort_by` / `sort_order` | string | No | `date`/`asc`-`desc` defaults. |
| `page` / `per_page` | integer | No | Defaults `1` / `1000`. |

```bash
curl "$BASE/commodity/?symbols=LGOc3,NICKEL&start_date=2026-10-01&end_date=2026-11-20&api_key=$API_KEY"
```

### Categories — `/commodity/categories/`

No parameters.

```bash
curl "$BASE/commodity/categories/?api_key=$API_KEY"
```

### Latest — `/commodity/latest/`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbols` | string | No | Comma-separated symbols. If omitted, returns latest for all. |
| `category` | string | No | Filter by category. |

```bash
curl "$BASE/commodity/latest/?symbols=LGOc3,NICKEL&api_key=$API_KEY"
```

### Symbols — `/commodity/symbols/`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | No | Filter by category. |

```bash
curl "$BASE/commodity/symbols/?api_key=$API_KEY"
```

---

## 9. US Treasury Rates

Four rate families, each with a paginated history endpoint and a latest endpoint, served from the `ust_*_rates` tables.

### Shared pagination parameters

All four `/*/` endpoints accept `start_date`, `end_date`, `sort_by` (default `date`), `sort_order` (default `desc`), `page` (default `1`) and `per_page` (default `1000`). Each adds its own identifier and value-range filters:

| Endpoint | Identifiers | Value range |
|---|---|---|
| `/ust/bill/` | `tenor`, `tenors` (e.g. `4WK,13WK,26WK,52WK`) | `discount_min`/`discount_max`, `coupon_min`/`coupon_max` |
| `/ust/long-term/` | `rate_type`, `rate_types` (e.g. `BC_20year,Over_10_Years`) | `rate_min`/`rate_max` |
| `/ust/real-yield/` | `tenor`, `tenors` | `rate_min`/`rate_max` |
| `/ust/yield/` | `tenor`, `tenors` (e.g. `2Y,5Y,10Y,30Y`) | `rate_min`/`rate_max` |

### Latest parameters

| Endpoint | Parameter |
|---|---|
| `/ust/bill/latest/` | `tenors` |
| `/ust/long-term/latest/` | `rate_types` |
| `/ust/real-yield/latest/` | `tenors` |
| `/ust/yield/latest/` | `tenors` |

```bash
curl "$BASE/ust/bill/?tenors=4WK,13WK&start_date=2026-10-01&api_key=$API_KEY"
curl "$BASE/ust/long-term/?rate_types=BC_20year&api_key=$API_KEY"
curl "$BASE/ust/real-yield/?tenors=10Y&api_key=$API_KEY"
curl "$BASE/ust/yield/?tenors=2Y,10Y,30Y&api_key=$API_KEY"

curl "$BASE/ust/bill/latest/?tenors=13WK&api_key=$API_KEY"
curl "$BASE/ust/long-term/latest/?rate_types=BC_20year&api_key=$API_KEY"
curl "$BASE/ust/real-yield/latest/?tenors=10Y&api_key=$API_KEY"
curl "$BASE/ust/yield/latest/?tenors=10Y&api_key=$API_KEY"
```

---

## 10. Asset Lookup

Looks up asset metadata by ticker across the unified `assets` table and the per-class asset tables.

### Parameters — `GET /assets/{ticker}`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | Yes | Path parameter (e.g. `AAPL`, `BTC-USD`, `SPY`). |
| `exchange` | string | No | Filter by exchange to disambiguate (e.g. `US`, `LSE`, `AU`). |

The response is a list, so a code listed on several venues can return several entries. Note that `assets.exchange` is **not** returned verbatim on this build: rows sourced from the `assets` table are hardcoded to `exchange: "US"`, while per-class tables return their own stored exchange (e.g. `LSE` for UK stocks).

Verified examples:

```bash
curl "$BASE/assets/ANT?api_key=$API_KEY"
curl "$BASE/assets/IWM?api_key=$API_KEY"
curl "$BASE/assets/SDR?exchange=LSE&api_key=$API_KEY"
```

---

## 11. Ticker Aliases

Maps an S&P 500 ticker to the ticker used in OHLCV data.

### List aliases — `GET /aliases/`

No parameters.

```bash
curl "$BASE/aliases/?api_key=$API_KEY"
```

### Get one alias — `GET /aliases/{sp500_ticker}`

```bash
curl "$BASE/aliases/BRK.B?api_key=$API_KEY"
```

### Create — `POST /aliases/`

Body: `sp500_ticker` and `ohlcv_ticker` (both required).

```bash
curl -X POST "$BASE/aliases/?api_key=$API_KEY" -H "Content-Type: application/json" \
  -d '{"sp500_ticker":"BRK.B","ohlcv_ticker":"BRK-B"}'
```

### Update — `PUT /aliases/{sp500_ticker}`

Body: `ohlcv_ticker` (required).

```bash
curl -X PUT "$BASE/aliases/BRK.B?api_key=$API_KEY" -H "Content-Type: application/json" \
  -d '{"ohlcv_ticker":"BRK-B"}'
```

### Delete — `DELETE /aliases/{sp500_ticker}`

```bash
curl -X DELETE "$BASE/aliases/BRK.B?api_key=$API_KEY"
```

---

## 12. Read-only SQL

### `POST /sql/`

Executes a single read-only statement and returns column names plus rows.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | A `SELECT` or `WITH` statement. |

Guardrails: only `SELECT`/`WITH` is permitted, at most 5000 rows are returned, queries time out after 30 seconds, and only whitelisted tables are allowed. **`ohlcv_unified` is not in the whitelist on this build** — querying it returns `400 Table(s) not allowed`. Allowed tables: `assets`, `commodities_eod`, `crypto_assets`, `etf_index_assets`, `ftse100_constituents`, `fx_assets`, `gov_bond_assets`, `ohlcv_data`, `ohlcv_data_crypto`, `ohlcv_data_etf_index`, `ohlcv_data_fx`, `ohlcv_data_gov_bonds`, `ohlcv_data_uk`, `sp500_constituents`, `ticker_aliases`, `tickers`, `uk_assets`, `ust_bill_rates`, `ust_long_term_rates`, `ust_real_yield_rates`, `ust_yield_rates`.

```bash
curl -X POST "$BASE/sql/?api_key=$API_KEY" -H "Content-Type: application/json" \
  -d '{"query":"SELECT code, exchange, name FROM assets WHERE code = '"'"'AAPL'"'"'"}'
```

---

## Appendix A — Endpoint index

All 67 deployed operations. Generated from the live `/openapi.json`.

| Method | Path | Path params | Query params | Response schema |
|---|---|---|---|---|
| `GET` | `/aliases/` | — | — | TickerAliasListResponse |
| `POST` | `/aliases/` | — | — | — |
| `GET` | `/aliases/{sp500_ticker}` | `sp500_ticker` | — | TickerAliasResponse |
| `PUT` | `/aliases/{sp500_ticker}` | `sp500_ticker` | — | TickerAliasResponse |
| `DELETE` | `/aliases/{sp500_ticker}` | `sp500_ticker` | — | — |
| `GET` | `/assets/{ticker}` | `ticker` | `exchange` | AssetLookupResponse |
| `GET` | `/commodity/` | — | `symbol`, `symbols`, `category`, `start_date`, `end_date`, `year`, `month`, `open_min`, `open_max`, `close_min`, `close_max`, `volume_min`, `volume_max`, `sort_by`, `sort_order`, `page`, `per_page` | CommodityPaginatedResponse |
| `GET` | `/commodity/categories/` | — | — | CommodityCategoryResponse |
| `GET` | `/commodity/latest/` | — | `symbols`, `category` | CommodityLatestResponse |
| `GET` | `/commodity/symbols/` | — | `category` | CommoditySymbolResponse |
| `GET` | `/crypto/` | — | `ticker`, `tickers`, `base_currency`, `quote_currency`, `start_date`, `end_date`, `year`, `month`, `open_min`, `open_max`, `close_min`, `close_max`, `volume_min`, `volume_max`, `sort_by`, `sort_order`, `page`, `per_page` | CryptoPaginatedResponse |
| `GET` | `/crypto/assets/` | — | `base_currency`, `quote_currency`, `type`, `search`, `sort`, `order`, `page`, `per_page` | CryptoAssetResponse |
| `GET` | `/crypto/history/` | — | `tickers`, `base_currency`, `quote_currency`, `start_date`, `end_date`, `year`, `month`, `sort_by`, `sort_order`, `page`, `per_page` | CryptoHistoryPaginatedResponse |
| `GET` | `/crypto/latest/` | — | `tickers` | RealTimeOhlcvResponse |
| `GET` | `/crypto/latest_close/` | — | `tickers`, `base_currency`, `quote_currency` | CryptoLatestResponse |
| `GET` | `/crypto/latest_close/{ticker}` | `ticker` | — | CryptoLatestItem |
| `GET` | `/crypto/top100/` | — | `base_currency`, `quote_currency` | CryptoTop100Response |
| `GET` | `/etf/` | — | `ticker`, `tickers`, `start_date`, `end_date`, `year`, `month`, `open_min`, `open_max`, `close_min`, `close_max`, `volume_min`, `volume_max`, `sort_by`, `sort_order`, `page`, `per_page` | EtfIndexPaginatedResponse |
| `GET` | `/etf/assets/` | — | `search`, `sort`, `order`, `page`, `per_page` | EtfIndexAssetListResponse |
| `GET` | `/etf/latest/` | — | `tickers` | RealTimeOhlcvResponse |
| `GET` | `/etf/latest_close/` | — | `tickers` | EtfIndexLatestResponse |
| `GET` | `/etf/latest_close/{ticker}` | `ticker` | — | EtfIndexLatestItem |
| `GET` | `/ftse100/` | — | `ticker`, `tickers`, `sector`, `industry`, `start_date`, `end_date`, `year`, `month`, `open_min`, `open_max`, `close_min`, `close_max`, `volume_min`, `volume_max`, `sort_by`, `sort_order`, `page`, `per_page` | Ftse100PaginatedResponse |
| `GET` | `/ftse100/constituents/` | — | `sector`, `industry`, `search`, `sort`, `order`, `page`, `per_page` | Ftse100ConstituentResponse |
| `GET` | `/ftse100/latest/` | — | `tickers`, `sector`, `industry` | Ftse100LatestResponse |
| `GET` | `/fx/` | — | `ticker`, `tickers`, `base_currency`, `quote_currency`, `start_date`, `end_date`, `year`, `month`, `open_min`, `open_max`, `close_min`, `close_max`, `volume_min`, `volume_max`, `sort_by`, `sort_order`, `page`, `per_page` | FxPaginatedResponse |
| `GET` | `/fx/assets/` | — | `base_currency`, `quote_currency`, `type`, `search`, `sort`, `order`, `page`, `per_page` | FxAssetResponse |
| `GET` | `/fx/latest/` | — | `tickers` | RealTimeOhlcvResponse |
| `GET` | `/fx/latest_close/` | — | `tickers`, `base_currency`, `quote_currency` | FxLatestResponse |
| `GET` | `/fx/latest_close/{ticker}` | `ticker` | — | FxLatestItem |
| `GET` | `/gov-bond/` | — | `ticker`, `tickers`, `country`, `countries`, `start_date`, `end_date`, `year`, `month`, `open_min`, `open_max`, `close_min`, `close_max`, `volume_min`, `volume_max`, `sort_by`, `sort_order`, `page`, `per_page` | GovBondPaginatedResponse |
| `GET` | `/gov-bond/assets/` | — | `country`, `type`, `search`, `sort`, `order`, `page`, `per_page` | GovBondAssetResponse |
| `GET` | `/gov-bond/latest/` | — | `tickers` | RealTimeOhlcvResponse |
| `GET` | `/gov-bond/latest_close/` | — | `tickers`, `country`, `countries` | GovBondLatestResponse |
| `GET` | `/gov-bond/latest_close/{ticker}` | `ticker` | — | GovBondLatestItem |
| `GET` | `/index/` | — | `ticker`, `tickers`, `start_date`, `end_date`, `year`, `month`, `open_min`, `open_max`, `close_min`, `close_max`, `volume_min`, `volume_max`, `sort_by`, `sort_order`, `page`, `per_page` | EtfIndexPaginatedResponse |
| `GET` | `/index/assets/` | — | `search`, `sort`, `order`, `page`, `per_page` | EtfIndexAssetListResponse |
| `GET` | `/index/latest/` | — | `tickers` | RealTimeOhlcvResponse |
| `GET` | `/index/latest_close/` | — | `tickers` | EtfIndexLatestResponse |
| `GET` | `/index/latest_close/{ticker}` | `ticker` | — | EtfIndexLatestItem |
| `GET` | `/ohlcv/` | — | `ticker`, `tickers`, `asset_isin`, `asset_isins`, `start_date`, `end_date`, `year`, `month`, `open_min`, `open_max`, `close_min`, `close_max`, `volume_min`, `volume_max`, `sort_by`, `sort_order`, `page`, `per_page` | PaginatedResponse |
| `POST` | `/ohlcv/` | — | — | — |
| `POST` | `/ohlcv/bulk/` | — | — | — |
| `GET` | `/ohlcv/latest/` | — | `tickers` | RealTimeOhlcvResponse |
| `GET` | `/ohlcv/latest_close/` | — | `tickers` | BatchLatestResponse |
| `GET` | `/ohlcv/latest_close/{ticker}` | `ticker` | — | OhlcvDataResponse |
| `GET` | `/ohlcv/stats/{ticker}` | `ticker` | — | OhlcvStatsResponse |
| `PUT` | `/ohlcv/{ohlcv_id}` | `ohlcv_id` | — | OhlcvDataResponse |
| `DELETE` | `/ohlcv/{ohlcv_id}` | `ohlcv_id` | — | — |
| `GET` | `/sp500/` | — | `sector`, `is_active`, `page`, `per_page` | SP500ListResponse |
| `GET` | `/sp500/history/` | — | `tickers`, `start_date`, `end_date`, `year`, `month`, `sort_by`, `sort_order`, `page`, `per_page` | SP500HistoryResponse |
| `GET` | `/sp500/latest/` | — | `tickers` | SP500LatestResponse |
| `POST` | `/sql/` | — | — | SqlQueryResponse |
| `GET` | `/tickers/` | — | — | array |
| `GET` | `/uk/` | — | `ticker`, `tickers`, `sector`, `industry`, `start_date`, `end_date`, `year`, `month`, `open_min`, `open_max`, `close_min`, `close_max`, `volume_min`, `volume_max`, `sort_by`, `sort_order`, `page`, `per_page` | UkPaginatedResponse |
| `GET` | `/uk/assets/` | — | `sector`, `industry`, `type`, `search`, `sort`, `order`, `page`, `per_page` | UkAssetResponse |
| `GET` | `/uk/latest/` | — | `tickers` | RealTimeOhlcvResponse |
| `GET` | `/uk/latest_close/` | — | `tickers`, `sector`, `industry` | UkLatestResponse |
| `GET` | `/uk/latest_close/{ticker}` | `ticker` | — | UkLatestItem |
| `GET` | `/ust/bill/` | — | `tenor`, `tenors`, `start_date`, `end_date`, `discount_min`, `discount_max`, `coupon_min`, `coupon_max`, `sort_by`, `sort_order`, `page`, `per_page` | UstBillPaginatedResponse |
| `GET` | `/ust/bill/latest/` | — | `tenors` | UstBillLatestResponse |
| `GET` | `/ust/long-term/` | — | `rate_type`, `rate_types`, `start_date`, `end_date`, `rate_min`, `rate_max`, `sort_by`, `sort_order`, `page`, `per_page` | UstLongTermPaginatedResponse |
| `GET` | `/ust/long-term/latest/` | — | `rate_types` | UstLongTermLatestResponse |
| `GET` | `/ust/real-yield/` | — | `tenor`, `tenors`, `start_date`, `end_date`, `rate_min`, `rate_max`, `sort_by`, `sort_order`, `page`, `per_page` | UstRealYieldPaginatedResponse |
| `GET` | `/ust/real-yield/latest/` | — | `tenors` | UstRealYieldLatestResponse |
| `GET` | `/ust/yield/` | — | `tenor`, `tenors`, `start_date`, `end_date`, `rate_min`, `rate_max`, `sort_by`, `sort_order`, `page`, `per_page` | UstYieldPaginatedResponse |
| `GET` | `/ust/yield/latest/` | — | `tenors` | UstYieldLatestResponse |

---

## Appendix B — Live limitations

These are properties of the deployed build (`41829f9`). They are documented here so consumers are not surprised; several are fixed by the undeployed `TICKER.EXCHANGE` work described in Appendix C.

1. **`/ohlcv/` is US-only.** The handler hardcodes `OhlcvUnified.exchange == 'US'` (`main.py`, `get_ohlcv_data`). There is no `exchange` or `asset_type` query parameter, so non-US rows that exist in `ohlcv_unified` — for example `TMV` on `XETRA` — cannot be retrieved through this endpoint.
2. **Bare tickers only.** `TICKER.EXCHANGE` syntax is not supported. `AAPL.US` is treated as a literal ticker and returns `404 {"detail": "No OHLCV data found for ticker: AAPL.US"}`.
3. **No `exchange` / `asset_type` filters** on `/ohlcv/`, `/ohlcv/latest_close/` or `/ohlcv/stats/{ticker}`. `/ohlcv/latest_close/` accepts only `tickers`, and `/ohlcv/stats/{ticker}` accepts no query parameters at all (so no `start_date`/`end_date`).
4. **`OhlcvDataResponse` has no `exchange` or `asset_type` field.** Those fields are added by the undeployed build.
5. **`/sql/` rejects `ohlcv_unified`.** The table whitelist on this build excludes it, so `SELECT ... FROM ohlcv_unified` returns `400 Table(s) not allowed`.
6. **`/assets/{ticker}` returns stored values verbatim**, with no normalisation. A code can map to several listings, and the `exchange` shown is the stored one — e.g. `ANT` reports `exchange: "AU"` and `currencyCode: "AUD"`.
7. **`*/latest/` depends on the `assets` table.** Before calling EODHD it checks that every requested code exists in `assets`, returning `404 No asset found with tickers: ...` otherwise.
8. **`*/latest/` is an external dependency.** EODHD requires `EODHD_API_TOKEN`; a 15-second timeout yields `504`, upstream failures yield `502`, and an empty/`NA` quote yields `404`.
9. **Bulk `/ohlcv/latest_close/` is driven by the `tickers` lookup table**, so a ticker absent from that table is omitted from the bulk response even when its price rows exist.
10. **Zero-volume rows are not filtered.** Placeholder rows (open = high = low = close, `volume` 0) are returned like any other row and are included in `/ohlcv/stats/{ticker}` aggregates.
12. **Index weights and sector metadata exist only on `/sp500/`.** `/index/assets/` and `/etf/assets/` return `code`, `name`, `exchange`, `type`, `isin`, `currency` with no weight or sector. FTSE 100 exposes `sector`/`industry` but no weight, and its `isin`/`currency` are `null` for every row.

11. **`/assets/{ticker}` has two known defects on this build.** Codes with several listings (e.g. `AAPL`, `MSFT`, `TMV`) can return `500 Internal Server Error` instead of a list, and the `exchange` filter is compared against `assets.countryName` rather than the exchange, so `?exchange=US` does not match US listings and returns `404`. Codes with few or single rows (`ANT`, `IWM`) and per-class exchanges (`SDR?exchange=LSE`) work normally.

---

## Appendix C — Not yet deployed

The `feature/ohlcv-unified-migration` branch carries four commits on top of this build (`311068e`, `39aa866`, `fb77197`, `145520f`) that add `TICKER.EXCHANGE` parsing, `exchange` and `asset_type` parameters on the `/ohlcv/` endpoints, `start_date`/`end_date` on `/ohlcv/stats/{ticker}`, `exchange` and `asset_type` fields on `OhlcvDataResponse`, multi-table asset lookup, and `ohlcv_unified` in the `/sql/` whitelist. `API_REFERENCE_V2.md` documents that build and **does not describe production**. When that build is deployed, this document must be regenerated from the then-current `/openapi.json`.
