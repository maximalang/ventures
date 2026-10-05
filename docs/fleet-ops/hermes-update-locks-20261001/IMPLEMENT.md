# Windows updater: locked retired PM entries — implementation contract v1

## Owners and anchor
Brain/decision owner: company. Hands owner: tech. Independent reviewer: qa (separate card). Activation owner: operations, after positive review only.
Source installation: C:/Users/max/AppData/Local/hermes/hermes-agent.
Frozen base: bda33b601d194fb8a43e5660c57542aad14aa372.
Implement only in prepared isolated worktree C:/Users/max/Documents/hermes-update-lock-recovery, branch fix/pm-retired-lock-recovery-20261001.
Durable output directory: C:/Users/max/Desktop/all/ventures/docs/fleet-ops/hermes-update-locks-20261001.

## Exact deliverable
A minimal committed patch fixing PM's confusion of completed publication/rollback with failure to reclaim a retired tree held open on Windows, with reproducing regression tests and executable Windows-lock evidence. Deliver candidate SHA, binary git diff PATCH.diff, REPORT.md, test logs, and MANIFEST.json with base/candidate SHA, touched files, commands, exit codes, counts and sha256 pins. Do not merge or activate it.

## Evidence already gathered, not yet a validated fix
Live checkout is clean at base. Handoff log C:/Users/max/AppData/Local/Hermes/logs/desktop-update-handoff.log:
- line 2520, 30.09 22:42:15: git install failed deleting tools/.previous-git-2.53.0+3-win32-x64/usr/bin/bash.exe, WinError 5; exit 1 at line 2531.
- line 2566, 22:49:12: source preparation failed deleting tools/.displaced-5dc341ec998b49d3960436a3c0051c04/DLLs/libcrypto-3-x64.dll; exit 1 at line 2567.
Current pm/install.py: _publish_entry verifies/yields for facts commit then _remove_entry(previous) at 292-293; _restore_previous_entry renames previous back then _remove_entry(displaced) at 273-274; _settle_previous_entry removes committed prior tree at 304. _remove_entry retries five times then propagates.
Ranked hypotheses: (1) committed publication is reported failed solely because old executable is held; (2) a successful rollback is reported failed solely because displaced DLL is held; (3) a real publication/rename/facts error instead precedes cleanup. Confirm/falsify with tests, do not assert a culprit process without proof. Marker/UI/cache are secondary unless a reproducible test contradicts this scope.

## Acceptance (all required; negative verdict permitted when disproven)
1. First add regression tests and run them on unmodified production code. Save RED log and exact expected failure; no generic import errors count as reproduction.
2. Committed replacement + persistent Windows-style cleanup hold: verified new bytes and facts stay authoritative; the operation is not failed solely by reclamation. A second install while the hold persists is safe and idempotent; releasing the hold allows bounded safe reclamation. Report retained bytes clearly; do not claim they were removed.
3. Interrupted publication recovery and successful rollback with a locked displaced tree: keep the valid restored tree/facts intact and preserve original publication/commit error, not a cleanup error. No false success when verification, rename/publication, facts write or restoration fails.
4. Cover host installs and stage-only semantics; retain the existing interrupted-replacement and failed-restore guarantees. Fresh publication and ordinary unlocked cleanup still work.
5. Run focused new tests, tests/pm/test_pm_authority.py and tests/pm/test_pm_core.py, plus any directly affected PM tests. Save raw exit codes/counts. Do not run all unrelated repository tests.
6. Exercise at least one REAL Windows file hold in an isolated fake PM store (e.g. ctypes CreateFileW without delete sharing or LoadLibrary on a copied test DLL), not the live tools directory. Assert cleanup fails on baseline and candidate preserves committed success/retry semantics. Close fixture handles and preserve report. If impossible, report NOT VERIFIED; do not fabricate.
7. Candidate git diff --check passes; commit on task branch; no unexplained changes. Provide rollback as reverse patch/restore base and state persistence requirements for the next external update.

## Scope and bans
Allowed production scope: pm/install.py; pm/store.py or closely related PM cleanup code only if necessary and justified by reproduction. Tests under tests/pm plus a bounded fixture harness are allowed. No broad refactor, updater UI/cache changes, runtime pin changes, or new services.
NEVER run an application update command, invoke a full desktop handoff, stop/restart desktop/gateway/workers, mutate the live checkout/runtime/tools store, apply a layer, change model routing/configuration, inspect account material or control-plane/profile databases, or publish/merge/deploy. Do not read private stores or infer past context. No inference probes. A policy deny is a stop/report condition, not permission to route around it.
Use read_file/search_files for bounded source reads, write_file/patch for changes, terminal for isolated tests and git. Do not assume execute_code is available. One effectful action per terminal call. Commit incremental progress before the final report, do not reread sources endlessly. Durable files must survive workspace cleanup.

## Verified interpreter and integration requirement (owner clarification)
Verified by company: C:/Users/max/AppData/Local/hermes/hermes-agent/.venv/Scripts/python.exe has pytest and yaml. Use that absolute interpreter with cwd set to the isolated worktree; prove pm.install.__file__ resolves to the worktree before every recorded suite. No acquisition is needed.
Owner requires a proper stable solution, no wrapper updater or silent catch-all. In REPORT.md distinguish harmless post-commit reclamation from publication failures, identify what remains retained, and explain how cleanup can be retried without corrupting rollback. The PM change is the first increment, not end-to-end acceptance. A clean child interpreter loads source AFTER an official checkout replacement (hermes_cli/update_completion.py main/_prepare); current dirty-layer patches alone may disappear at that seam. Report that persistence boundary honestly, do not add startup monkey-patches, scheduled patchers or extra services. Company will bind persistence/release and update-related fleet patch verification to separate independent gates.

## Verification tooling
Use a known available Python with pytest; discover it without invoking PM acquisition. The live repo's .venv/Scripts/python.exe may be used ONLY as interpreter for isolated worktree tests; no dependency installation into it. Print sys.executable/version and module.__file__ so test imports prove the candidate worktree is tested. Fixture runtime and temp paths must be explicitly scoped to the task's scratch/worktree, never the live store. Tests that use loopback fixture servers are allowed. Test command shape: <absolute-python> -m pytest -q tests/pm/test_pm_authority.py tests/pm/test_pm_core.py <new-test-file> from the isolated worktree. Persist stdout/stderr to durable logs.

## Decision, impact, kill, finance
Hypothesis: separating post-commit reclamation from publication correctness removes the observed repeat failure without bypassing safety. Confidence: medium-high from two exact paths, subject to RED/real-lock evidence.
Impact metric: deterministic Windows lock reproduction fails at base and passes at candidate; zero regressions in required focused shards. Live stability is separate and cannot be claimed by this producer.
Kill criterion: no faithful reproduction, lost rollback guarantee, suppressed real commit error, scope drift or failed required tests => report BLOCK with evidence; do not activate.
Financial scope: local updater repair, this task period starting 2026-10-01. Source: execution logs. Confirmed revenue/refunds: not applicable; incremental external paid costs/new commitments: none authorized. Estimated model usage cost: null until metered; no external paid actions permitted.
