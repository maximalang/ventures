# Decision Ledger v1

Thin decision ledger for the company OS: every material decision
(go / no-go / iterate / kill) is recorded with hypothesis, confidence,
expected impact, cost, kill criterion, kanban task id and evidence refs,
then its outcome (open / hit / missed / killed) is reviewed later. `brief`
renders the last N decisions plus all open outcomes for injection into the
owner digest and decision briefs.

## Attribution

The episodic decision-ledger pattern — decisions persisted in SQLite with an
outcome field, and the 8 most recent decisions injected into every new
briefing — is inspired by
[SenteLabsAI/OpenExecutive](https://github.com/SenteLabsAI/OpenExecutive)
(Apache License 2.0); see `packages/core/openexecutive/memory/episodic.py`
and the "Memory System" section of `docs/architecture.md` there
(head `b071101`). This package is an **original implementation** for the
Hermes/Kanban company OS; no OpenExecutive source code was copied. Per the
owner decision of 07.09.2026 the code is intentionally host-specific (no
portability layer).

## Layout

- `src/decision_ledger/store.py` — schema, validation, CRUD, brief renderer.
- `src/decision_ledger/__init__.py` — public API re-exports.
- `ledger.py` (repo root) — CLI: `add | list | review-outcome | brief`.
- `tests/test_decision_ledger.py` — unit tests (write / read / review / brief).

## Storage

Separate SQLite file `Desktop/all/ventures/.state/decision-ledger.db`
(`.state/` is gitignored). Never touches any other state database.
Override for tests/ad-hoc use with `--db` or the `DECISION_LEDGER_DB`
environment variable.

Schema (`decisions`): `id, ts, scope (portfolio|venture), venture,
hypothesis, decision (go|no-go|iterate|kill), confidence (0..1),
expected_impact, cost_rub, kill_criterion, kanban_task_id,
evidence_refs (json), outcome_status (open|hit|missed|killed),
outcome_reviewed_at, outcome_note`.

## Usage

```bash
python ledger.py add --scope venture --venture rr --decision go \
    --hypothesis "landing rewrite lifts signup CTR" --confidence 0.7 \
    --expected-impact "+15% CTR" --cost-rub 30000 \
    --kill-criterion "CTR below baseline in 14 days" \
    --kanban-task-id t_4dbcd5da \
    --evidence-ref "https://github.com/maximalang/ventures/pull/1"

python ledger.py list --outcome open
python ledger.py list --json --limit 20
python ledger.py review-outcome 3 --outcome hit --note "CTR +18% measured"
python ledger.py brief            # last 8 decisions + open outcomes
```

Write discipline: the `company` profile calls `ledger.py add` at the moment
of `decision:company=go/no-go`; outcome review happens when the kill
criterion or expected impact becomes measurable. Integration into the
company process is a separate step, not part of this package.

## Tests

```bash
uv run --frozen python -m pytest tests/test_decision_ledger.py -q
```
