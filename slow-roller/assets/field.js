// "The count" in three.js. One pitcher, batter, catcher and umpire; the count on the board and on screen. The story
// is one clock (shot and event times from build.py), so each frame is exact and repeatable. Units are feet. Home plate's back
// point is the origin, +x points toward first base's side, -z toward center field. Pitches and batted balls come from tools/physics.py.
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
  new THREE.MeshStandardMaterial({ map: dirtTex, bumpMap: dirtDetail, bumpScale: 0.25, roughness: 1, transparent: true, depthWrite: false }));
dirt.rotation.x = -Math.PI / 2; dirt.position.set(D0.x + D0.size / 2, 0.03, D0.z + D0.size / 2); dirt.receiveShadow = true;
scene.add(dirt);

// mound: a low dome of the same dirt
const moundGeo = new THREE.LatheGeometry([v3(0, MOUND_H, 0), v3(2.5, MOUND_H, 0), v3(5.5, 0.45, 0), v3(9, 0.0, 0)].map((p) => new THREE.Vector2(p.x, p.y)), 48);
const dirtMat = new THREE.MeshStandardMaterial({ color: 0xa6683f, roughness: 1, bumpMap: dirtDetail, bumpScale: 0.2 });
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
  home: { jersey: 0xe6e0d0, pants: 0xd9d3c3, cap: 0x1f4a35, accent: 0x1f4a35, skin: 0x9c7055 },     // the defense: cream and green
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
  const legR = M(kit.pants), hipM = M(kit.pants), foreM = M(kit.skin, 0.6);
  const root = new THREE.Group();
  const pelvis = new THREE.Group(); pelvis.position.y = 3.1; root.add(pelvis);
  const hipsMesh = new THREE.Mesh(new THREE.SphereGeometry(0.62, 16, 12), hipM); hipsMesh.scale.set(1.05, 0.62, 0.78); hipsMesh.castShadow = true; pelvis.add(hipsMesh);
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
    const fa = seg(0.92, 0.155, foreM); el.add(fa);
    const hand = new THREE.Group(); hand.position.y = -0.92; fa.add(hand);
    const isGlove = glove && s === 1;
    const hm = new THREE.Mesh(new THREE.SphereGeometry(isGlove ? 0.34 : 0.15, 14, 10), isGlove ? M(0x6b3d1f, 0.55) : skin);
    if (isGlove) hm.scale.set(1, 1.15, 0.6); hm.castShadow = true; hand.add(hm);
    const hp = new THREE.Group(); hp.position.set(s * 0.34, 0, 0); pelvis.add(hp);
    const th = seg(1.42, 0.27, s < 0 ? legR : pants); hp.add(th);
    const kn = new THREE.Group(); kn.position.y = -1.42; th.add(kn);
    const sn = seg(1.43, 0.2, s < 0 ? legR : pants); kn.add(sn);
    if (catcher) { const guard = new THREE.Mesh(new THREE.BoxGeometry(0.42, 1.25, 0.2), M(0x1c2b4b, 0.6)); guard.position.set(0, -0.7, 0.18); kn.add(guard); }
    const ft = new THREE.Group(); ft.position.y = -1.43; sn.add(ft);
    const foot = new THREE.Mesh(roundBox(0.38, 0.26, 0.98, 0.1, 6), shoe); foot.position.set(0, -0.06, 0.3); foot.castShadow = true; ft.add(foot);
    const k = s < 0 ? "R" : "L";
    Object.assign(limbs, { [`sh${k}`]: sh, [`el${k}`]: el, [`hand${k}`]: hand, [`hip${k}`]: hp, [`kn${k}`]: kn, [`ft${k}`]: ft });
  }
  if (bat) {
    const b = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.045, 2.8, 10), M(0xb8834e, 0.5)); b.position.y = 1.3; b.castShadow = true;
    const holder = new THREE.Group(); holder.add(b); limbs.handR.add(holder); limbs.bat = holder;
  }
  return { root, pelvis, spine, neck, ...limbs, mats: { jersey, pants, cap, skin, legR, hipM, foreM } };
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


const N_PARK = scene.children.length;                               // everything before the cast is the ballpark (hidden in the lab)
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
R.root.visible = false; U2.root.visible = false;

// ------------------------------------------------------------------ the pitches
const PI_ = PLAY.pitches, REL0 = V(PLAY.release);
function pathAt(path, t) {
  const u = (t - path.t0) * path.hz, n = path.p.length - 1;
  if (u <= 0) return V(path.p[0]);
  if (u >= n) return V(path.p[n]);
  const i = Math.floor(u), f = u - i, a = path.p[i], b = path.p[i + 1];
  return v3(lerp(a[0], b[0], f), lerp(a[1], b[1], f), lerp(a[2], b[2], f));
}
const moundY = (x, z) => { const r = Math.hypot(x - MOUND.x, z - MOUND.z); return r < 2.5 ? MOUND_H : r < 5.5 ? lerp(MOUND_H, 0.45, (r - 2.5) / 3) : r < 9 ? lerp(0.45, 0, (r - 5.5) / 3.5) : 0; };

// ------------------------------------------------------------------ close-up kit: reflections, the out-of-focus backdrop, close-up lights
const pmrem = new THREE.PMREMGenerator(renderer);
const ENV = (() => {
  const s = new THREE.Scene(); s.background = new THREE.Color(0x0e1522);
  const bm = new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide });
  for (let i = 0; i < 7; i++) { const a = i / 7 * Math.PI * 2 + 0.3; const m = new THREE.Mesh(new THREE.PlaneGeometry(5, 1.6), bm); m.position.set(Math.cos(a) * 14, 8 + (i % 2) * 2, Math.sin(a) * 14); m.lookAt(0, 0, 0); s.add(m); }
  const g = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.MeshBasicMaterial({ color: 0x5a4030, side: THREE.DoubleSide })); g.rotation.x = -Math.PI / 2; g.position.y = -4; s.add(g);
  const tp = new THREE.Mesh(new THREE.PlaneGeometry(14, 14), new THREE.MeshBasicMaterial({ color: 0x6f7f98, side: THREE.DoubleSide })); tp.rotation.x = Math.PI / 2; tp.position.y = 14; s.add(tp);
  return pmrem.fromScene(s, 0.04).texture;
})();
// the stadium out of focus: light banks and seat lights as soft discs over the dark bowl, the field below
const bokehTex = canvasTex(720, 1280, (g, w, h) => {
  const gr = g.createLinearGradient(0, 0, 0, h);
  gr.addColorStop(0, "#04070d"); gr.addColorStop(0.36, "#0d1626"); gr.addColorStop(0.5, "#1b2738"); gr.addColorStop(0.58, "#1f3a22"); gr.addColorStop(0.8, "#2b4a26"); gr.addColorStop(1, "#3b2a1c");
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  const disc = (x, y, r, col, a) => { const q = g.createRadialGradient(x, y, 0, x, y, r); q.addColorStop(0, `rgba(${col},${a})`); q.addColorStop(0.72, `rgba(${col},${a * 0.85})`); q.addColorStop(1, `rgba(${col},0)`); g.fillStyle = q; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); };
  for (let k = 0; k < 140; k++) { const y = h * (0.3 + rnd() * 0.22); disc(rnd() * w, y, 6 + rnd() * 16, rnd() < 0.7 ? "255,236,205" : "190,210,255", 0.1 + rnd() * 0.25); }
  for (let k = 0; k < 9; k++) disc(rnd() * w, h * (0.05 + rnd() * 0.14), 40 + rnd() * 50, "255,246,226", 0.35 + rnd() * 0.3);
  g.globalCompositeOperation = "lighter";
  const glow = g.createRadialGradient(w * 0.5, h * 0.12, 0, w * 0.5, h * 0.12, w * 0.9); glow.addColorStop(0, "rgba(120,140,170,.25)"); glow.addColorStop(1, "rgba(0,0,0,0)"); g.fillStyle = glow; g.fillRect(0, 0, w, h);
});
const cam = new THREE.PerspectiveCamera(40, W / H, 0.01, 3000);
scene.add(cam);
const BOKEH = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: bokehTex, fog: false }));
BOKEH.visible = false; cam.add(BOKEH);
function setBokeh(dist) {
  BOKEH.visible = dist > 0; if (!BOKEH.visible) return;
  const hh = 2 * dist * Math.tan(cam.fov * D2R / 2); BOKEH.scale.set(hh * cam.aspect * 1.05, hh * 1.05, 1); BOKEH.position.set(0, 0, -dist);
}
const MKEY = new THREE.DirectionalLight(0xfff0dc, 0), MRIM = new THREE.DirectionalLight(0xb8d4ff, 0), MFILL = new THREE.DirectionalLight(0xffe6d0, 0);
scene.add(MKEY, MKEY.target, MRIM, MRIM.target, MFILL, MFILL.target);
function closeLights(on, target) {                                // a soft key from above the camera and a cool rim from behind the subject
  MKEY.intensity = on ? 1.6 : 0; MRIM.intensity = on ? 1.4 : 0; MFILL.intensity = on ? 0.8 : 0; if (!on) return;
  const c = cam.position, d = target.clone().sub(c).normalize(), up = v3(0, 1, 0), side = d.clone().cross(up).normalize();
  MKEY.position.copy(c).addScaledVector(up, 3).addScaledVector(side, -2); MKEY.target.position.copy(target);
  MRIM.position.copy(target).addScaledVector(d, 4).addScaledVector(up, 2.5).addScaledVector(side, 1.5); MRIM.target.position.copy(target);
  MFILL.position.copy(c).addScaledVector(side, 1.5); MFILL.target.position.copy(target);
}

// ------------------------------------------------------------------ geometry helpers
function roundBox(w, h, d, r, seg = 8) {                          // a box with rounded edges (a pillow, a palm)
  const g = new THREE.BoxGeometry(w, h, d, seg, seg, seg), p = g.attributes.position, a = v3(), c = v3(), ix = w / 2 - r, iy = h / 2 - r, iz = d / 2 - r;
  for (let i = 0; i < p.count; i++) {
    a.fromBufferAttribute(p, i); c.set(clamp(a.x, -ix, ix), clamp(a.y, -iy, iy), clamp(a.z, -iz, iz));
    const n = a.clone().sub(c); if (n.lengthSq() < 1e-12) n.set(0, 0, 1); a.copy(c).addScaledVector(n.normalize(), r); p.setXYZ(i, a.x, a.y, a.z);
  }
  g.computeVertexNormals(); return g;
}
const speckTex = canvasTex(256, 256, (g, w) => { g.fillStyle = "#000"; g.fillRect(0, 0, w, w); for (let k = 0; k < 9000; k++) { const v = 120 + rnd() * 135; g.fillStyle = `rgb(${v},${v},${v})`; g.fillRect(rnd() * w, rnd() * w, 1 + rnd() * 1.5, 1 + rnd() * 1.5); } }, { srgb: false, repeat: [2, 2] });
const dotTex = canvasTex(64, 64, (g, w) => { const q = g.createRadialGradient(w / 2, w / 2, 0, w / 2, w / 2, w / 2); q.addColorStop(0, "rgba(255,255,255,1)"); q.addColorStop(0.45, "rgba(255,255,255,.7)"); q.addColorStop(1, "rgba(255,255,255,0)"); g.fillStyle = q; g.fillRect(0, 0, w, w); });

// ------------------------------------------------------------------ the hand: palm, four fingers and a thumb, each finger three jointed bones
// rig frame: the wrist at the origin; +y toward the fingertips, +z out of the palm, the thumb on the +x side (a right hand)
const SKIN = KIT.home.skin, SLEEVE = 0x1c2b4b;
const skinM = new THREE.MeshPhysicalMaterial({ color: SKIN, roughness: 0.52, sheen: 0.5, sheenColor: 0xffc6a8, sheenRoughness: 0.5, envMap: ENV, envMapIntensity: 0.35, emissive: 0x160904 });
const tipM = skinM.clone();                                        // fingertips: can turn wet (clearcoat) with sweat
const nailM = new THREE.MeshPhysicalMaterial({ color: 0xd8a896, roughness: 0.25, clearcoat: 0.6, envMap: ENV, envMapIntensity: 0.6 });
const dustM = new THREE.MeshStandardMaterial({ color: 0xf6f3ec, roughness: 1, transparent: true, opacity: 0, alphaMap: speckTex, depthWrite: false });
const gooM = new THREE.MeshPhysicalMaterial({ color: 0xf1e7d4, roughness: 0.12, clearcoat: 1, clearcoatRoughness: 0.05, envMap: ENV, envMapIntensity: 1.6, transparent: true, opacity: 0 });
const dropM = new THREE.MeshPhysicalMaterial({ color: 0xcfe6ff, roughness: 0.02, metalness: 0, clearcoat: 1, envMap: ENV, envMapIntensity: 3.0, transparent: true, opacity: 0.45 });
const FINGERS = {
  I: { x: 0.093, y: 0.312, len: [0.135, 0.08, 0.066], r: 0.031, sp: -4 },
  M: { x: 0.031, y: 0.322, len: [0.145, 0.09, 0.07], r: 0.032, sp: 0 },
  R: { x: -0.031, y: 0.314, len: [0.135, 0.085, 0.066], r: 0.030, sp: 4 },
  P: { x: -0.09, y: 0.292, len: [0.105, 0.064, 0.056], r: 0.026, sp: 10 },
  T: { x: 0.112, y: 0.07, len: [0.115, 0.092, 0.074], r: 0.039, sp: 0 },
};
function makeHand() {
  const root = new THREE.Group(), wrist = new THREE.Group(); root.add(wrist);
  const pg = roundBox(0.27, 0.32, 0.092, 0.042, 10), pp = pg.attributes.position;
  for (let i = 0; i < pp.count; i++) { const y = pp.getY(i) + 0.16, k = lerp(0.8, 1, smooth(y / 0.26)); pp.setX(i, pp.getX(i) * k); if (pp.getZ(i) < 0) pp.setZ(i, pp.getZ(i) * (1 + 0.25 * Math.sin(Math.PI * clamp(y / 0.32, 0, 1)))); }
  pg.computeVertexNormals();
  const palm = new THREE.Mesh(pg, skinM); palm.position.y = 0.16; wrist.add(palm);
  const pad = (x, y, z, sx, sy, sz) => { const m = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 14), skinM); m.position.set(x, y, z); m.scale.set(sx, sy, sz); wrist.add(m); return m; };
  pad(0.07, 0.085, 0.03, 0.075, 0.11, 0.045); pad(-0.075, 0.1, 0.025, 0.05, 0.11, 0.035); pad(0, 0.29, 0.03, 0.12, 0.035, 0.03);   // thenar, hypothenar, the pads under the knuckles
  const fore = new THREE.Mesh(new THREE.CapsuleGeometry(0.098, 0.9, 6, 16), skinM); fore.scale.set(1.18, 1, 0.86); fore.position.y = -0.47; root.add(fore);
  const cuff = new THREE.Mesh(new THREE.CylinderGeometry(0.128, 0.14, 0.62, 24, 1, true), new THREE.MeshStandardMaterial({ color: SLEEVE, roughness: 0.85, side: THREE.DoubleSide })); cuff.scale.set(1.12, 1, 0.92); cuff.position.y = -0.62; root.add(cuff);
  const F = {}, shells = { dust: [], goo: [], hl: {} }, drops = [];
  for (const [k, f] of Object.entries(FINGERS)) {
    const base = new THREE.Group(); base.position.set(f.x, f.y, k === "T" ? 0.03 : 0); wrist.add(base);
    const j = []; let parent = base;
    for (let n = 0; n < 3; n++) {
      const g = new THREE.Group(); if (n > 0) g.position.y = f.len[n - 1]; parent.add(g);
      const r = f.r * (1 - 0.06 * n), L = f.len[n];
      const m = new THREE.Mesh(new THREE.CapsuleGeometry(r, n === 2 ? L - r : L, 10, 20), n === 2 ? tipM : skinM); m.position.y = n === 2 ? (L - r) / 2 : L / 2; m.scale.set(1, 1, 0.9); g.add(m);
      if (n >= 1 && k !== "P") {
        const sd = new THREE.Mesh(new THREE.CapsuleGeometry(r * 1.07, Math.max(0.005, L - r * 0.6), 6, 14), dustM); sd.position.y = L / 2; g.add(sd); shells.dust.push(sd);
        if (n === 2 && "IMT".includes(k)) { const sg = new THREE.Mesh(new THREE.CapsuleGeometry(r * 1.1, L * 0.55, 6, 14), gooM); sg.position.set(0, L * 0.62, r * 0.12); g.add(sg); shells.goo.push(sg); }
      }
      if (n === 2) {
        const nail = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 10), nailM); nail.scale.set(r * 0.82, L * 0.36, r * 0.32); nail.position.set(0, L * 0.6, -r * 0.82); g.add(nail);
      }
      if (n >= 1 && k !== "P") {
        for (let d = 0; d < 7; d++) {                               // sweat beads all round the end of the finger
          const b = new THREE.Mesh(new THREE.SphereGeometry(1, 14, 10), dropM); const a = d * 2.4 + n + k.charCodeAt(0);
          b.userData = { p: v3(Math.sin(a) * r * 0.96, L * (0.2 + 0.6 * ((d * 0.37 + n * 0.21) % 1)), Math.cos(a) * r * 0.96), s: 0.005 + 0.0035 * ((d * 7 + n) % 3) / 2 };
          g.add(b); drops.push(b);
        }
      }
      const hl = new THREE.Mesh(new THREE.CapsuleGeometry(r * 1.22, L, 6, 14), new THREE.MeshBasicMaterial({ color: 0xffd84d, transparent: true, opacity: 0, side: THREE.BackSide, depthWrite: false }));
      hl.position.y = L / 2; hl.renderOrder = 5; g.add(hl); (shells.hl[k] ??= []).push(hl);
      j.push(g); parent = g;
    }
    F[k] = { base, j, tip: (() => { const o = new THREE.Object3D(); o.position.y = f.len[2] * 0.82; o.position.z = f.r * 0.7; j[2].add(o); return o; })() };
  }
  return { root, wrist, F, fore, cuff, shells, drops };
}
let HAND = makeHand(); scene.add(HAND.root);
HAND.root.traverse((o) => { if (o.isMesh) { o.castShadow = false; o.receiveShadow = false; } });
// a pose: wrist [flex, deviation, pronation]; each finger [knuckle, middle, end joint curl, splay] in degrees; thumb [abduction, opposition, curls...]
function applyHand(q) {
  const w = q.w ?? [0, 0, 0]; HAND.wrist.rotation.set(w[0] * D2R, w[2] * D2R, w[1] * D2R, "YXZ");
  for (const k of "IMRP") { const a = q[k] ?? [8, 10, 6, 0], f = FINGERS[k], F = HAND.F[k]; F.base.rotation.set(0, 0, (f.sp + (a[3] ?? 0)) * D2R); for (let n = 0; n < 3; n++) F.j[n].rotation.x = a[n] * D2R; }
  const t = q.T ?? T_OPEN, F = HAND.F.T;
  F.base.rotation.set(t[0] * D2R, t[1] * D2R, t[2] * D2R);
  F.j[0].rotation.x = t[3] * D2R; F.j[1].rotation.x = t[4] * D2R; F.j[2].rotation.x = t[5] * D2R;
}
const mixHand = (a, b, u) => mixPose(a, b, u);
// the thumb's base turned so it points at `aim` with its pad toward `pad` (wrist frame); returns its euler in degrees
function aimThumb(aim, pad, curls = [6, 8, 6]) {
  const b = v3(FINGERS.T.x, FINGERS.T.y, 0.03), y = aim.clone().sub(b).normalize(), z0 = pad.clone().sub(b);
  const z = z0.sub(y.clone().multiplyScalar(z0.dot(y))).normalize(), x = y.clone().cross(z).normalize();
  const e = new THREE.Euler().setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, z), "XYZ");
  return [e.x / D2R, e.y / D2R, e.z / D2R, ...curls];
}
// the fingers wrap until they touch: a surface in the wrist frame (signed distance), each finger curled step by step until any
// point of it reaches the surface. Solved once per grip, at load, with the hand at the origin.
function solveWrap(base, sdf, curl = {}, maxDeg = null) {
  // joint by joint, from the knuckle out: each joint bends until the finger (from that bone out) touches the surface, then the next
  const q = JSON.parse(JSON.stringify(base));
  HAND.root.position.set(0, 0, 0); HAND.root.quaternion.identity(); HAND.root.updateMatrixWorld(true);
  const MAX = maxDeg ?? { I: [70, 100, 80], M: [70, 100, 80], R: [80, 100, 80], P: [85, 100, 80], T: [60, 70, 80] };
  for (const k of Object.keys(curl)) {
    const F = HAND.F[k], f = FINGERS[k], isT = k === "T", lim = curl[k] ?? MAX[k] ?? [80, 100, 80];
    const get = () => (isT ? q.T.slice(3, 6) : q[k].slice(0, 3));
    const put = (ang) => { if (isT) q.T = [q.T[0], q.T[1], q.T[2], ...ang]; else q[k] = [...ang, q[k][3] ?? 0]; };
    if (!isT && !q[k]) q[k] = [0, 0, 0, 0];
    const touching = (from) => {
      applyHand(q); HAND.root.updateMatrixWorld(true);
      for (let n = from; n < 3; n++) for (const fy of [0.25, 0.5, 0.75, 1.0]) {
        const p = F.j[n].localToWorld(v3(0, f.len[n] * fy, 0)); HAND.wrist.worldToLocal(p);
        if (sdf(p) < f.r * (1 - 0.06 * n) * 0.95) return true;
      }
      return false;
    };
    for (let n = 0; n < 3; n++) {
      const ang = get();
      if (touching(n)) continue;
      for (let d = ang[n]; d <= lim[n]; d += 1) { ang[n] = d; put(ang); if (touching(n)) { ang[n] = Math.max(0, d - 1); put(ang); break; } }
    }
  }
  return q;
}
const sdSphere = (c, r) => (p) => p.distanceTo(c) - r;
function sdRoundBox(c, half, r, rot) {                            // half = half extents; rot = the box's orientation in the wrist frame
  const inv = rot.clone().invert();
  return (p) => { const q = p.clone().sub(c).applyQuaternion(inv); const d = v3(Math.abs(q.x) - half.x + r, Math.abs(q.y) - half.y + r, Math.abs(q.z) - half.z + r);
    return v3(Math.max(d.x, 0), Math.max(d.y, 0), Math.max(d.z, 0)).length() + Math.min(Math.max(d.x, d.y, d.z), 0) - r; };
}

// ------------------------------------------------------------------ the baseball: white leather, the figure-eight seam, 108 double stitches
const BALL_R = 0.1208;
function makeBaseball() {
  const g = new THREE.Group();
  const leather = canvasTex(512, 256, (c, w, h) => { c.fillStyle = "#f1ede3"; c.fillRect(0, 0, w, h); for (let k = 0; k < 16000; k++) { const v = rnd(); c.fillStyle = v < 0.5 ? `rgba(150,130,110,${0.05 + rnd() * 0.08})` : `rgba(255,255,255,${0.1 + rnd() * 0.15})`; c.fillRect(rnd() * w, rnd() * h, 1 + rnd() * 2, 1 + rnd() * 2); } });
  const bump = canvasTex(512, 256, (c, w, h) => { c.fillStyle = "#808080"; c.fillRect(0, 0, w, h); for (let k = 0; k < 30000; k++) { const v = 100 + rnd() * 70; c.fillStyle = `rgb(${v},${v},${v})`; c.fillRect(rnd() * w, rnd() * h, 1, 1); } }, { srgb: false });
  const ball = new THREE.Mesh(new THREE.SphereGeometry(BALL_R, 48, 32), new THREE.MeshPhysicalMaterial({ map: leather, bumpMap: bump, bumpScale: 0.4, roughness: 0.62, sheen: 0.3, sheenColor: 0xffffff, envMap: ENV, envMapIntensity: 0.45 }));
  g.add(ball);
  const a = 0.74, b = 0.26, cc = 2 * Math.sqrt(a * b);
  const S = (t) => v3(a * Math.cos(t) + b * Math.cos(3 * t), a * Math.sin(t) - b * Math.sin(3 * t), cc * Math.sin(2 * t)).normalize();
  const pts = []; for (let i = 0; i <= 400; i++) pts.push(S(i / 400 * Math.PI * 2).multiplyScalar(BALL_R * 1.0));
  const groove = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts, true), 400, 0.0042, 6, true), new THREE.MeshStandardMaterial({ color: 0xd6cfc1, roughness: 0.8 }));
  g.add(groove);
  const N = 108, st = new THREE.InstancedMesh(new THREE.CapsuleGeometry(0.0017, 0.013, 3, 6), new THREE.MeshStandardMaterial({ color: 0xc8232c, roughness: 0.55 }), 2 * N);
  const m4 = new THREE.Matrix4(), up = v3(0, 1, 0);
  for (let i = 0; i < N; i++) {
    const t = (i + 0.5) / N * Math.PI * 2, p = S(t), T = S(t + 1e-3).sub(S(t - 1e-3)).normalize(), B = p.clone().cross(T).normalize();
    for (const sgn of [-1, 1]) {
      const from = p.clone().multiplyScalar(BALL_R * 1.012).addScaledVector(B, sgn * 0.0135).addScaledVector(T, 0.006), to = p.clone().multiplyScalar(BALL_R * 1.02).addScaledVector(B, sgn * 0.0025).addScaledVector(T, -0.004);
      const mid = from.clone().add(to).multiplyScalar(0.5), dir = to.clone().sub(from).normalize();
      m4.compose(mid, new THREE.Quaternion().setFromUnitVectors(up, dir), v3(1, 1, 1)); st.setMatrixAt(2 * i + (sgn > 0 ? 1 : 0), m4);
    }
  }
  g.add(st);
  g.traverse((o) => { if (o.isMesh) o.castShadow = true; });
  return g;
}
const BB = makeBaseball(); scene.add(BB);
const blurB = new THREE.Mesh(new THREE.SphereGeometry(BALL_R * 1.05, 16, 12), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.0, depthWrite: false }));
scene.add(blurB);
// a long glowing streak for the ball in flight at full speed (wide shots)
const TRAIL = []; for (let i = 0; i < 26; i++) { const m = new THREE.Mesh(new THREE.SphereGeometry(0.075, 10, 8), new THREE.MeshBasicMaterial({ color: 0x56d1ff, transparent: true, opacity: 0.6, depthWrite: false })); m.visible = false; m.renderOrder = 7; scene.add(m); TRAIL.push(m); }
const STREAK = []; for (let i = 0; i < 16; i++) { const m = new THREE.Mesh(new THREE.SphereGeometry(0.11 * (1 - i / 16) + 0.02, 8, 6), new THREE.MeshBasicMaterial({ color: 0xfff1c8, transparent: true, opacity: 0.35 * (1 - i / 16), depthWrite: false })); m.visible = false; scene.add(m); STREAK.push(m); }



// ------------------------------------------------------------------ choking up: the cast
HAND.root.visible = false;
const HITS = PLAY.hits;
for (const el of [C.elR, C.elL, pitcher.elR, pitcher.elL]) el.children[0].children[0].scale.set(0.75, 1, 0.75);
batter.bat.visible = false; batter.handL.children[0].visible = false; batter.handR.children[0].visible = false;

// ------------------------------------------------------------------ the bat: a 34 in maple bat, natural handle with pine tar, dark barrel
const BAT_LEN = 2.833, SWEET = 2.30, CH = 0.167;                   // the sweet spot about 6 in from the end; choking up = hands 2 in higher
const BAT_PROF = [[0, 0], [0, 0.05], [0.012, 0.066], [0.03, 0.067], [0.046, 0.055], [0.065, 0.042], [0.11, 0.04], [0.8, 0.041], [1.15, 0.047], [1.45, 0.062],
  [1.75, 0.085], [2.0, 0.1], [2.2, 0.105], [2.76, 0.105], [2.8, 0.102], [2.825, 0.094], [2.833, 0.075], [2.833, 0]];
function batRadius(y) { for (let i = 1; i < BAT_PROF.length; i++) if (y <= BAT_PROF[i][0]) { const [y0, r0] = BAT_PROF[i - 1], [y1, r1] = BAT_PROF[i]; return y1 > y0 ? lerp(r0, r1, (y - y0) / (y1 - y0)) : r1; } return 0; }
const batGeo = (() => {                                            // resampled so the texture's v runs evenly along the bat
  const pts = [v3(0, 0, 0)]; pts.push(new THREE.Vector2(0.05, 0));
  const out = [new THREE.Vector2(0.0001, 0)];
  for (let i = 0; i <= 160; i++) { const y = BAT_LEN * i / 160; out.push(new THREE.Vector2(Math.max(batRadius(y), 0.0001), y)); }
  out.push(new THREE.Vector2(0.0001, BAT_LEN));
  return new THREE.LatheGeometry(out, 48);
})();
const batTex = canvasTex(256, 2048, (g, w, h) => {
  // v runs along the bat (canvas top = the end of the bat)
  const yAt = (y) => h * (1 - y / BAT_LEN);
  g.fillStyle = "#d8b27a"; g.fillRect(0, 0, w, h);
  for (let k = 0; k < 260; k++) { const x = rnd() * w, a = 0.05 + rnd() * 0.12; g.strokeStyle = `rgba(${120 + rnd() * 40},${80 + rnd() * 30},${40 + rnd() * 20},${a})`; g.lineWidth = 0.6 + rnd() * 1.6;
    g.beginPath(); g.moveTo(x, 0); for (let y = 0; y <= h; y += 64) g.lineTo(x + Math.sin(y * 0.004 + k) * 3, y); g.stroke(); }
  // pine tar on the handle, darkest where the hands go
  const tar = g.createLinearGradient(0, yAt(1.05), 0, yAt(0.08));
  tar.addColorStop(0, "rgba(92,52,20,0)"); tar.addColorStop(0.25, "rgba(92,52,20,.55)"); tar.addColorStop(0.6, "rgba(70,38,14,.75)"); tar.addColorStop(1, "rgba(60,32,12,.6)");
  g.fillStyle = tar; g.fillRect(0, yAt(1.05), w, yAt(0.08) - yAt(1.05));
  for (let k = 0; k < 900; k++) { g.fillStyle = `rgba(40,20,8,${rnd() * 0.25})`; g.fillRect(rnd() * w, yAt(0.15 + rnd() * 0.75), 2 + rnd() * 6, 1 + rnd() * 3); }
  // the dark barrel, fading in over the taper
  const bar = g.createLinearGradient(0, yAt(1.75), 0, yAt(1.3));
  bar.addColorStop(0, "rgba(22,14,10,1)"); bar.addColorStop(1, "rgba(22,14,10,0)");
  g.fillStyle = bar; g.fillRect(0, yAt(1.75), w, yAt(1.3) - yAt(1.75));
  g.fillStyle = "rgb(22,14,10)"; g.fillRect(0, 0, w, yAt(1.75));
  for (let k = 0; k < 120; k++) { const x = rnd() * w; g.strokeStyle = `rgba(90,60,40,${0.06 + rnd() * 0.08})`; g.lineWidth = 1; g.beginPath(); g.moveTo(x, 0); g.lineTo(x + rnd() * 4, yAt(1.6)); g.stroke(); }
  // a plain gold band and a ring of ink dots for the grain check
  g.fillStyle = "#c9a24a"; g.fillRect(0, yAt(2.62), w, 10);
  g.fillStyle = "#0b0b0b"; g.fillRect(0, yAt(0.05), w, yAt(0) - yAt(0.05));
});
const BAT = new THREE.Group(); scene.add(BAT);
const batMesh = new THREE.Mesh(batGeo, new THREE.MeshPhysicalMaterial({ map: batTex, roughness: 0.32, clearcoat: 0.7, clearcoatRoughness: 0.18, envMap: ENV, envMapIntensity: 0.7 }));
batMesh.castShadow = true; BAT.add(batMesh);

