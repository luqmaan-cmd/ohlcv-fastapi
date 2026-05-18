# OHLCV Data API

High-performance REST API for OHLCV (Open, High, Low, Close, Volume) financial data with **batch queries**, **S&P 500 enriched endpoints**, **ETF & Index data**, and **Government Bond data**. Query latest prices or full history for multiple companies, ETFs, indices, or government bonds in a single request, with automatic ticker alias resolution and constituent verification.

## Highlights

- **Batch queries** — Request data for multiple companies in one API call using `tickers=AAPL,MSFT,GOOGL`
- **S&P 500 enriched data** — OHLCV records enriched with company name, sector, industry, and index weight
- **ETF & Index data** — Dedicated endpoints for ETFs (SPY, QQQ, IWM…) and indices (GSPC, DJI, IXIC…) with enriched metadata (name, exchange, ISIN, currency)
- **Government Bond data** — Dedicated endpoints for government bonds (US10Y, UK10Y, DE10Y…) with enriched metadata (name, exchange, type, currency, country) and country filtering
- **SQL query endpoint** — Execute read-only SQL queries directly against the database with built-in guardrails (read-only, timeout, row limit, allowed tables)
- **Automatic alias resolution** — Mismatched tickers (e.g. `FISV` → `FI`) resolved transparently via the `ticker_aliases` table
- **Constituent verification** — S&P 500 endpoints reject invalid tickers with clear error messages
- **LATERAL join performance** — Latest-price queries use `CROSS JOIN LATERAL` for ~50ms response times across 12,500+ tickers
- **GZip compression** — Automatic response compression for payloads > 1KB

## Quick Start

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the API
uvicorn main:app --host 0.0.0.0 --port 8001
```

## Documentation

- **API Reference**: See [DEVELOPER.md](./DEVELOPER.md) for full endpoint documentation with real request/response examples
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## Project Structure

```
├── main.py          # FastAPI application and endpoints
├── models.py        # SQLAlchemy database models
├── schemas.py       # Pydantic request/response schemas
├── database.py      # Database connection configuration
├── requirements.txt # Python dependencies
├── .env             # Environment variables
└── DEVELOPER.md     # Full API reference
```

## Batch Queries

All "latest" and "history" endpoints support batch queries via the `tickers` query parameter. Instead of making N requests for N companies, make one:

```bash
# Latest OHLCV for 3 companies — one request
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/latest/?tickers=AAPL,MSFT,GOOGL&api_key=YOUR_KEY"

# Latest S&P 500 data for specific companies — enriched with name, sector, weight
curl "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/latest/?tickers=AAPL,MSFT,GOOGL&api_key=YOUR_KEY"

# Historical OHLCV for multiple S&P 500 companies with date range
curl "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/history/?tickers=AAPL,MSFT,GOOGL&start_date=2025-01-01&end_date=2025-12-31&api_key=YOUR_KEY"

# Historical OHLCV for multiple tickers (non-S&P 500)
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/?tickers=AAPL,MSFT,GOOGL&start_date=2025-01-01&end_date=2025-12-31&api_key=YOUR_KEY"

# Latest OHLCV for specific ETFs — enriched with name, exchange, ISIN, currency
curl "https://ohlcv-api-832081557693.europe-west2.run.app/etf/latest/?tickers=SPY,QQQ,IWM&api_key=YOUR_KEY"

# Latest OHLCV for specific indices
curl "https://ohlcv-api-832081557693.europe-west2.run.app/index/latest/?tickers=GSPC,DJI,IXIC&api_key=YOUR_KEY"

# Historical OHLCV for ETFs with date range
curl "https://ohlcv-api-832081557693.europe-west2.run.app/etf/?tickers=SPY,QQQ&start_date=2025-01-01&end_date=2025-12-31&api_key=YOUR_KEY"

# Latest OHLCV for specific government bonds — enriched with name, exchange, type, currency, country
curl "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest/?tickers=US10Y,UK10Y,DE10Y&api_key=YOUR_KEY"

# Latest OHLCV for all government bonds from specific countries
curl "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest/?countries=US,DE,JP&api_key=YOUR_KEY"

