// "Dive or sprint through?": the field, the players, a ground ball in the hole and one runner going down the line two ways.
// Everything is a pure function of HyperFrames time (hf-seek), so each frame is exact and repeatable.
// Units are feet. Home plate's back point is the origin, +x points toward first base's side, -z toward center field.
// The runners, the ground ball and the throw come from tools/physics.py via window.__PLAY (a model, not a measurement).
import * as THREE from "three";

const CC = window.__CC, PLAY = window.__PLAY;      // shot times from build.py, the simulated play from physics.py
const W = 1080, H = 1920;
const v3 = (x, y, z) => new THREE.Vector3(x, y, z);
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const lerp = (a, b, u) => a + (b - a) * u;
const smooth = (u) => { u = clamp(u, 0, 1); return u * u * (3 - 2 * u); };
const easeIO = (u) => { u = clamp(u, 0, 1); return u < .5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2; };

// ------------------------------------------------------------------ field geometry (feet)
const HOME = v3(0, 0, 0), B1 = v3(63.64, 0, -63.64), B2 = v3(0, 0, -127.28), B3 = v3(-63.64, 0, -63.64);
const MOUND = v3(0, 0, -59), RUBBER_Z = -60.5, MOUND_H = 0.83;

// ------------------------------------------------------------------ renderer + scene
const canvas = document.getElementById("field-gl");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W, H, false); renderer.setPixelRatio(1);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x0b1018, 320, 760);
let seed = 4242; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

function canvasTex(w, h, draw, { srgb = true, repeat = null } = {}) {
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  draw(c.getContext("2d"), w, h);
  const t = new THREE.CanvasTexture(c);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  if (repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(repeat[0], repeat[1]); }
  return t;
}

// night sky: deep navy, lighter at the horizon where the stadium lights glow
const sky = canvasTex(16, 512, (g, w, h) => {
  const gr = g.createLinearGradient(0, 0, 0, h);
  gr.addColorStop(0, "#03060c"); gr.addColorStop(0.62, "#0b1424"); gr.addColorStop(1, "#1d2a3c");
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
});
scene.background = sky;

// noise tiles, reused as canvas patterns (fast to draw, no per-pixel loops over big textures)
function noiseTile(size, n, color) {
  const c = document.createElement("canvas"); c.width = c.height = size; const g = c.getContext("2d");
  for (let k = 0; k < n; k++) { g.fillStyle = color(); g.fillRect(rnd() * size, rnd() * size, 1 + rnd() * 2, 1 + rnd() * 2); }
  return c;
}

// --- grass: a 45-degree mowing checkerboard in a 400x400 ft texture, plus fine detail
const G0 = { x: -200, z: -330, size: 400 };
const grassTex = canvasTex(2048, 2048, (g, w) => {
  const px = w / G0.size;
  g.fillStyle = "#3f6e2f"; g.fillRect(0, 0, w, w);
  g.save(); g.translate(w / 2, w / 2); g.rotate(Math.PI / 4); g.translate(-w, -w);
  g.fillStyle = "rgba(255,255,255,0.055)";
  const n = Math.ceil(2 * w / (12 * px)) + 2;
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) if (!((i + j) % 2)) g.fillRect(i * 12 * px, j * 12 * px, 12 * px, 12 * px);
  g.restore();
  g.fillStyle = g.createPattern(noiseTile(256, 2400, () => (rnd() < 0.5 ? `rgba(20,45,15,${0.06 + rnd() * 0.08})` : `rgba(120,160,80,${0.03 + rnd() * 0.05})`)), "repeat");
  g.fillRect(0, 0, w, w);
});
const grassDetail = canvasTex(512, 512, (g, w) => {
  g.fillStyle = "#808080"; g.fillRect(0, 0, w, w);
  for (let k = 0; k < 26000; k++) { const v = 90 + rnd() * 80; g.fillStyle = `rgb(${v},${v},${v})`; g.fillRect(rnd() * w, rnd() * w, 1, 2 + rnd() * 3); }
}, { srgb: false, repeat: [140, 140] });
const ground = new THREE.Mesh(new THREE.PlaneGeometry(G0.size, G0.size),
  new THREE.MeshStandardMaterial({ map: grassTex, bumpMap: grassDetail, bumpScale: 0.6, roughness: 0.95 }));
ground.rotation.x = -Math.PI / 2; ground.position.set(G0.x + G0.size / 2, 0, G0.z + G0.size / 2); ground.receiveShadow = true;
scene.add(ground);
const farGrass = new THREE.Mesh(new THREE.CircleGeometry(900, 64), new THREE.MeshStandardMaterial({ color: 0x35602a, roughness: 1 }));
farGrass.rotation.x = -Math.PI / 2; farGrass.position.y = -0.05; scene.add(farGrass);

