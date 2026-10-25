// "Pitch sequencing": the field, the players and three pitches (high fastball, curveball, fastball), in three.js.
// Everything is a pure function of HyperFrames time (hf-seek), so each frame is exact and repeatable.
// Units are feet. Home plate's back point is the origin, +x points toward first base's side, -z toward center field.
// The pitches and the swing timing come from tools/physics.py via window.__PLAY.
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
const pitcher = makePlayer(KIT.home, { glove: true });
const batter = makePlayer(KIT.away, { helmet: true });
const catcher = makePlayer(KIT.home, { glove: true, catcher: true });
const ump = makePlayer(KIT.ump, { catcher: true });
const fielders = [[-30, -112], [32, -118], [-60, -88], [62, -84], [-118, -250], [0, -300], [118, -250]].map(([x, z]) => {
  const p = makePlayer(KIT.home, { glove: true }); p.root.position.set(x, 0, z); p.root.rotation.y = Math.atan2(-x, -z); applyPose(p, READY); scene.add(p.root); return p;
});
for (const p of [pitcher, batter, catcher, ump]) scene.add(p.root);

// the bat: its own object, knob in the batter's hands, aimed by the swing keys
const BAT_LEN = 2.83, SWEET = 2.3;                          // a 34 in bat; the sweet spot about 6 in from the end
const bat = new THREE.Group();
{
  const M = new THREE.MeshStandardMaterial({ color: 0xc89058, roughness: 0.45 });
  const prof = [[0, 0.07], [0.08, 0.06], [0.1, 0.045], [1.2, 0.05], [1.9, 0.09], [2.45, 0.108], [2.78, 0.105], [2.83, 0.0]];
  const geo = new THREE.LatheGeometry(prof.map(([y, r]) => new THREE.Vector2(r, y)), 18);
  const m = new THREE.Mesh(geo, M); m.castShadow = true; bat.add(m);
  const knob = new THREE.Mesh(new THREE.CylinderGeometry(0.085, 0.085, 0.05, 14), new THREE.MeshStandardMaterial({ color: 0x2a2018, roughness: 0.6 })); bat.add(knob);
}
scene.add(bat);

// ------------------------------------------------------------------ the pitches (tools/physics.py)
const V = (a) => v3(a[0], a[1], a[2]);
const RELEASE = V(PLAY.release), PITCH = PLAY.pitches, SWING = PLAY.swing;
const COLORS = { fb1: 0xffd84d, cb: 0x56d1ff, fb2: 0xff6a3d };
function pathAt(path, t) {
  const u = t * path.hz, n = path.p.length - 1;
  if (u <= 0) return V(path.p[0]);
  if (u >= n) return V(path.p[n]);
  const i = Math.floor(u), f = u - i, a = path.p[i], b = path.p[i + 1];
  return v3(lerp(a[0], b[0], f), lerp(a[1], b[1], f), lerp(a[2], b[2], f));
}
const handPos = (h) => { h.updateWorldMatrix(true, false); return h.getWorldPosition(new THREE.Vector3()); };
const inFingers = (h) => { h.updateWorldMatrix(true, false); return h.localToWorld(v3(0, -0.19, 0.1)); };   // the ball sits in the fingers, not inside the hand

// balls: the pitch itself, and a ghost for comparing two pitches on the same clock
const glowTex = canvasTex(64, 64, (g, w) => { const gr = g.createRadialGradient(w / 2, w / 2, 0, w / 2, w / 2, w / 2); gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(0.3, "rgba(255,255,255,.5)"); gr.addColorStop(1, "rgba(255,255,255,0)"); g.fillStyle = gr; g.fillRect(0, 0, w, w); });
function makeBall(opacity) {
  const m = new THREE.Mesh(new THREE.SphereGeometry(0.121, 18, 14), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xfff4d6, emissiveIntensity: 0.55, roughness: 0.45, transparent: opacity < 1, opacity }));
  m.castShadow = opacity === 1; scene.add(m);
  const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: 0xffe7a8, transparent: true, opacity, depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: false }));
  glow.scale.set(0.014, 0.014, 1); scene.add(glow);
  const trail = [];
  for (let i = 0; i < 40; i++) { const t = new THREE.Mesh(new THREE.SphereGeometry(0.1 * (1 - i / 40) + 0.02, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffd84d, transparent: true, opacity: 0.45 * opacity * (1 - i / 40), depthWrite: false })); scene.add(t); trail.push(t); }
  return { m, glow, trail };
}
const BALL = makeBall(1), GHOST = makeBall(0.55);
function place(B, pos, path, tp, color, show = true) {
  B.m.visible = B.glow.visible = show; B.m.position.copy(pos); B.glow.position.copy(pos); B.glow.material.color.setHex(color);
  for (let i = 0; i < B.trail.length; i++) {
    const q = tp - (i + 1) * 0.0024, m = B.trail[i];
    m.visible = show && !!path && q > 0 && tp < path.dur + 0.01;
    if (m.visible) { m.position.copy(pathAt(path, q)); m.material.color.setHex(color); }
  }
}

