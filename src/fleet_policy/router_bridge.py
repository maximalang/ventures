"""v1.2.36 — SPEC v5: нативный автороутинг в pre-claim пути диспатча.

Мост между плагином fleet-policy (``kanban_task_claimed`` — существующий
официальный pre-claim guard) и ``router_hook.py`` в каталоге скриптов профиля
company (рядом с ``model_router.py`` и ``card_readiness.py``). Только штатные
примитивы Hermes: per-card model/provider override канбан-карты
(``hermes kanban set-model``), комментарий карты (``hermes kanban comment``),
конфиг-флаг (``router_hook.enabled`` в fleet-policy.yaml) и runtime-файл
режима ROUTER_ACTIVE.json рядом с hook. Никаких новых демонов/слоёв.

Контракт best-effort: роутер НИКОГДА не блокирует claim — любой сбой
деградирует молча к профильному дефолту (канон 7) и наблюдаем только через
событие policy-store kind="router_hook".

Семантика enforce: ``set-model`` нативно «applies on the next dispatch» —
пин, поставленный в момент claim, управляет следующим (ре)диспатчем карты;
поставленный до первого claim (вручную/ранним прогоном) — первым spawn.
Поставочный режим — shadow (пишет ROUTING-LOG.md, пин НЕ ставит).
Откат — {"mode": "off"} в ROUTER_ACTIVE.json (без передеплоя) или
router_hook.enabled=false в конфиге.
"""
from __future__ import annotations

import importlib.util
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Optional

# Путь по умолчанию: <hermes-home>/profiles/company/scripts/router_hook.py —
# тот же конвеншен резолва home, что в kanban_context._home_dir.
_COMPANY_HOOK_PARTS = ("profiles", "company", "scripts", "router_hook.py")
_HOOK_CACHE: dict[str, tuple[float, Any]] = {}
_BOARD_DB_CACHE: dict[str, str] = {}


def router_config(config: Optional[dict[str, Any]]) -> dict[str, Any]:
    rh = (config or {}).get("router_hook")
    return rh if isinstance(rh, dict) else {}


def router_enabled(config: Optional[dict[str, Any]]) -> bool:
    """Мастер-флаг интеграции: только явный true (отсутствие/мусор → off)."""
    return router_config(config).get("enabled") is True


