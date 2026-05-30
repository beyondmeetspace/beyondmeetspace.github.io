# Beyond Meet Space — in-world VR screen posters

Two **single-slide reveal.js "digital posters"** for the two in-world screens, each with a seamless looping ambient animation, plus pre-rendered seamless-loop videos for players that take a video URL.

| Screen | Poster (HTML) | Video | Look |
|---|---|---|---|
| Research overview | `research.html` | `video/research.mp4` | Light editorial |
| Collaboration / recruiting | `recruiting.html` | `video/recruiting.mp4` | Dark forest |

URLs (once deployed): `https://beyondmeet.space/screens/research.html` (or `…/video/research.mp4`), and the recruiting equivalents.

## Design
- **One poster per screen** — a single reveal.js slide with `disableLayout:true` (reveal hosts the stage; custom CSS controls a full-bleed 1920×1080 poster layout). Meant to be read at your own pace — no pagination, no auto-advance.
- **Seamless ambient motion.** All motion is CSS keyframes on a **12-second loop**, and every animation period divides 12s (background glow drift 12s, accent-bar glint 12s, kicker-dot pulse 3s, stat float 4s) so the frame at t=12s is identical to t=0 — the loop has no visible jump.
- Option C palette (off-white / forest / terracotta); Source Serif 4 (display), Atkinson Hyperlegible (body), JetBrains Mono (labels).

## Videos (`video/`)
- `research.mp4`, `recruiting.mp4` — 1920×1080, h264, **exactly 12.000s**, **seamless loop verified** (the wrap frame is pixel-identical to the first frame). Point a VR video player at the URL and it loops cleanly.
- Rendered deterministically: the Web Animations clock is seeked frame-by-frame over one 12s period (not screen-recorded), so the loop is mathematically exact.

## Re-render after editing a poster
Serve the repo locally, then run `bms_render.py` (uses the orator venv's Playwright + chromium and system ffmpeg). It captures 360 frames per poster by seeking `document.getAnimations()`, asserts the wrap frame equals frame 0, and encodes h264. Keep every CSS animation period a divisor of `window.BMS_LOOP_MS` (12000) or the seamless check will fail.

## Content provenance
All facts (r = .33 / 38 studies, the two DOIs, 15+ pubs, 6 PIs / 6 institutions, NSF FW-HTF-R awards) are verified against the live site — nothing fabricated.

_Earlier multi-slide deck versions of these files are preserved in git history._
