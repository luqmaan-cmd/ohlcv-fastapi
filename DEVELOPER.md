# OHLCV Data API

REST API for accessing OHLCV (Open, High, Low, Close, Volume) financial data.

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

## Endpoints

### 1. List OHLCV Data

Returns paginated OHLCV records with filtering and sorting options.

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
| `per_page` | integer | `100` | Records per page (min: 1, max: 1000) |

#### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25&ticker=AAPL&start_date=2025-01-01&end_date=2025-12-31&sort_by=volume&sort_order=desc&page=1&per_page=5"
```

#### Example Response

```json
{
  "data": [
    {
      "ticker": "AAPL",
      "date": "2025-03-15",
      "open": "210.5000",
      "high": "215.2000",
      "low": "209.8000",
      "close": "214.2500",
      "adjusted_close": "214.2500",
      "volume": 85000000,
      "asset_isin": "US0378331005",
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2025-03-15T20:00:00",
      "updated_at": "2025-03-15T20:00:00"
    }
  ],
  "total": 250,
  "page": 1,
  "per_page": 5,
  "total_pages": 50,
  "has_next": true,
  "has_prev": false
}
```

---

### 2. Get Latest OHLCV by Ticker

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
  "date": "2026-04-06",
  "open": "256.9625",
  "high": "262.1600",
  "low": "256.4800",
  "close": "258.8600",
  "adjusted_close": "258.8600",
  "volume": 29319825,
  "asset_isin": "US0378331005",
  "id": "8c3e6ce2-baae-4989-bbc1-80df76a981c3",
  "created_at": "2026-04-07T12:05:16.618365",
  "updated_at": "2026-04-07T14:08:59.341410"
}
```

---

### 3. Get OHLCV Statistics

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
  "count": 11419,
  "earliest_date": "1980-12-12",
  "latest_date": "2026-04-06",
  "avg_volume": 308260453.67,
  "min_close": "10.9984",
  "max_close": "702.1000",
  "avg_close": "118.3614",
  "fifty_two_week_high": "286.1900",
  "fifty_two_week_low": "190.4200"
}
```

---

### 4. Get All Tickers

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

### 5. Get OHLCV by ID

Returns a single OHLCV record by its UUID.

**Endpoint:** `GET /ohlcv/{ohlcv_id}`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ohlcv_id` | string (UUID) | Record ID |

#### Example Request

```bash
curl -X GET "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/8c3e6ce2-baae-4989-bbc1-80df76a981c3?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

#### Example Response

```json
{
  "ticker": "AAPL",
  "date": "2026-04-06",
  "open": "256.9625",
  "high": "262.1600",
  "low": "256.4800",
  "close": "258.8600",
  "adjusted_close": "258.8600",
  "volume": 29319825,
  "asset_isin": "US0378331005",
  "id": "8c3e6ce2-baae-4989-bbc1-80df76a981c3",
  "created_at": "2026-04-07T12:05:16.618365",
  "updated_at": "2026-04-07T14:08:59.341410"
}
```

---

### 6. Create OHLCV Record

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

### 7. Bulk Create OHLCV Records

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

### 8. Update OHLCV Record

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
curl -X PUT "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/8c3e6ce2-baae-4989-bbc1-80df76a981c3?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25" \
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
  "date": "2026-04-06",
  "open": "256.9625",
  "high": "262.1600",
  "low": "256.4800",
  "close": "260.0000",
  "adjusted_close": "258.8600",
  "volume": 35000000,
  "asset_isin": "US0378331005",
  "id": "8c3e6ce2-baae-4989-bbc1-80df76a981c3",
  "created_at": "2026-04-07T12:05:16.618365",
  "updated_at": "2026-04-10T12:00:00"
}
```

---

### 9. Delete OHLCV Record

Deletes an OHLCV record.

**Endpoint:** `DELETE /ohlcv/{ohlcv_id}`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ohlcv_id` | string (UUID) | Record ID |

#### Example Request

```bash
curl -X DELETE "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/8c3e6ce2-baae-4989-bbc1-80df76a981c3?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

#### Example Response

```
HTTP 204 No Content
```

---

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Validation error message"
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
| `data` | array | Array of OHLCV records |
| `total` | integer | Total number of matching records |
| `page` | integer | Current page number |
| `per_page` | integer | Records per page |
| `total_pages` | integer | Total number of pages |
| `has_next` | boolean | Whether next page exists |
| `has_prev` | boolean | Whether previous page exists |

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
  --allow-unauthenticated \
  --port 8080
```

### View Logs
```bash
gcloud run logs read --service=ohlcv-api --region=europe-west2
```

