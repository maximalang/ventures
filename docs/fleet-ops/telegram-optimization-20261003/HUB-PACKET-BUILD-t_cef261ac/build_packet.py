# -*- coding: utf-8 -*-
"""Build HUB-PACKET for t_cef261ac: compact candidates for two company skill hubs.

SOURCE-ONLY: reads live skill bytes read-only, writes packet under workspace.
Verbatim moves are programmatic slices of the anchored source; corrections are
surgical string replacements recorded in INVARIANT-MAP.json.
"""
import hashlib
import json
import shutil
from pathlib import Path

SKILLS = Path(r"C:/Users/max/AppData/Local/hermes/profiles/company/skills")
HA_DIR = SKILLS / "autonomous-ai-agents" / "hermes-agent"
FTE_DIR = SKILLS / "fleet-ops" / "fleet-token-economy"
WS = Path(r"C:/Users/max/AppData/Local/hermes/kanban/boards/fleet-ops/workspaces/t_cef261ac")
PKT = WS / "HUB-PACKET"

HA_SRC = (HA_DIR / "SKILL.md").read_bytes().decode("utf-8")
FTE_SRC = (FTE_DIR / "SKILL.md").read_bytes().decode("utf-8")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())


def slice_between(text, start, end=None, name=""):
    assert text.count(start) == 1, f"start marker not unique ({name}): {start[:60]!r} x{text.count(start)}"
    i = text.index(start)
    if end is None:
        return text[i:]
    assert text.count(end) == 1, f"end marker not unique ({name}): {end[:60]!r} x{text.count(end)}"
    j = text.index(end)
    assert j > i, f"end before start ({name})"
    return text[i:j]


def frontmatter(text):
    assert text.startswith("---\r\n") or text.startswith("---\n")
    nl = "\r\n" if text.startswith("---\r\n") else "\n"
    idx = text.index(nl + "---" + nl, 3)
    return text[: idx + len(nl) + 3 + len(nl)]


def crlf(s: str) -> str:
    """Normalize authored text to CRLF (house style of both anchored sources)."""
    return s.replace("\r\n", "\n").replace("\n", "\r\n")


# ---------------------------------------------------------------- source slices
ha = {}
ha["fm"] = frontmatter(HA_SRC)
ha["title_block"] = slice_between(HA_SRC, "# Hermes Agent", "Hermes Agent is an open-source", "ha.title")
ha["intro"] = slice_between(HA_SRC, "Hermes Agent is an open-source", "**This skill is a hub.**", "ha.intro")
ha["hub_decl"] = slice_between(HA_SRC, "**This skill is a hub.**", "## Scope & Verification", "ha.hubdecl")
ha["scope"] = slice_between(HA_SRC, "## Scope & Verification", "## Quick Start", "ha.scope")
ha["quickstart"] = slice_between(HA_SRC, "## Quick Start", "## Key Paths", "ha.qs")
ha["keypaths"] = slice_between(HA_SRC, "## Key Paths", "## Routing Table", "ha.kp")
ha["routing"] = slice_between(HA_SRC, "## Routing Table", "## Spawning Additional Hermes Instances", "ha.rt")
ha["spawning"] = slice_between(HA_SRC, "## Spawning Additional Hermes Instances", "## Surfaces (quick orientation)", "ha.spawn")
ha["surfaces"] = slice_between(HA_SRC, "## Surfaces (quick orientation)", "## Hard Invariants", "ha.surf")
ha["invariants"] = slice_between(HA_SRC, "## Hard Invariants", None, "ha.inv")

fte = {}
fte["fm"] = frontmatter(FTE_SRC)
fte["title_class"] = slice_between(FTE_SRC, "# Fleet Token Economy", "## Measure first (never guess)", "fte.title")
fte["measure"] = slice_between(FTE_SRC, "## Measure first (never guess)", "## Levers (typical impact order)", "fte.measure")
fte["levers"] = slice_between(FTE_SRC, "## Levers (typical impact order)", "## Mechanics & pitfalls", "fte.levers")
fte["lever4"] = slice_between(FTE_SRC, "4. **Reasoning effort", "5. **Skills index**", "fte.lever4")
fte["mechanics"] = slice_between(FTE_SRC, "## Mechanics & pitfalls", "## Routing-audit safeguards", "fte.mech")
fte["rsa"] = slice_between(FTE_SRC, "## Routing-audit safeguards", "## From audit to program", "fte.rsa")
fte["program"] = slice_between(FTE_SRC, "## From audit to program", "## Prompt-audit \u043b\u0435\u0439\u043d", "fte.prog")
fte["prompt_audit"] = slice_between(FTE_SRC, "## Prompt-audit \u043b\u0435\u0439\u043d", "## Support files", "fte.pa")
fte["support"] = slice_between(FTE_SRC, "## Support files", None, "fte.sup")

