# Measurement methodology second eye — verified corrections

The independent child review is advisory, not a release or QA gate. Company recomputed all following figures from the actual saved completion events; output is measurement-strata.json.

## Accepted clarifications
- API observations cover 2026-10-02T12:04:24+03:00 through 2026-10-03T11:35:18+03:00: 23.515 hours, 771 observed calls. Rotation coverage is incomplete. The unique tool-result audit uses a separate seven-day window; do not combine the windows as a weekly savings total.
- Mixed-model median222841 is valid as a description of that sample, not an apples-to-apples optimization metric. Qwen474 calls median316154, p95479591; Sol6.1297 calls median164533, p95224889.5.
- Cache-known uncached-input medians: Qwen1842.5 (474/474 cache-known), Sol3115 (289/297 cache-known;8 unknown). Do not subtract unknown cache as zero. Input/cache sums are retransmitted request usage, not unique content; they are valid observed-window measures, not invoice cash.
- Large cached prefixes still consume request footprint; neither the96.1% aggregate cache share nor gross input reduction proves cash savings, quota recovery, or quality gain. Record observed cached/uncached usage separately; no hypothetical weighted price without provider-specific verified tariff/quota semantics.
- Unique result-character ranking shows content generated/loaded by tools once, not marginal repeated-input token attribution. skill_view is the largest unique textual source in this audit, not proven the largest cause of all billed tokens.
- prompt-size is an offline byte/character snapshot, not measured tokenizer input. Do not convert with a chars-per-token constant or compare as money. Cross-model tokenization can be future evidence, not a new prerequisite to source hub-character reduction.
-128000 is a proposed compaction trigger. It is not a hard API-call ceiling. Before-change maxima above128000 cannot prove how an uninstalled candidate behaves. Native source/config consumer tests and natural after-change calls establish candidate behavior.
- Company-profile-wide scope includes Desktop/cron. Telegram-stratified measurements are still valid Telegram observations; do not attribute aggregate company savings to Telegram alone. Separate outside-Telegram effects when making a company-wide conclusion.

## After-change acceptance
Target at least10 real comparable natural Telegram calls PER observed model/provider stratum; if either sample is smaller, report insufficient sample rather than pool model mixes or invent a percentage. Measure preserved routing, owner goal, steering, attachments and alert behavior as quality guards. Do not run paid synthetic inference, induce loops, reset sessions, or create another recurring LLM lane to fill samples.

Finance scope=methodology review+natural Telegram observation; costs/revenue/refunds/estimated usage are unknown without attribution/invoice. No new purchase or commitment. This memo changes measurement requirements, not the immutable native candidate or its application authority.
