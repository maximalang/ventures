# QA-CONFIG-ALTERNATE-VERDICT — bounded independent alternate (qwen3.8-max/custom)

VERDICT: SOURCE_PASS (source/config acceptance only; no live application; not a release gate)
Card: t_e87dad43 (task_type review, run 2216) · Consumer: t_ee2ad6bf (task_type ops)
Author of candidate: company gpt-6.1-sol. Alternate reviewer: qwen3.8-max/custom per QA-NATIVE-RECOVERY.md targeted per-card routing.

## Anchor identity (recomputed this run, commands + exits in "Checks")
- Candidate: C:/Users/max/Desktop/all/ventures/docs/fleet-ops/telegram-optimization-20261003/NATIVE-CONFIG-CANDIDATE.json
  sha256 d7b59f1b29299d361b3539870f0789dbe089c790576be18126dedfc98ab2d105 — matches card body, QA-NATIVE-RECOVERY.md and candidate.installed_head_at_capture binding.
- Installed head: git rev-parse HEAD in C:/Users/max/AppData/Local/hermes/hermes-agent
  = 9aae3c23e2c4f39f77d8d54b5e72ba4b90f4ba8f (2026-10-02 21:08:13 -0400) — matches candidate anchor.
- Primary reviewer artifact: QA-CONFIG-PRIMARY-VERDICT.md sha256 86e6e65554c264f9d956d279a34be236f7b502a0472023ef93c2ed8b0a9c4171 — matches company comment 2026-10-03 13:03. Primary SOURCE_PASS (run 2214) is a separate, already-delivered prerequisite; this alternate is the second, independent consumer prerequisite.
- Worktree dirty (38 files) but ALL candidate consumers clean vs HEAD: agent/agent_init.py, agent/context_compressor.py, gateway/display_config.py, gateway/run_turn.py, gateway/run.py, hermes_cli/config.py, hermes_cli/config_defaults.py, hermes_cli/config_schema.py (git diff --quiet per file, this run). Dirty agent/auxiliary_client.py hunks confined to L7300+ retry-ladder; threshold functions untouched. Verdict is head-bound.

## Serving lineage independence (natural counters, qa state.db session_model_usage, RO copy-read)
This review's sessions: 20261003_123230_2e2016 (run 2210, timed_out) and 20261003_125303_af02f8 (run 2216, this verdict).
- MAIN rows: qwen3.8-max / custom / dashscope compatible-mode ONLY (32 calls in run2210 session; 14+ calls run2216 at readback time). in=113,786+51,837 / out=59,809+24,451 at readback.
- Auxiliary/compression/task-tagged rows for these sessions: NONE (task column empty; all probes offline, no LLM in loop).
- Rows with sol/gpt model in these two sessions: NONE.
Conclusion: main and auxiliary rows fully independent of author Sol6.1 → independence requirement MET.

## Executed checks this run (command → exit)
1. sha256sum NATIVE-CONFIG-CANDIDATE.json → exit 0 (hash above).
2. git rev-parse HEAD + git status --porcelain + per-consumer git diff --quiet HEAD → exit 0 (clean list above).
3. sha256sum QA-CONFIG-PRIMARY-VERDICT.md → exit 0 (matches company binding).
4. pytest tests/agent/test_compression_config_defaults.py tests/gateway/test_display_config.py -q → 15 passed, exit 0 (venv python 3.11, installed head).
5. ALTERNATE cap-dominance probe (evidence/qa_alt_probe_cap.py, ContextCompressor at head, offline) → exit 0:
   - cap=128000 @272K window, threshold 0.85: threshold_tokens = 128000 (cap strictly dominates ratio trigger 231,200); preview_threshold_tokens = 128000.
   - cap=None @272K: threshold_tokens = 231200 = int(272000*0.85) (ratio-only baseline).
   - cap=128000 @100K window: threshold_tokens = 85000 — cap clamped to window, ratio re-dominates (F-3 dominance/no-op boundary empirically confirmed, incl. small-window dormancy).
