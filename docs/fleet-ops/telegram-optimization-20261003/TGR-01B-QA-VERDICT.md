# TGR-01B exact-head QA verdict: BLOCK

Review card t_307fc218, run 2301, qa. Source-only offline acceptance, 2026-10-03 (UTC+03). This is a completed negative acceptance report, not approval of the source or a live release. Canonical consumer/owner: company t_32f46379.

## Identity and scope

Exact reviewed head c605e5b618cf20a2d94422bd2c995b864bd986c8.
Exact base 9aae3c23e2c4f39f77d8d54b5e72ba4b90f4ba8f is the head's direct parent; both identifiers validated as lowercase 40-character hex.
Fresh additive clones: head-r2301 and base-r2301 under this QA card workspace. No ref switching, source edits, author-test edits, runtime overlays or tests in the installed checkout.
Exactly four changed paths: gateway/run_config_loaders.py; gateway/run_turn.py; gateway/slash_commands_model.py; tests/gateway/test_profile_channel_override_routing.py. All production hunks read. Empty diffs independently confirmed for the nine other explicitly authorized source/test/runner paths; this is not a repo-wide absence claim.
Author source worktree and both QA clones: git status --porcelain empty before and after executed checks. Frozen HEAD unchanged. Commit patch matches submitted TGR-01B-fix.patch byte-for-byte: 21106 bytes, SHA-256 9b9a5cfb5c8f88be62efb7b464269a74af96434a77e650e083b9caa3a6629926.

## Numbered blockers

B1 — HIGH — Actual /model listing and Telegram picker disagree with the turn's channel route.

Reproduction:
1. In head-r2301, run canonical scripts/run_tests.sh with the external independent test_qa_tgr_routing.py; exact command/environment is in TGR-01B-QA-run2301-probe-results-v5.json.
2. Fixture company raw/typed configs share global gpt-6.1-sol/openai-codex and matching channel overrides qwen3.8-max/custom for DM1256122537 and forum-1004426332349. Profile homes, keys and provider URLs are synthetic; no real transport/provider is called.
3. Resolve the ordinary turn using the real _resolve_session_agent_runtime. Invoke the real _handle_model_command with no args, first a text-listing adapter seam, then a Telegram picker adapter seam. Only disk/provider catalogue/adapter/network boundaries are mocked; read_config and slash control flow execute.
Expected: both current-label and picker current_model/current_provider equal the effective turn qwen3.8-max/custom.
Actual: turn is qwen3.8-max/custom, but both slash surfaces report gpt-6.1-sol/openai-codex in both DM and forum. Four semantic assertion failures, no import/missing-symbol failure.
Evidence: TGR-01B-QA-run2301-qa-independent-head-v5.log, corresponding JUnit XML, and probe-results-v5.json. Failed nodes test_real_model_listing_agrees_with_effective_turn[dm|forum] and test_real_telegram_picker_agrees_with_effective_turn[dm|forum].
Location: gateway/slash_commands_model.py:93-105 read_config reads global model/provider only; _handle_model_command_locked:582-585 applies only session override, then _model_listing_reply:458-486 feeds ctx.current_model/current_provider to picker/listing. The changed _channel_override_for helper is not applied on this path.
Contract violated: SOURCE-SPEC behavior/acceptance3 and QA-SPEC acceptance2 (actual slash/status versus turn parity).
Attribution: unfixed acceptance defect, not evidence that these slash lines are a newly introduced code regression. The predecessor already lacked the channel tier; correcting the turn does not complete slash parity.
Required remediation: implementer closes this same channel-tier gap in the authorized slash file and adds genuine exposed listing/picker regressions, preserving session pin priority. QA must rerun on a new exact head. QA did not repair production code.
Owner: tech follow-up t_25e773da, created blocked pending the bounded remediation decision from company t_32f46379.

B2 — HIGH / governance — Actual serving lineage and independence are not attested.

Reproduction: native readback of author card t_ced9d357 (runs2225/2241) and current QA2301 lacks actual provider/model/fallback usage stamps; exposed tool catalog contains no session_model_usage. Permitted session_search for the author produced no dispatcher evidence; QA browse produced an unrelated interactive session. No DB/session-directory/profile workaround was attempted.
Expected: author and reviewer actual serving provider/model/fallback, including auxiliary authorship, proven by allowed readback; reviewer independent of source author/brain.
Actual: configured QA model/provider are gpt-6.1-sol/openai-codex in the native card and runtime context, but actual usage/fallback attribution is unverified; author model labels are not trusted as serving evidence.
Evidence: this card's lineage request comment5592 and native Kanban readbacks. Company read-only attestation was requested; no attestation received during this review.
Contract violated: BACKUP-SPEC lineage kill criterion and QA-SPEC lineage precondition.
Required action/owner: company t_32f46379 provides authorized bounded read-only attestations for source author2225, evidence continuation2241 and QA2301, including auxiliary authorship. If correlated or still unknown, no positive gate; use an independent other-model QA after the source fix. No model/profile repin or paid probe was performed.

B3 — MEDIUM / coverage gap — /status parity is NOT verified within the permitted read scope.

