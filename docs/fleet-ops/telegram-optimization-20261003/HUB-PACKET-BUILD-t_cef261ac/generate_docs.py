# -*- coding: utf-8 -*-
"""Generate APPLY-ROLLBACK.md and INVARIANT-MAP.md from MANIFEST/INVARIANT-MAP JSON."""
import json
from pathlib import Path

PKT = Path(__file__).resolve().parent / "HUB-PACKET"
M = json.loads((PKT / "MANIFEST.json").read_bytes().decode("utf-8"))
INV = json.loads((PKT / "INVARIANT-MAP.json").read_bytes().decode("utf-8"))


def h(skill, rel, tree):
    for f in M[tree][skill]:
        if f["path"] == rel:
            return f
    raise KeyError(rel)


ha_b = h("hermes-agent", "SKILL.md", "before_tree")
fte_b = h("fleet-token-economy", "SKILL.md", "before_tree")
ha_c = h("hermes-agent", "SKILL.md", "candidate_tree")
fte_c = h("fleet-token-economy", "SKILL.md", "candidate_tree")

ar = []
ar.append("# APPLY-ROLLBACK — exact ops CLI lists\n")
ar.append("Application owner: operations/company (bounded), only after QA PASS (t_d5e37e14) and the owner's go-anchor comment from company per fleet-policy arming rules. This packet's author (tech) made NO live writes.\n")
ar.append("## Paths\n")
ar.append('```bash\nSK="C:/Users/max/AppData/Local/hermes/profiles/company/skills"\nPK="C:/Users/max/Desktop/all/ventures/docs/fleet-ops/telegram-optimization-20261003/HUB-PACKET"\n```\n')
ar.append("## Apply (hub replacement + additive refs; existing refs/scripts/templates untouched)\n")
ar.append('```bash\ncp "$PK/candidates/hermes-agent/SKILL.md"        "$SK/autonomous-ai-agents/hermes-agent/SKILL.md"\ncp "$PK/candidates/fleet-token-economy/SKILL.md" "$SK/fleet-ops/fleet-token-economy/SKILL.md"\ncp "$PK/candidates/hermes-agent/references/product-overview.md"     "$SK/autonomous-ai-agents/hermes-agent/references/"\ncp "$PK/candidates/hermes-agent/references/quickstart-and-paths.md" "$SK/autonomous-ai-agents/hermes-agent/references/"\ncp "$PK/candidates/hermes-agent/references/spawning-instances.md"   "$SK/autonomous-ai-agents/hermes-agent/references/"\ncp "$PK/candidates/fleet-token-economy/references/"*.md             "$SK/fleet-ops/fleet-token-economy/references/"\n```\n')
ar.append("## Apply readback (expected sha256)\n")
ar.append('```bash\nsha256sum "$SK/autonomous-ai-agents/hermes-agent/SKILL.md" "$SK/fleet-ops/fleet-token-economy/SKILL.md"\n```\n')
ar.append(f"- hermes-agent/SKILL.md        = `{ha_c['sha256']}` ({ha_c['bytes']} bytes / {ha_c['chars']} chars)")
ar.append(f"- fleet-token-economy/SKILL.md = `{fte_c['sha256']}` ({fte_c['bytes']} bytes / {fte_c['chars']} chars)")
ar.append("- new refs: verify against MANIFEST.json candidate_tree entries (sha256 per file)\n")
ar.append("## Rollback candidate (byte-exact prior hubs + delete added refs)\n")
ar.append('```bash\ncp "$PK/rollback/hermes-agent.SKILL.md"        "$SK/autonomous-ai-agents/hermes-agent/SKILL.md"\ncp "$PK/rollback/fleet-token-economy.SKILL.md" "$SK/fleet-ops/fleet-token-economy/SKILL.md"\nrm "$SK/autonomous-ai-agents/hermes-agent/references/product-overview.md" \\\n   "$SK/autonomous-ai-agents/hermes-agent/references/quickstart-and-paths.md" \\\n   "$SK/autonomous-ai-agents/hermes-agent/references/spawning-instances.md"\nrm "$SK/fleet-ops/fleet-token-economy/references/measure-first-details.md" \\\n   "$SK/fleet-ops/fleet-token-economy/references/levers-playbook.md" \\\n   "$SK/fleet-ops/fleet-token-economy/references/mechanics-pitfalls.md" \\\n   "$SK/fleet-ops/fleet-token-economy/references/routing-audit-safeguards.md" \\\n   "$SK/fleet-ops/fleet-token-economy/references/audit-to-program.md" \\\n   "$SK/fleet-ops/fleet-token-economy/references/prompt-audit-lane.md"\n```\n')
ar.append("## Rollback readback (expected sha256 == anchored before)\n")
ar.append(f"- hermes-agent/SKILL.md        = `{ha_b['sha256']}` ({ha_b['bytes']} bytes / {ha_b['chars']} chars)")
ar.append(f"- fleet-token-economy/SKILL.md = `{fte_b['sha256']}` ({fte_b['bytes']} bytes / {fte_b['bytes'] and fte_b['chars']} chars)")
ar.append("- rollback/ snapshots in this packet are byte-identical to the anchored live sources (test T02).\n")
ar.append("## Guardrails\n")
ar.append("- Apply only to the two company skill paths above; no other profile, no config/SOUL/cron/model/history writes.")
ar.append("- Do not touch the telegram-message-formatting retirement files (t_b3e6c428/t_45c34a6a) or network lanes (t_930c007a).")
ar.append("- After apply: verify readback hashes, then the contract's natural-run measurement (acceptance step 6) is the only proof of runtime savings; this packet claims static offline sizes only.")
ar.append("- Stop rule: any lost goal/source/steering, route leakage, warning/attachment failure -> roll back via the list above.")
(PKT / "APPLY-ROLLBACK.md").write_bytes("\n".join(ar).encode("utf-8"))

