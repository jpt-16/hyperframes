// "First base is harder than it looks": the field, the infield, a first baseman who saves bad throws and hits one out, in three.js.
// Everything is a pure function of HyperFrames time (hf-seek), so each frame is exact and repeatable.
// Units are feet. Home plate's back point is the origin, +x points toward first base's side, -z toward center field.
// The home run comes from tools/physics.py via window.__PLAY; every throw is worked out here from the 3D figures themselves.
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
// our team (white): the first baseman and his infield; the other team (dark): the batter-runner, and its battery and
// defense when the first baseman bats
const FB = makePlayer(KIT.home, { glove: true });                 // the first baseman
const FBB = makePlayer(KIT.home, { helmet: true, bat: true });    // the same first baseman, batting
const INF = { ss: makePlayer(KIT.home, { glove: true }), b2: makePlayer(KIT.home, { glove: true }), b3: makePlayer(KIT.home, { glove: true }) };
const pitcher = makePlayer(KIT.home, { glove: true }), C = makePlayer(KIT.home, { glove: true, catcher: true });
const ump = makePlayer(KIT.ump, { catcher: true }), U1 = makePlayer(KIT.ump);
const runner = makePlayer(KIT.away, { helmet: true });
const OF = { lf: [-118, -262], cf: [0, -312], rf: [118, -262] };
const HOF = {}; for (const k of Object.keys(OF)) HOF[k] = makePlayer(KIT.home, { glove: true });
const awayD = { b1: [66, -82], b2: [30, -128], ss: [-28, -118], b3: [-58, -76], lf: [-118, -262], cf: [0, -312], rf: [118, -262] };
const AD = {}; for (const k of Object.keys(awayD)) AD[k] = makePlayer(KIT.away, { glove: true });
const awayP = makePlayer(KIT.away, { glove: true }), awayC = makePlayer(KIT.away, { glove: true, catcher: true });
const DEF = [FB, ...Object.values(INF), pitcher, C, U1, runner, ...Object.values(HOF)];
const BAT = [FBB, awayP, awayC, ...Object.values(AD)];
for (const p of [...DEF, ...BAT, ump]) scene.add(p.root);

// ------------------------------------------------------------------ helpers
const V = (a) => v3(a[0], a[1], a[2]);
const HR = PLAY.hr;
function pathAt(path, t) {
  const u = (t - path.t0) * path.hz, n = path.p.length - 1;
  if (u <= 0) return V(path.p[0]);
  if (u >= n) return V(path.p[n]);
  const i = Math.floor(u), f = u - i, a = path.p[i], b = path.p[i + 1];
  return v3(lerp(a[0], b[0], f), lerp(a[1], b[1], f), lerp(a[2], b[2], f));
}
const wpos = (o) => { o.updateWorldMatrix(true, false); return o.getWorldPosition(new THREE.Vector3()); };
const B1W = v3(63.64, 0, -63.64), B2W = v3(0, 0, -127.28), HOMEW = v3(0, 0, 0);
const flat = (a) => v3(a.x, 0, a.z);
const unit = (a, b) => flat(b).sub(flat(a)).normalize();
const G = -32.17;