// ------------------------------------------------------------------ the hands: two batting gloves on the handle (the close-up hand rig, twice)
const gloveM = new THREE.MeshPhysicalMaterial({ color: 0x17191e, roughness: 0.4, sheen: 0.8, sheenColor: 0x6c7a8c, sheenRoughness: 0.45, clearcoat: 0.2, clearcoatRoughness: 0.5, envMap: ENV, envMapIntensity: 0.55 });
const strapM = new THREE.MeshPhysicalMaterial({ color: KIT.away.accent, roughness: 0.5, envMap: ENV, envMapIntensity: 0.4 });
const armM = new THREE.MeshPhysicalMaterial({ color: KIT.away.skin, roughness: 0.55, sheen: 0.4, sheenColor: 0xffc6a8, envMap: ENV, envMapIntensity: 0.3 });
const sleeveM = new THREE.MeshStandardMaterial({ color: 0x15181d, roughness: 0.8, side: THREE.DoubleSide });
function gloveHand(Hn) {
  Hn.root.traverse((o) => {
    if (!o.isMesh) return; const m = o.material;
    if (m === skinM || m === tipM) o.material = gloveM;
    else if (m === nailM || m === dustM || m === gooM || m === dropM || m.side === THREE.BackSide) o.visible = false;
  });
  Hn.fore.material = armM; Hn.cuff.material = sleeveM;
  const strap = new THREE.Mesh(new THREE.CylinderGeometry(0.104, 0.104, 0.085, 32), strapM); strap.scale.set(1.2, 1, 0.9); strap.position.y = -0.005; Hn.root.add(strap);
  const cuffG = new THREE.Mesh(new THREE.CylinderGeometry(0.106, 0.103, 0.07, 32), gloveM); cuffG.scale.set(1.2, 1, 0.9); cuffG.position.y = 0.07; Hn.root.add(cuffG);
  Hn.root.traverse((o) => { if (o.isMesh) { o.castShadow = false; o.receiveShadow = false; } });
}
const HR = makeHand(), HL = makeHand(); gloveHand(HR); gloveHand(HL);
function withHand(Hn, f) { const h0 = HAND; HAND = Hn; try { return f(); } finally { HAND = h0; } }
// the grip in the right hand's wrist frame: the handle runs diagonally across the base of the fingers
const GA = v3(1, 0.42, 0).normalize(), GC = v3(0, 0.235, 0.102), GR = 0.041;
const sdHandle = (p) => { const d = p.clone().sub(GC); return d.sub(GA.clone().multiplyScalar(d.dot(GA))).length() - GR; };
const GRIP_Q = withHand(HR, () => solveWrap({ w: [0, 0, 0], I: [4, 0, 0, -2], M: [4, 0, 0, 0], R: [4, 0, 0, 2], P: [4, 0, 0, 4],
  T: aimThumb(v3(-0.02, 0.3, 0.17), GC.clone().addScaledVector(GA, 0.08), [8, 8, 8]) }, sdHandle,
  { I: [95, 110, 80], M: [95, 110, 80], R: [95, 110, 80], P: [95, 110, 80], T: [50, 60, 70] }));
withHand(HR, () => applyHand(GRIP_Q)); withHand(HL, () => applyHand(GRIP_Q));
function mountHand(Hn, mirror, palm) {                             // put the hand on the bat: its grip axis along the bat's +y, its palm toward `palm`
  const g = new THREE.Group(); g.add(Hn.root);
  const S = v3(mirror ? -1 : 1, 1, 1), a = GA.clone().multiply(S), n0 = v3(0, 0, 1), c = GC.clone().multiply(S);
  const Y = a.clone().normalize(), Z = n0.clone().sub(Y.clone().multiplyScalar(n0.dot(Y))).normalize(), X = Y.clone().cross(Z);
  const src = new THREE.Matrix4().makeBasis(X, Y, Z), Yt = v3(0, 1, 0), Zt = palm.clone().normalize(), Xt = Yt.clone().cross(Zt);
  const R = new THREE.Matrix4().makeBasis(Xt, Yt, Zt).multiply(src.clone().transpose());
  Hn.root.quaternion.setFromRotationMatrix(R); Hn.root.scale.copy(S); Hn.root.position.copy(c.clone().applyQuaternion(Hn.root.quaternion).negate());
  BAT.add(g); return g;
}
const GL = mountHand(HL, true, v3(0, 0, 1)), GRt = mountHand(HR, false, v3(0, 0, -1));   // left hand on the bottom (a right-handed hitter)
const GRIP0 = 0.158, GSPAN = 0.25;                                 // the bottom hand's center above the knob, and the gap to the top hand
let FORE = true;
function setGrip(choke, roll = 0) {
  GL.position.y = GRIP0 + choke * CH; GRt.position.y = GRIP0 + GSPAN + choke * CH;
  GL.rotation.y = roll; GRt.rotation.y = roll;
  for (const Hn of [HL, HR]) { Hn.fore.visible = FORE; Hn.cuff.visible = false; }
  return GRIP0 + GSPAN / 2 + choke * CH;                           // the middle of the hands, measured from the knob
}

// ------------------------------------------------------------------ the graphics on the bat: effective length, reach, the bat path
const glowM = (c, o) => new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: o, depthWrite: false, toneMapped: false });
const LEN = new THREE.Group(); BAT.add(LEN); LEN.visible = false;
const lenFull = new THREE.Mesh(new THREE.BoxGeometry(0.022, 1, 0.022), glowM(0xffffff, 0.7)); LEN.add(lenFull);
const lenCur = new THREE.Mesh(new THREE.BoxGeometry(0.03, 1, 0.03), glowM(0x56d1ff, 0.95)); LEN.add(lenCur);
const tick = (m) => new THREE.Mesh(new THREE.BoxGeometry(0.016, 0.016, 0.13), m.material);
const tA = tick(lenFull), tB = tick(lenCur), tC = tick(lenCur); LEN.add(tA, tB, tC);
function setLen(hBottomEdge, off = 0.26) {                         // two bars beside the bat (toward the camera's side): the full bat, and hands-to-end
  lenFull.scale.y = BAT_LEN - 0.035; lenFull.position.set(0, (BAT_LEN + 0.035) / 2, -off);
  lenCur.scale.y = BAT_LEN - hBottomEdge; lenCur.position.set(0, (BAT_LEN + hBottomEdge) / 2, -off - 0.1);
  tA.position.set(0, 0.035, -off); tB.position.set(0, hBottomEdge, -off - 0.1); tC.position.set(0, BAT_LEN, -off - 0.05);
}
const GHOSTS = []; for (let i = 0; i < 7; i++) { const m = new THREE.Mesh(batGeo, glowM(0xffd84d, 0.5 * (1 - i / 9))); m.visible = false; scene.add(m); GHOSTS.push(m); }
const REACH = [0xffd84d, 0x56d1ff].map((c) => { const m = new THREE.Mesh(new THREE.RingGeometry(1, 1.025, 96, 1, -0.75, 1.5), glowM(c, 0.95)); m.material.side = THREE.DoubleSide; m.visible = false; scene.add(m); return m; });
const FLASH = new THREE.Sprite(new THREE.SpriteMaterial({ map: dotTex, color: 0xfff4d6, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: 0 })); scene.add(FLASH);

// ------------------------------------------------------------------ poses: a right-handed hitter in the left-side box, facing +x
const B_STANCE = { drop: -0.35, lean: 18, look: 80, nod: -4, hipL: [20, 16], hipR: [22, 14], knL: 26, knR: 26, shL: [52, 8, 0], shR: [62, 36, 0], elL: 98, elR: 112, twist: 18 };
const B_LOAD = { ...B_STANCE, twist: 30, pelvisTwist: -8, hipL: [34, 22], knL: 40, shR: [70, 42, 0] };
const B_LAUNCH = { ...B_STANCE, twist: 28, pelvisTwist: 2, hipL: [28, 28], knL: 18, hipR: [26, 10], knR: 34 };
const B_MID = { drop: -0.45, lean: 22, look: 70, nod: -6, twist: 8, pelvisTwist: 42, hipL: [26, 28], knL: 14, hipR: [22, 10], knR: 40, shL: [82, -8, 0], elL: 38, shR: [58, 22, 0], elR: 78 };
const B_CONTACT = { drop: -0.5, lean: 24, look: 45, nod: -10, twist: -6, pelvisTwist: 72, hipL: [24, 28], knL: 10, hipR: [18, 12], knR: 46, shL: [86, -22, 0], elL: 8, shR: [80, 6, 0], elR: 26 };
const B_FOLLOW = { drop: -0.4, lean: 18, look: 20, twist: -30, pelvisTwist: 86, hipL: [20, 28], knL: 8, hipR: [10, 12], knR: 52, shL: [112, -8, 0], elL: 40, shR: [118, -28, 0], elR: 62 };
const B_FINISH = { drop: -0.3, lean: 10, look: 10, twist: -40, pelvisTwist: 92, hipL: [16, 26], knL: 8, hipR: [6, 12], knR: 56, shL: [142, 12, 0], elL: 104, shR: [150, -40, 0], elR: 112 };
const B_TAKE = { ...B_STANCE, twist: 26, pelvisTwist: -6, hipL: [30, 24], knL: 22, look: 76 };
const B_WALK0 = v3(-5.6, 0, 6.5), B_ROOT = v3(-3.15, 0, 0.15);
const D_STANCE = v3(-0.1, 0.86, 0.5), D_REGRIP = v3(0.55, 0.62, 0.15), D_CARRY = v3(0.15, 0.95, 0.3);
const D_C = v3(1, -0.08, -0.12).normalize();
function slerpDir(K, t) {
  if (t <= K[0][0]) return K[0][1].clone().normalize();
  for (let i = 1; i < K.length; i++) if (t <= K[i][0]) {
    const u = (t - K[i - 1][0]) / (K[i][0] - K[i - 1][0]), a = K[i - 1][1].clone().normalize(), b = K[i][1].clone().normalize();
    return a.applyQuaternion(new THREE.Quaternion().slerp(new THREE.Quaternion().setFromUnitVectors(a, b), K[i][2] ? smooth(u) : u));
  }
  return K.at(-1)[1].clone().normalize();
}
const swingKeys = (tc, dc) => { const ts = tc - 0.15; return [[ts - 0.3, D_STANCE], [ts, v3(0.12, 0.92, 0.38)], [ts + 0.08, v3(-0.2, 0.35, 0.92)], [tc, dc], [tc + 0.08, v3(0.25, 0.12, -1), 1], [tc + 0.3, v3(-0.7, 0.5, -0.2), 1], [tc + 0.7, v3(-0.35, -0.5, 0.8), 1]]; };
const swingPose = (k, tc) => { const ts = tc - 0.15; return keyed([[-0.5, B_STANCE], [-0.15, B_LOAD], [ts, B_LAUNCH], [ts + 0.08, B_MID], [tc, B_CONTACT], [tc + 0.12, B_FOLLOW], [tc + 0.6, B_FINISH]], k); };
const takePose = (k) => keyed([[-0.5, B_STANCE], [-0.15, B_LOAD], [0.25, B_TAKE], [0.9, B_STANCE]], k);
const handsMid = () => wpos(batter.handL).lerp(wpos(batter.handR), 0.5);
// each swing is placed once: the bat's line at contact passes through the ball, at distance D from the middle of the hands
const FIX = {};
function fixFor(pk, D) {
  const key = pk + "|" + D; if (FIX[key]) return FIX[key];
  const P = PI_[pk], Cp = V(P.contact);
  batter.root.position.copy(B_ROOT); batter.root.rotation.y = Math.PI / 2; applyPose(batter, B_CONTACT); batter.root.updateMatrixWorld(true);
  const Hm = handsMid(), dy = clamp((Cp.y - Hm.y) / D, -0.85, 0.85), hz = v3(D_C.x, 0, D_C.z).normalize().multiplyScalar(Math.sqrt(1 - dy * dy));
  const dc = v3(hz.x, dy, hz.z);
  const n = v3(0, 0, 1).addScaledVector(dc, -dc.z).normalize(), Cb = Cp.clone().addScaledVector(n, BALL_R + 0.1);   // the ball meets the face of the barrel
  const fix = Cb.sub(Hm).addScaledVector(dc, -D); fix.y = 0;
  return (FIX[key] = { fix, dc });
}

// ------------------------------------------------------------------ the scene at play time t; s carries the shot's settings
function batFrame(dir) {                                           // the bat's roll: the palms face the way the swing moves the bat
  const Y = dir.clone().normalize(), Z = v3(0, 1, 0).cross(Y).normalize(), X = Y.clone().cross(Z);
  return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(X, Y, Z));
}
function deliver(t, rel) {
  const k = t - rel, F = 1.05;
  let q = P_SET, pos = RUB.clone().add(v3(0, 0, 0.1)), yaw = -Math.PI / 2;
  if (k > -F) {
    q = keyed([[-F, P_SET], [-0.75, P_LIFT], [-0.3, P_STRIDE], [0, P_REL], [0.35, P_FOLLOW], [1.2, { ...READY, look: 0 }]], k);
    const zp = lerp(-60.6, -57.6, smooth((k + 0.42) / 0.48)); pos = v3(0, MOUND_H * (zp > -59 ? 0.6 : 1), zp);
    yaw = lerp(-Math.PI / 2, 0, smooth((k + 0.58) / 0.58));
  }
  return [q, pos, yaw];
}
const P_SET = { lean: 4, look: 80, nod: 4, shL: [42, 8, 0], elL: 105, shR: [38, -4, 0], elR: 112, hipL: [4, 6], hipR: [4, 6], knL: 8, knR: 8 };
const P_LIFT = { lean: -4, look: 80, shL: [48, 8, 0], elL: 100, shR: [44, -4, 0], elR: 108, hipL: [100, 4], knL: 105, hipR: [6, 6], knR: 14, drop: -0.15 };
const P_STRIDE = { lean: 6, look: 40, drop: -0.6, twist: -50, shL: [80, 35, 0], elL: 25, shR: [-55, 80, 0], elR: 85, hipL: [52, 4], knL: 28, hipR: [-28, 6], knR: 38 };
const P_REL = { lean: 42, nod: 8, drop: -1.0, twist: 28, shL: [12, 32, 0], elL: 85, shR: [168, 22, 0], elR: 8, hipL: [72, 4], knL: 22, hipR: [-18, 6], knR: 92 };
const P_FOLLOW = { lean: 62, nod: 18, drop: -1.25, twist: 48, shL: [8, 38, 0], elL: 95, shR: [58, -24, 0], elR: 22, hipL: [82, 4], knL: 38, hipR: [34, 6], knR: 84 };
const C_SET = { ...CROUCH, shL: [62, 18, 0], elL: 40, shR: [20, 10, 0], elR: 50, nod: -18 };
const U_SET = { drop: -1.0, lean: 30, nod: -6, hipL: [52, 28], hipR: [52, 28], knL: 68, knR: 68, shL: [30, 20, 0], elL: 60, shR: [30, 20, 0], elR: 60 };
const RUB = v3(0, MOUND_H, -60.5);
const chokeAt = (t, s) => s.cht ? keyed(s.cht.map(([a, b]) => [a, { u: b }]), t).u : (s.choke ?? 0);

// ------------------------------------------------------------------ pitch tipping: the pitcher's tells (hypothetical, for this one pitcher)
// tell = { glove: "lo" | "hi" (where his hands come set), flare: 0 | 1 (the glove opens while he changes grip), hold: seconds in the set }
const P_LOOK = { ...STAND, lean: 6, look: 80, nod: 6, shL: [10, 10, 0], elL: 24, shR: [8, 10, 0], elR: 22 };          // on the rubber, side on, looking in for the sign
const SET_LO = { ...P_SET, shL: [6, 10, 0], elL: 82, shR: [4, -8, 0], elR: 88 };                                       // hands together at the belt
const SET_HI = { ...P_SET, shL: [52, 8, 0], elL: 120, shR: [48, -4, 0], elR: 126 };                                      // hands together at the chest
const GLOVE_MESH = pitcher.handL.children[0], GLOVE_S = GLOVE_MESH.scale.clone();
function deliverT(t, rel, tell = {}) {
  const k = t - rel, F = 1.05, hold = tell.hold ?? 1.2, k0 = -F - hold;          // k0: when he is fully set
  const SET = tell.glove === "lo" ? SET_LO : SET_HI;
  let q = P_LOOK, pos = RUB.clone().add(v3(0, 0, 0.1)), yaw = -Math.PI / 2, flare = 0;
  if (k > k0 - 0.55) q = mixPose(P_LOOK, SET, smooth((k - k0 + 0.55) / 0.55));
  if (tell.flare && k > k0 && k < -F) {                                            // the hand works the grip in the glove: the glove flares, the wrist turns
    const u = clamp((k - k0 - 0.15) / 0.7, 0, 1); flare = Math.sin(Math.PI * u);
    q = { ...q, elR: q.elR - 10 * flare, shR: [q.shR[0] + 6 * flare, q.shR[1] - 14 * flare, 0] };
  }
  if (k > -F) {
    q = keyed([[-F, SET], [-0.75, P_LIFT], [-0.3, P_STRIDE], [0, P_REL], [0.35, P_FOLLOW], [1.2, { ...READY, look: 0 }]], k);
    const zp = lerp(-60.6, -57.6, smooth((k + 0.42) / 0.48)); pos = v3(0, MOUND_H * (zp > -59 ? 0.6 : 1), zp);
    yaw = lerp(-Math.PI / 2, 0, smooth((k + 0.58) / 0.58));
  }
  GLOVE_MESH.scale.set(GLOVE_S.x * (1 + 0.32 * flare), GLOVE_S.y * (1 + 0.06 * flare), GLOVE_S.z * (1 + 0.5 * flare));
  return [q, pos, yaw];
}
// the highlight ring on the glove (turned to face whichever camera renders it)
const TELL = new THREE.Mesh(new THREE.RingGeometry(0.62, 0.7, 64), glowM(0xffd84d, 0)); TELL.material.side = THREE.DoubleSide; TELL.renderOrder = 8; scene.add(TELL);
const TELL2 = new THREE.Mesh(new THREE.RingGeometry(0.74, 0.77, 64), glowM(0xffd84d, 0)); TELL2.material.side = THREE.DoubleSide; TELL2.renderOrder = 8; scene.add(TELL2);
function tellRing(op, c) {
  TELL.visible = TELL2.visible = op > 0.01; if (!TELL.visible) return;
  pitcher.root.updateMatrixWorld(true); const g = wpos(pitcher.handL);
  for (const m of [TELL, TELL2]) { m.position.copy(g); m.quaternion.copy(c.quaternion); }
  TELL.material.opacity = 0.95 * op; TELL2.material.opacity = 0.45 * op;
}

// ------------------------------------------------------------------ the catcher's signs (the jointed hand between his thighs), from the signs video
const T_OPEN = aimThumb(v3(0.3, 0.27, 0.06), v3(0.02, 0.3, 0.25));
const CURL = [88, 100, 62, 0], EXT = [4, 6, 3];
const T_TUCK = aimThumb(v3(0.0, 0.42, 0.12), v3(0.0, 0.3, 0.3), [10, 30, 20]);
const FIST = { w: [0, 0, 0], I: CURL, M: CURL, R: [92, 100, 64, 0], P: [95, 100, 66, 0], T: T_TUCK };
function signPose(n) {
  const q = { ...FIST }, ks = ["I", "M", "R", "P"], sp = { 1: [0], 2: [-3, 3], 3: [-5, 0, 5], 4: [-7, -2, 2, 7] }[n] ?? [];
  for (let i = 0; i < n; i++) q[ks[i]] = [...EXT, sp[i]];
  return q;
}
const SIGNS = { 0: FIST, 1: signPose(1), 2: signPose(2), 3: signPose(3), 4: signPose(4) };
function signAt(seq, t) {
  if (!seq || !seq.length) return FIST;
  for (let i = seq.length - 1; i >= 0; i--) {
    const [t0, n] = seq[i], t1 = i + 1 < seq.length ? seq[i + 1][0] : t0 + 0.75;
    if (t >= t0) { const out = smooth((t - t0) / 0.09), back = smooth((t - (t1 - 0.1)) / 0.08); return mixHand(FIST, SIGNS[n], out * (1 - back)); }
  }
  return FIST;
}
const C_FORE = C.elR.children[0];
HAND.cuff.visible = false; HAND.drops.forEach((d) => (d.visible = false)); HAND.shells.dust.forEach((d) => (d.visible = false)); HAND.shells.goo.forEach((d) => (d.visible = false));
function handOnCatcher(q) {
  C.root.updateMatrixWorld(true);
  const el = wpos(C.elR), w = wpos(C.handR), y = w.clone().sub(el).normalize();
  const back = v3(0, 0, 1).applyQuaternion(C.root.quaternion);
  const z = back.sub(y.clone().multiplyScalar(back.dot(y))).normalize(), x = y.clone().cross(z).normalize();
  HAND.root.visible = true; C_FORE.visible = false; HAND.fore.visible = true; HAND.cuff.visible = false;
  HAND.root.position.copy(w); HAND.root.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, z)); HAND.root.scale.set(1, 1, 1);
  applyHand(q);
}
const C_SIGN = { ...CROUCH, nod: -12, shL: [44, 34, 0], elL: 64, shR: [8, -14, -30], elR: 26 };

// ------------------------------------------------------------------ the ball in the pitcher's hand (the close-up at the end): a four-seam grip, solved at load
const BALL_C = v3(0.02, 0.37, 0.175);
const BALL_GRIP = solveWrap({ w: [0, 0, 0], I: [0, 0, 0, -3], M: [0, 0, 0, 3], R: [0, 0, 0, 9], P: [0, 0, 0, 15],
  T: aimThumb(BALL_C.clone().add(v3(-0.02, -0.1, 0.07)), BALL_C, [8, 10, 8]) }, sdSphere(BALL_C, BALL_R),
  { I: [75, 100, 80], M: [75, 100, 80], R: [90, 100, 80], P: [95, 100, 80], T: [50, 60, 70] });
const BALL_Q = new THREE.Quaternion().setFromEuler(new THREE.Euler(0.2, 0.0, 1.57));
function ballInHand(pos, look, roll) {                              // the hand on its own in front of the bokeh: wrist at pos, fingers up, palm toward `look`
  const y = v3(0, 1, 0), zf = look.clone().sub(pos); zf.y = 0; zf.normalize().negate();
  const x = y.clone().cross(zf).normalize();
  HAND.root.visible = true; HAND.fore.visible = true; HAND.cuff.visible = true;
  HAND.root.position.copy(pos); HAND.root.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, zf)); HAND.root.rotateY(roll); HAND.root.scale.set(1, 1, 1);
  applyHand(BALL_GRIP); HAND.root.updateMatrixWorld(true);
  BB.visible = true; BB.position.copy(HAND.wrist.localToWorld(BALL_C.clone()));
  const wq = new THREE.Quaternion(); HAND.wrist.getWorldQuaternion(wq); BB.quaternion.copy(wq.multiply(BALL_Q));
}

// ------------------------------------------------------------------ the runner at second and the dugout coach: two different, prearranged signals
const RUN2 = v3(-6.5, 0, -122.5), RUN_YAW = yawTo(RUN2, v3(0, 0, 0));
const R_LEAD = { drop: -0.6, lean: 26, nod: 10, hipL: [40, 22], hipR: [40, 22], knL: 48, knR: 48, shL: [18, 14, 0], shR: [18, 14, 0], elL: 25, elR: 25 };
const R_HELMET = { ...R_LEAD, drop: -0.45, lean: 18, shR: [150, -10, 0], elR: 130 };                 // right hand up to the bill of his helmet
const COACH = makePlayer(KIT.away); scene.add(COACH.root);
const CO_POS = dgAt(dg1, -15, 5.0), CO_YAW = dgYaw(dg1) + 0.35;
const CO_STAND = { ...STAND, lean: 12, nod: 4, shL: [44, 12, 0], elL: 70, shR: [44, 12, 0], elR: 70 };   // arms on the rail
const CO_CAP = { ...STAND, lean: 8, nod: 2, shL: [44, 12, 0], elL: 70, shR: [150, 6, 0], elR: 128 };     // touches the bill of his cap
const CO_SWIPE = { ...STAND, lean: 8, nod: 2, shL: [70, -20, 0], elL: 40, shR: [60, 30, 0], elR: 70 };   // swipes his left forearm

// ------------------------------------------------------------------ the scouting room: a separate scene with a video wall that plays two live renders of the pitcher
const ROOM = new THREE.Scene(); ROOM.background = new THREE.Color(0x07090d);
ROOM.add(new THREE.HemisphereLight(0x9fb4d0, 0x2a2018, 1.1)); ROOM.add(new THREE.AmbientLight(0x8090a8, 0.5));
const RKEY = new THREE.DirectionalLight(0xfff0dc, 1.6); RKEY.position.set(-6, 14, 14); RKEY.target.position.set(0, 2, 2); ROOM.add(RKEY, RKEY.target);
const RSCR = new THREE.PointLight(0x9cc8ff, 90, 40, 1.0); RSCR.position.set(0, 7, -3); ROOM.add(RSCR);
{
  const M = (c, r = 0.85, e = 0) => new THREE.MeshStandardMaterial({ color: c, roughness: r, emissive: e });
  const carpet = canvasTex(512, 512, (g, w) => { g.fillStyle = "#1b1f27"; g.fillRect(0, 0, w, w); for (let k = 0; k < 20000; k++) { const v = 20 + rnd() * 25; g.fillStyle = `rgb(${v},${v + 3},${v + 8})`; g.fillRect(rnd() * w, rnd() * w, 2, 2); } }, { repeat: [6, 6] });
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.MeshStandardMaterial({ map: carpet, roughness: 1 })); fl.rotation.x = -Math.PI / 2; ROOM.add(fl);
  const wall = M(0x1a2130, 0.9);
  const wb = new THREE.Mesh(new THREE.PlaneGeometry(40, 16), wall); wb.position.set(0, 8, -6); ROOM.add(wb);
  const wk = new THREE.Mesh(new THREE.PlaneGeometry(40, 16), wall); wk.position.set(0, 8, 22); wk.rotation.y = Math.PI; ROOM.add(wk);
  for (let i = 0; i < 4; i++) { const fr = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 2.2), M(0x2a3550, 0.6, 0x0a0f18)); fr.position.set(-9 + i * 6, 7.5, 21.9); fr.rotation.y = Math.PI; ROOM.add(fr); }
  for (const sx of [-1, 1]) { const w2 = new THREE.Mesh(new THREE.PlaneGeometry(40, 16), wall); w2.position.set(sx * 14, 8, 10); w2.rotation.y = -sx * Math.PI / 2; ROOM.add(w2); }
  const ceil = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), M(0x0d1016)); ceil.position.y = 13; ceil.rotation.x = Math.PI / 2; ROOM.add(ceil);
  for (const x of [-6, 0, 6]) { const l = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.08, 7), new THREE.MeshBasicMaterial({ color: 0xfff3dd })); l.position.set(x, 12.9, 6); ROOM.add(l); }
  // a team banner on the wall beside the screen
  const ban = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 6), M(0xc4352d, 0.7, 0x200505)); ban.position.set(-9.5, 7.2, -5.95); ROOM.add(ban);
  // the table and chairs
  const tbl = new THREE.Mesh(new THREE.BoxGeometry(12, 0.25, 3.2), M(0x2b2f36, 0.5)); tbl.position.set(0, 2.6, 4.2); ROOM.add(tbl);
  for (const x of [-5.2, 5.2]) { const leg = new THREE.Mesh(new THREE.BoxGeometry(0.3, 2.5, 2.6), M(0x16191e)); leg.position.set(x, 1.25, 4.2); ROOM.add(leg); }
  const lap = new THREE.Group(); const lb = new THREE.Mesh(new THREE.BoxGeometry(1.3, 0.06, 0.9), M(0x9aa1ab, 0.35)); lap.add(lb);
  const ls = new THREE.Mesh(new THREE.BoxGeometry(1.3, 0.85, 0.04), M(0x101318, 0.4, 0x2a4a6a)); ls.position.set(0, 0.42, -0.45); ls.rotation.x = -0.25; lap.add(ls);
  lap.position.set(3.2, 2.76, 4.0); ROOM.add(lap);
  for (const x of [-2.6, 2.4]) {                                    // two chairs
    const seat = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.22, 1.6), M(0x111419, 0.6)); seat.position.set(x, 1.45, 7.7); ROOM.add(seat);
    const back = new THREE.Mesh(new THREE.BoxGeometry(1.7, 2.0, 0.2), M(0x111419, 0.6)); back.position.set(x, 2.5, 8.55); ROOM.add(back);
    const post = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 1.35, 10), M(0x2c3036, 0.4)); post.position.set(x, 0.7, 7.7); ROOM.add(post);
  }
  const pad = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.02, 1.2), M(0xe9e4d8, 0.9)); pad.position.set(-2.4, 2.74, 4.4); pad.rotation.y = 0.2; ROOM.add(pad);
}
// the video wall: a bezel, two clips (render targets) and the pitch log underneath (a canvas, redrawn as the pattern is found)
const RT = [0, 1].map(() => new THREE.WebGLRenderTarget(960, 540, { samples: 4 }));
RT.forEach((r) => { r.texture.colorSpace = THREE.SRGBColorSpace; });
const SCREEN = new THREE.Group(); SCREEN.position.set(0, 7.4, -5.9); ROOM.add(SCREEN);
{
  const bez = new THREE.Mesh(new THREE.BoxGeometry(11.2, 7.9, 0.25), new THREE.MeshStandardMaterial({ color: 0x050608, roughness: 0.4 })); bez.position.set(0.9, 0, -0.14); SCREEN.add(bez);
  const panel = new THREE.Mesh(new THREE.PlaneGeometry(10.8, 7.5), new THREE.MeshBasicMaterial({ color: 0x0a0e15, toneMapped: false })); panel.position.x = 0.9; SCREEN.add(panel);
  RT.forEach((r, i) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(6.08, 3.42), new THREE.MeshBasicMaterial({ map: r.texture, toneMapped: false })); m.position.set(-1.6, i ? -1.8 : 1.8, 0.01); SCREEN.add(m); });
}
let LOG_HL = -1;
const logCanvas = document.createElement("canvas"); logCanvas.width = 1024; logCanvas.height = 1792;
const logTex = new THREE.CanvasTexture(logCanvas); logTex.colorSpace = THREE.SRGBColorSpace;
const LOG = [["Chest", "SL"], ["Belt", "FB"], ["Belt", "FB"], ["Chest", "SL"], ["Belt", "FB"], ["Chest", "SL"], ["Belt", "FB"], ["Chest", "SL"]];
function drawLog(hl) {                                              // hl: how far the highlight has run down the log (0..1)
  const g = logCanvas.getContext("2d"), w = logCanvas.width, h = logCanvas.height;
  g.fillStyle = "#0b1018"; g.fillRect(0, 0, w, h);
  g.fillStyle = "#7f8a9a"; g.font = "800 52px Inter, Arial, sans-serif"; g.textAlign = "left"; g.fillText("PITCH LOG", 60, 96);
  g.font = "700 40px Inter, Arial, sans-serif"; g.fillText("HANDS AT THE SET", 230, 176); g.fillText("PITCH", 760, 176);
  const y0 = 220, rh = (h - y0 - 40) / LOG.length;
  LOG.forEach(([gl, pt], i) => {
    const cy = y0 + rh * (i + 0.5), on = pt === "SL" && hl > (i + 0.5) / LOG.length;
    g.fillStyle = on ? "rgba(255,216,77,.16)" : "#141b27"; g.beginPath(); g.roundRect(40, cy - rh / 2 + 10, w - 80, rh - 20, 22); g.fill();
    if (on) { g.strokeStyle = "#ffd84d"; g.lineWidth = 8; g.stroke(); }
    g.textAlign = "left"; g.fillStyle = "#7f8a9a"; g.font = "800 50px Inter, Arial, sans-serif"; g.fillText(`#${i + 1}`, 80, cy + 18);
    g.fillStyle = gl === "Chest" ? "#ffd84d" : "#e9edf3"; g.font = "800 62px Inter, Arial, sans-serif"; g.fillText(gl, 230, cy + 22);
    g.fillStyle = pt === "SL" ? "#ff6a3d" : "#56d1ff"; g.font = "900 74px Inter, Arial, sans-serif"; g.fillText(pt, 760, cy + 26);
  });
  logTex.needsUpdate = true;
}
drawLog(0);
{ const m = new THREE.Mesh(new THREE.PlaneGeometry(3.9, 6.82), new THREE.MeshBasicMaterial({ map: logTex, toneMapped: false })); m.position.set(3.55, 0, 0.01); SCREEN.add(m); }
// the people: a hitting coach at the wall, two hitters at the table (same road grays as the batter)
const KIT_COACH = { jersey: 0x1f2633, pants: 0x3b414c, cap: 0xc4352d, accent: 0xc4352d, skin: 0x8a6048 };
const RCOACH = makePlayer(KIT_COACH), RP1 = makePlayer(KIT.away), RP2 = makePlayer(KIT.away, { helmet: false });
for (const p of [RCOACH, RP1, RP2]) ROOM.add(p.root);
const SIT = { drop: -1.55, lean: 6, nod: 8, hipL: [88, 6], hipR: [88, 6], knL: 92, knR: 92, ankL: 0, ankR: 0, shL: [40, 10, 0], elL: 70, shR: [40, 10, 0], elR: 70 };
const SIT_LEAN = { ...SIT, lean: 24, nod: 0, shR: [96, -12, 0], elR: 8 };                                // leans in and points at the screen
const CO_POINT = { ...STAND, lean: 4, look: -40, nod: 4, shR: [12, 10, 0], elR: 20, shL: [92, 64, 0], elL: 6 };   // turned to the room, left arm out to the screen
function setRoom(t, s) {
  RCOACH.root.position.set(-7.6, 0, -3.6); RCOACH.root.rotation.y = 0.55;
  applyPose(RCOACH, t > (s.cpoint ?? 1e9) ? mixPose({ ...STAND, lean: 4, look: -40, shL: [10, 10, 0], elL: 20, shR: [10, 10, 0], elR: 20 }, CO_POINT, smooth((t - s.cpoint) / 0.4)) : { ...STAND, lean: 4, look: -40, shL: [10, 10, 0], elL: 20, shR: [10, 10, 0], elR: 20 });
  RP1.root.position.set(-2.6, 0, 7.4); RP1.root.rotation.y = Math.PI + 0.12; applyPose(RP1, SIT);
  RP2.root.position.set(2.4, 0, 7.4); RP2.root.rotation.y = Math.PI - 0.12;
  const a = s.recog ?? 1e9; applyPose(RP2, t > a ? mixPose(SIT, SIT_LEAN, smooth((t - a) / 0.4)) : SIT);
  if (t > a + 0.5) RP1.neck.rotation.x += 0.25 * Math.max(0, Math.sin((t - a - 0.5) * 8));      // a nod
  const hl = s.loghl ? clamp((t - s.loghl[0]) / (s.loghl[1] - s.loghl[0]), 0, 1) : 0;
  if (Math.abs(hl - LOG_HL) > 1e-3) { drawLog(hl); LOG_HL = hl; }
}
// each clip: the same pitcher, from the third-base side, on a loop: comes set, delivers
const clipCam = new THREE.PerspectiveCamera(24, 16 / 9, 0.12, 2500);
const CLIP_L = 3.3;
function renderClips(t, s) {
  const tells = s.clips ?? [{ glove: "lo", hold: 0.9 }, { glove: "hi", hold: 0.9 }];
  tells.forEach((tl, i) => {
    const tc = ((t % CLIP_L) + CLIP_L) % CLIP_L, rel = 0.55 + (tl.hold ?? 0.9) + 1.05;
    setScene(tc, { ab: { pk: i ? "sl" : "fb", rel, swing: false, tell: tl }, streak: 1 });
    frame(clipCam, v3(-15.5, 5.6, -56.5), v3(0, 4.6, -60.4), 24, 16 / 9);
    tellRing(s.ring && (s.ring === "both" || s.ring === i) ? smooth((tc - 0.6) / 0.3) * (1 - smooth((tc - rel - 0.2) / 0.3)) : 0, clipCam);
    renderer.setRenderTarget(RT[i]); renderer.setScissorTest(false); renderer.setViewport(0, 0, 960, 540); renderer.render(scene, clipCam);
  });
  renderer.setRenderTarget(null);
}


