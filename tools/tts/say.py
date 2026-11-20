"""Voiceover, one WAV per line, run on this machine (nothing leaves it).

Usage: tools/tts/.venv/bin/python tools/tts/say.py <lines.json> <out dir> [--lang en|hu] [--voice V] [--rate 1.0]
  lines.json: [{"id": "intro", "text": "..."}, ...]
Writes <out dir>/<id>.wav and <out dir>/voice.json ({"voice": ..., "lines": {id: {"file", "duration", "text"}}}).

Engines (set up once with tools/tts/setup.sh), picked by the film's language:
  en  Kokoro-82M: natural, about 10x real time on the CPU. Voices: michael (US male, default), george (UK male),
      heart (US female).
  hu  Piper: instant, but sounds mechanical. Voices: imre (male, default), anna, berta (female).
male and female pick the default voice of either language.
"""
import argparse
import json
import pathlib
import subprocess
import sys
import wave

HERE = pathlib.Path(__file__).resolve().parent
LOUDNESS = "loudnorm=I=-15:TP=-1.5:LRA=11"  # every voice line at the same speech loudness (EBU R128)
VOICES = {
    "en": {"michael": "am_michael", "george": "bm_george", "heart": "af_heart"},
    "hu": {"imre": "imre", "anna": "anna", "berta": "berta"},
}
DEFAULT = {"en": {"male": "michael", "female": "heart"}, "hu": {"male": "imre", "female": "anna"}}


def normalize(path: pathlib.Path) -> None:
    """Bring a WAV to -15 LUFS with a -1.5 dBTP ceiling (ffmpeg loudnorm), in place: the film then lands near -14 LUFS."""
    tmp = path.with_suffix(".norm.wav")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(path), "-af", LOUDNESS, "-ar", "24000", str(tmp)], check=True)
    tmp.replace(path)


def piper(voice_name: str, rate: float):
    from piper import PiperVoice
    from piper.config import SynthesisConfig

    voice = PiperVoice.load(str(HERE / "voices" / f"hu_HU-{voice_name}-medium.onnx"))
    syn = SynthesisConfig(length_scale=rate)

    def speak(text: str, path: pathlib.Path) -> None:
        with wave.open(str(path), "wb") as wav:
            voice.synthesize_wav(text, wav, syn_config=syn)
    return speak, f"piper:hu_HU-{voice_name}-medium"


def kokoro(voice_name: str, rate: float):
    import warnings

    import numpy as np
    import soundfile as sf
    from kokoro import KModel, KPipeline

    warnings.filterwarnings("ignore", module="torch")  # upstream deprecation noise on every run

    root = HERE / "voices" / "kokoro"
    model = KModel(repo_id="hexgrad/Kokoro-82M", config=str(root / "config.json"), model=str(root / "kokoro-v1_0.pth")).eval()
    pipe = KPipeline(lang_code=voice_name[0], repo_id="hexgrad/Kokoro-82M", model=model)  # a: US, b: UK English
    voice = str(root / f"{voice_name}.pt")

    def speak(text: str, path: pathlib.Path) -> None:
        audio = [r.audio.numpy() for r in pipe(text, voice=voice, speed=1 / rate)]
        sf.write(str(path), np.concatenate(audio), 24000)
    return speak, f"kokoro-82m:{voice_name}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lines")
    ap.add_argument("out")
    ap.add_argument("--lang", default="en", choices=["en", "hu"], help="the film's language: en (Kokoro, default) or hu (Piper)")
    ap.add_argument("--voice", default="male", help="male (default), female, or a voice name: en michael, george, heart; hu imre, anna, berta")
    ap.add_argument("--rate", type=float, default=1.0, help=">1 slower, <1 faster")
    args = ap.parse_args()

    name = DEFAULT[args.lang].get(args.voice, args.voice)
    if name not in VOICES[args.lang]:
        sys.exit(f"tts: no {args.lang} voice {args.voice} ({', '.join(VOICES[args.lang])}, male, female)")
    engine = kokoro if args.lang == "en" else piper
    try:
        speak, label = engine(VOICES[args.lang][name], args.rate)
    except (ImportError, FileNotFoundError) as e:
        sys.exit(f"tts: the {args.lang} voice is not set up ({e}): tools/tts/setup.sh")

    lines = json.loads(pathlib.Path(args.lines).read_text(encoding="utf-8"))
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"voice": label, "lines": {}}
    for line in lines:
        path = out / f"{line['id']}.wav"
        speak(line["text"], path)
        normalize(path)
        with wave.open(str(path), "rb") as wav:
            duration = wav.getnframes() / wav.getframerate()
        manifest["lines"][line["id"]] = {"file": path.name, "duration": round(duration, 3), "text": line["text"]}
        print(f"{line['id']}: {duration:.2f}s")
    (out / "voice.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
