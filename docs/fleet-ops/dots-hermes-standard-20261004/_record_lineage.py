"""Record observed serving stamps for completed run2319 review; no inference, no billing claim."""
import datetime as dt
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path('C:/Users/max/Desktop/all/ventures/docs/fleet-ops/dots-hermes-standard-20261004')
SID = '20261004_030640_cd335f'
LOG = pathlib.Path('C:/Users/max/AppData/Local/hermes/profiles/qa/logs/agent.log')
HEAD = '2fedef53211adc07445caee7d4d3ef3cac4df5e7544508ca35a26e040774600e'

stamps = []
for line in LOG.read_text(encoding='utf-8', errors='replace').splitlines():
    if SID in line and 'API call #' in line:
        m = re.search(r'API call #(\d+): model=(\S+) provider=(\S+)', line)
        if m:
            stamps.append({'call': int(m.group(1)), 'model': m.group(2), 'provider': m.group(3)})
if not stamps:
    raise RuntimeError('No observed API stamps for the named review session')

receipt = {
    'scope': ('Observed API-call stamps of the completed source-QA session only; '
              'no auxiliary/hidden-chain or billing claim; absence elsewhere is unknown, not zero'),
    'at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'native_task': 't_d090b4ff',
    'native_run': 2319,
    'reviewer_session': SID,
    'observed_main_api_calls': len(stamps),
    'observed_provider_models': [
        {'provider': p, 'model': m} for p, m in sorted({(s['provider'], s['model']) for s in stamps})
    ],
    'source_log': str(LOG),
}
out = ROOT / 'QA2319-NATURAL-LINEAGE.json'
out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

members = []
for name in ['QA-CANDIDATE.md', 'QA-CANDIDATE.json', 'QA-RUN2319-INTEGRITY.json',
             'QA2319-CONSUMER-CHECK.json', 'QA2319-NATURAL-LINEAGE.json', 'BOARD-STATE-NOW.json']:
    data = (ROOT / name).read_bytes()
    members.append({'name': name, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
manifest = {
    'document_head': HEAD,
    'purpose': ('Frozen inputs for receipt correction only; original review artifacts preserved; '
                'not a positive gate and not rewritten reviewer content'),
    'members': members,
}
mpath = ROOT / 'RECEIPT-CORRECTION-INPUTS.json'
mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({
    'lineage_receipt': str(out),
    'observed_main_api_calls': len(stamps),
    'provider_models': receipt['observed_provider_models'],
    'inputs_manifest': str(mpath),
    'inputs_manifest_sha256': hashlib.sha256(mpath.read_bytes()).hexdigest(),
    'original_member_hashes': members,
}, ensure_ascii=False, indent=2))
