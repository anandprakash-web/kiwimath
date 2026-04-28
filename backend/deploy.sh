#!/usr/bin/env bash
# ============================================================================
# Kiwimath API — Deploy to Google Cloud Run (v2-only)
#
# Prerequisites:
#   1. gcloud CLI installed and authenticated
#   2. GCP project created with billing enabled
#   3. Firestore database created (Native mode)
#
# Usage:
#   ./deploy.sh                    # uses defaults
#   GCP_PROJECT=my-proj ./deploy.sh  # override project
# ============================================================================
set -euo pipefail

# Config — edit these or pass as env vars.
GCP_PROJECT="${GCP_PROJECT:-kiwimath-801c1}"
GCP_REGION="${GCP_REGION:-asia-south1}"       # Mumbai — closest to Indian users
SERVICE_NAME="${SERVICE_NAME:-kiwimath-api}"
IMAGE_NAME="gcr.io/${GCP_PROJECT}/${SERVICE_NAME}"

echo "=== Kiwimath API Deploy (v2) ==="
echo "Project:  $GCP_PROJECT"
echo "Region:   $GCP_REGION"
echo "Service:  $SERVICE_NAME"
echo ""

# Step 1: Set project.
echo ">>> Setting GCP project..."
gcloud config set project "$GCP_PROJECT"

# Step 2: Enable required APIs (idempotent).
echo ">>> Enabling APIs..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    firestore.googleapis.com \
    containerregistry.googleapis.com \
    2>/dev/null || true

# Step 3: Build and push Docker image.
echo ">>> Building Docker image..."
TMPDIR=$(mktemp -d)
cp -r . "$TMPDIR/backend"

# Copy v2 content (flat JSON/SVG questions).
V2_FOUND=false
for v2_path in "../content-v2" "../../content-v2" "../Kiwimath_Content_v2"; do
    if [ -d "$v2_path" ]; then
        cp -r "$v2_path" "$TMPDIR/backend/content-v2"
        echo "    (v2 content baked from $v2_path)"
        V2_FOUND=true
        break
    fi
done
if [ "$V2_FOUND" = false ]; then
    echo "ERROR: No v2 content folder found. Cannot deploy without content."
    rm -rf "$TMPDIR"
    exit 1
fi

# Build from the temp context with content included.
cd "$TMPDIR/backend"
cat >> Dockerfile <<'BAKE'

# Bake v2 content into image (added by deploy.sh).
COPY content-v2/ /content-v2/
BAKE

gcloud builds submit --tag "$IMAGE_NAME" .
cd - > /dev/null
rm -rf "$TMPDIR"

# Step 4: Deploy to Cloud Run.
echo ">>> Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME" \
    --region "$GCP_REGION" \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 1 \
    --max-instances 10 \
    --concurrency 80 \
    --timeout 60 \
    --set-env-vars "KIWIMATH_V2_CONTENT_DIR=/content-v2" \
    --port 8000

# Step 5: Print the URL.
URL=$(gcloud run services describe "$SERVICE_NAME" --region "$GCP_REGION" --format 'value(status.url)')
echo ""
echo "=== Deployed successfully! ==="
echo "URL: $URL"
echo "Health: ${URL}/health"
echo "Swagger: ${URL}/docs"
echo ""
echo "Next steps:"
echo "  1. Update Flutter app's API_BASE_URL to: $URL"
echo "  2. Run: curl ${URL}/health"
