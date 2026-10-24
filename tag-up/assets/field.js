// "Tagging up": a regulation field, the players and a sacrifice-fly play at the plate, in three.js.
// Everything is a pure function of HyperFrames time (hf-seek), so each frame is exact and repeatable.
// Units are feet. Home plate is the origin, +x points toward first base's side, -z toward center field.
// The play itself (ball flights, the runner, every time) comes from tools/physics.py via window.__PLAY.
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
const rf = makePlayer(KIT.home, { glove: true });            // right fielder: catches and throws
const runner = makePlayer(KIT.away, { helmet: true });       // runner tagging at third
const catcher = makePlayer(KIT.home, { glove: true, catcher: true });
const ump = makePlayer(KIT.ump, { catcher: true });          // plate umpire (mask, chest protector)
const pitcher = makePlayer(KIT.home, { glove: true });       // backing up home
const firstB = makePlayer(KIT.home, { glove: true });        // cutoff man, lets it go through
const thirdB = makePlayer(KIT.home, { glove: true });
const ss = makePlayer(KIT.home, { glove: true });
const secondB = makePlayer(KIT.home, { glove: true });
const cf = makePlayer(KIT.home, { glove: true });            // backing up the catch
const lf = makePlayer(KIT.home, { glove: true });
const coach = makePlayer(KIT.away);                          // third-base coach
const CAST = [rf, runner, catcher, ump, pitcher, firstB, thirdB, ss, secondB, cf, lf, coach];
for (const p of CAST) scene.add(p.root);

// ------------------------------------------------------------------ the simulated play (tools/physics.py)
const A = PLAY.assume;
const V = (a) => v3(a[0], a[1], a[2]);
const CATCH = V(PLAY.catch), REL = V(PLAY.release), GLOVE = V(PLAY.glove);
const U = v3(CATCH.x, 0, CATCH.z).normalize();               // home -> catch, on the ground
const TOHOME = U.clone().negate();
const SIDE = v3(-U.z, 0, U.x);                               // perpendicular to the throw line
const EXCH = A.exchange, TAGT = A.tag;
const SC = { direct: PLAY.direct, loop: PLAY.loop };
function pathAt(path, t) {                                    // position on a sampled flight at play time t
  const u = (t - path.t0) * path.hz, n = path.p.length - 1;
  if (u <= 0) return V(path.p[0]);
  if (u >= n) return V(path.p[n]);
  const i = Math.floor(u), f = u - i, a = path.p[i], b = path.p[i + 1];
  return v3(lerp(a[0], b[0], f), lerp(a[1], b[1], f), lerp(a[2], b[2], f));
}
const flightEnd = (path) => path.t0 + path.dur;
function runS(t) {                                            // runner's distance from third base (ft)
  if (t <= 0) return 0;
  const r = PLAY.runner, u = t * r.hz, n = r.s.length - 1;
  if (u >= n) return r.s[n];
  const i = Math.floor(u); return lerp(r.s[i], r.s[i + 1], u - i);
}
const PLATE_C = v3(-0.708, 0, -0.708);                        // the plate's third-base corner: 89 ft from the bag
const D3H = PLATE_C.clone().sub(B3).normalize();
const FOUL3 = v3(-Math.SQRT1_2, 0, Math.SQRT1_2);              // off the third-base line, toward foul ground
const onLine3 = (s, off = 0) => B3.clone().addScaledVector(D3H, s).addScaledVector(FOUL3, off);

