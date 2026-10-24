// "Look at the clock": a regulation baseball field, the players and the stolen-base race, in three.js.
// Everything is a pure function of HyperFrames time (hf-seek), so each frame is exact and repeatable.
// Units are feet. Home plate is the origin, +x points toward first base's side, -z toward center field.
// The play is computed from the script's numbers: time to plate (1.4 s or 1.2 s) + a 1.9 s pop time.
import * as THREE from "three";

const CC = window.__CC;                 // timing from build.py (shot boundaries follow the voiceover)
const W = 1080, H = 1920;
const v3 = (x, y, z) => new THREE.Vector3(x, y, z);
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const lerp = (a, b, u) => a + (b - a) * u;
const smooth = (u) => { u = clamp(u, 0, 1); return u * u * (3 - 2 * u); };
const easeIO = (u) => { u = clamp(u, 0, 1); return u < .5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2; };

// ------------------------------------------------------------------ field geometry (feet)
const HOME = v3(0, 0, 0), B1 = v3(63.64, 0, -63.64), B2 = v3(0, 0, -127.28), B3 = v3(-63.64, 0, -63.64);
const MOUND = v3(0, 0, -59), RUBBER_Z = -60.5, MOUND_H = 0.83;
const DIR12 = B2.clone().sub(B1).normalize();          // first -> second
const LEAD = 12;                                       // runner's lead off first, feet
const POP = 1.9;

// ------------------------------------------------------------------ the play, as a function of play time p (s since the pitcher's first move)
function scenario(Td) {
  const release = Td - 0.42;                 // a ~90 mph pitch covers ~55 ft in ~0.42 s
  const caught = Td;
  const throwAt = Td + 0.72;                 // catcher's transfer and release
  const arrive = Td + POP;                   // ball reaches the fielder at second
  return { Td, release, caught, throwAt, arrive };
}
const SCN = { A: scenario(1.4), B: scenario(1.2) };

// runner: reacts at 0.05 s, accelerates toward 30 ft/s (time constant 0.62 s); slides for the last 9 ft
const R_REACT = 0.05, R_VMAX = 30, R_TAU = 0.62, R_DIST = 90 - LEAD;
const runDist = (p) => { const t = p - R_REACT; if (t <= 0) return 0; return R_VMAX * (t - R_TAU * (1 - Math.exp(-t / R_TAU))); };
let RUN_ARRIVE = 0; for (let p = 0; p < 6; p += 0.0005) if (runDist(p) >= R_DIST) { RUN_ARRIVE = p; break; }
window.__RUN_ARRIVE = RUN_ARRIVE;

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
for (const [x, z] of [[-330, -260], [330, -260], [-420, 40], [420, 40], [-200, -470], [200, -470]]) {
  const tower = new THREE.Mesh(new THREE.BoxGeometry(26, 10, 4), new THREE.MeshBasicMaterial({ color: 0xfff6e6 }));
  tower.position.set(x, 150, z); tower.lookAt(0, 0, -60); scene.add(tower);
}

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

const pitcher = makePlayer(KIT.home, { glove: true });
const catcher = makePlayer(KIT.home, { glove: true, catcher: true });
const runner = makePlayer(KIT.away, { helmet: true });
const shortstop = makePlayer(KIT.home, { glove: true });
const firstB = makePlayer(KIT.home, { glove: true });
const secondB = makePlayer(KIT.home, { glove: true });
const batter = makePlayer(KIT.away, { helmet: true, bat: true });
for (const p of [pitcher, catcher, runner, shortstop, firstB, secondB, batter]) scene.add(p.root);

// ball, its trail, and analysis marks
const ball = new THREE.Mesh(new THREE.SphereGeometry(0.33, 16, 12), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xfff2c0, emissiveIntensity: 0.55, roughness: 0.4 }));
ball.castShadow = true; scene.add(ball);
const trailMat = new THREE.MeshBasicMaterial({ color: 0xffd84d, transparent: true, opacity: 0.85, depthWrite: false });
const TRAIL_N = 26; const trail = [];
for (let i = 0; i < TRAIL_N; i++) { const m = new THREE.Mesh(new THREE.SphereGeometry(0.22 * (1 - i / TRAIL_N) + 0.05, 8, 6), trailMat.clone()); m.material.opacity = 0.7 * (1 - i / TRAIL_N); scene.add(m); trail.push(m); }

