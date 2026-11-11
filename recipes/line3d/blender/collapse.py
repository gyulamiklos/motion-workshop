# Collapse: wire crates, a faceted tree, a panel and an orb stand on a floor grid; on the beat the stand breaks into
# pieces, a burst kicks them, and everything falls and shatters into rubble with loose shards (Blender rigid bodies,
# cached sim). Own content; the grammar is the "everything gives way" beat of the line-3D reference
# (recipes/_principles.md): the camera keeps one slow move through it and only shakes on the hit.
#
#   scripts/blender.sh -b --factory-startup -P recipes/line3d/blender/collapse.py -- --out DIR [--pick 30,150] [--open]
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "blender"))
import bmesh, bpy
from mathutils import Matrix, Vector
import kit
from kit import b3, clamp01, mix3, span, WHITE

A = kit.args({"seed": 4, "kick": 14.0})
DUR, SEED = 4.6, A.seed
FPS = kit.FPS
NFR = int(round(DUR * FPS))
ACCENT = kit.lin("#ff2d8c")

T_BREAK = 2.0                                      # the stand gives way
F_BREAK = int(round(T_BREAK * FPS))
SPREAD = 0.32                                      # the release ripples outward from the top crate over this long

cam_at = kit.camera_rig([
    dict(t=0, pos=[0.9, 1.7, 6.8], dir=[1.5, -5.5], fov=38),
    dict(t=DUR, pos=[0.0, 0.85, 4.3], dir=[-0.5, -1.0], fov=42, ease="sine.inOut"),
], amp=0.02, seed=SEED)

st = kit.Stage(background="#0a090c", samples=A.samples, shutter=0.5, bloom=0.8, volumetric_end=40)
LINE = kit.emit("line", fog=(5.0, 30.0, 0.15))
r = kit.mulberry32(SEED)

# ---------------------------------------------------------------- the things that stand (Three.js coordinates)
def box_mesh(w, h, d, pos, yaw, tri=False):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(w, d, h), verts=bm.verts[:])
    bmesh.ops.transform(bm, matrix=Matrix.Translation(b3(pos)) @ Matrix.Rotation(yaw, 4, "Z"), verts=bm.verts[:])
    if tri: bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("m"); bm.to_mesh(me); bm.free()
    return me

def ico_mesh(rad, pos, sub=1):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=rad)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(b3(pos)), verts=bm.verts[:])
    me = bpy.data.meshes.new("m"); bm.to_mesh(me); bm.free()
    return me

# name, mesh, braced copy (the look before the break), pieces, accent share
THINGS = [
    ("crate_a", box_mesh(1.0, 1.0, 1.0, [-0.35, 0.5, 0], 0.15), box_mesh(1.0, 1.0, 1.0, [-0.35, 0.5, 0], 0.15, True), 14, 0.15),
    ("crate_b", box_mesh(0.7, 0.7, 0.7, [-0.32, 1.35, 0], 0.55), box_mesh(0.7, 0.7, 0.7, [-0.32, 1.35, 0], 0.55, True), 10, 0.5),
    ("panel",   box_mesh(1.7, 1.05, 0.06, [-2.0, 0.95, -0.4], -0.35), box_mesh(1.7, 1.05, 0.06, [-2.0, 0.95, -0.4], -0.35), 12, 0.2),
    ("trunk",   box_mesh(0.14, 1.0, 0.14, [1.5, 0.5, -0.2], 0.0), box_mesh(0.14, 1.0, 0.14, [1.5, 0.5, -0.2], 0.0), 5, 0.0),
    ("crown",   ico_mesh(0.7, [1.5, 1.55, -0.2]), ico_mesh(0.7, [1.5, 1.55, -0.2]), 22, 0.35),
]
IMPACT = b3([-0.32, 1.4, 0])

kit.rigid_world(st, NFR, gravity=14.0)
ground = bpy.data.objects.new("ground", bpy.data.meshes.new("ground"))
gb = bmesh.new(); bmesh.ops.create_cube(gb, size=1.0); bmesh.ops.scale(gb, vec=(60, 60, 1), verts=gb.verts[:])
bmesh.ops.translate(gb, vec=(0, 0, -0.5), verts=gb.verts[:]); gb.to_mesh(ground.data); gb.free()
st.link(ground); ground.hide_render = True
kit.rigid(ground, passive=True, shape="BOX", friction=0.7, bounce=0.2)

