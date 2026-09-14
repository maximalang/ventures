"""A discussion of a verdict is not an attestation; actual verdicts stay guarded."""


def test_gate_prose_can_be_reported_without_arming_evidence(runtime, task_context):
    context = dict(task_context, profile="product", assignee="product", head="a" * 40)
    for body in (
        "Waiting for gate:review=pass from QA.",
        "The proposed decision:company=go requires company review.",
        "`gate:finance=pass` is an example, not a verdict.",
    ):
        assert runtime.gate_comment_allowed(body, context)
        read_context = dict(context, comment_records=[{"author": "qa", "body": body}])
        assert "review" in runtime.missing_gates("release_to_protected_branch", read_context)


def test_real_gate_lines_still_require_every_authority(runtime, task_context):
    context = dict(task_context, profile="product", assignee="product")
    for body in (
        "gate:review=pass",
        "  gate:review=pass  ",
        "gate:review=pass head=" + "a" * 40,
        "decision:company=go",
        "decision:company=go because evidence passed",
        "Details\ngate:finance=pass\nhead=" + "a" * 40,
        "gate:unknown=pass",
    ):
        assert not runtime.gate_comment_allowed(body, context)
    mixed = dict(task_context, profile="operations", assignee="operations")
    assert not runtime.gate_comment_allowed("gate:rollback=pass\ngate:finance=pass", mixed)
    own_review = dict(task_context, profile="qa", assignee="qa")
    assert not runtime.gate_comment_allowed("gate:review=pass", own_review)
