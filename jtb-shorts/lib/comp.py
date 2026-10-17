"""Composition builder: collects clips, CSS, GSAP lines and sound cues, then writes
a HyperFrames index.html. Scene code talks to it through a handful of verbs:

    c.clip(id, t0, t1, html)          a timed layer (class "scene clip", opacity 0 until tweened)
    c.ft(sel, frm, to, t)             tl.fromTo(...)      c.to / c.set likewise
    c.cue(name, t, db)                a sound at t (risers end on t, whooshes peak on t)
    o(opacity=0, y=40, ease="...")    a JS object literal; wrap raw JS in R("...")
"""
import json, html, re

r = lambda x: round(float(x), 3)
esc = html.escape

class R(str):
    """Raw JavaScript inside o(...)."""

def o(**kw):
    out = []
    for k, v in kw.items():
        if isinstance(v, R): out.append(f"{k}:{v}")
        elif isinstance(v, bool): out.append(f"{k}:{'true' if v else 'false'}")
        elif isinstance(v, (int, float)): out.append(f"{k}:{round(v, 4)}")
        else: out.append(f"{k}:{json.dumps(v)}")
    return "{ " + ", ".join(out) + " }"

def rich(s):
    """Spec text -> HTML: *word* becomes the accent colour, a newline becomes a line break."""
    s = esc(s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    return s.replace("\n", "<br>")

def plain(s): return re.sub(r"\*", "", s).replace("\n", " ")

class Comp:
    def __init__(self, duration, fps=30):
        self.D = duration; self.fps = fps
        self.html, self.css, self.js, self.cues, self.keys = [], [], [], [], []
        self.track = 0

    def clip(self, cid, t0, t1, inner, cls="scene", style=""):
        t0 = max(0.0, t0); t1 = min(self.D, t1); self.track += 1
        st = f' style="{style}"' if style else ""
        self.html.append(f'<div id="{cid}" class="{cls} clip" data-start="{r(t0)}" data-duration="{r(t1 - t0)}" '
                         f'data-track-index="{self.track}"{st}>{inner}</div>')

    def raw(self, h): self.html.append(h)
    def ft(self, sel, a, b, t): self.js.append(f"tl.fromTo({json.dumps(sel)}, {a}, {b}, {r(t)});")
    def to(self, sel, b, t): self.js.append(f"tl.to({json.dumps(sel)}, {b}, {r(t)});")
    def set(self, sel, b, t): self.js.append(f"tl.set({json.dumps(sel)}, {b}, {r(t)});")
    def line(self, js): self.js.append(js)

    def cue(self, name, t, db=0.0):
        if 0 <= t < self.D + 0.01: self.cues.append((name, r(t), db))

    def key(self, t, db=0.0):
        """One synthesised key click (typing)."""
        if 0 <= t < self.D: self.keys.append((r(t), db))

    def page(self, css, title):
        D = r(self.D)
        js = "\n".join("      " + l for l in self.js)
        body = "\n".join("      " + h for h in self.html)
        return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=1080, height=1920">
    <title>{esc(title)}</title>
    <script src="assets/gsap.min.js"></script>
    <style>{css}</style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{D}" data-width="1080" data-height="1920" data-fps="{self.fps}">
      <div id="grid"></div><div id="glow"></div>
{body}
      <div id="vignette"></div>
      <audio id="mix" src="assets/mix.wav" data-start="0" data-duration="{D}" data-track-index="0" data-volume="1"></audio>
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
{js}
      tl.set({{}}, {{}}, {D});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
