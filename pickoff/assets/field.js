// "Pickoff throw out of play": the field, dugouts, outfield seats, the players, in three.js.
// Everything is a pure function of HyperFrames time (hf-seek), so each frame is exact and repeatable.
// Units are feet. Home plate's back point is the origin, +x points toward first base's side, -z toward center field.
// The pitches come from tools/physics.py via window.__PLAY.
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
// the first-base dugout runs from about 51 to 115 ft down the line, 33 ft into foul territory (center 83 ft down the line)
const dg3 = makeDugout(-70.7, -7.1, 3 * Math.PI / 4, 0x1c2b4b), dg1 = makeDugout(82.0, -35.4, -3 * Math.PI / 4, 0xc4352d);
const dgAt = (g, x, z, y = 0) => g.localToWorld(v3(x, y, z));
const dgYaw = (g) => g.rotation.y;
const OD = v3(33, 0, 5);
for (const x of [OD.x, -OD.x]) { const m = new THREE.Mesh(new THREE.RingGeometry(2.3, 2.55, 40), chalk); m.rotation.x = -Math.PI / 2; m.position.set(x, 0.05, OD.z); scene.add(m); }


// ------------------------------------------------------------------ the cast
// the defense (white): pitcher, catcher, first baseman and the rest; the offense (dark): a right-handed batter and a runner on first
const pitcher = makePlayer(KIT.home, { glove: true });
const C = makePlayer(KIT.home, { glove: true, catcher: true });
const ump = makePlayer(KIT.ump, { catcher: true }), U1 = makePlayer(KIT.ump);
const batter = makePlayer(KIT.away, { helmet: true, bat: true });
const R = makePlayer(KIT.away, { helmet: true });
const homeD = { b2: [26, -116], ss: [-27, -114], b3: [-58, -76], lf: [-118, -262], cf: [0, -312], rf: [118, -262] };
const HD = {}; for (const [k, [x, z]] of Object.entries(homeD)) { HD[k] = makePlayer(KIT.home, { glove: true }); HD[k].root.position.set(x, 0, z); }
const B1F = makePlayer(KIT.home, { glove: true });
const bench = [];
for (const [g, kit, xs] of [[dg3, KIT.home, [-24, -12, -4, 9, 20]], [dg1, KIT.away, [-22, -9, 4, 16, 25]]]) for (const x of xs) {
  const p = makePlayer(kit); const q = dgAt(g, x, 3.4); p.root.position.copy(q); p.root.rotation.y = dgYaw(g); applyPose(p, { ...STAND, lean: 8, shL: [50, 12, 0], shR: [50, 12, 0], elL: 70, elR: 70, nod: -4 }); bench.push(p);
}
for (const p of [pitcher, C, ump, U1, batter, R, B1F, ...Object.values(HD), ...bench]) scene.add(p.root);
const PLATE_C = v3(0, 0, -0.7);
const headTop = (P) => wpos(P.neck).add(v3(0, 1.4, 0));


// ------------------------------------------------------------------ helpers
const sprint = (t, vmax, tau) => (t <= 0 ? 0 : vmax * (t - tau * (1 - Math.exp(-t / tau))));
const arcAt = (p0, p1, T, u) => p0.clone().lerp(p1, clamp(u / T, 0, 1)).add(v3(0, 16.1 * clamp(u, 0, T) * (T - clamp(u, 0, T)), 0));   // a throw under gravity
const moundY = (x, z) => { const r = Math.hypot(x - MOUND.x, z - MOUND.z); return r < 2.5 ? MOUND_H : r < 5.5 ? lerp(MOUND_H, 0.45, (r - 2.5) / 3) : r < 9 ? lerp(0.45, 0, (r - 5.5) / 3.5) : 0; };
const RUB_TOP = MOUND_H + 0.10, RUB_X = 1.0, RUB_Z0 = RUBBER_Z - 0.25, RUB_Z1 = RUBBER_Z + 0.25;   // the rubber: 24 x 6 in
const kf = (frames, t) => {                                          // keyed numbers: [[t, x], ...], eased between keys
  if (t <= frames[0][0]) return frames[0][1];
  for (let i = 1; i < frames.length; i++) if (t <= frames[i][0]) { const [t0, a] = frames[i - 1], [t1, b] = frames[i]; return lerp(a, b, easeIO((t - t0) / (t1 - t0))); }
  return frames.at(-1)[1];
};
const kv = (frames, t) => {                                          // keyed points
  if (t <= frames[0][0]) return frames[0][1].clone();
  for (let i = 1; i < frames.length; i++) if (t <= frames[i][0]) { const [t0, a] = frames[i - 1], [t1, b] = frames[i]; return a.clone().lerp(b, easeIO((t - t0) / (t1 - t0))); }
  return frames.at(-1)[1].clone();
};

