// "The infield fly rule": the field, dugouts, outfield seats, the players, in three.js.
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
// the defense (white); the hitters (dark): a right-handed batter, the bases loaded
const pitcher = makePlayer(KIT.home, { glove: true });
const C = makePlayer(KIT.home, { glove: true, catcher: true });
const ump = makePlayer(KIT.ump, { catcher: true });
const batter = makePlayer(KIT.away, { helmet: true, bat: true });
const R1 = makePlayer(KIT.away, { helmet: true }), R2 = makePlayer(KIT.away, { helmet: true }), R3 = makePlayer(KIT.away, { helmet: true });
const homeD = { b1: [61.8, -65.2], b2: [26, -116], ss: [-27, -114], b3: [-58, -76], lf: [-118, -262], cf: [0, -312], rf: [118, -262] };
const HD = {}; for (const [k, [x, z]] of Object.entries(homeD)) { HD[k] = makePlayer(KIT.home, { glove: true }); HD[k].root.position.set(x, 0, z); }
const SS = HD.ss, B2F = HD.b2, B1F = HD.b1;
const bench = [];
for (const [g, kit, xs] of [[dg3, KIT.home, [-24, -12, -4, 9, 20]], [dg1, KIT.away, [-22, -9, 4, 16, 25]]]) for (const x of xs) {
  const p = makePlayer(kit); const q = dgAt(g, x, 3.4); p.root.position.copy(q); p.root.rotation.y = dgYaw(g); applyPose(p, { ...STAND, lean: 8, shL: [50, 12, 0], shR: [50, 12, 0], elL: 70, elR: 70, nod: -4 }); bench.push(p);
}
for (const p of [pitcher, C, ump, batter, R1, R2, R3, ...Object.values(HD), ...bench]) scene.add(p.root);
const PLATE_C = v3(0, 0, -0.7);
const headTop = (P) => wpos(P.neck).add(v3(0, 1.4, 0));

// ------------------------------------------------------------------ the model (tools/physics.py)
const PP = PLAY.pitches.pop, PO = PLAY.pop, TL = PO.t_land, LAND = V(PO.land);
function pathAt(path, t) {
  const u = (t - path.t0) * path.hz, n = path.p.length - 1;
  if (u <= 0) return V(path.p[0]);
  if (u >= n) return V(path.p[n]);
  const i = Math.floor(u), f = u - i, a = path.p[i], b = path.p[i + 1];
  return v3(lerp(a[0], b[0], f), lerp(a[1], b[1], f), lerp(a[2], b[2], f));
}
const hopAt = (u) => { const k = clamp(u * 120, 0, PO.hop.length - 1.001), i = Math.floor(k); return V(PO.hop[i]).lerp(V(PO.hop[i + 1]), k - i); };
function walkAt(path, d) {
  for (let i = 1; i < path.length; i++) {
    const a = V(path[i - 1]), b = V(path[i]), L = a.distanceTo(b);
    if (d <= L || i === path.length - 1) return { p: a.clone().lerp(b, clamp(d / L, 0, 1)), yaw: Math.atan2(b.x - a.x, b.z - a.z) };
    d -= L;
  }
}
const sprint = (t, vmax, tau) => (t <= 0 ? 0 : vmax * (t - tau * (1 - Math.exp(-t / tau))));
const arcAt = (p0, p1, T, u) => p0.clone().lerp(p1, clamp(u / T, 0, 1)).add(v3(0, 16.1 * clamp(u, 0, T) * (T - clamp(u, 0, T)), 0));   // a throw under gravity

