# BOT-RECOVERY-RESULT — company Telegram intake restored

Task: t_0edb4ef8 (fleet-ops), run 2224, owner operations, decision:company=go.
Installed HEAD: 9aae3c23e2c4f39f77d8d54b5e72ba4b90f4ba8f.

## Состояние → действие → evidence → риски/откат

### Состояние (before, 2026-10-03T15:15:50Z)
- Host gateway PID 26200 alive; served_profiles = default, design, finance, product, qa, research, sales, tech, ux, video-director, video-editor.
- company: parked ("Profile 'company': parked (hermes -p company gateway start)").

### Действие (once, native)
- 2026-10-03T15:16:28Z: `venv/Scripts/hermes.exe -p company gateway start` (named-profile hot start; no restart/force/config/model changes; zero policy denials).
- CLI: "Profile 'company' unparked ... host retries on its next rescan (within 30s)."

### Evidence (after)
1. Status 2026-10-03T15:17:29Z: company in served_profiles; host PID unchanged 26200.
2. Host gateway_state.json (updated 2026-10-03T15:19:53Z, host writer alive):
   `company:telegram { state: connected, error_code: null, error_message: null, needs_attention: false, retrying_since: null, updated_at: 2026-10-03T15:16:51Z, writer_pid: 26200, writer_start_time: 179101792746 }` — writer_pid == live host PID; updated_at AFTER operation.
3. gateway.log deltas (18:16:51 local = 15:16:51Z):
   - `telegram connected (profile: company)`
   - `[MULTIPLEX] ... not starting a second listener`
   - `Now serving profile 'company' (1 adapter(s) connected; control-socket)`
   gateway-stdio.log: DNS-over-HTTPS fallback discovery 18:16:37 → Connecting attempt 1/8 18:16:39 → `Connected to Telegram (polling mode)` 18:16:51.
   Observation window 195s post-connect: 0 fatal, 0 duplicate-poller, 0 credential conflict, 0 unauthorized, 0 supervised-task death.
4. Webhook listener 127.0.0.1:8644 owned by PID 26200 (netstat), single host process; no second poller created.

### Acceptance scoreboard
1. before/after status + PID unchanged — PASS
2. host state company:telegram connected, errors null, writer_pid 26200, updated_at after op — PASS
3. log deltas served/connected/polling, >=60s clean — PASS
4. natural owner roundtrip — PENDING (end_to_end_verified=false; no owner inbound during window; no synthetic canary per spec)
5. receipt + result in durable evidence root — PASS (BOT-RECOVERY-RECEIPT.json alongside this file)

### Риски/откат
- Нет rollback-by-stop: host здоров, cron/owner-работа не тронута. Kill criterion не сработал (нет duplicate poller/conflict/fatal).
- Откат при новом инциденте — только native containment по решению company, не автоматом.
- Park origin не доказан и не утверждается.

### Next owner / APPROVAL
- End-to-end: owner (max) — переслать ONE старое сообщение боту; operations подтвердит по host state/log deltas как отдельную verification.
- Никаких model/config/source изменений не производилось; preservation-список спека соблюдён.
