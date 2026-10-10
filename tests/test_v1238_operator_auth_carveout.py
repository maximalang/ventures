"""v1.2.38: operator auth-store maintenance carve-out (regression tests).

Owner-directed credential purges must be executable by operator sessions via
structured JSON edits, while workers, raw reads and destructive file effects
keep the blanket secret_read_or_write deny.
"""
from fleet_policy.policy import PROTECTED_STORE_RULE, classify

CONFIG = {
    "protected": {
        "paths": [
            ".env*", "**/.env*", "auth.json", "**/auth.json",
            "**/*credential*", "**/*secret*", "**/sessions/**", "kanban.db*",
        ],
        "branches": ["main"],
    },
}

AUTH = "C:/Users/max/AppData/Local/hermes/auth.json"


def _cls(name, args, worker):
    return classify(name, args, CONFIG, worker=worker)


def test_operator_structured_json_edit_allowed():
    d = _cls(
        "terminal",
        {"command": f"python -c \"import json;d=json.load(open('{AUTH}'));json.dump(d,open('x.tmp','w'))\""},
        worker=False,
    )
    assert d.decision == "allow", d


def test_operator_fingerprint_probe_allowed():
    d = _cls("terminal", {"command": f"grep -c ee2172 {AUTH}"}, worker=False)
    assert d.decision == "allow", d


def test_worker_structured_edit_still_denied():
    d = _cls(
        "terminal",
        {"command": f"python -c \"import json;json.load(open('{AUTH}'))\""},
        worker=True,
    )
    assert d.decision == "deny" and d.category == PROTECTED_STORE_RULE


def test_worker_probe_still_denied():
    d = _cls("terminal", {"command": f"grep -c ee2172 {AUTH}"}, worker=True)
    assert d.decision == "deny" and d.category == PROTECTED_STORE_RULE


def test_env_store_structured_edit_still_denied():
    d = _cls("terminal", {"command": "python -c \"import json;json.load(open('C:/x/.env'))\""}, worker=False)
    assert d.decision == "deny"


def test_file_delete_still_denied():
    d = _cls("terminal", {"command": f"rm {AUTH}"}, worker=False)
    assert d.decision == "deny"


def test_direct_read_still_denied():
    d = _cls("read_file", {"path": AUTH}, worker=False)
    assert d.decision == "deny"
