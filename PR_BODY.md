Bounded operator-session carve-out in the secret_read_or_write guard for the fleet's own auth stores.

## Why
DashScope provider retirement (2026-10-10): 8 ghost credential pools could not be removed by any sanctioned CLI path (`hermes auth remove` only suppresses entries, never deletes). Manual JSON surgery was hard-denied for the operator session too, leaving dead entries stranded forever. Owner directed both the purge and the policy loosening.

## Scope (fail-closed)
- operator sessions only (workers keep the deny)
- auth-store basename only (.env*, key files, PEM stay denied)
- terminal lane: python/jq/Node JSON one-liners (read + state_change)
- read lane: grep/findstr probes by literal credential fingerprint or env-var NAME
- direct file reads (read_file/search_files), file-level effects (rm/mv/cp), all worker calls: still hard deny

## Tests
- 7 new regression tests (tests/test_v1238_operator_auth_carveout.py): all pass locally
- full suite: 909 passed; 4 pre-existing env failures identical on clean HEAD (evidence_observer, pristine-manifest)
- version bump 1.2.38 synced: plugin.yaml, integrations plugin.yaml, pyproject.toml, __init__.py, hardening test expectation

Incident context: the purge itself was executed in-session with backup + validated .tmp + os.replace; auth list verified clean afterwards; custom-provider route verified live. Rebased from the collided v1.2.37 branch (1.2.37 is claimed by in-flight fix branches fix/v1237-*).