// ------------------------------------------------------------------ the count: the strike zone, the center-field board, the catcher's reach, the umpire's call, ball four
// the strike zone at the front of the plate: 17 in wide plus the ball (a pitch is a strike if any part of it touches), knees to letters
const PLATE_F = PLAY.plate_front, ZX = 0.708 + BALL_R, ZY0 = 1.55, ZY1 = 3.45;
const ZONE = new THREE.Group(); scene.add(ZONE); ZONE.visible = false;
{
  const m = glowM(0xffffff, 0.85), w = 0.03;
  const bar = (x, y, sx, sy) => { const b = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, w), m); b.position.set(x, y, PLATE_F); ZONE.add(b); };
  bar(-ZX, (ZY0 + ZY1) / 2, w, ZY1 - ZY0 + w); bar(ZX, (ZY0 + ZY1) / 2, w, ZY1 - ZY0 + w); bar(0, ZY0, 2 * ZX, w); bar(0, ZY1, 2 * ZX, w);
  const fill = new THREE.Mesh(new THREE.PlaneGeometry(2 * ZX, ZY1 - ZY0), glowM(0xffffff, 0.06)); fill.position.set(0, (ZY0 + ZY1) / 2, PLATE_F); fill.material.side = THREE.DoubleSide; ZONE.add(fill);
}
const MARK = new THREE.Mesh(new THREE.CircleGeometry(BALL_R, 32), glowM(0xff4d4d, 0.9)); MARK.material.side = THREE.DoubleSide; scene.add(MARK); MARK.visible = false;
const MARKR = new THREE.Mesh(new THREE.RingGeometry(BALL_R * 1.15, BALL_R * 1.45, 32), glowM(0xffffff, 0.9)); MARKR.material.side = THREE.DoubleSide; scene.add(MARKR); MARKR.visible = false;
// the chase zone: where a pitcher expands to when he's ahead (just off the plate and below the knees), drawn around the zone
const CXP = 0.45, CYP = 0.4, ZCY = (ZY0 + ZY1) / 2;
const CHASE = new THREE.Group(); CHASE.position.set(0, ZCY, PLATE_F - 0.01); scene.add(CHASE); CHASE.visible = false;
{
  const m = glowM(0xff6a3d, 0.95), w = 0.035, hx = ZX, hy = (ZY1 - ZY0) / 2;
  const bar = (x, y, sx, sy) => { const b = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, w), m); b.position.set(x, y, 0); CHASE.add(b); };
  bar(-hx, 0, w, 2 * hy + w); bar(hx, 0, w, 2 * hy + w); bar(0, -hy, 2 * hx, w); bar(0, hy, 2 * hx, w);
  const fill = new THREE.Mesh(new THREE.PlaneGeometry(2 * hx, 2 * hy), glowM(0xff6a3d, 0.10)); fill.material.side = THREE.DoubleSide; fill.position.z = -0.02; CHASE.add(fill);
}
const inZone = (p) => Math.abs(p[0]) <= ZX && p[1] >= ZY0 - BALL_R && p[1] <= ZY1 + BALL_R;

// the center-field video board: the line score, the batter, and the count (balls, strikes, outs) as lights and as numbers
let BOARD_KEY = "";
const boardCanvas = document.createElement("canvas"); boardCanvas.width = 1280; boardCanvas.height = 720;
const boardTex = new THREE.CanvasTexture(boardCanvas); boardTex.colorSpace = THREE.SRGBColorSpace;
function drawBoard(b, st, o, msg) {
  const key = `${b}${st}${o}${msg}`; if (key === BOARD_KEY) return; BOARD_KEY = key;
  const g = boardCanvas.getContext("2d"), w = 1280, h = 720;
  g.fillStyle = "#05070b"; g.fillRect(0, 0, w, h); g.strokeStyle = "#1c2b4b"; g.lineWidth = 12; g.strokeRect(6, 6, w - 12, h - 12);
  g.font = "700 40px Inter, Arial, sans-serif"; g.textAlign = "left";
  const cols = ["", "1", "2", "3", "4", "5", "6", "7", "8", "9", "R", "H"], rows = [["AWAY", "0", "1", "0", "0", "0", "2", "0", "", "", "3", "7"], ["HOME", "1", "0", "0", "1", "0", "0", "1", "", "", "3", "6"]];
  cols.forEach((c, i) => { g.fillStyle = "#7f8a9a"; g.fillText(c, 50 + (i ? 170 + i * 70 : 0), 70); });
  rows.forEach((r, j) => r.forEach((c, i) => { g.fillStyle = i === 0 ? "#fff" : i >= 10 ? "#ffd84d" : "#e9edf3"; g.fillText(c, 50 + (i ? 170 + i * 70 : 0), 135 + j * 62); }));
  g.fillStyle = "#ff6a3d"; g.fillRect(50 + 170 + 8 * 70 - 12, 168, 50, 6);
  // the count: B / S / O lights and the big numbers
  const lights = (label, n, max, y, col) => {
    g.fillStyle = "#cfd6e0"; g.font = "900 64px Inter, Arial, sans-serif"; g.fillText(label, 60, y + 22);
    for (let i = 0; i < max; i++) { g.fillStyle = i < n ? col : "#1b2230"; g.beginPath(); g.arc(150 + i * 82, y, 30, 0, 7); g.fill(); if (i < n) { g.fillStyle = "rgba(255,255,255,.35)"; g.beginPath(); g.arc(142 + i * 82, y - 8, 9, 0, 7); g.fill(); } }
  };
  if (b < 0) { g.textAlign = "center"; g.fillStyle = "#7f8a9a"; g.font = "800 44px Inter, Arial, sans-serif"; g.fillText("PITCH SPEED", 640, 300); g.fillStyle = "#ffffff"; g.font = "900 230px Inter, Arial, sans-serif"; const [num, kind] = msg.split("|"); g.fillText(num, 640, 520); g.fillStyle = "#7f8a9a"; g.font = "700 40px Inter, Arial, sans-serif"; g.fillText(`MPH  ·  ${kind ?? "FASTBALL"}`, 640, 630); boardTex.needsUpdate = true; return; }
  lights("B", Math.min(b, 3), 3, 330, "#3dd68c"); lights("S", st, 2, 440, "#ff4d4d"); lights("O", o, 2, 550, "#ffd84d");
  g.textAlign = "center"; g.fillStyle = "#7f8a9a"; g.font = "800 44px Inter, Arial, sans-serif"; g.fillText("BALLS   –   STRIKES", 870, 300);
  g.fillStyle = b >= 4 ? "#ffd84d" : "#ffffff"; g.font = b >= 4 ? "900 170px Inter, Arial, sans-serif" : "900 230px Inter, Arial, sans-serif"; g.fillText(b >= 4 ? "WALK" : `${b}-${st}`, 870, 510);
  if (msg) { g.fillStyle = "#ffd84d"; g.font = "900 64px Inter, Arial, sans-serif"; g.fillText(msg, 870, 640); }
  else { g.fillStyle = "#7f8a9a"; g.font = "700 40px Inter, Arial, sans-serif"; g.fillText("AT BAT  ·  #24", 870, 630); }
  boardTex.needsUpdate = true;
}
const BOARD = (() => {
  const g = new THREE.Group();
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(64, 36), new THREE.MeshBasicMaterial({ map: boardTex, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 })); g.add(scr);
  const frameM = new THREE.MeshStandardMaterial({ color: 0x1a1f28, roughness: 0.7 });
  const fr = new THREE.Mesh(new THREE.BoxGeometry(68, 40, 2), frameM); fr.position.z = -4.0; g.add(fr);
  for (const x of [-20, 20]) { const leg = new THREE.Mesh(new THREE.BoxGeometry(3, 40, 3), frameM); leg.position.set(x, -38, -4.5); g.add(leg); }
  g.position.set(-70, 62, -432); g.lookAt(0, 20, 0); scene.add(g);
  return g;
})();
drawBoard(0, 0, 1, "");

// the catcher works his glove to where the pitch is going; the umpire calls a strike with his right arm
// the catcher's arm, solved once per pitch so the mitt is where the pitch ends (a coarse search over shoulder and elbow)
const CATCH = {};
function catchPose(pk) {
  if (CATCH[pk]) return CATCH[pk];
  const end = V(PI_[pk].path.p.at(-1)).add(v3(0, 0, 0.12));
  const cx = end.x + 0.45;                                                  // he sets up on the spot, slightly to his glove side of it
  C.root.position.set(cx, 0, 3.0); C.root.rotation.y = Math.PI;
  let best = null, bd = 1e9;
  for (const dr of [-1.7, -1.45, -1.2]) for (let fl = 0; fl <= 170; fl += 6) for (let ab = -40; ab <= 100; ab += 6) for (let el = 0; el <= 130; el += 10) {
    const q = { ...C_SET, drop: dr, shL: [fl, ab, 0], elL: el, nod: -14 }; applyPose(C, q); C.root.updateMatrixWorld(true);
    const d = wpos(C.handL).distanceTo(end); if (d < bd) { bd = d; best = q; }
  }
  best.cx = cx; return (CATCH[pk] = best);
}
const C_REACH = (dx, dy) => ({ ...C_SET, shL: [62 + clamp(dy, -1.5, 1.5) * 20, 18 + clamp(dx, -1.6, 1.6) * 24, 0], elL: 40 - clamp(dy, -1.5, 1.5) * 8, nod: -14 });
const U_STRIKE = { drop: -0.6, lean: 18, nod: -2, twist: -20, hipL: [36, 20], hipR: [36, 20], knL: 44, knR: 44, shL: [20, 20, 0], elL: 50, shR: [70, -40, 0], elR: 110 };   // the punch: right fist up and out
// ball four: he drops the bat and jogs to first
const B_JOG0 = v3(-2.2, 0, 0.6), B_JOG1 = v3(30.0, 0, -30.0);

let CUR = {}, RING_OP = 0;
function poseBatter(t, s) {                                        // the batter and the bat at play time t; returns what the shot needs
  const ab = s.ab, choke = chokeAt(t, s);
  let pos = B_ROOT.clone(), yaw = Math.PI / 2, q = B_STANCE, dir = D_STANCE.clone(), contact = null;
  const wob = Math.sin(t * 2.3) * 0.04;
  dir.add(v3(wob * 0.5, 0, wob));
  if (s.walk) {                                                    // stepping into the box, the bat carried up
    const [t0, t1] = s.walk, u = clamp((t - t0) / (t1 - t0), 0, 1);
    pos = B_WALK0.clone().lerp(B_ROOT, smooth(u));
    if (u < 1) { const ph = ((t - t0) * 1.7) % 1, sw = Math.sin(ph * 6.283);
      q = { ...STAND, lean: 6, look: 30, hipL: [18 * sw, 5], hipR: [-18 * sw, 5], knL: 10 + 14 * Math.max(0, -sw), knR: 10 + 14 * Math.max(0, sw), shL: [40, 10, 0], elL: 80, shR: [44, 20, 0], elR: 95 };
      yaw = yawTo(B_WALK0, B_ROOT) * (1 - smooth((u - 0.6) / 0.4)) + Math.PI / 2 * smooth((u - 0.6) / 0.4); dir = D_CARRY.clone(); }
    else { const k2 = t - t1; q = mixPose({ ...STAND, lean: 6, look: 30, shL: [40, 10, 0], elL: 80, shR: [44, 20, 0], elR: 95 }, B_STANCE, smooth(k2 / 0.7)); dir = D_CARRY.clone().lerp(dir, smooth(k2 / 0.7)); }
  }
  if (s.cht) {                                                     // regripping: the bat comes forward a little while the hands slide
    const a = s.cht[0][0], b = s.cht.at(-1)[0], u = clamp((t - a + 0.25) / (b - a + 0.5), 0, 1), w = Math.sin(Math.PI * u);
    dir.lerp(D_REGRIP, 0.55 * w);
  }
  if (ab) {
    const P = PI_[ab.pk], k = t - ab.rel;
    if (ab.swing) {
      const SW = ab.sw ?? ab.pk, PS = PI_[SW], tc = PS.t_contact - (ab.early ?? 0);   // he swings for SW's timing (the fastball), even when the pitch is slower
      const { fix, dc } = fixFor(SW, ab.D); pos.add(fix);
      const kc = ab.check ? tc - ab.check : 1e9;                // a checked swing: he starts it, holds up before the bat crosses
      if (k <= kc) { q = swingPose(k, tc); if (k > -0.5) dir = slerpDir(swingKeys(tc, dc), k); }
      else { const u = smooth((k - kc - 0.12) / 0.55); q = mixPose(swingPose(kc, tc), B_STANCE, u); dir = slerpDir(swingKeys(tc, dc), kc).lerp(D_STANCE.clone().normalize(), u); }
      if (ab.lunge) { const u = smooth((k - tc + 0.1) / 0.25); q = mixPose(q, { ...q, lean: (q.lean ?? 0) + 14, drop: (q.drop ?? 0) - 0.25, nod: (q.nod ?? 0) + 10 }, u * ab.lunge); }
      contact = V(PS.contact);
    } else if (k > -0.5) q = takePose(k);
    if (s.track && k > -0.15 && k < P.flight + 0.2) {                     // his eyes follow the ball in: the head turns and drops a little
      const u = smooth(k / P.flight); q = { ...q, nod: (q.nod ?? 0) + 16 * u, look: (q.look ?? 0) - 18 * u };
    }
  }
  batter.root.position.copy(pos); batter.root.rotation.y = yaw; applyPose(batter, q); batter.root.updateMatrixWorld(true);
  const hm = setGrip(choke, s.roll ?? 0), H = handsMid();
  BAT.quaternion.copy(batFrame(dir)); BAT.position.copy(H).addScaledVector(dir.clone().normalize(), -hm);
  return { choke, hm, dir: dir.normalize(), contact };
}
const batPt = (y) => { BAT.updateMatrixWorld(true); return BAT.localToWorld(v3(0, y, 0)); };

function setScene(t, s) {
  for (const [k, p] of Object.entries(HD)) { const [x, z] = homeD[k]; p.root.position.set(x, 0, z); p.root.rotation.y = Math.atan2(-x, -z); applyPose(p, READY); }
  B1F.root.position.set(56, 0, -78); B1F.root.rotation.y = Math.atan2(-56, 78); applyPose(B1F, READY);
  U1.root.position.set(70, 0, -56); U1.root.rotation.y = Math.atan2(-70, 56); applyPose(U1, { drop: -0.7, lean: 26, nod: -6, hipL: [40, 16], hipR: [40, 16], knL: 48, knR: 48, shL: [30, 12, 0], elL: 50, shR: [30, 12, 0], elR: 50 });
  HAND.root.visible = false; C_FORE.visible = true; RING_OP = 0;
  // the runner at second: leading off; his prearranged signal (in this example, a hand to the helmet)
  R.root.visible = !!s.runner; R.root.position.copy(RUN2); R.root.rotation.y = RUN_YAW;
  applyPose(R, s.rsig ? keyed([[s.rsig[0] - 0.25, R_LEAD], [s.rsig[0], R_HELMET], [s.rsig[1], R_HELMET], [s.rsig[1] + 0.3, R_LEAD]], t) : R_LEAD);
  // the coach on the dugout rail: a different team's signal (a touch of the cap, a swipe of the arm)
  COACH.root.position.copy(CO_POS); COACH.root.rotation.y = CO_YAW;
  applyPose(COACH, s.csig ? keyed([[s.csig[0] - 0.3, CO_STAND], [s.csig[0], CO_CAP], [s.csig[0] + 0.45, CO_CAP], [s.csig[0] + 0.75, CO_SWIPE], [s.csig[0] + 1.15, CO_SWIPE], [s.csig[0] + 1.5, CO_STAND]], t) : CO_STAND);
  ump.root.position.set(0.5, 0, 6.0); ump.root.rotation.y = Math.PI; applyPose(ump, U_SET);
  C.root.position.set(0.15, 0, 3.0); C.root.rotation.y = Math.PI; applyPose(C, s.signs ? C_SIGN : C_SET);
  if (s.signs) handOnCatcher(signAt(s.signs, t));
  const ab = s.ab;
  if (ab && !s.signs) {                                             // the catcher's glove goes to the pitch
    C.root.position.x = catchPose(ab.pk).cx;
    const Pp = PI_[ab.pk], k = t - ab.rel, w = smooth((k + 0.1) / 0.35) * (1 - smooth((k - Pp.flight - 0.9) / 0.5));
    applyPose(C, mixPose(C_SET, catchPose(ab.pk), w));
  }
  if (s.ucall) applyPose(ump, keyed([[s.ucall - 0.05, U_SET], [s.ucall + 0.25, U_STRIKE], [s.ucall + 0.9, U_STRIKE], [s.ucall + 1.4, U_SET]], t));
  if (s.board) { let cur = s.board[0]; for (const e of s.board) if (t >= e[0]) cur = e; drawBoard(cur[1], cur[2], cur[3], cur[4] ?? ""); }
  ZONE.visible = !!s.zone; MARK.visible = MARKR.visible = false;
  CHASE.visible = s.chase !== undefined && t >= s.chase;
  if (CHASE.visible) { const g = smooth((t - s.chase) / 0.5); CHASE.scale.set(1 + g * CXP / ZX, 1 + g * CYP / ((ZY1 - ZY0) / 2), 1); }
  if (s.mark && ab) {
    const Pp = PI_[ab.pk], k = t - ab.rel;
    if (k >= Pp.front) { const ok = inZone(Pp.cross); MARK.visible = MARKR.visible = true; MARK.material.color.set(ok ? 0xff4d4d : 0x3dd68c);
      MARK.position.set(Pp.cross[0], Pp.cross[1], PLATE_F + 0.02); MARKR.position.copy(MARK.position); MARKR.material.opacity = 0.9 * (1 - smooth((k - Pp.front - 0.6) / 0.4)) + 0.4; }
  }
  let pq = P_LOOK, ppos = RUB.clone().add(v3(0, 0, 0.1)), pyaw = -Math.PI / 2;
  GLOVE_MESH.scale.copy(GLOVE_S);
  if (ab) [pq, ppos, pyaw] = deliverT(t, ab.rel, ab.tell);
  else if (s.pset) [pq, ppos, pyaw] = deliverT(t, s.pset.rel ?? 1e9, s.pset);
  if (s.walkback) {                                                 // back up onto the mound after the hit, looking in at the catcher
    const [t0, t1] = s.walkback, a = v3(3.0, 0, -64.5), b = v3(0.0, 0, -61.0), u = clamp((t - t0) / (t1 - t0), 0, 1);
    ppos = a.clone().lerp(b, smooth(u)); ppos.y = moundY(ppos.x, ppos.z); pyaw = yawTo(a, b) * (1 - smooth((u - 0.7) / 0.3));
    const ph = ((t - t0) * 1.6) % 1, sw = Math.sin(ph * 6.283);
    pq = u < 1 ? { ...STAND, lean: 4, look: -20 * (1 - u), nod: 4, hipL: [16 * sw, 5], hipR: [-16 * sw, 5], knL: 10 + 12 * Math.max(0, -sw), knR: 10 + 12 * Math.max(0, sw), shL: [-10 * sw + 20, 12, 0], elL: 40, shR: [10 * sw, 10, 0], elR: 30 }
      : { ...STAND, lean: 6, nod: 6, shL: [24, 12, 0], elL: 40, shR: [8, 10, 0], elR: 30 };
  }
  // the arm path: where his throwing hand has been over the last half second (the same arc for both pitches)
  TRAIL.forEach((m) => (m.visible = false));
  if (s.trail && ab && t - ab.rel > -0.95) {
    for (let i = 0; i < TRAIL.length; i++) {
      const tg = t - i * 0.02; if (tg - ab.rel < -0.95 || tg - ab.rel > 0.45) continue;
      const [q2, p2, y2] = deliverT(tg, ab.rel, ab.tell); pitcher.root.position.copy(p2); pitcher.root.rotation.y = y2; applyPose(pitcher, q2);
      const m = TRAIL[i]; m.position.copy(wpos(pitcher.handR)); m.material.color.set(s.trail); m.material.opacity = 0.75 * (1 - i / TRAIL.length); m.visible = true;
    }
  }
  pitcher.root.position.copy(ppos); pitcher.root.rotation.y = pyaw; applyPose(pitcher, pq);
  if (s.ring) RING_OP = keyed(s.ring.map(([a, b]) => [a, { u: b }]), t).u;
  if (s.bnod) batter.neck.rotation.x += 0;
  FORE = !!s.fore; batter.elL.visible = batter.elR.visible = !s.fore;
  // the bat path: translucent copies of the bat a few hundredths of a second back
  GHOSTS.forEach((m) => (m.visible = false));
  if (s.ghost && ab) for (let i = 0; i < GHOSTS.length; i++) {
    const tg = t - (i + 1) * (s.ghost ?? 0.014); if (tg < ab.rel + PI_[ab.sw ?? ab.pk].t_contact - (ab.early ?? 0) - 0.2) break;
    poseBatter(tg, s); BAT.updateMatrixWorld(true); GHOSTS[i].position.copy(BAT.position); GHOSTS[i].quaternion.copy(BAT.quaternion); GHOSTS[i].visible = true;
  }
  CUR = poseBatter(t, s);
  for (const g of [GL, GRt]) g.visible = true; batter.handL.children[0].visible = batter.handR.children[0].visible = false;
  if (s.bwalk && t > s.bwalk[0]) {                                  // ball four: the bat goes down, he jogs to first
    const [t0, t1] = s.bwalk, u = clamp((t - t0) / (t1 - t0), 0, 1), pa = u < 0.15 ? B_ROOT.clone().lerp(B_JOG0, smooth(u / 0.15)) : B_JOG0.clone().lerp(B_JOG1, (u - 0.15) / 0.85);
    batter.root.position.copy(pa); batter.root.rotation.y = lerp(Math.PI / 2, yawTo(B_JOG0, B_JOG1), smooth(u / 0.15));
    applyPose(batter, u < 0.08 ? mixPose(B_STANCE, STAND, smooth(u / 0.08)) : runPose(((t - t0) * 2.4) % 1, 0.55 * smooth((u - 0.08) / 0.1)));
    BAT.position.set(-1.7, 0.11, 1.4); BAT.quaternion.setFromEuler(new THREE.Euler(0, 0.5, -Math.PI / 2 + 0.02));
    for (const g of [GL, GRt]) g.visible = false; batter.handL.children[0].visible = batter.handR.children[0].visible = true;
  }
  if (s.bnod && t > s.bnod) { batter.neck.rotation.x += 0.22 * Math.max(0, Math.sin((t - s.bnod) * 7)) * (t < s.bnod + 0.9 ? 1 : 0); }
  BAT.visible = true; batter.root.visible = !s.nobody; C.root.visible = ump.root.visible = !s.nobody;
  LEN.visible = !!s.len; if (s.len) setLen(GL.position.y - 0.125);
  // reach: the arc the end of the bat sweeps at contact, around the hands, for each grip
  REACH.forEach((m) => (m.visible = false));
  if (s.reach !== undefined && ab) {
    const { dc } = fixFor(ab.pk, ab.D), Hm = handsMid();
    [0, 1].forEach((g) => { if (s.reach === "both" || s.reach === g) {
      const m = REACH[g], r = BAT_LEN - (GRIP0 + GSPAN / 2 + g * CH), X = v3(dc.x, 0, dc.z).normalize(), Z = v3(0, 1, 0), Y = Z.clone().cross(X);
      m.visible = true; m.scale.setScalar(r); m.position.copy(Hm); m.position.y = 0.08;
      m.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(X, Y, Z)); } });
  }
  // the ball
  BB.visible = false; STREAK.forEach((m) => (m.visible = false)); FLASH.material.opacity = 0;
  if (ab) ballAt(t, s);
}
function ballAt(t, s) {
  const ab = s.ab, P = PI_[ab.pk], k = t - ab.rel; BB.visible = true;
  let path = null, kk = k, spin = P.rpm, axis = V(P.spin);
  if (k < 0) { BB.position.copy(wpos(pitcher.handR)); }
  else if (ab.hit && k >= P.t_contact) { path = HITS[ab.hit].path; kk = k - P.t_contact; BB.position.copy(pathAt(path, kk)); spin = 1800; axis = v3(0, 0, 1);
    if (kk < 0.07) { FLASH.position.copy(V(P.contact)); FLASH.scale.setScalar(0.9 + kk * 10); FLASH.material.opacity = 0.95 * (1 - kk / 0.07); } }
  else if (k < P.flight) { path = P.path; BB.position.copy(pathAt(path, k)); if (k < 0.05) BB.position.lerp(wpos(pitcher.handR), 1 - k / 0.05); }
  else BB.position.copy(wpos(C.handL)).add(v3(0, 0.05, -0.18));
  if (path && s.streak) STREAK.forEach((m, i) => { const d = (i + 1) * 0.008; if (kk - d > 0) { m.visible = true; m.position.copy(pathAt(path, kk - d)); } });
  BB.quaternion.setFromAxisAngle(axis, spin / 60 * 2 * Math.PI * Math.max(0, k));
}

// ------------------------------------------------------------------ cameras
function frame(c, pos, look, fov, aspect) { c.position.copy(pos); c.fov = fov; c.aspect = aspect; c.updateProjectionMatrix(); c.lookAt(look); }
const mixV = (a, b, u) => a.clone().lerp(b, u);
const pw = (v, vs, ts) => {
  if (v <= vs[0]) return ts[0];
  for (let i = 1; i < vs.length; i++) if (v <= vs[i]) return lerp(ts[i - 1], ts[i], (v - vs[i - 1]) / (vs[i] - vs[i - 1]));
  return ts.at(-1);
};
const A = (a) => v3(a[0], a[1], a[2]);
const OBJ = { phand: () => pitcher.handR, croot: () => COACH.root, broot: () => batter.root, bneck: () => batter.neck, bat: () => BAT, proot: () => pitcher.root, ball: () => BB, glove: () => pitcher.handL, chand: () => HAND.wrist, rneck: () => R.neck, pneck: () => pitcher.neck };
const objW = (o, p) => { const g = OBJ[o](); g.updateWorldMatrix(true, false); return g.localToWorld(A(p)); };
const CAMS = {
  world: (u, t, s) => [mixV(A(s.c0), A(s.c1 ?? s.c0), easeIO(u)), mixV(A(s.l), A(s.l1 ?? s.l), easeIO(u)), lerp(s.f0 ?? 36, s.f1 ?? s.f0 ?? 36, easeIO(u))],
  obj: (u, t, s) => [objW(s.o, mixV(A(s.c0), A(s.c1 ?? s.c0), easeIO(u)).toArray()), objW(s.lo ?? s.o, mixV(A(s.l), A(s.l1 ?? s.l), easeIO(u)).toArray()), lerp(s.f0 ?? 30, s.f1 ?? s.f0 ?? 30, easeIO(u))],
  aim: (u, t, s) => [mixV(A(s.c0), A(s.c1 ?? s.c0), easeIO(u)), objW(s.lo, s.l), lerp(s.f0 ?? 10, s.f1 ?? s.f0 ?? 10, easeIO(u))],
  // the race: a dolly beside the pitch path that keeps pace with the lead pitch (the fastball) and stops at the plate.
  // Both panes run the same camera, so the slower pitch falls behind in its frame.
  race: (u, t, s) => { const P = PI_[s.lead], k = t - s.rel0, zr = V(P.path.p[0]).z;
    const z = k <= 0 ? zr : Math.min(s.zstop ?? -4.0, pathAt(P.path, Math.min(k, P.flight)).z);
    const lz = lerp(-4.0, s.lz ?? 0, smooth(k / 0.12));                     // before the release, look back at the pitcher
    return [v3(s.cx, s.cy, z + (s.dz ?? 0)), v3(-0.6, s.ly ?? 3.6, z + lz), s.f0 ?? 40]; },
  // a world camera that turns to follow the ball once it's hit (k blends from the fixed look to the ball)
  follow: (u, t, s) => { const c = mixV(A(s.c0), A(s.c1 ?? s.c0), easeIO(u)), l0 = A(s.l), ab = s.ab, k = t - ab.rel - PI_[ab.pk].t_contact;
    const b = BB.position.clone(), w = smooth(k / (s.lag ?? 0.35)); return [c, l0.lerp(b, w * (s.fw ?? 1)), lerp(s.f0 ?? 36, s.f1 ?? s.f0 ?? 36, easeIO(u))]; },
};
function shotAt(v) {
  const L = CC.shots.list;
  const s = L.find((x) => v < x.b) || L.at(-1);
  return { s, t: pw(v, s.vs, s.ts), u: clamp((v - s.a) / (s.b - s.a), 0, 1) };
}

