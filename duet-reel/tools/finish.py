"""Instagram Reels deliverables from the HyperFrames render.

    python3 tools/finish.py
writes renders/claude-duet-reel-ig.mp4        (with the voiceover)
       renders/claude-duet-reel-novo-ig.mp4   (same picture, effects + music bed only, for an external voiceover)
H.264 High, 1080x1920, 30 fps, yuv420p, ~12 Mb/s; AAC 48 kHz 256 kb/s; moov atom up front (fast start).
"""
import os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(HERE, "..")
src = os.path.join(P, "renders", "claude-duet-reel.mp4")
V = ["-c:v", "libx264", "-profile:v", "high", "-level", "4.2", "-preset", "slow", "-b:v", "12M", "-maxrate", "16M", "-bufsize", "24M",
     "-pix_fmt", "yuv420p", "-r", "30", "-g", "60", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart"]
for name, audio in [("claude-duet-reel-ig.mp4", "mix.wav"), ("claude-duet-reel-novo-ig.mp4", "mix-novo.wav")]:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-i", os.path.join(P, "assets", audio), "-map", "0:v:0", "-map", "1:a:0", *V, "-shortest",
                    os.path.join(P, "renders", name)], check=True)
    print("renders/" + name)
