---
version: 1
name: Chalk — explainer style (frame layer)
description: >
  A teacher at a chalkboard: everything is written and drawn by hand while the viewer watches, in white
  chalk on a dark green-slate board, with one coloured chalk for what matters. Caveat for all writing.
  Friendly and patient; for lessons, first principles, maths and "why does this work".
unit: the frame, 1920×1080 (9:16 and 1:1 by the same rules)
principle: nothing appears, everything is written · one coloured chalk per frame · the board fills up, then is wiped

colors:
  board: "#1e2a26"
  chalk: "#edeae0"
  chalk-dim: "rgba(237,234,224,0.78)"
  accent: "#f2d16b"      # yellow chalk: the one thing to look at
  second: "#8ec9f0"      # blue chalk: only for a second, contrasting group (never with the accent as decoration)
  warn: "#f29bb2"        # pink chalk: wrong, crossed out, the trap

typography:
  title:    { fontFamily: "Caveat", weight: 700, px: 168, lineHeight: 1.0 }
  line:     { fontFamily: "Caveat", weight: 600, px: 132 }   # a formula or a line of code on the board
  note:     { fontFamily: "Caveat", weight: 500, px: 76, color: accent }
  subtitle: { fontFamily: "Caveat", weight: 500, px: 64, color: chalk-dim }
  floor:    "56 px: smaller chalk is unreadable"

texture: "SVG filter on the writing layer: feTurbulence (0.9, 2 octaves) → displacement 3.5 px + holes; seed re-posed every 0.125 s (8 fps boil). Never on the board itself."

motion:
  writing: "letter by letter, a left-to-right clip wipe inside each letter; 0.055 s a letter for lines, 0.035 s for notes, 0.07 s for titles"
  drawing: "strokes with stroke-dashoffset at hand speed (~900 px/s); a circle overshoots its start by 10–15 %; the arrowhead is a separate stroke after the shaft"
  emphasis: "circle, underline, cross out, or an arrow; never scale, glow or colour flashing"
  between scenes: "the board is wiped (a soft smear sweeping left to right, 0.5 s) or the camera slides to a clean part of the board; no hard cut between two full boards"
  pace: "the hand never waits: the next stroke starts within 0.3 s of the last one, then the finished board holds ≥ 1.5 s"
---

# Chalk — explainer style

## The idea
The viewer watches the idea being made. Every mark is drawn in the order a teacher would draw it, and the
coloured chalk shows where to look. It is warm and human, so it carries Hungarian copy and spoken
narration well.

## Blocks
| Block | Use it for |
|---|---|
| `chalk-title` (ours) | chapter and film titles: kicker, written title, drawn underline, written subtitle |
| `chalk-callout` (ours) | one line on the board, one part circled, an arrow to a note, an optional result line |
| registry `hw-arrow`, `hw-box-label` | single hand-drawn arrows and boxes; set stroke to `chalk`/`accent` |
| registry `hw-pipeline` | steps joined by curved connectors (a process, a data flow) |
| registry `hw-path-text` | writing that follows a curve |
| registry `hw-boil` | the seek-safe boil helper, when a hand-built drawing needs it |

Registry blocks: `npx hyperframes add <name>`, then recolour to the tokens above and wrap the drawing in
the chalk filter (copy it from `chalk-title.html`).

## Frame rules
- Board fills the frame; writing starts at x ≥ 220 px and stays in the 80 % title-safe box.
- At most three things on the board at once (a line, a mark, a note). A fourth means wipe and continue.
- One coloured chalk per frame; pink only for "wrong", blue only for a second group.
- Code on the board is written in Caveat like everything else; if exact characters matter (`::`, `->`), switch the scene to the `code` style instead.
- Font: `Caveat` (OFL, `fonts/Caveat.ttf`, covers Hungarian ő/ű); `new-film.sh` copies it to `assets/fonts/`.

## Never
- Text that fades or pops in: all writing is written.
- Clip-art, icons, emoji, drop shadows, gradients on the writing.
- A full board dropped on screen at once.
