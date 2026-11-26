"""Generate index.html: the "Is Parke a scam?" edit, motion-graphics version.

    python3 build.py && npx hyperframes check

base.mp4 (his talking head, 1080x1920) is the spine and the voice. Scenes are full-frame
flat-colour graphic cutaways that wipe up over him and wipe away again; he is on screen
roughly a third of the time. Every beat is pinned to a spoken word via PH("phrase").
Typefaces: Archivo (variable, grotesk), Instrument Serif Italic (emphasis), Graduate (the
collegiate block lettering Parke itself uses). Colours are sampled from the product photos.
"""
import json, re, html

WORDS = json.load(open("tools/words.json"))
END = 91.87

def norm(s): return re.sub(r"[^a-z0-9'$]", "", s.lower())
def PH(phrase, n=1):
    seq = [norm(x) for x in phrase.split()]
    toks = [norm(w["w"]) for w in WORDS]
    hits = [i for i in range(len(toks) - len(seq) + 1) if toks[i:i + len(seq)] == seq]
    if len(hits) < n: raise SystemExit(f"phrase not found: {phrase!r} #{n}")
    return WORDS[hits[n - 1]]["s"]
r = lambda x: round(x, 3)

# ------------------------------------------------------------------ beats
T = dict(
    g1_out=PH("park might") - 0.04,
    g2_in=PH("because when") - 0.10, selling=PH("selling"), controv=PH("controversy surrounding"), products=PH("products come"),
    g2_out=PH("it reads") - 0.10,
    g3_in=PH("why can't") - 0.12, someone=PH("someone else"), comparable=PH("comparable product"), ownbrand=PH("their own brand"),
    less=PH("significantly less"), g3_out=PH("let me explain") - 0.10,
    g4a_in=PH("founded by") - 0.10, chelsea=PH("chelsea kramer"), g4b_in=PH("it became") - 0.12, overs=PH("oversized sweatshirts"),
    name=PH("part name"), g4_out=PH("and here's") - 0.10,
    g5_in=PH("park is actually") - 0.12, middle=PH("middle name"), g6_in=PH("it started as") - 0.14,
    vintage=PH("vintage clothing"), brand=PH("turned into"), whopping=PH("whopping"), m16=PH("sixteen million"),
    y2024=PH("twenty twenty four"), g6_out=PH("but the controversy") - 0.10,
    g7_in=PH("clothing was actually") - 0.14, manuf=PH("manufactured"), wholesale=PH("wholesale manufacturers"),
    g7_out=PH("she's denied") - 0.08,
    denied=PH("denied white"), custom=PH("custom design"), revis=PH("multiple revisions"),
    g8_in=PH("but regardless") - 0.12, right=PH("who's right"), opp=PH("business opportunity"), anyone=PH("for anyone"),
    g9_in=PH("imagine someone") - 0.12, p125=PH("one hundred"), compq=PH("comparable quality"), p50=PH("fifty bucks"),
    g10_in=PH("entering a market") - 0.12, demand=PH("demand already"), convince=PH("convince people"), sweat=PH("need a sweatshirt") + 0.35,
    g10_out=PH("you just need") - 0.08,
    g11_in=PH("this applies") - 0.12, notjust=PH("just clothing"), g11_out=PH("sometimes the biggest") - 0.08,
    invent=PH("inventing something new"),
    g12_in=PH("it's finding") - 0.12, better=PH("figuring out"), build=PH("building a business"), g12_out=PH("because you're not") - 0.08,
)
print({k: r(v) for k, v in T.items()})