// ball(s), glow and trail
function makeBall(color, glowColor) {
  const m = new THREE.Mesh(new THREE.SphereGeometry(0.17, 16, 12), new THREE.MeshStandardMaterial({ color, emissive: glowColor, emissiveIntensity: 0.6, roughness: 0.4 }));
  m.castShadow = true; scene.add(m);
  const gt = canvasTex(64, 64, (g, w) => { const gr = g.createRadialGradient(w / 2, w / 2, 0, w / 2, w / 2, w / 2); gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(0.35, "rgba(255,255,255,.55)"); gr.addColorStop(1, "rgba(255,255,255,0)"); g.fillStyle = gr; g.fillRect(0, 0, w, w); });
  const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: gt, color: glowColor, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: false }));
  glow.scale.set(0.02, 0.02, 1); scene.add(glow);
  const trail = [];
  for (let i = 0; i < 70; i++) {
    const t = new THREE.Mesh(new THREE.SphereGeometry(0.13 * (1 - i / 70) + 0.04, 8, 6), new THREE.MeshBasicMaterial({ color: glowColor, transparent: true, opacity: 0.5 * (1 - i / 70), depthWrite: false }));
    scene.add(t); trail.push(t);
  }
  return { m, glow, trail };
}
const BALL = makeBall(0xffffff, 0xffd84d), GHOST = makeBall(0xffd2b0, 0xff8a3d);
function placeBall(B, pos, path, t, show = true, trailOn = true) {
  B.m.visible = B.glow.visible = show; B.m.position.copy(pos); B.glow.position.copy(pos);
  for (let i = 0; i < B.trail.length; i++) {
    const q = t - (i + 1) * 0.006, tr = B.trail[i];
    tr.visible = show && trailOn && path && q > path.t0 && t <= flightEnd(path) + 0.02;
    if (tr.visible) tr.position.copy(pathAt(path, q));
  }
}

// analysis marks
function lineMesh(points, color, width, y = 0.08, dashed = false, opacity = 0.9, round = false) {
  const g = new THREE.Group();
  for (let i = 0; i < points.length - 1; i++) {
    if (dashed && i % 2) continue;
    const a = points[i], b = points[i + 1], len = a.distanceTo(b);
    const m = new THREE.Mesh(new THREE.BoxGeometry(width, round ? width : 0.05, len), new THREE.MeshBasicMaterial({ color, transparent: true, opacity, depthWrite: false, fog: !round }));
    m.position.set((a.x + b.x) / 2, (a.y + b.y) / 2 + y, (a.z + b.z) / 2); m.lookAt(b.x, b.y + y, b.z); m.userData.u = i / (points.length - 1); g.add(m);
  }
  scene.add(g); return g;
}
function reveal(g, u) { g.visible = u > 0; for (const m of g.children) m.visible = m.userData.u < u; }
const throwLine = lineMesh(Array.from({ length: 61 }, (_, i) => v3(lerp(REL.x, GLOVE.x, i / 60), 0, lerp(REL.z, GLOVE.z, i / 60))), 0xf4f6f8, 0.7, 0.1, true, 0.75);
const runLine = lineMesh(Array.from({ length: 31 }, (_, i) => onLine3(89 * i / 30, 0.9)), 0x56d1ff, 0.6, 0.09, true, 0.85);
const arcPts = (path, n = 80) => Array.from({ length: n + 1 }, (_, i) => pathAt(path, path.t0 + path.dur * i / n));
const directArc = lineMesh(arcPts(PLAY.path.direct), 0xffd84d, 1.6, 0, false, 0.95, true);
const loopArc = lineMesh(arcPts(PLAY.path.loop), 0xff8a3d, 1.6, 0, false, 0.95, true);
const catchRing = new THREE.Mesh(new THREE.RingGeometry(3.4, 4.3, 64), new THREE.MeshBasicMaterial({ color: 0xff6a3d, transparent: true, opacity: 0.9, depthWrite: false, side: THREE.DoubleSide }));
catchRing.rotation.x = -Math.PI / 2; catchRing.position.set(CATCH.x, 0.12, CATCH.z); scene.add(catchRing);
const gapMark = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.06, 1), new THREE.MeshBasicMaterial({ color: 0x56d1ff })); scene.add(gapMark);
function labelSprite(text, color = "#ffffff", bg = "rgba(8,12,20,0.82)") {
  const t = canvasTex(512, 160, (g, w, h) => {
    g.fillStyle = bg; g.beginPath(); g.roundRect(4, 4, w - 8, h - 8, 34); g.fill();
    g.fillStyle = color; g.font = "800 92px 'Barlow Condensed', sans-serif"; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(text, w / 2, h / 2 + 4);
  });
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, depthTest: false, transparent: true })); s.scale.set(2.3, 0.72, 1); s.renderOrder = 10; scene.add(s); return s;
}
let gapLabel = null;
document.fonts.load("800 92px 'Barlow Condensed'").then(() => { gapLabel = labelSprite(`${(A.r_dist - PLAY.direct.runner_at_tag).toFixed(1)} FT`, "#56d1ff"); gapLabel.visible = false; last = -1; seek(window.__hfThreeTime || 0); });

