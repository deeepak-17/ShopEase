"""Throwaway spike: which Timbre Tamil voice sounds right for shop replies?

    .venv/bin/python spikes/timbre_spike.py

Writes one MP3 per voice and sentence style to spikes/output/timbre/.
"""

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv
from gnani.tts import AudioConfig, GnaniTTSClient

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "spikes" / "output" / "timbre"
MODEL = "timbre-v2.5"
LANGUAGE = "ta-IN"
TAMIL_VOICES = ("Asmita", "Trisha", "Brinda", "Vedika", "Noopur")
# Same reply in Tamil script and in Latin Tanglish: does Latin input read properly?
SENTENCES = {
    "tamil": "ரவி அண்ணாவுக்கு இருநூற்று ஐம்பது ரூபாய் சேர்த்துட்டேன். மொத்தம் அறுநூறு.",
    "latin": "Ravi anna ku 250 rupaa add pannitten. Total 600.",
}

logger = logging.getLogger("timbre_spike")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("gnani").setLevel(logging.WARNING)
    load_dotenv(ROOT / ".env")
    try:
        client = GnaniTTSClient()
    except Exception as exc:
        logger.error("Cannot start: %s\nPut your key in .env (see .env.example).", exc)
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config = AudioConfig(container="mp3", sample_rate=48000, bitrate="128k")
    failures = 0
    for voice in TAMIL_VOICES:
        for style, text in SENTENCES.items():
            target = OUTPUT_DIR / f"{voice}_{style}.mp3"
            try:
                audio = client.synthesize(
                    text, voice=voice, model=MODEL, language=LANGUAGE, audio_config=config
                )
            except Exception as exc:  # A spike should record every failure and keep going.
                logger.warning("%s/%s failed: %s", voice, style, exc)
                failures += 1
                continue
            target.write_bytes(audio)
            logger.info("Wrote %s", target)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
