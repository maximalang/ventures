"""Preserve genuine partial QA output and main serving stamps only.
No inference, live profile writes, raw control stores or original-query replay.
"""
from pathlib import Path
import datetime as dt
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parent
SOURCES=[Path('C:/Users/max/AppData/Local/hermes/profiles/qa/cache/scratch/qa_dryrun_12targets.py'),Path('C:/Users/max/AppData/Local/Temp/qa_dryrun_stage1.json')]
OUT=ROOT/'preserved-qa2318'
OUT.mkdir(exist_ok=True)
members=[]
for source in SOURCES:
    data=source.read_bytes()
    target=OUT/source.name
    with target.open('xb') as f:f.write(data)
    members.append({'source':str(source),'preserved':str(target),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
stage=json.loads(SOURCES[1].read_text(encoding='utf-8'))
assert len(stage['results'])==12 and len({r['profile'] for r in stage['results']})==12
assert stage['failures']==[]
assert all(r['old_hook_suffix'] and r['old_hook_count']==1 and r['live_root_same'] and r['live_ref_same'] and r['before_ref_frozen_ok'] for r in stage['results'])
assert stage['ref_sha']==hashlib.sha256((ROOT/'REFERENCE-CANDIDATE.md').read_bytes()).hexdigest()
assert stage['hook_sha']==hashlib.sha256((ROOT/'HOOK-CANDIDATE.md').read_bytes()).hexdigest()
SID='20261004_022802_f5a61c'
log=Path('C:/Users/max/AppData/Local/hermes/profiles/qa/logs/agent.log')
api=[]
turns=[]
fall=[]
for number,line in enumerate(log.read_text(encoding='utf-8',errors='replace').splitlines(),1):
    if '['+SID+']' not in line:continue
    if 'agent.turn_context: conversation turn:' in line and 'work kanban task t_d090b4ff' in line:
        match=re.search(r'model=(\S+) provider=(\S+)',line)
        if match:turns.append({'line':number,'model':match[1],'provider':match[2],'task':'t_d090b4ff','session':SID})
    if 'agent.conversation_loop: API call #' in line:
        match=re.search(r'API call #(\d+): model=(\S+) provider=(\S+)',line)
        if match:api.append({'line':number,'call':int(match[1]),'model':match[2],'provider':match[3],'session':SID})
    if 'Fallback skip:' in line or 'Fallback activated:' in line:fall.append({'line':number,'observed':True})
assert turns and api
assert [r['call'] for r in api]==list(range(1,len(api)+1))
author=json.loads((ROOT/'AUTHOR-LINEAGE.json').read_text(encoding='utf-8'))
pairs=sorted({(x['model'],x['provider']) for x in api})
author_pairs={(x['model'],x['provider']) for x in author['model_provider_pairs']}
summary={'created_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'native_task':'t_d090b4ff','run_id':2318,'session_id':SID,
         'typed_native_attempt_verdict':'WITHHELD','main_stamp_source':str(log),'turn_task_join':turns,
         'api_stamps':api,'main_api_call_count':len(api),'actual_main_pairs':pairs,'observed_main_fallback_events':fall,
         'author_main_pairs':sorted(author_pairs),'main_pair_overlap':bool(set(pairs)&author_pairs),
         'limits':['Main stamp comparison only; not full auxiliary-chain attestation or final semantic QA','Original optional batch content search was denied; not replayed here','Stage checker enumerates historical other files, not a live preservation acceptance','No formal M01-M17/scenario artifacts or positive gate exist'],
         'stage_profiles_count':len(stage['results']),'stage_failed_profiles':stage['failures'],'stage_expected_distinct_after_roots':len({r['cand_root_sha'] for r in stage['results']}),
         'preserved_files':members,'financial_scope':{'scope':'fleet-ops method normalization partial QA','period_end_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source':'native run2318, genuine stage file, natural main stamps; ledger not read','confirmed_revenue':None,'refunds':None,'incremental_paid_costs':None,'new_commitments':None,'estimated_usage_cost':None,'unknown_reason':'not measured; serving stamps are not billing records'}}
data=(json.dumps(summary,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
target=ROOT/'PRESERVED-QA-2318.json'
with target.open('xb') as f:f.write(data)
print(json.dumps({'receipt':str(target),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'stage_profiles':len(stage['results']),'stage_failures':stage['failures'],'observed_main_api_calls':len(api),'observed_main_pairs':pairs,'main_pair_overlap':summary['main_pair_overlap'],'semantic_qa':'WITHHELD'},ensure_ascii=False))
