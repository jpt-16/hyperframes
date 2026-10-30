// "The hit-and-run": the field, dugouts, outfield seats, the players, in three.js.
// Everything is a pure function of HyperFrames time (hf-seek), so each frame is exact and repeatable.
// Units are feet. Home plate's back point is the origin, +x points toward first base's side, -z toward center field.
// The pitches and batted balls come from tools/physics.py via window.__PLAY.
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
const G0 = { x: -260, z: -440, size: 520 };
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
strip(v3(1.5, 0, -1.5), v3(233, 0, -233), 0.33); strip(v3(-1.5, 0, -1.5), v3(-233, 0, -233), 0.33);
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

// outfield wall (330 ft at the lines, 375 in the alleys, 400 in center), warning track, foul poles
const FENCE = PLAY.fence;                                    // [[spray angle (rad), distance (ft)], ...] from tools/physics.py
const fenceAt = (a) => { const i = clamp((a - FENCE[0][0]) / (FENCE[1][0] - FENCE[0][0]), 0, FENCE.length - 1.001), k = Math.floor(i); return lerp(FENCE[k][1], FENCE[k + 1][1], i - k); };
const sprayPt = (a, r, y = 0) => v3(Math.sin(a) * r, y, -Math.cos(a) * r);
{
  const wallMat = new THREE.MeshStandardMaterial({ color: 0x1d3a2a, roughness: 0.9 }), padMat = new THREE.MeshStandardMaterial({ color: 0xd8b03a, roughness: 0.6 });
  const trackMat = new THREE.MeshStandardMaterial({ color: 0x9a6640, roughness: 1, bumpMap: dirtDetail, bumpScale: 0.6 });
  const wp = [], tp = [], ti = [];
  for (let k = 0; k < FENCE.length; k++) { const [a, r] = FENCE[k]; wp.push(sprayPt(a, r)); tp.push(sprayPt(a, r - 15), sprayPt(a, r)); }
  for (let k = 0; k < wp.length - 1; k++) {
    const a = wp[k], b = wp[k + 1], len = a.distanceTo(b) + 0.2;
    const m = new THREE.Mesh(new THREE.BoxGeometry(len, 8, 1.2), wallMat); m.position.set((a.x + b.x) / 2, 4, (a.z + b.z) / 2); m.rotation.y = -Math.atan2(b.z - a.z, b.x - a.x); m.castShadow = true; scene.add(m);
    const pad = new THREE.Mesh(new THREE.BoxGeometry(len, 0.35, 1.3), padMat); pad.position.set(m.position.x, 8.1, m.position.z); pad.rotation.y = m.rotation.y; scene.add(pad);
    const i = 2 * k; ti.push(i, i + 1, i + 2, i + 1, i + 3, i + 2);
  }
  const tg = new THREE.BufferGeometry().setFromPoints(tp.map((q) => q.clone().setY(0.025))); tg.setIndex(ti); tg.computeVertexNormals();
  const track = new THREE.Mesh(tg, trackMat); track.receiveShadow = true; track.material.side = THREE.DoubleSide; scene.add(track);
  for (const sgn of [-1, 1]) { const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 70, 10), new THREE.MeshStandardMaterial({ color: 0xf2d230, emissive: 0x3a3000, roughness: 0.5 })); const q = sprayPt(sgn * Math.PI / 4, fenceAt(sgn * Math.PI / 4) + 0.8); pole.position.set(q.x, 35, q.z); scene.add(pole); }
}
const standTex = canvasTex(2048, 256, (g, w, h) => {
  g.fillStyle = "#0e131c"; g.fillRect(0, 0, w, h);
  for (let k = 0; k < 9000; k++) { const v = rnd(); g.fillStyle = v < 0.7 ? `rgba(70,80,100,${0.25 + rnd() * 0.3})` : `rgba(210,190,160,${0.15 + rnd() * 0.25})`; g.fillRect(rnd() * w, 30 + rnd() * (h - 40), 2, 3); }
});
const stands = new THREE.Mesh(new THREE.CylinderGeometry(560, 430, 120, 96, 1, true), new THREE.MeshStandardMaterial({ map: standTex, roughness: 1, side: THREE.BackSide, emissive: 0x0a0d12 }));
stands.position.set(0, 55, -40); scene.add(stands);

// ------------------------------------------------------------------ lights: a night game under bright banks
scene.add(new THREE.HemisphereLight(0x8fa6c8, 0x223318, 0.55));
const key = new THREE.DirectionalLight(0xfff3e2, 2.6);
key.position.set(-160, 300, 40); key.target.position.set(0, 0, -90);
key.castShadow = true; key.shadow.mapSize.set(4096, 4096);
Object.assign(key.shadow.camera, { left: -170, right: 170, top: 170, bottom: -170, near: 50, far: 900 });
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


