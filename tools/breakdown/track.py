#!/usr/bin/env python3
"""Measure one region of a video frame by frame, and compare two measurements.

Whole-frame motion energy (breakdown.sh) is drowned out by a busy background; this looks only at the
region where the move happens, and counts accent-coloured and near-white pixels in it.

  track.py measure <video> --roi W:H:X:Y [--from S] [--to S] [--accent '#ff2d8c'] > ref.csv
      time,accent,accent_right,bright,luma   (time: s from --from; accent/bright: share of the region's pixels, 0-1;
      accent_right: the rightmost accent pixel as a share of the width, -1 if none; luma: mean, 0-255)
  track.py compare ref.csv ours.csv [--tol 2]
      events in both (accent appears, accent or bright jumps up), matched in order; prints the difference
      in frames of the reference and exits 1 if any matched pair differs by more than --tol frames.
      Events past the end of the shorter list are listed, not failed: measure the same span to avoid them.

Measure both at the same frame rate (render ours at the reference's fps), with --from set so the move starts
at the same time in both measurements; the regions may differ in size and place.
Python stdlib only; frames come from ffmpeg.
"""
import argparse
import colorsys
import csv
import subprocess
import sys

MAX_W = 480
JUMP = 0.004  # a jump of 0.4% of the region's pixels between two frames is an event


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def measure(a):
    w, h, x, y = (int(v) for v in a.roi.split(":"))
    sw = min(w, MAX_W)
    sh = max(2, round(h * sw / w / 2) * 2)
    fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                          "-of", "csv=p=0", a.video], capture_output=True, text=True, check=True).stdout.strip()
    num, _, den = fps.partition("/")
    fps = float(num) / float(den or 1)
    cmd = ["ffmpeg", "-nostdin", "-v", "error"]
    if a.start:
        cmd += ["-ss", str(a.start)]
    if a.to is not None:
        cmd += ["-t", str(a.to - (a.start or 0))]
    cmd += ["-i", a.video, "-vf", f"crop={w}:{h}:{x}:{y},scale={sw}:{sh}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    ah = colorsys.rgb_to_hsv(*hex_rgb(a.accent))[0]
    size = sw * sh * 3
    out = csv.writer(sys.stdout)
    out.writerow(["time", "accent", "accent_right", "bright", "luma"])
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = 0
    while True:
        d = p.stdout.read(size)
        if len(d) < size:
            break
        acc = bright = 0
        right = -1
        luma = 0
        for i in range(0, size, 3):
            r, g, b = d[i] / 255, d[i + 1] / 255, d[i + 2] / 255
            hh, s, v = colorsys.rgb_to_hsv(r, g, b)
            luma += 0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2]
            if s > 0.5 and v > 0.6 and min(abs(hh - ah), 1 - abs(hh - ah)) < 0.06:
                acc += 1
                right = max(right, (i // 3) % sw)
            elif v > 0.85 and s < 0.15:
                bright += 1
        px = sw * sh
        out.writerow([f"{n / fps:.3f}", f"{acc / px:.5f}", f"{right / sw:.4f}" if right >= 0 else "-1",
                      f"{bright / px:.5f}", f"{luma / px:.1f}"])
        n += 1
    if p.wait() != 0:
        sys.exit("ffmpeg failed")


def events(path):
    rows = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(open(path))]
    ev = []
    first = next((r["time"] for r in rows if r["accent"] > 0), None)
    if first is not None:
        ev.append(("accent appears", first))
    for prev, r in zip(rows, rows[1:]):
        if r["bright"] - prev["bright"] > JUMP:
            ev.append(("bright jump", r["time"]))
        if prev["accent"] > 0 and r["accent"] - prev["accent"] > JUMP * 4:
            ev.append(("accent jump", r["time"]))
    step = (rows[-1]["time"] - rows[0]["time"]) / max(1, len(rows) - 1) if len(rows) > 1 else 1 / 30
    return ev, step


def compare(a):
    ref, step = events(a.ref)
    ours, _ = events(a.ours)
    bad = False
    for kind in ("accent appears", "bright jump", "accent jump"):
        r = [t for k, t in ref if k == kind]
        o = [t for k, t in ours if k == kind]
        if not r and not o:
            continue
        diffs = [round((y - x) / step) for x, y in zip(r, o)]
        print(f"{kind}: ref {len(r)}, ours {len(o)}; difference in frames: {diffs}")
        if len(r) != len(o):
            extra, who = (r, "ref") if len(r) > len(o) else (o, "ours")
            print(f"  unmatched in {who} at: {', '.join(f'{t:.3f}' for t in extra[len(diffs):])} s")
        if not diffs or any(abs(d) > a.tol for d in diffs):
            bad = True
    print("FAIL: outside" if bad else "OK: within", f"{a.tol} frames (at {1 / step:.0f} fps)")
    sys.exit(1 if bad else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("measure")
    m.add_argument("video")
    m.add_argument("--roi", required=True, help="W:H:X:Y in source pixels (ffmpeg crop order)")
    m.add_argument("--from", dest="start", type=float, default=0)
    m.add_argument("--to", type=float)
    m.add_argument("--accent", default="#ff2d8c")
    c = sub.add_parser("compare")
    c.add_argument("ref")
    c.add_argument("ours")
    c.add_argument("--tol", type=int, default=2)
    a = ap.parse_args()
    measure(a) if a.cmd == "measure" else compare(a)


if __name__ == "__main__":
    main()
