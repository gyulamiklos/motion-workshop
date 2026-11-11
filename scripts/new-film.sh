#!/usr/bin/env bash
# New HyperFrames film from a pack: projects/YYYY-MM-DD_<slug>, pinned CLI (hyperframes.version),
# the pack's frame.md (the hyperframes skill reads it), fonts, logo and blocks.
# A pack is a brand (brands/<name>, local) or a style (styles/<name>, in git; for explainers and other unbranded films).
# Usage: scripts/new-film.sh <slug> [brand|style]      default: the only brand pack in brands/
set -eu
cd "$(dirname "$0")/.."
SLUG=${1:?usage: scripts/new-film.sh <slug> [brand|style]}
PACK=${2:-}
if [ -z "$PACK" ]; then
  packs=$(ls -d brands/*/ 2>/dev/null | wc -l | tr -d " ")
  [ "$packs" = 1 ] || { echo "name a brand or style: $(ls brands styles 2>/dev/null | grep -v -e ':$' -e '^$' | tr "\n" " ")" >&2; exit 1; }
  PACK=$(basename "$(ls -d brands/*/)")
fi
if [ -d "brands/$PACK" ]; then B="brands/$PACK"; elif [ -d "styles/$PACK" ]; then B="styles/$PACK"
else echo "no brand or style pack: $PACK (brands/, styles/)" >&2; exit 1; fi
V=$(tr -d '[:space:]' < hyperframes.version)
DIR="projects/$(date +%F)_$SLUG"
[ -e "$DIR" ] && { echo "exists: $DIR" >&2; exit 1; }

mkdir -p projects
(cd projects && HYPERFRAMES_SKIP_SKILLS=1 DO_NOT_TRACK=1 npx -y "hyperframes@$V" init "$(basename "$DIR")" --example blank --non-interactive --resolution landscape >/dev/null)
mkdir -p "$DIR/assets/fonts" "$DIR/assets/brand" "$DIR/compositions"
cp "$B/FRAME.md" "$DIR/frame.md"
for f in "$B"/fonts/*.ttf "$B"/fonts/*.woff2; do if [ -f "$f" ]; then cp "$f" "$DIR/assets/fonts/"; fi; done
[ -d "$B/assets" ] && cp "$B"/assets/* "$DIR/assets/brand/"
[ -d "$B/blocks" ] && cp "$B"/blocks/*.html "$DIR/compositions/"
cat > "$DIR/SPEC.md" <<SPEC
# $SLUG: spec

Pack: \`$B\` (frame.md in this folder). CLI: hyperframes@$V.

## Goal and audience
-

## Shots
| # | Time (s) | Shot | Motion | Copy |
|---|---|---|---|---|
SPEC
echo "$DIR"