// ------------------------------------------------------------------ poses for this play
const LOOK_UP = { lean: -4, nod: -38, shL: [20, 12, 0], shR: [20, 12, 0], elL: 40, elR: 40, hipL: [6, 8], hipR: [6, 8], knL: 12, knR: 12 };
const CATCH_UP = { lean: 2, nod: -30, shL: [168, 12, 0], elL: 12, shR: [150, -6, 0], elR: 35, hipL: [14, 6], hipR: [-6, 6], knL: 20, knR: 10 };
const TRANSFER = { drop: -0.3, lean: 14, nod: -6, shL: [70, 10, 0], elL: 95, shR: [65, -4, 0], elR: 110, hipL: [30, 6], hipR: [-10, 6], knL: 34, knR: 18 };
const CROW = { drop: -0.45, lean: 6, twist: -55, nod: -4, look: 50, shL: [80, 20, 0], elL: 30, shR: [-35, 75, 0], elR: 95, hipL: [38, 10], hipR: [-18, 14], knL: 30, knR: 40 };
const RELEASE = { drop: -0.6, lean: 32, twist: 35, nod: 6, shL: [20, 30, 0], elL: 60, shR: [165, 20, 0], elR: 15, hipL: [48, 8], hipR: [-30, 10], knL: 40, knR: 30 };
const FOLLOW = { drop: -0.8, lean: 48, twist: 50, nod: 10, shL: [10, 30, 0], elL: 70, shR: [55, -25, 0], elR: 25, hipL: [55, 8], hipR: [10, 10], knL: 52, knR: 70 };
const ROCKER = { drop: -0.7, lean: 26, look: 75, nod: -6, hipL: [36, 14], hipR: [44, 14], knL: 46, knR: 52, shL: [20, 14, 0], shR: [30, 14, 0], elL: 35, elR: 35 };
const C_READY = { drop: -1.0, lean: 28, nod: -10, hipL: [55, 26], hipR: [55, 26], knL: 70, knR: 70, shL: [70, 20, 0], elL: 25, shR: [40, 10, 0], elR: 60 };
const C_RECEIVE = { drop: -1.1, lean: 34, nod: -6, hipL: [60, 26], hipR: [60, 26], knL: 76, knR: 76, shL: [92, 14, 0], elL: 8, shR: [60, 10, 0], elR: 70 };
const C_HIGH = { drop: -0.6, lean: 10, nod: -24, hipL: [30, 20], hipR: [30, 20], knL: 40, knR: 40, shL: [140, 14, 0], elL: 10, shR: [100, 0, 0], elR: 60 };
const C_TAG = { drop: -2.0, lean: 62, nod: 18, hipL: [96, 30], hipR: [70, 30], knL: 118, knR: 96, shL: [120, 30, 0], elL: 6, shR: [70, 10, 0], elR: 70 };
const U_SET = { drop: -1.1, lean: 30, nod: -6, hipL: [55, 28], hipR: [55, 28], knL: 72, knR: 72, shL: [30, 20, 0], elL: 60, shR: [30, 20, 0], elR: 60 };
const U_OUT = { drop: -0.3, lean: 8, twist: -15, hipL: [16, 14], hipR: [16, 14], knL: 20, knR: 20, shL: [20, 20, 0], elL: 40, shR: [150, 40, 0], elR: 95 };
const U_SAFE = { drop: -0.4, lean: 12, hipL: [18, 14], hipR: [18, 14], knL: 22, knR: 22, shL: [90, 88, 0], elL: 5, shR: [90, 88, 0], elR: 5 };
const WAVE = (t) => ({ ...STAND, shR: [120 + 40 * Math.sin(t * 9), 40, 0], elR: 30, look: 10 });

