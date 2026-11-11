# Scanline material: the striped silhouette

`kit.scanline(name, freq, duty, ...)`, `kit.time_node(mat)`, the Value node `ACC`.

**Use when:** a `shape_mesh` figure that must read as a hologram: bright outline, horizontal stripes, an opaque dark fill that hides what stands behind.

## Intent
Stripes in object height keep a thousand overlapping figures readable; the dark fill stops them from turning into a white haze.

## Motion core
- `freq` stripes per unit of height, `duty` share lit, `edge` outline brightness, `stripe` stripe brightness.
- Instancer attributes: `born` gives a birth pulse (`1 + 2·0.5^(age/half)`), `shade` a per-copy brightness, `accent` whether the copy takes the accent fill.
- Per frame: `time_node(mat).outputs[0].default_value = t` and `mat.node_tree.nodes["ACC"]` (0..1) for how far accent copies are filled; let it pulse then hold at ~0.22.

## Pitfalls
- A missing `shade` reads 0 and would black the copy: the material treats it as 1.
- Fog (`fog=(6, 38, 0)`) must reach past the farthest row or the back of the crowd drops out.
