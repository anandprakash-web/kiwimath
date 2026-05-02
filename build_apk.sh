#!/usr/bin/env bash
# ============================================================================
# Kiwimath — Build Release APK (v1.2.0+4)
#
# Usage:  ./build_apk.sh
# Output: APK copied to ~/Downloads/kiwimath-v1.2.0-release.apk
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$SCRIPT_DIR/app"
OUTPUT_NAME="kiwimath-v1.2.0-release.apk"
OUTPUT_PATH="$SCRIPT_DIR/$OUTPUT_NAME"

echo "=== Kiwimath APK Build ==="
echo "App dir: $APP_DIR"
echo ""

# Verify Flutter
if ! command -v flutter &>/dev/null; then
    echo "ERROR: Flutter not found. Install from https://docs.flutter.dev/get-started/install"
    exit 1
fi
echo "Flutter: $(flutter --version | head -1)"

# Verify keystore
KEY_PROPS="$APP_DIR/android/key.properties"
if [ -f "$KEY_PROPS" ]; then
    STORE_FILE=$(grep storeFile "$KEY_PROPS" | cut -d= -f2)
    if [ ! -f "$STORE_FILE" ]; then
        echo "WARNING: Keystore not found at $STORE_FILE"
        echo "         APK will be signed with debug key."
    else
        echo "Keystore: $STORE_FILE (found)"
    fi
else
    echo "WARNING: key.properties not found. APK will use debug signing."
fi

cd "$APP_DIR"

# Step 1: Clean
echo ""
echo ">>> Cleaning previous build..."
flutter clean

# Step 2: Get dependencies
echo ""
echo ">>> Getting dependencies..."
flutter pub get

# Step 3: Build release APK
echo ""
echo ">>> Building release APK..."
flutter build apk --release --no-tree-shake-icons

# Step 4: Copy to project root
APK_PATH="$APP_DIR/build/app/outputs/flutter-apk/app-release.apk"
if [ -f "$APK_PATH" ]; then
    cp "$APK_PATH" "$OUTPUT_PATH"
    SIZE=$(ls -lh "$OUTPUT_PATH" | awk '{print $5}')
    echo ""
    echo "=== BUILD SUCCESSFUL ==="
    echo "APK: $OUTPUT_PATH"
    echo "Size: $SIZE"
    echo ""
    echo "To install on device:"
    echo "  adb install $OUTPUT_PATH"
    echo ""
    echo "To also build AAB for Play Store:"
    echo "  cd $APP_DIR && flutter build appbundle --release"
else
    echo ""
    echo "ERROR: APK not found at expected path."
    echo "Check build output above for errors."
    exit 1
fi
