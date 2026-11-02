"""header.svg: types `whoami`, prints who I am, then idles on a blinking cursor.

SMIL, not CSS: GitHub plays it, and headless Chrome renders it in screenshots. Every
animation only hides things during the first moments, so a renderer without SMIL
still shows the finished terminal instead of an empty panel.
"""

from theme import ACCENT, BRIGHT, FG, MUTED, WIDTH, esc, svg, write

HEIGHT = 172
PAD = 24
CW = 9  # px per glyph; textLength pins every mono run to it so the cursor math holds
USER, REST = "tarek@github", " ~ $ "
COMMAND = "whoami"
NAME = "Tarek ElHussain"
TAGLINE = "Building software from first idea to production, and keeping it running."
TYPE_START, TYPE_STEP = 0.6, 0.09  # s
ENTER = 1.4  # s: the output appears
OUT = "header"


def mono(x, y, s, fill):
    return (f'<text x="{x}" y="{y}" fill="{fill}" textLength="{len(s) * CW}" '
            f'lengthAdjust="spacingAndGlyphs">{esc(s)}</text>')


def prompt(y):
    return mono(PAD, y, USER, ACCENT) + mono(PAD + len(USER) * CW, y, REST, FG)


def main():
    x_cmd = PAD + len(USER + REST) * CW
    y1, y2, y3, y4 = 48, 88, 116, 150

    # typing: the clip grows one glyph per step; the cursor rides its right edge
    widths = [0] + [k * CW for k in range(1, len(COMMAND) + 1)]
    times = [0.0] + [TYPE_START + k * TYPE_STEP for k in range(len(COMMAND))]
    key_times = ";".join(f"{t / times[-1]:.4f}" for t in times)
    typing = (f'calcMode="discrete" keyTimes="{key_times}" dur="{times[-1]:.2f}s" '
              f'fill="freeze"')

    body = (
        f'<clipPath id="typed"><rect x="{x_cmd}" y="{y1 - 16}" width="{len(COMMAND) * CW}" height="22">'
        f'<animate attributeName="width" values="{";".join(map(str, widths))}" {typing}/>'
        f'</rect></clipPath>'
        + prompt(y1)
        + f'<g clip-path="url(#typed)">{mono(x_cmd, y1, COMMAND, BRIGHT)}</g>'
        # typing cursor: invisible without SMIL, so it never covers the command
        + f'<rect x="{x_cmd}" y="{y1 - 13}" width="{CW}" height="17" fill="{FG}" opacity="0">'
        f'<set attributeName="opacity" to="1" begin="0s" end="{ENTER}s"/>'
        f'<animate attributeName="x" values="{";".join(str(x_cmd + w) for w in widths)}" {typing}/>'
        f'</rect>'
        # output and the next prompt: hidden until "enter", visible otherwise
        + f'<g><set attributeName="opacity" to="0" begin="0s" end="{ENTER}s"/>'
        f'<text x="{PAD}" y="{y2}" fill="{BRIGHT}" font-size="22" font-weight="700">{esc(NAME)}</text>'
        f'<text x="{PAD}" y="{y3}" fill="{MUTED}">{esc(TAGLINE)}</text>'
        + prompt(y4)
        + f'<rect x="{x_cmd}" y="{y4 - 13}" width="{CW}" height="17" fill="{FG}">'
        f'<animate attributeName="opacity" values="1;0" calcMode="discrete" dur="1.06s" '
        f'begin="{ENTER}s" repeatCount="indefinite"/></rect></g>'
    )
    assert PAD + len(TAGLINE) * CW <= WIDTH - PAD, "tagline runs past the panel"
    write(OUT, svg(WIDTH, HEIGHT, body, font_size=15))


if __name__ == "__main__":
    main()
