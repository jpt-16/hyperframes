// "Reading fly balls": the field, the outfielders and five simulated fly balls, in three.js.
// Everything is a pure function of HyperFrames time (hf-seek), so each frame is exact and repeatable.
// Units are feet. Home plate's back point is the origin, +x points toward first base's side, -z toward center field.
// The fly balls and the fielders' routes come from tools/physics.py via window.__PLAY (a model, not a measurement).
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
key.position.set(-160, 300, -60); key.target.position.set(0, 0, -210);
key.castShadow = true; key.shadow.mapSize.set(4096, 4096);
Object.assign(key.shadow.camera, { left: -260, right: 260, top: 260, bottom: -260, near: 50, far: 900 });
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
const lf = makePlayer(KIT.home, { glove: true }), cf = makePlayer(KIT.home, { glove: true }), rf = makePlayer(KIT.home, { glove: true });
const cfAlt = makePlayer(KIT.home, { glove: true });         // a second center fielder for the split screen / ghost
const batter = makePlayer(KIT.away, { helmet: true, bat: true });
const pitcher = makePlayer(KIT.home, { glove: true }), catcher = makePlayer(KIT.home, { glove: true, catcher: true }), umpH = makePlayer(KIT.ump, { catcher: true });
const infield = [[52, -78], [24, -128], [-26, -122], [-56, -74]].map(([x, z]) => { const p = makePlayer(KIT.home, { glove: true }); p.root.position.set(x, 0, z); p.root.rotation.y = Math.atan2(-x, -z); return p; });
for (const p of [lf, cf, rf, cfAlt, batter, pitcher, catcher, umpH, ...infield]) scene.add(p.root);
const OF = { LF: lf, CF: cf, RF: rf };
const ghostMats = [];
cfAlt.root.traverse((o) => { if (o.isMesh) { o.material = o.material.clone(); ghostMats.push(o.material); } });
function ghost(on) { for (const m of ghostMats) { m.transparent = on; m.opacity = on ? 0.45 : 1; m.depthWrite = !on; m.emissive?.setHex(on ? 0x6a2008 : 0x000000); } }

// ------------------------------------------------------------------ the model (tools/physics.py)
const V = (a) => v3(a[0], a[1], a[2]);
const A = PLAY.assume, HZ = PLAY.hz, BALLS = PLAY.balls;
function pathAt(path, t) {
  const u = t * path.hz, n = path.p.length - 1;
  if (u <= 0) return V(path.p[0]);
  if (u >= n) return V(path.p[n]);
  const i = Math.floor(u), f = u - i, a = path.p[i], b = path.p[i + 1];
  return v3(lerp(a[0], b[0], f), lerp(a[1], b[1], f), lerp(a[2], b[2], f));
}
const series = (arr, t) => { const u = clamp(t, 0, (arr.length - 1) / HZ) * HZ, i = Math.min(Math.floor(u), arr.length - 2); return lerp(arr[i], arr[i + 1], u - i); };
const routeAt = (R, t) => v3(series(R.x, t), 0, series(R.z, t));
const handPos = (h) => { h.updateWorldMatrix(true, false); return h.getWorldPosition(new THREE.Vector3()); };

// ------------------------------------------------------------------ poses
const OF_READY = { drop: -0.45, lean: 22, nod: -10, hipL: [30, 16], hipR: [30, 16], knL: 36, knR: 36, shL: [30, 14, 0], shR: [30, 14, 0], elL: 40, elR: 40 };
const CATCH_UP = { lean: 2, nod: -34, shL: [168, 12, 0], elL: 12, shR: [150, -6, 0], elR: 35, hipL: [14, 6], hipR: [-6, 6], knL: 20, knR: 10 };
const SETTLE = { lean: 0, nod: -40, shL: [120, 14, 0], elL: 30, shR: [60, 10, 0], elR: 50, hipL: [8, 6], hipR: [8, 6], knL: 12, knR: 12 };
const BAT_SET = { drop: -0.35, lean: 18, look: 80, nod: -4, hipL: [22, 14], hipR: [22, 14], knL: 26, knR: 26, shL: [55, 6, 0], shR: [60, 34, 0], elL: 95, elR: 110, twist: 20 };
const BAT_LOAD = { ...BAT_SET, twist: 34, pelvisTwist: -10, hipL: [36, 22], knL: 40 };
const BAT_HIT = { drop: -0.5, lean: 24, look: 50, nod: -10, twist: -40, pelvisTwist: 60, hipL: [24, 28], knL: 10, hipR: [18, 12], knR: 46, shL: [86, -10, 0], elL: 10, shR: [80, 10, 0], elR: 20 };
const BAT_FIN = { drop: -0.3, lean: 10, look: 20, twist: -80, pelvisTwist: 90, hipL: [16, 26], knL: 8, hipR: [6, 12], knR: 56, shL: [140, 10, 0], elL: 100, shR: [150, -40, 0], elR: 110 };
const P_SET = { lean: 4, look: 0, shL: [42, 8, 0], elL: 105, shR: [38, -4, 0], elR: 112, hipL: [4, 6], hipR: [4, 6], knL: 8, knR: 8 };
const P_FOLLOW = { lean: 50, nod: 14, drop: -1.1, twist: 40, shL: [8, 38, 0], elL: 95, shR: [58, -24, 0], elR: 22, hipL: [82, 4], knL: 38, hipR: [34, 6], knR: 84 };

