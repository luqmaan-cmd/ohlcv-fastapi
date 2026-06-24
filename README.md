# OHLCV Data API

High-performance REST API for OHLCV (Open, High, Low, Close, Volume) financial data with **batch queries**, **S&P 500 enriched endpoints**, **ETF & Index data**, **Government Bond data**, and **US Treasury Rate data**. Query latest prices or full history for multiple companies, ETFs, indices, government bonds, or US Treasury rates in a single request, with automatic ticker alias resolution and constituent verification.

## Highlights

- **Batch queries** — Request data for multiple companies in one API call using `tickers=AAPL,MSFT,GOOGL`
- **S&P 500 enriched data** — OHLCV records enriched with company name, sector, industry, and index weight
- **ETF & Index data** — Dedicated endpoints for ETFs (SPY, QQQ, IWM…) and indices (GSPC, DJI, IXIC…) with enriched metadata (name, exchange, ISIN, currency)
- **Government Bond data** — Dedicated endpoints for government bonds (US10Y, UK10Y, DE10Y…) with enriched metadata (name, exchange, type, currency, country) and country filtering
- **US Treasury Rate data** — Dedicated endpoints for US Treasury bill rates, yield curve rates, real yield rates, and long-term rates with tenor/rate-type filtering and batch queries
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
# Latest close from DB for 3 companies — one request
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/latest_close/?tickers=AAPL,MSFT,GOOGL&api_key=YOUR_KEY"

# Real-time OHLCV from EODHD for 3 companies — one request
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/latest/?tickers=AAPL,MSFT,GOOGL&api_key=YOUR_KEY"

# Latest S&P 500 data for specific companies — enriched with name, sector, weight
curl "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/latest/?tickers=AAPL,MSFT,GOOGL&api_key=YOUR_KEY"

# Historical OHLCV for multiple S&P 500 companies with date range
curl "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/history/?tickers=AAPL,MSFT,GOOGL&start_date=2025-01-01&end_date=2025-12-31&api_key=YOUR_KEY"

# Historical OHLCV for multiple tickers (non-S&P 500)
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/?tickers=AAPL,MSFT,GOOGL&start_date=2025-01-01&end_date=2025-12-31&api_key=YOUR_KEY"

# Latest close from DB for specific ETFs — enriched with name, exchange, ISIN, currency
curl "https://ohlcv-api-832081557693.europe-west2.run.app/etf/latest_close/?tickers=SPY,QQQ,IWM&api_key=YOUR_KEY"

# Real-time ETF OHLCV from EODHD
curl "https://ohlcv-api-832081557693.europe-west2.run.app/etf/latest/?tickers=SPY,QQQ,IWM&api_key=YOUR_KEY"

# Latest close from DB for specific indices
curl "https://ohlcv-api-832081557693.europe-west2.run.app/index/latest_close/?tickers=GSPC,DJI,IXIC&api_key=YOUR_KEY"

# Real-time index OHLCV from EODHD
curl "https://ohlcv-api-832081557693.europe-west2.run.app/index/latest/?tickers=GSPC,DJI,IXIC&api_key=YOUR_KEY"

# Historical OHLCV for ETFs with date range
curl "https://ohlcv-api-832081557693.europe-west2.run.app/etf/?tickers=SPY,QQQ&start_date=2025-01-01&end_date=2025-12-31&api_key=YOUR_KEY"

# Latest close from DB for specific government bonds — enriched with name, exchange, type, currency, country
curl "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest_close/?tickers=US10Y,UK10Y,DE10Y&api_key=YOUR_KEY"

# Real-time government bond OHLCV from EODHD
curl "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest/?tickers=US10Y,UK10Y,DE10Y&api_key=YOUR_KEY"

# Latest close from DB for all government bonds from specific countries
curl "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest_close/?countries=US,DE,JP&api_key=YOUR_KEY"

# Historical OHLCV for government bonds with date range
curl "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/?tickers=US10Y,UK10Y&start_date=2025-01-01&end_date=2025-12-31&api_key=YOUR_KEY"

# Latest US Treasury bill rates for all tenors
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ust/bill/latest/?api_key=YOUR_KEY"

# Latest US Treasury yield rates for specific tenors
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ust/yield/latest/?tenors=2Y,5Y,10Y,30Y&api_key=YOUR_KEY"

# Latest US Treasury real yield rate for a single tenor
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ust/real-yield/latest/10Y?api_key=YOUR_KEY"