// ------------------------------------------------------------------ poses
// infielders (right-handed throwers: glove on the left hand)
const F_FIELD = { drop: -1.3, lean: 56, nod: -30, hipL: [80, 20], hipR: [50, 24], knL: 82, knR: 60, shL: [60, -10, 0], elL: 14, shR: [40, 10, 0], elR: 40 };
const F_BACK = { drop: -1.3, lean: 56, nod: -30, hipL: [80, 20], hipR: [50, 24], knL: 82, knR: 60, shL: [60, -30, 0], elL: 14, shR: [30, 16, 0], elR: 60 };   // backhand, glove across
const F_PLANT = { drop: -0.6, lean: 12, twist: -60, look: 60, nod: -4, shL: [80, 20, 0], elL: 30, shR: [-30, 78, 0], elR: 95, hipL: [10, 12], hipR: [38, 12], knL: 40, knR: 30 };
const F_REL = { drop: -0.6, lean: 30, twist: 30, nod: 6, shL: [20, 30, 0], elL: 60, shR: [165, 20, 0], elR: 15, hipL: [46, 8], hipR: [-26, 10], knL: 40, knR: 30 };
const F_FOL = { drop: -0.8, lean: 46, twist: 48, nod: 10, shL: [10, 30, 0], elL: 70, shR: [55, -25, 0], elR: 25, hipL: [55, 8], hipR: [10, 10], knL: 52, knR: 70 };
const F_OFFREL = { drop: -0.75, lean: 6, side: -16, twist: 30, nod: 2, shL: [30, 34, 0], elL: 60, shR: [150, 30, 0], elR: 20, hipL: [26, 16], hipR: [14, 16], knL: 46, knR: 36 };   // throwing while falling away
const F_OFFFOL = { ...F_OFFREL, side: -22, lean: 20, twist: 44, shR: [70, -10, 0], elR: 30, drop: -0.95 };
const F_BARE = { drop: -1.15, lean: 54, nod: -24, hipL: [74, 10], hipR: [-6, 10], knL: 72, knR: 30, shL: [36, 22, 0], elL: 50, shR: [64, 2, 0], elR: 10 };   // charging, bare hand to the ball
const F_SIDE = { drop: -0.7, lean: 30, twist: 34, side: 12, nod: 0, shL: [24, 34, 0], elL: 60, shR: [96, 84, 0], elR: 22, hipL: [52, 8], hipR: [-20, 10], knL: 42, knR: 36 };   // sidearm, on the run
const F_DIVE = { drop: -2.25, pelvisTilt: 82, lean: 4, nod: -48, hipL: [-4, 12], hipR: [-6, 10], knL: 20, knR: 34, shL: [168, 18, 0], elL: 8, shR: [120, 30, 0], elR: 30 };
const F_KNEE = { drop: -1.5, pelvisTilt: 6, lean: 14, nod: -6, hipL: [84, 10], hipR: [8, 10], knL: 96, knR: 100, ankL: -20, ankR: 40, shL: [40, 20, 0], elL: 50, shR: [30, 20, 0], elR: 60 };
const F_KNEE_REL = { ...F_KNEE, twist: 34, lean: 24, shL: [20, 32, 0], elL: 60, shR: [160, 20, 0], elR: 14 };
const F_KNEE_FOL = { ...F_KNEE, twist: 46, lean: 34, shL: [10, 32, 0], elL: 70, shR: [60, -20, 0], elR: 26 };
const F_FIST = { lean: 6, nod: -8, shR: [150, 22, 0], elR: 80, shL: [24, 12, 0], elL: 40, hipL: [6, 8], hipR: [6, 8], knL: 10, knR: 10 };
const F_POINT = { lean: 4, nod: -4, shR: [92, 4, 0], elR: 6, shL: [20, 12, 0], elL: 40, hipL: [6, 8], hipR: [6, 8], knL: 10, knR: 10 };
// the first baseman: right foot on the bag, the glove-side (left) leg reaching toward the throw
// legs are solved (legsIK) from the pelvis height and where each foot is planted: back = right foot (on the bag) behind
// the pelvis, front = left foot ahead of it, in feet. Both feet stay on the dirt; nothing floats or sinks.
const B_SET = { drop: -0.45, back: 0.6, front: 0.6, lean: 18, nod: -6, shL: [44, 16, 0], elL: 50, shR: [38, 14, 0], elR: 50 };   // at the bag, feet set, reading the throw
const B_TARGET = { drop: -0.2, back: 0.45, front: 0.5, lean: 8, nod: -6, shL: [96, 14, 0], elL: 24, shR: [40, 12, 0], elR: 60 };   // standing tall, glove up as a target
const B_REACH = { ...B_TARGET, shL: [96, 6, 0], elL: 4, lean: 12 };                                                   // a reach without stretching (the comparison)
const B_FULL = { drop: -1.2, back: 2.0, front: 2.05, lean: 52, nod: -12, shL: [100, 8, 0], elL: 4, shR: [28, 10, 0], elR: 50 };   // full extension: a ~4 ft split, front knee bent
const B_LOW = { drop: -1.35, back: 1.9, front: 1.8, lean: 60, nod: 2, shL: [70, 6, 0], elL: 4, shR: [28, 10, 0], elR: 50 };
const B_SCOOP = { drop: -1.45, back: 1.75, front: 1.85, lean: 64, nod: 8, shL: [58, 4, 0], elL: 4, shR: [24, 12, 0], elR: 50 };   // glove low and out front, short hop
const B_HIGH = { drop: 0.05, back: 0.25, front: 0.35, ankleY: 0.45, lean: -4, nod: -34, shL: [172, 12, 0], elL: 6, shR: [40, 12, 0], elR: 40 };   // up on his toes
const B_WIDE = { drop: -0.95, back: 1.3, front: 1.9, lean: 40, nod: -6, shL: [82, 36, 0], elL: 8, shR: [30, 12, 0], elR: 50 };
const B_TALL = { drop: -0.25, back: 0.5, front: 0.6, lean: 12, nod: -8, shL: [70, 14, 0], elL: 30, shR: [36, 12, 0], elR: 56 };      // stays tall: never gets down to it
const B_STAB = { drop: -0.55, back: 0.8, front: 0.9, lean: 30, nod: 6, shL: [34, 6, 0], elL: 18, shR: [30, 12, 0], elR: 56 };       // a late stab down at it
const B_SHOW = { drop: -0.3, back: 0.5, front: 0.5, lean: 10, nod: -4, shL: [64, 18, 0], elL: 70, shR: [30, 12, 0], elR: 50 };
function legsIK(q) {                                                 // two-bone leg IK in the figure's forward plane (thigh 1.42 ft, shin 1.43 ft)
  if (q.back == null) return q;
  const out = { ...q }, L1 = 1.42, L2 = 1.43, dy = 3.1 + (q.drop ?? 0) - (q.ankleY ?? 0.18);
  for (const [k, dz] of [["R", -q.back], ["L", q.front]]) {
    const d = Math.min(Math.hypot(dy, dz), L1 + L2 - 1e-3), phi = Math.atan2(dz, dy);
    const a = Math.acos(clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1)), b = Math.acos(clamp((L1 * L1 + L2 * L2 - d * d) / (2 * L1 * L2), -1, 1));
    const flex = (phi + a) / D2R, kn = (Math.PI - b) / D2R;
    out[`hip${k}`] = [flex, 6]; out[`kn${k}`] = kn; out[`ank${k}`] = flex - kn;                       // foot flat on the ground
  }
  return out;
}
const U1_SET = { drop: -0.9, lean: 34, nod: -8, hipL: [44, 22], hipR: [44, 22], knL: 56, knR: 56, shL: [20, 18, 0], elL: 40, shR: [20, 18, 0], elR: 40 };
const U1_OUT = { drop: -0.3, lean: 6, twist: 20, nod: -4, shR: [150, 30, 0], elR: 95, shL: [20, 14, 0], elL: 40, hipL: [14, 14], hipR: [14, 14], knL: 16, knR: 16 };
const U1_SAFE = { drop: -0.4, lean: 12, hipL: [18, 14], hipR: [18, 14], knL: 22, knR: 22, shL: [90, 88, 0], elL: 5, shR: [90, 88, 0], elR: 5 };
const U_SET = { drop: -1.0, lean: 30, nod: -6, hipL: [52, 28], hipR: [52, 28], knL: 68, knR: 68, shL: [30, 20, 0], elL: 60, shR: [30, 20, 0], elR: 60 };
const C_SET = { ...CROUCH, shL: [62, 18, 0], elL: 40, shR: [20, 10, 0], elR: 50, nod: -18 };
// batting (a right-handed hitter)
const BAT_SET = { drop: -0.35, lean: 18, look: 80, nod: -4, hipL: [22, 14], hipR: [22, 14], knL: 26, knR: 26, shL: [55, 6, 0], shR: [60, 34, 0], elL: 95, elR: 110, twist: 20 };
const BAT_LOAD = { ...BAT_SET, twist: 34, pelvisTwist: -14, hipL: [44, 10], knL: 52, hipR: [26, 18], knR: 34 };                       // hands back, front knee in
const BAT_STRIDE = { ...BAT_LOAD, drop: -0.55, hipL: [14, 26], knL: 20, hipR: [30, 18], knR: 38, twist: 30 };                       // the stride: front foot down, hands still back
const BAT_HIT = { drop: -0.55, lean: 30, look: 50, nod: -12, twist: -40, pelvisTwist: 60, hipL: [24, 28], knL: 12, hipR: [18, 12], knR: 46, shL: [80, -10, 0], elL: 10, shR: [74, 10, 0], elR: 20 };
const BAT_FIN = { drop: -0.3, lean: 12, look: 20, twist: -80, pelvisTwist: 90, hipL: [16, 26], knL: 8, hipR: [6, 12], knR: 56, shL: [140, 10, 0], elL: 100, shR: [150, -40, 0], elR: 110 };
const BAT_WATCH = { ...BAT_FIN, lean: 4, drop: -0.1, shR: [100, -10, 0], elR: 70, shL: [40, 10, 0], elL: 60, look: 30, nod: -16 };
const swingHR = [[-0.75, BAT_SET], [-0.45, BAT_LOAD], [-0.2, BAT_STRIDE], [0, BAT_HIT], [0.3, BAT_FIN], [1.3, BAT_WATCH]];
const P_SET = { lean: 4, look: 80, nod: 4, shL: [42, 8, 0], elL: 105, shR: [38, -4, 0], elR: 112, hipL: [4, 6], hipR: [4, 6], knL: 8, knR: 8 };
const P_LIFT = { lean: -4, look: 80, shL: [48, 8, 0], elL: 100, shR: [44, -4, 0], elR: 108, hipL: [100, 4], knL: 105, hipR: [6, 6], knR: 14, drop: -0.15 };
const P_STRIDE = { lean: 6, look: 40, drop: -0.6, twist: -50, shL: [80, 35, 0], elL: 25, shR: [-55, 80, 0], elR: 85, hipL: [52, 4], knL: 28, hipR: [-28, 6], knR: 38 };
const P_REL = { lean: 42, nod: 8, drop: -1.0, twist: 28, shL: [12, 32, 0], elL: 85, shR: [168, 22, 0], elR: 8, hipL: [72, 4], knL: 22, hipR: [-18, 6], knR: 92 };
const P_FOLLOW = { lean: 62, nod: 18, drop: -1.25, twist: 48, shL: [8, 38, 0], elL: 95, shR: [58, -24, 0], elR: 22, hipL: [82, 4], knL: 38, hipR: [34, 6], knR: 84 };