// a fielder on one of the model's routes. o: { ball, route ("ok" | "bad" | "naive" | "help"), noCatch }
function setFielder(P, o, t) {
  const B = BALLS[o.ball], R = B.routes[o.route];
  const pos = routeAt(R, t), sp = series(R.v, t);
  P.root.position.copy(pos);
  const ball = pathAt(B.path, Math.min(t, B.t_catch));
  const toBall = Math.atan2(ball.x - pos.x, ball.z - pos.z);
  const ahead = routeAt(R, t + 0.08).sub(routeAt(R, t - 0.08));
  const yawRun = ahead.length() > 0.2 ? Math.atan2(ahead.x, ahead.z) : toBall;
  const yaw = lerp(toBall, toBall + (((yawRun - toBall + Math.PI * 3) % (Math.PI * 2)) - Math.PI), clamp((sp - 4) / 6, 0, 1));
  P.root.rotation.y = yaw;
  let rel = ((toBall - yaw + Math.PI * 3) % (Math.PI * 2)) - Math.PI;              // head turns to keep the ball in sight
  const look = clamp(rel * 57.3, -105, 105);
  const elev = Math.atan2(ball.y - 5.5, Math.hypot(ball.x - pos.x, ball.z - pos.z)) * 57.3;
  const catches = o.route !== "bad" && o.route !== "naive" && !o.noCatch && o.route !== "help";
  let q;
  if (t < A.react) q = OF_READY;
  else q = runPose(series(R.ph, t) % 1, clamp(sp / A.vmax, 0.15, 1));
  if (sp < 6 && t > A.react) q = mixPose(q, SETTLE, smooth((6 - sp) / 6));
  if (catches) q = mixPose(q, CATCH_UP, smooth(1 - Math.abs(t - B.t_catch) / 0.45) * (t < B.t_catch + 0.5 ? 1 : 0) + (t >= B.t_catch + 0.5 ? smooth(1 - (t - B.t_catch - 0.5) / 0.8) : 0));
  applyPose(P, { ...q, look: (q.look ?? 0) + look * 0.9, nod: Math.min(q.nod ?? 0, -clamp(elev, 0, 55) * 0.8) });
}

