# Crowd: six striped figures stand in a foggy floor grid, turn accent on the beat, then copies of the same six meshes
# fill the floor (6 -> 60 -> 600 -> thousands) while the camera falls back and up to show the scale.
# Own content; the grammar is the line-3D "reveal of scale" (recipes/_principles.md, technique 10 and 17).
#
#   scripts/blender.sh -b --factory-startup -P recipes/line3d/blender/crowd.py -- --out DIR [--pick 30,120] [--open]
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "blender"))
import kit
from kit import b3, span, WHITE

A = kit.args({"seed": 9})
DUR, SEED = 5.6, A.seed

# ---------------------------------------------------------------- beats (s)
T_BORN = [0.25 + i * 0.13 for i in range(6)]       # the six arrive one by one
T_ACC = 1.35                                       # all six turn accent on the beat
T_GEN = [1.65, 1.95, 2.25]                         # 6 -> 60 -> 600 -> all
RIPPLE = 0.22                                      # each generation spreads outward over this long
T_REVEAL, D_REVEAL = 1.55, 1.9                     # the camera falls back and up

cam_at = kit.camera_rig([
    dict(t=0, pos=[0, 1.05, 5.4], dir=[0, -2.5], fov=38),
    dict(t=T_REVEAL, pos=[0, 1.1, 4.6], dir=[0, -3], fov=38, ease="sine.inOut"),
    dict(t=DUR, pos=[0.5, 8.2, 13.0], dir=[1.5, -26], fov=45, ease="sine.inOut"),   # one move that settles, no stop and restart
], amp=0.03, seed=SEED)

st = kit.Stage(background="#0a090c", samples=A.samples, shutter=0.5, bloom=0.7, volumetric_end=80)
FLOOR = kit.emit("floor", fog=(4.0, 40.0, 0.0))

# ---------------------------------------------------------------- six figures, as distance fields
def figure(v):
    H, sw = v.get("h", 1.72), v.get("sw", 0.2)
    hy = H - 0.13
    parts = [
        kit.sd_circle((0, hy), 0.112 * v.get("head", 1.0)),
        kit.sd_capsule((0, H - 0.26), (0, H - 0.33), 0.05),
        kit.sd_capsule((-sw, H - 0.42), (sw, H - 0.42), 0.07),             # shoulders
        kit.sd_capsule((0, 0.98), (0, H - 0.47), 0.165 * v.get("body", 1.0)),
        kit.sd_capsule((-sw - 0.02, H - 0.44), (-sw - 0.05, 0.84), 0.052),  # arms
        kit.sd_capsule((sw + 0.02, H - 0.44), (sw + 0.05, 0.84), 0.052),
        kit.sd_capsule((-0.095, 0.86), (-0.1, 0.05), 0.07),                 # legs
        kit.sd_capsule((0.095, 0.86), (0.1, 0.05), 0.07),
    ]
    hair = v.get("hair")
    if hair == "bun": parts.append(kit.sd_circle((0, H + 0.03), 0.065))
    if hair == "tail": parts.append(kit.sd_capsule((0.05, hy + 0.03), (0.15, hy - 0.22), 0.05))
    if hair == "long": parts.append(kit.sd_capsule((0, hy + 0.01), (0, hy - 0.26), 0.135))
    if hair == "cap": parts.append(kit.sd_capsule((-0.06, hy + 0.08), (0.2, hy + 0.08), 0.03))
    if v.get("skirt"): parts.append(kit.sd_capsule((0, 0.95), (0, 0.6), 0.23))
    return kit.sd_union(parts, k=0.035)

