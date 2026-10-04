"""Freeze allowed non-secret workflow docs and public docs as DATA.
No runtime updates, live services, config edits or execution of sources.
"""
from __future__ import annotations
import concurrent.futures
import datetime as dt
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parent
OLD = Path('C:/Users/max/Desktop/all/ventures/docs/fleet-ops/dots-20261003')
PROFILES = Path('C:/Users/max/AppData/Local/hermes/profiles')
VENTURES = Path('C:/Users/max/Desktop/all/ventures')
RUNTIME = Path('C:/Users/max/AppData/Local/hermes/hermes-agent')
EXPECTED_METHOD = 'f2a85ced87b620bf08cdfc2f3de85ce004a2912efded4da85b668148f00dce6f'
DOCS = {
    'kanban': 'user-guide/features/kanban',
    'delegation': 'user-guide/features/delegation',
    'cron': 'user-guide/features/cron',
    'memory': 'user-guide/features/memory',
    'skills': 'user-guide/features/skills',
    'context-files': 'user-guide/features/context-files',
    'sessions': 'user-guide/sessions',
    'profiles': 'user-guide/profiles',
    'security': 'user-guide/security',
    'hooks': 'user-guide/features/hooks',
    'webhooks': 'user-guide/messaging/webhooks',
    'subagent-lifecycle': 'developer-guide/subagent-lifecycle-api',
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_new(rel: str, data: bytes) -> dict:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    # Restart-safe only for identical snapshot bytes, never overwrite drift.
    if path.exists():
        if path.read_bytes() != data:
            raise RuntimeError('Existing artifact differs: ' + str(path))
    else:
        with path.open('xb') as handle:
            handle.write(data)
    return {'path': str(path), 'bytes': len(data), 'sha256': digest(data)}


def safe_input(path: Path) -> bytes:
    forbidden = ('auth.json', 'secrets', 'credentials', 'dumps')
    if any(p.lower().startswith('.env') or p.lower() in forbidden for p in path.parts):
        raise RuntimeError('Forbidden source path')
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_bytes()


class ArticleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.article_depth = None
        self.skip = 0
        self.out = []
        self.article_count = 0
    def handle_starttag(self, tag, attrs):
        if tag not in {'meta','link','br','hr','img','input','source','wbr','area','base','embed','param','track','col'}:
            self.depth += 1
        if tag == 'article':
            self.article_count += 1
            self.article_depth = self.depth
        if self.article_depth is not None:
            if tag in {'script','style','noscript','nav'}:
                self.skip += 1
            if not self.skip and tag in {'p','div','li','h1','h2','h3','h4','pre','tr','section','br','hr','blockquote'}:
                self.out.append('\n')
    def handle_endtag(self, tag):
        if self.article_depth is not None and tag in {'script','style','noscript','nav'}:
            self.skip = max(0, self.skip - 1)
        if self.article_depth is not None and not self.skip and tag in {'p','li','h1','h2','h3','h4','pre','tr','section','blockquote'}:
            self.out.append('\n')
        if tag == 'article':
            self.article_depth = None
        if tag not in {'meta','link','br','hr','img','input','source','wbr','area','base','embed','param','track','col'}:
            self.depth -= 1
    def handle_data(self, data):
        if self.article_depth is not None and not self.skip:
            self.out.append(data)
    def text(self):
        s = ''.join(self.out).replace('\xa0', ' ')
        s = re.sub(r'[ \t]+', ' ', s)
        s = re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+', '\n\n', s)
        return s.strip() + '\n'


def fetch_public(item):
    name, suffix = item
    url = 'https://hermes-agent.nousresearch.com/docs/' + suffix
    req = urllib.request.Request(url, headers={'User-Agent': 'Hermes-workflow-doc-audit/1.0'})
    with urllib.request.urlopen(req, timeout=50) as response:
        raw = response.read()
        status = response.status
        final = response.url
        ctype = response.headers.get('Content-Type', '')
    if status != 200 or not final.startswith('https://hermes-agent.nousresearch.com/docs/'):
        raise RuntimeError('Unaccepted public response: ' + name)
    parser = ArticleText()
    parser.feed(raw.decode('utf-8'))
    text = parser.text()
    if parser.article_count != 1 or len(text) < 1000:
        raise RuntimeError('Incomplete public article extraction: ' + name)
    record = {
        'name': name, 'url': url, 'final_url': final, 'http_status': status,
        'content_type': ctype, 'retrieved_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'article_count': parser.article_count,
        'raw': save_new('public/hermes-' + name + '.html', raw),
        'text': save_new('public/hermes-' + name + '.txt', text.encode('utf-8')),
        'scope': 'Full public article text; data only, no live capability or enforcement attestation',
    }
    return record


def main():
    inputs = []
    local_names = ['AGENTS.md','OPERATING_SYSTEM.md','APPROVALS.md','ORG_MODEL.md']
    for name in local_names:
        data = safe_input(VENTURES / name)
        inputs.append({'source_path': str(VENTURES / name), 'kind': 'fleet-canon', **save_new('local/ventures/' + name, data)})
    company = PROFILES / 'company' / 'skills'
    skill_paths = [
        'company-os/SKILL.md',
        'company-os/references/outcome-loop.md',
        'company-os/references/adaptive-product-organization.md',
        'devops/kanban-card-authoring/SKILL.md',
        'devops/sdlc-review/SKILL.md',
        'fleet-workflow-efficiency/SKILL.md',
        'fleet-ops/fleet-skills-rollout/SKILL.md',
        'fleet-ops/fleet-skills-rollout/references/scoped-additive-rollouts.md',
        'fleet-ops/fleet-notification-ops/SKILL.md',
        'fleet-ops/fleet-browser-routing/SKILL.md',
        'fleet-doctrine/fleet-doctrine/SKILL.md',
        'autonomous-ai-agents/hermes-agent/SKILL.md',
        'autonomous-ai-agents/hermes-agent/references/background-systems.md',
    ]
    for rel in skill_paths:
        path = company / rel
        if not path.is_file():
            # Find only this SKILL.md within the active company's skill tree.
            skillname = Path(rel).parts[-2] if rel.endswith('SKILL.md') else None
            matches = [p for p in company.rglob('SKILL.md') if p.parent.name == skillname] if skillname else []
            if len(matches) != 1:
                raise FileNotFoundError(path)
            path = matches[0]
        data = safe_input(path)
        inputs.append({'source_path': str(path), 'kind': 'company-skill', **save_new('local/company-skills/' + rel, data)})
    old_list = json.loads(safe_input(OLD / 'TARGETS-BASELINE.json'))['targets']
    if len(old_list) != 12 or len({x['profile'] for x in old_list}) != 12:
        raise RuntimeError('Old target allowlist count/uniqueness mismatch')
    targets = []
    hook = safe_input(OLD / 'LOAD-HOOK.md')
    inputs.append({'source_path': str(OLD / 'LOAD-HOOK.md'), 'kind': 'old-hook', **save_new('local/old-hook.md', hook)})
    for target in old_list:
        rootpath = Path(target['root_path'])
        refpath = Path(target['new_reference_path'])
        rootdata = safe_input(rootpath)
        refdata = safe_input(refpath)
        if digest(refdata) != EXPECTED_METHOD or not rootdata.endswith(hook) or rootdata.count(hook) != 1:
            raise RuntimeError('Old-method/current-hook drift: ' + target['profile'])
        if not rootpath.is_relative_to(PROFILES / target['profile'] / 'skills'):
            raise RuntimeError('Target path outside profile skills')
        snapshots = {
            'root': save_new('before/' + target['profile'] + '/SKILL.md', rootdata),
            'reference': save_new('before/' + target['profile'] + '/dots-operating-method.md', refdata),
        }
        auxiliary = []
        skillroot = rootpath.parent
        # Capture the actual scoped skill tree, only ordinary Markdown.
        for p in sorted(skillroot.rglob('*.md')):
            data = safe_input(p)
            auxiliary.append({'source_path': str(p), 'relative_path': p.relative_to(skillroot).as_posix(),
                              **save_new('before-trees/' + target['profile'] + '/' + p.relative_to(skillroot).as_posix(), data)})
        targets.append({'profile': target['profile'], 'root_path': str(rootpath), 'reference_path': str(refpath),
                        'before_root_sha256': digest(rootdata), 'before_reference_sha256': digest(refdata),
                        'unmodified_root_sha256': digest(rootdata[:-len(hook)]), 'snapshots': snapshots,
                        'markdown_tree': auxiliary})
    core_sources = json.loads(safe_input(OLD / 'SOURCES.json'))['sources']
    core_sources += json.loads(safe_input(OLD / 'SOURCES-ADDENDUM.json'))['additional_core_sources']
    dots = [s for s in core_sources if s.get('class') == 'dots-core' or s['name'] == 'dots-enterprise-local-access']
    if len(dots) != 8 or len({s['name'] for s in dots}) != 8:
        raise RuntimeError('Dots core source coverage mismatch')
    for entry in dots:
        path = Path(entry['path'])
        data = safe_input(path)
        if digest(data) != entry['file_sha256'] or len(data) != entry['file_bytes']:
            raise RuntimeError('Frozen Dots source changed: ' + entry['name'])
        inputs.append({'source_path': str(path), 'kind': 'verified-dots-source', 'source_url': entry['final_url'],
                       **save_new('dots-sources/' + path.name, data)})
    public = []
    errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fetch_public, item): item[0] for item in DOCS.items()}
        for future in concurrent.futures.as_completed(futures):
            try:
                public.append(future.result())
            except Exception as e:
                errors.append({'name': futures[future], 'error': type(e).__name__ + ': ' + str(e)})
    revisions = {}
    for name, repo in [('installed_hermes', RUNTIME), ('fleet_integration', VENTURES)]:
        head = subprocess.run(['git','-C',str(repo),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
        status = subprocess.run(['git','-C',str(repo),'status','--short'],capture_output=True,text=True,check=True).stdout.splitlines()
        revisions[name] = {'repo': str(repo), 'head': head, 'working_tree_dirty': bool(status),
                           'scope': 'Source checkout identity only; dirty files are frozen separately; no loaded-runtime claim'}
    # Bind each published document to the actual local source-doc bytes when present.
    installed_docs = []
    for name, suffix in DOCS.items():
        p = RUNTIME / 'website/docs' / (suffix + '.md')
        if p.is_file():
            installed_docs.append({'name': name, 'source_path': str(p),
                                   **save_new('installed-docs/' + name + '.md', safe_input(p))})
    manifest = {
        'created_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'scope': 'Dots versus existing Hermes workflow; source/data snapshot only',
        'revisions': revisions, 'old_method_sha256': EXPECTED_METHOD,
        'targets': targets, 'inputs': inputs, 'public_hermes_docs': sorted(public,key=lambda x:x['name']),
        'public_doc_errors': errors, 'installed_docs': installed_docs,
        'permitted_live_writes_for_later_review': [
            {'profile': t['profile'], 'paths': [t['root_path'],t['reference_path']]} for t in targets
        ],
        'financial_scope': {
            'scope': 'fleet-ops internal workflow normalization',
            'period_start_utc': '2026-10-03T22:33:54+00:00',
            'period_end_utc': None,
            'confirmed_revenue': None, 'refunds': None, 'incremental_paid_costs': None,
            'new_commitments': None, 'estimated_usage_cost': None,
            'source': 'Source collection and task scope; no billing/ledger readback',
            'unknown_reason': 'Not a revenue experiment; billing not measured; no paid capability/order is permitted',
        },
    }
    data = (json.dumps(manifest,ensure_ascii=False,indent=2) + '\n').encode('utf-8')
    record = save_new('BASELINE.json', data)
    print(json.dumps({'baseline': record, 'targets': len(targets), 'dots_core_sources': len(dots),
                      'public_hermes_docs': len(public), 'installed_source_docs': len(installed_docs),
                      'errors': errors, 'source_revisions': revisions},ensure_ascii=False,indent=2))
    if errors or len(public) != len(DOCS):
        raise SystemExit(2)

if __name__ == '__main__':
    main()
