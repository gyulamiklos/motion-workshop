# Line look and bloom: white lines, one accent that glows

Every object is 1 px white lines on near-black violet, faded by depth fog, its far side dashed; only the accent and single "live" points bloom.

**Use when:** always in a line-3D scene: it is the material, not an effect.

**Duration and energy:** static look. Its energy comes from how much of the frame is lit (keep 80–90 % dark).

## Intent
Principles 1–3: lines instead of surfaces, depth as brightness, one accent on what is alive. With no lighting model, fog and alpha carry the depth, and the bloom tells the eye where "now" is.

## Motion core
- **Stage:** `K.createStage(canvas, { look: { accent } })`. Two renders a frame: the scene, then a glow pass where each material writes only its accent share and `glow`, blurred at half size in three widening passes and added on top. Then the flash lift.
- **Material:** `K.lines(stage, geo, { alpha, glow, hold, draw, hidden })`; drive it in `draw(t)` with `obj.set({ alpha, draw, pulse, hold, glow })`.
- **Back side:** builders that give normals (sphere, sphere cells) dash the side facing away (dash ≈ 6 px, alpha 0.4).
- **Hidden lines** (solid objects such as towers or boxes): `K.occluder(stage, boxes)` writes depth only; lines test depth but never write it; `lines(..., { hidden: true })` adds a second pass for the occluded parts, dashed and at the back alpha. `cellGrid` returns its `boxes` for this. Lines without `hidden` simply vanish behind an occluder.
- **Colours:** use `K.color(css)` for any colour you pass to a shader. The stage writes linear output with no conversion, so `#0a090c` lands as RGB 10, 9, 12. `new THREE.Color("#0a090c")` converts sRGB to linear and came out as 1, 1, 1 (and the accent as `#ff0741`).

## Parameters (principles, measured)
| Parameter | Value | Push up | Push down |
|---|---|---|---|
| background | `#0a090c` | rooms lift to `#121116` | pure black: loses the violet cast |
| line alpha | 0.92 | – | under 0.6 for hero lines: grey, no depth range left |
| back / hidden alpha | 0.4 | the back competes with the front | under 0.25: the solid reads as a flat outline |
| fog (near, far, min) | globe 2.6–6.5, 0.3; city 5–22, 0.14 | far lines as bright as near ones: no depth | min under 0.1: the horizon disappears |
| `glow` on white | 0–0.1 | everything soft | – |
| bloom strength | 1.35 | neon smear | under 0.8: the accent stops reading as light |

## Pitfalls
- Over ~20 % lit pixels the frame turns grey: fog harder or remove geometry (a 81 × 81 city with towers sits close to that).
- Accent on static things dilutes it: titles and borders stay white.
- Points also test depth now, so a star field behind an occluder is hidden like a line.

## Reference
Pixel samples at 0:07.6, 0:08.0, 1:26.0, 2:01.5, 3:09.0, 3:42.5 (principles, "Look"). Kit: `createStage`, `lineMaterial`, `lines`, `occluder`, `color`.
