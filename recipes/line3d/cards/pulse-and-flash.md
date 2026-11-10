# Birth pulse and flash frame

A new part arrives in the accent with bloom and cools to white in a tenth of a second; once per big moment, the whole frame lifts for one frame and decays.

**Use when:** every event: a part being born, a value landing, a step done (pulse). The start or end of an act, a "boot" (flash). The HUD changes on the same frame.

**Duration and energy:** pulse ≈ 0.16 s, flash ≈ 0.15–0.2 s. Short and sharp; they set the beat.

## Intent
The accent means "now". A pulse that cools leaves a calm white world and a clear record of what just happened; a flash marks a boundary the viewer feels rather than reads.

## Motion core (measured at 60 fps, the same shape three times)
- **Pulse:** `K.pulse(t, t0, { attack: 0.06, half: 0.025 })`: 0 before `t0`, up to 1 in 3–4 frames (`power2.out`), then exponential decay, half-life ≈ 1.5 frames. Feed it to `set({ pulse })`; `hold` keeps a part in the accent for longer (a live point).
- **Flash:** `K.flash(t, t0)` → `stage.flash`: luma +50/255 in one frame, half-life ≈ 3 frames, slightly vignetted.
- **One event at a time:** the next pulse starts after the previous one has cooled; events land on a beat (≈ 0.65 s in the reference).
- **Tie a number to it:** a log row, a counter or a label changes on the pulse frame (`tl` rows at the same `t0`).

## Parameters
| Parameter | Value | Push up | Push down |
|---|---|---|---|
| `attack` | 0.06 s | a fade-in, not a birth | under 0.03 s: a flicker at 30 fps |
| `half` | 0.025 s | over 0.06 s: accent lingers, two events overlap | – |
| flash `lift` | 0.2 | over 0.3: a white frame, harsh | under 0.1: not noticed |
| beat | 0.65 s | slow, ceremonial | under 0.4 s: pulses merge into a shimmer |

## Pitfalls
- A pulse on a part that is not visible yet (draw still 0) wastes the event: start the draw-on on the same `t0`, quick (≈ 0.12 s).
- At 30 fps the attack is 2 frames; do not lengthen it to look smoother.
- Use the flash at most once or twice a film.

## Reference
Pulses 0:06.9, 0:07.6, 0:08.25; flash frames 0:04.88 and 3:41.65 (principles, "Event grammar"). Kit: `pulse`, `flash`, `PULSE`, `FLASH`.
