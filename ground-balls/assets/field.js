// "Work through the ball": the field, the shortstop and four simulated ground balls, in three.js.
// Everything is a pure function of HyperFrames time (hf-seek), so each frame is exact and repeatable.
// Units are feet. Home plate's back point is the origin, +x points toward first base's side, -z toward center field.
// The ground balls (bounces) and the shortstop's footwork come from tools/physics.py via window.__PLAY.
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
key.position.set(-160, 300, 20); key.target.position.set(0, 0, -100);
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
const ss = makePlayer(KIT.home, { glove: true });              // the shortstop
const ss2 = makePlayer(KIT.home, { glove: true });             // a second shortstop for the split screens
const batter = makePlayer(KIT.away, { helmet: true, bat: true });
const runner = makePlayer(KIT.away, { helmet: true });
const firstB = makePlayer(KIT.home, { glove: true }), pitcher = makePlayer(KIT.home, { glove: true });
const catcher = makePlayer(KIT.home, { glove: true, catcher: true }), umpH = makePlayer(KIT.ump, { catcher: true });
const others = [[28, -128], [-62, -86], [-112, -250], [0, -305], [112, -250]].map(([x, z]) => { const p = makePlayer(KIT.home, { glove: true }); p.root.position.set(x, 0, z); p.root.rotation.y = Math.atan2(-x, -z); return p; });
for (const p of [ss, ss2, batter, runner, firstB, pitcher, catcher, umpH, ...others]) scene.add(p.root);

// ------------------------------------------------------------------ the model (tools/physics.py)
const V = (a) => v3(a[0], a[1], a[2]);
const HZ = PLAY.hz, DIR = V(PLAY.dir), SIDE = V(PLAY.side), BL = PLAY.balls, PL = PLAY.plays;
const seriesAt = (arr, t) => { const u = clamp(t, 0, (arr.length - 1) / HZ) * HZ, i = Math.min(Math.floor(u), arr.length - 2); return [i, u - i]; };
function ballAt(name, t) { const p = BL[name].p, [i, f] = seriesAt(p, t); return v3(lerp(p[i][0], p[i + 1][0], f), lerp(p[i][1], p[i + 1][1], f), lerp(p[i][2], p[i + 1][2], f)); }
function posAt(play, t) { const P = PL[play].pos, [i, f] = seriesAt(P.x, t); return v3(lerp(P.x[i], P.x[i + 1], f), 0, lerp(P.z[i], P.z[i + 1], f)); }
const phAt = (play, t) => { const a = PL[play].pos.ph, [i, f] = seriesAt(a, t); return lerp(a[i], a[i + 1], f); };
function throwAt(play, t) { const T = PL[play].throw, u = (t - T.t0) * T.hz, n = T.p.length - 1; const i = clamp(Math.floor(u), 0, n - 1), f = clamp(u - i, 0, 1); return v3(lerp(T.p[i][0], T.p[i + 1][0], f), lerp(T.p[i][1], T.p[i + 1][1], f), lerp(T.p[i][2], T.p[i + 1][2], f)); }
const handPos = (h) => { h.updateWorldMatrix(true, false); return h.getWorldPosition(new THREE.Vector3()); };
const B1W = v3(63.64, 0, -63.64);
const FACE_HOME = Math.atan2(-DIR.x, -DIR.z);

