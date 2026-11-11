---
version: 1
name: Code — explainer style (frame layer)
description: >
  A dark editor as the whole world: programming ideas shown as code that types, lights up and rewrites
  itself. JetBrains Mono for code and chrome, Inter for titles and prose, one warm accent for "what
  changes now". For explainers about languages, algorithms, APIs and refactors.
unit: the frame, 1920×1080 (9:16 and 1:1 by the same rules)
principle: the code is the picture · one accent, only on the change · every line is real, runnable code

colors:
  ground: "#0d1117"
  surface: "#161b22"
  hairline: "#30363d"
  ink: "#e6edf3"
  dim: "#8b949e"
  faint: "#6e7681"
  accent: "#ffcb6b"   # the change, the caret, the answer; never decoration
syntax:               # fixed decoration, not brand colours
  keyword: "#c792ea"
  type: "#7fdbca"
  number: "#f78c6c"
  string: "#c3e88d"
  operator: "#89ddff"
  comment: "#6e7681"

typography:
  code:      { fontFamily: "JetBrains Mono", px: 60, lineHeight: 104px }   # 48 px with 8+ lines; floor 40
  code-dense:{ fontFamily: "JetBrains Mono", px: 40, lineHeight: 1.6 }
  kicker:    { fontFamily: "JetBrains Mono", px: 32, color: faint, form: "a comment: -- 01 / 05" }
  title:     { fontFamily: "Inter", weight: 700, px: 132, tracking: "-0.035em", case: sentence }
  line:      { fontFamily: "Inter", weight: 400, px: 44, color: dim }       # one prose line, ≤ 12 words
  label:     { fontFamily: "JetBrains Mono", px: 24, tracking: "0.16em", upper: true, color: accent }

motion:
  typing: "0.028–0.045 s a character, instant per char (no fade); caret follows the frontier"
  change: "highlight band scaleX 0→1 in 0.22 s power3.out; new text in accent, cools to syntax colour in 0.35 s"
  step-back: "a line that is done drops to opacity 0.32 in 0.3 s"
  enter: "opacity + y 10–16 px, 0.3–0.5 s power3.out; no blur, no bounce, no scale"
  scroll: "whole lines (104 px), 0.4 s power3.inOut"
  between scenes: "hard cut on a beat, or the window scrolls on; never a crossfade between two code views"
  caret: "0.5 s on / 0.5 s off with tl.set, only while nothing types"
---

# Code — explainer style

## The idea
The viewer reads along. Code is never a screenshot of a wall of text: it arrives at reading speed, one
idea per screen, and the accent shows the one thing that changes. Prose is one line under the code, never
a paragraph.

## Blocks
| Block | Use it for |
|---|---|
| `code-title` (ours) | chapter and film titles: comment kicker, typed title, one subtitle, a dim glyph |
| `code-reduce` (ours) | evaluation, substitution, refactor steps: an expression rewritten line by line, the rule on the right |
| registry `code-typing` | a definition typed on with its caret |
| registry `code-highlight` | one line of a longer snippet in focus, the rest dimmed |
| registry `code-diff` | before → after of an edit |
| registry `code-scroll` | a long file, scrolled to the line that matters |
| registry `code-terminal-run` | running it: a command and its output (GHCi, a REPL, a test) |

Registry blocks come in with `npx hyperframes add <name>`; recolour them to the tokens above
(ground, surface, ink, syntax), never keep their own palette.

## Frame rules
- Ground `ground`; a code panel, when framed, is `surface` with a 1 px `hairline` border and 12 px radius.
- Code starts at x = 200 px; at most 6 visible lines at 60 px, 10 at 40 px. More → scroll or cut.
- One accent area per frame (a highlight band, the caret, the new text, or the answer's marker).
- Types (Capitalised) in `type`, keywords in `keyword`: the syntax colours are the same in every block.
- A type signature reads as its own beat: show `f :: a -> b` before the definition, hold it ≥ 1 s.

## Never
- Code that does not compile or run as shown (check it in the real tool first: `ghci`, `node`, `python3`).
- Light theme, gradients on text, glow on code, bouncing or rotating code, emoji.
- Fake IDE chrome (tabs, file trees, minimaps) unless the scene is about the editor itself.
- Two accents in one frame; accent on decoration.