// ------------------------------------------------------------------ legs: two-bone IK, so a foot stays exactly where it's put
// A foot is { ball: the ball of the foot on the surface (world), yaw: which way the toes point, heel: how far the heel is lifted (rad) }.
const LEG_A = 1.42, LEG_B = 1.43, ANK = 0.18;
const _m1 = new THREE.Matrix4(), _m2 = new THREE.Matrix4(), _q = new THREE.Quaternion(), _qi = new THREE.Quaternion();
function footAnkle(f) {
  const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(f.heel ?? 0, f.yaw, 0, "YXZ"));
  return f.ball.clone().add(v3(0, ANK, -0.6).applyQuaternion(q));
}
function legIK(P, k, f) {
  const hp = P[`hip${k}`], kn = P[`kn${k}`], ft = P[`ft${k}`];
  P.root.updateMatrixWorld(true);
  P.pelvis.getWorldQuaternion(_q); _qi.copy(_q).invert();
  const d = footAnkle(f).sub(hp.getWorldPosition(new THREE.Vector3())).applyQuaternion(_qi);
  const fw = v3(Math.sin(f.yaw), 0, Math.cos(f.yaw)).applyQuaternion(_qi);
  const L = clamp(d.length(), 0.5, LEG_A + LEG_B - 0.002);
  const kb = Math.PI - Math.acos(clamp((LEG_A ** 2 + LEG_B ** 2 - L * L) / (2 * LEG_A * LEG_B), -1, 1));
  const e1 = v3(0, -LEG_A - LEG_B * Math.cos(kb), -LEG_B * Math.sin(kb)).normalize(), e2 = v3(0, 0, 1).addScaledVector(e1, -e1.z).normalize(), e3 = e1.clone().cross(e2);
  const f1 = d.clone().normalize(), f2 = fw.clone().addScaledVector(f1, -fw.dot(f1)).normalize(), f3 = f1.clone().cross(f2);
  _m1.makeBasis(f1, f2, f3); _m2.makeBasis(e1, e2, e3).transpose();
  hp.quaternion.setFromRotationMatrix(_m1.multiply(_m2));
  kn.rotation.set(kb, 0, 0);
  const t = fw.clone().applyQuaternion(hp.quaternion.clone().invert()).applyAxisAngle(v3(1, 0, 0), -kb);
  ft.rotation.set(Math.atan2(-t.y, t.z) + (f.heel ?? 0), 0, 0);
}

