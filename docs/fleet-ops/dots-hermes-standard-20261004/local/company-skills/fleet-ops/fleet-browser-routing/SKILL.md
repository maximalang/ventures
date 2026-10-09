---
name: fleet-browser-routing
description: "Use when choosing a browser for any fleet task."
version: 1.0.0
---
# Fleet Browser Routing (owner decision 30.08.2026)

## incy local proxy (ОТКРЫТИЕ 29.09 — egress для заблокированных доменов)
Владелец-VPN incy держит ЛОКАЛЬНЫЕ прокси: **127.0.0.1:10809 (HTTP)** и **10808 (SOCKS5)**. Проверено 29.09: instagram.com = 200, tiktok.com = 200 ЧЕРЕЗ 10809 (напрямую с флот-хоста: IG — DNS-блок, YT/VK — TLS EOF от SNI-фильтра). YouTube через прокси НЕ ходит (curl 35) — YT-хэндлы валидировать только формой создания.
- Терминал: `curl.exe -x http://127.0.0.1:10809 ...`; python requests/urllib — proxies={'https':'http://127.0.0.1:10809'}.
- Браузеры флота для IG/Meta-задач запускать с `--proxy-server=http://127.0.0.1:10809`.
- IG без логина отдаёт login-wall 200 на ЛЮБОЙ handle — доступность IG-хэндла проверять ТОЛЬКО формой из залогиненной сессии.
- Стена антибота остаётся независимо от прокси: CDP-синтетические события (isTrusted=false) TikTok/IG режут («Something went wrong», вечный «Please wait...» в headless) — чувствительные флоу (rename/registration) делать OS-level вводом (pyautogui/SendInput в headed-окно = trusted events) или руками владельца.

## ПРОВЕРЕННЫЕ РЕЦЕПТЫ (01.10, оба отработали в бою)
- **TikTok (rename/edit)**: headed Edge (profile-visible, detached-запуск через `cmd /c start` — иначе terminal-session cleanup убивает окно!) + **computer_use** (capture som → click по элементу; клавиатура/печать ТОЛЬКО delivery_mode=foreground, клики работают background). OS-ввод = trusted events, антибот пропускает; CDP-клики — режет. Username-лок 30 дней после смены, nickname-лок 7 дней (даже no-op save может съесть окно — проверять состояние поля перед Save).
- **Instagram (login/rename/edit/posting)**: **instagrapi** (venv curl-cffi) + proxy http://127.0.0.1:10809 — headless, БЕЗ браузера. Логин = пароль + email-код челленджа (код из Gmail нужного аккаунта — проверять ЧЕЙ ящик залогинен в браузере: GLOBALS[10]). Сессию сохранять в settings.json и переиспользовать (load_settings). 429-троттлинг штатный — delay 3-6s, account_edit проходит даже при 429 на check_username.

## CANON UPDATE (owner directive 24.09.2026): Donut и BrowserOS neo = ON-DEMAND, НЕ демоны
- **Donut**: поднимать только на время мультиаккаунтной задачи, после — опускать.
  - старт: `C:\Users\max\Desktop\Donut-Portable\donut-start.cmd` (идемпотентен, ждёт MCP 51080, выводит DONUT-UP/DONUT-ALREADY-UP/DONUT-TIMEOUT)
  - стоп: `C:\Users\max\Desktop\Donut-Portable\donut-stop.cmd`
- **BrowserOS neo**: headless-лейс поднимается только под задачу neo.
  - старт: `C:\Users\max\AppData\Local\BrowserClaw\fleet-bridge\start-neo-headless.cmd` (идемпотентен по MCP 9210)
- Автозагрузка обоих отключена: файлы лежат в `Startup\Disabled-autostart\{Donut_Browser.vbs, BrowserOS_neo.vbs}` (обратимо: вернуть в Startup).
- **Fleet-Browser (headless Edge, CDP 9222) остаётся демоном** — 8015 вызовов browser_exec за 30 дней, рабочая лошадка.
- Урок 24.09: Edge НЕ освобождает RAM после закрытия вкладок (26 хвостовых вкладок закрыто — всё ещё 2,5 ГБ/40 процессов). Тяжёлые сессии завершать рестартом: убить процессы с Fleet-Browser в cmdline → `start-fleet-browser.cmd` → падает до ~800 МБ. Хвосты смотреть: `http://127.0.0.1:9222/json/list`, закрывать `/json/close/<id>`.

