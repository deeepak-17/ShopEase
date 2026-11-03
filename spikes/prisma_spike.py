"""Throwaway spike: how does Prisma transcribe Tanglish shop commands?

Record clips/01.m4a ... clips/10.m4a by reading clips/prompts.csv, then run:

    .venv/bin/python spikes/prisma_spike.py            # all clips
    .venv/bin/python spikes/prisma_spike.py --limit 1  # one clip first

Each clip runs through every configuration in CONFIGS, so it costs
len(CONFIGS) API calls. Results go to spikes/output/prisma_results.json.
"""

import argparse
import csv
import json
import logging
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from gnani.stt import GnaniSTTClient

ROOT = Path(__file__).resolve().parent.parent
CLIPS_DIR = ROOT / "clips"
PROMPTS_FILE = CLIPS_DIR / "prompts.csv"
OUTPUT_FILE = ROOT / "spikes" / "output" / "prisma_results.json"
AUDIO_SUFFIXES = (".m4a", ".wav", ".mp3", ".aac", ".ogg", ".opus", ".caf")
LANGUAGE = "ta-IN"
V3 = "prisma-v3.0"
# Invented customer names and shop words, to see whether keyword hints help.
KEYWORDS = ("Ravi", "Priya", "Murugan", "Karthik", "Kutty", "kadan", "baaki")

logger = logging.getLogger("prisma_spike")


@dataclass(frozen=True)
class Config:
    label: str
    model: str | None
    format: str
    use_keywords: bool = False


CONFIGS = (
    Config("default_verbatim", None, "verbatim"),
    Config("v3_verbatim", V3, "verbatim"),
    Config("v3_codemix", V3, "codemix"),
    Config("v3_transliterate", V3, "transliterate"),
    Config("v3_transliterate_keywords", V3, "transliterate", use_keywords=True),
)


def load_prompts() -> dict[str, str]:
    with PROMPTS_FILE.open(encoding="utf-8") as handle:
        return {row["id"]: row["text"] for row in csv.DictReader(handle)}


def find_clip(clip_id: str) -> Path | None:
    for suffix in AUDIO_SUFFIXES:
        path = CLIPS_DIR / f"{clip_id}{suffix}"
        if path.exists():
            return path
    return None


def to_wav(source: Path, target: Path) -> None:
    """Convert to the 16 kHz mono WAV that the speech API handles best."""
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
         "-ar", "16000", "-ac", "1", str(target)],
        check=True,
    )


def transcribe(client: GnaniSTTClient, wav: Path, config: Config) -> dict[str, Any]:
    options: dict[str, Any] = {"format": config.format}
    if config.model:
        options["model"] = config.model
    if config.use_keywords:
        options["keywords"] = list(KEYWORDS)
    try:
        return client.transcribe(wav, language_code=LANGUAGE, **options)
    except Exception as exc:  # A spike should record every failure and keep going.
        logger.warning("%s failed: %s", config.label, exc)
        return {"error": f"{type(exc).__name__}: {exc}"}


def run_clip(client: GnaniSTTClient, clip_id: str, prompt: str, source: Path) -> dict[str, Any]:
    logger.info("\n%s  said: %s", clip_id, prompt)
    responses: dict[str, Any] = {}
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "clip.wav"
        to_wav(source, wav)
        for config in CONFIGS:
            response = transcribe(client, wav, config)
            responses[config.label] = response
            logger.info("  %-26s %s", config.label, response.get("transcript", response.get("error")))
    return {"id": clip_id, "prompt": prompt, "responses": responses}


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("gnani").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="only run this many clips")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    try:
        client = GnaniSTTClient()
    except Exception as exc:
        logger.error("Cannot start: %s\nPut your key in .env (see .env.example).", exc)
        return 1

    prompts = load_prompts()
    clips = [(cid, text, find_clip(cid)) for cid, text in prompts.items()]
    missing = [cid for cid, _, path in clips if path is None]
    if missing:
        logger.warning("No recording yet for: %s", ", ".join(missing))
    available = [clip for clip in clips if clip[2] is not None][: args.limit]
    if not available:
        logger.error("No clips found in %s. Record them from prompts.csv first.", CLIPS_DIR)
        return 1

    results = [run_clip(client, cid, text, path) for cid, text, path in available]
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("\nSaved %d clips to %s", len(results), OUTPUT_FILE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
