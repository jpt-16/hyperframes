// "Why pitchers use the rosin bag": the ballpark and players in three.js, plus a close-up kit: a jointed hand, a seamed
// baseball, the rosin bag, rosin dust, sweat beads and a sunscreen bottle. Everything is a pure function of HyperFrames
// time (hf-seek), so each frame is exact and repeatable. Units are feet. Home plate's back point is the origin, +x
// points toward first base's side, -z toward center field. The pitches come from tools/physics.py via window.__PLAY.
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
const HAND = makeHand(); scene.add(HAND.root);
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

// ------------------------------------------------------------------ the rosin bag: a small sewn cloth pillow of powder, "ROSIN" printed on it
const BAG_DIM = v3(0.24, 0.075, 0.34);
function makeBag() {
  const g = new THREE.Group();
  const cloth = canvasTex(512, 768, (c, w, h) => {
    c.fillStyle = "#efece4"; c.fillRect(0, 0, w, h);
    c.globalAlpha = 0.18; c.strokeStyle = "#b8b2a4"; c.lineWidth = 1;
    for (let x = 0; x < w; x += 3) { c.beginPath(); c.moveTo(x, 0); c.lineTo(x, h); c.stroke(); }
    for (let y = 0; y < h; y += 3) { c.beginPath(); c.moveTo(0, y); c.lineTo(w, y); c.stroke(); }
    c.globalAlpha = 1;
    c.save(); c.translate(w / 2, h / 2); c.scale(-1, 1); c.rotate(-Math.PI / 2); c.fillStyle = "rgba(30,34,40,.78)"; c.font = "900 128px Inter, Arial, sans-serif"; c.textAlign = "center"; c.textBaseline = "middle"; c.fillText("ROSIN", 0, 0); c.restore();
    for (let k = 0; k < 1800; k++) { c.fillStyle = `rgba(255,255,255,${0.25 + rnd() * 0.4})`; c.fillRect(rnd() * w, rnd() * h, 1 + rnd() * 2, 1 + rnd() * 2); }
    const v = c.createRadialGradient(w / 2, h / 2, w * 0.2, w / 2, h / 2, w * 0.75); v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(120,100,80,.18)"); c.fillStyle = v; c.fillRect(0, 0, w, h);
  });
  const geo = roundBox(BAG_DIM.x, BAG_DIM.y, BAG_DIM.z, 0.034, 14), p = geo.attributes.position, uv = geo.attributes.uv;
  for (let i = 0; i < p.count; i++) {                             // pillow: thick in the middle, thin at the sewn edges; soft wrinkles
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i), ex = 1 - Math.pow(Math.abs(x) / (BAG_DIM.x / 2), 4), ez = 1 - Math.pow(Math.abs(z) / (BAG_DIM.z / 2), 4);
    const k = 0.25 + 0.75 * Math.sqrt(Math.max(0, ex * ez)), wr = 0.004 * Math.sin(x * 90 + z * 40) * Math.sin(z * 70 - x * 30);
    p.setY(i, y * k + (y > 0 ? wr : -wr * 0.5));
    uv.setXY(i, x / BAG_DIM.x + 0.5, z / BAG_DIM.z + 0.5);
  }
  geo.computeVertexNormals();
  const body = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ map: cloth, roughness: 0.96 }));
  body.castShadow = true; body.receiveShadow = true; g.add(body);
  const edge = new THREE.Mesh(roundBox(BAG_DIM.x + 0.018, 0.01, BAG_DIM.z + 0.018, 0.004, 4), new THREE.MeshStandardMaterial({ color: 0xe4dfd3, roughness: 0.95 })); g.add(edge);
  return g;
}
const BAG = makeBag(); scene.add(BAG);
const BAG0 = v3(0.7, 0, -63.4); BAG0.y = moundY(BAG0.x, BAG0.z) + BAG_DIM.y * 0.5;
const BAG_YAW = 0.5, BAG_TILT = Math.atan2(0.38, 3);             // lying on the back slope of the mound
// a powdery patch where it sits, and pebbles: close-ups of the dirt
const patchTex = canvasTex(1024, 1024, (c, w) => {
  c.clearRect(0, 0, w, w);
  for (let k = 0; k < 26000; k++) { const r = Math.hypot(rnd() - 0.5, rnd() - 0.5); const v = rnd(); c.fillStyle = v < 0.45 ? `rgba(92,56,32,${0.35 * (1 - r)})` : v < 0.9 ? `rgba(196,140,96,${0.3 * (1 - r)})` : `rgba(250,248,242,${0.5 * Math.max(0, 1 - r * 3.2)})`; c.fillRect(rnd() * w, rnd() * w, 1 + rnd() * 3, 1 + rnd() * 3); }
  const q = c.createRadialGradient(w / 2, w / 2, 0, w / 2, w / 2, w * 0.22); q.addColorStop(0, "rgba(245,242,235,.28)"); q.addColorStop(1, "rgba(245,242,235,0)"); c.fillStyle = q; c.fillRect(0, 0, w, w);
});
const PATCH = new THREE.Mesh(new THREE.PlaneGeometry(3, 3), new THREE.MeshStandardMaterial({ map: patchTex, transparent: true, depthWrite: false, roughness: 1 }));
PATCH.rotation.set(-Math.PI / 2 - BAG_TILT, 0, 0); PATCH.position.set(BAG0.x, BAG0.y - BAG_DIM.y * 0.5 + 0.012, BAG0.z); PATCH.receiveShadow = true; scene.add(PATCH);
{ const peb = new THREE.InstancedMesh(new THREE.DodecahedronGeometry(1, 0), new THREE.MeshStandardMaterial({ color: 0x8a6a52, roughness: 0.9 }), 90), m4 = new THREE.Matrix4();
  for (let i = 0; i < 90; i++) { const a = rnd() * 7, r = 0.25 + rnd() * 1.4, x = BAG0.x + Math.cos(a) * r, z = BAG0.z + Math.sin(a) * r, s = 0.003 + rnd() * 0.006;
    m4.compose(v3(x, moundY(x, z) + s * 0.4, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(rnd() * 3, rnd() * 3, rnd() * 3)), v3(s, s * 0.7, s)); peb.setMatrixAt(i, m4); }
  peb.receiveShadow = true; scene.add(peb); }

