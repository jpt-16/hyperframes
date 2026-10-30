// "Does height matter in baseball?": the field, dugouts, outfield seats, the players, in three.js.
// Everything is a pure function of HyperFrames time (hf-seek), so each frame is exact and repeatable.
// Units are feet. Home plate's back point is the origin, +x points toward first base's side, -z toward center field.
// The pitches and batted balls come from tools/physics.py via window.__PLAY. Players are scaled to illustrative heights.
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
const KIT = {   // Brewers- and Rays-inspired colors (no logos, no names)
  brw: { jersey: 0x13294b, pants: 0xe9e3d2, cap: 0x13294b, accent: 0xffc52f, skin: 0x9c7055 },
  ray: { jersey: 0x8fbce6, pants: 0xf1f4f7, cap: 0x092c5c, accent: 0x092c5c, skin: 0x7a5440 },
  ump: { jersey: 0x15181d, pants: 0x4b515b, cap: 0x0d0f12, accent: 0x0d0f12, skin: 0x8a6048 },
};
const SKINS = [0x9c7055, 0x7a5440, 0xc89a7a, 0x5e3f2e, 0xb08060, 0x8a6048, 0xd2a888, 0x6b4a36, 0xa77b5e];
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
  const belt = new THREE.Mesh(new THREE.CylinderGeometry(0.64, 0.64, 0.14, 20, 1, true), M(kit.accent, 0.5)); belt.scale.set(1.05, 1, 0.78); belt.position.y = 0.3; pelvis.add(belt);
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
const dg3 = makeDugout(-70.7, -7.1, 3 * Math.PI / 4, 0xffc52f), dg1 = makeDugout(70.7, -7.1, -3 * Math.PI / 4, 0x8fbce6);
// World Series bunting: pleated half-fans along both dugout roofs
const buntTex = canvasTex(1024, 128, (g, w, h) => {
  g.clearRect(0, 0, w, h);
  for (let x = 0; x < w; x += 128) {
    for (const [r, c] of [[64, "#c8202f"], [50, "#f4f2ec"], [36, "#13294b"], [24, "#f4f2ec"], [12, "#c8202f"]]) { g.fillStyle = c; g.beginPath(); g.arc(x + 64, 0, r * 1.9, 0, Math.PI); g.fill(); }
    g.fillStyle = "#13294b"; g.fillRect(x, 0, 128, 10);
  }
});
buntTex.wrapS = THREE.RepeatWrapping; buntTex.repeat.set(5, 1);
for (const g of [dg3, dg1]) {
  const b = new THREE.Mesh(new THREE.PlaneGeometry(64, 6.4), new THREE.MeshStandardMaterial({ map: buntTex, transparent: true, roughness: 0.9, side: THREE.DoubleSide, emissive: 0x161616 }));
  b.position.set(0, 5.6, 6.9); g.add(b);
}
const dgAt = (g, x, z, y = 0) => g.localToWorld(v3(x, y, z));
const dgYaw = (g) => g.rotation.y;
const OD = v3(33, 0, 5);
for (const x of [OD.x, -OD.x]) { const m = new THREE.Mesh(new THREE.RingGeometry(2.3, 2.55, 40), chalk); m.rotation.x = -Math.PI / 2; m.position.set(x, 0.05, OD.z); scene.add(m); }


// ------------------------------------------------------------------ the cast: Brewers- and Rays-inspired players at illustrative heights
const pk = (kit, i) => ({ ...kit, skin: SKINS[i % SKINS.length] });
const BRW = Array.from({ length: 9 }, (_, i) => makePlayer(pk(KIT.brw, i), { glove: true }));
const RAY = Array.from({ length: 9 }, (_, i) => makePlayer(pk(KIT.ray, i + 4), { glove: true }));
const pitcher = makePlayer(pk(KIT.brw, 2), { glove: true });
const C = makePlayer(pk(KIT.ray, 1), { glove: true, catcher: true });
const ump = makePlayer(KIT.ump, { catcher: true });
const batter = makePlayer(pk(KIT.ray, 3), { helmet: true, bat: true });
const SS = makePlayer(pk(KIT.brw, 5), { glove: true }), B1F = makePlayer(pk(KIT.brw, 7), { glove: true });
const CFL = makePlayer(pk(KIT.ray, 6), { glove: true });
const ALL = [...BRW, ...RAY, pitcher, C, ump, batter, SS, B1F, CFL];
for (const p of ALL) scene.add(p.root);
const PLATE_C = v3(0, 0, -0.7);
// the rig's height (to the top of the cap) at scale 1, standing tall
applyPose(BRW[0], { lean: 0 }); BRW[0].root.position.set(0, 0, 0);
const H0 = wpos(BRW[0].neck).y + 0.725;
function setH(P, ft, build = 1) { const k = ft / H0; P.root.scale.set(k * build, k, k * build); P.k = k; }
const headTop = (P) => wpos(P.neck).add(v3(0, 1.3 * (P.k ?? 1), 0));
const show = (P, pos, yaw, q, ft, build = 1) => { P.root.visible = true; P.root.position.copy(pos); P.root.rotation.y = yaw; setH(P, ft, build); applyPose(P, q); };