// ------------------------------------------------------------------ the ballpark: outfield seats, dugouts, on-deck circles
const V = (a) => v3(a[0], a[1], a[2]);
const wpos = (o) => { o.updateWorldMatrix(true, false); return o.getWorldPosition(new THREE.Vector3()); };
const SEAT = PLAY.seats;
{
  const crowd = canvasTex(2048, 512, (g, w, h) => {          // rows of fans, about 2 ft each, 3 ft rows
    g.fillStyle = "#141a24"; g.fillRect(0, 0, w, h);
    const rows = 24;
    for (let r = 0; r < rows; r++) {
      const y = (r + 0.5) / rows * h; g.fillStyle = "#283041"; g.fillRect(0, y + 7, w, 3);
      for (let x = 4; x < w; x += 22 + rnd() * 8) {
        if (rnd() < 0.12) continue;
        const c = rnd(), col = c < 0.3 ? `rgb(${215 + rnd() * 30},${210 + rnd() * 30},${195 + rnd() * 30})` : c < 0.62 ? `rgb(${25 + rnd() * 20},${60 + rnd() * 30},${150 + rnd() * 40})` : c < 0.74 ? `rgb(${180 + rnd() * 40},${50 + rnd() * 20},${45 + rnd() * 20})` : `rgb(${80 + rnd() * 70},${80 + rnd() * 70},${90 + rnd() * 70})`;
        g.fillStyle = col; g.fillRect(x, y - 6, 12, 10); g.fillStyle = "#b98b6a"; g.fillRect(x + 3, y - 12, 6, 6);
      }
    }
  });
  crowd.wrapS = THREE.RepeatWrapping;
  const pos = [], uv = [], idx = [], n = FENCE.length, dep = 70;
  for (let k = 0; k < n; k++) {
    const [a, r] = FENCE[k], f = sprayPt(a, r + SEAT.gap, SEAT.y0), b = sprayPt(a, r + SEAT.gap + dep, SEAT.y0 + SEAT.rise * dep), u = k / (n - 1) * 9;
    pos.push(f.x, f.y, f.z, b.x, b.y, b.z); uv.push(u, 0, u, 1);
    if (k) { const i = 2 * k; idx.push(i - 2, i - 1, i, i - 1, i + 1, i); }
  }
  const sg = new THREE.BufferGeometry(); sg.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3)); sg.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2)); sg.setIndex(idx); sg.computeVertexNormals();
  const seats = new THREE.Mesh(sg, new THREE.MeshStandardMaterial({ map: crowd, roughness: 1, side: THREE.DoubleSide, emissive: 0x0b0f16 })); seats.receiveShadow = true; scene.add(seats);
  const fp = [], fi = [];                                      // the face under the front row (behind the wall)
  for (let k = 0; k < n; k++) { const [a, r] = FENCE[k], q0 = sprayPt(a, r + SEAT.gap, 0), q1 = sprayPt(a, r + SEAT.gap, SEAT.y0); fp.push(q0.x, 0, q0.z, q1.x, q1.y, q1.z); if (k) { const i = 2 * k; fi.push(i - 2, i - 1, i, i - 1, i + 1, i); } }
  const fg = new THREE.BufferGeometry(); fg.setAttribute("position", new THREE.Float32BufferAttribute(fp, 3)); fg.setIndex(fi); fg.computeVertexNormals();
  scene.add(new THREE.Mesh(fg, new THREE.MeshStandardMaterial({ color: 0x1d3a2a, roughness: 0.9, side: THREE.DoubleSide })));
}
// dugouts: the defense (home) on the third-base side, the hitters (away) on the first-base side; each faces the foul line
function makeDugout(cx, cz, yaw, accent) {
  const g = new THREE.Group(); g.position.set(cx, 0, cz); g.rotation.y = yaw;
  const M = (c, e = 0) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.85, emissive: e });
  const box = (w, h, d, x, y, z, m) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); b.position.set(x, y, z); b.castShadow = true; b.receiveShadow = true; g.add(b); return b; };
  box(64, 9, 1, 0, 4.5, -5.5, M(0x1a2232, 0x06080c));
  box(66, 0.9, 13, 0, 9.2, 0.2, M(0x202b3e));
  box(66, 1.3, 0.3, 0, 8.6, 6.7, M(accent));
  box(64, 3.2, 0.8, 0, 1.6, 5.4, M(0x1c2b4b));
  for (const sx of [-1, 1]) box(1, 9.6, 12, sx * 32.5, 4.8, 0.2, M(0x1a2232));
  box(54, 1.6, 2.2, 0, 0.8, -3.9, M(0x2c3646));
  const rail = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 64, 8), M(0x9aa3ad)); rail.rotation.z = Math.PI / 2; rail.position.set(0, 3.7, 5.4); g.add(rail);
  scene.add(g); g.updateMatrixWorld(true); return g;
}
const dg3 = makeDugout(-70.7, -7.1, 3 * Math.PI / 4, 0x1c2b4b), dg1 = makeDugout(70.7, -7.1, -3 * Math.PI / 4, 0xc4352d);
const dgAt = (g, x, z, y = 0) => g.localToWorld(v3(x, y, z));
const dgYaw = (g) => g.rotation.y;
const OD = v3(33, 0, 5);
for (const x of [OD.x, -OD.x]) { const m = new THREE.Mesh(new THREE.RingGeometry(2.3, 2.55, 40), chalk); m.rotation.x = -Math.PI / 2; m.position.set(x, 0.05, OD.z); scene.add(m); }


