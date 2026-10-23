// ClearFlow chat widget. Questions go to /api/chat (scripted demo engine or live AI, decided by the server).
// Booking is always the same deterministic, validated form flow, so a lead is never made up.
import { ICON, LOGO } from "./icons.js";

const el = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; };
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const PHONE = /^[+()\-.\s\d]{7,20}$/;
const EMAIL = /^[^\s@]{1,64}@[^\s@]{1,190}\.[a-z]{2,24}$/i;
const validContact = (v) => { const d = v.replace(/\D/g, ""); return EMAIL.test(v) || (PHONE.test(v) && d.length >= 10 && d.length <= 15); };

export function mountChat(config) {
  const B = config.business;
  const live = config.mode === "live";
  const history = [];          // what the server sees: {role, content}
  const transcript = [];       // what the dashboard shows: {role, text}
  let flow = null;             // booking state
  let opened = false;
  let busy = 0;
  let idleWaiters = [];

  const root = el("div", "cf");
  root.dataset.state = "closed";
  root.innerHTML = `
    <button class="cf-launch" type="button" aria-label="Open chat with ClearFlow">${ICON.chat}<span>Ask ClearFlow</span><i class="cf-online" aria-hidden="true"></i></button>
    <section class="cf-panel" role="dialog" aria-label="ClearFlow assistant" aria-hidden="true">
      <header class="cf-head">
        <span class="mark">${LOGO}</span>
        <div class="cf-who"><b>ClearFlow Assistant</b><small><i class="cf-dot"></i>${live ? "Online · answers from ClearFlow's info" : "Demo mode · scripted from ClearFlow's info"}</small></div>
        <button class="cf-x" type="button" aria-label="Close chat">${ICON.close}</button>
      </header>
      <div class="cf-log" aria-live="polite"></div>
      <form class="cf-compose" autocomplete="off">
        <input class="cf-in" type="text" maxlength="300" placeholder="Ask about services, areas, hours…" aria-label="Message">
        <button class="cf-send" type="submit" aria-label="Send">${ICON.send}</button>
      </form>
      <p class="cf-note">${live ? "AI assistant" : "Demo assistant"} · answers only from ClearFlow's listed info</p>
    </section>`;
  document.body.append(root);
  const $ = (s) => root.querySelector(s);
  const log = $(".cf-log"), input = $(".cf-in"), form = $(".cf-compose");

  // ------------------------------------------------------------------ idle tracking (used by the autopilot)
  const begin = () => { busy++; root.classList.add("is-busy"); };
  const end = () => { busy = Math.max(0, busy - 1); if (!busy) { root.classList.remove("is-busy"); idleWaiters.forEach((f) => f()); idleWaiters = []; } };
  const whenIdle = () => (busy ? new Promise((r) => idleWaiters.push(r)) : Promise.resolve());

  // ------------------------------------------------------------------ scrolling (rAF tween, so recordings are smooth and repeatable)
  let scrollAnim = 0;
  function scrollDown() {
    const from = log.scrollTop, to = log.scrollHeight - log.clientHeight;
    if (to - from < 2) return;
    const t0 = performance.now(), id = ++scrollAnim;
    const step = (now) => {
      if (id !== scrollAnim) return;
      const u = Math.min(1, (now - t0) / 320), e = 1 - Math.pow(1 - u, 3);
      log.scrollTop = from + (to - from) * e;
      if (u < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  // ------------------------------------------------------------------ rendering
  function rich(text) {
    // **bold**, line breaks, "• " bullet lines. Built with DOM nodes (no innerHTML), every word wrapped for the reveal.
    const box = el("div", "cf-rich");
    const words = [];
    let list = null;
    text = text.replace(/\((\d{3})\) (\d{3}-\d{4})/g, "($1)\u00a0$2");   // keep phone numbers on one line
    for (const line of text.split("\n")) {
      if (!line.trim()) { list = null; continue; }
      const bullet = line.startsWith("• ");
      let target;
      if (bullet) { if (!list) { list = el("ul"); box.append(list); } target = el("li"); list.append(target); }
      else { list = null; target = el("p"); box.append(target); }
      const parts = (bullet ? line.slice(2) : line).split(/(\*\*[^*]+\*\*)/);
      for (const part of parts) {
        if (!part) continue;
        const strong = part.startsWith("**") && part.endsWith("**");
        const host = strong ? el("strong") : target;
        if (strong) target.append(host);
        for (const w of (strong ? part.slice(2, -2) : part).split(/([ \t]+)/)) {
          if (!w) continue;
          if (/^[ \t]+$/.test(w)) { host.append(document.createTextNode(w)); continue; }
          const span = el("span", "w", w); host.append(span); words.push(span);
        }
      }
    }
    return { box, words };
  }

  function addUser(text) {
    const row = el("div", "cf-row user");
    row.append(el("div", "cf-msg user", text));
    log.append(row);
    history.push({ role: "user", content: text });
    transcript.push({ role: "user", text });
    scrollDown();
  }

  async function botSay(text, { quick = false } = {}) {
    begin();
    if (!quick) {
      const typing = el("div", "cf-row bot");
      typing.innerHTML = `<div class="cf-typing" aria-label="Assistant is typing"><i></i><i></i><i></i></div>`;
      log.append(typing); scrollDown();
      await wait(620 + Math.min(720, text.length * 4));
      typing.remove();
    }
    const row = el("div", "cf-row bot");
    const msg = el("div", "cf-msg bot");
    const { box, words } = rich(text);
    msg.append(box); row.append(msg); log.append(row);
    if (quick) words.forEach((w) => w.classList.add("on"));
    else for (let i = 0; i < words.length; i += 2) {
      words[i].classList.add("on"); words[i + 1]?.classList.add("on");
      if (i % 12 === 0) scrollDown();
      await wait(34);
    }
    history.push({ role: "assistant", content: text });
    transcript.push({ role: "assistant", text });
    scrollDown();
    end();
    return row;
  }

  function chips(labels, onPick, cls = "") {
    if (!labels?.length) return;
    const row = el("div", `cf-chips ${cls}`);
    labels.forEach((label, i) => {
      const b = el("button", "cf-chip", label);
      b.type = "button";
      b.style.animationDelay = `${i * 55}ms`;
      b.addEventListener("click", () => {
        if (busy) return;
        row.classList.add("gone");
        setTimeout(() => row.remove(), 180);
        onPick(label);
      });
      row.append(b);
    });
    log.append(row); scrollDown();
  }
  const clearChips = () => log.querySelectorAll(".cf-chips").forEach((c) => { c.classList.add("gone"); setTimeout(() => c.remove(), 180); });

  // ------------------------------------------------------------------ Q&A
  async function ask(text) {
    begin();
    try {
      const r = await fetch("/api/chat", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ messages: history }) }).then((x) => x.json());
      await botSay(r.text);
      if (r.action === "start_booking") await startBooking();
      else chips(r.suggestions, send);
    } catch {
      await botSay(`Sorry, something went wrong on my end. You can call ClearFlow at **${B.phone}**.`);
    } finally { end(); }
  }

  // ------------------------------------------------------------------ booking flow
  const setHint = (p) => (input.placeholder = p);
  async function startBooking() {
    flow = { step: "name", data: {} };
    await botSay("First, what's your name?");
    setHint("Your name");
  }
  function matchService(text) {
    const t = text.toLowerCase();
    return B.services.find((s) => t.includes(s.name.toLowerCase()) || (s.keywords || []).some((k) => t.includes(k)));
  }
  async function pickService(name) {
    const svc = B.services.find((s) => s.name === name);
    flow.data.service = svc.name;
    if (svc.id === "emergency") await botSay(`If water is leaking right now, call the 24/7 line: **${B.phone}**. I'll still send your request to dispatch.`);
    flow.step = "details";
    await botSay("Anything the plumber should know? This part's optional.");
    chips(["Skip"], (l) => send(l));
    setHint("Describe what's happening");
  }
  async function flowInput(text) {
    const f = flow;
    if (f.step === "name") {
      const name = text.replace(/\s+/g, " ").trim();
      if (name.length < 2 || name.length > 80) return botSay("Could you share your name?");
      f.data.name = name; f.step = "contact";
      await botSay(`Thanks, ${name.split(" ")[0]}. What's the best phone number or email to reach you?`);
      return setHint("Phone number or email");
    }
    if (f.step === "contact") {
      if (!validContact(text.trim())) return botSay("That doesn't look like a phone number or email. Mind checking it?");
      f.data.contact = text.trim(); f.step = "service";
      await botSay("Got it. What do you need help with?");
      chips(B.services.map((s) => s.name), (l) => send(l), "svc");
      return setHint("Pick an option or type it");
    }
    if (f.step === "service") {
      const svc = matchService(text);
      if (!svc) { await botSay("Pick one of the options below so dispatch knows who to send."); return chips(B.services.map((s) => s.name), (l) => send(l), "svc"); }
      clearChips();
      return pickService(svc.name);
    }
    if (f.step === "details") {
      clearChips();
      f.data.details = /^skip$/i.test(text.trim()) ? "" : text.trim().slice(0, 500);
      f.step = "review";
      setHint("Ask about services, areas, hours…");
      return review();
    }
  }

  function review() {
    const d = flow.data;
    const row = el("div", "cf-row bot");
    const card = el("div", "cf-card");
    card.innerHTML = `<div class="cf-card-h"><span class="mono">Review your request</span></div><dl class="cf-dl"></dl>
      <div class="cf-card-a"><button type="button" class="cf-primary">Send request</button><button type="button" class="cf-link">Start over</button></div>`;
    const dl = card.querySelector(".cf-dl");
    for (const [k, v] of [["Name", d.name], ["Contact", d.contact], ["Service", d.service], ["Details", d.details || "None"]]) {
      const r = el("div"); r.append(el("dt", null, k), el("dd", null, v)); dl.append(r);
    }
    row.append(card); log.append(row); scrollDown();
    const sendBtn = card.querySelector(".cf-primary");
    sendBtn.addEventListener("click", () => submit(card, sendBtn));
    card.querySelector(".cf-link").addEventListener("click", () => { if (!busy) { card.classList.add("dim"); startBooking(); } });
  }

  async function submit(card, btn) {
    if (busy || btn.disabled) return;
    begin();
    btn.disabled = true;
    btn.innerHTML = `<i class="cf-spin"></i>Sending…`;
    const started = performance.now();
    let res;
    try {
      res = await fetch("/api/leads", { method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ ...flow.data, transcript }) });
    } catch { res = null; }
    await wait(Math.max(0, 900 - (performance.now() - started)));
    if (!res || !res.ok) {
      btn.disabled = false; btn.textContent = "Try again";
      end();
      return botSay(`I couldn't send that just now. Please try again, or call **${B.phone}**.`);
    }
    const { lead } = await res.json();
    const emergency = lead.service === "Emergency plumbing";
    card.classList.add("sent");
    card.innerHTML = `
      <div class="cf-ok"><span class="cf-ok-ic">${ICON.check}</span><div><b>Request sent</b><span class="mono">${lead.ref}</span></div></div>
      <p class="cf-ok-p"></p>
      ${emergency ? `<a class="cf-em" href="${B.phoneHref}">${ICON.phone}<span>Leaking now? Call <b>${B.phone}</b></span></a>` : ""}`;
    card.querySelector(".cf-ok-p").textContent = B.policies.followUp;
    transcript.push({ role: "assistant", text: `Request sent (${lead.ref}).` });
    flow = null;
    scrollDown();
    window.dispatchEvent(new CustomEvent("cf:lead", { detail: lead }));
    if (window.parent !== window) window.parent.postMessage({ type: "cf-lead", lead }, location.origin);
    end();
    await wait(500);
    chips(["What are your hours?", "Do you handle emergencies?"], send);
  }

  // ------------------------------------------------------------------ input
  async function send(text) {
    text = String(text ?? "").trim();
    if (!text || busy) return;
    clearChips();
    addUser(text);
    if (flow && flow.step !== "review") {
      if (flow.step === "service" && B.services.some((s) => s.name === text)) return pickService(text);
      return flowInput(text);
    }
    return ask(text);
  }
  form.addEventListener("submit", (e) => { e.preventDefault(); const v = input.value; input.value = ""; send(v); });

  // ------------------------------------------------------------------ open / close
  async function open(prompt) {
    root.dataset.state = "open";
    $(".cf-panel").setAttribute("aria-hidden", "false");
    document.documentElement.classList.add("cf-locked");
    if (!opened) {
      opened = true;
      await wait(260);
      await botSay("Hi, I'm ClearFlow's assistant. I can answer questions about our services, service area, hours and emergency help, or get a plumber booked for you.", { quick: !!prompt });
      if (!prompt) chips(["Do you handle emergencies?", "Do you serve Lakewood?", "What are your hours?", "Book a plumber"], send);
    }
    if (prompt) { await wait(160); send(prompt); }
    else if (matchMedia("(min-width: 561px)").matches) input.focus({ preventScroll: true });
  }
  function close() {
    root.dataset.state = "closed";
    $(".cf-panel").setAttribute("aria-hidden", "true");
    document.documentElement.classList.remove("cf-locked");
  }
  $(".cf-launch").addEventListener("click", () => open());
  $(".cf-x").addEventListener("click", close);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && root.dataset.state === "open") close(); });

  const api = { open, close, send, whenIdle, root, input, form };
  window.ClearFlowChat = api;
  return api;
}
