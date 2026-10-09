# fleet-policy — one-time store prune runbook (t_40022daf, v1.2.43)

Operator-only procedure for the legacy event store
(`C:/Users/max/Desktop/all/ventures/.state/fleet-policy.db`, ~450 MB,
retention never executed). After v1.2.42+ is installed the built-in
retention ticks keep the store bounded; THIS runbook is the one-time
catch-up for the historical backlog.

Worker-side contract: a dispatcher worker never runs this. The store path
matches the protected `**/.state/fleet-policy.db*` pattern — worker access
is denied by the gate itself. The worker prepares bundle + this runbook and
blocks with `[continues: company]`; the operator executes.

## Preconditions

1. v1.2.43+ deployed (deploy runbook: fleet-policy-deploy-runbook.md) —
   the prune reuses its maintenance machinery (verified archive before
   delete) and its schema (v5 indexes, maintenance_state ledger).
2. `fleet-policy --root C:/Users/max/Desktop/all/ventures status` works and
   reports `db_size_bytes`.
3. Free disk: at least 1x the store size for the backup snapshot.

## Step 0 — dry-run (read-only, safe any time)

```
python scripts/prune_policy_db.py --root C:/Users/max/Desktop/all/ventures --dry-run
```

Expect: pre-flight counts per table, current size, planned steps. No
writes.

## Step 1 — execute the prune

```
python scripts/prune_policy_db.py --root C:/Users/max/Desktop/all/ventures --yes
```

The script, in order (each step verified before the next):

1. **backup** — SQLite online-backup API snapshot into
   `.state/fleet-policy-backups/prune-<UTC stamp>/fleet-policy.db`
   (consistent even with live writers; NOT a raw file copy of a live WAL
   pair), then MANIFEST.json + MANIFEST.sha256 over the backup dir.
2. **archive + delete** — forced maintenance tick in the one-time-prune
   posture (`preserve_state=True`): expired events (>90 days) exported to
   `.state/fleet-policy-archive/events-*.jsonl.gz` with sha256 sidecars;
   each batch's rows are deleted only AFTER the batch's archive verifies
   (hash + gzip decode + row count). Expired rows of the ledger tables
   (call_history / run_call_history / budget_ledger / run_budget /
   financial_ledger) are deleted per the retention config. The protected
   state tables — task_state, run_state, approvals, notification_outbox —
   are NEVER deleted from by this runbook: their horizon expiry stays the
   scheduled hook tick's job (approvals_days etc.), and the one-time
   catch-up only drains the ledger backlog. The report captures pre/post
   row counts for every protected table (`state_preservation`) and the
   script aborts non-zero if any of them moved.
3. **VACUUM** — full vacuum; activates `auto_vacuum=INCREMENTAL` on the
   legacy store so later ticks drain the freelist gradually.
4. **post-checks** — size/counts delta, protected-state preservation
   asserted (`state_preservation`, all ok), every archive sidecar
   re-verified, PRUNE-REPORT.json written next to the backup.

Expected result for the 2026-10-08 store (~450 MB, ~850k rows, oldest
events from 2026-08): events older than 90 days archived, store size drops
well under the 100 MB soft cap, `status` shows
`maintenance_last_run_epoch` stamped.

## Verify afterwards

```
fleet-policy --root C:/Users/max/Desktop/all/ventures status
sqlite3 "file:C:/Users/max/Desktop/all/ventures/.state/fleet-policy.db?mode=ro" "SELECT COUNT(*) FROM events;"
```

(size reported by `status` drops; event count keeps only the retained
window; the gate keeps working — watch the next worker run for normal
policy_decision events.)

## Rollback

1. Stop the gateway (writers).
2. Copy the backup snapshot over the live path:
   `cp .state/fleet-policy-backups/prune-<stamp>/fleet-policy.db .state/fleet-policy.db`
3. Remove stale `-wal`/`-shm` siblings if present.
4. Start the gateway. The archived rows remain restorable separately via
   the archive replay (INSERT OR IGNORE, PK-deduped) if only history is
   needed.

## Steady state (no operator action needed)

- Retention ticks run from plugin hooks (register / kanban_task_claimed),
  throttled to 24h via the maintenance_state ledger; size guard notifies at
  100 MB (soft) and forces a run at 300 MB (hard).
- `fleet-policy maintenance` is the manual operator tick;
  `--full-vacuum` is only for legacy-store activation (already done by this
  one-time prune).
