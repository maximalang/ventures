"""Read-only audit of exact allowed Dots/Hermes artifacts; no retrieved code execution.
Writes only this audit directory. Real board DBs are never opened by this script.
The in-memory fixture executes three AST-extracted native helpers, not a launcher.
"""
from __future__ import annotations
import ast
import collections
import contextlib
import datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from typing import Optional
import zipfile

STD = Path('C:/Users/max/Desktop/all/ventures/docs/fleet-ops/dots-hermes-standard-20261004')
OUT = Path('C:/Users/max/Desktop/all/ventures/docs/fleet-ops/dots-quality-audit-20261004')
SRC = Path('C:/Users/max/AppData/Local/hermes/hermes-agent')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def save(name, obj):
    data = (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    target = OUT / name
    assert target.parent == OUT
    tmp = target.with_suffix(target.suffix + '.tmp')
    tmp.write_bytes(data)
    json.loads(tmp.read_text(encoding='utf-8'))
    tmp.replace(target)
    return {'file': name, 'bytes': len(data), 'sha256': sha(data)}

def strict_json(data):
    duplicates = []
    def pairs(items):
        seen = set()
        for key, value in items:
            if key in seen:
                duplicates.append(key)
            seen.add(key)
        return dict(items)
    obj = json.loads(data, object_pairs_hook=pairs)
    return obj, duplicates

OUT.mkdir(parents=True, exist_ok=True)
baseline = json.loads((STD / 'BASELINE.json').read_text(encoding='utf-8'))
apply = json.loads((STD / 'APPLY.json').read_text(encoding='utf-8'))
apply_by_profile = {t['profile']: t for t in apply['per_target']}
reference = (STD / 'REFERENCE-CANDIDATE.md').read_bytes()
hook = (STD / 'HOOK-CANDIDATE.md').read_bytes()
old_hook = Path('C:/Users/max/Desktop/all/ventures/docs/fleet-ops/dots-20261003/LOAD-HOOK.md').read_bytes()
live = []
for target in baseline['targets']:
    root_path = Path(target['root_path'])
    ref_path = Path(target['reference_path'])
    root, ref = root_path.read_bytes(), ref_path.read_bytes()
    expected = apply_by_profile[target['profile']]
    before_root = Path(target['snapshots']['root']['path']).read_bytes()
    before_ref = Path(target['snapshots']['reference']['path']).read_bytes()
    backup_dir = STD / 'apply-backups' / target['profile']
    checks = {
        'reference_exact': ref == reference,
        'hook_once': root.count(hook) == 1,
        'old_hook_absent': root.count(old_hook) == 0,
        'root_matches_after': sha(root) == expected['after_root_sha256'],
        'root_preservation': root.removesuffix(hook) == before_root.removesuffix(old_hook),
        'before_root_binding': sha(before_root) == target['before_root_sha256'],
        'before_reference_binding': sha(before_ref) == target['before_reference_sha256'],
        'backup_root_exact': (backup_dir / 'SKILL.md').read_bytes() == before_root,
        'backup_reference_exact': (backup_dir / 'dots-operating-method.md').read_bytes() == before_ref,
    }
    live.append({'profile': target['profile'], 'root': str(root_path), 'reference': str(ref_path),
                 'root_sha256': sha(root), 'reference_sha256': sha(ref), 'checks': checks,
                 'root_text_snapshot': root.decode('utf-8'), 'reference_text_snapshot': ref.decode('utf-8')})
live_receipt = save('LIVE-SNAPSHOT.json', {'generated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope': 'Only the exact 24 allowlisted live SKILL/reference files and exact preimages/backups from BASELINE',
    'target_count': len(live), 'passed_checks': sum(sum(c is True for c in t['checks'].values()) for t in live),
    'total_checks': sum(len(t['checks']) for t in live), 'targets': live})

inventory, json_results, ast_errors, groups = [], [], [], collections.defaultdict(list)
for path in sorted(STD.rglob('*')):
    if not path.is_file() or '__pycache__' in path.parts:
        continue
    assert not path.name.startswith('.env')
    data = path.read_bytes()
    rel = path.relative_to(STD).as_posix()
    record = {'path': rel, 'bytes': len(data), 'sha256': sha(data)}
    inventory.append(record)
    groups[record['sha256']].append(record)
    if path.suffix.lower() == '.json':
        try:
            obj, dupes = strict_json(data)
            json_results.append({'path': rel, 'parsed': True, 'duplicate_keys': dupes})
        except Exception as ex:
            json_results.append({'path': rel, 'parsed': False, 'error': str(ex)})
    if path.suffix.lower() == '.py':
        try:
            ast.parse(data.decode('utf-8-sig'))
        except Exception as ex:
            ast_errors.append({'path': rel, 'error': str(ex)})

duplicate_groups = [{'sha256': h, 'bytes_each': members[0]['bytes'], 'paths': [m['path'] for m in members]}
                    for h, members in groups.items() if len(members) > 1]
zip_path = STD / 'dots-hermes-standard-20261004.zip'
with zipfile.ZipFile(zip_path) as z:
    manifest = json.loads(z.read('PACKAGE-MANIFEST.json'))
    names = set(z.namelist())
    bad_members = [e['name'] for e in manifest['members'] if e['name'] not in names or
                   sha(z.read(e['name'])) != e['sha256'] or len(z.read(e['name'])) != e['bytes']]
    required_sources = ['qa2321_battery.py', 'qa2321_loader.py', 'QA-CHECKER-RUN2319.py',
                        'APPLY-run2320-20261004T012335Z.json',
                        'preserved-qa2318/qa_dryrun_12targets.py', 'preserved-qa2318/qa_dryrun_stage1.json']
    rollback_routes = []
    for target in baseline['targets']:
        profile = target['profile']
        missing_direct = [f'apply-backups/{profile}/{n}' for n in ['SKILL.md', 'dots-operating-method.md']
                          if f'apply-backups/{profile}/{n}' not in names]
        alternatives = {}
        for field in ['root', 'reference']:
            before_path = Path(target['snapshots'][field]['path'])
            rel = before_path.relative_to(STD).as_posix()
            alternatives[field] = {'path': rel, 'in_zip': rel in names,
                'byte_exact': rel in names and z.read(rel) == before_path.read_bytes()}
        rollback_routes.append({'profile': profile, 'documented_direct_files_missing': missing_direct,
                                'alternative_before_snapshots': alternatives})
    archive = {'sha256': sha(zip_path.read_bytes()), 'bytes': zip_path.stat().st_size,
        'zip_members': len(z.namelist()), 'manifest_payload_count': manifest['member_count'],
        'manifest_entries': len(manifest['members']), 'self_excluded': 'PACKAGE-MANIFEST.json' not in {m['name'] for m in manifest['members']},
        'crc_bad': z.testzip(), 'bad_members': bad_members,
        'named_check_sources_missing': [n for n in required_sources if n not in names],
        'rollback_routes': rollback_routes,
        'local_files_not_archived': [e['path'] for e in inventory if e['path'] != zip_path.name and e['path'] not in names]}

# Execute source-verified helpers against SQLite :memory: ONLY; never connect to a real board.
source_map = {'kanban_db.py': ['_require_task', 'add_comment'],
              'kanban_db_graph.py': ['initial_task_state']}
extracted = []
source_bindings = []
for filename, wanted in source_map.items():
    path = SRC / 'hermes_cli' / filename
    data = path.read_text(encoding='utf-8')
    tree = ast.parse(data)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in wanted:
            code = ast.get_source_segment(data, node)
            source_bindings.append({'file': str(path), 'file_sha256': sha(path.read_bytes()),
                                    'function': node.name, 'line_start': node.lineno,
                                    'line_end': node.end_lineno, 'code': code})
            extracted.append(node)
ns = {'sqlite3': sqlite3, 'time': time, 'Optional': Optional,
      'write_txn': lambda conn, **kw: contextlib.nullcontext(conn),
      '_append_event': lambda *args, **kw: None}
module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)] + extracted, type_ignores=[])
exec(compile(ast.fix_missing_locations(module), '<native-helper-fixture>', 'exec'), ns)
conn = sqlite3.connect(':memory:')
conn.row_factory = sqlite3.Row
conn.execute('CREATE TABLE tasks (id TEXT PRIMARY KEY, status TEXT, tenant TEXT)')
conn.execute('CREATE TABLE task_comments (id INTEGER PRIMARY KEY, task_id TEXT, author TEXT, body TEXT, created_at INTEGER)')
fixture_results = []
for state in ['running', 'done', 'archived']:
    tid = 'fixture_' + state
    conn.execute('INSERT INTO tasks VALUES (?, ?, NULL)', (tid, state))
    cid = ns['add_comment'](conn, tid, 'fixture', 'fixture comment')
    child_state, _ = ns['initial_task_state'](conn, (tid,), 'running', False, None)
    fixture_results.append({'parent_status': state, 'comment_persisted': conn.execute('SELECT body FROM task_comments WHERE id=?',(cid,)).fetchone()['body'] == 'fixture comment',
                            'child_initial_status': child_state})
