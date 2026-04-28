#!/bin/bash
# merge_content.sh — Consolidate all question content into one tree.
#
# Copies the 68 sample files from _Schema/samples/ into
# ~/Documents/Kiwimath-Content/Grade1/01-Counting/ so the engine
# can load everything from a single KIWIMATH_CONTENT_DIR.
#
# Usage:
#   cd ~/Downloads/kiwimath
#   bash merge_content.sh
#
# After running, start the backend with:
#   cd backend
#   KIWIMATH_CONTENT_DIR=~/Documents/Kiwimath-Content/Grade1 \
#   KIWIMATH_DAG_PATH=../_Schema/concept_graph_grade1.json \
#   python3 -m uvicorn app.main:app --port 8000

set -euo pipefail

SAMPLES_DIR="$(cd "$(dirname "$0")" && pwd)/_Schema/samples"
CONTENT_DIR="$HOME/Documents/Kiwimath-Content/Grade1"
COUNT_DIR="$CONTENT_DIR/01-Counting"

# Sanity checks
if [ ! -d "$SAMPLES_DIR" ]; then
  echo "ERROR: Samples directory not found at $SAMPLES_DIR"
  exit 1
fi

if [ ! -d "$CONTENT_DIR" ]; then
  echo "ERROR: Content directory not found at $CONTENT_DIR"
  echo "Expected: ~/Documents/Kiwimath-Content/Grade1/"
  echo "Make sure the academic content is in place first."
  exit 1
fi

# Create 01-Counting if it doesn't exist
mkdir -p "$COUNT_DIR"

# Copy sample files (counting + arithmetic + shapes samples)
copied=0
skipped=0
for f in "$SAMPLES_DIR"/*.json; do
  fname=$(basename "$f")
  # Check if file already exists in any subfolder
  existing=$(find "$CONTENT_DIR" -name "$fname" -type f 2>/dev/null | head -1)
  if [ -n "$existing" ]; then
    skipped=$((skipped + 1))
  else
    # Route by prefix: G1-COUNT → 01-Counting, G1-ARITH → 02-Arithmetic, G1-SHAPE → 03-Shapes
    if [[ "$fname" == G1-COUNT* ]]; then
      dest="$CONTENT_DIR/01-Counting"
    elif [[ "$fname" == G1-ARITH* ]]; then
      dest="$CONTENT_DIR/02-Arithmetic"
    elif [[ "$fname" == G1-SHAPE* ]]; then
      dest="$CONTENT_DIR/03-Shapes"
    elif [[ "$fname" == G1-SPATIAL* ]]; then
      dest="$CONTENT_DIR/04-Spatial"
    elif [[ "$fname" == G1-MEASURE* ]] || [[ "$fname" == G1-LOGIC* ]]; then
      dest="$CONTENT_DIR/05-Measurement-Logic"
    else
      dest="$COUNT_DIR"  # fallback
    fi
    mkdir -p "$dest"
    cp "$f" "$dest/"
    copied=$((copied + 1))
  fi
done

echo "Done! Copied $copied files, skipped $skipped (already exist)."
echo ""
echo "Content tree:"
for d in "$CONTENT_DIR"/*/; do
  count=$(find "$d" -name "*.json" -type f | wc -l)
  echo "  $(basename "$d")/  — $count files"
done
total=$(find "$CONTENT_DIR" -name "*.json" -type f | wc -l)
echo "  TOTAL: $total files"
