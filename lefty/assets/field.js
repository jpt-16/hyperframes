// "Why every team wants a lefty": the field, a right- and a left-handed pitcher, both kinds of hitter, a runner on first, in three.js.
// Everything is a pure function of HyperFrames time (hf-seek), so each frame is exact and repeatable.
// Units are feet. Home plate's back point is the origin, +x points toward first base's side, -z toward center field.
// The pitches come from tools/physics.py via window.__PLAY. The left-hander is the right-hander's figure, mirrored.
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
// our team (white): the pitcher, catcher, defense; the other team (dark): the hitter and the runner on first.
// A left-hander is the right-handed figure drawn through a mirror (scale.x = -1 on a parent group): the same body and
// mechanics, throwing arm and glove swapped, his whole delivery reflected across the line from the mound to home.
function mirrorable(P) { const w = new THREE.Group(); w.add(P.root); scene.add(w); P.wrap = w; return P; }
const pitcher = mirrorable(makePlayer(KIT.home, { glove: true }));
const hitter = mirrorable(makePlayer(KIT.away, { helmet: true, bat: true }));
const C = makePlayer(KIT.home, { glove: true, catcher: true });
const ump = makePlayer(KIT.ump, { catcher: true });
const runner = makePlayer(KIT.away, { helmet: true });
const homeD = { b1: [60, -84], b2: [30, -128], ss: [-28, -118], b3: [-58, -76], lf: [-118, -262], cf: [0, -312], rf: [118, -262] };
const HD = {};
for (const [k, [x, z]] of Object.entries(homeD)) { HD[k] = makePlayer(KIT.home, { glove: true }); HD[k].root.position.set(x, 0, z); }
for (const p of [C, ump, runner, ...Object.values(HD)]) scene.add(p.root);
// place a mirrorable figure by its WORLD position and facing (the mirror flips x and the facing angle back)
function place(P, lefty, pos, yaw) {
  P.wrap.scale.x = lefty ? -1 : 1;
  P.root.position.set(lefty ? -pos.x : pos.x, pos.y, pos.z); P.root.rotation.y = lefty ? -yaw : yaw;
}

// ------------------------------------------------------------------ the model (tools/physics.py)
const V = (a) => v3(a[0], a[1], a[2]);
const PI_ = PLAY.pitches, Z = PLAY.zone;
function pathAt(path, t) {
  const u = (t - path.t0) * path.hz, n = path.p.length - 1;
  if (u <= 0) return V(path.p[0]);
  if (u >= n) return V(path.p[n]);
  const i = Math.floor(u), f = u - i, a = path.p[i], b = path.p[i + 1];
  return v3(lerp(a[0], b[0], f), lerp(a[1], b[1], f), lerp(a[2], b[2], f));
}
const handPos = (h) => { h.updateWorldMatrix(true, false); return h.getWorldPosition(new THREE.Vector3()); };
const B1W = v3(63.64, 0, -63.64), B2W = v3(0, 0, -127.28);
const TO2 = B2W.clone().sub(B1W).normalize();                    // first base toward second
const OUTF = v3(TO2.z, 0, -TO2.x).multiplyScalar(-1);            // across the base line, toward right field (the bag's back side)
const moundY = (x, z) => { const r = Math.hypot(x - MOUND.x, z - MOUND.z); return r < 2.5 ? MOUND_H : r < 5.5 ? lerp(MOUND_H, 0.45, (r - 2.5) / 3) : r < 9 ? lerp(0.45, 0, (r - 5.5) / 3.5) : 0; };

