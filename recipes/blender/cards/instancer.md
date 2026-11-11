# Instancer: thousands of copies of a few meshes

`kit.instancer(stage, name, points, variants, attrs)` and `kit.set_time(ob, t)`.

**Use when:** a crowd, a field of cubes, a swarm; anything where the count is the point (6 → 7 052 figures at 0.5 s a frame).

**Duration and energy:** births ripple over 0.2 s per wave; a wave every 0.3 s reads as multiplication.

## Intent
Geometry Nodes instances points with a variant picked by an int attribute. Nothing per copy lives in Python after setup.

## Motion core
- `points` in Three.js coordinates; `attrs`: `born` (s), `var` (int), `scl`, `rot` (yaw), and any extra float a shader reads as an INSTANCER attribute (`shade`, `accent`).
- A point exists from its `born` time: `set_time(ob, t)` each frame deletes the unborn ones.
- Order the points by distance from where the first copies stand and give them generations (`6, 54, 540, rest`), so the crowd spreads outward.

## Pitfalls
- 5.x: set the time socket with `mod.properties.inputs.<identifier>.value` (the kit stores the identifier in `ob["t_socket"]`).
- Keep the first frames' front clear of copies or the camera starts inside the crowd.
