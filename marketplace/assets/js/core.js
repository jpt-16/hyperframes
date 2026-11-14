// JT Builds "The hardest app to build": shared 3D kit. Renderer with bloom, helpers, scale-model people, the phone, the car.
// Everything is a pure function of time, so each frame is exact and repeatable. Units are metres.
import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { Reflector } from "three/addons/objects/Reflector.js";
export { THREE, RoundedBoxGeometry, Reflector };

export const W = 1080, H = 1920;
export const v3 = (x, y, z) => new THREE.Vector3(x, y, z);
export const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
export const lerp = (a, b, u) => a + (b - a) * u;
export const smooth = (u) => { u = clamp(u, 0, 1); return u * u * (3 - 2 * u); };
export const easeIO = (u) => { u = clamp(u, 0, 1); return u < .5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2; };
export const easeOut = (u) => 1 - Math.pow(1 - clamp(u, 0, 1), 3);
export const ramp = (t, a, b) => clamp((t - a) / (b - a), 0, 1);
export const A = (a) => v3(a[0], a[1], a[2]);
export function rng(seed) { let s = seed; return () => ((s = (s * 16807) % 2147483647) / 2147483647); }

// the palette: charcoal, warm white, one amber accent (JT Builds Co). Demand (customers) is ivory; supply (drivers, restaurants, detailers) is amber.
export const PAL = { bg: 0x0b0a09, char: 0x201e1d, char2: 0x2c2927, ivory: 0xe2dbcf, amber: 0xffb547, grey: 0xa09d9b, good: 0x3dd68c, bad: 0xff6161 };
export const CSSP = { bg: "#121110", bg2: "#1c1a19", tile: "#201e1d", line: "rgba(255,255,255,.08)", white: "#f7f6f4", grey: "#a09d9b", muted: "#8a8580", amber: "#ffb547", ink: "#1a1206", good: "#3dd68c", bad: "#ff6161" };

// ------------------------------------------------------------------ renderer
const canvas = document.getElementById("field-gl");
export const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W, H, false); renderer.setPixelRatio(1);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 });
const composer = new EffectComposer(renderer, rt);
const rpass = new RenderPass(new THREE.Scene(), new THREE.PerspectiveCamera());
const bloom = new UnrealBloomPass(new THREE.Vector2(W, H), 0.5, 0.65, 0.9);
composer.addPass(rpass); composer.addPass(bloom); composer.addPass(new OutputPass());
export const cam = new THREE.PerspectiveCamera(40, W / H, 0.05, 6000);
export function render(scene, { exposure = 1.0, bloomS = 0.5, bloomT = 0.9, bloomR = 0.65 } = {}) {
  renderer.toneMappingExposure = exposure; bloom.strength = bloomS; bloom.threshold = bloomT; bloom.radius = bloomR;
  rpass.scene = scene; rpass.camera = cam; composer.render();
}
export function frame(pos, look, fov, roll = 0) {
  cam.position.copy(pos); cam.fov = fov; cam.aspect = W / H; cam.up.set(Math.sin(roll), Math.cos(roll), 0); cam.updateProjectionMatrix(); cam.lookAt(look); cam.updateMatrixWorld(true);
}
// soft studio reflections for glass, paint and metal
const pmrem = new THREE.PMREMGenerator(renderer);
export const ENV = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

