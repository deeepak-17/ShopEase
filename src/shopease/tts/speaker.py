"""Cached Timbre speaker wrapper with a testable client boundary."""

from hashlib import sha256
import logging
import os
from pathlib import Path
from typing import Protocol

from gnani.tts import GnaniTTSError

LOGGER = logging.getLogger(__name__)


class TTSClient(Protocol):
    def synthesize(self, text: str, *, voice: str, model: str, language: str) -> bytes: ...


class TimbreSpeaker:
    def __init__(
        self,
        client: TTSClient | None = None,
        cache_dir: str | Path = ".tts-cache",
        voice: str | None = None,
    ) -> None:
        self.client = client
        self.cache_dir = Path(cache_dir)
        self.voice = voice or os.environ.get("TIMBRE_VOICE")
        if not self.voice:
            raise ValueError("TIMBRE_VOICE is required")

    def speak(self, text: str) -> Path | None:
        cache_path = self.cache_dir / f"{sha256((self.voice + text).encode()).hexdigest()}.mp3"
        if cache_path.exists():
            return cache_path
        try:
            client = self.client or self._default_client()
            audio = client.synthesize(
                text, voice=self.voice, model="timbre-v2.5", language="ta-IN"
            )
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(audio)
            return cache_path
        except (GnaniTTSError, OSError):
            LOGGER.exception("Timbre synthesis failed")
            return None

    @staticmethod
    def _default_client() -> TTSClient:
        from gnani.tts import AudioConfig, GnaniTTSClient

        class ClientAdapter:
            def __init__(self) -> None:
                self.client = GnaniTTSClient()

            def synthesize(
                self, text: str, *, voice: str, model: str, language: str
            ) -> bytes:
                return self.client.synthesize(
                    text,
                    voice=voice,
                    model=model,
                    language=language,
                    audio_config=AudioConfig(
                        container="mp3", sample_rate=48000, bitrate="128k"
                    ),
                )

        return ClientAdapter()
