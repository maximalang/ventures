# EVIDENCE-ERRATA — Dots packet evidence corrections (t_bf24d51d)

Date: 2026-10-04 (UTC+03:00). Author: research. task_type: research.
Scope: factual correction of false assertions in the completed reports SOURCE-AUDIT.md and ROLLOUT.md, against the frozen inputs of `docs/fleet-ops/dots-20261003/`. Original reports remain byte-unchanged; this errata supersedes ONLY the assertions explicitly listed below. This is a content correction document — not a reinstall, not a QA gate, not fleet acceptance.

## 0. Input integrity re-verified for this errata (exit 0)

- All frozen fingerprints from EVIDENCE-ERRATA-SPEC.md re-hashed and matched: SOURCE-AUDIT.md 9bc7d4a5…, ROLLOUT.md b01b0cdc…, ROLLOUT.json 1d63c2f8…, install script f75cd364…, verify script cba3323d…, AUTHOR-READBACK.json 68def383…, BRAIN-PACKET.json f76a04a0…, METHOD-CANDIDATE.md f2a85ced…/sha1 fd6c26f5…, STUDY.md b466f497… (sha256sum, exit 0).
- BRAIN-PACKET.json input_members re-verified byte-for-byte by a dedicated read-only script: 10/10 OK, exit 0 (script `scratch/_brain_check.py`).
- Task relationships read natively: t_87ddea42 parents=[t_f41c3c15], children=[t_895a7d39, t_a3c78661, t_bf24d51d]; t_f41c3c15 receipt verdict=PASS content/source accuracy. AUTHOR-READBACK.json self-describes as "direct filesystem readback; not independent QA or behavior proof" — author (company) readback, treated as such.

## 1. SOURCE-AUDIT.md lines 47–48 — invented candidate-quote attribution (FALSE attribution)

Original assertion (SOURCE-AUDIT.md, hash 9bc7d4a5…, lines 47–48): that the candidate "правильно маркирует его «[codex-not-dots]… Do not apply to Dots or Hermes» и использует только для deny-first/least-privilege/blast-radius модели" and that STUDY frames DoT.

Observation from actual inputs: METHOD-CANDIDATE.md (99 lines, hash f2a85ced…) contains NO string "codex", "[codex-not-dots]", "DoT", or "deny-first" anywhere (grep -i over the exact frozen bytes). Candidate line 3 only states the method is "derived from public OpenAI Dots guides… не установленный OpenAI Dots"; candidate line 97 lists adaptation-basis URLs; candidate line 74 says "не подключай OpenAI Dots к личному компьютеру". That is the whole codex/DoT-related content. The "codex-not-dots" classification exists ONLY as SOURCES.json line 162 (`"class": "codex-not-dots"`) — a company-side manifest label, not a candidate quote. The correct scoping of chatgpt-permissions.md as Codex-permission-profiles (not Dots, not Fleet Policy) is STUDY.md line 11 verbatim; the exclusion of Chain/Tree/Diagram-of-Thought framing is STUDY.md line 7 verbatim.

Replacement authoritative statement: the DoT-vs-Dots framing and the codex-not-dots scoping are properties of STUDY.md (lines 7 and 11) and of the SOURCES.json manifest label — not of the candidate. The candidate contains no such sections or quotes. Remove the quoted candidate attribution from effective evidence; the underlying boundary claim remains supported by STUDY.md line 11 and SOURCES.json line 162 + line 225 note.

Effect on rollout acceptance: none for the installed bytes (the candidate's actual content never imported Codex permission profiles — there is nothing to import). The PASS verdicts of t_f41c3c15 are unaffected in substance; only the cited location of the framing is corrected.

## 2. SOURCE-AUDIT.md lines 57 and 65 — nonexistent candidate clauses "R0"/"R6" (FALSE citation)

Original assertion (line 57): 'R0: «research owns no fleet-policy gate… never write gate:<name>=pass markers» — помечено как fleet context' attributed to the candidate. Original assertion (line 65): 'Кандидат ссылается на «Hermes deliverables artifacts receipt idempotency» (R6, строка 34)'.

Observation from actual inputs: the candidate contains no "R0" or "R6" labels and no text about fleet-policy gate markers, gate authorship, artifacts receipts, or idempotency (grep over frozen bytes). Candidate line 34 is verbatim: `Attention: <existing channel + threshold>; independent verifier: <profile>` — a field of the compact handoff template, not an artifacts-receipt clause. The "research owns no gate / never write gate markers" rule is a real LOCAL fleet convention (fleet-policy plugin GATE_AUTHORS, company-os skill lessons), not a candidate clause and not a Dots-source claim.

Replacement authoritative statement: candidate line 34 is the envelope's Attention/independent-verifier template field. The gate-marker rule and the artifacts-receipt mechanics are real local fleet rules (fleet-policy plugin; hermes-kanban.md lines 103–110, 135 per SOURCE-AUDIT's own mapping) but are NOT stated in the candidate; any citation of the candidate for them is removed. Do not preserve hallucinated citations because the intent is sensible.