Two browsers, split by purpose. Do NOT route special tasks to the standard
browser or everyday tasks to Donut.

## Standard browser — everyday fleet work

Headless Edge with a persistent fleet profile, driven by the native Hermes
browser stack (`browser_exec` tool / `browser-use` CLI, CDP port 9222).

- Launcher: `C:\Users\max\Desktop\Fleet-Browser\start-fleet-browser.cmd`
- Persistent profile: `C:\Users\max\Desktop\Fleet-Browser\profile\`
  (cookies/logins survive restarts — keep it tidy, it is shared)
- Autostart: `Startup\Fleet_Browser.vbs`
- Health check: `browser-use doctor` → chrome running / daemon alive /
  connections — 1. CDP: http://127.0.0.1:9222
- Config (company profile, fixed 08.09): `browser.use_real_profile: false`
  + `browser.cdp_url: http://127.0.0.1:9222`. PITFALL: if
  `use_real_profile: true` and the Windows default browser (http/https
  UserChoice) is NOT Chrome/Edge/Brave/Chromium — e.g. Perplexity Comet
  hijacked the default — EVERY browser_exec fails closed with "default
  browser is not a supported Chromium browser", even though fleet Edge is
  alive on 9222. Fix = the two config keys above (attach to fleet Edge via
  cdp_url); do not need to change the OS default browser.
- `browser-use doctor` shows daemon FAIL / 0 connections when Chrome was
  launched externally (fleet launcher) — that is EXPECTED with cdp_url mode;
  the real health probe is `curl http://127.0.0.1:9222/json/version`.
- Use for: landing checks, scraping public pages, QA, screenshots, form
  tests, any task that needs interaction/JS rendering but no disguise.
- If a plain HTTP fetch (`web_extract`/curl) reads the page — do NOT open
  the browser at all.
- Для фонового восстановления браузера не используй `cmd /c start "" <launcher.cmd>` как «тихий» запуск: Windows может открыть отдельный `cmd /K` и оставить владельцу терминал с `DevTools listening`. Headless скрывает окно браузера, но не консоль запуска. При жалобе сначала сверь точный WebSocket с `/json/version`, владельца порта, parent PID/creation time, команду и cwd консоли, затем script/job в штатном списке cron. Не приписывай такой запуск апдейтеру по одному тексту DevTools и не закрывай весь браузер вместо ненужной консоли.

## Donut — special tasks only

Anti-detect browser (MCP `donut`, 80 tools, `mcp__donut__*`), patched Wayfern
engine — see skill `donut-browser` for launch/verification.

- Use ONLY for: multi-accounting, distinct fingerprints/personas, anti-fraud
  bypass, proxy-chained identities.
- Never for ordinary browsing — the patched engine is a maintenance burden.

## Routing table

| Task | Browser |
|---|---|
| Check a landing page / UI | standard |
| Scrape public site (JS needed) | standard |
| QA test, form fill, screenshots | standard |
| Logged-in session reuse (fleet profile) | standard |
| Multiple distinct identities/accounts | Donut |
| Fingerprint/proxy isolation required | Donut |
| Plain public page, no JS needed | no browser (fetch) |
| **Owner hands-on action** (registration, KYC, payment, identity-bound login) | **headed window for owner only** |

## Anti-detect toolbox (29.09)

Stealth/анти-детект справочник — `references/antidetect-toolbox.md`: линии флота ↔ анти-детект инструменты (Donut/curl_cffi/scrapling-Camoufox уже в строю), лестница эскалации при bot-стене, read-only detection-тесты (CreepJS/Brotector/tls.peet.ws), бесплатные библиотеки-кандидаты (Camoufox/rebrowser-patches/ghost-cursor…), anti-detection tips, жёсткая политика (капчи агент решает сам если может — 29.09; платное — finance-гейт; SMS/номера и аккаунты/цифра из РФ — owner-канал 365sms/Funpay/Lolz). Загружать когда: линия уперлась в bot-wall/детекцию, мультиаккаунтная или прокси-задача, выбор stealth-подхода, прогрев аккаунтов, скрейпинг с маскировкой фингерпринта.

## Headed browser = owner-only surface (owner directive 16.09.2026)

