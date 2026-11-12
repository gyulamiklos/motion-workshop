---
name: motion-film
description: Make a branded motion-graphics film (product teaser, feature film, sales or website video, title card, logo sting) with HyperFrames in the motion-graphics workshop, from real product screens and a brand pack. Use when someone asks for a promo, teaser, product or feature video, an animated explainer of a product change, "animáld meg", "készíts videót az appról", or a motion graphic for a product app or website. For a team recap of shipped changes use motion-explainer; to copy a technique from a reference video use motion-breakdown.
---

# Brand film in the workshop

**Workshop:** `$MOTION_WORKSHOP`, or the current repo when it has `tools/breakdown/` (`$WS`). Read its `CLAUDE.md` and `STATE.md` first; their rules win.

## Pipeline
1. **Brief → SPEC.md.** Purpose, audience, length, must-show features, voice or not. One message per shot; titles hold ≥ 1 s; plan the timeline with rest frames.
2. **New film:** `scripts/new-film.sh <slug> [brand]` → `projects/<date>_<slug>` with the pinned CLI (`hyperframes.version`), the brand's `frame.md` (the `/hyperframes` skill reads it), fonts, logo and the brand blocks (`<brand>-title`, `<brand>-outro`, variables for the copy).
3. **Real screens.** Product UI is captured, never redrawn. Use the capture tool and the environment the brand's `BRAND.md` names (`tools/<name>-capture`: a read-only browser, test environment only, credentials from env vars). Hide scratch data and banners in the page, never edit the product. Abstract scenes may be drawn.
4. **Engine and motion vocabulary.** Pick the cheapest engine per scene (`recipes/blender/README.md`): HTML + GSAP for text, UI, data and product footage (most scenes); the Three.js kit for quick wire 3D; Blender only for a hero 3D scene that lives on light, haze, a crowd, true blur or physics. Read `recipes/_principles.md` and the cards of the pieces you use (`recipes/line3d/cards/`, `recipes/blender/cards/`). A Blender scene comes in as a video with its HUD in HTML: `scripts/blender-block.sh <scene.py> <scene.hud.json>`. Before hand-writing a move, look for it: the HyperFrames registry (`npx hyperframes catalog --query "<move>" --json`, `/hyperframes-registry`), our recipes (`recipes/`), and the video-shotcraft cards (`vendor/video-shotcraft/references/shots/<category>/<card>.md` + its Remotion demo). A shotcraft demo is ported, not imported: keep its frame timings and bezier curves (`CustomEase`), and write what you ported in the film's `TRANSLATION_NOTES.md`.
5. **Build** under the `/hyperframes` contract (seekable GSAP timeline, no `onUpdate` drawing: it doesn't run when the renderer seeks; one sub-composition per scene; a block reused N times gets N copies with their own ids).
6. **Check and look:** `DO_NOT_TRACK=1 npx -y hyperframes@<v> check`, then `snapshot` at every scene's end and its key frames; fix and look again (≤ 3 rounds).
7. **Sound:** music under, effects on the cuts and actions; voiceover with `tools/tts/say.py` (local Hungarian: MOSS-TTS v1.5 when set up, Piper otherwise) when asked.
8. **Render:** `FPS=60 scripts/render-film.sh <film>` (60 fps whenever a clip is 60 fps; the default is 30): check, render, a no-music version when there is a `bgm` track (never leave a second root `index-*.html` in the folder), copy to `renders/`, report loudness.

## Never without explicit permission
`hyperframes publish`, `cloud`, `cloudrun`, any upload or posting (the project guard asks). Live customer data in a film, ever.