// ------------------------------------------------------------------ the ball, its path, the marks on the field
function makeBall(glowHex) {
  const m = new THREE.Mesh(new THREE.SphereGeometry(0.2, 16, 12), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffe9b0, emissiveIntensity: 0.7, roughness: 0.4 }));
  m.castShadow = true; scene.add(m);
  const gt = canvasTex(64, 64, (g, w) => { const gr = g.createRadialGradient(w / 2, w / 2, 0, w / 2, w / 2, w / 2); gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(0.35, "rgba(255,255,255,.55)"); gr.addColorStop(1, "rgba(255,255,255,0)"); g.fillStyle = gr; g.fillRect(0, 0, w, w); });
  const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: gt, color: glowHex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: false }));
  glow.scale.set(0.03, 0.03, 1); scene.add(glow);
  const shadow = new THREE.Mesh(new THREE.CircleGeometry(0.9, 20), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.35, depthWrite: false }));
  shadow.rotation.x = -Math.PI / 2; scene.add(shadow);
  return { m, glow, shadow };
}
const BALL = makeBall(0xffd84d), BALL2 = makeBall(0xffffff);
function placeBall(B, pos, show = true) {
  B.m.visible = B.glow.visible = B.shadow.visible = show;
  B.m.position.copy(pos); B.glow.position.copy(pos); B.shadow.position.set(pos.x, 0.06, pos.z); B.shadow.material.opacity = clamp(0.4 - pos.y / 200, 0.12, 0.4);
}
function tube(points, color, width, opacity = 0.9, dashed = false) {
  const g = new THREE.Group();
  for (let i = 0; i < points.length - 1; i++) {
    if (dashed && i % 2) continue;
    const a = points[i], b = points[i + 1], len = a.distanceTo(b);
    const m = new THREE.Mesh(new THREE.BoxGeometry(width, width, len), new THREE.MeshBasicMaterial({ color, transparent: true, opacity, depthWrite: false }));
    m.position.set((a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2); m.lookAt(b.x, b.y, b.z); m.userData.u = (i + 1) / (points.length - 1); g.add(m);
  }
  g.visible = false; scene.add(g); return g;
}
function groundLine(points, color, width, opacity = 0.9, dashed = false) {
  const g = new THREE.Group();
  for (let i = 0; i < points.length - 1; i++) {
    if (dashed && i % 2) continue;
    const a = points[i], b = points[i + 1], len = a.distanceTo(b);
    if (len < 0.05) { const m = new THREE.Object3D(); m.userData.u = (i + 1) / (points.length - 1); g.add(m); continue; }
    const m = new THREE.Mesh(new THREE.PlaneGeometry(width, len + 0.1), new THREE.MeshBasicMaterial({ color, transparent: true, opacity, depthWrite: false }));
    m.rotation.x = -Math.PI / 2; m.rotation.z = -Math.atan2(b.x - a.x, -(b.z - a.z)); m.position.set((a.x + b.x) / 2, 0.12, (a.z + b.z) / 2);
    m.userData.u = (i + 1) / (points.length - 1); g.add(m);
  }
  g.visible = false; scene.add(g); return g;
}
function reveal(g, u) { g.visible = u > 0; for (const m of g.children) m.visible = m.userData.u <= u + 1e-6; }
const ringMesh = (r0, r1, color, opacity = 0.95, dashed = false) => {
  const g = new THREE.Group();
  if (!dashed) { const m = new THREE.Mesh(new THREE.RingGeometry(r0, r1, 64), new THREE.MeshBasicMaterial({ color, transparent: true, opacity, depthWrite: false, side: THREE.DoubleSide })); m.rotation.x = -Math.PI / 2; g.add(m); }
  else for (let k = 0; k < 16; k++) { const m = new THREE.Mesh(new THREE.RingGeometry(r0, r1, 8, 1, k * Math.PI / 8, Math.PI / 14), new THREE.MeshBasicMaterial({ color, transparent: true, opacity, depthWrite: false, side: THREE.DoubleSide })); m.rotation.x = -Math.PI / 2; g.add(m); }
  g.visible = false; scene.add(g); return g;
};
const MARKS = {};
for (const [name, B] of Object.entries(BALLS)) {
  const n = 120, pts = Array.from({ length: n + 1 }, (_, i) => pathAt(B.path, B.path.dur * i / n));
  const R = (key, color, w, op, dashed) => { const r = B.routes[key]; const N = r.x.length, step = 6; const p = []; for (let i = 0; i < N; i += step) p.push(v3(r.x[i], 0, r.z[i])); return groundLine(p, color, w, op, dashed); };
  MARKS[name] = {
    path: tube(pts, 0xffd84d, 0.55, 0.85),
    straight: B.path_straight ? tube(Array.from({ length: n + 1 }, (_, i) => pathAt(B.path_straight, B.path_straight.dur * i / n)), 0xf4f6f8, 0.45, 0.6, true) : null,
    land: ringMesh(3.2, 4.4, 0xffd84d), landDot: ringMesh(0, 1.1, 0xffd84d),
    naive: ringMesh(3.2, 4.2, 0xf4f6f8, 0.85, true),
    ok: R("ok", 0x56d1ff, 1.3, 0.9), bad: R("bad", 0xff6a3d, 1.3, 0.9), naiveR: R("naive", 0xff6a3d, 1.2, 0.85, true),
    help: B.routes.help ? R("help", 0xf4f6f8, 1.1, 0.7) : null,
  };
  const c = V(B.catch), nv = V(B.naive);
  for (const k of ["land", "landDot"]) MARKS[name][k].position.set(c.x, 0.14, c.z);
  MARKS[name].naive.position.set(nv.x, 0.13, nv.z);
}
const START_RINGS = {};
for (const k of ["LF", "CF", "RF"]) { START_RINGS[k] = ringMesh(2.6, 3.4, 0xf4f6f8, 0.9); const p = V(PLAY.start[k]); START_RINGS[k].position.set(p.x, 0.13, p.z); }
function labelSprite(text, color = "#ffffff", w = 26) {
  const t = canvasTex(512, 200, (g, W_, h) => { g.fillStyle = "rgba(6,10,18,0.82)"; g.beginPath(); g.roundRect(6, 6, W_ - 12, h - 12, 40); g.fill(); g.fillStyle = color; g.font = "800 132px 'Barlow Condensed', sans-serif"; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(text, W_ / 2, h / 2 + 6); });
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, depthTest: false, transparent: true })); sp.scale.set(w, w * 200 / 512, 1); sp.renderOrder = 10; sp.visible = false; scene.add(sp); return sp;
}
const POS_TAGS = {};
document.fonts.load("800 132px 'Barlow Condensed'").then(() => {
  for (const k of ["LF", "CF", "RF"]) { POS_TAGS[k] = labelSprite(k); const p = V(PLAY.start[k]); POS_TAGS[k].position.set(p.x, 22, p.z); }
  last = -1; seek(window.__hfThreeTime || 0);
});
// spin indicator: a thin ring around the ball, square to its spin axis, with a small arrow head
const spinRing = new THREE.Group();
{ const tor = new THREE.Mesh(new THREE.TorusGeometry(0.75, 0.035, 8, 48), new THREE.MeshBasicMaterial({ color: 0x56d1ff, transparent: true, opacity: 0.95 }));
  const head = new THREE.Mesh(new THREE.ConeGeometry(0.12, 0.3, 10), new THREE.MeshBasicMaterial({ color: 0x56d1ff })); head.position.set(0.75, 0, 0); head.rotation.x = Math.PI / 2;
  const axis = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 2.2, 6), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.7 })); axis.rotation.x = Math.PI / 2;
  const spinner = new THREE.Group(); spinner.add(tor, head); spinRing.add(spinner, axis); spinRing.userData.spinner = spinner; spinRing.visible = false; scene.add(spinRing); }
