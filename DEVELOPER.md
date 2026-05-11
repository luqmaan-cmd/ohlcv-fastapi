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