VARIANTS = [
    dict(h=1.78, sw=0.21, hair="cap"),
    dict(h=1.66, sw=0.18, hair="long", skirt=True),
    dict(h=1.74, sw=0.2),
    dict(h=1.62, sw=0.17, hair="bun", body=0.92),
    dict(h=1.82, sw=0.23, body=1.08),
    dict(h=1.68, sw=0.18, hair="tail"),
]
meshes = [kit.shape_mesh(f"face_{i + 1:02d}", figure(v), (-0.45, -0.02, 0.45, 1.95)) for i, v in enumerate(VARIANTS)]
STRIPE = kit.scanline("scanline", freq=15.0, duty=0.4, fog=(6.0, 38.0, 0.0))
for m in meshes:
    m.materials.append(STRIPE)

# ---------------------------------------------------------------- where they stand
r = kit.mulberry32(SEED)
HERO_X = [-2.5 + i for i in range(6)]
pts, born, var, scl, rot, shade, accent = [], [], [], [], [], [], []
for i, x in enumerate(HERO_X):
    pts.append([x, 0, 0]); born.append(T_BORN[i]); var.append(i); scl.append(1.0); rot.append(0.0)
    shade.append(1.0); accent.append(1.0)
crowd = []
for iz in range(-80, 12):
    for ix in range(-42, 43):
        x, z = ix * 0.78 + (r() - 0.5) * 0.36, iz * 0.95 + (r() - 0.5) * 0.4
        if abs(x) < 3.2 and abs(z) < 0.75: continue      # the six stand alone in the front row
        if z > 2.6: continue                              # keep the camera's first frames clear
        front = 30 if z > -0.8 and abs(x) < 7 else 0      # between the camera and the six: only the last wave
        crowd.append((math.hypot(x, z * 0.8) + front, x, z))
crowd.sort()
gens = [54, 540, len(crowd) - 594]                         # 6 + 54 = 60, + 540 = 600, then the rest
k = 0
for g, n in enumerate(gens):
    for j in range(n):
        _, x, z = crowd[k]; k += 1
        pts.append([x, 0, z])
        born.append(T_GEN[g] + RIPPLE * j / n)
        var.append(int(r() * 6)); scl.append(0.93 + r() * 0.14); rot.append((r() - 0.5) * 0.35)
        shade.append(0.55 + 0.45 * r()); accent.append(0.0)
TOTAL = len(pts)
people = kit.instancer(st, "people", pts, meshes, {"born": born, "var": var, "scl": scl, "rot": rot,
                                                   "shade": shade, "accent": accent})

# ---------------------------------------------------------------- the floor: a grid fading into fog
lines = [[[x, 0, -80], [x, 0, 12]] for x in range(-40, 41, 2)] + [[[-40, 0, z], [40, 0, z]] for z in range(-80, 13, 2)]
floor = kit.poly(st, "floor", lines, FLOOR, radius=kit.LINE_R * 1.3)
kit.set_color(floor, WHITE, 0.0)
glow = kit.point_light(st, "glow", kit.lin("#ff2d8c"), radius=1.5)  # the six light the floor when they turn
glow.location = b3([0, 0.9, 0.8])
kit.haze(st, (60, 6, 70), center=(0, 2.9, -25), density=0.012)

# ---------------------------------------------------------------- pose(t)
def pose(t):
    st.set_camera(*cam_at(t))
    kit.set_time(people, t)
    kit.time_node(STRIPE).outputs[0].default_value = t
    acc = kit.pulse(t, T_ACC, attack=0.05, half=0.18)  # fills, then cools to a held trace
    hold = 0.22 if t >= T_ACC else 0.0
    STRIPE.node_tree.nodes["ACC"].outputs[0].default_value = max(acc, hold * (1 - span(t, T_GEN[2], 1.2)))
    glow.data.energy = 220 * acc + 25 * hold
    kit.draw(floor, span(t, 0.0, 1.0, "power2.out"))
    kit.set_color(floor, WHITE, 0.45)

def anchors(t):
    return {
        "faces": [st.project([x, -0.12, 0]) for x in HERO_X],
        "count": sum(1 for b in born if b <= t),
    }

kit.run(st, A, DUR, pose, anchors)
