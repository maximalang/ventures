"""Company consumer readback: read-only verification of 12 live targets after apply.

Checks per target (actual bytes, no inference):
- references/dots-operating-method.md exists and equals REF sha256;
- the new hook text (HOOK-CANDIDATE.md body) is embedded in SKILL.md;
- no file in the skill tree carries the OLD hook sha256 bytes.
"""
import hashlib
import json
import pathlib

ROOT = pathlib.Path('C:/Users/max/Desktop/all/ventures/docs/fleet-ops/dots-hermes-standard-20261004')
REF = '80933ccf80e99e6b9d62b6f15c5c4f8cf69e9ee79ab1b2e9296173b99cdf4def'
OLD_HOOK = '2e10a1c6153947db1c2f335ea7037fa0522111f5be6ec31d83ebb345b9768ec9'

hook_text = (ROOT / 'HOOK-CANDIDATE.md').read_text(encoding='utf-8').strip()
probe = hook_text[:200]
baseline = json.loads((ROOT / 'BASELINE.json').read_text(encoding='utf-8'))
targets = baseline['targets']

results = []
ok = True
for t in targets:
    skill_md = pathlib.Path(t['root_path'])
    d = skill_md.parent
    ref = d / 'references' / 'dots-operating-method.md'
    ref_ok = ref.is_file() and hashlib.sha256(ref.read_bytes()).hexdigest() == REF
    embed_ok = probe in skill_md.read_text(encoding='utf-8', errors='replace')
    stale = [str(f.relative_to(d)) for f in d.rglob('*')
             if f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest() == OLD_HOOK]
    row_ok = ref_ok and embed_ok and not stale
    ok = ok and row_ok
    results.append({'profile': t['profile'], 'root_path': str(skill_md),
                    'reference_exact': ref_ok, 'hook_embedded': embed_ok,
                    'no_old_hook_bytes': not stale, 'row_ok': row_ok})

receipt = {
    'scope': ('Company independent read-only consumer readback of live targets after apply and QA; '
              'actual bytes, no inference; not a rewrite of reviewer artifacts'),
    'head': '2fedef53211adc07445caee7d4d3ef3cac4df5e7544508ca35a26e040774600e',
    'targets_checked': len(results),
    'all_ok': ok,
    'results': results,
}
out = ROOT / 'NATIVE-FINAL-READBACK.json'
out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'targets_checked': len(results), 'all_ok': ok,
                  'sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
                  'path': str(out)}, ensure_ascii=False, indent=1))