# Latest US Treasury long-term rates for all rate types
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ust/long-term/latest/?api_key=YOUR_KEY"

# Historical US Treasury yield rates with date range and rate filter
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ust/yield/?tenor=10Y&start_date=2025-01-01&end_date=2025-12-31&api_key=YOUR_KEY"
```

### Batch Endpoints Summary

| Endpoint | Batch Parameter | Returns | Enriched |
|----------|----------------|---------|----------|
| `GET /ohlcv/latest_close/` | `tickers=AAPL,MSFT,GOOGL` | Latest close per ticker (DB) | No |
| `GET /ohlcv/latest_close/` | *(omit tickers)* | Latest close for all ~12,500 tickers (DB) | No |
| `GET /ohlcv/latest/` | `tickers=AAPL,MSFT,GOOGL` | Real-time OHLCV from EODHD | No |
| `GET /ohlcv/latest/{ticker}` | — | Real-time OHLCV from EODHD for a single ticker | No |
| `GET /ohlcv/` | `tickers=AAPL,MSFT,GOOGL` | Paginated history per ticker | No |
| `GET /sp500/latest/` | `tickers=AAPL,MSFT,GOOGL` | Latest S&P 500 OHLCV | Yes |
| `GET /sp500/latest/` | *(omit tickers)* | Latest for all 503 constituents | Yes |
| `GET /sp500/history/` | `tickers=AAPL,MSFT,GOOGL` | Paginated S&P 500 history | Yes |
| `GET /sp500/history/` | *(omit tickers)* | Paginated history for all active constituents | Yes |
| `GET /etf/` | `tickers=SPY,QQQ,IWM` | Paginated ETF history | No |
| `GET /etf/latest_close/` | `tickers=SPY,QQQ,IWM` | Latest ETF close (DB) | Yes |
| `GET /etf/latest_close/` | *(omit tickers)* | Latest close for all ETFs (DB) | Yes |
| `GET /etf/latest_close/{ticker}` | — | Latest close for a single ETF (DB) | Yes |
| `GET /etf/latest/` | `tickers=SPY,QQQ,IWM` | Real-time ETF OHLCV from EODHD | No |
| `GET /etf/latest/{ticker}` | — | Real-time ETF OHLCV from EODHD for a single ETF | No |
| `GET /index/` | `tickers=GSPC,DJI,IXIC` | Paginated index history | No |
| `GET /index/latest_close/` | `tickers=GSPC,DJI,IXIC` | Latest index close (DB) | Yes |
| `GET /index/latest_close/` | *(omit tickers)* | Latest close for all indices (DB) | Yes |
| `GET /index/latest_close/{ticker}` | — | Latest close for a single index (DB) | Yes |
| `GET /index/latest/` | `tickers=GSPC,DJI,IXIC` | Real-time index OHLCV from EODHD | No |
| `GET /index/latest/{ticker}` | — | Real-time index OHLCV from EODHD for a single index | No |
| `GET /gov-bond/` | `tickers=US10Y,UK10Y,DE10Y` | Paginated gov bond history | No |
| `GET /gov-bond/` | `countries=US,DE,JP` | Paginated gov bond history by country | No |
| `GET /gov-bond/latest_close/` | `tickers=US10Y,UK10Y,DE10Y` | Latest gov bond close (DB) | Yes |
| `GET /gov-bond/latest_close/` | `countries=US,DE,JP` | Latest gov bond close by country (DB) | Yes |
| `GET /gov-bond/latest_close/` | *(omit tickers)* | Latest close for all 117 gov bonds (DB) | Yes |
| `GET /gov-bond/latest_close/{ticker}` | — | Latest close for a single gov bond (DB) | Yes |
| `GET /gov-bond/latest/` | `tickers=US10Y,UK10Y,DE10Y` | Real-time gov bond OHLCV from EODHD | No |
| `GET /gov-bond/latest/{ticker}` | — | Real-time gov bond OHLCV from EODHD for a single bond | No |
| `GET /fx/` | `tickers=EURUSD,GBPUSD,USDJPY` | Paginated FX history | No |
| `GET /fx/latest_close/` | `tickers=EURUSD,GBPUSD,USDJPY` | Latest FX close (DB) | Yes |
| `GET /fx/latest_close/` | *(omit tickers)* | Latest close for all FX pairs (DB) | Yes |
| `GET /fx/latest_close/{ticker}` | — | Latest close for a single FX pair (DB) | Yes |
| `GET /fx/latest/` | `tickers=EURUSD,GBPUSD,USDJPY` | Real-time FX OHLCV from EODHD | No |
| `GET /fx/latest/{ticker}` | — | Real-time FX OHLCV from EODHD for a single pair | No |
| `GET /uk/` | `tickers=AZN,SHEL,HSBA` | Paginated UK stock history | No |
| `GET /uk/latest_close/` | `tickers=AZN,SHEL,HSBA` | Latest UK stock close (DB) | Yes |
| `GET /uk/latest_close/` | *(omit tickers)* | Latest close for all UK stocks (DB) | Yes |
| `GET /uk/latest_close/{ticker}` | — | Latest close for a single UK stock (DB) | Yes |
| `GET /uk/latest/` | `tickers=AZN,SHEL,HSBA` | Real-time UK stock OHLCV from EODHD | No |
| `GET /uk/latest/{ticker}` | — | Real-time UK stock OHLCV from EODHD for a single stock | No |
| `GET /crypto/` | `tickers=BTC-USD,ETH-USD,SOL-USD` | Paginated crypto history | No |
| `GET /crypto/latest_close/` | `tickers=BTC-USD,ETH-USD,SOL-USD` | Latest crypto close (DB) | Yes |
| `GET /crypto/latest_close/` | *(omit tickers)* | Latest close for all crypto assets (DB) | Yes |
| `GET /crypto/latest_close/{ticker}` | — | Latest close for a single crypto asset (DB) | Yes |
| `GET /crypto/latest/` | `tickers=BTC-USD,ETH-USD,SOL-USD` | Real-time crypto OHLCV from EODHD | No |
| `GET /crypto/latest/{ticker}` | — | Real-time crypto OHLCV from EODHD for a single asset | No |
| `GET /ust/bill/` | `tenor=13WK` or `tenors=4WK,13WK,26WK` | Paginated bill rate history | No |
| `GET /ust/bill/latest/` | `tenors=4WK,13WK,26WK` | Latest bill rates per tenor | No |
| `GET /ust/bill/latest/` | *(omit tenors)* | Latest for all 7 bill tenors | No |
| `GET /ust/bill/latest/{tenor}` | — | Latest for a single bill tenor | No |
| `GET /ust/long-term/` | `rate_type=BC_20year` or `rate_types=BC_20year,Over_10_Years` | Paginated long-term rate history | No |
| `GET /ust/long-term/latest/` | `rate_types=BC_20year,Over_10_Years` | Latest long-term rates per type | No |
| `GET /ust/long-term/latest/` | *(omit rate_types)* | Latest for all 3 long-term rate types | No |
| `GET /ust/long-term/latest/{rate_type}` | — | Latest for a single long-term rate type | No |
| `GET /ust/real-yield/` | `tenor=10Y` or `tenors=5Y,10Y,30Y` | Paginated real yield history | No |
| `GET /ust/real-yield/latest/` | `tenors=5Y,10Y,30Y` | Latest real yield rates per tenor | No |
| `GET /ust/real-yield/latest/` | *(omit tenors)* | Latest for all 5 real yield tenors | No |
| `GET /ust/real-yield/latest/{tenor}` | — | Latest for a single real yield tenor | No |
| `GET /ust/yield/` | `tenor=10Y` or `tenors=2Y,5Y,10Y,30Y` | Paginated yield rate history | No |
| `GET /ust/yield/latest/` | `tenors=2Y,5Y,10Y,30Y` | Latest yield rates per tenor | No |
| `GET /ust/yield/latest/` | *(omit tenors)* | Latest for all 14 yield tenors | No |
| `GET /ust/yield/latest/{tenor}` | — | Latest for a single yield tenor | No |

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
| GET | `/ohlcv/latest/{ticker}` | Get real-time OHLCV from EODHD for a single ticker |
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
| GET | `/etf/latest/{ticker}` | Get real-time ETF OHLCV from EODHD for a single ETF |

### Index Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/index/` | List index OHLCV data with filters (supports batch `tickers`) |
| GET | `/index/latest_close/` | Batch get latest index close from DB (specific tickers or all) |
| GET | `/index/latest_close/{ticker}` | Get latest index close from DB for a single index |
| GET | `/index/latest/` | Batch get real-time index OHLCV from EODHD (requires `tickers`) |
| GET | `/index/latest/{ticker}` | Get real-time index OHLCV from EODHD for a single index |

