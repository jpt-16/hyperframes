// Lead inbox: loads /api/leads, then listens on /api/leads/stream so new chat leads appear without a refresh.
import { ICON, LOGO } from "./icons.js";

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const el = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; };
$$("[data-logo]").forEach((n) => (n.innerHTML = LOGO));
$(".icon-btn").innerHTML = ICON.close;

const STATUS = { new: "New", contacted: "Contacted", scheduled: "Scheduled" };
const EMERGENCY = "Emergency plumbing";
let leads = [];
let openId = null;

const timeOf = (iso) => new Date(iso).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
function ago(iso) {
  const min = Math.floor((Date.now() - new Date(iso)) / 60000);
  if (min < 1) return "Just now";
  if (min < 60) return `${min} min ago`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h} h ago`;
  return h < 48 ? "Yesterday" : new Date(iso).toLocaleDateString([], { month: "short", day: "numeric" });
}

function rowFor(lead) {
  const wrap = el("div", "row-wrap"); wrap.dataset.id = lead.id;
  const clip = el("div", "row-clip");
  const row = el("div", "row"); row.tabIndex = 0;
  const cust = el("div", "cust"); const nm = el("b", null, lead.name);
  if (lead.sample) nm.append(el("span", "tag-sample", "Sample"));
  cust.append(nm, el("small", null, lead.contact));
  const svc = el("div", `svc-cell${lead.service === EMERGENCY ? " em" : ""}`); svc.append(el("i"), el("span", null, lead.service));
  const det = el("div", "det", lead.details || "No details given");
  const when = el("div", "when"); when.append(el("span", null, ago(lead.createdAt)), el("small", null, timeOf(lead.createdAt)));
  const st = el("span", `status ${lead.status}`, STATUS[lead.status]);
  row.append(cust, svc, det, when, st);
  row.addEventListener("click", () => openDrawer(lead.id));
  row.addEventListener("keydown", (e) => { if (e.key === "Enter") openDrawer(lead.id); });
  clip.append(row); wrap.append(clip);
  return wrap;
}

function kpis(animate) {
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const vals = {
    new: leads.filter((l) => l.status === "new").length,
    today: leads.filter((l) => new Date(l.createdAt) >= today).length,
    emergency: leads.filter((l) => l.service === EMERGENCY).length,
    total: leads.length,
  };
  for (const [k, v] of Object.entries(vals)) {
    const n = $(`[data-kpi="${k}"]`);
    if (n.textContent !== String(v)) { n.textContent = v; if (animate) { n.classList.remove("bump"); void n.offsetWidth; n.classList.add("bump"); } }
  }
}

function render() {
  const rows = $("[data-rows]"); rows.replaceChildren(...leads.map(rowFor));
  $("[data-empty]").hidden = leads.length > 0;
  kpis(false);
}

function addLead(lead) {
  leads.unshift(lead);
  const wrap = rowFor(lead);
  wrap.classList.add("enter");
  const row = $(".row", wrap); row.classList.add("fresh");
  $("[data-rows]").prepend(wrap);
  $("[data-empty]").hidden = true;
  requestAnimationFrame(() => requestAnimationFrame(() => wrap.classList.remove("enter")));
  setTimeout(() => row.classList.remove("fresh"), 2600);
  kpis(true);
  toast(lead);
}

let toastTimer;
function toast(lead) {
  const t = $("[data-toast]");
  t.replaceChildren();
  const ic = el("span", "t-ic"); ic.innerHTML = ICON.chat;
  const tx = el("div"); tx.append(el("b", null, `New lead · ${lead.name}`), el("small", null, `${lead.service} · via website chat`));
  t.append(ic, tx);
  t.classList.add("on");
  clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove("on"), 3600);
}

function openDrawer(id) {
  const lead = leads.find((l) => l.id === id); if (!lead) return;
  openId = id;
  const d = (k) => $(`[data-d="${k}"]`);
  d("ref").textContent = lead.ref + (lead.sample ? " · sample" : "");
  d("name").textContent = lead.name;
  const isEmail = lead.contact.includes("@");
  const a = el("a", null, lead.contact); a.href = isEmail ? `mailto:${lead.contact}` : `tel:${lead.contact.replace(/[^\d+]/g, "")}`;
  d("contact").replaceChildren(a);
  d("service").textContent = lead.service;
  d("details").textContent = lead.details || "None";
  d("received").textContent = `${ago(lead.createdAt)} · ${timeOf(lead.createdAt)}`;
  d("source").textContent = lead.source;
  $$("[data-status]").forEach((b) => b.classList.toggle("on", b.dataset.status === lead.status));
  const convo = $("[data-convo]");
  convo.replaceChildren(...(lead.transcript?.length ? lead.transcript.map((m) => el("div", `m ${m.role}`, m.text)) : [el("p", "none", "No transcript stored for this lead.")]));
  $("[data-drawer]").classList.add("open");
  $("[data-drawer]").setAttribute("aria-hidden", "false");
}
function closeDrawer() { openId = null; $("[data-drawer]").classList.remove("open"); $("[data-drawer]").setAttribute("aria-hidden", "true"); }
$$("[data-close]").forEach((b) => b.addEventListener("click", closeDrawer));
document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeDrawer(); });

$$("[data-status]").forEach((b) => b.addEventListener("click", async () => {
  if (!openId) return;
  const r = await fetch(`/api/leads/${openId}`, { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify({ status: b.dataset.status }) });
  if (r.ok) { const { lead } = await r.json(); update(lead); openDrawer(lead.id); }
}));

function update(lead) {
  const i = leads.findIndex((l) => l.id === lead.id); if (i < 0) return;
  leads[i] = lead;
  const old = $(`.row-wrap[data-id="${lead.id}"]`); if (old) old.replaceWith(rowFor(lead));
  kpis(true);
}

$("[data-reset]").addEventListener("click", async () => { await fetch("/api/demo/reset", { method: "POST" }); });

async function load() {
  const data = await fetch("/api/leads").then((r) => r.json());
  leads = data.leads; render();
}

function connect() {
  const live = $("[data-live]");
  const es = new EventSource("/api/leads/stream");
  es.onopen = () => { live.classList.add("on"); live.lastElementChild.textContent = "Live"; };
  es.onerror = () => { live.classList.remove("on"); live.lastElementChild.textContent = "Reconnecting"; };
  es.onmessage = (e) => {
    const evt = JSON.parse(e.data);
    if (evt.type === "lead") addLead(evt.lead);
    else if (evt.type === "update") update(evt.lead);
    else if (evt.type === "reset") { closeDrawer(); load(); }
  };
}

await load();
connect();
// ?replay=1 (used by /stage after the autopilot): show the newest real lead arriving, as it did a moment ago.
if (new URLSearchParams(location.search).get("replay") === "1") {
  const latest = leads.find((l) => !l.sample);
  if (latest) {
    leads = leads.filter((l) => l !== latest); render();
    setTimeout(() => addLead(latest), 700);
  }
}
setInterval(() => $$(".row-wrap").forEach((w) => { const l = leads.find((x) => x.id === w.dataset.id); if (l) $(".when span", w).textContent = ago(l.createdAt); }), 30000);
