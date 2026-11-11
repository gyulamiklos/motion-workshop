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
- **Turning in place:** give keys `dir: [yaw, pitch]` (degrees) instead of `target`; the angles are eased, so a turn has the eased angular speed. A target lerp across a big angle speeds up and slows down in the wrong places.
- **Whip turn** (measured): a small counter-move first (≈ 0.1 s), then ≈ 0.4 s `power4.inOut`, ≈ 7 fast frames; ≈ 40–90° of yaw with ≈ 45° of roll; it lands rolled and keeps settling for ≈ 0.3 s. Lines smear on the fast frames: `stage.renderBlurred` with `shutter` ≈ 2.2 frames, 14 samples, `gain` swelling 1 → 2.2 → 1 with the turn (`1 + 1.2 sin(πk)`), so the smear stays bright and the frame never jumps in brightness at the blur window's edges.
- **Push on an impact** (measured): on the hit frame a flash (lift 0.32, half-life ≈ 4 frames) and a 0.14 s `power3.out` push toward the point with ≈ 10° of roll, then a slow settle. No blur on the push; the reference has none.
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
Built in `recipes/line3d/globe-dive.html` (`camGlobe`, `camCity`).
