// End-to-end check of the demo in a real browser (Playwright + Chromium).
//   npm start   (in another terminal)
//   node tools/verify.mjs [outDir]
// Runs the full chat -> lead -> dashboard flow on desktop and mobile, checks validation,
// fails on any console error, and saves screenshots.
import { createRequire } from "node:module";
const { chromium } = createRequire(import.meta.url)("playwright");   // local install, or a global one via NODE_PATH
import fs from "node:fs";

const BASE = process.env.BASE || "http://127.0.0.1:4310";
const OUT = process.argv[2] || "verify-shots";
fs.mkdirSync(OUT, { recursive: true });
const errors = [];
const ok = (cond, msg) => { if (!cond) throw new Error("FAIL: " + msg); console.log("  ✓ " + msg); };

const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || undefined });
const watch = (page, tag) => {
  page.on("console", (m) => { if (m.type() === "error") errors.push(`${tag}: ${m.text()}`); });
  page.on("pageerror", (e) => errors.push(`${tag}: ${e.message}`));
};

await fetch(`${BASE}/api/demo/reset`, { method: "POST" });

// ---------------------------------------------------------------- desktop: site + dashboard side by side
console.log("desktop");
const desk = await browser.newContext({ viewport: { width: 1366, height: 860 }, deviceScaleFactor: 1 });
const dash = await desk.newPage(); watch(dash, "dashboard");
await dash.goto(`${BASE}/dashboard`, { waitUntil: "load" });
await dash.waitForSelector("[data-live].on");
await dash.waitForSelector(".row");
const before = await dash.locator(".row").count();
ok(before === 4, `dashboard shows the 4 sample leads (${before})`);
await dash.screenshot({ path: `${OUT}/dash-before.png` });

const site = await desk.newPage(); watch(site, "site");
await site.goto(`${BASE}/`, { waitUntil: "networkidle" });
ok(await site.locator(".svc").count() === 8, "8 services rendered from business facts");
ok(await site.locator("[data-areas] li").count() === 8, "8 service areas rendered");
await site.screenshot({ path: `${OUT}/site-desktop.png` });
await site.screenshot({ path: `${OUT}/site-desktop-full.png`, fullPage: true });

const done = site.evaluate(() => new Promise((r) => addEventListener("cf:autopilot-done", () => r(true), { once: true })));
await site.evaluate(() => { window.runAutopilot(); });
await site.waitForFunction(() => [...document.querySelectorAll(".cf-msg.bot")].some((m) => m.textContent.includes("Lakewood is in ClearFlow's service area")), null, { timeout: 30000 });
await site.screenshot({ path: `${OUT}/chat-desktop-qa.png` });
await site.waitForSelector(".cf-card:not(.sent) .cf-primary", { timeout: 40000 });
await site.screenshot({ path: `${OUT}/chat-desktop-review.png` });
await done;
const ref = await site.locator(".cf-card.sent .mono").textContent();
ok(/^CF-\d{4}$/.test(ref), `lead submitted, reference ${ref}`);
await site.screenshot({ path: `${OUT}/chat-desktop-sent.png` });

await dash.waitForFunction(() => document.querySelector(".row .cust b")?.textContent.startsWith("Marcus Bell"), null, { timeout: 5000 });
ok(true, "new lead appeared live at the top of the dashboard (no refresh)");
ok(await dash.locator(".toast.on").count() === 1, "dashboard toast shown");
await dash.screenshot({ path: `${OUT}/dash-after.png` });
await dash.locator(".row").first().click();
await dash.waitForSelector(".drawer.open");
await dash.waitForTimeout(500);
ok((await dash.locator(".convo .m").count()) >= 6, "lead drawer shows the chat transcript");
await dash.screenshot({ path: `${OUT}/dash-drawer.png` });
const leads = await fetch(`${BASE}/api/leads`).then((r) => r.json());
const L = leads.leads[0];
ok(L.name === "Marcus Bell" && L.service === "Water heater repair & installation" && L.contact === "(555) 014-3391" && L.details.startsWith("No hot water"), "stored lead has name, contact, service, details");

// ---------------------------------------------------------------- validation + honesty
console.log("validation");
const v = await desk.newPage(); watch(v, "validation");
await v.goto(`${BASE}/`, { waitUntil: "networkidle" });
await v.locator(".cf-launch").click();
await v.waitForSelector(".cf-chip");
const say = async (text) => { await v.evaluate(() => window.ClearFlowChat.whenIdle()); await v.fill(".cf-in", text); await v.press(".cf-in", "Enter"); await v.waitForTimeout(150); await v.evaluate(() => window.ClearFlowChat.whenIdle()); };
await say("How much is a new water heater?");
ok((await v.locator(".cf-msg.bot").last().textContent()).includes("doesn't quote prices"), "no prices invented");
await say("Do you install furnaces?");
ok((await v.locator(".cf-msg.bot").last().textContent()).includes("isn't one of the services"), "unlisted service is not confirmed");
await say("Do you serve Boulder?");
ok((await v.locator(".cf-msg.bot").last().textContent()).includes("isn't on ClearFlow's listed service area"), "unlisted area is not confirmed");
await say("Can you come today?");
ok((await v.locator(".cf-msg.bot").last().textContent()).includes("can't promise a time"), "no availability promised");
await say("Book a plumber");
await say("Jo");
await say("not a number");
ok((await v.locator(".cf-msg.bot").last().textContent()).includes("doesn't look like a phone number or email"), "bad contact rejected");
await say("jo@example.com");
await say("something weird");
ok((await v.locator(".cf-msg.bot").last().textContent()).includes("Pick one of the options"), "unknown service asks to pick from the list");
await v.screenshot({ path: `${OUT}/chat-validation.png` });
await v.close();

// ---------------------------------------------------------------- mobile
console.log("mobile");
const mob = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
const m = await mob.newPage(); watch(m, "mobile");
await m.goto(`${BASE}/`, { waitUntil: "networkidle" });
const overflow = await m.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
ok(overflow <= 0, `no horizontal scroll on mobile (${overflow})`);
await m.screenshot({ path: `${OUT}/site-mobile.png` });
await m.screenshot({ path: `${OUT}/site-mobile-full.png`, fullPage: true });
const mdone = m.evaluate(() => new Promise((r) => addEventListener("cf:autopilot-done", () => r(true), { once: true })));
await m.evaluate(() => { window.runAutopilot(); });
await m.waitForFunction(() => [...document.querySelectorAll(".cf-msg.bot")].some((x) => x.textContent.includes("emergencies")), null, { timeout: 20000 });
await m.waitForTimeout(1400);
await m.screenshot({ path: `${OUT}/chat-mobile-qa.png` });
await m.waitForSelector(".cf-chips.svc", { timeout: 40000 });
await m.waitForTimeout(700);
await m.screenshot({ path: `${OUT}/chat-mobile-service.png` });
await mdone;
await m.screenshot({ path: `${OUT}/chat-mobile-sent.png` });
const md = await mob.newPage(); watch(md, "mobile-dash");
await md.goto(`${BASE}/dashboard?replay=1`, { waitUntil: "load" });
await md.waitForTimeout(1600);
await md.screenshot({ path: `${OUT}/dash-mobile.png` });

// ---------------------------------------------------------------- stage page loads
const st = await desk.newPage(); watch(st, "stage");
await st.goto(`${BASE}/stage`, { waitUntil: "load" });
await st.screenshot({ path: `${OUT}/stage.png` });

await browser.close();
if (errors.length) { console.log("console errors:\n" + errors.join("\n")); process.exit(1); }
console.log("all checks passed, screenshots in " + OUT);
