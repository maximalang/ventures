# QA-CONFIG-VERDICT — two-key native company Telegram config candidate

VERDICT: SOURCE_PASS (source/config acceptance only; no live application; not a release gate)
Card: t_8a81338c (task_type review) · Consumer: t_ee2ad6bf (task_type ops)
Run: 2214 (prior 2197/2202 rate_limited exit75 quota wall, 2206 timed_out 1221s — no verdicts issued, not evidence)
Same artifact satisfies QA-NATIVE-RECOVERY.md deliverable name "QA-CONFIG-ALTERNATE-VERDICT.md".

## Boundaries honored
No live config writes, no restarts, no model migrations, no paid inference, no secret reads. All probes
read-only or in-memory; candidate bytes never edited (hash below proves identity). Application by ops
remains bound to ALL consumer prerequisites: this PASS plus the bounded alternate qa t_e87dad43
(qwen/custom) per company note 03.10 12:34.

## Anchor identity (recomputed this run)
- Candidate: C:/Users/max/Desktop/all/ventures/docs/fleet-ops/telegram-optimization-20261003/NATIVE-CONFIG-CANDIDATE.json
  sha256 d7b59f1b29299d361b3539870f0789dbe089c790576be18126dedfc98ab2d105 — matches company anchor comment
  and QA-NATIVE-RECOVERY.md.
- Installed head: git -C C:/Users/max/AppData/Local/hermes/hermes-agent rev-parse HEAD
  = 9aae3c23e2c4f39f77d8d54b5e72ba4b90f4ba8f — matches candidate.installed_head_at_capture and recovery doc source root.
- Worktree is dirty (38 files). Candidate-relevant consumers carry NO local overlays: agent/agent_init.py,
  gateway/display_config.py, gateway/run_turn.py, gateway/run.py, hermes_cli/config*.py are clean vs HEAD;
  dirty agent/auxiliary_client.py hunks are confined to retry-ladder internals (L7300–7500), while the
  threshold/model-family functions it uses (L598–628, L674–688) are untouched. Verdict is therefore
  head-bound; dirty files are outside this acceptance.

## Serving lineage independence (author = company gpt-6.1-sol)
Readback: qa profile state.db, table session_model_usage, copy-read RO, session 20261003_122121_56:
- MAIN: glm-5.3 (zai) 3 calls + glm-5.3-flash (zai) 35 calls; in=147,011 / out=32,904 tokens.
- Auxiliary/compression task-tagged rows: none (all probes offline; no LLM in the loop).
- Rows with model sol/gpt in this session: none (sol/gpt rows in the DB belong to older sessions only).
Conclusion: no authorSol6.1 overlap in main or auxiliary rows → independence requirement MET.
Alternate qwen t_e87dad43 is a separate consumer prerequisite, not part of this verdict.

## Executed checks (command → exit)
1. sha256sum NATIVE-CONFIG-CANDIDATE.json → exit 0, hash above.
2. git rev-parse HEAD (+ status --porcelain) → exit 0; dirty inventory compared against consumer paths.
3. PROBE-C compression resolver (venv python 3.11.16, offline, _parse_compression_config):
   - empty cfg, model gpt-6.1-sol on openai-codex → threshold 0.85 (codex autoraise), threshold_tokens None (baseline).
   - company compression section verbatim (from profiles/company/config.yaml L104-117) → protect_last 10,
     protect_first 3, tail lean, prune 48000/8000/4096, enabled true, target_ratio 0.15 (fidelity OK).
   - + threshold_tokens 128000 → threshold_tokens resolves to 128000; every other key byte-equal;
     assertions PASS; exit 0. Probe script: profiles/qa/cache/scratch/qa_probe_compression_candidate.py.
