// Line-3D kit: thin white lines in a dark, foggy space, one accent that blooms on what is alive.
// Rules and measured numbers: recipes/_principles.md. Usage and the element cards: recipes/line3d/README.md.
//
// Determinism: nothing here reads the clock or Math.random. A scene is a pure function of time:
// build everything once, then draw(t) sets uniforms and the camera from t alone and renders.
import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.184.0/build/three.module.js";

export { THREE };

// ---------------------------------------------------------------- numbers from the principles
export const LOOK = {
  background: "#0a090c",
  line: "#ffffff",
  accent: "#ff2d8c",
  lineAlpha: 0.92, // front lines: white at 0.9-1.0
  backAlpha: 0.4, // hidden side: dashed, 0.35-0.45
  dash: 0.06, // dash + gap length in world units (the hidden side of a unit sphere: ~6 px at hero size)
  fogNear: 4,
  fogFar: 14,
  fogMin: 0.18, // far lines keep 0.15-0.25
  bloomStrength: 1.35,
  bloomRadius: 1.0,
};
export const PULSE = { attack: 0.06, half: 0.025 }; // 3-4 frames up, half-life ~1.5 frames at 60 fps
export const FLASH = { lift: 0.2, half: 0.05 }; // +50/255 for one frame, half-life ~3 frames

// ---------------------------------------------------------------- time helpers
export function mulberry32(seed) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export const clamp01 = (x) => Math.min(1, Math.max(0, x));
export const lerp = (a, b, k) => a + (b - a) * k;

// A GSAP ease by name ("expo.in", "power2.inOut"), or linear when GSAP is not there.
export function ease(name) {
  if (!name || name === "none" || name === "linear") return (k) => k;
  return window.gsap ? window.gsap.parseEase(name) : (k) => k;
}

// Progress of a span [t0, t0 + dur] at t, eased, clamped to 0..1.
export function span(t, t0, dur, easing) {
  const k = clamp01((t - t0) / dur);
  return easing ? ease(easing)(k) : k;
}

// Birth pulse: 0 before t0, rises to 1 over `attack`, then decays with half-life `half`.
export function pulse(t, t0, o = {}) {
  const attack = o.attack ?? PULSE.attack;
  const half = o.half ?? PULSE.half;
  if (t < t0) return 0;
  if (t < t0 + attack) return ease("power2.out")((t - t0) / attack);
  return Math.pow(0.5, (t - t0 - attack) / half);
}

// Flash frame: a whole-frame lift that jumps on t0 and decays.
export function flash(t, t0, o = {}) {
  if (t < t0) return 0;
  return (o.lift ?? FLASH.lift) * Math.pow(0.5, (t - t0) / (o.half ?? FLASH.half));
}

// Seeded, smooth drift in -1..1 (sum of sines with seeded phases): camera breathing without a clock.
export function drift(seed) {
  const r = mulberry32(seed);
  const w = [0.21 + r() * 0.1, 0.37 + r() * 0.1, 0.61 + r() * 0.1];
  const p = [r() * 6.28, r() * 6.28, r() * 6.28];
  return (t) => (Math.sin(t * w[0] * 6.283 + p[0]) * 0.55 + Math.sin(t * w[1] * 6.283 + p[1]) * 0.3 + Math.sin(t * w[2] * 6.283 + p[2]) * 0.15);
}

// ---------------------------------------------------------------- camera rig
// keys: [{ t, pos: [x,y,z], target: [x,y,z], fov?, roll?, ease? }], sorted by t. The ease of a key shapes the move
// that ARRIVES at it. Before the first key and after the last the camera holds that key, plus drift.
// o.drift: amplitude in world units of a seeded wander on position and target (the camera is never still).
export function cameraRig(keys, o = {}) {
  const amp = o.drift ?? 0;
  const dx = drift((o.seed ?? 7) + 1), dy = drift((o.seed ?? 7) + 2), dz = drift((o.seed ?? 7) + 3);
  const out = { pos: new THREE.Vector3(), target: new THREE.Vector3(), fov: 40, roll: 0 };
  const a = new THREE.Vector3(), b = new THREE.Vector3();
  return function at(t) {
    let i = 0;
    while (i < keys.length - 1 && t >= keys[i + 1].t) i++;
    const k0 = keys[i], k1 = keys[Math.min(i + 1, keys.length - 1)];
    const k = k1 === k0 || t <= k0.t ? 0 : ease(k1.ease || "power2.inOut")(clamp01((t - k0.t) / (k1.t - k0.t)));
    out.pos.copy(a.fromArray(k0.pos)).lerp(b.fromArray(k1.pos), k);
    out.target.copy(a.fromArray(k0.target)).lerp(b.fromArray(k1.target), k);
    out.fov = lerp(k0.fov ?? 40, k1.fov ?? 40, k);
    out.roll = lerp(k0.roll ?? 0, k1.roll ?? 0, k);
    if (amp) {
      out.pos.x += dx(t) * amp; out.pos.y += dy(t) * amp; out.pos.z += dz(t) * amp * 0.5;
      out.target.x += dy(t + 3) * amp * 0.4; out.target.y += dz(t + 5) * amp * 0.4;
    }
    return out;
  };
}

