# KadaiMate handoff

Last updated: 2026-11-03

## Current state

The Prisma test is done and the transcript format is chosen (see Prisma results).
No product code exists yet, and nothing is committed.
The next step is the implementation plan, then Deepak's review, then a test-first build.

## Context

- Entry for Gnani AI's Great Indian AI Internship Challenge.
- Deadline: Nov 10, 2026, 11:59 PM IST. Planned submission: Nov 9.
- Selection: verified engagement on the public demo post decides the shortlist; individual interviews decide offers.
- Deepak is Member A, in a team of two.
- Spec: `KadaiMate Problem Statement & Build Plan.pdf` in this folder. It is not an implementation plan.
- Online copy of the spec: https://claude.ai/artifact/Wj6jf5xBQAEyo3jJEsxB55

## Decisions

- Build Member A's scope only: Tanglish parser, intent schema, Prisma adapter, push-to-talk screen, a stub ledger and agreed interfaces for the teammate.
- Member B owns the ledger, name matching, smart confirmation, dashboard and Timbre integration.
- Process: implementation plan, Deepak's review, test-first build, final code review.
- Never add AI attribution to commits, PRs or docs.
- Timbre voice (provisional, changed Nov 3 from Vedika): **Asmita**, Tamil-script input (`_tamil`). Awaiting teammate confirmation. Keep the voice in one setting (`TIMBRE_VOICE`), never hard-coded, so a change costs only regenerating any saved prompt audio. Lock it before the demo post on Nov 7.
- Speech-to-text (Nov 2): **`prisma-v3.0`, `codemix` format, with `keywords`**, over REST. Reasons in Prisma results.

## Prisma results (Nov 2, 10 clips in Deepak's voice, iPhone Voice Memos)

Raw output: `spikes/output/prisma_results.json` (5 settings) and `spikes/output/prisma_codemix_keywords.json`.

- **codemix** writes Tamil words in Tamil script and English words in Latin script (`rice and oil packet`, `cancel`, `reminder`, `sugar`, `tea powder`). All 10 clips correct in meaning, every amount right.
- **verbatim**: same accuracy, but English words come out in Tamil script (`கேன்சல்`, `ரைஸ்`), so the parser would need both spellings. Rejected.
- **transliterate**: rejected. Clip 06 `adha cancel pannu` came back as the English sentence "Are they cancelled for me?", and 750 was mangled (`elluruthaiambathu`).
- **default model** (no model set): HTTP 504 gateway timeout on 6 of 10 clips. Unusable; always set `prisma-v3.0`.
- **keywords** fix names: `Kutty na Karthik` was right only with keywords (without: `Karthi`). Side effect: keyword names come out in Latin script (`Ravi அண்ணாவுக்கு`) but not always (`ரவிக்கு` in clips 04 and 10). Name matching must accept both scripts.
- **No confidence score** in any response. Fields are only `transcript`, `request_id`, `model`, timings and `detected_language_code`.
- Latency: about 0.3 to 0.4 s per clip.
- Parser input: Tamil number words in Tamil script, including spoken forms (`நூற்றம்பது` 150, `இருநூத்தி அஞ்சு` 205, `இருநூத்தம்பது` 250, `எழுநூற்றி ஐம்பது` 750, `ஒன்றரை` 1.5, `கால்` 0.25). Transcripts end with punctuation (`.` `?` `,`), so strip it.
- Credits: 4.9k of 5k after Timbre plus clip 01. Not rechecked after the full run (55 more calls).

## Next steps

1. Write the implementation plan for Member A's scope, built on the results above.
2. Deepak: review the plan.
3. Deepak: confirm Asmita (`_tamil`) with the teammate, and share the Prisma results with them (name matching needs both scripts).
4. Deepak: ask on Gnani's Discord whether a non-Gnani LLM is allowed, whether recording volunteers is allowed, and how regional judging works.
5. Update the spec (changes below).

## Spec changes to make

- Smart confirmation: no confidence score exists, so base confirmation on other signals (for example, unknown name, large amount, parse ambiguity).
- Push-to-talk: use REST with `prisma-v3.0`, `codemix`, `keywords` = known customer names plus shop words.
- Name matching: accept names in both Tamil and Latin script.
- Update the Tanglish and confidence items in "Verify first" with the results above.

## Open questions

- Credit cost per call: recheck the dashboard after the full run.
- Results are from one speaker. A second voice (the teammate) would show whether they hold.
- The other "Verify first" checks in the spec remain unconfirmed.

## Timeline from the spec

- Nov 4: Must features done.
- Nov 6: feature freeze.
- Nov 7: demo post live.
- Nov 9: submit.
