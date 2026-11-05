"""Project cards: one SVG per project, so each card can link to its own site.

An SVG inside <img> cannot hold its own links, hence one file per card; the links
themselves live in README.md. Each card carries a live light, refreshed hourly by
.github/workflows/update-status.yml. Rule for this list: only what is publicly
reachable *and* meant for the public - no staging, no admin panels, nothing personal.

The caption under the grid holds the check date, so a file changes at least daily: that
commit keeps the schedule alive (GitHub disables schedules after 60 quiet days) and
tells visitors how fresh the lights are.

--demo renders one card per state and checks them, without touching the network.
"""

import urllib.error
import urllib.request
from datetime import datetime, timezone

from theme import ACCENT, BORDER, BRIGHT, DANGER, DIM, KEY, MUTED, WIDTH, esc, svg, write

PROJECTS = [  # (slug, name, description lines, url or None while not public)
    ("bikelytics", "Bikelytics", ["Motorcycle history and stats explorer."],
     "https://bikelytics.tarek.foo"),
    ("portfolio", "Portfolio", ["My projects, skills and training", "in more detail."],
     "https://tarek.foo"),
    ("ichbinhier", "Ich bin hier", ["Volunteer sign-up for ichbinhier e.V.,",
                                    "a school project built in a team."],
     "https://ichbinhier.work.gd"),
    ("detour", "Detour", ["School project from an international",
                          "Design Thinking workshop in Taiwan."],
     "https://detour.tarek.foo"),
    ("navo", "Navo", ["Workout tracker app.", "Works offline, no account needed."], None),
]
CARD_W, CARD_H = 425, 140
PAD = 24
STATES = {  # state: (colour, label)
    "up": (ACCENT, "online"),
    "down": (DANGER, "offline"),
    "soon": (MUTED, "in testing, coming to Google Play"),
}


def is_up(url):
    """Up = the server answered below 500."""
    req = urllib.request.Request(url, headers={"User-Agent": "Tarek-9-profile-status"})
    try:
        with urllib.request.urlopen(req, timeout=10):
            return True
    except urllib.error.HTTPError as e:
        return e.code < 500
    except (urllib.error.URLError, OSError):
        return False


def card(name, lines, url, state):
    color, label = STATES[state]
    dot_y = CARD_H - 26
    pulse = (f'<circle cx="{PAD + 4}" cy="{dot_y}" r="4.5" fill="none" stroke="{color}" opacity="0">'
             f'<animate attributeName="r" values="4.5;10" dur="2s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="0.7;0" dur="2s" repeatCount="indefinite"/>'
             f'</circle>') if state == "up" else ""
    status = f'<text x="{PAD + 18}" y="{dot_y + 5}" fill="{color}">{esc(label)}</text>'
    if url:  # the domain tells people where the click goes
        domain = url.split("://", 1)[1]
        status += (f'<text x="{CARD_W - PAD}" y="{dot_y + 5}" fill="{KEY}" '
                   f'text-anchor="end">{esc(domain)}</text>')
    body = (
        f'<text x="{PAD}" y="40" fill="{BRIGHT}" font-size="18" font-weight="700">{esc(name)}</text>'
        + (f'<text x="{CARD_W - PAD}" y="40" fill="{ACCENT}" font-size="18" text-anchor="end">↗</text>'
           if url else "")
        + "".join(f'<text x="{PAD}" y="{66 + i * 20}" fill="{MUTED}">{esc(l)}</text>'
                  for i, l in enumerate(lines))
        + f'<circle cx="{PAD + 4}" cy="{dot_y}" r="4.5" fill="{color}"/>{pulse}{status}'
    )
    assert len(lines) <= 2, f"{name}: description has room for two lines"
    # ~8.4px per glyph at 14px monospace
    assert all(PAD + len(l) * 8.4 <= CARD_W - PAD for l in lines), f"{name}: line too long"
    return svg(CARD_W, CARD_H, body, font_size=14)


def caption(checked):
    text = esc(f"Live status, checked {checked} (UTC), refreshes hourly.")
    return svg(WIDTH, 28, f'<text x="{WIDTH / 2:.0f}" y="18" fill="{DIM}" font-size="12" '
                          f'text-anchor="middle">{text}</text>', framed=False)


def main():
    for slug, name, lines, url in PROJECTS:
        # one retry, so a single dropped request doesn't paint a card red for an hour
        state = "soon" if url is None else ("up" if is_up(url) or is_up(url) else "down")
        write(f"project-{slug}", card(name, lines, url, state), f" ({state})")
    write("projects-caption", caption(datetime.now(timezone.utc).date().isoformat()))


def demo():
    up = card("Up", ["line"], "https://example.org", "up")
    down = card("Down", ["line"], "https://example.org", "down")
    soon = card("Soon", ["line"], None, "soon")
    assert ">online<" in up and "<animate" in up and "example.org" in up
    assert ">offline<" in down and "<animate" not in down
    assert "↗" not in soon and "example.org" not in soon, "a card without url must not look clickable"
    assert "2026-01-01" in caption("2026-01-01")
    print("ok: up/down/soon cards and caption render as expected")


if __name__ == "__main__":
    import sys

    demo() if "--demo" in sys.argv else main()
