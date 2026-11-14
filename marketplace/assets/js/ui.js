// App screens, drawn on a 900 x 1950 canvas (the phone's display). Each is a pure function of time and a few 0..1 controls.
// Dark interfaces in the JT Builds palette: charcoal surfaces, warm white text, amber for the supply side and for actions.
import { clamp, lerp, smooth, easeOut, rng, rrPath, CSSP as C } from "./core.js";
const SW = 900, SH = 1950;
const F = (w, px, fam = "Inter") => `${w} ${px}px ${fam}, sans-serif`;
const M = (w, px) => F(w, px, "Montserrat");
function txt(g, s, x, y, font, color, align = "left", alpha = 1) { g.save(); g.globalAlpha *= alpha; g.font = font; g.fillStyle = color; g.textAlign = align; g.textBaseline = "alphabetic"; g.fillText(s, x, y); g.restore(); }
function rr(g, x, y, w, h, r, fill, stroke = null, lw = 2) { g.beginPath(); rrPath(g, x, y, w, h, r); if (fill) { g.fillStyle = fill; g.fill(); } if (stroke) { g.strokeStyle = stroke; g.lineWidth = lw; g.stroke(); } }
function circ(g, x, y, r, fill, stroke = null, lw = 2) { g.beginPath(); g.arc(x, y, r, 0, 6.2832); if (fill) { g.fillStyle = fill; g.fill(); } if (stroke) { g.strokeStyle = stroke; g.lineWidth = lw; g.stroke(); } }
const A = (hex, a) => { const n = parseInt(hex.slice(1), 16); return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`; };
function status(g, dark = true) {
  txt(g, "9:41", 76, 82, F(700, 34), C.white);
  for (let i = 0; i < 4; i++) rr(g, 700 + i * 13, 78 - 6 * i - 8, 8, 8 + 6 * i, 2, C.white);
  rr(g, 772, 56, 56, 28, 8, null, A("#f7f6f4", 0.5), 2.5); rr(g, 777, 61, 38, 18, 4, C.white);
  rr(g, 330, 44, 240, 56, 28, "#000");
}
// a dark city map: blocks, streets, one avenue, a park. (ox, oy) pans it; z zooms.
function map(g, { ox = 0, oy = 0, z = 1, seed = 7, dim = 1 } = {}) {
  g.fillStyle = "#12100f"; g.fillRect(0, 0, SW, SH);
  g.save(); g.translate(SW / 2, SH / 2); g.scale(z, z); g.translate(-SW / 2 + ox, -SH / 2 + oy);
  const R = rng(seed), bw = 168, bh = 132, gap = 26;
  for (let j = -4; j < 22; j++) for (let i = -4; i < 10; i++) {
    const x = i * (bw + gap) + (j % 2) * 0, y = j * (bh + gap), r = R();
    if (r < 0.07) { rr(g, x, y, bw, bh, 14, "#16201a"); continue; }
    rr(g, x, y, bw, bh, 12, "#1b1917");
    if (r > 0.55) rr(g, x + 14, y + 14, bw * (0.3 + R() * 0.4), bh * (0.3 + R() * 0.4), 6, "#211e1c"); else R(), R();
  }
  g.strokeStyle = "#2d2925"; g.lineWidth = 30; g.lineCap = "round"; g.beginPath(); g.moveTo(-600, 2300); g.lineTo(1500, -500); g.stroke();
  g.strokeStyle = "#39342f"; g.lineWidth = 3; g.setLineDash([22, 22]); g.beginPath(); g.moveTo(-600, 2300); g.lineTo(1500, -500); g.stroke(); g.setLineDash([]);
  g.restore();
  if (dim < 1) { g.fillStyle = `rgba(11,10,9,${1 - dim})`; g.fillRect(0, 0, SW, SH); }
}
function pulse(g, x, y, t, color, r0 = 26, r1 = 190, n = 3, per = 1.8) {
  for (let i = 0; i < n; i++) { const u = ((t / per + i / n) % 1 + 1) % 1; circ(g, x, y, lerp(r0, r1, u), null, A(color, 0.55 * (1 - u)), 5); }
}
function pin(g, x, y, color, s = 1, ring = true) {
  if (ring) circ(g, x, y, 30 * s, A(color, 0.18));
  circ(g, x, y, 15 * s, color, "#12100f", 5 * s);
}
function sheet(g, y, h = SH) { rr(g, 0, y, SW, h - y + 120, 56, "#1c1a19", "rgba(255,255,255,.07)", 2); rr(g, SW / 2 - 46, y + 20, 92, 9, 5, "#3a3632"); }
function spinner(g, x, y, r, t, color) { g.save(); g.lineCap = "round"; g.lineWidth = r * 0.24; g.strokeStyle = A(color, 0.18); g.beginPath(); g.arc(x, y, r, 0, 6.2832); g.stroke(); g.strokeStyle = color; g.beginPath(); g.arc(x, y, r, t * 6, t * 6 + 1.7); g.stroke(); g.restore(); }
function button(g, x, y, w, h, label, { fill = C.amber, ink = C.ink, press = 0, font = M(800, 44) } = {}) {
  const s = 1 - 0.05 * Math.sin(Math.PI * clamp(press, 0, 1));
  g.save(); g.translate(x + w / 2, y + h / 2); g.scale(s, s); rr(g, -w / 2, -h / 2, w, h, h / 2, fill); txt(g, label, 0, 16, font, ink, "center"); g.restore();
}
function carIcon(g, x, y, ang, color, s = 1) { g.save(); g.translate(x, y); g.rotate(ang); rr(g, -30 * s, -17 * s, 60 * s, 34 * s, 12 * s, color, "#12100f", 4); rr(g, -8 * s, -12 * s, 22 * s, 24 * s, 6 * s, "rgba(0,0,0,.35)"); g.restore(); }
function star(g, x, y, r, color) { g.beginPath(); for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, q = i % 2 ? r * 0.45 : r; g.lineTo(x + Math.cos(a) * q, y + Math.sin(a) * q); } g.closePath(); g.fillStyle = color; g.fill(); }
function check(g, x, y, s, color, lw = 9) { g.save(); g.strokeStyle = color; g.lineWidth = lw; g.lineCap = "round"; g.lineJoin = "round"; g.beginPath(); g.moveTo(x - s, y); g.lineTo(x - s * 0.3, y + s * 0.7); g.lineTo(x + s, y - s * 0.7); g.stroke(); g.restore(); }

// 1. a code editor: syntax-coloured bars scrolling by (the "complicated code")
export function uiCode(g, t, { out = 0 } = {}) {
  g.fillStyle = "#0e0d0c"; g.fillRect(0, 0, SW, SH); status(g);
  rr(g, 40, 130, 300, 70, 16, "#1c1a19"); circ(g, 84, 165, 9, C.amber); rr(g, 110, 154, 180, 22, 8, "#4a4541");
  rr(g, 360, 130, 240, 70, 16, "#151312"); rr(g, 400, 154, 150, 22, 8, "#2e2a27");
  const R = rng(31), lh = 58, scroll = t * 240, cols = [C.amber, "#e9e2d6", "#8a8580", "#3dd68c", "#e9e2d6", "#8a8580", "#ff8f6b"];
  g.save(); g.beginPath(); g.rect(0, 230, SW, SH); g.clip();
  for (let i = 0; i < 80; i++) {
    const y = 270 + i * lh - (scroll % (80 * lh)), yy = y < 200 ? y + 80 * lh : y, ind = Math.floor(R() * 4) * 44, n = 1 + Math.floor(R() * 4);
    let x = 120 + ind; rr(g, 44, yy + 4, 36, 16, 6, "#2a2623");
    for (let k = 0; k < n; k++) { const w = 50 + R() * 190, c = cols[Math.floor(R() * cols.length)]; if (yy > 210 && yy < SH) rr(g, x, yy, Math.min(w, SW - 60 - x), 24, 9, A(c.length === 7 ? c : "#e9e2d6", 0.85 * (1 - out))); x += w + 18; if (x > SW - 120) break; }
  }
  g.restore();
  const gr = g.createLinearGradient(0, SH - 420, 0, SH); gr.addColorStop(0, "rgba(14,13,12,0)"); gr.addColorStop(1, "rgba(14,13,12,1)"); g.fillStyle = gr; g.fillRect(0, SH - 420, SW, 420);
}
// 2. the empty marketplace: a map, a search pulse, and nobody on either side
export function uiEmpty(g, t, { a = 0, b = 0, title = "Marketplace" } = {}) {   // a, b: 0..1 highlight of each side's (empty) counter
  map(g, { z: 1.05, dim: 0.9 }); status(g);
  pulse(g, SW / 2, 560, t, "#f7f6f4", 36, 380, 3, 2.2); circ(g, SW / 2, 560, 26, "#f7f6f4", "#12100f", 8);
  sheet(g, 1010);
  txt(g, title, 70, 1150, M(800, 72), C.white); txt(g, "Nobody nearby yet", 70, 1222, F(600, 42), C.muted);
  const row = (x, label, color, hi) => {
    rr(g, x, 1290, 368, 520, 48, hi > 0 ? A(color, 0.10 + 0.10 * hi) : "#242120", hi > 0 ? A(color, hi) : "rgba(255,255,255,.07)", 6);
    circ(g, x + 62, 1372, 20, color); txt(g, label, x + 100, 1388, F(700, 44), hi > 0 ? "#f7f6f4" : C.grey);
    txt(g, "0", x + 184, 1720, M(800, 330), hi > 0 ? color : "#6a645f", "center");
  };
  row(62, "Customers", "#f3ede3", a); row(470, "Providers", C.amber, b);
}
// 3. a ride app, the rider's side: searching -> no drivers nearby -> matched
export function uiRide(g, t, { none = 0, match = 0, car = 0 } = {}) {
  map(g, { z: 1.12, oy: 120 }); status(g);
  const px = 470, py = 560, cx0 = 150, cy0 = 960;
  if (match > 0) {
    const pts = [[cx0, cy0], [cx0 + 190, cy0 - 30], [cx0 + 190, py + 150], [px, py + 150], [px, py]];
    g.save(); g.strokeStyle = C.amber; g.lineWidth = 14; g.lineCap = "round"; g.lineJoin = "round"; g.globalAlpha = match; g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.stroke(); g.restore();
    let L = 0; const seg = pts.slice(1).map(([x, y], i) => { const d = Math.hypot(x - pts[i][0], y - pts[i][1]); L += d; return d; });
    let d = car * L * 0.86, k = 0; while (k < seg.length - 1 && d > seg[k]) { d -= seg[k]; k++; }
    const u = d / seg[k], x = lerp(pts[k][0], pts[k + 1][0], u), y = lerp(pts[k][1], pts[k + 1][1], u);
    carIcon(g, x, y, Math.atan2(pts[k + 1][1] - pts[k][1], pts[k + 1][0] - pts[k][0]), C.amber, 1.7 * match);
  } else pulse(g, px, py, t, none > 0.5 ? C.bad : "#f7f6f4", 34, 330, 3, 1.9);
  pin(g, px, py, "#f3ede3", 1.7);
  sheet(g, 1130);
  if (match > 0.5) {
    txt(g, "Driver on the way", 70, 1290, M(800, 76), C.white); txt(g, "Arriving in 3 min", 70, 1372, F(700, 50), C.amber);
    circ(g, 150, 1580, 80, "#2c2927", C.amber, 6); txt(g, "D", 150, 1606, M(800, 72), C.white, "center");
    rr(g, 270, 1530, 300, 34, 12, "#4a4541"); rr(g, 270, 1594, 200, 28, 12, "#33302d");
    rr(g, 590, 1526, 250, 106, 26, "#f3ede3"); txt(g, "7KD 204", 715, 1596, M(800, 44), "#1a1206", "center");
  } else if (none > 0.5) {
    const a = smooth((none - 0.5) * 2);
    txt(g, "No drivers nearby", 70, 1290, M(800, 80), C.white, "left", a); txt(g, "0 cars available", 70, 1372, F(700, 50), C.bad, "left", a);
    rr(g, 70, 1460, 760, 210, 44, A("#ff6161", 0.10 * a), A("#ff6161", 0.6 * a), 4); circ(g, 170, 1565, 46, null, A("#ff6161", a), 9);
    g.save(); g.globalAlpha = a; g.strokeStyle = C.bad; g.lineWidth = 9; g.lineCap = "round"; g.beginPath(); g.moveTo(154, 1549); g.lineTo(186, 1581); g.moveTo(186, 1549); g.lineTo(154, 1581); g.stroke(); g.restore();
    txt(g, "Try again later", 250, 1584, F(700, 52), C.white, "left", a);
  } else {
    txt(g, "Requesting a ride", 70, 1290, M(800, 76), C.white); txt(g, "Finding drivers…", 170, 1374, F(700, 50), C.muted); spinner(g, 106, 1356, 28, t, C.white);
    for (let i = 0; i < 3; i++) rr(g, 70, 1470 + i * 100, 760 - i * 120, 60, 18, "#272422");
  }
}
// 4. the same ride app, the driver's side: online, nothing coming in -> a request -> accepted
export function uiDriver(g, t, { req = 0, acc = 0 } = {}) {
  map(g, { z: 1.0, ox: -120, oy: -220, seed: 12 }); status(g);
  rr(g, 200, 150, 500, 104, 52, "#1c1a19", "rgba(255,255,255,.08)"); circ(g, 262, 202, 16, C.good); txt(g, "You’re online", 300, 220, F(700, 48), C.white);
  carIcon(g, 450, 620, -0.6, C.amber, 2.0); pulse(g, 450, 620, t, C.amber, 46, 280, 2, 2.4);
  if (req < 0.05) {
    rr(g, 90, 1000, 720, 660, 56, "rgba(28,26,25,.96)", "rgba(255,255,255,.07)");
    txt(g, "0", 450, 1400, M(800, 380), C.white, "center"); txt(g, "ride requests", 450, 1510, F(700, 60), C.grey, "center"); txt(g, "Waiting for riders…", 450, 1590, F(600, 44), C.muted, "center");
  } else {
    const y = lerp(SH + 40, 1000, easeOut(req));
    rr(g, 50, y, 800, 820, 60, "#1c1a19", A("#ffb547", 0.7), 5);
    txt(g, "New ride request", 110, y + 140, M(800, 76), C.white); txt(g, "Pickup 3 min away", 110, y + 222, F(700, 50), C.amber);
    circ(g, 136, y + 340, 18, "#f3ede3"); rr(g, 186, y + 322, 460, 36, 12, "#4a4541"); circ(g, 136, y + 450, 18, C.amber); rr(g, 186, y + 432, 340, 36, 12, "#33302d");
    g.strokeStyle = "#4a4541"; g.lineWidth = 5; g.setLineDash([10, 12]); g.beginPath(); g.moveTo(136, y + 366); g.lineTo(136, y + 426); g.stroke(); g.setLineDash([]);
    if (acc > 0.5) { button(g, 110, y + 560, 680, 170, "Accepted", { fill: C.good, ink: "#062414", font: M(800, 60) }); check(g, 230, y + 645, 26, "#062414", 11); }
    else button(g, 110, y + 560, 680, 170, "Accept", { press: acc * 2, font: M(800, 60) });
  }
}
// 5. a delivery app, the customer's side: nothing to order -> restaurants appear
const FOODS = [["Bella Napoli", "Pizza · 25–35 min", "#c9553a"], ["Green Bowl", "Salads · 15–25 min", "#4f8a5b"], ["Taquería Sol", "Tacos · 20–30 min", "#d99a2b"], ["Noodle Bar", "Ramen · 30–40 min", "#7a5cc2"]];
export function uiFood(g, t, { fill = 0 } = {}) {
  g.fillStyle = "#12100f"; g.fillRect(0, 0, SW, SH); status(g);
  txt(g, "Deliver to", 70, 200, F(600, 30), C.muted); txt(g, "Home", 70, 256, M(800, 54), C.white);
  rr(g, 60, 300, 780, 96, 48, "#1c1a19", "rgba(255,255,255,.07)"); circ(g, 122, 346, 17, null, C.muted, 5); txt(g, "Search food", 164, 360, F(600, 36), C.muted);
  ["Pizza", "Burgers", "Sushi", "Tacos"].forEach((s, i) => { rr(g, 60 + i * 200, 430, 180, 72, 36, "#201e1d"); txt(g, s, 150 + i * 200, 478, F(700, 30), C.grey, "center"); });
  txt(g, "Restaurants near you", 70, 600, M(800, 44), C.white);
  for (let i = 0; i < 4; i++) {
    const y = 650 + i * 300, u = clamp(fill * 4.6 - i, 0, 1), e = easeOut(u);
    rr(g, 60, y, 780, 270, 40, "#1a1817", "rgba(255,255,255,.05)");
    if (u > 0) {
      g.save(); g.globalAlpha = e; g.translate(0, (1 - e) * 30);
      rr(g, 60, y, 780, 270, 40, "#201e1d", "rgba(255,255,255,.08)"); rr(g, 84, y + 24, 250, 222, 28, FOODS[i][2]); circ(g, 209, y + 135, 62, "rgba(255,255,255,.2)"); circ(g, 209, y + 135, 40, "rgba(255,255,255,.28)");
      txt(g, FOODS[i][0], 366, y + 96, M(800, 42), C.white); txt(g, FOODS[i][1], 366, y + 148, F(600, 30), C.grey);
      star(g, 380, y + 200, 16, C.amber); txt(g, (4.6 + i * 0.1).toFixed(1), 406, y + 212, F(700, 30), C.white);
      g.restore();
    } else { rr(g, 84, y + 24, 250, 222, 28, "#211f1d"); rr(g, 366, y + 66, 300, 34, 12, "#242120"); rr(g, 366, y + 126, 200, 26, 10, "#201e1d"); }
  }
  if (fill < 0.12) {
    const a = 1 - fill / 0.12;
    rr(g, 150, 960, 600, 300, 44, `rgba(18,16,15,${0.94 * a})`, A("#ff6161", 0.5 * a), 3);
    txt(g, "No restaurants yet", 450, 1090, M(800, 50), C.white, "center", a); txt(g, "0 open in your area", 450, 1156, F(600, 34), C.bad, "center", a);
  }
}
// 6. the kitchen's order screen (drawn on a 1280 x 720 canvas): no orders -> tickets come in
export function uiKitchen(g, t, { fill = 0 } = {}) {
  const w = 1280, h = 720; g.fillStyle = "#0e0d0c"; g.fillRect(0, 0, w, h);
  txt(g, "ORDERS", 50, 92, M(800, 54), C.white); const n = Math.floor(clamp(fill, 0, 1) * 4 + 0.001);
  rr(g, 1030, 40, 200, 76, 38, n ? A("#3dd68c", 0.16) : "#201e1d"); txt(g, `${n} new`, 1130, 92, F(700, 38), n ? C.good : C.muted, "center");
  for (let i = 0; i < 4; i++) {
    const x = 50 + i * 300, u = clamp(fill * 4.4 - i, 0, 1), e = easeOut(u);
    rr(g, x, 160, 280, 500, 28, "#161413", "rgba(255,255,255,.05)");
    if (u > 0) { g.save(); g.globalAlpha = e; g.translate(0, (1 - e) * 40); rr(g, x, 160, 280, 500, 28, "#201e1d", A("#ffb547", 0.7), 4); rr(g, x, 160, 280, 90, 28, C.amber); txt(g, `#${1041 + i}`, x + 30, 222, M(800, 44), C.ink);
      for (let k = 0; k < 4; k++) { rr(g, x + 30, 290 + k * 76, 150 + ((k * 37 + i * 53) % 70), 26, 10, "#4a4541"); circ(g, x + 236, 303 + k * 76, 14, "#33302d"); } g.restore(); }
  }
  if (fill < 0.1) { const a = 1 - fill / 0.1; txt(g, "No orders", w / 2, 420, M(800, 84), C.white, "center", 0.9 * a); txt(g, "Waiting for customers…", w / 2, 490, F(600, 40), C.muted, "center", a); }
}
// 7. DetailDash, the customer's side: browsing detailers near you
const PROS = [["MR", "Marcus R.", "4.9", "212", "Full detail · from $149", "Today 2:00 PM"], ["EV", "Elena V.", "5.0", "98", "Interior · from $89", "Today 4:30 PM"], ["DK", "Devon K.", "4.8", "341", "Exterior · from $59", "Tomorrow 9:00 AM"], ["SP", "Sam P.", "4.9", "127", "Full detail · from $159", "Tomorrow 11:00 AM"]];
function ddLogo(g, x, y, s = 1) { rr(g, x, y - 46 * s, 60 * s, 60 * s, 18 * s, C.amber); g.save(); g.fillStyle = C.ink; g.beginPath(); g.moveTo(x + 30 * s, y - 36 * s); g.bezierCurveTo(x + 52 * s, y - 14 * s, x + 46 * s, y + 6 * s, x + 30 * s, y + 6 * s); g.bezierCurveTo(x + 14 * s, y + 6 * s, x + 8 * s, y - 14 * s, x + 30 * s, y - 36 * s); g.fill(); g.restore();
  txt(g, "Detail", x + 78 * s, y, M(800, 50 * s), C.white); const w = (g.font = M(800, 50 * s), g.measureText("Detail").width); txt(g, "Dash", x + 78 * s + w, y, M(800, 50 * s), C.amber); }
