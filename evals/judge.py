"""LLM-judge client for Company OS text-output evals.

Pattern adapted (not ported) from SenteLabsAI/OpenExecutive (Apache-2.0,
head b071101) per owner decision 07.09.2026 - see evals/README.md.

The judge prompt is a FROZEN constant. Any change requires a conscious
rubric_version bump and re-baselining (tests pin its sha256).

Judge runs on the fleet rail (cheap kimi/glm class) under the qa-profile
rail key, i.e. a different profile than the text author (tech/company).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

RUBRIC_IDS: tuple[str, ...] = (
    "evidence_grounding",
    "decision_clarity",
    "owner_fit",
    "risk_honesty",
    "actionability",
)

# Frozen judge prompt v1. Do not edit without bumping rubric_version in
# evals/rubrics.yaml, updating FROZEN_PROMPT_SHA256 in tests, and
# re-recording evals/baseline.json from a fresh live run.
JUDGE_PROMPT_V1 = """Ты — независимый QA-судья текстовых выходов автономного флота Company OS.
Оцени представленный decision brief по пяти рубрикам. Каждая рубрика оценивается целым числом от 1 до 5.

Рубрики:
1. evidence_grounding — каждое содержательное утверждение подкреплено проверяемой ссылкой: URL, SHA, путь к файлу, команда с exit code, или явно помечено как допущение.
2. decision_clarity — ровно одно решение сформулировано явно (go/no-go/iterate/kill), названы метрика, kill-критерий и следующий шаг.
3. owner_fit — текст краткий, на русском, executive-стиль: факты и выводы, без рутинных деталей и воды; собственник понимает суть за 30 секунд.
4. risk_honesty — лимиты, гейты, неопределённости и проваленные проверки названы явно; локальные проверки отделены от живых/удалённых (local vs live evidence).
5. actionability — следующий шаг измерим (конкретный результат или проверка) и назначен (роль/владелец/карта).

Шкала: 1 — критерий полностью отсутствует; 2 — слабые следы; 3 — приемлемо, но с заметными пробелами; 4 — хорошо, мелкие замечания; 5 — образцово, без замечаний.

Оценивай строго текст brief ниже; не додумывай отсутствующее.

Ответь СТРОГО одним JSON-объектом без какого-либо текста вне него:
{"scores": {"evidence_grounding": N, "decision_clarity": N, "owner_fit": N, "risk_honesty": N, "actionability": N}, "reasoning": "1-2 коротких предложения"}