// ------------------------------------------------------------------ poses
const C_SET = { ...CROUCH, shL: [62, 18, 0], elL: 40, shR: [20, 10, 0], elR: 50, nod: -18 };
const U_SET = { drop: -1.0, lean: 30, nod: -6, hipL: [52, 28], hipR: [52, 28], knL: 68, knR: 68, shL: [30, 20, 0], elL: 60, shR: [30, 20, 0], elR: 60 };
const BAT_SET = { drop: -0.35, lean: 18, look: 80, nod: -4, hipL: [22, 14], hipR: [22, 14], knL: 26, knR: 26, shL: [55, 6, 0], shR: [60, 34, 0], elL: 95, elR: 110, twist: 20 };
// the pitcher (legs come from the IK; drop sets how low his hips are)
const P_SETW = { drop: -0.22, lean: 4, look: 112, twist: 14, nod: 2, shL: [42, 8, 0], elL: 105, shR: [38, -4, 0], elR: 112 };      // set, hands together, looking over his shoulder at the runner
const P_OFF = { ...P_SETW, drop: -0.3, lean: 2, look: 100 };                                                                    // stepped off: upright, still watching
const PO_TURN = { drop: -0.32, lean: 6, look: 0, twist: -30, shL: [70, 30, 0], elL: 40, shR: [40, 40, 0], elR: 95 };              // turned, side on to first
const PO_STRIDE = { drop: -0.5, lean: 10, look: 0, twist: -45, shL: [80, 35, 0], elL: 25, shR: [-35, 85, 0], elR: 90 };            // stride foot down, arm back
const PO_REL = { drop: -0.72, lean: 30, nod: 6, twist: 22, shL: [12, 32, 0], elL: 85, shR: [165, 22, 0], elR: 10 };
const PO_FOLLOW = { drop: -0.85, lean: 44, nod: 14, twist: 40, shL: [8, 38, 0], elL: 95, shR: [58, -24, 0], elR: 22 };
const PO_WATCH = { drop: -0.3, lean: 8, nod: 4, look: 10, shL: [20, 20, 0], elL: 40, shR: [12, 10, 0], elR: 30 };
// the runner
const R_LEAD = { drop: -0.7, lean: 26, nod: -14, hipL: [40, 24], hipR: [40, 24], knL: 50, knR: 50, shL: [18, 16, 0], shR: [18, 16, 0], elL: 25, elR: 25 };
const R_DIVE = { drop: -2.62, pelvisTilt: 84, lean: 0, nod: -62, hipL: [2, 6], hipR: [2, 6], knL: 12, knR: 26, shL: [176, 6, 0], elL: 4, shR: [176, 6, 0], elR: 4 };
const R_DIVE0 = { drop: -1.2, pelvisTilt: 40, lean: 20, nod: -40, hipL: [20, 6], hipR: [-10, 6], knL: 30, knR: 40, shL: [150, 8, 0], elL: 10, shR: [150, 8, 0], elR: 10 };
const R_UP = { drop: -1.3, pelvisTilt: 0, lean: 40, nod: -10, hipL: [80, 10], hipR: [60, 10], knL: 100, knR: 90, shL: [40, 20, 0], elL: 40, shR: [40, 20, 0], elR: 40 };
// the first baseman holding the runner, then leaping for the throw
const B_HOLD = { drop: -0.45, lean: 16, nod: -4, hipL: [26, 20], hipR: [26, 20], knL: 32, knR: 32, shL: [60, 18, 0], elL: 70, shR: [24, 10, 0], elR: 50 };
const B_LEAP = { drop: 0.0, lean: 4, nod: 22, side: -16, look: 30, hipL: [30, 26], hipR: [-6, 10], knL: 60, knR: 20, shL: [150, 58, 0], elL: 6, shR: [30, 30, 0], elR: 40 };
const B_LAND = { drop: -0.9, lean: 22, nod: 10, look: 40, hipL: [40, 20], hipR: [40, 20], knL: 60, knR: 60, shL: [60, 30, 0], elL: 30, shR: [30, 20, 0], elR: 40 };
// the first-base umpire: hands on knees; both arms up (dead ball); points to the base awarded
const U1_SET = { drop: -0.55, lean: 30, nod: -8, hipL: [38, 20], hipR: [38, 20], knL: 48, knR: 48, shL: [34, 16, 0], elL: 24, shR: [34, 16, 0], elR: 24 };
const U1_UP = { ...STAND, lean: 0, nod: 4, shL: [10, 10, 0], elL: 20, shR: [10, 10, 0], elR: 20 };
const U1_DEAD = { ...STAND, lean: -2, nod: 6, shL: [176, 14, 0], elL: 6, shR: [176, 14, 0], elR: 6 };
const U1_POINT = { ...STAND, lean: 2, nod: 0, shR: [92, 2, 0], elR: 2, shL: [10, 10, 0], elL: 20 };

// ------------------------------------------------------------------ the two plays. t = 0 is the release of the throw.
// "on":  he stays on the rubber: the pivot (right) foot turns on the rubber and stays in contact; the free (left) foot steps
//        directly toward first; he throws. The throw goes into the first-base dugout: 1 base (OBR 5.06(b)(4)(H)).
// "off": the pivot (right) foot steps backward off the rubber first (now an infielder, OBR 5.07(e)); then he turns, steps toward
//        first with the free foot and throws. Same throw, into the dugout: 2 bases, as a wild throw by an infielder (5.06(b)(4)(G)).
const TO1 = B1.clone().sub(v3(0, 0, RUBBER_Z)).setY(0).normalize(), TO2 = B2.clone().sub(B1).normalize(), TO3 = B3.clone().sub(B2).normalize();
const PIV0 = v3(-0.32, RUB_TOP, RUBBER_Z + 0.02);                   // the ball of the pivot foot on the rubber, toes toward third
const FREE0 = v3(-0.45, MOUND_H, -58.3);                             // the free foot, toward home
const BACK = v3(-0.22, moundY(-0.22, -61.95), -61.95);               // where the pivot foot lands behind the rubber
const LAND = { on: PIV0.clone().addScaledVector(TO1, 2.9), off: BACK.clone().addScaledVector(TO1, 2.9) };
for (const k in LAND) LAND[k].y = moundY(LAND[k].x, LAND[k].z);
const YAW0 = -Math.PI / 2, OPEN = YAW0 + 0.32;
const T_OFF = [-1.32, -0.98];                                        // "off": the pivot foot's step back (lift, down)
const T_TURN = [-0.62, -0.3];                                        // the turn and the step toward first
const L1 = B1.clone().addScaledVector(TO2, 11.5);                    // the runner's lead
const B1S = v3(62.2, 0, -62.6);                                      // the first baseman holding the runner
const U1P = v3(78.4, 0, -70.0);                                      // the first-base umpire, behind the bag in foul territory
// the throw: 0.9 s, about 75 mph, high and wide of the bag toward the home side, into the first-base dugout
const T_TH = 0.9;
const DG_IN = dg1.localToWorld(v3(-27, 3.9, 0)), DG_WALL = dg1.localToWorld(v3(-28.3, 3.0, -4.85)), DG_FLOOR = dg1.localToWorld(v3(-27.6, 0.13, -3.6)), DG_REST = dg1.localToWorld(v3(-25.4, 0.13, -1.8));
const T_DEAD = 1.35, T_AWARD = 2.45;                                  // the umpire's arms go up; he points to the base; the runner goes
const REL = {};                                                       // the hand at release, per play (filled in at load)

