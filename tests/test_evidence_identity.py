"""Pure fixtures: no repository, filesystem, DB, clock or network reads."""
import copy
import hashlib
import json
from datetime import datetime, timezone
from dataclasses import replace

import pytest
from fleet_policy import evidence_identity as ei
from fleet_policy.release_attestation import canonical_bytes

NOW = datetime(2026, 9, 9, 12, tzinfo=timezone.utc)


def seal(e):
    e['evidence_sha256'] = hashlib.sha256(canonical_bytes({k:v for k,v in e.items() if k != 'evidence_sha256'})).hexdigest()
    return e


def envelope():
    return seal({
        'schema':'hermes-evidence/v1',
        'decision_ref':{'board':'fleet-ops','task_id':'t_12345678','comment_id':12},
        'decision_revision':12,
        'subject':{'kind':'git_commit','repository_id':'ventures','object_format':'sha1','commit':'a'*40,
                   'implementation':{'board':'fleet-ops','task_id':'t_12345678','run_id':1}},
        'artifact':{'relative_path':'reports/result.json','sha256':'b'*64,'size_bytes':15},
        'target':{'kind':'kanban_handoff','board':'fleet-ops','task_id':'t_23456789','operation':'kanban_complete'},
        'environment':{'kind':'local','id':'local-test','manifest_sha256':'c'*64},
        'observed_at':'2026-09-09T11:00:00Z','valid_until':'2026-09-09T13:00:00Z',
        'verifier':{'profile':'qa','board':'fleet-ops','task_id':'t_23456789','run_id':2},
        'gate':'qa','verdict':'pass',
        'evidence_refs':[{'kind':'local_file','relative_path':'reports/test.txt','sha256':'d'*64,'size_bytes':10}],
    })


def context(e=None):
    e = copy.deepcopy(envelope() if e is None else e)
    return ei.ExpectedContext(
        decision_ref=e['decision_ref'], decision_revision=e['decision_revision'],
        target=e['target'], subject=e['subject'], environment=e['environment'],
        verifier=e['verifier'], artifact=e['artifact'], decision_active=True,
        allowed_verifier_profiles=('qa',), implementation_profiles=('tech',),
    )


def test_parse_failure():
    assert hasattr(ei, 'validate_evidence_v1'), 'pure validator is missing'
    verdict = ei.validate_evidence_v1('{', None, now=NOW)
    assert verdict.valid is False
    assert verdict.codes == ('PARSE_INVALID',)
    assert verdict.scope == 'internal_evidence_validation'


def test_valid_and_deterministic_without_mutation():
    assert hasattr(ei, 'ExpectedContext'), 'trusted context contract is missing'
    e = envelope()
    before = copy.deepcopy(e)
    c = context()
    result = ei.validate_evidence_v1(e, c, now=NOW)
    assert result.valid and result.codes == ()
    assert result == ei.validate_evidence_v1(e, c, now=NOW)
    assert result.evidence_sha256 == e['evidence_sha256']
    assert result.decision_revision == 12
    assert result.checked_at == '2026-09-09T12:00:00Z'
    assert e == before


@pytest.mark.parametrize('field,value,code', [
    ('schema','wrong','SCHEMA_INVALID'),
    ('decision_revision',13,'REVISION_MISMATCH'),
    ('evidence_sha256','0'*64,'EVIDENCE_DIGEST_MISMATCH'),
    ('valid_until','2026-09-09T12:00:00Z','EVIDENCE_EXPIRED'),
    ('observed_at','2026-09-09T12:00:01Z','EVIDENCE_FUTURE'),
])
def test_failures(field, value, code):
    e = envelope()
    e[field] = value
    if field != 'evidence_sha256':
        seal(e)
    assert ei.validate_evidence_v1(e, context(), now=NOW).codes == (code,)


@pytest.mark.parametrize('field', list(envelope()))
def test_missing_fields(field):
    e = envelope()
    del e[field]
    assert ei.validate_evidence_v1(e, context(), now=NOW).codes == ('SCHEMA_INVALID',)


@pytest.mark.parametrize('field,key,value,code', [
    ('verifier','profile','tech','VERIFIER_IDENTITY_MISMATCH'),
    ('target','task_id','t_34567890','TARGET_MISMATCH'),
    ('subject','commit','e'*40,'SUBJECT_MISMATCH'),
    ('environment','id','another','ENVIRONMENT_MISMATCH'),
    ('subject','commit','a'*7,'HASH_FORMAT'),
    ('artifact','sha256','B'*64,'HASH_FORMAT'),
    ('artifact','relative_path','../outside','PATH_INVALID'),
    ('artifact','size_bytes',True,'SCHEMA_INVALID'),
])
def test_nested_failures(field,key,value,code):
    e = envelope()
    e[field][key] = value
    assert ei.validate_evidence_v1(seal(e), context(), now=NOW).codes == (code,)


