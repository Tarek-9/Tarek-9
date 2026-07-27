"""Render a neofetch-style info card as a self-contained animated SVG.

Lines fade in on a stagger, then freeze - no loop. CSS lives inside the SVG, which is
fine: GitHub's sanitizer strips style from README *markdown*, but the SVG is fetched as
an image and rendered by the browser's SVG engine, which honours everything but scripts.

STATIC=1 emits a frozen frame for previewing.
"""

import os

TITLE = "tarek@github"
ROWS = [
    ("OS", "Windows 11 · Debian"),
    ("Shell", "PowerShell · bash"),
    ("Editor", "VS Code"),
    ("Stack", "TypeScript · React · Node"),
    ("Infra", "Docker · Linux · Traefik"),
    ("Lang", "DE · EN"),
]
SWATCHES = ["#39d353", "#26a641", "#006d32", "#58a6ff", "#bc8cff", "#f778ba", "#ffa657"]

WIDTH, HEIGHT = 482, 378  # 482 + the donut's 378 = 860, the heatmap's width
PAD = 22
KEY_X = 0
VAL_X = 96
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
FONT_SIZE = 15
BG, BORDER = "#0d1117", "#30363d"
FG, KEY, ACCENT, DIM = "#c9d1d9", "#58a6ff", "#39d353", "#484f58"
STEP = 0.09  # seconds between line reveals
OUT = "info-card.svg"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    static = os.environ.get("STATIC") == "1"
    body = []

    def line(i, content):
        """Wrap one line so it fades in at its own turn in the stagger."""
        if static:
            return f"<g>{content}</g>"
        return f'<g class="l" style="animation-delay:{i * STEP:.2f}s">{content}</g>'

    y = PAD + 24
    body.append(line(0, f'<text x="{KEY_X}" y="{y}" fill="{ACCENT}" '
                       f'font-weight="600">{esc(TITLE)}</text>'))

    y += 14
    body.append(line(1, f'<path d="M0 {y} H{WIDTH - 2 * PAD}" stroke="{DIM}"/>'))

    y += 30
    for i, (k, v) in enumerate(ROWS):
        body.append(line(
            i + 2,
            f'<text x="{KEY_X}" y="{y}" fill="{KEY}">{esc(k)}</text>'
            f'<text x="{VAL_X}" y="{y}" fill="{FG}">{esc(v)}</text>',
        ))
        y += 32

    y += 22
    blocks = "".join(
        f'<rect x="{i * 26}" y="{y}" width="18" height="18" rx="3" fill="{c}"/>'
        for i, c in enumerate(SWATCHES)
    )
    body.append(line(len(ROWS) + 2, blocks))

    # `both` (not `forwards`) and no base opacity:0 - the fade is an enhancement, so a
    # renderer that ignores CSS animation shows the card instead of a blank panel.
    style = "" if static else (
        "<style>"
        "@keyframes fi{from{opacity:0;transform:translateY(4px)}"
        "to{opacity:1;transform:translateY(0)}}"
        ".l{animation:fi .45s ease-out both}"
        "</style>"
    )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'width="{WIDTH}" height="{HEIGHT}" font-family="{FONT}" font-size="{FONT_SIZE}">'
        f"{style}"
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="8" '
        f'fill="{BG}" stroke="{BORDER}"/>'
        f'<g transform="translate({PAD},0)">' + "".join(body) + "</g></svg>"
    )
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)

    # the last element must still sit inside the panel, or the card silently clips
    assert y + 18 + PAD <= HEIGHT, f"content overflows: needs {y + 18 + PAD}px, have {HEIGHT}"
    print(f"{OUT}: {len(svg) / 1024:.1f} KB, {WIDTH}x{HEIGHT}, "
          f"content ends at {y + 18}px{' (static)' if static else ''}")


if __name__ == "__main__":
    main()