// ------------------------------------------------------------------ textures and small parts
export function canvasTex(w, h, draw, { srgb = true, repeat = null } = {}) {
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  draw(c.getContext("2d"), w, h);
  const t = new THREE.CanvasTexture(c);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  if (repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(repeat[0], repeat[1]); }
  return t;
}
export const dotTex = canvasTex(128, 128, (g, w) => { const gr = g.createRadialGradient(w / 2, w / 2, 0, w / 2, w / 2, w / 2); gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(0.25, "rgba(255,255,255,.6)"); gr.addColorStop(1, "rgba(255,255,255,0)"); g.fillStyle = gr; g.fillRect(0, 0, w, w); });
export function glow(color, size, op = 1) {                       // a soft additive light sprite
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: dotTex, color, transparent: true, opacity: op, depthWrite: false, blending: THREE.AdditiveBlending }));
  s.scale.setScalar(size); return s;
}
export const matte = (c, rough = 0.82) => new THREE.MeshStandardMaterial({ color: c, roughness: rough, envMap: ENV, envMapIntensity: 0.25 });
export const lit = (c, k = 1) => new THREE.MeshBasicMaterial({ color: new THREE.Color(c).multiplyScalar(k) });
export function box(w, h, d, m, x = 0, y = 0, z = 0, r = 0) {
  const g = r ? new RoundedBoxGeometry(w, h, d, 3, r) : new THREE.BoxGeometry(w, h, d);
  const b = new THREE.Mesh(g, m); b.position.set(x, y, z); b.castShadow = b.receiveShadow = true; return b;
}
export const wpos = (o) => { o.updateWorldMatrix(true, false); return o.getWorldPosition(new THREE.Vector3()); };

// ------------------------------------------------------------------ keyed values
export const mixPose = (a, b, u) => {
  const out = {};
  for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) {
    const x = a[k], y = b[k];
    if (Array.isArray(x) || Array.isArray(y)) { const xa = x ?? y.map(() => 0), ya = y ?? x.map(() => 0); out[k] = xa.map((v, i) => lerp(v, ya[i], u)); }
    else out[k] = lerp(x ?? 0, y ?? 0, u);
  }
  return out;
};
export function keyed(frames, t) {                                // [[time, pose], ...]
  if (t <= frames[0][0]) return frames[0][1];
  for (let i = 1; i < frames.length; i++) if (t <= frames[i][0]) { const [t0, a] = frames[i - 1], [t1, b] = frames[i]; return mixPose(a, b, easeIO((t - t0) / (t1 - t0))); }
  return frames.at(-1)[1];
}
export const kf = (frames, t, ease = easeIO) => {                 // [[time, number], ...]
  if (t <= frames[0][0]) return frames[0][1];
  for (let i = 1; i < frames.length; i++) if (t <= frames[i][0]) { const [t0, a] = frames[i - 1], [t1, b] = frames[i]; return lerp(a, b, ease((t - t0) / (t1 - t0))); }
  return frames.at(-1)[1];
};

