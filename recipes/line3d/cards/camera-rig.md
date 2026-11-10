# Camera rig: keyed moves that never stop

A camera path as a few keys (`pos`, `target`, `fov`, `roll`) with an ease per move and a seeded drift on top, so the world is never still, even on a hold.

**Use when:** any line-3D scene. Each scene has one rig; a scene change through a dive or a whip gets a second rig for the new world.

**Duration and energy:** a key every 1–3 s. The drift keeps a hold alive at almost no energy; the moves between keys carry the scene's energy.

## Intent
Principle 4 (the world always moves): a 3D frame that stops reads as a frozen render. The keys say where the camera goes, the drift says it is a camera. The HUD stays still above it, so the eye has a calm layer to read.

## Motion core
- **Keys:** `K.cameraRig([{ t, pos, target, fov?, roll?, ease? }], { drift, seed })` returns `at(t)`. The ease of a key shapes the move that arrives at it (`expo.out` for a landing after a fast move, `sine.inOut` for a slow push, `power2.inOut` default).
- **Drift:** a seeded sum of three sines (≈ 0.2–0.7 Hz), amplitude `drift` in world units on position, 40 % of it on the target. Globe scale (radius 1): 0.03–0.04. City scale (one cell = 1): 0.05–0.08.
- **Push and orbit between events** (principles): 2–4 % scale a second, or 3–5° a second around a stage.
- **Hold = slow move:** the last key is held plus drift, so end a scene on a key the camera is still easing into.

## Parameters
| Parameter | Value | Push up | Push down |
|---|---|---|---|
| `drift` | 0.035 (unit sphere) | over 0.08: handheld, nervous | 0: frozen frames on every hold |
| key spacing | 1–3 s | slow, documentary | under 0.6 s: every move is a jolt |
| `fov` | 40 | wider (50+): distorted edges, the object shrinks | under 30: flat, depth disappears |

## Pitfalls
- **A rig sample is a new object every call** (fixed in the kit, see B1): blending two samples (`at(t)` with `at(later)`) is safe. A version that reused one output object froze the camera for 0.55 s and then jumped.
- Lerp the `up` vector only across an orientation change you can see (top-down to oblique); a lerped `up` on a level camera tilts the horizon.
- The camera passing through a line object fills the frame with grey: keep the near plane and the path clear of geometry, or fade the object.

## Reference
`research/simulation-ending/` 0:06.4–0:09.0 (turn while the HUD works). Built in `recipes/line3d/globe-dive.html` (`camGlobe`, `camCity`).
