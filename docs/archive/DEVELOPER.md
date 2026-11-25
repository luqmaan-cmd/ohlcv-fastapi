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

## Get Latest Close (Database)

### Single Ticker

Returns the most recent OHLCV record from the database for a given ticker.

**Endpoint:** `GET /ohlcv/latest_close/{ticker}`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | Ticker symbol (e.g., `AAPL`) |

#### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/latest_close/AAPL?api_key=YOUR_API_KEY"
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

Returns the most recent OHLCV record from the database for one or more tickers in a single request. If no tickers are specified, returns the latest record for **all** tickers in the database.

**Endpoint:** `GET /ohlcv/latest_close/`

> **Note:** This endpoint must be called with the trailing slash. Without it, FastAPI will route the request to `GET /ohlcv/latest_close/{ticker}` and treat the query string as a path parameter.

> **URL Pattern — Batch vs Single Ticker:**
>
> ✅ **Batch (multiple tickers):** `GET /ohlcv/latest_close/?tickers=AAPL,MSFT,GOOGL`
>
> ✅ **All tickers:** `GET /ohlcv/latest_close/`
>
> ✅ **Single ticker (path param):** `GET /ohlcv/latest_close/AAPL`
>
> ❌ **Wrong:** `GET /ohlcv/latest_close/AAPL,MSFT` — commas not allowed in path params
>
> ❌ **Wrong:** `GET /ohlcv/latest_close?ticker=AAPL` — no `ticker` query param on this endpoint

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tickers` | string | - | Comma-separated ticker symbols (e.g., `AAPL,MSFT,GOOGL`). If omitted, returns latest for all ~12,500 tickers. |

#### Example Request — Specific Tickers (Batch)

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/latest_close/?api_key=YOUR_API_KEY&tickers=AAPL,MSFT,GOOGL"
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
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/latest_close/?api_key=YOUR_API_KEY"
```

> **Warning:** Omitting the `tickers` parameter returns the latest record for every ticker in the database (~12,500 records). The response can be several MB. Use with caution in bandwidth-constrained environments.

---

## Get Real-Time OHLCV (EODHD)

Returns real-time OHLCV data from EODHD's live API. These endpoints do not read from the database — they make a direct call to `https://eodhd.com/api/real-time/{TICKER}.{EXCHANGE}`.

### Get Real-Time OHLCV

Returns real-time OHLCV data for one or more tickers from EODHD's live API. The `tickers` parameter is **required**.

**Endpoint:** `GET /ohlcv/latest/`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tickers` | string | **Required** | Comma-separated ticker symbols (e.g., `AAPL,MSFT,GOOGL`) |

#### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/latest/?api_key=YOUR_API_KEY&tickers=AAPL,MSFT,GOOGL"
```

#### Example Response

```json
{
  "data": [
    {
      "ticker": "AAPL",
      "exchange": "US",
      "timestamp": 1746626400,
      "gmtoffset": 0,
      "datetime": "2026-05-07T20:00:00",
      "open": 289.27,
      "high": 292.13,
      "low": 285.78,
      "close": 287.44,
      "adjusted_close": 287.44,
      "volume": 40410371
    },
    {
      "ticker": "MSFT",
      "exchange": "US",
      "timestamp": 1746626400,
      "gmtoffset": 0,
      "datetime": "2026-05-07T20:00:00",
      "open": 420.11,
      "high": 427.98,
      "low": 418.76,
      "close": 420.77,
      "adjusted_close": 420.77,
      "volume": 33917670
    }
  ],
  "count": 2
}
```

> **Note:** The `tickers` parameter is required for the batch endpoint. Omitting it returns a 400 error.

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

### Get Latest ETF Close (Database)

#### Single ETF

Returns the most recent OHLCV record from the database for a single ETF, enriched with asset metadata.

**Endpoint:** `GET /etf/latest_close/{ticker}`

##### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | ETF ticker symbol (e.g., `SPY`) |

##### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/etf/latest_close/SPY?api_key=YOUR_API_KEY"
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

Returns the most recent OHLCV record from the database for one or more ETFs. If no tickers are specified, returns the latest record for **all** ETFs.

**Endpoint:** `GET /etf/latest_close/`

> **Note:** This endpoint must be called with the trailing slash. Without it, FastAPI will route the request to `GET /etf/latest_close/{ticker}`.

##### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tickers` | string | - | Comma-separated ETF tickers (e.g., `SPY,QQQ,IWM`). If omitted, returns latest for all ~5,500 ETFs. |

##### Example Request — Specific ETFs

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/etf/latest_close/?api_key=YOUR_API_KEY&tickers=SPY,QQQ,IWM"
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
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/etf/latest_close/?api_key=YOUR_API_KEY"
```

> **Warning:** Omitting the `tickers` parameter returns the latest record for every ETF in the database (~5,500 records). The response can be several MB. Use with caution in bandwidth-constrained environments.

### Get Real-Time ETF OHLCV (EODHD)

Returns real-time OHLCV data from EODHD for ETFs. The `tickers` parameter is **required**.

**Endpoint:** `GET /etf/latest/`

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/etf/latest/?api_key=YOUR_API_KEY&tickers=SPY,QQQ,IWM"
```

Returns real-time OHLCV data with `ticker`, `exchange`, `timestamp`, `gmtoffset`, `datetime`, `open`, `high`, `low`, `close`, `adjusted_close`, `volume` fields.

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

### Get Latest Index Close (Database)

#### Single Index

Returns the most recent OHLCV record from the database for a single index, enriched with asset metadata.

**Endpoint:** `GET /index/latest_close/{ticker}`

##### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | Index ticker symbol (e.g., `GSPC`) |

##### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/index/latest_close/GSPC?api_key=YOUR_API_KEY"
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

Returns the most recent OHLCV record from the database for one or more indices. If no tickers are specified, returns the latest record for **all** indices.

**Endpoint:** `GET /index/latest_close/`

> **Note:** This endpoint must be called with the trailing slash. Without it, FastAPI will route the request to `GET /index/latest_close/{ticker}`.

##### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tickers` | string | - | Comma-separated index tickers (e.g., `GSPC,DJI,IXIC`). If omitted, returns latest for all ~1,600 indices. |

##### Example Request — Specific Indices

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/index/latest_close/?api_key=YOUR_API_KEY&tickers=GSPC,DJI"
```

##### Example Request — All Indices

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/index/latest_close/?api_key=YOUR_API_KEY"
```

> **Warning:** Omitting the `tickers` parameter returns the latest record for every index in the database (~1,600 records).

### Get Real-Time Index OHLCV (EODHD)

Returns real-time OHLCV data from EODHD for indices. The `tickers` parameter is **required**.

**Endpoint:** `GET /index/latest/`

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/index/latest/?api_key=YOUR_API_KEY&tickers=GSPC,DJI"
```

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

### Get Latest Government Bond Close (Database)

#### Single Government Bond

Returns the most recent OHLCV record from the database for a single government bond, enriched with asset metadata.

**Endpoint:** `GET /gov-bond/latest_close/{ticker}`

##### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | Government bond ticker symbol (e.g., `US10Y`) |

##### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest_close/US10Y?api_key=YOUR_API_KEY"
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

Returns the most recent OHLCV record from the database for one or more government bonds. If no tickers are specified, returns the latest record for **all** government bonds. Uses LATERAL joins for efficient per-ticker latest-row lookups.

**Endpoint:** `GET /gov-bond/latest_close/`

> **Note:** This endpoint must be called with the trailing slash. Without it, FastAPI will route the request to `GET /gov-bond/latest_close/{ticker}`.

> **URL Pattern — Batch vs Single Ticker:**
>
> ✅ **Batch (specific tickers):** `GET /gov-bond/latest_close/?tickers=US10Y,UK10Y,DE10Y`
>
> ✅ **Filter by country:** `GET /gov-bond/latest_close/?countries=US,DE,JP`
>
> ✅ **All government bonds:** `GET /gov-bond/latest_close/`
>
> ✅ **Single ticker (path param):** `GET /gov-bond/latest_close/US10Y`
>
> ❌ **Wrong:** `GET /gov-bond/latest_close/US10Y,UK10Y` — commas not allowed in path params

##### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tickers` | string | - | Comma-separated government bond tickers (e.g., `US10Y,UK10Y,DE10Y`). If omitted, returns latest for all 117 government bonds. |
| `country` | string | - | Filter by single country code (e.g., `US`, `DE`, `JP`) |
| `countries` | string | - | Comma-separated country codes (e.g., `US,DE,JP`) |

