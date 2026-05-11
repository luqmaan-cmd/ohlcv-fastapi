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
| `api_key` | `0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25` |

**Example:**
```
https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Invalid or missing API key"
}
```

## Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Required for POST/PUT requests |
| `Accept` | `application/json` | Response format (default: JSON) |

---

## S&P 500 Batch Queries

The S&P 500 endpoints are the recommended way to query data for US large-cap stocks. They provide OHLCV data enriched with company metadata (name, sector, industry, index weight) and include two features the plain OHLCV endpoints don't offer:

1. **Constituent verification** — Returns `404` if a requested ticker is not an active S&P 500 member
2. **Automatic alias resolution** — Maps mismatched tickers (e.g. `FISV` → `FI` in OHLCV data) via the `ticker_aliases` table

### Get Latest S&P 500 Data for Specific Companies

Returns the most recent OHLCV record for the specified S&P 500 constituents, sorted by index weight descending. Enriched with name, sector, industry, and weight.

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
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/latest/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25&tickers=AAPL,MSFT,GOOGL"
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
      "weight": "0.067100",
      "date": "2026-05-07",
      "open": "289.2700",
      "high": "292.1300",
      "low": "285.7800",
      "close": "287.4400",
      "adjusted_close": "287.4400",
      "volume": 40410371,
      "asset_isin": "US0378331005"
    },
    {
      "ticker": "MSFT",
      "name": "Microsoft Corporation",
      "sector": "Technology",
      "industry": "Software - Infrastructure",
      "weight": "0.049700",
      "date": "2026-05-07",
      "open": "420.1100",
      "high": "427.9800",
      "low": "418.7600",
      "close": "420.7700",
      "adjusted_close": "420.7700",
      "volume": 33917670,
      "asset_isin": "US5949181045"
    },
    {
      "ticker": "GOOGL",
      "name": "Alphabet Inc Class A",
      "sector": "Communication Services",
      "industry": "Internet Content & Information",
      "weight": "0.036900",
      "date": "2026-05-07",
      "open": "399.9950",
      "high": "400.1000",
      "low": "392.6800",
      "close": "397.9900",
      "adjusted_close": "397.9900",
      "volume": 22403998,
      "asset_isin": "US02079K3059"
    }
  ],
  "count": 3
}
```

#### Example Request — All S&P 500 Constituents

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/latest/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

Returns all 503 constituents with latest OHLCV data, sorted by index weight descending.

> **Note:** Ticker alias resolution is applied automatically. For example, if you request `FISV`, the API resolves it to `FI` in the OHLCV data via the `ticker_aliases` table.

---

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
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/history/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25&tickers=AAPL,MSFT,GOOGL&start_date=2026-04-01&end_date=2026-04-07&sort_by=date&sort_order=desc&page=1&per_page=10"
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
      "weight": "0.067100",
      "date": "2026-04-07",
      "open": "256.1600",
      "high": "256.2000",
      "low": "245.7000",
      "close": "253.5000",
      "adjusted_close": "253.5000",
      "volume": 62148000,
      "asset_isin": "US0378331005"
    },
    {
      "ticker": "GOOGL",
      "name": "Alphabet Inc Class A",
      "sector": "Communication Services",
      "industry": "Internet Content & Information",
      "weight": "0.036900",
      "date": "2026-04-07",
      "open": "302.7300",
      "high": "305.6300",
      "low": "297.7200",
      "close": "305.4600",
      "adjusted_close": "305.4600",
      "volume": 23205400,
      "asset_isin": "US02079K3059"
    },
    {
      "ticker": "MSFT",
      "name": "Microsoft Corporation",
      "sector": "Technology",
      "industry": "Software - Infrastructure",
      "weight": "0.049700",
      "date": "2026-04-07",
      "open": "370.3400",
      "high": "372.4500",
      "low": "366.5600",
      "close": "372.2900",
      "adjusted_close": "372.2900",
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
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/history/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25&start_date=2026-05-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=10"
```

