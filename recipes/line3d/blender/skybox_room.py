# Skybox room, rendered in Blender (Eevee): the same beats, camera and geometry as recipes/line3d/skybox-room.html,
# with real haze lit by the nodes, true motion blur and bloom. The HUD stays in HTML; this script also writes the
# screen position of every HUD anchor per frame (proj.json) so the HTML layer can follow the 3D world.
#
#   blender -b --factory-startup -P skybox_room.py -- --out DIR [--frames A-B] [--samples N] [--proj-only]
#
# Coordinates are written in the kit's Three.js frame (Y up, the camera looks down -Z) and converted with b3().
# A scene is a pure function of time: pose(t) sets everything from t, called from a frame-change handler, so
# motion-blur sub-frames see the true pose.
import argparse, json, math, os, sys
import bpy
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--frames", default="0-515")
ap.add_argument("--samples", type=int, default=48)
ap.add_argument("--proj-only", action="store_true")
ap.add_argument("--pick", default="")
ap.add_argument("--open", action="store_true", help="build the scene and leave it open in the Blender window")
ap.add_argument("--font", default="/usr/share/fonts/truetype/lato/Lato-Black.ttf")
args = ap.parse_args(argv)
OUT = os.path.abspath(args.out)
os.makedirs(os.path.join(OUT, "frames"), exist_ok=True)

FPS, DUR, W, H = 60, 8.6, 1920, 1080
SEED = 5
LINE = "every request climbs until it meets the limit, and the limit holds"

# ---------------------------------------------------------------- time helpers (as in assets/line3d.js)
def clamp01(x): return min(1.0, max(0.0, x))
def lerp(a, b, k): return a + (b - a) * k

def ease(name):
    if not name or name in ("none", "linear"): return lambda k: k
    fam, kind = name.split(".")
    if fam == "sine":
        return {"in": lambda k: 1 - math.cos(k * math.pi / 2), "out": lambda k: math.sin(k * math.pi / 2),
                "inOut": lambda k: -(math.cos(math.pi * k) - 1) / 2}[kind]
    if fam == "expo":
        f_in = lambda k: 0.0 if k <= 0 else 2 ** (10 * k - 10)
    else:
        p = int(fam[5:]) + 1  # GSAP power1 = quad, power2 = cubic ...
        f_in = lambda k: k ** p
    if kind == "in": return f_in
    if kind == "out": return lambda k: 1 - f_in(1 - k)
    return lambda k: f_in(2 * k) / 2 if k < 0.5 else 1 - f_in(2 * (1 - k)) / 2

def span(t, t0, dur, e=None):
    k = clamp01((t - t0) / dur)
    return ease(e)(k) if e else k

def pulse(t, t0, attack=0.06, half=0.025):
    if t < t0: return 0.0
    if t < t0 + attack: return ease("power2.out")((t - t0) / attack)
    return 0.5 ** ((t - t0 - attack) / half)

def flash(t, t0, lift=0.2, half=0.05):
    return 0.0 if t < t0 else lift * 0.5 ** ((t - t0) / half)

def mulberry32(seed):
    s = [seed & 0xFFFFFFFF]
    imul = lambda a, b: (a * b) & 0xFFFFFFFF
    def r():
        s[0] = (s[0] + 0x6D2B79F5) & 0xFFFFFFFF
        t = s[0]
        t = imul(t ^ (t >> 15), 1 | t)
        t = ((t + imul(t ^ (t >> 7), 61 | t)) & 0xFFFFFFFF) ^ t
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296
    return r

def drift(seed):
    r = mulberry32(seed)
    w = [0.21 + r() * 0.1, 0.37 + r() * 0.1, 0.61 + r() * 0.1]
    p = [r() * 6.28, r() * 6.28, r() * 6.28]
    return lambda t: (math.sin(t * w[0] * 6.283 + p[0]) * 0.55 + math.sin(t * w[1] * 6.283 + p[1]) * 0.3
                      + math.sin(t * w[2] * 6.283 + p[2]) * 0.15)

