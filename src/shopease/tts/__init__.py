"""Gnani Timbre text to speech: Tamil replies and reminder voice notes (voice from TIMBRE_VOICE).

Owner: Member B
"""

from .speaker import TimbreSpeaker
from .templates import (
    balance_reply,
    credit_reply,
    daily_total_reply,
    payment_reply,
    reminder_reply,
    undo_reply,
)

__all__ = [
    "TimbreSpeaker", "balance_reply", "credit_reply", "daily_total_reply",
    "payment_reply", "reminder_reply", "undo_reply",
]
