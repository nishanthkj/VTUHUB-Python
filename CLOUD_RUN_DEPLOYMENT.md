# Google Cloud Run Deployment Guide

This guide will help you deploy the VTU Scraper API to Google Cloud Run.

## Prerequisites

1. **Google Cloud Account**: You need a Google Cloud account with billing enabled
2. **Google Cloud SDK**: Install the [gcloud CLI](https://cloud.google.com/sdk/docs/install)
3. **Docker**: Install [Docker Desktop](https://www.docker.com/products/docker-desktop) or Docker Engine
4. **Project Setup**: Create a GCP project or use an existing one

## Quick Start

### Option 1: Using the Deployment Script (Recommended)

#### For Linux/macOS:
```bash
# Set your GCP project ID
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
export SERVICE_NAME="vtuhub-api"

# Make the script executable
chmod +x deploy-cloud-run.sh

# Run the deployment script
./deploy-cloud-run.sh
```

#### For Windows (PowerShell):
```powershell
# Set your GCP project ID
$env:GCP_PROJECT_ID = "your-project-id"
$env:GCP_REGION = "us-central1"
$env:SERVICE_NAME = "vtuhub-api"

# Run the deployment script
.\deploy-cloud-run.ps1
```

### Option 2: Manual Deployment

#### Step 1: Authenticate with Google Cloud
```bash
gcloud auth login
gcloud auth configure-docker
```

#### Step 2: Set Your Project
```bash
gcloud config set project YOUR_PROJECT_ID
```

#### Step 3: Enable Required APIs
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### Step 4: Build and Push the Docker Image
```bash
# Build the image
docker build -f Dockerfile.cpu -t gcr.io/YOUR_PROJECT_ID/vtuhub-api:latest .

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/vtuhub-api:latest
```

#### Step 5: Deploy to Cloud Run
```bash
gcloud run deploy vtuhub-api \
    --image gcr.io/YOUR_PROJECT_ID/vtuhub-api:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars "PYTHONUNBUFFERED=1,HF_HOME=/app/.cache/huggingface,HF_HUB_DISABLE_SYMLINKS_WARNING=1"
```

### Option 3: Automated Deployment with Cloud Build

1. **Connect your repository to Cloud Build**:
   - Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
   - Click "Create Trigger"
   - Connect your repository (GitHub, GitLab, or Bitbucket)
   - Select the repository and branch

2. **Configure the trigger**:
   - Name: `deploy-vtuhub-api`
   - Event: Push to a branch
   - Branch: `^main$` (or your main branch)
   - Configuration: Cloud Build configuration file
   - Location: `cloudbuild.yaml`

3. **Push to your repository**:
   ```bash
   git push origin main
   ```
   Cloud Build will automatically build and deploy your service.

## Configuration Options

### Resource Allocation

The default configuration uses:
- **Memory**: 2Gi (2 GB)
- **CPU**: 2 vCPUs
- **Timeout**: 300 seconds (5 minutes)
- **Max Instances**: 10

You can adjust these based on your needs:

```bash
gcloud run services update vtuhub-api \
    --memory 4Gi \
    --cpu 4 \
    --timeout 600 \
    --max-instances 20 \
    --region us-central1
```

### Environment Variables

The deployment sets these environment variables:
- `PYTHONUNBUFFERED=1`: Ensures Python output is not buffered
- `HF_HOME=/app/.cache/huggingface`: Hugging Face cache directory
- `HF_HUB_DISABLE_SYMLINKS_WARNING=1`: Disables symlink warnings

To add more environment variables:
```bash
gcloud run services update vtuhub-api \
    --update-env-vars "NEW_VAR=value" \
    --region us-central1
```

### Authentication

By default, the service is deployed with `--allow-unauthenticated`, making it publicly accessible. To require authentication:

```bash
gcloud run deploy vtuhub-api \
    --no-allow-unauthenticated \
    --image gcr.io/YOUR_PROJECT_ID/vtuhub-api:latest \
    --region us-central1
```

## Updating the Service

### Update the Image
```bash
# Rebuild and push
docker build -f Dockerfile.cpu -t gcr.io/YOUR_PROJECT_ID/vtuhub-api:latest .
docker push gcr.io/YOUR_PROJECT_ID/vtuhub-api:latest

# Deploy the new version
gcloud run deploy vtuhub-api \
    --image gcr.io/YOUR_PROJECT_ID/vtuhub-api:latest \
    --region us-central1
```

### View Service Details
```bash
gcloud run services describe vtuhub-api --region us-central1
```

### View Logs
```bash
gcloud run services logs read vtuhub-api --region us-central1
```

## Testing the Deployment

After deployment, you'll receive a service URL. Test it:

```bash
# Health check
curl https://YOUR_SERVICE_URL/health

# API endpoint
curl -X POST https://YOUR_SERVICE_URL/single-post \
    -H "Content-Type: application/json" \
    -d '{
        "index_url": "https://results.vtu.ac.in/JJEcbcs25/index.php",
        "usn": "YOUR_USN"
    }'
```

## Cost Optimization

Cloud Run charges based on:
- **CPU and Memory**: Only when handling requests
- **Requests**: Per million requests
- **Duration**: Per 100ms of execution time

Tips to reduce costs:
- Use appropriate memory allocation (don't over-allocate)
- Set reasonable `max-instances` limits
- Use `min-instances=0` (default) to scale to zero when idle
- Monitor usage in Cloud Console

## Troubleshooting

### Build Failures
- Check Dockerfile syntax
- Verify all dependencies are in `requirements-docker.txt`
- Review Cloud Build logs in the GCP Console

### Deployment Failures
- Ensure the image was pushed successfully
- Check service logs: `gcloud run services logs read vtuhub-api --region us-central1`
- Verify environment variables are set correctly

### Runtime Issues
- Check application logs in Cloud Run console
- Verify the service is listening on port 8080
- Ensure health check endpoint `/health` is working

## Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [Container Registry Documentation](https://cloud.google.com/container-registry/docs)

