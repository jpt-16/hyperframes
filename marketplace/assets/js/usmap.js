// The United States as a dark relief map on a table. Every city is off except the one they started in; later the network spreads.
import { THREE, PAL, v3, clamp, lerp, smooth, easeOut, ramp, rng, matte, lit, glow, canvasTex, dotTex, makeArcs, ENV } from "./core.js";

export const clip = [0.2, 600];
export const scene = new THREE.Scene();
scene.background = new THREE.Color(0x080706); scene.fog = new THREE.Fog(0x080706, 60, 160);
scene.add(new THREE.HemisphereLight(0x8a96b0, 0x15110d, 0.6));
const key = new THREE.DirectionalLight(0xffe6c4, 2.0); key.position.set(-30, 40, 24); scene.add(key);
const rimL = new THREE.DirectionalLight(0x7f9fe0, 0.7); rimL.position.set(30, 14, -40); scene.add(rimL);

// a simplified outline of the contiguous states (longitude, latitude), clockwise from the northwest corner
const OUT = [[-124.7, 48.4], [-123.0, 48.3], [-122.8, 49.0], [-95.2, 49.0], [-94.6, 48.7], [-93.0, 48.6], [-91.5, 48.1], [-89.6, 48.0], [-92.1, 46.75], [-90.4, 46.6], [-89.2, 46.85], [-88.2, 47.45], [-87.6, 46.9], [-86.6, 46.45], [-85.0, 46.75], [-84.6, 46.45],
  [-85.5, 46.0], [-87.0, 45.7], [-87.6, 45.1], [-87.9, 43.9], [-87.8, 42.5], [-87.5, 41.7], [-86.9, 41.75], [-86.3, 42.9], [-86.5, 44.0], [-85.6, 45.0], [-84.8, 45.75], [-83.5, 45.3], [-83.3, 44.3], [-83.9, 43.7], [-82.6, 43.9], [-82.45, 42.95], [-83.1, 42.2], [-83.4, 41.75],
  [-82.5, 41.4], [-81.3, 41.75], [-79.8, 42.25], [-78.9, 42.85], [-79.05, 43.25], [-77.6, 43.25], [-76.2, 43.6], [-76.3, 44.2], [-75.0, 44.95], [-71.5, 45.0], [-71.3, 45.3], [-70.3, 45.9], [-70.0, 46.7], [-69.2, 47.45], [-68.2, 47.35], [-67.8, 47.05], [-67.8, 45.7], [-67.0, 44.8],
  [-68.5, 44.3], [-70.0, 43.8], [-70.6, 43.1], [-70.9, 42.4], [-70.0, 41.8], [-71.4, 41.45], [-72.9, 41.25], [-74.0, 40.6], [-74.1, 39.7], [-74.9, 38.95], [-75.5, 39.5], [-75.1, 38.4], [-75.9, 37.1], [-76.0, 36.9], [-75.5, 35.25], [-76.5, 34.7], [-77.9, 33.9], [-79.1, 33.2],
  [-80.0, 32.6], [-81.1, 31.9], [-81.4, 30.7], [-81.3, 29.8], [-80.6, 28.4], [-80.05, 26.9], [-80.15, 25.75], [-80.5, 25.2], [-81.1, 25.15], [-81.75, 25.95], [-82.2, 26.9], [-82.75, 27.9], [-82.8, 29.1], [-83.9, 30.05], [-84.9, 29.7], [-85.6, 30.1], [-87.0, 30.35], [-88.0, 30.25],
  [-89.0, 30.35], [-89.6, 30.15], [-89.3, 29.1], [-90.5, 29.1], [-91.8, 29.5], [-93.3, 29.75], [-94.7, 29.4], [-96.2, 28.55], [-97.2, 27.6], [-97.15, 25.95], [-99.1, 26.4], [-99.5, 27.5], [-100.3, 28.3], [-100.9, 29.35], [-102.3, 29.85], [-103.2, 29.0], [-104.4, 29.6],
  [-104.9, 30.6], [-106.5, 31.75], [-108.2, 31.78], [-108.2, 31.33], [-111.07, 31.33], [-114.8, 32.5], [-117.1, 32.53], [-117.3, 33.1], [-118.4, 33.75], [-118.5, 34.03], [-119.3, 34.3], [-120.5, 34.45], [-120.65, 35.15], [-121.9, 36.6], [-122.5, 37.5], [-122.5, 37.8],
  [-123.0, 38.0], [-123.8, 39.3], [-124.35, 40.4], [-124.1, 41.0], [-124.2, 42.0], [-124.5, 42.85], [-124.1, 44.0], [-123.95, 46.2], [-124.1, 46.9]];
