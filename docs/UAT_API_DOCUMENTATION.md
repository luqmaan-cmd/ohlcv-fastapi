# UAT API Documentation

> Environment: UAT. Production is documented in [PROD_API_DOCUMENTATION.md](PROD_API_DOCUMENTATION.md); the API surface is identical, only the base URL differs.

## Overview

The API serves daily OHLCV (open, high, low, close, adjusted close, volume)
for every instrument we hold, from a single partitioned table.

- **Addressing:** every instrument is identified by `TICKER.EXCHANGE`, e.g.
  `AAPL.US`, `BP.LSE`, `AZN.LSE`, `BTC-USD.CC`. Always include the suffix,
  `.US` included. A bare ticker is rejected with `400`.
- **History:** daily bars from **1962** through the current year, partitioned
  by year.
- **Grain:** one row per instrument per trading day. Non-trading days have no
  row, so an instrument missing from a given trading day is no longer trading.
- **Identifiers:** rows carry an `instrument_id` (a UUID) identifying the
  instrument. It is not an ISIN.

### Use this API for

- **Historical price series** — pull daily bars for any instrument from 1962 to today
- **Single-asset lookups** — fetch one ticker's history or its latest close
- **Batch queries** — request many tickers in one call instead of looping
- **Cross-market screening** — filter by exchange, asset type, price or volume range
- **Latest close** — get an asset's most recent bar by querying the latest trading day
- **Delisted detection** — an asset absent from a trading day's results is no longer trading
- **Real-time quotes** — request live prices for specific tickers
- **Ranking** — sort by volume, close or date to build top-N lists
- **ETFs, indices and funds** — the same endpoints cover all listed instruments we hold
- **FX and crypto** — currency pairs and crypto pairs are addressed like any other ticker
- **Commodities** — a separate endpoint set for futures-style symbols
- **Agent and LLM tooling** — OpenAPI-documented, JSON responses, predictable pagination

### Asset classes

Daily bars are held for:

- **Equities** — common stock, preferred stock, warrants and units
- **ETFs** and **ETCs**
- **Funds** — `FUND` and `Mutual Fund`
- **Indices** — `INDX`
- **Foreign exchange** — `FOREX` pairs
- **Cryptocurrencies** — `CC`
- **Government bonds** — `GBOND`
- **Notes**

