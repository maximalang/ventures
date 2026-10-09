# APPLY-ROLLBACK — exact ops CLI lists

Application owner: operations/company (bounded), only after QA PASS (t_d5e37e14) and the owner's go-anchor comment from company per fleet-policy arming rules. This packet's author (tech) made NO live writes.

## Paths

```bash
SK="C:/Users/max/AppData/Local/hermes/profiles/company/skills"
PK="C:/Users/max/Desktop/all/ventures/docs/fleet-ops/telegram-optimization-20261003/HUB-PACKET"
```

## Apply (hub replacement + additive refs; existing refs/scripts/templates untouched)

```bash
cp "$PK/candidates/hermes-agent/SKILL.md"        "$SK/autonomous-ai-agents/hermes-agent/SKILL.md"
cp "$PK/candidates/fleet-token-economy/SKILL.md" "$SK/fleet-ops/fleet-token-economy/SKILL.md"
cp "$PK/candidates/hermes-agent/references/product-overview.md"     "$SK/autonomous-ai-agents/hermes-agent/references/"
cp "$PK/candidates/hermes-agent/references/quickstart-and-paths.md" "$SK/autonomous-ai-agents/hermes-agent/references/"
cp "$PK/candidates/hermes-agent/references/spawning-instances.md"   "$SK/autonomous-ai-agents/hermes-agent/references/"
cp "$PK/candidates/fleet-token-economy/references/"*.md             "$SK/fleet-ops/fleet-token-economy/references/"
```

## Apply readback (expected sha256)

```bash
sha256sum "$SK/autonomous-ai-agents/hermes-agent/SKILL.md" "$SK/fleet-ops/fleet-token-economy/SKILL.md"
```

- hermes-agent/SKILL.md        = `0f2486ca0f260c458740bacf3db7ff94810b77c1f794c8df86e282bbc1ed7df0` (6559 bytes / 6515 chars)
- fleet-token-economy/SKILL.md = `f4853d61aed45b57598ca11682558810d493823773d7e4117f8784b9ffb24b58` (6369 bytes / 6008 chars)
- new refs: verify against MANIFEST.json candidate_tree entries (sha256 per file)

## Rollback candidate (byte-exact prior hubs + delete added refs)

```bash
cp "$PK/rollback/hermes-agent.SKILL.md"        "$SK/autonomous-ai-agents/hermes-agent/SKILL.md"
cp "$PK/rollback/fleet-token-economy.SKILL.md" "$SK/fleet-ops/fleet-token-economy/SKILL.md"
rm "$SK/autonomous-ai-agents/hermes-agent/references/product-overview.md" \
   "$SK/autonomous-ai-agents/hermes-agent/references/quickstart-and-paths.md" \
   "$SK/autonomous-ai-agents/hermes-agent/references/spawning-instances.md"
rm "$SK/fleet-ops/fleet-token-economy/references/measure-first-details.md" \
   "$SK/fleet-ops/fleet-token-economy/references/levers-playbook.md" \
   "$SK/fleet-ops/fleet-token-economy/references/mechanics-pitfalls.md" \
   "$SK/fleet-ops/fleet-token-economy/references/routing-audit-safeguards.md" \
   "$SK/fleet-ops/fleet-token-economy/references/audit-to-program.md" \
   "$SK/fleet-ops/fleet-token-economy/references/prompt-audit-lane.md"
```

## Rollback readback (expected sha256 == anchored before)

- hermes-agent/SKILL.md        = `a21232e109527dc470bb2271bd43fa10a99de681732260f8bed762eaa44888dc` (13580 bytes / 13494 chars)
- fleet-token-economy/SKILL.md = `2d6a90ced0f9e297dad1ee711e58f34e1f5c531123593ca76c54bf6134e817b8` (22714 bytes / 19878 chars)
- rollback/ snapshots in this packet are byte-identical to the anchored live sources (test T02).

## Guardrails

- Apply only to the two company skill paths above; no other profile, no config/SOUL/cron/model/history writes.
- Do not touch the telegram-message-formatting retirement files (t_b3e6c428/t_45c34a6a) or network lanes (t_930c007a).
- After apply: verify readback hashes, then the contract's natural-run measurement (acceptance step 6) is the only proof of runtime savings; this packet claims static offline sizes only.
- Stop rule: any lost goal/source/steering, route leakage, warning/attachment failure -> roll back via the list above.