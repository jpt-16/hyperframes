// "What should a catcher say?": the mound visit in three.js. The same pitcher and catcher throughout; the whole story is
// one clock (event times from build.py), so each frame is exact and repeatable. Units are feet. Home plate's back point is the
// origin, +x points toward first base's side, -z toward center field. The pitches come from tools/physics.py via window.__PLAY.
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


// ------------------------------------------------------------------ the mound visit: the cast, the scoreboard, the story clock
HAND.root.visible = false;
const EV = CC.ev;                                                  // event times (video seconds) from build.py
for (const el of [C.elR, C.elL, pitcher.elR, pitcher.elL]) el.children[0].children[0].scale.set(0.75, 1, 0.75);
const R1 = makePlayer(KIT.away, { helmet: true }); scene.add(R1.root);          // the runner on first (R is on second)
const MASK = C.neck.children[3];
const MASK_DOWN = { p: MASK.position.clone(), r: MASK.rotation.x }, MASK_UP = { p: v3(0, 0.66, 0.08), r: -1.45 };
function maskUp(u) { MASK.position.copy(MASK_DOWN.p).lerp(MASK_UP.p, u); MASK.rotation.x = lerp(MASK_DOWN.r, MASK_UP.r, u); }

// the center-field video board: inning, outs, the bases (runners on first and second), the line score
const BOARD = (() => {
  const tex = canvasTex(1280, 720, (g, w, h) => {
    g.fillStyle = "#06080c"; g.fillRect(0, 0, w, h);
    g.strokeStyle = "#1c2b4b"; g.lineWidth = 10; g.strokeRect(5, 5, w - 10, h - 10);
    g.fillStyle = "#cfd6e0"; g.font = "800 46px Inter, Arial, sans-serif"; g.textAlign = "left";
    const cols = ["", "1", "2", "3", "4", "5", "6", "7", "8", "9", "R", "H"];
    const rows = [["AWAY", "0", "1", "0", "0", "0", "2", "", "", "", "3", "8"], ["HOME", "1", "0", "0", "1", "0", "", "", "", "", "2", "5"]];
    cols.forEach((cc, i) => { g.fillStyle = "#7f8a9a"; g.fillText(cc, 60 + (i === 0 ? 0 : 180 + i * 72), 90); });
    rows.forEach((r, j) => r.forEach((cc, i) => { g.fillStyle = i === 0 ? "#ffffff" : i >= 10 ? "#ffd84d" : "#e9edf3"; g.fillText(cc, 60 + (i === 0 ? 0 : 180 + i * 72), 170 + j * 80); }));
    g.fillStyle = "#ff6a3d"; g.fillRect(60 + 180 + 6 * 72 - 14, 118, 56, 6);
    // bases: second and first lit
    const bx = 330, by = 520, s = 70;
    const base = (x, y, on) => { g.save(); g.translate(x, y); g.rotate(Math.PI / 4); g.fillStyle = on ? "#ffd84d" : "#1b2230"; g.strokeStyle = "#cfd6e0"; g.lineWidth = 5; g.fillRect(-s / 2, -s / 2, s, s); g.strokeRect(-s / 2, -s / 2, s, s); g.restore(); };
    base(bx, by - 110, true); base(bx + 110, by, true); base(bx - 110, by, false);
    g.fillStyle = "#ffffff"; g.font = "900 64px Inter, Arial, sans-serif"; g.fillText("TOP 6", 620, 450);
    g.font = "800 48px Inter, Arial, sans-serif"; g.fillStyle = "#7f8a9a"; g.fillText("OUTS", 620, 540); g.fillText("HITS THIS INNING", 620, 630);
    for (let i = 0; i < 2; i++) { g.fillStyle = i < 1 ? "#ff6a3d" : "#1b2230"; g.beginPath(); g.arc(800 + i * 60, 524, 20, 0, 7); g.fill(); }
    g.fillStyle = "#ffd84d"; g.font = "900 64px Inter, Arial, sans-serif"; g.fillText("3", 1050, 640);
  });
  const g = new THREE.Group();
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(64, 36), new THREE.MeshBasicMaterial({ map: tex, toneMapped: false })); g.add(scr);
  const frameM = new THREE.MeshStandardMaterial({ color: 0x1a1f28, roughness: 0.7 });
  const fr = new THREE.Mesh(new THREE.BoxGeometry(68, 40, 2), frameM); fr.position.z = -1.2; g.add(fr);
  for (const x of [-20, 20]) { const leg = new THREE.Mesh(new THREE.BoxGeometry(3, 40, 3), frameM); leg.position.set(x, -38, -1.5); g.add(leg); }
  g.position.set(-70, 62, -432); g.lookAt(0, 20, 0); scene.add(g);
  return g;
})();

