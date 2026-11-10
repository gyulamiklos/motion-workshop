# Line-3D visual language: principles

A topic-free grammar for 3D-looking line animation: thin white lines in a dark, foggy space, one accent colour that marks what is alive, a camera that never stops and scene changes that are camera moves. Read this before planning any 3D or "systems" scene; build it with the blocks in `recipes/line3d/`.

Learned from a music video (local reference, see the end). We keep the grammar and the numbers, never its pictures, words or music.

## The five rules

1. **Lines, not surfaces.** Everything is drawn with 1 px lines and small outlined shapes. No shaded faces, no textures, no gradients on objects. Solid fill is reserved for the accent at the moment of an event.
2. **Depth is brightness.** Near lines are white, far lines fade into the background; the hidden side of an object is dashed and dimmer. There is no lighting model: fog and alpha do the work of light.
3. **One accent, only on what is alive.** A single saturated colour appears only where something happens now, with a bloom halo, and cools to neutral white within a tenth of a second. A frame without an event has no accent in the 3D layer.
4. **The world always moves.** In every frame something in 3D turns or travels: the object rotates, or the camera drifts, dollies or orbits. A still 3D frame reads as a frozen render.
5. **Scenes change through the camera.** The camera dives into the object and its surface becomes the next world, or turns inside a space to face a new wall. Crossfades between 3D worlds do not happen.

## Inventory (25 techniques)

Times are `m:ss.s` in the reference. The class says where the rule lives below.

| # | Technique | Time | Class |
|---|---|---|---|
| 1 | Latitude-longitude wire sphere; back hemisphere dashed and dimmer | 0:05–0:09 | primitive |
| 2 | Cell-matrix surface: land masses as tiny outlined squares on the sphere, born one region at a time | 0:06–0:09 | primitive |
| 3 | Concentric rings and a reticle around a point, collapsing to it | 0:04.9–0:05.3, 3:41 | primitive, event |
| 4 | Ground of outlined cells (blocks, a city grid) seen from above | 0:09.5–0:10, 0:18 | primitive |
| 5 | Rain column: instanced vertical streaks inside a cylinder over a disc with ripple rings | 0:34–0:38 | primitive |
| 6 | Wire trees: flat outline billboards that swivel to the camera | 0:40–0:43 | primitive |
| 7 | Perspective corridor of panels to a vanishing point | 0:46–0:48 | primitive |
| 8 | Skybox room: a box seen from inside, dust of star points on its walls, axis labels | 1:24–1:31 | primitive |
| 9 | Graph in a 3D plane: a curve with text riding along it, a limit band at the top | 1:28–1:31 | primitive |
| 10 | Instanced crowd: one outlined figure, 6 copies then thousands, fading with distance | 2:00–2:02 | primitive |
| 11 | Particle galaxy whose points turn into instanced cubes | 3:08–3:12 | primitive, event |
| 12 | Warp field: radial streaks from the centre | 3:40–3:41 | primitive |
| 13 | Floor grid with fog to the horizon, props as wire boxes and an icosphere | 1:58, 2:00 | primitive |
| 14 | Continuous turn of the hero object while the HUD works | 0:06.4–0:09.0 | camera |
| 15 | Dive: accelerate into the object, its surface cells become the next scene's grid | 0:08.95–0:09.9 | camera, transition |
| 16 | Whip turn inside a room, lines smeared along the turn | 1:26.0–1:26.4 | camera, transition |
| 17 | Pull-back reveal of scale: a handful of instances, then the camera falls back over thousands | 2:00.5–2:02 | camera |
| 18 | 1 px white lines on near-black violet, about 85 % of the frame empty | throughout | look |
| 19 | Bloom only on the accent and on single "live" points (a cursor star) | throughout | look |
| 20 | Birth pulse: a new part arrives in accent and bloom, cools to white in ~0.1 s | 0:06.9, 0:07.6, 0:08.25 | event |
| 21 | Flash frame: the whole frame lifts for one frame and decays over ~0.15 s | 0:04.88, 3:41.65 | event, transition |
| 22 | Counter tied to the event: instance counts and values tick as things appear | 2:00, 1:28–1:31 | event, HUD |
| 23 | Window hand-off: the old scene shrinks into a framed card while the next fills the screen | 0:34.9, 3:09.8 | transition |
| 24 | Log panel: lines appear one per event, the current one on an accent bar | 0:05–0:10 | HUD |
| 25 | Leader lines from a 3D point to a mono label; corner labels and readouts with units | 1:27, 3:10, throughout | HUD |

## Rules with numbers

Measured at 1920×1080, 60 fps, from pixel samples and per-frame tracking (`tools/breakdown/track.py`, frame crops). "≈" marks an estimate read off contact sheets rather than measured.

