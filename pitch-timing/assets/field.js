// "Why pitchers vary their timing": the field, dugouts, outfield seats, the players, in three.js.
// Everything is a pure function of HyperFrames time (hf-seek), so each frame is exact and repeatable.
// Units are feet. Home plate's back point is the origin, +x points toward first base's side, -z toward center field.
// The pitch comes from tools/physics.py via window.__PLAY.
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
// the defense (white): a right-handed pitcher in the stretch, catcher, infield; a runner on first and a right-handed batter (dark); umpires (black)
const pitcher = makePlayer(KIT.home, { glove: true });
const C = makePlayer(KIT.home, { glove: true, catcher: true });
const ump = makePlayer(KIT.ump, { catcher: true }), U1 = makePlayer(KIT.ump), U2 = makePlayer(KIT.ump);
const batter = makePlayer(KIT.away, { helmet: true, bat: true });
const R = makePlayer(KIT.away, { helmet: true });
const homeD = { b2: [26, -116], ss: [-27, -114], b3: [-58, -76], lf: [-118, -262], cf: [0, -312], rf: [118, -262] };
const HD = {}; for (const [k, [x, z]] of Object.entries(homeD)) { HD[k] = makePlayer(KIT.home, { glove: true }); HD[k].root.position.set(x, 0, z); }
const B1F = makePlayer(KIT.home, { glove: true }), B2F = HD.b2;
const bench = [];
for (const [g, kit, xs] of [[dg3, KIT.home, [-24, -12, -4, 9, 20]], [dg1, KIT.away, [-22, -9, 4, 16, 25]]]) for (const x of xs) {
  const p = makePlayer(kit); const q = dgAt(g, x, 3.4); p.root.position.copy(q); p.root.rotation.y = dgYaw(g); applyPose(p, { ...STAND, lean: 8, shL: [50, 12, 0], shR: [50, 12, 0], elL: 70, elR: 70, nod: -4 }); bench.push(p);
}
for (const p of [pitcher, C, ump, U1, U2, batter, R, B1F, ...Object.values(HD), ...bench]) scene.add(p.root);
const PLATE_C = v3(0, 0, -0.7);
const headTop = (P) => wpos(P.neck).add(v3(0, 1.4, 0));

// ------------------------------------------------------------------ the model
const FB = PLAY.pitches.fb, FL = FB.flight;
function pathAt(path, t) {
  const u = (t - path.t0) * path.hz, n = path.p.length - 1;
  if (u <= 0) return V(path.p[0]);
  if (u >= n) return V(path.p[n]);
  const i = Math.floor(u), f = u - i, a = path.p[i], b = path.p[i + 1];
  return v3(lerp(a[0], b[0], f), lerp(a[1], b[1], f), lerp(a[2], b[2], f));
}
const sprint = (t, vmax, tau) => (t <= 0 ? 0 : vmax * (t - tau * (1 - Math.exp(-t / tau))));
const arcAt = (p0, p1, T, u) => p0.clone().lerp(p1, clamp(u / T, 0, 1)).add(v3(0, 16.1 * clamp(u, 0, T) * (T - clamp(u, 0, T)), 0));
const moundY = (x, z) => { const r = Math.hypot(x - MOUND.x, z - MOUND.z); return r < 2.5 ? MOUND_H : r < 5.5 ? lerp(MOUND_H, 0.45, (r - 2.5) / 3) : r < 9 ? lerp(0.45, 0, (r - 5.5) / 3.5) : 0; };
// times (play time; t = 0: the pitch reaches the catcher's glove, or for a pickoff the throw leaves his hand)
const FIRST = { pitch: 1.05, quick: 0.8 };                         // first move to release: a leg kick from the stretch, or a slide step
const tMove = (s) => (s.kind === "pick" ? -0.55 : -FIRST[s.kind ?? "pitch"] - FL);   // the pitcher's first move
const tSet = (s) => tMove(s) - (s.hold ?? 1.2);                   // he comes set (hands together) this long before it
const TO2 = B2.clone().sub(B1).normalize(), LEAD = 12.5, L1 = B1.clone().addScaledVector(TO2, LEAD);
const RUN = { vmax: 29.0, tau: 0.6, slideD: 8, vb: 12 };          // the steal: 3.3 s from the pitcher's first move to the bag
const T_CREL = 0.8, T_CT = 1.15, T_CAT = T_CREL + T_CT, T_TAG = T_CAT + 0.12;   // the catcher: pop time 1.95 s
const B2C = v3(2.6, 0, -125.4), B1S = v3(62.2, 0, -62.6), RUB_P = v3(0, MOUND_H, -60.7), PK_T = 0.55;
const runLen = L1.distanceTo(B2) - 1.0;
function stealD(u) {                                              // distance run u seconds after his break, with the slide into the bag
  const L = runLen, sd = RUN.slideD;
  let us = 0; while (sprint(us, RUN.vmax, RUN.tau) < L - sd && us < 6) us += 0.002;
  const vs = RUN.vmax * (1 - Math.exp(-us / RUN.tau)), dec = (vs * vs - RUN.vb * RUN.vb) / (2 * sd), ts = (vs - RUN.vb) / dec;
  if (u < us) return { d: sprint(u, RUN.vmax, RUN.tau), slide: 0, us, ts };
  const w = Math.min(u - us, ts); return { d: L - sd + vs * w - 0.5 * dec * w * w, slide: smooth((u - us) / 0.15), us, ts };
}

