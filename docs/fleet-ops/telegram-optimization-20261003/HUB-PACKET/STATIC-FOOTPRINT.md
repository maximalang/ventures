# STATIC-FOOTPRINT — offline before/proposed (chars and bytes, NOT tokens)

Static offline computation from anchored file bytes; no runtime inference, no token claims.
Chars/bytes ≠ tokens; usage/quota ≠ invoice (DECISION-AND-CONTRACT.md).

## Per-hub skill_view injection (hub body loaded on skill_view)

| Hub | before bytes | before chars | candidate bytes | candidate chars | bytes reduction |
|---|---|---|---|---|---|
| hermes-agent | 13580 | 13494 | 6559 | 6515 | 51.7% |
| fleet-token-economy | 22714 | 19878 | 6369 | 6008 | 71.96% |
| **combined** | **36294** | **33372** | **12928** | **12523** | **64.38%** |

## System prompt / skills index (per prompt, every session)

- Skills-index line per skill is UNCHANGED: frontmatter name/description are byte-identical, so the
  always-injected index contribution (6 + name + 2 + min(desc,60) bytes) does not change.
- System prompt baseline (prompt-baseline.json): system 47,291 chars / 57,806 bytes — untouched by this packet.
- Hubs are NOT injected into the system prompt; they load only on skill_view, so the saving is per-load,
  not per-prompt. Every load previously injected the full monolith; now it injects only the compact hub.

## Worst case: hub + ALL references loaded (honest upper bound)

- hermes-agent refs before: 140140 bytes; new refs added: 9790 bytes;
  worst-case total grows by pointer/header overhead only (content moved, not duplicated except short hub pointers).
- fleet-token-economy refs before: 15536 bytes; new refs added: 24091 bytes.
- Typical load is hub-only (refs are on-demand via routing table) — that is where the reduction lands.
- No imaginary runtime savings are claimed; natural-run measurement is acceptance step 6 of the contract.