// the hitter's spray tendency: a soft wedge toward the opposite field
const wedge = new THREE.Mesh(new THREE.RingGeometry(150, 300, 32, 1, Math.PI / 2 - 0.80, 0.42), new THREE.MeshBasicMaterial({ color: 0xff6a3d, transparent: true, opacity: 0.42, depthWrite: false, side: THREE.DoubleSide }));
wedge.rotation.x = -Math.PI / 2; wedge.position.y = 0.1; wedge.visible = false; scene.add(wedge);

// ------------------------------------------------------------------ set the scene at play time t (s since contact)
// s: { ball, mode: "single" | "split", fielders: [[role, route, (ghost)]], show: { path, land, naive, routes: [...], start, spin, straight, wedge } }
function hideMarks() { for (const M of Object.values(MARKS)) for (const g of Object.values(M)) if (g) g.visible = false; for (const g of Object.values(START_RINGS)) g.visible = false; spinRing.visible = false; wedge.visible = false; }
function setScene(t, s, half) {
  const ballName = half?.ball ?? s.ball, B = BALLS[ballName];
  // everyone at their spots
  for (const [k, P] of Object.entries(OF)) { const p = V(PLAY.start[k]); P.root.position.copy(p); P.root.rotation.y = Math.atan2(-p.x, -p.z); applyPose(P, t > -0.3 ? OF_READY : STAND); P.root.visible = true; }
  cfAlt.root.visible = false; ghost(false);
  const roster = half?.fielders ?? s.fielders ?? [];
  for (const [role, route, gh] of roster) {
    const P = gh ? cfAlt : OF[role];
    if (gh) { cfAlt.root.visible = true; ghost(true); }
    setFielder(P, { ball: ballName, route }, t);
  }
  // batter, pitcher, catcher, umpire
  batter.root.position.set(-3.0, 0, -0.9); batter.root.rotation.y = Math.PI / 2;
  applyPose(batter, keyed([[-0.6, BAT_SET], [-0.18, BAT_LOAD], [0, BAT_HIT], [0.35, BAT_FIN]], t));
  pitcher.root.position.set(0, MOUND_H, -56.5); pitcher.root.rotation.y = 0; applyPose(pitcher, keyed([[-0.9, P_SET], [-0.4, P_SET], [-0.05, P_FOLLOW], [0.8, { ...READY, look: 0 }]], t));
  catcher.root.position.set(0.15, 0, 3.6); catcher.root.rotation.y = Math.PI; applyPose(catcher, { ...CROUCH, shL: [70, 14, 0], elL: 25 });
  umpH.root.position.set(0.5, 0, 6.0); umpH.root.rotation.y = Math.PI; applyPose(umpH, { drop: -1.0, lean: 30, nod: -6, hipL: [52, 28], hipR: [52, 28], knL: 68, knR: 68 });
  for (const p of infield) applyPose(p, t > -0.3 ? READY : STAND);
  // the ball: pitch -> contact -> flight -> glove
  let bp;
  if (t < -0.42) bp = handPos(pitcher.handR);
  else if (t < 0) bp = v3(-1.9, 6.0, -54).lerp(V(PLAY.contact), (t + 0.42) / 0.42);
  else if (t < B.t_catch || !(s.catchBy ?? true)) bp = pathAt(B.path, t);
  else { const catcherP = roster.find((r) => !r[2] && r[1] !== "bad" && r[1] !== "naive" && r[1] !== "help"); bp = catcherP ? handPos(OF[catcherP[0]].handL) : pathAt(B.path, t); }
  placeBall(BALL, bp, true);
  placeBall(BALL2, v3(0, -50, 0), false);
  // marks
  hideMarks();
  const sh = s.show || {}, M = MARKS[ballName];
  if (sh.path) reveal(M.path, clamp(t / B.path.dur, 0, 1) * (t < 0 ? 0 : 1));
  if (sh.pathFull) reveal(M.path, 1);
  if (sh.land && t >= sh.land) { M.land.visible = M.landDot.visible = true; const k = 1 + 0.12 * Math.sin(t * 9); M.land.scale.set(k, 1, k); }
  if (sh.naive && t >= sh.naive) M.naive.visible = true;
  for (const r of sh.routes || []) { const g = r === "naive" ? M.naiveR : M[r]; if (g) reveal(g, clamp(t / 7, 0, 1)); }
  if (sh.start) for (const k of sh.start) START_RINGS[k].visible = true;
  for (const k of Object.keys(POS_TAGS)) POS_TAGS[k].visible = !!sh.tags && sh.start?.includes(k);
  if (sh.straight && M.straight) { reveal(M.straight, clamp(t / B.path_straight.dur, 0, 1)); placeBall(BALL2, pathAt(B.path_straight, Math.min(t, B.path_straight.dur)), t > 0); }
  if (sh.spin && t > 0) {
    spinRing.visible = true; spinRing.position.copy(pathAt(B.path, t));
    const ax = V(B.spin_axis).normalize(); spinRing.quaternion.setFromUnitVectors(v3(0, 0, 1), ax);
    spinRing.userData.spinner.rotation.z = -(window.__hfThreeTime || 0) * 5.0;
  }
  if (sh.wedge) wedge.visible = true;
}