// ------------------------------------------------------------------ the sunscreen bottle (the illegal comparison only): a plain tube, no brand
function makeBottle() {
  const g = new THREE.Group();
  const lab = canvasTex(512, 512, (c, w, h) => {
    const gr = c.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, "#ff9a3c"); gr.addColorStop(1, "#ff6a2a"); c.fillStyle = gr; c.fillRect(0, 0, w, h);
    c.fillStyle = "#fff"; c.textAlign = "center"; c.font = "900 92px Inter, Arial, sans-serif"; c.fillText("SUN", w / 2, 210); c.fillText("SCREEN", w / 2, 300); c.font = "800 64px Inter, Arial, sans-serif"; c.fillText("SPF 50", w / 2, 400);
  });
  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.085, 0.1, 0.46, 32), new THREE.MeshPhysicalMaterial({ map: lab, roughness: 0.3, clearcoat: 0.8, envMap: ENV, envMapIntensity: 0.8 })); body.scale.z = 0.62; body.position.y = 0.23; g.add(body);
  const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.065, 0.1, 24), new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.35, clearcoat: 0.6, envMap: ENV })); cap.position.y = 0.51; g.add(cap);
  g.traverse((o) => { if (o.isMesh) o.castShadow = true; });
  const blob = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 12), gooM.clone()); blob.material.opacity = 1; blob.scale.set(0.07, 0.022, 0.05); blob.position.set(0.2, 0.01, 0.05); g.add(blob);
  return g;
}
const BOTTLE = makeBottle(); BOTTLE.visible = false; scene.add(BOTTLE);

// ------------------------------------------------------------------ rosin dust: particles, each with its own fixed random seed
function makeDust(n, size, color = 0xf7f4ee) {
  const geo = new THREE.BufferGeometry(), pos = new Float32Array(n * 3); geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  const mat = new THREE.PointsMaterial({ color, size, map: dotTex, transparent: true, depthWrite: false, opacity: 0 });
  const pts = new THREE.Points(geo, mat); pts.frustumCulled = false; scene.add(pts);
  const R = Array.from({ length: n }, (_, i) => { let s = (i + 1) * 9301 + 49297; const r = () => ((s = (s * 16807) % 2147483647) / 2147483647); return [r(), r(), r(), r(), r(), r()]; });
  return { pts, pos, R, n };
}
const PUFF = makeDust(260, 0.006), FALL = makeDust(160, 0.0045), MOTE = makeDust(120, 0.006);
// a puff from a squeeze: out of the cloth, spreading and drifting down, fading
function puffAt(D, origin, age, spread = 0.35, op = 0.9) {
  const on = age > 0 && age < 2.2; D.pts.visible = on; if (!on) return;
  for (let i = 0; i < D.n; i++) {
    const r = D.R[i], th = r[0] * Math.PI * 2, ph = Math.acos(2 * r[1] - 1), sp = spread * (0.3 + r[2]), dr = 1 - Math.exp(-age * 3.2);
    const dir = v3(Math.sin(ph) * Math.cos(th), Math.abs(Math.cos(ph)) * 0.8 + 0.2, Math.sin(ph) * Math.sin(th));
    const p = origin.clone().addScaledVector(dir, sp * dr / 3.2 * 3).add(v3(0, -0.05 * age * age * r[3], 0));
    D.pos.set([p.x, p.y, p.z], i * 3);
  }
  D.pts.geometry.attributes.position.needsUpdate = true; D.pts.material.opacity = op * (1 - smooth(age / 2.2)) * smooth(age / 0.06);
}
// dust falling off rubbing fingertips
function fallAt(D, origins, age, op = 0.8) {
  const on = age > 0 && age < 3; D.pts.visible = on; if (!on) return;
  for (let i = 0; i < D.n; i++) {
    const r = D.R[i], o = origins[i % origins.length], life = (age + r[0] * 1.2) % 1.2;
    const p = o.clone().add(v3((r[1] - 0.5) * 0.04 + (r[4] - 0.5) * 0.05 * life, -0.25 * life * (0.5 + r[2]), (r[3] - 0.5) * 0.04 + (r[5] - 0.5) * 0.05 * life));
    D.pos.set([p.x, p.y, p.z], i * 3);
  }
  D.pts.geometry.attributes.position.needsUpdate = true; D.pts.material.opacity = op * smooth(age / 0.2) * (1 - smooth((age - 2.4) / 0.6));
}
// motes hanging in the light around the bag
function motesAt(D, c, t, op = 0.55) {
  D.pts.visible = op > 0; if (!D.pts.visible) return;
  for (let i = 0; i < D.n; i++) { const r = D.R[i], a = r[0] * 7 + t * (0.15 + r[1] * 0.2);
    D.pos.set([c.x + Math.cos(a) * (0.1 + r[2] * 0.6), c.y + 0.05 + r[3] * 0.7 + 0.04 * Math.sin(t * 0.8 + r[4] * 6), c.z + Math.sin(a) * (0.1 + r[5] * 0.6)], i * 3); }
  D.pts.geometry.attributes.position.needsUpdate = true; D.pts.material.opacity = op;
}

