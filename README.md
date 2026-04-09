# OHLCV Data API

FastAPI application for accessing OHLCV (Open, High, Low, Close, Volume) financial data.

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

- **API Documentation**: See [DEVELOPER.md](./DEVELOPER.md)
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
└── DEVELOPER.md     # API documentation
```

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ohlcv/` | List OHLCV data with filters |
| GET | `/ohlcv/latest/{ticker}` | Get latest record for ticker |
| GET | `/ohlcv/stats/{ticker}` | Get statistics for ticker |
| GET | `/tickers/` | List all tickers |
| GET | `/ohlcv/{id}` | Get record by ID |
| POST | `/ohlcv/` | Create new record |
| POST | `/ohlcv/bulk/` | Bulk create records |
| PUT | `/ohlcv/{id}` | Update record |
| DELETE | `/ohlcv/{id}` | Delete record |

## Deploy to GCP Cloud Run

### Prerequisites
1. GCP CLI installed and authenticated: `gcloud auth login`
2. Docker installed
3. VPC Connector configured (already exists: `bls-connector`)

### Deploy
```bash
./deploy.sh
```

### Manual Deploy Steps
```bash
# Set your project
gcloud config set project testgke-412710

# Build and push to Container Registry
gcloud builds submit --tag gcr.io/testgke-412710/ohlcv-api

# Deploy to Cloud Run
gcloud run deploy ohlcv-api \
  --image gcr.io/testgke-412710/ohlcv-api \
  --platform managed \
  --region europe-west2 \
  --vpc-connector bls-connector \
  --set-env-vars DB_HOST=10.154.15.212,DB_USER=postgres,DB_PASSWORD=hSg8vrqSb9SYT1Eg,DB_NAME=asset_identification_scheme \
  --allow-unauthenticated \
  --port 8080
```

### Environment Variables

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
