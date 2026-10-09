# Independent QA dry-run of hook/reference replacement for all 12 targets (read-only).
# Writes only into TMPDIR. Reads: SUBJECT.json targets, before/, before-trees/, HOOK-CANDIDATE.md, REFERENCE-CANDIDATE.md, old-hook.md.
import json, hashlib, os, sys

ROOT = r'C:/Users/max/Desktop/all/ventures/docs/fleet-ops/dots-hermes-standard-20261004'
subj = json.load(open(ROOT + '/SUBJECT.json', encoding='utf-8'))

old_hook = open(ROOT + '/local/old-hook.md', 'rb').read()
new_hook = open(ROOT + '/HOOK-CANDIDATE.md', 'rb').read()
new_ref = open(ROOT + '/REFERENCE-CANDIDATE.md', 'rb').read()

ref_sha = hashlib.sha256(new_ref).hexdigest()
hook_sha = hashlib.sha256(new_hook).hexdigest()
old_hook_sha = hashlib.sha256(old_hook).hexdigest()

EXPECT_REF = '80933ccf80e99e6b9d62b6f15c5c4f8cf69e9ee79ab1b2e9296173b99cdf4def'
EXPECT_HOOK = '40b6f5e5edad6b8349c3143e032e29d2d02fa5cd1362c9ba9c10dbdbc2bdc88d'

print('candidate ref sha  =', ref_sha, 'match=', ref_sha == EXPECT_REF)
print('candidate hook sha =', hook_sha, 'match=', hook_sha == EXPECT_HOOK)
print('old hook sha       =', old_hook_sha)
print()

results = []
failures = []

for t in subj['targets']:
    prof = t['profile']
    rec = {'profile': prof}
    before_root = open(ROOT + '/before/%s/SKILL.md' % prof, 'rb').read()
    # 1) old hook is a suffix of the current root
    suffix_ok = before_root.endswith(old_hook)
    hook_count = before_root.count(old_hook)
    rec['old_hook_suffix'] = suffix_ok
    rec['old_hook_count'] = hook_count
    # also check hook occurs with the preceding blank line boundary intact
    base_part = before_root[:-len(old_hook)] if suffix_ok else None
    rec['base_len'] = len(base_part) if base_part is not None else None
    # 2) candidate root = base + new hook (exactly one new hook, nothing else changed)
    cand_root = base_part + new_hook if suffix_ok else None
    rec['cand_root_len'] = len(cand_root) if cand_root is not None else None
    rec['cand_root_sha'] = hashlib.sha256(cand_root).hexdigest() if cand_root else None
    # 3) live files unchanged since freeze
    live_root = open(t['root_path'], 'rb').read()
    live_ref = open(t['reference_path'], 'rb').read()
    rec['live_root_same'] = hashlib.sha256(live_root).hexdigest() == t['before_root_sha256']
    rec['live_ref_same'] = hashlib.sha256(live_ref).hexdigest() == t['before_reference_sha256']
    # old reference frozen copy matches SUBJECT
    old_ref = open(ROOT + '/before/%s/dots-operating-method.md' % prof, 'rb').read()
    rec['before_ref_frozen_ok'] = hashlib.sha256(old_ref).hexdigest() == t['before_reference_sha256']
    # 4) captured tree: other files (besides SKILL.md and the reference) — enumeration only
    tree_dir = ROOT + '/before-trees/' + prof
    tree_files = []
    for r, ds, fs in os.walk(tree_dir):
        for f in fs:
            p = os.path.join(r, f)
            rel = os.path.relpath(p, tree_dir).replace(os.sep, '/')
            tree_files.append([rel, hashlib.sha256(open(p, 'rb').read()).hexdigest(), os.path.getsize(p)])
    rec['tree_file_count'] = len(tree_files)
    rec['tree_files'] = tree_files
    others = [x for x in tree_files if x[0] not in ('SKILL.md', 'references/dots-operating-method.md')]
    rec['other_files_count'] = len(others)
    if others:
        rec['other_files'] = others
    results.append(rec)
    flag = suffix_ok and hook_count == 1 and rec['live_root_same'] and rec['live_ref_same'] and rec['before_ref_frozen_ok']
    if not flag:
        failures.append(prof)
    print('%-14s suffix=%s hook_count=%d base=%sB cand_root=%sB live_root_same=%s live_ref_same=%s before_ref_ok=%s tree_files=%d others=%d' % (
        prof, suffix_ok, hook_count, rec['base_len'], rec['cand_root_len'],
        rec['live_root_same'], rec['live_ref_same'], rec['before_ref_frozen_ok'],
        rec['tree_file_count'], rec['other_files_count']))

# distinct base parts across profiles (roots may legitimately differ)
bases = set(r['base_len'] for r in results if r['base_len'] is not None)
cand_roots = {}
for r in results:
    if r['cand_root_sha']:
        cand_roots.setdefault(r['cand_root_sha'], []).append(r['profile'])
print()
print('distinct base lengths:', sorted(bases))
print('distinct candidate root hashes:', len(cand_roots))
for h, ps in cand_roots.items():
    print('  %s -> %d profiles' % (h[:16], len(ps)))

out = os.path.join(os.environ.get('TMPDIR', ROOT), 'qa_dryrun_stage1.json')
json.dump({'results': results, 'failures': failures,
           'ref_sha': ref_sha, 'hook_sha': hook_sha, 'old_hook_sha': old_hook_sha},
          open(out, 'w'), ensure_ascii=False, indent=1)
print()
print('saved', out)
print('FAILURES:', failures if failures else 'none')
sys.exit(0 if not failures else 1)