// ------------------------------------------------------------------ poses
const P_SET = { lean: 4, look: 80, nod: 4, shL: [42, 8, 0], elL: 105, shR: [38, -4, 0], elR: 112, hipL: [4, 6], hipR: [4, 6], knL: 8, knR: 8 };
const P_LIFT = { lean: -4, look: 80, shL: [48, 8, 0], elL: 100, shR: [44, -4, 0], elR: 108, hipL: [100, 4], knL: 105, hipR: [6, 6], knR: 14, drop: -0.15 };
const P_STRIDE = { lean: 6, look: 40, drop: -0.6, twist: -50, shL: [80, 35, 0], elL: 25, shR: [-55, 80, 0], elR: 85, hipL: [52, 4], knL: 28, hipR: [-28, 6], knR: 38 };
const P_REL = { lean: 42, nod: 8, drop: -1.0, twist: 28, shL: [12, 32, 0], elL: 85, shR: [168, 22, 0], elR: 8, hipL: [72, 4], knL: 22, hipR: [-18, 6], knR: 92 };
const P_FOLLOW = { lean: 62, nod: 18, drop: -1.25, twist: 48, shL: [8, 38, 0], elL: 95, shR: [58, -24, 0], elR: 22, hipL: [82, 4], knL: 38, hipR: [34, 6], knR: 84 };
const P_SIGN = { lean: 22, nod: 4, shL: [16, 14, 0], elL: 40, shR: [8, 10, 0], elR: 30, hipL: [22, 8], hipR: [20, 8], knL: 24, knR: 22, drop: -0.2 };
const P_WATCH = { ...STAND, lean: 2, look: 150, twist: 30, nod: 10, shL: [20, 14, 0], elL: 40, shR: [10, 10, 0], elR: 30 };       // turned, watching the hit go into the outfield
const P_HIPS = { ...STAND, lean: 6, nod: 26, shL: [-14, 46, 0], elL: 100, shR: [-14, 46, 0], elR: 100 };                            // hands on hips, head down
const P_CAP = { ...STAND, lean: 4, nod: 10, shL: [-12, 44, 0], elL: 100, shR: [150, 24, 0], elR: 112 };                           // tugging the bill of his cap
const P_LOOKIN = { ...STAND, lean: 4, nod: 2, shL: [18, 16, 0], elL: 50, shR: [6, 10, 0], elR: 30 };
const P_TALK = { ...STAND, lean: 4, nod: 8, shL: [96, -26, 0], elL: 128, shR: [30, 14, 0], elR: 70 };                            // glove up over his mouth, talking
const P_LISTEN = { ...STAND, lean: 6, nod: 14, shL: [96, -26, 0], elL: 128, shR: [12, 10, 0], elR: 30 };
const P_INHALE = { ...STAND, lean: -6, nod: -6, shL: [22, 22, 0], elL: 40, shR: [22, 22, 0], elR: 40 };
const P_RELAX = { ...STAND, lean: 4, nod: 8, shL: [8, 10, 0], elL: 20, shR: [6, 8, 0], elR: 20 };
const C_STAND = { ...STAND, lean: 6, nod: 4, shL: [30, 16, 0], elL: 60, shR: [10, 10, 0], elR: 30 };
const C_TALK = { ...STAND, lean: 8, nod: 10, shL: [100, -24, 0], elL: 128, shR: [20, 12, 0], elR: 40 };                           // mitt over his mouth
const C_POINT = { ...STAND, lean: 12, nod: 18, shL: [46, 42, 0], elL: 20, shR: [52, -22, 0], elR: 26 };                          // the mitt held out low and away, pointing at it: that's the spot
const C_TAP = { ...STAND, lean: 10, nod: 10, shL: [70, -6, 0], elL: 20, shR: [10, 10, 0], elR: 30 };                              // a tap of the mitt on the pitcher's glove
const C_SET = { ...CROUCH, shL: [62, 18, 0], elL: 40, shR: [20, 10, 0], elR: 50, nod: -18 };
const C_TGT = { ...CROUCH, shL: [70, 38, 0], elL: 40, shR: [20, 10, 0], elR: 50, nod: -16 };                                      // the mitt held low and away
const C_RECV = { ...CROUCH, nod: -8, shL: [70, 40, 0], elL: 30, shR: [20, 10, 0], elR: 60 };
const C_UP = { ...STAND, lean: 8, shL: [40, 14, 0], elL: 70, shR: [40, 20, 0], elR: 90 };
const C_TOSS = { ...STAND, lean: 12, twist: -10, shL: [30, 16, 0], elL: 60, shR: [120, 20, 0], elR: 40 };
const C_TOSS2 = { ...STAND, lean: 14, twist: 6, shL: [30, 16, 0], elL: 60, shR: [70, 6, 0], elR: 10 };
const P_CATCH = { ...STAND, lean: 6, shL: [90, 10, 0], elL: 20, shR: [10, 10, 0], elR: 30 };
const R_LEAD = { drop: -0.6, lean: 26, nod: 10, hipL: [40, 22], hipR: [40, 22], knL: 48, knR: 48, shL: [18, 14, 0], shR: [18, 14, 0], elL: 25, elR: 25 };
const U_SET = { drop: -1.0, lean: 30, nod: -6, hipL: [52, 28], hipR: [52, 28], knL: 68, knR: 68, shL: [30, 20, 0], elL: 60, shR: [30, 20, 0], elR: 60 };
const U_BASE = { drop: -0.7, lean: 26, nod: -6, hipL: [40, 16], hipR: [40, 16], knL: 48, knR: 48, shL: [30, 12, 0], elL: 50, shR: [30, 12, 0], elR: 50 };
const BAT_SET = { drop: -0.35, lean: 18, look: 80, nod: -4, hipL: [22, 14], hipR: [22, 14], knL: 26, knR: 26, shL: [55, 6, 0], shR: [60, 34, 0], elL: 95, elR: 110, twist: 20 };
const BAT_SWING = { ...BAT_SET, twist: -70, pelvisTwist: -40, look: 60, shL: [80, -10, 0], elL: 20, shR: [70, 20, 0], elR: 30, hipL: [30, 18], knL: 20 };
const BAT_TAKE = { ...BAT_SET, twist: 26, pelvisTwist: -8, hipL: [30, 18], knL: 34 };
const RUN2 = v3(-6.5, 0, -122.5), RUN1 = v3(60.0, 0, -71.0);
const RUB = v3(0, MOUND_H, -60.5), VISIT_P = v3(0.2, 0, -57.0), VISIT_C = v3(0.55, 0, -54.6);
const yP = (p) => moundY(p.x, p.z);

