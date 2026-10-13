#!/usr/bin/env bash
# Preview or check the reveal reel without touching index.html (the founder reel).
#
#   tools/reveal/workspace.sh preview   # Studio on reveal.html
#   tools/reveal/workspace.sh check     # lint + runtime + layout + motion + contrast on reveal.html
#
# HyperFrames' preview/check always read a project's index.html, so this builds a
# throwaway workspace (.reveal-workspace/, gitignored) whose index.html is
# reveal.html and whose assets are symlinks back into this project.
set -euo pipefail
cd "$(dirname "$0")/../.."
HF="npx --yes hyperframes@0.8.154"
W=.reveal-workspace
rm -rf "$W"; mkdir -p "$W"
for f in compositions assets vendor hyperframes.json package.json meta.json; do ln -s "../$f" "$W/$f"; done
cp reveal.html "$W/index.html"
case "${1:-preview}" in
  preview) $HF preview "$W" ;;
  check)   $HF check "$W" ;;
  *) echo "usage: $0 preview|check" >&2; exit 2 ;;
esac