// ------------------------------------------------------------------ people: architectural scale figures, 1.75 m, one matte colour each
function limb(len, r0, r1, mat) {
  const g = new THREE.Group();
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r0, r1, len, 14), mat); m.position.y = -len / 2; m.castShadow = true; g.add(m);
  const j = new THREE.Mesh(new THREE.SphereGeometry(r0, 14, 10), mat); j.castShadow = true; g.add(j);
  return g;
}
const TORSO = new THREE.LatheGeometry([[0.0, -0.02], [0.118, 0], [0.132, 0.07], [0.12, 0.2], [0.15, 0.36], [0.168, 0.46], [0.15, 0.52], [0.07, 0.555], [0.046, 0.6], [0.0, 0.6]].map(([r, y]) => new THREE.Vector2(r, y)), 24);
export function makeFigure(color, { phone = false, scale = 1 } = {}) {
  const mat = matte(color, 0.78);
  const root = new THREE.Group();
  const pelvis = new THREE.Group(); pelvis.position.y = 0.93; root.add(pelvis);
  const hips = new THREE.Mesh(new THREE.SphereGeometry(0.135, 18, 12), mat); hips.scale.set(1.12, 0.8, 0.78); hips.castShadow = true; pelvis.add(hips);
  const spine = new THREE.Group(); spine.position.y = 0.02; pelvis.add(spine);
  const torso = new THREE.Mesh(TORSO, mat); torso.scale.set(1.12, 1, 0.66); torso.castShadow = true; spine.add(torso);
  const neck = new THREE.Group(); neck.position.y = 0.6; spine.add(neck);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.103, 22, 16), mat); head.scale.set(0.9, 1.13, 1.0); head.position.y = 0.12; head.castShadow = true; neck.add(head);
  const P = { root, pelvis, spine, neck, mat };
  for (const s of [-1, 1]) {   // s = -1 right, +1 left (the figure faces +z)
    const k = s < 0 ? "R" : "L";
    const sh = new THREE.Group(); sh.position.set(s * 0.2, 0.5, 0); spine.add(sh);
    const ua = limb(0.29, 0.048, 0.04, mat); sh.add(ua);
    const el = new THREE.Group(); el.position.y = -0.29; ua.add(el);
    const fa = limb(0.26, 0.039, 0.03, mat); el.add(fa);
    const hand = new THREE.Group(); hand.position.y = -0.26; fa.add(hand);
    const hm = new THREE.Mesh(new RoundedBoxGeometry(0.075, 0.1, 0.035, 2, 0.015), mat); hm.position.y = -0.045; hm.castShadow = true; hand.add(hm);
    const hp = new THREE.Group(); hp.position.set(s * 0.09, -0.02, 0); pelvis.add(hp);
    const th = limb(0.44, 0.078, 0.058, mat); hp.add(th);
    const kn = new THREE.Group(); kn.position.y = -0.44; th.add(kn);
    const sn = limb(0.42, 0.056, 0.04, mat); kn.add(sn);
    const ft = new THREE.Group(); ft.position.y = -0.42; sn.add(ft);
    const foot = new THREE.Mesh(new RoundedBoxGeometry(0.09, 0.07, 0.25, 2, 0.03), mat); foot.position.set(0, -0.015, 0.07); foot.castShadow = true; ft.add(foot);
    Object.assign(P, { [`sh${k}`]: sh, [`el${k}`]: el, [`hand${k}`]: hand, [`hip${k}`]: hp, [`kn${k}`]: kn, [`ft${k}`]: ft });
  }
  if (phone) {                                                    // a lit phone in the right hand
    const ph = new THREE.Group(); ph.position.set(0, -0.09, 0.03); ph.rotation.set(-1.15, 0, 0);
    ph.add(new THREE.Mesh(new THREE.BoxGeometry(0.075, 0.15, 0.01), matte(0x111111, 0.4)));
    const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.066, 0.14), lit(phone === true ? 0xdfe9ff : phone, 1.6)); scr.position.z = 0.006; ph.add(scr);
    P.handR.add(ph); P.phone = ph; P.screen = scr;
  }
  root.scale.setScalar(scale);
  return P;
}
const D2R = Math.PI / 180;
export function applyPose(P, q) {                                 // angles in degrees: flex = forward, abd = out to the side
  P.pelvis.position.y = 0.93 + (q.drop ?? 0);
  P.pelvis.rotation.set((q.pelvisTilt ?? 0) * D2R, (q.pelvisTwist ?? 0) * D2R, 0);
  P.spine.rotation.set((q.lean ?? 0) * D2R, (q.twist ?? 0) * D2R, (q.side ?? 0) * D2R, "YXZ");
  P.neck.rotation.set((q.nod ?? 0) * D2R, (q.look ?? 0) * D2R, 0, "YXZ");
  for (const k of ["L", "R"]) {
    const s = k === "L" ? 1 : -1;
    const sh = q[`sh${k}`] ?? [0, 6, 0];
    P[`sh${k}`].rotation.set(-sh[0] * D2R, sh[2] * D2R * s, s * sh[1] * D2R, "XZY");
    P[`el${k}`].rotation.set(-(q[`el${k}`] ?? 8) * D2R, 0, 0);
    const hp = q[`hip${k}`] ?? [0, 3];
    P[`hip${k}`].rotation.set(-hp[0] * D2R, 0, s * hp[1] * D2R, "XZY");
    P[`kn${k}`].rotation.set((q[`kn${k}`] ?? 3) * D2R, 0, 0);
    P[`ft${k}`].rotation.set((q[`ank${k}`] ?? 0) * D2R, 0, 0);
  }
}
export const POSE = {
  stand: { lean: 2, shL: [4, 7, 0], shR: [4, 7, 0], elL: 12, elR: 12, hipL: [1, 4], hipR: [1, 4], knL: 4, knR: 4 },
  phone: { lean: 5, nod: 24, shL: [6, 7, 0], elL: 14, shR: [34, 4, -14], elR: 104, hipL: [1, 5], hipR: [3, 4], knL: 4, knR: 8 },     // looking down at the phone in the right hand
  phoneUp: { lean: 2, nod: 4, look: 18, shL: [6, 7, 0], elL: 14, shR: [24, 6, -10], elR: 96, hipL: [1, 5], hipR: [3, 4], knL: 4, knR: 8 },   // phone in hand, looking up and around
  wait: { lean: -2, nod: 2, shL: [18, 4, 62], elL: 92, shR: [22, 4, 62], elR: 96, hipL: [-2, 7], hipR: [2, 5], knL: 2, knR: 6, side: 2 },   // arms folded
  hips: { lean: 0, nod: 4, shL: [-14, 30, 0], elL: 74, shR: [-14, 30, 0], elR: 74, hipL: [0, 7], hipR: [0, 7], knL: 3, knR: 3 },          // hands on hips
  lean: { lean: -6, nod: 6, side: -4, shL: [10, 8, 0], elL: 20, shR: [20, 10, 0], elR: 60, hipL: [16, 4], hipR: [-4, 6], knL: 28, knR: 4 },    // leaning back against a car
  wave: { lean: 2, look: -10, shL: [6, 7, 0], elL: 14, shR: [150, 24, 0], elR: 30, hipL: [1, 5], hipR: [1, 5], knL: 4, knR: 4 },
  counter: { lean: 12, nod: 10, shL: [38, 14, 0], elL: 30, shR: [38, 14, 0], elR: 30, hipL: [4, 5], hipR: [4, 5], knL: 6, knR: 6 },             // hands on the counter
  polish: { lean: 34, nod: 6, drop: -0.06, twist: -8, shL: [20, 14, 0], elL: 40, shR: [82, 4, 0], elR: 22, hipL: [30, 6], hipR: [22, 6], knL: 24, knR: 18 },
  sit: { drop: -0.42, lean: 4, hipL: [84, 6], hipR: [84, 6], knL: 88, knR: 88, shL: [30, 8, 0], elL: 60, shR: [30, 8, 0], elR: 60 },
};
export function walkPose(ph, k = 1) {                             // ph: stride phase 0..1
  const s = Math.sin(ph * Math.PI * 2), c = Math.cos(ph * Math.PI * 2);
  return { drop: -0.015 * Math.abs(c) * k, lean: 5, hipL: [26 * s * k, 3], hipR: [-26 * s * k, 3], knL: 8 + 34 * Math.max(0, -c) * k * (s > 0 ? 0.4 : 1), knR: 8 + 34 * Math.max(0, c) * k * (s < 0 ? 0.4 : 1),
    shL: [-22 * s * k, 6, 0], shR: [22 * s * k, 6, 0], elL: 22, elR: 22, nod: 2 };
}
export const yawTo = (from, to) => Math.atan2(to.x - from.x, to.z - from.z);

