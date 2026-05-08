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
  --set-secrets="DB_HOST=db-host:latest,DB_USER=db-user:latest,DB_PASSWORD=db-password:latest,DB_NAME=db-name:latest,DB_PORT=db-port:latest,API_KEY=api-key:latest" \
  --allow-unauthenticated \
  --port 8080 \
  --min-instances 0 \
  --max-instances 10 \
  --memory 512Mi \
  --cpu 1

echo "Deployment complete!"
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
