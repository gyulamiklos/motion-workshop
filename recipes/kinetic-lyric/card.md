# Kinetic lyric: squeeze-and-sweep

A whole line lands at once, grey and horizontally squeezed; each word unsqueezes about its centre as an accent colour sweeps through it letter by letter, then turns white when the next word starts.

**Use when:** a line is sung or spoken over the picture and the viewer should read along with it: lyric videos, voiceover subtitles that are the main text of a scene, a punchline built word by word. Not for body copy, or for a line with nothing driving its rhythm.

**Duration and energy:** 0.15–0.5 s per word, set by the voice, not by a fixed beat. Medium-high energy: the movement is small (scale and colour, no travel), so it can run under a busy background.

## Intent
The reader sees the whole line at once, so their eye never has to hunt for the next word. The squeeze sorts the words into said and not yet said before any colour does: grey and narrow is "coming", full width is "said". The accent marks the exact syllable, and the word turning white a beat later leaves a calm, readable line behind.

## Motion core (measured at 60 fps)
- **Line entrance:** every word at once, grey `#8f8a90`, `scaleX ≈ 0.58` about the word's centre. Lands in 1–2 frames with a slight blur, cutting straight in over the previous line (no reveal).
- **Word activation, three layers starting together:**
  - `scaleX 0.58 → 1` about the centre in **~0.15 s (8–9 frames)**, decelerating. The word's centre does not move: in the reference, "trees" grew from 133 px to 232 px around the same centre.
  - Accent `#ff2d8c` sweeps through the letters over **~65 % of the word's sung length**: "trees" took 8 of 14 frames, "interesting" 28 of 36. Each letter changes in one frame.
  - A soft accent glow: a text shadow of about 14 px at 35 % and a radial bloom behind the word.
- **Hand-off:** the next word's sweep starts first. About **2 frames (0.035 s) later** the previous word snaps to white `#f5f1ea` in one frame and its glow fades out over ~0.2 s.
- **Accent words** (the line's keyword) keep the accent colour after they are sung.
- **Variant without squeeze** (the 2:42 instance of the reference): the same sweep and hand-off with `scaleX = 1`. It is calmer and suits longer lines.
- **Optional extras seen in the reference, not built:** a 1-frame accent scanline across the frame on the line change; a short tracking "breath" (letter spacing ±) on strong beats; a sung word glitching into a glyph and then a cursor bar.

## Parameters
| Parameter | Value | Push up | Push down |
|---|---|---|---|
| `squeeze` | 0.58 | toward 1: calmer, the future reads as text | under 0.5: the grey words become unreadable stripes |
| unsqueeze time | 0.15 s | slow, "stretchy", lags behind the voice | under 0.08 s: a pop, nervous |
| sweep share | 0.65 of the word | the last letter lands as the next word starts, no rest | under 0.4: whole-word flashes, the syllable feel is lost |
| white lag | 0.035 s | over 0.1 s: two words lit at once, muddy | 0: the hand-off feels mechanical |
| glow | 14 px / 35 % | neon, the edges get soft, hurts reading | 0: flat, loses the "lit" feeling |
| font | wide, heavy grotesk (Archivo Black, bundled) | – | a light or condensed face: the squeeze no longer reads |

## Timing input
`times` is a JSON array of word starts (s) from the line start, from the voice or the song: `hyperframes init --audio` transcribes with whisper and gives word timestamps; for local TTS, the Piper phoneme timing. Leave it empty for an even `beat`.

## Pitfalls
- Timing to a fixed beat when the voice is uneven: the eye catches it at once. Use real word timestamps.
- `transform-origin` on the left edge makes the line "pump" to the right. It must be the centre, and the gaps between the grey words come from that.
- Long lines: past 6–7 words per row the squeezed tail runs out of the title-safe area. Break them with `\n`.
- At 30 fps the one-frame colour steps become cuts, which is fine; do not lengthen them to "smooth" it.
- The accent must hold contrast against the background (the `check` contrast pass); a mid-grey future colour on a light brand background disappears.

## Reference
`research/simulation-ending/` (local, never committed): `source.mp4` 0:40.4–0:41.6 (squeeze variant) and 2:41.6–2:44 (no squeeze). Measured with `breakdown.sh` and an accent-pixel tracker on the text strip. Our render: word hand-offs within 1–2 frames of the reference at 60 fps.