# Historical OHLCV for government bonds with date range
curl "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/?tickers=US10Y,UK10Y&start_date=2025-01-01&end_date=2025-12-31&api_key=YOUR_KEY"
```

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
| `GET /etf/` | `tickers=SPY,QQQ,IWM` | Paginated ETF history | No |
| `GET /etf/latest/` | `tickers=SPY,QQQ,IWM` | Latest ETF OHLCV | Yes |
| `GET /etf/latest/` | *(omit tickers)* | Latest for all ETFs | Yes |
| `GET /etf/latest/{ticker}` | — | Latest for a single ETF | Yes |
| `GET /index/` | `tickers=GSPC,DJI,IXIC` | Paginated index history | No |
| `GET /index/latest/` | `tickers=GSPC,DJI,IXIC` | Latest index OHLCV | Yes |
| `GET /index/latest/` | *(omit tickers)* | Latest for all indices | Yes |
| `GET /index/latest/{ticker}` | — | Latest for a single index | Yes |
| `GET /gov-bond/` | `tickers=US10Y,UK10Y,DE10Y` | Paginated gov bond history | No |
| `GET /gov-bond/` | `countries=US,DE,JP` | Paginated gov bond history by country | No |
| `GET /gov-bond/latest/` | `tickers=US10Y,UK10Y,DE10Y` | Latest gov bond OHLCV | Yes |
| `GET /gov-bond/latest/` | `countries=US,DE,JP` | Latest gov bond OHLCV by country | Yes |
| `GET /gov-bond/latest/` | *(omit tickers)* | Latest for all 117 gov bonds | Yes |
| `GET /gov-bond/latest/{ticker}` | — | Latest for a single gov bond | Yes |

## S&P 500 Endpoints

The S&P 500 endpoints provide OHLCV data enriched with company metadata and two features the plain OHLCV endpoints don't offer:

1. **Constituent verification** — Returns `404` if a requested ticker is not an active S&P 500 member
2. **Automatic alias resolution** — Maps mismatched tickers (e.g. `FISV` → `FI` in OHLCV data) via the `ticker_aliases` table

### Example: Latest S&P 500 Data for Specific Companies

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/latest/?tickers=AAPL,MSFT,GOOGL&api_key=YOUR_KEY"
```

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

### Example: Batch Historical Data for S&P 500 Companies

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/history/?tickers=AAPL,MSFT,GOOGL&start_date=2026-04-01&end_date=2026-04-07&api_key=YOUR_KEY"
```

Returns paginated historical records enriched with name, sector, industry, and weight — one request for multiple companies across a date range.

### Example: Invalid Ticker Rejection

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/history/?tickers=AAPL,FAKE&api_key=YOUR_KEY"
```

```json
{
  "detail": "Ticker(s) not active S&P 500 constituents: FAKE"
}
```

### Example: Ticker Aliases

The API automatically resolves ticker mismatches between S&P 500 symbols and OHLCV data. Current aliases:

| S&P 500 Ticker | OHLCV Ticker |
|----------------|---------------|
| FISV | FI |
| MRSH | MMC |

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/aliases/?api_key=YOUR_KEY"
```

```json
{
  "data": [
    { "sp500_ticker": "FISV", "ohlcv_ticker": "FI" },
    { "sp500_ticker": "MRSH", "ohlcv_ticker": "MMC" }
  ],
  "total": 2
}
```

## SQL Query Endpoint

Execute read-only SQL SELECT queries directly against the database. Four guardrails protect data integrity:

1. **Read-only** — Only `SELECT` / `WITH` (CTE) statements permitted
2. **Timeout** — Queries cancelled after 30s (configurable via `SQL_TIMEOUT_S`)
3. **Row limit** — Max 5,000 rows returned (configurable via `SQL_MAX_ROWS`)
4. **Allowed tables** — Only `ohlcv_data`, `assets`, `sp500_constituents`, `ticker_aliases`, `tickers`, `ohlcv_data_etf_index`, `etf_index_assets`, `ohlcv_data_gov_bonds`, `gov_bond_assets`

```bash
curl -X POST "https://ohlcv-api-832081557693.europe-west2.run.app/sql/?api_key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT ticker, date, close, volume FROM ohlcv_data WHERE ticker = '\''AAPL'\'' ORDER BY date DESC LIMIT 5"}'
```

```json
{
  "columns": ["ticker", "date", "close", "volume"],
  "rows": [
    {"ticker": "AAPL", "date": "2026-05-07", "close": "287.4400", "volume": 40410371},
    {"ticker": "AAPL", "date": "2026-05-06", "close": "287.5100", "volume": 58336100}
  ],
  "row_count": 2,
  "truncated": false
}
```

See [DEVELOPER.md](./DEVELOPER.md) for full documentation including CTE examples, error responses, and configuration options.

## All Endpoints

### OHLCV Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ohlcv/` | List OHLCV data with filters (supports batch `tickers`) |
| GET | `/ohlcv/latest/` | Batch get latest records (specific tickers or all) |
| GET | `/ohlcv/latest/{ticker}` | Get latest record for a single ticker |
| GET | `/ohlcv/stats/{ticker}` | Get statistics for a ticker (52-week high/low) |
| GET | `/tickers/` | List all ~12,500 tickers |
| GET | `/ohlcv/{id}` | Get record by UUID |
| POST | `/ohlcv/` | Create new record |
| POST | `/ohlcv/bulk/` | Bulk create records |
| PUT | `/ohlcv/{id}` | Update record |
| DELETE | `/ohlcv/{id}` | Delete record |

