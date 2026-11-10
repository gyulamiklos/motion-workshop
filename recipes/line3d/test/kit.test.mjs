// Kit logic that runs without a GPU. Run: node --import ./recipes/line3d/test/register.mjs --test recipes/line3d/test/
import { test } from "node:test";
import assert from "node:assert/strict";

globalThis.window = globalThis.window || {};
const K = await import("../assets/line3d.js");

test("cameraRig samples are independent: a second call does not overwrite the first", () => {
  const rig = K.cameraRig([
    { t: 0, pos: [0, 0, 0], target: [0, 0, -1] },
    { t: 1, pos: [10, 0, 0], target: [10, 0, -1], ease: "none" },
  ]);
  const a = rig(0.25);
  const b = rig(1);
  assert.equal(a.pos.x, 2.5);
  assert.equal(b.pos.x, 10);
  assert.notEqual(a, b);
});

test("cellGrid reports one occluder box per extruded cell, sized like its outline", () => {
  const g = K.cellGrid({ cols: 3, rows: 2, cell: 1, gap: 0.5, height: (i, j) => (i === 1 && j === 0 ? 2 : 0) });
  assert.equal(g.boxes.length, 1);
  assert.deepEqual(g.boxes[0], { x: 0, z: -0.5, w: 0.5, d: 0.5, h: 2 });
  const m = K.occluder({}, g.boxes);
  assert.equal(m.geometry.index.count, 36);
  assert.equal(m.material.colorWrite, false);
});

test("look colours reach the frame as written: hex in, the same bytes out (no sRGB-to-linear conversion)", () => {
  const c = K.color("#0a090c");
  assert.deepEqual([c.r, c.g, c.b].map((v) => Math.round(v * 255)), [10, 9, 12]);
  const a = K.color("#ff2d8c");
  assert.deepEqual([a.r, a.g, a.b].map((v) => Math.round(v * 255)), [255, 45, 140]);
});

test("shutterTimes spreads samples evenly over the shutter, ending inside the frame at t", () => {
  const ts = K.shutterTimes(1, 0.1, 4);
  assert.equal(ts.length, 4);
  ts.forEach((v, i) => assert.ok(Math.abs(v - (0.9 + 0.025 * (i + 0.5))) < 1e-9, `sample ${i}: ${v}`));
  assert.ok(ts.at(-1) < 1 && ts[0] > 0.9);
});

test("path draws on by arc length", () => {
  const g = K.path([[0, 0, 0], [1, 0, 0], [1, 3, 0]]);
  assert.deepEqual(g.t, [0, 0.25, 0.25, 1]);
});

test("hatch stays inside its rectangle", () => {
  const g = K.hatch({ w: 2, h: 0.5, step: 0.1 });
  for (let i = 0; i < g.positions.length; i += 3) {
    assert.ok(g.positions[i] >= -1e-9 && g.positions[i] <= 2 + 1e-9);
    assert.ok(g.positions[i + 1] >= -1e-9 && g.positions[i + 1] <= 0.5 + 1e-9);
  }
});

test("wall dust lies on the room's inner walls", () => {
  const p = K.scatter(500, { kind: "walls", w: 8, h: 4, d: 6, seed: 2 });
  for (let i = 0; i < p.length; i += 3) {
    const [x, y, z] = [p[i], p[i + 1], p[i + 2]];
    const onWall = Math.abs(Math.abs(x) - 4) < 0.05 || Math.abs(Math.abs(y) - 2) < 0.05 || Math.abs(z + 3) < 0.05;
    assert.ok(onWall, `${x},${y},${z}`);
  }
});

test("cameraRig dir keys turn at the eased angle, not along a straight target line", () => {
  const rig = K.cameraRig([
    { t: 0, pos: [0, 0, 0], dir: [0, 0] },
    { t: 1, pos: [0, 0, 0], dir: [-90, 0], ease: "none" },
  ]);
  const mid = rig(0.5).target; // 45° to the right of -Z
  assert.ok(Math.abs(mid.x - Math.SQRT1_2) < 1e-9 && Math.abs(mid.z + Math.SQRT1_2) < 1e-9, `${mid.x}, ${mid.z}`);
});