// ------------------------------------------------------------------ poses
const C_SET = { ...CROUCH, shL: [62, 18, 0], elL: 40, shR: [20, 10, 0], elR: 50, nod: -18 };
const C_LOWAWAY = { ...CROUCH, nod: -12, shL: [58, 34, 0], elL: 16, shR: [14, 10, 0], elR: 60 };      // glove low, to his glove side (third-base side)
const C_MID = { ...CROUCH, nod: -8, shL: [78, 12, 0], elL: 24, shR: [20, 10, 0], elR: 60 };
// pitcher, from the stretch (poses in the right-hander's own frame; the mirror makes them left-handed)
const P_OPEN = { lean: 2, look: 80, nod: 6, shL: [20, 12, 0], elL: 40, shR: [12, 6, 0], elR: 30, hipL: [4, 6], hipR: [4, 6], knL: 8, knR: 8 };   // on the rubber, hands apart, getting the sign
const P_SET = { lean: 4, look: 80, nod: 4, shL: [42, 8, 0], elL: 105, shR: [38, -4, 0], elR: 112, hipL: [4, 6], hipR: [4, 6], knL: 8, knR: 8 };   // set: hands together, looking in
const P_WATCH = { ...P_SET, look: 4, nod: 2 };                                                                   // set, head over his front... the runner in view
const P_LIFT = { lean: -4, look: 80, shL: [48, 8, 0], elL: 100, shR: [44, -4, 0], elR: 108, hipL: [100, 4], knL: 105, hipR: [6, 6], knR: 14, drop: -0.15 };
const P_STRIDE = { lean: 6, look: 40, drop: -0.6, twist: -50, shL: [80, 35, 0], elL: 25, shR: [-55, 80, 0], elR: 85, hipL: [52, 4], knL: 28, hipR: [-28, 6], knR: 38 };
const P_REL = { lean: 42, nod: 8, drop: -1.0, twist: 28, shL: [12, 32, 0], elL: 85, shR: [168, 22, 0], elR: 8, hipL: [72, 4], knL: 22, hipR: [-18, 6], knR: 92 };
const P_FOLLOW = { lean: 62, nod: 18, drop: -1.25, twist: 48, shL: [8, 38, 0], elL: 95, shR: [58, -24, 0], elR: 22, hipL: [82, 4], knL: 38, hipR: [34, 6], knR: 84 };
// the pickoff: a quicker, shorter arm action than a pitch, stepping straight at first base
const PK_LIFT = { ...P_LIFT, hipL: [78, 4], knL: 88, look: 70 };
const PK_STRIDE = { ...P_STRIDE, drop: -0.45, twist: -40, look: 30, hipL: [42, 4], knL: 30, hipR: [-18, 6], knR: 30 };
const PK_REL = { lean: 26, nod: 4, drop: -0.7, twist: 22, shL: [16, 30, 0], elL: 80, shR: [150, 18, 0], elR: 14, hipL: [56, 4], knL: 26, hipR: [-12, 6], knR: 52 };
const PK_FOLLOW = { lean: 34, nod: 8, drop: -0.8, twist: 36, shL: [10, 34, 0], elL: 90, shR: [62, -16, 0], elR: 30, hipL: [58, 4], knL: 34, hipR: [8, 6], knR: 60 };
// hitters (a right-hander's poses; the mirror makes a left-handed hitter)
const BAT_SET = { drop: -0.35, lean: 18, look: 80, nod: -4, hipL: [22, 14], hipR: [22, 14], knL: 26, knR: 26, shL: [55, 6, 0], shR: [60, 34, 0], elL: 95, elR: 110, twist: 20 };
const BAT_LOAD = { ...BAT_SET, twist: 34, pelvisTwist: -10, hipL: [36, 22], knL: 40 };
const BAT_HIT = { drop: -0.55, lean: 30, look: 50, nod: -12, twist: -40, pelvisTwist: 60, hipL: [24, 28], knL: 12, hipR: [18, 12], knR: 46, shL: [80, -10, 0], elL: 10, shR: [74, 10, 0], elR: 20 };
const BAT_FIN = { drop: -0.3, lean: 12, look: 20, twist: -80, pelvisTwist: 90, hipL: [16, 26], knL: 8, hipR: [6, 12], knR: 56, shL: [140, 10, 0], elL: 100, shR: [150, -40, 0], elR: 110 };
const BAT_CHASE = { ...BAT_HIT, drop: -0.75, lean: 40, nod: -22, shL: [62, -14, 0], shR: [58, 6, 0] };      // swinging over a ball that's diving away
const BAT_BAIL = { ...BAT_SET, twist: 10, pelvisTwist: -16, lean: 10, look: 60, nod: -16, hipR: [30, 22], knR: 36 };   // a pitch at his back foot: weight back, he takes it
const swing = (tc) => [[tc - 0.6, BAT_SET], [tc - 0.2, BAT_LOAD], [tc - 0.02, BAT_CHASE], [tc + 0.3, BAT_FIN], [tc + 1.1, { ...BAT_FIN, lean: 6, drop: -0.1 }]];
const take = (tc) => [[tc - 0.6, BAT_SET], [tc - 0.25, BAT_LOAD], [tc - 0.05, BAT_BAIL], [tc + 0.6, BAT_BAIL], [tc + 1.3, BAT_SET]];
// first baseman holding the runner, the catch, the tag
const B_HOLD = { drop: -0.45, lean: 16, nod: -4, hipL: [26, 20], hipR: [26, 20], knL: 32, knR: 32, shL: [60, 18, 0], elL: 70, shR: [24, 10, 0], elR: 50 };
const B_CATCH = { drop: -0.6, lean: 18, nod: -6, hipL: [30, 22], hipR: [30, 22], knL: 40, knR: 40, shL: [82, 8, 0], elL: 20, shR: [36, 10, 0], elR: 60 };
const B_TAG = { drop: -1.55, lean: 58, nod: 16, twist: 22, hipL: [86, 26], hipR: [62, 26], knL: 100, knR: 86, shL: [52, 14, 0], elL: 8, shR: [30, 16, 0], elR: 60 };
// the runner
const LEADP = { drop: -0.75, lean: 28, look: 0, hipL: [42, 22], hipR: [42, 22], knL: 52, knR: 52, shL: [18, 14, 0], shR: [18, 14, 0], elL: 25, elR: 25, nod: -14 };
const LEAD_BACK = { ...LEADP, lean: 14, drop: -0.6, side: -10, hipL: [30, 26], hipR: [46, 18], knL: 40, knR: 58 };      // weight shifted back toward the bag
const CROSS = { drop: -0.6, lean: 36, nod: -14, hipL: [52, 6], hipR: [-22, 6], knL: 58, knR: 30, shL: [30, 14, 0], shR: [40, 14, 0], elL: 60, elR: 60 };
const DIVE_LAUNCH = { pelvisTilt: 38, lean: 16, nod: -40, hipL: [6, 6], hipR: [-26, 6], knL: 18, knR: 46, shL: [140, 16, 0], shR: [150, 12, 0], elL: 20, elR: 12 };
const DIVE_FLY = { pelvisTilt: 74, lean: 6, nod: -58, hipL: [-4, 8], hipR: [-10, 8], knL: 22, knR: 34, shL: [160, 20, 0], shR: [172, 10, 0], elL: 18, elR: 4 };
const DIVE_FLAT = { pelvisTilt: 86, lean: 3, nod: -62, hipL: [-4, 10], hipR: [-6, 10], knL: 8, knR: 14, shL: [150, 26, 0], shR: [170, 6, 0], elL: 30, elR: 2 };
const U_SET = { drop: -1.0, lean: 30, nod: -6, hipL: [52, 28], hipR: [52, 28], knL: 68, knR: 68, shL: [30, 20, 0], elL: 60, shR: [30, 20, 0], elR: 60 };

