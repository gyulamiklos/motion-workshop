# Skybox room, rendered in Blender (Eevee): the same beats, camera and geometry as recipes/line3d/skybox-room.html,
# with haze lit by the nodes, motion blur on every frame and bloom. The HUD stays in HTML; proj.json gives it the
# screen position of each anchor per frame.
#
#   scripts/blender.sh -b --factory-startup -P recipes/line3d/blender/skybox_room.py -- --out DIR [--pick 30,200] [--open]
#
# Points are written in the Three.js frame of the line-3D kit; kit.b3() converts them.
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "blender"))
import kit
from kit import b3, clamp01, mix3, pulse, span, WHITE

A = kit.args({"line": "every request climbs until it meets the limit, and the limit holds", "seed": 5})
DUR, SEED = 8.6, A.seed
ACCENT = kit.lin("#ff2d8c")

# ---------------------------------------------------------------- beats (s), as in the HTML block
T_WHIP, D_WHIP = 1.9, 0.4
T_NODE = [2.65 + i * 0.65 for i in range(4)]
T_BACK, D_BACK = 5.15, 0.45
T_RUN, D_RUN = 5.75, 1.5
T_HIT = T_RUN + D_RUN

cam_at = kit.camera_rig([
    dict(t=0, pos=[0, 0.1, 4.2], dir=[0, 0], fov=50),
    dict(t=T_WHIP, pos=[0.2, 0.0, 2.4], dir=[7, 0], roll=-0.05, fov=50, ease="sine.inOut"),
    dict(t=T_WHIP + D_WHIP, pos=[-1.8, -0.4, 2.8], dir=[-46, 1], roll=0.78, fov=50, ease="power4.inOut"),
    dict(t=T_BACK, pos=[-1.6, -0.35, 2.4], dir=[-44, 1], roll=0.6, fov=50, ease="sine.out"),
    dict(t=T_BACK + D_BACK, pos=[-1.4, -0.3, 1.4], dir=[-14, -1.5], roll=-0.04, fov=46, ease="power4.inOut"),
    dict(t=T_HIT, pos=[-1.1, -0.2, 0.8], dir=[-12.5, -1], roll=-0.03, fov=46, ease="sine.inOut"),
    dict(t=T_HIT + 0.14, pos=[-0.6, 0.45, -1.2], dir=[-12, 11], roll=0.18, fov=42, ease="power3.out"),
    dict(t=DUR, pos=[-0.55, 0.5, -1.45], dir=[-13, 11.5], roll=0.14, fov=42, ease="sine.out"),
], amp=0.025, seed=SEED)

st = kit.Stage(background="#121116", samples=A.samples, shutter=0.5)  # 180°: the whip smears, still reads
LINE, GLOW, DUST = kit.emit("line"), kit.emit("glow"), kit.emit("dust", attr="bright")
R = kit.LINE_R

# ---------------------------------------------------------------- the room
RW, RH, RD = 8, 4.5, 10
w2, h2, d2 = RW / 2, RH / 2, RD / 2
V = [[-w2, -h2, -d2], [w2, -h2, -d2], [w2, h2, -d2], [-w2, h2, -d2], [-w2, -h2, d2], [w2, -h2, d2], [w2, h2, d2], [-w2, h2, d2]]
EDGES = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]]
edges = [kit.poly(st, f"edge{k}", [[V[a], V[b]]], LINE) for k, (a, b) in enumerate(EDGES)]

def wall_grid(div=9):
    step, out = (2 * h2) / div, []
    def lines(a0, a1, b0, b1, put):
        a = a0 + step
        while a < a1 - 1e-6: out.append([put(a, b0), put(a, b1)]); a += step
        b = b0 + step
        while b < b1 - 1e-6: out.append([put(a0, b), put(a1, b)]); b += step
    lines(-w2, w2, -h2, h2, lambda a, b: [a, b, -d2])
    lines(-d2, d2, -h2, h2, lambda a, b: [-w2, b, a])
    lines(-d2, d2, -h2, h2, lambda a, b: [w2, b, a])
    lines(-w2, w2, -d2, d2, lambda a, b: [a, -h2, b])
    lines(-w2, w2, -d2, d2, lambda a, b: [a, h2, b])
    return out
grid = kit.poly(st, "grid", wall_grid(), LINE, radius=R * 0.8)