The VISIBLE (headed) browser window is opened ONLY for the owner to act with their own hands — registrations, logins bound to identity, payments, KYC.
The fleet NEVER drives the headed window for routine work and never opens headed windows on its own initiative beyond handing the page to the owner.

- Launch pattern: separate user-data-dir `C:\Users\max\Desktop\Fleet-Browser\profile-visible` + `--remote-debugging-port=9333` + `--new-window` (NO --headless). Standard fleet browser stays headless on 9222 with `profile`.
- The two profiles are isolated: a login made in profile-visible is NOT visible to the headless fleet profile. VERIFIED WORKING reuse (16.09, Klipni): launch a HEADLESS Edge instance on `profile-visible` itself — `--headless=new --remote-debugging-port=9334 --user-data-dir=...profile-visible` — the on-disk session is picked up, no visible window. Prerequisite: the headed window on that profile must be closed first (SingletonLock; profile serves one Edge instance at a time). NOT working: copying/decrypting cookies (DPAPI+AES-GCM) into another profile via CDP — __Host-/__Secure- prefixed session cookies get rejected or don't stick ("Sanitizing cookie failed" / silent no-auth). Record which profile holds which account in capabilities notes (Klipni → capabilities/klipni/ACCESS.md).
- Company may read the headed window state (CDP /json/list on 9333, cookies DB read-only) to verify owner actions completed; do NOT click/type in the owner's window without their explicit request.
- When owner finishes a registration, company verifies session persisted (cookie presence), then closes/leaves the window per owner preference.
- Реакция владельца 17.09 (жёсткая, «зачем открыл браузер с головой? не открывай его видимым мне»): headed-окно открывать ТОЛЬКО после явного согласия владельца в текущем диалоге — сначала спросить («нужен ручной вход, открыть окно?»), потом запускать. Молча всплывшее окно = нарушение. После ручного логина сразу вернуть headless (taskkill headful → relaunch --headless=new на том же профиле/порту) и закрыть все следы.

## BrowserOS / BrowserOS neo (owner personal browser, 19.09.2026)

Owner's Comet was fully migrated to BrowserOS (Chromium fork, v0.50.5 = Chromium 151) by profile transplant, not the built-in importer.

