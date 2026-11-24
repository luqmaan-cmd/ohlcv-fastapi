# OHLCV Data API

High-performance REST API for OHLCV (Open, High, Low, Close, Volume) financial data with **batch queries**, **S&P 500 enriched endpoints**, **ETF & Index data**, **Government Bond data**, **US Treasury Rate data**, **Crypto data**, **FTSE 100 data**, and **Commodity data**. Query latest prices or full history for multiple companies, ETFs, indices, government bonds, or US Treasury rates in a single request, with automatic ticker alias resolution and constituent verification.

## Highlights

- **Batch queries** — Request data for multiple companies in one API call using `tickers=AAPL,MSFT,GOOGL`
- **S&P 500 enriched data** — OHLCV records enriched with company name, sector, industry, and index weight
- **ETF & Index data** — Dedicated endpoints for ETFs (SPY, QQQ, IWM…) and indices (GSPC, DJI, IXIC…) with enriched metadata (name, exchange, ISIN, currency)
- **Government Bond data** — Dedicated endpoints for government bonds (US10Y, UK10Y, DE10Y…) with enriched metadata (name, exchange, type, currency, country) and country filtering
- **US Treasury Rate data** — Dedicated endpoints for US Treasury bill rates, yield curve rates, real yield rates, and long-term rates with tenor/rate-type filtering and batch queries
- **Crypto data** — Dedicated endpoints for cryptocurrency assets (BTC-USD, ETH-USD…) with enriched metadata, top-100 by volume, and real-time EODHD data
- **FTSE 100 data** — Dedicated endpoints for FTSE 100 constituents with enriched metadata (name, sector, industry, isin, currency)
- **Commodity data** — Dedicated endpoints for commodity OHLCV data (LGOc3, NICKEL, GDK…) with enriched metadata (name, category) and category filtering
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
4. **Allowed tables** — Only `ohlcv_data`, `assets`, `sp500_constituents`, `ticker_aliases`, `tickers`, `ohlcv_data_etf_index`, `etf_index_assets`, `ohlcv_data_gov_bonds`, `gov_bond_assets`, `ust_bill_rates`, `ust_long_term_rates`, `ust_real_yield_rates`, `ust_yield_rates`

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
| GET | `/ohlcv/latest_close/` | Batch get latest close from DB (specific tickers or all) |
| GET | `/ohlcv/latest_close/{ticker}` | Get latest close from DB for a single ticker |
| GET | `/ohlcv/latest/` | Batch get real-time OHLCV from EODHD (requires `tickers`) |
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
| GET | `/etf/latest_close/` | Batch get latest ETF close from DB (specific tickers or all) |
| GET | `/etf/latest_close/{ticker}` | Get latest ETF close from DB for a single ETF |
| GET | `/etf/latest/` | Batch get real-time ETF OHLCV from EODHD (requires `tickers`) |

### Index Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/index/` | List index OHLCV data with filters (supports batch `tickers`) |
| GET | `/index/latest_close/` | Batch get latest index close from DB (specific tickers or all) |
| GET | `/index/latest_close/{ticker}` | Get latest index close from DB for a single index |
| GET | `/index/latest/` | Batch get real-time index OHLCV from EODHD (requires `tickers`) |

### Government Bond Data

Dedicated endpoints for government bonds (US10Y, UK10Y, DE10Y…) with enriched metadata (name, exchange, type, currency, country). Supports country filtering via `country` (single) and `countries` (comma-separated) parameters.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/gov-bond/` | List gov bond OHLCV data with filters (supports batch `tickers`, `country`/`countries`) |
| GET | `/gov-bond/latest_close/` | Batch get latest gov bond close from DB (specific tickers, countries, or all) |
| GET | `/gov-bond/latest_close/{ticker}` | Get latest gov bond close from DB for a single government bond |
| GET | `/gov-bond/latest/` | Batch get real-time gov bond OHLCV from EODHD (requires `tickers`) |

### Foreign Exchange (FX) Data

Dedicated endpoints for foreign exchange pairs (EURUSD, GBPUSD, USDJPY…) with enriched metadata (name, exchange, type, currency, base_currency, quote_currency).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/fx/` | List FX OHLCV data with filters (supports batch `tickers`, `base_currency`, `quote_currency`) |
| GET | `/fx/latest_close/` | Batch get latest FX close from DB (specific tickers or all) |
| GET | `/fx/latest_close/{ticker}` | Get latest FX close from DB for a single pair |
| GET | `/fx/latest/` | Batch get real-time FX OHLCV from EODHD (requires `tickers`) |

### UK Stock (LSE) Data

Dedicated endpoints for UK stocks listed on the London Stock Exchange (LSE) with enriched metadata (name, exchange, type, sector, industry, isin, currency).

> **Note:** UK tickers are **case-sensitive** (e.g., `AZN`, not `azn`).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/uk/` | List UK stock OHLCV data with filters (supports batch `tickers`, `sector`, `industry`) |
| GET | `/uk/latest_close/` | Batch get latest UK stock close from DB (specific tickers or all) |
| GET | `/uk/latest_close/{ticker}` | Get latest UK stock close from DB for a single stock |
| GET | `/uk/latest/` | Batch get real-time UK stock OHLCV from EODHD (requires `tickers`) |

### Crypto Data

Dedicated endpoints for cryptocurrency assets (BTC-USD, ETH-USD, SOL-USD…) with enriched metadata (name, exchange, type, currency, base_currency, quote_currency).

> **Note:** Crypto tickers are **case-sensitive** (e.g., `BTC-USD`, not `btc-usd`).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/crypto/` | List crypto OHLCV data with filters (supports batch `tickers`, `base_currency`, `quote_currency`) |
| GET | `/crypto/latest_close/` | Batch get latest crypto close from DB (specific tickers or all) |
| GET | `/crypto/latest_close/{ticker}` | Get latest crypto close from DB for a single asset |
| GET | `/crypto/latest/` | Batch get real-time crypto OHLCV from EODHD (requires `tickers`) |
| GET | `/crypto/history/` | Paginated crypto history with metadata (supports batch `tickers`) |
| GET | `/crypto/top100/` | Top 100 crypto by volume with notional_value |
| GET | `/crypto/assets/` | List all crypto asset metadata (no OHLCV) |

