#!/bin/bash
set -euo pipefail

SRC="$HOME/Downloads"
DEST="$(dirname "$0")/fit_files/unprocessed"

moved=0
for f in "$SRC"/*.fit; do
  [ -e "$f" ] || { echo "No .fit files found in $SRC"; exit 0; }
  mv -f "$f" "$DEST/"
  echo "Moved: $(basename "$f")"
  ((moved++))
done

echo "$moved file(s) moved to fit_files/unprocessed"