### Government Bond Data

Dedicated endpoints for government bonds (US10Y, UK10Y, DE10Y…) with enriched metadata (name, exchange, type, currency, country). Supports country filtering via `country` (single) and `countries` (comma-separated) parameters.

```bash
# Latest close from DB for specific government bonds — enriched with name, exchange, type, currency, country
curl "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest_close/?tickers=US10Y,UK10Y,DE10Y&api_key=YOUR_KEY"

# Real-time government bond OHLCV from EODHD
curl "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest/?tickers=US10Y,UK10Y,DE10Y&api_key=YOUR_KEY"

# Latest close from DB for all government bonds from specific countries
curl "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest_close/?countries=US,DE,JP&api_key=YOUR_KEY"

# Historical OHLCV for government bonds with date range
curl "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/?tickers=US10Y,UK10Y&start_date=2025-01-01&end_date=2025-12-31&api_key=YOUR_KEY"

# Historical OHLCV for all bonds from a specific country
curl "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/?countries=US&start_date=2025-01-01&api_key=YOUR_KEY"
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/gov-bond/` | List gov bond OHLCV data with filters (supports batch `tickers`, `country`/`countries`) |
| GET | `/gov-bond/latest_close/` | Batch get latest gov bond close from DB (specific tickers, countries, or all) |
| GET | `/gov-bond/latest_close/{ticker}` | Get latest gov bond close from DB for a single government bond |
| GET | `/gov-bond/latest/` | Batch get real-time gov bond OHLCV from EODHD (requires `tickers`) |
| GET | `/gov-bond/latest/{ticker}` | Get real-time gov bond OHLCV from EODHD for a single bond |

