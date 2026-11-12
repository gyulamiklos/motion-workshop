"""Hungarian voiceover, one WAV per line, run on this machine (nothing leaves it).

Usage: tools/tts/.venv/bin/python tools/tts/say.py <lines.json> <out dir> [--engine auto|moss|piper] [--voice V] [--takes 3] [--rate 1.0]
  lines.json: [{"id": "intro", "text": "..."}, ...]
Writes <out dir>/<id>.wav and <out dir>/voice.json ({"voice": ..., "lines": {id: {"file", "duration", "text"}}}).

Engines (set up once with tools/tts/setup.sh):
  moss   MOSS-TTS-Local-Transformer-v1.5 (tools/tts/moss_say.py): natural, needs an NVIDIA GPU with 8 GB or more and
         about 7 s of compute for 1 s of speech on 8 GB. Voices: male (default), female.
  piper  Piper: instant on any CPU, but sounds mechanical. Voices: imre (male, default), anna, berta (female).
  auto   moss when it is set up, otherwise piper (the default).
A voice name of the other engine is mapped: imre -> male, anna/berta -> female, and back.
"""
import argparse
import json
import pathlib
import subprocess
import sys
import wave

HERE = pathlib.Path(__file__).resolve().parent
MOSS_PY = HERE / ".venv-moss" / "bin" / "python"
LOUDNESS = "loudnorm=I=-15:TP=-1.5:LRA=11"  # every voice line at the same speech loudness (EBU R128)
TO_MOSS = {"imre": "male", "anna": "female", "berta": "female"}
TO_PIPER = {"male": "imre", "female": "anna"}


def normalize(path: pathlib.Path) -> None:
    """Bring a WAV to -15 LUFS with a -1.5 dBTP ceiling (ffmpeg loudnorm), in place: the film then lands near -14 LUFS."""
    tmp = path.with_suffix(".norm.wav")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(path), "-af", LOUDNESS, "-ar", "22050", str(tmp)], check=True)
    tmp.replace(path)


def piper(lines, out: pathlib.Path, voice_name: str, rate: float) -> None:
    from piper import PiperVoice
    from piper.config import SynthesisConfig

    voice = PiperVoice.load(str(HERE / "voices" / f"hu_HU-{voice_name}-medium.onnx"))
    syn = SynthesisConfig(length_scale=rate)
    manifest = {"voice": f"hu_HU-{voice_name}-medium", "lines": {}}
    for line in lines:
        path = out / f"{line['id']}.wav"
        with wave.open(str(path), "wb") as wav:
            voice.synthesize_wav(line["text"], wav, syn_config=syn)
        normalize(path)
        with wave.open(str(path), "rb") as wav:
            duration = wav.getnframes() / wav.getframerate()
        manifest["lines"][line["id"]] = {"file": path.name, "duration": round(duration, 3), "text": line["text"]}
        print(f"{line['id']}: {duration:.2f}s")
    (out / "voice.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lines")
    ap.add_argument("out")
    ap.add_argument("--engine", default="auto", choices=["auto", "moss", "piper"])
    ap.add_argument("--voice", help="moss: male (default), female; piper: imre (default), anna, berta")
    ap.add_argument("--takes", type=int, default=3, help="moss: takes per line, the best is kept")
    ap.add_argument("--rate", type=float, default=1.0, help="piper: >1 slower, <1 faster (length_scale)")
    args = ap.parse_args()

    engine = args.engine
    if engine == "auto":
        engine = "moss" if MOSS_PY.exists() else "piper"
        if engine == "piper":
            print("tts: MOSS is not set up (tools/tts/setup.sh --moss), using Piper", file=sys.stderr)
    if engine == "moss":
        if not MOSS_PY.exists():
            sys.exit("tts: MOSS is not set up: tools/tts/setup.sh --moss")
        voice = TO_MOSS.get(args.voice, args.voice) or "male"
        cmd = [str(MOSS_PY), str(HERE / "moss_say.py"), args.lines, args.out, "--voice", voice, "--takes", str(args.takes)]
        sys.exit(subprocess.run(cmd).returncode)

    voice = TO_PIPER.get(args.voice, args.voice) or "imre"
    if voice not in ("imre", "anna", "berta"):
        sys.exit(f"tts: no Piper voice {voice} (imre, anna, berta)")
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    piper(json.loads(pathlib.Path(args.lines).read_text(encoding="utf-8")), out, voice, args.rate)


if __name__ == "__main__":
    main()