Reproduction: runtime entrypoint locator reports GatewayRunner._handle_status_command.__module__ = gateway.slash_commands_status. That source file is absent from the explicitly allowed source-read list.
Expected: a real behavioural status entrypoint probe, not a helper or source-string claim.
Actual: only the method locator was executed; no status parity claim is made. The locator's pytest PASS is excluded from behavioural-green totals.
Evidence: QA_STATUS_MODULE in own probe logs and SOURCE-SPEC authorized-read list. No read/search of this additional source was attempted.
Required action/owner: company authorizes the exact gateway/slash_commands_status.py fixture/control-flow read for a subsequent bounded QA, or narrows the status acceptance criterion explicitly. Do not treat this as a demonstrated product status defect.

## Executed checks and honest limits

Canonical interpreter: C:/Users/max/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe.
Canonical runner: scripts/run_tests.sh from each clone, invoked with the native Git-bash executable found by command -v/cygpath. Native Bash path: C:/Users/max/AppData/Local/hermes/tools/git-2.53.0+3-win32-x64/usr/bin/bash.exe.

Focused existing author fixtures rerun independently on head: 18 passed / 0 failed, runner exit0. This verifies the authored fixture result, not independent adversarial coverage.
Own FINAL v5 matrix on head: 28 pytest cases = 24 passed / 4 semantic failures, exit1. Of the 24 passes, one is a locator only: behavioural totals 23 passed / 4 failed, with one non-behavioural locator excluded. No sum across any probe revision retries.
Own FINAL v5 matrix on base: 8 passed / 20 failed, exit1. DM and exact-negative-ID forum fail with actual launcher model/provider/URL versus expected company values, not missing APIs. The same first four routed cases pass on head. Independent positive cases cover topics, own-profile specialist rule/global fallback, unknown/missing/unserved caches, identity precedence, launcher/standalone, two explicit pins, ordinary next-turn runtime/signature replacement, A-B-A nonmutation, slash helper parity and legacy system-prompt semantics. No real agent/provider completion or installed runtime is proven.
Own v1 slash failures were probe bugs: a network guard blocked Windows asyncio's local self-pipe. Corrected v2 permits only stdlib _fallback_socketpair on loopback, never an external service. v2 establishes real text-listing failure. v3/v4 picker checks did not reach the adapter because the picker-specific catalogue seam was not supplied (text fallback, captured None); they are not product-defect evidence. Final v5 supplies the proper isolated catalogue/metadata/success seams and captures actual picker model/provider, establishing its real semantic mismatch. Earlier logs retained, not counted as product defects.

Exact ten-file existing regression list, both base and head: 18 passed from six files, overall runner exit1. Identical four files crash before usable assertions: test_empty_model_fallback.py, test_model_switch_persistence.py, test_agent_cache.py, test_busy_session_profile_scope.py. Both logs show10 real-home guard refusals and4 pytest StashKey occurrences. Six green per-file counts match (6,1,1,1,5,4 by file). This is a reproduced pre-existing host/environment problem, not a new source regression; the four crashed files remain UNVERIFIED, not PASS. No guard bypass, assertion weakening or broad discovery.
Exact named tests/gateway/test_profile_route_ownership.py absent in both trees, checked only at that exact path; not executed.
First subprocess Bash attempt resolved Windows' WSL Bash and failed exit127 with bash-CR shebang error; no tests ran. This environment failure was corrected by invoking the actual native Git Bash. Failed-attempt logs retained; not a product regression or counted green.
No remote CI, publication, installed-plugin or production natural-completion evidence obtained or implied. Positive review/QA/CI stamps are withheld.

## Rollback and safety boundary

In the isolated head clone, git apply --reverse --check ../evidence/qa-exact-head.patch exited0. This proves source patch reversal applicability only; no reversal was applied. No claim of live-runtime restore or backup quality.
Reviewed trees remain unchanged. Writes limited to fresh disposable QA clones, this workspace's probe/temp/evidence files and the authorized durable evidence directory. No source/runtime config, history, pool, cron, transport or other-profile modifications. The excluded ancillary/protected paths were not accessed explicitly.
Primary t_d088d7f1 is done/superseded with NO_VERDICT; it did not pass QA. Actual backup verdict here is BLOCK. Live Qwen restoration remains false within this review's scope, not a readback claim of current live configuration.

## Finance and disposition

Scope: actual run2301 offline QA period, native Git/test receipts. Revenue/refunds null (not investigated); incremental provider paid cost and estimated usage null (no attribution/invoice). New paid commitments0; no purchases or synthetic inference authorized.
One verdict: BLOCK for exact head c605e5b618cf20a2d94422bd2c995b864bd986c8.
Review deliverable is the negative acceptance report. Company t_32f46379 must consume this BLOCK, not promote it to approval. Source changes are implementer follow-up work; lineage attestation and status-read scope remain owner decisions. Any source resubmission requires a new frozen SHA and independent re-QA; no live activation from this report.

Changed files: only QA-owned scripts/probes/receipts/logs and this report; reviewed production/test trees unchanged.
Suggested commit message for evidence only: docs(qa): record TGR-01B exact-head routing BLOCK.
