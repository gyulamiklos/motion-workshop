#!/usr/bin/env bash
# One-time setup of the local Hungarian voiceover (nothing is sent anywhere when speaking).
#   tools/tts/setup.sh            Piper always; MOSS too when an NVIDIA GPU with 8 GB or more is present
#   tools/tts/setup.sh --moss     Piper and MOSS (fails without a CUDA GPU)
#   tools/tts/setup.sh --no-moss  Piper only (any machine)
# Piper: a uv venv with piper-tts and the three hu_HU voices (~200 MB). The voices are trained on a CC0 dataset,
# fine-tuned from Piper's English "lessac" voice; check that base model's licence before external use.
# MOSS: a second venv (.venv-moss, PyTorch with CUDA 12.8) and the pinned MOSS-TTS-Local-Transformer-v1.5 model,
# its audio codec and the Whisper model that picks the best take: about 7 GB of venv and 17 GB in the Hugging Face
# cache (~/.cache/huggingface). All Apache-2.0 or MIT (THIRD_PARTY.md).
set -eu
cd "$(dirname "$0")"

moss=auto
case "${1:-}" in --moss) moss=yes ;; --no-moss) moss=no ;; "") ;; *) echo "usage: setup.sh [--moss|--no-moss]" >&2; exit 2 ;; esac

[ -x .venv/bin/python ] || uv venv -q .venv
uv pip install -q --python .venv/bin/python "piper-tts==1.8.0"
mkdir -p voices
for v in anna berta imre; do
  for ext in onnx onnx.json; do
    f="voices/hu_HU-$v-medium.$ext"
    [ -s "$f" ] || curl -sfL -o "$f" "https://huggingface.co/rhasspy/piper-voices/resolve/main/hu/hu_HU/$v/medium/hu_HU-$v-medium.$ext"
  done
done
echo "piper ready: $(ls voices/*.onnx | wc -l) voices"

if [ "$moss" = auto ]; then
  vram=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | sort -n | tail -1 || true)
  if [ "${vram:-0}" -ge 7500 ]; then moss=yes; else moss=no; echo "no NVIDIA GPU with 8 GB: Piper only (say.py uses Piper)"; fi
fi
[ "$moss" = yes ] || exit 0

[ -x .venv-moss/bin/python ] || uv venv -q --python 3.12 .venv-moss
uv pip install -q --python .venv-moss/bin/python --torch-backend cu128 \
  "torch==2.9.1" "torchaudio==2.9.1" "transformers==5.0.0" "accelerate==1.15.0" "safetensors==0.6.2" \
  "numpy==2.1.0" "soundfile==0.14.0" "faster-whisper==1.2.1" "huggingface-hub==1.33.0"
hf=.venv-moss/bin/hf
$hf download OpenMOSS-Team/MOSS-TTS-Local-Transformer-v1.5 --revision be7766a6735b98bd793f7c79fb720b4d0f5d13b8 >/dev/null
$hf download OpenMOSS-Team/MOSS-Audio-Tokenizer-v2 --revision f6e20e543b33d2c252a7ef71bdf8aa71e5ff9169 >/dev/null
$hf download mobiuslabsgmbh/faster-whisper-large-v3-turbo >/dev/null
.venv-moss/bin/python -c "import torch; assert torch.cuda.is_available(), 'CUDA not available'; print('moss ready on', torch.cuda.get_device_name(0))"