// ------------------------------------------------------------------ poses (shortstop: facing home = +z of the figure)
const SS_READY = { drop: -0.7, lean: 28, nod: -12, hipL: [44, 20], hipR: [44, 20], knL: 52, knR: 52, shL: [36, 16, 0], shR: [36, 16, 0], elL: 45, elR: 45 };
const SS_UPRIGHT = { drop: -0.2, lean: 10, nod: -14, hipL: [12, 12], hipR: [12, 12], knL: 16, knR: 16, shL: [20, 14, 0], shR: [16, 12, 0], elL: 40, elR: 40 };   // tall, flat-footed
const FIELD_FRONT = { drop: -1.45, lean: 52, nod: -26, hipL: [86, 22], hipR: [56, 26], knL: 92, knR: 70, shL: [62, -6, 0], elL: 10, shR: [46, 10, 0], elR: 55 };   // glove out front, left foot forward
const FIELD_SHORT = { drop: -1.75, lean: 58, nod: -30, hipL: [96, 28], hipR: [70, 30], knL: 104, knR: 86, shL: [70, -8, 0], elL: 4, shR: [52, 14, 0], elR: 45 };   // lower, wider: short hop
const FIELD_MID = { drop: -1.0, lean: 38, nod: -18, hipL: [64, 18], hipR: [44, 22], knL: 66, knR: 52, shL: [48, -6, 0], elL: 16, shR: [40, 10, 0], elR: 60 };       // a higher hop, still out front
const FIELD_BODY = { drop: -0.8, lean: 30, nod: -34, hipL: [40, 16], hipR: [40, 16], knL: 46, knR: 46, shL: [14, 2, 0], elL: 46, shR: [10, 8, 0], elR: 70 };      // late, at his body
const GATHER = { drop: -0.3, lean: 10, nod: -6, look: 60, hipL: [14, 12], hipR: [14, 12], knL: 20, knR: 20, shL: [40, 10, 0], elL: 112, shR: [40, -4, 0], elR: 112 };
const SHUF_A = { ...GATHER, hipL: [22, 20], knL: 30, hipR: [6, 8], knR: 14 }, SHUF_B = { ...GATHER, hipL: [6, 8], knL: 14, hipR: [22, 20], knR: 30 };
const THROUGH = { drop: -0.7, lean: 24, twist: -40, look: 50, nod: -6, hipL: [20, 10], hipR: [46, 14], knL: 30, knR: 42, shL: [60, 16, 0], elL: 60, shR: [30, 40, 0], elR: 100 };   // right foot steps through
const PLANT = { drop: -0.6, lean: 12, twist: -60, look: 62, nod: -4, shL: [80, 20, 0], elL: 30, shR: [-30, 78, 0], elR: 95, hipL: [10, 12], hipR: [38, 12], knL: 40, knR: 30 };
const RELEASE = { drop: -0.6, lean: 30, twist: 30, nod: 6, shL: [20, 30, 0], elL: 60, shR: [165, 20, 0], elR: 15, hipL: [46, 8], hipR: [-26, 10], knL: 40, knR: 30 };
const FOLLOW = { drop: -0.8, lean: 46, twist: 48, nod: 10, shL: [10, 30, 0], elL: 70, shR: [55, -25, 0], elR: 25, hipL: [55, 8], hipR: [10, 10], knL: 52, knR: 70 };
const BACKPEDAL = { drop: -0.6, lean: 14, nod: -20, hipL: [30, 18], hipR: [10, 18], knL: 40, knR: 28, shL: [30, 14, 0], shR: [30, 14, 0], elL: 50, elR: 50 };
const B_READY = { drop: -0.4, lean: 20, nod: -8, hipL: [26, 18], hipR: [26, 18], knL: 30, knR: 30, shL: [40, 16, 0], shR: [40, 16, 0], elL: 50, elR: 50 };
const B_STRETCH = { drop: -1.0, lean: 44, nod: -12, hipL: [70, 10], hipR: [-18, 12], knL: 34, knR: 12, shL: [96, 10, 0], elL: 6, shR: [40, 10, 0], elR: 60 };
const BAT_SET = { drop: -0.35, lean: 18, look: 80, nod: -4, hipL: [22, 14], hipR: [22, 14], knL: 26, knR: 26, shL: [55, 6, 0], shR: [60, 34, 0], elL: 95, elR: 110, twist: 20 };
const BAT_HIT = { drop: -0.6, lean: 34, look: 50, nod: -16, twist: -40, pelvisTwist: 60, hipL: [24, 28], knL: 14, hipR: [18, 12], knR: 46, shL: [70, -10, 0], elL: 10, shR: [64, 10, 0], elR: 20 };
const BAT_FIN = { drop: -0.3, lean: 14, look: 20, twist: -80, pelvisTwist: 90, hipL: [16, 26], knL: 8, hipR: [6, 12], knR: 56, shL: [140, 10, 0], elL: 100, shR: [150, -40, 0], elR: 110 };
const P_SET = { lean: 4, look: 0, shL: [42, 8, 0], elL: 105, shR: [38, -4, 0], elR: 112, hipL: [4, 6], hipR: [4, 6], knL: 8, knR: 8 };
const P_FOLLOW = { lean: 50, nod: 14, drop: -1.1, twist: 40, shL: [8, 38, 0], elL: 95, shR: [58, -24, 0], elR: 22, hipL: [82, 4], knL: 38, hipR: [34, 6], knR: 84 };

