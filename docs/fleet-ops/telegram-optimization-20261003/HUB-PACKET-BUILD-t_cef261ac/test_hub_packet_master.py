# -*- coding: utf-8 -*-
"""HUB-PACKET acceptance tests (t_cef261ac). SOURCE-ONLY, read-only against live skills.

Run:  python tests/test_hub_packet.py   (from packet root or anywhere; unittest)
Env override for live anchor root: HUB_PACKET_SKILLS_ROOT
"""
import hashlib
import json
import os
import re
import unittest
from pathlib import Path

PACKET = Path(__file__).resolve().parent.parent
SKILLS = Path(os.environ.get("HUB_PACKET_SKILLS_ROOT",
                             r"C:/Users/max/AppData/Local/hermes/profiles/company/skills"))
SKILL_DIRS = {
    "hermes-agent": SKILLS / "autonomous-ai-agents" / "hermes-agent",
    "fleet-token-economy": SKILLS / "fleet-ops" / "fleet-token-economy",
}
MANIFEST = json.loads((PACKET / "MANIFEST.json").read_bytes().decode("utf-8"))
INV = json.loads((PACKET / "INVARIANT-MAP.json").read_bytes().decode("utf-8"))
CORRECTIONS = INV["corrections"]


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def live_text(skill):
    return (SKILL_DIRS[skill] / "SKILL.md").read_bytes().decode("utf-8")


def slice_src(text, start, end):
    assert text.count(start) == 1, f"anchor not unique: {start[:50]!r}"
    i = text.index(start)
    if end is None:
        return text[i:]
    assert text.count(end) == 1, f"end anchor not unique: {end[:50]!r}"
    j = text.index(end)
    assert j > i
    return text[i:j]


def frontmatter(text):
    nl = "\r\n" if text.startswith("---\r\n") else "\n"
    idx = text.index(nl + "---" + nl, 3)
    return text[: idx + len(nl) + 3 + len(nl)]


def applied_tree(skill):
    """Live files overlaid with packet candidates: relpath -> text."""
    tree = {}
    for p in SKILL_DIRS[skill].rglob("*"):
        if p.is_file():
            tree[str(p.relative_to(SKILL_DIRS[skill])).replace("\\", "/")] = p.read_bytes().decode("utf-8")
    cand_root = PACKET / "candidates" / skill
    for p in cand_root.rglob("*"):
        if p.is_file():
            tree[str(p.relative_to(cand_root)).replace("\\", "/")] = p.read_bytes().decode("utf-8")
    return tree


def corrected_slice(skill, span, corr_ids):
    src = live_text(skill)
    if span["type"] == "frontmatter":
        text = frontmatter(src)
    elif span["type"] == "support_bullets":
        sup = slice_src(src, "## Support files", None)
        text = sup.split("\r\n\r\n", 1)[1]
    else:
        text = slice_src(src, span["start"], span["end"])
    for cid in corr_ids or []:
        c = CORRECTIONS[cid]
        assert text.count(c["before"]) == 1, f"correction anchor not unique: {cid}"
        text = text.replace(c["before"], c["after"])
    return text


class T01_AnchorIntegrity(unittest.TestCase):
    def test_live_files_match_manifest_before_hashes(self):
        for skill, files in MANIFEST["before_tree"].items():
            root = SKILL_DIRS[skill]
            live = sorted(str(p.relative_to(root)).replace("\\", "/") for p in root.rglob("*") if p.is_file())
            self.assertEqual(live, [f["path"] for f in files], f"live tree drift in {skill}")
            for f in files:
                b = (root / f["path"]).read_bytes()
                self.assertEqual(sha256_bytes(b), f["sha256"], f"hash drift: {skill}/{f['path']}")
                self.assertEqual(len(b), f["bytes"])
                self.assertEqual(len(b.decode("utf-8")), f["chars"])


