"""Post-handoff telemetry only. Never consumed by policy or lifecycle code.

No expectation issuer exists in the baseline. Production resolution deliberately
returns unavailable; a submitted envelope cannot supply an expectation. The
validated branches are exercised with independent fixture snapshots in tests.
"""
from datetime import datetime, timezone
import json
import logging
import os
import re
import sqlite3
from pathlib import Path
from time import perf_counter

from .evidence_identity import validate_evidence_v1

_LOG = logging.getLogger(__name__)
VERSION = '0.2.0'
ELIGIBLE = ('kanban_complete', 'kanban_request_review')


def _token(value, pattern=r'[A-Za-z0-9_-]{1,96}'):
    return value if type(value) is str and re.fullmatch(pattern, value) else None


def invocation(tool, arguments, hook, env):
    # Tool args identify the invoked target, NEVER the submitted envelope.
    # Conflicting explicit/pinned board context is unresolved, not scanned.
    board = arguments.get('board') or env.get('HERMES_KANBAN_BOARD') or hook.get('board')
    task = arguments.get('task_id') or env.get('HERMES_KANBAN_TASK')
    run = hook.get('run_id') or env.get('HERMES_KANBAN_RUN_ID')
    run = int(run) if type(run) in (str, int) and re.fullmatch(r'[0-9]{1,18}', str(run)) else None
    conflict = any(v and v != board for v in (env.get('HERMES_KANBAN_BOARD'), hook.get('board')))
    pinned_run = env.get('HERMES_KANBAN_RUN_ID')
    conflict |= bool(pinned_run and str(run) != pinned_run)
    return {'operation': tool, 'kind': 'kanban_handoff',
            'board': None if conflict else _token(board, r'[a-z0-9][a-z0-9_-]{0,63}'),
            'task_id': _token(task, r't_[0-9a-f]{8}'), 'run_id': run,
            'actor': _token(hook.get('profile_name') or env.get('HERMES_PROFILE')),
            'tool_call_id': _token(hook.get('tool_call_id'))}


def resolve_context(invocation, env):
    if not all(invocation.get(k) for k in ('board', 'task_id', 'run_id', 'actor')):
        return None, 'invocation_unavailable'
    # Only dispatcher-pinned local DB. Do not guess board mappings, scan boards,
    # load comments or use post-handoff current_run_id (it can already be null).
    raw_path = env.get('HERMES_KANBAN_DB')
    if not raw_path or raw_path.startswith(('\\\\', '//')):
        return None, 'db_locator_unavailable'
    path = Path(raw_path)
    if not path.is_absolute():
        return None, 'db_locator_unavailable'
    try:
        conn = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=0)
        try:
            # Bounded VM work, zero lock waiting, exact primary-key lookup.
            conn.set_progress_handler(lambda: 1, 2000)
            row = conn.execute(
                'SELECT task_id,profile FROM task_runs WHERE id=?',
                (invocation['run_id'],),
            ).fetchone()
        finally:
            conn.close()
    except sqlite3.Error:
        return None, 'run_read_unavailable'
    if row is None:
        return None, 'run_unknown'
    if row != (invocation['task_id'], invocation['actor']):
        return None, 'run_identity_mismatch'
    # Existing run metadata is submitted by the worker, not an independently
    # issued decision/subject/artifact/environment expectation. Never promote it.
    return None, 'run_matched_expectation_missing'


def _bounded_snapshot(value):
    # Bound allocation/traversal BEFORE copying; do not stringify custom objects.
    budget = 65536
    nodes = 0

    def visit(item, depth):
        nonlocal budget, nodes
        nodes += 1
        budget -= 8
        if depth > 16 or nodes > 4096 or budget < 0:
            raise ValueError('observer input limit')
        if type(item) is str:
            budget -= len(item) * 6
            if budget < 0:
                raise ValueError('observer input limit')
            return item
        if type(item) is dict:
            if len(item) > 4096:
                raise ValueError('observer input limit')
            result = {}
            for key, child in item.items():
                if type(key) is not str:
                    raise ValueError('observer input type')
                result[visit(key, depth + 1)] = visit(child, depth + 1)
            return result
        if type(item) is list:
            if len(item) > 4096:
                raise ValueError('observer input limit')
            return [visit(child, depth + 1) for child in item]
        if item is None or type(item) in (bool, float):
            return item
        if type(item) is int and item.bit_length() <= 64:
            return item
        raise ValueError('observer input type')

    return visit(value, 0)


def _emit(record):
    # Existing Python logging infrastructure only; no handler, queue or outbox.
    _LOG.info('%s', json.dumps(record, separators=(',', ':'), sort_keys=True))


def observe(tool_name, arguments, hook, *, env=None):
    if tool_name not in ELIGIBLE or type(arguments) is not dict:
        return
    metadata = arguments.get('metadata')
    if type(metadata) is not dict or 'evidence_v1' not in metadata:
        return
    started = perf_counter()
    record = {
        'schema': 'hermes-evidence-observation/v1', 'observer_version': VERSION,
        'mode': 'post_tool_metadata', 'scope': 'observe_only', 'invocation': {},
        'observed_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'observation_status': 'context_unavailable', 'valid': None,
        'codes': ['CONTEXT_UNAVAILABLE'], 'evidence_sha256': None,
        'context_provenance_quality': 'unavailable', 'timing_ms': 0,
    }
    try:
        snapshot = _bounded_snapshot(metadata['evidence_v1'])
        environ = os.environ if env is None else env
        record['invocation'] = invocation(tool_name, arguments, hook, environ)
        expected, quality = resolve_context(record['invocation'], environ)
        record['context_provenance_quality'] = quality
        if expected is not None:
            verdict = validate_evidence_v1(snapshot, expected, now=datetime.now(timezone.utc))
            if verdict.codes == ('CONTEXT_UNAVAILABLE',):
                record.update(codes=list(verdict.codes))
            else:
                record.update(observation_status='validated', valid=verdict.valid,
                              codes=list(verdict.codes), evidence_sha256=verdict.evidence_sha256)
    except Exception:
        record.update(observation_status='validator_error', valid=None,
                      codes=['OBSERVER_ERROR'], evidence_sha256=None)
    record['timing_ms'] = round((perf_counter() - started) * 1000, 3)
    try:
        _emit(record)
    except Exception:
        # No recursive logging, retry or tool invocation on diagnostic failure.
        pass
