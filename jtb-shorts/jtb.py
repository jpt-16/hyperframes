#!/usr/bin/env python3
"""JT Builds Co faceless shorts: spec JSON -> HyperFrames project -> 1080x1920 MP4.

  python3 jtb.py build  videos/redesign-detailing.json     # write out/<slug>/ (html, assets, mastered audio)
  python3 jtb.py check  videos/redesign-detailing.json     # build + hyperframes check (lint, runtime, layout, contrast)
  python3 jtb.py snap   videos/redesign-detailing.json 0.3 4 9   # build + PNG frames at those seconds
  python3 jtb.py render videos/redesign-detailing.json     # build + check + render -> renders/<slug>.mp4
  python3 jtb.py all                                       # render every spec in videos/
  python3 jtb.py fanout videos/mistakes-hvac.json          # the same video for every niche in niches.json
  python3 jtb.py new local-seo dental local-seo-dental-2   # start a new spec from an existing one
  python3 jtb.py lint   videos/*.json                      # copy lint only

Options: --niche <key> and --slug <name> override the spec; --draft renders fast/low quality.
Spec strings may use {business} {short} {label} {city} {query} {category}; they are filled from the niche.
"""
import json, os, re, shutil, subprocess, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
from brand import BASE_CSS
from mocks import MOCK_CSS
from scenes import SCENE_CSS, TYPING_CSS
from templates import TEMPLATES, HOOK, CTA_LEN, BA_CSS
from comp import Comp, plain
from audio import make_bed, STYLES
from mix import mix, master, measure
from copylint import lint

HF = ["npx", "--yes", "hyperframes@0.8.154"]
NICHES = {k: v for k, v in json.load(open(os.path.join(HERE, "niches.json"))).items() if not k.startswith("_")}
FPS = 30

def fill(x, n):
    if isinstance(x, str):
        return re.sub(r"\{(business|short|label|city|query|category)\}", lambda m: n[m.group(1)], x)
    if isinstance(x, list): return [fill(v, n) for v in x]
    if isinstance(x, dict): return {k: fill(v, n) for k, v in x.items()}
    return x

def load(path, niche=None, slug=None):
    s = json.load(open(path))
    if niche: s["niche"] = niche
    if slug: s["slug"] = slug
    s.setdefault("slug", os.path.splitext(os.path.basename(path))[0])
    if s["niche"] not in NICHES: sys.exit(f"unknown niche {s['niche']!r}; have {', '.join(NICHES)}")
    return fill(s, NICHES[s["niche"]]), NICHES[s["niche"]]

def schedule(segments, bpm):
    """Scene starts on the beat grid: hook at 0, then each scene, then the CTA."""
    beat = 60 / bpm
    def snap(t, min_t):
        k = round(t / beat)
        while k * beat < min_t: k += 1
        return round(k * beat, 4)
    T = {}; t = snap(HOOK, HOOK - 0.15)
    for name, d in segments:
        T[name] = t; t = snap(t + d, t + d - 0.2)
    T["cta"] = t
    return T

def build(spec, niche, quiet=False):
    slug = spec["slug"]; out = os.path.join(HERE, "out", slug)
    errors, warnings = lint(spec)
    for w in warnings: print("  copy warning:", w)
    if errors:
        for e in errors: print("  COPY ERROR:", e)
        sys.exit(f"{slug}: copy lint failed. Reword, or list the rule in \"_allow\" if the claim is genuinely true and sourced.")
    segs_fn, build_fn = TEMPLATES[spec["template"]]
    style = spec.get("style", "drive")
    T = schedule(segs_fn(spec), STYLES[style]["bpm"])
    D = round((T["cta"] + CTA_LEN) * FPS) / FPS
    if not 10 <= D <= 20.5: print(f"  note: {slug} runs {D:.1f}s (target 10-20 s)")
    c = Comp(D, FPS)
    build_fn(c, spec, niche, T)

    if os.path.isdir(out): shutil.rmtree(out)
    os.makedirs(os.path.join(out, "assets"))
    shutil.copytree(os.path.join(HERE, "brand", "fonts"), os.path.join(out, "assets", "fonts"))
    shutil.copy(os.path.join(HERE, "brand", "jt-mark.png"), os.path.join(out, "assets", "jt-mark.png"))
    shutil.copy(os.path.join(HERE, "brand", "gsap.min.js"), os.path.join(out, "assets", "gsap.min.js"))
    css = "\n".join([BASE_CSS, MOCK_CSS, SCENE_CSS, BA_CSS, TYPING_CSS])
    open(os.path.join(out, "index.html"), "w").write(c.page(css, f"JT Builds Co · {plain(' '.join(spec['hook']['lines']))}"))
    json.dump({"name": slug, "private": True, "type": "module",
               "scripts": {k: " ".join(HF + [v]) for k, v in dict(dev="preview", check="check", render="render").items()}},
              open(os.path.join(out, "package.json"), "w"), indent=2)
    json.dump({"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json", "paths": {"assets": "assets"}, "media": {"autoProxy": True}},
              open(os.path.join(out, "hyperframes.json"), "w"), indent=2)
    json.dump({"id": slug, "name": slug, "createdAt": "2026-10-17T00:00:00.000Z"}, open(os.path.join(out, "meta.json"), "w"), indent=2)

    tmp = os.path.join(out, ".audio"); os.makedirs(tmp)
    cta_g = make_bed(os.path.join(tmp, "bed.wav"), D, T["cta"], style, spec.get("seed", 7))
    assert abs(cta_g - T["cta"]) < 1e-3, (cta_g, T["cta"])
    aud = mix(os.path.join(tmp, "pre.wav"), D, os.path.join(tmp, "bed.wav"), c.cues, c.keys, os.path.join(HERE, "brand", "sfx"))
    m = master(os.path.join(tmp, "pre.wav"), os.path.join(out, "assets", "mix.wav"))
    shutil.rmtree(tmp)
    quiet_cues = [a for a in aud if a[2] < -8]
    report = dict(slug=slug, template=spec["template"], niche=spec["niche"], style=style, duration=D,
                  times={k: round(v, 3) for k, v in T.items()}, sounds=len(c.cues), key_clicks=len(c.keys), master=m,
                  quiet_cues=quiet_cues)
    json.dump(report, open(os.path.join(out, "build.json"), "w"), indent=2)
    if not quiet:
        print(f"  {slug}: {D:.2f}s, {spec['template']} / {spec['niche']} / {style} {STYLES[style]['bpm']} bpm, "
              f"{len(c.cues)} sounds + {len(c.keys)} key clicks")
        print(f"  scenes: " + ", ".join(f"{k} {v:.2f}" for k, v in T.items()))
        print(f"  master: {m['lufs']} LUFS, true peak {m['true_peak']} dBTP, gain {m['gain_db']:+} dB, "
              f"limiter active {m['limited_pct']}% of the time (max {m['max_reduction_db']} dB)")
        if quiet_cues: print("  quiet sounds (vs music, 1.5-8 kHz):", quiet_cues)
    return out, report