// ================================================================== A-Rod vs. Teacherman: two hitters, two swings
// Hitter A swings with the knob cue: his hands and knob work down toward the ball and the barrel releases late.
// Hitter B loads into his rear hip and turns the barrel back into the plane early (a rearward arc), then rotates through.
// Both stride, shift their weight onto the front side, turn the hips and meet the same 95 mph fastball with the barrel.
// The legs and arms are solved (two-bone IK), so the feet stay planted and both hands stay on the bat.
// Hitter frame: a = toward the pitcher (his lead side), b = toward the plate (his chest), y up.
const HK = {
  A: { jersey: 0xf0f1f3, pants: 0xe0e2e6, cap: 0x1b2a4a, skin: 0xa77857, fore: 0xa77857, glove: 0x1b2a4a, strap: 0xdfe3ea, glow: 0x56d1ff },
  B: { jersey: 0x2b2f37, pants: 0x8b929c, cap: 0xb8322a, skin: 0x6e4a37, fore: 0x17191d, glove: 0x17191d, strap: 0xc4352d, glow: 0xffd84d },   // the hitter: the away kit
};
function dressHitter(who) {
  const k = HK[who], m = batter.mats;
  m.jersey.color.set(k.jersey); m.pants.color.set(k.pants); m.legR.color.set(k.pants); m.hipM.color.set(k.pants);
  m.cap.color.set(k.cap); m.skin.color.set(k.skin); m.foreM.color.set(k.fore);
  gloveM.color.set(k.glove); strapM.color.set(k.strap); armM.color.set(k.fore);
}
const HB = (R, a, y, b) => v3(R.x + b, y, R.z - a);
let SCB = 1;                                                        // the build's scale while a hitter is posed (the IK works in the rig's own units)
const BUILD = { big: { s: 1.07, t: 1.32 }, small: { s: 0.93, t: 0.84 } };   // height scale, and how thick the limbs and torso are
function applyBuild(w) {
  const b = BUILD[w] ?? { s: 1, t: 1 };
  batter.root.scale.setScalar(b.s);
  batter.root.traverse((o) => {
    if (!o.isMesh) return; const g = o.geometry;
    if (g.type !== "CapsuleGeometry" && !(g.type === "SphereGeometry" && g.parameters.radius > 0.5)) return;
    o.userData.s0 = o.userData.s0 ?? o.scale.clone(); o.scale.set(o.userData.s0.x * b.t, o.userData.s0.y, o.userData.s0.z * b.t);
  });
  batter.shL.position.x = 0.74 * (1 + 0.5 * (b.t - 1)); batter.shR.position.x = -batter.shL.position.x;
  batter.hipL.position.x = 0.34 * (1 + 0.6 * (b.t - 1)); batter.hipR.position.x = -batter.hipL.position.x;
}
function showHelmet(on) { batter.neck.traverse((o) => { if (o.isMesh && (o.geometry.type === "CylinderGeometry" || (o.geometry.type === "SphereGeometry" && o.geometry.parameters.radius > 0.37))) o.visible = on; }); }
const LEG_A = 1.42, LEG_B = 1.43, ANK = 0.18;
const _m1 = new THREE.Matrix4(), _m2 = new THREE.Matrix4(), _q = new THREE.Quaternion(), _qi = new THREE.Quaternion();
function footAnkle(f) {
  const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(f.heel ?? 0, f.yaw, 0, "YXZ"));
  return f.ball.clone().add(v3(0, ANK, -0.6).applyQuaternion(q));
}
function legIK(P, k, f) {                                           // a foot = { ball (world), yaw (toes), heel (lift, rad) }
  const hp = P[`hip${k}`], kn = P[`kn${k}`], ft = P[`ft${k}`];
  P.root.updateMatrixWorld(true);
  P.pelvis.getWorldQuaternion(_q); _qi.copy(_q).invert();
  const d = footAnkle(f).sub(hp.getWorldPosition(new THREE.Vector3())).applyQuaternion(_qi).divideScalar(SCB);
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
const ARM_A = 1.0, ARM_B = 0.92;
function armIK(P, k, target, pole) {                                // the wrist to `target`; the elbow points toward `pole` (world direction)
  const sh = P[`sh${k}`], el = P[`el${k}`];
  P.root.updateMatrixWorld(true);
  P.spine.getWorldQuaternion(_q); _qi.copy(_q).invert();
  const d = target.clone().sub(sh.getWorldPosition(new THREE.Vector3())).applyQuaternion(_qi).divideScalar(SCB);
  const pl = pole.clone().applyQuaternion(_qi);
  const L = clamp(d.length(), 0.35, ARM_A + ARM_B - 0.002);
  const th = Math.PI - Math.acos(clamp((ARM_A ** 2 + ARM_B ** 2 - L * L) / (2 * ARM_A * ARM_B), -1, 1));
  const e1 = v3(0, -ARM_A - ARM_B * Math.cos(th), ARM_B * Math.sin(th)).normalize(), e2 = v3(0, 0, 1).addScaledVector(e1, -e1.z).normalize(), e3 = e1.clone().cross(e2);
  const f1 = d.clone().normalize(), f2 = pl.clone().negate().addScaledVector(f1, pl.dot(f1)).normalize(), f3 = f1.clone().cross(f2);
  _m1.makeBasis(f1, f2, f3); _m2.makeBasis(e1, e2, e3).transpose();
  sh.quaternion.setFromRotationMatrix(_m1.multiply(_m2));
  el.rotation.set(-th, 0, 0);
  return d.length() - L;                                            // > 0: the target is out of reach by this much
}
// piecewise cubic Hermite through timed keys (Catmull-Rom tangents): smooth positions and speeds through every key
function herm(keys, k, f = (x) => x) {
  const n = keys.length; if (k <= keys[0][0]) return f(keys[0][1]).clone(); if (k >= keys[n - 1][0]) return f(keys[n - 1][1]).clone();
  let i = 0; while (k > keys[i + 1][0]) i++;
  const P = (j) => f(keys[clamp(j, 0, n - 1)][1]), T = (j) => keys[clamp(j, 0, n - 1)][0];
  const t0 = T(i), t1 = T(i + 1), h = t1 - t0, u = (k - t0) / h;
  const tan = (j) => { const a = clamp(j - 1, 0, n - 1), b = clamp(j + 1, 0, n - 1); return P(b).clone().sub(P(a)).multiplyScalar(1 / Math.max(1e-6, T(b) - T(a))); };
  const m0 = tan(i).multiplyScalar(h), m1 = tan(i + 1).multiplyScalar(h);
  const u2 = u * u, u3 = u2 * u;
  return P(i).clone().multiplyScalar(2 * u3 - 3 * u2 + 1).add(m0.multiplyScalar(u3 - 2 * u2 + u)).add(P(i + 1).clone().multiplyScalar(-2 * u3 + 3 * u2)).add(m1.multiplyScalar(u3 - u2));
}
const nv = (x, y, z) => v3(x, y, z).normalize();

// the pitch both of them hit: the 95 mph fastball, and where the barrel meets it
const PK = PI_.fb, CP = V(PK.contact), TCON = PK.t_contact;
const HM = GRIP0 + GSPAN / 2, D_SW = SWEET - HM;                    // the middle of the hands from the knob; the sweet spot from there
const DC = { A: nv(1, -0.13, -0.26), B: nv(1, -0.17, -0.34) };      // the bat at contact (B's barrel a touch further around: he pulls it)
const H0 = {}; for (const w of ["A", "B"]) {
  const dc = DC[w], n = v3(0, 0, 1).addScaledVector(dc, -dc.z).normalize();
  H0[w] = CP.clone().addScaledVector(n, BALL_R + 0.1).addScaledVector(dc, -D_SW);
}
// the body, keyed on k = time from contact (s): pelvis height (drop), weight shift toward the pitcher (shift), forward bend (lean),
// tilt away from the pitcher (side), hip turn (pelvisTwist) and the shoulders' turn against the hips (twist)
const ST = { drop: -0.32, shift: -0.08, lean: 16, side: 0, twist: -4, pelvisTwist: 0 };
const FOLLOW_ = { drop: -0.4, shift: 0.5, lean: 14, side: 4, twist: 22, pelvisTwist: 86 };
const FINISH_ = { drop: -0.28, shift: 0.55, lean: 8, side: 2, twist: 30, pelvisTwist: 94 };
const BODY = {   // shoulders = pelvisTwist + twist (positive: open toward the pitcher)
  A: [[-1.0, ST], [-0.32, { drop: -0.38, shift: -0.2, lean: 18, side: 1, twist: -10, pelvisTwist: -8 }], [-0.2, { drop: -0.42, shift: 0.06, lean: 19, side: 2, twist: -16, pelvisTwist: -2 }],
      [-0.08, { drop: -0.46, shift: 0.3, lean: 21, side: 6, twist: -36, pelvisTwist: 38 }], [0, { drop: -0.55, shift: 0.5, lean: 22, side: 16, twist: 0, pelvisTwist: 66 }], [0.12, FOLLOW_], [0.6, FINISH_]],
  B: [[-1.0, ST], [-0.32, { drop: -0.56, shift: -0.4, lean: 25, side: 4, twist: -6, pelvisTwist: -20 }], [-0.2, { drop: -0.54, shift: -0.04, lean: 24, side: 5, twist: -14, pelvisTwist: -10 }],
      [-0.12, { drop: -0.52, shift: 0.18, lean: 24, side: 8, twist: -40, pelvisTwist: 30 }], [-0.05, { drop: -0.56, shift: 0.38, lean: 23.5, side: 14, twist: -20, pelvisTwist: 58 }],
      [0, { drop: -0.58, shift: 0.48, lean: 23, side: 18, twist: 0, pelvisTwist: 72 }], [0.12, FOLLOW_], [0.6, FINISH_]],
};
// bat speed: from the end of the load on, the body moves on a smooth curve through its keys (no stop at each key), so the
// pelvis reaches its fastest turn just before the torso does: the sequence the video shows.
const BODY_SMOOTH = new Set(["B"]);
// the hands (middle of the grip), in the hitter frame [a, y, b], or "H0" = where they are at contact
const HANDS_K = {
  A: [[-1.0, [-0.6, 4.62, 0.62]], [-0.32, [-0.85, 4.75, 0.55]], [-0.2, [-0.85, 4.7, 0.6]], [-0.08, "drive"], [0, "H0"], [0.12, "fol"], [0.6, [0.05, 5.35, -0.55]]],
  B: [[-1.0, [-0.6, 4.62, 0.62]], [-0.32, [-0.95, 4.6, 0.52]], [-0.2, [-0.9, 4.52, 0.58]], [-0.12, [-0.6, 3.9, 0.72]], [-0.05, "round"], [0, "H0"], [0.12, "fol"], [0.6, [0.05, 5.35, -0.55]]],
};
// the bat (from the hands toward the barrel), world directions
const BAT_K = {
  A: [[-1.0, nv(-0.12, 0.88, 0.46)], [-0.32, nv(-0.05, 0.92, 0.38)], [-0.2, nv(-0.04, 0.93, 0.36)], [-0.08, "knob"], [-0.045, nv(-0.1, -0.25, 0.96)], [-0.02, nv(0.62, -0.32, 0.72)], [0, "dc"],
      [0.08, nv(0.25, 0.12, -1)], [0.3, nv(-0.7, 0.5, -0.2)], [0.45, nv(-0.85, 0.1, 0.5)], [0.7, nv(-0.35, -0.5, 0.8)]],
  B: [[-1.0, nv(-0.12, 0.88, 0.46)], [-0.32, nv(-0.05, 0.93, 0.36)], [-0.2, nv(-0.1, 0.85, 0.52)], [-0.14, nv(-0.3, 0.45, 0.84)], [-0.1, nv(-0.2, -0.12, 0.97)], [-0.05, nv(0.45, -0.3, 0.84)],
      [-0.02, nv(0.85, -0.27, 0.45)], [0, "dc"], [0.08, nv(0.25, 0.12, -1)], [0.3, nv(-0.7, 0.5, -0.2)], [0.45, nv(-0.85, 0.1, 0.5)], [0.7, nv(-0.35, -0.5, 0.8)]],
};
// the elbows: which way each points (world)
const POLE_K = {
  L: [[-1.0, nv(0.3, -1, -0.6)], [-0.2, nv(0.2, -1, -0.5)], [0, nv(0.5, -1, 0.1)], [0.15, nv(0.4, -0.6, 0.6)], [0.6, nv(-0.2, -0.4, -1)]],
  R: [[-1.0, nv(-0.3, -0.3, 1)], [-0.2, nv(-0.3, -0.5, 1)], [-0.1, nv(0, -1, 0.5)], [0, nv(0.3, -1, 0.2)], [0.15, nv(0.4, -1, -0.4)], [0.6, nv(0.3, 0.2, -1)]],
};
const ROOT0 = v3(-3.15, 0, 0.15), ROOT = { A: ROOT0.clone(), B: ROOT0.clone() };
function bodyAt(w, k) {                                             // body numbers at k (eased between keys)
  const K = BODY[w]; if (k <= K[0][0]) return { ...K[0][1] };
  if (BODY_SMOOTH.has(w) && k > K[1][0]) {
    const out = {}; for (const key of Object.keys(K[1][1])) out[key] = herm(K.slice(1).map(([kk, q]) => [kk, v3(q[key] ?? 0, 0, 0)]), k).x;
    return out;
  }
  for (let i = 1; i < K.length; i++) if (k <= K[i][0]) return mixPose(K[i - 1][1], K[i][1], (i <= 2 ? easeIO : smooth)((k - K[i - 1][0]) / (K[i][0] - K[i - 1][0])));
  return { ...K.at(-1)[1] };
}
const FOLOFF = [0.25, 0.55, -1.0];                                    // the hands 0.12 s after contact, from where they were at contact (hitter frame)
function batAt(w, k, t = 0) {                                       // { H: the middle of the hands, dir: the bat } at k (pure: no scene changes)
  const R = ROOT[w], h0 = H0[w], sc = BUILD[w]?.s ?? 1;
  const loc = (p) => HB(R, p[0] * sc, p[1] * sc, p[2] * sc);
  const plant = loc(HANDS_K[w].find((x) => x[0] === -0.2)[1]);
  const special = {
    H0: h0, fol: h0.clone().add(HB(v3(0, 0, 0), ...FOLOFF)),
    drive: plant.clone().lerp(h0, 0.58),                            // A: the hands go straight from the launch position toward contact
    round: loc([-0.6, 3.9, 0.72]).lerp(h0, 0.55).add(HB(v3(0, 0, 0), 0, -0.05, 0.22)),   // B: around the body, not straight
  };
  const HKs = HANDS_K[w].map(([kk, p]) => [kk, typeof p === "string" ? special[p] : loc(p)]);
  let H = herm(HKs, k);
  const knobDir = special.drive.clone().sub(CP).normalize();       // A, k = -0.08: the knob points straight at the ball
  const BKs = BAT_K[w].map(([kk, d]) => [kk, d === "dc" ? DC[w] : d === "knob" ? knobDir : d]);
  let dir = herm(BKs, k).normalize();
  if (k < -0.9) { const wob = Math.sin(t * 2.6) * 0.035; H.add(v3(0, wob * 0.5, wob * 0.6)); dir.add(v3(wob * 0.6, 0, wob)).normalize(); }   // the waggle before the load
  return { H, dir };
}
const knobAt = (w, k, t) => { const { H, dir } = batAt(w, k, t); return H.addScaledVector(dir, -HM); };
const tipAt = (w, k, t) => { const { H, dir } = batAt(w, k, t); return H.addScaledVector(dir, BAT_LEN - HM); };
const sweetAt = (w, k, t) => { const { H, dir } = batAt(w, k, t); return H.addScaledVector(dir, D_SW); };
// swing styles: how high the front foot lifts (ft), when the lift starts (k), the stride, how he slides on afterwards, and how far off the sweet spot he meets the ball
const STY0 = { lift: 0.32, t0: -0.75, lead0: 0.85, lead1: 2.0, slide: 0, step: 0, miss: 0 };
const STY = {};
function feetAt(w, k) {                                             // the feet: the stride lands at k = -0.22; the rear foot pivots and its heel comes up
  const R = ROOT[w], sc = BUILD[w]?.s ?? 1, st = { ...STY0, ...(STY[w] ?? {}) };
  if (!BUILD[w] && w !== "B") st.lift = 0.2;                        // the older A swing keeps its low lift
  const ph = clamp((k - st.t0) / (-0.22 - st.t0), 0, 1), u = smooth(ph), lift = Math.sin(Math.PI * ph) * st.lift * sc, sl = st.slide * smooth((k - 0.02) / 0.35);
  const lead = { ball: HB(R, (lerp(st.lead0, st.lead1, u) + sl) * sc, lift, 0.02 * u), yaw: Math.PI / 2 + lerp(-0.12, 0.38, u) + 0.3 * smooth((k + 0.05) / 0.4), heel: 0.12 * Math.sin(Math.PI * ph) };
  const p = smooth((k + 0.12) / 0.5), stp = st.step * smooth((k - 0.1) / 0.42);
  const rear = { ball: HB(R, (-1.25 + 0.12 * smooth((k - 0.05) / 0.5) + stp) * sc, (st.step ? 0.6 * Math.sin(Math.PI * clamp((k - 0.1) / 0.5, 0, 1)) : 0) * sc, 0.05 * p), yaw: Math.PI / 2 + 1.0 * p, heel: 0.75 * smooth((k + 0.1) / 0.3) - 0.15 * smooth((k - 0.2) / 0.4) };
  return { lead, rear };
}
const HIT = { who: "A", k: 0 };
let REACH_ERR = 0;
function poseHitter(w, k, t, look) {                                // pose the hitter and the bat at k; look = where his eyes go (world)
  const R = ROOT[w], b = bodyAt(w, k);
  applyBuild(w); SCB = BUILD[w]?.s ?? 1;
  batter.root.position.copy(R); batter.root.rotation.y = Math.PI / 2;
  applyPose(batter, { drop: b.drop, lean: b.lean, side: b.side, twist: b.twist, pelvisTwist: b.pelvisTwist });
  batter.pelvis.position.x = b.shift;
  batter.root.updateMatrixWorld(true);
  const f = feetAt(w, k); legIK(batter, "R", f.rear); legIK(batter, "L", f.lead);
  const { H, dir } = batAt(w, k, t); setGrip(0, 0);
  BAT.quaternion.copy(batFrame(dir)); BAT.position.copy(H).addScaledVector(dir, -HM); BAT.updateMatrixWorld(true);
  const wl = HL.root.getWorldPosition(new THREE.Vector3()), wr = HR.root.getWorldPosition(new THREE.Vector3());
  REACH_ERR = [armIK(batter, "L", wl, herm(POLE_K.L, k).normalize()), armIK(batter, "R", wr, herm(POLE_K.R, k).normalize())];
  if (look) {                                                       // the head turns to the ball
    batter.root.updateMatrixWorld(true); batter.spine.getWorldQuaternion(_q); _qi.copy(_q).invert();
    const d = look.clone().sub(batter.neck.getWorldPosition(new THREE.Vector3())).applyQuaternion(_qi);
    batter.neck.rotation.set(clamp(Math.atan2(-d.y, Math.hypot(d.x, d.z)), -0.6, 0.7), clamp(Math.atan2(d.x, d.z), -1.75, 1.75), 0, "YXZ");
  }
  HIT.who = w; HIT.k = k; SCB = 1;
}
// place each hitter so his lead arm reaches the contact point without straining (about 94% of its length)
for (const w of ["A", "B"]) for (let it = 0; it < 8; it++) {
  poseHitter(w, 0, 0, null); const S = wpos(batter.shL), d = H0[w].clone().sub(S); d.y = 0;
  const full = H0[w].clone().sub(S).length(), want = 1.76;
  if (Math.abs(full - want) < 0.005) break;
  ROOT[w].addScaledVector(d.normalize(), (full - want) * 0.9);
}

// ================================================================== power: two builds, one pitch, two swings
// "big" (charcoal, red helmet, orange graphics): a larger, thicker hitter whose shoulders turn almost with his hips (little separation).
// "small" (white, navy helmet, cyan graphics): a smaller, leaner hitter whose hips open first and whose torso follows (the sequence).
// Both meet the same pitch at the same spot. The swings are illustrations of a coordinated and a less coordinated sequence; the exit speeds are not shown.
HK.big = { ...HK.B, glow: 0xff6a3d }; HK.small = { ...HK.A };
DC.big = DC.small = DC.B;
for (const w of ["big", "small"]) {
  const dc = DC[w], n = v3(0, 0, 1).addScaledVector(dc, -dc.z).normalize();
  H0[w] = CP.clone().addScaledVector(n, BALL_R + 0.1).addScaledVector(dc, -D_SW);
  HANDS_K[w] = HANDS_K.B; BAT_K[w] = BAT_K.B; BODY_SMOOTH.add(w); ROOT[w] = ROOT0.clone();
}
BODY.small = BODY.B;
BODY.big = BODY.B.map(([kk, q]) => [kk, { ...q, twist: q.twist < -5 ? q.twist * 0.3 : q.twist }]);
for (const w of ["big", "small"]) for (let it = 0; it < 8; it++) {
  poseHitter(w, 0, 0, null); const S = wpos(batter.shL), d = H0[w].clone().sub(S); d.y = 0;
  const full = H0[w].clone().sub(S).length(), want = 1.76 * BUILD[w].s;
  if (Math.abs(full - want) < 0.005) break;
  ROOT[w].addScaledVector(d.normalize(), (full - want) * 0.9);
}

// ================================================================== copying a swing: three professional styles, and a young hitter's copy of the kick
// kick = a big leg kick; quiet = a short stride and a still setup; hands = busy hands set high; young = the same big kick copied by a young hitter
// (lunging, off balance, on the end of the bat, stumbling through); okay = the same young hitter with a swing that fits him (a modest lift, balanced).
Object.assign(BUILD, { kick: { s: 1.05, t: 1.12 }, quiet: { s: 0.98, t: 0.98 }, hands: { s: 1.02, t: 1.0 }, young: { s: 0.8, t: 0.82 }, okay: { s: 0.8, t: 0.82 } });
Object.assign(STY, {
  kick: { lift: 1.5, t0: -1.0, lead1: 2.15 }, quiet: { lift: 0.1, t0: -0.5, lead1: 1.5 }, hands: { lift: 0.4, lead1: 1.95 },
  okay: { lift: 0.45, lead1: 1.9 }, young: { lift: 1.55, t0: -1.0, lead1: 2.9, slide: 0.9, step: 1.7, miss: 0.42 },
});
HK.kick = { ...HK.B, glow: 0xff6a3d };
HK.quiet = { ...HK.A };
HK.hands = { jersey: 0x2f6b4a, pants: 0xd9dfd6, cap: 0xd9a92c, skin: 0x8a5d44, fore: 0x8a5d44, glove: 0xd9a92c, strap: 0xd9a92c, glow: 0x3dd68c };
HK.young = { jersey: 0x2f7fd6, pants: 0xe8eaee, cap: 0xf4f6f8, skin: 0xb98562, fore: 0xb98562, glove: 0xf4f6f8, strap: 0x2f7fd6, glow: 0xffd84d }; HK.okay = HK.young;
const LATE = (tbl, k0) => tbl.filter(([kk]) => kk > k0);
BODY.kick = [BODY.B[0], [-0.7, { drop: -0.46, shift: -0.38, lean: 22, side: 2, twist: -4, pelvisTwist: -12 }], ...BODY.B.slice(1)];
BODY.quiet = [BODY.B[0], [-0.32, { drop: -0.4, shift: -0.12, lean: 21, side: 2, twist: -4, pelvisTwist: -10 }], [-0.2, { drop: -0.42, shift: 0.04, lean: 21, side: 3, twist: -10, pelvisTwist: -6 }], ...BODY.B.slice(3)];
BODY.hands = BODY.B; BODY.okay = BODY.B;
BODY.young = [[-1.0, ST], [-0.6, { drop: -0.62, shift: -0.55, lean: 28, side: 8, twist: -8, pelvisTwist: -26 }], [-0.3, { drop: -0.7, shift: -0.2, lean: 30, side: 10, twist: -14, pelvisTwist: -20 }],
  [-0.12, { drop: -0.72, shift: 0.55, lean: 34, side: 16, twist: -34, pelvisTwist: 24 }], [-0.05, { drop: -0.82, shift: 0.88, lean: 38, side: 22, twist: -16, pelvisTwist: 50 }],
  [0, { drop: -0.9, shift: 1.08, lean: 40, side: 26, twist: 4, pelvisTwist: 62 }], [0.12, { drop: -0.9, shift: 1.34, lean: 44, side: 22, twist: 16, pelvisTwist: 76 }], [0.6, { drop: -0.7, shift: 1.6, lean: 36, side: 12, twist: 24, pelvisTwist: 84 }]];
HANDS_K.quiet = [[-1.0, [-0.62, 4.3, 0.64]], [-0.32, [-0.62, 4.3, 0.64]], [-0.2, [-0.62, 4.3, 0.64]], ...LATE(HANDS_K.B, -0.2)];
HANDS_K.hands = [[-1.0, [-0.95, 5.55, 0.5]], [-0.62, [-0.7, 4.5, 0.7]], [-0.4, [-1.05, 5.1, 0.48]], [-0.2, [-0.95, 4.7, 0.55]], ...LATE(HANDS_K.B, -0.2)];
HANDS_K.young = [[-1.0, [-0.9, 5.4, 0.5]], [-0.5, [-1.2, 5.6, 0.4]], [-0.32, [-1.1, 5.0, 0.45]], [-0.2, [-0.95, 4.5, 0.55]], ...LATE(HANDS_K.B, -0.2)];
HANDS_K.kick = HANDS_K.okay = HANDS_K.B;
BAT_K.quiet = [[-1.0, nv(-0.02, 0.98, 0.2)], [-0.32, nv(-0.02, 0.98, 0.2)], [-0.2, nv(-0.06, 0.9, 0.4)], ...LATE(BAT_K.B, -0.2)];
BAT_K.hands = [[-1.0, nv(-0.5, 0.78, 0.38)], [-0.62, nv(-0.1, 0.9, 0.42)], [-0.4, nv(-0.45, 0.82, 0.35)], [-0.2, nv(-0.1, 0.85, 0.52)], ...LATE(BAT_K.B, -0.2)];
BAT_K.young = BAT_K.hands; BAT_K.kick = BAT_K.okay = BAT_K.B;
for (const w of ["kick", "quiet", "hands", "young", "okay"]) {
  DC[w] = DC.B; const dc = DC[w], n = v3(0, 0, 1).addScaledVector(dc, -dc.z).normalize();
  H0[w] = CP.clone().addScaledVector(n, BALL_R + 0.1).addScaledVector(dc, -(D_SW + (STY[w]?.miss ?? 0)));
  ROOT[w] = ROOT0.clone(); BODY_SMOOTH.add(w);
}
for (const w of ["kick", "quiet", "hands", "young", "okay"]) for (let it = 0; it < 8; it++) {
  poseHitter(w, 0, 0, null); const S = wpos(batter.shL), d = H0[w].clone().sub(S); d.y = 0;
  const full = H0[w].clone().sub(S).length(), want = 1.76 * BUILD[w].s;
  if (Math.abs(full - want) < 0.005) break;
  ROOT[w].addScaledVector(d.normalize(), (full - want) * 0.9);
}

// ------------------------------------------------------------------ the graphics: path lines, the intent arrow, the hip ring, highlights
function makeTrail(color, r) {
  const core = new THREE.Mesh(new THREE.BufferGeometry(), glowM(color, 0.95)), halo = new THREE.Mesh(new THREE.BufferGeometry(), glowM(color, 0.22));
  halo.material.blending = THREE.AdditiveBlending; core.renderOrder = 7; halo.renderOrder = 6; core.visible = halo.visible = false; scene.add(core, halo);
  return { core, halo, set(pts, op = 1, col = null) {
    const vis = pts.length >= 2 && op > 0.01; core.visible = halo.visible = vis; if (!vis) return;
    if (col !== null) { core.material.color.set(col); halo.material.color.set(col); }
    const curve = new THREE.CatmullRomCurve3(pts), n = Math.max(12, pts.length * 3);
    core.geometry.dispose(); halo.geometry.dispose();
    core.geometry = new THREE.TubeGeometry(curve, n, r, 8, false); halo.geometry = new THREE.TubeGeometry(curve, n, r * 2.8, 8, false);
    core.material.opacity = 0.95 * op; halo.material.opacity = 0.22 * op; } };
}
const TR_KNOB = makeTrail(0x56d1ff, 0.028), TR_TIP = makeTrail(0xff6a3d, 0.034), TR_KNOB2 = makeTrail(0xff6a3d, 0.028);
const TR_EXP = [makeTrail(0x56d1ff, 0.05), makeTrail(0xffd84d, 0.05)];                       // the pitch he expects (and the one that comes)
const BB2 = BB.clone(); scene.add(BB2); BB2.visible = false;                                   // a second ball: the changeup beside the fastball
const EYES = new THREE.Group(); EYES.visible = false; batter.neck.add(EYES);                  // two small eyes, used only in the close-ups of his face
const EYE_C = [v3(-0.125, 0.14, 0.3), v3(0.125, 0.14, 0.3)], PUPILS = [];
for (const c of EYE_C) {
  const e = new THREE.Mesh(new THREE.SphereGeometry(0.075, 16, 12), new THREE.MeshStandardMaterial({ color: 0xf4f6f8, roughness: 0.35 })); e.position.copy(c); EYES.add(e);
  const pu = new THREE.Mesh(new THREE.SphereGeometry(0.03, 14, 10), new THREE.MeshStandardMaterial({ color: 0x0b0e13, roughness: 0.2 })); pu.position.copy(c).add(v3(0, 0, 0.065)); EYES.add(pu); PUPILS.push(pu);
}
function lookEyes(look) {                                                                       // the pupils slide toward what he is looking at
  batter.neck.updateWorldMatrix(true, false);
  EYE_C.forEach((c, i) => { const d = batter.neck.worldToLocal(look.clone()).sub(c).normalize(); d.z = Math.max(0.35, d.z); d.normalize(); PUPILS[i].position.copy(c).addScaledVector(d, 0.068); });
}
function makeArrow(color) {                                         // a dashed straight line with a head
  const g = new THREE.Group(), dashes = [];
  for (let i = 0; i < 24; i++) { const m = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 1, 10), glowM(color, 0.95)); m.renderOrder = 8; g.add(m); dashes.push(m); }
  const head = new THREE.Mesh(new THREE.ConeGeometry(0.1, 0.26, 18), glowM(color, 0.95)); head.renderOrder = 8; g.add(head);
  g.visible = false; scene.add(g);
  return { g, set(a, b, prog, op = 1, col = null) {
    g.visible = op > 0.01 && prog > 0.001; if (!g.visible) return;
    const d = b.clone().sub(a), L = d.length() * prog, u = d.clone().normalize(), q = new THREE.Quaternion().setFromUnitVectors(v3(0, 1, 0), u);
    const DL = 0.16, GAP = 0.12;
    dashes.forEach((m, i) => { const s0 = i * (DL + GAP), s1 = Math.min(s0 + DL, L - 0.2); m.visible = s1 > s0; if (!m.visible) return;
      m.position.copy(a).addScaledVector(u, (s0 + s1) / 2); m.scale.set(1, s1 - s0, 1); m.quaternion.copy(q); m.material.opacity = 0.95 * op; if (col !== null) m.material.color.set(col); });
    head.position.copy(a).addScaledVector(u, Math.max(0.13, L - 0.13)); head.quaternion.copy(q); head.material.opacity = 0.95 * op; if (col !== null) head.material.color.set(col); } };
}
const AR_INTENT = makeArrow(0x56d1ff), AR_STRAIGHT = makeArrow(0xf4f6f8);
const ringM = (c, o, r, tube) => { const m = new THREE.Mesh(new THREE.TorusGeometry(r, tube, 10, 96), glowM(c, o)); m.renderOrder = 7; m.visible = false; return m; };
const HIPRING = ringM(0xff6a3d, 0.95, 0.5, 0.025), HIPHALO = ringM(0xff6a3d, 0.2, 0.5, 0.075); HIPHALO.material.blending = THREE.AdditiveBlending; scene.add(HIPRING, HIPHALO);
// the hips' turn: an arc arrow round the pelvis (it turns with him)
const ROT = new THREE.Group(); batter.pelvis.add(ROT); ROT.visible = false;
const ROT_ARC = new THREE.Mesh(new THREE.TorusGeometry(1.05, 0.03, 8, 64, Math.PI * 0.9), glowM(0x56d1ff, 0.9)); ROT_ARC.rotation.x = Math.PI / 2; ROT.add(ROT_ARC);
const ROT_HEAD = new THREE.Mesh(new THREE.ConeGeometry(0.1, 0.26, 16), glowM(0x56d1ff, 0.9)); ROT.add(ROT_HEAD);
{ const a = Math.PI * 0.9; ROT_HEAD.position.set(Math.cos(a) * 1.05, 0, Math.sin(a) * 1.05); ROT_HEAD.rotation.set(0, 0, 0); ROT_HEAD.quaternion.setFromUnitVectors(v3(0, 1, 0), v3(-Math.sin(a), 0, Math.cos(a))); }
ROT.rotation.y = -Math.PI * 0.2;
// glow on the barrel and at the knob
const barrelHL = (() => { const out = []; for (let i = 0; i <= 40; i++) { const y = lerp(1.55, BAT_LEN, i / 40); out.push(new THREE.Vector2(batRadius(y) + 0.03, y)); }
  const m = new THREE.Mesh(new THREE.LatheGeometry(out, 32), glowM(0xff6a3d, 0)); m.material.blending = THREE.AdditiveBlending; m.renderOrder = 7; BAT.add(m); return m; })();
const KNOBHL = new THREE.Sprite(new THREE.SpriteMaterial({ map: dotTex, color: 0x56d1ff, transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending, opacity: 0 })); KNOBHL.position.y = 0.02; KNOBHL.scale.setScalar(0.5); BAT.add(KNOBHL);
const BGLOW = new THREE.Sprite(new THREE.SpriteMaterial({ map: dotTex, color: 0xfff4d6, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: false, opacity: 0 }));
BGLOW.scale.setScalar(0.035); BGLOW.renderOrder = 9; scene.add(BGLOW);
const BGLOW2 = BGLOW.clone(); BGLOW2.material = BGLOW.material.clone(); scene.add(BGLOW2);          // the glow on the second ball                        // keeps a far ball visible: a glow of constant size on screen
const winOp = (v, w, fin = 0.2, fout = 0.25) => (!w ? 0 : smooth((v - w[0]) / fin) * (1 - smooth((v - (w[1] ?? 1e9)) / fout)));
const GHOST_C = { A: 0x56d1ff, B: 0xffd84d, big: 0xff6a3d, small: 0x56d1ff, kick: 0xff6a3d, quiet: 0x56d1ff, hands: 0x3dd68c, young: 0xffd84d, okay: 0xffd84d };