// ------------------------------------------------------------------ set the whole play to time t (s since the catch), mode "direct" | "loop"
function setPlay(t, mode = "direct") {
  const sc = SC[mode], path = PLAY.path[mode];
  const gloveT = sc.glove_t, tagT = sc.tag_t;
  // --- right fielder: settles a few feet deep, comes in through the catch, crow-hops and throws
  const deep = CATCH.clone().setY(0).addScaledVector(U, 6);
  const at0 = CATCH.clone().setY(0), atR = REL.clone().setY(0);
  let rp;
  if (t < -0.7) rp = deep.clone().addScaledVector(SIDE, 0.6 * Math.sin(t * 1.3));
  else if (t < 0) rp = deep.clone().lerp(at0, smooth((t + 0.7) / 0.7));
  else if (t < EXCH) rp = at0.clone().lerp(atR, easeIO(t / EXCH));
  else rp = atR.clone().addScaledVector(TOHOME, 3.5 * smooth((t - EXCH) / 0.6));
  rf.root.position.copy(rp); rf.root.rotation.y = Math.atan2(TOHOME.x, TOHOME.z);
  let q;
  if (t < -0.7) q = LOOK_UP;
  else if (t < -0.25) q = mixPose(mixPose(LOOK_UP, runPose(((t + 0.7) * 2.2) % 1, 0.35), 0.6), CATCH_UP, smooth((t + 0.7) / 0.45));
  else q = keyed([[-0.25, CATCH_UP], [0.05, CATCH_UP], [0.3, TRANSFER], [0.55, CROW], [EXCH, RELEASE], [EXCH + 0.35, FOLLOW], [EXCH + 1.2, { ...FOLLOW, lean: 20, drop: -0.3 }]], t);
  applyPose(rf, q);

  // --- the ball: fly ball -> glove -> throwing hand -> the throw -> catcher's glove -> the tag
  let bp; const handPos = (h) => { h.updateWorldMatrix(true, false); const v = new THREE.Vector3(); return h.getWorldPosition(v); };
  // catcher first (his glove carries the ball at the end)
  const kFace = Math.atan2(REL.x - GLOVE.x, REL.z - GLOVE.z);
  const kRoot = GLOVE.clone().setY(0).addScaledVector(v3(Math.sin(kFace), 0, Math.cos(kFace)), -1.5).addScaledVector(v3(Math.cos(kFace), 0, -Math.sin(kFace)), -0.55);
  const sTag = runS(tagT), footTag = onLine3(Math.min(sTag, 89.2), 0.3);
  const kTagYaw = Math.atan2(footTag.x - kRoot.x, footTag.z - kRoot.z);
  catcher.root.position.copy(kRoot);
  let ky = kFace, kq;
  if (mode === "direct") {
    kq = keyed([[gloveT - 0.6, C_READY], [gloveT, C_RECEIVE], [gloveT + 0.06, C_RECEIVE], [tagT, C_TAG]], t);
    ky = lerp(kFace, kTagYaw, smooth((t - gloveT - 0.04) / (tagT - gloveT - 0.04)));
  } else {
    kq = keyed([[gloveT - 0.9, C_READY], [gloveT - 0.25, C_HIGH], [gloveT, C_HIGH], [gloveT + 0.06, C_RECEIVE], [tagT, C_TAG]], t);
    ky = lerp(kFace, kTagYaw, smooth((t - gloveT - 0.04) / (tagT - gloveT - 0.04)));
  }
  catcher.root.rotation.y = ky; applyPose(catcher, kq);
  const gloveHand = handPos(catcher.handL);

  if (t < -0.06) bp = pathAt(PLAY.path.fly, t);
  else if (t < 0.3) bp = pathAt(PLAY.path.fly, Math.min(t, 0)).lerp(handPos(rf.handL), smooth((t + 0.06) / 0.06));
  else if (t < EXCH) { bp = handPos(rf.handR); if (t > EXCH - 0.15) bp.lerp(REL, smooth((t - (EXCH - 0.15)) / 0.15)); }
  else if (t < gloveT) bp = pathAt(path, t);
  else bp = GLOVE.clone().lerp(gloveHand, smooth((t - gloveT) / 0.05));
  const inFlight = t >= EXCH && t < gloveT;
  placeBall(BALL, bp, inFlight ? path : (t < 0 ? PLAY.path.fly : null), t, true, inFlight || t < 0);

  // --- runner: foot on the bag until the catch, then the sprint and a feet-first slide
  const s = runS(t);
  const slideFrom = A.slide_at;
  const ahead = s > slideFrom - 2 ? 3.2 * smooth((s - (slideFrom - 2)) / 4) : 0;        // feet lead the body in the slide
  const off = 0.9 * (1 - smooth(s / 70)) + 0.3;
  const body = onLine3(Math.max(0, s - ahead) + 0.4, off);
  runner.root.position.copy(body);
  runner.root.rotation.y = Math.atan2(D3H.x, D3H.z);
  let rq;
  if (t < A.r_react) rq = ROCKER;
  else {
    const k = clamp((t - A.r_react) / 0.6, 0, 1);
    rq = mixPose(ROCKER, runPose((s / 8.4) % 1, 0.45 + 0.55 * k), smooth((t - A.r_react) / 0.22));
    if (s > slideFrom - 2) rq = mixPose(rq, SLIDE_POSE, smooth((s - (slideFrom - 2)) / 4));
  }
  applyPose(runner, rq);

  // --- the rest of the field
  ump.root.position.set(6.5, 0, 4.0); ump.root.rotation.y = Math.atan2(GLOVE.x - 6.5, GLOVE.z - 4.0);
  const callT = mode === "direct" ? tagT + 0.3 : PLAY.score_t + 0.25;
  applyPose(ump, keyed([[callT - 0.01, U_SET], [callT + 0.25, mode === "direct" ? U_OUT : U_SAFE]], t));
  const backup = GLOVE.clone().setY(0).addScaledVector(TOHOME, 34).addScaledVector(SIDE, -3);
  pitcher.root.position.copy(v3(-20, 0, 6).lerp(backup, smooth((t + 2) / 4))); pitcher.root.rotation.y = Math.atan2(GLOVE.x - backup.x, GLOVE.z - backup.z);
  applyPose(pitcher, t < 1.6 ? runPose(((t + 3) * 2) % 1, 0.6) : READY);
  const cut = GLOVE.clone().setY(0).addScaledVector(U, 48).addScaledVector(SIDE, 4.5);
  firstB.root.position.copy(cut); firstB.root.rotation.y = Math.atan2(REL.x - cut.x, REL.z - cut.z);
  applyPose(firstB, t < sc.glove_t - 0.9 ? { ...STAND, shL: [120, 20, 0], elL: 20, shR: [120, 10, 0], elR: 30 } : { ...READY, look: -120 });
  thirdB.root.position.set(-58.5, 0, -58.5); thirdB.root.rotation.y = Math.atan2(B3.x + 58.5, B3.z + 58.5); applyPose(thirdB, { ...READY, nod: -10 });
  ss.root.position.set(-30, 0, -112); ss.root.rotation.y = Math.atan2(CATCH.x + 30, CATCH.z + 112); applyPose(ss, STAND);
  secondB.root.position.set(38, 0, -150); secondB.root.rotation.y = Math.atan2(CATCH.x - 38, CATCH.z + 150); applyPose(secondB, STAND);
  const cfAt = v3(40, 0, -300).lerp(v3(78, 0, -300), smooth((t + 3) / 3));
  cf.root.position.copy(cfAt); cf.root.rotation.y = Math.atan2(CATCH.x - cfAt.x, CATCH.z - cfAt.z); applyPose(cf, t < 0 ? runPose(((t + 3) * 2.1) % 1, 0.6) : STAND);
  lf.root.position.set(-120, 0, -250); lf.root.rotation.y = Math.atan2(CATCH.x + 120, CATCH.z + 250); applyPose(lf, STAND);
  coach.root.position.set(-80, 0, -50); coach.root.rotation.y = Math.atan2(HOME.x + 80, HOME.z + 50);
  applyPose(coach, t < 0 ? { ...STAND, look: 60 } : WAVE(t));

  // --- the comparison ball: the looping throw, released at the same moment
  return { s, sTag, footTag, body, bp, gloveHand };
}