// ------------------------------------------------------------------ the plays (t = 0: the ball reaches the first baseman's glove; for "hr", contact)
// fielder: who throws, from where; kind: how he fields and throws; fb: how the first baseman takes it (pose, yaw off the
// thrower's line toward home, + = his glove side); bounce: a short hop, ft in front of the glove; runner: when his foot hits the bag
const PL = {
  hook:   { who: "ss", start: [-31, -117], field: [-41, -113], kind: "backhand", off: true, mph: 80, fb: { pose: B_FULL, yaw: 8 }, runner: 0.07, call: "out" },
  low:    { who: "b2", start: [28, -120], field: [36, -108], kind: "field", mph: 74, fb: { pose: B_LOW, yaw: 0 }, runner: 0.35, call: "out" },
  glove:  { who: "ss", start: [-28, -118], field: [-24, -110], kind: "field", mph: 82, fb: { pose: B_FULL, yaw: 26 }, runner: 0.3, call: "out" },
  pull:   { who: "b3", start: [-58, -76], field: [-52, -72], kind: "field", mph: 84, fb: { pose: B_FULL, yaw: 42 }, runner: 0.85, call: "out" },
  scoop:  { who: "ss", start: [-26, -118], field: [-20, -98], kind: "charge", off: true, mph: 76, fb: { pose: B_SCOOP, yaw: 4 }, bounce: 3.6, runner: 0.12, call: "out" },
  late:   { same: "scoop", fb: { late: true }, runner: 0.12, call: "safe" },
  high:   { who: "ss", start: [-28, -118], field: [-26, -112], kind: "field", mph: 82, fb: { pose: B_HIGH, yaw: 0, toes: 0.28 }, runner: 0.3, call: "out" },
  wide:   { who: "b3", start: [-58, -76], field: [-50, -70], kind: "field", off: true, mph: 80, fb: { pose: B_WIDE, yaw: 70, off: 6.5 }, runner: 0.0, call: "safe" },
  p3b:    { who: "b3", start: [-58, -78], field: [-66, -86], kind: "backhand", mph: 82, fb: { pose: B_LOW, yaw: 14 }, runner: 0.15, call: "out", react: "fist" },
  p2b:    { who: "b2", start: [30, -126], field: [42, -114], kind: "dive", mph: 66, fb: { pose: B_FULL, yaw: -14 }, runner: 0.18, call: "out", react: "point" },
  pss:    { who: "ss", start: [-26, -118], field: [-12, -80], kind: "bare", mph: 72, fb: { pose: B_SCOOP, yaw: 18 }, bounce: 4.5, runner: 0.08, call: "out", react: "fist" },
};
for (const [k, p] of Object.entries(PL)) if (p.same) PL[k] = { ...PL[p.same], ...p, fb: { ...PL[p.same].fb, ...p.fb } };
const EXCH = { field: 0.75, backhand: 0.85, charge: 0.6, bare: 0.42, dive: 1.15 };
const BAG_FOOT = (u) => B1W.clone().addScaledVector(u, 0.32);       // his right foot against the near edge of the bag