- DAILY MCP FIX (19.09, verified): the .lnk-launched chrome starts WITHOUT a debug port, so the app's sidecar can never attach (log loop "Failed to start CDP", cdp port auto-increments 9100→9101→9102 each failed attempt, config.json gets rewritten). Recovery uses the current fleet-bridge launcher and manager-discovered ports; do not manually start a sidecar or pin port 9100. Check the current manager state before a scoped recovery. **PORT ALIGNMENT (19.09, critical): sidecar.json ports MUST equal the extension's expectation — read prefs `browseros.server.server_port` / `mcp_port` / `proxy_port` via chrome.browserOS.getPref from an extension page (current: server=mcp=**9201**, proxy=9200). Mismatch symptoms: Assistant sidepanel renders EMPTY (bodyLen 0), Settings UI shows only built-in BrowserOS provider, new-tab chat shows only web-link cards — while GET /providers on the real port lists everything.** Launcher + owner shortcut «BrowserOS (с MCP).lnk» on Desktop; idempotent (skips chrome/sidecar if already up). MCP daily = **http://127.0.0.1:9201/mcp** (24 tools), health `/health` → cdpConnected:true.
- DAILY CANON (21.09 FINAL, upstream issue #884): the managed CDP server of this BrowserOS build (0.50.5, chromium 151.0.8162.137) serves ONLY /devtools/browser/<id> — NO /json/version — so a bare launch makes the sidecar die "Failed to start CDP" (3 tries, kMaxStartupFailures=3 in browseros_server_manager.cc) and the manager permanently stops until browser restart; providers UI then empty. WORKAROUND = official precedence path from the manager source: launch chrome with explicit --remote-debugging-port=<config.json ports.cdp> (manager logs "Skipping managed CDP server" and chrome's STANDARD DevTools serves /json/version); manager then owns sidecar+proxy+server.json normally. Launch script: fleet-bridge/start-browseros.cmd (reads port from config.json, idempotent via server.json); owner shortcut "BrowserOS (MCP).lnk" -> it. NEVER write config.json/prefs yourself, NEVER run a manual sidecar, NEVER pin ports — the manager resolves and persists them; server port DRIFTS (9201/9202/9200 seen): always read ~/.browseros/server.json (official discovery) and point Hermes mcp_servers.browseros_daily.url there. bind 0x2740 noise right after "CDP WebSocket server requested" = the broken managed bind attempt, harmless on the precedence path. Kill-cycles leave TIME_WAIT on the CDP port which break the next managed bind (SO_EXCLUSIVEADDRUSE) — drain sockets BOTH sides before relaunch.
- DAILY WORKING LAUNCH (21.09 verified, supersedes all below): chrome args = `--remote-debugging-port=<cfg.cdp> --browseros-cdp-port=<cfg.cdp> --remote-allow-origins=* --restore-last-session`. The `--browseros-cdp-port` switch (official, browseros_switches.h) sets `cdp_fixed=true` in ResolvePortsForStartup → manager SKIPS FindAvailablePort ("trust the developer"), which was the race source: without it the manager bumped cdp 9100→9101 while chrome DevTools sat on 9100 → sidecar FATAL. Manager then owns sidecar+proxy+server.json. Script: `fleet-bridge\daily-launch.ps1`. Verify chain: `~/.browseros/server.json` (official discovery) → read server_port from it → GET /health {cdpConnected:true} → GET /providers. Ports DRIFT per session — never hardcode, always read server.json/config.json. Sidecar HTTP: only /health /status /providers answer without Origin; mutating routes (/providers PUT/POST, agent routes) return 403 ForbiddenOrigin — provider/default changes are UI-only (Settings → Providers), don't forge Origin.
- DAILY INCIDENT 21.09 — earlier (superseded) theory: `%UD%\.browseros\config.json` `ports.cdp` is the EXTENSION'S OWN COUNTER — every failed sidecar spawn increments it (9100→9101→…→9104 observed live) and every chrome start the extension ALSO rewrites config (observed: pinned 9100 → back to 9104 within 10s of chrome launch). The sidecar reads config.json and FATALs "Failed to start CDP on port N" unless chrome listens on EXACTLY config.cdp. Hard-pinning 9100 + running a second (bridge) sidecar on 9201 was FIGHTING the extension: my sidecar occupied config.server → extension saw it, drifted cdp → its own sidecars died → UI read config and found an empty port → «провайдеры не грузятся». CORRECT ARCHITECTURE (v3, verified stable 2.5min+ with zero drift): (1) kill all sidecars + daily chrome, (2) READ config.json ports.cdp (whatever the counter says — e.g. 9104), (3) launch chrome headed WITH `--remote-debugging-port=<config.cdp>` + `--restore-last-session`, (4) wait for CDP 200, (5) let the EXTENSION spawn its own sidecar on config.server (fallback: spawn `browseros_server.exe --config %UD%\.browseros\config.json` yourself), (6) verify `/health` cdpConnected:true + `/providers` (4 providers) + config.cdp UNCHANGED (drift = raced, rerun). NEVER pin/rewrite config.json ports — read and follow. Launcher: resolve the current fleet-bridge launcher and owner shortcut on disk before invocation; do not infer filenames or start a replacement browser. Historical launcher names are not a runtime contract. Pitfalls: `/json/version` on a bare-launched chrome's RANDOM port (DevToolsActivePort file) returns 404 — only the ws path answers, that's the tell it's the wrong port; PowerShell 5 Set-Content UTF8 adds BOM (use -Encoding ASCII if you must write JSON); delete stale `%UD%\.browseros\server.lock` before manual sidecar spawns.
- TWO PROVIDER SYSTEMS, don't confuse: (a) pref `browseros.third_party_llm.providers` = simple name+URL cards in the new-tab chat picker (ChatGPT/Claude/Grok/Gemini/Perplexity — just open the sites, NOT API providers); (b) sidecar `/providers` store = real BYOK providers with apiKey, shown in Assistant model switcher + chrome://browseros/settings. The import API writes to (b).
- Assistant sidepanel diagnostics: target chrome-extension://bflpfmnmnokmjhmgnolecpppdbdophmk/sidepanel.html; if body empty it can't reach the sidecar — fix ports, then Page.reload extension targets (sidepanel.html + background.js) via CDP 9100.
- Comet leftovers cleaned 19.09: pref `newtab_page_location_override=https://www.perplexity.ai/...` made every new tab Perplexity — deleted, newtab now chrome://newtab (backup Preferences.pre-newtab-fix). Legacy Comet extensions still installed (Comet, Comet Web Resources, comet-agent) — disable candidates, owner decision pending.
- PROVIDERS via HTTP (no GUI needed): sidecar requires header `Origin: chrome-extension://bflpfmnmnokmjhmgnolecpppdbdophmk` (else Forbidden). `GET /providers`; `POST /providers/import` body `{"providers":[{id,kind:'llm',type,name,modelId,baseUrl,supportsImages,contextWindow,temperature,apiKey?,createdAt,updatedAt}]}` (Zod: id/type/modelId/contextWindow/name required; 200 → {imported:[ids]}); `PUT /providers/default` {providerId}. Providers persist across sidecar restarts. NEVER call `/test-provider` or any inference endpoint on owner keys (owner ban 09.09) — validate keys read-only via provider `/models` instead.
- Configured 19.09 (free tier): default = built-in BrowserOS (Kimi, no key) + Codex ACP + OpenRouter cards (deepseek-v4-flash/qwen3.8-27b/glm-5.2/nemotron-3-ultra/inkling, all :free, key from OPENROUTER_API_KEY) + DashScope qwen3.8-max (openai-compatible, DASHSCOPE_API_KEY). Groq/Mistral keys in .env are DEAD (403/401) — not added. Position NOT wanted by owner.
- neo quirk: `windows` create fails with "No profile available" until ≥1 normal tab exists; create one via CDP PUT `http://127.0.0.1:9110/json/new?about:blank` first. MCP schemas: page=uint32 (not string), evaluate uses `func` or `code` (not `expression`), grep over=ax|content, run takes only {code,timeout}.
- Hermes config (company): mcp_servers.browseros_neo=9210/mcp, browseros_daily uses the manager's discovered current MCP endpoint. Do not treat port 9201 as fixed or edit model/MCP configuration as a browsing fallback; diagnose and use the authorized capability path.
- Install: `%LOCALAPPDATA%\BrowserOS` (daily, owner personal) + `%LOCALAPPDATA%\BrowserClaw` (neo, agent-driven). Shortcuts on Desktop. neo VERIFIED ports (config.json): cdp=9110 proxy=9010 MCP=**9210**.
- daily chrome must NEVER be launched without an explicit `--remote-debugging-port=<config.json ports.cdp>` (read the counter first — it drifts, 9104 as of 21.09): the .lnk default picks a RANDOM port and once grabbed 9222, colliding with fleet Edge (fleet Edge went down 19.09 until relaunched). Use the «BrowserOS (с MCP).lnk» Desktop shortcut (runs fleet-bridge\daily-lane.ps1 via start-browseros-daily.cmd) so chrome lands on the counter port and the app's sidecar connects first try. Re-probe after any restart: `curl http://127.0.0.1:<config.server>/health` + MCP initialize on the same port. Hermes mcp_servers.browseros_daily must point at config.server (9201 as of 21.09); if the counter ever moves the server port, update via `hermes config set`.
- neo MCP E2E VERIFIED 19.09 (browseros-neo v0.0.54, 20 tools): streamable HTTP+SSE at http://127.0.0.1:9210/mcp; echo back `Mcp-Session-Id` from initialize; responses are SSE `data:` lines; send notifications/initialized. WIRED into company config as `mcp_servers.browseros_neo` via `hermes config set` (direct file patch refused; effective after gateway restart).
- neo MCP SCHEMA QUIRKS: `page` = u32 INT (ids from tabs list); `run` takes ONLY {code,timeout}; `grep` over=ax|content; `evaluate` field=`code`; windows close uses `windowId`. `windows create` fails "CDP error: No profile available" when zero tabs — fix: `PUT http://127.0.0.1:9110/json/new?about:blank` first (PUT, GET=405). Fresh neo has no cookies — Google redirects to /sorry captcha (expected).
- Migration artifacts: full backup `Desktop\Comet-Backup-20260919` (855MB, all 3 Comet profiles), clean pre-migration BO profile at `BrowserOS\User Data.pre-migration`, tab safety net `Desktop\comet-open-tabs-20260919.html` (522 URLs).
- PITFALL downgrade reset: Comet=Chromium 152, BrowserOS=151. Raw-copied profile gets its History/Login Data/Cookies RESET on first launch unless `User Data\Last Version` file is rewritten to BrowserOS's version (151.0.8162.137). Done + verified.
- PITFALL headless launches DESTROY owner session state: launching the owner's BrowserOS profile headless (--headless=new on `BrowserOS\User Data`) writes a NEW session over the migrated one and nulls `session.restore_on_startup` in Preferences. NEVER launch the owner's BrowserOS profile headless. Restored from backup; verify-only rule: check files while browser is closed.
- PITFALL editing while running: Preferences/Web Data edits only while ALL BrowserOS chrome.exe processes are dead (else overwritten on exit). Kill by Path -like '*\BrowserOS\Application\*' (tasklist filters misreport; use PowerShell Get-Process).
- DPAPI portability CONFIRMED: Comet had no app-bound encryption (os_crypt key prefix RFBBUEkB = "DPAPI"), same Windows user → passwords/cookies decrypt natively in BrowserOS. Test decrypt SUCCESS before transplant.
- Search engines (configured 19.09): Google = default (guid a974d90f-...), Яндекс = secondary trigger `@yandex` (keywords id 8), Perplexity kept as `@p` (id 2). `restore_on_startup=4` (reopen last session). Preferences backup: `Temp\browseros-install\Preferences.pre-search`.
- Fleet policy: owner's BrowserOS daily profile = OWNER-ONLY surface (personal logins: Gmail, 51 passwords, 2.7k cookies). Fleet must NOT drive it or launch it headless. Fleet lanes stay: headless Edge 9222 (everyday), Donut (anti-detect). neo = agent lane (pilot vs Edge 9222 before replacing it).
- **PILOT VERDICT (24.09, owner question «neo или edge — что оставить основным»): Edge 9222 остаётся ОСНОВНЫМ, neo — резервная линия по требованию.** Evidence: neo-линия дала ТРЕТИЙ отказ того же класса (19-21.09 zombie, 24.09 «browser session not connected» при живых процессах): config.json дрейфнул cdp 9110→9111 и server 9210→9211, headless chrome без `--remote-debugging-address` биндит DevTools ТОЛЬКО на IPv6 ::1 (недостижимо для claw-server на 127.0.0.1), v2-гард с хардкодом 9110 пропускал «здоровье» при сломанной линии. Edge 9222: один фиксированный порт, нативный browser_exec-стек, без sidecar и без дрейфа — аптайм подтверждён. neo MCP (20 инструментов: read/grep/snapshot/pdf/download) ценен, но цена поддержки выше выгоды для рутины. Автостарт neo ВЫКЛЮЧЕН (vbs в Startup\Disabled-autostart) — не включать; при необходимости поднять одной командой: `cmd /c %LOCALAPPDATA%\BrowserClaw\fleet-bridge\start-neo-headless.cmd` (v3, 24.09: читает cdp/server из config.json — порты ДРЕЙФУЮТ, пинит `--remote-debugging-address=127.0.0.1`, health = C IPv4 + MCP 9210; exit 3 = server-порт удрал с 9210, нужен realign mcp_servers.browseros_neo). После ручного старта neo проверять: `mcp__browseros_neo__tabs` отвечает списком вкладок.
- AUTOSTART (19.09, owner scope = neo ONLY): `Startup\BrowserOS_neo.vbs` (silent, Fleet_Browser.vbs pattern) → `%LOCALAPPDATA%\BrowserClaw\fleet-bridge\start-neo-headless.cmd`. Launcher v2 (21.09): liveness guard checks **CDP 9110 (v4+v6), NOT MCP 9210** — incident 19-21.09: headless neo chrome lost its DevTools listener (zombie alive, `bind() error 0x2740` in debug.log) while claw-server kept answering on 9210, so the old 9210-guard no-op'd and MCP stayed dead ~1.5 days. v2 on dead CDP: runs `kill-neo-stale.ps1` (kills chrome filtered by *BrowserClaw* cmdline + claw-server; never touches owner daily BrowserOS), relaunches chrome, waits CDP up to 60s, then ensures claw-server (reads `current_version` for the bin path). Pitfalls fixed in v2: `--user-data-dir` with space must be ONE quoted arg (split args → "Multiple targets are not supported in headless mode" crash loop in debug.log); `timeout /t` hangs without console stdin under PowerShell → use `ping -n N 127.0.0.1`; `start` without `/b ... <NUL >NUL` keeps the parent pipe open (git-bash/PowerShell call appears to hang forever even though chrome started fine); use delays via ping and detached redirects. Health probe after anything: `curl http://127.0.0.1:9110/json/version` then MCP initialize on 9210 (20 tools). VERIFIED: headless neo = fully functional agent lane (no window at login, claw-server self-attaches, MCP 9210 alive, Hermes-native mcp__browseros_neo__tabs works).
- DAILY BrowserOS is NOT autostarted BY DESIGN: owner-only personal profile — headless launch destroys the owner session (pitfall above) and a headed auto-pop at login violates the owner directive (17.09). daily MCP is ON-DEMAND via the «BrowserOS (с MCP).lnk» desktop shortcut (chrome 9100 + sidecar 9201). After a reboot: neo + fleet Edge + Donut come up automatically; daily MCP only when the owner opens BrowserOS through the MCP shortcut.
- PROVIDER TROUBLESHOOTING (21.09, owner «провайдеры неправильно работают»): lane healthy ≠ providers work. Diagnose by reading sidecar log `%UD%\.browseros\browseros-server.log` for `"msg":"Agent stream failed"` — it carries the upstream error verbatim. Two findings: (1) **DashScope CN vs INTL are DIFFERENT accounts** — Hermes company uses `https://dashscope.aliyuncs.com/compatible-mode/v1` (CN) with a 35-char sk- key (verified HTTP 200); BrowserOS had `dashscope-intl.aliyuncs.com` (INTL) with a different 117-char key → `403 AllocationQuota.FreeTierOnly`. The CN key is `invalid_api_key` on INTL and vice versa — never mix endpoint and key. (2) **OpenRouter `:free` models mostly don't support tool use** → `404 No endpoints found that support tool use` → Agent mode dead with them; only paid/tool-capable OpenRouter models work in Agent mode.
- CODEX PROVIDER `hasApiKey:False` IS NORMAL, not a missing credential: Codex in BrowserOS is an ACP/OAuth provider, `api_key` column is NULL by design. Real cred = `~/.codex/auth.json` (ChatGPT OAuth). Per official code: `codex-home.ts` builds a CODEX_HOME overlay (symlink farm over `~/.codex`, regenerates config.toml to disable `browser@openai-bundled`), `launcher.ts` spawns the adapter via bundled bun (`resources\bin\third_party\bun.exe x --package <acp-spec>`) which reads auth from that home; falls back to real `~/.codex` if the overlay fails. Verify without reading secrets: `codex login status` → "Logged in using ChatGPT"; sidecar log shows `"agent":"codex"..."Installed BrowserOS MCP into agent"` + `"type":"codex","msg":"ACP agent created"`. So: don't chase a missing key for Codex; if Codex chat fails it's subscription/model-side, not cred-side.
- KEY PROBING PITFALL (21.09, cost an hour): when testing a provider key with curl/urllib, a wrong Authorization header (`***`+key instead of `Bearer `+key) yields 401 and looks like a dead key. Always verify header construction first; a `401 invalid_api_key` on the endpoint whose key you meant to test may be YOUR bug, not the key's.
- BYOK providers: add via sidecar HTTP `POST /providers/import` (see PROVIDERS block above) — NOT GUI-only. The encrypted extension leveldb (`Local Extension Settings`) must still never be injected directly. GUI path (chrome://browseros/settings) is the owner fallback. Provider types supported: browseros(built-in Kimi K2.5 free), chatgpt-pro/github-copilot/qwen-code (OAuth device-code), openai/anthropic/google/openrouter/moonshot/azure/bedrock/openai-compatible (api-key), ollama/lmstudio (local). Chat mode works with local models (context ≥15-20K tokens); Agent mode needs cloud models. Secret handoff without chat: powershell Set-Clipboard from env var (Desktop\copy-provider-key.ps1), owner pastes — or write via import API reading key from .env in-process (never printed).

## Captcha & phone policy (owner approval 18.09, EXTENDED 29.09.2026)

Fleet-wide standing permission (29.09): agents MAY solve captchas themselves when they are able to — checkbox ticks (SmartCaptcha «Я не робот», reCAPTCHA v2 — via a real CDP mouse click, NOT JS .click()) AND image/text/slider challenges solved by the agent's own capability (vision/logic), without paid services. Lower challenge probability first: donut profile + clean IP/proxy + human-like delays. Record the solve fact in the task's evidence.

Money: paid solving services (2Captcha/CapSolver etc.) — only through the finance gate (`gate:finance=pass` + `decision:company=go`), when the agent itself failed and the task is worth it.

Phone/SMS: NOT solved autonomously — owner channel. The owner buys numbers/SMS on **365sms.vip** and provides account access on request. Need a number/code → ONE escalation touchpoint with exact spec (service, country/number, budget, where to deliver the code). Fleet phone +79009666092 stays for owner-bound flows (VK, directive 23.09).

Accounts / digital goods that cannot be bought directly from RF: the owner purchases on **Funpay, Lolz** and similar marketplaces. Fleet escalates with an exact spec (item, parameters, budget, handoff); received items are onboarded via `web-account-onboarding`/vault with provenance=owner-purchased. Fleet does NOT buy accounts on its own (spend + ownership risk).

## YouTube не ходит через VPN incy — рабочий путь = SOCKS через Timeweb VDS (23.09.2026)

Владелец-VPN incy (TUN `wwan99` 198.18.0.1 + прокси 127.0.0.1:10809 HTTP / 10808 SOCKS, выход DE netcup 159.195.42.172) пропускает google.com и instagram.com (200), но ВСЕ youtube.com-хосты (www/studio/upload/youtu.be/m./music.) — TCP timeout 20s, и через TUN, и через прокси. DNS не виноват (DoH Cloudflare/Google дают Status 0 + реальные IP 142.251.x). Причина: датацентровый выход блокируется YouTube-антиботом + QUIC/HTTP3 в браузере владельца идёт другим путём, а curl/yt-dlp ходят TCP.

Директива владельца: «через VPN не работает — не дрочить его, найти простой рабочий путь». VPN НЕ чинить/не настраивать.

**Рабочий путь — SOCKS через наш Timeweb VDS (0 ₽, уже оплачен):**
```
ssh -b 192.168.31.141 -f -N -D 127.0.0.1:10810 timeweb-rr
# далее любой инструмент:
curl --socks5-hostname 127.0.0.1:10810 https://www.youtube.com/
yt-dlp --proxy socks5://127.0.0.1:10810 <url>
```
Evidence (23.09): youtube.com 200 + <title>YouTube</title>, studio.youtube 302, accounts.google 302, www.googleapis.com/upload/youtube 401 (живой, ждёт токен), myaccount.google.com/brandaccounts 302. Привязка к Wi-Fi `-b 192.168.31.141` обязательна (egress-ловушка 20.09 — через VPN wwan99 SSH до VDS таймаутит).

Google/instagram/TikTok/Pinterest/VK работают и напрямую (без туннеля) — туннель нужен ТОЛЬКО для youtube.com. Браузер Edge CDP 9222 (start-fleet-browser.cmd) для YouTube-задач тоже упрётся в тот же TCP-timeout — поднимать SOCKS-туннель и проксировать, либо гонять YouTube-задачи через VDS.

## Evaluated and rejected: Perplexity Comet (30.08.2026)

Comet (Chromium 151.0.7922.249) was live-tested as an alternative default:
headless + CDP fully works — `/json/version`, `/json`, new-tab navigation,
JS eval, screenshots all PASS (test port 9333). Technically browser-use could
drive it. Rejected as default anyway:

- In headless it auto-opens a `perplexity.ai/sidecar` tab and attempts GCM
  registration (telemetry phone-home) — extra noise, network traffic and
  fingerprint baggage in the shared fleet profile.
- Its built-in Perplexity agent is not something the fleet controls or needs;
  as a bare Chromium shell it equals Edge but ships a non-enterprise updater
  (CometUpdater) and Perplexity account hooks.
- Product risk record (CometJacking hijack vuln, Amazon federal injunction
  03.2026 against Comet's auto-purchases) — caution signal, not our lane.

Default stays headless Edge; Donut stays the only anti-detect lane.
(An older Temp\comet_cdp.py note claimed Comet has no `/json` — that was
wrong; with `--remote-debugging-port` it serves standard CDP HTTP.)