// --- infield dirt, drawn with canvas paths over a 240x240 ft area so its edges follow the real layout:
// the skin arc (95 ft from the rubber, fair territory only) minus the infield grass, plus the home circle,
// the mound and the baselines from home to first and third.
const D0 = { x: -120, z: -200, size: 240, px: 2048 };
const dirtTex = canvasTex(D0.px, D0.px, (g, w) => {
  const k = w / D0.size, X = (x) => (x - D0.x) * k, Z = (z) => (z - D0.z) * k;
  const shape = (draw) => { g.beginPath(); draw(); g.fill(); };
  g.fillStyle = "#a8683d";
  g.save();                                                     // arc, clipped to fair territory
  g.beginPath(); g.moveTo(X(0), Z(0)); g.lineTo(X(200), Z(-200)); g.lineTo(X(-200), Z(-200)); g.closePath(); g.clip();
  shape(() => g.arc(X(0), Z(RUBBER_Z), 95 * k, 0, Math.PI * 2));
  g.restore();
  g.globalCompositeOperation = "destination-out";               // the infield grass, 3 ft in from the base paths
  shape(() => { g.moveTo(X(0), Z(-4.24)); g.lineTo(X(59.4), Z(-63.64)); g.lineTo(X(0), Z(-123.04)); g.lineTo(X(-59.4), Z(-63.64)); g.closePath(); });
  g.globalCompositeOperation = "source-over";
  shape(() => g.arc(X(0), Z(-1), 13 * k, 0, Math.PI * 2));      // home plate circle
  shape(() => g.arc(X(0), Z(MOUND.z), 9 * k, 0, Math.PI * 2));  // mound
  g.lineWidth = 6 * k; g.strokeStyle = "#a8683d";               // baselines
  g.beginPath(); g.moveTo(X(0), Z(0)); g.lineTo(X(B1.x), Z(B1.z)); g.moveTo(X(0), Z(0)); g.lineTo(X(B3.x), Z(B3.z)); g.stroke();
  g.globalCompositeOperation = "source-atop";                   // texture: grain + worn patches
  g.fillStyle = g.createPattern(noiseTile(256, 3000, () => (rnd() < 0.5 ? `rgba(70,40,20,${0.08 + rnd() * 0.12})` : `rgba(210,160,110,${0.06 + rnd() * 0.1})`)), "repeat");
  g.fillRect(0, 0, w, w);
  for (const [x, z, r] of [[0, -1, 11], [B1.x, B1.z, 9], [B2.x, B2.z, 10], [B3.x, B3.z, 9], [0, RUBBER_Z, 6]]) {
    const gr = g.createRadialGradient(X(x), Z(z), 0, X(x), Z(z), r * k);
    gr.addColorStop(0, "rgba(90,52,28,0.35)"); gr.addColorStop(1, "rgba(90,52,28,0)");
    g.fillStyle = gr; g.fillRect(X(x) - r * k, Z(z) - r * k, 2 * r * k, 2 * r * k);
  }
  g.globalCompositeOperation = "source-over";
});
const dirtDetail = canvasTex(512, 512, (g, w) => {
  g.fillStyle = "#808080"; g.fillRect(0, 0, w, w);
  for (let k = 0; k < 20000; k++) { const v = 70 + rnd() * 110; g.fillStyle = `rgb(${v},${v},${v})`; g.fillRect(rnd() * w, rnd() * w, 1 + rnd() * 2, 1 + rnd() * 2); }
}, { srgb: false, repeat: [90, 90] });
const dirt = new THREE.Mesh(new THREE.PlaneGeometry(D0.size, D0.size),
  new THREE.MeshStandardMaterial({ map: dirtTex, bumpMap: dirtDetail, bumpScale: 0.8, roughness: 1, transparent: true, depthWrite: false }));
dirt.rotation.x = -Math.PI / 2; dirt.position.set(D0.x + D0.size / 2, 0.03, D0.z + D0.size / 2); dirt.receiveShadow = true;
scene.add(dirt);

// mound: a low dome of the same dirt
const moundGeo = new THREE.LatheGeometry([v3(0, MOUND_H, 0), v3(2.5, MOUND_H, 0), v3(5.5, 0.45, 0), v3(9, 0.0, 0)].map((p) => new THREE.Vector2(p.x, p.y)), 48);
const dirtMat = new THREE.MeshStandardMaterial({ color: 0xa6683f, roughness: 1, bumpMap: dirtDetail, bumpScale: 0.6 });
const mound = new THREE.Mesh(moundGeo, dirtMat); mound.position.copy(MOUND); mound.receiveShadow = true; scene.add(mound);

// chalk: foul lines, batter's boxes, catcher's box
const chalk = new THREE.MeshStandardMaterial({ color: 0xf4f2ec, roughness: 0.9, emissive: 0x222222 });
function strip(a, b, wdt = 0.25, y = 0.045) {
  const len = a.distanceTo(b), m = new THREE.Mesh(new THREE.PlaneGeometry(wdt, len), chalk);
  m.rotation.x = -Math.PI / 2; m.rotation.z = -Math.atan2(b.x - a.x, -(b.z - a.z));
  m.position.set((a.x + b.x) / 2, y, (a.z + b.z) / 2); m.receiveShadow = true; scene.add(m);
}
strip(v3(1.5, 0, -1.5), v3(230, 0, -230)); strip(v3(-1.5, 0, -1.5), v3(-230, 0, -230));
for (const sx of [-1, 1]) {      // batter's boxes 4x6 ft, 6 in from the plate
  const x0 = sx * 1.2, x1 = sx * 5.2, z0 = 2.6, z1 = -3.4;
  strip(v3(x0, 0, z0), v3(x0, 0, z1)); strip(v3(x1, 0, z0), v3(x1, 0, z1)); strip(v3(x0, 0, z0), v3(x1, 0, z0)); strip(v3(x0, 0, z1), v3(x1, 0, z1));
}
strip(v3(-1.8, 0, 2.6), v3(-1.8, 0, 10.5)); strip(v3(1.8, 0, 2.6), v3(1.8, 0, 10.5)); strip(v3(-1.8, 0, 10.5), v3(1.8, 0, 10.5));
// running lane (last 45 ft to first)
strip(v3(63.64 - 32, 0, -63.64 + 32 + 0), v3(63.64 - 0.4, 0, -63.64 + 0.4 + 0));

// bases (15 in square), home plate, rubber
const baseMat = new THREE.MeshStandardMaterial({ color: 0xf7f6f2, roughness: 0.6 });
for (const b of [B1, B2, B3]) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(1.25, 0.25, 1.25), baseMat);
  m.position.set(b.x, 0.125, b.z); m.rotation.y = Math.PI / 4; m.castShadow = true; m.receiveShadow = true; scene.add(m);
}
const plateShape = new THREE.Shape([new THREE.Vector2(-0.708, 0), new THREE.Vector2(0.708, 0), new THREE.Vector2(0.708, 0.708), new THREE.Vector2(0, 1.416), new THREE.Vector2(-0.708, 0.708)]);
const plate = new THREE.Mesh(new THREE.ShapeGeometry(plateShape), baseMat);
plate.rotation.x = -Math.PI / 2; plate.rotation.z = Math.PI; plate.position.set(0, 0.05, -1.416); scene.add(plate);
const rubber = new THREE.Mesh(new THREE.BoxGeometry(2, 0.12, 0.5), baseMat); rubber.position.set(0, MOUND_H + 0.04, RUBBER_Z); scene.add(rubber);

// outfield wall, stands and lights (far away, mostly silhouette)
const wall = new THREE.Mesh(new THREE.CylinderGeometry(380, 380, 9, 96, 1, true, Math.PI * 0.75, Math.PI * 0.5),
  new THREE.MeshStandardMaterial({ color: 0x1d3a2a, roughness: 0.9, side: THREE.BackSide }));
