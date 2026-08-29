from __future__ import annotations

from fleet_policy.drift import approval_drift


def test_approval_docs_and_executable_policy_are_in_sync(runtime):
    assert approval_drift(runtime.root, runtime.config) == []
