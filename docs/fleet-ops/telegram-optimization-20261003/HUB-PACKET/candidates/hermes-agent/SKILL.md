---
name: hermes-agent
description: "Configure, extend, theme, and troubleshoot Hermes Agent."
version: 3.2.0
author: Hermes Agent + Teknium
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, setup, configuration, multi-agent, spawning, cli, gateway, bots, bot-mode, features, themes, skins, desktop-plugins, tui-widgets, petdex, development]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [claude-code, codex, opencode]
---
# Hermes Agent

> Extended triggers: "Use, configure, theme, extend, and orchestrate Hermes Agent."

Hermes Agent — open-source AI-agent framework by Nous Research (terminal, native desktop app, messaging platforms, IDEs; any LLM provider; Linux/macOS/Windows/WSL). Full identity, differentiators and feature scope: `references/product-overview.md`.

**This skill is a hub.** The body covers identity, quick start, spawning/orchestration, and hard invariants. Everything else lives in reference files — **load the matching reference (below) before answering**; do not answer detail questions from the body alone.

**Docs:** https://hermes-agent.nousresearch.com/docs/

## Scope & Verification (invariant — full text moved to `references/product-overview.md`)

This skill is a concise operating guide, not the complete source of truth. A feature missing here is NOT evidence it does not exist. Cheapest verification first: **https://hermes-agent.nousresearch.com/docs/llms.txt** (one line per shipped feature, never behind the product; whole set at `/docs/llms-full.txt`; fetch via `web_extract` or curl), then `hermes --help` / `hermes <command> --help`, then the source tree https://github.com/NousResearch/hermes-agent. **Never answer "Hermes can't do that" from memory.**

## Routing Table — load the reference for the task

| User wants... | Load |
|---|---|
| **Anything not listed below — "can Hermes do X?", "how do I set up X?"** | **https://hermes-agent.nousresearch.com/docs/llms.txt** |
| Bots that chat, run routines, or message each other; the Bots tab | docs: `/user-guide/bot-mode` |
| CLI commands, subcommands, flags, "how do I run X" | `references/cli-reference.md` |
| In-session slash commands | `references/slash-commands.md` |
| Provider setup, API keys, OAuth | `references/providers-and-models.md` |
| config.yaml sections, toolsets, voice/STT/TTS | `references/configuration.md` |
| AGENTS.md / .hermes.md / CLAUDE.md project rules | `references/project-context-files.md` |
| Secret redaction, PII, approval modes, "reset permissions" | `references/security-privacy.md` |
| Delegation, cron, curator, kanban | `references/background-systems.md` |
| MCP servers (add, catalog, `hermes mcp`) | `references/native-mcp.md` |
| Webhook routes and event-driven runs | `references/webhooks.md` |
| A custom theme/skin ("synthwave theme", "change the gold ●") | `references/themes.md` + `templates/skin.yaml` |
| A desktop app UI element (pane, widget, ⌘K command, page) | `references/desktop-plugins.md` + `templates/plugin.js` |
| A live TUI panel or modal widget (ticker, clock, dashboard) | `references/tui-widgets.md` + `templates/clock.mjs` |
| Pet mascots — install, select, scale, diagnose | `references/petdex.md` |
| Windows-specific issues (keybinds, WinError 10106, BOM) | `references/windows-quirks.md` |
| Windows PM tool integrity / partial Desktop update | `references/windows-pm-update-recovery.md` |
| Debugging: voice, tools missing, gateway, aux models | `references/troubleshooting.md` |
| Contributing code: adding tools, slash commands, tests | `references/contributor-guide.md` |
| delegate_task "capped at N" reports | `references/delegate-task-concurrency-diagnosis.md` |
| "Can app X use my Nous Portal subscription/OAuth?" | `references/portal-auth-for-third-party-apps.md` |
| What Hermes is, differentiators, surfaces (desktop/dashboard/TUI/proxy) | `references/product-overview.md` |
| Install, quick start, key paths (`~/.hermes`, `$HERMES_HOME`, profiles) | `references/quickstart-and-paths.md` |
| Spawning extra Hermes processes (one-shot, tmux PTY, multi-agent, resume) | `references/spawning-instances.md` |
| Connecting a messaging platform (Telegram, Discord, Slack, WhatsApp, …) | docs: `/user-guide/messaging` |

The reference list above is not the feature list — it is the set of topics that
need more than their docs page. For everything else Hermes ships, fetch
`llms.txt` and it maps the question to the page that answers it.

Two theming rules that hold even without loading the reference: **you apply skins yourself** (`hermes config set display.skin <name>` — every surface repaints live within ~a second; don't tell the user to run `/skin`), and **to tweak one color, edit the ACTIVE skin** (`hermes skin set <key> <hex>`) — never fork `default`, which drops the palette and resets the background.

## Hub pointers (depth moved to topic references — load on demand)

- **Install / quick start / key paths** (`~/.hermes`, `config.yaml`, `.env`, state.db, sessions, logs, auth.json, profiles) → `references/quickstart-and-paths.md`. Invariant: when a profile is active, resolve the real home from `$HERMES_HOME` — never hardcode `~/.hermes`.
- **Spawning additional Hermes instances** (fully independent subprocesses; one-shot `hermes chat -q`; interactive tmux PTY; multi-agent coordination; session resume; delegate_task-vs-spawn table) → `references/spawning-instances.md`. Prefer `delegate_task` for quick subtasks; for scheduled tasks use the `cronjob` tool instead of spawning.
- **Surfaces** (desktop app, web dashboard, Ink TUI, OpenAI-compatible proxy) and **product overview / differentiators / scope-and-verification full text** → `references/product-overview.md`.

## Hard Invariants (never violate, regardless of what you loaded)

- **Never break prompt caching** — don't change past context, toolsets, or the system prompt mid-conversation. The only exception is context compression.
- **Message role alternation** — never two assistant or two user messages in a row; only `tool` results can repeat.
- **Secrets in `.env`, settings in `config.yaml`** — never tell a user to put a non-credential setting in `.env`.
- **Profile-safe paths** — `get_hermes_home()` in code, `$HERMES_HOME` when resolving paths in a session.
- **Never hand-edit `config.yaml` for the user** — use `hermes config set KEY VAL`; a stray indent can corrupt the file and break the live gateway.