// ------------------------------------------------------------------ the scene for one shot (or one pane) at play time t, video time v
// s.hit = { who, rel (release time), hit (batted ball id) }; s.who alone = that hitter in his stance
function setSceneH(t, s, v) {
  setLab(!!s.lab);
  for (const [k, p] of Object.entries(HD)) { const [x, z] = homeD[k]; p.root.position.set(x, 0, z); p.root.rotation.y = Math.atan2(-x, -z); applyPose(p, READY); }
  B1F.root.position.set(56, 0, -78); B1F.root.rotation.y = Math.atan2(-56, 78); applyPose(B1F, READY);
  U1.root.position.set(70, 0, -56); U1.root.rotation.y = Math.atan2(-70, 56); applyPose(U1, { drop: -0.7, lean: 26, nod: -6, hipL: [40, 16], hipR: [40, 16], knL: 48, knR: 48, shL: [30, 12, 0], elL: 50, shR: [30, 12, 0], elR: 50 });
  BOARD.visible = false; COACH.root.visible = false; R.root.visible = false; HAND.root.visible = false; RING_OP = 0; ZONE.visible = false; MARK.visible = MARKR.visible = false; CHASE.visible = false;
  ump.root.position.set(0.5, 0, 6.0); ump.root.rotation.y = Math.PI; applyPose(ump, U_SET); ump.root.visible = !s.noump;
  C.root.position.set(0.15, 0, 3.0); C.root.rotation.y = Math.PI; applyPose(C, C_SET);
  const hs = s.hit, w = hs?.who ?? s.who ?? "A", pid = hs?.pitch ?? "fb", PX = PI_[pid], cnt = !!hs?.hit && pid === "fb";   // the swing is timed to the fastball; any other pitch has no contact
  let k = hs ? t - hs.rel - TCON - (hs.sk ?? 0) : -1.5; if (hs?.take !== undefined) k = Math.min(k, hs.take);                    // a taken pitch: he holds at his stride
  let pq = P_LOOK, ppos = RUB.clone().add(v3(0, 0, 0.1)), pyaw = -Math.PI / 2;
  if (hs) { posePitcher(t - hs.rel); pitcher.root.visible = true; }
  else { pitcher.root.position.copy(ppos); pitcher.root.rotation.y = pyaw; applyPose(pitcher, pq); }
  showHelmet(true); BAT.visible = true; for (const g of [GL, GRt]) g.visible = true;
  dressHitter(w); FORE = false; batter.elL.visible = batter.elR.visible = true;
  for (const g of [GL, GRt]) g.visible = true; batter.handL.children[0].visible = batter.handR.children[0].visible = false;
  // the ball (where it is decides where he looks)
  BB.visible = false; BB.scale.set(1, 1, 1); STREAK.forEach((m) => (m.visible = false)); FLASH.material.opacity = 0; BGLOW.material.opacity = 0;
  let look = CP.clone();
  if (hs) {
    const kr = t - hs.rel; BB.visible = true;
    if (kr < 0) BB.position.copy(ballInFingers());
    else if (!cnt) { BB.position.copy(kr < PX.flight ? pathAt(PX.path, kr) : MITT(v3(0, 0.02, -0.42))); if (kr < 0.012) BB.position.lerp(ballInFingers(), 1 - kr / 0.012); }
    else if (kr < TCON) { BB.position.copy(pathAt(PK.path, kr)); if (kr < 0.012) BB.position.lerp(ballInFingers(), 1 - kr / 0.012); }
    else { const kk = kr - TCON; BB.position.copy(pathAt(HITS[hs.hit].path, kk));
      if (kk < 0.07) { FLASH.position.copy(CP); FLASH.scale.setScalar(0.9 + kk * 10); FLASH.material.opacity = 0.95 * (1 - kk / 0.07); } }
    if (s.streak && kr > 0) { const hitp = cnt && kr >= TCON, path = hitp ? HITS[hs.hit].path : PX.path, kk = hitp ? kr - TCON : kr;
      STREAK.forEach((m, i) => { const d = (i + 1) * 0.008; if (kk - d > 0 && (hitp || kk - d < PX.flight)) { m.visible = true; m.position.copy(pathAt(path, kk - d)); } }); }
    BB.quaternion.setFromAxisAngle(V(PX.spin), PX.rpm / 60 * 2 * Math.PI * Math.min(Math.max(0, kr), PX.flight));
    const sq = cnt ? Math.exp(-(((kr - TCON) / 0.0016) ** 2)) : 0;                  // the ball squashes against the bat for a few thousandths of a second
    BB.scale.set(1 + 0.13 * sq, 1 + 0.13 * sq, 1 - 0.4 * sq); if (sq > 0.04) BB.quaternion.set(0, 0, 0, 1);
    if (kr > -0.6 && kr < (cnt ? TCON + 0.02 : PX.flight + 0.2)) look = BB.position.clone();
    BGLOW.position.copy(BB.position); BGLOW.material.opacity = s.glow ? 0.9 : s.bglow ? 0.9 * smooth((kr - TCON - 0.05) / 0.2) : 0;
    BGLOW.scale.setScalar(s.bgs ?? 0.035); BGLOW.material.color.set(s.gcol ?? 0xfff4d6); BGLOW.material.blending = s.gnorm ? THREE.NormalBlending : THREE.AdditiveBlending;
    // a second ball (the changeup beside the fastball): its own path from the same release
    if (s.ball2) { const P2 = PI_[s.ball2.pitch], k2 = t - hs.rel; BB2.visible = true; BB2.scale.set(1, 1, 1);
      BB2.position.copy(k2 < 0 ? ballInFingers() : pathAt(P2.path, Math.min(k2, P2.flight))); if (k2 >= 0 && k2 < 0.012) BB2.position.lerp(ballInFingers(), 1 - k2 / 0.012);
      BB2.quaternion.setFromAxisAngle(V(P2.spin), P2.rpm / 60 * 2 * Math.PI * Math.min(Math.max(0, k2), P2.flight));
      BGLOW2.position.copy(BB2.position); BGLOW2.material.opacity = s.glow ? 0.9 : 0; BGLOW2.scale.setScalar(s.bgs ?? 0.035); BGLOW2.material.color.set(s.gcol2 ?? 0xff6a3d); BGLOW2.material.blending = s.gnorm ? THREE.NormalBlending : THREE.AdditiveBlending; }
  }
  if (s.noball) { BB.visible = false; STREAK.forEach((m) => (m.visible = false)); FLASH.material.opacity = 0; BGLOW.material.opacity = 0; look = s.look ? A(s.look) : CP.clone(); }
  // the bat path behind the swing: translucent copies of the bat a few hundredths of a second back
  GHOSTS.forEach((m) => (m.visible = false));
  if (s.ghost && hs) for (let i = 0; i < GHOSTS.length; i++) {
    const kg = k - (i + 1) * s.ghost; if (kg < -0.12 || kg > 0.1) continue;
    const { H, dir } = batAt(w, kg, t); GHOSTS[i].quaternion.copy(batFrame(dir)); GHOSTS[i].position.copy(H).addScaledVector(dir, -HM); GHOSTS[i].material.color.set(GHOST_C[w]); GHOSTS[i].visible = true;
  }
  poseHitter(w, k, t, look);
  if (hs && !cnt) { poseCRecv(pid, t - hs.rel - PX.flight, CPOSE[hs.cbase ?? "mid"], { from: 0.55, depth: 0.28 }); if (t - hs.rel >= PX.flight) BB.position.copy(MITT(v3(0, 0.02, -0.42))); }   // the catcher takes it
  EYES.visible = !!s.eyes; if (s.eyes) lookEyes(look);
  (s.expect ?? []).forEach((e, i) => {                                                              // the path he expects: a glowing line from the release to the plate
    const P = PI_[e.pitch], n = 18, pts = [], reach = e.upto ?? 1;
    for (let j = 0; j <= n; j++) pts.push(pathAt(P.path, P.front * reach * j / n));
    TR_EXP[i].set(pts, winOp(v, e.v, e.fin ?? 0.15, e.fout ?? 0.2), e.c ?? null);
  });
  // path lines: where the knob / the end of the bat have been since the launch
  const trail = (T, f, spec, col) => {
    if (!spec || !hs) { T.set([]); return; }
    const k0 = spec.from ?? -0.3, k1 = spec.ahead ? (spec.to ?? 0) : Math.min(k, spec.to ?? 0.04), pts = [];
    for (let kk = k0; kk <= k1 + 1e-6; kk += 0.006) pts.push(f(w, kk, t));
    if (pts.length && k1 > k0) pts.push(f(w, k1, t));
    T.set(pts, winOp(v, spec.v ?? [-1, 1e9]), col);
  };
  trail(TR_KNOB, knobAt, s.knob, s.knob?.c ?? HK[w].glow); trail(TR_TIP, tipAt, s.tip, s.tip?.c ?? HK[w].glow); trail(TR_KNOB2, knobAt, s.knob2, s.knob2?.c ?? 0xf4f6f8);
  // the cue: a straight dashed line from the knob to the ball
  const arrow = (ar, spec) => {
    if (!spec) { ar.set(v3(), v3(), 0, 0); return; }
    const kf = spec.k ?? k, a = knobAt(w, kf, t), b = spec.toBall ? BB.position.clone() : CP.clone();
    ar.set(a, b, smooth((v - spec.v[0]) / (spec.dur ?? 0.45)), winOp(v, spec.v, 0.05), spec.c ?? null);
  };
  arrow(AR_INTENT, s.intent); arrow(AR_STRAIGHT, s.straight);
  // the rear hip, the rear leg, the hands, the barrel
  const hl = s.hl ?? {}, hipOp = winOp(v, hl.hip), legOp = winOp(v, hl.leg), handOp = winOp(v, hl.hands), barOp = winOp(v, hl.barrel), knobOp = winOp(v, hl.knob);
  const glowC = new THREE.Color(hl.c ?? HK[w].glow);
  HIPRING.visible = HIPHALO.visible = hipOp > 0.01;
  if (HIPRING.visible) { const p = wpos(batter.hipR); for (const m of [HIPRING, HIPHALO]) { m.position.copy(p); m.rotation.set(Math.PI / 2, 0, 0); m.material.color.copy(glowC); }
    const pulse = 1 + 0.06 * Math.sin(v * 9); HIPRING.scale.setScalar(pulse); HIPHALO.scale.setScalar(pulse); HIPRING.material.opacity = 0.95 * hipOp; HIPHALO.material.opacity = 0.22 * hipOp; }
  const m = batter.mats;
  m.legR.emissive.copy(glowC); m.legR.emissiveIntensity = 0.55 * legOp;
  m.hipM.emissive.copy(glowC); m.hipM.emissiveIntensity = 0.5 * hipOp;
  gloveM.emissive.copy(glowC); gloveM.emissiveIntensity = 0.7 * handOp;
  barrelHL.material.color.copy(glowC); barrelHL.material.opacity = 0.45 * barOp;
  KNOBHL.material.color.copy(glowC); KNOBHL.material.opacity = 0.9 * Math.max(knobOp, handOp * 0.6);
  ROT.visible = !!s.rot && winOp(v, s.rot) > 0.01;
  if (ROT.visible) { const o = winOp(v, s.rot); ROT_ARC.material.opacity = ROT_HEAD.material.opacity = 0.9 * o; ROT_ARC.material.color.copy(glowC); ROT_HEAD.material.color.copy(glowC); }
  setXray(s, v, k); const g_ = setGRF(s, v, k, w); setBalance(s, v, w, k); SUP = g_.rear / Math.max(1e-3, g_.rear + g_.lead); KNOW = k;
  BAT.visible = true; batter.root.visible = true;
  if (s.cam === "hpov") { batter.root.visible = false; BAT.visible = false; }          // the camera is in his head: no body in the way
}
let SUP = 0.5, KNOW = -1;
const PINH = { knob: () => batPt(0.02), hands: () => batPt(HM), hipR: () => wpos(batter.hipR), knee: () => wpos(batter.knR), barrel: () => batPt(2.4), tip: () => batPt(BAT_LEN),
  ball: () => BB.position.clone(), head: () => headTop(batter), pelvis: () => wpos(batter.pelvis), contact: () => CP.clone(),
  chest: () => wpos(batter.neck).add(v3(0, -0.5, 0)), footR: () => wpos(batter.ftR).add(v3(0, 0.6, 0)), footL: () => wpos(batter.ftL).add(v3(0, 0.6, 0)), elbow: () => wpos(batter.elR) };
// the camera in his eyes: from the helmet looking at the ball
CAMS.hpov = (u, t, s) => { batter.neck.updateWorldMatrix(true, false); const q = batter.neck.getWorldQuaternion(new THREE.Quaternion()), f = v3(0, 0, 1).applyQuaternion(q), e = wpos(batter.neck).add(v3(0, 0.4, 0)).addScaledVector(f, s.fwd ?? 0.5);
  return [e, BB.position.clone().add(A(s.lo ?? [0, 0, 0])), lerp(s.f0 ?? 46, s.f1 ?? s.f0 ?? 46, easeIO(u))]; };
// a close-up of his face: `d` in front of it, turned `ang` degrees to one side
CAMS.eyes = (u, t, s) => { batter.neck.updateWorldMatrix(true, false); const q = batter.neck.getWorldQuaternion(new THREE.Quaternion()), f = v3(0, 0, 1).applyQuaternion(q), up = v3(0, 1, 0);
  const a = lerp(s.a0 ?? 20, s.a1 ?? s.a0 ?? 20, easeIO(u)) * D2R, d = lerp(s.d0 ?? 1.5, s.d1 ?? s.d0 ?? 1.5, easeIO(u)), c = wpos(batter.neck).add(v3(0, s.cy ?? 0.3, 0)).addScaledVector(f, 0.28), dir = f.clone().applyAxisAngle(up, a);
  return [c.clone().addScaledVector(dir, d).add(v3(0, s.h ?? 0.05, 0)), c.clone().add(A(s.lo ?? [0, 0, 0])), lerp(s.f0 ?? 24, s.f1 ?? s.f0 ?? 24, easeIO(u))]; };
// rides with any pitch (hs.pitch) from the hand to the plate
CAMS.hride = (u, t, s) => { const P = PI_[s.hit.pitch ?? "fb"], k = t - s.hit.rel, b = k < 0 ? ballInFingers() : pathAt(P.path, Math.min(k, P.flight)), o = A(s.off ?? [-0.9, 0.35, -2.2]);
  const w = smooth(k / (s.ease ?? 0.05)); return [b.clone().add(o), b.clone().add(v3(0, -0.1, 0.8)).lerp(v3(0.3, 2.4, 2.0), smooth((k - P.flight + 0.2) / 0.2) * (s.home ?? 1)), lerp(s.f0 ?? 34, s.f1 ?? 50, w)]; };
CAMS.hfollow = (u, t, s) => { const c = mixV(A(s.c0), A(s.c1 ?? s.c0), easeIO(u)), l0 = A(s.l), kk = t - s.hit.rel - TCON;
  const w = smooth(kk / (s.lag ?? 0.35)); return [c, l0.lerp(BB.position.clone(), w * (s.fw ?? 1)), lerp(s.f0 ?? 36, s.f1 ?? s.f0 ?? 36, easeIO(u))]; };

// ------------------------------------------------------------------ DOM overlays fed from the same clock
const $ = (id) => document.getElementById(id);

// ================================================================== bat speed: the lab, the x-ray, ground reaction forces, the sequence
// One hitter (swing "B": a load into the rear hip, a stride, the pelvis then the torso turning, the arms and hands delivering the barrel).
// The ballpark is hidden for the lab shots: a dark capture stage with a force plate under each foot.
// Colors per segment: legs/ground amber, pelvis orange, torso cyan, arms/hands green, the bat gold.
const SEGC = { legs: 0xffb547, pelvis: 0xff6a3d, torso: 0x56d1ff, arms: 0x3dd68c, bat: 0xffd84d };
const PARK = scene.children.slice(0, N_PARK).filter((o) => !o.isLight && o !== cam);
const CASTP = [pitcher, C, ump, U1, B1F, ...Object.values(HD), ...bench].map((p) => p.root);
const SKY0 = scene.background, FOG0 = { c: scene.fog.color.clone(), n: scene.fog.near, f: scene.fog.far };
const LAB = new THREE.Group(); LAB.visible = false; scene.add(LAB);
{
  const gridTex = canvasTex(1024, 1024, (g, w, h) => {
    g.fillStyle = "#0a0e15"; g.fillRect(0, 0, w, h);
    for (let i = 0; i <= 32; i++) { const x = i / 32 * w; g.strokeStyle = i % 4 ? "rgba(120,150,190,.13)" : "rgba(140,175,220,.32)"; g.lineWidth = i % 4 ? 1.5 : 3;
      g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); g.beginPath(); g.moveTo(0, x); g.lineTo(w, x); g.stroke(); }
  }, { repeat: [3, 3] });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(192, 192), new THREE.MeshStandardMaterial({ map: gridTex, roughness: 0.55, metalness: 0.1, envMap: ENV, envMapIntensity: 0.4 }));
  floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; floor.position.set(-3, 0.002, 0); LAB.add(floor);
  // capture cameras on stands in a ring, each with a lit ring
  for (let i = 0; i < 10; i++) {
    const a = i / 10 * Math.PI * 2 + 0.2, r = 19, x = -3 + Math.cos(a) * r, z = Math.sin(a) * r;
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 9, 8), new THREE.MeshStandardMaterial({ color: 0x1a1f28, roughness: 0.6 })); pole.position.set(x, 4.5, z); LAB.add(pole);
    const body = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.45, 0.7), new THREE.MeshStandardMaterial({ color: 0x20262f, roughness: 0.4 })); body.position.set(x, 9.1, z); body.lookAt(-3, 3, 0); LAB.add(body);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.2, 0.05, 8, 24), glowM(0xff4d4d, 0.9)); ring.position.copy(body.position).add(v3(-3 - x, 3 - 9.1, -z).normalize().multiplyScalar(0.38)); ring.lookAt(-3, 3, 0); LAB.add(ring);
  }
  // a soft floor glow under the hitter
  const pool = new THREE.Mesh(new THREE.CircleGeometry(14, 64), new THREE.MeshBasicMaterial({ map: dotTex, color: 0x5a7aa8, transparent: true, opacity: 0.35, depthWrite: false })); pool.rotation.x = -Math.PI / 2; pool.position.set(-3, 0.01, 0); LAB.add(pool);
}
const LABFILL = new THREE.HemisphereLight(0x9fb8e0, 0x10141c, 0); scene.add(LABFILL);
function setLab(on, gym = false) {
  LAB.visible = on && !gym; if (typeof GYM !== "undefined") GYM.visible = on && gym; for (const o of PARK) o.visible = !on; for (const o of CASTP) o.visible = !on;
  scene.background = on ? new THREE.Color(0x06090f) : SKY0;
  if (on) { scene.fog.color.set(0x06090f); scene.fog.near = 40; scene.fog.far = 140; } else { scene.fog.color.copy(FOG0.c); scene.fog.near = FOG0.n; scene.fog.far = FOG0.f; }
  LABFILL.intensity = on ? 0.9 : 0;
}
// force plates: one under the rear foot, one where the stride lands
const PLATES = {};
for (const [key, a, b] of [["rear", -1.25 + 0.4, 0.05], ["lead", 2.0 - 0.35, 0.02]]) {
  const g = new THREE.Group();
  const top = new THREE.Mesh(roundBox(2.0, 0.14, 3.0, 0.05, 4), new THREE.MeshStandardMaterial({ color: 0x2a313c, roughness: 0.35, metalness: 0.6, envMap: ENV, envMapIntensity: 0.6 })); top.position.y = 0.07; top.receiveShadow = true; g.add(top);
  const edge = new THREE.Mesh(new THREE.EdgesGeometry(new THREE.BoxGeometry(2.04, 0.16, 3.04)), new THREE.LineBasicMaterial({ color: SEGC.legs, transparent: true, opacity: 0.6, toneMapped: false })); edge.position.y = 0.07; g.add(edge);
  const glow = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 4.2), new THREE.MeshBasicMaterial({ map: dotTex, color: SEGC.legs, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false })); glow.rotation.x = -Math.PI / 2; glow.position.y = 0.16; g.add(glow);
  PLATES[key] = { g, a, b, edge, glow }; LAB.add(g);
}
// ground reaction force arrows: a shaft and a head, from the ground under each foot
function makeForce() {
  const g = new THREE.Group(); g.visible = false; scene.add(g);
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 1, 14), glowM(SEGC.legs, 0.95)), head = new THREE.Mesh(new THREE.ConeGeometry(0.26, 0.55, 20), glowM(SEGC.legs, 0.95));
  const halo = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.24, 1, 14), glowM(SEGC.legs, 0.18)); halo.material.blending = THREE.AdditiveBlending;
  for (const m of [shaft, head, halo]) { m.renderOrder = 9; m.material.depthTest = false; g.add(m); }
  return { g, set(base, dir, len, op) {
    g.visible = op > 0.01 && len > 0.05; if (!g.visible) return;
    const u = dir.clone().normalize(), q = new THREE.Quaternion().setFromUnitVectors(v3(0, 1, 0), u), L = Math.max(0.1, len - 0.5);
    shaft.scale.set(1, L, 1); shaft.position.copy(base).addScaledVector(u, L / 2); shaft.quaternion.copy(q);
    halo.scale.set(1, L, 1); halo.position.copy(shaft.position); halo.quaternion.copy(q);
    head.position.copy(base).addScaledVector(u, L + 0.27); head.quaternion.copy(q);
    shaft.material.opacity = head.material.opacity = 0.95 * op; halo.material.opacity = 0.2 * op; } };
}
const F_REAR = makeForce(), F_LEAD = makeForce();
// how the support is shared (qualitative, relative to standing): the load onto the rear leg, the stride lands at k = -0.22,
// the lead leg takes over and braking builds into contact. Directions: the rear leg pushes toward the pitcher; the lead leg braces against it.
function grfAt(k) {
  const land = smooth((k + 0.24) / 0.16), air = k > -0.75 && k < -0.22;
  const rear = k < -0.75 ? lerp(0.55, 0.62, smooth((k + 1.0) / 0.25)) : lerp(lerp(0.62, 1.0, smooth((k + 0.75) / 0.25)), lerp(0.55, 0.18, smooth((k + 0.1) / 0.3)), land);
  const lead = air ? 0.45 * (1 - smooth((k + 0.75) / 0.08)) : k < -0.75 ? 0.45 : lerp(0, 1.25 - 0.35 * smooth((k - 0.02) / 0.3), land) * (1 - 0.0);
  const push = smooth((k + 0.6) / 0.3) * (1 - smooth((k + 0.02) / 0.2)), brake = land * (1 - 0.5 * smooth((k - 0.05) / 0.3));
  return { rear, lead, push, brake };
}
// the x-ray: the uniform goes translucent and the segments glow underneath
const XMATS = []; batter.root.traverse((o) => { if (o.isMesh && !XMATS.includes(o.material)) XMATS.push(o.material); });
for (const m of [gloveM, strapM, armM]) if (!XMATS.includes(m)) XMATS.push(m);
function makeBone(c, r) { const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 1, 12), glowM(c, 0.95)); m.material.depthTest = false; m.renderOrder = 10; m.visible = false; scene.add(m); return m; }
function makeJoint(c, r) { const m = new THREE.Mesh(new THREE.SphereGeometry(r, 16, 12), glowM(c, 0.95)); m.material.depthTest = false; m.renderOrder = 11; m.visible = false; scene.add(m); return m; }
const BONES = {
  legs: [makeBone(SEGC.legs, 0.07), makeBone(SEGC.legs, 0.07), makeBone(SEGC.legs, 0.06), makeBone(SEGC.legs, 0.06), makeBone(SEGC.legs, 0.05), makeBone(SEGC.legs, 0.05)],
  pelvis: [makeBone(SEGC.pelvis, 0.11), makeBone(SEGC.pelvis, 0.3)],
  torso: [makeBone(SEGC.torso, 0.1), makeBone(SEGC.torso, 0.11), makeBone(SEGC.torso, 0.3)],
  arms: [makeBone(SEGC.arms, 0.07), makeBone(SEGC.arms, 0.07), makeBone(SEGC.arms, 0.06), makeBone(SEGC.arms, 0.06)],
};
const JOINTS = { legs: [0, 1, 2, 3].map(() => makeJoint(SEGC.legs, 0.13)), pelvis: [0, 1].map(() => makeJoint(SEGC.pelvis, 0.16)), torso: [0, 1, 2].map(() => makeJoint(SEGC.torso, 0.15)), arms: [0, 1, 2, 3].map(() => makeJoint(SEGC.arms, 0.12)) };
for (const k of ["pelvis", "torso"]) { BONES[k][BONES[k].length - 1].material.blending = THREE.AdditiveBlending; }   // the halos on the hip and shoulder lines
function setBone(m, a, b, op) {
  m.visible = op > 0.01; if (!m.visible) return;
  const d = b.clone().sub(a); m.position.copy(a).addScaledVector(d, 0.5); m.scale.set(1, d.length(), 1); m.quaternion.setFromUnitVectors(v3(0, 1, 0), d.normalize());
  m.material.opacity = (m.geometry.parameters.radiusTop > 0.2 ? 0.16 : 0.95) * op;
}
const ext = (a, b, f) => { const m = a.clone().add(b).multiplyScalar(0.5); return [m.clone().lerp(a, f), m.clone().lerp(b, f)]; };
const SEP = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0, depthWrite: false, depthTest: false, side: THREE.DoubleSide, toneMapped: false })); SEP.renderOrder = 8; scene.add(SEP);
const BARC = new THREE.Color();
function setXray(s, v, k, P = batter) {
  const xo = winOp(v, s.xray, s.xin ?? 0.4, 0.3);
  for (const m of (P === pitcher ? XMATS_P : XMATS)) { m.transparent = xo > 0.01; m.opacity = 1 - 0.87 * xo; m.depthWrite = xo < 0.5; }
  const sg = s.seg ?? {}, any = Object.keys(sg).length > 0;
  const lit = (key) => (any ? 0.22 + 0.78 * winOp(v, sg[key], 0.12) : 1) * xo;
  const W_ = (o) => wpos(o);
  const toe = (f) => { f.updateWorldMatrix(true, false); return f.localToWorld(v3(0, -0.12, 0.72)); };
  const hipL = W_(P.hipL), hipR = W_(P.hipR), knL = W_(P.knL), knR = W_(P.knR), ftL = W_(P.ftL), ftR = W_(P.ftR);
  const shL = W_(P.shL), shR = W_(P.shR), elL = W_(P.elL), elR = W_(P.elR), hdL = W_(P.handL), hdR = W_(P.handR), pc = W_(P.pelvis), nk = W_(P.neck);
  const lo = lit("legs"); [[hipL, knL], [hipR, knR], [knL, ftL], [knR, ftR], [ftL, toe(P.ftL)], [ftR, toe(P.ftR)]].forEach(([a, b], i) => setBone(BONES.legs[i], a, b, lo));
  [knL, knR, ftL, ftR].forEach((p, i) => { JOINTS.legs[i].visible = lo > 0.01; JOINTS.legs[i].position.copy(p); JOINTS.legs[i].material.opacity = 0.95 * lo; });
  const po = lit("pelvis"), [pa, pb] = ext(hipL, hipR, 1.9);
  setBone(BONES.pelvis[0], pa, pb, po); setBone(BONES.pelvis[1], pa, pb, po);
  [hipL, hipR].forEach((p, i) => { JOINTS.pelvis[i].visible = po > 0.01; JOINTS.pelvis[i].position.copy(p); JOINTS.pelvis[i].material.opacity = 0.95 * po; });
  const to = lit("torso"), [sa, sb] = ext(shL, shR, 1.6);
  setBone(BONES.torso[0], pc, nk, to); setBone(BONES.torso[1], sa, sb, to); setBone(BONES.torso[2], sa, sb, to);
  [shL, shR, nk].forEach((p, i) => { JOINTS.torso[i].visible = to > 0.01; JOINTS.torso[i].position.copy(p); JOINTS.torso[i].material.opacity = 0.95 * to; });
  const ao = lit("arms"); [[shL, elL], [shR, elR], [elL, hdL], [elR, hdR]].forEach(([a, b], i) => setBone(BONES.arms[i], a, b, ao));
  [elL, elR, hdL, hdR].forEach((p, i) => { JOINTS.arms[i].visible = ao > 0.01; JOINTS.arms[i].position.copy(p); JOINTS.arms[i].material.opacity = 0.95 * ao; });
  // the bat glows gold with the x-ray or on its own cue
  if (P === batter) { const bo = Math.max(lit("bat"), winOp(v, s.batglow, 0.15));
  barrelHL.material.color.set(SEGC.bat); barrelHL.material.opacity = Math.max(barrelHL.material.opacity, 0.5 * bo); }
  // hip-shoulder separation: the wedge between the hip line and the shoulder line, seen from above
  const so = winOp(v, s.sep, 0.2);
  SEP.visible = so > 0.01;
  if (SEP.visible) {
    const ang = (a, b) => Math.atan2(b.z - a.z, b.x - a.x), a0 = ang(hipR, hipL), a1 = ang(shR, shL);
    let d = a1 - a0; while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI;
    const c = pc.clone(), y = shL.y * 0.5 + pc.y * 0.5, R0 = 2.6, pts = [];
    for (let i = 0; i <= 24; i++) { const a = a0 + d * i / 24; for (const sgn of [1, -1]) pts.push([c.x + sgn * Math.cos(a) * R0, y, c.z + sgn * Math.sin(a) * R0]); }
    const pos = [], P2 = (q) => pos.push(...q);
    for (const sgn of [0, 1]) for (let i = 0; i < 24; i++) { P2([c.x, y, c.z]); P2(pts[i * 2 + sgn]); P2(pts[(i + 1) * 2 + sgn]); }
    SEP.geometry.dispose(); SEP.geometry = new THREE.BufferGeometry(); SEP.geometry.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    SEP.material.opacity = 0.32 * so;
  }
}
function setGRF(s, v, k, w = "B") {
  const go = winOp(v, s.grf, 0.3), f = grfAt(k), lab = !!s.lab;
  const R_ = ROOT[w], ft = feetAt(w, k);
  for (const [key, P] of Object.entries(PLATES)) { P.g.position.copy(HB(R_, P.a, 0, P.b)); P.g.rotation.y = Math.PI / 2; P.g.visible = lab;
    const load = key === "rear" ? f.rear : f.lead; P.glow.material.opacity = 0.55 * go * clamp(load, 0, 1.2); P.edge.material.opacity = 0.35 + 0.6 * go * clamp(load, 0, 1); }
  const pz = v3(0, 0, -1), base = (fb) => v3(fb.ball.x, 0.18, fb.ball.z + 0.2);
  const dR = v3(0, 1, 0).addScaledVector(pz, 0.55 * f.push), dL = v3(0, 1, 0).addScaledVector(pz, -0.6 * f.brake);
  F_REAR.set(base(ft.rear), dR, 3.4 * f.rear, go); F_LEAD.set(base(ft.lead), dL, 3.4 * f.lead * (ft.lead.ball.y < 0.05 ? 1 : 0), go);
  return f;
}
// the rotation traces: how fast the pelvis and the torso are turning through the swing (from the same keyed body: no measured data)
const TRK0 = -0.34, TRK1 = 0.1;
const TRACE = (() => { const n = 160, pel = [], tor = [];
  for (let i = 0; i <= n; i++) { const k = lerp(TRK0, TRK1, i / n), h = 0.004, a = bodyAt("B", k - h), b = bodyAt("B", k + h);
    pel.push((b.pelvisTwist - a.pelvisTwist) / (2 * h)); tor.push(((b.pelvisTwist + b.twist) - (a.pelvisTwist + a.twist)) / (2 * h)); }
  const mx = Math.max(...pel, ...tor); return { n, pel: pel.map((x) => x / mx), tor: tor.map((x) => x / mx) }; })();
