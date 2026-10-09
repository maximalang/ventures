# Independent QA report — Dots method exact filesystem acceptance (t_a3c78661)

Date: 2026-10-04 (UTC+03:00). Reviewer profile: qa. task_type: review.
Scope: independent acceptance QA of the Dots-methodology rollout described by QA-SPEC.md. Reviewer is NOT the author/installer; subject files were not modified by this run. Effective evidence basis = original frozen reports + EVIDENCE-ERRATA.md (t_bf24d51d, sha256 e07e24518f29029102deb430f92f0c061512fff9e3ca5caeede222b551485c94).

## VERDICT: PASS (installation + integrity + methodology boundaries; scope = methodology/filesystem only)

All Q1–Q10 verified independently. Evidence-quality defects in the ORIGINAL reports are confirmed real and superseded by the errata (details in §Q8/Q9). Behavior benefit / new runtime functionality NOT measured (out of scope per Q10).

## Input integrity (independently re-hashed, `sha256sum`, exit 0)

- BRAIN-PACKET.json = f76a04a02d97e19a97d3dc912a11569d64e608c728aeed342536b5fe719d9bc9; 10/10 input_members byte-verified by own script `python _qa_check_t_a3c78661.py` (exit 0).
- METHOD-CANDIDATE.md = f2a85ced87b620bf08cdfc2f3de85ce004a2912efded4da85b668148f00dce6f, sha1 fd6c26f5dbebba33baa17761f43a80e22ed17427, 99 lines. LOAD-HOOK.md = 2e10a1c6153947db1c2f335ea7037fa0522111f5be6ec31d83ebb345b9768ec9.
- Report fingerprints match EVIDENCE-ERRATA-SPEC.md: SOURCE-AUDIT.md 9bc7d4a5…, ROLLOUT.md b01b0cdc…, ROLLOUT.json 1d63c2f8…, install script f75cd364…, verify script cba3323d…, AUTHOR-READBACK.json 68def383… (matches operator note receipt).
- Frozen sources: 13/13 files re-hashed OK (7 dots-core in SOURCES.json + 1 addendum core + 5 supporting; script `scratch/_qa_sources_check.py`, exit 0). normalized_text_sha256 == source_declared for 12/13 (addendum entry has no declared pair — recorded, not a mismatch). 2 unavailable sources honestly documented with both failed attempts (403).

## Q1 Targets — PASS
Own code count/dedupe of TARGETS-BASELINE.json: 12 targets, 12 unique profiles, no case-insensitive collisions of profile/root/reference paths; exact set {company, research, product, operations, qa, tech, finance, sales, design, ux, video-director, video-editor}; reference file exists at every exact path; ROLLOUT.json entries match baseline 1:1.

## Q2 References — PASS
Independently hashed all 12 installed references: every one equals f2a85ced… (byte-equal to frozen candidate); unique hash count = exactly 1.

## Q3 Hook — PASS
Exact LOAD-HOOK bytes appear exactly once in each of 12 SKILL.md roots; relative link target references/dots-operating-method.md exists in every skill root; root-minus-exact-hook == own backup raw bytes for all 12 (mode=direct, no inserted LF); backup sha == ROLLOUT original == baseline sha for all 12; frontmatter intact in all 12. No whole-root overwrite. backup-t_87ddea42/: 24 files (12 originals + 12 reference-existence markers, all markers say reference_existed=false; 12/12 originals match baseline hashes).

## Q4 Fresh state / no unrelated edits — PASS (bounded scope)
Fresh root hashes of all 12 targets equal producer after-manifest (root_sha256_after) — no concurrent drift at QA time. Default profile (C:\Users\max\AppData\Local\hermes\skills\company-os) untouched: no new reference, no hook. Proof scope: 12 company-os skill roots (inventories captured), captured manifests/receipts, scripts read. NOT a host-wide negative assertion (matches errata §9 bounding). No runtime/config/model/provider/pool/cron/policy/DB change within this scope.

## Q5 Loader registration — PASS
Executed for each of 12 profiles: `hermes -p <profile> skills list` (venv CLI, read-only). Result: rc=0 for all 12; `company-os` listed as enabled/local in every profile. No startup repair, no update, no worker pin changes.

## Q6 Natural load — PASS
In THIS qa run: `skill_view(name='company-os', file_path='references/dots-operating-method.md')` returned the full installed reference body from C:\Users\max\AppData\Local\hermes\profiles\qa\skills\company-os\references\dots-operating-method.md (sha f2a85ced…). Validates the load path for this run only.