Returns paginated historical OHLCV data for all active S&P 500 constituents within the specified date range. Ticker alias resolution is applied automatically.

---

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
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25&page=1&per_page=5"
```

#### Example Request — Filter by Sector

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25&sector=Technology&per_page=5"
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
      "weight": "0.000500",
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
      "weight": "0.067100",
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
      "weight": "0.005700",
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

---

## OHLCV Batch Queries

The plain OHLCV endpoints support batch queries for any ticker in the database (not just S&P 500). Use these when you need data for non-S&P 500 stocks or don't need the enriched metadata.

### Batch Get Latest OHLCV

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
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/latest/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25&tickers=AAPL,MSFT,GOOGL"
```

#### Example Response — Specific Tickers

```json
{
  "data": [
    {
      "ticker": "AAPL",
      "date": "2026-05-07",
      "open": "289.2700",
      "high": "292.1300",
      "low": "285.7800",
      "close": "287.4400",
      "adjusted_close": "287.4400",
      "volume": 40410371,
      "asset_isin": "US0378331005",
      "id": "b7ed13ca-94fb-4ac3-a952-bb46febe0a4b",
      "created_at": "2026-05-08T02:02:41.827964",
      "updated_at": "2026-05-08T02:02:41.827964"
    },
    {
      "ticker": "GOOGL",
      "date": "2026-05-07",
      "open": "399.9950",
      "high": "400.1000",
      "low": "392.6800",
      "close": "397.9900",
      "adjusted_close": "397.9900",
      "volume": 22403998,
      "asset_isin": "US02079K3059",
      "id": "fa557734-4a27-4e10-a485-894d73580693",
      "created_at": "2026-05-08T02:18:10.054961",
      "updated_at": "2026-05-08T02:18:10.054961"
    },
    {
      "ticker": "MSFT",
      "date": "2026-05-07",
      "open": "420.1100",
      "high": "427.9800",
      "low": "418.7600",
      "close": "420.7700",
      "adjusted_close": "420.7700",
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
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/latest/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

> **Warning:** Omitting the `tickers` parameter returns the latest record for every ticker in the database (~12,500 records). The response can be several MB. Use with caution in bandwidth-constrained environments.

---

### List OHLCV Data (with Batch Tickers)

Returns paginated OHLCV records with filtering and sorting options. Supports batch queries via the `tickers` parameter.

**Endpoint:** `GET /ohlcv/`

#### Query Parameters

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

#### Example Request — Single Ticker

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25&ticker=AAPL&start_date=2026-05-01&end_date=2026-05-07&sort_by=volume&sort_order=desc&page=1&per_page=5"
```

