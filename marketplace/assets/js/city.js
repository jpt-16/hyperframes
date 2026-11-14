// The city at night, built like an architect's model: charcoal blocks, warm windows, wet streets, traffic.
// It carries the ride story (a rider with no drivers, drivers with no riders, then a match), the delivery match, and the
// network views: customers (ivory) and the supply side (amber) appearing over one area, linking up, and spreading.
import { THREE, PAL, v3, clamp, lerp, smooth, easeOut, easeIO, ramp, rng, matte, lit, glow, canvasTex, dotTex, makeFigure, applyPose, POSE, mixPose, walkPose, makePhone, makeCar, makeArcs, wpos, yawTo, ENV, cam } from "./core.js";
import { uiRide, uiDriver, uiFood, uiDDMap } from "./ui.js";

export const clip = [0.08, 4000];
export const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0b0e); scene.fog = new THREE.FogExp2(0x0c0d11, 0.002);
scene.add(new THREE.HemisphereLight(0x7f90b0, 0x1c1712, 0.95));
const moon = new THREE.DirectionalLight(0xa9bbdc, 1.1); moon.position.set(-120, 260, 140); scene.add(moon);

// ------------------------------------------------------------------ layout
export const N = 11, B = 44, RW = 14, P = B + RW, HALF = N * P / 2;
const blockC = (i, j) => v3((i - (N - 1) / 2) * P, 0, (j - (N - 1) / 2) * P);
const R = rng(77);

// the ground: one tile per block, with the two streets that cross at its corner, lane dashes, crosswalks and lamp pools
const tile = canvasTex(512, 512, (g, w) => {
  const s = w / P, b = B * s, r = RW * s;
  g.fillStyle = "#0d0c0b"; g.fillRect(0, 0, w, w);
  g.fillStyle = "#181614"; g.fillRect(r / 2, r / 2, b, b);                        // the block's pavement
  g.fillStyle = "#141210"; g.fillRect(r / 2 + 3 * s, r / 2 + 3 * s, b - 6 * s, b - 6 * s);
  g.strokeStyle = "rgba(240,225,190,.5)"; g.lineWidth = 0.35 * s; g.setLineDash([2.2 * s, 3 * s]);
  g.beginPath(); g.moveTo(0, r / 2 + 6 * s); g.lineTo(0, w); g.moveTo(w, r / 2 + 6 * s); g.lineTo(w, w); g.moveTo(r / 2 + 6 * s, 0); g.lineTo(w, 0); g.moveTo(r / 2 + 6 * s, w); g.lineTo(w, w); g.stroke(); g.setLineDash([]);
  g.fillStyle = "rgba(235,230,220,.28)";
  for (let k = 0; k < 6; k++) { g.fillRect(r / 2 + 1 * s, (k * 1.1 - 3.0) * s + (k < 3 ? 0 : 0), 3 * s, 0.55 * s); }
  for (const [x, y] of [[r / 2, r / 2], [r / 2 + b, r / 2], [r / 2, r / 2 + b], [r / 2 + b, r / 2 + b]]) {
    const gr = g.createRadialGradient(x, y, 0, x, y, 13 * s); gr.addColorStop(0, "rgba(255,196,120,.34)"); gr.addColorStop(1, "rgba(255,196,120,0)"); g.fillStyle = gr; g.fillRect(x - 13 * s, y - 13 * s, 26 * s, 26 * s);
  }
}, { repeat: [N + 8, N + 8] });
const ground = new THREE.Mesh(new THREE.PlaneGeometry((N + 8) * P, (N + 8) * P), new THREE.MeshStandardMaterial({ map: tile, roughness: 0.42, metalness: 0.1, envMap: ENV, envMapIntensity: 0.5 }));
ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);   // (N + 8) is odd, so the tiles' corners land on the street crossings