function pitcherFeet(play, t) {
  // pivot (right) foot
  let piv, pivYaw, pivHeel = 0, onRubber = true;
  if (play === "on") {
    piv = PIV0.clone();
    pivYaw = kf([[T_TURN[0], YAW0], [T_TURN[1], 0], [0.05, 0.55], [0.5, 0.75]], t);
    pivHeel = kf([[-0.3, 0], [0, 0.38], [0.35, 0.55], [1.2, 0.4]], t);
  } else {
    const u = clamp((t - T_OFF[0]) / (T_OFF[1] - T_OFF[0]), 0, 1);
    piv = PIV0.clone().lerp(BACK, easeIO(u)); piv.y = lerp(PIV0.y, BACK.y, easeIO(u)) + 0.42 * Math.sin(Math.PI * u);
    pivYaw = kf([[T_TURN[0], YAW0], [T_TURN[1], 0], [0.05, 0.55], [0.5, 0.75]], t);
    pivHeel = kf([[-0.3, 0], [0, 0.38], [0.35, 0.55], [1.2, 0.4]], t);
    onRubber = u <= 0.02;
  }
  // free (left) foot: steps directly toward first
  const u = clamp((t - T_TURN[0]) / (T_TURN[1] - T_TURN[0]), 0, 1), land = LAND[play];
  const free = FREE0.clone().lerp(land, easeIO(u)); free.y = lerp(FREE0.y, land.y, u) + 0.75 * Math.sin(Math.PI * Math.min(1, u * 1.05));
  const freeYaw = lerp(OPEN, Math.PI / 2 - 0.15, easeIO(u));
  return { piv: { ball: piv, yaw: pivYaw, heel: pivHeel }, free: { ball: free, yaw: freeYaw, heel: 0 }, onRubber };
}
function pitcherPose(play, t) {
  const turn = [[T_TURN[0] - 0.05, play === "on" ? P_SETW : P_OFF], [T_TURN[0] + 0.16, PO_TURN], [T_TURN[1], PO_STRIDE], [0, PO_REL], [0.3, PO_FOLLOW], [1.1, PO_WATCH]];
  if (play === "on") return keyed([[-9, P_SETW], ...turn], t);
  return keyed([[-9, P_SETW], [T_OFF[0], P_SETW], [T_OFF[1] + 0.1, P_OFF], ...turn], t);
}
const pitcherYaw = (play, t) => kf([[T_TURN[0], YAW0], [T_TURN[1], 0.05], [0.04, Math.PI / 2], [0.45, Math.PI / 2 + 0.25], [1.4, Math.PI / 2 + 0.6]], t);

