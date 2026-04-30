#!/bin/bash
# Generate an upload keystore for Google Play Store
# Run this ONCE, then keep the .jks file safe forever!

set -euo pipefail

KEYSTORE_FILE="$HOME/kiwimath-upload-key.jks"
ALIAS="kiwimath-upload"

echo "=== Kiwimath Upload Keystore Generator ==="
echo ""
echo "This will create: $KEYSTORE_FILE"
echo "IMPORTANT: Back up this file! If you lose it, you cannot update your app."
echo ""

keytool -genkey -v \
  -keystore "$KEYSTORE_FILE" \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -alias "$ALIAS" \
  -dname "CN=Kiwimath, OU=Mobile, O=Vedantu, L=Bangalore, ST=Karnataka, C=IN"

echo ""
echo "Keystore created at: $KEYSTORE_FILE"
echo ""
echo "Now create android/key.properties with:"
echo ""
echo "storePassword=<password you just entered>"
echo "keyPassword=<password you just entered>"
echo "keyAlias=$ALIAS"
echo "storeFile=$KEYSTORE_FILE"
