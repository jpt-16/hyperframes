// A restaurant's pass: food bagged and ready under the heat lamps, a cook waiting, and an order screen with nothing on it.
import { THREE, PAL, v3, clamp, lerp, smooth, ramp, rng, matte, lit, glow, canvasTex, box, makeFigure, applyPose, POSE, mixPose, ENV } from "./core.js";
import { uiKitchen } from "./ui.js";

export const clip = [0.1, 60];
export const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0908); scene.fog = new THREE.Fog(0x0a0908, 7, 16);
scene.add(new THREE.HemisphereLight(0x8a93a8, 0x1a1410, 0.35));
const steel = new THREE.MeshStandardMaterial({ color: 0x8d8a86, metalness: 0.92, roughness: 0.34, envMap: ENV, envMapIntensity: 0.7 });
const dark = matte(0x1a1817, 0.7);

// the back wall: dark tile
const tiles = canvasTex(256, 256, (g, w) => { g.fillStyle = "#1d1b19"; g.fillRect(0, 0, w, w); g.strokeStyle = "#0f0e0d"; g.lineWidth = 5; for (let i = 0; i <= 4; i++) { g.beginPath(); g.moveTo(0, i * 64); g.lineTo(w, i * 64); g.stroke(); }
  for (let j = 0; j < 4; j++) for (let i = -1; i < 2; i++) { const x = i * 128 + (j % 2) * 64; g.beginPath(); g.moveTo(x, j * 64); g.lineTo(x, j * 64 + 64); g.stroke(); g.beginPath(); g.moveTo(x + 128, j * 64); g.lineTo(x + 128, j * 64 + 64); g.stroke(); } }, { repeat: [10, 6] });