// ------------------------------------------------------------------ the ball and the graphics
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
const markAt = (p, color) => { const m = new THREE.Mesh(new THREE.CircleGeometry(0.13, 20), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.95, depthWrite: false, side: THREE.DoubleSide })); m.position.set(p[0], p[1], Z.z + 0.02); m.visible = false; scene.add(m); return m; };
const SL_MARK = markAt(PI_.sl_l.at_plate, 0xffd84d);
function tube(points, color, width, opacity = 0.85) {
  const g = new THREE.Group();
  for (let i = 0; i < points.length - 1; i++) { const a = points[i], b = points[i + 1], len = a.distanceTo(b); const m = new THREE.Mesh(new THREE.BoxGeometry(width, width, len + 0.02), new THREE.MeshBasicMaterial({ color, transparent: true, opacity, depthWrite: false })); m.position.set((a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2); m.lookAt(b.x, b.y, b.z); m.userData.u = (i + 1) / (points.length - 1); g.add(m); }
  g.visible = false; scene.add(g); return g;
}
function reveal(g, u) { g.visible = u > 0; for (const m of g.children) m.visible = m.userData.u <= u + 1e-6; }
const pitchTube = (k, color, w, op) => tube(Array.from({ length: 41 }, (_, i) => pathAt(PI_[k].path, PI_[k].path.t0 + PI_[k].path.dur * i / 40)), color, w, op);
const CYAN = 0x56d1ff, HOT = 0xff6a3d, YEL = 0xffd84d;
const TUBE = { fb_r: pitchTube("fb_r", CYAN, 0.12), fb_l: pitchTube("fb_l", HOT, 0.12), sl_l: pitchTube("sl_l", YEL, 0.08) };
const GHOST = Object.fromEntries(["fb_r", "sl_r", "ch_r", "cu_r"].map((k) => [k, pitchTube(k, CYAN, 0.05, 0.32)]));
// the runner's lead (a strip on the dirt), the pitcher's line of sight to him, the pickoff step
const flatMat = (c, op) => new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: op, depthWrite: false, side: THREE.DoubleSide });
const leadBar = new THREE.Mesh(new THREE.BoxGeometry(1, 0.04, 0.55), flatMat(HOT, 0.85)); leadBar.visible = false; scene.add(leadBar);
const sight = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.07, 1), flatMat(CYAN, 0.7)); sight.visible = false; scene.add(sight);
const sightRing = new THREE.Mesh(new THREE.RingGeometry(1.3, 1.6, 40), flatMat(CYAN, 0.75)); sightRing.rotation.x = -Math.PI / 2; sightRing.visible = false; scene.add(sightRing);
const stepArrow = new THREE.Group();
{
  const m = flatMat(HOT, 0.9);
  const shaft = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 0.32), m); shaft.position.x = 1.6; stepArrow.add(shaft);
  const head = new THREE.Mesh(new THREE.ShapeGeometry(new THREE.Shape([new THREE.Vector2(0, -0.6), new THREE.Vector2(1.0, 0), new THREE.Vector2(0, 0.6)])), m); head.position.x = 3.2; stepArrow.add(head);
  for (const c of stepArrow.children) c.rotation.x = -Math.PI / 2;
  const a = v3(1.2, 0, RUBBER_Z - 0.2), b = B1W;
  stepArrow.position.set(a.x, MOUND_H + 0.1, a.z); stepArrow.rotation.y = -Math.atan2(b.z - a.z, b.x - a.x);
  stepArrow.visible = false; scene.add(stepArrow);
}
function between(m, a, b) { const d = b.clone().sub(a); m.position.copy(a).addScaledVector(d, 0.5); m.scale.set(1, 1, d.length()); m.lookAt(b); }

