# Physics: shatter, fall and pile up

`kit.wire_solid`, `fracture(me, n, seed)`, `rigid_world`, `rigid`, `hold_until`, `burst`, `simulate`. Scene: `recipes/line3d/blender/collapse.py`.

**Use when:** a beat where things give way (a collapse, a shatter, a drop); anything that must fall like it weighs something.

**Duration and energy:** ~0.3 s ripple of release, 0.13 s burst, settled in ~1.5 s at gravity 14 (a film's 9.81 reads floaty at this scale).

## Intent
Real rigid bodies give the weight a keyframed fall cannot. The sim is baked once, so every frame, pick or range render sees the same fall.

## Motion core
- **Solids:** meshes in Blender coordinates, already placed. `wire_solid` draws a mesh as its edges (wireframe modifier) with an emit material.
- **Fracture:** `fracture(me, n, seed)` cuts a convex mesh into about `n` Voronoi cells with bisect planes and caps them; each piece is recentred and shrunk 1.5 % so wires do not fight. Show the intact braced solid first; swap to the cells on the break (hide the intact with `hide_render`, cells appear).
- **Stand then fall:** `hold_until(ob, frame)` keeps a body kinematic until `frame`, then dynamic. Stagger the frames by distance from an impact point (0.32 s over 3 m) so the break ripples.
- **Kick:** `burst(stage, loc, frame, strength, length=8, reach=4.5)` is a radial force field for a few frames. Strength 14 with masses ~0.2–2 spreads the pile; 160 threw pieces 60 m up.
- **Shards:** tetrahedra on collision layer 1 (`rigid(..., layer=1)`) pass through the pieces (layer 0) and collide with the ground (both): they fly out of the pile instead of fighting it. Hidden until the break.
- **Bake:** `simulate(stage, nfr)` before `run()`.

## Parameters
| Parameter | Value | Push up | Push down |
|---|---|---|---|
| gravity | 14 | heavier, snappier | floaty |
| burst strength | 14 | pieces scatter wide | a slump |
| cells per solid | 10–22 | finer rubble, slower bake | big chunks |

## Pitfalls
- Convex only: `fracture` assumes a convex source (box, icosphere). A concave object needs to be built from convex parts.
- `frame_set()` in a loop does not fill the cache headless; use `simulate` (bake).
- The sim restarts from frame 0 on every run: seeded randomness only, no wall-clock anything.
- A thin box (the panel) fractures into slivers whose wires may barely read (not checked in the render); make it thicker or fracture fewer pieces.
