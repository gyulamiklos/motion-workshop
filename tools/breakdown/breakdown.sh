#!/usr/bin/env bash
# Motion breakdown of a reference video: the raw material for reverse-engineering a technique.
# Usage: tools/breakdown/breakdown.sh <video file> [out dir] [--shots N,M,...|all] [--range A-B [--crop W:H:X:Y]]
# Writes into the out dir (default: research/<video name>/):
#   meta.txt          resolution, fps, duration
#   cuts.txt          detected cuts (seconds); scene threshold SCENE (default 0.12; raise it for footage with lots of motion)
#   shots.txt         shot number, start, end, length (s)
#   motion.csv        per-frame motion energy (mean absolute difference to the previous frame, 0–255)
#   motion.png        the motion curve with the cuts marked: easing and holds read off its shape
#   overview-P.jpg    the whole video in at most 3 pages of 48 tiles (one tile every 0.5 s, or sparser for long videos)
#   shot-NN-P.jpg     contact sheets per shot (24 tiles a page): every 3rd frame, frame numbers burned in.
#                     All shots for a video up to 30 s, else only the ones named with --shots.
#   range-A-B.jpg     --range: every frame of A..B seconds (every 2nd/3rd when long, 48 tiles max), frame numbers
#                     burned in; --crop zooms into one region at full resolution (ffmpeg crop order W:H:X:Y)
# With --shots or --range on an out dir that already has a breakdown, only the sheets are made.
# Reference videos stay local (research/ is git-ignored): we re-implement techniques, never copy footage.
set -eu
SCENE=${SCENE:-0.12}
USAGE="usage: breakdown.sh <video> [out dir] [--shots N,M,...|all] [--range A-B [--crop W:H:X:Y]]"
IN=${1:?$USAGE}; shift
NAME=$(basename "${IN%.*}")
OUT="$(dirname "$0")/../../research/$NAME"
case "${1:-}" in ""|--*) ;; *) OUT=$1; shift ;; esac
SHOTS=""; RANGE=""; CROP=""
while [ $# -gt 0 ]; do
  case "$1" in
    --shots) SHOTS=${2:?$USAGE}; shift 2 ;;
    --range) RANGE=${2:?$USAGE}; shift 2 ;;
    --crop) CROP=${2:?$USAGE}; shift 2 ;;
    *) echo "$USAGE" >&2; exit 2 ;;
  esac
done
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
FPS=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$IN" | LC_ALL=C awk -F/ '{printf "%.3f", $1/($2?$2:1)}')
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")

# contact sheet of one shot: shot number, start, length
shot_sheet() {
  local n start len
  n=$(printf '%02d' "$1"); start=$2; len=$3
  ffmpeg -nostdin -v error -y -ss "$start" -t "$len" -i "$IN" -vf "select='not(mod(n\,3))',scale=480:-2,drawtext=text='%{eif\:n*3+$(LC_ALL=C awk -v p="$start" -v f="$FPS" 'BEGIN{printf "%d", p*f}')\:d}':x=8:y=8:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.6,tile=4x6:padding=4" "$OUT/shot-$n-%d.jpg" 2>/dev/null || true
}