export const XY = (lon, lat) => [(lon + 96) * 0.79, (lat - 38)];                 // map units: about one degree of latitude each
const shape = new THREE.Shape(OUT.map(([lo, la]) => new THREE.Vector2(...XY(lo, la))));
const landG = new THREE.ExtrudeGeometry(shape, { depth: 0.5, bevelEnabled: true, bevelThickness: 0.12, bevelSize: 0.12, bevelSegments: 3 }); landG.rotateX(-Math.PI / 2);
const grid = canvasTex(512, 512, (g, w) => { g.fillStyle = "#4a443f"; g.fillRect(0, 0, w, w); g.strokeStyle = "rgba(255,255,255,.09)"; g.lineWidth = 2; for (let i = 0; i <= 8; i++) { g.beginPath(); g.moveTo(i * 64, 0); g.lineTo(i * 64, w); g.moveTo(0, i * 64); g.lineTo(w, i * 64); g.stroke(); } }, { repeat: [0.25, 0.25] });
const land = new THREE.Mesh(landG, [new THREE.MeshStandardMaterial({ map: grid, color: 0xffffff, roughness: 0.75, metalness: 0.1, envMap: ENV, envMapIntensity: 0.3 }), new THREE.MeshStandardMaterial({ color: 0x8a8178, roughness: 0.4, metalness: 0.4, envMap: ENV, envMapIntensity: 0.8 })]);
land.position.y = 0; scene.add(land);
const edge = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(OUT.map(([lo, la]) => { const [x, y] = XY(lo, la); return v3(x, 0.64, -y); })), new THREE.LineBasicMaterial({ color: 0xcfc8be, transparent: true, opacity: 0.9 })); scene.add(edge);
const tgrid = canvasTex(256, 256, (g, w) => { g.fillStyle = "#0f0e0d"; g.fillRect(0, 0, w, w); g.strokeStyle = "rgba(255,255,255,.07)"; g.lineWidth = 2; g.strokeRect(0, 0, w, w); g.fillStyle = "rgba(255,255,255,.12)"; g.fillRect(0, 0, 5, 5); }, { repeat: [100, 100] });
const table = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.MeshStandardMaterial({ map: tgrid, roughness: 0.45, envMap: ENV, envMapIntensity: 0.35 })); table.rotation.x = -Math.PI / 2; table.position.y = -0.15; scene.add(table);

// the cities. The first is where it starts (San Francisco: Uber launched there in 2010; DoorDash began down the road in Palo Alto in 2013).
const CITIES = [["San Francisco", -122.42, 37.77], ["Los Angeles", -118.24, 34.05], ["Seattle", -122.33, 47.61], ["Portland", -122.68, 45.52], ["San Diego", -117.16, 32.72], ["Las Vegas", -115.14, 36.17], ["Phoenix", -112.07, 33.45], ["Salt Lake City", -111.89, 40.76],
  ["Denver", -104.99, 39.74], ["Dallas", -96.8, 32.78], ["Austin", -97.74, 30.27], ["Houston", -95.37, 29.76], ["Kansas City", -94.58, 39.1], ["Minneapolis", -93.27, 44.98], ["St. Louis", -90.2, 38.63], ["New Orleans", -90.07, 29.95], ["Chicago", -87.63, 41.88], ["Nashville", -86.78, 36.16],
  ["Detroit", -83.05, 42.33], ["Atlanta", -84.39, 33.75], ["Miami", -80.19, 25.76], ["Orlando", -81.38, 28.54], ["Charlotte", -80.84, 35.23], ["Washington", -77.04, 38.9], ["Philadelphia", -75.17, 39.95], ["New York", -74.0, 40.71], ["Boston", -71.06, 42.36]]
  .map(([name, lo, la]) => { const [x, y] = XY(lo, la); return { name, p: v3(x, 0.66, -y) }; });
