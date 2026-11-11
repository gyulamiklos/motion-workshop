# Blender kit: the shared parts of every Blender scene in the workshop (Eevee, run through scripts/blender.sh).
# A scene script builds its world once, then pose(t) sets everything from t alone; run() hooks pose into a
# frame-change handler (so motion-blur sub-frames see the true pose), writes the HUD anchors (proj.json) and renders.
#
#   import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "blender")); import kit
#
# Coordinates: scene scripts may write points in the Three.js frame of the line-3D kit (Y up, -Z forward) and
# convert them with b3(); Blender itself is Z up.
import argparse, json, math, os, sys
import bmesh
import bpy
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

FPS, W, H = 60, 1920, 1080

# ---------------------------------------------------------------- command line
def args(defaults=None):
    """--out DIR [--frames A-B] [--samples N] [--pick 30,126] [--proj-only] [--open], plus scene extras."""
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames", default="")
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--pick", default="", help="single frames for a look: 30,126,200")
    ap.add_argument("--proj-only", action="store_true")
    ap.add_argument("--open", action="store_true", help="build the scene and leave it open in the Blender window")
    for k, v in (defaults or {}).items():
        ap.add_argument("--" + k, default=v, type=type(v))
    a = ap.parse_args(argv)
    a.out = os.path.abspath(a.out)
    os.makedirs(os.path.join(a.out, "frames"), exist_ok=True)
    return a

# ---------------------------------------------------------------- time (as in recipes/line3d/assets/line3d.js)
def clamp01(x): return min(1.0, max(0.0, x))
def lerp(a, b, k): return a + (b - a) * k

def ease(name):
    """GSAP eases by name: sine, expo, power1-4 (quad..quint) with .in / .out / .inOut."""
    if not name or name in ("none", "linear"): return lambda k: k
    fam, kind = name.split(".")
    if fam == "sine":
        return {"in": lambda k: 1 - math.cos(k * math.pi / 2), "out": lambda k: math.sin(k * math.pi / 2),
                "inOut": lambda k: -(math.cos(math.pi * k) - 1) / 2}[kind]
    if fam == "expo":
        f_in = lambda k: 0.0 if k <= 0 else 2 ** (10 * k - 10)
    else:
        p = int(fam[5:]) + 1
        f_in = lambda k: k ** p
    if kind == "in": return f_in
    if kind == "out": return lambda k: 1 - f_in(1 - k)
    return lambda k: f_in(2 * k) / 2 if k < 0.5 else 1 - f_in(2 * (1 - k)) / 2

def span(t, t0, dur, e=None):
    k = clamp01((t - t0) / dur)
    return ease(e)(k) if e else k

def pulse(t, t0, attack=0.06, half=0.025):
    """Birth pulse: 0 before t0, up over `attack`, then decays with half-life `half`."""
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
    """Seeded smooth wander in -1..1: the camera is never still."""
    r = mulberry32(seed)
    w = [0.21 + r() * 0.1, 0.37 + r() * 0.1, 0.61 + r() * 0.1]
    p = [r() * 6.28, r() * 6.28, r() * 6.28]
    return lambda t: (math.sin(t * w[0] * 6.283 + p[0]) * 0.55 + math.sin(t * w[1] * 6.283 + p[1]) * 0.3
                      + math.sin(t * w[2] * 6.283 + p[2]) * 0.15)

# ---------------------------------------------------------------- space and colour
def b3(v):
    """Three.js (x, y up, z toward the viewer) -> Blender (x, y forward, z up)."""
    return Vector((v[0], -v[2], v[1]))