// ------------------------------------------------------------------ poses
const C_SET = { ...CROUCH, shL: [62, 18, 0], elL: 40, shR: [20, 10, 0], elR: 50, nod: -18 };
const C_MID = { ...CROUCH, nod: -8, shL: [78, 12, 0], elL: 24, shR: [20, 10, 0], elR: 60 };
const C_POP = { ...STAND, drop: -0.4, lean: 14, twist: -40, shR: [-30, 80, 0], elR: 95, shL: [60, 20, 0], elL: 30, hipL: [30, 6], knL: 26, hipR: [10, 6], knR: 20 };
const C_THROW = { ...STAND, drop: -0.3, lean: 26, twist: 30, shR: [160, 20, 0], elR: 15, shL: [30, 34, 0], elL: 70, hipL: [36, 4], knL: 26, hipR: [-10, 6], knR: 30 };
const U_SET = { drop: -1.0, lean: 30, nod: -6, hipL: [52, 28], hipR: [52, 28], knL: 68, knR: 68, shL: [30, 20, 0], elL: 60, shR: [30, 20, 0], elR: 60 };
const U_BASE = { drop: -0.7, lean: 26, nod: -6, hipL: [40, 16], hipR: [40, 16], knL: 48, knR: 48, shL: [30, 12, 0], elL: 50, shR: [30, 12, 0], elR: 50 };
const U_SAFE = { ...STAND, lean: 2, shL: [8, 88, 0], elL: 2, shR: [8, 88, 0], elR: 2 };
const P_OPEN = { lean: 2, look: 80, nod: 6, shL: [20, 12, 0], elL: 40, shR: [12, 6, 0], elR: 30, hipL: [4, 6], hipR: [4, 6], knL: 8, knR: 8 };   // on the rubber, hands apart, taking the sign
const P_SET = { lean: 4, look: 80, nod: 4, shL: [42, 8, 0], elL: 105, shR: [38, -4, 0], elR: 112, hipL: [4, 6], hipR: [4, 6], knL: 8, knR: 8 };   // set: hands together, looking in
const P_CHECK = { ...P_SET, look: -70, nod: 0, twist: -12 };                                                    // a look over at the runner
const P_LIFT = { lean: -4, look: 80, shL: [48, 8, 0], elL: 100, shR: [44, -4, 0], elR: 108, hipL: [100, 4], knL: 105, hipR: [6, 6], knR: 14, drop: -0.15 };
const P_SLIDE = { ...P_LIFT, hipL: [38, 4], knL: 44, lean: 2, drop: -0.25 };                                     // a slide step: barely a lift
const P_STRIDE = { lean: 6, look: 40, drop: -0.6, twist: -50, shL: [80, 35, 0], elL: 25, shR: [-55, 80, 0], elR: 85, hipL: [52, 4], knL: 28, hipR: [-28, 6], knR: 38 };
const P_REL = { lean: 42, nod: 8, drop: -1.0, twist: 28, shL: [12, 32, 0], elL: 85, shR: [168, 22, 0], elR: 8, hipL: [72, 4], knL: 22, hipR: [-18, 6], knR: 92 };
const P_FOLLOW = { lean: 62, nod: 18, drop: -1.25, twist: 48, shL: [8, 38, 0], elL: 95, shR: [58, -24, 0], elR: 22, hipL: [82, 4], knL: 38, hipR: [34, 6], knR: 84 };
const PK_TURN = { ...P_SET, look: 0, drop: -0.2, hipL: [30, 6], knL: 36, shR: [-20, 60, 0], elR: 90 };          // the jump turn
const PK_STRIDE = { ...P_STRIDE, drop: -0.45, twist: -40, look: 0, hipL: [42, 4], knL: 30, hipR: [-18, 6], knR: 30 };
const PK_REL = { lean: 24, nod: 4, drop: -0.7, twist: 22, shL: [16, 30, 0], elL: 80, shR: [150, 18, 0], elR: 14, hipL: [50, 4], knL: 26, hipR: [-12, 6], knR: 52 };
const PK_FOLLOW = { lean: 30, nod: 8, drop: -0.8, twist: 36, shL: [10, 34, 0], elL: 90, shR: [62, -16, 0], elR: 30, hipL: [52, 4], knL: 34, hipR: [8, 6], knR: 60 };
const BAT_SET = { drop: -0.35, lean: 18, look: 80, nod: -4, hipL: [22, 14], hipR: [22, 14], knL: 26, knR: 26, shL: [55, 6, 0], shR: [60, 34, 0], elL: 95, elR: 110, twist: 20 };
const BAT_TAKE = { ...BAT_SET, twist: 26, pelvisTwist: -8, hipL: [30, 18], knL: 34 };
const B_HOLD = { drop: -0.45, lean: 16, nod: -4, hipL: [26, 20], hipR: [26, 20], knL: 32, knR: 32, shL: [60, 18, 0], elL: 70, shR: [24, 10, 0], elR: 50 };
const B_CATCH = { ...B_HOLD, shL: [88, 0, 0], elL: 8 };
const B_TAG1 = { drop: -1.0, lean: 50, nod: -24, hipL: [56, 14], hipR: [56, 14], knL: 66, knR: 66, shL: [56, -8, 0], elL: 6, shR: [40, 0, 0], elR: 40 };
const B2_RECV = { ...READY, drop: -0.3, lean: 16, shL: [86, -6, 0], elL: 10, shR: [50, 0, 0], elR: 40 };
const B2_TAG = { drop: -1.1, lean: 48, nod: -26, hipL: [60, 14], hipR: [60, 14], knL: 72, knR: 72, shL: [52, -20, 0], elL: 8, shR: [40, 0, 0], elR: 40 };
const R_LEAD = { ...LEAD_POSE, nod: 14 };                                                          // eyes up, on the pitcher
const R_LEAN = { ...LEAD_POSE, nod: 10, lean: 34, twist: -18, drop: -0.85, hipR: [30, 26], knR: 40, hipL: [48, 18], knL: 58 };   // weight shifting toward second
const R_BACK = { ...LEAD_POSE, nod: 12, lean: 22, twist: 10, drop: -0.7 };                                                // weight back toward first
const R_DIVE = { drop: -2.72, pelvisTilt: 84, lean: 0, nod: -55, hipL: [-6, 8], hipR: [-6, 8], knL: 14, knR: 22, shL: [172, 10, 0], elL: 4, shR: [168, 14, 0], elR: 6 };   // head first, back to the bag

