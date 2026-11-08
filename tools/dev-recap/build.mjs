// Builds a dev-recap film (HyperFrames) from recap.json into a film folder made by scripts/new-film.sh.
// Usage: node tools/dev-recap/build.mjs <recap.json> <film dir> [--voice imre|anna|berta|none] [--no-music]
// recap.json: see tools/dev-recap/recap.example.json. Scene lengths come from reading time (0.3 s a word
// plus the entrance) or from the voiceover, whichever is longer. An item with "composition" (a path relative
// to recap.json, e.g. a diagram) uses that scene instead of the card; "min_duration" sets a floor in seconds.
import fs from 'fs';
import path from 'path';
import { spawnSync } from 'child_process';
import { fileURLToPath } from 'url';

const WS = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const args = process.argv.slice(2);
const flag = (name, dflt) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : dflt; };
const [recapPath, filmArg] = args.filter((a, i) => !a.startsWith('--') && !(i > 0 && args[i - 1].startsWith('--voice')));
if (!recapPath || !filmArg) throw new Error('usage: build.mjs <recap.json> <film dir> [--voice imre|anna|berta|none] [--no-music]');
const recap = JSON.parse(fs.readFileSync(recapPath, 'utf8'));
const FILM = path.resolve(filmArg);
const VOICE = flag('--voice', recap.voice?.speaker ?? 'imre'); // imre = male (default), anna and berta = female
const MUSIC = !args.includes('--no-music');

const comp = (...p) => path.join(FILM, 'compositions', ...p);
const asset = (...p) => path.join(FILM, 'assets', ...p);
for (const d of ['compositions', 'assets/fonts', 'assets/brand', 'assets/audio', 'assets/voice']) fs.mkdirSync(path.join(FILM, d), { recursive: true });

// ── brand and audio assets ──
if (!recap.brand) throw new Error('recap.json needs "brand" (a folder under brands/)');
const BRAND = path.join(WS, 'brands', recap.brand);
// the brand's opening and closing blocks: blocks/<name>-title.html and blocks/<name>-outro.html
const block = (kind) => {
  const f = fs.readdirSync(path.join(BRAND, 'blocks')).find((n) => n.endsWith(`-${kind}.html`));
  if (!f) throw new Error(`no blocks/*-${kind}.html in ${BRAND}`);
  return path.join(BRAND, 'blocks', f);
};
for (const f of fs.readdirSync(path.join(BRAND, 'fonts'))) fs.copyFileSync(path.join(BRAND, 'fonts', f), asset('fonts', f));
for (const f of fs.readdirSync(path.join(BRAND, 'assets'))) fs.copyFileSync(path.join(BRAND, 'assets', f), asset('brand', f));
fs.copyFileSync(path.join(BRAND, 'FRAME.md'), path.join(FILM, 'frame.md'));
const SFX = path.join(WS, 'vendor/video-shotcraft/assets/audio');
const audioSrc = { 'transition-soft.mp3': 'sfx/transition/transition-soft.mp3', 'swoosh-quick.mp3': 'sfx/transition/swoosh-quick.mp3', 'bgm-tech-house.mp3': 'bgm/bgm-tech-house.mp3' };
for (const [name, rel] of Object.entries(audioSrc)) if (fs.existsSync(path.join(SFX, rel))) fs.copyFileSync(path.join(SFX, rel), asset('audio', name));

// A block copied under its own id, with this film's values baked in as the variable defaults
// (Studio still edits them through the host's data-variable-values).
function placeBlock(src, id, prefix, newPrefix, values) {
  let html = fs.readFileSync(src, 'utf8');
  const oldId = html.match(/data-composition-id="([^"]+)"/)[1];
  html = html.replaceAll(`data-composition-id="${oldId}"`, `data-composition-id="${id}"`)
    .replaceAll(`window.__timelines["${oldId}"]`, `window.__timelines["${id}"]`);
  if (prefix !== newPrefix) html = html.replace(new RegExp(`(["#.])${prefix}-`, 'g'), `$1${newPrefix}-`);
  html = html.replace(/data-composition-variables='([\s\S]*?)'/, (_, json) => {
    const decl = JSON.parse(json).map((d) => (values[d.id] !== undefined ? { ...d, default: typeof values[d.id] === 'string' ? values[d.id] : JSON.stringify(values[d.id]) } : d));
    return `data-composition-variables='${JSON.stringify(decl).replaceAll("'", '&#39;')}'`;
  });
  fs.writeFileSync(comp(`${id}.html`), html);
}

// ── voiceover first: it sets the timing ──
const lines = [];
if (recap.voice_lines?.intro) lines.push({ id: 'intro', text: recap.voice_lines.intro });
if (recap.voice_lines?.stats) lines.push({ id: 'stats', text: recap.voice_lines.stats });
recap.items.forEach((it, i) => it.voice && lines.push({ id: `item-${i + 1}`, text: it.voice }));
if (recap.voice_lines?.outro) lines.push({ id: 'outro', text: recap.voice_lines.outro });
let vo = { lines: {} };
if (VOICE !== 'none' && lines.length) {
  const tmp = path.join(FILM, 'capture', 'voice-lines.json');
  fs.mkdirSync(path.dirname(tmp), { recursive: true });
  fs.writeFileSync(tmp, JSON.stringify(lines, null, 2));
  const py = path.join(WS, 'tools/tts/.venv/bin/python');
  const r = spawnSync(py, [path.join(WS, 'tools/tts/say.py'), tmp, asset('voice'), '--voice', VOICE], { encoding: 'utf8' });
  if (r.status !== 0) throw new Error(`tts failed (run tools/tts/setup.sh first): ${r.stderr}`);
  vo = JSON.parse(fs.readFileSync(asset('voice', 'voice.json'), 'utf8'));
}
const voDur = (id) => vo.lines[id]?.duration ?? 0;
const words = (...t) => t.flat().join(' ').split(/\s+/).filter(Boolean).length;