#### Example Request — Batch Multiple Tickers

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25&tickers=AAPL,MSFT&start_date=2026-05-01&end_date=2026-05-07&sort_by=date&sort_order=desc&page=1&per_page=3"
```

#### Example Response

```json
{
  "data": [
    {
      "ticker": "MSFT",
      "date": "2026-05-07",
      "open": "420.1100",
      "high": "427.9800",
      "low": "418.7600",
      "close": "420.7700",
      "adjusted_close": "420.7700",
      "volume": 33917670,
      "asset_isin": "US5949181045",
      "id": "c60b9d4f-55ad-435e-b706-8bbddc6f5f55",
      "created_at": "2026-05-08T02:26:05.444586",
      "updated_at": "2026-05-08T02:26:05.444586"
    },
    {
      "ticker": "AAPL",
      "date": "2026-05-07",
      "open": "289.2700",
      "high": "292.1300",
      "low": "285.7800",
      "close": "287.4400",
      "adjusted_close": "287.4400",
      "volume": 40410371,
      "asset_isin": "US0378331005",
      "id": "b7ed13ca-94fb-4ac3-a952-bb46febe0a4b",
      "created_at": "2026-05-08T02:02:41.827964",
      "updated_at": "2026-05-08T02:02:41.827964"
    },
    {
      "ticker": "AAPL",
      "date": "2026-05-06",
      "open": "281.9200",
      "high": "288.0300",
      "low": "281.0700",
      "close": "287.5100",
      "adjusted_close": "287.5100",
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

## Single-Ticker Endpoints

### Get Latest OHLCV by Ticker

Returns the most recent OHLCV record for a given ticker.

**Endpoint:** `GET /ohlcv/latest/{ticker}`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | Ticker symbol (e.g., `AAPL`) |

#### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/latest/AAPL?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

#### Example Response

```json
{
  "ticker": "AAPL",
  "date": "2026-05-07",
  "open": "289.2700",
  "high": "292.1300",
  "low": "285.7800",
  "close": "287.4400",
  "adjusted_close": "287.4400",
  "volume": 40410371,
  "asset_isin": "US0378331005",
  "id": "b7ed13ca-94fb-4ac3-a952-bb46febe0a4b",
  "created_at": "2026-05-08T02:02:41.827964",
  "updated_at": "2026-05-08T02:02:41.827964"
}
```

---

### Get OHLCV Statistics

Returns statistical summary for a ticker including 52-week high/low.

**Endpoint:** `GET /ohlcv/stats/{ticker}`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | Ticker symbol (e.g., `AAPL`) |

#### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/stats/AAPL?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

#### Example Response

```json
{
  "ticker": "AAPL",
  "count": 11442,
  "earliest_date": "1980-12-12",
  "latest_date": "2026-05-07",
  "avg_volume": 307735328.81,
  "min_close": "10.9984",
  "max_close": "702.1000",
  "avg_close": "118.6657226009438909",
  "fifty_two_week_high": "287.5100",
  "fifty_two_week_low": "195.2700"
}
```

---

### Get All Tickers

Returns a list of all available ticker symbols.

**Endpoint:** `GET /tickers/`

#### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/tickers/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

#### Example Response

```json
["A", "AA", "AABB", "AACAY", "AACB", "AAPL", "MSFT", "GOOGL"]
```

---

## CRUD Endpoints

### Get OHLCV by ID

Returns a single OHLCV record by its UUID.

**Endpoint:** `GET /ohlcv/{ohlcv_id}`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ohlcv_id` | string (UUID) | Record ID |

#### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/b7ed13ca-94fb-4ac3-a952-bb46febe0a4b?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

#### Example Response

```json
{
  "ticker": "AAPL",
  "date": "2026-05-07",
  "open": "289.2700",
  "high": "292.1300",
  "low": "285.7800",
  "close": "287.4400",
  "adjusted_close": "287.4400",
  "volume": 40410371,
  "asset_isin": "US0378331005",
  "id": "b7ed13ca-94fb-4ac3-a952-bb46febe0a4b",
  "created_at": "2026-05-08T02:02:41.827964",
  "updated_at": "2026-05-08T02:02:41.827964"
}
```

---

### Create OHLCV Record

Creates a new OHLCV record.

**Endpoint:** `POST /ohlcv/`

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | Ticker symbol (max 20 chars) |
| `date` | date | Yes | Trading date (YYYY-MM-DD) |
| `open` | decimal | No | Opening price |
| `high` | decimal | No | High price |
| `low` | decimal | No | Low price |
| `close` | decimal | No | Closing price |
| `adjusted_close` | decimal | No | Adjusted closing price |
| `volume` | integer | No | Trading volume |
| `asset_isin` | string | No | ISIN code (max 50 chars) |

#### Example Request

```bash
curl -X POST "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "date": "2026-04-10",
    "open": 260.50,
    "high": 265.00,
    "low": 259.00,
    "close": 263.75,
    "adjusted_close": 263.75,
    "volume": 30000000,
    "asset_isin": "US0378331005"
  }'
```

#### Example Response

```json
{
  "ticker": "AAPL",
  "date": "2026-04-10",
  "open": "260.5000",
  "high": "265.0000",
  "low": "259.0000",
  "close": "263.7500",
  "adjusted_close": "263.7500",
  "volume": 30000000,
  "asset_isin": "US0378331005",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-04-10T12:00:00",
  "updated_at": "2026-04-10T12:00:00"
}
```

---

### Bulk Create OHLCV Records

Creates multiple OHLCV records in a single request.

**Endpoint:** `POST /ohlcv/bulk/`

#### Request Body

| Field | Type | Description |
|-------|------|-------------|
| `records` | array | Array of OHLCV records (see Create schema) |

#### Example Request

```bash
curl -X POST "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/bulk/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25" \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {
        "ticker": "AAPL",
        "date": "2026-04-10",
        "open": 260.50,
        "high": 265.00,
        "low": 259.00,
        "close": 263.75,
        "volume": 30000000,
        "asset_isin": "US0378331005"
      },
      {
        "ticker": "MSFT",
        "date": "2026-04-10",
        "open": 375.00,
        "high": 380.00,
        "low": 372.00,
        "close": 378.50,
        "volume": 15000000,
        "asset_isin": "US5949181045"
      }
    ]
  }'
