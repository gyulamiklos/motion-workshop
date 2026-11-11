#!/usr/bin/env bash
# Run the pinned Blender (blender.version) on the NVIDIA GPU. On a hybrid laptop Blender would otherwise render on the
# integrated GPU: Eevee on the Intel iGPU took 4.7 s a frame, on the NVIDIA 0.4 s, with the same picture.
# Usage: scripts/blender.sh [blender args...]
#   scripts/blender.sh -b --factory-startup -P recipes/line3d/blender/skybox_room.py -- --out DIR    render
#   scripts/blender.sh --factory-startup -P recipes/line3d/blender/skybox_room.py -- --out DIR --open look around
# Install: the linux-x64 tarball from a blender.org mirror, unpacked into ~/.local/opt (or set BLENDER=/path/to/blender).
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
V=$(tr -d '[:space:]' < "$ROOT/blender.version")
BIN=${BLENDER:-$HOME/.local/opt/blender-$V-linux-x64/blender}
[ -x "$BIN" ] || { echo "blender $V not found at $BIN (see scripts/blender.sh)" >&2; exit 1; }
NV=/usr/share/glvnd/egl_vendor.d/10_nvidia.json
if [ -f "$NV" ] && [ -z "${BLENDER_IGPU:-}" ]; then
  export __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia __EGL_VENDOR_LIBRARY_FILENAMES=$NV
fi
exec "$BIN" "$@"