### Foreign Exchange (FX) Data

Dedicated endpoints for foreign exchange pairs (EURUSD, GBPUSD, USDJPY…) with enriched metadata (name, exchange, type, currency, base_currency, quote_currency).

```bash
# Latest close from DB for specific FX pairs
curl "https://ohlcv-api-832081557693.europe-west2.run.app/fx/latest_close/?tickers=EURUSD,GBPUSD,USDJPY&api_key=YOUR_KEY"

# Real-time FX OHLCV from EODHD
curl "https://ohlcv-api-832081557693.europe-west2.run.app/fx/latest/?tickers=EURUSD,GBPUSD,USDJPY&api_key=YOUR_KEY"
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/fx/` | List FX OHLCV data with filters (supports batch `tickers`, `base_currency`, `quote_currency`) |
| GET | `/fx/latest_close/` | Batch get latest FX close from DB (specific tickers or all) |
| GET | `/fx/latest_close/{ticker}` | Get latest FX close from DB for a single pair |
| GET | `/fx/latest/` | Batch get real-time FX OHLCV from EODHD (requires `tickers`) |
| GET | `/fx/latest/{ticker}` | Get real-time FX OHLCV from EODHD for a single pair |

### UK Stock (LSE) Data

Dedicated endpoints for UK stocks listed on the London Stock Exchange (LSE) with enriched metadata (name, exchange, type, sector, industry, isin, currency).

> **Note:** UK tickers are **case-sensitive** (e.g., `AZN`, not `azn`).

```bash
# Latest close from DB for specific UK stocks
curl "https://ohlcv-api-832081557693.europe-west2.run.app/uk/latest_close/?tickers=AZN,SHEL,HSBA&api_key=YOUR_KEY"

# Real-time UK stock OHLCV from EODHD
curl "https://ohlcv-api-832081557693.europe-west2.run.app/uk/latest/?tickers=AZN,SHEL,HSBA&api_key=YOUR_KEY"
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/uk/` | List UK stock OHLCV data with filters (supports batch `tickers`, `sector`, `industry`) |
| GET | `/uk/latest_close/` | Batch get latest UK stock close from DB (specific tickers or all) |
| GET | `/uk/latest_close/{ticker}` | Get latest UK stock close from DB for a single stock |
| GET | `/uk/latest/` | Batch get real-time UK stock OHLCV from EODHD (requires `tickers`) |
| GET | `/uk/latest/{ticker}` | Get real-time UK stock OHLCV from EODHD for a single stock |

### Crypto Data

Dedicated endpoints for cryptocurrency assets (BTC-USD, ETH-USD, SOL-USD…) with enriched metadata (name, exchange, type, currency, base_currency, quote_currency).

