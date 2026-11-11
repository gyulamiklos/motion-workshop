# Materials and fog: emission, distance fade, lit haze

`kit.emit(name, strength, attr, fog)`, `kit.set_color(ob, rgb, alpha)`, `kit.haze(...)`, `kit.point_light(...)`.

**Use when:** any line or wire object, and any scene whose accent should light the air.

**Duration and energy:** static look; the colour is animated per frame.

## Intent
Lines are emission, not lit surfaces: the object's colour is the colour, its alpha is the brightness (above 1 blooms), and brightness fades with camera distance, so far lines sink into the dark. Haze is the only thing light scatters in.

## Motion core
- `emit(name, fog=(near, far, far_brightness))`: one material, many objects; animate only `ob.color` through `set_color`. `attr` multiplies by a per-point float attribute (dust brightness).
- `haze(stage, size, center, density)`: a box of faint volume; a `point_light` with no shadows inside it makes a glow. Pulse the light's energy with the accent (`300 * acc` in the collapse scene).
- Colours go through `kit.lin("#ff2d8c")` (sRGB hex → linear). White is `WHITE`; mix with `mix3`.

## Parameters
| Parameter | Value | Push up | Push down |
|---|---|---|---|
| haze `density` | 0.01–0.035 | a visible fog | the light shows only on the objects |
| fog far brightness | 0–0.2 | far lines stay | far lines vanish |
| line alpha | 0.4 floor, 0.9 hero | brighter | quieter |

## Pitfalls
- An alpha-0 emission is black and still hides what is behind it: hide with `show()` (scale) or `hide_render`.
- `volumetric_end` on the Stage bounds the volume; a haze larger than that is cut.