// ------------------------------------------------------------------ the plays (t = 0: the pitch reaches the glove; for "pick", the pickoff release)
// s.play: "fb_r" | "fb_l" | "sl_l_lhb" | "sl_l_rhb" | "pick" | "hold" | "walk"
const PLAYS = {
  fb_r: { pitch: "fb_r", lefty: false, lhb: false, catcher: C_MID },
  fb_l: { pitch: "fb_l", lefty: true, lhb: false, catcher: C_MID },
  sl_l_lhb: { pitch: "sl_l", lefty: true, lhb: true, catcher: C_LOWAWAY, swing: true },
  sl_l_rhb: { pitch: "sl_l", lefty: true, lhb: false, catcher: C_LOWAWAY, take: true },
};
function setPitcherDelivery(lefty, tr) {                         // tr: time since release (a pitch to home from the stretch)
  const q = keyed([[-1.3, P_SET], [-0.9, P_LIFT], [-0.35, P_STRIDE], [0, P_REL], [0.35, P_FOLLOW], [1.0, { ...READY, look: 0 }]], tr);
  const z = lerp(-60.6, -57.6, smooth((tr + 0.45) / 0.5));
  place(pitcher, lefty, v3(0, MOUND_H * (z > -59 ? 0.6 : 1), z), lerp((lefty ? 1 : -1) * Math.PI / 2, 0, smooth((tr + 0.6) / 0.6)));   // set: side-on (a lefty faces first base), then square to home
  applyPose(pitcher, q);
}
const LEAD_FT = 11;                                               // the runner's lead, from the bag
const PK = { arrive: 0.55, tag: 0.68, mph: 76 };                  // the pickoff throw reaches the glove 0.55 s after release (63 ft at ~76 mph)
let PK_THROW = null, LEAD_MID = null;                                              // worked out once from the figure's own hand at release
function setPickoffPitcher(t) {
  const q = keyed([[-6, P_OPEN], [-5.4, P_OPEN], [-4.8, P_SET], [-4.4, P_SET], [-4.0, P_WATCH], [-1.05, P_WATCH], [-0.8, PK_LIFT], [-0.5, { ...PK_LIFT, look: 20 }],
                   [-0.22, PK_STRIDE], [0, PK_REL], [0.3, PK_FOLLOW], [1.2, { ...READY, look: 0 }]], t);
  const yaw = lerp(Math.PI / 2, yawTo(v3(0, 0, RUBBER_Z), B1W), smooth((t + 0.6) / 0.5));   // already facing first in the set; squares up to the bag
  const dir = v3(Math.sin(yaw), 0, Math.cos(yaw));               // the step: straight at first base
  const p = v3(0, 0, RUBBER_Z - 0.1).addScaledVector(dir, 2.2 * smooth((t + 0.4) / 0.35));
  p.y = moundY(p.x, p.z) - (t > -0.3 ? 0.05 : 0);
  place(pitcher, true, p, yaw); applyPose(pitcher, q);
}
function b1Spot() { return B1W.clone().add(v3(-1.6, 0, 0.9)); }   // holding the runner: in front of the bag, facing the pitcher
function setRunnerLead(d, q, yaw) { runner.root.visible = true; runner.root.position.copy(B1W).addScaledVector(TO2, d); runner.root.rotation.y = yaw; applyPose(runner, q); }
const FACE_IN = Math.atan2(-Math.SQRT1_2, Math.SQRT1_2);          // facing the infield, square to the base line
const FACE_BAG = Math.atan2(-TO2.x, -TO2.z);                     // facing back toward first base
function setScene(t, s) {
  const play = s.play;
  ump.root.position.set(0.5, 0, 6.0); ump.root.rotation.y = Math.PI; applyPose(ump, U_SET);
  C.root.position.set(0.15, 0, 3.0); C.root.rotation.y = Math.PI;
  for (const [k, p] of Object.entries(HD)) { const [x, z] = homeD[k]; p.root.position.set(x, 0, z); p.root.rotation.y = Math.atan2(-x, -z); applyPose(p, READY); }
  runner.root.visible = false; hitter.root.visible = !s.noHitter; pitcher.root.visible = true;
  zoneG.visible = !!s.show?.zone; SL_MARK.visible = !!s.show?.mark;
  for (const g of Object.values(TUBE)) reveal(g, 0);
  Object.entries(GHOST).forEach(([k, g], i) => reveal(g, !s.show?.ghost?.includes(k) ? 0 : s.show.ghostT0 == null ? 1 : clamp((t - s.show.ghostT0 - 0.28 * i) / 0.3, 0, 1)));   // "what hitters see most": the right-hander's pitches
  leadBar.visible = sight.visible = sightRing.visible = stepArrow.visible = false;
  const P = PLAYS[play];
  // the hitter
  const hL = P ? P.lhb : false;
  place(hitter, hL, v3(hL ? 3.0 : -3.0, 0, -0.9), hL ? -Math.PI / 2 : Math.PI / 2);   // a lefty stands in the first-base side box
  applyPose(hitter, P?.swing ? keyed(swing(-0.04), t) : P?.take ? keyed(take(0), t) : BAT_SET);
  if (P) {                                                        // a pitch
    const pk = PI_[P.pitch], fl = pk.flight;
    setPitcherDelivery(P.lefty, t + fl);
    applyPose(C, keyed([[-0.45, C_SET], [-0.03, P.catcher], [0.8, P.catcher], [1.4, C_SET]], t));
    let bp, path = pk.path;
    if (t < -fl - 0.04) { bp = handPos(pitcher.handR); path = null; }
    else if (t < 0) bp = pathAt(pk.path, t);
    else { bp = handPos(C.handL); path = null; }
    placeBall(bp, path, t);
    if (s.show?.tube) reveal(TUBE[s.show.tube], clamp((t - pk.path.t0) / pk.path.dur, 0, 1));
    if (s.show?.tubeFull) reveal(TUBE[s.show.tubeFull], 1);
    return;
  }
  applyPose(C, C_SET);
  if (play === "walk") {                                          // back up the mound, onto the rubber, looks in
    const a = v3(1.6, 0, -51.8), b = v3(0.5, 0, -60.2), u = clamp(t / 2.5, 0, 1), dist = a.distanceTo(b);
    const p = a.clone().lerp(b, u); p.y = moundY(p.x, p.z);
    const yawA = Math.atan2(b.x - a.x, b.z - a.z), yaw = lerp(yawA, 0, smooth((t - 2.55) / 0.8));   // walking away from home, then turns to face it
    place(pitcher, true, p, yaw);
    const ph = (u * dist / 5.4) % 1;
    let q = t < 2.5 ? { ...runPose(ph, 0.22), lean: 6, nod: 6, shL: [-12 * Math.sin(ph * Math.PI * 2), 10, 0], shR: [12 * Math.sin(ph * Math.PI * 2), 10, 0], elL: 30, elR: 30 } : keyed([[2.5, STAND], [3.4, { ...STAND, nod: 8 }], [4.0, { ...P_OPEN, look: 0 }]], t);
    applyPose(pitcher, q);
    placeBall(handPos(pitcher.handL), null, t);
    return;
  }
  // a runner on first: the left-hander works from the stretch
  const hb = HD.b1; const spot = b1Spot(); hb.root.position.copy(spot); hb.root.rotation.y = yawTo(spot, v3(0, 0, RUBBER_Z));
  applyPose(hb, B_HOLD);
  if (play === "hold") {                                          // he extends his lead; the pitcher's head snaps over; the runner freezes and gives ground
    const q = keyed([[-9, P_SET], [0.45, P_SET], [0.6, P_WATCH], [1.7, P_WATCH], [2.1, P_SET]], t);
    place(pitcher, true, v3(0, MOUND_H, RUBBER_Z - 0.1), Math.PI / 2); applyPose(pitcher, q);
    const d = LEAD_FT + 2.2 * smooth(t / 0.55) - 2.6 * smooth((t - 0.75) / 0.55);
    const bob = Math.abs(Math.sin(clamp(t / 0.55, 0, 1) * Math.PI * 2)) * 0.12;
    setRunnerLead(d, t < 0.7 ? { ...LEADP, drop: -0.75 + bob } : keyed([[0.7, LEADP], [0.95, LEAD_BACK], [1.3, LEAD_BACK], [2.0, LEADP]], t), FACE_IN);
    placeBall(handPos(pitcher.handR), null, t);
    return;
  }
  if (play === "pick") {
    setPickoffPitcher(t);
    // the throw: from his hand at release to the first baseman's glove, gravity only (76 mph over ~60 ft)
    if (!PK_THROW) { setPickoffPitcher(0); const r = handPos(pitcher.handR); const g = spot.clone().add(v3(-0.9, 3.4, 0.25)); const T = PK.arrive; PK_THROW = { r, g, v: g.clone().sub(r).sub(v3(0, -16.1 * T * T, 0)).divideScalar(T) }; setPickoffPitcher(t); }
    // first baseman: holds, gives a target, catches, sweeps the tag down to the back corner of the bag
    const tagAt = B1W.clone().addScaledVector(OUTF, 0.55).addScaledVector(TO2, 0.15);
    const yHold = yawTo(spot, v3(0, 0, RUBBER_Z)), yTag = yawTo(spot, tagAt);
    hb.root.rotation.y = lerp(yHold, yTag, smooth((t - PK.arrive) / 0.14));
    applyPose(hb, keyed([[-0.3, B_HOLD], [0.35, B_CATCH], [PK.arrive + 0.02, B_CATCH], [PK.tag, B_TAG], [PK.tag + 0.7, B_TAG], [PK.tag + 1.4, B_HOLD]], t));
    // the runner: leads off, holds, reads the move, crossover step and a head-first dive back to the bag
    const dLead = 4 + (LEAD_FT - 4) * smooth((t + 6.0) / 1.9);
    let d, q, yaw = FACE_IN, drop;
    if (t < -0.32) { d = dLead; const sh = clamp((t + 6.0) / 1.9, 0, 1); q = { ...LEADP, drop: -0.75 + Math.abs(Math.sin(sh * Math.PI * 3)) * 0.14 * (sh < 1 ? 1 : 0) }; }
    else {
      const k = (t + 0.32);
      yaw = lerp(FACE_IN, FACE_BAG, smooth(k / 0.18));
      d = LEAD_FT - 2.2 * smooth(k / 0.3) - 3.4 * smooth((k - 0.3) / 0.3) - 0.9 * smooth((k - 0.6) / 0.25);
      q = k < 0.3 ? mixPose(LEADP, CROSS, smooth(k / 0.3)) : k < 0.45 ? mixPose(CROSS, DIVE_LAUNCH, (k - 0.3) / 0.15) : k < 0.6 ? mixPose(DIVE_LAUNCH, DIVE_FLY, (k - 0.45) / 0.15) : mixPose(DIVE_FLY, DIVE_FLAT, smooth((k - 0.6) / 0.15));
      drop = k < 0.3 ? -0.6 : lerp(-0.6, -2.25, smooth((k - 0.3) / 0.42));
      q = { ...q, drop };
    }
    setRunnerLead(d, q, yaw);
    if (t > -0.32) runner.root.position.addScaledVector(OUTF, 0.7 * smooth((t + 0.02) / 0.5));   // toward the back corner, away from the tag
    // the ball
    let bp, path = null;
    if (t < 0) bp = handPos(pitcher.handR);
    else if (t < PK.arrive) { const { r, v } = PK_THROW; bp = r.clone().addScaledVector(v, t).add(v3(0, -16.1 * t * t, 0)); }
    else bp = handPos(hb.handL);
    placeBall(bp, path, t);
    if (s.show?.lead) { const a = B1W.clone().addScaledVector(TO2, 0.9), b = B1W.clone().addScaledVector(TO2, Math.max(1, d - 0.6)); between(leadBar, a.setY(0.06), b.setY(0.06)); leadBar.visible = true; LEAD_MID = a.clone().lerp(b, 0.5); }
    if (s.show?.step) stepArrow.visible = true;
    if (s.show?.sight && t < -0.9) {
      pitcher.neck.updateWorldMatrix(true, false); const eye = pitcher.neck.getWorldPosition(new THREE.Vector3()).add(v3(0, 0.35, 0));
      runner.neck.updateWorldMatrix(true, false); const rh = runner.neck.getWorldPosition(new THREE.Vector3()).add(v3(0, 0.2, 0));
      between(sight, eye, rh); sight.visible = true; sightRing.position.set(runner.root.position.x, 0.08, runner.root.position.z); sightRing.visible = true;
    }
  }
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
  hookP: (u) => [mixV(v3(4.6, 4.4, -46.6), v3(4.0, 4.6, -47.6), easeIO(u)), v3(-0.4, 5.8, -60), 50],                 // in front, first-base side: the left arm coming through
  hookB: (u) => [mixV(v3(4.2, 6.0, 1.3), v3(4.0, 5.9, 1.0), u), v3(-0.6, 4.6, -14), 50],                           // over the left-handed hitter's shoulder
  behind: (u) => [mixV(v3(0, 17, 27), v3(0, 16.5, 25.5), u), v3(0, 3.4, -30), 50],                                  // high behind home: both release points, the paths in
  eye: (u) => [v3(-2.45, 5.35, -0.55), v3(0.3, 4.6, -54), lerp(22, 20, u)],     // the right-handed hitter's eyes
  plate: (u) => [v3(-4.5, 17, -205), v3(0, 3.2, -18), lerp(6.8, 6.3, u)],                                      // the center-field camera
  front: (u) => [mixV(v3(-1.6, 4.6, -8.5), v3(-1.3, 4.6, -7.8), u), v3(2.8, 4.4, -0.6), 40],                       // in front of him: the swing through it
  zone: (u) => [mixV(v3(-4.5, 13, 13), v3(-4.2, 12.4, 12.2), easeIO(u)), v3(0.5, 2.0, -3.5), 34],                  // high behind the plate, third-base side: the zone and the break
  wide: (u) => [mixV(v3(-48, 36, -56), v3(-44, 33, -57), easeIO(u)), v3(36, 0, -64), 32],                          // high behind the mound: the lefty, the runner, first base
  pov: (u) => [mixV(v3(-9, 10, -60), v3(-8.2, 9.6, -60.2), u), v3(52, 2.5, -69), 32],                               // over the left-hander's shoulder: the runner in front of him
  pick: (u) => [mixV(v3(-24, 13, -55), v3(-21, 12, -56), u), v3(52, 2.5, -66), 32],                              // behind the mound, third-base side, toward first
  replay: (u) => [mixV(v3(86, 10, -74), v3(84.5, 9.6, -73), u), v3(45, 2, -63.5), 44],                            // beyond first base, right-field side: the lead, the dive, the tag
  low: (u) => [mixV(v3(12, 6, -92), v3(11, 5.6, -89), u), v3(0, 5, -58), 34],                                       // behind the mound, first-base side: the left arm coming through
  catcherV: (u) => [mixV(v3(2.8, 4.6, 8.8), v3(2.6, 4.5, 8.0), u), v3(0.6, 3.6, -20), 40],                            // behind the plate, first-base side: the left-handed hitter
  first: (u) => [mixV(v3(80, 5, -88), v3(78, 4.8, -86), u), v3(38, 3.2, -65), 42],                                   // behind first base: the runner, the pitcher beyond
  walk: (u) => [mixV(v3(2.8, 1.7, -39.5), v3(2.3, 1.6, -42), easeIO(u)), v3(0.4, 4.6, -60), 38],                    // low, in front of the mound: back up to the rubber
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
function overlays(s, v) {
  if ($("spd")) { const sp = s.freeze && v >= s.freeze[0] && v < s.freeze[1] ? "freeze" : s.speed; $("spd").textContent = SPEEDS[sp] ?? ""; $("spd").style.opacity = sp === "none" ? 0 : 1; $("spd").className = "spd " + (sp === "rt" ? "rt" : "sl"); }
}

// labels that point at something in the scene follow its projected position
function pin(id, p) {
  const el = $(id); if (!el || !p) return;
  const q = p.clone().project(cam);
  el.style.left = `${((q.x + 1) / 2 * W).toFixed(1)}px`; el.style.top = `${((1 - q.y) / 2 * H).toFixed(1)}px`;
}
function renderAt(v) {
  const { s, t, u } = shotAt(v);
  const c = CAMS[s.cam](u, t, s);
  renderer.setScissorTest(s.mode === "split");
  if (s.mode === "split") {                                       // the same pitch side by side: right-hander on the left, left-hander on the right
    for (const [x, play, tb] of [[0, "fb_r", "fb_r"], [W / 2, "fb_l", "fb_l"]]) {
      setScene(t, { ...s, play, show: { tube: tb } });
      frame(cam, c[0], c[1], c[2], (W / 2) / H);
      renderer.setViewport(x, 0, W / 2, H); renderer.setScissor(x, 0, W / 2, H);
      renderer.render(scene, cam);
    }
  } else {
    setScene(t, s);
    renderer.setViewport(0, 0, W, H);
    frame(cam, c[0], c[1], c[2], W / H);
    const g = c[2] < 12 ? 0.008 : 0.022; BALL.glow.scale.set(g, g, 1);
    renderer.render(scene, cam);
    pin("leadw", LEAD_MID); pin("stepw", stepArrow.localToWorld(v3(3.6, 0, 0)));
  }
  overlays(s, v);
}

let last = -1;
function seek(time) { if (time === last) return; last = time; renderAt(time); }
window.addEventListener("hf-seek", (e) => seek(e.detail.time));
window.__fieldRender = renderAt;
document.fonts.ready.then(() => seek(window.__hfThreeTime || 0));
seek(window.__hfThreeTime || 0);
