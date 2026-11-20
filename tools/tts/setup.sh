#!/usr/bin/env bash
# One-time setup of the local voiceover (nothing is sent anywhere when speaking), any machine, CPU only.
# One uv venv (.venv) with both engines, about 1 GB:
# - English: Kokoro-82M (Apache-2.0), the pinned model revision and three voices in voices/kokoro/ (~330 MB).
#   PyTorch is the CPU build: Kokoro runs about 10x real time there, no GPU needed.
# - Hungarian: Piper and the three hu_HU voices (~200 MB). The voices are trained on a CC0 dataset,
#   fine-tuned from Piper's English "lessac" voice; check that base model's licence before external use.
set -eu
cd "$(dirname "$0")"

[ -x .venv/bin/python ] || uv venv -q --python 3.12 .venv
uv pip install -q --python .venv/bin/python --torch-backend cpu "piper-tts==1.8.0" "torch==2.8.0" "kokoro==0.9.4" \
  "soundfile==0.13.1" "pip" \
  "en_core_web_sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl"

mkdir -p voices/kokoro
for v in anna berta imre; do
  for ext in onnx onnx.json; do
    f="voices/hu_HU-$v-medium.$ext"
    [ -s "$f" ] || curl -sfL -o "$f" "https://huggingface.co/rhasspy/piper-voices/resolve/main/hu/hu_HU/$v/medium/hu_HU-$v-medium.$ext"
  done
done
kokoro="https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987"
for f in config.json kokoro-v1_0.pth voices/am_michael.pt voices/bm_george.pt voices/af_heart.pt; do
  dst="voices/kokoro/$(basename "$f")"
  [ -s "$dst" ] || curl -sfL -o "$dst" "$kokoro/$f"
done
echo "tts ready: $(ls voices/*.onnx | wc -l) Hungarian, $(ls voices/kokoro/*.pt | wc -l) English voices"