// ------------------------------------------------------------------ graphics: the ball, rings, the pickoff step, the runner's jump
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
const ringMat = (c) => new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: 0.9, depthWrite: false, side: THREE.DoubleSide });
const RINGS = { r: [0xffd84d, R], p: [0x56d1ff, pitcher] };
for (const k of Object.keys(RINGS)) { const m = new THREE.Mesh(new THREE.RingGeometry(1.8, 2.4, 36), ringMat(RINGS[k][0])); m.rotation.x = -Math.PI / 2; m.renderOrder = 7; m.visible = false; scene.add(m); RINGS[k].push(m); }
function arrow(color) {                                          // a flat arrow on the ground from a to b
  const g = new THREE.Group(), m = flatMat(color, 0.92);
  const s = new THREE.Mesh(new THREE.PlaneGeometry(1, 0.5), m); s.rotation.x = -Math.PI / 2; s.renderOrder = 8; g.add(s);
  const head = new THREE.Mesh(new THREE.ShapeGeometry(new THREE.Shape([new THREE.Vector2(0, -0.85), new THREE.Vector2(1.5, 0), new THREE.Vector2(0, 0.85)])), m); head.rotation.x = -Math.PI / 2; head.renderOrder = 8; g.add(head);
  g.visible = false; scene.add(g);
  g.userData.set = (a, b, u = 1) => { const d = b.clone().sub(a), L = d.length() * u; g.position.copy(a); g.rotation.set(0, -Math.atan2(d.z, d.x), 0); s.position.set((L - 1.4) / 2, 0, 0); s.scale.set(Math.max(0.01, L - 1.4), 1, 1); head.position.set(L - 1.5, 0, 0); g.visible = u > 0; };
  return g;
}
const AR_PK = arrow(0xff6a3d), AR_JUMP = arrow(0xffd84d);
const SIGHT = new THREE.Mesh(new THREE.BoxGeometry(1, 0.06, 0.06), flatMat(0x56d1ff, 0.75)); SIGHT.renderOrder = 8; SIGHT.visible = false; scene.add(SIGHT);

