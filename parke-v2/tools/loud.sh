#!/usr/bin/env bash
# Make the voice louder without distortion: high-pass, gentle compression, then two-pass loudness
# normalisation to -13.5 LUFS with a -1.5 dBTP ceiling. Video is copied untouched.
#   tools/loud.sh            (reads base_quiet.mp4, writes base.mp4)
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f base_quiet.mp4 ] || cp base.mp4 base_quiet.mp4
PRE="highpass=f=80,acompressor=threshold=-26dB:ratio=3.2:attack=5:release=110:makeup=5dB"
M=$(ffmpeg -hide_banner -i base_quiet.mp4 -af "$PRE,loudnorm=I=-13.5:TP=-1.5:LRA=9:print_format=json" -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$M" | python3 -c "import sys,json;print(json.load(sys.stdin)['$1'])"; }
ffmpeg -v error -y -i base_quiet.mp4 -c:v copy \
  -af "$PRE,loudnorm=I=-13.5:TP=-1.5:LRA=9:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,alimiter=limit=0.84:level=false" \
  -c:a aac -b:a 192k -movflags +faststart base.mp4