function drawTrace(k) {
  const cv = $("trace"); if (!cv) return; const g = cv.getContext("2d"), w = cv.width, h = cv.height, x0 = 20, x1 = w - 20, y0 = h - 30, y1 = 24;
  g.clearRect(0, 0, w, h);
  g.strokeStyle = "rgba(255,255,255,.35)"; g.lineWidth = 3; g.beginPath(); g.moveTo(x0, y1 - 10); g.lineTo(x0, y0); g.lineTo(x1, y0); g.stroke();
  const upto = clamp((k - TRK0) / (TRK1 - TRK0), 0, 1) * TRACE.n;
  for (const [arr, col] of [[TRACE.pel, "#FF6A3D"], [TRACE.tor, "#56D1FF"]]) {
    g.strokeStyle = col; g.lineWidth = 8; g.lineJoin = "round"; g.lineCap = "round"; g.shadowColor = col; g.shadowBlur = 14; g.beginPath();
    for (let i = 0; i <= Math.min(TRACE.n, upto); i++) { const x = lerp(x0, x1, i / TRACE.n), y = lerp(y0, y1, Math.max(0, arr[i])); i ? g.lineTo(x, y) : g.moveTo(x, y); }
    g.stroke(); g.shadowBlur = 0;
    const i = Math.floor(Math.min(TRACE.n, upto)), x = lerp(x0, x1, i / TRACE.n), y = lerp(y0, y1, Math.max(0, arr[i]));
    g.fillStyle = col; g.beginPath(); g.arc(x, y, 11, 0, 7); g.fill();
  }
}
const PINT = { batter: () => headTop(batter), hands: () => batPt(CUR.hm ?? 0.3), knob: () => batPt(-0.02), bottom: () => batPt(GL.position.y - 0.14), top: () => batPt(GRt.position.y + 0.14),
  sweet: () => batPt(SWEET), end: () => batPt(BAT_LEN), lenmid: () => { BAT.updateMatrixWorld(true); return BAT.localToWorld(v3(0, (BAT_LEN + GL.position.y) / 2 + 0.3, -0.42)); },
  ball: () => BB.position.clone(), pitcher: () => headTop(pitcher), plate: () => v3(0, 0, -0.7), mark: () => MARK.position.clone().add(v3(0, 0.42, 0)), zone: () => v3(0, ZY1 + 0.35, PLATE_F), chase: () => v3(0, ZY1 + CYP + 0.35, PLATE_F), ump: () => headTop(ump),
  glove: () => wpos(pitcher.handL).add(v3(0, 0.95, 0)), runner: () => headTop(R), coach: () => headTop(COACH), chand: () => wpos(HAND.wrist).add(v3(0, 0.55, 0)),
  phand: () => wpos(pitcher.handR).add(v3(0, 0.75, 0)), bball: () => BB.position.clone().add(v3(0, 0.55, 0)), glovec: () => wpos(C.handL).add(v3(0, 0.6, 0)),
  bhead: () => headTop(batter), scrA: () => SCREEN.localToWorld(v3(-1.6, 3.35, 0.05)), scrB: () => SCREEN.localToWorld(v3(-1.6, -0.25, 0.05)), scrLog: () => SCREEN.localToWorld(v3(3.55, 3.55, 0.05)), rp2: () => headTop(RP2), rcoach: () => headTop(RCOACH) };
function pin(id, p, rect) {
  const el = $(id); if (!el || !p) return;
  const q = p.clone().project(cam), [x0, y0, w, h] = rect, half = Math.min(270, w / 2 - 10);
  el.style.left = `${clamp(x0 + (q.x + 1) / 2 * w, x0 + half, x0 + w - half).toFixed(1)}px`; el.style.top = `${clamp(y0 + (1 - q.y) / 2 * h, y0 + 40, y0 + h - 20).toFixed(1)}px`;
}
function view(c, s, aspect) { cam.up.set(...(s.up ?? [0, 1, 0])); frame(cam, c[0], c[1], c[2], aspect); setBokeh(s.bokeh ?? 0); closeLights(!!s.close, c[1]); }

// ================================================================== 100 mph: the delivery (a right-handed pitcher from the windup)
// Keyed on k = time from release (s). The body (pelvis and trunk rotation, drop, lean, tilt) runs on smooth curves; the legs are
// solved (two-bone IK) so the drive foot stays on the rubber and the stride foot lands and holds; each arm is keyed as the
// direction of the upper arm and of the forearm in the trunk's frame, so shoulder external rotation (the forearm laid back),
// internal rotation (the forearm sweeping forward over the top) and elbow extension (the forearm lining up with the upper arm)
// are separate, visible motions. An illustration of a typical delivery, not a measurement of any pitcher.
const PBODY = [   // pelvisTwist: 0 = side-on, + = open toward home; twist = the trunk's turn on top of the pelvis; side < 0 = tilted toward the glove side
  [-1.35, { drop: 0, lean: 4, side: 0, twist: 0, pelvisTwist: 0 }],
  [-0.95, { drop: -0.12, lean: -6, side: 4, twist: -10, pelvisTwist: -12 }],       // the leg lift: a little coil
  [-0.55, { drop: -0.38, lean: -3, side: 6, twist: -12, pelvisTwist: -10 }],
  [-0.15, { drop: -0.98, lean: 4, side: 4, twist: -30, pelvisTwist: 28 }],          // foot contact: low, the pelvis opening, the trunk still closed
  [-0.09, { drop: -0.93, lean: 10, side: -4, twist: -25, pelvisTwist: 66 }],
  [-0.045, { drop: -0.86, lean: 18, side: -10, twist: 2, pelvisTwist: 83 }],
  [0, { drop: -0.8, lean: 34, side: -18, twist: 12, pelvisTwist: 92 }],              // release: the lead knee has straightened and lifted him; tilted to the glove side
  [0.1, { drop: -0.88, lean: 46, side: -14, twist: 26, pelvisTwist: 98 }],
  [0.6, { drop: -1.02, lean: 55, side: -8, twist: 36, pelvisTwist: 104 }],
];
const PROOT = [[-1.35, [0, -60.25]], [-0.95, [0, -60.25]], [-0.55, [0.05, -59.6]], [-0.15, [0.15, -57.9]], [0, [0.2, -56.6]], [0.6, [0.25, -55.8]]];
const GY = (x, z) => moundY(x, z);
const PLEAD = [   // the stride foot: [k, ball x, height above the mound, z, toe yaw, heel]
  [-1.35, [-0.35, 0, -59.0, -Math.PI / 2, 0]], [-1.1, [-0.4, 0.5, -59.3, -Math.PI / 2, 0.3]], [-0.95, [-0.55, 2.3, -60.0, -Math.PI / 2 - 0.2, 0.7]],
  [-0.6, [-0.3, 1.5, -59.2, -1.4, 0.5]], [-0.32, [0.25, 0.6, -56.6, -0.7, 0.3]], [-0.15, [0.45, 0, -54.95, -0.35, 0]], [0.6, [0.45, 0, -54.95, -0.35, 0]]];
const PDRIVE = [  // the drive foot: on the rubber, then the heel comes up, it turns and drags
  [-1.35, [-0.3, 0, -60.2, -Math.PI / 2, 0]], [-0.15, [-0.3, 0, -60.2, -Math.PI / 2, 0.15]], [-0.04, [-0.25, 0, -60.05, -1.1, 0.7]],
  [0.12, [-0.1, 0, -59.3, -0.3, 1.35]], [0.6, [0.05, 0.25, -57.6, -0.1, 1.2]]];
const nv3 = (a) => v3(a[0], a[1], a[2]).normalize();
const ARM_K = {   // [k, upper-arm direction, forearm direction] in the trunk's frame (+x his left, +y up the spine, +z his chest)
  R: [[-1.35, [0.15, -0.9, 0.4], [0.75, 0.35, 0.55]], [-0.95, [0.2, -0.8, 0.55], [0.8, 0.45, 0.4]], [-0.62, [0.1, -0.95, 0.3], [0.3, -0.7, 0.6]],
      [-0.42, [-0.2, -0.9, -0.4], [-0.2, -0.85, -0.5]], [-0.26, [-0.75, -0.45, -0.5], [-0.6, -0.2, -0.75]],
      [-0.15, [-0.95, 0.05, -0.3], [0, 1, -0.1]],                      // foot contact: the forearm up
      [-0.09, [-0.97, 0.08, -0.15], [0.05, 0.75, -0.65]],
      [-0.05, [-0.98, 0.1, 0.05], [0.05, 0.25, -0.97]],              // maximum external rotation: the forearm laid back
      [-0.033, [-0.98, 0.1, 0.04], [0, 0.55, -0.84]],
      [-0.016, [-0.97, 0.14, 0.12], [-0.25, 0.92, 0.15]],                  // internal rotation: the forearm sweeps forward over the top
      [-0.006, [-0.9, 0.32, 0.3], [-0.42, 0.72, 0.55]],
      [0, [-0.76, 0.46, 0.46], [-0.58, 0.48, 0.66]],                     // release: the elbow nearly straight
      [0.08, [-0.15, -0.35, 0.92], [0.3, -0.6, 0.74]], [0.3, [0.55, -0.75, 0.35], [0.65, -0.6, 0.2]], [0.6, [0.6, -0.75, 0.2], [0.7, -0.5, 0.3]]],
  L: [[-1.35, [-0.15, -0.9, 0.4], [-0.75, 0.35, 0.55]], [-0.95, [-0.2, -0.8, 0.55], [-0.8, 0.45, 0.4]], [-0.62, [0.2, -0.6, 0.75], [0.6, 0.2, 0.75]],
      [-0.3, [0.8, 0.1, 0.45], [0.85, 0.2, 0.45]], [-0.15, [0.85, 0.15, 0.4], [0.6, 0.5, 0.6]], [-0.05, [0.4, -0.6, 0.65], [-0.4, 0.6, 0.65]],
      [0, [0.3, -0.85, 0.35], [-0.3, 0.5, 0.8]], [0.3, [0.4, -0.85, 0.2], [0, 0.3, 0.95]], [0.6, [0.4, -0.85, 0.2], [0, 0.3, 0.95]]],
};
const herm3 = (keys, k) => herm(keys.map(([kk, a]) => [kk, v3(a[0], a[1], a[2])]), k);
function pbodyAt(k) { const out = {}; for (const key of Object.keys(PBODY[0][1])) out[key] = herm(PBODY.map(([kk, q]) => [kk, v3(q[key], 0, 0)]), k).x; return out; }
function pfoot(keys, k) { const a = herm(keys.map(([kk, q]) => [kk, v3(q[0], q[1], q[2])]), k), b = herm(keys.map(([kk, q]) => [kk, v3(q[3], q[4], 0)]), k);
  return { ball: v3(a.x, GY(a.x, a.z) + a.y, a.z), yaw: b.x, heel: b.y }; }
const ARMQ = { U: v3(), F: v3() };
function armSet(P, side, k) {                                       // aim the upper arm along U and bend the forearm toward F (trunk frame)
  const K = ARM_K[side], U = herm(K.map(([kk, u]) => [kk, nv3(u)]), k).normalize(), F = herm(K.map(([kk, , f]) => [kk, nv3(f)]), k).normalize();
  let n = F.clone().addScaledVector(U, -F.dot(U)); const th = Math.acos(clamp(F.dot(U), -1, 1));
  if (n.length() < 1e-4) n = v3(0, 0, 1).addScaledVector(U, -U.z); n.normalize();
  const ey = U.clone().negate(), ez = n, ex = ey.clone().cross(ez).normalize();
  P[`sh${side}`].quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(ex, ey, ez));
  P[`el${side}`].rotation.set(-th, 0, 0);
  if (side === "R") { ARMQ.U.copy(U); ARMQ.F.copy(F); }
}
const PX = { k: -1.35 };
function posePitcher(k) {
  const P = pitcher, b = pbodyAt(k), r = herm(PROOT.map(([kk, q]) => [kk, v3(q[0], 0, q[1])]), k);
  P.root.position.set(r.x, GY(r.x, r.z), r.z); P.root.rotation.y = -Math.PI / 2;
  applyPose(P, { drop: b.drop, lean: b.lean, side: b.side, twist: b.twist, pelvisTwist: b.pelvisTwist, nod: 4 });
  P.root.updateMatrixWorld(true);
  legIK(P, "R", pfoot(PDRIVE, k)); legIK(P, "L", pfoot(PLEAD, k));
  armSet(P, "R", k); armSet(P, "L", k);
  // the head: eyes on the target (the catcher's mitt) through the delivery
  P.root.updateMatrixWorld(true); P.spine.getWorldQuaternion(_q); _qi.copy(_q).invert();
  const d = v3(0.4, 2.4, 2.6).sub(P.neck.getWorldPosition(new THREE.Vector3())).applyQuaternion(_qi);
  P.neck.rotation.set(clamp(Math.atan2(-d.y, Math.hypot(d.x, d.z)), -0.6, 0.7), clamp(Math.atan2(d.x, d.z), -1.75, 1.75), 0, "YXZ");
  P.root.updateMatrixWorld(true); PX.k = k;
}
const ballInFingers = () => { pitcher.root.updateMatrixWorld(true); const h = wpos(pitcher.handR), f = ARMQ.F.clone().transformDirection(pitcher.spine.matrixWorld); return h.addScaledVector(f, 0.24); };
// the x-ray materials of the pitcher
const XMATS_P = []; pitcher.root.traverse((o) => { if (o.isMesh && !XMATS_P.includes(o.material)) XMATS_P.push(o.material); });
// the shoulder's rotation about the upper arm: an arc with a head (external rotation, then internal rotation)
const ROTARC = new THREE.Group(); ROTARC.visible = false; scene.add(ROTARC);
{ const arc = new THREE.Mesh(new THREE.TorusGeometry(0.42, 0.04, 10, 48, Math.PI * 1.35), glowM(SEGC.arms, 0.95)); arc.material.depthTest = false; arc.renderOrder = 12; ROTARC.add(arc);
  const a = Math.PI * 1.35, head = new THREE.Mesh(new THREE.ConeGeometry(0.11, 0.26, 16), glowM(SEGC.arms, 0.95)); head.material.depthTest = false; head.renderOrder = 12;
  head.position.set(Math.cos(a) * 0.42, Math.sin(a) * 0.42, 0); head.quaternion.setFromUnitVectors(v3(0, 1, 0), v3(-Math.sin(a), Math.cos(a), 0)); ROTARC.add(head); }
function setRotArc(op, dir, col) {
  ROTARC.visible = op > 0.01; if (!ROTARC.visible) return;
  const P = pitcher, S = wpos(P.shR), E = wpos(P.elR), U = E.clone().sub(S).normalize();
  ROTARC.position.copy(S).lerp(E, 0.62); ROTARC.quaternion.setFromUnitVectors(v3(0, 0, 1), U.multiplyScalar(dir));
  ROTARC.children.forEach((m) => { m.material.opacity = 0.95 * op; m.material.color.set(col); });
}
const ELBOWGLOW = new THREE.Sprite(new THREE.SpriteMaterial({ map: dotTex, color: SEGC.arms, transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending, opacity: 0 })); ELBOWGLOW.renderOrder = 13; scene.add(ELBOWGLOW);
// ground reaction forces for the pitcher (qualitative): the drive leg pushes toward home through the stride; the stride leg
// lands, takes the load and braces (its force points up and back toward the rubber)
function grfP(k) {
  const fc = smooth((k + 0.17) / 0.06), lift = k > -1.1 && k < -0.15;
  const drive = lerp(lerp(0.55, 1.0, smooth((k + 1.2) / 0.3)), 0.25, smooth((k + 0.15) / 0.2)) * (1 - smooth((k - 0.05) / 0.1));
  const lead = lift ? 0 : k < -1.1 ? 0.45 : fc * (1.5 - 0.5 * smooth((k - 0.05) / 0.4));
  return { drive, lead, push: smooth((k + 0.7) / 0.35) * (1 - smooth((k + 0.1) / 0.15)), brake: fc };
}
const CATCHQ = () => catchPose("fb");
const PKF = PI_.fb;
function setSceneP(t, s, v) {
  for (const [k, p] of Object.entries(HD)) { const [x, z] = homeD[k]; p.root.position.set(x, 0, z); p.root.rotation.y = Math.atan2(-x, -z); applyPose(p, READY); }
  B1F.root.position.set(56, 0, -78); B1F.root.rotation.y = Math.atan2(-56, 78); applyPose(B1F, READY);
  U1.root.position.set(70, 0, -56); U1.root.rotation.y = Math.atan2(-70, 56); applyPose(U1, { drop: -0.7, lean: 26, nod: -6, hipL: [40, 16], hipR: [40, 16], knL: 48, knR: 48, shL: [30, 12, 0], elL: 50, shR: [30, 12, 0], elR: 50 });
  BOARD.visible = false; COACH.root.visible = false; R.root.visible = false; HAND.root.visible = false; RING_OP = 0; ZONE.visible = false; MARK.visible = MARKR.visible = false; CHASE.visible = false;
  setLab(false); for (const P of PLATES ? Object.values(PLATES) : []) P.g.visible = false;
  batter.root.visible = false; BAT.visible = false; GHOSTS.forEach((m) => (m.visible = false)); TR_KNOB.set([]); TR_TIP.set([]); TR_KNOB2.set([]);
  AR_INTENT.set(v3(), v3(), 0, 0); AR_STRAIGHT.set(v3(), v3(), 0, 0); HIPRING.visible = HIPHALO.visible = false; ROT.visible = false; barrelHL.material.opacity = 0; KNOBHL.material.opacity = 0;
  ump.root.position.set(0.5, 0, 6.0); ump.root.rotation.y = Math.PI; applyPose(ump, U_SET);
  const cq = CATCHQ(); C.root.position.set(cq.cx, 0, 3.0); C.root.rotation.y = Math.PI; applyPose(C, cq);
  const k = t;                                                      // the pitch is released at t = 0
  posePitcher(k);
  // the ball: in the fingers, then the pitch, then in the mitt
  BB.visible = !s.noball; STREAK.forEach((m) => (m.visible = false)); FLASH.material.opacity = 0; BGLOW.material.opacity = 0;
  if (k < 0) BB.position.copy(ballInFingers());
  else if (k < PKF.flight) { BB.position.copy(pathAt(PKF.path, k)); if (k < 0.012) BB.position.lerp(ballInFingers(), 1 - k / 0.012);
    if (s.streak) STREAK.forEach((m, i) => { const d = (i + 1) * 0.006; if (k - d > 0) { m.visible = true; m.position.copy(pathAt(PKF.path, k - d)); } }); }
  else { const kk = k - PKF.flight; C.root.updateMatrixWorld(true); applyPose(C, { ...cq, shL: [cq.shL[0] - 6 * Math.exp(-kk * 14), cq.shL[1], 0] }); C.root.updateMatrixWorld(true); BB.position.copy(wpos(C.handL)).add(v3(0, 0, -0.05)); }
  BB.quaternion.setFromAxisAngle(V(PKF.spin), PKF.rpm / 60 * 2 * Math.PI * Math.max(0, k) * (s.spinx ?? 1));
  BGLOW.position.copy(BB.position); BGLOW.material.opacity = s.bglow ? 0.8 : 0;
  // the x-ray, segment highlights, the separation wedge
  setXray(s, v, k, pitcher);
  // ground reaction forces at the pitcher's feet
  const go = winOp(v, s.grf, 0.3), f = grfP(k), fl = pfoot(PLEAD, k), fd = pfoot(PDRIVE, k);
  const base = (fb) => v3(fb.ball.x, fb.ball.y - fb.ball.y + GY(fb.ball.x, fb.ball.z) + 0.12, fb.ball.z);
  F_REAR.set(base(fd), v3(0, 1, 0).addScaledVector(v3(0, 0, 1), 0.6 * f.push), 3.2 * f.drive * (fd.ball.y - GY(fd.ball.x, fd.ball.z) < 0.08 ? 1 : 0), go);
  F_LEAD.set(base(fl), v3(0, 1, 0).addScaledVector(v3(0, 0, -1), 0.65 * f.brake), 3.2 * f.lead * (fl.ball.y - GY(fl.ball.x, fl.ball.z) < 0.08 ? 1 : 0), go);
  // the arm: rotation arcs and the elbow
  const er = winOp(v, s.er, 0.15), ir = winOp(v, s.ir, 0.15);
  if (er > 0.01) setRotArc(er, 1, 0x56d1ff); else setRotArc(ir, -1, SEGC.arms);
  const eo = winOp(v, s.elbow, 0.12); ELBOWGLOW.material.opacity = 0.95 * eo; ELBOWGLOW.position.copy(wpos(pitcher.elR)); ELBOWGLOW.scale.setScalar(0.9 + 0.1 * Math.sin(v * 12));
  pitcher.root.visible = true;
  SUP = 0.5; KNOW = k;
}
CAMS.orbit = (u, t, s) => { const a = lerp(s.a0, s.a1 ?? s.a0, easeIO(u)) * D2R, c = A(s.ctr), r = lerp(s.r0, s.r1 ?? s.r0, easeIO(u)), h = lerp(s.h0, s.h1 ?? s.h0, easeIO(u));
  return [c.clone().add(v3(Math.sin(a) * r, h, Math.cos(a) * r)), c.clone().add(v3(0, s.ly ?? 0, 0)), lerp(s.f0 ?? 40, s.f1 ?? s.f0 ?? 40, easeIO(u))]; };
// a camera that rides with the ball from the hand toward the plate, a little behind and beside it, looking ahead
CAMS.ride = (u, t, s) => { const k = t, b = k < 0 ? ballInFingers() : pathAt(PKF.path, Math.min(k, PKF.flight)), o = A(s.off ?? [-0.9, 0.35, -2.2]);
  const w = smooth(k / (s.ease ?? 0.05)); return [b.clone().add(o), b.clone().add(v3(0, -0.15, 4.0)).lerp(v3(0.3, 2.4, 2.0), smooth((k - 0.12) / 0.2) * (s.home ?? 1)), lerp(s.f0 ?? 34, s.f1 ?? 50, w)]; };
Object.assign(PINH, { pshoulder: () => wpos(pitcher.shR), pelbow: () => wpos(pitcher.elR), phand: () => wpos(pitcher.handR), pfootL: () => wpos(pitcher.ftL).add(v3(0, 0.7, 0)),
  pfootR: () => wpos(pitcher.ftR).add(v3(0, 0.7, 0)), ppelvis: () => wpos(pitcher.pelvis), pchest: () => wpos(pitcher.neck).add(v3(0, -0.4, 0)), pball: () => BB.position.clone(), mitt: () => wpos(C.handL).add(v3(0, 0.5, 0)) });
// the speed gauge, fed from the clock: window.__CC.gauge = [[v, mph], ...]
function drawGauge(v) {
  const ns = document.querySelectorAll(".gneedle"); if (!ns.length) return; const K = CC.gauge ?? [[0, 0]];
  let mph = K[0][1]; for (let i = 1; i < K.length; i++) if (v >= K[i - 1][0]) mph = v >= K[i][0] ? K[i][1] : lerp(K[i - 1][1], K[i][1], easeIO((v - K[i - 1][0]) / (K[i][0] - K[i - 1][0])));
  ns.forEach((g) => (g.style.transform = `rotate(${(-120 + mph / 110 * 240).toFixed(2)}deg)`)); document.querySelectorAll(".gdig").forEach((d) => (d.textContent = String(Math.round(mph))));
}

// ================================================================== shortstop: the fielders, their plays and throws
// Each play: a ground ball from tools/physics.py, the fielder who takes it, how he fields it (forehand, backhand, dive, charge),
// and his throw (plant, from his knees after the dive, a jump throw, a feed to second). The glove arm is solved onto the ball
// (two-bone IK), so glove and ball meet exactly; each throw flies from his hand at release to the receiver's glove under gravity.
const HG = PLAY.hits;
const gAt = (id, t) => pathAt(HG[id].path, Math.max(0, t));
const SSP = HD.ss, B2P = HD.b2, B1P = B1F;
const BAG2 = v3(0, 0, -127.28), BAG1 = v3(63.64, 0, -63.64), BAG3 = v3(-63.64, 0, -63.64);
const START = { ss: v3(-36, 0, -140), b2: v3(32, 0, -140), b1: v3(58, 0, -72) };
const FP = { ss: SSP, b2: B2P, b1: B1P };
const READY_F = { drop: -0.75, lean: 32, hipL: [44, 18], hipR: [44, 18], knL: 52, knR: 52, shL: [35, 14, 0], shR: [35, 14, 0], elL: 45, elR: 45, nod: -18 };
const F_FORE = { drop: -1.55, lean: 58, nod: -30, hipL: [100, 30], hipR: [95, 30], knL: 105, knR: 100, shR: [30, 10, 0], elR: 60 };
const F_BACK = { drop: -1.25, lean: 46, twist: -30, nod: -26, hipL: [82, 16], knL: 88, hipR: [55, 34], knR: 66, shR: [20, 20, 0], elR: 70 };
const F_CHARGE = { drop: -1.05, lean: 50, nod: -26, hipL: [78, 10], knL: 72, hipR: [18, 8], knR: 52, shR: [30, 15, 0], elR: 60 };
const DIVEP = { drop: 0, lean: 0, nod: 38, hipL: [-4, 6], hipR: [-14, 8], knL: 14, knR: 38, shR: [150, 24, 0], elR: 25 };
const KNEEL = { drop: -1.7, lean: 14, nod: -4, hipL: [92, 10], knL: 96, hipR: [-6, 10], knR: 118, shR: [30, 12, 0], elR: 70 };
const THROWLEG = { drop: -0.55, hipL: [52, 10], knL: 34, hipR: [-24, 10], knR: 42 };
const JUMPLEG = { drop: -0.2, hipL: [42, 12], knL: 64, hipR: [12, 12], knR: 84 };
const RECEIVE = { drop: -0.72, lean: 26, nod: -6, hipL: [66, 10], knL: 34, hipR: [-16, 14], knR: 8, shR: [20, 14, 0], elR: 50 };
const ONBAG = { drop: -0.35, lean: 14, nod: -6, hipL: [22, 10], knL: 22, hipR: [8, 12], knR: 18, shR: [20, 14, 0], elR: 50 };
const COMM = { drop: -0.25, lean: 10, nod: -4, hipL: [10, 10], knL: 12, hipR: [10, 10], knR: 12, shR: [10, 12, 0], elR: 30 };
const THROW_K = [   // throwing arm [k from release, upper arm, forearm] in the trunk's frame
  [-0.5, [0.15, -0.9, 0.4], [0.75, 0.35, 0.55]], [-0.3, [-0.3, -0.9, -0.3], [-0.3, -0.8, -0.5]], [-0.16, [-0.95, 0, -0.3], [0, 1, -0.1]],
  [-0.06, [-0.98, 0.1, 0.05], [0.05, 0.3, -0.95]], [-0.025, [-0.97, 0.14, 0.15], [-0.25, 0.92, 0.2]], [0, [-0.8, 0.3, 0.5], [-0.62, 0.35, 0.7]],
  [0.12, [-0.1, -0.4, 0.9], [0.3, -0.6, 0.74]], [0.45, [0.5, -0.8, 0.3], [0.6, -0.6, 0.3]]];
const FEED_K = [    // a short sidearm feed to the bag
  [-0.3, [0.15, -0.9, 0.4], [0.75, 0.35, 0.55]], [-0.12, [-0.85, -0.35, -0.35], [-0.4, 0.4, -0.8]], [0, [-0.75, -0.2, 0.62], [-0.55, -0.05, 0.83]],
  [0.2, [-0.2, -0.5, 0.85], [0.1, -0.4, 0.9]], [0.5, [0.2, -0.85, 0.45], [0.4, -0.6, 0.6]]];