// ------------------------------------------------------------------ the phone: aluminium frame, black glass, a live screen drawn on a canvas
export const SCR_W = 900, SCR_H = 1950;
export function makePhone(size = 1) {
  const g = new THREE.Group();
  const w = 0.072 * size, h = 0.156 * size, d = 0.0085 * size;
  const body = new THREE.Mesh(new RoundedBoxGeometry(w, h, d, 6, d * 0.48), new THREE.MeshStandardMaterial({ color: 0x2a2725, metalness: 0.8, roughness: 0.45, envMap: ENV, envMapIntensity: 0.22 }));
  body.castShadow = true; g.add(body);
  const glass = new THREE.Mesh(new RoundedBoxGeometry(w * 0.965, h * 0.984, d * 0.3, 4, d * 0.14), new THREE.MeshPhysicalMaterial({ color: 0x050505, roughness: 0.08, metalness: 0, envMap: ENV, envMapIntensity: 1.2, clearcoat: 1 }));
  glass.position.z = d * 0.34; g.add(glass);
  const cv = document.createElement("canvas"); cv.width = SCR_W; cv.height = SCR_H;
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 16;
  const mat = new THREE.MeshBasicMaterial({ map: tex, color: new THREE.Color(1.2, 1.2, 1.2), polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(w * 0.925, w * 0.925 * SCR_H / SCR_W), mat); scr.position.z = d * 0.56; g.add(scr);
  const ctx = cv.getContext("2d");
  return { g, scr, mat, tex, ctx, w, h, d,
    draw(fn, ...args) {                                           // fn(g2d, ...args) draws the whole screen
      ctx.save(); ctx.clearRect(0, 0, SCR_W, SCR_H);
      ctx.beginPath(); rrPath(ctx, 0, 0, SCR_W, SCR_H, 96); ctx.clip();
      fn(ctx, ...args); ctx.restore(); tex.needsUpdate = true;
    },
    bright(k) { mat.color.setScalar(k); } };
  // (the screen is tone-mapped with the scene, so it is drawn a little brighter than it should read)
}
export function rrPath(g, x, y, w, h, r) { r = Math.min(r, w / 2, h / 2); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }

// ------------------------------------------------------------------ a car: an extruded profile with a glass cabin, wheels and lights
function profile(pts, depth, bevel) {
  const s = new THREE.Shape(pts.map(([x, y]) => new THREE.Vector2(x, y)));
  const g = new THREE.ExtrudeGeometry(s, { depth, bevelEnabled: true, bevelThickness: bevel, bevelSize: bevel, bevelSegments: 4, curveSegments: 8 });
  g.translate(0, 0, -depth / 2); return g;
}
const BODY_G = profile([[-2.2, 0.36], [-2.26, 0.62], [-2.18, 0.86], [-1.5, 0.95], [-0.72, 1.0], [1.25, 1.0], [1.95, 0.94], [2.24, 0.82], [2.28, 0.5], [2.2, 0.34], [1.72, 0.3], [1.72, 0.3], [-1.6, 0.3]], 1.62, 0.09);
const CABIN_G = profile([[-0.98, 0.96], [-0.3, 1.42], [0.85, 1.44], [1.62, 0.98]], 1.34, 0.07);
const GLASS_G = profile([[-0.86, 1.0], [-0.27, 1.37], [0.82, 1.39], [1.47, 1.0]], 1.5, 0.01);
const WHEEL_G = new THREE.CylinderGeometry(0.33, 0.33, 0.24, 28); WHEEL_G.rotateX(Math.PI / 2);
const RIM_G = new THREE.CylinderGeometry(0.2, 0.2, 0.25, 20); RIM_G.rotateX(Math.PI / 2);
export function makeCar(color = 0x1b1a19, { gloss = true, accent = null } = {}) {   // faces -x (the nose is at x = -2.26); length 4.5 m
  const g = new THREE.Group();
  const paint = gloss ? new THREE.MeshPhysicalMaterial({ color, roughness: 0.28, metalness: 0.55, clearcoat: 1, clearcoatRoughness: 0.06, envMap: ENV, envMapIntensity: 1.3 })
    : new THREE.MeshStandardMaterial({ color, roughness: 0.55, metalness: 0.3, envMap: ENV, envMapIntensity: 0.5 });
  const body = new THREE.Mesh(BODY_G, paint); body.castShadow = body.receiveShadow = true; g.add(body);
  const cabin = new THREE.Mesh(CABIN_G, paint); cabin.castShadow = true; g.add(cabin);
  g.add(new THREE.Mesh(GLASS_G, new THREE.MeshPhysicalMaterial({ color: 0x07090c, roughness: 0.06, metalness: 0.2, envMap: ENV, envMapIntensity: 1.6 })));
  const tyre = matte(0x0c0c0c, 0.9), rim = new THREE.MeshStandardMaterial({ color: 0x8c8884, metalness: 0.9, roughness: 0.3, envMap: ENV });
  for (const x of [-1.38, 1.38]) for (const z of [-0.78, 0.78]) { const wl = new THREE.Mesh(WHEEL_G, tyre); wl.position.set(x, 0.33, z); wl.castShadow = true; g.add(wl); const r = new THREE.Mesh(RIM_G, rim); r.position.set(x, 0.33, z); g.add(r); }
  const head = lit(0xfff3d6, 2.6), tail = lit(0xff3b30, 1.8);
  const lights = [];
  for (const z of [-0.6, 0.6]) {
    const hl = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.09, 0.36), head); hl.position.set(-2.33, 0.72, z); g.add(hl); lights.push(hl);
    const tl = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.08, 0.4), tail); tl.position.set(2.34, 0.8, z); g.add(tl);
  }
  if (accent) { const st = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.08, 0.26), lit(accent, 2.0)); st.position.set(0.2, 1.52, 0); g.add(st); }   // a lit roof sign: a car on the platform
  return { g, paint, lights };
}

