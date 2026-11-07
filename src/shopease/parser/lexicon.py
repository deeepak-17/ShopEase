"""Word lists the parser recognises. Data only, all casefolded.

Tamil words are in Tamil script as Prisma's codemix output writes them;
English words in Latin script. Triggers are stems, matched as prefixes.
"""

from types import MappingProxyType

from shopease.contracts import IntentType

HONORIFICS = frozenset({
    "அண்ணா", "அண்ணன்", "அக்கா", "தம்பி", "அம்மா", "ஐயா", "சார்",
    "anna", "akka", "thambi", "amma", "sir", "madam",
})

FILLERS = frozenset({
    "அது", "அதை", "adhu", "adha", "sorry", "இருக்கு", "irukku", "பண்ணு",
    "pannu", "அனுப்பு", "anuppu", "இன்னைக்கு", "inniku", "எவ்வளவு",
    "எவ்வளோ", "எவ்ளோ", "evlo", "ok",
})

UNITS = MappingProxyType({
    "கிலோ": "kilo", "kilo": "kilo", "kg": "kilo",
    "கிராம்": "gram", "gram": "gram",
    "லிட்டர்": "litre", "litre": "litre", "liter": "litre",
})

CURRENCY = frozenset({"ரூபா", "ரூபாய்", "rupa", "rupees", "rs", "₹"})

ITEM_JOINERS = frozenset({"and", "உம்"})

CORRECTION_WORDS = frozenset({"இல்ல", "illa", "இல்லை"})

ALIAS_WORDS = frozenset({"na", "னா", "நா"})

DATIVE_WORDS = frozenset({"ku", "kku"})

TRIGGERS: tuple[tuple[IntentType, tuple[str, ...]], ...] = (
    (IntentType.ADD_CREDIT, ("கடன", "kadan", "credit", "udhaar")),
    (IntentType.RECORD_PAYMENT, ("கொடுத்", "குடுத்", "kodut", "kudut", "paid")),
    (IntentType.BALANCE_QUERY, ("பாக்கி", "baaki", "balance", "பேலன்ஸ்")),
    (IntentType.UNDO, ("cancel", "கேன்சல்", "undo", "delete")),
    (IntentType.DAILY_TOTAL, ("வியாபாரம்", "vyaapaaram", "sales")),
    (IntentType.SEND_REMINDER, ("reminder", "ரிமைண்டர்")),
)
