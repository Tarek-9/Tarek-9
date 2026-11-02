"""Shared look for every profile SVG: one font, one panel, a dark and a light palette.

Scripts draw with the dark colours; write() saves that as img/<name>-dark.svg and swaps
each dark hex for its light partner to get img/<name>-light.svg. The README picks one
per viewer via <picture> + prefers-color-scheme.
"""

import os

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
DARK = {
    "bg": "#0d1117", "border": "#30363d", "node": "#161b22", "fg": "#c9d1d9",
    "bright": "#e6edf3", "muted": "#8b949e", "dim": "#484f58", "key": "#58a6ff",
    "accent": "#39d353", "danger": "#f85149",
}
LIGHT = {
    "bg": "#f6f8fa", "border": "#d0d7de", "node": "#ffffff", "fg": "#1f2328",
    "bright": "#0b0d10", "muted": "#59636e", "dim": "#8c959f", "key": "#0969da",
    "accent": "#1a7f37", "danger": "#cf222e",
}
# the swap is a plain text replace, so no dark hex may repeat or reappear as a light one
assert len(set(DARK.values())) == len(DARK) and not set(DARK.values()) & set(LIGHT.values())

BG, BORDER, NODE = DARK["bg"], DARK["border"], DARK["node"]
FG, BRIGHT, MUTED, DIM = DARK["fg"], DARK["bright"], DARK["muted"], DARK["dim"]
KEY, ACCENT, DANGER = DARK["key"], DARK["accent"], DARK["danger"]
WIDTH = 860  # every full-width panel, so they line up in the README
OUT_DIR = "img"


def esc(s):
    # NBSP: Chromium collapses leading and repeated spaces despite xml:space, which
    # turned the ASCII donut into a filled block
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", " ")


def svg(w, h, body, framed=True, **attrs):
    extra = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    frame = (f'<rect x="0.5" y="0.5" width="{w - 1:.0f}" height="{h - 1:.0f}" rx="8" '
             f'fill="{BG}" stroke="{BORDER}"/>') if framed else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
            f'width="{w:.0f}" height="{h:.0f}" font-family="{FONT}"{extra}>{frame}{body}</svg>')


def to_light(dark_svg):
    for role, hex_ in DARK.items():
        dark_svg = dark_svg.replace(hex_, LIGHT[role])
    return dark_svg


def write(name, dark_svg, note=""):
    """Save img/<name>-dark.svg and img/<name>-light.svg."""
    os.makedirs(OUT_DIR, exist_ok=True)
    for variant, content in (("dark", dark_svg), ("light", to_light(dark_svg))):
        with open(os.path.join(OUT_DIR, f"{name}-{variant}.svg"), "w", encoding="utf-8") as f:
            f.write(content)
    print(f"{OUT_DIR}/{name}-{{dark,light}}.svg: {len(dark_svg) / 1024:.1f} KB{note}")
