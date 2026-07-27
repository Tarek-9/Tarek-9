"""Render the classic donut.c torus as a rotating ASCII animation in a self-contained SVG.

GitHub strips <script> from READMEs but does play SMIL inside SVGs served via <img>,
so every frame is baked in as a <g> and cycled with <animate calcMode="discrete">.
"""

import math
import os

# --- geometry (donut.c constants) ---
R1 = 1.0  # radius of the tube
R2 = 2.0  # distance from origin to tube center
K2 = 5.0  # viewer distance
THETA_STEP = 0.06  # around the tube
PHI_STEP = 0.015  # around the torus axis
RAMP = ".,-~:;=!*#$@"  # dark -> bright

# --- output grid ---
# Projected into a generous work area, then cropped to the bounding box the torus
# actually occupies across *all* frames - centering by hand only ever half-works,
# and a fixed grid either clips the donut or leaves dead rows under it.
COLS, ROWS = 68, 44
CHAR_W, CHAR_H = 7.0, 14.0  # monospace cell: twice as tall as wide
SPAN = 52  # how many columns wide the torus should render
FRAMES = 36
DURATION = 4.0  # seconds per full rotation
PAD = 14.0
# Baked-in dark panel: GitHub renders README images on the *viewer's* theme background,
# so light text on a transparent SVG disappears in light mode.
FG = "#c9d1d9"
BG = "#0d1117"
BORDER = "#30363d"
OUT = "ascii-donut.svg"


def frange(stop, step):
    n = int(stop / step)
    return (i * step for i in range(n))


def render_frame(a, b):
    """One projected frame of the torus, as a list of ROWS strings."""
    grid = [[" "] * COLS for _ in range(ROWS)]
    zbuf = [[0.0] * COLS for _ in range(ROWS)]

    # scale so the torus spans SPAN columns; y is squashed by the cell aspect
    kx = SPAN * K2 * 3 / (8 * (R1 + R2))
    ky = kx * (CHAR_W / CHAR_H)

    cos_a, sin_a = math.cos(a), math.sin(a)
    cos_b, sin_b = math.cos(b), math.sin(b)

    for theta in frange(2 * math.pi, THETA_STEP):
        cos_t, sin_t = math.cos(theta), math.sin(theta)
        circle_x = R2 + R1 * cos_t
        circle_y = R1 * sin_t

        for phi in frange(2 * math.pi, PHI_STEP):
            cos_p, sin_p = math.cos(phi), math.sin(phi)

            x = circle_x * (cos_b * cos_p + sin_a * sin_b * sin_p) - circle_y * cos_a * sin_b
            y = circle_x * (sin_b * cos_p - sin_a * cos_b * sin_p) + circle_y * cos_a * cos_b
            z = K2 + cos_a * circle_x * sin_p + circle_y * sin_a
            ooz = 1 / z

            xp = int(COLS / 2 + kx * ooz * x)
            yp = int(ROWS / 2 - ky * ooz * y)

            # luminance = surface normal . light direction (0, 1, -1)
            lum = (
                cos_p * cos_t * sin_b
                - cos_a * cos_t * sin_p
                - sin_a * sin_t
                + cos_b * (cos_a * sin_t - cos_t * sin_a * sin_p)
            )
            if lum <= 0:  # facing away from the light
                continue
            if not (0 <= xp < COLS and 0 <= yp < ROWS):
                continue
            if ooz > zbuf[yp][xp]:
                zbuf[yp][xp] = ooz
                grid[yp][xp] = RAMP[min(int(lum * 8), len(RAMP) - 1)]

    return ["".join(row) for row in grid]


