#!/usr/bin/env bash
# New HyperFrames film with a brand pack: projects/YYYY-MM-DD_<slug>, pinned CLI (hyperframes.version),
# the brand's frame.md (the hyperframes skill reads it), fonts, logo and blocks.
# Usage: scripts/new-film.sh <slug> [brand]      brand defaults to the only pack in brands/
set -eu
cd "$(dirname "$0")/.."
SLUG=${1:?usage: scripts/new-film.sh <slug> [brand]}
BRAND=${2:-}
if [ -z "$BRAND" ]; then
  packs=$(ls -d brands/*/ 2>/dev/null | wc -l | tr -d " ")
  [ "$packs" = 1 ] || { echo "name the brand: $(ls brands 2>/dev/null | tr "\n" " ")" >&2; exit 1; }
  BRAND=$(basename "$(ls -d brands/*/)")
fi
V=$(tr -d '[:space:]' < hyperframes.version)
DIR="projects/$(date +%F)_$SLUG"
B="brands/$BRAND"
[ -d "$B" ] || { echo "no brand pack: $B" >&2; exit 1; }
[ -e "$DIR" ] && { echo "exists: $DIR" >&2; exit 1; }

(cd projects && HYPERFRAMES_SKIP_SKILLS=1 DO_NOT_TRACK=1 npx -y "hyperframes@$V" init "$(basename "$DIR")" --example blank --non-interactive --resolution landscape >/dev/null)
mkdir -p "$DIR/assets/fonts" "$DIR/assets/brand" "$DIR/compositions"
cp "$B/FRAME.md" "$DIR/frame.md"
cp "$B"/fonts/*.ttf "$DIR/assets/fonts/"
[ -d "$B/assets" ] && cp "$B"/assets/* "$DIR/assets/brand/"
[ -d "$B/blocks" ] && cp "$B"/blocks/*.html "$DIR/compositions/"
cat > "$DIR/SPEC.md" <<SPEC
# $SLUG: spec

Brand: \`$B\` (frame.md in this folder). CLI: hyperframes@$V.

## Goal and audience
-

## Shots
| # | Time (s) | Shot | Motion | Copy |
|---|---|---|---|---|
SPEC
echo "$DIR"