def lin(hexs):
    """An sRGB hex as linear RGB (the Standard view transform turns it back on output)."""
    c = [int(hexs[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

def mix3(a, b, k): return tuple(lerp(a[i], b[i], k) for i in range(3))

WHITE = (1.0, 1.0, 1.0)

# ---------------------------------------------------------------- camera rig
def camera_rig(keys, amp=0.0, seed=7):
    """keys: [{t, pos, dir: [yaw, pitch] deg, fov, roll?, ease?}] in Three.js coordinates (yaw 0 looks down -Z,
    positive turns left; pitch positive looks up). The ease of a key shapes the move that arrives at it; angles are
    eased, so a whip turns at the eased angular speed. amp: seeded drift in world units."""
    dx, dy, dz = drift(seed + 1), drift(seed + 2), drift(seed + 3)
    def at(t):
        i = 0
        while i < len(keys) - 1 and t >= keys[i + 1]["t"]: i += 1
        k0, k1 = keys[i], keys[min(i + 1, len(keys) - 1)]
        k = 0 if k1 is k0 or t <= k0["t"] else ease(k1.get("ease", "power2.inOut"))(clamp01((t - k0["t"]) / (k1["t"] - k0["t"])))
        pos = Vector(k0["pos"]).lerp(Vector(k1["pos"]), k)
        yaw, pitch = math.radians(lerp(k0["dir"][0], k1["dir"][0], k)), math.radians(lerp(k0["dir"][1], k1["dir"][1], k))
        target = pos + Vector((-math.sin(yaw) * math.cos(pitch), math.sin(pitch), -math.cos(yaw) * math.cos(pitch)))
        fov, roll = lerp(k0.get("fov", 40), k1.get("fov", 40), k), lerp(k0.get("roll", 0), k1.get("roll", 0), k)
        pos += Vector((dx(t) * amp, dy(t) * amp, dz(t) * amp * 0.5))
        target += Vector((dy(t + 3) * amp * 0.4, dz(t + 5) * amp * 0.4, 0))
        return pos, target, fov, roll
    return at

# ---------------------------------------------------------------- stage
class Stage:
    """An empty Eevee scene at 1920x1080/60 with a camera, a flat world colour and bloom above `bloom_threshold`.
    o: background (hex), samples, shutter (motion blur, share of a frame; 0 = off), bloom (strength),
    bloom_threshold, bloom_size, volumes (True when the scene has haze)."""

    def __init__(self, **o):
        for ob in list(bpy.data.objects):  # empty, also in the window, where reading factory settings would reset the UI
            bpy.data.objects.remove(ob)
        self.sc = sc = bpy.context.scene
        sc.render.engine = "BLENDER_EEVEE"
        sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
        sc.render.fps = FPS
        sc.view_settings.view_transform = "Standard"
        sc.view_settings.look = "None"
        sc.eevee.taa_render_samples = o.get("samples", 32)
        shutter = o.get("shutter", 0.5)
        sc.render.use_motion_blur = shutter > 0
        sc.render.motion_blur_shutter = shutter or 0.5
        sc.eevee.motion_blur_steps = o.get("blur_steps", 3)
        sc.eevee.volumetric_tile_size = "4"
        sc.eevee.volumetric_samples = 96
        sc.eevee.volumetric_end = o.get("volumetric_end", 30)
        sc.eevee.use_volumetric_shadows = False
        sc.render.image_settings.file_format = "PNG"
        sc.render.image_settings.color_mode = "RGB"
        world = bpy.data.worlds.new("world")
        sc.world = world
        world.use_nodes = True
        self.bg_node = world.node_tree.nodes["Background"]
        self.bg_node.inputs[1].default_value = 1.0
        self.bg = lin(o.get("background", "#0a090c"))
        self.background(0.0)
        comp = bpy.data.node_groups.new("comp", "CompositorNodeTree")
        sc.compositing_node_group = comp
        comp.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        rl = comp.nodes.new("CompositorNodeRLayers")
        g = self.glare = comp.nodes.new("CompositorNodeGlare")
        g.inputs["Type"].default_value = "Bloom"
        g.inputs["Quality"].default_value = "High"
        g.inputs["Threshold"].default_value = o.get("bloom_threshold", 1.0)
        g.inputs["Strength"].default_value = o.get("bloom", 0.9)
        g.inputs["Size"].default_value = o.get("bloom_size", 0.6)
        self.comp_out = comp.nodes.new("NodeGroupOutput")
        comp.links.new(rl.outputs["Image"], g.inputs["Image"])
        comp.links.new(g.outputs[0], self.comp_out.inputs[0])
        self.comp = comp
        camd = bpy.data.cameras.new("cam")
        camd.sensor_fit = "VERTICAL"
        camd.sensor_height = 24.0
        camd.clip_start, camd.clip_end = 0.05, 200
        self.cam = self.link(bpy.data.objects.new("cam", camd))
        sc.camera = self.cam

    def link(self, ob):
        self.sc.collection.objects.link(ob)
        return ob

    def background(self, lift=0.0):
        """The world colour, lifted toward grey by `lift` (a flash frame)."""
        self.bg_node.inputs[0].default_value = (*[c + lift for c in self.bg], 1)

    def set_camera(self, pos, target, fov, roll=0.0):
        """Point the camera (Three.js coordinates): vertical fov in degrees, roll tilts the up vector in world XY."""
        p, f = b3(pos), (b3(target) - b3(pos)).normalized()
        up = b3([math.sin(roll), math.cos(roll), 0])
        right = f.cross(up).normalized()
        m = Matrix((right, right.cross(f), -f)).transposed().to_4x4()
        m.translation = p
        self.cam.matrix_world = m
        self.cam.data.lens = (self.cam.data.sensor_height / 2) / math.tan(math.radians(fov) / 2)

    def project(self, p3):
        """Screen position [x, y, in front] of a Three.js point, for the HTML HUD."""
        v = world_to_camera_view(self.sc, self.cam, b3(p3))
        return [round(v.x * W, 1), round((1 - v.y) * H, 1), 1 if v.z > 0 else 0]

# ---------------------------------------------------------------- materials
def emit(name, strength=1.0, attr=None, fog=(3.0, 15.0, 0.22)):
    """Emission coloured by the object's colour (rgb), its alpha as brightness (> 1 blooms), times `strength`, faded
    with camera distance like the line-3D fog (near, far, far brightness). attr: a per-point float attribute that
    multiplies the brightness. Animate obj.color only (set_color)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    info = nt.nodes.new("ShaderNodeObjectInfo")
    camd = nt.nodes.new("ShaderNodeCameraData")
    fr = nt.nodes.new("ShaderNodeMapRange")
    fr.inputs["From Min"].default_value, fr.inputs["From Max"].default_value = fog[0], fog[1]
    fr.inputs["To Min"].default_value, fr.inputs["To Max"].default_value = 1.0, fog[2]
    nt.links.new(camd.outputs["View Distance"], fr.inputs["Value"])
    m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = "MULTIPLY"
    nt.links.new(info.outputs["Alpha"], m1.inputs[0]); nt.links.new(fr.outputs["Result"], m1.inputs[1])
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

def set_color(ob, rgb, a):
    ob.color = (rgb[0], rgb[1], rgb[2], a)

def show(ob, on, s=1.0):
    """Hide by scale (keeps motion blur and the depsgraph stable, unlike hide_render)."""
    ob.scale = (s, s, s) if on else (0, 0, 0)

def haze(stage, size, center=(0, 0, 0), density=0.035, anisotropy=0.35, color=(0.8, 0.78, 0.85)):
    """A box of faint volume (Three.js size w, h, d) that lights scatter in: glow around point lights."""
    me = bpy.data.meshes.new("haze")
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
    ob = stage.link(bpy.data.objects.new("haze", me))
    ob.location = b3(center)
    ob.scale = (size[0], size[2], size[1])
    m = bpy.data.materials.new("haze"); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Density"].default_value = density
    v.inputs["Anisotropy"].default_value = anisotropy
    v.inputs["Color"].default_value = (*color, 1)
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(v.outputs[0], o.inputs["Volume"])
    me.materials.append(m)
    return ob

# ---------------------------------------------------------------- geometry
LINE_R = 0.0042  # tube radius: ~1-1.5 px at 4-6 units with a 50° lens

def poly(stage, name, strokes, mat, radius=LINE_R):
    """Lines as one curve object of poly splines (Three.js points), a thin tube each. Draw-on: data.bevel_factor_end
    (0..1 of each spline's length)."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 1
    cu.bevel_factor_mapping_end = "SPLINE"
    for pts in strokes:
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            v = b3(p)
            sp.points[i].co = (v.x, v.y, v.z, 1)
    cu.materials.append(mat)
    ob = stage.link(bpy.data.objects.new(name, cu))
    set_color(ob, WHITE, 1.0)
    return ob

def draw(ob, k):
    """Draw a poly() object on to k (0..1); hidden at 0."""
    show(ob, k > 0.001)
    ob.data.bevel_factor_end = max(0.001, k)

def sphere(stage, name, r, mat, segments=24):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments // 2, radius=r)
    bm.to_mesh(me); bm.free()
    for f in me.polygons: f.use_smooth = True
    me.materials.append(mat)
    return stage.link(bpy.data.objects.new(name, me))

def point_light(stage, name, rgb, radius=0.05):
    li = bpy.data.lights.new(name, "POINT")
    li.color = rgb
    li.shadow_soft_size = radius
    li.use_shadow = False
    return stage.link(bpy.data.objects.new(name, li))

def point_cloud(stage, name, pts, mat, radius, bright=None):
    """Points as a point cloud (Three.js positions). radius: one value or one per point; bright: a per-point
    brightness the material reads with emit(attr="bright")."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(b3(p)) for p in pts], [], [])
    rad = radius if isinstance(radius, (list, tuple)) else [radius] * len(pts)
    me.attributes.new("rad", "FLOAT", "POINT").data.foreach_set("value", rad)
    if bright is not None:
        me.attributes.new("bright", "FLOAT", "POINT").data.foreach_set("value", bright)
    ob = stage.link(bpy.data.objects.new(name, me))
    gn = bpy.data.node_groups.new(name + "_points", "GeometryNodeTree")
    gn.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    gn.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi, go = gn.nodes.new("NodeGroupInput"), gn.nodes.new("NodeGroupOutput")
    m2p = gn.nodes.new("GeometryNodeMeshToPoints")
    na = gn.nodes.new("GeometryNodeInputNamedAttribute"); na.data_type = "FLOAT"; na.inputs["Name"].default_value = "rad"
    sm = gn.nodes.new("GeometryNodeSetMaterial"); sm.inputs["Material"].default_value = mat
    gn.links.new(gi.outputs[0], m2p.inputs["Mesh"])
    gn.links.new(na.outputs[0], m2p.inputs["Radius"])
    gn.links.new(m2p.outputs[0], sm.inputs["Geometry"])
    gn.links.new(sm.outputs[0], go.inputs[0])
    ob.modifiers.new("points", "NODES").node_group = gn
    set_color(ob, WHITE, 1.0)
    return ob

def text_mesh(stage, text, size, font):
    """A filled text mesh (Blender units, baseline at y = 0, starting at x = 0) and its advance width."""
    cu = bpy.data.curves.new("t", "FONT"); cu.body = text; cu.font = font; cu.size = size
    tmp = bpy.data.objects.new("t", cu); stage.link(tmp)
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp); bpy.data.curves.remove(cu)
    xs = [v.co.x for v in me.vertices]
    return me, (max(xs) if xs else 0.0)

class Path2D:
    """A polyline in a plane, walked by arc length: at(s) -> (point, unit tangent), straight on beyond the ends."""

    def __init__(self, pts):
        self.p = pts
        self.s = [0.0]
        for i in range(1, len(pts)):
            self.s.append(self.s[-1] + math.dist(pts[i], pts[i - 1]))
        self.length = self.s[-1]

    def at(self, s):
        if s <= 0: i = 1
        elif s >= self.length: i = len(self.p) - 1
        else:
            lo, hi = 0, len(self.s) - 1
            while hi - lo > 1:
                mid = (lo + hi) // 2
                if self.s[mid] <= s: lo = mid
                else: hi = mid
            i = hi
        (x0, y0), (x1, y1) = self.p[i - 1], self.p[i]
        seg = math.dist((x0, y0), (x1, y1)) or 1e-9
        k = (s - self.s[i - 1]) / seg
        return (x0 + (x1 - x0) * k, y0 + (y1 - y0) * k), ((x1 - x0) / seg, (y1 - y0) / seg)

def text_on_path(stage, text, path, to3, mat, size, font, start=0.0, offset=0.35):
    """One mesh per word, every glyph vertex bent onto `path` (Path2D); to3(x, y, z) places the plane in Three.js
    space. Returns [(object, start along the path 0..1)] for painting word by word."""
    _, w_aa = text_mesh(stage, "aa", size, font)
    _, w_a_a = text_mesh(stage, "a a", size, font)
    space, at, words = w_a_a - w_aa, start * path.length, []
    for wi, word in enumerate(text.split(" ")):
        me, wlen = text_mesh(stage, word, size, font)
        for v in me.vertices:
            (px, py), (tx, ty) = path.at(at + v.co.x)
            off = v.co.y + offset * size
            v.co = b3(to3(px - ty * off, py + tx * off, 0.01 + v.co.z * 0.2))
        me.materials.append(mat)
        words.append((stage.link(bpy.data.objects.new(f"word{wi}", me)), at / path.length))
        at += wlen + space
    return words

def font(path="/usr/share/fonts/truetype/lato/Lato-Black.ttf"):
    return bpy.data.fonts.load(path)

# ---------------------------------------------------------------- flat shapes from distance fields
# A silhouette (a figure, an icon) as a union of circles and capsules, contoured with marching squares: one smooth
# outline, whatever the parts. shape_mesh() turns it into a filled mesh plus an outline ribbon (face attribute
# "edge" = 1), standing in the Blender XZ plane, facing -Y.
def sd_circle(c, r):
    return lambda x, y: math.hypot(x - c[0], y - c[1]) - r

def sd_capsule(a, b, r):
    def f(x, y):
        bax, bay, pax, pay = b[0] - a[0], b[1] - a[1], x - a[0], y - a[1]
        h = clamp01((pax * bax + pay * bay) / (bax * bax + bay * bay or 1e-9))
        return math.hypot(pax - bax * h, pay - bay * h) - r
    return f

def sd_union(parts, k=0.04):
    """Smooth union (polynomial smooth-min, blend radius k): parts melt into one body."""
    def f(x, y):
        d = parts[0](x, y)
        for p in parts[1:]:
            e = p(x, y)
            h = clamp01(0.5 + 0.5 * (e - d) / k)
            d = lerp(e, d, h) - k * h * (1 - h)
        return d
    return f

def contour(sdf, box, step=0.008):
    """Closed loops [(x, y), ...] where sdf = 0 inside box (x0, y0, x1, y1), marching squares."""
    x0, y0, x1, y1 = box
    nx, ny = int((x1 - x0) / step) + 1, int((y1 - y0) / step) + 1
    v = [[sdf(x0 + i * step, y0 + j * step) for i in range(nx)] for j in range(ny)]
    def cross(i0, j0, i1, j1):
        a, b = v[j0][i0], v[j1][i1]
        k = a / (a - b)
        return (round(x0 + (i0 + (i1 - i0) * k) * step, 6), round(y0 + (j0 + (j1 - j0) * k) * step, 6))
    nxt = {}
    for j in range(ny - 1):
        for i in range(nx - 1):
            c = [v[j][i] < 0, v[j][i + 1] < 0, v[j + 1][i + 1] < 0, v[j + 1][i] < 0]
            e = {0: (i, j, i + 1, j), 1: (i + 1, j, i + 1, j + 1), 2: (i, j + 1, i + 1, j + 1), 3: (i, j, i, j + 1)}
            sides = [s for s, (a, b) in zip(range(4), [(0, 1), (1, 2), (3, 2), (0, 3)]) if c[a] != c[b]]
            pts = [cross(*e[s]) for s in sides]
            for a, b in zip(pts[0::2], pts[1::2]):  # saddles pair up arbitrarily: fine at this resolution
                nxt.setdefault(a, []).append(b); nxt.setdefault(b, []).append(a)
    loops, seen = [], set()
    for start in nxt:
        if start in seen: continue
        loop, prev, cur = [start], None, start
        seen.add(start)
        while True:
            cand = [p for p in nxt[cur] if p != prev and p not in seen]
            if not cand: break
            prev, cur = cur, cand[0]
            seen.add(cur); loop.append(cur)
        if len(loop) > 8: loops.append(loop[::2])  # every other point: still smooth, half the vertices
    return loops

def shape_mesh(name, sdf, box, rim=0.012, step=0.008):
    """A filled mesh of the shape with an inner outline ribbon `rim` wide (face attribute "edge": 1 on the ribbon)."""
    loops = contour(sdf, box, step)
    bm = bmesh.new()
    inner_edges, ribbon = [], []
    eps = step * 0.5
    for loop in loops:
        outer, inner = [], []
        for (x, y) in loop:
            gx = (sdf(x + eps, y) - sdf(x - eps, y)) / (2 * eps)
            gy = (sdf(x, y + eps) - sdf(x, y - eps)) / (2 * eps)
            g = math.hypot(gx, gy) or 1.0
            outer.append(bm.verts.new((x, 0.0, y)))
            inner.append(bm.verts.new((x - gx / g * rim, 0.0, y - gy / g * rim)))
        n = len(loop)
        for i in range(n):
            j = (i + 1) % n
            ribbon.append(bm.faces.new((outer[i], outer[j], inner[j], inner[i])))
            inner_edges.append(bm.edges.get((inner[i], inner[j])))
    fill = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=inner_edges)["geom"]
    fill_faces = [f for f in fill if isinstance(f, bmesh.types.BMFace)]
    bmesh.ops.recalc_face_normals(bm, faces=ribbon + fill_faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = False
    ed = me.attributes.new("edge", "FLOAT", "FACE")
    nf = len(me.polygons)
    ed.data.foreach_set("value", [1.0] * len(ribbon) + [0.0] * (nf - len(ribbon)))
    return me

# ---------------------------------------------------------------- instancing
def instancer(stage, name, points, variants, attrs=None):
    """Many copies of a few meshes. points: Three.js positions; variants: meshes, picked per point by the int
    attribute "var"; attrs: per-point floats ("born" s, "scl" scale, "rot" yaw rad, any other for the shader to read
    with an INSTANCER attribute). A point shows from its "born" time on: set_time(ob, t) per frame."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(b3(p)) for p in points], [], [])
    for k, vals in (attrs or {}).items():
        typ = "INT" if k == "var" else "FLOAT"
        me.attributes.new(k, typ, "POINT").data.foreach_set("value", vals)
    ob = stage.link(bpy.data.objects.new(name, me))
    col = bpy.data.collections.new(name + "_variants")  # not linked to the scene: only its instances render
    for i, vm in enumerate(variants):
        col.objects.link(bpy.data.objects.new(f"{name}_v{i}", vm))
    gn = bpy.data.node_groups.new(name + "_instances", "GeometryNodeTree")
    gn.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    gn.interface.new_socket("T", in_out="INPUT", socket_type="NodeSocketFloat")
    gn.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = gn.nodes, gn.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    m2p = N.new("GeometryNodeMeshToPoints")
    def named(n, typ="FLOAT"):
        a = N.new("GeometryNodeInputNamedAttribute"); a.data_type = typ; a.inputs["Name"].default_value = n
        return a.outputs[0]
    later = N.new("FunctionNodeCompare"); later.data_type = "FLOAT"; later.operation = "GREATER_THAN"
    L.new(named("born"), later.inputs[0]); L.new(gi.outputs["T"], later.inputs[1])
    dele = N.new("GeometryNodeDeleteGeometry")
    ci = N.new("GeometryNodeCollectionInfo")
    ci.inputs["Collection"].default_value = col
    ci.inputs["Separate Children"].default_value = True
    ci.inputs["Reset Children"].default_value = True
    iop = N.new("GeometryNodeInstanceOnPoints")
    iop.inputs["Pick Instance"].default_value = True
    rot = N.new("ShaderNodeCombineXYZ")
    L.new(named("rot"), rot.inputs["Z"])
    L.new(gi.outputs[0], m2p.inputs["Mesh"])
    L.new(m2p.outputs[0], dele.inputs["Geometry"])
    L.new(later.outputs[0], dele.inputs["Selection"])
    L.new(dele.outputs[0], iop.inputs["Points"])
    L.new(ci.outputs[0], iop.inputs["Instance"])
    L.new(named("var", "INT"), iop.inputs["Instance Index"])
    L.new(rot.outputs[0], iop.inputs["Rotation"])
    L.new(named("scl"), iop.inputs["Scale"])
    L.new(iop.outputs[0], go.inputs[0])
    mod = ob.modifiers.new("instances", "NODES")
    mod.node_group = gn
    ob["t_socket"] = gn.interface.items_tree["T"].identifier
    set_color(ob, WHITE, 0.0)
    return ob

def set_time(ob, t):
    """The instancer's clock: points born after t are not there yet."""
    getattr(ob.modifiers["instances"].properties.inputs, ob["t_socket"]).value = t
    ob.update_tag()

def time_node(mat):
    """A Value node "T" in a material, for shaders that compute pulses from the clock; set it with .outputs[0]."""
    n = mat.node_tree.nodes.get("T") or mat.node_tree.nodes.new("ShaderNodeValue")
    n.name = "T"
    return n

def scanline(name, freq=16.0, duty=0.42, edge=1.0, stripe=0.5, fill="#0d0c10", accent="#ff2d8c",
             fog=(6.0, 45.0, 0.1), pulse_half=0.07):
    """The striped-silhouette look for shape_mesh() meshes: a bright outline, horizontal stripes (`freq` per unit of
    height, `duty` lit) and an opaque dark fill that hides what stands behind. An instancer's "born", "shade" and "accent" attributes give
    each copy a birth pulse, a brightness and whether it takes the accent fill. Per frame: time_node(mat) is the clock,
    the Value node "ACC" (0..1) how far the "accent" copies are filled."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    N, L = nt.nodes, nt.links
    def math_(op, a, b=None, v=None):
        n = N.new("ShaderNodeMath"); n.operation = op
        for i, x in enumerate((a, b)):
            if x is None: continue
            if isinstance(x, (int, float)): n.inputs[i].default_value = x
            else: L.new(x, n.inputs[i])
        return n.outputs[0]
    def attr(n, typ):
        a = N.new("ShaderNodeAttribute"); a.attribute_name = n; a.attribute_type = typ
        return a.outputs["Fac"]
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    frac = math_("FRACT", math_("MULTIPLY", sep.outputs["Z"], freq))
    lit = math_("LESS_THAN", frac, duty)
    e = attr("edge", "GEOMETRY")
    base = math_("ADD", math_("MULTIPLY", e, edge), math_("MULTIPLY", math_("MULTIPLY", lit, math_("SUBTRACT", 1.0, e)), stripe))
    # birth pulse: 1 + 2 * 0.5^((T - born) / half) once born
    t = time_node(m).outputs[0]
    age = math_("SUBTRACT", t, attr("born", "INSTANCER"))
    pls = math_("MULTIPLY", math_("POWER", 0.5, math_("DIVIDE", math_("MAXIMUM", age, 0.0), pulse_half)), 2.0)
    shade = attr("shade", "INSTANCER")
    shade = math_("ADD", math_("MULTIPLY", math_("LESS_THAN", shade, 0.001), 1.0), shade)  # missing = 1
    camd = N.new("ShaderNodeCameraData")
    fr = N.new("ShaderNodeMapRange")
    fr.inputs["From Min"].default_value, fr.inputs["From Max"].default_value = fog[0], fog[1]
    fr.inputs["To Min"].default_value, fr.inputs["To Max"].default_value = 1.0, fog[2]
    L.new(camd.outputs["View Distance"], fr.inputs["Value"])
    white = math_("MULTIPLY", math_("MULTIPLY", math_("MULTIPLY", base, math_("ADD", pls, 1.0)), shade), fr.outputs["Result"])
    accn = N.new("ShaderNodeValue"); accn.name = "ACC"
    fill_acc = math_("MULTIPLY", accn.outputs[0], attr("accent", "INSTANCER"))
    acc = N.new("ShaderNodeEmission"); acc.inputs["Color"].default_value = (*lin(accent), 1)
    L.new(math_("MULTIPLY", math_("ADD", math_("MULTIPLY", base, 1.5), 1.2), fr.outputs["Result"]), acc.inputs["Strength"])
    wem = N.new("ShaderNodeEmission"); L.new(white, wem.inputs["Strength"])
    dark = N.new("ShaderNodeEmission"); dark.inputs["Color"].default_value = (*lin(fill), 1); dark.inputs["Strength"].default_value = 1.0
    add = N.new("ShaderNodeAddShader"); L.new(wem.outputs[0], add.inputs[0]); L.new(dark.outputs[0], add.inputs[1])
    mix = N.new("ShaderNodeMixShader"); L.new(fill_acc, mix.inputs[0])
    L.new(add.outputs[0], mix.inputs[1]); L.new(acc.outputs[0], mix.inputs[2])
    out = N.new("ShaderNodeOutputMaterial"); L.new(mix.outputs[0], out.inputs["Surface"])
    return m

# ---------------------------------------------------------------- physics (rigid body)
# Pieces are meshes in Blender coordinates, already placed in the world (origin at 0). The sim is stepped once through
# every frame before rendering, so it is cached and the same on every run; pose(t) never touches a body.
def wire_solid(stage, name, me, mat, wire=0.012):
    """A mesh drawn as its edges (wireframe modifier) with an emit material; colour it with set_color."""
    me.materials.clear(); me.materials.append(mat)
    ob = stage.link(bpy.data.objects.new(name, me))
    md = ob.modifiers.new("wire", "WIREFRAME")
    md.thickness, md.use_even_offset, md.use_replace, md.use_boundary = wire, True, True, True
    set_color(ob, WHITE, 1.0)
    return ob

def fracture(me, n, seed, gap=0.985):
    """Split a convex mesh into about n convex pieces: Voronoi cells around random seeds inside it, each cut out with
    bisect planes and capped. Returns [(centre, mesh)]; each mesh is recentred on its centre, shrunk a little (`gap`)
    so neighbouring wires do not fight."""
    r = mulberry32(seed)
    vs = [v.co.copy() for v in me.vertices]
    lo = Vector([min(v[i] for v in vs) for i in range(3)]); hi = Vector([max(v[i] for v in vs) for i in range(3)])
    polys = [(p.center.copy(), p.normal.copy()) for p in me.polygons]
    seeds, tries = [], 0
    while len(seeds) < n and tries < n * 400:
        tries += 1
        p = Vector([lerp(lo[i], hi[i], r()) for i in range(3)])
        if all((p - c).dot(nm) < -0.03 for c, nm in polys): seeds.append(p)
    out = []
    for i, si in enumerate(seeds):
        bm = bmesh.new(); bm.from_mesh(me)
        for j, sj in enumerate(seeds):
            if j == i or not bm.verts: continue
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(si + sj) / 2,
                                   plane_no=(sj - si).normalized(), clear_outer=True, dist=1e-6)
            bd = [e for e in bm.edges if e.is_boundary]
            if bd: bmesh.ops.holes_fill(bm, edges=bd, sides=64)
        if len(bm.verts) < 4: bm.free(); continue
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(1.0), verts=bm.verts[:], edges=bm.edges[:])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        c = sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
        bmesh.ops.translate(bm, vec=-c, verts=bm.verts[:])
        bmesh.ops.scale(bm, vec=(gap, gap, gap), verts=bm.verts[:])
        cm = bpy.data.meshes.new("cell"); bm.to_mesh(cm); bm.free()
        out.append((c, cm))
    return out

def rigid_world(stage, nfr, gravity=9.81, substeps=12, iterations=30):
    """The scene's rigid body world for nfr frames, gravity in m/s^2."""
    sc = stage.sc
    bpy.context.view_layer.update()
    bpy.ops.rigidbody.world_add()
    w = sc.rigidbody_world
    w.point_cache.frame_start, w.point_cache.frame_end = 0, nfr
    w.substeps_per_frame, w.solver_iterations = substeps, iterations
    sc.gravity = (0, 0, -gravity)
    return w

def rigid(ob, passive=False, mass=1.0, shape="CONVEX_HULL", friction=0.6, bounce=0.25, layer=0):
    """Make ob a rigid body. layer: bodies collide only with bodies sharing a layer (0 or 1); ground should use both."""
    bpy.context.view_layer.update()
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.ops.rigidbody.object_add(type="PASSIVE" if passive else "ACTIVE")
    rb = ob.rigid_body
    rb.collision_shape, rb.mass, rb.friction, rb.restitution = shape, mass, friction, bounce
    rb.use_margin, rb.collision_margin = True, 0.004
    rb.linear_damping, rb.angular_damping = 0.04, 0.25
    rb.collision_collections = [i == layer or (passive and i < 2) for i in range(20)]

def hold_until(ob, frame):
    """The body stands where it is (animated, not simulated) until `frame`, then falls."""
    rb = ob.rigid_body
    rb.kinematic = True;  ob.keyframe_insert("rigid_body.kinematic", frame=0)
    rb.kinematic = False; ob.keyframe_insert("rigid_body.kinematic", frame=frame)

def burst(stage, loc, frame, strength, length=8, reach=4.0):
    """A radial force field (Three.js point) that kicks every body near it for `length` frames from `frame`."""
    bpy.ops.object.effector_add(type="FORCE", location=tuple(b3(loc)))
    ob = bpy.context.object
    f = ob.field
    f.shape, f.use_max_distance, f.distance_max, f.strength = "POINT", True, reach, 0.0
    f.keyframe_insert("strength", frame=max(0, frame - 1))
    f.strength = strength; f.keyframe_insert("strength", frame=frame)
    f.strength = 0.0;      f.keyframe_insert("strength", frame=frame + length)
    return ob

def simulate(stage, nfr):
    """Bake the sim for nfr frames (call before run()). Stepping frame_set() in a background run does not fill the
    cache; the bake does, and every later frame_set reads it."""
    with bpy.context.temp_override(scene=stage.sc):
        bpy.ops.ptcache.bake_all(bake=True)
    stage.sc.frame_set(0)

# ---------------------------------------------------------------- run
def run(stage, a, duration, pose, anchors=None):
    """Hook pose(t) into the frame-change handler, then: --open leaves the window with the timeline live; otherwise
    write proj.json (anchors(t) -> dict per frame, after pose; empty without anchors) on a full run or --proj-only, and render --pick frames
    or the --frames range (default: all)."""
    sc = stage.sc
    nfr = int(round(duration * FPS))
    bpy.app.handlers.frame_change_pre.clear()
    bpy.app.handlers.frame_change_pre.append(lambda scene, *_: pose((scene.frame_current + scene.frame_subframe) / FPS))
    sc.frame_start, sc.frame_end = 0, nfr - 1
    if a.open:
        sc.frame_set(0)
        for area in bpy.context.screen.areas if bpy.context.screen else []:
            if area.type == "VIEW_3D":
                area.spaces.active.shading.type = "RENDERED"
                area.spaces.active.region_3d.view_perspective = "CAMERA"
        return
    f0, f1 = (int(x) for x in a.frames.split("-")) if a.frames else (0, nfr - 1)
    anchors = anchors or (lambda t: {})
    if a.proj_only or (not a.pick and f0 == 0 and f1 >= nfr - 1):
        frames = []
        for f in range(nfr):
            sc.frame_set(f)
            frames.append(anchors(f / FPS))
        with open(os.path.join(a.out, "proj.json"), "w") as fh:
            json.dump({"fps": FPS, "duration": duration, "frames": frames}, fh)
        print("wrote proj.json")
    if a.proj_only:
        return
    if a.pick:
        for f in (int(x) for x in a.pick.split(",")):
            sc.frame_set(f)
            sc.render.filepath = os.path.join(a.out, "frames", f"pick_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
        return
    sc.frame_start, sc.frame_end = f0, f1
    sc.render.filepath = os.path.join(a.out, "frames", "f_")
    bpy.ops.render.render(animation=True)
