# S1 — logo-design-skill: vet + install into fleet (design, ux) + provenance

**Card type:** ops
**Executor:** operations profile
**Owner directive (03.10.2026):** «вот это надо интегрировать правильно» — image: slide of github.com/kaankiziltug/logo-design-skill.
**Pinned source:** `kaankiziltug/logo-design-skill` @ `0ecf52e9a4b3ac92b714f7cc6e3148ab8c774134` (HEAD verified 03.10 ~19:0x MSK). License: MIT — raw LICENSE verified by company (Copyright (c) 2026 kaankiziltug). Repo: 1655★, updated 03.10, skill layout `skills/logo-design/` (SKILL.md + 14 references + assets/library [catalog.json, classifications.json, gallery.html, stats.json, ~1400 SVG] + 9 python scripts + 2 templates).
**Protocols:** load skills `external-asset-vetting` (§5 autonomous cycle, §6 minimal surface, §9 skill-libraries) and `fleet-skills-rollout` (install, Windows pitfalls, verification, rollback).

## 1. Steps (in order)

1. **Content vet BEFORE any install.** Download the pinned-SHA tree (prefer full tarball via `git archive`/codeload zip at exact SHA into a scratch dir; record sha256 of the archive). Read SKILL.md + all 14 `references/*.md` + 9 `scripts/*.py` + templates: scan for prompt-injection/exfil patterns (instructions to read env/secrets, unexpected network calls, credential handling), and check scripts for numeric-integrity defects (§9: missing input must NOT silently become 0/empty-plausible output). Check script imports: stdlib-only vs pip deps (e.g. render_png.py). Verdict gate: any dangerous finding → STOP, do not install, block with exact quotes.
2. **Frontmatter audit.** SKILL.md `name:`/`description:`; `platforms:` field — if present without `windows`, plan post-install frontmatter patch (silent non-load pitfall). Description trigger must survive the 60-char catalog truncation — if the trigger is buried, patch description minimally (trigger first ≤~55 chars) and preserve upstream wording in a `> Extended triggers:` line under H1. Record EVERY local edit as a diff vs upstream.
3. **Install into `design` and `ux` profiles ONLY.** Try hub path first: `hermes skills search "logo design"` then `hermes --profile <p> skills install <source>/kaankiziltug/logo-design-skill/logo-design --yes`. On fetch failure: manual copy from the pinned-SHA tree into `<profile>/skills/<category>/logo-design/` — SKILL.md + references/ + assets/ + scripts/ + templates/ (do NOT install `.claude-plugin/`, `evals/`, `tools/`, `.github/` — not part of the skill surface). Remember: exit codes lie — verify by `skills list`; `HERMES_PROFILE` env does not route — only `--profile` flag; long installs → background terminal.
4. **Security-scan triage.** If skills-guard-v2 blocks: read the FULL report; content/fixture-class findings (docs/tests, e.g. evals.json strings) → `--force` with documented reason; dangerous verdict → reject, never force.
5. **Verify (evidence, not exit codes).** `hermes --profile design skills list` and `hermes --profile ux skills list` → skill present + enabled (grep short prefix `logo`, table truncates names). File listing + sha256 of installed SKILL.md in both profiles (must be identical). Name-collision check: `find "$LOCALAPPDATA/hermes/profiles" -maxdepth 4 -type d -name "logo-design"` → only design + ux; also check no other skill named `logo-design` in those profiles' registries.
6. **Smoke probes (fail-loud discipline).** Run `scripts/search_library.py` with a real query (expect hits) AND with empty/broken input (expect loud failure or explicit empty-result contract, not a plausible fake); run `svg_audit.py` on one library SVG. Use the fleet runtime python; if a script needs pip deps not present → mark it restricted in provenance (do NOT pip-install anything — finance gate).
7. **Provenance file.** Write `C:/Users/max/Desktop/all/ventures/docs/fleet-ops/logo-design-skill-20261003/PROVENANCE.md`: repo URL + pinned SHA + license; what is taken (method + references + SVG library) vs rejected/restricted (list: .claude-plugin, evals, tools/, gallery.html usage note, any dep-blocked scripts); local-edit diffs; target profiles; installed-copy sha256s; rollback recipe (file-level removal per fleet-skills-rollout «Откат» + readback).

## 2. Acceptance (all in completion comment)

- A1 injection/numeric vet report: clean OR documented false-positives with quotes; dangerous → card blocks instead.
- A2 enabled readback for design AND ux (`skills list` excerpts).
- A3 sha256: archive, installed SKILL.md ×2 profiles (identical), match with upstream raw at pinned SHA (documented edits listed as diffs).
- A4 collision check output (only 2 dirs).
- A5 probe outputs (valid + broken input).
- A6 PROVENANCE.md path + section list.

## 3. Bans

- No installs into company or any other profile; no other skills installed "while at it"; no pip installs; no fleet config/model changes; do not open/render gallery.html in a browser; do not use library SVGs as own artwork (TRADEMARKS.md — reference only); no owner contact.

## 4. Budget / rollback

- Bounded run; ≤2 install attempts per profile (hub → manual). Cost 0 RUB. Rollback: remove installed dirs in design/ux, readback grep=0, note in PROVENANCE.md; no approvals needed.