def scatter_walls(n, seed):  # the line-3D kit's scatter "walls", same seed
    r, pts = kit.mulberry32(seed), []
    areas = [w2 * h2, d2 * h2, d2 * h2, w2 * d2, w2 * d2]
    tot = sum(areas)
    for _ in range(n):
        a, b, inn = r() * 2 - 1, r() * 2 - 1, 0.995
        pick, k = r() * tot, 0
        while pick > areas[k]: pick -= areas[k]; k += 1
        pts.append([[a * w2, b * h2, -d2 * inn], [-w2 * inn, b * h2, a * d2], [w2 * inn, b * h2, a * d2],
                    [a * w2, -h2 * inn, b * d2], [a * w2, h2 * inn, b * d2]][k])
    return pts
dust_pts = scatter_walls(5200, SEED)
rr = kit.mulberry32(SEED + 11)
bright = [0.25 + 0.75 * rr() ** 2.2 for _ in dust_pts]  # most dust is dim, a few points are stars
dust = kit.point_cloud(st, "dust", dust_pts, DUST, [0.006 + 0.010 * b for b in bright], bright)
kit.haze(st, (RW * 0.99, RH * 0.99, RD * 0.99))

# ---------------------------------------------------------------- nodes on the east wall
NODE_P = [[4, 0.9, -2.2], [4, -0.2, -3.6], [4, 1.3, -4.3], [4, -1.05, -2.9]]
ring_pts = [[0, math.cos(j / 96 * 2 * math.pi), math.sin(j / 96 * 2 * math.pi)] for j in range(97)]
nodes = []
for i, p in enumerate(NODE_P):
    core = kit.sphere(st, f"node{i}", 0.032, GLOW)
    core.location = b3([p[0] - 0.04, p[1], p[2]])
    rg = kit.poly(st, f"ring{i}", [ring_pts], GLOW, radius=R * 0.9)
    rg.location = b3([p[0] - 0.02, p[1], p[2]])
    li = kit.point_light(st, f"nodelight{i}", ACCENT)
    li.location = b3([p[0] - 0.25, p[1], p[2]])
    nodes.append((core, rg, li))

# ---------------------------------------------------------------- the graph on the back wall
GO = [-3.1, -1.75, -d2 + 0.01]
def g3(x, y, z=0.0): return [GO[0] + x, GO[1] + y, GO[2] + z]
GW, CAP, X_HIT = 6.4, 3.0, 3.5
def gy(x): return max(0.05, CAP * (1 - math.cos((x / X_HIT) ** 1.6 * math.pi / 2)) if x < X_HIT else CAP)
CP = [(GW * i / 2000, gy(GW * i / 2000)) for i in range(2001)]
path = kit.Path2D(CP)
U_HIT = next(path.s[i] for i in range(len(CP)) if CP[i][1] >= CAP - 1e-3) / path.length

axes = kit.poly(st, "axes", [[g3(0, CAP + 0.5), g3(0, 0), g3(GW, 0)]], LINE)
hatch, c = [], -0.32
while c < GW:
    x0, x1 = max(0, c), min(GW, c + 0.32)
    if x1 > x0: hatch.append([g3(x0, CAP + x0 - c), g3(x1, CAP + x1 - c)])
    c += 0.09
band = kit.poly(st, "band", hatch, LINE, radius=R * 0.8)
capl = kit.poly(st, "cap", [[g3(0, CAP), g3(GW, CAP)]], GLOW)
curve = kit.poly(st, "curve", [[g3(x, y, 0.005) for x, y in CP[::8]] + [g3(*CP[-1], 0.005)]], LINE)
drop = kit.poly(st, "drop", [[[0, 0, 0], [0, 1, 0]]], GLOW)
head = kit.sphere(st, "head", 0.026, GLOW)
head_l = kit.point_light(st, "headlight", ACCENT)
words = kit.text_on_path(st, A.line, path, g3, GLOW, size=0.21, font=kit.font(), start=0.02, offset=0.35)

AX_P = [[-3.6, 1.9, -d2], [w2, 1.9, -1.2], [1.4, -h2, -2.2]]

# ---------------------------------------------------------------- pose(t): everything from t
state = {}

