// "The complete catcher": the field, both teams, and six plays that show a catcher's skills, in three.js.
// Everything is a pure function of HyperFrames time (hf-seek), so each frame is exact and repeatable.
// Units are feet. Home plate's back point is the origin, +x points toward first base's side, -z toward center field.
// Pitches, the ball in the dirt, the steal and the gap double come from tools/physics.py via window.__PLAY.
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


// ------------------------------------------------------------------ the cast
// our team (white): the catcher and his defense; the other team (dark): hitters, runners, and its defense when he bats
const C = makePlayer(KIT.home, { glove: true, catcher: true });                // the catcher
const CB = makePlayer(KIT.home, { helmet: true, bat: true });                  // the same catcher, batting / running
const pitcher = makePlayer(KIT.home, { glove: true });
const ump = makePlayer(KIT.ump, { catcher: true });
const hitter = makePlayer(KIT.away, { helmet: true, bat: true });              // a right-handed hitter
const runner = makePlayer(KIT.away, { helmet: true });                         // runner on first
const homeD = { b1: [61.5, -60.5], b2: [30, -128], ss: [-28, -118], b3: [-58, -76], lf: [-118, -262], cf: [0, -312], rf: [118, -262] };
const HD = {}, AD = {};
for (const [k, [x, z]] of Object.entries(homeD)) {
  HD[k] = makePlayer(KIT.home, { glove: true }); HD[k].root.position.set(x, 0, z);
  AD[k] = makePlayer(KIT.away, { glove: true }); AD[k].root.position.set(x, 0, z);
}
const awayP = makePlayer(KIT.away, { glove: true }), awayC = makePlayer(KIT.away, { glove: true, catcher: true });
for (const p of [C, CB, pitcher, ump, hitter, runner, awayP, awayC, ...Object.values(HD), ...Object.values(AD)]) scene.add(p.root);
// fingers for the signs (the catcher's throwing hand)
const FING = [];
for (let k = 0; k < 4; k++) { const f = new THREE.Mesh(new THREE.CapsuleGeometry(0.035, 0.22, 4, 6), new THREE.MeshStandardMaterial({ color: KIT.home.skin, roughness: 0.6 })); f.position.set(-0.08 + k * 0.055, -0.2, 0.02); C.handR.add(f); FING.push(f); }

// ------------------------------------------------------------------ the model (tools/physics.py)
const V = (a) => v3(a[0], a[1], a[2]);
const PI_ = PLAY.pitches, ST = PLAY.steal, DB = PLAY.double, RN = PLAY.runner, Z = PLAY.zone;
function pathAt(path, t) {
  const u = (t - path.t0) * path.hz, n = path.p.length - 1;
  if (u <= 0) return V(path.p[0]);
  if (u >= n) return V(path.p[n]);
  const i = Math.floor(u), f = u - i, a = path.p[i], b = path.p[i + 1];
  return v3(lerp(a[0], b[0], f), lerp(a[1], b[1], f), lerp(a[2], b[2], f));
}
const handPos = (h) => { h.updateWorldMatrix(true, false); return h.getWorldPosition(new THREE.Vector3()); };
const B1W = v3(63.64, 0, -63.64), B2W = v3(0, 0, -127.28);
const TO2 = B2W.clone().sub(B1W).normalize();