// the lineups along the foul lines (they face the infield). Heights are illustrative, not any real player's.
const LINE3 = v3(-Math.SQRT1_2, 0, -Math.SQRT1_2), LINE1 = v3(Math.SQRT1_2, 0, -Math.SQRT1_2);
const IN3 = v3(Math.SQRT1_2, 0, -Math.SQRT1_2), IN1 = v3(-Math.SQRT1_2, 0, -Math.SQRT1_2);
const HT = {
  intro: [6.45, 5.6, 6.3, 5.72, 6.5, 5.64, 6.12],
  brw: [5.83, 6.17, 5.75, 6.25, 5.92, 5.67, 6.08, 5.79, 6.04],
  ray: [5.86, 5.75, 6.17, 5.92, 5.68, 5.96, 5.79, 5.88, 5.72],    // one figure over the 6 ft line
};
const SHORT_INTRO = [1, 3, 5];
const linePos = (dir, i, d0 = 12, sp = 4.2) => dir.clone().multiplyScalar(d0 + sp * i);
const yawOf = (d) => Math.atan2(d.x, d.z);
const LINE_POSES = [STAND, { ...STAND, shL: [-10, 14, 0], shR: [-10, 14, 0], elL: 40, elR: 40 }, { ...STAND, look: 6, nod: -3 }, { ...STAND, shL: [25, 30, 0], elL: 95, shR: [25, 30, 0], elR: 95 }];
const lp = (i, t) => ({ ...LINE_POSES[i % 4], look: (LINE_POSES[i % 4].look ?? 0) + 4 * Math.sin(t * 0.8 + i), nod: -2 + Math.sin(t * 0.6 + i * 1.7) });

// ------------------------------------------------------------------ the model (tools/physics.py)
const HI = PLAY.pitches.hi, LO = PLAY.pitches.lo, GB = PLAY.gb, LD = PLAY.ld, FL = HI.flight, TC = HI.t_contact;
function pathAt(path, t) {
  const u = (t - path.t0) * path.hz, n = path.p.length - 1;
  if (u <= 0) return V(path.p[0]);
  if (u >= n) return V(path.p[n]);
  const i = Math.floor(u), f = u - i, a = path.p[i], b = path.p[i + 1];
  return v3(lerp(a[0], b[0], f), lerp(a[1], b[1], f), lerp(a[2], b[2], f));
}
const arcAt = (p0, p1, T, u) => p0.clone().lerp(p1, clamp(u / T, 0, 1)).add(v3(0, 16.1 * clamp(u, 0, T) * (T - clamp(u, 0, T)), 0));