negative = []
for function in ['_require_task', 'initial_task_state']:
    try:
        if function == '_require_task': ns[function](conn, 'missing_in_this_fixture')
        else: ns[function](conn, ('missing_in_this_fixture',), 'running', False, None)
        negative.append({'function': function, 'raises_for_missing': False})
    except ValueError as ex:
        negative.append({'function': function, 'raises_for_missing': True, 'message': str(ex)})
conn.close()
source_receipt = save('NATIVE-SOURCE-PROBE.json', {'scope': 'AST-extracted exact native helpers; in-memory synthetic DB; NOT production tool/policy behavior',
    'sources': source_bindings, 'status_tests': fixture_results, 'missing_controls': negative,
    'conclusion': 'Native data-layer does not reject comments or parent links because status is done. Missing-id errors describe lookup absence; wrong-board diagnosis requires native readback.'})

summary = {'generated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'subject_head': sha((STD/'SUBJECT.json').read_bytes()), 'inventory_count': len(inventory),
    'inventory': inventory, 'live_receipt': live_receipt, 'source_receipt': source_receipt,
    'json_files': json_results, 'python_ast_errors': ast_errors, 'exact_duplicate_groups': duplicate_groups,
    'duplicate_redundant_bytes': sum((len(g['paths'])-1)*g['bytes_each'] for g in duplicate_groups),
    'archive': archive, 'limits': ['No inference, runtime changes, profile/config edits, deletion, model tests, scheduling or source-content execution.',
        'Filesystem and source fixture proofs do not attest behavioral compliance, live cancellation, enabled-state across all profiles or economics.']}
receipt = save('AUDIT-EVIDENCE.json', summary)
print(json.dumps({'audit': receipt, 'live_targets': len(live), 'live_checks': [sum(sum(c is True for c in t['checks'].values()) for t in live), sum(len(t['checks']) for t in live)],
    'json_files': len(json_results), 'json_defects': [r for r in json_results if not r['parsed'] or r.get('duplicate_keys')],
    'python_ast_errors': ast_errors, 'duplicate_groups': len(duplicate_groups), 'redundant_bytes': summary['duplicate_redundant_bytes'],
    'zip': {k:archive[k] for k in ['zip_members','manifest_payload_count','crc_bad','bad_members','named_check_sources_missing']},
    'documented_rollback_missing_count': sum(len(r['documented_direct_files_missing']) for r in archive['rollback_routes']),
    'alternate_rollback_snapshots_all_exact': all(all(v['byte_exact'] for v in r['alternative_before_snapshots'].values()) for r in archive['rollback_routes']),
    'native_status_probe': fixture_results, 'missing_controls': negative}, ensure_ascii=False, indent=2))