// runner: a lead; dives back on the move; gets up on the bag; jogs to the base he's awarded
function runnerAt(play, t, s) {
  const tl = s.leadAt ?? -4.2;                                         // the shuffle out to his lead
  let p = B1.clone(), yaw = yawTo(L1, v3(0, 0, -60)), q = { ...R_LEAD, look: 0 };
  if (t < tl + 1.3) { const u = clamp((t - tl) / 1.3, 0, 1); p = B1.clone().addScaledVector(TO2, 1.2).lerp(L1, easeIO(u)); q = mixPose({ ...STAND, lean: 10 }, R_LEAD, Math.min(1, u * 2)); if (u > 0 && u < 1) q = mixPose(q, { ...q, hipL: [30, 40], hipR: [44, 12] }, Math.sin(u * Math.PI * 4) ** 2); return { p, yaw, q }; }
  const tg = T_TURN[0] + 0.06;                                         // he reacts to the move toward first
  if (t < tg) return { p: L1.clone(), yaw, q };
  const RD = B1.clone().addScaledVector(TO2, 3.7);                     // where his hips lie when his hands are on the bag
  if (t < tg + 0.75) {
    const u = (t - tg) / 0.75, dyaw = yawTo(L1, B1);
    p = L1.clone().lerp(RD, easeIO(u)); yaw = dyaw;
    q = u < 0.45 ? mixPose(runPose(u * 2.2 % 1, 0.8), R_DIVE0, smooth((u - 0.25) / 0.2)) : mixPose(R_DIVE0, R_DIVE, smooth((u - 0.45) / 0.3));
    return { p, yaw, q };
  }
  const tu = 1.35;                                                     // up on the bag after the ball's gone
  if (t < tu) return { p: RD, yaw: yawTo(L1, B1), q: R_DIVE };
  if (t < tu + 0.7) { const u = (t - tu) / 0.7; return { p: RD.clone().lerp(B1.clone().addScaledVector(TO2, 0.6), easeIO(u)), yaw: lerp(yawTo(L1, B1), yawTo(B1, B2), smooth(u)), q: u < 0.5 ? mixPose(R_DIVE, R_UP, smooth(u * 2)) : mixPose(R_UP, { ...STAND, look: -30 }, smooth(u * 2 - 1)) }; }
  // the award: a trot to second (one base) or around second to third (two bases)
  const START = B1.clone().addScaledVector(TO2, 0.6), legs = play === "on" ? [START, B2] : [START, B2, B3];
  const total = legs.reduce((a, b, i) => (i ? a + legs[i - 1].distanceTo(b) : 0), 0) - 0.8;
  const d = Math.min(total, sprint(t - T_AWARD - 0.1, 19.5, 0.9));
  if (t < T_AWARD + 0.1) return { p: START, yaw: yawTo(B1, B2), q: { ...STAND, look: t > T_AWARD - 0.6 ? 70 : -30 } };
  let rem = d, a = legs[0], b = legs[1], k = 1;
  while (k < legs.length - 1 && rem > a.distanceTo(b)) { rem -= a.distanceTo(b); a = legs[k]; b = legs[++k]; }
  p = a.clone().lerp(b, rem / a.distanceTo(b)); yaw = yawTo(a, b);
  if (legs.length === 3) {                                             // round second smoothly
    const dc = d - legs[0].distanceTo(legs[1]), w = smooth((dc + 7) / 14);
    yaw = lerp(yawTo(legs[0], legs[1]), yawTo(legs[1], legs[2]), w);
    if (Math.abs(dc) < 7) p.addScaledVector(v3(0, 0, -1), 1.6 * Math.cos(dc / 7 * Math.PI / 2) ** 2);
  }
  const arrived = d >= total - 0.01;
  q = arrived ? { ...STAND, look: -20 } : runPose((d / 9.5) % 1, 0.7);
  return { p, yaw, q };
}

// ------------------------------------------------------------------ graphics: the ball, the rubber, the pivot foot, arrows
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
function arrow(color, dashed, w = 0.42) {                          // a flat arrow on the ground from a to b
  const g = new THREE.Group(), m = flatMat(color, 0.92), segs = [];
  const n = dashed ? 7 : 1;
  for (let i = 0; i < n; i++) { const s = new THREE.Mesh(new THREE.PlaneGeometry(1, w), m); s.rotation.x = -Math.PI / 2; s.renderOrder = 8; g.add(s); segs.push(s); }
  const hw = w * 1.8, hl = w * 3.1;
  const head = new THREE.Mesh(new THREE.ShapeGeometry(new THREE.Shape([new THREE.Vector2(0, -hw), new THREE.Vector2(hl, 0), new THREE.Vector2(0, hw)])), m); head.rotation.x = -Math.PI / 2; head.renderOrder = 8; g.add(head);
  g.visible = false; scene.add(g);
  g.userData.set = (a, b, u = 1) => {
    const d = b.clone().sub(a), L = Math.max(0.01, d.length() * u), yaw = -Math.atan2(d.z, d.x); g.position.copy(a); g.rotation.set(0, yaw, 0);
    segs.forEach((s, i) => { const f0 = n > 1 ? i / n : 0, f1 = n > 1 ? (i + 0.6) / n : 1; s.position.set((f0 + f1) / 2 * Math.max(0.01, L - hl), 0, 0); s.scale.set(Math.max(0.01, (f1 - f0) * (L - hl)), 1, 1); });
    head.position.set(L - hl, 0, 0); g.visible = u > 0;
  };
  return g;
}
const AR_STEP = arrow(0xf4f6f8, false, 0.16), AR_BACK = arrow(0xff6a3d, false, 0.16), AR_A1 = arrow(0xffd84d, false), AR_A2 = arrow(0xffd84d, false);
const RUB = new THREE.Mesh(new THREE.BoxGeometry(2.12, 0.16, 0.62), flatMat(0xffd84d, 0.55)); RUB.position.set(0, MOUND_H + 0.05, RUBBER_Z); RUB.renderOrder = 6; RUB.visible = false; scene.add(RUB);
const PIVR = new THREE.Mesh(new THREE.RingGeometry(0.62, 0.74, 48), flatMat(0x56d1ff, 0.95)); PIVR.rotation.x = -Math.PI / 2; PIVR.renderOrder = 9; PIVR.visible = false; scene.add(PIVR);
const GAP = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), flatMat(0xff3d2e, 0.85)); GAP.rotation.x = -Math.PI / 2; GAP.renderOrder = 9; GAP.visible = false; scene.add(GAP);

