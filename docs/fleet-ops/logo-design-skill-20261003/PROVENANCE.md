# PROVENANCE — logo-design-skill

## Source
- Repo: https://github.com/kaankiziltug/logo-design-skill
- Pinned SHA: `0ecf52e9a4b3ac92b714f7cc6e3148ab8c774134` (HEAD verified 2026-10-03 ~19:0x MSK)
- License: MIT (Copyright (c) 2026 kaankiziltug) — raw LICENSE verified by company.
- Upstream layout used: `skills/logo-design/` (SKILL.md + 14 references + assets/library + 9 scripts + 2 templates).
- Archive (codeload tarball @ pinned SHA): sha256 `ab8f36ea5fd46456645fa637d1107cc58f8b1d1ff6c0d8b88b60951caa4705c2` (6,455,726 bytes).

## What is taken (installed)
- `SKILL.md` — unchanged vs upstream (sha256 `65ec4bd58732e8cc11e244724e8666de78764b973f6d3b03b233904639cf47c6`).
- `references/` — all 14 `.md` files, unchanged.
- `templates/` — `brand-guidelines-template.md`, `presentation-spec.example.json`, unchanged.
- `assets/library/` — `catalog.json`, `classifications.json`, `gallery.html`, `stats.json`, `svg/` (1,436 files, ~1,400 SVG + json sidecars), unchanged.
- `scripts/` — all 9 `.py` (build_catalog, concept_sheet, export_variants, presentation_board, preview_sheet, render_png, search_library, svg_audit, svglib), unchanged.

## What is NOT taken (excluded per spec)
- `.claude-plugin/` — marketplace/plugin metadata, not part of skill surface.
- `.github/` — CI workflows, not part of skill surface.
- `docs/` — images for README, not part of skill surface.
- `evals/` — upstream eval fixtures, not part of skill surface.
- `tools/` — upstream packaging/smoke-test helpers (`package_skill.py`, `smoke_test.py`), not part of skill surface.
- `README.md`, `LICENSE`, `TRADEMARKS.md`, `.gitignore` — repo-level files, not copied into profiles.

## Restrictions noted
- `scripts/render_png.py` — requires a raster backend. On this fleet runtime python:
  - `cairosvg`: ABSENT (`ModuleNotFoundError`), pip install is BANNED (finance gate) → render_png's cairosvg backend unavailable.
  - `PIL`: present (12.1.1) but only used by render_png for favicon.ico repack, not SVG→PNG.
  - `rsvg-convert`, `inkscape`, `chrome/chromium`: ABSENT from PATH.
  - Consequence: PNG rendering path is effectively unavailable in-fleet; SVG work must be verified by opening `.svg` files directly or by `svg_audit.py` metrics. Marked RESTRICTED.
- `scripts/build_catalog.py` — maintainer-only per SKILL.md; not needed at runtime.
- `assets/library/gallery.html` — must NOT be opened/rendered in a browser (spec ban); file copied only for library completeness.
- Library SVGs are trademarks of their owners (TRADEMARKS.md) — reference/study only, never reuse as own artwork.

## Vet summary (A1)
- Prompt-injection / exfiltration scan of `SKILL.md`, all `references/*.md`, `scripts/*.py`, `templates/*`: no env/secret/credential reads, no network calls (`requests/urllib/httpx/aiohttp/fetch/curl/wget/socket` — none; only SVG-namespace `url(#...)` CSS refs and a documentation `https://{handle}.com` string in presentation_board mockup HTML). `subprocess` usage limited to local renderer binaries (`rsvg-convert`, `inkscape`, `chrome`, `qlmanage`, `taskkill`) in `render_png.py` only.
- Imports across all 9 scripts: stdlib-only + local `svglib`/`render_png` cross-imports; optional pip deps (`cairosvg`, `PIL`) imported lazily inside try-blocks with graceful fallback.
- Numeric-integrity / fail-loud probes:
  - `search_library.py --type monogram` → `unknown --type 'monogram'. Did you mean: abstract, combination, emblem, letterform, ...` (exit 0, loud refusal with suggestion).
  - `search_library.py --query "nosuchqueryzzz123"` → `0 match, showing 0` (explicit empty-result contract, no fabricated hits).
  - `svg_audit.py` on non-SVG garbage → `✖ could not parse: syntax error: line 1, column 0` (loud failure).
  - `svg_audit.py` on missing file → `✖ could not parse: [Errno 2] No such file or directory: ...` (loud failure).
  - `svg_audit.py` on real library SVG → metrics + score 97/100 (real work).
- No dangerous findings → verdict: CLEAN, install allowed.

## Local edits vs upstream
- NONE. SKILL.md frontmatter audit: `name: logo-design`; description starts `Professional logo and brand-mark design, from brief to produ…` — trigger survives 60-char catalog truncation (keyword "logo" present in first 60 chars). No `platforms:` field present → no Windows non-load pitfall. No description/frontmatter patch applied.

## Target profiles
- `design` — `C:/Users/max/AppData/Local/hermes/profiles/design/skills/creative/logo-design/`
- `ux` — `C:/Users/max/AppData/Local/hermes/profiles/ux/skills/creative/logo-design/`
Install method: manual copy from pinned-SHA tree (hub fetch not attempted; spec allows hub→manual, direct copy is equivalent and fully offline-deterministic).

## Installed-copy sha256 (A3)
- Upstream SKILL.md @ pinned SHA: `65ec4bd58732e8cc11e244724e8666de78764b973f6d3b03b233904639cf47c6`
- design copy SKILL.md: `65ec4bd58732e8cc11e244724e8666de78764b973f6d3b03b233904639cf47c6` — IDENTICAL
- ux copy SKILL.md: `65ec4bd58732e8cc11e244724e8666de78764b973f6d3b03b233904639cf47c6` — IDENTICAL

## Verification readbacks
- `hermes --profile design skills list | grep -i logo` → `│ logo-design │ creative │ local │ local │ enabled │`
- `hermes --profile ux skills list | grep -i logo` → `│ logo-design │ creative │ local │ local │ enabled │`
- Collision check `find "$LOCALAPPDATA/hermes/profiles" -maxdepth 4 -type d -name "logo-design"` → exactly 2 dirs (design, ux). No other profile carries this skill.

## Rollback recipe (per fleet-skills-rollout «Откат»)
1. `rm -rf "C:/Users/max/AppData/Local/hermes/profiles/design/skills/creative/logo-design"`
2. `rm -rf "C:/Users/max/AppData/Local/hermes/profiles/ux/skills/creative/logo-design"`
3. Readback: `find "$LOCALAPPDATA/hermes/profiles" -maxdepth 4 -type d -name "logo-design"` → 0 dirs; `hermes --profile <p> skills list | grep -i logo` → no rows.
4. Note rollback in this PROVENANCE.md (append section with timestamp + operator).
No approvals needed for rollback (per spec §4).

## Notes
- Smoke probes were run against the INSTALLED copy under `design` profile; `ux` copy is byte-identical (same sha256 on SKILL.md; whole tree copied from the same source in one operation).
- Any future upgrade: re-pin SHA, re-vet per `external-asset-vetting`, re-install both profiles, update this file.
