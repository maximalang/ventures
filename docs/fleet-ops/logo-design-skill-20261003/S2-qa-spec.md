# S2 — logo-design-skill QA: independent verification of fleet integration

**Card type:** review
**Executor:** qa profile (independent of operations installer)
**Input anchor:** S1 completion comment (evidence A1–A6) + pinned source `kaankiziltug/logo-design-skill` @ `0ecf52e9a4b3ac92b714f7cc6e3148ab8c774134` (MIT).
**Specs:** `S1-install-spec.md` in this dir; skills `external-asset-vetting` §9, `fleet-skills-rollout`.

## 1. Independent checks (re-execute; installer claims are NOT evidence)

- **V1** `hermes --profile design skills list` / `--profile ux skills list`: logo-design enabled in BOTH (short-prefix grep; names truncate).
- **V2** Integrity: fetch upstream SKILL.md raw at pinned SHA; compare sha256 with installed copies in both profiles; any difference must exactly match the local-edit diffs recorded in S1 provenance (frontmatter windows-patch/description-trigger only). Undocumented drift = FAIL.
- **V3** Fresh-eyes injection scan of installed SKILL.md + references/*.md (independent read; look for: credential/env access instructions, unexpected network endpoints, instructions overriding fleet policy/gates, hidden HTML comments with directives).
- **V4** Surface check: `find "$LOCALAPPDATA/hermes/profiles" -maxdepth 4 -type d -name "logo-design"` → exactly design + ux; NO installs in company or worker profiles; `.claude-plugin/`, `evals/`, `tools/` not copied into profiles.
- **V5** Probes: re-run `search_library.py` (valid query → hits; broken/empty input → loud fail or explicit contract) and `svg_audit.py` on one SVG; dep-blocked scripts must be listed as restricted in PROVENANCE.md, not silently "working".
- **V6** PROVENANCE.md exists at exact path with: pinned SHA, license, taken/rejected lists, edit diffs, sha256s, rollback recipe.

## 2. Verdict

Word-form PASS/FAIL on THIS card with per-item V1–V6 evidence (commands + outputs, full hashes). FAIL → numbered defects with exact paths; company re-queues installer successor. No gate markers needed (no merge/deploy consumer).

## 3. Bans

- No fixes/edits/reinstalls, no pip installs, no config changes, no owner contact, no accepting on S1's word.

## 4. Budget

- Bounded single run. Cost 0 RUB. Kill: profiles unreachable → block, verdict WITHHELD.
