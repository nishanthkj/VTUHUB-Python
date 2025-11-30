#!/bin/bash

# Google Cloud Run Deployment Script
# This script builds and deploys the Docker image to Google Cloud Run

set -e

# Configuration - Update these variables
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-vtuhub-api}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
DOCKERFILE="${DOCKERFILE:-Dockerfile.cpu}"

echo "🚀 Starting deployment to Google Cloud Run"
echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service Name: ${SERVICE_NAME}"
echo "Image: ${IMAGE_NAME}"
echo "Dockerfile: ${DOCKERFILE}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed"
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    exit 1
fi

# Authenticate with Google Cloud
echo "📋 Authenticating with Google Cloud..."
gcloud auth configure-docker

# Set the project
echo "📋 Setting GCP project..."
gcloud config set project ${PROJECT_ID}

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -f ${DOCKERFILE} -t ${IMAGE_NAME}:latest .

# Push the image to Google Container Registry
echo "📤 Pushing image to GCR..."
docker push ${IMAGE_NAME}:latest

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars "PYTHONUNBUFFERED=1,HF_HOME=/app/.cache/huggingface,HF_HUB_DISABLE_SYMLINKS_WARNING=1"

echo "✅ Deployment complete!"
echo "📋 Getting service URL..."
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)'

