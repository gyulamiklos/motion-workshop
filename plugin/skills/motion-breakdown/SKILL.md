---
name: motion-breakdown
description: Reverse-engineer a motion-graphics technique from a reference video (an AI-generated clip, a product launch film, a social post) and turn it into a reusable recipe and HyperFrames block in the motion-graphics workshop. Use when someone shares a video or link and says "make something like this", "how is this animated", "reverse engineer", "csináljunk ilyet", "ezt a mozgást szeretném", or wants the workshop to learn a new move.
---

# Motion breakdown → recipe

We learn the technique (timing, easing, choreography, layering), never the footage: no frames, logos, text, music or characters of the reference end up in our work.

**Workshop:** `${MOTION_WORKSHOP:-/mnt/storage/04-projects/motion-graphics}` (`$WS`).

1. **Get the file.** A local file from the user, or a download they are entitled to make. Keep it in `research/<name>/` (git-ignored). Don't fetch from platforms whose terms forbid it; ask for the file instead.
2. **Measure:** `tools/breakdown/breakdown.sh <video> research/<name>` writes `meta.txt`, `cuts.txt` (scene change + one-frame motion spikes), `motion.csv`/`motion.svg` (per-frame motion energy: ramps show easing, flat stretches are holds), `overview.jpg` (every 0.5 s) and `shot-NN-P.jpg` (every 3rd frame with frame numbers).
3. **Read it shot by shot:** `overview.jpg` first, then the shot sheets of the moves that matter. For each move write: what moves, start and end frame, the curve (accelerating, decelerating, overshoot: read the positions frame to frame), what happens in parallel, the hold after it. Cheap tokens: read sheets, not single full-size frames; zoom only where a frame decides a value.
4. **Write the recipe card** `recipes/<name>/card.md` in the video-shotcraft card shape: one sentence; use when; duration and energy; intent (why it works); motion core (the mechanics with measured numbers); a parameter table (value, how it feels when pushed up or down); known pitfalls; the reference (local path, never committed).
5. **Build it as a block:** `recipes/<name>/<name>.html` (a HyperFrames block: variables for copy and colours, GSAP timeline, brand-neutral defaults). Re-skin with a brand's `frame.md` when it goes into a film.
6. **Verify by measurement:** render the block, run `breakdown.sh` on our render too, and compare cuts and motion peaks with the reference (within 2 frames) and the contact sheets side by side. At most 3 rounds; then report what still differs.
7. **Tell the user** what the technique is in one paragraph, where the card and block are, how close the measurement came, and one idea for where it fits in one of the brand's films.
