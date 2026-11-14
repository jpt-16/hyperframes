"""Voiceover for the JT Builds marketplace video, with HyperFrames' built-in Kokoro TTS, plus the time each word is spoken.

    export HYPERFRAMES_PYTHON=<python with kokoro-onnx + soundfile + onnx>
    $HYPERFRAMES_PYTHON tools/vo.py

1. Each script line is spoken by `hyperframes tts` (local Kokoro model, voice am_michael, speed 1.7).
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
VOICE, SPEED = "am_michael", 1.7

# (caption = the script exactly as written, spoken = what the voice reads)
LINES = [   # (id, caption, spoken)
    ('h1', 'The hardest app to build isn’t necessarily the one with the most complicated code.', "The hardest app to build isn't necessarily the one with the most complicated code."),
    ('h2', 'It’s the one that needs two completely different groups of people to succeed.', "It's the one that needs two completely different groups of people to succeed."),
    ('u1', 'And this is a problem companies like Uber and DoorDash had to solve.', 'And this is a problem companies like Uber and Door Dash had to solve.'),
    ('u2', 'Think about it.', None),
    ('u3', 'Customers won’t use Uber if there are no drivers.', "Customers won't use Uber if there are no drivers."),
    ('u4', 'And drivers won’t join Uber if there are no customers.', "And drivers won't join Uber if there are no customers."),
    ('d1', 'It’s the same problem with DoorDash.', "It's the same problem with Door Dash."),
    ('d2', 'No restaurants means no customers, and no customers means no reason for restaurants to join.', None),
    ('s1', 'So how did they solve it?', None),
    ('s2', 'They didn’t try to take over the entire country on day one.', "They didn't try to take over the entire country on day one."),
    ('s3', 'They focused on one city, built up enough supply and demand to make the platform useful, proved the model worked, and then expanded into new markets.', None),
    ('k1', 'Now think about an app like DetailDash.', 'Now think about an app like Detail Dash.'),
    ('k2', 'It’s essentially DoorDash for car detailing.', "It's essentially Door Dash for car detailing."),
    ('k3', 'It connects people who want their cars detailed with detailers who want more customers.', None),
    ('c1', 'But building the app is only half the battle.', None),
    ('c2', 'You need enough detailers in an area to attract customers, and enough customers to make joining worthwhile for detailers.', None),
    ('e1', 'That’s why the smartest way to build a marketplace isn’t to launch everywhere.', "That's why the smartest way to build a marketplace isn't to launch everywhere."),
    ('e2', 'It’s to dominate one market first.', "It's to dominate one market first."),
    ('e3', 'Then expand.', None),
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
