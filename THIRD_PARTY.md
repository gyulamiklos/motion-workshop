# Third-party material

| What | Where | Licence | How we use it |
|---|---|---|---|
| HyperFrames (HeyGen) | `npx hyperframes@<hyperframes.version>`, skills in `~/.claude/skills` | Apache-2.0 | the render engine and its agent skills |
| GSAP + CustomEase | loaded from jsDelivr in every film | GSAP "no charge" standard licence (free, commercial use included; not OSI) | the animation runtime |
| three.js 0.184.0 (mrdoob and contributors) | imported from jsDelivr by `recipes/line3d/assets/line3d.js` (ES module, pinned version) | MIT | the WebGL renderer of the line-3D kit |
| video-shotcraft (Vincent Wei) | `vendor/video-shotcraft` (pinned clone, not committed) | Apache-2.0 (code, cards); audio per file, see its `assets/audio/ATTRIBUTION.md` | shot recipe cards and timings, ported to HyperFrames; some sound effects and a music bed (several sources unverified: internal use only until checked) |
| brag-video `/brag` skill (Shunit Haviv Hakimi) | rules adapted in `plugin/skills/dev-recap` | MIT | the recap's working rules (cover everything, claims from the project, privacy scan, reading time); no code or assets copied |
| Caveat (The Caveat Project Authors) | `styles/chalk/fonts/Caveat.ttf` + `OFL.txt` | SIL OFL 1.1 | the handwriting of the chalk explainer style |
| Piper TTS + hu_HU voices (anna, berta, imre) | `tools/tts` (venv and voices not committed) | piper-tts GPL-3.0 (the tool); voices: CC0 data, fine-tuned from the "lessac" English voice | local Hungarian voiceover; check the base voice's licence before external use |
