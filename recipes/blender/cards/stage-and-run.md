# Stage and run: an empty Eevee scene and the frame loop

`kit.args()`, `kit.Stage(...)`, `kit.run(stage, args, duration, pose, anchors)`: everything a scene needs before it has content.

**Use when:** every Blender scene.

**Duration and energy:** none; it is the frame. Cost is the scene's: 0.4 s a frame for the room, 0.6 s for the crowd at 16 samples.

## Intent
A scene is a pure function of time. `pose(t)` sets camera, colours and clocks from `t` alone, so a single frame (`--pick`),
a range (`--frames A-B`) and the full run agree, and motion blur sees the true pose at every sub-frame.

## Motion core
- `Stage(background, samples, shutter, bloom, bloom_threshold, bloom_size, volumetric_end)`: 1920×1080 at 60 fps, flat world colour, Standard view transform, bloom only above `bloom_threshold` (1.0), so white lines (emission 1) stay crisp and accent (> 1) glows.
- `shutter` is the motion-blur share of a frame (0.5 = 180°, 0 = off). A whip or a fall smears, a hold stays sharp.
- `stage.background(lift)` lifts the world toward grey for a flash frame (pair it with `kit.flash`).
- `run()`: `--out DIR` (frames in `DIR/frames/f_NNNN.png`), `--pick 30,126` (single frames `pick_NNNN.png`), `--frames A-B`, `--samples N`, `--proj-only`, `--open`. A full run first writes `proj.json`.
- Scene extras: `kit.args({"seed": 9})` adds `--seed` (and any key) with that default.

## Parameters
| Parameter | Value | Push up | Push down |
|---|---|---|---|
| `samples` | 16 to look, 32 to render | smoother haze, slower | grainy volumes |
| `bloom` | 0.7–0.9 | soft, dreamy | lines read as plain |
| `shutter` | 0.5 | smeared | 0: crisp, strobing on fast moves |

## Pitfalls
- Look with `--pick` and a contact sheet (`ffmpeg ... -vf "scale=640:-1,tile=3x3"`) before a full render; a pick is ~1 s.
- `--open` leaves the window on the timeline; physics scenes bake first, so they open slower.
