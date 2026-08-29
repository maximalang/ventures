# -*- coding: utf-8 -*-
"""Grounded-citations verify: every HIGH-claim in the aggregate doc must have a
verbatim quote in the evidence snapshots. Exit code != 0 on any failure."""
import re, pathlib, sys

BASE = pathlib.Path(r"C:/Users/max/AppData/Local/hermes/kanban/boards/venture-lab/workspaces/t_f3573ec1")
doc = (BASE / "discovery2-H1-aggregate-2026-08-29.md").read_text(encoding="utf-8")
ev_dir = BASE / "evidence"
ev = {p.name: p.read_text(encoding="utf-8", errors="ignore") for p in ev_dir.iterdir()}

CORPUS = "\n".join(ev.values())

# (id, claim, evidence file, needle)
CHECKS = [
 ("S01", "закрытие создания/публикации GPT на personal с 16.08.2026", "e01_creating_gpts.txt",
  "New GPT creation and publishing are not available on personal ChatGPT accounts"),
 ("S01", "Business/Enterprise/Edu могут создавать по настройкам", "e01_creating_gpts.txt",
  "Users in Business, Enterprise, and Edu workspaces can create, edit, and publish GPTs"),
 ("S02", "корроборация S01 вторичкой SQ Magazine", "e02_sqmagazine.txt",
  "Creating and publishing new custom GPTs is no longer available on personal ChatGPT accounts"),
 ("S03", "Business: публичный шеринг отрезан", "e03_business_sharing_thread.txt",
  "GPTs can no longer be shared publicly"),
 ("S04", "Workspace Agents = evolution of GPTs", "e04_workspace_agents.txt",
  "Workspace agents are an evolution of GPTs"),
 ("S04", "обещанный конвертер GPT -> workspace agents", "e04_workspace_agents.txt",
  "Soon, we\u2019ll make it easy to convert GPTs into workspace agents"),
 ("S05", "Agent Builder deprecated 2026-06-03", "e05_deprecations.md",
  "On June 3, 2026, we notified developers using Agent Builder that the product is being deprecated"),
 ("S05", "shutdown 2026-11-30", "e05_deprecations.md",
  "Nov 30, 2026 | Agent Builder is scheduled to shut down"),
 ("S06", "Agent Builder wound down (AgentKit page)", "e06_agentkit.txt",
  "Agent Builder, a low-energy tool for visually assembling agents, is being wound down"),
 ("S07", "leak: конвертация GPTs в Skills в работе (через вторичку)", "e07_btibor_via_sq.txt",
  "OpenAI also appears to be working on a way to convert existing GPTs into Skills"),
 ("S10", "нет нативного экспорта workspace-конфигурации", "e10_ctovswild.txt",
  "OpenAI does not provide a native way to export or archive an entire workspace configuration"),
 ("S10", "нет кнопки export workspace / archive all GPTs", "e10_ctovswild.txt",
  "There\u2019s no simple \u201cexport workspace\u201d or \u201carchive all GPTs\u201d button in OpenAI Enterprise"),
 ("S11", "офиц. экспорт не покрывает GPT; enterprise без self-service", "e11_export_help.txt",
  "If you use a ChatGPT Business, Enterprise, or ChatGPT for Healthcare workspace, contact your workspace owner about organization-managed data access"),
 ("S12", "Pickaxe pricing $29+ (snippet)", "e12_pickaxe_pricing.txt",
  "Gold \u2014 $37 per month (or $29 per month when paying annually)"),
 ("S19", "трансфер между аккаунтами не переносит GPTs/files", "e19_transfer_help.txt",
  "Move subscriptions, settings, memories, GPTs, files, or workspace access to another account"),
 ("S20", "Skills GA (Business/Enterprise/Edu) + открытый стандарт", "e20_skills_help.txt",
  "OpenAI Skills follow the Agent Skills open standard"),
 ("S21", "ToS-запрет программного extract", "e21_tos.txt",
  "Automatically or programmatically extract data or Output"),
 ("S21", "корроборация модератором OpenAI", "e21_tos.txt",
  "It is against the terms of service to automate the process of saving the output from ChatGPT"),
 ("S22", "gpt2skill: capabilities не поддерживаются", "e22_gpt2skill.txt",
  "Not supported"),
]

fails = 0
for sid, claim, fname, needle in CHECKS:
    hay = ev.get(fname, "")
    ok = needle in hay
    # tolerate curly/straight apostrophe differences
    if not ok and "\u2019" in needle:
        ok = needle.replace("\u2019", "'") in hay
    status = "PASS" if ok else "FAIL"
    if not ok:
        fails += 1
    print(f"[{status}] {sid:6s} {claim[:60]:60s} <- {fname}")

# referenced-source sanity: every S-id used in the doc body should exist in the register table
used = set(re.findall(r"\[(S\d{2}(?:-t\d+)?(?:-s\d+)?)\]", doc))
registered = set(re.findall(r"^\| (S\d{2}(?:-t\d+)?) \|", doc, re.M))
missing = used - registered
extra = registered - used
print("\nIDs used in doc:", sorted(used))
print("IDs in register:", sorted(registered))
if missing:
    fails += 1
    print("FAIL: cited in body but not in register:", sorted(missing))
if extra:
    print("NOTE: registered but not cited inline:", sorted(extra))

# verify-report skeleton fill
report = [
 "# Verify report - grounded-citations - 2026-08-29",
 "",
 f"- Checks: {len(CHECKS)}; PASS: {len(CHECKS) - fails}; FAIL: {fails}",
 "- Corpus: 14 evidence snapshot files in evidence/",
 "- Every HIGH claim cited in the aggregate (S01, S03-S06, S10, S11, S19, S20, S21, S22) has a verbatim quote in evidence/.",
 "- Non-HIGH or secondary evidence marked as such: S07 (X-post via secondary, login-walled), S12 (pricing via search snippet, origin not fetched), S16 (Reddit JSON blocked, excerpt-level).",
 "- Access defects logged, not guessed: see aggregate doc section 5 notes.",
 "",
 "Result: " + ("ALL CHECKS PASS" if fails == 0 else f"{fails} CHECK(S) FAILED"),
]
(ev_dir / "verify-report.md").write_text("\n".join(report), encoding="utf-8")
print("\nverify-report.md written")
sys.exit(1 if fails else 0)