```

#### Example Response

```json
{
  "inserted": 2,
  "failed": 0,
  "errors": []
}
```

---

### Update OHLCV Record

Updates an existing OHLCV record.

**Endpoint:** `PUT /ohlcv/{ohlcv_id}`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ohlcv_id` | string (UUID) | Record ID |

#### Request Body

All fields are optional. Only provided fields will be updated.

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Ticker symbol |
| `date` | date | Trading date |
| `open` | decimal | Opening price |
| `high` | decimal | High price |
| `low` | decimal | Low price |
| `close` | decimal | Closing price |
| `adjusted_close` | decimal | Adjusted closing price |
| `volume` | integer | Trading volume |
| `asset_isin` | string | ISIN code |

#### Example Request

```bash
curl -X PUT "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/b7ed13ca-94fb-4ac3-a952-bb46febe0a4b?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25" \
  -H "Content-Type: application/json" \
  -d '{
    "close": 260.00,
    "volume": 35000000
  }'
```

#### Example Response

```json
{
  "ticker": "AAPL",
  "date": "2026-05-07",
  "open": "289.2700",
  "high": "292.1300",
  "low": "285.7800",
  "close": "260.0000",
  "adjusted_close": "287.4400",
  "volume": 35000000,
  "asset_isin": "US0378331005",
  "id": "b7ed13ca-94fb-4ac3-a952-bb46febe0a4b",
  "created_at": "2026-05-08T02:02:41.827964",
  "updated_at": "2026-05-08T12:00:00"
}
```

#### Example Response

```json
{
  "ticker": "AAPL",
  "date": "2026-05-07",
  "open": "289.2700",
  "high": "292.1300",
  "low": "285.7800",
  "close": "287.4400",
  "adjusted_close": "287.4400",
  "volume": 40410371,
  "asset_isin": "US0378331005",
  "id": "b7ed13ca-94fb-4ac3-a952-bb46febe0a4b",
  "created_at": "2026-05-08T02:02:41.827964",
  "updated_at": "2026-05-08T02:02:41.827964"
}
```

---

### Delete OHLCV Record

Deletes an OHLCV record.

**Endpoint:** `DELETE /ohlcv/{ohlcv_id}`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ohlcv_id` | string (UUID) | Record ID |

#### Example Request

```bash
curl -X DELETE "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/b7ed13ca-94fb-4ac3-a952-bb46febe0a4b?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

#### Example Response

```
HTTP 204 No Content
```

---

## Ticker Aliases

Ticker aliases resolve mismatches between S&P 500 ticker symbols and the ticker symbols used in the OHLCV data table. The S&P 500 endpoints apply alias resolution automatically — these CRUD endpoints are for managing the alias mappings.