# ------------------------------------------------------------------- corrections
CORRECTIONS = {
    "C1a": {
        "skill": "fleet-token-economy",
        "before": "are IGNORED by the current kernel",
        "after": ("are ignored by the bare kernel (UPDATE 2026-10-03 per evidence-root DECISION-AND-CONTRACT.md: "
                  "plugin hermes-session-reset-policy 0.3.0 IS installed on this host and implements session_reset \u2014 "
                  "the old blanket \u00abreset keys are inert\u00bb advice is incomplete here; owner directive 2026-10-03: "
                  "do NOT shorten/reset/archive sessions as an economy shortcut \u2014 this correction is not a permission "
                  "to reset/restart)"),
        "rationale": "Obsolete blanket default must not override active owner directive; contract line 13 documents installed reset-policy plugin.",
        "evidence": "DECISION-AND-CONTRACT.md \u00a7'Evidence already collected' line 13; profiles/company/plugins/hermes-session-reset-policy exists (ls).",
        "dest": "references/levers-playbook.md",
    },
    "C1b": {
        "skill": "fleet-token-economy",
        "before": "(grep it in config_defaults.py / runtime)",
        "after": "(grep it in config_defaults.py / runtime / installed plugins)",
        "rationale": "Consumer verification must include installed plugins, not only kernel source.",
        "evidence": "DECISION-AND-CONTRACT.md line 13 + line 17 ('Check installed consumers, not documentation alone').",
        "dest": "references/levers-playbook.md",
    },
    "C2": {
        "skill": "fleet-token-economy",
        "before": "config applies to NEW sessions only;",
        "after": ("application varies per key \u2014 \u00abNEW sessions only\u00bb is not blanket-true (UPDATE 2026-10-03: the official "
                 "configuration snapshot in the evidence root documents gateway hot-reload of compression/context length; "
                 "verify the installed consumer for the specific key);"),
        "rationale": "PRODUCT-BRIEF.md: fix obsolete blanket advice about 'only new sessions'; hot reload must be checked against installed consumer.",
        "evidence": "hermes-configuration-official.txt line 2532 'Gateway hot-reload of compression and context length'; PRODUCT-BRIEF.md \u00a7delta.",
        "dest": "references/mechanics-pitfalls.md",
    },
}


def apply_corrections(text, ids):
    for cid in ids:
        c = CORRECTIONS[cid]
        assert text.count(c["before"]) == 1, f"correction anchor not unique: {cid}"
        text = text.replace(c["before"], c["after"])
    return text


# --------------------------------------------------------------- authored pieces
HA_IDENTITY = """Hermes Agent \u2014 open-source AI-agent framework by Nous Research (terminal, native desktop app, messaging platforms, IDEs; any LLM provider; Linux/macOS/Windows/WSL). Full identity, differentiators and feature scope: `references/product-overview.md`.

"""

HA_SCOPE_SUMMARY = """## Scope & Verification (invariant \u2014 full text moved to `references/product-overview.md`)

This skill is a concise operating guide, not the complete source of truth. A feature missing here is NOT evidence it does not exist. Cheapest verification first: **https://hermes-agent.nousresearch.com/docs/llms.txt** (one line per shipped feature, never behind the product; whole set at `/docs/llms-full.txt`; fetch via `web_extract` or curl), then `hermes --help` / `hermes <command> --help`, then the source tree https://github.com/NousResearch/hermes-agent. **Never answer "Hermes can't do that" from memory.**

"""

HA_ROUTING_ANCHOR = "| Connecting a messaging platform (Telegram, Discord, Slack, WhatsApp, \u2026) | docs: `/user-guide/messaging` |\n"
HA_ROUTING_NEW_ROWS = """| What Hermes is, differentiators, surfaces (desktop/dashboard/TUI/proxy) | `references/product-overview.md` |
| Install, quick start, key paths (`~/.hermes`, `$HERMES_HOME`, profiles) | `references/quickstart-and-paths.md` |
| Spawning extra Hermes processes (one-shot, tmux PTY, multi-agent, resume) | `references/spawning-instances.md` |
"""

HA_POINTERS = """## Hub pointers (depth moved to topic references \u2014 load on demand)

- **Install / quick start / key paths** (`~/.hermes`, `config.yaml`, `.env`, state.db, sessions, logs, auth.json, profiles) \u2192 `references/quickstart-and-paths.md`. Invariant: when a profile is active, resolve the real home from `$HERMES_HOME` \u2014 never hardcode `~/.hermes`.
- **Spawning additional Hermes instances** (fully independent subprocesses; one-shot `hermes chat -q`; interactive tmux PTY; multi-agent coordination; session resume; delegate_task-vs-spawn table) \u2192 `references/spawning-instances.md`. Prefer `delegate_task` for quick subtasks; for scheduled tasks use the `cronjob` tool instead of spawning.
- **Surfaces** (desktop app, web dashboard, Ink TUI, OpenAI-compatible proxy) and **product overview / differentiators / scope-and-verification full text** \u2192 `references/product-overview.md`.

"""