class T02_CandidateIntegrity(unittest.TestCase):
    def test_candidate_files_match_manifest(self):
        for skill, files in MANIFEST["candidate_tree"].items():
            root = PACKET / "candidates" / skill
            on_disk = sorted(str(p.relative_to(root)).replace("\\", "/") for p in root.rglob("*") if p.is_file())
            self.assertEqual(on_disk, [f["path"] for f in files])
            for f in files:
                b = (root / f["path"]).read_bytes()
                self.assertEqual(sha256_bytes(b), f["sha256"], f"candidate hash mismatch: {skill}/{f['path']}")

    def test_rollback_snapshots_are_byte_exact(self):
        for r in MANIFEST["rollback_snapshots"]:
            snap = (PACKET / r["packet_file"]).read_bytes()
            self.assertEqual(sha256_bytes(snap), r["sha256"])
            skill = "hermes-agent" if "hermes-agent" in r["dest"] else "fleet-token-economy"
            self.assertEqual(snap, (SKILL_DIRS[skill] / "SKILL.md").read_bytes(),
                             f"rollback snapshot != live source for {skill}")


class T03_FrontmatterTriggers(unittest.TestCase):
    def test_frontmatter_byte_identical_and_triggers_preserved(self):
        for skill in SKILL_DIRS:
            src = live_text(skill)
            cand = (PACKET / "candidates" / skill / "SKILL.md").read_bytes().decode("utf-8")
            fm = frontmatter(src)
            self.assertTrue(cand.startswith(fm), f"{skill}: candidate does not start with byte-exact frontmatter")
            name = re.search(r"^name: (.+?)\r?$", fm, re.M).group(1)
            desc = re.search(r'^description: "(.+?)"\r?$', fm, re.M).group(1)
            self.assertIn(f"name: {name}", cand)
            self.assertIn(f'description: "{desc}"', cand)
        ha = (PACKET / "candidates/hermes-agent/SKILL.md").read_bytes().decode("utf-8")
        self.assertIn('> Extended triggers: "Use, configure, theme, extend, and orchestrate Hermes Agent."', ha)
        self.assertIn("# Hermes Agent", ha)


class T04_SlicePreservation(unittest.TestCase):
    """Every mapped source section exists verbatim (minus recorded corrections) at its destination."""

    def test_all_map_entries(self):
        checked = 0
        for e in INV["entries"]:
            span = e.get("span")
            if not span or span.get("type") == "none":
                continue  # marker-only entry, covered by T05
            if e["disposition"] == "kept_in_hub_verbatim_plus_rows":
                continue  # whole-slice check impossible by design; row-level checks below
            skill = e["skill"]
            text = corrected_slice(skill, span, e.get("corrections"))
            tree = applied_tree(skill)
            dest = e["dest"]
            self.assertIn(dest, tree, f"{e['id']}: dest {dest} missing in applied tree")
            self.assertIn(text, tree[dest], f"{e['id']}: source slice not preserved verbatim in {dest}")
            checked += 1
        self.assertGreaterEqual(checked, 20, "map should cover every section of both hubs")

    def test_routing_kept_with_all_original_rows(self):
        e = next(x for x in INV["entries"] if x["id"] == "HA-RT")
        orig = corrected_slice("hermes-agent", e["span"], None)
        hub = applied_tree("hermes-agent")["SKILL.md"]
        for line in orig.splitlines():
            if line.strip():
                self.assertIn(line, hub, f"routing line lost: {line[:80]!r}")

    def test_routing_addition_rows_present(self):
        add = MANIFEST["routing_addition"]
        hub = applied_tree("hermes-agent")["SKILL.md"]
        for row in add["inserted_rows"]:
            self.assertIn(row, hub)
        self.assertIn(add["anchor_row"], hub)


