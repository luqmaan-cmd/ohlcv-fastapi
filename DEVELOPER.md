# OHLCV Data API — Developer Reference

REST API for accessing OHLCV (Open, High, Low, Close, Volume) financial data with batch queries and S&P 500 enriched endpoints.

## Base URL

| Environment | URL |
|-------------|-----|
| **Production** | `https://ohlcv-api-832081557693.europe-west2.run.app` |
| Local | `http://localhost:8001` |

## Authentication

All endpoints require an API key passed as a query parameter.

| Parameter | Value |
|-----------|-------|
| `api_key` | `YOUR_API_KEY` |

**Example:**
```
https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/?api_key=YOUR_API_KEY
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Invalid or missing API key"
}
```

---

## List OHLCV Data

Returns paginated OHLCV records with filtering and sorting options. Supports batch queries via the `tickers` parameter.

**Endpoint:** `GET /ohlcv/`

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `ticker` | string | - | Single ticker symbol (e.g., `AAPL`) |
| `tickers` | string | - | Comma-separated tickers (e.g., `AAPL,MSFT,GOOGL`) |
| `asset_isin` | string | - | Single ISIN code |
| `asset_isins` | string | - | Comma-separated ISIN codes |
| `start_date` | date | - | Start date filter (YYYY-MM-DD) |
| `end_date` | date | - | End date filter (YYYY-MM-DD) |
| `year` | integer | - | Filter by year (1900-2100) |
| `month` | integer | - | Filter by month (1-12) |
| `open_min` | decimal | - | Minimum open price |
| `open_max` | decimal | - | Maximum open price |
| `close_min` | decimal | - | Minimum close price |
| `close_max` | decimal | - | Maximum close price |
| `volume_min` | integer | - | Minimum volume |
| `volume_max` | integer | - | Maximum volume |
| `sort_by` | string | `date` | Sort field: `date`, `volume`, `close`, `open`, `high`, `low` |
| `sort_order` | string | `desc` | Sort order: `asc`, `desc` |
| `page` | integer | `1` | Page number (min: 1) |
| `per_page` | integer | `1000` | Records per page (min: 1, max: 5000) |

### Example Request — Single Ticker

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/?api_key=YOUR_API_KEY&ticker=AAPL&start_date=2026-05-01&end_date=2026-05-07&sort_by=volume&sort_order=desc&page=1&per_page=5"
```

### Example Request — Batch Multiple Tickers

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/?api_key=YOUR_API_KEY&tickers=AAPL,MSFT&start_date=2026-05-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=3"
```

### Example Response

```json
{
  "data": [
    {
      "ticker": "MSFT",
      "date": "2026-05-07",
      "open": 420.11,
      "high": 427.98,
      "low": 418.76,
      "close": 420.77,
      "adjusted_close": 420.77,
      "volume": 33917670,
      "asset_isin": "US5949181045",
      "id": "c60b9d4f-55ad-435e-b706-8bbddc6f5f55",
      "created_at": "2026-05-08T02:26:05.444586",
      "updated_at": "2026-05-08T02:26:05.444586"
    },
    {
      "ticker": "AAPL",
      "date": "2026-05-07",
      "open": 289.27,
      "high": 292.13,
      "low": 285.78,
      "close": 287.44,
      "adjusted_close": 287.44,
      "volume": 40410371,
      "asset_isin": "US0378331005",
      "id": "b7ed13ca-94fb-4ac3-a952-bb46febe0a4b",
      "created_at": "2026-05-08T02:02:41.827964",
      "updated_at": "2026-05-08T02:02:41.827964"
    },
    {
      "ticker": "AAPL",
      "date": "2026-05-06",
      "open": 281.92,
      "high": 288.03,
      "low": 281.07,
      "close": 287.51,
      "adjusted_close": 287.51,
      "volume": 58336100,
      "asset_isin": "US0378331005",
      "id": "34b7f530-2d8c-467b-8d2c-bb24a83f1c4d",
      "created_at": "2026-05-07T02:06:10.132570",
      "updated_at": "2026-05-08T02:02:41.827964"
    }
  ],
  "total": 10,
  "page": 1,
  "per_page": 3,
  "total_pages": 4,
  "has_next": true,
  "has_prev": false
}
```

---

## Get Latest OHLCV

### Single Ticker

Returns the most recent OHLCV record for a given ticker.

**Endpoint:** `GET /ohlcv/latest/{ticker}`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | Ticker symbol (e.g., `AAPL`) |

#### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/latest/AAPL?api_key=YOUR_API_KEY"
```

#### Example Response

```json
{
  "ticker": "AAPL",
  "date": "2026-05-07",
  "open": 289.27,
  "high": 292.13,
  "low": 285.78,
  "close": 287.44,
  "adjusted_close": 287.44,
  "volume": 40410371,
  "asset_isin": "US0378331005",
  "id": "b7ed13ca-94fb-4ac3-a952-bb46febe0a4b",
  "created_at": "2026-05-08T02:02:41.827964",
  "updated_at": "2026-05-08T02:02:41.827964"
}
```

### Batch / All Tickers

Returns the most recent OHLCV record for one or more tickers in a single request. If no tickers are specified, returns the latest record for **all** tickers in the database.

**Endpoint:** `GET /ohlcv/latest/`

> **Note:** This endpoint must be called with the trailing slash. Without it, FastAPI will route the request to `GET /ohlcv/latest/{ticker}` and treat the query string as a path parameter.

> **URL Pattern — Batch vs Single Ticker:**
>
> ✅ **Batch (multiple tickers):** `GET /ohlcv/latest/?tickers=AAPL,MSFT,GOOGL`
>
> ✅ **All tickers:** `GET /ohlcv/latest/`
>
> ✅ **Single ticker (path param):** `GET /ohlcv/latest/AAPL`
>
> ❌ **Wrong:** `GET /ohlcv/latest/AAPL,MSFT` — commas not allowed in path params
>
> ❌ **Wrong:** `GET /ohlcv/latest?ticker=AAPL` — no `ticker` query param on this endpoint

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tickers` | string | - | Comma-separated ticker symbols (e.g., `AAPL,MSFT,GOOGL`). If omitted, returns latest for all ~12,500 tickers. |

#### Example Request — Specific Tickers (Batch)

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/latest/?api_key=YOUR_API_KEY&tickers=AAPL,MSFT,GOOGL"
```

#### Example Response — Specific Tickers

```json
{
  "data": [
    {
      "ticker": "AAPL",
      "date": "2026-05-07",
      "open": 289.27,
      "high": 292.13,
      "low": 285.78,
      "close": 287.44,
      "adjusted_close": 287.44,
      "volume": 40410371,
      "asset_isin": "US0378331005",
      "id": "b7ed13ca-94fb-4ac3-a952-bb46febe0a4b",
      "created_at": "2026-05-08T02:02:41.827964",
      "updated_at": "2026-05-08T02:02:41.827964"
    },
    {
      "ticker": "GOOGL",
      "date": "2026-05-07",
      "open": 399.995,
      "high": 400.1,
      "low": 392.68,
      "close": 397.99,
      "adjusted_close": 397.99,
      "volume": 22403998,
      "asset_isin": "US02079K3059",
      "id": "fa557734-4a27-4e10-a485-894d73580693",
      "created_at": "2026-05-08T02:18:10.054961",
      "updated_at": "2026-05-08T02:18:10.054961"
    },
    {
      "ticker": "MSFT",
      "date": "2026-05-07",
      "open": 420.11,
      "high": 427.98,
      "low": 418.76,
      "close": 420.77,
      "adjusted_close": 420.77,
      "volume": 33917670,
      "asset_isin": "US5949181045",
      "id": "c60b9d4f-55ad-435e-b706-8bbddc6f5f55",
      "created_at": "2026-05-08T02:26:05.444586",
      "updated_at": "2026-05-08T02:26:05.444586"
    }
  ],
  "count": 3
}
```

#### Example Request — All Tickers

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/latest/?api_key=YOUR_API_KEY"
```

> **Warning:** Omitting the `tickers` parameter returns the latest record for every ticker in the database (~12,500 records). The response can be several MB. Use with caution in bandwidth-constrained environments.

---

## S&P 500 Constituents

### List S&P 500 Constituents

Returns paginated list of S&P 500 constituents enriched with metadata from the `assets` table (ISIN, GIC sector, description, country).

**Endpoint:** `GET /sp500/`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `sector` | string | - | Filter by GIC sector (e.g., `Technology`, `Healthcare`, `Communication Services`) |
| `is_active` | boolean | - | Filter by active status (`true`/`false`) |
| `page` | integer | `1` | Page number (min: 1) |
| `per_page` | integer | `1000` | Records per page (min: 1, max: 5000) |

#### Example Request — All Constituents

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/?api_key=YOUR_API_KEY&page=1&per_page=5"
```

#### Example Request — Filter by Sector

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/?api_key=YOUR_API_KEY&sector=Technology&per_page=5"
```

#### Example Response

```json
{
  "data": [
    {
      "ticker": "A",
      "name": "Agilent Technologies Inc",
      "sector": "Healthcare",
      "industry": "Diagnostics & Research",
      "weight": 0.0005,
      "is_active": true,
      "isin": "US00846U1016",
      "gic_sector": "Health Care",
      "description": "Agilent Technologies, Inc. provides application focused solutions to the life sciences, diagnostics, and applied chemical markets worldwide...",
      "country": "USA"
    },
    {
      "ticker": "AAPL",
      "name": "Apple Inc",
      "sector": "Technology",
      "industry": "Consumer Electronics",
      "weight": 0.0671,
      "is_active": true,
      "isin": "US0378331005",
      "gic_sector": "Information Technology",
      "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide...",
      "country": "USA"
    },
    {
      "ticker": "ABBV",
      "name": "AbbVie Inc",
      "sector": "Healthcare",
      "industry": "Drug Manufacturers - General",
      "weight": 0.0057,
      "is_active": true,
      "isin": "US00287Y1091",
      "gic_sector": "Health Care",
      "description": "AbbVie Inc., a research-based biopharmaceutical company, engages in the research and development, manufacturing, commercializing, and sale of medicines and therapies worldwide...",
      "country": "USA"
    }
  ],
  "total": 503,
  "page": 1,
  "per_page": 3,
  "total_pages": 168,
  "has_next": true,
  "has_prev": false
}
```

### Get Latest S&P 500 Data

Returns the most recent OHLCV record for S&P 500 constituents, sorted by index weight descending. Enriched with name, sector, industry, and weight.

**Endpoint:** `GET /sp500/latest/`

> **URL Pattern — Batch vs All Constituents:**
>
> ✅ **Batch (specific tickers):** `GET /sp500/latest/?tickers=AAPL,MSFT,GOOGL`
>
> ✅ **All constituents:** `GET /sp500/latest/`
>
> ❌ **Wrong:** `GET /sp500/latest/AAPL` — no single-ticker path param on this endpoint
>
> ❌ **Wrong:** `GET /sp500/latest?ticker=AAPL` — parameter is `tickers` (plural), not `ticker`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tickers` | string | - | Comma-separated S&P 500 tickers (e.g., `AAPL,MSFT,GOOGL`). If omitted, returns latest for all 503 constituents. |

#### Example Request — Batch Specific Tickers

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/latest/?api_key=YOUR_API_KEY&tickers=AAPL,MSFT,GOOGL"
```

#### Example Response

```json
{
  "data": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc",
      "sector": "Technology",
      "industry": "Consumer Electronics",
      "weight": 0.0671,
      "date": "2026-05-07",
      "open": 289.27,
      "high": 292.13,
      "low": 285.78,
      "close": 287.44,
      "adjusted_close": 287.44,
      "volume": 40410371,
      "asset_isin": "US0378331005"
    },
    {
      "ticker": "MSFT",
      "name": "Microsoft Corporation",
      "sector": "Technology",
      "industry": "Software - Infrastructure",
      "weight": 0.0497,
      "date": "2026-05-07",
      "open": 420.11,
      "high": 427.98,
      "low": 418.76,
      "close": 420.77,
      "adjusted_close": 420.77,
      "volume": 33917670,
      "asset_isin": "US5949181045"
    },
    {
      "ticker": "GOOGL",
      "name": "Alphabet Inc Class A",
      "sector": "Communication Services",
      "industry": "Internet Content & Information",
      "weight": 0.0369,
      "date": "2026-05-07",
      "open": 399.995,
      "high": 400.1,
      "low": 392.68,
      "close": 397.99,
      "adjusted_close": 397.99,
      "volume": 22403998,
      "asset_isin": "US02079K3059"
    }
  ],
  "count": 3
}
```