The exchange and market codes are listed in [Coverage reference](#coverage-reference).

### Endpoints

Retrieval is `GET` except where a write is supported:

| Path | Methods | Notes |
|---|---|---|
| `/ohlcv/` | `GET`, `POST` | `POST` inserts one row (`201`) |
| `/ohlcv/bulk/` | `POST` | Bulk insert (`201`) |
| `/ohlcv/latest/` | `GET` | Live quotes |
| `/commodity/` | `GET` | Stored commodity history |
| `/commodity/latest/` | `GET` | Live commodity quotes |
| `/commodity/symbols/` | `GET` | Symbol reference |
| `/ust/` | `GET` | Treasury rates |
| `/sql/` | `POST` | `SELECT` / `WITH` only, whitelisted tables, 5,000-row cap |

No path supports `PUT` or `DELETE`. An unsupported method returns `405` with
the permitted methods in the `Allow` header — `/ohlcv/` reports `Allow: GET`
even though `POST` is also served, because the two are separate handlers.

### Response envelopes

Four envelope shapes are used, each stable within its group:

| Shape | Used by |
|---|---|
| `{data, total, page, per_page, total_pages, has_next, has_prev}` | `/ohlcv/`, `/commodity/`, `/ust/` |
| `{data, count, missing}` | `/ohlcv/latest/`, `/commodity/latest/` |
| `{data, count}` | `/commodity/symbols/` |
| `{columns, rows, row_count, truncated}` | `/sql/` |

| Endpoint | Method | Purpose |
|---|---|---|
| `/ohlcv/` | GET | Paginated OHLCV history, filterable by ticker, venue, asset type, date and price/volume |
| `/ohlcv/latest/` | GET | Real-time quotes for specific tickers |
| `/commodity/` and related | GET | Commodity history (separate table) |
| `/ust/` | GET | US Treasury rates across bill, long-term, real-yield and yield series |

---

#### GET /ohlcv/

Returns daily bars, newest first by default.

**Query parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ticker` | string | — | Single ticker, e.g. `AAPL.US`, `BP.LSE`, `BTC-USD.CC` |
| `tickers` | string | — | Comma-separated tickers, e.g. `AAPL.US,MSFT.US` |
| `exchange` | string | `US` | Venue filter when no tickers are given, e.g. `LSE`, `CC` |
| `asset_type` | string | — | Class filter, e.g. `ETF`, `INDEX`, `FOREX`, `Cryptocurrencies`, `Government Bonds` |
| `start_date` | date | — | Inclusive start, `YYYY-MM-DD` |
| `end_date` | date | — | Inclusive end, `YYYY-MM-DD` |
| `year` | int | — | Shorthand for a whole calendar year; prunes partitions |
| `month` | int | — | Month filter (1–12) |
| `open_min` / `open_max` | decimal | — | Open price range |
| `close_min` / `close_max` | decimal | — | Close price range |
| `volume_min` / `volume_max` | int | — | Volume range |
| `sort_by` | string | `date` | `date`, `open`, `high`, `low`, `close`, `volume` |
| `sort_order` | string | `desc` | `asc` or `desc` |
| `realtime` | bool | `false` | Return live quotes instead of stored rows (requires a ticker) |
| `page` | int | `1` | Page number |
| `per_page` | int | `1000` | Rows per page (max 5000) |

`exchange` and `asset_type` are filters for when you are not naming tickers.
Neither can supply a missing suffix: `ticker=AZN&exchange=LSE` is rejected —
write `ticker=AZN.LSE`.

**Example request**

```bash
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/?ticker=AAPL.US&start_date=2026-11-19&end_date=2026-11-23&per_page=2"
```

**Example response**

```json
{
  "data": [
    {
      "ticker": "AAPL",
      "date": "2026-11-23",
      "open": "347.8700",
      "high": "352.6000",
      "low": "345.4422",
      "close": "349.0800",
      "adjusted_close": "349.0800",
      "volume": 56934608,
      "instrument_id": "66ab0ba1-3b9d-4f2f-94ae-b2cc069d53e6",
      "exchange": "US",
      "asset_type": "Common Stock"
    },
    {
      "ticker": "AAPL",
      "date": "2026-11-20",
      "open": "352.8650",
      "high": "354.3400",
      "low": "340.5600",
      "close": "342.5600",
      "adjusted_close": "342.5600",
      "volume": 79734485,
      "instrument_id": "66ab0ba1-3b9d-4f2f-94ae-b2cc069d53e6",
      "exchange": "US",
      "asset_type": "Common Stock"
    }
  ],
  "total": 3,
  "page": 1,
  "per_page": 2,
  "total_pages": 2,
  "has_next": true,
  "has_prev": false
}
```

**Response fields**

| Field | Type | Description |
|---|---|---|
| `ticker` | string | Instrument code, without the exchange suffix |
| `date` | date | Trading day, `YYYY-MM-DD` |
| `open` / `high` / `low` / `close` | decimal | Daily prices |
| `adjusted_close` | decimal | Close adjusted for corporate actions |
| `volume` | int | Shares or units traded |
| `instrument_id` | uuid | Stable instrument identifier (a UUID, not an ISIN) |
| `exchange` | string | Venue code, e.g. `US`, `LSE`, `CC` |
| `asset_type` | string | Asset class |

Price fields (`open`, `high`, `low`, `close`, `adjusted_close`) are decimal
**strings**, preserving stored precision; `volume` and `timestamp` are numbers.
`/sql/` is the exception — it returns driver-native numerics (e.g. `349.08`).

**Pagination envelope**

| Field | Type | Description |
|---|---|---|
| `total` | int | Total matching rows across all pages |
| `page` | int | Current page |
| `per_page` | int | Rows requested per page |
| `total_pages` | int | Number of pages available |
| `has_next` / `has_prev` | bool | Whether further pages exist |

#### Latest close

There is no dedicated latest-close endpoint. Request the last trading day for
the asset with the date filters:

```bash
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/?ticker=AAPL.US&start_date=2026-11-23&end_date=2026-11-23"
```

- Use the most recent trading day for that exchange (e.g. Friday for a
  weekend date, or the prior session on a public holiday).
- An empty result means the instrument did not trade that day.
- A ticker that never appears is no longer trading.
- Raise `per_page` if you need every instrument for that day, not one asset.

---

#### GET /ohlcv/latest/

Live quote from the upstream provider, rather than the stored table.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `tickers` | string | yes | Comma-separated tickers, e.g. `AAPL.US,BP.LSE` |

```bash
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/latest/?tickers=AAPL.US,NOTAREAL.US"
```

```json
{
  "data": [
    {
      "ticker": "AAPL",
      "exchange": "US",
      "timestamp": 1795463100,
      "datetime": "2026-11-23T00:00:00",
      "open": "347.78",
      "high": "352.6",
      "low": "345.442189",
      "close": "349.675",
      "adjusted_close": null,
      "volume": 29347030
    }
  ],
  "count": 1,
  "missing": ["NOTAREAL.US"]
}
```

Each ticker is resolved independently:

- A ticker with no live quote comes back with null prices.
- An unknown ticker is listed in `missing`; the rest are still returned.
- `404` only when none of the requested tickers resolve.

Rows carry `ticker`, `exchange`, `timestamp`, `datetime`, `open`, `high`, `low`,
`close`, `adjusted_close` and `volume`. Real-time rows have no `asset_type` or
`instrument_id` — query `/ohlcv/` for stored metadata.

---

#### POST /ohlcv/

Inserts one row. Returns `201` with the stored record.

| Field | Type | Required | Description |
|---|---|---|---|
| `ticker` | string | yes | Code without the exchange suffix, e.g. `AAPL` |
| `date` | date | yes | Trading day, `YYYY-MM-DD` |
| `exchange` | string | yes | Venue code, e.g. `US`, `LSE` |
| `asset_type` | string | yes | Class, e.g. `Common Stock`, `ETF` |
| `open` / `high` / `low` / `close` | decimal | — | Daily prices |
| `adjusted_close` | decimal | — | Adjusted close |
| `volume` | int | — | Shares or units traded |
| `instrument_id` | uuid | — | Instrument identifier |

`exchange` and `asset_type` are required by the database — a payload that
omits either is rejected.

```bash
curl -X POST \
  -H "X-API-Key: YOUR-API-KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "ticker": "AAPL",
        "date": "2026-11-24",
        "open": "349.08",
        "high": "352.60",
        "low": "345.44",
        "close": "349.08",
        "adjusted_close": "349.08",
        "volume": 56934608,
        "exchange": "US",
        "asset_type": "Common Stock"
      }' \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/"