const THROW_T = [[-0.5, 0, -5], [-0.15, 10, -15], [-0.05, 45, 5], [0, 70, 25], [0.15, 85, 40], [0.5, 90, 45]];   // [k, pelvisTwist, twist]
const PLAYS = {
  hard: { who: "ss", hit: "hard", tech: "fore", thr: { dt: 0.58, to: "b1", mph: 84, how: "plant" } },
  roll: { who: "ss", hit: "roll", tech: "charge", thr: { dt: 0.34, to: "b1", mph: 72, how: "plant" } },
  hard2: { who: "ss", hit: "hard2", tech: "fore", thr: { dt: 0.58, to: "b1", mph: 84, how: "plant" } },
  roll2: { who: "ss", hit: "roll2", tech: "charge", thr: { dt: 0.34, to: "b1", mph: 72, how: "plant" } },
};
const hz = (v) => v3(v.x, 0, v.z);
const yawFace = (d) => Math.atan2(d.x, d.z), yawSide = (d) => Math.atan2(-d.z, d.x);
const leftOf = (yaw) => v3(Math.cos(yaw), 0, -Math.sin(yaw)), fwdOf = (yaw) => v3(Math.sin(yaw), 0, Math.cos(yaw));
const rotY = (d, a) => v3(d.x * Math.cos(a) + d.z * Math.sin(a), 0, -d.x * Math.sin(a) + d.z * Math.cos(a));
function lerpAng(a, b, u) { let d = b - a; while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI; return a + d * u; }
// where each receiver catches the throw: in front of the bag toward the thrower, at chest height
function catchPt(play) {
  const pl = PLAYS[play], bag = pl.thr.to === "b1" ? BAG1 : BAG2, from = PLAN[play].F;
  const d = hz(from.clone().sub(bag)).normalize(); return bag.clone().addScaledVector(d, pl.thr.to === "b1" ? 3.4 : 1.6).add(v3(0, 4.4, 0));
}
// the plan of each play: where he fields it, which way he faces, where his body is
const PLAN = {};
for (const [id, pl] of Object.entries(PLAYS)) {
  const H = HG[pl.hit], F = V(H.field), tf = H.tf, S = pl.start ?? START[pl.who];
  const vin = hz(gAt(pl.hit, tf).clone().sub(gAt(pl.hit, tf - 0.05))).normalize();          // the ball's direction as it arrives
  const u = hz(F.clone().sub(S)); const run = u.length(); u.normalize();
  let face, R;
  if (pl.tech === "fore") { face = vin.clone().negate(); R = F.clone().addScaledVector(face, -1.65).addScaledVector(leftOf(yawFace(face)), -0.55); }
  else if (pl.tech === "charge") { face = vin.clone().negate(); R = F.clone().addScaledVector(face, -1.5).addScaledVector(leftOf(yawFace(face)), -0.45); }
  else if (pl.tech === "back") { face = rotY(vin.clone().negate(), 0.6); R = F.clone().addScaledVector(face, -0.95).addScaledVector(leftOf(yawFace(face)), 1.35); }
  else { face = u.clone(); R = F.clone().addScaledVector(face, -6.3); }                               // the dive: laid out toward the ball (his feet are the pivot)
  R.y = 0; PLAN[id] = { F, tf, S, u, run, face, yawF: yawFace(face), R, tr: tf + pl.thr.dt };
}
const ARMS = { q0: new THREE.Quaternion(), e0: 0 };
function armKeyed(P, side, keys, k, w) {                            // blend the arm from its posed rotation toward keyed U/F
  if (w <= 0.001) return; ARMS.q0.copy(P[`sh${side}`].quaternion); ARMS.e0 = P[`el${side}`].rotation.x;
  const U = herm(keys.map(([kk, u]) => [kk, nv3(u)]), k).normalize(), Fv = herm(keys.map(([kk, , f]) => [kk, nv3(f)]), k).normalize();
  let n = Fv.clone().addScaledVector(U, -Fv.dot(U)); const th = Math.acos(clamp(Fv.dot(U), -1, 1));
  if (n.length() < 1e-4) n = v3(0, 0, 1).addScaledVector(U, -U.z); n.normalize();
  const ey = U.clone().negate(), ex = ey.clone().cross(n).normalize();
  const q = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(ex, ey, n));
  P[`sh${side}`].quaternion.slerpQuaternions(ARMS.q0, q, w); P[`el${side}`].rotation.set(lerp(ARMS.e0, -th, w), 0, 0);
}
function groundFix(P, minY, pts) {                                 // lift or lower him so his lowest point sits at minY
  P.root.updateMatrixWorld(true); let m = 1e9; for (const o of pts) m = Math.min(m, wpos(o).y);
  P.root.position.y += minY - m; P.root.updateMatrixWorld(true);
}
const HANDCACHE = {};
// pose fielder `who` for play `id` at play time t (s since contact); returns { glove: world point the glove holds the ball at or null }
function poseFielder(id, t, P = FP[PLAYS[id].who]) {
  const pl = PLAYS[id], pn = PLAN[id], { F, tf, S, u, R, yawF, tr } = pn, t0 = 0.14;
  const thrTo = pl.thr.to === "b1" ? catchPt(id) : catchPt(id), dT = hz(thrTo.clone().sub(R)).normalize(), ySide = yawSide(dT);
  let pos, yaw, q, pitch = 0, minY = 0.07, lift = 0;
  const yawRun = yawFace(u), tAppr = tf - (pl.tech === "dive" ? 0.32 : 0.3);
  if (t <= t0) { pos = S.clone(); yaw = yawFace(hz(v3(0, 0, 0).sub(S)).normalize()); q = { ...READY_F }; }
  else if (t <= tf) {
    const k = (t - t0) / (tf - t0), e = pl.tech === "dive" || pl.tech === "charge" ? Math.pow(k, 1.5) : smooth(k) * 0.5 + k * 0.5;
    pos = S.clone().lerp(R, e);
    const spd = pn.run / (tf - t0), ph = pn.run * e / 7.0;
    q = mixPose(READY_F, runPose(ph, clamp(spd / 18, 0.4, 1)), smooth((t - t0) / 0.18));
    yaw = lerpAng(yawFace(hz(v3(0, 0, 0).sub(S)).normalize()), yawRun, smooth((t - t0) / 0.15));
    const wF = smooth((t - tAppr) / (tf - tAppr));
    const tech = pl.tech === "fore" ? F_FORE : pl.tech === "back" ? F_BACK : pl.tech === "charge" ? F_CHARGE : DIVEP;
    q = mixPose(q, tech, wF); yaw = lerpAng(yaw, yawF, wF);
    if (pl.tech === "dive") { pitch = 1.38 * smooth((t - tAppr) / 0.22); }
  } else {
    const dtF = t - tf, mom = pl.tech === "dive" ? 1.2 : pl.tech === "charge" ? 4.0 : 1.6;
    pos = R.clone().addScaledVector(u, mom * (1 - Math.exp(-dtF / 0.25)));
    const tech = pl.tech === "fore" ? F_FORE : pl.tech === "back" ? F_BACK : pl.tech === "charge" ? F_CHARGE : DIVEP;
    if (pl.tech === "dive") {                                       // down, up to his knees, up, then the throw
      const up = smooth((dtF - 0.45) / 0.4), st = smooth((dtF - 0.85) / 0.3);
      pitch = 1.38 * (1 - up); q = mixPose(mixPose(DIVEP, KNEEL, up), READY_F, st); yaw = lerpAng(yawF, ySide, smooth((dtF - 0.6) / 0.4));
    } else { q = mixPose(tech, READY_F, smooth(dtF / 0.3)); yaw = lerpAng(yawF, ySide, smooth((dtF - 0.08) / Math.max(0.12, tr - tf - 0.35))); }
    // the throw: side-on to the target, the trunk turning through it, a stride toward the target
    const kt = t - tr, wT = smooth((kt + 0.42) / 0.3);
    if (pl.thr.how !== "feed") {
      const T = herm(THROW_T.map(([kk, a, b]) => [kk, v3(a, b, 0)]), kt);
      q = mixPose(q, { ...(pl.thr.how === "jump" ? JUMPLEG : THROWLEG), lean: 22 + 18 * smooth((kt + 0.05) / 0.25), nod: -4, pelvisTwist: T.x, twist: T.y }, wT);
      pos.addScaledVector(dT, 2.2 * smooth((kt + 0.25) / 0.45));
      if (pl.thr.how === "jump") lift = 1.5 * Math.sin(Math.PI * clamp((kt + 0.32) / 0.62, 0, 1));
    } else { q = mixPose(q, { ...ONBAG, lean: 30, pelvisTwist: 25 * smooth((kt + 0.2) / 0.3) }, wT); }
    yaw = pl.thr.how === "feed" ? lerpAng(yaw, yawFace(dT) - 0.9, smooth((dtF) / 0.25)) : yaw;
  }
  P.root.position.copy(pos); P.root.rotation.set(pitch, yaw, 0, "YXZ");
  applyPose(P, q); P.root.updateMatrixWorld(true);
  // the glove: onto the ball as it arrives, holding it, then into the throwing hand
  let gloveTgt = null, wG = 0;
  if (t < tf + 0.02) { wG = smooth((t - (tf - 0.38)) / 0.3); gloveTgt = gAt(pl.hit, Math.min(t, tf)); if (t > tf - 0.38) gloveTgt = gAt(pl.hit, tf).clone().lerp(gloveTgt, clamp((tf - t) / 0.38, 0, 1) * 0); }
  else { wG = 1 - smooth((t - tf - 0.25) / 0.25); const chest = wpos(P.neck).add(v3(0, -0.9, 0)).addScaledVector(fwdOf(yaw), 0.9); gloveTgt = gAt(pl.hit, tf).clone().lerp(chest, smooth((t - tf) / 0.22)); }
  if (wG > 0.001) {
    const qs = P.shL.quaternion.clone(), es = P.elL.rotation.x;
    armIK(P, "L", gloveTgt, v3(0, -1, 0).addScaledVector(fwdOf(yaw), -0.3).normalize());
    P.shL.quaternion.slerpQuaternions(qs, P.shL.quaternion.clone(), wG); P.elL.rotation.x = lerp(es, P.elL.rotation.x, wG);
  }
  // the throwing arm
  if (t > tf) { const kt = t - tr; armKeyed(P, "R", pl.thr.how === "feed" ? FEED_K : THROW_K, kt, smooth((kt + 0.55) / 0.2)); }
  // feet (or body, in the dive) to the ground; the jump throw lifts him
  const pts = pitch > 0.2 ? [P.ftL, P.ftR, P.knL, P.knR, P.pelvis, P.neck, P.handL] : [P.ftL, P.ftR];
  groundFix(P, (pitch > 0.2 ? 0.45 : minY) + lift, pts);
  return { t, tf, tr };
}
// the throw's flight: from the hand at release to the receiver's glove; flight time from distance and speed
const THROWS = {};
function throwOf(id) {
  if (THROWS[id]) return THROWS[id]; const pl = PLAYS[id], pn = PLAN[id], P = FP[pl.who];
  poseFielder(id, pn.tr, P); const p0 = wpos(P.handR), p1 = catchPt(id), T = p0.distanceTo(p1) / (pl.thr.mph * 1.4667);
  const g = v3(0, -32.17, 0), v0 = p1.clone().sub(p0).multiplyScalar(1 / T).addScaledVector(g, -0.5 * T);
  return (THROWS[id] = { p0, p1, T, v0, g, ta: pn.tr + T });
}
const throwPos = (th, k) => th.p0.clone().addScaledVector(th.v0, k).addScaledVector(th.g, 0.5 * k * k);
// the receiver: at the bag (first base) or running to cover second; reaches for the throw with the glove
function poseReceiver(id, t) {
  const pl = PLAYS[id], th = throwOf(id), P = FP[pl.thr.to], from = PLAN[id].R;
  const bag = pl.thr.to === "b1" ? BAG1 : BAG2;
  let pos, yaw, q;
  if (pl.thr.to === "b1") { const d = hz(from.clone().sub(bag)).normalize(); pos = bag.clone().addScaledVector(d, 0.6); yaw = yawFace(d);
    q = mixPose(READY_F, RECEIVE, smooth((t - (th.ta - 0.55)) / 0.35)); }
  else {                                                            // covering second: runs to the bag, arrives before the throw
    const S = pl.thr.to === "ss" ? START.ss : START.b2, a0 = 0.25, a1 = Math.min(th.ta - 0.15, PLAN[id].tf + 0.4);
    const k = smooth((t - a0) / (a1 - a0)), tgt = bag.clone().add(v3(pl.thr.to === "ss" ? -1.2 : 1.2, 0, 0.6));
    pos = S.clone().lerp(tgt, k); const run = S.distanceTo(tgt);
    yaw = lerpAng(yawFace(hz(tgt.clone().sub(S)).normalize()), yawFace(hz(from.clone().sub(bag)).normalize()), smooth((t - a1 + 0.3) / 0.3));
    q = mixPose(mixPose(READY_F, runPose(run * k / 7, 0.8), smooth((t - a0) / 0.2) * (1 - smooth((t - a1 + 0.1) / 0.25))), ONBAG, smooth((t - a1 + 0.1) / 0.25));
    if (t <= a0) yaw = yawFace(hz(v3(0, 0, 0).sub(S)).normalize());
  }
  P.root.position.copy(pos); P.root.rotation.set(0, yaw, 0, "YXZ"); applyPose(P, q); P.root.updateMatrixWorld(true);
  const w = smooth((t - (th.ta - 0.4)) / 0.3);
  if (w > 0.001) { const tgt = t < th.ta ? th.p1.clone() : th.p1.clone().add(v3(0, -0.2 * smooth((t - th.ta) / 0.2), 0));
    const qs = P.shL.quaternion.clone(), es = P.elL.rotation.x; armIK(P, "L", tgt, v3(0, -1, 0)); P.shL.quaternion.slerpQuaternions(qs, P.shL.quaternion.clone(), w); P.elL.rotation.x = lerp(es, P.elL.rotation.x, w); }
  groundFix(P, 0.07, [P.ftL, P.ftR]);
}
function poseIdle(P, pos, look, q = READY_F) { P.root.position.copy(pos); P.root.rotation.set(0, yawFace(hz(look.clone().sub(pos)).normalize()), 0, "YXZ"); applyPose(P, q); groundFix(P, 0.07, [P.ftL, P.ftR]); }
// the scene at play time t for shot s (s.play = play id; t < 0 = the pitch on its way)
const TCON_S = PI_.fb.t_contact;
function setSceneS(t, s, v) {
  BB.scale.set(1, 1, 1);
  setLab(false); for (const P of Object.values(PLATES)) P.g.visible = false;
  BOARD.visible = false; COACH.root.visible = false; HAND.root.visible = false; RING_OP = 0; ZONE.visible = false; MARK.visible = MARKR.visible = false; CHASE.visible = false;
  GHOSTS.forEach((m) => (m.visible = false)); TR_KNOB.set([]); TR_TIP.set([]); TR_KNOB2.set([]); AR_INTENT.set(v3(), v3(), 0, 0); AR_STRAIGHT.set(v3(), v3(), 0, 0);
  HIPRING.visible = HIPHALO.visible = false; ROT.visible = false; barrelHL.material.opacity = 0; KNOBHL.material.opacity = 0; ROTARC.visible = false; ELBOWGLOW.material.opacity = 0;
  F_REAR.set(v3(), v3(0, 1, 0), 0, 0); F_LEAD.set(v3(), v3(0, 1, 0), 0, 0); SEP.visible = false;
  for (const b of Object.values(BONES)) b.forEach((m) => (m.visible = false)); for (const j of Object.values(JOINTS)) j.forEach((m) => (m.visible = false));
  U1.root.position.set(70, 0, -56); U1.root.rotation.y = Math.atan2(-70, 56); applyPose(U1, { drop: -0.7, lean: 26, nod: -6, hipL: [40, 16], hipR: [40, 16], knL: 48, knR: 48, shL: [30, 12, 0], elL: 50, shR: [30, 12, 0], elR: 50 });
  ump.root.position.set(0.5, 0, 6.0); ump.root.rotation.y = Math.PI; applyPose(ump, U_SET);
  const cq = catchPose("fb"); C.root.position.set(cq.cx, 0, 3.0); C.root.rotation.y = Math.PI; applyPose(C, cq);
  for (const [k, p] of Object.entries(HD)) if (k !== "ss" && k !== "b2") poseIdle(p, v3(...[homeD[k][0], 0, homeD[k][1]]), v3(0, 0, 0));
  const id = s.play, pl = PLAYS[id];
  // the pitcher, the pitch and the swing (contact at t = 0)
  posePitcher(t + TCON_S); pitcher.root.visible = true;
  batter.root.visible = t < 2.0 || !!s.batter; BAT.visible = batter.root.visible; dressHitter("B");
  if (batter.root.visible) poseHitter("B", clamp(t, -1.2, 0.6), t, t < 0 ? BB.position.clone() : CP.clone());
  // fielders
  if (s.talk) {                                                     // before the pitch: the middle infielders talk it over behind their gloves
    const a = v3(-3.6, 0, -131), b = v3(3.6, 0, -131), w = winOp(v, s.talk, 0.25);
    poseIdle(SSP, a, b, COMM); poseIdle(B2P, b, a, COMM);
    for (const [P, o] of [[SSP, b], [B2P, a]]) { const face = wpos(P.neck).add(v3(0, 0.25, 0)).addScaledVector(fwdOf(P.root.rotation.y), 0.45);
      const qs = P.shL.quaternion.clone(), es = P.elL.rotation.x; armIK(P, "L", face, v3(0, -1, 0.3)); P.shL.quaternion.slerpQuaternions(qs, P.shL.quaternion.clone(), w); P.elL.rotation.x = lerp(es, P.elL.rotation.x, w); }
    poseIdle(B1P, START.b1, v3(0, 0, 0));
  } else {
    if (pl.who === "ss") poseFielder(id, t, SSP); else poseFielder(id, t, B2P);
    if (pl.thr.to === "b1") { poseReceiver(id, t); if (pl.who === "ss") poseIdle(B2P, START.b2, v3(0, 0, 0)); }
    else { poseReceiver(id, t); poseIdle(B1P, START.b1, v3(0, 0, 0)); }
  }
  // the runner from first (force plays)
  R.root.visible = !!(pl && pl.runner) && !s.talk;
  if (R.root.visible) { const r0 = BAG1.clone().add(v3(-3, 0, -3)), r1 = BAG2.clone().add(v3(2.5, 0, 2.5)), k = clamp((t + 0.1) / 3.6, 0, 1);
    R.root.position.copy(r0.clone().lerp(r1, k)); R.root.rotation.set(0, yawFace(hz(r1.clone().sub(r0)).normalize()), 0, "YXZ"); applyPose(R, runPose(k * 90 / 7, 0.9)); groundFix(R, 0.07, [R.ftL, R.ftR]); }
  // the ball: the pitch, the grounder, in the glove, in the hand, the throw, in the receiver's glove
  BB.visible = !s.talk; STREAK.forEach((m) => (m.visible = false)); FLASH.material.opacity = 0; BGLOW.material.opacity = 0;
  if (!s.talk) {
    const P = FP[pl.who], tf = PLAN[id].tf, tr = PLAN[id].tr, th = throwOf(id);
    poseFielder(id, t, P);                                          // re-pose (throwOf may have posed him elsewhere)
    if (pl.thr.to === "b1" || true) poseReceiver(id, t);
    let bp;
    if (t < 0) bp = pathAt(PI_.fb.path, Math.max(0, t + TCON_S));
    else if (t < tf) bp = gAt(pl.hit, t);
    else if (t < tr - 0.3) bp = wpos(P.handL).addScaledVector(fwdOf(P.root.rotation.y), 0.12);
    else if (t < tr) bp = wpos(P.handR);
    else if (t < th.ta) bp = throwPos(th, t - tr);
    else bp = wpos(FP[pl.thr.to].handL).add(v3(0, 0, 0));
    BB.position.copy(bp); BB.quaternion.setFromAxisAngle(v3(1, 0, 0), t * 30);
    if (s.streak && t > 0) STREAK.forEach((m, i) => { const d = (i + 1) * 0.012, tt = t - d; if (tt <= 0) return; m.visible = true;
      m.position.copy(tt < tf ? gAt(pl.hit, tt) : tt > tr && tt < th.ta ? throwPos(th, tt - tr) : bp); });
    if (t > 0 && t < 0.05) { FLASH.position.copy(CP); FLASH.scale.setScalar(0.9 + t * 10); FLASH.material.opacity = 0.9 * (1 - t / 0.05); }
    BGLOW.position.copy(BB.position); BGLOW.material.opacity = s.bglow ? 0.9 : 0;
  }
  setRange(s, v, t); setRoutes(s, v, t); setCover(s, v, t);
  SUP = 0.5; KNOW = t;
}
// the shortstop's range on the dirt (overhead): a soft fan from up the middle to deep in the hole
const RANGE = (() => {
  const shp = new THREE.Shape(), pts = []; const c = v3(0, 0, 0);
  for (let a = -33; a <= -2; a += 1) { const r = 158, rr = a < -28 ? 158 : 160; pts.push([Math.sin(a * D2R) * rr, -Math.cos(a * D2R) * rr]); }
  for (let a = -2; a >= -33; a -= 1) { const r = 104; pts.push([Math.sin(a * D2R) * r, -Math.cos(a * D2R) * r]); }
  shp.moveTo(pts[0][0], pts[0][1]); for (const p of pts.slice(1)) shp.lineTo(p[0], p[1]);
  const m = new THREE.Mesh(new THREE.ShapeGeometry(shp), new THREE.MeshBasicMaterial({ color: 0x56d1ff, transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide, toneMapped: false }));
  m.rotation.x = Math.PI / 2; m.position.y = 0.12; m.renderOrder = 4; scene.add(m); return m; })();
function setRange(s, v) { const o = winOp(v, s.range, 0.4); RANGE.visible = o > 0.01; RANGE.material.opacity = 0.3 * o; }
// his routes to each ball (they stay drawn), the spot he fields each one
const ROUTE = {}; const ROUTEC = { mid: 0x3dd68c, hole: 0xff6a3d, chop: 0xffd84d };
for (const id of Object.keys(ROUTEC)) { ROUTE[id] = makeTrail(ROUTEC[id], 0.32); }
function setRoutes(s, v, t) {
  for (const id of Object.keys(ROUTE)) {
    const spec = s.routes?.[id]; if (!spec) { ROUTE[id].set([]); continue; }
    const pn = PLAN[id], upto = s.play === id ? clamp(t, 0, pn.tf) : (spec.done ? pn.tf : 0), pts = [];
    for (let tt = 0.14; tt <= upto + 1e-6; tt += 0.04) { const k = (tt - 0.14) / (pn.tf - 0.14), e = PLAYS[id].tech === "dive" || PLAYS[id].tech === "charge" ? Math.pow(k, 1.5) : smooth(k) * 0.5 + k * 0.5;
      const p = pn.S.clone().lerp(pn.R, e); p.y = 0.3; pts.push(p); }
    ROUTE[id].set(pts, winOp(v, spec.v ?? [-1, 1e9], 0.2));
  }
}
// who covers second: a ring on the bag in the coverer's colour, and an arrow on the dirt from him to the bag
const COVRING = ringM(0xffd84d, 0.95, 2.2, 0.12); COVRING.rotation.x = Math.PI / 2; scene.add(COVRING);
const COVARROW = makeArrow(0xffd84d);
function setCover(s, v, t) {
  const o = winOp(v, s.cover, 0.25); COVRING.visible = o > 0.01; if (!COVRING.visible) { COVARROW.set(v3(), v3(), 0, 0); return; }
  COVRING.position.copy(BAG2).add(v3(0, 0.15, 0)); COVRING.material.opacity = 0.95 * o; COVRING.scale.setScalar(1 + 0.06 * Math.sin(v * 8));
  const who = s.cover_who === "ss" ? (s.play === "b2" ? START.ss : START.ss) : START.b2;
  COVARROW.set(v3(), v3(), 0, 0);
}
// cameras that follow a player or the ball
const followTgt = (who) => who === "ball" ? BB.position.clone() : who === "mitt" ? wpos(C.handL) : who === "catcher" ? wpos(C.pelvis) : who === "runner" ? wpos(R.pelvis) : wpos(FP[who] ? FP[who].pelvis : SSP.pelvis);
CAMS.follow2 = (u, t, s) => { const g = followTgt(s.who); return [g.clone().add(A(s.off)), g.clone().add(A(s.lo ?? [0, 0, 0])), lerp(s.f0 ?? 40, s.f1 ?? s.f0 ?? 40, easeIO(u))]; };
CAMS.chase = (u, t, s) => { const id = s.play, th = throwOf(id), tr = PLAN[id].tr, k = clamp(t - tr, 0, th.T), b = throwPos(th, k), d = th.p1.clone().sub(th.p0).normalize();
  const cpos = b.clone().addScaledVector(d, -(s.back ?? 7)).add(v3(0, s.rise ?? 2.2, 0)).add(hz(d).cross(v3(0, 1, 0)).normalize().multiplyScalar(s.side ?? 2.5));
  return [cpos, b.clone().addScaledVector(d, 6), s.f0 ?? 44]; };
Object.assign(PINH, { ss: () => headTop(SSP), b2: () => headTop(B2P), b1: () => headTop(B1P), bag2: () => BAG2.clone().add(v3(0, 3.5, 0)), sball: () => BB.position.clone().add(v3(0, 1.2, 0)) });

// ================================================================== catcher: receiving, blocking, the steal, the signs, the talk
// t = 0 is the moment the pitch reaches the mitt (z = 2 ft); the pitch is released at t = -flight. The mitt is solved onto the ball
// (two-bone IK) so glove and ball meet exactly; the block's rebound is simulated off his chest; the steal's throw flies from his hand at
// release to the second baseman's glove under gravity; the runner's slide is timed so the tag is down a hair before his foot reaches the bag.
const CPITCH = PLAY.pitches;
const cflight = (id) => CPITCH[id].flight;
const cBall = (id, t) => pathAt(CPITCH[id].path, Math.max(0, t + cflight(id)));
const CPOSE = {
  set: { ...CROUCH, shL: [62, 18, 0], elL: 40, shR: [20, 10, 0], elR: 50, nod: -18 },
  mid: { ...CROUCH, nod: -8, shL: [78, 12, 0], elL: 24, shR: [20, 10, 0], elR: 60 },
  low: { ...CROUCH, nod: -16, shL: [54, 10, 0], elL: 22, shR: [14, 10, 0], elR: 60 },
  lowaway: { ...CROUCH, nod: -12, shL: [58, 34, 0], elL: 16, shR: [14, 10, 0], elR: 60 },
  sign: { ...CROUCH, nod: -12, shL: [44, 34, 0], elL: 64, shR: [8, -14, -30], elR: 26 },
  block: { drop: -2.05, lean: 34, nod: 26, hipL: [8, 36], hipR: [8, 36], knL: 112, knR: 112, ankL: 40, ankR: 40, shL: [18, 6, 0], elL: 16, shR: [26, -6, 0], elR: 40 },
  pop: { drop: -0.6, lean: 18, nod: -2, twist: -40, hipL: [38, 14], hipR: [20, 14], knL: 44, knR: 32, shL: [70, 20, 0], elL: 40, shR: [-25, 75, 0], elR: 100 },
  step: { drop: -0.45, lean: 10, twist: -60, look: 0, nod: -4, hipL: [40, 10], hipR: [-12, 14], knL: 30, knR: 24, shL: [82, 20, 0], elL: 30, shR: [-35, 78, 0], elR: 95 },
  rel: { drop: -0.6, lean: 30, twist: 30, nod: 6, shL: [20, 30, 0], elL: 60, shR: [165, 20, 0], elR: 15, hipL: [46, 8], hipR: [-26, 10], knL: 40, knR: 30 },
  fol: { drop: -0.8, lean: 46, twist: 48, nod: 10, shL: [10, 30, 0], elL: 70, shR: [55, -25, 0], elR: 25, hipL: [55, 8], hipR: [10, 10], knL: 52, knR: 70 },
  stand: { ...STAND, lean: 6, nod: -2, shL: [10, 10, 0], elL: 40, shR: [10, 10, 0], elR: 30 },
  point: { ...STAND, lean: 4, nod: -2, twist: -25, shL: [12, 10, 0], elL: 40, shR: [118, 28, 0], elR: 8 },        // the right arm out, pointing
  wave: { ...STAND, lean: 4, nod: -2, twist: 25, shL: [12, 10, 0], elL: 40, shR: [96, -22, 0], elR: 30 },          // sweeping the arm back across
  up: { ...STAND, lean: 10, nod: -6, hipL: [14, 8], hipR: [14, 8], knL: 22, knR: 22, shL: [20, 10, 0], elL: 45, shR: [18, 10, 0], elR: 40 },
};
const XPOSE = {   // the second baseman's tag, the runner's slide and lead
  recv: { drop: -0.6, lean: 20, nod: -6, hipL: [36, 18], hipR: [36, 18], knL: 40, knR: 40, shL: [80, 0, 0], elL: 15, shR: [40, 10, 0], elR: 60 },
  tag: { drop: -1.5, lean: 50, nod: 14, hipL: [80, 30], hipR: [60, 30], knL: 96, knR: 84, shL: [60, -10, 0], elL: 10, shR: [40, 10, 0], elR: 60 },
  slide: { drop: -2.45, pelvisTilt: 0, lean: -48, hipL: [78, 4], hipR: [52, 4], knL: 8, knR: 62, shL: [70, 30, 0], shR: [40, 30, 0], elL: 20, elR: 30, nod: 30 },
  lead: { drop: -0.75, lean: 28, look: -70, hipL: [42, 22], hipR: [42, 22], knL: 52, knR: 52, shL: [18, 14, 0], shR: [18, 14, 0], elL: 25, elR: 25, nod: -18 },
};
const FIRSTB = v3(63.64, 0, -63.64), SECONDB = v3(0, 0, -127.28), TO_2ND = SECONDB.clone().sub(FIRSTB).normalize();
const TAG_PT = v3(0.9, 1.4, -125.6), COVER_B2 = v3(-1.3, 0, -126.6), B2_HOME = v3(26, 0, -116);
const ikBlend = (P, side, tgt, pole, w) => {                        // the arm toward its target, blended in from its posed rotation
  if (w <= 0.001) return;
  const qs = P[`sh${side}`].quaternion.clone(), es = P[`el${side}`].rotation.x;
  armIK(P, side, tgt, pole);
  P[`sh${side}`].quaternion.slerpQuaternions(qs, P[`sh${side}`].quaternion.clone(), w); P[`el${side}`].rotation.x = lerp(es, P[`el${side}`].rotation.x, w);
};
const MITT = (extra = v3(0, 0.02, -0.14)) => wpos(C.handL).add(extra);
// the catcher receiving pitch `id` (t = 0 at the mitt); `base` is his crouch; the mitt goes where the ball will be, a hair early, and gives a little
function poseCRecv(id, t, base, o = {}) {
  const E = cBall(id, 0), cx = E.x + 0.45;
  C.root.position.set(cx, 0, 3.0); C.root.rotation.set(0, Math.PI, 0);
  applyPose(C, base); C.root.updateMatrixWorld(true);
  const rest = wpos(C.handL);
  const dz = v3(0, 0, o.depth ?? 0), chase = cBall(id, Math.min(t + (o.lead ?? 0.07), 0)).add(dz), give = v3(0, 0, 0.14 * Math.exp(-Math.max(0, t) * 9));       // o.depth: the mitt's face a little behind the ball, so it shows
  const tgt = rest.clone().lerp(t < 0 ? chase : E.clone().add(dz).add(give), smooth((t + (o.from ?? 0.55)) / 0.3));
  ikBlend(C, "L", tgt, v3(-0.45, -1, 0.35).normalize(), (o.w ?? 1) * smooth((t + (o.from ?? 0.55)) / 0.3));
  C.root.updateMatrixWorld(true);
}
// the block: down onto his knees with his chest over the ball; the rebound off his body is simulated (gravity, a dead dirt bounce)
const BLOCKQ = (t) => keyed([[-0.5, CPOSE.set], [-0.06, CPOSE.block], [1.3, CPOSE.block], [1.9, CPOSE.set]], t);
function poseCBlock(t) {
  const id = "cdirt", E = cBall(id, 0);
  C.root.position.set(E.x + 0.2, 0, 3.0 - 1.0 * smooth((t + 0.34) / 0.3)); C.root.rotation.set(0, Math.PI, 0);
  applyPose(C, BLOCKQ(t)); C.root.updateMatrixWorld(true);
}
let BLK = null;
function blockPlan() {
  if (BLK) return BLK;
  poseCBlock(0.0);                                                  // the body at the block
  const tc = C.spine.children[0]; tc.updateWorldMatrix(true, false);
  const fwd = v3(0, 0, -1).applyQuaternion(C.root.quaternion).applyAxisAngle(v3(1, 0, 0), 0);   // he faces the pitcher: -z
  const front = tc.localToWorld(v3(0, -0.15, -0.5));                // the front of his pad, a little below the middle of the chest
  let kc = cflight("cdirt");                                         // the first moment the ball is at (or past) his pad
  const P = CPITCH.cdirt.path; const n = P.p.length;
  let ic = -1; for (let i = 1; i < n; i++) { const q = V(P.p[i]); if (q.z >= front.z && i / P.hz > CPITCH.cdirt.bounce_t) { ic = i; break; } }
  if (ic < 0) ic = n - 1;
  const hit = V(P.p[ic]), v0 = V(P.p[ic]).sub(V(P.p[ic - 1])).multiplyScalar(P.hz);
  // the rebound: mostly dead, a little back toward the pitcher, a little down; then bounces and rolls out in front of him
  let p = hit.clone(), v = v3(v0.x * 0.18, -Math.abs(v0.y) * 0.1 - 2.0, -Math.abs(v0.z) * 0.14 - 1.5);
  const path = [p.clone()]; let rolling = false; const dt = 1 / 240;
  for (let i = 0; i < 480; i++) {
    if (rolling) { const sp = Math.hypot(v.x, v.z); const dec = Math.min(sp, 3.2 * dt); if (sp > 1e-6) { v.x -= v.x / sp * dec; v.z -= v.z / sp * dec; } v.y = 0; }
    else v.y -= 32.17 * dt;
    p.addScaledVector(v, dt);
    if (!rolling && p.y < 0.121 && v.y < 0) { p.y = 0.121; if (Math.abs(v.y) < 2.0) { v.y = 0; rolling = true; } else { v.y = -v.y * 0.35; v.x *= 0.6; v.z *= 0.6; } }
    path.push(p.clone());
  }
  return (BLK = { tc: ic / P.hz - cflight("cdirt"), hit, path, front });
}
function blockBall(t) {
  const B = blockPlan();
  if (t < B.tc) return cBall("cdirt", t);
  const i = Math.min(B.path.length - 1, Math.round((t - B.tc) * 240)); return B.path[i].clone();
}
// the steal: he catches high, comes up, steps and throws; the runner is timed so the tag is down just before his foot reaches the bag
const S_REL = 0.75, S_MPH = 82;
function poseCSteal(t) {
  const id = "csteal", E = cBall(id, 0), cx = E.x + 0.45;
  const cq = keyed([[-0.45, CPOSE.set], [0, CPOSE.mid], [0.18, CPOSE.pop], [0.5, CPOSE.step], [S_REL, CPOSE.rel], [S_REL + 0.4, CPOSE.fol]], t);
  C.root.position.set(cx, 0, 3.0 - 2.6 * smooth((t - 0.1) / 0.7)); C.root.rotation.set(0, Math.PI, 0);
  applyPose(C, cq); C.root.updateMatrixWorld(true);
  if (t < 0.22) {                                                   // the mitt out to the pitch until the catch, then the pose takes over
    const rest = wpos(C.handL), chase = cBall(id, Math.min(t + 0.07, 0));
    const tgt = rest.lerp(t < 0 ? chase : E, smooth((t + 0.55) / 0.3));
    ikBlend(C, "L", tgt, v3(-0.45, -1, 0.35).normalize(), smooth((t + 0.55) / 0.3) * (1 - smooth((t - 0.05) / 0.17)));
    C.root.updateMatrixWorld(true);
  }
}
let STL = null;
function stealPlan() {
  if (STL) return STL;
  poseCSteal(S_REL); const p0 = wpos(C.handR), p1 = TAG_PT.clone(), T = p0.distanceTo(p1) / (S_MPH * 1.4667);
  const g = v3(0, -32.17, 0), v0 = p1.clone().sub(p0).multiplyScalar(1 / T).addScaledVector(g, -0.5 * T);
  const tTag = S_REL + T, L = FIRSTB.distanceTo(SECONDB) - 13 - 0.6;
  const sprint = (u) => 28.5 * (Math.max(0, u) - 0.62 * (1 - Math.exp(-Math.max(0, u) / 0.62)));
  let Trun = 0; while (sprint(Trun) < L) Trun += 0.005;
  const GOT = tTag + 0.1 - Trun;                                     // he gets there a hair after the tag is down
  return (STL = { p0, p1, T, v0, g, tTag, L, sprint, GOT, Trun });
}
const stealThrow = (t) => { const S = stealPlan(), k = t - S_REL; return S.p0.clone().addScaledVector(S.v0, k).addScaledVector(S.g, 0.5 * k * k); };
function poseB2Steal(t) {
  const S = stealPlan(), P = HD.b2, k = smooth((t - (S.GOT + 0.35)) / Math.max(0.3, S.tTag - 0.4 - (S.GOT + 0.35)));
  const pos = B2_HOME.clone().lerp(COVER_B2, k); P.root.position.copy(pos);
  P.root.rotation.set(0, lerpAng(Math.atan2(-pos.x, -pos.z), Math.atan2(0 - pos.x, 3 - pos.z), smooth((t - (S.tTag - 0.7)) / 0.4)), 0, "YXZ");
  const run = k < 0.02 || k > 0.98 ? 0 : 1;
  let q = mixPose(READY, runPose(((t + 3) * 2.4) % 1, 0.7), run);
  q = mixPose(q, XPOSE.recv, smooth((t - (S.tTag - 0.5)) / 0.3)); q = mixPose(q, XPOSE.tag, smooth((t - S.tTag) / 0.12));
  applyPose(P, q); P.root.updateMatrixWorld(true);
  ikBlend(P, "L", t < S.tTag ? S.p1.clone().add(v3(0, 0.2, 0.5)).lerp(S.p1, smooth((t - (S.tTag - 0.3)) / 0.3)) : S.p1, v3(0, -1, 0), smooth((t - (S.tTag - 0.6)) / 0.3));
  groundFix(P, 0.07, [P.ftL, P.ftR]);
}
function poseRunner(t, mode) {                                       // R: on first; "lead" (stands in his lead), or "steal" (goes, slides)
  const lead = FIRSTB.clone().addScaledVector(TO_2ND, 13);
  R.root.visible = true; R.root.rotation.set(0, Math.atan2(TO_2ND.x, TO_2ND.z), 0, "YXZ");
  if (mode === "steal") {
    const S = stealPlan(), s_ = Math.min(S.sprint(t - S.GOT), S.L + 1.4);
    R.root.position.copy(lead).addScaledVector(TO_2ND, s_);
    let q = t < S.GOT ? XPOSE.lead : runPose((s_ / 11) % 1, clamp(s_ / 24, 0.3, 1));
    if (s_ > S.L - 9) q = mixPose(q, XPOSE.slide, smooth((s_ - (S.L - 9)) / 3));
    applyPose(R, q);
  } else {
    R.root.position.copy(lead).addScaledVector(TO_2ND, 3 * smooth((t + 0.6) / 0.3) * (1 - smooth((t - 0.3) / 0.4)));
    applyPose(R, { ...XPOSE.lead, look: 0 });
  }
  groundFix(R, 0.07, [R.ftL, R.ftR]);
}
const C_FORE_M = C.elR.children[0];
// the scene for a catcher shot: s.c = { kind: "recv" | "block" | "steal" | "sign" | "talk" | "rest", id: pitch id, ... }
function setSceneC(t, s, v) {
  BB.scale.set(1, 1, 1);
  setLab(false); for (const P of Object.values(PLATES)) P.g.visible = false;
  BOARD.visible = false; COACH.root.visible = false; HAND.root.visible = false; C_FORE_M.visible = true; HAND.fore.visible = false; RING_OP = 0; ZONE.visible = false; MARK.visible = MARKR.visible = false; CHASE.visible = false;
  GHOSTS.forEach((m) => (m.visible = false)); TR_KNOB.set([]); TR_TIP.set([]); TR_KNOB2.set([]); AR_INTENT.set(v3(), v3(), 0, 0); AR_STRAIGHT.set(v3(), v3(), 0, 0);
  HIPRING.visible = HIPHALO.visible = false; ROT.visible = false; barrelHL.material.opacity = 0; KNOBHL.material.opacity = 0; ROTARC.visible = false; ELBOWGLOW.material.opacity = 0;
  F_REAR.set(v3(), v3(0, 1, 0), 0, 0); F_LEAD.set(v3(), v3(0, 1, 0), 0, 0); SEP.visible = false; RANGE.visible = false; COVRING.visible = false; COVARROW.set(v3(), v3(), 0, 0);
  for (const id of Object.keys(ROUTE)) ROUTE[id].set([]);
  for (const b of Object.values(BONES)) b.forEach((m) => (m.visible = false)); for (const j of Object.values(JOINTS)) j.forEach((m) => (m.visible = false));
  U1.root.position.set(70, 0, -56); U1.root.rotation.y = Math.atan2(-70, 56); applyPose(U1, { drop: -0.7, lean: 26, nod: -6, hipL: [40, 16], hipR: [40, 16], knL: 48, knR: 48, shL: [30, 12, 0], elL: 50, shR: [30, 12, 0], elR: 50 });
  ump.root.position.set(0.5, 0, 6.0); ump.root.rotation.y = Math.PI; applyPose(ump, U_SET); ump.root.visible = !s.noump;
  R.root.visible = false;
  const cc = s.c, kind = cc.kind, id = cc.id ?? "cfb", F = cflight(id);
  for (const [k, p] of Object.entries(HD)) { poseIdle(p, v3(homeD[k][0], 0, homeD[k][1]), v3(0, 0, 0)); }
  poseIdle(B1P, START.b1, v3(0, 0, 0));
  if (kind === "talk") {                                            // he stands, points the defense where to play; they adjust
    const a = smooth((t - cc.at[0]) / 0.5), b = smooth((t - cc.at[1]) / 0.5);
    C.root.position.set(0.15, 0, 2.4); C.root.rotation.set(0, Math.PI, 0);
    const cq = mixPose(mixPose(mixPose(CPOSE.set, CPOSE.up, smooth((t - (cc.at[0] - 0.7)) / 0.5)), CPOSE.point, a), CPOSE.wave, b);
    applyPose(C, cq); groundFix(C, 0.07, [C.ftL, C.ftR]);
    const look = t < cc.at[2] ? v3(-30, 0, -110) : FIRSTB.clone();   // his eyes: the infield, then first base
    C.root.updateMatrixWorld(true); C.spine.getWorldQuaternion(_q); _qi.copy(_q).invert();
    const d = look.clone().sub(C.neck.getWorldPosition(new THREE.Vector3())).applyQuaternion(_qi);
    C.neck.rotation.set(clamp(Math.atan2(-d.y, Math.hypot(d.x, d.z)), -0.6, 0.7), clamp(Math.atan2(d.x, d.z), -1.75, 1.75), 0, "YXZ");
    const shift = smooth((t - cc.at[0] - 0.25) / 0.9), shift2 = smooth((t - cc.at[1] - 0.25) / 0.9);       // the infield moves
    poseIdle(SSP, v3(-27 - 7 * shift + 5 * shift2, 0, -114 + 6 * shift - 3 * shift2), v3(0, 0, 0));
    poseIdle(B2P, v3(26 - 8 * shift - 4 * shift2, 0, -116 + 4 * shift), v3(0, 0, 0));
    poseIdle(HD.b3, v3(-58 - 4 * shift2, 0, -76 + 4 * shift2), v3(0, 0, 0));
    pitcher.root.position.copy(RUB).add(v3(0, 0, 0.1)); posePitcher(-1.35); pitcher.root.visible = true;
    poseRunner(t, "lead"); poseIdle(B1P, START.b1.clone().add(v3(-4, 0, 6)), FIRSTB.clone());
    batter.root.visible = true; BAT.visible = true; dressHitter("B"); poseHitter("B", -1.5, t, v3(0, 3, -40));
    BB.visible = false; STREAK.forEach((m) => (m.visible = false)); FLASH.material.opacity = 0; BGLOW.material.opacity = 0;
    SUP = 0.5; KNOW = t; return;
  }
  // the pitcher, the batter, the pitch
  posePitcher(t + F); pitcher.root.visible = true;
  batter.root.visible = true; BAT.visible = true; dressHitter("B");
  const ballNow = kind === "block" ? blockBall(t) : cBall(id, t);
  poseHitter("B", -1.5, t, t < 0 ? ballNow.clone() : v3(0, 3, -30));
  if (kind === "recv") poseCRecv(id, t, CPOSE[cc.base ?? "mid"], cc);
  else if (kind === "block") poseCBlock(t);
  else if (kind === "steal") { poseCSteal(t); poseB2Steal(t); poseRunner(t, "steal"); }
  else if (kind === "sign") {                                       // the sign between his thighs, the pitcher's nod
    C.root.position.set(0.15, 0, 3.0); C.root.rotation.set(0, Math.PI, 0); applyPose(C, CPOSE.sign); C.root.updateMatrixWorld(true);
    handOnCatcher(signAt(cc.seq, t));
    const nod = smooth((t - cc.nod) / 0.18) * (1 - smooth((t - cc.nod - 0.3) / 0.25));
    pitcher.neck.rotation.x += 0.4 * nod;
    poseRunner(t, "lead");
  } else { C.root.position.set(0.15, 0, 3.0); C.root.rotation.set(0, Math.PI, 0); applyPose(C, CPOSE.set); }
  if (cc.runner && kind !== "steal") poseRunner(t, "lead");
  C.root.updateMatrixWorld(true);
  // the ball: in the pitcher's hand, the pitch, then in the mitt / bouncing off him / in his hand / the throw / the second baseman's glove
  BB.visible = true; STREAK.forEach((m) => (m.visible = false)); FLASH.material.opacity = 0; BGLOW.material.opacity = 0;
  let bp;
  if (t + F < 0) bp = ballInFingers();
  else if (kind === "block") bp = blockBall(t);
  else if (t < 0) bp = cBall(id, t);
  else if (kind === "steal") {
    const S = stealPlan();
    if (t < 0.28) bp = MITT(); else if (t < S_REL) bp = wpos(C.handR); else if (t < S.tTag) { bp = stealThrow(t); if (t < S_REL + 0.04) bp.lerp(wpos(C.handR), 1 - (t - S_REL) / 0.04); }
    else bp = wpos(HD.b2.handL).add(v3(0, -0.05, 0));
  } else bp = MITT();
  if (t + F >= 0 && t + F < 0.012) bp.lerp(ballInFingers(), 1 - (t + F) / 0.012);
  BB.position.copy(bp); BB.quaternion.setFromAxisAngle(V(CPITCH[id].spin ?? [0, 0, -1]), CPITCH[id].rpm / 60 * 2 * Math.PI * Math.max(0, t + F) * (s.spinx ?? 1));
  if (s.streak && t + F > 0) STREAK.forEach((m, i) => { const d = (i + 1) * 0.006, tt = t - d; if (tt + F <= 0 || (kind !== "block" && tt > 0)) return; m.visible = true; m.position.copy(kind === "block" ? blockBall(tt) : cBall(id, tt)); });
  BGLOW.position.copy(BB.position); BGLOW.material.opacity = s.bglow ? 0.9 : 0;
  SUP = 0.5; KNOW = t;
}
CAMS.pride = (u, t, s) => { const id = s.pid, k = clamp(t + cflight(id), 0, cflight(id)), b = cBall(id, t), o = A(s.off ?? [-0.9, 0.5, -2.4]);
  const ahead = cBall(id, Math.min(0, t + 0.12)); return [b.clone().add(o), ahead.clone().lerp(v3(0.3, 2.6, 2.4), smooth((k - cflight(id) + 0.25) / 0.2)), lerp(s.f0 ?? 36, s.f1 ?? s.f0 ?? 36, easeIO(u))]; };