Effect on rollout acceptance: none for installed bytes. These were audit-side citations, not installation inputs. Effective evidence now cites the real locations only.

## 3. Source mapping validity

The 16-claim fact→URL mapping in SOURCE-AUDIT.md §2 stands: spot re-verification of the contested line ranges against frozen sources confirms dots-controls.md "## Stop work" at 86–97 and "## Delete your dot" at 101; dots-tasks-memory.md "### Across messaging channels" at 108–123. Corrections in this errata are limited to the two attribution defects above and the pointer supersession in §4. No wholesale re-fetch performed; frozen hashes reused.

## 4. STUDY.md line-pointer supersession (frozen STUDY preserved)

STUDY.md (hash b466f497…) is NOT modified. The following pointer inaccuracies are superseded by reference here, per spec:
- STUDY line 32 "Controls, строки 86–105" → actual frozen dots-controls.md: "## Stop work" occupies lines 86–97; lines 99–105 are "## Delete your dot" (heading at 101). Both sections are stop-relevant; the combined read "86–105 (stop work + delete)" is the accurate form.
- STUDY line 32 "Tasks and memory 108–119" → actual frozen dots-tasks-memory.md: "### Across messaging channels" occupies lines 108–123.

## 5. ROLLOUT.md line 3 — wrong parent task id (FALSE reference)

Original assertion (ROLLOUT.md, hash b01b0cdc…, line 3): "Kanban task: t_87ddea42 (board: fleet-ops, parent: t_2c44dd2f)".

Observation: native task read of t_87ddea42 returns parents=["t_f41c3c15"], children=["t_895a7d39","t_a3c78661","t_bf24d51d"], created_by=company, with the company go-decision comment naming t_f41c3c15 the conditional authority and t_a3c78661/t_895a7d39 the downstream. t_2c44dd2f does not appear in this chain; it is not looked up or normalized as an authority — it is simply a wrong token.

Replacement authoritative statement: ROLLOUT line 3 parent reference is superseded by parent=t_f41c3c15 (the SOURCE-AUDIT producer and conditional authority per the company decision comment on t_87ddea42).

Effect on rollout acceptance: cosmetic for file integrity, material for evidence-chain accuracy — any consumer tracing provenance via ROLLOUT line 3 would have followed a wrong link.

## 6. ROLLOUT.md line 24 — "All 11 frozen BRAIN-PACKET members" (FALSE count)

Original assertion (line 24): "All 11 frozen BRAIN-PACKET members re-verified with `sha256sum -c` immediately before install: 11× OK, exit 0."

Observation: BRAIN-PACKET.json contains exactly 10 input_members (counted programmatically: STUDY.md, METHOD-CANDIDATE.md, LOAD-HOOK.md, SOURCE-AUDIT-SPEC.md, ROLLOUT-SPEC.md, QA-SPEC.md, CONSUMER-SPEC.md, SOURCES.json, SOURCES-ADDENDUM.json, TARGETS-BASELINE.json). Re-run now: 10/10 OK, exit 0. The install script `_rollout_t_87ddea42.py` itself hashes only 2 packet members (METHOD-CANDIDATE.md, LOAD-HOOK.md) plus TARGETS-BASELINE.json — no 11-member check exists in the captured scripts. "11" is reachable only by counting the BRAIN-PACKET.json file itself in addition to its 10 members, and no command receipt in ROLLOUT.json/ROLLOUT.md shows such an 11-file check.

Replacement authoritative statement: BRAIN-PACKET.json has 10 input_members; 10/10 re-verified OK (exit 0) both at install time per ROLLOUT's own claim pattern and again now. The "11 members / 11× OK" phrasing is superseded; if an 11-file check including the packet file itself was intended, no receipt supports it.

Effect on rollout acceptance: integrity conclusion unchanged (all actual members verified); only the count is corrected.

## 7. ROLLOUT.md line 119 — financial line (partially unsupported phrasing)

Original assertion (line 119): "revenue / refunds / incremental paid costs / new paid commitments / estimated usage: null (billing not measured for this task; no spend authorized or incurred)."