// ------------------------------------------------------------------ poses
const C_SET = { ...CROUCH, shL: [62, 18, 0], elL: 40, shR: [20, 10, 0], elR: 50, nod: -18 };
const C_MID = { ...CROUCH, nod: -8, shL: [78, 12, 0], elL: 24, shR: [20, 10, 0], elR: 60 };
const U_SET = { drop: -1.0, lean: 30, nod: -6, hipL: [52, 28], hipR: [52, 28], knL: 68, knR: 68, shL: [30, 20, 0], elL: 60, shR: [30, 20, 0], elR: 60 };
const P_SET = { lean: 4, look: 80, nod: 4, shL: [42, 8, 0], elL: 105, shR: [38, -4, 0], elR: 112, hipL: [4, 6], hipR: [4, 6], knL: 8, knR: 8 };
const P_LIFT = { lean: -4, look: 80, shL: [48, 8, 0], elL: 100, shR: [44, -4, 0], elR: 108, hipL: [100, 4], knL: 105, hipR: [6, 6], knR: 14, drop: -0.15 };
const P_STRIDE = { lean: 6, look: 40, drop: -0.6, twist: -50, shL: [80, 35, 0], elL: 25, shR: [-55, 80, 0], elR: 85, hipL: [52, 4], knL: 28, hipR: [-28, 6], knR: 38 };
const P_REL = { lean: 42, nod: 8, drop: -1.0, twist: 28, shL: [12, 32, 0], elL: 85, shR: [168, 22, 0], elR: 8, hipL: [72, 4], knL: 22, hipR: [-18, 6], knR: 92 };
const P_FOLLOW = { lean: 62, nod: 18, drop: -1.25, twist: 48, shL: [8, 38, 0], elL: 95, shR: [58, -24, 0], elR: 22, hipL: [82, 4], knL: 38, hipR: [34, 6], knR: 84 };
const BAT_SET = { drop: -0.35, lean: 18, look: 80, nod: -4, hipL: [22, 14], hipR: [22, 14], knL: 26, knR: 26, shL: [55, 6, 0], shR: [60, 34, 0], elL: 95, elR: 110, twist: 20 };
const BAT_LOAD = { ...BAT_SET, twist: 34, pelvisTwist: -14, hipL: [44, 10], knL: 52, hipR: [26, 18], knR: 34 };
const BAT_STRIDE = { ...BAT_LOAD, drop: -0.55, hipL: [14, 26], knL: 20, hipR: [30, 18], knR: 38, twist: 30 };
const BAT_HIT = { drop: -0.6, lean: 30, look: 74, nod: -14, twist: -36, pelvisTwist: 50, hipL: [24, 28], knL: 14, hipR: [18, 12], knR: 46, shL: [86, -8, 0], elL: 6, shR: [80, 12, 0], elR: 16 };
const BAT_FIN = { drop: -0.3, lean: 12, look: 20, twist: -70, pelvisTwist: 80, hipL: [16, 26], knL: 8, hipR: [6, 12], knR: 56, shL: [130, 10, 0], elL: 90, shR: [140, -40, 0], elR: 100 };
const F_LOW = { drop: -1.55, lean: 62, nod: -30, hipL: [92, 34], hipR: [92, 34], knL: 104, knR: 104, ankL: -18, ankR: -18, shL: [84, 10, 0], elL: 8, shR: [70, -6, 0], elR: 24 };   // wide base, glove out front, eyes on it
const F_BACK = { ...STAND, drop: -0.3, twist: -30, shR: [-30, 80, 0], elR: 95, shL: [70, 20, 0], elL: 30, hipL: [30, 6], knL: 20 };
const F_REL = { ...STAND, lean: 22, twist: 30, shR: [160, 20, 0], elR: 15, shL: [30, 34, 0], elL: 70, hipL: [34, 4], knL: 24, hipR: [-10, 6], knR: 30 };
const B1_STRETCH = { drop: -1.0, lean: 38, nod: -10, shL: [96, -8, 0], elL: 4, hipL: [70, 8], knL: 60, hipR: [-14, 10], knR: 4, shR: [30, 20, 0], elR: 50 };
const WING = { ...STAND, shL: [172, 10, 0], shR: [172, 10, 0], elL: 2, elR: 2, nod: 6 };       // arms straight up: the reach
const C_STAND = { ...STAND, shL: [30, 14, 0], elL: 60, shR: [10, 10, 0], elR: 20 };