##### Example Request — Specific Government Bonds

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest_close/?api_key=YOUR_API_KEY&tickers=US10Y,UK10Y,DE10Y"
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
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest_close/?api_key=YOUR_API_KEY&countries=US,DE,JP"
```

Returns the latest record for all government bonds from the specified countries.

##### Example Request — All Government Bonds

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest_close/?api_key=YOUR_API_KEY"
```

> **Warning:** Omitting the `tickers` parameter returns the latest record for every government bond in the database (117 records across 28 countries).

### Get Real-Time Government Bond OHLCV (EODHD)

Returns real-time OHLCV data from EODHD for government bonds. The `tickers` parameter is **required**.

**Endpoint:** `GET /gov-bond/latest/`

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest/?api_key=YOUR_API_KEY&tickers=US10Y,UK10Y,DE10Y"
```

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

### Get Latest FX Close (Database)

#### Single FX Pair

Returns the most recent OHLCV record from the database for a single foreign exchange pair, enriched with asset metadata.

**Endpoint:** `GET /fx/latest_close/{ticker}`

##### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | FX ticker symbol (e.g., `EURUSD`) |

##### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/fx/latest_close/EURUSD?api_key=YOUR_API_KEY"
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

Returns the most recent OHLCV record from the database for one or more foreign exchange pairs. If no tickers are specified, returns the latest record for **all** FX pairs. Uses LATERAL joins for efficient per-ticker latest-row lookups.

**Endpoint:** `GET /fx/latest_close/`

> **Note:** This endpoint must be called with the trailing slash. Without it, FastAPI will route the request to `GET /fx/latest_close/{ticker}`.

> **URL Pattern — Batch vs Single Ticker:**
>
> ✅ **Batch (specific tickers):** `GET /fx/latest_close/?tickers=EURUSD,GBPUSD,USDJPY`
>
> ✅ **Filter by base currency:** `GET /fx/latest_close/?base_currency=EUR`
>
> ✅ **Filter by quote currency:** `GET /fx/latest_close/?quote_currency=USD`
>
> ✅ **All FX pairs:** `GET /fx/latest_close/`
>
> ✅ **Single ticker (path param):** `GET /fx/latest_close/EURUSD`
>
> ❌ **Wrong:** `GET /fx/latest_close/EURUSD,GBPUSD` — commas not allowed in path params

##### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tickers` | string | - | Comma-separated FX tickers (e.g., `EURUSD,GBPUSD,USDJPY`). If omitted, returns latest for all ~948 FX pairs. |
| `base_currency` | string | - | Filter by base currency code (e.g., `EUR`, `GBP`) |
| `quote_currency` | string | - | Filter by quote currency code (e.g., `USD`, `JPY`) |

##### Example Request — Specific FX Pairs

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/fx/latest_close/?api_key=YOUR_API_KEY&tickers=EURUSD,GBPUSD,USDJPY"
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
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/fx/latest_close/?api_key=YOUR_API_KEY&base_currency=EUR"
```

Returns the latest record for all FX pairs where the base currency is EUR.

##### Example Request — All FX Pairs

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/fx/latest_close/?api_key=YOUR_API_KEY"
```

> **Warning:** Omitting the `tickers` parameter returns the latest record for every FX pair in the database (~948 records). The response can be several MB. Use with caution in bandwidth-constrained environments.

### Get Real-Time FX OHLCV (EODHD)

Returns real-time OHLCV data from EODHD for FX pairs. The `tickers` parameter is **required**.

**Endpoint:** `GET /fx/latest/`

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/fx/latest/?api_key=YOUR_API_KEY&tickers=EURUSD,GBPUSD,USDJPY"
```

---

## Crypto Data

Dedicated endpoints for cryptocurrency assets (BTC-USD, ETH-USD, SOL-USD…) with enriched metadata (name, exchange, type, currency, base_currency, quote_currency). Supports filtering by `base_currency` and `quote_currency` parameters.

> **Case-sensitivity note:** Crypto tickers are **case-sensitive** and must be provided exactly as stored in the database (e.g., `BTC-USD`, not `btc-usd`).

### List Crypto OHLCV Data

Returns paginated OHLCV records for crypto assets only. Only returns data for tickers that exist in `crypto_assets`. Supports filtering by ticker(s), base_currency, and quote_currency.

**Endpoint:** `GET /crypto/`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `ticker` | string | - | Single crypto ticker (e.g., `BTC-USD`) |
| `tickers` | string | - | Comma-separated crypto tickers (e.g., `BTC-USD,ETH-USD,SOL-USD`) |
| `base_currency` | string | - | Filter by base currency code (e.g., `BTC`, `ETH`) |
| `quote_currency` | string | - | Filter by quote currency code (e.g., `USD`, `USDT`) |
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
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/crypto/?api_key=YOUR_API_KEY&ticker=BTC-USD&start_date=2026-05-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=5"
```