// ------------------------------------------------------------------ grips (solved at load), the hand on the pitcher
const T_OPEN = aimThumb(v3(0.3, 0.27, 0.06), v3(0.02, 0.3, 0.25));
const OPEN = { w: [0, 0, 0], I: [10, 12, 6, 0], M: [10, 12, 6, 0], R: [12, 14, 8, 0], P: [14, 16, 8, 0], T: T_OPEN };
const RELAX = { w: [8, 0, 0], I: [22, 28, 14, 0], M: [26, 32, 16, 0], R: [30, 36, 18, 0], P: [34, 40, 20, 0], T: aimThumb(v3(0.2, 0.3, 0.13), v3(0.04, 0.34, 0.22), [8, 14, 10]) };
const FLICK = { w: [-18, 0, 0], I: [4, 6, 2, -2], M: [4, 6, 2, 0], R: [8, 10, 4, 2], P: [12, 14, 6, 4], T: aimThumb(v3(0.3, 0.3, 0.02), v3(0.02, 0.3, 0.2), [4, 6, 2]) };
const T_UNDER = (c) => aimThumb(c.clone().add(v3(-0.01, -BALL_R * 0.9, 0.0)), c, [0, 0, 0]);   // under the ball, opposite the fingers
const GRIP = {
  fb: { c: v3(0.03, 0.43, 0.15), q: new THREE.Euler(0.2, 0.0, 1.57), base: { ...OPEN, I: [0, 0, 0, -2], M: [0, 0, 0, 2], R: [0, 0, 0, 6], P: [0, 0, 0, 12] }, thumb: (c) => T_UNDER(c) },
  cb: { c: v3(0.035, 0.42, 0.15), q: new THREE.Euler(1.2, 0.3, 0.4), base: { ...OPEN, I: [0, 0, 0, -1], M: [0, 0, 0, 1], R: [0, 0, 0, 6], P: [0, 0, 0, 12] }, thumb: (c) => T_UNDER(c) },
  ch: { c: v3(0.0, 0.37, 0.17), q: new THREE.Euler(0.2, 0.9, 1.4), base: { ...OPEN, I: [0, 0, 0, -14], M: [0, 0, 0, 0], R: [0, 0, 0, 4], P: [0, 0, 0, 10] },
        thumb: (c) => aimThumb(c.clone().add(v3(0.07, -0.05, 0.05)), c, [0, 0, 0]) },
};
for (const g of Object.values(GRIP)) { g.pose = solveWrap({ ...g.base, T: g.thumb(g.c) }, sdSphere(g.c, BALL_R), { I: null, M: null, R: null, P: null, T: null }); g.qq = new THREE.Quaternion().setFromEuler(g.q); }
// the bag in the palm, held, then squeezed
const BAGH = { c: v3(0.0, 0.2, 0.088), rot: new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(v3(0, 1, 0), v3(0, 0, 1), v3(1, 0, 0))) };
const BAG_T = aimThumb(v3(0.06, 0.3, 0.16), v3(0.0, 0.2, 0.3), [0, 0, 0]);
const BAG_HOLD = solveWrap({ ...OPEN, T: BAG_T }, sdRoundBox(BAGH.c, v3(BAG_DIM.x / 2, BAG_DIM.y / 2 + 0.004, BAG_DIM.z / 2), 0.03, BAGH.rot), { I: null, M: null, R: null, P: null, T: null });
const BAG_SQZ = solveWrap({ ...OPEN, T: BAG_T }, sdRoundBox(BAGH.c.clone().add(v3(0, 0, -0.012)), v3(BAG_DIM.x / 2 * 0.95, BAG_DIM.y / 2 * 0.6, BAG_DIM.z / 2), 0.022, BAGH.rot), { I: null, M: null, R: null, P: null, T: null });
// rubbing the fingertips: the thumb pad slides over the index and middle pads
const RUB_BASE = { w: [10, 0, 0], I: [38, 52, 26, -2], M: [42, 56, 28, 2], R: [62, 78, 44, 4], P: [70, 84, 48, 8], T: T_OPEN };
function rubPose(phase) {
  const c = HAND.F; applyHand(RUB_BASE); HAND.root.position.set(0, 0, 0); HAND.root.quaternion.identity(); HAND.root.updateMatrixWorld(true);
  const a = c.I.tip.getWorldPosition(v3()), b = c.M.tip.getWorldPosition(v3()), mid = a.lerp(b, 0.5 + 0.45 * Math.sin(phase)); HAND.wrist.worldToLocal(mid);
  return solveWrap({ ...RUB_BASE, T: aimThumb(mid, mid.clone().add(v3(0, 0, -0.1)), [0, 0, 0]) }, sdSphere(mid, 0.012), { T: null });
}
const RUBS = Array.from({ length: 24 }, (_, i) => rubPose(i / 24 * Math.PI * 2));
const rubAt = (k) => { const x = ((k % 1) + 1) % 1 * 24, i = Math.floor(x); return mixHand(RUBS[i], RUBS[(i + 1) % 24], x - i); };

// the pitcher wears a navy undershirt; his right hand is the jointed hand
const PIT_FORE = pitcher.elR.children[0].children[0], PIT_HAND = pitcher.handR.children[0];
for (const el of [pitcher.elR, pitcher.elL]) { const m = el.children[0].children[0]; m.material = new THREE.MeshStandardMaterial({ color: SLEEVE, roughness: 0.8 }); m.scale.set(0.72, 1, 0.72); }
const RIG_ON = new THREE.Quaternion().setFromEuler(new THREE.Euler(0, Math.PI / 2, 0)).multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0, Math.PI)));
function handOnPitcher(on) {
  PIT_HAND.visible = !on; HAND.fore.visible = HAND.cuff.visible = !on;
  if (on) { pitcher.handR.add(HAND.root); HAND.root.position.set(0, 0.04, 0); HAND.root.quaternion.copy(RIG_ON); }
  else scene.add(HAND.root);
}

