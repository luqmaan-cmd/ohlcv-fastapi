# OHLCV Unified API Reference

Base URL: `https://ohlcv-api-832081557693.europe-west2.run.app`

Authentication: All endpoints require an `api_key` query parameter.

```
api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25
```

---

## 1. Overview

This service provides REST API access to OHLCV data ingested from EODHD. It covers stocks, ETFs, indices, cryptocurrencies, forex, government bonds, and more across 50+ global exchanges.

**Use this API to retrieve:**

- Historical OHLCV data (paginated, with date/price/volume filters)
- Latest close prices (single ticker or batch)
- Real-time OHLCV data from EODHD's live API
- OHLCV statistics (count, min/max/avg close, 52-week high/low)
- Read-only SQL query access to underlying tables

---

## Contents

1. [Overview](#1-overview)
2. [Ticker Format](#2-ticker-format)
3. [Supported Exchanges](#3-supported-exchanges)
4. [GET /ohlcv/ — Historical OHLCV](#4-get-ohlcv--historical-ohlcv)
5. [GET /ohlcv/latest_close/ — Batch Latest Close](#5-get-ohlcvlatest_close--batch-latest-close)
6. [GET /ohlcv/latest_close/{ticker} — Single Latest Close](#6-get-ohlcvlatest_closeticker--single-latest-close)
7. [GET /ohlcv/latest/ — Real-Time (EODHD)](#7-get-ohlcvlatest--real-time-eodhd)
8. [GET /ohlcv/stats/{ticker} — Statistics](#8-get-ohlcvstatsticker--statistics)
9. [POST /sql/ — Read-Only SQL Query](#9-post-sql--read-only-sql-query)
10. [GET /commodity/ — Historical Commodity OHLCV](#10-get-commodity--historical-commodity-ohlcv)
11. [GET /commodity/latest/ — Latest Commodity OHLCV](#11-get-commoditylatest--latest-commodity-ohlcv)
12. [GET /commodity/symbols/ — Commodity Symbols](#12-get-commoditysymbols--commodity-symbols)
13. [GET /commodity/categories/ — Commodity Categories](#13-get-commoditycategories--commodity-categories)
14. [Error Responses](#14-error-responses)
15. [Caching](#15-caching)

---

## 2. Ticker Format

All ticker parameters must use the `{TICKER}.{EXCHANGE}` format. Bare tickers are rejected with HTTP 400.

| Format | Example | Valid |
|--------|---------|-------|
| `TICKER.EXCHANGE` | `AAPL.US` | Yes |
| `TICKER.EXCHANGE` | `BP.LSE` | Yes |
| `TICKER.EXCHANGE` | `BTC-USD.CC` | Yes |
| `TICKER.EXCHANGE` | `EURUSD.FOREX` | Yes |
| `TICKER` (bare) | `AAPL` | **No — 400 error** |

**Why:** The same ticker can exist on multiple exchanges with completely different prices. For example, `AZN.US` (AstraZeneca on NASDAQ, ~$65 USD) and `AZN.LSE` (AstraZeneca on London, ~11,970 GBp) are different instruments. Requiring the exchange eliminates ambiguity.

**Error response for bare tickers:**
```json
{
  "detail": "Ticker 'AAPL' must include exchange (e.g., AAPL.US)"
}
```

---

## 3. Supported Exchanges

| Exchange Code | Description | Asset Types | Example Tickers |
|---------------|-------------|-------------|-----------------|
| `US` | US Stocks (NYSE, NASDAQ) | Common Stock, ETF, Preferred Stock | `AAPL.US`, `MSFT.US`, `SPY.US` |
| `LSE` | London Stock Exchange | Common Stock | `BP.LSE`, `AZN.LSE`, `SHEL.LSE` |
| `CC` | Cryptocurrency | Cryptocurrencies | `BTC-USD.CC`, `ETH-USD.CC` |
| `FOREX` | Foreign Exchange | FOREX | `EURUSD.FOREX`, `GBPUSD.FOREX` |
| `GBOND` | Government Bonds | Government Bonds | `US10Y.GBOND`, `UK10Y.GBOND` |
| `AS` | Australian Securities Exchange | INDEX | |
| `BSE` | Bombay Stock Exchange | INDEX | |
| `F` | Euronext Paris | INDEX | |
| `HK` | Hong Kong Stock Exchange | INDEX | |
| `INDX` | Index (generic) | INDEX | |

**Asset Type values:** Common Stock, Cryptocurrencies, ETF, FOREX, Government Bonds, INDEX, BOND, ETC, FUND, Mutual Fund, Notes, Preferred Stock, Unit, Warrant

---

## 4. GET /ohlcv/ — Historical OHLCV

Returns paginated historical OHLCV records. The `year` parameter is **required** for partition pruning.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | — | API key |
| `ticker` | string | No | — | Single ticker (e.g., `AAPL.US`) |
| `tickers` | string | No | — | Comma-separated tickers (e.g., `AAPL.US,MSFT.US,BP.LSE`) |
| `exchange` | string | No | — | Filter by exchange (e.g., `US`, `LSE`, `CC`). Used when no tickers specified. |
| `asset_type` | string | No | — | Filter by asset type (e.g., `ETF`, `Cryptocurrencies`, `FOREX`) |
| `year` | integer | **Yes** | — | Year (1900-2100). Required for partition pruning. |
| `start_date` | date | No | — | Start date (YYYY-MM-DD) |
| `end_date` | date | No | — | End date (YYYY-MM-DD) |
| `month` | integer | No | — | Month filter (1-12) |
| `open_min` | decimal | No | — | Minimum open price |
| `open_max` | decimal | No | — | Maximum open price |
| `close_min` | decimal | No | — | Minimum close price |
| `close_max` | decimal | No | — | Maximum close price |
| `volume_min` | integer | No | — | Minimum volume |
| `volume_max` | integer | No | — | Maximum volume |
| `sort_by` | string | No | `date` | Sort field: `date`, `volume`, `close`, `open`, `high`, `low` |
| `sort_order` | string | No | `desc` | `asc` or `desc` |
| `page` | integer | No | `1` | Page number |
| `per_page` | integer | No | `1000` | Records per page (1-5000) |

### Example Request

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/?tickers=AAPL.US&year=2026&start_date=2026-06-01&end_date=2026-06-30&per_page=10&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Response Schema: PaginatedResponse

```json
{
  "data": [OhlcvDataResponse],
  "total": 165,
  "page": 1,
  "per_page": 1000,
  "total_pages": 1,
  "has_next": false,
  "has_prev": false
}
```

**OhlcvDataResponse fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Record ID |
| `ticker` | string | Ticker symbol (e.g., `AAPL`) |
| `date` | date | Trading date (YYYY-MM-DD) |
| `open` | decimal | Open price |
| `high` | decimal | High price |
| `low` | decimal | Low price |
| `close` | decimal | Close price |
| `adjusted_close` | decimal | Adjusted close price |
| `volume` | integer | Trading volume |
| `asset_isin` | string | ISIN (nullable) |
| `instrument_id` | UUID | Instrument ID (nullable) |
| `exchange` | string | Exchange code (e.g., `US`, `LSE`) |
| `asset_type` | string | Asset type (e.g., `Common Stock`, `ETF`) |
| `created_at` | datetime | Record creation timestamp |
| `updated_at` | datetime | Record update timestamp |

### Example Response

```json
{
  "data": [
    {
      "id": "2438a7ac-0ac8-48d7-a2b1-f012da90d93c",
      "ticker": "AAPL",
      "date": "2026-06-30",
      "open": "310.0000",
      "high": "312.5000",
      "low": "309.2000",
      "close": "311.5000",
      "adjusted_close": "311.5000",
      "volume": 45678901,
      "asset_isin": null,
      "instrument_id": "4a78cd6d-353d-4766-82c0-17082ace2df9",
      "exchange": "US",
      "asset_type": "Common Stock",
      "created_at": "2026-08-31T19:00:51.828141",
      "updated_at": "2026-08-31T19:00:51.828141"
    }
  ],
  "total": 21,
  "page": 1,
  "per_page": 10,
  "total_pages": 3,
  "has_next": true,
  "has_prev": false
}
```

### Equivalent SQL

```sql
SELECT ticker, date, open, high, low, close, adjusted_close, volume, exchange, asset_type
FROM ohlcv_unified
WHERE ticker = 'AAPL' AND exchange = 'US'
  AND date >= '2026-06-01' AND date <= '2026-06-30'
ORDER BY date DESC
LIMIT 10;
```

Via the SQL endpoint:

```bash
curl -X POST "https://ohlcv-api-832081557693.europe-west2.run.app/sql/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT ticker, date, close, volume FROM ohlcv_unified WHERE ticker = '\''AAPL'\'' AND exchange = '\''US'\'' AND date >= '\''2026-06-01'\'' AND date <= '\''2026-06-30'\'' ORDER BY date DESC LIMIT 10"}'
```

---

## 5. GET /ohlcv/latest_close/ — Batch Latest Close

Returns the most recent OHLCV record for each specified ticker. If no tickers are provided, returns the latest record for all tickers on the specified exchange.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | — | API key |
| `tickers` | string | No | — | Comma-separated tickers (e.g., `AAPL.US,MSFT.US,BP.LSE`) |
| `exchange` | string | No | `US` | Filter by exchange when no tickers specified |
| `asset_type` | string | No | — | Filter by asset type |
| `sort_by` | string | No | `ticker` | Sort: `ticker`, `volume`, `close`, `open`, `high`, `low` |
| `per_page` | integer | No | — | Limit results (1-5000). Use with `sort_by=volume` for top-N. |

### Example Request

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/latest_close/?tickers=AAPL.US,MSFT.US&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Response Schema: BatchLatestResponse

| Field | Type | Description |
|-------|------|-------------|
| `data` | array[OhlcvDataResponse] | List of latest OHLCV records (see section 4 for OhlcvDataResponse fields) |
| `count` | integer | Number of records returned |

### Example Response

```json
{
  "data": [
    {
      "id": "2438a7ac-0ac8-48d7-a2b1-f012da90d93c",
      "ticker": "AAPL",
      "date": "2026-08-31",
      "open": "314.5000",
      "high": "318.0000",
      "low": "313.2000",
      "close": "316.8500",
      "adjusted_close": "316.8500",
      "volume": 12345678,
      "asset_isin": null,
      "instrument_id": "4a78cd6d-353d-4766-82c0-17082ace2df9",
      "exchange": "US",
      "asset_type": "Common Stock",
      "created_at": "2026-08-31T19:00:51.828141",
      "updated_at": "2026-08-31T19:00:51.828141"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "ticker": "MSFT",
      "date": "2026-08-31",
      "open": "505.0000",
      "high": "509.0000",
      "low": "503.0000",
      "close": "507.2900",
      "adjusted_close": "507.2900",
      "volume": 9876543,
      "asset_isin": null,
      "instrument_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "exchange": "US",
      "asset_type": "Common Stock",
      "created_at": "2026-08-31T19:00:51.828141",
      "updated_at": "2026-08-31T19:00:51.828141"
    }
  ],
  "count": 2
}
```

### Equivalent SQL

```sql
SELECT t.ticker, o.id, o.date, o.open, o.high, o.low, o.close,
       o.adjusted_close, o.volume, o.exchange, o.asset_type
FROM (VALUES ('AAPL','US'), ('MSFT','US')) AS t(ticker, exchange)
CROSS JOIN LATERAL (
    SELECT id, date, open, high, low, close, adjusted_close, volume, exchange, asset_type
    FROM ohlcv_unified
    WHERE ticker = t.ticker AND exchange = t.exchange
          AND date >= '2026-08-25'
    ORDER BY date DESC
    LIMIT 1
) o
ORDER BY t.ticker ASC;
```

---

## 6. GET /ohlcv/latest_close/{ticker} — Single Latest Close

Returns the most recent OHLCV record for a single ticker (within the last 7 days).

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | Yes | Ticker in `TICKER.EXCHANGE` format (e.g., `AAPL.US`) |

### Example Request

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/latest_close/AAPL.US?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Response Schema: OhlcvDataResponse

See section 4 for full field reference.

### Example Response

```json
{
  "id": "2438a7ac-0ac8-48d7-a2b1-f012da90d93c",
  "ticker": "AAPL",
  "date": "2026-08-31",
  "open": "314.5000",
  "high": "318.0000",
  "low": "313.2000",
  "close": "316.8500",
  "adjusted_close": "316.8500",
  "volume": 12345678,
  "asset_isin": null,
  "instrument_id": "4a78cd6d-353d-4766-82c0-17082ace2df9",
  "exchange": "US",
  "asset_type": "Common Stock",
  "created_at": "2026-08-31T19:00:51.828141",
  "updated_at": "2026-08-31T19:00:51.828141"
}
```

### Equivalent SQL

```sql
SELECT * FROM ohlcv_unified
WHERE ticker = 'AAPL' AND exchange = 'US'
  AND date >= '2026-08-25'
ORDER BY date DESC
LIMIT 1;
```

---

## 7. GET /ohlcv/latest/ — Real-Time (EODHD)

Returns real-time OHLCV data from EODHD's live API. Tickers are validated against the `assets` table before fetching.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | API key |
| `tickers` | string | Yes | Comma-separated tickers in `TICKER.EXCHANGE` format (e.g., `AAPL.US,BP.LSE,BTC-USD.CC`) |

### Example Request

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/latest/?tickers=AAPL.US,MSFT.US&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Response Schema: RealTimeOhlcvResponse

| Field | Type | Description |
|-------|------|-------------|
| `data` | array[RealTimeOhlcvItem] | List of real-time OHLCV items |
| `count` | integer | Number of items returned |

**RealTimeOhlcvItem fields:**

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Ticker with exchange (e.g., `AAPL.US`) |
| `exchange` | string | Exchange code |
| `timestamp` | integer | Unix timestamp |
| `datetime` | datetime | ISO datetime |
| `open` | decimal | Open price |
| `high` | decimal | High price |
| `low` | decimal | Low price |
| `close` | decimal | Close price |
| `adjusted_close` | decimal | Adjusted close price |
| `volume` | integer | Trading volume |

### Example Response

```json
{
  "data": [
    {
      "ticker": "AAPL.US",
      "exchange": "US",
      "timestamp": 1725148800,
      "datetime": "2026-09-01T16:00:00",
      "open": "314.50",
      "high": "318.00",
      "low": "313.20",
      "close": "316.85",
      "adjusted_close": "316.85",
      "volume": 12345678
    },
    {
      "ticker": "MSFT.US",
      "exchange": "US",
      "timestamp": 1725148800,
      "datetime": "2026-09-01T16:00:00",
      "open": "505.00",
      "high": "509.00",
      "low": "503.00",
      "close": "507.29",
      "adjusted_close": "507.29",
      "volume": 9876543
    }
  ],
  "count": 2
}
```

### Equivalent SQL

This endpoint fetches from EODHD's external API, not from the database. There is no direct SQL equivalent.

---

## 8. GET /ohlcv/stats/{ticker} — Statistics

Returns aggregated OHLCV statistics for a ticker, including 52-week high/low.

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | Yes | Ticker in `TICKER.EXCHANGE` format (e.g., `AAPL.US`) |

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | — | API key |
| `start_date` | date | No | — | Start date for stats (enables partition pruning) |
| `end_date` | date | No | — | End date for stats (enables partition pruning) |

### Example Request

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/stats/AAPL.US?start_date=2026-01-01&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Response Schema: OhlcvStatsResponse

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Ticker with exchange (e.g., `AAPL.US`) |
| `count` | integer | Number of OHLCV records |
| `earliest_date` | date | First available date |
| `latest_date` | date | Most recent date |
| `avg_volume` | float | Average trading volume |
| `min_close` | decimal | Minimum close price |
| `max_close` | decimal | Maximum close price |
| `avg_close` | decimal | Average close price |
| `fifty_two_week_high` | decimal | 52-week high (close) |
| `fifty_two_week_low` | decimal | 52-week low (close) |

### Example Response

```json
{
  "ticker": "AAPL.US",
  "count": 165,
  "earliest_date": "2026-01-02",
  "latest_date": "2026-08-31",
  "avg_volume": 58234567.5,
  "min_close": "246.6300",
  "max_close": "340.0800",
  "avg_close": "295.1234",
  "fifty_two_week_high": "340.0800",
  "fifty_two_week_low": "226.7900"
}
```

### Equivalent SQL

```sql
-- Stats
SELECT count(*), min(date), max(date), avg(volume),
       min(close), max(close), avg(close)
FROM ohlcv_unified
WHERE ticker = 'AAPL' AND exchange = 'US'
  AND date >= '2026-01-01';

-- 52-week high/low
SELECT max(close), min(close)
FROM ohlcv_unified
WHERE ticker = 'AAPL' AND exchange = 'US'
  AND date >= '2025-09-01';
```

---

## 9. POST /sql/ — Read-Only SQL Query

Executes a read-only SQL query against the database. Only `SELECT` statements are allowed. Tables must be in the allowed list.

### Allowed Tables

`ohlcv_unified`, `assets`, `tickers`, `commodities_eod`, `ust_bill_rates`, `ust_long_term_rates`, `ust_real_yield_rates`, `ust_yield_rates`, and all legacy tables.

### Request Body

```json
{
  "query": "SELECT ticker, close, volume FROM ohlcv_unified WHERE exchange = 'US' AND date = '2026-08-31' ORDER BY volume DESC LIMIT 10"
}
```

### Example Request

```bash
curl -X POST "https://ohlcv-api-832081557693.europe-west2.run.app/sql/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT ticker, close, volume FROM ohlcv_unified WHERE exchange = '\''US'\'' AND date = '\''2026-08-31'\'' ORDER BY volume DESC LIMIT 10"}'
```

### Response Schema: SqlQueryResponse

| Field | Type | Description |
|-------|------|-------------|
| `columns` | array[string] | Column names in the result set |
| `rows` | array[object] | Result rows as list of dicts |
| `row_count` | integer | Number of rows returned |
| `truncated` | boolean | True if result was truncated due to row limit |

### Example Response

```json
{
  "columns": ["ticker", "close", "volume"],
  "rows": [
    {"ticker": "AAPL", "close": "316.8500", "volume": 12345678},
    {"ticker": "TSLA", "close": "245.6700", "volume": 9876543}
  ],
  "row_count": 2,
  "truncated": false
}
```

### Limits

- Maximum 5,000 rows returned (configurable via `SQL_MAX_ROWS` env var)
- Query timeout: 30 seconds (configurable)
- Only `SELECT` statements allowed
- All referenced tables must be in the allowed list

---

## 10. GET /commodity/ — Historical Commodity OHLCV

Returns paginated historical OHLCV data for commodities. Commodities use separate tables (`commodities_eod`) with their own metadata — they are not part of `ohlcv_unified`.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | — | API key |
| `symbol` | string | No | — | Single commodity symbol (e.g., `LGOc3`) |
| `symbols` | string | No | — | Comma-separated symbols (e.g., `LGOc3,NICKEL,GDK`) |
| `category` | string | No | — | Filter by category (e.g., `Energy`, `Metals`, `Grains`, `Softs`, `Livestock`, `Other`) |
| `start_date` | date | No | — | Start date (YYYY-MM-DD) |
| `end_date` | date | No | — | End date (YYYY-MM-DD) |
| `year` | integer | No | — | Filter by year (e.g., `2026`) |
| `month` | integer | No | — | Month filter (1-12) |
| `open_min` | decimal | No | — | Minimum open price |
| `open_max` | decimal | No | — | Maximum open price |
| `close_min` | decimal | No | — | Minimum close price |
| `close_max` | decimal | No | — | Maximum close price |
| `volume_min` | integer | No | — | Minimum volume |
| `volume_max` | integer | No | — | Maximum volume |
| `sort_by` | string | No | `date` | Sort field: `date`, `volume`, `close`, `open`, `high`, `low` |
| `sort_order` | string | No | `desc` | `asc` or `desc` |
| `page` | integer | No | `1` | Page number |
| `per_page` | integer | No | `1000` | Records per page (1-5000) |

### Example Request

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/commodity/?symbols=LGOc3,NICKEL&start_date=2026-01-01&end_date=2026-06-30&per_page=10&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Response Schema: CommodityPaginatedResponse

| Field | Type | Description |
|-------|------|-------------|
| `data` | array[CommodityOhlcvResponse] | List of commodity OHLCV records |
| `total` | integer | Total matching records |
| `page` | integer | Current page |
| `per_page` | integer | Records per page |
| `total_pages` | integer | Total pages |
| `has_next` | boolean | Has next page |
| `has_prev` | boolean | Has previous page |

**CommodityOhlcvResponse fields:**

| Field | Type | Description |
|-------|------|-------------|
| `date` | date | Trading date |
| `symbol` | string | Commodity symbol (e.g., `LGOc3`) |
| `name` | string | Commodity name (e.g., `Gold Futures`) |
| `open` | decimal | Open price |
| `high` | decimal | High price |
| `low` | decimal | Low price |
| `close` | decimal | Close price |
| `adjusted_close` | decimal | Adjusted close price |
| `volume` | integer | Trading volume |
| `category` | string | Category (e.g., `Energy`, `Metals`) |
| `ingestion_ts` | datetime | Ingestion timestamp |

### Example Response

```json
{
  "data": [
    {
      "date": "2026-06-30",
      "symbol": "LGOc3",
      "name": "Gold Futures",
      "open": "2350.0000",
      "high": "2360.0000",
      "low": "2345.0000",
      "close": "2355.0000",
      "adjusted_close": "2355.0000",
      "volume": 150000,
      "category": "Metals",
      "ingestion_ts": "2026-06-30T18:00:00"
    }
  ],
  "total": 21,
  "page": 1,
  "per_page": 10,
  "total_pages": 3,
  "has_next": true,
  "has_prev": false
}
```

### Equivalent SQL

```sql
SELECT date, symbol, name, open, high, low, close, adjusted_close, volume, category, ingestion_ts
FROM commodities_eod
WHERE symbol IN ('LGOc3', 'NICKEL')
  AND date >= '2026-01-01' AND date <= '2026-06-30'
ORDER BY date DESC
LIMIT 10;
```

---

## 11. GET /commodity/latest/ — Latest Commodity OHLCV

Returns the latest OHLCV record for each commodity symbol. If no symbols are provided, returns latest for all commodities.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | — | API key |
| `symbols` | string | No | — | Comma-separated symbols (e.g., `LGOc3,NICKEL,GDK`). If omitted, returns latest for all. |
| `category` | string | No | — | Filter by category (e.g., `Energy`, `Metals`) |

### Example Request

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/commodity/latest/?symbols=LGOc3,NICKEL&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Response Schema: CommodityLatestResponse

| Field | Type | Description |
|-------|------|-------------|
| `data` | array[CommodityLatestItem] | List of latest commodity OHLCV items |
| `count` | integer | Number of items returned |

**CommodityLatestItem fields:**

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | string | Commodity symbol |
| `name` | string | Commodity name |
| `category` | string | Category |
| `date` | date | Latest trading date |
| `open` | decimal | Open price |
| `high` | decimal | High price |
| `low` | decimal | Low price |
| `close` | decimal | Close price |
| `adjusted_close` | decimal | Adjusted close price |
| `volume` | integer | Trading volume |

### Example Response

```json
{
  "data": [
    {
      "symbol": "LGOc3",
      "name": "Gold Futures",
      "category": "Metals",
      "date": "2026-08-31",
      "open": "2350.0000",
      "high": "2360.0000",
      "low": "2345.0000",
      "close": "2355.0000",
      "adjusted_close": "2355.0000",
      "volume": 150000
    },
    {
      "symbol": "NICKEL",
      "name": "Nickel",
      "category": "Metals",
      "date": "2026-08-31",
      "open": "16800.0000",
      "high": "16900.0000",
      "low": "16750.0000",
      "close": "16850.0000",
      "adjusted_close": "16850.0000",
      "volume": 5000
    }
  ],
  "count": 2
}
```

### Equivalent SQL

```sql
SELECT DISTINCT ON (symbol) symbol, name, category,
       date, open, high, low, close, adjusted_close, volume
FROM commodities_eod
WHERE symbol IN ('LGOc3', 'NICKEL')
ORDER BY symbol, date DESC;
```

---

## 12. GET /commodity/symbols/ — Commodity Symbols

Returns all commodity symbols with their latest metadata (name and category).

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | — | API key |
| `category` | string | No | — | Filter by category (e.g., `Energy`, `Metals`) |

### Example Request

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/commodity/symbols/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Response Schema: CommoditySymbolResponse

| Field | Type | Description |
|-------|------|-------------|
| `data` | array[CommoditySymbolItem] | List of commodity symbols |
| `count` | integer | Number of symbols |

**CommoditySymbolItem fields:**

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | string | Commodity symbol (e.g., `LGOc3`) |
| `name` | string | Commodity name (e.g., `Gold Futures`) |
| `category` | string | Category (e.g., `Metals`) |

### Example Response

```json
{
  "data": [
    {
      "symbol": "LGOc3",
      "name": "Gold Futures",
      "category": "Metals"
    },
    {
      "symbol": "NICKEL",
      "name": "Nickel",
      "category": "Metals"
    },
    {
      "symbol": "BRTc3",
      "name": "Brent Crude Oil Futures",
      "category": "Energy"
    }
  ],
  "count": 3
}
```

### Equivalent SQL

```sql
SELECT DISTINCT ON (symbol) symbol, name, category
FROM commodities_eod
ORDER BY symbol, date DESC;
```

---

## 13. GET /commodity/categories/ — Commodity Categories

Returns a list of all commodity categories.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | API key |

### Example Request

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/commodity/categories/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Response Schema: CommodityCategoryResponse

| Field | Type | Description |
|-------|------|-------------|
| `data` | array[string] | List of category names |
| `count` | integer | Number of categories |

### Example Response

```json
{
  "data": ["Energy", "Metals", "Grains", "Softs", "Livestock", "Other"],
  "count": 6
}
```

### Equivalent SQL

```sql
SELECT DISTINCT category FROM commodities_eod ORDER BY category;
```

---

## 14. Error Responses

### 400 Bad Request — Bare Ticker

Returned when a ticker is provided without an exchange suffix.

```json
{
  "detail": "Ticker 'AAPL' must include exchange (e.g., AAPL.US)"
}
```

### 404 Not Found

Returned when no data is found for the given ticker/ID.

```json
{
  "detail": "No OHLCV data found for ticker: AAPL.US"
}
```

### 422 Validation Error

Returned when required parameters are missing or invalid (e.g., `year` not provided, `per_page` > 5000).

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["query", "year"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

### 400 Bad Request — SQL Error

Returned by `/sql/` when the query is invalid or references disallowed tables.

```json
{
  "detail": "Query references disallowed tables: some_table. Allowed tables: ohlcv_unified, assets, ..."
}
```

---

## 15. Caching

- **What:** Count query results (used for pagination metadata)
- **TTL:** 3,600 seconds (1 hour)
- **Scope:** Global — shared across all API consumers
- **Key:** Based on query parameters (tickers, exchange, year, dates, filters)
- **Impact:** First request for a given query may be slow (e.g., `exchange=US` count takes ~7s cold). Subsequent requests within 1 hour return cached count in ~10ms.
