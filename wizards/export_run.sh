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
    "proj/assets/logs/${RUN_CODE}.debug.log" \
    "proj/assets/logs/${RUN_CODE}.debug.log.1" \
    "proj/assets/logs/${RUN_CODE}.debug.log.2" \
    "proj/assets/logs/${RUN_CODE}.json" \
    "proj/assets/videos_temp/${RUN_CODE}.avi"; do
    if [ -f "$path" ]; then
        FILES+=("$path")
    fi
done

SYSTEM_INFO="${OUTPUT_DIR}/${RUN_CODE}.system.txt"
{
    echo "run_code=${RUN_CODE}"
    date --iso-8601=seconds 2>/dev/null || date
    uname -a 2>/dev/null || true
    df -h . 2>/dev/null || true
    python3 --version 2>/dev/null || true
} > "$SYSTEM_INFO"
FILES+=("$SYSTEM_INFO")

if [ "${#FILES[@]}" -eq 0 ]; then
    echo "No artifacts found for run: $RUN_CODE" >&2
    exit 1
fi

tar -czf "$ARCHIVE" "${FILES[@]}"
sha256sum "$ARCHIVE" > "${ARCHIVE}.sha256"
rm -f "$SYSTEM_INFO"
echo "Exported: $ARCHIVE"
echo "Checksum: ${ARCHIVE}.sha256"