// the target: a glowing ring where the catcher holds his mitt (the imagined pitch), and its pulse when the ball arrives
const TGT = new THREE.Group(); scene.add(TGT);
const tgtRing = new THREE.Mesh(new THREE.RingGeometry(0.34, 0.42, 48), new THREE.MeshBasicMaterial({ color: 0x56d1ff, transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false })); TGT.add(tgtRing);
const tgtDot = new THREE.Mesh(new THREE.CircleGeometry(0.07, 24), new THREE.MeshBasicMaterial({ color: 0x56d1ff, transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false })); TGT.add(tgtDot);
const tgtPulse = new THREE.Mesh(new THREE.RingGeometry(0.4, 0.46, 48), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false })); TGT.add(tgtPulse);
TGT.renderOrder = 9;

// ------------------------------------------------------------------ the story, as a function of video time t (slow motion maps t in build.py)
function walkTo(P, a, b, t0, t1, t, run = false) {                 // a walk (or a jog) from a to b between t0 and t1; returns [pos, yaw, pose or null]
  const u = clamp((t - t0) / (t1 - t0), 0, 1), p = a.clone().lerp(b, smooth(u)); p.y = yP(p);
  if (u <= 0 || u >= 1) return [p, null, null];
  const ph = ((t - t0) * (run ? 2.6 : 1.8)) % 1;
  return [p, yawTo(a, b), run ? runPose(ph, 0.55) : { ...STAND, lean: 6, hipL: [20 * Math.sin(ph * 6.283), 5], hipR: [-20 * Math.sin(ph * 6.283), 5], knL: 10 + 16 * Math.max(0, -Math.sin(ph * 6.283)), knR: 10 + 16 * Math.max(0, Math.sin(ph * 6.283)), shL: [-12 * Math.sin(ph * 6.283), 10, 0], shR: [12 * Math.sin(ph * 6.283), 10, 0], elL: 25, elR: 25 }];
}
const keyedT = (frames, t) => keyed(frames, t);
function deliver(t, rel) {                                           // the pitcher from the stretch, release at rel; returns his pose/pos/yaw
  const k = t - rel, F = 1.05;
  let q = P_SET, pos = RUB.clone().add(v3(0, 0, 0.1)), yaw = -Math.PI / 2;
  if (k > -F) {
    q = keyed([[-F, P_SET], [-0.75, P_LIFT], [-0.3, P_STRIDE], [0, P_REL], [0.35, P_FOLLOW], [1.2, { ...READY, look: 0 }]], k);
    const zp = lerp(-60.6, -57.6, smooth((k + 0.42) / 0.48)); pos = v3(0, MOUND_H * (zp > -59 ? 0.6 : 1), zp);
    yaw = lerp(-Math.PI / 2, 0, smooth((k + 0.58) / 0.58));
  }
  return [q, pos, yaw];
}
function setScene(t, s) {
  for (const [k, p] of Object.entries(HD)) { const [x, z] = homeD[k]; p.root.position.set(x, 0, z); p.root.rotation.y = Math.atan2(-x, -z); applyPose(p, READY); }
  B1F.root.position.set(61, 0, -66); B1F.root.rotation.y = yawTo(B1F.root.position, MOUND); applyPose(B1F, { ...READY, drop: -0.4 });
  U1.root.position.set(72, 0, -82); U1.root.rotation.y = yawTo(U1.root.position, PLATE_C); applyPose(U1, U_BASE);
  U2.root.visible = true; U2.root.position.set(-12, 0, -112); U2.root.rotation.y = yawTo(U2.root.position, PLATE_C); applyPose(U2, U_BASE);
  ump.root.position.set(0.5, 0, 6.0); ump.root.rotation.y = Math.PI; applyPose(ump, t < EV.visit0 || t > EV.back1 || s.vision ? U_SET : { ...STAND, lean: 4 });
  R.root.visible = true; R.root.position.copy(RUN2); R.root.rotation.y = yawTo(RUN2, MOUND); applyPose(R, t < EV.visit0 || t > EV.back1 || s.vision ? R_LEAD : { ...STAND, lean: 2 });
  R1.root.position.copy(RUN1); R1.root.rotation.y = yawTo(RUN1, MOUND); applyPose(R1, t < EV.visit0 || t > EV.back1 || s.vision ? R_LEAD : { ...STAND, lean: 2 });
  for (const m of STREAK) m.visible = false; tgtRing.material.opacity = tgtDot.material.opacity = tgtPulse.material.opacity = 0;
  // the batter: swings at the start (the hit); the same hitter takes the next pitches; a new hitter steps in at the end
  batter.root.position.set(-3.0, 0, -0.9); batter.root.rotation.y = Math.PI / 2; batter.bat.visible = true;
  let bq = BAT_SET;
  if (t < 1.4) bq = keyed([[EV.hit - 0.25, BAT_SET], [EV.hit, BAT_SWING], [EV.hit + 0.4, { ...BAT_SWING, twist: -90 }]], t);
  if (t > EV.newb0) { const [p, yw, q] = walkTo(batter, v3(-6.5, 0, 9), v3(-3.0, 0, -0.9), EV.newb0, EV.newb1, t); batter.root.position.copy(p); if (yw != null) batter.root.rotation.y = yw; bq = q ?? BAT_SET; }
  applyPose(batter, bq);
  // pitcher and catcher
  let pq = P_LOOKIN, ppos = RUB.clone().add(v3(0, 0, 0.6)), pyaw = 0, cq = C_SET, cpos = v3(0.15, 0, 3.0), cyaw = Math.PI, mask = 0;
  BB.visible = false;
  if (s.vision) {                                                 // the imagined pitch: catcher set up low and away, the pitcher on the rubber
    cq = C_TGT; [pq, ppos, pyaw] = deliver(t, s.rel);
    tgtOn(t, s, 0.9);
    ballFlight(t, s.rel, "tgt");
  } else if (t < EV.hit + 1.6) {                                   // the hit: a single up the middle, he turns to watch it
    pq = t < EV.hit + 0.15 ? P_LOOKIN : mixPose(P_LOOKIN, P_WATCH, smooth((t - EV.hit - 0.15) / 0.4)); pyaw = 0;
    const k = t - EV.hit; BB.visible = k > -0.6;
    if (k < 0) BB.position.copy(pathAt(PI_.fb.path, PI_.fb.flight * (1 + k / 0.6)));
    else { const a = v3(0, 2.8, -1), b = v3(-6, 0.1, -110), u = k / 0.9; BB.position.copy(a.clone().lerp(b, Math.min(u, 1))); BB.position.y = u < 1 ? lerp(2.8, 0.1, u) + 6 * u * (1 - u) : 0.12; if (u > 1) BB.position.add(v3(-1.5, 0, -45 * (u - 1))); }
    if (k > 0 && k < 0.9) STREAK.forEach((m, i) => { const d = (i + 1) * 0.012; if (k - d > 0) { m.visible = true; const u = (k - d) / 0.9; m.position.copy(v3(0, 2.8, -1).lerp(v3(-6, 0.1, -110), u)); m.position.y = lerp(2.8, 0.1, u) + 6 * u * (1 - u); } });
  } else if (t < EV.visit0) {                                      // frustrated: hands on hips, the cap, a look in
    pq = keyed([[EV.hit + 1.6, P_WATCH], [EV.hips, P_HIPS], [EV.cap - 0.1, P_HIPS], [EV.cap + 0.25, P_CAP], [EV.cap + 0.6, P_CAP], [EV.look, P_LOOKIN]], t);
    pyaw = keyed([[EV.hit + 1.6, { y: 0.7 }], [EV.hips, { y: 0.2 }], [EV.look, { y: 0 }]], t).y;
    cq = t > EV.cup ? mixPose(C_SET, C_STAND, smooth((t - EV.cup) / 0.5)) : C_SET; mask = smooth((t - EV.cup - 0.2) / 0.4);
    ppos.y = yP(ppos);
  } else if (t < EV.back0) {                                        // the visit
    mask = 1;
    ppos = VISIT_P.clone(); ppos.y = yP(ppos); pyaw = yawTo(VISIT_P, VISIT_C);
    const prog = keyed(EV.jog.map(([a, b]) => [a, { u: b }]), t).u, H0 = v3(0.15, 0, 3.0);
    cpos = H0.clone().lerp(VISIT_C, prog); cpos.y = yP(cpos); cyaw = prog < 1 ? yawTo(H0, VISIT_C) : yawTo(VISIT_C, VISIT_P);
    const cjq = prog > 0 && prog < 1 ? runPose(((t - EV.visit0) * 2.6) % 1, 0.55) : null;
    if (t < EV.visit1) { const [pp, py2, pwq] = walkTo(pitcher, RUB.clone().add(v3(0, 0, 0.6)), VISIT_P, EV.visit0 + 0.6, EV.visit0 + 1.8, t); ppos = pp; if (py2 != null) pyaw = py2; pq = pwq ?? P_HIPS; cq = cjq ?? C_STAND; }
    else {
      // listening first: he asks, the pitcher talks; then the calm talk, mitts over mouths; the breath; the plan; the nod and the tap
      const bob = (t0) => Math.sin((t - t0) * 9) * 4;
      pq = keyed([[EV.visit1, P_HIPS], [EV.ask + 0.4, P_LISTEN], [EV.ptalk, P_TALK], [EV.ptalk1, P_TALK], [EV.close0, P_LISTEN], [EV.close1, P_LISTEN], [EV.inhale - 0.1, P_RELAX], [EV.inhale + 0.9, P_INHALE], [EV.exhale + 1.2, P_RELAX], [EV.point, P_RELAX], [EV.nod + 0.6, P_RELAX]], t);
      if (t > EV.ptalk && t < EV.ptalk1) pq = { ...pq, nod: pq.nod + bob(EV.ptalk), shR: [30 + 12 * Math.sin((t - EV.ptalk) * 5), 14, 0] };
      if (t > EV.nod && t < EV.nod + 0.7) pq = { ...pq, nod: pq.nod + 16 * Math.sin(Math.PI * (t - EV.nod) / 0.35) };
      cq = keyed([[EV.visit1, C_STAND], [EV.ask, C_TALK], [EV.ask + 0.7, C_TALK], [EV.ptalk, { ...C_STAND, nod: 16 }], [EV.close0 - 0.2, { ...C_STAND, nod: 16 }], [EV.close0 + 0.2, C_TALK], [EV.point - 0.2, C_TALK], [EV.point + 0.3, C_POINT], [EV.point + 1.6, C_POINT], [EV.point + 2.0, C_STAND], [EV.tap - 0.2, C_STAND], [EV.tap, C_TAP], [EV.tap + 0.4, C_STAND]], t);
      if ((t > EV.ask && t < EV.ask + 0.7) || (t > EV.close0 + 0.2 && t < EV.close1)) cq = { ...cq, nod: cq.nod + bob(EV.ask) };
      if (t > EV.ptalk && t < EV.ptalk1) cq = { ...cq, nod: 16 + 6 * Math.max(0, Math.sin((t - EV.ptalk) * 3)) };   // nodding along
      cyaw = yawTo(VISIT_C, VISIT_P);
    }
  } else {                                                          // back to work: the catcher jogs home, the pitcher to the rubber; the next pitch
    const [cp, cy, cjq] = walkTo(C, VISIT_C, v3(0.15, 0, 3.0), EV.back0, EV.back1, t, true); cpos = cp; cyaw = cy ?? Math.PI; mask = 1 - smooth((t - EV.back1 + 0.3) / 0.4);
    cq = cjq ?? (t < EV.back1 + 0.4 ? mixPose(C_STAND, C_SET, smooth((t - EV.back1) / 0.4)) : C_SET);
    const [pp, py2, pwq] = walkTo(pitcher, VISIT_P, RUB.clone().add(v3(0, 0, 0.6)), EV.back0 + 0.2, EV.back0 + 1.6, t); ppos = pp; pyaw = py2 ?? 0; pq = pwq ?? P_SIGN;
    if (t > EV.back0 + 1.6) { ppos = RUB.clone().add(v3(0, 0, 0.2)); pq = keyed([[EV.back0 + 1.6, P_SIGN], [EV.setP - 0.6, P_SIGN], [EV.setP, P_SET]], t); pyaw = lerp(0, -Math.PI / 2, smooth((t - EV.setP + 0.6) / 0.6)); }
    if (t > EV.rel - 1.2) { [pq, ppos, pyaw] = deliver(t, EV.rel); cq = keyed([[EV.rel - 0.6, C_TGT], [EV.rel + 0.38, C_TGT], [EV.rel + 0.48, C_RECV], [EV.toss - 0.8, C_RECV], [EV.toss - 0.4, C_UP], [EV.toss - 0.12, C_TOSS], [EV.toss + 0.12, C_TOSS2], [EV.toss + 0.9, C_UP], [EV.reset, C_SET]], t);
      if (t < EV.newb0) applyPose(batter, keyed([[EV.rel, BAT_SET], [EV.rel + 0.25, BAT_TAKE], [EV.rel + 1.0, BAT_TAKE]], t)); }
    if (t > EV.rel - 1.2 && t < EV.toss + 1.5) ballFlight(t, EV.rel, "tgt");
    if (t > EV.toss + 0.75) { pq = keyed([[EV.toss + 0.4, { ...READY, look: 0 }], [EV.toss + 0.75, P_CATCH], [EV.toss + 1.3, P_LOOKIN], [EV.reset, P_SIGN]], t); ppos = keyed([[EV.toss + 0.4, { z: -57.6 }], [EV.toss + 1.6, { z: -58.6 }], [EV.reset, { z: -60.2 }]], t); ppos = v3(0, 0, ppos.z); ppos.y = yP(ppos); pyaw = 0; }
    if (s.tgtReal) tgtOn(t, s, 0.6);
  }
  pitcher.root.position.copy(ppos); pitcher.root.rotation.y = pyaw; applyPose(pitcher, pq);
  C.root.position.copy(cpos); C.root.rotation.y = cyaw; applyPose(C, cq); maskUp(mask);
  // the ball in the hand during the visit and the toss
  pitcher.root.updateMatrixWorld(true); C.root.updateMatrixWorld(true);
}
function tgtOn(t, s, op) {                                          // the target ring at the mitt
  C.root.updateMatrixWorld(true);
  const g = wpos(C.handL).add(v3(0, 0.05, -0.45)); TGT.position.copy(g); TGT.lookAt(g.clone().add(v3(0, 0, -10)));
  const rel = s.rel ?? EV.rel, k = t - rel - PI_.tgt.flight;
  tgtRing.material.opacity = op * (0.6 + 0.3 * Math.sin(t * 7)); tgtDot.material.opacity = op * 0.8;
  if (k > 0 && k < 0.6) { tgtPulse.material.opacity = 0.9 * (1 - k / 0.6); tgtPulse.scale.setScalar(1 + k * 3); }
}
function ballFlight(t, rel, kind) {
  const P = PI_[kind], k = t - rel; BB.visible = true; scene.add(BB);
  pitcher.root.updateMatrixWorld(true); C.root.updateMatrixWorld(true);
  if (k < 0) BB.position.copy(wpos(pitcher.handR));
  else if (k < P.flight) { BB.position.copy(pathAt(P.path, k)); if (k < 0.05) BB.position.lerp(wpos(pitcher.handR), 1 - k / 0.05); STREAK.forEach((m, i) => { const d = (i + 1) * 0.008; if (k - d > 0) { m.visible = true; m.position.copy(pathAt(P.path, k - d)); } }); }
  else if (t < EV.toss) BB.position.copy(wpos(C.handL)).add(v3(0, 0.05, -0.18));
  else if (t < EV.toss + 0.75) { const a = wpos(C.handR), b = wpos(pitcher.handL), u = (t - EV.toss) / 0.75; BB.position.copy(TOSS_A ?? a).lerp(b, u); BB.position.y += 16.1 * 0.75 * 0.75 * u * (1 - u) * 0.9; }
  else BB.position.copy(wpos(pitcher.handL));
  BB.quaternion.setFromAxisAngle(V(P.spin), P.rpm / 60 * 2 * Math.PI * clamp(k, 0, P.flight));
}
let TOSS_A = null;
setScene(EV.toss, {}); TOSS_A = wpos(C.handR);

