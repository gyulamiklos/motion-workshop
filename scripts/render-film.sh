#!/usr/bin/env bash
# Check and render a film with the pinned CLI, no telemetry; with music, also a version without it.
# Usage: scripts/render-film.sh <film dir> [--skip-no-music]
# Writes <film>/out/<name>.mp4 (and <name>-nobgm.mp4 when the film has an <audio id="bgm">), copies them to
# renders/<film folder name>[-nobgm].mp4 and prints duration and loudness.
set -eu
cd "$(dirname "$0")/.."
ROOT=$(pwd)
FILM=$(cd "${1:?usage: render-film.sh <film dir>}" && pwd)
NAME=$(basename "$FILM")
V=$(tr -d '[:space:]' < hyperframes.version)
hf() { (cd "$FILM" && DO_NOT_TRACK=1 npx -y "hyperframes@$V" "$@"); }

hf check >/dev/null 2>&1 || { hf check 2>&1 | tail -20; exit 1; }
hf render -q delivery -o "out/$NAME.mp4" --quiet >/dev/null 2>&1
cp "$FILM/out/$NAME.mp4" "$ROOT/renders/$NAME.mp4"

# the no-music version exists only while it renders: two root compositions side by side would both play
if [ "${2:-}" != "--skip-no-music" ] && grep -q '<audio id="bgm"' "$FILM/index.html"; then
  trap 'rm -f "$FILM/index-nobgm.html"' EXIT
  sed 's|<audio id="bgm" class="clip"|<audio id="bgm" class="clip" data-hidden|' "$FILM/index.html" > "$FILM/index-nobgm.html"
  hf render -c index-nobgm.html -q delivery -o "out/$NAME-nobgm.mp4" --quiet >/dev/null 2>&1
  rm -f "$FILM/index-nobgm.html"
  cp "$FILM/out/$NAME-nobgm.mp4" "$ROOT/renders/$NAME-nobgm.mp4"
fi

for f in "$ROOT/renders/$NAME.mp4" "$ROOT/renders/$NAME-nobgm.mp4"; do
  [ -f "$f" ] || continue
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  l=$(ffmpeg -hide_banner -nostdin -i "$f" -af ebur128 -f null /dev/null 2>&1 | grep -E '^\s+I:' | tail -1 | awk '{print $2, $3}')
  echo "$(basename "$f"): ${d}s, ${l}"
done
