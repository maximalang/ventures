# Self-check — Wardogs first pack v3

Status: **drafts only, not published**.

## Deliverables
- `WD-V2-02_draft.mp4` — 25.283 s, 1080×1920, 59.960 fps, H.264/AAC; SHA-256 `fa89e8f7301e466ea67671a34e920a5b4d32da121d32400945627b59114f0dc8`.
- `WD-V2-03_draft.mp4` — 17.500 s, 1080×1920, 60 fps, H.264/AAC; SHA-256 `c8c3c8dc1061d3b10b02d257629b47d7fd42fa496c006fb19e05ac6db43643be`.

## Automated evidence
- Full decode: PASS for both (`ffmpeg -v error -f null`, exit 0).
- Long black frames ≥0.5 s: none.
- Loudness / peak:
  - WD-V2-02: −14.03 LUFS-I, −4.06 dBTP.
  - WD-V2-03: −13.95 LUFS-I, −3.27 dBTP.
- Original Klipni banner presence at first/middle/final samples: PASS. Pixel MAE against source banner on opaque region:
  - WD-V2-02: 3.74 / 3.58 / 3.53.
  - WD-V2-03: 3.72 / 3.60 / 3.57.
- Banner is applied by the render filter for 100% of each clip (requirement ≥80%).
- Required description URL and hashtags are in `descriptions.txt`.

## Editorial decisions
- WD-V2-02 reorders the explainer into consequence → mechanic → action, not a raw repost.
- WD-V2-03 isolates the rescue-under-fire arc and omits the earlier profanity-heavy section.
- WD-V2-01 rejected: legacy EOF/caption damage; delogo test created unacceptable artifacts. Director handoff permitted a two-clip shortage.

## Remaining gate
Independent QA must visually review safe-zone readability, absence of clipped text, story coherence, and exact-hash deliverables before owner approval. Publishing remains forbidden.