// facades: a 16 x 16 sheet of window cells. One texture is the wall (frames and dark glass), one is the light in the windows that are on.
function facade(seed, litP, wall, glass) {
  const cells = []; const Rw = rng(seed); for (let k = 0; k < 256; k++) cells.push(Rw() < litP ? 0.5 + Rw() * 0.5 : 0);
  const draw = (emis) => canvasTex(512, 512, (g, w) => {
    const c = w / 16; g.fillStyle = emis ? "#000" : wall; g.fillRect(0, 0, w, w);
    for (let j = 0; j < 16; j++) for (let i = 0; i < 16; i++) {
      const v = cells[j * 16 + i];
      if (emis) { if (v > 0) { g.fillStyle = `rgba(255,255,255,${v})`; g.fillRect(i * c + c * 0.16, j * c + c * 0.2, c * 0.68, c * 0.6); g.fillStyle = "rgba(0,0,0,.35)"; g.fillRect(i * c + c * 0.16, j * c + c * 0.62, c * 0.68, c * 0.18); } }
      else { g.fillStyle = glass; g.fillRect(i * c + c * 0.16, j * c + c * 0.2, c * 0.68, c * 0.6); g.fillStyle = "rgba(255,255,255,.05)"; g.fillRect(i * c, j * c, c, 1.5); }
    }
  });
  const out = [draw(false), draw(true)]; for (const t of out) t.wrapS = t.wrapT = THREE.RepeatWrapping; return out;
}
const FAC = [facade(5, 0.32, "#4a443e", "#14161b"), facade(9, 0.42, "#57504a", "#181a20"), facade(13, 0.24, "#3c3a3c", "#10141c")];
const BMAT = FAC.map(([map, em], k) => new THREE.MeshStandardMaterial({ map, roughness: 0.62, envMap: ENV, envMapIntensity: 0.3, emissive: [0xffc98a, 0xffdcae, 0xcfe0ff][k], emissiveMap: em, emissiveIntensity: 1.25 }));

export const BUILD = [];                                             // { x, z, w, d, h }
function building(x, z, w, d, h, m) {
  const g = new THREE.BoxGeometry(w, h, d), uv = g.attributes.uv, ou = Math.floor(R() * 16) / 16, ov = Math.floor(R() * 16) / 16;
  for (let f = 0; f < 6; f++) for (let k = 0; k < 4; k++) {
    const i = f * 4 + k, side = f < 2 ? d : w;
    if (f === 2 || f === 3) uv.setXY(i, 0.003, 0.003);
    else uv.setXY(i, ou + uv.getX(i) * Math.round(side / 2.6) / 16, ov + uv.getY(i) * Math.round(h / 3.3) / 16);
  }
  const mesh = new THREE.Mesh(g, BMAT[m]); mesh.position.set(x, h / 2 + 0.15, z); scene.add(mesh);
  BUILD.push({ x, z, w, d, h });
}
for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
  const c = blockC(i, j), dist = Math.hypot(c.x, c.z) / HALF, tall = lerp(95, 14, clamp(dist * 1.25, 0, 1));
  if (R() < 0.05 && dist > 0.2) continue;                             // an open lot
  const split = R(), pad = 4, S = B - 2 * pad;
  const lots = split < 0.3 ? [[0, 0, S, S]] : split < 0.65 ? [[-S / 4, 0, S / 2 - 2, S], [S / 4, 0, S / 2 - 2, S]] : [[-S / 4, -S / 4, S / 2 - 2, S / 2 - 2], [S / 4, -S / 4, S / 2 - 2, S / 2 - 2], [-S / 4, S / 4, S / 2 - 2, S / 2 - 2], [S / 4, S / 4, S / 2 - 2, S / 2 - 2]];
  for (const [ox, oz, w, d] of lots) building(c.x + ox, c.z + oz, w, d, Math.max(9, tall * (0.45 + R() * 0.9)), Math.floor(R() * 3));
}
// shopfronts along the two blocks the story uses: a lit band at street level
const shopTex = canvasTex(1024, 128, (g, w, h) => {
  g.fillStyle = "#17130f"; g.fillRect(0, 0, w, h); const Rs = rng(3);
  for (let i = 0; i < 9; i++) { const x = 10 + i * 113, lit = Rs() < 0.75; g.fillStyle = lit ? ["#ffcf8a", "#ffe3b8", "#f6c27a", "#ffd9a0"][i % 4] : "#231d17"; g.fillRect(x, 26, 96, 86);
    g.fillStyle = "rgba(0,0,0,.28)"; g.fillRect(x + 46, 26, 4, 86); g.fillRect(x, 80, 96, 3); g.fillStyle = lit ? "#2a2018" : "#17130f"; g.fillRect(x, 8, 96, 14); }
});
for (const cx of [0, 116]) { const m = new THREE.Mesh(new THREE.PlaneGeometry(36, 4.2), new THREE.MeshBasicMaterial({ map: shopTex, color: new THREE.Color(0.5, 0.5, 0.5) })); m.position.set(cx, 2.25, 22 - 3.9); scene.add(m);
  const l = new THREE.PointLight(0xffc98a, 10, 26, 1.6); l.position.set(cx + 6, 2.6, 21); scene.add(l); }