// the timeline (play time; 0 = contact)
const T_CALL = 1.2;                                   // the umpire declares it: arm up, while the ball is still climbing
const TF = TL + 0.36;                                 // the shortstop has it after the short hop
const TR1 = TF + 0.34, B2S = v3(1.8, 0, -125.6), B1S = v3(61.8, 0, -65.2);
const SSREL = () => wpos(SS.root).add(v3(0, 6.2, 0));
const T1 = 0.42, TC1 = TR1 + T1, TR2 = TC1 + 0.25, T2 = 0.8, TC2 = TR2 + T2;     // the cheap double play: short to second, second to first
const UD = LAND.clone().setY(0).normalize();
const SS0 = v3(...homeD.ss.slice(0, 1), 0, homeD.ss[1]), UNDER = LAND.clone().setY(0).addScaledVector(UD, 1.5), BACK = LAND.clone().setY(0).addScaledVector(UD, 2.7);
const R1L = B1.clone().lerp(B2, 9 / 90), R2L = B2.clone().lerp(B3, 11 / 90), R3L = B3.clone().lerp(HOME, 10 / 90).add(v3(-1.8, 0, 1.8));   // the runner on third leads off in foul territory
const BPATH = [[-3.0, 0, -0.9], [2.4, 0, -3.2], [63.0, 0, -63.0]];

// ------------------------------------------------------------------ poses
const C_SET = { ...CROUCH, shL: [62, 18, 0], elL: 40, shR: [20, 10, 0], elR: 50, nod: -18 };
const C_MID = { ...CROUCH, nod: -8, shL: [78, 12, 0], elL: 24, shR: [20, 10, 0], elR: 60 };
const UPLOOK = { ...STAND, nod: -45, shL: [20, 14, 0], elL: 50, shR: [10, 10, 0], elR: 20 };
const U_SET = { drop: -1.0, lean: 30, nod: -6, hipL: [52, 28], hipR: [52, 28], knL: 68, knR: 68, shL: [30, 20, 0], elL: 60, shR: [30, 20, 0], elR: 60 };
const U_IFLY = { ...STAND, nod: -38, shR: [178, 6, 0], elR: 4, shL: [6, 10, 0], elL: 15 };            // "Infield fly!": right arm straight up
const P_SET = { lean: 4, look: 80, nod: 4, shL: [42, 8, 0], elL: 105, shR: [38, -4, 0], elR: 112, hipL: [4, 6], hipR: [4, 6], knL: 8, knR: 8 };
const P_LIFT = { lean: -4, look: 80, shL: [48, 8, 0], elL: 100, shR: [44, -4, 0], elR: 108, hipL: [100, 4], knL: 105, hipR: [6, 6], knR: 14, drop: -0.15 };
const P_STRIDE = { lean: 6, look: 40, drop: -0.6, twist: -50, shL: [80, 35, 0], elL: 25, shR: [-55, 80, 0], elR: 85, hipL: [52, 4], knL: 28, hipR: [-28, 6], knR: 38 };
const P_REL = { lean: 42, nod: 8, drop: -1.0, twist: 28, shL: [12, 32, 0], elL: 85, shR: [168, 22, 0], elR: 8, hipL: [72, 4], knL: 22, hipR: [-18, 6], knR: 92 };
const P_FOLLOW = { lean: 62, nod: 18, drop: -1.25, twist: 48, shL: [8, 38, 0], elL: 95, shR: [58, -24, 0], elR: 22, hipL: [82, 4], knL: 38, hipR: [34, 6], knR: 84 };
const P_POINT = { ...STAND, nod: -40, shR: [150, -6, 0], elR: 8, shL: [30, 10, 0], elL: 70 };      // the pitcher points at it
const BAT_SET = { drop: -0.35, lean: 18, look: 80, nod: -4, hipL: [22, 14], hipR: [22, 14], knL: 26, knR: 26, shL: [55, 6, 0], shR: [60, 34, 0], elL: 95, elR: 110, twist: 20 };
const BAT_LOAD = { ...BAT_SET, twist: 34, pelvisTwist: -14, hipL: [44, 10], knL: 52, hipR: [26, 18], knR: 34 };
const BAT_STRIDE = { ...BAT_LOAD, drop: -0.55, hipL: [14, 26], knL: 20, hipR: [30, 18], knR: 38, twist: 30 };
const BAT_HIT = { drop: -0.6, lean: 34, look: 60, nod: -14, twist: -30, pelvisTwist: 50, hipL: [24, 28], knL: 14, hipR: [18, 12], knR: 46, shL: [70, -10, 0], elL: 14, shR: [64, 10, 0], elR: 26 };   // under it: jammed
const BAT_FIN = { drop: -0.3, lean: 10, look: 30, nod: -30, twist: -70, pelvisTwist: 80, hipL: [16, 26], knL: 8, hipR: [6, 12], knR: 56, shL: [120, 10, 0], elL: 90, shR: [130, -40, 0], elR: 100 };
const SS_CALL = { ...STAND, lean: -6, nod: -58, shL: [165, 8, 0], elL: 25, shR: [150, -12, 0], elR: 30 };        // "I got it": glove up under the ball
const SS_DECOY = { ...STAND, lean: 12, nod: -18, shL: [12, 22, 0], elL: 40, shR: [12, 16, 0], elR: 30, hipL: [10, 6], hipR: [10, 6], knL: 14, knR: 14 };   // pulls the glove away
const SS_FIELD = { drop: -1.0, lean: 58, nod: -25, hipL: [62, 12], hipR: [62, 12], knL: 74, knR: 74, shL: [72, 8, 0], elL: 12, shR: [64, -4, 0], elR: 20 };
const SS_HOLD = { ...STAND, lean: 6, shR: [70, 70, 0], elR: 115, shL: [34, 20, 0], elL: 70 };                  // ball up by his ear, looking the runner back
const SS_BACK = { ...STAND, twist: -30, shR: [-30, 80, 0], elR: 95, shL: [70, 20, 0], elL: 30, hipL: [30, 6], knL: 20 };
const SS_REL = { ...STAND, lean: 22, twist: 30, shR: [160, 20, 0], elR: 15, shL: [30, 34, 0], elL: 70, hipL: [34, 4], knL: 24, hipR: [-10, 6], knR: 30 };
const B2_CATCH = { ...READY, drop: -0.35, lean: 18, shL: [88, -8, 0], elL: 8, shR: [60, 0, 0], elR: 40 };
const B1_STRETCH = { ...READY, drop: -0.7, lean: 34, shL: [92, -6, 0], elL: 6, hipL: [56, 6], knL: 44, hipR: [-8, 6], knR: 8, shR: [40, 10, 0], elR: 40 };
const THROW = (t0, rel) => [[t0, SS_BACK], [rel, SS_REL], [rel + 0.4, { ...STAND, lean: 14 }]];

