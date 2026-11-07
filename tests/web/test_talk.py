"""Static checks on the push-to-talk page (no JS test runner in this repo)."""

import re
from pathlib import Path

import pytest

TALK = Path(__file__).parents[2] / "web" / "talk" / "index.html"


@pytest.fixture(scope="module")
def page() -> str:
    return TALK.read_text(encoding="utf-8")


def test_page_is_mobile_ready(page):
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in page
    assert "<title>" in page


def test_audio_is_posted_to_command_as_form_field(page):
    assert "fetch('/command'" in page
    assert "form.append('audio'" in page


def test_server_text_is_never_parsed_as_html(page):
    assert "innerHTML" not in page
    assert "insertAdjacentHTML" not in page
    assert "textContent" in page


def test_recording_stops_at_prismas_30_second_limit(page):
    assert re.search(r"MAX_RECORDING_MS\s*=\s*30_?000", page)


def test_hold_to_talk_works_with_touch_mouse_and_space_key(page):
    for event in ("pointerdown", "pointerup", "pointercancel", "keydown", "keyup"):
        assert f"'{event}'" in page


def test_mic_problems_are_explained(page):
    assert "isSecureContext" in page  # phones only allow the mic over https
    assert "NotAllowedError" in page


def test_reply_audio_and_transcript_are_shown(page):
    assert "audio_url" in page
    assert "transcript" in page
    assert "needs_confirmation" in page