class T05_Markers(unittest.TestCase):
    def test_markers_at_destination_and_hub(self):
        for e in INV["entries"]:
            skill = e["skill"]
            tree = applied_tree(skill)
            for m in e.get("markers", []):
                self.assertIn(m, tree[e["dest"]], f"{e['id']}: marker missing in dest {e['dest']}: {m[:60]!r}")
            for m in e.get("hub_markers", []):
                self.assertIn(m, tree["SKILL.md"], f"{e['id']}: hub marker missing: {m[:60]!r}")


class T06_ReferenceResolution(unittest.TestCase):
    LINK = re.compile(r"(?<![A-Za-z0-9_./\\-])((?:references|scripts|templates)/[A-Za-z0-9_.\-/]+\.(?:md|py|yaml|mjs|js))")
    PROFILE_LINK = re.compile(r"(?<![A-Za-z0-9_./\\-])(profiles/company/[A-Za-z0-9_.\-/]+\.(?:md|py))")

    def test_every_relative_link_resolves_in_applied_tree(self):
        total = 0
        profile_root = SKILLS.parent  # .../hermes/profiles/company
        for skill in SKILL_DIRS:
            tree = applied_tree(skill)
            cand_root = PACKET / "candidates" / skill
            for p in cand_root.rglob("*"):
                if not p.is_file():
                    continue
                text = p.read_bytes().decode("utf-8")
                for m in set(self.LINK.findall(text)):
                    self.assertIn(m, tree, f"unresolved skill-relative link {m} in {skill}/{p.name}")
                    total += 1
                for m in set(self.PROFILE_LINK.findall(text)):
                    self.assertTrue((profile_root / m.split("profiles/company/", 1)[1]).exists(),
                                    f"unresolved profile-relative link {m} in {skill}/{p.name}")
                    total += 1
        self.assertGreater(total, 30, "link extraction suspiciously low")

    def test_existing_references_untouched(self):
        """Packet must not modify pre-existing reference/script/template files."""
        for skill, files in MANIFEST["before_tree"].items():
            cand_paths = {f["path"] for f in MANIFEST["candidate_tree"][skill]}
            for f in files:
                if f["path"] == "SKILL.md":
                    continue
                self.assertNotIn(f["path"], cand_paths,
                                 f"packet must not overwrite existing file {skill}/{f['path']}")


class T07_SelectiveRetrieval(unittest.TestCase):
    QUERIES = [
        # (skill, hub must contain pointer line with (kw, ref), ref must contain content marker)
        ("hermes-agent", "product-overview.md", "differentiators", "Multi-platform gateway"),
        ("hermes-agent", "product-overview.md", "Scope & Verification", "never behind the product"),
        ("hermes-agent", "quickstart-and-paths.md", "quick start", "install.sh"),
        ("hermes-agent", "quickstart-and-paths.md", "$HERMES_HOME", "Canonical session store"),
        ("hermes-agent", "spawning-instances.md", "Spawning", "tmux new-session"),
        ("hermes-agent", "spawning-instances.md", "delegate_task", "capped at N"),
        ("fleet-token-economy", "measure-first-details.md", "measure-first-details.md", "session_model_usage"),
        ("fleet-token-economy", "levers-playbook.md", "levers-playbook.md", "MoA fan-out"),
        ("fleet-token-economy", "mechanics-pitfalls.md", "mechanics-pitfalls.md", "Skill reload loop after compression"),
        ("fleet-token-economy", "routing-audit-safeguards.md", "routing-audit-safeguards.md", "cost_status=unknown"),
        ("fleet-token-economy", "audit-to-program.md", "audit-to-program.md", "boundary snapshot"),
        ("fleet-token-economy", "prompt-audit-lane.md", "prompt-audit-lane.md", "d341b0d4a136"),
    ]

    def test_hub_pointer_and_ref_content(self):
        for skill, ref, hub_kw, content_marker in self.QUERIES:
            tree = applied_tree(skill)
            hub = tree["SKILL.md"]
            self.assertIn(ref, hub, f"{skill}: hub lacks pointer to {ref}")
            lines = [ln for ln in hub.splitlines() if ref in ln]
            self.assertTrue(any(hub_kw.lower() in ln.lower() for ln in lines),
                            f"{skill}: no hub pointer line for {ref} mentions {hub_kw!r}")
            self.assertIn(content_marker, tree["references/" + ref],
                          f"{skill}/{ref}: content marker {content_marker!r} missing")

    def test_owner_directive_stays_in_hub(self):
        hub = applied_tree("fleet-token-economy")["SKILL.md"]
        src = live_text("fleet-token-economy")
        lever4 = slice_src(src, "4. **Reasoning effort", "5. **Skills index**")
        self.assertIn(lever4, hub, "owner effort directive not byte-preserved in hub")