// trajectory overlays: the path each pitch takes (drawn as it flies), and a dashed "expected" path
function lineMesh(points, color, width, opacity = 0.9, dashed = false) {
  const g = new THREE.Group();
  for (let i = 0; i < points.length - 1; i++) {
    if (dashed && i % 2) continue;
    const a = points[i], b = points[i + 1], len = a.distanceTo(b);
    const m = new THREE.Mesh(new THREE.BoxGeometry(width, width, len), new THREE.MeshBasicMaterial({ color, transparent: true, opacity, depthWrite: false }));
    m.position.set((a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2); m.lookAt(b.x, b.y, b.z); m.userData.u = (i + 1) / (points.length - 1); g.add(m);
  }
  g.visible = false; scene.add(g); return g;
}
function reveal(g, u) { g.visible = u > 0; for (const m of g.children) m.visible = m.userData.u <= u + 1e-6; }
const pts = (name, n = 90) => { const P = PITCH[name].path; return Array.from({ length: n + 1 }, (_, i) => pathAt(P, P.dur * i / n)); };
const LINES = { fb1: lineMesh(pts("fb1"), COLORS.fb1, 0.07, 0.85), cb: lineMesh(pts("cb"), COLORS.cb, 0.07, 0.85), fb2: lineMesh(pts("fb2"), COLORS.fb2, 0.07, 0.9) };
const EXPECT = lineMesh(pts("cb", 60), COLORS.cb, 0.085, 0.55, true);   // the breaking ball the hitter is expecting

// ------------------------------------------------------------------ poses
const moundY = (z) => { const d = Math.abs(z - MOUND.z); return d < 2.5 ? MOUND_H : d < 9 ? MOUND_H * (1 - (d - 2.5) / 6.5) : 0; };
// right-handed pitcher, from the stretch (t relative to release)
const P_SET = { lean: 4, look: 80, shL: [42, 8, 0], elL: 105, shR: [38, -4, 0], elR: 112, hipL: [4, 6], hipR: [4, 6], knL: 8, knR: 8 };
const P_GRIP = { lean: 6, look: 80, nod: 4, shL: [44, 10, 0], elL: 104, shR: [14, 14, 0], elR: 48, hipL: [4, 6], hipR: [4, 6], knL: 8, knR: 8 };
const P_LIFT = { lean: -4, look: 80, shL: [48, 8, 0], elL: 100, shR: [44, -4, 0], elR: 108, hipL: [100, 4], knL: 105, hipR: [6, 6], knR: 14, drop: -0.15 };
const P_STRIDE = { lean: 6, look: 40, drop: -0.6, twist: -50, shL: [80, 35, 0], elL: 25, shR: [-55, 80, 0], elR: 85, hipL: [52, 4], knL: 28, hipR: [-28, 6], knR: 38 };
const P_PLANT = { lean: 18, look: 10, drop: -0.85, twist: -35, shL: [62, 40, 0], elL: 60, shR: [-15, 98, 0], elR: 100, hipL: [58, 4], knL: 24, hipR: [-34, 6], knR: 62 };
const P_REL = { lean: 42, nod: 8, drop: -1.0, twist: 28, shL: [12, 32, 0], elL: 85, shR: [168, 22, 0], elR: 8, hipL: [72, 4], knL: 22, hipR: [-18, 6], knR: 92 };
const P_FOLLOW = { lean: 62, nod: 18, drop: -1.25, twist: 48, shL: [8, 38, 0], elL: 95, shR: [58, -24, 0], elR: 22, hipL: [82, 4], knL: 38, hipR: [34, 6], knR: 84 };
const P_RECOVER = { ...READY, look: 0 };
function setPitcher(t) {
  const q = keyed([[-1.75, P_GRIP], [-1.4, P_SET], [-1.15, P_SET], [-0.82, P_LIFT], [-0.4, P_STRIDE], [-0.12, P_PLANT], [0, P_REL], [0.32, P_FOLLOW], [0.95, P_RECOVER]], t);
  const z = lerp(-60.6, -56.6, smooth((t + 0.55) / 0.6)) + 0.7 * smooth((t - 0.05) / 0.4);
  pitcher.root.position.set(0, moundY(z), z);
  pitcher.root.rotation.y = lerp(-Math.PI / 2, 0, smooth((t + 0.62) / 0.6));
  applyPose(pitcher, q);
}
// the pitcher's hand at release, measured once, so the ball leaves his hand at the simulated release point
setPitcher(0); const P_FIX = RELEASE.clone().sub(inFingers(pitcher.handR)); P_FIX.y = 0;

// right-handed batter in the left-side box (facing +x), stride with the front (left) foot
const B_STANCE = { drop: -0.35, lean: 18, look: 80, nod: -4, hipL: [20, 16], hipR: [22, 14], knL: 26, knR: 26, shL: [52, 8, 0], shR: [62, 36, 0], elL: 98, elR: 112, twist: 18 };
const B_LOAD = { ...B_STANCE, twist: 30, pelvisTwist: -8, hipL: [34, 22], knL: 40, shR: [70, 42, 0] };
const B_LAUNCH = { ...B_STANCE, twist: 28, pelvisTwist: 2, hipL: [28, 28], knL: 18, hipR: [26, 10], knR: 34 };
const B_MID = { drop: -0.45, lean: 22, look: 70, nod: -6, twist: 8, pelvisTwist: 42, hipL: [26, 28], knL: 14, hipR: [22, 10], knR: 40, shL: [82, -8, 0], elL: 38, shR: [58, 22, 0], elR: 78 };
const B_CONTACT = { drop: -0.5, lean: 24, look: 45, nod: -10, twist: -6, pelvisTwist: 72, hipL: [24, 28], knL: 10, hipR: [18, 12], knR: 46, shL: [86, -22, 0], elL: 8, shR: [80, 6, 0], elR: 26 };
const B_FOLLOW = { drop: -0.4, lean: 18, look: 20, twist: -30, pelvisTwist: 86, hipL: [20, 28], knL: 8, hipR: [10, 12], knR: 52, shL: [112, -8, 0], elL: 40, shR: [118, -28, 0], elR: 62 };
const B_FINISH = { drop: -0.3, lean: 10, look: 10, twist: -40, pelvisTwist: 92, hipL: [16, 26], knL: 8, hipR: [6, 12], knR: 56, shL: [142, 12, 0], elL: 104, shR: [150, -40, 0], elR: 112 };
const BAT_KEYS = (tc, ts) => [   // [time, bat direction (knob -> end)]
  [ts - 0.3, v3(0.25, 0.85, 0.45)], [ts, v3(0.12, 0.92, 0.38)], [ts + 0.08, v3(-0.2, 0.35, 0.92)], [tc, v3(1, -0.08, -0.12)],
  [tc + 0.08, v3(0.25, 0.12, -1)], [tc + 0.3, v3(-0.7, 0.5, -0.2)], [tc + 0.7, v3(-0.35, -0.5, 0.8)]];
const B_ROOT = v3(-3.15, 0, 0.15);
// ts: when the swing starts (s after release), or null for a take. The bat reaches the zone SWING seconds later.
function batterPose(t, ts) {
  if (ts == null) return keyed([[-0.5, B_STANCE], [-0.15, B_LOAD], [0.12, B_LAUNCH], [0.7, B_STANCE]], t);
  const tc = ts + SWING;
  return keyed([[-0.5, B_STANCE], [-0.15, B_LOAD], [ts, B_LAUNCH], [ts + 0.08, B_MID], [tc, B_CONTACT], [tc + 0.12, B_FOLLOW], [tc + 0.6, B_FINISH]], t);
}
function batDir(t, ts) {
  const K = BAT_KEYS(ts == null ? 9 : ts + SWING, ts == null ? 9 : ts);
  if (ts == null || t <= K[0][0]) return K[0][1].clone().normalize();
  for (let i = 1; i < K.length; i++) if (t <= K[i][0]) {
    const u = (t - K[i - 1][0]) / (K[i][0] - K[i - 1][0]);
    const a = K[i - 1][1].clone().normalize(), b = K[i][1].clone().normalize();
    const qa = new THREE.Quaternion(), qb = new THREE.Quaternion().setFromUnitVectors(a, b);
    return a.applyQuaternion(qa.slerp(qb, i <= 4 ? u : smooth(u)));
  }
  return K.at(-1)[1].clone().normalize();
}
function knobAt() { const a = handPos(batter.handL), b = handPos(batter.handR); return a.lerp(b, 0.5); }
// where the batter stands: placed so an on-time swing at the final fastball would meet it on the sweet spot
const CAL = PITCH.fb2;
batter.root.position.copy(B_ROOT); batter.root.rotation.y = Math.PI / 2; applyPose(batter, batterPose(CAL.t_contact, CAL.t_commit));
const B_FIX = V(CAL.contact).sub(knobAt().addScaledVector(batDir(CAL.t_contact, CAL.t_commit), SWEET)); B_FIX.y = 0;

// ------------------------------------------------------------------ set the whole play to time t (s from release)
// o = { pitch, swing (start time or null), ghost (pitch name or null), ghostT, lines: {name: drawn-to time}, expect: drawn fraction }
function setPlay(t, o) {
  const pc = PITCH[o.pitch];
  setPitcher(t);
  pitcher.root.position.addScaledVector(P_FIX, smooth((t + 0.6) / 0.6));
  batter.root.position.copy(B_ROOT).add(B_FIX); batter.root.rotation.y = Math.PI / 2;
  applyPose(batter, batterPose(t, o.swing ?? null));
  bat.position.copy(knobAt()); bat.quaternion.setFromUnitVectors(v3(0, 1, 0), batDir(t, o.swing ?? null));
  catcher.root.position.set(0.15, 0, 3.6); catcher.root.rotation.y = Math.PI;
  applyPose(catcher, { ...CROUCH, shL: [70, 14, 0], elL: 25 });
  ump.root.position.set(0.5, 0, 6.0); ump.root.rotation.y = Math.PI;
  applyPose(ump, { drop: -1.0, lean: 30, nod: -6, hipL: [52, 28], hipR: [52, 28], knL: 68, knR: 68, shL: [30, 20, 0], elL: 60, shR: [30, 20, 0], elR: 60 });
  const glovePt = (p) => V(p.path.p[p.path.p.length - 1]);
  const ballAt = (p, tt) => tt < -0.07 ? inFingers(pitcher.handR) : tt < 0 ? inFingers(pitcher.handR).lerp(RELEASE, smooth((tt + 0.07) / 0.07))
    : tt < p.t_glove ? pathAt(p.path, tt) : glovePt(p).lerp(handPos(catcher.handL), smooth((tt - p.t_glove) / 0.05));
  place(BALL, ballAt(pc, t), pc.path, t, COLORS[o.pitch]);
  if (o.ghost) { const g = PITCH[o.ghost], tg = o.ghostT ?? t; place(GHOST, ballAt(g, Math.max(tg, 0)), g.path, tg, COLORS[o.ghost], tg > 0.01 && tg < g.t_glove + 0.25); }
  else place(GHOST, v3(0, -50, 0), null, 0, 0xffffff, false);
  for (const k of Object.keys(LINES)) reveal(LINES[k], o.lines?.[k] != null ? clamp(o.lines[k] / PITCH[k].path.dur, 0, 1) : 0);
  reveal(EXPECT, o.expect ?? 0);
}

// ------------------------------------------------------------------ cameras
const cam = new THREE.PerspectiveCamera(40, W / H, 0.12, 2500);
function frame(c, pos, look, fov) { c.position.copy(pos); c.fov = fov; c.aspect = W / H; c.updateProjectionMatrix(); c.lookAt(look); }
const mixV = (a, b, u) => a.clone().lerp(b, u);
const pw = (v, vs, ts) => {
  if (v <= vs[0]) return ts[0];
  for (let i = 1; i < vs.length; i++) if (v <= vs[i]) return lerp(ts[i - 1], ts[i], (v - vs[i - 1]) / (vs[i] - vs[i - 1]));
  return ts.at(-1);
};
const headPos = () => { batter.neck.updateWorldMatrix(true, false); return batter.neck.getWorldPosition(new THREE.Vector3()).add(v3(0, 0.3, 0)); };
const eyes = () => headPos().add(v3(0.25, 0.05, -0.45));
const CAMS = {
  behind: (u, t, s) => {                            // over the pitcher's shoulder, then chase the pitch in
    let pos = mixV(v3(-3.2, 7.6, -73), v3(-2.8, 7.2, -70.5), u), look = v3(0, 4.4, -40);
    if (t > 0) {
      const b = pathAt(PITCH[s.pitch].path, Math.min(t, PITCH[s.pitch].t_glove));
      const chase = b.clone().add(v3(-2.4, 1.1, -8.5)); chase.z = Math.min(chase.z, -9);
      pos = pos.clone().lerp(chase, smooth(t / 0.12)); look = b.clone().add(v3(0, -0.2, 0)).lerp(v3(0, 2.6, 1), smooth((t - 0.3) / 0.15));
    }
    return [pos, look, 40];
  },
  cf: () => [v3(-3.5, 17, -205), v3(0, 3.2, -18), 6.8],                       // the center-field broadcast camera
  pov: () => [eyes(), v3(-0.6, 4.6, -52), 38],                                  // the batter's eyes
  povw: () => [eyes(), v3(4.5, 3.3, -40), 54],                                  // the batter's eyes, wider and turned toward the plate, where the break shows
  stare: (u) => [eyes(), v3(-0.9, 5.0, -56), lerp(36, 24, easeIO(u))],          // the batter's eyes, closing in on the pitcher
  track: (u) => [mixV(v3(-3.5, 6.5, 13), v3(-3.0, 6.0, 11.5), u), v3(0.2, 2.6, -18), 54],    // high behind the batter: his view of the paths, from outside
  swing: (u) => [mixV(v3(-3.4, 5.8, 10.5), v3(-3.0, 5.5, 9.5), u), v3(-0.6, 2.8, -12), 50],   // the same side, closer, for the swing
  freeze: (u) => { const e = easeIO(u); return [mixV(v3(-3.0, 6.0, 11.5), v3(-2.7, 5.1, 7.6), e), mixV(v3(0.2, 2.6, -18), v3(-1.2, 3.0, -7), e), lerp(54, 50, e)]; },
};
// the fastball at the same distance from the plate as the pitch in flight (for comparing paths, not arrival times)
function timeAtZ(path, z) {
  const p = path.p; let lo = 0, hi = p.length - 1;
  if (z <= p[0][2]) return 0;
  if (z >= p[hi][2]) return path.dur;
  while (hi - lo > 1) { const m = (lo + hi) >> 1; if (p[m][2] < z) lo = m; else hi = m; }
  return (lo + (z - p[lo][2]) / (p[hi][2] - p[lo][2])) / path.hz;
}
function shotAt(v) {
  const L = CC.shots.list;
  const s = L.find((x) => v < x.b) || L.at(-1);
  const t = pw(v, s.vs, s.ts);
  const r = s.cu || [s.a, s.b];
  return { s, t, u: clamp((v - r[0]) / (r[1] - r[0]), 0, 1) };
}

// ------------------------------------------------------------------ DOM overlays fed from the same clock
const $ = (id) => document.getElementById(id);
const SPEEDS = { rt: "Real time", slow4: "Slow motion · ¼ speed", slow6: "Slow motion · ⅙ speed", slow8: "Slow motion · ⅛ speed", slowv: "Slow motion",
  replay: "Slow-motion replay", freeze: "Freeze" };
function overlays(sp) {
  if ($("spd")) { $("spd").textContent = SPEEDS[sp] || ""; $("spd").className = "spd " + (sp === "rt" ? "rt" : "sl"); }
}

function renderAt(v) {
  const { s, t, u } = shotAt(v);
  const main = PITCH[s.pitch].path;
  let tg = null;
  if (s.ghost) tg = s.gmode === "z" ? (t <= 0 ? t : timeAtZ(PITCH[s.ghost].path, pathAt(main, t).z)) : t;
  const lines = {};
  for (const [k, m] of Object.entries(s.lines || {})) lines[k] = m === "all" ? 9 : m === "g" ? tg : typeof m === "number" ? m : t;
  setPlay(t, { pitch: s.pitch, swing: s.swing, ghost: s.ghost, ghostT: tg, lines, expect: Array.isArray(s.expect) ? clamp((v - s.expect[0]) / (s.expect[1] - s.expect[0]), 0, 1) : s.expect });
  batter.root.visible = bat.visible = !(s.cam.startsWith("pov") || s.cam === "stare");     // the camera is his eyes
  const c = CAMS[s.cam](u, t, s);
  frame(cam, c[0], c[1], c[2]);
  renderer.render(scene, cam);
  overlays(s.speed);
}

let last = -1;
function seek(time) { if (time === last) return; last = time; renderAt(time); }
window.addEventListener("hf-seek", (e) => seek(e.detail.time));
window.__fieldRender = renderAt;
document.fonts.ready.then(() => seek(window.__hfThreeTime || 0));
seek(window.__hfThreeTime || 0);
