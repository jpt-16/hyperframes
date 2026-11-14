// The stage: a giant phone standing in a dark studio, customers (ivory) on its left, providers (amber) on its right.
// Used for the hook (an empty marketplace between two crowds) and again for the DetailDash challenge (the two sides connect through it).
import { THREE, Reflector, PAL, v3, clamp, lerp, smooth, easeOut, ramp, rng, matte, lit, glow, makeFigure, applyPose, POSE, mixPose, makePhone, makeArcs, wpos, ENV } from "./core.js";
import { uiCode, uiEmpty, uiDDMap } from "./ui.js";

export const clip = [0.3, 300];
export const scene = new THREE.Scene();
scene.background = new THREE.Color(0x070605); scene.fog = new THREE.Fog(0x070605, 26, 70);
scene.add(new THREE.HemisphereLight(0x8f99ad, 0x14110f, 0.22));
const key = new THREE.DirectionalLight(0xfff1dd, 0.3); key.position.set(4, 18, 14); key.castShadow = true; key.shadow.mapSize.set(2048, 2048);
Object.assign(key.shadow.camera, { left: -16, right: 16, top: 14, bottom: -6, near: 1, far: 60 }); key.shadow.bias = -0.0005; scene.add(key);

// a dark mirror floor
const mirror = new Reflector(new THREE.PlaneGeometry(200, 200), { textureWidth: 1024, textureHeight: 1820, color: 0x3a3836 });
mirror.rotation.x = -Math.PI / 2; mirror.position.y = -0.002; scene.add(mirror);
const veil = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.MeshStandardMaterial({ color: 0x0a0908, roughness: 0.6, transparent: true, opacity: 0.7 })); veil.rotation.x = -Math.PI / 2; veil.receiveShadow = true; scene.add(veil);

// the giant phone: 9 m tall, floating just off the floor, its screen toward the camera
const PH = makePhone(57.7); PH.g.position.set(0, 4.95, 0); scene.add(PH.g);   // 9 m tall
const screenLight = new THREE.PointLight(0xffe2b8, 60, 26, 1.6); screenLight.position.set(0, 4.2, 3.4); scene.add(screenLight);
const edgeL = glow(PAL.ivory, 9, 0), edgeR = glow(PAL.amber, 9, 0); edgeL.position.set(-2.2, 3.6, 0.3); edgeR.position.set(2.2, 3.6, 0.3); scene.add(edgeL, edgeR);

// two spotlights with soft cones, one per side
const coneTex = (() => { const c = document.createElement("canvas"); c.width = 8; c.height = 256; const g = c.getContext("2d"), gr = g.createLinearGradient(0, 0, 0, 256);
  gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(0.5, "rgba(255,255,255,.35)"); gr.addColorStop(1, "rgba(255,255,255,0)"); g.fillStyle = gr; g.fillRect(0, 0, 8, 256); return new THREE.CanvasTexture(c); })();
function spot(x, color) {
  const s = new THREE.SpotLight(color, 0, 40, 0.36, 0.85, 1.2); s.position.set(x * 1.5, 12, 7.5); s.target.position.set(x, 0, 2.6); s.castShadow = false; scene.add(s, s.target);
  const cone = new THREE.Mesh(new THREE.ConeGeometry(1.9, 12, 40, 1, true), new THREE.MeshBasicMaterial({ color, map: coneTex, transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending }));
  cone.position.set(x * 1.35, 6.0, 3.0); cone.rotation.z = -Math.sign(x) * 0.1; scene.add(cone);
  return { s, cone };
}
const SPA = spot(-2.2, 0xdfe6ff), SPB = spot(2.2, 0xffb866);

// the crowds
const R = rng(2024);
function crowd(sign, color, n, poses, phone) {
  const out = [];
  for (let i = 0; i < n; i++) {
    const row = Math.floor(i / 3), col = i % 3, z = 0.9 + row * 1.45 + R() * 0.4, xmax = 0.262 * (15 - z) - 0.45;   // each row fits a 9:16 frame from the aisle
    const x = sign * (1.0 + col * (xmax - 1.0) / 2 + (R() - 0.5) * 0.2);
    const f = makeFigure(color, { phone: phone ? 0xcfe0ff : false });
    f.root.position.set(x, 0, z); f.yaw0 = (R() < 0.3 ? Math.PI - sign * 0.5 : -sign * Math.PI / 2 - sign * 0.35) + (R() - 0.5) * 0.5;   // most face across the aisle, some face the phone
    f.pose = poses[Math.floor(R() * poses.length)]; f.ph = R() * 6.28; f.sc = 0.94 + R() * 0.12;
    f.root.scale.setScalar(f.sc); scene.add(f.root); out.push(f);
  }
  return out;
}
const CUST = crowd(-1, PAL.ivory, 12, ["phone", "phone", "phoneUp"], true);
const PROV = crowd(1, PAL.amber, 12, ["wait", "hips", "stand", "wait"], false);
const ARCS = makeArcs(scene, 40, { radius: 0.035 });
export const figs = { CUST, PROV };

