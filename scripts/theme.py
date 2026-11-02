"""Shared look for every profile SVG: one palette, one font, one panel."""

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
# Baked-in dark panel: README images sit on the *viewer's* theme background, so light
# text on a transparent SVG would vanish in light mode.
BG, BORDER, NODE = "#0d1117", "#30363d", "#161b22"
FG, BRIGHT, MUTED, DIM = "#c9d1d9", "#e6edf3", "#8b949e", "#484f58"
KEY, ACCENT, DANGER = "#58a6ff", "#39d353", "#f85149"
WIDTH = 860  # every full-width panel, so they line up in the README


def esc(s):
    # NBSP: Chromium collapses leading and repeated spaces despite xml:space, which
    # turned the ASCII donut into a filled block
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", " ")


def panel(w, h):
    return (f'<rect x="0.5" y="0.5" width="{w - 1:.0f}" height="{h - 1:.0f}" rx="8" '
            f'fill="{BG}" stroke="{BORDER}"/>')


def svg(w, h, body, **attrs):
    extra = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
            f'width="{w:.0f}" height="{h:.0f}" font-family="{FONT}"{extra}>'
            f'{panel(w, h)}{body}</svg>')


def write(path, content, note=""):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"{path}: {len(content) / 1024:.1f} KB{note}")
