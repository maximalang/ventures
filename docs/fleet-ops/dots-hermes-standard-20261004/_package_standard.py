"""Package permitted workflow snapshots as DATA; no rollout/control changes."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent
HEAD = '2fedef53211adc07445caee7d4d3ef3cac4df5e7544508ca35a26e040774600e'
CORE = [
    'REPORT.md', 'COMPANY-BRIEF.md', 'COMPANY-MATRIX.md', 'SUBJECT.json',
    'BASELINE.json', 'REFERENCE-CANDIDATE.md', 'HOOK-CANDIDATE.md',
    'AUTHOR-LINEAGE.json', 'QA-CANDIDATE-SPEC.md', 'APPLY-SPEC.md',
    'LANE.json', 'DRY-RUN.json', 'PROCEDURE-DELTA.md',
    'PRESERVED-QA-2318.json', '_verify_entrypoints.py',
    '_collect_baseline.py', '_freeze_subject.py', '_preserve_qa2318.py',
    '_package_standard.py',
]
OPTIONAL = [
    'QA-CANDIDATE.md', 'QA-CANDIDATE.json', 'QA-CANDIDATE-FIXED.json',
    'QA-RUN2319-INTEGRITY.json', 'QA2319-CONSUMER-CHECK.json',
    'CONSUMER-DEFECT-ANALYSIS.json', 'QA2319-NATURAL-LINEAGE.json',
    'RECEIPT-CORRECTION-INPUTS.json', 'CONSUMER-ACCEPTANCE-RECEIPT.json',
    'COMPANY-GO.md', 'APPLY.md', 'APPLY.json', 'APPLY-VERIFY.json',
    'APPLY-LOADER.json', 'FINAL-QA.md', 'FINAL-QA.json',
    'QA2321-BATTERY.json', 'QA2321-LOADER.json',
    'FINAL-ACCEPTANCE.md', 'NATIVE-FINAL-READBACK.json',
    'COMPANY-SOURCE-ACCEPTANCE.json', '_company_final_readback.py',
    '_consumer_accept.py', '_record_lineage.py', '_dup_key_probe.py',
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def scoped(path: Path) -> Path:
    p = path.resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError('Not a package-local artifact: ' + str(path))
    if any(x.lower().startswith('.env') or x.lower() in
           {'auth.json', 'secrets', 'credentials', 'dumps', 'kanban.db',
            'config.yaml', 'fleet-policy.db'} for x in p.parts):
        raise ValueError('Forbidden package member')
    if p.suffix.lower() not in {'.md', '.json', '.py', '.txt', '.html'}:
        raise ValueError('Unaccepted artifact extension: ' + str(path))
    return p


def record(path: Path, expected: dict | None = None) -> dict:
    p = scoped(path)
    data = p.read_bytes()
    if expected is not None:
        literal = expected['sha256']
        if not isinstance(literal, str) or not re.fullmatch('[0-9a-f]{64}', literal):
            raise ValueError('Malformed source digest; literal is not repaired')
        if sha(data) != literal or len(data) != expected['bytes']:
            raise ValueError('Frozen bytes changed: ' + str(path))
    return {'name': p.relative_to(ROOT).as_posix(),
            'bytes': len(data), 'sha256': sha(data)}


def hash_records(value):
    if isinstance(value, dict):
        if {'path', 'sha256', 'bytes'}.issubset(value):
            p = Path(value['path'])
            if p.is_absolute() and p.resolve().is_relative_to(ROOT):
                yield value
        for child in value.values():
            yield from hash_records(child)
    elif isinstance(value, list):
        for child in value:
            yield from hash_records(child)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--zip-name', help='Optional NEW artifact filename; no acceptance claim')
    args = ap.parse_args()
    subject_bytes = (ROOT / 'SUBJECT.json').read_bytes()
    if sha(subject_bytes) != HEAD:
        raise ValueError('Exact document subject changed')
    subject = json.loads(subject_bytes)
    members = {name: record(ROOT / name) for name in CORE}
    for frozen in subject['members']:
        item = record(ROOT / frozen['name'], frozen)
        members[item['name']] = item
    baseline = json.loads((ROOT / 'BASELINE.json').read_bytes())
    for frozen in hash_records(baseline):
        item = record(Path(frozen['path']), frozen)
        existing = members.get(item['name'])
        if existing is not None and existing != item:
            raise ValueError('Inconsistent duplicate hash record')
        members[item['name']] = item
    for name in OPTIONAL:
        p = ROOT / name
        if p.is_file():
            members[name] = record(p)
    dry = json.loads((ROOT / 'DRY-RUN.json').read_bytes())
    checks = dry['checks']
    if not checks or not all(value is True for value in checks.values()):
        raise ValueError('Dry-run contains a non-PASS actual check')
    matrix = (ROOT / 'COMPANY-MATRIX.md').read_text(encoding='utf-8')
    ids = re.findall(r'^\| (M\d{2})\b', matrix, re.MULTILINE)
    wanted = ['M' + str(i).zfill(2) for i in range(1, 18)]
    if ids != wanted or subject['mechanism_ids'] != wanted:
        raise ValueError('Mechanism coverage/order/uniqueness mismatch')
    profiles = [t['profile'] for t in baseline['targets']]
    if len(profiles) != 12 or len(set(profiles)) != 12:
        raise ValueError('Exact target uniqueness mismatch')
    result = {
        'artifact': 'PACKAGE-PREFLIGHT',
        'created_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'scope': 'Source/data packaging only; not semantic or installation acceptance',
        'document_head': HEAD,
        'frozen_subject_members_verified': len(subject['members']),
        'mechanism_ids_verified': ids,
        'target_profiles': profiles,
        'baseline_inputs': len(baseline['inputs']),
        'dots_core_inputs': sum(x.get('kind') == 'verified-dots-source' for x in baseline['inputs']),
        'hermes_public_articles': len(baseline['public_hermes_docs']),
        'hermes_installed_source_docs': len(baseline['installed_docs']),
        'dryrun_checks': {'total': len(checks), 'passed': sum(v is True for v in checks.values())},
        'helper_selftest': dry['selftest'],
        'members': [members[name] for name in sorted(members)],
        'member_count': len(members),
        'acceptance_by_packager': None,
        'financial_effect_or_billing_claim': None,
    }
    if args.zip_name:
        name = args.zip_name
        if Path(name).name != name or not name.endswith('.zip'):
            raise ValueError('ZIP must be a leaf artifact filename')
        output = ROOT / name
        if output.exists():
            raise FileExistsError('Do not silently replace an earlier evidence package')
        with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as z:
            for name in sorted(members):
                data = (ROOT / name).read_bytes()
                if sha(data) != members[name]['sha256']:
                    raise ValueError('Concurrent artifact change during packaging: ' + name)
                z.writestr(name, data)
            z.writestr('PACKAGE-MANIFEST.json', json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        with zipfile.ZipFile(output) as z:
            if z.testzip() is not None or len(z.namelist()) != len(members) + 1:
                raise ValueError('ZIP member count/CRC failure')
            for name, expected in members.items():
                data = z.read(name)
                if sha(data) != expected['sha256'] or len(data) != expected['bytes']:
                    raise ValueError('Archive bytes mismatch')
        data = output.read_bytes()
        result['zip'] = {'path': str(output), 'sha256': sha(data),
                         'bytes': len(data), 'members': len(members) + 1,
                         'crc_and_member_hashes_verified': True}
    out = ROOT / 'PACKAGE-PREFLIGHT.json'
    if out.exists():
        previous = json.loads(out.read_bytes())
        if previous.get('artifact') != 'PACKAGE-PREFLIGHT':
            raise ValueError('Refuse to overwrite a non-owned artifact')
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items() if key != 'members'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