intact, cells = [], []            # intact[i]: the braced solid; cells: (object, accent weight, kind)
for k, (name, me, braced, n, acc) in enumerate(THINGS):
    ob = kit.wire_solid(st, name, braced, LINE)
    intact.append(ob)
    for ci, (c, cm) in enumerate(kit.fracture(me, n, SEED + k * 11)):
        co = kit.wire_solid(st, f"{name}_{ci}", cm, LINE, wire=0.009)
        co.location = c
        vol = sum(p.area for p in cm.polygons) * 0.1
        kit.rigid(co, mass=max(0.2, vol * 40), friction=0.6, bounce=0.3)
        d = (c - IMPACT).length
        kit.hold_until(co, F_BREAK + int(round((SPREAD * clamp01(d / 3.2) + r() * 0.05) * FPS)))
        kit.set_color(co, WHITE, 0.0)
        cells.append((co, 1.0 if r() < acc else 0.0))
        co["accent"] = cells[-1][1]

# the orb stands alone: one body, no cells
orb = kit.wire_solid(st, "orb", ico_mesh(0.2, [0.75, 0.2, 0.9], 1), LINE, wire=0.009)
kit.rigid(orb, mass=1.0, shape="SPHERE", bounce=0.5)
kit.hold_until(orb, F_BREAK + 4)

# loose shards: little tetrahedra inside the pieces, invisible until the break; they collide with the ground and each
# other only, so they fly out of the rubble instead of fighting the pieces
DEBRIS = []
for i in range(90):
    c, _ = cells[int(r() * len(cells))][0].location, None
    s = 0.04 + r() * 0.06
    me = bpy.data.meshes.new("shard")
    me.from_pydata([(s, s, s), (s, -s, -s), (-s, s, -s), (-s, -s, s)], [], [(0, 1, 2), (0, 3, 1), (0, 2, 3), (1, 3, 2)])
    me.update()
    sh = kit.wire_solid(st, f"shard_{i}", me, LINE, wire=0.006)
    sh.location = c + Vector(((r() - 0.5) * 0.15, (r() - 0.5) * 0.15, (r() - 0.5) * 0.15))
    sh.rotation_euler = (r() * 6.28, r() * 6.28, r() * 6.28)
    kit.rigid(sh, mass=0.05, shape="CONVEX_HULL", friction=0.5, bounce=0.35, layer=1)
    kit.hold_until(sh, F_BREAK)
    kit.set_color(sh, WHITE, 0.0)
    DEBRIS.append(sh)

kit.burst(st, [-0.2, 0.5, 0.4], F_BREAK, A.kick, length=8, reach=4.5)
kit.simulate(st, NFR)

# ---------------------------------------------------------------- the floor and the light
lines = [[[x, 0, -30], [x, 0, 10]] for x in range(-20, 21, 2)] + [[[-20, 0, z], [20, 0, z]] for z in range(-30, 11, 2)]
floor = kit.poly(st, "floor", lines, kit.emit("floor", fog=(4.0, 30.0, 0.0)), radius=kit.LINE_R * 1.3)
kit.set_color(floor, WHITE, 0.0)
glow = kit.point_light(st, "glow", ACCENT, radius=1.5)
glow.location = b3([-0.2, 1.0, 1.2])
kit.haze(st, (30, 6, 30), center=(0, 2.5, -4), density=0.01)

# ---------------------------------------------------------------- pose(t)
def shake(t):
    d = math.exp(-(t - T_BREAK) * 7.0) if t >= T_BREAK else 0.0
    return Vector((math.sin(t * 61.0), math.sin(t * 47.0 + 1.3), math.sin(t * 53.0 + 2.1))) * 0.045 * d

def pose(t):
    pos, target, fov, roll = cam_at(t)
    sh = shake(t)
    st.set_camera(pos + sh, target + sh * 0.5, fov, roll)
    acc = kit.pulse(t, T_BREAK, attack=0.04, half=0.22)
    broken = t >= T_BREAK
    for i, ob in enumerate(intact):
        a = 0.9 * span(t, 0.2 + i * 0.12, 0.6, "power2.out")
        ob.hide_render = broken       # a black (alpha 0) wire would still hide what is behind it
        kit.set_color(ob, mix3(WHITE, ACCENT, acc), a)
    for ob, w in cells:
        ob.hide_render = not broken
        kit.set_color(ob, mix3(WHITE, ACCENT, max(acc, w * (1 - span(t, T_BREAK + 0.4, 2.5)) * 0.9)), 0.9 + 1.2 * acc)
    kit.set_color(orb, WHITE, 0.9 * span(t, 0.9, 0.6, "power2.out"))
    for sh_ in DEBRIS:
        sh_.hide_render = not broken
        kit.set_color(sh_, mix3(WHITE, ACCENT, acc), 0.8 + acc)
    glow.data.energy = 300 * acc
    st.background(kit.flash(t, T_BREAK, lift=0.3, half=0.07) * 0.1)
    kit.draw(floor, span(t, 0.0, 1.0, "power2.out"))
    kit.set_color(floor, WHITE, 0.4)

kit.run(st, A, DUR, pose)
