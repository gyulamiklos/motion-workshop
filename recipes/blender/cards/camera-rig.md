# Camera rig (Blender): keyed moves, eased angles, a drift

`kit.camera_rig(keys, amp, seed)` returns `at(t) -> (pos, target, fov, roll)`; feed it to `stage.set_camera(...)`.

**Use when:** every scene. Same keys as the Three.js rig (`recipes/line3d/cards/camera-rig.md`), so a block moves to Blender with its keys intact.

**Duration and energy:** a key every 1–3 s. The move between keys carries the energy; the drift keeps holds alive.

## Intent
Principle 4 (the world always moves). The camera never stops, and never stops and restarts: one slow move through a beat reads as filmed, two eased moves back to back read as a glitch.

## Motion core
- Keys `{t, pos, dir: [yaw, pitch], fov, roll?, ease?}` in Three.js coordinates; yaw 0 looks down −Z, positive turns left. The ease of a key shapes the move that arrives at it.
- Angles are eased, not the target point: a whip turns at the eased angular speed.
- `amp` is a seeded drift in world units (0.02–0.03 at metre scale).
- Add a hit shake in `pose`: `exp(-(t - T) * 7) * 0.045 * sin(61 t)` on position and half on target (collapse scene).

## Parameters
| Parameter | Value | Push up | Push down |
|---|---|---|---|
| `amp` | 0.02–0.03 | handheld | frozen holds |
| `fov` | 38–46 | wide, distorted | flat |

## Pitfalls
- Two segments that meet at rest and move on, or that reverse direction, read as the camera hesitating (the first crowd rig did this: it stopped at 3.45 s and crept back). Use one key to the end with `sine.inOut`.
- A camera that passes through geometry fills the frame; keep the path clear.
