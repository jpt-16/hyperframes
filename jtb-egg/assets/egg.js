// The opening shot: an egg rolls across a dark stone counter, tips over the edge and drops.
// Rendered with three.js from HyperFrames time only (hf-seek), so every frame is exact and repeatable.
// Everything is built in code: egg (lathe profile + shell texture), counter (stone texture), lights.
import * as THREE from "three";
import { RoomEnvironment } from "./vendor/RoomEnvironment.js";

const W = 1080, H = 1920;
const T_EDGE = 1.5;          // centre of the egg reaches the counter edge
const SHOT_END = 2.05;       // after this the layer is hidden; stop rendering

const canvas = document.getElementById("egg-gl");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: true });
renderer.setSize(W, H, false);
renderer.setPixelRatio(1);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.92;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.setClearColor(0x000000, 0);

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x070504, 11, 24);      // the counter falls off into a dark kitchen
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(renderer), 0.04).texture;

// deterministic noise
let seed = 1234567;
const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

function canvasTex(size, draw, srgb = true) {
  const c = document.createElement("canvas"); c.width = c.height = size;
  draw(c.getContext("2d"), size);
  const t = new THREE.CanvasTexture(c);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 8;
  return t;
}

// ---------------------------------------------------------------- counter: dark honed stone
const stone = canvasTex(1024, (g, s) => {
  g.fillStyle = "#1b1815"; g.fillRect(0, 0, s, s);
  for (let i = 0; i < 26000; i++) {
    const v = rnd(); const x = rnd() * s, y = rnd() * s, r = rnd() * 1.6 + 0.3;
    g.fillStyle = v < 0.5 ? `rgba(62,56,50,${0.25 + rnd() * 0.4})` : v < 0.93 ? `rgba(12,10,9,${0.3 + rnd() * 0.4})` : `rgba(150,140,125,${0.25 + rnd() * 0.35})`;
    g.beginPath(); g.arc(x, y, r, 0, 6.283); g.fill();
  }
  g.strokeStyle = "rgba(120,108,92,0.10)"; g.lineWidth = 2;
  for (let k = 0; k < 7; k++) {          // a few soft veins
    g.beginPath(); let x = rnd() * s, y = 0; g.moveTo(x, y);
    while (y < s) { x += (rnd() - 0.5) * 60; y += 30 + rnd() * 40; g.lineTo(x, y); }
    g.stroke();
  }
});
stone.repeat.set(9, 13);
const stoneRough = canvasTex(512, (g, s) => {
  g.fillStyle = "#7a7a7a"; g.fillRect(0, 0, s, s);
  for (let i = 0; i < 9000; i++) { const v = 90 + rnd() * 90; g.fillStyle = `rgb(${v},${v},${v})`; g.fillRect(rnd() * s, rnd() * s, 2, 2); }
}, false);
stoneRough.repeat.set(18, 26);
const counterMat = new THREE.MeshStandardMaterial({ map: stone, roughnessMap: stoneRough, roughness: 0.46, metalness: 0.0, envMapIntensity: 0.22 });
const top = new THREE.Mesh(new THREE.BoxGeometry(40, 0.6, 60), counterMat);
top.position.set(0, -0.3, -30); top.receiveShadow = true; scene.add(top);


// ---------------------------------------------------------------- the egg
const prof = [];
for (let i = 0; i <= 64; i++) {
  const t = (i / 64) * Math.PI;
  const y = -Math.cos(t);                                   // -1 (blunt end) .. 1 (pointed end)
  const r = 0.74 * Math.sin(t) * (1 + 0.12 * Math.cos(t)) * (1 - 0.04 * Math.sin(t) * Math.cos(t));
  prof.push(new THREE.Vector2(Math.max(r, 1e-4), y));
}
const eggGeo = new THREE.LatheGeometry(prof, 96);
eggGeo.rotateZ(-Math.PI / 2);                               // long axis along +x (pointed end at +x)
const shellBump = canvasTex(1024, (g, s) => {
  g.fillStyle = "#808080"; g.fillRect(0, 0, s, s);
  for (let i = 0; i < 60000; i++) { const v = 110 + rnd() * 50; g.fillStyle = `rgba(${v},${v},${v},0.5)`; g.fillRect(rnd() * s, rnd() * s, 1.5, 1.5); }
  for (let i = 0; i < 900; i++) { const v = 95 + rnd() * 30; g.fillStyle = `rgba(${v},${v},${v},0.8)`; g.beginPath(); g.arc(rnd() * s, rnd() * s, 1 + rnd() * 2.5, 0, 6.283); g.fill(); }
}, false);
const shellCol = canvasTex(512, (g, s) => {
  g.fillStyle = "#e8dccb"; g.fillRect(0, 0, s, s);
  for (let i = 0; i < 60; i++) { g.fillStyle = `rgba(150,110,80,${0.18 + rnd() * 0.2})`; g.beginPath(); g.arc(rnd() * s, rnd() * s, 1.2 + rnd() * 2.2, 0, 6.283); g.fill(); }
  for (let i = 0; i < 5000; i++) { g.fillStyle = `rgba(${190 + rnd() * 30},${165 + rnd() * 30},${130 + rnd() * 30},${0.04 + rnd() * 0.07})`; g.beginPath(); g.arc(rnd() * s, rnd() * s, 0.6 + rnd() * 2.2, 0, 6.283); g.fill(); }
});
const eggMat = new THREE.MeshPhysicalMaterial({
  map: shellCol, bumpMap: shellBump, bumpScale: 0.012, roughness: 0.58, metalness: 0,
  sheen: 0.35, sheenColor: new THREE.Color("#fff3df"), sheenRoughness: 0.6, envMapIntensity: 0.6,
});
const egg = new THREE.Mesh(eggGeo, eggMat); egg.castShadow = true; egg.receiveShadow = true;
const eggRoll = new THREE.Group(); eggRoll.add(egg);         // spins about the long axis (x)
const eggPos = new THREE.Group(); eggPos.add(eggRoll);       // travels, yaws, pitches over the edge
scene.add(eggPos);