// lamp posts by the kerb
for (const [x, z] of [[2, 22.6], [26, 22.6], [112, 22.6], [136, 22.6], [14, 35.4], [124, 35.4]]) {
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.12, 8, 8), matte(0x1a1817, 0.5)); pole.position.set(x, 4, z); scene.add(pole);
  const arm = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.1, 1.8), matte(0x1a1817, 0.5)); arm.position.set(x, 7.9, z + (z < 29 ? 0.8 : -0.8)); scene.add(arm);
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.12, 0.9), lit(0xffd9a0, 3)); head.position.set(x, 7.82, z + (z < 29 ? 1.6 : -1.6)); scene.add(head);
}
// street lamps: one soft warm point at every corner
{
  const pos = [];
  for (let j = 0; j <= N; j++) for (let i = 0; i <= N; i++) for (const [sx, sz] of [[1, 1], [-1, -1]]) pos.push((i - N / 2) * P + sx * (RW / 2 + 0.6), 7.5, (j - N / 2) * P + sz * (RW / 2 + 0.6));
  const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  scene.add(new THREE.Points(g, new THREE.PointsMaterial({ map: dotTex, color: 0xffc27a, size: 7, sizeAttenuation: true, transparent: true, opacity: 0.9, depthWrite: false, blending: THREE.AdditiveBlending })));
}
// traffic: head and tail lights running along the streets
const TRAF = [], Rt = rng(404);
for (let k = 0; k < 90; k++) TRAF.push({ road: Math.floor(Rt() * (N + 1)), ax: Rt() < 0.5, dir: Rt() < 0.5 ? 1 : -1, off: Rt() * N * P, sp: 9 + Rt() * 8 });
const trafG = new THREE.BufferGeometry(); trafG.setAttribute("position", new THREE.Float32BufferAttribute(new Float32Array(TRAF.length * 6), 3)); trafG.setAttribute("color", new THREE.Float32BufferAttribute(new Float32Array(TRAF.length * 6), 3));
const traf = new THREE.Points(trafG, new THREE.PointsMaterial({ map: dotTex, size: 5.5, sizeAttenuation: true, vertexColors: true, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending })); traf.frustumCulled = false; scene.add(traf);
function traffic(t, amount) {
  const p = trafG.attributes.position, c = trafG.attributes.color;
  TRAF.forEach((q, k) => {
    const on = k < TRAF.length * amount, line = (q.road - N / 2) * P + q.dir * 2.6, along = ((q.off + q.dir * q.sp * t) % (N * P) + N * P) % (N * P) - HALF;
    for (let e = 0; e < 2; e++) {
      const a = along + (e ? -q.dir * 2.2 : q.dir * 2.2), i = k * 2 + e;
      p.setXYZ(i, q.ax ? a : line, on ? 0.8 : -50, q.ax ? line : a);
      if (e) c.setXYZ(i, 1.0, 0.16, 0.1); else c.setXYZ(i, 1.0, 0.92, 0.75);
    }
  });
  p.needsUpdate = c.needsUpdate = true;
}