wall.position.set(0, 4.5, 30); scene.add(wall);
const standTex = canvasTex(2048, 256, (g, w, h) => {
  g.fillStyle = "#0e131c"; g.fillRect(0, 0, w, h);
  for (let k = 0; k < 9000; k++) { const v = rnd(); g.fillStyle = v < 0.7 ? `rgba(70,80,100,${0.25 + rnd() * 0.3})` : `rgba(210,190,160,${0.15 + rnd() * 0.25})`; g.fillRect(rnd() * w, 30 + rnd() * (h - 40), 2, 3); }
});
const stands = new THREE.Mesh(new THREE.CylinderGeometry(560, 430, 120, 96, 1, true), new THREE.MeshStandardMaterial({ map: standTex, roughness: 1, side: THREE.BackSide, emissive: 0x0a0d12 }));
stands.position.set(0, 55, -40); scene.add(stands);

// ------------------------------------------------------------------ lights: a night game under bright banks
scene.add(new THREE.HemisphereLight(0x8fa6c8, 0x223318, 0.55));
const key = new THREE.DirectionalLight(0xfff3e2, 2.6);
key.position.set(-160, 260, 60); key.target.position.set(0, 0, -70);
key.castShadow = true; key.shadow.mapSize.set(4096, 4096);
Object.assign(key.shadow.camera, { left: -150, right: 150, top: 150, bottom: -150, near: 50, far: 700 });
key.shadow.bias = -0.0004; key.shadow.normalBias = 0.6;
scene.add(key, key.target);
const fill = new THREE.DirectionalLight(0xdfe8ff, 0.9); fill.position.set(220, 200, -120); scene.add(fill);
const rimL = new THREE.DirectionalLight(0xffffff, 0.6); rimL.position.set(0, 140, -400); scene.add(rimL);

// ------------------------------------------------------------------ players: articulated figures
const KIT = {
  home: { jersey: 0xeef0f3, pants: 0xdfe2e7, cap: 0x1c2b4b, accent: 0x1c2b4b, skin: 0x9c7055 },
  away: { jersey: 0x464c56, pants: 0x9ba2ac, cap: 0xc4352d, accent: 0xc4352d, skin: 0x7a5440 },
  ump: { jersey: 0x15181d, pants: 0x4b515b, cap: 0x0d0f12, accent: 0x0d0f12, skin: 0x8a6048 },
};
function seg(len, r, mat) {
  const g = new THREE.Group();
  const m = new THREE.Mesh(new THREE.CapsuleGeometry(r, Math.max(0.01, len - 2 * r), 6, 12), mat);
  m.position.y = -len / 2; m.castShadow = true; g.add(m); return g;
}
function makePlayer(kit, { glove = false, catcher = false, helmet = false, bat = false } = {}) {
  const M = (c, rough = 0.75) => new THREE.MeshStandardMaterial({ color: c, roughness: rough });
  const jersey = M(kit.jersey), pants = M(kit.pants), cap = M(kit.cap, 0.5), skin = M(kit.skin, 0.6), shoe = M(0x16181c, 0.6);
  const root = new THREE.Group();
  const pelvis = new THREE.Group(); pelvis.position.y = 3.1; root.add(pelvis);
  const hipsMesh = new THREE.Mesh(new THREE.SphereGeometry(0.62, 16, 12), pants); hipsMesh.scale.set(1.05, 0.62, 0.78); hipsMesh.castShadow = true; pelvis.add(hipsMesh);
  const spine = new THREE.Group(); pelvis.add(spine);
  const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.58, 1.05, 6, 16), jersey); torso.scale.set(1.18, 1, 0.74); torso.position.y = 1.0; torso.castShadow = true; spine.add(torso);
  if (catcher) { const pad = new THREE.Mesh(new THREE.BoxGeometry(1.1, 1.4, 0.3), M(0x1c2b4b, 0.6)); pad.position.set(0, 1.05, 0.42); pad.castShadow = true; spine.add(pad); }
  const neck = new THREE.Group(); neck.position.y = 1.92; spine.add(neck);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.36, 20, 16), skin); head.position.y = 0.3; head.castShadow = true; neck.add(head);
  const hat = new THREE.Mesh(new THREE.SphereGeometry(0.385, 20, 12, 0, Math.PI * 2, 0, Math.PI * (helmet || catcher ? 0.6 : 0.5)), cap);
  hat.position.y = 0.34; hat.castShadow = true; neck.add(hat);
  const bill = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.04, 16, 1, false, -Math.PI / 2, Math.PI), cap); bill.position.set(0, 0.36, 0.26); neck.add(bill);
  if (catcher) { const mask = new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.62, 0.12), M(0x23262b, 0.4)); mask.position.set(0, 0.28, 0.36); neck.add(mask); }
  const limbs = {};
  for (const s of [-1, 1]) {   // s = -1 right, +1 left (figure faces +z, so its right is -x)
    const sh = new THREE.Group(); sh.position.set(s * 0.74, 1.62, 0); spine.add(sh);
    const ua = seg(1.0, 0.18, jersey); sh.add(ua);
    const el = new THREE.Group(); el.position.y = -1.0; ua.add(el);
    const fa = seg(0.92, 0.155, skin); el.add(fa);
    const hand = new THREE.Group(); hand.position.y = -0.92; fa.add(hand);
    const isGlove = glove && s === 1;
    const hm = new THREE.Mesh(new THREE.SphereGeometry(isGlove ? 0.34 : 0.15, 14, 10), isGlove ? M(0x6b3d1f, 0.55) : skin);
    if (isGlove) hm.scale.set(1, 1.15, 0.6); hm.castShadow = true; hand.add(hm);
    const hp = new THREE.Group(); hp.position.set(s * 0.34, 0, 0); pelvis.add(hp);
    const th = seg(1.42, 0.27, pants); hp.add(th);
    const kn = new THREE.Group(); kn.position.y = -1.42; th.add(kn);
    const sn = seg(1.43, 0.2, s === 0 ? pants : pants); kn.add(sn);
    if (catcher) { const guard = new THREE.Mesh(new THREE.BoxGeometry(0.42, 1.25, 0.2), M(0x1c2b4b, 0.6)); guard.position.set(0, -0.7, 0.18); kn.add(guard); }
    const ft = new THREE.Group(); ft.position.y = -1.43; sn.add(ft);
    const foot = new THREE.Mesh(new THREE.BoxGeometry(0.36, 0.24, 0.95), shoe); foot.position.set(0, -0.06, 0.3); foot.castShadow = true; ft.add(foot);
    const k = s < 0 ? "R" : "L";
    Object.assign(limbs, { [`sh${k}`]: sh, [`el${k}`]: el, [`hand${k}`]: hand, [`hip${k}`]: hp, [`kn${k}`]: kn, [`ft${k}`]: ft });
  }
  if (bat) {
    const b = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.045, 2.8, 10), M(0xb8834e, 0.5)); b.position.y = 1.3; b.castShadow = true;
    const holder = new THREE.Group(); holder.add(b); limbs.handR.add(holder); limbs.bat = holder;
  }
  return { root, pelvis, spine, neck, ...limbs };
}
// a pose: angles in degrees. flex = forward, abd = out to the side, twist = about the vertical
const D2R = Math.PI / 180;
function applyPose(P, q) {
  P.pelvis.position.y = 3.1 + (q.drop ?? 0);
  P.pelvis.rotation.set((q.pelvisTilt ?? 0) * D2R, (q.pelvisTwist ?? 0) * D2R, 0);
  P.spine.rotation.set((q.lean ?? 0) * D2R, (q.twist ?? 0) * D2R, (q.side ?? 0) * D2R, "YXZ");
  P.neck.rotation.set((q.nod ?? 0) * D2R, (q.look ?? 0) * D2R, 0, "YXZ");
  for (const k of ["L", "R"]) {
    const s = k === "L" ? 1 : -1;
    const sh = q[`sh${k}`] ?? [0, 8, 0];   // [flex, abd, twist]
    P[`sh${k}`].rotation.set(-sh[0] * D2R, sh[2] * D2R * s, s * sh[1] * D2R, "XZY");
    P[`el${k}`].rotation.set(-(q[`el${k}`] ?? 10) * D2R, 0, 0);
    const hp = q[`hip${k}`] ?? [0, 4];       // [flex, abd]
    P[`hip${k}`].rotation.set(-hp[0] * D2R, 0, s * hp[1] * D2R, "XZY");
    P[`kn${k}`].rotation.set((q[`kn${k}`] ?? 4) * D2R, 0, 0);
    P[`ft${k}`].rotation.set((q[`ank${k}`] ?? 0) * D2R, 0, 0);
  }
}
const mixPose = (a, b, u) => {
  const out = {};
  for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) {
    const x = a[k], y = b[k];
    if (Array.isArray(x) || Array.isArray(y)) {
      const xa = x ?? y.map(() => 0), ya = y ?? x.map(() => 0);
      out[k] = xa.map((v, i) => lerp(v, ya[i], u));
    } else out[k] = lerp(x ?? 0, y ?? 0, u);
  }
  return out;
};
function keyed(frames, t) {          // frames: [[time, pose], ...] sorted
  if (t <= frames[0][0]) return frames[0][1];
  for (let i = 1; i < frames.length; i++) if (t <= frames[i][0]) {
    const [t0, a] = frames[i - 1], [t1, b] = frames[i];
    return mixPose(a, b, easeIO((t - t0) / (t1 - t0)));
  }
  return frames.at(-1)[1];
}
const yawTo = (from, to) => Math.atan2(to.x - from.x, to.z - from.z);

