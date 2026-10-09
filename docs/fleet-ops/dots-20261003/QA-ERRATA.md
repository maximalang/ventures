# Supplemental independent QA — effective evidence after errata (t_a1ec6fed)

Date: 2026-10-04 (UTC+03:00). Reviewer profile: qa. task_type: review.
Scope: QA-ERRATA-SPEC.md acceptance only. This is a supplemental review of the COMBINED effective evidence (original frozen reports + EVIDENCE-ERRATA.md) and its compatibility with the original independent QA (t_a3c78661, QA.md/QA.json). It is NOT a re-run of that QA, not a waiver of any of its checks, and not fleet acceptance. Installer/verify scripts were read, never executed.

## VERDICT: PASS (supplemental; effective evidence after errata is factually corrected and consistent with the original QA PASS)

- Primary QA disposition: original t_a3c78661 PASS on Q1–Q10 STANDS; its own report enumerated 6 producer-report defects (all evidence/documentation-class) + 2 non-blocking observations, and no installation/load/integrity/security defect. Nothing blocking remained to waive.
- Errata EVIDENCE-ERRATA.md (sha256 e07e24518f29029102deb430f92f0c061512fff9e3ca5caeede222b551485c94, fresh re-hash this run) is factually accurate on every item I could test (see §Errata verification) EXCEPT two residual over-claims in its own lines 58/82 (E-1/E-2 below), which this verdict explicitly EXCLUDES from effective evidence. With those exclusions applied, all corrected defects are evidence/documentation-only — the class a supplemental PASS may cover per spec.
- This verdict does NOT assert behavior benefit, agent obedience, future runtime function, model independence of the original run, or host-wide negatives.

## Own receipts (this run, real exit codes)

- `python _qa_errata_check_t_a1ec6fed.py` → 31/31 checks PASS, OVERALL PASS, EXIT=0 (run twice this run: 29/29 before the operator note, 31/31 after adding G.E1/G.E2). Writes only QA-ERRATA-CHECK-t_a1ec6fed.json (original QA artifacts untouched: their script was re-derived, not re-run — it would have overwritten QA-CHECK-t_a3c78661.json).
- Checks cover: frozen subject hashes (candidate sha256 f2a85ced…, sha1 fd6c26f5…; hook 2e10a1c6…; BRAIN-PACKET f76a04a0… with 10/10 input_members byte-verified); original reports byte-unchanged (SOURCE-AUDIT 9bc7d4a5…, ROLLOUT.md b01b0cdc…, ROLLOUT.json 1d63c2f8…); errata hash; original QA.md 6567e7c9… / QA.json 7f45e721… match its completion metadata.
- Fresh readback all 12 targets (2026-10-04, this run): references byte-equal candidate (unique hash count = 1, f2a85ced…); hook exactly once per root; root-minus-hook == own backup (mode=direct ×12); backup sha == ROLLOUT original == baseline ×12; frontmatter intact ×12; fresh root sha256 == ROLLOUT root_sha256_after ×12 (no drift since install); default profile still untouched (no reference, no hook). Exact profile set = {company, research, product, operations, qa, tech, finance, sales, design, ux, video-director, video-editor}, no case-collisions; ROLLOUT.json entries match baseline 1:1.
- `sed -n 84,103p sources/dots-controls.md`, `sed -n 106,124p sources/dots-tasks-memory.md`, STUDY lines 5–12/32, SOURCES.json ~line 162, ROLLOUT rollback section, `_verify_t_87ddea42.py` lines 80–95 → EXIT=0 (direct locus verification below).
- Native task read t_87ddea42 (kanban_show, read-only): parents=[t_f41c3c15], children=[t_895a7d39, t_a3c78661, t_bf24d51d].
- Natural load in THIS run: `skill_view(name='company-os', file_path='references/dots-operating-method.md')` returned the full installed body from C:\Users\max\AppData\Local\hermes\profiles\qa\skills\company-os\references\dots-operating-method.md.

## Errata verification (all 9 spec items; defects re-captured programmatically + locus reads)

