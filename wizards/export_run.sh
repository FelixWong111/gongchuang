#!/bin/bash

# Export one run's log and video for offline debugging.
# Usage: bash wizards/export_run.sh run_20250926_123456_123456_1234
set -e

RUN_CODE="$1"
if [ -z "$RUN_CODE" ]; then
    echo "Usage: $0 <run_code> [output_dir]" >&2
    exit 2
fi

OUTPUT_DIR="${2:-proj/assets/exports}"
mkdir -p "$OUTPUT_DIR"
ARCHIVE="$OUTPUT_DIR/${RUN_CODE}.tar.gz"

FILES=()
for path in \
    "proj/assets/logs/${RUN_CODE}.log" \
    "proj/assets/logs/${RUN_CODE}.log.1" \
    "proj/assets/logs/${RUN_CODE}.log.2" \
    "proj/assets/videos_temp/${RUN_CODE}.avi"; do
    if [ -f "$path" ]; then
        FILES+=("$path")
    fi
done

if [ "${#FILES[@]}" -eq 0 ]; then
    echo "No artifacts found for run: $RUN_CODE" >&2
    exit 1
fi

tar -czf "$ARCHIVE" "${FILES[@]}"
echo "Exported: $ARCHIVE"
