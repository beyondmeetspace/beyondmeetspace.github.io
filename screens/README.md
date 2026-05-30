# Beyond Meet Space — in-world VR screen decks

Two self-contained, auto-looping reveal.js presentations for the two screens in the BMS world.

| File | Purpose | URL (once deployed) |
|---|---|---|
| `research.html` | Research overview — the three program findings + the program by the numbers | https://beyondmeet.space/screens/research.html |
| `recruiting.html` | Collaboration — FY26–28 multi-institution partner recruitment | https://beyondmeet.space/screens/recruiting.html |

## Behavior (built for unattended VR display)
- **Auto-advance + infinite loop**, no controls/keyboard/touch (`loop:true`, `autoSlide`, paused→auto-resume). Point a screen at the URL and walk away.
- Base canvas 1920×1080 (16:9); reveal.js scales to fill the screen. Large, distance-legible type.
- **All animations < 1s** (fade/slide transitions ~0.4s; auto-animate morphs 0.8s) — well under the 5-second cap.
- Option C palette (off-white / forest / terracotta) + Source Serif 4 (display), Atkinson Hyperlegible (body), JetBrains Mono (labels). reveal.js + fonts load from CDN.

## Content provenance
All facts (r = .33 / 38 studies, the two DOIs, 15+ pubs, 6 PIs / 6 institutions, NSF FW-HTF-R awards) are verified against the live site — nothing fabricated. Edit copy inline in each file's `<section>` blocks.

## If a screen only accepts video (not a web URL)
Screen-record the looping deck once (a full loop) to an mp4 and point the in-world video player at that file.
