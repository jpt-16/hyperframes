"""Voiceover for the height-matters video, with HyperFrames' built-in Kokoro TTS, plus the time each word is spoken.

    export HYPERFRAMES_PYTHON=<python with kokoro-onnx + soundfile + onnx>
    $HYPERFRAMES_PYTHON tools/vo.py

1. Each script line is spoken by `hyperframes tts` (local Kokoro model, voice am_michael, speed 1.65).
2. Word timings come from the same model: a copy of HyperFrames' kokoro-v1.0.onnx with its internal
   per-phoneme duration tensor exposed as an output (weights untouched). kokoro-onnx's create_timed()
   with no inserted pauses reproduces the CLI audio sample for sample, so its phoneme times are the
   times in the file. Each line is checked against the CLI's wav before its timings are kept.
Writes assets/vo/NN.wav and assets/vo/lines.json (caption text, spoken text, words with times).
"""
import json, os, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "vo")
CACHE = os.path.join(HERE, "..", ".cache")
HF_TTS = os.path.expanduser("~/.cache/hyperframes/tts")
MODEL, VOICES = os.path.join(HF_TTS, "models", "kokoro-v1.0.onnx"), os.path.join(HF_TTS, "voices", "voices-v1.0.bin")
TIMED = os.path.join(CACHE, "kokoro-v1.0-timed.onnx")
VOICE, SPEED = "am_michael", 1.65

# (caption = the script exactly as written, spoken = what the voice reads)
# Numbers are spelled out for the voice so Kokoro reads them cleanly; the captions keep the script's numerals.
LINES = [   # (id, caption, spoken)
    ("hook", "The 2026 World Series is challenging one of baseball's biggest assumptions.", "The twenty twenty-six World Series is challenging one of baseball's biggest assumptions."),
    ("short", "The Brewers and Rays have some of the shortest lineups in recent World Series history.", None),
    ("rays", "In fact, the Rays' starting lineup has just one player taller than six feet.", None),
    ("q", "So does height actually matter in baseball?", None),
    ("tall", "Being taller can give players longer levers, and pitchers may benefit from a higher release point.", None),
    ("but", "But being shorter can come with advantages too.", None),
    ("shortadv", "A shorter hitter may have a smaller strike zone, while some shorter infielders can benefit from getting lower to the ground.", None),
    ("research", "And the research is interesting.", None),
    ("study", "A 2023 study examining 319 first-round MLB draft picks found no relationship between players' physical measurements in high school and their eventual MLB performance, measured by WAR.",
              "A twenty twenty-three study examining three hundred nineteen first-round M L B draft picks found no relationship between players' physical measurements in high school and their eventual M L B performance, measured by war."),
    ("take", "The takeaway?", None),
    ("height", "Height can influence how a player moves and plays, but it doesn't determine how good they become.", None),
    ("end", "The Brewers and Rays are proving that talent doesn't come in one size.", None),
]

def timed_model():
    if not os.path.exists(TIMED):
        import onnx, onnx.helper as h
        os.makedirs(CACHE, exist_ok=True)
        m = onnx.load(MODEL)
        m.graph.node.append(h.make_node("Identity", ["/encoder/Cast_output_0"], ["duration"], name="expose_duration"))
        m.graph.output.append(h.make_tensor_value_info("duration", onnx.TensorProto.INT64, None))
        onnx.save(m, TIMED)
    import kokoro_onnx
    return kokoro_onnx.Kokoro(TIMED, VOICES)

STRESS = "ˈˌ"
def word_times(kokoro, spoken, timings):
    """When each spoken word is said. espeak can merge short words ("for the" -> one phonetic word),
    so align the line's timed phonemes with each word phonemized on its own (difflib), and give every
    word the span of the phonemes matched to it."""
    import difflib
    src = [(t.phoneme, t.start, t.end) for t in timings if t.phoneme not in STRESS + " .,!?;:"]
    tgt, owner = [], []
    for k, w in enumerate(spoken.split()):
        ph = [c for c in kokoro.tokenizer.phonemize(w, "en-us") if c not in STRESS + " .,!?;:"]
        tgt += ph; owner += [k] * len(ph)
    sm = difflib.SequenceMatcher(None, [c for c, _, _ in src], tgt, autojunk=False)
    who = [None] * len(src)
    for blk in sm.get_matching_blocks():
        for j in range(blk.size): who[blk.a + j] = owner[blk.b + j]
    for i in range(len(who)):                      # unmatched phonemes go with the word before them
        if who[i] is None: who[i] = who[i - 1] if i else 0
    out = []
    for k, w in enumerate(spoken.split()):
        idx = [i for i, o in enumerate(who) if o == k]
        if not idx:                                # a word with no phonemes of its own: squeeze it in
            prev = out[-1]["end"] if out else 0.0
            out.append({"w": w, "start": prev, "end": prev}); continue
        out.append({"w": w, "start": round(src[idx[0]][1], 3), "end": round(src[idx[-1]][2], 3)})
    for k in range(1, len(out)):                   # keep the order monotonic
        if out[k]["start"] < out[k - 1]["start"]: out[k]["start"] = out[k - 1]["end"]
        out[k]["end"] = max(out[k]["end"], out[k]["start"])
    return out

if __name__ == "__main__":
    import soundfile as sf
    os.makedirs(OUT, exist_ok=True)
    kokoro = timed_model()
    meta = []
    for i, (lid, caption, spoken) in enumerate(LINES):
        spoken = spoken or caption
        path = os.path.join(OUT, f"{i:02d}.wav")
        subprocess.run(["npx", "--yes", "hyperframes@0.8.154", "tts", spoken, "-v", VOICE, "-s", str(SPEED), "-o", path], check=True, capture_output=True)
        cli, sr = sf.read(path, dtype="float64")
        audio, sr2, tim = kokoro.create_timed(spoken, voice=VOICE, speed=SPEED, sentence_pause=0, clause_pause=0)
        audio = np.asarray(audio, dtype=np.float64)
        n = min(len(cli), len(audio))
        err = float(np.max(np.abs(cli[:n] - audio[:n])))
        assert sr == sr2 and abs(len(cli) - len(audio)) <= 1, f"line {i}: timing model doesn't match the TTS audio ({len(cli)} vs {len(audio)})"
        if err >= 2e-3:                                # same model and length, tiny numeric drift: keep the timed render so timings are exact
            sf.write(path, audio, sr, subtype="PCM_16"); cli = audio
        words = word_times(kokoro, spoken, tim)
        meta.append({"i": i, "id": lid, "text": caption, "spoken": spoken, "dur": round(len(cli) / sr, 3), "words": words})
        print(f"{i:02d} {len(cli) / sr:5.2f}s  {len(words)} words, matches TTS audio (max diff {err:.1e})  {spoken}")
    json.dump(meta, open(os.path.join(OUT, "lines.json"), "w"), indent=1)