// ------------------------------------------------------------------ cameras
const cam = new THREE.PerspectiveCamera(40, W / H, 0.3, 2500);
function frame(c, pos, look, fov) { c.position.copy(pos); c.fov = fov; c.aspect = W / H; c.updateProjectionMatrix(); c.lookAt(look); }
const mixV = (a, b, u) => a.clone().lerp(b, u);
const T = CC.shots;      // video-time shot boundaries and play-time mapping, from build.py

const pw = (v, vs, ts) => {                                   // piecewise-linear video time -> play time
  if (v <= vs[0]) return ts[0];
  for (let i = 1; i < vs.length; i++) if (v <= vs[i]) return lerp(ts[i - 1], ts[i], (v - vs[i - 1]) / (vs[i] - vs[i - 1]));
  return ts.at(-1);
};
const SIDECAM = (u) => {                                      // far side view of the throw line, everything to scale
  const mid = REL.clone().lerp(GLOVE, 0.5).setY(0);
  return [mid.clone().addScaledVector(SIDE, lerp(-660, -620, u)).add(v3(0, 22, 0)), mid.clone().add(v3(0, 190, 0)), 50];
};

function shotAt(v) {
  // returns { t, mode, cam: [pos, look, fov], show: {...}, replay }
  const s = T;
  if (v < s.catchV) {                              // hook: one continuous move, from straight above the runner on third,
    const t = v - s.catchV;                         // out over the infield, wide of right field and down behind the fielder for the catch
    const u = easeIO((v - s.sw0) / (s.sw1 - s.sw0));
    const ballP = pathAt(PLAY.path.fly, t);
    const p0 = B3.clone().add(v3(14, 105, 34)).add(v3(0, -6 * clamp(v / s.sw0, 0, 1), 0));
    const p2 = CATCH.clone().setY(0).addScaledVector(U, 26).addScaledVector(SIDE, 5).add(v3(0, 6.5, 0)).addScaledVector(TOHOME, 4 * smooth((v - s.sw1) / (s.catchV - s.sw1)));
    const p1 = CATCH.clone().setY(120).addScaledVector(U, 40).addScaledVector(SIDE, -150);   // swing wide and deep, never over the fielder
    const pos = p0.clone().multiplyScalar((1 - u) * (1 - u)).addScaledVector(p1, 2 * u * (1 - u)).addScaledVector(p2, u * u);
    const look0 = B3.clone().add(v3(4, 0, -6));
    const spot = CATCH.clone().setY(3);
    const k = s.catchV - 1.4;                       // the ball drops into frame over the last 1.4 s
    const track = mixV(spot, ballP, 0.24 * smooth((v - k) / 0.4) * (1 - smooth((v - (s.catchV - 0.5)) / 0.5)));
    const look = mixV(look0, track, smooth((v - s.sw0) / 1.6));
    return { t, cam: [pos, look, lerp(52, 48, u)], show: { ring: true }, ringPulse: v - s.ringT };
  }
  if (v < s.v3) {                                   // freeze at the catch: how far is it?
    const u = (v - s.catchV) / (s.v3 - s.catchV);
    const p0 = CATCH.clone().setY(0).addScaledVector(U, 26).addScaledVector(SIDE, 5).add(v3(0, 6.5, 0)).addScaledVector(TOHOME, 4);
    const p1 = CATCH.clone().setY(0).addScaledVector(U, 95).addScaledVector(SIDE, 20).add(v3(0, 150, 0));
    const look = mixV(CATCH.clone().setY(4), v3(CATCH.x * 0.45, 0, CATCH.z * 0.45), easeIO(u * 1.3));
    return { t: 0, cam: [mixV(p0, p1, easeIO(u * 1.3)), look, lerp(48, 52, easeIO(u))], show: { ring: true, throwLine: smooth((v - s.dl0) / 1.1), runLine: smooth((v - s.dl1) / 0.8) } };
  }
  if (v < s.v4) {                                   // the exchange, in slow motion: glove, crow hop, release
    const t = pw(v, [s.v3, s.vRel, s.v4], [0, EXCH, s.t4]);
    const u = (v - s.v3) / (s.v4 - s.v3);
    const c = REL.clone().setY(0).addScaledVector(U, 3);
    const a = lerp(0.2, 0.95, easeIO(u));
    const dir = SIDE.clone().multiplyScalar(-Math.cos(a)).addScaledVector(TOHOME, Math.sin(a));
    return { t, cam: [c.clone().addScaledVector(dir, lerp(19, 15, u)).add(v3(0, 4.4, 0)), c.clone().add(v3(0, 3.9, 0)).addScaledVector(TOHOME, 2), 36], show: {} };
  }
  if (v < s.v4b) {                                  // the throw, chased from behind and beside it
    const t = pw(v, [s.v4, s.v5], [s.t4, s.t5]);
    const b = pathAt(PLAY.path.direct, t);
    const pos = b.clone().setY(0).addScaledVector(TOHOME, -58).addScaledVector(SIDE, 30).add(v3(0, 12, 0));
    return { t, cam: [pos, b.clone().addScaledVector(TOHOME, 30).setY(b.y * 0.7), 50], show: {} };
  }
  if (v < s.v5) {                                   // looking out from behind the plate: the ball still coming
    const t = pw(v, [s.v4, s.v5], [s.t4, s.t5]), u = (v - s.v4b) / (s.v5 - s.v4b);
    const b = pathAt(PLAY.path.direct, t);
    const pos = GLOVE.clone().setY(0).addScaledVector(TOHOME, 20).addScaledVector(SIDE, -4).add(v3(0, 4.5, 0)).addScaledVector(TOHOME, -3 * u);
    return { t, cam: [pos, mixV(b, GLOVE.clone().addScaledVector(U, 60).setY(10), 0.45), 42], show: {} };
  }
  if (v < s.v6) {                                   // the runner, tracked from behind his shoulder
    const t = pw(v, [s.v5, s.v6], [s.t5, s.t6]);
    const b = onLine3(runS(t), 0.6);
    const pos = b.clone().addScaledVector(D3H, -15).addScaledVector(FOUL3, 7).add(v3(0, 5.5, 0));
    return { t, cam: [pos, b.clone().addScaledVector(D3H, 6).add(v3(0, 2.4, 0)), 40], show: {} };
  }
  if (v < s.v7) {                                   // replay, side view to scale: the line and the loop launched together
    const u = (v - s.v6) / (s.v7 - s.v6);
    const tr = EXCH + Math.max(0, v - s.vLaunch) * s.rRep;
    return { t: EXCH, cam: SIDECAM(u * 0.5), show: { arcsTo: tr }, replay: tr, hud: false };
  }
  if (v < s.vPlate) {                               // the race: behind the runner as the ball comes in
    const t = pw(v, [s.v7, s.vPlate, s.vTime], [s.t7, PLAY.direct.glove_t, PLAY.direct.tag_t]);
    const b = onLine3(runS(t), 0.6);
    const pos = b.clone().addScaledVector(D3H, -17).addScaledVector(FOUL3, 9).add(v3(0, 6.5, 0));
    return { t, cam: [pos, b.clone().addScaledVector(D3H, 9).add(v3(0, 2.6, 0)), 46], show: {} };
  }
  if (v < s.vTime) {                                // the plate from the first-base side, slowing to the tag
    const t = pw(v, [s.v7, s.vPlate, s.vTime], [s.t7, PLAY.direct.glove_t, PLAY.direct.tag_t]);
    const u = easeIO((v - s.vPlate) / (s.vTime - s.vPlate));
    return { t, cam: [mixV(v3(21, 6.2, -15.5), v3(18, 5.4, -13.2), u), mixV(v3(-4.2, 1.5, -4.4), v3(-4.8, 1.3, -4.8), u), lerp(44, 41, u)], show: {} };
  }
  if (v < s.v8) {                                   // freeze on the tag: orbit from foul ground
    const u = (v - s.vTime) / (s.v8 - s.vTime), t = PLAY.direct.tag_t;
    const ctr = v3(-3.0, 1.2, -3.4);
    const a = lerp(-1.75, -0.55, easeIO(u)), rad = lerp(13, 16, u);
    const pos = v3(ctr.x + Math.sin(a) * rad, lerp(3.4, 6.0, easeIO(u)), ctr.z + Math.cos(a) * rad);
    return { t, cam: [pos, ctr, 38], show: { gap: true } };
  }
  if (v < s.v9) {                                   // what decides it: both throws side by side, to scale
    const u = (v - s.v8) / (s.v9 - s.v8);
    return { t: PLAY.direct.tag_t, cam: SIDECAM(0.5 + 0.5 * u), show: { arcsTo: 99 }, hud: false };
  }
  {                                                 // send him or hold him? back above the runner on third, before the catch
    const u = (v - s.v9) / (CC.duration - s.v9);
    const pos = B3.clone().add(v3(lerp(10, 6, u), lerp(70, 52, easeIO(u)), lerp(26, 18, u)));
    return { t: -0.35, cam: [pos, B3.clone().add(v3(5, 0, -4)), 50], show: { ring: true }, hud: false };
  }
}