// ------------------------------------------------------------------ poses
// catcher (root faces the field: rotation.y = PI)
const C_SET = { ...CROUCH, shL: [62, 18, 0], elL: 40, shR: [20, 10, 0], elR: 50, nod: -18 };
const C_SIGN = { ...CROUCH, nod: -10, shL: [40, 30, 0], elL: 60, shR: [10, -15, -40], elR: 30 };          // throwing hand down between his thighs
const C_LOWAWAY = { ...CROUCH, nod: -12, shL: [58, 34, 0], elL: 16, shR: [14, 10, 0], elR: 60 };      // glove low, to his left (away from a righty)
const C_LOW = { ...CROUCH, nod: -16, shL: [54, 10, 0], elL: 22, shR: [14, 10, 0], elR: 60 };
const C_MID = { ...CROUCH, nod: -8, shL: [78, 12, 0], elL: 24, shR: [20, 10, 0], elR: 60 };
const C_BLOCK = { drop: -2.05, lean: 30, nod: 26, hipL: [8, 36], hipR: [8, 36], knL: 112, knR: 112, ankL: 40, ankR: 40, shL: [18, 6, 0], elL: 16, shR: [26, -6, 0], elR: 40 };   // on his knees, chest over the ball, glove between his legs
const C_POP = { drop: -0.6, lean: 18, nod: -2, twist: -40, hipL: [38, 14], hipR: [20, 14], knL: 44, knR: 32, shL: [70, 20, 0], elL: 40, shR: [-25, 75, 0], elR: 100 };   // up, ball to the ear
const C_STEP = { drop: -0.45, lean: 10, twist: -60, look: 0, nod: -4, hipL: [40, 10], hipR: [-12, 14], knL: 30, knR: 24, shL: [82, 20, 0], elL: 30, shR: [-35, 78, 0], elR: 95 };
const C_REL = { drop: -0.6, lean: 30, twist: 30, nod: 6, shL: [20, 30, 0], elL: 60, shR: [165, 20, 0], elR: 15, hipL: [46, 8], hipR: [-26, 10], knL: 40, knR: 30 };
const C_FOL = { drop: -0.8, lean: 46, twist: 48, nod: 10, shL: [10, 30, 0], elL: 70, shR: [55, -25, 0], elR: 25, hipL: [55, 8], hipR: [10, 10], knL: 52, knR: 70 };
// pitcher (from the stretch; t relative to release)
const P_SET = { lean: 4, look: 80, nod: 4, shL: [42, 8, 0], elL: 105, shR: [38, -4, 0], elR: 112, hipL: [4, 6], hipR: [4, 6], knL: 8, knR: 8 };
const P_NOD = { ...P_SET, nod: 16 };
const P_LIFT = { lean: -4, look: 80, shL: [48, 8, 0], elL: 100, shR: [44, -4, 0], elR: 108, hipL: [100, 4], knL: 105, hipR: [6, 6], knR: 14, drop: -0.15 };
const P_STRIDE = { lean: 6, look: 40, drop: -0.6, twist: -50, shL: [80, 35, 0], elL: 25, shR: [-55, 80, 0], elR: 85, hipL: [52, 4], knL: 28, hipR: [-28, 6], knR: 38 };
const P_REL = { lean: 42, nod: 8, drop: -1.0, twist: 28, shL: [12, 32, 0], elL: 85, shR: [168, 22, 0], elR: 8, hipL: [72, 4], knL: 22, hipR: [-18, 6], knR: 92 };
const P_FOLLOW = { lean: 62, nod: 18, drop: -1.25, twist: 48, shL: [8, 38, 0], elL: 95, shR: [58, -24, 0], elR: 22, hipL: [82, 4], knL: 38, hipR: [34, 6], knR: 84 };
function setPitcher(P, tr) {                                  // tr: time since release
  const q = keyed([[-1.3, P_SET], [-0.9, P_LIFT], [-0.35, P_STRIDE], [0, P_REL], [0.35, P_FOLLOW], [1.0, { ...READY, look: 0 }]], tr);
  const z = lerp(-60.6, -57.6, smooth((tr + 0.45) / 0.5));
  P.root.position.set(0, MOUND_H * (z > -59 ? 0.6 : 1), z); P.root.rotation.y = lerp(-Math.PI / 2, 0, smooth((tr + 0.6) / 0.6)); applyPose(P, q);
}
// hitters (right-handed, in the box on the third-base side, facing the plate)
const BAT_SET = { drop: -0.35, lean: 18, look: 80, nod: -4, hipL: [22, 14], hipR: [22, 14], knL: 26, knR: 26, shL: [55, 6, 0], shR: [60, 34, 0], elL: 95, elR: 110, twist: 20 };
const BAT_LOAD = { ...BAT_SET, twist: 34, pelvisTwist: -10, hipL: [36, 22], knL: 40 };
const BAT_HIT = { drop: -0.55, lean: 30, look: 50, nod: -12, twist: -40, pelvisTwist: 60, hipL: [24, 28], knL: 12, hipR: [18, 12], knR: 46, shL: [80, -10, 0], elL: 10, shR: [74, 10, 0], elR: 20 };
const BAT_FIN = { drop: -0.3, lean: 12, look: 20, twist: -80, pelvisTwist: 90, hipL: [16, 26], knL: 8, hipR: [6, 12], knR: 56, shL: [140, 10, 0], elL: 100, shR: [150, -40, 0], elR: 110 };
const swing = (tc) => [[tc - 0.6, BAT_SET], [tc - 0.2, BAT_LOAD], [tc, BAT_HIT], [tc + 0.3, BAT_FIN]];
// infield / runner
const SS_TAG = { drop: -1.5, lean: 50, nod: 14, hipL: [80, 30], hipR: [60, 30], knL: 96, knR: 84, shL: [60, -10, 0], elL: 10, shR: [40, 10, 0], elR: 60 };
const SS_RECV = { drop: -0.6, lean: 20, nod: -6, hipL: [36, 18], hipR: [36, 18], knL: 40, knR: 40, shL: [80, 0, 0], elL: 15, shR: [40, 10, 0], elR: 60 };
const SLIDE = { drop: -2.45, pelvisTilt: 0, lean: -48, hipL: [78, 4], hipR: [52, 4], knL: 8, knR: 62, shL: [70, 30, 0], shR: [40, 30, 0], elL: 20, elR: 30, nod: 30 };
const LEAD = { drop: -0.75, lean: 28, look: -70, hipL: [42, 22], hipR: [42, 22], knL: 52, knR: 52, shL: [18, 14, 0], shR: [18, 14, 0], elL: 25, elR: 25, nod: -18 };
const U_SET = { drop: -1.0, lean: 30, nod: -6, hipL: [52, 28], hipR: [52, 28], knL: 68, knR: 68, shL: [30, 20, 0], elL: 60, shR: [30, 20, 0], elR: 60 };
const U_STRIKE = { drop: -0.3, lean: 8, twist: 20, shR: [80, 70, 0], elR: 90, shL: [20, 20, 0], elL: 40, hipL: [16, 14], hipR: [16, 14], knL: 20, knR: 20 };

