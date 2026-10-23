// ClearFlow Plumbing demo server (no framework). Serves the site, the lead dashboard and a small JSON API.
//   npm start                 -> http://127.0.0.1:4310 (demo mode: scripted, deterministic answers)
//   ANTHROPIC_API_KEY=... npm start   -> live mode: answers come from Claude, server-side only
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { BUSINESS, SERVICE_NAMES } from "./business.js";
import { demoReply } from "./demo-engine.js";
import { liveAvailable, liveReply } from "./live-ai.js";
import { loadLeads, listLeads, validateLead, addLead, setStatus, resetDemo, subscribe } from "./leads.js";

const ROOT = path.join(path.dirname(new URL(import.meta.url).pathname), "..", "public");
const PORT = Number(process.env.PORT || 4310);
const HOST = process.env.HOST || "127.0.0.1";
const MODE = (await liveAvailable()) ? "live" : "demo";
loadLeads();

const TYPES = { ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript", ".woff2": "font/woff2", ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon" };
const PAGES = { "/": "index.html", "/dashboard": "dashboard.html", "/stage": "stage.html" };

const json = (res, code, body) => {
  res.writeHead(code, { "content-type": "application/json", "cache-control": "no-store" });
  res.end(JSON.stringify(body));
};

function readBody(req) {
  return new Promise((resolve, reject) => {
    let size = 0; const chunks = [];
    req.on("data", (c) => { size += c.length; if (size > 32 * 1024) { reject(new Error("too large")); req.destroy(); } else chunks.push(c); });
    req.on("end", () => { try { resolve(JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}")); } catch { reject(new Error("bad json")); } });
  });
}

async function api(req, res, url) {
  if (url.pathname === "/api/config" && req.method === "GET") {
    return json(res, 200, { mode: MODE, business: { ...BUSINESS, services: BUSINESS.services.map(({ id, name, blurb, keywords }) => ({ id, name, blurb, keywords })) } });
  }
  if (url.pathname === "/api/chat" && req.method === "POST") {
    const body = await readBody(req);
    const messages = Array.isArray(body.messages) ? body.messages.slice(-20) : [];
    if (MODE === "live") {
      try {
        const r = await liveReply(messages);
        return json(res, 200, { mode: "live", text: r.text, action: r.action, suggestions: r.action ? [] : ["Book a plumber", "What are your hours?"] });
      } catch (err) {
        console.error("live AI error:", err?.status ?? "", err?.message ?? err);
        return json(res, 200, { mode: "live", text: `Sorry, I'm having trouble answering right now. You can call ${BUSINESS.phone}.`, action: null, suggestions: ["Book a plumber"] });
      }
    }
    const r = demoReply(messages);
    return json(res, 200, { mode: "demo", text: r.text, action: r.action, suggestions: r.suggestions, intent: r.intent });
  }
  if (url.pathname === "/api/leads" && req.method === "GET") return json(res, 200, { leads: listLeads(), services: SERVICE_NAMES });
  if (url.pathname === "/api/leads" && req.method === "POST") {
    const { errors, lead } = validateLead(await readBody(req));
    if (errors.length) return json(res, 422, { errors });
    return json(res, 201, { lead: addLead(lead) });
  }
  const m = url.pathname.match(/^\/api\/leads\/(L\d+)$/);
  if (m && req.method === "PATCH") {
    const lead = setStatus(m[1], (await readBody(req)).status);
    return lead ? json(res, 200, { lead }) : json(res, 404, { error: "not found" });
  }
  if (url.pathname === "/api/leads/stream" && req.method === "GET") {
    res.writeHead(200, { "content-type": "text/event-stream", "cache-control": "no-store", connection: "keep-alive" });
    res.write(": connected\n\n");
    return subscribe(res);
  }
  if (url.pathname === "/api/demo/reset" && req.method === "POST") { resetDemo(); return json(res, 200, { ok: true }); }
  return json(res, 404, { error: "not found" });
}

function serveStatic(res, url) {
  const rel = PAGES[url.pathname] ?? url.pathname.replace(/^\/+/, "");
  const file = path.normalize(path.join(ROOT, rel));
  if (!file.startsWith(ROOT + path.sep)) { res.writeHead(403); return res.end(); }
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404, { "content-type": "text/plain" }); return res.end("Not found"); }
    res.writeHead(200, { "content-type": TYPES[path.extname(file)] ?? "application/octet-stream", "cache-control": "no-cache" });
    res.end(data);
  });
}

http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  try {
    if (url.pathname.startsWith("/api/")) return await api(req, res, url);
    if (req.method !== "GET") { res.writeHead(405); return res.end(); }
    serveStatic(res, url);
  } catch (err) {
    json(res, 400, { error: err.message });
  }
}).listen(PORT, HOST, () => {
  console.log(`ClearFlow demo (${MODE} mode) -> http://${HOST}:${PORT}   dashboard: /dashboard   9:16 stage: /stage`);
});