// ------------------------------------------------------------------ cameras
const cam = new THREE.PerspectiveCamera(40, W / H, 0.12, 3000);
function frame(c, pos, look, fov, aspect) { c.position.copy(pos); c.fov = fov; c.aspect = aspect; c.updateProjectionMatrix(); c.lookAt(look); }
const mixV = (a, b, u) => a.clone().lerp(b, u);
const pw = (v, vs, ts) => {
  if (v <= vs[0]) return ts[0];
  for (let i = 1; i < vs.length; i++) if (v <= vs[i]) return lerp(ts[i - 1], ts[i], (v - vs[i - 1]) / (vs[i] - vs[i - 1]));
  return ts.at(-1);
};
const SP = (deg, r, y = 0) => sprayPt(deg * D2R, r, y);
const CAMS = {
  plate: (u, t) => { const b = pathAt(BALLS.deep.path, Math.max(t, 0)); return [mixV(v3(-6, 7.5, 16), v3(-5, 9, 13), u), t < 0.15 ? v3(0, 4, -30) : v3(0, 4, -30).lerp(b, smooth((t - 0.15) / 0.5)), 38]; },   // behind the plate, then up with the ball
  behindCF: (u) => [mixV(SP(1, 385, 18), SP(1, 376, 16), easeIO(u)), SP(1, 250, 28), 55],                                     // behind the center fielder, looking in
  half: (u, t, s, k) => k === 1 ? [SP(1, 470, 92), SP(1, 362, 0), 48] : [SP(-2, 405, 70), SP(-3, 295, 0), 48],                   // split: high behind center field
  aerial: (u) => [mixV(v3(0, 380, 40), v3(0, 360, 28), easeIO(u)), v3(0, 0, -230), 55],                                       // high behind home: the whole outfield
  gap: (u) => [mixV(SP(0, 430, 60), SP(2, 425, 55), u), SP(12, 320, 0), 48],                                                  // behind center field, looking at right-center
  lfc: (u) => [mixV(SP(-12, 370, 26), SP(-14, 368, 24), u), SP(-36, 320, 2), 50],                                            // behind left field, the line and the pole in view
  rfc: (u) => [mixV(SP(12, 370, 26), SP(14, 368, 24), u), SP(36, 320, 2), 50],                                               // behind right field, the line and the pole in view
  ballcam: (u, t) => { const B = BALLS.rfslice, b = pathAt(B.path, t), b2 = pathAt(B.path, t + 0.05), d = b2.clone().sub(b).normalize(); return [b.clone().addScaledVector(d, -6).add(v3(-2.5, 1.6, 2)), b.clone().addScaledVector(d, 3), 46]; },
  top: (u) => [mixV(SP(22, 170, 140), SP(23, 180, 132), u), SP(27, 335, 0), 42],                                              // high over the infield, down the right-field line
  hitter: (u) => [mixV(v3(-11, 15, 24), v3(-10, 14, 22), easeIO(u)), v3(60, 0, -150), 60],                                    // behind the right-handed hitter, his opposite field ahead
  rftrack: (u, t) => { const f = routeAt(BALLS.rfslice.routes.ok, t), out = v3(f.x, 0, f.z).normalize(), side = v3(-out.z, 0, out.x);
    const look = f.clone().addScaledVector(out, -80); look.y = 19; return [f.clone().addScaledVector(out, 34).addScaledVector(side, -8).add(v3(0, 12, 0)), look, 50]; },   // behind the right fielder, with him
  endwide: (u) => [mixV(SP(20, 250, 40), SP(18, 240, 36), u), SP(30, 330, 6), 46],
};
function shotAt(v) {
  const L = CC.shots.list;
  const s = L.find((x) => v < x.b) || L.at(-1);
  const r = s.cu || [s.a, s.b];
  return { s, t: pw(v, s.vs, s.ts), u: clamp((v - r[0]) / (r[1] - r[0]), 0, 1) };
}

