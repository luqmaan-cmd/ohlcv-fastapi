#!/bin/bash

PROJECT_ID="testgke-412710"
SERVICE_NAME="ohlcv-api"
REGION="europe-west2"
VPC_CONNECTOR="bls-connector"

echo "Building and pushing container..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --vpc-connector $VPC_CONNECTOR \
  --set-env-vars DB_HOST=10.154.15.212,DB_USER=postgres,DB_PASSWORD=hSg8vrqSb9SYT1Eg,DB_NAME=asset_identification_scheme,API_KEY=0637848019b44f86cce1692f14b3a837e4dd66d21c07baf3d052e4ffc6d02b25 \
  --allow-unauthenticated \
  --port 8080 \
  --min-instances 0 \
  --max-instances 10 \
  --memory 512Mi \
  --cpu 1

echo "Deployment complete!"
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