// sprint cycle as a function of stride phase (0..1) and how hard he's running (0..1)
function runPose(ph, k) {
  const s = Math.sin(ph * Math.PI * 2), c = Math.cos(ph * Math.PI * 2);
  return {
    drop: -0.25 * k + 0.12 * Math.abs(c) * k, lean: 14 + 10 * k,
    hipL: [10 + 48 * s * k, 4], hipR: [10 - 48 * s * k, 4],
    knL: 25 + (55 * Math.max(0, -s) + 25) * k, knR: 25 + (55 * Math.max(0, s) + 25) * k,
    shL: [-50 * s * k, 12, 0], shR: [50 * s * k, 12, 0], elL: 85, elR: 85, nod: -6,
  };
}
const LEAD_POSE = { drop: -0.75, lean: 28, hipL: [42, 22], hipR: [42, 22], knL: 52, knR: 52, shL: [18, 14, 0], shR: [18, 14, 0], elL: 25, elR: 25, nod: -18 };
const SLIDE_POSE = { drop: -2.45, pelvisTilt: 0, lean: -48, hipL: [78, 4], hipR: [52, 4], knL: 8, knR: 62, shL: [70, 30, 0], shR: [40, 30, 0], elL: 20, elR: 30, nod: 30 };
const SET_POSE = { lean: 4, look: -60, shL: [38, 4, 0], shR: [38, 4, 0], elL: 105, elR: 105, hipL: [4, 6], hipR: [4, 6], knL: 10, knR: 10 };
const CROUCH = { drop: -1.7, lean: 30, hipL: [100, 30], hipR: [100, 30], knL: 118, knR: 118, ankL: -30, ankR: -30, shL: [62, 18, 0], elL: 40, shR: [20, 10, 0], elR: 50, nod: -25 };
const READY = { drop: -0.6, lean: 30, hipL: [40, 16], hipR: [40, 16], knL: 45, knR: 45, shL: [35, 14, 0], shR: [35, 14, 0], elL: 40, elR: 40, nod: -20 };
const STAND = { lean: 2, shL: [5, 8, 0], shR: [5, 8, 0], elL: 15, elR: 15, hipL: [2, 5], hipR: [2, 5], knL: 6, knR: 6 };
const BAT_STANCE = { drop: -0.35, lean: 18, look: -80, hipL: [22, 14], hipR: [22, 14], knL: 26, knR: 26, shL: [55, 6, 0], shR: [60, 34, 0], elL: 95, elR: 110, twist: 20 };