// ------------------------------------------------------------------ one frame
function setScene(t, s) {
  const play = s.play ?? "on";
  for (const [k, p] of Object.entries(HD)) { const [x, z] = homeD[k]; p.root.position.set(x, 0, z); p.root.rotation.y = Math.atan2(-x, -z); applyPose(p, READY); }
  ump.root.position.set(0.5, 0, 6.4); ump.root.rotation.y = Math.PI + 0.02; applyPose(ump, U_SET);
  batter.root.position.set(-3.0, 0, -0.9); batter.root.rotation.y = Math.PI / 2; batter.bat.visible = true; applyPose(batter, BAT_SET);
  C.root.position.set(0.15, 0, 3.0); C.root.rotation.y = Math.PI; applyPose(C, C_SET);
  // the pitcher
  const ft = pitcherFeet(play, t);
  const aP = footAnkle(ft.piv), aF = footAnkle(ft.free);
  const yaw = pitcherYaw(play, t);
  const mid = aP.clone().lerp(aF, 0.5);
  pitcher.root.position.set(mid.x, MOUND_H, mid.z); pitcher.root.rotation.y = yaw;
  applyPose(pitcher, pitcherPose(play, t));
  legIK(pitcher, "R", ft.piv); legIK(pitcher, "L", ft.free);
  // the ball
  let bp = null, trail = null;
  if (t < 0) bp = wpos(pitcher.handR);
  else {
    const a = REL[play] ?? wpos(pitcher.handR);
    const at = (u) => {
      if (u < T_TH) return arcAt(a, DG_IN, T_TH, u);
      const w = u - T_TH;
      if (w < 0.07) return DG_IN.clone().lerp(DG_WALL, w / 0.07);
      if (w < 0.42) { const v = (w - 0.07) / 0.35; const p = DG_WALL.clone().lerp(DG_FLOOR, v); p.y = lerp(DG_WALL.y, DG_FLOOR.y, v * v); return p; }
      const v = clamp((w - 0.42) / 1.4, 0, 1); return DG_FLOOR.clone().lerp(DG_REST, 1 - (1 - v) ** 2);
    };
    bp = at(t); trail = (d) => (t - d > 0 && t - d < T_TH + 0.1 ? at(t - d) : null);
  }
  placeBall(bp, trail);
  // the first baseman: holds the runner; leaps toward the line for the throw and misses; lands and turns to watch it go
  const tl = 0.5;
  const leapU = clamp((t - (tl - 0.3)) / 0.75, 0, 1), side = TO2.clone().multiplyScalar(-1).cross(v3(0, 1, 0)).normalize();
  const bpos = B1S.clone().add(v3(-0.4, 0, 3.0).multiplyScalar(smooth(leapU))); bpos.y = 1.1 * Math.sin(Math.PI * clamp((t - (tl - 0.2)) / 0.5, 0, 1));
  B1F.root.position.copy(bpos); B1F.root.rotation.y = lerp(yawTo(B1S, MOUND), yawTo(B1S, DG_IN) - 0.3, smooth((t - 0.6) / 0.6));
  applyPose(B1F, keyed([[-9, B_HOLD], [tl - 0.28, B_HOLD], [tl - 0.02, B_LEAP], [tl + 0.3, B_LEAP], [tl + 0.55, B_LAND], [tl + 1.3, { ...STAND, look: 0, lean: 6 }]], t));
  // the first-base umpire: dead ball, then points the runner to the base he's awarded
  const awardTo = play === "on" ? B2 : B3;
  U1.root.position.copy(U1P);
  U1.root.rotation.y = kf([[0.6, yawTo(U1P, v3(20, 0, -60))], [1.0, yawTo(U1P, DG_IN) - 0.4], [T_AWARD - 0.3, yawTo(U1P, DG_IN) - 0.4], [T_AWARD, yawTo(U1P, awardTo) + 0.25]], t);
  applyPose(U1, keyed([[-9, U1_SET], [0.55, U1_SET], [0.95, U1_UP], [T_DEAD - 0.15, U1_UP], [T_DEAD + 0.12, U1_DEAD], [T_AWARD - 0.35, U1_DEAD], [T_AWARD - 0.1, U1_UP], [T_AWARD + 0.15, U1_POINT], [T_AWARD + 1.8, U1_POINT], [T_AWARD + 2.4, U1_UP]], t));
  // the runner
  const r = runnerAt(play, t, s); R.root.position.copy(r.p); R.root.rotation.y = r.yaw; applyPose(R, r.q);
  // graphics
  const rv = (k, dur = 0.35) => (s[k] != null ? clamp((t - s[k]) / dur, 0, 1) : 0);
  RUB.visible = s.rub != null && t >= s.rub; if (RUB.visible) RUB.material.opacity = 0.42 + 0.2 * Math.sin(t * 9);
  PIVR.visible = s.pivr != null && t >= s.pivr;
  if (PIVR.visible) { const b = ft.piv.ball, c = b.clone().add(v3(Math.sin(ft.piv.yaw), 0, Math.cos(ft.piv.yaw)).multiplyScalar(-0.2)); PIVR.position.set(c.x, (ft.onRubber ? RUB_TOP : moundY(c.x, c.z)) + 0.035, c.z); PIVR.material.color.set(ft.onRubber ? 0x56d1ff : 0xff6a3d); }
  GAP.visible = s.gap != null && t >= s.gap && play === "off";
  if (GAP.visible) { const z0 = RUB_Z0, z1 = BACK.z + 0.24, g = rv("gap", 0.3); GAP.scale.set(2.0, Math.max(0.01, (z0 - z1) * g), 1); GAP.position.set(BACK.x + 0.3, moundY(0, (z0 + z1) / 2) + 0.06, z0 - (z0 - z1) * g / 2); }
  AR_STEP.visible = AR_BACK.visible = AR_A1.visible = AR_A2.visible = false;
  if (s.arStep != null) { const a = (play === "on" ? PIV0 : BACK).clone().setY((play === "on" ? RUB_TOP : BACK.y) + 0.06); AR_STEP.userData.set(a.clone().addScaledVector(TO1, 0.4), a.clone().addScaledVector(TO1, 4.2), rv("arStep")); }
  if (s.arBack != null && play === "off") { const a = v3(BACK.x + 0.35, RUB_TOP + 0.04, RUB_Z1 + 0.1); AR_BACK.userData.set(a, v3(BACK.x + 0.35, BACK.y + 0.08, BACK.z - 0.55), rv("arBack")); }
  if (s.arAdv != null) {
    const y = 0.12, u = rv("arAdv", 0.5);
    AR_A1.userData.set(B1.clone().addScaledVector(TO2, 3).setY(y), B2.clone().addScaledVector(TO2, -3).setY(y), play === "on" ? u : clamp(u * 2, 0, 1));
    if (play === "off") AR_A2.userData.set(B2.clone().addScaledVector(TO3, 3).setY(y), B3.clone().addScaledVector(TO3, -3).setY(y), clamp(u * 2 - 1, 0, 1));
  }
}
for (const play of ["on", "off"]) { setScene(0, { play }); REL[play] = wpos(pitcher.handR); }