// ------------------------------------------------------------------ DOM overlays fed from the same clock
const $ = (id) => document.getElementById(id);
const fmt = (x) => Math.max(0, x).toFixed(2);
function overlays(st) {
  const set = (id, txt) => { for (const k of [id, id.replace("tm-", "tm2-")]) { const e = $(k); if (e) e.textContent = txt; } };   // both clock panels
  const t = st.t, sc = SC.direct;
  const scored = runS(t) >= A.r_dist;
  set("tm-run", fmt(scored ? PLAY.score_t : t));
  set("tm-run-ft", scored ? "safe at the plate" : `${Math.max(0, A.r_dist - runS(t)).toFixed(1)} ft to go`);
  set("tm-ball", fmt(Math.min(t, sc.tag_t)));
  set("tm-ball-ph", t < EXCH ? "release" : t < sc.glove_t ? `in flight ${fmt(t - EXCH)} s` : t < sc.tag_t ? "caught · tag" : "tag applied");
  set("tm-fl", fmt(clamp(t - EXCH, 0, PLAY.direct.flight)));
  if (st.replay != null) {
    set("tm-rd", fmt(clamp(st.replay - EXCH, 0, PLAY.direct.flight)));
    set("tm-rl", fmt(clamp(st.replay - EXCH, 0, PLAY.loop.flight)));
  }
}

