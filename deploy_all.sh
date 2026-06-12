#!/usr/bin/env bash
# ============================================================================
# Kiwimath — Full Deploy Script (Backend + Flutter AAB)
# Run from: ~/Downloads/kiwimath/
# Usage: chmod +x deploy_all.sh && ./deploy_all.sh
# ============================================================================
set -euo pipefail

echo "=========================================="
echo "  KIWIMATH FULL DEPLOY"
echo "=========================================="
echo ""

# --- Step 1: Deploy Backend to Cloud Run ---
echo ">>> STEP 1: Deploying backend to Cloud Run..."
cd backend
chmod +x deploy.sh
./deploy.sh
cd ..
echo ""
echo "✅ Backend deployed!"
echo ""

# --- Step 2: Build Flutter AAB for Play Store ---
echo ">>> STEP 2: Building Flutter AAB..."
cd app

# Verify keystore exists
if [ ! -f ~/Downloads/kiwimath-upload-key.jks ]; then
    echo "❌ ERROR: Keystore not found at ~/Downloads/kiwimath-upload-key.jks"
    exit 1
fi
echo "✅ Keystore found"

# Clean and build
flutter clean
flutter pub get
flutter build appbundle --release

# Copy AAB to Downloads for easy access
AAB_PATH="build/app/outputs/bundle/release/app-release.aab"
if [ -f "$AAB_PATH" ]; then
    cp "$AAB_PATH" ~/Downloads/kiwimath-release.aab
    echo ""
    echo "✅ AAB built successfully!"
    echo "📦 File: ~/Downloads/kiwimath-release.aab"
    echo "📏 Size: $(du -h ~/Downloads/kiwimath-release.aab | cut -f1)"
else
    echo "❌ AAB not found at expected path"
    ls -la build/app/outputs/bundle/release/ 2>/dev/null || echo "Release dir doesn't exist"
    exit 1
fi

cd ..
echo ""
echo "=========================================="
echo "  ALL DONE!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Go to play.google.com/console"
echo "  2. Upload ~/Downloads/kiwimath-release.aab"
echo "  3. Submit for review"
echo ""