// ------------------------------------------------------------------ the cast
const diver = makePlayer(KIT.away, { helmet: true });        // the same runner, diving head first
const runner = makePlayer(KIT.away, { helmet: true });       // ... and running through the bag
const ss = makePlayer(KIT.home, { glove: true });            // fields it in the hole and throws
const firstB = makePlayer(KIT.home, { glove: true });
const ump1 = makePlayer(KIT.ump);                            // first-base umpire
const pitcher = makePlayer(KIT.home, { glove: true });
const secondB = makePlayer(KIT.home, { glove: true });
const thirdB = makePlayer(KIT.home, { glove: true });
const catcher = makePlayer(KIT.home, { glove: true, catcher: true });
const umpH = makePlayer(KIT.ump, { catcher: true });
const coach = makePlayer(KIT.away);                          // first-base coach
const fielders = [[-110, -255], [0, -300], [112, -255]].map(([x, z]) => { const p = makePlayer(KIT.home, { glove: true }); p.root.position.set(x, 0, z); p.root.rotation.y = Math.atan2(-x, -z); applyPose(p, READY); return p; });
for (const p of [diver, runner, ss, firstB, ump1, pitcher, secondB, thirdB, catcher, umpH, ...fielders]) scene.add(p.root);   // (no base coach: same uniform as the runner)
// the run-through runner can be drawn as a see-through ghost over the diver
const ghostMats = [];
runner.root.traverse((o) => { if (o.isMesh) { o.material = o.material.clone(); ghostMats.push(o.material); } });
function ghost(on) { for (const m of ghostMats) { m.transparent = on; m.opacity = on ? 0.42 : 1; m.depthWrite = !on; m.emissive?.setHex(on ? 0x5a1a08 : 0x000000); } }
// the dropped bat
const droppedBat = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.045, 2.8, 10), new THREE.MeshStandardMaterial({ color: 0xb8834e, roughness: 0.5 }));
droppedBat.rotation.set(Math.PI / 2, 0, 0.9); droppedBat.position.set(-3.6, 0.12, -1.6); droppedBat.castShadow = true; scene.add(droppedBat);

// ------------------------------------------------------------------ the model (tools/physics.py)
const V = (a) => v3(a[0], a[1], a[2]);
const A = PLAY.assume, HZ = PLAY.hz;
const START = V(PLAY.start), DIR = V(PLAY.dir), FOUL = V(PLAY.foul), BAG = V(PLAY.b1);
const YAW = Math.atan2(DIR.x, DIR.z);
const T_RUN = PLAY.t_run, T_DIVE = PLAY.t_dive, T_PLANT = PLAY.t_plant, T_LAND = PLAY.t_land, T_STOP = PLAY.t_stop;
const T_FIELD = PLAY.t_field, T_REL = PLAY.t_release, T_ARR = PLAY.t_arrive;
const series = (arr, t) => { const u = clamp(t, 0, (arr.length - 1) / HZ) * HZ, i = Math.min(Math.floor(u), arr.length - 2); return lerp(arr[i], arr[i + 1], u - i); };
function pathAt(path, t) {
  const u = (t - path.t0) * path.hz, n = path.p.length - 1;
  if (u <= 0) return V(path.p[0]);
  if (u >= n) return V(path.p[n]);
  const i = Math.floor(u), f = u - i, a = path.p[i], b = path.p[i + 1];
  return v3(lerp(a[0], b[0], f), lerp(a[1], b[1], f), lerp(a[2], b[2], f));
}
const handPos = (h) => { h.updateWorldMatrix(true, false); return h.getWorldPosition(new THREE.Vector3()); };
window.__model = (kind, t) => kind === "run" ? { s: series(PLAY.run.s, t), v: series(PLAY.run.v, t) } : { s: series(PLAY.dive.s, t), v: series(PLAY.dive.v, t) };

// ------------------------------------------------------------------ poses for this play
const BREAK = { drop: -0.5, lean: 34, look: 0, nod: -10, hipL: [40, 8], hipR: [-10, 8], knL: 50, knR: 30, shL: [-30, 12, 0], shR: [50, 12, 0], elL: 80, elR: 80 };
const DIVE_LOAD = { drop: -0.5, lean: 34, nod: -16, hipL: [52, 6], hipR: [-22, 6], knL: 58, knR: 30, shL: [30, 14, 0], shR: [40, 14, 0], elL: 60, elR: 60 };
const DIVE_LAUNCH = { pelvisTilt: 38, lean: 16, nod: -40, hipL: [6, 6], hipR: [-26, 6], knL: 18, knR: 46, shL: [140, 16, 0], shR: [150, 12, 0], elL: 20, elR: 12 };
const DIVE_FLY = { pelvisTilt: 74, lean: 6, nod: -58, hipL: [-4, 8], hipR: [-10, 8], knL: 22, knR: 34, shL: [160, 20, 0], shR: [172, 10, 0], elL: 18, elR: 4 };
const DIVE_FLAT = { pelvisTilt: 86, lean: 3, nod: -62, hipL: [-4, 10], hipR: [-6, 10], knL: 8, knR: 14, shL: [150, 26, 0], shR: [170, 6, 0], elL: 30, elR: 2 };   // right hand reaching for the bag
const PUSH_UP = { pelvisTilt: 62, lean: -10, nod: -40, hipL: [20, 10], hipR: [30, 10], knL: 80, knR: 70, shL: [70, 16, 0], shR: [70, 16, 0], elL: 20, elR: 20 };
const KNEEL = { pelvisTilt: 10, lean: 20, nod: -10, hipL: [80, 10], hipR: [10, 10], knL: 95, knR: 100, shL: [30, 14, 0], shR: [30, 14, 0], elL: 40, elR: 40 };
const JOG = (ph) => runPose(ph, 0.35);
const B_READY = { drop: -0.4, lean: 20, nod: -8, hipL: [26, 18], hipR: [26, 18], knL: 30, knR: 30, shL: [40, 16, 0], shR: [40, 16, 0], elL: 50, elR: 50 };
const B_STRETCH = { drop: -1.0, lean: 44, nod: -12, hipL: [70, 10], hipR: [-18, 12], knL: 34, knR: 12, shL: [96, 10, 0], elL: 6, shR: [40, 10, 0], elR: 60 };
const B_REACH_OUT = { ...B_STRETCH, shL: [100, -12, 0], twist: 12 };
const SS_READY = { drop: -0.6, lean: 30, hipL: [40, 16], hipR: [40, 16], knL: 45, knR: 45, shL: [35, 14, 0], shR: [35, 14, 0], elL: 40, elR: 40, nod: -20 };
const SS_FIELD = { drop: -1.3, lean: 56, nod: -30, hipL: [80, 20], hipR: [50, 24], knL: 82, knR: 60, shL: [60, -30, 0], elL: 14, shR: [30, 16, 0], elR: 60 };   // backhand, glove down
const SS_PLANT = { drop: -0.6, lean: 12, twist: -60, look: 60, nod: -4, shL: [80, 20, 0], elL: 30, shR: [-30, 78, 0], elR: 95, hipL: [10, 12], hipR: [38, 12], knL: 40, knR: 30 };
const SS_RELEASE = { drop: -0.6, lean: 30, twist: 30, nod: 6, shL: [20, 30, 0], elL: 60, shR: [165, 20, 0], elR: 15, hipL: [46, 8], hipR: [-26, 10], knL: 40, knR: 30 };
const SS_FOLLOW = { drop: -0.8, lean: 46, twist: 48, nod: 10, shL: [10, 30, 0], elL: 70, shR: [55, -25, 0], elR: 25, hipL: [55, 8], hipR: [10, 10], knL: 52, knR: 70 };
const U1_SET = { drop: -0.9, lean: 34, nod: -8, hipL: [44, 22], hipR: [44, 22], knL: 56, knR: 56, shL: [20, 18, 0], elL: 40, shR: [20, 18, 0], elR: 40 };
const U1_SAFE = { drop: -0.4, lean: 12, hipL: [18, 14], hipR: [18, 14], knL: 22, knR: 22, shL: [90, 88, 0], elL: 5, shR: [90, 88, 0], elR: 5 };