// ------------------------------------------------------------------ one frame
// s.kind: "pitch" (a leg kick from the stretch), "quick" (a slide step), "pick" (a pickoff to first); s.hold: seconds in the set
// s.runner: "lead" (lead, a secondary lead on the pitch), "watch" (studying, rocking with the pitcher), "steal", "hesitate" (he leans to go
// at s.lean, has to stop), "dive" (back to the bag on the pickoff). s.checks: times the pitcher looks over at him.
const FACE_IN = yawTo(L1, MOUND);
function pitcherAt(t, s) {
  const ts = tSet(s), tm = tMove(s);
  let pre = keyed([[ts - 1.6, P_OPEN], [ts - 0.6, P_OPEN], [ts, P_SET]], t);
  for (const c of s.checks ?? []) if (t > c - 0.3 && t < c + 0.9) pre = keyed([[c - 0.3, P_SET], [c, P_CHECK], [c + 0.5, P_CHECK], [c + 0.85, P_SET]], t);
  let pos = RUB_P.clone().add(v3(0, 0, 0.1)), yaw = -Math.PI / 2, q = pre;
  if (s.kind === "pick") {
    if (t > tm) q = keyed([[tm, pre], [-0.38, PK_TURN], [-0.16, PK_STRIDE], [0, PK_REL], [0.3, PK_FOLLOW], [1.2, { ...READY, look: -10 }]], t);
    yaw = lerp(-Math.PI / 2, PK_YAW, smooth((t - tm) / 0.3));
    const dir = v3(Math.sin(PK_YAW), 0, Math.cos(PK_YAW));
    pos = RUB_P.clone().addScaledVector(dir, 2.0 * smooth((t + 0.25) / 0.3)); pos.y = moundY(pos.x, pos.z);
  } else if (t > tm) {
    const F = FIRST[s.kind ?? "pitch"], tr = t + FL;
    const lift = s.kind === "quick" ? P_SLIDE : P_LIFT, k = F / 1.05;
    q = keyed([[-F, pre], [-0.75 * k, lift], [-0.3 * k, P_STRIDE], [0, P_REL], [0.35, P_FOLLOW], [1.0, { ...READY, look: 0 }]], tr);
    const zp = lerp(-60.6, -57.6, smooth((tr + 0.42 * k) / (0.48 * k))); pos = v3(0, MOUND_H * (zp > -59 ? 0.6 : 1), zp);
    yaw = lerp(-Math.PI / 2, 0, smooth((tr + 0.58 * k) / (0.58 * k)));
  }
  pitcher.root.position.copy(pos); pitcher.root.rotation.y = yaw; applyPose(pitcher, q);
}
const PK_YAW = Math.atan2(B1.x - RUB_P.x, B1.z - RUB_P.z) - 2 * Math.PI;   // facing first base; the jump turn swings round through the second-base side
function setScene(t, s) {
  const kind = s.kind ?? "pitch", tm = tMove(s), ts = tSet(s), mode = s.runner ?? "lead";
  const pitch = kind !== "pick", steal = mode === "steal";
  for (const [k, p] of Object.entries(HD)) { const [x, z] = homeD[k]; p.root.position.set(x, 0, z); p.root.rotation.y = Math.atan2(-x, -z); applyPose(p, pitch && t > tm + 0.4 ? READY : STAND); }
  pitcherAt(t, s);
  // umpires
  ump.root.position.set(0.5, 0, 6.0); ump.root.rotation.y = Math.PI; applyPose(ump, pitch && t > tm ? U_SET : { ...STAND, lean: 6 });
  U1.root.position.set(72, 0, -78); U1.root.rotation.y = yawTo(U1.root.position, PLATE_C); applyPose(U1, U_BASE);
  const u2p = v3(-14, 0, -110).lerp(v3(-12, 0, -128), steal ? smooth((t - tm - 0.4) / 1.4) : 0); U2.root.position.copy(u2p); U2.root.rotation.y = yawTo(u2p, steal && t > 0 ? B2 : PLATE_C);
  applyPose(U2, steal && t > T_TAG + 0.15 ? keyed([[T_TAG + 0.15, U_BASE], [T_TAG + 0.4, U_SAFE], [T_TAG + 2, U_SAFE]], t) : U_BASE);
  // batter: takes the pitch
  batter.root.position.set(-3.0, 0, -0.9); batter.root.rotation.y = Math.PI / 2; batter.bat.visible = true;
  applyPose(batter, pitch ? keyed([[-0.7, BAT_SET], [-0.3, BAT_TAKE], [0.4, BAT_TAKE], [1.0, BAT_SET]], t) : BAT_SET);
  // catcher
  C.root.position.set(0.15, 0, 3.0); C.root.rotation.y = Math.PI;
  let cq = pitch ? keyed([[-0.6, C_SET], [-0.05, C_MID], [0.5, C_MID], [1.1, { ...C_MID, nod: 0 }]], t) : C_SET;
  if (steal) { cq = keyed([[-0.6, C_SET], [-0.05, C_MID], [0.12, C_MID], [0.45, C_POP], [T_CREL, C_THROW], [T_CREL + 0.5, STAND]], t); if (t > 0.2) C.root.position.z = lerp(3.0, 1.8, smooth((t - 0.2) / 0.5)); }
  applyPose(C, cq);
  // first baseman: holding the runner on; off the bag once the pitch is on its way; the pickoff catch and tag
  let b1p = B1S.clone(), b1q = B_HOLD;
  if (pitch && t > tm + 0.25) b1q = mixPose(B_HOLD, READY, smooth((t - tm - 0.25) / 0.5));   // off the hold, into his ready stance
  if (!pitch) b1q = keyed([[-0.25, B_HOLD], [0.1, B_CATCH], [PK_T + 0.02, B_CATCH], [PK_T + 0.25, B_TAG1], [PK_T + 1.2, B_TAG1], [PK_T + 1.7, B_HOLD]], t);
  B1F.root.position.copy(b1p); B1F.root.rotation.y = yawTo(b1p, MOUND); applyPose(B1F, b1q);
  // second baseman: covers second on the steal
  if (steal && t > tm + 0.35) {
    const d0 = v3(...homeD.b2.slice(0, 1), 0, homeD.b2[1]), u = clamp((t - tm - 0.35) / 1.6, 0, 1), p = d0.clone().lerp(B2C, smooth(u));
    B2F.root.position.copy(p); B2F.root.rotation.y = u < 1 ? yawTo(p, B2C) : yawTo(p, PLATE_C);
    applyPose(B2F, u < 1 ? runPose(((t - tm) * 1.9) % 1, 0.85) : keyed([[T_CAT - 0.1, B2_RECV], [T_TAG, B2_TAG], [T_TAG + 0.8, B2_TAG], [T_TAG + 1.3, { ...STAND, shL: [60, 10, 0], elL: 30 }]], t));
  }
  // the runner
  let rp = L1.clone(), ry = FACE_IN, rq = R_LEAD;
  const rock = (k) => mixPose(R_BACK, R_LEAN, 0.5 + 0.5 * Math.sin(k));
  if (mode === "watch") rq = mixPose(R_LEAD, rock((t - ts) * 2 * Math.PI / 1.2), t > ts ? 0.55 : 0.2);          // rocking in rhythm with the pitcher's hold
  if (mode === "lead" || mode === "hesitate") {
    if (pitch && t > tm + 0.15) { const u = clamp((t - tm - 0.15) / 0.9, 0, 1); rp = L1.clone().addScaledVector(TO2, 6 * smooth(u)); rq = u < 1 ? mixPose(R_LEAD, runPose((u * 1.6) % 1, 0.35), Math.sin(Math.PI * u)) : { ...R_LEAD, lean: 22, drop: -0.6 }; }
  }
  if (mode === "hesitate" && s.lean != null) {                    // he leans to go when he expects the pitch... and has to stop
    const a = s.lean, w = clamp((t - a) / 0.25, 0, 1) * (1 - clamp((t - a - 0.55) / 0.35, 0, 1));
    if (t > a && t < a + 0.95) { rq = mixPose(rq, R_LEAN, w); rp = rp.clone().addScaledVector(TO2, 1.4 * w); }
  }
  if (steal && t > s.brk) {
    const u = t - s.brk, sd = stealD(u), p = L1.clone().addScaledVector(TO2, sd.d);
    rp = p; ry = yawTo(L1, B2);
    rq = sd.slide ? mixPose(runPose((sd.d / 11.5) % 1, 1), SLIDE_POSE, sd.slide) : u < 0.3 ? mixPose(R_LEAD, runPose((sd.d / 11.5) % 1, 1), smooth(u / 0.3)) : runPose((sd.d / 11.5) % 1, 1);
    if (u > sd.us + sd.ts + 0.6) rq = mixPose(SLIDE_POSE, { ...STAND, look: 40 }, smooth((u - sd.us - sd.ts - 0.6) / 0.5));
  }
  if (mode === "dive" && t > -0.28) {                             // the pickoff: a crossover and a dive back, hand to the bag
    const u = clamp((t + 0.28) / 0.62, 0, 1), end = B1.clone().addScaledVector(TO2, 5.6);
    rp = L1.clone().lerp(end, smooth(u)); ry = yawTo(L1, B1);
    rq = u < 0.45 ? mixPose(R_LEAD, runPose(u * 1.2 % 1, 0.8), u / 0.45) : mixPose(runPose(0.5, 0.8), R_DIVE, smooth((u - 0.45) / 0.35));
  }
  R.root.position.copy(rp); R.root.rotation.y = ry; applyPose(R, rq);
  // the ball
  let bp, trail = null;
  if (pitch) {
    if (t < -FL - 0.02) bp = wpos(pitcher.handR);
    else if (t < 0) { bp = pathAt(FB.path, t); trail = (d) => (t - d > FB.path.t0 ? pathAt(FB.path, t - d) : null); }
    else if (!steal || t < T_CREL - 0.25) bp = wpos(C.handL);
    else if (t < T_CREL) bp = wpos(C.handR);
    else if (t < T_CAT) { const a = v3(0.3, 6.1, 2.2); bp = arcAt(a, wpos(B2F.handL), T_CT, t - T_CREL); trail = (d) => (t - d > T_CREL ? arcAt(a, wpos(B2F.handL), T_CT, t - d - T_CREL) : null); }
    else bp = wpos(B2F.handL);
  } else {
    if (t < 0) bp = wpos(pitcher.handR);
    else if (t < PK_T) { const a = PK_HAND ?? wpos(pitcher.handR); bp = arcAt(a, wpos(B1F.handL), PK_T, t); trail = (d) => (t - d > 0 ? arcAt(a, wpos(B1F.handL), PK_T, t - d) : null); }
    else bp = wpos(B1F.handL);
  }
  placeBall(bp, trail);
  // graphics
  for (const [k, [, P, m]] of Object.entries(RINGS)) { m.visible = !!s.rings?.includes(k); if (m.visible) { const q2 = wpos(P.pelvis); m.position.set(q2.x, 0.12, q2.z); m.material.opacity = 0.7 + 0.25 * Math.sin(t * 9); } }
  AR_PK.visible = AR_JUMP.visible = false;
  SIGHT.visible = s.sight != null && t > s.sight;
  if (SIGHT.visible) { const e = wpos(R.neck).add(v3(0, 0.35, 0)), g = wpos(pitcher.neck).add(v3(0, -0.6, 0)), d = g.clone().sub(e), u2 = clamp((t - s.sight) / 0.4, 0, 1), L = d.length() * u2;
    SIGHT.position.copy(e).addScaledVector(d.normalize(), L / 2); SIGHT.scale.set(L, 1, 1); SIGHT.rotation.set(0, -Math.atan2(d.z, d.x), Math.atan2(d.y, Math.hypot(d.x, d.z))); }
  if (!pitch && s.arPk != null) { const a = RUB_P.clone().setY(MOUND_H + 0.1); AR_PK.userData.set(a, a.clone().add(v3(Math.sin(PK_YAW), 0, Math.cos(PK_YAW)).multiplyScalar(9)), clamp((t - s.arPk) / 0.3, 0, 1)); }
  if (steal && s.arJump != null) AR_JUMP.userData.set(L1.clone().setY(0.1), B2.clone().addScaledVector(TO2, -4).setY(0.1), clamp((t - s.arJump) / 0.5, 0, 1));
}
let PK_HAND = null;
setScene(0, { kind: "pick", hold: 1, runner: "dive" }); PK_HAND = wpos(pitcher.handR);