// ------------------------------------------------------------------ the street: the rider on the kerb, the drivers down the block
const KERB = v3(8, 0, 21.0);                                       // the south edge of the centre block; the street runs east-west at z = 29
const rider = makeFigure(PAL.ivory, { phone: 0xcfe0ff }); scene.add(rider.root);
const lamp = new THREE.SpotLight(0xffc98a, 0, 40, 0.75, 0.7, 1.4); lamp.position.set(KERB.x - 2, 8.5, KERB.z + 2.5); lamp.target.position.set(KERB.x, 0, KERB.z + 1); lamp.castShadow = true; lamp.shadow.mapSize.set(1024, 1024); lamp.shadow.bias = -0.0008; scene.add(lamp, lamp.target);
const fillL = new THREE.PointLight(0x9db4e0, 0, 30, 1.5); scene.add(fillL);
const DSPOT = v3(118, 0, 24.3);                                       // where the drivers wait, parked two blocks east
const drivers = [], dcars = [];
for (let k = 0; k < 3; k++) {
  const car = makeCar(k === 0 ? 0x24211f : k === 1 ? 0x2e2b28 : 0x1d1c1b, { accent: PAL.amber }); car.g.position.set(DSPOT.x + k * 6.2, 0, DSPOT.z); scene.add(car.g); dcars.push(car);
  const d = makeFigure(PAL.amber, { phone: k === 0 ? 0xffdcae : false }); d.root.position.set(DSPOT.x + k * 6.2 - 0.3, 0, DSPOT.z + 1.25); d.root.rotation.y = (k - 1) * 0.3; scene.add(d.root); drivers.push(d);
}
const dlamp = new THREE.SpotLight(0xffc98a, 0, 46, 0.8, 0.7, 1.4); dlamp.position.set(DSPOT.x + 3, 9, DSPOT.z + 8); dlamp.target.position.set(DSPOT.x + 6, 0, DSPOT.z); scene.add(dlamp, dlamp.target);
const hero = makeCar(0x24211f, { accent: PAL.amber }); scene.add(hero.g);   // the car that takes the ride

// the phone for close-ups: it hangs in front of the camera
const PH = makePhone(1); scene.add(PH.g);
const phLight = new THREE.PointLight(0xfff0dd, 0, 2, 1.5); scene.add(phLight);