def run(cmd, **kw):
    print("  $", " ".join(cmd)); return subprocess.run(cmd, **kw)

def check(out):
    r = run(HF + ["check", out], capture_output=True, text=True)
    tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-25:])
    print(tail)
    return r.returncode == 0

def render(spec, niche, draft=False):
    out, rep = build(spec, niche)
    if not check(out): sys.exit(f"{spec['slug']}: check failed (see above)")
    os.makedirs(os.path.join(HERE, "renders"), exist_ok=True)
    mp4 = os.path.join(HERE, "renders", spec["slug"] + ".mp4")
    q = ["-q", "draft"] if draft else ["-q", "delivery"]
    r = run(HF + ["render", out, "-o", mp4, "--quiet"] + q)
    if r.returncode: sys.exit(f"{spec['slug']}: render failed")
    I, tp = measure(mp4)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
                               capture_output=True, text=True).stdout)
    size = os.path.getsize(mp4) / 1e6
    print(f"  -> {os.path.relpath(mp4, HERE)}  {dur:.2f}s  {size:.1f} MB  {I} LUFS  {tp} dBTP")
    if abs(I - rep["master"]["lufs"]) > 0.5:
        sys.exit(f"{spec['slug']}: rendered audio is {I} LUFS but the master was {rep['master']['lufs']} (the renderer changed the gain)")
    return mp4

def main(argv):
    if not argv or argv[0] in ("-h", "--help"): print(__doc__); return
    cmd, rest = argv[0], argv[1:]
    opt = {}
    for k in ("--niche", "--slug"):
        if k in rest: i = rest.index(k); opt[k[2:]] = rest[i + 1]; del rest[i:i + 2]
    draft = "--draft" in rest; rest = [a for a in rest if a != "--draft"]
    if cmd == "lint":
        bad = 0
        for p in rest:
            s, _ = load(p); e, w = lint(s); bad += len(e)
            print(f"{p}: {len(e)} errors, {len(w)} warnings"); [print("  ERROR", x) for x in e]; [print("  warn ", x) for x in w]
        sys.exit(1 if bad else 0)
    if cmd == "new":
        tpl, niche, slug = rest[:3]
        src = next((p for p in sorted(glob.glob(os.path.join(HERE, "videos", "*.json"))) if json.load(open(p))["template"] == tpl), None)
        if not src: sys.exit(f"no example spec for template {tpl}")
        s = json.load(open(src)); s["niche"] = niche; s["slug"] = slug
        dst = os.path.join(HERE, "videos", slug + ".json"); json.dump(s, open(dst, "w"), indent=2, ensure_ascii=False)
        print(f"wrote {os.path.relpath(dst, HERE)} (from {os.path.basename(src)}); edit the hook, copy and CTA, then render it")
        return
    if cmd == "all":
        for p in sorted(glob.glob(os.path.join(HERE, "videos", "*.json"))):
            s, n = load(p); print(f"\n== {s['slug']}"); render(s, n, draft)
        return
    if cmd == "fanout":
        for p in rest:
            base, _ = load(p)
            for key in NICHES:
                s, n = load(p, key, f"{base['slug']}--{key}"); print(f"\n== {s['slug']}"); render(s, n, draft)
        return
    if cmd == "snap":
        s, n = load(rest[0], opt.get("niche"), opt.get("slug"))
        out, _ = build(s, n)
        times = rest[1:] or ["0.05", "1.2", "4", "8", "12"]
        snapdir = os.path.join(out, "snaps"); shutil.rmtree(snapdir, ignore_errors=True)
        run(HF + ["snapshot", out, "--at", ",".join(times), "-o", snapdir, "--no-end", "--describe", "false"])
        print("\n".join(sorted(glob.glob(os.path.join(snapdir, "*.png")))))
        return
    for p in rest:
        s, n = load(p, opt.get("niche"), opt.get("slug"))
        if cmd == "build": build(s, n)
        elif cmd == "check":
            out, _ = build(s, n)
            if not check(out): sys.exit(1)
        elif cmd == "render": render(s, n, draft)
        else: sys.exit(f"unknown command {cmd}")

if __name__ == "__main__":
    main(sys.argv[1:])
