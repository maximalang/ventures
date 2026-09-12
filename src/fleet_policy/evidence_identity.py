"""Pure snapshot validation, NOT authorization or proof of execution.

Only JSON primitives are accepted. The caller supplies trusted context and time.
Artifact metadata is compared; bytes, Git, clocks and stores are never read.

Canonical digest contract (release_attestation.canonical_bytes): UTF-8 JSON,
sort_keys=True, ensure_ascii=False, compact separators (',', ':'), exactly
one trailing LF. SHA-256 covers the entire envelope except evidence_sha256,
including optional fields. No Unicode normalization is performed. Parsing
rejects duplicate keys; this validator rejects floats/nonfinite numbers and
invalid Unicode before canonicalization. canonical_bytes itself is an encoder,
not a strict parser or schema validator. The digest is not a signature.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re

from .release_attestation import canonical_bytes


@dataclass(frozen=True)
class EvidenceVerdict:
    valid: bool
    codes: tuple[str, ...]
    evidence_sha256: str | None
    decision_revision: int | None
    checked_at: str
    scope: str = 'internal_evidence_validation'


@dataclass(frozen=True)
class ExpectedContext:
    """Caller-owned trusted snapshot; never derived from the envelope here.

    Nested dicts are not mutated. The caller must not concurrently mutate them.
    Authorization/implementation profile lists are trusted policy inputs.
    """
    decision_ref: dict
    decision_revision: int
    target: dict
    subject: dict
    environment: dict
    verifier: dict
    artifact: dict
    decision_active: bool
    allowed_verifier_profiles: tuple[str, ...]
    implementation_profiles: tuple[str, ...]


class _Invalid(ValueError):
    pass


def _require(ok, code='SCHEMA_INVALID'):
    if not ok:
        raise _Invalid(code)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, 'PARSE_INVALID')
        result[key] = value
    return result


def _reject_number(_):
    raise _Invalid('PARSE_INVALID')


def _json_tree(value):
    if type(value) is dict:
        for key, item in value.items():
            _require(type(key) is str, 'PARSE_INVALID')
            key.encode('utf-8')
            _json_tree(item)
    elif type(value) is list:
        for item in value:
            _json_tree(item)
    elif type(value) is str:
        value.encode('utf-8')
    else:
        _require(value is None or type(value) in (bool, int), 'PARSE_INVALID')


def _keys(obj, names, optional=()):
    _require(type(obj) is dict)
    _require(set(names) <= obj.keys() <= set(names) | set(optional))


def _text(value):
    _require(type(value) is str and bool(value) and value == value.strip()
             and len(value) <= 512 and all(ord(c) >= 32 for c in value))


def _int(value, minimum=1):
    _require(type(value) is int and minimum <= value <= 2**63 - 1)


def _hash(value, length):
    _require(type(value) is str and re.fullmatch('[0-9a-f]{%d}' % length, value) is not None,
             'HASH_FORMAT')


def _task(obj, extra):
    _keys(obj, ('board', 'task_id', *extra))
    _text(obj['board'])
    _require(re.fullmatch(r'[a-z0-9][a-z0-9_-]*', obj['board']) is not None)
    _require(type(obj['task_id']) is str and re.fullmatch(r't_[0-9a-f]{8}', obj['task_id']) is not None)


def _file(obj, reference=False):
    _keys(obj, ('relative_path', 'sha256', 'size_bytes', *(('kind',) if reference else ())))
    if reference:
        _require(obj['kind'] == 'local_file')
    path = obj['relative_path']
    _text(path)
    # Portable lexical contract only. No claim of filesystem containment.
    _require(not any(c in path for c in '\\:*?"<>|') and not path.startswith('/'), 'PATH_INVALID')
    for part in path.split('/'):
        _require(part not in ('', '.', '..') and not part.endswith((' ', '.')), 'PATH_INVALID')
        _require(not re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', part), 'PATH_INVALID')
    _hash(obj['sha256'], 64)
    _int(obj['size_bytes'], 0)


def _identities(e):
    _task(e['decision_ref'], ('comment_id',))
    _int(e['decision_ref']['comment_id'])
    _int(e['decision_revision'])
    s = e['subject']
    _keys(s, ('kind', 'repository_id', 'object_format', 'commit', 'implementation'))
    _require(s['kind'] == 'git_commit' and s['object_format'] == 'sha1')
    _text(s['repository_id'])
    _hash(s['commit'], 40)
    _task(s['implementation'], ('run_id',))
    _int(s['implementation']['run_id'])
    _file(e['artifact'])
    t = e['target']
    _task(t, ('kind', 'operation'))
    _require(t['kind'] == 'kanban_handoff' and t['operation'] in ('kanban_complete', 'kanban_request_review'))
    env = e['environment']
    _keys(env, ('kind', 'id', 'manifest_sha256'))
    _require(env['kind'] == 'local')
    _text(env['id'])
    _hash(env['manifest_sha256'], 64)
    v = e['verifier']
    _task(v, ('profile', 'run_id'))
    _text(v['profile'])
    _int(v['run_id'])


def _schema(e):
    _keys(e, ('schema', 'decision_ref', 'decision_revision', 'subject', 'artifact',
              'target', 'environment', 'observed_at', 'valid_until', 'verifier',
              'gate', 'verdict', 'evidence_refs', 'evidence_sha256'), ('note',))
    _require(e['schema'] == 'hermes-evidence/v1')
    _identities(e)
    _require(e['gate'] in ('qa', 'review') and e['verdict'] == 'pass')
    _require(type(e['evidence_refs']) is list and 1 <= len(e['evidence_refs']) <= 8)
    for ref in e['evidence_refs']:
        _file(ref, reference=True)
    _hash(e['evidence_sha256'], 64)
    for key in ('observed_at', 'valid_until'):
        _require(type(e[key]) is str)
    if 'note' in e:
        _require(type(e['note']) is str and len(e['note']) <= 500)


def _timestamp(value):
    _require(re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value) is not None, 'TIMESTAMP_INVALID')
    try:
        return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except ValueError:
        raise _Invalid('TIMESTAMP_INVALID') from None


def validate_evidence_v1(envelope, expected: ExpectedContext | None, *, now: datetime) -> EvidenceVerdict:
    """Return one deterministic first failure; perform no IO or state mutation.

    Parse -> schema -> digest -> context -> decision -> verifier -> subject
    (including artifact claims) -> target -> environment -> time.
    Malformed trusted time/context is reported at the context stage.
    """
    checked = ''
    clock_ok = type(now) is datetime and now.tzinfo is not None and now.utcoffset() is not None
    if clock_ok:
        checked = now.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
    digest = None
    revision = None

    def verdict(code=None):
        return EvidenceVerdict(code is None, (code,) if code else (), digest, revision, checked)

    try:
        if type(envelope) in (str, bytes):
            if type(envelope) is bytes:
                envelope = envelope.decode('utf-8')
            e = json.loads(envelope, object_pairs_hook=_pairs,
                           parse_float=_reject_number, parse_constant=_reject_number)
        else:
            e = envelope
        _json_tree(e)
    except (ValueError, TypeError, UnicodeError, RecursionError):
        return verdict('PARSE_INVALID')
    try:
        _schema(e)
        actual = hashlib.sha256(canonical_bytes({k: v for k, v in e.items() if k != 'evidence_sha256'})).hexdigest()
        _require(actual == e['evidence_sha256'], 'EVIDENCE_DIGEST_MISMATCH')
        digest = actual
        _require(type(expected) is ExpectedContext and clock_ok, 'CONTEXT_UNAVAILABLE')
        try:
            context_fields = {key: getattr(expected, key) for key in
                              ('decision_ref', 'decision_revision', 'target', 'subject', 'environment', 'verifier', 'artifact')}
            _json_tree(context_fields)
            _identities(context_fields)
            _require(type(expected.decision_active) is bool)
            for profiles in (expected.allowed_verifier_profiles, expected.implementation_profiles):
                _require(type(profiles) is tuple and bool(profiles))
                for profile in profiles:
                    _text(profile)
        except (ValueError, TypeError, UnicodeError, RecursionError):
            raise _Invalid('CONTEXT_UNAVAILABLE') from None
        _require(expected.decision_active, 'DECISION_REVOKED')
        _require(e['decision_ref'] == expected.decision_ref, 'DECISION_MISMATCH')
        _require(e['decision_revision'] == expected.decision_revision == e['decision_ref']['comment_id'], 'REVISION_MISMATCH')
        revision = e['decision_revision']
        _require(e['verifier'] == expected.verifier, 'VERIFIER_IDENTITY_MISMATCH')
        _require(e['verifier']['profile'] in expected.allowed_verifier_profiles, 'VERIFIER_UNAUTHORIZED')
        _require(e['verifier']['profile'] not in expected.implementation_profiles, 'SELF_APPROVAL')
        _require(e['subject'] == expected.subject, 'SUBJECT_MISMATCH')
        _require(e['artifact'] == expected.artifact, 'ARTIFACT_MISMATCH')
        _require(e['target'] == expected.target, 'TARGET_MISMATCH')
        _require(e['environment'] == expected.environment, 'ENVIRONMENT_MISMATCH')
        observed, until = _timestamp(e['observed_at']), _timestamp(e['valid_until'])
        _require(observed <= now, 'EVIDENCE_FUTURE')
        _require(until > observed, 'TIMESTAMP_INVALID')
        _require(now < until, 'EVIDENCE_EXPIRED')
        _require(until - observed <= timedelta(hours=24), 'TTL_EXCEEDED')
        return verdict()
    except _Invalid as exc:
        return verdict(str(exc))
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        return verdict('SCHEMA_INVALID')
