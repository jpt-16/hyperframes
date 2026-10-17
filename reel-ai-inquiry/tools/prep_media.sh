#!/usr/bin/env bash
# Rebuild media/ from the original uploads (gitignored: his footage + demo recording).
#   tools/prep_media.sh <talking-head.mp4> <demo screen recording>
set -euo pipefail
cd "$(dirname "$0")/.."
TH="$1"; DEMO="$2"; mkdir -p media
X264="-c:v libx264 -preset slow -crf 15 -g 15 -keyint_min 15 -sc_threshold 0 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709"

# Talking head: same picture, keyframe every half second so seeks are instant; audio untouched.
ffmpeg -v error -y -i "$TH" -vf "fps=30" $X264 -c:a copy -movflags +faststart media/base_src.mp4   # un-cut reference; tools/cut_base.py makes media/base.mp4

# Demo: full frame kept at 2160 px wide so the composition can zoom into crops and stay sharp.
# Each segment is retimed so the demo moment lands on the line that describes it.
demo() {  # name src_in src_out out_dur
  local k; k=$(python3 -c "print(round($4/($3-$2),5))")
  ffmpeg -v error -y -ss "$2" -to "$3" -i "$DEMO" \
    -vf "setpts=$k*(PTS-STARTPTS),fps=30,scale=2160:-2:flags=lanczos:in_range=full:out_range=tv,setsar=1" -an $X264 "media/$1.mp4"
}
demo demo-form    0.00  1.70  3.95   # form fills + "Sending..."      -> "a customer submits a quote request..."
demo demo-ai      1.60  5.80  3.70   # "AI is writing", reply streams -> "the AI ... generates a personalized response"
demo demo-saved   6.10 12.20  5.90   # request received -> leads dashboard, Responded -> "the whole process happens automatically..."
# The website itself, before anyone touches it, for "requests a quote through their website".
ffmpeg -v error -y -ss 0.05 -i "$DEMO" -frames:v 1 -vf "scale=2160:-2:flags=lanczos:in_range=full:out_range=tv" media/demo-site.png
ls -la media