// ------------------------------------------------------------------ the ball
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
  BALL.m.position.copy(pos); BALL.glow.position.copy(pos);
  for (let i = 0; i < BALL.trail.length; i++) { const p = trailFn ? trailFn((i + 1) * 0.02) : null, tr = BALL.trail[i]; tr.visible = !!p; if (p) tr.position.copy(p); }
}
const ringMat = (c) => new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: 0.9, depthWrite: false, side: THREE.DoubleSide });
const MARKS = [0, 1, 2, 3].map(() => { const m = new THREE.Mesh(new THREE.RingGeometry(2.6, 3.6, 36), ringMat(0xff6a3d)); m.rotation.x = -Math.PI / 2; m.renderOrder = 5; m.visible = false; scene.add(m); return m; });   // the batter and runners, marked in the split screen
const SHADOW = new THREE.Mesh(new THREE.CircleGeometry(0.5, 20), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.35, depthWrite: false }));
SHADOW.rotation.x = -Math.PI / 2; SHADOW.renderOrder = 5; scene.add(SHADOW);                                                 // where it will come down

// ------------------------------------------------------------------ one frame
// s.play: "rule" (the umpire declares the infield fly) or "norule" (the same pop-up with no rule: the cheap double play)
function setScene(t, s) {
  const rule = s.play !== "norule";
  // defense
  for (const [n, p] of Object.entries(HD)) { const [x, z] = homeD[n]; p.root.position.set(x, 0, z); p.root.rotation.y = Math.atan2(-x, -z); applyPose(p, t < -0.3 ? STAND : t < 0.25 ? READY : { ...UPLOOK, look: 0 }); }
  for (const n of ["b3", "lf", "cf"]) HD[n].root.rotation.y = yawTo(HD[n].root.position, LAND);
  // the shortstop: drifts under it, calls for it, pulls the glove away, lets it drop, picks it up
  let sp = SS0.clone(), sq = READY;
  if (t > 0.3) {
    const u = smooth((t - 0.3) / 2.2); sp = SS0.clone().lerp(UNDER, u);
    sq = t < 2.5 ? mixPose(runPose(((t - 0.3) * 1.6) % 1, 0.45), { ...UPLOOK, look: 0 }, 0.5) : keyed([[2.5, { ...UPLOOK, look: 0 }], [3.0, SS_CALL], [TL - 0.6, SS_CALL], [TL - 0.3, SS_DECOY], [TL + 0.05, SS_DECOY], [TF - 0.05, SS_FIELD]], t);
    if (t > TL - 0.55) sp = UNDER.clone().lerp(BACK, smooth((t - TL + 0.55) / 0.3));
    if (t > TL + 0.05) sp = BACK.clone().lerp(LAND.clone().setY(0).addScaledVector(UD, 2.0), smooth((t - TL - 0.05) / 0.3));
  }
  let sy = yawTo(sp, PLATE_C);
  if (t > TF) {
    if (rule) { sq = keyed([[TF, SS_FIELD], [TF + 0.4, SS_HOLD]], t); sy = lerp(sy, yawTo(sp, B3), smooth((t - TF) / 0.4)); }
    else { sq = keyed([[TF, SS_FIELD], [TF + 0.25, SS_BACK], ...THROW(TF + 0.25, TR1).slice(1)], t); sy = lerp(sy, yawTo(sp, B2S) + 0.25, smooth((t - TF) / 0.25)); }
  }
  SS.root.position.copy(sp); SS.root.rotation.y = sy; applyPose(SS, sq);
  // second baseman: covers the bag (no rule) or drifts in and watches
  if (!rule && t > TL - 0.5) {
    const d0 = v3(...[homeD.b2[0]], 0, homeD.b2[1]), u = smooth((t - TL + 0.5) / 1.3), p = d0.clone().lerp(B2S, u);
    B2F.root.position.copy(p); B2F.root.rotation.y = u < 1 ? yawTo(p, B2S) : yawTo(p, SS.root.position);
    let q = u < 1 ? runPose(((t - TL) * 1.8) % 1, 0.9) : B2_CATCH;
    if (t > TC1) { B2F.root.rotation.y = lerp(yawTo(B2S, SS.root.position), yawTo(B2S, B1S), smooth((t - TC1) / 0.25)); q = keyed([[TC1, B2_CATCH], [TC1 + 0.12, SS_BACK], [TR2, SS_REL], [TR2 + 0.4, STAND]], t); }
    applyPose(B2F, q);
  } else if (t > 0.3) { const d0 = v3(homeD.b2[0], 0, homeD.b2[1]); B2F.root.position.copy(d0.lerp(v3(14, 0, -110), smooth((t - 0.3) / 2))); B2F.root.rotation.y = yawTo(B2F.root.position, LAND); applyPose(B2F, { ...UPLOOK, look: 0 }); }
  // first baseman: on the bag
  B1F.root.position.copy(B1S); B1F.root.rotation.y = yawTo(B1S, rule || t < TR2 ? LAND : B2S);
  applyPose(B1F, !rule && t > TR2 - 0.3 ? B1_STRETCH : t > 0.25 ? { ...UPLOOK, look: 0 } : READY);
  // umpire: the call, arm straight up, while the ball is in the air (only when the rule exists)
  ump.root.position.set(lerp(0.5, -1.5, smooth((t - 0.2) / 0.6)), 0, lerp(6.0, 4.5, smooth((t - 0.2) / 0.6))); ump.root.rotation.y = Math.PI;
  applyPose(ump, t < 0.15 ? U_SET : rule ? keyed([[0.15, U_SET], [0.6, UPLOOK], [T_CALL - 0.12, UPLOOK], [T_CALL + 0.08, U_IFLY], [TL + 1.6, U_IFLY], [TL + 2.0, STAND]], t) : keyed([[0.15, U_SET], [0.6, UPLOOK]], t));
  // catcher
  C.root.position.set(0.15, 0, 3.0); C.root.rotation.y = Math.PI;
  applyPose(C, keyed([[-0.6, C_SET], [-0.05, C_MID], [0.2, C_MID], [0.7, UPLOOK]], t));
  // pitcher
  const tr = t + PP.t_contact + PP.flight, zp = lerp(-60.6, -57.6, smooth((tr + 0.45) / 0.5));
  pitcher.root.position.set(0, MOUND_H * (zp > -59 ? 0.6 : 1), zp); pitcher.root.rotation.y = lerp(-Math.PI / 2, 0, smooth((tr + 0.6) / 0.6)) + (tr > 0.9 ? lerp(0, yawTo(pitcher.root.position, LAND), smooth((tr - 0.9) / 0.5)) : 0);
  applyPose(pitcher, keyed([[-1.3, P_SET], [-0.9, P_LIFT], [-0.35, P_STRIDE], [0, P_REL], [0.35, P_FOLLOW], [1.0, P_POINT], [TL, P_POINT], [TL + 0.5, STAND]], tr));
  // the batter: under it, a pop-up; he drops the bat and trots (no rule: he's thrown out; the rule: he's already out, he peels off)
  let q = keyed([[-0.8, BAT_SET], [-0.5, BAT_LOAD], [-0.22, BAT_STRIDE], [0, BAT_HIT], [0.3, BAT_FIN]], t), bp = V(BPATH[0]), by = Math.PI / 2;
  batter.bat.visible = t < 0.65;
  if (t > 0.7) {
    let d = sprint(t - 0.75, 13.5, 1.0);
    if (rule) d = Math.min(d, sprint(TL + 0.6 - 0.75, 13.5, 1.0) + Math.max(0, Math.min(t, TL + 1.4) - TL - 0.6) * 6.5);
    else if (t > TC2 + 0.3) d = sprint(TC2 + 0.3 - 0.75, 13.5, 1.0) + (t - TC2 - 0.3) * 5;
    const w = walkAt(BPATH, d); bp = w.p; by = w.yaw;
    const stopped = rule && t > TL + 1.4;
    if (stopped) { const off = t - TL - 1.4; by = lerp(by, yawTo(bp, dg1.position), smooth(off / 0.5)); bp = bp.clone().add(dg1.position.clone().sub(bp).setY(0).normalize().multiplyScalar(Math.max(0, off - 0.4) * 3.2)); }
    q = mixPose(q, stopped ? runPose((t * 1.1) % 1, 0.15) : runPose((d / 10) % 1, rule && t > TL + 0.6 ? 0.3 : 0.6), smooth((t - 0.7) / 0.3));
  }
  batter.root.position.copy(bp); batter.root.rotation.y = by; applyPose(batter, q);
  // runners: leads; frozen while it's up; they scramble back when he pulls the glove away; then...
  for (const [R, base, lead, next] of [[R1, B1, R1L, B2], [R2, B2, R2L, B3], [R3, B3, R3L, HOME]]) {
    let p = lead.clone(), yaw = yawTo(lead, PLATE_C), rq = t < 0.15 ? LEAD_POSE : { ...UPLOOK, look: 0 };
    if (t > TL - 0.55) { const u = smooth((t - TL + 0.55) / 0.75); p = lead.clone().lerp(base, u); yaw = yawTo(lead, base); rq = u < 1 ? runPose(((t - TL) * 2.2) % 1, 0.85) : { ...STAND, look: 0 }; if (u >= 1) yaw = yawTo(base, LAND); }
    if (t > TL + 0.1) {
      const dir = next.clone().sub(base).normalize();
      if (!rule) {                                           // forced: the batter is running, so both runners must go
        let d = sprint(t - TL - 0.1, 25, 0.7);
        if (R === R1 && t > TC1 + 0.3) d = sprint(TC1 + 0.3 - TL - 0.1, 25, 0.7) + (t - TC1 - 0.3) * 4;
        d = Math.min(d, 88.5); p = base.clone().addScaledVector(dir, d); yaw = yawTo(base, next);
        rq = d >= 88.5 ? STAND : runPose((d / 11) % 1, R === R1 && t > TC1 + 0.3 ? 0.25 : 0.95);
      } else if (R === R3) {                                 // the rule: no force; he breaks for home at his own risk, the shortstop looks him back
        const go = TL + 0.05, turn = TF + 0.7, dGo = sprint(Math.min(t, turn) - go, 24, 0.6);
        const d = t < turn ? dGo : dGo * (1 - smooth((t - turn) / 1.1));
        p = base.clone().addScaledVector(dir, d); yaw = t < turn + 0.15 ? yawTo(base, next) : yawTo(next, base);
        rq = t < turn ? runPose((d / 10) % 1, 0.8) : d > 0.6 ? runPose(((t - turn) * 2) % 1, 0.7) : { ...STAND, look: 0 };
        if (d <= 0.6 && t > turn) yaw = yawTo(base, SS.root.position);
      }
    }
    R.root.position.copy(p); R.root.rotation.y = yaw; applyPose(R, rq);
  }
  // the ball
  const tRel = -(PP.flight + PP.t_contact) - 0.02;
  let bpos, trail = null;
  if (t < tRel) bpos = wpos(pitcher.handR);
  else if (t < 0) bpos = pathAt(PP.path, t + PP.t_contact);
  else if (t < TL) { bpos = pathAt(PO.path, t); trail = (d) => (t - d > 0 ? pathAt(PO.path, t - d) : null); }
  else if (t < TF - 0.08) bpos = hopAt(t - TL);
  else if (t < TF) bpos = hopAt(TF - 0.08 - TL).lerp(wpos(SS.handL), smooth((t - TF + 0.08) / 0.08));
  else if (rule || t < TR1) bpos = t < TF + 0.2 ? wpos(SS.handL) : wpos(SS.handR);
  else if (t < TC1) bpos = arcAt(SSREL(), wpos(B2F.handL), T1, t - TR1);
  else if (t < TR2) bpos = t < TC1 + 0.12 ? wpos(B2F.handL) : wpos(B2F.handR);
  else if (t < TC2) bpos = arcAt(v3(2.2, 6.3, -125.2), wpos(B1F.handL), T2, t - TR2);
  else bpos = wpos(B1F.handL);
  placeBall(bpos, trail);
  [batter, R1, R2, R3].forEach((P, i) => { const q = wpos(P.pelvis); MARKS[i].position.set(q.x, 0.08, q.z); MARKS[i].visible = !!s.marks && !(i === 0 && s.marks === "run"); });
  SHADOW.visible = t > 1.0 && t < TL; SHADOW.position.set(LAND.x, 0.06, LAND.z); SHADOW.material.opacity = 0.15 + 0.3 * smooth((t - 1) / (TL - 1));
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
const popAt = (t) => pathAt(PO.path, clamp(t, 0, TL));
const zoom = (s, t, f0, f1) => (s.zt != null ? lerp(f0, f1, smooth((t - s.zt) / 0.14)) : f0);
const CAMS = {
  plateHi: (u) => [mixV(v3(-5, 13.5, 27), v3(-4.6, 12.2, 22), easeIO(u)), v3(-10, 5, -45), 50],                            // high behind the plate: runners on 1st and 2nd, the swing
  rise: (u, t) => { const b = popAt(t); return [mixV(v3(7, 3.2, 14), v3(6.4, 3.0, 12.5), u), b.clone().lerp(v3(-6, 2, -40), 0.5), 66]; },   // low behind the plate: it climbs over the infield
  under: (u) => [mixV(v3(-14, 3.0, -84), v3(-15, 2.8, -86.5), easeIO(u)), v3(-24, 7, -104), 40],                       // in front of the shortstop: "I got it"
  drop: (u, t, s) => { const z = s.zt != null ? smooth((t - s.zt) / 0.14) : 0; return [mixV(v3(-38, 7, -96), v3(-37, 6.8, -95), u), v3(-4, 2.5, -114).lerp(LAND.clone().setY(2.2), 0.55 * z), lerp(42, 30, z)]; },   // behind the shortstop: the drop, the runner at second
  mound: (u, t) => { const b = popAt(t); return [mixV(v3(4, 1.6, -40), v3(3.6, 1.6, -37), u), v3(0, 3, 0).lerp(b, 0.35), 46]; },   // the replay: low in front of the mound
  umpCU: (u, t, s) => [mixV(v3(-8.5, 4.4, -1.5), v3(-8, 4.5, -0.8), easeIO(u)), wpos(ump.neck).add(v3(0, 1.8, 0)), zoom(s, t, 42, 36)],   // third-base side of the plate umpire
  wideAir: (u, t) => [mixV(v3(34, 30, 30), v3(30, 28, 26), u), v3(-6, 14, -70), 54],
  loaded: (u) => [mixV(v3(0, 44, 42), v3(0, 41, 37), u), v3(0, 0, -60), 55],                                              // high behind the plate: bases loaded
  dpWide: (u) => [mixV(v3(30, 75, 40), v3(28, 72, 36), u), v3(20, 0, -85), 52],                                           // without the rule: the drop, the force at 2nd, the relay to 1st
  split: () => [v3(34, 58, 4), v3(28, 0, -92), 44],
  top: (u) => { const a = lerp(0.1, -0.1, u); return [v3(Math.sin(a) * 30, 250, -64 + Math.cos(a) * 30), v3(0, 0, -64), 40]; },
  dirt: (u) => [mixV(v3(-30, 1.5, -92), v3(-29, 1.5, -93), u), v3(-22, 2.4, -104), 42],                                  // on the dirt: it falls in
  runners: (u) => [mixV(v3(-16, 6, -122), v3(-17, 5.8, -120), u), v3(-50, 3, -58), 44],                                 // behind the shortstop: the runner on third breaks for home
  final: (u) => [mixV(v3(44, 42, 28), v3(42, 39, 24), easeIO(u)), v3(12, 0, -78), 56],
};
function shotAt(v) {
  const L = CC.shots.list;
  const s = L.find((x) => v < x.b) || L.at(-1);
  return { s, t: pw(v, s.vs, s.ts), u: clamp((v - s.a) / (s.b - s.a), 0, 1) };
}

// ------------------------------------------------------------------ DOM overlays fed from the same clock
const $ = (id) => document.getElementById(id);
const SPEEDS = { rt: "", replay: "Replay · ½ speed", slow: "Slow motion · ½ speed", freeze: "Freeze", none: "" };
const PINT = { batter: () => headTop(batter), ump: () => headTop(ump).add(v3(0, 2.4, 0)), ss: () => headTop(SS), r2: () => headTop(R2), r3: () => headTop(R3) };
function pin(id, p) {
  const el = $(id); if (!el || !p) return;
  const q = p.clone().project(cam);
  el.style.left = `${((q.x + 1) / 2 * W).toFixed(1)}px`; el.style.top = `${((1 - q.y) / 2 * H).toFixed(1)}px`;
}
function overlays(s, v) {
  if ($("spd")) { const sp = s.freeze != null && v >= s.freeze ? "freeze" : s.speed; $("spd").textContent = SPEEDS[sp] ?? ""; $("spd").style.opacity = SPEEDS[sp] ? 1 : 0; }
  for (const [id, key] of CC.pins) pin(id, PINT[key]());
}
function renderAt(v) {
  const { s, t, u } = shotAt(v);
  const c = CAMS[s.cam](u, t, s);
  renderer.setScissorTest(s.mode === "split");
  if (s.mode === "split") {                                       // the same pop-up: no rule (top), the rule (bottom)
    for (const [y, play] of [[H / 2, "norule"], [0, "rule"]]) {
      setScene(t, { ...s, play });
      frame(cam, c[0], c[1], c[2], W / (H / 2));
      renderer.setViewport(0, y, W, H / 2); renderer.setScissor(0, y, W, H / 2);
      BALL.glow.scale.set(0.02, 0.02, 1);
      renderer.render(scene, cam);
    }
  } else {
    setScene(t, s);
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