const wall = new THREE.Mesh(new THREE.PlaneGeometry(12, 6), new THREE.MeshStandardMaterial({ map: tiles, roughness: 0.35, envMap: ENV, envMapIntensity: 0.4 })); wall.position.set(0, 3, -2.6); scene.add(wall);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(14, 12), matte(0x121110, 0.5)); floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
// the pass: a steel counter, a shelf above it with heat lamps
scene.add(box(4.6, 0.06, 0.9, steel, 0, 0.95, 0), box(4.6, 0.9, 0.82, dark, 0, 0.46, 0), box(4.6, 0.05, 0.42, steel, 0, 2.05, -0.1));
for (const x of [-2.25, 2.25]) scene.add(box(0.06, 1.1, 0.06, steel, x, 1.5, -0.28));
const LAMPS = [];
for (const x of [-0.72, 0.72]) {
  const shade = new THREE.Mesh(new THREE.ConeGeometry(0.17, 0.2, 20, 1, true), new THREE.MeshStandardMaterial({ color: 0x2a2623, metalness: 0.8, roughness: 0.4, side: THREE.DoubleSide })); shade.position.set(x, 1.86, 0.02); scene.add(shade);
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.055, 12, 10), lit(0xffb866, 3.5)); bulb.position.set(x, 1.8, 0.02); scene.add(bulb);
  const s = new THREE.SpotLight(0xffb060, 9, 6, 0.62, 0.8, 1.6); s.position.set(x, 1.82, 0.02); s.target.position.set(x, 0.95, 0.06); s.castShadow = true; s.shadow.mapSize.set(1024, 1024); s.shadow.bias = -0.001; scene.add(s, s.target); LAMPS.push(s);
}
// the orders: paper bags and boxes, ready to go
const kraft = matte(0xb08d62, 0.9), lidM = matte(0xe9e2d6, 0.6);
function bag(x, z, s = 1, yaw = 0) {
  const g = new THREE.Group(); g.add(box(0.24 * s, 0.3 * s, 0.15 * s, kraft, 0, 0.15 * s, 0, 0.012)); const top = box(0.24 * s, 0.07 * s, 0.03 * s, kraft, 0, 0.33 * s, 0, 0.008); g.add(top);
  const tag = new THREE.Mesh(new THREE.PlaneGeometry(0.1 * s, 0.07 * s), lit(PAL.amber, 0.9)); tag.position.set(0, 0.18 * s, 0.076 * s); g.add(tag);
  g.position.set(x, 0.98, z); g.rotation.y = yaw; scene.add(g);
}
bag(-0.86, 0.12, 1.05, 0.2); bag(-0.56, 0.16, 0.92, -0.15); bag(0.6, 0.14, 1.0, 0.1); bag(0.9, 0.1, 1.08, -0.25);
for (const [x, z] of [[-0.12, 0.2], [0.16, 0.22]]) { const b = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.085, 0.07, 24), matte(0x1d1b19, 0.5)); b.position.set(x, 1.015, z); b.castShadow = true; scene.add(b); const l = new THREE.Mesh(new THREE.CylinderGeometry(0.112, 0.112, 0.012, 24), lidM); l.position.set(x, 1.055, z); scene.add(l); }
// shelves behind, with pans
scene.add(box(3.4, 0.04, 0.3, steel, 0.4, 2.6, -2.4), box(3.4, 0.04, 0.3, steel, 0.4, 3.1, -2.4));
for (let i = 0; i < 6; i++) { const p = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.13, 0.14 + (i % 3) * 0.05, 20), i % 2 ? steel : matte(0x26221f, 0.5)); p.position.set(-1.0 + i * 0.52, 2.7 + (i % 2) * 0.5, -2.4); scene.add(p); }
// the cook: the supply side, in amber, with a toque
const cook = makeFigure(PAL.amber); cook.root.position.set(-0.12, 0, -0.78); scene.add(cook.root);
{ const hat = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.092, 0.13, 20), cook.mat); hat.position.y = 0.27; cook.neck.add(hat); const puff = new THREE.Mesh(new THREE.SphereGeometry(0.115, 18, 12), cook.mat); puff.scale.y = 0.62; puff.position.y = 0.345; cook.neck.add(puff); }
const cook2 = makeFigure(PAL.amber); cook2.root.position.set(1.5, 0, -1.7); cook2.root.rotation.y = -0.9; cook2.root.scale.setScalar(0.96); scene.add(cook2.root);
const keyL = new THREE.SpotLight(0xffd9b0, 9, 10, 0.6, 0.8, 1.4); keyL.position.set(-1.4, 3.4, 1.6); keyL.target.position.set(-0.1, 1.4, -0.8); scene.add(keyL, keyL.target);
const rim = new THREE.PointLight(0x8fb0ff, 8, 7, 1.6); rim.position.set(1.6, 2.4, -2.0); scene.add(rim);
// the order screen, hanging over the pass
const cv = document.createElement("canvas"); cv.width = 1280; cv.height = 720; const ctx = cv.getContext("2d");
const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
const scr = new THREE.Group(); scr.add(box(1.32, 0.78, 0.05, matte(0x0c0c0c, 0.4)));
const face = new THREE.Mesh(new THREE.PlaneGeometry(1.24, 0.7), new THREE.MeshBasicMaterial({ map: tex, color: new THREE.Color(1.25, 1.25, 1.25) })); face.position.z = 0.03; scr.add(face);
scr.position.set(0.1, 2.62, -0.2); scr.rotation.x = 0.2; scene.add(scr);
const scrL = new THREE.PointLight(0xffe2b8, 0, 4, 1.5); scrL.position.set(0.1, 2.5, 0.4); scene.add(scrL);

// s.fill: [t0, t1] orders coming in
export function update(t, s) {
  const fill = s.fill ? ramp(t, s.fill[0], s.fill[1]) : 0;
  uiKitchen(ctx, t, { fill }); tex.needsUpdate = true; scrL.intensity = 1.5 + 5 * fill;
  const sway = Math.sin(t * 0.9);
  let q = mixPose(POSE.wait, { ...POSE.wait, side: 3, look: 6 }, 0.5 + 0.5 * sway);
  q = { ...q, nod: -14, look: (q.look ?? 0) + 4 };                               // looking up at the screen
  if (fill > 0) q = mixPose(q, { ...POSE.counter, nod: -16 }, smooth(ramp(fill, 0.1, 0.6)));
  cook.root.rotation.y = 0.08; applyPose(cook, q);
  applyPose(cook2, mixPose(POSE.hips, { ...POSE.hips, look: -30 }, 0.5 + 0.5 * Math.sin(t * 0.6 + 1)));
  LAMPS.forEach((l, i) => (l.intensity = 9 + 0.5 * Math.sin(t * 3 + i)));
  return { exposure: 1.0, bloomS: 0.45, bloomT: 0.9, bloomR: 0.6 };
}