// Dive into a surface (principles: "Dive"). From a rig sample `from` ({ pos, target }) to `endHeight` above the
// surface point `p` with normal `n` and on-screen up `up`: the camera first swings onto the normal (power2.inOut over
// the first `swing` share), then falls along it with power3.in, so the surface is met head-on, never at a graze.
// k: 0..1 progress of the dive (linear). Returns { pos, target, up } for stage.setCamera.
export function dive(k, from, p, n, up, endHeight, o = {}) {
  const swing = o.swing ?? 0.55;
  const ks = ease("power2.inOut")(clamp01(k / swing));
  const kf = ease(o.ease ?? "power3.in")(clamp01(k));
  const d0 = from.pos.distanceTo(p);
  const dir = from.pos.clone().sub(p).normalize().lerp(n, ks).normalize();
  // the swing already pushes in (to `push` of the start distance), so the object never shrinks while the camera turns
  const pos = p.clone().addScaledVector(dir, lerp(d0 * lerp(1, o.push ?? 0.6, ks), endHeight, kf));
  const target = from.target.clone().lerp(p, ks);
  const camUp = new THREE.Vector3(0, 1, 0).lerp(up, ks).normalize();
  return { pos, target, up: camUp, fov: from.fov ?? 40 };
}

// ---------------------------------------------------------------- the stage: renderer, camera, bloom, flash
// Two renders a frame: the scene, then the same scene in "glow" mode (each material outputs only its accent and glow
// share), blurred at half size and added on top. Only the accent and glowing points bloom; white lines never do.
export function createStage(canvas, o = {}) {
  const W = o.width ?? 1920, H = o.height ?? 1080;
  const look = { ...LOOK, ...(o.look || {}) };
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, preserveDrawingBuffer: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(1);
  renderer.setSize(W, H, false);
  renderer.outputColorSpace = THREE.LinearSRGBColorSpace; // colours are written as given, no conversion
  renderer.autoClear = false;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(40, W / H, 0.01, 200);
  const shared = {
    uGlowPass: { value: 0 },
    uAccent: { value: new THREE.Color(look.accent) },
    uFog: { value: new THREE.Vector3(look.fogNear, look.fogFar, look.fogMin) },
  };

  const rtOpts = { type: THREE.HalfFloatType, depthBuffer: true };
  const rtMain = new THREE.WebGLRenderTarget(W, H, { ...rtOpts, samples: 4 });
  const rtGlow = new THREE.WebGLRenderTarget(W, H, { ...rtOpts, samples: 4 });
  const hw = W >> 1, hh = H >> 1;
  const rtA = new THREE.WebGLRenderTarget(hw, hh, { type: THREE.HalfFloatType, depthBuffer: false });
  const rtB = new THREE.WebGLRenderTarget(hw, hh, { type: THREE.HalfFloatType, depthBuffer: false });

  const quadCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2));
  const quadScene = new THREE.Scene();
  quadScene.add(quad);
  const fsVert = "varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }";
  const blurMat = new THREE.ShaderMaterial({
    uniforms: { tSrc: { value: null }, uDir: { value: new THREE.Vector2() } },
    vertexShader: fsVert,
    fragmentShader: `uniform sampler2D tSrc; uniform vec2 uDir; varying vec2 vUv;
      void main(){
        vec3 c = texture2D(tSrc, vUv).rgb * 0.1964825501511404;
        c += texture2D(tSrc, vUv + uDir * 1.411764705882353).rgb * 0.2969069646728344;
        c += texture2D(tSrc, vUv - uDir * 1.411764705882353).rgb * 0.2969069646728344;
        c += texture2D(tSrc, vUv + uDir * 3.2941176470588234).rgb * 0.09447039785044732;
        c += texture2D(tSrc, vUv - uDir * 3.2941176470588234).rgb * 0.09447039785044732;
        c += texture2D(tSrc, vUv + uDir * 5.176470588235294).rgb * 0.010381362401148057;
        c += texture2D(tSrc, vUv - uDir * 5.176470588235294).rgb * 0.010381362401148057;
        gl_FragColor = vec4(c, 1.0);
      }`,
    depthTest: false, depthWrite: false,
  });
  const compMat = new THREE.ShaderMaterial({
    uniforms: {
      tMain: { value: rtMain.texture }, tGlow: { value: rtGlow.texture }, tBloom: { value: rtA.texture },
      uBg: { value: new THREE.Color(look.background) }, uStrength: { value: look.bloomStrength }, uFlash: { value: 0 },
    },
    vertexShader: fsVert,
    fragmentShader: `uniform sampler2D tMain, tGlow, tBloom; uniform vec3 uBg; uniform float uStrength, uFlash; varying vec2 vUv;
      void main(){
        vec3 c = uBg + texture2D(tMain, vUv).rgb;
        c += texture2D(tGlow, vUv).rgb * 0.35 + texture2D(tBloom, vUv).rgb * uStrength;
        c += vec3(uFlash) * (1.0 - 0.45 * length(vUv - 0.5));
        gl_FragColor = vec4(min(c, vec3(1.0)), 1.0);
      }`,
    depthTest: false, depthWrite: false,
  });

  const stage = {
    THREE, W, H, look, renderer, scene, camera, shared, flash: 0, bloomStrength: look.bloomStrength,
    add(obj) { scene.add(obj); return obj; },
    // Point the camera from a rig sample ({ pos, target, fov, roll } or { pos, target, up }).
    setCamera(c) {
      camera.position.copy(c.pos);
      if (c.up) camera.up.copy(c.up);
      else camera.up.set(Math.sin(c.roll || 0), Math.cos(c.roll || 0), 0);
      camera.lookAt(c.target);
      if (camera.fov !== c.fov) { camera.fov = c.fov; camera.updateProjectionMatrix(); }
    },
    // A world point in screen pixels (for HUD leader lines and labels); visible = in front of the camera.
    project(v) {
      const p = v.clone().project(camera);
      return { x: (p.x * 0.5 + 0.5) * W, y: (-p.y * 0.5 + 0.5) * H, visible: p.z < 1 && p.z > -1 };
    },
    render() {
      camera.updateMatrixWorld();
      renderer.setClearColor(0x000000, 1);
      shared.uGlowPass.value = 0;
      renderer.setRenderTarget(rtMain); renderer.clear(); renderer.render(scene, camera);
      shared.uGlowPass.value = 1;
      renderer.setRenderTarget(rtGlow); renderer.clear(); renderer.render(scene, camera);
      shared.uGlowPass.value = 0;
      // bloom: glow -> half size, two separable passes, the second one wider
      const r = look.bloomRadius;
      const pass = (src, dst, dx, dy) => {
        blurMat.uniforms.tSrc.value = src.texture; blurMat.uniforms.uDir.value.set(dx / hw, dy / hh);
        quad.material = blurMat; renderer.setRenderTarget(dst); renderer.render(quadScene, quadCam);
      };
      pass(rtGlow, rtA, r, 0); pass(rtA, rtB, 0, r);
      pass(rtB, rtA, r * 2.5, 0); pass(rtA, rtB, 0, r * 2.5);
      pass(rtB, rtA, r * 5, 0); pass(rtA, rtB, 0, r * 5);
      compMat.uniforms.tBloom.value = rtB.texture;
      compMat.uniforms.uFlash.value = stage.flash;
      compMat.uniforms.uStrength.value = stage.bloomStrength;
      quad.material = compMat; renderer.setRenderTarget(null); renderer.clear(); renderer.render(quadScene, quadCam);
    },
  };
  return stage;
}

