from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any


def board_db(board: str, env: dict[str, str] | None = None) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", board or ""):
        raise ValueError("invalid Kanban board slug")
    environ = env or os.environ
    explicit = environ.get("HERMES_KANBAN_DB")
    if explicit:
        return Path(explicit)
    home = Path(environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "hermes"
    if not board or board == "default":
        return home / "kanban.db"
    return home / "kanban" / "boards" / board / "kanban.db"


def load_task_context(base: dict[str, Any], projects: dict[str, Any], env: dict[str, str] | None = None) -> dict[str, Any]:
    environ = env or os.environ
    context = dict(base)
    mapping = {
        "task_id": "HERMES_KANBAN_TASK",
        "run_id": "HERMES_KANBAN_RUN_ID",
        "workspace": "HERMES_KANBAN_WORKSPACE",
        "board": "HERMES_KANBAN_BOARD",
        "profile": "HERMES_PROFILE",
    }
    for key, env_name in mapping.items():
        if not context.get(key) and environ.get(env_name):
            context[key] = environ[env_name]
    board = str(context.get("board") or "default")
    context.setdefault("board", board)
    project = projects.get(board, {}) if isinstance(projects, dict) else {}
    context.setdefault("project", str(project.get("project") or board))
    context.setdefault("profile", str(context.get("assignee") or environ.get("HERMES_PROFILE") or "unknown"))
    task_id = str(context.get("task_id") or "")
    if not task_id:
        context["worker"] = False
        return context
    context["worker"] = True
    path = board_db(board, environ)
    context["kanban_db"] = str(path)
    if not path.is_file():
        context["task_context_error"] = f"kanban DB not found: {path}"
        return context
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(
            "SELECT id,title,body,assignee,status,started_at,max_retries,skills,current_run_id FROM tasks WHERE id=?",
            (task_id,),
        ).fetchone()
        if row is None:
            context["task_context_error"] = f"task not found: {task_id}"
            return context
        context.update({
            "task_title": row["title"] or "",
            "task_body": row["body"] or "",
            "assignee": row["assignee"] or "",
            "profile": row["assignee"] or context.get("profile") or "unknown",
            "task_status": row["status"] or "",
            "started_at": row["started_at"],
            "max_retries": row["max_retries"],
            "current_run_id": row["current_run_id"],
        })
        try:
            skills = json.loads(row["skills"] or "[]")
            context["skills"] = skills if isinstance(skills, list) else []
        except (TypeError, json.JSONDecodeError):
            context["skills"] = []
        comments = connection.execute(
            "SELECT author,body FROM task_comments WHERE task_id=? ORDER BY id", (task_id,)
        ).fetchall()
        context["comments"] = [item["body"] for item in comments]
        context["comment_records"] = [{"author": item["author"] or "", "body": item["body"]} for item in comments]
    finally:
        connection.close()
    return context