// ------------------------------------------------------------------ the first baseman at the bag
function fbYaw(p) { const F = v3(p.field[0], 0, p.field[1]); return yawTo(B1W, F) + (p.fb.yaw ?? 0) * D2R; }
function anchorFoot(P, at, y = 0) {                                  // slide the figure so his right foot stays put
  P.root.position.set(0, y, 0); const f = wpos(P.ftR); P.root.position.set(at.x - f.x, y, at.z - f.z);
}
function setFirstBaseman(p, t) {
  FB.root.visible = true;
  const F = v3(p.field[0], 0, p.field[1]), u = unit(B1W, F), yaw0 = yawTo(B1W, F), yaw = fbYaw(p);
  const commit = -0.34;                                             // he reads the throw, then commits to the stretch
  if (p.fb.late) {                                                  // stays tall, reaches down too late; the ball skips by
    const q = legsIK(keyed([[-3, B_SET], [-0.6, B_TARGET], [-0.06, B_TALL], [0.08, B_STAB], [0.45, B_STAB], [0.9, { ...B_STAB, lean: 20 }]], t));
    FB.root.rotation.y = lerp(yaw0, yaw0 + 0.9, smooth((t - 0.35) / 0.5)); applyPose(FB, q);
    anchorFoot(FB, BAG_FOOT(u));
    if (t > 0.35) FB.root.position.add(v3(1.6, 0, 1.6).multiplyScalar(smooth((t - 0.35) / 0.8)));   // turns and goes after it, too late
    return;
  }
  const pose = p.fb.pose;
  const q = legsIK(keyed([[-3, B_SET], [-0.7, B_TARGET], [commit, B_TARGET], [-0.02, pose], [0.3, pose], [0.95, B_SHOW]], t));
  FB.root.rotation.y = t < commit ? yaw0 : lerp(yaw0, yaw, smooth((t - commit) / 0.3));
  applyPose(FB, q);
  if (p.fb.off) {                                                   // too wide to stay on the bag: off it, toward the throw, to keep it in front
    anchorFoot(FB, BAG_FOOT(u));
    const left = v3(Math.cos(yaw0), 0, -Math.sin(yaw0));
    FB.root.position.addScaledVector(left, p.fb.off * smooth((t - commit + 0.12) / 0.42));
  } else anchorFoot(FB, BAG_FOOT(u), (p.fb.toes ?? 0) * smooth((t - commit) / 0.3) * (t < 0.6 ? 1 : 1 - smooth((t - 0.6) / 0.3)));
}

// ------------------------------------------------------------------ the infielder: fields it, throws, reacts
function setFielder(p, t, th) {
  const P = INF[p.who], F = v3(p.field[0], 0, p.field[1]), S = v3(p.start[0], 0, p.start[1]);
  const tr = th.tr, tf = tr - EXCH[p.kind];
  const run = smooth((t - (tf - 1.0)) / 1.0);
  const pos = S.clone().lerp(F, run);
  const away = unit(B1W, F);                                         // away from first base
  if (p.off) pos.addScaledVector(away, 1.8 * smooth((t - tr + 0.15) / 0.5));
  if (p.kind === "bare") pos.addScaledVector(unit(F, B1W).add(unit(F, HOMEW)).normalize(), 5 * smooth((t - tf + 0.05) / (tr - tf + 0.4)));
  P.root.position.copy(pos);
  const faceBall = yawTo(pos, HOMEW), faceFirst = yawTo(pos, B1W);
  P.root.rotation.y = t < tf + 0.08 ? faceBall : lerp(faceBall, faceFirst, smooth((t - tf - 0.08) / Math.max(0.2, tr - tf - 0.25)));
  if (p.kind === "dive") P.root.rotation.y = t < tf + 0.35 ? yawTo(S, F) : lerp(yawTo(S, F), faceFirst, smooth((t - tf - 0.35) / 0.4));
  const fieldPose = { field: F_FIELD, backhand: F_BACK, charge: F_FIELD, bare: F_BARE, dive: F_DIVE }[p.kind];
  let rel = p.off ? F_OFFREL : F_REL, fol = p.off ? F_OFFFOL : F_FOL, plant = F_PLANT;
  if (p.kind === "bare") { rel = F_SIDE; fol = { ...F_SIDE, twist: 50, shR: [60, 40, 0] }; plant = { ...F_BARE, drop: -0.8, lean: 36 }; }
  if (p.kind === "dive") { rel = F_KNEE_REL; fol = F_KNEE_FOL; plant = F_KNEE; }
  const ph = ((t + 5) * 2.3) % 1;
  let q;
  if (t < tf - 0.25) q = run > 0.02 && run < 0.98 ? runPose(ph, 0.6) : READY;
  else {
    const frames = [[tf - 0.25, p.kind === "dive" ? { ...runPose(ph, 0.7), lean: 40 } : READY], [tf, fieldPose], [tf + 0.12, fieldPose], [tr - 0.22, plant], [tr, rel], [tr + 0.35, fol]];
    if (p.kind === "dive") frames.splice(3, 0, [tf + 0.45, F_KNEE]);
    const react = p.react === "fist" ? F_FIST : p.react === "point" ? F_POINT : { ...READY, lean: 10, drop: -0.2 };
    frames.push([0.35, fol], [0.75, react], [2.0, react]);
    q = keyed(frames, t);
  }
  if (p.kind === "dive" && t > tf - 0.25 && t < tf + 0.45) P.root.position.addScaledVector(unit(S, F), -1.2 * (1 - smooth((t - tf + 0.25) / 0.3)));
  applyPose(P, q);
  return { P, tf };
}