```

The ticker is stored **without** the exchange suffix; the venue goes in the
`exchange` field. A rejected write returns `400` with the database error in
`detail`.

---

#### POST /ohlcv/bulk/

Inserts many rows in one request. Same fields as `POST /ohlcv/`, wrapped in a
`records` array.

```bash
curl -X POST \
  -H "X-API-Key: YOUR-API-KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "records": [
          { "ticker": "AAPL", "date": "2026-11-24", "close": "349.08", "volume": 56934608, "exchange": "US", "asset_type": "Common Stock" },
          { "ticker": "MSFT", "date": "2026-11-24", "close": "412.30", "volume": 21000000, "exchange": "US", "asset_type": "Common Stock" }
        ]
      }' \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/bulk/"
```

Returns `201` with a per-request summary — check `failed` before assuming every
record landed:

```json
{
  "inserted": 2,
  "failed": 0,
  "errors": []
}
```

`errors` holds one message per rejected record, prefixed by its index in the
`records` array (e.g. `"Record 1: duplicate key value ..."`).

Partial success applies only to records that reach the database. Shape problems
are rejected before the request runs: one record with a malformed field returns
`422` for the whole request (e.g. `{"loc": ["records", 1, "date"]}`) and nothing
is inserted.

---

#### POST /sql/

Runs a read-only SQL query. It is a `POST` because the query travels in the
body, not because it writes.

```bash
curl -X POST \
  -H "X-API-Key: YOUR-API-KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "query": "SELECT ticker, date, close, volume FROM ohlcv_unified WHERE ticker = '"'"'AAPL'"'"' AND exchange = '"'"'US'"'"' AND date >= '"'"'2026-11-01'"'"' ORDER BY date DESC LIMIT 5"
      }' \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/sql/"
