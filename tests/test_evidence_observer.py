"""Observe-only integration: no real tools or live stores are exercised."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace


def adapter():
    path = Path(__file__).resolve().parents[1] / 'integrations/hermes/fleet-policy-plugin/__init__.py'
    spec = importlib.util.spec_from_file_location('observer_adapter_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_enabled_observer_runs_after_legacy(monkeypatch):
    module = adapter()
    trace = []
    runtime = SimpleNamespace(config={'evidence_observer_enabled': True},
                              post_tool_call=lambda *a, **k: trace.append('runtime') or {'test': True})
    monkeypatch.setattr(module, 'runtime', lambda: runtime)
    monkeypatch.setattr(module, 'context', lambda kw: {})
    monkeypatch.setattr(module, '_project', lambda p: trace.append('project'))
    monkeypatch.setattr(module, '_observe_evidence', lambda *a: trace.append('observe'), raising=False)
    assert module.post_tool_call('kanban_complete', {'metadata': {'evidence_v1': {}}}) is None
    assert trace == ['runtime', 'project', 'observe']


def test_missing_evidence_has_no_resolution(monkeypatch):
    from fleet_policy import evidence_observer as observer
    monkeypatch.setattr(observer, 'resolve_context', lambda *a: (_ for _ in ()).throw(AssertionError('resolution')))
    assert observer.observe('kanban_complete', {'metadata': {}}, {}, env={}) is None


def test_missing_expectation_is_not_envelope_context(monkeypatch):
    from fleet_policy import evidence_observer as observer
    records = []
    monkeypatch.setattr(observer, '_emit', records.append)
    observer.observe('kanban_complete', {'metadata': {'evidence_v1': {'note': 'DO NOT LOG'}}}, {}, env={})
    assert records[0]['observation_status'] == 'context_unavailable'
    assert records[0]['valid'] is None
    assert 'DO NOT LOG' not in repr(records)


import sqlite3
import pytest


@pytest.fixture
def run_fixture(tmp_path):
    db = tmp_path / 'board.sqlite'
    with sqlite3.connect(db) as conn:
        conn.execute('CREATE TABLE task_runs (id INTEGER PRIMARY KEY, task_id TEXT, profile TEXT, status TEXT)')
        conn.execute("INSERT INTO task_runs VALUES (7, 't_12345678', 'qa', 'done')")
    return {'HERMES_KANBAN_DB': str(db), 'HERMES_KANBAN_BOARD': 'fleet-ops',
            'HERMES_KANBAN_TASK': 't_12345678', 'HERMES_KANBAN_RUN_ID': '7', 'HERMES_PROFILE': 'qa'}


@pytest.mark.parametrize('actor,run,quality', [('qa', 7, 'run_matched_expectation_missing'),
                                               ('tech', 7, 'run_identity_mismatch'),
                                               ('qa', 8, 'run_unknown')])
def test_completed_run_resolution(monkeypatch, run_fixture, actor, run, quality):
    from fleet_policy import evidence_observer as observer
    records = []
    monkeypatch.setattr(observer, '_emit', records.append)
    env = dict(run_fixture, HERMES_KANBAN_RUN_ID=str(run))
    observer.observe('kanban_complete', {'metadata': {'evidence_v1': {}}, 'assignee': 'someone_else'},
                     {'profile_name': actor, 'run_id': run, 'tool_call_id': 'call_123'}, env=env)
    assert records[0]['context_provenance_quality'] == quality
    assert records[0]['invocation']['actor'] == actor
    assert records[0]['valid'] is None


@pytest.mark.parametrize('bad', ['huge', 'deep', 'cycle', 'object'])
def test_bounded_input(monkeypatch, bad):
    from fleet_policy import evidence_observer as observer
    value = {'note': 'x' * 70000}
    if bad == 'deep':
        value = {}
        for _ in range(20):
            value = {'a': value}
    if bad == 'cycle':
        value = {}; value['self'] = value
    if bad == 'object':
        value = object()
    records = []
    monkeypatch.setattr(observer, '_emit', records.append)
    observer.observe('kanban_complete', {'metadata': {'evidence_v1': value}}, {}, env={})
    assert records[0]['observation_status'] == 'validator_error'
    assert records[0]['valid'] is None


def test_toggle_off_no_extra_runtime_lookup(monkeypatch):
    module = adapter()
    calls = []
    instance = SimpleNamespace(config={}, post_tool_call=lambda *a, **kw: None)
    monkeypatch.setattr(module, 'runtime', lambda: calls.append('lookup') or instance)
    monkeypatch.setattr(module, 'context', lambda kw: {})
    module.post_tool_call('kanban_complete', {})
    assert calls == ['lookup']


import copy
from test_evidence_identity import envelope, context as trusted_fixture, NOW


@pytest.mark.parametrize('invalid', [False, True])
def test_validated_fixture_is_not_live_provenance(monkeypatch, invalid):
    from fleet_policy import evidence_observer as observer
    e, expected = envelope(), trusted_fixture()  # separate independent fixture snapshots
    if invalid:
        e['decision_revision'] = 99
    original = copy.deepcopy((e, expected))
    records = []
    monkeypatch.setattr(observer, '_emit', records.append)
    monkeypatch.setattr(observer, 'datetime', SimpleNamespace(now=lambda zone: NOW))
    monkeypatch.setattr(observer, 'resolve_context', lambda invocation, env: (expected, 'independent_fixture'))
    observer.observe('kanban_complete', {'metadata': {'evidence_v1': e}}, {}, env={})
    assert records[0]['observation_status'] == 'validated'
    assert records[0]['valid'] is (not invalid)
    assert (e, expected) == original
    assert 'relative_path' not in repr(records)


@pytest.mark.parametrize('failure', ['resolver', 'validator', 'logger'])
def test_observer_failures_are_diagnostics_only(monkeypatch, failure):
    from fleet_policy import evidence_observer as observer
    records = []
    def fail(*a, **kw):
        raise RuntimeError('PRIVATE ERROR TEXT')
    monkeypatch.setattr(observer, '_emit', records.append)
    monkeypatch.setattr(observer, 'resolve_context', lambda *a: (trusted_fixture(), 'independent_fixture'))
    monkeypatch.setattr(observer, {'resolver': 'resolve_context', 'validator': 'validate_evidence_v1', 'logger': '_emit'}[failure], fail)
    assert observer.observe('kanban_complete', {'metadata': {'evidence_v1': envelope()}}, {}, env={}) is None
    if failure != 'logger':
        assert records[0]['observation_status'] == 'validator_error'
        assert records[0]['valid'] is None
        assert 'PRIVATE' not in repr(records)


@pytest.mark.parametrize('fault', [None, 'context', 'runtime', 'project', 'observer'])
@pytest.mark.parametrize('status', ['ok', 'error'])
def test_differential_legacy_trace(monkeypatch, fault, status):
    results = []
    for enabled in (False, True):
        module = adapter()
        trace, diagnostics = [], []
        args = {'metadata': {'evidence_v1': envelope()}}
        before = copy.deepcopy(args)
        error = ValueError('same legacy exception')
        def ctx(kw):
            trace.append(('context', copy.deepcopy(kw)))
            if fault == 'context':
                raise error
            return {'profile': 'assignee', 'task_status': 'done'}
        def post(*a, **kw):
            trace.append(('runtime', copy.deepcopy((a, kw))))
            if fault == 'runtime':
                raise error
            return {'rule_id': 'fixture'}
        def project(p):
            trace.append(('project', copy.deepcopy(p)))
            if fault == 'project':
                raise error
        def obs(*a):
            diagnostics.append('observation')
            if fault == 'observer':
                raise RuntimeError('observer only')
        instance = SimpleNamespace(config={'evidence_observer_enabled': enabled}, post_tool_call=post)
        monkeypatch.setattr(module, 'runtime', lambda: instance)
        monkeypatch.setattr(module, 'context', ctx)
        monkeypatch.setattr(module, '_project', project)
        monkeypatch.setattr(module, '_observe_evidence', obs)
        try:
            result = module.post_tool_call('kanban_complete', args, status=status, profile_name='qa')
            outcome = ('return', result)
        except ValueError as caught:
            assert caught is error
            outcome = ('error', type(caught), str(caught))
        assert args == before
        assert bool(diagnostics) == (enabled and fault not in ('context', 'runtime', 'project'))
        results.append((outcome, trace, args))
    assert results[0] == results[1]


def test_duplicate_diagnostics_do_not_replay_action(monkeypatch, run_fixture):
    from fleet_policy import evidence_observer as observer
    records = []
    monkeypatch.setattr(observer, '_emit', records.append)
    args = {'metadata': {'evidence_v1': {}}}
    for _ in range(2):
        observer.observe('kanban_complete', args, {'tool_call_id': 'call_123'}, env=run_fixture)
    assert len(records) == 2  # harmless logger duplicates, not execution receipts
    assert records[0]['invocation'] == records[1]['invocation']
    assert all(r['valid'] is None for r in records)


def test_locked_run_db_is_unavailable_without_wait(monkeypatch, run_fixture):
    from fleet_policy import evidence_observer as observer
    records = []
    monkeypatch.setattr(observer, '_emit', records.append)
    conn = sqlite3.connect(run_fixture['HERMES_KANBAN_DB'])
    try:
        conn.execute('BEGIN EXCLUSIVE')
        observer.observe('kanban_complete', {'metadata': {'evidence_v1': {}}}, {}, env=run_fixture)
    finally:
        conn.rollback(); conn.close()
    assert records[0]['context_provenance_quality'] == 'run_read_unavailable'


@pytest.mark.parametrize('tool,metadata', [('kanban_create', {'evidence_v1': {}}),
                                         ('kanban_request_review', {}), ('kanban_complete', None)])
def test_ineligible_no_io(monkeypatch, tool, metadata):
    from fleet_policy import evidence_observer as observer
    def fail(*a):
        raise AssertionError('should not reach observation')
    monkeypatch.setattr(observer, '_emit', fail)
    monkeypatch.setattr(observer, 'resolve_context', fail)
    observer.observe(tool, {'metadata': metadata}, {}, env={})


def test_real_runtime_gate_and_budget_differential(monkeypatch, runtime, task_context):
    from fleet_policy import evidence_observer as observer
    module = adapter()
    monkeypatch.setattr(module, 'runtime', lambda: runtime)
    monkeypatch.setattr(module, 'context', lambda kw: dict(task_context))
    monkeypatch.setattr(module, '_project', lambda payload: None)
    # Diagnostic lookup has no locator, and does not reach the fixture policy DB.
    monkeypatch.setattr(module, '_observe_evidence', lambda tool, args, hook: observer.observe(tool, args, hook, env={}))
    states = []
    for enabled in (False, True):
        runtime.config['evidence_observer_enabled'] = enabled
        before = runtime.budget_snapshot(task_context, 'code')
        module.post_tool_call('kanban_complete', {'metadata': {'evidence_v1': {}}}, status='ok')
        after = runtime.budget_snapshot(task_context, 'code')
        with runtime.store.connect() as conn:
            counts = list(conn.iterdump())
        gates = runtime.missing_gates('public_product_action', task_context)
        states.append((before, after, counts, gates, copy.deepcopy(task_context)))
    assert states[0] == states[1]


def test_local_performance(monkeypatch, run_fixture):
    from fleet_policy import evidence_observer as observer
    from time import perf_counter, process_time
    import math
    # Exercise the real logger serialization with a local, nonblocking handler.
    import logging
    class Sink(logging.Handler):
        def emit(self, record):
            record.getMessage()
    handler = Sink()
    monkeypatch.setattr(observer._LOG, 'handlers', [handler])
    monkeypatch.setattr(observer._LOG, 'propagate', False)
    monkeypatch.setattr(observer._LOG, 'level', logging.INFO)
    args = {'metadata': {'evidence_v1': envelope()}}
    module = adapter()
    instance = SimpleNamespace(config={'evidence_observer_enabled': True}, post_tool_call=lambda *a, **kw: None)
    monkeypatch.setattr(module, 'runtime', lambda: instance)
    monkeypatch.setattr(module, 'context', lambda kw: {})
    real_resolver = observer.resolve_context
    expected = trusted_fixture()
    monkeypatch.setattr(observer, 'datetime', SimpleNamespace(now=lambda zone: NOW))
    cpu, total = [], []
    for _ in range(300):
        monkeypatch.setattr(observer, 'resolve_context', lambda *a: (expected, 'independent_fixture'))
        start = process_time()
        # Amortize Windows process clock granularity over a bounded batch.
        for _ in range(100):
            observer.observe('kanban_complete', args, {}, env={})
        cpu.append((process_time() - start) * 1000 / 100)
        monkeypatch.setattr(observer, 'resolve_context', real_resolver)
        monkeypatch.setattr(module, '_observe_evidence', lambda tool, args, hook: observer.observe(tool, args, hook, env=run_fixture))
        start = perf_counter()
        module.post_tool_call('kanban_request_review', args, status='ok')
        total.append((perf_counter() - start) * 1000)
    p95 = lambda data: sorted(data)[math.ceil(len(data) * .95) - 1]
    print(f'PERFORMANCE n=300 pure_observer_cpu_p95_ms={p95(cpu):.4f} adapter_total_p95_ms={p95(total):.4f}')
    assert p95(cpu) < 10
    assert p95(total) < 50


def test_incomplete_expected_snapshot_stays_unavailable(monkeypatch):
    from fleet_policy import evidence_observer as observer
    records = []
    monkeypatch.setattr(observer, '_emit', records.append)
    monkeypatch.setattr(observer, 'resolve_context', lambda *a: (object(), 'incomplete_fixture'))
    observer.observe('kanban_complete', {'metadata': {'evidence_v1': envelope()}}, {}, env={})
    assert records[0]['observation_status'] == 'context_unavailable'
    assert records[0]['valid'] is None


@pytest.mark.parametrize('change', [{'board': 'other'}, {'task_id': 't_87654321'}])
def test_target_not_copied_from_envelope(monkeypatch, run_fixture, change):
    from fleet_policy import evidence_observer as observer
    records = []
    monkeypatch.setattr(observer, '_emit', records.append)
    observer.observe('kanban_request_review', {'metadata': {'evidence_v1': envelope()}, **change}, {}, env=run_fixture)
    assert records[0]['valid'] is None
    assert records[0]['context_provenance_quality'] in ('invocation_unavailable', 'run_identity_mismatch')
    assert records[0]['invocation']['operation'] == 'kanban_request_review'


@pytest.mark.parametrize('mode', ['success', 'runtime_error', 'project_error'])
def test_original_base_hook_matches_candidate(monkeypatch, mode):
    import ast
    import subprocess
    source = subprocess.check_output([
        'git', 'show', '8fafc3713c44f7ab0046696cc45e81cca69cb597:'
        'integrations/hermes/fleet-policy-plugin/__init__.py'], text=True)
    original = next(node for node in ast.parse(source).body
                    if isinstance(node, ast.FunctionDef) and node.name == 'post_tool_call')
    results = []
    for kind in ('original', 'off', 'on'):
        module = adapter()
        if kind == 'original':
            exec(compile(ast.Module(body=[original], type_ignores=[]), '<base-hook>', 'exec'), module.__dict__)
        trace = []
        def post(*args, **kwargs):
            trace.append(('runtime', args, kwargs))
            if mode == 'runtime_error':
                raise ValueError('legacy-runtime')
            return {'legacy': True}
        def project(payload):
            trace.append(('project', payload))
            if mode == 'project_error':
                raise ValueError('legacy-project')
        instance = SimpleNamespace(config={'evidence_observer_enabled': kind == 'on'}, post_tool_call=post)
        monkeypatch.setattr(module, 'runtime', lambda: instance)
        monkeypatch.setattr(module, 'context', lambda kw: {'profile': 'assignee', 'tool_call_id': 'call_1'})
        monkeypatch.setattr(module, '_project', project)
        monkeypatch.setattr(module, '_observe_evidence', lambda *a: None)
        args = {'metadata': {'evidence_v1': {}}, 'task_id': 't_12345678'}
        try:
            outcome = module.post_tool_call('kanban_complete', args, status='ok')
        except ValueError as exc:
            outcome = (type(exc), str(exc))
        results.append((trace, args, outcome))
    assert results[0] == results[1] == results[2]