// ------------------------------------------------------------------ the cast
// the defense (white); the hitting team (dark): a right-handed batter and the runner on first
const pitcher = makePlayer(KIT.home, { glove: true });
const C = makePlayer(KIT.home, { glove: true, catcher: true });
const ump = makePlayer(KIT.ump, { catcher: true }), ump2 = makePlayer(KIT.ump);
const batter = makePlayer(KIT.away, { helmet: true, bat: true });
const R = makePlayer(KIT.away, { helmet: true });
const homeD = { b1: [62.4, -62.2], b2: [26, -116], ss: [-27, -114], b3: [-58, -76], lf: [-118, -262], cf: [0, -312], rf: [118, -262] };
const HD = {}; for (const [k, [x, z]] of Object.entries(homeD)) { HD[k] = makePlayer(KIT.home, { glove: true }); HD[k].root.position.set(x, 0, z); }
const B2F = HD.b2, B1F = HD.b1, SSF = HD.ss, RFF = HD.rf;
const bench = [];
for (const [g, kit, xs] of [[dg3, KIT.home, [-24, -12, -4, 9, 20]], [dg1, KIT.away, [-22, -9, 4, 16, 25]]]) for (const x of xs) {
  const p = makePlayer(kit); const q = dgAt(g, x, 3.4); p.root.position.copy(q); p.root.rotation.y = dgYaw(g); applyPose(p, { ...STAND, lean: 8, shL: [50, 12, 0], shR: [50, 12, 0], elL: 70, elR: 70, nod: -4 }); bench.push(p);
}
for (const p of [pitcher, C, ump, ump2, batter, R, ...Object.values(HD), ...bench]) scene.add(p.root);
const PLATE_C = v3(0, 0, -0.7);
const headTop = (P) => wpos(P.neck).add(v3(0, 1.4, 0));

// ------------------------------------------------------------------ the model (tools/physics.py)
const FB = PLAY.pitches.fb, GB = PLAY.gb, FL = FB.flight, TC = FB.t_contact;
function pathAt(path, t) {
  const u = (t - path.t0) * path.hz, n = path.p.length - 1;
  if (u <= 0) return V(path.p[0]);
  if (u >= n) return V(path.p[n]);
  const i = Math.floor(u), f = u - i, a = path.p[i], b = path.p[i + 1];
  return v3(lerp(a[0], b[0], f), lerp(a[1], b[1], f), lerp(a[2], b[2], f));
}
function walkAt(path, d) {
  for (let i = 1; i < path.length; i++) {
    const a = path[i - 1], b = path[i], L = a.distanceTo(b);
    if (d <= L || i === path.length - 1) return { p: a.clone().lerp(b, clamp(d / L, 0, 1)), yaw: Math.atan2(b.x - a.x, b.z - a.z), end: d >= L && i === path.length - 1 };
    d -= L;
  }
}
const pathLen = (path) => path.slice(1).reduce((s, q, i) => s + q.distanceTo(path[i]), 0);
const sprint = (t, vmax, tau) => (t <= 0 ? 0 : vmax * (t - tau * (1 - Math.exp(-t / tau))));
const arcAt = (p0, p1, T, u) => p0.clone().lerp(p1, clamp(u / T, 0, 1)).add(v3(0, 16.1 * clamp(u, 0, T) * (T - clamp(u, 0, T)), 0));   // a throw under gravity

// the timeline (play time; 0 = the pitch reaches the plate)
const T_MOVE = -1.3 - FL;                         // the pitcher's first move
const T_BRK = T_MOVE + 0.15;                      // the runner goes with the pitch
const L1 = B1.clone().lerp(B2, 11 / 90);          // his lead
const B2C = v3(2.6, 0, -125.4);                   // where the second baseman takes the throw at the bag
const RUN_HIT = [L1, v3(4.8, 0, -124.6), v3(-1.2, 0, -131.2), v3(-8.5, 0, -124.5), B3.clone().add(v3(1.0, 0, 0.4))];   // rounding second, on to third
const RUN_MISS = [L1, v3(1.4, 0, -125.6)];
const T_FIELD = GB.t_field, RFP = V(GB.field).setY(0);
const T_RFTHROW = T_FIELD + 0.45, T_RF = 0.95, T_RFC = T_RFTHROW + T_RF;   // the right fielder throws it in to second
const T_CREL = 0.72, T_CT = 1.1, T_CAT = T_CREL + T_CT;                    // the catcher: receives at 0, throws at 0.72, it's at second at 1.82
const L_MISS = pathLen(RUN_MISS);