### List Ticker Aliases

**Endpoint:** `GET /aliases/`

#### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/aliases/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

#### Example Response

```json
{
  "data": [
    { "sp500_ticker": "FISV", "ohlcv_ticker": "FI" },
    { "sp500_ticker": "MRSH", "ohlcv_ticker": "MMC" }
  ],
  "total": 2
}
```

---

### Get Ticker Alias

**Endpoint:** `GET /aliases/{sp500_ticker}`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `sp500_ticker` | string | S&P 500 ticker symbol (e.g., `FISV`) |

#### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/aliases/FISV?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

#### Example Response

```json
{ "sp500_ticker": "FISV", "ohlcv_ticker": "FI" }
```

---

### Create Ticker Alias

**Endpoint:** `POST /aliases/`

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sp500_ticker` | string | Yes | S&P 500 ticker symbol |
| `ohlcv_ticker` | string | Yes | Corresponding ticker in the OHLCV data table |

#### Example Request

```bash
curl -X POST "https://ohlcv-api-832081557693.europe-west2.run.app/aliases/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25" \
  -H "Content-Type: application/json" \
  -d '{"sp500_ticker": "FISV", "ohlcv_ticker": "FI"}'
```

#### Example Response

```json
{ "sp500_ticker": "FISV", "ohlcv_ticker": "FI" }
```

---

### Update Ticker Alias

**Endpoint:** `PUT /aliases/{sp500_ticker}`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `sp500_ticker` | string | S&P 500 ticker symbol |

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ohlcv_ticker` | string | Yes | New OHLCV ticker mapping |

#### Example Request

```bash
curl -X PUT "https://ohlcv-api-832081557693.europe-west2.run.app/aliases/FISV?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25" \
  -H "Content-Type: application/json" \
  -d '{"ohlcv_ticker": "FISV"}'
```

#### Example Response

```json
{ "sp500_ticker": "FISV", "ohlcv_ticker": "FISV" }
```

---

### Delete Ticker Alias

**Endpoint:** `DELETE /aliases/{sp500_ticker}`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `sp500_ticker` | string | S&P 500 ticker symbol |

#### Example Request

```bash
curl -X DELETE "https://ohlcv-api-832081557693.europe-west2.run.app/aliases/FISV?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

#### Example Response

```
HTTP 204 No Content
```

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
| 4 | **Allowed tables** | Only the following tables may be referenced: `ohlcv_data`, `assets`, `sp500_constituents`, `ticker_aliases`, `tickers`. |

### Allowed Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `ohlcv_data` | OHLCV price data (43M+ rows) | `ticker`, `date`, `open`, `high`, `low`, `close`, `adjusted_close`, `volume`, `asset_isin` |
| `assets` | Asset metadata | `isin`, `code`, `name`, `gicSector`, `description`, `countryName` |
| `sp500_constituents` | S&P 500 index constituents | `code`, `name`, `sector`, `industry`, `weight`, `is_active` |
| `ticker_aliases` | Ticker symbol mappings | `sp500_ticker`, `ohlcv_ticker` |
| `tickers` | Unique ticker lookup table | `ticker` |

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | SQL SELECT query to execute |

### Example Request — Simple Query

```bash
curl -X POST "https://ohlcv-api-832081557693.europe-west2.run.app/sql/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT ticker, date, close, volume FROM ohlcv_data WHERE ticker = '\''AAPL'\'' ORDER BY date DESC LIMIT 5"}'
```

### Example Response

```json
{
  "columns": ["ticker", "date", "close", "volume"],
  "rows": [
    {"ticker": "AAPL", "date": "2026-05-07", "close": "287.4400", "volume": 40410371},
    {"ticker": "AAPL", "date": "2026-05-06", "close": "287.5100", "volume": 58336100},
    {"ticker": "AAPL", "date": "2026-05-05", "close": "281.9200", "volume": 48263100},
    {"ticker": "AAPL", "date": "2026-05-02", "close": "280.8800", "volume": 42187400},
    {"ticker": "AAPL", "date": "2026-05-01", "close": "276.4100", "volume": 36452700}
  ],
  "row_count": 5,
  "truncated": false
}
```

### Example Request — CTE with JOIN

```bash
curl -X POST "https://ohlcv-api-832081557693.europe-west2.run.app/sql/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25" \
  -H "Content-Type: application/json" \
  -d '{"query": "WITH latest AS (SELECT ticker, MAX(date) AS latest_date FROM ohlcv_data WHERE ticker IN ('\''AAPL'\'', '\''MSFT'\'') GROUP BY ticker) SELECT l.ticker, l.latest_date, o.close, o.volume FROM latest l JOIN ohlcv_data o ON o.ticker = l.ticker AND o.date = l.latest_date ORDER BY l.ticker"}'
