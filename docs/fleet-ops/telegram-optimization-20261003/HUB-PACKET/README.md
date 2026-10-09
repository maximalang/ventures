# HUB-PACKET — t_cef261ac (SOURCE-ONLY)

Compact hub candidates for exactly two company skills:

- `autonomous-ai-agents/hermes-agent`
- `fleet-ops/fleet-token-economy`

Nothing here is installed. Live skills were read-only anchors; this packet lives in the durable evidence root `docs/fleet-ops/telegram-optimization-20261003/HUB-PACKET/`.

## Contents

- `MANIFEST.json` — exact before/candidate file hashes (sha256), bytes, chars, combined hub reduction, rollback snapshot hashes, recorded corrections, routing-table addition.
- `INVARIANT-MAP.json` / `INVARIANT-MAP.md` — exhaustive section-level map: every safety invariant, owner directive and unique procedure → disposition + destination + verification markers; corrections C1a/C1b/C2 with exact before/after strings and evidence anchors.
- `candidates/<skill>/SKILL.md` — compact hub candidates (frontmatter and triggers byte-identical to the anchored source).
- `candidates/<skill>/references/*.md` — new topic-focused references (verbatim moves; corrections marked inline `UPDATE 2026-10-03`).
- `rollback/` — byte-exact prior hub snapshots (rollback candidate).
- `tests/test_hub_packet.py` — 17 acceptance tests: anchor integrity, candidate hashes, frontmatter/triggers, slice preservation, markers, reference resolution, selective retrieval, corrections applied, ≥60% reduction, packet hygiene, no-live-writes.
- `reference/COMMUNICATION-TEMPLATES.md` — product T1–T5 recommendation (NOT a required skill/SOUL addendum, per contract).
- `APPLY-ROLLBACK.md` — exact ops CLI apply/rollback lists + expected hashes.
- `STATIC-FOOTPRINT.md` — offline static before/proposed sizes (chars/bytes, NOT tokens).

## Verify (read-only)

```
python tests/test_hub_packet.py     # expect: Ran 17 tests ... OK, exit 0
```

Env `HUB_PACKET_SKILLS_ROOT` overrides the live anchor root (default: `C:/Users/max/AppData/Local/hermes/profiles/company/skills`).

## Result

Combined hub bytes 36,294 → 12,928 (−64.38%); chars 33,372 → 12,523 (−62.47%). Both ≥ 60%.

PRODUCT-BRIEF.md cited 33,078 source chars; measured anchor here = 33,372 chars / 36,294 bytes from the sha256-anchored files (294-char method delta noted in MANIFEST; reduction computed from measured bytes, per QA card).

Chain: tech t_cef261ac → qa t_d5e37e14 → bounded operations/company. No live config/SOUL/skill/cron/model/other-profile writes were made by this packet's author.