def crop_all(frames):
    """Crop every frame to the box the torus occupies across the whole rotation."""
    top, bottom, left, right = ROWS, -1, COLS, -1
    for lines in frames:
        for r, line in enumerate(lines):
            stripped = line.rstrip()
            if not stripped:
                continue
            top, bottom = min(top, r), max(bottom, r)
            left = min(left, len(line) - len(line.lstrip()))
            right = max(right, len(stripped) - 1)
    assert bottom >= top and right >= left, "nothing drawn in any frame"
    return [[l[left : right + 1] for l in lines[top : bottom + 1]] for lines in frames]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def frame_svg(index, lines, cols):
    """A frame group, visible only during its slice of the loop."""
    lo, hi = index / FRAMES, (index + 1) / FRAMES
    if index == 0:
        values, times = "inline;none", f"0;{hi:.5f}"
    elif index == FRAMES - 1:
        values, times = "none;inline", f"0;{lo:.5f}"
    else:
        values, times = "none;inline;none", f"0;{lo:.5f};{hi:.5f}"

    text = "".join(
        # textLength pins each row's width so alignment survives any monospace font
        f'<text x="0" y="{(i + 1) * CHAR_H:.0f}" textLength="{cols * CHAR_W:.0f}" '
        f'lengthAdjust="spacingAndGlyphs">{esc(line)}</text>'
        for i, line in enumerate(lines)
    )
    return (
        f'<g display="none">{text}'
        f'<animate attributeName="display" calcMode="discrete" values="{values}" '
        f'keyTimes="{times}" dur="{DURATION}s" repeatCount="indefinite"/></g>'
    )


def static_svg(lines, cols):
    """A single frozen frame - for previewing, since a screenshot of a loop is a lottery."""
    text = "".join(
        f'<text x="0" y="{(i + 1) * CHAR_H:.0f}" textLength="{cols * CHAR_W:.0f}" '
        f'lengthAdjust="spacingAndGlyphs">{esc(line)}</text>'
        for i, line in enumerate(lines)
    )
    return f"<g>{text}</g>"


def main():
    static = os.environ.get("STATIC") == "1"
    frames = crop_all([render_frame(i * 0.14, i * 0.07) for i in range(FRAMES)])
    rows, cols = len(frames[0]), len(frames[0][0])
    width, height = cols * CHAR_W + 2 * PAD, rows * CHAR_H + 2 * PAD
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'width="{width:.0f}" height="{height:.0f}" font-family="ui-monospace,SFMono-Regular,'
        f'Menlo,Consolas,monospace" font-size="{CHAR_H * 0.82:.1f}" fill="{FG}" '
        f'xml:space="preserve">'
        f'<rect x="0.5" y="0.5" width="{width - 1:.0f}" height="{height - 1:.0f}" rx="8" '
        f'fill="{BG}" stroke="{BORDER}"/>'
        f'<g transform="translate({PAD:.0f},{PAD:.0f})">'
        + (static_svg(frames[9], cols) if static
           else "".join(frame_svg(i, f, cols) for i, f in enumerate(frames)))
        + "</g></svg>"
    )
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"{OUT}: {len(svg) / 1024:.0f} KB, {1 if static else FRAMES} frame(s), "
          f"{cols}x{rows} chars, {width:.0f}x{height:.0f} px"
          f"{' (static)' if static else ''}")


def demo():
    """Sanity check: frames must draw a ring, and cropping must leave no dead margin."""
    raw = [render_frame(i * 0.14, i * 0.07) for i in range(FRAMES)]
    assert all(len(f) == ROWS and all(len(l) == COLS for l in f) for f in raw)

    frames = crop_all(raw)
    rows, cols = len(frames[0]), len(frames[0][0])
    # cropping is only correct if every edge of the union is actually touched
    assert any(f[0].strip() for f in frames), "dead row at top"
    assert any(f[-1].strip() for f in frames), "dead row at bottom"
    assert any(l[0] != " " for f in frames for l in f), "dead column at left"
    assert any(l[-1] != " " for f in frames for l in f), "dead column at right"

    filled = sum(c != " " for l in frames[9] for c in l)
    assert 100 < filled < rows * cols * 0.75, f"implausible fill: {filled}"
    # A torus is hollow, but only from a tilted view - at A=B=0 it is edge-on and
    # legitimately solid. So the hole has to show up in *some* frame, not every one.
    holed = sum(1 for f in frames if "  " in f[rows // 2].strip())
    assert holed >= FRAMES // 4, f"hole visible in only {holed}/{FRAMES} frames - not a torus"

    print("\n".join(frames[9]))
    print(f"ok: {cols}x{rows} after crop, {filled} glyphs in frame 9, hole in {holed}/{FRAMES}")


if __name__ == "__main__":
    import sys

    demo() if "--demo" in sys.argv else main()
