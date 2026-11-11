# Blender kit

The shared parts of the workshop's Blender scenes (`kit.py`, Eevee, run through `scripts/blender.sh`). A scene script
builds its world once, then `pose(t)` sets everything from `t` alone; `kit.run()` hooks it into the frame-change handler
(so motion-blur sub-frames see the true pose), writes the HUD anchors and renders. Every technique below is its own
piece with its own card: a film uses the ones it needs and none of the others.

## Which engine
The film starts with the cheapest tier that is enough (`docs/decisions.md`, 2026-11-11).

| Tier | Use for | Cost |
|---|---|---|
| 1. HTML + GSAP | text, UI, data, product footage, most films | seconds |
| 2. Three.js kit (`recipes/line3d/`) | quick wire 3D, no real light | a minute |
| 3. Blender (this kit) | a hero 3D scene that lives on light, haze, a crowd, real motion blur or physics | ~0.4 s a frame on the NVIDIA GPU |

A Blender scene is a video inside the HyperFrames composition; text and HUD stay in HTML on top, placed from `proj.json`. `scripts/blender-block.sh <scene.py> <scene.hud.json>` builds that block from `templates/blender-hud/`.

## Cards
| Card | Piece | Technique it gives |
|---|---|---|
| `cards/stage-and-run.md` | `args`, `Stage`, `run` | the empty Eevee scene, bloom, motion blur, picking frames, the window |
| `cards/camera-rig.md` | `camera_rig` | keyed moves with eased angles and a seeded drift |
| `cards/materials-and-fog.md` | `emit`, `haze`, `point_light` | colour-and-brightness emission with distance fog, lit haze |
| `cards/lines-points-text.md` | `poly`, `point_cloud`, `text_on_path` | draw-on lines, dust, words bent onto a curve |
| `cards/sdf-shape.md` | `sd_*`, `shape_mesh` | a smooth filled silhouette with an outline ribbon |
| `cards/instancer.md` | `instancer`, `set_time` | thousands of copies of a few meshes, born over time |
| `cards/scanline.md` | `scanline` | the striped-silhouette material with birth pulse and accent fill |
| `cards/physics.md` | `fracture`, `rigid*`, `hold_until`, `burst`, `simulate` | shatter, fall and pile up, cached and deterministic |
| `cards/hud-export.md` | `Stage.project`, anchors, `proj.json` | where the 3D points are on screen, per frame |

Scenes (`recipes/line3d/blender/`): `skybox_room.py`, `crowd.py`, `collapse.py`. Read `recipes/_principles.md` for the look.

## Run
```bash
scripts/blender.sh -b --factory-startup -P <scene>.py -- --out DIR                 # frames + proj.json
scripts/blender.sh -b --factory-startup -P <scene>.py -- --out DIR --pick 30,200   # a few frames, to look
scripts/blender.sh --factory-startup -P <scene>.py -- --out DIR --open             # the window, timeline live
ffmpeg -framerate 60 -i DIR/frames/f_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 16 out.mp4
```
Always through `scripts/blender.sh`: it pins the version (`blender.version`) and runs on the NVIDIA GPU. On the hybrid
laptop a plain headless run lands on the Intel GPU, 12× slower, and nothing says so.

## Blender 5.x pitfalls (each cost a round)
- Curve `bevel_factor_mapping_end` is `SPLINE`, not `LENGTH`.
- The compositor is `scene.compositing_node_group` (a node group) with a `NodeGroupOutput`; there is no `scene.node_tree`.
- A Geometry Nodes input is set as `mod.properties.inputs.<socket identifier>.value`, not `mod["Socket_2"]`.
- A headless `frame_set()` loop does not fill the rigid-body cache; `bpy.ops.ptcache.bake_all` does (`kit.simulate`).
- Hide by scale (or `hide_render`), not by alpha 0: an alpha-0 emission is black and still hides what is behind it.
- After a text replace, `grep` the replaced name; Python `replace` and `sed` have silently missed one.
