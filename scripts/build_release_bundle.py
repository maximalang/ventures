from __future__ import annotations

import argparse
from pathlib import Path

from fleet_policy.release_bundle import build_release_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the canonical fleet-policy review/install bundle")
    parser.add_argument("output", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).parents[1])
    args = parser.parse_args()
    files = build_release_bundle(args.root, args.output)
    print(f"bundle={args.output.resolve()} files={len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
