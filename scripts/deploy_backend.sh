#!/bin/bash
# Deploy backend to Google Cloud Run

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

PROJECT_ID=$(gcloud config get-value project)
echo "🚀 Deploying to project: $PROJECT_ID"
echo "📁 Build context: $PROJECT_ROOT"

# Build and deploy (from project root so ml/ is accessible)
gcloud builds submit --config backend/cloudbuild.yaml .

# Get the service URL
SERVICE_URL=$(gcloud run services describe type-beat-backend \
  --region us-central1 \
  --format 'value(status.url)' 2>/dev/null || echo "")

if [ -n "$SERVICE_URL" ]; then
  echo ""
  echo "✅ Backend deployed!"
  echo "📍 URL: $SERVICE_URL"
  echo ""
  echo "Update frontend/.env.production with:"
  echo "NEXT_PUBLIC_API_URL=$SERVICE_URL"
else
  echo "⚠️  Service deployed but URL not found. Check Cloud Run console."
fi
