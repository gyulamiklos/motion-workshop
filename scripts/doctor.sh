#!/usr/bin/env bash
# Is the workshop ready to make a film? Tools on PATH, the pinned HyperFrames CLI and its skills,
# the pinned video-shotcraft clone (recipe cards and sounds), the optional voice and capture tools.
# Usage: scripts/doctor.sh      Exit code: 0 if ready, 1 otherwise (warnings don't fail).
set -u
cd "$(dirname "$0")/.." || exit 1
ROOT=$(pwd)
fail=0
ok()   { echo "ok    $*"; }
bad()  { echo "FAIL  $*"; fail=1; }
warn() { echo "warn  $*"; }

command -v node >/dev/null 2>&1 && [ "$(node -p 'process.versions.node.split(".")[0]')" -ge 22 ] && ok "node $(node -v)" || bad "node 22+ needed (HyperFrames)"
for t in npx ffmpeg ffprobe; do command -v $t >/dev/null 2>&1 && ok "$t" || bad "$t missing"; done

V=$(tr -d '[:space:]' < hyperframes.version 2>/dev/null)
if [ -z "$V" ]; then bad "hyperframes.version missing"
elif got=$(DO_NOT_TRACK=1 npx -y "hyperframes@$V" --version 2>/dev/null | tail -1) && [ "$got" = "$V" ]; then ok "hyperframes $V"
else bad "hyperframes@$V does not run (got: ${got:-nothing})"; fi
[ -f "$HOME/.claude/skills/hyperframes/SKILL.md" ] && ok "hyperframes skills" || bad "hyperframes skills missing: npx hyperframes@$V skills update"

VENDOR="$ROOT/vendor/video-shotcraft"
pinned=$(tr -d '[:space:]' < "$ROOT/vendor/video-shotcraft.commit" 2>/dev/null)
if [ ! -d "$VENDOR/.git" ]; then bad "vendor/video-shotcraft missing (scripts/update-shotcraft.sh --sync)"
elif [ "$(git -C "$VENDOR" rev-parse HEAD)" != "$pinned" ]; then bad "video-shotcraft not at the pinned ${pinned:0:7} (scripts/update-shotcraft.sh --sync)"
elif [ -n "$(git -C "$VENDOR" status --porcelain --untracked-files=no)" ]; then bad "vendor/video-shotcraft has local changes"
else ok "video-shotcraft at ${pinned:0:7}"; fi

BV=$(tr -d '[:space:]' < blender.version 2>/dev/null)
case "$(scripts/blender.sh -b --factory-startup --version 2>/dev/null | head -1)" in
  "Blender $BV"*) ok "blender $BV (scripts/blender.sh)" ;;
  *) warn "blender $BV missing (3D scenes in recipes/line3d/blender): see scripts/blender.sh" ;;
esac
command -v yt-dlp >/dev/null 2>&1 && ok "yt-dlp $(yt-dlp --version)" || warn "yt-dlp missing (reference downloads): uv tool install yt-dlp --with yt-dlp-ejs"
[ -x tools/tts/.venv/bin/python ] && [ "$(ls tools/tts/voices/*.onnx 2>/dev/null | wc -l)" -ge 1 ] && ok "voice (piper)" || warn "voice not set up: tools/tts/setup.sh"
for c in tools/*-capture; do
  [ -f "$c/package.json" ] || continue
  [ -d "$c/node_modules/puppeteer" ] && ok "$(basename "$c")" || warn "$(basename "$c") deps: (cd $c && npm install)"
done

exit $fail