```

### Example Request — S&P 500 with Asset Metadata

```bash
curl -X POST "https://ohlcv-api-832081557693.europe-west2.run.app/sql/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25" \
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
  "detail": "Table(s) not allowed: pg_class. Allowed tables: assets, ohlcv_data, sp500_constituents, ticker_aliases, tickers."
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

## Batch Query Patterns

### When to Use S&P 500 vs Plain OHLCV

| Use Case | Endpoint | Why |
|----------|----------|-----|
| Latest prices for S&P 500 stocks with company metadata | `GET /sp500/latest/` | Enriched with name, sector, industry, weight |
| Historical data for S&P 500 stocks with company metadata | `GET /sp500/history/` | Enriched + constituent verification + alias resolution |
| Latest prices for any stock (non-S&P 500) | `GET /ohlcv/latest/` | Covers all ~12,500 tickers |
| Historical data for any stock | `GET /ohlcv/` | Full filtering and pagination |

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

---

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized

```json
{
  "detail": "Invalid or missing API key"
}
```

### 404 Not Found

```json
{
  "detail": "OHLCV data not found"
}
```

### 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "loc": ["body", "ticker"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Running the API

### Development

```bash
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Production

```bash
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
```

---

## Interactive Documentation

| Documentation | URL |
|---------------|-----|
| Swagger UI | https://ohlcv-api-832081557693.europe-west2.run.app/docs |
| ReDoc | https://ohlcv-api-832081557693.europe-west2.run.app/redoc |
| OpenAPI Spec | https://ohlcv-api-832081557693.europe-west2.run.app/openapi.json |

For local development, use `http://localhost:8001` instead.

---

## Response Fields Reference

### OHLCV Data Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique record identifier |
| `ticker` | string | Stock ticker symbol |
| `date` | date | Trading date |
| `open` | decimal | Opening price |
| `high` | decimal | Highest price of the day |
| `low` | decimal | Lowest price of the day |
| `close` | decimal | Closing price |
| `adjusted_close` | decimal | Dividend/split adjusted closing price |
| `volume` | integer | Trading volume |
| `asset_isin` | string | International Securities Identification Number |
| `created_at` | datetime | Record creation timestamp |
| `updated_at` | datetime | Record last update timestamp |

### Paginated Response Object

| Field | Type | Description |
|-------|------|-------------|
| `data` | array | Array of records |
| `total` | integer | Total number of matching records |
| `page` | integer | Current page number |
| `per_page` | integer | Records per page |
| `total_pages` | integer | Total number of pages |
| `has_next` | boolean | Whether next page exists |
| `has_prev` | boolean | Whether previous page exists |

### Batch Latest Response Object

| Field | Type | Description |
|-------|------|-------------|
| `data` | array | Array of OHLCV records (one per ticker, sorted by ticker ascending) |
| `count` | integer | Number of tickers returned |

