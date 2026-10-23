# ClearFlow Plumbing: AI website assistant demo (JT Builds Co)

A working local demo for a faceless Reel. It has three parts:

- a plumbing company website, ClearFlow Plumbing (fictional);
- a chat assistant that answers questions and captures leads;
- a lead dashboard where submitted requests appear live.

```bash
cd clearflow-demo
npm start               # http://127.0.0.1:4310  (Node 20+, no install needed for demo mode)
```

| Page | What it is |
|---|---|
| `/` | The website, with the chat widget (bottom right, or full screen on mobile). |
| `/dashboard` | The lead inbox. New chat leads appear without a refresh. |
| `/stage` | A 9:16 recording stage for screen recording (see below). |

## Demo mode vs live AI

| | Demo mode (default) | Live AI |
|---|---|---|
| **When** | No API key set | `ANTHROPIC_API_KEY=… npm install && npm start` |
| **Answers** | `server/demo-engine.js`: scripted, rule-based matching. It is not AI. | `server/live-ai.js`: Claude, called from the server only. |
| **Label in the chat** | "Demo mode · scripted from ClearFlow's info" | "Online · answers from ClearFlow's info" |
| **Booking form** | The same deterministic, validated form in both modes. | (same) |

- **One source of facts.** Services, service area, hours, the emergency line and the two policies (no prices over chat; how follow-up works) live only in `server/business.js`.
  - The website renders from that file.
  - The demo engine answers from it.
  - The live prompt is built from it.
- **No made-up answers.** For anything not in that file (prices, availability, warranties, unlisted services or towns), the assistant says it doesn't have that information and offers a follow-up.
- **No secrets in the browser.** The API key is only read by the server and never reaches the browser.
- **Live mode settings.** Live mode uses `claude-opus-5-5` at low effort, with the server-side refusal fallback (`fallbacks: "default"`) turned on.
  - The live path isn't tested here, because no API key was available.

## Recording it yourself (9:16)

1. Open `http://127.0.0.1:4310/stage` and make the window tall. The phone-shaped frame is exactly 9:16.
2. Start your screen recorder on that frame, then press **Space** (or click **Play demo**).
   - The autopilot runs the conversation through the real UI: real clicks, real typing and real API calls.
   - It then switches to the dashboard and shows the new lead arriving.
3. **H** hides the control panel. **Reset leads** puts the inbox back to its 4 sample leads.

You can also drive the site by hand.

- **Suggested prompt chips:** these sit under every answer.
- **Start triggers:** `/?autopilot=1` or **Shift+D** on the site starts the same autopilot.

## The reel

`reel/` is the finished 9:16 reel (HyperFrames). It has motion graphics and sound effects (risers, impacts, whooshes, taps, typing clicks), and no music or voiceover.

```bash
npm start &                                   # the app must be running
node reel/tools/capture.mjs                   # frame-exact 30 fps capture of the real app (Playwright)
python3 reel/tools/prep.py                    # re-time the capture, map every tap/reply to the reel clock
cd reel && python3 build.py && npx --yes hyperframes@0.8.154 render . -o renders/clearflow-ai-assistant-reel.mp4 --video-bitrate 16M
```

The capture runs the page on a virtual clock and pins every CSS animation to it, so each frame is exact. Answers play at real speed. Pauses and typing are sped up by dropping frames; nothing in the app is redrawn.

| Time | Section |
|---|---|
| 0–2.9 s | Hook: 9:47 PM. / Pipe just burst. / Office is closed. / Website isn't. |
| 2.9–24.2 s | The demo on a phone: emergency question, service-area check, booking (name → phone → service → details), "Request sent" with a push-in. |
| 24.2–28.4 s | The lead arriving in the dashboard, with a push-in. |
| 28.4–31.6 s | End card: "Never miss the 9:47 PM call." JT Builds Co \| DM ‘AI’. |

Sound effects sit at about −24 LUFS, so a voiceover can go on top. Every on-screen tap and reply has its own sound on the exact frame.

## Checks

```bash
npm test                                      # API smoke test (engine answers, lead validation)
node tools/verify.mjs [outDir]                # browser test: full flow on desktop + mobile, live dashboard,
                                              # validation, no console errors (needs Playwright)
```

## Files

- `server/`
  - `index.js`: HTTP server and API.
  - `business.js`: the facts.
  - `demo-engine.js`: demo-mode answers.
  - `live-ai.js`: live-mode answers.
  - `leads.js`: lead storage (`data/leads.json`) and live push to the dashboard.
- `public/`
  - `index.html`, `css/site.css`, `js/site.js`: the website.
  - `js/chat.js`, `css/chat.css`: the chat widget.
  - `dashboard.html`, `js/dashboard.js`, `css/dashboard.css`: the lead inbox.
  - `stage.html`: the recording stage.
  - `js/autopilot.js`: the scripted demo run.
- `reel/`: the reel project.

The capture, renders and lead data are git-ignored.

ClearFlow Plumbing, its phone number (555 range) and the `.example` email are fictional. Sample leads are labelled "Sample" in the dashboard.
