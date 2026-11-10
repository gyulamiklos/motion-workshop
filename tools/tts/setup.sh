#!/usr/bin/env bash
# One-time setup of the local Hungarian voiceover: a uv venv with piper-tts and the three hu_HU voices.
# The voices are trained on a CC0 dataset, fine-tuned from Piper's English "lessac" voice; check that
# base model's licence before using a voice in anything published outside the team.
set -eu
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || uv venv -q .venv
uv pip install -q --python .venv/bin/python "piper-tts==1.8.0"
mkdir -p voices
for v in anna berta imre; do
  for ext in onnx onnx.json; do
    f="voices/hu_HU-$v-medium.$ext"
    [ -s "$f" ] || curl -sfL -o "$f" "https://huggingface.co/rhasspy/piper-voices/resolve/main/hu/hu_HU/$v/medium/hu_HU-$v-medium.$ext"
  done
done
echo "tts ready: $(ls voices/*.onnx | wc -l) voices"
