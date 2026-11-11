# Line-3D kit

A small Three.js kit for the line-3D visual language (`recipes/_principles.md`): thin white lines in a dark, foggy space, one accent that blooms on what is alive, a camera that never stops. One ES module, `assets/line3d.js`, Three.js r184 from a pinned CDN URL.

Read the principles first, then the card of each element you use.

## Cards
| Card | Element |
|---|---|
| `cards/look-and-bloom.md` | the stage, line material, fog, back side, hidden lines, colours, bloom |
| `cards/camera-rig.md` | keyed camera with drift |
| `cards/dive.md` | the dive into a surface and the hand-over to the next world |
| `cards/pulse-and-flash.md` | birth pulse, flash frame, one event at a time |
| `cards/primitives.md` | geometry builders and point clouds, which are used and which are not yet |
| `cards/hud.md` | corners, log, leader labels, live readouts |

## Blocks
| Block | What | Length |
|---|---|---|
| `globe-dive.html` | a wire globe boots, four regions are born on the beat, the camera dives into one and lands in a city that rises | 6.6 s |
| `skybox-room.html` | inside a room with dust on its walls, a whip turn to a corner where nodes are born, a turn back to a wall graph whose curve carries text up to a limit band; flash and push on the hit | 8.6 s |

Render one: `scripts/render-block.sh recipes/line3d/<block>.html [out.mp4]`.

## Scene skeleton
A scene is a pure function of time: build everything once, then `draw(t)` sets uniforms and the camera from `t` alone and renders. HyperFrames seeks a paused GSAP timeline; a driver tween calls `draw` on every seek.

```html
<canvas id="gl" width="1920" height="1080" data-layout-allow-overflow></canvas>
<script>
  window.__hf = window.__hf || {}; window.__hf.buildReady = window.__hf.buildReady || {};
  window.__hf.buildReady["my-scene"] = new Promise((res) => (window.__ready = res));
</script>
<script type="module">
  import * as K from "./assets/line3d.js";
  const { THREE } = K;
  const stage = K.createStage(document.getElementById("gl"), { look: { accent: "#ff2d8c" } });
  const hero = stage.add(K.lines(stage, K.sphereLatLong({ lat: 12, lon: 18 })));
  const cam = K.cameraRig([{ t: 0, pos: [0, 0.2, 3.2], target: [0, 0, 0] }, { t: 4, pos: [-0.4, 0.3, 3.0], target: [0, 0, 0], ease: "sine.inOut" }], { drift: 0.035 });
  function draw(t) {
    hero.rotation.y = 0.2 * t;                                   // the world always moves
    hero.set({ draw: K.span(t, 0.4, 1.1, "power2.out"), pulse: K.pulse(t, 2.0) });
    stage.setCamera(cam(t));
    stage.render();
  }
  const driver = { _t: 0 };
  Object.defineProperty(driver, "t", { get() { return this._t; }, set(v) { this._t = v; draw(v); } });
  const tl = gsap.timeline({ paused: true });
  tl.fromTo(driver, { t: 0 }, { t: 6, duration: 6, ease: "none", immediateRender: false }, 0);
  (window.__timelines = window.__timelines || {})["my-scene"] = tl;
  draw(0);
  await stage.renderer.compileAsync(stage.scene, stage.camera);
  window.__ready();
</script>
```

## API
**Numbers:** `LOOK` (colours, alphas, fog, bloom), `PULSE` (`attack`, `half`), `FLASH` (`lift`, `half`): the measured defaults.

**Time:** `span(t, t0, dur, ease?)` → 0..1 · `pulse(t, t0, { attack, half })` · `flash(t, t0, { lift, half })` · `ease(name)` (GSAP ease by name) · `drift(seed)` → smooth −1..1 · `lerp`, `clamp01`, `mulberry32(seed)`.

**Colour:** `color(css)` → a `THREE.Color` that lands in the frame as written. Use it for anything you pass to a shader.

**Stage:** `createStage(canvas, { width, height, look })` → `stage` with `add(obj)`, `setCamera({ pos, target, fov, roll | up })`, `project(v)` → `{ x, y, visible }` in pixels, `render()`, and the writable `flash`, `bloomStrength`, `shared.uFog.value.set(near, far, min)`.

**Camera:** `cameraRig(keys, { drift, seed })` → `at(t)` (a new sample each call; keys take `target` or `dir: [yaw, pitch]` in degrees) · `dive(k, from, p, n, up, endHeight, { swing, push, ease })`.

**Motion blur:** `stage.renderBlurred(t, pose, { shutter, samples, gain })` renders `pose(tt)` at each `shutterTimes(t, shutter, samples)` and averages; `pose` sets the scene without rendering. `gain` brightens only what is above the background.

**Lines:** `lines(stage, geo, { alpha, glow, hold, draw, back, dash, color, facing, hidden })` → `LineSegments` with `set({ alpha, draw, pulse, hold, glow })` · `occluder(stage, boxes)` → a depth-only mesh · `lineMaterial(stage, opts)`.

**Builders** (line geometry): `sphereLatLong`, `ring`, `sphereCells`, `cellCentre`, `blobRegions`, `gridFloor`, `cellGrid` (+ `boxes`), `box`, `wallGrid`, `path`, `hatch`, `tunnel`, `instances`, `figure`, `warp`. **Points:** `points(stage, positions, opts)`, `scatter(n, { kind: "box" | "shell" | "walls" | "galaxy" })`. **Text:** `textPath(stage, text, curve, opts)` → group with `paint(head, { ahead, window })`. Details in `cards/primitives.md`.

## Blender scenes
For a hero scene that needs real light, the kit's look is also built in Blender (Eevee): haze lit by the accent
points, motion blur on every frame, bloom above 1.0 only. Same beats and camera keys as the HTML block; the HUD stays
in HTML on top of the rendered video, and the script writes `proj.json`, the screen position of each HUD anchor per frame.

| Script | What |
|---|---|
| `blender/skybox_room.py` | the skybox room of `skybox-room.html` (516 frames, ~0.4 s a frame on the NVIDIA GPU) |

```bash
scripts/blender.sh -b --factory-startup -P recipes/line3d/blender/skybox_room.py -- --out DIR            # frames + proj.json
scripts/blender.sh -b --factory-startup -P recipes/line3d/blender/skybox_room.py -- --out DIR --pick 30,200   # a few frames
scripts/blender.sh --factory-startup -P recipes/line3d/blender/skybox_room.py -- --out DIR --open        # look around in the window
```
The shared parts (stage, eases and camera rig, materials, lines, point clouds, text on a path, the run loop) are in
`recipes/blender/kit.py`; a scene script is the world, `pose(t)` and its HUD anchors.
`scripts/blender.sh` runs the pinned version (`blender.version`) on the NVIDIA GPU; on the integrated GPU a frame took ~12× longer.
The text on the curve uses Lato Black from the system fonts (OFL).

## Tests
Kit logic that runs without a GPU (camera rig, colours, occluder geometry, shutter times, builders):

```bash
node --import ./recipes/line3d/test/register.mjs --test recipes/line3d/test/*.test.mjs
```

The loader fetches the pinned Three.js once into `~/.cache/motion-workshop/https/`. What a test cannot see (the picture) is checked with a range sheet next to the reference (`tools/breakdown/breakdown.sh <render> <dir> --range A-B`).