// ------------------------------------------------------------------ the runners
// kind "run" | "dive": place the figure at play time t
function setRunner(P, kind, t) {
  const R = kind === "run" ? PLAY.run : PLAY.dive;
  const sv = series(R.s, t), vv = series(R.v, t), k = clamp(Math.pow(vv / A.vmax, 0.7), 0, 1);
  const lat = kind === "run" ? series(R.lat, t) : 0;
  P.root.position.copy(START).addScaledVector(DIR, sv).addScaledVector(FOUL, lat);
  let yaw = YAW;
  if (kind === "run") { const d = (series(R.lat, t + 0.05) - series(R.lat, t - 0.05)) / Math.max(0.5, series(R.s, t + 0.05) - series(R.s, t - 0.05)); yaw = YAW + Math.atan(d) * 0.9; }
  P.root.rotation.y = yaw;
  const ph = series(R.ph, t) % 1;
  let q;
  if (t < 0) q = mixPose(BREAK, runPose(ph, 0.3), smooth((t + 0.25) / 0.25));
  else if (kind === "run") {
    q = runPose(ph, Math.max(k, 0.25));
    if (vv < 9) q = mixPose(q, { ...STAND, look: -60, nod: -6 }, smooth((9 - vv) / 9));     // eases up, looks back at the play
  } else {
    const t0 = T_PLANT - A.stride;
    if (t < t0) q = runPose(ph, Math.max(k, 0.25));
    else if (t < T_PLANT) q = mixPose(runPose(ph, k), DIVE_LOAD, smooth((t - t0) / A.stride));
    else if (t < T_LAND) { const u = (t - T_PLANT) / (T_LAND - T_PLANT); q = u < 0.5 ? mixPose(DIVE_LAUNCH, DIVE_FLY, u / 0.5) : mixPose(DIVE_FLY, DIVE_FLAT, (u - 0.5) / 0.5); }
    else if (t < T_STOP + 0.6) q = DIVE_FLAT;
    else q = keyed([[T_STOP + 0.6, DIVE_FLAT], [T_STOP + 1.0, PUSH_UP], [T_STOP + 1.45, KNEEL], [T_STOP + 1.95, STAND]], t);
    q = { ...q, drop: series(R.y, t) - 3.1 + (t < t0 ? (q.drop ?? 0) : 0) };
    if (t > T_STOP + 0.6) q.drop = lerp(series(R.y, t) - 3.1, 0, smooth((t - T_STOP - 0.6) / 1.35));
  }
  applyPose(P, q);
}

// ------------------------------------------------------------------ the ball
function makeBall() {
  const m = new THREE.Mesh(new THREE.SphereGeometry(0.16, 16, 12), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffe9b0, emissiveIntensity: 0.6, roughness: 0.4 }));
  m.castShadow = true; scene.add(m);
  const gt = canvasTex(64, 64, (g, w) => { const gr = g.createRadialGradient(w / 2, w / 2, 0, w / 2, w / 2, w / 2); gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(0.35, "rgba(255,255,255,.55)"); gr.addColorStop(1, "rgba(255,255,255,0)"); g.fillStyle = gr; g.fillRect(0, 0, w, w); });
  const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: gt, color: 0xffd84d, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: false }));
  glow.scale.set(0.022, 0.022, 1); scene.add(glow);
  const trail = [];
  for (let i = 0; i < 40; i++) { const tr = new THREE.Mesh(new THREE.SphereGeometry(0.12 * (1 - i / 40) + 0.03, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffd84d, transparent: true, opacity: 0.45 * (1 - i / 40), depthWrite: false })); scene.add(tr); trail.push(tr); }
  return { m, glow, trail };
}
const BALL = makeBall();
function placeBall(pos, path, t) {
  BALL.m.position.copy(pos); BALL.glow.position.copy(pos);
  for (let i = 0; i < BALL.trail.length; i++) {
    const q = t - (i + 1) * 0.006, tr = BALL.trail[i];
    tr.visible = !!path && q > path.t0 && t < path.t0 + path.dur + 0.02;
    if (tr.visible) tr.position.copy(pathAt(path, q));
  }
}