function revealArc(g, path, tr) { reveal(g, clamp((tr - path.t0) / path.dur, 0, 1) + 1e-6 * (tr >= path.t0 + path.dur)); }
function renderAt(v) {
  const st = shotAt(v);
  const r = setPlay(st.t, "direct");
  if (st.replay != null) {                  // the replay: both throws on their own clock, the players held at the release
    const tr = st.replay;
    placeBall(BALL, tr < flightEnd(PLAY.path.direct) ? pathAt(PLAY.path.direct, tr) : GLOVE.clone(), PLAY.path.direct, tr, true, true);
    placeBall(GHOST, tr < flightEnd(PLAY.path.loop) ? pathAt(PLAY.path.loop, tr) : GLOVE.clone(), PLAY.path.loop, tr, true, true);
  } else placeBall(GHOST, v3(0, -50, 0), null, 0, false, false);
  reveal(throwLine, st.show?.throwLine ?? 0);
  reveal(runLine, st.show?.runLine ?? 0);
  if (st.show?.arcsTo != null) { revealArc(directArc, PLAY.path.direct, st.show.arcsTo); revealArc(loopArc, PLAY.path.loop, st.show.arcsTo); }
  else directArc.visible = loopArc.visible = false;
  catchRing.visible = !!st.show?.ring;
  const rp = st.ringPulse ?? -1;                 // the ring punches out on the cue word
  catchRing.scale.setScalar(rp > 0 ? 1 + 0.55 * Math.exp(-rp * 5) * Math.sin(Math.min(rp * 14, Math.PI)) : 1);
  gapMark.visible = !!st.show?.gap;
  if (gapLabel) gapLabel.visible = !!st.show?.gap;
  if (st.show?.gap) {                       // the distance the runner's foot is still short of the plate
    const a = onLine3(PLAY.direct.runner_at_tag, 0.3), b = onLine3(A.r_dist, 0.3);
    gapMark.scale.z = Math.max(0.1, a.distanceTo(b)); gapMark.position.copy(a.clone().lerp(b, 0.5)).setY(0.14); gapMark.lookAt(b.x, 0.14, b.z);
    if (gapLabel) gapLabel.position.copy(a.clone().lerp(b, 0.5)).addScaledVector(FOUL3, 2.4).setY(1.0);
  }
  frame(cam, st.cam[0], st.cam[1], st.cam[2]);
  renderer.render(scene, cam);
  overlays(st);
}

let last = -1;
function seek(time) { if (time === last) return; last = time; renderAt(time); }
window.addEventListener("hf-seek", (e) => seek(e.detail.time));
window.__fieldRender = renderAt;
document.fonts.ready.then(() => seek(window.__hfThreeTime || 0));
seek(window.__hfThreeTime || 0);