function lineMesh(points, color, width, y = 0.08, dashed = false) {
  const g = new THREE.Group();
  for (let i = 0; i < points.length - 1; i++) {
    if (dashed && i % 2) continue;
    const a = points[i], b = points[i + 1], len = a.distanceTo(b);
    const m = new THREE.Mesh(new THREE.BoxGeometry(width, 0.05, len), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.9, depthWrite: false }));
    m.position.set((a.x + b.x) / 2, (a.y + b.y) / 2 + y, (a.z + b.z) / 2); m.lookAt(b.x, b.y + y, b.z); g.add(m);
  }
  scene.add(g); return g;
}
const runPath = lineMesh(Array.from({ length: 31 }, (_, i) => B1.clone().addScaledVector(DIR12, LEAD + (i / 30) * (90 - LEAD))), 0x56d1ff, 0.55, 0.06, true);
function arcPoints(a, b, h, n = 40) { return Array.from({ length: n + 1 }, (_, i) => { const u = i / n; const p = a.clone().lerp(b, u); p.y += h * 4 * u * (1 - u); return p; }); }
const PITCH_FROM = v3(-1.8, MOUND_H + 5.4, -54.6), GLOVE_AT = v3(0.25, 2.25, 1.0), THROW_FROM = v3(0.55, 6.1, 1.2), TAG_AT = v3(0.45, 2.0, -126.4);
const ballPath = lineMesh([...arcPoints(PITCH_FROM, GLOVE_AT, 0.6, 20), ...arcPoints(THROW_FROM, TAG_AT, 4.2, 40)], 0xffd84d, 0.32, 0, false);

function labelSprite(text, color = "#ffffff", bg = "rgba(8,12,20,0.82)") {
  const t = canvasTex(512, 160, (g, w, h) => {
    g.fillStyle = bg; g.beginPath(); g.roundRect(4, 4, w - 8, h - 8, 34); g.fill();
    g.fillStyle = color; g.font = "800 92px 'Barlow Condensed', sans-serif"; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(text, w / 2, h / 2 + 4);
  });
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, depthTest: false, transparent: true })); s.scale.set(3.4, 1.06, 1); s.renderOrder = 10; scene.add(s); return s;
}
const gapMark = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.06, 1), new THREE.MeshBasicMaterial({ color: 0x56d1ff }));
scene.add(gapMark);
let gapLabel = null;                                   // drawn once the caption font has loaded
document.fonts.load("800 92px 'Barlow Condensed'").then(() => { gapLabel = labelSprite("≈ 5 FT", "#56d1ff"); gapLabel.visible = false; last = -1; seek(window.__hfThreeTime || 0); });