// ---------------------------------------------------------------- the line look
// One material for every line: white at `alpha`, faded by depth fog, the side facing away from the camera dashed
// and dimmer (needs a `normal` attribute), drawn on along `aT` (0..1 per polyline) up to `draw`, and mixed to the
// accent by `pulse`. In the glow pass it writes only the accent share and `glow`.
const LINE_VERT = `
  attribute float aT; attribute float aDist;
  uniform vec3 uFog;
  varying float vT, vDist, vFog, vFacing;
  void main(){
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    vT = aT; vDist = aDist;
    vFog = mix(1.0, uFog.z, smoothstep(uFog.x, uFog.y, -mv.z));
    #ifdef L3_FACING
      vec3 n = normalize(normalMatrix * normal);
      vFacing = dot(n, normalize(-mv.xyz));
    #else
      vFacing = 1.0;
    #endif
    gl_Position = projectionMatrix * mv;
  }`;
const LINE_FRAG = `
  uniform vec3 uColor, uAccent; uniform float uAlpha, uBack, uDash, uDraw, uPulse, uGlow, uGlowPass, uHold;
  varying float vT, vDist, vFog, vFacing;
  void main(){
    if (vT > uDraw) discard;
    float a = uAlpha * vFog;
    if (vFacing < 0.0) {
      if (uDash > 0.0 && fract(vDist / uDash) > 0.5) discard;
      a *= uBack;
    }
    float p = max(uPulse, uHold);
    vec3 c = mix(uColor, uAccent, p);
    if (uGlowPass > 0.5) {
      gl_FragColor = vec4((uAccent * p + uColor * uGlow) * a, 1.0);
    } else {
      gl_FragColor = vec4(c * a, 1.0);
    }
  }`;