export const HOME = CITIES[0].p.clone();
CITIES.forEach((c, i) => {
  c.d = c.p.distanceTo(HOME);
  c.pin = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.14, 20), new THREE.MeshBasicMaterial({ color: 0x55504b })); c.pin.position.copy(c.p); scene.add(c.pin);
  c.beam = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 1, 8), lit(PAL.amber, 2.2)); c.beam.geometry.translate(0, 0.5, 0); c.beam.position.copy(c.p); scene.add(c.beam);
  c.glow = glow(PAL.amber, 3, 0); c.glow.position.copy(c.p).add(v3(0, 0.3, 0)); scene.add(c.glow);
  c.ring = new THREE.Mesh(new THREE.RingGeometry(0.9, 1.0, 48), new THREE.MeshBasicMaterial({ color: PAL.amber, transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide })); c.ring.rotation.x = -Math.PI / 2; c.ring.position.copy(c.p).add(v3(0, 0.03, 0)); scene.add(c.ring);
});
// each city is reached from the nearest city that is closer to home
CITIES.forEach((c, i) => { if (!i) return; let best = 0, bd = 1e9; CITIES.forEach((m, k) => { if (k === i || m.d >= c.d) return; const d = m.p.distanceTo(c.p); if (d < bd) { bd = d; best = k; } }); c.from = best; });
const ARCS = makeArcs(scene, 60, { radius: 0.045 });
const homeL = new THREE.PointLight(0xffb866, 0, 30, 1.6); homeL.position.copy(HOME).add(v3(0, 2.5, 0)); scene.add(homeL);

// s.one: when home lights up. s.flick: when every city tries (and fails) at once. s.spread: [t0, t1] the wave leaving home. s.all: everything lit.
export function update(t, s) {
  ARCS.begin();
  const dmax = 46, one = s.one != null ? easeOut(ramp(t, s.one, s.one + 0.4)) : 1;
  CITIES.forEach((c, i) => {
    let on = 0, tr = 1e9;
    if (i === 0) { on = one; tr = s.one ?? -1e9; }
    else if (s.all) { on = 1; tr = -1e9; }
    else if (s.spread) { tr = s.spread[0] + (c.d / dmax) * (s.spread[1] - s.spread[0]); on = easeOut(ramp(t, tr, tr + 0.3)); }
    let flick = 0;
    if (s.flick != null && i > 0) { const u = ramp(t, s.flick + (i % 5) * 0.04, s.flick + 0.9); flick = u > 0 && u < 1 ? Math.sin(u * Math.PI) * (0.35 + 0.25 * Math.sin(t * 40 + i * 2.1)) : 0; }
    c.pin.material.color.set(on > 0 ? PAL.amber : flick > 0 ? 0xff6161 : 0x8a8580).multiplyScalar(on > 0 ? 1.2 : 0.8 + flick * 2.6);
    c.beam.scale.set(1, Math.max(0.001, (i === 0 ? 3.4 : 1.7) * on), 1); c.beam.visible = on > 0;
    c.glow.material.opacity = 0.8 * on; c.glow.scale.setScalar((i === 0 ? 5.5 : 3) * (0.9 + 0.1 * Math.sin(t * 3 + i)));
    const ru = on > 0 ? ((t - tr) / 1.6) % 1 : 0; c.ring.scale.setScalar(0.6 + 2.6 * ru * (i === 0 ? 1.5 : 1)); c.ring.material.opacity = on > 0 ? 0.6 * (1 - ru) : 0;
    if (i > 0 && on > 0 && (s.spread || s.all)) {
      const a = CITIES[c.from], t0 = tr - 0.35, u = s.all ? 1 : ramp(t, t0, tr + 0.05);
      ARCS.arc(a.p.clone().add(v3(0, 0.1, 0)), c.p.clone().add(v3(0, 0.1, 0)), easeOut(u), { slot: i, r: 0.05, color: PAL.amber, k: 1.7, lift: a.p.distanceTo(c.p) * 0.16 });
    }
  });
  homeL.intensity = 26 * one;
  return { exposure: 1.0, bloomS: 0.7, bloomT: 0.8, bloomR: 0.75 };
}