// ------------------------------------------------------------------ arcs: a pool of glowing links between two points
export function makeArcs(scene, n, { radius = 0.12, color = PAL.amber } = {}) {
  const pool = [];
  for (let i = 0; i < n; i++) {
    const geo = new THREE.TubeGeometry(new THREE.LineCurve3(v3(0, 0, 0), v3(1, 0, 0)), 40, radius, 6, false);
    const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 1, depthWrite: false })); m.visible = false; m.frustumCulled = false; scene.add(m);
    const head = glow(color, radius * 14, 1); head.visible = false; scene.add(head);
    pool.push({ m, head, key: "" });
  }
  let used = 0;
  return {
    begin() { used = 0; for (const p of pool) { p.m.visible = false; p.head.visible = false; } },
    // draw the arc a -> b up to progress u (0..1); it lifts by `lift`; fade 0..1
    arc(a, b, u, { lift = null, color = PAL.amber, op = 1, r = radius, head = true, k = 1.6, slot = null } = {}) {
      if ((slot == null && used >= pool.length) || u <= 0 || op <= 0) return;
      const p = slot != null ? pool[slot] : pool[used++], L = a.distanceTo(b), hgt = lift ?? L * 0.28;
      const key = `${a.x.toFixed(2)},${a.y.toFixed(2)},${a.z.toFixed(2)}|${b.x.toFixed(2)},${b.y.toFixed(2)},${b.z.toFixed(2)}|${hgt.toFixed(2)}|${r}`;
      const mid = a.clone().lerp(b, 0.5); mid.y += hgt * 2;
      const curve = new THREE.QuadraticBezierCurve3(a, mid, b);
      if (p.key !== key) { p.m.geometry.dispose(); p.m.geometry = new THREE.TubeGeometry(curve, 40, r, 6, false); p.key = key; }
      p.m.geometry.setDrawRange(0, Math.floor(clamp(u, 0, 1) * 40) * 6 * 6);
      p.m.material.color.set(color).multiplyScalar(k); p.m.material.opacity = op; p.m.visible = true;
      if (head && u < 1) { p.head.position.copy(curve.getPoint(clamp(u, 0, 1))); p.head.material.color.set(color); p.head.material.opacity = op; p.head.scale.setScalar(r * 16); p.head.visible = true; }
    } };
}
