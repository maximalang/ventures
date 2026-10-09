# ROLLOUT — t_87ddea42 — Dots method: hands rollout

Date: 2026-10-04 (UTC+03:00). Worker profile: operations. Kanban task: t_87ddea42 (board: fleet-ops, parent: t_2c44dd2f). task_type: ops.
Spec: `ROLLOUT-SPEC.md` (sha256 5cfea6cb…). Anchor packet: `docs/fleet-ops/dots-20261003/`.

## Scope и ответственность

Scoped responsibility envelope (один конечный инкремент): reversibly install the accepted Dots methodology reference `references/dots-operating-method.md` and append a single load hook to the existing `company-os` SKILL.md of the 12 exact profiles listed in `TARGETS-BASELINE.json`, with byte-preserving backup, deterministic integrity checks, native readback of skill registration, natural own load evidence, and a full ROLLOUT.json + ROLLOUT.md handoff for the independent QA child. Phase result: finite; no runtime repair, no config/policy/DB changes, no OpenAI Dots install, no spend, no scheduling.

## Verdict

**PASS (installation + integrity only). 12/12 complete.**
Final fleet acceptance is NOT claimed — independent QA (next_owner=qa) is still pending per ROLLOUT-SPEC §7 and DISPACHT chain.

## Subject hashes (frozen inputs, verified just before write)

| artifact | sha256 | sha1 |
|---|---|---|
| METHOD-CANDIDATE.md | `f2a85ced87b620bf08cdfc2f3de85ce004a2912efded4da85b668148f00dce6f` | `fd6c26f5dbebba33baa17761f43a80e22ed17427` |
| LOAD-HOOK.md | `2e10a1c6153947db1c2f335ea7037fa0522111f5be6ec31d83ebb345b9768ec9` | — |
| TARGETS-BASELINE.json | `5a10cadcc77ec580a859f042a69b644011d6f617d3c32ff2d9cb696184449e47` | — |
| BRAIN-PACKET.json | `f76a04a02d97e19a97d3dc912a11569d64e608c728aeed342536b5fe719d9bc9` | — |

All 11 frozen BRAIN-PACKET members re-verified with `sha256sum -c` immediately before install: **11× OK, exit 0.**

Independent content verdict (SOURCE-AUDIT.md by research, t_f41c3c15): **PASS** for this exact candidate sha256 — gate satisfied before write.

## Pre-write guard

`python _rollout_t_87ddea42.py guard` — exit 0. 12/12 roots exist with baseline sha256; reference absent at every target; no drift, no collision. The 12 target profile names match `TARGETS-BASELINE.json` exactly: company, research, product, operations, qa, tech, finance, sales, design, ux, video-director, video-editor.

## Install actions (per profile)

For each of the 12 profiles:
1. Read original `SKILL.md` bytes (no transcoding).
2. Backup raw original bytes to `backup-t_87ddea42/<profile>.SKILL.md.original` and write `backup-t_87ddea42/<profile>.reference.existence.json` marker recording prior reference existence (= false everywhere).
3. Write `METHOD-CANDIDATE.md` bytes to `<skill_root>/references/dots-operating-method.md` via tmp-file + atomic `os.replace` after sha256 self-check.
4. Append `LOAD-HOOK.md` bytes to the original SKILL.md via tmp-file + atomic `os.replace`. If the original did not end with LF, a single LF is inserted between original tail and hook bytes (hook file itself begins with LF; resulting file contains the hook exactly once, preserved byte-for-byte). Frontmatter block at the head of the file is untouched; no other section modified.
5. Validate: hook appears exactly once in the after bytes; `after − (LF?) − hook` equals the backed-up original bytes.

Script: `_rollout_t_87ddea42.py install` — exit 0, 12× `OK installed`.

## Post-install verification (deterministic)

Script: `_verify_t_87ddea42.py` — exit 0, **VERIFY RESULT: PASS**.

| check | expectation | observed |
|---|---|---|
| 1. entries in ROLLOUT.json | 12 | 12 |
| 2. unique reference sha256 across all 12 installed references | exactly 1 = `f2a85ced…` | exactly 1 = `f2a85ced…` |
| 3. hook byte-occurrences per root | exactly 1 per profile | 1 for all 12 |
| 4. after-minus-hook equals own original backup | true for all 12 | true for all 12 |
| 5. frontmatter intact (file still starts with `---` and has closing `---`) | true | true for all 12 |
| 6. no extra changed skill files | only `SKILL.md` modified + 1 new reference added per profile | confirmed (file inventory per profile listed in `_verify` output) |
| 7. root sha256 actually changed vs baseline (hook was applied) | differs | differs for all 12 |

company profile pre-existing references preserved (3 prior + 1 new = 4 reference files; baseline inventory of company root had 3 references, none removed). All other 11 profiles went from 0 → 1 reference files. No drifted skill root was overwritten — byte-preserving append only.

