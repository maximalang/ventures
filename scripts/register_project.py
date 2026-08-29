from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path
import yaml

ROOT = Path("C:/Users/max/Desktop/all/ventures")


def run(*args: str) -> None:
    result = subprocess.run(list(args), check=False, text=True)
    if result.returncode:
        raise SystemExit(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Register a revenue project with a board and thin skill")
    parser.add_argument("slug")
    parser.add_argument("--name", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--metric", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}", args.slug):
        raise SystemExit("invalid slug")
    repo = Path(args.repo)
    if not (repo / ".git").exists():
        raise SystemExit("project requires an existing git repo")
    if args.dry_run:
        print(f"would create board/project/skill/config/registry: {args.slug} owner={args.owner} metric={args.metric}")
        return 0
    skill = ROOT / "skills" / f"{args.slug}-project" / "SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    if not skill.exists():
        skill.write_text(
            f"---\nname: {args.slug}-project\ndescription: Use for {args.name} project tasks.\n---\n\n"
            f"# {args.name}\n\nRepo: `{repo.as_posix()}`. Owner: `{args.owner}`. Primary metric: `{args.metric}`.\n\n"
            "Before work read the repo's canonical AGENTS.md/CLAUDE.md. Use the project board as task truth. "
            "Record evidence, metric impact, rollback, and next action; do not duplicate repo rules here.\n",
            encoding="utf-8",
        )
    run("hermes", "kanban", "boards", "create", args.slug, "--name", args.name,
        "--description", f"{args.name}: owner={args.owner}; metric={args.metric}",
        "--default-workdir", str(repo))
    run("hermes", "project", "create", args.name, str(repo), "--slug", args.slug,
        "--primary", str(repo), "--board", args.slug)
    config_path = ROOT / "config" / "fleet-policy.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config.setdefault("projects", {})[args.slug] = {
        "project": args.slug, "path": str(repo),
        "guidance": skill.relative_to(ROOT).as_posix(),
    }
    config_path.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")
    registry = ROOT / "PORTFOLIO.md"
    text = registry.read_text(encoding="utf-8")
    marker = f"| {args.name} | `{repo.as_posix()}`"
    if marker not in text:
        text += f"\n| {args.name} | `{repo.as_posix()}` | `{args.slug}` | `{args.slug}` | Registered | `{args.owner}` | Improve `{args.metric}` |\n"
        registry.write_text(text, encoding="utf-8")
    print(f"created board/project/skill/config/registry for {args.slug}; commit/push the scoped repo changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