// ------------------------------------------------------------------ set the whole play to time p, scenario S
function setPlay(p, S) {
  const { Td, release, caught, throwAt, arrive } = S;
  // --- pitcher (right-hander, from the stretch): side-on, slide step, throw, follow-through
  const mz = RUBBER_Z + 0.4;
  const toHome = 0, sideOn = -Math.PI / 2;          // facing +z = home; facing -x = third base side
  const r = release;
  const pf = [
    [-9, { ...SET_POSE }],
    [0.0, { ...SET_POSE, look: -10 }],
    [r * 0.35, { lean: -4, look: 0, hipL: [48, 6], knL: 62, hipR: [6, 6], knR: 14, shL: [40, 6, 0], shR: [40, 6, 0], elL: 100, elR: 100 }],
    [r * 0.72, { drop: -0.55, lean: -6, twist: -30, hipL: [36, 22], knL: 30, hipR: [-12, 10], knR: 34, shL: [60, 70, 0], elL: 40, shR: [-20, 95, 0], elR: 95 }],
    [r, { drop: -0.8, lean: 32, twist: 15, hipL: [50, 18], knL: 36, hipR: [-28, 10], knR: 40, shL: [10, 30, 0], elL: 70, shR: [150, 40, 0], elR: 15, nod: -10 }],
    [r + 0.35, { drop: -0.9, lean: 48, twist: 40, hipL: [62, 16], knL: 55, hipR: [10, 10], knR: 70, shL: [-10, 25, 0], elL: 80, shR: [70, 10, 40], elR: 30, nod: -20 }],
    [r + 1.2, { drop: -0.6, lean: 24, hipL: [36, 16], knL: 40, hipR: [30, 16], knR: 40, shL: [20, 14, 0], shR: [20, 14, 0], elL: 40, elR: 40, nod: -8 }],
  ];
  applyPose(pitcher, keyed(pf, p));
  const yawP = p < r * 0.55 ? sideOn : lerp(sideOn, toHome, easeIO((p - r * 0.55) / (r * 0.5)));
  const stride = smooth((p - r * 0.35) / (r * 0.4)) * 4.2;
  pitcher.root.position.set(0, MOUND_H, mz + stride * smooth((p - r * 0.5) / (r * 0.4)));
  pitcher.root.rotation.y = yawP;

  // --- catcher: receives at Td, pops up, throws at throwAt
  const cf = [
    [-9, CROUCH], [caught - 0.15, CROUCH],
    [caught, { ...CROUCH, shL: [80, 16, 0], elL: 20 }],
    [caught + 0.3, { drop: -0.9, lean: 26, hipL: [50, 18], knL: 60, hipR: [40, 18], knR: 70, shL: [70, 30, 0], elL: 60, shR: [-10, 80, 0], elR: 100, twist: -35 }],
    [throwAt - 0.05, { drop: -0.6, lean: 12, hipL: [30, 14], knL: 30, hipR: [-8, 14], knR: 30, shL: [55, 50, 0], elL: 40, shR: [-30, 100, 0], elR: 95, twist: -45 }],
    [throwAt + 0.12, { drop: -0.7, lean: 34, hipL: [40, 14], knL: 34, hipR: [-24, 14], knR: 40, shL: [10, 30, 0], elL: 60, shR: [150, 30, 0], elR: 10, twist: 15 }],
    [throwAt + 0.6, { drop: -0.6, lean: 40, hipL: [44, 14], knL: 40, hipR: [10, 14], knR: 50, shL: [0, 20, 0], elL: 60, shR: [60, 10, 30], elR: 30, twist: 30 }],
  ];
  applyPose(catcher, keyed(cf, p));
  const cStep = smooth((p - caught - 0.2) / 0.35) * 1.6;
  catcher.root.position.set(0.2, 0, 2.9 - cStep); catcher.root.rotation.y = Math.PI;   // faces the pitcher (-z)

  // --- runner: lead, jump, sprint, slide
  const d = runDist(p);
  const slideFrom = R_DIST - 9;
  let rp, ry;
  const facePitcher = yawTo(B1.clone().addScaledVector(DIR12, LEAD), v3(0, 0, RUBBER_Z));
  const faceRun = Math.atan2(DIR12.x, DIR12.z);
  if (p < R_REACT) {
    const shuffle = p < -1.5 ? 0.45 * Math.sin((p + 9) * 1.3) : 0;
    rp = B1.clone().addScaledVector(DIR12, LEAD + shuffle); ry = facePitcher;
    applyPose(runner, { ...LEAD_POSE, look: 4 });
  } else {
    const dd = Math.min(d, R_DIST + 0.6);
    rp = B1.clone().addScaledVector(DIR12, LEAD + dd - (dd > slideFrom ? 0 : 0));
    const turn = smooth((p - R_REACT) / 0.32);
    ry = lerp(facePitcher, faceRun, turn);
    const k = clamp((p - R_REACT) / 0.5, 0, 1);
    let q = runPose((dd / 8.2) % 1, 0.45 + 0.55 * k);
    q = mixPose(LEAD_POSE, q, smooth((p - R_REACT) / 0.25));
    if (dd > slideFrom) q = mixPose(q, SLIDE_POSE, smooth((dd - slideFrom) / 4.5));
    q.look = d < 30 ? lerp(-40, 0, d / 30) : 0;          // a look in at the plate as he goes
    applyPose(runner, q);
  }
  runner.root.position.copy(rp); runner.root.rotation.y = ry;

  // --- shortstop: covers second, receives the throw, tags
  const ssStart = v3(-24, 0, -143), ssBag = v3(0.9, 0, -125.9);
  const goT = Td + 0.08, atBag = Td + 1.55;
  const sp = clamp((p - goT) / (atBag - goT), 0, 1);
  const ssPos = ssStart.clone().lerp(ssBag, easeIO(sp));
  shortstop.root.position.copy(ssPos);
  const ssRunYaw = yawTo(ssStart, ssBag), ssFaceHome = yawTo(ssBag, v3(0, 0, 0));
  shortstop.root.rotation.y = sp < 0.7 ? (p < goT ? ssFaceHome : ssRunYaw) : lerp(ssRunYaw, ssFaceHome, smooth((sp - 0.7) / 0.3));
  let sq;
  if (p < goT) sq = READY;
  else if (sp < 1) sq = mixPose(runPose(((p - goT) * 2.6) % 1, 0.8), READY, smooth((sp - 0.8) / 0.2));
  else sq = keyed([[atBag, { ...READY, shL: [70, 20, 0], elL: 30 }], [arrive, { drop: -0.7, lean: 30, hipL: [40, 20], knL: 44, hipR: [40, 20], knR: 44, shL: [95, 25, 0], elL: 10, shR: [60, 20, 0], elR: 50 }],
                    [arrive + 0.18, { drop: -1.3, lean: 52, hipL: [60, 24], knL: 70, hipR: [60, 24], knR: 70, shL: [70, 55, 0], elL: 5, shR: [40, 30, 0], elR: 60, nod: -30 }]], p);
  applyPose(shortstop, sq);

  // --- first baseman holds the runner, second baseman in his spot, batter takes the pitch
  firstB.root.position.set(61.2, 0, -62.2); firstB.root.rotation.y = yawTo(v3(61.2, 0, -62.2), v3(0, 0, RUBBER_Z));
  applyPose(firstB, p < 0.2 ? { ...READY, shL: [60, 20, 0], elL: 30 } : mixPose({ ...READY, shL: [60, 20, 0], elL: 30 }, STAND, smooth((p - 0.2) / 0.6)));
  secondB.root.position.set(34, 0, -146); secondB.root.rotation.y = yawTo(v3(34, 0, -146), HOME);
  applyPose(secondB, p < Td ? READY : mixPose(READY, STAND, smooth((p - Td) / 0.8)));
  batter.root.position.set(-3.2, 0, 0.2); batter.root.rotation.y = Math.PI / 2;
  applyPose(batter, BAT_STANCE);
  batter.bat.rotation.set(0.5, 0, -0.9);

  // --- the ball
  let bp;
  if (p < release) { pitcher.handR.updateWorldMatrix(true, false); bp = new THREE.Vector3(); pitcher.handR.getWorldPosition(bp); }
  else if (p < caught) {
    const u = (p - release) / (caught - release);
    bp = PITCH_FROM.clone().lerp(GLOVE_AT, u); bp.y += 0.6 * 4 * u * (1 - u) - 1.2 * u * u * 0;
  } else if (p < throwAt) {
    const hand = p < caught + 0.35 ? catcher.handL : catcher.handR;
    hand.updateWorldMatrix(true, false); bp = new THREE.Vector3(); hand.getWorldPosition(bp);
  } else if (p < arrive) {
    const u = (p - throwAt) / (arrive - throwAt);
    bp = THROW_FROM.clone().lerp(TAG_AT, u); bp.y += 4.2 * 4 * u * (1 - u);
  } else { shortstop.handL.updateWorldMatrix(true, false); bp = new THREE.Vector3(); shortstop.handL.getWorldPosition(bp); }
  ball.position.copy(bp);
  ball.scale.setScalar(p >= release && p < arrive ? 1 : 0.8);
  // trail: where the ball was in the last ~0.12 s of flight
  const inFlight = (q) => (q >= release && q < caught) || (q >= throwAt && q < arrive);
  for (let i = 0; i < TRAIL_N; i++) {
    const q = p - (i + 1) * 0.006;
    const m = trail[i];
    if (!inFlight(p) || !inFlight(q)) { m.visible = false; continue; }
    let tp;
    if (q < caught) { const u = (q - release) / (caught - release); tp = PITCH_FROM.clone().lerp(GLOVE_AT, u); tp.y += 0.6 * 4 * u * (1 - u); }
    else { const u = (q - throwAt) / (arrive - throwAt); tp = THROW_FROM.clone().lerp(TAG_AT, u); tp.y += 4.2 * 4 * u * (1 - u); }
    m.position.copy(tp); m.visible = true;
  }
  return { runnerDist: d };
}