@pytest.mark.parametrize('raw', ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', b'\xff', '{"a":1e999}', '{"a":"\\ud800"}'])
def test_strict_parse(raw):
    assert ei.validate_evidence_v1(raw,None,now=NOW).codes == ('PARSE_INVALID',)


def test_json_order_and_utf8():
    e = envelope()
    e['note'] = 'Проверено'
    seal(e)
    raw = json.dumps(dict(reversed(list(e.items()))), ensure_ascii=False, indent=2).encode('utf-8')
    assert ei.validate_evidence_v1(raw,context(),now=NOW).valid


def test_context_fail_closed_and_revoked():
    e = envelope()
    assert ei.validate_evidence_v1(e,None,now=NOW).codes == ('CONTEXT_UNAVAILABLE',)
    assert ei.validate_evidence_v1(e,replace(context(),decision_active=False),now=NOW).codes == ('DECISION_REVOKED',)
    assert ei.validate_evidence_v1(e,replace(context(),implementation_profiles=('qa',)),now=NOW).codes == ('SELF_APPROVAL',)
    assert ei.validate_evidence_v1(e,replace(context(),allowed_verifier_profiles=('operations',)),now=NOW).codes == ('VERIFIER_UNAUTHORIZED',)


def test_first_failure_precedence():
    e = envelope()
    e['evidence_sha256'] = '0'*64
    e['target']['task_id'] = 't_87654321'
    assert ei.validate_evidence_v1(e,None,now=NOW).codes == ('EVIDENCE_DIGEST_MISMATCH',)
    seal(e)
    assert ei.validate_evidence_v1(e,None,now=NOW).codes == ('CONTEXT_UNAVAILABLE',)


def test_artifact_claims_only_no_reads():
    e = envelope()
    e['artifact']['sha256'] = 'e'*64
    assert ei.validate_evidence_v1(seal(e),context(),now=NOW).codes == ('ARTIFACT_MISMATCH',)


@pytest.mark.parametrize('path', ['/abs','C:/file','dir\\file','a//b','a/./b','NUL.txt','dir/trailing.'])
def test_unsafe_portable_paths(path):
    e = envelope()
    e['artifact']['relative_path'] = path
    assert ei.validate_evidence_v1(seal(e),context(),now=NOW).codes == ('PATH_INVALID',)


def test_timestamp_format_ttl_and_missing_clock():
    e = envelope()
    e['valid_until'] = '2026-09-11T13:00:00Z'
    assert ei.validate_evidence_v1(seal(e),context(),now=NOW).codes == ('TTL_EXCEEDED',)
    e['valid_until'] = 'not-time'
    assert ei.validate_evidence_v1(seal(e),context(),now=NOW).codes == ('TIMESTAMP_INVALID',)
    assert ei.validate_evidence_v1(envelope(),context(),now=NOW.replace(tzinfo=None)).codes == ('CONTEXT_UNAVAILABLE',)


def test_binding_order():
    e = envelope()
    for field, key, value, code in [
        ('environment','id','other','ENVIRONMENT_MISMATCH'),
        ('target','task_id','t_34567890','TARGET_MISMATCH'),
        ('subject','commit','f'*40,'SUBJECT_MISMATCH'),
        ('verifier','profile','tech','VERIFIER_IDENTITY_MISMATCH'),
        ('decision_ref','task_id','t_34567890','DECISION_MISMATCH'),
    ]:
        e[field][key] = value
        assert ei.validate_evidence_v1(seal(e),context(),now=NOW).codes == (code,)


def test_stale_valid_evidence_after_decision_revocation():
    e = envelope()
    snapshot = copy.deepcopy(e)
    c = context()
    assert ei.validate_evidence_v1(e, c, now=NOW).valid
    # Same unexpired envelope and digest: only trusted decision state changes.
    revoked = replace(c, decision_active=False)
    result = ei.validate_evidence_v1(e, revoked, now=NOW)
    assert not result.valid
    assert result.codes == ('DECISION_REVOKED',)
    assert e == snapshot


def test_unexpected_field_cannot_be_made_valid_by_resealing():
    e = envelope()
    assert ei.validate_evidence_v1(e, context(), now=NOW).valid
    e['unexpected'] = 'mutated'
    assert ei.validate_evidence_v1(e, context(), now=NOW).codes == ('SCHEMA_INVALID',)
    old_digest = e['evidence_sha256']
    seal(e)
    assert e['evidence_sha256'] != old_digest
    assert ei.validate_evidence_v1(e, context(), now=NOW).codes == ('SCHEMA_INVALID',)


def test_optional_field_mutation_invalidates_original_digest():
    e = envelope()
    e['note'] = 'original'
    seal(e)
    assert ei.validate_evidence_v1(e, context(), now=NOW).valid
    old_digest = e['evidence_sha256']
    e['note'] = 'unexpected mutation'
    assert ei.validate_evidence_v1(e, context(), now=NOW).codes == ('EVIDENCE_DIGEST_MISMATCH',)
    seal(e)
    assert e['evidence_sha256'] != old_digest
    assert ei.validate_evidence_v1(e, context(), now=NOW).valid


def test_context_is_not_inferred_and_remains_unchanged():
    c = context()
    snapshot = copy.deepcopy(c)
    assert ei.validate_evidence_v1(envelope(),c,now=NOW).valid
    assert c == snapshot
    assert ei.validate_evidence_v1(envelope(),replace(c,subject={}),now=NOW).codes == ('CONTEXT_UNAVAILABLE',)
