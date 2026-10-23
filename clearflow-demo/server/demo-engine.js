// DEMO MODE ONLY. A deterministic, rule-based responder. It is not AI: it matches
// the question to an intent and answers with text built from business.js.
// Anything it can't match gets an honest "I don't have that" + a follow-up offer,
// so it never invents services, prices, availability or policies.
import { BUSINESS } from "./business.js";

const B = BUSINESS;
const norm = (s) => ` ${String(s).toLowerCase().replace(/[’']/g, "'").replace(/[^a-z0-9' ]+/g, " ").replace(/\s+/g, " ")} `;
const has = (t, words) => words.some((w) => t.includes(` ${w} `));

// Things people ask about that ClearFlow does not list. Answer honestly, never "yes".
const NOT_LISTED = [
  ["hvac", "HVAC"], ["air conditioning", "air conditioning"], ["air conditioner", "air conditioning"], ["ac", "AC repair"], ["furnace", "furnace work"], ["furnaces", "furnace work"],
  ["boiler", "boiler service"], ["boilers", "boiler service"], ["heating", "heating systems"], ["roofs", "roofing"], ["gas line", "gas line work"], ["gas", "gas line work"], ["roof", "roofing"],
  ["electrical", "electrical work"], ["electrician", "electrical work"], ["septic", "septic service"],
  ["sprinkler", "sprinkler systems"], ["irrigation", "irrigation"], ["pool", "pool plumbing"], ["well", "well pumps"],
];

const DEFAULT_SUGGESTIONS = ["Do you handle emergencies?", "What areas do you serve?", "What are your hours?", "Book a plumber"];

const reply = (text, extra = {}) => ({ text, suggestions: extra.suggestions ?? DEFAULT_SUGGESTIONS, action: extra.action ?? null, intent: extra.intent });
const listAreas = () => `${B.areas.slice(0, -1).join(", ")} and ${B.areas.at(-1)}`;
const hoursText = () => B.hours.map((h) => `**${h.days}:** ${h.time}`).join("\n");

function findService(t) {
  for (const s of B.services) if (s.id !== "emergency" && has(t, s.keywords)) return s;
  return null;
}

function findArea(raw) {
  const t = norm(raw);
  const known = B.areas.find((a) => t.includes(` ${a.toLowerCase()} `));
  if (known) return { known };
  // a place name the business doesn't list ("do you serve Boulder?", "in Castle Rock")
  const m = String(raw).match(/\b(?:serve|in|to|near|cover|around)\s+([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)?)/);
  if (m && !/^(The|My|Your|A|An|Our)$/.test(m[1])) return { unknown: m[1] };
  return {};
}

