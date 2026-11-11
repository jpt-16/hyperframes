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
    const foot = new THREE.Mesh(roundBox(0.38, 0.26, 0.98, 0.1, 6), shoe); foot.position.set(0, -0.06, 0.3); foot.castShadow = true; ft.add(foot);
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
const GHOSTS = []; for (let i = 0; i < 7; i++) { const m = new THREE.Mesh(batGeo, glowM(0xffd84d, 0.2 * (1 - i / 8))); m.visible = false; scene.add(m); GHOSTS.push(m); }
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
  if (b < 0) { g.textAlign = "center"; g.fillStyle = "#7f8a9a"; g.font = "800 44px Inter, Arial, sans-serif"; g.fillText("PITCH SPEED", 640, 300); g.fillStyle = "#ffffff"; g.font = "900 230px Inter, Arial, sans-serif"; g.fillText(msg, 640, 520); g.fillStyle = "#7f8a9a"; g.font = "700 40px Inter, Arial, sans-serif"; g.fillText("MPH  ·  FASTBALL", 640, 630); boardTex.needsUpdate = true; return; }
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
      const { fix, dc } = fixFor(ab.pk, ab.D); pos.add(fix);
      const kc = ab.check ? P.t_contact - ab.check : 1e9;                // a checked swing: he starts it, holds up before the bat crosses
      if (k <= kc) { q = swingPose(k, P.t_contact); if (k > -0.5) dir = slerpDir(swingKeys(P.t_contact, dc), k); }
      else { const u = smooth((k - kc - 0.12) / 0.55); q = mixPose(swingPose(kc, P.t_contact), B_STANCE, u); dir = slerpDir(swingKeys(P.t_contact, dc), kc).lerp(D_STANCE.clone().normalize(), u); }
      contact = V(P.contact);
    } else if (k > -0.5) q = takePose(k);
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
    const Pp = PI_[ab.pk], k = t - ab.rel, w = smooth((k + 0.1) / 0.35) * (1 - smooth((k - Pp.flight - 0.9) / 0.5));
    applyPose(C, mixPose(C_SET, C_REACH(Pp.cross[0] - 0.1, Pp.cross[1] - 2.45), w));
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
  pitcher.root.position.copy(ppos); pitcher.root.rotation.y = pyaw; applyPose(pitcher, pq);
  if (s.ring) RING_OP = keyed(s.ring.map(([a, b]) => [a, { u: b }]), t).u;
  if (s.bnod) batter.neck.rotation.x += 0;
  FORE = !!s.fore; batter.elL.visible = batter.elR.visible = !s.fore;
  // the bat path: translucent copies of the bat a few hundredths of a second back
  GHOSTS.forEach((m) => (m.visible = false));
  if (s.ghost && ab) for (let i = 0; i < GHOSTS.length; i++) {
    const tg = t - (i + 1) * (s.ghost ?? 0.014); if (tg < ab.rel + PI_[ab.pk].t_contact - 0.2) break;
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
const OBJ = { croot: () => COACH.root, broot: () => batter.root, bneck: () => batter.neck, bat: () => BAT, proot: () => pitcher.root, ball: () => BB, glove: () => pitcher.handL, chand: () => HAND.wrist, rneck: () => R.neck, pneck: () => pitcher.neck };
const objW = (o, p) => { const g = OBJ[o](); g.updateWorldMatrix(true, false); return g.localToWorld(A(p)); };
const CAMS = {
  world: (u, t, s) => [mixV(A(s.c0), A(s.c1 ?? s.c0), easeIO(u)), mixV(A(s.l), A(s.l1 ?? s.l), easeIO(u)), lerp(s.f0 ?? 36, s.f1 ?? s.f0 ?? 36, easeIO(u))],
  obj: (u, t, s) => [objW(s.o, mixV(A(s.c0), A(s.c1 ?? s.c0), easeIO(u)).toArray()), objW(s.lo ?? s.o, mixV(A(s.l), A(s.l1 ?? s.l), easeIO(u)).toArray()), lerp(s.f0 ?? 30, s.f1 ?? s.f0 ?? 30, easeIO(u))],
  aim: (u, t, s) => [mixV(A(s.c0), A(s.c1 ?? s.c0), easeIO(u)), objW(s.lo, s.l), lerp(s.f0 ?? 10, s.f1 ?? s.f0 ?? 10, easeIO(u))],
  // a world camera that turns to follow the ball once it's hit (k blends from the fixed look to the ball)
  follow: (u, t, s) => { const c = mixV(A(s.c0), A(s.c1 ?? s.c0), easeIO(u)), l0 = A(s.l), ab = s.ab, k = t - ab.rel - PI_[ab.pk].t_contact;
    const b = BB.position.clone(), w = smooth(k / (s.lag ?? 0.35)); return [c, l0.lerp(b, w * (s.fw ?? 1)), lerp(s.f0 ?? 36, s.f1 ?? s.f0 ?? 36, easeIO(u))]; },
};
function shotAt(v) {
  const L = CC.shots.list;
  const s = L.find((x) => v < x.b) || L.at(-1);
  return { s, t: pw(v, s.vs, s.ts), u: clamp((v - s.a) / (s.b - s.a), 0, 1) };
}

// ------------------------------------------------------------------ DOM overlays fed from the same clock
const $ = (id) => document.getElementById(id);
const PINT = { batter: () => headTop(batter), hands: () => batPt(CUR.hm ?? 0.3), knob: () => batPt(-0.02), bottom: () => batPt(GL.position.y - 0.14), top: () => batPt(GRt.position.y + 0.14),
  sweet: () => batPt(SWEET), end: () => batPt(BAT_LEN), lenmid: () => { BAT.updateMatrixWorld(true); return BAT.localToWorld(v3(0, (BAT_LEN + GL.position.y) / 2 + 0.3, -0.42)); },
  ball: () => BB.position.clone(), pitcher: () => headTop(pitcher), plate: () => v3(0, 0, -0.7), mark: () => MARK.position.clone().add(v3(0, 0.42, 0)), zone: () => v3(0, ZY1 + 0.35, PLATE_F), chase: () => v3(0, ZY1 + CYP + 0.35, PLATE_F), ump: () => headTop(ump),
  glove: () => wpos(pitcher.handL).add(v3(0, 0.95, 0)), runner: () => headTop(R), coach: () => headTop(COACH), chand: () => wpos(HAND.wrist).add(v3(0, 0.55, 0)),
  bhead: () => headTop(batter), scrA: () => SCREEN.localToWorld(v3(-1.6, 3.35, 0.05)), scrB: () => SCREEN.localToWorld(v3(-1.6, -0.25, 0.05)), scrLog: () => SCREEN.localToWorld(v3(3.55, 3.55, 0.05)), rp2: () => headTop(RP2), rcoach: () => headTop(RCOACH) };
function pin(id, p, rect) {
  const el = $(id); if (!el || !p) return;
  const q = p.clone().project(cam), [x0, y0, w, h] = rect, half = Math.min(270, w / 2 - 10);
  el.style.left = `${clamp(x0 + (q.x + 1) / 2 * w, x0 + half, x0 + w - half).toFixed(1)}px`; el.style.top = `${clamp(y0 + (1 - q.y) / 2 * h, y0 + 40, y0 + h - 20).toFixed(1)}px`;
}
function view(c, s, aspect) { cam.up.set(...(s.up ?? [0, 1, 0])); frame(cam, c[0], c[1], c[2], aspect); setBokeh(s.bokeh ?? 0); closeLights(!!s.close, c[1]); }
function renderAt(v) {
  const { s, t, u } = shotAt(v);
  const panes = s.panes ?? [{ rect: [0, 0, W, H] }];
  renderer.setScissorTest(panes.length > 1);
  panes.forEach((pn, i) => {
    const sh = { ...s, ...pn }, th = pn.vs ? pw(v, pn.vs, pn.ts) : t, [x, y, w, h] = pn.rect;
    if (sh.room) { renderClips(th, sh); setRoom(th, sh); }
    else setScene(th, sh);
    view(CAMS[sh.cam](u, th, sh, v), sh, w / h);
    if (!sh.room) tellRing(RING_OP, cam);
    if (sh.ballhand) { const L = A(sh.l); ballInHand(L.clone().add(v3(0, -0.42, 0)), cam.position, sh.roll ?? 0); }
    renderer.setScissorTest(panes.length > 1);
    renderer.setViewport(x, H - y - h, w, h); renderer.setScissor(x, H - y - h, w, h);
    if (sh.room) cam.updateMatrixWorld(true);                      // the camera lives in the field scene; the room render doesn't update it
    renderer.render(sh.room ? ROOM : scene, cam);
    for (const [id, key, pi] of CC.pins) if ((pi ?? 0) === i) pin(id, PINT[key](), pn.rect);
  });
  if ($("spd")) { const sp = s.speed === "slow" ? "Slow motion" : s.speed === "freeze" ? "Freeze" : ""; $("spd").textContent = sp; $("spd").style.opacity = sp ? 1 : 0; }
}

let last = -1;
function seek(time) { if (time === last) return; last = time; renderAt(time); }
window.addEventListener("hf-seek", (e) => seek(e.detail.time));
window.__fieldRender = renderAt;
window.__dbg = { drawBoard, ZONE, MARK, ROOM, SCREEN, RT, COACH, R, TELL, ballInHand, BALL_GRIP, renderClips, setRoom, batter, BAT, HL, HR, GL, GRt, wpos, v3, setScene, fixFor, PI_, handsMid, GRIP_Q, renderer, cam, scene, frame, setBokeh, closeLights, CC, C, ump };
document.fonts.ready.then(() => seek(window.__hfThreeTime || 0));
seek(window.__hfThreeTime || 0);