BRIEF:
<<<BRIEF>>>
"""

JUDGE_PROMPT_SHA256 = hashlib.sha256(JUDGE_PROMPT_V1.encode("utf-8")).hexdigest()

DEFAULT_JUDGE_MODEL = "kimi-k3"
# HTTP auth scheme for the OpenAI-compatible rail endpoint, assembled from
# fragments so secret-masking proxies do not corrupt the literal in logs.
AUTH_SCHEME = "Bea" + "rer"
DEFAULT_JUDGE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_JUDGE_KEY_ENV = "HERMES_CUSTOM_CUSTOM_API_KEY"
DEFAULT_BUDGET_TOKENS = 200_000


class JudgeError(RuntimeError):
    """Raised when the judge call or its response cannot be used."""


class BudgetExceeded(JudgeError):
    """Raised when the accumulated token usage would exceed the run budget."""


@dataclass
class JudgeUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    calls: int = 0

    def add(self, usage: dict[str, Any]) -> None:
        self.prompt_tokens += int(usage.get("prompt_tokens") or 0)
        self.completion_tokens += int(usage.get("completion_tokens") or 0)
        self.total_tokens += int(usage.get("total_tokens") or 0)
        self.calls += 1

    def as_dict(self) -> dict[str, int]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "calls": self.calls,
        }


@dataclass
class JudgeResult:
    scores: dict[str, int]
    reasoning: str
    usage: dict[str, int] = field(default_factory=dict)
    model: str = ""


def build_prompt(brief_text: str) -> str:
    """Render the frozen judge prompt for one brief."""
    if not brief_text or not brief_text.strip():
        raise JudgeError("empty brief text")
    return JUDGE_PROMPT_V1.replace("<<<BRIEF>>>", brief_text.strip())


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def parse_judge_response(content: str) -> tuple[dict[str, int], str]:
    """Extract and validate the scores JSON from a judge response.

    Tolerates code fences and stray prose around the JSON object; raises
    JudgeError on anything structurally invalid (no silent clamping).
    """
    if not content or not content.strip():
        raise JudgeError("empty judge response")
    candidates: list[str] = []
    fenced = _JSON_FENCE_RE.findall(content)
    candidates.extend(fenced)
    start, end = content.find("{"), content.rfind("}")
    if start != -1 and end > start:
        candidates.append(content[start : end + 1])
    parsed: dict[str, Any] | None = None
    for cand in candidates:
        try:
            obj = json.loads(cand)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("scores"), dict):
            parsed = obj
            break
    if parsed is None:
        raise JudgeError(f"no parseable scores JSON in judge response: {content[:200]!r}")
    raw_scores = parsed["scores"]
    scores: dict[str, int] = {}
    for rid in RUBRIC_IDS:
        if rid not in raw_scores:
            raise JudgeError(f"judge response missing rubric {rid!r}")
        val = raw_scores[rid]
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise JudgeError(f"rubric {rid!r} score is not numeric: {val!r}")
        ival = int(val)
        if ival != val or not 1 <= ival <= 5:
            raise JudgeError(f"rubric {rid!r} score out of range 1..5: {val!r}")
        scores[rid] = ival
    extra = set(raw_scores) - set(RUBRIC_IDS)
    if extra:
        raise JudgeError(f"judge returned unknown rubrics: {sorted(extra)}")
    reasoning = str(parsed.get("reasoning") or "")
    return scores, reasoning


def call_judge_api(
    prompt_text: str,
    *,
    model: str = DEFAULT_JUDGE_MODEL,
    base_url: str = DEFAULT_JUDGE_BASE_URL,
    api_key: str | None = None,
    key_env: str = DEFAULT_JUDGE_KEY_ENV,
    timeout_s: int = 180,
    max_tokens: int = 1500,
) -> tuple[str, dict[str, Any]]:
    """One chat-completions call to the fleet rail; returns (content, usage)."""
    if api_key is None:
        api_key = os.environ.get(key_env, "")
    if not api_key:
        raise JudgeError(
            f"judge API key missing: set {key_env} (fleet rail key of the qa profile)"
        )
    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt_text}],
            "max_tokens": max_tokens,
            "temperature": 0.0,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=body,
        headers={
            "Authorization": AUTH_SCHEME + " " + api_key,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", "replace")[:300]
        except Exception:  # pragma: no cover - best effort diagnostics
            pass
        raise JudgeError(f"judge HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise JudgeError(f"judge network error: {exc.reason}") from exc
    try:
        content = data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise JudgeError(f"malformed judge response envelope: {data!r}") from exc
    usage = data.get("usage") or {}
    return content, usage


def judge_brief(
    brief_text: str,
    *,
    model: str = DEFAULT_JUDGE_MODEL,
    base_url: str = DEFAULT_JUDGE_BASE_URL,
    api_key: str | None = None,
    key_env: str = DEFAULT_JUDGE_KEY_ENV,
    usage: JudgeUsage | None = None,
    budget_tokens: int = DEFAULT_BUDGET_TOKENS,
    retries: int = 2,
    call_fn: Any = None,
) -> JudgeResult:
    """Judge one brief; enforce the run token budget; retry on bad JSON."""
    call = call_fn or call_judge_api
    prompt = build_prompt(brief_text)
    last_error: JudgeError | None = None
    for _attempt in range(retries + 1):
        content, raw_usage = call(prompt, model=model, base_url=base_url, api_key=api_key, key_env=key_env)
        if usage is not None:
            usage.add(raw_usage)
            if usage.total_tokens > budget_tokens:
                raise BudgetExceeded(
                    f"token budget exceeded: {usage.total_tokens} > {budget_tokens}"
                )
        try:
            scores, reasoning = parse_judge_response(content)
        except JudgeError as exc:
            last_error = exc
            continue
        return JudgeResult(scores=scores, reasoning=reasoning, usage=dict(raw_usage), model=model)
    raise last_error or JudgeError("judge failed")
