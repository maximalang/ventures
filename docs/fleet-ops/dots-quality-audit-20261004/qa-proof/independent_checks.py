"""Independent bounded re-execution audit (t_7638de4f, profile qa).

Re-executes (not trusts) the checks from the prior coordinator harness
audit_current.py against frozen inputs; reads only allowlisted paths:
- 6 AUDIT-SUBJECT members (hash check done separately, MATCH 6/6)
- BASELINE.json targets' 24 live root/reference paths + snapshots
- the standard ZIP (CRC + member payload checks)
- two native helper sources in a sqlite :memory: fixture (no real board)
Writes nothing outside its own stdout; final deliverables are written by the
agent via sanctioned tools.
"""
from __future__ import annotations
import ast, collections, contextlib, hashlib, json, sqlite3, sys, time
from pathlib import Path
from typing import Optional
import zipfile

STD = Path('C:/Users/max/Desktop/all/ventures/docs/fleet-ops/dots-hermes-standard-20261004')
SRC = Path('C:/Users/max/AppData/Local/hermes/hermes-agent')

def sha(b): return hashlib.sha256(b).hexdigest()

out = {}

# ---- 1. Subject anchor + 6 member hashes (re-check inside same run) ----
subj = json.loads((STD.parent / 'dots-quality-audit-20261004' / 'AUDIT-SUBJECT.json').read_bytes())
members_ok = []
for m in subj['members']:
    data = Path(m['path']).read_bytes()
    members_ok.append({'name': Path(m['path']).name,
                       'sha_match': sha(data) == m['sha256'],
                       'bytes_match': len(data) == m['bytes']})
out['subject_head'] = subj['source_subject_head']
out['member_checks'] = members_ok
out['members_all_ok'] = all(m['sha_match'] and m['bytes_match'] for m in members_ok)

# ---- 2. Live checks: 12 targets x 24 allowed live paths ----
baseline = json.loads((STD / 'BASELINE.json').read_bytes())
apply = json.loads((STD / 'APPLY.json').read_bytes())
apply_by_profile = {t['profile']: t for t in apply['per_target']}
reference = (STD / 'REFERENCE-CANDIDATE.md').read_bytes()
hook = (STD / 'HOOK-CANDIDATE.md').read_bytes()
old_hook = Path('C:/Users/max/Desktop/all/ventures/docs/fleet-ops/dots-20261003/LOAD-HOOK.md').read_bytes()

live = []
for t in baseline['targets']:
    root_p, ref_p = Path(t['root_path']), Path(t['reference_path'])
    root, ref = root_p.read_bytes(), ref_p.read_bytes()
    exp = apply_by_profile[t['profile']]
    before_root = Path(t['snapshots']['root']['path']).read_bytes()
    before_ref = Path(t['snapshots']['reference']['path']).read_bytes()
    backup_dir = STD / 'apply-backups' / t['profile']
    checks = {
        'reference_exact': ref == reference,
        'hook_once': root.count(hook) == 1,
        'old_hook_absent': root.count(old_hook) == 0,
        'root_matches_after': sha(root) == exp['after_root_sha256'],
        'root_preservation': root.removesuffix(hook) == before_root.removesuffix(old_hook),
        'before_root_binding': sha(before_root) == t['before_root_sha256'],
        'before_reference_binding': sha(before_ref) == t['before_reference_sha256'],
        'backup_root_exact': (backup_dir / 'SKILL.md').read_bytes() == before_root,
        'backup_reference_exact': (backup_dir / 'dots-operating-method.md').read_bytes() == before_ref,
        'expected_in_apply': sha(root) == exp['intended_root_sha256'],
    }
    live.append({'profile': t['profile'], 'ok': all(checks.values()),
                 'failed': [k for k, v in checks.items() if not v]})
out['live_targets'] = len(live)
out['live_ok'] = sum(1 for t in live if t['ok'])
out['live_failures'] = [t for t in live if not t['ok']]
out['live_checks_total'] = len(live) * 10

# ---- 3. Directory inventory + JSON dup-keys + duplicate groups ----
inv, json_res, ast_err = [], [], []
groups = collections.defaultdict(list)
for p in sorted(STD.rglob('*')):
    if not p.is_file() or '__pycache__' in p.parts:
        continue
    data = p.read_bytes()
    rec = {'path': p.relative_to(STD).as_posix(), 'bytes': len(data), 'sha256': sha(data)}
    inv.append(rec); groups[rec['sha256']].append(rec)
    if p.suffix.lower() == '.json':
        dupes = []
        def pairs(items, dupes=dupes):
            seen = set()
            for k, v in items:
                if k in seen: dupes.append(k)
                seen.add(k)
            return dict(items)
        try:
            json.loads(data, object_pairs_hook=pairs)
            json_res.append({'path': rec['path'], 'parsed': True, 'dup': dupes})
        except Exception as ex:
            json_res.append({'path': rec['path'], 'parsed': False, 'err': str(ex)})
    if p.suffix.lower() == '.py':
        try: ast.parse(data.decode('utf-8-sig'))
        except Exception as ex: ast_err.append({'path': rec['path'], 'err': str(ex)})

out['inventory_count'] = len(inv)
out['json_files'] = len(json_res)
out['json_defects'] = [r for r in json_res if not r['parsed'] or r.get('dup')]
out['python_ast_errors'] = ast_err
dup_groups = [{'sha256': h, 'n': len(m), 'bytes': m[0]['bytes']}
              for h, m in groups.items() if len(m) > 1]