```

```json
{
  "columns": ["ticker", "date", "close", "volume"],
  "rows": [
    { "ticker": "AAPL", "date": "2026-11-23", "close": 349.08, "volume": 56934608 }
  ],
  "row_count": 1,
  "truncated": false
}
```

Guardrails:

| Rule | Detail |
|---|---|
| Read-only | Only `SELECT` or `WITH` (CTE) statements |
| Tables | Must be in the whitelist — `ohlcv_unified`, `assets`, `tickers`, `ticker_aliases`, `commodities_eod`, and the four `ust_*` rate tables |
| Timeout | 30 seconds (`SQL_TIMEOUT_S`); exceeding it returns `504` |
| Row cap | 5,000 rows (`SQL_MAX_ROWS`); extra rows are dropped and `truncated` is `true` |

A rejected statement returns `400`. Two cases share one message shape,
`Only SELECT queries are allowed. Statement starts with '…'`: a genuine write
attempt (`DELETE …`) and malformed SQL whose first word is not a keyword
(`SELEC …`). Malformed SQL that passes the guardrails fails at execution and
returns `Query execution error: …` instead.

---

### Commodities

Commodities are also available, but from their own table rather than the
shared OHLCV table, so they have a separate endpoint set:

| Endpoint | Purpose |
|---|---|
| `/commodity/` | Paginated historical OHLCV; `latest=true` for the most recent stored bar per symbol |
| `/commodity/latest/` | Real-time quotes from EODHD (live, not stored) |
| `/commodity/symbols/` | List of available commodity symbols, with name and category |

Commodity symbols are addressed directly (e.g. `LGOc3`, `NICKEL`, `GDK`),
not as `TICKER.EXCHANGE`.

#### GET /commodity/

| Parameter | Type | Description |
|---|---|---|
| `symbol` | string | Single commodity symbol, e.g. `LGOc3` |
| `symbols` | string | Comma-separated symbols, e.g. `LGOc3,NICKEL,GDK` |
| `category` | string | e.g. `Energy`, `Metals`, `Grains`, `Softs`, `Livestock`, `Other` |
| `start_date` / `end_date` | date | Date range, `YYYY-MM-DD` |
| `year` / `month` | int | Calendar filters |
| `open_min` / `open_max` | decimal | Open price range |
| `close_min` / `close_max` | decimal | Close price range |
| `volume_min` / `volume_max` | int | Volume range |
| `sort_by` | string | `date` (default), `open`, `high`, `low`, `close`, `volume` |
| `sort_order` | string | `asc` or `desc` (default) |
| `latest` | bool | `true` = one row per symbol, its most recent stored bar |
| `page` / `per_page` | int | Default `1` / `1000` (max `5000`) |

```bash
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/commodity/?symbol=LGOc3&per_page=1"
```

Most recent stored bar for several symbols at once:

```bash
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/commodity/?symbols=LGOc3,NICKEL,GDK&latest=true"
```

```json
{
  "data": [
    {
      "date": "2026-11-23",
      "symbol": "LGOc3",
      "name": "Gas Oil",
      "open": "1112.75",
      "high": "1116",
      "low": "1046.5",
      "close": "1052",
      "adjusted_close": "1052",
      "volume": 34891,
      "category": null,
      "ingestion_ts": "2026-11-24T06:00:42.264029"
    }
  ],
  "total": 11835,
  "page": 1,
  "per_page": 1,
  "total_pages": 11835,
  "has_next": true,
  "has_prev": false
}
```

Response fields: `date`, `symbol`, `name`, `open`, `high`, `low`, `close`,
`adjusted_close`, `volume`, `category`, `ingestion_ts`. The pagination envelope
matches `/ohlcv/`.

#### GET /commodity/latest/

Live quotes from EODHD, mirroring `/ohlcv/latest/` — not the stored table. All
requested symbols go out in one upstream request, resolved as `SYMBOL.COMM`.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `symbols` | string | yes | Comma-separated symbols, e.g. `GDK,LGOc3` |

```bash
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/commodity/latest/?symbols=GDK,LGOc3"
```

```json
{
  "data": [
    {
      "ticker": "GDK",
      "exchange": "COMM",
      "timestamp": 1795535820,
      "datetime": "2026-11-24T11:57:00",
      "open": "19.81",
      "high": "19.91",
      "low": "19.39",
      "close": "19.39",
      "adjusted_close": null,
      "volume": 33
    },
    {
      "ticker": "LGOc3",
      "exchange": "COMM",
      "timestamp": null,
      "datetime": null,
      "open": null,
      "high": null,
      "low": null,
      "close": null,
      "adjusted_close": null,
      "volume": null
    }
  ],
  "count": 2,
  "missing": []
}
```

Symbols are resolved independently: one with no live quote comes back with null
prices, and an unknown symbol is listed in `missing` while the rest are still
returned. `404` only when none of the requested symbols exist. Use the stored
`/commodity/?latest=true` if you need a value for a symbol without a quote.

#### GET /commodity/symbols/

Lists symbols with their name and category. Optional `category` filter.

```bash
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/commodity/symbols/?category=Metals"
```

Returns `{ "data": [{ "symbol": "...", "name": "...", "category": "..." }], "count": N }`.

Distinct categories are not a separate endpoint; take them from
`/commodity/symbols/`.

---

### US Treasury rates

One endpoint returns all four rate series from a single union; `series` selects
which. It is a `GET`.

| Parameter | Type | Description |
|---|---|---|
| `series` | string | `bill`, `long_term`, `real_yield`, `yield`; comma-separated; default all four |
| `tenor` / `tenors` | string | `bill`, `real_yield`, `yield`; see the value lists below |
| `rate_type` / `rate_types` | string | `long_term` only; `BC_20year`, `Over_10_Years`, `Real_Rate` |
| `start_date` / `end_date` | date | Inclusive bounds |
| `latest` | bool | `true` = one row per series and tenor/rate type |
| `sort_by` | string | `date` (default), `rate`, `discount`, `coupon` |
| `sort_order` | string | `asc` or `desc` (default) |
| `page` / `per_page` | int | Default `1` / `1000` (max `5000`) |

Every accepted value per series is listed under **US Treasury series and
tenors** in the Coverage reference. A `tenor` or `rate_type` outside those
lists is rejected with `400`, naming the accepted values — it is not treated
as an empty result.

Every series shares one envelope and one item shape; each populates only its own
fields:

| Field | Populated by |
|---|---|
| `series`, `date` | all |
| `tenor` | `bill`, `real_yield`, `yield` |
| `rate_type` | `long_term` |
| `rate` | `long_term`, `real_yield`, `yield` |
| `discount`, `coupon`, `avg_discount`, `avg_coupon`, `maturity_date`, `cusip` | `bill` |
| `extrapolation_factor` | `long_term` |

`extrapolation_factor` is reserved for `long_term` rows and is currently always
null — the upstream source does not populate it.

```bash
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ust/?series=bill&tenor=13WK&per_page=1"
```

```json
{
  "data": [
    {
      "series": "bill",
      "date": "2026-11-20",
      "tenor": "13WK",
      "rate_type": null,
      "rate": null,
      "discount": "4.130000",
      "coupon": "4.230000",
      "avg_discount": "4.150000",
      "avg_coupon": "4.250000",
      "maturity_date": "2027-02-18",
      "cusip": "912797TV9",
      "extrapolation_factor": null
    }
  ],
  "total": 223,
  "page": 1,
  "per_page": 1,
  "total_pages": 223,
  "has_next": true,
  "has_prev": false
}
```

The most recent value for every series and tenor in one call:

```bash
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ust/?latest=true&per_page=50"
```

This endpoint replaces the eight per-series Treasury routes, which are retired.

---

## Environment

Base URL (UAT): `https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app`

This document covers the UAT environment.

---

## Authentication

Every request requires an API key. Send it either way:

**Query parameter**

```bash
curl "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/?ticker=AAPL.US&per_page=5&api_key=YOUR-API-KEY"
```

**Header (preferred — keeps the key out of URLs and logs)**

```bash
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/?ticker=AAPL.US&per_page=5"
```

| Situation | Response |
|---|---|
| Valid key | `200` |
| Missing key | `401 Invalid or missing API key` |
| Unknown key | `401 Invalid or missing API key` |

Notes:

- `YOUR-API-KEY` is a placeholder — request the real key separately.
- Keys are rate-limited per key. Do not share a key across services.
- Extra parameters join with `&` — never append the key to the path or after a
  second `?`. See [Good practices](#good-practices).

---

## Coverage reference

### Exchange codes

Every instrument is addressed as `TICKER.CODE`. The code is a listing
venue, or one of the non-venue codes listed separately below.

| Code | Market |
|---|---|
| `AS` | Amsterdam |
| `AT` | Athens |
| `AU` | Australia (ASX) |
| `BA` | Buenos Aires |
| `BK` | Thailand |
| `BR` | Brussels |
| `BUD` | Budapest |
| `CM` | Colombo |
| `CO` | Copenhagen |
| `DU` | Dusseldorf |
| `EGX` | Egypt |
| `F` | Frankfurt / Xetra composite |
| `HA` | Hanover |
| `HE` | Helsinki |
| `HK` | Hong Kong |
| `HM` | Hamburg |
| `IR` | Irish Stock Exchange |
| `JK` | Jakarta |
| `JSE` | Johannesburg |
| `KAR` | Karachi |
| `KLSE` | Malaysia |
| `KO` | Korea (KOSPI) |
| `KQ` | Korea (KOSDAQ) |
| `LIM` | Lima |
| `LS` | Lisbon |
| `LSE` | London Stock Exchange |
| `LU` | Luxembourg |
| `MC` | Madrid |
| `MU` | Munich |
| `MX` | Mexico |
| `NEO` | Cboe Canada |
| `NSE` | National Stock Exchange of India |
| `OL` | Oslo |
| `PA` | Paris |
| `PR` | Prague |
| `PSE` | Philippines |
| `RO` | Bucharest |
| `SA` | Sao Paulo |
| `SHE` | Shenzhen |
| `SHG` | Shanghai |
| `SN` | Santiago |
| `ST` | Stockholm |
| `STU` | Stuttgart |
| `SW` | Switzerland |
| `TA` | Tel Aviv |
| `TO` | Toronto |
| `TW` | Taiwan |
| `TWO` | Taiwan OTC |
| `US` | United States (NYSE, NASDAQ, OTC) |
| `V` | TSX Venture |
| `VI` | Vienna |
| `VN` | Vietnam |
| `WAR` | Warsaw |
| `XBOT` | Cboe BZX |
| `XETRA` | Xetra |

Non-venue codes group instruments that are not tied to a single listing
venue:

| Code | Market |
|---|---|
| `CC` | Cryptocurrencies (e.g. `BTC-USD.CC`) |
| `FOREX` | Foreign exchange pairs (e.g. `EURUSD.FOREX`) |
| `GBOND` | Government bonds |
| `INDX` | Indices |

Crypto pairs use `BASE-QUOTE.CC`, e.g. `BTC-USD.CC`, `ETH-USD.CC`. FX pairs use `BASEQUOTE.FOREX`, e.g. `EURUSD.FOREX`.

### US Treasury series and tenors

`/ust/` is addressed by series rather than ticker. Pass `series` to choose one
or more, then `tenor` or `rate_type` to narrow within them.

| `series` | Table | Keyed by | Accepted values |
|---|---|---|---|
| `bill` | `ust_bill_rates` | `tenor` | `4WK`, `6WK`, `8WK`, `13WK`, `17WK`, `26WK`, `52WK` |
| `yield` | `ust_yield_rates` | `tenor` | `1M`, `1.5M`, `2M`, `3M`, `4M`, `6M`, `1Y`, `2Y`, `3Y`, `5Y`, `7Y`, `10Y`, `20Y`, `30Y` |
| `real_yield` | `ust_real_yield_rates` | `tenor` | `5Y`, `7Y`, `10Y`, `20Y`, `30Y` |
| `long_term` | `ust_long_term_rates` | `rate_type` | `BC_20year`, `Over_10_Years`, `Real_Rate` |

`tenor` applies only to `bill`, `yield` and `real_yield`; `rate_type` applies
only to `long_term`. Both are validated, not ignored:

- A key that matches none of the selected series returns `400` — for example
  `series=long_term&tenor=13WK` or `series=bill&rate_type=BC_20year`.
- A value outside the accepted list returns `400` naming the accepted values.

Use a value from your selected series' row above.

## Querying

### Filtering

Filters combine with AND. `ticker` / `tickers` take precedence — when either is
present, `exchange` is ignored. When neither is given, `exchange` defaults to
`US`.

| Filter group | Parameters |
|---|---|
| Instrument | `ticker`, `tickers` |
| Venue / class | `exchange`, `asset_type` |
| Date | `start_date`, `end_date`, `year`, `month` |
| Price | `open_min`, `open_max`, `close_min`, `close_max` |
| Volume | `volume_min`, `volume_max` |

```bash
# One instrument, one year
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/?ticker=BP.LSE&year=2026"

