# Lines, points and text on a curve

`kit.poly(stage, name, strokes, mat)` + `kit.draw(ob, k)`, `kit.point_cloud(...)`, `kit.text_on_path(...)` with `Path2D`.

**Use when:** wire rooms and floors that draw on, dust on walls, a line of text that rides a curve.

**Duration and energy:** a draw-on is 0.6–1.0 s `power2.out`; text paints word by word with the curve.

## Intent
Thin geometry is the look. A line is a tube (`LINE_R` ≈ 1–1.5 px), so it blooms, blurs and fogs like everything else.

## Motion core
- `poly`: many splines in one curve object; `draw(ob, k)` sets the bevel end (0..1 of each spline) and hides at 0.
- `point_cloud`: points as spheres through Geometry Nodes, radius per point, `bright` attribute for `emit(attr="bright")`.
- `text_on_path`: one mesh per word, every vertex bent onto a `Path2D` by arc length; returns `[(object, start 0..1)]` for painting word by word.

## Pitfalls
- 5.x: `bevel_factor_mapping_end = "SPLINE"`.
- The font is Lato Black from the system fonts (`kit.font()`, OFL); a missing font fails at load.
