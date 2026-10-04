# Video department — owner approval packet v3

**Prepared:** 2026-09-21 03:58 +03:00  
**State:** ready for owner decision; nothing published.

## Decision requested

Approve or reject this exact package:

1. `VIDEO_STRATEGY_V4_DRAFT.md` — SHA-256 `f521e60aee1434e8e24dad18801ad615ab66ace4dd0a0ff4e1c5014749548bd5`.
2. `MONETIZATION_EXECUTION_PLAN_D0_14.md` — SHA-256 `033be17855ccd87427f3e42aad07385b58f3a9b73ef3cf4e0cde443e47df2793`.
3. `WD-V2-02_draft.mp4` — SHA-256 `fa89e8f7301e466ea67671a34e920a5b4d32da121d32400945627b59114f0dc8`.
4. `WD-V2-03_draft.mp4` — SHA-256 `c8c3c8dc1061d3b10b02d257629b47d7fd42fa496c006fb19e05ac6db43643be`.

A GO applies only to these hashes and the D0–14 plan. Any changed render requires a new QA hash gate.

## Evidence

- YouTube Shorts channel exists: `https://www.youtube.com/channel/UCKpIMZSrgLpk92FqXTvJEew` / `https://youtube.com/@Maxi-m1c6g`.
- Live Klipni profile check: YouTube Shorts is connected and marked `верифицирован`.
- Klipni Wardogs RU campaign checked live: campaign running; 25 ₽ / 1,000 views; 1,500 ₽ clip cap; 4,300 ₽ of 5,000 ₽ campaign budget shown available; minimum 1,000 views; 9:16, 15–60 s; supplied banner required ≥80% duration.
- Independent QA card `t_fb77ebf7`: **PASS** on both exact video hashes.
- QA independently reproduced: decode exit 0, 1080×1920 H.264/AAC, 25.283 s / 17.500 s, −14.0 LUFS-I, no black/frozen/silent defects, original campaign banner visible 100%, exact URL/tags present, no profanity detected.
- WD-V2-01 was rejected because its legacy source had caption/EOF damage; the director explicitly allowed a two-clip pack rather than shipping a damaged or duplicate third clip.

## Publication route after GO

1. Publish the two exact files to the verified YouTube Shorts channel with `descriptions.txt`.
2. Submit the published URLs to the live Wardogs RU Klipni campaign.
3. Record baselines at 0 h, then check 24 h / 72 h / day 7.
4. Kill or re-cut a format if three comparable posts miss the plan's minimum retention/view thresholds; do not scale spend without evidence.

TikTok remains a later channel and VPN is requested only if an actual geo-block occurs. EasyStart remains NO. MoneyPrinter/content-factory integration remains parked until validated volume or first repeatable payouts make throughput the bottleneck.

## Financial scope

- Period: prelaunch through owner decision; D0–14 begins only after GO.
- Confirmed revenue: `null` — nothing published, no eligible views/payouts.
- Refunds: `null` — no purchases/refunds in scope.
- Incremental paid costs: `0 ₽`.
- New commitments: `0 ₽`.
- Estimated usage cost: `null` — local tooling/model usage not metered into a reliable ruble amount.
- Source: live Klipni campaign/profile, exact local artifacts, Kanban `video` evidence.

## Decision format

- **GO VIDEO V3** — approve plan + both exact video hashes for publication/submission.
- **NO-GO:** specify which clip or plan clause must change.