// ------------------------------------------------------------------ graphics: the 6 ft line, rings, pitch tubes, release dots, strike zones, span bars
const glowMat = (c, op = 0.95) => new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: op, depthWrite: false });
const ROPE = new THREE.Mesh(new THREE.BoxGeometry(1, 0.07, 0.07), glowMat(0xffd84d)); ROPE.renderOrder = 8; scene.add(ROPE);
function bar(m, a, b) { const d = b.clone().sub(a), L = d.length(); m.position.copy(a).add(b).multiplyScalar(0.5); m.scale.set(L, 1, 1); m.rotation.set(0, -Math.atan2(d.z, d.x), Math.atan2(d.y, Math.hypot(d.x, d.z))); m.visible = true; }
const ringMat = (c) => new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: 0.9, depthWrite: false, side: THREE.DoubleSide });
const RINGS = Array.from({ length: 6 }, () => { const m = new THREE.Mesh(new THREE.RingGeometry(1.5, 2.0, 36), ringMat(0xffd84d)); m.rotation.x = -Math.PI / 2; m.renderOrder = 7; scene.add(m); return m; });
function ringsOn(list, t) { RINGS.forEach((m, i) => { const P = list[i]; m.visible = !!P; if (P) { const q = wpos(P.pelvis); m.position.set(q.x, 0.12, q.z); m.material.opacity = 0.7 + 0.25 * Math.sin(t * 9); } }); }
const tube = (path, c, r) => {
  const pts = path.p.map(V), g = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), pts.length * 2, r, 8, false);
  const m = new THREE.Mesh(g, glowMat(c, 0.8)); m.renderOrder = 6; m.userData.n = g.index.count; scene.add(m); return m;
};
const TUBE_HI = tube(HI.path, 0xffd84d, 0.07), TUBE_LO = tube(LO.path, 0x56d1ff, 0.07);
const reveal = (m, u) => { m.visible = u > 0; m.geometry.setDrawRange(0, Math.floor(m.userData.n * clamp(u, 0, 1) / 6) * 6); };
const dot = (c) => { const m = new THREE.Mesh(new THREE.SphereGeometry(0.2, 16, 12), glowMat(c, 1)); m.renderOrder = 9; scene.add(m); return m; };
const DOT_HI = dot(0xffd84d), DOT_LO = dot(0x56d1ff);
DOT_HI.position.copy(V(HI.release)); DOT_LO.position.copy(V(LO.release));
const RELBAR = new THREE.Mesh(new THREE.BoxGeometry(1, 0.05, 0.05), glowMat(0xffffff, 0.8)); scene.add(RELBAR);
function zoneFrame(c, dashed) {
  const g = new THREE.Group(), m = glowMat(c, 0.95), segs = [];
  const n = dashed ? 9 : 1;
  for (let e = 0; e < 4; e++) for (let i = 0; i < n; i++) { const b = new THREE.Mesh(new THREE.BoxGeometry(1, 0.045, 0.045), m); b.renderOrder = 9; b.userData = { e, i, n }; g.add(b); segs.push(b); }
  const fill = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), glowMat(c, dashed ? 0.0 : 0.16)); fill.renderOrder = 8; g.add(fill);
  g.visible = false; scene.add(g);
  g.userData.set = (x0, x1, y0, y1, z) => {
    const C4 = [v3(x0, y0, z), v3(x1, y0, z), v3(x1, y1, z), v3(x0, y1, z)];
    for (const b of segs) { const { e, i, n } = b.userData, a = C4[e], c2 = C4[(e + 1) % 4]; const f0 = n > 1 ? i / n : 0, f1 = n > 1 ? (i + 0.55) / n : 1; bar(b, a.clone().lerp(c2, f0), a.clone().lerp(c2, f1)); }
    fill.position.set((x0 + x1) / 2, (y0 + y1) / 2, z); fill.scale.set(x1 - x0, y1 - y0, 1);
  };
  return g;
}
const ZONE_S = zoneFrame(0xffd84d, false), ZONE_T = zoneFrame(0xf4f6f8, true);
const SPAN_T = new THREE.Mesh(new THREE.BoxGeometry(1, 0.16, 0.16), glowMat(0xffd84d)), SPAN_S = new THREE.Mesh(new THREE.BoxGeometry(1, 0.16, 0.16), glowMat(0x56d1ff));
SPAN_T.renderOrder = SPAN_S.renderOrder = 9; scene.add(SPAN_T, SPAN_S);

// the strike zone of a hitter in his stance: from the midpoint between the tops of the shoulders and the top of the
// pants down to the hollow beneath the kneecap (the rulebook definition), measured on the posed figure
const BAT_POS = v3(-3.0, 0, -0.9);
function zoneOf(P) {
  const k = P.k, sh = (wpos(P.shL).y + wpos(P.shR).y) / 2 + 0.18 * k, belt = wpos(P.pelvis).y + 0.37 * k, knee = (wpos(P.knL).y + wpos(P.knR).y) / 2 - 0.12 * k;
  return [knee, (sh + belt) / 2];
}
const H_SHORT = 5.6, H_TALL = 6.55;
const ZN = {};
for (const [key, ft] of [["s", H_SHORT], ["t", H_TALL]]) { show(batter, BAT_POS, Math.PI / 2, BAT_SET, ft); ZN[key] = zoneOf(batter); }


