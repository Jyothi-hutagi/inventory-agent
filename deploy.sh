#!/bin/bash
# ============================================================
# deploy.sh — Deploy Inventory Intelligence Agent to Cloud Run
# Usage: bash deploy.sh
# ============================================================
set -e

# ── CONFIG — edit these ──────────────────────────────────────
PROJECT_ID="jyothiapikey1"
REGION="asia-south1"          # Mumbai — closest to Belagavi
BACKEND_SERVICE="inventory-agent-api"
FRONTEND_SERVICE="inventory-agent-ui"
# ─────────────────────────────────────────────────────────────

echo "🔧 Setting GCP project..."
gcloud config set project $PROJECT_ID

echo "🔌 Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com \
  bigquery.googleapis.com \
  artifactregistry.googleapis.com \
  --quiet

# ── STEP 1: Upload service account key to Secret Manager ─────
echo ""
echo "📦 STEP 1: Storing GCP credentials in Secret Manager..."
echo "   Enter the FULL path to your service account JSON key:"
read -p "   Path: " SA_KEY_PATH

if [ ! -f "$SA_KEY_PATH" ]; then
  echo "❌ File not found: $SA_KEY_PATH"
  exit 1
fi

gcloud secrets create gcp-sa-key \
  --data-file="$SA_KEY_PATH" \
  --replication-policy="automatic" \
  --quiet 2>/dev/null || \
gcloud secrets versions add gcp-sa-key \
  --data-file="$SA_KEY_PATH" \
  --quiet

echo "✅ Secret stored."

# ── STEP 2: Grant Cloud Run SA access to secrets + BigQuery ──
echo ""
echo "🔐 STEP 2: Setting up IAM permissions..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
CLOUD_RUN_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding gcp-sa-key \
  --member="serviceAccount:${CLOUD_RUN_SA}" \
  --role="roles/secretmanager.secretAccessor" \
  --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUD_RUN_SA}" \
  --role="roles/bigquery.dataViewer" \
  --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUD_RUN_SA}" \
  --role="roles/bigquery.user" \
  --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUD_RUN_SA}" \
  --role="roles/aiplatform.user" \
  --quiet

echo "✅ IAM permissions set."

# ── STEP 3: Deploy Backend ────────────────────────────────────
echo ""
echo "🚀 STEP 3: Building & deploying backend to Cloud Run..."
gcloud run deploy $BACKEND_SERVICE \
  --source . \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 120 \
  --concurrency 10 \
  --set-secrets "GOOGLE_APPLICATION_CREDENTIALS=gcp-sa-key:latest" \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=true" \
  --quiet

BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE \
  --region $REGION \
  --format="value(status.url)")

echo "✅ Backend deployed: $BACKEND_URL"

# ── STEP 4: Deploy Frontend ───────────────────────────────────
echo ""
echo "🌐 STEP 4: Building & deploying frontend to Cloud Run..."
cd frontend

gcloud run deploy $FRONTEND_SERVICE \
  --source . \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 120 \
  --set-build-env-vars "VITE_API_URL=${BACKEND_URL}" \
  --quiet


FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE \
  --region $REGION \
  --format="value(status.url)")

cd ..

echo ""
echo "════════════════════════════════════════════"
echo "✅ DEPLOYMENT COMPLETE"
echo "════════════════════════════════════════════"
echo ""
echo "  🌐 Frontend (submit this): $FRONTEND_URL"
echo "  🔧 Backend API:            $BACKEND_URL"
echo "  ❤️  Health check:          $BACKEND_URL/health"
echo ""
echo "  Test with:"
echo "  curl -X POST $BACKEND_URL/ask \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"question\": \"Give me an inventory overview\"}'"
echo ""