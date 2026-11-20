# Motion workshop

Motion graphics videók Claude Code-dal, [HyperFrames](https://github.com/heygen-com/hyperframes)-szel
(HTML + GSAP → MP4). Ez a repó egyszerre a műhely (eszközök, sablonok, receptek) és a
`motion-workshop` Claude Code plugin, amellyel bármelyik repóból kérhetsz videót.

## Mit tud

| Skill | Mire jó | Így kérd |
|---|---|---|
| `motion-film` | Márkás film valódi termékképernyőkből: teaser, funkcióvideó, weboldalra szánt animáció | „Készíts 20 mp-es teasert az új regisztrációs űrlapról.” |
| `motion-explainer` | Magyarázó videó egy fogalomról (programnyelv, algoritmus, rendszer) két stílus egyikében: kódszerkesztő, tervrajz. Ugyanez a skill készíti a fejlesztői összefoglalót: mi került be a fő ágba egy időszakban (hét, sprint), PR-onként egy jelenet, a márkában, helyi hangalámondással | „Készíts egyperces magyarázó videót a Haskell curry-zéséről.” · „Csinálj recapet a múlt hétről az app és a web repóból.” |
| `motion-breakdown` | Egy referenciavideó mozgásának visszafejtése: mérés, receptkártya, újrahasznosítható blokk | „Nézd meg ezt a videót, és tanuld meg a nyitó mozgását.” (a fájl elérési útjával) |

A filmek egy márkacsomagból dolgoznak (`brands/<márka>/`: `BRAND.md`, `FRAME.md`, betűk, logók,
`blocks/<márka>-title.html` és `-outro.html`); ezek helyiek, a repóban nincsenek. A hang helyben készül, szöveg
nem megy külső szolgáltatóhoz (lásd [Hang](#hang)).
A magyarázó videók márka nélkül, a `styles/` alatti stíluscsomagokból dolgoznak (ezek a repóban vannak).

## Beállítás (egyszer)

Kell hozzá: Linux vagy macOS, Node.js 22+, `ffmpeg`, `git`, `gh` (bejelentkezve), Python 3.10+, [`uv`](https://docs.astral.sh/uv/); referenciavideó letöltéséhez `yt-dlp` (`uv tool install yt-dlp --with yt-dlp-ejs`).

```bash
# 1. A műhely klónja (a skillek ebből futtatják az eszközöket)
git clone https://github.com/gyulamiklos/motion-workshop.git
cd motion-workshop
git config core.hooksPath .githooks
# a skillek innen tudják, hol a műhely:
echo 'export MOTION_WORKSHOP="'"$PWD"'"' >> ~/.bashrc

# 2. HyperFrames: a rögzített verzió skilljei, telemetria ki
npx -y hyperframes@$(cat hyperframes.version) skills update
npx -y hyperframes@$(cat hyperframes.version) telemetry disable

# 3. Receptkönyvtár, helyi hang (angol Kokoro, magyar Piper; csak CPU)
scripts/update-shotcraft.sh --sync
tools/tts/setup.sh

# 4. A plugin
claude plugin marketplace add gyulamiklos/motion-workshop
claude plugin install motion-workshop@motion-workshop

# 5. Ellenőrzés: minden sor "ok" legyen
scripts/doctor.sh
```

Új Claude Code munkamenetben a három skill már elérhető. A plugin frissítése:
`claude plugin marketplace update motion-workshop`, a műhelyé: `git pull`.

## Hang

Két helyi motor, a film nyelve szerint; a `tools/tts/say.py` a `--lang` alapján választ (alapból `en`):

| Nyelv | Motor | Hangzás | Hangok |
|---|---|---|---|
| **angol** (alapértelmezett) | Kokoro-82M | természetes, CPU-n kb. 10× valós idő | `michael` (amerikai férfi, alap), `george` (brit férfi), `heart` (amerikai nő) |
| magyar | Piper | gépies, de azonnali | `imre` (alap), `anna`, `berta` |

- Telepítés: `tools/tts/setup.sh`, bármilyen gépen, GPU nélkül (~1,8 GB).
- A `male` és a `female` mindkét nyelven az alaphangot választja (angolul `michael`, `heart`; magyarul `imre`, `anna`).
- Jó, helyben futó magyar hangot nem találtunk: a MOSS-TTS, az F5-TTS és az XTTS gyenge vagy nem kereskedelmi
  licencű (`docs/decisions.md`).
- Számokat és jeleket betűvel írj a szövegbe („twelve thousand”, „tizenkétezer”, nem „12 000”).

## Használat

- Kérd szavakkal (lásd a táblázatot). Claude elkészíti a filmet a `projects/` alá, megnézi képkockákon,
  és a kész MP4-et a `renders/` mappába teszi (ez nincs gitben).
- Kézzel: `scripts/new-film.sh <név> [márka|stílus]` új film, `scripts/render-film.sh <filmmappa>` render
  (zenés és zene nélküli változat, hangerőméréssel), `scripts/check.sh` ellenőrzés.
- Szerkeszteni a HyperFrames böngészős felületén is lehet: a filmmappában `npm run dev`.

## Szabályok

- **Közzététel, feltöltés** (`hyperframes publish`, `cloud`, közösségi posztolás) csak kifejezett kérésre.
- **Termékképernyő** csak teszt környezetből, csak olvasva; éles ügyféladat soha nem kerül videóba.
  Belépési adat csak környezeti változóban.
- **Recapbe** csak beolvasztott, vissza nem vont változás kerül, forrással; a szöveg átmegy az adatvédelmi szűrőn.
- **Licencek:** `THIRD_PARTY.md`. Néhány hang forrása ellenőrizetlen, ezért kifelé menő anyag előtt cseréld.

A műhely szabályai: `CLAUDE.md`. A márkacsomagok, filmek és jegyzetek helyben maradnak (`.gitignore`).
