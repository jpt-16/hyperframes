// The clock: HyperFrames time -> the current shot -> its set, camera and controls.
import { W, H, v3, A, clamp, lerp, easeIO, easeOut, frame, render, cam } from "./core.js";
import * as stage from "./stage.js";
import * as city from "./city.js";
import * as kitchen from "./kitchen.js";
import * as usmap from "./usmap.js";
import * as bay from "./bay.js";
const SETS = { stage, city, kitchen, usmap, bay };
await Promise.all(["800 60px Montserrat", "700 40px Montserrat", "600 40px Inter", "700 40px Inter", "400 40px Inter"].map((f) => document.fonts.load(f)));
const CC = window.__CC;
const pw = (v, vs, ts) => {
  if (v <= vs[0]) return ts[0];
  for (let i = 1; i < vs.length; i++) if (v <= vs[i]) return lerp(ts[i - 1], ts[i], (v - vs[i - 1]) / (vs[i] - vs[i - 1]));
  return ts.at(-1);
};
const EASE = { io: easeIO, out: easeOut, lin: (u) => u, in: (u) => u * u * u };
function renderAt(v) {
  const L = CC.shots, s = L.find((x) => v < x.b) || L.at(-1);
  const u = clamp((v - s.a) / (s.b - s.a), 0, 1), e = (EASE[s.ease] ?? easeIO)(u), t = pw(v, s.vs, s.ts);
  const set = SETS[s.set];
  [cam.near, cam.far] = set.clip ?? [0.1, 2000];
  if (s.c0) frame(v3(...s.c0).lerp(A(s.c1 ?? s.c0), e), v3(...s.l).lerp(A(s.l1 ?? s.l), e), lerp(s.f0 ?? 40, s.f1 ?? s.f0 ?? 40, e), lerp(s.r0 ?? 0, s.r1 ?? s.r0 ?? 0, e));
  const opts = set.update(t, s, u, e) ?? {};
  render(set.scene, opts);
}
let last = -1;
function seek(time) { if (time === last) return; last = time; renderAt(time); }
window.addEventListener("hf-seek", (e) => seek(e.detail.time));
window.__fieldRender = renderAt;
window.__dbg = { SETS, cam };
seek(window.__hfThreeTime || 0);
