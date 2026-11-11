# HUD export: where the 3D points are on screen

`stage.project(p3)`, the `anchors(t)` function given to `run()`, `proj.json`.

**Use when:** text, labels or counters in HTML must stick to things in the Blender video.

## Intent
Blender renders the picture, HTML sets the type. The scene says where each anchor is per frame; the composition reads that and places the DOM.

## Motion core
- `anchors(t)` returns a dict per frame, e.g. `{"faces": [project(p) for p in HERO_X], "count": n}`; `project` gives `[x px, y px, in front 0/1]` in 1920×1080.
- A full run writes `DIR/proj.json`: `{fps, duration, frames: [...]}`. `--proj-only` writes just that.
- The HUD composite is built from the rendered video and `proj.json` by `scripts/blender-block.sh <scene.py> <hud.json>` (template `templates/blender-hud/block.html`; the video, `proj.json` and the block folder stay under `renders/`, untracked). A scene's HUD is its `<scene>.hud.json`: `status` text with `{field}` tokens from `proj.json`, `head` words on beats, `labels` that follow an anchor (see `recipes/line3d/blender/crowd.hud.json`).
- `--dir DIR` reuses frames already rendered there; `--render` forces a new render.

## Pitfalls
- Anchors are evaluated after `pose(t)`; they follow the camera drift and shake.
- A scene without anchors still gets a `proj.json` (empty dicts), so its block needs only `head` text.
