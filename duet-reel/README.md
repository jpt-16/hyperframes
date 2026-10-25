# Claude Duet for small business: JT Builds Co reel

A 36 s, 9:16 (1080×1920, 30 fps) faceless Instagram Reel about Anthropic's Claude Duet research preview and what it could mean for small business owners.

- **Voice:** the creator's own voiceover recording. The face is not used.
- **Text:** large key-phrase captions.
- **Sound:** subtle effects and a quiet music bed.

```bash
# put the voiceover at assets/vo/voice.wav (48 kHz mono; not committed), then:
python3 build.py                 # index.html + assets/mix.wav (with voice) + assets/mix-novo.wav (effects + bed only)
npx --yes hyperframes@0.8.154 render . -o renders/claude-duet-reel.mp4 --video-bitrate 16M
python3 tools/finish.py          # renders/claude-duet-reel-ig.mp4 and renders/claude-duet-reel-novo-ig.mp4
```

Everything on screen is defined in `build.py`: the scenes, mock interfaces, captions, timing and sound cues. Edit there and rebuild. The timing table `T` and the caption list `CAPS` sit at the top of the file.

## Accuracy

**Sources:** Anthropic's announcement on X and the "Get started with Claude Duet" help-center article, October 21, 2026.

**What the reel says about Duet:**
- **What it is:** a proactive agent app that brings you what needs your attention, works on tasks you hand it, and checks with you before it acts on your behalf.
- **Status and access:** an early research preview for US Pro and Max plans, by waitlist.
- **Approvals:** it asks before it sends messages, makes payments, signs documents or deletes anything.
- **Limitations:** it can make mistakes, so users should review its work.

**How the reel stays honest:**
- **Illustrative mockups:** no real Duet footage is used. Every interface is a mockup, and the reel labels it on screen: "Illustrative mockup · not real product footage".
- **Fictional details:** the businesses, names and amounts in the mockups are made up.
- **Approval shown on screen:** every mock action ends in an approval step, such as "Needs your OK", "Approve & send", "1 change proposed" or "Waiting on you". The board reads "Nothing goes out until you approve it."
- **Disclaimer:** the end card carries the research-preview, approval and mistakes caveat.
- **Branding:** no Anthropic or Claude logos are reproduced. "Claude Duet" is set in plain type, and the orange is a restrained Claude-inspired accent.

## Timeline (cut to the voiceover)

| Time | Scene | On screen |
|---|---|---|
| 0–3.9 s | Hook: a phone lock screen at 2:14 AM, with work notifications arriving | **AI THAT WORKS WHILE YOU DON'T?** |
| 3.9–7.6 s | Title | Claude *Duet*, a one-line description, and badges: early research preview · US · Pro & Max · waitlist |
| 7.6–11.7 s | Morning brief and Tasks | Things that need your attention; tasks working in the background |
| 11.7–13.9 s | Unpaid invoices | 3 overdue, $4,820 outstanding |
| 13.9–15.6 s | Follow-up draft | The reminder email types in, then "Duet asks before sending · Approve & send" |
| 15.6–17.5 s | Calendar | The conflicting install moves to Friday as a proposal: "Approve" |
| 17.5–18.4 s | Content drafts | Three post drafts for review |
| 18.4–21.4 s | The board | "Waiting on you · 4 approvals"; "Nothing goes out until you approve it." |
| 21.4–26.5 s | The shift | *Asking AI* (question and answer, then you do the rest) → *Delegating to AI* (a task with steps, the last one waiting for approval) |
| 26.5–31.5 s | Statement | **STOP JUST USING AI. START BUILDING SYSTEMS.** |
| 31.5–36 s | End card | JT BUILDS CO lockup, the closing line, the research-preview disclaimer |

**Captions:** key phrases of the voiceover, timed to when they're spoken. They aren't a word-for-word transcript: a local speech recognizer timed them, and a few words in the recording couldn't be transcribed reliably.

## Audio

| File | Contents |
|---|---|
| `assets/mix.wav` | The voice, effects about 6 dB under it and the music bed, mastered to −14 LUFS. |
| `assets/mix-novo.wav` | The same effects and bed at the same gain, with no voice, so a new voiceover dropped on top balances the same way. |
