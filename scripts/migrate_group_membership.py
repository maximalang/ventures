from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

HERMES_HOME = Path("C:/Users/max/AppData/Local/hermes")
UNIVERSAL = ["company", "tech", "product", "design", "ux", "qa", "research", "sales", "finance", "operations"]


def profile_names() -> list[str]:
    return sorted(path.name for path in (HERMES_HOME / "profiles").iterdir() if path.is_dir())


def desired(profile: str) -> tuple[dict, int]:
    path = HERMES_HOME / "profiles" / profile / "profile.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else {}
    data = data if isinstance(data, dict) else {}
    ui_meta = data.get("ui_meta") if isinstance(data.get("ui_meta"), dict) else {}
    bots = dict(ui_meta.get("hermes-bots")) if isinstance(ui_meta.get("hermes-bots"), dict) else {}
    groups = ["up-team"] if profile in UNIVERSAL else []
    bots["groups"] = groups
    bots["group"] = groups[0] if groups else None
    revisions = data.get("_ui_meta_revisions") if isinstance(data.get("_ui_meta_revisions"), dict) else {}
    return bots, int(revisions.get("hermes-bots", 0) or 0)


def apply(dry_run: bool) -> list[dict]:
    targets = [*UNIVERSAL, *[name for name in profile_names() if name.startswith("rr-")]]
    actions = []
    if not dry_run:
        import tui_gateway.methods_profiles  # noqa: F401
        from tui_gateway import server
        configure = server._methods["profiles.configure"]
    for profile in targets:
        bots, revision = desired(profile)
        item = {"profile": profile, "groups": bots["groups"], "expected_revision": revision}
        if not dry_run:
            response = configure(
                f"fleet-group-{profile}",
                {
                    "name": profile,
                    "ui_meta": {"hermes-bots": bots},
                    "ui_meta_expected_revisions": {"hermes-bots": revision},
                },
            )
            item["response"] = response
            applied = response.get("result", {}).get("applied", {})
            if applied.get("ui_meta") is not True:
                raise RuntimeError(f"profiles.configure failed for {profile}: {response}")
        actions.append(item)
    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate Bot Mode group membership through profiles.configure")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(apply(args.dry_run), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
