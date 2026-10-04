"""Locate duplicate JSON keys and their surrounding context inside QA-CANDIDATE.json."""
import json
import pathlib
import re

P = pathlib.Path('C:/Users/max/Desktop/all/ventures/docs/fleet-ops/dots-hermes-standard-20261004/QA-CANDIDATE.json')
text = P.read_text(encoding='utf-8')
KEYS = ['checks_this_run', 'm01_m17', 'scenarios_s01_s17', 'reviewer_lineage_run_2319']
report = {}
for key in KEYS:
    spans = [m.start() for m in re.finditer('"' + key + r'"\s*:', text)]
    occurrences = []
    for pos in spans:
        chunk = text[pos:pos + 700]
        occurrences.append(chunk[:650])
    report[key] = {'occurrences': len(spans), 'contexts': occurrences}
print(json.dumps(report, ensure_ascii=False, indent=1)[:6000])
