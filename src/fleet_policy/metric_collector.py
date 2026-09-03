"""Deterministic read-only collector for the three primary demand metrics.

Implements Phase 1 of the autonomous loop per DEMAND_METRIC_SOURCE_CONTRACT_V3
(kanban attachment of card t_dbb4235b, board fleet-ops) and the task contract
of card t_84ded8a3.

Design decisions (architectural, recorded for QA):

1. Data access is ONLY the official ``hermes kanban`` CLI in read mode
   (``list --archived --json`` and ``runs --json``). No direct sqlite/DB
   reads. The CLI is invoked with HERMES_KANBAN_DB / HERMES_KANBAN_BOARD
   removed from the child environment: when those variables are present they
   pin the CLI to one board and silently override ``--board`` (verified
   empirically: identical dumps for four different boards while the env vars
   were set).

2. Byte idempotency. The snapshot bytes depend only on (a) the local run
   date and (b) board data. ``observed_at`` is the timestamp of the latest
   counted source fact (a card ``completed_at``), never the wall clock at
   run time, so two same-day runs produce identical bytes. Serialization is
   ``json.dumps(..., sort_keys=True, indent=2, ensure_ascii=False) + "\\n"``.

3. No invented values. A metric with no qualifying evidence is emitted as
   ``value = null``, ``observed_at = null`` plus an explicit stable
   ``evidence_gap`` code (schema nullability invariant: value/observed_at
   are null iff evidence_gap is non-null).

4. Records carry EXACTLY the 12 schema fields. Evidence references must
   therefore live outside the record: the snapshot has a top-level
   ``evidence`` object keyed by metric_id, and each record's ``source_ref``
   is an opaque pointer into THIS snapshot document (``#/evidence/<metric>``),
   never a live locator.

Metric rules (deterministic):

* accepted_evidence_backed_leads_28d (rr-team): completed cards in the
  28-day window whose completion metadata/summary/result carries a LEAD
  outcome marker (accepted|contacted|replied|won). A bare prose occurrence
  of e.g. "accepted" in a QA review is not a lead outcome; a marker counts
  only in lead context: (a) structured - a metadata key named
  outcome/lead_outcome/lead_status/исход whose value is an enum token; or
  (b) prose - the enum token as a whole word within 60 characters of a
  lead-domain word (lead/лид/кандидат/candidate/outreach/отклик...).
  No qualifying marker -> evidence_gap rr_lead_outcome_markers_absent.

* evidence_backed_go_no_go_decisions_28d (fleet-ops + portfolio): completed
  cards whose completed-run metadata carries key ``company_decisions`` (each
  entry = one decision) or key ``verdict`` together with at least one
  evidence key (contains 'finding'/'evidence', equals 'checks', or starts
  with 'check'). Each card contributes len(company_decisions) decisions, or
  1 for the verdict+evidence shape. No qualifying card ->
  evidence_gap company_decision_markers_absent.

* successful_organic_calculations_28d (seo-site): Yandex Metrica counter
  112116194, read-only. The collector checks only for the PRESENCE of a
  Metrika token env variable (name match, value never printed or read into
  the snapshot). Absent -> evidence_gap metrica_token_unavailable. Present
  -> Phase 1 does not perform live API calls (a network fetch would break
  byte idempotency and is untestable without a token); stable gap
  metrica_goal_configuration_unknown marks the Phase 1b slice.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

CONTRACT_NAME = "demand_metric_source_contract"
CONTRACT_VERSION = "3.0-collector"
GENERATOR = "metric_collector_v1"
WINDOW_DAYS = 28
DEFAULT_OUT_DIR = Path("C:/Users/max/Desktop/all/metric-snapshots")

LEAD_OUTCOME_TOKENS = ("accepted", "contacted", "replied", "won")
LEAD_CONTEXT_WORDS = (
    "lead", "leads", "лид", "лида", "лиды", "лидов", "лидом",
    "кандидат", "кандидата", "кандидаты", "кандидатов", "candidate",
    "outreach", "аутрич", "отклик", "отклики",
)
MARKER_RE = re.compile(r"\b(accepted|contacted|replied|won)\b", re.IGNORECASE)
CONTEXT_RE = re.compile(
    "|".join(re.escape(w) for w in LEAD_CONTEXT_WORDS), re.IGNORECASE
)
STRUCTURED_OUTCOME_KEY_RE = re.compile(
    r"^(lead[_ -]?outcome|outcome|lead[_ -]?status|исход)$", re.IGNORECASE
)
EVIDENCE_KEY_RE = re.compile(
    r"(finding|evidence)|^checks$|^check_", re.IGNORECASE
)
METRIKA_TOKEN_NAME_RE = re.compile(r"(metrika|metrica)", re.IGNORECASE)
METRIKA_COUNTER_ID = "112116194"

SCHEMA_FIELDS = (
    "project", "board", "metric_id", "metric_class", "definition", "unit",
    "source_type", "source_ref", "observed_at", "value", "confidence",
    "evidence_gap",
)

RECORDS_SPEC = (
    {
        "project": "recruiter-radar",
        "board": "rr-team",
        "metric_id": "accepted_evidence_backed_leads_28d",
        "definition": (
            "Число evidence-backed лидов, принятых в работу, за скользящее "
            "28-дневное окно (исходы accepted|contacted|replied|won)"
        ),
        "unit": "leads",
    },
    {
        "project": "seo-site",
        "board": "seo-site",
        "metric_id": "successful_organic_calculations_28d",
        "definition": (
            "Число успешных расчётов на SEO-сайте из органических визитов "
            "за скользящее 28-дневное окно"
        ),
        "unit": "calculations",
    },
    {
        "project": "company-os",
        "board": "fleet-ops",
        "metric_id": "evidence_backed_go_no_go_decisions_28d",
        "definition": (
            "Число закрытых evidence-backed GO/NO-GO решений портфеля за "
            "скользящее 28-дневное окно"
        ),
        "unit": "decisions",
    },
)

# Confidence policy (documented constant, not runtime judgement):
# direct exact-key match on first-party kanban completion metadata -> 0.8.
# Gap records -> null (not assessable without an observed value).
DIRECT_CONFIDENCE = 0.8

GAP_RR_MARKERS = "rr_lead_outcome_markers_absent"
GAP_COMPANY_MARKERS = "company_decision_markers_absent"
GAP_METRIKA_TOKEN = "metrica_token_unavailable"
GAP_METRIKA_GOAL = "metrica_goal_configuration_unknown"


def sanitize_env(env: dict | None = None) -> dict:
    """Child env for the kanban CLI: drop board-pinning variables.

    HERMES_KANBAN_DB / HERMES_KANBAN_BOARD, when present, pin the CLI to a
    single board and override the ``--board`` flag; the collector must query
    four distinct boards, so both are removed.
    """
    base = dict(os.environ if env is None else env)
    base.pop("HERMES_KANBAN_DB", None)
    base.pop("HERMES_KANBAN_BOARD", None)
    return base


class KanbanCliRunner:
    """Read-only adapter over the official ``hermes kanban`` CLI."""

    def __init__(self, env: dict | None = None):
        self._env = sanitize_env(env)

    def _call(self, board: str, *args: str):
        cmd = ["hermes", "kanban", "--board", board, *args, "--json"]
        proc = subprocess.run(
            cmd, capture_output=True, text=True, env=self._env,
            encoding="utf-8",
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"kanban CLI failed rc={proc.returncode}: {' '.join(cmd)}: "
                f"{proc.stderr[:200]}"
            )
        return json.loads(proc.stdout)

    def list_tasks(self, board: str) -> list[dict]:
        return self._call(board, "list", "--archived")

    def runs(self, board: str, task_id: str) -> list[dict]:
        return self._call(board, "runs", task_id)


def compute_window(run_date: _dt.date) -> dict:
    """Rolling 28-day window ending on run_date (inclusive), local time."""
    local_tz = _dt.datetime.now().astimezone().tzinfo
    end_exclusive = _dt.datetime(
        run_date.year, run_date.month, run_date.day, tzinfo=local_tz
    ) + _dt.timedelta(days=1)
    end_epoch = int(end_exclusive.timestamp())
    start_epoch = end_epoch - WINDOW_DAYS * 86400
    start_dt = _dt.datetime.fromtimestamp(start_epoch, tz=local_tz)
    return {
        "end": end_epoch,
        "end_date": run_date.isoformat(),
        "start": start_epoch,
        "start_date": start_dt.date().isoformat(),
    }


def _iter_strings(value, out: list) -> None:
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for v in value.values():
            _iter_strings(v, out)
    elif isinstance(value, list):
        for v in value:
            _iter_strings(v, out)


def _completed_cards(tasks: list[dict], window: dict) -> list[dict]:
    return sorted(
        (
            t for t in tasks
            if t.get("completed_at")
            and window["start"] <= int(t["completed_at"]) < window["end"]
        ),
        key=lambda t: (int(t["completed_at"]), t.get("id") or ""),
    )


def _completed_runs(runs: list[dict]) -> list[dict]:
    return [r for r in runs if r.get("outcome") == "completed"]


def _lead_marker_in_text(text: str) -> bool:
    """Tier B: enum token within 60 chars of a lead-domain word."""
    for m in MARKER_RE.finditer(text):
        lo = max(0, m.start() - 60)
        hi = min(len(text), m.end() + 60)
        if CONTEXT_RE.search(text[lo:hi]):
            return True
    return False


def _structured_lead_marker(metadata) -> bool:
    """Tier A: an outcome-named key whose value is an enum token."""
    if not isinstance(metadata, dict):
        return False
    for key, value in metadata.items():
        if not STRUCTURED_OUTCOME_KEY_RE.match(str(key)):
            continue
        values = value if isinstance(value, list) else [value]
        for v in values:
            if isinstance(v, str) and v.strip().lower() in LEAD_OUTCOME_TOKENS:
                return True
    return False


def collect_rr_leads(runner, window: dict) -> dict:
    spec = RECORDS_SPEC[0]
    tasks = runner.list_tasks(spec["board"])
    completed = _completed_cards(tasks, window)
    counted: list[dict] = []
    scanned_texts = 0
    for task in completed:
        runs = runner.runs(spec["board"], task["id"])
        comp = _completed_runs(runs)
        matched = False
        for run in comp:
            if _structured_lead_marker(run.get("metadata")):
                matched = True
                break
        if not matched:
            texts: list[str] = []
            if task.get("result"):
                texts.append(task["result"])
            for run in comp:
                if run.get("summary"):
                    texts.append(run["summary"])
                _iter_strings(run.get("metadata"), texts)
            scanned_texts += len(texts)
            matched = any(_lead_marker_in_text(t) for t in texts)
        if matched:
            counted.append({
                "board": spec["board"],
                "completed_at": int(task["completed_at"]),
                "task_id": task["id"],
            })
    if counted:
        return _valued_result(spec, counted, len(counted), window)
    return _gap_result(
        spec, GAP_RR_MARKERS, window,
        note=(
            "completed cards scanned; no lead-context outcome marker "
            "(accepted|contacted|replied|won) found in completion "
            "metadata/summary/result"
        ),
        scanned_cards=len(completed), scanned_texts=scanned_texts,
    )


def _has_evidence_key(metadata: dict) -> bool:
    return any(EVIDENCE_KEY_RE.search(str(k)) for k in metadata)


def collect_company_decisions(runner, window: dict) -> dict:
    spec = RECORDS_SPEC[2]
    counted: list[dict] = []
    total_decisions = 0
    scanned_cards = 0
    for board in ("fleet-ops", "portfolio"):
        tasks = runner.list_tasks(board)
        for task in _completed_cards(tasks, window):
            scanned_cards += 1
            runs = runner.runs(board, task["id"])
            merged_decisions: dict = {}
            verdict_with_evidence = False
            for run in _completed_runs(runs):
                md = run.get("metadata")
                if not isinstance(md, dict):
                    continue
                cd = md.get("company_decisions")
                if isinstance(cd, dict):
                    merged_decisions.update(cd)
                elif isinstance(cd, list):
                    for i, item in enumerate(cd):
                        merged_decisions[f"item_{i}"] = item
                if "verdict" in md and _has_evidence_key(md):
                    verdict_with_evidence = True
            if merged_decisions:
                n = len(merged_decisions)
            elif verdict_with_evidence:
                n = 1
            else:
                continue
            total_decisions += n
            counted.append({
                "board": board,
                "completed_at": int(task["completed_at"]),
                "decisions": n,
                "task_id": task["id"],
            })
    if counted:
        result = _valued_result(spec, counted, total_decisions, window)
        result["scanned_cards"] = scanned_cards
        return result
    return _gap_result(
        spec, GAP_COMPANY_MARKERS, window,
        note=(
            "completed cards on fleet-ops and portfolio scanned; no "
            "company_decisions key and no verdict-with-evidence-key found"
        ),
        scanned_cards=scanned_cards,
    )


def collect_seo(env: dict | None = None) -> dict:
    spec = RECORDS_SPEC[1]
    environment = dict(os.environ if env is None else env)
    token_present = any(
        METRIKA_TOKEN_NAME_RE.search(name) for name in environment
    )
    if not token_present:
        return _gap_result(
            spec, GAP_METRIKA_TOKEN, None,
            note=(
                "no Metrika token variable present in the environment "
                "(checked variable NAMES only; values never read or "
                f"printed); counter {METRIKA_COUNTER_ID} not queried"
            ),
        )
    # Token present: Phase 1 deliberately performs no live network fetch.
    # A live read-only Metrika call belongs to Phase 1b: it would break
    # byte-idempotency of same-day snapshots and cannot be exercised here.
    return _gap_result(
        spec, GAP_METRIKA_GOAL, None,
        note=(
            "Metrika token variable detected (name only); live read-only "
            "API fetch is Phase 1b and is not executed by this collector"
        ),
    )


def _evidence_ref(metric_id: str) -> str:
    return f"#/evidence/{metric_id}"


def _valued_result(spec: dict, counted: list[dict], value: int,
                   window: dict) -> dict:
    observed_at = max(c["completed_at"] for c in counted)
    return {
        "record": _record(
            spec,
            source_type="board_handoff",
            observed_at=observed_at,
            value=value,
            confidence=DIRECT_CONFIDENCE,
            evidence_gap=None,
        ),
        "evidence": {
            "counted_cards": counted,
            "note": (
                "value derived from completion metadata of completed "
                "kanban cards in the window; observed_at is the latest "
                "counted card completed_at"
            ),
            "observed_at_source": "max(completed_at) of counted cards",
            "rule_version": GENERATOR,
            "scanned_window": window,
        },
        "scanned_cards": len(counted),
    }


def _gap_result(spec: dict, gap: str, window: dict | None, note: str,
                **extra) -> dict:
    evidence = {
        "counted_cards": [],
        "note": note,
        "rule_version": GENERATOR,
    }
    if window is not None:
        evidence["scanned_window"] = window
    evidence.update(extra)
    return {
        "record": _record(
            spec,
            source_type="board_handoff",
            observed_at=None,
            value=None,
            confidence=None,
            evidence_gap=gap,
        ),
        "evidence": evidence,
        "scanned_cards": extra.get("scanned_cards", 0),
    }


def _record(spec: dict, *, source_type: str, observed_at, value,
            confidence, evidence_gap) -> dict:
    return {
        "project": spec["project"],
        "board": spec["board"],
        "metric_id": spec["metric_id"],
        "metric_class": "leading",
        "definition": spec["definition"],
        "unit": spec["unit"],
        "source_type": source_type,
        "source_ref": _evidence_ref(spec["metric_id"]),
        "observed_at": observed_at,
        "value": value,
        "confidence": confidence,
        "evidence_gap": evidence_gap,
    }


def validate_snapshot(snapshot: dict) -> list[str]:
    """Return a list of violations (empty = valid)."""
    problems: list[str] = []
    for key in ("contract", "version", "generator", "window", "records"):
        if key not in snapshot:
            problems.append(f"missing top-level key: {key}")
    records = snapshot.get("records")
    if not isinstance(records, list) or len(records) != 3:
        problems.append("records must contain exactly 3 entries")
        return problems
    for rec in records:
        keys = set(rec)
        if keys != set(SCHEMA_FIELDS):
            problems.append(
                f"{rec.get('metric_id')}: field set deviates from the "
                f"12-field schema; extra={sorted(keys - set(SCHEMA_FIELDS))} "
                f"missing={sorted(set(SCHEMA_FIELDS) - keys)}"
            )
            continue
        has_gap = rec["evidence_gap"] is not None
        if (rec["value"] is None) != has_gap:
            problems.append(
                f"{rec['metric_id']}: nullability invariant violated "
                "(value must be null iff evidence_gap is set)"
            )
        if (rec["observed_at"] is None) != has_gap:
            problems.append(
                f"{rec['metric_id']}: nullability invariant violated "
                "(observed_at must be null iff evidence_gap is set)"
            )
        if rec["metric_class"] not in ("revenue", "leading", "gate_removal"):
            problems.append(f"{rec['metric_id']}: bad metric_class")
        if rec["confidence"] is not None and not (
                0 <= float(rec["confidence"]) <= 1):
            problems.append(f"{rec['metric_id']}: confidence out of 0..1")
        if rec["value"] is not None and rec["metric_id"] not in snapshot.get(
                "evidence", {}):
            problems.append(
                f"{rec['metric_id']}: non-null value without evidence block"
            )
    return problems


def serialize(snapshot: dict) -> str:
    return json.dumps(
        snapshot, sort_keys=True, indent=2, ensure_ascii=False
    ) + "\n"


def build_snapshot(runner, window: dict, env: dict | None = None) -> dict:
    rr = collect_rr_leads(runner, window)
    seo = collect_seo(env)
    company = collect_company_decisions(runner, window)
    snapshot = {
        "contract": CONTRACT_NAME,
        "version": CONTRACT_VERSION,
        "generator": GENERATOR,
        "window": window,
        "records": [rr["record"], seo["record"], company["record"]],
        "evidence": {
            rr["record"]["metric_id"]: rr["evidence"],
            seo["record"]["metric_id"]: seo["evidence"],
            company["record"]["metric_id"]: company["evidence"],
        },
    }
    problems = validate_snapshot(snapshot)
    if problems:
        raise ValueError("snapshot failed self-validation: " + "; ".join(problems))
    return snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--date", default=None,
        help="window end date YYYY-MM-DD (default: local today)",
    )
    parser.add_argument(
        "--out-dir", default=str(DEFAULT_OUT_DIR),
        help="snapshot output directory",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="print sha256 and path without writing the file",
    )
    args = parser.parse_args(argv)

    if args.date:
        run_date = _dt.date.fromisoformat(args.date)
    else:
        run_date = _dt.datetime.now().astimezone().date()
    window = compute_window(run_date)
    runner = KanbanCliRunner()
    snapshot = build_snapshot(runner, window)
    text = serialize(snapshot)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    out_path = Path(args.out_dir) / f"snapshot-{run_date.isoformat()}.json"
    if not args.dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # write_bytes: text-mode write_text would translate '\n' to the OS
        # line separator (CRLF on Windows), making on-disk bytes differ
        # from the serialized canonical bytes and breaking the reported
        # sha256 evidence. Exact bytes only.
        out_path.write_bytes(text.encode("utf-8"))
    print(f"sha256={digest}")
    print(f"path={out_path}")
    print(f"window={window['start_date']}..{window['end_date']}")
    for rec in snapshot["records"]:
        print(
            f"record {rec['metric_id']}: value={rec['value']} "
            f"observed_at={rec['observed_at']} gap={rec['evidence_gap']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
