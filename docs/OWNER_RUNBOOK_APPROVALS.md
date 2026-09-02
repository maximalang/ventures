# Owner Runbook: Approval Decisions (fleet-policy v1.2.5)

For: the fleet owner (a human). Audience is NOT an agent. v1.2.5 enforces
owner-principal approval: `approve`, `reject`, and `revoke` only succeed from
an interactive terminal (TTY) with an explicit `--confirm` suffix. Agent tool
calls, cron jobs, pipes, and redirected stdin cannot perform these actions —
the CLI exits 2.

Canonical invocation (from repo README):

```
uv run --frozen fleet-policy --root <REPO_ROOT> <command> ...
```

If you run from a source checkout, `<REPO_ROOT>` is the repository directory
(the one containing `src/fleet_policy/`). If `--root` is omitted, the CLI
uses `HERMES_VENTURES_ROOT` or auto-detects the bundle/source root.

## 1. Open an interactive terminal on the fleet host

On the Windows fleet host:

1. Press `Win + R`, type `wt`, press Enter (Windows Terminal).
   Alternatives: `Win + X` then `Terminal`, or open `cmd.exe` / PowerShell.
2. Go to the ventures checkout:

```
cd C:\Users\max\Desktop\all\ventures
```

3. Every command below must be typed by you in this window. Do not paste the
   command into a bot chat, an agent prompt, or any tool that runs commands
   on your behalf — those channels have no TTY and the action will be
   refused by design.

## 2. Find the rule_key and build the confirm suffix

When a serious action needs your decision, the notifier posts an
`APPROVAL REQUIRED` card to the `company` Bot Chat. The card contains a
line:

```
Binding: <RULE_KEY>
```

That full string is the `rule_key`. The confirmation code is the LAST 8
CHARACTERS of it.

Example — if the card shows:

```
Binding: 3f9a1c2e-ops-vds-snapshot-7b41ac09e2d5f8a1
```

then the confirm suffix is `e2d5f8a1`.

Copy the full rule_key exactly as shown (do not retype it by hand) and note
the 8-character suffix.

## 3. Decision commands

Run from the interactive terminal, inside the ventures checkout. Replace
`<RULE_KEY>` with the full binding string and `<SUFFIX8>` with its last 8
characters. All examples below use the example binding from section 2.

Approve (grant the pending action):

```
uv run --frozen fleet-policy --root . approve 3f9a1c2e-ops-vds-snapshot-7b41ac09e2d5f8a1 --by user --confirm=e2d5f8a1
```

Reject (deny the pending action):

```
uv run --frozen fleet-policy --root . reject 3f9a1c2e-ops-vds-snapshot-7b41ac09e2d5f8a1 --by user --confirm=e2d5f8a1
```

Revoke (kill a binding you already granted, or cancel a still-pending one —
use this to retract a stale approval before it is consumed):

```
uv run --frozen fleet-policy --root . revoke 3f9a1c2e-ops-vds-snapshot-7b41ac09e2d5f8a1 --by user --confirm=e2d5f8a1
```

Notes:

- `--confirm` is mandatory in practice: without it (or with a wrong value)
  the command exits 2.
- Each command prints one JSON line with the outcome.

## 4. Exit codes and error text

Exit code 0 — success. Output:

```
{"ok": true, "rule_key": "...", "decision": "approve" | "reject" | "revoked"}
```

Exit code 2 — refused. Two distinct reasons:

```
{"ok": false, "rule_key": "...", "reason": "approval decisions require an interactive owner terminal (no TTY)"}
{"ok": false, "rule_key": "...", "reason": "revocation requires an interactive owner terminal (no TTY)"}
```

Meaning: stdin is not an interactive terminal — you ran it through an
agent, a script, a pipe, or CI. Open a real terminal window (section 1) and
retype the command.

```
{"ok": false, "rule_key": "...", "decision": "...", "reason": "binding missing, already decided, or confirmation code invalid (expected the binding's last 8 characters)"}
{"ok": false, "rule_key": "...", "decision": "revoked", "reason": "binding missing, already consumed/rejected/revoked, or confirmation code invalid"}
```

Meaning: one of — (a) the rule_key does not exist or was mistyped; (b) the
binding is no longer in a state this command can change (already decided /
consumed / rejected / revoked); (c) the `--confirm` suffix does not equal
the last 8 characters of the rule_key. Re-read the Binding line from the
notification and retry; if the binding was already decided or consumed, no
further action is possible on it.

## 5. Audit trail and verification

Every decision is an immutable row in the `approvals` table of the policy
database:

```
<REPO_ROOT>\.state\fleet-policy.db      (e.g. C:\Users\max\Desktop\all\ventures\.state\fleet-policy.db)
```

Decided rows carry `status` (`approved`, `rejected`, `revoked`, or
`consumed` once the granted action fires), plus `decided_at` / `decided_by`
(or `revoked_at` / `revoked_by`). Rows are never deleted — `revoked` stays
as audit history.

Quick fleet-level verification (read-only, safe from any terminal):

```
uv run --frozen fleet-policy --root . status
```

prints pending approval / notification counts, and

```
uv run --frozen fleet-policy --root . drift-check
```

exits 0 when no binding is waiting undecided. To inspect one exact binding,
query the `approvals` row for its `rule_key` in the database above.

## Safety properties (why this flow exists)

- Workers physically cannot self-approve: the storage layer refuses any
  decision made while `HERMES_KANBAN_TASK` is set in the environment, and
  the CLI additionally requires a TTY plus the binding suffix.
- The confirm suffix proves you read the exact binding you are acting on;
  a free-text `--by user` claim alone is not sufficient.
