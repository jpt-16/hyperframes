// API smoke test (no browser needed). Start the server first: npm start, then npm test.
const BASE = process.env.BASE || "http://127.0.0.1:4310";
let fails = 0;
const check = (cond, msg) => { console.log(`${cond ? "✓" : "✗"} ${msg}`); if (!cond) fails++; };
const ask = async (q) => (await fetch(`${BASE}/api/chat`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ messages: [{ role: "user", content: q }] }) })).json();

const cfg = await fetch(`${BASE}/api/config`).then((r) => r.json());
check(["demo", "live"].includes(cfg.mode), `server is up (${cfg.mode} mode)`);
if (cfg.mode === "demo") {
  check((await ask("Do you handle emergencies?")).text.includes("24/7"), "emergency question answered from facts");
  check((await ask("Do you serve Lakewood?")).text.startsWith("Yes, Lakewood"), "listed area confirmed");
  check((await ask("Do you serve Boulder?")).text.includes("isn't on ClearFlow's listed service area"), "unlisted area not confirmed");
  check((await ask("How much for a new water heater?")).text.includes("doesn't quote prices"), "no prices given");
  check((await ask("Do you do HVAC?")).text.includes("isn't one of the services"), "unlisted service not confirmed");
  check((await ask("Can you come today?")).text.includes("can't promise a time"), "no availability promised");
  check((await ask("What's your warranty?")).text.includes("don't have that information"), "unknown policy not invented");
  check((await ask("Book a plumber")).action === "start_booking", "booking starts the lead form");
}
const bad = await fetch(`${BASE}/api/leads`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ name: "A", contact: "nope", service: "Roofing" }) });
check(bad.status === 422, "invalid lead rejected (422)");
const good = await fetch(`${BASE}/api/leads`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ name: "Smoke Test", contact: "smoke@example.com", service: "Drain cleaning", details: "test" }) });
check(good.status === 201, "valid lead stored (201)");
const list = await fetch(`${BASE}/api/leads`).then((r) => r.json());
check(list.leads[0].name === "Smoke Test", "new lead is first in the inbox");
await fetch(`${BASE}/api/demo/reset`, { method: "POST" });
process.exit(fails ? 1 : 0);
