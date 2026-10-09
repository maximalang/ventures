# TGR-01 — multiplex profile-local Telegram model routing

## Deliverable / acceptance / bans / anchor
Tech owns one minimal tested source commit/patch fixing routed profile-local channel model/provider selection. Base exactHEAD9aae3c23e2c4f39f77d8d54b5e72ba4b90f4ba8f in C:/Users/max/AppData/Local/hermes/hermes-agent; use a fresh isolated worktree at that base. Runtime checkout is dirty with unrelated canonical overlays: NEVER change/reset/stash/clean it. Allowed production files gateway/run_config_loaders.py and gateway/run_turn.py; adjacent helper only if strictly required by actual consumer evidence and documented. Tests in relevant gateway tests; durable evidence in this directory. No live model/transport/config/plugin activation, no restart/update/source overlay or credentials/control DB reads.

## Reproduced defect / expected contract
Root GatewayRunner.config belongs to launch default profile. Native per-channel model/provider settings for a secondary bot's profile are ignored because GatewayTurnMixin._resolve_session_agent_runtime calls _get_channel_override(self.config,..), while GatewayConfigMixin._channel_override likewise reads self.config. _profile_configs is the existing cache of served profile config populated in run_adapters._start_one_profile_adapters. Company DM1256122537/new thread716310 and forum-1004426332349/thread20 thus inherit company/globalSol; only some explicit old-session pins use Qwen. Current native ops t_b8210384 cannot repair fresh topics without changing Desktop/global model or affecting specialist bots. Fix this specific defect, not models generally.

Expected contract: current selected source profile's platform/channel override determines model AND provider consistently in both turn runtime and user/status/slash resolution. Existing session /model remains highest priority. Fresh/unpinned company DM/forum topics resolve qwen3.8-max/custom from COMPANY channel rules; company Desktop remains Sol6.1; product/design/etc in same forum inherit THEIR rules/models, never company's. Standalone/primary behavior unchanged. Missing/unserved/unknown profile must follow existing safe fallback, never accidentally pick another profile's route. Warm cached agent must not carry oldSol after a legitimate routed config change. Do not expand scopes or change system_prompt semantics.

## Executed acceptance evidence
1. RED on frozen base for at least company DM fresh topic and forum fresh topic: primary typed config has no Qwen rule, company typed config does; wrongSol/default provider reproduced with fixtures and no network.
2. Same probes GREEN on implementation. Separate assertions for provider=custom, not Qwen name sent toCodex.
3. Regression fixture matrix: primary/standalone unaffected; company scoped DM+forum; another specialist bot in samechat unaffected; explicit sessionSol/Astra pin preserved; missing/unknown/unserved profile fallback; subsequent fresh topic inherits company rule; warm cached next-turn resolution updates correctly. Record actual passed/failed counts+commands+exit0, old-head failures vs new-head passes.
4. Relevant existing gateway model/slash/cache/multiplex/profile-route suites executed via canonical runner with baseline attribution; no rewriting assertions to hide failures. Commit exactSHA, diff paths, clean isolated before/after and rollback.
5. Deliver MODEL-ROUTING-HANDOFF.md, patch, hashes and test logs. Stage only. Independent QA and exact company decision still precede any publication/runtime apply.

## Downstream
Independent qa must use lineage different from actual implementation author including auxiliaries. After source PASS, company creates a bounded release consumer through supported attested mechanism; no overwriting dirty checkout or unapproved Hermes updater invocation. Existing native ops t_b8210384 is future configuration consumer only AFTER corrected code is loaded, with narrowed safe metadata readback; do not re-unblock it before denied session-directory precondition/scope changes. Any required deployment drain/lifecycle is a separate explicit bounded release decision, not part of this source card.

## Finance
Source remediation+tests period; natural worker usage is real but price attribution/invoice absent, incremental paid costs/estimated usage=null, revenue/refunds=null (not investigated), new paid commitments0. No paid model probes/purchases.