6. Rerun of primary fixtures under alternate session (independent execution, same head):
   - qa_probe_compression_candidate.py → PROBE2_ASSERTS_OK, exit 0: baseline threshold_tokens=null; +candidate → 128000; protect_last 10 / protect_first 3 / tail lean / prune 48000/8000/4096 / target_ratio 0.15 / enabled true all preserved byte-equal.
   - qa_probe_telegram_display.py (real company config.yaml, in-memory deep copy only) → PROBE3_ASSERTS_OK, exit 0: BEFORE resolve_tool_progress('telegram') = ('new', explicit=True) = candidate before-value; AFTER single-key override = ('off', explicit=True) = candidate after-value; discord + global display.tool_progress stay 'all' (platform isolation); ALL preserve asserts pass (grouping accumulate, busy_ack_detail false, busy_steer_ack_enabled true, interim_assistant_messages true, long_running_notifications true, suppress_warning_notifications false, show_reasoning false, display.streaming true, rich_messages/rich_all true, compression section intact, threshold_tokens ABSENT pre-application).

## Consumer/cache verification at installed head (code read, this run)
- compression.threshold_tokens parsed in agent_init.py L1557-1559 (_positive_int), flows to ContextCompressor(threshold_tokens_cap=...) at L2024; cap semantics "lower of ratio threshold and cap, clamped to window" confirmed in context_compressor.py _derive_trigger/_effective_threshold_cap/_apply_threshold_tokens_cap (L2635-2718) and probe 5.
- Hot reload: ("compression","threshold_tokens") present in _CACHE_BUSTING_CONFIG_KEYS (gateway/run.py L4399-4415) → mid-gateway change invalidates cached agent; display keys resolve per turn via resolve_tool_progress (run_turn.py L2958+), no agent-level caching.
- tool_progress='off' consumer: run_turn.py L3001 tool_progress_enabled = progress_mode not in {"off","log"} → progress bubbles off for Telegram only; long-running notifications / interim messages / busy-ack+steering are independent surfaces preserved (probe 6). display_config.py L53 telegram tier default already 'off'; explicit YAML 'off' wins (L115-126) — no behavioral surprise.
- config_defaults.py L592-595: threshold_tokens documented as absolute compaction TRIGGER, not an API payload ceiling; migration 46→47 (config_migrations.py L802-811) confirms null default — candidate adds explicit value, no schema violation.

## Acceptance mapping (QA-NATIVE-RECOVERY.md)
- native threshold resolution 128000 with protected tail10 / goal-history preserve → probes 5-6 PASS.
- Telegram display off with warnings/steering/interim/long-running preserved → probe 6 + run_turn consumer PASS.
- native config consumer / cache invalidation on installed head → section above PASS.
- profile-wide compaction scope honest → candidate scope field states "company profile incl. Telegram/Desktop/cron, not worker/default" — matches contract §company decision; no Telegram-only claim.
- not hard API ceiling, no cash-savings assertion → candidate effect/rollback fields honest; incremental_paid_cost_rub=null with reason; new_paid_commitments_rub=0. PASS.
- bans list consistent with contract boundaries (no model/pool changes, no session deletion, no restarts, no other-profile writes, no secrets, no new watchers). PASS.
- Non-blocking notes inherited/confirmed: F-3 cap dormancy if future model window < ~151K (128K/0.85) — empirically shown by probe 5 (@100K ratio wins, 85000); monitor on model change. F-4 earlier compaction breaks prompt-cache prefix more often; continuity protected by lean tail + protect_last 10 + protect_first 3; judge in 24h/48h observation per MEASUREMENT-REVIEW.md.

## Boundaries honored
No live config writes, no candidate edits (hash proves identity), no restarts, no model migrations, no paid inference probes, no secret/credential reads, no session deletion, no other-profile writes. All probes offline/in-memory on installed head. Fixtures live in this task workspace evidence/ (isolated directory).

## Typed result
SOURCE_PASS for exact candidate bytes d7b59f1b29299d361b3539870f0789dbe089c790576be18126dedfc98ab2d105 on installed head 9aae3c23e2c4f39f77d8d54b5e72ba4b90f4ba8f, by alternate reviewer qwen3.8-max/custom with Sol6.1-free serving lineage. Any changed candidate bytes or head drift void this verdict and require re-review. Ops application on t_ee2ad6bf remains bound to BOTH verdicts (primary run2214 + this alternate) and company's exact binding; this document is not self-approval of application.