// ------------------------------------------------------------------ the throws: from the fielder's hand to the first baseman's glove
// worked out once from the figures: the fielder posed at release, the first baseman posed at the catch
const TH = {};
function throwFor(name) {
  if (TH[name]) return TH[name];
  const p = PL[name];
  setFirstBaseman(p.same ? PL[p.same] : p, 0); const Gp = wpos(FB.handL);
  const dist0 = flat(Gp).distanceTo(v3(p.field[0], 0, p.field[1]));
  const vh = p.mph * 1.4667 * 0.98;                                  // ft/s along the ground (the throw is nearly flat)
  const tr = -dist0 / vh;
  setFielder(p, tr, { tr }); const R = wpos(INF[p.who].handR);
  const th = { tr, R, Gp };
  if (!p.bounce) { const T = -tr; th.v = Gp.clone().sub(R).sub(v3(0, 0.5 * G * T * T, 0)).divideScalar(T); }
  else {                                                             // a short hop: down into the dirt just in front of him, up into the glove
    const d = unit(R, Gp), Bp = flat(Gp).addScaledVector(d, -p.bounce).setY(0.13);
    const v2h = vh * 0.78, T2 = flat(Gp).distanceTo(flat(Bp)) / v2h, T1 = -tr - T2;
    th.v = Bp.clone().sub(R).sub(v3(0, 0.5 * G * T1 * T1, 0)).divideScalar(T1);
    th.Bp = Bp; th.T1 = T1; th.T2 = T2;
    th.v2 = d.clone().multiplyScalar(v2h); th.v2.y = (Gp.y - 0.13 - 0.5 * G * T2 * T2) / T2;
    th.e = th.v2.y / -(th.v.y + G * T1);                             // the bounce this implies (vertical speed kept)
  }
  // what the ball does if nobody catches it (the "late" first baseman): on past him, a second bounce, rolling into foul ground
  const samples = []; let pos, vel;
  if (th.Bp) { pos = th.Bp.clone(); vel = th.v2.clone(); } else { pos = R.clone(); vel = th.v.clone(); }
  const t0 = th.Bp ? tr + th.T1 : tr; const dt = 1 / 240;
  for (let k = 0; k < 240 * 3; k++) {
    samples.push(pos.clone()); vel.y += G * dt; pos.addScaledVector(vel, dt);
    if (pos.y < 0.13) { pos.y = 0.13; vel.y = Math.abs(vel.y) * 0.42; vel.x *= 0.7; vel.z *= 0.7; if (vel.y < 1.5) vel.y = 0; }
    if (vel.y === 0) { const s = Math.hypot(vel.x, vel.z); const k2 = Math.max(0, s - 18 * dt) / Math.max(s, 1e-6); vel.x *= k2; vel.z *= k2; }
  }
  th.loose = { t0, samples };
  TH[name] = th; return th;
}
function throwPos(th, t) {                                           // t: play time, between release and the glove
  const k = t - th.tr;
  if (!th.Bp) return th.R.clone().addScaledVector(th.v, k).add(v3(0, 0.5 * G * k * k, 0));
  if (k < th.T1) return th.R.clone().addScaledVector(th.v, k).add(v3(0, 0.5 * G * k * k, 0));
  const k2 = k - th.T1; return th.Bp.clone().addScaledVector(th.v2, k2).add(v3(0, 0.5 * G * k2 * k2, 0));
}
const loosePos = (th, t) => { const i = clamp(Math.round((t - th.loose.t0) * 240), 0, th.loose.samples.length - 1); return th.loose.samples[i].clone(); };
// the ground ball to the fielder, hopping in from the plate
function grounderPos(p, tf, glove, t) {
  const S = v3(0.5, 0.4, -3), T = S.distanceTo(glove) / 95, u = clamp((t - (tf - T)) / T, 0, 1);
  const q = S.clone().lerp(glove, u); q.y = lerp(S.y, glove.y, u) + 4.5 * Math.abs(Math.sin(u * Math.PI * 3)) * (1 - u) * (u < 0.9 ? 1 : 0);
  return q;
}

// ------------------------------------------------------------------ the batter-runner: out of the box, through the bag
const R0 = v3(-2.2, 0, -1.2), RDIR = unit(R0, B1W), RLEN = flat(R0).distanceTo(B1W) - 0.4, FOUL = v3(RDIR.z, 0, -RDIR.x).multiplyScalar(-1);
const sprint = (t) => { t = Math.max(t, 0); return 27 * (t - 0.8 * (1 - Math.exp(-t / 0.8))); };
let T_LINE = 0; for (let s = 0; sprint(T_LINE) < RLEN; T_LINE += 0.001);   // ~4.2 s home to first
function setRunner(tBag, t) {
  runner.root.visible = true;
  const tg = t - (tBag - T_LINE);
  let s = sprint(tg);
  if (s > RLEN) { const over = tg - T_LINE; s = RLEN + 26 * over - 6 * over * over; s = Math.min(s, RLEN + 28); }
  const lane = 1.4 * (1 - smooth((s - (RLEN - 14)) / 10)) + 4 * smooth((s - RLEN - 6) / 20);
  runner.root.position.copy(R0).addScaledVector(RDIR, s).addScaledVector(FOUL, lane);
  runner.root.rotation.y = yawTo(R0, B1W);
  const v = (sprint(tg + 0.02) - sprint(tg - 0.02)) / 0.04;
  applyPose(runner, tg < 0 ? { ...BAT_SET } : s > RLEN + 12 ? runPose((s / 11) % 1, 0.4) : runPose((s / 11) % 1, clamp(v / 25, 0.35, 1)));
}

