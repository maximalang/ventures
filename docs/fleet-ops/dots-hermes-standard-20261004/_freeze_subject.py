"""Freeze author serving stamps and exact document subject; no inference."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
SESSION = '20261003_231256_1a496e'
LOGS = Path('C:/Users/max/AppData/Local/hermes/profiles/company/logs')

def h(data):
    return hashlib.sha256(data).hexdigest()

def create(name, obj):
    data = (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    p = ROOT/name
    with p.open('xb') as f:
        f.write(data)
    return {'path': str(p),'sha256': h(data),'bytes':len(data)}

stamps=[]
for p in sorted(LOGS.glob('agent.log*')):
    if p.suffix=='.gz' or not p.is_file():
        continue
    with p.open(encoding='utf-8',errors='replace') as f:
        for lineno,line in enumerate(f,1):
            if SESSION not in line or not any(t in line for t in ('conversation turn:', 'Turn ended:')):
                continue
            model=re.search(r'\bmodel=([^\s,\]\)]+)',line)
            provider=re.search(r'\bprovider=([^\s,\]\)]+)',line)
            if model and provider:
                stamps.append({'log_path':str(p),'line':lineno,'event':'conversation_turn' if 'conversation turn:' in line else 'turn_ended',
                               'session_id':SESSION,'model':model.group(1),'provider':provider.group(1)})
pairs=sorted({(s['model'],s['provider']) for s in stamps})
author=create('AUTHOR-LINEAGE.json',{
    'observed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
    'role':'company brain author; interactive session, not a fabricated worker run',
    'session_id':SESSION,
    'evidence_scope':'Only session-bound main conversation/turn-ended stamps; no message content, auth or config read',
    'stamp_count':len(stamps),
    'model_provider_pairs':[{'model':m,'provider':p} for m,p in pairs],
    'stamps':stamps,
    'independence':'No reviewer yet; compare reviewer actual natural chain with these author pairs, never infer from assignment',
    'unknown_reason':None if stamps else 'No matching public-safe stamps; model identity needs separate supported zero-inference readback',
})
names=['BASELINE.json','COMPANY-BRIEF.md','COMPANY-MATRIX.md','REFERENCE-CANDIDATE.md','HOOK-CANDIDATE.md','AUTHOR-LINEAGE.json']
members=[{'name':name,'bytes':len((ROOT/name).read_bytes()),'sha256':h((ROOT/name).read_bytes())} for name in names]
base=json.loads((ROOT/'BASELINE.json').read_text(encoding='utf-8'))
checks=[]
for record in base['inputs']+base['installed_docs']:
    p=Path(record['path']); data=p.read_bytes()
    if h(data)!=record['sha256'] or len(data)!=record['bytes']:
        raise RuntimeError('Frozen source mismatch: '+str(p))
for record in base['public_hermes_docs']:
    for key in ['raw','text']:
        p=Path(record[key]['path']); data=p.read_bytes()
        if h(data)!=record[key]['sha256'] or len(data)!=record[key]['bytes']:
            raise RuntimeError('Public source snapshot mismatch: '+str(p))
ids=re.findall(r'^\| (M\d{2}) ',(ROOT/'COMPANY-MATRIX.md').read_text(encoding='utf-8'),re.M)
if ids!=['M%02d'%i for i in range(1,18)]:
    raise RuntimeError('Matrix IDs incomplete/duplicated')
for target in base['targets']:
    for current_key, expected_key in [('root_path','before_root_sha256'),('reference_path','before_reference_sha256')]:
        if h(Path(target[current_key]).read_bytes())!=target[expected_key]:
            raise RuntimeError('Target drift before dispatch: '+target['profile'])
subject=create('SUBJECT.json',{
    'scope':'Source comparison + exact reference/hook candidate; no current installation acceptance',
    'created_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
    'members':members,
    'mechanism_ids':ids,
    'targets':[{'profile':t['profile'],'root_path':t['root_path'],'reference_path':t['reference_path'],
                'before_root_sha256':t['before_root_sha256'],'before_reference_sha256':t['before_reference_sha256']} for t in base['targets']],
    'financial_scope':base['financial_scope'],
    'candidate_sha256':h((ROOT/'REFERENCE-CANDIDATE.md').read_bytes()),
    'hook_sha256':h((ROOT/'HOOK-CANDIDATE.md').read_bytes()),
})
print(json.dumps({'subject':subject,'author_lineage':author,'author_model_pairs':[{'model':m,'provider':p} for m,p in pairs],
                  'author_stamp_count':len(stamps),'mechanisms':len(ids),'frozen_targets_current':len(base['targets']),
                  'candidate_sha256':h((ROOT/'REFERENCE-CANDIDATE.md').read_bytes()),
                  'hook_sha256':h((ROOT/'HOOK-CANDIDATE.md').read_bytes())},ensure_ascii=False,indent=2))
