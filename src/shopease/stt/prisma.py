"""Audio to transcript with Gnani Prisma (prisma-v3.0, codemix, keywords).

Codemix keeps English words and names in Latin script and Tamil numbers as
words, which is what the parser reads. Keywords (customer names first, then
shop words) help Prisma spell names the way the ledger stores them.
"""

import io
import logging
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Protocol

from gnani.stt import GnaniSTTError

logger = logging.getLogger(__name__)

MODEL = "prisma-v3.0"
LANGUAGE = "ta-IN"
FORMAT = "codemix"
MAX_KEYWORDS = 200  # Prisma's limit
SHOP_WORDS = ("kadan", "baaki", "credit", "balance", "cancel", "undo", "reminder")
SAMPLE_RATE = 16000
FFMPEG_TIMEOUT_SECONDS = 30
_TRAILING_PUNCTUATION = ".?!,;:।"


class SpeechToTextError(Exception):
    """Audio could not be turned into a transcript."""


@dataclass(frozen=True)
class Transcript:
    text: str
    request_id: str | None
    is_truncated: bool = False


class _Client(Protocol):
    def transcribe(self, audio: BinaryIO, language_code: str, **options: Any) -> dict[str, Any]: ...


def clean_transcript(text: str) -> str:
    """Drop the sentence-final punctuation Prisma adds; keep inner commas."""
    return text.strip().rstrip(_TRAILING_PUNCTUATION).strip()


def keywords_for(names: Iterable[str]) -> tuple[str, ...]:
    """Customer names first, then shop words, without repeats, up to MAX_KEYWORDS."""
    words = (word.strip() for word in (*names, *SHOP_WORDS))
    return tuple(dict.fromkeys(word for word in words if word))[:MAX_KEYWORDS]


def to_wav(audio: bytes) -> bytes:
    """Any browser or phone recording to the 16 kHz mono WAV Prisma handles best.

    Goes through a temporary file, since m4a/mp4 cannot be read from a pipe.
    """
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise SpeechToTextError("ffmpeg is not installed; it is needed to convert audio")
    with tempfile.TemporaryDirectory() as folder:
        source, target = Path(folder) / "input", Path(folder) / "output.wav"
        source.write_bytes(audio)
        command = [ffmpeg, "-y", "-loglevel", "error", "-i", str(source),
                   "-ar", str(SAMPLE_RATE), "-ac", "1", str(target)]
        try:
            subprocess.run(command, check=True, capture_output=True, timeout=FFMPEG_TIMEOUT_SECONDS)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            stderr = getattr(exc, "stderr", b"") or b""
            logger.warning("ffmpeg failed: %s", stderr.decode(errors="replace").strip())
            raise SpeechToTextError("Could not convert the recording to WAV") from exc
        return target.read_bytes()


class PrismaSTT:
    def __init__(self, client: _Client | None = None, convert: Callable[[bytes], bytes] = to_wav) -> None:
        self._client = client
        self._convert = convert

    def _get_client(self) -> _Client:
        if self._client is None:
            from gnani.stt import GnaniSTTClient

            try:
                self._client = GnaniSTTClient()
            except Exception as exc:
                raise SpeechToTextError("Cannot start Prisma; set GNANI_API_KEY in .env") from exc
        return self._client

    def transcribe(self, audio: bytes, names: Iterable[str] = ()) -> Transcript:
        """Transcribe one recording. `names` are the shop's customer names."""
        if not audio:
            raise SpeechToTextError("The recording is empty")
        wav = io.BytesIO(self._convert(audio))
        wav.name = "command.wav"
        try:
            response = self._get_client().transcribe(
                wav, LANGUAGE, model=MODEL, format=FORMAT, keywords=list(keywords_for(names))
            )
        except GnaniSTTError as exc:
            logger.warning("Prisma request failed: %s", exc)
            raise SpeechToTextError("Prisma could not transcribe the recording") from exc
        return _transcript_from(response)


def _transcript_from(response: dict[str, Any]) -> Transcript:
    text = response.get("transcript")
    if not response.get("success") or not isinstance(text, str):
        logger.warning("Prisma returned no transcript: request_id=%s", response.get("request_id"))
        raise SpeechToTextError("Prisma returned no transcript")
    return Transcript(clean_transcript(text), response.get("request_id"), bool(response.get("truncated")))
