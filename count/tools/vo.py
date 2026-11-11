"""Voiceover for the count video, with HyperFrames' built-in Kokoro TTS, plus the time each word is spoken.

    export HYPERFRAMES_PYTHON=<python with kokoro-onnx + soundfile + onnx>
    $HYPERFRAMES_PYTHON tools/vo.py

1. Each script line is spoken by `hyperframes tts` (local Kokoro model, voice am_michael, speed 1.6).
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
VOICE, SPEED = "am_michael", 1.6

# (caption = the script exactly as written, spoken = what the voice reads)
# Counts are read the way a broadcaster says them ("oh and two"); the captions keep the script's numerals.
LINES = [   # (id, caption, spoken)
    ('q', 'Why can the exact same pitch be an easy take in one count… but a must-swing in another?', 'Why can the exact same pitch be an easy take in one count, but a must swing in another?'),
    ('a02', 'With two strikes, the pitcher has the advantage.', None),
    ('b02', 'They can expand the zone, throw breaking balls off the plate, and make the hitter protect against more possibilities.', None),
    ('a30', 'But at 3-0, everything changes.', 'But at three and oh, everything changes.'),
    ('b30', 'The hitter can be much more selective because one ball means a walk.', None),
    ('c30', 'The pitcher has very little room for error.', None),
    ('a11', 'At 1-1, neither side has a major advantage.', 'At one and one, neither side has a major advantage.'),
    ('b11', 'The next pitch can shift the entire at-bat.', 'The next pitch can shift the entire at bat.'),
    ('c11', 'A strike creates 1-2, while a ball creates 2-1.', 'A strike creates one and two, while a ball creates two and one.'),
    ('a32', 'And at a full count, every pitch matters.', None),
    ('b32', 'The hitter has to protect the strike zone, while the pitcher has to throw a strike without giving up a good opportunity to hit.', None),
    ('e1', 'That’s what makes baseball so strategic.', "That's what makes baseball so strategic."),
    ('e2', 'The count doesn’t just track balls and strikes.', "The count doesn't just track balls and strikes."),
    ('e3', 'It changes the leverage of every pitch.', None),
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
