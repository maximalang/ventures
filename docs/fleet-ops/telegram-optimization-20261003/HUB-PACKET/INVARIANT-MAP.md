# INVARIANT-MAP (human-readable; machine source: INVARIANT-MAP.json)

Every section of both anchored hubs is mapped. Dispositions: kept_in_hub_verbatim (byte-exact in candidate hub), moved_verbatim (byte-exact in new reference), moved_corrected (verbatim minus recorded surgical corrections), kept_in_hub_verbatim_plus_rows (routing table: all original rows byte-exact + 3 additive rows), kept_in_hub_verbatim_expanded (support list: original bullets byte-exact + new bullets).

| ID | Skill | Kind | Disposition | Destination | Corrections |
|---|---|---|---|---|---|
| HA-FM | hermes-agent | frontmatter_triggers | kept_in_hub_verbatim | `SKILL.md` | - |
| HA-TITLE-TRIG | hermes-agent | trigger | kept_in_hub_verbatim | `SKILL.md` | - |
| HA-INTRO | hermes-agent | unique_content | moved_verbatim | `references/product-overview.md` | - |
| HA-HUBDECL | hermes-agent | procedure | kept_in_hub_verbatim | `SKILL.md` | - |
| HA-SCOPE | hermes-agent | safety_invariant | moved_verbatim | `references/product-overview.md` | - |
| HA-QS | hermes-agent | unique_procedure | moved_verbatim | `references/quickstart-and-paths.md` | - |
| HA-KP | hermes-agent | unique_procedure | moved_verbatim | `references/quickstart-and-paths.md` | - |
| HA-RT | hermes-agent | procedure | kept_in_hub_verbatim_plus_rows | `SKILL.md` | - |
| HA-THEMING | hermes-agent | safety_invariant | kept_in_hub_verbatim | `SKILL.md` | - |
| HA-SPAWN | hermes-agent | unique_procedure | moved_verbatim | `references/spawning-instances.md` | - |
| HA-SURF | hermes-agent | unique_content | moved_verbatim | `references/product-overview.md` | - |
| HA-INV | hermes-agent | safety_invariant | kept_in_hub_verbatim | `SKILL.md` | - |
| FTE-FM | fleet-token-economy | frontmatter_triggers | kept_in_hub_verbatim | `SKILL.md` | - |
| FTE-TITLE | fleet-token-economy | procedure | kept_in_hub_verbatim | `SKILL.md` | - |
| FTE-MEASURE | fleet-token-economy | unique_procedure | moved_verbatim | `references/measure-first-details.md` | - |
| FTE-LEVERS | fleet-token-economy | unique_procedure | moved_corrected | `references/levers-playbook.md` | C1a, C1b |
| FTE-LEV4-EFFORT | fleet-token-economy | owner_directive_safety | kept_in_hub_verbatim | `SKILL.md` | - |
| FTE-MECH | fleet-token-economy | unique_procedure | moved_corrected | `references/mechanics-pitfalls.md` | C2 |
| FTE-RSA | fleet-token-economy | safety_invariant | moved_verbatim | `references/routing-audit-safeguards.md` | - |
| FTE-PROG | fleet-token-economy | unique_procedure | moved_verbatim | `references/audit-to-program.md` | - |
| FTE-PA | fleet-token-economy | unique_procedure | moved_verbatim | `references/prompt-audit-lane.md` | - |
| FTE-SUP | fleet-token-economy | procedure | kept_in_hub_verbatim_expanded | `SKILL.md` | - |

## Recorded corrections (full before/after strings in INVARIANT-MAP.json and MANIFEST.json)

- **C1a** (fleet-token-economy -> `references/levers-playbook.md`): Obsolete blanket default must not override active owner directive; contract line 13 documents installed reset-policy plugin. Evidence: DECISION-AND-CONTRACT.md §'Evidence already collected' line 13; profiles/company/plugins/hermes-session-reset-policy exists (ls).
- **C1b** (fleet-token-economy -> `references/levers-playbook.md`): Consumer verification must include installed plugins, not only kernel source. Evidence: DECISION-AND-CONTRACT.md line 13 + line 17 ('Check installed consumers, not documentation alone').
- **C2** (fleet-token-economy -> `references/mechanics-pitfalls.md`): PRODUCT-BRIEF.md: fix obsolete blanket advice about 'only new sessions'; hot reload must be checked against installed consumer. Evidence: hermes-configuration-official.txt line 2532 'Gateway hot-reload of compression and context length'; PRODUCT-BRIEF.md §delta.

## Hub marker summary (compressed hub lines; full depth verbatim in refs)

- HA-SCOPE: `llms.txt`; `llms-full.txt`; `Never answer "Hermes can't do that" from memory.`; `product-overview.md`
- HA-QS: `quickstart-and-paths.md`
- HA-KP: `$HERMES_HOME`; `never hardcode `~/.hermes``
- HA-SPAWN: `spawning-instances.md`; `Prefer `delegate_task` for quick subtasks`; `cronjob`
- HA-SURF: `product-overview.md`
- FTE-MEASURE: `hermes insights --days N`; `prompt-size --json`; `mode=ro`; `hermes cron list`; `Wasted-turn audit`; `measure-first-details.md`
- FTE-LEVERS: `moa.presets.default.enabled`; `compression.protect_last_n`; `skills.disabled`; `bot-chat:<profile>`; `levers-playbook.md`
- FTE-MECH: `hermes config set key value`; `timestamped backup`; `Unknown-key warning`; `kanban_*`; `mechanics-pitfalls.md`
- FTE-RSA: `routing-audit-safeguards.md`; `cost_status`
- FTE-PROG: `audit-to-program.md`; `boundary snapshot`
- FTE-PA: `prompt-audit-lane.md`; `prompt_audit.py`; `d341b0d4a136`

Tests re-slice the LIVE anchored sources by unique anchors, replay corrections, and assert substring/marker presence — tests/test_hub_packet.py (T04/T05/T07/T08).