// ------------------------------------------------------------------ cameras
const cam = new THREE.PerspectiveCamera(40, W / H, 0.05, 3000);
function frame(c, pos, look, fov, aspect) { c.position.copy(pos); c.fov = fov; c.aspect = aspect; c.updateProjectionMatrix(); c.lookAt(look); }
const mixV = (a, b, u) => a.clone().lerp(b, u);
const A_ = (a) => v3(a[0], a[1], a[2]);
const pw = (v, vs, ts) => {
  if (v <= vs[0]) return ts[0];
  for (let i = 1; i < vs.length; i++) if (v <= vs[i]) return lerp(ts[i - 1], ts[i], (v - vs[i - 1]) / (vs[i] - vs[i - 1]));
  return ts.at(-1);
};
const rateAt = (v, vs, ts) => { for (let i = 1; i < vs.length; i++) if (v <= vs[i] || i === vs.length - 1) return (ts[i] - ts[i - 1]) / Math.max(1e-6, vs[i] - vs[i - 1]); return 1; };
const OBJ = { pivot: () => footAnkle(pitcherFeet(CUR.play, CUR.t).piv), pitcher: () => wpos(pitcher.pelvis), runner: () => wpos(R.pelvis), ball: () => BALL.m.position.clone(), b1: () => wpos(B1F.pelvis), u1: () => wpos(U1.pelvis) };
const CAMS = {
  // a fixed or moving camera: c0 -> c1, looking at l -> l1, field of view f0 -> f1 (eased over the shot)
  world: (u, s) => [mixV(A_(s.c0), A_(s.c1 ?? s.c0), easeIO(u)), mixV(A_(s.l), A_(s.l1 ?? s.l), easeIO(u)), lerp(s.f0 ?? 36, s.f1 ?? s.f0 ?? 36, easeIO(u))],
  // the same, but turning to follow an object (s.fo) by s.fw
  follow: (u, s) => { const c = mixV(A_(s.c0), A_(s.c1 ?? s.c0), easeIO(u)), l = mixV(A_(s.l), A_(s.l1 ?? s.l), easeIO(u)); return [c, l.lerp(OBJ[s.fo](), s.fw ?? 1), lerp(s.f0 ?? 36, s.f1 ?? s.f0 ?? 36, easeIO(u))]; },
};
let CUR = { play: "on", t: 0 };
function shotAt(v) {
  const L = CC.shots.list;
  const s = L.find((x) => v < x.b) || L.at(-1);
  return { s, u: clamp((v - s.a) / (s.b - s.a), 0, 1) };
}