// ------------------------------------------------------------------ cameras
const cam = new THREE.PerspectiveCamera(40, W / H, 0.05, 3000);
function frame(c, pos, look, fov, aspect) { c.position.copy(pos); c.fov = fov; c.aspect = aspect; c.updateProjectionMatrix(); c.lookAt(look); }
const mixV = (a, b, u) => a.clone().lerp(b, u);
const pw = (v, vs, ts) => {
  if (v <= vs[0]) return ts[0];
  for (let i = 1; i < vs.length; i++) if (v <= vs[i]) return lerp(ts[i - 1], ts[i], (v - vs[i - 1]) / (vs[i] - vs[i - 1]));
  return ts.at(-1);
};
const CAMS = {
  behindR: (u) => [mixV(v3(67.6, 6.2, -74.6), v3(66.2, 6.0, -74.2), u), v3(0, 3.8, -60.5), 30],              // behind the runner, toward the mound
  side3b: (u) => [mixV(v3(-17, 5.4, -52), v3(-15.5, 5.3, -53.5), u), v3(0, 4.3, -60.2), 34],               // third-base side: the pitcher's front in the set
  runnerZoom: (u) => [mixV(v3(57, 6.2, -55), v3(52.5, 5.0, -64), easeIO(u)), v3(53.2, 4.6, -72.3), lerp(44, 32, easeIO(u))],   // in on the runner's profile
  runnerFace: (u) => [mixV(v3(52.5, 5.0, -64), v3(52.4, 5.0, -64.6), u), v3(53.2, 4.6, -72.3), 32],      // his profile, his line of sight to the pitcher
  runnerFeet: (u) => [mixV(v3(49, 1.2, -80), v3(49.6, 1.1, -79.4), u), v3(54.8, 1.5, -72.5), 44],
  wideR: (u) => [mixV(v3(82, 9, -60), v3(80, 8.6, -63), u), v3(30, 3, -84), 40],                             // beyond first: the runner, the mound, second
  throwCam: (u) => [mixV(v3(2, 17, 24), v3(2, 16, 20), u), v3(0, 3, -112), 26],
  tag2: (u) => [mixV(v3(-14, 3, -118), v3(-13, 3, -118.6), u), v3(2, 1.4, -125.5), 36],                     // the shortstop's side of the bag: the slide, the tag
  highHome: (u) => [mixV(v3(74.3, 10, -76.8), v3(73, 9.4, -76.4), easeIO(u)), v3(10, 2, -62), 40],      // up behind the runner: him and the pitcher
  pick: (u) => [mixV(v3(-22, 16, -58), v3(-21, 15.5, -58.5), u), v3(30, 1, -62), 40],
  dive1: (u) => [mixV(v3(70, 3.2, -48), v3(69, 3.0, -49.5), u), v3(60, 1.6, -66), 40],
  finalLow: (u) => [mixV(v3(80, 9.5, -77.5), v3(73, 8.2, -76.2), easeIO(u)), v3(0, 3.6, -60.5), 24],   // behind and above the runner: him, and the pitcher beyond
};
function shotAt(v) {
  const L = CC.shots.list;
  const s = L.find((x) => v < x.b) || L.at(-1);
  return { s, t: pw(v, s.vs, s.ts), u: clamp((v - s.a) / (s.b - s.a), 0, 1) };
}

