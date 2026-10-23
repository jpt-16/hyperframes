// Recording autopilot: plays the demo conversation through the real UI (real clicks, real typing,
// real /api calls), at a natural, repeatable pace. Nothing here bypasses the app.
// Start it with ?autopilot=1, Shift+D, or (from /stage) a postMessage {type: "cf-autopilot"}.
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
let seed = 7;
const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

async function until(fn, timeout = 8000) {
  const t0 = performance.now();
  for (;;) { const v = fn(); if (v) return v; if (performance.now() - t0 > timeout) throw new Error("autopilot: timed out"); await wait(50); }
}
const chat = () => window.ClearFlowChat;
const idle = async (extra = 0) => { await wait(60); await chat().whenIdle(); if (extra) await wait(extra); };

async function press(node, ms = 140) { node.classList.add("pressed"); await wait(ms); node.classList.remove("pressed"); node.click(); }

async function tapChip(label) {
  const chip = await until(() => [...document.querySelectorAll(".cf-chip")].find((c) => c.textContent === label && !c.closest(".gone")));
  await press(chip, 160);
}

async function type(text) {
  const { input } = chat();
  input.focus({ preventScroll: true });
  await wait(220);
  for (const ch of text) {
    input.value += ch;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    await wait(ch === " " ? 70 : 38 + rnd() * 46);
  }
  await wait(260);
  await press(chat().root.querySelector(".cf-send"), 120);
}

let running = false;
export async function runAutopilot() {
  if (running) return; running = true; seed = 7;
  try {
    await until(() => window.ClearFlowChat);
    await wait(900);
    await press(document.querySelector(".cf-launch"), 160);
    await idle(900);
    await tapChip("Do you handle emergencies?");
    await idle(1600);
    await type("Do you serve Lakewood?");
    await idle(1300);
    await tapChip("Book a plumber");
    await idle(500);
    await type("Marcus Bell");
    await idle(450);
    await type("(555) 014-3391");
    await idle(600);
    await tapChip("Water heater repair & installation");
    await idle(450);
    await type("No hot water since this morning.");
    await idle(1000);
    await press(await until(() => document.querySelector(".cf-card:not(.sent) .cf-primary")), 180);
    await until(() => document.querySelector(".cf-card.sent"));
    await idle(1800);
    window.dispatchEvent(new Event("cf:autopilot-done"));
    if (window.parent !== window) window.parent.postMessage({ type: "cf-autopilot-done" }, location.origin);
  } finally { running = false; }
}
window.runAutopilot = runAutopilot;

if (new URLSearchParams(location.search).get("autopilot") === "1") runAutopilot();
window.addEventListener("message", (e) => { if (e.origin === location.origin && e.data?.type === "cf-autopilot") runAutopilot(); });
document.addEventListener("keydown", (e) => { if (e.shiftKey && e.key === "D" && document.activeElement?.tagName !== "INPUT") runAutopilot(); });
