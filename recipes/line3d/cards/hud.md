# HUD: corners, a log and leader labels

A flat mono layer over the 3D world: corner brackets and readouts, a log that gains one line per event on an accent bar, and leader lines from a 3D point to a label.

**Use when:** a scene needs words: what is happening, a number that grows, a name for the part just born. Add it last and keep it sparse: a title block, one live readout, and a log or labels, not all of them.

**Duration and energy:** rows land in 0.05 s on the event frame; the bar moves in 0.06 s and cools over 0.25 s. The HUD never moves with the camera.

## Intent
The world moves, the HUD stays: the eye has a stable layer to read while the 3D keeps turning. Tying each HUD change to a pulse makes the words and the picture one event.

## Motion core
- **Type:** mono 11–15 px, white at 0.5–0.7, letter spacing +0.05 em, tabular numbers. Bold white only for the title.
- **Corners:** 14 px brackets, 1 px at 0.35, inside the 90 % action-safe box (96 px / 64 px at 1080p); readouts 16 px inside them.
- **Log:** one row per event at the event's `t0` (opacity 0 → 1 in 0.05 s); an accent bar (`mix-blend-mode: screen`, 0.32 → 0.14) jumps to the new row. Times in the row are the event times (`0.412`), and "new" in the accent.
- **Leader label:** project the 3D point every frame (`stage.project(v)`), draw a 1 px polyline with an elbow (40 px out, 90 px up), the label at its end, flipped left when the point is past ≈ 75 % of the width. It appears on the pulse frame (0.08 s) and leaves before a dive.
- **Live readouts** (`t = 2.400 s`, `alt 2.553 u`) update every frame from the same values the scene uses.
- **Structure:** HUD as GSAP tweens on the same timeline as the driver; numbers and leaders written inside `draw(t)`.

## Parameters
| Parameter | Value | Push up | Push down |
|---|---|---|---|
| HUD alpha | 0.62 | competes with the 3D | under 0.4: unreadable on video |
| log width | 540 px | covers the hero | – |
| rows | ≤ 8 | a wall of text | – |

## Pitfalls
- The reference's own words, labels and layout stay out: write our own text for our topic.
- A HUD that follows the camera (attached in 3D) loses the stable layer; only leader lines follow a point.
- Accent only on "new" and the bar, never on the title.

## Reference
Inventory rows 22, 24, 25 in `recipes/_principles.md`. Built in `recipes/line3d/globe-dive.html` (`#gd-log`, `#gd-lead`).