// the tall pitcher, sized and placed so his hand is at the high release point when he lets it go
const H_PITCH = 6.6, P_STRIDE_Z = -57.6;
const PREL = { pos: v3(0, MOUND_H * 0.6, P_STRIDE_Z), k: H_PITCH };
{
  show(pitcher, PREL.pos, 0, P_REL, H_PITCH);
  const h = wpos(pitcher.handR), rel = V(HI.release);
  PREL.pos = PREL.pos.clone().add(v3(rel.x - h.x, 0, rel.z - h.z)); PREL.k = H_PITCH * (rel.y - PREL.pos.y) / (h.y - PREL.pos.y);
  show(pitcher, PREL.pos, 0, P_REL, PREL.k);
}

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
  const vis = !!pos; BALL.m.visible = BALL.glow.visible = vis;
  if (vis) { BALL.m.position.copy(pos); BALL.glow.position.copy(pos); }
  for (let i = 0; i < BALL.trail.length; i++) { const p = vis && trailFn ? trailFn((i + 1) * 0.012) : null, tr = BALL.trail[i]; tr.visible = !!p; if (p) tr.position.copy(p); }
}

// ------------------------------------------------------------------ the scenes
// s.sc picks the scene; t is that scene's own clock
const SS0 = v3(-27, 0, -114), SSP = V(GB.field).setY(0), T_SSF = TC + GB.t_field, T_SSREL = T_SSF + 0.62, T_SST = 0.95, T_SSC = T_SSREL + T_SST;
const B1S = v3(62.6, 0, -64.6), H_SS = 5.6, H_1B = 6.5;
const BPOS = (i) => v3(6 - 4.2 * i, 0, -18 - 5 * i);            // a diagonal row on the infield grass
const BUILD = [   // [player, height ft, build (width), position]
  [C, 5.95, 1.16, "C"], [B1F, 6.5, 1.0, "1B"], [SS, 5.6, 0.96, "SS"], [CFL, 6.08, 0.88, "CF"], [pitcher, 6.6, 0.94, "P"],
];
function pitcherAt(t) {      // the delivery: release at t = -FL (the ball reaches the plate at t = 0)
  const tr = t + FL, zp = lerp(-60.6, PREL.pos.z, smooth((tr + 0.45) / 0.5));
  const x = lerp(0, PREL.pos.x, smooth((tr + 0.45) / 0.5));
  show(pitcher, v3(x, MOUND_H * (zp > -59 ? 0.6 : 1), zp), lerp(-Math.PI / 2, 0, smooth((tr + 0.6) / 0.6)),
    keyed([[-1.3, P_SET], [-0.9, P_LIFT], [-0.35, P_STRIDE], [0, P_REL], [0.35, P_FOLLOW], [1.0, { ...READY, look: 0 }]], tr), PREL.k);
}
function battery(t, contact) {
  show(C, v3(0.15, 0, 3.0), Math.PI, contact ? keyed([[-0.6, C_SET], [-0.05, C_MID], [0.3, C_MID], [0.9, { ...STAND, look: 30 }]], t) : keyed([[-0.6, C_SET], [-0.05, C_MID], [0.6, C_MID]], t), 5.95, 1.1);
  show(ump, v3(0.5, 0, 6.0), Math.PI, U_SET, 6.0);
}
function setScene(t, s) {
  for (const p of ALL) p.root.visible = false;
  for (const g of [ROPE, DOT_HI, DOT_LO, RELBAR, ZONE_S, ZONE_T, SPAN_T, SPAN_S, TUBE_HI, TUBE_LO]) g.visible = false;
  ringsOn([], t);
  let bp = null, trail = null;
  const sc = s.sc;
  if (sc === "lines") {             // the teams on the foul lines: Brewers-inspired on the third-base side, Rays-inspired on the first-base side
    const intro = s.set === "intro";
    BRW.forEach((P, i) => { if (intro && i >= HT.intro.length) return; show(P, linePos(LINE3, i).add(IN3.clone().multiplyScalar(0.0)), yawOf(IN3), lp(i, t), intro ? HT.intro[i] : HT.brw[i]); });
    if (!intro) RAY.forEach((P, i) => show(P, linePos(LINE1, i), yawOf(IN1), lp(i + 3, t), HT.ray[i]));
    if (s.rope) { const d = s.rope === "1b" ? LINE1 : LINE3, n = s.rope === "1b" ? IN1 : IN3; bar(ROPE, d.clone().multiplyScalar(7).addScaledVector(n, 0.8).setY(6), d.clone().multiplyScalar(intro ? 42 : 50).addScaledVector(n, 0.8).setY(6)); }
    if (s.hl === "short" && t > s.hlt) ringsOn(SHORT_INTRO.map((i) => BRW[i]), t);
    if (s.hl === "tall" && t > s.hlt) ringsOn([RAY[2]], t);
  } else if (sc === "pair") {       // a taller and a shorter player, arms out: the span
    const u = smooth((t - 0.15) / 0.5);
    show(BRW[3], v3(-2.3, 0, -24), 0, mixPose(STAND, WING, u), 6.55);
    show(RAY[4], v3(2.3, 0, -24), 0, mixPose(STAND, WING, u), 5.6);
    if (u > 0.98 && s.span != null && t > s.span) {          // shoulder to fingertips, each arm
      const f = v3(0, 0, 0.7), tip = (P) => wpos(P.handL).add(v3(0, 0.15 * P.k, 0));
      bar(SPAN_T, wpos(BRW[3].shL).add(f), tip(BRW[3]).add(f)); bar(SPAN_S, wpos(RAY[4].shL).add(f), tip(RAY[4]).add(f));
      const g = smooth((t - s.span) / 0.3); SPAN_T.scale.x *= g; SPAN_S.scale.x *= g;
    }
  } else if (sc === "pitch") {      // the release-point demo
    pitcherAt(t); battery(t, false);
    const tRel = -FL;
    if (s.tubes) { const u = clamp((t - tRel) / FL, 0, 1); reveal(TUBE_HI, u); reveal(TUBE_LO, s.tubes === 2 ? u : 0); DOT_HI.visible = t > tRel; DOT_LO.visible = s.tubes === 2 && t > tRel; if (s.tubes === 2 && t > tRel) bar(RELBAR, V(HI.release).add(v3(-0.6, 0, 0)), V(LO.release).add(v3(-0.6, 0, 0))); }
    if (t < tRel - 0.02) bp = wpos(pitcher.handR);
    else if (t < 0) { bp = pathAt(HI.path, t); trail = (d) => (t - d > HI.path.t0 ? pathAt(HI.path, t - d) : null); }
    else bp = wpos(C.handL);
  } else if (sc === "bat") {        // the shorter hitter: his strike zone (s.zone), or a line drive (s.hit)
    const hit = !!s.hit;
    if (hit) pitcherAt(t); else show(pitcher, v3(0, MOUND_H, -60.6), 0, P_SET, PREL.k);
    battery(t, hit); if (s.zone != null) ump.root.visible = C.root.visible = false;
    let q = BAT_SET;
    if (hit) q = keyed([[TC - 0.8, BAT_SET], [TC - 0.5, BAT_LOAD], [TC - 0.22, BAT_STRIDE], [TC, BAT_HIT], [TC + 0.3, BAT_FIN], [TC + 0.9, { ...BAT_FIN, lean: 6, drop: -0.1 }]], t);
    else q = { ...BAT_SET, look: 80 + 3 * Math.sin(t * 1.3), nod: -4 + Math.sin(t) };
    show(batter, BAT_POS, Math.PI / 2, q, H_SHORT); batter.bat.visible = true;
    if (s.zone) {
      const x0 = -PLAY.zone.half_w, x1 = PLAY.zone.half_w, z = -0.71, u = smooth((t - s.zone) / 0.35), [b, tp] = ZN.s;
      ZONE_S.visible = u > 0; ZONE_S.userData.set(x0, x1, b, lerp(b + 0.02, tp, u), z);
      if (s.ghost != null && t > s.ghost) { ZONE_T.visible = true; ZONE_T.userData.set(x0 - 0.02, x1 + 0.02, ZN.t[0], ZN.t[1], z + 0.02); }
    }
    if (hit) {
      if (t < -FL - 0.02) bp = wpos(pitcher.handR);
      else if (t < TC) { bp = pathAt(HI.path, t); trail = (d) => (t - d > HI.path.t0 ? pathAt(HI.path, t - d) : null); }
      else { bp = pathAt(LD.path, t - TC); trail = (d) => (t - d >= TC ? pathAt(LD.path, t - d - TC) : pathAt(HI.path, t - d)); }
    }
  } else if (sc === "field") {      // the shorter shortstop gets low on a ground ball and throws to a taller first baseman
    const tf = T_SSF, u = clamp((t - TC - 0.2) / (tf - TC - 0.45), 0, 1);
    const toHome = PLATE_C.clone().sub(SSP).setY(0).normalize(), end = SSP.clone().addScaledVector(toHome, -1.2);
    const p = SS0.clone().lerp(end, smooth(u)), yaw = t < tf + 0.3 ? yawOf(toHome) : yawTo(p, B1S);
    const q = t < tf - 0.45 ? (t < TC + 0.2 ? { ...READY, look: 0 } : runPose(((t - TC) * 1.8) % 1, 0.7)) : keyed([[tf - 0.45, { ...READY, drop: -0.9, lean: 40 }], [tf - 0.12, F_LOW], [tf + 0.22, F_LOW], [tf + 0.5, F_BACK], [T_SSREL, F_REL], [T_SSREL + 0.5, STAND]], t);
    show(SS, p, yaw, q, H_SS);
    show(B1F, v3(56, 0, -72).lerp(B1S, smooth((t - TC - 0.2) / 0.9)), yawTo(B1S, SSP), t > T_SSREL - 0.15 ? keyed([[T_SSREL - 0.15, READY], [T_SSC - 0.1, B1_STRETCH]], t) : READY, H_1B);
    show(BRW[6], v3(-58, 0, -78), yawTo(v3(-58, 0, -78), PLATE_C), READY, 6.0);
    show(RAY[7], v3(24, 0, -117), yawTo(v3(24, 0, -117), PLATE_C), READY, 5.85);
    if (t < TC) bp = null;
    else if (t < tf) { bp = pathAt(GB.path, t - TC); trail = (d) => (t - d >= TC ? pathAt(GB.path, t - d - TC) : null); }
    else if (t < T_SSREL - 0.3) bp = wpos(SS.handL);
    else if (t < T_SSREL) bp = wpos(SS.handR);
    else if (t < T_SSC) { const a = v3(SSP.x, 5.6, SSP.z); bp = arcAt(a, wpos(B1F.handL), T_SST, t - T_SSREL); trail = (d) => (t - d > T_SSREL ? arcAt(a, wpos(B1F.handL), T_SST, t - d - T_SSREL) : null); }
    else bp = wpos(B1F.handL);
  } else if (sc === "builds") {     // different builds, different jobs
    BUILD.forEach(([P, ft, b], i) => { const p = BPOS(i); show(P, p, yawTo(p, v3(12, 0, -6)), i === 0 ? C_STAND : lp(i, t), ft, b); });
  }
  placeBall(bp, trail);
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
  hookLine: (u) => [mixV(v3(8, 6, -4), v3(9.2, 6, -3.0), easeIO(u)), v3(-28, 6, -21), 40],          // eye level at 6 ft, down the third-base line
  wsWide: (u) => [mixV(v3(0, 12, -72), v3(0, 10, -64), easeIO(u)), v3(0, 2.5, -14), 56],
  raysLine: (u) => [mixV(v3(-8, 6, -4), v3(-9.2, 6, -3.0), easeIO(u)), v3(28, 6, -21), 40],          // eye level at 6 ft, down the first-base line
  qHigh: (u) => [mixV(v3(0, 58, 30), v3(0, 70, 42), easeIO(u)), v3(0, 0, -24), 44],
  pair: (u) => [mixV(v3(0, 4.4, -1), v3(0, 4.4, -4), easeIO(u)), v3(0, 4.8, -24), 40],
  pitchSide: (u) => [mixV(v3(4.2, 5.2, 10), v3(3.6, 5.2, 8), u), v3(-1, 4.8, -40), 26],                  // beside the plate, looking out at the mound
  pitcherCU: (u) => [mixV(v3(12, 6, -40), v3(11, 6, -42), u), v3(-1, 5, -56), 34],
  batHero: (u) => [mixV(v3(2.5, 1.4, -12), v3(2.2, 1.5, -11), easeIO(u)), v3(-3, 3.3, -0.9), 34],
  catcherV: (u) => [mixV(v3(2.0, 5.0, 13.5), v3(1.9, 5.0, 12.5), easeIO(u)), v3(-0.9, 2.8, -1), 30],
  batSide: (u) => [mixV(v3(5.5, 4.2, -11), v3(4.8, 4.0, -9.5), u), v3(-2.2, 3.2, -0.6), 40],
  ssLow2: (u) => [mixV(v3(-16, 2.2, -90), v3(-17, 2.2, -91), u), v3(-26, 1.6, -100), 40],
  ssLow: (u) => [mixV(v3(-37, 2.2, -105), v3(-36, 2.0, -104), u), v3(-25, 1.4, -99), 40],
  b1Low: (u) => [mixV(v3(46, 2.6, -58), v3(47, 2.6, -59), u), v3(62, 3, -65.5), 44],
  buildsA: (u) => [mixV(v3(23, 5, -8), v3(21.5, 5, -9.5), easeIO(u)), v3(-6, 3.4, -30), 36],
  buildsD: (u) => [mixV(v3(24, 9, -4), v3(22, 8, -6), easeIO(u)), v3(-5, 3, -31), 40],
  buildsB: (u) => [mixV(v3(-2, 22, -4), v3(0, 19, -6), easeIO(u)), v3(-4, 2, -28), 46],
  buildsC: (u) => [mixV(v3(4, 3.5, -5), v3(3, 3.5, -6.5), easeIO(u)), v3(-4, 4, -30), 38],
  endWide: (u) => [mixV(v3(0, 12, -66), v3(0, 12, -60), easeIO(u)), v3(0, 13, -8), 54],
};

