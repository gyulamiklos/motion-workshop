"""Hungarian voiceover with Piper, one WAV per line, run on this machine (nothing leaves it).

Usage: tools/tts/.venv/bin/python tools/tts/say.py <lines.json> <out dir> [--voice imre|anna|berta] [--rate 1.0]
  lines.json: [{"id": "intro", "text": "..."}, ...]
Writes <out dir>/<id>.wav and <out dir>/voice.json ({"voice": ..., "lines": {id: {"file", "duration"}}}).
Set up the environment and voices once with tools/tts/setup.sh.
"""
import argparse
import json
import pathlib
import subprocess
import wave

from piper import PiperVoice
from piper.config import SynthesisConfig

HERE = pathlib.Path(__file__).resolve().parent
LOUDNESS = "loudnorm=I=-15:TP=-1.5:LRA=11"  # every voice line at the same speech loudness (EBU R128)


def normalize(path: pathlib.Path) -> None:
    """Bring a WAV to -15 LUFS with a -1.5 dBTP ceiling (ffmpeg loudnorm), in place: the film then lands near -14 LUFS."""
    tmp = path.with_suffix(".norm.wav")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(path), "-af", LOUDNESS, "-ar", "22050", str(tmp)], check=True)
    tmp.replace(path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lines")
    ap.add_argument("out")
    ap.add_argument("--voice", default="imre", choices=["imre", "anna", "berta"], help="imre: male (default); anna, berta: female")
    ap.add_argument("--rate", type=float, default=1.0, help=">1 slower, <1 faster (Piper length_scale)")
    args = ap.parse_args()

    lines = json.loads(pathlib.Path(args.lines).read_text(encoding="utf-8"))
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    voice = PiperVoice.load(str(HERE / "voices" / f"hu_HU-{args.voice}-medium.onnx"))
    syn = SynthesisConfig(length_scale=args.rate)

    manifest = {"voice": f"hu_HU-{args.voice}-medium", "lines": {}}
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


if __name__ == "__main__":
    main()
