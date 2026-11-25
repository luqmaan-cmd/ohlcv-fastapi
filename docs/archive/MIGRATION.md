# ohlcv_unified Migration Tracker

## Completed

- [x] `OhlcvUnified` model added to `models.py`
- [x] `instrument_id` added to `OhlcvDataBase` schema (backward compat with `asset_isin`)
- [x] `GET /ohlcv/` → `ohlcv_unified WHERE exchange = 'US'`
- [x] `GET /ohlcv/latest_close/` → `ohlcv_unified WHERE exchange = 'US'` + 7-day partition pruning
- [x] `GET /ohlcv/latest_close/{ticker}` → `ohlcv_unified WHERE exchange = 'US'` + 7-day partition pruning
- [x] `GET /ohlcv/{ohlcv_id}` → `ohlcv_unified` (exchange-agnostic)
- [x] `GET /ohlcv/stats/{ticker}` → `ohlcv_unified WHERE exchange = 'US'`

## Remaining

Blocked on `instrument_id` population per asset class. Route each group when its data is ready in `ohlcv_unified`.

### S&P 500 (currently joins `ohlcv_data` + `sp500_constituents` + `ticker_aliases`)

- [ ] `GET /sp500/latest/`
- [ ] `GET /sp500/latest_close/`
- [ ] `GET /sp500/history/`

### UK Stocks → `ohlcv_unified WHERE exchange = 'LSE'`

- [ ] `GET /uk/` (historical)
- [ ] `GET /uk/latest/`
- [ ] `GET /uk/latest_close/`

### ETF → `ohlcv_unified WHERE asset_type = 'ETF'`

- [ ] `GET /etf/` (historical)
- [ ] `GET /etf/latest/`
- [ ] `GET /etf/latest_close/`

### Index → `ohlcv_unified WHERE asset_type = 'INDEX'`

- [ ] `GET /index/` (historical)
- [ ] `GET /index/latest/`
- [ ] `GET /index/latest_close/`

### Government Bonds → `ohlcv_unified WHERE asset_type = 'Government Bonds'`

- [ ] `GET /gov-bond/` (historical)
- [ ] `GET /gov-bond/latest/`
- [ ] `GET /gov-bond/latest_close/`

### FX → `ohlcv_unified WHERE asset_type = 'FOREX'`

- [ ] `GET /fx/` (historical)
- [ ] `GET /fx/latest/`
- [ ] `GET /fx/latest_close/`

### Crypto → `ohlcv_unified WHERE asset_type = 'Cryptocurrencies'`

- [ ] `GET /crypto/` (historical)
- [ ] `GET /crypto/latest/`
- [ ] `GET /crypto/latest_close/`

### FTSE 100 → `ohlcv_unified WHERE exchange = 'LSE'` (subset of UK)

- [ ] `GET /ftse100/` (historical)
- [ ] `GET /ftse100/latest/`
- [ ] `GET /ftse100/latest_close/`

## Post-migration Cleanup

- [ ] Remove old OHLCV ORM models (`OhlcvData`, `UkOhlcvData`, `EtfIndexOhlcvData`, etc.)
- [ ] Drop old OHLCV tables (`ohlcv_data`, `ohlcv_data_uk`, `ohlcv_data_etf_index`, etc.)
- [ ] Remove `asset_isin` from schema (replace fully with `instrument_id`)
- [ ] Update asset list endpoints to query unified assets table
- [ ] Update `/assets/{ticker}` to query unified assets table
- [ ] Update `API_REFERENCE.md`
- [ ] Verify `tickers` table is kept in sync with `ohlcv_unified` (trigger update)
