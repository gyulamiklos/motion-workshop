#!/usr/bin/env bash
# Render one block (a recipe or template HTML file) on its own, to look at it or to measure it against a reference.
# Usage: scripts/render-block.sh <block.html> [out.mp4] [--fps N] [--duration S] [--variables JSON]
#   --duration  sets the root's length (and every clip as long as the root); default: the block's own
#   --variables JSON object over the block's variable defaults, e.g. '{"text":"Hello"}'
# Out default: renders/blocks/<block name>.mp4. A block is not a project, so it is copied into a temporary one
# (with the assets/ folder next to it, if any) and rendered there with the pinned CLI, no telemetry.
set -eu
cd "$(dirname "$0")/.."
ROOT=$(pwd)
USAGE="usage: render-block.sh <block.html> [out.mp4] [--fps N] [--duration S] [--variables JSON]"
BLOCK=$(cd "$(dirname "${1:?$USAGE}")" && pwd)/$(basename "$1"); shift
NAME=$(basename "${BLOCK%.*}")
OUT="$ROOT/renders/blocks/$NAME.mp4"
case "${1:-}" in ""|--*) ;; *) OUT=$1; shift ;; esac
FPS=""; DURATION=""; VARS=""
while [ $# -gt 0 ]; do
  case "$1" in
    --fps) FPS=${2:?$USAGE}; shift 2 ;;
    --duration) DURATION=${2:?$USAGE}; shift 2 ;;
    --variables) VARS=${2:?$USAGE}; shift 2 ;;
    *) echo "$USAGE" >&2; exit 2 ;;
  esac
done
case "$OUT" in /*) ;; *) OUT="$ROOT/$OUT" ;; esac
mkdir -p "$(dirname "$OUT")"
V=$(tr -d '[:space:]' < hyperframes.version)

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
python3 -I - "$BLOCK" "$TMP/index.html" "$DURATION" <<'PY'
import re, sys
src, dst, dur = sys.argv[1:4]
s = open(src).read()
if dur:
    m = re.search(r'data-composition-id="[^"]*"[^>]*?data-duration="([^"]+)"', s, re.S)
    if not m:
        sys.exit("render-block: no root data-duration to change")
    s = s.replace(f'data-duration="{m.group(1)}"', f'data-duration="{dur}"')
open(dst, "w").write(s)
PY
[ -d "$(dirname "$BLOCK")/assets" ] && cp -r "$(dirname "$BLOCK")/assets" "$TMP/assets"

args=(-o "$OUT" --quiet)
[ -n "$FPS" ] && args+=(-f "$FPS")
[ -n "$VARS" ] && args+=(--variables "$VARS" --strict-variables)
(cd "$TMP" && DO_NOT_TRACK=1 npx -y "hyperframes@$V" check >/dev/null 2>&1) || { (cd "$TMP" && DO_NOT_TRACK=1 npx -y "hyperframes@$V" check 2>&1 | tail -20); exit 1; }
log=$(cd "$TMP" && DO_NOT_TRACK=1 npx -y "hyperframes@$V" render "${args[@]}" 2>&1) || { echo "$log" | tail -15 >&2; echo "render failed: $BLOCK" >&2; exit 1; }
echo "$OUT: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s"
