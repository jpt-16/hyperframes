---
name: baseball-decoded
description: "Build a Baseball Decoded vertical (1080x1920) 3D baseball explainer end to end: intake, brief, a three.js field with the series' geometric players, Kokoro voiceover with word timings, physics, shot list and captions, stills and probes, a parallel render, a phone-sized MP4, and a published artifact with a save button. Use for any Baseball Decoded video, episode, breakdown or series piece, or when asked to make, render or publish one. [baseball, baseball decoded, bat speed, pitching, fielding, shortstop, biomechanics, 3D, vertical, Kokoro, three.js, artifact]"
---

# Baseball Decoded videos

The series is 3D baseball explainers for serious players and fans: a vertical
1080×1920, 30 fps film of 40–55 seconds, one three.js field, the series' geometric
players, a narrated voiceover, word-by-word captions and a logo end card. Every episode is
its own folder at the repo root (`bat-speed/`, `velo/`, `shortstop/`, `hitting-debate/`, …).
The newest episode is the template: start from it, don't rebuild from scratch.
Episodes so far, and what each one adds to `field.js` (reuse these before writing new rigs):
`bat-speed` (hitter swing, lab stage, x-ray, force plates, traces), `velo` (pitcher delivery,
speed gauge, shoulder arcs), `shortstop` (fielders, ground balls, throws, coverage),
`catcher-hardest` (receive, block, steal with a runner and tag, signs, talk with the infield),
`power` (two hitter builds on one rig, left/right split-screen panes, a gym with a back squat,
the ball squashing against the bat, a camera that trails the batted ball).

## 0. Standing choices (keep unless the user changes them)

- **Style:** geometric figures, no faces. The user chose to keep this on `bat-speed`
  and it has stayed for every episode since.
- **Build in one go.** The user asked for no sketch pass ("just do it all at once") and has
  since sent complete scripts with scene direction and no questions. Post the plan as text
  (the scene table), then keep building without waiting for a yes. Offer sketches only if the
  user asks for a storyboard, and only stop to ask when something blocks the work.
- **No paid generators** (no Higgsfield, no AI video). The voice is local Kokoro.
- **Accuracy rules** (from the user, every episode):
  - no invented numbers, percentages, forces or measured claims; label force arrows and
    traces as "illustration, not measured data";
  - never imply energy passes straight from the lower body into the bat or arm, and
    never credit one body part alone;
  - show observed motion and label explanations separately;
  - add an on-screen note that sequence and timing vary between players;
  - cite only sources you have actually checked.
- **Length:** 40–50 s (up to 55 s when the user asks for 45–55). Check the duration after
  the voice is assembled and before building. Target the user's scene timings within about
  a second, and say so when they differ.

## 1. Intake (ask only what's missing)

