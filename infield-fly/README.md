# "The infield fly rule"

A 29.4 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded: why an infielder can't drop an easy pop-up to turn a cheap double play.

- **Framework:** the same three.js field, players, dugouts, seats and HyperFrames workflow as `intentional-walk` and `first-pitch`.
- **New 3D pieces:**
  - a physics pop-up with a short hop
  - the shortstop's decoy (calls for it, pulls the glove away, lets it drop)
  - the plate umpire's infield-fly signal
  - the 6-4-3 relay
  - a top/bottom split screen of the same play without and with the rule
  - rings marking the batter and runners
- **Audio:** no narration, since the brief gave no script; the text carries it. A `make_bed` music bed (style "drive") lands its chord on the closing question. Effects:
  - the pop-up's bat sound
  - a riser and hit into the freeze
  - a hard hit on the umpire's signal
  - ball-on-dirt thuds (one at half speed), glove pops on the double play
  - whooshes on the cuts and ticks on the conditions
- **Mix:** mastered to about −14 LUFS.

```bash
python3 tools/physics.py        # the pitch and the pop-up -> assets/play.json
python3 build.py                # index.html + assets/mix.wav
npx --yes hyperframes@0.8.154 render . -o renders/infield-fly.mp4 --video-bitrate 16M
```

## The rule as shown

From MLB's Official Baseball Rules (the definition of an infield fly, and 5.09(a)(12)):
- **What it covers:** a fair fly ball, not a line drive or a bunt, that an infielder can catch with ordinary effort. It applies with runners on 1st and 2nd, or the bases loaded, with fewer than two out.
- **The call:** the umpire declares it while the ball is in the air, as soon as it's apparent. The signal is the right arm straight up.
- **The batter** is out whether or not the ball is caught.
- **The runners:**
  - The ball stays live, and runners may advance at their own risk.
  - The batter is already out, so there is no force: a runner off his base has to be tagged.
  - If the ball is caught, runners must retouch, as on any fly ball.
- **Line drives and bunts** are excluded, and the call is the umpire's judgment. The conditions card says so, so the video doesn't imply every pop-up qualifies.

**The split screen:**
- **Top, "without the rule":** a hypothetical. The shortstop lets it drop. The batter, who was jogging, and both runners are forced, so a throw to second and a relay to first make a double play.
- **Bottom, with the rule:** the batter is already out. The runner from second tries for third at his own risk, and the shortstop looks him back. No force, no double play.

**The pop-up physics** (gravity, drag, backspin): 54 mph off the bat at 65°.
- It peaks at 79 ft and comes down on the dirt in front of the shortstop, 104 ft out, after a 4.6 s hang time.
- It takes a short hop that keeps 35% of its vertical speed.
- The pitch is a 93 mph fastball in on a right-handed hitter's hands.

## Shots

| Time | Scene | Shot | On screen |
|---|---|---|---|
| 0–3.9 s | The trap | The swing. The ball climbing over the infield. The shortstop under it, calling for it. He pulls the glove away, and the runner scrambles back to second. Freeze with the ball just above the dirt, plus a fast zoom | "1 out · runners on 1st & 2nd"; **WAIT… HE DID THAT ON PURPOSE?** |
| 3.9–9.4 s | The rule | A ½-speed replay from low in front of the mound. The umpire's arm goes straight up while it's still climbing. Wide, as it drops uncaught and the batter runs | **"INFIELD FLY!"**; **BATTER: AUTOMATICALLY OUT** with an OUT pin; "…even though nobody caught it" |
| 9.4–16.6 s | Why it exists | Split screen, the same pop-up. Top: dropped on purpose, force at 2nd, relay to 1st, double play. Bottom: batter already out, no force | **NO CHEAP DOUBLE PLAY.** |
| 16.6–23.4 s | The conditions | A diamond with runners on 1st and 2nd. The four conditions tick in one at a time, then a runner appears on 3rd | **BASES LOADED ALSO QUALIFIES**; "Not on a line drive or a bunt · the umpire's judgment" |
| 23.4–29.4 s | The twist | ½ speed on the dirt: it falls in. The runner tries for 3rd and is looked back. Wide, with the batter walking off; freeze | **THE CATCH DOESN'T MATTER.** then **DID YOU KNOW THIS RULE?** |
