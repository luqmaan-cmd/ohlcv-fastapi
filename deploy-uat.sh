#!/bin/bash
set -euo pipefail

PROJECT_ID="testgke-412710"
SERVICE_NAME="ohlcv-api-uat"
REGION="europe-west2"
VPC_CONNECTOR="bls-connector"

echo "Building and pushing container..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

echo "Deploying to Cloud Run (UAT)..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --vpc-connector $VPC_CONNECTOR \
  --set-secrets="DB_HOST=db-host:latest,DB_USER=db-user:latest,DB_PASSWORD=db-password:latest,DB_NAME=db-name:latest,DB_PORT=db-port:latest,API_KEY=api-key:latest,API_KEYS=api-keys-uat:latest,EODHD_API_TOKEN=eodhd-api-token:latest" \
  --allow-unauthenticated \
  --port 8080 \
  --min-instances 0 \
  --max-instances 20 \
  --concurrency 100 \
  --memory 2Gi \
  --cpu 4 \
  --set-env-vars="APP_ENV=uat,DB_POOL_SIZE=3,DB_MAX_OVERFLOW=2"

echo "Deployment complete!"
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
