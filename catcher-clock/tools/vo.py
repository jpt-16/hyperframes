"""Scratch voiceover: one local text-to-speech clip per script line (Kokoro, voice am_michael).
    HYPERFRAMES_PYTHON=<venv python with kokoro-onnx> python3 tools/vo.py
Writes assets/vo/NN.wav and assets/vo/lines.json. A real voiceover can replace it (see README)."""
import json, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "assets", "vo")

# (caption = the script exactly as written, spoken = what the voice model reads)
# Numbers are spelled out for the voice: "1.9-second" otherwise comes out as "one. nine second".
LINES = [
    ("Everyone judges a catcher by how fast he throws to second.", None),
    ("But that's only half the story.", None),
    ("Because before the catcher can even make a throw, the pitcher has to deliver the ball.", None),
    ("Let's say the pitcher takes 1.4 seconds to deliver, and the catcher has a 1.9-second pop time.",
     "Let's say the pitcher takes one point four seconds to deliver, and the catcher has a one point nine second pop time."),
    ("That's 3.3 seconds before accounting for the runner's jump and the tag.",
     "That's three point three seconds before accounting for the runner's jump and the tag."),
    ("Now compare that with a pitcher who delivers in 1.2 seconds.",
     "Now compare that with a pitcher who delivers in one point two seconds."),
    ("That's two-tenths of a second less time for the runner to advance.", None),
    ("And that's why stopping a stolen base isn't just a catching problem.", None),
    ("It's a race between the pitcher's delivery, the catcher's throw, and the runner's jump.", None),
    ("So next time a runner steals second, don't just blame the catcher.", None),
    ("Look at the clock.", None),
]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    meta = []
    for i, (caption, spoken) in enumerate(LINES):
        spoken = spoken or caption
        path = os.path.join(OUT, f"{i:02d}.wav")
        if not os.path.exists(path):
            subprocess.run(["npx", "--yes", "hyperframes@0.8.154", "tts", spoken, "-v", "am_michael", "-o", path], check=True, capture_output=True)
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout)
        meta.append({"i": i, "text": caption, "spoken": spoken, "dur": round(d, 3)})
        print(f"{i:02d} {d:5.2f}s  {spoken}")
    json.dump(meta, open(os.path.join(OUT, "lines.json"), "w"), indent=1)