# scenes: id, in, out, exits-to-video?, bg, caption-mode
SC = [
    ("g1", 0.0, T["g1_out"], True),
    ("g2", T["g2_in"], T["g2_out"], True),
    ("g3", T["g3_in"], T["g3_out"], True),
    ("g4a", T["g4a_in"], T["g4b_in"], False),
    ("g4b", T["g4b_in"], T["g4_out"], True),
    ("g5", T["g5_in"], T["g6_in"], False),
    ("g6", T["g6_in"], T["g6_out"], True),
    ("g7", T["g7_in"], T["g7_out"], True),
    ("g8", T["g8_in"], T["g9_in"], False),
    ("g9", T["g9_in"], T["g10_in"], False),
    ("g10", T["g10_in"], T["g10_out"], True),
    ("g11", T["g11_in"], T["g11_out"], True),
    ("g12", T["g12_in"], T["g12_out"], True),
]
NAVY_SCENES = {"g5", "g8", "g12"}
WIN = {}
for i, (sid, a, b, ex) in enumerate(SC):
    start = max(0.0, a - 0.45)
    end = b + (0.60 if ex else 0.80)
    WIN[sid] = (r(start), r(end - start))

# talking-head slow pushes (scale a -> b), only visible on the face segments
VZ = [(0, 2.0, 1.00, 1.05), (T["g1_out"], T["g2_in"], 1.03, 1.08), (T["g2_out"], T["g3_in"], 1.10, 1.03),
      (T["g3_out"], T["g4a_in"], 1.02, 1.07), (T["g4_out"], T["g5_in"], 1.08, 1.03),
      (T["g6_out"], T["g7_in"], 1.03, 1.08), (T["g7_out"], T["g8_in"], 1.10, 1.02),
      (T["g10_out"], T["g11_in"], 1.02, 1.09), (T["g11_out"], T["g12_in"], 1.08, 1.02),
      (T["g12_out"], END, 1.03, 1.07)]

# ------------------------------------------------------------------ captions
def fix(words):
    """Spoken-word transcript -> what he actually means (Parke, numbers, a few mis-hearings)."""
    ws = [dict(w) for w in words]
    out, i = [], 0
    n = lambda k: norm(ws[k]["w"]) if k < len(ws) else ""
    def span(k, j, texts):
        a, b = ws[k]["s"], ws[j]["e"]
        step = (b - a) / len(texts)
        for q, t in enumerate(texts):
            out.append({"w": t, "s": r(a + step * q), "e": r(a + step * (q + 1))})
    while i < len(ws):
        w = n(i); pun = re.search(r"[.,?!]+$", ws[i]["w"]); pun = pun.group(0) if pun else ""
        if i == 0 and w == "the" and n(1) == "park": span(0, 1, ["Is", "Parke"]); i += 2; continue
        if w == "a" and n(i + 1) == "part" and n(i + 2) == "name": span(i, i + 2, ["the", "Parke", "name" + re.sub(r".*?([.,?!]*)$", r"\1", ws[i + 2]["w"])]); i += 3; continue
        if w == "there" and n(i + 1) == "s": span(i, i + 1, ["there's"]); i += 2; continue
        if w == "park": span(i, i, ["Parke" + pun]); i += 1; continue
        if w == "featured": span(i, i, ["feature"]); i += 1; continue
        if w == "reads": span(i, i, ["raises"]); i += 1; continue
        if w == "narrative": span(i, i, ["question" + pun]); i += 1; continue
        if w == "whether" and n(i + 1) == "clothing": span(i, i + 1, ["where", "the", "clothing"]); i += 2; continue
        if w == "sixteen" and n(i + 1) == "million": span(i, i + 2, ["$16", "million"]); i += 3; continue
        if w == "twenty" and n(i + 1) == "twenty" and n(i + 2) == "four": span(i, i + 2, ["2024"]); i += 3; continue
        if w == "one" and n(i + 1) == "hundred": span(i, i + 3, ["$125"]); i += 4; continue
        if w == "fifty": span(i, i, ["$50"]); i += 1; continue
        out.append({"w": ws[i]["w"], "s": ws[i]["s"], "e": ws[i]["e"]}); i += 1
    return out

EMPH = {"scam", "scams", "lesson", "controversy", "question", "less", "middle", "$16", "million", "2024", "wholesale",
        "white", "labeling", "opportunity", "$125", "$50", "demand", "already", "exists", "new", "better", "affordable",
        "comparable", "denied", "sweatshirts"}
