# SDF shape: a smooth silhouette from circles and capsules

`kit.sd_circle`, `sd_capsule`, `sd_union(parts, k)`, `contour`, `shape_mesh(name, sdf, box)`.

**Use when:** figures, icons or any flat symbol that must stay smooth at any scale and be the same mesh for thousands of copies.

## Intent
Define the body as a distance field, contour it once with marching squares, get one outline whatever the parts: no seams where limbs meet.

## Motion core
- Parts are circles and capsules; `sd_union(parts, k=0.04)` melts them with a polynomial smooth-min.
- `shape_mesh` returns a filled mesh plus an inner outline ribbon `rim` wide; face attribute `edge` = 1 on the ribbon. It stands in the XZ plane facing −Y.
- Mesh cost is set by `step` (0.008 default); every other contour point is dropped.

## Pitfalls
- Saddle cells in marching squares pair arbitrarily; fine at this step, visible if you raise it.
- One mesh per variant (six faces = six meshes), not one per copy: the instancer does the copies.
