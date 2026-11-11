#!/usr/bin/env bash
# Build a block from a Blender scene: render the scene (or reuse its frames), encode the video, put the HUD from the
# scene's hud.json on top (templates/blender-hud), and render the composition with scripts/render-block.sh.
# Usage: scripts/blender-block.sh <scene.py> <hud.json> [--dir DIR] [--render] [--samples N] [--out out.mp4]
#   --dir     work folder (default renders/blocks/<id>-blender): frames/, proj.json and block/ (the HTML + assets)
#   --render  render the frames even if DIR/frames already has them
# Nothing here is committed: the video, proj.json and the block folder are outputs under renders/.
set -eu
cd "$(dirname "$0")/.."
ROOT=$(pwd)
USAGE="usage: blender-block.sh <scene.py> <hud.json> [--dir DIR] [--render] [--samples N] [--out out.mp4]"
SCENE=$(realpath "${1:?$USAGE}"); HUD=$(realpath "${2:?$USAGE}"); shift 2
ID=$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' "$HUD")
DIR=renders/blocks/$ID-blender; RENDER=""; SAMPLES=""; OUT=renders/blocks/$ID.mp4
while [ $# -gt 0 ]; do
  case "$1" in
    --dir) DIR=${2:?$USAGE}; shift 2 ;;
    --render) RENDER=1; shift ;;
    --samples) SAMPLES=${2:?$USAGE}; shift 2 ;;
    --out) OUT=${2:?$USAGE}; shift 2 ;;
    *) echo "$USAGE" >&2; exit 2 ;;
  esac
done
case "$DIR" in /*) ;; *) DIR="$ROOT/$DIR" ;; esac
mkdir -p "$DIR/frames" "$DIR/block/assets"

if [ -n "$RENDER" ] || [ ! -f "$DIR/frames/f_0000.png" ] || [ ! -f "$DIR/proj.json" ]; then
  rm -f "$DIR"/frames/f_*.png
  extra=(); [ -n "$SAMPLES" ] && extra+=(--samples "$SAMPLES")
  scripts/blender.sh -b --factory-startup -P "$SCENE" -- --out "$DIR" "${extra[@]}" > "$DIR/render.log" 2>&1 \
    || { tail -20 "$DIR/render.log" >&2; echo "blender-block: the render failed" >&2; exit 1; }
fi

VIDEO=$(basename "${SCENE%.py}").mp4
ffmpeg -loglevel error -y -framerate 60 -i "$DIR/frames/f_%04d.png" -c:v libx264 -pix_fmt yuv420p -crf 16 "$DIR/block/assets/$VIDEO"
cp "$DIR/proj.json" "$DIR/block/assets/proj.json"
cp "$HUD" "$DIR/block/assets/hud.json"
python3 -I - "$ID" "$HUD" "$VIDEO" "$DIR/block/$ID.html" <<'PY'
import json, sys
id_, hud, video, dst = sys.argv[1:5]
h = json.load(open(hud))
s = open("templates/blender-hud/block.html").read()
for k, v in {"__ID__": id_, "__TITLE__": h.get("title", id_), "__DUR__": str(h["duration"]), "__VIDEO__": video}.items():
    s = s.replace(k, v)
open(dst, "w").write(s)
PY
case "$OUT" in /*) ;; *) OUT="$ROOT/$OUT" ;; esac
scripts/render-block.sh "$DIR/block/$ID.html" "$OUT" --fps 60