// ------------------------------------------------------------------ graphics: the stretch line, the foot on the bag, the ball
const flatMat = (c, op) => new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: op, depthWrite: false, side: THREE.DoubleSide });
const gainBar = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.16, 1), flatMat(0xff6a3d, 0.95)); gainBar.visible = false; scene.add(gainBar);
const gainDots = [0, 1].map(() => { const m = new THREE.Mesh(new THREE.SphereGeometry(0.16, 14, 10), flatMat(0xff6a3d, 0.95)); m.visible = false; scene.add(m); return m; });
const ghostGlove = new THREE.Mesh(new THREE.SphereGeometry(0.3, 14, 10), flatMat(0xffffff, 0.35)); ghostGlove.visible = false; scene.add(ghostGlove);
const footRing = new THREE.Mesh(new THREE.RingGeometry(0.85, 1.1, 40), flatMat(0x56d1ff, 0.9)); footRing.rotation.x = -Math.PI / 2; footRing.visible = false; scene.add(footRing);
function between(m, a, b) { const d = b.clone().sub(a); m.position.copy(a).addScaledVector(d, 0.5); m.scale.set(1, 1, Math.max(0.01, d.length())); m.lookAt(b); }
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
function placeBall(pos, trailFn) {                                   // trailFn(dt) -> where the ball was dt seconds ago (or null)
  BALL.m.position.copy(pos); BALL.glow.position.copy(pos);
  for (let i = 0; i < BALL.trail.length; i++) { const p = trailFn ? trailFn((i + 1) * 0.008) : null, tr = BALL.trail[i]; tr.visible = !!p; if (p) tr.position.copy(p); }
}
const HR_TUBE = (() => {
  const g = new THREE.Group(), pts = Array.from({ length: 121 }, (_, i) => pathAt(HR.path, HR.path.dur * i / 120));
  for (let i = 0; i < pts.length - 1; i++) { const a = pts[i], b = pts[i + 1]; const m = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.7, a.distanceTo(b) + 0.05), new THREE.MeshBasicMaterial({ color: 0xffd84d, transparent: true, opacity: 0.8, depthWrite: false })); m.position.copy(a).lerp(b, 0.5); m.lookAt(b); m.userData.u = (i + 1) / (pts.length - 1); g.add(m); }
  g.visible = false; scene.add(g); return g;
})();
function reveal(g, u) { g.visible = u > 0; for (const m of g.children) m.visible = m.userData.u <= u + 1e-6; }

