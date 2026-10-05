# TGR-01B model/provider routing fix — final delivery handoff (SOURCE ONLY)

Card t_ced9d357 (board default). Author run 2225 (implementation + commit); continuation run 2241 (this evidence, 2026-10-03). Company go-anchor: comment 8102, 2026-10-03T15:48:26+00:00.

## 1. Identity / anchor
- Frozen HEAD: `c605e5b618cf20a2d94422bd2c995b864bd986c8` (== company go-anchor; no new commits this run)
- Base: `9aae3c23e2c4f39f77d8d54b5e72ba4b90f4ba8f`
- Author: teknium1 <127238744+teknium1@users.noreply.github.com>, Sat, 3 Oct 2026 18:39:41 +0300
- Subject: `fix(gateway): scope channel overrides to the routed profile config (TGR-01B)`
- Assigned worktree: `C:/Users/max/AppData/Local/hermes/hermes-agent/.worktrees/tg-qwen-profile-routing-bounded-20261003`
- `git status --porcelain`: EMPTY before and after all runs (worktree and baseline clone); HEAD unchanged.

## 2. What the fix does
Scopes Telegram channel/status/slash model+provider overrides to the ROUTED profile's own config (served profile cache) instead of launcher-scope typed `GatewayRunner.config`. Explicit session model pin keeps first priority. On future rollout: fresh company DM 1256122537 and forum -1004426332349 (incl. new threads) inherit company `qwen3.8-max`/`custom`; a specialist in the same forum uses its OWN rule or own global default, never company's; missing/unknown/unserved profiles never borrow another profile's rule; warm next-turn runtime/signature updates after legit cache config replacement; system_prompt semantics preserved; Desktop/specialists untouched.

Changed paths — exactly the four allowed:
1. `gateway/run_config_loaders.py`
2. `gateway/run_turn.py`
3. `gateway/slash_commands_model.py`
4. `tests/gateway/test_profile_channel_override_routing.py` (18 new routing fixtures)

## 3. Evidence inventory (this directory)
| File | sha256 | Content |
|---|---|---|
| TGR-01B-red-new-fixtures.log | `5527f80b482652e559f5cae9595605df803688aa5c5fcfd27d782b5a1a9b4283` | run2225 RED at base: 12 failed / 6 passed; genuine model/provider AssertionErrors ('gpt-6.1-sol'/'sol'/'https://api.openai.com/v1/' != 'qwen3.8-max'/'custom'/'https://codex-proxy.internal-mcp.su/v1/'); zero Type/Import/Attribute errors. PRESERVED UNMODIFIED. |
| TGR-01B-green-new-fixtures.log | `5bb275f24379c51a9ff343e94323dbbfb18575f8597d3d8ffb3d1f5c92f423fb` | run2225 GREEN at head: 18 passed / 0 failed. PRESERVED UNMODIFIED. |
| TGR-01B-baseline-regressions.log | `fac830dde440f05b4e9880e773c271e5639f1e4ba9b39f6dd2007c46fa595835` | run2241, base tree: exit 1; 10 files, 18 passed, 0 failed; 4 files crashed (no tests ran; environmental, §6). |
| TGR-01B-head-regressions.log | `97eb80e301a8baf4a01311df391761e14b84ee422c598264c8d519849784c871` | run2241, head tree: exit 1; identical outcome to baseline. |
| TGR-01B-fix.patch | `9b9a5cfb5c8f88be62efb7b464269a74af96434a77e650e083b9caa3a6629926` | 21106 bytes; `git format-patch -1 c605e5b618... --stdout` (ordinary stdout redirect). |
| TGR-01B-DELIVERY.json | (machine record) | Full delivery record: anchors, per-file counts derived in code, hashes, comparisons, attributions. |

## 4. Baseline method (additive only)
`git clone --shared C:/Users/max/AppData/Local/hermes/hermes-agent C:/Users/max/AppData/Local/hermes/profiles/tech/cache/scratch/tgr01b-base-9aae3c23-r2241` — fresh never-before-existing unique directory; NO prefixed or follow-up deletion/ref-switch command. Clone HEAD asserted == exact base `9aae3c23e2...` ✓; `status --porcelain` empty after clone and after tests. Live source checkout used input-only (never tested/modified there). Managed scratch is prune-eligible (~24h idle); recreate with the same additive recipe if needed.

## 5. Bounded regression suite (both trees)
Command (canonical, foreground, once per tree, full stdout+stderr captured to the durable logs):

