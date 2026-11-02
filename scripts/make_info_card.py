"""The info half of neofetch.svg: name, then skills, methods and training.

Lines fade in on a stagger, then freeze - no loop. `both` (not `forwards`) and no base
opacity:0, so a renderer that ignores CSS animation still shows the card.
"""

from theme import ACCENT, DIM, FG, KEY, esc

TITLE = "Tarek ElHussain"
# Skills, not tools - tools change, these don't. Training mirrors hub's src/data/trainings.tsx.
ROWS = [
    ("Skills", ["Web & mobile apps, end to end", "Accessible UI (WCAG)",
                "Design systems (Atomic Design)", "Self-hosting & deployments",
                "Networking fundamentals"]),
    ("Methods", ["Scrum, Kanban, Clean Code"]),
    ("Training", ["Requirements Engineering (IREB)", "Digital Accessibility (UX/UI)",
                  "Design Thinking, React Deep Dive", "Agile & Project Management"]),
    ("Lang", ["German, English"]),
]
# Plain punctuation only on the profile: no dashes, no middle dots.

CARD_W = 482
PAD = 22
VAL_X = 96
FONT_SIZE = 15
LINE = 25  # px between lines
GAP = 6  # extra px before each new key
STEP = 0.07  # seconds between line reveals


def card(static, height):
    """Return (style, body) for a CARD_W x height area whose origin is its top-left."""
    body = []

    def line(i, content):
        if static:
            return f"<g>{content}</g>"
        return f'<g class="l" style="animation-delay:{i * STEP:.2f}s">{content}</g>'

    y = PAD + 24
    body.append(line(0, f'<text x="0" y="{y}" fill="{ACCENT}" font-weight="600">{esc(TITLE)}</text>'))
    y += 14
    body.append(line(1, f'<path d="M0 {y} H{CARD_W - 2 * PAD}" stroke="{DIM}"/>'))
    y += 30
    n = 2
    for k, values in ROWS:
        for j, v in enumerate(values):
            key = f'<text x="0" y="{y}" fill="{KEY}">{esc(k)}</text>' if j == 0 else ""
            body.append(line(n, f'{key}<text x="{VAL_X}" y="{y}" fill="{FG}">{esc(v)}</text>'))
            n += 1
            y += LINE
        y += GAP
    last = y - LINE - GAP

    # the last row must sit inside the panel, or the card silently clips
    assert last + PAD <= height, f"card overflows: needs {last + PAD}px, have {height}"
    # ~9px per glyph at 15px monospace; a longer value runs past the right border
    longest = max(len(v) for _, values in ROWS for v in values)
    assert VAL_X + longest * 9 <= CARD_W - 2 * PAD, f"value too wide: {longest} chars"

    style = "" if static else (
        "<style>@keyframes fi{from{opacity:0;transform:translateY(4px)}"
        "to{opacity:1;transform:translateY(0)}}.l{animation:fi .45s ease-out both}</style>"
    )
    return style, (f'<g transform="translate({PAD},0)" font-size="{FONT_SIZE}">'
                   + "".join(body) + "</g>")