def hook_script_path(config: Optional[dict[str, Any]], env: Optional[dict[str, str]] = None) -> Path:
    environ = env if env is not None else os.environ
    explicit = router_config(config).get("script") or environ.get("HERMES_ROUTER_HOOK")
    if explicit:
        return Path(str(explicit))
    home = Path(environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")) / "hermes"
    return home.joinpath(*_COMPANY_HOOK_PARTS)


# Соседние stdlib-модули, которые hook импортирует из своего каталога
# (top-level ``import model_router`` → sys.modules). Их mtime входят в
# сигнатуру кэша: замена ТОЛЬКО таблицы правил инвалидирует кэш без правки
# hook'а и без рестарта процесса (t_9d220da7: промоушен v6.2 оставил
# долгоживущие процессы на v4-таблице до рестарта хоста).
_HOOK_DEPS = ("model_router",)


def _deps_signature(path: Path) -> tuple:
    """Сигнатура кэша hook'а: его mtime + mtime каждого sibling-dep
    (None для отсутствующего dep — import в hook'е тогда падает на exec,
    как и раньше)."""
    sig: list = [path.stat().st_mtime]
    for name in _HOOK_DEPS:
        try:
            sig.append(path.parent.joinpath(f"{name}.py").stat().st_mtime)
        except OSError:
            sig.append(None)
    return tuple(sig)


def _evict_deps(path: Path) -> None:
    """Сбросить dep-модули, импортированные ИЗ КАТАЛОГА hook'а, чтобы
    top-level ``import model_router`` в свежем exec перечитал байты с диска
    (контракт sys.path.insert(HERE) сохраняется). Одноимённый модуль из
    ЧУЖОГО каталога не трогаем (status-quo связывание)."""
    try:
        hook_dir = path.resolve().parent
    except OSError:
        return
    for name in _HOOK_DEPS:
        mod = sys.modules.get(name)
        mod_file = getattr(mod, "__file__", None) if mod is not None else None
        if not mod_file:
            continue
        try:
            same_dir = Path(str(mod_file)).resolve().parent == hook_dir
        except OSError:
            same_dir = False
        if same_dir:
            sys.modules.pop(name, None)


def load_hook(path: Path) -> Any:
    """Импорт router_hook.py с диска (кэш по path + mtime hook'а и его
    sibling-deps; stdlib-only модуль). Hot-reload таблицы без рестарта."""
    key = str(path)
    sig = _deps_signature(path)
    cached = _HOOK_CACHE.get(key)
    if cached is not None and cached[0] == sig:
        return cached[1]
    _evict_deps(path)
    spec = importlib.util.spec_from_file_location("fleet_router_hook", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load router hook: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _HOOK_CACHE[key] = (sig, module)
    return module


def _board_db(ctx: dict[str, Any], board: str) -> str:
    """Путь kanban.db карты: из ctx (worker-путь) или резолвом каталога бордов
    (dispatcher-путь); кэш board→path. Пусто = деградация без pin/фактов."""
    db = str(ctx.get("kanban_db") or "")
    if db:
        return db
    key = str(board or "")
    if key in _BOARD_DB_CACHE:
        return _BOARD_DB_CACHE[key]
    resolved = ""
    try:
        if key:
            from .kanban_context import board_db_path

            resolved = str(board_db_path(key))
    except Exception:
        resolved = ""
    _BOARD_DB_CACHE[key] = resolved
    return resolved


def card_payload(ctx: dict[str, Any], task_id: str, board: str,
                 task_type: Optional[str] = None) -> dict[str, Any]:
    """Карта для router_hook.decide: те же поля, что model_router.py --card.

    title/body — из ctx (load_task_context); task_type — из пре-диспатч
    проверки (runtime().task_type); pinned_model/prior_run_failed — read-only
    запросом канбан-БД (tasks.model_override/consecutive_failures).
    author_model — в процессе диспатчера автор карты неизвестен: env
    HERMES_ROUTER_AUTHOR_MODEL/HERMES_MODEL, иначе поле отсутствует
    (консервативная деградация: R1 review-исключение author_model не сработает,
    класс не повысится — канон 7).
    """
    card: dict[str, Any] = {
        "task_id": task_id,
        "title": str(ctx.get("task_title") or ""),
        "body": str(ctx.get("task_body") or ""),
    }
    if task_type:
        card["task_type"] = str(task_type)
    author_model = os.environ.get("HERMES_ROUTER_AUTHOR_MODEL") or os.environ.get("HERMES_MODEL")
    if author_model:
        card["author_model"] = author_model
    db = _board_db(ctx, board)
    if db and Path(db).is_file():
        try:
            conn = sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro", uri=True, timeout=2)
            try:
                row = conn.execute(
                    "SELECT model_override, provider_override, consecutive_failures "
                    "FROM tasks WHERE id = ?", (task_id,),
                ).fetchone()
            finally:
                conn.close()
            if row:
                if row[0]:
                    card["pinned_model"] = f"{row[1]}/{row[0]}" if row[1] else str(row[0])
                card["prior_run_failed"] = bool(row[2])
        except sqlite3.Error:
            pass  # нет фактов пина — деградация безопасна (канон 7)
    return card


def _cli_env() -> dict[str, str]:
    # Штатный паттерн card_readiness.kanban: дочерний env БЕЗ HERMES_KANBAN_*,
    # чтобы CLI резолвил борд по явному --board, а не по пину чужого воркера.
    return {k: v for k, v in os.environ.items() if not k.startswith("HERMES_KANBAN_")}


def _default_runner(cmd: list[str], timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=_cli_env())


def apply_override(board: str, task_id: str, decision: dict[str, Any],
                   runner: Optional[Callable[[list[str], int], Any]] = None) -> bool:
    """enforce: штатные поля карты — set-model + комментарий «ROUTER vN: …».

    Возвращает True при успехе set-model. Комментарий пишется в любом случае
    успеха set-model; сбой comment не отменяет пин (виден в логе/событии)."""
    run = runner or _default_runner
    model = str(decision.get("model") or "")
    if not model:
        return False
    b = str(board or "default")
    cmd = ["hermes", "kanban", "--board", b, "set-model", task_id, model]
    if decision.get("provider"):
        cmd += ["--provider", str(decision["provider"])]
    result = run(cmd, 30)
    ok = int(getattr(result, "returncode", 1) or 0) == 0
    if ok:
        comment = (f"ROUTER {decision.get('router_version') or ''}: "
                   f"model={decision.get('provider') or '-'}/{model} "
                   f"pattern={model} rules_sha={decision.get('rules_sha') or '-'}")
        run(["hermes", "kanban", "--board", b, "comment", task_id, comment,
             "--author", "fleet-router"], 30)
    return ok


def router_step(ctx: dict[str, Any], task_id: str, board: str, run_id: Any,
                config: Optional[dict[str, Any]], store: Any = None,
                task_type: Optional[str] = None,
                runner: Optional[Callable[[list[str], int], Any]] = None) -> Optional[dict[str, Any]]:
    """Один шаг автороутинга в pre-claim пути. None = флаг выключен/hook не
    найден/режим off. Исключения не глотает только вызывающий плагин (canon 7:
    claim не блокируется); сам шаг best-effort на всех внутренних путях."""
    if not router_enabled(config):
        return None
    path = hook_script_path(config)
    if not path.is_file():
        return None
    rh = router_config(config)
    hook = load_hook(path)
    active = rh.get("active_file") or str(path.parent / "ROUTER_ACTIVE.json")
    card = card_payload(ctx, task_id, board, task_type=task_type)
    decision = hook.decide(card, active_path=active, log_path=rh.get("log_file"),
                           status_path=rh.get("status_file"))
    if not isinstance(decision, dict):
        return None
    applied: Optional[bool] = None
    if decision.get("action") == "override":
        applied = apply_override(board, task_id, decision, runner=runner)
        decision["applied"] = applied
    if store is not None:
        try:
            store.record_event(
                f"router:{task_id}:{run_id or 'claim'}", str(run_id or task_id), task_id,
                "router_hook",
                {"board": str(board or ""), "mode": decision.get("mode"),
                 "action": decision.get("action"), "class": decision.get("class"),
                 "model": decision.get("model"), "provider": decision.get("provider"),
                 "rules_sha": decision.get("rules_sha"), "applied": applied,
                 "logged": decision.get("logged"), "degrade": decision.get("degrade")},
                False,
            )
        except Exception:
            pass  # наблюдаемость не должна ломать диспатч
    return decision