export function uiDD(g, t, { scroll = 0, tap = 0, booked = 0, show = 1 } = {}) {
  g.fillStyle = "#12100f"; g.fillRect(0, 0, SW, SH); status(g);
  ddLogo(g, 64, 212); circ(g, 800, 190, 36, "#201e1d", "rgba(255,255,255,.08)");
  txt(g, "Detailers near you", 70, 330, M(800, 52), C.white); txt(g, "Available this week", 70, 384, F(600, 32), C.muted);
  ["Full detail", "Interior", "Exterior"].forEach((s, i) => { rr(g, 60 + i * 262, 420, 244, 76, 38, i ? "#201e1d" : C.amber); txt(g, s, 182 + i * 262, 470, F(700, 32), i ? C.grey : C.ink, "center"); });
  g.save(); g.beginPath(); g.rect(0, 520, SW, SH); g.clip();
  PROS.forEach((p, i) => {
    const y = 540 + i * 336 - scroll, u = clamp(show * 4.5 - i, 0, 1), e = easeOut(u); if (u <= 0) return;
    g.save(); g.globalAlpha = e; g.translate(0, (1 - e) * 36);
    const hot = i === 0 && tap > 0;
    rr(g, 60, y, 780, 306, 44, "#1c1a19", hot ? A("#ffb547", 0.9) : "rgba(255,255,255,.07)", hot ? 5 : 2);
    circ(g, 148, y + 96, 58, "#2c2927", C.amber, 5); txt(g, p[0], 148, y + 112, M(800, 40), C.white, "center");
    txt(g, p[1], 236, y + 84, M(800, 44), C.white); star(g, 250, y + 124, 16, C.amber); txt(g, p[2], 276, y + 136, F(700, 32), C.white); txt(g, `(${p[3]})`, 336, y + 136, F(600, 30), C.muted);
    txt(g, p[4], 90, y + 208, F(600, 32), C.grey); txt(g, p[5], 90, y + 258, F(700, 30), C.good);
    if (i === 0 && booked > 0.5) { button(g, 580, y + 192, 230, 84, "Booked", { fill: C.good, ink: "#062414", font: M(800, 34) }); }
    else button(g, 610, y + 192, 200, 84, "Book", { press: i === 0 ? tap : 0, font: M(800, 36) });
    g.restore();
  });
  g.restore();
}
// 8. DetailDash, the detailer's side: today's jobs, then a new booking lands
export function uiDDPro(g, t, { note = 0 } = {}) {
  g.fillStyle = "#12100f"; g.fillRect(0, 0, SW, SH); status(g);
  ddLogo(g, 64, 212, 0.8); txt(g, "PRO", 330, 208, F(700, 26), C.amber);
  txt(g, "Today", 70, 340, M(800, 60), C.white); txt(g, "2 jobs booked", 70, 396, F(600, 34), C.muted);
  rr(g, 60, 450, 780, 250, 44, "#1c1a19", "rgba(255,255,255,.07)"); txt(g, "This week", 100, 526, F(600, 32), C.muted); txt(g, "$1,240", 100, 640, M(800, 104), C.white);
  for (let i = 0; i < 6; i++) rr(g, 560 + i * 42, 650 - [50, 90, 70, 120, 100, 150][i], 26, [50, 90, 70, 120, 100, 150][i], 8, i === 5 ? C.amber : "#3a3632");
  [["10:00 AM", "Full detail · SUV"], ["2:00 PM", "Interior · Sedan"]].forEach(([a, b], i) => { const y = 740 + i * 210; rr(g, 60, y, 780, 180, 40, "#1a1817", "rgba(255,255,255,.06)"); rr(g, 60, y, 14, 180, 7, C.amber); txt(g, a, 110, y + 76, M(800, 44), C.white); txt(g, b, 110, y + 130, F(600, 32), C.grey); });
  if (note > 0) {
    const e = easeOut(clamp(note * 1.6, 0, 1)), y = lerp(-320, 130, e);
    rr(g, 40, y, 820, 290, 50, "#26221e", C.amber, 5); rr(g, 76, y + 40, 96, 96, 28, C.amber); check(g, 124, y + 90, 22, C.ink, 10);
    txt(g, "New booking", 200, y + 86, M(800, 50), C.white); txt(g, "Full detail · Tomorrow 9:00 AM", 200, y + 140, F(600, 32), C.grey);
    txt(g, "+$180", 76, y + 240, M(800, 64), C.good); txt(g, "0.8 mi away", 800, y + 232, F(600, 32), C.muted, "right");
  }
}
// 9. DetailDash's market map: detailers (amber) and customers (ivory) in one area, and the bookings between them
export function uiDDMap(g, t, { sup = 0, dem = 0, link = 0, title = "Your area" } = {}) {
  map(g, { z: 1.0, seed: 21, oy: 60 }); status(g);
  const R = rng(77), S = [], Dm = [];
  for (let i = 0; i < 12; i++) S.push([110 + R() * 680, 300 + R() * 880]);
  for (let i = 0; i < 26; i++) Dm.push([80 + R() * 740, 260 + R() * 960]);
  const ns = Math.floor(sup * 12 + 0.001), nd = Math.floor(dem * 26 + 0.001), nl = Math.floor(link * 26 + 0.001);
  g.save(); g.lineCap = "round";
  for (let i = 0; i < Math.min(nl, nd); i++) { const s = S[i % Math.max(1, ns)] ?? S[0], d = Dm[i]; if (!ns) break; g.strokeStyle = A("#ffb547", 0.55); g.lineWidth = 4; g.beginPath(); g.moveTo(s[0], s[1]); g.lineTo(d[0], d[1]); g.stroke(); }
  g.restore();
  for (let i = 0; i < nd; i++) pin(g, Dm[i][0], Dm[i][1], "#f3ede3", 0.85, false);
  for (let i = 0; i < ns; i++) pin(g, S[i][0], S[i][1], C.amber, 1.2);
  if (!ns && !nd) pulse(g, SW / 2, 760, t, "#f7f6f4", 30, 300, 3, 2.2);
  sheet(g, 1330); ddLogo(g, 64, 1450, 0.8); txt(g, title, 840, 1444, F(600, 32), C.muted, "right");
  const st = (x, label, n, color) => { rr(g, x, 1510, 248, 250, 36, "#242120", "rgba(255,255,255,.06)"); circ(g, x + 40, 1562, 12, color); txt(g, label, x + 62, 1574, F(700, 28), C.grey); txt(g, String(n), x + 30, 1706, M(800, 104), n ? C.white : "#5a544f"); };
  st(60, "Detailers", ns, C.amber); st(326, "Customers", nd, "#f3ede3"); st(592, "Bookings", Math.min(nl, nd) * (ns ? 1 : 0), C.good);
}