# Several instruments at once
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/?tickers=AAPL.US,MSFT.US,NVDA.US&year=2026"

# A whole venue over a date range
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/?exchange=LSE&start_date=2026-11-01&end_date=2026-11-20"
```

### Pagination

`per_page` sets the rows per response (default `1000`, maximum `5000`); `page`
selects the slice. The envelope reports the full match count.

```bash
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/?ticker=AAPL.US&year=2026&per_page=2&page=2"
```

```json
{
  "data": [ "...2 rows..." ],
  "total": 224,
  "page": 2,
  "per_page": 2,
  "total_pages": 112,
  "has_next": true,
  "has_prev": true
}
```

Walk pages while `has_next` is `true`. `total` counts every matching row, not
just the current page.

### Sorting

`sort_by` accepts `date`, `open`, `high`, `low`, `close` or `volume`.
`sort_order` is `asc` or `desc`; the default is `date` descending.

```bash
# Lowest-volume days first
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/?ticker=AAPL.US&year=2026&sort_by=volume&sort_order=asc&per_page=2"
```

### Performance

Payload grows with the date window; latency stays roughly flat. Measured on
UAT for `AAPL.US`:

| Window | Filter | Rows |
|---|---|---|
| Last week | `start_date=2026-11-17&end_date=2026-11-24` | 5 |
| Last month | `start_date=2026-10-24&end_date=2026-11-24` | 21 |
| Last year | `start_date=2025-11-24&end_date=2026-11-24` | 250 |
| This year | `year=2026` | 224 |
| Full history | `start_date=2000-01-01&end_date=2026-11-24` | 6,763 |

Every query above answered in 0.04–0.10 s — the cost is the response size, not
the query. Full history is roughly 1,350× the rows of a one-week question.

Naming tickers is far faster than filtering a whole venue, and venue-wide scans
combined with `asset_type` can exceed the request timeout.

See [Good practices](#good-practices) for choosing the window, the ticker
format and key placement.

## Good practices

### Derive the date window from the question

Never default to `start_date=2000-01-01`. Set the window from what was asked:

| The question | Use |
|---|---|
| "last week" | `start_date` = today − 7 days, `end_date` = today |
| "last month" | `start_date` = today − 30 days |
| "last year" | `start_date` = today − 365 days |
| "this year" / "YTD" | `year=<current year>` |
| "latest close" | `start_date` = `end_date` = the last trading day |

Wrong — 6,763 rows to answer a one-week question:

```bash
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/?ticker=AAPL.US&start_date=2000-01-01&end_date=2026-11-24"
```

Right — 5 rows:

```bash
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/?ticker=AAPL.US&start_date=2026-11-17&end_date=2026-11-24"
```

### `per_page` is a row cap, not a time window

`per_page` slices the response; `total` still counts every matching row. Raising
it to `5000` does not bound the period being asked about — only the dates do.

Wrong — unbounded, at maximum page size:

```bash
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/?ticker=AAPL.US&per_page=5000"
```

Right — the dates do the limiting:

```bash
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/?ticker=AAPL.US&start_date=2026-11-23&end_date=2026-11-23"
```

### Always suffix the ticker with `.EXCHANGE`

Include `.US`. The suffix is required — a bare ticker returns
`400 {"detail": "Ticker 'AZN' must include exchange (e.g., AZN.US)"}`.

| Instrument | Form | Example |
|---|---|---|
| Equity, ETF, index | `TICKER.CODE` | `AAPL.US`, `BP.LSE`, `AEX.INDX` |
| Crypto | `BASE-QUOTE.CC` | `BTC-USD.CC`, `ETH-USD.CC` |
| FX | `BASEQUOTE.FOREX` | `EURUSD.FOREX` |
| Government bond | `TICKER.GBOND` | `AU10Y.GBOND` |
| Commodity | bare symbol, no suffix | `LGOc3`, `NICKEL` |

Wrong — rejected with `400`:

```bash
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/?ticker=AZN&year=2026"
```

Right:

```bash
curl -H "X-API-Key: YOUR-API-KEY" \
  "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/?ticker=AZN.LSE&year=2026"
