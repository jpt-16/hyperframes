// A detailing bay: hexagon lights overhead, a dark glossy floor, a car being polished. The customer books on their phone;
// the detailer gets the job on theirs. A real, working business, not a concept.
import { THREE, Reflector, PAL, v3, clamp, lerp, smooth, easeOut, ramp, rng, matte, lit, glow, canvasTex, box, makeFigure, applyPose, POSE, mixPose, makePhone, makeCar, renderer, cam, ENV } from "./core.js";
import { uiDD, uiDDPro } from "./ui.js";

export const clip = [0.05, 120];
export const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0908); scene.fog = new THREE.Fog(0x0a0908, 16, 40);
scene.add(new THREE.HemisphereLight(0xa9b3c6, 0x17130f, 0.5));
const key = new THREE.DirectionalLight(0xfff4e6, 1.2); key.position.set(3, 9, 5); key.castShadow = true; key.shadow.mapSize.set(2048, 2048);
Object.assign(key.shadow.camera, { left: -8, right: 8, top: 8, bottom: -8, near: 1, far: 30 }); key.shadow.bias = -0.0006; scene.add(key);

// the room
const wallM = matte(0x1c1a19, 0.8);
const back = new THREE.Mesh(new THREE.PlaneGeometry(26, 7), wallM); back.position.set(0, 3.5, -5.2); scene.add(back);
for (const sx of [-1, 1]) { const w = new THREE.Mesh(new THREE.PlaneGeometry(22, 7), wallM); w.position.set(sx * 9, 3.5, 3); w.rotation.y = -sx * Math.PI / 2; scene.add(w); }
for (const y of [1.4, 2.5]) { const bar = new THREE.Mesh(new THREE.BoxGeometry(11, 0.07, 0.05), lit(0xfff1dc, 1.5)); bar.position.set(0, y, -5.15); scene.add(bar); }
const mirror = new Reflector(new THREE.PlaneGeometry(60, 60), { textureWidth: 1024, textureHeight: 1820, color: 0x4a4744 }); mirror.rotation.x = -Math.PI / 2; mirror.position.y = -0.002; scene.add(mirror);
const veil = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshStandardMaterial({ color: 0x100f0e, roughness: 0.5, transparent: true, opacity: 0.76 })); veil.rotation.x = -Math.PI / 2; veil.receiveShadow = true; scene.add(veil);
// the hexagon light grid over the car
{
  const hexM = lit(0xfff3e0, 1.7), r = 0.62, pts = [];
  for (let j = -3; j <= 3; j++) for (let i = -4; i <= 4; i++) {
    const cx = i * r * 1.5, cz = (j + (i % 2 ? 0.5 : 0)) * r * Math.sqrt(3);
    if (Math.abs(cx) > 3.6 || Math.abs(cz) > 2.3) continue;
    for (let k = 0; k < 6; k++) { const a0 = k * Math.PI / 3, a1 = (k + 1) * Math.PI / 3, x0 = cx + Math.cos(a0) * r, z0 = cz + Math.sin(a0) * r, x1 = cx + Math.cos(a1) * r, z1 = cz + Math.sin(a1) * r;
      const seg = new THREE.Mesh(new THREE.BoxGeometry(r, 0.035, 0.045), hexM); seg.position.set((x0 + x1) / 2, 4.3, (z0 + z1) / 2); seg.rotation.y = -Math.atan2(z1 - z0, x1 - x0); scene.add(seg); }
  }
  const over = new THREE.PointLight(0xfff1dc, 26, 14, 1.4); over.position.set(0, 4.0, 0); scene.add(over);
}
scene.add(box(9.6, 0.25, 0.3, matte(0x141312, 0.6), 0, 4.55, -2.6), box(9.6, 0.25, 0.3, matte(0x141312, 0.6), 0, 4.55, 2.6));
// a cart of supplies
{ const g = new THREE.Group(); g.add(box(0.7, 0.04, 0.45, matte(0x2a2725, 0.5), 0, 0.85, 0), box(0.7, 0.04, 0.45, matte(0x2a2725, 0.5), 0, 0.4, 0));
  for (const [x, z] of [[-0.32, -0.2], [0.32, -0.2], [-0.32, 0.2], [0.32, 0.2]]) g.add(box(0.03, 0.85, 0.03, matte(0x55504b, 0.4), x, 0.43, z));
  [[-0.2, PAL.amber], [0.0, 0xe2dbcf], [0.2, 0x3dd68c]].forEach(([x, c]) => { const b = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.05, 0.22, 14), matte(c, 0.4)); b.position.set(x, 0.98, 0); b.castShadow = true; g.add(b); });
  g.position.set(3.0, 0, -1.6); g.rotation.y = -0.5; scene.add(g); }