// ------------------------------------------------------------------ DOM overlays fed from the same clock
const $ = (id) => document.getElementById(id);
const PINT = { runner: () => headTop(R), pitcher: () => headTop(pitcher), b1: () => headTop(B1F), u1: () => headTop(U1),
  rubber: () => v3(0.9, RUB_TOP + 0.15, RUBBER_Z), pivot: () => footAnkle(pitcherFeet(CUR.play, CUR.t).piv).add(v3(0, 0.75, 0)), ball: () => BALL.m.position.clone().add(v3(0, 0.6, 0)),
  dugout: () => dg1.localToWorld(v3(-24, 10.5, 6)), base2: () => B2.clone().add(v3(0, 6.5, 0)), base3: () => B3.clone().add(v3(0, 6.5, 0)), base1: () => B1.clone().add(v3(0, 6.5, 0)),
  gap: () => v3(BACK.x + 0.3, BACK.y + 0.35, (RUB_Z0 + BACK.z + 0.24) / 2) };
function pin(id, p, rect) {
  const el = $(id); if (!el || !p) return;
  const q = p.clone().project(cam), [x0, y0, w, h] = rect, half = Math.min(260, w / 2 - 8);
  el.style.left = `${clamp(x0 + (q.x + 1) / 2 * w, x0 + half, x0 + w - half).toFixed(1)}px`; el.style.top = `${clamp(y0 + (1 - q.y) / 2 * h, y0 + 40, y0 + h - 20).toFixed(1)}px`;
}
function renderAt(v) {
  const { s, u } = shotAt(v);
  const panes = s.panes ?? [{ rect: [0, 0, W, H] }];
  renderer.setScissorTest(panes.length > 1);
  let rate = 1;
  panes.forEach((pn, i) => {
    const sh = { ...s, ...pn }, t = pw(v, sh.vs, sh.ts), [x, y, w, h] = pn.rect;
    if (i === 0) rate = rateAt(v, sh.vs, sh.ts);
    CUR = { play: sh.play ?? "on", t };
    setScene(t, sh);
    const c = CAMS[sh.cam](u, sh);
    frame(cam, c[0], c[1], c[2], w / h);
    const g = c[2] < 16 ? 0.009 : 0.02; BALL.glow.scale.set(g, g, 1);
    renderer.setViewport(x, H - y - h, w, h); renderer.setScissor(x, H - y - h, w, h);
    renderer.render(scene, cam);
    for (const [id, key, pi] of CC.pins) if ((pi ?? 0) === i) pin(id, PINT[key](), pn.rect);
  });
  renderer.setScissorTest(false);
  if ($("spd")) { const sp = s.panes ? "" : rate < 0.02 ? "Freeze" : rate < 0.9 ? "Slow motion" : ""; $("spd").textContent = sp; $("spd").style.opacity = sp ? 1 : 0; }
}

let last = -1;
function seek(time) { if (time === last) return; last = time; renderAt(time); }
window.addEventListener("hf-seek", (e) => seek(e.detail.time));
window.__fieldRender = renderAt;
window.__dbg = { setScene, pitcherFeet, footAnkle, REL, DG_IN, LAND, BACK, PIV0, runnerAt, R };
document.fonts.ready.then(() => seek(window.__hfThreeTime || 0));
seek(window.__hfThreeTime || 0);
