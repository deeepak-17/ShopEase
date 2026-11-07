import shutil
import subprocess

import pytest
from gnani.stt import APIError

from shopease.stt import PrismaSTT, SpeechToTextError, Transcript, clean_transcript, keywords_for, to_wav
from shopease.stt.prisma import LANGUAGE, MAX_KEYWORDS, MODEL, SHOP_WORDS

WAV = b"RIFF fake wav"


class FakeClient:
    def __init__(self, response=None, error=None):
        self.response = response if response is not None else {"success": True, "request_id": "req_1", "transcript": "Ravi-க்கு 200 கடன்."}
        self.error = error
        self.calls = []

    def transcribe(self, audio, language_code, **options):
        self.calls.append({"audio": audio.read(), "name": audio.name, "language_code": language_code, **options})
        if self.error:
            raise self.error
        return self.response


def stt(client, convert=lambda audio: WAV):
    return PrismaSTT(client=client, convert=convert)


@pytest.mark.parametrize(
    "raw, clean",
    [
        ("Ravi அண்ணாவுக்கு நூற்றம்பது ரூபா கடன்.", "Ravi அண்ணாவுக்கு நூற்றம்பது ரூபா கடன்"),
        ("Ravi-க்கு எவ்வளவு பாக்கி இருக்கு?", "Ravi-க்கு எவ்வளவு பாக்கி இருக்கு"),
        ("  Ravi ku 200, Priya 100!  ", "Ravi ku 200, Priya 100"),
        ("2.5 கிலோ", "2.5 கிலோ"),
        ("", ""),
    ],
)
def test_clean_transcript_strips_only_trailing_punctuation(raw, clean):
    assert clean_transcript(raw) == clean


def test_keywords_put_names_first_then_shop_words_without_duplicates():
    words = keywords_for(["Ravi", "Priya", "Ravi", " ", "kadan"])
    assert words[:3] == ("Ravi", "Priya", "kadan")
    assert set(SHOP_WORDS) <= set(words)
    assert len(words) == len(set(words))


def test_keywords_are_capped_at_the_api_limit():
    names = [f"name{i}" for i in range(MAX_KEYWORDS + 50)]
    words = keywords_for(names)
    assert len(words) == MAX_KEYWORDS
    assert words[0] == "name0"


def test_transcribe_calls_prisma_v3_codemix_with_keywords():
    client = FakeClient()
    result = stt(client).transcribe(b"webm bytes", names=["Ravi"])
    assert result == Transcript("Ravi-க்கு 200 கடன்", "req_1")
    call = client.calls[0]
    assert call["audio"] == WAV
    assert call["name"].endswith(".wav")
    assert call["language_code"] == LANGUAGE == "ta-IN"
    assert call["model"] == MODEL == "prisma-v3.0"
    assert call["format"] == "codemix"
    assert call["keywords"][0] == "Ravi"


def test_transcribe_passes_the_original_audio_to_the_converter():
    seen = []
    stt(FakeClient(), convert=lambda audio: seen.append(audio) or WAV).transcribe(b"webm bytes")
    assert seen == [b"webm bytes"]


def test_empty_audio_is_rejected_before_calling_prisma():
    client = FakeClient()
    with pytest.raises(SpeechToTextError, match="empty"):
        stt(client).transcribe(b"")
    assert client.calls == []


def test_api_error_becomes_speech_to_text_error():
    client = FakeClient(error=APIError(500, "boom"))
    with pytest.raises(SpeechToTextError, match="Prisma"):
        stt(client).transcribe(b"audio")


@pytest.mark.parametrize("response", [{"success": False, "request_id": "r"}, {"success": True}, {}])
def test_response_without_transcript_is_an_error(response):
    with pytest.raises(SpeechToTextError):
        stt(FakeClient(response=response)).transcribe(b"audio")


def test_silence_gives_an_empty_transcript():
    response = {"success": True, "request_id": "r", "transcript": " . "}
    assert stt(FakeClient(response=response)).transcribe(b"audio").text == ""


def test_truncated_transcript_is_flagged():
    response = {"success": True, "request_id": "r", "transcript": "Ravi", "truncated": True}
    assert stt(FakeClient(response=response)).transcribe(b"audio").is_truncated is True


def test_to_wav_rejects_bytes_that_are_not_audio():
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not installed")
    with pytest.raises(SpeechToTextError, match="convert"):
        to_wav(b"not audio at all")


def test_to_wav_makes_16khz_mono_wav():
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not installed")
    tone = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=0.2:sample_rate=44100",
         "-ac", "2", "-f", "ogg", "pipe:1"],
        check=True, capture_output=True,
    ).stdout
    wav = to_wav(tone)
    assert wav[:4] == b"RIFF" and wav[8:12] == b"WAVE"
    channels = int.from_bytes(wav[22:24], "little")
    sample_rate = int.from_bytes(wav[24:28], "little")
    assert (channels, sample_rate) == (1, 16000)


def test_missing_ffmpeg_is_a_clear_error(monkeypatch):
    monkeypatch.setattr("shopease.stt.prisma.shutil.which", lambda name: None)
    with pytest.raises(SpeechToTextError, match="ffmpeg"):
        to_wav(b"audio")


def test_missing_api_key_is_a_clear_error(monkeypatch):
    def no_key():
        raise ValueError("api_key is required")

    monkeypatch.setattr("gnani.stt.GnaniSTTClient", no_key)
    with pytest.raises(SpeechToTextError, match="GNANI_API_KEY"):
        PrismaSTT(convert=lambda audio: WAV).transcribe(b"audio")