# sheets on request, from an existing breakdown
if [ -n "$SHOTS$RANGE" ] && [ -f "$OUT/shots.txt" ]; then
  if [ -n "$SHOTS" ]; then
    LC_ALL=C awk -v want=",$SHOTS," '(want == ",all," || index(want, "," $1 ",")) {print $1, $2, $4}' "$OUT/shots.txt" \
      | while read -r n start len; do shot_sheet "$n" "$start" "$len"; echo "  shot $n: $OUT/shot-$(printf '%02d' "$n")-*.jpg"; done
  fi
  if [ -n "$RANGE" ]; then
    A=${RANGE%-*}; B=${RANGE#*-}
    STEP=$(LC_ALL=C awk -v a="$A" -v b="$B" -v f="$FPS" 'BEGIN{s=int((b-a)*f/48)+1; print s}')
    F0=$(LC_ALL=C awk -v a="$A" -v f="$FPS" 'BEGIN{printf "%d", a*f+0.5}')
    if [ -n "$CROP" ]; then VIEW="crop=$CROP"; COLS=2; else VIEW="scale=480:-2"; COLS=4; fi
    SHEET="$OUT/range-$A-$B${CROP:+-crop}.jpg"
    ffmpeg -nostdin -v error -y -ss "$A" -t "$(LC_ALL=C awk -v a="$A" -v b="$B" 'BEGIN{print b-a}')" -i "$IN" \
      -vf "select='not(mod(n\,$STEP))',$VIEW,drawtext=text='%{eif\:n*$STEP+$F0\:d}':x=6:y=6:fontsize=20:fontcolor=yellow:box=1:boxcolor=black@0.7,tile=${COLS}x$((48 / COLS)):padding=3" \
      -frames:v 1 "$SHEET"
    echo "  range $A-$B s, every $STEP. frame: $SHEET"
  fi
  exit 0
fi

ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames -show_entries format=duration -of default=nw=1 "$IN" > "$OUT/meta.txt"

# cuts
ffmpeg -nostdin -v error -i "$IN" -vf "select='gt(scene,$SCENE)',metadata=print:file=-" -an -f null - 2>/dev/null \
  | LC_ALL=C awk -F'pts_time:' '/pts_time/ {split($2,a," "); printf "%.3f\n", a[1]}' > "$OUT/cuts.txt" || true

# per-frame motion energy
ffmpeg -v error -i "$IN" -vf "scale=480:-2,format=gray,tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-" -an -f null - 2>/dev/null \
  | LC_ALL=C awk '/pts_time/ {split($0,a,"pts_time:"); t=a[2]+0} /YAVG/ {split($0,b,"="); printf "%d,%.3f,%.3f\n", n++, t, b[2]}' > "$OUT/motion.csv"
sed -i '1i frame,time,energy' "$OUT/motion.csv"

# second detector: a cut between similar-looking frames still shows as a one-frame spike in motion energy
python3 -I - "$OUT" <<'PY'
import csv, sys, pathlib
out = pathlib.Path(sys.argv[1])
rows = [(float(r["time"]), float(r["energy"])) for r in csv.DictReader(open(out / "motion.csv"))]
cuts = [float(x) for x in (out / "cuts.txt").read_text().split()]
for i in range(2, len(rows) - 2):
    t, e = rows[i]
    around = max(rows[i - 2][1], rows[i - 1][1], rows[i + 1][1], rows[i + 2][1])
    if e >= 6 and e > 4 * max(around, 0.5):
        cuts.append(t)
merged = []
for c in sorted(cuts):
    if not merged or c - merged[-1] > 0.1:
        merged.append(c)
(out / "cuts.txt").write_text("".join(f"{c:.3f}\n" for c in merged))
PY

# shots: boundaries = 0, cuts, end
LC_ALL=C awk -v d="$DUR" 'BEGIN{p=0} {if ($1 > p) {printf "%d %.3f %.3f %.3f\n", ++n, p, $1, $1-p; p=$1}} END{printf "%d %.3f %.3f %.3f\n", ++n, p, d, d-p}' "$OUT/cuts.txt" > "$OUT/shots.txt"
SHOT_COUNT=$(wc -l < "$OUT/shots.txt")
rm -f "$OUT"/shot-*.jpg
SHORT=$(LC_ALL=C awk -v d="$DUR" 'BEGIN{print (d <= 30) ? 1 : 0}')
if [ "$SHORT" = 1 ] || [ -n "$SHOTS" ]; then
  LC_ALL=C awk -v want=",${SHOTS:-all}," '(want == ",all," || index(want, "," $1 ",")) {print $1, $2, $4}' "$OUT/shots.txt" \
    | while read -r n start len; do shot_sheet "$n" "$start" "$len"; done
fi

# overview: the whole video in at most 3 pages of 48 tiles, one tile every 0.5 s or sparser
rm -f "$OUT"/overview*.jpg
EVERY=$(LC_ALL=C awk -v d="$DUR" 'BEGIN{s=d/144; s=(s <= 0.5) ? 0.5 : int(s * 2 + 0.999) / 2; print s}')
ffmpeg -nostdin -v error -y -i "$IN" -vf "fps=1/$EVERY,scale=384:-2,drawtext=text='%{pts\:hms}':x=6:y=6:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6,tile=6x8:padding=4" "$OUT/overview-%d.jpg" 2>/dev/null || true

# motion curve plot (python3 stdlib only: writes an SVG, converted with ffmpeg if possible)
python3 -I - "$OUT" <<'PY'
import csv, sys, pathlib
out = pathlib.Path(sys.argv[1])
rows = list(csv.DictReader(open(out / "motion.csv")))
cuts = [float(x) for x in (out / "cuts.txt").read_text().split()] if (out / "cuts.txt").exists() else []
if rows:
    W, H, pad = 1800, 420, 40
    tmax = max(float(r["time"]) for r in rows) or 1
    emax = max(float(r["energy"]) for r in rows) or 1
    pts = " ".join(f"{pad + float(r['time']) / tmax * (W - 2 * pad):.1f},{H - pad - float(r['energy']) / emax * (H - 2 * pad):.1f}" for r in rows)
    lines = "".join(f'<line x1="{pad + c / tmax * (W - 2 * pad):.1f}" y1="{pad}" x2="{pad + c / tmax * (W - 2 * pad):.1f}" y2="{H - pad}" stroke="#d33" stroke-dasharray="4 4"/>' for c in cuts)
    ticks = "".join(f'<text x="{pad + s / tmax * (W - 2 * pad):.1f}" y="{H - 12}" font-size="14" fill="#555">{s}s</text>' for s in range(0, int(tmax) + 1, max(1, int(tmax) // 20 or 1)))
    (out / "motion.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"><rect width="100%" height="100%" fill="#fff"/>{lines}<polyline points="{pts}" fill="none" stroke="#007A55" stroke-width="1.5"/>{ticks}</svg>')
PY
if command -v rsvg-convert >/dev/null 2>&1; then rsvg-convert "$OUT/motion.svg" -o "$OUT/motion.png"; fi

echo "breakdown: $OUT"
echo "  $(wc -l < "$OUT/cuts.txt") cuts, $SHOT_COUNT shots, $(ls "$OUT"/overview-*.jpg 2>/dev/null | wc -l) overview pages (a tile every ${EVERY}s), $(ls "$OUT"/shot-*.jpg 2>/dev/null | wc -l) shot sheet pages, fps $FPS, ${DUR}s"
[ "$SHORT" = 0 ] && [ -z "$SHOTS" ] && echo "  shot sheets on request: breakdown.sh <video> $OUT --shots 3,7  or  --range 40.3-41.7 [--crop W:H:X:Y]"
[ -n "$RANGE" ] && exec bash "$0" "$IN" "$OUT" --range "$RANGE" ${CROP:+--crop "$CROP"}
exit 0
