"""Offline/readonly verifier for the exact Dots/Hermes entrypoint diff.
Not a semantic verdict, registration attestation, gate or live-behavior test.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import unittest
import yaml

ROOT=Path(__file__).resolve().parent
HEAD='2fedef53211adc07445caee7d4d3ef3cac4df5e7544508ca35a26e040774600e'
BASELINE='5490e880fcd4d596029d127e1a1bf4011df7003b53e9faca3fef9680fa61f817'

def h(data):
    return hashlib.sha256(data).hexdigest()

def replace_suffix(root,old,new):
    if not old or not new or root.count(old)!=1 or not root.endswith(old):
        raise ValueError('Old hook is not one exact suffix')
    if new in root[:-len(old)]:
        raise ValueError('New hook would duplicate preexisting bytes')
    return root[:-len(old)]+new

def frontmatter(data):
    text=data.decode('utf-8-sig')
    match=re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)',text,re.S)
    if not match:
        raise ValueError('No valid skill frontmatter delimiters')
    value=yaml.safe_load(match.group(1))
    if not isinstance(value,dict) or value.get('name')!='company-os':
        raise ValueError('Unexpected skill name/frontmatter')
    return value

class VerifierUnitTests(unittest.TestCase):
    def test_preserves_prefix(self):
        self.assertEqual(replace_suffix(b'prefix OLD',b'OLD',b'NEW'),b'prefix NEW')
    def test_preserves_crlf(self):
        prefix=b'---\r\nname: company-os\r\n---\r\ncontent\r\n'
        self.assertEqual(replace_suffix(prefix+b'OLD',b'OLD',b'NEW')[:-3],prefix)
    def test_rejects_duplicate_old(self):
        with self.assertRaises(ValueError): replace_suffix(b'OLD prefix OLD',b'OLD',b'NEW')
    def test_rejects_not_suffix(self):
        with self.assertRaises(ValueError): replace_suffix(b'prefix OLD extra',b'OLD',b'NEW')
    def test_rejects_new_duplicate(self):
        with self.assertRaises(ValueError): replace_suffix(b'NEW prefix OLD',b'OLD',b'NEW')
    def test_yaml_identity(self):
        self.assertEqual(frontmatter(b'---\nname: company-os\ndescription: example\n---\nbody')['name'],'company-os')
        with self.assertRaises(ValueError): frontmatter(b'---\nname: other\n---\n')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--phase',choices=['before','dry-run','after'],required=True)
    parser.add_argument('--out')
    parser.add_argument('--selftest',action='store_true')
    args=parser.parse_args()
    tests=None
    if args.selftest:
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(VerifierUnitTests))
        tests={'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'pass':result.wasSuccessful()}
        if not result.wasSuccessful(): raise SystemExit(2)
    if h((ROOT/'SUBJECT.json').read_bytes())!=HEAD or h((ROOT/'BASELINE.json').read_bytes())!=BASELINE:
        raise RuntimeError('Frozen subject/baseline mismatch')
    subject=json.loads((ROOT/'SUBJECT.json').read_text(encoding='utf-8'))
    for record in subject['members']:
        data=(ROOT/record['name']).read_bytes()
        if h(data)!=record['sha256'] or len(data)!=record['bytes']:
            raise RuntimeError('Member drift: '+record['name'])
    base=json.loads((ROOT/'BASELINE.json').read_text(encoding='utf-8'))
    old=(ROOT/'local/old-hook.md').read_bytes()
    new=(ROOT/'HOOK-CANDIDATE.md').read_bytes()
    ref=(ROOT/'REFERENCE-CANDIDATE.md').read_bytes()
    entries=[]
    all_checks={'unique_12_profiles':len(base['targets'])==12 and len({t['profile'] for t in base['targets']})==12,
                'unique_24_target_paths':len({t[k] for t in base['targets'] for k in ['root_path','reference_path']})==24}
    for target in base['targets']:
        prior=Path(target['snapshots']['root']['path']).read_bytes()
        prior_ref=Path(target['snapshots']['reference']['path']).read_bytes()
        expected=replace_suffix(prior,old,new)
        live_root=Path(target['root_path']).read_bytes()
        live_ref=Path(target['reference_path']).read_bytes()
        observed_root=live_root if args.phase!='dry-run' else expected
        observed_ref=live_ref if args.phase!='dry-run' else ref
        checks={
            'before_backup_root_hash':h(prior)==target['before_root_sha256'],
            'before_backup_reference_hash':h(prior_ref)==target['before_reference_sha256'],
            'root_matches_expected':observed_root==(expected if args.phase in ['after','dry-run'] else prior),
            'reference_matches_expected':observed_ref==(ref if args.phase in ['after','dry-run'] else prior_ref),
            'own_prefix_preserved':(observed_root[:-len(new)] if args.phase in ['after','dry-run'] else observed_root[:-len(old)])==prior[:-len(old)],
            'exact_single_hook':observed_root.count(new if args.phase in ['after','dry-run'] else old)==1,
            'valid_same_yaml':frontmatter(observed_root)==frontmatter(prior),
            'new_entrypoint_link_exact':re.findall(rb'\]\((references/dots-operating-method\.md)\)',new)==[b'references/dots-operating-method.md'],
            'live_preimage_unchanged_for_dry_run':args.phase!='dry-run' or (live_root==prior and live_ref==prior_ref),
        }
        before_rel={r['relative_path'] for r in target['markdown_tree']}
        actual_rel={p.relative_to(Path(target['root_path']).parent).as_posix() for p in Path(target['root_path']).parent.rglob('*.md')}
        checks['same_markdown_path_set']=before_rel==actual_rel
        unchanged=[]
        for record in target['markdown_tree']:
            if record['source_path'] in [target['root_path'],target['reference_path']]:continue
            data=Path(record['source_path']).read_bytes()
            unchanged.append({'path':record['source_path'],'before_sha256':record['sha256'],'actual_sha256':h(data),
                              'matches':h(data)==record['sha256'] and len(data)==record['bytes']})
        checks['all_other_captured_markdown_unchanged']=all(x['matches'] for x in unchanged)
        for key,val in checks.items(): all_checks[target['profile']+':'+key]=val
        entries.append({'profile':target['profile'],'root_path':target['root_path'],'reference_path':target['reference_path'],
                        'current_root_sha256':h(live_root),'expected_after_root_sha256':h(expected),
                        'current_reference_sha256':h(live_ref),'expected_after_reference_sha256':h(ref),
                        'checks':checks,'other_files':unchanged})
    result={'created_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'phase':args.phase,'head':HEAD,
            'scope':'Read-only byte/frontmatter/diff validation; predictive dry-run is not live installation or QA',
            'selftest':tests,'checks':all_checks,'checks_passed':sum(v is True for v in all_checks.values()),
            'checks_total':len(all_checks),'entries':entries,'overall_pass':all(v is True for v in all_checks.values()),
            'unattested':['semantic acceptance','native loader registration across profiles','serving independence','future model behavior','live full stop','economic effect']}
    if args.out:
        p=Path(args.out)
        if p.resolve().parent!=ROOT.resolve():raise RuntimeError('Receipt outside evidence root')
        data=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
        with p.open('xb') as f:f.write(data)
        print(json.dumps({'receipt_path':str(p),'receipt_sha256':h(data),'receipt_bytes':len(data)},ensure_ascii=False))
    print(json.dumps({k:result[k] for k in ['phase','checks_passed','checks_total','overall_pass','scope','unattested']},ensure_ascii=False))
    if not result['overall_pass']:raise SystemExit(1)

if __name__=='__main__':main()
