"""Render Beyond Meet Space in-world VR-screen posters to seamless-loop mp4s.

Deterministic, not screen-recorded: serves the repo locally, drives headless
chromium (Playwright) over the posters, freezes the Web Animations clock and
seeks it frame-by-frame across exactly one BMS_LOOP_MS period (default 12000 ms
= 360 frames at 30 fps), screenshots each frame, asserts the wrap frame is
pixel-identical to frame 0 (the seamless-loop guarantee), and encodes h264 via
system ffmpeg.

Reconstructed 2026-05-31 by the LLC instance from the spec in screens/README.md
+ the ACAD->LLC handoff, because the copy used on 2026-05-30 was never committed.
Now committed so it stops being a recurring gap.

Usage (from the Orator venv, repo root as cwd):
    python bms_render.py                       # renders the two pending posters
    python bms_render.py platform wellbeing    # explicit list
    python bms_render.py --all                 # all four screens

Requires: Orator venv (Playwright + chromium installed) and system ffmpeg.
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import shutil
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SCREENS = REPO_ROOT / "screens"
VIDEO_DIR = SCREENS / "video"

FPS = 30
DEFAULT_LOOP_MS = 12000
WIDTH, HEIGHT = 1920, 1080
PENDING = ["platform", "wellbeing"]
ALL_SCREENS = ["research", "recruiting", "platform", "wellbeing"]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _serve(root: Path, port: int) -> socketserver.TCPServer:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", port), handler)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def _ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        sys.exit("ffmpeg not found on PATH (install Gyan.FFmpeg).")
    return exe


def render_poster(page, name: str, base_url: str, frames_dir: Path, loop_ms: int) -> dict:
    """Capture the 360-frame loop for one poster. Returns verification info."""
    n_frames = round(FPS * loop_ms / 1000)
    page.goto(f"{base_url}/screens/{name}.html", wait_until="networkidle")
    # Reveal + webfonts must be settled before the first capture.
    page.wait_for_selector(".reveal .slides", state="visible", timeout=15000)
    page.evaluate("async () => { await document.fonts.ready; }")
    page.wait_for_timeout(300)

    # Freeze every animation so the only clock is the one we set.
    n_anims = page.evaluate(
        "() => { const a = document.getAnimations(); a.forEach(x => x.pause()); return a.length; }"
    )

    def capture(t_ms: float, path: Path) -> bytes:
        # Seek every animation, then wait for two real paints so the screenshot
        # reflects the new clock rather than a stale compositor frame.
        page.evaluate(
            "(t) => new Promise(res => {"
            "  document.getAnimations().forEach(a => { a.currentTime = t; });"
            "  requestAnimationFrame(() => requestAnimationFrame(res));"
            "})",
            t_ms,
        )
        page.screenshot(path=str(path), clip={"x": 0, "y": 0, "width": WIDTH, "height": HEIGHT})
        return path.read_bytes()

    first_bytes = None
    for i in range(n_frames):
        t = i * (loop_ms / n_frames)
        b = capture(t, frames_dir / f"f_{i:04d}.png")
        if i == 0:
            first_bytes = b
    # Wrap frame at exactly loop_ms must equal frame 0 (seamless loop).
    wrap_bytes = capture(loop_ms, frames_dir / "wrap.png")
    (frames_dir / "wrap.png").unlink(missing_ok=True)

    seamless = hashlib.sha256(first_bytes).hexdigest() == hashlib.sha256(wrap_bytes).hexdigest()
    return {"n_frames": n_frames, "n_anims": n_anims, "seamless": seamless,
            "first_bytes": first_bytes, "wrap_bytes": wrap_bytes}


def encode(frames_dir: Path, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        _ffmpeg(), "-y", "-framerate", str(FPS), "-i", str(frames_dir / "f_%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-vf", f"scale={WIDTH}:{HEIGHT}", "-movflags", "+faststart", str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def probe_duration(path: Path) -> float:
    exe = shutil.which("ffprobe") or "ffprobe"
    r = subprocess.run(
        [exe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def bottom_band_uniform(mid_png: Path, band_px: int = 64) -> bool:
    """Heuristic for the 5/30 'empty bottom band' bug: is the bottom band a
    single flat color spanning the full width? Advisory only."""
    from PIL import Image
    import statistics
    img = Image.open(mid_png).convert("RGB")
    w, h = img.size
    px = img.load()
    colors = {px[x, y] for y in range(h - band_px, h) for x in range(0, w, 37)}
    return len(colors) <= 2  # essentially one flat color across the band


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("posters", nargs="*", help="poster stems (default: pending two)")
    ap.add_argument("--all", action="store_true", help="render all four screens")
    ap.add_argument("--loop-ms", type=int, default=DEFAULT_LOOP_MS)
    args = ap.parse_args()

    posters = ALL_SCREENS if args.all else (args.posters or PENDING)
    for name in posters:
        if not (SCREENS / f"{name}.html").exists():
            sys.exit(f"missing poster: screens/{name}.html")

    port = _free_port()
    httpd = _serve(REPO_ROOT, port)
    base_url = f"http://127.0.0.1:{port}"
    print(f"serving {REPO_ROOT} at {base_url}")

    from playwright.sync_api import sync_playwright

    results = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--force-color-profile=srgb"])
            ctx = browser.new_context(viewport={"width": WIDTH, "height": HEIGHT},
                                      device_scale_factor=1)
            page = ctx.new_page()
            for name in posters:
                with tempfile.TemporaryDirectory() as td:
                    frames = Path(td)
                    print(f"\n=== {name} ===")
                    info = render_poster(page, name, base_url, frames, args.loop_ms)
                    print(f"  frames={info['n_frames']} animations={info['n_anims']} "
                          f"seamless={'YES' if info['seamless'] else 'NO'}")
                    if not info["seamless"]:
                        sys.exit(f"  SEAMLESS CHECK FAILED for {name}: wrap frame != frame 0. "
                                 f"Check that every CSS animation period divides {args.loop_ms}ms.")
                    out = VIDEO_DIR / f"{name}.mp4"
                    encode(frames, out)
                    # Save a mid-frame next to the video for the owner to eyeball.
                    mid = VIDEO_DIR / f"{name}-midframe.png"
                    shutil.copy(frames / f"f_{info['n_frames'] // 2:04d}.png", mid)
                    dur = probe_duration(out)
                    flat = bottom_band_uniform(mid)
                    size_kb = out.stat().st_size // 1024
                    print(f"  wrote {out} ({size_kb} KB, {dur:.3f}s, {WIDTH}x{HEIGHT})")
                    if abs(dur - args.loop_ms / 1000) > 0.01:
                        print(f"  WARNING: duration {dur:.3f}s != {args.loop_ms/1000:.3f}s")
                    if flat:
                        print(f"  WARNING: bottom band looks flat in {mid.name} — eyeball for an "
                              f"empty band (the 5/30 display:block-over-flex bug).")
                    results[name] = {"duration": dur, "seamless": True, "flat_bottom": flat}
            browser.close()
    finally:
        httpd.shutdown()

    print("\nSummary:")
    for name, r in results.items():
        print(f"  {name}: {r['duration']:.3f}s seamless=YES bottom_flat={r['flat_bottom']}")
    print("\nMid-frame PNGs saved to screens/video/<name>-midframe.png for visual confirmation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
