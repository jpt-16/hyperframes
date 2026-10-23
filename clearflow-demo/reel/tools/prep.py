"""Turn the frame captures into the reel's video tracks and an event timeline.

    python3 tools/prep.py      (after node tools/capture.mjs)

The phone recording is re-timed in segments: answers play at real speed, the pauses
and the typing play faster. Frames are only dropped or held, never altered.
Every recorded event (tap, bot reply, lead sent) is mapped onto the reel's clock
and written to assets/media/timeline.json so sounds and labels land on the exact frame.
"""
import json, os, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CAP = os.path.join(ROOT, "capture")
MEDIA = os.path.join(ROOT, "assets", "media")
FPS = 30

PHONE_START = 2.85                       # reel time the phone recording starts
SEGMENTS = [                             # (source start, source end, speed)
    (0.0, 3.1, 1.0),                     # the site, tap the chat button, greeting
    (3.1, 5.4, 1.0),                     # "Do you handle emergencies?" and the answer
    (5.4, 8.7, 2.2),                     # reading pause + typing "Do you serve Lakewood?"
    (8.7, 10.9, 1.0),                    # the Lakewood answer
    (10.9, 15.7, 1.6),                   # Book a plumber, name
    (15.7, 24.4, 1.8),                   # phone, service, details
    (24.4, 28.8, 1.0),                   # review card, send, "Request sent"
]
DASH_LEN = 4.2

def out_segments():
    t, segs = PHONE_START, []
    for a, b, sp in SEGMENTS:
        d = (b - a) / sp
        segs.append((a, b, sp, t, t + d)); t += d
    return segs

def to_out(src_t):
    for a, b, sp, o0, o1 in out_segments():
        if a <= src_t <= b: return round(o0 + (src_t - a) / sp, 3)
    return None

def encode(frames, src_dir, dst, scale=None):
    tmp = dst + ".seq"; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    for i, f in enumerate(frames):
        os.symlink(os.path.abspath(os.path.join(src_dir, f"{f:05d}.jpg")), os.path.join(tmp, f"{i:05d}.jpg"))
    vf = (f"scale={scale}:flags=lanczos," if scale else "") + "format=yuv420p"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.jpg"), "-vf", vf,
                    "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-g", "15", "-movflags", "+faststart", dst], check=True)
    shutil.rmtree(tmp)

if __name__ == "__main__":
    os.makedirs(MEDIA, exist_ok=True)
    cap = json.load(open(os.path.join(CAP, "phone-events.json")))
    n_src = cap["frames"]
    frames = []
    for a, b, sp, o0, o1 in out_segments():
        for k in range(round((o1 - o0) * FPS)):
            frames.append(min(n_src - 1, round((a + k / FPS * sp) * FPS)))
    encode(frames, os.path.join(CAP, "phone"), os.path.join(MEDIA, "phone.mp4"))
    phone_end = round(PHONE_START + len(frames) / FPS, 3)

    dash_frames = list(range(round(DASH_LEN * FPS)))
    encode(dash_frames, os.path.join(CAP, "dash"), os.path.join(MEDIA, "dash.mp4"), scale="1760:1088")

    events = []
    for e in cap["events"]:
        t = to_out(e["t"])
        if t is None: continue
        ev = {"t": t, "type": e["type"]}
        for k in ("what", "x", "y", "text"):
            if k in e: ev[k] = e[k]
        events.append(ev)
    json.dump({"phone_start": PHONE_START, "phone_end": phone_end, "dash_len": DASH_LEN, "events": events},
              open(os.path.join(MEDIA, "timeline.json"), "w"), indent=1)
    print(f"phone.mp4: {len(frames)} frames ({PHONE_START}-{phone_end}s), dash.mp4: {len(dash_frames)} frames, {len(events)} events")
