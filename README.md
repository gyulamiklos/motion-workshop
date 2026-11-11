# Motion workshop

Motion graphics videók Claude Code-dal, [HyperFrames](https://github.com/heygen-com/hyperframes)-szel
(HTML + GSAP → MP4). Ez a repó egyszerre a műhely (eszközök, sablonok, receptek) és a
`motion-workshop` Claude Code plugin, amellyel bármelyik repóból kérhetsz videót.

## Mit tud

| Skill | Mire jó | Így kérd |
|---|---|---|
| `dev-recap` | Rövid videó arról, mi került be a fő ágba egy időszakban (hét, sprint), PR-onként egy jelenet, magyar hangalámondással | „Csinálj recapet a múlt hétről az app és a web repóból.” |
| `motion-film` | Márkás film valódi termékképernyőkből: teaser, funkcióvideó, weboldalra szánt animáció | „Készíts 20 mp-es teasert az új regisztrációs űrlapról.” |
| `motion-explainer` | Magyarázó videó egy fogalomról (programnyelv, algoritmus, rendszer) három stílus egyikében: kódszerkesztő, krétatábla, tervrajz | „Készíts egyperces táblás magyarázó videót a Haskell curry-zéséről.” |
| `motion-breakdown` | Egy referenciavideó mozgásának visszafejtése: mérés, receptkártya, újrahasznosítható blokk | „Nézd meg ezt a videót, és tanuld meg a nyitó mozgását.” (a fájl elérési útjával) |

A filmek egy márkacsomagból dolgoznak (`brands/<márka>/`: `BRAND.md`, `FRAME.md`, betűk, logók,
`blocks/<márka>-title.html` és `-outro.html`); ezek helyiek, a repóban nincsenek. A hang helyben készül (Piper), szöveg
nem megy külső szolgáltatóhoz. Alapértelmezett hang: `imre` (férfi); női hang: `anna`, `berta`.
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

# 3. Receptkönyvtár, magyar hang
scripts/update-shotcraft.sh --sync
tools/tts/setup.sh

# 4. A plugin
claude plugin marketplace add gyulamiklos/motion-workshop
claude plugin install motion-workshop@motion-workshop

# 5. Ellenőrzés: minden sor "ok" legyen
scripts/doctor.sh
```

Új Claude Code munkamenetben a négy skill már elérhető. A plugin frissítése:
`claude plugin marketplace update motion-workshop`, a műhelyé: `git pull`.

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