FTE_MEASURE = """Never guess \u2014 measure. Full commands, caveats and tested SQL for every item: `references/measure-first-details.md` (+ `references/audit-recipes.md`).

1. `hermes insights --days N` \u2014 raw input/output tokens, model/platform/tool/skill breakdowns; "Total tokens" includes context re-transmission/cache; frame `subscription_included` as quota/latency, not invoice.
2. `hermes prompt-size --json` \u2014 fixed per-prompt budget (system, skills index, memory, profile, tool schemas); every disabled skill shrinks EVERY future prompt.
3. Per-profile `state.db` read-only (`file:...?mode=ro`): `sessions`, `messages.tool_calls`, `session_model_usage` \u2014 daily-slice PITFALL (cumulative rows, new/carry split, provider health from logs) in `references/measure-first-details.md`.
4. `hermes cron list` \u2014 `deliver` targets, `last_delivery_error`; `Mode: no-agent` jobs cost zero tokens, agent-mode jobs run a FULL agent turn per fire.
5. **Wasted-turn audit** \u2014 repeat loops + error turns via state.db scans: recipes in `references/measure-first-details.md` and `references/audit-recipes.md`.

"""

FTE_LEVERS_A = """1. **Session hygiene** \u2014 biggest free lever for interactive chats: `/new` after big tasks; archive/delete/prune dead sessions; cron/kanban always start fresh sessions. Per-key pitfalls \u2014 incl. UPDATED session_reset / reset-policy-plugin facts and the owner ban on reset-as-economy \u2014 in `references/levers-playbook.md`.
2. **MoA fan-out** \u2014 each user turn pays reference models + aggregator; real switch is preset-level: `hermes config set moa.presets.default.enabled false` (pitfalls in `references/levers-playbook.md`).
3. **Compression** \u2014 `hermes config set compression.protect_last_n / target_ratio / protect_first_n`.
"""

FTE_LEVERS_B = """5. **Skills index** \u2014 disable never-loaded skills via `skills.disabled` (reversible, per-profile scope); measured numbers, quarantine variant and tiering in `references/levers-playbook.md` + `references/mechanics-pitfalls.md`.
6. **Cron delivery targets** \u2014 `bot-chat:<profile>` resumes that profile's Bot Chat session and runs a FULL agent turn every fire; drop it when the real channel is Telegram.

Full lever text with every measured number and pitfall: `references/levers-playbook.md`.

"""

FTE_MECHANICS = """## Mechanics & pitfalls \u2014 always-on safety subset (full list: `references/mechanics-pitfalls.md`)

- **Config writes:** `patch`/`write_file` on a profile config.yaml is refused by the agent guard \u2014 always use `hermes config set key value` via terminal. Take a timestamped backup copy first; verify each value with `hermes config get`.
- **Unknown-key warning matters:** if `hermes config set` says a key is "not recognized", the intended consumer may not read that path \u2014 verify in installed source/plugins before claiming the change works.
- **fleet-policy:** direct sqlite reads of kanban.db and the sessions dir are blocked \u2014 use `kanban_*` tools and `hermes sessions ...` CLI. Read-only `mode=ro` queries on `state.db` pass.
- **Skill body size is a per-load cost:** keep only always-on rules in SKILL.md, depth in on-demand `references/`; rank skills by weekly injection = loads \u00d7 chars/4.

"""

FTE_LANES = """## Deep lanes (load the reference on demand)

- **Routing/provider audit safeguards** (catalog vs primary/fallback slots, configured vs effective reasoning, `cost_status` semantics, usage scopes, Windows `where.exe hermes` discovery) \u2192 `references/routing-audit-safeguards.md`.
- **From audit to program** (freeze baseline + boundary snapshot of cumulative counters BEFORE levers deploy; per-lever revertible kanban cards; per-profile LOADED readback; weekly no-agent delta cron; money stays `null` without pricing; window-compression procedure) \u2192 `references/audit-to-program.md`.
- **Prompt-audit \u043b\u0435\u0439\u043d** (\u043a\u0430\u043d\u043e\u043d 25.09: `profiles/company/scripts/prompt_audit.py`, daily no-agent cron `d341b0d4a136`, \u0440\u0443\u0431\u0440\u0438\u043a\u0438 P1/P2/P3/P5, anti-noise quantization, P4 false-premise lesson, 25.09 cleaning evidence, consumer cron `9bf1839bf40f`) \u2192 `references/prompt-audit-lane.md`.

"""