export function lineMaterial(stage, o = {}) {
  const look = stage.look;
  const m = new THREE.ShaderMaterial({
    uniforms: {
      uAccent: stage.shared.uAccent, uFog: stage.shared.uFog, uGlowPass: stage.shared.uGlowPass,
      uColor: { value: new THREE.Color(o.color ?? look.line) },
      uAlpha: { value: o.alpha ?? look.lineAlpha },
      uBack: { value: o.back ?? look.backAlpha },
      uDash: { value: o.dash ?? look.dash },
      uDraw: { value: o.draw ?? 1 },
      uPulse: { value: 0 }, uHold: { value: o.hold ?? 0 }, uGlow: { value: o.glow ?? 0 },
    },
    defines: o.facing === false ? {} : { L3_FACING: 1 },
    vertexShader: LINE_VERT, fragmentShader: LINE_FRAG,
    transparent: true, depthTest: false, depthWrite: false, blending: THREE.AdditiveBlending,
  });
  // Shorthands for draw(t): m.set({ alpha, draw, pulse, hold, glow })
  m.set = (v) => {
    for (const k in v) {
      const u = m.uniforms["u" + k[0].toUpperCase() + k.slice(1)];
      if (u) u.value = v[k];
    }
    return m;
  };
  return m;
}

// LineSegments from a builder's output: { positions, normals?, t, dist } (flat arrays, segment pairs).
export function lines(stage, geo, o = {}) {
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(geo.positions, 3));
  if (geo.normals) g.setAttribute("normal", new THREE.Float32BufferAttribute(geo.normals, 3));
  g.setAttribute("aT", new THREE.Float32BufferAttribute(geo.t, 1));
  g.setAttribute("aDist", new THREE.Float32BufferAttribute(geo.dist, 1));
  const mat = lineMaterial(stage, { ...o, facing: !!geo.normals && o.facing !== false });
  const obj = new THREE.LineSegments(g, mat);
  obj.frustumCulled = false;
  obj.set = mat.set;
  return obj;
}

// ---------------------------------------------------------------- geometry builders
// Each returns { positions, normals?, t, dist } as segment pairs. `t` runs 0..1 along each polyline (draw-on order),
// `dist` is the length along it (dashes). Builders know nothing about materials or time.
function Geo() {
  const g = { positions: [], normals: [], t: [], dist: [], hasNormals: false };
  // Push a polyline: pts = [[x,y,z],...], nrm = same length or null, t0/t1 = its draw-on range.
  g.poly = (pts, nrm, t0 = 0, t1 = 1, closed = false) => {
    const P = closed ? [...pts, pts[0]] : pts;
    const N = nrm ? (closed ? [...nrm, nrm[0]] : nrm) : null;
    if (N) g.hasNormals = true;
    let d = 0;
    for (let i = 0; i < P.length - 1; i++) {
      const a = P[i], b = P[i + 1];
      const len = Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]);
      g.positions.push(...a, ...b);
      g.normals.push(...(N ? N[i] : [0, 0, 1]), ...(N ? N[i + 1] : [0, 0, 1]));
      g.t.push(lerp(t0, t1, i / (P.length - 1)), lerp(t0, t1, (i + 1) / (P.length - 1)));
      g.dist.push(d, d + len);
      d += len;
    }
    return g;
  };
  g.done = () => ({ positions: g.positions, normals: g.hasNormals ? g.normals : null, t: g.t, dist: g.dist });
  return g;
}

const toXYZ = (r, lat, lon) => [r * Math.cos(lat) * Math.sin(lon), r * Math.sin(lat), r * Math.cos(lat) * Math.cos(lon)];