def pose(t):
    st.set_camera(*cam_at(t))
    st.background(kit.flash(t, T_HIT, lift=0.32, half=0.06) * 0.1)
    # the room draws on in the first second; the dust is there from the start
    de = span(t, 0.0, 0.9, "power2.out")
    for k, ob in enumerate(edges):
        kit.draw(ob, clamp01((de - k / 12) * 12)); kit.set_color(ob, WHITE, 0.85)
    kit.draw(grid, span(t, 0.3, 1.0, "power2.out")); kit.set_color(grid, WHITE, 0.07)
    kit.set_color(dust, WHITE, 1.1 * span(t, 0, 0.6))
    for i, (core, rg, li) in enumerate(nodes):
        on, pu = t >= T_NODE[i], pulse(t, T_NODE[i])
        kit.show(core, on, 1 + 1.2 * pulse(t, T_NODE[i], half=0.05))
        kit.set_color(core, mix3(WHITE, ACCENT, 0.35 + 0.65 * pu), 3.0 + 9.0 * pu)
        k = span(t, T_NODE[i], 0.5, "expo.out")  # a reticle opens around the new node and collapses to it
        kit.show(rg, on and k < 1, 0.05 + 0.7 * math.sin(k * math.pi))
        kit.set_color(rg, mix3(WHITE, ACCENT, pu), 0.9 * (1 - k) * (1 + 3 * pu))
        li.data.energy = (12 + 140 * pu) if on else 0.0
    # the graph: the head runs up the curve and meets the cap, then creeps along it
    run = span(t, T_RUN, D_RUN, "power2.in")
    uu = min(0.995, min(U_HIT, run * U_HIT) + max(0.0, t - T_HIT) * 0.06)
    (hx, hy), _ = path.at(uu * path.length)
    g_on = span(t, T_BACK - 0.2, 0.6, "power2.out")
    hit_p, hold = pulse(t, T_HIT, half=0.1), (1.0 if t >= T_HIT else 0.0)
    kit.draw(axes, g_on); kit.set_color(axes, WHITE, 0.7)
    kit.draw(band, g_on); kit.set_color(band, mix3(WHITE, ACCENT, max(hit_p, 0.6 * hold)), 0.35 * (1 + 2 * hit_p + 1.5 * hold))
    kit.draw(capl, g_on); kit.set_color(capl, mix3(WHITE, ACCENT, max(hit_p, hold)), 1.0 + 5 * hit_p + 1.5 * hold)
    running = t >= T_RUN
    kit.draw(curve, uu if running else 0)
    head.location = b3(g3(hx, hy, 0.02))
    kit.show(head, running, 1 + 1.6 * pulse(t, T_HIT, half=0.08))
    kit.set_color(head, mix3(WHITE, ACCENT, 0.3 + 0.7 * hit_p), 5 + 10 * hit_p)
    head_l.location = b3(g3(hx, hy, 0.3))
    head_l.data.energy = (20 + 30 * min(1, run * 2) + 100 * hit_p) if running else 0.0
    drop.location = b3(g3(hx, 0, 0.004))
    drop.scale = (1, 1, max(0.001, hy)) if running else (0, 0, 0)
    kit.set_color(drop, mix3(WHITE, ACCENT, 0.5 + 0.5 * hold), 0.6 * (1 + hold))
    # words: before the head white, the current word in the accent, the next ones fade in ahead of it
    vis, head_u = t >= T_RUN - 0.25, (uu if running else -1)
    ahead_a, window = 0.4 * span(t, T_RUN - 0.25, 0.25), 0.22
    cur = max([wi for wi, (_, ws) in enumerate(words) if ws <= head_u], default=-1)
    for wi, (ob, ws) in enumerate(words):
        if wi > cur:
            a = ahead_a * clamp01(1 - (ws - head_u) / window)
            kit.show(ob, vis and a > 0.002); kit.set_color(ob, WHITE, a)
        else:
            kit.show(ob, vis); kit.set_color(ob, ACCENT if wi == cur else WHITE, 6.0 if wi == cur else 1.0)
    state["hy"] = hy

def anchors(t):
    return {
        "nodes": [st.project(p) for p in NODE_P],
        "axes": [st.project(p) for p in AX_P],
        "band": st.project(g3(0.12, CAP + 0.16)),
        "head": round(state["hy"] / CAP, 4),
    }

kit.run(st, A, DUR, pose, anchors)