// ------------------------------------------------------------------ one frame of a play
let GAIN = null, FOOT = null;
function setScene(t, s) {
  const play = s.play;
  gainBar.visible = ghostGlove.visible = footRing.visible = false; gainDots.forEach((d) => (d.visible = false)); reveal(HR_TUBE, 0);
  GAIN = FOOT = null;
  ump.root.position.set(0.5, 0, 6.0); ump.root.rotation.y = Math.PI; applyPose(ump, U_SET);
  if (play === "hr" || play === "trot") return setBatting(t, s);
  for (const p of BAT) p.root.visible = false; for (const p of DEF) p.root.visible = true; runner.root.visible = false;
  const p = PL[play];
  // everyone else
  pitcher.root.position.set(0, MOUND_H, -59.5); pitcher.root.rotation.y = 0; applyPose(pitcher, { ...READY, drop: -0.3, lean: 14 });
  C.root.position.set(0.15, 0, 3.0); C.root.rotation.y = Math.PI; applyPose(C, C_SET);
  for (const [k, [x, z]] of Object.entries(OF)) { HOF[k].root.position.set(x, 0, z); HOF[k].root.rotation.y = Math.atan2(-x, -z); applyPose(HOF[k], READY); }
  for (const [k, P] of Object.entries(INF)) if (k !== p.who) { const at = { ss: [-28, -118], b2: [30, -126], b3: [-58, -76] }[k]; P.root.position.set(at[0], 0, at[1]); P.root.rotation.y = Math.atan2(-at[0], -at[1]); applyPose(P, READY); }
  const th = throwFor(play);
  setFirstBaseman(p, t);
  const { P: Fp, tf } = setFielder(p, t, th);
  setRunner(p.runner ?? 0.1, t);
  // first-base umpire: watches the bag, makes the call
  const U1at = v3(71, 0, -77); U1.root.position.copy(U1at); U1.root.rotation.y = yawTo(U1at, B1W.clone().add(v3(-6, 0, 2)));
  applyPose(U1, t < 0.25 ? U1_SET : p.call === "out" ? mixPose(U1_SET, U1_OUT, smooth((t - 0.25) / 0.25)) : mixPose(U1_SET, U1_SAFE, smooth((t - 0.3) / 0.25)));
  // the ball
  let bp, trail = null;
  const gloveF = wpos(Fp.handL);
  if (t < tf) { bp = grounderPos(p, tf, gloveF, t); trail = (d) => (t - d > tf - 1.2 ? grounderPos(p, tf, gloveF, t - d) : null); }
  else if (t < th.tr - 0.25) bp = gloveF;
  else if (t < th.tr) bp = wpos(Fp.handR);
  else if (t < 0 || p.fb.late) {
    bp = t < 0 ? throwPos(th, t) : loosePos(th, t);
    trail = (d) => (t - d > th.tr ? (t - d < 0 || !p.fb.late ? throwPos(th, Math.min(t - d, 0)) : loosePos(th, t - d)) : null);
    if (p.fb.late && t >= 0) trail = (d) => loosePos(th, t - d);
  } else bp = wpos(FB.handL);
  placeBall(bp, trail);
  // graphics
  const u = unit(B1W, v3(p.field[0], 0, p.field[1]));
  FOOT = wpos(FB.ftR);
  if (s.show?.foot) { footRing.position.set(FOOT.x, 0.3, FOOT.z); footRing.visible = true; }
  if (s.show?.gain && t > -0.25) {                                    // how much closer the stretch brings the catch: his glove at the catch vs. a reach standing tall
    const keep = FB.root.position.clone(), rot = FB.root.rotation.y;
    applyPose(FB, legsIK(B_REACH)); FB.root.rotation.y = yawTo(B1W, v3(p.field[0], 0, p.field[1])); anchorFoot(FB, BAG_FOOT(u)); const g0 = wpos(FB.handL);
    setFirstBaseman(p, Math.max(t, 0)); const g1 = wpos(FB.handL); setFirstBaseman(p, t);
    const a = g0.clone(), b = g1.clone(), k = smooth((t + 0.25) / 0.3);
    between(gainBar, a, a.clone().lerp(b, k)); gainBar.visible = true;
    gainDots[0].position.copy(a); gainDots[1].position.copy(a.clone().lerp(b, k)); gainDots.forEach((d) => (d.visible = true));
    ghostGlove.position.copy(g0); ghostGlove.visible = true;
    GAIN = { mid: a.clone().lerp(b, 0.5), ft: flat(g0).distanceTo(flat(g1)) };
  }
}
function setBatting(t, s) {
  for (const p of DEF) p.root.visible = false; for (const p of BAT) p.root.visible = true;
  for (const [k, [x, z]] of Object.entries(awayD)) { AD[k].root.position.set(x, 0, z); AD[k].root.rotation.y = Math.atan2(-x, -z); applyPose(AD[k], READY); }
  awayC.root.position.set(0.15, 0, 3.0); awayC.root.rotation.y = Math.PI; applyPose(awayC, C_SET);
  // the pitch: from the stretch, contact at t = 0
  const tr = t + 0.45;
  awayP.root.position.set(0, MOUND_H, lerp(-60.6, -57.6, smooth((tr + 0.45) / 0.5))); awayP.root.rotation.y = lerp(-Math.PI / 2, 0, smooth((tr + 0.6) / 0.6));
  applyPose(awayP, keyed([[-1.3, P_SET], [-0.9, P_LIFT], [-0.35, P_STRIDE], [0, P_REL], [0.35, P_FOLLOW], [1.0, { ...READY, look: 0 }]], tr));
  // left fielder and center fielder drift back and watch it go
  const land = pathAt(HR.path, HR.path.dur);
  for (const k of ["lf", "cf"]) {
    const st = v3(awayD[k][0], 0, awayD[k][1]), tgt = st.clone().lerp(flat(land), 0.35), d = tgt.clone().sub(st), run = Math.min(d.length(), Math.max(0, 24 * (t - 0.5)));
    AD[k].root.position.copy(st).addScaledVector(d.normalize(), run); AD[k].root.rotation.y = Math.atan2(d.x, d.z);
    applyPose(AD[k], t > 0.5 && run < tgt.distanceTo(st) - 0.5 ? runPose((run / 11) % 1, 0.8) : t > 0.5 ? { ...STAND, nod: -30, look: 0 } : READY);
  }
  if (s.play === "hr") {
    FBB.root.position.set(-3.0, 0, -0.9); FBB.root.rotation.y = Math.PI / 2; applyPose(FBB, keyed(swingHR, t)); FBB.bat.visible = true;
  } else {                                                           // the trot: around first base
    const s0 = Math.max(0, (t - 0.3) * 18), a = R0, b1 = B1W, b2 = B2W;
    let p;
    if (s0 < RLEN) p = a.clone().addScaledVector(RDIR, s0).addScaledVector(FOUL, 1.2 * (1 - smooth((s0 - RLEN + 20) / 14)));
    else { const k = s0 - RLEN, d = unit(b1, b2); p = b1.clone().addScaledVector(d, k).addScaledVector(v3(d.z, 0, -d.x), -2.5 * Math.exp(-k / 8)); }
    const ahead = s0 < RLEN ? RDIR : unit(B1W, B2W);
    FBB.root.position.copy(p); FBB.root.rotation.y = Math.atan2(ahead.x, ahead.z); FBB.bat.visible = false;
    applyPose(FBB, { ...runPose((s0 / 9) % 1, 0.35), nod: -4 });
  }
  let bp, trail = null;
  if (t < -0.45) bp = wpos(awayP.handR);
  else if (t < 0) bp = v3(-1.9, 6, -54).lerp(V(HR.contact), (t + 0.45) / 0.45);
  else { bp = pathAt(HR.path, t); trail = (d) => (t - d > 0 ? pathAt(HR.path, t - d) : null); }
  if (s.play === "trot") { bp = v3(0, -50, 0); trail = null; }
  placeBall(bp, trail);
  if (s.show?.hrPath) reveal(HR_TUBE, clamp(t / HR.path.dur, 0, 1));
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
const fieldOf = (s) => { const p = PL[s.play]; return v3(p.field[0], 0, p.field[1]); };
const CAMS = {
  // behind the fielder, low: the play and the throw across
  fielder: (u, t, s) => { const F = fieldOf(s), d = unit(F, B1W), n = v3(d.z, 0, -d.x); return [F.clone().addScaledVector(d, -17 + 2 * u).add(v3(0, 6.5, 0)).addScaledVector(n, 4), F.clone().addScaledVector(d, 9).setY(2.4), 40]; },
  // square to the stretch, foul side: his reach toward the throw, the runner coming
  fbSide: (u, t, s) => { const F = fieldOf(s), d = unit(B1W, F), n = v3(-d.z, 0, d.x); return [B1W.clone().addScaledVector(n, 16 - 1.2 * u).addScaledVector(d, 2.5).add(v3(0, 3.8, 0)), B1W.clone().addScaledVector(d, 1.6).setY(2.0), 40]; },
  // from the infield side, facing him: the glove, the bag
  fbFront: (u, t, s) => { const F = fieldOf(s), d = unit(B1W, F); return [B1W.clone().addScaledVector(d, 17 - u * 1.5).add(v3(0, 3.8, 0)).addScaledVector(v3(-d.z, 0, d.x), 4), B1W.clone().addScaledVector(d, 1.5).setY(1.8), 40]; },
  // low, up the line from home: the stretch toward the plate, the runner behind it
  fbLine: (u) => [mixV(v3(46, 4.5, -70), v3(47, 4.3, -69.2), u), v3(61, 2, -61), 36],                                   // infield grass, home side: the stretch up the line
  fbWide: (u) => [mixV(v3(46, 4.5, -70), v3(47, 4.3, -69.2), u), v3(62, 2, -57), 34],                                   // the same, looking up the line: off the bag
  fbIn: (u) => [mixV(v3(52, 3.2, -76), v3(53, 3.0, -75), u), v3(62, 0.8, -62), 42],                                     // the infield, second-base side, low: the hop into the glove
  // behind the bag, right-field side: the throw coming in, the hop, the glove
  fbBack: (u, t, s) => { const F = fieldOf(s), d = unit(B1W, F), n = v3(-d.z, 0, d.x); return [B1W.clone().addScaledVector(d, -9.5 + u).addScaledVector(n, 2.5).add(v3(0, 8.5, 0)), B1W.clone().addScaledVector(d, 5.5).setY(0.6), 42]; },
  // the replay angle: square to the stretch, a little higher, the line on the dirt
  gain: (u, t, s) => { const y = fbYaw(PL[s.play]), d = v3(Math.sin(y), 0, Math.cos(y)), n = v3(-d.z, 0, d.x); return [B1W.clone().addScaledVector(n, 13).addScaledVector(d, 3.0).add(v3(0, 7 - u * 0.6, 0)), B1W.clone().addScaledVector(d, 3.0).setY(1.6), 42]; },
  bat: (u) => [mixV(v3(4.5, 4.0, -9), v3(4.0, 3.8, -8), u), v3(-2.5, 3.0, 0), 44],                                       // in front of the hitter, first-base side
  batLow: (u) => [mixV(v3(-9, 4, 8), v3(-8.4, 3.8, 7.2), u), v3(-3.0, 3.6, -1.5), 44],                                       // behind him, third-base side: the load, the stride
  track: (u, t) => { const b = pathAt(HR.path, Math.max(t, 0)); return [mixV(v3(6, 22, 30), v3(4, 28, 22), u), v3(-60, 18, -200).lerp(b, 0.55), 48]; },
  wall: (u) => [mixV(v3(-85, 3, -318), v3(-86, 2.6, -322), u), v3(-122, 14, -362), 54],                                     // left-center, in front of the wall: up and over it
  trot: (u, t) => { const p = FBB.root.position.clone(); return [p.clone().add(v3(9, 4.5, 9)), p.clone().add(v3(-3, 2.8, -5)), 40]; },
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
  if ($("spd")) { const sp = s.freeze && v >= s.freeze[0] ? "freeze" : s.speed; $("spd").textContent = SPEEDS[sp] ?? ""; $("spd").style.opacity = sp === "none" ? 0 : 1; $("spd").className = "spd " + (sp === "rt" ? "rt" : "sl"); }
  if ($("gainv") && GAIN) $("gainv").textContent = `+${GAIN.ft.toFixed(1)} ft`;
}
function pin(id, p) {
  const el = $(id); if (!el || !p) return;
  const q = p.clone().project(cam);
  el.style.left = `${((q.x + 1) / 2 * W).toFixed(1)}px`; el.style.top = `${((1 - q.y) / 2 * H).toFixed(1)}px`;
}
function renderAt(v) {
  const { s, t, u } = shotAt(v);
  setScene(t, s);
  const c = CAMS[s.cam](u, t, s);
  frame(cam, c[0], c[1], c[2], W / H);
  renderer.render(scene, cam);
  pin("gainw", GAIN?.mid); pin("footw", FOOT);
  overlays(s, v);
}

let last = -1;
function seek(time) { if (time === last) return; last = time; renderAt(time); }
window.addEventListener("hf-seek", (e) => seek(e.detail.time));
window.__fieldRender = renderAt;
window.__throws = () => Object.fromEntries(Object.keys(PL).map((k) => { const th = throwFor(k); return [k, { tr: +th.tr.toFixed(3), e: th.e ? +th.e.toFixed(2) : null, G: th.Gp.toArray().map((x) => +x.toFixed(2)), R: th.R.toArray().map((x) => +x.toFixed(2)) }]; }));
document.fonts.ready.then(() => seek(window.__hfThreeTime || 0));
seek(window.__hfThreeTime || 0);
