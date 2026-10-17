"""Copy lint: keep every on-screen word honest and readable.

Errors (block the build):
  - promises about rankings, traffic, leads or results ("guaranteed #1 on Google",
    "double your leads", "rank on page one"). A sentence that NEGATES the claim
    ("no one can guarantee rankings") is allowed, because saying so is accurate.
Warnings: text longer than its slot comfortably holds.
"""
import re

CLAIMS = [
    (r"\bguarantee[sd]?\b|\bguaranteed\b", "guarantee language"),
    (r"#\s?1\b|\bnumber[- ]one\b|\bno\.\s?1\b", "a #1 claim"),
    (r"\b(top|first)\s+(spot|page|place|position|result)\b|\bpage\s+(one|1)\b|\btop of google\b", "a ranking-position promise"),
    (r"\b(rank|ranks|ranking|rankings)\b[^.!?]*\b(first|top|higher|#1)\b", "a ranking promise"),
    (r"\b\d+\s?(x|%)\s+(more\s+)?(leads|traffic|calls|customers|sales|revenue|bookings|clicks)\b", "a specific results promise"),
    (r"\b(double|triple|10x|explode|skyrocket)\w*\s+(your\s+)?(leads|traffic|calls|sales|revenue|bookings|customers)\b", "a results promise"),
    (r"\b(overnight|instant(ly)?|in days)\b[^.!?]*\b(rank\w*|leads|traffic|results|customers)\b", "an instant-results promise"),
    (r"\bwill\s+(rank|get you (more|to)|bring (you )?more|flood)\b", "a promised outcome"),
    (r"\b(more|extra)\s+(leads|customers|calls|traffic)\s+(guaranteed|fast|today)\b", "a results promise"),
]
NEGATION = re.compile(r"\b(no|not|never|can'?t|cannot|won'?t|doesn'?t|don'?t|nobody|no one|isn'?t|aren'?t)\b|n['’]t\b", re.I)

LIMITS = {  # (path pattern, max visible chars)
    "hook.lines": 18, "head": 60, "problems": 22, "fixes": 22, "changes": 26, "tips.text": 24, "tips.sub": 30,
    "factors": 26, "cta.headline": 48, "cta.action": 26, "cta.sub": 90, "mistake": 40, "fix": 40,
}

def _strings(x, path=""):
    if isinstance(x, str): yield path, x
    elif isinstance(x, dict):
        for k, v in x.items():
            if k.startswith("_") or k in ("template", "niche", "slug", "style", "type", "ring", "section", "seed"): continue
            yield from _strings(v, f"{path}.{k}" if path else k)
    elif isinstance(x, list):
        for v in x: yield from _strings(v, path)

def lint(spec):
    errors, warnings = [], []
    allow = set(spec.get("_allow", []))
    for path, s in _strings(spec):
        text = s.replace("*", "")
        for sentence in re.split(r"(?<=[.!?])\s+|\n", text):
            for pat, what in CLAIMS:
                if what in allow: continue
                if re.search(pat, sentence, re.I) and not NEGATION.search(sentence):
                    errors.append(f"{path}: {what} in “{sentence.strip()}”")
        for key, mx in LIMITS.items():
            if path.endswith(key) and len(text.replace("\n", " ")) > mx:
                warnings.append(f"{path}: {len(text)} chars (keep under {mx} to stay readable): “{text}”")
    return errors, warnings

if __name__ == "__main__":
    tests = ["We guarantee #1 on Google", "No one can guarantee rankings.", "Double your leads in 30 days",
             "Get 3x more calls", "Rank on page one fast", "These help Google understand your business.",
             "Google doesn't promise a top spot.", "Reviews, links, reputation"]
    for t in tests: print(f"{t!r:50} ->", lint({"head": t})[0] or "ok")