### S&P 500

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sp500/` | List S&P 500 constituents (paginated, filterable by sector) |
| GET | `/sp500/latest/` | Latest OHLCV for S&P 500 constituents (supports batch `tickers`) |
| GET | `/sp500/history/` | Historical OHLCV for multiple S&P 500 constituents (batch) |

### ETF Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/etf/` | List ETF OHLCV data with filters (supports batch `tickers`) |
| GET | `/etf/latest/` | Batch get latest ETF records (specific tickers or all) |
| GET | `/etf/latest/{ticker}` | Get latest record for a single ETF |

### Index Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/index/` | List index OHLCV data with filters (supports batch `tickers`) |
| GET | `/index/latest/` | Batch get latest index records (specific tickers or all) |
| GET | `/index/latest/{ticker}` | Get latest record for a single index |

### Government Bond Data

Dedicated endpoints for government bonds (US10Y, UK10Y, DE10Y…) with enriched metadata (name, exchange, type, currency, country). Supports country filtering via `country` (single) and `countries` (comma-separated) parameters.

```bash
# Latest OHLCV for specific government bonds — enriched with name, exchange, type, currency, country
curl "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest/?tickers=US10Y,UK10Y,DE10Y&api_key=YOUR_KEY"

# Latest OHLCV for all government bonds from specific countries
curl "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest/?countries=US,DE,JP&api_key=YOUR_KEY"

# Historical OHLCV for government bonds with date range
curl "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/?tickers=US10Y,UK10Y&start_date=2025-01-01&end_date=2025-12-31&api_key=YOUR_KEY"

# Historical OHLCV for all bonds from a specific country
curl "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/?countries=US&start_date=2025-01-01&api_key=YOUR_KEY"
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/gov-bond/` | List gov bond OHLCV data with filters (supports batch `tickers`, `country`/`countries`) |
| GET | `/gov-bond/latest/` | Batch get latest gov bond records (specific tickers, countries, or all) |
| GET | `/gov-bond/latest/{ticker}` | Get latest record for a single government bond |

### Ticker Aliases

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/aliases/` | List ticker aliases |
| GET | `/aliases/{sp500_ticker}` | Get ticker alias |
| POST | `/aliases/` | Create ticker alias |
| PUT | `/aliases/{sp500_ticker}` | Update ticker alias |
| DELETE | `/aliases/{sp500_ticker}` | Delete ticker alias |

### SQL Query

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sql/` | Execute read-only SQL SELECT query (with guardrails) |

## Deploy to GCP Cloud Run

### Prerequisites
1. GCP CLI installed and authenticated: `gcloud auth login`
2. Docker installed
3. VPC Connector configured (already exists: `bls-connector`)
4. Secrets configured in GCP Secret Manager (see below)

### Deploy
```bash
./deploy.sh
```

### Secrets (GCP Secret Manager)

The application reads configuration from GCP Secret Manager. The following secrets must exist:

| Secret Name | Description |
|-------------|-------------|
| `db-host` | Database host IP address |
| `db-port` | Database port (e.g., `5432`) |
| `db-user` | Database username |
| `db-name` | Database name |
| `db-password` | Database password |
| `api-key` | API key for authentication |

### Environment Variables (Local Development)

| Variable | Description | Default |
|----------|-------------|---------|
| DB_HOST | Database host | Required |
| DB_PORT | Database port | 5432 |
| DB_USER | Database user | postgres |
| DB_PASSWORD | Database password | Required |
| DB_NAME | Database name | asset_identification_scheme |
| DB_POOL_SIZE | Connection pool size | 10 |
| DB_MAX_OVERFLOW | Max overflow connections | 5 |
| DB_ECHO | SQL echo mode | false |
