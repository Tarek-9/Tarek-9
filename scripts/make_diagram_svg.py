"""diagram: how a request reaches Bikelytics on my server, drawn as an animated network path.

Named after one real system on purpose: an unnamed "web app, API, database" left viewers
guessing what it showed. Bikelytics really runs like this (Cloudflare DNS, Traefik via
Coolify, web + API + Postgres on the VPS). Static: no domains (those live on the
clickable project cards) and no live checks (make_projects_svg.py does those). DNS is its own lookup step, not a hop the
request passes through. Packets run under the nodes, so they vanish inside a box as if
it were processing them.
"""

from theme import BORDER, BRIGHT, DIM, FG, KEY, MUTED, NODE, ACCENT, WIDTH, esc, svg, write

TITLE = "How Bikelytics runs on my own server"
TITLE_H = 40  # px the title adds on top; the network below shifts down by this much
HEIGHT = 250 + TITLE_H
MAIN_Y = 140  # the https line from "you" to the proxy, before the shift
OUT = "diagram"


def node(x, y, w, label, color=FG):
    return (f'<rect x="{x}" y="{y - 16}" width="{w}" height="32" rx="6" fill="{NODE}" '
            f'stroke="{BORDER}"/><text x="{x + w / 2:.0f}" y="{y + 5}" fill="{color}" '
            f'text-anchor="middle">{esc(label)}</text>')


def small(x, y, s, anchor="middle"):
    return f'<text x="{x}" y="{y}" fill="{MUTED}" font-size="12" text-anchor="{anchor}">{esc(s)}</text>'


def packet(path, dur, begin):
    """A dot running along `path` and back (request, then response). Hidden without SMIL."""
    timing = f'dur="{dur}s" begin="{begin}s" repeatCount="indefinite"'
    return (f'<circle r="3.5" fill="{ACCENT}" opacity="0">'
            f'<animateMotion path="{path}" keyPoints="0;1;0" keyTimes="0;0.5;1" calcMode="linear" {timing}/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.05;0.95;1" {timing}/>'
            f'</circle>')


def main():
    you_x, you_w = 24, 104
    dns_x, dns_y = 168, 54
    proxy_x, proxy_w = 318, 128
    fork_x, app_x, app_w = 476, 506, 120
    web_y, api_y = 92, 188
    db_x, db_w = 676, 136
    you_c, you_r = you_x + you_w / 2, you_x + you_w

    lookup = f"M{you_c:.0f},{MAIN_Y - 16} V{dns_y} H{dns_x}"
    to_web = f"M{you_r},{MAIN_Y} H{fork_x} V{web_y} H{app_x}"
    to_db = f"M{you_r},{MAIN_Y} H{fork_x} V{api_y} H{db_x}"
    line = f'fill="none" stroke="{DIM}"'

    network = (
        # the server boundary: everything inside runs on my own machine
        f'<rect x="296" y="24" width="540" height="210" rx="8" fill="none" stroke="{BORDER}" '
        f'stroke-dasharray="6 5"/>' + small(312, 44, "my server", "start")
        + f'<path d="{lookup}" {line} stroke-dasharray="4 4"/>'
        + f'<path d="M{you_r},{MAIN_Y} H{proxy_x}" {line}/>'
        + f'<path d="M{proxy_x + proxy_w},{MAIN_Y} H{fork_x} V{web_y} H{app_x}" {line}/>'
        + f'<path d="M{proxy_x + proxy_w},{MAIN_Y} H{fork_x} V{api_y} H{app_x}" {line}/>'
        + f'<path d="M{app_x + app_w},{api_y} H{db_x}" {line}/>'
        + packet(lookup, 1.8, 0) + packet(to_web, 3.0, 0.6) + packet(to_db, 3.6, 1.6)
        + node(you_x, MAIN_Y, you_w, "you", BRIGHT)
        + node(dns_x, dns_y, 96, "DNS", KEY)
        + small(you_c + 8, 98, "1  lookup", "start")
        + small(you_r + 14, MAIN_Y - 10, "2  https", "start")
        + node(proxy_x, MAIN_Y, proxy_w, "reverse proxy", KEY)
        + small(proxy_x + proxy_w / 2, MAIN_Y + 34, "TLS, routes by host")
        + node(app_x, web_y, app_w, "web app")
        + small(app_x + app_w / 2, web_y + 34, "serves the UI")
        + node(app_x, api_y, app_w, "API")
        + small(app_x + app_w / 2, api_y + 34, "business logic")
        + node(db_x, api_y, db_w, "database")
        + small(db_x + db_w / 2, api_y + 34, "persistent data")
    )
    body = (f'<text x="24" y="34" fill="{BRIGHT}" font-weight="600">{esc(TITLE)}</text>'
            f'<g transform="translate(0,{TITLE_H})">{network}</g>')
    write(OUT, svg(WIDTH, HEIGHT, body, font_size=14))


if __name__ == "__main__":
    main()
