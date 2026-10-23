// LIVE MODE ONLY. Runs on the server when ANTHROPIC_API_KEY (or another credential
// the Anthropic SDK can resolve) is configured. The key never reaches the browser.
// The model only sees ClearFlow's facts from business.js and is told to answer from
// them alone. Booking is not done by the model: it signals intent and the chat
// widget runs the same deterministic lead form as demo mode.
import { BUSINESS } from "./business.js";

const MODEL = "claude-opus-5-5";
let client = null;

export async function liveAvailable() {
  if (!process.env.ANTHROPIC_API_KEY && !process.env.ANTHROPIC_AUTH_TOKEN) return false;
  try {
    const { default: Anthropic } = await import("@anthropic-ai/sdk");
    client = new Anthropic();
    return true;
  } catch {
    console.warn("ANTHROPIC_API_KEY is set but @anthropic-ai/sdk is not installed (npm install). Staying in demo mode.");
    return false;
  }
}

const SYSTEM = `You are the website chat assistant for ${BUSINESS.name}, a plumbing company.
Answer customer questions using ONLY the business facts below. Rules:
- If the facts don't answer the question, say you don't have that information and offer to pass the question to the team. Never guess.
- Never state or estimate prices, discounts, arrival times, availability slots, warranties or any policy that isn't in the facts.
- Never offer a service or area that isn't listed. If asked about one, say it isn't listed.
- Keep replies short and friendly: 1-3 sentences, plain text. You may use **bold** for one key detail.
- If the customer wants to book, schedule, get a quote, or have someone come out, reply with one short sentence and end your reply with the exact token [[BOOK]]. The website then collects their details.
- For anything urgent (burst pipe, flooding, sewer backup), give the 24/7 emergency line.

Business facts (JSON):
${JSON.stringify({ ...BUSINESS, services: BUSINESS.services.map(({ name, blurb }) => ({ name, blurb })) }, null, 1)}`;

export async function liveReply(messages) {
  const history = messages
    .filter((m) => (m.role === "user" || m.role === "assistant") && typeof m.content === "string" && m.content.trim())
    .slice(-12)
    .map((m) => ({ role: m.role, content: m.content.slice(0, 1000) }));
  while (history.length && history[0].role !== "user") history.shift();

  const response = await client.beta.messages.create({
    model: MODEL,
    max_tokens: 2000,
    system: SYSTEM,
    output_config: { effort: "low" },
    betas: ["server-side-fallback-2026-07-01"],
    fallbacks: "default",
    messages: history,
  });

  if (response.stop_reason === "refusal") {
    return { text: `I can't help with that here. For anything about your plumbing, call ${BUSINESS.phone}.`, action: null };
  }
  let text = response.content.filter((b) => b.type === "text").map((b) => b.text).join("").trim();
  const book = text.includes("[[BOOK]]");
  text = text.replace("[[BOOK]]", "").trim();
  return { text, action: book ? "start_booking" : null };
}
