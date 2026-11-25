# OHLCV Data API

REST API for OHLCV (Open, High, Low, Close, Volume) financial data. Every
non-commodity instrument — equities, ETFs, funds, indices, FX, crypto and
government bonds — is served from one partitioned `ohlcv_unified` table and
addressed as `TICKER.EXCHANGE` (e.g. `AAPL.US`, `BP.LSE`, `BTC-USD.CC`).
Commodities and US Treasury rates have their own endpoints.

## Highlights

- **One addressing scheme** — `TICKER.EXCHANGE` for every asset class in the unified table; the suffix is required and a bare ticker returns `400`
- **Batch queries** — request many instruments in a single call: `tickers=AAPL.US,MSFT.US,BP.LSE`
- **Real-time quotes** — live prices from EODHD via `/ohlcv/latest/` and `/commodity/latest/`, batched upstream in one request
- **Commodities** — stored history, live quotes and a symbol/category reference, addressed without a suffix (`LGOc3`, `GDK`)
- **US Treasury rates** — bill, long-term, real-yield and yield series behind one `/ust/` endpoint
- **Historical depth** — daily bars from 1962 to today, partitioned by year
- **SQL query endpoint** — read-only `SELECT`/`WITH` with guardrails (timeout, row cap, table whitelist)
- **GZip compression** — automatic response compression for payloads over 1KB

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

- **Production API reference**: [docs/PROD_API_DOCUMENTATION.md](docs/PROD_API_DOCUMENTATION.md)
- **UAT API reference**: [docs/UAT_API_DOCUMENTATION.md](docs/UAT_API_DOCUMENTATION.md)
- **Swagger UI** (local): http://localhost:8001/docs
- **ReDoc** (local): http://localhost:8001/redoc

The two API references describe the same surface and differ only in base URL.
Superseded documentation lives in `docs/archive/`.

## Project Structure

```
├── main.py                        # FastAPI application and endpoints
├── models.py                      # SQLAlchemy database models
├── schemas.py                     # Pydantic request/response schemas
├── database.py                    # Database connection configuration
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container image
├── deploy.sh                      # Deploy to production Cloud Run
├── deploy-uat.sh                  # Deploy to the UAT Cloud Run service
├── cloudbuild.yaml                # Cloud Build configuration
├── docs/
│   ├── PROD_API_DOCUMENTATION.md  # Production API reference
│   ├── UAT_API_DOCUMENTATION.md   # UAT API reference
│   └── archive/                   # Superseded documentation
├── migrations/                    # SQL migrations
└── tests/                         # Test suite
```

## SQL Query Endpoint

Execute read-only SQL SELECT queries directly against the database. Four guardrails protect data integrity:

1. **Read-only** — Only `SELECT` / `WITH` (CTE) statements permitted
2. **Timeout** — Queries cancelled after 30s (configurable via `SQL_TIMEOUT_S`)
3. **Row limit** — Max 5,000 rows returned (configurable via `SQL_MAX_ROWS`)
4. **Allowed tables** — `ohlcv_unified`, `assets`, `tickers`, `ticker_aliases`, `commodities_eod`, the per-class tables (`ohlcv_data`, `ohlcv_data_etf_index`, `ohlcv_data_gov_bonds`, `ohlcv_data_fx`, `ohlcv_data_uk`, `ohlcv_data_crypto` and their metadata tables), `sp500_constituents`, `ftse100_constituents`, and the four `ust_*` rate tables

```bash
curl -X POST "https://ohlcv-api-832081557693.europe-west2.run.app/sql/?api_key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT ticker, date, close, volume FROM ohlcv_unified WHERE ticker = '\''AAPL'\'' AND exchange = '\''US'\'' ORDER BY date DESC LIMIT 5"}'
```

```json
{
  "columns": ["ticker", "date", "close", "volume"],
  "rows": [
    {"ticker": "AAPL", "date": "2026-11-23", "close": 349.08, "volume": 56934608},
    {"ticker": "AAPL", "date": "2026-11-20", "close": 342.56, "volume": 79734485}
  ],
  "row_count": 2,
  "truncated": false
}
```

`/sql/` returns driver-native numerics (e.g. `349.08`), unlike the REST endpoints, which serialize prices as strings. See [docs/PROD_API_DOCUMENTATION.md](docs/PROD_API_DOCUMENTATION.md) for the full guardrail rules.

## All Endpoints

Eight paths, nine operations. Anything not listed here is retired — set
`ENABLE_RETIRED_ROUTES=1` to re-register the legacy routes for comparison only.

### OHLCV

Every non-commodity asset class shares one table and one addressing scheme,
`TICKER.EXCHANGE`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ohlcv/` | Paginated history; filters `ticker`/`tickers`, `exchange`, `asset_type`, dates, price and volume ranges |
| POST | `/ohlcv/` | Insert one row (`201`) |
| POST | `/ohlcv/bulk/` | Bulk insert |
| GET | `/ohlcv/latest/` | Real-time quotes from EODHD for `tickers`; unknown tickers are listed in `missing` |

### Commodities

Commodities live in their own table and are addressed without a suffix
(`LGOc3`, `NICKEL`, `GDK`).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/commodity/` | Paginated history; `latest=true` returns the newest stored bar per symbol |
| GET | `/commodity/latest/` | Real-time quotes from EODHD, resolved as `SYMBOL.COMM` |
| GET | `/commodity/symbols/` | Symbols with name and category |

### US Treasury Rates

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ust/` | All four series in one envelope: `series` (`bill`, `long_term`, `real_yield`, `yield`), `tenor`/`tenors`, `rate_type`/`rate_types`, dates, `latest` |

### SQL

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sql/` | Execute a read-only `SELECT`/`WITH` query (guardrailed) |

Full request and response documentation:
[docs/PROD_API_DOCUMENTATION.md](docs/PROD_API_DOCUMENTATION.md) for production,
[docs/UAT_API_DOCUMENTATION.md](docs/UAT_API_DOCUMENTATION.md) for UAT.

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

UAT uses the same per-instance sizing as production so results are comparable:
`max-instances 20`, `concurrency 100`, `2Gi` memory / `4` CPU, and the same DB
pool (`DB_POOL_SIZE=3`, `DB_MAX_OVERFLOW=2`). It uses the same region, VPC
connector, and secrets, so it reaches the same database. Both services run the
same image; promotion is `./deploy.sh` with the validated image.

Unlike production, UAT runs `--min-instances 0`, so it scales to zero when idle
and costs nothing between uses. The trade-off is a cold start on the first
request after an idle period.

UAT mounts `api-keys-uat` instead of `api-keys`, so the UAT key is isolated in its
own secret and can be rotated without touching production keys. `API_KEY` is still
shared with production, so a production key also authenticates on UAT.

`/ust/` serves US Treasury rates on both services. The eight per-series routes
(`/ust/bill/`, `/ust/yield/`, …) are retired; set `ENABLE_RETIRED_ROUTES=1` to
re-register them alongside `/ust/`.

`ENABLE_RETIRED_ROUTES=1` re-registers the retired legacy routes (`/uk/`, `/etf/`,
`/index/`, `/fx/`, `/crypto/`, `/gov-bond/`, `/sp500/`, `/ftse100/`, `/aliases/`,
`/assets/{ticker}`, `/tickers/`, `/ohlcv/latest_close/*`, `/ohlcv/stats/*`). It is
off by default and exists only to compare old and new surfaces side by side.

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
