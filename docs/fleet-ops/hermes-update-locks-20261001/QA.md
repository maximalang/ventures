# QA.md — Independent exact-head review (incremental, survives TTL)

Task: t_0ab59219 (qa). Spec: REVIEW.md. Producer: t_91dbfaf5 (tech).
Base: bda33b601d194fb8a43e5660c57542aad14aa372. Candidate: 6f82d6d9ccc2659b621c7ccd93d24653afe2147d.
Run: 1929, model glm-5.3 (zai). Incremental — blocks appended as completed.

## Block 1 — Artifact identity (DONE 2026-10-01, run 1929)

Evidence: workspace evidence/qa-identity3.log, qa-hashes.log, qa-git-diff-base-head.diff.

- wt-base (detached clone): HEAD = bda33b601d…; status --porcelain = 0 lines.
- wt-candidate (detached clone): HEAD = 6f82d6d9ccc2659b621c7ccd93d24653afe2147d; status = 0 lines.
- Producer worktree C:/Users/max/Documents/hermes-update-lock-recovery: HEAD = 6f82d6d9ccc2659b621c7ccd93d24653afe2147d, status = 0 lines (read-only check; not modified by QA).
- Ancestry: rev-list --count base..HEAD = 2; HEAD..base = 0 → base is ancestor, exactly 2 in-scope commits (0d8cc2fe96 tests, 6f82d6d9cc fix).
- Scope: `git diff --name-status base head` = M pm/install.py (+96/-8 per numstat; stat shows 104 changed lines), A tests/pm/test_pm_locked_retired_recovery.py (+563). No other files.
- diff --check exit 0 (no whitespace/conflict markers).
- Protected zones EMPTY diffs (bytes=0): pm/store.py, pm/lock.py, hermes_cli/update_completion.py, pm/gc.py, pm/package.py, pm/registry.py.
- Byte identity: reconstructed `git diff base..head` = 33155 bytes, sha256 bb16e153a90a8cdbdd2355c74acc260c0a1cdfb7726d96653544f8d96d81593b == PATCH.diff sha256 (byte-for-byte equal).
- File hashes at HEAD: pm/install.py 18842b0fe49b5cc337398db9de26cff6361f78bf33a63f0b69303dbfa3cb7a6b; tests/pm/test_pm_locked_retired_recovery.py cfa35afda127c2a641084bd78b93a0a0fe5a65f4814b57561fc1ff9208862e5c — both match MANIFEST.json.
- Workspace note: prior crashed run (claim-TTL) left truncated evidence (qa-identity.log, empty diff); re-verified from scratch this run; wt-base/wt-candidate reused (both were already at correct SHAs, clean).

Block-1 verdict inputs: identity OK. Next: code diff review (Block 2).