```
HERMES_PYTHON=C:/Users/max/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe bash scripts/run_tests.sh tests/gateway/test_channel_overrides.py tests/gateway/test_empty_model_recovery.py tests/gateway/test_empty_model_fallback.py tests/gateway/test_model_command_profile_config.py tests/gateway/test_model_switch_persistence.py tests/gateway/test_agent_cache.py tests/gateway/test_agent_cache_release_profile_scope.py tests/gateway/test_busy_session_profile_scope.py tests/gateway/test_handoff_secondary_profile_adapter.py tests/gateway/test_model_command_custom_providers.py
```

Per-file results — IDENTICAL in baseline and head (counts derived in code from the logs; zero retries in both trees):

| File | Baseline | Head |
|---|---|---|
| test_channel_overrides.py | 6 passed ✓ | 6 passed ✓ |
| test_empty_model_recovery.py | 1 passed ✓ | 1 passed ✓ |
| test_agent_cache_release_profile_scope.py | 5 passed ✓ | 5 passed ✓ |
| test_model_command_profile_config.py | 1 passed ✓ | 1 passed ✓ |
| test_model_command_custom_providers.py | 1 passed ✓ | 1 passed ✓ |
| test_handoff_secondary_profile_adapter.py | 4 passed ✓ | 4 passed ✓ |
| test_empty_model_fallback.py | crashed: 8 collected, 0 ran (env, §6) | crashed: 8 collected, 0 ran (env, §6) |
| test_model_switch_persistence.py | crashed: 8 collected, 0 ran (env, §6) | crashed: 8 collected, 0 ran (env, §6) |
| test_busy_session_profile_scope.py | crashed: 1 collected, 0 ran (env, §6) | crashed: 1 collected, 0 ran (env, §6) |
| test_agent_cache.py | crashed: 30 collected, 0 ran (env, §6) | crashed: 30 collected, 0 ran (env, §6) |

Runner summary (both trees): `=== Summary: 10 files, 18 tests passed, 0 failed (100% complete) ===`. Exit code: 1 in both trees (caused solely by the 4 env-crashed files; pytest-reported failed tests = 0 in both).

Missing named file: `tests/gateway/test_profile_route_ownership.py` — ABSENT in both base and head trees (exact path checked with `test -f` in each tree only; no repo scan). Not executed; recorded, per run2225's report.

## 6. Attribution of the 4 crashed files (identical in both trees)
Pre-existing host-environment artifact AT BASE, unrelated to the diff (the diff touches only `gateway/*` + its new fixture). Two pytest-internal crash modes, both visible in the logs:
1. `KeyError: <_pytest.stash.StashKey object ...>` in `tmp_path` fixture teardown — session aborts before running tests (4 occurrences per log).
2. `tests/home_io_guard.py` AssertionError `TEST BUG: file I/O against the REAL hermes home` (10 occurrences per log): the repo's own guard refuses pytest traceback/linecache `os.stat()` of interpreter stdlib sources because on THIS host the managed Python runtime and venv live UNDER the real hermes home tree (`C:/Users/max/AppData/Local/hermes/hermes-agent/.hermes-runtime/...`, `.../venv/...`).

Internal-error signature counts are identical baseline vs head (10 guard refusals + 4 StashKey errors each). No test weakened; no assertion changed; no retries double-counted. QA repro recommendation: run those 4 files where interpreter/runtime/TEMP live outside the guarded hermes home (e.g. CI layout); they should collect and run normally there.

## 7. Verdict
NO REGRESSION from the fix: identical green-file set with identical per-file passed counts (18 total), identical not-passed set (4 env-crashed files), `new_regressions = []` (computed in code; see `tests.comparison` in TGR-01B-DELIVERY.json). Combined with preserved RED (12 failed at base, genuine wrong model/provider) and GREEN (18 passed at head) fixture evidence, acceptance items 1–5 of TGR-01B-SOURCE-SPEC.md are now all evidenced.

## 8. Scope guard — SOURCE ONLY
LIVE QWEN RESTORATION REMAINS FALSE. Runtime serving in the dirty live checkout is untouched (still `gpt-6.1-sol`/`openai-codex`). No runtime patch applied, no remote publication, no live config/model/pool/session/DB mutation, no policy/classifier edits, no new source commit. This handoff is AUTHOR EVIDENCE only — NOT independent QA and NOT permission to apply a runtime patch.

## 9. Rollback
Revert source commit `c605e5b618cf20a2d94422bd2c995b864bd986c8` in an isolated review worktree; never on a live runtime checkout.

## 10. Next owners
- QA `t_d088d7f1` (released by this completion): independently verify the frozen commit and actual serving lineage.
- Company `t_32f46379`: decides the next legal activation step ONLY after the QA verdict.