### S&P 500 Constituent Object

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Stock ticker symbol |
| `name` | string | Company name |
| `sector` | string | GIC sector from S&P 500 data |
| `industry` | string | GIC industry from S&P 500 data |
| `weight` | decimal | Index weight percentage |
| `is_active` | boolean | Whether currently in the S&P 500 |
| `isin` | string | International Securities Identification Number (from `assets` table) |
| `gic_sector` | string | GIC sector from `assets` table |
| `description` | string | Company description (from `assets` table) |
| `country` | string | Country of incorporation (from `assets` table) |

### S&P 500 Latest Item Object

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Stock ticker symbol |
| `name` | string | Company name |
| `sector` | string | GIC sector |
| `industry` | string | GIC industry |
| `weight` | decimal | Index weight percentage |
| `date` | date | Latest trading date |
| `open` | decimal | Opening price |
| `high` | decimal | Highest price of the day |
| `low` | decimal | Lowest price of the day |
| `close` | decimal | Closing price |
| `adjusted_close` | decimal | Dividend/split adjusted closing price |
| `volume` | integer | Trading volume |
| `asset_isin` | string | International Securities Identification Number |

### S&P 500 Latest Response Object

| Field | Type | Description |
|-------|------|-------------|
| `data` | array | Array of S&P 500 Latest Items (sorted by weight descending) |
| `count` | integer | Number of constituents returned |

### S&P 500 History Item Object

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Stock ticker symbol |
| `name` | string | Company name |
| `sector` | string | GIC sector |
| `industry` | string | GIC industry |
| `weight` | decimal | Index weight percentage |
| `date` | date | Trading date |
| `open` | decimal | Opening price |
| `high` | decimal | Highest price of the day |
| `low` | decimal | Lowest price of the day |
| `close` | decimal | Closing price |
| `adjusted_close` | decimal | Dividend/split adjusted closing price |
| `volume` | integer | Trading volume |
| `asset_isin` | string | International Securities Identification Number |

### S&P 500 History Response Object

| Field | Type | Description |
|-------|------|-------------|
| `data` | array | Array of S&P 500 History Items |
| `total` | integer | Total number of matching records |
| `page` | integer | Current page number |
| `per_page` | integer | Records per page |
| `total_pages` | integer | Total number of pages |
| `has_next` | boolean | Whether next page exists |
| `has_prev` | boolean | Whether previous page exists |

### Ticker Alias Object

| Field | Type | Description |
|-------|------|-------------|
| `sp500_ticker` | string | Ticker symbol in the S&P 500 constituents table |
| `ohlcv_ticker` | string | Corresponding ticker symbol in the OHLCV data table |

### Ticker Alias List Response Object

| Field | Type | Description |
|-------|------|-------------|
| `data` | array | Array of Ticker Alias objects |
| `total` | integer | Total number of aliases |

### SQL Query Response Object

| Field | Type | Description |
|-------|------|-------------|
| `columns` | array | Column names in the result set |
| `rows` | array | Result rows as list of dictionaries |
| `row_count` | integer | Number of rows returned |
| `truncated` | boolean | `true` if the result was truncated due to the row limit |

---

## Deployment

The API is deployed on GCP Cloud Run.

### Production URL
```
https://ohlcv-api-832081557693.europe-west2.run.app
```

### Deploy Updates
```bash
./deploy.sh
```

### Manual Deploy
```bash
gcloud builds submit --tag gcr.io/testgke-412710/ohlcv-api
gcloud run deploy ohlcv-api \
  --image gcr.io/testgke-412710/ohlcv-api \
  --platform managed \
  --region europe-west2 \
  --vpc-connector bls-connector \
  --set-secrets="DB_HOST=db-host:latest,DB_USER=db-user:latest,DB_PASSWORD=db-password:latest,DB_NAME=db-name:latest,DB_PORT=db-port:latest,API_KEY=api-key:latest" \
  --allow-unauthenticated \
  --port 8080
```

### View Logs
```bash
gcloud run logs read --service=ohlcv-api --region=europe-west2
```