function shotAt(v) {
  const L = CC.shots.list;
  const s = L.find((x) => v < x.b) || L.at(-1);
  return { s, t: pw(v, s.vs, s.ts), u: clamp((v - s.a) / (s.b - s.a), 0, 1) };
}

// ------------------------------------------------------------------ DOM overlays fed from the same clock
const $ = (id) => document.getElementById(id);
const SPEEDS = { rt: "", replay: "Replay · slow motion", slow: "Slow motion · ½ speed", freeze: "Freeze", none: "" };
const PINT = {
  rope: () => ROPE.position.clone().add(v3(0, 0.6, 0)), rope1: () => LINE1.clone().multiplyScalar(44).addScaledVector(IN1, 0.8).setY(6.3),
  rayTall: () => headTop(RAY[2]), hiRel: () => V(HI.release).add(v3(0, 0.5, 0)), loRel: () => V(LO.release).add(v3(0, -1.2, 0)),
  zoneS: () => v3(0, ZN.s[1] - 0.55, -0.7), zoneT: () => v3(0, ZN.t[1] + 0.06, -0.7),
  bwLine: () => headTop(BRW[2]), rsLine: () => headTop(RAY[2]), batter: () => headTop(batter),
  tallP: () => headTop(BRW[3]), shortP: () => headTop(RAY[4]), ss: () => headTop(SS), b1: () => headTop(B1F),
  bC: () => headTop(C), b1B: () => headTop(B1F), bSS: () => headTop(SS), bCF: () => headTop(CFL), bP: () => headTop(pitcher),
};
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
  setScene(t, s);
  const c = CAMS[s.cam](u, t, s);
  renderer.setViewport(0, 0, W, H);
  frame(cam, c[0], c[1], c[2], W / H);
  const g = c[2] < 16 ? 0.009 : 0.02; BALL.glow.scale.set(g, g, 1);
  renderer.render(scene, cam);
  overlays(s, v);
}

let last = -1;
function seek(time) { if (time === last) return; last = time; renderAt(time); }
window.addEventListener("hf-seek", (e) => seek(e.detail.time));
window.__fieldRender = renderAt;
document.fonts.ready.then(() => seek(window.__hfThreeTime || 0));
seek(window.__hfThreeTime || 0);