// Latitude-longitude sphere. Draw-on: latitudes from the equator outward, then meridians from pole to pole.
export function sphereLatLong(o = {}) {
  const r = o.radius ?? 1, nLat = o.lat ?? 9, nLon = o.lon ?? 12, seg = o.segments ?? 128;
  const g = Geo();
  const lats = [];
  for (let i = 1; i < nLat; i++) lats.push(-Math.PI / 2 + (i * Math.PI) / nLat);
  lats.sort((a, b) => Math.abs(a) - Math.abs(b));
  lats.forEach((lat, k) => {
    const pts = [], nrm = [];
    for (let j = 0; j < seg; j++) { const p = toXYZ(r, lat, (j / seg) * Math.PI * 2); pts.push(p); nrm.push(p.map((v) => v / r)); }
    const t0 = (k / lats.length) * 0.5;
    g.poly(pts, nrm, t0, t0 + 0.5 / lats.length + 0.15, true);
  });
  for (let i = 0; i < nLon; i++) {
    const lon = (i / nLon) * Math.PI * 2, pts = [], nrm = [];
    for (let j = 0; j <= seg / 2; j++) { const p = toXYZ(r, -Math.PI / 2 + (j / (seg / 2)) * Math.PI, lon); pts.push(p); nrm.push(p.map((v) => v / r)); }
    g.poly(pts, nrm, 0.45 + (i / nLon) * 0.3, 0.75 + (i / nLon) * 0.25);
  }
  return g.done();
}

// A circle (ring) in the XY plane, or on a sphere at latitude `lat` when `sphere` is given.
export function ring(o = {}) {
  const r = o.radius ?? 1, seg = o.segments ?? 128, g = Geo(), pts = [];
  for (let j = 0; j < seg; j++) { const a = (j / seg) * Math.PI * 2; pts.push([Math.cos(a) * r, Math.sin(a) * r, 0]); }
  return g.poly(pts, null, 0, 1, true).done();
}

// Cell-matrix surface on a sphere: small outlined squares where mask(lat, lon) is true (lat, lon in radians).
// cell: angular size of one cell (the same step in latitude and longitude, so rows and columns line up everywhere
// and a dive can hand over to a flat cellGrid of the same pitch); gap: share of the cell left empty.
// Draw-on order: `order(lat, lon)` -> 0..1 (e.g. distance from the region's centre, so a region grows outward).
// Cell centres sit at lat = -PI/2 + cell/2 + i*cell and lon = j*cell (cellCentre() gives the nearest one).
export function sphereCells(o = {}) {
  const r = o.radius ?? 1.002, cell = o.cell ?? 0.035, gap = o.gap ?? 0.3, g = Geo();
  const half = (cell * (1 - gap)) / 2;
  const order = o.order || (() => 0);
  for (let lat = -Math.PI / 2 + cell / 2; lat < Math.PI / 2; lat += cell) {
    for (let lon = 0; lon < Math.PI * 2 - cell / 2; lon += cell) {
      if (!o.mask(lat, lon)) continue;
      const dl = half;
      const c = [toXYZ(r, lat - half, lon - dl), toXYZ(r, lat - half, lon + dl), toXYZ(r, lat + half, lon + dl), toXYZ(r, lat + half, lon - dl)];
      const n = c.map((p) => p.map((v) => v / r));
      const t0 = clamp01(order(lat, lon));
      g.poly(c, n, t0, t0, true);
    }
  }
  return g.done();
}

// The sphereCells cell centre nearest to (lat, lon), and the surface frame there.
export function cellCentre(lat, lon, cell) {
  const la = -Math.PI / 2 + cell / 2 + Math.round((lat - (-Math.PI / 2 + cell / 2)) / cell) * cell;
  const lo = Math.round(lon / cell) * cell;
  return { lat: la, lon: lo };
}

// Seeded blob regions on a sphere (fictional land masses): returns [{ lat, lon, mask(lat, lon), dist(lat, lon) }].
export function blobRegions(o = {}) {
  const rnd = mulberry32(o.seed ?? 11), n = o.count ?? 4, out = [];
  for (let i = 0; i < n; i++) {
    const c = o.centres?.[i] ?? [(rnd() - 0.5) * 1.6, rnd() * Math.PI * 2];
    const size = (o.size ?? 0.42) * (0.75 + rnd() * 0.5);
    const lobes = Array.from({ length: 5 }, () => [(rnd() - 0.5) * size * 1.4, (rnd() - 0.5) * size * 1.8, size * (0.35 + rnd() * 0.45)]);
    const centre = new THREE.Vector3(...toXYZ(1, c[0], c[1]));
    const ang = (lat, lon, la, lo) => centre.set(...toXYZ(1, la, lo)).angleTo(new THREE.Vector3(...toXYZ(1, lat, lon)));
    const dist = (lat, lon) => ang(lat, lon, c[0], c[1]);
    const mask = (lat, lon) => {
      if (dist(lat, lon) < size * 0.55) return true;
      return lobes.some(([dla, dlo, s]) => ang(lat, lon, c[0] + dla, c[1] + dlo / Math.max(0.3, Math.cos(c[0]))) < s);
    };
    out.push({ lat: c[0], lon: c[1], size, mask, dist, point: (rad = 1) => new THREE.Vector3(...toXYZ(rad, c[0], c[1])) });
  }
  return out;
}