> **Note:** Crypto tickers are **case-sensitive** (e.g., `BTC-USD`, not `btc-usd`).

```bash
# Latest close from DB for specific crypto assets
curl "https://ohlcv-api-832081557693.europe-west2.run.app/crypto/latest_close/?tickers=BTC-USD,ETH-USD,SOL-USD&api_key=YOUR_KEY"

# Real-time crypto OHLCV from EODHD
curl "https://ohlcv-api-832081557693.europe-west2.run.app/crypto/latest/?tickers=BTC-USD,ETH-USD,SOL-USD&api_key=YOUR_KEY"
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/crypto/` | List crypto OHLCV data with filters (supports batch `tickers`, `base_currency`, `quote_currency`) |
| GET | `/crypto/latest_close/` | Batch get latest crypto close from DB (specific tickers or all) |
| GET | `/crypto/latest_close/{ticker}` | Get latest crypto close from DB for a single asset |
| GET | `/crypto/latest/` | Batch get real-time crypto OHLCV from EODHD (requires `tickers`) |
| GET | `/crypto/latest/{ticker}` | Get real-time crypto OHLCV from EODHD for a single asset |

### US Treasury Rate Data

Dedicated endpoints for US Treasury rates across four categories: bill rates, yield curve rates, real yield rates, and long-term rates. Each category supports tenor or rate-type filtering and batch queries.

> **Note:** Long-term rate types (`BC_20year`, `Over_10_Years`, `Real_Rate`) are **case-sensitive**. All other UST tenors are case-insensitive (automatically uppercased).

```bash
# Latest US Treasury bill rates for all tenors
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ust/bill/latest/?api_key=YOUR_KEY"

# Latest US Treasury yield rates for specific tenors
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ust/yield/latest/?tenors=2Y,5Y,10Y,30Y&api_key=YOUR_KEY"

# Latest US Treasury real yield rate for a single tenor
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ust/real-yield/latest/10Y?api_key=YOUR_KEY"

# Latest US Treasury long-term rates for all rate types (case-sensitive!)
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ust/long-term/latest/?api_key=YOUR_KEY"

# Historical US Treasury yield rates with date range
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ust/yield/?tenor=10Y&start_date=2025-01-01&end_date=2025-12-31&api_key=YOUR_KEY"
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ust/bill/` | List US Treasury bill rates with filters (supports `tenor`/`tenors`) |
| GET | `/ust/bill/latest/` | Batch get latest bill rates (specific tenors or all) |
| GET | `/ust/bill/latest/{tenor}` | Get latest bill rate for a single tenor |
| GET | `/ust/long-term/` | List US Treasury long-term rates with filters (supports `rate_type`/`rate_types`) |
| GET | `/ust/long-term/latest/` | Batch get latest long-term rates (specific rate types or all) |
| GET | `/ust/long-term/latest/{rate_type}` | Get latest long-term rate for a single rate type |
| GET | `/ust/real-yield/` | List US Treasury real yield rates with filters (supports `tenor`/`tenors`) |
| GET | `/ust/real-yield/latest/` | Batch get latest real yield rates (specific tenors or all) |
| GET | `/ust/real-yield/latest/{tenor}` | Get latest real yield rate for a single tenor |
| GET | `/ust/yield/` | List US Treasury yield curve rates with filters (supports `tenor`/`tenors`) |
| GET | `/ust/yield/latest/` | Batch get latest yield rates (specific tenors or all) |
| GET | `/ust/yield/latest/{tenor}` | Get latest yield rate for a single tenor |

#### Distinct Values

| Category | Filter | Values |
|----------|--------|--------|
| Bill | `tenor` | `4WK`, `6WK`, `8WK`, `13WK`, `17WK`, `26WK`, `52WK` |
| Long-Term | `rate_type` | `BC_20year`, `Over_10_Years`, `Real_Rate` *(case-sensitive)* |
| Real-Yield | `tenor` | `5Y`, `7Y`, `10Y`, `20Y`, `30Y` |
| Yield | `tenor` | `1M`, `1.5M`, `2M`, `3M`, `4M`, `6M`, `1Y`, `2Y`, `3Y`, `5Y`, `7Y`, `10Y`, `20Y`, `30Y` |

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
| EODHD_API_TOKEN | EODHD API token for real-time OHLCV endpoints | Required |
