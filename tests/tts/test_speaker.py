from pathlib import Path

from shopease.tts import TimbreSpeaker


class FakeClient:
    def __init__(self) -> None:
        self.calls = 0

    def synthesize(self, text: str, *, voice: str, model: str, language: str) -> bytes:
        self.calls += 1
        assert voice == "Asmita"
        return b"audio"


def test_speaker_caches_by_voice_and_text(tmp_path: Path):
    client = FakeClient()
    speaker = TimbreSpeaker(client, tmp_path, "Asmita")
    assert speaker.speak("வணக்கம்") == speaker.speak("வணக்கம்")
    assert client.calls == 1