### FTSE 100 Data

Dedicated endpoints for FTSE 100 constituents with enriched metadata (name, sector, industry from `ftse100_constituents`; isin, currency from `uk_assets`). Supports filtering by `sector` and `industry` parameters.

> **Note:** FTSE 100 tickers are **case-sensitive** (e.g., `AZN`, not `azn`).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ftse100/` | List FTSE 100 OHLCV data with filters (supports batch `tickers`, `sector`, `industry`) |
| GET | `/ftse100/latest/` | Batch get latest FTSE 100 OHLCV (specific tickers, sector, industry, or all) |

### US Treasury Rate Data

Dedicated endpoints for US Treasury rates across four categories: bill rates, yield curve rates, real yield rates, and long-term rates. Each category supports tenor or rate-type filtering and batch queries.

> **Note:** Long-term rate types (`BC_20year`, `Over_10_Years`, `Real_Rate`) are **case-sensitive**. All other UST tenors are case-insensitive (automatically uppercased).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ust/bill/` | List US Treasury bill rates with filters (supports `tenor`/`tenors`) |
| GET | `/ust/bill/latest/` | Batch get latest bill rates (specific tenors or all) |
| GET | `/ust/long-term/` | List US Treasury long-term rates with filters (supports `rate_type`/`rate_types`) |
| GET | `/ust/long-term/latest/` | Batch get latest long-term rates (specific rate types or all) |
| GET | `/ust/real-yield/` | List US Treasury real yield rates with filters (supports `tenor`/`tenors`) |
| GET | `/ust/real-yield/latest/` | Batch get latest real yield rates (specific tenors or all) |
| GET | `/ust/yield/` | List US Treasury yield curve rates with filters (supports `tenor`/`tenors`) |
| GET | `/ust/yield/latest/` | Batch get latest yield rates (specific tenors or all) |

#### Distinct Values

| Category | Filter | Values |
|----------|--------|--------|
| Bill | `tenor` | `4WK`, `6WK`, `8WK`, `13WK`, `17WK`, `26WK`, `52WK` |
| Long-Term | `rate_type` | `BC_20year`, `Over_10_Years`, `Real_Rate` *(case-sensitive)* |
| Real-Yield | `tenor` | `5Y`, `7Y`, `10Y`, `20Y`, `30Y` |
| Yield | `tenor` | `1M`, `1.5M`, `2M`, `3M`, `4M`, `6M`, `1Y`, `2Y`, `3Y`, `5Y`, `7Y`, `10Y`, `20Y`, `30Y` |

### Commodity Data

Dedicated endpoints for commodity OHLCV data (LGOc3, NICKEL, GDK…) with enriched metadata (name, category). Supports filtering by `category`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/commodity/` | List commodity OHLCV data with filters (supports batch `symbols`, `category`) |
| GET | `/commodity/latest/` | Batch get latest commodity OHLCV (specific symbols, category, or all) |
| GET | `/commodity/symbols/` | List commodity symbols (filterable by `category`) |
| GET | `/commodity/categories/` | List all distinct commodity categories |

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

### Deploy UAT

`ohlcv-api-uat` is a separate Cloud Run service for validating new endpoints
against the same database before promoting to production.

```bash
./deploy-uat.sh
```

UAT mirrors production sizing so results are comparable: `min-instances 1`,
`max-instances 20`, `concurrency 100`, `2Gi` memory / `4` CPU, and the same DB
pool (`DB_POOL_SIZE=3`, `DB_MAX_OVERFLOW=2`). It uses the same region, VPC
connector, and secrets, so it reaches the same database. Both services run the
same image; promotion is `./deploy.sh` with the validated image. After
validation, set `--min-instances 0` or delete the service to stop paying for a
warm instance.

UAT mounts `api-keys-uat` instead of `api-keys`, so the UAT key is isolated in its
own secret and can be rotated without touching production keys. `API_KEY` is still
shared with production, so a production key also authenticates on UAT.

### Secrets (GCP Secret Manager)

The application reads configuration from GCP Secret Manager. The following secrets must exist:

| Secret Name | Description |
|-------------|-------------|
| `db-host` | Database host IP address |
| `db-port` | Database port (e.g., `5432`) |
| `db-user` | Database username |
| `db-name` | Database name |
| `db-password` | Database password |
| `api-key` | Primary API key for authentication |
| `api-keys` | Additional API keys, comma-separated `key[:label]` (optional) |
| `api-keys-uat` | API keys mounted only by `ohlcv-api-uat` (the `uat`-labelled key) |
| `eodhd-api-token` | EODHD API token for real-time OHLCV endpoints |

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
| API_KEY | Primary API key | Required |
| API_KEYS | Additional API keys, comma-separated `key[:label]` | (none) |
| EODHD_API_TOKEN | EODHD API token for real-time OHLCV endpoints | Required |