// ------------------------------------------------------------------ cameras
const cam = new THREE.PerspectiveCamera(40, W / H, 0.3, 2000);
function frame(c, pos, look, fov, aspect = W / H) { c.position.copy(pos); c.fov = fov; c.aspect = aspect; c.updateProjectionMatrix(); c.lookAt(look); }
const mixV = (a, b, u) => a.clone().lerp(b, u);
const T = CC.shots;      // shot times from build.py
const CF_POS = v3(-3.5, 17, -205), CF_LOOK = v3(0, 3.2, -18);          // center-field camera, long lens

function shotAt(t) {
  // returns { p, S, cam: [pos, look, fov], split?: {...}, show: {paths, gap} }
  const s = T;
  if (t < s.s1b) {                                          // runner leading off first, from behind him
    const u = t / s.s1b;
    return { p: -9 + t, S: SCN.A, cam: [mixV(v3(73, 4.2, -79.5), v3(69.5, 3.9, -77.5), easeIO(u)), v3(20, 3.5, -64), 30] };
  }
  if (t < s.s2) {                                            // over the catcher's shoulder: the catcher, the runner off first
    const u = (t - s.s1b) / (s.s2 - s.s1b);
    return { p: -9 + t, S: SCN.A, cam: [mixV(v3(1.2, 5.4, 14.5), v3(0.9, 5.0, 12.2), easeIO(u)), v3(0, 1.6, -40), 34] };
  }
  if (t < s.s3) {                                            // center-field camera: the delivery, timed
    const p = clamp((t - s.go2) * 0.5, -2, 1.42);
    return { p, S: SCN.A, cam: [CF_POS, CF_LOOK, 7.2], timer: { del: clamp(p, 0, 1.4) } };
  }
  if (t < s.s4) {                                            // split: delivery (top) + pop time (bottom)
    const pTop = clamp((t - s.go3a) * 0.5, -0.2, 1.4);
    const pBot = 1.4 + clamp((t - s.go3b) * 0.5, 0, 1.9);
    return { split: { top: { p: pTop, cam: [CF_POS, CF_LOOK, 4.6] }, bot: { p: pBot, cam: [v3(25, 5, -15), v3(-0.5, 3.4, 0.5), 23] } }, S: SCN.A,
             timer: { del: clamp(pTop, 0, 1.4), pop: clamp(pBot - 1.4, 0, 1.9) } };
  }
  if (t < s.s5) {                                            // the 3.3 seconds, drawn out on the field
    const u = (t - s.s4) / (s.s5 - s.s4);
    return { p: SCN.A.arrive, S: SCN.A, cam: [mixV(v3(26, 120, 66), v3(48, 108, 44), easeIO(u)), v3(14, 0, -78), 38], show: { paths: true } };
  }
  if (t < s.s6) {                                            // 1.2 s delivery: the runner breaks, the ball travels
    const p = clamp((t - s.go5) * 0.42, -1.5, SCN.B.arrive);
    const u = (t - s.s5) / (s.s6 - s.s5);
    const look = mixV(v3(18, 2.5, -78), v3(4, 2.5, -118), easeIO(u));
    return { p, S: SCN.B, cam: [mixV(v3(104, 30, -30), v3(70, 22, -70), easeIO(u)), look, 34], timer: { del: clamp(p, 0, 1.2), total: clamp(p, 0, SCN.B.arrive) }, show: { runPath: true } };
  }
  if (t < s.s7) {                                            // freeze: the ball is at second, the runner isn't
    const u = (t - s.s6) / (s.s7 - s.s6);
    const a = lerp(-0.35, 1.25, easeIO(u)), rad = lerp(22, 19, u);
    const pos = v3(B2.x + Math.sin(a) * rad, lerp(5.5, 8.5, u), B2.z + Math.cos(a) * rad);
    return { p: SCN.B.arrive, S: SCN.B, cam: [pos, v3(2.5, 1.8, -124), 40], show: { gap: true, runPath: true } };
  }
  {                                                          // overhead, second base: the tag
    const u = (t - s.s7) / (CC.duration - s.s7);
    const p = SCN.B.arrive + clamp((t - s.s7) * 0.12, 0, 0.32);
    const h = lerp(46, 30, easeIO(u));
    return { p, S: SCN.B, overhead: true, cam: [v3(4, h, -123.5), v3(4, 0, -123.6), 40], spin: lerp(0.2, -0.15, easeIO(u)) };
  }
}