// ------------------------------------------------------------------ DOM overlays fed from the same clock
const $ = (id) => document.getElementById(id);
const PINT = { runner: () => headTop(R), pitcher: () => headTop(pitcher), catcher: () => headTop(C), b1: () => headTop(B1F), base2: () => B2.clone().add(v3(0, 5, 0)),
  step: () => RUB_P.clone().add(v3(Math.sin(PK_YAW) * 8, 1.0, Math.cos(PK_YAW) * 8)), feet: () => wpos(R.ftL).add(v3(0, 2.4, 0)) };
function pin(id, p) {                                            // x is clamped so the label stays on screen
  const el = $(id); if (!el || !p) return;
  const q = p.clone().project(cam);
  el.style.left = `${clamp((q.x + 1) / 2 * W, 190, W - 190).toFixed(1)}px`; el.style.top = `${((1 - q.y) / 2 * H).toFixed(1)}px`;
}
function meter(id, t, s) {                                       // how long he has held the set: counts while he's set, holds the number after
  const el = $(id); if (!el) return;
  const ts = tSet(s), tm = tMove(s), held = clamp(t - ts, 0, tm - ts), live = t > ts && t < tm;
  el.style.opacity = t > ts - 0.3 ? 1 : 0;
  el.querySelector(".mv").textContent = `${held.toFixed(1)} s`;
  el.querySelector(".mf").style.width = `${(100 * held / 3).toFixed(1)}%`;
  el.querySelector(".mk").textContent = t < ts ? "" : live ? "set…" : s.kind === "pick" ? "pickoff" : "pitch";
  el.classList.toggle("go", t >= tm);
}
function renderAt(v) {
  const { s, t, u } = shotAt(v);
  renderer.setScissorTest(s.mode === "split");
  if (s.mode === "split") {
    for (const [y, half, mid] of [[H / 2, s.top, "mtA"], [0, s.bot, "mtB"]]) {
      const sh = { ...s, ...half }, th = pw(v, half.vs, half.ts);
      setScene(th, sh);
      const c = CAMS[half.cam](u, th, sh, v);
      frame(cam, c[0], c[1], c[2], W / (H / 2));
      renderer.setViewport(0, y, W, H / 2); renderer.setScissor(0, y, W, H / 2);
      BALL.glow.scale.set(0.02, 0.02, 1);
      renderer.render(scene, cam);
      meter(mid, th, sh);
    }
  } else {
    setScene(t, s);
    const c = CAMS[s.cam](u, t, s, v);
    renderer.setViewport(0, 0, W, H);
    frame(cam, c[0], c[1], c[2], W / H);
    const g = c[2] < 16 ? 0.009 : 0.02; BALL.glow.scale.set(g, g, 1);
    renderer.render(scene, cam);
    for (const [id, key] of CC.pins) pin(id, PINT[key]());
    if (s.meter) meter("mt", t, s); else if ($("mt")) $("mt").style.opacity = 0;
  }
  if ($("spd")) { const sp = s.freeze != null && v >= s.freeze && (s.freezeEnd == null || v < s.freezeEnd) ? "Freeze" : s.speed === "slow" && (s.slowEnd == null || v < s.slowEnd) && (s.slowStart == null || v >= s.slowStart) ? "Slow motion" : s.speed === "replay" ? "Replay" : ""; $("spd").textContent = sp; $("spd").style.opacity = sp ? 1 : 0; }
}

let last = -1;
function seek(time) { if (time === last) return; last = time; renderAt(time); }
window.addEventListener("hf-seek", (e) => seek(e.detail.time));
window.__fieldRender = renderAt;
document.fonts.ready.then(() => seek(window.__hfThreeTime || 0));
seek(window.__hfThreeTime || 0);
