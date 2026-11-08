#!/usr/bin/env bash
# Keeps vendor/video-shotcraft at the commit pinned in vendor/video-shotcraft.commit.
# Usage:
#   scripts/update-shotcraft.sh          show what upstream has added since the pin (read only)
#   scripts/update-shotcraft.sh --apply  move the pin to upstream main; commit the .commit file afterwards
#   scripts/update-shotcraft.sh --sync   put the clone on the pinned commit (clones it first if missing)
set -eu
cd "$(dirname "$0")/.."
VENDOR=vendor/video-shotcraft
PIN=vendor/video-shotcraft.commit
URL=https://github.com/Vincentwei1021/video-shotcraft.git
pinned=$(tr -d '[:space:]' < "$PIN")
mode=${1:-}

if [ "$mode" = "--sync" ]; then
  [ -d "$VENDOR/.git" ] || git clone -q --filter=blob:none "$URL" "$VENDOR"
  git -C "$VENDOR" fetch -q origin
  git -C "$VENDOR" checkout -q main
  git -C "$VENDOR" reset -q --keep "$pinned"
  echo "vendor at ${pinned:0:7}"
  exit 0
fi

git -C "$VENDOR" fetch -q origin
echo "Upstream since the pin (${pinned:0:7}):"
git -C "$VENDOR" log --oneline --no-decorate "$pinned..origin/main" | head -40
count=$(git -C "$VENDOR" rev-list --count "$pinned..origin/main")
[ "$count" -eq 0 ] && { echo "(nothing new)"; exit 0; }

if [ "$mode" = "--apply" ]; then
  lock_changed=$(git -C "$VENDOR" diff --name-only "$pinned" origin/main -- template/package-lock.json)
  git -C "$VENDOR" merge -q --ff-only origin/main
  git -C "$VENDOR" rev-parse HEAD > "$PIN"
  echo "Pin moved to $(git -C "$VENDOR" rev-parse --short HEAD). Commit $PIN."
  [ -n "$lock_changed" ] && echo "template/package-lock.json changed: run npm ci in $VENDOR/template."
else
  echo "$count new commits. Read the changes, then: scripts/update-shotcraft.sh --apply"
fi