#### Example Request — All S&P 500 Constituents

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/latest/?api_key=YOUR_API_KEY"
```

Returns all 503 constituents with latest OHLCV data, sorted by index weight descending.

> **Note:** Ticker alias resolution is applied automatically. For example, if you request `FISV`, the API resolves it to `FI` in the OHLCV data via the `ticker_aliases` table.

---

## Historical OHLCV

### Get Batch Historical OHLCV for S&P 500 Constituents

Returns paginated historical OHLCV data for S&P 500 constituents in a single request. Verifies all requested tickers are active S&P 500 members and resolves ticker aliases automatically. Results are enriched with name, sector, industry, and weight.

If `tickers` is omitted, returns history for all active S&P 500 constituents.

**Endpoint:** `GET /sp500/history/`

> **URL Pattern — Batch vs All Constituents:**
>
> ✅ **Batch (specific tickers):** `GET /sp500/history/?tickers=AAPL,MSFT,GOOGL&start_date=2026-01-01`
>
> ✅ **All constituents:** `GET /sp500/history/?start_date=2026-01-01`
>
> ❌ **Wrong:** `GET /sp500/history/AAPL` — no single-ticker path param on this endpoint
>
> ❌ **Wrong:** `GET /sp500/history?ticker=AAPL` — parameter is `tickers` (plural), not `ticker`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tickers` | string | - | Comma-separated S&P 500 tickers (e.g., `AAPL,MSFT,GOOGL`). If omitted, returns history for all active constituents. |
| `start_date` | date | - | Start date filter (YYYY-MM-DD) |
| `end_date` | date | - | End date filter (YYYY-MM-DD) |
| `year` | integer | - | Filter by year (1900-2100) |
| `month` | integer | - | Filter by month (1-12) |
| `sort_by` | string | `date` | Sort field: `date`, `volume`, `close`, `open`, `high`, `low` |
| `sort_order` | string | `desc` | Sort order: `asc`, `desc` |
| `page` | integer | `1` | Page number (min: 1) |
| `per_page` | integer | `1000` | Records per page (min: 1, max: 5000) |

#### Example Request — Batch History for Multiple Companies

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/history/?api_key=YOUR_API_KEY&tickers=AAPL,MSFT,GOOGL&start_date=2026-04-01&end_date=2026-04-07&sort_by=date&sort_order=desc&page=1&per_page=10"
```

#### Example Response

```json
{
  "data": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc",
      "sector": "Technology",
      "industry": "Consumer Electronics",
      "weight": 0.0671,
      "date": "2026-04-07",
      "open": 256.16,
      "high": 256.2,
      "low": 245.7,
      "close": 253.5,
      "adjusted_close": 253.5,
      "volume": 62148000,
      "asset_isin": "US0378331005"
    },
    {
      "ticker": "GOOGL",
      "name": "Alphabet Inc Class A",
      "sector": "Communication Services",
      "industry": "Internet Content & Information",
      "weight": 0.0369,
      "date": "2026-04-07",
      "open": 302.73,
      "high": 305.63,
      "low": 297.72,
      "close": 305.46,
      "adjusted_close": 305.46,
      "volume": 23205400,
      "asset_isin": "US02079K3059"
    },
    {
      "ticker": "MSFT",
      "name": "Microsoft Corporation",
      "sector": "Technology",
      "industry": "Software - Infrastructure",
      "weight": 0.0497,
      "date": "2026-04-07",
      "open": 370.34,
      "high": 372.45,
      "low": 366.56,
      "close": 372.29,
      "adjusted_close": 372.29,
      "volume": 21443300,
      "asset_isin": "US5949181045"
    }
  ],
  "total": 12,
  "page": 1,
  "per_page": 10,
  "total_pages": 2,
  "has_next": true,
  "has_prev": false
}
```

#### Error Response — Invalid Ticker

```json
{
  "detail": "Ticker(s) not active S&P 500 constituents: FAKE"
}
```

#### Example Request — All S&P 500 Constituents

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/history/?api_key=YOUR_API_KEY&start_date=2026-05-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=10"
```

Returns paginated historical OHLCV data for all active S&P 500 constituents within the specified date range. Ticker alias resolution is applied automatically.

---

## ETF Data

### List ETF OHLCV Data

Returns paginated OHLCV records for ETFs only. Only returns data for tickers that exist in `etf_index_assets` with `type='etf'`.

**Endpoint:** `GET /etf/`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `ticker` | string | - | Single ETF ticker (e.g., `SPY`) |
| `tickers` | string | - | Comma-separated ETF tickers (e.g., `SPY,QQQ,IWM`) |
| `start_date` | date | - | Start date filter (YYYY-MM-DD) |
| `end_date` | date | - | End date filter (YYYY-MM-DD) |
| `year` | integer | - | Filter by year (1900-2100) |
| `month` | integer | - | Filter by month (1-12) |
| `open_min` | decimal | - | Minimum open price |
| `open_max` | decimal | - | Maximum open price |
| `close_min` | decimal | - | Minimum close price |
| `close_max` | decimal | - | Maximum close price |
| `volume_min` | integer | - | Minimum volume |
| `volume_max` | integer | - | Maximum volume |
| `sort_by` | string | `date` | Sort field: `date`, `volume`, `close`, `open`, `high`, `low` |
| `sort_order` | string | `desc` | Sort order: `asc`, `desc` |
| `page` | integer | `1` | Page number (min: 1) |
| `per_page` | integer | `1000` | Records per page (min: 1, max: 5000) |

#### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/etf/?api_key=YOUR_API_KEY&ticker=AAAA&per_page=3"
```

#### Example Response

```json
{
  "data": [
    {
      "id": "b9ea446a-...",
      "ticker": "AAAA",
      "date": "2026-05-12",
      "open": "29.9400",
      "high": "29.9487",
      "low": "29.8600",
      "close": "29.9487",
      "adjusted_close": "29.9487",
      "volume": 4617,
      "created_at": "2026-05-13T15:16:55.809181",
      "updated_at": "2026-05-13T15:16:55.809181"
    }
  ],
  "total": 208,
  "page": 1,
  "per_page": 3,
  "total_pages": 70,
  "has_next": true,
  "has_prev": false
}
```

### Get Latest ETF Data

#### Single ETF

Returns the most recent OHLCV record for a single ETF, enriched with asset metadata.

**Endpoint:** `GET /etf/latest/{ticker}`

##### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | ETF ticker symbol (e.g., `SPY`) |

##### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/etf/latest/SPY?api_key=YOUR_API_KEY"
```

##### Example Response

```json
{
  "ticker": "SPY",
  "name": "SPDR S&P 500 ETF Trust",
  "exchange": "US",
  "type": "etf",
  "isin": null,
  "currency": "USD",
  "date": "2026-05-12",
  "open": "736.8900",
  "high": "738.8400",
  "low": "731.8300",
  "close": "738.1800",
  "adjusted_close": "738.1800",
  "volume": 52768657
}
```

#### Batch / All ETFs

Returns the most recent OHLCV record for one or more ETFs. If no tickers are specified, returns the latest record for **all** ETFs.

**Endpoint:** `GET /etf/latest/`

> **Note:** This endpoint must be called with the trailing slash. Without it, FastAPI will route the request to `GET /etf/latest/{ticker}`.

##### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tickers` | string | - | Comma-separated ETF tickers (e.g., `SPY,QQQ,IWM`). If omitted, returns latest for all ~5,500 ETFs. |

##### Example Request — Specific ETFs

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/etf/latest/?api_key=YOUR_API_KEY&tickers=SPY,QQQ,IWM"
```

##### Example Response

```json
{
  "data": [
    {
      "ticker": "IWM",
      "name": "iShares Russell 2000 ETF",
      "exchange": "US",
      "type": "etf",
      "isin": null,
      "currency": "USD",
      "date": "2026-05-12",
      "open": "284.0400",
      "high": "284.0600",
      "low": "278.2900",
      "close": "282.5700",
      "adjusted_close": "282.5700",
      "volume": 26076705
    },
    {
      "ticker": "QQQ",
      "name": "Invesco QQQ Trust",
      "exchange": "US",
      "type": "etf",
      "isin": null,
      "currency": "USD",
      "date": "2026-05-12",
      "open": "708.1750",
      "high": "710.1800",
      "low": "696.6600",
      "close": "707.2400",
      "adjusted_close": "707.2400",
      "volume": 43812655
    },
    {
      "ticker": "SPY",
      "name": "SPDR S&P 500 ETF Trust",
      "exchange": "US",
      "type": "etf",
      "isin": null,
      "currency": "USD",
      "date": "2026-05-12",
      "open": "736.8900",
      "high": "738.8400",
      "low": "731.8300",
      "close": "738.1800",
      "adjusted_close": "738.1800",
      "volume": 52768657
    }
  ],
  "count": 3
}
```

##### Example Request — All ETFs

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/etf/latest/?api_key=YOUR_API_KEY"
```

> **Warning:** Omitting the `tickers` parameter returns the latest record for every ETF in the database (~5,500 records). The response can be several MB. Use with caution in bandwidth-constrained environments.

---

## Index Data

### List Index OHLCV Data

Returns paginated OHLCV records for indices only. Only returns data for tickers that exist in `etf_index_assets` with `type='index'`.

**Endpoint:** `GET /index/`

#### Query Parameters