def camera_rig(keys, amp, seed):
    dx, dy, dz = drift(seed + 1), drift(seed + 2), drift(seed + 3)
    def at(t):
        i = 0
        while i < len(keys) - 1 and t >= keys[i + 1]["t"]: i += 1
        k0, k1 = keys[i], keys[min(i + 1, len(keys) - 1)]
        k = 0 if k1 is k0 or t <= k0["t"] else ease(k1.get("ease", "power2.inOut"))(clamp01((t - k0["t"]) / (k1["t"] - k0["t"])))
        pos = Vector(k0["pos"]).lerp(Vector(k1["pos"]), k)
        yaw, pitch = math.radians(lerp(k0["dir"][0], k1["dir"][0], k)), math.radians(lerp(k0["dir"][1], k1["dir"][1], k))
        target = pos + Vector((-math.sin(yaw) * math.cos(pitch), math.sin(pitch), -math.cos(yaw) * math.cos(pitch)))
        fov, roll = lerp(k0["fov"], k1["fov"], k), lerp(k0.get("roll", 0), k1.get("roll", 0), k)
        pos += Vector((dx(t) * amp, dy(t) * amp, dz(t) * amp * 0.5))
        target += Vector((dy(t + 3) * amp * 0.4, dz(t + 5) * amp * 0.4, 0))
        return pos, target, fov, roll
    return at

def b3(v):  # Three.js (x, y up, z toward the viewer) -> Blender (x, y forward, z up)
    return Vector((v[0], -v[2], v[1]))