// the car: its paint reflects the room, lights included
const car = makeCar(0x8f959c); car.g.rotation.y = -0.42; scene.add(car.g);
car.lights[0].material.color.set(0xfff3d6).multiplyScalar(0.5);                     // parked: the lamps only catch the room
const cubeRT = new THREE.WebGLCubeRenderTarget(256, { type: THREE.HalfFloatType }); const cubeCam = new THREE.CubeCamera(0.3, 60, cubeRT); cubeCam.position.set(0, 1.0, 0);
car.g.visible = false; mirror.visible = false; cubeCam.update(renderer, scene); car.g.visible = true; mirror.visible = true;
car.paint.envMap = cubeRT.texture; car.paint.envMapIntensity = 1.2; car.paint.needsUpdate = true;

// the people: a detailer (supply, amber) polishing the bonnet; the customer (ivory) by the door with a phone
const pro = makeFigure(PAL.amber); scene.add(pro.root);
const pad = new THREE.Mesh(new THREE.CylinderGeometry(0.085, 0.085, 0.04, 20), matte(0x1a1817, 0.6)); pad.rotation.x = Math.PI / 2; pad.position.set(0, -0.11, 0.02); pro.handR.add(pad);
const cust = makeFigure(PAL.ivory, { phone: 0xffdcae }); scene.add(cust.root);
const PH = makePhone(1); scene.add(PH.g);
const phLight = new THREE.PointLight(0xfff0dd, 0, 2, 1.5); scene.add(phLight);

// s.mode: "wide" | "phone". s.ui: "dd" | "pro". The phone hangs in front of the camera for close-ups.
export function update(t, s) {
  // the detailer works the bonnet in small circles
  const a = t * 5.2, cx = Math.cos(a), sx = Math.sin(a);
  pro.root.position.set(-1.62, 0, 1.18); pro.root.rotation.y = 2.5;
  let q = { ...POSE.polish, shR: [78 + 7 * sx, 6 + 9 * cx, 0], elR: 24 + 8 * cx, twist: -8 + 3 * sx, nod: 8 };
  if (s.proLook != null) q = mixPose(q, { ...POSE.stand, lean: 6, nod: 16, shL: [34, 4, 14], elL: 100 }, smooth(ramp(t, s.proLook, s.proLook + 0.4)));
  applyPose(pro, q);
  cust.root.position.set(2.3, 0, 3.7); cust.root.rotation.y = -2.46;
  applyPose(cust, mixPose(POSE.phone, POSE.phoneUp, s.custUp != null ? smooth(ramp(t, s.custUp, s.custUp + 0.5)) : 0.15 + 0.15 * Math.sin(t * 0.8)));
  cust.root.visible = s.mode !== "phone";
  PH.g.visible = s.mode === "phone";
  if (PH.g.visible) {
    const dir = cam.getWorldDirection(new THREE.Vector3()), right = new THREE.Vector3().crossVectors(dir, cam.up).normalize();
    const rise = s.rise != null ? 1 - easeOut(ramp(t, s.rise, s.rise + 0.45)) : 0;
    PH.g.position.copy(cam.position).addScaledVector(dir, s.pd ?? 0.36).addScaledVector(right, (s.px ?? 0) + Math.sin(t * 1.1) * 0.003).add(v3(0, (s.py ?? 0) - rise * 0.2 + Math.cos(t * 0.9) * 0.003, 0));
    PH.g.quaternion.copy(cam.quaternion); PH.g.rotateY((s.pry ?? -0.12) + Math.sin(t * 0.7) * 0.02 + rise * 0.5); PH.g.rotateX((s.prx ?? 0.03) - rise * 0.3);
    const k = (v) => (v != null ? ramp(t, v[0], v[1]) : 0);
    if (s.ui === "pro") PH.draw(uiDDPro, t, { note: k(s.note) });
    else PH.draw(uiDD, t, { show: s.show != null ? k(s.show) : 1, scroll: (s.scroll != null ? smooth(k(s.scroll)) : 0) * 300, tap: k(s.tap), booked: k(s.booked) });
    phLight.position.copy(PH.g.position).addScaledVector(dir, -0.12); phLight.intensity = 0.1;
  } else phLight.intensity = 0;
  return { exposure: 1.0, bloomS: s.mode === "phone" ? 0.3 : 0.5, bloomT: s.mode === "phone" ? 0.95 : 0.88, bloomR: 0.6 };
}