// ------------------------------------------------------------------ poses for the pitcher
const P_SET = { lean: 4, look: 80, nod: 4, shL: [42, 8, 0], elL: 105, shR: [38, -4, 0], elR: 112, hipL: [4, 6], hipR: [4, 6], knL: 8, knR: 8 };
const P_LIFT = { lean: -4, look: 80, shL: [48, 8, 0], elL: 100, shR: [44, -4, 0], elR: 108, hipL: [100, 4], knL: 105, hipR: [6, 6], knR: 14, drop: -0.15 };
const P_STRIDE = { lean: 6, look: 40, drop: -0.6, twist: -50, shL: [80, 35, 0], elL: 25, shR: [-55, 80, 0], elR: 85, hipL: [52, 4], knL: 28, hipR: [-28, 6], knR: 38 };
const P_REL = { lean: 42, nod: 8, drop: -1.0, twist: 28, shL: [12, 32, 0], elL: 85, shR: [168, 22, 0], elR: 8, hipL: [72, 4], knL: 22, hipR: [-18, 6], knR: 92 };
const P_FOLLOW = { lean: 62, nod: 18, drop: -1.25, twist: 48, shL: [8, 38, 0], elL: 95, shR: [58, -24, 0], elR: 22, hipL: [82, 4], knL: 38, hipR: [34, 6], knR: 84 };
const P_HOLD = { lean: 6, nod: 34, look: 4, shL: [22, 14, 0], elL: 40, shR: [22, -16, 0], elR: 96, hipL: [4, 6], hipR: [4, 6], knL: 8, knR: 8 };   // the ball out in front, looking at his grip
const P_WALK = (ph) => ({ ...STAND, lean: 8, nod: 8, hipL: [18 * Math.sin(ph), 5], hipR: [-18 * Math.sin(ph), 5], knL: 10 + 14 * Math.max(0, -Math.sin(ph)), knR: 10 + 14 * Math.max(0, Math.sin(ph)), shL: [-10 * Math.sin(ph), 10, 0], elL: 30, shR: [30, 12, 20], elR: 70 });
const P_BEND = { drop: -1.7, lean: 60, nod: 20, hipL: [100, 14], hipR: [92, 14], knL: 118, knR: 110, ankL: -30, ankR: -26, shL: [34, 16, 0], elL: 60, shR: [70, 8, 30], elR: 10 };
const P_RISE = { lean: 8, nod: 30, look: 4, shL: [24, 14, 0], elL: 60, shR: [22, -14, 0], elR: 92, hipL: [4, 6], hipR: [4, 6], knL: 8, knR: 8 };
const C_SET = { ...CROUCH, shL: [62, 18, 0], elL: 40, shR: [20, 10, 0], elR: 50, nod: -18 };
const C_MID = { ...CROUCH, nod: -8, shL: [78, 12, 0], elL: 24, shR: [20, 10, 0], elR: 60 };
const U_SET = { drop: -1.0, lean: 30, nod: -6, hipL: [52, 28], hipR: [52, 28], knL: 68, knR: 68, shL: [30, 20, 0], elL: 60, shR: [30, 20, 0], elR: 60 };
const U_BASE = { drop: -0.7, lean: 26, nod: -6, hipL: [40, 16], hipR: [40, 16], knL: 48, knR: 48, shL: [30, 12, 0], elL: 50, shR: [30, 12, 0], elR: 50 };
const BAT_SET = { drop: -0.35, lean: 18, look: 80, nod: -4, hipL: [22, 14], hipR: [22, 14], knL: 26, knR: 26, shL: [55, 6, 0], shR: [60, 34, 0], elL: 95, elR: 110, twist: 20 };
const BAT_TAKE = { ...BAT_SET, twist: 26, pelvisTwist: -8, hipL: [30, 18], knL: 34 };