CAMS.schase = (u, t, s) => { const S = stealPlan(), k = clamp(t, S_REL, S.tTag), b = stealThrow(k), d = S.p1.clone().sub(S.p0).normalize();       // rides behind the throw
  const cpos = b.clone().addScaledVector(d, -(s.back ?? 9)).add(v3(0, s.rise ?? 2, 0)).add(hz(d).cross(v3(0, 1, 0)).normalize().multiplyScalar(s.side ?? 3));
  return [cpos, b.clone().addScaledVector(d, 8), s.f0 ?? 44]; };
CAMS.bchase = (u, t, s) => { const hs = s.hit, kk = clamp(t - hs.rel - TCON, 0, 5.5), path = HITS[hs.hit].path, b = pathAt(path, kk), d = pathAt(path, kk + 0.15).sub(b);   // trails behind the batted ball
  if (d.length() < 1e-4) d.set(0, 0, -1); d.normalize();
  return [b.clone().addScaledVector(d, -(s.back ?? 14)).add(v3(0, s.rise ?? 5, 0)), b.clone().addScaledVector(d, 6).add(v3(0, s.lift ?? 0.8, 0)), lerp(s.f0 ?? 40, s.f1 ?? s.f0 ?? 40, easeIO(u))]; };
CAMS.track = (u, t, s) => [mixV(A(s.c0), A(s.c1 ?? s.c0), easeIO(u)), (s.look === "mitt" ? wpos(C.handL) : BB.position.clone()).add(A(s.lo ?? [0, 0, 0])), lerp(s.f0 ?? 36, s.f1 ?? s.f0 ?? 36, easeIO(u))];

// ================================================================== the gym: a rubber floor, a rack, a dumbbell shelf, a barbell; both hitters back squat
// One rep is SQ_T seconds: down, then up. Both hitters do the same lift; the bigger one has more plates on the bar.
const GYM = new THREE.Group(); GYM.visible = false; scene.add(GYM);
const BARBELL = new THREE.Group(); GYM.add(BARBELL);
const PLATES_L = [], PLATES_R = [];
{
  const rubber = canvasTex(512, 512, (g, w, h) => { g.fillStyle = "#1a1d23"; g.fillRect(0, 0, w, h); for (let i = 0; i < 3200; i++) { g.fillStyle = `rgba(255,255,255,${0.02 + rnd() * 0.05})`; g.fillRect(rnd() * w, rnd() * h, 2, 2); } }, { repeat: [12, 12] });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(90, 90), new THREE.MeshStandardMaterial({ map: rubber, roughness: 0.85 })); floor.rotation.x = -Math.PI / 2; floor.position.y = 0.002; floor.receiveShadow = true; GYM.add(floor);
  const wood = new THREE.Mesh(new THREE.BoxGeometry(9, 0.12, 7.5), new THREE.MeshStandardMaterial({ color: 0x8a6a45, roughness: 0.6 })); wood.position.set(0, 0.06, 0.2); wood.receiveShadow = true; GYM.add(wood);
  const wall = new THREE.Mesh(new THREE.BoxGeometry(60, 18, 0.4), new THREE.MeshStandardMaterial({ color: 0x1b222c, roughness: 0.9 })); wall.position.set(0, 9, -9.5); GYM.add(wall);
  const mirror = new THREE.Mesh(new THREE.BoxGeometry(22, 7, 0.06), new THREE.MeshStandardMaterial({ color: 0x8fa3bb, roughness: 0.08, metalness: 0.9, envMap: ENV, envMapIntensity: 1.1 })); mirror.position.set(0, 5.6, -9.25); GYM.add(mirror);
  const stripe = new THREE.Mesh(new THREE.BoxGeometry(60, 0.5, 0.1), new THREE.MeshBasicMaterial({ color: 0xff6a3d })); stripe.position.set(0, 1.4, -9.28); GYM.add(stripe);
  const steel = new THREE.MeshStandardMaterial({ color: 0x2a2f38, roughness: 0.4, metalness: 0.7, envMap: ENV, envMapIntensity: 0.6 });
  for (const sx of [-1, 1]) { const up = new THREE.Mesh(new THREE.BoxGeometry(0.32, 8, 0.32), steel); up.position.set(sx * 3.1, 4.0, -2.4); up.castShadow = true; GYM.add(up);
    const hook = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.14, 0.5), steel); hook.position.set(sx * 2.95, 5.1, -2.2); GYM.add(hook); }
  const top = new THREE.Mesh(new THREE.BoxGeometry(6.5, 0.3, 0.34), steel); top.position.set(0, 8.0, -2.4); GYM.add(top);
  const shelf = new THREE.Mesh(new THREE.BoxGeometry(16, 0.3, 1.3), steel); shelf.position.set(-2.5, 1.7, -8.4); GYM.add(shelf);
  for (const sx of [-9.5, 4.5]) { const leg = new THREE.Mesh(new THREE.BoxGeometry(0.3, 1.7, 1.2), steel); leg.position.set(sx, 0.85, -8.4); GYM.add(leg); }
  for (let i = 0; i < 9; i++) { const g = new THREE.Group(), r = 0.2 + 0.016 * i; for (const sx of [-0.34, 0.34]) { const hd = new THREE.Mesh(new THREE.CylinderGeometry(r + 0.05, r + 0.05, 0.4, 6), new THREE.MeshStandardMaterial({ color: 0x15171b, roughness: 0.5 })); hd.rotation.z = Math.PI / 2; hd.position.x = sx; g.add(hd); }
    const hn = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.7, 8), steel); hn.rotation.z = Math.PI / 2; g.add(hn); g.position.set(-9.4 + i * 1.85, 1.7 + r + 0.15, -8.4); GYM.add(g); }
  const barM = new THREE.MeshStandardMaterial({ color: 0x9aa3ae, roughness: 0.3, metalness: 0.85, envMap: ENV, envMapIntensity: 0.8 }), plateM = new THREE.MeshStandardMaterial({ color: 0x14161a, roughness: 0.45, metalness: 0.2 }), rimM = new THREE.MeshStandardMaterial({ color: 0xc4352d, roughness: 0.5 });
  const bar = new THREE.Mesh(new THREE.CylinderGeometry(0.055, 0.055, 7.2, 16), barM); bar.rotation.z = Math.PI / 2; BARBELL.add(bar);
  for (const sx of [-1, 1]) { const sl = new THREE.Mesh(new THREE.CylinderGeometry(0.085, 0.085, 1.5, 16), barM); sl.rotation.z = Math.PI / 2; sl.position.x = sx * 2.75; BARBELL.add(sl);
    for (let i = 0; i < 5; i++) { const pl = new THREE.Mesh(new THREE.CylinderGeometry(0.74, 0.74, 0.2, 36), plateM); pl.rotation.z = Math.PI / 2; pl.position.x = sx * (2.15 + 0.22 * i); pl.castShadow = true;
      const rm = new THREE.Mesh(new THREE.TorusGeometry(0.7, 0.025, 8, 36), rimM); rm.rotation.y = Math.PI / 2; rm.position.x = sx * (2.15 + 0.22 * i + 0.105); pl.add(rm); rm.position.set(0, sx * 0.105, 0); rm.rotation.set(Math.PI / 2, 0, 0);
      BARBELL.add(pl); (sx < 0 ? PLATES_L : PLATES_R).push(pl); } }
}
const setPlates = (n) => { PLATES_L.forEach((m, i) => (m.visible = i < n)); PLATES_R.forEach((m, i) => (m.visible = i < n)); };
const SQ_T = 3.6;
const squatD = (t) => { const u = (((t % SQ_T) + SQ_T) % SQ_T) / SQ_T; return u < 0.5 ? smooth(u / 0.5) : smooth(1 - (u - 0.5) / 0.5); };
function poseSquat(w, t) {
  const d = squatD(t), b = BUILD[w], sc = b.s;
  applyBuild(w); SCB = sc; showHelmet(false);
  batter.root.position.set(0, 0.12, 0); batter.root.rotation.y = 0;
  applyPose(batter, { drop: -1.4 * d, lean: 36 * d, nod: -30 * d + 4 });
  batter.pelvis.position.z = -1.0 * d * sc; batter.root.updateMatrixWorld(true);
  const foot = (sg) => ({ ball: v3(sg * 0.98 * sc * (0.9 + 0.1 * b.t), 0.12, 0.35 * sc), yaw: sg * 0.3, heel: 0 });
  legIK(batter, "R", foot(-1)); legIK(batter, "L", foot(1)); batter.root.updateMatrixWorld(true);
  const ms = wpos(batter.shL).add(wpos(batter.shR)).multiplyScalar(0.5), bar = ms.clone().add(v3(0, 0.36 * sc, -0.2 * sc)), gx = 1.4 * sc * (0.92 + 0.08 * b.t);
  BARBELL.position.copy(bar);
  armIK(batter, "L", bar.clone().add(v3(gx, -0.02, 0)), v3(0.2, -1, -0.7).normalize()); armIK(batter, "R", bar.clone().add(v3(-gx, -0.02, 0)), v3(-0.2, -1, -0.7).normalize());
  SCB = 1;
}
function setSceneG(t, s, v) {
  BB.scale.set(1, 1, 1); setLab(true, true);
  BOARD.visible = false; COACH.root.visible = false; HAND.root.visible = false; R.root.visible = false; RING_OP = 0; ZONE.visible = false; MARK.visible = MARKR.visible = false; CHASE.visible = false;
  GHOSTS.forEach((m) => (m.visible = false)); TR_KNOB.set([]); TR_TIP.set([]); TR_KNOB2.set([]); AR_INTENT.set(v3(), v3(), 0, 0); AR_STRAIGHT.set(v3(), v3(), 0, 0);
  HIPRING.visible = HIPHALO.visible = false; ROT.visible = false; barrelHL.material.opacity = 0; KNOBHL.material.opacity = 0; ROTARC.visible = false; ELBOWGLOW.material.opacity = 0;
  F_REAR.set(v3(), v3(0, 1, 0), 0, 0); F_LEAD.set(v3(), v3(0, 1, 0), 0, 0); SEP.visible = false; RANGE.visible = false; COVRING.visible = false; COVARROW.set(v3(), v3(), 0, 0);
  for (const id of Object.keys(ROUTE)) ROUTE[id].set([]);
  for (const b of Object.values(BONES)) b.forEach((m) => (m.visible = false)); for (const j of Object.values(JOINTS)) j.forEach((m) => (m.visible = false));
  for (const P of Object.values(PLATES)) P.g.visible = false; pitcher.root.visible = false; BB.visible = false;
  const g = s.gym; dressHitter(g.who); BAT.visible = false; GL.visible = false; GRt.visible = false; batter.handL.children[0].visible = batter.handR.children[0].visible = true;
  batter.root.visible = true; BARBELL.visible = true; FILM.visible = false; if (GYM.userData.wood) GYM.userData.wood.visible = true; setPlates(g.plates); poseSquat(g.who, t);
  SUP = 0.5; KNOW = t;
}

// ================================================================== the balance marker: his base of support and where his weight is (an illustration)
const BALG = new THREE.Group(); BALG.visible = false; scene.add(BALG);
const BALPOLY = new THREE.Mesh(new THREE.BufferGeometry(), glowM(0x3dd68c, 0.3)); BALPOLY.renderOrder = 5; BALG.add(BALPOLY);
const BALDOT = new THREE.Mesh(new THREE.CircleGeometry(0.36, 28), glowM(0x3dd68c, 0.95)); BALDOT.rotation.x = -Math.PI / 2; BALDOT.renderOrder = 6; BALG.add(BALDOT);
const BALLINE = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 1, 8), glowM(0x3dd68c, 0.8)); BALLINE.renderOrder = 6; BALG.add(BALLINE);
function hull2(P) {                                                 // convex hull of [x, z] points (monotone chain)
  const q = P.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]), cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]), lo = [], up = [];
  for (const p of q) { while (lo.length >= 2 && cr(lo.at(-2), lo.at(-1), p) <= 0) lo.pop(); lo.push(p); }
  for (const p of q.slice().reverse()) { while (up.length >= 2 && cr(up.at(-2), up.at(-1), p) <= 0) up.pop(); up.push(p); }
  return lo.slice(0, -1).concat(up.slice(0, -1));
}
function setBalance(s, v, w, k) {
  const bo = winOp(v, s.bal, 0.2); BALG.visible = bo > 0.01; if (!BALG.visible) return;
  const f = feetAt(w, k), sc = BUILD[w]?.s ?? 1, pts = [];
  for (const ft of [f.rear, f.lead]) {
    if (ft.ball.y > 0.14 * sc) continue;                             // a foot in the air isn't holding him up
    const y = ft.yaw, d = [Math.sin(y), Math.cos(y)], pr = [Math.cos(y), -Math.sin(y)];
    for (const [a, b] of [[-0.65, 0.17], [-0.65, -0.17], [0.4, 0.17], [0.4, -0.17]]) pts.push([ft.ball.x + d[0] * a + pr[0] * b, ft.ball.z + d[1] * a + pr[1] * b]);
  }
  if (pts.length < 3) for (const ft of [f.rear, f.lead]) pts.push([ft.ball.x, ft.ball.z + 0.2], [ft.ball.x, ft.ball.z - 0.2]);
  const H = hull2(pts), com = wpos(batter.pelvis);
  const sh = new THREE.Shape(H.map(([x, z]) => new THREE.Vector2(x, -z))); BALPOLY.geometry.dispose(); BALPOLY.geometry = new THREE.ShapeGeometry(sh); BALPOLY.rotation.x = -Math.PI / 2; BALPOLY.position.y = 0.07;
  let inside = true, dmin = 1e9;                                     // inside the hull, or how far outside
  for (let i = 0; i < H.length; i++) { const a = H[i], b = H[(i + 1) % H.length], ex = b[0] - a[0], ez = b[1] - a[1], cr_ = ex * (com.z - a[1]) - ez * (com.x - a[0]);
    if (cr_ < 0) inside = false; const t_ = clamp(((com.x - a[0]) * ex + (com.z - a[1]) * ez) / (ex * ex + ez * ez + 1e-9), 0, 1); dmin = Math.min(dmin, Math.hypot(com.x - a[0] - ex * t_, com.z - a[1] - ez * t_)); }
  const dist = inside ? 0 : dmin, col = dist <= 0.35 * sc ? 0x3dd68c : dist <= 0.9 * sc ? 0xffd84d : 0xff4d4d;
  for (const m of [BALPOLY, BALDOT, BALLINE]) m.material.color.set(col);
  BALPOLY.material.opacity = 0.3 * bo; BALDOT.material.opacity = 0.95 * bo; BALLINE.material.opacity = 0.7 * bo;
  BALDOT.position.set(com.x, 0.1, com.z); BALLINE.position.set(com.x, com.y / 2, com.z); BALLINE.scale.set(1, com.y, 1);
  BAL_STATE = dist <= 0.35 * sc ? 0 : dist <= 0.9 * sc ? 1 : 2;
}
let BAL_STATE = 0;

// ================================================================== the film room: three screens play three professional swings; he studies them
const FCAM = new THREE.PerspectiveCamera(34, 16 / 9, 0.1, 2500);
const RTF = [0, 1, 2].map(() => new THREE.WebGLRenderTarget(640, 360, { samples: 4 })); RTF.forEach((r) => { r.texture.colorSpace = THREE.SRGBColorSpace; });
const FILM = new THREE.Group(); FILM.visible = false; GYM.add(FILM);
const FY = [2.5, 6.1, 9.7];                                          // three screens in a column: they fit a vertical frame
{
  const wallM = new THREE.Mesh(new THREE.BoxGeometry(0.4, 16, 18), new THREE.MeshStandardMaterial({ color: 0x141922, roughness: 0.9 })); wallM.position.set(9.9, 8, -0.2); FILM.add(wallM);
  RTF.forEach((r, i) => {
    const bez = new THREE.Mesh(new THREE.BoxGeometry(0.2, 3.5, 6.0), new THREE.MeshStandardMaterial({ color: 0x050608, roughness: 0.4 })); bez.position.set(9.6, FY[i], -0.2); FILM.add(bez);
    const m = new THREE.Mesh(new THREE.PlaneGeometry(5.6, 3.15), new THREE.MeshBasicMaterial({ map: r.texture, toneMapped: false })); m.position.set(9.49, FY[i], -0.2); m.rotation.y = -Math.PI / 2; FILM.add(m);
  });
}
GYM.userData.wood = GYM.children.find((o) => o.isMesh && o.geometry.type === "BoxGeometry" && o.geometry.parameters.width === 9);
function setSceneF(t, s, v) {
  const f = s.film, L = 2.4;
  f.clips.forEach((who, i) => {                                      // each clip: the swing on a loop, from the third-base-side chest view
    const tc = -1.0 + ((((t * (f.rate ?? 1) + i * 0.8) % L) + L) % L);
    setSceneH(tc, { hit: { who, rel: 0, hit: who } }, v);
    frame(FCAM, v3(10.5, 4.4, -0.3), v3(-2.6, 3.4, -0.4), 34, 16 / 9); setBokeh(0); closeLights(false, v3());
    renderer.setRenderTarget(RTF[i]); renderer.setScissorTest(false); renderer.setViewport(0, 0, 640, 360); renderer.render(scene, FCAM);
  });
  renderer.setRenderTarget(null);
  BB.scale.set(1, 1, 1); setLab(true, true);
  BOARD.visible = false; COACH.root.visible = false; HAND.root.visible = false; R.root.visible = false; RING_OP = 0; ZONE.visible = false; MARK.visible = MARKR.visible = false; CHASE.visible = false;
  GHOSTS.forEach((m) => (m.visible = false)); TR_KNOB.set([]); TR_TIP.set([]); TR_KNOB2.set([]); AR_INTENT.set(v3(), v3(), 0, 0); AR_STRAIGHT.set(v3(), v3(), 0, 0);
  HIPRING.visible = HIPHALO.visible = false; ROT.visible = false; barrelHL.material.opacity = 0; KNOBHL.material.opacity = 0; ROTARC.visible = false; ELBOWGLOW.material.opacity = 0;
  F_REAR.set(v3(), v3(0, 1, 0), 0, 0); F_LEAD.set(v3(), v3(0, 1, 0), 0, 0); SEP.visible = false; RANGE.visible = false; COVRING.visible = false; COVARROW.set(v3(), v3(), 0, 0); BALG.visible = false;
  for (const id of Object.keys(ROUTE)) ROUTE[id].set([]);
  for (const b of Object.values(BONES)) b.forEach((m) => (m.visible = false)); for (const j of Object.values(JOINTS)) j.forEach((m) => (m.visible = false));
  for (const P of Object.values(PLATES)) P.g.visible = false; pitcher.root.visible = false; BB.visible = false; BARBELL.visible = false; FILM.visible = true;
  if (GYM.userData.wood) GYM.userData.wood.visible = false;
  dressHitter("young"); batter.root.visible = true; showHelmet(true); BAT.visible = true; GL.visible = GRt.visible = true; batter.handL.children[0].visible = batter.handR.children[0].visible = false;
  const idx = clamp(Math.floor((t - (f.t0 ?? 0)) / (f.dwell ?? 1.6)), 0, 2);
  poseHitter("young", -1.5, t, v3(9.4, FY[idx], -0.2));
  SUP = 0.5; KNOW = t;
}

let KTR = null;
function renderAt(v) {
  const { s, t, u } = shotAt(v);
  const panes = s.panes ?? [{ rect: [0, 0, W, H] }];
  renderer.setScissorTest(panes.length > 1);
  panes.forEach((pn, i) => {
    const sh = { ...s, ...pn }, th = pn.vs ? pw(v, pn.vs, pn.ts) : t;
    const rk = pn.r1 ? smooth((v - pn.rw[0]) / (pn.rw[1] - pn.rw[0])) : 0, [x, y, w, h] = pn.rect.map((a, j) => Math.round(pn.r1 ? lerp(a, pn.r1[j], rk) : a));
    if (w < 2 || h < 2) return;
    BB2.visible = false; BGLOW2.material.opacity = 0; EYES.visible = false; TR_EXP.forEach((T) => T.set([]));
    if (sh.room) { renderClips(th, sh); setRoom(th, sh); }
    else (sh.c ? setSceneC : sh.gym ? setSceneG : sh.film ? setSceneF : (sh.hit || (sh.who && sh.who !== "ss" && sh.who !== "b2")) ? setSceneH : setSceneS)(th, sh, v);
    view(CAMS[sh.cam](u, th, sh, v), sh, w / h);
    if (!sh.room) tellRing(RING_OP, cam);
    if (sh.ballhand) { const L = A(sh.l); ballInHand(L.clone().add(v3(0, -0.42, 0)), cam.position, sh.roll ?? 0); }
    renderer.setScissorTest(panes.length > 1);
    renderer.setViewport(x, H - y - h, w, h); renderer.setScissor(x, H - y - h, w, h);
    if (sh.room) cam.updateMatrixWorld(true);                      // the camera lives in the field scene; the room render doesn't update it
    renderer.render(sh.room ? ROOM : scene, cam);
    for (const [id, key, pi] of CC.pins) if ((pi ?? 0) === i) pin(id, (PINH[key] ?? PINT[key])(), [x, y, w, h]);
  });
  drawTrace(KTR ?? KNOW); KTR = null; drawGauge(v);
  if ($("sup")) { const el = $("supk"); if (el) el.style.left = `${((1 - SUP) * 100).toFixed(1)}%`; }
  if ($("spd")) {                                                 // the speed label follows the shot's own clock: frozen, slowed, or neither
    const p0 = { ...s, ...(s.panes?.[0] ?? {}) }, vs = p0.vs, ts = p0.ts; let r = 1;
    for (let i = 1; i < vs.length; i++) if (v <= vs[i] || i === vs.length - 1) { r = (ts[i] - ts[i - 1]) / Math.max(1e-6, vs[i] - vs[i - 1]); break; }
    const sp = r < 0.002 ? "Freeze" : r < 0.9 ? "Slow motion" : ""; $("spd").textContent = sp; $("spd").style.opacity = sp ? 1 : 0; }
}

let last = -1;
function seek(time) { if (time === last) return; last = time; renderAt(time); }
window.addEventListener("hf-seek", (e) => seek(e.detail.time));
window.__fieldRender = renderAt;
window.__dbg = { BB2, EYES, TR_EXP, lookEyes, setSceneF, STY, BAL: () => BAL_STATE, BB, BGLOW, CAMS, setSceneH, setSceneG, BUILD, poseHitter, ROOT, C, cam, setSceneS, setSceneC, stealPlan, blockPlan, poseCRecv, poseCSteal, poseB2Steal, CPOSE, TAG_PT, SSP, B2P, B1P, PLAN, PLAYS, poseFielder, throwOf, HG, pitcher, posePitcher, ballInFingers, pbodyAt, ARMQ, pfoot, PLEAD, PDRIVE, FOLOFF, ROOT, H0, batAt, poseHitter, setSceneH, REACH: () => REACH_ERR, BODY, catchPose, drawBoard, ZONE, MARK, ROOM, SCREEN, RT, COACH, R, TELL, ballInHand, BALL_GRIP, renderClips, setRoom, batter, BAT, HL, HR, GL, GRt, wpos, v3, setScene, fixFor, PI_, handsMid, GRIP_Q, renderer, cam, scene, frame, setBokeh, closeLights, CC, C, ump };
document.fonts.ready.then(() => seek(window.__hfThreeTime || 0));
seek(window.__hfThreeTime || 0);
