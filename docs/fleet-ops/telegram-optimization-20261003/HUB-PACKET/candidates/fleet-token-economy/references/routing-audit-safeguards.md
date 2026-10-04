# fleet-token-economy — routing-audit safeguards

> Topic-focused reference — moved from this skill's SKILL.md by hub compaction (t_cef261ac, 2026-10-03, SOURCE-ONLY packet). Original text preserved verbatim.

## Routing-audit safeguards

- Inspect the current named-provider catalog as well as primary/fallback slots. New relays may exist only in `company`, while Groq/Mistral/Cloudflare exist only in `default`; profile configurations are independent. Export only allowlisted routing metadata, never whole configs or credential stores. Group/deduplicate the export before printing it to avoid flooding the audit context.
- Separate configured reasoning from effective reasoning. Current Hermes documentation says title generation disables thinking at the call site, overriding its auxiliary effort; same-model background review inherits the parent effort for cache parity, ignoring its own auxiliary effort. Do not claim a `max` title setting caused reasoning spend or promise that lowering same-model review effort will save tokens without checking the installed call path.
- Report provider-list entries as configured credentials, not validated availability. A local `429 (ready to retry)` is historical cooldown metadata, not proof of a current outage or recovery. Relay public prices are estimates subject to account/group multipliers; `cost_status=unknown` with zero cost fields means unknown, not free — and `cost_status=included` with 0 USD means subscription-included: quota/latency burn is real, so report it as quota consumption, never as free/zero. `reasoning_tokens` may already be counted inside `output_tokens` in the installed accounting — list them side by side, do not sum them.
- Preserve usage scopes: group auxiliary calls by the `task` column and leave empty task labels unattributed; model usage alone does not identify delegation or prove accepted-output quality. Keep cached input and reasoning separate unless the installed accounting semantics justify a sum.
- On Windows Git Bash, if `hermes` is not on PATH, discover its `.cmd` wrapper with `where.exe hermes`, read that wrapper, then use its absolute venv executable. Do not retry the unresolved shell command or install another Hermes copy.