// ------------------------------------------------------------------ everyone else, and the ball, at play time t
// ball: "throw" (caught at first) | "away" (gets past the first baseman)
const FAC = (from, to) => Math.atan2(to.x - from.x, to.z - from.z);
const FIELD = V(PLAY.field), SS0 = V(PLAY.ss0), REL = V(PLAY.release), GLOVE = V(PLAY.glove);
const B1_SPOT = BAG.clone().add(v3(-1.15, 0, -1.05));       // first baseman's spot: right foot on the infield side of the bag
function setField(t, o) {
  // shortstop: drifts into the hole, backhands it, plants, throws
  const toField = smooth((t - (PLAY.contact_t + 0.25)) / (T_FIELD - PLAY.contact_t - 0.25));
  ss.root.position.copy(SS0).lerp(FIELD, toField).add(v3(0, 0, 0));
  if (t > T_FIELD) ss.root.position.addScaledVector(v3(GLOVE.x - FIELD.x, 0, GLOVE.z - FIELD.z).normalize(), 2.5 * smooth((t - T_FIELD) / (T_REL - T_FIELD)));
  const faceHome = FAC(ss.root.position, v3(0, 0, 0)), faceFirst = FAC(ss.root.position, GLOVE);
  ss.root.rotation.y = t < T_FIELD ? faceHome : lerp(faceHome, faceFirst, smooth((t - T_FIELD) / 0.35));
  const runPh = ((t + 2) * 2.4) % 1;
  let sq;
  if (t < PLAY.contact_t + 0.25) sq = SS_READY;
  else if (t < T_FIELD - 0.35) sq = mixPose(runPose(runPh, 0.55), SS_READY, 0.25);
  else sq = keyed([[T_FIELD - 0.35, runPose(runPh, 0.5)], [T_FIELD, SS_FIELD], [T_FIELD + 0.12, SS_FIELD], [T_REL - 0.22, SS_PLANT], [T_REL, SS_RELEASE], [T_REL + 0.35, SS_FOLLOW], [T_REL + 1.2, { ...SS_FOLLOW, lean: 20, drop: -0.3 }]], t);
  applyPose(ss, sq);
  // first baseman: at the bag, stretches toward the throw
  firstB.root.position.copy(B1_SPOT); firstB.root.rotation.y = FAC(B1_SPOT, REL);
  let bq = keyed([[T_REL - 0.2, B_READY], [T_ARR - 0.12, o.ball === "away" ? B_REACH_OUT : B_STRETCH], [T_ARR + 0.5, o.ball === "away" ? B_REACH_OUT : B_STRETCH], [T_ARR + 1.1, B_READY]], t);
  if (o.ball === "away" && t > T_ARR + 0.15) { firstB.root.rotation.y = lerp(FAC(B1_SPOT, REL), FAC(B1_SPOT, v3(110, 0, -10)), smooth((t - T_ARR - 0.15) / 0.5)); bq = mixPose(bq, runPose(((t - T_ARR) * 2.2) % 1, 0.5), smooth((t - T_ARR - 0.4) / 0.4)); firstB.root.position.addScaledVector(v3(1, 0, 0.55).normalize(), 7 * smooth((t - T_ARR - 0.4) / 1.6) * (t - T_ARR - 0.4 > 0 ? 1 : 0)); }
  applyPose(firstB, bq);
  // the ball
  const G = PLAY.path.grounder, TH = PLAY.path.throw, AW = PLAY.path.away;
  let bp, path = null;
  if (t < PLAY.contact_t) bp = v3(0.4, 2.6, -1.6);
  else if (t < T_FIELD) { bp = pathAt(G, t); path = G; }
  else if (t < T_REL - 0.25) bp = handPos(ss.handL);
  else if (t < T_REL) bp = handPos(ss.handR);
  else if (t < T_ARR) { bp = pathAt(TH, t); path = TH; if (t > T_REL && t < T_REL + 0.05) bp = handPos(ss.handR).lerp(bp, (t - T_REL) / 0.05); }
  else if (o.ball === "away") { bp = pathAt(AW, t); path = AW; }
  else bp = handPos(firstB.handL);
  placeBall(bp, path, t);
  // umpire at first: foul ground behind the bag; the safe sign when asked
  const uAt = BAG.clone().addScaledVector(FOUL, 12).addScaledVector(DIR, 15);
  ump1.root.position.copy(uAt); ump1.root.rotation.y = FAC(uAt, BAG);
  applyPose(ump1, o.call && t > T_RUN + 0.25 ? mixPose(U1_SET, U1_SAFE, smooth((t - T_RUN - 0.25) / 0.2)) : U1_SET);
  // the rest
  pitcher.root.position.set(0.5, MOUND_H * 0.7, -56); pitcher.root.rotation.y = FAC(pitcher.root.position, FIELD); applyPose(pitcher, READY);
  secondB.root.position.set(28, 0, -132); secondB.root.rotation.y = FAC(secondB.root.position, FIELD); applyPose(secondB, STAND);
  thirdB.root.position.set(-58, 0, -78); thirdB.root.rotation.y = FAC(thirdB.root.position, FIELD); applyPose(thirdB, STAND);
  const cAt = v3(0.3, 0, 3.4).lerp(v3(12, 0, -9), smooth((t - 0.2) / 2.5));      // catcher trails the runner to back up first
  catcher.root.position.copy(cAt); catcher.root.rotation.y = FAC(cAt, BAG); applyPose(catcher, t < 0.2 ? CROUCH : mixPose(runPose((t * 2.2) % 1, 0.45), STAND, smooth((t - 2.6) / 0.6)));
  umpH.root.position.set(0.5, 0, 6); umpH.root.rotation.y = Math.PI; applyPose(umpH, STAND);
  const coachAt = BAG.clone().addScaledVector(FOUL, 30).addScaledVector(DIR, -26);
  coach.root.position.copy(coachAt); coach.root.rotation.y = FAC(coachAt, BAG); applyPose(coach, t > 1.5 && t < T_RUN + 0.3 ? { ...STAND, shR: [150 + 20 * Math.sin(t * 12), 30, 0], elR: 20 } : STAND);
}