lm = ["# INVARIANT-MAP (human-readable; machine source: INVARIANT-MAP.json)\n",
      "Every section of both anchored hubs is mapped. Dispositions: kept_in_hub_verbatim (byte-exact in candidate hub), "
      "moved_verbatim (byte-exact in new reference), moved_corrected (verbatim minus recorded surgical corrections), "
      "kept_in_hub_verbatim_plus_rows (routing table: all original rows byte-exact + 3 additive rows), "
      "kept_in_hub_verbatim_expanded (support list: original bullets byte-exact + new bullets).\n",
      "| ID | Skill | Kind | Disposition | Destination | Corrections |",
      "|---|---|---|---|---|---|"]
for e in INV["entries"]:
    lm.append(f"| {e['id']} | {e['skill']} | {e['kind']} | {e['disposition']} | `{e['dest']}` | {', '.join(e.get('corrections') or []) or '-'} |")
lm.append("\n## Recorded corrections (full before/after strings in INVARIANT-MAP.json and MANIFEST.json)\n")
for cid, c in INV["corrections"].items():
    lm.append(f"- **{cid}** ({c['skill']} -> `{c['dest']}`): {c['rationale']} Evidence: {c['evidence']}")
lm.append("\n## Hub marker summary (compressed hub lines; full depth verbatim in refs)\n")
for e in INV["entries"]:
    if e.get("hub_markers"):
        lm.append(f"- {e['id']}: " + "; ".join(f"`{m[:60]}`" for m in e["hub_markers"]))
lm.append("\nTests re-slice the LIVE anchored sources by unique anchors, replay corrections, and assert substring/marker presence — tests/test_hub_packet.py (T04/T05/T07/T08).")
(PKT / "INVARIANT-MAP.md").write_bytes("\n".join(lm).encode("utf-8"))
print("DOCS OK")
for label, x in [("ha_before", ha_b), ("fte_before", fte_b), ("ha_cand", ha_c), ("fte_cand", fte_c)]:
    print(label, x["sha256"], x["bytes"])