export function demoReply(messages) {
  const last = [...messages].reverse().find((m) => m.role === "user");
  const raw = last ? String(last.content).slice(0, 500) : "";
  const t = norm(raw);

  // booking first: "can you send someone", "book", "schedule"
  if (has(t, ["book", "booking", "schedule", "appointment", "send someone", "send a plumber", "come out", "get someone out", "request service", "set up a visit"])) {
    const urgent = has(t, ["emergency", "burst", "flooding", "flood", "urgent", "leaking", "backup", "no water"]);
    return reply(
      urgent
        ? `If water is coming in right now, call the 24/7 line at **${B.phone}**. It goes straight to the on-call plumber. I can also send your details to dispatch.`
        : "Happy to get that started. I'll take a few details and pass them to the ClearFlow dispatch team.",
      { action: "start_booking", suggestions: [], intent: "booking" }
    );
  }

  if (has(t, ["emergency", "emergencies", "burst", "flooding", "flood", "urgent", "after hours", "24 7", "middle of the night", "backup", "backed up sewer", "no water"])) {
    return reply(
      `Yes. ClearFlow handles emergencies **${B.emergency.available}**: ${B.emergency.covers.join(", ")}.\n\n${B.emergency.howTo.replace(B.phone, `**${B.phone}**`)}`,
      { suggestions: ["Book a plumber", "What areas do you serve?", "What are your hours?"], intent: "emergency" }
    );
  }

  if (has(t, ["price", "prices", "pricing", "cost", "costs", "how much", "rate", "rates", "fee", "fees", "charge", "estimate", "quote", "expensive", "cheap"])) {
    return reply(B.policies.pricing, { suggestions: ["Book a plumber", "What services do you offer?"], intent: "pricing" });
  }

  const area = findArea(raw);
  const asksArea = has(t, ["serve", "service area", "areas", "area", "cover", "come to", "located", "location", "near", "zip", "city", "cities", "travel"]);
  if (area.known) {
    return reply(`Yes, ${area.known} is in ClearFlow's service area. The full list: ${listAreas()}.`, { suggestions: ["Book a plumber", "Do you handle emergencies?"], intent: "areas" });
  }
  if (area.unknown && asksArea) {
    return reply(
      `${area.unknown} isn't on ClearFlow's listed service area (${listAreas()}). I can pass your details to the team so they can tell you whether they can help.`,
      { suggestions: ["Book a plumber", "What areas do you serve?"], intent: "areas" }
    );
  }
  if (asksArea) {
    return reply(`ClearFlow serves the ${B.region}: ${listAreas()}.`, { suggestions: ["Do you serve Lakewood?", "Book a plumber"], intent: "areas" });
  }

  // availability: the assistant can't see the schedule, so it never promises a time
  if (has(t, ["today", "tomorrow", "tonight", "this week", "asap", "soon", "available", "availability", "how fast", "how soon", "when can", "right away", "same day"])) {
    return reply(
      `I can't see ClearFlow's schedule, so I can't promise a time. ${B.policies.followUp}`,
      { suggestions: ["Book a plumber", "Do you handle emergencies?", "What are your hours?"], intent: "availability" }
    );
  }

  if (has(t, ["hours", "open", "close", "closed", "closing", "weekend", "weekends", "saturday", "sunday", "what time", "when are you"])) {
    return reply(`${hoursText()}\n\nEmergency service is available ${B.emergency.available}.`, { suggestions: ["Do you handle emergencies?", "Book a plumber"], intent: "hours" });
  }

  const notListed = NOT_LISTED.find(([w]) => has(t, [w]));
  if (notListed) {
    return reply(
      `${notListed[1][0].toUpperCase() + notListed[1].slice(1)} isn't one of the services ClearFlow lists, so I can't confirm it. I can pass your question to the team, or tell you what they do offer.`,
      { suggestions: ["What services do you offer?", "Book a plumber"], intent: "not_listed" }
    );
  }

  const svc = findService(t);
  if (svc) {
    return reply(`ClearFlow can help with that. It falls under **${svc.name}**: ${svc.blurb[0].toLowerCase() + svc.blurb.slice(1)} Want me to get a plumber booked?`, { suggestions: ["Book a plumber", "Do you serve Lakewood?"], intent: "service" });
  }

  if (has(t, ["services", "service", "what do you do", "offer", "help with", "work on", "specialize"])) {
    return reply(`ClearFlow handles:\n${B.services.map((s) => `• ${s.name}`).join("\n")}`, { suggestions: ["Book a plumber", "Do you handle emergencies?"], intent: "services" });
  }

  if (has(t, ["licensed", "insured", "license", "insurance"])) {
    return reply(`Yes, ClearFlow's team are ${B.licensed.toLowerCase()}.`, { intent: "licensed" });
  }
  if (has(t, ["phone", "call", "number", "email", "contact"])) {
    return reply(`You can call ClearFlow at **${B.phone}** or email ${B.email}. For an emergency, call the 24/7 line at the same number.`, { intent: "contact" });
  }
  if (has(t, ["hi", "hello", "hey", "good morning", "good afternoon"])) {
    return reply("Hi! Ask me about ClearFlow's services, service area, hours or emergency help, or I can get a plumber booked.", { intent: "greeting" });
  }
  if (has(t, ["thanks", "thank you", "thx", "appreciate"])) {
    return reply("You're welcome. Anything else I can help with?", { intent: "thanks" });
  }

  return reply(
    "I don't have that information, and I'd rather not guess. I can pass your question to the ClearFlow team. They'll follow up during business hours.",
    { suggestions: ["Book a plumber", "What services do you offer?"], intent: "unknown" }
  );
}