out['dup_groups'] = len(dup_groups)
out['dup_redundant_bytes'] = sum((g['n'] - 1) * g['bytes'] for g in dup_groups)
out['dup_group_details'] = sorted(dup_groups, key=lambda g: -g['n'])

# ---- 4. ZIP: CRC, manifest payload closure, named sources, rollback routes ----
zpath = STD / 'dots-hermes-standard-20261004.zip'
with zipfile.ZipFile(zpath) as z:
    manifest = json.loads(z.read('PACKAGE-MANIFEST.json'))
    names = set(z.namelist())
    bad = [e['name'] for e in manifest['members']
           if e['name'] not in names or sha(z.read(e['name'])) != e['sha256']
           or len(z.read(e['name'])) != e['bytes']]
    required = ['qa2321_battery.py', 'qa2321_loader.py', 'QA-CHECKER-RUN2319.py',
                'APPLY-run2320-20261004T012335Z.json',
                'preserved-qa2318/qa_dryrun_12targets.py',
                'preserved-qa2318/qa_dryrun_stage1.json']
    rollback = []
    for t in baseline['targets']:
        prof = t['profile']
        miss = [f'apply-backups/{prof}/{n}' for n in ['SKILL.md', 'dots-operating-method.md']
                if f'apply-backups/{prof}/{n}' not in names]
        alts = {}
        for field in ['root', 'reference']:
            bp = Path(t['snapshots'][field]['path'])
            rel = bp.relative_to(STD).as_posix()
            alts[field] = {'path': rel, 'in_zip': rel in names,
                           'byte_exact': rel in names and z.read(rel) == bp.read_bytes()}
        rollback.append({'profile': prof, 'missing_direct': miss, 'alts': alts})
    ziprec = {
        'zip_sha256': sha(zpath.read_bytes()), 'zip_bytes': zpath.stat().st_size,
        'members_total': len(z.namelist()),
        'manifest_payload_count': manifest['member_count'],
        'manifest_entries': len(manifest['members']),
        'manifest_self_excluded': 'PACKAGE-MANIFEST.json' not in {m['name'] for m in manifest['members']},
        'crc_bad': z.testzip(), 'bad_members': bad,
        'named_sources_missing': [n for n in required if n not in names],
        'rollback_direct_missing_total': sum(len(r['missing_direct']) for r in rollback),
        'rollback_alt_all_exact': all(all(v['byte_exact'] for v in r['alts'].values()) for r in rollback),
    }
    # extra: 157 vs 158 arithmetic
    ziprec['arithmetic_note'] = (ziprec['members_total'] == ziprec['manifest_payload_count'] + 1
                                 and ziprec['manifest_payload_count'] == len(manifest['members']))
out['zip'] = ziprec
not_archived = [e['path'] for e in inv if e['path'] != zpath.name and e['path'] not in names]
out['local_files_not_archived_count'] = len(not_archived)
out['local_files_not_archived'] = not_archived

# ---- 5. Native helpers in :memory: fixture (AST-extracted; no real board) ----
src_map = {'kanban_db.py': ['_require_task', 'add_comment'],
           'kanban_db_graph.py': ['initial_task_state']}
bindings, fns = [], []
for fn, wanted in src_map.items():
    data = (SRC / 'hermes_cli' / fn).read_text(encoding='utf-8')
    tree = ast.parse(data)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in wanted:
            bindings.append({'file': fn, 'file_sha256': sha((SRC / 'hermes_cli' / fn).read_bytes()),
                             'function': node.name, 'lines': [node.lineno, node.end_lineno]})
            fns.append(node)
ns = {'sqlite3': sqlite3, 'time': time, 'Optional': Optional,
      'write_txn': lambda conn, **kw: contextlib.nullcontext(conn),
      '_append_event': lambda *a, **k: None}
mod = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)] + fns,
                 type_ignores=[])
exec(compile(ast.fix_missing_locations(mod), '<fixture>', 'exec'), ns)
conn = sqlite3.connect(':memory:')
conn.row_factory = sqlite3.Row
conn.execute('CREATE TABLE tasks (id TEXT PRIMARY KEY, status TEXT, tenant TEXT)')
conn.execute('CREATE TABLE task_comments (id INTEGER PRIMARY KEY, task_id TEXT, author TEXT, body TEXT, created_at INTEGER)')
fx = []
for state in ['running', 'done', 'archived']:
    tid = 'fx_' + state
    conn.execute('INSERT INTO tasks VALUES (?, ?, NULL)', (tid, state))
    cid = ns['add_comment'](conn, tid, 'fx', 'fx comment')
    child, _ = ns['initial_task_state'](conn, (tid,), 'running', False, None)
    fx.append({'parent': state,
               'comment_ok': conn.execute('SELECT body FROM task_comments WHERE id=?', (cid,)).fetchone()['body'] == 'fx comment',
               'child_state': child})
neg = []
for fname in ['_require_task', 'initial_task_state']:
    try:
        if fname == '_require_task':
            ns[fname](conn, 'missing_fx')
        else:
            ns[fname](conn, ('missing_fx',), 'running', False, None)
        neg.append({'function': fname, 'raises': False})
    except ValueError as ex:
        neg.append({'function': fname, 'raises': True, 'msg': str(ex)})
conn.close()
out['native_helpers'] = bindings
out['native_fixture'] = fx
out['native_missing_controls'] = neg

print(json.dumps(out, ensure_ascii=False, indent=1))