// ------------------------------------------------------------------ DOM overlays fed from the same clock
const $ = (id) => document.getElementById(id);
const fmt = (x) => x.toFixed(2);
function overlays(st) {
  const tm = st.timer || {};
  if ($("tm-del") && tm.del != null) $("tm-del").textContent = fmt(tm.del);
  if ($("tm-pop") && tm.pop != null) $("tm-pop").textContent = fmt(tm.pop);
  if ($("tm-b-del") && tm.del != null && st.S === SCN.B) $("tm-b-del").textContent = fmt(tm.del);
  if ($("tm-b-tot") && tm.total != null) $("tm-b-tot").textContent = fmt(tm.total);
}

function renderAt(t) {
  const st = shotAt(t);
  runPath.visible = !!st.show?.runPath || !!st.show?.paths;
  ballPath.visible = !!st.show?.paths;
  gapMark.visible = !!st.show?.gap;
  if (gapLabel) gapLabel.visible = !!st.show?.gap;
  for (const m of trail) m.visible = false;
  if (st.split) {
    renderer.setScissorTest(true);
    for (const [key, y] of [["top", H / 2], ["bot", 0]]) {
      const v = st.split[key];
      setPlay(v.p, st.S);
      frame(cam, v.cam[0], v.cam[1], v.cam[2], W / (H / 2));
      renderer.setViewport(0, y, W, H / 2); renderer.setScissor(0, y, W, H / 2);
      renderer.render(scene, cam);
    }
    renderer.setScissorTest(false); renderer.setViewport(0, 0, W, H);
  } else {
    const r = setPlay(st.p, st.S);
    if (st.show?.gap) {           // the distance still to go when the ball arrives
      const footD = LEAD + r.runnerDist;
      const a = B1.clone().addScaledVector(DIR12, Math.min(footD + 1.6, 89.2)), b = B1.clone().addScaledVector(DIR12, 89.3);
      gapMark.scale.z = Math.max(0.1, a.distanceTo(b));
      gapMark.position.copy(a.clone().lerp(b, 0.5)).setY(0.12); gapMark.lookAt(b.x, 0.12, b.z);
      if (gapLabel) gapLabel.position.copy(a.clone().lerp(b, 0.5)).add(v3(DIR12.z, 0, -DIR12.x).multiplyScalar(-2.6)).setY(0.9);
    }
    frame(cam, st.cam[0], st.cam[1], st.cam[2]);
    if (st.overhead) { cam.up.set(Math.sin(st.spin), 0, -Math.cos(st.spin)); cam.lookAt(st.cam[1]); cam.up.set(0, 1, 0); }
    renderer.render(scene, cam);
  }
  overlays(st);
}

let last = -1;
function seek(time) { if (time === last) return; last = time; renderAt(time); }
window.addEventListener("hf-seek", (e) => seek(e.detail.time));
window.__fieldRender = renderAt;
document.fonts.ready.then(() => seek(window.__hfThreeTime || 0));
seek(window.__hfThreeTime || 0);