#### Example Request — Filter by Base Currency

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/crypto/?api_key=YOUR_API_KEY&base_currency=BTC&start_date=2026-05-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=5"
```

#### Example Response

```json
{
  "data": [
    {
      "id": "a1b2c3d4-...",
      "ticker": "BTC-USD",
      "date": "2026-05-07",
      "open": "104250.0000",
      "high": "105120.0000",
      "low": "103380.0000",
      "close": "104480.0000",
      "adjusted_close": "104480.0000",
      "volume": 32567890123,
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

### Get Latest Crypto Close (Database)

#### Single Crypto Asset

Returns the most recent OHLCV record from the database for a single crypto asset, enriched with asset metadata.

**Endpoint:** `GET /crypto/latest_close/{ticker}`

##### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | Crypto ticker symbol (e.g., `BTC-USD`). Case-sensitive. |

##### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/crypto/latest_close/BTC-USD?api_key=YOUR_API_KEY"
```

##### Example Response

```json
{
  "ticker": "BTC-USD",
  "name": "Bitcoin USD",
  "exchange": "CCC",
  "type": "cryptocurrency",
  "currency": "USD",
  "base_currency": "BTC",
  "quote_currency": "USD",
  "date": "2026-05-13",
  "open": "104250.0000",
  "high": "105120.0000",
  "low": "103380.0000",
  "close": "104480.0000",
  "adjusted_close": "104480.0000",
  "volume": 32567890123
}
```

##### Error Response — Ticker Not Found

```json
{
  "detail": "No crypto asset found with ticker: INVALID"
}
```

#### Batch / All Crypto Assets

Returns the most recent OHLCV record from the database for one or more crypto assets. If no tickers are specified, returns the latest record for **all** crypto assets. Uses LATERAL joins for efficient per-ticker latest-row lookups.

**Endpoint:** `GET /crypto/latest_close/`

> **Note:** This endpoint must be called with the trailing slash. Without it, FastAPI will route the request to `GET /crypto/latest_close/{ticker}`.

> **URL Pattern — Batch vs Single Ticker:**
>
> ✅ **Batch (specific tickers):** `GET /crypto/latest_close/?tickers=BTC-USD,ETH-USD,SOL-USD`
>
> ✅ **Filter by base currency:** `GET /crypto/latest_close/?base_currency=BTC`
>
> ✅ **Filter by quote currency:** `GET /crypto/latest_close/?quote_currency=USD`
>
> ✅ **All crypto assets:** `GET /crypto/latest_close/`
>
> ✅ **Single ticker (path param):** `GET /crypto/latest_close/BTC-USD`
>
> ❌ **Wrong:** `GET /crypto/latest_close/BTC-USD,ETH-USD` — commas not allowed in path params

##### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tickers` | string | - | Comma-separated crypto tickers (e.g., `BTC-USD,ETH-USD,SOL-USD`). If omitted, returns latest for all crypto assets. |
| `base_currency` | string | - | Filter by base currency code (e.g., `BTC`, `ETH`) |
| `quote_currency` | string | - | Filter by quote currency code (e.g., `USD`, `USDT`) |

##### Example Request — Specific Crypto Assets

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/crypto/latest_close/?api_key=YOUR_API_KEY&tickers=BTC-USD,ETH-USD,SOL-USD"
```

##### Example Response

```json
{
  "data": [
    {
      "ticker": "BTC-USD",
      "name": "Bitcoin USD",
      "exchange": "CCC",
      "type": "cryptocurrency",
      "currency": "USD",
      "base_currency": "BTC",
      "quote_currency": "USD",
      "date": "2026-05-13",
      "open": "104250.0000",
      "high": "105120.0000",
      "low": "103380.0000",
      "close": "104480.0000",
      "adjusted_close": "104480.0000",
      "volume": 32567890123
    },
    {
      "ticker": "ETH-USD",
      "name": "Ethereum USD",
      "exchange": "CCC",
      "type": "cryptocurrency",
      "currency": "USD",
      "base_currency": "ETH",
      "quote_currency": "USD",
      "date": "2026-05-13",
      "open": "2520.5000",
      "high": "2565.8000",
      "low": "2498.2000",
      "close": "2543.7000",
      "adjusted_close": "2543.7000",
      "volume": 15678901234
    },
    {
      "ticker": "SOL-USD",
      "name": "Solana USD",
      "exchange": "CCC",
      "type": "cryptocurrency",
      "currency": "USD",
      "base_currency": "SOL",
      "quote_currency": "USD",
      "date": "2026-05-13",
      "open": "172.4500",
      "high": "175.8900",
      "low": "169.3200",
      "close": "174.5600",
      "adjusted_close": "174.5600",
      "volume": 3456789012
    }
  ],
  "count": 3
}
```

##### Example Request — Filter by Base Currency

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/crypto/latest_close/?api_key=YOUR_API_KEY&base_currency=BTC"
```

Returns the latest record for all crypto assets where the base currency is BTC.

##### Example Request — All Crypto Assets

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/crypto/latest_close/?api_key=YOUR_API_KEY"
```

Returns the latest record for every crypto asset in the database.

### Get Real-Time Crypto OHLCV (EODHD)

Returns real-time OHLCV data from EODHD for crypto assets. The `tickers` parameter is **required**.

**Endpoint:** `GET /crypto/latest/`

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/crypto/latest/?api_key=YOUR_API_KEY&tickers=BTC-USD,ETH-USD,SOL-USD"
```

### Get Crypto Historical Data

Returns paginated historical OHLCV data for crypto assets. Enriched with name, exchange, type, currency, base_currency, quote_currency from `crypto_assets`.

**Endpoint:** `GET /crypto/history/`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tickers` | string | - | Comma-separated crypto tickers (e.g., `BTC-USD,ETH-USD`). If omitted, returns history for all crypto assets. |
| `base_currency` | string | - | Filter by base currency code (e.g., `BTC`, `ETH`) |
| `quote_currency` | string | - | Filter by quote currency code (e.g., `USD`, `USDT`) |
| `start_date` | date | - | Start date filter (YYYY-MM-DD) |
| `end_date` | date | - | End date filter (YYYY-MM-DD) |
| `year` | integer | - | Filter by year (1900-2100) |
| `month` | integer | - | Filter by month (1-12) |
| `sort_by` | string | `date` | Sort field: `date`, `volume`, `close`, `open`, `high`, `low` |
| `sort_order` | string | `desc` | Sort order: `asc`, `desc` |
| `page` | integer | `1` | Page number (min: 1) |
| `per_page` | integer | `1000` | Records per page (min: 1, max: 5000) |

#### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/crypto/history/?api_key=YOUR_API_KEY&tickers=BTC-USD,ETH-USD&start_date=2026-05-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=5"
```

#### Example Response

```json
{
  "data": [
    {
      "ticker": "BTC-USD",
      "name": "Bitcoin USD",
      "exchange": "CCC",
      "type": "cryptocurrency",
      "currency": "USD",
      "base_currency": "BTC",
      "quote_currency": "USD",
      "date": "2026-05-07",
      "open": "104250.0000",
      "high": "105120.0000",
      "low": "103380.0000",
      "close": "104480.0000",
      "adjusted_close": "104480.0000",
      "volume": 32567890123
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

### Get Top 100 Crypto by Volume

Returns the top 100 crypto assets ranked by latest volume (descending). Enriched with name, exchange, type, currency, base_currency, quote_currency, and `notional_value` (close × volume). Uses LATERAL joins for efficient per-ticker latest-row lookups.

**Endpoint:** `GET /crypto/top100/`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `base_currency` | string | - | Filter by base currency code (e.g., `BTC`, `ETH`) |
| `quote_currency` | string | - | Filter by quote currency code (e.g., `USD`, `USDT`) |

#### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/crypto/top100/?api_key=YOUR_API_KEY"
```

#### Example Response

```json
{
  "data": [
    {
      "ticker": "BTC-USD",
      "name": "Bitcoin USD",
      "exchange": "CCC",
      "type": "cryptocurrency",
      "currency": "USD",
      "base_currency": "BTC",
      "quote_currency": "USD",
      "date": "2026-05-13",
      "open": "104250.0000",
      "high": "105120.0000",
      "low": "103380.0000",
      "close": "104480.0000",
      "adjusted_close": "104480.0000",
      "volume": 32567890123,
      "notional_value": "3405432898794.0400"
    }
  ],
  "count": 100
}
```

#### Example Request — Filter by Quote Currency

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/crypto/top100/?api_key=YOUR_API_KEY&quote_currency=USD"
```

Returns the top 100 crypto assets by volume where the quote currency is USD.

### List Crypto Assets

Returns a paginated list of all crypto asset metadata (no OHLCV price data). Useful for discovering available tickers and their base/quote currencies.

**Endpoint:** `GET /crypto/assets/`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `base_currency` | string | - | Filter by base currency (e.g., `BTC`, `ETH`) |
| `quote_currency` | string | - | Filter by quote currency (e.g., `USD`, `EUR`) |
| `type` | string | - | Filter by type (e.g., `cryptocurrency`) |
| `search` | string | - | Search code or name (case-insensitive partial match) |
| `sort` | string | `code` | Sort field: `code` or `name` |
| `order` | string | `asc` | Sort order: `asc` or `desc` |
| `page` | integer | `1` | Page number (≥ 1) |
| `per_page` | integer | `50` | Results per page (1–500) |

#### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/crypto/assets/?api_key=YOUR_API_KEY&per_page=3"
```

#### Example Response

```json
{
  "data": [
    {
      "code": "00-USD",
      "name": "00 Token USD",
      "exchange": "CC",
      "type": "cryptocurrency",
      "base_currency": "00",
      "quote_currency": "USD",
      "currency": "USD"
    },
    {
      "code": "0G-USD",
      "name": "0G",
      "exchange": "CC",
      "type": "cryptocurrency",
      "base_currency": "0G",
      "quote_currency": "USD",
      "currency": "USD"
    },
    {
      "code": "0X0-USD",
      "name": "0x0.ai USD",
      "exchange": "CC",
      "type": "cryptocurrency",
      "base_currency": "0X0",
      "quote_currency": "USD",
      "currency": "USD"
    }
  ],
  "total": 2847,
  "page": 1,
  "per_page": 3,
  "total_pages": 949,
  "has_next": true,
  "has_prev": false
}
```

#### Example Request — Search by Name

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/crypto/assets/?api_key=YOUR_API_KEY&search=bitcoin"
```

#### Example Request — Filter by Base Currency

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/crypto/assets/?api_key=YOUR_API_KEY&base_currency=BTC"
```

---

## UK Stock (LSE) Data

Dedicated endpoints for UK stocks listed on the London Stock Exchange (LSE) with enriched metadata (name, exchange, type, sector, industry, isin, currency). Supports filtering by `sector` and `industry` parameters.

> **Case-sensitivity note:** UK tickers are **case-sensitive** and must be provided exactly as stored in the database (e.g., `AZN`, not `azn`).

### List UK Stock OHLCV Data

Returns paginated OHLCV records for UK stocks (LSE) only. Only returns data for tickers that exist in `uk_assets`. Supports filtering by ticker(s), sector, and industry.

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

### Get Latest UK Stock Close (Database)

#### Single UK Stock

Returns the most recent OHLCV record from the database for a single UK stock, enriched with asset metadata.

**Endpoint:** `GET /uk/latest_close/{ticker}`

##### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | UK stock ticker symbol (e.g., `AZN`). Case-sensitive. |

##### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/uk/latest_close/AZN?api_key=YOUR_API_KEY"
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

Returns the most recent OHLCV record from the database for one or more UK stocks. If no tickers are specified, returns the latest record for **all** UK stocks. Uses LATERAL joins for efficient per-ticker latest-row lookups.

**Endpoint:** `GET /uk/latest_close/`

> **Note:** This endpoint must be called with the trailing slash. Without it, FastAPI will route the request to `GET /uk/latest_close/{ticker}`.

> **URL Pattern — Batch vs Single Ticker:**
>
> ✅ **Batch (specific tickers):** `GET /uk/latest_close/?tickers=AZN,SHEL,HSBA`
>
> ✅ **Filter by sector:** `GET /uk/latest_close/?sector=Healthcare`
>
> ✅ **Filter by industry:** `GET /uk/latest_close/?industry=Drug Manufacturers - General`
>
> ✅ **All UK stocks:** `GET /uk/latest_close/`
>
> ✅ **Single ticker (path param):** `GET /uk/latest_close/AZN`
>
> ❌ **Wrong:** `GET /uk/latest_close/AZN,SHEL` — commas not allowed in path params

##### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tickers` | string | - | Comma-separated UK tickers (e.g., `AZN,SHEL,HSBA`). If omitted, returns latest for all ~3,965 LSE stocks. |
| `sector` | string | - | Filter by sector (e.g., `Healthcare`, `Energy`) |
| `industry` | string | - | Filter by industry (e.g., `Drug Manufacturers`, `Oil & Gas`) |

##### Example Request — Specific UK Stocks

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/uk/latest_close/?api_key=YOUR_API_KEY&tickers=AZN,SHEL,HSBA"
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
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/uk/latest_close/?api_key=YOUR_API_KEY&sector=Healthcare"
```

Returns the latest record for all UK stocks in the Healthcare sector.

##### Example Request — All UK Stocks

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/uk/latest_close/?api_key=YOUR_API_KEY"
```

> **Warning:** Omitting the `tickers` parameter returns the latest record for every UK stock in the database (~3,965 LSE stocks).

### Get Real-Time UK Stock OHLCV (EODHD)

Returns real-time OHLCV data from EODHD for UK stocks. The `tickers` parameter is **required**.

**Endpoint:** `GET /uk/latest/`

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/uk/latest/?api_key=YOUR_API_KEY&tickers=AZN,SHEL,HSBA"
```

---

## FTSE 100 Data

Dedicated endpoints for FTSE 100 constituents with enriched metadata (name, sector, industry from `ftse100_constituents`; isin, currency from `uk_assets`). Supports filtering by `sector` and `industry` parameters.

> **Case-sensitivity note:** FTSE 100 tickers are **case-sensitive** and must be provided exactly as stored in the database (e.g., `AZN`, not `azn`).

### List FTSE 100 OHLCV Data

Returns paginated OHLCV records for FTSE 100 constituents only. Only returns data for tickers that exist in `ftse100_constituents`. Supports filtering by ticker(s), sector, and industry.

**Endpoint:** `GET /ftse100/`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `ticker` | string | - | Single FTSE 100 ticker (e.g., `AZN`) |
| `tickers` | string | - | Comma-separated FTSE 100 tickers (e.g., `AZN,SHEL,HSBA`) |
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
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ftse100/?api_key=YOUR_API_KEY&ticker=AZN&start_date=2026-05-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=5"
```

#### Example Request — Filter by Sector

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ftse100/?api_key=YOUR_API_KEY&sector=Healthcare&start_date=2026-05-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=5"
```

#### Example Response

```json
{
  "data": [
    {
      "ticker": "AZN",
      "name": "AstraZeneca PLC",
      "sector": "Healthcare",
      "industry": "Drug Manufacturers - General",
      "isin": "GB0009895292",
      "currency": "GBP",
      "date": "2026-05-07",
      "open": "12450.0000",
      "high": "12520.0000",
      "low": "12380.0000",
      "close": "12480.0000",
      "adjusted_close": "12480.0000",
      "volume": 3256789
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

#### Error Response — Invalid Ticker

```json
{
  "detail": "Ticker(s) not FTSE 100 constituents: FAKE"
}
```

### Get Latest FTSE 100 Data

Returns the most recent OHLCV record for one or more FTSE 100 constituents. If no tickers are specified, returns the latest record for **all** FTSE 100 constituents. Uses LATERAL joins for efficient per-ticker latest-row lookups.

**Endpoint:** `GET /ftse100/latest/`

> **URL Pattern — Batch vs Single Ticker:**
>
> ✅ **Batch (specific tickers):** `GET /ftse100/latest/?tickers=AZN,SHEL,HSBA`
>
> ✅ **Single ticker:** `GET /ftse100/latest/?tickers=AZN`
>
> ✅ **Filter by sector:** `GET /ftse100/latest/?sector=Healthcare`
>
> ✅ **Filter by industry:** `GET /ftse100/latest/?industry=Drug Manufacturers - General`
>
> ✅ **All FTSE 100 constituents:** `GET /ftse100/latest/`

##### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `tickers` | string | - | Comma-separated FTSE 100 tickers (e.g., `AZN,SHEL,HSBA`). If omitted, returns latest for all 100 constituents. |
| `sector` | string | - | Filter by sector (e.g., `Healthcare`, `Energy`) |
| `industry` | string | - | Filter by industry (e.g., `Drug Manufacturers`, `Oil & Gas`) |

##### Example Request — Specific FTSE 100 Constituents

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ftse100/latest/?api_key=YOUR_API_KEY&tickers=AZN,SHEL,HSBA"
```

##### Example Response

```json
{
  "data": [
    {
      "ticker": "AZN",
      "name": "AstraZeneca PLC",
      "sector": "Healthcare",
      "industry": "Drug Manufacturers - General",
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
      "sector": "Financial Services",
      "industry": "Banks - Diversified",
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
      "sector": "Energy",
      "industry": "Oil & Gas Integrated",
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
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ftse100/latest/?api_key=YOUR_API_KEY&sector=Healthcare"
```

Returns the latest record for all FTSE 100 constituents in the Healthcare sector.

##### Example Request — All FTSE 100 Constituents

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ftse100/latest/?api_key=YOUR_API_KEY"
```

Returns the latest record for all 100 FTSE 100 constituents.

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

Returns the most recent bill rate record for one or more tenors. If no tenors are specified, returns the latest record for **all** bill tenors. Uses `DISTINCT ON` for efficient per-tenor latest-row lookups.

**Endpoint:** `GET /ust/bill/latest/`

> **URL Pattern — Batch vs Single Tenor:**
>
> ✅ **Batch (specific tenors):** `GET /ust/bill/latest/?tenors=4WK,13WK,26WK`
>
> ✅ **Single tenor:** `GET /ust/bill/latest/?tenors=13WK`
>
> ✅ **All tenors:** `GET /ust/bill/latest/`

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

Returns the most recent long-term rate record for one or more rate types. If no rate types are specified, returns the latest record for **all** long-term rate types. Uses `DISTINCT ON` for efficient per-rate-type latest-row lookups.

**Endpoint:** `GET /ust/long-term/latest/`

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

Returns the most recent real yield rate record for one or more tenors. If no tenors are specified, returns the latest record for **all** real yield tenors. Uses `DISTINCT ON` for efficient per-tenor latest-row lookups.

**Endpoint:** `GET /ust/real-yield/latest/`

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

Returns the most recent yield curve rate record for one or more tenors. If no tenors are specified, returns the latest record for **all** yield tenors. Uses `DISTINCT ON` for efficient per-tenor latest-row lookups.

**Endpoint:** `GET /ust/yield/latest/`

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
| 4 | **Allowed tables** | Only the following tables may be referenced: `ohlcv_data`, `assets`, `sp500_constituents`, `ticker_aliases`, `tickers`, `ohlcv_data_etf_index`, `etf_index_assets`, `ohlcv_data_gov_bonds`, `gov_bond_assets`, `ohlcv_data_fx`, `fx_assets`, `ohlcv_data_uk`, `uk_assets`, `ftse100_constituents`, `ohlcv_data_crypto`, `crypto_assets`, `ust_bill_rates`, `ust_long_term_rates`, `ust_real_yield_rates`, `ust_yield_rates`. |

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
| `ohlcv_data_uk` | OHLCV price data for UK stocks / LSE (11.4M+ rows) | `ticker`, `date`, `open`, `high`, `low`, `close`, `adjusted_close`, `volume` |
| `uk_assets` | UK stock / LSE metadata (3,965 stocks) | `code`, `name`, `exchange`, `type`, `sector`, `industry`, `isin`, `currency` |
| `ftse100_constituents` | FTSE 100 index constituents (100 stocks) | `code`, `name`, `sector`, `industry` |
| `ohlcv_data_crypto` | OHLCV price data for crypto assets | `ticker`, `date`, `open`, `high`, `low`, `close`, `adjusted_close`, `volume` |
| `crypto_assets` | Crypto asset metadata | `code`, `name`, `exchange`, `type`, `currency`, `base_currency`, `quote_currency` |
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

Used by: `GET /ohlcv/latest_close/{ticker}`, `GET /ohlcv/{ohlcv_id}`, `POST /ohlcv/`, `PUT /ohlcv/{ohlcv_id}`

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

Used by: `GET /ohlcv/latest_close/`

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

Used by: `GET /etf/latest_close/{ticker}`, `GET /index/latest_close/{ticker}`, nested inside `EtfIndexLatestResponse`

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

Used by: `GET /etf/latest_close/`, `GET /index/latest_close/`

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

Used by: `GET /gov-bond/latest_close/{ticker}`, nested inside `GovBondLatestResponse`

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

Used by: `GET /gov-bond/latest_close/`

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

Used by: `GET /fx/latest_close/{ticker}`, nested inside `FxLatestResponse`

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

Used by: `GET /fx/latest_close/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[FxLatestItem] | Yes | Array of FX pairs with latest OHLCV data |
| `count` | integer | Yes | Number of records returned |

### CryptoOhlcvResponse

Used by: `GET /crypto/`, nested inside `CryptoPaginatedResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique record identifier |
| `ticker` | string | Yes | Crypto ticker (e.g., `BTC-USD`, `ETH-USD`) |
| `date` | date | Yes | Trading date |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price |
| `volume` | integer | No | Trading volume |
| `created_at` | datetime | No | Record creation timestamp |
| `updated_at` | datetime | No | Record last-update timestamp |

### CryptoPaginatedResponse

Used by: `GET /crypto/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[CryptoOhlcvResponse] | Yes | Array of crypto OHLCV records for the current page |
| `total` | integer | Yes | Total number of matching records across all pages |
| `page` | integer | Yes | Current page number |
| `per_page` | integer | Yes | Number of records per page |
| `total_pages` | integer | Yes | Total number of pages |
| `has_next` | boolean | Yes | Whether a next page exists |
| `has_prev` | boolean | Yes | Whether a previous page exists |

### CryptoLatestItem

Used by: `GET /crypto/latest_close/`, `GET /crypto/latest_close/{ticker}`, nested inside `CryptoLatestResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | Crypto ticker (e.g., `BTC-USD`) |
| `name` | string | No | Crypto asset name (e.g., `Bitcoin USD`) |
| `exchange` | string | No | Exchange (e.g., `CCC`) |
| `type` | string | No | Asset type (e.g., `cryptocurrency`) |
| `currency` | string | No | Trading currency (e.g., `USD`) |
| `base_currency` | string | No | Base currency code (e.g., `BTC`, `ETH`) |
| `quote_currency` | string | No | Quote currency code (e.g., `USD`, `USDT`) |
| `date` | date | No | Trading date |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price |
| `volume` | integer | No | Trading volume |

### CryptoLatestResponse

Used by: `GET /crypto/latest_close/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[CryptoLatestItem] | Yes | Array of crypto assets with latest OHLCV data |
| `count` | integer | Yes | Number of records returned |

### CryptoHistoryItem

Used by: nested inside `CryptoHistoryPaginatedResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | Crypto ticker |
| `name` | string | No | Crypto asset name |
| `exchange` | string | No | Exchange |
| `type` | string | No | Asset type |
| `currency` | string | No | Trading currency |
| `base_currency` | string | No | Base currency code |
| `quote_currency` | string | No | Quote currency code |
| `date` | date | No | Trading date |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price |
| `volume` | integer | No | Trading volume |

### CryptoHistoryPaginatedResponse

Used by: `GET /crypto/history/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[CryptoHistoryItem] | Yes | Array of crypto historical OHLCV records |
| `total` | integer | Yes | Total number of matching records |
| `page` | integer | Yes | Current page number |
| `per_page` | integer | Yes | Number of records per page |
| `total_pages` | integer | Yes | Total number of pages |
| `has_next` | boolean | Yes | Whether a next page exists |
| `has_prev` | boolean | Yes | Whether a previous page exists |

### CryptoTop100Item

Used by: nested inside `CryptoTop100Response`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | Crypto ticker |
| `name` | string | No | Crypto asset name |
| `exchange` | string | No | Exchange |
| `type` | string | No | Asset type |
| `currency` | string | No | Trading currency |
| `base_currency` | string | No | Base currency code |
| `quote_currency` | string | No | Quote currency code |
| `date` | date | No | Latest trading date |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price |
| `volume` | integer | No | Trading volume |
| `notional_value` | decimal | No | Close price × volume |

### CryptoTop100Response

Used by: `GET /crypto/top100/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[CryptoTop100Item] | Yes | Array of top 100 crypto assets by volume with latest OHLCV data |
| `count` | integer | Yes | Number of records returned |

### CryptoAssetItem

Used by: nested inside `CryptoAssetResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | Yes | Crypto ticker code (e.g., `BTC-USD`, `ETH-USD`) |
| `name` | string | No | Asset name (e.g., `Bitcoin`, `Ethereum`) |
| `exchange` | string | No | Exchange code (e.g., `CC`) |
| `type` | string | No | Asset type (e.g., `cryptocurrency`) |
| `base_currency` | string | No | Base currency (e.g., `BTC`, `ETH`) |
| `quote_currency` | string | No | Quote currency (e.g., `USD`, `EUR`) |
| `currency` | string | No | Pricing currency |

### CryptoAssetResponse

Used by: `GET /crypto/assets/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[CryptoAssetItem] | Yes | Array of crypto asset metadata |
| `total` | integer | Yes | Total matching records |
| `page` | integer | Yes | Current page number |
| `per_page` | integer | Yes | Results per page |
| `total_pages` | integer | Yes | Total number of pages |
| `has_next` | boolean | Yes | Whether a next page exists |
| `has_prev` | boolean | Yes | Whether a previous page exists |

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

Used by: `GET /uk/latest_close/`, `GET /uk/latest_close/{ticker}`, nested inside `UkLatestResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | Stock ticker symbol (case-sensitive) |
| `name` | string | No | Company name |
| `exchange` | string | No | Exchange name |
| `type` | string | No | Asset type |
| `sector` | string | No | GICS sector |
| `industry` | string | No | GICS industry |
| `isin` | string | No | ISIN identifier |
| `currency` | string | No | Trading currency |
| `date` | date | No | Latest trading date (YYYY-MM-DD) |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price |
| `volume` | integer | No | Trading volume |

> **Note:** `isin` and `currency` are populated from the `uk_assets` metadata table.

### UkLatestResponse

Used by: `GET /uk/latest_close/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[UkLatestItem] | Yes | Array of UK stocks with latest OHLCV data |
| `count` | integer | Yes | Number of records returned |

### Ftse100LatestItem

Used by: `GET /ftse100/latest/`, nested inside `Ftse100LatestResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | Stock ticker symbol |
| `name` | string | No | Company name |
| `sector` | string | No | GICS sector |
| `industry` | string | No | GICS industry |
| `isin` | string | No | ISIN identifier |
| `currency` | string | No | Trading currency |
| `date` | date | No | Latest trading date (YYYY-MM-DD) |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price |
| `volume` | integer | No | Trading volume |

> **Note:** `isin` and `currency` are populated from the `uk_assets` metadata table via LEFT JOIN.

### Ftse100LatestResponse

Used by: `GET /ftse100/latest/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[Ftse100LatestItem] | Yes | Array of FTSE 100 constituents with latest OHLCV data |
| `count` | integer | Yes | Number of records returned |

### Ftse100HistoryItem

Used by: `GET /ftse100/`, nested inside `Ftse100PaginatedResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | Stock ticker symbol |
| `name` | string | No | Company name |
| `sector` | string | No | GICS sector |
| `industry` | string | No | GICS industry |
| `isin` | string | No | ISIN identifier |
| `currency` | string | No | Trading currency |
| `date` | date | No | Trading date (YYYY-MM-DD) |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price |
| `volume` | integer | No | Trading volume |

> **Note:** `isin` and `currency` are populated from the `uk_assets` metadata table via LEFT JOIN.

### Ftse100PaginatedResponse

Used by: `GET /ftse100/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[Ftse100HistoryItem] | Yes | Array of FTSE 100 historical OHLCV records |
| `total` | integer | Yes | Total number of matching records across all pages |
| `page` | integer | Yes | Current page number |
| `per_page` | integer | Yes | Number of records per page |
| `total_pages` | integer | Yes | Total number of pages |
| `has_next` | boolean | Yes | Whether a next page exists |
| `has_prev` | boolean | Yes | Whether a previous page exists |

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

Used by: `GET /ust/bill/latest/`, nested inside `UstBillLatestResponse`

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

Used by: `GET /ust/long-term/latest/`, nested inside `UstLongTermLatestResponse`

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

Used by: `GET /ust/real-yield/latest/`, nested inside `UstRealYieldLatestResponse`

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

Used by: `GET /ust/yield/latest/`, nested inside `UstYieldLatestResponse`

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

### CommodityOhlcvResponse

Used by: `GET /commodity/`, nested inside `CommodityPaginatedResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `date` | date | Yes | Trading date |
| `symbol` | string | Yes | Commodity symbol (e.g., `LGOc3`) |
| `name` | string | Yes | Commodity name (e.g., `Crude Oil (WTI)`) |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price |
| `volume` | integer | No | Trading volume |
| `category` | string | No | Commodity category (e.g., `Energy`, `Metals`) |
| `ingestion_ts` | datetime | No | Record ingestion timestamp |

### CommodityPaginatedResponse

Used by: `GET /commodity/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[CommodityOhlcvResponse] | Yes | Array of commodity OHLCV records for the current page |
| `total` | integer | Yes | Total number of matching records across all pages |
| `page` | integer | Yes | Current page number |
| `per_page` | integer | Yes | Number of records per page |
| `total_pages` | integer | Yes | Total number of pages |
| `has_next` | boolean | Yes | Whether a next page exists |
| `has_prev` | boolean | Yes | Whether a previous page exists |

### CommodityLatestItem

Used by: `GET /commodity/latest/`, nested inside `CommodityLatestResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `symbol` | string | Yes | Commodity symbol (e.g., `LGOc3`) |
| `name` | string | No | Commodity name (e.g., `Crude Oil (WTI)`) |
| `category` | string | No | Commodity category (e.g., `Energy`, `Metals`) |
| `date` | date | No | Trading date |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | Highest price |
| `low` | decimal | No | Lowest price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price |
| `volume` | integer | No | Trading volume |

### CommodityLatestResponse

Used by: `GET /commodity/latest/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[CommodityLatestItem] | Yes | Array of commodities with latest OHLCV data |
| `count` | integer | Yes | Number of records returned |

### CommoditySymbolItem

Used by: nested inside `CommoditySymbolResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `symbol` | string | Yes | Commodity symbol (e.g., `LGOc3`) |
| `name` | string | No | Commodity name (e.g., `Crude Oil (WTI)`) |
| `category` | string | No | Commodity category (e.g., `Energy`, `Metals`) |

### CommoditySymbolResponse

Used by: `GET /commodity/symbols/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[CommoditySymbolItem] | Yes | Array of commodity symbol metadata |
| `count` | integer | Yes | Number of records returned |

### CommodityCategoryResponse

Used by: `GET /commodity/categories/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | list[string] | Yes | Array of distinct category names |
| `count` | integer | Yes | Number of categories returned |

---

## Commodities Data

Dedicated endpoints for commodity assets (Crude Oil, Natural Gas, Gold, Wheat, etc.) with embedded metadata (name, category). Supports filtering by `category` parameter (Energy, Metals, Grains, Softs, Livestock, Other).

> **Case-sensitivity note:** Commodity symbols are **case-sensitive** and must be provided exactly as stored in the database (e.g., `LGOc3`, not `lgoc3`).

### List Commodity OHLCV Data

Returns paginated OHLCV records for commodities. Supports filtering by symbol(s), category, date range, and price/volume bounds.

**Endpoint:** `GET /commodity/`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `symbol` | string | - | Single commodity symbol (e.g., `LGOc3`) |
| `symbols` | string | - | Comma-separated commodity symbols (e.g., `LGOc3,NICKEL,GDK`) |
| `category` | string | - | Filter by category (e.g., `Energy`, `Metals`, `Grains`, `Softs`, `Livestock`, `Other`) |
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

#### Example Request — Single Symbol

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/commodity/?api_key=YOUR_API_KEY&symbol=LGOc3&start_date=2026-05-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=5"
```

#### Example Request — Filter by Category

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/commodity/?api_key=YOUR_API_KEY&category=Energy&start_date=2026-05-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=5"
```

#### Example Response

```json
{
  "data": [
    {
      "date": "2026-05-07",
      "symbol": "LGOc3",
      "name": "Crude Oil (WTI)",
      "open": "78.5000",
      "high": "79.2000",
      "low": "77.8000",
      "close": "78.9000",
      "adjusted_close": "78.9000",
      "volume": 456789,
      "category": "Energy",
      "ingestion_ts": "2026-05-08T02:00:00.000000"
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

### Get Latest Commodity Data

Returns the most recent OHLCV record for one or more commodities. If no symbols are specified, returns the latest record for **all** commodities. Uses `DISTINCT ON` for efficient per-symbol latest-row lookups.

**Endpoint:** `GET /commodity/latest/`

> **URL Pattern — Batch vs Single Symbol:**
>
> ✅ **Batch (specific symbols):** `GET /commodity/latest/?symbols=LGOc3,NICKEL,GDK`
>
> ✅ **Single symbol:** `GET /commodity/latest/?symbols=LGOc3`
>
> ✅ **Filter by category:** `GET /commodity/latest/?category=Energy`
>
> ✅ **All commodities:** `GET /commodity/latest/`

##### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `symbols` | string | - | Comma-separated commodity symbols (e.g., `LGOc3,NICKEL,GDK`). If omitted, returns latest for all commodities. |
| `category` | string | - | Filter by category (e.g., `Energy`, `Metals`) |

##### Example Request — Specific Commodities

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/commodity/latest/?api_key=YOUR_API_KEY&symbols=LGOc3,NICKEL,GDK"
```

##### Example Response

```json
{
  "data": [
    {
      "symbol": "GDK",
      "name": "Gold",
      "category": "Metals",
      "date": "2026-05-13",
      "open": "2345.6000",
      "high": "2360.0000",
      "low": "2340.0000",
      "close": "2352.8000",
      "adjusted_close": "2352.8000",
      "volume": 123456
    },
    {
      "symbol": "LGOc3",
      "name": "Crude Oil (WTI)",
      "category": "Energy",
      "date": "2026-05-13",
      "open": "78.5000",
      "high": "79.2000",
      "low": "77.8000",
      "close": "78.9000",
      "adjusted_close": "78.9000",
      "volume": 456789
    },
    {
      "symbol": "NICKEL",
      "name": "Nickel",
      "category": "Metals",
      "date": "2026-05-13",
      "open": "18250.0000",
      "high": "18500.0000",
      "low": "18100.0000",
      "close": "18350.0000",
      "adjusted_close": "18350.0000",
      "volume": 7890
    }
  ],
  "count": 3
}
```

##### Example Request — Filter by Category

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/commodity/latest/?api_key=YOUR_API_KEY&category=Energy"
```

Returns the latest record for all commodities in the Energy category.

##### Example Request — All Commodities

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/commodity/latest/?api_key=YOUR_API_KEY"
```

Returns the latest record for every commodity in the database.

### List Commodity Symbols

Returns all commodity symbols with their latest metadata (name, category). Useful for discovering available symbols.

**Endpoint:** `GET /commodity/symbols/`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | **Required** | API key for authentication |
| `category` | string | - | Filter by category (e.g., `Energy`, `Metals`) |

#### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/commodity/symbols/?api_key=YOUR_API_KEY"
```

#### Example Response

```json
{
  "data": [
    {
      "symbol": "GDK",
      "name": "Gold",
      "category": "Metals"
    },
    {
      "symbol": "LGOc3",
      "name": "Crude Oil (WTI)",
      "category": "Energy"
    },
    {
      "symbol": "NICKEL",
      "name": "Nickel",
      "category": "Metals"
    }
  ],
  "count": 3
}
```

### List Commodity Categories

Returns all distinct commodity categories.

**Endpoint:** `GET /commodity/categories/`

#### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/commodity/categories/?api_key=YOUR_API_KEY"
```

#### Example Response

```json
{
  "data": ["Energy", "Grains", "Livestock", "Metals", "Other", "Softs"],
  "count": 6
}
```

---

## Batch Query Patterns

### When to Use Which Endpoint Group

| Use Case | Endpoint | Why |
|----------|----------|-----|
| Latest prices for S&P 500 stocks with company metadata | `GET /sp500/latest/` | Enriched with name, sector, industry, weight |
| Historical data for S&P 500 stocks with company metadata | `GET /sp500/history/` | Enriched + constituent verification + alias resolution |
| Latest close for any stock (non-S&P 500) | `GET /ohlcv/latest_close/` | Covers all ~12,500 tickers |
| Historical data for any stock | `GET /ohlcv/` | Full filtering and pagination |
| Real-time OHLCV from EODHD | `GET /ohlcv/latest/` | Live data from EODHD API |
| Latest close for ETFs with metadata | `GET /etf/latest_close/` | Enriched with name, exchange, isin, currency |
| Real-time ETF OHLCV from EODHD | `GET /etf/latest/` | Live data from EODHD API |
| Historical data for ETFs | `GET /etf/` | Filtered to ETFs only via `etf_index_assets` |
| Latest close for indices with metadata | `GET /index/latest_close/` | Enriched with name, exchange, isin, currency |
| Real-time index OHLCV from EODHD | `GET /index/latest/` | Live data from EODHD API |
| Historical data for indices | `GET /index/` | Filtered to indices only via `etf_index_assets` |
| Latest close for government bonds with metadata | `GET /gov-bond/latest_close/` | Enriched with name, exchange, type, currency, country |
| Real-time gov bond OHLCV from EODHD | `GET /gov-bond/latest/` | Live data from EODHD API |
| Historical data for government bonds | `GET /gov-bond/` | Filtered to gov bonds only via `gov_bond_assets`; supports country filtering |
| Latest close for FX pairs with metadata | `GET /fx/latest_close/` | Enriched with name, exchange, type, currency, base_currency, quote_currency |
| Real-time FX OHLCV from EODHD | `GET /fx/latest/` | Live data from EODHD API |
| Historical data for FX pairs | `GET /fx/` | Filtered to FX pairs only via `fx_assets`; supports base_currency/quote_currency filtering |
| Latest close for crypto assets with metadata | `GET /crypto/latest_close/` | Enriched with name, exchange, type, currency, base_currency, quote_currency |
| Real-time crypto OHLCV from EODHD | `GET /crypto/latest/` | Live data from EODHD API |
| Historical data for crypto assets | `GET /crypto/` | Filtered to crypto via `crypto_assets`; supports base_currency/quote_currency filtering |
| Top 100 crypto by volume with notional value | `GET /crypto/top100/` | Ranked by latest volume DESC; includes close × volume as `notional_value` |
| Browse available crypto assets (no price data) | `GET /crypto/assets/` | Metadata only: code, name, exchange, type, base/quote currency; searchable |
| Latest close for UK stocks (LSE) with metadata | `GET /uk/latest_close/` | Enriched with name, exchange, type, sector, industry, isin, currency |
| Real-time UK stock OHLCV from EODHD | `GET /uk/latest/` | Live data from EODHD API |
| Historical data for UK stocks (LSE) | `GET /uk/` | Filtered to LSE via `uk_assets`; supports sector/industry filtering |
| Latest prices for FTSE 100 constituents with metadata | `GET /ftse100/latest/` | Enriched with name, sector, industry, isin, currency; constituent verification |
| Historical data for FTSE 100 constituents | `GET /ftse100/` | Filtered to FTSE 100 via `ftse100_constituents`; supports sector/industry filtering |
| Latest US Treasury bill rates | `GET /ust/bill/latest/` | Returns latest rates for all 4 bill tenors |
| Historical US Treasury bill rates | `GET /ust/bill/` | Paginated with date and tenor filtering |
| Latest US Treasury long-term rates | `GET /ust/long-term/latest/` | Returns latest rates for all 2 rate types |
| Historical US Treasury long-term rates | `GET /ust/long-term/` | Paginated with date and rate_type filtering |
| Latest US Treasury real yield rates | `GET /ust/real-yield/latest/` | Returns latest rates for all 5 real yield tenors |
| Historical US Treasury real yield rates | `GET /ust/real-yield/` | Paginated with date and tenor filtering |
| Latest US Treasury yield curve rates | `GET /ust/yield/latest/` | Returns latest rates for all 14 yield tenors |
| Historical US Treasury yield curve rates | `GET /ust/yield/` | Paginated with date and tenor filtering |
| Latest prices for commodities with metadata | `GET /commodity/latest/` | Enriched with name, category; supports category filtering |
| Historical data for commodities | `GET /commodity/` | Paginated with symbol, category, date, and price/volume filtering |
| Browse available commodity symbols | `GET /commodity/symbols/` | Metadata only: symbol, name, category; filterable by category |
| List all commodity categories | `GET /commodity/categories/` | Returns all distinct categories |

### S&P 500 vs Plain OHLCV

The S&P 500 endpoints add two features the plain OHLCV endpoints don't provide:

1. **Constituent verification** — Returns 404 if a ticker is not an active S&P 500 member
2. **Alias resolution** — Automatically maps mismatched tickers (e.g., `FISV` → `FI` in OHLCV data) via the `ticker_aliases` table

### Batch Endpoints Summary

| Endpoint | Batch Parameter | Returns | Enriched |
|----------|----------------|---------|----------|
| `GET /ohlcv/latest_close/` | `tickers=AAPL,MSFT,GOOGL` | Latest close per ticker (DB) | No |
| `GET /ohlcv/latest_close/` | *(omit tickers)* | Latest close for all ~12,500 tickers (DB) | No |
| `GET /ohlcv/latest_close/{ticker}` | — | Latest close for a single ticker (DB) | No |
| `GET /ohlcv/latest/` | `tickers=AAPL,MSFT,GOOGL` | Real-time OHLCV per ticker (EODHD) | No |
| `GET /ohlcv/` | `tickers=AAPL,MSFT,GOOGL` | Paginated history per ticker | No |
| `GET /sp500/latest/` | `tickers=AAPL,MSFT,GOOGL` | Latest S&P 500 OHLCV | Yes |
| `GET /sp500/latest/` | *(omit tickers)* | Latest for all 503 constituents | Yes |
| `GET /sp500/history/` | `tickers=AAPL,MSFT,GOOGL` | Paginated S&P 500 history | Yes |
| `GET /sp500/history/` | *(omit tickers)* | Paginated history for all active constituents | Yes |
| `GET /etf/latest_close/` | `tickers=SPY,QQQ,IWM` | Latest ETF close (DB) | Yes |
| `GET /etf/latest_close/` | *(omit tickers)* | Latest close for all ~5,500 ETFs (DB) | Yes |
| `GET /etf/latest_close/{ticker}` | — | Latest close for a single ETF (DB) | Yes |
| `GET /etf/latest/` | `tickers=SPY,QQQ,IWM` | Real-time ETF OHLCV (EODHD) | No |
| `GET /etf/` | `tickers=SPY,QQQ,IWM` | Paginated ETF history | No |
| `GET /index/latest_close/` | `tickers=GSPC,DJI,IXIC` | Latest index close (DB) | Yes |
| `GET /index/latest_close/` | *(omit tickers)* | Latest close for all ~1,600 indices (DB) | Yes |
| `GET /index/latest_close/{ticker}` | — | Latest close for a single index (DB) | Yes |
| `GET /index/latest/` | `tickers=GSPC,DJI,IXIC` | Real-time index OHLCV (EODHD) | No |
| `GET /index/` | `tickers=GSPC,DJI,IXIC` | Paginated index history | No |
| `GET /gov-bond/` | `tickers=US10Y,UK10Y,DE10Y` | Paginated gov bond history | No |
| `GET /gov-bond/` | `countries=US,DE,JP` | Paginated gov bond history by country | No |
| `GET /gov-bond/latest_close/` | `tickers=US10Y,UK10Y,DE10Y` | Latest gov bond close (DB) | Yes |
| `GET /gov-bond/latest_close/` | `countries=US,DE,JP` | Latest gov bond close by country (DB) | Yes |
| `GET /gov-bond/latest_close/` | *(omit tickers)* | Latest close for all 117 gov bonds (DB) | Yes |
| `GET /gov-bond/latest_close/{ticker}` | — | Latest close for a single gov bond (DB) | Yes |
| `GET /gov-bond/latest/` | `tickers=US10Y,UK10Y,DE10Y` | Real-time gov bond OHLCV (EODHD) | No |
| `GET /fx/` | `tickers=EURUSD,GBPUSD,USDJPY` | Paginated FX history | No |
| `GET /fx/` | `base_currency=EUR` | Paginated FX history by base currency | No |
| `GET /fx/` | `quote_currency=USD` | Paginated FX history by quote currency | No |
| `GET /fx/latest_close/` | `tickers=EURUSD,GBPUSD,USDJPY` | Latest FX close (DB) | Yes |
| `GET /fx/latest_close/` | `base_currency=EUR` | Latest FX close by base currency (DB) | Yes |
| `GET /fx/latest_close/` | `quote_currency=USD` | Latest FX close by quote currency (DB) | Yes |
| `GET /fx/latest_close/` | *(omit tickers)* | Latest close for all 948 FX pairs (DB) | Yes |
| `GET /fx/latest_close/{ticker}` | — | Latest close for a single FX pair (DB) | Yes |
| `GET /fx/latest/` | `tickers=EURUSD,GBPUSD,USDJPY` | Real-time FX OHLCV (EODHD) | No |
| `GET /crypto/` | `tickers=BTC-USD,ETH-USD,SOL-USD` | Paginated crypto history | No |
| `GET /crypto/` | `base_currency=BTC` | Paginated crypto history by base currency | No |
| `GET /crypto/` | `quote_currency=USD` | Paginated crypto history by quote currency | No |
| `GET /crypto/latest_close/` | `tickers=BTC-USD,ETH-USD,SOL-USD` | Latest crypto close (DB) | Yes |
| `GET /crypto/latest_close/` | `base_currency=BTC` | Latest crypto close by base currency (DB) | Yes |
| `GET /crypto/latest_close/` | `quote_currency=USD` | Latest crypto close by quote currency (DB) | Yes |
| `GET /crypto/latest_close/` | *(omit tickers)* | Latest close for all crypto assets (DB) | Yes |
| `GET /crypto/latest_close/{ticker}` | — | Latest close for a single crypto asset (DB) | Yes |
| `GET /crypto/latest/` | `tickers=BTC-USD,ETH-USD,SOL-USD` | Real-time crypto OHLCV (EODHD) | No |
| `GET /crypto/history/` | `tickers=BTC-USD,ETH-USD` | Paginated crypto history with metadata | Yes |
| `GET /crypto/history/` | *(omit tickers)* | Paginated history for all crypto assets | Yes |
| `GET /crypto/top100/` | — | Top 100 crypto by volume with notional_value | Yes |
| `GET /crypto/assets/` | — | List all crypto asset metadata (no OHLCV) | Yes |
| `GET /uk/` | `tickers=AZN,SHEL,HSBA` | Paginated UK stock history | No |
| `GET /uk/` | `sectors=Healthcare,Energy` | Paginated UK stock history by sector | No |
| `GET /uk/` | `industries=Oil Gas Consumable Fuels` | Paginated UK stock history by industry | No |
| `GET /uk/latest_close/` | `tickers=AZN,SHEL,HSBA` | Latest UK stock close (DB) | Yes |
| `GET /uk/latest_close/` | `sectors=Healthcare,Energy` | Latest UK stock close by sector (DB) | Yes |
| `GET /uk/latest_close/` | `industries=Oil Gas Consumable Fuels` | Latest UK stock close by industry (DB) | Yes |
| `GET /uk/latest_close/` | *(omit tickers)* | Latest close for all ~3,965 LSE stocks (DB) | Yes |
| `GET /uk/latest_close/{ticker}` | — | Latest close for a single UK stock (DB) | Yes |
| `GET /uk/latest/` | `tickers=AZN,SHEL,HSBA` | Real-time UK stock OHLCV (EODHD) | No |
| `GET /ftse100/` | `tickers=AZN,SHEL,HSBA` | Paginated FTSE 100 history | No |
| `GET /ftse100/` | `sectors=Healthcare,Energy` | Paginated FTSE 100 history by sector | No |
| `GET /ftse100/` | `industries=Oil Gas Consumable Fuels` | Paginated FTSE 100 history by industry | No |
| `GET /ftse100/latest/` | `tickers=AZN,SHEL,HSBA` | Latest FTSE 100 OHLCV | Yes |
| `GET /ftse100/latest/` | `sectors=Healthcare,Energy` | Latest FTSE 100 OHLCV by sector | Yes |
| `GET /ftse100/latest/` | `industries=Oil Gas Consumable Fuels` | Latest FTSE 100 OHLCV by industry | Yes |
| `GET /ftse100/latest/` | *(omit tickers)* | Latest for all 100 FTSE 100 constituents | Yes |
| `GET /ust/bill/` | `tenors=4-Week,13-Week` | Paginated bill rate history | No |
| `GET /ust/bill/latest/` | *(omit tenors)* | Latest for all 4 bill tenors | No |
| `GET /ust/long-term/` | `rate_types=LT Composite > 10 Years` | Paginated long-term rate history | No |
| `GET /ust/long-term/latest/` | *(omit rate_types)* | Latest for all 2 rate types | No |
| `GET /ust/real-yield/` | `tenors=5-Year,10-Year` | Paginated real yield history | No |
| `GET /ust/real-yield/latest/` | *(omit tenors)* | Latest for all 5 real yield tenors | No |
| `GET /ust/yield/` | `tenors=2-Year,10-Year,30-Year` | Paginated yield curve history | No |
| `GET /ust/yield/latest/` | *(omit tenors)* | Latest for all 14 yield tenors | No |
| `GET /commodity/` | `symbols=LGOc3,NICKEL,GDK` | Paginated commodity history | No |
| `GET /commodity/` | `category=Energy` | Paginated commodity history by category | No |
| `GET /commodity/latest/` | `symbols=LGOc3,NICKEL,GDK` | Latest commodity OHLCV | Yes |
| `GET /commodity/latest/` | `category=Energy` | Latest commodity OHLCV by category | Yes |
| `GET /commodity/latest/` | *(omit symbols)* | Latest for all commodities | Yes |
| `GET /commodity/symbols/` | `category=Energy` | List commodity symbols by category | Yes |
| `GET /commodity/symbols/` | *(omit category)* | List all commodity symbols | Yes |
| `GET /commodity/categories/` | — | List all distinct categories | No |