4. PROBE-T telegram display resolver on the REAL company config.yaml (in-memory deep copy only):
   - before: resolve_tool_progress(cfg,'telegram') = ('new', explicit=True) — equals candidate before-value.
   - after single-key override: ('off', explicit=True) — equals candidate after-value; resolver normalises
     'off' (display_config.py L186) and explicit YAML wins (L115-126).
   - isolation: discord stays tier default 'all'; global display.tool_progress stays 'all' (CLI untouched).
   - preserve assertions ALL PASS: tool_progress_grouping accumulate, busy_ack_detail false,
     busy_steer_ack_enabled true, interim_assistant_messages true, long_running_notifications true,
     suppress_warning_notifications false, show_reasoning false, display.streaming true,
     platforms.telegram.extra.rich_messages/rich_all true; compression section intact;
     threshold_tokens ABSENT before application. exit 0. Script: qa_probe_telegram_display.py.

## Consumer verification (code, head)
- compression.threshold_tokens: parsed into CompressionSettings (agent_init.py L1557-1559, probe-verified);
  semantics "absolute cap — compression triggers at the lower of the ratio threshold and this count,
  clamped to the model context length" (config_defaults.py L592-595); explicit null = ratio-only opt-out.
- Hot-reload/cache invalidation: ("compression","threshold_tokens") is in _CACHE_BUSTING_CONFIG_KEYS
  (gateway/run.py L4399-4415) → a mid-gateway config change invalidates the cached agent; display keys
  resolve per turn via resolve_tool_progress (gateway/run_turn.py L2958-2965), no agent-level caching.
- display.platforms.telegram.tool_progress='off' consumer: run_turn.py L3001
  tool_progress_enabled = progress_mode not in {"off","log"} → progress bubbles off for Telegram only
  (per-platform key). Long-running notifications, interim assistant messages and busy-ack/steer are
  independent surfaces (run_turn.py L3005+; probe values preserved) → warnings/steering/long-running kept.
  rich transport (platforms.telegram.extra.*) is non-allowlisted and untouched.

## Scope honesty and risk notes (non-blocking)
- F-1 Scope: compression is profile-wide — company profile incl. its Telegram, Desktop and cron; NOT
  Telegram-only. Candidate scope field states exactly this. OK.
- F-2 Not a hard cap: 128000 gates only the compaction trigger; per-call API payload unaffected. Matches
  candidate "effect" honesty.
- F-3 Dominance/no-op boundary: on the current 272K-capped Codex Sol route the ratio threshold fires at
  0.85×window≈231K ≫ 128K, so the cap strictly dominates → earlier semantic compaction achieved. If a
  future model context_length drops below ~160K (128K/0.8), the ratio re-dominates and the cap goes
  dormant silently (no error). Monitor on model change. Severity: info.
- F-4 Cache-prefix tradeoff: earlier trigger ⇒ compression/proactive-prune passes occur earlier/more
  often; each committed pass rewrites sent history and breaks the prompt-cache prefix
  (config_defaults.py L628-631 code comment). Continuity protected by lean tail, protect_last 10,
  min 1 user message, protect_first 3. Quality/latency/summary-retention to be judged in the 24h/48h
  observation window per company metrics plan (MEASUREMENT-REVIEW.md). Severity: info.
- F-5 Cash: no savings asserted; uncached medians Qwen 1842.5 / Sol 3115 tokens stand
  (MEASUREMENT-REVIEW.md); cached footprint reduction ≠ cash savings. Financial scope = this review;
  provider incremental cost unknown/unpriced, 0 new commitments, no purchase.

## Typed result
SOURCE_PASS for exact candidate bytes d7b59f1b29299d361b3539870f0789dbe089c790576be18126dedfc98ab2d105
on installed head 9aae3c23e2c4f39f77d8d54b5e72ba4b90f4ba8f. Any changed candidate bytes require a new
company binding and re-review. This is not a release gate and not self-approval of application:
ops application on t_ee2ad6bf remains conditional on the remaining prerequisite (alternate qa t_e87dad43).