// Flat grid of lines in the XZ plane (a floor), size x size, `div` cells a side. Draw-on from the centre out.
export function gridFloor(o = {}) {
  const s = o.size ?? 20, div = o.div ?? 40, g = Geo(), h = s / 2;
  for (let i = 0; i <= div; i++) {
    const v = -h + (i * s) / div, t0 = Math.abs(v) / h * 0.6;
    g.poly([[v, 0, -h], [v, 0, h]], null, t0, t0 + 0.4);
    g.poly([[-h, 0, v], [h, 0, v]], null, t0, t0 + 0.4);
  }
  return g.done();
}

// Outlined cells on the XZ plane (city blocks, storage, a board): squares of `cell` with `gap`, on cols x rows,
// where keep(i, j) is true; height(i, j) > 0 extrudes the cell into a wire box. Draw-on by distance from the centre.
export function cellGrid(o = {}) {
  const cols = o.cols ?? 40, rows = o.rows ?? 40, cell = o.cell ?? 0.2, gap = o.gap ?? 0.3, g = Geo();
  const keep = o.keep || (() => true), height = o.height || (() => 0), q = (cell * (1 - gap)) / 2;
  const maxD = Math.hypot(cols, rows) / 2;
  for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) {
    if (!keep(i, j)) continue;
    const x = (i - cols / 2 + 0.5) * cell, z = (j - rows / 2 + 0.5) * cell;
    const t0 = (Math.hypot(i - cols / 2, j - rows / 2) / maxD) * 0.85, hgt = height(i, j);
    const base = [[x - q, 0, z - q], [x + q, 0, z - q], [x + q, 0, z + q], [x - q, 0, z + q]];
    if (o.base !== false) g.poly(base, null, t0, t0 + 0.05, true);
    if (hgt > 0) {
      const top = base.map((p) => [p[0], hgt, p[2]]);
      g.poly(top, null, t0 + 0.05, t0 + 0.12, true);
      base.forEach((p, k) => g.poly([p, top[k]], null, t0 + 0.02, t0 + 0.1));
    }
  }
  return g.done();
}

// Wire box (w x h x d) centred at the origin; inside: true adds nothing but is the convention for a room.
export function box(o = {}) {
  const w = (o.w ?? 1) / 2, h = (o.h ?? 1) / 2, d = (o.d ?? 1) / 2, g = Geo();
  const v = [[-w, -h, -d], [w, -h, -d], [w, h, -d], [-w, h, -d], [-w, -h, d], [w, -h, d], [w, h, d], [-w, h, d]];
  [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]].forEach(([a, b], k) => g.poly([v[a], v[b]], null, k / 12, (k + 1) / 12));
  return g.done();
}

// Tunnel along -Z: `rings` cross-sections (a polygon of `sides`, or a rectangle when sides = 4) every `step`,
// with `rails` lines joining them. Draw-on from the mouth inward.
export function tunnel(o = {}) {
  const rings = o.rings ?? 30, step = o.step ?? 1, sides = o.sides ?? 4, rad = o.radius ?? 1, g = Geo();
  const shape = [];
  for (let k = 0; k < sides; k++) { const a = (k / sides) * Math.PI * 2 + Math.PI / sides; shape.push([Math.cos(a) * rad * (o.aspect ?? 1), Math.sin(a) * rad]); }
  for (let i = 0; i < rings; i++) g.poly(shape.map(([x, y]) => [x, y, -i * step]), null, i / rings, i / rings + 0.05, true);
  for (let k = 0; k < sides; k++) for (let r = 1; r <= (o.rails ?? 1); r++) {
    const a = shape[k], b = shape[(k + 1) % sides], f = r / ((o.rails ?? 1) + 1);
    const x = lerp(a[0], b[0], f), y = lerp(a[1], b[1], f);
    g.poly([[x, y, 0], [x, y, -(rings - 1) * step]], null, 0, 1);
  }
  return g.done();
}