// ------------------------------------------------------------------ the acts (play time t), what each shot shows
// pick: he walks back off the rubber to the bag, bends, picks it up, holds it, squeezes it (a puff), drops it, rubs his fingertips.
const PK = { walk: 0, bend: 1.15, grab: 1.7, up: 2.35, sq0: 3.35, sq1: 3.8, drop: 4.05, rub0: 4.25, rub1: 5.6 };
const WALK_FROM = v3(3.2, 0, -59.6);
let PICK_ROOT = null;                                             // where he stands to reach the bag (found at load)
function placePicker() {
  pitcher.root.position.set(0, 0, 0); pitcher.root.rotation.y = Math.PI * 0.94; applyPose(pitcher, P_BEND); handOnPitcher(true); applyHand(BAG_HOLD);
  pitcher.root.updateMatrixWorld(true); const h = HAND.wrist.localToWorld(BAGH.c.clone());
  PICK_ROOT = v3(BAG0.x - h.x, 0, BAG0.z - h.z); PICK_ROOT.y = moundY(PICK_ROOT.x, PICK_ROOT.z) + (BAG0.y - (h.y + moundY(PICK_ROOT.x, PICK_ROOT.z)));
}
placePicker();
const PICK_YAW = Math.PI * 0.94;
function holdBagInHand(q) {                                       // the bag in the palm, squeezed by q (0..1)
  HAND.wrist.add(BAG); BAG.position.copy(BAGH.c).add(v3(0, 0, -0.012 * q)); BAG.quaternion.copy(BAGH.rot); BAG.scale.set(lerp(1, 1.04, q), lerp(1, 0.62, q), 1);
}
function bagOnMound(off = v3(0, 0, 0), yaw = BAG_YAW) { scene.add(BAG); BAG.position.copy(BAG0).add(off); BAG.rotation.set(-BAG_TILT, yaw, 0, "YXZ"); BAG.scale.set(1, 1, 1); }
const tipsW = () => ["I", "M", "T"].map((k) => wpos(HAND.F[k].tip));
let STATE = { wet: 0, dust: 0, goo: 0 };
function setSkin({ wet = 0, dust = 0, goo = 0 }) {
  tipM.clearcoat = wet; tipM.clearcoatRoughness = 0.12; tipM.roughness = lerp(0.52, 0.28, wet); tipM.color.setHex(SKIN); tipM.color.lerp(new THREE.Color(0xf2ede4), dust * 0.35);
  dustM.opacity = 0.85 * dust; gooM.opacity = 0.92 * goo;
  for (const d of HAND.drops) { const s = d.userData.s * smooth(wet); d.visible = s > 1e-4; d.position.copy(d.userData.p); d.scale.setScalar(Math.max(s, 1e-5)); }
}
function actPick(t, s) {
  const wet0 = s.wet0 ?? 0;
  let pos, yaw = PICK_YAW, q, hq = RELAX, bagHeld = false, sq = 0;
  if (t < 0) { pos = WALK_FROM.clone(); pos.y = moundY(pos.x, pos.z); q = { ...STAND, nod: 10, shR: [30, 12, 20], elR: 60 }; yaw = yawTo(WALK_FROM, PICK_ROOT); }   // standing on the back of the mound
  else if (t < PK.bend) {                                        // walking back to the bag
    const u = clamp(t / PK.bend, 0, 1); pos = WALK_FROM.clone().lerp(PICK_ROOT, smooth(u)); pos.y = moundY(pos.x, pos.z);
    q = P_WALK(t * 7.5); yaw = lerp(yawTo(WALK_FROM, PICK_ROOT), PICK_YAW, smooth((u - 0.6) / 0.4));
  } else {
    pos = PICK_ROOT.clone();
    q = keyed([[PK.bend, P_WALK(PK.bend * 7.5)], [PK.grab, P_BEND], [PK.grab + 0.12, P_BEND], [PK.up, P_RISE]], t);
    if (t > PK.up) pos.y = moundY(pos.x, pos.z);
    else if (t > PK.grab) pos.y = lerp(PICK_ROOT.y, moundY(pos.x, pos.z), smooth((t - PK.grab) / (PK.up - PK.grab)));
    else pos.y = lerp(moundY(pos.x, pos.z), PICK_ROOT.y, smooth((t - PK.bend) / (PK.grab - PK.bend)));
  }
  pitcher.root.position.copy(pos); pitcher.root.rotation.y = yaw; applyPose(pitcher, q);
  handOnPitcher(true);
  // the hand
  if (t < PK.grab - 0.25) hq = RELAX;
  else if (t < PK.grab) hq = mixHand(OPEN, BAG_HOLD, smooth((t - PK.grab + 0.25) / 0.25) * 0.4);
  else if (t < PK.drop) {
    bagHeld = true; sq = smooth((t - PK.sq0) / 0.18) * (1 - smooth((t - PK.sq1 + 0.15) / 0.15));
    hq = mixHand(BAG_HOLD, BAG_SQZ, sq);
    if (s.bounce) { const b = Math.max(0, Math.sin((t - PK.up) * Math.PI * 2 / 0.42)); sq = Math.max(sq, b * 0.6); hq = mixHand(BAG_HOLD, BAG_SQZ, sq); }
  } else if (t < PK.rub0) hq = mixHand(BAG_HOLD, OPEN, smooth((t - PK.drop) / 0.2));
  else hq = mixHand(OPEN, rubAt((t - PK.rub0) / 0.55), smooth((t - PK.rub0) / 0.25));
  // his wrist turns the palm up a little to look at it after the drop
  hq = { ...hq, w: [lerp(10, 25, smooth((t - PK.up) / 0.4)), 0, lerp(0, 40, smooth((t - PK.drop) / 0.4))] };
  applyHand(hq);
  if (bagHeld) holdBagInHand(sq);
  else if (t >= PK.drop) {                                        // dropped: it falls back onto the mound by his feet
    const u = clamp((t - PK.drop) / 0.36, 0, 1), a = BAG0.clone().add(v3(0, 1.6, 0)); scene.add(BAG);
    pitcher.root.updateMatrixWorld(true); const from = HAND.wrist.localToWorld(BAGH.c.clone()), to = BAG0.clone().add(v3(0.25, 0, 0.3));
    if (!DROP_FROM[s.k]) DROP_FROM[s.k] = from.clone();
    const f = DROP_FROM[s.k]; BAG.position.copy(f).lerp(to, u); BAG.position.y = lerp(f.y, to.y, u * u); BAG.rotation.set(-BAG_TILT * u + (1 - u) * 1.2, BAG_YAW + 0.8 * (1 - u), 0, "YXZ"); BAG.scale.set(1, 1, 1);
  } else bagOnMound();
  // dust and sweat
  const dust = smooth((t - PK.grab - 0.1) / 0.5) * (s.dustMax ?? 1), wet = wet0 * (1 - smooth((t - PK.grab) / 0.7));
  setSkin({ wet, dust });
  pitcher.root.updateMatrixWorld(true);
  const bagC = bagHeld ? HAND.wrist.localToWorld(BAGH.c.clone()) : BAG.position.clone();
  puffAt(PUFF, bagC.add(v3(0, 0.04, 0)), t - (PK.sq0 + 0.1), 0.28, 0.85);
  if (s.bounce) puffAt(PUFF, HAND.wrist.localToWorld(BAGH.c.clone()), ((t - PK.up) % 0.42) + (t > PK.up && t < PK.drop ? 0.001 : -9), 0.18, 0.6);
  fallAt(FALL, tipsW(), t - PK.rub0, 0.8);
}
const DROP_FROM = {};
// hold: on the rubber, facing home, the ball out in front of him; sweat builds, the ball shifts in his fingers, he regrips
const HD_ = { wet0: 1.4, wet1: 3.0, slip0: 3.7, slip1: 4.05, lift: 5.0, reset: 6.3 };
function actHold(t, s) {
  pitcher.root.position.set(0, MOUND_H, -60.15); pitcher.root.rotation.y = 0; applyPose(pitcher, P_HOLD);
  handOnPitcher(true);
  const g = GRIP[s.kind ?? "fb"]; let hq = g.pose, slip = 0, ballQ = g.qq.clone(), off = v3(0, 0, 0);
  if (!s.dry) {
    slip = smooth((t - HD_.slip0) / (HD_.slip1 - HD_.slip0)) * (1 - smooth((t - HD_.lift - 0.5) / 0.8));
    const lift = smooth((t - HD_.lift) / 0.35) * (1 - smooth((t - HD_.reset) / 0.4));
    hq = mixHand(hq, { ...hq, I: hq.I.map((x, i) => (i < 3 ? x * 0.55 : x)), M: hq.M.map((x, i) => (i < 3 ? x * 0.55 : x)), R: hq.R.map((x, i) => (i < 3 ? x * 0.7 : x)) }, lift);
    hq = mixHand(hq, { ...hq, I: [hq.I[0] - 6, hq.I[1] - 10, hq.I[2] - 8, hq.I[3] - 3], M: [hq.M[0] - 6, hq.M[1] - 10, hq.M[2] - 8, hq.M[3] + 2] }, slip);
    ballQ.multiply(new THREE.Quaternion().setFromAxisAngle(v3(0, 0, 1), -0.32 * slip)); off.set(-0.012 * slip, -0.018 * slip, 0);
  }
  hq = { ...hq, w: [24, 0, 70] };
  applyHand(hq);
  HAND.wrist.add(BB); BB.position.copy(g.c).add(off); BB.quaternion.copy(ballQ); BB.visible = true;
  const wet = s.dry ? 0 : smooth((t - HD_.wet0) / (HD_.wet1 - HD_.wet0)) * (1 - smooth((t - HD_.lift - 2.5) / 1)) * 1;
  setSkin({ wet: s.dry ? 0 : wet, dust: s.dry ? 1 : 0 });
  bagOnMound();
}
// pitch: from the set, a leg kick, release at t = 0. Grip s.kind; the ball leaves his fingers onto the simulated path, spinning.
const DELIV = { set: -2.2, first: -1.05 };
const RELFIX = {};                                                // per pitch: where the ball really is in his fingers at release vs. the path's start
function pitcherDeliv(t, kind) {
  const F = 1.05;
  let q = P_SET, pos = v3(0, MOUND_H, -60.5), yaw = -Math.PI / 2;
  if (t > -F) {
    q = keyed([[-F, P_SET], [-0.75, P_LIFT], [-0.3, P_STRIDE], [0, P_REL], [0.35, P_FOLLOW], [1.2, { ...READY, look: 0 }]], t);
    const zp = lerp(-60.6, -57.6, smooth((t + 0.42) / 0.48)); pos = v3(0, MOUND_H * (zp > -59 ? 0.6 : 1), zp);
    yaw = lerp(-Math.PI / 2, 0, smooth((t + 0.58) / 0.58));
  }
  pitcher.root.position.copy(pos); pitcher.root.rotation.y = yaw; applyPose(pitcher, q);
  handOnPitcher(true);
  const g = GRIP[kind === "end" ? "fb" : kind];
  let hq = g.pose;
  if (t > -0.04) hq = mixHand(g.pose, FLICK, smooth((t + 0.04) / 0.1));
  hq = { ...hq, w: [lerp(-30, 40, smooth((t + 0.12) / 0.16)), 0, kind === "cb" ? lerp(0, -40, smooth((t + 0.2) / 0.2)) : kind === "ch" ? lerp(0, 25, smooth((t + 0.2) / 0.2)) : 0] };
  applyHand(hq);
  return g;
}
function ballInFingers(g) { pitcher.root.updateMatrixWorld(true); return HAND.wrist.localToWorld(g.c.clone()); }
for (const k of Object.keys(PI_)) { const g = pitcherDeliv(0, k); RELFIX[k] = ballInFingers(g).sub(REL0); const qq = new THREE.Quaternion(); HAND.wrist.getWorldQuaternion(qq); RELFIX[k + "_q"] = qq.multiply(g.qq); }
function flightAt(kind, t) {                                      // the simulated path, eased from the ball's spot in his fingers back onto the path in the first 0.15 s
  const P = PI_[kind], p = pathAt(P.path, t), w = 1 - smooth(t / 0.15); return p.add(RELFIX[kind].clone().multiplyScalar(w));
}
function actPitch(t, s) {
  const kind = s.kind ?? "fb", P = PI_[kind], g = pitcherDeliv(t, kind);
  pitcher.root.updateMatrixWorld(true);
  for (const m of STREAK) m.visible = false;
  blurB.visible = false;
  if (t < 0) { HAND.wrist.add(BB); BB.position.copy(g.c); BB.quaternion.copy(g.qq); }
  else {
    scene.add(BB);
    const tf = P.flight, tt = Math.min(t, tf), p = t < tf ? flightAt(kind, tt) : wpos(C.handL);
    BB.position.copy(p);
    const ax = V(P.spin), ang = P.rpm / 60 * 2 * Math.PI * Math.min(t, tf);
    BB.quaternion.copy(new THREE.Quaternion().setFromAxisAngle(ax, ang).multiply(RELFIX[kind + "_q"]));
    if (s.streak && t > 0 && t < tf) STREAK.forEach((m, i) => { const d = (i + 1) * 0.008; if (t - d > 0) { m.visible = true; m.position.copy(flightAt(kind, t - d)); } });
  }
  BB.visible = true;
  setSkin({ wet: 0, dust: s.dust ?? 1 });
  bagOnMound();
  // catcher, umpire, batter
  C.root.position.set(0.15, 0, 3.0); C.root.rotation.y = Math.PI; applyPose(C, keyed([[-0.6, C_SET], [P.flight - 0.05, C_MID], [P.flight + 0.6, C_MID]], t));
  ump.root.position.set(0.5, 0, 6.0); ump.root.rotation.y = Math.PI; applyPose(ump, U_SET);
  batter.root.position.set(-3.0, 0, -0.9); batter.root.rotation.y = Math.PI / 2; applyPose(batter, keyed([[P.flight - 0.6, BAT_SET], [P.flight - 0.2, BAT_TAKE], [P.flight + 0.5, BAT_TAKE]], t));
}
// rules: a hand held palm up beside the bag on the mound; legal (rosin dust) or illegal (rosin mixed with sunscreen)
const RULE_HAND = { q: new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(v3(0, 0, -1), v3(-1, 0, 0), v3(0, 1, 0))).premultiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(0.25, 0.35, -0.25))) };
function actRules(t, s) {
  pitcher.root.visible = false;
  handOnPitcher(false); HAND.root.visible = !s.noHand; HAND.root.position.copy(BAG0).add(v3(0.6, 0.32, 0.05)); HAND.root.quaternion.copy(RULE_HAND.q);
  applyHand({ ...RELAX, w: [-8, 0, 0], I: [6, 8, 4, -3], M: [6, 8, 4, 0], R: [8, 10, 6, 3], P: [10, 12, 8, 7], T: aimThumb(v3(0.26, 0.26, 0.05), v3(0.05, 0.3, 0.25), [4, 6, 4]) });
  bagOnMound(v3(0.1, 0, 0.05));
  const ill = !!s.illegal; BOTTLE.visible = ill;
  if (ill) { BOTTLE.position.copy(BAG0).add(v3(-0.4, -BAG_DIM.y * 0.5, 0.02)); BOTTLE.rotation.set(0, 0.6, 0); }
  setSkin({ wet: 0, dust: ill ? 0.6 : 1, goo: ill ? 1 : 0 });
  motesAt(MOTE, BAG0, t, 0.35);
}