// soft contact shadow under the egg (ambient occlusion where shell meets stone)
const aoTex = canvasTex(256, (g, s) => {
  const gr = g.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
  gr.addColorStop(0, "rgba(0,0,0,0.85)"); gr.addColorStop(0.45, "rgba(0,0,0,0.35)"); gr.addColorStop(1, "rgba(0,0,0,0)");
  g.fillStyle = gr; g.fillRect(0, 0, s, s);
});
const ao = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 1.3), new THREE.MeshBasicMaterial({ map: aoTex, transparent: true, depthWrite: false }));
ao.rotation.x = -Math.PI / 2; ao.position.y = 0.002; // (contact shadow comes from the key light's soft shadow map)

// ---------------------------------------------------------------- light: warm key, amber rim, soft fill
const key = new THREE.SpotLight(0xffe2bf, 520, 40, 0.42, 0.7, 1.6);
key.position.set(-5, 11, 3); key.castShadow = true;
key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -0.00015; key.shadow.normalBias = 0.0; key.shadow.radius = 6;
key.target.position.set(0.2, 0, -1.2); scene.add(key, key.target);
const rim = new THREE.SpotLight(0xffa23a, 160, 40, 0.16, 0.9, 1.6);
rim.position.set(2.0, 5.5, -9); rim.target.position.set(0.0, 0.7, -2.0); scene.add(rim, rim.target);
scene.add(new THREE.HemisphereLight(0x3a3430, 0x0b0908, 0.35));

// ---------------------------------------------------------------- camera
const cam = new THREE.PerspectiveCamera(34, W / H, 0.05, 120);

// ---------------------------------------------------------------- motion (pure function of time)
const R = 0.7463;                               // resting centre height on its side (the profile's widest radius)
const V0 = 2.2, ACC = 1.0;                    // rolling speed (units/s) and gentle acceleration
const DIST = V0 * T_EDGE + 0.5 * ACC * T_EDGE * T_EDGE;
const Z0 = -DIST;
const G = 95;                                   // fall acceleration (slightly slowed for drama)
const ease = (x) => x * x * (3 - 2 * x);

function renderAt(time) {
  const t = Math.max(0, Math.min(time, SHOT_END));
  let x, y, z, roll, pitch = 0, yaw;
  if (t <= T_EDGE) {
    const d = V0 * t + 0.5 * ACC * t * t;
    z = Z0 + d;
    x = -0.25 + 0.16 * (d / DIST) * (d / DIST);  // eggs drift toward the pointed end as they roll
    yaw = -0.12 * (d / DIST);
    y = R + 0.006 * Math.sin(2 * d / R);         // the faint bob of a real, imperfect shell
    roll = d / R;
  } else {
    const u = t - T_EDGE, v = V0 + ACC * T_EDGE;
    const d = DIST + v * u;
    z = Z0 + d;
    x = -0.25 + 0.16 + 0.08 * u;
    yaw = -0.12;
    y = R - 0.5 * G * u * u - 2.2 * u;           // over the edge: it drops
    roll = d / R + 3 * u;
    pitch = Math.min(1.2, 9 * u * u);            // nose dips as it leaves the edge
  }
  eggPos.position.set(x, y, z); eggPos.rotation.set(pitch, yaw + 0.07 * Math.sin(roll * 0.5), 0.045 * Math.sin(roll));   // a real shell wobbles as it rolls
  eggRoll.rotation.x = roll;
  const lift = Math.max(0, R - y);

  // camera: low, tight, slow push toward the edge; tilts to follow the drop
  const push = ease(Math.min(1, t / T_EDGE));
  const fall = Math.max(0, t - T_EDGE);
  const tilt = ease(Math.min(1, fall / 0.4));
  cam.position.set(1.3 - 0.4 * push, 4.4 - 0.5 * push - 1.5 * tilt, 10.5 - 1.6 * push);
  const look = new THREE.Vector3(0.0, 0.3 - 4.5 * tilt, -2.4 + 1.6 * push);
  cam.lookAt(look);
  renderer.render(scene, cam);
}

let last = -1;
function seek(time) {
  if (time > SHOT_END + 0.05 && last > SHOT_END + 0.05) return;   // the shot is over; nothing to draw
  last = time; renderAt(time);
}
window.addEventListener("hf-seek", (e) => seek(e.detail.time));
window.__eggRender = renderAt;                                       // for previews
seek(window.__hfThreeTime || 0);
