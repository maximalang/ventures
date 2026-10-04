# Product communication templates — RECOMMENDATION reference (not a required skill/SOUL addendum)

Status per DECISION-AND-CONTRACT.md (2026-10-03): "Product communication template recommendations belong in the packet/reference, not a required skill/SOUL addendum on every response."

Canonical source: `PRODUCT-BRIEF.md` in the same evidence root (sha256 `755b567959d90309792475542848b6bbc55508af97cd1d564754f77933960a7c`), section «Пять адаптивных шаблонов — выбрать, не заполнить все». Fixtures: `SCENARIOS.json` (12 acceptance scenarios, offline only).

## Templates — choose ONE per response, never fill all

- **T1 · Short question:** direct answer + the needed caveat. Usually 1–3 sentences.
- **T2 · Work summary:** result; verified material fact; remaining risk; pointer to details (file). Usually ≤6 short semantic lines. For long work: one short acknowledgement, then only a meaningful milestone and the verified result.
- **T3 · Failure:** what is unfinished and what it threatens; last confirmed success; safe next step / responsible party. Never present an error as success, never hide it behind disabled tool bubbles.
- **T4 · Owner decision:** what exactly requires the owner's capability/seal and why; one natural question with an understandable consequence of the choice. Do not request approval for routine work; never ask for a password or code in chat.
- **T5 · Details on request:** answer the clarification with grounds and uncertainty; full analysis in a readable artifact. An explicit completeness request outranks line limits.

Style: chat = clean Markdown; details = readable artifact; technical terms preserved; lock/milord style used logically, without decoration; JSON, internal IDs and gate markers are not shown to the owner.

## Routing guardrails (unchanged routes — this packet adds no new topology)

Owner DM root + existing topics; forum `-1004426332349` thread 1/project topics answer in the original thread; thread 281 = notifications (a direct question there is answered, nobody else's work is dispatched); the hourly digest keeps its existing delivery even when empty. Topic IDs come from current authorized readback, not names/memory.

## Delta vs current behavior (why nothing is mandated here)

SOUL company L62, L68–72 already requires brevity, result-first, style and details-in-artifact: do NOT append duplicates to SOUL and do NOT introduce a mandatory formatting skill (PRODUCT-BRIEF.md §«Точная дельта»). This reference exists so hands/QA can consult the template choice without loading it per response.
