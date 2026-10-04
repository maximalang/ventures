"""Company consumer spot-check: read-only readback of 12 live targets after apply."""
import hashlib
import json
import pathlib

ROOT = pathlib.Path('C:/Users/max/Desktop/all/ventures/docs/fleet-ops/dots-hermes-standard-20261004')
REF = '80933ccf80e99e6b9d62b6f15c5c4f8cf69e9ee79ab1b2e9296173b99cdf4def'
HOOK = '40b6f5e5edad6b8349c3143e032e29d2d02fa5cd1362c9ba9c10dbdbc2bdc88d'
OLD_HOOK = '2e10a1c6153947db1c2f335ea7037fa0522111f5be6ec31d83ebb345b9768ec9'

baseline = json.loads((ROOT / 'BASELINE.json').read_text(encoding='utf-8'))
targets = baseline.get('targets')
if isinstance(targets, dict):
    paths = list(targets)
elif isinstance(targets, list):
    paths = [t if isinstance(t, str) else t.get('path') or t.get('live_path') for t in targets]
else:
    raise RuntimeError('unrecognized BASELINE targets shape')
paths = [p for p in paths if p]

results = []
ok = True
for p in paths:
    d = pathlib.Path(p)
    ref = d / 'references' / 'dots-operating-method.md'
    hook = d / 'references' / 'dots-operating-method-load.md'
    old = d / 'references' / 'dots-load-hook.md'
    r_ok = ref.is_file() and hashlib.sha256(ref.read_bytes()).hexdigest() == REF
    h_ok = hook.is_file() and hashlib.sha256(hook.read_bytes()).hexdigest() == HOOK
    o_absent = not old.exists() or hashlib.sha256(old.read_bytes()).hexdigest() != OLD_HOOK
    # any stale old-hook bytes anywhere in references?
    stale = []
    if (d / 'references').is_dir():
        for f in (d / 'references').iterdir():
            if f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest() == OLD_HOOK:
                stale.append(f.name)
    row_ok = r_ok and h_ok and o_absent and not stale
    ok = ok and row_ok
    results.append({'path': p, 'ref_exact': r_ok, 'new_hook_exact': h_ok,
                    'no_old_hook_bytes': not stale, 'row_ok': row_ok})

print(json.dumps({'targets_checked': len(results), 'all_ok': ok, 'results': results}, ensure_ascii=False, indent=1))
out = ROOT / 'COMPANY-POST-APPLY-READBACK.json'
out.write_text(json.dumps({'scope': 'Company read-only consumer readback of live targets after apply+QA',
                           'targets_checked': len(results), 'all_ok': ok, 'results': results},
                          ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('written:', out, hashlib.sha256(out.read_bytes()).hexdigest())