class T08_Corrections(unittest.TestCase):
    def test_obsolete_claims_gone_and_updates_in_place(self):
        for cid, c in CORRECTIONS.items():
            skill = c["skill"]
            src = live_text(skill)
            self.assertIn(c["before"], src, f"{cid}: before-string not found in live source (anchor drift)")
            tree = applied_tree(skill)
            for rel, text in tree.items():
                if rel == "SKILL.md" or rel.startswith("references/"):
                    self.assertNotIn(c["before"], text, f"{cid}: obsolete claim survives in candidate {rel}")
            self.assertIn(c["after"], tree[c["dest"]], f"{cid}: corrected text missing in {c['dest']}")

    def test_owner_ban_recorded(self):
        tree = applied_tree("fleet-token-economy")
        self.assertIn("do NOT shorten/reset/archive sessions as an economy shortcut",
                      tree["references/levers-playbook.md"])
        self.assertIn("hermes-session-reset-policy 0.3.0", tree["references/levers-playbook.md"])


class T09_Reduction(unittest.TestCase):
    def test_combined_hub_reduction_ge_60(self):
        hb = hc = cb = cc = 0
        for skill in SKILL_DIRS:
            src = live_text(skill).encode("utf-8")
            cand = (PACKET / "candidates" / skill / "SKILL.md").read_bytes()
            hb += len(src); hc += len(src.decode("utf-8"))
            cb += len(cand); cc += len(cand.decode("utf-8"))
        rb = 100.0 * (hb - cb) / hb
        rc = 100.0 * (hc - cc) / hc
        self.assertGreaterEqual(rb, 60.0, f"bytes reduction {rb:.2f}% < 60%")
        self.assertGreaterEqual(rc, 60.0, f"chars reduction {rc:.2f}% < 60%")
        m = MANIFEST["hub_reduction"]
        self.assertEqual((m["combined_bytes_before"], m["combined_bytes_candidate"]), (hb, cb))
        self.assertEqual((m["combined_chars_before"], m["combined_chars_candidate"]), (hc, cc))


class T10_PacketHygieneAndNoLiveWrites(unittest.TestCase):
    ALLOWED_TOP = {"MANIFEST.json", "INVARIANT-MAP.json", "INVARIANT-MAP.md", "README.md",
                   "APPLY-ROLLBACK.md", "STATIC-FOOTPRINT.md", "candidates", "rollback", "tests", "reference"}
    ALLOWED_DIRS = {"candidates", "rollback", "tests", "reference"}

    def test_packet_contains_only_allowed_paths(self):
        for p in PACKET.rglob("*"):
            rel = p.relative_to(PACKET)
            top = rel.parts[0]
            self.assertIn(top, self.ALLOWED_TOP, f"unexpected packet path: {rel}")

    def test_live_skills_still_pristine_after_test_run(self):
        for skill, files in MANIFEST["before_tree"].items():
            root = SKILL_DIRS[skill]
            for f in files:
                self.assertEqual(sha256_bytes((root / f["path"]).read_bytes()), f["sha256"],
                                 f"live file changed during test run: {skill}/{f['path']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