tok = fix(WORDS)
chunks, cur = [], []
for t in tok:
    cur.append(t)
    chars = sum(len(x["w"]) + 1 for x in cur)
    endp = bool(re.search(r"[.,?!]$", t["w"]))
    if len(cur) >= 4 or chars >= 24 or (endp and len(cur) >= 2): chunks.append(cur); cur = []
if cur: chunks.append(cur)
# fold a one-word tail into the previous chunk when it still fits
fold = []
for c in chunks:
    if fold and len(c) == 1 and sum(len(x["w"]) + 1 for x in fold[-1]) + len(c[0]["w"]) < 29 and len(fold[-1]) < 5 and not re.search(r"[.?!]$", fold[-1][-1]["w"]):
        fold[-1] += c
    else: fold.append(c)
chunks = fold
for k in range(len(chunks) - 1, 0, -1):          # no stranded one-word chunk after a long one
    if len(chunks[k]) == 1 and len(chunks[k - 1]) >= 3 and not re.search(r"[.?!]$", chunks[k - 1][-1]["w"]):
        chunks[k].insert(0, chunks[k - 1].pop())

caps_html, caps_js = [], []
for k, c in enumerate(chunks):
    t0 = c[0]["s"]; t1 = c[-1]["e"]
    nxt = chunks[k + 1][0]["s"] if k + 1 < len(chunks) else END
    t_end = nxt if nxt - t1 < 0.45 else t1 + 0.18
    ws = "".join(f'<span class="w{" em" if norm(w["w"]).rstrip(chr(63)) in EMPH else ""}" id="w{k}_{q}">{html.escape(w["w"])}</span>' for q, w in enumerate(c))
    caps_html.append(f'<div class="cap" id="c{k}">{ws}</div>')
    caps_js.append(f'[{r(t0)},{r(t_end)},{k},{json.dumps([r(w["s"]) for w in c])}]')
print(len(chunks), "caption chunks")

# ------------------------------------------------------------------ sound
S = []
def snd(i, f, t, d, v, ms=0.0): S.append((i, f, r(max(t, 0)), r(d), v, r(ms)))
def typing(tag, t0, t1, v=0.7):
    t, n = t0, 0
    while t < t1 - 0.05:
        d = min(1.0, t1 - t + 0.05); snd(f"{tag}{n}", "keys.wav", t, d, v, 0.12); t += 0.95; n += 1
