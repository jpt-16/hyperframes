#!/usr/bin/env bash
# Rebuild base.mp4 from the original upload (gitignored: personal footage).
#   tools/prep_base.sh <original.mp4>
# The upload has a keyframe only every 4-8 s and full-range (yuvj420p) colour,
# which makes every seek decode seconds of video. Re-encode once: lanczos to
# 1080x1920, limited range, keyframe every second. Audio is copied untouched.
set -euo pipefail
ffmpeg -v error -y -i "$1" \
  -vf "scale=1080:1920:flags=lanczos:in_range=full:out_range=tv,format=yuv420p,fps=30" \
  -c:v libx264 -preset slow -crf 15 -g 30 -keyint_min 30 -sc_threshold 0 \
  -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -c:a copy -movflags +faststart base.mp4
