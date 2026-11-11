# HUD export: where the 3D points are on screen

`stage.project(p3)`, the `anchors(t)` function given to `run()`, `proj.json`.

**Use when:** text, labels or counters in HTML must stick to things in the Blender video.

## Intent
Blender renders the picture, HTML sets the type. The scene says where each anchor is per frame; the composition reads that and places the DOM.

## Motion core
- `anchors(t)` returns a dict per frame, e.g. `{"faces": [project(p) for p in HERO_X], "count": n}`; `project` gives `[x px, y px, in front 0/1]` in 1920×1080.
- A full run writes `DIR/proj.json`: `{fps, duration, frames: [...]}`. `--proj-only` writes just that.
- The HUD composite (video + HTML) is built from the rendered video and `proj.json`; the rendered video is not in git.

## Pitfalls
- Anchors are evaluated after `pose(t)`; they follow the camera drift and shake.
- The composite HTMLs still live under `renders/blocks/*-blender/block/`, untracked. How they become real blocks is open.
