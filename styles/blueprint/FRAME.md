---
version: 1
name: Blueprint — explainer style (frame layer)
description: >
  A technical drawing that builds itself: white lines plotted on a blueprint-blue grid, mono labels,
  dimension lines, a title cartouche, and one safety-orange accent for the signal that moves through the
  system. For architectures, data flows, pipelines, protocols and "how the parts fit".
unit: the frame, 1920×1080 (9:16 and 1:1 by the same rules)
principle: everything is plotted, nothing is filled · the grid always drifts · orange is the signal, never decoration

colors:
  ground: "#0b2a4a"
  grid-major: "rgba(232,241,255,0.13)"   # every 120 px
  grid-minor: "rgba(232,241,255,0.05)"   # every 24 px
  line: "#e8f1ff"
  dim: "#8fb3d9"
  accent: "#ffb547"   # the signal, dimension lines, the current value

typography:
  title:  { fontFamily: "Oswald", weight: 600, px: 150, upper: true, tracking: "0.01em" }
  label:  { fontFamily: "IBM Plex Mono", weight: 500, px: 44 }     # inside a box; shrinks to fit, floor 30
  kicker: { fontFamily: "IBM Plex Mono", weight: 500, px: 30, upper: true, tracking: "0.16em", color: dim }  # "FIG. 3 · PIPELINE"
  sub:    { fontFamily: "IBM Plex Mono", px: 28, upper: true, tracking: "0.16em", color: dim }
  value:  { fontFamily: "IBM Plex Mono", weight: 600, px: 34, color: accent }
  caption:{ fontFamily: "IBM Plex Mono", px: 40, color: line }

lines: "2 px everywhere; corner ticks and crop marks at 0.6–0.7 opacity; arrowheads are open chevrons (16 × 20 px), never filled triangles"

motion:
  plot: "strokes draw at a constant 2200 px/s with ease none (a plotter, not a hand); boxes one after another"
  type: "labels type on with steps(12) in 0.3 s; kickers and subs fade 0.25 s"
  signal: "an accent dot (r 11) eases box to box (0.55 s power2.inOut); on arrival the box outline flashes accent → line in 0.5 s and a halo ring grows 14 → 60 px while fading"
  grid: "the grid drifts the whole scene (48 × 24 px over the slot, linear); a cut to a new sheet keeps the drift direction"
  between scenes: "pan across the sheet to the next drawing (the grid moves with it), or a hard cut to a new sheet number"
---

# Blueprint — explainer style

## The idea
The system is drawn as an engineer would draw it, then something runs through it. The viewer first sees
the parts (plotted one by one), then the behaviour (the orange signal). It suits structure: what talks to
what, what flows where, in what order.

## Blocks
| Block | Use it for |
|---|---|
| `blueprint-title` (ours) | chapter and film titles: crop marks, plotted title, dimension line with a formula, cartouche |
| `blueprint-flow` (ours) | a chain of 2–5 steps; a signal runs it and each step shows its value |
| registry `flowchart` | branching decisions (recolour: line on ground, sticky notes become plotted boxes) |
| registry `exploded-stack` | layers of a system pulled apart (recolour, outlines only) |
| `recipes/line3d/` (Three.js kit) | a wire 3D model of the system; same palette, lines only |

## Frame rules
- Grid on every frame; content in the 80 % title-safe box (crop marks sit at its corners).
- Outlines only: no filled shapes except the signal dot. No shadows, no gradients, no rounded corners.
- One signal (accent) at a time; values in accent only while they are the newest, then they step back to the `dim` colour.
- Every box has a mono label; every figure a kicker (`FIG. n · NAME`).

## Never
- Hand-drawn wobble (that is the `chalk` style), icons, emoji, photos.
- A whole drawing at once: plot it.
- Orange on anything that is not the signal, a dimension or the current value.