def lin(hexs):  # an sRGB hex as linear RGB (the Standard view transform turns it back on output)
    c = [int(hexs[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

WHITE, ACCENT = (1.0, 1.0, 1.0), lin("#ff2d8c")
BG = "#121116"

def mix3(a, b, k): return tuple(lerp(a[i], b[i], k) for i in range(3))

# ---------------------------------------------------------------- beats (s), as in the HTML block
T_WHIP, D_WHIP = 1.9, 0.4
BEAT = 0.65
T_NODE = [2.65 + i * BEAT for i in range(4)]
T_BACK, D_BACK = 5.15, 0.45
T_RUN, D_RUN = 5.75, 1.5
T_HIT = T_RUN + D_RUN

cam_at = camera_rig([
    dict(t=0, pos=[0, 0.1, 4.2], dir=[0, 0], fov=50),
    dict(t=T_WHIP, pos=[0.2, 0.0, 2.4], dir=[7, 0], roll=-0.05, fov=50, ease="sine.inOut"),
    dict(t=T_WHIP + D_WHIP, pos=[-1.8, -0.4, 2.8], dir=[-46, 1], roll=0.78, fov=50, ease="power4.inOut"),
    dict(t=T_BACK, pos=[-1.6, -0.35, 2.4], dir=[-44, 1], roll=0.6, fov=50, ease="sine.out"),
    dict(t=T_BACK + D_BACK, pos=[-1.4, -0.3, 1.4], dir=[-14, -1.5], roll=-0.04, fov=46, ease="power4.inOut"),
    dict(t=T_HIT, pos=[-1.1, -0.2, 0.8], dir=[-12.5, -1], roll=-0.03, fov=46, ease="sine.inOut"),
    dict(t=T_HIT + 0.14, pos=[-0.6, 0.45, -1.2], dir=[-12, 11], roll=0.18, fov=42, ease="power3.out"),
    dict(t=DUR, pos=[-0.55, 0.5, -1.45], dir=[-13, 11.5], roll=0.14, fov=42, ease="sine.out"),
], amp=0.025, seed=SEED)

# ---------------------------------------------------------------- scene, render, colour
for ob in list(bpy.data.objects):  # an empty scene (works in the window too, where reading factory settings would reset it)
    bpy.data.objects.remove(ob)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
sc.render.fps = FPS
sc.render.film_transparent = False
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"
sc.eevee.taa_render_samples = args.samples
sc.render.use_motion_blur = True
sc.render.motion_blur_shutter = 0.5  # a 180° shutter: half a frame of smear, the whip still reads
sc.eevee.motion_blur_steps = 3
sc.eevee.volumetric_tile_size = "4"
sc.eevee.volumetric_samples = 96
sc.eevee.volumetric_end = 30
sc.eevee.use_volumetric_shadows = False
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"

world = bpy.data.worlds.new("world")
sc.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes["Background"]
bg_node.inputs[1].default_value = 1.0

# compositor: bloom only above 1.0, so 1.0 white lines stay crisp and the accent (strength > 1) glows
comp = bpy.data.node_groups.new("comp", "CompositorNodeTree")
sc.compositing_node_group = comp
comp.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
rl = comp.nodes.new("CompositorNodeRLayers")
glare = comp.nodes.new("CompositorNodeGlare")
glare.inputs["Type"].default_value = "Bloom"
glare.inputs["Quality"].default_value = "High"
glare.inputs["Threshold"].default_value = 1.0
glare.inputs["Strength"].default_value = 0.9
glare.inputs["Size"].default_value = 0.6
gout = comp.nodes.new("NodeGroupOutput")
comp.links.new(rl.outputs["Image"], glare.inputs["Image"])
comp.links.new(glare.outputs[0], gout.inputs[0])

# ---------------------------------------------------------------- materials
# emit(): emission coloured by the object's colour (rgb) times its alpha times `strength`, faded with distance like
# the kit's fog (near 3, far 15, far brightness 0.22). Animated objects change obj.color only.
def emit(name, strength=1.0, attr=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    info = nt.nodes.new("ShaderNodeObjectInfo")
    camd = nt.nodes.new("ShaderNodeCameraData")
    fog = nt.nodes.new("ShaderNodeMapRange")
    fog.inputs["From Min"].default_value, fog.inputs["From Max"].default_value = 3.0, 15.0
    fog.inputs["To Min"].default_value, fog.inputs["To Max"].default_value = 1.0, 0.22
    nt.links.new(camd.outputs["View Distance"], fog.inputs["Value"])
    m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = "MULTIPLY"
    nt.links.new(info.outputs["Alpha"], m1.inputs[0]); nt.links.new(fog.outputs["Result"], m1.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; m2.inputs[1].default_value = strength
    nt.links.new(m1.outputs[0], m2.inputs[0])
    last = m2
    if attr:
        a = nt.nodes.new("ShaderNodeAttribute"); a.attribute_name = attr; a.attribute_type = "GEOMETRY"
        m3 = nt.nodes.new("ShaderNodeMath"); m3.operation = "MULTIPLY"
        nt.links.new(m2.outputs[0], m3.inputs[0]); nt.links.new(a.outputs["Fac"], m3.inputs[1])
        last = m3
    nt.links.new(info.outputs["Color"], em.inputs["Color"])
    nt.links.new(last.outputs[0], em.inputs["Strength"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m

MAT_LINE = emit("line")
MAT_GLOW = emit("glow", strength=1.0)  # strength comes from the object's alpha (> 1 blooms)
MAT_DUST = emit("dust", attr="bright")

def link(obj):
    sc.collection.objects.link(obj)
    return obj

def setc(obj, rgb, a):
    obj.color = (rgb[0], rgb[1], rgb[2], a)

LINE_R = 0.0042  # tube radius: ~1-1.5 px at 4-6 units

def poly(name, strokes, mat=MAT_LINE, radius=LINE_R, mapping="SPLINE"):
    """A curve object of poly splines, points in Three.js coordinates. Draw-on with bevel_factor_end."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 1
    cu.bevel_factor_mapping_end = mapping
    for pts in strokes:
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            v = b3(p)
            sp.points[i].co = (v.x, v.y, v.z, 1)
    cu.materials.append(mat)
    ob = link(bpy.data.objects.new(name, cu))
    setc(ob, WHITE, 1.0)
    return ob

def sphere(name, r, mat=MAT_GLOW):
    me = bpy.data.meshes.new(name)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=r)
    bm.to_mesh(me); bm.free()
    for f in me.polygons: f.use_smooth = True
    me.materials.append(mat)
    return link(bpy.data.objects.new(name, me))

def plight(name, rgb, radius=0.05):
    li = bpy.data.lights.new(name, "POINT")
    li.color = rgb
    li.shadow_soft_size = radius
    li.use_shadow = False
    return link(bpy.data.objects.new(name, li))

# ---------------------------------------------------------------- the room
RW, RH, RD = 8, 4.5, 10
w2, h2, d2 = RW / 2, RH / 2, RD / 2
V = [[-w2, -h2, -d2], [w2, -h2, -d2], [w2, h2, -d2], [-w2, h2, -d2], [-w2, -h2, d2], [w2, -h2, d2], [w2, h2, d2], [-w2, h2, d2]]
EDGES = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]]
edge_obs = [poly(f"edge{k}", [[V[a], V[b]]]) for k, (a, b) in enumerate(EDGES)]

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
grid = poly("grid", wall_grid(), radius=LINE_R * 0.8, mapping="SPLINE")

# dust painted on the walls (the kit's scatter "walls", same seed), as a point cloud with a brightness per point
def scatter_walls(n, seed):
    r, pts = mulberry32(seed), []
    areas = [RW / 2 * RH / 2, RD / 2 * RH / 2, RD / 2 * RH / 2, RW / 2 * RD / 2, RW / 2 * RD / 2]
    tot = sum(areas)
    for _ in range(n):
        a, b, inn = r() * 2 - 1, r() * 2 - 1, 0.995
        pick, k = r() * tot, 0
        while pick > areas[k]: pick -= areas[k]; k += 1
        pts.append([[a * w2, b * h2, -d2 * inn], [-w2 * inn, b * h2, a * d2], [w2 * inn, b * h2, a * d2],
                    [a * w2, -h2 * inn, b * d2], [a * w2, h2 * inn, b * d2]][k])
    return pts

dust_pts = scatter_walls(5200, SEED)
dme = bpy.data.meshes.new("dust")
dme.from_pydata([tuple(b3(p)) for p in dust_pts], [], [])
rr = mulberry32(SEED + 11)
bright = [0.25 + 0.75 * rr() ** 2.2 for _ in dust_pts]   # most dust is dim, a few points are stars
rad = [0.006 + 0.010 * b for b in bright]
dme.attributes.new("bright", "FLOAT", "POINT").data.foreach_set("value", bright)
dme.attributes.new("rad", "FLOAT", "POINT").data.foreach_set("value", rad)
dust = link(bpy.data.objects.new("dust", dme))
gn = bpy.data.node_groups.new("dust_points", "GeometryNodeTree")
gn.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
gn.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
gi, go = gn.nodes.new("NodeGroupInput"), gn.nodes.new("NodeGroupOutput")
m2p = gn.nodes.new("GeometryNodeMeshToPoints")
na = gn.nodes.new("GeometryNodeInputNamedAttribute"); na.data_type = "FLOAT"; na.inputs["Name"].default_value = "rad"
sm = gn.nodes.new("GeometryNodeSetMaterial"); sm.inputs["Material"].default_value = MAT_DUST
gn.links.new(gi.outputs[0], m2p.inputs["Mesh"])
gn.links.new(na.outputs[0], m2p.inputs["Radius"])
gn.links.new(m2p.outputs[0], sm.inputs["Geometry"])
gn.links.new(sm.outputs[0], go.inputs[0])
dust.modifiers.new("points", "NODES").node_group = gn
setc(dust, WHITE, 1.0)

# haze: a faint volume filling the room, lit by the nodes' accent lights
vme = bpy.data.meshes.new("haze")
import bmesh
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(vme); bm.free()
haze = link(bpy.data.objects.new("haze", vme))
haze.scale = (RW * 0.99, RD * 0.99, RH * 0.99)
hm = bpy.data.materials.new("haze"); hm.use_nodes = True
hn = hm.node_tree; hn.nodes.clear()
hv = hn.nodes.new("ShaderNodeVolumePrincipled")
hv.inputs["Density"].default_value = 0.035
hv.inputs["Anisotropy"].default_value = 0.35
hv.inputs["Color"].default_value = (0.8, 0.78, 0.85, 1)
ho = hn.nodes.new("ShaderNodeOutputMaterial")
hn.links.new(hv.outputs[0], ho.inputs["Volume"])
vme.materials.append(hm)

# ---------------------------------------------------------------- nodes on the east wall
NODE_P = [[4, 0.9, -2.2], [4, -0.2, -3.6], [4, 1.3, -4.3], [4, -1.05, -2.9]]
nodes = []
for i, p in enumerate(NODE_P):
    core = sphere(f"node{i}", 0.032)
    core.location = b3([p[0] - 0.04, p[1], p[2]])
    ring_pts = [[0, math.cos(a), math.sin(a)] for a in [j / 96 * 2 * math.pi for j in range(97)]]
    rg = poly(f"ring{i}", [ring_pts], mat=MAT_GLOW, radius=LINE_R * 0.9)
    rg.location = b3([p[0] - 0.02, p[1], p[2]])
    li = plight(f"nodelight{i}", ACCENT)
    li.location = b3([p[0] - 0.25, p[1], p[2]])
    nodes.append((core, rg, li))

# ---------------------------------------------------------------- the graph on the back wall
GO = [-3.1, -1.75, -d2 + 0.01]
def g3(x, y, z=0.0): return [GO[0] + x, GO[1] + y, GO[2] + z]
GW, CAP, X_HIT = 6.4, 3.0, 3.5

def gy(x): return max(0.05, CAP * (1 - math.cos((x / X_HIT) ** 1.6 * math.pi / 2)) if x < X_HIT else CAP)
CP = [(GW * i / 2000, gy(GW * i / 2000)) for i in range(2001)]
CS = [0.0]
for i in range(1, len(CP)):
    CS.append(CS[-1] + math.dist(CP[i], CP[i - 1]))
CLEN = CS[-1]
S_HIT = next(CS[i] for i in range(len(CP)) if CP[i][1] >= CAP - 1e-3)
U_HIT = S_HIT / CLEN

def at_s(s):  # point and unit tangent at arc length s (straight on beyond the ends)
    if s <= 0: i = 1
    elif s >= CLEN: i = len(CP) - 1
    else:
        lo, hi = 0, len(CS) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if CS[mid] <= s: lo = mid
            else: hi = mid
        i = hi
    (x0, y0), (x1, y1) = CP[i - 1], CP[i]
    seg = math.dist((x0, y0), (x1, y1)) or 1e-9
    tx, ty = (x1 - x0) / seg, (y1 - y0) / seg
    k = (s - CS[i - 1]) / seg
    return (x0 + (x1 - x0) * k, y0 + (y1 - y0) * k), (tx, ty)

axes = poly("axes", [[g3(0, CAP + 0.5), g3(0, 0), g3(GW, 0)]])
hatch = []
c, hh, step = -0.32, 0.32, 0.09
while c < GW:
    x0, x1 = max(0, c), min(GW, c + hh)
    if x1 > x0: hatch.append([g3(x0, CAP + x0 - c), g3(x1, CAP + x1 - c)])
    c += step
band = poly("band", hatch, radius=LINE_R * 0.8, mapping="SPLINE")
capl = poly("cap", [[g3(0, CAP), g3(GW, CAP)]], mat=MAT_GLOW)
curve = poly("curve", [[g3(x, y, 0.005) for x, y in CP[::8]] + [g3(*CP[-1], 0.005)]])
drop = poly("drop", [[[0, 0, 0], [0, 1, 0]]], mat=MAT_GLOW)
head = sphere("head", 0.026)
head_l = plight("headlight", ACCENT)
for ob in (band, capl):  # reveal from the graph's left edge by scaling x around it
    pass

# text riding the curve: one mesh per word, each glyph vertex bent onto the curve (the kit's textPath, continuous)
font = bpy.data.fonts.load(args.font)
SIZE, OFFSET, START = 0.21, 0.35, 0.02
def word_mesh(word):
    cu = bpy.data.curves.new("w", "FONT"); cu.body = word; cu.font = font; cu.size = SIZE
    tmp = bpy.data.objects.new("w", cu); sc.collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp); bpy.data.curves.remove(cu)
    xs = [v.co.x for v in me.vertices]
    return me, (max(xs) if xs else 0.0)

_, w_aa = word_mesh("aa")
_, w_a_a = word_mesh("a a")
SPACE = w_a_a - w_aa
words = []
at = START * CLEN
for wi, word in enumerate(LINE.split(" ")):
    me, wlen = word_mesh(word)
    for v in me.vertices:
        (px, py), (tx, ty) = at_s(at + v.co.x)
        off = v.co.y + OFFSET * SIZE
        v.co = b3(g3(px - ty * off, py + tx * off, 0.01 + v.co.z * 0.2))
    me.materials.append(MAT_GLOW)
    ob = link(bpy.data.objects.new(f"word{wi}", me))
    words.append((ob, at / CLEN))
    at += wlen + SPACE

# ---------------------------------------------------------------- camera
camd = bpy.data.cameras.new("cam")
camd.sensor_fit = "VERTICAL"
camd.sensor_height = 24.0
camd.clip_start, camd.clip_end = 0.05, 100
cam = link(bpy.data.objects.new("cam", camd))
sc.camera = cam

def set_camera(pos, target, fov, roll):
    p, f = b3(pos), (b3(target) - b3(pos)).normalized()
    up = b3([math.sin(roll), math.cos(roll), 0])
    right = f.cross(up).normalized()
    u = right.cross(f)
    m = Matrix((right, u, -f)).transposed().to_4x4()
    m.translation = p
    cam.matrix_world = m
    camd.lens = (camd.sensor_height / 2) / math.tan(math.radians(fov) / 2)

AX_P = [[-3.6, 1.9, -d2], [w2, 1.9, -1.2], [1.4, -h2, -2.2]]
BG_LIN = lin(BG)

# ---------------------------------------------------------------- pose(t): everything from t
def show(ob, on): ob.scale = (1, 1, 1) if on else (0, 0, 0)

def pose(t):
    pos, target, fov, roll = cam_at(t)
    set_camera(pos, target, fov, roll)
    fl = flash(t, T_HIT, lift=0.32, half=0.06)
    bg_node.inputs[0].default_value = (*[c + fl * 0.1 for c in BG_LIN], 1)
    # the room draws on in the first second; the dust is there from the start
    de = span(t, 0.0, 0.9, "power2.out")
    for k, ob in enumerate(edge_obs):
        f = clamp01((de - k / 12) * 12)
        show(ob, f > 0.001); ob.data.bevel_factor_end = max(0.001, f)
        setc(ob, WHITE, 0.85)
    dg = span(t, 0.3, 1.0, "power2.out")
    show(grid, dg > 0.001); grid.data.bevel_factor_end = max(0.001, dg); setc(grid, WHITE, 0.07)
    setc(dust, WHITE, 1.1 * span(t, 0, 0.6))
    for i, (core, rg, li) in enumerate(nodes):
        on = t >= T_NODE[i]
        pu = pulse(t, T_NODE[i])
        show(core, on)
        core.scale = (1 + 1.2 * pulse(t, T_NODE[i], half=0.05),) * 3 if on else (0, 0, 0)
        setc(core, mix3(WHITE, ACCENT, 0.35 + 0.65 * pu), 3.0 + 9.0 * pu)
        k = span(t, T_NODE[i], 0.5, "expo.out")
        s = 0.05 + 0.7 * math.sin(k * math.pi)
        rg.scale = (s, s, s) if on and k < 1 else (0, 0, 0)
        setc(rg, mix3(WHITE, ACCENT, pu), 0.9 * (1 - k) * (1 + 3 * pu))
        li.data.energy = (12 + 140 * pu) if on else 0.0
    # the graph
    run = span(t, T_RUN, D_RUN, "power2.in")
    u = min(U_HIT, run * U_HIT) + max(0.0, t - T_HIT) * 0.06
    uu = min(0.995, u)
    (hx, hy), _ = at_s(uu * CLEN)
    g_on = span(t, T_BACK - 0.2, 0.6, "power2.out")
    hit_p, hold = pulse(t, T_HIT, half=0.1), (1.0 if t >= T_HIT else 0.0)
    show(axes, g_on > 0.001); axes.data.bevel_factor_end = max(0.001, g_on); setc(axes, WHITE, 0.7)
    show(band, g_on > 0.001); band.data.bevel_factor_end = max(0.001, g_on)
    setc(band, mix3(WHITE, ACCENT, max(hit_p, 0.6 * hold)), 0.35 * (1 + 2 * hit_p + 1.5 * hold))
    show(capl, g_on > 0.001); capl.data.bevel_factor_end = max(0.001, g_on)
    setc(capl, mix3(WHITE, ACCENT, max(hit_p, hold)), 1.0 + 5 * hit_p + 1.5 * hold)
    show(curve, t >= T_RUN); curve.data.bevel_factor_end = max(0.001, uu)
    setc(curve, WHITE, 1.0)
    running = t >= T_RUN
    hp = b3(g3(hx, hy, 0.02))
    head.location = hp
    hs = 1 + 1.6 * pulse(t, T_HIT, half=0.08)
    head.scale = (hs,) * 3 if running else (0, 0, 0)
    setc(head, mix3(WHITE, ACCENT, 0.3 + 0.7 * hit_p), 5 + 10 * hit_p)
    head_l.location = b3(g3(hx, hy, 0.3))
    head_l.data.energy = (20 + 30 * min(1, run * 2) + 100 * hit_p) if running else 0.0
    drop.location = b3(g3(hx, 0, 0.004))
    drop.scale = (1, 1, max(0.001, hy)) if running else (0, 0, 0)
    setc(drop, mix3(WHITE, ACCENT, 0.5 + 0.5 * hold), 0.6 * (1 + hold))
    # words: before the head white, the current word in the accent, the next ones fade in ahead of it
    vis = t >= T_RUN - 0.25
    head_u = uu if t >= T_RUN else -1
    ahead_a, window = 0.4 * span(t, T_RUN - 0.25, 0.25), 0.22
    cur = max([wi for wi, (_, ws) in enumerate(words) if ws <= head_u], default=-1)
    for wi, (ob, ws) in enumerate(words):
        if wi > cur:
            a = ahead_a * clamp01(1 - (ws - head_u) / window)
            show(ob, vis and a > 0.002); setc(ob, WHITE, a)
        elif wi == cur:
            show(ob, vis); setc(ob, ACCENT, 6.0)
        else:
            show(ob, vis); setc(ob, WHITE, 1.0)
    return hy

def on_frame(scene, depsgraph=None):
    pose((scene.frame_current + scene.frame_subframe) / FPS)

bpy.app.handlers.frame_change_pre.clear()
bpy.app.handlers.frame_change_pre.append(on_frame)

# ---------------------------------------------------------------- HUD anchors per frame
f0, f1 = (int(x) for x in args.frames.split("-"))
NFR = int(round(DUR * FPS))
if not args.open and (f0 == 0 and f1 >= NFR - 1 or args.proj_only):
    frames = []
    for f in range(NFR):
        sc.frame_set(f)
        hy = pose(f / FPS)
        def proj(p3):
            v = world_to_camera_view(sc, cam, b3(p3))
            return [round(v.x * W, 1), round((1 - v.y) * H, 1), 1 if v.z > 0 else 0]
        frames.append({
            "nodes": [proj(p) for p in NODE_P],
            "axes": [proj(p) for p in AX_P],
            "band": proj(g3(0.12, CAP + 0.16)),
            "head": round(hy / CAP, 4),
        })
    with open(os.path.join(OUT, "proj.json"), "w") as fh:
        json.dump({"fps": FPS, "duration": DUR, "frames": frames}, fh)
    print("wrote proj.json")
if args.proj_only:
    sys.exit(0)

# ---------------------------------------------------------------- look around in the window
if args.open:
    # The animation lives in the frame-change handler, so scrubbing the timeline plays it while this window is open.
    sc.frame_start, sc.frame_end = 0, NFR - 1
    sc.frame_set(0)
    for area in bpy.context.screen.areas if bpy.context.screen else []:
        if area.type == "VIEW_3D":
            area.spaces.active.shading.type = "RENDERED"
            area.spaces.active.region_3d.view_perspective = "CAMERA"

# ---------------------------------------------------------------- render (not when the window stays open)
def render():
    if args.pick:  # single frames for a look: --pick 30,126,200
        for f in (int(x) for x in args.pick.split(",")):
            sc.frame_set(f)
            sc.render.filepath = os.path.join(OUT, "frames", f"pick_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
        sys.exit(0)
    sc.frame_start, sc.frame_end = f0, f1
    sc.render.filepath = os.path.join(OUT, "frames", "f_")
    bpy.ops.render.render(animation=True)


if not args.open:
    render()
