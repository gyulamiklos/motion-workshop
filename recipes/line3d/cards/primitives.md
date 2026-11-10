# Primitives: the hero objects

Geometry builders that return line segments with a draw-on order, plus point clouds: the shapes a line-3D scene is made of.

**Use when:** picking the hero object for a topic (principles, "How to build a scene"): a sphere for the world, cells for storage or a city, a column for a stream, a crowd for users, a corridor for a pipeline.

**Duration and energy:** a primitive draws on over 0.1–1.1 s (`draw` 0 → 1), then lives on pulses and camera moves.

## Intent
One hero per scene, made of few lines. Each builder knows its own draw-on order (`t` per vertex), so "being born" is one uniform, and the same structure can carry the next scene (sphere cells → city grid).

## The builders
All line builders return `{ positions, normals?, t, dist }` (segment pairs); pass them to `K.lines(stage, geo, opts)`.

| Builder | Shape | Draw-on order | Status |
|---|---|---|---|
| `sphereLatLong({ radius, lat, lon })` | wire globe, back side dashed | latitudes from the equator out, then meridians | used (pilot) |
| `ring({ radius })` | circle in XY | around | used (pilot rings) |
| `sphereCells({ cell, gap, mask, order })` | outlined squares on a sphere; cell centres on a fixed lat/lon grid | `order(lat, lon)` (e.g. distance from a region's centre) | used |
| `blobRegions({ seed, count, size, centres })` | seeded fictional land masses: `mask`, `dist`, `point` | – | used |
| `cellCentre(lat, lon, cell)` | the nearest `sphereCells` centre (dive target) | – | used |
| `cellGrid({ cols, rows, cell, gap, keep, height, base })` | outlined cells on XZ, extruded into wire boxes; returns `boxes` for `occluder` | by distance from the centre | used (city) |
| `gridFloor({ size, div })` | floor grid | from the centre out | used |
| `box({ w, h, d })` | wire box (a room seen from inside) | edge by edge | not yet |
| `tunnel({ rings, step, sides })` | corridor to a vanishing point | from the mouth in | not yet |
| `instances(geo, [{ p, s, ry, t }])` | copies of one builder output in one draw call | per copy `t` | not yet |
| `figure({ stripes })` | outlined standing figure, 1 unit tall | head, then body | not yet |
| `warp({ count, radius, depth })` | radial streaks along -Z | random | used (pilot sparks) |
| `points(stage, positions, { sizes, births, glow })` + `scatter(n, { kind: "box" \| "shell" \| "galaxy" })` | dust, star shells, a galaxy | per point `birth` | used (seed point) |
| `textPath(stage, text, curve, { font, size })` | glyph sprites along a 3D curve | `update(progress)` | not yet |

## Motion core
- **What is born faces the camera.** A part that appears on the far side or at a graze is wasted: choose its position in view space at its birth time and subtract the object's spin (`lon = lonView - SPIN * tBirth`). Region 04 is also the dive target, so it faces the camera at the dive.
- **Draw-on fast, then pulse:** `draw` over ≈ 0.12 s on the event, `pulse` on the same `t0`; slow draw-ons (0.5–1.1 s) only for the opening structure (graticule).
- **Solid things grow, they do not pop edge by edge:** towers rise by `scale.y` (`expo.out`, 0.45 s) with their occluder in the same group.
- **Seeded, deterministic:** `seed` everywhere (`mulberry32`); nothing reads the clock or `Math.random`.

## Pitfalls
- A cell or grid of 81 × 81 with towers is ≈ 30 k segments: fine for rendering, but fog it so the horizon does not turn into a grey band.
- `sphereCells` cells are equal in angle, so they narrow toward the poles; keep regions under ±60° latitude.
- Instanced copies share `dist`, so dashes line up across copies; give a crowd a little scale jitter.

## Reference
Inventory rows 1–13 in `recipes/_principles.md`. Kit: "geometry builders" and "points" sections of `assets/line3d.js`.