// ── scenes ──
const scenes = [];
const VO_LEAD = 0.35;
placeBlock(block('title'), 'title', 'ot', 'ot', recap.title);
scenes.push({ id: 'title', dur: Math.max(3.8, VO_LEAD + voDur('intro') + 0.8), vo: 'intro' });
if (recap.stats) {
  placeBlock(path.join(WS, 'templates/dev-recap/compositions/recap-stats.html'), 'stats', 'rs', 'rs', recap.stats);
  const read = 1.6 + 0.3 * words(recap.stats.eyebrow ?? '', recap.stats.period ?? '') + 0.8 * (recap.stats.stats?.length ?? 0);
  scenes.push({ id: 'stats', dur: Math.max(4, read, VO_LEAD + voDur('stats') + 0.8), vo: 'stats' });
}
recap.items.forEach((it, i) => {
  const id = `item-${i + 1}`;
  const values = { index: `${String(i + 1).padStart(2, '0')} / ${String(recap.items.length).padStart(2, '0')}`, area: it.area, title: it.title, text: it.text, details: it.details ?? [], source: it.source ?? '' };
  // an item may bring its own scene (a diagram) instead of the card: "composition" is relative to recap.json
  const src = it.composition ? path.resolve(path.dirname(recapPath), it.composition) : path.join(WS, 'templates/dev-recap/compositions/recap-item.html');
  placeBlock(src, id, 'ri', `ri${i + 1}`, values);
  const read = 1.4 + 0.3 * words(it.title, it.text, ...(it.details ?? []));
  scenes.push({ id, dur: Math.max(4.5, read, it.min_duration ?? 0, VO_LEAD + voDur(id) + 1.0), vo: id });
});
placeBlock(block('outro'), 'outro', 'oo', 'oo', recap.outro ?? {});
// the closing line needs ≥2 s on screen: the lockup's tagline lands at 3.1 s
scenes.push({ id: 'outro', dur: Math.max(5.6, 0.6 + voDur('outro') + 1.6), vo: 'outro', voAt: 0.6 });

let t = 0;
for (const s of scenes) { s.start = Math.round(t * 30) / 30; s.dur = Math.ceil(s.dur * 30) / 30; t = s.start + s.dur; }
const TOTAL = Math.round(t * 1000) / 1000;
const sec = (x) => String(Math.round(x * 1000) / 1000);

const hosts = scenes.map((s) => `      <div id="${s.id}" data-composition-id="${s.id}" data-composition-src="compositions/${s.id}.html" data-start="${sec(s.start)}" data-duration="${sec(s.dur)}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>`);
const audio = [];
scenes.forEach((s, i) => {
  if (vo.lines[s.vo]) audio.push(`      <audio id="vo-${s.id}" class="clip" src="assets/voice/${vo.lines[s.vo].file}" data-start="${sec(s.start + (s.voAt ?? VO_LEAD))}" data-duration="${sec(vo.lines[s.vo].duration)}" data-track-index="2" data-volume="1"></audio>`);
  if (i > 0 && fs.existsSync(asset('audio', 'transition-soft.mp3'))) audio.push(`      <audio id="sfx-cut-${i}" class="clip" src="assets/audio/transition-soft.mp3" data-start="${sec(Math.max(0, s.start - 0.15))}" data-duration="1.2" data-track-index="4" data-volume="0.22"></audio>`);
});
if (MUSIC && fs.existsSync(asset('audio', 'bgm-tech-house.mp3'))) {
  const vol = Object.keys(vo.lines).length ? 0.1 : 0.3;
  audio.unshift(`      <!-- music bed: ducked under the voice; hide it with data-hidden for a version without music -->\n      <audio id="bgm" class="clip" src="assets/audio/bgm-tech-house.mp3" data-start="0" data-duration="${sec(TOTAL)}" data-track-index="3" data-volume="${vol}" data-fade-in="1" data-fade-out="1.5"></audio>`);
}

fs.writeFileSync(path.join(FILM, 'index.html'), `<!doctype html>
<html lang="hu" data-resolution="landscape">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>${recap.name ?? 'Dev recap'}</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/CustomEase.min.js"></script>
    <script>gsap.registerPlugin(CustomEase);</script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #ffffff; }
      #root { position: relative; width: 100%; height: 100%; }
    </style>
  </head>
  <body>
    <!-- Built by tools/dev-recap/build.mjs from ${path.basename(recapPath)}; edit the recap and rebuild, or edit here in Studio. -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="${sec(TOTAL)}" data-width="1920" data-height="1080">
${hosts.join('\n')}
${audio.join('\n')}
    </div>
    <script>
      window.__timelines["main"] = gsap.timeline({ paused: true });
    </script>
  </body>
</html>
`);
console.log(`built ${scenes.length} scenes, ${TOTAL.toFixed(1)} s, voice: ${VOICE === 'none' ? 'none' : Object.keys(vo.lines).length + ' lines'}`);
for (const s of scenes) console.log(`  ${s.id.padEnd(8)} ${sec(s.start).padStart(6)}s  ${s.dur.toFixed(2)}s${vo.lines[s.vo] ? `  vo ${vo.lines[s.vo].duration.toFixed(2)}s` : ''}`);