// ------------------------------------------------------------------ poses
const C_SET = { ...CROUCH, shL: [62, 18, 0], elL: 40, shR: [20, 10, 0], elR: 50, nod: -18 };
const C_MID = { ...CROUCH, nod: -8, shL: [78, 12, 0], elL: 24, shR: [20, 10, 0], elR: 60 };
const C_POP = { ...STAND, drop: -0.4, lean: 14, twist: -40, shR: [-30, 80, 0], elR: 95, shL: [60, 20, 0], elL: 30, hipL: [30, 6], knL: 26, hipR: [10, 6], knR: 20 };
const C_THROW = { ...STAND, drop: -0.3, lean: 26, twist: 30, shR: [160, 20, 0], elR: 15, shL: [30, 34, 0], elL: 70, hipL: [36, 4], knL: 26, hipR: [-10, 6], knR: 30 };
const U_SET = { drop: -1.0, lean: 30, nod: -6, hipL: [52, 28], hipR: [52, 28], knL: 68, knR: 68, shL: [30, 20, 0], elL: 60, shR: [30, 20, 0], elR: 60 };
const U2_SET = { ...READY, shL: [20, 14, 0], shR: [20, 14, 0], elL: 40, elR: 40 };
const U_OUT = { ...STAND, lean: 6, shR: [150, 40, 0], elR: 105, shL: [10, 10, 0], elL: 20 };       // the out call: fist up
const P_SET = { lean: 4, look: 80, nod: 4, shL: [42, 8, 0], elL: 105, shR: [38, -4, 0], elR: 112, hipL: [4, 6], hipR: [4, 6], knL: 8, knR: 8 };
const P_LIFT = { lean: -4, look: 80, shL: [48, 8, 0], elL: 100, shR: [44, -4, 0], elR: 108, hipL: [100, 4], knL: 105, hipR: [6, 6], knR: 14, drop: -0.15 };
const P_STRIDE = { lean: 6, look: 40, drop: -0.6, twist: -50, shL: [80, 35, 0], elL: 25, shR: [-55, 80, 0], elR: 85, hipL: [52, 4], knL: 28, hipR: [-28, 6], knR: 38 };
const P_REL = { lean: 42, nod: 8, drop: -1.0, twist: 28, shL: [12, 32, 0], elL: 85, shR: [168, 22, 0], elR: 8, hipL: [72, 4], knL: 22, hipR: [-18, 6], knR: 92 };
const P_FOLLOW = { lean: 62, nod: 18, drop: -1.25, twist: 48, shL: [8, 38, 0], elL: 95, shR: [58, -24, 0], elR: 22, hipL: [82, 4], knL: 38, hipR: [34, 6], knR: 84 };
const BAT_SET = { drop: -0.35, lean: 18, look: 80, nod: -4, hipL: [22, 14], hipR: [22, 14], knL: 26, knR: 26, shL: [55, 6, 0], shR: [60, 34, 0], elL: 95, elR: 110, twist: 20 };
const BAT_LOAD = { ...BAT_SET, twist: 34, pelvisTwist: -14, hipL: [44, 10], knL: 52, hipR: [26, 18], knR: 34 };
const BAT_STRIDE = { ...BAT_LOAD, drop: -0.55, hipL: [14, 26], knL: 20, hipR: [30, 18], knR: 38, twist: 30 };
const BAT_HIT = { drop: -0.6, lean: 34, look: 64, nod: -18, twist: -20, pelvisTwist: 44, hipL: [24, 28], knL: 14, hipR: [18, 12], knR: 46, shL: [74, 0, 0], elL: 10, shR: [68, 18, 0], elR: 20 };   // inside-out, to the right side
const BAT_MISS = { ...BAT_HIT, lean: 30, nod: -6, look: 70, twist: -34, shL: [84, -6, 0], shR: [80, 12, 0] };                                // over the top of it
const BAT_FIN = { drop: -0.3, lean: 12, look: 20, twist: -70, pelvisTwist: 80, hipL: [16, 26], knL: 8, hipR: [6, 12], knR: 56, shL: [130, 10, 0], elL: 90, shR: [140, -40, 0], elR: 100 };
const F_FIELD = { drop: -1.0, lean: 58, nod: -25, hipL: [62, 12], hipR: [62, 12], knL: 74, knR: 74, shL: [72, 8, 0], elL: 12, shR: [64, -4, 0], elR: 20 };
const F_BACK = { ...STAND, twist: -30, shR: [-30, 80, 0], elR: 95, shL: [70, 20, 0], elL: 30, hipL: [30, 6], knL: 20 };
const F_REL = { ...STAND, lean: 22, twist: 30, shR: [160, 20, 0], elR: 15, shL: [30, 34, 0], elL: 70, hipL: [34, 4], knL: 24, hipR: [-10, 6], knR: 30 };
const B2_RECV = { ...READY, drop: -0.3, lean: 16, shL: [86, -6, 0], elL: 10, shR: [50, 0, 0], elR: 40 };
const B2_TAG = { drop: -1.1, lean: 48, nod: -26, hipL: [60, 14], hipR: [60, 14], knL: 72, knR: 72, shL: [52, -20, 0], elL: 8, shR: [40, 0, 0], elR: 40 };   // glove down on the sliding runner

