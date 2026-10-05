"""Company consumer acceptance of the corrected machine receipt (read-only)."""
import datetime as dt
import hashlib
import json
import pathlib

ROOT = pathlib.Path('C:/Users/max/Desktop/all/ventures/docs/fleet-ops/dots-hermes-standard-20261004')
HEAD = '2fedef53211adc07445caee7d4d3ef3cac4df5e7544508ca35a26e040774600e'
P = ROOT / 'QA-CANDIDATE-FIXED.json'
raw = P.read_text(encoding='utf-8')
data = json.loads(raw)

# strict per-object duplicate-key scan
bad = []


def hook(pairs):
    seen = {}
    for k, _v in pairs:
        seen[k] = seen.get(k, 0) + 1
    bad.extend(k for k, c in seen.items() if c > 1)
    return dict(pairs)


json.loads(raw, object_pairs_hook=hook)

checks = []


def add(name, ok, detail):
    checks.append({'check': name, 'ok': bool(ok), 'detail': detail})


add('no_per_object_duplicate_keys', not bad, f'scan result: {bad or "none"}')
add('typed_verdict_word_PASS', data.get('typed_verdict_word') == 'PASS', repr(data.get('typed_verdict_word')))
m = data['m01_m17']
s = data['scenarios_s01_s17']
lin = data['reviewer_lineage_run_2319']
add('m01_m17_17_confirmed', '17/17' in m.get('result', '') and len(m.get('routing', {})) == 17,
    f"{m.get('result')} | routing entries={len(m.get('routing', {}))}")
add('s01_s17_17_consistent', '17/17' in s.get('result', ''), s.get('result'))
add('lineage_non_overlapping', lin.get('main_pair_overlap') is False,
    json.dumps({k: lin[k] for k in ('session_id', 'main_api_stamps', 'author_chain')}, ensure_ascii=False))
add('head_binding_embedded', HEAD in raw, 'exact frozen subject head present')
add('integrity_receipt_19_of_19', data['checks_this_run'].get('integrity_result', '').startswith('19/19'),
    data['checks_this_run'].get('integrity_result'))
mine = json.loads((ROOT / 'QA2319-NATURAL-LINEAGE.json').read_text(encoding='utf-8'))
add('stamps_corroborated_by_company_readback',
    mine['observed_main_api_calls'] >= 42 and mine['observed_provider_models'] == [{'provider': 'zai', 'model': 'glm-5.3'}],
    f"company independently observed {mine['observed_main_api_calls']} main calls {mine['observed_provider_models']}")

ok = all(c['ok'] for c in checks)
receipt = {
    'scope': ('Company consumer acceptance of the corrected machine receipt; read-only; '
              'not a rewrite of reviewer artifacts'),
    'at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'artifact': 'QA-CANDIDATE-FIXED.json',
    'artifact_sha256': hashlib.sha256(P.read_bytes()).hexdigest(),
    'artifact_bytes': P.stat().st_size,
    'checks': checks,
    'all_ok': ok,
    'note': ('Review-run lineage fields retained verbatim (42/42 lower bound at artifact time); '
             'company later observed 60 calls of the same pair, consistent, not contradictory.'),
}
out = ROOT / 'CONSUMER-ACCEPTANCE-RECEIPT.json'
out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({
    'all_ok': ok,
    'checks': [(c['check'], c['ok']) for c in checks],
    'receipt': str(out),
    'receipt_sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
}, ensure_ascii=False, indent=1))