// Copies of one builder output at many transforms: [{ p: [x,y,z], s?: number, ry?: number }]. One draw call.
export function instances(geo, xf) {
  const g = { positions: [], normals: geo.normals ? [] : null, t: [], dist: [] };
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), v = new THREE.Vector3(), e = new THREE.Euler();
  xf.forEach((x, k) => {
    m.compose(new THREE.Vector3(...x.p), q.setFromEuler(e.set(0, x.ry ?? 0, 0)), new THREE.Vector3().setScalar(x.s ?? 1));
    for (let i = 0; i < geo.positions.length; i += 3) {
      v.set(geo.positions[i], geo.positions[i + 1], geo.positions[i + 2]).applyMatrix4(m);
      g.positions.push(v.x, v.y, v.z);
      if (geo.normals) g.normals.push(geo.normals[i], geo.normals[i + 1], geo.normals[i + 2]);
    }
    const tk = x.t ?? 0;
    geo.t.forEach((t) => g.t.push(Math.max(t, tk)));
    g.dist.push(...geo.dist);
  });
  return g;
}

// Outline of a standing figure (head circle + body), 1 unit tall, in the XY plane. For crowds via instances().
export function figure(o = {}) {
  const g = Geo(), seg = 24, hr = 0.09;
  const head = [];
  for (let k = 0; k < seg; k++) { const a = (k / seg) * Math.PI * 2; head.push([Math.cos(a) * hr, 0.88 + Math.sin(a) * hr, 0]); }
  g.poly(head, null, 0, 0.3, true);
  const body = [[-0.06, 0.78], [-0.17, 0.72], [-0.2, 0.42], [-0.15, 0.42], [-0.14, 0.62], [-0.13, 0.0], [-0.03, 0.0], [0, 0.38], [0.03, 0.0], [0.13, 0.0], [0.14, 0.62], [0.15, 0.42], [0.2, 0.42], [0.17, 0.72], [0.06, 0.78]];
  g.poly(body.map(([x, y]) => [x, y, 0]), null, 0.3, 1, true);
  if (o.stripes) for (let y = 0.05; y < 0.75; y += o.stripes) g.poly([[-0.13, y, 0], [0.13, y, 0]], null, 0.5, 1);
  return g.done();
}