// ------------------------------------------------------------------ the network: nodes on rooftops, links between them
const NODES = [], Rn = rng(909);
{
  const order = BUILD.map((b, i) => i).sort(() => Rn() - 0.5);
  for (let k = 0; k < order.length; k++) { const b = BUILD[order[k]]; NODES.push({ p: v3(b.x + (Rn() - 0.5) * b.w * 0.4, b.h + 0.3, b.z + (Rn() - 0.5) * b.d * 0.4), sup: k % 3 === 0, j: Rn() }); }
}
const beamG = new THREE.CylinderGeometry(0.5, 0.5, 1, 8); beamG.translate(0, 0.5, 0);
const beams = { c: new THREE.InstancedMesh(beamG, lit(PAL.ivory, 1.5), NODES.length), s: new THREE.InstancedMesh(beamG, lit(PAL.amber, 1.9), NODES.length) };
const headsG = new THREE.BufferGeometry(); headsG.setAttribute("position", new THREE.Float32BufferAttribute(new Float32Array(NODES.length * 3), 3)); headsG.setAttribute("color", new THREE.Float32BufferAttribute(new Float32Array(NODES.length * 3), 3));
const heads = new THREE.Points(headsG, new THREE.PointsMaterial({ map: dotTex, size: 20, sizeAttenuation: true, vertexColors: true, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
for (const m of [beams.c, beams.s, heads]) { m.frustumCulled = false; scene.add(m); }
const ARCS = makeArcs(scene, 150, { radius: 0.5 });
const M4 = new THREE.Matrix4();
const runG = new THREE.BufferGeometry(); runG.setAttribute("position", new THREE.Float32BufferAttribute(new Float32Array(150 * 3), 3));
const runners = new THREE.Points(runG, new THREE.PointsMaterial({ map: dotTex, color: 0xfff0d0, size: 9, sizeAttenuation: true, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending })); runners.frustumCulled = false; scene.add(runners);
// each customer links to its nearest supplier
const LINKS = [];
NODES.forEach((n, i) => { if (n.sup) return; let best = -1, bd = 1e9; NODES.forEach((m, k) => { if (!m.sup) return; const d = m.p.distanceTo(n.p); if (d < bd) { bd = d; best = k; } }); if (best >= 0 && bd < 190) LINKS.push([i, best]); });
LINKS.sort((x, y) => Math.hypot(NODES[x[0]].p.x, NODES[x[0]].p.z) - Math.hypot(NODES[y[0]].p.x, NODES[y[0]].p.z));   // the pool of 149 links goes to the centre first
// s.net = { c: [x, z], ph: [[t0, t1, r0, r1], ...] (the lit area's radius over time), dens }
function revealT(net, d) { for (const [t0, t1, r0, r1] of net.ph) { if (d <= r0) return t0; if (d <= r1) return t0 + (d - r0) / (r1 - r0) * (t1 - t0); } return 1e9; }
function network(t, net) {
  ARCS.begin();
  const hp = headsG.attributes.position, hc = headsG.attributes.color; let nc = 0, ns = 0, shown = []; const sz = net?.sz ?? 1; heads.material.size = 20 * sz; runners.material.size = 9 * sz;
  NODES.forEach((n, i) => {
    let u = 0;
    if (net && net.ph && n.j < (net.dens ?? 1)) { const tr = revealT(net, Math.hypot(n.p.x - net.c[0], n.p.z - net.c[1])) + n.j * 0.35; u = easeOut(ramp(t, tr, tr + 0.35)); n.tr = tr; } else n.tr = 1e9;
    if (net && net.thin && i % 6 === 0) { const w = ramp(t, net.thin[0] + n.j * 0.5, net.thin[0] + n.j * 0.5 + 0.25) * (1 - ramp(t, net.thin[1] + n.j * 0.4, net.thin[1] + n.j * 0.4 + 0.3)); u = Math.max(u, w * (0.45 + 0.2 * Math.sin(t * 9 + i))); }   // launched everywhere at once: a few, far apart, and they go out
    shown[i] = u;
    const hgt = (n.sup ? 16 : 11) * u * Math.sqrt(sz), m = n.sup ? beams.s : beams.c, k = n.sup ? ns++ : nc++;
    M4.makeScale(u > 0 ? 0.55 * sz : 0, Math.max(0.001, hgt), u > 0 ? 0.55 * sz : 0).setPosition(n.p.x, n.p.y, n.p.z); m.setMatrixAt(k, M4);
    hp.setXYZ(i, n.p.x, u > 0 ? n.p.y + hgt : -90, n.p.z); const col = n.sup ? [1, 0.68, 0.24] : [0.95, 0.92, 0.86]; hc.setXYZ(i, col[0] * u, col[1] * u, col[2] * u);
  });
  for (let k = nc; k < NODES.length; k++) { M4.makeScale(0, 0, 0); beams.c.setMatrixAt(k, M4); } for (let k = ns; k < NODES.length; k++) { M4.makeScale(0, 0, 0); beams.s.setMatrixAt(k, M4); }
  beams.c.instanceMatrix.needsUpdate = beams.s.instanceMatrix.needsUpdate = true; hp.needsUpdate = hc.needsUpdate = true;
  let nr = 0; const rp = runG.attributes.position;
  if (net && net.ph) LINKS.forEach(([a, b], i) => {
    if (i >= 149 || !shown[a] || !shown[b] || NODES[a].tr > 1e8 || NODES[b].tr > 1e8) return;
    const t0 = Math.max(NODES[a].tr, NODES[b].tr) + 0.25, u = ramp(t, t0, t0 + 0.5); if (u <= 0) return;
    const A = NODES[a].p.clone().setY(NODES[a].p.y + 11 * Math.sqrt(sz)), Bp = NODES[b].p.clone().setY(NODES[b].p.y + 16 * Math.sqrt(sz));
    ARCS.arc(A, Bp, easeOut(u), { slot: i, r: net.r ?? 0.5, color: PAL.amber, k: 1.5, op: 0.9, head: false });
    if (u >= 1 && nr < 149) {                                          // a courier, a car, a job: something moving along each link
      const w = ((t - t0) * 0.55 + NODES[a].j) % 1, mid = A.clone().lerp(Bp, 0.5); mid.y += A.distanceTo(Bp) * 0.56;
      const q = new THREE.QuadraticBezierCurve3(Bp, mid, A).getPoint(w); rp.setXYZ(nr++, q.x, q.y, q.z); }
  });
  for (let k = nr; k < 150; k++) rp.setXYZ(k, 0, -90, 0); rp.needsUpdate = true;
}

// ------------------------------------------------------------------ one frame
// s.mode: "kerb" (the rider waits), "phone" (a close-up of an app), "drivers" (they wait), "match" (the car comes), "net" (the network views)
export function update(t, s) {
  scene.fog.density = s.fog ?? 0.002;
  traffic(t, s.traffic ?? 0.5);
  const mode = s.mode;
  // the rider
  const look = Math.sin(t * 0.9) * 0.5 + 0.5;
  rider.root.position.copy(KERB); rider.root.rotation.y = 0.15;
  applyPose(rider, mixPose(POSE.phone, POSE.phoneUp, s.riderUp != null ? smooth(ramp(t, s.riderUp, s.riderUp + 0.5)) : smooth(look) * 0.35));
  lamp.intensity = mode === "net" ? 0 : 70; fillL.intensity = mode === "net" ? 0 : 5; fillL.position.set(KERB.x + 5, 4.5, KERB.z + 9);
  // the drivers
  drivers.forEach((d, k) => applyPose(d, k === 0 ? mixPose(POSE.phone, POSE.phoneUp, s.dUp != null ? smooth(ramp(t, s.dUp, s.dUp + 0.4)) : 0) : k === 1 ? POSE.wait : POSE.hips));
  dlamp.intensity = mode === "net" ? 0 : 90;
  // the matched car: it pulls out and drives to the kerb
  const go = s.go != null ? t - s.go : -1;
  hero.g.visible = go > -0.5;
  if (hero.g.visible) {
    const u = smooth(clamp(go / (s.goDur ?? 3.0), 0, 1)), x0 = DSPOT.x - 6.5, x1 = KERB.x + 3.4;
    hero.g.position.set(lerp(x0, x1, u), 0, lerp(26.4, 24.3, smooth(ramp(u, 0.75, 1)))); hero.g.rotation.y = -0.1 * Math.sin(Math.PI * ramp(u, 0.75, 1));
  }
  // the phone for close-ups
  PH.g.visible = mode === "phone";
  if (PH.g.visible) {
    const camDir = cam.getWorldDirection(new THREE.Vector3()), right = new THREE.Vector3().crossVectors(camDir, cam.up).normalize();
    const drift = Math.sin(t * 1.1) * 0.004;
    const rise = s.rise != null ? 1 - easeOut(ramp(t, s.rise, s.rise + 0.5)) : 0, upv = cam.up.clone().applyQuaternion(new THREE.Quaternion()).normalize(), camUp = new THREE.Vector3().crossVectors(right, camDir).normalize();
    PH.g.position.copy(cam.position).addScaledVector(camDir, s.pd ?? 0.4).addScaledVector(right, (s.px ?? 0) + drift).addScaledVector(camUp, (s.py ?? 0) - rise * 0.2 + Math.cos(t * 0.9) * 0.003);
    PH.g.quaternion.copy(cam.quaternion); PH.g.rotateY((s.pry ?? -0.16) + Math.sin(t * 0.7) * 0.02); PH.g.rotateX(s.prx ?? 0.05);
    const k = (a) => (a != null ? ramp(t, a[0], a[1]) : 0);
    if (s.ui === "ride") PH.draw(uiRide, t, { none: k(s.none), match: k(s.matchUI), car: k(s.carUI) });
    if (s.ui === "driver") PH.draw(uiDriver, t, { req: k(s.req), acc: k(s.acc) });
    if (s.ui === "food") PH.draw(uiFood, t, { fill: k(s.fill) });
    if (s.ui === "ddmap") PH.draw(uiDDMap, t, { sup: 1, dem: 1, link: 1, title: "Your city" });
    phLight.position.copy(PH.g.position).addScaledVector(camDir, -0.12); phLight.intensity = 0.1;
  } else phLight.intensity = 0;
  network(t, s.net ?? null);
  // the first link: from the driver to the rider
  if (s.link) { const u = ramp(t, s.link[0], s.link[1]); if (u > 0) ARCS.arc(DSPOT.clone().add(v3(-6, 2.5, 2)), KERB.clone().add(v3(0, 2.4, 0)), easeOut(u), { slot: 149, r: s.linkR ?? 0.35, color: PAL.amber, k: 2.0, lift: 22 }); }
  return { exposure: s.exp ?? 1.0, bloomS: s.bloom ?? (mode === "phone" ? 0.3 : 0.6), bloomT: mode === "phone" ? 0.95 : 0.82, bloomR: 0.7 };
}
