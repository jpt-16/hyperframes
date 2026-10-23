// Frame-accurate capture of the running demo for the reel (30 fps, no dropped frames).
// The page runs on Playwright's virtual clock and every CSS animation is pinned to that clock,
// so each frame is rendered at an exact time even though screenshots take longer than 33 ms.
// Nothing is faked: the autopilot drives the real UI and the real API.
//   (server running)  node reel/tools/capture.mjs
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
const { chromium } = createRequire(import.meta.url)("playwright");

const BASE = process.env.BASE || "http://127.0.0.1:4310";
const OUT = path.join(path.dirname(new URL(import.meta.url).pathname), "..", "capture");
const FPS = 30;
const TZ = "America/Denver";

// Pins every running CSS animation/transition to the page's (virtual) performance.now().
const SYNC = () => {
  const now = performance.now();
  for (const a of document.getAnimations()) {
    if (a.__t0 === undefined) { a.__t0 = now - 16; a.pause(); }
    a.currentTime = now - a.__t0;
  }
};
const RECORDER = () => {
  window.__ev = [];
  const rec = (type, extra = {}) => window.__ev.push({ t: performance.now(), type, ...extra });
  document.addEventListener("click", (e) => {
    const b = e.target.closest("button, a"); const r = b?.getBoundingClientRect();
    rec("click", { what: (b?.className || "").split(" ")[0], x: r ? r.left + r.width / 2 : 0, y: r ? r.top + r.height / 2 : 0 });
  }, true);
  document.addEventListener("input", () => rec("key"), true);
  new MutationObserver((muts) => {
    for (const m of muts) {
      if (m.type === "childList") for (const n of m.addedNodes) {
        if (!(n instanceof HTMLElement)) continue;
        if (n.matches(".cf-row.bot") && n.querySelector(".cf-typing")) rec("typing");
        else if (n.matches(".cf-row.bot") && n.querySelector(".cf-card")) rec("review");
        else if (n.matches(".cf-row.bot") && n.querySelector(".cf-msg")) rec("bot", { text: n.textContent.slice(0, 60) });
        else if (n.matches(".cf-row.bot") && n.querySelector(".cf-card")) rec("review");
        else if (n.matches(".cf-row.user")) rec("user", { text: n.textContent });
        else if (n.matches(".cf-chips")) rec("chips");
      }
      if (m.type === "attributes" && m.target.classList?.contains("sent")) rec("sent");
    }
  }).observe(document, { childList: true, subtree: true, attributes: true, attributeFilter: ["class", "data-state"] });
  addEventListener("cf:lead", () => rec("lead"));
  addEventListener("cf:autopilot-done", () => rec("done"));
};
const NO_CARET = ".cf-in { caret-color: transparent !important; } ::-webkit-scrollbar { display: none; }";

async function record(page, dir, { until, maxSec, after = 0 }) {
  fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
  let n = 0, endAt = null;
  for (;;) {
    await page.evaluate(SYNC);
    await page.screenshot({ path: path.join(dir, `${String(n).padStart(5, "0")}.jpg`), type: "jpeg", quality: 93 });
    n++;
    const t = n / FPS;
    if (endAt === null && (await until(page))) endAt = t + after;
    if ((endAt !== null && t >= endAt) || t >= maxSec) break;
    await page.clock.runFor(Math.round((n * 1000) / FPS) - Math.round(((n - 1) * 1000) / FPS));
    if (n % 60 === 0) process.stdout.write(`  ${t.toFixed(0)}s`);
  }
  console.log(`\n  ${n} frames -> ${dir}`);
  return n;
}

const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || undefined });
await fetch(`${BASE}/api/demo/reset`, { method: "POST" });

// ---------------------------------------------------------------- 1. the phone: the full chat -> lead flow
console.log("phone");
const phoneCtx = await browser.newContext({ viewport: { width: 390, height: 716 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, timezoneId: TZ, locale: "en-US" });
const phone = await phoneCtx.newPage();
await phone.clock.install({ time: new Date() });
await phone.addInitScript(RECORDER);
await phone.goto(`${BASE}/`, { waitUntil: "load" });
await phone.addStyleTag({ content: NO_CARET });
await phone.evaluate(() => document.fonts.ready);
await phone.clock.pauseAt(Date.now() + 1000);       // from here on, time only moves when we step it
await phone.clock.runFor(500);
await phone.evaluate(() => { window.runAutopilot(); });
const t0 = await phone.evaluate(() => performance.now());
const frames = await record(phone, path.join(OUT, "phone"), { until: (p) => p.evaluate(() => window.__ev.some((e) => e.type === "done")), maxSec: 60, after: 0.4 });
const events = (await phone.evaluate(() => window.__ev)).map((e) => ({ ...e, t: +((e.t - t0) / 1000).toFixed(3) })).filter((e) => e.t >= 0);
fs.writeFileSync(path.join(OUT, "phone-events.json"), JSON.stringify({ fps: FPS, frames, events }, null, 1));
await phoneCtx.close();

// ---------------------------------------------------------------- 2. the dashboard: the lead arriving
console.log("dashboard");
const deskCtx = await browser.newContext({ viewport: { width: 1100, height: 680 }, deviceScaleFactor: 2, timezoneId: TZ, locale: "en-US" });
const dash = await deskCtx.newPage();
await dash.clock.install({ time: new Date() });
await dash.clock.pauseAt(Date.now() + 1000);        // frozen before load, so the replay timer starts with frame 0
await dash.goto(`${BASE}/dashboard?replay=1`, { waitUntil: "load" });
await dash.addStyleTag({ content: NO_CARET });
await dash.evaluate(() => document.fonts.ready);
await dash.waitForSelector("[data-live].on");
await dash.waitForSelector(".row");
await record(dash, path.join(OUT, "dash"), { until: () => false, maxSec: 5.0 });
await deskCtx.close();

await browser.close();
console.log("done");