FTE_SUPPORT_NEW = """- `references/measure-first-details.md` \u2014 full "Measure first" depth: commands, state.db daily-slice PITFALL, wasted-turn audit.
- `references/levers-playbook.md` \u2014 full levers depth: session hygiene incl. UPDATED reset-policy facts, MoA, compression, skills-index measurements, cron targets.
- `references/mechanics-pitfalls.md` \u2014 full mechanics & pitfalls list incl. UPDATED verify-after-changes rule.
- `references/routing-audit-safeguards.md` \u2014 routing/provider audit safeguards.
- `references/audit-to-program.md` \u2014 baseline/boundary/program procedure.
- `references/prompt-audit-lane.md` \u2014 prompt-audit lane canon (25.09\u201330.09).
"""

REF_NOTE = ("> Topic-focused reference \u2014 moved from this skill's SKILL.md by hub compaction "
            "(t_cef261ac, 2026-10-03, SOURCE-ONLY packet). Original text preserved verbatim")
REF_NOTE_CORR = REF_NOTE + "; inline `(UPDATE 2026-10-03 ...)` marks are documented corrections recorded in INVARIANT-MAP.json.\n\n"
REF_NOTE_PLAIN = REF_NOTE + ".\n\n"

# ------------------------------------------------------------------- assemble hubs
_RT_ANCHOR = crlf(HA_ROUTING_ANCHOR)
assert HA_SRC.count(_RT_ANCHOR) == 1, f"routing anchor count={HA_SRC.count(_RT_ANCHOR)}"
ha_routing_new = ha["routing"].replace(_RT_ANCHOR, crlf(HA_ROUTING_NEW_ROWS) + _RT_ANCHOR)

HA_HUB = (ha["fm"] + ha["title_block"] + crlf(HA_IDENTITY) + ha["hub_decl"] + crlf(HA_SCOPE_SUMMARY)
          + ha_routing_new + crlf(HA_POINTERS) + ha["invariants"])

_support_header = "## Support files\r\n\r\n"
assert fte["support"].startswith(_support_header)
fte_support_body = fte["support"][len(_support_header):]
FTE_SUPPORT = _support_header + crlf(FTE_SUPPORT_NEW) + fte_support_body

FTE_HUB = (fte["fm"] + fte["title_class"]
           + "## Measure first (never guess)\r\n\r\n" + crlf(FTE_MEASURE)
           + "## Levers (typical impact order)\r\n\r\n" + crlf(FTE_LEVERS_A) + fte["lever4"] + crlf(FTE_LEVERS_B)
           + crlf(FTE_MECHANICS) + crlf(FTE_LANES) + FTE_SUPPORT)

# ---------------------------------------------------------------------- references
_RN_CORR = crlf(REF_NOTE_CORR)
_RN_PLAIN = crlf(REF_NOTE_PLAIN)
ha_refs = {
    "product-overview.md": crlf("# hermes-agent \u2014 product overview, scope & verification, surfaces\n\n") + _RN_PLAIN
                           + ha["intro"] + ha["scope"] + ha["surfaces"],
    "quickstart-and-paths.md": crlf("# hermes-agent \u2014 quick start & key paths\n\n") + _RN_PLAIN
                               + ha["quickstart"] + ha["keypaths"],
    "spawning-instances.md": crlf("# hermes-agent \u2014 spawning additional Hermes instances\n\n") + _RN_PLAIN
                             + ha["spawning"],
}
fte_refs = {
    "measure-first-details.md": crlf("# fleet-token-economy \u2014 measure-first depth\n\n") + _RN_PLAIN + fte["measure"],
    "levers-playbook.md": crlf("# fleet-token-economy \u2014 levers playbook\n\n") + _RN_CORR
                          + apply_corrections(fte["levers"], ["C1a", "C1b"]),
    "mechanics-pitfalls.md": crlf("# fleet-token-economy \u2014 mechanics & pitfalls\n\n") + _RN_CORR
                             + apply_corrections(fte["mechanics"], ["C2"]),
    "routing-audit-safeguards.md": crlf("# fleet-token-economy \u2014 routing-audit safeguards\n\n") + _RN_PLAIN + fte["rsa"],
    "audit-to-program.md": crlf("# fleet-token-economy \u2014 from audit to program\n\n") + _RN_PLAIN + fte["program"],
    "prompt-audit-lane.md": crlf("# fleet-token-economy \u2014 prompt-audit lane (canon)\n\n") + _RN_PLAIN + fte["prompt_audit"],
}

# ------------------------------------------------------------------------ write out
if PKT.exists():
    shutil.rmtree(PKT)
