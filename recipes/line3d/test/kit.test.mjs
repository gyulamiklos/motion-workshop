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