// ------------------------------------------------------------------ cameras
function frame(c, pos, look, fov, aspect) { c.position.copy(pos); c.fov = fov; c.aspect = aspect; c.updateProjectionMatrix(); c.lookAt(look); }
const mixV = (a, b, u) => a.clone().lerp(b, u);
const pw = (v, vs, ts) => {
  if (v <= vs[0]) return ts[0];
  for (let i = 1; i < vs.length; i++) if (v <= vs[i]) return lerp(ts[i - 1], ts[i], (v - vs[i - 1]) / (vs[i] - vs[i - 1]));
  return ts.at(-1);
};
const A = (a) => v3(a[0], a[1], a[2]);
const OBJ = { proot: () => pitcher.root, croot: () => C.root, pneck: () => pitcher.neck, cneck: () => C.neck, glove: () => C.handL, ball: () => BB };
const objW = (o, p) => { const g = OBJ[o](); g.updateWorldMatrix(true, false); return g.localToWorld(A(p)); };
const CAMS = {
  world: (u, t, s) => [mixV(A(s.c0), A(s.c1 ?? s.c0), easeIO(u)), mixV(A(s.l), A(s.l1 ?? s.l), easeIO(u)), lerp(s.f0 ?? 36, s.f1 ?? s.f0 ?? 36, easeIO(u))],
  // a camera in one object's frame, looking at a point in another's
  obj: (u, t, s) => [objW(s.o, mixV(A(s.c0), A(s.c1 ?? s.c0), easeIO(u)).toArray()), objW(s.lo ?? s.o, mixV(A(s.l), A(s.l1 ?? s.l), easeIO(u)).toArray()), lerp(s.f0 ?? 30, s.f1 ?? s.f0 ?? 30, easeIO(u))],
  // a fixed world position aimed at a point in an object's frame
  aim: (u, t, s) => [mixV(A(s.c0), A(s.c1 ?? s.c0), easeIO(u)), objW(s.lo, s.l), lerp(s.f0 ?? 10, s.f1 ?? s.f0 ?? 10, easeIO(u))],
};
function shotAt(v) {
  const L = CC.shots.list;
  const s = L.find((x) => v < x.b) || L.at(-1);
  return { s, t: pw(v, s.vs, s.ts), u: clamp((v - s.a) / (s.b - s.a), 0, 1) };
}

