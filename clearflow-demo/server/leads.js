// Lead storage: a JSON file in data/ (git-ignored) plus live push to open dashboards (SSE).
// Sample leads are clearly flagged `sample: true` and labelled in the dashboard.
import fs from "node:fs";
import path from "node:path";
import { SERVICE_NAMES } from "./business.js";

const FILE = path.join(path.dirname(new URL(import.meta.url).pathname), "..", "data", "leads.json");
const clients = new Set();
let leads = [];
let nextRef = 2041;

const ago = (min) => new Date(Date.now() - min * 60000).toISOString();
function samples() {
  return [
    { name: "Dana Whitfield", contact: "(555) 014-2286", service: "Drain cleaning", details: "Kitchen sink drains slowly, worse after the dishwasher runs.", createdAt: ago(42), status: "new" },
    { name: "Luis Ortega", contact: "luis.ortega@example.com", service: "Fixture & faucet installation", details: "Replace two bathroom faucets (customer has the faucets).", createdAt: ago(128), status: "contacted" },
    { name: "Priya Raman", contact: "(555) 014-6631", service: "Leak detection & repair", details: "Water stain spreading on the basement ceiling.", createdAt: ago(305), status: "contacted" },
    { name: "Tom Becker", contact: "(555) 014-9018", service: "Sump pump service", details: "Pump runs constantly.", createdAt: ago(1460), status: "scheduled" },
  ].map((l) => ({ ...l, id: `L${nextRef}`, ref: `CF-${nextRef++}`, source: "Website chat", sample: true, transcript: [] }));
}

export function loadLeads() {
  try {
    const saved = JSON.parse(fs.readFileSync(FILE, "utf8"));
    leads = saved.leads; nextRef = saved.nextRef;
  } catch {
    leads = samples(); save();
  }
}
function save() {
  fs.mkdirSync(path.dirname(FILE), { recursive: true });
  fs.writeFileSync(FILE, JSON.stringify({ leads, nextRef }, null, 1));
}

export const listLeads = () => [...leads].sort((a, b) => b.createdAt.localeCompare(a.createdAt));

const PHONE = /^[+()\-.\s\d]{7,20}$/;
const EMAIL = /^[^\s@]{1,64}@[^\s@]{1,190}\.[a-z]{2,24}$/i;

export function validateLead(body) {
  const name = String(body?.name ?? "").trim();
  const contact = String(body?.contact ?? "").trim();
  const service = String(body?.service ?? "").trim();
  const details = String(body?.details ?? "").trim();
  const errors = [];
  if (name.length < 2 || name.length > 80) errors.push("name");
  const digits = contact.replace(/\D/g, "");
  if (!(EMAIL.test(contact) || (PHONE.test(contact) && digits.length >= 10 && digits.length <= 15))) errors.push("contact");
  if (!SERVICE_NAMES.includes(service)) errors.push("service");
  if (details.length > 500) errors.push("details");
  const transcript = Array.isArray(body?.transcript)
    ? body.transcript.slice(-12).map((m) => ({ role: m.role === "user" ? "user" : "assistant", text: String(m.text ?? "").slice(0, 400) }))
    : [];
  return { errors, lead: { name, contact, service, details, transcript } };
}

export function addLead(data) {
  const lead = { ...data, id: `L${nextRef}`, ref: `CF-${nextRef++}`, source: "Website chat", status: "new", sample: false, createdAt: new Date().toISOString() };
  leads.push(lead); save();
  broadcast({ type: "lead", lead });
  return lead;
}

export function setStatus(id, status) {
  const lead = leads.find((l) => l.id === id);
  if (!lead || !["new", "contacted", "scheduled"].includes(status)) return null;
  lead.status = status; save();
  broadcast({ type: "update", lead });
  return lead;
}

export function resetDemo() {
  nextRef = 2041; leads = samples(); save();
  broadcast({ type: "reset" });
}

export function subscribe(res) {
  clients.add(res);
  res.on("close", () => clients.delete(res));
}
function broadcast(evt) {
  for (const res of clients) res.write(`data: ${JSON.stringify(evt)}\n\n`);
}
