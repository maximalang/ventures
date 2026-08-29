from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConfigError(RuntimeError):
    pass


TASK_TYPES = {"research", "code", "review", "ops"}
BUDGET_KEYS = {"tokens", "wall_clock_minutes", "tool_calls", "retries"}


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    try:
        raw = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read fleet policy config: {config_path}") from exc
    if config_path.suffix.lower() == ".json":
        data = json.loads(raw)
    else:
        try:
            import yaml
        except ImportError as exc:
            raise ConfigError("PyYAML is required to load fleet-policy YAML") from exc
        data = yaml.safe_load(raw)
    if not isinstance(data, dict) or data.get("schema") != "hermes-fleet-policy" or data.get("version") != 1:
        raise ConfigError("invalid fleet policy schema/version")
    budgets = data.get("budgets")
    if not isinstance(budgets, dict) or set(budgets) != TASK_TYPES:
        raise ConfigError(f"budgets must define exactly {sorted(TASK_TYPES)}")
    for task_type, budget in budgets.items():
        if not isinstance(budget, dict) or set(budget) != BUDGET_KEYS:
            raise ConfigError(f"budget {task_type} must define exactly {sorted(BUDGET_KEYS)}")
        if any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in budget.values()):
            raise ConfigError(f"budget {task_type} values must be positive integers")
    return data