Observation: the parenthetical "no spend… incurred" is an affirmative claim about all spend, which cannot be evidenced without billing data — the run's own evidence basis is task/tool receipts only. The null values themselves and "billing not measured" are correct and match the company decision comment ("revenue/refunds/incremental paid costs/estimated inference costs=null, billing/outcomes not measured. No claim of zero inference cost.").

Replacement authoritative statement: confirmed — revenue=null, refunds=null, incremental paid costs=null, estimated usage=null, all with cause "billing not measured for this task; receipts-only evidence basis". Confirmed — new paid commitments=0, evidenced by the no-commitment scope of the company go-decision (explicit ban on new paid plans/commitments). Superseded — "no spend authorized or incurred" as phrased: replace with "no spend authorized in this scope; incurred inference cost unmeasured (no billing read); absence of a new paid order is not evidence of zero inference cost".

Effect on rollout acceptance: none; financial posture unchanged, wording aligned with the decision comment.

## 8. ROLLOUT.md rollback instructions — hash-check gap (documentation only; no rollback executed)

Observation: ROLLOUT.md §Rollback step 1 checks current SKILL.md against `root_sha256_after`; step 2 removes `references/dots-operating-method.md` with only an existence-marker check; step 3 restores bytes and verifies against the original hash. Gap: before removing the reference file, its current hash is not compared against this operation's after-hash (f2a85ced…). If a later, unrelated edit changed the reference, blind removal would delete someone else's later work.

Replacement authoritative statement (supersedes the rollback procedure text for any future use): before any removal/restore, check BOTH (a) current SKILL.md sha256 == entries[i].root_sha256_after AND (b) current references/dots-operating-method.md sha256 == f2a85ced87b620bf08cdfc2f3de85ce004a2912efded4da85b668148f00dce6f. If either differs, STOP that target — remove nothing; only a separately authorized rollback may then edit out exactly the LOAD-HOOK.md bytes (sha256 2e10a1c6…) and the candidate-hash reference, preserving later edits. This errata documents the procedure only; nothing was rolled back, no profile file was touched.

Effect on rollout acceptance: none for the install verdict; hardens the documented reversal path.

## 9. "No extra changes" — proof scope statement

ROLLOUT.md verification check 6 ("no extra changed skill files") is, per the verify script `_verify_t_87ddea42.py` lines 86–91 (read, not rerun), a file-set inventory of each of the 12 profiles' company-os skill roots compared against TARGETS-BASELINE.json — i.e., proof scope = allowlisted writes (12 SKILL.md appends + 12 new reference files) plus captured inventories/receipts within the 12 company-os roots. It is NOT a host-wide negative assertion: no evidence was captured about files outside those roots, other profiles, or the default profile beyond "not touched by this run" (ROLLOUT.md line 113 is consistent with this scope). Effective evidence reads check 6 exactly as that bounded inventory, nothing broader.

## 10. Content verdict on the effective combined evidence

VERDICT: PASS — installation and integrity evidence stands after corrections.

Basis: 10/10 BRAIN-PACKET members verified (exit 0, re-run now); install/verify scripts (read, not rerun) implement the byte-preserving guard/backup/install/verify flow that ROLLOUT.json records as 12/12 installed, 0 failed; SOURCE-AUDIT's 16-claim mapping is CONFIRMED against frozen sources with only the pointer supersessions above; AUTHOR-READBACK.json is author readback and is not counted as independent QA.

Owner of the two false attributions (items 1–2): research (t_f41c3c15, SOURCE-AUDIT.md). Owner of the false references/counts (items 5–7): operations (t_87ddea42, ROLLOUT.md). These are evidence-quality defects, not cosmetic labels, and are corrected here without relabeling.

Explicitly NOT asserted: final fleet acceptance (independent QA t_a3c78661 pending), worker obedience, zero inference cost, host-wide no-extra-changes.

## 11. Financial scope of this errata run

scope: fleet-ops methodology evidence correction. period: 2026-10-03 packet start → this run (2026-10-04). source: native task/tool receipts; no billing API read. revenue / refunds / incremental paid costs / estimated usage: null (cause: not measured; receipts-only basis). new paid commitments: 0 (no-commitment scope of this task). No claim of free inference or measured savings.

## 12. Handoff

outcome_ref: docs/fleet-ops/dots-20261003/EVIDENCE-ERRATA.md
phase_result: PASS (evidence corrected; installation/integrity verdict unaffected)
next_owner: qa (t_a3c78661), then company (t_895a7d39)
disposition_ref: exact dependents — independent reviewer t_a3c78661; final company consumer t_895a7d39
next_action: qa applies the effective evidence (original reports + this errata) when reviewing the installation; company consumes only after qa.
