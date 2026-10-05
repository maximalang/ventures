# Scoped company Telegram intake recovery

Deliverable: restore the EXISTING company Telegram adapter on the current default-host multiplexer, with durable nonsecret recovery receipt. Owner: operations; company owns disposition. Owner explicitly requested verification/continuation and investigation of silent existing Telegram bot in this Desktop conversation.

Anchor: installed source HEAD 9aae3c23e2c4f39f77d8d54b5e72ba4b90f4ba8f; host PID26200 observed alive by native `hermes -p default gateway status` at 2026-10-03T17:59–18:04+03; company is explicitly parked and absent from served_profiles. Refresh native state before any action; if host changed, is down, or company is already connected, do not repeat the action. Company profile C:/Users/max/AppData/Local/hermes/profiles/company. Existing DM1256122537 and forum -1004426332349, no new surface.

Diagnosis evidence: native company gateway status says `Profile 'company': parked (hermes -p company gateway start)`; host state is fresh/running, served_profiles excludes company. Company's separate gateway_state.json is obsolete (2026-09-22) and is NOT current platform proof. Installed hermes_cli/gateway_profile_lifecycle.py L30–65 documents that named-profile start removes only that profile's parked marker and calls request_serve_profile_hot on the living host. It does not restart/stop the host or create a second poller. Why/who parked the profile has NOT been proven; do not claim it.

Permitted operation: ONCE, ONLY if still parked and host alive, native `C:/Users/max/AppData/Local/hermes/hermes-agent/venv/Scripts/hermes.exe -p company gateway start`. No all/force/restart. Native tools/CLI only. First policy denial => persist exact call/result and stop; no other spelling/tool/script/identity bypass. Worker's inherited task/run/board pins stay intact.

Acceptance:
1. Capture exact before/after native status and timestamp. Host writer PID and creation identity unchanged.
2. Current host gateway_state.json contains served_profiles company and company:telegram state connected, errors null, writer_pid equals live host PID, updated_at AFTER operation. Old default telegram timestamp is not company proof.
3. New host gateway.log deltas show company served, `telegram connected (profile: company)` and polling progressing. Examine >=60s of new deltas for supervised task death, adapter fatal/duplicate credentials/network conflict, and owner unauthorized block; connected alone is not end-to-end proof.
4. Natural owner inbound/reply pair only if one arrives. Otherwise explicit end_to_end_verified=false and ask owner to resend ONE old message. NEVER send a synthetic/paid LLM canary or second getUpdates poller. Cold boot may drop offline updates; do not alter retention.
5. Create BOT-RECOVERY-RECEIPT.json and BOT-RECOVERY-RESULT.md in the durable evidence root (this directory), attach the genuine receipt before finalization. No claimed complete round-trip without actual inbound and delivered response.

Preserve: compression.threshold_tokens=128000, display.platforms.telegram.tool_progress=off, Desktop model gpt-6.1-sol, pools, specialists, history, group/DM topology. Qwen model restoration is a separate blocked source lane; no model changes here.

Forbidden: host/profile restart/stop, new gateway process or bot, source overlays/update/doctor/migration; secrets/auth/dumps/raw databases/session-directory reads; editing config, notification scripts, crons, skills/plugins/permissions; deleting messages/history, terminating workers, direct parked-marker manipulation. Don't unpark operations or any other profile.

Risk/kill criterion: any duplicate poller/conflict/fatal or host disruption => stop and company decision; do not blindly restart. No automatic rollback-by-stop because it could kill healthy cron/owner work; native supported containment only if independently justified by new incident evidence.

Financial scope: existing company Telegram availability recovery, period 2026-10-03, source native status/state/logs. No purchases/new payment commitments authorized. Confirmed revenue/refunds null (outside scope); incremental paid/estimated provider usage cost null (invoice/usage attribution absent). Hypothesis: recover owner interaction, not measurable cash savings. Confidence: high on parked intake explanation, unproven on park origin and final model health.