// ---------------------------------------------------------------- points: dust, stars, galaxy, warp
// A point cloud with per-point size and brightness; `glow` share blooms. Points born over `birth` (0..1 per point)
// appear when draw >= birth. positions: flat array; o.sizes, o.births: per point arrays (optional).
export function points(stage, positions, o = {}) {
  const n = positions.length / 3, rnd = mulberry32(o.seed ?? 5);
  const size = new Float32Array(n), birth = new Float32Array(n);
  for (let i = 0; i < n; i++) { size[i] = o.sizes ? o.sizes[i] : 0.6 + rnd() * 0.8; birth[i] = o.births ? o.births[i] : 0; }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  g.setAttribute("aSize", new THREE.BufferAttribute(size, 1));
  g.setAttribute("aBirth", new THREE.BufferAttribute(birth, 1));
  const mat = new THREE.ShaderMaterial({
    uniforms: {
      uAccent: stage.shared.uAccent, uFog: stage.shared.uFog, uGlowPass: stage.shared.uGlowPass,
      uColor: { value: new THREE.Color(o.color ?? stage.look.line) }, uAlpha: { value: o.alpha ?? 0.8 },
      uSize: { value: o.size ?? 2.5 }, uDraw: { value: 1 }, uPulse: { value: 0 }, uHold: { value: 0 }, uGlow: { value: o.glow ?? 0 },
      uPx: { value: stage.H / 1080 },
    },
    vertexShader: `attribute float aSize, aBirth; uniform vec3 uFog; uniform float uSize, uDraw, uPx;
      varying float vFog, vOn;
      void main(){
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        vFog = mix(1.0, uFog.z, smoothstep(uFog.x, uFog.y, -mv.z));
        vOn = step(aBirth, uDraw);
        gl_PointSize = max(1.0, uSize * aSize * uPx * 4.0 / max(0.5, -mv.z));
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: `uniform vec3 uColor, uAccent; uniform float uAlpha, uPulse, uHold, uGlow, uGlowPass;
      varying float vFog, vOn;
      void main(){
        if (vOn < 0.5) discard;
        float d = length(gl_PointCoord - 0.5);
        float a = smoothstep(0.5, 0.15, d) * uAlpha * vFog;
        float p = max(uPulse, uHold);
        vec3 c = mix(uColor, uAccent, p);
        gl_FragColor = vec4((uGlowPass > 0.5 ? uAccent * p + uColor * uGlow : c) * a, 1.0);
      }`,
    transparent: true, depthTest: false, depthWrite: false, blending: THREE.AdditiveBlending,
  });
  mat.set = (v) => { for (const k in v) { const u = mat.uniforms["u" + k[0].toUpperCase() + k.slice(1)]; if (u) u.value = v[k]; } return mat; };
  const obj = new THREE.Points(g, mat);
  obj.frustumCulled = false;
  obj.set = mat.set;
  return obj;
}

// Seeded positions: a dust box, a shell (stars on a skybox), a spiral galaxy disc.
export function scatter(n, o = {}) {
  const r = mulberry32(o.seed ?? 3), out = new Float32Array(n * 3), kind = o.kind ?? "box";
  for (let i = 0; i < n; i++) {
    let x, y, z;
    if (kind === "box") { x = (r() - 0.5) * (o.w ?? 10); y = (r() - 0.5) * (o.h ?? 10); z = (r() - 0.5) * (o.d ?? 10); }
    else if (kind === "shell") { const u = r() * 2 - 1, a = r() * Math.PI * 2, s = Math.sqrt(1 - u * u), R = o.radius ?? 10; x = s * Math.cos(a) * R; y = u * R; z = s * Math.sin(a) * R; }
    else { // galaxy
      const arms = o.arms ?? 3, R = o.radius ?? 3, k = Math.pow(r(), 1.5), arm = (i % arms) / arms * Math.PI * 2;
      const th = arm + k * (o.spin ?? 4.5) + (r() - 0.5) * 0.5 * (1 - k * 0.5), rr = k * R + (r() - 0.5) * 0.25;
      x = Math.cos(th) * rr; z = Math.sin(th) * rr; y = (r() - 0.5) * 0.12 * (1 - k);
    }
    out[i * 3] = x; out[i * 3 + 1] = y; out[i * 3 + 2] = z;
  }
  return out;
}

// Warp streaks: n radial segments from near the axis outward, along -Z. A line builder (use with lines()).
export function warp(o = {}) {
  const r = mulberry32(o.seed ?? 9), n = o.count ?? 400, g = Geo();
  for (let i = 0; i < n; i++) {
    const a = r() * Math.PI * 2, rad = 0.4 + r() * (o.radius ?? 4), z = -r() * (o.depth ?? 30), len = 0.5 + r() * (o.length ?? 3);
    g.poly([[Math.cos(a) * rad, Math.sin(a) * rad, z], [Math.cos(a) * rad, Math.sin(a) * rad, z - len]], null, r() * 0.8, 1);
  }
  return g.done();
}

// ---------------------------------------------------------------- text on a 3D path
// Glyph sprites (one canvas texture per glyph) placed along a THREE.Curve, facing the camera's plane of the curve.
// update(progress): glyphs up to `progress` (0..1) are shown; `accentFrom` index onward can be pulsed with set().
export async function textPath(stage, text, curve, o = {}) {
  const font = o.font ?? "700 64px 'Archivo Black'";
  await document.fonts.load(font);
  const size = o.size ?? 0.18, group = new THREE.Group(), glyphs = [];
  const cv = document.createElement("canvas"), ctx = cv.getContext("2d");
  ctx.font = font;
  const widths = [...text].map((ch) => ctx.measureText(ch).width);
  const total = widths.reduce((a, b) => a + b, 0), len = curve.getLength(), scale = (size / 64);
  let at = (o.start ?? 0) * len;
  [...text].forEach((ch, i) => {
    const w = widths[i] * scale;
    if (ch.trim()) {
      const c = document.createElement("canvas"); c.width = Math.ceil(widths[i]) + 8; c.height = 88;
      const x = c.getContext("2d"); x.font = font; x.fillStyle = "#fff"; x.textBaseline = "middle"; x.fillText(ch, 4, 46);
      const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.NoColorSpace;
      const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthTest: false, depthWrite: false, opacity: 1, blending: THREE.AdditiveBlending });
      const m = new THREE.Mesh(new THREE.PlaneGeometry(c.width * scale, c.height * scale), mat);
      const u = Math.min(1, (at + w / 2) / len), p = curve.getPointAt(u), tan = curve.getTangentAt(u);
      m.position.copy(p); m.rotation.z = Math.atan2(tan.y, tan.x);
      group.add(m); glyphs.push({ m, at: (at + w / 2) / len });
    }
    at += w;
  });
  group.update = (progress) => glyphs.forEach((g) => (g.m.visible = g.at <= progress * ((o.start ?? 0) + total * scale / len)));
  return group;
}
