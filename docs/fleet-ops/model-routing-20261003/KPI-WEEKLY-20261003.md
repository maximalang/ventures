# KPI-WEEKLY — Рельсы v2.2 (окно от 2026-10-03T19:31:10.094284+00:00)

**Now:** 2026-10-03T21:29:47.910426+00:00  
**Profiles:** 13  
**Errors:** 0

## Дельта токенов по рельсам (now − baseline)

| Rail | Δinput | Δoutput | Δcache_read | Δreasoning | Δcalls |
|---|---:|---:|---:|---:|---:|
| 1|unknown|unknown | 0 | 0 | 0 | 0 | 0 |
| alibaba|chat_completions|unknown | 0 | 0 | 0 | 0 | 0 |
| cloudflare|chat_completions|unknown | 0 | 0 | 0 | 0 | 0 |
| copilot|unknown|unknown | 0 | 0 | 0 | 0 | 0 |
| custom|chat_completions|unknown | 0 | 0 | 0 | 0 | 0 |
| custom|codex_responses|unknown | 0 | 0 | 0 | 0 | 0 |
| custom|subscription_included|unknown | 0 | 0 | 0 | 0 | 0 |
| custom|unknown|unknown | 2,275,535 | 504,148 | 64,870,912 | 244,756 | 11 |
| fallback_chain[0](custom)|unknown|unknown | 0 | 0 | 0 | 0 | 0 |
| fallback_chain[0](openrouter)|unknown|unknown | 0 | 0 | 0 | 0 | 0 |
| groq|unknown|unknown | 0 | 0 | 0 | 0 | 0 |
| kilocode|chat_completions|unknown | 0 | 0 | 0 | 0 | 0 |
| kilocode|subscription_included|unknown | 0 | 0 | 0 | 0 | 0 |
| kilocode|unknown|estimated | 0 | 0 | 0 | 0 | 0 |
| kilocode|unknown|unknown | 0 | 0 | 0 | 0 | 0 |
| kilo|chat_completions|estimated | 0 | 0 | 0 | 0 | 0 |
| mistral|chat_completions|unknown | 0 | 0 | 0 | 0 | 0 |
| moa|unknown|unknown | 0 | 0 | 0 | 0 | 0 |
| ollama-cloud|chat_completions|unknown | 0 | 0 | 0 | 0 | 0 |
| ollama-cloud|unknown|unknown | 0 | 0 | 0 | 0 | 0 |
| openai-codex|subscription_included|included | 2,967,463 | 162,560 | 13,157,504 | 59,515 | 7 |
| openai-codex|unknown|unknown | 16,819 | 2,014 | 0 | 0 | 1 |
| opencode-free|unknown|unknown | 0 | 0 | 0 | 0 | 0 |
| opencode-zen|subscription_included|unknown | 0 | 0 | 0 | 0 | 0 |
| opencode-zen|unknown|unknown | 0 | 0 | 0 | 0 | 0 |
| openrouter|chat_completions|unknown | 0 | 0 | 0 | 0 | 0 |
| openrouter|subscription_included|estimated | 0 | 0 | 0 | 0 | 0 |
| openrouter|subscription_included|unknown | 0 | 0 | 0 | 0 | 0 |
| openrouter|unknown|estimated | 0 | 0 | 0 | 0 | 0 |
| openrouter|unknown|unknown | 0 | 0 | 0 | 0 | 0 |
| unknown|unknown|unknown | 0 | 0 | 0 | 0 | 0 |
| zai|chat_completions|unknown | 0 | 0 | 0 | 0 | 0 |
| zai|codex_responses|unknown | 0 | 0 | 0 | 0 | 0 |
| zai|subscription_included|unknown | 0 | 0 | 0 | 0 | 0 |
| zai|unknown|unknown | 1,275,468 | 304,645 | 17,574,016 | 222,229 | 10 |

## ROUTING-LOG (фаза C: shadow)

- Строк журнала: **0**
- Override share: n/a (журнал пуст — shadow-фаза ещё не писала диспатчи)
- Escalation rate: n/a

## QA-block (VERDICT-MATRIX*.md)

- Файлов: 0; PASS: **0**, FAIL: **0**
- Примечание: no by-class breakdown in this phase

## Limitations

- Первый прогон: дельты ≈ 0 — это нормально, фиксируется точка отсчёта KPI.
- included ≠ бесплатно: подписочные рельсы — предоплаченная квота.
- reasoning может уже входить в output; не суммировать.
- Чтение БД только через URI mode=ro&immutable=0; записи нет.
