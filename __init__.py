"""Installable root wrapper for the fleet-policy Hermes plugin."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_IMPL = Path(__file__).resolve().parent / "integrations" / "hermes" / "fleet-policy-plugin" / "__init__.py"
_SPEC = importlib.util.spec_from_file_location("ventures_fleet_policy_plugin_impl", _IMPL)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load fleet-policy plugin: {_IMPL}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
register = _MODULE.register