### Look
| Property | Value |
|---|---|
| Background | `#0a090c` (RGB 10, 9, 12): near-black with a violet cast; rooms and close-ups lift to `#121116` |
| Empty frame | 80–90 % of pixels stay under luma 20 in a line scene |
| Front lines | 1 px (1.5 px with antialiasing), core luma 230–255: white at 0.9–1.0 |
| Hidden side | dashed (dash ≈ 6 px, gap ≈ 6 px), alpha ≈ 0.35–0.45 |
| Fog | far lines fall to alpha ≈ 0.15–0.25; a crowd row at mid distance peaks at luma ~160 (≈ 0.6) |
| Accent | `#ff2d8c`; its bloom halo samples as `#d07087` (the accent mixed toward white) |
| Bloom | only pixels above the accent threshold glow; halo radius ≈ 20–40 px; white lines do not bloom |
| Cell surface | square outlines ≈ 8–12 px across at hero size, gap ≈ 30 % of the cell |

### Camera grammar
- **Never still.** Either the object turns (a sphere at ≈ 10–15° a second, linear) or the camera drifts. A hold is a slow move, not a stop.
- **Dive:** measured on the sphere's edge: speed 2 px per frame at the start, 10 px per frame 0.25 s later, filling the frame after ~0.5 s. Ease-in all the way through the surface (`expo.in`-like, the speed grows ~5× in a quarter second), then the new world decelerates to its drift in ~0.4 s (`expo.out`). Total ≈ 0.9 s. The cells of the surface are the cells of the next scene: no cut, no fade.
- **Whip turn:** ≈ 0.4 s, ≈ 45–90° about the vertical, `power3.inOut`, lines smeared along the turn on the fastest 2–3 frames.
- **Dolly and drift:** slow pushes of ≈ 2–4 % scale a second between events; orbit at 3–5° a second when the subject is a stage.
- **Reveal of scale:** start on a handful of instances, framed close; the count jumps (6 → hundreds → thousands) as the camera falls back and down in ≈ 1.5 s.

### Event grammar
- **Birth pulse** (measured three times, same shape each time): attack 3–4 frames (0.05–0.07 s) to full accent; decay to neutral in 5–6 frames (≈ 0.1 s), roughly exponential with a half-life of ~1.5 frames. The part stays afterwards, in white. Events land on the beat: here every ≈ 0.65 s.
- **Flash frame** (measured twice, identical): mean luma jumps by ≈ +50 (on 0–255) in one frame and decays with a half-life of ~3 frames, back to base in ≈ 0.15–0.2 s. Use it once per big moment (a start, an ending, a "boot").
- **One event at a time.** Pulses do not overlap; the next starts after the previous has cooled.
- **Tie a number to it.** A counter, a log line or a label changes on the same frame as the pulse.

### Transitions (in order of preference)
1. **Dive into the object** (rule above): the hero object's own structure becomes the next scene.
2. **Turn inside a space:** the camera whips to a new wall, which carries the next content.
3. **Collapse to a point, flash, expand:** rings collapse into a point, a flash frame, the next scene grows out of it.
4. **Window hand-off:** the old scene shrinks into a framed card (≈ 30 % of the frame) while the next fills the screen.
Hard cuts between 3D worlds only on a strong beat, and never more than one in three seams.

### HUD
- Mono, small: 11–14 px caps or lowercase, white at 0.5–0.7, letter-spacing +0.05 em; numbers tabular.
- Corner blocks (top-left title, top-right status, bottom readouts) inside the 90 % action-safe box; thin 1 px brackets.
- Leader lines: 1 px, from a projected 3D point to a label, the label following the point every frame.
- A log panel gains one line per event; the newest sits on an accent bar that moves down with it.
- The HUD never moves with the camera; the 3D world does.

## How to build a scene from this

1. **Pick one hero object** that is the topic's metaphor (a sphere for "the world", a column for "a stream", a crowd for "users", a grid of cells for "storage"). One hero per scene.
2. **Write the beats** as events: each one a part of the hero being born (birth pulse), with a HUD line or a counter for it. 3–6 events per scene, on a steady beat.
3. **Keep the world turning** between events; decide the drift before the events.
4. **End by entering the hero** (dive) or by turning to the next space; the last frame of a scene is mid-move.
5. **Add the HUD last**, sparse: a title block, one live readout, a log or leader labels, not all of them.

## Pitfalls
- Too many lines: past ~20 % lit pixels the frame turns grey and depth disappears. Fog harder or remove geometry.
- Accent on static things (titles, borders) dilutes it; the eye stops reading it as "now".
- Bloom on white lines makes everything soft; threshold it to the accent and to the brightest points.
- Thick lines (3 px and up) read as UI, not as a 3D world; keep 1 px and use alpha for hierarchy.
- A camera that stops for the text kills the space. Text lands still in the HUD layer; the world keeps moving under it.

## Reference
`research/simulation-ending/` (local, never committed): `source.mp4`, measurement in `bd2/` (`range-*.jpg` sheets, `motion.csv`). Pixel samples at 0:07.6, 0:08.0, 1:26.0, 2:01.5, 3:09.0, 3:42.5; pulse and dive tracking over 0:06.0–0:09.95; flash frames at 0:04.88 and 3:41.65.