// ------------------------------------------------------------------ the ball, arrows, the hole
function makeBall() {
  const m = new THREE.Mesh(new THREE.SphereGeometry(0.13, 16, 12), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffe9b0, emissiveIntensity: 0.7, roughness: 0.4 }));
  m.castShadow = true; scene.add(m);
  const gt = canvasTex(64, 64, (g, w) => { const gr = g.createRadialGradient(w / 2, w / 2, 0, w / 2, w / 2, w / 2); gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(0.35, "rgba(255,255,255,.55)"); gr.addColorStop(1, "rgba(255,255,255,0)"); g.fillStyle = gr; g.fillRect(0, 0, w, w); });
  const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: gt, color: 0xffd84d, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: false }));
  glow.scale.set(0.022, 0.022, 1); scene.add(glow);
  const trail = [];
  for (let i = 0; i < 22; i++) { const tr = new THREE.Mesh(new THREE.SphereGeometry(0.09 * (1 - i / 22) + 0.02, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffd84d, transparent: true, opacity: 0.4 * (1 - i / 22), depthWrite: false })); scene.add(tr); trail.push(tr); }
  return { m, glow, trail };
}
const BALL = makeBall();
function placeBall(pos, trailFn) {
  const vis = !!pos; BALL.m.visible = BALL.glow.visible = vis;
  if (vis) { BALL.m.position.copy(pos); BALL.glow.position.copy(pos); }
  for (let i = 0; i < BALL.trail.length; i++) { const p = vis && trailFn ? trailFn((i + 1) * 0.012) : null, tr = BALL.trail[i]; tr.visible = !!p; if (p) tr.position.copy(p); }
}
const flatMat = (c, op = 0.85) => new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: op, depthWrite: false, side: THREE.DoubleSide });
function groundArrow(pts, color, w = 1.2) {                                  // a flat arrow on the ground along pts, revealed with u
  const g = new THREE.Group(), m = flatMat(color, 0.85), n = pts.length - 1, segs = [];
  for (let i = 0; i < n; i++) { const a = pts[i], b = pts[i + 1], L = a.distanceTo(b); const s = new THREE.Mesh(new THREE.PlaneGeometry(w, L), m); s.rotation.x = -Math.PI / 2; s.rotation.z = -Math.atan2(b.x - a.x, -(b.z - a.z)); s.position.set((a.x + b.x) / 2, 0.1, (a.z + b.z) / 2); s.userData.u = (i + 1) / n; g.add(s); segs.push(s); }
  const a = pts[n - 1], b = pts[n], hs = new THREE.Shape([new THREE.Vector2(-w * 1.6, 0), new THREE.Vector2(w * 1.6, 0), new THREE.Vector2(0, w * 2.6)]);
  const head = new THREE.Mesh(new THREE.ShapeGeometry(hs), m); head.rotation.x = -Math.PI / 2; head.rotation.z = -Math.atan2(b.x - a.x, -(b.z - a.z)); head.position.set(b.x, 0.11, b.z); g.add(head);
  g.renderOrder = 6; g.children.forEach((c) => (c.renderOrder = 6)); g.visible = false; scene.add(g); g.userData = { segs, head, m }; return g;
}
const curve = (a, b, n = 16, bow = 0) => Array.from({ length: n + 1 }, (_, i) => { const u = i / n, p = a.clone().lerp(b, u); const d = b.clone().sub(a), nrm = v3(-d.z, 0, d.x).normalize(); return p.addScaledVector(nrm, bow * 4 * u * (1 - u)); });
const AR_RUN = groundArrow(curve(L1.clone().addScaledVector(B2.clone().sub(B1).normalize(), 4), B2.clone().lerp(B1, 6 / 90), 12), 0xffd84d, 1.1);
const AR_2B = groundArrow(curve(v3(homeD.b2[0], 0, homeD.b2[1]).add(v3(-2, 0, -2)), B2C.clone().add(v3(3, 0, 1.5)), 10, -2), 0xff6a3d, 1.0);
const AR_THIRD = groundArrow([B2.clone().add(v3(-6, 0, 4.5)), ...curve(B2.clone().lerp(B3, 0.12), B3.clone().lerp(B2, 0.1), 12)], 0xffd84d, 1.1);
function showArrow(g, u) { g.visible = u > 0; g.userData.segs.forEach((s) => (s.visible = s.userData.u <= u + 1e-6)); g.userData.head.visible = u >= 0.999; }
const GAP = (() => {                                                          // the hole on the right side, where the second baseman was
  const a0 = THREE.MathUtils.degToRad(6), a1 = THREE.MathUtils.degToRad(34), r0 = 92, r1 = 150, sh = new THREE.Shape();
  sh.moveTo(Math.sin(a0) * r0, Math.cos(a0) * r0);
  for (let i = 0; i <= 20; i++) { const a = lerp(a0, a1, i / 20); sh.lineTo(Math.sin(a) * r0, Math.cos(a) * r0); }
  for (let i = 20; i >= 0; i--) { const a = lerp(a0, a1, i / 20); sh.lineTo(Math.sin(a) * r1, Math.cos(a) * r1); }
  const m = new THREE.Mesh(new THREE.ShapeGeometry(sh), flatMat(0xffd84d, 0.3)); m.rotation.x = -Math.PI / 2; m.position.y = 0.09; m.renderOrder = 5; m.visible = false; scene.add(m); return m;
})();
const GAPC = v3(Math.sin(THREE.MathUtils.degToRad(20)) * 121, 0, -Math.cos(THREE.MathUtils.degToRad(20)) * 121);
const TRACE = (() => { const pts = []; for (let t = 0; t <= GB.t_field; t += 0.05) pts.push(pathAt(GB.path, t).setY(0.25)); const g = groundArrow(pts, 0xffffff, 0.5); g.userData.m.opacity = 0.75; return g; })();
const ringMat = (c) => new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: 0.9, depthWrite: false, side: THREE.DoubleSide });
const RINGS = { r: [0xffd84d, R], b2: [0xff6a3d, B2F] };
for (const k of Object.keys(RINGS)) { const m = new THREE.Mesh(new THREE.RingGeometry(1.8, 2.4, 36), ringMat(RINGS[k][0])); m.rotation.x = -Math.PI / 2; m.renderOrder = 7; m.visible = false; scene.add(m); RINGS[k].push(m); }