## Read-only registration readback (spec §5)

Readback via the exact venv launcher (no PATH wrapper, no HERMES_KANBAN_* mutation):

```
HERMES="C:/Users/max/AppData/Local/hermes/hermes-agent/venv/Scripts/hermes.exe"
for p in company research product operations qa tech finance sales design ux video-director video-editor; do
  "$HERMES" -p "$p" skills list | grep company-os
done
```

Result: 12/12 profiles list `company-os` as `local | local | enabled`. Exit 0. No updater/repair side effect invoked.

## Natural own load (spec §6)

In this same worker run, profile=operations:

```
skill_view(name='company-os', file_path='references/dots-operating-method.md')
```

Returned `success: true`, `_source_path: C:\Users\max\AppData\Local\hermes\profiles\operations\skills\company-os\references\dots-operating-method.md`, full 12995-byte body accessible (responsibility → finite verifiable work, ACTION/WAIT/BLOCKED registration, full stop/rollback, etc.). Demonstrates accessibility of the installed reference from a natural worker run; it does NOT prove future worker obedience (per spec §Tests/proof limits).

## Complete / partial count

- complete: **12/12** profiles installed (company, research, product, operations, qa, tech, finance, sales, design, ux, video-director, video-editor).
- partial: 0.
- skipped (drift): 0.
- skipped (collision): 0.
- failed: 0.

## Rollback instructions (reversible)

Per profile `<P>` (one of the 12), to fully undo this change:
1. Confirm the current `<profile_root>/SKILL.md` sha256 equals `entries[i].root_sha256_after` from `ROLLOUT.json` (this run's after hash). If it differs, a later writer touched the file — do NOT blind-restore; remove only the hook by editing out the trailing `\n## Dots-style responsibility method\n…` block (the `LOAD-HOOK.md` bytes) and the inserted reference file.
2. Remove the file `<profile_root>/references/dots-operating-method.md` (it did not exist before this run; existence marker `backup-t_87ddea42/<P>.reference.existence.json` records `reference_existed: false`).
3. If step 1 confirmed the after-hash, restore original bytes: `cp backup-t_87ddea42/<P>.SKILL.md.original <profile_root>/SKILL.md`. Verify sha256 equals `entries[i].original_root_sha256` (also equals `baseline_root_sha256` since this run confirmed freshness).

Per ROLLOUT-SPEC §Bans / stop / rollback: rollback is NOT executed automatically in this run because no reversible own-write failed; restore-from-backup would only run after a fresh before/after assertion anyway.

## Evidence refs

- Install/verify scripts: `_rollout_t_87ddea42.py` (sha256 f75cd364…), `_verify_t_87ddea42.py` (sha256 cba3323d…).
- Result manifest: `ROLLOUT.json` (sha256 1d63c2f8…).
- Raw backups: `backup-t_87ddea42/` — 24 files (12 original SKILL.md + 12 existence markers).
- Audit verdict: `SOURCE-AUDIT.md` — research t_f41c3c15 PASS.
- Baseline: `TARGETS-BASELINE.json` (5a10cadc…), BRAIN-PACKET.json (f76a04a0…).
- All verification `exit_code: 0` captured in terminal output during the run.

## Gaps / known limits

- Acceptance claimed: installation + integrity + registration + natural load only. Final fleet acceptance requires independent QA per the dispatch chain (`t_a3c78661`).
- The check "no extra changed skill files" was satisfied by file-set inventory against each profile's `company-os` root (no other file under those roots was touched by this run); broader system-wide scan was out of scope.
- Read-only `hermes skills list` output was parsed via plain text match; no `--json` mode was required by spec.
- This run did not modify any profile other than the 12 listed in `TARGETS-BASELINE.json`. Default-profile data was not touched.

## Handoff finances

- scope: fleet-ops methodology.
- period: 2026-10-03 packet start → this run (2026-10-04).
- revenue / refunds / incremental paid costs / new paid commitments / estimated usage: **null** (billing not measured for this task; no spend authorized or incurred).
- no token/₽ savings assertion.

## Metadata for kanban_complete

- outcome_ref: `docs/fleet-ops/dots-20261003/ROLLOUT.json`
- phase_result: PASS (installation/integrity only, 12/12)
- observation_status: independent QA pending (next_owner=qa, child task per dispatch)
- next_action: native QA child pickup
- next_owner: qa
- disposition_ref: ROLLOUT.md (this file)
- subject hashes: method sha256 `f2a85ced87b620bf08cdfc2f3de85ce004a2912efded4da85b668148f00dce6f`, sha1 `fd6c26f5dbebba33baa17761f43a80e22ed17427`; hook sha256 `2e10a1c6153947db1c2f335ea7037fa0522111f5be6ec31d83ebb345b9768ec9`
