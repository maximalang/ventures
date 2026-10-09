# Independent PM candidate review — no end-to-end readiness by inference

Owner: qa. Producer: fleet-ops t_91dbfaf5 (tech).
Review begins only after that producer is done and its durable MANIFEST.json exists at C:/Users/max/Desktop/all/ventures/docs/fleet-ops/hermes-update-locks-20261001/MANIFEST.json.
Exact base: bda33b601d194fb8a43e5660c57542aad14aa372. Exact candidate: immutable full candidate_sha in that manifest, verified against the producer's local commit and submitted PATCH.diff; do not guess or silently review a different SHA. Missing/wrong identity => BLOCK, no publication.
Source implementation contract: IMPLEMENT.md in the same directory. Review every required criterion. Any unproved required claim => numbered BLOCK.

Deliverable: QA.md and QA-MANIFEST.json in the same durable directory, with ONE verdict (APPROVE FOR MERGE or BLOCK), exact base/head, touched files, raw command logs/exit codes/counts, independent fault-probe output and concrete findings. Keep live/source author tree untouched. Make your own detached review worktree at candidate inside your scratch workspace using the known repository's objects. Test imports must resolve there. Use absolute interpreter C:/Users/max/AppData/Local/hermes/hermes-agent/.venv/Scripts/python.exe (pytest and yaml verified).

Required evidence:
1. Artifact identity before and after tests, clean git status, base ancestry, scope diff, patch hash/bytes vs git diff.
2. Reproduce RED at the base and GREEN at the frozen candidate; author logs are claims, not evidence. A baseline collection/import error is not a RED control.
3. Run tests/pm/test_pm_authority.py, tests/pm/test_pm_core.py, the new regression file(s), plus directly affected PM shards. Attribute any failure on candidate against a detached base worktree. Follow the task's bounded suite, not all unrelated tests/ in this large Windows repository.
4. Independent real Windows sharing hold in a fake PM store outside live tools. Check committed new bytes/facts, second install while the hold persists, bounded retained-tree cleanup after release, stage-only semantics, interrupted publish/rollback. A retained tree must not masquerade as an interrupted transaction.
5. Fault matrix: genuine publish/rename/verify/facts-write/restore failure still fails, preserving good old content and original error; ordinary cleanup remains correct. Reject blanket exception suppression, false success, lost rollback guarantees, unbounded dead-tree growth or a new wrapper/monkey-patch.
6. Explicit limitations: this candidate is NOT yet live, no application update was executed, post-source-swap child imports and fleet extension persistence are not proven by PM tests. A source APPROVE permits further gated integration, not a stable-update claim.
7. Record your actual serving model/worker_session_id from supported usage/lineage, not profile defaults. Never read auth/secrets/profile control stores; never change model settings or probe inference. If actual model independence is unavailable, verdict must state it as a condition and cannot be used as the final positive acceptance stamp.

Bans: do not fix reviewed code, write the producer's worktree, publish, merge, apply layers, run application updates/handoffs, restart/stop live processes, alter configs/pools/plugins/private stores, or broaden scope. On policy deny, report exact limitation without alternate-control-plane paths. Use native task tools for lifecycle; put verdict in card and preserve artifacts.

Finance: scoped local repair review, this run period; no external paid action/commitment authorized. Model cost null until usage evidence. Source: raw execution and usage ledger only.
