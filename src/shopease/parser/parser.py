"""Entry point: a Prisma transcript in, a ParseResult out."""

from shopease.contracts import Intent, IntentType, ParseResult
from shopease.parser.clauses import split_clauses
from shopease.parser.intents import build_intent
from shopease.parser.tokens import Token, normalize, segments, tokenize


def parse(transcript: str) -> ParseResult:
    text = normalize(transcript)
    tokens: tuple[Token, ...] = sum((tokenize(part, i) for i, part in enumerate(segments(transcript))), ())
    built = tuple(build_intent(clause) for clause in split_clauses(tokens))
    if not built:
        return ParseResult(text, (Intent(IntentType.UNKNOWN),), is_ambiguous=True)
    return ParseResult(
        text,
        tuple(b.intent for b in built),
        is_ambiguous=any(b.is_ambiguous for b in built),
    )