```

### Keep the key in the query string, never on the path

Prefer the `X-API-Key` header. When using `?api_key=`, it is an ordinary
parameter: every addition after the first joins with `&`, never a second `?`.

Wrong — the second `?` truncates the query and the request returns `401`:

```bash
curl "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/?ticker=AAPL.US&year=2026?api_key=YOUR-API-KEY"
```

Right:

```bash
curl "https://ohlcv-api-uat-2r464mi4sq-nw.a.run.app/ohlcv/?ticker=AAPL.US&year=2026&api_key=YOUR-API-KEY"
```

A missing key and an unknown key return the same body,
`401 {"detail":"Invalid or missing API key"}`, so check placement before
assuming the key itself is wrong.

## Errors

Failures return a JSON body with a `detail` field.

```json
{ "detail": "Invalid or missing API key" }
```

| Status | Meaning | Typical cause |
|---|---|---|
| `400` | Bad request | Invalid parameter combination, e.g. `realtime=true` without a ticker, or a ticker missing its `.EXCHANGE` suffix |
| `401` | Unauthorized | Missing or unknown API key |
| `404` | Not found | Unknown ticker, or no data in the requested window |
| `422` | Validation error | Parameter failed validation, e.g. unknown `sort_by` value |
| `502` | Upstream error | Real-time provider returned an error |
| `504` | Upstream timeout | Real-time provider did not respond in time |

Validation errors list each failing parameter:

```json
{
  "detail": [
    {
      "type": "string_pattern_mismatch",
      "loc": ["query", "sort_by"],
      "msg": "String should match pattern '^(date|volume|close|open|high|low)$'",
      "input": "bogus"
    }
  ]
}
```

An empty `data` array with `total: 0` is **not** an error — the filters simply
matched nothing. That is how a delisted instrument appears when you query its
last trading day.
