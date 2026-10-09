# TEMPLATE_BENCHMARK — Wardogs V4
Scope: public, reusable gaming/explainer Shorts templates and layouts. Pattern-level reuse only; no proprietary asset copying. Compiled 2026-09-21.

## Benchmark table (13 public sources)

| # | Source | What it is | Reusable pattern(s) | Notes for Wardogs V4 |
|---|--------|------------|---------------------|----------------------|
| 1 | Eklipse clip-templates guide [1] | Branding system for gaming Shorts (watermark, captions, intro/outro, background fill) | Template-as-render-config: set once, applied to every clip; base layouts = gameplay-fill (blurred), split-screen, gameplay-only, facecam-focus; watermark 120–180 px at 1080×1920; captions styled as lower-thirds | Confirms V4 need for a *fleet* template (one config → all clips), not one-off filters. Blurred-fill and split-screen are the two dominant vertical layouts |
| 2 | DOR viral gaming Shorts pattern [2] | Empirical pattern guide for gaming Shorts | First-3-second hook; big captions 4–7 words, high-contrast white-on-black; loop end→start; 15–30 s length; vertical crop 9:16 | Validates the “cold-open payoff” and “rewind + annotated action” beats of `gaming-moment-breakdown`. Confirms caption size and word count |
| 3 | Mixkit Premiere Pro gaming templates [3] | 2 free gaming templates (Facebook Lower Third, Gaming Title Animation) | Lower-third for stream branding; particle title reveal for headline | Thin catalog; pattern = minimal lower-third + bold title card. Nothing here covers step-by-step explanation |
| 4 | Mixkit After Effects vertical templates [4] | 10 free vertical AE templates | Vertical logo glitch, travel/social story with fast text animation, sport border with bold text, call-out vertical story | Shows what “vertical template” usually means: title + text placeholders + fast transitions. Missing: ordered explanatory beats and annotation layer |
| 5 | Adobe Express YouTube Shorts templates [5] | 3,029 editable Shorts templates | Drag-and-drop, one-click animated effects, royalty-free stock, caption styling | Volume confirms generic Shorts templates are commoditised; differentiation must come from structure (explainer beats + annotations), not decoration |
| 6 | Kapwing gaming video editor [6] | Online editor with gaming-specific tools | Automatic subtitles, safe-zone presets, resizing to 9:16, animated stickers, sound effects | Safe-zone presets and word-by-word animated captions are now table stakes; Wardogs V4 must hard-wire safe zones into the template |
| 7 | Mixkit Premiere Pro call-outs [7] | 73 free call-out MOGRTs | Dot/focus point, rounded-rectangle frame, animated line, underlined title, two-line text block | Rich pattern library for annotation layer: arrow, target ring, numbered callout, stat card. All are “call-out” class, not full explainer templates |
| 8 | Everpop — YouTube Shorts safe zone [8] | Google-ads safe-zone template + caption placement rules | Safe box = 288 px top / 672 px bottom / 48 px left / 192 px right on 1080×1920 → 840×960 px usable; caption floor at 65% height; max width 696 px when centred | Authoritative safe-zone numbers. Bottom third is reserved — V4 “lower-third subtitles” must sit *above* the 200 px bottom safe zone, not inside it |
| 9 | Clypse vertical gaming clips guide [9] | 2026 layout guide for gaming + facecam | Four layout archetypes: split-screen (40/60), facecam overlay (20–25%), blurred background, dynamic switching; export 1080×1920, 60 fps, H.264, AAC 48 kHz | Layout archetypes map 1-to-1 to Wardogs remaster needs. Dynamic switching is the “restrained transition” pattern |
| 10 | Canva YouTube Shorts templates [10] | 931+ editable Shorts templates | Bold title cards, split-screen day-in-life, tips listicles, colour-blocked captions | Volume again commoditised; Canva pattern = static layout + animated text. No built-in step/progress logic |
| 11 | PosterMyWall gaming-overlay Shorts [11] | 28 free video Shorts templates tagged “gaming overlay” | Neon/gradient overlays, animated stickers, lower-third banners | Overlay-heavy style; useful for accent elements but risks “decoration without information” that owner feedback bans |
| 12 | Enchanted Media free MOGRTs [12] | Free Premiere Pro motion-graphics templates | Animated titles, lower thirds, transitions, overlays; plugin-free, drag-and-drop | Confirms lower-thirds + transitions are solved commodities; the reusable V4 value is the *ordered explanatory structure* on top |
| 13 | HyperVids — Shorts explainer guide [13] | Spec + structure for 60-second vertical explainers | 0–2 s cold open, 2–5 s outcome framing, 5–20 s concept, 20–45 s three steps, 45–55 s payoff, 55–59 s soft CTA; visual reset every 2–3 s; captions 2 lines max, 28–32 chars; safe area 864×1536 with 130 px top/bottom | Closest match to `gaming-explainer` template. Gives exact beat timing and caption constraints that align with owner feedback |