for sub in ["candidates/hermes-agent/references", "candidates/fleet-token-economy/references",
            "rollback", "tests", "reference"]:
    (PKT / sub).mkdir(parents=True, exist_ok=True)

(PKT / "candidates/hermes-agent/SKILL.md").write_bytes(HA_HUB.encode("utf-8"))
(PKT / "candidates/fleet-token-economy/SKILL.md").write_bytes(FTE_HUB.encode("utf-8"))
for name, text in ha_refs.items():
    (PKT / "candidates/hermes-agent/references" / name).write_bytes(text.encode("utf-8"))
for name, text in fte_refs.items():
    (PKT / "candidates/fleet-token-economy/references" / name).write_bytes(text.encode("utf-8"))
# rollback snapshots: byte-exact prior allowlisted hub bytes
(PKT / "rollback/hermes-agent.SKILL.md").write_bytes(HA_SRC.encode("utf-8"))
(PKT / "rollback/fleet-token-economy.SKILL.md").write_bytes(FTE_SRC.encode("utf-8"))
assert (PKT / "rollback/hermes-agent.SKILL.md").read_bytes() == (HA_DIR / "SKILL.md").read_bytes()
assert (PKT / "rollback/fleet-token-economy.SKILL.md").read_bytes() == (FTE_DIR / "SKILL.md").read_bytes()

# ------------------------------------------------------------------------- manifest
def file_stat(path: Path, root: Path):
    b = path.read_bytes()
    s = b.decode("utf-8")
    return {"path": str(path.relative_to(root)).replace("\\", "/"), "bytes": len(b),
            "chars": len(s), "sha256": sha256_bytes(b)}


before_tree = {}
for label, d in [("hermes-agent", HA_DIR), ("fleet-token-economy", FTE_DIR)]:
    before_tree[label] = sorted([file_stat(p, d) for p in d.rglob("*") if p.is_file()],
                                key=lambda x: x["path"])

cand_tree = {}
for label, sub in [("hermes-agent", "candidates/hermes-agent"), ("fleet-token-economy", "candidates/fleet-token-economy")]:
    root = PKT / sub
    cand_tree[label] = sorted([file_stat(p, root) for p in root.rglob("*") if p.is_file()],
                              key=lambda x: x["path"])

hb_b = sum(f["bytes"] for f in before_tree["hermes-agent"] if f["path"] == "SKILL.md") + \
       sum(f["bytes"] for f in before_tree["fleet-token-economy"] if f["path"] == "SKILL.md")
hb_c = sum(f["bytes"] for f in cand_tree["hermes-agent"] if f["path"] == "SKILL.md") + \
       sum(f["bytes"] for f in cand_tree["fleet-token-economy"] if f["path"] == "SKILL.md")
hc_b = sum(f["chars"] for f in before_tree["hermes-agent"] if f["path"] == "SKILL.md") + \
       sum(f["chars"] for f in before_tree["fleet-token-economy"] if f["path"] == "SKILL.md")
hc_c = sum(f["chars"] for f in cand_tree["hermes-agent"] if f["path"] == "SKILL.md") + \
       sum(f["chars"] for f in cand_tree["fleet-token-economy"] if f["path"] == "SKILL.md")

