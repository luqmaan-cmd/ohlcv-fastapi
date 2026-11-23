# API Reference

Base URL: `https://ohlcv-api-832081557693.europe-west2.run.app`

Authentication: All endpoints require an API key, supplied either as the `api_key` query parameter or the `X-API-Key` header. If both are sent, a match on either is accepted.

```
API_KEY = $API_KEY
```

```bash
curl -H "X-API-Key: $API_KEY" "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/latest_close/AAPL"
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/latest_close/AAPL?api_key=$API_KEY"
```

---

## 1. Historical OHLCV Data

Returns paginated historical OHLCV records for a date range. Supports batch queries via comma-separated tickers/symbols.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | API key for authentication |
| `tickers` / `symbols` | string | No | Comma-separated tickers (e.g., `AAPL,MSFT`). If omitted, returns data for all. |
| `start_date` | date | No | Start date (YYYY-MM-DD) |
| `end_date` | date | No | End date (YYYY-MM-DD) |
| `year` | integer | No | Filter by year (e.g., `2025`) |
| `month` | integer | No | Filter by month (1-12) |
| `open_min` / `open_max` | decimal | No | Open price range filter |
| `close_min` / `close_max` | decimal | No | Close price range filter |
| `volume_min` / `volume_max` | integer | No | Volume range filter |
| `sort_by` | string | No | Sort field: `date` (default), `volume`, `close`, `open`, `high`, `low` |
| `sort_order` | string | No | `asc` or `desc` (default) |
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Records per page (default: 1000, max: 5000) |

### US Stocks

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/?tickers=AAPL,MSFT&start_date=2025-01-01&end_date=2025-12-31&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Crypto

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/crypto/history/?tickers=BTC-USD,ETH-USD&start_date=2025-01-01&end_date=2025-12-31&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Commodities

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/commodity/?symbols=LGOc3,NICKEL&start_date=2025-01-01&end_date=2025-12-31&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Foreign Exchange (FX)

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/fx/?tickers=EURUSD,GBPUSD&start_date=2025-01-01&end_date=2025-12-31&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### ETFs

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/etf/?tickers=SPY,QQQ&start_date=2025-01-01&end_date=2025-12-31&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Indices

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/index/?tickers=GSPC,DJI&start_date=2025-01-01&end_date=2025-12-31&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### UK Stocks (LSE)

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/uk/?tickers=AZN,SHEL&start_date=2025-01-01&end_date=2025-12-31&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Government Bonds

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/?tickers=US10Y,UK10Y&start_date=2025-01-01&end_date=2025-12-31&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

---

## 2. Current / Real-Time Price

Returns real-time OHLCV data from EODHD's live API. The `tickers` parameter is **required**.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | API key for authentication |
| `tickers` | string | Yes | Comma-separated tickers (e.g., `AAPL,MSFT`) |

### US Stocks

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ohlcv/latest/?tickers=AAPL,MSFT&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Crypto

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/crypto/latest/?tickers=BTC-USD,ETH-USD&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Foreign Exchange (FX)

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/fx/latest/?tickers=EURUSD,GBPUSD&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### ETFs

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/etf/latest/?tickers=SPY,QQQ&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Indices

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/index/latest/?tickers=GSPC,DJI&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### UK Stocks (LSE)

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/uk/latest/?tickers=AZN,SHEL&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Government Bonds

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/latest/?tickers=US10Y,UK10Y&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Commodities (DB — Latest)

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/commodity/latest/?symbols=LGOc3,NICKEL&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

---

## 3. Supported Tickers

Returns a list of all supported tickers/symbols for each asset class.

### US Stocks (~12,500 tickers)

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/tickers/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Crypto Assets

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/crypto/assets/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Commodity Symbols

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/commodity/symbols/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### S&P 500 Constituents

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/sp500/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### FX Assets

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/fx/assets/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### UK Stock Assets (LSE)

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/uk/assets/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### FTSE 100 Constituents

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/ftse100/constituents/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### ETF Assets

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/etf/assets/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Index Assets

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/index/assets/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Government Bond Assets

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/gov-bond/assets/?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

---

## 4. Asset Lookup by Ticker

Look up asset metadata by ticker across all asset classes (US stocks, UK stocks, ETFs, indices, government bonds, FX, crypto, FTSE 100). Searches all asset tables in one request.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | API key for authentication |
| `ticker` | string | Yes | Ticker symbol (path parameter, e.g., `AAPL`, `BTC-USD`, `SPY`) |
| `exchange` | string | No | Filter by exchange to disambiguate tickers (e.g., `LSE`, `US`, `CC`) |

### US Stock

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/assets/AAPL?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Crypto

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/assets/BTC-USD?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### ETF

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/assets/SPY?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### UK Stock (with exchange filter)

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/assets/SDR?exchange=LSE&api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```

### Government Bond

```bash
curl "https://ohlcv-api-832081557693.europe-west2.run.app/assets/US10Y?api_key=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25"
```