Same as `GET /etf/` — see [ETF Query Parameters](#list-etf-ohlcv-data) for the full list. The `ticker`/`tickers` parameters accept index symbols (e.g., `GSPC` for S&P 500, `DJI` for Dow Jones).

> **Note:** Index tickers in this API do **not** include the `^` prefix. For example, use `GSPC` instead of `^GSPC`.

#### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/index/?api_key=YOUR_API_KEY&tickers=GSPC,DJI&start_date=2026-05-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=5"
```

#### Example Response

```json
{
  "data": [
    {
      "id": "e5f6a7b8-...",
      "ticker": "GSPC",
      "date": "2026-05-13",
      "open": "7409.1200",
      "high": "7409.1200",
      "low": "7375.1300",
      "close": "7386.5000",
      "adjusted_close": "7386.5000",
      "volume": 446017255,
      "created_at": "2026-05-13T15:16:55.809181",
      "updated_at": "2026-05-13T15:16:55.809181"
    }
  ],
  "total": 10,
  "page": 1,
  "per_page": 5,
  "total_pages": 2,
  "has_next": true,
  "has_prev": false
}
```

### Get Latest Index Data

#### Single Index

Returns the most recent OHLCV record for a single index, enriched with asset metadata.

**Endpoint:** `GET /index/latest/{ticker}`

##### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | Index ticker symbol (e.g., `GSPC`) |

##### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/index/latest/GSPC?api_key=YOUR_API_KEY"
```

##### Example Response

```json
{
  "ticker": "GSPC",
  "name": "S&P 500 Index",
  "exchange": "INDX",
  "type": "index",
  "isin": null,
  "currency": "USD",
  "date": "2026-05-13",
  "open": "7409.1200",
  "high": "7409.1200",
  "low": "7375.1300",
  "close": "7386.5000",
  "adjusted_close": "7386.5000",
  "volume": 446017255
}
```

#### Batch / All Indices

Returns the most recent OHLCV record for one or more indices. If no tickers are specified, returns the latest record for **all** indices.

**Endpoint:** `GET /index/latest/`

> **Note:** This endpoint must be called with the trailing slash. Without it, FastAPI will route the request to `GET /index/latest/{ticker}`.

##### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tickers` | string | - | Comma-separated index tickers (e.g., `GSPC,DJI,IXIC`). If omitted, returns latest for all ~1,600 indices. |

##### Example Request — Specific Indices

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/index/latest/?api_key=YOUR_API_KEY&tickers=GSPC,DJI"
```

##### Example Request — All Indices

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/index/latest/?api_key=YOUR_API_KEY"
```

> **Warning:** Omitting the `tickers` parameter returns the latest record for every index in the database (~1,600 records).

---

## Government Bond Data

Dedicated endpoints for government bonds (US10Y, UK10Y, DE10Y…) with enriched metadata (name, exchange, type, currency, country). Supports country filtering via `country` (single) and `countries` (comma-separated) parameters.

### List Government Bond OHLCV Data

Returns paginated OHLCV records for government bonds only. Only returns data for tickers that exist in `gov_bond_assets`. Supports filtering by ticker(s) and country/countries.

**Endpoint:** `GET /gov-bond/`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `ticker` | string | - | Single government bond ticker (e.g., `US10Y`) |
| `tickers` | string | - | Comma-separated government bond tickers (e.g., `US10Y,UK10Y,DE10Y`) |
| `country` | string | - | Filter by single country code (e.g., `US`, `DE`, `JP`) |
| `countries` | string | - | Comma-separated country codes (e.g., `US,DE,JP`) |
| `start_date` | date | - | Start date filter (YYYY-MM-DD) |
| `end_date` | date | - | End date filter (YYYY-MM-DD) |
| `year` | integer | - | Filter by year (1900-2100) |
| `month` | integer | - | Filter by month (1-12) |
| `open_min` | decimal | - | Minimum open price |
| `open_max` | decimal | - | Maximum open price |
| `close_min` | decimal | - | Minimum close price |
| `close_max` | decimal | - | Maximum close price |
| `volume_min` | integer | - | Minimum volume |
| `volume_max` | integer | - | Maximum volume |
| `sort_by` | string | `date` | Sort field: `date`, `volume`, `close`, `open`, `high`, `low` |
| `sort_order` | string | `desc` | Sort order: `asc`, `desc` |
| `page` | integer | `1` | Page number (min: 1) |
| `per_page` | integer | `1000` | Records per page (min: 1, max: 5000) |

#### Example Request — Single Ticker

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/?api_key=YOUR_API_KEY&ticker=US10Y&start_date=2026-05-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=5"
```

#### Example Request — Filter by Country

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/?api_key=YOUR_API_KEY&countries=US,DE,JP&start_date=2026-05-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=5"
```

#### Example Response

```json
{
  "data": [
    {
      "id": "a1b2c3d4-...",
      "ticker": "US10Y",
      "date": "2026-05-07",
      "open": "4.2800",
      "high": "4.3100",
      "low": "4.2600",
      "close": "4.2900",
      "adjusted_close": "4.2900",
      "volume": 0,
      "created_at": "2026-05-08T02:00:00.000000",
      "updated_at": "2026-05-08T02:00:00.000000"
    }
  ],
  "total": 5,
  "page": 1,
  "per_page": 5,
  "total_pages": 1,
  "has_next": false,
  "has_prev": false
}
```

### Get Latest Government Bond Data

#### Single Government Bond

Returns the most recent OHLCV record for a single government bond, enriched with asset metadata.

**Endpoint:** `GET /gov-bond/latest/{ticker}`

##### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | Government bond ticker symbol (e.g., `US10Y`) |

##### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest/US10Y?api_key=YOUR_API_KEY"
```

##### Example Response

```json
{
  "ticker": "US10Y",
  "name": "United States 10-Year Bond",
  "exchange": "GBOND",
  "type": "government_bond",
  "currency": "USD",
  "country": "US",
  "date": "2026-05-13",
  "open": "4.2800",
  "high": "4.3100",
  "low": "4.2600",
  "close": "4.2900",
  "adjusted_close": "4.2900",
  "volume": 0
}
```

##### Error Response — Ticker Not Found

```json
{
  "detail": "No government bond found with ticker: INVALID"
}
```

#### Batch / All Government Bonds

Returns the most recent OHLCV record for one or more government bonds. If no tickers are specified, returns the latest record for **all** government bonds. Uses LATERAL joins for efficient per-ticker latest-row lookups.

**Endpoint:** `GET /gov-bond/latest/`

> **Note:** This endpoint must be called with the trailing slash. Without it, FastAPI will route the request to `GET /gov-bond/latest/{ticker}`.

> **URL Pattern — Batch vs Single Ticker:**
>
> ✅ **Batch (specific tickers):** `GET /gov-bond/latest/?tickers=US10Y,UK10Y,DE10Y`
>
> ✅ **Filter by country:** `GET /gov-bond/latest/?countries=US,DE,JP`
>
> ✅ **All government bonds:** `GET /gov-bond/latest/`
>
> ✅ **Single ticker (path param):** `GET /gov-bond/latest/US10Y`
>
> ❌ **Wrong:** `GET /gov-bond/latest/US10Y,UK10Y` — commas not allowed in path params

##### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tickers` | string | - | Comma-separated government bond tickers (e.g., `US10Y,UK10Y,DE10Y`). If omitted, returns latest for all 117 government bonds. |
| `country` | string | - | Filter by single country code (e.g., `US`, `DE`, `JP`) |
| `countries` | string | - | Comma-separated country codes (e.g., `US,DE,JP`) |

##### Example Request — Specific Government Bonds

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest/?api_key=YOUR_API_KEY&tickers=US10Y,UK10Y,DE10Y"
```

##### Example Response

```json
{
  "data": [
    {
      "ticker": "DE10Y",
      "name": "Germany 10-Year Bond",
      "exchange": "GBOND",
      "type": "government_bond",
      "currency": "EUR",
      "country": "DE",
      "date": "2026-05-13",
      "open": "2.5800",
      "high": "2.6000",
      "low": "2.5700",
      "close": "2.5900",
      "adjusted_close": "2.5900",
      "volume": 0
    },
    {
      "ticker": "UK10Y",
      "name": "United Kingdom 10-Year Bond",
      "exchange": "GBOND",
      "type": "government_bond",
      "currency": "GBP",
      "country": "UK",
      "date": "2026-05-13",
      "open": "4.4500",
      "high": "4.4800",
      "low": "4.4300",
      "close": "4.4600",
      "adjusted_close": "4.4600",
      "volume": 0
    },
    {
      "ticker": "US10Y",
      "name": "United States 10-Year Bond",
      "exchange": "GBOND",
      "type": "government_bond",
      "currency": "USD",
      "country": "US",
      "date": "2026-05-13",
      "open": "4.2800",
      "high": "4.3100",
      "low": "4.2600",
      "close": "4.2900",
      "adjusted_close": "4.2900",
      "volume": 0
    }
  ],
  "count": 3
}
```

##### Example Request — Filter by Country

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest/?api_key=YOUR_API_KEY&countries=US,DE,JP"
```

Returns the latest record for all government bonds from the specified countries.

##### Example Request — All Government Bonds

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest/?api_key=YOUR_API_KEY"
```

> **Warning:** Omitting the `tickers` parameter returns the latest record for every government bond in the database (117 records across 28 countries).

---

## Foreign Exchange (FX) Data

Dedicated endpoints for foreign exchange pairs (EURUSD, GBPUSD, USDJPY…) with enriched metadata (name, exchange, type, currency, base_currency, quote_currency). Supports filtering by `base_currency` and `quote_currency` parameters.

### List FX OHLCV Data

Returns paginated OHLCV records for foreign exchange pairs only. Only returns data for tickers that exist in `fx_assets`. Supports filtering by ticker(s), base_currency, and quote_currency.

**Endpoint:** `GET /fx/`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `ticker` | string | - | Single FX ticker (e.g., `EURUSD`) |
| `tickers` | string | - | Comma-separated FX tickers (e.g., `EURUSD,GBPUSD,USDJPY`) |
| `base_currency` | string | - | Filter by base currency code (e.g., `EUR`, `GBP`) |
| `quote_currency` | string | - | Filter by quote currency code (e.g., `USD`, `JPY`) |
| `start_date` | date | - | Start date filter (YYYY-MM-DD) |
| `end_date` | date | - | End date filter (YYYY-MM-DD) |
| `year` | integer | - | Filter by year (1900-2100) |
| `month` | integer | - | Filter by month (1-12) |
| `open_min` | decimal | - | Minimum open price |
| `open_max` | decimal | - | Maximum open price |
| `close_min` | decimal | - | Minimum close price |
| `close_max` | decimal | - | Maximum close price |
| `volume_min` | integer | - | Minimum volume |
| `volume_max` | integer | - | Maximum volume |
| `sort_by` | string | `date` | Sort field: `date`, `volume`, `close`, `open`, `high`, `low` |
| `sort_order` | string | `desc` | Sort order: `asc`, `desc` |
| `page` | integer | `1` | Page number (min: 1) |
| `per_page` | integer | `1000` | Records per page (min: 1, max: 5000) |

#### Example Request — Single Ticker

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/fx/?api_key=YOUR_API_KEY&ticker=EURUSD&start_date=2026-05-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=5"
```

#### Example Request — Filter by Base Currency

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/fx/?api_key=YOUR_API_KEY&base_currency=EUR&start_date=2026-05-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=5"
```

#### Example Request — Filter by Quote Currency

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/fx/?api_key=YOUR_API_KEY&quote_currency=USD&start_date=2026-05-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=5"
```

#### Example Response

```json
{
  "data": [
    {
      "id": "a1b2c3d4-...",
      "ticker": "EURUSD",
      "date": "2026-05-07",
      "open": "1.1320",
      "high": "1.1345",
      "low": "1.1298",
      "close": "1.1332",
      "adjusted_close": "1.1332",
      "volume": 0,
      "created_at": "2026-05-08T02:00:00.000000",
      "updated_at": "2026-05-08T02:00:00.000000"
    }
  ],
  "total": 5,
  "page": 1,
  "per_page": 5,
  "total_pages": 1,
  "has_next": false,
  "has_prev": false
}
```

### Get Latest FX Data

#### Single FX Pair

Returns the most recent OHLCV record for a single foreign exchange pair, enriched with asset metadata.

**Endpoint:** `GET /fx/latest/{ticker}`

##### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | FX ticker symbol (e.g., `EURUSD`) |

##### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/fx/latest/EURUSD?api_key=YOUR_API_KEY"
```

##### Example Response

```json
{
  "ticker": "EURUSD",
  "name": "EUR/USD",
  "exchange": "FX",
  "type": "currency",
  "currency": "USD",
  "base_currency": "EUR",
  "quote_currency": "USD",
  "date": "2026-05-13",
  "open": "1.1320",
  "high": "1.1345",
  "low": "1.1298",
  "close": "1.1332",
  "adjusted_close": "1.1332",
  "volume": 0
}
```

##### Error Response — Ticker Not Found

```json
{
  "detail": "No FX pair found with ticker: INVALID"
}
```

#### Batch / All FX Pairs

Returns the most recent OHLCV record for one or more foreign exchange pairs. If no tickers are specified, returns the latest record for **all** FX pairs. Uses LATERAL joins for efficient per-ticker latest-row lookups.

**Endpoint:** `GET /fx/latest/`

> **Note:** This endpoint must be called with the trailing slash. Without it, FastAPI will route the request to `GET /fx/latest/{ticker}`.

> **URL Pattern — Batch vs Single Ticker:**
>
> ✅ **Batch (specific tickers):** `GET /fx/latest/?tickers=EURUSD,GBPUSD,USDJPY`
>
> ✅ **Filter by base currency:** `GET /fx/latest/?base_currency=EUR`
>
> ✅ **Filter by quote currency:** `GET /fx/latest/?quote_currency=USD`
>
> ✅ **All FX pairs:** `GET /fx/latest/`
>
> ✅ **Single ticker (path param):** `GET /fx/latest/EURUSD`
>
> ❌ **Wrong:** `GET /fx/latest/EURUSD,GBPUSD` — commas not allowed in path params

##### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tickers` | string | - | Comma-separated FX tickers (e.g., `EURUSD,GBPUSD,USDJPY`). If omitted, returns latest for all ~948 FX pairs. |
| `base_currency` | string | - | Filter by base currency code (e.g., `EUR`, `GBP`) |
| `quote_currency` | string | - | Filter by quote currency code (e.g., `USD`, `JPY`) |

##### Example Request — Specific FX Pairs

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/fx/latest/?api_key=YOUR_API_KEY&tickers=EURUSD,GBPUSD,USDJPY"
```

##### Example Response

```json
{
  "data": [
    {
      "ticker": "EURUSD",
      "name": "EUR/USD",
      "exchange": "FX",
      "type": "currency",
      "currency": "USD",
      "base_currency": "EUR",
      "quote_currency": "USD",
      "date": "2026-05-13",
      "open": "1.1320",
      "high": "1.1345",
      "low": "1.1298",
      "close": "1.1332",
      "adjusted_close": "1.1332",
      "volume": 0
    },
    {
      "ticker": "GBPUSD",
      "name": "GBP/USD",
      "exchange": "FX",
      "type": "currency",
      "currency": "USD",
      "base_currency": "GBP",
      "quote_currency": "USD",
      "date": "2026-05-13",
      "open": "1.3210",
      "high": "1.3245",
      "low": "1.3198",
      "close": "1.3232",
      "adjusted_close": "1.3232",
      "volume": 0
    },
    {
      "ticker": "USDJPY",
      "name": "USD/JPY",
      "exchange": "FX",
      "type": "currency",
      "currency": "JPY",
      "base_currency": "USD",
      "quote_currency": "JPY",
      "date": "2026-05-13",
      "open": "145.2300",
      "high": "145.6700",
      "low": "144.8900",
      "close": "145.4500",
      "adjusted_close": "145.4500",
      "volume": 0
    }
  ],
  "count": 3
}
```

##### Example Request — Filter by Base Currency

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/fx/latest/?api_key=YOUR_API_KEY&base_currency=EUR"
```

Returns the latest record for all FX pairs where the base currency is EUR.

##### Example Request — All FX Pairs

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/fx/latest/?api_key=YOUR_API_KEY"
```

> **Warning:** Omitting the `tickers` parameter returns the latest record for every FX pair in the database (~948 records). The response can be several MB. Use with caution in bandwidth-constrained environments.

---

## UK Stock (FTSE 100) Data

Dedicated endpoints for UK stocks in the FTSE 100 index with enriched metadata (name, exchange, type, sector, industry, weight, isin, currency). Supports filtering by `sector` and `industry` parameters.

> **Case-sensitivity note:** UK tickers are **case-sensitive** and must be provided exactly as stored in the database (e.g., `AZN`, not `azn`).

### List UK Stock OHLCV Data

Returns paginated OHLCV records for UK stocks (FTSE 100) only. Only returns data for tickers that exist in `uk_assets`. Supports filtering by ticker(s), sector, and industry.

**Endpoint:** `GET /uk/`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `ticker` | string | - | Single UK ticker (e.g., `AZN`) |
| `tickers` | string | - | Comma-separated UK tickers (e.g., `AZN,SHEL,HSBA`) |
| `sector` | string | - | Filter by sector (e.g., `Healthcare`, `Energy`) |
| `industry` | string | - | Filter by industry (e.g., `Drug Manufacturers`, `Oil & Gas`) |
| `start_date` | date | - | Start date filter (YYYY-MM-DD) |
| `end_date` | date | - | End date filter (YYYY-MM-DD) |
| `year` | integer | - | Filter by year (1900-2100) |
| `month` | integer | - | Filter by month (1-12) |
| `open_min` | decimal | - | Minimum open price |
| `open_max` | decimal | - | Maximum open price |
| `close_min` | decimal | - | Minimum close price |
| `close_max` | decimal | - | Maximum close price |
| `volume_min` | integer | - | Minimum volume |
| `volume_max` | integer | - | Maximum volume |
| `sort_by` | string | `date` | Sort field: `date`, `volume`, `close`, `open`, `high`, `low` |
| `sort_order` | string | `desc` | Sort order: `asc`, `desc` |
| `page` | integer | `1` | Page number (min: 1) |
| `per_page` | integer | `1000` | Records per page (min: 1, max: 5000) |

#### Example Request — Single Ticker

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/uk/?api_key=YOUR_API_KEY&ticker=AZN&start_date=2026-05-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=5"
```

#### Example Request — Filter by Sector

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/uk/?api_key=YOUR_API_KEY&sector=Healthcare&start_date=2026-05-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=5"
```

#### Example Response

```json
{
  "data": [
    {
      "id": "a1b2c3d4-...",
      "ticker": "AZN",
      "date": "2026-05-07",
      "open": "12450.0000",
      "high": "12520.0000",
      "low": "12380.0000",
      "close": "12480.0000",
      "adjusted_close": "12480.0000",
      "volume": 3256789,
      "created_at": "2026-05-08T02:00:00.000000",
      "updated_at": "2026-05-08T02:00:00.000000"
    }
  ],
  "total": 5,
  "page": 1,
  "per_page": 5,
  "total_pages": 1,
  "has_next": false,
  "has_prev": false
}
```

### Get Latest UK Stock Data

#### Single UK Stock

Returns the most recent OHLCV record for a single UK stock, enriched with asset metadata.

**Endpoint:** `GET /uk/latest/{ticker}`

##### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | UK stock ticker symbol (e.g., `AZN`). Case-sensitive. |

##### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/uk/latest/AZN?api_key=YOUR_API_KEY"
```

##### Example Response

```json
{
  "ticker": "AZN",
  "name": "AstraZeneca PLC",
  "exchange": "LSE",
  "type": "stock",
  "sector": "Healthcare",
  "industry": "Drug Manufacturers - General",
  "weight": "0.075000",
  "isin": "GB0009895292",
  "currency": "GBP",
  "date": "2026-05-13",
  "open": "12450.0000",
  "high": "12520.0000",
  "low": "12380.0000",
  "close": "12480.0000",
  "adjusted_close": "12480.0000",
  "volume": 3256789
}
```

##### Error Response — Ticker Not Found

```json
{
  "detail": "No UK stock found with ticker: INVALID"
}
```

#### Batch / All UK Stocks

Returns the most recent OHLCV record for one or more UK stocks. If no tickers are specified, returns the latest record for **all** UK stocks. Uses LATERAL joins for efficient per-ticker latest-row lookups.

**Endpoint:** `GET /uk/latest/`

> **Note:** This endpoint must be called with the trailing slash. Without it, FastAPI will route the request to `GET /uk/latest/{ticker}`.

> **URL Pattern — Batch vs Single Ticker:**
>
> ✅ **Batch (specific tickers):** `GET /uk/latest/?tickers=AZN,SHEL,HSBA`
>
> ✅ **Filter by sector:** `GET /uk/latest/?sector=Healthcare`
>
> ✅ **Filter by industry:** `GET /uk/latest/?industry=Drug Manufacturers - General`
>
> ✅ **All UK stocks:** `GET /uk/latest/`
>
> ✅ **Single ticker (path param):** `GET /uk/latest/AZN`
>
> ❌ **Wrong:** `GET /uk/latest/AZN,SHEL` — commas not allowed in path params

##### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tickers` | string | - | Comma-separated UK tickers (e.g., `AZN,SHEL,HSBA`). If omitted, returns latest for all ~100 FTSE 100 stocks. |
| `sector` | string | - | Filter by sector (e.g., `Healthcare`, `Energy`) |
| `industry` | string | - | Filter by industry (e.g., `Drug Manufacturers`, `Oil & Gas`) |

##### Example Request — Specific UK Stocks

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/uk/latest/?api_key=YOUR_API_KEY&tickers=AZN,SHEL,HSBA"
```

##### Example Response

```json
{
  "data": [
    {
      "ticker": "AZN",
      "name": "AstraZeneca PLC",
      "exchange": "LSE",
      "type": "stock",
      "sector": "Healthcare",
      "industry": "Drug Manufacturers - General",
      "weight": "0.075000",
      "isin": "GB0009895292",
      "currency": "GBP",
      "date": "2026-05-13",
      "open": "12450.0000",
      "high": "12520.0000",
      "low": "12380.0000",
      "close": "12480.0000",
      "adjusted_close": "12480.0000",
      "volume": 3256789
    },
    {
      "ticker": "HSBA",
      "name": "HSBC Holdings PLC",
      "exchange": "LSE",
      "type": "stock",
      "sector": "Financial Services",
      "industry": "Banks - Diversified",
      "weight": "0.061200",
      "isin": "GB0005405286",
      "currency": "GBP",
      "date": "2026-05-13",
      "open": "856.4000",
      "high": "862.2000",
      "low": "851.6000",
      "close": "858.8000",
      "adjusted_close": "858.8000",
      "volume": 12456789
    },
    {
      "ticker": "SHEL",
      "name": "Shell PLC",
      "exchange": "LSE",
      "type": "stock",
      "sector": "Energy",
      "industry": "Oil & Gas Integrated",
      "weight": "0.089300",
      "isin": "GB00BP6MXD84",
      "currency": "GBP",
      "date": "2026-05-13",
      "open": "2780.0000",
      "high": "2795.0000",
      "low": "2765.0000",
      "close": "2788.0000",
      "adjusted_close": "2788.0000",
      "volume": 5678901
    }
  ],
  "count": 3
}
```

##### Example Request — Filter by Sector

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/uk/latest/?api_key=YOUR_API_KEY&sector=Healthcare"
```

Returns the latest record for all UK stocks in the Healthcare sector.

##### Example Request — All UK Stocks

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/uk/latest/?api_key=YOUR_API_KEY"
```

> **Warning:** Omitting the `tickers` parameter returns the latest record for every UK stock in the database (~100 FTSE 100 constituents, of which ~68 have price data).

---

## US Treasury Rate Data

Dedicated endpoints for US Treasury rates across four categories: bill rates, yield curve rates, real yield rates, and long-term rates. Each category provides paginated history, batch latest, and single-tenor latest endpoints.

> **Case-sensitivity note:** Long-term rate types (`BC_20year`, `Over_10_Years`, `Real_Rate`) are **case-sensitive** — they must be provided exactly as stored in the database. All other UST tenors (bill, real-yield, yield) are case-insensitive and automatically uppercased.

### Distinct Values

| Category | Filter | Valid Values |
|----------|--------|-------------|
| Bill | `tenor` | `4WK`, `6WK`, `8WK`, `13WK`, `17WK`, `26WK`, `52WK` |
| Long-Term | `rate_type` | `BC_20year`, `Over_10_Years`, `Real_Rate` *(case-sensitive)* |
| Real-Yield | `tenor` | `5Y`, `7Y`, `10Y`, `20Y`, `30Y` |
| Yield | `tenor` | `1M`, `1.5M`, `2M`, `3M`, `4M`, `6M`, `1Y`, `2Y`, `3Y`, `5Y`, `7Y`, `10Y`, `20Y`, `30Y` |

---

### List US Treasury Bill Rates

Returns paginated US Treasury bill rate records with filtering and sorting options. Supports filtering by tenor(s), date range, and discount/coupon bounds.

**Endpoint:** `GET /ust/bill/`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tenor` | string | - | Single tenor (e.g., `13WK`) |
| `tenors` | string | - | Comma-separated tenors (e.g., `4WK,13WK,26WK`) |
| `start_date` | date | - | Start date filter (YYYY-MM-DD) |
| `end_date` | date | - | End date filter (YYYY-MM-DD) |
| `discount_min` | decimal | - | Minimum discount rate |
| `discount_max` | decimal | - | Maximum discount rate |
| `coupon_min` | decimal | - | Minimum coupon equivalent rate |
| `coupon_max` | decimal | - | Maximum coupon equivalent rate |
| `sort_by` | string | `date` | Sort field: `date`, `discount`, `coupon`, `avg_discount`, `avg_coupon` |
| `sort_order` | string | `desc` | Sort order: `asc`, `desc` |
| `page` | integer | `1` | Page number (min: 1) |
| `per_page` | integer | `1000` | Records per page (min: 1, max: 5000) |

#### Example Request — Single Tenor

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ust/bill/?api_key=YOUR_API_KEY&tenor=13WK&start_date=2026-01-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=5"
```

#### Example Response

```json
{
  "data": [
    {
      "id": "a1b2c3d4-...",
      "date": "2026-05-07",
      "tenor": "13WK",
      "discount": "4.2650",
      "coupon": "4.3550",
      "avg_discount": "4.2650",
      "avg_coupon": "4.3550",
      "maturity_date": "2026-08-06",
      "cusip": "US912796ZG39",
      "created_at": "2026-05-08T02:00:00.000000",
      "updated_at": "2026-05-08T02:00:00.000000"
    }
  ],
  "total": 94,
  "page": 1,
  "per_page": 5,
  "total_pages": 19,
  "has_next": true,
  "has_prev": false
}
```

---

### Get Latest US Treasury Bill Rates

#### Single Tenor

Returns the most recent bill rate record for a single tenor.

**Endpoint:** `GET /ust/bill/latest/{tenor}`

##### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `tenor` | string | Bill tenor (e.g., `13WK`). Case-insensitive. |

##### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ust/bill/latest/13WK?api_key=YOUR_API_KEY"
```

##### Example Response

```json
{
  "tenor": "13WK",
  "date": "2026-05-07",
  "discount": "4.2650",
  "coupon": "4.3550",
  "avg_discount": "4.2650",
  "avg_coupon": "4.3550",
  "maturity_date": "2026-08-06",
  "cusip": "US912796ZG39"
}
```

##### Error Response — Tenor Not Found

```json
{
  "detail": "No US Treasury bill rate found for tenor: INVALID"
}
```

#### Batch / All Tenors

Returns the most recent bill rate record for one or more tenors. If no tenors are specified, returns the latest record for **all** bill tenors. Uses `DISTINCT ON` for efficient per-tenor latest-row lookups.

**Endpoint:** `GET /ust/bill/latest/`

> **Note:** This endpoint must be called with the trailing slash. Without it, FastAPI will route the request to `GET /ust/bill/latest/{tenor}`.

> **URL Pattern — Batch vs Single Tenor:**
>
> ✅ **Batch (specific tenors):** `GET /ust/bill/latest/?tenors=4WK,13WK,26WK`
>
> ✅ **All tenors:** `GET /ust/bill/latest/`
>
> ✅ **Single tenor (path param):** `GET /ust/bill/latest/13WK`
>
> ❌ **Wrong:** `GET /ust/bill/latest/4WK,13WK` — commas not allowed in path params

##### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tenors` | string | - | Comma-separated tenors (e.g., `4WK,13WK,26WK`). If omitted, returns latest for all 7 bill tenors. |

##### Example Request — Specific Tenors

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ust/bill/latest/?api_key=YOUR_API_KEY&tenors=4WK,13WK,26WK"
```

##### Example Response

```json
{
  "data": [
    {
      "tenor": "13WK",
      "date": "2026-05-07",
      "discount": "4.2650",
      "coupon": "4.3550",
      "avg_discount": "4.2650",
      "avg_coupon": "4.3550",
      "maturity_date": "2026-08-06",
      "cusip": "US912796ZG39"
    },
    {
      "tenor": "26WK",
      "date": "2026-05-07",
      "discount": "4.1900",
      "coupon": "4.3900",
      "avg_discount": "4.1900",
      "avg_coupon": "4.3900",
      "maturity_date": "2026-11-06",
      "cusip": "US912796ZH22"
    },
    {
      "tenor": "4WK",
      "date": "2026-05-07",
      "discount": "4.3400",
      "coupon": "4.4100",
      "avg_discount": "4.3400",
      "avg_coupon": "4.4100",
      "maturity_date": "2026-06-04",
      "cusip": "US912796ZF56"
    }
  ],
  "count": 3
}
```

##### Example Request — All Bill Tenors

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ust/bill/latest/?api_key=YOUR_API_KEY"
```

Returns the latest record for all 7 bill tenors.

---

### List US Treasury Long-Term Rates

Returns paginated US Treasury long-term rate records with filtering and sorting options. Supports filtering by rate type(s), date range, and rate bounds.

**Endpoint:** `GET /ust/long-term/`

> **Warning:** Long-term rate types are **case-sensitive**. Use exact values: `BC_20year`, `Over_10_Years`, `Real_Rate`.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `rate_type` | string | - | Single rate type (e.g., `BC_20year`) |
| `rate_types` | string | - | Comma-separated rate types (e.g., `BC_20year,Over_10_Years`) |
| `start_date` | date | - | Start date filter (YYYY-MM-DD) |
| `end_date` | date | - | End date filter (YYYY-MM-DD) |
| `rate_min` | decimal | - | Minimum rate |
| `rate_max` | decimal | - | Maximum rate |
| `sort_by` | string | `date` | Sort field: `date`, `rate`, `extrapolation_factor` |
| `sort_order` | string | `desc` | Sort order: `asc`, `desc` |
| `page` | integer | `1` | Page number (min: 1) |
| `per_page` | integer | `1000` | Records per page (min: 1, max: 5000) |

#### Example Request — Single Rate Type

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ust/long-term/?api_key=YOUR_API_KEY&rate_type=BC_20year&start_date=2026-01-01&sort_by=date&sort_order=desc&page=1&per_page=5"
```

#### Example Response

```json
{
  "data": [
    {
      "id": "d4e5f6a7-...",
      "date": "2026-05-07",
      "rate_type": "BC_20year",
      "rate": "4.7100",
      "extrapolation_factor": "1.0000",
      "created_at": "2026-05-08T02:00:00.000000",
      "updated_at": "2026-05-08T02:00:00.000000"
    }
  ],
  "total": 94,
  "page": 1,
  "per_page": 5,
  "total_pages": 19,
  "has_next": true,
  "has_prev": false
}
```

---

### Get Latest US Treasury Long-Term Rates

#### Single Rate Type

Returns the most recent long-term rate record for a single rate type.

**Endpoint:** `GET /ust/long-term/latest/{rate_type}`

> **Warning:** The `rate_type` path parameter is **case-sensitive**. Use exact values: `BC_20year`, `Over_10_Years`, `Real_Rate`.

##### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `rate_type` | string | Long-term rate type (e.g., `BC_20year`). Case-sensitive. |

##### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ust/long-term/latest/BC_20year?api_key=YOUR_API_KEY"
```

##### Example Response

```json
{
  "rate_type": "BC_20year",
  "date": "2026-05-07",
  "rate": "4.7100",
  "extrapolation_factor": "1.0000"
}
```

##### Error Response — Rate Type Not Found

```json
{
  "detail": "No US Treasury long-term rate found for rate type: invalid_type"
}
```

#### Batch / All Rate Types

Returns the most recent long-term rate record for one or more rate types. If no rate types are specified, returns the latest record for **all** long-term rate types. Uses `DISTINCT ON` for efficient per-rate-type latest-row lookups.

**Endpoint:** `GET /ust/long-term/latest/`

> **Note:** This endpoint must be called with the trailing slash. Without it, FastAPI will route the request to `GET /ust/long-term/latest/{rate_type}`.

> **Warning:** The `rate_types` query parameter is **case-sensitive**. Use exact values: `BC_20year`, `Over_10_Years`, `Real_Rate`.

##### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `rate_types` | string | - | Comma-separated rate types (e.g., `BC_20year,Over_10_Years`). If omitted, returns latest for all 3 long-term rate types. |

##### Example Request — Specific Rate Types

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ust/long-term/latest/?api_key=YOUR_API_KEY&rate_types=BC_20year,Over_10_Years"
```

##### Example Response

```json
{
  "data": [
    {
      "rate_type": "BC_20year",
      "date": "2026-05-07",
      "rate": "4.7100",
      "extrapolation_factor": "1.0000"
    },
    {
      "rate_type": "Over_10_Years",
      "date": "2026-05-07",
      "rate": "4.5300",
      "extrapolation_factor": "1.0000"
    }
  ],
  "count": 2
}
```

##### Example Request — All Long-Term Rate Types

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ust/long-term/latest/?api_key=YOUR_API_KEY"
```

Returns the latest record for all 3 long-term rate types.

---

### List US Treasury Real Yield Rates

Returns paginated US Treasury real yield rate records with filtering and sorting options. Supports filtering by tenor(s), date range, and rate bounds.

**Endpoint:** `GET /ust/real-yield/`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tenor` | string | - | Single tenor (e.g., `10Y`) |
| `tenors` | string | - | Comma-separated tenors (e.g., `5Y,10Y,30Y`) |
| `start_date` | date | - | Start date filter (YYYY-MM-DD) |
| `end_date` | date | - | End date filter (YYYY-MM-DD) |
| `rate_min` | decimal | - | Minimum rate |
| `rate_max` | decimal | - | Maximum rate |
| `sort_by` | string | `date` | Sort field: `date`, `rate` |
| `sort_order` | string | `desc` | Sort order: `asc`, `desc` |
| `page` | integer | `1` | Page number (min: 1) |
| `per_page` | integer | `1000` | Records per page (min: 1, max: 5000) |

#### Example Request — Single Tenor

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ust/real-yield/?api_key=YOUR_API_KEY&tenor=10Y&start_date=2026-01-01&sort_by=date&sort_order=desc&page=1&per_page=5"
```

#### Example Response

```json
{
  "data": [
    {
      "id": "b2c3d4e5-...",
      "date": "2026-05-07",
      "tenor": "10Y",
      "rate": "2.0800",
      "created_at": "2026-05-08T02:00:00.000000",
      "updated_at": "2026-05-08T02:00:00.000000"
    }
  ],
  "total": 94,
  "page": 1,
  "per_page": 5,
  "total_pages": 19,
  "has_next": true,
  "has_prev": false
}
```

---

### Get Latest US Treasury Real Yield Rates

#### Single Tenor

Returns the most recent real yield rate record for a single tenor.

**Endpoint:** `GET /ust/real-yield/latest/{tenor}`

##### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `tenor` | string | Real yield tenor (e.g., `10Y`). Case-insensitive. |

##### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ust/real-yield/latest/10Y?api_key=YOUR_API_KEY"
```

##### Example Response

```json
{
  "tenor": "10Y",
  "date": "2026-05-07",
  "rate": "2.0800"
}
```

##### Error Response — Tenor Not Found

```json
{
  "detail": "No US Treasury real yield rate found for tenor: INVALID"
}
```

#### Batch / All Tenors

Returns the most recent real yield rate record for one or more tenors. If no tenors are specified, returns the latest record for **all** real yield tenors. Uses `DISTINCT ON` for efficient per-tenor latest-row lookups.

**Endpoint:** `GET /ust/real-yield/latest/`

> **Note:** This endpoint must be called with the trailing slash. Without it, FastAPI will route the request to `GET /ust/real-yield/latest/{tenor}`.

##### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tenors` | string | - | Comma-separated tenors (e.g., `5Y,10Y,30Y`). If omitted, returns latest for all 5 real yield tenors. |

##### Example Request — Specific Tenors

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ust/real-yield/latest/?api_key=YOUR_API_KEY&tenors=5Y,10Y,30Y"
```

##### Example Response

```json
{
  "data": [
    {
      "tenor": "10Y",
      "date": "2026-05-07",
      "rate": "2.0800"
    },
    {
      "tenor": "30Y",
      "date": "2026-05-07",
      "rate": "2.4100"
    },
    {
      "tenor": "5Y",
      "date": "2026-05-07",
      "rate": "1.8300"
    }
  ],
  "count": 3
}
```

##### Example Request — All Real Yield Tenors

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ust/real-yield/latest/?api_key=YOUR_API_KEY"
```

Returns the latest record for all 5 real yield tenors.

---

### List US Treasury Yield Rates

Returns paginated US Treasury yield curve rate records with filtering and sorting options. Supports filtering by tenor(s), date range, and rate bounds.

**Endpoint:** `GET /ust/yield/`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tenor` | string | - | Single tenor (e.g., `10Y`) |
| `tenors` | string | - | Comma-separated tenors (e.g., `2Y,5Y,10Y,30Y`) |
| `start_date` | date | - | Start date filter (YYYY-MM-DD) |
| `end_date` | date | - | End date filter (YYYY-MM-DD) |
| `rate_min` | decimal | - | Minimum rate |
| `rate_max` | decimal | - | Maximum rate |
| `sort_by` | string | `date` | Sort field: `date`, `rate` |
| `sort_order` | string | `desc` | Sort order: `asc`, `desc` |
| `page` | integer | `1` | Page number (min: 1) |
| `per_page` | integer | `1000` | Records per page (min: 1, max: 5000) |

#### Example Request — Single Tenor with Date Range

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ust/yield/?api_key=YOUR_API_KEY&tenor=10Y&start_date=2026-01-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=5"
```

#### Example Response

```json
{
  "data": [
    {
      "id": "c3d4e5f6-...",
      "date": "2026-05-07",
      "tenor": "10Y",
      "rate": "4.2900",
      "created_at": "2026-05-08T02:00:00.000000",
      "updated_at": "2026-05-08T02:00:00.000000"
    }
  ],
  "total": 94,
  "page": 1,
  "per_page": 5,
  "total_pages": 19,
  "has_next": true,
  "has_prev": false
}
```

---

### Get Latest US Treasury Yield Rates

#### Single Tenor

Returns the most recent yield curve rate record for a single tenor.

**Endpoint:** `GET /ust/yield/latest/{tenor}`

##### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `tenor` | string | Yield tenor (e.g., `10Y`). Case-insensitive. |

##### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ust/yield/latest/10Y?api_key=YOUR_API_KEY"
```

##### Example Response

```json
{
  "tenor": "10Y",
  "date": "2026-05-07",
  "rate": "4.2900"
}
```

##### Error Response — Tenor Not Found

```json
{
  "detail": "No US Treasury yield rate found for tenor: INVALID"
}
```

#### Batch / All Tenors

Returns the most recent yield curve rate record for one or more tenors. If no tenors are specified, returns the latest record for **all** yield tenors. Uses `DISTINCT ON` for efficient per-tenor latest-row lookups.

**Endpoint:** `GET /ust/yield/latest/`

> **Note:** This endpoint must be called with the trailing slash. Without it, FastAPI will route the request to `GET /ust/yield/latest/{tenor}`.

##### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tenors` | string | - | Comma-separated tenors (e.g., `2Y,5Y,10Y,30Y`). If omitted, returns latest for all 14 yield tenors. |

##### Example Request — Specific Tenors

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ust/yield/latest/?api_key=YOUR_API_KEY&tenors=2Y,5Y,10Y,30Y"
```

##### Example Response

```json
{
  "data": [
    {
      "tenor": "10Y",
      "date": "2026-05-07",
      "rate": "4.2900"
    },
    {
      "tenor": "2Y",
      "date": "2026-05-07",
      "rate": "3.8800"
    },
    {
      "tenor": "30Y",
      "date": "2026-05-07",
      "rate": "4.5300"
    },
    {
      "tenor": "5Y",
      "date": "2026-05-07",
      "rate": "4.0600"
    }
  ],
  "count": 4
}
```

##### Example Request — All Yield Tenors

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ust/yield/latest/?api_key=YOUR_API_KEY"
```

Returns the latest record for all 14 yield tenors.

---

## SQL Query Endpoint

Execute read-only SQL SELECT queries directly against the database. This endpoint is designed for ad-hoc data exploration and analysis that isn't covered by the existing REST endpoints.

**Endpoint:** `POST /sql/`

### Guardrails

The SQL endpoint enforces four guardrails to protect data integrity and performance:

| # | Guardrail | Description |
|---|-----------|-------------|
| 1 | **Read-only** | Only `SELECT` and `WITH` (CTE) statements are permitted. DML (`INSERT`, `UPDATE`, `DELETE`) and DDL (`CREATE`, `DROP`, `ALTER`) are blocked. |
| 2 | **Timeout** | Queries are cancelled after 30 seconds (configurable via `SQL_TIMEOUT_S` env var). Returns `408 Request Timeout` if exceeded. |
| 3 | **Row limit** | At most 5,000 rows are returned (configurable via `SQL_MAX_ROWS` env var). If the query produces more rows, the response is truncated and `truncated` is set to `true`. |
| 4 | **Allowed tables** | Only the following tables may be referenced: `ohlcv_data`, `assets`, `sp500_constituents`, `ticker_aliases`, `tickers`, `ohlcv_data_etf_index`, `etf_index_assets`, `ohlcv_data_gov_bonds`, `gov_bond_assets`, `ohlcv_data_fx`, `fx_assets`, `ohlcv_data_uk`, `uk_assets`, `ust_bill_rates`, `ust_long_term_rates`, `ust_real_yield_rates`, `ust_yield_rates`. |

### Allowed Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `ohlcv_data` | OHLCV price data (43M+ rows) | `ticker`, `date`, `open`, `high`, `low`, `close`, `adjusted_close`, `volume`, `asset_isin` |
| `assets` | Asset metadata | `isin`, `code`, `name`, `gicSector`, `description`, `countryName` |
| `sp500_constituents` | S&P 500 index constituents | `code`, `name`, `sector`, `industry`, `weight`, `is_active` |
| `ticker_aliases` | Ticker symbol mappings | `sp500_ticker`, `ohlcv_ticker` |
| `tickers` | Unique ticker lookup table | `ticker` |
| `ohlcv_data_etf_index` | OHLCV price data for ETFs and indices (7.3M+ rows) | `ticker`, `date`, `open`, `high`, `low`, `close`, `adjusted_close`, `volume` |
| `etf_index_assets` | ETF and index metadata (5,562 ETFs + 1,666 indices) | `code`, `name`, `exchange`, `type`, `isin`, `currency` |
| `ohlcv_data_gov_bonds` | OHLCV price data for government bonds (678K+ rows) | `ticker`, `date`, `open`, `high`, `low`, `close`, `adjusted_close`, `volume` |
| `gov_bond_assets` | Government bond metadata (117 bonds, 28 countries) | `code`, `name`, `exchange`, `type`, `currency`, `country` |
| `ohlcv_data_fx` | OHLCV price data for foreign exchange pairs (6.3M+ rows) | `ticker`, `date`, `open`, `high`, `low`, `close`, `adjusted_close`, `volume` |
| `fx_assets` | Foreign exchange pair metadata (948 pairs) | `code`, `name`, `exchange`, `type`, `currency`, `base_currency`, `quote_currency` |
| `ohlcv_data_uk` | OHLCV price data for UK stocks / FTSE 100 (478K+ rows) | `ticker`, `date`, `open`, `high`, `low`, `close`, `adjusted_close`, `volume` |
| `uk_assets` | UK stock / FTSE 100 metadata (100 constituents) | `code`, `name`, `exchange`, `type`, `sector`, `industry`, `weight`, `isin`, `currency` |
| `ust_bill_rates` | US Treasury bill rates (658 rows) | `date`, `tenor`, `discount`, `coupon`, `avg_discount`, `avg_coupon`, `maturity_date`, `cusip` |
| `ust_long_term_rates` | US Treasury long-term rates (282 rows) | `date`, `rate_type`, `rate`, `extrapolation_factor` |
| `ust_real_yield_rates` | US Treasury real yield rates (470 rows) | `date`, `tenor`, `rate` |
| `ust_yield_rates` | US Treasury yield curve rates (1,316 rows) | `date`, `tenor`, `rate` |

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | SQL SELECT query to execute |

### Example Request — Simple Query

```bash
curl -X POST "https://ohlcv-api-832081557693.europe-west2.run.app/sql/?api_key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT ticker, date, close, volume FROM ohlcv_data WHERE ticker = '\''AAPL'\'' ORDER BY date DESC LIMIT 5"}'
```

### Example Response

```json
{
  "columns": ["ticker", "date", "close", "volume"],
  "rows": [
    {"ticker": "AAPL", "date": "2026-05-07", "close": 287.44, "volume": 40410371},
    {"ticker": "AAPL", "date": "2026-05-06", "close": 287.51, "volume": 58336100},
    {"ticker": "AAPL", "date": "2026-05-05", "close": 281.92, "volume": 48263100},
    {"ticker": "AAPL", "date": "2026-05-02", "close": 280.88, "volume": 42187400},
    {"ticker": "AAPL", "date": "2026-05-01", "close": 276.41, "volume": 36452700}
  ],
  "row_count": 5,
  "truncated": false
}
```

### Example Request — CTE with JOIN

```bash
curl -X POST "https://ohlcv-api-832081557693.europe-west2.run.app/sql/?api_key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "WITH latest AS (SELECT ticker, MAX(date) AS latest_date FROM ohlcv_data WHERE ticker IN ('\''AAPL'\'', '\''MSFT'\'') GROUP BY ticker) SELECT l.ticker, l.latest_date, o.close, o.volume FROM latest l JOIN ohlcv_data o ON o.ticker = l.ticker AND o.date = l.latest_date ORDER BY l.ticker"}'
```

### Example Request — S&P 500 with Asset Metadata

```bash
curl -X POST "https://ohlcv-api-832081557693.europe-west2.run.app/sql/?api_key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT s.code, s.name, s.sector, s.weight, a.isin, a.description FROM sp500_constituents s LEFT JOIN assets a ON s.code = a.code WHERE s.is_active = true ORDER BY s.weight DESC LIMIT 10"}'
```

### Error Responses

#### 400 — Forbidden Statement

```json
{
  "detail": "Only SELECT queries are allowed. Statement starts with 'DELETE'."
}
```

#### 400 — Forbidden Keyword

```json
{
  "detail": "Forbidden keyword(s) in query: INSERT. Only read-only SELECT queries are allowed."
}
```

#### 400 — Disallowed Table

```json
{
  "detail": "Table(s) not allowed: pg_class. Allowed tables: assets, etf_index_assets, fx_assets, gov_bond_assets, ohlcv_data, ohlcv_data_etf_index, ohlcv_data_fx, ohlcv_data_gov_bonds, ohlcv_data_uk, sp500_constituents, ticker_aliases, tickers, uk_assets, ust_bill_rates, ust_long_term_rates, ust_real_yield_rates, ust_yield_rates."
}
```

#### 408 — Query Timeout

```json
{
  "detail": "Query timed out after 30s. Simplify your query or add more filters."
}
```

#### 400 — Execution Error

```json
{
  "detail": "Query execution error: column \"nonexistent\" does not exist"
}
```

### Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `SQL_MAX_ROWS` | `5000` | Maximum number of rows returned per query |
| `SQL_TIMEOUT_S` | `30` | Query timeout in seconds |

---

## Response Schemas

All API responses conform to the Pydantic schemas defined in `schemas.py`. Below is a reference of every response schema, its fields, and which endpoint(s) use it.

### OhlcvDataResponse

Used by: `GET /ohlcv/latest/{ticker}`, `GET /ohlcv/{ohlcv_id}`, `POST /ohlcv/`, `PUT /ohlcv/{ohlcv_id}`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | Ticker symbol (e.g., `AAPL`) |
| `date` | date | Yes | Trading date (YYYY-MM-DD) |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price (corporate actions) |
| `volume` | integer | No | Trading volume |
| `asset_isin` | string | No | ISIN code (e.g., `US0378331005`) |
| `id` | UUID | Yes | Unique record identifier |
| `created_at` | datetime | No | Record creation timestamp |
| `updated_at` | datetime | No | Record last-update timestamp |

### PaginatedResponse

Used by: `GET /ohlcv/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[OhlcvDataResponse] | Yes | Array of OHLCV records for the current page |
| `total` | integer | Yes | Total number of matching records across all pages |
| `page` | integer | Yes | Current page number |
| `per_page` | integer | Yes | Number of records per page |
| `total_pages` | integer | Yes | Total number of pages |
| `has_next` | boolean | Yes | Whether a next page exists |
| `has_prev` | boolean | Yes | Whether a previous page exists |

### BatchLatestResponse

Used by: `GET /ohlcv/latest/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[OhlcvDataResponse] | Yes | Array of the latest OHLCV record per ticker |
| `count` | integer | Yes | Number of records returned |

### SP500ConstituentResponse

Used by: nested inside `SP500ListResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | Ticker symbol (e.g., `AAPL`) |
| `name` | string | No | Company name (e.g., `Apple Inc`) |
| `sector` | string | No | S&P sector classification |
| `industry` | string | No | S&P industry classification |
| `weight` | decimal | No | Index weight (e.g., `0.0671` for ~6.71%) |
| `is_active` | boolean | No | Whether the constituent is currently active |
| `isin` | string | No | ISIN code from the `assets` table |
| `gic_sector` | string | No | GIC sector from the `assets` table |
| `description` | string | No | Company description from the `assets` table |
| `country` | string | No | Country of incorporation from the `assets` table |

### SP500ListResponse

Used by: `GET /sp500/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[SP500ConstituentResponse] | Yes | Array of S&P 500 constituent records |
| `total` | integer | Yes | Total number of matching constituents |
| `page` | integer | Yes | Current page number |
| `per_page` | integer | Yes | Number of records per page |
| `total_pages` | integer | Yes | Total number of pages |
| `has_next` | boolean | Yes | Whether a next page exists |
| `has_prev` | boolean | Yes | Whether a previous page exists |

### SP500LatestItem

Used by: nested inside `SP500LatestResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | Ticker symbol |
| `name` | string | No | Company name |
| `sector` | string | No | S&P sector classification |
| `industry` | string | No | S&P industry classification |
| `weight` | decimal | No | Index weight |
| `date` | date | No | Trading date |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price |
| `volume` | integer | No | Trading volume |
| `asset_isin` | string | No | ISIN code |

### SP500LatestResponse

Used by: `GET /sp500/latest/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[SP500LatestItem] | Yes | Array of S&P 500 constituents with latest OHLCV data |
| `count` | integer | Yes | Number of records returned |

### SP500HistoryItem

Used by: nested inside `SP500HistoryResponse`

> **Note:** `SP500HistoryItem` has the same fields as `SP500LatestItem` — both combine constituent metadata (name, sector, industry, weight) with OHLCV price data (date, open, high, low, close, adjusted_close, volume, asset_isin).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | Ticker symbol |
| `name` | string | No | Company name |
| `sector` | string | No | S&P sector classification |
| `industry` | string | No | S&P industry classification |
| `weight` | decimal | No | Index weight |
| `date` | date | No | Trading date |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price |
| `volume` | integer | No | Trading volume |
| `asset_isin` | string | No | ISIN code |

### SP500HistoryResponse

Used by: `GET /sp500/history/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[SP500HistoryItem] | Yes | Array of S&P 500 historical OHLCV records |
| `total` | integer | Yes | Total number of matching records |
| `page` | integer | Yes | Current page number |
| `per_page` | integer | Yes | Number of records per page |
| `total_pages` | integer | Yes | Total number of pages |
| `has_next` | boolean | Yes | Whether a next page exists |
| `has_prev` | boolean | Yes | Whether a previous page exists |

### SqlQueryResponse

Used by: `POST /sql/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `columns` | list[string] | Yes | Column names in the result set |
| `rows` | list[dict] | Yes | Result rows as an array of objects |
| `row_count` | integer | Yes | Number of rows returned |
| `truncated` | boolean | No (default: `false`) | `true` if the result was truncated due to the row limit |

### EtfIndexOhlcvResponse

Used by: nested inside `EtfIndexPaginatedResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique record identifier |
| `ticker` | string | Yes | Ticker symbol (e.g., `SPY`, `GSPC`) |
| `date` | date | Yes | Trading date (YYYY-MM-DD) |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price (corporate actions) |
| `volume` | integer | No | Trading volume |
| `created_at` | datetime | No | Record creation timestamp |
| `updated_at` | datetime | No | Record last-update timestamp |

> **Note:** Unlike `OhlcvDataResponse`, this schema does **not** include `asset_isin` because the `ohlcv_data_etf_index` table lacks that column.

### EtfIndexPaginatedResponse

Used by: `GET /etf/`, `GET /index/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[EtfIndexOhlcvResponse] | Yes | Array of ETF/Index OHLCV records for the current page |
| `total` | integer | Yes | Total number of matching records across all pages |
| `page` | integer | Yes | Current page number |
| `per_page` | integer | Yes | Number of records per page |
| `total_pages` | integer | Yes | Total number of pages |
| `has_next` | boolean | Yes | Whether a next page exists |
| `has_prev` | boolean | Yes | Whether a previous page exists |

### EtfIndexAssetResponse

Used by: internal (metadata from `etf_index_assets`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | Yes | Ticker symbol (e.g., `SPY`, `GSPC`) |
| `name` | string | No | ETF or index name (e.g., `SPDR S&P 500 ETF Trust`) |
| `exchange` | string | No | Exchange (e.g., `US`, `INDX`) |
| `type` | string | No | Asset type: `etf` or `index` |
| `isin` | string | No | ISIN code (e.g., `US78462F1030`, or `null` for many ETFs/indices) |
| `currency` | string | No | Trading currency (e.g., `USD`) |

### EtfIndexLatestItem

Used by: `GET /etf/latest/{ticker}`, `GET /index/latest/{ticker}`, nested inside `EtfIndexLatestResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | Ticker symbol |
| `name` | string | No | ETF or index name |
| `exchange` | string | No | Exchange |
| `type` | string | No | Asset type (`etf` or `index`) |
| `isin` | string | No | ISIN code |
| `currency` | string | No | Trading currency |
| `date` | date | No | Trading date |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price |
| `volume` | integer | No | Trading volume |

### EtfIndexLatestResponse

Used by: `GET /etf/latest/`, `GET /index/latest/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[EtfIndexLatestItem] | Yes | Array of ETFs/indices with latest OHLCV data |
| `count` | integer | Yes | Number of records returned |

### GovBondOhlcvResponse

Used by: nested inside `GovBondPaginatedResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique record identifier |
| `ticker` | string | Yes | Ticker symbol (e.g., `US10Y`, `UK10Y`) |
| `date` | date | Yes | Trading date (YYYY-MM-DD) |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price (corporate actions) |
| `volume` | integer | No | Trading volume |
| `created_at` | datetime | No | Record creation timestamp |
| `updated_at` | datetime | No | Record last-update timestamp |

> **Note:** Unlike `OhlcvDataResponse`, this schema does **not** include `asset_isin` because the `ohlcv_data_gov_bonds` table lacks that column.

### GovBondPaginatedResponse

Used by: `GET /gov-bond/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[GovBondOhlcvResponse] | Yes | Array of government bond OHLCV records for the current page |
| `total` | integer | Yes | Total number of matching records across all pages |
| `page` | integer | Yes | Current page number |
| `per_page` | integer | Yes | Number of records per page |
| `total_pages` | integer | Yes | Total number of pages |
| `has_next` | boolean | Yes | Whether a next page exists |
| `has_prev` | boolean | Yes | Whether a previous page exists |

### GovBondLatestItem

Used by: `GET /gov-bond/latest/{ticker}`, nested inside `GovBondLatestResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | Ticker symbol |
| `name` | string | No | Government bond name (e.g., `United States 10-Year Bond`) |
| `exchange` | string | No | Exchange (always `GBOND` for government bonds) |
| `type` | string | No | Asset type (always `government_bond`) |
| `currency` | string | No | Trading currency (e.g., `USD`, `EUR`, `GBP`) |
| `country` | string | No | Country code (e.g., `US`, `DE`, `JP`) |
| `date` | date | No | Trading date |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price |
| `volume` | integer | No | Trading volume |

> **Note:** Unlike `EtfIndexLatestItem`, this schema uses `country` instead of `isin` because government bonds are identified by country rather than ISIN.

### GovBondLatestResponse

Used by: `GET /gov-bond/latest/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[GovBondLatestItem] | Yes | Array of government bonds with latest OHLCV data |
| `count` | integer | Yes | Number of records returned |

### FxOhlcvResponse

Used by: `GET /fx/`, nested inside `FxPaginatedResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique record identifier |
| `ticker` | string | Yes | FX pair ticker (e.g., `EURUSD`, `GBPUSD`) |
| `date` | date | Yes | Trading date |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price |
| `volume` | integer | No | Trading volume |
| `created_at` | datetime | No | Record creation timestamp |
| `updated_at` | datetime | No | Record last-update timestamp |

> **Note:** Unlike `OhlcvDataResponse`, this schema does **not** include `asset_isin` because the `ohlcv_data_fx` table lacks that column.

### FxPaginatedResponse

Used by: `GET /fx/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[FxOhlcvResponse] | Yes | Array of FX OHLCV records for the current page |
| `total` | integer | Yes | Total number of matching records across all pages |
| `page` | integer | Yes | Current page number |
| `per_page` | integer | Yes | Number of records per page |
| `total_pages` | integer | Yes | Total number of pages |
| `has_next` | boolean | Yes | Whether a next page exists |
| `has_prev` | boolean | Yes | Whether a previous page exists |

### FxLatestItem

Used by: `GET /fx/latest/{ticker}`, nested inside `FxLatestResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | FX pair ticker (e.g., `EURUSD`) |
| `name` | string | No | FX pair name (e.g., `EUR/USD`) |
| `exchange` | string | No | Exchange (always `FX` for foreign exchange) |
| `type` | string | No | Asset type (always `currency`) |
| `currency` | string | No | Trading currency (e.g., `USD`) |
| `base_currency` | string | No | Base currency code (e.g., `EUR`, `GBP`) |
| `quote_currency` | string | No | Quote currency code (e.g., `USD`, `JPY`) |
| `date` | date | No | Trading date |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price |
| `volume` | integer | No | Trading volume |

> **Note:** Unlike `GovBondLatestItem`, this schema uses `base_currency`/`quote_currency` instead of `country` because FX pairs are identified by their currency pair composition rather than country.

### FxLatestResponse

Used by: `GET /fx/latest/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[FxLatestItem] | Yes | Array of FX pairs with latest OHLCV data |
| `count` | integer | Yes | Number of records returned |

### UkOhlcvResponse

Used by: `GET /uk/`, nested inside `UkPaginatedResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique record identifier |
| `ticker` | string | Yes | Stock ticker symbol (case-sensitive, e.g., `AZN`, `SHEL`) |
| `date` | date | Yes | Trading date (YYYY-MM-DD) |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price |
| `volume` | integer | No | Trading volume |
| `created_at` | datetime | No | Record creation timestamp |
| `updated_at` | datetime | No | Record update timestamp |

### UkPaginatedResponse

Used by: `GET /uk/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[UkOhlcvResponse] | Yes | Array of UK stock OHLCV records |
| `total` | integer | Yes | Total number of matching records across all pages |
| `page` | integer | Yes | Current page number |
| `per_page` | integer | Yes | Number of records per page |
| `total_pages` | integer | Yes | Total number of pages |
| `has_next` | boolean | Yes | Whether a next page exists |
| `has_prev` | boolean | Yes | Whether a previous page exists |

### UkLatestItem

Used by: `GET /uk/latest/`, `GET /uk/latest/{ticker}`, nested inside `UkLatestResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | Stock ticker symbol (case-sensitive) |
| `name` | string | No | Company name |
| `exchange` | string | No | Exchange name |
| `type` | string | No | Asset type |
| `sector` | string | No | GICS sector |
| `industry` | string | No | GICS industry |
| `weight` | decimal | No | Index weight |
| `isin` | string | No | ISIN identifier |
| `currency` | string | No | Trading currency |
| `date` | date | No | Latest trading date (YYYY-MM-DD) |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price |
| `volume` | integer | No | Trading volume |

> **Note:** `weight`, `isin`, and `currency` are currently `NULL` in the database but included in the schema for future population.

### UkLatestResponse

Used by: `GET /uk/latest/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[UkLatestItem] | Yes | Array of UK stocks with latest OHLCV data |
| `count` | integer | Yes | Number of records returned |

### UstBillRateResponse

Used by: `GET /ust/bill/`, nested inside `UstBillPaginatedResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique record identifier |
| `date` | date | Yes | Rate date (YYYY-MM-DD) |
| `tenor` | string | Yes | Bill tenor (e.g., `4-Week`, `13-Week`, `26-Week`, `52-Week`) |
| `discount` | decimal | No | Discount rate |
| `coupon` | decimal | No | Coupon equivalent rate |
| `avg_discount` | decimal | No | Average discount rate |
| `avg_coupon` | decimal | No | Average coupon equivalent rate |
| `maturity_date` | date | No | Maturity date (YYYY-MM-DD) |
| `cusip` | string | No | CUSIP identifier |
| `created_at` | datetime | No | Record creation timestamp |
| `updated_at` | datetime | No | Record update timestamp |

### UstBillPaginatedResponse

Used by: `GET /ust/bill/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[UstBillRateResponse] | Yes | Array of bill rate records |
| `total` | integer | Yes | Total number of matching records across all pages |
| `page` | integer | Yes | Current page number |
| `per_page` | integer | Yes | Number of records per page |
| `total_pages` | integer | Yes | Total number of pages |
| `has_next` | boolean | Yes | Whether a next page exists |
| `has_prev` | boolean | Yes | Whether a previous page exists |

### UstBillLatestItem

Used by: `GET /ust/bill/latest/{tenor}`, nested inside `UstBillLatestResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tenor` | string | Yes | Bill tenor (e.g., `4-Week`, `13-Week`, `26-Week`, `52-Week`) |
| `date` | date | No | Rate date (YYYY-MM-DD) |
| `discount` | decimal | No | Discount rate |
| `coupon` | decimal | No | Coupon equivalent rate |
| `avg_discount` | decimal | No | Average discount rate |
| `avg_coupon` | decimal | No | Average coupon equivalent rate |
| `maturity_date` | date | No | Maturity date (YYYY-MM-DD) |
| `cusip` | string | No | CUSIP identifier |

### UstBillLatestResponse

Used by: `GET /ust/bill/latest/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[UstBillLatestItem] | Yes | Array of bill rates for all tenors |
| `count` | integer | Yes | Number of records returned |

### UstLongTermRateResponse

Used by: `GET /ust/long-term/`, nested inside `UstLongTermPaginatedResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique record identifier |
| `date` | date | Yes | Rate date (YYYY-MM-DD) |
| `rate_type` | string | Yes | Rate type (e.g., `LT Composite > 10 Years`, `LT Real Average > 10 Years`) |
| `rate` | decimal | No | Rate value |
| `extrapolation_factor` | decimal | No | Extrapolation factor |
| `created_at` | datetime | No | Record creation timestamp |
| `updated_at` | datetime | No | Record update timestamp |

> **Note:** The `rate_type` field is **case-sensitive**. Always use the exact values returned by the `/ust/long-term/distinct-values/` endpoint (e.g., `LT Composite > 10 Years`, not `lt composite > 10 years`).

### UstLongTermPaginatedResponse

Used by: `GET /ust/long-term/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[UstLongTermRateResponse] | Yes | Array of long-term rate records |
| `total` | integer | Yes | Total number of matching records across all pages |
| `page` | integer | Yes | Current page number |
| `per_page` | integer | Yes | Number of records per page |
| `total_pages` | integer | Yes | Total number of pages |
| `has_next` | boolean | Yes | Whether a next page exists |
| `has_prev` | boolean | Yes | Whether a previous page exists |

### UstLongTermLatestItem

Used by: `GET /ust/long-term/latest/{rate_type}`, nested inside `UstLongTermLatestResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rate_type` | string | Yes | Rate type (e.g., `LT Composite > 10 Years`) |
| `date` | date | No | Rate date (YYYY-MM-DD) |
| `rate` | decimal | No | Rate value |
| `extrapolation_factor` | decimal | No | Extrapolation factor |

### UstLongTermLatestResponse

Used by: `GET /ust/long-term/latest/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[UstLongTermLatestItem] | Yes | Array of long-term rates for all rate types |
| `count` | integer | Yes | Number of records returned |

### UstRealYieldRateResponse

Used by: `GET /ust/real-yield/`, nested inside `UstRealYieldPaginatedResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique record identifier |
| `date` | date | Yes | Rate date (YYYY-MM-DD) |
| `tenor` | string | Yes | Tenor (e.g., `5-Year`, `10-Year`, `30-Year`) |
| `rate` | decimal | No | Real yield rate |
| `created_at` | datetime | No | Record creation timestamp |
| `updated_at` | datetime | No | Record update timestamp |

### UstRealYieldPaginatedResponse

Used by: `GET /ust/real-yield/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[UstRealYieldRateResponse] | Yes | Array of real yield rate records |
| `total` | integer | Yes | Total number of matching records across all pages |
| `page` | integer | Yes | Current page number |
| `per_page` | integer | Yes | Number of records per page |
| `total_pages` | integer | Yes | Total number of pages |
| `has_next` | boolean | Yes | Whether a next page exists |
| `has_prev` | boolean | Yes | Whether a previous page exists |

### UstRealYieldLatestItem

Used by: `GET /ust/real-yield/latest/{tenor}`, nested inside `UstRealYieldLatestResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tenor` | string | Yes | Tenor (e.g., `5-Year`, `10-Year`, `30-Year`) |
| `date` | date | No | Rate date (YYYY-MM-DD) |
| `rate` | decimal | No | Real yield rate |

### UstRealYieldLatestResponse

Used by: `GET /ust/real-yield/latest/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[UstRealYieldLatestItem] | Yes | Array of real yield rates for all tenors |
| `count` | integer | Yes | Number of records returned |

### UstYieldRateResponse

Used by: `GET /ust/yield/`, nested inside `UstYieldPaginatedResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique record identifier |
| `date` | date | Yes | Rate date (YYYY-MM-DD) |
| `tenor` | string | Yes | Tenor (e.g., `1-Month`, `3-Month`, `2-Year`, `10-Year`, `30-Year`) |
| `rate` | decimal | No | Yield rate |
| `created_at` | datetime | No | Record creation timestamp |
| `updated_at` | datetime | No | Record update timestamp |

### UstYieldPaginatedResponse

Used by: `GET /ust/yield/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[UstYieldRateResponse] | Yes | Array of yield rate records |
| `total` | integer | Yes | Total number of matching records across all pages |
| `page` | integer | Yes | Current page number |
| `per_page` | integer | Yes | Number of records per page |
| `total_pages` | integer | Yes | Total number of pages |
| `has_next` | boolean | Yes | Whether a next page exists |
| `has_prev` | boolean | Yes | Whether a previous page exists |

### UstYieldLatestItem

Used by: `GET /ust/yield/latest/{tenor}`, nested inside `UstYieldLatestResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tenor` | string | Yes | Tenor (e.g., `1-Month`, `3-Month`, `2-Year`, `10-Year`, `30-Year`) |
| `date` | date | No | Rate date (YYYY-MM-DD) |
| `rate` | decimal | No | Yield rate |

### UstYieldLatestResponse

Used by: `GET /ust/yield/latest/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[UstYieldLatestItem] | Yes | Array of yield rates for all tenors |
| `count` | integer | Yes | Number of records returned |

---

## Batch Query Patterns

### When to Use Which Endpoint Group

| Use Case | Endpoint | Why |
|----------|----------|-----|
| Latest prices for S&P 500 stocks with company metadata | `GET /sp500/latest/` | Enriched with name, sector, industry, weight |
| Historical data for S&P 500 stocks with company metadata | `GET /sp500/history/` | Enriched + constituent verification + alias resolution |
| Latest prices for any stock (non-S&P 500) | `GET /ohlcv/latest/` | Covers all ~12,500 tickers |
| Historical data for any stock | `GET /ohlcv/` | Full filtering and pagination |
| Latest prices for ETFs with metadata | `GET /etf/latest/` | Enriched with name, exchange, isin, currency |
| Historical data for ETFs | `GET /etf/` | Filtered to ETFs only via `etf_index_assets` |
| Latest prices for indices with metadata | `GET /index/latest/` | Enriched with name, exchange, isin, currency |
| Historical data for indices | `GET /index/` | Filtered to indices only via `etf_index_assets` |
| Latest prices for government bonds with metadata | `GET /gov-bond/latest/` | Enriched with name, exchange, type, currency, country |
| Historical data for government bonds | `GET /gov-bond/` | Filtered to gov bonds only via `gov_bond_assets`; supports country filtering |
| Latest prices for FX pairs with metadata | `GET /fx/latest/` | Enriched with name, exchange, type, currency, base_currency, quote_currency |
| Historical data for FX pairs | `GET /fx/` | Filtered to FX pairs only via `fx_assets`; supports base_currency/quote_currency filtering |
| Latest prices for UK stocks (FTSE 100) with metadata | `GET /uk/latest/` | Enriched with name, exchange, type, sector, industry, weight, isin, currency |
| Historical data for UK stocks (FTSE 100) | `GET /uk/` | Filtered to FTSE 100 via `uk_assets`; supports sector/industry filtering |
| Latest US Treasury bill rates | `GET /ust/bill/latest/` | Returns latest rates for all 4 bill tenors |
| Historical US Treasury bill rates | `GET /ust/bill/` | Paginated with date and tenor filtering |
| Latest US Treasury long-term rates | `GET /ust/long-term/latest/` | Returns latest rates for all 2 rate types |
| Historical US Treasury long-term rates | `GET /ust/long-term/` | Paginated with date and rate_type filtering |
| Latest US Treasury real yield rates | `GET /ust/real-yield/latest/` | Returns latest rates for all 5 real yield tenors |
| Historical US Treasury real yield rates | `GET /ust/real-yield/` | Paginated with date and tenor filtering |
| Latest US Treasury yield curve rates | `GET /ust/yield/latest/` | Returns latest rates for all 14 yield tenors |
| Historical US Treasury yield curve rates | `GET /ust/yield/` | Paginated with date and tenor filtering |

### S&P 500 vs Plain OHLCV

The S&P 500 endpoints add two features the plain OHLCV endpoints don't provide:

1. **Constituent verification** — Returns 404 if a ticker is not an active S&P 500 member
2. **Alias resolution** — Automatically maps mismatched tickers (e.g., `FISV` → `FI` in OHLCV data) via the `ticker_aliases` table

### Batch Endpoints Summary

| Endpoint | Batch Parameter | Returns | Enriched |
|----------|----------------|---------|----------|
| `GET /ohlcv/latest/` | `tickers=AAPL,MSFT,GOOGL` | Latest OHLCV per ticker | No |
| `GET /ohlcv/latest/` | *(omit tickers)* | Latest for all ~12,500 tickers | No |
| `GET /ohlcv/` | `tickers=AAPL,MSFT,GOOGL` | Paginated history per ticker | No |
| `GET /sp500/latest/` | `tickers=AAPL,MSFT,GOOGL` | Latest S&P 500 OHLCV | Yes |
| `GET /sp500/latest/` | *(omit tickers)* | Latest for all 503 constituents | Yes |
| `GET /sp500/history/` | `tickers=AAPL,MSFT,GOOGL` | Paginated S&P 500 history | Yes |
| `GET /sp500/history/` | *(omit tickers)* | Paginated history for all active constituents | Yes |
| `GET /etf/latest/` | `tickers=SPY,QQQ,IWM` | Latest ETF OHLCV | Yes |
| `GET /etf/latest/` | *(omit tickers)* | Latest for all ~5,500 ETFs | Yes |
| `GET /etf/` | `tickers=SPY,QQQ,IWM` | Paginated ETF history | No |
| `GET /index/latest/` | `tickers=GSPC,DJI,IXIC` | Latest index OHLCV | Yes |
| `GET /index/latest/` | *(omit tickers)* | Latest for all ~1,600 indices | Yes |
| `GET /index/` | `tickers=GSPC,DJI,IXIC` | Paginated index history | No |
| `GET /gov-bond/` | `tickers=US10Y,UK10Y,DE10Y` | Paginated gov bond history | No |
| `GET /gov-bond/` | `countries=US,DE,JP` | Paginated gov bond history by country | No |
| `GET /gov-bond/latest/` | `tickers=US10Y,UK10Y,DE10Y` | Latest gov bond OHLCV | Yes |
| `GET /gov-bond/latest/` | `countries=US,DE,JP` | Latest gov bond OHLCV by country | Yes |
| `GET /gov-bond/latest/` | *(omit tickers)* | Latest for all 117 gov bonds | Yes |
| `GET /gov-bond/latest/{ticker}` | — | Latest for a single gov bond | Yes |
| `GET /fx/` | `tickers=EURUSD,GBPUSD,USDJPY` | Paginated FX history | No |
| `GET /fx/` | `base_currency=EUR` | Paginated FX history by base currency | No |
| `GET /fx/` | `quote_currency=USD` | Paginated FX history by quote currency | No |
| `GET /fx/latest/` | `tickers=EURUSD,GBPUSD,USDJPY` | Latest FX OHLCV | Yes |
| `GET /fx/latest/` | `base_currency=EUR` | Latest FX OHLCV by base currency | Yes |
| `GET /fx/latest/` | `quote_currency=USD` | Latest FX OHLCV by quote currency | Yes |
| `GET /fx/latest/` | *(omit tickers)* | Latest for all 948 FX pairs | Yes |
| `GET /fx/latest/{ticker}` | — | Latest for a single FX pair | Yes |
| `GET /uk/` | `tickers=AZN,SHEL,HSBA` | Paginated UK stock history | No |
| `GET /uk/` | `sectors=Healthcare,Energy` | Paginated UK stock history by sector | No |
| `GET /uk/` | `industries=Oil Gas Consumable Fuels` | Paginated UK stock history by industry | No |
| `GET /uk/latest/` | `tickers=AZN,SHEL,HSBA` | Latest UK stock OHLCV | Yes |
| `GET /uk/latest/` | `sectors=Healthcare,Energy` | Latest UK stock OHLCV by sector | Yes |
| `GET /uk/latest/` | `industries=Oil Gas Consumable Fuels` | Latest UK stock OHLCV by industry | Yes |
| `GET /uk/latest/` | *(omit tickers)* | Latest for all 100 FTSE 100 constituents | Yes |
| `GET /uk/latest/{ticker}` | — | Latest for a single UK stock | Yes |
| `GET /ust/bill/` | `tenors=4-Week,13-Week` | Paginated bill rate history | No |
| `GET /ust/bill/latest/` | *(omit tenors)* | Latest for all 4 bill tenors | No |
| `GET /ust/bill/latest/{tenor}` | — | Latest for a single bill tenor | No |
| `GET /ust/long-term/` | `rate_types=LT Composite > 10 Years` | Paginated long-term rate history | No |
| `GET /ust/long-term/latest/` | *(omit rate_types)* | Latest for all 2 rate types | No |
| `GET /ust/long-term/latest/{rate_type}` | — | Latest for a single rate type | No |
| `GET /ust/real-yield/` | `tenors=5-Year,10-Year` | Paginated real yield history | No |
| `GET /ust/real-yield/latest/` | *(omit tenors)* | Latest for all 5 real yield tenors | No |
| `GET /ust/real-yield/latest/{tenor}` | — | Latest for a single real yield tenor | No |
| `GET /ust/yield/` | `tenors=2-Year,10-Year,30-Year` | Paginated yield curve history | No |
| `GET /ust/yield/latest/` | *(omit tenors)* | Latest for all 14 yield tenors | No |
| `GET /ust/yield/latest/{tenor}` | — | Latest for a single yield tenor | No |