manifest = {
    "packet": "HUB-PACKET", "task": "t_cef261ac", "date": "2026-10-03",
    "anchor_profile": "C:/Users/max/AppData/Local/hermes/profiles/company",
    "skills": {
        "hermes-agent": "autonomous-ai-agents/hermes-agent",
        "fleet-token-economy": "fleet-ops/fleet-token-economy",
    },
    "before_tree": before_tree,
    "candidate_tree": cand_tree,
    "hub_reduction": {
        "combined_bytes_before": hb_b, "combined_bytes_candidate": hb_c,
        "combined_bytes_reduction_pct": round(100.0 * (hb_b - hb_c) / hb_b, 2),
        "combined_chars_before": hc_b, "combined_chars_candidate": hc_c,
        "combined_chars_reduction_pct": round(100.0 * (hc_b - hc_c) / hc_b, 2),
        "note": "chars/bytes are NOT tokens. PRODUCT-BRIEF cites 33,078 source chars; measured here 33,372 chars / 36,294 bytes from anchored sha256 bytes (294-char method delta noted, reduction computed from measured anchor).",
    },
    "rollback_snapshots": [
        {"dest": "autonomous-ai-agents/hermes-agent/SKILL.md", "packet_file": "rollback/hermes-agent.SKILL.md",
         "sha256": sha256_file(PKT / "rollback/hermes-agent.SKILL.md")},
        {"dest": "fleet-ops/fleet-token-economy/SKILL.md", "packet_file": "rollback/fleet-token-economy.SKILL.md",
         "sha256": sha256_file(PKT / "rollback/fleet-token-economy.SKILL.md")},
    ],
    "corrections": CORRECTIONS,
    "routing_addition": {"skill": "hermes-agent", "anchor_row": HA_ROUTING_ANCHOR.strip(),
                          "inserted_rows": [r.strip() for r in HA_ROUTING_NEW_ROWS.strip().splitlines()]},
}
(PKT / "MANIFEST.json").write_bytes(json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"))

# ------------------------------------------------------------------- invariant map
def span(start, end=None):
    return {"start_anchor": start, "end_anchor": end}

INV = [
    {"id": "HA-FM", "skill": "hermes-agent", "kind": "frontmatter_triggers", "disposition": "kept_in_hub_verbatim",
     "dest": "SKILL.md", "span": span("---\nname: hermes-agent", None), "slice": "frontmatter",
     "markers": [], "note": "name/description/version/metadata byte-identical; extended trigger line preserved in body."},
    {"id": "HA-TITLE-TRIG", "skill": "hermes-agent", "kind": "trigger", "disposition": "kept_in_hub_verbatim",
     "dest": "SKILL.md", "slice": "title_block", "markers": []},
    {"id": "HA-INTRO", "skill": "hermes-agent", "kind": "unique_content", "disposition": "moved_verbatim",
     "dest": "references/product-overview.md", "slice": "intro", "markers": []},
    {"id": "HA-HUBDECL", "skill": "hermes-agent", "kind": "procedure", "disposition": "kept_in_hub_verbatim",
     "dest": "SKILL.md", "slice": "hub_decl", "markers": []},
    {"id": "HA-SCOPE", "skill": "hermes-agent", "kind": "safety_invariant", "disposition": "moved_verbatim",
     "dest": "references/product-overview.md", "slice": "scope",
     "hub_markers": ["llms.txt", "llms-full.txt", "Never answer \"Hermes can't do that\" from memory.", "product-overview.md"]},
    {"id": "HA-QS", "skill": "hermes-agent", "kind": "unique_procedure", "disposition": "moved_verbatim",
     "dest": "references/quickstart-and-paths.md", "slice": "quickstart",
     "hub_markers": ["quickstart-and-paths.md"]},
    {"id": "HA-KP", "skill": "hermes-agent", "kind": "unique_procedure", "disposition": "moved_verbatim",
     "dest": "references/quickstart-and-paths.md", "slice": "keypaths",
     "hub_markers": ["$HERMES_HOME", "never hardcode `~/.hermes`"]},
    {"id": "HA-RT", "skill": "hermes-agent", "kind": "procedure", "disposition": "kept_in_hub_verbatim_plus_rows",
     "dest": "SKILL.md", "slice": "routing", "markers": [],
     "note": "Every original routing row preserved byte-exact; 3 additive rows for new refs (MANIFEST.routing_addition)."},
    {"id": "HA-THEMING", "skill": "hermes-agent", "kind": "safety_invariant", "disposition": "kept_in_hub_verbatim",
     "dest": "SKILL.md", "slice": None,
     "markers": ["you apply skins yourself", "never fork `default`, which drops the palette"]},
    {"id": "HA-SPAWN", "skill": "hermes-agent", "kind": "unique_procedure", "disposition": "moved_verbatim",
     "dest": "references/spawning-instances.md", "slice": "spawning",
     "hub_markers": ["spawning-instances.md", "Prefer `delegate_task` for quick subtasks", "cronjob"]},
    {"id": "HA-SURF", "skill": "hermes-agent", "kind": "unique_content", "disposition": "moved_verbatim",
     "dest": "references/product-overview.md", "slice": "surfaces",
     "hub_markers": ["product-overview.md"]},
    {"id": "HA-INV", "skill": "hermes-agent", "kind": "safety_invariant", "disposition": "kept_in_hub_verbatim",
     "dest": "SKILL.md", "slice": "invariants",
     "markers": ["Never break prompt caching", "Message role alternation", "Secrets in `.env`, settings in `config.yaml`",
                  "Profile-safe paths", "Never hand-edit `config.yaml` for the user"]},
    {"id": "FTE-FM", "skill": "fleet-token-economy", "kind": "frontmatter_triggers", "disposition": "kept_in_hub_verbatim",
     "dest": "SKILL.md", "slice": "frontmatter", "markers": []},
    {"id": "FTE-TITLE", "skill": "fleet-token-economy", "kind": "procedure", "disposition": "kept_in_hub_verbatim",
     "dest": "SKILL.md", "slice": "title_class", "markers": []},
    {"id": "FTE-MEASURE", "skill": "fleet-token-economy", "kind": "unique_procedure", "disposition": "moved_verbatim",
     "dest": "references/measure-first-details.md", "slice": "measure",
     "hub_markers": ["hermes insights --days N", "prompt-size --json", "mode=ro", "hermes cron list",
                      "Wasted-turn audit", "measure-first-details.md"]},
    {"id": "FTE-LEVERS", "skill": "fleet-token-economy", "kind": "unique_procedure", "disposition": "moved_corrected",
     "corrections": ["C1a", "C1b"], "dest": "references/levers-playbook.md", "slice": "levers",
     "hub_markers": ["moa.presets.default.enabled", "compression.protect_last_n", "skills.disabled",
                      "bot-chat:<profile>", "levers-playbook.md"]},
    {"id": "FTE-LEV4-EFFORT", "skill": "fleet-token-economy", "kind": "owner_directive_safety",
     "disposition": "kept_in_hub_verbatim", "dest": "SKILL.md", "slice": "lever4",
     "markers": ["\u0417\u0410\u041f\u0420\u0415\u0429\u0401\u041d\u041d\u042b\u0419 \u0440\u044b\u0447\u0430\u0433", "reasoning **max**", "DashScope"]},
    {"id": "FTE-MECH", "skill": "fleet-token-economy", "kind": "unique_procedure", "disposition": "moved_corrected",
     "corrections": ["C2"], "dest": "references/mechanics-pitfalls.md", "slice": "mechanics",
     "hub_markers": ["hermes config set key value", "timestamped backup", "Unknown-key warning", "kanban_*",
                      "mechanics-pitfalls.md"]},
    {"id": "FTE-RSA", "skill": "fleet-token-economy", "kind": "safety_invariant", "disposition": "moved_verbatim",
     "dest": "references/routing-audit-safeguards.md", "slice": "rsa",
     "hub_markers": ["routing-audit-safeguards.md", "cost_status"]},
    {"id": "FTE-PROG", "skill": "fleet-token-economy", "kind": "unique_procedure", "disposition": "moved_verbatim",
     "dest": "references/audit-to-program.md", "slice": "program",
     "hub_markers": ["audit-to-program.md", "boundary snapshot"]},
    {"id": "FTE-PA", "skill": "fleet-token-economy", "kind": "unique_procedure", "disposition": "moved_verbatim",
     "dest": "references/prompt-audit-lane.md", "slice": "prompt_audit",
     "hub_markers": ["prompt-audit-lane.md", "prompt_audit.py", "d341b0d4a136"]},
    {"id": "FTE-SUP", "skill": "fleet-token-economy", "kind": "procedure", "disposition": "kept_in_hub_verbatim_expanded",
     "dest": "SKILL.md", "slice": "support_bullets", "markers": []},
]

# enrich entries with explicit source spans so tests can re-slice independently
SPANS = {
    ("hermes-agent", "title_block"): ("# Hermes Agent", "Hermes Agent is an open-source"),
    ("hermes-agent", "intro"): ("Hermes Agent is an open-source", "**This skill is a hub.**"),
    ("hermes-agent", "hub_decl"): ("**This skill is a hub.**", "## Scope & Verification"),
    ("hermes-agent", "scope"): ("## Scope & Verification", "## Quick Start"),
    ("hermes-agent", "quickstart"): ("## Quick Start", "## Key Paths"),
    ("hermes-agent", "keypaths"): ("## Key Paths", "## Routing Table"),
    ("hermes-agent", "routing"): ("## Routing Table", "## Spawning Additional Hermes Instances"),
    ("hermes-agent", "spawning"): ("## Spawning Additional Hermes Instances", "## Surfaces (quick orientation)"),
    ("hermes-agent", "surfaces"): ("## Surfaces (quick orientation)", "## Hard Invariants"),
    ("hermes-agent", "invariants"): ("## Hard Invariants", None),
    ("fleet-token-economy", "title_class"): ("# Fleet Token Economy", "## Measure first (never guess)"),
    ("fleet-token-economy", "measure"): ("## Measure first (never guess)", "## Levers (typical impact order)"),
    ("fleet-token-economy", "levers"): ("## Levers (typical impact order)", "## Mechanics & pitfalls"),
    ("fleet-token-economy", "lever4"): ("4. **Reasoning effort", "5. **Skills index**"),
    ("fleet-token-economy", "mechanics"): ("## Mechanics & pitfalls", "## Routing-audit safeguards"),
    ("fleet-token-economy", "rsa"): ("## Routing-audit safeguards", "## From audit to program"),
    ("fleet-token-economy", "program"): ("## From audit to program", "## Prompt-audit \u043b\u0435\u0439\u043d"),
    ("fleet-token-economy", "prompt_audit"): ("## Prompt-audit \u043b\u0435\u0439\u043d", "## Support files"),
    ("fleet-token-economy", "support"): ("## Support files", None),
}
for e in INV:
    sl = e.get("slice")
    if sl in ("frontmatter", "support_bullets", None):
        e["span"] = {"type": sl or "none", "start": None, "end": None}
    else:
        s, en = SPANS[(e["skill"], sl)]
        e["span"] = {"type": "anchors", "start": s, "end": en}

(PKT / "INVARIANT-MAP.json").write_bytes(json.dumps(
    {"task": "t_cef261ac", "entries": INV, "corrections": CORRECTIONS,
     "method": "Each source section is a slice between unique anchors; disposition tells where the slice lives in the applied tree (candidate hub and/or new reference). moved_corrected = verbatim slice minus the recorded surgical corrections. Tests re-slice live source and assert substring/marker presence."},
    ensure_ascii=False, indent=2).encode("utf-8"))

# ------------------------------------------------------------------ static footprint
def stat_text(t):
    b = t.encode("utf-8")
    return {"chars": len(t), "bytes": len(b)}


ha_refs_before = sum(p.stat().st_size for p in (HA_DIR / "references").rglob("*") if p.is_file())
fte_refs_before = sum(p.stat().st_size for p in (FTE_DIR / "references").rglob("*") if p.is_file())
ha_refs_new = sum(len(t.encode("utf-8")) for t in ha_refs.values())
fte_refs_new = sum(len(t.encode("utf-8")) for t in fte_refs.values())

fp_lines = [
    "# STATIC-FOOTPRINT \u2014 offline before/proposed (chars and bytes, NOT tokens)",
    "",
    "Static offline computation from anchored file bytes; no runtime inference, no token claims.",
    "Chars/bytes \u2260 tokens; usage/quota \u2260 invoice (DECISION-AND-CONTRACT.md).",
    "",
    "## Per-hub skill_view injection (hub body loaded on skill_view)",
    "",
    "| Hub | before bytes | before chars | candidate bytes | candidate chars | bytes reduction |",
    "|---|---|---|---|---|---|",
]
for label, src_text, hub_rel in [("hermes-agent", HA_SRC, "candidates/hermes-agent/SKILL.md"),
                                  ("fleet-token-economy", FTE_SRC, "candidates/fleet-token-economy/SKILL.md")]:
    cb = (PKT / hub_rel).read_bytes()
    cs = cb.decode("utf-8")
    ob = src_text.encode("utf-8")
    fp_lines.append(f"| {label} | {len(ob)} | {len(src_text)} | {len(cb)} | {len(cs)} | {round(100.0*(len(ob)-len(cb))/len(ob),2)}% |")
fp_lines += [
    f"| **combined** | **{hb_b}** | **{hc_b}** | **{hb_c}** | **{hc_c}** | **{round(100.0*(hb_b-hb_c)/hb_b,2)}%** |",
    "",
    "## System prompt / skills index (per prompt, every session)",
    "",
    "- Skills-index line per skill is UNCHANGED: frontmatter name/description are byte-identical, so the",
    "  always-injected index contribution (6 + name + 2 + min(desc,60) bytes) does not change.",
    "- System prompt baseline (prompt-baseline.json): system 47,291 chars / 57,806 bytes \u2014 untouched by this packet.",
    "- Hubs are NOT injected into the system prompt; they load only on skill_view, so the saving is per-load,",
    "  not per-prompt. Every load previously injected the full monolith; now it injects only the compact hub.",
    "",
    "## Worst case: hub + ALL references loaded (honest upper bound)",
    "",
    f"- hermes-agent refs before: {ha_refs_before} bytes; new refs added: {ha_refs_new} bytes;",
    f"  worst-case total grows by pointer/header overhead only (content moved, not duplicated except short hub pointers).",
    f"- fleet-token-economy refs before: {fte_refs_before} bytes; new refs added: {fte_refs_new} bytes.",
    "- Typical load is hub-only (refs are on-demand via routing table) \u2014 that is where the reduction lands.",
    "- No imaginary runtime savings are claimed; natural-run measurement is acceptance step 6 of the contract.",
    "",
]
(PKT / "STATIC-FOOTPRINT.md").write_bytes("\n".join(fp_lines).encode("utf-8"))

# ------------------------------------------------------------------------- report
print("BUILD OK")
print(f"hub bytes: before={hb_b} candidate={hb_c} reduction={round(100.0*(hb_b-hb_c)/hb_b,2)}%")
print(f"hub chars: before={hc_b} candidate={hc_c} reduction={round(100.0*(hc_b-hc_c)/hc_b,2)}%")
for rel in ["candidates/hermes-agent/SKILL.md", "candidates/fleet-token-economy/SKILL.md"]:
    p = PKT / rel
    print(rel, len(p.read_bytes()), "bytes", sha256_file(p)[:16])