// ------------------------------------------------------------------ DOM overlays fed from the same clock
const $ = (id) => document.getElementById(id);
const SPEEDS = { rt: "Real time", slow2: "Slow motion · ½ speed", slow3: "Slow motion · ⅓ speed", slow4: "Slow motion · ¼ speed", replay: "Replay · ⅓ speed", freeze: "Freeze", pre: "" };
function overlays(s, t) {
  if ($("spd")) { $("spd").textContent = SPEEDS[s.speed] ?? ""; $("spd").className = "spd " + (s.speed === "rt" ? "rt" : "sl"); $("spd").style.opacity = s.speed === "pre" ? 0 : 1; }
}

function renderAt(v) {
  const { s, t, u } = shotAt(v);
  renderer.setScissorTest(s.mode === "split");
  if (s.mode === "split") {
    s.halves.forEach((half, k) => {
      const th = s.hold ? Math.min(t, BALLS[half.ball].t_catch) : t;
      setScene(th, s, half);
      const c = CAMS[s.cam](u, th, s, k);
      frame(cam, c[0], c[1], c[2], (W / 2) / H);
      renderer.setViewport(k * W / 2, 0, W / 2, H); renderer.setScissor(k * W / 2, 0, W / 2, H);
      renderer.render(scene, cam);
    });
  } else {
    setScene(t, s);
    const c = CAMS[s.cam](u, t, s);
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
document.fonts.ready.then(() => seek(window.__hfThreeTime || 0));
seek(window.__hfThreeTime || 0);