// t: local time. s: { ui: "code" | "empty" | "dd", tEmpty, tA, tB (the sides light up), tTry: [..] (links that fail), link: [t0, t1] (links that land) }
export function update(t, s) {
  const mixE = s.ui === "code" ? smooth(ramp(t, s.tEmpty ?? 1e9, (s.tEmpty ?? 1e9) + 0.35)) : 1;
  const a = s.tA != null ? smooth(ramp(t, s.tA, s.tA + 0.3)) : (s.lit ?? 0), b = s.tB != null ? smooth(ramp(t, s.tB, s.tB + 0.3)) : (s.lit ?? 0);
  const L = s.link ? ramp(t, s.link[0], s.link[1]) : 0;
  PH.draw((g) => {
    if (s.ui === "dd") { uiDDMap(g, t, { sup: s.sup != null ? ramp(t, s.sup[0], s.sup[1]) : 1, dem: s.dem != null ? ramp(t, s.dem[0], s.dem[1]) : 1, link: L, title: "Your area" }); return; }
    if (mixE < 1) uiCode(g, t, { out: mixE });
    if (mixE > 0) { g.save(); g.globalAlpha = mixE; uiEmpty(g, t, { a, b }); g.restore(); }
  });
  PH.g.position.y = 4.95 + 0.05 * Math.sin(t * 0.9); PH.g.rotation.y = 0.02 * Math.sin(t * 0.5);
  screenLight.intensity = 26 + 14 * mixE;
  SPA.s.intensity = 5 + 60 * a; SPB.s.intensity = 5 + 60 * b; SPA.cone.material.opacity = 0.006 + 0.045 * a; SPB.cone.material.opacity = 0.006 + 0.045 * b;
  edgeL.material.opacity = 0.12 * a; edgeR.material.opacity = 0.12 * b;
  const up = (f, i, base) => {
    const sw = Math.sin(t * 0.8 + f.ph), look = s.ui === "dd" && L > i / 12 ? 1 : 0;
    let q = POSE[f.pose];
    q = mixPose(q, { ...q, side: (q.side ?? 0) + 2.2 * sw, look: (q.look ?? 0) + 8 * Math.sin(t * 0.37 + f.ph * 2), nod: (q.nod ?? 0) + 2 * sw }, 1);
    if (look) q = mixPose(q, base === "c" ? POSE.phoneUp : POSE.stand, 0.8);
    f.root.rotation.y = f.yaw0; applyPose(f, q);
    if (f.screen) f.screen.material.color.set(0xcfe0ff).multiplyScalar(0.9 + 0.5 * (base === "c" ? a : 0));
  };
  CUST.forEach((f, i) => up(f, i, "c")); PROV.forEach((f, i) => up(f, i, "p"));
  // links: in the hook they leave each side, reach the phone's edge and die there; later they land
  ARCS.begin();
  const edge = (sign, y) => v3(sign * 2.1, y, 0.3);
  if (s.tTry) s.tTry.forEach((t0, i) => {
    const u = ramp(t, t0, t0 + 0.55), fade = 1 - ramp(t, t0 + 0.5, t0 + 0.95); if (u <= 0 || fade <= 0) return;
    const side = i % 2 ? 1 : -1, f = (side < 0 ? CUST : PROV)[(i * 5) % 12], from = f.root.position.clone().setY(1.5 * f.sc);
    ARCS.arc(from, edge(side, 2.4 + (i % 4) * 1.0), easeOut(u), { color: side < 0 ? PAL.ivory : PAL.amber, op: fade, lift: 0.8, r: 0.026, k: side < 0 ? 1.0 : 1.6 });
  });
  if (s.link) for (let i = 0; i < 12; i++) {
    const u = ramp(L, i / 13, i / 13 + 0.12); if (u <= 0) continue;
    const c = CUST[i], p = PROV[(i * 7) % 12], y = 2.2 + (i % 5) * 0.95;
    ARCS.arc(c.root.position.clone().setY(1.5 * c.sc), edge(-1, y), easeOut(u), { color: PAL.ivory, lift: 0.7, r: 0.022, k: 1.0 });
    ARCS.arc(edge(1, y), p.root.position.clone().setY(1.5 * p.sc), easeOut(ramp(u, 0.3, 1)), { color: PAL.amber, lift: 0.7, r: 0.022, k: 1.5 });
  }
  return { exposure: 1.0, bloomS: 0.42, bloomT: 0.92, bloomR: 0.6 };
}
