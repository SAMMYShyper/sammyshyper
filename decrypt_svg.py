#!/usr/bin/env python3
"""
Generate an animated "decrypting text" SVG for a GitHub README.

Each character flickers through random glyphs, then locks into the real
letter, sweeping left to right. Lines cycle one after another, forever.
Pure SVG/SMIL: no JavaScript, so it renders on GitHub.

Usage:
    python decrypt_svg.py "First line of text" "Second line of text" -o decrypt.svg
    python decrypt_svg.py --help    # see all options (colors, size, speed...)
"""
import argparse
import random
from xml.sax.saxutils import escape

GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*<>?/\\|[]{}=+~"


def build(lines, size=28, width=None, height=None, color="#36BCF7", scramble_color="#3fb950",
          bg="none", reveal_ms=60, frame_ms=45, frames=7, hold_ms=1800, gap_ms=300,
          font="'Fira Code', Consolas, 'Courier New', monospace", weight=600, seed=7):
    rng = random.Random(seed)
    adv = size * 0.62                       # approx monospace advance
    longest = max(len(l) for l in lines)
    width = width or int(longest * adv + size * 2)
    height = height or int(size * 2.2)
    y = height / 2

    # timeline (ms) for each line
    timings, t = [], 0
    for line in lines:
        n = len(line)
        lock_last = (n - 1) * reveal_ms + frames * frame_ms
        timings.append((t, n))
        t += lock_last + hold_ms + gap_ms
    total = t
    dur = f"{total / 1000:.3f}s"

    def kt(ms):
        return f"{ms / total:.5f}"

    def anim(on_ms, off_ms):
        # visible from on_ms to off_ms, hidden otherwise (discrete steps)
        if on_ms <= 0:
            return (f'<animate attributeName="opacity" values="1;0" keyTimes="0;{kt(off_ms)}" '
                    f'dur="{dur}" calcMode="discrete" repeatCount="indefinite"/>')
        return (f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;{kt(on_ms)};{kt(off_ms)}" '
                f'dur="{dur}" calcMode="discrete" repeatCount="indefinite"/>')

    out = []
    for (start, n), line in zip(timings, lines):
        x0 = width / 2 - (n * adv) / 2 + adv / 2
        lock_last = (n - 1) * reveal_ms + frames * frame_ms
        line_end = start + lock_last + hold_ms
        for i, ch in enumerate(line):
            if ch == " ":
                continue
            x = x0 + i * adv
            appear = start + i * reveal_ms
            # scrambling glyphs
            prev = None
            for f in range(frames):
                g = rng.choice(GLYPHS)
                while g == prev or g == ch:
                    g = rng.choice(GLYPHS)
                prev = g
                on = appear + f * frame_ms
                out.append(f'<text x="{x:.1f}" y="{y}" class="s" opacity="0">{escape(g)}'
                           f'{anim(on, on + frame_ms)}</text>')
            # final locked character
            lock = appear + frames * frame_ms
            out.append(f'<text x="{x:.1f}" y="{y}" class="f" opacity="0">{escape(ch)}'
                       f'{anim(lock, line_end)}</text>')

    bg_rect = f'<rect width="100%" height="100%" fill="{bg}"/>' if bg != "none" else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>
text {{ font-family: {font}; font-size: {size}px; font-weight: {weight};
       text-anchor: middle; dominant-baseline: middle; }}
.f {{ fill: {color}; }}
.s {{ fill: {scramble_color}; opacity: 0; }}
</style>
{bg_rect}
{chr(10).join(out)}
</svg>
'''


def main():
    p = argparse.ArgumentParser(description="Decrypting-text animated SVG for GitHub READMEs")
    p.add_argument("lines", nargs="+", help="one or more lines of text")
    p.add_argument("-o", "--out", default="decrypt.svg")
    p.add_argument("--size", type=int, default=28, help="font size in px")
    p.add_argument("--width", type=int)
    p.add_argument("--height", type=int)
    p.add_argument("--color", default="#36BCF7", help="final text color")
    p.add_argument("--scramble-color", default="#3fb950", help="color of the random glyphs")
    p.add_argument("--bg", default="none", help="background color, e.g. #0d1117")
    p.add_argument("--reveal-ms", type=int, default=60, help="delay between characters")
    p.add_argument("--frame-ms", type=int, default=45, help="how long each random glyph shows")
    p.add_argument("--frames", type=int, default=7, help="random glyphs before each letter locks")
    p.add_argument("--hold-ms", type=int, default=1800, help="how long the finished line stays")
    p.add_argument("--seed", type=int, default=7)
    a = p.parse_args()
    svg = build(a.lines, a.size, a.width, a.height, a.color, a.scramble_color, a.bg,
                a.reveal_ms, a.frame_ms, a.frames, a.hold_ms, seed=a.seed)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote {a.out} ({len(svg) // 1024} KB)")


if __name__ == "__main__":
    main()