// the shortstop on one of the plays, at play time t; the body is nudged so his glove meets the ball exactly
const FIELD_POSE = { stand: FIELD_BODY, through: FIELD_FRONT, short: FIELD_SHORT, back: FIELD_MID };
function ssPose(play, t) {
  const p = PL[play], k = p.kind, tf = p.t_field, tr = p.t_release, run = phAt(play, t) % 1;
  if (k === "stand") return keyed([[0.15, SS_READY], [0.45, SS_UPRIGHT], [tf - 0.22, SS_UPRIGHT], [tf, FIELD_BODY], [tf + 0.1, FIELD_BODY], [tf + 0.3, GATHER], [tf + 0.45, SHUF_A],
    [tf + 0.62, SHUF_B], [tf + 0.78, SHUF_A], [tr - 0.14, PLANT], [tr, RELEASE], [tr + 0.35, FOLLOW], [tr + 1.0, { ...FOLLOW, lean: 18, drop: -0.3 }]], t);
  const field = FIELD_POSE[k];
  let pre;
  if (k === "back") pre = keyed([[0.2, SS_READY], [0.5, BACKPEDAL], [tf - 0.35, BACKPEDAL], [tf - 0.1, field]], t);
  else pre = t < 0.25 ? SS_READY : mixPose(SS_READY, runPose(run, k === "short" ? 0.45 : 0.62), smooth((t - 0.25) / 0.2));
  if (t < tf - 0.25) return pre;
  return keyed([[tf - 0.25, pre], [tf, field], [tf + 0.08, field], [tf + 0.22, THROUGH], [tr - 0.12, PLANT], [tr, RELEASE], [tr + 0.35, FOLLOW], [tr + 1.0, { ...FOLLOW, lean: 18, drop: -0.3 }]], t);
}
function ssYaw(play, t) {
  const p = PL[play], tf = p.t_field, tr = p.t_release, at = posAt(play, tf + 0.1), to1 = Math.atan2(B1W.x - at.x, B1W.z - at.z);
  const d = ((to1 - FACE_HOME + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
  return FACE_HOME + d * smooth((t - tf - 0.05) / (tr - tf - 0.05));
}
const FIX = {};
function gloveFix(play) {                     // offset so the glove is on the ball at the moment he fields it
  if (FIX[play]) return FIX[play];
  const p = PL[play]; ss.root.position.copy(posAt(play, p.t_field)); ss.root.rotation.y = ssYaw(play, p.t_field); applyPose(ss, ssPose(play, p.t_field));
  const g = handPos(ss.handL), b = V(p.glove_pt); const f = b.sub(g); f.y = 0; FIX[play] = f; return f;
}
function setSS(P, play, t) {
  const p = PL[play], fix = gloveFix(play);
  P.root.position.copy(posAt(play, t)).addScaledVector(fix, smooth((t - 0.3) / Math.max(0.3, p.t_field - 0.5)));
  P.root.rotation.y = ssYaw(play, t);
  const q = ssPose(play, t);
  if (t > 0.3 && t < p.t_field) {               // eyes on the ball
    const b = ballAt(p.ball, t), pos = P.root.position, rel = Math.atan2(b.x - pos.x, b.z - pos.z) - P.root.rotation.y;
    q.look = (q.look ?? 0) + clamp((((rel + Math.PI * 3) % (Math.PI * 2)) - Math.PI) * 57.3, -60, 60) * 0.6;
  }
  applyPose(P, q);
}

// ------------------------------------------------------------------ the ball, marks
function makeBall(glowHex) {
  const m = new THREE.Mesh(new THREE.SphereGeometry(0.16, 16, 12), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffe9b0, emissiveIntensity: 0.7, roughness: 0.4 }));
  m.castShadow = true; scene.add(m);
  const gt = canvasTex(64, 64, (g, w) => { const gr = g.createRadialGradient(w / 2, w / 2, 0, w / 2, w / 2, w / 2); gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(0.35, "rgba(255,255,255,.55)"); gr.addColorStop(1, "rgba(255,255,255,0)"); g.fillStyle = gr; g.fillRect(0, 0, w, w); });
  const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: gt, color: glowHex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: false }));
  glow.scale.set(0.024, 0.024, 1); scene.add(glow);
  const shadow = new THREE.Mesh(new THREE.CircleGeometry(0.3, 16), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.4, depthWrite: false }));
  shadow.rotation.x = -Math.PI / 2; scene.add(shadow);
  return { m, glow, shadow };
}
const BALL = makeBall(0xffd84d);
function placeBall(pos) { BALL.m.position.copy(pos); BALL.glow.position.copy(pos); BALL.shadow.position.set(pos.x, 0.07, pos.z); BALL.shadow.material.opacity = clamp(0.45 - pos.y / 20, 0.1, 0.45); }
function tube(points, color, width, opacity = 0.9) {
  const g = new THREE.Group();
  for (let i = 0; i < points.length - 1; i++) {
    const a = points[i], b = points[i + 1], len = a.distanceTo(b);
    const m = new THREE.Mesh(new THREE.BoxGeometry(width, width, len + 0.02), new THREE.MeshBasicMaterial({ color, transparent: true, opacity, depthWrite: false }));
    m.position.set((a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2); m.lookAt(b.x, b.y, b.z); m.userData.t = (i + 1) / HZ * 2; g.add(m);
  }
  g.visible = false; scene.add(g); return g;
}
function revealT(g, t) { g.visible = t > 0; for (const m of g.children) m.visible = m.userData.t <= t; }
const ringMesh = (r0, r1, color, opacity = 0.95) => { const m = new THREE.Mesh(new THREE.RingGeometry(r0, r1, 40), new THREE.MeshBasicMaterial({ color, transparent: true, opacity, depthWrite: false, side: THREE.DoubleSide })); m.rotation.x = -Math.PI / 2; m.visible = false; scene.add(m); return m; };
const MK = {};
for (const [name, B] of Object.entries(BL)) {
  const pts = []; for (let i = 0; i < B.p.length; i += 2) pts.push(V(B.p[i]));
  MK[name] = { path: tube(pts, 0xffd84d, 0.12, 0.8), hops: B.bounces.filter((b) => Math.hypot(b[1][0], b[1][2]) > 60 && Math.hypot(b[1][0], b[1][2]) < 175).map((b) => { const r = ringMesh(0.5, 0.9, 0xf4f6f8, 0.9); r.position.set(b[1][0], 0.12, b[1][2]); r.userData.t = b[0]; return r; }) };
}
const GLOVE_MK = {};
for (const [name, p] of Object.entries(PL)) { const r = ringMesh(0.9, 1.35, p.kind === "stand" ? 0xff6a3d : 0x56d1ff); r.position.set(p.glove_pt[0], 0.13, p.glove_pt[2]); GLOVE_MK[name] = r; }
// footprints after he fields it, and the movement arrow (approach -> glove -> toward first)
const FOOTS = {};
for (const [name, p] of Object.entries(PL)) FOOTS[name] = p.footprints.map((f, k) => { const m = new THREE.Mesh(new THREE.CircleGeometry(0.42, 16), new THREE.MeshBasicMaterial({ color: p.kind === "stand" ? 0xff6a3d : 0x56d1ff, transparent: true, opacity: 0.9, depthWrite: false })); m.scale.set(0.7, 1.25, 1); m.rotation.x = -Math.PI / 2; m.position.set(f[0], 0.14, f[2]); m.visible = false; m.userData.t = p.steps[k]; scene.add(m); return m; });
function arrowFor(play) {
  const p = PL[play], g = new THREE.Group(), tEnd = p.t_release + 0.25, pts = [];
  for (let t = 0.25; t <= tEnd; t += 0.05) pts.push(posAt(play, t).add(gloveFix(play).clone().multiplyScalar(smooth((t - 0.3) / Math.max(0.3, p.t_field - 0.5)))));
  for (let i = 0; i < pts.length - 1; i++) { const a = pts[i], b = pts[i + 1], len = a.distanceTo(b); if (len < 0.01) continue;
    const m = new THREE.Mesh(new THREE.PlaneGeometry(0.55, len + 0.05), new THREE.MeshBasicMaterial({ color: 0x56d1ff, transparent: true, opacity: 0.75, depthWrite: false }));
    m.rotation.x = -Math.PI / 2; m.rotation.z = -Math.atan2(b.x - a.x, -(b.z - a.z)); m.position.set((a.x + b.x) / 2, 0.15, (a.z + b.z) / 2); m.userData.t = 0.25 + (i + 1) * 0.05; g.add(m); }
  const last = pts.at(-1), prev = pts.at(-3), dir = last.clone().sub(prev).normalize();
  const head = new THREE.Mesh(new THREE.ConeGeometry(0.9, 2.0, 3), new THREE.MeshBasicMaterial({ color: 0x56d1ff, transparent: true, opacity: 0.85, depthWrite: false }));
  head.rotation.x = -Math.PI / 2; head.rotation.z = -Math.atan2(dir.x, -dir.z); head.position.set(last.x + dir.x, 0.16, last.z + dir.z); head.userData.t = tEnd; head.scale.set(1, 1, 0.05); g.add(head);
  g.visible = false; scene.add(g); return g;
}
let ARROW = null;

// ------------------------------------------------------------------ set the scene at play time t (s since contact)
// shot: { play, show: { path, hops, glove, foot, arrow } }
function setScene(t, s, half) {
  const play = half?.play ?? s.play, p = PL[play], ballName = p.ball;
  ss2.root.visible = false;
  setSS(ss, play, t);
  // batter -> runner
  batter.root.visible = t < 0.25; runner.root.visible = t >= 0.25;
  batter.root.position.set(-3.0, 0, -0.9); batter.root.rotation.y = Math.PI / 2;
  applyPose(batter, keyed([[-0.5, BAT_SET], [0, BAT_HIT], [0.3, BAT_FIN]], t));
  const sr = Math.max(0, t - 0.25), srun = 27 * (sr - 0.8 * (1 - Math.exp(-sr / 0.8)));
  const r0 = v3(-2.4, 0, -0.7), rdir = v3(66.4, 0, -62.9).normalize();
  runner.root.position.copy(r0).addScaledVector(rdir, Math.min(srun, 96)); runner.root.rotation.y = Math.atan2(rdir.x, rdir.z);
  applyPose(runner, runPose((srun / 10) % 1, clamp(srun / 20, 0.3, 1)));
  pitcher.root.position.set(0, MOUND_H, -56.5); pitcher.root.rotation.y = 0; applyPose(pitcher, keyed([[-0.9, P_SET], [-0.4, P_SET], [-0.05, P_FOLLOW], [0.8, READY]], t));
  catcher.root.position.set(0.15, 0, 3.6); catcher.root.rotation.y = Math.PI; applyPose(catcher, { ...CROUCH, shL: [70, 14, 0], elL: 25 });
  umpH.root.position.set(0.5, 0, 6.0); umpH.root.rotation.y = Math.PI; applyPose(umpH, { drop: -1.0, lean: 30, nod: -6, hipL: [52, 28], hipR: [52, 28], knL: 68, knR: 68 });
  for (const o of others) applyPose(o, t > -0.3 ? READY : STAND);
  const fb = B1W.clone().add(v3(-1.1, 0, -1.1)); firstB.root.position.copy(fb); firstB.root.rotation.y = Math.atan2(V(p.release).x - fb.x, V(p.release).z - fb.z);
  applyPose(firstB, keyed([[p.t_release - 0.3, B_READY], [p.t_arrive - 0.15, B_STRETCH], [p.t_arrive + 0.5, B_STRETCH], [p.t_arrive + 1.1, B_READY]], t));
  // the ball: pitch -> contact -> hops -> glove -> throwing hand -> throw -> first baseman
  let bp;
  if (t < -0.42) bp = handPos(pitcher.handR);
  else if (t < 0) bp = v3(-1.9, 6.0, -54).lerp(V(BL[ballName].p[0]), (t + 0.42) / 0.42);
  else if (t < p.t_field) bp = ballAt(ballName, t);
  else if (t < p.t_release - 0.3) bp = handPos(ss.handL);
  else if (t < p.t_release) bp = handPos(ss.handR);
  else if (t < p.t_arrive) { bp = throwAt(play, t); if (t < p.t_release + 0.05) bp = handPos(ss.handR).lerp(bp, (t - p.t_release) / 0.05); }
  else bp = handPos(firstB.handL);
  placeBall(bp);
  // marks
  for (const M of Object.values(MK)) { M.path.visible = false; for (const h of M.hops) h.visible = false; }
  for (const g of Object.values(GLOVE_MK)) g.visible = false;
  for (const F of Object.values(FOOTS)) for (const m of F) m.visible = false;
  if (ARROW) ARROW.visible = false;
  const sh = s.show || {};
  if (sh.path) revealT(MK[ballName].path, Math.min(t, p.t_field));
  if (sh.hops) for (const h of MK[ballName].hops) h.visible = t >= h.userData.t;
  if (sh.glove && t >= sh.glove) GLOVE_MK[play].visible = true;
  if (sh.foot) for (const m of FOOTS[play]) m.visible = t >= m.userData.t;
  if (sh.arrow) { if (!ARROW) ARROW = arrowFor(sh.arrow); revealT(ARROW, t); }
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
const LP = (r, lat = 0, y = 0) => DIR.clone().multiplyScalar(r).addScaledVector(SIDE, lat).add(v3(0, y, 0));     // a point by distance along the line to the shortstop
const CAMS = {
  plate: (u, t) => [mixV(v3(4, 7, 15), v3(3, 8, 12), u), mixV(v3(-20, 2, -60), LP(120, 0, 1), smooth((t + 0.1) / 0.9)), 42],
  hook: (u) => [mixV(LP(157, -4.5, 4.8), LP(155, -4, 4.4), easeIO(u)), LP(122, 0, 1.6), 50],                    // low, just behind the shortstop: the ball coming at him
  side: (u) => [mixV(LP(143.5, -26, 5), LP(143.5, -25, 5), u), LP(143.5, 1, 2.2), 46],                         // square to the line, third-base side: the late field and the reset
  halfL: () => [LP(168, -3, 15), LP(118, 2, 0), 50],                                                           // behind the shortstop, looking in
  high: (u) => [mixV(LP(149.5, -30, 5), LP(149.5, -29, 4.8), u), LP(149.5, 0, 2.4), 46],                        // square to the line: the hop's height, the step back
  wide: (u) => [mixV(LP(150, -60, 40), LP(140, -62, 38), u), v3(10, 0, -110), 50],                              // high on the third-base side: shortstop to first
  through: (u) => [mixV(LP(122, -26, 6), LP(124, -24, 6), u), LP(140, 4, 2.0), 50],                             // in front, third-base side: approach, glove, momentum toward first
  behind: (u) => [mixV(LP(161, -1, 9.5), LP(159, 0, 9), u), LP(130, 3.5, 0.5), 50],                             // behind and above him: the approach in depth, the carry toward first across the frame
};
function shotAt(v) {
  const L = CC.shots.list;
  const s = L.find((x) => v < x.b) || L.at(-1);
  const r = s.cu || [s.a, s.b];
  return { s, t: pw(v, s.vs, s.ts), u: clamp((v - r[0]) / (r[1] - r[0]), 0, 1) };
}

// ------------------------------------------------------------------ DOM overlays fed from the same clock
const $ = (id) => document.getElementById(id);
const SPEEDS = { rt: "Real time", slow2: "Slow motion · ½ speed", replay: "Replay · ½ speed", freeze: "Freeze" };
function overlays(s) { if ($("spd")) { $("spd").textContent = SPEEDS[s.speed] ?? ""; $("spd").className = "spd " + (s.speed === "rt" ? "rt" : "sl"); } }

function renderAt(v) {
  const { s, t, u } = shotAt(v);
  renderer.setScissorTest(s.mode === "split");
  if (s.mode === "split") {
    s.halves.forEach((half, k) => {
      setScene(t, s, half);
      const c = CAMS[half.cam || s.cam](u, t, s, k);
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
  overlays(s);
}

let last = -1;
function seek(time) { if (time === last) return; last = time; renderAt(time); }
window.addEventListener("hf-seek", (e) => seek(e.detail.time));
window.__fieldRender = renderAt;

document.fonts.ready.then(() => seek(window.__hfThreeTime || 0));
seek(window.__hfThreeTime || 0);