// ------------------------------------------------------------------ the ball, the strike zone, marks
function makeBall() {
  const m = new THREE.Mesh(new THREE.SphereGeometry(0.13, 16, 12), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffe9b0, emissiveIntensity: 0.7, roughness: 0.4 }));
  m.castShadow = true; scene.add(m);
  const gt = canvasTex(64, 64, (g, w) => { const gr = g.createRadialGradient(w / 2, w / 2, 0, w / 2, w / 2, w / 2); gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(0.35, "rgba(255,255,255,.55)"); gr.addColorStop(1, "rgba(255,255,255,0)"); g.fillStyle = gr; g.fillRect(0, 0, w, w); });
  const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: gt, color: 0xffd84d, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: false }));
  glow.scale.set(0.022, 0.022, 1); scene.add(glow);
  const trail = [];
  for (let i = 0; i < 26; i++) { const tr = new THREE.Mesh(new THREE.SphereGeometry(0.1 * (1 - i / 26) + 0.02, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffd84d, transparent: true, opacity: 0.45 * (1 - i / 26), depthWrite: false })); scene.add(tr); trail.push(tr); }
  return { m, glow, trail };
}
const BALL = makeBall();
function placeBall(pos, path, t) {
  BALL.m.position.copy(pos); BALL.glow.position.copy(pos);
  for (let i = 0; i < BALL.trail.length; i++) { const q = t - (i + 1) * 0.008, tr = BALL.trail[i]; tr.visible = !!path && q > path.t0 && t < path.t0 + path.dur; if (tr.visible) tr.position.copy(pathAt(path, q)); }
}
const zoneG = new THREE.Group(), zoneMat = new THREE.MeshBasicMaterial({ color: 0xf4f6f8, transparent: true, opacity: 0.85, depthWrite: false });
{
  const hw = Z.half_w, b = Z.bot, tp = Z.top, z = Z.z, w = 0.035;
  const bar = (x0, y0, x1, y1, m = zoneMat, ww = w) => { const len = Math.hypot(x1 - x0, y1 - y0); const g = new THREE.Mesh(new THREE.BoxGeometry(Math.abs(x1 - x0) > 0.01 ? len : ww, Math.abs(y1 - y0) > 0.01 ? len : ww, ww), m); g.position.set((x0 + x1) / 2, (y0 + y1) / 2, z); zoneG.add(g); };
  bar(-hw, b, hw, b); bar(-hw, tp, hw, tp); bar(-hw, b, -hw, tp); bar(hw, b, hw, tp);
  const faint = new THREE.MeshBasicMaterial({ color: 0xf4f6f8, transparent: true, opacity: 0.25, depthWrite: false });
  for (const k of [1, 2]) { bar(-hw + 2 * hw * k / 3, b, -hw + 2 * hw * k / 3, tp, faint, 0.02); bar(-hw, b + (tp - b) * k / 3, hw, b + (tp - b) * k / 3, faint, 0.02); }
}
zoneG.visible = false; scene.add(zoneG);
const chase = new THREE.Mesh(new THREE.PlaneGeometry(1.15, 1.25), new THREE.MeshBasicMaterial({ color: 0xff6a3d, transparent: true, opacity: 0.32, depthWrite: false, side: THREE.DoubleSide }));
chase.position.set(Z.half_w + 0.55, Z.bot - 0.55, Z.z); chase.visible = false; scene.add(chase);       // low and away from a right-handed hitter: where he chases
const mark = (color) => { const m = new THREE.Mesh(new THREE.CircleGeometry(0.13, 20), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.95, depthWrite: false, side: THREE.DoubleSide })); m.visible = false; scene.add(m); return m; };
const MARK = { slider: mark(0xffd84d), fastball: mark(0x56d1ff) };
for (const [k, m] of Object.entries(MARK)) { const p = PI_[k].at_plate; m.position.set(p[0], p[1], Z.z + 0.02); }
const targetRing = new THREE.Mesh(new THREE.RingGeometry(0.16, 0.24, 24), new THREE.MeshBasicMaterial({ color: 0x56d1ff, transparent: true, opacity: 0.9, depthWrite: false, side: THREE.DoubleSide }));
targetRing.position.set(PI_.slider.at_plate[0], PI_.slider.at_plate[1], Z.z + 0.03); targetRing.visible = false; scene.add(targetRing);
function tube(points, color, width, opacity = 0.85) {
  const g = new THREE.Group();
  for (let i = 0; i < points.length - 1; i++) { const a = points[i], b = points[i + 1], len = a.distanceTo(b); const m = new THREE.Mesh(new THREE.BoxGeometry(width, width, len + 0.02), new THREE.MeshBasicMaterial({ color, transparent: true, opacity, depthWrite: false })); m.position.set((a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2); m.lookAt(b.x, b.y, b.z); m.userData.u = (i + 1) / (points.length - 1); g.add(m); }
  g.visible = false; scene.add(g); return g;
}
function reveal(g, u) { g.visible = u > 0; for (const m of g.children) m.visible = m.userData.u <= u + 1e-6; }
const SLIDER_TUBE = tube(Array.from({ length: 41 }, (_, i) => pathAt(PI_.slider.path, PI_.slider.path.t0 + PI_.slider.path.dur * i / 40)), 0xffd84d, 0.06);
const THROW_TUBE = tube(Array.from({ length: 41 }, (_, i) => pathAt(ST.throw, ST.throw.t0 + ST.throw.dur * i / 40)), 0x56d1ff, 0.1);
const HIT_TUBE = tube(Array.from({ length: 81 }, (_, i) => pathAt(DB.path, DB.path.dur * i / 80)), 0xffd84d, 0.6);

// ------------------------------------------------------------------ the plays (t = 0: pitch in the glove, or contact for "hit"/"run")
// s.play: "sign" | "slider" | "frame" | "block" | "steal" | "hit" | "run";  s.show: { zone, chase, marks, target, slider, throwPath, hitPath }
function setTeams(batting) {
  for (const p of Object.values(HD)) p.root.visible = !batting;
  for (const p of Object.values(AD)) p.root.visible = batting;
  C.root.visible = pitcher.root.visible = !batting; awayP.root.visible = awayC.root.visible = batting; CB.root.visible = batting;
  hitter.root.visible = !batting;
}
function idleDefense(D, t) {
  for (const [k, p] of Object.entries(D)) { const [x, z] = homeD[k]; p.root.position.set(x, 0, z); p.root.rotation.y = Math.atan2(-x, -z); applyPose(p, t > -0.3 ? READY : STAND); }
}
function setScene(t, s) {
  const play = s.play, batting = play === "hit" || play === "run";
  setTeams(batting);
  ump.root.position.set(0.5, 0, 6.0); ump.root.rotation.y = Math.PI;
  applyPose(ump, s.strike && t > 0.35 ? mixPose(U_SET, U_STRIKE, smooth((t - 0.35) / 0.25)) : U_SET);
  runner.root.visible = false; for (const f of FING) f.visible = false;
  zoneG.visible = !!s.show?.zone; chase.visible = !!s.show?.chase; targetRing.visible = !!s.show?.target;
  for (const [k, m] of Object.entries(MARK)) m.visible = !!s.show?.marks?.includes(k);
  reveal(SLIDER_TUBE, s.show?.slider ? 1 : 0); reveal(THROW_TUBE, 0); reveal(HIT_TUBE, 0);
  if (batting) return setBatting(t, s);
  idleDefense(HD, t);
  C.root.position.set(0.15, 0, 3.0); C.root.rotation.y = Math.PI;
  hitter.root.position.set(-3.0, 0, -0.9); hitter.root.rotation.y = Math.PI / 2; applyPose(hitter, BAT_SET);
  const pk = { sign: "slider", slider: "slider", frame: "fastball", block: "curve_dirt", steal: "steal" }[play];
  const P = PI_[pk], flight = P.flight ?? P.path.dur;
  setPitcher(pitcher, t + flight);
  if (play === "sign") {                                       // the sign, the nod
    for (let k = 0; k < FING.length; k++) FING[k].visible = k < 2;
    applyPose(C, C_SIGN); applyPose(pitcher, keyed([[-9, P_SET], [s.nodAt ?? 9, P_SET], [(s.nodAt ?? 9) + 0.2, P_NOD], [(s.nodAt ?? 9) + 0.45, P_SET]], t));
    placeBall(handPos(pitcher.handR), null, t); return;
  }
  // the catcher
  const recv = { slider: C_LOWAWAY, frame: C_LOW, steal: C_MID, block: C_SET }[play];
  let cq;
  if (play === "block") {
    cq = keyed([[-0.32, C_SET], [-0.08, C_BLOCK], [1.2, C_BLOCK], [1.7, C_SET]], t);
    C.root.position.z = 3.0 - 0.9 * smooth((t + 0.3) / 0.25);        // drops forward onto his knees
  } else if (play === "steal") {
    cq = keyed([[-0.45, C_SET], [0, recv], [0.18, C_POP], [0.5, C_STEP], [ST.t_release, C_REL], [ST.t_release + 0.4, C_FOL]], t);
    C.root.position.z = 3.0 - 2.6 * smooth((t - 0.1) / 0.7);          // footwork toward second
  } else {
    cq = keyed([[-0.45, play === "frame" ? C_LOW : C_SET], [-0.03, recv], [0.5, recv], [1.0, recv], [1.5, C_SET]], t);   // a quiet glove: there, and held
  }
  if (play === "slider") applyPose(hitter, keyed(swing(-0.04), t));          // chases it: the swing goes over the top
  applyPose(C, cq);
  // the ball
  let bp, path = P.path;
  if (t < -flight - 0.05) { bp = handPos(pitcher.handR); path = null; }
  else if (play === "block") {
    if (t < 0) bp = pathAt(P.path, t);
    else { const a = V(P.at_end), b = v3(a.x + 0.2, 0.13, a.z - 2.6), u = clamp(t / 0.7, 0, 1); bp = a.clone().lerp(b, 1 - Math.pow(1 - u, 2)); bp.y = Math.max(0.13, lerp(a.y, 0.13, u) + 0.35 * Math.sin(Math.PI * clamp(u * 1.6, 0, 1))); path = null; }
  } else if (t < 0) bp = pathAt(P.path, t);
  else if (play === "steal") {
    if (t < 0.25) bp = handPos(C.handL);
    else if (t < ST.t_release) bp = handPos(C.handR);
    else if (t < ST.t_tag) { bp = pathAt(ST.throw, t); path = ST.throw; if (t < ST.t_release + 0.05) bp = handPos(C.handR).lerp(bp, (t - ST.t_release) / 0.05); }
    else bp = handPos(HD.ss.handL);
  } else { bp = handPos(C.handL); path = null; }
  placeBall(bp, path, t);
  // runner on first: leads; on the steal he goes; on the block he takes two steps and gets back
  if (play === "block" || play === "steal") {
    runner.root.visible = true;
    const lead = B1W.clone().addScaledVector(TO2, 12);
    if (play === "block") {
      const d = 12 + 4 * smooth((t + 1.2) / 0.9) + 3 * smooth((t + 0.05) / 0.3) - 15.5 * smooth((t - 0.45) / 1.0);
      runner.root.position.copy(B1W).addScaledVector(TO2, d); runner.root.rotation.y = Math.atan2(TO2.x, TO2.z) + (t > 0.4 ? Math.PI : 0);
      applyPose(runner, t > 0.45 && t < 1.45 ? runPose(((t - 0.45) * 2.6) % 1, 0.55) : { ...LEAD, look: t > 0.4 ? 0 : -70 });
    } else {
      const u = (t - ST.run.t0) * ST.run.hz, s_ = ST.run.s[clamp(Math.floor(u), 0, ST.run.s.length - 1)];
      const L = ST.run_len, d = 13 + Math.min(s_, L + 1.2);
      runner.root.position.copy(B1W).addScaledVector(TO2, d); runner.root.rotation.y = Math.atan2(TO2.x, TO2.z);
      const slideFrom = L - 9;
      let q = t < ST.go ? LEAD : runPose((s_ / 11) % 1, clamp(s_ / 25, 0.3, 1));
      if (s_ > slideFrom) q = mixPose(q, SLIDE, smooth((s_ - slideFrom) / 3));
      applyPose(runner, q);
      // shortstop covers the bag, takes the throw, puts the tag down
      const ssAt = v3(-28, 0, -118).lerp(v3(-1.6, 0, -126.2), smooth((t - (ST.go + 0.7)) / 2.0));
      HD.ss.root.position.copy(ssAt); HD.ss.root.rotation.y = Math.atan2(B1W.x - ssAt.x, B1W.z - ssAt.z) * 0.5 + Math.atan2(-ssAt.x, -ssAt.z) * 0.5;
      applyPose(HD.ss, t < ST.go + 0.7 ? READY : t < ST.t_tag - 0.35 ? runPose(((t + 3) * 2.4) % 1, 0.6) : keyed([[ST.t_tag - 0.35, SS_RECV], [ST.t_tag, SS_RECV], [ST.t_tag + 0.12, SS_TAG]], t));
      HD.b1.root.position.set(62.5, 0, -62.5); applyPose(HD.b1, READY);
      if (s.show?.throwPath) reveal(THROW_TUBE, clamp((t - ST.t_release) / ST.throw.dur, 0, 1));
    }
  }
}
function setBatting(t, s) {
  idleDefense(AD, t);
  awayC.root.position.set(0.15, 0, 3.0); awayC.root.rotation.y = Math.PI; applyPose(awayC, C_MID);
  setPitcher(awayP, t + 0.45);
  // the hit: contact at t = 0
  const CBroot = v3(-3.0, 0, -0.9);
  if (s.play === "hit" && t < 0.35) { CB.root.position.copy(CBroot); CB.root.rotation.y = Math.PI / 2; applyPose(CB, keyed(swing(0), t)); if (CB.bat) CB.bat.visible = true; }
  else {                                                       // the run: drops the bat, down the line, rounds first
    const u = clamp(t * RN.hz, 0, RN.x.length - 2), i = Math.floor(u), f = u - i;
    const p = v3(lerp(RN.x[i], RN.x[i + 1], f), 0, lerp(RN.z[i], RN.z[i + 1], f));
    const q2 = v3(RN.x[Math.min(i + 6, RN.x.length - 1)], 0, RN.z[Math.min(i + 6, RN.z.length - 1)]);
    CB.root.position.copy(p); if (q2.distanceTo(p) > 0.05) CB.root.rotation.y = Math.atan2(q2.x - p.x, q2.z - p.z);
    const sp = (RN.s[Math.min(i + 1, RN.s.length - 1)] - RN.s[i]) * RN.hz;
    if (CB.bat) CB.bat.visible = false;
    applyPose(CB, sp > 1 ? runPose((RN.s[i] / 11) % 1, clamp(sp / 25, 0.3, 1)) : STAND);
  }
  // outfielders go after it
  const land = V(DB.land);
  for (const k of ["lf", "cf"]) {
    const [x, z] = homeD[k], st = v3(x, 0, z), tgt = land.clone().lerp(v3(-150, 0, -330), 0.5); const d = tgt.clone().sub(st);
    const run = Math.min(d.length() - 6, Math.max(0, 25 * (t - 0.4)));
    AD[k].root.position.copy(st).addScaledVector(d.normalize(), Math.max(0, run)); AD[k].root.rotation.y = Math.atan2(d.x, d.z);
    applyPose(AD[k], t > 0.4 ? runPose((run / 11) % 1, 0.9) : READY);
  }
  // the ball
  let bp, path = null;
  if (t < -0.45) bp = handPos(awayP.handR);
  else if (t < 0) bp = v3(-1.9, 6, -54).lerp(V(DB.contact), (t + 0.45) / 0.45);
  else { bp = pathAt(DB.path, t); path = DB.path; }
  placeBall(bp, path, t);
  if (s.show?.hitPath) reveal(HIT_TUBE, clamp(t / DB.path.dur, 0, 1));
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
const CAMS = {
  hero: (u) => [mixV(v3(-2.6, 2.9, -8.0), v3(-2.0, 2.6, -6.8), easeIO(u)), v3(0.1, 2.6, 2.6), 42],                    // in front of the plate, low: the catcher
  sign: (u) => [mixV(v3(0.35, 0.9, 4.6), v3(0.3, 0.85, 4.3), u), v3(0.15, 1.15, 2.6), 46],                             // behind and below: the sign between his thighs
  mound: (u) => [mixV(v3(0.9, 7.2, 9.5), v3(0.8, 6.8, 8.8), u), v3(0, 5, -50), 34],                                    // behind the catcher, looking out at the pitcher
  plate: (u) => [v3(-3.5, 17, -205), v3(0, 3.2, -18), lerp(6.8, 6.3, u)],                                              // the center-field camera
  zone: (u) => [mixV(v3(0.5, 9.5, 11.5), v3(0.5, 9.0, 10.8), easeIO(u)), v3(0.3, 2.2, -1.4), 28],                       // high behind the plate: the zone
  glove: (u) => [mixV(v3(6.5, 1.9, -4.0), v3(6.0, 1.8, -3.4), u), v3(0.4, 1.6, 1.9), 40],                              // first-base side, out front, low: the glove
  dirt: (u) => [mixV(v3(3.4, 1.4, -11), v3(2.8, 1.3, -9.5), u), v3(0.2, 0.9, 1.5), 38],                                // out front, low: the ball in the dirt and the block
  side: (u) => [mixV(v3(-0.5, 1.2, -7), v3(-0.4, 1.1, -6.2), u), v3(0.2, 0.9, 1.8), 38],                              // straight on, low: drop and smother
  first: (u) => [mixV(v3(30, 30, 40), v3(26, 28, 34), u), v3(40, 0, -50), 44],                                         // high behind home: the runner at first
  steal: (u) => [mixV(v3(2.6, 7.6, 12.5), v3(2.4, 7.4, 11.8), u), v3(-0.2, 1.6, -12), 46],                            // behind the plate, first-base side: the catch, the exchange, the throw
  tag: (u) => [mixV(v3(14, 5.5, -112), v3(12, 4.8, -114), u), v3(0, 1.2, -126.5), 40],                                // at second: the tag
  bat: (u) => [mixV(v3(4.5, 4.0, -9), v3(4.0, 3.8, -8), u), v3(-2.5, 3.0, 0), 44],                                    // in front of the hitter, first-base side
  gap: (u, t) => { const b = pathAt(DB.path, Math.max(t, 0)); return [mixV(v3(18, 28, 32), v3(14, 34, 22), u), v3(-90, 10, -230).lerp(b, 0.35), 46]; },
  run: (u, t) => { const i = clamp(Math.floor(t * RN.hz), 0, RN.x.length - 1), p = v3(RN.x[i], 0, RN.z[i]); return [p.clone().add(v3(26, 16, 32)), p.clone().add(v3(-6, 2, -14)), 48]; },
};
function shotAt(v) {
  const L = CC.shots.list;
  const s = L.find((x) => v < x.b) || L.at(-1);
  const r = s.cu || [s.a, s.b];
  return { s, t: pw(v, s.vs, s.ts), u: clamp((v - r[0]) / (r[1] - r[0]), 0, 1) };
}

// ------------------------------------------------------------------ DOM overlays fed from the same clock
const $ = (id) => document.getElementById(id);
const SPEEDS = { rt: "Real time", slow2: "Slow motion · ½ speed", replay: "Replay · ½ speed", freeze: "Freeze", none: "" };
function overlays(s) { if ($("spd")) { $("spd").textContent = SPEEDS[s.speed] ?? ""; $("spd").style.opacity = s.speed === "none" ? 0 : 1; $("spd").className = "spd " + (s.speed === "rt" ? "rt" : "sl"); } }

function renderAt(v) {
  const { s, t, u } = shotAt(v);
  setScene(t, s);
  const c = CAMS[s.cam](u, t, s);
  frame(cam, c[0], c[1], c[2], W / H);
  const g = c[2] < 12 ? 0.008 : 0.022; BALL.glow.scale.set(g, g, 1);           // a smaller glow through the long center-field lens
  renderer.render(scene, cam);
  overlays(s);
}

let last = -1;
function seek(time) { if (time === last) return; last = time; renderAt(time); }
window.addEventListener("hf-seek", (e) => seek(e.detail.time));
window.__fieldRender = renderAt;
document.fonts.ready.then(() => seek(window.__hfThreeTime || 0));
seek(window.__hfThreeTime || 0);