// ------------------------------------------------------------------ one frame
// s.play: "hit" (he swings, a ground ball through the hole, the runner goes first to third) or "miss" (he swings and
// misses; the catcher throws to second; the runner is tagged out). t = 0: the pitch reaches the plate.
function setScene(t, s) {
  const hit = s.play === "hit";
  // defense
  for (const [n, p] of Object.entries(HD)) { const [x, z] = homeD[n]; p.root.position.set(x, 0, z); p.root.rotation.y = Math.atan2(-x, -z); applyPose(p, t > T_MOVE + 0.9 ? READY : STAND); }
  B1F.root.rotation.y = yawTo(B1F.root.position, MOUND); applyPose(B1F, t < T_MOVE + 0.6 ? { ...READY, drop: -0.3, lean: 20, shL: [40, 30, 0], elL: 40 } : READY);   // holding the runner on
  if (t > T_MOVE + 0.6) B1F.root.position.copy(v3(...[homeD.b1[0]], 0, homeD.b1[1]).lerp(v3(56, 0, -72), smooth((t - T_MOVE - 0.6) / 0.8)));
  // the second baseman: covers second once the runner goes (that opens the hole), takes the throw
  const d0 = v3(homeD.b2[0], 0, homeD.b2[1]);
  if (t > T_BRK + 0.15) {
    const u = clamp((t - T_BRK - 0.15) / 1.35, 0, 1), p = d0.clone().lerp(B2C, smooth(u));
    B2F.root.position.copy(p); B2F.root.rotation.y = u < 1 ? yawTo(p, B2C) : yawTo(p, hit ? RFP : PLATE_C);
    let q = u < 1 ? runPose(((t - T_BRK) * 1.9) % 1, 0.85) : B2_RECV;
    if (!hit && t > T_CAT - 0.1) q = keyed([[T_CAT - 0.1, B2_RECV], [T_CAT + 0.18, B2_TAG], [T_CAT + 0.75, B2_TAG], [T_CAT + 1.2, { ...STAND, shL: [100, 10, 0], elL: 20 }]], t);
    if (hit && t > T_RFC - 0.3) q = B2_RECV;
    applyPose(B2F, q);
  }
  // the shortstop: backs up second
  if (t > T_BRK + 0.4) { const p = v3(homeD.ss[0], 0, homeD.ss[1]).lerp(v3(-6, 0, -138), smooth((t - T_BRK - 0.4) / 1.6)); SSF.root.position.copy(p); SSF.root.rotation.y = yawTo(p, B2); applyPose(SSF, t < T_BRK + 2 ? runPose(((t - T_BRK) * 1.8) % 1, 0.7) : READY); }
  // the right fielder: charges the ground ball, fields it, throws it in to second
  if (hit && t > TC + 0.3) {
    const st = v3(homeD.rf[0], 0, homeD.rf[1]), u = clamp((t - TC - 0.3) / (T_FIELD - TC - 0.3), 0, 1), p = st.clone().lerp(RFP.clone().add(v3(1.2, 0, -1.5)), u);
    RFF.root.position.copy(p); RFF.root.rotation.y = t < T_FIELD ? yawTo(p, RFP) : yawTo(p, B2C);
    applyPose(RFF, t < T_FIELD - 0.25 ? runPose(((t - TC) * 1.7) % 1, 0.9) : keyed([[T_FIELD - 0.25, F_FIELD], [T_FIELD + 0.15, F_BACK], [T_RFTHROW, F_REL], [T_RFTHROW + 0.5, STAND]], t));
    HD.cf.root.position.copy(v3(0, 0, -312).lerp(v3(40, 0, -232), smooth((t - 0.4) / 3))); HD.cf.root.rotation.y = yawTo(HD.cf.root.position, RFP); applyPose(HD.cf, t < 3.2 ? runPose((t * 1.5) % 1, 0.7) : READY);
  }
  // umpires
  ump.root.position.set(0.5, 0, 6.0); ump.root.rotation.y = Math.PI; applyPose(ump, t < 0.4 || !hit ? U_SET : { ...STAND, look: 20 });
  const u2p = v3(-14, 0, -110).lerp(v3(-14, 0, -128), smooth((t - T_BRK - 0.3) / 1.4)); ump2.root.position.copy(u2p); ump2.root.rotation.y = yawTo(u2p, hit ? PLATE_C : B2);
  applyPose(ump2, !hit && t > T_CAT + 0.35 ? keyed([[T_CAT + 0.35, U2_SET], [T_CAT + 0.6, U_OUT], [T_CAT + 1.6, U_OUT]], t) : U2_SET);
  // catcher
  C.root.position.set(0.15, 0, 3.0); C.root.rotation.y = Math.PI;
  applyPose(C, hit ? keyed([[-0.6, C_SET], [-0.05, C_MID], [0.3, C_MID], [0.9, { ...STAND, look: 30 }]], t) : keyed([[-0.6, C_SET], [-0.05, C_MID], [0.12, C_MID], [0.45, C_POP], [T_CREL, C_THROW], [T_CREL + 0.5, STAND]], t));
  if (!hit && t > 0.2) C.root.position.z = lerp(3.0, 1.8, smooth((t - 0.2) / 0.5));
  // pitcher
  const tr = t + FL, zp = lerp(-60.6, -57.6, smooth((tr + 0.45) / 0.5));
  pitcher.root.position.set(0, MOUND_H * (zp > -59 ? 0.6 : 1), zp); pitcher.root.rotation.y = lerp(-Math.PI / 2, 0, smooth((tr + 0.6) / 0.6));
  if (!hit && tr > 0.9) pitcher.root.rotation.y = lerp(0, Math.PI, smooth((tr - 0.9) / 0.5));
  applyPose(pitcher, keyed([[-1.3, P_SET], [-0.9, P_LIFT], [-0.35, P_STRIDE], [0, P_REL], [0.35, P_FOLLOW], [1.0, { ...READY, look: 0 }]], tr));
  // the batter: swings either way (that's his job on a hit-and-run); on contact he runs to first
  batter.root.position.set(-3.0, 0, -0.9); batter.root.rotation.y = Math.PI / 2; batter.bat.visible = true;
  let q = keyed([[TC - 0.8, BAT_SET], [TC - 0.5, BAT_LOAD], [TC - 0.22, BAT_STRIDE], [TC, hit ? BAT_HIT : BAT_MISS], [TC + 0.3, BAT_FIN], [TC + 0.9, { ...BAT_FIN, lean: 6, drop: -0.1 }]], t);
  if (hit && t > TC + 0.45) {
    const u = t - TC - 0.45, d = Math.min(92, sprint(u, 26, 0.8)), w = walkAt([v3(-3, 0, -0.9), v3(2.4, 0, -3.2), v3(66.5, 0, -61)], d);
    batter.root.position.copy(w.p); batter.root.rotation.y = w.yaw; batter.bat.visible = false;
    q = mixPose(q, w.end ? { ...STAND, look: -40 } : runPose((d / 11) % 1, 0.9), smooth(u / 0.25));
  } else if (!hit && t > TC + 0.9) { q = mixPose(q, { ...STAND, look: -60, shR: [20, 10, 0], elR: 40 }, smooth((t - TC - 0.9) / 0.5)); }
  applyPose(batter, q);
  // the runner: leads off, goes with the pitch; on contact he keeps going to third; on a miss he slides into second
  let rp = L1.clone(), ry = yawTo(L1, PLATE_C), rq = t < T_BRK - 0.6 ? { ...STAND, look: 0 } : LEAD_POSE;
  if (t > T_BRK) {
    const u = t - T_BRK;
    if (hit) {
      const d = Math.min(pathLen(RUN_HIT), sprint(u, 27, 0.7)), w = walkAt(RUN_HIT, d);
      rp = w.p; ry = w.yaw; rq = w.end ? { ...STAND, look: 40 } : runPose((d / 11.5) % 1, 1);
      if (w.end) ry = yawTo(rp, RFP);
      if (!w.end && t > TC + 0.15 && t < TC + 1.4) rq = { ...rq, look: 55, nod: -6 };        // a look in at the plate as he runs
    } else {
      const tSl = T_CAT - 0.12, d0s = sprint(tSl - T_BRK, 27, 0.7), vs = 26, dec = vs * vs / (2 * (L_MISS - d0s));   // he slides the last few feet
      let d = sprint(u, 27, 0.7), slide = 0;
      if (t > tSl) { const ts = Math.min(t - tSl, vs / dec); d = d0s + vs * ts - 0.5 * dec * ts * ts; slide = 1; }
      const w = walkAt(RUN_MISS, Math.min(d, L_MISS)); rp = w.p; ry = w.yaw;
      rq = slide ? mixPose(runPose((d / 11.5) % 1, 1), SLIDE_POSE, smooth((t - tSl) / 0.15)) : runPose((d / 11.5) % 1, 1);
    }
  } else if (t > T_BRK - 0.6) ry = yawTo(L1, MOUND);
  R.root.position.copy(rp); R.root.rotation.y = ry; applyPose(R, rq);
  // the ball
  const tRel = -FL - 0.02;
  let bp, trail = null;
  if (t < tRel) bp = wpos(pitcher.handR);
  else if (hit && t >= TC) {
    if (t < T_FIELD) { bp = pathAt(GB.path, t - TC); trail = (d) => (t - d >= TC ? pathAt(GB.path, t - d - TC) : pathAt(FB.path, t - d)); }
    else if (t < T_RFTHROW) bp = wpos(RFF.handR);
    else if (t < T_RFC) bp = arcAt(v3(RFP.x, 6.2, RFP.z), wpos(B2F.handL), T_RF, t - T_RFTHROW);
    else bp = wpos(B2F.handL);
  } else if (t < 0) { bp = pathAt(FB.path, t); trail = (d) => (t - d > FB.path.t0 ? pathAt(FB.path, t - d) : null); }
  else if (hit) bp = pathAt(FB.path, 0);
  else if (t < T_CREL - 0.25) bp = wpos(C.handL);
  else if (t < T_CREL) bp = wpos(C.handR);
  else if (t < T_CAT) { bp = arcAt(v3(0.3, 6.1, 2.2), wpos(B2F.handL), T_CT, t - T_CREL); trail = (d) => (t - d > T_CREL ? arcAt(v3(0.3, 6.1, 2.2), wpos(B2F.handL), T_CT, t - d - T_CREL) : null); }
  else bp = wpos(B2F.handL);
  placeBall(bp, trail);
  // graphics
  const rv = (k) => (s[k] ? clamp((t - s[k][0]) / (s[k][1] - s[k][0]), 0, 1) : 0);
  showArrow(AR_RUN, rv("arR")); showArrow(AR_2B, rv("ar2")); showArrow(AR_THIRD, rv("ar3")); showArrow(TRACE, rv("trace"));
  GAP.visible = !!s.gap && t > s.gap; GAP.material.opacity = 0.22 + 0.12 * Math.sin(t * 7);
  for (const [k, [, P, m]] of Object.entries(RINGS)) { m.visible = !!s.rings?.includes(k); if (m.visible) { const q2 = wpos(P.pelvis); m.position.set(q2.x, 0.12, q2.z); m.material.opacity = 0.7 + 0.25 * Math.sin(t * 9); } }
}

