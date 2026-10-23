// Fills the page from /api/config (the same facts the assistant answers from), then mounts the chat widget.
import { ICON, LOGO } from "./icons.js";
import { mountChat } from "./chat.js";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const el = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; };

const config = await fetch("/api/config").then((r) => r.json());
const B = config.business;

$$("[data-logo]").forEach((n) => (n.innerHTML = LOGO));
$$("[data-icon]").forEach((n) => (n.innerHTML = ICON[n.dataset.icon] ?? ""));
$$("[data-icon-btn]").forEach((n) => n.insertAdjacentHTML("afterbegin", ICON[n.dataset.iconBtn] ?? ""));
$$('[data-fact="phone"]').forEach((n) => (n.textContent = B.phone));
$$('[data-fact="email"]').forEach((n) => (n.textContent = B.email));
$$('[data-fact="emergencyHow"]').forEach((n) => (n.textContent = B.emergency.howTo));

const grid = $("[data-services]");
for (const s of B.services) {
  const card = el("article", `svc${s.id === "emergency" ? " em" : ""}`);
  const i = el("i"); i.innerHTML = ICON[s.id] ?? ICON.leak;
  card.append(i, el("h3", null, s.name), el("p", null, s.blurb));
  grid.append(card);
}
const areas = $("[data-areas]");
for (const a of B.areas) areas.append(el("li", null, a));
const hours = $("[data-hours]");
for (const h of B.hours) { const row = el("div"); row.append(el("dt", null, h.days), el("dd", null, h.time)); hours.append(row); }

const chat = mountChat(config);
$$("[data-open-chat]").forEach((b) => b.addEventListener("click", () => chat.open(b.dataset.openChat)));