## Q7 Semantic/scenario review — PASS (semantic, not live behavior tests)
14 scenarios against candidate clauses (all semantic review; only S0 was executed):
- S0 executed: natural load (see Q6).
- S1 research finding tries to publish → §2 «Находка сама по себе не разрешает send, publish, spend…» — boundary present. PASS.
- S2 draft message treated as sent → §2 «Draft ≠ send». PASS.
- S3 saved vault credentials imply new-sender rights → §2 «Наличие credentials ≠ scope grant» + §5 «Не подключай Slack/Teams/новый sender». PASS.
- S4 worker spawns/schedules its own subtree → §3 dispatcher ownership + «Не добавляй второго scheduler/writer». PASS.
- S5 "проверю завтра" prose → §4 requires saved schedule with timezone/expiry + registration ref. PASS.
- S6 promised event-driven wake without live capability → §4 «Не утверждай event-driven wake… без live capability evidence». PASS.
- S7 private deadline shared to team channel → §5 audience/disclosure boundary (matches frozen dots-tasks-memory.md lines 117–123: "sharing private details in a team channel still requires permission"). PASS.
- S8 device move assumed to carry session → §6 device/app/session separation. PASS.
- S9 chat request "stop everything and delete" → §7 no stop-all/root/delete grant; destructive rollback needs backup/scope gates. PASS.
- S10 executor DONE treated as outcome → §8 completion ≠ outcome; independent review + readback required. PASS.
- S11 financial handoff "cost=0" → §5 «Unknown = null + причина, не 0». PASS.
- S12 producer DONE auto-PASSes review → §3 «Producer DONE лишь освобождает review child; не делает review PASS». PASS.
- S13 candidate expected to carry local gate-marker rules → NOT in candidate by design; local fleet rules live outside it (this is exactly the false attribution corrected by errata §1–2). Documented, not a candidate defect.
- S14 methodology itself creates a scheduler → §4 «Расписание не создаётся этой reference». PASS.
No new cron/scheduler introduced by the packet (config/cron untouched per Q4 scope; registration is documentation-only).

## Q8 Source audit on effective evidence — PASS (with recorded original-report defects)
Frozen candidate audit basis: 8 core Dots sources (7 + 1 addendum) + 5 supporting all hash-verified on disk; unavailable sources honestly listed; chatgpt-permissions.md classified `codex-not-dots` (SOURCES.json line 162) and NOT used as Dots/Hermes config. Independently confirmed that METHOD-CANDIDATE.md contains NO «codex», «deny-first», «R0»/«R6», gate-marker or artifacts-receipt text (grep -i over frozen bytes; only "Dots"/"idempotent recovery" matches, lines 1/3/68/74/87/97/99). Therefore the ORIGINAL SOURCE-AUDIT.md lines 47/48/57/65 attributed to the candidate text that exists only in STUDY.md (lines 7, 11) / SOURCES.json / local fleet rules — false citations, real defect, superseded by errata §1–2 which I verified line-by-line against frozen bytes. Effective combined evidence is now accurate; no false source/availability claim remains effective.

## Q9 Deterministic integrity + rollback — PASS
Reproduced independently with own script `python _qa_check_t_a3c78661.py` (exit 0, 25/25 checks PASS: counts, hashes, hook, minus-hook==backup, frontmatter, fresh==after, inventory, default untouched) — installer/verify-script PASS not taken on faith; `_verify_t_87ddea42.py` (107 lines) read and its 7 checks match the executed assertions. Rollback: ORIGINAL ROLLOUT.md step 2 removes the reference without a freshness hash check (confirmed by direct reading — gap real); errata §8 supersedes the procedure: check BOTH current SKILL.md == root_sha256_after AND reference == f2a85ced…, STOP the target on mismatch, only a separately authorized rollback may edit out exactly hook bytes (2e10a1c6…) and candidate-hash reference — later writers preserved. Nothing was rolled back by QA.

## Q10 Handoff — this document
Worker does not accept itself: this reviewer (qa) is independent of author (research/operations). Integration accepted on Q1–Q9 all verified. Explicitly not measured: behavior benefit, agent obedience, runtime outcomes, host-wide negatives, zero-cost claims.

## Observations (non-blocking)
- OBS-1: errata §2 phrase «no text about … or idempotency» is slightly overbroad — candidate line 87 contains «idempotent recovery» (external-write recovery context, unrelated to artifacts receipts). No verdict affected.
- OBS-2: producer ROLLOUT.md contained 3 evidence defects (parent id, member count, financial phrasing) + rollback gap, all now superseded by errata; originals byte-unchanged (re-hashed during this run).

## Financial handoff
scope=fleet-ops methodology QA; period=2026-10-03 packet start → this run; source=task/tool receipts. revenue/refunds/incremental paid costs/estimated usage=null (not measured; receipts-only basis). new paid commitments=0 (no-commitment scope). No savings/free-inference claims.

## Receipts (commands + exit codes)
- python _qa_check_t_a3c78661.py → OVERALL PASS, EXIT=0 (QA-CHECK-t_a3c78661.json written; 25 checks)
- python scratch/_qa_sources_check.py → 13/13 OK, EXIT=0
- sha256sum (10 packet files) → EXIT=0, all match spec/manifests
- hermes -p <12 profiles> skills list → rc=0 ×12, company-os enabled ×12
- skill_view(company-os, references/dots-operating-method.md) → success, installed qa path
- sed -n spot checks sources/dots-controls.md 84–102, sources/dots-tasks-memory.md 106–124 → EXIT=0
- grep -in -E "codex|DoT|deny-first|R0|R6|idempoten" METHOD-CANDIDATE.md → only Dots/idempotent-recovery matches (no codex/deny-first/R0/R6)

Artifacts: QA.md (this file), QA.json, QA-CHECK-t_a3c78661.json, _qa_check_t_a3c78661.py.