RS, RM = 0.45, 0.75
typing("k1", 0.12, 1.48, 0.8); snd("c-hl", "click.mp3", 1.52, 0.3, 0.5)
snd("p-g2", "popup.wav", T["g2_in"], 0.22, 0.55); snd("b-g2a", "bubble.wav", T["controv"], 0.18, 0.5)
snd("r-g3", "riser-s.wav", T["g3_in"] - RS + 0.2, RS, 0.7)
for n, t in enumerate((T["comparable"] - 0.25, T["ownbrand"] - 0.2, T["less"] - 0.1)): snd(f"b-g3{n}", "bubble.wav", t, 0.18, 0.5)
snd("c-flip", "click.mp3", T["ownbrand"] + 0.05, 0.3, 0.45)
snd("r-g4", "riser-s.wav", T["g4a_in"] - RS + 0.2, RS, 0.7)
typing("k4", T["chelsea"], T["chelsea"] + 0.95, 0.75)
snd("p-g4b", "popup.wav", T["g4b_in"], 0.22, 0.55); snd("b-g4b", "bubble.wav", T["name"] - 0.1, 0.18, 0.5)
typing("k5", T["g5_in"] + 0.10, T["g5_in"] + 1.0, 0.75); snd("b-g5", "bubble-in.wav", T["middle"], 0.18, 0.5)
snd("r-g6", "riser-m.wav", T["g6_in"] - RM + 0.25, RM, 0.7)
snd("b-g6a", "bubble.wav", T["brand"], 0.18, 0.5)
snd("r-g6b", "riser-m.wav", T["m16"] - RM, RM, 0.75); snd("l-g6", "land.wav", T["m16"] + 0.95, 0.8, 0.5)
snd("p-g7", "popup.wav", T["g7_in"], 0.22, 0.55); snd("b-g7a", "bubble.wav", T["manuf"] - 0.2, 0.18, 0.5); snd("b-g7b", "bubble.wav", T["wholesale"] - 0.15, 0.18, 0.5)
typing("k6", T["denied"] - 0.45, T["denied"] + 0.35, 0.7); snd("c-denied", "click.mp3", T["denied"] + 0.55, 0.3, 0.55)
snd("b-chip1", "bubble.wav", T["custom"], 0.18, 0.5); snd("b-chip2", "bubble.wav", T["revis"], 0.18, 0.5)
snd("r-g8", "riser-m.wav", T["g8_in"] - RM + 0.25, RM, 0.7); snd("b-g8", "bubble.wav", T["opp"] - 0.1, 0.18, 0.5)
snd("p-g9", "popup.wav", T["g9_in"], 0.22, 0.55); snd("c-p125", "click.mp3", T["p125"] + 0.35, 0.3, 0.5)
snd("b-g9", "bubble.wav", T["compq"], 0.18, 0.5); snd("c-p50", "click.mp3", T["p50"] + 0.1, 0.3, 0.5); snd("b-g9b", "bubble.wav", T["p50"] + 0.6, 0.18, 0.5)
snd("p-g10", "popup.wav", T["g10_in"], 0.22, 0.55); snd("b-g10", "bubble.wav", T["demand"], 0.18, 0.5); snd("c-strike", "click.mp3", T["sweat"] - 0.1, 0.3, 0.5)
snd("p-g11", "popup.wav", T["g11_in"], 0.22, 0.55); snd("b-g11", "bubble.wav", T["notjust"] - 0.2, 0.18, 0.5)
snd("r-g12", "riser-s.wav", T["g12_in"] - RS + 0.2, RS, 0.7)
for n, t in enumerate((T["g12_in"] + 0.25, T["better"] - 0.05, T["build"] - 0.15)): snd(f"b-g12{n}", "bubble.wav", t, 0.18, 0.5)
snd("c-inv", "click.mp3", T["invent"] + 0.7, 0.3, 0.5)
audio = "\n".join(f'      <audio id="{i}" src="assets/sfx/{f}" data-start="{t}" data-duration="{d}" data-media-start="{ms}" '
                  f'data-track-index="{10 + n}" data-volume="{v}"></audio>' for n, (i, f, t, d, v, ms) in enumerate(S))

# ------------------------------------------------------------------ page
page = open("tools/template.html").read()
scene_attrs = {sid: f'data-start="{s}" data-duration="{d}"' for sid, (s, d) in WIN.items()}
for sid, a in scene_attrs.items(): page = page.replace(f"__WIN_{sid}__", a)
tov = (r(T["denied"] - 0.6), r(T["g8_in"] - T["denied"] + 0.6)); tov2 = (r(T["invent"] - 0.3), r(T["g12_in"] - T["invent"] + 0.3))
page = (page.replace("__TOV_S__", str(tov[0])).replace("__TOV_D__", str(tov[1])).replace("__TOV2_S__", str(tov2[0])).replace("__TOV2_D__", str(tov2[1]))
        .replace("__END__", str(END)).replace("__T__", json.dumps({k: r(v) for k, v in T.items()}))
        .replace("__SC__", json.dumps([[sid, r(a), r(b), ex] for sid, a, b, ex in SC]))
        .replace("__NAVY__", json.dumps(sorted(NAVY_SCENES)))
        .replace("__VZ__", json.dumps([[r(a), r(b), s0, s1] for a, b, s0, s1 in VZ]))
        .replace("__CAPS_HTML__", "\n        ".join(caps_html))
        .replace("__CAPS__", "[" + ",".join(caps_js) + "]")
        .replace("__AUDIO__", audio))
open("index.html", "w").write(page)
print(f"index.html: {len(S)} sounds")