// ------------------------------------------------------------------ cameras
const cam = new THREE.PerspectiveCamera(40, W / H, 0.05, 3000);
function frame(c, pos, look, fov, aspect) { c.position.copy(pos); c.fov = fov; c.aspect = aspect; c.updateProjectionMatrix(); c.lookAt(look); }
const mixV = (a, b, u) => a.clone().lerp(b, u);
const pw = (v, vs, ts) => {
  if (v <= vs[0]) return ts[0];
  for (let i = 1; i < vs.length; i++) if (v <= vs[i]) return lerp(ts[i - 1], ts[i], (v - vs[i - 1]) / (vs[i] - vs[i - 1]));
  return ts.at(-1);
};
const zoom = (s, t, f0, f1) => (s.zt != null ? lerp(f0, f1, smooth((t - s.zt) / 0.14)) : f0);
const CAMS = {
  cfHigh: (u) => [mixV(v3(72, 7, -50), v3(68, 6.4, -56), easeIO(u)), v3(22, 3, -112), 40],                                  // behind the runner at first: he takes off
  batSide: (u, t, s) => [mixV(v3(5.5, 4.2, -11), v3(4.8, 4.0, -9.5), u), v3(-2.2, 3.2, -0.6), zoom(s, t, 46, 34)],          // in front of the batter: the swing
  wideHigh: (u) => [mixV(v3(10, 50, 50), v3(11, 46, 44), easeIO(u)), v3(19, 0, -58), 64],                                    // high behind the plate: the situation
  runner: (u) => [mixV(v3(78, 6.5, -46), v3(76, 6.2, -50), u), v3(18, 3.5, -104), 40],                                      // beyond first: the runner breaks, the pitcher delivers
  overhead: (u) => [mixV(v3(34, 120, -40), v3(32, 112, -46), u), v3(26, 0, -100), 52],                                   // above: the second baseman goes, the hole opens
  track: (u, t) => { const b = pathAt(GB.path, clamp(t - TC, 0, GB.t_field)); return [mixV(v3(10, 14, -84), v3(16, 16, -100), u), b.clone().lerp(v3(50, 0, -200), 0.3), 44]; },   // the ball through the hole
  third: (u) => [mixV(v3(-86, 8, -44), v3(-82, 7.5, -48), u), v3(-24, 3, -112), 40],                                       // beyond third: first to third
  throwCam: (u) => [mixV(v3(2, 17, 24), v3(2, 16, 20), u), v3(0, 3, -112), 26],                                            // high behind the plate: the throw to second
  tag2: (u) => [mixV(v3(16, 2.6, -114), v3(15, 2.6, -115), u), v3(0.5, 1.6, -126.5), 34],                                  // low, near second: the tag
  split: () => [v3(18, 52, 10), v3(-28, 0, -92), 50],
};
function shotAt(v) {
  const L = CC.shots.list;
  const s = L.find((x) => v < x.b) || L.at(-1);
  return { s, t: pw(v, s.vs, s.ts), u: clamp((v - s.a) / (s.b - s.a), 0, 1) };
}

