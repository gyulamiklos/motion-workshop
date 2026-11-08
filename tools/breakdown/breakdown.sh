#!/usr/bin/env bash
# Motion breakdown of a reference video: the raw material for reverse-engineering a technique.
# Usage: tools/breakdown/breakdown.sh <video file> [out dir]
# Writes into the out dir (default: research/<video name>/):
#   meta.txt          resolution, fps, duration
#   cuts.txt          detected cuts (seconds); scene threshold SCENE (default 0.12; raise it for footage with lots of motion)
#   shot-NN-P.jpg     contact sheets per shot (24 tiles a page): every 3rd frame, frame numbers burned in
#   motion.csv        per-frame motion energy (mean absolute difference to the previous frame, 0–255)
#   motion.png        the motion curve with the cuts marked: easing and holds read off its shape
#   overview.jpg      one frame every 0.5 s, for the whole video
# Reference videos stay local (research/ is git-ignored): we re-implement techniques, never copy footage.
set -eu
SCENE=${SCENE:-0.12}
IN=${1:?usage: breakdown.sh <video> [out dir]}
NAME=$(basename "${IN%.*}")
OUT=${2:-"$(dirname "$0")/../../research/$NAME"}
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)

ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames -show_entries format=duration -of default=nw=1 "$IN" > "$OUT/meta.txt"
FPS=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$IN" | LC_ALL=C awk -F/ '{printf "%.3f", $1/($2?$2:1)}')
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")

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
LC_ALL=C awk -v d="$DUR" 'BEGIN{print 0} {print $1} END{print d}' "$OUT/cuts.txt" > "$OUT/.bounds"
i=0
prev=""
while read -r b; do
  if [ -n "$prev" ]; then
    i=$((i + 1))
    n=$(printf '%02d' "$i")
    len=$(LC_ALL=C awk -v a="$prev" -v b="$b" 'BEGIN{printf "%.3f", b-a}')
    ffmpeg -nostdin -v error -y -ss "$prev" -t "$len" -i "$IN" -vf "select='not(mod(n\,3))',scale=480:-2,drawtext=text='%{eif\:n*3+$(LC_ALL=C awk -v p="$prev" -v f="$FPS" 'BEGIN{printf "%d", p*f}')\:d}':x=8:y=8:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.6,tile=4x6:padding=4" "$OUT/shot-$n-%d.jpg" 2>/dev/null || true
  fi
  prev=$b
done < "$OUT/.bounds"
rm -f "$OUT/.bounds"

# overview, one frame every 0.5 s
ffmpeg -v error -y -i "$IN" -vf "fps=2,scale=384:-2,drawtext=text='%{pts\:hms}':x=6:y=6:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6,tile=6x8:padding=4" -frames:v 1 "$OUT/overview.jpg" 2>/dev/null || true

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
echo "  $(wc -l < "$OUT/cuts.txt") cuts, $(ls "$OUT"/shot-*.jpg 2>/dev/null | wc -l) shot sheet pages, fps $FPS, ${DUR}s"