// ------------------------------------------------------------------ one frame
function setScene(t, s) {
  for (const [k, p] of Object.entries(HD)) { const [x, z] = homeD[k]; p.root.position.set(x, 0, z); p.root.rotation.y = Math.atan2(-x, -z); applyPose(p, READY); }
  B1F.root.position.set(58, 0, -74); B1F.root.rotation.y = yawTo(B1F.root.position, MOUND); applyPose(B1F, READY);
  U1.root.position.set(72, 0, -78); U1.root.rotation.y = yawTo(U1.root.position, PLATE_C); applyPose(U1, U_BASE);
  C.root.position.set(0.15, 0, 3.0); C.root.rotation.y = Math.PI; applyPose(C, C_SET);
  ump.root.position.set(0.5, 0, 6.0); ump.root.rotation.y = Math.PI; applyPose(ump, { ...STAND, lean: 6 });
  batter.root.position.set(-3.0, 0, -0.9); batter.root.rotation.y = Math.PI / 2; applyPose(batter, BAT_SET);
  BB.visible = false; BOTTLE.visible = false; for (const m of STREAK) m.visible = false; pitcher.root.visible = true; HAND.root.visible = true;
  for (const D of [PUFF, FALL, MOTE]) D.pts.visible = false;
  setSkin({});
  for (const [k, arr] of Object.entries(HAND.shells.hl)) for (const m of arr) m.material.opacity = (s.hl ?? "").includes(k) ? 0.55 + 0.2 * Math.sin(t * 6) : 0;
  const act = s.act ?? "pick";
  if (act === "pick") actPick(t, s);
  else if (act === "hold") actHold(t, s);
  else if (act === "pitch") actPitch(t, s);
  else if (act === "rules") actRules(t, s);
  else if (act === "rest") { actPitch(t, s); motesAt(MOTE, BAG0, t, 0.6); }
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
const rigW = (p) => { HAND.root.updateMatrixWorld(true); return HAND.root.localToWorld(A(p)); };          // a point in the hand's frame (forearm-fixed)
const wristW = (p) => { HAND.root.updateMatrixWorld(true); return HAND.wrist.localToWorld(A(p)); };
const CAMS = {
  // a point near the bag, relative to it (it sits still on the mound)
  bag: (u, t, s) => [BAG0.clone().add(mixV(A(s.c0), A(s.c1 ?? s.c0), easeIO(u))), BAG0.clone().add(mixV(A(s.l ?? [0, 0.02, 0]), A(s.l1 ?? s.l ?? [0, 0.02, 0]), easeIO(u))), lerp(s.f0 ?? 30, s.f1 ?? s.f0 ?? 30, easeIO(u))],
  // anywhere in the world
  world: (u, t, s) => [mixV(A(s.c0), A(s.c1 ?? s.c0), easeIO(u)), mixV(A(s.l), A(s.l1 ?? s.l), easeIO(u)), lerp(s.f0 ?? 36, s.f1 ?? s.f0 ?? 36, easeIO(u))],
  // the camera rides with the hand: positions in the hand's frame (fixed to the forearm), aimed at a point in the wrist frame
  rig: (u, t, s) => [rigW(mixV(A(s.c0), A(s.c1 ?? s.c0), easeIO(u)).toArray()), wristW(s.l ?? [0.02, 0.36, 0.12]), lerp(s.f0 ?? 30, s.f1 ?? s.f0 ?? 30, easeIO(u))],
  // from a world point, zooming in on the hand
  zoomHand: (u, t, s) => { const h = wristW(s.l ?? [0.02, 0.36, 0.12]), e = easeIO(clamp(u * 1.1, 0, 1)), near = rigW(s.c1), dir = near.clone().sub(h); const d = dir.length(); dir.normalize();
    return [h.clone().addScaledVector(dir, lerp(s.dFar ?? 10, d, e)), h, lerp(s.f0 ?? 36, s.f1 ?? 24, e)]; },
  // following the hand through the delivery, from a fixed offset in the world (smoothed toward the hand)
  track: (u, t, s) => { const h = wpos(HAND.wrist).add(v3(0, 0.1, 0)); return [h.clone().add(A(s.off)), h.clone().add(A(s.lo ?? [0, 0, 0])), s.f0 ?? 30]; },
  // behind the pitcher, toward the plate, for the flight
  ball: (u, t, s) => { const b = BB.getWorldPosition(v3()); return [mixV(A(s.c0), A(s.c1 ?? s.c0), u), b.lerp(A(s.l ?? [0, 2.6, 0]), s.k ?? 0.6), s.f0 ?? 24]; },
};
function shotAt(v) {
  const L = CC.shots.list;
  const s = L.find((x) => v < x.b) || L.at(-1);
  return { s, t: pw(v, s.vs, s.ts), u: clamp((v - s.a) / (s.b - s.a), 0, 1) };
}

// ------------------------------------------------------------------ DOM overlays fed from the same clock
const $ = (id) => document.getElementById(id);
const PINT = {
  bag: () => (BAG.parent === scene ? BAG.position.clone() : BAG.getWorldPosition(v3())).add(v3(0, 0.12, 0)),
  tipI: () => wpos(HAND.F.I.tip), tipM: () => wpos(HAND.F.M.tip), tipT: () => wpos(HAND.F.T.tip),
  ball: () => BB.getWorldPosition(v3()).add(v3(0, 0.16, 0)), rubber: () => v3(0, MOUND_H + 0.3, RUBBER_Z), bottle: () => BOTTLE.getWorldPosition(v3()).add(v3(0, 0.42, 0)),
  pitcher: () => headTop(pitcher),
};
function pin(id, p) {                                            // x is clamped so the label stays on screen
  const el = $(id); if (!el || !p) return;
  const q = p.clone().project(cam), half = el.dataset.half;
  const y0 = half === "t" ? 0 : half === "b" ? H / 2 : 0, hh = half ? H / 2 : H;
  el.style.left = `${clamp((q.x + 1) / 2 * W, 190, W - 190).toFixed(1)}px`; el.style.top = `${(y0 + (1 - q.y) / 2 * hh).toFixed(1)}px`;
}
function view(c, s, aspect) {
  frame(cam, c[0], c[1], c[2], aspect);
  setBokeh(s.bokeh ?? 0); closeLights(!!s.close, c[1]);
}
function renderAt(v) {
  const { s, t, u } = shotAt(v);
  renderer.setScissorTest(s.mode === "split");
  if (s.mode === "split") {
    for (const [y, half, k] of [[H / 2, s.top, "t"], [0, s.bot, "b"]]) {
      const sh = { ...s, ...half }, th = pw(v, half.vs ?? s.vs, half.ts ?? s.ts);
      setScene(th, sh);
      view(CAMS[sh.cam](u, th, sh, v), sh, W / (H / 2));
      renderer.setViewport(0, y, W, H / 2); renderer.setScissor(0, y, W, H / 2);
      renderer.render(scene, cam);
      for (const [id, key, hk] of CC.pins) if (hk === k) pin(id, PINT[key]());
    }
  } else {
    setScene(t, s);
    view(CAMS[s.cam](u, t, s, v), s, W / H);
    renderer.setViewport(0, 0, W, H);
    renderer.render(scene, cam);
    for (const [id, key, hk] of CC.pins) if (!hk) pin(id, PINT[key]());
  }
  if ($("spd")) { const sp = s.freeze != null && v >= s.freeze && (s.freezeEnd == null || v < s.freezeEnd) ? "Freeze" : s.speed === "slow" && (s.slowEnd == null || v < s.slowEnd) && (s.slowStart == null || v >= s.slowStart) ? "Slow motion" : ""; $("spd").textContent = sp; $("spd").style.opacity = sp ? 1 : 0; }
}

let last = -1;
function seek(time) { if (time === last) return; last = time; renderAt(time); }
window.addEventListener("hf-seek", (e) => seek(e.detail.time));
window.__fieldRender = renderAt;
window.__dbg = { CAMS, HAND, GRIP, applyHand, v3, setScene, BAG0, BAGH, P_HOLD, get PICK_ROOT() { return PICK_ROOT; }, pitcher, wpos };
window.__gripView = (name, off, fov = 30) => {
  setScene(0, { act: "none" }); handOnPitcher(false); pitcher.root.visible = false;
  HAND.root.position.set(0, 40, -150); HAND.root.quaternion.identity();
  const g = name === "bag" ? { pose: BAG_HOLD, c: BAGH.c } : name === "sqz" ? { pose: BAG_SQZ, c: BAGH.c } : name.startsWith("rub") ? { pose: RUBS[+name.slice(3)], c: v3(0.05, 0.5, 0.06) } : GRIP[name];
  applyHand(g.pose); setSkin({});
  if (GRIP[name]) { HAND.wrist.add(BB); BB.position.copy(g.c); BB.quaternion.copy(g.qq); BB.visible = true; }
  if (name === "bag" || name === "sqz") holdBagInHand(name === "sqz" ? 1 : 0);
  HAND.root.updateMatrixWorld(true);
  const tgt = HAND.wrist.localToWorld(g.c.clone());
  frame(cam, HAND.root.position.clone().add(v3(...off)), tgt, fov, W / H); setBokeh(8); closeLights(true, tgt);
  renderer.setScissorTest(false); renderer.setViewport(0, 0, W, H); renderer.render(scene, cam); pitcher.root.visible = true;
};
document.fonts.ready.then(() => seek(window.__hfThreeTime || 0));
seek(window.__hfThreeTime || 0);