// ------------------------------------------------------------------ DOM overlays fed from the same clock
const $ = (id) => document.getElementById(id);
const PINT = { pitcher: () => headTop(pitcher), catcher: () => headTop(C), pmouth: () => wpos(pitcher.neck).add(v3(0, 0.9, 0)), cmouth: () => wpos(C.neck).add(v3(0, 0.9, 0)),
  glove: () => wpos(C.handL).add(v3(0, -0.6, 0)), tgt: () => TGT.getWorldPosition(v3()).add(v3(0, 0.75, 0)), pchest: () => wpos(pitcher.neck).add(v3(0, -0.9, 0)) };
function pin(id, p, rect) {
  const el = $(id); if (!el || !p) return;
  const q = p.clone().project(cam), [x0, y0, w, h] = rect;
  el.style.left = `${clamp(x0 + (q.x + 1) / 2 * w, x0 + 220, x0 + w - 220).toFixed(1)}px`; el.style.top = `${(y0 + (1 - q.y) / 2 * h).toFixed(1)}px`;
}
function view(c, s, aspect) { frame(cam, c[0], c[1], c[2], aspect); setBokeh(s.bokeh ?? 0); closeLights(!!s.close, c[1]); }
function renderAt(v) {
  const { s, t, u } = shotAt(v);
  renderer.setScissorTest(false);
  setScene(t, s);
  view(CAMS[s.cam](u, t, s, v), s, W / H);
  renderer.setViewport(0, 0, W, H);
  renderer.render(scene, cam);
  for (const [id, key] of CC.pins) pin(id, PINT[key](), [0, 0, W, H]);
  if ($("spd")) { const sp = s.speed === "slow" ? "Slow motion" : ""; $("spd").textContent = sp; $("spd").style.opacity = sp ? 1 : 0; }
}

let last = -1;
function seek(time) { if (time === last) return; last = time; renderAt(time); }
window.addEventListener("hf-seek", (e) => seek(e.detail.time));
window.__fieldRender = renderAt;
window.__dbg = { C, pitcher, wpos, v3, setScene, BOARD };
document.fonts.ready.then(() => seek(window.__hfThreeTime || 0));
seek(window.__hfThreeTime || 0);