// ------------------------------------------------------------------ cameras
const cam = new THREE.PerspectiveCamera(40, W / H, 0.12, 2500);
function frame(c, pos, look, fov, aspect) { c.position.copy(pos); c.fov = fov; c.aspect = aspect; c.updateProjectionMatrix(); c.lookAt(look); }
const mixV = (a, b, u) => a.clone().lerp(b, u);
const pw = (v, vs, ts) => {
  if (v <= vs[0]) return ts[0];
  for (let i = 1; i < vs.length; i++) if (v <= vs[i]) return lerp(ts[i - 1], ts[i], (v - vs[i - 1]) / (vs[i] - vs[i - 1]));
  return ts.at(-1);
};
const onPath = (s, lat = 0, y = 0) => START.clone().addScaledVector(DIR, s).addScaledVector(FOUL, lat).add(v3(0, y, 0));
const SB = PLAY.s_bag;
const CAMS = {
  ss: (u) => [mixV(v3(-62, 16, -150), v3(-58, 14, -146), u), v3(-30, 2, -118), 34],                // behind the shortstop
  hook: (u) => [mixV(onPath(124, 9, 13), onPath(118, 8, 12), easeIO(u)), onPath(77, -7, 1.6), 42],                // beyond first, foul side: runner, bag and throw
  half: (u) => [onPath(112, 1.5, 14), onPath(62, 0, -2.5), 46],                                    // the split-screen view: high on the line beyond first, looking back at home
  side: (u, t, s) => { const k = s.who === "run" ? "run" : "dive", st = Math.min(series(PLAY[k].s, Math.max(t, 0)), SB + 3);   // square to the line, foul side, tracking him to the bag
    return [onPath(st - 4, 21, 4.4), onPath(st + 1.5, 0, 3.4), 40]; },
  low: (u) => [mixV(onPath(SB + 5, 5.5, 1.3), onPath(SB + 4.2, 4.6, 1.2), u), onPath(SB - 2, 0.2, 0.9), 50],  // low, right at the bag
  wide1: (u) => [mixV(onPath(SB - 10, 34, 12), onPath(SB + 4, 32, 11), u), onPath(SB + 8, 3, 1.5), 46],      // foul ground: the bag and the space past it
  take: (u, t) => { const tt = Math.max(t, 0), st = Math.min(series(PLAY.run.s, tt), SB + 34), la = series(PLAY.run.lat, tt);
    return [onPath(st - 4, 22 + la, 4.6), onPath(st + 1.5, la, 1.0), 40]; },   // the side view, framed higher for the rule card
  end: (u, t) => { const st = clamp(series(PLAY.run.s, t), SB, SB + 30); return [mixV(onPath(SB - 4, 34, 11), onPath(SB + 6, 33, 10), easeIO(u)), onPath(st + 4, 5, 1.8), 46]; },   // he eases up past the bag
};
function shotAt(v) {
  const L = CC.shots.list;
  const s = L.find((x) => v < x.b) || L.at(-1);
  const r = s.cu || [s.a, s.b];
  return { s, t: pw(v, s.vs, s.ts), u: clamp((v - r[0]) / (r[1] - r[0]), 0, 1) };
}

// ------------------------------------------------------------------ DOM overlays fed from the same clock
const $ = (id) => document.getElementById(id);
const SPEEDS = { rt: "Real time", slow2: "Slow motion · ½ speed", slow3: "Slow motion · ⅓ speed", slow4: "Slow motion · ¼ speed", slow6: "Slow motion · ⅙ speed", replay: "Slow-motion replay", freeze: "Freeze" };
const tenths = (x) => Math.max(0, x).toFixed(1);
function overlays(s, t) {
  if ($("spd")) { $("spd").textContent = SPEEDS[s.speed] || ""; $("spd").className = "spd " + (s.speed === "rt" ? "rt" : "sl"); }
  if ($("tmL")) $("tmL").textContent = tenths(Math.min(t, T_DIVE)) + " s";
  if ($("tmR")) $("tmR").textContent = tenths(Math.min(t, T_RUN)) + " s";
  for (const [id, kind, T] of [["hdL", "dive", T_DIVE], ["hdR", "run", T_RUN]]) if ($(id)) $(id).classList.toggle("hit", t >= T);
  for (const [id, kind] of [["mvD", "dive"], ["mvR", "run"]]) if ($(id)) {
    const v = series(PLAY[kind].v, Math.max(t, 0));
    $(id).querySelector("b").textContent = v.toFixed(0);
    $(id).querySelector("i").style.width = (v / A.vmax * 100).toFixed(1) + "%";
  }
}

function renderAt(v) {
  const { s, t, u } = shotAt(v);
  setField(t, { ball: s.ball || "throw", call: !!s.call });
  const c = CAMS[s.cam](u, t, s);
  renderer.setScissorTest(s.mode === "split");
  if (s.mode === "split") {                         // two identical plays side by side: dive on the left, run through on the right
    for (const [x, kind] of [[0, "dive"], [W / 2, "run"]]) {
      const P = kind === "dive" ? diver : runner;
      diver.root.visible = kind === "dive"; runner.root.visible = kind === "run"; ghost(false);
      const th = s.hold ? Math.min(t, kind === "dive" ? T_DIVE : T_RUN) : t;    // each side freezes on its own touch
      setRunner(P, kind, th);
      setField(th, { ball: s.ball || "throw" });
      frame(cam, c[0], c[1], c[2], (W / 2) / H);
      renderer.setViewport(x, 0, W / 2, H); renderer.setScissor(x, 0, W / 2, H);
      renderer.render(scene, cam);
    }
  } else {
    const who = s.who || "run";
    diver.root.visible = who === "dive" || who === "both"; runner.root.visible = who === "run" || who === "both";
    ghost(who === "both");
    if (diver.root.visible) setRunner(diver, "dive", t);
    if (runner.root.visible) setRunner(runner, "run", t);
    renderer.setViewport(0, 0, W, H);
    frame(cam, c[0], c[1], c[2], W / H);
    renderer.render(scene, cam);
  }
  overlays(s, t);
}

let last = -1;
function seek(time) { if (time === last) return; last = time; renderAt(time); }
window.addEventListener("hf-seek", (e) => seek(e.detail.time));
window.__fieldRender = renderAt;
window.__measure = () => {   // the 3D figure's reach, to keep tools/physics.py honest
  diver.root.visible = true; diver.root.position.set(0, 0, 0); diver.root.rotation.y = 0;
  applyPose(diver, { ...DIVE_FLAT, drop: PLAY.assume.hip_flat - 3.1 });
  const hand = handPos(diver.handR), pel = diver.pelvis.getWorldPosition(new THREE.Vector3());
  runner.root.position.set(0, 0, 0); runner.root.rotation.y = 0;
  const feet = [];
  for (const ph of [0.27, 0.77]) { applyPose(runner, runPose(ph, 1)); const f = [runner.ftL, runner.ftR].map((x) => handPos(x)); const p = runner.pelvis.getWorldPosition(new THREE.Vector3()); feet.push(Math.max(f[0].z, f[1].z) - p.z); }
  return { reach: hand.z - pel.z, handY: hand.y, pelvisY: pel.y, foot: feet };
};
document.fonts.ready.then(() => seek(window.__hfThreeTime || 0));
seek(window.__hfThreeTime || 0);