// ------------------------------------------------------------------ DOM overlays fed from the same clock
const $ = (id) => document.getElementById(id);
const SPEEDS = { rt: "", replay: "Replay", slow: "Slow motion · ½ speed", freeze: "Freeze", none: "" };
const PINT = { runner: () => headTop(R), batter: () => headTop(batter), pitcher: () => headTop(pitcher), b2: () => headTop(B2F), gap: () => GAPC.clone().setY(4), ball: () => BALL.m.position.clone().add(v3(0, 3, 0)) };
function pin(id, p) {
  const el = $(id); if (!el || !p) return;
  const q = p.clone().project(cam);
  el.style.left = `${((q.x + 1) / 2 * W).toFixed(1)}px`; el.style.top = `${((1 - q.y) / 2 * H).toFixed(1)}px`;
}
function overlays(s, v) {
  if ($("spd")) { const sp = s.freeze != null && v >= s.freeze ? "freeze" : s.speed; $("spd").textContent = SPEEDS[sp] ?? ""; $("spd").style.opacity = SPEEDS[sp] ? 1 : 0; }
  if (s.mode !== "split") for (const [id, key] of CC.pins) pin(id, PINT[key]());
}
function renderAt(v) {
  const { s, t, u } = shotAt(v);
  renderer.setScissorTest(s.mode === "split");
  if (s.mode === "split") {                                       // the same play: contact (top), a miss (bottom)
    const c = CAMS.split(u, t, s);
    for (const [y, play] of [[H / 2, "hit"], [0, "miss"]]) {
      setScene(t, { ...s, play });
      frame(cam, c[0], c[1], c[2], W / (H / 2));
      renderer.setViewport(0, y, W, H / 2); renderer.setScissor(0, y, W, H / 2);
      BALL.glow.scale.set(0.02, 0.02, 1);
      renderer.render(scene, cam);
    }
  } else {
    setScene(t, s);
    const c = CAMS[s.cam](u, t, s);
    renderer.setViewport(0, 0, W, H);
    frame(cam, c[0], c[1], c[2], W / H);
    const g = c[2] < 16 ? 0.009 : 0.02; BALL.glow.scale.set(g, g, 1);
    renderer.render(scene, cam);
  }
  overlays(s, v);
}

let last = -1;
function seek(time) { if (time === last) return; last = time; renderAt(time); }
window.addEventListener("hf-seek", (e) => seek(e.detail.time));
window.__fieldRender = renderAt;
document.fonts.ready.then(() => seek(window.__hfThreeTime || 0));
seek(window.__hfThreeTime || 0);