1. SA lines 47–48 false candidate attribution ([codex-not-dots]/DoT/deny-first): defect present in frozen SA; candidate contains no "codex"/"[codex-not-dots]"/"DoT"/"deny-first" (own grep over frozen bytes). Real loci confirmed: STUDY line 7 (Chain/Tree/Diagram-of-Thought exclusion) and line 11 verbatim "Codex permission profiles, не инструкция Dots…"; SOURCES.json ~line 162 `"class": "codex-not-dots"`. Errata §1 CORRECT.
2. SA lines 57/65 false R0/R6 citations: R0/R6 present in SA lines, absent from candidate; candidate line 34 confirmed verbatim = "Attention: <existing channel + threshold>; independent verifier: <profile>" (envelope template field). Errata §2 CORRECT.
3. Source mapping §3: contested ranges spot-verified against frozen sources: dots-controls.md "## Stop work" = lines 86–97, "## Delete your dot" heading = 101; dots-tasks-memory.md "### Across messaging channels" = 108–123 incl. the private-sharing permission sentence. Mapping stands. CORRECT.
4. STUDY line-pointer supersession: STUDY line 32 frozen text says "Controls, строки 86–105 … private sharing: 108–119"; actual frozen sources are 86–97 (+Delete 101) and 108–123. Errata §4 correction accurate; STUDY.md untouched (hash basis preserved). CORRECT.
5. ROLLOUT line 3 wrong parent t_2c44dd2f: wrong token confirmed present in frozen line 3; native read gives parent=t_f41c3c15. Errata §5 CORRECT (material for evidence-chain, cosmetic for file integrity).
6. ROLLOUT line 24 "11 members": claim confirmed present; BRAIN-PACKET.json input_members counted programmatically = 10, all 10 byte-verified this run. Count correction CORRECT — but see residual over-claim E-1 below on errata's own line 58.
7. ROLLOUT financial line: "no spend authorized or incurred" confirmed present in frozen §Handoff finances; null-values + unmeasured-cause framing and new paid commitments=0 confirmed. Errata §7 replacement accurate. CORRECT.
8. Rollback freshness gap: confirmed by DIRECT reading of frozen ROLLOUT §Rollback — step 1 checks SKILL.md vs after-hash, step 2 removes the reference citing only the existence marker; no reference-hash check before removal. Errata §8 hardening (check BOTH hashes, stop on mismatch, preserve later edits) is documentation-only; nothing rolled back. CORRECT. Honesty note: my checker flag `rollback_sec_checks_ref_hash` over-captured (the f2a85ced prefix appears in ROLLOUT's later Evidence-refs/Metadata sections, not in the rollback steps); the gap conclusion rests on the direct read, not on that flag.
9. "No extra changes" proof scope: `_verify_t_87ddea42.py` check 6 (lines 84–91, read) is a per-profile file-set inventory of the company-os roots — bounded, not host-wide. Bounding CORRECT — but see residual over-claim E-2 below on errata's own line 82.

## Residual errata over-claims (operator mid-run note, independently verified this run; checker checks G.E1/G.E2, EXIT=0)

- E-1 (errata §6, line 58): "10/10 re-verified OK … at install time per ROLLOUT's own claim pattern" asserts an install-time member verification that no captured receipt supports. Verified: ROLLOUT.json contains no member/preflight/brain receipt keys; the installer `_rollout_t_87ddea42.py` hashes exactly three fixed inputs (candidate sha256+sha1, hook, TARGETS baseline roots/reference) and never touches BRAIN-PACKET members; errata's own §6 (line 56) already noted the absence of the historical 11-file receipt. DISPOSITION: excluded from effective evidence. Only the actually executed 10/10 member checks are proven — the errata run's own (§0) and this supplemental run's. Unsupported historical timing stands corrected here; effective claim narrowed to "10 input_members verified now, twice, exit 0".
- E-2 (errata §9, line 82): "a file-set inventory … compared against TARGETS-BASELINE.json" overstates the baseline. Verified: TARGETS-BASELINE.json target entries carry only {profile, skill_root, root_path, baseline_sha256, new_reference_path, reference_exists} — root/reference paths and hashes, no before-inventory of supporting files; verify check 6 prints the current file set and performs no comparison (no ==/!=/diff in the check-6 code region). DISPOSITION: excluded from effective evidence. Proven scope is: inspected allowlisted script writes (12 SKILL.md appends + 12 new references) plus the CURRENT file set of the 12 company-os roots (current-state inventory, not before/after comparison); historical supporting-file hash coverage is absent and is reported as absent.
- Both are documentation-precision defects in the errata itself; installed subject bytes, all subject/reference/root hashes and the original QA's physical checks are unaffected. This supplemental verdict accepts the errata WITH these two exclusions applied, not as written. No changes to the installed subject were requested or made; author readback (AUTHOR-READBACK.json) remains author readback — not extended to independent QA, system-wide negatives, or future behavior.

## Defect inventory and dispositions (effective combined evidence)

| # | Original defect | Class | Disposition |
|---|---|---|---|
| 1 | SA 47/48 invented candidate attribution | evidence/documentation | Corrected by errata §1 (verified) — covered by this supplemental PASS |
| 2 | SA 57/65 nonexistent R0/R6 clauses | evidence/documentation | Corrected by errata §2 (verified) — covered |
| 3 | STUDY pointer wobble (2 ranges) | documentation pointer | Superseded by errata §4, STUDY frozen — covered |
| 4 | ROLLOUT wrong parent id | false reference | Corrected by errata §5, native-read verified — covered |
| 5 | ROLLOUT "11 members" | false count | Corrected by errata §6, recount=10 — covered |
| 6 | ROLLOUT "no spend incurred" | unsupported phrasing | Corrected by errata §7 — covered |
| 7 | Rollback lacks reference freshness check | procedure gap (documentation) | Hardened by errata §8; nothing executed — covered |
| 8 | "No extra changes" overbroad reading | scope statement | Bounded by errata §9, script read confirms — covered |

Remaining non-blocking: OBS-1 (errata §2 "no text about idempotency" slightly overbroad — candidate line 87 "Ambiguous external write требует readback/idempotent recovery…" confirmed this run; unrelated to artifacts receipts; no verdict affected). OBS-2 (originals byte-unchanged) re-confirmed this run by hash.

No installation/load/integrity/security defect, wrong lineage assertion, or missing test from the original Q1–Q10 remains unaddressed. Nothing waived.

## Serving lineage and proof limits

- This supplemental run: qa profile, model glm-5.3 (zai) — observed from own runtime header; configured label ≠ proof of served weights (no live probe attempted, per ban on synthetic inference).
- Original QA run reviewer profile = qa (same lane); its actual served model is NOT evidenced in its artifacts — recorded as a proof limit, not asserted. Author brain per packet = gpt-6.1-sol; reviewer-vs-author model independence of the original run is therefore correlated-not-demonstrated; this supplemental review (different model family from the author brain) adds an independent re-verification of the physical facts but does not retroactively attest the original run's model.
- Scope limits: methodology/filesystem only; 12 company-os skill roots + packet artifacts; no host-wide negative; behavior benefit and obedience NOT measured; installation/method accuracy ≠ future runtime benefit. Existing autocompany runtime repair remains a separate responsibility.

## Financial handoff

scope=fleet-ops methodology supplemental QA; period=2026-10-03 packet start → this run; source=task/tool receipts. revenue/refunds/incremental paid costs/estimated usage=null (not measured; receipts-only basis). new paid commitments=0 (no-commitment scope). No zero-cost or savings claim.

## Handoff metadata

- outcome_ref: docs/fleet-ops/dots-20261003/QA-ERRATA.md
- phase_result: PASS (supplemental; effective evidence after errata)
- primary_QA_disposition: original t_a3c78661 PASS stands; 6 producer-report defects + 2 observations enumerated; all defects documentation-class, corrected by verified errata
- excluded_unsupported_claims: E-1 errata line 58 "10/10 at install time" (no install-time member receipt exists in ROLLOUT.json or installer script — only the two actually executed 10/10 checks, errata run + this run); E-2 errata line 82 "inventory compared against TARGETS-BASELINE.json" (baseline has paths+hashes only, no supporting-file before-inventory; verify check 6 prints current set, compares nothing). Effective evidence = errata with these two claims excluded.
- errata_hash: sha256 e07e24518f29029102deb430f92f0c061512fff9e3ca5caeede222b551485c94
- exact_subject: METHOD-CANDIDATE.md sha256 f2a85ced…/sha1 fd6c26f5…; LOAD-HOOK.md 2e10a1c6…; BRAIN-PACKET.json f76a04a0… (all re-hashed this run)
- after-hashes fresh: 12/12 root_sha256_after match, 12/12 references == f2a85ced… (this run)
- test receipts: _qa_errata_check_t_a1ec6fed.py 29/29 EXIT=0; locus sed/awk reads EXIT=0; native kanban_show t_87ddea42; own skill_view natural load
- next_owner: company; disposition_ref: t_895a7d39