## Reusable pattern shortlist

Patterns below are extracted from the benchmark and map directly to the owner’s required reusable templates.

### gaming-explainer (Hook → Context → 3-step explanation → Payoff → CTA)
- 0–2 s cold-open hook: no logo, no sting; open on the most specific visual or a bold claim [13].
- 2–5 s outcome framing: one sentence telling the viewer what they will get [13].
- 5–20 s core concept visualised: one idea per shot, 2–3 s per visual [13].
- 20–45 s three ordered steps: each step = one sentence + one visual [13].
- 45–55 s payoff: numeric or before/after result [13].
- 55–59 s soft CTA: “save this”, “comment next”, no hard sell [13].
- Visual reset every 2–3 s (crop, zoom, caption pop) [13].

### gaming-moment-breakdown (cold-open payoff → rewind → annotated action → lesson → payoff)
- Pull the moment just before the payoff into the first frame; cut setup entirely [2].
- Use big captions of 4–7 words, high-contrast white-on-black, placed in safe area [2].
- Loop end frame back to start frame to drive re-watches [2].
- Annotate the action with call-outs (see Annotation layer).

### Bottom-subtitle system
- 4–7 words per phrase, 1–2 lines, ≤32 chars/line (HyperVids) to ≤42 chars/line (owner) [13].
- High-contrast white text with black outline or semi-opaque plate [2][13].
- Position: lower third *above* the 200 px bottom safe zone; Google safe-zone floor is 65% of frame height (1,248 px from top on 1080×1920) [8].
- Word-by-word or per-phrase timing is now standard in Kapwing, Eklipse, Clypse [1][6][9].
- Highlight one keyword per line with a single accent colour [13].

### Annotation layer (arrow, target ring, numbered callout, stat/info card, chapter/progress pill)
- Call-out classes from Mixkit: focus dot, rounded-rectangle frame, animated line, underlined title, two-line block [7].
- Eklipse/Clypse use text overlays for channel name, game title, CTA [1][9].
- Use call-outs to label gameplay proof (e.g. “Step 2”, “Watch the crosshair”), not decoration [7].

### Transition set (hard cut, 4–6 frame dip, 105–112% punch-in, 0.3–0.5 s freeze-frame)
- HyperVids: direct cuts for clarity; reserve big moves for beat changes [13].
- DOR: cut the sagging stretches so no cut is wasted [2].
- Clypse: dynamic switching between fullscreen facecam and fullscreen gameplay keeps attention [9].
- Punch-in/zoom is a standard “visual reset” every 2–3 s [13].

## What public templates do NOT give us (gaps the fleet template must fill)
1. **Ordered explanatory structure.** Generic Shorts templates (Canva, Adobe Express, PosterMyWall) are layout + text placeholders; none encode a 3-step explanatory beat map [5][10][11].
2. **Safe-zone-aware caption system.** Safe zones are documented (Everpop/Google) but not baked into most free templates; Kapwing/Eklipse offer presets, not enforcement [6][8].
3. **Annotation + step indicator as a reusable class.** Call-outs exist as isolated MOGRTs (Mixkit/Enchanted) but not as a coordinated annotation layer tied to a progress pill [7][12].
4. **Restrained transition grammar.** Most free templates ship flashy transitions; owner feedback explicitly bans decoration without information. The fleet template must default to hard cuts, dips, punch-ins, and freeze-frames [2][13].

## Sources
[1] https://blog.eklipse.gg/featured/eklipse-clip-templates-branded-gaming-shorts.html (2026-05-04)
[2] https://clip.dor.gg/en/blog/gaming-shorts-viral-pattern (2026-06-24)
[3] https://mixkit.co/free-premiere-pro-templates/gaming/ (accessed 2026-09-21)
[4] https://mixkit.co/free-after-effects-templates/vertical/ (accessed 2026-09-21)
[5] https://www.adobe.com/express/templates/video/youtube/shorts (accessed 2026-09-21)
[6] https://www.kapwing.com/video-editor/gaming (accessed 2026-09-21)
[7] https://mixkit.co/free-premiere-pro-templates/call-outs/ (accessed 2026-09-21)
[8] https://everpop.app/blog/where-to-put-captions-so-youtube-ui-doesnt-cover-them (2026-08-12)
[9] https://clypse.ai/blog/how-to-make-vertical-gaming-clips-facecam-2026 (2026-01-19)
[10] https://www.canva.com/youtube-shorts/templates/ (accessed 2026-09-21)
[11] https://www.postermywall.com/index.php/posters/search?s=gaming+overlay&dss=youtube-shorts-template&tt=video (accessed 2026-09-21)
[12] https://www.enchanted.media/free-premiere-pro-motion-graphics-templates/ (accessed 2026-09-21)
[13] https://hypervids.hub.elitecoders.co/learn/how-to-make-explainer-video-for-youtube-shorts (accessed 2026-09-21)