Ask for, in one message: the script (verbatim), the scene timings, the on-screen text,
the length, and the logo (the series' typographic mark is the default). Don't ask about
style, which is fixed above. Record each answer in the brief.

## 2. Brief and plan

If the script's own timings don't fit a natural read (they usually don't), keep the script
and the length target and say how the scene starts moved. Make the episode folder with `BRIEF.md` (YAML frontmatter: `workflow`, `flow`,
`storyboard`, `message`, `destination`, `aspect`, `resolution`, `length`, `audience`,
`vo_mode`; then Intent, Assets, Customizations, Notes) and `STORYBOARD.md` (the
scene-by-scene table: time, beat, on screen, why). Post the plan as text, then build (see §0).

## 3. Scaffold from the newest episode

```bash
NEW=<new-folder>; SRC=power   # the newest episode
mkdir -p $NEW/assets/vo $NEW/tools
cp -r $SRC/assets/fonts $SRC/assets/sfx $SRC/assets/vendor $NEW/assets/
cp $SRC/assets/field.js $NEW/assets/
cp $SRC/tools/*.py $SRC/tools/render_chunks.js $NEW/tools/
cp $SRC/build.py $SRC/hyperframes.json $SRC/package.json $SRC/.gitignore $NEW/
sed -i "s/$SRC/$NEW/" $NEW/package.json
echo "{ \"id\": \"$NEW\", \"name\": \"$NEW\", \"createdAt\": \"$(date -u +%FT%TZ)\" }" > $NEW/meta.json
```

Don't copy the old `vo/`, `play.json`, `release.json` or `renders/`. The `sfx/` folder is
about 12 MB, so it's copied from the template and not recreated.

## 4. Voiceover (Kokoro, local)

- **Script:** `tools/vo.py`, the `LINES` list, one `(id, caption, spoken)` per sentence.
  The caption is the script exactly as written. Use `spoken` only to fix pronunciation,
  for example `"100"` → `"one hundred"`.
- **Voice:** `am_michael`. Speed 1.15–1.5 (the older episodes ran 1.2–1.5). Pick the speed
  so the full script lands at the target length, and never speed past 1.5, because the
  voice gets rushed.
- **Setup once:** `pip install kokoro-onnx soundfile onnx numpy` into a venv, then run
  `npx --yes hyperframes@0.8.154 tts "x" -v am_michael -o /tmp/x.wav` once so the model
  downloads to `~/.cache/hyperframes/tts`. Then set `HYPERFRAMES_PYTHON=<venv python>`.
- **Run:** `$HYPERFRAMES_PYTHON tools/vo.py`, then `python3 tools/assemble.py`. The latter
  writes `assets/vo/vo.wav`, `timing.json` (line and word times) and prints the duration.
- **Timing controls, in `tools/assemble.py`:**
  - `GAP_AFTER`: the pause after each line, which is the "pauses after important statements"
    the user asks for;
  - `AT`: forced scene starts, for example `{"d1": 6.0, "r1": 15.0}`. Each scene's first
    line starts no earlier than its anchor. Use `AT` to match the user's scene timings.
- Re-run `assemble.py` after any change to the gaps and recheck the duration.

## 5. Physics (`tools/physics.py`)

- **Field frame:** home plate's back point at the origin, +x toward first base, −z toward
  center field, y up, feet and seconds.
- **Pitches:** `PITCHES` has mph, rpm, spin efficiency, lift direction and target. The
  release point is `RELEASE`, overridden by `tools/release.json` when a pitcher rig exists.
  Write the release point you measured from the rig, not a guessed one.
- **Batted balls:** `HITS` (line drives, with exit speed, launch angle and spray).
  `GROUNDERS` (ground balls) use a bounce model: 52% vertical and 88% horizontal kept per
  bounce, rolls after low skips, and an optional bad hop.
- **Output:** `assets/play.json`, which `field.js` reads as `PLAY`.

## 6. The 3D field (`assets/field.js`)

Its sections, top to bottom: field geometry, lights, `makePlayer` (articulated figures),
`applyPose` and the pose tables, the cast, the pitches, close-up kit, hands and bat, the
ballpark, the poses for each episode (look for the `// ====` banners), then
`renderAt`/`seek`.

- **New sections** go before the `// ---- DOM overlays` banner, then hook them into
  `renderAt` (the `setSceneX(th, sh, v)` call) and add the debug handles to
  `window.__dbg` so the probes can read them.
- **Pose rules that matter:**
  - a `legIK` foot keeps the foot planted; a `armIK` hand holds its target;
  - key the throwing arm as **upper-arm and forearm directions in the trunk frame**, so
    external rotation, internal rotation and elbow extension are separate, visible motions;
  - key the body on smooth curves (`herm` through timed keys), so there's no stop at each key.
- **X-ray and force visuals:** `setXray` (uniform fade plus coloured segments), `setGRF`
  or `grfP` (ground-force arrows at the feet, labelled as illustrations), `drawTrace`
  (turning-speed traces from the same keyed body).

**Segment colours (keep):** legs/ground amber `#FFB547`, pelvis orange `#FF6A3D`, torso
cyan `#56D1FF`, arms and hands green `#3DD68C`, bat gold `#FFD84D`.

## 7. Shots, captions, sound (`build.py`)

- **Shot list:** `shot(a, b, cam, vs, ts, **opts)` on play times `a`–`b`. `vs` is the video
  time and `ts` the play time, interpolated between keys. Use `W(line, word)` and
  `S[line]` to key shots to the voiceover's words. Shot boundaries must chain:
  `shots[i].b == shots[i+1].a` (the build asserts this).
- **Cameras** are dicts: `c0`, `c1`, `l`, `l1`, `f0`, `f1`, `close`, `bokeh`, `up`, `o`,
  `lo`, plus `cam` kinds `world`, `obj`, `orbit`, `follow2`, `chase`, `ride`, `hfollow`.
  **Never name a shot option `up`, `rise`… or any key the camera code already reads**;
  `up` collided with `cam.up` and produced "Spread syntax requires iterable", which is
  why `chase` uses `rise`.
- **Captions:** `KEY` lists the words to highlight in yellow. Captions are chunked by
  punctuation or four words, and each chunk is timed to its first word.
- **Overlays:** `title` (the band or big title), `pinl` (a label pinned to a moving point,
  using `PINH`/`PINT` keys), `chip`, `note` (the illustration/variation notes), `legend`,
  `gauge`. Keep on-screen text minimal: a title per scene plus a few short labels.
- **Sound:** `cue(name, time, dB)` from `assets/sfx/`. Use whooshes on cuts, a crack on
  contact, glove pops, ticks on labels, an impact on titles, and the riser into the
  end card. `mixdown()` ducks the bed under the voice and masters to about −14 LUFS.
- **The scene table:** `SCENES` (start, end, name, description, title). `build.py` writes
  `CUES.md` from it, so the user can record over `assets/mix-novo.wav`.

Build in two steps: `python3 build.py --nomix` checks that the shots chain and
`index.html` is written. Then `python3 build.py` mixes the audio too. Mixing needs `scipy`.

## 8. Check before the long render

The render takes about 10 seconds per frame in software WebGL, so a full run is 30–60
minutes. Check first:

- **Stills at key times:** `node scripts/stills.js <episode dir> <out dir> <port> t1 t2 …`
  writes `s_<t>.png`. Tile them into a contact sheet with ffmpeg `hstack` and look at every
  shot. Check labels, camera framing, the freeze and the end card.
- **Poses:** `node scripts/poses.js <dir> <port> <out.png> k1 k2 …` renders a figure from
  the side and from home. Use it to tune a pose before blaming the timing.
- **Numbers:** `node scripts/probe.js <dir> <port> '<js expr>'` runs an expression in the
  page and returns JSON. Use it for world positions (the hand at release, the feet on the
  plates, the ball's hop height) and for the hand speed through a key.
- **Cameras:** `node scripts/camtest.js <dir> <port> <out dir> '{"t":..,"s":{"c":{...}}}' '[[[cx,cy,cz],[lx,ly,lz],fov,close],...]'`
  renders one scene from several candidate cameras at once. Use it to choose each camera
  before it goes into `build.py`. It also prints the catcher's hand and pelvis positions.
- **Check every camera for things in the way.** The batter (at x ≈ −3.2), the umpire (z ≈ 6) and
  the catcher's own back block most cameras behind and beside the plate. Hide the umpire with the
  shot option `noump=1`, aim from the front or from above, and compare a few angles with `camtest`.
- **Fix, then re-check** the frames that changed. Don't render until the stills pass.

## 9. Render (4 workers, resumable)

```bash
cd <scratch>; for r in 0 1 2 3; do NW=4 RW=$r nohup node render_par.js <episode dir> <chunks dir> 30 <duration> 90 $((8900+r)) > rr$r.log 2>&1 & done
```

- `render_par.js` takes chunks of 90 frames, round-robin across workers. It skips finished
  chunks, so a crash only costs the chunk in progress. Restart a dead worker with the same
  `RW`.
- Monitor with `Monitor` on `tail -F rr*.log` and filter for `chunk|ALL DONE|pageerror|TimeoutError`.
  Don't `sleep` to wait. Launch a `Monitor` and end the turn.
- A `pageerror` stops that chunk. Read the stack from a probe (`window.__fieldRender(t)`
  inside `try/catch`) and fix it before restarting the worker.

## 10. Join, mux, compress

```bash
ls <chunks>/c*.mp4 | grep -v part | sort | sed "s|^|file '$PWD/|; s|$|'|" > list.txt
ffmpeg -y -f concat -safe 0 -i list.txt -i assets/mix.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -c:a aac -b:a 256k -movflags +faststart -shortest renders/master.mp4
ffmpeg -y -i renders/master.mp4 -c:v libx264 -preset slow -crf 26 -maxrate 1700k -bufsize 3400k -pix_fmt yuv420p -profile:v high -level 4.1 -c:a aac -b:a 128k -movflags +faststart renders/<episode>.mp4
```

The phone copy should be about 10–12 MB at 1080×1920. Check the frames from the phone copy.

## 11. Publish

- **Page:** a single HTML file with the video player and a **Save video to phone** button.
  The button uses the `downloads` capability, and the video is an uploaded asset.
  Copy `catcher-hardest/artifact.html` and change the title, heading, file name, duration, size and
  scene list. Its video `src` is a placeholder (`__VIDEO_URL__`) until the asset is uploaded; the
  committed copy keeps the last published `/_blob/<id>` URL, so replace that with the new one.
  Commit the page into the episode folder when the episode is final.
- **Publish:** `Artifact` with `capabilities: {"assets": {}, "downloads": true}`, an icon
  and a one-sentence description. Upload the MP4 with `Artifact` `asset: true`, then
  replace the `src` placeholder with the returned `/_blob/<id>` URL using an `edits`
  publish of the same file.
- **Tell the user:** the link is private to them by default. Anyone else needs it shared
  from the Share menu. The save prompt only works in a viewer, so say the button should be
  tested on the phone.

## 12. Commit and push

- **Branch:** the working branch from the session instructions (`claude/determined-hawking-9l0mif`).
  Don't open a PR unless the user asks.
- **Commit:** the episode folder only, excluding `renders/`, `index.html`, `assets/vo/*.wav`,
  `assets/mix*.wav` and `assets/bed.wav` (the `.gitignore` covers these).
- **Attribution:** use the Co-Authored-By and Claude-Session lines from the attribution
  reminder in the current session.
- **Files to write:** `README.md` (the shot table, timings, what's labelled as an
  illustration, the build commands), `transcript.txt` (from `timing.json`), `CUES.md`
  (generated by `build.py`), `BRIEF.md`.

## Gotchas (learned the hard way)

- **Shot boundaries:** every shot must end exactly where the next begins. Ending one shot at
  `V3 - 0.02` and starting the next at `V3` trips the build's assertion. Use the same value for both.
- **Values read back from a rig** (a throw's release point, the steal's timing, where a block
  makes contact): measure them with `probe.js` and store them in `tools/*.json`
  (`release.json`, `plan.json`) for the physics and `build.py` to read. Don't guess them.
- **Don't pipe `physics.py` into `head`.** It stops the script before `play.json` is written.
- **Camera presets:** a preset used with `"world"` needs `c0`/`c1`/`l`; one used with `"track"`
  needs `look`. Don't reuse a preset across both kinds.
- **A plan that waits for approval** isn't wanted here; see §0.
- **Split-screen layouts:** half-width panes (540×1920) make each figure about a quarter of the
  frame height, so use them for comparisons and fill the dark space above with the title. Use
  `camtest` with a pane width as the fifth camera value to frame them. Top/bottom halves
  (1080×960) give much larger figures if left/right isn't required.
- **Rig scale:** a hitter scaled with `BUILD` needs `SCB` (the IK works in the rig's own units).
  Anything that poses the batter with its own IK must reset `SCB = 1` afterwards.
- **A ball that is a tiny dot** (batted-ball chase shots): raise the glow with the shot option
  `bgs`, and aim the camera at the ball with `lift`, so it isn't hidden under the caption band.
- **Duplicate top-level names in `field.js`.** `FORE`, `BACK` and `CHARGE` collided with
  series constants and broke every render. Rename new constants with a prefix, and check
  for duplicates before building:
  `grep -oE '^(const|let|function) [A-Za-z_$][A-Za-z0-9_$]*' assets/field.js | sort | uniq -d`
  should print nothing.
- **Shot option names** must not collide with camera keys (see §7).
- **`page.screenshot` times out** under software GL. Pass `timeout: 300000`, which
  `render_par.js` already does.
- **Browser flags:** `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`.
  The scripts already pass them.
- **Multiple gauges or labels:** target them by class, not id. Duplicate ids meant only one
  gauge updated.
- **The lab stage** hides the ballpark with `setLab(true)`. Restore it with `setLab(false)`
  in every scene, or the ballpark stays hidden.
- **Scene timing:** the video's scene starts follow the voiceover (`AT` anchors), not the
  brief. Say so when they differ.
- **Kokoro needs** the model downloaded once through the CLI, and `scipy` for the mix.
- **Long waits:** don't `sleep` in a shell (the harness blocks it). Use `Monitor` or a
  background command.
- **Container restarts** wipe `/tmp` and the scratch folder. Keep renders and the working
  copies inside the repo, and commit the source before a long render.
