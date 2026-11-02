"""status.svg: how a request reaches my apps, with a live up/down light per app.

Run hourly by .github/workflows/update-status.yml. Only public apps belong here -
admin panels and tailnet-only services stay off a public profile.
The footer carries the check date, so the file changes at least daily: that commit
keeps the scheduled workflow alive (GitHub disables schedules after 60 quiet days)
and tells visitors how fresh the lights are.

--demo renders a fixed up/down mix and checks it, without touching the network.
"""

import urllib.error
import urllib.request
from datetime import datetime, timezone

from theme import (ACCENT, BORDER, BRIGHT, DANGER, DIM, FG, KEY, MUTED, NODE, WIDTH,
                   esc, svg, write)

SERVICES = [  # (name, environment, url)
    ("bikelytics", "production", "https://bikelytics.run.place"),
    ("bikelytics", "staging", "https://staging.bikelytics.run.place"),
    ("bikelytics", "testing", "https://testing.bikelytics.run.place"),
    ("ich bin hier", "production", "https://ichbinhier.work.gd"),
]
HEIGHT = 280
MAIN_Y = 142  # the https line from "you" to the proxy
ROW_GAP = 40
OUT = "status.svg"


def is_up(url):
    """Up = the server answered below 500. A 401 behind basic auth is still up."""
    req = urllib.request.Request(url, headers={"User-Agent": "Tarek-9-profile-status"})
    try:
        with urllib.request.urlopen(req, timeout=10):
            return True
    except urllib.error.HTTPError as e:
        return e.code < 500
    except (urllib.error.URLError, OSError):
        return False


def node(x, y, w, label, color=FG):
    return (f'<rect x="{x}" y="{y - 16}" width="{w}" height="32" rx="6" fill="{NODE}" '
            f'stroke="{BORDER}"/><text x="{x + w / 2:.0f}" y="{y + 5}" fill="{color}" '
            f'text-anchor="middle">{esc(label)}</text>')


def small(x, y, s, color=MUTED, anchor="start"):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="12" text-anchor="{anchor}">{esc(s)}</text>'


def packet(path, dur, begin, there_and_back=False):
    """A dot running along `path`; invisible before it starts or without SMIL."""
    motion = ' keyPoints="0;1;0" keyTimes="0;0.5;1" calcMode="linear"' if there_and_back else ""
    return (f'<circle r="3.5" fill="{ACCENT}" opacity="0">'
            f'<animateMotion path="{path}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"{motion}/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.9;1" '
            f'dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/></circle>')


def render(states, checked):
    n = len(SERVICES)
    ys = [MAIN_Y + (i - (n - 1) / 2) * ROW_GAP for i in range(n)]
    you_x, you_w = 24, 104
    dns_x, dns_y = 168, 56
    proxy_x, proxy_w = 330, 140
    fork_x, app_x, app_w = 510, 540, 276  # ends 20px inside the server boundary
    you_c = you_x + you_w / 2

    lookup = f"M{you_c:.0f},{MAIN_Y - 16} V{dns_y} H{dns_x}"
    edges = (f'<path d="{lookup}" fill="none" stroke="{DIM}" stroke-dasharray="4 4"/>'
             f'<path d="M{you_x + you_w},{MAIN_Y} H{proxy_x}" stroke="{DIM}"/>')
    packets = packet(lookup, 1.8, 0, there_and_back=True)
    apps = ""
    for i, ((name, env, _), up, y) in enumerate(zip(SERVICES, states, ys)):
        route = f"M{you_x + you_w},{MAIN_Y} H{fork_x} V{y:.0f} H{app_x}"
        dash = "" if up else ' stroke-dasharray="3 4"'
        edges += (f'<path d="M{proxy_x + proxy_w},{MAIN_Y} H{fork_x} V{y:.0f} H{app_x}" '
                  f'fill="none" stroke="{DIM if up else DANGER}"{dash}/>')
        if up:  # traffic only flows to apps that answer
            packets += packet(route, 2.6, round(i * 0.65, 2))
        color = ACCENT if up else DANGER
        pulse = (f'<circle cx="{app_x + 18}" cy="{y:.0f}" r="4.5" fill="none" stroke="{color}" opacity="0">'
                 f'<animate attributeName="r" values="4.5;10" dur="2s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0.7;0" dur="2s" repeatCount="indefinite"/>'
                 f'</circle>') if up else ""
        apps += (f'<rect x="{app_x}" y="{y - 15:.0f}" width="{app_w}" height="30" rx="6" '
                 f'fill="{NODE}" stroke="{BORDER}"/>'
                 f'<circle cx="{app_x + 18}" cy="{y:.0f}" r="4.5" fill="{color}"/>{pulse}'
                 f'<text x="{app_x + 34}" y="{y + 5:.0f}" fill="{FG}">{esc(name)}</text>'
                 + small(app_x + 160, y + 4, env)
                 + small(app_x + app_w - 14, y + 4, "up" if up else "down", color, "end"))

    body = (
        # the server boundary: everything inside runs on my own machine
        f'<rect x="300" y="28" width="536" height="220" rx="8" fill="none" stroke="{BORDER}" '
        f'stroke-dasharray="6 5"/>' + small(316, 48, "my server")
        + edges + packets
        + node(you_x, MAIN_Y, you_w, "you", BRIGHT)
        + node(dns_x, dns_y, 96, "DNS", KEY)
        + small(you_c + 8, 100, "1  lookup")
        + small(you_x + you_w + 14, MAIN_Y - 10, "2  https")
        + node(proxy_x, MAIN_Y, proxy_w, "reverse proxy", KEY)
        + small(proxy_x + proxy_w / 2, MAIN_Y + 34, "TLS · routes by host", anchor="middle")
        + apps
        + small(WIDTH - 24, HEIGHT - 14, f"checked {checked} · refreshes hourly", DIM, "end")
    )
    return svg(WIDTH, HEIGHT, body, font_size=14)


def main():
    # one retry, so a single dropped request doesn't paint an app red for an hour
    states = [is_up(url) or is_up(url) for _, _, url in SERVICES]
    checked = datetime.now(timezone.utc).date().isoformat()
    write(OUT, render(states, checked),
          " · " + ", ".join(f"{n}/{e}: {'up' if s else 'DOWN'}" for (n, e, _), s in zip(SERVICES, states)))


def demo():
    out = render([True, False, True, True], "2026-01-01")
    assert out.count("<animateMotion") == 1 + 3, "one dns packet + one per up app"
    assert out.count(">down<") == 1 and out.count(">up<") == 3
    assert "2026-01-01" in out, "check date missing from the footer"
    write("status-demo.svg", out, " (demo: staging down)")


if __name__ == "__main__":
    import sys

    demo() if "--demo" in sys.argv else main()
